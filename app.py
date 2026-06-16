import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json
import io

st.set_page_config(page_title="Kuma Gift Order Control", layout="centered")
st.title("🪻 Kuma Gift Order Control (Server Cloud 24 Jam)")

# ==============================================================================
# 1. KONEKSI GOOGLE SHEETS VIA GSPREAD
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
            nama_file_sheets = "Database Kuma Gift" 
            return client.open(nama_file_sheets).sheet1
        else:
            return None
    except Exception:
        return None

sheet = dapatkan_koneksi_sheets()

# ==============================================================================
# SIKLUS PEMBERSIH FORM
# ==============================================================================
if "input_counter" not in st.session_state:
    st.session_state["input_counter"] = 0

kunci_bantu = f"v1_{st.session_state['input_counter']}"

# ==============================================================================
# 2. FORM INPUTAN UTAMA
# ==============================================================================
st.write("### 📝 Formulir Input Pesanan")

with st.container(border=True):
    nama_pelanggan = st.text_input("Nama Pelanggan / Pemesan:", key=f"nama_{kunci_bantu}")
    produk = st.selectbox("Pilih Jenis Produk:", ["Buket A = Artifisial", "Buket B = Boneka", "Buket C = Custom (Snack, Uang, dll)", "Buket F = Fresh (Bunga)", "Buket S = Satin", "Acc", "Tas", "Mahar"], key=f"prod_{kunci_bantu}")
    tema_warna = st.text_input("Tema Warna Buket:", key=f"warna_{kunci_bantu}")

with st.container(border=True):
    sama_dengan_pemesan = st.checkbox("Nama Penerima sama dengan Nama Pelanggan", key=f"cek_{kunci_bantu}")
    if sama_dengan_pemesan:
        nama_penerima = st.text_input("Nama Penerima:", value=nama_pelanggan, disabled=True, key=f"penerima_{kunci_bantu}")
    else:
        nama_penerima = st.text_input("Nama Penerima:", key=f"penerima_{kunci_bantu}")
        
    no_hp_penerima = st.text_input("No HP Penerima:", key=f"hp_{kunci_bantu}")
    metode = st.radio("Metode Penyerahan Buket:", ["Ambil Sendiri", "Antar / Kirim"], key=f"metode_{kunci_bantu}")
    alamat = st.text_area("Alamat Lengkap Pengiriman:", key=f"alamat_{kunci_bantu}") if metode == "Antar / Kirim" else "-"
    catatan_khusus = st.text_area("Catatan Khusus:", value="-", key=f"catat_{kunci_bantu}")
    tanggal_ambil = st.date_input("Tanggal Pengambilan / Pengiriman Orderan:", value=datetime.today() + timedelta(days=1), key=f"tgl_{kunci_bantu}")

if st.button("Simpan Orderan", type="primary", use_container_width=True):
    if nama_pelanggan and sheet:
        waktu_sekarang = pd.Timestamp.now(tz="Asia/Jakarta")
        sheet.append_row([
            waktu_sekarang.strftime("%Y-%m-%d"), waktu_sekarang.strftime("%H:%M"),
            nama_pelanggan, produk, tema_warna, nama_penerima, no_hp_penerima,
            metode, alamat, catatan_khusus, tanggal_ambil.strftime("%Y-%m-%d"),
            0, 0, 0, "Belum Selesai"
        ])
        st.session_state["input_counter"] += 1
        st.success("🎉 Sukses tersimpan!")
        st.rerun()

# ==============================================================================
# 3. DASHBOARD LIVE
# ==============================================================================
if sheet:
    try:
        records = sheet.get_all_records()
        if records:
            df_all = pd.DataFrame(records)
            st.write("---")
            st.write("## 🏛️ DASHBOARD LIVE ORDERAN")
            
            # Filter hanya yang aktif
            df_aktif = df_all[df_all["Status"] == "Belum Selesai"]
            
            # Tabs
            tab1, tab6 = st.tabs(["🚨 Semua Aktif", "✅ Tandai Selesai"])
            
            with tab1:
                st.dataframe(df_aktif)
            
            with tab6:
                if not df_aktif.empty:
                    df_aktif["Tampilan"] = df_aktif["Nama Pelanggan"] + " (" + df_aktif["Pilih Jenis Produk"] + ")"
                    pilihan = st.selectbox("Pilih yang sudah selesai:", df_aktif["Tampilan"].tolist())
                    if st.button("Ubah Jadi SELESAI ✅"):
                        indeks = df_all[df_all["Nama Pelanggan"] == pilihan.split(" (")[0]].index[0] + 2
                        sheet.update_cell(indeks, 15, "Selesai")
                        st.rerun()
                else:
                    st.info("Semua orderan sudah selesai!")
    except Exception as e:
        st.error(f"Eror saat memuat dashboard: {e}")
