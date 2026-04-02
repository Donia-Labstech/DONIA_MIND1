
# ╔══════════════════════════════════════════════════════════════════╗
# ║  PATCH FINAL v5 — الحل النهائي الحقيقي                         ║
# ║  يستخدم @st.cache_resource لتسجيل الخط مرة واحدة فقط           ║
# ║  احذف كل الـ patches السابقة والصق هذا وحده في آخر app.py      ║
# ╚══════════════════════════════════════════════════════════════════╝

import glob as _glob
import sys as _sys


@st.cache_resource
def _load_and_register_arabic_fonts():
    """
    يعمل مرة واحدة فقط طوال عمر السيرفر — محفوظ في ذاكرة Streamlit.
    يبحث في النظام أولاً ثم يحمّل إلى /tmp.
    """

    # ── كل المسارات المحتملة ──────────────────────────────────────
    base_dir = os.path.dirname(os.path.abspath(__file__))

    def _find(fname):
        # 1) /tmp أولاً (أسرع)
        tmp = f"/tmp/{fname}"
        if os.path.isfile(tmp) and os.path.getsize(tmp) > 50_000:
            return tmp
        # 2) مسارات المشروع
        for d in [base_dir,
                  os.path.join(base_dir, "fonts"),
                  os.path.join(base_dir, "assets"),
                  os.path.join(base_dir, "assets", "fonts"),
                  "/app", "/app/app", os.getcwd(),
                  os.path.join(os.getcwd(), "fonts")]:
            p = os.path.join(d, fname)
            if os.path.isfile(p) and os.path.getsize(p) > 50_000:
                return p
        # 3) خطوط النظام (packages.txt → fonts-hosny-amiri)
        for pat in [f"/usr/share/fonts/**/{fname}",
                    f"/usr/local/share/fonts/**/{fname}"]:
            hits = _glob.glob(pat, recursive=True)
            if hits:
                return hits[0]
        return None

    def _download(fname, urls):
        dest = f"/tmp/{fname}"
        for url in urls:
            try:
                urllib.request.urlretrieve(url, dest)
                if os.path.isfile(dest) and os.path.getsize(dest) > 50_000:
                    return dest
            except Exception:
                continue
        return None

    # ── روابط موثوقة لكل خط (بديلات متعددة) ─────────────────────
    FONTS = [
        ("Amiri", "Amiri-Regular.ttf", [
            "https://github.com/alif-type/amiri/raw/master/fonts/Amiri-Regular.ttf",
            "https://cdn.jsdelivr.net/gh/alif-type/amiri@master/fonts/Amiri-Regular.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Regular.ttf",
        ]),
        ("Amiri-Bold", "Amiri-Bold.ttf", [
            "https://github.com/alif-type/amiri/raw/master/fonts/Amiri-Bold.ttf",
            "https://cdn.jsdelivr.net/gh/alif-type/amiri@master/fonts/Amiri-Bold.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Bold.ttf",
        ]),
    ]

    results = {}  # {"Amiri": "/tmp/Amiri-Regular.ttf", ...}

    for label, fname, urls in FONTS:
        path = _find(fname)
        if not path:
            path = _download(fname, urls)
        if path:
            try:
                pdfmetrics.registerFont(TTFont(label, path))
                results[label] = path
            except Exception:
                pass

    return results   # يُعاد استخدام هذا الناتج في كل مكان


def _apply_arabic_font_patch():
    """
    يُطبّق نتيجة التسجيل على المتغيرات العالمية.
    يُستدعى مرة واحدة عند بدء التطبيق.
    """
    global _AR_FONT_MAIN, _AR_FONT_BOLD, _STYLES_CACHE

    registered = _load_and_register_arabic_fonts()

    if not registered:
        return  # فشل كل شيء → Helvetica يبقى

    if "Amiri" in registered:
        _AR_FONT_MAIN = "Amiri"
        _AR_FONT_BOLD = "Amiri-Bold" if "Amiri-Bold" in registered else "Amiri"
    elif registered:
        first = list(registered.keys())[0]
        _AR_FONT_MAIN = first
        _AR_FONT_BOLD = first

    # أعد بناء كاش الأنماط بالخط الجديد
    _STYLES_CACHE.clear()
    # سجّل الأنماط فوراً
    make_pdf_styles(True)
    make_pdf_styles(False)


# ══════════════════════════════════════════════════════════
# تنفيذ فوري عند تحميل التطبيق
# ══════════════════════════════════════════════════════════
_apply_arabic_font_patch()
