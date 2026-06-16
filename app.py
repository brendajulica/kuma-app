import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json
import io

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

   # ==============================================================================
# 3. 🏛️ DASHBOARD PEMILAH LIVE (H-1, H-2, H-3, & H-7 REAL-TIME)
# ==============================================================================
if sheet is not None:
    try:
        records = sheet.get_all_records()
        if records:
            df_all = pd.DataFrame(records)
            
            st.write("---")
            st.write("## 🏛️ DASHBOARD LIVE ORDERAN KUMA GIFT")
            
            # Tombol Download Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_all.to_excel(writer, index=False, sheet_name='Semua Orderan')
            buku_excel = buffer.getvalue()
            
            st.download_button(
                label="📥 Download Seluruh Data ke Excel (.xlsx)",
                data=buku_excel,
                file_name=f"Rekap_Orderan_KumaGift_{datetime.today().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.write("") 
            
            # Perhitungan tanggal otomatis
            hari_ini_wib = pd.Timestamp.now(tz="Asia/Jakarta")
            besok_str = (hari_ini_wib + timedelta(days=1)).strftime("%Y-%m-%d")
            lusa_str = (hari_ini_wib + timedelta(days=2)).strftime("%Y-%m-%d")
            hari_ke3_str = (hari_ini_wib + timedelta(days=3)).strftime("%Y-%m-%d")
            hari_ke7_str = (hari_ini_wib + timedelta(days=7)).strftime("%Y-%m-%d") # Logika H-7 seminggu lagi
            
            if "Status" in df_all.columns and "Tanggal Pengambilan" in df_all.columns:
                df_aktif = df_all[df_all["Status"] == "Belum Selesai"]
                df_h1 = df_aktif[df_aktif["Tanggal Pengambilan"] == besok_str]
                df_h2 = df_aktif[df_aktif["Tanggal Pengambilan"] == lusa_str]
                df_h3 = df_aktif[df_aktif["Tanggal Pengambilan"] == hari_ke3_str]
                df_h7 = df_aktif[df_aktif["Tanggal Pengambilan"] == hari_ke7_str] # Filter H-7
            else:
                df_h1, df_h2, df_h3, df_h7 = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            # Menu Tab Dashboard (Ditambah opsi H-7)
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "🚨 Semua", 
                "⏳ H-1 (Besok)", 
                "🗓️ H-2 (Lusa)",
                "📅 H-3 (3 Hari)",
                "📆 H-7 (Seminggu)", # TAB BARU H-7
                "✅ Tandai Selesai"
            ])
            
            with tab1:
                st.write("### Master Data (Seluruh Orderan di Google Sheets)")
                st.dataframe(df_all)
                
            with tab2:
                st.write(f"### 📋 Rangkaian Buket Harus Siap Besok ({besok_str})")
                if not df_h1.empty:
                    st.dataframe(df_h1)
                else:
                    st.info("Aman! Tidak ada pesanan untuk besok.")
                    
            with tab3:
                st.write(f"### 📋 Persiapan Bahan / Buket untuk Lusa ({lusa_str})")
                if not df_h2.empty:
                    st.dataframe(df_h2)
                else:
                    st.info("Aman! Tidak ada pesanan untuk lusa.")

            with tab4:
                st.write(f"### 📦 List Orderan Masuk untuk 3 Hari ke Depan ({hari_ke3_str})")
                if not df_h3.empty:
                    st.dataframe(df_h3)
                else:
                    st.info("Aman! Belum ada pesanan masuk untuk 3 hari ke depan.")

            with tab5:
                st.write(f"### 💐 Persiapan Stok & Bahan untuk Seminggu ke Depan ({hari_ke7_str})")
                if not df_h7.empty:
                    st.dataframe(df_h7)
                else:
                    st.info("Aman! Belum ada pesanan masuk untuk tepat seminggu ke depan.")

            with tab6:
                st.write("### 🛠️ Tandai Pesanan yang Sudah Diambil / Dikirim")
                df_pilihan = df_all[df_all["Status"] == "Belum Selesai"]
                
                if not df_pilihan.empty:
                    pilihan_nama = df_pilihan["Nama Pelanggan"].tolist()
                    orderan_terpilih = st.selectbox("Pilih Nama Pelanggan yang Sudah Selesai:", pilihan_nama)
                    
                    st.warning(f"⚠️ **PENTING:** Pastikan Anda benar-benar ingin menyelesaikan pesanan atas nama: **{orderan_terpilih}**.")
                    konfirmasi_benar = st.checkbox(f"Ya, saya sudah memeriksa dan nama **{orderan_terpilih}** sudah benar.")
                    
                    if st.button("Ubah Status Jadi SELESAI ✅", use_container_width=True, disabled=not konfirmasi_benar):
                        indeks_baris = df_all[df_all["Nama Pelanggan"] == orderan_terpilled].index[0] + 2 if orderan_terpilih in df_all["Nama Pelanggan"].values else df_all[df_all["Nama Pelanggan"] == orderan_terpilih].index[0] + 2
                        # Cari indeks baris yang tepat
                        indeks_baris = df_all[df_all["Nama Pelanggan"] == orderan_terpilih].index[0] + 2
                        sheet.update_cell(indeks_baris, 14, "Selesai")
                        st.success(f"👍 Berhasil! Status orderan atas nama {orderan_terpilih} sekarang sudah SELESAI!")
                        st.rerun()
                else:
                    st.info("Semua orderan toko saat ini sudah selesai diproses! Mantap! 🎉")
                    
    except Exception as d_error:
        st.info(f"💡 Dashboard Menunggu data: {d_error}")
