import streamlit as st
import google.generativeai as genai # Menggunakan cara import yang lebih standard
from PIL import Image
import json
import traceback
import pandas as pd
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Bakery Ingredient Extractor | MISDEC",
    page_icon="🍞",
    layout="centered"
)

# --- HEADER ---
st.title("🍞 AI Vision: Bakery Ingredient Analyzer")
st.markdown("---")

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("⚙️ System Setup")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.caption("🎓 MISDEC AI Training")

# --- MAIN ---
uploaded_file = st.file_uploader("📁 Muat naik gambar resipi:", type=["jpg", "png", "jpeg", "webp"])

default_prompt = """Anda adalah pakar sains makanan dan bakeri AI. Analisis gambar dan ekstrak maklumat bahan ke dalam format JSON:
{
  "summary_fields": {"Nama Resipi": "Teks", "Kategori": "Teks"},
  "extracted_items": [
    {
      "Nama Bahan": "Teks", 
      "Jenis": "Teks", 
      "Kegunaan (Donut)": "Teks", 
      "Kegunaan (Ban)": "Teks", 
      "Kegunaan (Piza)": "Teks", 
      "Berat (gram)": "Teks", 
      "Sukatan (ml)": "Teks"
    }
  ]
}
"""

if st.button("🚀 Ekstrak Data"):
    if not api_key:
        st.error("Sila masukkan API Key!")
        st.stop()
    
    try:
        # Konfigurasi SDK standard
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        image = Image.open(uploaded_file)
        
        with st.spinner("AI sedang memproses..."):
            response = model.generate_content([default_prompt, image])
            
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            parsed_json = json.loads(raw_text)
            
            # Papar Data
            st.success("Data berjaya diekstrak!")
            items = parsed_json.get("extracted_items", [])
            df = pd.DataFrame(items)
            st.dataframe(df)
            
            # Download Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button("📊 Muat Turun Excel", data=buffer.getvalue(), file_name="bahan_bakeri.xlsx")

    except Exception as e:
        st.error(f"Ralat: {str(e)}")
