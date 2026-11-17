import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

st.set_page_config(page_title="SIBIMA Performance Dashboard", layout="wide", page_icon="📈")

# Fungsi load data dengan cache dinamis
@st.cache_data(ttl=10)
def load_data(url, header_row=0):
    try:
        df = pd.read_csv(url, header=header_row)
        df.columns = df.columns.str.replace('\n', ' ').str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

# SIDEBAR NAVIGATION
st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSuPAMy4KN4jFEnYc3C6xHVWnXsylZ6c0wMrIkFSuRY3IphB8EOdoVf1gII&s=10", width=100)
st.sidebar.title("Navigasi Central Procurement & Project")
mode = st.sidebar.radio("Pilih Dashboard:", [
    "🏢 Central Procurement & Interco", 
    "🏗️ Project (YTP Tahap 2 & 3)"
])
st.sidebar.divider()
st.sidebar.caption("Data terhubung langsung ke Google Sheets (Live Sync).")

# ==========================================
# MODE 1: CENTRAL PROCUREMENT & INTERCO
# ==========================================
if mode == "🏢 Central Procurement & Interco":
    st.title("SIBIMA Performance Dashboard - PROCUREMENT & INTERCO")
    st.caption("Pusat monitoring RFQ, Konversi SQ ke PO, Analisis Transaksi, Analisis Vendor, dan Outstanding Supply.")

    URL_RFQ = "https://docs.google.com/spreadsheets/d/18isSUeBYGiM2xuhV8QsXP57_AOotJ07vu1dvd5i62GI/export?format=csv&gid=1100229590"
    URL_ORDER = "https://docs.google.com/spreadsheets/d/18isSUeBYGiM2xuhV8QsXP57_AOotJ07vu1dvd5i62GI/export?format=csv&gid=467075902"

    df_rfq = load_data(URL_RFQ, header_row=1)
    df_order = load_data(URL_ORDER, header_row=0)

    # Pemisahan Tab Interco
    tab_i1, tab_i2, tab_i3, tab_i4, tab_i5 = st.tabs([
        "📊 Overview & Detail Transaksi", 
        "🔍 Monitoring RFQ (Pending & Kendala)", 
        "📈 Konversi SQ ke PO", 
        "📋 Analisis Vendor",
        "🚚 Outstanding Supply Vendor"
    ])

    # --- TAB 1: OVERVIEW & DETAIL TRANSAKSI ---
    with tab_i1:
        if not df_rfq.empty and not df_order.empty:
            df_rfq['TANGGAL RFQ'] = pd.to_datetime(df_rfq['TANGGAL RFQ'], errors='coerce')
            min_date = df_rfq['TANGGAL RFQ'].min().date() if not df_rfq['TANGGAL RFQ'].isnull().all() else datetime.today().date()
            max_date = df_rfq['TANGGAL RFQ'].max().date() if not df_rfq['TANGGAL RFQ'].isnull().all() else datetime.today().date()
            
            kat_col_order = next((c for c in df_order.columns if 'KATEGORI' in str(c).upper()), None)
            list_cust_options = ["Semua"] + sorted(list(df_order[kat_col_order].dropna().unique())) if kat_col_order and not df_order[kat_col_order].dropna().empty else ["Semua"]

            st.write("### Filter Dashboard Interco")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1: date_range = st.date_input("Select Date Range 📅", [min_date, max_date], key="i_date")
            with f_col2: pilih_status = st.selectbox("Cari Status 🔍", ["Semua"] + list(df_order['STATUS'].dropna().unique()), key="i_stat")
            with f_col3: pilih_cust = st.selectbox("Pilih Customer (Kategori) 👤", list_cust_options, key="i_cust")
            with f_col4: pilih_no = st.text_input("Cari Nomor Transaksi (SO/PO) 🔍", key="i_no")

            df_order_filtered = df_order.copy()
            if pilih_status != "Semua": df_order_filtered = df_order_filtered[df_order_filtered['STATUS'] == pilih_status]
            if pilih_cust != "Semua" and kat_col_order: df_order_filtered = df_order_filtered[df_order_filtered[kat_col_order] == pilih_cust]
            if pilih_no: df_order_filtered = df_order_filtered[df_order_filtered.astype(str).apply(lambda x: x.str.contains(pilih_no, case=False, na=False)).any(axis=1)]

            # Fungsi pembersihan nilai numerik/harga
            def clean_price(val):
                if pd.isna(val): return 0.0
                s = str(val).replace('Rp', '').replace('idr', '').strip()
                if ',' in s and '.' in s:
                    if s.find('.') < s.find(','): s = s.replace('.', '').replace(',', '.')
                    else: s = s.replace(',', '')
                elif ',' in s:
                    if len(s.split(',')[-1]) == 3: s = s.replace(',', '')
                    else: s = s.replace(',', '.')
                elif s.count('.') > 1: s = s.replace('.', '', s.count('.') - 1)
                try: return float(s)
                except: return 0.0

            # Deteksi Kolom QTY, Harga Satuan, dan HPP untuk perhitungan otomatis di Python
            qty_col = next((c for c in df_order_filtered.columns if 'QTY' in str(c).upper() or 'QUANTITY' in str(c).upper()), None)
            price_col = next((c for c in df_order_filtered.columns if any(k in str(c).upper() for k in ['HARGA JUAL', 'TOTAL HARGA', 'GRAND TOTAL', 'TOTAL', 'PRICE'])), None)
            unit_price_col = next((c for c in df_order_filtered.columns if any(k in str(c
