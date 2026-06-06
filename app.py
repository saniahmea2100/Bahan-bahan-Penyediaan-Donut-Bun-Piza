import streamlit as st
from google import genai
from PIL import Image
import json
import pandas as pd
import io
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Bakery Ingredient Extractor | MISDEC",
    page_icon="🍞",
    layout="centered"
)

# --- HEADER ---
st.title("🍞 AI Vision: Bakery Ingredient Analyzer")
st.caption("Ekstrak bahan bakeri daripada gambar resipi menggunakan Gemini AI")
st.markdown("---")

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("⚙️ System Setup")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.caption("🎓 MISDEC AI Training")

# --- MAIN ---
uploaded_file = st.file_uploader(
    "📁 Muat naik gambar resipi:",
    type=["jpg", "png", "jpeg", "webp"]
)

default_prompt = """
Anda adalah pakar sains makanan dan bakeri AI.

Tugas:
Analisis gambar resipi yang diberi dan ekstrak maklumat bahan bakeri.

Jawab dalam JSON SAHAJA. Jangan tambah penerangan lain.
Pastikan format JSON sah dan boleh dibaca oleh Python json.loads().

Gunakan struktur ini:

{
  "summary_fields": {
    "Nama Resipi": "",
    "Kategori": ""
  },
  "extracted_items": [
    {
      "Nama Bahan": "",
      "Jenis": "",
      "Kegunaan (Donut)": "",
      "Kegunaan (Ban)": "",
      "Kegunaan (Piza)": "",
      "Berat (gram)": "",
      "Sukatan (ml)": ""
    }
  ]
}

Panduan:
- Jika maklumat tiada dalam gambar, isi "Tidak dinyatakan".
- Jika bahan sesuai untuk donut, ban atau piza, nyatakan kegunaannya secara ringkas.
- Jangan reka berat atau sukatan jika tidak kelihatan dalam gambar.
"""

def clean_json_text(text):
    text = text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return text

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Gambar resipi yang dimuat naik", use_container_width=True)

if st.button("🚀 Ekstrak Data"):
    if not api_key:
        st.error("Sila masukkan API Key dahulu.")
        st.stop()

    if uploaded_file is None:
        st.error("Sila muat naik gambar resipi dahulu.")
        st.stop()

    try:
        client = genai.Client(api_key=api_key)

        image = Image.open(uploaded_file)

        with st.spinner("AI sedang memproses gambar..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image, default_prompt]
            )

            raw_text = response.text
            cleaned_text = clean_json_text(raw_text)

            try:
                parsed_json = json.loads(cleaned_text)
            except json.JSONDecodeError:
                st.error("AI tidak menghasilkan JSON yang sah. Sila cuba semula.")
                st.subheader("Output mentah daripada AI:")
                st.code(raw_text)
                st.stop()

            summary = parsed_json.get("summary_fields", {})
            items = parsed_json.get("extracted_items", [])

            if not items:
                st.warning("Tiada bahan berjaya dikesan daripada gambar.")
                st.stop()

            df = pd.DataFrame(items)

            df.insert(0, "Nama Resipi", summary.get("Nama Resipi", "Tidak dinyatakan"))
            df.insert(1, "Kategori", summary.get("Kategori", "Tidak dinyatakan"))

            st.success("Data berjaya diekstrak!")

            st.subheader("📌 Ringkasan Resipi")
            st.write(f"**Nama Resipi:** {summary.get('Nama Resipi', 'Tidak dinyatakan')}")
            st.write(f"**Kategori:** {summary.get('Kategori', 'Tidak dinyatakan')}")

            st.subheader("📋 Senarai Bahan")
            st.dataframe(df, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Bahan Bakeri")

            st.download_button(
                label="📊 Muat Turun Excel",
                data=buffer.getvalue(),
                file_name="bahan_bakeri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error("Ralat berlaku semasa memproses data.")
        st.code(str(e))
