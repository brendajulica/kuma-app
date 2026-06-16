import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Kuma Gift Dashboard", layout="wide")
st.title("🪻 Kuma Gift Order Control")

# 1. KONEKSI
@st.cache_resource
def dapatkan_koneksi_sheets():
    try:
        if "gspread" in st.secrets:
            creds = Credentials.from_service_account_info(json.loads(st.secrets["gspread"]["creds"]), scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
            return gspread.authorize(creds).open("Database Kuma Gift").sheet1
    except:
        return None
    return None

sheet = dapatkan_koneksi_sheets()

# 2. INPUTAN
with st.expander("📝 Form Input Pesanan"):
    col1, col2 = st.columns(2)
    with col1:
        input_hp = st.text_input("No HP:")
        nama = st.text_input("Nama Pelanggan:")
    with col2:
        produk = st.selectbox("Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
        tema = st.text_input("Tema:")
    alamat = st.text_area("Alamat:")
    if st.button("Simpan Orderan"):
        if sheet and nama:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), nama, produk, tema, nama, input_hp, "Antar/Kirim", alamat, "-", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), 0, 0, 0, "Belum Selesai"])
            st.rerun()

# 3. DASHBOARD LENGKAP
if sheet:
    try:
        df = pd.DataFrame(sheet.get_all_records())
        if not df.empty and "Status" in df.columns:
            # Kalkulasi Tanggal
            hari_ini = datetime.now()
            
            # Tab Dashboard
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚨 Semua Aktif", "⏳ H-1", "🗓️ H-2", "📅 H-3", "📆 H-7", "✅ Tandai Selesai"])
            
            df_aktif = df[df["Status"] == "Belum Selesai"]
            
            with tab1:
                st.dataframe(df_aktif)
                
            with tab2:
                tgl = (hari_ini + timedelta(days=1)).strftime("%Y-%m-%d")
                st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == tgl])
                
            with tab3:
                tgl = (hari_ini + timedelta(days=2)).strftime("%Y-%m-%d")
                st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == tgl])
                
            with tab4:
                tgl = (hari_ini + timedelta(days=3)).strftime("%Y-%m-%d")
                st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == tgl])
                
            with tab5:
                tgl = (hari_ini + timedelta(days=7)).strftime("%Y-%m-%d")
                st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == tgl])
                
            with tab6:
                pilihan = st.selectbox("Pilih Order Selesai:", df_aktif["Nama Pelanggan"].tolist())
                if st.button("Ubah ke SELESAI"):
                    idx = df[df["Nama Pelanggan"] == pilihan].index[0] + 2
                    sheet.update_cell(idx, 15, "Selesai")
                    st.rerun()
        else:
            st.warning("Data kosong atau kolom 'Status' tidak ditemukan.")
    except Exception as e:
        st.error(f"Error: {e}")
