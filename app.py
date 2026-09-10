import base64
import os
import shutil
import streamlit as st
import qrcode
from PIL import Image

# إعداد إعدادات الصفحة وإغلاق أي شريط جانبي افتراضياً
st.set_page_config(
    page_title="نظام أرشيف المستندات",
    layout="wide",
    page_icon="🗂️",
    initial_sidebar_state="collapsed",
)

# إعداد المجلد الرئيسي للمستندات
BASE_DOCS_DIR = "documents"
if not os.path.exists(BASE_DOCS_DIR):
  os.makedirs(BASE_DOCS_DIR)

# --- 1. رأس الصفحة والعنوان (أول شيء يظهر للعامة) ---
st.title("🗂️ بوابة استعراض وطباعة المستندات")
st.markdown(
    "مرحباً بك. يمكنك تصفح المستندات مقسمة حسب الأقسام، ومعاينتها أو تحميلها"
    " مباشرة."
)
st.divider()

# --- 2. اختيار القسم أولاً ---
st.header("📂 أقسام المستندات")

categories = [
    d
    for d in os.listdir(BASE_DOCS_DIR)
    if os.path.isdir(os.path.join(BASE_DOCS_DIR, d))
]

if not categories:
  st.info(
      "لا توجد أقسام أو مستندات مرفوعة حالياً. (يمكن للمدير رفع ملفات من لوحة"
      " التحكم بالأسفل)."
  )
else:
  selected_category = st.selectbox("اختر القسم لعرض مستنداته:", categories)

  cat_path = os.path.join(BASE_DOCS_DIR, selected_category)
  files = [
      f
      for f in os.listdir(cat_path)
      if os.path.isfile(os.path.join(cat_path, f))
  ]

  # خانة البحث
  search_query = st.text_input(
      f"بحث في قسم ({selected_category}):", placeholder="اكتب اسم المستند..."
  )

  filtered_files = [
      f for f in files if search_query.lower() in f.lower()
  ]

  if filtered_files:
    st.write(f"المستندات المتوفرة في قسم **{selected_category}**:")

    for file_name in filtered_files:
      file_path = os.path.join(cat_path, file_name)

      col1, col2, col3 = st.columns([3, 1, 1])
      with col1:
        st.markdown(f"📄 **{file_name}**")

      with col2:
        with open(file_path, "rb") as f:
          st.download_button(
              label="تحميل",
              data=f,
              file_name=file_name,
              mime="application/octet-stream",
              key=f"dl_{selected_category}_{file_name}",
          )

      with col3:
        preview_key = f"preview_{selected_category}_{file_name}"
        show_preview = st.button("👁️ معاينة", key=preview_key)

      # --- عرض المعاينة بطريقة ذكية وآمنة داخل الصفحة ---
      if st.session_state.get(f"state_{preview_key}", False):
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border: 1px solid #ccc; margin-top: 10px; margin-bottom: 15px;">
                <h4 style="color: #333; margin-top: 0;">🔍 معاينة المستند: {file_name}</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ext = file_name.split(".")[-1].lower()
        if ext in ["png", "jpg", "jpeg"]:
          st.image(file_path, caption=file_name, use_container_width=True)
        elif ext == "pdf":
          file_size = os.path.getsize(file_path)
          if file_size > 0:
            with open(file_path, "rb") as pdf_file:
              b64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")

            # عرض عارض آمن يتيح الطباعة والعرض بدون قيود الـ iframe التقليدي
            st.markdown(
                f"""
                <div style="text-align: center; padding: 20px; background: white; border-radius: 8px; border: 1px dashed #ff4b4b;">
                    <p style="font-weight: bold; color: #333;">ملف PDF جاهز للعرض والطباعة المباشرة:</p>
                    <embed src="data:application/pdf;base64,{b64_pdf}" width="100%" height="500px" type="application/pdf">
                    <br><br>
                    <a href="data:application/pdf;base64,{b64_pdf}" target="_blank" style="
                        padding: 0.5em 1.2em;
                        background-color: #ff4b4b;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                    ">🖨️ فتح المستند بشاشة كاملة للطباعة</a>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("❌ إغلاق المعاينة", key=f"close_{preview_key}"):
          st.session_state[f"state_{preview_key}"] = False
          st.rerun()

        st.markdown("---")

      if show_preview:
        st.session_state[f"state_{preview_key}"] = (
            not st.session_state.get(f"state_{preview_key}", False)
        )
        st.rerun()

  else:
    st.warning("لا توجد مستندات تطابق بحثك في هذا القسم.")

# --- 3. لوحة تحكم المدير (المخفية تماماً في أسفل الصفحة) ---
st.markdown("<br><hr><br>", unsafe_allow_html=True)

with st.expander("🛠️ لوحة تحكم المدير (إضافة، حذف، تعديل، ونقل)"):
  admin_pass = st.text_input("أدخل كلمة مرور المدير:", type="password")

  if admin_pass == "Abo_jana97":
    st.success("تم تسجيل الدخول بنجاح كمدير! ✅")
    st.divider()

    # --- القسم الأول: رفع مستند جديد ---
    st.subheader("📤 رفع مستند جديد")
    with st.form("upload_form"):
      existing_cats = [
          d
          for d in os.listdir(BASE_DOCS_DIR)
          if os.path.isdir(os.path.join(BASE_DOCS_DIR, d))
      ]
      new_cat = st.text_input(
          "أو اكتب اسم قسم جديد (اختياري):", placeholder="مثال: عقود جديدة"
      )
      selected_target_cat = st.selectbox(
          "اختر القسم للرفع:",
          options=existing_cats if existing_cats else ["عام"],
      )

      target_category = (
          new_cat.strip()
          if new_cat
          else (selected_target_cat if selected_target_cat else "عام")
      )

      uploaded_file = st.file_uploader(
          "اختر الملف (PDF أو صور)", type=["pdf", "png", "jpg", "jpeg"]
      )

      submit_upload = st.form_submit_button(label="رفع الملف الآن")

      if submit_upload:
        if uploaded_file:
          cat_path = os.path.join(BASE_DOCS_DIR, target_category)
          if not os.path.exists(cat_path):
            os.makedirs(cat_path)

          file_path = os.path.join(cat_path, uploaded_file.name)
          with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
          st.success(
              f"تم رفع الملف بنجاح إلى قسم: **{target_category}**! قم بتحديث"
              " الصفحة."
          )
        else:
          st.warning("الرجاء اختيار ملف أولاً.")

    st.divider()

    # --- القسم الثاني: إدارة الأقسام (تعديل اسم قسم أو حذفه بالكامل) ---
    st.subheader("📁 إدارة الأقسام (تعديل أو حذف)")
    if categories:
      col_m1, col_m2 = st.columns(2)

      with col_m1:
        st.markdown("##### ✏️ تعديل اسم قسم")
        cat_to_rename = st.selectbox(
            "اختر القسم لإعادة تسميته:", categories, key="rename_select"
        )
        new_name_input = st.text_input("اسم القسم الجديد:")
        if st.button("تحديث اسم القسم"):
          if new_name_input.strip():
            old_p = os.path.join(BASE_DOCS_DIR, cat_to_rename)
            new_p = os.path.join(BASE_DOCS_DIR, new_name_input.strip())
            if not os.path.exists(new_p):
              os.rename(old_p, new_p)
              st.success("تم تحديث اسم القسم بنجاح!")
              st.rerun()
            else:
              st.error("هذا الاسم موجود مسبقاً.")
          else:
            st.warning("يرجى كتابة الاسم الجديد.")

      with col_m2:
        st.markdown("##### 🗑️ حذف قسم بالكامل")
        cat_to_delete = st.selectbox(
            "اختر القسم للحذف:", categories, key="delete_cat_select"
        )
        if st.button("حذف القسم ومستنداته", type="primary"):
          cat_path_del = os.path.join(BASE_DOCS_DIR, cat_to_delete)
          shutil.rmtree(cat_path_del)
          st.success(f"تم حذف القسم ({cat_to_delete}) بنجاح!")
          st.rerun()

    st.divider()

    # --- القسم الثالث: إدارة المستندات (حذف مستند أو نقله لقسم آخر) ---
    st.subheader("📄 إدارة المستندات (حذف أو نقل)")
    if categories:
      manage_cat = st.selectbox(
          "اختر القسم لإدارة مستنداته:", categories, key="man_cat"
      )
      m_cat_path = os.path.join(BASE_DOCS_DIR, manage_cat)
      m_files = [
          f
          for f in os.listdir(m_cat_path)
          if os.path.isfile(os.path.join(m_cat_path, f))
      ]

      if m_files:
        file_to_manage = st.selectbox(
            "اختر المستند المطلوب:", m_files, key="man_file"
        )
        current_file_path = os.path.join(m_cat_path, file_to_manage)

        col_f1, col_f2 = st.columns(2)

        with col_f1:
          st.markdown("##### 🗑️ حذف المستند")
          if st.button("حذف هذا المستند نهائياً", type="primary"):
            os.remove(current_file_path)
            st.success(f"تم حذف المستند ({file_to_manage}) بنجاح!")
            st.rerun()

        with col_f2:
          st.markdown("##### 📦 نقل المستند لقسم آخر")
          other_cats = [c for c in categories if c != manage_cat]
          if other_cats:
            target_move_cat = st.selectbox(
                "انقل إلى القسم:", other_cats, key="target_move"
            )
            if st.button("تنفيذ نقل المستند"):
              dest_dir = os.path.join(BASE_DOCS_DIR, target_move_cat)
              dest_path = os.path.join(dest_dir, file_to_manage)
              shutil.move(current_file_path, dest_path)
              st.success(
                  f"تم نقل المستند بنجاح إلى قسم ({target_move_cat})!"
              )
              st.rerun()
          else:
            st.info("لا توجد أقسام أخرى لنقل المستند إليها.")
      else:
        st.info("هذا القسم خالي من المستندات.")

  elif admin_pass:
    st.error("كلمة المرور غير صحيحة")