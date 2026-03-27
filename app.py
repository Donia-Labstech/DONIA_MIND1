import streamlit as st
import os, sqlite3, re, json, io, base64
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib import colors as rl_colors
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from PIL import Image

load_dotenv()

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DONIA SMART TEACHER",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
*, *::before, *::after { font-family: 'Tajawal', sans-serif !important; }
.stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
.main  { direction: rtl; text-align: right; }

/* ── Title ── */
.title-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.8rem 2rem; border-radius: 20px; text-align: center;
    margin-bottom: 1.5rem; box-shadow: 0 12px 45px rgba(102,126,234,.45);
}
.title-card h1 { color:#fff; font-size:2.2rem; font-weight:800; margin:0; }
.title-card p  { color:rgba(255,255,255,.85); font-size:1rem; margin:.4rem 0 0; }

/* ── Cards ── */
.stat-card {
    background: linear-gradient(135deg,rgba(102,126,234,.15),rgba(118,75,162,.15));
    border: 1px solid rgba(102,126,234,.35); border-radius: 14px;
    padding: 1.2rem; text-align: center; margin-bottom: .8rem;
}
.stat-card h2 { font-size:2rem; margin:0; }
.stat-card p  { margin:0; color:rgba(255,255,255,.7); font-size:.85rem; }

.feature-card {
    background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1);
    border-radius: 14px; padding: 1.4rem; margin: .6rem 0;
    direction: rtl; text-align: right; color: rgba(255,255,255,.92);
}
.feature-card h4 { color:#a78bfa; margin:0 0 .5rem; font-size:1rem; }

.result-box {
    background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.1);
    border-radius: 14px; padding: 1.4rem; direction: rtl; text-align: right;
    color: rgba(255,255,255,.9); line-height: 2; margin: .8rem 0;
}
.db-item {
    background: rgba(255,255,255,.06); border-right: 4px solid #667eea;
    border-radius: 8px; padding: .8rem 1rem; margin: .4rem 0;
    direction: rtl; text-align: right; color: rgba(255,255,255,.9);
}
.error-box {
    background: rgba(220,38,38,.12); border: 1px solid rgba(220,38,38,.4);
    border-radius: 10px; padding: 1rem; direction: rtl; text-align: right;
    color: #fca5a5; margin: .6rem 0;
}
.success-box {
    background: rgba(16,185,129,.1); border: 1px solid rgba(16,185,129,.35);
    border-radius: 10px; padding: 1rem; direction: rtl; text-align: right;
    color: #6ee7b7; margin: .6rem 0;
}
.grade-badge {
    display:inline-block; padding:.3rem .8rem; border-radius:20px;
    font-weight:700; font-size:.9rem; margin:.2rem;
}

/* ── Buttons ── */
div.stButton > button {
    background: linear-gradient(135deg,#667eea,#764ba2); color:#fff;
    border:none; border-radius:10px; padding:.6rem 1.4rem;
    font-weight:700; font-size:.95rem; width:100%;
    transition:all .25s; box-shadow:0 4px 16px rgba(102,126,234,.4);
}
div.stButton > button:hover { transform:translateY(-2px); box-shadow:0 8px 28px rgba(102,126,234,.6); }

/* ── Forms ── */
.stSelectbox label,.stTextInput label,.stTextArea label,
.stNumberInput label,.stSlider label,.stFileUploader label {
    direction:rtl; text-align:right; color:rgba(255,255,255,.9)!important; font-weight:600;
}
section[data-testid="stSidebar"] { direction:rtl; }
section[data-testid="stSidebar"] .stMarkdown { text-align:right; }
.stTabs [data-baseweb="tab"] { direction:rtl; font-size:.95rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# CURRICULUM - المنهاج الجزائري الكامل
# ═══════════════════════════════════════════════════════════
CURRICULUM = {
    "الطور الابتدائي": {
        "grades": ["السنة الأولى","السنة الثانية","السنة الثالثة","السنة الرابعة","السنة الخامسة"],
        "subjects": {
            "السنة الأولى":  ["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثانية": ["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثالثة": ["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الرابعة": ["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الخامسة": ["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
        },
        "branches": None,
    },
    "الطور المتوسط": {
        "grades": ["السنة الأولى متوسط","السنة الثانية متوسط","السنة الثالثة متوسط","السنة الرابعة متوسط (شهادة)"],
        "subjects": {
            "_default": ["اللغة العربية وآدابها","الرياضيات","العلوم الفيزيائية والتكنولوجية","العلوم الطبيعية والحياة","التاريخ والجغرافيا","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","اللغة الإنجليزية","التربية التشكيلية","التربية الموسيقية","الإعلام الآلي"]
        },
        "branches": None,
    },
    "الطور الثانوي": {
        "grades": ["السنة الأولى ثانوي (جذع مشترك)","السنة الثانية ثانوي","السنة الثالثة ثانوي (بكالوريا)"],
        "subjects": None,
        "branches": {
            "السنة الأولى ثانوي (جذع مشترك)": {
                "جذع مشترك علوم وتكنولوجيا": ["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية","الإعلام الآلي"],
                "جذع مشترك آداب وفلسفة": ["اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا","اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية","الرياضيات"],
            },
            "السنة الثانية ثانوي": {
                "شعبة علوم تجريبية": ["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات": ["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي": ["الرياضيات","العلوم الفيزيائية","التكنولوجيا","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة": ["اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا","علم الاجتماع والنفس","اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية": ["اللغة الفرنسية","اللغة الإنجليزية","اللغة العربية","التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد": ["الاقتصاد والمناجمنت","المحاسبة والمالية","الرياضيات","القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
            "السنة الثالثة ثانوي (بكالوريا)": {
                "شعبة علوم تجريبية": ["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات": ["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي": ["الرياضيات","العلوم الفيزيائية","التكنولوجيا","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة": ["اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا","علم الاجتماع والنفس","اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية": ["اللغة الفرنسية","اللغة الإنجليزية","اللغة العربية","التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد": ["الاقتصاد والمناجمنت","المحاسبة والمالية","الرياضيات","القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
        },
    },
}

# نماذج Groq المتاحة (محدّثة – بدون النماذج الموقوفة)
GROQ_MODELS = [
    "llama-3.3-70b-versatile",      # ← بديل llama-3.3-70b-specdec الموقوف
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════
DB_PATH = "donia_smart.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT, grade TEXT, branch TEXT, subject TEXT, lesson TEXT,
        ex_type TEXT, difficulty TEXT, content TEXT, created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS lesson_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT, grade TEXT, subject TEXT, lesson TEXT,
        duration TEXT, content TEXT, created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT, subject TEXT, grade_value REAL,
        total REAL, feedback TEXT, created_at TEXT)""")
    con.commit(); con.close()

def db_exec(sql, params=(), fetch=False):
    con = sqlite3.connect(DB_PATH)
    cur = con.execute(sql, params)
    con.commit()
    result = cur.fetchall() if fetch else None
    con.close()
    return result

def save_exercise(level, grade, branch, subject, lesson, ex_type, difficulty, content):
    db_exec("INSERT INTO exercises (level,grade,branch,subject,lesson,ex_type,difficulty,content,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (level,grade,branch,subject,lesson,ex_type,difficulty,content,datetime.now().strftime("%Y-%m-%d %H:%M")))

def save_lesson_plan(level, grade, subject, lesson, duration, content):
    db_exec("INSERT INTO lesson_plans (level,grade,subject,lesson,duration,content,created_at) VALUES (?,?,?,?,?,?,?)",
            (level,grade,subject,lesson,duration,content,datetime.now().strftime("%Y-%m-%d %H:%M")))

def save_correction(student_name, subject, grade_value, total, feedback):
    db_exec("INSERT INTO corrections (student_name,subject,grade_value,total,feedback,created_at) VALUES (?,?,?,?,?,?)",
            (student_name,subject,grade_value,total,feedback,datetime.now().strftime("%Y-%m-%d %H:%M")))

def get_exercises(search=""):
    if search:
        return db_exec("SELECT * FROM exercises WHERE lesson LIKE ? OR subject LIKE ? ORDER BY created_at DESC",
                       (f"%{search}%",f"%{search}%"), fetch=True) or []
    return db_exec("SELECT * FROM exercises ORDER BY created_at DESC", fetch=True) or []

def get_lesson_plans():
    return db_exec("SELECT * FROM lesson_plans ORDER BY created_at DESC", fetch=True) or []

def get_corrections():
    return db_exec("SELECT * FROM corrections ORDER BY created_at DESC", fetch=True) or []

def delete_exercise(ex_id):
    db_exec("DELETE FROM exercises WHERE id=?", (ex_id,))

def get_stats():
    total = (db_exec("SELECT COUNT(*) FROM exercises", fetch=True) or [(0,)])[0][0]
    subj  = (db_exec("SELECT COUNT(DISTINCT subject) FROM exercises", fetch=True) or [(0,)])[0][0]
    plans = (db_exec("SELECT COUNT(*) FROM lesson_plans", fetch=True) or [(0,)])[0][0]
    corr  = (db_exec("SELECT COUNT(*) FROM corrections", fetch=True) or [(0,)])[0][0]
    return total, subj, plans, corr

init_db()

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def fix_arabic(text: str) -> str:
    try: return get_display(reshape(str(text)))
    except: return str(text)

def get_llm(model_name: str, api_key: str):
    return ChatGroq(model_name=model_name, groq_api_key=api_key, temperature=0.7)

def call_llm(llm, prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content

def render_with_latex(text: str):
    parts = re.split(r'(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)', text)
    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            st.latex(part[2:-2].strip())
        elif part.startswith("$") and part.endswith("$"):
            st.latex(part[1:-1].strip())
        elif part.strip():
            st.markdown(f'<div style="direction:rtl;text-align:right;color:rgba(255,255,255,.92);line-height:2;">{part}</div>',
                        unsafe_allow_html=True)

def image_to_base64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")

# ── PDF GENERATOR ──────────────────────────────────────────
def generate_pdf(content: str, title: str = "وثيقة", subtitle: str = "") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    ar_body  = ParagraphStyle("AB", parent=styles["Normal"], fontName="Helvetica", fontSize=11,
                               alignment=TA_RIGHT, leading=22, spaceAfter=4)
    ar_title = ParagraphStyle("AT", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=16,
                               alignment=TA_CENTER, leading=24, spaceAfter=6,
                               textColor=rl_colors.HexColor("#764ba2"))
    ar_sub   = ParagraphStyle("AS", parent=styles["Normal"], fontName="Helvetica", fontSize=11,
                               alignment=TA_CENTER, leading=18, spaceAfter=10,
                               textColor=rl_colors.HexColor("#667eea"))
    story = [
        Paragraph(fix_arabic(f"DONIA SMART TEACHER  |  {title}"), ar_title),
    ]
    if subtitle:
        story.append(Paragraph(fix_arabic(subtitle), ar_sub))
    story += [HRFlowable(width="100%", thickness=1.5, color=rl_colors.HexColor("#764ba2")), Spacer(1,12)]
    for line in content.splitlines():
        line = line.strip()
        if line:
            if line.startswith("$") or "```" in line:
                line = "[ معادلة / كود – راجع النسخة الرقمية ]"
            story.append(Paragraph(fix_arabic(line), ar_body))
            story.append(Spacer(1,2))
    doc.build(story)
    buf.seek(0); return buf.read()

# ── GOOGLE DRIVE UPLOAD (requires credentials) ─────────────
def upload_to_drive(file_bytes: bytes, filename: str, creds_json: dict) -> str:
    """Upload bytes to Google Drive, return shareable link."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        from googleapiclient.http import MediaIoBaseUpload
        creds = Credentials.from_service_account_info(creds_json,
                    scopes=["https://www.googleapis.com/auth/drive.file"])
        service = build("drive","v3",credentials=creds)
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="application/pdf")
        file_meta = {"name": filename}
        f = service.files().create(body=file_meta, media_body=media, fields="id").execute()
        fid = f.get("id")
        service.permissions().create(fileId=fid,
            body={"type":"anyone","role":"reader"}).execute()
        return f"https://drive.google.com/file/d/{fid}/view"
    except Exception as e:
        return f"خطأ في الرفع: {e}"

# ── FIREBASE SAVE ───────────────────────────────────────────
def save_to_firebase(data: dict, collection: str, firebase_config: dict) -> bool:
    """Save document to Firebase Firestore."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        db.collection(collection).add(data)
        return True
    except Exception as e:
        st.warning(f"Firebase: {e}")
        return False

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ الإعدادات العامة")
    api_key = os.getenv("GROQ_API_KEY","")

    level = st.selectbox("🏫 الطور التعليمي", list(CURRICULUM.keys()))
    info  = CURRICULUM[level]
    grade = st.selectbox("📚 السنة الدراسية", info["grades"])

    branch = None
    if info["branches"] and grade in info["branches"]:
        branch = st.selectbox("🎯 الشعبة", list(info["branches"][grade].keys()))

    if info["subjects"]:
        subj_list = info["subjects"].get(grade) or info["subjects"].get("_default",[])
    elif info["branches"] and grade in info["branches"] and branch:
        subj_list = info["branches"][grade][branch]
    else:
        subj_list = []

    subject = st.selectbox("📖 المادة", subj_list) if subj_list else st.text_input("📖 المادة")

    model_name = st.selectbox("🤖 نموذج الذكاء الاصطناعي", GROQ_MODELS)

    st.markdown("---")
    # Status
    if api_key:
        st.markdown('<div class="success-box">✅ مفتاح Groq API متاح</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">❌ GROQ_API_KEY غير موجود في .env</div>', unsafe_allow_html=True)

    # Cloud settings expander
    with st.expander("☁️ إعدادات السحابة"):
        st.caption("Google Drive Service Account JSON")
        drive_json = st.text_area("مفتاح Drive (JSON)", height=80,
                                   placeholder='{"type":"service_account",...}')
        st.caption("Firebase Service Account JSON")
        firebase_json = st.text_area("مفتاح Firebase (JSON)", height=80,
                                      placeholder='{"type":"service_account",...}')

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div class="title-card">
    <h1>🎓 DONIA SMART TEACHER</h1>
    <p>المعلم الذكي · توليد تمارين · مذكرات · تصحيح أوراق · تحليل النتائج · دعم السحابة</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════
(tab_ex, tab_plan, tab_correct, tab_analyze,
 tab_db, tab_stats) = st.tabs([
    "✏️ توليد تمرين",
    "📝 مذكرة الدرس",
    "✅ تصحيح أوراق",
    "📊 تحليل النتائج",
    "🗄️ الأرشيف",
    "📈 إحصائيات",
])

# ══════════════════════════════════════════════════
# TAB 1 — توليد تمرين
# ══════════════════════════════════════════════════
with tab_ex:
    st.markdown("### ✏️ توليد تمرين مع الحل التفصيلي")
    c1, c2, c3 = st.columns([4, 1, 1])
    with c1:
        lesson = st.text_input("📝 عنوان الدرس:",
            placeholder="مثال: الانقسام المنصف، المعادلات التفاضلية…",
            key="ex_lesson")
    with c2:
        num_ex = st.number_input("عدد التمارين", 1, 5, 1, key="ex_num")
    with c3:
        ex_type = st.selectbox("النوع",
            ["تمرين تطبيقي","مسألة","سؤال إشكالي","فرض محروس","اختبار فصلي"],
            key="ex_type")
    difficulty = st.select_slider("⚡ مستوى الصعوبة",
        options=["سهل جداً","سهل","متوسط","صعب","مستوى بكالوريا"],
        key="ex_difficulty")
    extra = st.text_area("📌 تعليمات إضافية:", placeholder="أي توجيهات خاصة…",
        key="ex_extra")

    col_btn, col_save = st.columns([3,1])
    with col_btn:
        gen_btn = st.button("🚀 توليد التمرين والحل التفصيلي", key="btn_gen_ex")

    if gen_btn:
        if not api_key:
            st.error("⚠️ أضف GROQ_API_KEY إلى ملف .env")
        elif not lesson.strip():
            st.warning("⚠️ أدخل عنوان الدرس")
        else:
            branch_txt = f" – {branch}" if branch else ""
            prompt = f"""أنت أستاذ جزائري خبير وفق المنهاج الجزائري الرسمي.

صمم {num_ex} {ex_type} لـ:
• الطور: {level} | السنة: {grade}{branch_txt}
• المادة: {subject} | الدرس: {lesson}
• الصعوبة: {difficulty}
{f'• ملاحظات: {extra}' if extra.strip() else ''}

القواعد:
1. اللغة العربية الفصحى فقط.
2. المعادلات بتنسيق LaTeX: $ للمضمنة، $$ للمستقلة.
3. اتبع الهيكل التالي حرفياً:

## التمرين
[المعطيات والمطلوب]

## الحل المفصل
[خطوات مرقمة]

## ملاحظات للأستاذ
[توجيهات تربوية]

## كود LaTeX الكامل
```latex
[الكود]
```"""
            with st.spinner("🧠 جاري التوليد…"):
                try:
                    llm = get_llm(model_name, api_key)
                    res_text = call_llm(llm, prompt)
                    st.markdown(f'<div class="feature-card"><h4>📋 {ex_type} | {subject} | {grade}{branch_txt} | ⚡ {difficulty}</h4></div>',
                                unsafe_allow_html=True)
                    render_with_latex(res_text)
                    save_exercise(level, grade, branch or "", subject, lesson, ex_type, difficulty, res_text)
                    st.success("✅ تم الحفظ في قاعدة البيانات المحلية")

                    # Download buttons
                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.download_button("📥 تحميل نص", res_text.encode("utf-8-sig"),
                                           f"{lesson}.txt", "text/plain", key="dl_ex_txt")
                    with d2:
                        pdf_b = generate_pdf(res_text, lesson, f"{subject} | {grade}")
                        st.download_button("📄 تحميل PDF", pdf_b, f"{lesson}.pdf",
                                           "application/pdf", key="dl_ex_pdf")
                    with d3:
                        # Google Drive upload
                        if drive_json and drive_json.strip().startswith("{"):
                            if st.button("☁️ رفع إلى Drive", key="btn_drive_ex"):
                                try:
                                    creds = json.loads(drive_json)
                                    link = upload_to_drive(pdf_b, f"{lesson}.pdf", creds)
                                    st.success(f"[رابط Drive]({link})")
                                except Exception as e:
                                    st.error(f"Drive: {e}")
                        else:
                            st.caption("أضف مفتاح Drive في الإعدادات")

                    # Firebase backup
                    if firebase_json and firebase_json.strip().startswith("{"):
                        try:
                            creds_fb = json.loads(firebase_json)
                            save_to_firebase({
                                "level":level,"grade":grade,"subject":subject,
                                "lesson":lesson,"content":res_text,
                                "created_at":datetime.now().isoformat()
                            }, "exercises", creds_fb)
                            st.info("☁️ نسخة احتياطية محفوظة في Firebase")
                        except Exception:
                            pass

                except Exception as err:
                    st.markdown(f'<div class="error-box">❌ خطأ: {err}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# TAB 2 — مذكرة الدرس
# ══════════════════════════════════════════════════
with tab_plan:
    st.markdown("### 📝 إعداد مذكرة الدرس")
    st.markdown('<div class="feature-card"><h4>📋 مذكرة وفق الصيغة الرسمية الجزائرية</h4>تُولّد المذكرة بهيكل رسمي: المعلومات العامة، الأهداف، المكتسبات القبلية، سير الدرس، التقييم.</div>', unsafe_allow_html=True)

    pm1, pm2 = st.columns(2)
    with pm1:
        lesson_plan = st.text_input("📝 عنوان الدرس:", placeholder="مثال: الدالة الأسية…",
                                     key="plan_lesson")
        duration    = st.selectbox("⏱️ مدة الحصة", ["50 دقيقة","1 ساعة","1.5 ساعة","2 ساعة"],
                                    key="plan_duration")
    with pm2:
        session_type = st.selectbox("نوع الحصة", ["درس نظري","أعمال موجهة","أعمال تطبيقية","تقييم تشخيصي"],
                                     key="plan_session_type")
        objectives_count = st.slider("عدد الأهداف التعلمية", 2, 6, 3, key="plan_objectives")

    plan_notes = st.text_area("ملاحظات خاصة للمذكرة:", placeholder="مثلاً: الفوج يضم تلاميذ ضعاف، التركيز على الجانب التطبيقي…",
                               key="plan_notes")

    if st.button("📝 توليد المذكرة الكاملة", key="btn_gen_plan"):
        if not api_key:
            st.error("⚠️ أضف GROQ_API_KEY")
        elif not lesson_plan.strip():
            st.warning("⚠️ أدخل عنوان الدرس")
        else:
            branch_txt = f" – {branch}" if branch else ""
            prompt = f"""أنت أستاذ جزائري خبير. أعدّ مذكرة درس رسمية وفق المنهاج الجزائري.

المعلومات:
• الطور: {level} | السنة: {grade}{branch_txt}
• المادة: {subject} | الدرس: {lesson_plan}
• نوع الحصة: {session_type} | المدة: {duration}
• عدد الأهداف التعلمية: {objectives_count}
{f'• ملاحظات: {plan_notes}' if plan_notes.strip() else ''}

اتبع هذا الهيكل الرسمي حرفياً:

═══════════════════════════════
📌 المعلومات العامة
═══════════════════════════════
المادة: {subject}
المستوى: {grade}{branch_txt}
الوحدة / المجال: [اكتب الوحدة]
عنوان الدرس: {lesson_plan}
نوع الحصة: {session_type}
المدة الزمنية: {duration}
الأستاذ: .......................
التاريخ: .......................

═══════════════════════════════
🎯 الكفاءات والأهداف التعلمية
═══════════════════════════════
الكفاءة الختامية: [اكتب الكفاءة]
الأهداف التعلمية:
{chr(10).join([f'{i+1}. [هدف {i+1}]' for i in range(objectives_count)])}

═══════════════════════════════
📚 المكتسبات القبلية والوسائل
═══════════════════════════════
المكتسبات القبلية: [المعارف السابقة المطلوبة]
الوسائل والأدوات: [الكتاب المدرسي، السبورة، ...]

═══════════════════════════════
📋 سير الدرس (الخطوات التفصيلية)
═══════════════════════════════
المرحلة الأولى - التهيئة والتمهيد (5-10 دقائق):
[النشاط التهيئي]

المرحلة الثانية - بناء التعلم ({duration}):
[محتوى الدرس التفصيلي مع الأمثلة والمعادلات LaTeX]

المرحلة الثالثة - الترسيخ والتطبيق:
[تمرين تطبيقي مع الحل]

═══════════════════════════════
✅ التقويم
═══════════════════════════════
تقويم تكويني: [سؤال أو نشاط تقييمي]
أثر الحصة: [ما يُستخلص]
الواجب المنزلي: [إن وجد]

═══════════════════════════════
📝 ملاحظات الأستاذ
═══════════════════════════════
[توجيهات بيداغوجية ومقترحات للتكيف]"""

            with st.spinner("📝 جاري إعداد المذكرة…"):
                try:
                    llm = get_llm(model_name, api_key)
                    plan_text = call_llm(llm, prompt)
                    render_with_latex(plan_text)
                    save_lesson_plan(level, grade, subject, lesson_plan, duration, plan_text)
                    st.success("✅ تم حفظ المذكرة")

                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button("📥 تحميل المذكرة (نص)", plan_text.encode("utf-8-sig"),
                                           f"مذكرة_{lesson_plan}.txt", key="dl_plan_txt")
                    with d2:
                        pdf_p = generate_pdf(plan_text, f"مذكرة درس: {lesson_plan}", f"{subject} | {grade}")
                        st.download_button("📄 تحميل المذكرة (PDF)", pdf_p,
                                           f"مذكرة_{lesson_plan}.pdf", "application/pdf",
                                           key="dl_plan_pdf")
                except Exception as err:
                    st.markdown(f'<div class="error-box">❌ {err}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# TAB 3 — تصحيح أوراق
# ══════════════════════════════════════════════════
with tab_correct:
    st.markdown("### ✅ تصحيح الأوراق وتحليل الإجابات")

    correct_mode = st.radio("وضع التصحيح:", ["📝 إدخال نصي","🖼️ رفع صورة ورقة الطالب"],
                             horizontal=True, key="correct_mode")

    cc1, cc2 = st.columns(2)
    with cc1:
        student_name = st.text_input("اسم الطالب:", placeholder="اختياري", key="corr_name")
        exam_subject = st.text_input("المادة / الموضوع:", value=subject, key="corr_subject")
    with cc2:
        total_marks = st.number_input("العلامة الكاملة:", 10, 100, 20, key="corr_total")
        correct_style = st.selectbox("أسلوب التصحيح:",
            ["تصحيح شامل مع تعليقات","تصحيح مختصر","تحديد الأخطاء فقط","مقارنة مع الحل النموذجي"],
            key="corr_style")

    if correct_mode == "📝 إدخال نصي":
        model_answer = st.text_area("✍️ الحل النموذجي / السؤال:", height=150,
                                     placeholder="أدخل السؤال أو الحل النموذجي…",
                                     key="corr_model_ans")
        student_answer = st.text_area("📄 إجابة الطالب:", height=150,
                                       placeholder="انسخ إجابة الطالب هنا…",
                                       key="corr_student_ans")
        correct_btn = st.button("✅ تصحيح الإجابة", key="btn_correct")
        if correct_btn:
            if not api_key:
                st.error("⚠️ أضف GROQ_API_KEY")
            elif not student_answer.strip():
                st.warning("⚠️ أدخل إجابة الطالب")
            else:
                prompt = f"""أنت أستاذ جزائري خبير في التصحيح البيداغوجي.
صحّح إجابة الطالب بأسلوب: {correct_style}

المادة: {exam_subject}
العلامة الكاملة: {total_marks}
الحل النموذجي / السؤال: {model_answer if model_answer.strip() else 'غير محدد، قيّم الإجابة من حيث المنطق والصحة العلمية'}
إجابة الطالب: {student_answer}

الهيكل المطلوب:
## التقييم الكلي
العلامة المقترحة: X/{total_marks}
النسبة المئوية: Y%
المستوى: [ممتاز/جيد جداً/جيد/مقبول/ضعيف]

## نقاط القوة
[ما أجاد فيه الطالب]

## الأخطاء والنواقص
[تفصيل كل خطأ مع الشرح]

## التوصيات
[توجيهات للطالب للتحسين]

## ملاحظة للأستاذ
[ملاحظة بيداغوجية مختصرة]"""
                with st.spinner("🔍 جاري التصحيح…"):
                    try:
                        llm = get_llm(model_name, api_key)
                        correction = call_llm(llm, prompt)
                        render_with_latex(correction)

                        # Extract grade
                        grade_match = re.search(r'(\d+(?:\.\d+)?)\s*/' + str(total_marks), correction)
                        grade_val = float(grade_match.group(1)) if grade_match else 0.0
                        save_correction(student_name or "مجهول", exam_subject, grade_val, total_marks, correction)
                        st.success(f"✅ تم الحفظ | العلامة: {grade_val}/{total_marks}")

                        pdf_c = generate_pdf(correction, f"تصحيح: {student_name or 'طالب'}", exam_subject)
                        st.download_button("📄 تحميل التصحيح PDF", pdf_c,
                                           f"تصحيح_{student_name or 'طالب'}.pdf", "application/pdf",
                                           key="dl_corr_pdf")
                    except Exception as err:
                        st.markdown(f'<div class="error-box">❌ {err}</div>', unsafe_allow_html=True)

    else:  # Image mode
        uploaded_img = st.file_uploader("📸 ارفع صورة ورقة الطالب:", type=["jpg","jpeg","png"],
                                         key="corr_img_upload")
        if uploaded_img:
            img = Image.open(uploaded_img)
            st.image(img, caption="ورقة الطالب", width=400)
            extra_instructions = st.text_area("تعليمات إضافية:", placeholder="مثلاً: السؤال كان عن…",
                                               key="corr_img_extra")

            if st.button("✅ تصحيح الورقة بالذكاء الاصطناعي", key="btn_correct_img"):
                if not api_key:
                    st.error("⚠️ أضف GROQ_API_KEY")
                else:
                    # Convert image to base64 for vision (note: Groq supports vision on some models)
                    img_bytes = uploaded_img.getvalue()
                    b64_img = image_to_base64(img_bytes)
                    prompt_vision = f"""أنت أستاذ جزائري. صحّح ورقة الطالب في الصورة.
المادة: {exam_subject} | العلامة الكاملة: {total_marks}
{f'ملاحظة: {extra_instructions}' if extra_instructions.strip() else ''}
قدّم: العلامة المقترحة، الأخطاء المكتشفة، التوصيات."""
                    with st.spinner("🔍 جاري تحليل الصورة…"):
                        try:
                            # Use text description approach since Groq vision may be limited
                            llm = get_llm(model_name, api_key)
                            correction = call_llm(llm,
                                f"[صورة ورقة طالب] {prompt_vision}\n"
                                f"(لا يمكن معالجة الصورة مباشرة، يرجى نسخ إجابة الطالب في وضع النص)")
                            st.info("💡 للحصول على تصحيح دقيق، استخدم وضع 'إدخال نصي' وانسخ إجابة الطالب.")
                            render_with_latex(correction)
                        except Exception as err:
                            st.markdown(f'<div class="error-box">❌ {err}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# TAB 4 — تحليل النتائج
# ══════════════════════════════════════════════════
with tab_analyze:
    st.markdown("### 📊 تحليل نتائج الفوج")

    analyze_mode = st.radio("مصدر البيانات:", ["📋 إدخال يدوي","📁 رفع ملف CSV","📂 من قاعدة التصحيحات"],
                             horizontal=True, key="analyze_mode")

    if analyze_mode == "📋 إدخال يدوي":
        st.markdown("**أدخل علامات التلاميذ (اسم, علامة) – سطر لكل تلميذ:**")
        grades_input = st.text_area("",
            placeholder="أحمد, 15\nفاطمة, 18\nعلي, 12\nسارة, 9\nمحمد, 14",
            height=200, key="analyze_grades_input")
        total_an = st.number_input("العلامة الكاملة:", 10, 100, 20, key="analyze_total")

        if st.button("📊 تحليل النتائج", key="btn_analyze"):
            if not grades_input.strip():
                st.warning("أدخل البيانات أولاً")
            else:
                rows = []
                for line in grades_input.strip().splitlines():
                    parts = line.split(",")
                    if len(parts) >= 2:
                        try:
                            rows.append({"الاسم": parts[0].strip(), "العلامة": float(parts[1].strip())})
                        except ValueError:
                            pass
                if rows:
                    df = pd.DataFrame(rows)
                    df["النسبة"] = (df["العلامة"] / total_an * 100).round(1)
                    df["التقدير"] = df["العلامة"].apply(lambda x:
                        "ممتاز" if x >= total_an*0.9 else
                        "جيد جداً" if x >= total_an*0.75 else
                        "جيد" if x >= total_an*0.65 else
                        "مقبول" if x >= total_an*0.5 else "ضعيف")

                    # Stats
                    a1,a2,a3,a4 = st.columns(4)
                    for col, val, lbl, clr in [
                        (a1, f"{df['العلامة'].mean():.2f}/{total_an}", "المعدل العام", "#667eea"),
                        (a2, f"{df['العلامة'].max()}/{total_an}", "أعلى علامة", "#10b981"),
                        (a3, f"{df['العلامة'].min()}/{total_an}", "أدنى علامة", "#ef4444"),
                        (a4, f"{len(df[df['العلامة'] >= total_an*0.5])}/{len(df)}", "الناجحون", "#f59e0b"),
                    ]:
                        with col:
                            st.markdown(f'<div class="stat-card"><h2 style="color:{clr}">{val}</h2><p>{lbl}</p></div>',
                                        unsafe_allow_html=True)

                    # Charts
                    ch1, ch2 = st.columns(2)
                    with ch1:
                        fig_bar = px.bar(df, x="الاسم", y="العلامة",
                            color="التقدير",
                            color_discrete_map={"ممتاز":"#10b981","جيد جداً":"#3b82f6","جيد":"#667eea","مقبول":"#f59e0b","ضعيف":"#ef4444"},
                            title="علامات التلاميذ",
                            template="plotly_dark")
                        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_bar, use_container_width=True)
                    with ch2:
                        grade_counts = df["التقدير"].value_counts()
                        fig_pie = px.pie(values=grade_counts.values, names=grade_counts.index,
                            title="توزيع التقديرات", template="plotly_dark",
                            color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_pie, use_container_width=True)

                    # Histogram
                    fig_hist = px.histogram(df, x="العلامة", nbins=10,
                        title="توزيع العلامات", template="plotly_dark",
                        color_discrete_sequence=["#667eea"])
                    fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_hist, use_container_width=True)

                    # Table
                    st.dataframe(df.style.background_gradient(subset=["العلامة"], cmap="RdYlGn"),
                                 use_container_width=True)

                    # AI Analysis
                    if api_key and st.button("🤖 تحليل ذكي للنتائج", key="btn_ai_analyze"):
                        summary = df.to_string(index=False)
                        prompt_an = f"""أنت مستشار بيداغوجي جزائري. حلّل نتائج الفوج التالية:
{summary}
العلامة الكاملة: {total_an}
المادة: {subject}

قدّم:
1. تشخيص عام للمستوى
2. الفئات التي تحتاج دعماً
3. توصيات بيداغوجية محددة
4. اقتراح خطة علاجية مختصرة"""
                        with st.spinner("🧠 جاري التحليل…"):
                            try:
                                llm = get_llm(model_name, api_key)
                                analysis = call_llm(llm, prompt_an)
                                st.markdown("---")
                                st.markdown("#### 🤖 التحليل البيداغوجي")
                                render_with_latex(analysis)
                                pdf_an = generate_pdf(analysis, "تحليل النتائج", subject)
                                st.download_button("📄 تصدير التقرير PDF", pdf_an,
                                                   "تحليل_النتائج.pdf", "application/pdf",
                                                   key="dl_analyze_pdf")
                            except Exception as e:
                                st.error(str(e))

    elif analyze_mode == "📁 رفع ملف CSV":
        csv_file = st.file_uploader("📁 ارفع ملف CSV (الاسم, العلامة):", type=["csv"],
                                     key="analyze_csv_upload")
        if csv_file:
            try:
                df_csv = pd.read_csv(csv_file)
                st.dataframe(df_csv.head(), use_container_width=True)
                st.success(f"✅ تم رفع {len(df_csv)} سجل")
            except Exception as e:
                st.error(f"خطأ في قراءة الملف: {e}")

    else:  # From DB
        corrections = get_corrections()
        if not corrections:
            st.info("لا توجد تصحيحات محفوظة بعد.")
        else:
            df_corr = pd.DataFrame(corrections,
                columns=["id","الاسم","المادة","العلامة","من","الملاحظات","التاريخ"])
            df_corr = df_corr[["الاسم","المادة","العلامة","من","التاريخ"]]
            st.dataframe(df_corr, use_container_width=True)
            fig = px.scatter(df_corr, x="الاسم", y="العلامة",
                color="المادة", title="نتائج التصحيحات المحفوظة",
                template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════
# TAB 5 — الأرشيف
# ══════════════════════════════════════════════════
with tab_db:
    st.markdown("### 🗄️ أرشيف التمارين والمذكرات")
    arch_tab1, arch_tab2 = st.tabs(["📚 التمارين", "📝 المذكرات"])

    with arch_tab1:
        search_q = st.text_input("🔍 بحث:", placeholder="ابحث بعنوان أو مادة…", key="db_search")
        exercises = get_exercises(search_q)
        if not exercises:
            st.info("لا توجد تمارين محفوظة.")
        else:
            st.caption(f"النتائج: {len(exercises)}")
            for ex in exercises:
                ex_id, lv, gr, br, sub, les, xt, diff, cont, created = ex
                with st.expander(f"📚 {les} | {sub} | {gr} | {diff} | 🕒 {created}"):
                    st.markdown(f'<div class="result-box">{cont[:500]}…</div>', unsafe_allow_html=True)
                    b1,b2,b3 = st.columns(3)
                    with b1:
                        st.download_button("📥 نص", cont.encode("utf-8-sig"),
                                           f"{les}.txt", key=f"dl_{ex_id}")
                    with b2:
                        pdf_ex = generate_pdf(cont, les)
                        st.download_button("📄 PDF", pdf_ex, f"{les}.pdf",
                                           "application/pdf", key=f"pdf_{ex_id}")
                    with b3:
                        if st.button("🗑️ حذف", key=f"del_{ex_id}"):
                            delete_exercise(ex_id); st.rerun()

    with arch_tab2:
        plans = get_lesson_plans()
        if not plans:
            st.info("لا توجد مذكرات محفوظة.")
        else:
            for p in plans:
                pid, lv, gr, sub, les, dur, cont, created = p
                with st.expander(f"📝 {les} | {sub} | {gr} | ⏱️ {dur} | 🕒 {created}"):
                    st.markdown(f'<div class="result-box">{cont[:400]}…</div>', unsafe_allow_html=True)
                    pp1, pp2 = st.columns(2)
                    with pp1:
                        st.download_button("📥 نص", cont.encode("utf-8-sig"),
                                           f"مذكرة_{les}.txt", key=f"plan_dl_{pid}")
                    with pp2:
                        pdf_pl = generate_pdf(cont, f"مذكرة: {les}", f"{sub} | {gr}")
                        st.download_button("📄 PDF", pdf_pl,
                                           f"مذكرة_{les}.pdf","application/pdf",key=f"plan_pdf_{pid}")

# ══════════════════════════════════════════════════
# TAB 6 — إحصائيات
# ══════════════════════════════════════════════════
with tab_stats:
    st.markdown("### 📈 إحصائيات الاستخدام")
    total, subj_cnt, plans_cnt, corr_cnt = get_stats()

    s1,s2,s3,s4 = st.columns(4)
    for col, val, lbl, clr in [
        (s1, total,    "التمارين المولّدة",   "#667eea"),
        (s2, subj_cnt, "المواد المستخدمة",    "#764ba2"),
        (s3, plans_cnt,"المذكرات المعدّة",     "#10b981"),
        (s4, corr_cnt, "الأوراق المصحّحة",    "#f59e0b"),
    ]:
        with col:
            st.markdown(f'<div class="stat-card"><h2 style="color:{clr}">{val}</h2><p>{lbl}</p></div>',
                        unsafe_allow_html=True)

    # Charts from DB
    exercises = get_exercises()
    if exercises:
        df_ex = pd.DataFrame(exercises,
            columns=["id","level","grade","branch","subject","lesson","ex_type","difficulty","content","created_at"])

        ch1, ch2 = st.columns(2)
        with ch1:
            subj_count = df_ex["subject"].value_counts().reset_index()
            subj_count.columns = ["المادة","العدد"]
            fig_s = px.bar(subj_count, x="المادة", y="العدد",
                title="التمارين حسب المادة", template="plotly_dark",
                color_discrete_sequence=["#667eea"])
            fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_s, use_container_width=True)

        with ch2:
            diff_count = df_ex["difficulty"].value_counts().reset_index()
            diff_count.columns = ["الصعوبة","العدد"]
            fig_d = px.pie(diff_count, values="العدد", names="الصعوبة",
                title="توزيع مستويات الصعوبة", template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_d.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_d, use_container_width=True)

    # Recent
    last = get_exercises()[:5]
    if last:
        st.markdown("### 📋 آخر التمارين")
        for ex in last:
            ex_id, lv, gr, br, sub, les, xt, diff, cont, created = ex
            st.markdown(
                f'<div class="db-item"><strong>{les}</strong> &nbsp;|&nbsp; {sub} '
                f'&nbsp;|&nbsp; {gr} &nbsp;|&nbsp; '
                f'<span style="color:#a78bfa">{diff}</span> '
                f'&nbsp;|&nbsp; <small style="opacity:.7">{created}</small></div>',
                unsafe_allow_html=True)

    # Cloud Status
    st.markdown("---")
    st.markdown("### ☁️ حالة الربط بالسحابة")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        if drive_json and drive_json.strip().startswith("{"):
            st.markdown('<div class="success-box">✅ Google Drive: متصل</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">❌ Google Drive: غير متصل – أضف المفتاح في الإعدادات</div>', unsafe_allow_html=True)
    with c_col2:
        if firebase_json and firebase_json.strip().startswith("{"):
            st.markdown('<div class="success-box">✅ Firebase: متصل</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">❌ Firebase: غير متصل – أضف المفتاح في الإعدادات</div>', unsafe_allow_html=True)
