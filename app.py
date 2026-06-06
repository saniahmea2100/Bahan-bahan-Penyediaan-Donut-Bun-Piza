import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json
import traceback
import pandas as pd
import io  # Diperlukan untuk proses download Excel

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Bakery Ingredient Extractor | MISDEC",
    page_icon="🍞",
    layout="centered"
)

# --- HEADER ---
st.title("🍞 AI Vision: Bakery Ingredient Analyzer")
st.caption("Built for MISDEC AI Training • Cik Kiah War Room")
st.markdown("---")
st.markdown(
    "Muat naik gambar resipi, senarai bahan, atau gambar bahan mentah. "
    "Gemini AI akan mengekstrak maklumat nama bahan, jenis, berat/sukatan, serta fungsinya dalam pembuatan Donut, Ban, dan Piza. ✨"
)

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("⚙️ System Setup")
    api_key = st.text_input(
        "Enter your Gemini API Key:",
        type="password",
        help="Get it from Google AI Studio"
    )
    st.markdown(
        "🔑 [Get your API Key](https://aistudio.google.com/app/apikey)"
    )

    # --- API Key Tester Button ---
    st.divider()
    if st.button("🧪 Test API Key", use_container_width=True):
        if not api_key:
            st.error("Paste a key first")
        else:
            try:
                client = genai.Client(api_key=api_key)
                test_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=["Say hello in one word"]
                )
                st.success(f"✅ Key works! Response: {test_response.text}")
            except Exception as e:
                st.error(f"❌ RAW ERROR:\n\n{type(e).__name__}: {str(e)}")
                st.code(traceback.format_exc())

    st.divider()
    st.caption("💡 Your API key is never stored. Stays in your browser only.")
    st.divider()
    st.caption("🎓 MISDEC AI Vision Training")
    st.caption("Trainer: Muhammad Nur Aqmal bin Khatiman")

# --- MAIN: FILE UPLOAD ---
uploaded_file = st.file_uploader(
    "📁 Muat naik gambar resipi atau bahan bakeri anda:",
    type=["jpg", "png", "jpeg", "webp"],
    help="Max 10MB. Berfungsi paling baik dengan tulisan atau gambar yang jelas."
)

# --- DEFAULT BAKERY PROMPT ---
default_prompt = """Anda adalah pakar sains makanan dan bakeri AI. Analisis gambar yang dimuat naik (sama ada teks resipi, senarai barang, atau gambar bahan mentah) dan ekstrak maklumat bahan ke dalam format JSON yang berstruktur.

Respons JSON anda mesti mengikut skema yang tepat ini:
{
  "summary_fields": {
    "Nama Resipi / Tajuk": "Nama resipi atau tajuk dokumen yang dikesan",
    "Kategori": "Kategori produk (cth: Bakeri / Pastri)"
  },
  "extracted_items": [
    {
      "Nama Bahan": "Nama bahan mentah (cth: Tepung Gandum, Yis, Susu Segar, Mentega)",
      "Jenis": "Jenis fizikal bahan (cth: Pepejal, Cecair, Serbuk, Gel)",
      "Kegunaan (Donut)": "Fungsi/kegunaan bahan ini khusus dalam pembuatan Donut",
      "Kegunaan (Ban)": "Fungsi/kegunaan bahan ini khusus dalam pembuatan Ban (Roti)",
      "Kegunaan (Piza)": "Fungsi/
