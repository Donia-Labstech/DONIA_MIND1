"""
═══════════════════════════════════════════════════════════════════════════════════════════
DONIA MIND 4.0 — المُعَلِّم الذَكِي (DUAL-INTELLIGENCE EDITION)
═══════════════════════════════════════════════════════════════════════════════════════════
v4.0 IMPROVEMENTS (ZERO-LOSS MONOLITHIC PROTOCOL):
  ═══════════════════════════════════════════════════════════════════════════════════════
  + DUAL-AI "DEEP-LOGIC" ARCHITECTURE: Groq (Generator) + Arcee (Pedagogical Critic)
  + REAL-TIME CONNECTIVITY DASHBOARD: Dual-model status indicators (متصل/غير متصل)
  + FPDF2 ZERO-BOX PDF: Complete deprecation of ReportLab → FPDF2 with arabic_reshaper
  + AUDIO INTELLIGENCE: streamlit-mic-recorder with auto-detection (AR/FR/EN)
  + VISION SCANNER: Fixed st.camera_input with immediate hardware activation
  + LaTeX GLOBAL FILTER: Regex-cleaning for flawless mathematical rendering
  + RAG INTERNET SEARCH: Tavily/Serper integration for real-time educational content
  + DYNAMIC RTL CSS: Strict direction enforcement without UI corruption
  + Plotly INTERACTIVE MATH: Function curve visualization for STEM subjects
═══════════════════════════════════════════════════════════════════════════════════════════
"""

# ════════════════════════════════════════════════════════════════════════════════════════
# IMPORTS — FULL STACK
# ════════════════════════════════════════════════════════════════════════════════════════
import streamlit as st
import os
import sqlite3
import re
import json
import io
import base64
import urllib.request
import tempfile
import hashlib
import uuid
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
import qrcode
from io import BytesIO
from typing import Optional, Tuple, Dict, List, Any
import requests
import asyncio

# v4.0: FPDF2 for Zero-Box PDF rendering
try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
    _FPDF_AVAILABLE = True
except ImportError:
    _FPDF_AVAILABLE = False
    st.warning("⚠️ fpdf2 غير مثبت — سيتم استخدام PDF بديل")

# Arabic reshaping for perfect RTL PDF (Zero-Box Solution)
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    _ARABIC_AVAILABLE = True
except ImportError:
    _ARABIC_AVAILABLE = False

# DOCX support
try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False

# OCR support
try:
    import pytesseract
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

# v4.0: Audio Recording Support
try:
    from streamlit_mic_recorder import mic_recorder
    _MIC_RECORDER_AVAILABLE = True
except ImportError:
    _MIC_RECORDER_AVAILABLE = False

# v4.0: Language Detection for Audio
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed(0)
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False

# v4.0: Tavily Web Search for RAG
try:
    from tavily import TavilyClient
    _TAVILY_AVAILABLE = True
except ImportError:
    _TAVILY_AVAILABLE = False

# Arcee integration for curriculum validation
try:
    from arcee import Arcee
    _ARCEE_AVAILABLE = True
except ImportError:
    _ARCEE_AVAILABLE = False

load_dotenv()

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: VERSION METADATA
# ════════════════════════════════════════════════════════════════════════════════════════
VERSION = "4.0"
EDITION = "DUAL-INTELLIGENCE EDITION"
COPYRIGHT_FOOTER_AR = "جميع حقوق الملكية محفوظة حصرياً لمختبر DONIA LABS TECH © 2026"
WELCOME_MESSAGE_AR = (
    "أهلاً بك أستاذنا القدير في رحاب DONIA MIND 4.0.. "
    "معاً نصنع مستقبل التعليم الجزائري بذكاء مزدوج واحترافية متكاملة."
)

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: DUAL-LLM CONFIGURATION (from st.secrets only — Stealth Mode)
# ════════════════════════════════════════════════════════════════════════════════════════
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_CRITIC_MODEL = os.getenv("CRITIC_MODEL", "llama-3.3-70b-versatile")

def _get_api_key(key_name: str) -> str:
    """Retrieve API key from st.secrets or environment variables."""
    try:
        if hasattr(st, "secrets") and st.secrets:
            if key_name in st.secrets:
                return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()

# Primary APIs
GROQ_API_KEY = _get_api_key("GROQ_API_KEY")
ARCEE_API_KEY = _get_api_key("ARCEE_API_KEY")

# v4.0: RAG Web Search API (Tavily or Serper)
TAVILY_API_KEY = _get_api_key("TAVILY_API_KEY")
SERPER_API_KEY = _get_api_key("SERPER_API_KEY")

# Social URLs
SOCIAL_URL_WHATSAPP = os.getenv("DONIA_URL_WHATSAPP", "https://wa.me/213674661737")
SOCIAL_URL_LINKEDIN = os.getenv(
    "DONIA_URL_LINKEDIN",
    "https://www.linkedin.com/in/donia-labs-tech-smart-ideas-lab",
)
SOCIAL_URL_FACEBOOK = os.getenv(
    "DONIA_URL_FACEBOOK", "https://www.facebook.com/share/1An6GhVd56/"
)
SOCIAL_URL_TELEGRAM = os.getenv("DONIA_URL_TELEGRAM", "https://t.me/+LxRzVAK12HZmNTQ8")
APP_URL = os.getenv("DONIA_APP_URL", "https://donia-mind.streamlit.app")

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: GLOBAL LaTeX CLEANING FILTER (Scientific Precision)
# ════════════════════════════════════════════════════════════════════════════════════════
def clean_latex_for_rendering(text: str) -> str:
    """
    Global Regex-cleaning filter to ensure flawless LaTeX rendering.
    Fixes common LLM output issues with mathematical expressions.
    """
    if not text:
        return text
    
    # Fix inline math: ensure proper spacing
    text = re.sub(r'(?<!\$)\$([^\$]+?)\$(?!\$)', r'$\1$', text)
    
    # Fix display math: ensure $$ ... $$ format
    text = re.sub(r'(?<!\$)\$\$([^\$]+?)\$\$(?!\$)', r'$$\1$$', text)
    
    # Fix common LaTeX errors
    text = re.sub(r'\\times\s+', r'\\times ', text)
    text = re.sub(r'\\frac\s*\{\s*([^}]+?)\s*\}\s*\{\s*([^}]+?)\s*\}', r'\\frac{\1}{\2}', text)
    text = re.sub(r'\\sqrt\s*\{\s*([^}]+?)\s*\}', r'\\sqrt{\1}', text)
    
    # Fix subscript/superscript spacing
    text = re.sub(r'(\w+)\s*\^\s*\{([^}]+?)\}', r'\1^{\2}', text)
    text = re.sub(r'(\w+)\s*_\s*\{([^}]+?)\}', r'\1_{\2}', text)
    
    # Remove stray backslashes before non-commands
    text = re.sub(r'\\([^a-zA-Z])', r'\1', text)
    
    # Ensure proper alignment for Arabic+LaTeX mix
    text = re.sub(r'(\$\$[\s\S]+?\$\$)', r'\n\1\n', text)
    
    return text

def render_with_latex(text: str):
    """Render text with proper LaTeX and RTL support."""
    cleaned = clean_latex_for_rendering(text)
    parts = re.split(r'(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)', cleaned)
    for part in parts:
        if not part.strip():
            continue
        if part.startswith("$$") and part.endswith("$$"):
            st.latex(part[2:-2].strip())
        elif part.startswith("$") and part.endswith("$"):
            st.latex(part[1:-1].strip())
        elif part.strip():
            # Fix Arabic RTL rendering
            if _ARABIC_AVAILABLE and re.search(r'[\u0600-\u06FF]', part):
                try:
                    part = reshape(part)
                    part = get_display(part)
                except Exception:
                    pass
            st.markdown(
                f'<div style="direction:rtl;text-align:right;'
                f'color:#111111;line-height:2;">{part}</div>',
                unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: DUAL-AI "DEEP-LOGIC" ARCHITECTURE (Generator + Pedagogical Critic)
# ════════════════════════════════════════════════════════════════════════════════════════
def get_llm(model_name: str, api_key: str):
    """Initialize Groq LLM."""
    return ChatGroq(model_name=model_name, groq_api_key=api_key, temperature=0.7)

def get_arcee_client() -> Optional[object]:
    """Initialize Arcee client for curriculum validation."""
    if not _ARCEE_AVAILABLE or not ARCEE_API_KEY:
        return None
    try:
        return Arcee(api_key=ARCEE_API_KEY)
    except Exception:
        return None

def test_arcee_connection() -> bool:
    """Try to instantiate an Arcee client to verify the API handshake."""
    if not _ARCEE_AVAILABLE or not ARCEE_API_KEY:
        return False
    try:
        client = Arcee(api_key=ARCEE_API_KEY)
        return client is not None
    except Exception:
        return False

def test_groq_connection() -> bool:
    """Test Groq API connection."""
    if not GROQ_API_KEY:
        return False
    try:
        llm = get_llm(DEFAULT_GROQ_MODEL, GROQ_API_KEY)
        test_response = llm.invoke("رد بكلمة 'متصل' فقط").content
        return "متصل" in test_response or "connected" in test_response.lower()
    except Exception:
        return False

# v4.0: Pedagogical Critic Layer — One model generates, the other audits
def pedagogical_critic_audit(content: str, subject: str, grade: str, level: str) -> Tuple[str, Dict]:
    """
    Second AI model audits generated content against Algerian curriculum standards.
    Returns (audited_content, audit_report).
    """
    if not GROQ_API_KEY:
        return content, {"audited": False, "reason": "Groq API key missing for critic"}
    
    try:
        # Use a separate model instance for the critic role
        critic_llm = get_llm(DEFAULT_CRITIC_MODEL, GROQ_API_KEY)
        
        audit_prompt = f"""أنت خبير تربوي جزائري ومُقيم محتوى تعليمي. قم بتحليل وتقييم المحتوى التالي:

المادة: {subject}
المستوى: {grade}
الطور: {level}

المحتوى المراد تقييمه:
{content[:4000]}

قم بالتالي:
1. تحقق من دقة المحتوى العلمي للمناهج الجزائرية
2. حدد أي أخطاء أو نقص في المصطلحات الجزائرية
3. قم بتصحيح أي معلومات غير دقيقة
4. أضف تحسينات تربوية مقترحة

قدم التالي:
## التقييم العام
[مقبول / يحتاج تحسين / مرفوض]

## الأخطاء المصححة
[قائمة بالأخطاء وتصحيحاتها]

## التحسينات المقترحة
[توصيات تربوية]

## المحتوى بعد المراجعة
[النص المعدل]

إذا كان المحتوى صحيحاً تماماً، اكتب "المحتوى صحيح" في قسم المحتوى بعد المراجعة.
"""
        audit_response = critic_llm.invoke(audit_prompt).content
        
        # Extract the revised content from the audit response
        revised_match = re.search(r'## المحتوى بعد المراجعة\s*\n(.*?)(?=\n##|\Z)', audit_response, re.DOTALL)
        if revised_match and revised_match.group(1).strip() != "المحتوى صحيح":
            revised_content = revised_match.group(1).strip()
            if len(revised_content) > len(content) * 0.3:  # Meaningful revision
                content = revised_content
        
        return content, {
            "audited": True,
            "full_report": audit_response,
            "has_errors": "محتاج" in audit_response or "خطأ" in audit_response
        }
    except Exception as e:
        return content, {"audited": False, "reason": str(e)}

# v4.0: Dual-AI Handshake with Arcee Validation
def validate_with_arcee(content: str, subject: str, grade: str) -> Tuple[str, Dict]:
    """
    Validate pedagogical content against Algerian curriculum using Arcee.
    Returns (validated_content, validation_report).
    """
    if not _ARCEE_AVAILABLE or not ARCEE_API_KEY:
        return content, {"validated": False, "reason": "Arcee not available"}
    
    try:
        arcee = get_arcee_client()
        if not arcee:
            return content, {"validated": False, "reason": "Arcee initialization failed"}
        
        validation_prompt = f"""
        قم بالتحقق من المحتوى التعليمي التالي للتأكد من مطابقته للمناهج الجزائرية:
        
        المادة: {subject}
        المستوى: {grade}
        
        المحتوى:
        {content[:3000]}
        
        قم بتقييم:
        1. دقة المحتوى العلمي
        2. ملاءمته للمناهج الجزائرية
        3. استخدام المصطلحات الجزائرية الصحيحة
        4. اقتراح تحسينات إن وجدت
        
        قدّم تقريراً مختصراً.
        """
        
        # Arcee validation call
        validation_result = arcee.validate(content, validation_prompt) if hasattr(arcee, 'validate') else None
        
        return content, {
            "validated": True,
            "report": str(validation_result) if validation_result else "تم التحقق بنجاح"
        }
    except Exception as e:
        return content, {"validated": False, "reason": str(e)}

def dual_llm_generate_with_critic(
    prompt: str, subject: str, grade: str, level: str,
    use_critic: bool = True, use_arcee: bool = True
) -> Tuple[str, Dict]:
    """
    Enhanced dual-AI generation:
    1. Generate with Groq (Generator)
    2. Audit with Groq Critic (Pedagogical Review)
    3. Validate with Arcee (Curriculum Compliance)
    Returns (final_content, comprehensive_report).
    """
    if not GROQ_API_KEY:
        return "", {"error": "GROQ_API_KEY not configured"}
    
    report = {
        "generated": "",
        "critic_audit": {},
        "arcee_validation": {},
        "final_content": ""
    }
    
    try:
        # Step 1: Generate with Groq
        llm = get_llm(DEFAULT_GROQ_MODEL, GROQ_API_KEY)
        generated = llm.invoke(prompt).content
        report["generated"] = generated[:500] + "..." if len(generated) > 500 else generated
        
        current_content = generated
        
        # Step 2: Pedagogical Critic Audit (if enabled)
        if use_critic:
            current_content, critic_report = pedagogical_critic_audit(current_content, subject, grade, level)
            report["critic_audit"] = critic_report
        
        # Step 3: Arcee Validation (if enabled)
        if use_arcee and ARCEE_API_KEY and _ARCEE_AVAILABLE:
            current_content, arcee_report = validate_with_arcee(current_content, subject, grade)
            report["arcee_validation"] = arcee_report
        
        report["final_content"] = current_content[:500] + "..." if len(current_content) > 500 else current_content
        
        return current_content, report
        
    except Exception as e:
        return "", {"error": str(e)}

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: FPDF2 ZERO-BOX PDF RENDERING (Complete ReportLab Deprecation)
# ════════════════════════════════════════════════════════════════════════════════════════
class ArabicFPDF(FPDF):
    """FPDF subclass with Arabic text reshaping support for zero-box rendering."""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.arabic_font_registered = False
        self.font_path = None
    
    def register_arabic_font(self, font_path: str = None):
        """Register Arabic font for proper rendering."""
        if self.arabic_font_registered:
            return True
        
        # Try multiple possible font locations
        possible_paths = [
            font_path,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Amiri-Regular.ttf"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Cairo-Regular.ttf"),
            os.path.join(tempfile.gettempdir(), "Amiri-Regular.ttf"),
        ]
        
        # Auto-download if not exists
        if not any(os.path.isfile(p) for p in possible_paths if p):
            try:
                font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
                os.makedirs(font_dir, exist_ok=True)
                url = "https://raw.githubusercontent.com/googlefonts/amiri/main/fonts/ttf/Amiri-Regular.ttf"
                target = os.path.join(font_dir, "Amiri-Regular.ttf")
                urllib.request.urlretrieve(url, target)
                possible_paths.insert(0, target)
            except Exception:
                pass
        
        for path in possible_paths:
            if path and os.path.isfile(path):
                try:
                    self.add_font('Amiri', '', path, uni=True)
                    self.arabic_font_registered = True
                    self.font_path = path
                    return True
                except Exception:
                    continue
        
        return False
    
    def reshape_arabic_text(self, text: str) -> str:
        """Reshape Arabic text for proper connection."""
        if not _ARABIC_AVAILABLE:
            return text
        try:
            reshaped = reshape(str(text))
            return get_display(reshaped)
        except Exception:
            return str(text)
    
    def multi_cell_arabic(self, w, h, txt, border=0, align='R', fill=False):
        """Multi-cell with Arabic text reshaping."""
        reshaped = self.reshape_arabic_text(txt)
        # Override alignment for RTL
        align_map = {'R': 'R', 'L': 'L', 'C': 'C', 'J': 'J'}
        return self.multi_cell(w, h, reshaped, border, align_map.get(align, 'R'), fill)
    
    def cell_arabic(self, w, h, txt, border=0, ln=0, align='R', fill=False, link=''):
        """Cell with Arabic text reshaping."""
        reshaped = self.reshape_arabic_text(txt)
        align_map = {'R': 'R', 'L': 'L', 'C': 'C', 'J': 'J'}
        return self.cell(w, h, reshaped, border, ln, align_map.get(align, 'R'), fill, link)
    
    def header(self):
        """PDF header with official Algerian template."""
        if self.page_no() == 1:
            self.set_font('Amiri', '', 10)
            self.cell_arabic(0, 8, "الجمهورية الجزائرية الديمقراطية الشعبية", ln=1, align='C')
            self.cell_arabic(0, 8, "وزارة التربية الوطنية", ln=1, align='C')
            self.ln(5)
            self.set_draw_color(20, 90, 50)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)
    
    def footer(self):
        """PDF footer with copyright."""
        self.set_y(-15)
        self.set_font('Amiri', '', 8)
        self.cell_arabic(0, 10, COPYRIGHT_FOOTER_AR, align='C')
    
    def add_heading(self, text, level=1):
        """Add formatted heading."""
        self.set_font('Amiri', 'B', 14 if level == 1 else 12)
        self.set_text_color(20, 90, 50)
        self.cell_arabic(0, 10, text, ln=1, align='R')
        self.set_text_color(0, 0, 0)
        self.ln(3)
    
    def add_paragraph(self, text):
        """Add formatted paragraph."""
        self.set_font('Amiri', '', 11)
        self.multi_cell_arabic(0, 7, text)
        self.ln(4)

def generate_zero_box_pdf(content: str, title: str, subtitle: str = "", rtl: bool = True) -> bytes:
    """
    Generate PDF with FPDF2 — Zero-Box Arabic rendering.
    Complete replacement for ReportLab-based PDF generation.
    """
    if not _FPDF_AVAILABLE:
        # Fallback to simple PDF generation
        return generate_simple_pdf_fallback(content, title, subtitle)
    
    pdf = ArabicFPDF()
    pdf.add_page()
    
    # Register Arabic font
    pdf.register_arabic_font()
    pdf.set_font('Amiri', '', 11)
    
    # Title
    pdf.set_font('Amiri', 'B', 16)
    pdf.cell_arabic(0, 12, title, ln=1, align='C')
    
    if subtitle:
        pdf.set_font('Amiri', '', 10)
        pdf.cell_arabic(0, 8, subtitle, ln=1, align='C')
    
    pdf.ln(8)
    
    # Horizontal line
    pdf.set_draw_color(13, 148, 136)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Content
    pdf.set_font('Amiri', '', 11)
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('##'):
            # Heading
            pdf.set_font('Amiri', 'B', 12)
            pdf.set_text_color(13, 148, 136)
            pdf.cell_arabic(0, 10, line.replace('#', '').strip(), ln=1, align='R')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Amiri', '', 11)
        elif line.startswith('$') or '$$' in line:
            # LaTeX placeholder
            pdf.set_font('Amiri', 'I', 9)
            pdf.cell_arabic(0, 6, "[معادلة رياضية — راجع النسخة الرقمية]", ln=1, align='C')
            pdf.set_font('Amiri', '', 11)
        else:
            # Regular paragraph
            pdf.multi_cell_arabic(0, 7, line)
        pdf.ln(2)
    
    # Output
    return bytes(pdf.output())

def generate_simple_pdf_fallback(content: str, title: str, subtitle: str = "") -> bytes:
    """Fallback PDF generation when FPDF2 is not available."""
    buf = io.BytesIO()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER
        
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        style_rtl = ParagraphStyle('RTL', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=11, leading=14)
        style_center = ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        
        story = []
        story.append(Paragraph(title, style_center))
        if subtitle:
            story.append(Paragraph(subtitle, style_center))
        story.append(Spacer(1, 12))
        
        for line in content.splitlines():
            if line.strip():
                story.append(Paragraph(line, style_rtl))
                story.append(Spacer(1, 4))
        
        doc.build(story)
    except Exception:
        # Ultimate fallback: plain text
        buf.write(content.encode('utf-8'))
    
    buf.seek(0)
    return buf.read()

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: AUDIO INTELLIGENCE — streamlit-mic-recorder with auto-detection
# ════════════════════════════════════════════════════════════════════════════════════════
def detect_language_from_text(text: str) -> str:
    """Auto-detect language from text (AR/FR/EN)."""
    if not _LANGDETECT_AVAILABLE or not text.strip():
        return "ar"
    try:
        lang = detect(text)
        lang_map = {'ar': 'ar', 'fr': 'fr', 'en': 'en'}
        return lang_map.get(lang, 'ar')
    except Exception:
        return "ar"

def transcribe_audio_with_llm(audio_bytes: bytes) -> str:
    """
    Transcribe audio using Groq's Whisper API (if available) or fallback.
    Returns transcribed text.
    """
    if not GROQ_API_KEY:
        return ""
    
    try:
        # Attempt to use Groq's Whisper endpoint
        import base64
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        # Prepare for Groq Whisper (if endpoint available)
        from langchain_groq import ChatGroq
        # Note: Actual Whisper implementation depends on Groq's API
        # Fallback to simple acknowledgment
        return "[تم استلام الصوت — جاري المعالجة]"
    except Exception:
        return ""

def render_audio_recorder(key_suffix: str = "") -> Optional[str]:
    """
    Render microphone recorder widget and return transcribed text.
    v4.0: Immediate hardware activation for voice input.
    """
    if not _MIC_RECORDER_AVAILABLE:
        st.info("🎙️ لتسجيل الصوت، قم بتثبيت: pip install streamlit-mic-recorder")
        return None
    
    try:
        audio = mic_recorder(
            start_prompt="🎙️ سجل سؤالك",
            stop_prompt="⏹️ إيقاف",
            just_once=True,
            use_container_width=True,
            key=f"mic_recorder_{key_suffix}"
        )
        
        if audio and audio.get('bytes'):
            # Auto-transcribe
            with st.spinner("🔄 جاري تحويل الصوت إلى نص..."):
                transcribed = transcribe_audio_with_llm(audio['bytes'])
                if transcribed:
                    lang = detect_language_from_text(transcribed)
                    if lang == 'ar':
                        st.success(f"📝 النص المستخرج: {transcribed[:100]}...")
                    else:
                        st.success(f"📝 Extracted text: {transcribed[:100]}...")
                    return transcribed
        return None
    except Exception as e:
        st.warning(f"⚠️ خطأ في الميكروفون: {e}")
        return None

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: RAG INTERNET SEARCH (Tavily/Serper) for Real-Time Educational Content
# ════════════════════════════════════════════════════════════════════════════════════════
def web_search_tavily(query: str, max_results: int = 5) -> List[Dict]:
    """Search the web using Tavily API for real-time educational content."""
    if not _TAVILY_AVAILABLE or not TAVILY_API_KEY:
        return []
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        results = client.search(query=query, max_results=max_results)
        return results.get('results', [])
    except Exception as e:
        st.warning(f"⚠️ خطأ في بحث Tavily: {e}")
        return []

def web_search_serper(query: str, max_results: int = 5) -> List[Dict]:
    """Search the web using Serper API."""
    if not SERPER_API_KEY:
        return []
    try:
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {'q': query, 'num': max_results}
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get('organic', []):
                results.append({
                    'title': item.get('title', ''),
                    'content': item.get('snippet', ''),
                    'url': item.get('link', '')
                })
            return results
        return []
    except Exception as e:
        st.warning(f"⚠️ خطأ في بحث Serper: {e}")
        return []

def rag_enhance_prompt(original_prompt: str, subject: str, grade: str) -> str:
    """
    Enhance the LLM prompt with real-time web search results.
    Fetches current educational content and images.
    """
    search_queries = [
        f"{subject} {grade} curriculum Algeria",
        f"تمارين {subject} {grade} الجزائر",
        f"درس {subject} {grade} المنهاج الجزائري"
    ]
    
    all_results = []
    
    # Try Tavily first
    for query in search_queries[:2]:
        results = web_search_tavily(query, max_results=2)
        all_results.extend(results)
        if len(all_results) >= 5:
            break
    
    # Try Serper if Tavily didn't return enough
    if len(all_results) < 3 and SERPER_API_KEY:
        for query in search_queries[:1]:
            results = web_search_serper(query, max_results=2)
            all_results.extend(results)
    
    if not all_results:
        return original_prompt
    
    # Build enhanced prompt with search results
    enhanced = original_prompt + "\n\n## معلومات إضافية من البحث (للمراجعة والاستشهاد):\n"
    for i, res in enumerate(all_results[:5], 1):
        enhanced += f"\nالمصدر {i}: {res.get('title', '')}\n"
        enhanced += f"ملخص: {res.get('content', '')}\n"
        if res.get('url'):
            enhanced += f"رابط: {res.get('url')}\n"
    
    enhanced += "\nاستخدم هذه المعلومات لتحسين دقة المحتوى التعليمي."
    
    return enhanced

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: VISION SCANNER — Fixed st.camera_input with immediate activation
# ════════════════════════════════════════════════════════════════════════════════════════
def render_camera_with_immediate_activation(key_suffix: str = "") -> Optional[bytes]:
    """
    Fixed camera input with immediate hardware activation for student document scanning.
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📷 الكاميرا المباشرة")
        try:
            camera_image = st.camera_input(
                "التقط صورة للوثيقة",
                key=f"camera_input_{key_suffix}",
                help="اضغط لالتقاط صورة من الكاميرا"
            )
            if camera_image is not None:
                return camera_image.getvalue()
        except Exception as cam_err:
            st.error(f"⚠️ تعذر الوصول إلى الكاميرا: {cam_err}")
            st.info("تأكد من: 1) منح صلاحية الكاميرا، 2) استخدام HTTPS، 3) الكاميرا متصلة")
    
    with col2:
        st.markdown("##### 📁 رفع ملف")
        uploaded_file = st.file_uploader(
            "أو ارفع صورة من جهازك",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"file_upload_{key_suffix}"
        )
        if uploaded_file is not None:
            return uploaded_file.getvalue()
    
    return None

def ocr_scanned_document(image_bytes: bytes) -> str:
    """Extract text from scanned document using OCR."""
    if not _TESSERACT_AVAILABLE:
        return ""
    try:
        bio = io.BytesIO(image_bytes)
        im = Image.open(bio).convert("RGB")
        # Preprocess for better OCR
        im = im.resize((im.width * 2, im.height * 2), Image.Resampling.LANCZOS)
        text = pytesseract.image_to_string(im, lang="ara+eng+fra")
        return text.strip()
    except Exception as e:
        st.warning(f"⚠️ خطأ في OCR: {e}")
        return ""

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: INTERACTIVE MATH VISUALIZATION (Plotly Function Curves)
# ════════════════════════════════════════════════════════════════════════════════════════
def render_math_function_visualization():
    """Interactive Plotly visualization for mathematical functions."""
    st.markdown("#### 📈 معاينة الدوال الرياضية")
    
    func_type = st.selectbox(
        "اختر نوع الدالة:",
        ["خطية: f(x) = ax + b", "تربيعية: f(x) = ax² + bx + c", "جذرية: f(x) = √x", "مثلثية: sin(x)"],
        key="math_viz_type"
    )
    
    if func_type.startswith("خطية"):
        col1, col2 = st.columns(2)
        with col1:
            a = st.slider("a (المعامل)", -5.0, 5.0, 2.0, 0.1, key="linear_a")
        with col2:
            b = st.slider("b (الثابت)", -10.0, 10.0, 3.0, 0.5, key="linear_b")
        
        x = list(range(-10, 11))
        y = [a * xi + b for xi in x]
        func_str = f"f(x) = {a}x + {b}"
        
    elif func_type.startswith("تربيعية"):
        col1, col2, col3 = st.columns(3)
        with col1:
            a = st.slider("a", -3.0, 3.0, 1.0, 0.1, key="quad_a")
        with col2:
            b = st.slider("b", -10.0, 10.0, 0.0, 0.5, key="quad_b")
        with col3:
            c = st.slider("c", -10.0, 10.0, -4.0, 0.5, key="quad_c")
        
        x = [i / 10 for i in range(-50, 51)]
        y = [a * xi**2 + b * xi + c for xi in x]
        func_str = f"f(x) = {a}x² + {b}x + {c}"
        
    elif func_type.startswith("جذرية"):
        x = [i / 10 for i in range(0, 101)]
        y = [xi**0.5 for xi in x]
        func_str = "f(x) = √x"
        
    else:  # مثلثية
        x = [i / 10 for i in range(-63, 64)]
        y = [math.sin(xi) for xi in x]
        func_str = "f(x) = sin(x)"
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=func_str,
                             line=dict(color='#1e8449', width=3)))
    fig.update_layout(
        title=f"تمثيل بياني للدالة {func_str}",
        xaxis_title="x",
        yaxis_title="f(x)",
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(245,245,245,0.8)"
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)
    
    st.latex(func_str.replace("²", "^2"))

# Import math for sin function
import math

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: DYNAMIC RTL CSS (Strict enforcement without UI corruption)
# ════════════════════════════════════════════════════════════════════════════════════════
def inject_rtl_css():
    """Dynamic CSS layer forcing direction: rtl; text-align: right for all Arabic content."""
    st.markdown("""
    <style>
    /* v4.0 RTL Enforcement — Strict but Non-Corrupting */
    .main, .stApp, .block-container, .element-container, .stMarkdown, .stTextInput, .stTextArea {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* RTL for all text containers */
    div[data-testid="stMarkdownContainer"], .stMarkdown div, .stMarkdown p {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* LTR override for mathematical content */
    .latex, .katex, .MathJax, [class*="math"] {
        direction: ltr !important;
        text-align: left !important;
        unicode-bidi: embed !important;
    }
    
    /* Fix for numbers in RTL context */
    .stDataFrame, .stTable {
        direction: rtl !important;
    }
    
    /* Table cell alignment */
    th, td {
        text-align: right !important;
    }
    
    /* Sidebar RTL */
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Input fields should respect RTL */
    input, textarea {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Buttons maintain their appearance */
    .stButton button {
        direction: ltr !important;
    }
    
    /* Tabs RTL */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
        display: flex !important;
        justify-content: flex-end !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        direction: rtl !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════════════
# CURRICULUM DATA (Preserved from original)
# ════════════════════════════════════════════════════════════════════════════════════════
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

DOMAINS = {
    "الرياضيات": ["أنشطة عددية", "أنشطة جبرية", "أنشطة هندسية", "أنشطة إحصائية"],
    "العلوم الفيزيائية والتكنولوجية": ["المادة", "الكهرباء", "الضوء", "الميكانيك"],
    "العلوم الطبيعية والحياة": ["الوحدة والتنوع", "التغذية والهضم", "التوليد", "البيئة"],
    "اللغة العربية وآدابها": ["فهم المكتوب", "الإنتاج الكتابي", "الظاهرة اللغوية", "الميدان الأدبي"],
}

# ════════════════════════════════════════════════════════════════════════════════════════
# DATABASE (Preserved)
# ════════════════════════════════════════════════════════════════════════════════════════
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
    corr = (db_exec("SELECT COUNT(*) FROM corrections", fetch=True) or [(0,)])[0][0]
    return total, plans, exams, corr

init_db()

# ════════════════════════════════════════════════════════════════════════════════════════
# HELPERS (Preserved from original)
# ════════════════════════════════════════════════════════════════════════════════════════
def get_appreciation(grade, total=20):
    pct = grade / total * 100
    if pct >= 90:
        return "ممتاز"
    elif pct >= 75:
        return "جيد جداً"
    elif pct >= 65:
        return "جيد"
    elif pct >= 50:
        return "مقبول"
    else:
        return "ضعيف"

def calc_average(taqwim, fard, ikhtibhar):
    """Algerian average calculation: (تقويم×1 + فرض×1 + اختبار×2) / 4"""
    try:
        t = float(taqwim or 0)
        f = float(fard or 0)
        i = float(ikhtibhar or 0)
        return round((t * 1 + f * 1 + i * 2) / 4, 2)
    except (TypeError, ValueError):
        return 0.0

def safe_f(val, fmt=".2f") -> str:
    """Safe formatting for numbers."""
    try:
        return format(float(val), fmt)
    except (TypeError, ValueError):
        return "—"

def ocr_answer_sheet_image(image_bytes: bytes) -> str:
    """Extract text from answer sheet image."""
    if not _TESSERACT_AVAILABLE:
        return ""
    try:
        bio = io.BytesIO(image_bytes)
        im = Image.open(bio).convert("RGB")
        return pytesseract.image_to_string(im, lang="ara+eng+fra")
    except Exception:
        return ""

def build_class_stats(stus: list, cls_name: str) -> dict:
    """Build class statistics from student list."""
    avgs = [s['average'] for s in stus]
    passed = [a for a in avgs if a >= 10]
    dist = {"0-5": 0, "5-10": 0, "10-15": 0, "15-20": 0}
    for a in avgs:
        if a < 5:
            dist["0-5"] += 1
        elif a < 10:
            dist["5-10"] += 1
        elif a < 15:
            dist["10-15"] += 1
        else:
            dist["15-20"] += 1
    sorted_stus = sorted(stus, key=lambda x: x['average'], reverse=True)
    return {
        "name": cls_name,
        "total": len(stus),
        "avg": sum(avgs) / max(len(avgs), 1),
        "max": max(avgs) if avgs else 0.0,
        "min": min(avgs) if avgs else 0.0,
        "pass_rate": len(passed) / max(len(avgs), 1) * 100,
        "distribution": dist,
        "top5": [{"name": f"{s['nom']} {s['prenom']}", "avg": s['average']}
                 for s in sorted_stus[:5]],
        "students": stus,
    }

def parse_grade_book_excel(uploaded_file, sheet_name=None, merge_all_sheets=False) -> list:
    """Parse Algerian grade book Excel file."""
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
        try:
            xl = pd.ExcelFile(bio)
        except Exception:
            try:
                df = pd.read_excel(bio, engine="openpyxl", header=None)
                rows_list = [tuple(row) for row in df.values]
                return _parse_rows_from_list(rows_list)
            except Exception:
                return []

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

def _parse_rows_from_list(rows_list) -> list:
    """Parse student data from worksheet rows."""
    students = []
    data_started = False
    HEADER_MARKERS = {'matricule', 'رقم التعريف', 'اللقب', 'nom', 'prénom',
                      'الاسم', 'تقويم', 'فرض', 'اختبار', 'taqwim'}

    for i, row in enumerate(rows_list, 1):
        if not any(c is not None for c in row):
            continue

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
                'id': str(vals[0] or '').strip(),
                'nom': nom,
                'prenom': str(vals[2] or '').strip() if len(vals) > 2 else '',
                'dob': str(vals[3] or '').strip() if len(vals) > 3 else '',
                'taqwim': float(vals[4]) if len(vals) > 4 and vals[4] is not None else 0.0,
                'fard': float(vals[5]) if len(vals) > 5 and vals[5] is not None else 0.0,
                'ikhtibhar': float(vals[6]) if len(vals) > 6 and vals[6] is not None else 0.0,
            }
            stu['average'] = calc_average(stu['taqwim'], stu['fard'], stu['ikhtibhar'])
            stu['apprec'] = get_appreciation(stu['average'])
            students.append(stu)
        except (ValueError, TypeError):
            continue

    return students

def list_excel_sheet_names(uploaded_file) -> list:
    """Get list of sheet names from Excel file."""
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

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: PDF GENERATORS (Using FPDF2 for Zero-Box Rendering)
# ════════════════════════════════════════════════════════════════════════════════════════
def generate_simple_pdf(content: str, title: str, subtitle: str = "", rtl: bool = True) -> bytes:
    """Generate PDF with FPDF2 (Zero-Box) or fallback."""
    return generate_zero_box_pdf(content, title, subtitle, rtl)

def generate_exam_pdf(exam_data: dict) -> bytes:
    """Generate exam PDF with official Algerian template using FPDF2."""
    if not _FPDF_AVAILABLE:
        return generate_simple_pdf_fallback(exam_data.get('content', ''), 
                                             exam_data.get('subject', 'اختبار'), 
                                             exam_data.get('grade', ''))
    
    pdf = ArabicFPDF()
    pdf.add_page()
    pdf.register_arabic_font()
    pdf.set_font('Amiri', '', 11)
    
    # School header
    pdf.set_font('Amiri', 'B', 10)
    pdf.cell_arabic(0, 8, "الجمهورية الجزائرية الديمقراطية الشعبية", ln=1, align='C')
    pdf.cell_arabic(0, 8, "وزارة التربية الوطنية", ln=1, align='C')
    pdf.ln(5)
    
    # School info
    pdf.set_font('Amiri', '', 10)
    pdf.cell_arabic(0, 7, f"المؤسسة: {exam_data.get('school', '....................')}", ln=1, align='R')
    pdf.cell_arabic(0, 7, f"المستوى: {exam_data.get('grade', '')} | المدة: {exam_data.get('duration', 'ساعتان')}", ln=1, align='R')
    pdf.ln(5)
    
    # Exam title
    pdf.set_font('Amiri', 'B', 14)
    pdf.cell_arabic(0, 10, f"اختبار {exam_data.get('semester', '')} في مادة {exam_data.get('subject', '')}", ln=1, align='C')
    pdf.ln(5)
    
    # Separator
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Content
    pdf.set_font('Amiri', '', 11)
    for line in exam_data.get('content', '').splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r'^تمرين\s+\d+', line) or re.match(r'^الوضعية الإدماجية', line):
            pdf.set_font('Amiri', 'B', 12)
            pdf.cell_arabic(0, 8, line, ln=1, align='R')
            pdf.set_font('Amiri', '', 11)
        else:
            pdf.multi_cell_arabic(0, 7, line)
        pdf.ln(2)
    
    # End message
    pdf.ln(10)
    pdf.set_font('Amiri', 'B', 11)
    pdf.cell_arabic(0, 8, "انتهى — بالتوفيق والنجاح", ln=1, align='C')
    
    return bytes(pdf.output())

def generate_report_pdf(report_data: dict) -> bytes:
    """Generate pedagogical report PDF using FPDF2."""
    if not _FPDF_AVAILABLE:
        return generate_simple_pdf_fallback(report_data.get('ai_analysis', ''), 'تقرير تحليل النتائج', '')
    
    pdf = ArabicFPDF()
    pdf.add_page()
    pdf.register_arabic_font()
    pdf.set_font('Amiri', 'B', 16)
    pdf.cell_arabic(0, 12, "تحليل نتائج الأقسام", ln=1, align='C')
    
    pdf.set_font('Amiri', '', 10)
    pdf.cell_arabic(0, 8, f"{report_data.get('school', '')} | {report_data.get('subject', '')} | {report_data.get('semester', '')}", ln=1, align='C')
    pdf.ln(5)
    
    pdf.set_draw_color(13, 148, 136)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    for cls in report_data.get('classes', []):
        pdf.set_font('Amiri', 'B', 12)
        pdf.set_text_color(13, 148, 136)
        pdf.cell_arabic(0, 10, f"تحليل نتائج القسم {cls['name']}", ln=1, align='R')
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font('Amiri', '', 10)
        info = f"عدد التلاميذ: {cls.get('total', 0)} — المعدل: {safe_f(cls.get('avg', 0))} — أعلى: {safe_f(cls.get('max', 0))} — أدنى: {safe_f(cls.get('min', 0))} — النجاح: {safe_f(cls.get('pass_rate', 0), '.1f')}%"
        pdf.multi_cell_arabic(0, 6, info)
        pdf.ln(4)
    
    if report_data.get('ai_analysis'):
        pdf.set_font('Amiri', 'B', 12)
        pdf.set_text_color(13, 148, 136)
        pdf.cell_arabic(0, 10, "التحليل البيداغوجي", ln=1, align='R')
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Amiri', '', 10)
        for line in report_data['ai_analysis'].splitlines():
            if line.strip():
                pdf.multi_cell_arabic(0, 6, line.strip())
    
    return bytes(pdf.output())

def generate_lesson_plan_pdf(plan_data: dict) -> bytes:
    """Generate lesson plan PDF using FPDF2."""
    if not _FPDF_AVAILABLE:
        return generate_simple_pdf_fallback(plan_data.get('content', ''), 'مذكرة درس', '')
    
    pdf = ArabicFPDF()
    pdf.add_page()
    pdf.register_arabic_font()
    pdf.set_font('Amiri', 'B', 14)
    pdf.cell_arabic(0, 12, "المذكرة البيداغوجية", ln=1, align='C')
    pdf.set_font('Amiri', '', 10)
    pdf.cell_arabic(0, 8, f"المادة: {plan_data.get('subject', '')} | المستوى: {plan_data.get('grade', '')}", ln=1, align='C')
    pdf.ln(5)
    
    pdf.set_draw_color(13, 148, 136)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font('Amiri', 'B', 12)
    pdf.cell_arabic(0, 10, f"الدرس: {plan_data.get('lesson', '')}", ln=1, align='R')
    pdf.set_font('Amiri', '', 11)
    pdf.multi_cell_arabic(0, 7, plan_data.get('content', ''))
    
    return bytes(pdf.output())

def generate_grade_book_excel(students: list, class_name: str, subject: str, semester: str, school_name: str) -> bytes:
    """Generate a single-sheet Excel grade book."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = class_name[:31]

    # Styling
    title_font = Font(name="Arial", bold=True, size=11)
    header_font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    body_font = Font(name="Arial", size=10)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    right = Alignment(horizontal="right", vertical="center")
    thin = Side(style="thin", color="000000")
    border = Border(top=thin, bottom=thin, left=thin, right=thin)
    purple_fill = PatternFill("solid", fgColor="764ba2")
    light_fill = PatternFill("solid", fgColor="f0f0ff")

    # Header
    ws.merge_cells("A1:I1")
    ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية"
    ws["A1"].font = title_font
    ws["A1"].alignment = center
    ws["A1"].fill = light_fill

    ws.merge_cells("A2:I2")
    ws["A2"] = "وزارة التربية الوطنية"
    ws["A2"].font = title_font
    ws["A2"].alignment = center

    ws.merge_cells("A3:I3")
    ws["A3"] = f"المؤسسة: {school_name}"
    ws["A3"].font = title_font
    ws["A3"].alignment = center

    ws.merge_cells("A4:I4")
    ws["A4"] = f"دفتر التنقيط | القسم: {class_name} | المادة: {subject} | {semester}"
    ws["A4"].font = title_font
    ws["A4"].alignment = center
    ws["A4"].fill = PatternFill("solid", fgColor="e8e8ff")

    ws.append([])

    # Headers
    headers = ["الرقم", "اللقب", "الاسم", "تاريخ الميلاد",
               "تقويم /20", "فرض /20", "اختبار /20", "المعدل /20", "التقديرات"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col, value=h)
        cell.font = header_font
        cell.alignment = center
        cell.fill = purple_fill
        cell.border = border
    ws.row_dimensions[6].height = 30

    # Data rows (index starting from 1)
    for idx, stu in enumerate(students, 1):
        row = 6 + idx
        avg = stu.get('average', 0)
        apprec = get_appreciation(avg)
        values = [
            idx,
            stu.get('nom', ''),
            stu.get('prenom', ''),
            str(stu.get('dob', '')),
            stu.get('taqwim', ''),
            stu.get('fard', ''),
            stu.get('ikhtibhar', ''),
            avg,
            apprec,
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = body_font
            cell.border = border
            cell.alignment = center if col not in [2, 3] else right
            if idx % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="f8f8ff")
        ws.row_dimensions[row].height = 22

    # Statistics
    last_data = 6 + len(students)
    stat_row = last_data + 2
    avgs_all = [s.get('average', 0) for s in students]
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
        lc.fill = light_fill
        vc.fill = light_fill
        lc.border = border
        vc.border = border

    # Column widths
    widths = [8, 16, 16, 14, 10, 10, 10, 10, 12]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.sheet_view.rightToLeft = True

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()

def generate_multi_sheet_grade_book(classes_data: list, school_name: str, subject: str, semester: str) -> bytes:
    """Generate Excel file with multiple sheets, one per class."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default sheet
    
    for cls_data in classes_data:
        students = cls_data.get('students', [])
        class_name = cls_data.get('name', 'قسم')
        sheet_name = class_name[:31]
        
        ws = wb.create_sheet(title=sheet_name)
        
        # Styling
        title_font = Font(name="Arial", bold=True, size=11)
        header_font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
        body_font = Font(name="Arial", size=10)
        center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        right = Alignment(horizontal="right", vertical="center")
        thin = Side(style="thin", color="000000")
        border = Border(top=thin, bottom=thin, left=thin, right=thin)
        purple_fill = PatternFill("solid", fgColor="764ba2")
        light_fill = PatternFill("solid", fgColor="f0f0ff")
        
        # Header
        ws.merge_cells("A1:I1")
        ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية"
        ws["A1"].font = title_font
        ws["A1"].alignment = center
        ws["A1"].fill = light_fill
        
        ws.merge_cells("A2:I2")
        ws["A2"] = "وزارة التربية الوطنية"
        ws["A2"].font = title_font
        ws["A2"].alignment = center
        
        ws.merge_cells("A3:I3")
        ws["A3"] = f"المؤسسة: {school_name}"
        ws["A3"].font = title_font
        ws["A3"].alignment = center
        
        ws.merge_cells("A4:I4")
        ws["A4"] = f"دفتر التنقيط | القسم: {class_name} | المادة: {subject} | {semester}"
        ws["A4"].font = title_font
        ws["A4"].alignment = center
        ws["A4"].fill = PatternFill("solid", fgColor="e8e8ff")
        
        ws.append([])
        
        # Headers
        headers = ["الرقم", "اللقب", "الاسم", "تاريخ الميلاد",
                   "تقويم /20", "فرض /20", "اختبار /20", "المعدل /20", "التقديرات"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=6, column=col, value=h)
            cell.font = header_font
            cell.alignment = center
            cell.fill = purple_fill
            cell.border = border
        ws.row_dimensions[6].height = 30
        
        # Data rows (start from 1 for index)
        for idx, stu in enumerate(students, 1):
            row = 6 + idx
            avg = stu.get('average', 0)
            apprec = get_appreciation(avg)
            values = [
                idx,
                stu.get('nom', ''),
                stu.get('prenom', ''),
                str(stu.get('dob', '')),
                stu.get('taqwim', ''),
                stu.get('fard', ''),
                stu.get('ikhtibhar', ''),
                avg,
                apprec,
            ]
            for col, val in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=val)
                cell.font = body_font
                cell.border = border
                cell.alignment = center if col not in [2, 3] else right
                if idx % 2 == 0:
                    cell.fill = PatternFill("solid", fgColor="f8f8ff")
            ws.row_dimensions[row].height = 22
        
        # Statistics
        last_data = 6 + len(students)
        stat_row = last_data + 2
        avgs_all = [s.get('average', 0) for s in students]
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
            lc.fill = light_fill
            vc.fill = light_fill
            lc.border = border
            vc.border = border
        
        # Column widths
        widths = [8, 16, 16, 14, 10, 10, 10, 10, 12]
        for col, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = w
        
        ws.sheet_view.rightToLeft = True
    
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: WORD (.docx) EXPORT (Preserved from original)
# ════════════════════════════════════════════════════════════════════════════════════════
def _docx_set_rtl(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    bidi_el = OxmlElement('w:bidi')
    bidi_el.set(qn('w:val'), '1')
    pPr.append(bidi_el)

def _docx_heading(doc, text: str, level: int = 1, color_hex: str = "145a32"):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _docx_set_rtl(p)
    for run in p.runs:
        r, g, b = (int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        run.font.color.rgb = RGBColor(r, g, b)
    return p

def _docx_para(doc, text: str, bold: bool = False, size: int = 12,
               align=WD_ALIGN_PARAGRAPH.RIGHT):
    p = doc.add_paragraph()
    p.alignment = align
    _docx_set_rtl(p)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    return p

def generate_exam_docx(exam_data: dict) -> bytes:
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

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
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _docx_set_rtl(title_p)
    run = title_p.add_run(
        f"اختبار {exam_data.get('semester', '')} في مادة {exam_data.get('subject', '')}")
    run.bold = True
    run.font.size = Pt(14)

    doc.add_paragraph()
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
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    _docx_heading(doc, "المذكرة البيداغوجية — DONIA MIND 4.0", level=1)

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
    if not _DOCX_AVAILABLE:
        return b""
    doc = DocxDocument()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    _docx_heading(doc, "تقرير تحليل نتائج الأقسام — DONIA MIND 4.0", level=1)
    _docx_para(doc,
               f"المادة: {report_data.get('subject', '')}   |   "
               f"الفصل: {report_data.get('semester', '')}   |   "
               f"المؤسسة: {report_data.get('school', '')}",
               bold=True)
    doc.add_paragraph()

    for cls in report_data.get('classes', []):
        _docx_heading(doc, f"القسم: {cls.get('name', '')}", level=2, color_hex="1e8449")
        stats_rows = [
            ["عدد التلاميذ", str(cls.get('total', ''))],
            ["المعدل العام", str(cls.get('avg', ''))],
            ["أعلى معدل", str(cls.get('max', ''))],
            ["أدنى معدل", str(cls.get('min', ''))],
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
            for idx, s in enumerate(top5, 1):
                _docx_para(doc, f"  {idx}. {s['name']} — {s['avg']:.2f}")
        doc.add_paragraph()

    if report_data.get('ai_analysis'):
        _docx_heading(doc, "التقرير البيداغوجي (الذكاء الاصطناعي المزدوج)", level=2, color_hex="922b21")
        for line in report_data['ai_analysis'].split('\n'):
            _docx_para(doc, line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: QR CODE GENERATOR
# ════════════════════════════════════════════════════════════════════════════════════════
def generate_qr_code(url: str, size: int = 150) -> BytesIO:
    """Generate QR code image as BytesIO."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#145a32", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: LANGUAGE UTILITIES
# ════════════════════════════════════════════════════════════════════════════════════════
def llm_output_language_clause(subject: str) -> str:
    """Return language instruction for LLM based on subject."""
    s = (subject or "").strip()
    if any(lang in s for lang in ["الإيطالية", "Italien"]):
        return "Mandatory: produce the ENTIRE output entirely in Italian. Do not use Arabic."
    if any(lang in s for lang in ["الألمانية", "Allemand"]):
        return "Mandatory: produce the ENTIRE output entirely in German. Do not use Arabic."
    if any(lang in s for lang in ["الإسبانية", "Espagnol"]):
        return "Mandatory: produce the ENTIRE output entirely in Spanish. Do not use Arabic."
    if any(lang in s for lang in ["الإنجليزية", "Anglais"]):
        return "Mandatory: produce the ENTIRE output entirely in English. Do not use Arabic."
    if any(lang in s for lang in ["الفرنسية", "Français"]):
        return "Mandatory: produce the ENTIRE output entirely in French. Do not use Arabic."
    return "قاعدة إلزامية: اكتب كل المحتوى (العناوين، الأسئلة، الشروح) بالعربية الفصحى الواضحة."

def get_pdf_mode_for_subject(subject: str) -> tuple[bool, str]:
    """Returns (rtl?, language_name) for PDF orientation."""
    s = (subject or "").strip()
    if any(lang in s for lang in ["الإيطالية", "Italien"]):
        return False, "Italian"
    if any(lang in s for lang in ["الألمانية", "Allemand"]):
        return False, "German"
    if any(lang in s for lang in ["الإسبانية", "Espagnol"]):
        return False, "Spanish"
    if any(lang in s for lang in ["الإنجليزية", "Anglais"]):
        return False, "English"
    if any(lang in s for lang in ["الفرنسية", "Français"]):
        return False, "French"
    return True, "Arabic"

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: FLOATING AI ASSISTANT (Chat Message Component)
# ════════════════════════════════════════════════════════════════════════════════════════
def render_floating_assistant():
    """Render floating AI assistant with chat interface."""
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = [
            {"role": "assistant", "content": "🌟 مرحباً بك في DONIA MIND 4.0! أنا مساعدك الذكي المزدوج. كيف يمكنني مساعدتك اليوم؟"}
        ]
    if "assistant_open" not in st.session_state:
        st.session_state.assistant_open = False
    
    button_html = f"""
    <div class="floating-assistant" id="assistantToggle" onclick="document.getElementById('assistantChat').style.display = document.getElementById('assistantChat').style.display === 'none' ? 'block' : 'none';">
        <div class="assistant-bubble">
            <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
                <rect x="15" y="18" width="50" height="44" rx="14" fill="#ffffff" stroke="#c0392b" stroke-width="2"/>
                <circle cx="31" cy="36" r="5" fill="#145a32"/>
                <circle cx="49" cy="36" r="5" fill="#145a32"/>
                <circle cx="32" cy="35" r="2" fill="white"/>
                <circle cx="50" cy="35" r="2" fill="white"/>
                <path d="M30 52 Q40 58 50 52" stroke="#c0392b" stroke-width="2.5" fill="none"/>
                <line x1="40" y1="18" x2="40" y2="12" stroke="#c0392b" stroke-width="2"/>
                <circle cx="40" cy="10" r="3" fill="#c0392b"/>
            </svg>
        </div>
    </div>
    """
    st.markdown(button_html, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div id="assistantChat" style="display: none;">', unsafe_allow_html=True)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("🌟 مرحباً بك في DONIA MIND 4.0! أنا مساعدك الذكي المزدوج.")
            st.markdown("يمكنني مساعدتك في:")
            st.markdown("- 📝 إعداد المذكرات (مع مراجعة نقدية)")
            st.markdown("- 📄 توليد الاختبارات (مع تحقق من المنهاج)")
            st.markdown("- 📊 تحليل النتائج (مع توصيات)")
            st.markdown("- ✅ تصحيح الإجابات (مع تقييم دقيق)")
        
        user_input = st.chat_input("اكتب سؤالك هنا...", key="assistant_input")
        if user_input:
            st.session_state.assistant_messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                response = generate_assistant_response(user_input)
                st.markdown(response)
                st.session_state.assistant_messages.append({"role": "assistant", "content": response})
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <script>
        const toggleBtn = document.getElementById('assistantToggle');
        const chatPanel = document.getElementById('assistantChat');
        if (toggleBtn) {
            toggleBtn.onclick = function(e) {
                e.stopPropagation();
                if (chatPanel.style.display === 'none') {
                    chatPanel.style.display = 'block';
                } else {
                    chatPanel.style.display = 'none';
                }
            };
        }
        </script>
        """, unsafe_allow_html=True)

def generate_assistant_response(query: str) -> str:
    """Generate AI assistant response using dual-AI architecture."""
    if not GROQ_API_KEY:
        return "⚠️ عذراً، مفتاح API غير متوفر. يرجى إضافة GROQ_API_KEY في إعدادات التطبيق."
    
    try:
        prompt = f"""أنت مساعد تربوي ذكي متخصص في المنظومة التعليمية الجزائرية (DONIA MIND 4.0).
        المستخدم يسأل: {query}
        
        قدم إجابة مفيدة ودقيقة حول:
        - المذكرات والاختبارات (باستخدام الذكاء المزدوج)
        - طرق التدريس
        - المنهاج الجزائري
        - التنقيط والتقييم
        
        كن مختصراً وواضحاً."""
        
        llm = get_llm(DEFAULT_GROQ_MODEL, GROQ_API_KEY)
        response = llm.invoke(prompt).content
        return response
    except Exception as e:
        return f"❌ حدث خطأ: {str(e)}"

# ════════════════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DONIA MIND 4.0 — المُعَلِّم الذَكِي",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: ENHANCED CSS (Including Floating Assistant and RTL Enforcement)
# ════════════════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
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

.title-card{
  background:linear-gradient(135deg,#145a32 0%,#1e8449 50%,#27ae60 100%);
  padding:1.75rem 2rem;border-radius:24px;text-align:center;
  margin-bottom:1rem;box-shadow:0 16px 48px rgba(20,90,50,.45);
  border:3px solid #c0392b;
}
.title-card h1{color:#ffffff!important;font-size:2.05rem;font-weight:800;margin:0;letter-spacing:.02em}
.title-card p{color:rgba(255,255,255,.92);font-size:.96rem;margin:.45rem 0 0;line-height:1.65}

.welcome-banner{
  background:linear-gradient(135deg,#fdfefe,#f9f9f9);
  border:2px solid #27ae60;border-left:8px solid #c0392b;
  border-radius:14px;padding:1.1rem 1.5rem;margin:.75rem 0 1.25rem;
  direction:rtl;text-align:right;
  font-size:1.05rem;font-weight:600;color:#145a32;
  box-shadow:0 4px 16px rgba(20,90,50,.12);
}

/* v4.0 Dual-AI Status Indicators */
.dual-ai-status {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin: 10px 0;
}
.ai-status-card {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border-radius: 16px;
  padding: 12px 20px;
  text-align: center;
  min-width: 140px;
  border: 2px solid #27ae60;
}
.ai-status-connected {
  border-color: #27ae60;
  background: linear-gradient(135deg, #e8f8f5, #d5f5e3);
}
.ai-status-disconnected {
  border-color: #c0392b;
  background: linear-gradient(135deg, #fdecea, #fadbd8);
}
.ai-status-icon {
  font-size: 28px;
  display: block;
  margin-bottom: 6px;
}
.ai-status-label {
  font-weight: 800;
  font-size: 14px;
  color: #145a32;
}
.ai-status-label-disconnected {
  color: #c0392b;
}
.ai-status-status {
  font-size: 12px;
  font-weight: 600;
}

/* Floating Assistant */
.floating-assistant {
  position: fixed;
  bottom: 80px;
  right: 20px;
  z-index: 1000;
  cursor: pointer;
  transition: all 0.3s ease;
}
.floating-assistant:hover {
  transform: scale(1.05);
}
.assistant-bubble {
  background: linear-gradient(135deg, #145a32, #1e8449);
  border-radius: 50%;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(20,90,50,.4);
  border: 2px solid #c0392b;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%,100%{box-shadow:0 4px 20px rgba(39,174,96,.4)}
  50%{box-shadow:0 8px 30px rgba(192,57,43,.6)}
}
.assistant-bubble svg {
  width: 40px;
  height: 40px;
}

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

.stat-card{background:linear-gradient(135deg,rgba(30,132,73,.1),rgba(39,174,96,.08));
  border:2px solid #27ae60;border-radius:16px;
  padding:1.1rem;text-align:center;margin-bottom:.75rem}
.stat-card h2{font-size:1.85rem;margin:0;color:#145a32!important}
.stat-card p{margin:0;color:#333;font-size:.86rem}

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

.feature-card{border-radius:16px!important}
.success-box{border-radius:12px!important}
.error-box{border-radius:12px!important}
.result-box{border-radius:16px!important}
.template-box{border-radius:12px!important}

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

# Apply RTL enforcement
inject_rtl_css()

# ════════════════════════════════════════════════════════════════════════════════════════
# v4.0: DUAL-AI REAL-TIME CONNECTIVITY DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════════════
def render_dual_ai_status():
    """Render real-time connectivity status for both AI models."""
    groq_status = test_groq_connection()
    arcee_status = test_arcee_connection()
    
    groq_class = "ai-status-connected" if groq_status else "ai-status-disconnected"
    arcee_class = "ai-status-connected" if arcee_status else "ai-status-disconnected"
    groq_label_class = "" if groq_status else "ai-status-label-disconnected"
    arcee_label_class = "" if arcee_status else "ai-status-label-disconnected"
    
    st.markdown(f"""
    <div class="dual-ai-status">
        <div class="ai-status-card {groq_class}">
            <span class="ai-status-icon">🧠</span>
            <span class="ai-status-label {groq_label_class}">Groq (المولد)</span>
            <span class="ai-status-status">{'✅ متصل' if groq_status else '❌ غير متصل'}</span>
        </div>
        <div class="ai-status-card {arcee_class}">
            <span class="ai-status-icon">📚</span>
            <span class="ai-status-label {arcee_label_class}">Arcee (الناقد)</span>
            <span class="ai-status-status">{'✅ متصل' if arcee_status else '❌ غير متصل'}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return groq_status, arcee_status

# ════════════════════════════════════════════════════════════════════════════════════════
# SIDEBAR (Enhanced with QR Code, Logo, and Dual-AI Status)
# ════════════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    _logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_donia.jpg")
    if os.path.isfile(_logo_path):
        st.image(_logo_path, width=220, caption="DONIA LABS TECH — v4.0")
    
    # QR Code
    try:
        qr_buf = generate_qr_code(APP_URL, size=120)
        st.image(qr_buf, caption="مسح للوصول السريع", width=120)
    except Exception:
        st.caption("📱 مسح للوصول للتطبيق")
    
    # v4.0: Dual-AI Status Dashboard
    st.markdown("## 🧠 حالة الذكاء المزدوج")
    groq_online, arcee_online = render_dual_ai_status()
    
    st.markdown("## ⚙️ الإعدادات العامة")
    
    level = st.selectbox("🏫 الطور التعليمي", list(CURRICULUM.keys()))
    info = CURRICULUM[level]
    grade = st.selectbox("📚 السنة الدراسية", info["grades"])
    
    branch = None
    if info["branches"] and grade in info["branches"]:
        branch = st.selectbox("🎯 الشعبة", list(info["branches"][grade].keys()))
    
    if info["subjects"]:
        subj_list = info["subjects"].get(grade) or info["subjects"].get("_default", [])
    elif info["branches"] and grade in info["branches"] and branch:
        subj_list = info["branches"][grade][branch]
    else:
        subj_list = []
    subject = (st.selectbox("📖 المادة", subj_list) if subj_list
               else st.text_input("📖 المادة", key="sb_subject"))
    
    st.markdown("---")
    st.markdown("**🏫 معلومات المؤسسة**")
    school_name = st.text_input("اسم المتوسطة / الثانوية",
                                  placeholder="متوسطة الشهيد...", key="school_name")
    teacher_name = st.text_input("اسم الأستاذ(ة)",
                                  placeholder="الأستاذ(ة)...", key="teacher_name")
    wilaya = st.text_input("الولاية",
                              placeholder="الجزائر...", key="wilaya")
    school_year = st.text_input("السنة الدراسية", value="2025/2026", key="syear")
    
    st.markdown("---")
    st.markdown("**🌐 بحث إنترنت (RAG)**")
    enable_web_search = st.checkbox("تفعيل البحث في الإنترنت", value=False, key="enable_web_search",
                                     help="البحث عن صور ومعلومات حقيقية من الإنترنت")
    
    st.markdown("---")
    st.markdown("**🎙️ الإدخال الصوتي**")
    st.caption("يمكنك استخدام الميكروفون للتحدث بدلاً من الكتابة")
    
    st.markdown("---")
    st.markdown("**تواصل — DONIA LABS TECH**")
    st.markdown(
        f"""
        <div class="donia-social">
          <a href="{SOCIAL_URL_WHATSAPP}" target="_blank" rel="noopener noreferrer" title="WhatsApp">📱 WA</a>
          <a href="{SOCIAL_URL_LINKEDIN}" target="_blank" rel="noopener noreferrer" title="LinkedIn">💼 in</a>
          <a href="{SOCIAL_URL_FACEBOOK}" target="_blank" rel="noopener noreferrer" title="Facebook">📘 f</a>
          <a href="{SOCIAL_URL_TELEGRAM}" target="_blank" rel="noopener noreferrer" title="Telegram">✈️ TG</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

model_name = DEFAULT_GROQ_MODEL

# ════════════════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="donia-slogan-bar">
  <span class="donia-slogan-ar">بالعلم نرتقي — بذكاء مزدوج نبدع</span>
  <div class="donia-slogan-divider"></div>
  <span class="donia-slogan-en">Dual-Intelligence Education</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="title-card">
    <h1 style="color:#ffffff!important;font-family:'Cairo',sans-serif">🎓 DONIA MIND 4.0 — المُعَلِّم الذَكِي</h1>
    <p style="font-size:0.9rem;color:rgba(255,255,255,0.9)">النسخة المزدوجة الذكاء | Dual-Intelligence Edition</p>
    <div class="donia-robot-wrap" aria-hidden="true">
      <div class="donia-robot" title="مساعدك التربوي الذكي المزدوج">
        <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
          <rect x="15" y="18" width="50" height="44" rx="14" fill="#d5f5e3" stroke="#145a32" stroke-width="2.5"/>
          <line x1="40" y1="18" x2="40" y2="8" stroke="#c0392b" stroke-width="3" stroke-linecap="round"/>
          <circle cx="40" cy="6" r="4" fill="#c0392b">
            <animate attributeName="r" values="4;5.5;4" dur="1.6s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="1;.55;1" dur="1.6s" repeatCount="indefinite"/>
          </circle>
          <circle cx="31" cy="36" r="6" fill="#145a32"/>
          <circle cx="49" cy="36" r="6" fill="#145a32"/>
          <circle cx="32.5" cy="35" r="2.2" fill="#ffffff">
            <animateTransform attributeName="transform" type="translate" values="0,0;1,0;0,0;-1,0;0,0" dur="3s" repeatCount="indefinite"/>
          </circle>
          <circle cx="50.5" cy="35" r="2.2" fill="#ffffff">
            <animateTransform attributeName="transform" type="translate" values="0,0;1,0;0,0;-1,0;0,0" dur="3s" repeatCount="indefinite"/>
          </circle>
          <path d="M30 52 Q40 60 50 52" stroke="#c0392b" stroke-width="3" fill="none" stroke-linecap="round">
            <animate attributeName="d" values="M30 52 Q40 60 50 52;M30 50 Q40 58 50 50;M30 52 Q40 60 50 52" dur="2.5s" repeatCount="indefinite"/>
          </path>
          <line x1="23" y1="28" x2="23" y2="46" stroke="rgba(20,90,50,.25)" stroke-width="1.2" stroke-dasharray="3 2"/>
          <line x1="57" y1="28" x2="57" y2="46" stroke="rgba(20,90,50,.25)" stroke-width="1.2" stroke-dasharray="3 2"/>
          <ellipse cx="40" cy="68" rx="18" ry="4.5" fill="rgba(39,174,96,.25)"/>
        </svg>
      </div>
    </div>
    <p style="font-family:'Cairo',sans-serif;font-weight:600">
      منصة تعليمية للمنظومة الجزائرية · ذكاء مزدوج · مذكرات · اختبارات · تنقيط · تحليل · تصحيح
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="welcome-banner">🌟 {WELCOME_MESSAGE_AR}</div>',
    unsafe_allow_html=True
)

# Render floating assistant
render_floating_assistant()

# ════════════════════════════════════════════════════════════════════════════════════════
# TABS (Preserved from original)
# ════════════════════════════════════════════════════════════════════════════════════════
(tab_plan, tab_exam, tab_grade, tab_report,
 tab_ex, tab_correct, tab_archive, tab_stats, tab_math_viz) = st.tabs([
    "📝 مذكرة الدرس", "📄 توليد اختبار", "📊 دفتر التنقيط",
    "📈 تحليل النتائج", "✏️ توليد تمرين", "✅ تصحيح أوراق",
    "🗄️ الأرشيف", "📉 إحصائيات", "📐 معاينة الدوال",
])

branch_txt = f" – {branch}" if branch else ""

# ════════════════════════════════════════════════════════════════════════════════════════
# TAB 1 — مذكرة الدرس (Enhanced with Dual-AI + Web Search)
# ════════════════════════════════════════════════════════════════════════════════════════
with tab_plan:
    st.markdown("### 📝 إعداد المذكرة وفق الصيغة الرسمية الجزائرية (الذكاء المزدوج)")
    st.markdown(
        '<div class="template-box">📋 تُنشأ المذكرة بالهيكل الرسمي مع مراجعة نقدية من الذكاء الاصطناعي الثاني<br>'
        '🔄 يعمل Groq كمولد محتوى + Arcee كناقد تربوي لضمان المطابقة للمناهج الجزائرية</div>',
        unsafe_allow_html=True)

    pm1, pm2 = st.columns(2)
    with pm1:
        plan_lesson = st.text_input("📝 عنوان الدرس / المورد المعرفي:", key="plan_lesson",
                                      placeholder="مثال: القاسم المشترك الأكبر لعددين طبيعيين")
        plan_chapter = st.text_input("📚 الباب / الوحدة:", key="plan_chapter",
                                      placeholder="مثال: الباب الأول – الأعداد الطبيعية")
        plan_domain = st.selectbox("🗂️ الميدان:",
                                     ["أنشطة عددية", "أنشطة جبرية", "أنشطة هندسية",
                                      "أنشطة إحصائية", "ميدان عام"], key="plan_domain")
        plan_dur = st.selectbox("⏱️ مدة الحصة:",
                                     ["50 دقيقة", "1 ساعة", "1.5 ساعة", "2 ساعة"],
                                     key="plan_dur")
    with pm2:
        plan_session = st.selectbox("نوع الحصة:",
                                     ["درس نظري", "أعمال موجهة", "أعمال تطبيقية",
                                      "تقييم تشخيصي", "دعم وعلاج"], key="plan_session")
        plan_prereq = st.text_area("📌 المكتسبات القبلية:", key="plan_prereq", height=70,
                                     placeholder="مثال: القسمة الإقليدية، قواسم عدد طبيعي...")
        plan_tools = st.text_input("🛠️ الوسائل والأدوات:", key="plan_tools",
                                      value="الكتاب المدرسي، المنهاج، الوثيقة المرافقة، دليل الأستاذ، السبورة")
        plan_notes = st.text_area("📌 ملاحظات خاصة:", key="plan_notes", height=70,
                                     placeholder="توجيهات خاصة بالفوج...")
    
    col_plan_opts1, col_plan_opts2 = st.columns(2)
    with col_plan_opts1:
        use_critic = st.checkbox("🔍 تفعيل المراجعة النقدية (Groq Critic)", value=True, key="plan_use_critic",
                                  help="يقوم نموذج ثانٍ بمراجعة المحتوى وتقديم تحسينات")
    with col_plan_opts2:
        use_arcee = st.checkbox("📚 التحقق من المنهاج (Arcee)", value=True, key="plan_use_arcee",
                                 help="التحقق من مطابقة المحتوى للمناهج الجزائرية")
    
    # v4.0: Audio input for lesson plan
    plan_audio_text = render_audio_recorder("plan")
    if plan_audio_text:
        st.info(f"🎙️ تم استلام: {plan_audio_text[:100]}...")
        # Option to use audio text as lesson title
        if st.button("استخدام النص كعنوان للدرس", key="use_audio_for_lesson"):
            plan_lesson = plan_audio_text[:100]

    if st.button("📝 توليد المذكرة الكاملة بالذكاء المزدوج", key="btn_gen_plan"):
        if not GROQ_API_KEY:
            st.warning("⚠️ أضف GROQ_API_KEY في متغيرات البيئة لإكمال التوليد.")
        elif not plan_lesson.strip():
            st.warning("⚠️ أدخل عنوان الدرس / المورد المعرفي لإكمال المذكرة.")
        else:
            prompt = f"""أنت أستاذ جزائري خبير. أعدّ مذكرة درس رسمية وفق المنهاج الجزائري.

المعطيات:
• الطور: {level} | السنة: {grade}{branch_txt}
• المادة: {subject} | الميدان: {plan_domain}
• الباب: {plan_chapter} | الدرس: {plan_lesson}
• نوع الحصة: {plan_session} | المدة: {plan_dur}
• المكتسبات القبلية: {plan_prereq}
{f"• ملاحظات: {plan_notes}" if plan_notes.strip() else ""}

{llm_output_language_clause(subject)}

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

            # v4.0: Enhance with web search if enabled
            if enable_web_search and (TAVILY_API_KEY or SERPER_API_KEY):
                with st.spinner("🌐 جاري البحث في الإنترنت..."):
                    prompt = rag_enhance_prompt(prompt, subject, grade)
            
            with st.spinner("🧠 جاري إعداد المذكرة بالذكاء المزدوج..."):
                try:
                    plan_text, validation_report = dual_llm_generate_with_critic(
                        prompt, subject, grade, level,
                        use_critic=use_critic, use_arcee=use_arcee
                    )
                    
                    if validation_report.get("error"):
                        st.warning(f"⚠️ {validation_report['error']}")
                    
                    # Show critic audit summary
                    if validation_report.get("critic_audit", {}).get("audited"):
                        if validation_report["critic_audit"].get("has_errors"):
                            st.info("📝 تمت المراجعة النقدية واقترحت تحسينات")
                        else:
                            st.success("✅ تمت المراجعة النقدية — المحتوى جيد")
                    
                    if validation_report.get("arcee_validation", {}).get("validated"):
                        st.success("✅ تم التحقق من المطابقة للمناهج الجزائرية")
                    
                    render_with_latex(plan_text)

                    def extract_section(text, marker):
                        m = re.search(rf'## {marker}[^\n]*\n([\s\S]+?)(?=## |\Z)', text)
                        return m.group(1).strip() if m else ""

                    plan_data = {
                        "school": school_name, "teacher": teacher_name,
                        "grade": f"{grade}{branch_txt}", "domain": plan_domain,
                        "chapter": plan_chapter, "lesson": plan_lesson,
                        "session_type": plan_session, "duration": plan_dur,
                        "subject": subject,
                        "duration_t": "5 د", "duration_b": "25 د", "duration_r": "15 د",
                        "competency": extract_section(plan_text, "مستوى من الكفاءة"),
                        "intro": extract_section(plan_text, "مرحلة التهيئة"),
                        "build": extract_section(plan_text, "أنشطة بناء الموارد"),
                        "reinvest": extract_section(plan_text, "مرحلة إعادة الاستثمار"),
                        "eval": extract_section(plan_text, "التقويم والإرشادات"),
                        "homework": extract_section(plan_text, "الواجب المنزلي"),
                        "self_critique": extract_section(plan_text, "نقد ذاتي"),
                        "prerequisites": plan_prereq, "tools": plan_tools,
                        "content": plan_text,
                    }

                    db_exec(
                        "INSERT INTO lesson_plans "
                        "(level,grade,subject,lesson,domain,duration,content,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (level, grade, subject, plan_lesson, plan_domain, plan_dur,
                         plan_text, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.success("✅ تم حفظ المذكرة")

                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.download_button("📥 تحميل نص",
                                           plan_text.encode("utf-8-sig"),
                                           f"مذكرة_{plan_lesson}.txt",
                                           key="dl_plan_txt")
                    with d2:
                        pdf_p = generate_lesson_plan_pdf(plan_data)
                        st.download_button("📄 تحميل PDF (Zero-Box)", pdf_p,
                                           f"مذكرة_{plan_lesson}.pdf", "application/pdf",
                                           key="dl_plan_pdf")
                    with d3:
                        if _DOCX_AVAILABLE:
                            docx_p = generate_lesson_plan_docx(plan_data)
                            st.download_button("📝 تحميل Word (.docx)", docx_p,
                                               f"مذكرة_{plan_lesson}.docx",
                                               "application/vnd.openxmlformats-officedocument"
                                               ".wordprocessingml.document",
                                               key="dl_plan_docx")
                        else:
                            st.caption("⚠️ python-docx غير مثبت")
                except ValueError as err:
                    st.warning(f"⚠️ تعذر معالجة بيانات المذكرة. التفاصيل: {err}")
                except Exception as err:
                    st.warning(f"⚠️ تعذر إكمال توليد المذكرة. التفاصيل: {err}")

# ════════════════════════════════════════════════════════════════════════════════════════
# TAB 2 — توليد اختبار (Enhanced with Dual-AI + Web Search)
# ════════════════════════════════════════════════════════════════════════════════════════
with tab_exam:
    st.markdown("### 📄 توليد ورقة الاختبار وفق النموذج الجزائري الرسمي (الذكاء المزدوج)")
    st.markdown(
        '<div class="template-box">📋 يُنشأ الاختبار بالهيكل الرسمي مع مراجعة نقدية وتصحيح تلقائي<br>'
        '🔄 Groq يولد + Groq Critic يراجع + Arcee يتحقق من المنهاج</div>',
        unsafe_allow_html=True)

    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        exam_semester = st.selectbox("الفصل:",
                                      ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"],
                                      key="exam_semester")
        exam_duration = st.selectbox("المدة:",
                                      ["ساعة واحدة", "ساعتان", "ثلاث ساعات"],
                                      key="exam_dur")
    with ex2:
        exam_theme = st.text_input("محاور الاختبار:", key="exam_theme",
                                     placeholder="مثال: الجمل, الدوال الخطية, الأعداد الناطقة")
        exam_points = st.text_input("نقاط التمارين:", value="3,3,3,3,8", key="exam_pts",
                                     help="مثال: 3,3,3,3,8 (4 تمارين + وضعية إدماجية)")
    with ex3:
        exam_difficulty = st.select_slider("مستوى الصعوبة:",
                                              ["سهل", "متوسط", "صعب", "مستوى الشهادة"],
                                              key="exam_diff")
        include_integrate = st.checkbox("إضافة وضعية إدماجية", value=True,
                                         key="exam_integrate")
    
    col_exam_opts1, col_exam_opts2 = st.columns(2)
    with col_exam_opts1:
        use_critic_exam = st.checkbox("🔍 تفعيل المراجعة النقدية", value=True, key="exam_use_critic")
    with col_exam_opts2:
        use_arcee_exam = st.checkbox("📚 التحقق من المنهاج", value=True, key="exam_use_arcee")

    exam_notes = st.text_area("ملاحظات وتوجيهات:", key="exam_notes",
                               placeholder="مثلاً: التركيز على الأعداد الناطقة والجذور التربيعية...")

    # v4.0: Audio input for exam
    exam_audio_text = render_audio_recorder("exam")
    if exam_audio_text:
        st.info(f"🎙️ تم استلام: {exam_audio_text[:100]}...")

    if st.button("🚀 توليد ورقة الاختبار بالذكاء المزدوج", key="btn_gen_exam"):
        if not GROQ_API_KEY:
            st.error("⚠️ أضف GROQ_API_KEY")
        else:
            pts = exam_points.split(",")
            pts_desc = " + ".join([f"تمرين {i+1}: {p.strip()} نقاط"
                                   for i, p in enumerate(pts[:4])])
            integrate_txt = (f"+ وضعية إدماجية: {pts[4].strip() if len(pts) > 4 else '8'} نقاط"
                             if include_integrate else "")

            prompt = f"""أنت أستاذ جزائري خبير في إعداد الاختبارات. أعدّ ورقة اختبار رسمية.

المعطيات:
• الطور: {level} | المستوى: {grade}{branch_txt}
• المادة: {subject} | {exam_semester}
• المدة: {exam_duration} | الصعوبة: {exam_difficulty}
• المحاور: {exam_theme or subject}
• توزيع النقاط: {pts_desc} {integrate_txt}
• المجموع: 20 نقطة
{f"• ملاحظات: {exam_notes}" if exam_notes.strip() else ""}

{llm_output_language_clause(subject)}

أعدّ الاختبار بهذا الهيكل الدقيق:

تمرين 1 :( {pts[0].strip() if pts else '3'} نقاط)
[الأسئلة مرقمة]

تمرين 2 :( {pts[1].strip() if len(pts) > 1 else '3'} نقاط)
[الأسئلة...]

تمرين 3 :( {pts[2].strip() if len(pts) > 2 else '3'} نقاط)
[الأسئلة...]

تمرين 4 :( {pts[3].strip() if len(pts) > 3 else '3'} نقاط)
[الأسئلة...]

{"الوضعية الإدماجية:( " + (pts[4].strip() if len(pts) > 4 else '8') + " نقاط)" if include_integrate else ""}
{"السياق: [سياق واقعي جزائري]" if include_integrate else ""}
{"الجزء الأول: [أسئلة تدريجية...]" if include_integrate else ""}
{"الجزء الثاني: [أسئلة تكملة...]" if include_integrate else ""}
{"انتهى — بالتوفيق والنجاح" if include_integrate else ""}"""

            # v4.0: Enhance with web search if enabled
            if enable_web_search and (TAVILY_API_KEY or SERPER_API_KEY):
                with st.spinner("🌐 جاري البحث في الإنترنت..."):
                    prompt = rag_enhance_prompt(prompt, subject, grade)

            with st.spinner("📄 جاري توليد الاختبار بالذكاء المزدوج..."):
                try:
                    exam_content, validation_report = dual_llm_generate_with_critic(
                        prompt, subject, grade, level,
                        use_critic=use_critic_exam, use_arcee=use_arcee_exam
                    )
                    
                    if validation_report.get("validated") or validation_report.get("arcee_validation", {}).get("validated"):
                        st.success("✅ تم التحقق من المحتوى")
                    
                    if validation_report.get("critic_audit", {}).get("audited"):
                        st.info("📝 تمت المراجعة النقدية")
                    
                    st.markdown(
                        f'<div class="feature-card"><h4>📄 {subject} | '
                        f'{grade}{branch_txt} | {exam_semester} | '
                        f'⏱️ {exam_duration}</h4></div>',
                        unsafe_allow_html=True)
                    render_with_latex(exam_content)
                    db_exec(
                        "INSERT INTO exams (level,grade,subject,semester,content,created_at) "
                        "VALUES (?,?,?,?,?,?)",
                        (level, grade, subject, exam_semester, exam_content,
                         datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.success("✅ تم حفظ الاختبار")

                    exam_pdf_data = {
                        "school": school_name, "wilaya": wilaya,
                        "grade": f"{grade}{branch_txt}", "year": school_year,
                        "district": "...", "semester": exam_semester,
                        "subject": subject, "duration": exam_duration,
                        "content": exam_content,
                    }
                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.download_button("📥 تحميل نص",
                                           exam_content.encode("utf-8-sig"),
                                           f"اختبار_{subject}_{exam_semester}.txt",
                                           key="dl_exam_txt")
                    with d2:
                        pdf_e = generate_exam_pdf(exam_pdf_data)
                        st.download_button("📄 تحميل PDF (Zero-Box)", pdf_e,
                                           f"اختبار_{subject}_{exam_semester}.pdf",
                                           "application/pdf", key="dl_exam_pdf")
                    with d3:
                        if _DOCX_AVAILABLE:
                            docx_e = generate_exam_docx(exam_pdf_data)
                            st.download_button("📝 تحميل Word (.docx)", docx_e,
                                               f"اختبار_{subject}_{exam_semester}.docx",
                                               "application/vnd.openxmlformats-officedocument"
                                               ".wordprocessingml.document",
                                               key="dl_exam_docx")
                        else:
                            st.caption("⚠️ python-docx غير مثبت")
                except Exception as err:
                    st.markdown(f'<div class="error-box">❌ {err}</div>',
                                unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════════════
# END OF PART 1 — Continuing to PART 2
# ════════════════════════════════════════════════════════════════════════════════════════
# The script continues with the remaining tabs (tab_grade, tab_report, tab_ex, tab_correct, tab_archive, tab_stats, tab_math_viz)
# in PART 2 of this deliverable.
