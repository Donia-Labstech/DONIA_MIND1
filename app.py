input("عدد التلاميذ", min_value=1, max_value=50, value=30)

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
        ├── assets/
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
