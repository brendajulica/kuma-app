import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Kuma Gift Order Control", layout="centered")
st.title("🪻 Kuma Gift Order Control (Server Cloud 24 Jam)")

# ==============================================================================
# 1. KONEKSI GOOGLE SHEETS VIA GSPREAD (VERSI CLOUD SECRETS)
# ==============================================================================
@st.cache_resource
def dapatkan_koneksi_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Mengecek apakah rahasia gspread ada di Secrets
        if "gspread" in st.secrets and "creds" in st.secrets["gspread"]:
            info_kunci = st.secrets["gspread"]["creds"]
            info_dict = json.loads(info_kunci)
            creds = Credentials.from_service_account_info(info_dict, scopes=scope)
            client = gspread.authorize(creds)
            
            # Nama file Google Sheets Anda di Google Drive
            nama_file_sheets = "Database Kuma Gift" 
            return client.open(nama_file_sheets).sheet1
        else:
            st.error("❌ Eror: Struktur [gspread] atau 'creds' tidak ditemukan di menu Secrets Streamlit Cloud!")
            return None
    except Exception as e:
        st.error(f"❌ Eror Sistem Koneksi: {e}")
        return None

sheet = dapatkan_koneksi_sheets()

# ==============================================================================
# 2. FORM INPUTAN UTAMA UNTUK KARYAWAN / HP
# ==============================================================================
st.write("### 📝 Input Orderan Baru")

nama_pelanggan = st.text_input("Nama Pelanggan / Pemesan:")
produk = st.selectbox(
    "Pilih Jenis Produk:", 
    ["Buket A = Artifisial", "Buket B = Boneka", "Buket C = Custom (Snack, Uang, dll)", "Buket F = Fresh (Bunga)", "Buket S = Satin", "Acc", "Tas", "Mahar"]
)
tema_warna = st.text_input("Tema Warna Buket:")

st.write("---")
st.write("### 🚚 Detail Pengiriman / Penerima")
nama_penerima = st.text_input("Nama Penerima:")
no_hp_penerima = st.text_input("No HP Penerima:")
metode = st.radio("Metode Penyerahan Buket:", ["Ambil Sendiri", "Antar / Kirim"])

alamat = "-"
if metode == "Antar / Kirim":
    alamat = st.text_area("Alamat Lengkap Pengiriman:")

# Tanggal Pengambilan otomatis default ke tanggal besok (H-1)
tanggal_ambil = st.date_input("Tanggal Pengambilan / Pengiriman Orderan:", value=datetime.today() + timedelta(days=1))

st.write("---")
st.write("### 💰 Status Pembayaran (Input Angka Saja)")
total_bayar = st.number_input("Total Bayar Seharusnya (Rp):", min_value=0, step=1000, value=0)
dp_awal = st.number_input("DP Awal (Rp):", min_value=0, step=1000, value=0)
kekurangan = total_bayar - dp_awal

if kekurangan > 0:
    st.warning(f"⚠️ Kekurangan Pembayaran: Rp {kekurangan:,.0f}")
elif kekurangan == 0 and total_bayar > 0:
    st.success("✅ Lunas!")

st.write("---")

# Tombol Simpan
if st.button("Simpan Orderan", type="primary"):
    if nama_pelanggan:
        if sheet is not None:
            new_row = [
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                nama_pelanggan,
                produk,
                tema_warna if tema_warna else "-",
                nama_penerima if nama_penerima else "-",
                no_hp_penerima if no_hp_penerima else "-",
                metode,
                alamat if alamat else "-",
                tanggal_ambil.strftime("%Y-%m-%d"),
                int(total_bayar),
                int(dp_awal),
                int(kekurangan)
            ]
            sheet.append_row(new_row)
            st.success(f"🎉 Sukses! Orderan atas nama {nama_pelanggan} masuk ke Google Sheets!")
            st.rerun()
        else:
            st.error("❌ Tombol tidak berfungsi karena koneksi ke Google Sheets terputus. Lihat detail eror di bagian atas halaman.")
    else:
        st.error("Nama pelanggan wajib diisi!")

# ==============================================================================
# 3. 🏛️ DASHBOARD PEMILAH LIVE (H-1 & H-2 YANG SUDAH DIPERBAIKI)
# ==============================================================================
if sheet is not None:
    try:
        records = sheet.get_all_records()
        if records:
            df_all = pd.DataFrame(records)
            
            st.write("---")
            st.write("## 🏛️ DASHBOARD LIVE ORDERAN KUMA GIFT")
            
            # Hitung otomatis tanggal besok (H-1) dan lusa (H-2)
            besok_str = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            lusa_str = (datetime.today() + timedelta(days=2)).strftime("%Y-%m-%d")
            
            # Memilah data berdasarkan kolom Tanggal Pengambilan
            if "Tanggal Pengambilan" in df_all.columns:
                df_h1 = df_all[df_all["Tanggal Pengambilan"] == besok_str]
                df_h2 = df_all[df_all["Tanggal Pengambilan"] == lusa_str]
            else:
                df_h1 = pd.DataFrame()
                df_h2 = pd.DataFrame()
            
            # Tampilan menu TAB Dashboard
            tab1, tab2, tab3 = st.tabs(["🚨 Semua Orderan", "⏳ Orderan H-1 (Esok Hari)", "🗓️ Orderan H-2 (Lusa)"])
            
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
    except Exception as d_error:
        st.info(f"💡 Dashboard Menunggu data: {d_error}")
