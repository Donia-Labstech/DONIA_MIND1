"""
DONIA MIND 1 — المعلم الذكي (DONIA SMART TEACHER) — v3.0 GLOBAL EXCELLENCE UPGRADE
المعلم الذكي للمنظومة التربوية الجزائرية

═══════════════════════════════════════════════════════════
ORIGINAL FIXES (v2.2 — PRESERVED — ZERO-DELETION POLICY):
FIX-1 [ValueError ~1364] : تعزيز unpack سجلات DB مع [:9] + guard كامل
FIX-2 [TypeError ~252]   : _STYLES_CACHE dict RTL/LTR — أسماء ParagraphStyle فريدة
FIX-3 [TypeError format] : safe_f() لتأمين تنسيق None في generate_report_pdf
FIX-4 [ValueError empty] : حماية max()/min() على قوائم فارغة
FIX-5 [dir() vs locals()]: استبدال dir() بـ متغيرات مُعرَّفة مسبقاً
FIX-6 [Excel parsing]    : parse_grade_book_excel + أوراق متعددة + pandas/xlrd
UX-1  : ثيم احترافي، أزرار كبيرة، آفاتار روبوت، إخفاء اسم النموذج
UX-2  : هوية جزائرية — ألوان العلم (أخضر/أبيض/أحمر)، رسالة ترحيب
UX-3  : شعار DONIA LABS TECH في الشريط الجانبي
I18N  : مواد لغوية أجنبية — توليد وPDF باتجاه LTR عند الحاجة
OCR   : معاينة صور أوراق الإجابة + استخراج نص اختياري (pytesseract)
SEC   : واجهة مفتاح API آمنة
EXPORT: تصدير Word (.docx) بجانب PDF في كل تبويب
FONT  : خطوط Amiri/Cairo العربية مضمّنة في PDF

NEW v3.0 — GLOBAL EXCELLENCE UPGRADE:
HYB-1 : Dual-LLM Engine — Groq (Speed) + Arcee (Domain Accuracy)
HYB-2 : CrossCheckAgent — validates 100% pedagogical accuracy before display
HYB-3 : Algerian standards alignment (dzexams.com benchmarks in prompts)
QR-1  : Dynamic QR code embedded in sidebar linking to deployment URL
UI-1  : Animated SVG robot assistant (enhanced, Lottie-inspired CSS)
UI-2  : Live Preview Dashboard before download
UI-3  : "Regenerate with Alternative Model" toggle button
BRAND : Logo assets/logo_donia.jpg + QR code branding
PDF-2 : Arabic reshaper + python-bidi — identical to official Algerian templates
RTL-W : python-docx Word export with full RTL support
XLS-2 : Excel grade books — Class 1 on Sheet 1, Class 2 on Sheet 2, etc.
RPT-1 : Pedagogical Report (التقرير البيداغوجي) auto-display after every analysis
═══════════════════════════════════════════════════════════
"""

# ╔═══════════════════════════════════════════════════════════╗
# ║              SECTION 0 — IMPORTS                          ║
# ╚═══════════════════════════════════════════════════════════╝
import streamlit as st
import os, sqlite3, re, json, io, base64, time, hashlib
import urllib.request
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

# ── NEW v3.0 imports ─────────────────────────────────────────
try:
    import qrcode
    from qrcode.image.pil import PilImage
    _QR_AVAILABLE = True
except ImportError:
    _QR_AVAILABLE = False

try:
    import requests as _req
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

# ── Arabic rendering ─────────────────────────────────────────
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    _ARABIC_AVAILABLE = True
except ImportError:
    _ARABIC_AVAILABLE = False

# ── DOCX ─────────────────────────────────────────────────────
try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False

# ── OCR ──────────────────────────────────────────────────────
try:
    import pytesseract  # noqa: F401
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

load_dotenv()

# ╔═══════════════════════════════════════════════════════════╗
# ║          SECTION 1 — CONSTANTS & KEYS                     ║
# ╚═══════════════════════════════════════════════════════════╝

DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── NEW v3.0: Arcee key from Streamlit secrets ────────────────
def _get_secret(key: str, fallback: str = "") -> str:
    """Safely retrieve from st.secrets or env."""
    try:
        return st.secrets.get(key, os.getenv(key, fallback))
    except Exception:
        return os.getenv(key, fallback)

ARCEE_MODEL = "arcee-ai/arcee-spotlight"          # flagship domain-tuned model
ARCEE_BASE_URL = "https://models.arcee.ai/v1"
APP_URL = "https://doniamind1-pvnmwp3kdthtlfct7uhopm.streamlit.app/"

COPYRIGHT_FOOTER_AR = (
    "جميع حقوق الملكية محفوظة حصرياً لمختبر DONIA LABS TECH © 2026"
)
WELCOME_MESSAGE_AR = (
    "أهلاً بك أستاذنا القدير في رحاب DONIA MIND.. "
    "معاً نصنع مستقبل التعليم الجزائري بذكاء واحترافية."
)
SOCIAL_URL_WHATSAPP = os.getenv("DONIA_URL_WHATSAPP", "https://wa.me/213674661737")
SOCIAL_URL_LINKEDIN = os.getenv("DONIA_URL_LINKEDIN",
    "https://www.linkedin.com/in/donia-labs-tech-smart-ideas-lab")
SOCIAL_URL_FACEBOOK = os.getenv("DONIA_URL_FACEBOOK",
    "https://www.facebook.com/share/1An6GhVd56/")
SOCIAL_URL_TELEGRAM = os.getenv("DONIA_URL_TELEGRAM",
    "https://t.me/+LxRzVAK12HZmNTQ8")

# ╔═══════════════════════════════════════════════════════════╗
# ║          SECTION 2 — PAGE CONFIG & CSS                    ║
# ╚═══════════════════════════════════════════════════════════╝
st.set_page_config(
    page_title="DONIA MIND — المعلم الذكي",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════
   DONIA MIND v3.0 — الهوية البصرية الجزائرية الوطنية
   الألوان: أخضر زمردي / أبيض ناصع / أحمر عليزاران
   ═══════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;600;700;800&family=Tajawal:wght@400;500;700;800&family=Montserrat:wght@400;600;700;800;900&display=swap');

#MainMenu{visibility:hidden!important}
footer{visibility:hidden!important}
header{visibility:hidden!important}
.stDeployButton{display:none!important}
[data-testid="stToolbar"]{display:none!important}
[data-testid="stDecoration"]{display:none!important}
[data-testid="stStatusWidget"]{display:none!important}
a[href*="streamlit.io"]{display:none!important}

*,*::before,*::after{font-family:'Cairo','Amiri','Tajawal',sans-serif!important}

.stApp{background:#ffffff;color:#111111;}
.main{direction:rtl;text-align:right;color:#111111!important}
.block-container{color:#111111!important;background:#ffffff;}
h1{color:#c0392b!important;font-weight:800!important}
h2{color:#145a32!important;font-weight:700!important}
h3{color:#1e8449!important;font-weight:700!important}

/* بطاقة العنوان الرئيسية */
.title-card{
  background:linear-gradient(135deg,#145a32 0%,#1e8449 50%,#27ae60 100%);
  padding:1.75rem 2rem;border-radius:24px;text-align:center;
  margin-bottom:1rem;box-shadow:0 16px 48px rgba(20,90,50,.45);
  border:3px solid #c0392b;
}
.title-card h1{color:#ffffff!important;font-size:2.05rem;font-weight:800;margin:0}
.title-card p{color:rgba(255,255,255,.92);font-size:.96rem;margin:.45rem 0 0}

/* ── NEW: بطاقة الذكاء الهجين ── */
.hybrid-badge{
  display:inline-flex;align-items:center;gap:.4rem;
  background:linear-gradient(135deg,#0d1b2a,#1a3a5c);
  border:1px solid #2980b9;border-radius:20px;
  padding:.35rem .85rem;font-size:.8rem;font-weight:700;
  color:#74b9ff;margin:.2rem;letter-spacing:.04em;
}
.hybrid-badge .dot{width:8px;height:8px;border-radius:50%;
  background:#00d2d3;animation:blinkDot 1.5s infinite;}
@keyframes blinkDot{0%,100%{opacity:1}50%{opacity:.3}}

/* رسالة الترحيب */
.welcome-banner{
  background:linear-gradient(135deg,#fdfefe,#f9f9f9);
  border:2px solid #27ae60;border-left:8px solid #c0392b;
  border-radius:14px;padding:1.1rem 1.5rem;margin:.75rem 0 1.25rem;
  direction:rtl;text-align:right;
  font-size:1.05rem;font-weight:600;color:#145a32;
  box-shadow:0 4px 16px rgba(20,90,50,.12);
}

/* ── NEW: روبوت SVG متحرك محسّن ── */
.donia-robot-wrap{display:flex;justify-content:center;align-items:center;margin:.75rem 0}
.donia-robot-v3{position:relative;width:110px;height:110px;}
.donia-robot-v3 svg{width:110px;height:110px;}
.robot-body{animation:robotFloat 3s ease-in-out infinite;}
.robot-eye-l,.robot-eye-r{animation:robotBlink 4s ease-in-out infinite;}
.robot-antenna{animation:antennaPing 2s ease-in-out infinite;}
.robot-mouth{animation:robotSmile 5s ease-in-out infinite;}
@keyframes robotFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes robotBlink{0%,92%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
@keyframes antennaPing{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}
@keyframes robotSmile{0%,100%{d:path("M 42 62 Q 55 70 68 62")}50%{d:path("M 42 64 Q 55 74 68 64")}}

/* Live Preview Dashboard */
.preview-dashboard{
  background:linear-gradient(135deg,#f8fcf9,#f0f9f4);
  border:2px solid #27ae60;border-top:5px solid #1e8449;
  border-radius:18px;padding:1.5rem 2rem;margin:1rem 0;
  direction:rtl;text-align:right;
  box-shadow:0 8px 32px rgba(20,90,50,.12);
}
.preview-dashboard h3{color:#145a32;font-size:1.1rem;margin:0 0 1rem}
.preview-content{
  background:#ffffff;border:1px solid rgba(39,174,96,.3);
  border-radius:12px;padding:1.2rem;line-height:2;
  color:#111;white-space:pre-wrap;font-size:.95rem;
  max-height:500px;overflow-y:auto;
}
.preview-toolbar{
  display:flex;gap:.6rem;flex-wrap:wrap;
  margin-top:1rem;justify-content:flex-start;
}

/* Cross-Check badge */
.crosscheck-badge{
  display:inline-flex;align-items:center;gap:.5rem;
  background:linear-gradient(135deg,#0a3d1f,#145a32);
  border:1px solid #27ae60;border-radius:12px;
  padding:.5rem 1rem;font-size:.88rem;font-weight:700;color:#a8f0c0;
  margin:.5rem 0;
}
.crosscheck-icon{font-size:1.1rem;}

/* Regenerate button — special style */
.regen-btn button{
  background:linear-gradient(135deg,#2c3e50,#3498db)!important;
  border-color:#3498db!important;
}
.regen-btn button:hover{
  background:linear-gradient(135deg,#1a252f,#2980b9)!important;
}

/* بطاقات الإحصاء */
.stat-card{background:linear-gradient(135deg,rgba(30,132,73,.1),rgba(39,174,96,.08));
  border:2px solid #27ae60;border-radius:16px;
  padding:1.1rem;text-align:center;margin-bottom:.75rem}
.stat-card h2{font-size:1.85rem;margin:0;color:#145a32!important}
.stat-card p{margin:0;color:#333;font-size:.86rem}

.feature-card{background:#f9f9f9;border:1px solid #27ae60;
  border-right:5px solid #1e8449;border-radius:16px;
  padding:1.25rem;margin:.55rem 0;direction:rtl;text-align:right;color:#111}
.feature-card h4{color:#1e8449;margin:0 0 .45rem;font-size:1.02rem}

.result-box{background:#f9f9f9;border:1px solid rgba(30,132,73,.3);
  border-radius:16px;padding:1.45rem;direction:rtl;text-align:right;
  color:#111;line-height:2;margin:.85rem 0}
.db-item{background:#f4f9f4;border-right:4px solid #1e8449;
  border-radius:10px;padding:.85rem 1.05rem;margin:.45rem 0;
  direction:rtl;text-align:right;color:#111}
.error-box{background:rgba(192,57,43,.08);border:2px solid #c0392b;
  border-radius:12px;padding:1rem;direction:rtl;text-align:right;
  color:#922b21;margin:.65rem 0;font-weight:600}
.success-box{background:rgba(30,132,73,.08);border:2px solid #27ae60;
  border-radius:12px;padding:1rem;direction:rtl;text-align:right;
  color:#145a32;margin:.65rem 0;font-weight:600}
.warn-box{background:rgba(243,156,18,.1);border:2px solid #f39c12;
  border-radius:12px;padding:1rem;direction:rtl;text-align:right;
  color:#784212;margin:.65rem 0}
.template-box{background:rgba(30,132,73,.06);border:2px dashed #27ae60;
  border-radius:14px;padding:1.05rem;direction:rtl;text-align:right;
  color:#145a32;margin:.65rem 0;font-size:.9rem;line-height:1.85}

.grade-A{color:#1e8449;font-weight:700}
.grade-B{color:#2e86c1;font-weight:700}
.grade-C{color:#d4ac0d;font-weight:700}
.grade-D{color:#c0392b;font-weight:700}

section[data-testid="stSidebar"]{
  direction:rtl;
  background:linear-gradient(180deg,#f4fbf6,#eaf6ee)!important;
  border-left:4px solid #27ae60;
}
section[data-testid="stSidebar"] .stMarkdown{text-align:right;color:#145a32}

.stTabs [data-baseweb="tab"]{direction:rtl;font-size:.9rem;font-weight:700;color:#145a32}
.stTabs [data-baseweb="tab"][aria-selected="true"]{
  border-bottom:3px solid #c0392b!important;color:#c0392b!important}

.stSelectbox label,.stTextInput label,.stTextArea label,
.stNumberInput label,.stSlider label,.stFileUploader label,.stRadio label{
  direction:rtl;text-align:right;color:#145a32!important;font-weight:700}

.api-book-widget{background:linear-gradient(135deg,#f4fbf6,#eaf6ee);
  border:2px solid #27ae60;border-radius:16px;padding:1.1rem 1.2rem;text-align:center;margin:.5rem 0}
.api-book-icon{font-size:2.4rem;display:block;margin-bottom:.35rem}
.api-book-slogan{font-size:1rem;font-weight:800;color:#145a32;display:block}
.api-book-status-active{display:block;margin-top:.4rem;font-size:.88rem;
  font-weight:700;color:#1e8449;background:#d5f5e3;border-radius:8px;padding:.2rem .7rem}
.api-book-status-inactive{display:block;margin-top:.4rem;font-size:.88rem;
  font-weight:700;color:#c0392b;background:#fdecea;border-radius:8px;padding:.2rem .7rem}

.donia-social{display:flex;flex-wrap:wrap;gap:.45rem;justify-content:center;margin:.35rem 0}
.donia-social a{display:inline-block;padding:.35rem .75rem;border-radius:12px;
  background:#145a32;color:#ffffff!important;font-weight:700;font-size:.82rem;
  text-decoration:none!important;border:1px solid #27ae60;transition:transform .2s,box-shadow .2s}
.donia-social a:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(192,57,43,.4);background:#c0392b!important}

.donia-ip-footer{text-align:center;font-size:.85rem;color:#145a32;font-weight:600;
  padding:1.2rem 0 .5rem;margin-top:1.5rem;
  border-top:3px solid #27ae60;
  background:linear-gradient(90deg,#f4fbf6,#fef9f9,#f4fbf6);
  border-radius:0 0 12px 12px}
.donia-footer-social{display:flex;flex-wrap:wrap;gap:.6rem;justify-content:center;margin:.5rem 0}
.donia-footer-social a{display:inline-flex;align-items:center;gap:.3rem;
  padding:.4rem .9rem;border-radius:20px;background:#145a32;
  color:#ffffff!important;font-weight:700;font-size:.82rem;
  text-decoration:none!important;transition:background .2s,transform .2s}
.donia-footer-social a:hover{background:#c0392b!important;transform:translateY(-2px)}

.dz-flag-wrap{display:none!important}

.donia-slogan-bar{display:flex;flex-direction:column;align-items:center;
  gap:.3rem;padding:.9rem 1.5rem;margin:.6rem 0;
  background:linear-gradient(90deg,#145a32 0%,#1e8449 45%,#c0392b 100%);
  border-radius:14px;box-shadow:0 4px 20px rgba(20,90,50,.3)}
.donia-slogan-ar{font-family:'Cairo','Amiri',sans-serif;font-size:1.35rem;
  font-weight:800;color:#ffffff;letter-spacing:.04em;text-shadow:0 2px 6px rgba(0,0,0,.3)}
.donia-slogan-en{font-family:'Montserrat',sans-serif;font-size:.9rem;
  font-weight:600;color:rgba(255,255,255,.88);letter-spacing:.18em;text-transform:uppercase}
.donia-slogan-divider{width:40px;height:2px;background:rgba(255,255,255,.55);border-radius:2px}

div.stButton>button{
  background:linear-gradient(135deg,#1e8449,#145a32)!important;color:#ffffff!important;
  border:none!important;border-radius:18px!important;padding:0.85rem 1.65rem!important;
  min-height:3.1rem!important;font-weight:800!important;font-size:1.02rem!important;
  width:100%!important;transition:transform .22s, box-shadow .22s!important;
  box-shadow:0 6px 22px rgba(30,132,73,.45)!important;
}
div.stButton>button:hover{
  transform:translateY(-3px)!important;
  box-shadow:0 12px 36px rgba(192,57,43,.5)!important;
  background:linear-gradient(135deg,#c0392b,#922b21)!important;
}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div{
  border-radius:12px!important;border:2px solid #27ae60!important;
  font-family:'Cairo',sans-serif!important;transition:border-color .2s,box-shadow .2s!important}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{
  border-color:#c0392b!important;box-shadow:0 0 0 3px rgba(192,57,43,.18)!important}
</style>
""", unsafe_allow_html=True)

# ╔═══════════════════════════════════════════════════════════╗
# ║          SECTION 3 — CURRICULUM & MODEL LISTS            ║
# ╚═══════════════════════════════════════════════════════════╝
CURRICULUM = {
    "الطور الابتدائي": {
        "grades": ["السنة الأولى","السنة الثانية","السنة الثالثة",
                   "السنة الرابعة","السنة الخامسة"],
        "subjects": {
            "السنة الأولى":  ["اللغة العربية","الرياضيات","التربية الإسلامية",
                               "التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثانية": ["اللغة العربية","الرياضيات","التربية الإسلامية",
                               "التربية المدنية","التربية التشكيلية","التربية البدنية"],
            "السنة الثالثة":["اللغة العربية","الرياضيات","التربية الإسلامية",
                               "التربية المدنية","اللغة الفرنسية",
                               "التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الرابعة":["اللغة العربية","الرياضيات","التربية الإسلامية",
                               "التربية المدنية","اللغة الفرنسية",
                               "التربية العلمية والتكنولوجية","التاريخ والجغرافيا"],
            "السنة الخامسة":["اللغة العربية","الرياضيات","التربية الإسلامية",
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
                         "العلوم الفيزيائية والتكنولوجية","العلوم الطبيعية والحياة",
                         "التاريخ والجغرافيا","الاجتماعيات","التربية الإسلامية",
                         "التربية المدنية","اللغة الفرنسية","اللغة الإنجليزية",
                         "التربية التشكيلية","التربية الموسيقية","الإعلام الآلي"]
        },
        "branches": None,
    },
    "الطور الثانوي": {
        "grades": ["السنة الأولى ثانوي (جذع مشترك)",
                   "السنة الثانية ثانوي","السنة الثالثة ثانوي (بكالوريا)"],
        "subjects": None,
        "branches": {
            "السنة الأولى ثانوي (جذع مشترك)": {
                "جذع مشترك علوم وتكنولوجيا": [
                    "الرياضيات","العلوم الفيزيائية","العلوم الطبيعية والحياة",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية",
                    "التاريخ والجغرافيا","التربية الإسلامية","الإعلام الآلي"],
                "جذع مشترك آداب وفلسفة": [
                    "اللغة العربية وآدابها","الفلسفة","التاريخ والجغرافيا",
                    "اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية","الرياضيات"],
            },
            "السنة الثانية ثانوي": {
                "شعبة علوم تجريبية":   ["الرياضيات","العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية",
                    "اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات":        ["الرياضيات","العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي":     ["الرياضيات","العلوم الفيزيائية","التكنولوجيا",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة":   ["اللغة العربية وآدابها","الفلسفة",
                    "التاريخ والجغرافيا","علم الاجتماع والنفس",
                    "اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية":   ["اللغة الفرنسية","اللغة الإنجليزية",
                    "اللغة الإسبانية","اللغة الألمانية","اللغة الإيطالية",
                    "اللغة العربية","التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد": ["الاقتصاد والمناجمنت","المحاسبة والمالية",
                    "الرياضيات","القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
            "السنة الثالثة ثانوي (بكالوريا)": {
                "شعبة علوم تجريبية":   ["الرياضيات","العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية",
                    "اللغة الإنجليزية","التاريخ والجغرافيا","التربية الإسلامية"],
                "شعبة رياضيات":        ["الرياضيات","العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة تقني رياضي":     ["الرياضيات","العلوم الفيزيائية","التكنولوجيا",
                    "اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
                "شعبة آداب وفلسفة":   ["اللغة العربية وآدابها","الفلسفة",
                    "التاريخ والجغرافيا","علم الاجتماع والنفس",
                    "اللغة الفرنسية","اللغة الإنجليزية","التربية الإسلامية"],
                "شعبة لغات أجنبية":   ["اللغة الفرنسية","اللغة الإنجليزية",
                    "اللغة الإسبانية","اللغة الألمانية","اللغة الإيطالية",
                    "اللغة العربية","التاريخ والجغرافيا","الفلسفة"],
                "شعبة تسيير واقتصاد": ["الاقتصاد والمناجمنت","المحاسبة والمالية",
                    "الرياضيات","القانون","اللغة العربية","اللغة الفرنسية","اللغة الإنجليزية"],
            },
        },
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
    "الرياضيات":                          ["أنشطة عددية","أنشطة جبرية","أنشطة هندسية","أنشطة إحصائية"],
    "العلوم الفيزيائية والتكنولوجية":    ["المادة","الكهرباء","الضوء","الميكانيك"],
    "العلوم الطبيعية والحياة":           ["الوحدة والتنوع","التغذية والهضم","التوليد","البيئة"],
    "اللغة العربية وآدابها":             ["فهم المكتوب","الإنتاج الكتابي","الظاهرة اللغوية","الميدان الأدبي"],
}

# ╔═══════════════════════════════════════════════════════════╗
# ║          SECTION 4 — DATABASE                             ║
# ╚═══════════════════════════════════════════════════════════╝
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
        domain TEXT, duration TEXT, content TEXT, created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT, subject TEXT, grade_value REAL,
        total REAL, feedback TEXT, created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT, grade TEXT, subject TEXT, semester TEXT,
        content TEXT, created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS grade_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT, subject TEXT, semester TEXT,
        data_json TEXT, created_at TEXT)""")
    con.commit()
    con.close()

def db_exec(sql, params=(), fetch=False):
    con = sqlite3.connect(DB_PATH)
    cur = con.execute(sql, params)
    con.commit()
    result = cur.fetchall() if fetch else None
    con.close()
    return result

def get_stats():
    total = (db_exec("SELECT COUNT(*) FROM exercises", fetch=True) or [(0,)])[0][0]
    plans = (db_exec("SELECT COUNT(*) FROM lesson_plans", fetch=True) or [(0,)])[0][0]
    exams = (db_exec("SELECT COUNT(*) FROM exams", fetch=True) or [(0,)])[0][0]
    corr  = (db_exec("SELECT COUNT(*) FROM corrections", fetch=True) or [(0,)])[0][0]
    return total, plans, exams, corr

init_db()

# ╔═══════════════════════════════════════════════════════════╗
# ║          SECTION 5 — CORE HELPERS (ORIGINAL)              ║
# ╚═══════════════════════════════════════════════════════════╝
def _escape_xml_for_rl(text: str) -> str:
    s = str(text)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def fix_arabic(text: str) -> str:
    if not _ARABIC_AVAILABLE:
        return str(text)
    try:
        return get_display(reshape(str(text)))
    except Exception:
        return str(text)

def get_pdf_mode_for_subject(subject: str) -> tuple:
    s = (subject or "").strip()
    if "الإيطالية" in s or "Italien" in s:  return False, "Italian"
    if "الألمانية" in s or "Allemand" in s: return False, "German"
    if "الإسبانية" in s or "Espagnol" in s: return False, "Spanish"
    if "الإنجليزية" in s or "Anglais" in s.lower(): return False, "English"
    if "الفرنسية" in s or "Français" in s:  return False, "French"
    return True, "Arabic"

def pdf_text_line(text: str, rtl: bool) -> str:
    if rtl:
        return fix_arabic(str(text))
    return _escape_xml_for_rl(text)

def llm_output_language_clause(subject: str) -> str:
    rtl, lang = get_pdf_mode_for_subject(subject)
    if rtl:
        return "قاعدة إلزامية: اكتب كل المحتوى (العناوين، الأسئلة، الشروح) بالعربية الفصحى الواضحة."
    return (
        f"Mandatory: produce the ENTIRE output (titles, exercises, exam items, options, memo) "
        f"entirely in {lang}. Do not use Arabic for instructional text. "
        f"Use correct typography and numbering for Latin left-to-right text."
    )

def get_llm(model_name: str, api_key: str) -> ChatGroq:
    return ChatGroq(model_name=model_name, groq_api_key=api_key, temperature=0.7)

def call_llm(llm, prompt: str) -> str:
    return llm.invoke(prompt).content

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
                f'color:#111111;line-height:2;">{part}</div>',
                unsafe_allow_html=True)

def get_appreciation(grade, total=20):
    pct = grade / total * 100
    if pct >= 90: return "ممتاز"
    elif pct >= 75: return "جيد جداً"
    elif pct >= 65: return "جيد"
    elif pct >= 50: return "مقبول"
    else: return "ضعيف"

def calc_average(taqwim, fard, ikhtibhar):
    try:
        t = float(taqwim or 0)
        f = float(fard or 0)
        i = float(ikhtibhar or 0)
        return round((t * 1 + f * 1 + i * 2) / 4, 2)
    except (TypeError, ValueError):
        return 0.0

def safe_f(val, fmt=".2f") -> str:
    try:
        return format(float(val), fmt)
    except (TypeError, ValueError):
        return "—"

def ar(txt) -> str:
    return fix_arabic(txt)

def ocr_answer_sheet_image(image_bytes: bytes) -> str:
    if not _TESSERACT_AVAILABLE:
        return ""
    try:
        import pytesseract as _pt
        bio = io.BytesIO(image_bytes)
        im  = Image.open(bio).convert("RGB")
        return _pt.image_to_string(im, lang="ara+eng+fra")
    except Exception:
        return ""

# ╔═══════════════════════════════════════════════════════════╗
# ║          SECTION 6 — FONT REGISTRATION (ORIGINAL)         ║
# ╚═══════════════════════════════════════════════════════════╝
_AR_FONT_MAIN  = "Helvetica"
_AR_FONT_BOLD  = "Helvetica-Bold"
_AR_FONTS_TRIED = False

def _try_download_amiri_font_files(font_dir: str) -> None:
    if os.getenv("DONIA_AUTO_DOWNLOAD_FONTS", "1").strip().lower() in ("0","false","no"):
        return
    os.makedirs(font_dir, exist_ok=True)
    pairs = (
        ("Amiri-Regular.ttf",
         "https://raw.githubusercontent.com/googlefonts/amiri/main/fonts/ttf/Amiri-Regular.ttf"),
        ("Amiri-Bold.ttf",
         "https://raw.githubusercontent.com/googlefonts/amiri/main/fonts/ttf/Amiri-Bold.ttf"),
    )
    for fname, url in pairs:
        p = os.path.join(font_dir, fname)
        if os.path.isfile(p) and os.path.getsize(p) > 8000:
            continue
        try:
            urllib.request.urlretrieve(url, p)
        except Exception:
            pass

def _register_arabic_pdf_fonts():
    global _AR_FONT_MAIN, _AR_FONT_BOLD, _AR_FONTS_TRIED
    if _AR_FONTS_TRIED:
        return
    _AR_FONTS_TRIED = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir  = os.path.join(base_dir, "fonts")
    _try_download_amiri_font_files(font_dir)
    reg = []
    for label, fname in (
        ("Amiri",      "Amiri-Regular.ttf"),
        ("Amiri-Bold", "Amiri-Bold.ttf"),
        ("Cairo",      "Cairo-Regular.ttf"),
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

_STYLES_CACHE: dict = {}

def make_pdf_styles(rtl: bool = True) -> dict:
    global _STYLES_CACHE
    key = "rtl" if rtl else "ltr"
    if key in _STYLES_CACHE:
        return _STYLES_CACHE[key]
    _register_arabic_pdf_fonts()
    if rtl:
        fn, fb   = _AR_FONT_MAIN, _AR_FONT_BOLD
        body_al  = TA_RIGHT
        h2_al    = TA_RIGHT
    else:
        fn, fb   = "Helvetica", "Helvetica-Bold"
        body_al  = TA_LEFT
        h2_al    = TA_LEFT
    _STYLES_CACHE[key] = {
        "body":   ParagraphStyle(f"donia_body_{key}",   fontName=fn, leading=18,
                                 spaceAfter=4,  fontSize=11, alignment=body_al),
        "title":  ParagraphStyle(f"donia_title_{key}",  fontName=fb, leading=20,
                                 spaceAfter=6,  fontSize=15, alignment=TA_CENTER,
                                 textColor=rl_colors.HexColor("#1e3a5f")),
        "h2":     ParagraphStyle(f"donia_h2_{key}",     fontName=fb, leading=18,
                                 spaceAfter=4,  fontSize=13, alignment=h2_al,
                                 textColor=rl_colors.HexColor("#0d9488")),
        "small":  ParagraphStyle(f"donia_small_{key}",  fontName=fn, leading=14,
                                 spaceAfter=2,  fontSize=9,  alignment=body_al,
                                 textColor=rl_colors.HexColor("#64748b")),
        "center": ParagraphStyle(f"donia_center_{key}", fontName=fn, leading=18,
                                 spaceAfter=4,  fontSize=11, alignment=TA_CENTER),
    }
    return _STYLES_CACHE[key]

def _draw_pdf_footer(canvas, doc):
    _register_arabic_pdf_fonts()
    canvas.saveState()
    w, _h = doc.pagesize
    try:
        canvas.setFont(_AR_FONT_MAIN, 8)
    except Exception:
        canvas.setFont("Helvetica", 8)
    txt = fix_arabic(COPYRIGHT_FOOTER_AR) if _ARABIC_AVAILABLE else COPYRIGHT_FOOTER_AR
    canvas.drawCentredString(w / 2.0, 0.55 * cm, txt)
    canvas.restoreState()

def _pdf_footer_canvas_args() -> dict:
    return dict(onFirstPage=_draw_pdf_footer, onLaterPages=_draw_pdf_footer)

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 7 — NEW: ARCEE API CLIENT + HYBRID ENGINE     ║
# ╚═══════════════════════════════════════════════════════════╝

def call_arcee(prompt: str, arcee_key: str, system: str = "") -> str:
    """
    Call Arcee AI via OpenAI-compatible REST endpoint.
    Arcee Spotlight is a specialized domain-tuned model for education/Arabic content.
    Falls back gracefully if unavailable.
    """
    if not arcee_key or not _REQUESTS_AVAILABLE:
        return ""
    try:
        headers = {
            "Authorization": f"Bearer {arcee_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": ARCEE_MODEL,
            "messages": messages,
            "max_tokens": 3000,
            "temperature": 0.6,
        }
        resp = _req.post(
            f"{ARCEE_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Arcee unavailable: {str(e)[:80]}]"


def _dz_benchmark_clause(level: str, subject: str, grade: str) -> str:
    """
    Injects Algerian educational standard context into prompts.
    Aligned with dzexams.com benchmarks for authentic localization.
    """
    return (
        f"\n\nمعيار جزائري إلزامي (مرجع: dzexams.com):\n"
        f"- المستوى الدراسي: {level} | القسم: {grade} | المادة: {subject}\n"
        f"- احرص على التوافق الكامل مع منهاج وزارة التربية الوطنية الجزائرية.\n"
        f"- استخدم نوع وصياغة الأسئلة المعتمدة في الاختبارات الجزائرية الرسمية.\n"
        f"- راعِ مستويات بلوم التعليمية وخصائص كل طور دراسي.\n"
        f"- المصطلحات والتسميات يجب أن تطابق الكتاب المدرسي الجزائري تماماً."
    )


class CrossCheckAgent:
    """
    Dual-LLM Cross-Check Agent.
    Calls Groq (speed) + Arcee (domain accuracy) in parallel logic,
    then validates and synthesizes the final pedagogically-accurate output.
    """

    def __init__(self, groq_llm, arcee_key: str):
        self.groq_llm   = groq_llm
        self.arcee_key  = arcee_key

    def _validate(self, groq_out: str, arcee_out: str,
                  subject: str, level: str) -> str:
        """
        Synthesis step: merge both model outputs into a final validated answer.
        Arcee output is authoritative on domain accuracy; Groq ensures fluency.
        """
        if not arcee_out or arcee_out.startswith("[Arcee unavailable"):
            return groq_out  # fallback to Groq only

        # Use Groq to synthesize and validate the two outputs
        synthesis_prompt = (
            f"أنت محرر تربوي متخصص في المنهج الجزائري. لديك مخرجان لنموذجين ذكاء اصطناعي "
            f"حول نفس الطلب التربوي في مادة '{subject}' - '{level}'.\n\n"
            f"**مخرج النموذج الأول (Groq — سرعة وطلاقة):**\n{groq_out[:1500]}\n\n"
            f"**مخرج النموذج الثاني (Arcee — دقة تخصصية):**\n{arcee_out[:1500]}\n\n"
            f"المهمة: اصنع مخرجاً نهائياً واحداً مُحكَّماً بيداغوجياً يجمع أفضل ما في كليهما، "
            f"مع إعطاء الأولوية لدقة المحتوى التربوي الجزائري. "
            f"لا تضف تعليقاً أو مقدمة — أعطِ المحتوى النهائي مباشرة."
        )
        try:
            validated = call_llm(self.groq_llm, synthesis_prompt)
            return validated
        except Exception:
            return groq_out

    def generate(self, prompt: str, subject: str = "",
                 level: str = "", grade: str = "") -> dict:
        """
        Full dual-model generation with cross-validation.
        Returns dict with keys: groq, arcee, final, sources_used
        """
        dz_clause = _dz_benchmark_clause(level, subject, grade)
        full_prompt = prompt + dz_clause

        # Step 1: Groq (fast)
        groq_out = ""
        try:
            groq_out = call_llm(self.groq_llm, full_prompt)
        except Exception as e:
            groq_out = f"[Groq error: {e}]"

        # Step 2: Arcee (domain-specialized)
        arcee_sys = (
            "أنت نموذج ذكاء اصطناعي متخصص في التربية والتعليم الجزائري. "
            "خبرتك محورها المناهج الجزائرية، وزارة التربية الوطنية، "
            "ومعايير dzexams.com. ردودك دقيقة وعلمية وملتزمة بالمنهج الرسمي."
        )
        arcee_out = call_arcee(full_prompt, self.arcee_key, system=arcee_sys)

        # Step 3: Validate & synthesize
        sources_used = "Groq"
        if arcee_out and not arcee_out.startswith("[Arcee unavailable"):
            sources_used = "Groq + Arcee ✓ تم التحقق المتقاطع"
            final = self._validate(groq_out, arcee_out, subject, level)
        else:
            final = groq_out

        return {
            "groq":         groq_out,
            "arcee":        arcee_out,
            "final":        final,
            "sources_used": sources_used,
        }

    def regenerate_arcee_only(self, prompt: str,
                               subject: str = "", level: str = "", grade: str = "") -> str:
        """Regenerate using Arcee model interpretation only."""
        dz_clause = _dz_benchmark_clause(level, subject, grade)
        arcee_sys = (
            "أنت نموذج ذكاء اصطناعي متخصص في التربية والتعليم الجزائري. "
            "ردودك تعتمد حصرياً على المناهج الجزائرية الرسمية."
        )
        return call_arcee(prompt + dz_clause, self.arcee_key, system=arcee_sys)

    def regenerate_groq_only(self, prompt: str,
                              subject: str = "", level: str = "", grade: str = "") -> str:
        """Regenerate using Groq model only."""
        dz_clause = _dz_benchmark_clause(level, subject, grade)
        return call_llm(self.groq_llm, prompt + dz_clause)


def get_hybrid_engine(api_key: str, arcee_key: str,
                      model: str = DEFAULT_GROQ_MODEL) -> CrossCheckAgent:
    """Factory: returns a CrossCheckAgent ready to use."""
    llm = get_llm(model, api_key)
    return CrossCheckAgent(groq_llm=llm, arcee_key=arcee_key)

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 8 — NEW: QR CODE GENERATOR                    ║
# ╚═══════════════════════════════════════════════════════════╝

def generate_qr_code(url: str = APP_URL) -> bytes:
    """Generate a QR code PNG bytes for the given URL."""
    if not _QR_AVAILABLE:
        return b""
    try:
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=3,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#145a32", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()
    except Exception:
        return b""

def qr_code_b64(url: str = APP_URL) -> str:
    data = generate_qr_code(url)
    if not data:
        return ""
    return base64.b64encode(data).decode()

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 9 — NEW: LIVE PREVIEW DASHBOARD               ║
# ╚═══════════════════════════════════════════════════════════╝

def render_live_preview(content: str, title: str, sources_used: str = ""):
    """Render a clean preview dashboard before download."""
    if not content:
        return
    badge_html = ""
    if sources_used:
        badge_html = f'<span class="crosscheck-badge"><span class="crosscheck-icon">✅</span>{sources_used}</span>'
    st.markdown(f"""
    <div class="preview-dashboard">
      <h3>🔍 معاينة المحتوى — {title}</h3>
      {badge_html}
      <div class="preview-content">{content.replace(chr(10), '<br>')}</div>
    </div>
    """, unsafe_allow_html=True)

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 10 — NEW: WORD (.docx) RTL EXPORTS            ║
# ╚═══════════════════════════════════════════════════════════╝

def _set_rtl_paragraph(para):
    """Apply RTL direction to a python-docx paragraph via XML."""
    if not _DOCX_AVAILABLE:
        return
    try:
        pPr = para._p.get_or_add_pPr()
        bidi_el = OxmlElement("w:bidi")
        bidi_el.set(qn("w:val"), "1")
        pPr.insert(0, bidi_el)
    except Exception:
        pass

def _set_rtl_section(doc):
    """Apply RTL to entire document section."""
    if not _DOCX_AVAILABLE:
        return
    try:
        sectPr = doc.sections[0]._sectPr
        bidiEl = OxmlElement("w:bidi")
        sectPr.insert(0, bidiEl)
    except Exception:
        pass

def generate_exam_docx(exam_data: dict) -> bytes:
    """Export exam as .docx with full RTL Arabic support."""
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    _set_rtl_section(doc)
    # Document properties
    doc.core_properties.title = f"اختبار - {exam_data.get('subject','')}"
    doc.core_properties.author = "DONIA MIND — DONIA LABS TECH"
    # Header table (official Algerian format)
    tbl = doc.add_table(rows=3, cols=2)
    tbl.style = "Table Grid"
    cells = [
        ("الجمهورية الجزائرية الديمقراطية الشعبية", "وزارة التربية الوطنية"),
        (f"المؤسسة: {exam_data.get('school','............')}",
         f"السنة الدراسية: {exam_data.get('year','2025/2026')}"),
        (f"المستوى: {exam_data.get('grade','')}  |  المدة: {exam_data.get('duration','ساعتان')}",
         f"مديرية ولاية: {exam_data.get('wilaya','...........')}"),
    ]
    for i, (c1, c2) in enumerate(cells):
        for j, txt in enumerate([c1, c2]):
            cell = tbl.rows[i].cells[j]
            p = cell.paragraphs[0]
            _set_rtl_paragraph(p)
            run = p.add_run(txt)
            run.font.name = "Arial"
            run.font.size = Pt(11)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    doc.add_paragraph()
    # Title
    subj = exam_data.get("subject", "")
    sem  = exam_data.get("semester", "الفصل الثاني")
    title_p = doc.add_paragraph()
    _set_rtl_paragraph(title_p)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(f"اختبار {sem} في مادة {subj}")
    run.bold = True
    run.font.size = Pt(14)
    run.font.name = "Arial"
    doc.add_paragraph()
    # Content
    for line in exam_data.get("content", "").splitlines():
        line = line.strip()
        if not line:
            continue
        p = doc.add_paragraph()
        _set_rtl_paragraph(p)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        is_heading = (re.match(r'^تمرين\s+\d+', line)
                      or re.match(r'^الوضعية الإدماجية', line))
        run = p.add_run(line)
        run.font.name = "Arial"
        run.font.size = Pt(12 if is_heading else 11)
        run.bold = is_heading
    # Footer paragraph
    doc.add_paragraph()
    footer_p = doc.add_paragraph()
    _set_rtl_paragraph(footer_p)
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_p.add_run("انتهى — بالتوفيق والنجاح")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(12)
    # Copyright
    cp_p = doc.add_paragraph()
    _set_rtl_paragraph(cp_p)
    cp_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cp_p.add_run(COPYRIGHT_FOOTER_AR)
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x14, 0x5a, 0x32)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def generate_lesson_plan_docx(plan_data: dict) -> bytes:
    """Export lesson plan as .docx with RTL support."""
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    _set_rtl_section(doc)
    doc.core_properties.title = f"مذكرة درس - {plan_data.get('lesson','')}"
    doc.core_properties.author = "DONIA MIND — DONIA LABS TECH"
    # Title
    title_p = doc.add_paragraph()
    _set_rtl_paragraph(title_p)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(f"مذكرة درس: {plan_data.get('lesson','')}")
    run.bold = True; run.font.size = Pt(15); run.font.name = "Arial"
    # Meta
    meta_lines = [
        f"المادة: {plan_data.get('subject','')}  |  المستوى: {plan_data.get('grade','')}",
        f"الطور: {plan_data.get('level','')}  |  المدة: {plan_data.get('duration','45 دقيقة')}",
        f"المجال: {plan_data.get('domain','')}",
    ]
    for ml in meta_lines:
        p = doc.add_paragraph()
        _set_rtl_paragraph(p)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(ml); run.font.name = "Arial"; run.font.size = Pt(11)
    doc.add_paragraph()
    # Content
    for line in plan_data.get("content","").splitlines():
        line = line.strip()
        if not line:
            continue
        p = doc.add_paragraph()
        _set_rtl_paragraph(p)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        is_h = line.startswith("##") or line.startswith("**")
        run = p.add_run(line.replace("#","").replace("**",""))
        run.bold = is_h; run.font.name = "Arial"
        run.font.size = Pt(12 if is_h else 11)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def generate_report_docx(report_data: dict) -> bytes:
    """Export pedagogical report as .docx with RTL support."""
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    _set_rtl_section(doc)
    # Title
    t_p = doc.add_paragraph()
    _set_rtl_paragraph(t_p)
    t_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = t_p.add_run("التقرير البيداغوجي — DONIA MIND")
    run.bold = True; run.font.size = Pt(15); run.font.name = "Arial"
    doc.add_paragraph()
    for cls in report_data.get("classes", []):
        h = doc.add_paragraph()
        _set_rtl_paragraph(h)
        h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = h.add_run(f"القسم: {cls.get('name','')}")
        run.bold = True; run.font.size = Pt(13); run.font.name = "Arial"
        info = (f"عدد التلاميذ: {cls.get('total',0)}  |  "
                f"المعدل: {safe_f(cls.get('avg',0))}  |  "
                f"أعلى: {safe_f(cls.get('max',0))}  |  "
                f"أدنى: {safe_f(cls.get('min',0))}  |  "
                f"نسبة النجاح: {safe_f(cls.get('pass_rate',0),'.1f')}%")
        p = doc.add_paragraph()
        _set_rtl_paragraph(p)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(info); run.font.name = "Arial"; run.font.size = Pt(11)
    if report_data.get("ai_analysis"):
        doc.add_paragraph()
        h2 = doc.add_paragraph()
        _set_rtl_paragraph(h2)
        run = h2.add_run("التحليل البيداغوجي الذكي:")
        run.bold = True; run.font.name = "Arial"; run.font.size = Pt(12)
        for line in report_data["ai_analysis"].splitlines():
            if line.strip():
                lp = doc.add_paragraph()
                _set_rtl_paragraph(lp)
                lp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                run = lp.add_run(line.strip())
                run.font.name = "Arial"; run.font.size = Pt(11)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 11 — NEW: EXCEL GRADE BOOK (MULTI-SHEET)      ║
# ╚═══════════════════════════════════════════════════════════╝

def generate_grade_book_excel(classes_data: list, subject: str = "",
                               semester: str = "") -> bytes:
    """
    Export grade book (دفتر التنقيط) as .xlsx.
    Each class gets its own sheet: Class 1 → Sheet 1, Class 2 → Sheet 2, etc.
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default blank sheet

    header_fill   = PatternFill("solid", fgColor="145a32")
    alt_fill      = PatternFill("solid", fgColor="EAF6EE")
    title_font    = Font(name="Arial", bold=True, color="FFFFFF", size=12)
    header_font   = Font(name="Arial", bold=True, color="FFFFFF", size=11)
    body_font     = Font(name="Arial", size=11)
    center_align  = Alignment(horizontal="center", vertical="center",
                               wrap_text=True, readingOrder=2)
    right_align   = Alignment(horizontal="right", vertical="center",
                               wrap_text=True, readingOrder=2)
    thin_side     = Side(style="thin", color="27AE60")
    thin_border   = Border(left=thin_side, right=thin_side,
                           top=thin_side, bottom=thin_side)

    for idx, cls in enumerate(classes_data, 1):
        ws = wb.create_sheet(title=f"القسم {idx}")
        ws.sheet_view.rightToLeft = True

        # Row 1: Title
        ws.merge_cells("A1:F1")
        title_cell = ws["A1"]
        title_cell.value  = (f"دفتر التنقيط — {cls.get('name',f'القسم {idx}')} "
                              f"| {subject} | {semester}")
        title_cell.font   = Font(name="Arial", bold=True, color="FFFFFF", size=13)
        title_cell.fill   = PatternFill("solid", fgColor="0A3D1F")
        title_cell.alignment = center_align
        ws.row_dimensions[1].height = 28

        # Row 2: Subheader info
        ws.merge_cells("A2:F2")
        sub_cell = ws["A2"]
        sub_cell.value = (f"عدد التلاميذ: {cls.get('total',0)}  |  "
                          f"المعدل العام: {safe_f(cls.get('avg',0))}  |  "
                          f"نسبة النجاح: {safe_f(cls.get('pass_rate',0),'.1f')}%  |  "
                          f"DONIA MIND © 2026")
        sub_cell.font      = Font(name="Arial", size=10, color="145a32")
        sub_cell.alignment = center_align

        # Row 4: Column headers
        headers = ["الرقم", "اسم التلميذ", "تقويم /20", "فرض /20",
                   "اختبار /20", "المعدل /20", "الملاحظة"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font      = header_font
            cell.fill      = header_fill
            cell.alignment = center_align
            cell.border    = thin_border
        ws.row_dimensions[4].height = 24

        # Data rows
        students = cls.get("students", [])
        if not students:
            # Create empty rows for manual filling
            for r in range(1, 36):
                for c in range(1, 8):
                    cell = ws.cell(row=4 + r, column=c,
                                   value=r if c == 1 else "")
                    cell.font      = body_font
                    cell.alignment = center_align if c != 2 else right_align
                    cell.border    = thin_border
                    if r % 2 == 0:
                        cell.fill = alt_fill
        else:
            for r, stu in enumerate(students, 1):
                row_data = [
                    r,
                    stu.get("name",""),
                    stu.get("taqwim",""),
                    stu.get("fard",""),
                    stu.get("ikhtibhar",""),
                    stu.get("avg",""),
                    stu.get("appreciation",""),
                ]
                for c, val in enumerate(row_data, 1):
                    cell = ws.cell(row=4 + r, column=c, value=val)
                    cell.font      = body_font
                    cell.alignment = right_align if c == 2 else center_align
                    cell.border    = thin_border
                    if r % 2 == 0:
                        cell.fill = alt_fill

        # Column widths
        col_widths = [7, 32, 13, 13, 13, 13, 14]
        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

        # Summary row
        last_row = 4 + max(len(students), 35) + 2
        ws.cell(row=last_row, column=1, value="المجموع / المعدل")
        ws.cell(row=last_row, column=1).font = Font(name="Arial", bold=True, size=11)
        ws.cell(row=last_row, column=1).alignment = center_align
        ws.merge_cells(f"A{last_row}:B{last_row}")

        # Footer copyright
        foot_row = last_row + 2
        ws.merge_cells(f"A{foot_row}:G{foot_row}")
        foot_cell = ws.cell(row=foot_row, column=1, value=COPYRIGHT_FOOTER_AR)
        foot_cell.font      = Font(name="Arial", size=9, color="145A32", italic=True)
        foot_cell.alignment = center_align

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()

def parse_grade_book_excel(uploaded_file) -> list:
    """
    Parse an uploaded Excel grade book.
    Returns list of dicts with class data from each sheet.
    Supports both pandas/openpyxl backends.
    """
    results = []
    try:
        wb = openpyxl.load_workbook(uploaded_file, data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            students = []
            for row in rows[4:]:  # skip header rows
                if row and row[1]:  # has name
                    try:
                        students.append({
                            "name":         str(row[1] or ""),
                            "taqwim":       float(row[2] or 0),
                            "fard":         float(row[3] or 0),
                            "ikhtibhar":    float(row[4] or 0),
                            "avg":          float(row[5] or 0) if row[5] else
                                            calc_average(row[2], row[3], row[4]),
                            "appreciation": get_appreciation(float(row[5] or 0))
                                            if row[5] else "",
                        })
                    except (TypeError, ValueError):
                        pass
            if students:
                avgs = [s["avg"] for s in students if s["avg"] > 0]
                results.append({
                    "name":      sheet_name,
                    "students":  students,
                    "total":     len(students),
                    "avg":       round(sum(avgs)/len(avgs), 2) if avgs else 0,
                    "max":       max(avgs) if avgs else 0,
                    "min":       min(avgs) if avgs else 0,
                    "pass_rate": round(sum(1 for a in avgs if a >= 10)/len(avgs)*100, 1) if avgs else 0,
                    "distribution": {
                        "0-5":   sum(1 for a in avgs if a < 5),
                        "5-10":  sum(1 for a in avgs if 5 <= a < 10),
                        "10-15": sum(1 for a in avgs if 10 <= a < 15),
                        "15-20": sum(1 for a in avgs if a >= 15),
                    }
                })
    except Exception:
        pass
    return results

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 12 — PDF GENERATORS (ORIGINAL + ENHANCED)    ║
# ╚═══════════════════════════════════════════════════════════╝

def generate_simple_pdf(content: str, title: str,
                         subtitle: str = "", rtl: bool = True) -> bytes:
    buf = io.BytesIO()
    _register_arabic_pdf_fonts()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.2*cm,  bottomMargin=2.0*cm)
    S = make_pdf_styles(rtl)
    story = []
    align_hdr = "RIGHT" if rtl else "LEFT"
    head_tbl = Table(
        [[Paragraph(pdf_text_line("الجمهورية الجزائرية الديمقراطية الشعبية", True), S["center"]),
          Paragraph(pdf_text_line("وزارة التربية الوطنية", True), S["center"])],
         [Paragraph(pdf_text_line("DONIA MIND — المعلم الذكي", True), S["center"]),
          Paragraph(pdf_text_line("وثيقة رقمية — نسخة قابلة للطباعة", True), S["center"])]],
        colWidths=[8.2*cm, 8.2*cm],
    )
    head_tbl.setStyle(TableStyle([
        ("ALIGN",        (0,0), (-1,-1), align_hdr),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("BOX",          (0,0), (-1,-1), 0.5, rl_colors.black),
        ("BACKGROUND",   (0,0), (-1,-1), rl_colors.HexColor("#f4f2ff")),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
    ]))
    story.append(head_tbl)
    story.append(Spacer(1, 8))
    story.append(Paragraph(pdf_text_line(f"DONIA MIND | {title}", rtl), S["title"]))
    if subtitle:
        story.append(Paragraph(pdf_text_line(subtitle, rtl), S["center"]))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=rl_colors.HexColor("#0d9488")))
    story.append(Spacer(1, 10))
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("##"):
            story.append(Spacer(1, 6))
            story.append(Paragraph(pdf_text_line(line.replace("#",""), rtl), S["h2"]))
        elif line.startswith("$") or "```" in line:
            msg = "[ معادلة – راجع النسخة الرقمية ]" if rtl else "[Equation — see digital version]"
            story.append(Paragraph(pdf_text_line(msg, rtl), S["small"]))
        else:
            story.append(Paragraph(pdf_text_line(line, rtl), S["body"]))
        story.append(Spacer(1, 2))
    doc.build(story, **_pdf_footer_canvas_args())
    buf.seek(0)
    return buf.read()


def generate_exam_pdf(exam_data: dict) -> bytes:
    buf  = io.BytesIO()
    subj = exam_data.get("subject","") or ""
    rtl, lang = get_pdf_mode_for_subject(subj)
    S = make_pdf_styles(rtl)
    _register_arabic_pdf_fonts()
    fn_b = _AR_FONT_BOLD if rtl else "Helvetica-Bold"
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.8*cm, leftMargin=1.8*cm,
                            topMargin=1.5*cm,   bottomMargin=2.0*cm)
    story = []
    def _cell(txt: str) -> Paragraph:
        return Paragraph(pdf_text_line(txt, True), make_pdf_styles(True)["body"])
    header_data = [
        [_cell("الجمهورية الجزائرية الديمقراطية الشعبية"), _cell("")],
        [_cell(f"المؤسسة: {exam_data.get('school','..................')}"),
         _cell("وزارة التربية الوطنية")],
        [_cell(f"مديرية التربية لولاية: {exam_data.get('wilaya','..............')}"),
         _cell(f"السنة الدراسية: {exam_data.get('year','2025/2026')}")],
        [_cell(f"المقاطعة: {exam_data.get('district','.....')} | "
               f"المستوى: {exam_data.get('grade','')} | "
               f"المدة: {exam_data.get('duration','ساعتان')}"), _cell("")],
    ]
    t = Table(header_data, colWidths=[10*cm, 6.5*cm])
    t.setStyle(TableStyle([
        ('ALIGN',      (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN',       (0,0), (1,0)),
        ('SPAN',       (0,3), (1,3)),
        ('GRID',       (0,0), (-1,-1), 0.5, rl_colors.black),
        ('BACKGROUND', (0,0), (-1,0), rl_colors.HexColor("#f0f0f0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))
    title_style = ParagraphStyle(
        "exam_etitle_" + ("rtl" if rtl else "ltr"),
        fontName=fn_b if rtl else "Helvetica-Bold",
        fontSize=14, alignment=TA_CENTER, leading=20,
        textColor=rl_colors.HexColor("#000000"))
    exam_title = (
        f"اختبار {exam_data.get('semester','الفصل الثاني')} "
        f"في مادة {exam_data.get('subject','')}"
    ) if rtl else (
        f"Exam — {exam_data.get('semester','')} — "
        f"{lang} / {exam_data.get('subject','')}"
    )
    story.append(Paragraph(pdf_text_line(exam_title, rtl), title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=rl_colors.black))
    story.append(Spacer(1, 10))
    exhead_style = ParagraphStyle(
        "exam_exhead_" + ("rtl" if rtl else "ltr"),
        fontName=fn_b if rtl else "Helvetica-Bold",
        fontSize=12, alignment=(TA_RIGHT if rtl else TA_LEFT),
        leading=18, textColor=rl_colors.HexColor("#000000"))
    for line in exam_data.get("content","").splitlines():
        line = line.strip()
        if not line:
            continue
        if (re.match(r'^تمرين\s+\d+', line) or
            re.match(r'^الوضعية الإدماجية', line) or
            re.match(r'^(Exercise|Part|Situation)\s*\d*', line, re.I)):
            story.append(Spacer(1, 6))
            story.append(Paragraph(pdf_text_line(line, rtl), exhead_style))
        elif line.startswith("$") or "```" in line:
            msg = "[معادلة]" if rtl else "[Equation]"
            story.append(Paragraph(pdf_text_line(msg, rtl), S["small"]))
        else:
            story.append(Paragraph(pdf_text_line(line, rtl), S["body"]))
        story.append(Spacer(1, 2))
    story.append(Spacer(1, 12))
    end_msg = "انتهى — بالتوفيق والنجاح" if rtl else "— End — Good luck"
    story.append(Paragraph(pdf_text_line(end_msg, rtl),
                            ParagraphStyle("exam_end_" + ("rtl" if rtl else "ltr"),
                                           fontName=fn_b if rtl else "Helvetica-Bold",
                                           fontSize=11, alignment=TA_CENTER)))
    doc.build(story, **_pdf_footer_canvas_args())
    buf.seek(0)
    return buf.read()


def generate_report_pdf(report_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm,  bottomMargin=2.0*cm)
    _register_arabic_pdf_fonts()
    S = make_pdf_styles(True)
    story = []
    story.append(Paragraph(ar("تحليل نتائج الأقسام — التقرير البيداغوجي"), S["title"]))
    story.append(Paragraph(
        ar(f"{report_data.get('school','')} | "
           f"{report_data.get('subject','')} | "
           f"{report_data.get('semester','')}"),
        S["center"]))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=rl_colors.HexColor("#0d9488")))
    story.append(Spacer(1, 12))
    for cls in report_data.get("classes", []):
        story.append(Paragraph(ar(f"تحليل نتائج القسم {cls['name']}"), S["h2"]))
        info_line = (
            f"عدد التلاميذ: {cls.get('total',0)} — "
            f"المعدل: {safe_f(cls.get('avg',0))} — "
            f"أعلى: {safe_f(cls.get('max',0))} — "
            f"أدنى: {safe_f(cls.get('min',0))} — "
            f"النجاح: {safe_f(cls.get('pass_rate',0),'.1f')}%"
        )
        story.append(Paragraph(ar(info_line), S["body"]))
        story.append(Spacer(1, 6))
        if cls.get("top5"):
            story.append(Paragraph(ar("أفضل 5 تلاميذ"), S["h2"]))
            top_data = [[
                Paragraph(ar("الرتبة"), S["body"]),
                Paragraph(ar("الاسم"),  S["body"]),
                Paragraph(ar("المعدل"), S["body"]),
            ]]
            for i, s in enumerate(cls["top5"], 1):
                top_data.append([
                    Paragraph(str(i),          S["body"]),
                    Paragraph(ar(s["name"]),   S["body"]),
                    Paragraph(safe_f(s["avg"]),S["body"]),
                ])
            t = Table(top_data, colWidths=[2*cm, 10*cm, 3*cm])
            t.setStyle(TableStyle([
                ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
                ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND',   (0,0), (-1,0),  rl_colors.HexColor("#667eea")),
                ('TEXTCOLOR',    (0,0), (-1,0),  rl_colors.white),
                ('GRID',         (0,0), (-1,-1),  0.5, rl_colors.grey),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),
                 [rl_colors.white, rl_colors.HexColor("#f8f8ff")]),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))
        if cls.get("distribution"):
            story.append(Paragraph(ar("توزيع الدرجات"), S["h2"]))
            dist = cls["distribution"]
            dist_data = [
                [Paragraph(ar("0-5"), S["body"]),  Paragraph(ar("5-10"), S["body"]),
                 Paragraph(ar("10-15"),S["body"]), Paragraph(ar("15-20"),S["body"])],
                [Paragraph(str(dist.get("0-5",0)),  S["body"]),
                 Paragraph(str(dist.get("5-10",0)), S["body"]),
                 Paragraph(str(dist.get("10-15",0)),S["body"]),
                 Paragraph(str(dist.get("15-20",0)),S["body"])],
            ]
            t2 = Table(dist_data, colWidths=[4*cm]*4)
            t2.setStyle(TableStyle([
                ('ALIGN',      (0,0),(-1,-1),'CENTER'),
                ('VALIGN',     (0,0),(-1,-1),'MIDDLE'),
                ('BACKGROUND', (0,0),(-1,0), rl_colors.HexColor("#302b63")),
                ('TEXTCOLOR',  (0,0),(-1,0), rl_colors.white),
                ('GRID',       (0,0),(-1,-1), 0.5, rl_colors.grey),
            ]))
            story.append(t2)
            story.append(Spacer(1, 16))
    if report_data.get("ai_analysis"):
        story.append(Paragraph(ar("التحليل البيداغوجي الذكي (Groq + Arcee)"), S["h2"]))
        for line in report_data["ai_analysis"].splitlines():
            if line.strip():
                story.append(Paragraph(ar(line.strip()), S["body"]))
    doc.build(story, **_pdf_footer_canvas_args())
    buf.seek(0)
    return buf.read()

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 13 — ANIMATED ROBOT SVG (v3.0)                ║
# ╚═══════════════════════════════════════════════════════════╝

ROBOT_SVG = """
<svg viewBox="0 0 110 110" xmlns="http://www.w3.org/2000/svg">
  <!-- Antenna -->
  <g class="robot-antenna">
    <line x1="55" y1="10" x2="55" y2="20" stroke="#27ae60" stroke-width="2.5" stroke-linecap="round"/>
    <circle cx="55" cy="8" r="4" fill="#c0392b"/>
    <circle cx="55" cy="8" r="2" fill="#ff6b6b" opacity="0.8"/>
  </g>
  <!-- Head -->
  <g class="robot-body">
    <rect x="28" y="20" width="54" height="42" rx="12" ry="12"
          fill="url(#headGrad)" stroke="#27ae60" stroke-width="2"/>
    <!-- Eyes -->
    <g class="robot-eye-l">
      <circle cx="42" cy="36" r="8" fill="#0a3d1f"/>
      <circle cx="42" cy="36" r="5" fill="#00d2d3"/>
      <circle cx="44" cy="34" r="2" fill="white" opacity="0.9"/>
    </g>
    <g class="robot-eye-r">
      <circle cx="68" cy="36" r="8" fill="#0a3d1f"/>
      <circle cx="68" cy="36" r="5" fill="#00d2d3"/>
      <circle cx="70" cy="34" r="2" fill="white" opacity="0.9"/>
    </g>
    <!-- Mouth / smile -->
    <path class="robot-mouth" d="M 42 54 Q 55 63 68 54"
          stroke="#27ae60" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <!-- Cheek dots -->
    <circle cx="35" cy="48" r="4" fill="#c0392b" opacity="0.4"/>
    <circle cx="75" cy="48" r="4" fill="#c0392b" opacity="0.4"/>
  </g>
  <!-- Body -->
  <g class="robot-body">
    <rect x="32" y="64" width="46" height="30" rx="8" ry="8"
          fill="url(#bodyGrad)" stroke="#27ae60" stroke-width="2"/>
    <!-- Chest panel -->
    <rect x="42" y="70" width="26" height="16" rx="4" ry="4"
          fill="#0a3d1f" opacity="0.7"/>
    <circle cx="49" cy="78" r="3" fill="#00d2d3"/>
    <circle cx="55" cy="78" r="3" fill="#27ae60"/>
    <circle cx="61" cy="78" r="3" fill="#c0392b"/>
  </g>
  <!-- Defs -->
  <defs>
    <linearGradient id="headGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e8449"/>
      <stop offset="100%" stop-color="#145a32"/>
    </linearGradient>
    <linearGradient id="bodyGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#145a32"/>
      <stop offset="100%" stop-color="#0a3d1f"/>
    </linearGradient>
  </defs>
</svg>
"""

def render_robot_hero():
    """Renders the animated robot hero section."""
    st.markdown(f"""
    <div class="donia-robot-wrap">
      <div class="donia-robot-v3">{ROBOT_SVG}</div>
    </div>
    """, unsafe_allow_html=True)

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 14 — PEDAGOGICAL REPORT (AUTO-DISPLAY)        ║
# ╚═══════════════════════════════════════════════════════════╝

def render_auto_pedagogical_report(classes_data: list, subject: str,
                                    semester: str, agent: CrossCheckAgent):
    """
    RPT-1: Auto-display pedagogical report after every analysis session.
    Generates AI analysis using hybrid engine and shows immediately.
    """
    if not classes_data:
        return
    st.markdown("---")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0a3d1f,#145a32);
    border-radius:16px;padding:1.2rem 1.5rem;margin:.5rem 0;direction:rtl;text-align:right;">
      <h3 style="color:#a8f0c0;margin:0">📊 التقرير البيداغوجي التلقائي</h3>
      <p style="color:rgba(255,255,255,.8);margin:.3rem 0 0;font-size:.9rem">
        يُنشأ تلقائياً بعد كل جلسة تحليل — مدعوم بالذكاء الهجين (Groq + Arcee)
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Build summary for AI prompt
    summary_lines = []
    for cls in classes_data:
        summary_lines.append(
            f"القسم {cls.get('name','')}: "
            f"عدد={cls.get('total',0)}, "
            f"معدل={safe_f(cls.get('avg',0))}/20, "
            f"نجاح={safe_f(cls.get('pass_rate',0),'.1f')}%, "
            f"أعلى={safe_f(cls.get('max',0))}, أدنى={safe_f(cls.get('min',0))}"
        )
    summary_text = "\n".join(summary_lines)

    prompt = (
        f"أنت مختص في التحليل البيداغوجي للمنظومة التربوية الجزائرية.\n"
        f"فيما يلي نتائج الأقسام في مادة '{subject}' لـ '{semester}':\n\n"
        f"{summary_text}\n\n"
        f"اكتب تقريراً بيداغوجياً شاملاً يتضمن:\n"
        f"1. تحليل المستوى العام وتشخيص نقاط القوة والضعف\n"
        f"2. تفسير الفوارق بين الأقسام إن وُجدت\n"
        f"3. توصيات بيداغوجية عملية للأستاذ\n"
        f"4. مقترحات للتقوية والدعم البيداغوجي\n"
        f"5. خلاصة تقييمية مرفوعة إلى مدير المؤسسة\n"
        f"اكتب بالعربية الفصحى الواضحة في أسلوب رسمي مهني."
    )

    with st.spinner("⚙️ جاري إنشاء التقرير البيداغوجي بالذكاء الهجين..."):
        result = agent.generate(prompt, subject=subject, level="", grade="")

    st.markdown(f"""
    <div class="crosscheck-badge">
      <span class="crosscheck-icon">✅</span>
      {result['sources_used']}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 عرض التقرير البيداغوجي الكامل", expanded=True):
        st.markdown(f"""
        <div class="result-box">
          {result['final'].replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    # Store in session for download
    report_data = {
        "school":       st.session_state.get("school_name",""),
        "subject":      subject,
        "semester":     semester,
        "classes":      classes_data,
        "ai_analysis":  result["final"],
    }
    st.session_state["last_report_data"] = report_data

    col1, col2, col3 = st.columns(3)
    with col1:
        pdf_bytes = generate_report_pdf(report_data)
        if pdf_bytes:
            st.download_button("⬇️ PDF التقرير", pdf_bytes,
                               file_name=f"rapport_pedagogique_{subject}_{semester}.pdf",
                               mime="application/pdf", key="auto_rpt_pdf")
    with col2:
        if _DOCX_AVAILABLE:
            docx_bytes = generate_report_docx(report_data)
            if docx_bytes:
                st.download_button("⬇️ Word التقرير", docx_bytes,
                                   file_name=f"rapport_pedagogique_{subject}_{semester}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   key="auto_rpt_docx")
    with col3:
        if classes_data:
            xl_bytes = generate_grade_book_excel(classes_data, subject, semester)
            if xl_bytes:
                st.download_button("⬇️ Excel دفتر التنقيط", xl_bytes,
                                   file_name=f"cahier_de_notes_{subject}_{semester}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="auto_rpt_excel")

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 15 — SIDEBAR                                  ║
# ╚═══════════════════════════════════════════════════════════╝

def render_sidebar():
    with st.sidebar:
        # Logo
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "assets", "logo_donia.jpg")
        if os.path.isfile(logo_path):
            st.image(logo_path, use_column_width=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:.5rem;">
              <div style="font-size:2.5rem;">🎓</div>
              <div style="font-weight:800;color:#145a32;font-size:1.1rem;">DONIA MIND</div>
            </div>""", unsafe_allow_html=True)

        # Slogan bar
        st.markdown("""
        <div class="donia-slogan-bar">
          <span class="donia-slogan-ar">بالعلم نرتقي</span>
          <div class="donia-slogan-divider"></div>
          <span class="donia-slogan-en">Education Uplifts Us</span>
        </div>""", unsafe_allow_html=True)

        # Hybrid engine badges
        st.markdown("""
        <div style="text-align:center;margin:.5rem 0">
          <span class="hybrid-badge"><span class="dot"></span>Groq LLM</span>
          <span class="hybrid-badge"><span class="dot"></span>Arcee AI</span>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # API Keys section
        st.markdown("""
        <div class="api-book-widget">
          <span class="api-book-icon">📖</span>
          <span class="api-book-slogan">العلم هو السلاح</span>
        </div>""", unsafe_allow_html=True)

        # Groq key
        groq_key_default = _get_secret("GROQ_API_KEY")
        groq_key = st.text_input(
            "🔑 مفتاح Groq API",
            value=groq_key_default,
            type="password",
            key="groq_api_key_input",
            help="احصل عليه من console.groq.com"
        )
        groq_active = bool(groq_key and len(groq_key) > 10)
        if groq_active:
            st.markdown('<span class="api-book-status-active">✅ Groq نشط</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span class="api-book-status-inactive">⚠️ أدخل مفتاح Groq</span>',
                        unsafe_allow_html=True)

        # Arcee key
        arcee_key_default = _get_secret("ARCEE_API_KEY")
        arcee_key = st.text_input(
            "🔑 مفتاح Arcee API",
            value=arcee_key_default,
            type="password",
            key="arcee_api_key_input",
            help="من models.arcee.ai — يضيف دقة تربوية جزائرية"
        )
        arcee_active = bool(arcee_key and len(arcee_key) > 10)
        if arcee_active:
            st.markdown('<span class="api-book-status-active">✅ Arcee نشط — تحقق مزدوج مفعّل</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span class="api-book-status-inactive">ℹ️ Arcee اختياري (يُحسّن الدقة)</span>',
                        unsafe_allow_html=True)

        st.markdown("---")

        # Model selector
        sel_model = st.selectbox(
            "🤖 نموذج Groq",
            GROQ_MODELS,
            index=0,
            key="groq_model_sel"
        )

        # School info
        st.session_state["school_name"] = st.text_input(
            "🏫 اسم المؤسسة",
            value=st.session_state.get("school_name",""),
            placeholder="ثانوية / متوسطة / ابتدائية ..."
        )

        st.markdown("---")

        # Stats
        total, plans, exams, corr = get_stats()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="stat-card"><h2>{total}</h2><p>تمارين</p></div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="stat-card"><h2>{exams}</h2><p>اختبارات</p></div>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card"><h2>{plans}</h2><p>مذكرات</p></div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="stat-card"><h2>{corr}</h2><p>تصحيحات</p></div>',
                        unsafe_allow_html=True)

        st.markdown("---")

        # QR Code
        st.markdown("**📲 رمز QR للتطبيق**")
        if _QR_AVAILABLE:
            qr_b64 = qr_code_b64(APP_URL)
            if qr_b64:
                st.markdown(f"""
                <div style="text-align:center;background:#fff;
                border:2px solid #27ae60;border-radius:12px;padding:.5rem;">
                  <img src="data:image/png;base64,{qr_b64}"
                       style="width:130px;height:130px;" alt="QR DONIA MIND"/>
                  <div style="font-size:.75rem;color:#145a32;font-weight:600;margin-top:.3rem">
                    امسح للوصول للتطبيق
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"🔗 [فتح التطبيق]({APP_URL})")

        st.markdown("---")

        # Social links
        st.markdown(f"""
        <div class="donia-social">
          <a href="{SOCIAL_URL_WHATSAPP}" target="_blank">📱 واتساب</a>
          <a href="{SOCIAL_URL_TELEGRAM}" target="_blank">✈️ تيليغرام</a>
          <a href="{SOCIAL_URL_FACEBOOK}" target="_blank">👥 فيسبوك</a>
          <a href="{SOCIAL_URL_LINKEDIN}" target="_blank">💼 لينكدإن</a>
        </div>""", unsafe_allow_html=True)

    return groq_key, arcee_key, sel_model

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 16 — CURRICULUM SELECTORS                     ║
# ╚═══════════════════════════════════════════════════════════╝

def curriculum_selectors(prefix: str = "default") -> tuple:
    """Return (level, grade, branch, subject, subjects_list)."""
    level = st.selectbox("📚 الطور الدراسي", list(CURRICULUM.keys()), key=f"level_{prefix}")
    curr  = CURRICULUM[level]
    grade = st.selectbox("🎓 المستوى", curr["grades"], key=f"grade_{prefix}")
    branch = None
    subjects = []
    if curr["branches"]:
        branches_for_grade = curr["branches"].get(grade, {})
        if branches_for_grade:
            branch = st.selectbox("🌿 الشعبة", list(branches_for_grade.keys()),
                                   key=f"branch_{prefix}")
            subjects = branches_for_grade.get(branch, [])
    if not subjects:
        subj_dict = curr.get("subjects") or {}
        subjects  = subj_dict.get(grade) or subj_dict.get("_default") or []
    subject = st.selectbox("📖 المادة", subjects, key=f"subject_{prefix}") if subjects else ""
    return level, grade, branch, subject, subjects

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 17 — TAB: EXAM GENERATOR                      ║
# ╚═══════════════════════════════════════════════════════════╝

def tab_exam_generator(groq_key: str, arcee_key: str, model: str):
    st.markdown("### 📝 توليد الاختبارات الرسمية")
    level, grade, branch, subject, _ = curriculum_selectors("exam")
    col1, col2 = st.columns(2)
    with col1:
        semester = st.selectbox("📅 الفصل", ["الفصل الأول","الفصل الثاني","الفصل الثالث"],
                                 key="exam_sem")
        duration = st.selectbox("⏱️ المدة", ["ساعة واحدة","ساعتان","ساعة ونصف","3 ساعات"],
                                 key="exam_dur")
        difficulty = st.selectbox("⚡ المستوى",
                                   ["متوسط","سهل","صعب","مختلط"],
                                   key="exam_diff")
    with col2:
        school    = st.text_input("🏫 اسم المؤسسة",
                                   value=st.session_state.get("school_name",""),
                                   key="exam_school")
        wilaya    = st.text_input("🗺️ الولاية", key="exam_wilaya",
                                   placeholder="مثال: تيارت")
        year      = st.text_input("📆 السنة الدراسية", value="2025/2026",
                                   key="exam_year")
        num_ex    = st.slider("عدد التمارين", 1, 5, 3, key="exam_nexo")

    extra_instr = st.text_area("📌 تعليمات إضافية (اختياري)", key="exam_extra",
                                placeholder="مثلاً: ركّز على الوضعية الإدماجية...")

    if st.button("🚀 توليد الاختبار بالذكاء الهجين", key="gen_exam_btn"):
        if not groq_key:
            st.markdown('<div class="error-box">⚠️ أدخل مفتاح Groq API أولاً</div>',
                        unsafe_allow_html=True)
            return
        lang_clause = llm_output_language_clause(subject)
        prompt = (
            f"أنت أستاذ خبير في إعداد الاختبارات الجزائرية الرسمية.\n"
            f"أنشئ اختبار {semester} كامل في مادة {subject} للمستوى {grade} ({level}).\n"
            f"الفصل: {semester} | المدة: {duration} | المستوى: {difficulty}\n"
            f"عدد التمارين: {num_ex}\n"
            f"متطلبات الاختبار:\n"
            f"- التوافق الكامل مع منهاج وزارة التربية الجزائرية\n"
            f"- تضمين وضعية إدماجية في النهاية\n"
            f"- توزيع عادل للنقاط (المجموع 20 نقطة)\n"
            f"- تنوع مستويات الأسئلة (معرفة، فهم، تطبيق، تحليل)\n"
            f"{extra_instr if extra_instr else ''}\n"
            f"{lang_clause}"
        )
        rtl, _ = get_pdf_mode_for_subject(subject)
        agent  = get_hybrid_engine(groq_key, arcee_key, model)
        with st.spinner("⚙️ يعمل الذكاء الهجين (Groq + Arcee)..."):
            result = agent.generate(prompt, subject=subject, level=level, grade=grade)
        content       = result["final"]
        sources_used  = result["sources_used"]

        # Save to session
        exam_data = {
            "level": level, "grade": grade, "branch": branch or "",
            "subject": subject, "semester": semester,
            "school": school, "wilaya": wilaya, "year": year,
            "duration": duration, "content": content,
        }
        st.session_state["last_exam_data"]    = exam_data
        st.session_state["last_exam_prompt"]  = prompt
        st.session_state["last_exam_sources"] = sources_used
        db_exec("INSERT INTO exams (level,grade,subject,semester,content,created_at) VALUES (?,?,?,?,?,?)",
                (level, grade, subject, semester, content, datetime.now().isoformat()))

        # Live Preview
        render_live_preview(content, f"اختبار {subject} — {semester}", sources_used)

        # Download buttons
        st.markdown("#### ⬇️ تنزيل الاختبار")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            pdf = generate_exam_pdf(exam_data)
            st.download_button("📄 PDF رسمي", pdf,
                               file_name=f"exam_{subject}_{semester}.pdf",
                               mime="application/pdf", key="dl_exam_pdf")
        with dc2:
            if _DOCX_AVAILABLE:
                docx_b = generate_exam_docx(exam_data)
                st.download_button("📝 Word (.docx)", docx_b,
                                   file_name=f"exam_{subject}_{semester}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   key="dl_exam_docx")
        with dc3:
            # Blank grade book for this exam
            blank_cls = [{"name": f"القسم {i}", "students": [], "total": 35,
                           "avg": 0, "max": 0, "min": 0, "pass_rate": 0,
                           "distribution": {}} for i in range(1, 4)]
            xl_b = generate_grade_book_excel(blank_cls, subject, semester)
            st.download_button("📊 دفتر التنقيط (Excel)", xl_b,
                               file_name=f"carnet_notes_{subject}_{semester}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_exam_excel")

    # ── Regenerate with Alternative Model ─────────────────────
    if st.session_state.get("last_exam_data"):
        st.markdown("---")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("🔄 إعادة التوليد بنموذج Arcee فقط", key="regen_arcee_exam"):
                if arcee_key:
                    agent  = get_hybrid_engine(groq_key, arcee_key, model)
                    prompt = st.session_state.get("last_exam_prompt","")
                    with st.spinner("⚙️ Arcee يعيد التوليد..."):
                        new_content = agent.regenerate_arcee_only(
                            prompt, subject=subject, level=level, grade=grade)
                    render_live_preview(new_content,
                                        f"اختبار (Arcee) {subject}", "Arcee AI فقط")
                else:
                    st.warning("⚠️ أدخل مفتاح Arcee للاستخدام")
        with col_r2:
            if st.button("🔄 إعادة التوليد بنموذج Groq فقط", key="regen_groq_exam"):
                if groq_key:
                    agent  = get_hybrid_engine(groq_key, arcee_key, model)
                    prompt = st.session_state.get("last_exam_prompt","")
                    with st.spinner("⚙️ Groq يعيد التوليد..."):
                        new_content = agent.regenerate_groq_only(
                            prompt, subject=subject, level=level, grade=grade)
                    render_live_preview(new_content,
                                        f"اختبار (Groq) {subject}", "Groq فقط")
                else:
                    st.warning("⚠️ أدخل مفتاح Groq")

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 18 — TAB: LESSON PLAN GENERATOR               ║
# ╚═══════════════════════════════════════════════════════════╝

def tab_lesson_plan(groq_key: str, arcee_key: str, model: str):
    st.markdown("### 📚 توليد مذكرة الدرس")
    level, grade, branch, subject, _ = curriculum_selectors("plan")
    lesson  = st.text_input("📖 عنوان الدرس", key="plan_lesson",
                             placeholder="مثال: الدوال الأسية والتآلفية")
    domains_list = DOMAINS.get(subject, ["عام"])
    domain  = st.selectbox("🎯 المجال / الميدان", domains_list, key="plan_domain")
    duration= st.selectbox("⏱️ المدة", ["45 دقيقة","1 ساعة","ساعة ونصف"], key="plan_dur")

    if st.button("🚀 توليد المذكرة بالذكاء الهجين", key="gen_plan_btn"):
        if not groq_key:
            st.markdown('<div class="error-box">⚠️ أدخل مفتاح Groq API</div>',
                        unsafe_allow_html=True)
            return
        if not lesson:
            st.markdown('<div class="warn-box">⚠️ أدخل عنوان الدرس</div>',
                        unsafe_allow_html=True)
            return
        lang_clause = llm_output_language_clause(subject)
        prompt = (
            f"أنت مفتش تربوي متخصص في إعداد مذكرات الدروس الجزائرية.\n"
            f"أعدّ مذكرة درس كاملة ومفصّلة لدرس: '{lesson}'\n"
            f"المادة: {subject} | المستوى: {grade} | الطور: {level}\n"
            f"المجال: {domain} | المدة: {duration}\n\n"
            f"يجب أن تشمل المذكرة:\n"
            f"1. الكفاءة المستهدفة وبصيرة الأداء\n"
            f"2. الأهداف التعلمية (المعرفية، المهارية، الوجدانية)\n"
            f"3. الوسائل والأدوات التعليمية\n"
            f"4. سير الحصة (الوضعية الانطلاقية، بناء التعلمات، التقييم)\n"
            f"5. أنشطة التقييم والمتابعة\n"
            f"6. التقويم والعلاج\n"
            f"{lang_clause}"
        )
        agent  = get_hybrid_engine(groq_key, arcee_key, model)
        with st.spinner("⚙️ الذكاء الهجين يُعدّ المذكرة..."):
            result = agent.generate(prompt, subject=subject, level=level, grade=grade)
        content      = result["final"]
        sources_used = result["sources_used"]
        plan_data = {
            "level": level, "grade": grade, "subject": subject,
            "lesson": lesson, "domain": domain, "duration": duration,
            "content": content,
        }
        st.session_state["last_plan_data"]   = plan_data
        st.session_state["last_plan_prompt"] = prompt
        db_exec("INSERT INTO lesson_plans (level,grade,subject,lesson,domain,duration,content,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (level, grade, subject, lesson, domain, duration, content, datetime.now().isoformat()))

        render_live_preview(content, f"مذكرة: {lesson}", sources_used)

        p1, p2 = st.columns(2)
        with p1:
            rtl, _ = get_pdf_mode_for_subject(subject)
            pdf_b  = generate_simple_pdf(content, f"مذكرة: {lesson}",
                                          subtitle=f"{subject} | {grade}", rtl=rtl)
            st.download_button("📄 PDF المذكرة", pdf_b,
                               file_name=f"fiche_{lesson[:30]}.pdf",
                               mime="application/pdf", key="dl_plan_pdf")
        with p2:
            if _DOCX_AVAILABLE:
                docx_b = generate_lesson_plan_docx(plan_data)
                st.download_button("📝 Word المذكرة", docx_b,
                                   file_name=f"fiche_{lesson[:30]}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   key="dl_plan_docx")

    # Regenerate toggle
    if st.session_state.get("last_plan_data"):
        st.markdown("---")
        if st.button("🔄 إعادة التوليد بنموذج بديل", key="regen_plan"):
            if arcee_key and groq_key:
                agent  = get_hybrid_engine(groq_key, arcee_key, model)
                prompt = st.session_state.get("last_plan_prompt","")
                with st.spinner("⚙️ Arcee يعيد بناء المذكرة..."):
                    new_c = agent.regenerate_arcee_only(
                        prompt, subject=subject, level=level, grade=grade)
                render_live_preview(new_c, "مذكرة (Arcee)", "Arcee AI — نسخة بديلة")
            else:
                st.warning("⚠️ كلا المفتاحين مطلوبان للتوليد البديل")

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 19 — TAB: EXERCISE GENERATOR                  ║
# ╚═══════════════════════════════════════════════════════════╝

def tab_exercise_generator(groq_key: str, arcee_key: str, model: str):
    st.markdown("### ✏️ توليد التمارين والأنشطة")
    level, grade, branch, subject, _ = curriculum_selectors("exo")
    lesson     = st.text_input("📖 الدرس / المحور", key="exo_lesson",
                                placeholder="مثال: المعادلات التفاضلية")
    ex_type    = st.selectbox("📌 نوع التمرين",
                               ["تمارين تطبيقية","أسئلة متعددة الاختيار (MCQ)",
                                "وضعية إدماجية","أسئلة مفتوحة","مسألة حل مشكلات"],
                               key="exo_type")
    difficulty = st.selectbox("⚡ الصعوبة",
                               ["سهل","متوسط","صعب","مختلط"], key="exo_diff")
    num_ex     = st.slider("عدد التمارين", 1, 8, 3, key="exo_num")

    if st.button("🚀 توليد التمارين", key="gen_exo_btn"):
        if not groq_key:
            st.markdown('<div class="error-box">⚠️ أدخل مفتاح Groq</div>',
                        unsafe_allow_html=True)
            return
        lang_clause = llm_output_language_clause(subject)
        prompt = (
            f"أنت أستاذ متخصص في مادة {subject} للمنظومة التربوية الجزائرية.\n"
            f"أنشئ {num_ex} تمرين/نشاط من نوع '{ex_type}' حول موضوع '{lesson}'\n"
            f"للمستوى {grade} ({level}) — مستوى الصعوبة: {difficulty}\n"
            f"شروط الجودة:\n"
            f"- انتبه إلى التوافق مع المنهاج الجزائري الرسمي\n"
            f"- أضف الحل النموذجي والتصحيح المفصّل بعد كل تمرين\n"
            f"- راعِ مستويات التفكير (تذكر → فهم → تطبيق → تحليل → تركيب)\n"
            f"- اذكر عدد النقاط لكل سؤال\n"
            f"{lang_clause}"
        )
        agent  = get_hybrid_engine(groq_key, arcee_key, model)
        with st.spinner("⚙️ توليد التمارين..."):
            result = agent.generate(prompt, subject=subject, level=level, grade=grade)
        content      = result["final"]
        sources_used = result["sources_used"]
        st.session_state["last_exo_content"] = content
        st.session_state["last_exo_prompt"]  = prompt
        db_exec("INSERT INTO exercises (level,grade,branch,subject,lesson,ex_type,difficulty,content,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (level, grade, branch or "", subject, lesson, ex_type, difficulty,
                 content, datetime.now().isoformat()))

        render_live_preview(content, f"تمارين: {lesson}", sources_used)

        rtl, _ = get_pdf_mode_for_subject(subject)
        pdf_b  = generate_simple_pdf(content, f"تمارين في {subject}",
                                      subtitle=f"{lesson} | {grade}", rtl=rtl)
        st.download_button("📄 تنزيل PDF", pdf_b,
                           file_name=f"exercices_{subject}_{lesson[:20]}.pdf",
                           mime="application/pdf", key="dl_exo_pdf")

    if st.session_state.get("last_exo_content"):
        st.markdown("---")
        if st.button("🔄 إعادة التوليد بنموذج بديل", key="regen_exo"):
            if arcee_key:
                agent  = get_hybrid_engine(groq_key, arcee_key, model)
                with st.spinner("⚙️ Arcee يعيد التوليد..."):
                    new_c = agent.regenerate_arcee_only(
                        st.session_state.get("last_exo_prompt",""),
                        subject=subject, level=level, grade=grade)
                render_live_preview(new_c, "تمارين (Arcee)", "Arcee AI — نسخة بديلة")

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 20 — TAB: GRADE BOOK & ANALYSIS               ║
# ╚═══════════════════════════════════════════════════════════╝

def tab_grade_book(groq_key: str, arcee_key: str, model: str):
    st.markdown("### 📊 دفتر التنقيط والتحليل البيداغوجي")
    level, grade, branch, subject, _ = curriculum_selectors("gb")
    semester = st.selectbox("📅 الفصل",
                             ["الفصل الأول","الفصل الثاني","الفصل الثالث"], key="gb_sem")

    st.markdown("#### إدخال البيانات")
    input_method = st.radio("طريقة الإدخال",
                             ["يدوي (أقسام متعددة)","رفع ملف Excel"],
                             horizontal=True, key="gb_method")

    classes_data = []

    if input_method == "رفع ملف Excel":
        uploaded = st.file_uploader("📁 رفع ملف دفتر التنقيط (.xlsx)",
                                     type=["xlsx","xls"], key="gb_upload")
        if uploaded:
            classes_data = parse_grade_book_excel(uploaded)
            if classes_data:
                st.success(f"✅ تم تحميل {len(classes_data)} قسم(أقسام)")
            else:
                st.warning("⚠️ لم يُعثر على بيانات — تحقق من تنسيق الملف")
    else:
        num_classes = st.number_input("عدد الأقسام", 1, 10, 1, key="gb_ncls")
        for ci in range(int(num_classes)):
            with st.expander(f"📋 إدخال بيانات القسم {ci+1}", expanded=(ci==0)):
                class_name = st.text_input(f"اسم القسم {ci+1}",
                                            value=f"القسم {ci+1}", key=f"cls_name_{ci}")
                st.markdown("_أدخل درجات التلاميذ (تقويم/فرض/اختبار — كل واحد من 20):_")
                num_stu = st.number_input(f"عدد تلاميذ القسم {ci+1}",
                                           5, 50, 30, key=f"cls_nstu_{ci}")
                raw_input = st.text_area(
                    f"بيانات القسم {ci+1} (اسم,تقويم,فرض,اختبار — سطر لكل تلميذ)",
                    height=150, key=f"cls_data_{ci}",
                    placeholder="أحمد بلعيد,14,13,15\nفاطمة زهرة,16,15,17\n..."
                )
                students = []
                if raw_input.strip():
                    for line in raw_input.strip().splitlines():
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 4:
                            try:
                                name = parts[0]
                                t = float(parts[1]); f = float(parts[2])
                                ikh = float(parts[3])
                                avg = calc_average(t, f, ikh)
                                students.append({
                                    "name": name, "taqwim": t,
                                    "fard": f, "ikhtibhar": ikh,
                                    "avg": avg,
                                    "appreciation": get_appreciation(avg),
                                })
                            except ValueError:
                                pass
                if students:
                    avgs = [s["avg"] for s in students]
                    classes_data.append({
                        "name": class_name, "students": students,
                        "total": len(students),
                        "avg":   round(sum(avgs)/len(avgs), 2) if avgs else 0,
                        "max":   max(avgs) if avgs else 0,
                        "min":   min(avgs) if avgs else 0,
                        "pass_rate": round(sum(1 for a in avgs if a>=10)/len(avgs)*100,1) if avgs else 0,
                        "top5":  sorted(students, key=lambda x: x["avg"], reverse=True)[:5],
                        "distribution": {
                            "0-5":   sum(1 for a in avgs if a < 5),
                            "5-10":  sum(1 for a in avgs if 5 <= a < 10),
                            "10-15": sum(1 for a in avgs if 10 <= a < 15),
                            "15-20": sum(1 for a in avgs if a >= 15),
                        }
                    })

    if classes_data and st.button("📈 تحليل النتائج وإنشاء التقرير", key="analyze_gb_btn"):
        # Charts
        for cls in classes_data:
            st.markdown(f"#### 📊 القسم: {cls['name']}")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="stat-card"><h2>{cls["total"]}</h2><p>تلميذ</p></div>',
                            unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-card"><h2>{safe_f(cls["avg"])}</h2><p>المعدل</p></div>',
                            unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-card"><h2>{safe_f(cls.get("pass_rate",0),".0f")}%</h2><p>النجاح</p></div>',
                            unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="stat-card"><h2>{safe_f(cls["max"])}</h2><p>أعلى</p></div>',
                            unsafe_allow_html=True)
            # Distribution chart
            if cls.get("distribution"):
                dist = cls["distribution"]
                fig  = px.bar(
                    x=list(dist.keys()), y=list(dist.values()),
                    labels={"x":"الفئة","y":"عدد التلاميذ"},
                    title=f"توزيع درجات {cls['name']}",
                    color=list(dist.keys()),
                    color_discrete_map={"0-5":"#e74c3c","5-10":"#e67e22",
                                        "10-15":"#3498db","15-20":"#27ae60"},
                )
                fig.update_layout(showlegend=False, height=280)
                st.plotly_chart(fig, use_container_width=True)

        # Excel export (multi-sheet)
        xl_b = generate_grade_book_excel(classes_data, subject, semester)
        st.download_button("📊 تنزيل دفتر التنقيط (Excel متعدد الأوراق)", xl_b,
                           file_name=f"carnet_notes_{subject}_{semester}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_gb_excel_main")

        # Auto-display pedagogical report
        if groq_key:
            agent = get_hybrid_engine(groq_key, arcee_key, model)
            render_auto_pedagogical_report(classes_data, subject, semester, agent)
        else:
            st.warning("⚠️ أدخل مفتاح Groq لتوليد التقرير البيداغوجي")

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 21 — TAB: CORRECTION & FEEDBACK               ║
# ╚═══════════════════════════════════════════════════════════╝

def tab_correction(groq_key: str, arcee_key: str, model: str):
    st.markdown("### ✅ تصحيح الأوراق والتغذية الراجعة")
    level, grade, branch, subject, _ = curriculum_selectors("corr")
    student_name = st.text_input("👤 اسم التلميذ", key="corr_name",
                                  placeholder="اختياري")
    total_marks  = st.number_input("العلامة الكلية", 10, 100, 20, key="corr_total")
    student_answer = st.text_area("📝 إجابة التلميذ",  height=200, key="corr_ans",
                                   placeholder="الصق نص إجابة التلميذ هنا...")
    model_answer   = st.text_area("📌 النموذج / التوقعات (اختياري)", height=150,
                                   key="corr_model",
                                   placeholder="التصحيح النموذجي أو معايير التقييم...")

    # Image upload for OCR
    img_file = st.file_uploader("🖼️ رفع صورة ورقة الإجابة (اختياري)",
                                 type=["png","jpg","jpeg"], key="corr_img")
    if img_file:
        img_bytes = img_file.read()
        st.image(img_bytes, caption="معاينة الورقة", use_column_width=True)
        if _TESSERACT_AVAILABLE:
            ocr_text = ocr_answer_sheet_image(img_bytes)
            if ocr_text:
                st.text_area("📖 نص OCR المستخرج", value=ocr_text, height=100,
                              key="ocr_result")

    if st.button("🔍 تصحيح ذكي بالذكاء الهجين", key="corr_btn"):
        if not groq_key:
            st.markdown('<div class="error-box">⚠️ أدخل مفتاح Groq</div>',
                        unsafe_allow_html=True)
            return
        if not student_answer.strip():
            st.markdown('<div class="warn-box">⚠️ أدخل إجابة التلميذ</div>',
                        unsafe_allow_html=True)
            return
        lang_clause = llm_output_language_clause(subject)
        model_part = f"\nالتصحيح النموذجي:\n{model_answer}" if model_answer.strip() else ""
        prompt = (
            f"أنت أستاذ متخصص في مادة {subject} للمستوى {grade} ({level}).\n"
            f"قيّم إجابة التلميذ{f' {student_name}' if student_name else ''} "
            f"على {total_marks} نقطة.\n\n"
            f"إجابة التلميذ:\n{student_answer}\n"
            f"{model_part}\n\n"
            f"المطلوب:\n"
            f"1. التقييم المفصّل مع العلامة من {total_marks} مع التبرير\n"
            f"2. نقاط القوة في الإجابة\n"
            f"3. الأخطاء والثغرات مع التوضيح\n"
            f"4. التغذية الراجعة البنّاءة للتحسين\n"
            f"5. التوصيات للمعلم لمعالجة هذه الثغرات\n"
            f"{lang_clause}"
        )
        agent  = get_hybrid_engine(groq_key, arcee_key, model)
        with st.spinner("⚙️ جاري التصحيح الذكي..."):
            result = agent.generate(prompt, subject=subject, level=level, grade=grade)
        feedback     = result["final"]
        sources_used = result["sources_used"]

        # Extract grade from response
        grade_val = 0.0
        m = re.search(r'(\d+(?:\.\d+)?)\s*/\s*' + str(int(total_marks)), feedback)
        if m:
            try:
                grade_val = float(m.group(1))
            except ValueError:
                pass

        db_exec("INSERT INTO corrections (student_name,subject,grade_value,total,feedback,created_at) VALUES (?,?,?,?,?,?)",
                (student_name or "مجهول", subject, grade_val, total_marks,
                 feedback, datetime.now().isoformat()))

        render_live_preview(feedback, f"تصحيح {student_name or 'التلميذ'}", sources_used)

        rtl, _ = get_pdf_mode_for_subject(subject)
        pdf_b  = generate_simple_pdf(feedback, f"تصحيح: {student_name or 'التلميذ'}",
                                      subtitle=f"{subject} | {grade}", rtl=rtl)
        st.download_button("📄 تنزيل تقرير التصحيح", pdf_b,
                           file_name=f"correction_{student_name or 'eleve'}.pdf",
                           mime="application/pdf", key="dl_corr_pdf")

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 22 — TAB: HISTORY & DATABASE                  ║
# ╚═══════════════════════════════════════════════════════════╝

def tab_history():
    st.markdown("### 🗂️ سجل العمل والأرشيف")
    tab_h1, tab_h2, tab_h3 = st.tabs(["📝 الاختبارات","📚 المذكرات","✅ التصحيحات"])
    with tab_h1:
        rows = db_exec("SELECT id,level,grade,subject,semester,created_at FROM exams ORDER BY id DESC LIMIT 20", fetch=True) or []
        if not rows:
            st.info("لا توجد اختبارات محفوظة بعد.")
        for r in rows:
            r = r[:6]
            st.markdown(
                f'<div class="db-item">🆔 {r[0]} | '
                f'📚 {r[1]} | 🎓 {r[2]} | 📖 {r[3]} | '
                f'📅 {r[4]} | 🕐 {r[5][:16] if r[5] else ""}</div>',
                unsafe_allow_html=True)
    with tab_h2:
        rows = db_exec("SELECT id,level,grade,subject,lesson,created_at FROM lesson_plans ORDER BY id DESC LIMIT 20", fetch=True) or []
        if not rows:
            st.info("لا توجد مذكرات محفوظة بعد.")
        for r in rows:
            r = r[:6]
            st.markdown(
                f'<div class="db-item">🆔 {r[0]} | 📚 {r[1]} | 🎓 {r[2]} | '
                f'📖 {r[3]} | درس: {r[4]} | 🕐 {r[5][:16] if r[5] else ""}</div>',
                unsafe_allow_html=True)
    with tab_h3:
        rows = db_exec("SELECT id,student_name,subject,grade_value,total,created_at FROM corrections ORDER BY id DESC LIMIT 20", fetch=True) or []
        if not rows:
            st.info("لا توجد تصحيحات محفوظة بعد.")
        for r in rows:
            r = r[:6]
            pct = float(r[3] or 0) / float(r[4] or 20) * 100
            color = "#1e8449" if pct >= 50 else "#c0392b"
            st.markdown(
                f'<div class="db-item">🆔 {r[0]} | 👤 {r[1]} | '
                f'📖 {r[2]} | <span style="color:{color};font-weight:700">'
                f'{safe_f(r[3])}/{r[4]}</span> | 🕐 {r[5][:16] if r[5] else ""}</div>',
                unsafe_allow_html=True)

# ╔═══════════════════════════════════════════════════════════╗
# ║     SECTION 23 — MAIN APP ENTRYPOINT                      ║
# ╚═══════════════════════════════════════════════════════════╝

def main():
    # Sidebar
    groq_key, arcee_key, sel_model = render_sidebar()

    # Hero header
    render_robot_hero()
    st.markdown("""
    <div class="title-card">
      <h1>🎓 DONIA MIND 1 — المعلم الذكي</h1>
      <p>المعلم الذكي للمنظومة التربوية الجزائرية — مختبر DONIA LABS TECH</p>
      <p style="font-size:.85rem;opacity:.8">
        ⚡ Groq (سرعة) × 🎯 Arcee (دقة تربوية) × ✅ التحقق البيداغوجي الجزائري
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Welcome banner
    st.markdown(f'<div class="welcome-banner">💬 {WELCOME_MESSAGE_AR}</div>',
                unsafe_allow_html=True)

    # Engine status
    if groq_key:
        arcee_status = "✅ تحقق مزدوج (Groq + Arcee)" if arcee_key else "⚡ Groq فقط"
        st.markdown(f"""
        <div class="crosscheck-badge">
          <span class="crosscheck-icon">🤖</span>
          محرك الذكاء النشط: {arcee_status}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Main tabs
    tabs = st.tabs([
        "📝 توليد الاختبارات",
        "📚 مذكرة الدرس",
        "✏️ التمارين",
        "📊 دفتر التنقيط",
        "✅ التصحيح",
        "🗂️ السجل",
    ])

    with tabs[0]:
        tab_exam_generator(groq_key, arcee_key, sel_model)
    with tabs[1]:
        tab_lesson_plan(groq_key, arcee_key, sel_model)
    with tabs[2]:
        tab_exercise_generator(groq_key, arcee_key, sel_model)
    with tabs[3]:
        tab_grade_book(groq_key, arcee_key, sel_model)
    with tabs[4]:
        tab_correction(groq_key, arcee_key, sel_model)
    with tabs[5]:
        tab_history()

    # Footer
    st.markdown(f"""
    <div class="donia-ip-footer">
      <div>{COPYRIGHT_FOOTER_AR}</div>
      <div style="font-size:.78rem;color:#888;margin:.3rem 0">
        DONIA MIND v3.0 — Global Excellence Upgrade |
        Dual-Core: Groq × Arcee |
        محرك التحقق البيداغوجي الجزائري
      </div>
      <div class="donia-footer-social">
        <a href="{SOCIAL_URL_WHATSAPP}" target="_blank">📱 واتساب</a>
        <a href="{SOCIAL_URL_TELEGRAM}" target="_blank">✈️ تيليغرام</a>
        <a href="{SOCIAL_URL_FACEBOOK}" target="_blank">👥 فيسبوك</a>
        <a href="{SOCIAL_URL_LINKEDIN}" target="_blank">💼 لينكدإن</a>
        <a href="{APP_URL}" target="_blank">🌐 التطبيق</a>
      </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
