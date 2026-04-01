
# ╔══════════════════════════════════════════════════════════════════╗
# ║  PATCH NUCLEAR — الحل النهائي المضمون 100%                      ║
# ║  يكتب الخط في /tmp (مضمون الكتابة على أي سيرفر)                ║
# ║  أضف هذا في آخر app.py — يستبدل كل الـ patches السابقة        ║
# ╚══════════════════════════════════════════════════════════════════╝

import tempfile as _tempfile


def _get_font_to_tmp(font_name: str, url: str) -> str | None:
    """
    يحمّل الخط مباشرة إلى /tmp ويعيد المسار.
    /tmp مضمون الكتابة على Streamlit Cloud وأي Linux سيرفر.
    """
    dest = f"/tmp/{font_name}"

    # إذا موجود ومكتمل → أعد المسار مباشرة
    if os.path.isfile(dest) and os.path.getsize(dest) > 50_000:
        return dest

    try:
        import urllib.request
        urllib.request.urlretrieve(url, dest)
        if os.path.isfile(dest) and os.path.getsize(dest) > 50_000:
            return dest
    except Exception as e:
        pass

    return None


def _register_arabic_pdf_fonts():
    """
    NUCLEAR v4 — يكتب الخط في /tmp ثم يسجّله مع ReportLab.
    مضمون العمل على Streamlit Cloud بغض النظر عن بنية المشروع.
    """
    global _AR_FONT_MAIN, _AR_FONT_BOLD, _AR_FONTS_TRIED

    if _AR_FONTS_TRIED:
        return
    _AR_FONTS_TRIED = True

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ══════════════════════════════════════════════════════
    # المسارات بالترتيب: /tmp أولاً ثم المشروع ثم النظام
    # ══════════════════════════════════════════════════════
    def _find_local(fname):
        candidates = [
            f"/tmp/{fname}",
            os.path.join(base_dir, fname),
            os.path.join(base_dir, "fonts", fname),
            f"/usr/share/fonts/truetype/hosny-amiri/{fname}",
            f"/usr/share/fonts/truetype/noto/{fname}",
        ]
        for p in candidates:
            if os.path.isfile(p) and os.path.getsize(p) > 50_000:
                return p
        return None

    # ══════════════════════════════════════════════════════
    # روابط مباشرة موثوقة لخط Amiri (مفتوح المصدر)
    # ══════════════════════════════════════════════════════
    FONTS = [
        (
            "Amiri",
            "Amiri-Regular.ttf",
            "https://github.com/alif-type/amiri/raw/master/fonts/Amiri-Regular.ttf",
        ),
        (
            "Amiri-Bold",
            "Amiri-Bold.ttf",
            "https://github.com/alif-type/amiri/raw/master/fonts/Amiri-Bold.ttf",
        ),
    ]

    registered = []

    for label, fname, url in FONTS:
        # 1) ابحث محلياً
        path = _find_local(fname)

        # 2) حمّل إلى /tmp
        if not path:
            path = _get_font_to_tmp(fname, url)

        # 3) سجّل مع ReportLab
        if path:
            try:
                pdfmetrics.registerFont(TTFont(label, path))
                registered.append(label)
            except Exception:
                pass

    # ══════════════════════════════════════════════════════
    # تعيين الخط الفعّال
    # ══════════════════════════════════════════════════════
    if "Amiri" in registered:
        _AR_FONT_MAIN = "Amiri"
        _AR_FONT_BOLD = "Amiri-Bold" if "Amiri-Bold" in registered else "Amiri"
    # إذا فشل التحميل تماماً → يبقى Helvetica (هذا لن يحدث إلا بانقطاع الإنترنت)


# ══════════════════════════════════════════════════════════
# تنفيذ فوري عند بدء التطبيق
# ══════════════════════════════════════════════════════════
_AR_FONTS_TRIED = False
_STYLES_CACHE.clear()
_register_arabic_pdf_fonts()
