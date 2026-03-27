import streamlit as st
import os
import sqlite3
import re
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import io

load_dotenv()

# ─────────────────────────────────────────────────────────────
# إعداد الصفحة
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DONIA LABS - المعلم الذكي",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# CSS مخصص
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
*, *::before, *::after { font-family: 'Tajawal', sans-serif !important; }
.stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
.main  { direction: rtl; text-align: right; }

.title-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2.2rem 2rem; border-radius: 20px; text-align: center;
    margin-bottom: 1.8rem; box-shadow: 0 12px 45px rgba(102,126,234,.45);
}
.title-card h1 { color:#fff; font-size:2.6rem; font-weight:800; margin:0; }
.title-card p  { color:rgba(255,255,255,.85); font-size:1.1rem; margin:.5rem 0 0; }

.stat-card {
    background: linear-gradient(135deg,rgba(102,126,234,.18),rgba(118,75,162,.18));
    border: 1px solid rgba(102,126,234,.35); border-radius: 14px;
    padding: 1.2rem; text-align: center; margin-bottom: .8rem;
}
.stat-card h2 { font-size:2.2rem; margin:0; }
.stat-card p  { margin:0; color:rgba(255,255,255,.75); font-size:.9rem; }

.db-item {
    background: rgba(255,255,255,.06); border-right: 4px solid #667eea;
    border-radius: 8px; padding: .8rem 1rem; margin: .4rem 0;
    direction: rtl; text-align: right; color: rgba(255,255,255,.9);
}

.result-box {
    background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.12);
    border-radius: 14px; padding: 1.6rem; direction: rtl; text-align: right;
    backdrop-filter: blur(10px); color: rgba(255,255,255,.92);
    line-height: 2; margin: 1rem 0;
}

div.stButton > button {
    background: linear-gradient(135deg,#667eea,#764ba2); color: #fff;
    border: none; border-radius: 10px; padding: .65rem 1.5rem;
    font-weight: 700; font-size: 1rem; width: 100%;
    transition: all .25s; box-shadow: 0 4px 16px rgba(102,126,234,.4);
}
div.stButton > button:hover {
    transform: translateY(-2px); box-shadow: 0 8px 28px rgba(102,126,234,.6);
}
.stSelectbox label,.stTextInput label,.stTextArea label,
.stNumberInput label,.stSlider label {
    direction:rtl; text-align:right; color:rgba(255,255,255,.9)!important; font-weight:600;
}
section[data-testid="stSidebar"] { direction: rtl; }
section[data-testid="stSidebar"] .stMarkdown { text-align: right; }
.stTabs [data-baseweb="tab"] { direction:rtl; font-size:1rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# المنهاج الجزائري الكامل
# ─────────────────────────────────────────────────────────────
CURRICULUM = {
    "الطور الابتدائي": {
        "grades": ["السنة الأولى","السنة الثانية","السنة الثالثة",
                   "السنة الرابعة","السنة الخامسة"],
        "subjects": {
            "السنة الأولى":  ["اللغة العربية","الرياضيات","التربية الإسلامية",
                              "التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثانية": ["اللغة العربية","الرياضيات","التربية الإسلامية",
                              "التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثالثة": ["اللغة العربية","الرياضيات","التربية الإسلامية",
                              "التربية المدنية","اللغة الفرنسية",
                              "التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الرابعة": ["اللغة العربية","الرياضيات","التربية الإسلامية",
                              "التربية المدنية","اللغة الفرنسية",
                              "التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الخامسة": ["اللغة العربية","الرياضيات","التربية الإسلامية",
                              "التربية المدنية","اللغة الفرنسية",
                              "التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
        },
        "branches": None,
    },
    "الطور المتوسط": {
        "grades": ["السنة الأولى متوسط","السنة الثانية متوسط",
                   "السنة الثالثة متوسط","السنة الرابعة متوسط (شهادة)"],
        "subjects": {
            "_default": ["اللغة العربية وآدابها","الرياضيات",
                         "العلوم الفيزيائية والتكنولوجية",
                         "العلوم الطبيعية والحياة","التاريخ والجغرافيا",
                         "التربية الإسلامية","التربية المدنية",
                         "اللغة الفرنسية","اللغة الإنجليزية",
                         "التربية التشكيلية","التربية الموسيقية","الإعلام الآلي"]
        },
        "branches": None,
    },
    "الطور الثانوي": {
        "grades": ["السنة الأولى ثانوي (جذع مشترك)",
                   "السنة الثانية ثانوي",
                   "السنة الثالثة ثانوي (بكالوريا)"],
        "subjects": None,
        "branches": {
            "السنة الأولى ثانوي (جذع مشترك)": {
                "جذع مشترك علوم وتكنولوجيا": [
                    "الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية",
                    "التاريخ والجغرافيا","التربية الإسلامية","الإعلام الآلي"],
                "جذع مشترك آداب وفلسفة": [
                    "اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا",
                    "اللغة الفرنسية","اللغة الإنجليزية",
                    "التربية الإسلامية","الرياضيات"],
            },
            "السنة الثانية ثانوي": {
                "شعبة علوم تجريبية": [
                    "الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية",
                    "التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات": [
                    "الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي": [
                    "الرياضيات","العلوم الفيزيائية","التكنولوجيا",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة": [
                    "اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا",
                    "علم الاجتماع والنفس","اللغة الفرنسية",
                    "اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية": [
                    "اللغة الفرنسية","اللغة الإنجليزية","اللغة العربية",
                    "التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد": [
                    "الاقتصاد والمناجمنت","المحاسبة والمالية","الرياضيات",
                    "القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
            "السنة الثالثة ثانوي (بكالوريا)": {
                "شعبة علوم تجريبية": [
                    "الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية",
                    "التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات": [
                    "الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي": [
                    "الرياضيات","العلوم الفيزيائية","التكنولوجيا",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة": [
                    "اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا",
                    "علم الاجتماع والنفس","اللغة الفرنسية",
                    "اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية": [
                    "اللغة الفرنسية","اللغة الإنجليزية","اللغة العربية",
                    "التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد": [
                    "الاقتصاد والمناجمنت","المحاسبة والمالية","الرياضيات",
                    "القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
        },
    },
}


# ─────────────────────────────────────────────────────────────
# قاعدة البيانات SQLite
# ─────────────────────────────────────────────────────────────
DB_PATH = "donia_labs.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT, grade TEXT, branch TEXT,
            subject TEXT, lesson TEXT,
            ex_type TEXT, difficulty TEXT,
            content TEXT, created_at TEXT
        )
    """)
    con.commit(); con.close()

def save_exercise(level, grade, branch, subject, lesson, ex_type, difficulty, content):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO exercises (level,grade,branch,subject,lesson,ex_type,difficulty,content,created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (level, grade, branch, subject, lesson, ex_type, difficulty, content,
         datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    con.commit(); con.close()

def get_exercises(search=""):
    con = sqlite3.connect(DB_PATH)
    if search:
        rows = con.execute(
            "SELECT * FROM exercises WHERE lesson LIKE ? OR subject LIKE ? ORDER BY created_at DESC",
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = con.execute("SELECT * FROM exercises ORDER BY created_at DESC").fetchall()
    con.close()
    return rows

def delete_exercise(ex_id):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM exercises WHERE id=?", (ex_id,))
    con.commit(); con.close()

def get_stats():
    con = sqlite3.connect(DB_PATH)
    total = con.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    subj  = con.execute("SELECT COUNT(DISTINCT subject) FROM exercises").fetchone()[0]
    lvls  = con.execute("SELECT COUNT(DISTINCT level) FROM exercises").fetchone()[0]
    con.close()
    return total, subj, lvls

init_db()


# ─────────────────────────────────────────────────────────────
# مساعدات
# ─────────────────────────────────────────────────────────────
def fix_arabic(text: str) -> str:
    try:
        return get_display(reshape(text))
    except Exception:
        return text

def generate_pdf(content: str, title: str = "تمرين") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    ar_body = ParagraphStyle("ArabicBody", parent=styles["Normal"],
        fontName="Helvetica", fontSize=11,
        alignment=TA_RIGHT, leading=22, spaceAfter=5)
    ar_title = ParagraphStyle("ArabicTitle", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=15,
        alignment=TA_CENTER, leading=24, spaceAfter=10,
        textColor=colors.HexColor("#764ba2"))

    story = [
        Paragraph(fix_arabic(f"DONIA LABS  |  {title}"), ar_title),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#764ba2")),
        Spacer(1, 14),
    ]
    for line in content.splitlines():
        if line.strip():
            if line.strip().startswith("$") or "```" in line:
                line = "[ معادلة رياضية – راجع النص الأصلي ]"
            story.append(Paragraph(fix_arabic(line), ar_body))
            story.append(Spacer(1, 3))
    doc.build(story)
    buf.seek(0)
    return buf.read()

def render_with_latex(text: str):
    parts = re.split(r'(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)', text)
    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            st.latex(part[2:-2].strip())
        elif part.startswith("$") and part.endswith("$"):
            st.latex(part[1:-1].strip())
        elif part.strip():
            st.markdown(
                f'<div style="direction:rtl;text-align:right;'
                f'color:rgba(255,255,255,.92);line-height:2;">{part}</div>',
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────────────────────
# رأس الصفحة
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="title-card">
    <h1>🎓 DONIA LABS</h1>
    <p>المعلم الذكي للمناهج الجزائرية · توليد تمارين بدعم LaTeX + PDF + قاعدة بيانات</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# الشريط الجانبي
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ إعدادات التمرين")
    api_key = os.getenv("GROQ_API_KEY")

    level  = st.selectbox("🏫 الطور التعليمي", list(CURRICULUM.keys()))
    info   = CURRICULUM[level]
    grade  = st.selectbox("📚 السنة الدراسية", info["grades"])

    branch = None
    if info["branches"] and grade in info["branches"]:
        branch = st.selectbox("🎯 الشعبة", list(info["branches"][grade].keys()))

    if info["subjects"]:
        subj_list = info["subjects"].get(grade) or info["subjects"].get("_default", [])
    elif info["branches"] and grade in info["branches"] and branch:
        subj_list = info["branches"][grade][branch]
    else:
        subj_list = []

    subject = (st.selectbox("📖 المادة", subj_list)
               if subj_list else st.text_input("📖 المادة (يدويًا)"))

    ex_type = st.selectbox("🧩 نوع التمرين",
        ["تمرين تطبيقي","مسألة","سؤال إشكالي",
         "تقييم تشخيصي","فرض محروس","اختبار فصلي"])

    difficulty = st.select_slider("⚡ مستوى الصعوبة",
        options=["سهل جداً","سهل","متوسط","صعب","مستوى بكالوريا"])

    model_name = st.selectbox("🤖 النموذج",
        ["llama-3.3-70b-specdec","llama3-70b-8192",
         "mixtral-8x7b-32768","gemma2-9b-it"])

    st.markdown("---")
    st.success("✅ مفتاح API متاح") if api_key else st.error("❌ GROQ_API_KEY غير موجود في .env")


# ─────────────────────────────────────────────────────────────
# التبويبات
# ─────────────────────────────────────────────────────────────
tab_gen, tab_db, tab_stats = st.tabs([
    "✏️ توليد تمرين", "🗄️ قاعدة التمارين", "📊 إحصائيات"
])

# ══════════════════════════════════════════════════
# تبويب 1 – توليد
# ══════════════════════════════════════════════════
with tab_gen:
    c1, c2 = st.columns([4, 1])
    with c1:
        lesson = st.text_input("📝 عنوان الدرس:",
            placeholder="مثال: الانقسام المنصف، المعادلات التفاضلية، الجملة الفعلية…")
    with c2:
        num_ex = st.number_input("عدد التمارين", 1, 5, 1)

    extra = st.text_area("📌 تعليمات إضافية (اختياري):",
        placeholder="مثلاً: ركّز على الجانب التطبيقي، أضف رسومات بيانية…")

    if st.button("🚀 توليد التمرين والحل التفصيلي"):
        if not api_key:
            st.error("⚠️ مفتاح GROQ_API_KEY غير موجود في ملف .env")
        elif not lesson.strip():
            st.warning("⚠️ الرجاء إدخال عنوان الدرس")
        else:
            branch_txt = f" – {branch}" if branch else ""
            llm = ChatGroq(model_name=model_name, groq_api_key=api_key)

            prompt = f"""أنت أستاذ جزائري خبير ومتخصص في إعداد الاختبارات والتمارين
وفق المنهاج الجزائري الرسمي المعتمد من وزارة التربية الوطنية.

المطلوب: صمم {num_ex} {ex_type} للمرحلة التالية:
  • الطور: {level}
  • السنة / الشعبة: {grade}{branch_txt}
  • المادة: {subject}
  • الدرس / الوحدة: {lesson}
  • مستوى الصعوبة: {difficulty}
{f"  • تعليمات إضافية: {extra}" if extra.strip() else ""}

القواعد الإلزامية:
1. اللغة العربية الفصحى السليمة فقط (ما عدا المصطلحات العلمية).
2. كل معادلة: $ للمضمنة، $$ للمستقلة.
3. التزم بالمنهاج الجزائري الرسمي.
4. اتبع الهيكل التالي حرفياً:

---
## التمرين
[المعطيات والمطلوب بوضوح]

## الحل المفصل
[خطوات الحل التفصيلية مرقّمة]

## ملاحظات للأستاذ
[توجيهات تربوية مختصرة]

## كود LaTeX الكامل
```latex
[الكود الجاهز للطباعة]
```
---
"""
            with st.spinner("🧠 جاري التواصل مع الذكاء الاصطناعي…"):
                try:
                    response = llm.invoke(prompt)
                    res_text = response.content

                    st.markdown(f"""
                    <div style="background:rgba(102,126,234,.12);border:1px solid rgba(102,126,234,.35);
                    border-radius:10px;padding:.9rem 1.2rem;direction:rtl;text-align:right;margin-bottom:1rem;">
                        <strong>📋 {ex_type} | {subject} | {grade}{branch_txt} | ⚡ {difficulty}</strong>
                    </div>""", unsafe_allow_html=True)

                    render_with_latex(res_text)

                    save_exercise(level, grade, branch or "", subject,
                                  lesson, ex_type, difficulty, res_text)
                    st.success("✅ تم حفظ التمرين في قاعدة البيانات")

                    dc1, dc2 = st.columns(2)
                    with dc1:
                        st.download_button("📥 تحميل نص",
                            data=res_text.encode("utf-8-sig"),
                            file_name=f"{lesson}_{grade}.txt",
                            mime="text/plain")
                    with dc2:
                        try:
                            pdf_bytes = generate_pdf(res_text, lesson)
                            st.download_button("📄 تحميل PDF",
                                data=pdf_bytes,
                                file_name=f"{lesson}_{grade}.pdf",
                                mime="application/pdf")
                        except Exception as e:
                            st.warning(f"⚠️ PDF غير متاح: {e}")

                except Exception as err:
                    st.error(f"❌ خطأ: {err}")


# ══════════════════════════════════════════════════
# تبويب 2 – قاعدة البيانات
# ══════════════════════════════════════════════════
with tab_db:
    st.markdown("### 🗄️ التمارين المحفوظة")
    search_q  = st.text_input("🔍 بحث:", placeholder="ابحث بعنوان الدرس أو المادة…")
    exercises = get_exercises(search_q)

    if not exercises:
        st.info("لا توجد تمارين محفوظة بعد.")
    else:
        st.caption(f"عدد النتائج: {len(exercises)}")
        for ex in exercises:
            ex_id, lv, gr, br, sub, les, xt, diff, cont, created = ex
            with st.expander(f"📚 {les}  |  {sub}  |  {gr}  |  {diff}  |  🕒 {created}"):
                st.markdown(
                    f'<div class="result-box">{cont[:600]}…</div>',
                    unsafe_allow_html=True)
                ba, bb, bc = st.columns(3)
                with ba:
                    st.download_button("📥 نص", data=cont.encode("utf-8-sig"),
                        file_name=f"{les}.txt", key=f"dl_{ex_id}")
                with bb:
                    try:
                        pdf_b = generate_pdf(cont, les)
                        st.download_button("📄 PDF", data=pdf_b,
                            file_name=f"{les}.pdf", mime="application/pdf",
                            key=f"pdf_{ex_id}")
                    except Exception:
                        pass
                with bc:
                    if st.button("🗑️ حذف", key=f"del_{ex_id}"):
                        delete_exercise(ex_id); st.rerun()


# ══════════════════════════════════════════════════
# تبويب 3 – إحصائيات
# ══════════════════════════════════════════════════
with tab_stats:
    total, subj_count, lvl_count = get_stats()
    st.markdown("### 📊 إحصائيات الاستخدام")
    s1, s2, s3 = st.columns(3)
    for col, val, label, clr in [
        (s1, total,      "إجمالي التمارين",    "#667eea"),
        (s2, subj_count, "المواد المختلفة",    "#764ba2"),
        (s3, lvl_count,  "الأطوار التعليمية", "#f093fb"),
    ]:
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="color:{clr}">{val}</h2>
                <p>{label}</p>
            </div>""", unsafe_allow_html=True)

    last = get_exercises()[:8]
    if last:
        st.markdown("### 📋 آخر التمارين المولّدة")
        for ex in last:
            ex_id, lv, gr, br, sub, les, xt, diff, cont, created = ex
            st.markdown(
                f'<div class="db-item"><strong>{les}</strong>'
                f' &nbsp;|&nbsp; {sub} &nbsp;|&nbsp; {gr}'
                f' &nbsp;|&nbsp; <span style="color:#a78bfa">{diff}</span>'
                f' &nbsp;|&nbsp; <small style="opacity:.7">{created}</small></div>',
                unsafe_allow_html=True)
