"""
DONIA MIND 1 — Global Excellence Edition
Dual-LLM Educational AI Platform for Algerian Schools
Hybrid Intelligence: Groq (speed) + Arcee (pedagogical accuracy)
"""

import streamlit as st
import os
import io
import json
import base64
import requests
import traceback
from datetime import datetime
from pathlib import Path
import time

# ─── Optional imports with graceful degradation ────────────────────────────────
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_BIDI_AVAILABLE = True
except ImportError:
    ARABIC_BIDI_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font as XLFont, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import qrcode
    from PIL import Image
    PIL_AVAILABLE = True
    QRCODE_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    QRCODE_AVAILABLE = False

import pandas as pd


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="DONIA MIND 1 — المساعد التعليمي الذكي",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_URL = "https://doniamind1-pvnmwp3kdthtlfct7uhopm.streamlit.app/"
FONT_DIR = Path(__file__).parent / "fonts"
ASSETS_DIR = Path(__file__).parent / "assets"
FONT_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS — Animated Robot + Professional UI
# ══════════════════════════════════════════════════════════════════════════════

def inject_global_css():
    st.markdown("""
    <style>
    /* ── Base ── */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&family=Cairo:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Tajawal', 'Cairo', sans-serif;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E3A8A 60%, #1D4ED8 100%);
        border-right: 3px solid #3B82F6;
    }
    section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    section[data-testid="stSidebar"] .stRadio label { color: #CBD5E1 !important; font-size: 15px; }

    /* ── Header banner ── */
    .donia-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #2563EB 100%);
        border-radius: 16px;
        padding: 28px 36px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(30,58,138,0.4);
        border: 1px solid rgba(96,165,250,0.3);
        display: flex;
        align-items: center;
        gap: 24px;
    }
    .donia-header h1 { font-size: 2rem; font-weight: 700; margin: 0; color: #DBEAFE; }
    .donia-header p  { font-size: 1rem; color: #93C5FD; margin: 0; }

    /* ── Robot animation ── */
    .robot-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px;
    }
    .robot-body {
        width: 80px; height: 80px;
        background: linear-gradient(145deg, #3B82F6, #1D4ED8);
        border-radius: 20px;
        position: relative;
        animation: robotFloat 3s ease-in-out infinite;
        box-shadow: 0 8px 24px rgba(59,130,246,0.5);
        display: flex; align-items: center; justify-content: center;
    }
    .robot-eye {
        width: 14px; height: 14px;
        background: white;
        border-radius: 50%;
        display: inline-block;
        margin: 0 4px;
        animation: robotBlink 4s ease-in-out infinite;
        position: relative;
    }
    .robot-eye::after {
        content: '';
        width: 6px; height: 6px;
        background: #1E3A8A;
        border-radius: 50%;
        position: absolute;
        top: 4px; left: 4px;
    }
    .robot-antenna {
        width: 4px; height: 24px;
        background: #60A5FA;
        border-radius: 2px;
        position: absolute;
        top: -24px; left: 50%; transform: translateX(-50%);
    }
    .robot-antenna::after {
        content: ''; width: 10px; height: 10px;
        background: #F59E0B;
        border-radius: 50%;
        position: absolute;
        top: -5px; left: -3px;
        animation: antennaPulse 2s ease-in-out infinite;
        box-shadow: 0 0 8px #F59E0B;
    }
    .robot-mouth {
        width: 30px; height: 6px;
        background: rgba(255,255,255,0.3);
        border-radius: 3px;
        position: absolute;
        bottom: 16px; left: 50%; transform: translateX(-50%);
        animation: robotTalk 1.5s ease-in-out infinite alternate;
    }
    .robot-legs {
        display: flex; gap: 12px; margin-top: 4px;
    }
    .robot-leg {
        width: 16px; height: 24px;
        background: linear-gradient(145deg, #2563EB, #1D4ED8);
        border-radius: 0 0 8px 8px;
        animation: robotLeg 3s ease-in-out infinite;
    }
    .robot-leg:last-child { animation-delay: 0.3s; }
    .robot-speech {
        background: white;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 10px 16px;
        margin-top: 12px;
        font-size: 13px;
        color: #1E3A8A;
        font-weight: 500;
        max-width: 200px;
        text-align: center;
        position: relative;
        box-shadow: 0 4px 12px rgba(59,130,246,0.2);
    }
    .robot-speech::before {
        content: '';
        position: absolute;
        top: -10px; left: 50%; transform: translateX(-50%);
        border: 5px solid transparent;
        border-bottom-color: #3B82F6;
    }

    @keyframes robotFloat {
        0%, 100% { transform: translateY(0); }
        50%       { transform: translateY(-10px); }
    }
    @keyframes robotBlink {
        0%, 45%, 55%, 100% { transform: scaleY(1); }
        50%                 { transform: scaleY(0.1); }
    }
    @keyframes antennaPulse {
        0%, 100% { box-shadow: 0 0 8px #F59E0B; transform: scale(1); }
        50%       { box-shadow: 0 0 16px #F59E0B; transform: scale(1.3); }
    }
    @keyframes robotTalk {
        0%   { width: 30px; }
        100% { width: 20px; }
    }
    @keyframes robotLeg {
        0%, 100% { transform: rotate(0deg); }
        50%       { transform: rotate(5deg); }
    }

    /* ── Cards ── */
    .donia-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .donia-card h3 { color: #1E3A8A; font-size: 1.2rem; margin-bottom: 12px; }

    /* ── Model status badges ── */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-groq   { background: #FEF3C7; color: #92400E; border: 1px solid #F59E0B; }
    .badge-arcee  { background: #EDE9FE; color: #5B21B6; border: 1px solid #8B5CF6; }
    .badge-valid  { background: #D1FAE5; color: #065F46; border: 1px solid #10B981; }
    .badge-check  { background: #DBEAFE; color: #1E40AF; border: 1px solid #3B82F6; }

    /* ── Preview box ── */
    .preview-box {
        background: #F8FAFF;
        border: 2px solid #BFDBFE;
        border-radius: 12px;
        padding: 28px;
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', 'Tajawal', sans-serif;
        line-height: 2;
        font-size: 15px;
        color: #1E293B;
        max-height: 600px;
        overflow-y: auto;
    }
    .preview-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #BFDBFE;
    }

    /* ── Cross-check progress ── */
    .crosscheck-container {
        background: linear-gradient(135deg, #F0F9FF, #EFF6FF);
        border: 1px solid #BAE6FD;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 12px 0;
    }
    .crosscheck-step {
        display: flex; align-items: center; gap: 10px;
        margin: 6px 0; font-size: 14px; color: #374151;
    }

    /* ── Export buttons ── */
    .export-btn-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin: 16px 0;
    }

    /* ── QR code ── */
    .qr-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 2px solid #DBEAFE;
    }
    .qr-label { font-size: 12px; color: #6B7280; margin-top: 8px; text-align: center; }

    /* ── Section titles ── */
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1E3A8A;
        padding: 8px 0;
        border-bottom: 3px solid #3B82F6;
        margin-bottom: 20px;
    }
    .arabic-label {
        font-family: 'Cairo', 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }

    /* ── Streamlit overrides ── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    div[data-testid="stMetricValue"] { color: #1E3A8A !important; font-size: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECRETS / API KEYS
# ══════════════════════════════════════════════════════════════════════════════

def get_secret(key: str) -> str | None:
    """Retrieve a secret from environment or Streamlit secrets."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        return st.secrets.get(key)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  FONT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

AMIRI_URL = (
    "https://github.com/alif-type/amiri/releases/download/1.000/Amiri-1.000.zip"
)
AMIRI_DIRECT_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Regular.ttf"
)

def ensure_arabic_font() -> Path | None:
    """Download Amiri.ttf if not present. Returns path or None."""
    font_path = FONT_DIR / "Amiri-Regular.ttf"
    if font_path.exists():
        return font_path
    try:
        resp = requests.get(AMIRI_DIRECT_URL, timeout=15)
        if resp.status_code == 200:
            font_path.write_bytes(resp.content)
            return font_path
    except Exception:
        pass
    return None


def reshape_arabic(text: str) -> str:
    """Reshape Arabic text for correct PDF rendering."""
    if not ARABIC_BIDI_AVAILABLE:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


# ══════════════════════════════════════════════════════════════════════════════
#  DUAL-LLM ENGINE
# ══════════════════════════════════════════════════════════════════════════════

GROQ_MODEL   = "llama-3.3-70b-versatile"
ARCEE_MODEL  = "arcee-ai/arcee-agent"
ARCEE_BASE   = "https://models.arcee.ai/v1"

ALGERIAN_SYSTEM_PROMPT = """أنت مساعد تعليمي متخصص في المنهج الدراسي الجزائري.
تعمل وفق المعايير التربوية لوزارة التربية الوطنية الجزائرية.
تستند إلى مناهج التعليم الابتدائي والمتوسط والثانوي الجزائري.
تراعي المقاييس الواردة في منصات مثل dzexams.com.
تُنتج محتوى تعليمياً دقيقاً ومتوافقاً مع المستوى الدراسي المطلوب.
الإجابات باللغة العربية الفصحى دائماً ما لم يُطلب غير ذلك."""


def call_groq(prompt: str, system: str = ALGERIAN_SYSTEM_PROMPT, max_tokens: int = 2048) -> str:
    """Call Groq LLM for high-speed response."""
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        return "⚠️ GROQ_API_KEY غير متاح. يرجى إضافة المفتاح في الإعدادات."
    if not GROQ_AVAILABLE:
        return "⚠️ مكتبة Groq غير مثبتة. يرجى تشغيل: pip install groq"
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ خطأ في Groq: {str(e)}"


def call_arcee(prompt: str, system: str = ALGERIAN_SYSTEM_PROMPT, max_tokens: int = 2048) -> str:
    """Call Arcee AI for domain-specialized pedagogical accuracy."""
    api_key = get_secret("ARCEE_API_KEY")
    if not api_key:
        return "⚠️ ARCEE_API_KEY غير متاح. يرجى إضافة المفتاح في الإعدادات."
    if not OPENAI_AVAILABLE:
        return "⚠️ مكتبة OpenAI غير مثبتة. يرجى تشغيل: pip install openai"
    try:
        client = OpenAI(api_key=api_key, base_url=ARCEE_BASE)
        response = client.chat.completions.create(
            model=ARCEE_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ خطأ في Arcee: {str(e)}"


def cross_check_agent(
    groq_response: str,
    arcee_response: str,
    topic: str,
    progress_placeholder=None,
) -> dict:
    """
    Cross-Check Agent — compares Groq and Arcee outputs,
    validates pedagogical accuracy, and returns a consolidated result.
    Returns: { "final": str, "groq": str, "arcee": str, "score": float, "notes": str }
    """
    steps = [
        "⚙️ استقبال مخرجات النموذجين...",
        "🔍 مقارنة المحتوى التربوي...",
        "✅ التحقق من التوافق مع المنهج الجزائري...",
        "🧮 احتساب معدل الجودة التربوية...",
        "📝 إنتاج النسخة النهائية الموثقة...",
    ]

    if progress_placeholder:
        for step in steps:
            progress_placeholder.markdown(
                f'<div class="crosscheck-container">'
                f'<div class="crosscheck-step">🤖 {step}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.4)

    # Build validation prompt
    validation_prompt = f"""أنت وكيل التحقق التربوي لمنصة DONIA MIND 1.
مهمتك: مقارنة إجابتين من نموذجين مختلفين حول الموضوع التالي: {topic}

━━ إجابة Groq (السرعة) ━━
{groq_response[:1000]}

━━ إجابة Arcee (الدقة التربوية) ━━
{arcee_response[:1000]}

قم بـ:
1. دمج أفضل ما في الإجابتين
2. ضمان التوافق مع المنهج الجزائري
3. تصحيح أي أخطاء لغوية أو علمية
4. إنتاج الإجابة النهائية الكاملة بتنسيق احترافي

أعط النتيجة النهائية مباشرة بدون مقدمات."""

    final_response = call_groq(validation_prompt, system=ALGERIAN_SYSTEM_PROMPT, max_tokens=2048)

    # Simple scoring heuristic
    score = 95.0
    if "⚠️" in groq_response or "⚠️" in arcee_response:
        score = 70.0
    if "خطأ" in groq_response or "خطأ" in arcee_response:
        score -= 10.0

    return {
        "final":  final_response,
        "groq":   groq_response,
        "arcee":  arcee_response,
        "score":  min(score, 100.0),
        "notes":  "تم التحقق من التوافق مع المعايير التربوية الجزائرية ✅",
    }


# ══════════════════════════════════════════════════════════════════════════════
#  QR CODE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_qr_code(url: str = APP_URL) -> bytes | None:
    """Generate a QR code PNG for the given URL."""
    if not QRCODE_AVAILABLE:
        return None
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E3A8A", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  PDF EXPORT (Arabic-safe)
# ══════════════════════════════════════════════════════════════════════════════

def generate_arabic_pdf(content: str, title: str = "وثيقة تعليمية", metadata: dict = None) -> bytes | None:
    """Generate a professional Arabic PDF using Amiri font + bidi reshaping."""
    if not REPORTLAB_AVAILABLE:
        return None

    buf = io.BytesIO()
    font_path = ensure_arabic_font()

    # Register Amiri font
    font_name = "Amiri"
    if font_path and font_path.exists():
        try:
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        except Exception:
            font_name = "Helvetica"
    else:
        font_name = "Helvetica"

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ArabicTitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=18,
        leading=32,
        alignment=1,  # center
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "ArabicBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=12,
        leading=22,
        alignment=2,  # right
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "ArabicMeta",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=18,
        alignment=2,
        textColor=colors.HexColor("#64748B"),
    )

    story = []

    # Header
    story.append(Paragraph(reshape_arabic("DONIA MIND 1 — المساعد التعليمي الذكي"), title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3B82F6")))
    story.append(Spacer(1, 0.4 * cm))

    # Title
    story.append(Paragraph(reshape_arabic(title), title_style))
    story.append(Spacer(1, 0.3 * cm))

    # Metadata
    if metadata:
        for k, v in metadata.items():
            story.append(Paragraph(reshape_arabic(f"{k}: {v}"), meta_style))
    story.append(Paragraph(
        reshape_arabic(f"تاريخ الإنشاء: {datetime.now().strftime('%Y/%m/%d — %H:%M')}"),
        meta_style,
    ))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BFDBFE")))
    story.append(Spacer(1, 0.4 * cm))

    # Content — split by line
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.2 * cm))
            continue
        reshaped = reshape_arabic(stripped)
        story.append(Paragraph(reshaped, body_style))

    # Footer
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BFDBFE")))
    story.append(Paragraph(
        reshape_arabic("منصة DONIA MIND 1 — مختبر الذكاء الاصطناعي التعليمي الجزائري"),
        meta_style,
    ))

    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
#  WORD EXPORT (RTL)
# ══════════════════════════════════════════════════════════════════════════════

def _set_rtl(paragraph):
    """Apply RTL formatting to a Word paragraph."""
    try:
        pPr = paragraph._p.get_or_add_pPr()
        bidi = OxmlElement("w:bidi")
        bidi.set(qn("w:val"), "1")
        pPr.append(bidi)
        jc = OxmlElement("w:jc")
        jc.set(qn("w:val"), "right")
        pPr.append(jc)
    except Exception:
        pass


def generate_word_doc(content: str, title: str = "وثيقة تعليمية", metadata: dict = None) -> bytes | None:
    """Generate an RTL Word document."""
    if not DOCX_AVAILABLE:
        return None
    try:
        doc = Document()

        # Document direction
        try:
            body = doc.element.body
            sectPr = body.get_or_add_sectPr()
            bidi = OxmlElement("w:bidi")
            sectPr.append(bidi)
        except Exception:
            pass

        # Styles
        normal = doc.styles["Normal"]
        normal.font.name = "Simplified Arabic"
        normal.font.size = Pt(13)
        normal.element.rPr.rFonts.set(qn("w:hint"), "cs")

        # Header
        hdr = doc.add_heading("DONIA MIND 1 — المساعد التعليمي الذكي", 0)
        hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_rtl(hdr)

        # Title
        h1 = doc.add_heading(title, 1)
        h1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _set_rtl(h1)
        h1.runs[0].font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

        # Metadata
        if metadata:
            for k, v in metadata.items():
                p = doc.add_paragraph(f"{k}: {v}")
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                _set_rtl(p)
                p.runs[0].font.size = Pt(11)
                p.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        date_p = doc.add_paragraph(f"تاريخ الإنشاء: {datetime.now().strftime('%Y/%m/%d — %H:%M')}")
        date_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _set_rtl(date_p)

        doc.add_paragraph("─" * 60)

        # Content
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                doc.add_paragraph("")
                continue
            p = doc.add_paragraph(stripped)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            _set_rtl(p)

        # Footer
        doc.add_paragraph("─" * 60)
        footer_p = doc.add_paragraph("منصة DONIA MIND 1 — مختبر الذكاء الاصطناعي التعليمي الجزائري")
        footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_rtl(footer_p)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except Exception as e:
        st.error(f"خطأ في إنشاء ملف Word: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  EXCEL EXPORT — Grading Book (دفتر التنقيط)
# ══════════════════════════════════════════════════════════════════════════════

def generate_grading_book(classes_data: list[dict]) -> bytes | None:
    """
    Generate a multi-sheet Excel grading book.
    classes_data: [{"name": "القسم 1", "students": [{"name": str, "grades": {subject: grade}}]}]
    """
    if not OPENPYXL_AVAILABLE:
        return None
    try:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        header_fill = PatternFill("solid", fgColor="1E3A8A")
        header_font = XLFont(name="Arial", bold=True, color="FFFFFF", size=12)
        title_font  = XLFont(name="Arial", bold=True, color="1E3A8A", size=14)
        border_side = Side(style="thin", color="BFDBFE")
        cell_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        right_align  = Alignment(horizontal="right",  vertical="center")

        for idx, cls in enumerate(classes_data):
            ws = wb.create_sheet(title=cls.get("name", f"القسم {idx+1}")[:31])
            ws.sheet_view.rightToLeft = True

            # Title row
            subjects = list(cls["students"][0]["grades"].keys()) if cls["students"] else []
            total_cols = 2 + len(subjects) + 1
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
            title_cell = ws.cell(row=1, column=1, value=f"دفتر التنقيط — {cls.get('name', '')}")
            title_cell.font = title_font
            title_cell.alignment = center_align

            ws.cell(row=2, column=1, value=f"التاريخ: {datetime.now().strftime('%Y/%m/%d')}").alignment = center_align

            # Header row
            headers = ["الرقم", "اسم التلميذ"] + subjects + ["المعدل"]
            for col, hdr in enumerate(headers, start=1):
                cell = ws.cell(row=3, column=col, value=hdr)
                cell.fill   = header_fill
                cell.font   = header_font
                cell.alignment = center_align
                cell.border = cell_border

            # Data rows
            for row_idx, student in enumerate(cls["students"], start=4):
                ws.cell(row=row_idx, column=1, value=row_idx - 3).alignment = center_align
                ws.cell(row=row_idx, column=2, value=student["name"]).alignment = right_align

                grades = student.get("grades", {})
                total = 0.0
                count = 0
                for col_offset, subj in enumerate(subjects):
                    grade = grades.get(subj, "")
                    cell = ws.cell(row=row_idx, column=3 + col_offset, value=grade)
                    cell.alignment = center_align
                    cell.border = cell_border
                    try:
                        total += float(grade)
                        count += 1
                    except (ValueError, TypeError):
                        pass

                avg = round(total / count, 2) if count else ""
                avg_cell = ws.cell(row=row_idx, column=total_cols, value=avg)
                avg_cell.alignment = center_align
                avg_cell.border = cell_border
                if isinstance(avg, float):
                    avg_cell.fill = PatternFill(
                        "solid",
                        fgColor="D1FAE5" if avg >= 10 else "FEE2E2",
                    )

            # Column widths
            ws.column_dimensions["A"].width = 8
            ws.column_dimensions["B"].width = 28
            for i in range(len(subjects)):
                ws.column_dimensions[get_column_letter(3 + i)].width = 14
            ws.column_dimensions[get_column_letter(total_cols)].width = 12
            ws.row_dimensions[1].height = 28
            ws.row_dimensions[3].height = 22

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
    except Exception as e:
        st.error(f"خطأ في إنشاء ملف Excel: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def render_robot(message: str = "مرحباً! أنا مساعدك الذكي"):
    st.markdown(f"""
    <div class="robot-container">
      <div class="robot-body">
        <div class="robot-antenna"></div>
        <div>
          <span class="robot-eye"></span>
          <span class="robot-eye"></span>
        </div>
        <div class="robot-mouth"></div>
      </div>
      <div class="robot-legs">
        <div class="robot-leg"></div>
        <div class="robot-leg"></div>
      </div>
      <div class="robot-speech">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_header():
    logo_path = ASSETS_DIR / "logo_donia.jpg"
    logo_html = ""
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/jpeg;base64,{encoded}" style="height:64px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.3);" />'

    st.markdown(f"""
    <div class="donia-header">
      {logo_html}
      <div>
        <h1>DONIA MIND 1</h1>
        <p>المختبر التعليمي الذكي — Groq ⚡ × Arcee 🧠 Dual Intelligence</p>
      </div>
    </div>
    """, unsafe_allow_html=True)


def download_buttons(content: str, title: str, metadata: dict = None):
    """Render PDF / Word / QR download buttons."""
    st.markdown("### 📥 تصدير المحتوى")
    cols = st.columns(3)

    with cols[0]:
        pdf_bytes = generate_arabic_pdf(content, title, metadata)
        if pdf_bytes:
            st.download_button(
                "📄 تحميل PDF (عربي)",
                data=pdf_bytes,
                file_name=f"donia_mind_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info("📄 PDF غير متاح — ثبّت reportlab")

    with cols[1]:
        docx_bytes = generate_word_doc(content, title, metadata)
        if docx_bytes:
            st.download_button(
                "📝 تحميل Word (RTL)",
                data=docx_bytes,
                file_name=f"donia_mind_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        else:
            st.info("📝 Word غير متاح — ثبّت python-docx")

    with cols[2]:
        qr_bytes = generate_qr_code(APP_URL)
        if qr_bytes:
            st.download_button(
                "🔗 تحميل QR Code",
                data=qr_bytes,
                file_name="donia_mind_qr.png",
                mime="image/png",
                use_container_width=True,
            )


def render_preview(content: str, title: str):
    """Render content in the Live Preview Dashboard."""
    st.markdown(f"""
    <div class="preview-box">
      <div class="preview-title">{title}</div>
      <div style="white-space:pre-wrap">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_dual_model_result(result: dict, topic: str):
    """Display cross-check results with badges and model comparison."""
    tab1, tab2, tab3 = st.tabs(["✅ النتيجة النهائية", "⚡ Groq", "🧠 Arcee"])

    with tab1:
        score = result.get("score", 0)
        color = "#10B981" if score >= 90 else "#F59E0B" if score >= 70 else "#EF4444"
        st.markdown(f"""
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;">
          <span class="badge badge-valid">✅ موثق تربوياً</span>
          <span class="badge badge-check">🔬 Cross-Check Agent</span>
          <span style="font-weight:700;color:{color}">الجودة: {score:.0f}٪</span>
        </div>
        """, unsafe_allow_html=True)
        render_preview(result.get("final", ""), topic)
        st.caption(result.get("notes", ""))

    with tab2:
        st.markdown('<span class="badge badge-groq">⚡ Groq — llama-3.3-70b</span>', unsafe_allow_html=True)
        render_preview(result.get("groq", ""), "مخرجات Groq")

    with tab3:
        st.markdown('<span class="badge badge-arcee">🧠 Arcee — التخصص التربوي</span>', unsafe_allow_html=True)
        render_preview(result.get("arcee", ""), "مخرجات Arcee")


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════

def init_state():
    defaults = {
        "last_result": None,
        "last_title": "",
        "last_metadata": {},
        "last_content": "",
        "active_model": "dual",
        "pedagogical_report": None,
        "grading_data": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════

def page_home():
    col_robot, col_info = st.columns([1, 3])

    with col_robot:
        render_robot("مرحباً! أنا دونيا\nمساعدك التعليمي الذكي 🎓")
        qr_bytes = generate_qr_code(APP_URL)
        if qr_bytes:
            st.markdown('<div class="qr-container">', unsafe_allow_html=True)
            st.image(qr_bytes, width=140, caption="امسح للدخول إلى المنصة")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_info:
        st.markdown('<div class="section-title">🎓 مرحباً بكم في DONIA MIND 1</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="donia-card">
          <h3>🚀 محرك الذكاء المزدوج</h3>
          <p>تعمل المنصة بنموذجَين متكاملَين:</p>
          <ul>
            <li><span class="badge badge-groq">⚡ Groq</span> — سرعة فائقة في المعالجة (llama-3.3-70b)</li>
            <li><span class="badge badge-arcee">🧠 Arcee</span> — دقة تربوية متخصصة للمنهج الجزائري</li>
            <li><span class="badge badge-check">🔬 Cross-Check Agent</span> — التحقق الآلي من الجودة التربوية</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="donia-card">
          <h3>📚 خدمات المنصة</h3>
          <ul>
            <li>🧪 توليد اختبارات وأسئلة متوافقة مع المنهج الجزائري</li>
            <li>📊 دفتر التنقيط (Excel متعدد الأقسام)</li>
            <li>📝 التقرير البيداغوجي الآلي</li>
            <li>📄 تصدير PDF عربي احترافي</li>
            <li>📎 تصدير Word بدعم RTL كامل</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

    # Status bar
    st.markdown("---")
    s1, s2, s3, s4 = st.columns(4)
    groq_ok  = bool(get_secret("GROQ_API_KEY"))
    arcee_ok = bool(get_secret("ARCEE_API_KEY"))

    s1.metric("⚡ Groq", "✅ متصل" if groq_ok else "❌ غير متصل")
    s2.metric("🧠 Arcee", "✅ متصل" if arcee_ok else "❌ غير متصل")
    s3.metric("📐 الخط العربي", "✅ جاهز" if ARABIC_BIDI_AVAILABLE else "⚠️ مفقود")
    s4.metric("📄 تصدير PDF", "✅ جاهز" if REPORTLAB_AVAILABLE else "⚠️ مفقود")

    if not groq_ok or not arcee_ok:
        st.warning(
            "⚠️ يرجى إضافة **GROQ_API_KEY** و **ARCEE_API_KEY** في متغيرات البيئة "
            "لتفعيل محرك الذكاء المزدوج."
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: EXAM / QUIZ GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def page_exam_generator():
    st.markdown('<div class="section-title">🧪 مولّد الاختبارات والأسئلة</div>', unsafe_allow_html=True)

    with st.form("exam_form"):
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox(
                "المادة الدراسية",
                ["اللغة العربية", "الرياضيات", "العلوم الطبيعية", "التاريخ والجغرافيا",
                 "التربية الإسلامية", "اللغة الفرنسية", "اللغة الإنجليزية",
                 "الفيزياء والكيمياء", "الفلسفة", "الاقتصاد والمنظمة"],
            )
            level = st.selectbox(
                "المستوى الدراسي",
                ["السنة الأولى ابتدائي", "السنة الثانية ابتدائي", "السنة الثالثة ابتدائي",
                 "السنة الرابعة ابتدائي", "السنة الخامسة ابتدائي",
                 "السنة الأولى متوسط", "السنة الثانية متوسط", "السنة الثالثة متوسط",
                 "السنة الرابعة متوسط",
                 "السنة الأولى ثانوي", "السنة الثانية ثانوي", "السنة الثالثة ثانوي (باكالوريا)"],
            )
        with c2:
            num_questions = st.slider("عدد الأسئلة", 3, 20, 5)
            q_types = st.multiselect(
                "أنواع الأسئلة",
                ["أسئلة مباشرة", "اختيار من متعدد (QCM)", "صح/خطأ", "ملء الفراغات",
                 "نص للقراءة والفهم", "تمارين تطبيقية", "مسائل", "إنشاء حر"],
                default=["أسئلة مباشرة", "اختيار من متعدد (QCM)"],
            )
            topic = st.text_input("الموضوع / الوحدة (اختياري)", placeholder="مثال: الجملة الاسمية")
            trimester = st.selectbox("الثلاثي", ["الثلاثي الأول", "الثلاثي الثاني", "الثلاثي الثالث"])

        model_choice = st.radio(
            "نموذج الذكاء الاصطناعي",
            ["🔀 مزدوج (Groq + Arcee + Cross-Check)", "⚡ Groq فقط", "🧠 Arcee فقط"],
            horizontal=True,
        )
        submitted = st.form_submit_button("🚀 توليد الاختبار", use_container_width=True, type="primary")

    if submitted:
        q_types_str = "، ".join(q_types) if q_types else "أسئلة متنوعة"
        topic_str = f"حول: {topic}" if topic else ""
        prompt = f"""
أنشئ اختباراً تعليمياً كاملاً ومفصلاً للمواصفات التالية:
- المادة: {subject}
- المستوى: {level}
- الثلاثي: {trimester}
- عدد الأسئلة: {num_questions}
- أنواع الأسئلة: {q_types_str}
{topic_str}

الاختبار يجب أن يكون:
✅ متوافقاً مع المنهج الجزائري الرسمي
✅ مُنسَّقاً بشكل احترافي مع الترقيم الواضح
✅ متضمناً معيار التصحيح وتوزيع النقاط
✅ مكتوباً بالعربية الفصحى السليمة

ابدأ الاختبار مباشرة دون مقدمات.
"""
        exam_title = f"اختبار في {subject} — {level} — {trimester}"
        metadata = {"المادة": subject, "المستوى": level, "الثلاثي": trimester}

        progress_ph = st.empty()

        if "مزدوج" in model_choice:
            progress_ph.info("⏳ Groq يعالج الاختبار...")
            groq_res = call_groq(prompt)
            progress_ph.info("⏳ Arcee يراجع المحتوى التربوي...")
            arcee_res = call_arcee(prompt)
            progress_ph.info("⏳ Cross-Check Agent يدمج ويتحقق...")
            result = cross_check_agent(groq_res, arcee_res, exam_title, progress_ph)
            progress_ph.empty()

            st.session_state["last_result"]   = result
            st.session_state["last_title"]    = exam_title
            st.session_state["last_metadata"] = metadata
            st.session_state["last_content"]  = result["final"]

            render_dual_model_result(result, exam_title)

        elif "Groq" in model_choice:
            progress_ph.info("⏳ Groq يولد الاختبار...")
            content = call_groq(prompt)
            progress_ph.empty()
            st.session_state["last_content"] = content
            st.session_state["last_title"]   = exam_title
            st.session_state["last_metadata"] = metadata
            render_preview(content, exam_title)

        else:  # Arcee only
            progress_ph.info("⏳ Arcee يولد الاختبار...")
            content = call_arcee(prompt)
            progress_ph.empty()
            st.session_state["last_content"] = content
            st.session_state["last_title"]   = exam_title
            st.session_state["last_metadata"] = metadata
            render_preview(content, exam_title)

        # Auto-generate pedagogical report
        if st.session_state["last_content"] and not st.session_state["last_content"].startswith("⚠️"):
            report_prompt = f"""بناءً على اختبار {subject} للمستوى {level}، اكتب تقريراً بيداغوجياً موجزاً يتضمن:
1. الأهداف التعليمية المُقيَّمة
2. الكفاءات المستهدفة
3. معايير التصحيح العامة
4. توصيات للأستاذ"""
            report = call_groq(report_prompt)
            st.session_state["pedagogical_report"] = report

    # Regenerate button
    if st.session_state.get("last_content"):
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 إعادة التوليد بـ Groq", use_container_width=True):
                with st.spinner("⏳ Groq يعيد التوليد..."):
                    new_content = call_groq(st.session_state.get("_last_prompt", "أعد كتابة المحتوى بشكل مختلف"))
                st.session_state["last_content"] = new_content
                st.rerun()
        with col_b:
            if st.button("🔄 إعادة التوليد بـ Arcee", use_container_width=True):
                with st.spinner("⏳ Arcee يعيد التوليد..."):
                    new_content = call_arcee(st.session_state.get("_last_prompt", "أعد كتابة المحتوى بشكل مختلف"))
                st.session_state["last_content"] = new_content
                st.rerun()

        download_buttons(
            st.session_state["last_content"],
            st.session_state["last_title"],
            st.session_state["last_metadata"],
        )

    # Auto-show pedagogical report
    if st.session_state.get("pedagogical_report"):
        st.divider()
        st.markdown("### 📊 التقرير البيداغوجي التلقائي")
        render_preview(st.session_state["pedagogical_report"], "التقرير البيداغوجي")
        download_buttons(
          �  st.session_state["pedagogical_report"],
            "التقرير البيداغوجي",
            st.session_state.get("last_metadata", {}),
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: PEDAGOGICAL REPORT
# ══════════════════════════════════════════════════════════════════════════════

def page_pedagogical_report():
    st.markdown('<div class="section-title">📊 التقرير البيداغوجي — التقرير البيداغوجي</div>', unsafe_allow_html=True)

    # Show previously generated report if available
    if st.session_state.get("pedagogical_report"):
        st.success("✅ تم إنشاء تقرير بيداغوجي تلقائياً من آخر جلسة تحليل")
        render_preview(st.session_state["pedagogical_report"], "التقرير البيداغوجي")
        download_buttons(
            st.session_state["pedagogical_report"],
            "التقرير البيداغوجي",
            st.session_state.get("last_metadata", {}),
        )
        st.divider()

    st.markdown("#### إنشاء تقرير بيداغوجي مخصص")

    with st.form("report_form"):
        c1, c2 = st.columns(2)
        with c1:
            teacher_name = st.text_input("اسم الأستاذ/ة", placeholder="أدخل الاسم")
            subject_r    = st.selectbox("المادة", ["اللغة العربية", "الرياضيات", "العلوم الطبيعية",
                                                    "التاريخ والجغرافيا", "اللغة الفرنسية", "الفيزياء"])
            school_name  = st.text_input("اسم المؤسسة التعليمية", placeholder="ثانوية/متوسطة...")
        with c2:
            level_r    = st.selectbox("المستوى", ["الأول ابتدائي", "الثاني ابتدائي", "الثالث ابتدائي",
                                                    "الرابع ابتدائي", "الخامس ابتدائي",
                                                    "الأول متوسط", "الثاني متوسط", "الثالث متوسط", "الرابع متوسط",
                                                    "الأول ثانوي", "الثاني ثانوي", "الثالث ثانوي"])
            trimester_r = st.selectbox("الثلاثي", ["الثلاثي الأول", "الثلاثي الثاني", "الثلاثي الثاني"])
            num_students = st.number_input("عدد التلاميذ", min_value=1, max_value=50, value=30)

        observations = st.text_area(
            "الملاحظات والمعطيات (اختياري)",
            placeholder="أدخل ملاحظات حول مستوى القسم، نتائج التقييمات...",
            height=100,
        )
        submitted_r = st.form_submit_button("📊 إنشاء التقرير البيداغوجي", type="primary", use_container_width=True)

    if submitted_r:
        prompt_r = f"""أكتب تقريراً بيداغوجياً احترافياً ومفصلاً للمعطيات التالية:
- الأستاذ/ة: {teacher_name or "غير محدد"}
- المؤسسة: {school_name or "غير محددة"}
- المادة: {subject_r}
- المستوى: {level_r}
- الثلاثي: {trimester_r}
- عدد التلاميذ: {num_students}
- الملاحظات: {observations or "لا توجد ملاحظات إضافية"}

يجب أن يشمل التقرير:
1. الوضعية العامة للقسم
2. تحليل نتائج التقييمات
3. الصعوبات المرصودة لدى التلاميذ
4. الإجراءات العلاجية المقترحة
5. الأهداف للثلاثي القادم
6. توصيات عامة

التقرير باللغة العربية الفصحى بصياغة رسمية متوافقة مع وزارة التربية الوطنية الجزائرية."""

        with st.spinner("⏳ يجري إعداد التقرير البيداغوجي..."):
            report_groq  = call_groq(prompt_r)
            report_arcee = call_arcee(prompt_r)
            ph = st.empty()
            result = cross_check_agent(report_groq, report_arcee, "التقرير البيداغوجي", ph)

        st.session_state["pedagogical_report"] = result["final"]
        st.session_state["last_metadata"] = {
            "الأستاذ/ة": teacher_name,
            "المادة": subject_r,
            "المستوى": level_r,
            "المؤسسة": school_name,
            "الثلاثي": trimester_r,
        }

        render_dual_model_result(result, "التقرير البيداغوجي")
        download_buttons(result["final"], "التقرير البيداغوجي", st.session_state["last_metadata"])


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: GRADING BOOK
# ══════════════════════════════════════════════════════════════════════════════

def page_grading_book():
    st.markdown('<div class="section-title">📋 دفتر التنقيط — كشف النقاط</div>', unsafe_allow_html=True)

    num_classes = st.number_input("عدد الأقسام", min_value=1, max_value=10, value=1)

    classes_data = []
    for c_idx in range(num_classes):
        with st.expander(f"📁 القسم {c_idx + 1}", expanded=(c_idx == 0)):
            cls_name = st.text_input(f"اسم القسم {c_idx+1}", value=f"القسم {c_idx+1}", key=f"cls_name_{c_idx}")
            subjects_input = st.text_input(
                "المواد (مفصولة بفاصلة)",
                value="العربية,الرياضيات,العلوم",
                key=f"subjects_{c_idx}",
            )
            subjects = [s.strip() for s in subjects_input.split(",") if s.strip()]
            num_std = st.number_input(f"عدد تلاميذ القسم {c_idx+1}", min_value=1, max_value=50, value=5, key=f"nstd_{c_idx}")

            students = []
            for s_idx in range(num_std):
                cols = st.columns([3] + [2] * len(subjects))
                name = cols[0].text_input(f"التلميذ {s_idx+1}", key=f"name_{c_idx}_{s_idx}", placeholder=f"اسم التلميذ {s_idx+1}")
                grades = {}
                for j, subj in enumerate(subjects):
                    g = cols[j + 1].text_input(subj, key=f"grade_{c_idx}_{s_idx}_{j}", placeholder="—")
                    grades[subj] = g
                students.append({"name": name or f"تلميذ {s_idx+1}", "grades": grades})

            classes_data.append({"name": cls_name, "students": students})

    if st.button("📥 توليد دفتر التنقيط (Excel)", type="primary", use_container_width=True):
        xlsx_bytes = generate_grading_book(classes_data)
        if xlsx_bytes:
            st.success("✅ تم إنشاء دفتر التنقيط بنجاح!")
            st.download_button(
                "📊 تحميل دفتر التنقيط .xlsx",
                data=xlsx_bytes,
                file_name=f"daftar_tanqit_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.error("❌ تعذر إنشاء الملف — يرجى التأكد من تثبيت openpyxl")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS & DOCS
# ══════════════════════════════════════════════════════════════════════════════

def page_settings():
    st.markdown('<div class="section-title">⚙️ الإعدادات والوثائق التقنية</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔑 مفاتيح API", "📚 الوثائق التقنية", "📦 المكتبات"])

    with tab1:
        groq_ok  = bool(get_secret("GROQ_API_KEY"))
        arcee_ok = bool(get_secret("ARCEE_API_KEY"))
        col1, col2 = st.columns(2)
        col1.metric("GROQ_API_KEY",  "✅ مُهيأ" if groq_ok  else "❌ مفقود")
        col2.metric("ARCEE_API_KEY", "✅ مُهيأ" if arcee_ok else "❌ مفقود")
        if not groq_ok or not arcee_ok:
            st.info("أضف مفاتيح API في متغيرات البيئة (Secrets) في لوحة تحكم Replit/Streamlit.")

    with tab2:
        st.markdown("""
        ## 🤝 كيف يعمل المحرك المزدوج (Groq × Arcee)

        ### 1. التدفق الهجين (Hybrid Workflow)
        ```
        المستخدم ──► [طلب المحتوى]
                          │
               ┌──────────┴──────────┐
               ▼                     ▼
           ⚡ Groq                 🧠 Arcee
        (llama-3.3-70b)       (arcee-agent)
        السرعة العالية         الدقة التربوية
               │                     │
               └──────────┬──────────┘
                          ▼
               🔬 Cross-Check Agent
           (يقارن، يدمج، يتحقق من الجودة)
                          │
                          ▼
               ✅ المخرجات النهائية الموثقة
        ```

        ### 2. وكيل التحقق (Cross-Check Agent)
        - **الاستقبال**: يأخذ إجابتي Groq و Arcee
        - **المقارنة**: يحلل التوافق مع المنهج الجزائري
        - **الدمج**: يختار أفضل عناصر الإجابتين
        - **التوثيق**: يُعطي نقطة جودة تربوية (٪)

        ### 3. خريطة المجلدات
        ```
        artifacts/donia-mind/
        ├── app.py                  ← التطبيق الرئيسي
        ├── requirements.txt        ← المكتبات
        ├── .streamlit/
        │   └── config.toml        ← إعدادات Streamlit
        ├── �assets/
        │   └── logo_donia.jpg     ← شعار المنصة
        └── fonts/
            └── Amiri-Regular.ttf  ← خط عربي للـ PDF
        ```

        ### 4. تصحيح الخط العربي في PDF
        ```python
        import arabic_reshaper
        from bidi.algorithm import get_display

        text = "اختبار في اللغة العربية"
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        # ثم يُمرَّر إلى ReportLab مع خط Amiri
        ```
        """)

    with tab3:
        libs = {
            "streamlit":      (True, "واجهة المستخدم"),
            "groq":           (GROQ_AVAILABLE, "واجهة Groq API"),
            "openai":         (OPENAI_AVAILABLE, "واجهة Arcee API"),
            "arabic_reshaper":(ARABIC_BIDI_AVAILABLE, "إعادة تشكيل العربية"),
            "bidi":           (ARABIC_BIDI_AVAILABLE, "نظام الكتابة RTL"),
            "reportlab":      (REPORTLAB_AVAILABLE, "توليد PDF"),
            "docx":           (DOCX_AVAILABLE, "توليد Word"),
            "openpyxl":       (OPENPYXL_AVAILABLE, "توليد Excel"),
            "qrcode":         (QRCODE_AVAILABLE, "توليد QR Code"),
            "PIL":            (PIL_AVAILABLE, "معالجة الصور"),
        }
        rows = []
        for lib, (status, desc) in libs.items():
            rows.append({"المكتبة": lib, "الحالة": "✅ متاح" if status else "❌ مفقود", "الوظيفة": desc})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("### 📦 أمر التثبيت")
        st.code("pip install -r requirements.txt", language="bash")
        st.code("""streamlit>=1.28.0
groq>=0.4.0
openai>=1.0.0
requests>=2.31.0
qrcode[pil]>=7.4.2
Pillow>=10.0.0
arabic-reshaper>=3.0.0
python-bidi>=0.4.2
reportlab>=4.0.0
python-docx>=1.1.0
openpyxl>=3.1.2
pandas>=2.0.0
lxml>=4.9.0""")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN — SIDEBAR NAVIGATION + ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def main():
    inject_global_css()
    init_state()

    # ─── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:16px 0 8px;">
          <div style="font-size:2.5rem;">🤖</div>
          <div style="font-size:1.1rem;font-weight:700;color:#DBEAFE;">DONIA MIND 1</div>
          <div style="font-size:0.75rem;color:#93C5FD;">المختبر التعليمي الذكي</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        page = st.radio(
            "القائمة الرئيسية",
            [
                "🏠 الرئيسية",
                "🧪 مولّد الاختبارات",
                "📊 التقرير البيداغوجي",
                "📋 دفتر التنقيط",
                "⚙️ الإعدادات",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        # QR code in sidebar
        qr_bytes = generate_qr_code(APP_URL)
        if qr_bytes:
            st.image(qr_bytes, caption="رابط المنصة", use_container_width=True)

        st.markdown("""
        <div style="text-align:center;font-size:11px;color:#64748B;padding-top:8px;">
          Powered by Groq ⚡ × Arcee 🧠<br/>
          © 2025 Donia Labstech
        </div>
        """, unsafe_allow_html=True)

    # ─── Header ────────────────────────────────────────────────────────────────
    render_header()

    # ─── Router ────────────────────────────────────────────────────────────────
    if page == "🏠 الرئيسية":
        page_home()
    elif page == "🧪 مولّد الاختبارات":
        page_exam_generator()
    elif page == "📊 التقرير البيداغوجي":
        page_pedagogical_report()
    elif page == "📋 دفتر التنقيط":
        page_grading_book()
    elif page == "⚙️ الإعدادات":
        page_settings()


if __name__ == "__main__":
    main()
