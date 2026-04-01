
# ╔══════════════════════════════════════════════════════════════════╗
# ║  PATCH FINAL v3 — أضف في آخر app.py تماماً                     ║
# ╚══════════════════════════════════════════════════════════════════╝

import sys as _sys
import glob as _glob


def _register_arabic_pdf_fonts():
    """
    نسخة v3 — تبحث في مسارات النظام أولاً (fonts-hosny-amiri / fonts-noto)
    ثم مجلدات المشروع ثم تحميل تلقائي كملاذ أخير.
    """
    global _AR_FONT_MAIN, _AR_FONT_BOLD, _AR_FONTS_TRIED
    if _AR_FONTS_TRIED:
        return
    _AR_FONTS_TRIED = True

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ══════════════════════════════════════════════════════
    # 1) مسارات خطوط النظام (Streamlit Cloud = Ubuntu/Debian)
    #    تُثبَّت بـ packages.txt: fonts-hosny-amiri / fonts-noto-core
    # ══════════════════════════════════════════════════════
    system_font_dirs = [
        "/usr/share/fonts/truetype/hosny-amiri",   # fonts-hosny-amiri ← Amiri
        "/usr/share/fonts/truetype/noto",          # fonts-noto-core   ← NotoSansArabic
        "/usr/share/fonts/opentype/hosny-amiri",
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/opentype",
        "/usr/share/fonts",
    ]

    # 2) مسارات المشروع
    project_dirs = [
        base_dir,
        os.path.join(base_dir, "fonts"),
        os.path.join(base_dir, "assets"),
        os.path.join(base_dir, "assets", "fonts"),
        "/app",
        "/app/app",
        os.getcwd(),
        os.path.join(os.getcwd(), "fonts"),
    ] + [p for p in _sys.path if p]

    all_search_dirs = system_font_dirs + project_dirs

    def _find_file(fname):
        """ابحث عن الملف في كل المسارات."""
        for d in all_search_dirs:
            p = os.path.join(d, fname)
            if os.path.isfile(p) and os.path.getsize(p) > 8_000:
                return p
        # بحث بـ glob في مجلدات النظام (قد يكون اسم المجلد مختلفاً)
        for pattern in [
            f"/usr/share/fonts/**/{fname}",
            f"/usr/local/share/fonts/**/{fname}",
        ]:
            results = _glob.glob(pattern, recursive=True)
            if results:
                return results[0]
        return None

    def _find_any_arabic_font():
        """
        إذا لم يُعثر على Amiri تحديداً، ابحث عن أي خط عربي متاح
        (NotoNaskhArabic، Scheherazade، DejaVu... إلخ)
        """
        arabic_font_names = [
            "NotoNaskhArabic-Regular.ttf",
            "NotoSansArabic-Regular.ttf",
            "Scheherazade-Regular.ttf",
            "ScheherazadeNew-Regular.ttf",
        ]
        for fname in arabic_font_names:
            p = _find_file(fname)
            if p:
                return p, os.path.splitext(fname)[0]
        # بحث بـ glob عن أي خط نوتو عربي
        for pattern in [
            "/usr/share/fonts/**/Noto*Arabic*.ttf",
            "/usr/share/fonts/**/Amiri*.ttf",
        ]:
            results = _glob.glob(pattern, recursive=True)
            if results:
                fname = os.path.basename(results[0])
                label = os.path.splitext(fname)[0].replace(" ", "_")
                return results[0], label
        return None, None

    def _download_font(fname, url, dest_dir):
        """تحميل احتياطي من الإنترنت."""
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, fname)
        if os.path.isfile(dest) and os.path.getsize(dest) > 8_000:
            return dest
        try:
            urllib.request.urlretrieve(url, dest)
            if os.path.isfile(dest) and os.path.getsize(dest) > 8_000:
                return dest
        except Exception:
            pass
        return None

    # ══════════════════════════════════════════════════════
    # قائمة الخطوط بالترتيب الأفضل
    # ══════════════════════════════════════════════════════
    FONT_LIST = [
        (
            "Amiri", "Amiri-Regular.ttf",
            "https://raw.githubusercontent.com/googlefonts/amiri/main/fonts/ttf/Amiri-Regular.ttf",
        ),
        (
            "Amiri-Bold", "Amiri-Bold.ttf",
            "https://raw.githubusercontent.com/googlefonts/amiri/main/fonts/ttf/Amiri-Bold.ttf",
        ),
    ]

    registered = []

    for label, fname, url in FONT_LIST:
        font_path = _find_file(fname)
        if not font_path:
            # محاولة تحميل
            font_path = _download_font(fname, url, os.path.join(base_dir, "fonts"))
        if font_path:
            try:
                pdfmetrics.registerFont(TTFont(label, font_path))
                registered.append(label)
            except Exception:
                pass

    # إذا لم يُسجَّل شيء → ابحث عن أي خط عربي على النظام
    if not registered:
        fallback_path, fallback_label = _find_any_arabic_font()
        if fallback_path and fallback_label:
            try:
                pdfmetrics.registerFont(TTFont(fallback_label, fallback_path))
                registered.append(fallback_label)
                registered.append(fallback_label)  # للـ Bold أيضاً
            except Exception:
                pass

    # ══════════════════════════════════════════════════════
    # اختر أفضل خط متاح
    # ══════════════════════════════════════════════════════
    if "Amiri" in registered:
        _AR_FONT_MAIN = "Amiri"
        _AR_FONT_BOLD = "Amiri-Bold" if "Amiri-Bold" in registered else "Amiri"
    elif registered:
        _AR_FONT_MAIN = registered[0]
        _AR_FONT_BOLD = registered[1] if len(registered) > 1 else registered[0]
    # إذا فشل كل شيء → Helvetica (مربعات) — لكن هذا لن يحدث مع packages.txt


# ══════════════════════════════════════════════════════════
# إعادة تسجيل فوري عند بدء التطبيق
# ══════════════════════════════════════════════════════════
_AR_FONTS_TRIED = False
_STYLES_CACHE.clear()
_register_arabic_pdf_fonts()
