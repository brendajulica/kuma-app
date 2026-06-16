import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Kuma Gift Order Control", layout="wide")
st.title("🪻 Kuma Gift Order Control (Full Integrated)")

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

# 2. LOAD DATA UNTUK AUTO-FILL
df_histori = pd.DataFrame()
if sheet:
    try:
        df_histori = pd.DataFrame(sheet.get_all_records())
    except:
        pass

# 3. FORM INPUT
st.subheader("📝 Form Input Pesanan")
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        input_hp = st.text_input("No HP Pelanggan (Deteksi Data):")
        # Auto-fill logika
        data_lama = df_histori[df_histori["No HP Penerima"].astype(str) == input_hp].iloc[-1] if not df_histori.empty and input_hp in df_histori["No HP Penerima"].astype(str).values else None
        nama = st.text_input("Nama Pelanggan:", value=data_lama["Nama Pelanggan"] if data_lama is not None else "")
    with col2:
        produk = st.selectbox("Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
        tema = st.text_input("Tema Warna:")
    
    alamat = st.text_area("Alamat Pengiriman:", value=data_lama["Alamat Lengkap Pengiriman"] if data_lama is not None else "")
    
    if st.button("Simpan Orderan", type="primary", use_container_width=True):
        if sheet and nama and input_hp:
            now = datetime.now()
            sheet.append_row([now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), nama, produk, tema, nama, input_hp, "Antar/Kirim", alamat, "-", (now + timedelta(days=1)).strftime("%Y-%m-%d"), 0, 0, 0, "Belum Selesai"])
            st.success("Tersimpan!")
            st.rerun()

# 4. DASHBOARD
st.subheader("🏛️ Dashboard Live")
if sheet and not df_histori.empty:
    df_aktif = df_histori[df_histori["Status"] == "Belum Selesai"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚨 Semua Aktif", "⏳ H-1", "🗓️ H-2", "📅 H-3", "📆 H-7", "✅ Tandai Selesai"])
    
    with tab1: st.dataframe(df_aktif, use_container_width=True)
    with tab2: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab3: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab4: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab5: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab6:
        df_aktif["Dropdown"] = df_aktif["Nama Pelanggan"] + " (" + df_aktif["Pilih Jenis Produk"] + ")"
        pilihan = st.selectbox("Pilih yang Selesai:", df_aktif["Dropdown"].tolist())
        if st.button("Ubah ke SELESAI"):
            idx = df_histori[df_histori["Nama Pelanggan"] + " (" + df_histori["Pilih Jenis Produk"] + ")" == pilihan].index[0] + 2
            sheet.update_cell(idx, 15, "Selesai")
            st.rerun()
