import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

# Konfigurasi Halaman
st.set_page_config(page_title="Kuma Gift Management", layout="wide")
st.title("🪻 Kuma Gift Integrated Management System")

# 1. KONEKSI DATA (Menggunakan cache_data agar lebih mudah refresh)
@st.cache_data(ttl=10) # Data akan di-refresh setiap 10 detik
def load_data():
    try:
        if "gspread" in st.secrets:
            creds = Credentials.from_service_account_info(json.loads(st.secrets["gspread"]["creds"]), scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
            sheet = gspread.authorize(creds).open("Database Kuma Gift").sheet1
            data = sheet.get_all_records()
            return pd.DataFrame(data), sheet
    except:
        return pd.DataFrame(), None
    return pd.DataFrame(), None

df_histori, sheet = load_data()

# Bersihkan Data
if not df_histori.empty:
    df_histori = df_histori.fillna("-")
    df_histori["Tanggal Input"] = pd.to_datetime(df_histori["Tanggal Input"], errors='coerce')
    df_histori["Tanggal Pengambilan"] = pd.to_datetime(df_histori["Tanggal Pengambilan"], errors='coerce')
    df_histori["Status"] = df_histori["Status"].astype(str).str.strip() # Menghapus spasi tersembunyi

# 2. TAB MENU
tab_ops, tab_laporan = st.tabs(["📋 Operasional Pesanan", "📊 Laporan Bulanan"])

with tab_ops:
    # FORM INPUT
    with st.expander("📝 Form Input Pesanan Baru", expanded=True):
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
            
        tema = st.text_input("Tema Warna Buket:")
        alamat = st.text_area("Alamat Lengkap Pengiriman:")
        catatan = st.text_area("Catatan Khusus:")
        tgl_ambil = st.date_input("Tanggal Pengambilan:", value=datetime.now() + timedelta(days=1))
        
        if st.button("Simpan Orderan", type="primary"):
            data_baru = [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), nama, produk, tema, nama, input_hp, metode, alamat, catatan, tgl_ambil.strftime("%Y-%m-%d"), total, dp, (total - dp), "Belum Selesai", nama_admin]
            sheet.append_row(data_baru)
            st.success("Data tersimpan!")
            st.rerun()

    # DASHBOARD
    st.subheader("🏛️ Dashboard Live")
    
    if sheet is None:
        st.error("Koneksi Sheets terputus.")
    elif df_histori.empty:
        st.warning("Data kosong! Pastikan Google Sheets memiliki isi.")
    else:
        # Debugging: Tampilkan jumlah baris yang ditemukan
        st.write(f"Total baris ditemukan: {len(df_histori)}")
        
        # Filter Status (pastikan tulisan di Sheets 'Belum Selesai')
        # Kita gunakan .str.contains agar lebih fleksibel terhadap spasi
        df_aktif = df_histori[df_histori["Status"].str.contains("Belum Selesai", na=False)].copy()
        
        if df_aktif.empty:
            st.warning("Tidak ada data dengan status 'Belum Selesai'. Cek apakah penulisan status di Google Sheets sudah benar.")
            st.write("Contoh data pertama di sheet Anda:", df_histori.iloc[0].to_dict() if len(df_histori)>0 else "Kosong")
        else:
            today = datetime.now().date()
            tabs = st.tabs(["🚨 Semua", "⏳ H-1", "🗓️ H-2", "📅 H-3", "📆 H-7", "✅ Tandai Selesai"])
            
            # ... (Lanjutkan dengan kode tabs seperti sebelumnya) ...
            
            def filter_tgl(df, days):
                target = today + timedelta(days=days)
                return df[df["Tanggal Pengambilan"].dt.date == target]

            with tabs[0]: st.dataframe(df_aktif, use_container_width=True)
            with tabs[1]: st.dataframe(filter_tgl(df_aktif, 1), use_container_width=True)
            with tabs[2]: st.dataframe(filter_tgl(df_aktif, 2), use_container_width=True)
            with tabs[3]: st.dataframe(filter_tgl(df_aktif, 3), use_container_width=True)
            with tabs[4]: st.dataframe(filter_tgl(df_aktif, 7), use_container_width=True)
            
            with tabs[5]:
                pilihan = st.selectbox("Pilih pesanan selesai:", df_aktif["Nama Pelanggan"] + " (" + df_aktif["Tanggal Pengambilan"].dt.strftime('%d-%m-%Y') + ")")
                if st.button("Ubah Status ke Selesai"):
                    idx = df_aktif[df_aktif["Nama Pelanggan"] + " (" + df_aktif["Tanggal Pengambilan"].dt.strftime('%d-%m-%Y') + ")" == pilihan].index[0]
                    sheet.update_cell(idx + 2, 15, "Selesai")
                    st.rerun()
