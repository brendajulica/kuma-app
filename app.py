import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Kuma Gift Order Control", layout="wide")
st.title("🪻 Kuma Gift Order Control (System Integrated)")

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
        # Bersihkan kolom nomor HP agar selalu terbaca sebagai teks
        if not df_histori.empty:
            df_histori["No HP Penerima"] = df_histori["No HP Penerima"].astype(str).str.strip()
    except:
        pass

# 2. FORM INPUT
st.subheader("📝 Form Input Pesanan")
with st.container(border=True):
    nama_admin = st.selectbox("Pilih Nama Admin:", ["Admin 1", "Admin 2", "Admin 3"])
    col1, col2 = st.columns(2)
    with col1:
        input_hp = st.text_input("No HP Pelanggan (Cek Histori):")
        
        # Logika Auto-Fill
        input_hp_clean = str(input_hp).strip()
        data_lama = None
        if not df_histori.empty and input_hp_clean in df_histori["No HP Penerima"].values:
            data_lama = df_histori[df_histori["No HP Penerima"] == input_hp_clean].iloc[-1]
            
        nama = st.text_input("Nama Pelanggan:", value=data_lama["Nama Pelanggan"] if data_lama is not None else "")
    with col2:
        produk = st.selectbox("Pilih Jenis Produk:", ["Buket A", "Buket B", "Buket C", "Buket F", "Buket S", "Acc", "Tas", "Mahar"])
        tema = st.text_input("Tema Warna Buket:", value=data_lama["Tema Warna Buket"] if data_lama is not None else "")
    
    alamat = st.text_area("Alamat Lengkap Pengiriman:", value=data_lama["Alamat Lengkap Pengiriman"] if data_lama is not None else "")
    catatan = st.text_area("Catatan Khusus:")
    tgl_ambil = st.date_input("Tanggal Pengambilan:", value=datetime.now() + timedelta(days=1))
    
    if st.button("Simpan Orderan", type="primary", use_container_width=True):
        if sheet and nama and input_hp:
            now = datetime.now()
            # Menyimpan ke 16 kolom
            sheet.append_row([
                now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), nama, produk, tema, nama, 
                input_hp, "Antar/Kirim", alamat, catatan, tgl_ambil.strftime("%Y-%m-%d"), 
                0, 0, 0, "Belum Selesai", nama_admin
            ])
            st.success(f"Berhasil disimpan oleh {nama_admin}!")
            st.rerun()

# 3. DASHBOARD
st.subheader("🏛️ Dashboard Live")
if sheet and not df_histori.empty:
    df_aktif = df_histori[df_histori["Status"] == "Belum Selesai"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚨 Semua", "⏳ H-1", "🗓️ H-2", "📅 H-3", "📆 H-7", "✅ Selesai"])
    
    with tab1: st.dataframe(df_aktif, use_container_width=True)
    with tab2: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab3: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab4: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab5: st.dataframe(df_aktif[df_aktif["Tanggal Pengambilan"] == (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")], use_container_width=True)
    with tab6:
        if not df_aktif.empty:
            df_aktif["Display"] = df_aktif["Nama Pelanggan"] + " (" + df_aktif["Pilih Jenis Produk"] + ")"
            pilihan = st.selectbox("Pilih yang sudah selesai:", df_aktif["Display"].tolist())
            if st.button("Ubah Status Jadi SELESAI"):
                idx = df_histori[df_histori["Nama Pelanggan"] + " (" + df_histori["Pilih Jenis Produk"] + ")" == pilihan].index[0] + 2
                sheet.update_cell(idx, 15, "Selesai")
                st.rerun()
