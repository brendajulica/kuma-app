import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

# Konfigurasi
st.set_page_config(page_title="Kuma Gift Management", layout="wide")
st.title("🪻 Kuma Gift Integrated Management System")

# 1. KONEKSI DATA
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
        # Konversi tipe data
        df_histori["Tanggal Pengambilan"] = pd.to_datetime(df_histori["Tanggal Pengambilan"], errors='coerce')
    except:
        pass

# 2. DASHBOARD & FILTER
st.subheader("🏛️ Dashboard Live")
if not df_histori.empty:
    df_aktif = df_histori[df_histori["Status"] == "Belum Selesai"].copy()
    today = datetime.now().date()
    
    tabs = st.tabs(["🚨 Semua", "⏳ H-1", "🗓️ H-2", "📅 H-3", "📆 H-7", "✅ Tandai Selesai"])
    
    # Fungsi Filter
    def get_filter(days):
        target = today + timedelta(days=days)
        return df_aktif[df_aktif["Tanggal Pengambilan"].dt.date == target]

    with tabs[0]: st.dataframe(df_aktif, use_container_width=True)
    with tabs[1]: st.dataframe(get_filter(1), use_container_width=True)
    with tabs[2]: st.dataframe(get_filter(2), use_container_width=True)
    with tabs[3]: st.dataframe(get_filter(3), use_container_width=True)
    with tabs[4]: st.dataframe(get_filter(7), use_container_width=True)
    
    with tabs[5]:
        pilihan = st.selectbox("Pilih pesanan selesai:", df_aktif["Nama Pelanggan"] + " - " + df_aktif["Pilih Jenis Produk"])
        if st.button("Ubah Status ke Selesai"):
            # Cari baris yang cocok (ditambah 2 karena header Google Sheets)
            idx = df_aktif[df_aktif["Nama Pelanggan"] + " - " + df_aktif["Pilih Jenis Produk"] == pilihan].index[0]
            sheet.update_cell(idx + 2, 15, "Selesai")
            st.success("Status diupdate! Refresh halaman.")
            st.rerun()
