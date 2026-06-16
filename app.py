import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json
import io

st.set_page_config(page_title="Kuma Gift Order Control", layout="wide")
st.title("🪻 Kuma Gift Order Control (Auto-Fill System)")

# ==============================================================================
# 1. KONEKSI GOOGLE SHEETS
# ==============================================================================
@st.cache_resource
def dapatkan_koneksi_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gspread" in st.secrets and "creds" in st.secrets["gspread"]:
            info_kunci = st.secrets["gspread"]["creds"]
            info_dict = json.loads(info_kunci)
            creds = Credentials.from_service_account_info(info_dict, scopes=scope)
            client = gspread.authorize(creds)
            return client.open("Database Kuma Gift").sheet1
    except:
        return None
    return None

sheet = dapatkan_koneksi_sheets()

# ==============================================================================
# 2. LOAD DATA UNTUK AUTO-FILL
# ==============================================================================
df_histori = pd.DataFrame()
if sheet:
    try:
        records = sheet.get_all_records()
        df_histori = pd.DataFrame(records)
    except:
        pass

# ==============================================================================
# 3. FORM INPUTAN DENGAN AUTO-FILL BERBASIS NO HP
# ==============================================================================
st.write("### 📝 Formulir Input Pesanan")

# -- INPUT NO HP TERLEBIH DAHULU --
input_hp = st.text_input("Masukkan No HP Pelanggan (Deteksi Data):")

# Cek apakah No HP ada di histori
data_lama = None
if input_hp and not df_histori.empty:
    # Filter data berdasarkan No HP (Kolom No HP Penerima)
    mask = df_histori["No HP Penerima"].astype(str) == input_hp
    if mask.any():
        data_lama = df_histori[mask].iloc[-1]
        st.success(f"✅ Data ditemukan untuk No HP: {input_hp}")

# -- INPUTAN LAIN --
with st.container(border=True):
    # Nama otomatis terisi jika data ada, tapi bisa diedit
    nama = st.text_input("Nama Pelanggan:", value=data_lama["Nama Pelanggan"] if data_lama is not None else "")
    produk = st.selectbox("Pilih Jenis Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
    tema = st.text_input("Tema Warna:")

with st.container(border=True):
    # Alamat otomatis terisi, tapi TETAP BISA DIEDIT manual
    alamat = st.text_area("Alamat Pengiriman:", value=data_lama["Alamat Lengkap Pengiriman"] if data_lama is not None else "")
    catatan = st.text_area("Catatan Khusus:")
    tanggal_ambil = st.date_input("Tanggal Pengambilan:", value=datetime.today() + timedelta(days=1))

# -- TOMBOL SIMPAN --
if st.button("Simpan Orderan", type="primary"):
    if nama and input_hp:
        jam_wib = pd.Timestamp.now(tz="Asia/Jakarta")
        sheet.append_row([
            jam_wib.strftime("%Y-%m-%d"), jam_wib.strftime("%H:%M"),
            nama, produk, tema, nama, input_hp, "Antar / Kirim", alamat, catatan,
            tanggal_ambil.strftime("%Y-%m-%d"), 0, 0, 0, "Belum Selesai"
        ])
        st.success(f"🎉 Sukses! Data pelanggan {nama} tersimpan.")
        st.rerun()
    else:
        st.error("Nama dan No HP wajib diisi!")
