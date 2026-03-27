"""
DONIA SMART TEACHER - النسخة الشاملة
المعلم الذكي للمنظومة التربوية الجزائرية
"""
import streamlit as st
import os, sqlite3, re, json, io, base64
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from PIL import Image
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 HRFlowable, Table, TableStyle, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display

load_dotenv()

# خطوط PDF العربية (Amiri/Cairo) — ضع ملفات .ttf داخل مجلد fonts بجانب app.py
_AR_FONT_MAIN = "Helvetica"
_AR_FONT_BOLD = "Helvetica-Bold"
_AR_FONTS_TRIED = False

def _register_arabic_pdf_fonts():
    """تسجيل خطوط TrueType للعربية في ReportLab إن وُجدت (بدون إلزام المستخدم)."""
    global _AR_FONT_MAIN, _AR_FONT_BOLD, _AR_FONTS_TRIED
    if _AR_FONTS_TRIED:
        return
    _AR_FONTS_TRIED = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(base_dir, "fonts")
    reg = []
    for label, fname in (
        ("Amiri", "Amiri-Regular.ttf"),
        ("Amiri-Bold", "Amiri-Bold.ttf"),
        ("Cairo", "Cairo-Regular.ttf"),
        ("Cairo-Bold", "Cairo-Bold.ttf"),
    ):
        p = os.path.join(font_dir, fname)
        if os.path.isfile(p):
            try:
                pdfmetrics.registerFont(TTFont(label, p))
                reg.append(label)
            except Exception:
                pass
    if "Cairo" in reg:
        _AR_FONT_MAIN = "Cairo"
        _AR_FONT_BOLD = "Cairo-Bold" if "Cairo-Bold" in reg else "Cairo"
    elif "Amiri" in reg:
        _AR_FONT_MAIN = "Amiri"
        _AR_FONT_BOLD = "Amiri-Bold" if "Amiri-Bold" in reg else "Amiri"

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title="DONIA SMART TEACHER",page_icon="🎓",
                   layout="wide",initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;600;700;800&family=Tajawal:wght@400;500;700;800&display=swap');
*,*::before,*::after{font-family:'Cairo','Amiri','Tajawal',sans-serif!important}
.stApp{background:linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%)}
.main{direction:rtl;text-align:right}
.title-card{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
  padding:1.6rem 2rem;border-radius:20px;text-align:center;
  margin-bottom:1.4rem;box-shadow:0 12px 45px rgba(102,126,234,.45)}
.title-card h1{color:#fff;font-size:2rem;font-weight:800;margin:0}
.title-card p{color:rgba(255,255,255,.85);font-size:.95rem;margin:.4rem 0 0}
.stat-card{background:linear-gradient(135deg,rgba(102,126,234,.15),rgba(118,75,162,.15));
  border:1px solid rgba(102,126,234,.35);border-radius:14px;
  padding:1rem;text-align:center;margin-bottom:.7rem}
.stat-card h2{font-size:1.9rem;margin:0}
.stat-card p{margin:0;color:rgba(255,255,255,.7);font-size:.85rem}
.feature-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
  border-radius:14px;padding:1.2rem;margin:.5rem 0;
  direction:rtl;text-align:right;color:rgba(255,255,255,.92)}
.feature-card h4{color:#a78bfa;margin:0 0 .4rem;font-size:1rem}
.result-box{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);
  border-radius:14px;padding:1.4rem;direction:rtl;text-align:right;
  color:rgba(255,255,255,.9);line-height:2;margin:.8rem 0}
.db-item{background:rgba(255,255,255,.06);border-right:4px solid #667eea;
  border-radius:8px;padding:.8rem 1rem;margin:.4rem 0;
  direction:rtl;text-align:right;color:rgba(255,255,255,.9)}
.error-box{background:rgba(220,38,38,.12);border:1px solid rgba(220,38,38,.4);
  border-radius:10px;padding:1rem;direction:rtl;text-align:right;
  color:#fca5a5;margin:.6rem 0}
.success-box{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.35);
  border-radius:10px;padding:1rem;direction:rtl;text-align:right;
  color:#6ee7b7;margin:.6rem 0}
.warn-box{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.35);
  border-radius:10px;padding:1rem;direction:rtl;text-align:right;
  color:#fcd34d;margin:.6rem 0}
.template-box{background:rgba(102,126,234,.08);border:2px dashed rgba(102,126,234,.4);
  border-radius:12px;padding:1rem;direction:rtl;text-align:right;
  color:rgba(255,255,255,.85);margin:.6rem 0;font-size:.9rem;line-height:1.8}
div.stButton>button{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;
  border:none;border-radius:10px;padding:.6rem 1.4rem;
  font-weight:700;font-size:.9rem;width:100%;
  transition:all .25s;box-shadow:0 4px 16px rgba(102,126,234,.4)}
div.stButton>button:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(102,126,234,.6)}
.stSelectbox label,.stTextInput label,.stTextArea label,
.stNumberInput label,.stSlider label,.stFileUploader label{
  direction:rtl;text-align:right;color:rgba(255,255,255,.9)!important;font-weight:600}
section[data-testid="stSidebar"]{direction:rtl}
section[data-testid="stSidebar"] .stMarkdown{text-align:right}
.stTabs [data-baseweb="tab"]{direction:rtl;font-size:.88rem;font-weight:600}
.grade-A{color:#10b981;font-weight:700}
.grade-B{color:#3b82f6;font-weight:700}
.grade-C{color:#f59e0b;font-weight:700}
.grade-D{color:#ef4444;font-weight:700}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# CURRICULUM
# ═══════════════════════════════════════════════════════════
CURRICULUM = {
    "الطور الابتدائي":{
        "grades":["السنة الأولى","السنة الثانية","السنة الثالثة","السنة الرابعة","السنة الخامسة"],
        "subjects":{
            "السنة الأولى":["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثانية":["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثالثة":["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الرابعة":["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الخامسة":["اللغة العربية","الرياضيات","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
        },"branches":None
    },
    "الطور المتوسط":{
        "grades":["السنة الأولى متوسط","السنة الثانية متوسط","السنة الثالثة متوسط","السنة الرابعة متوسط (شهادة)"],
        "subjects":{"_default":["اللغة العربية وآدابها","الرياضيات","العلوم الفيزيائية والتكنولوجية","العلوم الطبيعية والحياة","التاريخ والجغرافيا","التربية الإسلامية","التربية المدنية","اللغة الفرنسية","اللغة الإنجليزية","التربية التشكيلية","التربية الموسيقية","الإعلام الآلي"]},
        "branches":None
    },
    "الطور الثانوي":{
        "grades":["السنة الأولى ثانوي (جذع مشترك)","السنة الثانية ثانوي","السنة الثالثة ثانوي (بكالوريا)"],
        "subjects":None,
        "branches":{
            "السنة الأولى ثانوي (جذع مشترك)":{
                "جذع مشترك علوم وتكنولوجيا":["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية","الإعلام الآلي"],
                "جذع مشترك آداب وفلسفة":["اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا","اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية","الرياضيات"],
            },
            "السنة الثانية ثانوي":{
                "شعبة علوم تجريبية":["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات":["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي":["الرياضيات","العلوم الفيزيائية","التكنولوجيا","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة":["اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا","علم الاجتماع والنفس","اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية":["اللغة الفرنسية","اللغة الإنجليزية","اللغة العربية","التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد":["الاقتصاد والمناجمنت","المحاسبة والمالية","الرياضيات","القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
            "السنة الثالثة ثانوي (بكالوريا)":{
                "شعبة علوم تجريبية":["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات":["الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي":["الرياضيات","العلوم الفيزيائية","التكنولوجيا","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة":["اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا","علم الاجتماع والنفس","اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية":["اللغة الفرنسية","اللغة الإنجليزية","اللغة العربية","التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد":["الاقتصاد والمناجمنت","المحاسبة والمالية","الرياضيات","القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
        }
    },
}

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

DOMAINS = {
    "الرياضيات":["أنشطة عددية","أنشطة جبرية","أنشطة هندسية","أنشطة إحصائية"],
    "العلوم الفيزيائية والتكنولوجية":["المادة","الكهرباء","الضوء","الميكانيك"],
    "العلوم الطبيعية والحياة":["الوحدة والتنوع","التغذية والهضم","التوليد","البيئة"],
    "اللغة العربية وآدابها":["فهم المكتوب","الإنتاج الكتابي","الظاهرة اللغوية","الميدان الأدبي"],
}

# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════
DB_PATH = "donia_smart.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT,grade TEXT,branch TEXT,subject TEXT,lesson TEXT,
        ex_type TEXT,difficulty TEXT,content TEXT,created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS lesson_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT,grade TEXT,subject TEXT,lesson TEXT,
        domain TEXT,duration TEXT,content TEXT,created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,subject TEXT,grade_value REAL,
        total REAL,feedback TEXT,created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT,grade TEXT,subject TEXT,semester TEXT,
        content TEXT,created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS grade_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT,subject TEXT,semester TEXT,
        data_json TEXT,created_at TEXT)""")
    con.commit(); con.close()

def db_exec(sql, params=(), fetch=False):
    con = sqlite3.connect(DB_PATH)
    cur = con.execute(sql, params)
    con.commit()
    result = cur.fetchall() if fetch else None
    con.close()
    return result

def get_stats():
    total = (db_exec("SELECT COUNT(*) FROM exercises",fetch=True) or [(0,)])[0][0]
    plans = (db_exec("SELECT COUNT(*) FROM lesson_plans",fetch=True) or [(0,)])[0][0]
    exams = (db_exec("SELECT COUNT(*) FROM exams",fetch=True) or [(0,)])[0][0]
    corr  = (db_exec("SELECT COUNT(*) FROM corrections",fetch=True) or [(0,)])[0][0]
    return total, plans, exams, corr

init_db()

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def fix_arabic(text):
    try: return get_display(reshape(str(text)))
    except: return str(text)

def get_llm(model_name, api_key):
    return ChatGroq(model_name=model_name, groq_api_key=api_key, temperature=0.7)

def call_llm(llm, prompt):
    return llm.invoke(prompt).content

def render_with_latex(text):
    parts = re.split(r'(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)', text)
    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            st.latex(part[2:-2].strip())
        elif part.startswith("$") and part.endswith("$"):
            st.latex(part[1:-1].strip())
        elif part.strip():
            st.markdown(f'<div style="direction:rtl;text-align:right;color:rgba(255,255,255,.92);line-height:2;">{part}</div>',
                        unsafe_allow_html=True)

def get_appreciation(grade, total=20):
    pct = grade / total * 100
    if pct >= 90: return "ممتاز"
    elif pct >= 75: return "جيد جداً"
    elif pct >= 65: return "جيد"
    elif pct >= 50: return "مقبول"
    else: return "ضعيف"

def calc_average(taqwim, fard, ikhtibhar):
    """حساب المعدل: (تقويم×1 + فرض×1 + اختبار×2) / 4"""
    try:
        t = float(taqwim or 0)
        f = float(fard or 0)
        i = float(ikhtibhar or 0)
        return round((t * 1 + f * 1 + i * 2) / 4, 2)
    except: return 0.0

# ─── PDF helpers ────────────────────────────────────────────
def ar(txt):
    return fix_arabic(txt)

def make_pdf_styles():
    _register_arabic_pdf_fonts()
    styles = getSampleStyleSheet()
    fn = _AR_FONT_MAIN
    fb = _AR_FONT_BOLD
    return {
        "body":  ParagraphStyle("body",  fontName=fn, leading=18, spaceAfter=4, fontSize=11, alignment=TA_RIGHT),
        "title": ParagraphStyle("title", fontName=fb, leading=20, spaceAfter=6, fontSize=15, alignment=TA_CENTER,
                                textColor=rl_colors.HexColor("#764ba2")),
        "h2":    ParagraphStyle("h2",    fontName=fb, leading=18, spaceAfter=4, fontSize=13, alignment=TA_RIGHT,
                                textColor=rl_colors.HexColor("#667eea")),
        "small": ParagraphStyle("small", fontName=fn, leading=14, spaceAfter=2, fontSize=9, alignment=TA_RIGHT,
                                textColor=rl_colors.HexColor("#888888")),
        "center":ParagraphStyle("center",fontName=fn, leading=18, spaceAfter=4, fontSize=11, alignment=TA_CENTER),
    }

def generate_simple_pdf(content, title, subtitle=""):
    buf = io.BytesIO()
    _register_arabic_pdf_fonts()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.2*cm, bottomMargin=1.5*cm)
    S = make_pdf_styles()
    story = []
    head_tbl = Table(
        [
            [Paragraph(ar("الجمهورية الجزائرية الديمقراطية الشعبية"), S["center"]),
             Paragraph(ar("وزارة التربية الوطنية"), S["center"])],
            [Paragraph(ar("DONIA SMART TEACHER — المعلم الذكي"), S["center"]),
             Paragraph(ar("وثيقة رقمية — نسخة قابلة للطباعة"), S["center"])],
        ],
        colWidths=[8.2 * cm, 8.2 * cm],
    )
    head_tbl.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, rl_colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), rl_colors.HexColor("#f4f2ff")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(head_tbl)
    story.append(Spacer(1, 8))
    story.append(Paragraph(ar(f"DONIA SMART TEACHER  |  {title}"), S["title"]))
    if subtitle:
        story.append(Paragraph(ar(subtitle), S["center"]))
    story.append(HRFlowable(width="100%",thickness=1.5,
                             color=rl_colors.HexColor("#764ba2")))
    story.append(Spacer(1, 10))
    for line in content.splitlines():
        line = line.strip()
        if not line: continue
        if line.startswith("##"):
            story.append(Spacer(1,6))
            story.append(Paragraph(ar(line.replace("#","")), S["h2"]))
        elif line.startswith("$") or "```" in line:
            story.append(Paragraph(ar("[ معادلة – راجع النسخة الرقمية ]"), S["small"]))
        else:
            story.append(Paragraph(ar(line), S["body"]))
        story.append(Spacer(1,2))
    doc.build(story)
    buf.seek(0); return buf.read()

# ─── EXAM PDF (النموذج الجزائري الرسمي) ────────────────────
def generate_exam_pdf(exam_data: dict) -> bytes:
    """Generate exam PDF matching exact Algerian format"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.8*cm, leftMargin=1.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    S = make_pdf_styles()
    story = []

    # Header table
    thin = Side(style='thin', color='000000')
    border = Border(top=thin,bottom=thin,left=thin,right=thin)

    header_data = [
        [ar("الجمهورية الجزائرية الديمقراطية الشعبية"), ""],
        [ar(f"متوسطة: {exam_data.get('school','....................')}"),
         ar(f"وزارة التربية الوطنية")],
        [ar(f"مديرية التربية لولاية: {exam_data.get('wilaya','..............')}"),
         ar(f"السنة الدراسية: {exam_data.get('year','2025/2026')}")],
        [ar(f"المقاطعة: {exam_data.get('district','.....')}  |  المستوى: {exam_data.get('grade','')}  |  المدة: {exam_data.get('duration','ساعتان')}"), ""],
    ]
    t = Table(header_data, colWidths=[10*cm, 6.5*cm])
    t.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),10),
        ('SPAN',(0,0),(1,0)),
        ('SPAN',(0,3),(1,3)),
        ('GRID',(0,0),(-1,-1),0.5,rl_colors.black),
        ('BACKGROUND',(0,0),(-1,0),rl_colors.HexColor("#f0f0f0")),
    ]))
    story.append(t)
    story.append(Spacer(1,8))

    # Exam title
    title_style = ParagraphStyle("etitle", fontName="Helvetica-Bold", fontSize=14,
                                 alignment=TA_CENTER, leading=20,
                                 textColor=rl_colors.HexColor("#000000"))
    story.append(Paragraph(ar(f"اختبار {exam_data.get('semester','الفصل الثاني')} في مادة {exam_data.get('subject','')}"), title_style))
    story.append(HRFlowable(width="100%",thickness=1.5,color=rl_colors.black))
    story.append(Spacer(1,10))

    # Exercises from content
    for line in exam_data.get('content','').splitlines():
        line = line.strip()
        if not line: continue
        if re.match(r'^تمرين\s+\d+', line) or re.match(r'^الوضعية الإدماجية', line):
            story.append(Spacer(1,6))
            story.append(Paragraph(ar(line), ParagraphStyle("exhead",
                fontName="Helvetica-Bold",fontSize=12,alignment=TA_RIGHT,
                leading=18, underlineWidth=0.5,
                textColor=rl_colors.HexColor("#000000"))))
        elif line.startswith("$") or "```" in line:
            story.append(Paragraph(ar("[معادلة]"), S["small"]))
        else:
            story.append(Paragraph(ar(line), S["body"]))
        story.append(Spacer(1,2))

    story.append(Spacer(1,12))
    story.append(Paragraph(ar("انتهى — بالتوفيق والنجاح"), ParagraphStyle(
        "end", fontName="Helvetica-Bold", fontSize=11, alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0); return buf.read()

# ─── Grade Report PDF ────────────────────────────────────────
def generate_report_pdf(report_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    S = make_pdf_styles()
    story = []

    story.append(Paragraph(ar("تحليل نتائج الأقسام"), S["title"]))
    story.append(Paragraph(ar(f"{report_data.get('school','')} | {report_data.get('subject','')} | {report_data.get('semester','')}"), S["center"]))
    story.append(HRFlowable(width="100%",thickness=1.5,color=rl_colors.HexColor("#764ba2")))
    story.append(Spacer(1,12))

    for cls in report_data.get('classes', []):
        story.append(Paragraph(ar(f"تحليل نتائج القسم {cls['name']}"), S["h2"]))
        info_line = (f"عدد التلاميذ: {cls['total']} — "
                     f"المعدل: {cls['avg']:.2f} — "
                     f"أعلى: {cls['max']:.2f} — "
                     f"أدنى: {cls['min']:.2f} — "
                     f"النجاح: {cls['pass_rate']:.1f}%")
        story.append(Paragraph(ar(info_line), S["body"]))
        story.append(Spacer(1,6))

        # Top 5
        if cls.get('top5'):
            story.append(Paragraph(ar("أفضل 5 تلاميذ"), S["h2"]))
            top_data = [[ar("الرتبة"), ar("الاسم"), ar("المعدل")]]
            for i, s in enumerate(cls['top5'], 1):
                top_data.append([str(i), ar(s['name']), f"{s['avg']:.2f}"])
            t = Table(top_data, colWidths=[2*cm, 10*cm, 3*cm])
            t.setStyle(TableStyle([
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('BACKGROUND',(0,0),(-1,0),rl_colors.HexColor("#667eea")),
                ('TEXTCOLOR',(0,0),(-1,0),rl_colors.white),
                ('GRID',(0,0),(-1,-1),0.5,rl_colors.grey),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[rl_colors.white,rl_colors.HexColor("#f8f8ff")]),
            ]))
            story.append(t)
            story.append(Spacer(1,6))

        # Grade distribution
        if cls.get('distribution'):
            story.append(Paragraph(ar("توزيع الدرجات"), S["h2"]))
            dist = cls['distribution']
            dist_data = [[ar("0-5"), ar("5-10"), ar("10-15"), ar("15-20")],
                         [str(dist.get('0-5',0)), str(dist.get('5-10',0)),
                          str(dist.get('10-15',0)), str(dist.get('15-20',0))]]
            t = Table(dist_data, colWidths=[4*cm]*4)
            t.setStyle(TableStyle([
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('BACKGROUND',(0,0),(-1,0),rl_colors.HexColor("#302b63")),
                ('TEXTCOLOR',(0,0),(-1,0),rl_colors.white),
                ('GRID',(0,0),(-1,-1),0.5,rl_colors.grey),
            ]))
            story.append(t)
        story.append(Spacer(1,16))

    # AI Analysis
    if report_data.get('ai_analysis'):
        story.append(Paragraph(ar("التحليل البيداغوجي"), S["h2"]))
        for line in report_data['ai_analysis'].splitlines():
            if line.strip():
                story.append(Paragraph(ar(line.strip()), S["body"]))
        story.append(Spacer(1,4))

    doc.build(story)
    buf.seek(0); return buf.read()

# ─── Grade Book Excel ────────────────────────────────────────
def generate_grade_book_excel(students: list, class_name: str,
                               subject: str, semester: str, school: str) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "دفتر التنقيط"

    # Styles
    title_font = Font(name="Arial", bold=True, size=11)
    header_font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    body_font = Font(name="Arial", size=10)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    right  = Alignment(horizontal="right",  vertical="center")
    thin = Side(style="thin", color="000000")
    border = Border(top=thin,bottom=thin,left=thin,right=thin)

    purple_fill = PatternFill("solid", fgColor="764ba2")
    blue_fill   = PatternFill("solid", fgColor="667eea")
    light_fill  = PatternFill("solid", fgColor="f0f0ff")

    # Header rows
    ws.merge_cells("A1:I1")
    ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية"
    ws["A1"].font = title_font; ws["A1"].alignment = center
    ws["A1"].fill = light_fill

    ws.merge_cells("A2:I2")
    ws["A2"] = "وزارة التربية الوطنية"
    ws["A2"].font = title_font; ws["A2"].alignment = center

    ws.merge_cells("A3:I3")
    ws["A3"] = f"متوسطة: {school}"
    ws["A3"].font = title_font; ws["A3"].alignment = center

    ws.merge_cells("A4:I4")
    ws["A4"] = f"دفتر التنقيط | القسم: {class_name} | المادة: {subject} | {semester}"
    ws["A4"].font = title_font; ws["A4"].alignment = center
    ws["A4"].fill = PatternFill("solid", fgColor="e8e8ff")

    ws.append([])  # row 5 empty

    # Column headers (row 6)
    headers = ["رقم التعريف", "اللقب", "الاسم", "تاريخ الميلاد",
               "تقويم /20", "فرض /20", "اختبار /20", "المعدل /20", "التقديرات"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col, value=h)
        cell.font = header_font; cell.alignment = center
        cell.fill = purple_fill; cell.border = border
    ws.row_dimensions[6].height = 30

    # Data rows
    for idx, stu in enumerate(students):
        row = 7 + idx
        avg = calc_average(stu.get('taqwim',0), stu.get('fard',0), stu.get('ikhtibhar',0))
        apprec = get_appreciation(avg)
        values = [
            stu.get('id',''), stu.get('nom',''), stu.get('prenom',''),
            str(stu.get('dob','')), stu.get('taqwim',''), stu.get('fard',''),
            stu.get('ikhtibhar',''), avg, apprec
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = body_font; cell.border = border
            cell.alignment = center if col != 2 else right
            if idx % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="f8f8ff")
        ws.row_dimensions[row].height = 22

    # Stats rows
    last_data = 6 + len(students)
    ws.append([])
    stat_row = last_data + 2
    stats = [
        ("عدد التلاميذ", len(students)),
        ("معدل القسم", round(sum(calc_average(s.get('taqwim',0),s.get('fard',0),s.get('ikhtibhar',0)) for s in students)/max(len(students),1),2)),
        ("الناجحون", sum(1 for s in students if calc_average(s.get('taqwim',0),s.get('fard',0),s.get('ikhtibhar',0)) >= 10)),
    ]
    for i, (label, val) in enumerate(stats):
        lc = ws.cell(row=stat_row+i, column=1, value=label)
        vc = ws.cell(row=stat_row+i, column=2, value=val)
        lc.font = Font(bold=True, name="Arial", size=10)
        vc.font = Font(bold=True, name="Arial", size=10, color="764ba2")
        lc.fill = light_fill; vc.fill = light_fill
        lc.border = border; vc.border = border

    # Column widths
    widths = [18, 16, 16, 14, 10, 10, 10, 10, 12]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.sheet_view.rightToLeft = True

    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)
    return buf.read()

# ─── Parse Excel grade book ──────────────────────────────────
def parse_grade_book_excel(uploaded_file) -> list:
    """Parse the Algerian grade book Excel format"""
    wb = openpyxl.load_workbook(uploaded_file, data_only=True)
    ws = wb.active
    students = []
    header_row = None

    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if row and any(str(c) in ['matricule','رقم التعريف','اللقب'] for c in row if c):
            if str(row[0]) in ['matricule','رقم التعريف']:
                continue  # skip label row
            header_row = i; continue

        if header_row and i > header_row + 1:
            vals = list(row)
            if len(vals) >= 7 and vals[0]:
                try:
                    stu = {
                        'id': str(vals[0] or ''),
                        'nom': str(vals[1] or ''),
                        'prenom': str(vals[2] or ''),
                        'dob': str(vals[3] or ''),
                        'taqwim': float(vals[4] or 0),
                        'fard': float(vals[5] or 0),
                        'ikhtibhar': float(vals[6] or 0),
                    }
                    stu['average'] = calc_average(stu['taqwim'], stu['fard'], stu['ikhtibhar'])
                    stu['apprec']  = get_appreciation(stu['average'])
                    students.append(stu)
                except: pass
    return students

# ─── Lesson Plan PDF (النموذج الرسمي للمذكرة) ───────────────
def generate_lesson_plan_pdf(plan_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.2*cm, leftMargin=1.2*cm,
                            topMargin=1.2*cm, bottomMargin=1.2*cm)
    S = make_pdf_styles()
    story = []

    thin = Side(style='thin', color='000000')
    bdr  = Border(top=thin,bottom=thin,left=thin,right=thin)

    # Title header
    story.append(Paragraph(ar("الجمهورية الجزائرية الديمقراطية الشعبية — وزارة التربية الوطنية"), S["center"]))
    story.append(Paragraph(ar(f"مذكرة رقم: ____  |  المؤسسة: {plan_data.get('school','.............')}  |  الأستاذ(ة): {plan_data.get('teacher','.............')}"), S["center"]))
    story.append(HRFlowable(width="100%",thickness=1.5,color=rl_colors.HexColor("#764ba2")))
    story.append(Spacer(1,6))

    # Info table
    info_data = [
        [ar("الميدان"), ar(plan_data.get('domain','')),
         ar("المستوى"), ar(plan_data.get('grade',''))],
        [ar("الباب / الوحدة"), ar(plan_data.get('chapter','')),
         ar("المدة الزمنية"), ar(plan_data.get('duration','50 دقيقة'))],
        [ar("المورد المعرفي"), ar(plan_data.get('lesson','')),
         ar("نوع الحصة"), ar(plan_data.get('session_type','درس نظري'))],
        [ar("مستوى من الكفاءة"), ar(plan_data.get('competency','')), "", ""],
    ]
    t = Table(info_data, colWidths=[3.5*cm,7*cm,3.5*cm,3.5*cm])
    t.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('FONTNAME',(2,0),(2,-2),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),10),
        ('GRID',(0,0),(-1,-1),0.5,rl_colors.black),
        ('BACKGROUND',(0,0),(0,-1),rl_colors.HexColor("#e8e8ff")),
        ('BACKGROUND',(2,0),(2,-2),rl_colors.HexColor("#e8e8ff")),
        ('SPAN',(1,3),(3,3)),
    ]))
    story.append(t); story.append(Spacer(1,6))

    # Main lesson table (4 columns: المراحل | المدة | سير الدرس | التقويم والإرشادات)
    lesson_header = [ar("المراحل"), ar("المدة"), ar("سير الدرس"), ar("التقويم والإرشادات")]
    lesson_rows = [lesson_header]

    sections = [
        ("تهيئة", plan_data.get('duration_t','5 د'), plan_data.get('intro','')),
        ("أنشطة بناء الموارد", plan_data.get('duration_b','25 د'), plan_data.get('build','')),
        ("إعادة الاستثمار", plan_data.get('duration_r','15 د'), plan_data.get('reinvest','')),
    ]
    for section, dur, content in sections:
        lesson_rows.append([ar(section), ar(dur), ar(content[:300]), ar(plan_data.get('eval',''))])

    # Homework row
    lesson_rows.append([ar("الواجب المنزلي"), "", ar(plan_data.get('homework','')), ""])

    col_widths = [2.5*cm, 1.5*cm, 10*cm, 3.5*cm]
    lt = Table(lesson_rows, colWidths=col_widths, repeatRows=1)
    lt.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('BACKGROUND',(0,0),(-1,0),rl_colors.HexColor("#764ba2")),
        ('TEXTCOLOR',(0,0),(-1,0),rl_colors.white),
        ('GRID',(0,0),(-1,-1),0.5,rl_colors.black),
        ('BACKGROUND',(0,1),(0,-1),rl_colors.HexColor("#f0f0ff")),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[rl_colors.white,rl_colors.HexColor("#f8f8ff")]),
        ('WORDWRAP',(2,1),(2,-1),True),
        ('ROWHEIGHT',(0,1),(-1,-2),60),
    ]))
    story.append(lt); story.append(Spacer(1,6))

    # Prerequisites and tools
    pre_data = [
        [ar("المكتسبات القبلية"), ar(plan_data.get('prerequisites',''))],
        [ar("الوسائل والأدوات"), ar(plan_data.get('tools','الكتاب المدرسي، السبورة، دليل الأستاذ'))],
        [ar("نقد ذاتي"), ar(plan_data.get('self_critique',''))],
    ]
    pt = Table(pre_data, colWidths=[3.5*cm,14*cm])
    pt.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('GRID',(0,0),(-1,-1),0.5,rl_colors.black),
        ('BACKGROUND',(0,0),(0,-1),rl_colors.HexColor("#e8e8ff")),
    ]))
    story.append(pt)

    doc.build(story)
    buf.seek(0); return buf.read()

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
    subject = st.selectbox("📖 المادة", subj_list) if subj_list else st.text_input("📖 المادة", key="sb_subject")
    model_name = st.selectbox("🤖 النموذج", GROQ_MODELS)

    st.markdown("---")
    st.markdown("**🏫 معلومات المؤسسة**")
    school_name = st.text_input("اسم المتوسطة / الثانوية", placeholder="متوسطة الشهيد...", key="school_name")
    teacher_name = st.text_input("اسم الأستاذ(ة)", placeholder="الأستاذ(ة)...", key="teacher_name")
    wilaya = st.text_input("الولاية", placeholder="الجزائر...", key="wilaya")
    school_year = st.text_input("السنة الدراسية", value="2025/2026", key="syear")

    st.markdown("---")
    if api_key:
        st.markdown('<div class="success-box">✅ مفتاح Groq API متاح</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">❌ GROQ_API_KEY غير موجود</div>', unsafe_allow_html=True)

    with st.expander("☁️ إعدادات السحابة"):
        drive_json   = st.text_area("مفتاح Google Drive (JSON)", height=60, placeholder='{"type":"service_account",...}')
        firebase_json= st.text_area("مفتاح Firebase (JSON)",    height=60, placeholder='{"type":"service_account",...}')

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div class="title-card">
    <h1>🎓 DONIA SMART TEACHER</h1>
    <p>المعلم الذكي للمنظومة التربوية الجزائرية · مذكرات · اختبارات · دفتر التنقيط · تحليل النتائج · تصحيح الأوراق</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════
(tab_plan, tab_exam, tab_grade, tab_report,
 tab_ex, tab_correct, tab_archive, tab_stats) = st.tabs([
    "📝 مذكرة الدرس",
    "📄 توليد اختبار",
    "📊 دفتر التنقيط",
    "📈 تحليل النتائج",
    "✏️ توليد تمرين",
    "✅ تصحيح أوراق",
    "🗄️ الأرشيف",
    "📉 إحصائيات",
])

branch_txt = f" – {branch}" if branch else ""

# ══════════════════════════════════════════════════════════
# TAB 1 — مذكرة الدرس (النموذج الرسمي الجزائري)
# ══════════════════════════════════════════════════════════
with tab_plan:
    st.markdown("### 📝 إعداد المذكرة وفق الصيغة الرسمية الجزائرية")
    st.markdown('<div class="template-box">📋 تُنشأ المذكرة بالهيكل الرسمي: المعلومات العامة · المورد المعرفي · الكفاءة · سير الدرس (تهيئة - بناء - استثمار) · التقويم · الواجب المنزلي</div>', unsafe_allow_html=True)

    pm1, pm2 = st.columns(2)
    with pm1:
        plan_lesson  = st.text_input("📝 عنوان الدرس / المورد المعرفي:", key="plan_lesson",
                                      placeholder="مثال: القاسم المشترك الأكبر لعددين طبيعيين")
        plan_chapter = st.text_input("📚 الباب / الوحدة:", key="plan_chapter",
                                      placeholder="مثال: الباب الأول – الأعداد الطبيعية")
        plan_domain  = st.selectbox("🗂️ الميدان:", ["أنشطة عددية","أنشطة جبرية","أنشطة هندسية","أنشطة إحصائية","ميدان عام"], key="plan_domain")
        plan_dur     = st.selectbox("⏱️ مدة الحصة:", ["50 دقيقة","1 ساعة","1.5 ساعة","2 ساعة"], key="plan_dur")

    with pm2:
        plan_session = st.selectbox("نوع الحصة:", ["درس نظري","أعمال موجهة","أعمال تطبيقية","تقييم تشخيصي","دعم وعلاج"], key="plan_session")
        plan_prereq  = st.text_area("📌 المكتسبات القبلية:", key="plan_prereq", height=70,
                                     placeholder="مثال: القسمة الإقليدية، قواسم عدد طبيعي...")
        plan_tools   = st.text_input("🛠️ الوسائل والأدوات:", key="plan_tools",
                                      value="الكتاب المدرسي، المنهاج، الوثيقة المرافقة، دليل الأستاذ، السبورة")
        plan_notes   = st.text_area("📌 ملاحظات خاصة:", key="plan_notes", height=70,
                                     placeholder="توجيهات خاصة بالفوج...")

    if st.button("📝 توليد المذكرة الكاملة بالذكاء الاصطناعي", key="btn_gen_plan"):
        if not api_key: st.warning("⚠️ أضف GROQ_API_KEY في متغيرات البيئة لإكمال التوليد.")
        elif not plan_lesson.strip(): st.warning("⚠️ أدخل عنوان الدرس / المورد المعرفي لإكمال المذكرة.")
        else:
            prompt = f"""أنت أستاذ جزائري خبير. أعدّ مذكرة درس رسمية وفق المنهاج الجزائري لوزارة التربية الوطنية.

المعطيات:
• الطور: {level} | السنة: {grade}{branch_txt}
• المادة: {subject} | الميدان: {plan_domain}
• الباب: {plan_chapter} | الدرس: {plan_lesson}
• نوع الحصة: {plan_session} | المدة: {plan_dur}
• المكتسبات القبلية: {plan_prereq}
{f"• ملاحظات: {plan_notes}" if plan_notes.strip() else ""}

أعدّ المذكرة بهذا الهيكل:

## الكفاءة الختامية
[اكتب الكفاءة الختامية للوحدة]

## مستوى من الكفاءة
[اكتب مستوى الكفاءة المستهدف في هذه الحصة]

## مرحلة التهيئة (5 دقائق)
[نشاط الاستعداد والتمهيد بأسئلة مراجعة]

## أنشطة بناء الموارد (25-30 دقيقة)
### وضعية تعلمية
[وصف النشاط التعلمي التفصيلي مع أمثلة ومعادلات LaTeX حيث يلزم]

### حوصلة
[الخلاصة والقاعدة التي يصل إليها الأستاذ مع التلاميذ]

## مرحلة إعادة الاستثمار (15 دقيقة)
### حل التمرين
[تمرين تطبيقي مع حله التفصيلي]

## التقويم والإرشادات
[أسئلة تقييمية وتوجيهات للأستاذ أثناء كل مرحلة]

## الواجب المنزلي
[تمارين المنزل مع رقم الصفحة إن أمكن]

## نقد ذاتي
[ملاحظات بيداغوجية لما بعد الحصة]"""

            with st.spinner("📝 جاري إعداد المذكرة…"):
                try:
                    llm = get_llm(model_name, api_key)
                    plan_text = call_llm(llm, prompt)
                    render_with_latex(plan_text)

                    # Parse sections for structured PDF
                    def extract_section(text, marker):
                        m = re.search(rf'## {marker}[^\n]*\n([\s\S]+?)(?=## |\Z)', text)
                        return m.group(1).strip() if m else ""

                    plan_data = {
                        "school": school_name, "teacher": teacher_name,
                        "grade": f"{grade}{branch_txt}", "domain": plan_domain,
                        "chapter": plan_chapter, "lesson": plan_lesson,
                        "session_type": plan_session, "duration": plan_dur,
                        "duration_t":"5 د","duration_b":"25 د","duration_r":"15 د",
                        "competency": extract_section(plan_text,"مستوى من الكفاءة"),
                        "intro":     extract_section(plan_text,"مرحلة التهيئة"),
                        "build":     extract_section(plan_text,"أنشطة بناء الموارد"),
                        "reinvest":  extract_section(plan_text,"مرحلة إعادة الاستثمار"),
                        "eval":      extract_section(plan_text,"التقويم والإرشادات"),
                        "homework":  extract_section(plan_text,"الواجب المنزلي"),
                        "self_critique": extract_section(plan_text,"نقد ذاتي"),
                        "prerequisites": plan_prereq, "tools": plan_tools,
                    }

                    db_exec("INSERT INTO lesson_plans (level,grade,subject,lesson,domain,duration,content,created_at) VALUES (?,?,?,?,?,?,?,?)",
                            (level,grade,subject,plan_lesson,plan_domain,plan_dur,plan_text,datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.success("✅ تم حفظ المذكرة")

                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button("📥 تحميل نص", plan_text.encode("utf-8-sig"),
                                           f"مذكرة_{plan_lesson}.txt", key="dl_plan_txt")
                    with d2:
                        pdf_p = generate_lesson_plan_pdf(plan_data)
                        st.download_button("📄 تحميل PDF (النموذج الرسمي)", pdf_p,
                                           f"مذكرة_{plan_lesson}.pdf","application/pdf", key="dl_plan_pdf")
                except ValueError as err:
                    st.warning(f"⚠️ تعذر معالجة بيانات المذكرة (ValueError). تأكد من إكمال الحقول الأساسية. التفاصيل: {err}")
                except Exception as err:
                    st.warning(f"⚠️ تعذر إكمال توليد المذكرة. تحقق من الاتصال ومن مفتاح Groq. التفاصيل: {err}")

# ══════════════════════════════════════════════════════════
# TAB 2 — توليد اختبار (النموذج الرسمي)
# ══════════════════════════════════════════════════════════
with tab_exam:
    st.markdown("### 📄 توليد ورقة الاختبار وفق النموذج الجزائري الرسمي")
    st.markdown('<div class="template-box">📋 يُنشأ الاختبار بالهيكل الرسمي: رأس الورقة (المؤسسة، المستوى، المدة) · 4 تمارين بنقاط محددة · وضعية إدماجية 8 نقاط</div>', unsafe_allow_html=True)

    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        exam_semester = st.selectbox("الفصل:", ["الفصل الأول","الفصل الثاني","الفصل الثالث"], key="exam_semester")
        exam_duration = st.selectbox("المدة:", ["ساعة واحدة","ساعتان","ثلاث ساعات"], key="exam_dur")
    with ex2:
        exam_theme    = st.text_input("محاور الاختبار:", key="exam_theme",
                                       placeholder="مثال: الجمل, الدوال الخطية, الأعداد الناطقة")
        exam_points   = st.text_input("نقاط التمارين:", value="3,3,3,3,8", key="exam_pts",
                                       help="مثال: 3,3,3,3,8 (4 تمارين + وضعية إدماجية)")
    with ex3:
        exam_difficulty = st.select_slider("مستوى الصعوبة:",
            ["سهل","متوسط","صعب","مستوى الشهادة"], key="exam_diff")
        include_integrate = st.checkbox("إضافة وضعية إدماجية", value=True, key="exam_integrate")

    exam_notes = st.text_area("ملاحظات وتوجيهات:", key="exam_notes",
                               placeholder="مثلاً: التركيز على الأعداد الناطقة والجذور التربيعية...")

    if st.button("🚀 توليد ورقة الاختبار", key="btn_gen_exam"):
        if not api_key: st.error("⚠️ أضف GROQ_API_KEY")
        else:
            pts = exam_points.split(",")
            pts_desc = " + ".join([f"تمرين {i+1}: {p.strip()} نقاط" for i, p in enumerate(pts[:4])])
            integrate_txt = f"+ وضعية إدماجية: {pts[4].strip() if len(pts)>4 else '8'} نقاط" if include_integrate else ""

            prompt = f"""أنت أستاذ جزائري خبير في إعداد الاختبارات. أعدّ ورقة اختبار رسمية.

المعطيات:
• الطور: {level} | المستوى: {grade}{branch_txt}
• المادة: {subject} | {exam_semester}
• المدة: {exam_duration} | الصعوبة: {exam_difficulty}
• المحاور: {exam_theme or subject}
• توزيع النقاط: {pts_desc} {integrate_txt}
• المجموع: 20 نقطة
{f"• ملاحظات: {exam_notes}" if exam_notes.strip() else ""}

أعدّ الاختبار بهذا الهيكل الدقيق:

تمرين 1 :( {pts[0].strip() if pts else '3'} نقاط)
[الأسئلة مرقمة: 1( 2( 3( مع المعادلات LaTeX حيث يلزم]

تمرين 2 :( {pts[1].strip() if len(pts)>1 else '3'} نقاط)
[الأسئلة...]

تمرين 3 :( {pts[2].strip() if len(pts)>2 else '3'} نقاط)
[الأسئلة...]

تمرين 4 :( {pts[3].strip() if len(pts)>3 else '3'} نقاط)
[الأسئلة...]

{"الوضعية الإدماجية:( " + (pts[4].strip() if len(pts)>4 else '8') + " نقاط)" if include_integrate else ""}
{"السياق: [سياق واقعي من الحياة اليومية للمنطقة الجزائرية]" if include_integrate else ""}
{"الجزء الأول: [أسئلة تدريجية...]" if include_integrate else ""}
{"الجزء الثاني: [أسئلة تكملة...]" if include_integrate else ""}
{"انتهى — بالتوفيق والنجاح" if include_integrate else ""}

القواعد الإلزامية:
- اللغة العربية الفصحى
- المعادلات بتنسيق LaTeX: $ للمضمنة، $$ للمستقلة
- الأسئلة مرقمة ومتدرجة في الصعوبة
- الوضعية الإدماجية ذات سياق واقعي جزائري"""

            with st.spinner("📄 جاري توليد الاختبار…"):
                try:
                    llm = get_llm(model_name, api_key)
                    exam_content = call_llm(llm, prompt)

                    st.markdown(f'<div class="feature-card"><h4>📄 {subject} | {grade}{branch_txt} | {exam_semester} | ⏱️ {exam_duration}</h4></div>',
                                unsafe_allow_html=True)
                    render_with_latex(exam_content)

                    db_exec("INSERT INTO exams (level,grade,subject,semester,content,created_at) VALUES (?,?,?,?,?,?)",
                            (level,grade,subject,exam_semester,exam_content,datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.success("✅ تم حفظ الاختبار")

                    exam_pdf_data = {
                        "school": school_name,"wilaya": wilaya,
                        "grade": f"{grade}{branch_txt}","year": school_year,
                        "district":"...","semester": exam_semester,
                        "subject": subject,"duration": exam_duration,
                        "content": exam_content,
                    }

                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button("📥 تحميل نص", exam_content.encode("utf-8-sig"),
                                           f"اختبار_{subject}_{exam_semester}.txt", key="dl_exam_txt")
                    with d2:
                        pdf_e = generate_exam_pdf(exam_pdf_data)
                        st.download_button("📄 تحميل PDF (النموذج الرسمي)", pdf_e,
                                           f"اختبار_{subject}_{exam_semester}.pdf","application/pdf",
                                           key="dl_exam_pdf")
                except Exception as err:
                    st.markdown(f'<div class="error-box">❌ {err}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — دفتر التنقيط
# ══════════════════════════════════════════════════════════
with tab_grade:
    st.markdown("### 📊 دفتر التنقيط الرسمي")

    grade_mode = st.radio("وضع الإدخال:", ["📁 رفع ملف Excel (دفتر موجود)","✏️ إدخال يدوي"],
                           horizontal=True, key="grade_mode")

    students_data = []

    if grade_mode == "📁 رفع ملف Excel (دفتر موجود)":
        gr_file = st.file_uploader("📁 ارفع ملف دفتر التنقيط:", type=["xlsx","xls"], key="gr_upload")
        if gr_file:
            with st.spinner("جاري قراءة الملف…"):
                try:
                    students_data = parse_grade_book_excel(gr_file)
                    st.success(f"✅ تم قراءة {len(students_data)} تلميذ")
                except Exception as e:
                    st.error(f"خطأ في القراءة: {e}")
    else:
        st.markdown("**أدخل بيانات التلاميذ (اسم، تقويم، فرض، اختبار) — سطر لكل تلميذ:**")
        manual_data = st.text_area("", height=200, key="grade_manual",
            placeholder="أحمد بلعيد, 15, 12, 14\nفاطمة زروق, 18, 17, 19\nعلي حمدي, 10, 8, 11")
        if manual_data.strip():
            for line in manual_data.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    try:
                        name_parts = parts[0].split()
                        students_data.append({
                            'id':'', 'nom': name_parts[0] if name_parts else parts[0],
                            'prenom': " ".join(name_parts[1:]) if len(name_parts)>1 else "",
                            'dob':'', 'taqwim': float(parts[1]),
                            'fard': float(parts[2]), 'ikhtibhar': float(parts[3]),
                        })
                    except: pass
            for s in students_data:
                s['average'] = calc_average(s['taqwim'],s['fard'],s['ikhtibhar'])
                s['apprec']  = get_appreciation(s['average'])

    if students_data:
        gc1, gc2 = st.columns(2)
        with gc1:
            gb_class   = st.text_input("اسم القسم:", placeholder="4م1", key="gb_class")
            gb_sem     = st.selectbox("الفصل:", ["الفصل الأول","الفصل الثاني","الفصل الثالث"], key="gb_sem")
        with gc2:
            gb_subject = st.text_input("المادة:", value=subject, key="gb_subject")
            gb_school  = st.text_input("المؤسسة:", value=school_name, key="gb_school")

        # Build DataFrame
        df = pd.DataFrame([{
            "اللقب": s.get('nom',''), "الاسم": s.get('prenom',''),
            "تقويم /20": s.get('taqwim',''), "فرض /20": s.get('fard',''),
            "اختبار /20": s.get('ikhtibhar',''),
            "المعدل": s.get('average',0), "التقدير": s.get('apprec','')
        } for s in students_data])

        st.markdown("#### 📋 جدول النتائج")
        st.dataframe(df, use_container_width=True, height=350)

        # Statistics
        averages = [s['average'] for s in students_data]
        passed   = [a for a in averages if a >= 10]
        a1,a2,a3,a4,a5 = st.columns(5)
        for col, val, lbl, clr in [
            (a1, len(students_data),     "عدد التلاميذ",  "#667eea"),
            (a2, f"{sum(averages)/max(len(averages),1):.2f}", "معدل القسم", "#764ba2"),
            (a3, f"{max(averages):.2f}", "أعلى معدل",    "#10b981"),
            (a4, f"{min(averages):.2f}", "أدنى معدل",    "#ef4444"),
            (a5, f"{len(passed)}/{len(averages)}", "الناجحون", "#f59e0b"),
        ]:
            with col:
                st.markdown(f'<div class="stat-card"><h2 style="color:{clr}">{val}</h2><p>{lbl}</p></div>',
                            unsafe_allow_html=True)

        # Chart
        fig = px.bar(df, x="اللقب", y="المعدل", color="التقدير",
            color_discrete_map={"ممتاز":"#10b981","جيد جداً":"#3b82f6","جيد":"#667eea","مقبول":"#f59e0b","ضعيف":"#ef4444"},
            title=f"نتائج {gb_class or 'القسم'}", template="plotly_dark")
        fig.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="حد النجاح")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        # Downloads
        dg1, dg2 = st.columns(2)
        with dg1:
            xlsx_bytes = generate_grade_book_excel(students_data, gb_class or "القسم",
                                                    gb_subject or subject, gb_sem, gb_school or school_name)
            st.download_button("📊 تحميل دفتر التنقيط (Excel)", xlsx_bytes,
                               f"دفتر_{gb_class}_{gb_sem}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_grade_xlsx")
        with dg2:
            # Save to DB
            if st.button("💾 حفظ في قاعدة البيانات", key="btn_save_grade"):
                db_exec("INSERT INTO grade_books (class_name,subject,semester,data_json,created_at) VALUES (?,?,?,?,?)",
                        (gb_class,subject,gb_sem,json.dumps(students_data,ensure_ascii=False),
                         datetime.now().strftime("%Y-%m-%d %H:%M")))
                st.success("✅ تم الحفظ")

# ══════════════════════════════════════════════════════════
# TAB 4 — تحليل النتائج الشامل
# ══════════════════════════════════════════════════════════
with tab_report:
    st.markdown("### 📈 تحليل نتائج الأقسام (تقرير شامل)")

    rep_mode = st.radio("مصدر البيانات:",
        ["📁 رفع ملف Excel","📋 إدخال يدوي","📂 من قاعدة البيانات"],
        horizontal=True, key="rep_mode")

    all_classes = []

    if rep_mode == "📁 رفع ملف Excel":
        rep_files = st.file_uploader("📁 ارفع ملفات دفتر التنقيط (يمكن رفع عدة أقسام):",
                                      type=["xlsx"], accept_multiple_files=True, key="rep_upload")
        if rep_files:
            for f in rep_files:
                try:
                    stus = parse_grade_book_excel(f)
                    if stus:
                        avgs = [s['average'] for s in stus]
                        passed = [a for a in avgs if a >= 10]
                        dist = {"0-5":0,"5-10":0,"10-15":0,"15-20":0}
                        for a in avgs:
                            if a<5: dist["0-5"]+=1
                            elif a<10: dist["5-10"]+=1
                            elif a<15: dist["10-15"]+=1
                            else: dist["15-20"]+=1
                        sorted_stus = sorted(stus, key=lambda x: x['average'], reverse=True)
                        cls_name = f.name.replace(".xlsx","").replace("_"," ")
                        all_classes.append({
                            "name": cls_name, "total": len(stus),
                            "avg": sum(avgs)/len(avgs), "max": max(avgs), "min": min(avgs),
                            "pass_rate": len(passed)/len(avgs)*100,
                            "distribution": dist,
                            "top5": [{"name":f"{s['nom']} {s['prenom']}", "avg":s['average']}
                                     for s in sorted_stus[:5]],
                            "students": stus,
                        })
                except Exception as e:
                    st.warning(f"خطأ في {f.name}: {e}")

    elif rep_mode == "📋 إدخال يدوي":
        st.caption("أدخل بيانات كل قسم (اسم القسم, عدد الناجحين, المعدل, المجموع):")
        rep_text = st.text_area("", height=150, key="rep_manual",
            placeholder="4م1, 13, 8.07, 42\n4م2, 14, 8.86, 41\n4م3, 18, 10.5, 40")
        for line in (rep_text or "").strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                try:
                    total = int(parts[3])
                    passed_n = int(parts[1])
                    avg = float(parts[2])
                    all_classes.append({
                        "name": parts[0], "total": total,
                        "avg": avg, "max": 20, "min": 0,
                        "pass_rate": passed_n/total*100 if total>0 else 0,
                        "distribution": {}, "top5": [], "students": [],
                    })
                except: pass
    else:
        saved = db_exec("SELECT * FROM grade_books ORDER BY created_at DESC LIMIT 20", fetch=True) or []
        if not saved: st.info("لا توجد بيانات محفوظة بعد.")
        else:
            for row in saved:
                rid, cname, sub, sem, data_j, created = row
                try:
                    stus = json.loads(data_j)
                    avgs = [s['average'] for s in stus]
                    if avgs:
                        passed = [a for a in avgs if a >= 10]
                        dist = {"0-5":0,"5-10":0,"10-15":0,"15-20":0}
                        for a in avgs:
                            if a<5: dist["0-5"]+=1
                            elif a<10: dist["5-10"]+=1
                            elif a<15: dist["10-15"]+=1
                            else: dist["15-20"]+=1
                        sorted_stus = sorted(stus, key=lambda x: x['average'], reverse=True)
                        all_classes.append({
                            "name": cname, "total": len(stus),
                            "avg": sum(avgs)/len(avgs), "max": max(avgs), "min": min(avgs),
                            "pass_rate": len(passed)/len(avgs)*100,
                            "distribution": dist,
                            "top5": [{"name":f"{s['nom']} {s['prenom']}", "avg":s['average']}
                                     for s in sorted_stus[:5]],
                            "students": stus,
                        })
                except: pass

    if all_classes:
        rep_subject  = st.text_input("المادة:", value=subject, key="rep_subj")
        rep_semester = st.selectbox("الفصل:", ["الفصل الأول","الفصل الثاني","الفصل الثالث"], key="rep_sem")

        # Summary comparison chart
        df_cls = pd.DataFrame([{
            "القسم": c['name'], "المعدل": round(c['avg'],2),
            "نسبة النجاح": round(c['pass_rate'],1), "عدد التلاميذ": c['total']
        } for c in all_classes])

        ch1, ch2 = st.columns(2)
        with ch1:
            fig1 = px.bar(df_cls, x="القسم", y="المعدل", color="القسم",
                          title="مقارنة معدلات الأقسام", template="plotly_dark")
            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig1, use_container_width=True)
        with ch2:
            fig2 = px.bar(df_cls, x="القسم", y="نسبة النجاح", color="القسم",
                          title="مقارنة نسب النجاح %", template="plotly_dark")
            fig2.add_hline(y=50, line_dash="dash", line_color="red")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df_cls, use_container_width=True)

        # Per-class details
        for cls in all_classes:
            with st.expander(f"📊 تفاصيل القسم {cls['name']}"):
                st.markdown(f"""
                <div class="template-box">
                عدد التلاميذ: <b>{cls['total']}</b> &nbsp;|&nbsp;
                المعدل: <b>{cls['avg']:.2f}</b> &nbsp;|&nbsp;
                أعلى: <b>{cls['max']:.2f}</b> &nbsp;|&nbsp;
                أدنى: <b>{cls['min']:.2f}</b> &nbsp;|&nbsp;
                نسبة النجاح: <b>{cls['pass_rate']:.1f}%</b>
                </div>""", unsafe_allow_html=True)

                if cls.get('top5'):
                    top_df = pd.DataFrame(cls['top5'])
                    top_df.index = range(1, len(top_df)+1)
                    st.caption("أفضل 5 تلاميذ:")
                    st.dataframe(top_df, use_container_width=True)

                if cls.get('distribution'):
                    dist = cls['distribution']
                    dist_df = pd.DataFrame([dist])
                    st.caption("توزيع الدرجات:")
                    st.dataframe(dist_df, use_container_width=True)

        # AI Analysis
        if api_key and st.button("🤖 توليد التقرير البيداغوجي بالذكاء الاصطناعي", key="btn_rep_ai"):
            summary = "\n".join([f"القسم {c['name']}: معدل={c['avg']:.2f}, نجاح={c['pass_rate']:.1f}%, عدد={c['total']}"
                                  for c in all_classes])
            prompt_rep = f"""أنت مستشار بيداغوجي جزائري خبير. حلّل النتائج التالية:
{summary}
المادة: {rep_subject} | {rep_semester} | المستوى: {grade}{branch_txt}

قدّم تقريراً شاملاً يتضمن:
1. التشخيص العام للمستوى
2. مقارنة بين الأقسام (نقاط القوة والضعف)
3. الفئات التي تحتاج دعماً
4. توصيات بيداغوجية محددة لكل قسم
5. خطة علاجية مقترحة
6. مقترحات للأستاذ لتطوير أدائه"""

            with st.spinner("🧠 جاري التحليل البيداغوجي…"):
                try:
                    llm = get_llm(model_name, api_key)
                    ai_analysis = call_llm(llm, prompt_rep)
                    st.markdown("---")
                    st.markdown("#### 🤖 التقرير البيداغوجي")
                    render_with_latex(ai_analysis)

                    # Generate full PDF report
                    report_data = {
                        "school": school_name, "subject": rep_subject,
                        "semester": rep_semester, "classes": all_classes,
                        "ai_analysis": ai_analysis,
                    }
                    pdf_rep = generate_report_pdf(report_data)
                    st.download_button("📄 تحميل التقرير الكامل PDF", pdf_rep,
                                       f"تقرير_نتائج_{rep_semester}.pdf","application/pdf",
                                       key="dl_report_pdf")
                except Exception as e:
                    st.error(str(e))
        else:
            # Basic PDF without AI
            report_data = {
                "school": school_name, "subject": rep_subject if 'rep_subject' in dir() else subject,
                "semester": rep_semester if 'rep_semester' in dir() else "",
                "classes": all_classes, "ai_analysis": "",
            }
            pdf_rep = generate_report_pdf(report_data)
            st.download_button("📄 تحميل التقرير PDF", pdf_rep,
                               "تقرير_نتائج.pdf","application/pdf", key="dl_report_pdf2")

# ══════════════════════════════════════════════════════════
# TAB 5 — توليد تمرين
# ══════════════════════════════════════════════════════════
with tab_ex:
    st.markdown("### ✏️ توليد تمرين مع الحل التفصيلي")
    c1, c2, c3 = st.columns([4,1,1])
    with c1:
        lesson = st.text_input("📝 عنوان الدرس:", key="ex_lesson",
                                placeholder="مثال: الانقسام المنصف، المعادلات التفاضلية…")
    with c2:
        num_ex = st.number_input("عدد التمارين", 1, 5, 1, key="ex_num")
    with c3:
        ex_type = st.selectbox("النوع", ["تمرين تطبيقي","مسألة","سؤال إشكالي","فرض محروس"], key="ex_type")
    difficulty = st.select_slider("⚡ مستوى الصعوبة",
        ["سهل جداً","سهل","متوسط","صعب","مستوى بكالوريا"], key="ex_difficulty")
    extra = st.text_area("📌 تعليمات إضافية:", placeholder="أي توجيهات خاصة…", key="ex_extra")

    if st.button("🚀 توليد التمرين والحل التفصيلي", key="btn_gen_ex"):
        if not api_key: st.error("⚠️ أضف GROQ_API_KEY")
        elif not lesson.strip(): st.warning("⚠️ أدخل عنوان الدرس")
        else:
            prompt = f"""أنت أستاذ جزائري خبير. صمم {num_ex} {ex_type}.

• الطور: {level} | السنة: {grade}{branch_txt}
• المادة: {subject} | الدرس: {lesson} | الصعوبة: {difficulty}
{f"• ملاحظات: {extra}" if extra.strip() else ""}

الهيكل المطلوب:
## التمرين
[المعطيات والمطلوب بوضوح]

## الحل المفصل
[خطوات مرقمة]

## ملاحظات للأستاذ
[توجيهات بيداغوجية]

## كود LaTeX
```latex
[الكود الكامل]
```"""
            with st.spinner("🧠 جاري التوليد…"):
                try:
                    llm = get_llm(model_name, api_key)
                    res_text = call_llm(llm, prompt)
                    render_with_latex(res_text)
                    db_exec("INSERT INTO exercises (level,grade,branch,subject,lesson,ex_type,difficulty,content,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                            (level,grade,branch or "",subject,lesson,ex_type,difficulty,res_text,datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.success("✅ تم الحفظ")
                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button("📥 نص", res_text.encode("utf-8-sig"),
                                           f"{lesson}.txt", key="dl_ex_txt")
                    with d2:
                        pdf_ex = generate_simple_pdf(res_text, lesson, f"{subject} | {grade}")
                        st.download_button("📄 PDF", pdf_ex, f"{lesson}.pdf","application/pdf", key="dl_ex_pdf")
                except Exception as err:
                    st.markdown(f'<div class="error-box">❌ {err}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 6 — تصحيح أوراق
# ══════════════════════════════════════════════════════════
with tab_correct:
    st.markdown("### ✅ تصحيح أوراق الاختبار")
    correct_mode = st.radio("وضع التصحيح:", ["📝 إدخال نصي","📋 التحقق من إجابة وفق نموذج الحل"],
                             horizontal=True, key="correct_mode")

    cc1, cc2 = st.columns(2)
    with cc1:
        student_name = st.text_input("اسم الطالب:", key="corr_name", placeholder="اختياري")
        exam_subj    = st.text_input("المادة:", value=subject, key="corr_subject")
    with cc2:
        total_marks  = st.number_input("العلامة الكاملة:", 10, 100, 20, key="corr_total")
        correct_style= st.selectbox("أسلوب التصحيح:",
            ["تصحيح شامل مع تعليقات","تصحيح مختصر","تحديد الأخطاء فقط"], key="corr_style")

    model_answer  = st.text_area("✍️ الحل النموذجي / السؤال:", height=120, key="corr_model_ans",
                                  placeholder="أدخل السؤال أو الحل النموذجي…")
    student_answer= st.text_area("📄 إجابة الطالب:", height=120, key="corr_student_ans",
                                  placeholder="انسخ إجابة الطالب هنا…")

    if st.button("✅ تصحيح الإجابة", key="btn_correct"):
        if not api_key: st.error("⚠️ أضف GROQ_API_KEY")
        elif not student_answer.strip(): st.warning("⚠️ أدخل إجابة الطالب")
        else:
            prompt_corr = f"""أنت أستاذ جزائري خبير. صحّح إجابة الطالب بأسلوب: {correct_style}

المادة: {exam_subj} | العلامة الكاملة: {total_marks}/20
الحل النموذجي: {model_answer or 'غير محدد — قيّم من حيث المنطق العلمي'}
إجابة الطالب: {student_answer}

## التقييم الكلي
العلامة المقترحة: X/{total_marks}
المستوى: [ممتاز/جيد جداً/جيد/مقبول/ضعيف]

## نقاط القوة

## الأخطاء والنواقص

## التوصيات للطالب

## ملاحظة للأستاذ"""

            with st.spinner("🔍 جاري التصحيح…"):
                try:
                    llm = get_llm(model_name, api_key)
                    correction = call_llm(llm, prompt_corr)
                    render_with_latex(correction)
                    m = re.search(r'(\d+(?:\.\d+)?)\s*/' + str(total_marks), correction)
                    gv = float(m.group(1)) if m else 0.0
                    db_exec("INSERT INTO corrections (student_name,subject,grade_value,total,feedback,created_at) VALUES (?,?,?,?,?,?)",
                            (student_name or "مجهول",exam_subj,gv,total_marks,correction,datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.success(f"✅ العلامة: {gv}/{total_marks}")
                    pdf_c = generate_simple_pdf(correction, f"تصحيح: {student_name or 'طالب'}", exam_subj)
                    st.download_button("📄 تحميل التصحيح PDF", pdf_c,
                                       f"تصحيح_{student_name or 'طالب'}.pdf","application/pdf",
                                       key="dl_corr_pdf")
                except Exception as err:
                    st.markdown(f'<div class="error-box">❌ {err}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 7 — الأرشيف
# ══════════════════════════════════════════════════════════
with tab_archive:
    st.markdown("### 🗄️ الأرشيف الشامل")
    arch_tabs = st.tabs(["📚 التمارين","📝 المذكرات","📄 الاختبارات","✅ التصحيحات"])

    with arch_tabs[0]:
        search_q = st.text_input("🔍 بحث:", key="db_search", placeholder="ابحث بعنوان أو مادة…")
        exercises = db_exec("SELECT * FROM exercises WHERE lesson LIKE ? OR subject LIKE ? ORDER BY created_at DESC",
                            (f"%{search_q}%",f"%{search_q}%"), fetch=True) or []
        st.caption(f"النتائج: {len(exercises)}")
        for ex in exercises:
            ex_id,lv,gr,br,sub,les,xt,diff,cont,created = ex
            with st.expander(f"📚 {les} | {sub} | {gr} | {diff} | 🕒 {created}"):
                st.markdown(f'<div class="result-box">{cont[:400]}…</div>', unsafe_allow_html=True)
                b1,b2,b3 = st.columns(3)
                with b1:
                    st.download_button("📥 نص", cont.encode("utf-8-sig"), f"{les}.txt", key=f"dl_{ex_id}")
                with b2:
                    px2 = generate_simple_pdf(cont, les)
                    st.download_button("📄 PDF", px2, f"{les}.pdf","application/pdf", key=f"pdf_{ex_id}")
                with b3:
                    if st.button("🗑️ حذف", key=f"del_{ex_id}"):
                        db_exec("DELETE FROM exercises WHERE id=?", (ex_id,)); st.rerun()

    with arch_tabs[1]:
        plans = db_exec("SELECT * FROM lesson_plans ORDER BY created_at DESC", fetch=True) or []
        for p in plans:
            try:
                if p is None or not isinstance(p, (tuple, list)) or len(p) < 9:
                    st.warning("⚠️ سجل مذكرة غير مكتمل في قاعدة البيانات — تم تخطيه. أعد حفظ المذكرة بعد إكمال عنوان الدرس والحقول.")
                    continue
                pid, lv, gr, sub, les, dom, dur, cont, created = p[:9]
                les = "بدون عنوان" if les is None else str(les)
                sub = "" if sub is None else str(sub)
                gr = "" if gr is None else str(gr)
                dom = "" if dom is None else str(dom)
                cont = "" if cont is None else str(cont)
                created = "" if created is None else str(created)
            except ValueError as ve:
                st.warning(f"⚠️ تعذر قراءة سجل مذكرة (ValueError): {ve}")
                continue
            except Exception as e:
                st.warning(f"⚠️ تعذر عرض مذكرة من الأرشيف: {e}")
                continue
            with st.expander(f"📝 {les} | {sub} | {gr} | {dom} | 🕒 {created}"):
                st.markdown(f'<div class="result-box">{cont[:350]}…</div>', unsafe_allow_html=True)
                pp1,pp2 = st.columns(2)
                with pp1:
                    st.download_button("📥 نص", cont.encode("utf-8-sig"), f"مذكرة_{les}.txt", key=f"pln_{pid}")
                with pp2:
                    ppdf = generate_simple_pdf(cont, f"مذكرة: {les}", f"{sub} | {gr}")
                    st.download_button("📄 PDF", ppdf, f"مذكرة_{les}.pdf","application/pdf", key=f"ppdf_{pid}")

    with arch_tabs[2]:
        exams = db_exec("SELECT * FROM exams ORDER BY created_at DESC", fetch=True) or []
        for ex in exams:
            eid,lv,gr,sub,sem,cont,created = ex
            with st.expander(f"📄 {sub} | {gr} | {sem} | 🕒 {created}"):
                st.markdown(f'<div class="result-box">{cont[:350]}…</div>', unsafe_allow_html=True)
                ep1,ep2 = st.columns(2)
                with ep1:
                    st.download_button("📥 نص", cont.encode("utf-8-sig"), f"اختبار_{sub}.txt", key=f"edl_{eid}")
                with ep2:
                    exam_d = {"school":school_name,"wilaya":wilaya,"grade":gr,
                              "year":school_year,"district":"...","semester":sem,
                              "subject":sub,"duration":"ساعتان","content":cont}
                    epdf = generate_exam_pdf(exam_d)
                    st.download_button("📄 PDF", epdf, f"اختبار_{sub}.pdf","application/pdf", key=f"epdf_{eid}")

    with arch_tabs[3]:
        corrs = db_exec("SELECT * FROM corrections ORDER BY created_at DESC", fetch=True) or []
        if not corrs: st.info("لا توجد تصحيحات.")
        else:
            df_c = pd.DataFrame(corrs, columns=["id","الاسم","المادة","العلامة","من","الملاحظات","التاريخ"])
            st.dataframe(df_c[["الاسم","المادة","العلامة","من","التاريخ"]], use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 8 — إحصائيات
# ══════════════════════════════════════════════════════════
with tab_stats:
    total_ex, plans_cnt, exams_cnt, corr_cnt = get_stats()
    st.markdown("### 📉 إحصائيات الاستخدام")

    s1,s2,s3,s4 = st.columns(4)
    for col,val,lbl,clr in [
        (s1,total_ex,"التمارين المولّدة","#667eea"),
        (s2,plans_cnt,"المذكرات المعدّة","#764ba2"),
        (s3,exams_cnt,"الاختبارات المولّدة","#10b981"),
        (s4,corr_cnt,"الأوراق المصحّحة","#f59e0b"),
    ]:
        with col:
            st.markdown(f'<div class="stat-card"><h2 style="color:{clr}">{val}</h2><p>{lbl}</p></div>',
                        unsafe_allow_html=True)

    exercises_all = db_exec("SELECT * FROM exercises ORDER BY created_at DESC", fetch=True) or []
    if exercises_all:
        df_ex = pd.DataFrame(exercises_all,
            columns=["id","level","grade","branch","subject","lesson","ex_type","difficulty","content","created_at"])
        ch1,ch2 = st.columns(2)
        with ch1:
            sc = df_ex["subject"].value_counts().reset_index()
            sc.columns=["المادة","العدد"]
            fig_s = px.bar(sc, x="المادة", y="العدد", title="التمارين حسب المادة",
                template="plotly_dark", color_discrete_sequence=["#667eea"])
            fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_s, use_container_width=True)
        with ch2:
            dc = df_ex["difficulty"].value_counts().reset_index()
            dc.columns=["الصعوبة","العدد"]
            fig_d = px.pie(dc, values="العدد", names="الصعوبة",
                title="توزيع مستويات الصعوبة", template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_d.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_d, use_container_width=True)

    st.markdown("---")
    st.markdown("### ☁️ حالة الربط")
    c1,c2 = st.columns(2)
    with c1:
        if drive_json and drive_json.strip().startswith("{"):
            st.markdown('<div class="success-box">✅ Google Drive: متصل</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">❌ Google Drive: غير متصل</div>', unsafe_allow_html=True)
    with c2:
        if firebase_json and firebase_json.strip().startswith("{"):
            st.markdown('<div class="success-box">✅ Firebase: متصل</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">❌ Firebase: غير متصل</div>', unsafe_allow_html=True)
