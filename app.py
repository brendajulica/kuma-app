import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Kuma Gift Order Control", layout="wide")
st.title("🪻 Kuma Gift Order Control")

# 1. KONEKSI
@st.cache_resource
def dapatkan_koneksi_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gspread" in st.secrets:
            creds = Credentials.from_service_account_info(json.loads(st.secrets["gspread"]["creds"]), scopes=scope)
            client = gspread.authorize(creds)
            return client.open("Database Kuma Gift").sheet1
    except:
        return None
    return None

sheet = dapatkan_koneksi_sheets()

# 2. FORM INPUT
st.subheader("📝 Formulir Input")
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        input_hp = st.text_input("No HP Pelanggan (Untuk Cek Data):")
        nama = st.text_input("Nama Pelanggan:")
    with col2:
        produk = st.selectbox("Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
        tema = st.text_input("Tema Warna:")
    alamat = st.text_area("Alamat:")
    
    if st.button("Simpan Orderan"):
        if sheet and nama:
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"),
                nama, produk, tema, nama, input_hp, "Antar/Kirim", alamat, "-",
                (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), 0, 0, 0, "Belum Selesai"
            ])
            st.success("Tersimpan!")
            st.rerun()

# 3. DASHBOARD (DENGAN PENGECEKAN KOLOM)
st.subheader("🏛️ Dashboard Live")
if sheet:
    try:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            
            # Pengecekan otomatis header
            if "Status" not in df.columns:
                st.error(f"❌ Kolom 'Status' tidak ditemukan! Header di Sheets Anda adalah: {df.columns.tolist()}")
            else:
                df_aktif = df[df["Status"] == "Belum Selesai"]
                if not df_aktif.empty:
                    st.dataframe(df_aktif, use_container_width=True)
                else:
                    st.info("Tidak ada orderan aktif.")
        else:
            st.warning("Data Google Sheets kosong.")
    except Exception as e:
        st.error(f"Error: {e}")
