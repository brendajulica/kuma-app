# ==============================================================================
# 1. KONEKSI GOOGLE SHEETS VIA GSPREAD (VERSI CLOUD SECRETS - LACAK EROR)
# ==============================================================================
@st.cache_resource
def dapatkan_koneksi_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Membaca info kredensial langsung dari kotak hitam Secrets [gspread]
        info_kunci = st.secrets["gspread"]["creds"]
        
        import json
        info_dict = json.loads(info_kunci)
        
        creds = Credentials.from_service_account_info(info_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        nama_file_sheets = "Database Kuma Gift" 
        return client.open(nama_file_sheets).sheet1
    except Exception as e:
        # Menampilkan pesan eror asli dari sistem Google/Streamlit di layar aplikasi
        st.error(f"Eror Sistem yang Terjadi: {e}")
        return None
        import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

st.set_page_config(page_title="Kuma Gift Order Control", layout="centered")
st.title("🪻 Kuma Gift Order Control (Server Cloud 24 Jam)")

# ==============================================================================
# 1. KONEKSI GOOGLE SHEETS VIA GSPREAD
# ==============================================================================
# 1. KONEKSI GOOGLE SHEETS VIA GSPREAD (VERSI CLOUD SECRETS)
# ==============================================================================
@st.cache_resource
def dapatkan_koneksi_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Membaca info kredensial langsung dari kotak hitam Secrets [gspread]
        info_kunci = st.secrets["gspread"]["creds"]
        
        # Mengubah teks rahasia menjadi objek kredensial resmi
        import json
        info_dict = json.loads(info_kunci)
        
        creds = Credentials.from_service_account_info(info_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Nama file spreadsheet Anda di Google Drive
        nama_file_sheets = "Database Kuma Gift" 
        return client.open(nama_file_sheets).sheet1
    except Exception as e:
        return None

sheet = dapatkan_koneksi_sheets()

# ==============================================================================
# 2. FORM INPUTAN UTAMA UNTUK KARYAWAN / HP
# ==============================================================================
st.write("### 📝 Input Orderan Baru")

nama_pelanggan = st.text_input("Nama Pelanggan / Pemesan:")
produk = st.selectbox(
    "Pilih Jenis Produk:", 
    [
        "Buket A = Artifisial", 
        "Buket B = Boneka", 
        "Buket C = Custom (Snack, Uang, dll)", 
        "Buket F = Fresh (Bunga)", 
        "Buket S = Satin", 
        "Acc", 
        "Tas", 
        "Mahar"
    ]
)
tema_warna = st.text_input("Tema Warna Buket:")

st.write("---")
st.write("### 🚚 Detail Pengiriman / Penerima")
nama_penerima = st.text_input("Nama Penerima:")
no_hp_penerima = st.text_input("No HP Penerima:")
metode = st.radio("Metode Penyerahan Buket:", ["Ambil Sendiri", "Antar / Kirim"])

# Alamat hanya wajib diisi dan muncul jika memilih opsi "Antar / Kirim"
alamat = "-"
if metode == "Antar / Kirim":
    alamat = st.text_area("Alamat Lengkap Pengiriman:")

# Tanggal Pengambilan otomatis default ke tanggal besok (H-1)
tanggal_ambil = st.date_input("Tanggal Pengambilan / Pengiriman Orderan:", value=datetime.today() + timedelta(days=1))

st.write("---")
st.write("### 💰 Status Pembayaran (Input Angka Saja, Tanpa Titik/Rp)")
total_bayar = st.number_input("Total Bayar Seharusnya (Rp):", min_value=0, step=1000, value=0)
dp_awal = st.number_input("DP Awal (Rp):", min_value=0, step=1000, value=0)

# Sistem Otomatis Menghitung Kekurangan
kekurangan = total_bayar - dp_awal

# Menampilkan sisa kekurangan secara langsung dengan warna interaktif
if kekurangan > 0:
    st.warning(f"⚠️ Kekurangan Pembayaran: Rp {kekurangan:,.0f}")
elif kekurangan == 0 and total_bayar > 0:
    st.success("✅ Lunas!")
else:
    st.write(f"Sisa: Rp {kekurangan:,.0f}")

st.write("---")

# Tombol Simpan - Data langsung dikunci ke Google Sheets secara Online
if st.button("Simpan Orderan", type="primary"):
    if nama_pelanggan:
        if sheet is not None:
            # Susunan data baris baru untuk dikirim ke Google Sheets
            new_row = [
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), # Tanggal Input otomatis jam sekarang
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
            
            # Perintah memasukkan data ke baris paling bawah Google Sheets
            sheet.append_row(new_row)
            
            st.success(f"🎉 Sukses! Orderan atas nama {nama_pelanggan} langsung masuk ke Google Sheets Toko!")
            st.rerun()
        else:
            st.error("❌ Gagal terhubung ke Google Sheets! Pastikan file 'creds.json' sudah diletakkan di folder KumaApps dan Google Sheets sudah dibagikan (Share) ke email robot.")
    else:
        st.error("Nama pelanggan wajib diisi!")

# ==============================================================================
# 3. 🏛️ DASHBOARD PEMILAH LIVE (H-1 & H-2 REALTIME DARI GOOGLE SHEETS)
# ==============================================================================
if sheet is not None:
    try:
        # Mengambil data real-time terupdate dari Google Sheets
        records = sheet.get_all_records()
        if records:
            df_all = pd.DataFrame(records)
            
            st.write("---")
            st.write("## 🏛️ DASHBOARD LIVE ORDERAN KUMA GIFT")
            
            # Hitung otomatis tanggal besok (H-1) dan lusa (H-2)
            besok_str = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            lusa_str = (datetime.today() + timedelta(days=2)).strftime("%Y-%m-%d")
            
            # Memilah data otomatis berdasarkan tanggal pengambilan yang tertera di Google Sheets
            if "Tanggal Pengambilan" in df_all.columns:
                df_h1 = df_all[df_all["Tanggal Pengambilan"] == besok_str]
                df_h2 = df_all[df_all["Tanggal Pengambilan"] == lusa_str]
            else:
                df_h1 = pd.DataFrame()
                df_h2 = pd.DataFrame()
            
            # Tampilan Tab Dashboard Interaktif
            tab1, tab2, tab3 = st.tabs(["🚨 Semua Orderan", "⏳ Orderan H-1 (Esok Hari)", "🗓️ Orderan H-2 (Lusa)"])
            
            with tab1:
                st.write("### Master Data (Seluruh Orderan di Google Sheets)")
                st.dataframe(df_all)
                
            with tab2:
                st.write(f"### 📋 Rangkaian Buket Harus Siap Hari Ini Untuk Besok ({besok_str})")
                if not df_h1.empty:
                    st.dataframe(df_h1)
                else:
                    st.info("Aman! Tidak ada pesanan rangkaian buket untuk besok.")
                    
            with tab3:
                st.write(f"### 📋 Persiapan Bahan / Buket Stok Untuk Lusa ({lusa_str})")
                if not df_h2.empty:
                    st.dataframe(df_h2)
                else:
                    st.info("Aman! Tidak ada pesanan untuk lusa.")
    except Exception as e:
        st.info("💡 Dashboard siap! Menunggu baris judul kolom pertama di Google Sheets Anda diisi.")
