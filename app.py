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
        df_histori = df_histori.fillna("-")
        df_histori["Nama Pelanggan"] = df_histori["Nama Pelanggan"].astype(str)
        df_histori["Pilih Jenis Produk"] = df_histori["Pilih Jenis Produk"].astype(str)
        df_histori["No HP Penerima"] = df_histori["No HP Penerima"].astype(str).str.strip()
        # Konversi ke numerik untuk perhitungan laporan
        df_histori["Total Bayar Seharusnya"] = pd.to_numeric(df_histori["Total Bayar Seharusnya"], errors='coerce').fillna(0)
        df_histori["Tanggal Input"] = pd.to_datetime(df_histori["Tanggal Input"], errors='coerce')
    except:
        pass

# 2. TAB MENU
tab_ops, tab_laporan = st.tabs(["📋 Operasional Pesanan", "📊 Laporan Bulanan"])

with tab_ops:
    st.subheader("📝 Form Input Pesanan")
    with st.container(border=True):
        nama_admin = st.selectbox("Pilih Nama Admin:", ["Admin 1", "Admin 2", "Admin 3"])
        col1, col2, col3 = st.columns(3)
        with col1:
            input_hp = st.text_input("No HP Pelanggan:")
            input_hp_clean = str(input_hp).strip()
            data_lama = df_histori[df_histori["No HP Penerima"] == input_hp_clean].iloc[-1] if not df_histori.empty and input_hp_clean in df_histori["No HP Penerima"].values else None
            nama = st.text_input("Nama Pelanggan:", value=data_lama["Nama Pelanggan"] if data_lama is not None and data_lama["Nama Pelanggan"] != "-" else "")
        with col2:
            produk = st.selectbox("Pilih Jenis Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
            metode = st.selectbox("Metode Penyerahan:", ["Antar/Kirim", "Ambil di Toko"])
        with col3:
            total_bayar = st.number_input("Total Bayar:", min_value=0)
            dp = st.number_input("DP Awal:", min_value=0)
            kekurangan = total_bayar - dp
            st.write(f"**Sisa Kekurangan: Rp {kekurangan:,}**")
        
        tema = st.text_input("Tema Warna:", value=data_lama["Tema Warna Buket"] if data_lama is not None and data_lama["Tema Warna Buket"] != "-" else "")
        alamat = st.text_area("Alamat Lengkap:")
        tgl_ambil = st.date_input("Tanggal Pengambilan:", value=datetime.now() + timedelta(days=1))
        
        if st.button("Simpan Orderan", type="primary", use_container_width=True):
            if sheet and nama and input_hp:
                now = datetime.now()
                # Urutan data sesuai 16 kolom yang Anda punya
                sheet.append_row([
                    now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), nama, produk, tema, nama, 
                    input_hp, metode, alamat, "-", tgl_ambil.strftime("%Y-%m-%d"), 
                    total_bayar, dp, kekurangan, "Belum Selesai", nama_admin
                ])
                st.success("Data berhasil disimpan!")
                st.rerun()

    st.subheader("🏛️ Dashboard Live")
    if not df_histori.empty:
        df_aktif = df_histori[df_histori["Status"] == "Belum Selesai"].copy()
        st.dataframe(df_aktif, use_container_width=True)

with tab_laporan:
    st.subheader("📊 Analisis Bulanan")
    if not df_histori.empty:
        # Perbaikan filter agar tidak error lagi
        df_valid = df_histori.dropna(subset=["Tanggal Input"]).copy()
        df_bulan_ini = df_valid[(df_valid["Tanggal Input"].dt.month == datetime.now().month) & (df_valid["Tanggal Input"].dt.year == datetime.now().year)]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Order", len(df_bulan_ini))
        c2.metric("Total Omset", f"Rp {df_bulan_ini['Total Bayar Seharusnya'].sum():,.0f}")
        c3.metric("Total DP Masuk", f"Rp {df_bulan_ini['DP Awal'].sum():,.0f}")
