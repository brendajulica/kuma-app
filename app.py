import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Kuma Gift Management", layout="wide")
st.title("🪻 Kuma Gift Integrated Management System")

# 2. KONEKSI & LOAD DATA
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

df_histori = pd.DataFrame()
if sheet:
    try:
        data = sheet.get_all_records()
        df_histori = pd.DataFrame(data)
        df_histori = df_histori.fillna("-")
        
        # Konversi paksa kolom agar tidak Eror
        df_histori["Tanggal Input"] = pd.to_datetime(df_histori["Tanggal Input"], errors='coerce')
        df_histori["Tanggal Pengambilan"] = pd.to_datetime(df_histori["Tanggal Pengambilan"], errors='coerce')
        df_histori["Total Bayar Seharusnya"] = pd.to_numeric(df_histori["Total Bayar Seharusnya"], errors='coerce').fillna(0)
        df_histori["DP Awal"] = pd.to_numeric(df_histori["DP Awal"], errors='coerce').fillna(0)
        df_histori["Kekurangan"] = pd.to_numeric(df_histori["Kekurangan"], errors='coerce').fillna(0)
    except:
        pass

# 3. TAB MENU
tab_ops, tab_laporan = st.tabs(["📋 Operasional Pesanan", "📊 Laporan Bulanan"])

with tab_ops:
    st.subheader("📝 Form Input Pesanan")
    with st.container(border=True):
        nama_admin = st.selectbox("Pilih Nama Admin:", ["Admin 1", "Admin 2", "Admin 3"])
        col1, col2, col3 = st.columns(3)
        with col1:
            input_hp = st.text_input("No HP Penerima:")
            nama = st.text_input("Nama Pelanggan:")
        with col2:
            produk = st.selectbox("Pilih Jenis Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
            metode = st.selectbox("Metode Penyerahan:", ["Antar/Kirim", "Ambil di Toko"])
        with col3:
            total = st.number_input("Total Bayar:", min_value=0)
            dp = st.number_input("DP Awal:", min_value=0)
            st.write(f"Kekurangan: Rp {total - dp:,}")
        
        tema = st.text_input("Tema Warna Buket:")
        alamat = st.text_area("Alamat Lengkap Pengiriman:")
        catatan = st.text_area("Catatan Khusus:")
        tgl_ambil = st.date_input("Tanggal Pengambilan:", value=datetime.now() + timedelta(days=1))
        
        if st.button("Simpan Orderan", type="primary"):
            now = datetime.now()
            sheet.append_row([
                now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), nama, produk, tema, nama, 
                input_hp, metode, alamat, catatan, tgl_ambil.strftime("%Y-%m-%d"), 
                total, dp, (total - dp), "Belum Selesai
