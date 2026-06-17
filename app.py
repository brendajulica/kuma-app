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
    
    # Konversi ke format datetime agar bisa diolah (untuk perhitungan bulan/tahun)
    df_histori["Tanggal Input"] = pd.to_datetime(df_histori["Tanggal Input"], errors='coerce')
    df_histori["Tanggal Pengambilan"] = pd.to_datetime(df_histori["Tanggal Pengambilan"], errors='coerce')
    
    # Membersihkan status agar tidak ada spasi
    df_histori["Status"] = df_histori["Status"].astype(str).str.strip()

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
            # 1. Definisikan Katalog
            katalog = {
                "Buket": ["Buket Satin", "Buket Fresh Flower", "Buket Snack", "Buket Boneka", "Buket Uang"],
                "Bloom Box": ["Bloom Box PVC", "Bloom Box Bunga"],
                "Hampers": ["Parcel Buah", "Hampers Lebaran", "Hampers Custom"],
                "Lainnya": ["Seserahan", "Mahar", "Frame", "Papan Akrilik"]
            }
            
            # 2. Selectbox Kategori
            pilih_kategori = st.selectbox("Pilih Kategori:", list(katalog.keys()))
            
            # 3. Selectbox Produk (isi otomatis berdasarkan pilihan kategori)
            produk = st.selectbox("Pilih Jenis Produk:", katalog[pilih_kategori])
            
            metode = st.selectbox("Metode Penyerahan:", ["Antar/Kirim", "Ambil di Toko"])
        with col3:
            total = st.number_input("Total Bayar:", min_value=0)
            dp = st.number_input("DP Awal:", min_value=0)
            
        tema = st.text_input("Tema Warna Buket:")
        alamat = st.text_area("Alamat Lengkap Pengiriman:")
        catatan = st.text_area("Catatan Khusus:")
        tgl_ambil = st.date_input("Tanggal Pengambilan:", value=datetime.now() + timedelta(days=1))
        
        if st.button("Simpan Orderan", type="primary"):
            # Mengambil waktu saat tombol diklik
            waktu_klik = datetime.now()
            
            # Memisahkan tanggal dan jam
            tgl_input = waktu_klik.strftime("%Y-%m-%d")
            jam_input = waktu_klik.strftime("%H:%M:%S")
    
            # Masukkan ke data_baru (sesuai urutan header Anda)
            data_baru = [
                tgl_input,              # Kolom A: Tanggal Input
                jam_input,              # Kolom B: Jam Input
                nama,                   # Kolom C
                pilih_kategori,         # Kolom D
                produk,                 # Kolom E
                tema,                   # Kolom F
                nama,                   # Kolom G
                input_hp,               # Kolom H
                metode,                 # Kolom I
                alamat,                 # Kolom J
                catatan,                # Kolom K
                tgl_ambil.strftime("%Y-%m-%d"), # Kolom L
                total,                  # Kolom M
                dp,                     # Kolom N
                (total - dp),           # Kolom O
                "Belum Selesai",        # Kolom P
                nama_admin              # Kolom Q
            ]
            
            sheet.append_row(data_baru)
            st.success("Data tersimpan!")
            st.rerun()

# 3. 🏛️ DASHBOARD PEMILAH LIVE
    if sheet is not None:
        try:
            if not df_histori.empty:
                st.write("---")
                st.write("## 🏛️ DASHBOARD LIVE ORDERAN KUMA GIFT")
                
                # Tombol Download Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_histori.to_excel(writer, index=False, sheet_name='Semua Orderan')
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
                hari_ini = datetime.now().date()
                besok_str = (hari_ini + timedelta(days=1))
                lusa_str = (hari_ini + timedelta(days=2))
                hari_ke3_str = (hari_ini + timedelta(days=3))
                hari_ke7_str = (hari_ini + timedelta(days=7))
                
                if "Status" in df_histori.columns and "Tanggal Pengambilan" in df_histori.columns:
                    df_aktif = df_histori[df_histori["Status"] == "Belum Selesai"].copy()
                    df_aktif['Tgl_Check'] = df_aktif['Tanggal Pengambilan'].dt.date
                    
                    df_h1 = df_aktif[df_aktif["Tgl_Check"] == besok_str]
                    df_h2 = df_aktif[df_aktif["Tgl_Check"] == lusa_str]
                    df_h3 = df_aktif[df_aktif["Tgl_Check"] == hari_ke3_str]
                    df_h7 = df_aktif[df_aktif["Tgl_Check"] == hari_ke7_str]
                else:
                    df_aktif, df_h1, df_h2, df_h3, df_h7 = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
                
                # Menu Tab Dashboard
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "🚨 Semua Belum Selesai", 
                    "⏳ H-1 (Besok)", 
                    "🗓️ H-2 (Lusa)",
                    "📅 H-3 (3 Hari)",
                    "📆 H-7 (Seminggu)", 
                    "✅ Tandai Selesai"
                ])
                
                with tab1:
                    st.write("### Master Data")
                    # Buat salinan data hanya untuk tampilan
                    df_tampil = df_aktif.copy()
    
                    # Ubah format menjadi string agar rapi (YYYY-MM-DD)
                    df_tampil["Tanggal Input"] = df_tampil["Tanggal Input"].dt.strftime('%Y-%m-%d')
                    df_tampil["Tanggal Pengambilan"] = df_tampil["Tanggal Pengambilan"].dt.strftime('%Y-%m-%d')
    
                    st.dataframe(df_tampil, use_container_width=True)
                    
                with tab2:
                    st.write(f"### 📋 Rangkaian Buket Harus Siap Besok ({besok_str.strftime('%Y-%m-%d')})")
                    if not df_h1.empty:
                        st.dataframe(df_h1.drop(columns=['Tgl_Check'], errors='ignore'), use_container_width=True)
                    else:
                        st.info("Aman! Tidak ada pesanan untuk besok.")
                        
                with tab3:
                    st.write(f"### 📋 Persiapan Bahan / Buket untuk Lusa ({lusa_str.strftime('%Y-%m-%d')})")
                    if not df_h2.empty:
                        st.dataframe(df_h2.drop(columns=['Tgl_Check'], errors='ignore'), use_container_width=True)
                    else:
                        st.info("Aman! Tidak ada pesanan untuk lusa.")

                with tab4:
                    st.write(f"### 📦 List Orderan Masuk untuk 3 Hari ke Depan ({hari_ke3_str.strftime('%Y-%m-%d')})")
                    if not df_h3.empty:
                        st.dataframe(df_h3.drop(columns=['Tgl_Check'], errors='ignore'), use_container_width=True)
                    else:
                        st.info("Aman! Belum ada pesanan masuk untuk 3 hari ke depan.")

                with tab5:
                    st.write(f"### 💐 Persiapan Stok & Bahan untuk Seminggu ke Depan ({hari_ke7_str.strftime('%Y-%m-%d')})")
                    if not df_h7.empty:
                        st.dataframe(df_h7.drop(columns=['Tgl_Check'], errors='ignore'), use_container_width=True)
                    else:
                        st.info("Aman! Belum ada pesanan masuk untuk tepat seminggu ke depan.")

                with tab6:
                    st.write("### 🛠️ Tandai Pesanan yang Sudah Diambil / Dikirim")
                    if not df_aktif.empty:
                        # --- PERBAIKAN DI SINI ---
                        # Menggabungkan Nama Pelanggan, Jenis Produk, dan Tanggal Pengambilan agar informasi dropdown lengkap dan sangat jelas
                        df_aktif["Dropdown_Label"] = (
                            df_aktif["Nama Pelanggan"].astype(str) + 
                            " -> [" + df_aktif["Pilih Jenis Produk"].astype(str) + "] " +
                            " (Ambil: " + df_aktif["Tanggal Pengambilan"].dt.strftime('%d-%m-%Y') + ")"
                        )
                        pilihan_label = df_aktif["Dropdown_Label"].tolist()
                        
                        orderan_terpilih = st.selectbox("Pilih Orderan Pelanggan yang Sudah Selesai:", pilihan_label)
                        
                        st.warning(f"⚠️ **PENTING:** Pastikan Anda benar-benar ingin menyelesaikan pesanan: **{orderan_terpilih}**.")
                        konfirmasi_benar = st.checkbox("Ya, saya sudah memeriksa dan data ini sudah benar.")
                        
                        if st.button("Ubah Status Jadi SELESAI ✅", use_container_width=True, disabled=not konfirmasi_benar):
                            # Membuat pencocokan label yang sama pada data utama
                            df_histori["Dropdown_Label_Master"] = (
                                df_histori["Nama Pelanggan"].astype(str) + 
                                " -> [" + df_histori["Pilih Jenis Produk"].astype(str) + "] " +
                                " (Ambil: " + df_histori["Tanggal Pengambilan"].dt.strftime('%d-%m-%Y') + ")"
                            )
                            indeks_baris = df_histori[df_histori["Dropdown_Label_Master"] == orderan_terpilih].index[0] + 2
                            
                            # Update status ke kolom ke-15 di Google Sheets
                            sheet.update_cell(indeks_baris, 15, "Selesai")
                            st.success(f"👍 Berhasil! Status orderan {orderan_terpilih} sekarang sudah SELESAI!")
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.info("Semua orderan toko saat ini sudah selesai diproses! Mantap! 🎉")
            else:
                st.warning("Menunggu data masuk dari Google Sheets... Pastikan lembar kerja Anda tidak kosong.")
                        
        except Exception as d_error:
            st.error(f"🚨 Terjadi gangguan sistem pembacaan dashboard: {d_error}")
    else:
        st.error("Koneksi aplikasi ke Google Sheets terputus.")
        
# 4. TAB LAPORAN BULANAN
with tab_laporan:
    st.subheader("📊 Analisis Penjualan")
    if not df_histori.empty and "Tanggal Input" in df_histori.columns:
        df_valid = df_histori.dropna(subset=["Tanggal Input"]).copy()
        now = datetime.now()
        df_bulan = df_valid[(df_valid["Tanggal Input"].dt.month == now.month) & (df_valid["Tanggal Input"].dt.year == now.year)]
        
        if not df_bulan.empty:
            # 1. Tampilan Ringkasan Finansial (Metrics)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Order Bulan Ini", len(df_bulan))
            
            omset = df_bulan['Total Bayar Seharusnya'].sum() if 'Total Bayar Seharusnya' in df_bulan.columns else 0
            dp_masuk = df_bulan['DP Awal'].sum() if 'DP Awal' in df_bulan.columns else 0
            
            c2.metric("Omset Bulan Ini", f"Rp {omset:,.0f}")
            c3.metric("DP Masuk", f"Rp {dp_masuk:,.0f}")
            
            st.write("---")
            
            # 2. Tampilan Jumlah Inputan per Admin (Fitur Baru)
            st.write("### 👩‍💻 Produktivitas Admin (Bulan Ini)")
            if "Nama Admin" in df_bulan.columns:
                # Menghitung jumlah inputan per admin dan mengubahnya menjadi tabel yang rapi
                df_admin = df_bulan["Nama Admin"].value_counts().reset_index()
                df_admin.columns = ["Nama Admin", "Jumlah Input Pesanan"]
                
                # Menampilkan tabel produktivitas admin di dashboard
                st.dataframe(df_admin, use_container_width=True, hide_index=True)
            else:
                st.warning("Kolom 'Nama Admin' tidak ditemukan di Google Sheets.")
                
        else:
            st.info("Belum ada data transaksi yang tercatat untuk bulan ini.")
