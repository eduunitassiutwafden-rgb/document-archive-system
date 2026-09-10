import base64
import os
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

# --- 1. رأس الصفحة والعنوان (أول شيء يظهر للموبايل بدون أي مربعات إدخال) ---
st.title("🗂️ بوابة استعراض وطباعة المستندات")
st.markdown(
    "مرحباً بك. يمكنك تصفح المستندات مقسمة حسب الأقسام، ومعاينتها أو تحميلها"
    " مباشرة."
)
st.divider()

# --- 2. اختيار القسم أولاً (قبل البحث عشان الموبايل ميعملش فوكس على كيبورد) ---
st.header("📂 أقسام المستندات")

categories = [
    d
    for d in os.listdir(BASE_DOCS_DIR)
    if os.path.isdir(os.path.join(BASE_DOCS_DIR, d))
]

if not categories:
  st.info("لا توجد أقسام أو مستندات مرفوعة حالياً.")
else:
  selected_category = st.selectbox("اختر القسم لعرض مستنداته:", categories)

  cat_path = os.path.join(BASE_DOCS_DIR, selected_category)
  files = [
      f
      for f in os.listdir(cat_path)
      if os.path.isfile(os.path.join(cat_path, f))
  ]

  # خانة البحث في مكان هادي بعد اختيار القسم
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

      # عرض المعاينة
      if st.session_state.get(f"state_{preview_key}", False):
        if st.button("❌ إغلاق المعاينة", key=f"close_{preview_key}"):
          st.session_state[f"state_{preview_key}"] = False
          st.rerun()

        st.markdown(
            f"--- \n 🔍 **معاينة المستند: {file_name}**", unsafe_allow_html=True
        )

        ext = file_name.split(".")[-1].lower()
        if ext in ["png", "jpg", "jpeg"]:
          st.image(file_path, caption=file_name, width="stretch")
        elif ext == "pdf":
          file_size = os.path.getsize(file_path)
          if file_size > 0:
            with open(file_path, "rb") as pdf_file:
              base64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{base64_pdf}"'
                ' width="100%" height="600px" type="application/pdf"></iframe>',
                unsafe_allow_html=True,
            )
        st.markdown("---")

      if show_preview:
        st.session_state[f"state_{preview_key}"] = (
            not st.session_state.get(f"state_{preview_key}", False)
        )
        st.rerun()

  else:
    st.warning("لا توجد مستندات تطابق بحثك في هذا القسم.")

# --- 3. لوحة تحكم المدير المخفية تماماً في أسفل الصفحة ---
st.markdown("<br><hr><br>", unsafe_allow_html=True)

with st.expander("🛠️ لوحة تحكم المدير (لرفع الملفات فقط)"):
  admin_pass = st.text_input("أدخل كلمة مرور المدير:", type="password")

  if admin_pass == "Abo_jana97":
    st.success("تم تسجيل الدخول بنجاح! يمكنك رفع المستندات الآن:")

    with st.form("upload_form"):
      st.subheader("رفع مستند جديد")
      existing_categories = [
          d
          for d in os.listdir(BASE_DOCS_DIR)
          if os.path.isdir(os.path.join(BASE_DOCS_DIR, d))
      ]
      new_cat = st.text_input(
          "أو اكتب اسم قسم جديد (اختياري):", placeholder="مثال: عقود"
      )
      selected_cat = st.selectbox(
          "اختر القسم:",
          options=existing_categories if existing_categories else ["عام"],
      )

      target_category = (
          new_cat.strip()
          if new_cat
          else (selected_cat if selected_cat else "عام")
      )

      uploaded_file = st.file_uploader(
          "اختر الملف (PDF أو صور)", type=["pdf", "png", "jpg", "jpeg"]
      )

      submit_button = st.form_submit_button(label="رفع الملف")

      if submit_button:
        if uploaded_file:
          cat_path = os.path.join(BASE_DOCS_DIR, target_category)
          if not os.path.exists(cat_path):
            os.makedirs(cat_path)

          file_path = os.path.join(cat_path, uploaded_file.name)
          with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
          st.success(f"تم رفع الملف بنجاح إلى قسم: **{target_category}**!")
        else:
          st.warning("الرجاء اختيار ملف أولاً.")
  elif admin_pass:
    st.error("كلمة المرور غير صحيحة")