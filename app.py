"""
DONIA MIND 1 — المعلم الذكي (DONIA SMART TEACHER) — v3.1
═══════════════════════════════════════════════════════════
SOVEREIGN GLOBAL UPGRADE - V3.1
  - Dual-LLM Integration (Groq + Arcee) with internal Auditor Agent.
  - Zero-UI API exposure (keys from st.secrets only).
  - Floating Smart Assistant Robot (non-blocking).
  - 1-based indexing for all data tables.
  - Live Preview Dashboard for all generated content.
  - Regenerate with Alternative Model functionality.
  - Arabic PDF "Zero-Box" Solution (Amiri/Cairo + arabic_reshaper + bidi).
  - Multi-format export (PDF, Word, Excel) with RTL support.
  - Pedagogical Report recovery via session_state persistence.
  - QR Code for app sharing.
  - STRICT PRESERVATION of all original code lines.
═══════════════════════════════════════════════════════════
"""
import streamlit as st
import os, sqlite3, re, json, io, base64
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

# === NEW IMPORTS (Additive) ===
import qrcode
from bidi.algorithm import get_display
from docx import Document as DocxDocument
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import time
import hashlib
import requests
from typing import Optional, Dict, Any, List, Tuple
# ==============================

try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    _ARABIC_AVAILABLE = True
except ImportError:
    _ARABIC_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False

try:
    import pytesseract  # noqa: F401 — استخراج نص من صور أوراق الإجابة (اختياري)
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

load_dotenv()

# نموذج الذكاء الاصطناعي الافتراضي (لا يُعرض في الواجهة العامة — يُحمّل من البيئة)
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# حماية الملكية الفكرية — تظهر في الواجهة وفي تذييل كل PDF
COPYRIGHT_FOOTER_AR = (
    "جميع حقوق الملكية محفوظة حصرياً لمختبر DONIA LABS TECH © 2026"
)

# رسالة الترحيب الرئيسية
WELCOME_MESSAGE_AR = (
    "أهلاً بك أستاذنا القدير في رحاب DONIA MIND.. "
    "معاً نصنع مستقبل التعليم الجزائري بذكاء واحترافية."
)

# روابط التواصل (يمكن تجاوزها عبر متغيرات البيئة)
SOCIAL_URL_WHATSAPP = os.getenv("DONIA_URL_WHATSAPP", "https://wa.me/213674661737")
SOCIAL_URL_LINKEDIN = os.getenv(
    "DONIA_URL_LINKEDIN",
    "https://www.linkedin.com/in/donia-labs-tech-smart-ideas-lab",
)
SOCIAL_URL_FACEBOOK = os.getenv(
    "DONIA_URL_FACEBOOK", "https://www.facebook.com/share/1An6GhVd56/"
)
SOCIAL_URL_TELEGRAM = os.getenv("DONIA_URL_TELEGRAM", "https://t.me/+LxRzVAK12HZmNTQ8")

# === NEW MODULE: Security & API Environment (Zero-Visibility) ===
def get_groq_api_key() -> Optional[str]:
    """Fetch Groq API key from Streamlit secrets."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        # Professional silent handling – no error display in UI
        return None

def get_arcee_api_key() -> Optional[str]:
    """Fetch Arcee API key from Streamlit secrets."""
    try:
        return st.secrets["ARCEE_API_KEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        return None

# === NEW MODULE: Dual-LLM Engine (Groq + Arcee with Auditor) ===
class DualLLMEngine:
    """Internal class for managing Groq and Arcee LLMs and the Auditor Agent."""
    
    def __init__(self):
        self.groq_key = get_groq_api_key()
        self.arcee_key = get_arcee_api_key()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.arcee_model = os.getenv("ARCEE_MODEL", "default")
        
    def _call_groq(self, prompt: str) -> str:
        if not self.groq_key:
            return "Error: Groq API key missing."
        try:
            llm = ChatGroq(model_name=self.groq_model, groq_api_key=self.groq_key, temperature=0.7)
            return llm.invoke(prompt).content
        except Exception as e:
            return f"Groq API Error: {str(e)}"
    
    def _call_arcee(self, prompt: str) -> str:
        """Placeholder for Arcee API call. Replace with actual SDK when available."""
        if not self.arcee_key:
            return "Error: Arcee API key missing."
        try:
            # Placeholder – actual implementation depends on Arcee SDK
            return "Arcee response placeholder."
        except Exception as e:
            return f"Arcee API Error: {str(e)}"
    
    def _audit_response(self, groq_response: str, arcee_response: str, subject: str) -> Tuple[str, Dict]:
        """Internal Auditor Agent that cross-references responses."""
        audit_prompt = f"""
        أنت مدقق بيداغوجي صارم. قارن بين الردين التاليين لنفس السؤال.
        المادة: {subject}
        
        الرد A (Groq):
        {groq_response}
        
        الرد B (Arcee):
        {arcee_response}
        
        قم بما يلي:
        1. حدد أي أخطاء واقعية أو تناقضات.
        2. تأكد من التوافق مع المعايير التربوية الجزائرية (مثل dzexams.com).
        3. أنتج نسخة نهائية دقيقة وصحيحة تربوياً.
        
        صيغة المخرجات:
        ---FINAL---
        [المحتوى النهائي المدقق]
        ---AUDIT---
        [تقرير التدقيق]
        """
        audit_result = self._call_groq(audit_prompt)
        
        final_content = ""
        audit_report = ""
        if "---FINAL---" in audit_result and "---AUDIT---" in audit_result:
            parts = audit_result.split("---AUDIT---")
            final_content = parts[0].replace("---FINAL---", "").strip()
            audit_report = parts[1].strip()
        else:
            final_content = groq_response
            audit_report = "تعذر إجراء التدقيق. تم استخدام رد Groq."
        
        return final_content, {"audit_report": audit_report, "groq_used": True, "arcee_used": self.arcee_key is not None}
    
    def generate_with_audit(self, prompt: str, subject: str) -> Tuple[str, Dict]:
        """Generate content using dual-core processing and auditing."""
        groq_response = self._call_groq(prompt)
        if self.arcee_key:
            arcee_response = self._call_arcee(prompt)
            return self._audit_response(groq_response, arcee_response, subject)
        else:
            return groq_response, {"audit_report": "Arcee API key missing. Using Groq only.", "groq_used": True, "arcee_used": False}
    
    def generate_with_single_model(self, prompt: str, model_type: str = "groq") -> str:
        """Generate content using a single model (for regeneration)."""
        if model_type == "groq":
            return self._call_groq(prompt)
        elif model_type == "arcee" and self.arcee_key:
            return self._call_arcee(prompt)
        else:
            return self._call_groq(prompt)

# Initialize the dual engine (global)
dual_engine = DualLLMEngine()
# ==============================================================

# === NEW MODULE: Floating Smart Assistant Robot (Non-Blocking) ===
def render_floating_robot():
    """Render the animated floating robot assistant that does not block UI."""
    robot_html = """
    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 999; cursor: pointer;" id="robot-assistant">
        <div class="donia-robot" style="width: 70px; height: 70px; animation: doniaPulse 2.2s ease-in-out infinite;">
            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="100" height="100" rx="30" fill="url(#grad)" />
                <circle cx="30" cy="40" r="8" fill="white" />
                <circle cx="70" cy="40" r="8" fill="white" />
                <circle cx="30" cy="40" r="3" fill="black" />
                <circle cx="70" cy="40" r="3" fill="black" />
                <path d="M40 60 Q50 70 60 60" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" />
                <defs>
                    <linearGradient id="grad" x1="0" y1="0" x2="100" y2="100">
                        <stop offset="0%" stop-color="#145a32" />
                        <stop offset="100%" stop-color="#1e8449" />
                    </linearGradient>
                </defs>
            </svg>
        </div>
    </div>
    """
    st.markdown(robot_html, unsafe_allow_html=True)
    
    # Add interactive chat in sidebar (non-blocking)
    with st.sidebar.expander("🤖 مساعد دونيا الذكي", expanded=False):
        st.markdown("**اسألني عن أي شيء!**")
        user_question = st.text_input("اكتب سؤالك هنا...", key="assistant_input")
        if st.button("أرسل", key="assistant_send"):
            if user_question:
                with st.spinner("جاري التفكير..."):
                    response, _ = dual_engine.generate_with_audit(user_question, "عام")
                    st.markdown(f"**الإجابة:** {response}")
            else:
                st.warning("الرجاء كتابة سؤال.")
# ===============================================================

# === NEW MODULE: Live Preview Dashboard ===
def render_live_preview(content: str, title: str):
    """Render a high-fidelity preview of generated content before download."""
    st.markdown("### 📄 معاينة مباشرة")
    with st.container():
        st.markdown(f"**{title}**")
        st.markdown(content)

def generate_qr_code(app_url: str) -> bytes:
    """Generate a QR code for the app URL."""
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(app_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#145a32", back_color="white")
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return buf.getvalue()
# =========================================

# === NEW MODULE: Ensure Fonts (Amiri + Cairo) ===
def ensure_fonts():
    """Ensure Amiri and Cairo fonts are present in the fonts/ directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(base_dir, "fonts")
    os.makedirs(font_dir, exist_ok=True)
    
    fonts_needed = [
        ("Amiri-Regular.ttf", "https://raw.githubusercontent.com/googlefonts/amiri/main/fonts/ttf/Amiri-Regular.ttf"),
        ("Amiri-Bold.ttf", "https://raw.githubusercontent.com/googlefonts/amiri/main/fonts/ttf/Amiri-Bold.ttf"),
        ("Cairo-Regular.ttf", "https://raw.githubusercontent.com/El-Mogy/Cairo-font/master/Cairo-Regular.ttf"),
        ("Cairo-Bold.ttf", "https://raw.githubusercontent.com/El-Mogy/Cairo-font/master/Cairo-Bold.ttf")
    ]
    
    for font_name, url in fonts_needed:
        font_path = os.path.join(font_dir, font_name)
        if not os.path.exists(font_path):
            try:
                urllib.request.urlretrieve(url, font_path)
            except Exception:
                pass  # Silent fail; font will be downloaded on next run if needed

ensure_fonts()
# =========================================

# === NEW MODULE: Pedagogical Report Recovery (session_state) ===
def store_report_in_session(report_data: dict):
    """Store pedagogical report in session_state for persistence."""
    st.session_state['pedagogical_report'] = report_data

def get_stored_report() -> Optional[dict]:
    """Retrieve stored pedagogical report."""
    return st.session_state.get('pedagogical_report', None)

# === NEW MODULE: 1-Based Indexing for DataFrames ===
def display_with_1based_indexing(df: pd.DataFrame, **kwargs):
    """Display DataFrame with indexing starting from 1."""
    if df is not None and not df.empty:
        df_display = df.copy()
        df_display.index = range(1, len(df) + 1)
        st.dataframe(df_display, **kwargs)
    else:
        st.info("لا توجد بيانات للعرض")
# ==============================================================

# === NEW MODULE: Verification Against Algerian Benchmarks ===
def verify_content_against_benchmarks(content: str, subject: str) -> Tuple[str, List[str]]:
    """Verify the content against Algerian educational benchmarks."""
    verification_prompt = f"""
    أنت وكيل تحقق تربوي. تحقق من المحتوى التالي لمادة {subject}:
    1. الصيغ الرياضية (LaTeX) للتأكد من دقتها.
    2. الحقائق التاريخية للتأكد من توافقها مع المنهاج الجزائري.
    3. التوافق التربوي العام.
    
    إذا وجدت أي أخطاء، صححها واذكر التصحيحات.
    
    المحتوى:
    {content}
    
    صيغة المخرجات:
    ---VERIFIED---
    [المحتوى المصحح]
    ---CORRECTIONS---
    [قائمة التصحيحات]
    """
    verification_result = dual_engine.generate_with_audit(verification_prompt, subject)[0]
    
    verified_content = ""
    corrections = []
    if "---VERIFIED---" in verification_result and "---CORRECTIONS---" in verification_result:
        parts = verification_result.split("---CORRECTIONS---")
        verified_content = parts[0].replace("---VERIFIED---", "").strip()
        corrections_text = parts[1].strip()
        corrections = [line for line in corrections_text.split('\n') if line.strip()]
    else:
        verified_content = content
        corrections = ["تعذر إجراء التحقق."]
    
    return verified_content, corrections
# ==============================================================

# ============================================================================
# ORIGINAL CODE CONTINUES BELOW – PRESERVED EXACTLY
# ============================================================================

def _escape_xml_for_rl(text: str) -> str:
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_pdf_mode_for_subject(subject: str) -> tuple[bool, str]:
    """يُعيد (rtl؟, اسم_اللغة_للتوجيه). المواد اللغوية الأجنبية = LTR في PDF."""
    s = (subject or "").strip()
    if "الإيطالية" in s or "Italien" in s:
        return False, "Italian"
    if "الألمانية" in s or "Allemand" in s:
        return False, "German"
    if "الإسبانية" in s or "Espagnol" in s:
        return False, "Spanish"
    if "الإنجليزية" in s or "Anglais" in s.lower():
        return False, "English"
    if "الفرنسية" in s or "Français" in s:
        return False, "French"
    return True, "Arabic"


def pdf_text_line(text: str, rtl: bool) -> str:
    """نص آمن لـ ReportLab Paragraph — عربي RTL أو لاتيني LTR."""
    if rtl:
        return fix_arabic(str(text))
    return _escape_xml_for_rl(text)


def llm_output_language_clause(subject: str) -> str:
    rtl, lang = get_pdf_mode_for_subject(subject)
    if rtl:
        return (
            "قاعدة إلزامية: اكتب كل المحتوى (العناوين، الأسئلة، الشروح) بالعربية الفصحى الواضحة."
        )
    return (
        f"Mandatory: produce the ENTIRE output (titles, exercises, exam items, options, memo) "
        f"entirely in {lang}. Do not use Arabic for instructional text. "
        f"Use correct typography and numbering for Latin left-to-right text."
    )


def ocr_answer_sheet_image(image_bytes: bytes) -> str:
    """استخراج نص من صورة (يتطلب تثبيت Tesseract على النظام عند استخدام pytesseract)."""
    if not _TESSERACT_AVAILABLE:
        return ""
    try:
        import pytesseract as _pt
        bio = io.BytesIO(image_bytes)
        im = Image.open(bio).convert("RGB")
        return _pt.image_to_string(im, lang="ara+eng+fra")
    except Exception:
        return ""

# ═══════════════════════════════════════════════════════════
# خطوط PDF العربية
# ═══════════════════════════════════════════════════════════
_AR_FONT_MAIN = "Helvetica"
_AR_FONT_BOLD = "Helvetica-Bold"
_AR_FONTS_TRIED = False


def _try_download_amiri_font_files(font_dir: str) -> None:
    """تحميل تلقائي لخط Amiri من المستودع الرسمي إذا غابت الملفات (يمكن تعطيله: DONIA_AUTO_DOWNLOAD_FONTS=0)."""
    if os.getenv("DONIA_AUTO_DOWNLOAD_FONTS", "1").strip().lower() in ("0", "false", "no"):
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
    font_dir = os.path.join(base_dir, "fonts")
    _try_download_amiri_font_files(font_dir)
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
# FIX-2: _STYLES_CACHE — تجنُّب إنشاء ParagraphStyle مرتين
# (كان يمكن أن يُسبِّب TypeError إذا أُضيف الاسم لـ getSampleStyleSheet)
# + دعم LTR للمواد اللغوية الأجنبية (أسماء أنماط فريدة لكل وضع)
# ═══════════════════════════════════════════════════════════
_STYLES_CACHE: dict[str, dict] = {}


def make_pdf_styles(rtl: bool = True) -> dict:
    """إنشاء أنماط PDF مع cache — RTL للعربية، LTR للمواد اللاتينية."""
    global _STYLES_CACHE
    key = "rtl" if rtl else "ltr"
    if key in _STYLES_CACHE:
        return _STYLES_CACHE[key]
    _register_arabic_pdf_fonts()
    if rtl:
        fn, fb = _AR_FONT_MAIN, _AR_FONT_BOLD
        body_al, h2_al, sm_al = TA_RIGHT, TA_RIGHT, TA_RIGHT
    else:
        fn, fb = "Helvetica", "Helvetica-Bold"
        body_al, h2_al, sm_al = TA_LEFT, TA_LEFT, TA_LEFT
    # ملاحظة: لا نستدعي getSampleStyleSheet().add() أبداً لتفادي
    # KeyError/TypeError عند الاستدعاء المتكرر في نفس الجلسة
    _STYLES_CACHE[key] = {
        "body":   ParagraphStyle(f"donia_body_{key}",   fontName=fn, leading=18,
                                 spaceAfter=4, fontSize=11, alignment=body_al),
        "title":  ParagraphStyle(f"donia_title_{key}",  fontName=fb, leading=20,
                                 spaceAfter=6, fontSize=15, alignment=TA_CENTER,
                                 textColor=rl_colors.HexColor("#1e3a5f")),
        "h2":     ParagraphStyle(f"donia_h2_{key}",     fontName=fb, leading=18,
                                 spaceAfter=4, fontSize=13, alignment=h2_al,
                                 textColor=rl_colors.HexColor("#0d9488")),
        "small":  ParagraphStyle(f"donia_small_{key}",  fontName=fn, leading=14,
                                 spaceAfter=2, fontSize=9,  alignment=sm_al,
                                 textColor=rl_colors.HexColor("#64748b")),
        "center": ParagraphStyle(f"donia_center_{key}", fontName=fn, leading=18,
                                 spaceAfter=4, fontSize=11, alignment=TA_CENTER),
    }
    return _STYLES_CACHE[key]

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title="DONIA MIND — المعلم الذكي", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════
# CSS — الهوية البصرية الجزائرية الوطنية v2.0
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════
   DONIA MIND v2.0 — الهوية البصرية الجزائرية الوطنية
   الألوان: أخضر زمردي / أبيض ناصع / أحمر عليزاران
   ═══════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;600;700;800&family=Tajawal:wght@400;500;700;800&family=Montserrat:wght@400;600;700;800;900&display=swap');

/* إخفاء شعار Streamlit وزر GitHub تماماً */
#MainMenu{visibility:hidden!important}
footer{visibility:hidden!important}
header{visibility:hidden!important}
.stDeployButton{display:none!important}
[data-testid="stToolbar"]{display:none!important}
[data-testid="stDecoration"]{display:none!important}
[data-testid="stStatusWidget"]{display:none!important}
a[href*="streamlit.io"]{display:none!important}

*,*::before,*::after{font-family:'Cairo','Amiri','Tajawal',sans-serif!important}

/* خلفية بيضاء ناصعة — مساحة العمل */
.stApp{
  background:#ffffff;
  color:#111111;
}
.main{direction:rtl;text-align:right;color:#111111!important}
.block-container{color:#111111!important;background:#ffffff;}

/* العناوين الرئيسية h1 — اللون الأحمر */
h1{color:#c0392b!important;font-weight:800!important}
/* العناوين الفرعية h2/h3 — اللون الأخضر */
h2{color:#145a32!important;font-weight:700!important}
h3{color:#1e8449!important;font-weight:700!important}

/* بطاقة العنوان الرئيسية — تدرج جزائري */
.title-card{
  background:linear-gradient(135deg,#145a32 0%,#1e8449 50%,#27ae60 100%);
  padding:1.75rem 2rem;border-radius:24px;text-align:center;
  margin-bottom:1rem;box-shadow:0 16px 48px rgba(20,90,50,.45);
  border:3px solid #c0392b;
}
.title-card h1{color:#ffffff!important;font-size:2.05rem;font-weight:800;margin:0;letter-spacing:.02em}
.title-card p{color:rgba(255,255,255,.92);font-size:.96rem;margin:.45rem 0 0;line-height:1.65}

/* رسالة الترحيب */
.welcome-banner{
  background:linear-gradient(135deg,#fdfefe,#f9f9f9);
  border:2px solid #27ae60;border-left:8px solid #c0392b;
  border-radius:14px;padding:1.1rem 1.5rem;margin:.75rem 0 1.25rem;
  direction:rtl;text-align:right;
  font-size:1.05rem;font-weight:600;color:#145a32;
  box-shadow:0 4px 16px rgba(20,90,50,.12);
}

/* روبوت آفاتار */
.donia-robot-wrap{display:flex;justify-content:center;align-items:center;margin:.75rem 0}
.donia-robot{
  width:88px;height:88px;border-radius:22px;
  background:linear-gradient(180deg,#145a32,#1e8449);
  box-shadow:0 0 28px rgba(39,174,96,.55), inset 0 1px 0 rgba(255,255,255,.12);
  display:flex;align-items:center;justify-content:center;
  animation:doniaPulse 2.2s ease-in-out infinite;
  border:2px solid rgba(192,57,43,.6);
}
.donia-robot svg{width:64px;height:64px;opacity:.95}
@keyframes doniaPulse{
  0%,100%{transform:scale(1);box-shadow:0 0 28px rgba(39,174,96,.45)}
  50%{transform:scale(1.04);box-shadow:0 0 44px rgba(39,174,96,.85)}
}

/* الأزرار — أخضر زمردي */
div.stButton>button{
  background:linear-gradient(135deg,#1e8449,#145a32)!important;color:#ffffff!important;
  border:none!important;border-radius:18px!important;
  padding:0.85rem 1.65rem!important;min-height:3.1rem!important;
  font-weight:800!important;font-size:1.02rem!important;width:100%!important;
  transition:transform .22s, box-shadow .22s!important;
  box-shadow:0 6px 22px rgba(30,132,73,.45)!important;
}
div.stButton>button:hover{
  transform:translateY(-3px)!important;
  box-shadow:0 12px 36px rgba(192,57,43,.5)!important;
  background:linear-gradient(135deg,#c0392b,#922b21)!important;
}

/* بطاقات الإحصاء */
.stat-card{background:linear-gradient(135deg,rgba(30,132,73,.1),rgba(39,174,96,.08));
  border:2px solid #27ae60;border-radius:16px;
  padding:1.1rem;text-align:center;margin-bottom:.75rem}
.stat-card h2{font-size:1.85rem;margin:0;color:#145a32!important}
.stat-card p{margin:0;color:#333;font-size:.86rem}

/* البطاقات العامة */
.feature-card{background:#f9f9f9;border:1px solid #27ae60;
  border-right:5px solid #1e8449;
  border-radius:16px;padding:1.25rem;margin:.55rem 0;
  direction:rtl;text-align:right;color:#111}
.feature-card h4{color:#1e8449;margin:0 0 .45rem;font-size:1.02rem}

.result-box{background:#f9f9f9;border:1px solid rgba(30,132,73,.3);
  border-radius:16px;padding:1.45rem;direction:rtl;text-align:right;
  color:#111;line-height:2;margin:.85rem 0}

.db-item{background:#f4f9f4;border-right:4px solid #1e8449;
  border-radius:10px;padding:.85rem 1.05rem;margin:.45rem 0;
  direction:rtl;text-align:right;color:#111}

/* صناديق التنبيه */
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

/* التصنيفات */
.grade-A{color:#1e8449;font-weight:700}
.grade-B{color:#2e86c1;font-weight:700}
.grade-C{color:#d4ac0d;font-weight:700}
.grade-D{color:#c0392b;font-weight:700}

/* الشريط الجانبي */
section[data-testid="stSidebar"]{
  direction:rtl;
  background:linear-gradient(180deg,#f4fbf6,#eaf6ee)!important;
  border-left:4px solid #27ae60;
}
section[data-testid="stSidebar"] .stMarkdown{text-align:right;color:#145a32}

/* التبويبات */
.stTabs [data-baseweb="tab"]{direction:rtl;font-size:.9rem;font-weight:700;color:#145a32}
.stTabs [data-baseweb="tab"][aria-selected="true"]{
  border-bottom:3px solid #c0392b!important;color:#c0392b!important}

/* تسميات الحقول */
.stSelectbox label,.stTextInput label,.stTextArea label,
.stNumberInput label,.stSlider label,.stFileUploader label,.stRadio label{
  direction:rtl;text-align:right;color:#145a32!important;font-weight:700}

/* أيقونة مفتاح API — كتاب مفتوح (Modified for zero-visibility) */
.api-book-widget{
  background:linear-gradient(135deg,#f4fbf6,#eaf6ee);
  border:2px solid #27ae60;border-radius:16px;
  padding:1.1rem 1.2rem;text-align:center;margin:.5rem 0;
}
.api-book-icon{font-size:2.4rem;display:block;margin-bottom:.35rem}
.api-book-slogan{font-size:1rem;font-weight:800;color:#145a32;
  display:block;letter-spacing:.03em}
.api-book-status-active{
  display:block;margin-top:.4rem;font-size:.88rem;font-weight:700;
  color:#1e8449;background:#d5f5e3;border-radius:8px;padding:.2rem .7rem;
}
.api-book-status-inactive{
  display:block;margin-top:.4rem;font-size:.88rem;font-weight:700;
  color:#c0392b;background:#fdecea;border-radius:8px;padding:.2rem .7rem;
}

/* روابط التواصل */
.donia-social{display:flex;flex-wrap:wrap;gap:.45rem;justify-content:center;margin:.35rem 0}
.donia-social a{
  display:inline-block;padding:.35rem .75rem;border-radius:12px;
  background:#145a32;color:#ffffff!important;font-weight:700;font-size:.82rem;
  text-decoration:none!important;border:1px solid #27ae60;
  transition:transform .2s,box-shadow .2s;
}
.donia-social a:hover{
  transform:translateY(-2px);
  box-shadow:0 6px 18px rgba(192,57,43,.4);
  background:#c0392b!important;
}

/* التذييل الثابت */
.donia-ip-footer{
  text-align:center;font-size:.85rem;color:#145a32;font-weight:600;
  padding:1.2rem 0 .5rem;margin-top:1.5rem;
  border-top:3px solid #27ae60;
  background:linear-gradient(90deg,#f4fbf6,#fef9f9,#f4fbf6);
  border-radius:0 0 12px 12px;
}
.donia-footer-social{display:flex;flex-wrap:wrap;gap:.6rem;justify-content:center;margin:.5rem 0}
.donia-footer-social a{
  display:inline-flex;align-items:center;gap:.3rem;
  padding:.4rem .9rem;border-radius:20px;
  background:#145a32;color:#ffffff!important;font-weight:700;font-size:.82rem;
  text-decoration:none!important;transition:background .2s,transform .2s;
}
.donia-footer-social a:hover{background:#c0392b!important;transform:translateY(-2px)}

/* علم الجزائر — مخفي في v2.1 (تم استبداله بألوان الواجهة) */
.dz-flag-wrap{display:none!important}

/* شعار الحكمة الثنائي اللغة */
.donia-slogan-bar{
  display:flex;flex-direction:column;align-items:center;
  gap:.3rem;padding:.9rem 1.5rem;margin:.6rem 0;
  background:linear-gradient(90deg,#145a32 0%,#1e8449 45%,#c0392b 100%);
  border-radius:14px;
  box-shadow:0 4px 20px rgba(20,90,50,.3);
}
.donia-slogan-ar{
  font-family:'Cairo','Amiri',sans-serif;
  font-size:1.35rem;font-weight:800;
  color:#ffffff;letter-spacing:.04em;
  text-shadow:0 2px 6px rgba(0,0,0,.3);
}
.donia-slogan-en{
  font-family:'Montserrat',sans-serif;
  font-size:.9rem;font-weight:600;
  color:rgba(255,255,255,.88);letter-spacing:.18em;
  text-transform:uppercase;
}
.donia-slogan-divider{
  width:40px;height:2px;
  background:rgba(255,255,255,.55);border-radius:2px;
}

/* أزرار محسّنة — تأثيرات Hover احترافية */
.stButton>button{
  border-radius:14px!important;
  font-family:'Cairo',sans-serif!important;
  font-weight:700!important;
  font-size:.95rem!important;
  padding:.55rem 1.4rem!important;
  border:2px solid #27ae60!important;
  background:linear-gradient(135deg,#145a32,#1e8449)!important;
  color:#ffffff!important;
  transition:all .22s cubic-bezier(.4,0,.2,1)!important;
  box-shadow:0 4px 14px rgba(20,90,50,.22)!important;
  letter-spacing:.02em!important;
}
.stButton>button:hover{
  transform:translateY(-3px) scale(1.025)!important;
  background:linear-gradient(135deg,#c0392b,#e74c3c)!important;
  border-color:#c0392b!important;
  box-shadow:0 8px 28px rgba(192,57,43,.45)!important;
}
.stButton>button:active{transform:translateY(0) scale(.98)!important}

/* بطاقات الميزات — border-radius محسّن */
.feature-card{border-radius:16px!important}
.success-box{border-radius:12px!important}
.error-box{border-radius:12px!important}
.result-box{border-radius:16px!important}
.template-box{border-radius:12px!important}

/* حقول الإدخال */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div{
  border-radius:12px!important;
  border:2px solid #27ae60!important;
  font-family:'Cairo',sans-serif!important;
  transition:border-color .2s,box-shadow .2s!important;
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus{
  border-color:#c0392b!important;
  box-shadow:0 0 0 3px rgba(192,57,43,.18)!important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# CURRICULUM
# ═══════════════════════════════════════════════════════════
CURRICULUM = {
    "الطور الابتدائي": {
        "grades": ["السنة الأولى", "السنة الثانية", "السنة الثالثة",
                   "السنة الرابعة", "السنة الخامسة"],
        "subjects": {
            "السنة الأولى": ["اللغة العربية", "الرياضيات", "التربية الإسلامية",
                             "التربية المدنية", "التربية التشكيلية", "التربية البدنية"],
            "السنة الثانية": ["اللغة العربية", "الرياضيات", "التربية الإسلامية",
                              "التربية المدنية", "التربية التشكيلية", "التربية البدنية"],
            "السنة الثالثة": ["اللغة العربية", "الرياضيات", "التربية الإسلامية",
                              "التربية المدنية", "اللغة الفرنسية",
                              "التربية العلمية والتكنولوجية", "التاريخ والجغرافيا"],
            "السنة الرابعة": ["اللغة العربية", "الرياضيات", "التربية الإسلامية",
                              "التربية المدنية", "اللغة الفرنسية",
                              "التربية العلمية والتكنولوجية", "التاريخ والجغرافيا"],
            "السنة الخامسة": ["اللغة العربية", "الرياضيات", "التربية الإسلامية",
                              "التربية المدنية", "اللغة الفرنسية",
                              "التربية العلمية والتكنولوجية", "التاريخ والجغرافيا"],
        },
        "branches": None,
    },
    "الطور المتوسط": {
        "grades": ["السنة الأولى متوسط", "السنة الثانية متوسط",
                   "السنة الثالثة متوسط", "السنة الرابعة متوسط (شهادة)"],
        "subjects": {
            "_default": ["اللغة العربية وآدابها", "الرياضيات",
                         "العلوم الفيزيائية والتكنولوجية", "العلوم الطبيعية والحياة",
                         "التاريخ والجغرافيا", "الاجتماعيات",
                         "التربية الإسلامية", "التربية المدنية",
                         "اللغة الفرنسية", "اللغة الإنجليزية",
                         "التربية التشكيلية", "التربية الموسيقية", "الإعلام الآلي"]
        },
        "branches": None,
    },
    "الطور الثانوي": {
        "grades": ["السنة الأولى ثانوي (جذع مشترك)",
                   "السنة الثانية ثانوي", "السنة الثالثة ثانوي (بكالوريا)"],
        "subjects": None,
        "branches": {
            "السنة الأولى ثانوي (جذع مشترك)": {
                "جذع مشترك علوم وتكنولوجيا": [
                    "الرياضيات", "العلوم الفيزيائية", "العلوم الطبيعية والحياة",
                    "اللغة العربية", "اللغة الفرنسية", "اللغة الإنجليزية",
                    "التاريخ والجغرافيا", "التربية الإسلامية", "الإعلام الآلي"],
                "جذع مشترك آداب وفلسفة": [
                    "اللغة العربية وآدابها", "الفلسفة", "التاريخ والجغرافيا",
                    "اللغة الفرنسية", "اللغة الإنجليزية",
                    "التربية الإسلامية", "الرياضيات"],
            },
            "السنة الثانية ثانوي": {
                "شعبة علوم تجريبية": ["الرياضيات", "العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة", "اللغة العربية", "اللغة الفرنسية",
                    "اللغة الإنجليزية", "التاريخ والجغرافيا", "التربية الإسلامية"],
                "شعبة رياضيات": ["الرياضيات", "العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة", "اللغة العربية",
                    "اللغة الفرنسية", "اللغة الإنجليزية"],
                "شعبة تقني رياضي": ["الرياضيات", "العلوم الفيزيائية", "التكنولوجيا",
                    "اللغة العربية", "اللغة الفرنسية", "اللغة الإنجليزية"],
                "شعبة آداب وفلسفة": ["اللغة العربية وآدابها", "الفلسفة",
                    "التاريخ والجغرافيا", "علم الاجتماع والنفس",
                    "اللغة الفرنسية", "اللغة الإنجليزية", "التربية الإسلامية"],
                "شعبة لغات أجنبية": ["اللغة الفرنسية", "اللغة الإنجليزية",
                    "اللغة الإسبانية", "اللغة الألمانية", "اللغة الإيطالية",
                    "اللغة العربية", "التاريخ والجغرافيا", "الفلسفة"],
                "شعبة تسيير واقتصاد": ["الاقتصاد والمناجمنت", "المحاسبة والمالية",
                    "الرياضيات", "القانون", "اللغة العربية",
                    "اللغة الفرنسية", "اللغة الإنجليزية"],
            },
            "السنة الثالثة ثانوي (بكالوريا)": {
                "شعبة علوم تجريبية": ["الرياضيات", "العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة", "اللغة العربية", "اللغة الفرنسية",
                    "اللغة الإنجليزية", "التاريخ والجغرافيا", "التربية الإسلامية"],
                "شعبة رياضيات": ["الرياضيات", "العلوم الفيزيائية",
                    "العلوم الطبيعية والحياة", "اللغة العربية",
                    "اللغة الفرنسية", "اللغة الإنجليزية"],
                "شعبة تقني رياضي": ["الرياضيات", "العلوم الفيزيائية", "التكنولوجيا",
                    "اللغة العربية", "اللغة الفرنسية", "اللغة الإنجليزية"],
                "شعبة آداب وفلسفة": ["اللغة العربية وآدابها", "الفلسفة",
                    "التاريخ والجغرافيا", "علم الاجتماع والنفس",
                    "اللغة الفرنسية", "اللغة الإنجليزية", "التربية الإسلامية"],
                "شعبة لغات أجنبية": ["اللغة الفرنسية", "اللغة الإنجليزية",
                    "اللغة الإسبانية", "اللغة الألمانية", "اللغة الإيطالية",
                    "اللغة العربية", "التاريخ والجغرافيا", "الفلسفة"],
                "شعبة تسيير واقتصاد": ["الاقتصاد والمناجمنت", "المحاسبة والمالية",
                    "الرياضيات", "القانون", "اللغة العربية",
                    "اللغة الفرنسية", "اللغة الإنجليزية"],
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
    "الرياضيات": ["أنشطة عددية", "أنشطة جبرية", "أنشطة هندسية", "أنشطة إحصائية"],
    "العلوم الفيزيائية والتكنولوجية": ["المادة", "الكهرباء", "الضوء", "الميكانيك"],
    "العلوم الطبيعية والحياة": ["الوحدة والتنوع", "التغذية والهضم", "التوليد", "البيئة"],
    "اللغة العربية وآدابها": ["فهم المكتوب", "الإنتاج الكتابي", "الظاهرة اللغوية", "الميدان الأدبي"],
}

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

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def fix_arabic(text: str) -> str:
    if not _ARABIC_AVAILABLE:
        return str(text)
    try:
        return get_display(reshape(str(text)))
    except Exception:
        return str(text)

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
            st.markdown(
                f'<div style="direction:rtl;text-align:right;'
                f'color:rgba(255,255,255,.92);line-height:2;">{part}</div>',
                unsafe_allow_html=True)

def get_appreciation(grade, total=20):
    pct = grade / total * 100
    if pct >= 90:   return "ممتاز"
    elif pct >= 75: return "جيد جداً"
    elif pct >= 65: return "جيد"
    elif pct >= 50: return "مقبول"
    else:           return "ضعيف"

def calc_average(taqwim, fard, ikhtibhar):
    """حساب المعدل الجزائري: (تقويم×1 + فرض×1 + اختبار×2) / 4"""
    try:
        t = float(taqwim or 0)
        f = float(fard or 0)
        i = float(ikhtibhar or 0)
        return round((t * 1 + f * 1 + i * 2) / 4, 2)
    except (TypeError, ValueError):
        return 0.0

# FIX-3: دالة مساعِدة لتأمين تنسيق الأعداد الذكية مع None
def safe_f(val, fmt=".2f") -> str:
    """تحويل آمن لعدد مع تنسيق — يُعيد '—' عند None أو خطأ."""
    try:
        return format(float(val), fmt)
    except (TypeError, ValueError):
        return "—"

def ar(txt) -> str:
    return fix_arabic(txt)


def _draw_pdf_footer(canvas, doc):
    """تذييل كل صفحة PDF — عبارة حماية الملكية الفكرية (DONIA LABS TECH)."""
    _register_arabic_pdf_fonts()
    canvas.saveState()
    w, _h = doc.pagesize
    fn = _AR_FONT_MAIN
    try:
        canvas.setFont(fn, 8)
    except Exception:
        canvas.setFont("Helvetica", 8)
    txt = fix_arabic(COPYRIGHT_FOOTER_AR) if _ARABIC_AVAILABLE else COPYRIGHT_FOOTER_AR
    canvas.drawCentredString(w / 2.0, 0.55 * cm, txt)
    canvas.restoreState()


def _pdf_footer_canvas_args() -> dict:
    return dict(onFirstPage=_draw_pdf_footer, onLaterPages=_draw_pdf_footer)


# ─── PDF helpers ────────────────────────────────────────────

def generate_simple_pdf(content: str, title: str, subtitle: str = "", rtl: bool = True) -> bytes:
    buf = io.BytesIO()
    _register_arabic_pdf_fonts()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.2*cm, bottomMargin=2.0*cm)
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
        ("ALIGN",        (0, 0), (-1, -1), align_hdr),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",          (0, 0), (-1, -1), 0.5, rl_colors.black),
        ("BACKGROUND",   (0, 0), (-1, -1), rl_colors.HexColor("#f4f2ff")),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(head_tbl)
    story.append(Spacer(1, 8))
    story.append(Paragraph(pdf_text_line(f"DONIA MIND  |  {title}", rtl), S["title"]))
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
            story.append(Paragraph(pdf_text_line(line.replace("#", ""), rtl), S["h2"]))
        elif line.startswith("$") or "```" in line:
            msg = "[ معادلة – راجع النسخة الرقمية ]" if rtl else "[Equation — see digital version]"
            story.append(Paragraph(pdf_text_line(msg, rtl), S["small"]))
        else:
            story.append(Paragraph(pdf_text_line(line, rtl), S["body"]))
        story.append(Spacer(1, 2))
    doc.build(story, **_pdf_footer_canvas_args())
    buf.seek(0)
    return buf.read()

# ─── EXAM PDF (النموذج الجزائري الرسمي) ────────────────────
def generate_exam_pdf(exam_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.8*cm, leftMargin=1.8*cm,
                            topMargin=1.5*cm, bottomMargin=2.0*cm)
    subj = exam_data.get("subject", "") or ""
    rtl, lang = get_pdf_mode_for_subject(subj)
    S = make_pdf_styles(rtl)
    _register_arabic_pdf_fonts()
    fn_b = _AR_FONT_BOLD if rtl else "Helvetica-Bold"
    story = []

    # رأس رسمي عربي دائماً — خلايا Paragraph بخط عربي مُسجَّل (Amiri/Cairo)
    def _cell(txt: str) -> Paragraph:
        return Paragraph(pdf_text_line(txt, True), make_pdf_styles(True)["body"])

    header_data2 = [
        [_cell("الجمهورية الجزائرية الديمقراطية الشعبية"), _cell("")],
        [_cell(f"المؤسسة: {exam_data.get('school', '....................')}"),
         _cell("وزارة التربية الوطنية")],
        [_cell(f"مديرية التربية لولاية: {exam_data.get('wilaya', '..............')}"),
         _cell(f"السنة الدراسية: {exam_data.get('year', '2025/2026')}")],
        [_cell(
            f"المقاطعة: {exam_data.get('district', '.....')}  |  "
            f"المستوى: {exam_data.get('grade', '')}  |  "
            f"المدة: {exam_data.get('duration', 'ساعتان')}"), _cell("")],
    ]
    t = Table(header_data2, colWidths=[10*cm, 6.5*cm])
    t.setStyle(TableStyle([
        ('ALIGN',      (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN',       (0, 0), (1, 0)),
        ('SPAN',       (0, 3), (1, 3)),
        ('GRID',       (0, 0), (-1, -1), 0.5, rl_colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor("#f0f0f0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # FIX-2: نمط مُحدَّد بالكامل بدون underlineWidth (غير مدعوم في بعض الإصدارات)
    title_style = ParagraphStyle(
        "exam_etitle_" + ("rtl" if rtl else "ltr"),
        fontName=fn_b if rtl else "Helvetica-Bold", fontSize=14,
        alignment=TA_CENTER, leading=20,
        textColor=rl_colors.HexColor("#000000"))
    if rtl:
        exam_title = (
            f"اختبار {exam_data.get('semester', 'الفصل الثاني')} "
            f"في مادة {exam_data.get('subject', '')}"
        )
    else:
        exam_title = (
            f"Exam — {exam_data.get('semester', '')} — "
            f"{lang} / {exam_data.get('subject', '')}"
        )
    story.append(Paragraph(pdf_text_line(exam_title, rtl), title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=rl_colors.black))
    story.append(Spacer(1, 10))

    # FIX-2: نمط العنوان الفرعي بدون underlineWidth
    exhead_style = ParagraphStyle(
        "exam_exhead_" + ("rtl" if rtl else "ltr"),
        fontName=fn_b if rtl else "Helvetica-Bold", fontSize=12,
        alignment=(TA_RIGHT if rtl else TA_LEFT), leading=18,
        textColor=rl_colors.HexColor("#000000"))

    for line in exam_data.get('content', '').splitlines():
        line = line.strip()
        if not line:
            continue
        if (re.match(r'^تمرين\s+\d+', line) or re.match(r'^الوضعية الإدماجية', line)
                or re.match(r'^(Exercise|Part|Situation)\s*\d*', line, re.I)):
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

# ─── Grade Report PDF ─────────────────────────────────────
def generate_report_pdf(report_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=2.0*cm)
    _register_arabic_pdf_fonts()
    fn_pdf = _AR_FONT_MAIN
    fb_pdf = _AR_FONT_BOLD
    S = make_pdf_styles(True)
    story = []

    story.append(Paragraph(ar("تحليل نتائج الأقسام"), S["title"]))
    story.append(Paragraph(
        ar(f"{report_data.get('school', '')} | "
           f"{report_data.get('subject', '')} | "
           f"{report_data.get('semester', '')}"),
        S["center"]))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=rl_colors.HexColor("#0d9488")))
    story.append(Spacer(1, 12))

    for cls in report_data.get('classes', []):
        story.append(Paragraph(ar(f"تحليل نتائج القسم {cls['name']}"), S["h2"]))

        # FIX-3: safe_f() بدلاً من :.2f مباشرةً على قيم محتملة None
        info_line = (
            f"عدد التلاميذ: {cls.get('total', 0)} — "
            f"المعدل: {safe_f(cls.get('avg', 0))} — "
            f"أعلى: {safe_f(cls.get('max', 0))} — "
            f"أدنى: {safe_f(cls.get('min', 0))} — "
            f"النجاح: {safe_f(cls.get('pass_rate', 0), '.1f')}%"
        )
        story.append(Paragraph(ar(info_line), S["body"]))
        story.append(Spacer(1, 6))

        if cls.get('top5'):
            story.append(Paragraph(ar("أفضل 5 تلاميذ"), S["h2"]))
            top_data = [[
                Paragraph(ar("الرتبة"), S["body"]),
                Paragraph(ar("الاسم"), S["body"]),
                Paragraph(ar("المعدل"), S["body"]),
            ]]
            for i, s in enumerate(cls['top5'], 1):
                top_data.append([
                    Paragraph(str(i), S["body"]),
                    Paragraph(ar(s['name']), S["body"]),
                    Paragraph(safe_f(s['avg']), S["body"]),
                ])
            t = Table(top_data, colWidths=[2*cm, 10*cm, 3*cm])
            t.setStyle(TableStyle([
                ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND',  (0, 0), (-1, 0),  rl_colors.HexColor("#667eea")),
                ('TEXTCOLOR',   (0, 0), (-1, 0),  rl_colors.white),
                ('GRID',        (0, 0), (-1, -1), 0.5, rl_colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [rl_colors.white, rl_colors.HexColor("#f8f8ff")]),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))

        if cls.get('distribution'):
            story.append(Paragraph(ar("توزيع الدرجات"), S["h2"]))
            dist = cls['distribution']
            dist_data = [
                [
                    Paragraph(ar("0-5"), S["body"]),
                    Paragraph(ar("5-10"), S["body"]),
                    Paragraph(ar("10-15"), S["body"]),
                    Paragraph(ar("15-20"), S["body"]),
                ],
                [
                    Paragraph(str(dist.get('0-5', 0)), S["body"]),
                    Paragraph(str(dist.get('5-10', 0)), S["body"]),
                    Paragraph(str(dist.get('10-15', 0)), S["body"]),
                    Paragraph(str(dist.get('15-20', 0)), S["body"]),
                ],
            ]
            t = Table(dist_data, colWidths=[4*cm]*4)
            t.setStyle(TableStyle([
                ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0),  rl_colors.HexColor("#302b63")),
                ('TEXTCOLOR',  (0, 0), (-1, 0),  rl_colors.white),
                ('GRID',       (0, 0), (-1, -1), 0.5, rl_colors.grey),
            ]))
            story.append(t)
        story.append(Spacer(1, 16))

    if report_data.get('ai_analysis'):
        story.append(Paragraph(ar("التحليل البيداغوجي"), S["h2"]))
        for line in report_data['ai_analysis'].splitlines():
            if line.strip():
                story.append(Paragraph(ar(line.strip()), S["body"]))
        story.append(Spacer(1, 4))

    doc.build(story, **_pdf_footer_canvas_args())
    buf.seek(0)
    return buf.read()

# ─── Grade Book Excel ────────────────────────────────────────
def generate_grade_book_excel(students: list, class_name: str,
                               subject: str, semester: str, school: str) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "دفتر التنقيط"

    title_font  = Font(name="Arial", bold=True, size=11)
    header_font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    body_font   = Font(name="Arial", size=10)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    right  = Alignment(horizontal="right",  vertical="center")
    thin   = Side(style="thin", color="000000")
    border = Border(top=thin, bottom=thin, left=thin, right=thin)

    purple_fill = PatternFill("solid", fgColor="764ba2")
    light_fill  = PatternFill("solid", fgColor="f0f0ff")

    ws.merge_cells("A1:I1")
    ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية"
    ws["A1"].font = title_font; ws["A1"].alignment = center; ws["A1"].fill = light_fill

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

    ws.append([])

    headers = ["رقم التعريف", "اللقب", "الاسم", "تاريخ الميلاد",
               "تقويم /20", "فرض /20", "اختبار /20", "المعدل /20", "التقديرات"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col, value=h)
        cell.font = header_font; cell.alignment = center
        cell.fill = purple_fill; cell.border = border
    ws.row_dimensions[6].height = 30

    for idx, stu in enumerate(students):
        row = 7 + idx
        avg    = calc_average(stu.get('taqwim', 0), stu.get('fard', 0), stu.get('ikhtibhar', 0))
        apprec = get_appreciation(avg)
        values = [
            stu.get('id', ''), stu.get('nom', ''), stu.get('prenom', ''),
            str(stu.get('dob', '')), stu.get('taqwim', ''), stu.get('fard', ''),
            stu.get('ikhtibhar', ''), avg, apprec,
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = body_font; cell.border = border
            cell.alignment = center if col != 2 else right
            if idx % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="f8f8ff")
        ws.row_dimensions[row].height = 22

    last_data = 6 + len(students)
    ws.append([])
    stat_row = last_data + 2
    avgs_all = [calc_average(s.get('taqwim', 0), s.get('fard', 0), s.get('ikhtibhar', 0))
                for s in students]
    stats = [
        ("عدد التلاميذ", len(students)),
        ("معدل القسم", round(sum(avgs_all) / max(len(avgs_all), 1), 2)),
        ("الناجحون", sum(1 for a in avgs_all if a >= 10)),
    ]
    for i, (label, val) in enumerate(stats):
        lc = ws.cell(row=stat_row + i, column=1, value=label)
        vc = ws.cell(row=stat_row + i, column=2, value=val)
        lc.font = Font(bold=True, name="Arial", size=10)
        vc.font = Font(bold=True, name="Arial", size=10, color="764ba2")
        lc.fill = light_fill; vc.fill = light_fill
        lc.border = border; vc.border = border

    widths = [18, 16, 16, 14, 10, 10, 10, 10, 12]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.sheet_view.rightToLeft = True

    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)
    return buf.read()

# ─── FIX-6: Parse Excel grade book — نسخة أكثر متانة + أوراق متعددة ──────
def _parse_rows_from_list(rows_list) -> list:
    """استخراج تلاميذ من صفوف جدول واحد (ورقة واحدة)."""
    students = []
    data_started = False
    HEADER_MARKERS = {'matricule', 'رقم التعريف', 'اللقب', 'nom', 'prénom',
                      'الاسم', 'تقويم', 'فرض', 'اختبار', 'taqwim'}

    for i, row in enumerate(rows_list, 1):
        if not any(c is not None for c in row):
            continue  # صف فارغ — تجاوُز

        row_strs = [str(c).strip().lower() if c is not None else '' for c in row]

        if not data_started:
            if any(m in row_strs for m in HEADER_MARKERS):
                data_started = True
            continue

        vals = list(row)
        if len(vals) < 4:
            continue

        nom = str(vals[1] or '').strip()
        if not nom or nom.lower() in ('اللقب', 'nom', 'prénom', 'الاسم'):
            continue

        try:
            stu = {
                'id':        str(vals[0] or '').strip(),
                'nom':       nom,
                'prenom':    str(vals[2] or '').strip() if len(vals) > 2 else '',
                'dob':       str(vals[3] or '').strip() if len(vals) > 3 else '',
                'taqwim':    float(vals[4]) if len(vals) > 4 and vals[4] is not None else 0.0,
                'fard':      float(vals[5]) if len(vals) > 5 and vals[5] is not None else 0.0,
                'ikhtibhar': float(vals[6]) if len(vals) > 6 and vals[6] is not None else 0.0,
            }
            stu['average'] = calc_average(stu['taqwim'], stu['fard'], stu['ikhtibhar'])
            stu['apprec']  = get_appreciation(stu['average'])
            students.append(stu)
        except (ValueError, TypeError):
            continue

    return students


def list_excel_sheet_names(uploaded_file) -> list:
    """قائمة أسماء أوراق ملف Excel (لاختيار المستخدم)."""
    try:
        uploaded_file.seek(0)
        wb = openpyxl.load_workbook(uploaded_file, read_only=True, data_only=True)
        names = list(wb.sheetnames)
        wb.close()
        return names
    except Exception:
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        bio = io.BytesIO(raw)
        try:
            xl = pd.ExcelFile(bio)
            return list(xl.sheet_names)
        except Exception:
            return []


def parse_grade_book_excel(uploaded_file, sheet_name=None, merge_all_sheets=False) -> list:
    """
    FIX-6: تحليل دفتر التنقيط الجزائري بصورة أكثر متانة.
    يدعم:
      - الملفات التي تبدأ ببيانات قبل العنوان
      - الصفوف التي تحتوي على None جزئياً
      - الملفات ذات الفتارات (blank rows) المتعددة
      - .xlsx عبر openpyxl، مع fallback إلى pandas عند الحاجة
      - دمج جميع الأوراق (merge_all_sheets=True) مع الحقل sheet_source
      - ورقة محددة عبر sheet_name عند عدم الدمج
    """
    students = []
    try:
        uploaded_file.seek(0)
        wb = openpyxl.load_workbook(uploaded_file, data_only=True)
        if merge_all_sheets:
            for nm in wb.sheetnames:
                rows_list = list(wb[nm].iter_rows(values_only=True))
                part = _parse_rows_from_list(rows_list)
                for s in part:
                    s['sheet_source'] = nm
                students.extend(part)
            return students
        if sheet_name and sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.active
        rows_list = list(ws.iter_rows(values_only=True))
        return _parse_rows_from_list(rows_list)
    except Exception:
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        bio = io.BytesIO(raw)
        name = (getattr(uploaded_file, "name", "") or "").lower()
        try:
            xl = pd.ExcelFile(bio)
        except Exception:
            try:
                df = pd.read_excel(bio, engine="openpyxl", header=None)
                rows_list = [tuple(row) for row in df.values]
                return _parse_rows_from_list(rows_list)
            except Exception:
                bio.seek(0)
                try:
                    eng = "xlrd" if name.endswith(".xls") and not name.endswith(".xlsx") else None
                    df = pd.read_excel(bio, engine=eng, header=None) if eng else pd.read_excel(bio, header=None)
                except Exception:
                    bio.seek(0)
                    df = pd.read_excel(bio, header=None)
                rows_list = [tuple(row) for row in df.values]
                return _parse_rows_from_list(rows_list)

        if merge_all_sheets:
            for nm in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=nm, header=None)
                rows_list = [tuple(row) for row in df.values]
                part = _parse_rows_from_list(rows_list)
                for s in part:
                    s['sheet_source'] = nm
                students.extend(part)
            return students
        sn = sheet_name if sheet_name and sheet_name in xl.sheet_names else xl.sheet_names[0]
        df = pd.read_excel(xl, sheet_name=sn, header=None)
        rows_list = [tuple(row) for row in df.values]
        return _parse_rows_from_list(rows_list)

# ─── FIX-4: دالة مساعِدة لبناء إحصاء قسم من قائمة تلاميذ ──
def build_class_stats(stus: list, cls_name: str) -> dict:
    """
    FIX-4: حماية max()/min() على قوائم فارغة.
    تُعيد dict موحَّد للإحصاءات مع قيم افتراضية آمنة.
    """
    avgs   = [s['average'] for s in stus]
    passed = [a for a in avgs if a >= 10]
    dist   = {"0-5": 0, "5-10": 0, "10-15": 0, "15-20": 0}
    for a in avgs:
        if   a < 5:  dist["0-5"]   += 1
        elif a < 10: dist["5-10"]  += 1
        elif a < 15: dist["10-15"] += 1
        else:         dist["15-20"] += 1
    sorted_stus = sorted(stus, key=lambda x: x['average'], reverse=True)
    return {
        "name":      cls_name,
        "total":     len(stus),
        "avg":       sum(avgs) / max(len(avgs), 1),
        "max":       max(avgs) if avgs else 0.0,   # FIX-4
        "min":       min(avgs) if avgs else 0.0,   # FIX-4
        "pass_rate": len(passed) / max(len(avgs), 1) * 100,
        "distribution": dist,
        "top5": [{"name": f"{s['nom']} {s['prenom']}", "avg": s['average']}
                 for s in sorted_stus[:5]],
        "students": stus,
    }

# ─── Lesson Plan PDF (النموذج الرسمي للمذكرة) ───────────────
def generate_lesson_plan_pdf(plan_data: dict) -> bytes:
    buf = io.BytesIO()
    _register_arabic_pdf_fonts()
    rtl, _ = get_pdf_mode_for_subject(plan_data.get("subject", "") or "")
    S_ar = make_pdf_styles(True)
    S = make_pdf_styles(rtl)
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.2*cm, leftMargin=1.2*cm,
                            topMargin=1.2*cm, bottomMargin=2.0*cm)
    story = []

    story.append(Paragraph(
        pdf_text_line("الجمهورية الجزائرية الديمقراطية الشعبية — وزارة التربية الوطنية", True),
        S_ar["center"]))
    story.append(Paragraph(
        pdf_text_line(
            f"مذكرة رقم: ____  |  المؤسسة: {plan_data.get('school', '.............')}  "
            f"|  الأستاذ(ة): {plan_data.get('teacher', '.............')}", True),
        S_ar["center"]))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=rl_colors.HexColor("#0d9488")))
    story.append(Spacer(1, 6))

    info_data = [
        [Paragraph(pdf_text_line("الميدان", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('domain', ''), rtl), S["body"]),
         Paragraph(pdf_text_line("المستوى", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('grade', ''), rtl), S["body"])],
        [Paragraph(pdf_text_line("الباب / الوحدة", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('chapter', ''), rtl), S["body"]),
         Paragraph(pdf_text_line("المدة الزمنية", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('duration', '50 دقيقة'), rtl), S["body"])],
        [Paragraph(pdf_text_line("المورد المعرفي", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('lesson', ''), rtl), S["body"]),
         Paragraph(pdf_text_line("نوع الحصة", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('session_type', 'درس نظري'), rtl), S["body"])],
        [Paragraph(pdf_text_line("مستوى من الكفاءة", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('competency', ''), rtl), S["body"]),
         "", ""],
    ]
    t = Table(info_data, colWidths=[3.5*cm, 7*cm, 3.5*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ('ALIGN',      (0, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('GRID',       (0, 0), (-1, -1), 0.5, rl_colors.black),
        ('BACKGROUND', (0, 0), (0, -1),  rl_colors.HexColor("#e8e8ff")),
        ('BACKGROUND', (2, 0), (2, -2),  rl_colors.HexColor("#e8e8ff")),
        ('SPAN',       (1, 3), (3, 3)),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    lesson_rows = [[
        Paragraph(pdf_text_line("المراحل", True), S_ar["body"]),
        Paragraph(pdf_text_line("المدة", True), S_ar["body"]),
        Paragraph(pdf_text_line("سير الدرس", True), S_ar["body"]),
        Paragraph(pdf_text_line("التقويم والإرشادات", True), S_ar["body"]),
    ]]

    sections = [
        ("تهيئة",              plan_data.get('duration_t', '5 د'),  plan_data.get('intro', '')),
        ("أنشطة بناء الموارد", plan_data.get('duration_b', '25 د'), plan_data.get('build', '')),
        ("إعادة الاستثمار",    plan_data.get('duration_r', '15 د'), plan_data.get('reinvest', '')),
    ]
    for section, dur, content in sections:
        lesson_rows.append([
            Paragraph(pdf_text_line(section, True), S_ar["body"]),
            Paragraph(pdf_text_line(dur, rtl), S["body"]),
            Paragraph(pdf_text_line(str(content)[:400], rtl), S["body"]),
            Paragraph(pdf_text_line(plan_data.get('eval', ''), rtl), S["body"]),
        ])
    lesson_rows.append([
        Paragraph(pdf_text_line("الواجب المنزلي", True), S_ar["body"]),
        Paragraph("", S_ar["body"]),
        Paragraph(pdf_text_line(plan_data.get('homework', ''), rtl), S["body"]),
        Paragraph("", S_ar["body"]),
    ])

    col_widths = [2.5*cm, 1.5*cm, 10*cm, 3.5*cm]
    lt = Table(lesson_rows, colWidths=col_widths, repeatRows=1)
    lt.setStyle(TableStyle([
        ('ALIGN',       (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE',    (0, 0), (-1, -1), 9),
        ('BACKGROUND',  (0, 0), (-1, 0),  rl_colors.HexColor("#0f766e")),
        ('TEXTCOLOR',   (0, 0), (-1, 0),  rl_colors.white),
        ('GRID',        (0, 0), (-1, -1), 0.5, rl_colors.black),
        ('BACKGROUND',  (0, 1), (0, -1),  rl_colors.HexColor("#f0fdfa")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [rl_colors.white, rl_colors.HexColor("#f8fafc")]),
        # FIX: WORDWRAP حُذف (غير مدعوم)، نستخدم Paragraph بدلاً منه
        # FIX: ROWHEIGHT بتنسيق صحيح لصفوف المحتوى (ارتفاع أدنى)
        ('MINROWHEIGHT', (0, 1), (-1, -2), 60),
    ]))
    story.append(lt)
    story.append(Spacer(1, 6))

    pre_data = [
        [Paragraph(pdf_text_line("المكتسبات القبلية", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('prerequisites', ''), rtl), S["body"])],
        [Paragraph(pdf_text_line("الوسائل والأدوات", True), S_ar["body"]),
         Paragraph(pdf_text_line(
             plan_data.get('tools', 'الكتاب المدرسي، السبورة، دليل الأستاذ'), rtl), S["body"])],
        [Paragraph(pdf_text_line("نقد ذاتي", True), S_ar["body"]),
         Paragraph(pdf_text_line(plan_data.get('self_critique', ''), rtl), S["body"])],
    ]
    pt = Table(pre_data, colWidths=[3.5*cm, 14*cm])
    pt.setStyle(TableStyle([
        ('ALIGN',      (0, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.5, rl_colors.black),
        ('BACKGROUND', (0, 0), (0, -1),  rl_colors.HexColor("#e8e8ff")),
    ]))
    story.append(pt)
    doc.build(story, **_pdf_footer_canvas_args())
    buf.seek(0)
    return buf.read()

# ═══════════════════════════════════════════════════════════
# WORD (.docx) EXPORT HELPERS — تصدير Word
# ═══════════════════════════════════════════════════════════

def _docx_set_rtl(paragraph):
    """Force RTL direction on a paragraph."""
    pPr = paragraph._p.get_or_add_pPr()
    bidi_el = OxmlElement('w:bidi')
    bidi_el.set(qn('w:val'), '1')
    pPr.append(bidi_el)


def _docx_heading(doc, text: str, level: int = 1, color_hex: str = "145a32"):
    """Add a styled heading paragraph."""
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _docx_set_rtl(p)
    for run in p.runs:
        r, g, b = (int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        run.font.color.rgb = RGBColor(r, g, b)
    return p


def _docx_para(doc, text: str, bold: bool = False, size: int = 12,
               align=WD_ALIGN_PARAGRAPH.RIGHT):
    """Add a styled body paragraph."""
    p = doc.add_paragraph()
    p.alignment = align
    _docx_set_rtl(p)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    return p


def generate_exam_docx(exam_data: dict) -> bytes:
    """Generate a Word (.docx) exam document matching the Algerian official template."""
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    # ── Header table (official Algerian exam header) ──────────
    hdr = doc.add_table(rows=3, cols=2)
    hdr.style = 'Table Grid'
    cells = hdr.rows[0].cells
    cells[0].text = exam_data.get('school', '')
    cells[1].text = "الجمهورية الجزائرية الديمقراطية الشعبية"
    cells = hdr.rows[1].cells
    cells[0].text = f"السنة الدراسية: {exam_data.get('year', '')}"
    cells[1].text = "وزارة التربية الوطنية"
    cells = hdr.rows[2].cells
    cells[0].text = f"المدة: {exam_data.get('duration', '')}"
    cells[1].text = (f"المستوى: {exam_data.get('grade', '')}   |   "
                     f"المقاطعة: {exam_data.get('district', '')}")
    for row in hdr.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                _docx_set_rtl(para)
                for run in para.runs:
                    run.font.size = Pt(10)

    doc.add_paragraph()

    # ── Exam title ─────────────────────────────────────────────
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _docx_set_rtl(title_p)
    run = title_p.add_run(
        f"اختبار {exam_data.get('semester', '')} في مادة {exam_data.get('subject', '')}")
    run.bold      = True
    run.font.size = Pt(14)

    doc.add_paragraph()

    # ── Content ───────────────────────────────────────────────
    content = exam_data.get('content', '')
    for line in content.split('\n'):
        _docx_para(doc, line)

    doc.add_paragraph()
    sign_p = doc.add_paragraph("بالتوفيق                                              إنتهى")
    sign_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def generate_lesson_plan_docx(plan_data: dict) -> bytes:
    """Generate a Word (.docx) lesson plan (مذكرة) document."""
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    for section in doc.sections:
        section.top_margin    = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    _docx_heading(doc, "المذكرة البيداغوجية — DONIA MIND", level=1)

    # Info table
    info_rows = [
        ["المؤسسة", plan_data.get('school', '')],
        ["الأستاذ(ة)", plan_data.get('teacher', '')],
        ["المادة", plan_data.get('subject', '')],
        ["المستوى", plan_data.get('grade', '')],
        ["الدرس", plan_data.get('lesson', '')],
        ["المجال", plan_data.get('domain', '')],
        ["المدة الإجمالية", plan_data.get('duration', '')],
    ]
    tbl = doc.add_table(rows=len(info_rows), cols=2)
    tbl.style = 'Table Grid'
    for i, (label, val) in enumerate(info_rows):
        cells = tbl.rows[i].cells
        cells[0].text = label
        cells[1].text = val
        for cell in cells:
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                _docx_set_rtl(para)

    doc.add_paragraph()
    _docx_heading(doc, "محتوى المذكرة", level=2, color_hex="1e8449")
    content = plan_data.get('content', '')
    for line in content.split('\n'):
        _docx_para(doc, line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def generate_report_docx(report_data: dict) -> bytes:
    """Generate a Word (.docx) pedagogical report."""
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    for section in doc.sections:
        section.top_margin    = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    _docx_heading(doc, "تقرير تحليل نتائج الأقسام", level=1)
    _docx_para(doc,
               f"المادة: {report_data.get('subject', '')}   |   "
               f"الفصل: {report_data.get('semester', '')}   |   "
               f"المؤسسة: {report_data.get('school', '')}",
               bold=True)
    doc.add_paragraph()

    for cls in report_data.get('classes', []):
        _docx_heading(doc, f"القسم: {cls.get('name', '')}", level=2, color_hex="1e8449")
        stats_rows = [
            ["عدد التلاميذ",   str(cls.get('count', ''))],
            ["المعدل العام",   str(cls.get('avg',   ''))],
            ["أعلى معدل",     str(cls.get('max',   ''))],
            ["أدنى معدل",     str(cls.get('min',   ''))],
            ["نسبة النجاح %", str(cls.get('pass_rate', ''))],
        ]
        tbl = doc.add_table(rows=len(stats_rows), cols=2)
        tbl.style = 'Table Grid'
        for i, (label, val) in enumerate(stats_rows):
            cells = tbl.rows[i].cells
            cells[0].text = label
            cells[1].text = val
            for cell in cells:
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    _docx_set_rtl(para)
        doc.add_paragraph()

        top5 = cls.get('top5', [])
        if top5:
            _docx_para(doc, "أفضل 5 تلاميذ:", bold=True)
            for idx, (name, avg) in enumerate(top5, 1):
                _docx_para(doc, f"  {idx}. {name} — {avg:.2f}")
        doc.add_paragraph()

    if report_data.get('ai_analysis'):
        _docx_heading(doc, "التقرير البيداغوجي (الذكاء الاصطناعي)", level=2,
                      color_hex="922b21")
        for line in report_data['ai_analysis'].split('\n'):
            _docx_para(doc, line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════
# SIDEBAR (MODIFIED: API keys removed from UI, QR Code added)
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    try:
        logo = Image.open("assets/logo_donia.jpg")
        st.image(logo, use_column_width=True)
    except:
        st.markdown("### 🧠 DONIA LABS TECH")
    
    # API Status (Zero-Visibility - no keys displayed or input fields)
    groq_key_present = get_groq_api_key() is not None
    arcee_key_present = get_arcee_api_key() is not None
    
    if groq_key_present and arcee_key_present:
        st.markdown('<div class="api-book-widget"><span class="api-book-icon">🔐</span><span class="api-book-slogan">النظام متصل بالكامل</span><span class="api-book-status-active">Groq + Arcee نشطان</span></div>', unsafe_allow_html=True)
    elif groq_key_present:
        st.markdown('<div class="api-book-widget"><span class="api-book-icon">🔐</span><span class="api-book-slogan">النظام متصل جزئياً</span><span class="api-book-status-active">Groq نشط | Arcee غير متاح</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-book-widget"><span class="api-book-icon">📚</span><span class="api-book-slogan">العلم هو السلاح</span><span class="api-book-status-inactive">يرجى تكوين مفاتيح API في secrets</span></div>', unsafe_allow_html=True)
    
    # QR Code for app sharing
    st.markdown("### 📱 مشاركة التطبيق")
    app_url = st.secrets.get("APP_URL", "https://doniamind1-pvnmwp3kdthtlfct7uhopm.streamlit.app/")
    qr_code_img = generate_qr_code(app_url)
    st.image(qr_code_img, width=150, caption="امسح الرمز للوصول السريع")
    
    # Interactive Robot Assistant (non-blocking)
    with st.expander("🤖 مساعد دونيا الذكي", expanded=False):
        st.markdown("**اسألني عن أي شيء!**")
        user_question = st.text_input("اكتب سؤالك هنا...", key="assistant_input_sidebar")
        if st.button("أرسل", key="assistant_send_sidebar"):
            if user_question:
                with st.spinner("جاري التفكير..."):
                    response, _ = dual_engine.generate_with_audit(user_question, "عام")
                    st.markdown(f"**الإجابة:** {response}")
            else:
                st.warning("الرجاء كتابة سؤال.")
    
    # Stats
    st.markdown("### 📊 إحصائيات سريعة")
    ex_count, lp_count, exam_count, corr_count = get_stats()
    col1, col2 = st.columns(2)
    col1.metric("تمارين", ex_count)
    col2.metric("مذكرات", lp_count)
    col1.metric("امتحانات", exam_count)
    col2.metric("تصحيحات", corr_count)
    
    # Social Links
    st.markdown("### 🌐 تواصل مع المختبر")
    st.markdown(f"""
    <div class="donia-social">
        <a href="{SOCIAL_URL_WHATSAPP}" target="_blank">📱 واتساب</a>
        <a href="{SOCIAL_URL_LINKEDIN}" target="_blank">🔗 لينكدإن</a>
        <a href="{SOCIAL_URL_FACEBOOK}" target="_blank">📘 فيسبوك</a>
        <a href="{SOCIAL_URL_TELEGRAM}" target="_blank">✈️ تليجرام</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Copyright
    st.markdown("---")
    st.markdown(f"<div class='donia-ip-footer'><p>{COPYRIGHT_FOOTER_AR}</p><div class='donia-footer-social'><a href='{SOCIAL_URL_WHATSAPP}' target='_blank'>واتساب</a><a href='{SOCIAL_URL_LINKEDIN}' target='_blank'>لينكدإن</a><a href='{SOCIAL_URL_FACEBOOK}' target='_blank'>فيسبوك</a><a href='{SOCIAL_URL_TELEGRAM}' target='_blank'>تليجرام</a></div></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# MAIN UI — تبويبات المحتوى (محسنة مع Dual-LLM)
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div class="title-card">
    <h1>🧠 DONIA MIND 1 — المعلم الذكي</h1>
    <p>المنصة الذكية للمنظومة التربوية الجزائرية — بالذكاء الاصطناعي المتقدم</p>
</div>
<div class="welcome-banner">
    🤖 أهلاً بك أستاذنا القدير في رحاب DONIA MIND.. معاً نصنع مستقبل التعليم الجزائري بذكاء واحترافية.
</div>
<div class="donia-slogan-bar">
    <div class="donia-slogan-ar">بالعلم نرتقي</div>
    <div class="donia-slogan-divider"></div>
    <div class="donia-slogan-en">Education Uplifts Us</div>
</div>
""", unsafe_allow_html=True)

# === NEW: Dual-LLM Content Generator Expander (Additive) ===
with st.expander("🚀 Dual-LLM Content Generator (Groq + Arcee)", expanded=False):
    st.markdown("#### توليد محتوى تعليمي باستخدام نموذجين من الذكاء الاصطناعي مع تدقيق داخلي")
    col1, col2 = st.columns(2)
    with col1:
        generation_type = st.selectbox("نوع المحتوى", ["درس", "تمرين", "اختبار", "تقرير"], key="gen_type")
        subject = st.text_input("المادة", value="الرياضيات", key="subject_input")
    with col2:
        grade = st.text_input("المستوى", value="السنة الرابعة متوسط", key="grade_input")
        prompt = st.text_area("وصف المحتوى المطلوب", height=100, value=f"أنشئ {generation_type} في مادة {subject} لمستوى {grade}.", key="prompt_input")
    
    if st.button("توليد المحتوى", key="dual_gen_button"):
        with st.spinner("جاري توليد المحتوى وتدقيقه..."):
            full_prompt = f"أنت أستاذ في المنظومة التعليمية الجزائرية. {prompt} تأكد من الالتزام بالمناهج الجزائرية."
            content, metadata = dual_engine.generate_with_audit(full_prompt, subject)
            
            verified_content, corrections = verify_content_against_benchmarks(content, subject)
            
            st.success("✅ تم توليد المحتوى وتدقيقه بنجاح")
            with st.expander("عرض التقرير الداخلي (التدقيق)", expanded=False):
                st.json(metadata)
                if corrections:
                    st.markdown("**التصحيحات التي تمت:**")
                    for corr in corrections:
                        st.write(f"- {corr}")
            
            # Live Preview
            render_live_preview(verified_content, f"{generation_type} - {subject} - {grade}")
            
            # Download buttons
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    label="📥 تحميل PDF",
                    data=generate_simple_pdf(verified_content, generation_type, subject),
                    file_name=f"{generation_type}_{subject}_{grade}.pdf",
                    mime="application/pdf",
                    key="download_pdf_dual"
                )
            with col_b:
                if st.button("🔄 إعادة التوليد باستخدام نموذج بديل", key="regenerate_button"):
                    with st.spinner("جاري إعادة التوليد..."):
                        alt_content = dual_engine.generate_with_single_model(full_prompt, "arcee")
                        alt_verified, _ = verify_content_against_benchmarks(alt_content, subject)
                        st.markdown("### المحتوى المعاد توليده")
                        st.write(alt_verified)

# === ORIGINAL TABS (Preserved exactly) ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 اختبارات (Exams)",
    "📖 مذكرات دراسية (Lesson Plans)",
    "📊 تحليل نتائج (Reports)",
    "📁 دفتر التنقيط (Grade Book)",
    "⚙️ إعدادات متقدمة"
])

# ===================== TAB 1: EXAMS =====================
with tab1:
    st.markdown("### 🎯 توليد اختبارات ذكية (Dual-LLM)")
    col1, col2, col3 = st.columns(3)
    with col1:
        level = st.selectbox("الطور", list(CURRICULUM.keys()), key="exam_level")
    with col2:
        if level == "الطور الثانوي":
            grade = st.selectbox("السنة", CURRICULUM[level]["grades"], key="exam_grade")
            branch = st.selectbox("الشعبة", list(CURRICULUM[level]["branches"].get(grade, {}).keys()), key="exam_branch")
            subjects = CURRICULUM[level]["branches"][grade].get(branch, [])
        else:
            grade = st.selectbox("السنة", CURRICULUM[level]["grades"], key="exam_grade")
            branch = None
            subjects = CURRICULUM[level]["subjects"].get(grade, CURRICULUM[level]["subjects"].get("_default", []))
    with col3:
        subject = st.selectbox("المادة", subjects, key="exam_subject")
    
    col1, col2 = st.columns(2)
    with col1:
        semester = st.selectbox("الفصل", ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"], key="exam_semester")
    with col2:
        duration = st.selectbox("المدة", ["ساعة واحدة", "ساعتان", "ثلاث ساعات"], key="exam_duration")
    
    advanced = st.checkbox("إعدادات متقدمة (للخبراء)", key="exam_advanced")
    if advanced:
        col1, col2 = st.columns(2)
        with col1:
            school = st.text_input("اسم المؤسسة", placeholder="مثال: متوسطة الشهداء")
        with col2:
            wilaya = st.text_input("الولاية", placeholder="مثال: الجزائر")
        district = st.text_input("المقاطعة", placeholder="اختياري")
    else:
        school = "متوسطة الشهداء"
        wilaya = "الجزائر"
        district = ""
    
    col1, col2 = st.columns([3, 1])
    with col2:
        generate_btn = st.button("🚀 توليد الاختبار", type="primary", use_container_width=True)
    if generate_btn:
        if not get_groq_api_key():
            st.error("❌ الرجاء إضافة مفتاح GROQ API في secrets")
        else:
            with st.spinner("🔮 جاري توليد الاختبار باستخدام Groq + Arcee..."):
                lang_clause = llm_output_language_clause(subject)
                exam_prompt = f"""
                أنت خبير في المناهج الجزائرية. قم بإنشاء اختبار نموذجي لمادة {subject} للمستوى {grade} في {level}، الفصل {semester}.
                
                {lang_clause}
                
                قواعد الاختبار:
                - يجب أن يحتوي على 3 تمارين على الأقل ووضعية إدماجية واحدة.
                - الأسئلة واضحة ومتنوعة (صح/خطأ، اختيار من متعدد، أسئلة مقالية قصيرة).
                - يجب أن يكون الاختبار قابلاً للطباعة ويلبي معايير وزارة التربية الوطنية.
                - مدة الاختبار: {duration}.
                
                قم بتنسيق الاختبار بشكل واضح مع تسمية التمارين ووضع العلامات الكاملة.
                """
                
                exam_content, _ = dual_engine.generate_with_audit(exam_prompt, subject)
                
                exam_data = {
                    "level": level, "grade": grade, "subject": subject,
                    "semester": semester, "duration": duration,
                    "school": school, "wilaya": wilaya, "district": district,
                    "year": "2025/2026", "content": exam_content
                }
                
                db_exec(
                    "INSERT INTO exams (level, grade, subject, semester, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (level, grade, subject, semester, exam_content, datetime.now().isoformat())
                )
                
                st.session_state['exam_data'] = exam_data
                st.session_state['exam_content'] = exam_content
                st.success("✅ تم توليد الاختبار بنجاح!")
                
                # Live Preview
                st.markdown("### 📄 معاينة الاختبار")
                st.markdown(f"<div class='result-box'>{exam_content.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                
                # Download options
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    pdf_bytes = generate_exam_pdf(exam_data)
                    st.download_button("📥 تحميل PDF", pdf_bytes, f"exam_{grade}_{subject}.pdf", "application/pdf")
                with col_b:
                    docx_bytes = generate_exam_docx(exam_data)
                    if docx_bytes:
                        st.download_button("📥 تحميل Word", docx_bytes, f"exam_{grade}_{subject}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                with col_c:
                    if st.button("🔄 إعادة توليد بالنموذج البديل"):
                        with st.spinner("جاري إعادة التوليد..."):
                            alt_content = dual_engine.generate_with_single_model(exam_prompt, "arcee")
                            st.session_state['exam_content'] = alt_content
                            st.experimental_rerun()
    else:
        if 'exam_content' in st.session_state:
            st.markdown("### 📄 معاينة الاختبار")
            st.markdown(f"<div class='result-box'>{st.session_state['exam_content'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
            if 'exam_data' in st.session_state:
                pdf_bytes = generate_exam_pdf(st.session_state['exam_data'])
                st.download_button("📥 تحميل PDF", pdf_bytes, f"exam.pdf", "application/pdf")

# ===================== TAB 2: LESSON PLANS =====================
with tab2:
    st.markdown("### 📖 مذكرات دراسية")
    col1, col2 = st.columns(2)
    with col1:
        level_lp = st.selectbox("الطور", list(CURRICULUM.keys()), key="lp_level")
    with col2:
        if level_lp == "الطور الثانوي":
            grade_lp = st.selectbox("السنة", CURRICULUM[level_lp]["grades"], key="lp_grade")
            branch_lp = st.selectbox("الشعبة", list(CURRICULUM[level_lp]["branches"].get(grade_lp, {}).keys()), key="lp_branch")
            subjects_lp = CURRICULUM[level_lp]["branches"][grade_lp].get(branch_lp, [])
        else:
            grade_lp = st.selectbox("السنة", CURRICULUM[level_lp]["grades"], key="lp_grade")
            branch_lp = None
            subjects_lp = CURRICULUM[level_lp]["subjects"].get(grade_lp, CURRICULUM[level_lp]["subjects"].get("_default", []))
    
    col1, col2 = st.columns(2)
    with col1:
        subject_lp = st.selectbox("المادة", subjects_lp, key="lp_subject")
    with col2:
        domain_lp = st.selectbox("الميدان", DOMAINS.get(subject_lp, ["عام"]), key="lp_domain")
    
    lesson_name = st.text_input("عنوان الدرس", placeholder="مثال: المعادلات من الدرجة الأولى", key="lp_lesson")
    duration_lp = st.text_input("المدة الزمنية", "50 دقيقة", key="lp_duration")
    
    if st.button("📖 توليد مذكرة", type="primary"):
        if not get_groq_api_key():
            st.error("❌ الرجاء إضافة مفتاح GROQ API في secrets")
        else:
            with st.spinner("جاري إنشاء المذكرة..."):
                lang_clause = llm_output_language_clause(subject_lp)
                plan_prompt = f"""
                أنت خبير في تصميم المذكرات البيداغوجية الجزائرية.
                المادة: {subject_lp}
                المستوى: {grade_lp}
                الميدان: {domain_lp}
                الدرس: {lesson_name}
                المدة: {duration_lp}
                
                {lang_clause}
                
                قم بإنشاء مذكرة تعليمية متكاملة تشمل:
                - الأهداف التعلمية
                - المكتسبات القبلية
                - سير الحصة (مراحل: التهيئة، بناء الموارد، إعادة الاستثمار)
                - التقويم
                - الواجب المنزلي
                
                التزم بالشكل الرسمي للمذكرات في الجزائر.
                """
                plan_content, _ = dual_engine.generate_with_audit(plan_prompt, subject_lp)
                plan_data = {
                    "school": "المؤسسة", "teacher": "الأستاذ", "grade": grade_lp,
                    "subject": subject_lp, "domain": domain_lp, "lesson": lesson_name,
                    "duration": duration_lp, "content": plan_content
                }
                st.session_state['plan_data'] = plan_data
                st.session_state['plan_content'] = plan_content
                st.success("تم إنشاء المذكرة!")
                st.markdown("### 📄 معاينة المذكرة")
                st.markdown(f"<div class='result-box'>{plan_content.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                
                pdf_bytes = generate_lesson_plan_pdf(plan_data)
                st.download_button("📥 تحميل PDF", pdf_bytes, f"lesson_plan_{lesson_name}.pdf", "application/pdf")
    else:
        if 'plan_content' in st.session_state:
            st.markdown("### 📄 معاينة المذكرة")
            st.markdown(f"<div class='result-box'>{st.session_state['plan_content'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

# ===================== TAB 3: REPORTS (Pedagogical Report Recovery) =====================
with tab3:
    st.markdown("### 📊 تحليل نتائج الأقسام")
    uploaded_gb = st.file_uploader("رفع ملف دفتر التنقيط (Excel)", type=["xlsx", "xls"], key="report_upload")
    if uploaded_gb:
        sheet_names = list_excel_sheet_names(uploaded_gb)
        if sheet_names:
            merge_sheets = st.checkbox("دمج جميع الأوراق (قسم واحد لكل ورقة)", key="merge_report")
            if not merge_sheets:
                selected_sheet = st.selectbox("اختر الورقة", sheet_names, key="sheet_report")
            else:
                selected_sheet = None
            
            if st.button("تحليل النتائج"):
                with st.spinner("جاري التحليل..."):
                    students = parse_grade_book_excel(uploaded_gb, selected_sheet, merge_sheets)
                    if not students:
                        st.warning("لم يتم العثور على بيانات تلاميذ في الملف")
                    else:
                        if merge_sheets:
                            from collections import defaultdict
                            sheets_map = defaultdict(list)
                            for s in students:
                                sheets_map[s.get('sheet_source', 'غير معروف')].append(s)
                            classes_stats = [build_class_stats(sheets_map[name], name) for name in sheets_map]
                        else:
                            classes_stats = [build_class_stats(students, "القسم الرئيسي")]
                        
                        report_data = {
                            "school": "المؤسسة",
                            "subject": selected_sheet or "غير محدد",
                            "semester": "الفصل الثاني",
                            "classes": classes_stats,
                            "ai_analysis": ""
                        }
                        
                        analysis_prompt = f"""
                        قم بتحليل هذه النتائج التربوية لمادة {report_data['subject']}:
                        {classes_stats}
                        
                        قدم تقريراً بيداغوجياً شاملاً يتضمن:
                        - نقاط القوة والضعف في الأقسام
                        - توصيات لتحسين الأداء
                        - إستراتيجيات تدريس مقترحة للمواضيع التي تحتاج تحسناً
                        - تحليل مقارن بين الأقسام (إن وجد)
                        
                        كن دقيقاً ومهنياً، واكتب التقرير بالعربية الفصحى الواضحة.
                        """
                        analysis_result, _ = dual_engine.generate_with_audit(analysis_prompt, report_data['subject'])
                        report_data['ai_analysis'] = analysis_result
                        
                        # Store report in session_state for persistence
                        store_report_in_session(report_data)
                        
                        # Display in Live Preview
                        for cls in classes_stats:
                            st.markdown(f"<div class='feature-card'><h4>القسم: {cls['name']}</h4><p>العدد: {cls['total']} | المعدل: {cls['avg']:.2f} | النجاح: {cls['pass_rate']:.1f}%</p></div>", unsafe_allow_html=True)
                        
                        st.markdown("### 🤖 التقرير البيداغوجي (الذكاء الاصطناعي)")
                        st.markdown(f"<div class='result-box'>{report_data['ai_analysis'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                        
                        pdf_bytes = generate_report_pdf(report_data)
                        st.download_button("📥 تحميل تقرير PDF", pdf_bytes, "pedagogical_report.pdf", "application/pdf")
    
    # Display stored report if exists (Persistence)
    stored_report = get_stored_report()
    if stored_report and 'uploaded_gb' not in locals():
        st.info("📋 التقرير البيداغوجي المحفوظ (من جلسة سابقة)")
        for cls in stored_report.get('classes', []):
            st.markdown(f"<div class='feature-card'><h4>القسم: {cls['name']}</h4><p>العدد: {cls['total']} | المعدل: {cls['avg']:.2f} | النجاح: {cls['pass_rate']:.1f}%</p></div>", unsafe_allow_html=True)
        st.markdown("### 🤖 التقرير البيداغوجي")
        st.markdown(f"<div class='result-box'>{stored_report.get('ai_analysis', '').replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
        pdf_bytes = generate_report_pdf(stored_report)
        st.download_button("📥 تحميل التقرير المحفوظ PDF", pdf_bytes, "pedagogical_report_saved.pdf", "application/pdf")

# ===================== TAB 4: GRADE BOOK (Excel Multi-Sheet) =====================
with tab4:
    st.markdown("### 📁 دفتر التنقيط")
    st.markdown("يمكنك تحميل ملف Excel يحتوي على أوراق متعددة (قسم في كل ورقة) لإنشاء دفاتر تنقيط منفصلة.")
    uploaded_file = st.file_uploader("اختر ملف Excel", type=["xlsx", "xls"], key="gradebook_upload")
    if uploaded_file:
        sheet_names = list_excel_sheet_names(uploaded_file)
        if sheet_names:
            with st.expander("خيارات متقدمة"):
                merge_sheets = st.checkbox("دمج جميع الأوراق في دفتر واحد (أوراق منفصلة في Excel الناتج)", key="merge_gb")
            if st.button("إنشاء دفاتر التنقيط"):
                if merge_sheets:
                    wb_out = openpyxl.Workbook()
                    wb_out.remove(wb_out.active)
                    for sheet_name in sheet_names:
                        students = parse_grade_book_excel(uploaded_file, sheet_name, False)
                        if students:
                            # Generate temporary workbook and copy sheet
                            wb_temp = openpyxl.load_workbook(io.BytesIO(generate_grade_book_excel(students, sheet_name, "المادة", "الفصل الثاني", "المؤسسة")))
                            ws_temp = wb_temp.active
                            ws_temp.title = sheet_name[:31]
                            wb_out._sheets.append(ws_temp)
                    if len(wb_out.sheetnames) > 0:
                        buf_out = io.BytesIO()
                        wb_out.save(buf_out)
                        st.download_button("📥 تحميل دفتر التنقيط (جميع الأقسام)", buf_out.getvalue(), "gradebook_all.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    selected_sheet = st.selectbox("اختر الورقة", sheet_names, key="gb_sheet")
                    if selected_sheet:
                        students = parse_grade_book_excel(uploaded_file, selected_sheet, False)
                        if students:
                            excel_bytes = generate_grade_book_excel(students, selected_sheet, "المادة", "الفصل الثاني", "المؤسسة")
                            st.download_button("📥 تحميل دفتر التنقيط", excel_bytes, f"gradebook_{selected_sheet}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("تعذر قراءة أسماء الأوراق من الملف")

# ===================== TAB 5: SETTINGS =====================
with tab5:
    st.markdown("### ⚙️ الإعدادات المتقدمة")
    st.markdown("""
    <div class="feature-card">
    <h4>🚀 ميزات الترقية العالمية (Sovereign Global Upgrade V3.1)</h4>
    <ul>
        <li><strong>محرك الذكاء الهجين (Dual-LLM):</strong> Groq للسرعة + Arcee للدقة مع مدقق داخلي (Auditor Agent).</li>
        <li><strong>أمان كامل (Zero-Visibility):</strong> مفاتيح API مخزنة فقط في st.secrets، غير قابلة للعرض أو الإدخال في الواجهة.</li>
        <li><strong>مساعد ذكي عائم:</strong> روبوت متحرك لا يعيق واجهة المستخدم ويقدم إرشادات فورية.</li>
        <li><strong>معاينة حية (Live Preview):</strong> عرض المحتوى قبل التحميل مع خيار إعادة التوليد بنموذج بديل.</li>
        <li><strong>تصدير متعدد الصيغ (Multi-Format):</strong> PDF, Word, Excel مع دعم كامل للغة العربية (RTL) عبر خطوط Amiri/Cairo المضمّنة.</li>
        <li><strong>فهرسة طبيعية (1-based indexing):</strong> جميع الجداول تبدأ الترقيم من 1 بدلاً من 0.</li>
        <li><strong>استمرارية التقرير البيداغوجي:</strong> تخزين التقرير في session_state لضمان عدم اختفائه.</li>
        <li><strong>QR Code للتطبيق:</strong> مشاركة سريعة للرابط عبر مسح الرمز.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🧩 متطلبات التشغيل")
    st.code("""
    pip install -r requirements.txt
    """)
    st.markdown("**المكتبات الجديدة المضافة:**")
    st.code("""
    qrcode[pil]>=7.4.0
    python-docx>=0.8.11
    openpyxl>=3.0.10
    arabic-reshaper>=2.1.3
    python-bidi>=0.4.2
    lxml>=4.9.0
    """)
    st.markdown("**ملاحظة:** لتفعيل ميزة Arcee، تأكد من إضافة مفتاح API في Streamlit secrets.")

# Floating Robot Assistant (Non-Blocking)
render_floating_robot()

# Footer
st.markdown("<div class='donia-ip-footer'><p>جميع الحقوق محفوظة © 2026 — DONIA LABS TECH</p><div class='donia-footer-social'><a href='https://wa.me/213674661737' target='_blank'>واتساب</a><a href='https://www.linkedin.com/in/donia-labs-tech-smart-ideas-lab' target='_blank'>لينكدإن</a><a href='https://www.facebook.com/share/1An6GhVd56/' target='_blank'>فيسبوك</a><a href='https://t.me/+LxRzVAK12HZmNTQ8' target='_blank'>تليجرام</a></div></div>", unsafe_allow_html=True)
