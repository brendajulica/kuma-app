import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

# Konfigurasi Halaman
st.set_page_config(page_title="Kuma Gift Management", layout="wide")
st.title("🪻 Kuma Gift Integrated Management System")

# 1. KONEKSI & LOAD DATA
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
        
        # PEMBERSIHAN DATA (Anti-Eror)
        df_histori = df_histori.fillna("-")
        df_histori["Nama Pelanggan"] = df_histori["Nama Pelanggan"].astype(str)
        df_histori["Pilih Jenis Produk"] = df_histori["Pilih Jenis Produk"].astype(str)
        df_histori["No HP Penerima"] = df_histori["No HP Penerima"].astype(str).str.strip()
        df_histori["Total Bayar Seharusnya"] = pd.to_numeric(df_histori["Total Bayar Seharusnya"], errors='coerce').fillna(0)
        
        # KONVERSI TANGGAL YANG AMAN
        df_histori["Tanggal Input"] = pd.to_datetime(df_histori["Tanggal Input"], errors='coerce')
    except:
        pass

# 2. TAB MENU
tab_ops, tab_laporan = st.tabs(["📋 Operasional Pesanan", "📊 Laporan Bulanan"])

with tab_ops:
    st.subheader("📝 Form Input Pesanan")
    with st.container(border=True):
        nama_admin = st.selectbox("Pilih Nama Admin:", ["Admin 1", "Admin 2", "Admin 3"])
        col1, col2 = st.columns(2)
        with col1:
            input_hp = st.text_input("No HP Pelanggan (Cek Histori):")
            input_hp_clean = str(input_hp).strip()
            data_lama = df_histori[df_histori["No HP Penerima"] == input_hp_clean].iloc[-1] if not df_histori.empty and input_hp_clean in df_histori["No HP Penerima"].values else None
            nama = st.text_input("Nama Pelanggan:", value=data_lama["Nama Pelanggan"] if data_lama is not None and data_lama["Nama Pelanggan"] != "-" else "")
        with col2:
            produk = st.selectbox("Pilih Jenis Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
            tema = st.text_input("Tema Warna Buket:", value=data_lama["Tema Warna Buket"] if data_lama is not None and data_lama["Tema Warna Buket"] != "-" else "")
        
        alamat = st.text_area("Alamat Lengkap Pengiriman:", value=data_lama["Alamat Lengkap Pengiriman"] if data_lama is not None and data_lama["Alamat Lengkap Pengiriman"] != "-" else "")
        catatan = st.text_area("Catatan Khusus:")
        tgl_ambil = st.date_input("Tanggal Pengambilan:", value=datetime.now() + timedelta(days=1))
        
        if st.button("Simpan Orderan", type="primary", use_container_width=True):
            if sheet and nama and input_hp:
                now = datetime.now()
                sheet.append_row([now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), nama, produk, tema, nama, input_hp, "Antar/Kirim", alamat, catatan, tgl_ambil.strftime("%Y-%m-%d"), 0, 0, 0, "Belum Selesai", nama_admin])
                st.success(f"Disimpan oleh {nama_admin}!")
                st.rerun()

    st.subheader("🏛️ Dashboard Live")
    if not df_histori.empty:
        df_aktif = df_histori[df_histori["Status"] == "Belum Selesai"].copy()
        tabs_sub = st.tabs(["🚨 Semua", "⏳ H-1", "🗓️ H-2", "📅 H-3", "📆 H-7", "✅ Selesai"])
        
        with tabs_sub[0]: st.dataframe(df_aktif, use_container_width=True)
        with tabs_sub[5]: # TAB SELESAI
            if not df_aktif.empty:
                df_aktif["Display"] = df_aktif["Nama Pelanggan"] + " (" + df_aktif["Pilih Jenis Produk"] + ")"
                pilihan = st.selectbox("Pilih pesanan yang selesai:", df_aktif["Display"].tolist())
                nama_pilih = pilihan.split(" (")[0]
                produk_pilih = pilihan.split(" (")[1].replace(")", "")
                st.info(f"Verifikasi: **{nama_pilih}** - **{produk_pilih}**")
                konfirmasi = st.checkbox("Ya, saya sudah memastikan pesanan ini SELESAI.")
                if st.button("Ubah Status Jadi SELESAI", disabled=not konfirmasi):
                    mask = (df_histori["Nama Pelanggan"] == nama_pilih) & (df_histori["Pilih Jenis Produk"] == produk_pilih) & (df_histori["Status"] == "Belum Selesai")
                    sheet.update_cell(df_histori[mask].index[0] + 2, 15, "Selesai")
                    st.rerun()

with tab_laporan:
    st.subheader("📊 Analisis Penjualan Bulan Ini")
    if not df_histori.empty:
        # Filter aman dengan pengecekan NaT
        df_valid = df_histori.dropna(subset=["Tanggal Input"])
        df_bulan_ini = df_
