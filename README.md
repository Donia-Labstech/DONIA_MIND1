# DONIA MIND v6.0 — إصلاح العربية + الهوية البصرية (الشعار والموقع)
# Arabic Fix + Branding (Logo & Website) Update

## ملخص بسيط / Quick summary

هذا التحديث يحتوي على شيئين مدمجين في نسخة واحدة:
1. **إصلاح خلل العربية** (نفس الإصلاح المُختبَر في الجلسة السابقة، مُطبَّق الآن على
   النسخة الأحدث من `app.py`).
2. **إضافة الشعار + الموقع الرسمي** في الواجهة والمستندات المُصدَّرة.

This update bundles two things into one tested release:
1. **The Arabic font fix** (same fix verified in the previous session, now
   applied to the newer `app.py` you uploaded).
2. **Logo + official website branding**, added to the UI and to exported
   documents.

---

## 1) إصلاح العربية / Arabic Fix (unchanged from before)

نفس السبب الجذري: لا يوجد خط مضمّن في المستودع، فيعتمد التطبيق على تنزيل
الخط وقت التشغيل، وهذا يفشل غالبًا على Streamlit Cloud.

Same root cause as before: no font bundled in the repo, so the app relied on
a runtime download that frequently fails on Streamlit Cloud. Fixed by:
- `fonts/Amiri-Regular.ttf` + `fonts/Amiri-Bold.ttf` bundled directly in the repo
- `ArabicFPDF.__init__` checks this bundled path **first**, before any
  network call
- `ensure_font_files()` skips the network round-trip entirely when the
  bundle is present
- DOCX generation now also sets `w:rFonts/w:cs="Amiri"` on every Arabic run,
  not just the RTL flag
- `packages.txt` added so Streamlit Cloud installs FreeSans/Noto as a real
  system-level backup tier (previously expected but never actually installed)

**Verified again in this session** against the new `app.py`: bundled-font
PDF generation tested with network calls deliberately blocked — passes.
DOCX RTL + complex-script font tested at the XML level — passes.

---

## 2) الهوية البصرية الجديدة / New Branding

### الشعار / Logo — `assets/logo_donia.jpg`

ملاحظة مهمة: الكود الأصلي كان **يتوقع بالفعل** وجود شعار على المسار
`assets/logo_donia.jpg` — لكن الملف لم يكن موجودًا في المستودع، فلم يظهر أي
شعار من الأساس (الشرط `if os.path.isfile(...)` يفشل بصمت). المشكلة كانت ملفًا
ناقصًا، لا خللًا في المنطق.

Important: the original code **already expected** a logo at
`assets/logo_donia.jpg` — it just wasn't in the repo, so nothing showed up
(`if os.path.isfile(...)` silently does nothing when the file is missing).
This was a missing file, not broken logic.

**التصميم / Design decision:** الشعار الأصلي مصمَّم لخلفية سوداء بالكامل
(توهجات نيون، نجمة لامعة). وضعه مباشرة فوق الشريط الجانبي ذو الخلفية الفاتحة
(أخضر فاتح) كان سيظهر كصندوق أسود غير مرغوب. الحل: إطار دائري داكن مُصمَّم
خصيصًا (`donia-logo-frame` في CSS) يُحوّل الخلفية السوداء إلى "بادج" مقصود
بدل أن تبدو كخطأ.

The logo's full-black background would look like a rendering glitch if
dropped directly onto the light-green sidebar. Fix: a dedicated dark rounded
frame (`.donia-logo-frame` in the CSS) turns the black background into an
intentional badge treatment instead.

### الموقع الرسمي / Official website

`donialabstech.online` تمت إضافته في:
- متغير جديد `WEBSITE_URL` (قابل للتعديل عبر `.env` بمتغير `DONIA_WEBSITE_URL`)
- الشريط الجانبي: رابط أسفل الشعار + ضمن قسم "تواصل"
- تذييل الصفحة الرئيسي (Footer)
- **داخل كل مستند PDF مُصدَّر** (عبر `COPYRIGHT_FOOTER_AR` المُحدَّث)
- **داخل كل مستند DOCX مُصدَّر** (دالة جديدة `_docx_add_footer()` تمت إضافتها
  لثلاثة مولّدات DOCX التي لم يكن لديها أي تذييل أصلاً: الاختبار، المذكرة
  البيداغوجية، التقرير)

Added in: a new `WEBSITE_URL` constant (overridable via `.env`), the
sidebar (under the logo + in the "تواصل" contact block), the page footer,
and — this is the part that needed real code, not just a constant — **every
exported PDF and DOCX document now carries it too**. The three DOCX
generators (`generate_exam_docx`, `generate_lesson_plan_docx`,
`generate_report_docx`) previously had **no footer at all**; a new shared
`_docx_add_footer()` helper was added and wired into all three.

---

## التعديلات الدقيقة في app.py / Exact code changes

| # | الموقع / Location | التغيير / Change |
|---|---|---|
| 1 | `ArabicFPDF.__init__` | Bundled-font priority tier (Arabic fix) |
| 2 | `ensure_font_files()` | Skip network when bundle exists (Arabic fix) |
| 3 | `_docx_set_complex_font()` (new) | `w:cs` font for DOCX Arabic runs (Arabic fix) |
| 4 | `_docx_heading`, `_docx_para` | Wired to use #3 (Arabic fix) |
| 5 | `WEBSITE_URL` (new constant) | Official website, env-overridable (branding) |
| 6 | `COPYRIGHT_FOOTER_AR` | Website appended to existing copyright line (branding) |
| 7 | Sidebar logo block | Reads real `assets/logo_donia.jpg`, dark-frame CSS treatment, website link under it (branding) |
| 8 | Sidebar "تواصل" block | Website link added alongside WhatsApp/LinkedIn/Facebook/Telegram (branding) |
| 9 | Page footer | Website link added (branding) |
| 10 | `_docx_add_footer()` (new) | Shared footer helper (branding) |
| 11 | `generate_exam_docx`, `generate_lesson_plan_docx`, `generate_report_docx` | Now call #10 before saving (branding) |
| 12 | CSS block | New `.donia-logo-frame` and `.donia-website-link` classes (branding) |

**لم يتم حذف أي ميزة موجودة.** كل التعديلات إضافية بالكامل.
**No existing feature was removed.** All changes are additive.

---

## ما الذي أُثبت فعليًا في هذه الجلسة / What was actually verified this session

- ✅ تثبيت `requirements.txt` بالكامل في بيئة نظيفة — **بدون أي تعارض بين
  المكتبات** (تم تنفيذه فعليًا، ليس افتراضًا)
- ✅ استيراد `app.py` الكامل (5000+ سطر) في تلك البيئة — **تنفيذ كل الكود على
  مستوى الموديول بدون أي استثناء (exception)**، بما في ذلك تحميل الشعار،
  بناء الواجهة، التذييل
- ✅ توليد PDF فعلي بالخط المُضمَّن مع حظر الشبكة عمدًا — يعمل
- ✅ توليد DOCX فعلي يحتوي على `w:bidi` و `w:cs="Amiri"` و رابط الموقع في
  XML الناتج — تم فحصه مباشرة
- ✅ معاينة بصرية للشعار داخل إطاره الجديد فوق خلفية الشريط الجانبي الفعلية

**Verified, not assumed**, in this session:
- Full `requirements.txt` installs cleanly with zero conflicts (actually run)
- Full `app.py` module-level code executes with zero exceptions in that
  environment (actually run)
- PDF generation with bundled font, network blocked — works
- DOCX output contains `w:bidi`, `w:cs="Amiri"`, and the website URL in the
  raw XML — checked directly
- Visual mockup of the logo in its new frame against the real sidebar
  background color

### ما لم يُثبت / What's not provable from here
لا يمكنني تشغيل Streamlit Cloud الفعلي من هنا. التوصية: بعد الرفع، اعمل
**Reboot app** (لا redeploy عادي) من Manage app، لأن `packages.txt` يحتاج
إعادة بناء كاملة.

I can't run your actual Streamlit Cloud deployment from here. After
uploading, use **Manage app → Reboot app** (not a normal redeploy), since
`packages.txt` needs a full environment rebuild to take effect.

---

## كيفية النشر / Deployment steps

1. استبدل `app.py` بالنسخة الجديدة في مستودعك على GitHub.
2. أضف مجلد `fonts/` (يحتوي ملفي الخط) في جذر المستودع، بجانب `app.py`.
3. أضف مجلد `assets/` (يحتوي `logo_donia.jpg`) في جذر المستودع.
4. أضف/استبدل `requirements.txt` و `packages.txt` في الجذر.
5. ارفع (commit + push).
6. على Streamlit Cloud: **Manage app → Reboot app**.
7. تحقق: افتح التطبيق، تأكد من ظهور الشعار في الشريط الجانبي، ثم صدّر اختبارًا
   PDF وملف Word وتأكد من ظهور النص العربي بشكل صحيح ووجود رابط الموقع.

---

## تخصيص إضافي (اختياري) / Optional further customization

- لتغيير رابط الموقع بدون تعديل الكود: أضف `DONIA_WEBSITE_URL=...` في ملف
  `.env` أو في أسرار Streamlit Cloud (Secrets).
- لتغيير حجم الشعار في الشريط الجانبي: عدّل `width="180"` في سطر
  `<img src="data:image/jpeg;base64,...">`.
