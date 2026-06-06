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
      "Kegunaan (Piza)": "Fungsi/kegunaan bahan ini khusus dalam pembuatan Piza",
      "Berat (gram)": "Berat bahan dalam unit gram jika ia jenis pepejal/serbuk (Tulis 'N/A' jika cecair atau tidak dinyatakan)",
      "Sukatan (ml)": "Sukatan bahan dalam unit ml jika ia jenis cecair (Tulis 'N/A' jika pepejal atau tidak dinyatakan)"
    }
  ]
}

Arahan Penting:
1. Ekstrak SEMUA bahan yang dikesan dalam gambar ke dalam senarai "extracted_items".
2. Di kolum "Kegunaan (Donut)", "Kegunaan (Ban)", dan "Kegunaan (Piza)", terangkan secara saintifik/teknikal apa peranan bahan tersebut (cth: Yis untuk menaikkan doh, Tepung Tinggi Protein untuk membentuk gluten, dsb).
3. Jika berat (gram) atau sukatan (ml) tidak ditulis secara jelas pada gambar resipi, berikan anggaran standard yang logik atau tulis "Tidak dinyatakan". Jangan biarkan kosong.
"""

# --- PROMPT EDITOR ---
st.markdown("### 🎯 AI Instruction (Prompt Bakeri)")
prompt = st.text_area(
    "Ubah suai arahan prompt jika perlu:",
    value=default_prompt,
    height=400,
    label_visibility="collapsed"
)

# --- ACTION BUTTON ---
if st.button("🚀 Ekstrak & Analisis Bahan", type="primary", use_container_width=True):

    if not api_key:
        st.error("❌ Sila masukkan Gemini API Key anda di sidebar.")
        st.stop()

    if not uploaded_file:
        st.error("❌ Sila muat naik gambar resipi atau bahan terlebih dahulu.")
        st.stop()

    try:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📷 Gambar Resipi/Bahan")
            st.image(image, use_container_width=True)

        client = genai.Client(api_key=api_key)

        with col2:
            st.markdown("#### ✨ Hasil Analisis Bahan Bakeri")
            with st.spinner("🧠 AI sedang menganalisis kandungan bahan..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, image],
                    config=types.GenerateContentConfig(
                        temperature=0.2, # Ditetapkan rendah untuk ketepatan fakta sains bakeri
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    )
                )

                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                try:
                    parsed_json = json.loads(raw_text)
                    st.success("✅ Maklumat bahan berjaya diekstrak!")
                    
                    summary = parsed_json.get("summary_fields", {})
                    items = parsed_json.get("extracted_items", [])

                    df_summary = None
                    df_items = None

                    # 1. Paparkan Rumusan Dokumen (Jadual Ringkas)
                    if summary:
                        st.markdown("##### 📋 Ringkasan Resipi")
                        df_summary = pd.DataFrame(list(summary.items()), columns=["Perkara", "Maklumat"])
                        st.table(df_summary)

                    # 2. Paparkan Senarai Jadual Bahan (Jadual Utama)
                    if isinstance(items, list) and len(items) > 0:
                        st.markdown("##### 📊 Jadual Analisis Bahan-Bahan")
                        df_items = pd.DataFrame(items)
                        # Menyusun susunan kolum supaya kemas jika perlu
                        st.dataframe(df_items) # Menggunakan dataframe supaya boleh skrol jika panjang
                    else:
                        st.warning("⚠️ Tiada senarai bahan berasingan yang ditemui.")

                    # --- JANA FAIL EXCEL (.XLSX) ---
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        if df_summary is not None:
                            df_summary.to_excel(writer, sheet_name='Ringkasan', index=False)
                        if df_items is not None:
                            df_items.to_excel(writer, sheet_name='Analisis Bahan', index=False)
                        
                        if df_summary is None and df_items is None:
                            pd.DataFrame([{"Mesej": "Tiada data"}]).to_excel(writer, sheet_name='Empty', index=False)
                    
                    excel_buffer.seek(0)

                    # Butang Muat Turun Fail Excel
                    st.download_button(
                        label="📊 Muat Turun Data Bahan (Excel)",
                        data=excel_buffer,
                        file_name="analisis_bahan_bakeri.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                except json.JSONDecodeError:
                    st.warning("⚠️ AI gagal mengembalikan format JSON yang bersih.")
                    st.code(raw_text, language="json")

    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "API_KEY" in error_msg or "401" in error_msg:
            st.error("❌ API Key salah. Sila semak semula di sidebar.")
        elif "429" in error_msg:
            st.error("❌ Had limit API dicapai. Sila tunggu sebentar dan cuba lagi.")
        else:
            st.error(f"❌ Ralat Sistem: {error_msg}")

# --- FOOTER ---
st.markdown("---")
st.caption("🎓 Building AI Vision App with Gemini API • MISDEC Melaka")
