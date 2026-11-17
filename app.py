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

            # Deteksi Kolom QTY, Harga, HPP, dan No PO Customer
            qty_col = next((c for c in df_order_filtered.columns if 'QTY' in str(c).upper() or 'QUANTITY' in str(c).upper()), None)
            price_col = next((c for c in df_order_filtered.columns if any(k in str(c).upper() for k in ['HARGA JUAL', 'TOTAL HARGA', 'GRAND TOTAL', 'TOTAL', 'PRICE'])), None)
            unit_price_col = next((c for c in df_order_filtered.columns if any(k in str(c).upper() for k in ['SATUAN', 'UNIT PRICE', 'HARGA SATUAN'])), None)
            hpp_col = next((c for c in df_order_filtered.columns if any(k in str(c).upper() for k in ['HPP', 'MODAL', 'COST'])), None)
            po_cust_col = next((c for c in df_order_filtered.columns if any(k in str(c).upper() for k in ['NO PO CUSTOMER', 'PO CUSTOMER', 'NOMOR PO'])), None)

            df_order_filtered['QTY_CLEAN'] = pd.to_numeric(df_order_filtered[qty_col], errors='coerce').fillna(0) if qty_col else 1.0

            if price_col:
                df_order_filtered['PRICE_CLEAN'] = df_order_filtered[price_col].apply(clean_price)
            elif unit_price_col and qty_col:
                df_order_filtered['PRICE_CLEAN'] = df_order_filtered['QTY_CLEAN'] * df_order_filtered[unit_price_col].apply(clean_price)
            else:
                df_order_filtered['PRICE_CLEAN'] = 0.0

            if hpp_col:
                df_order_filtered['HPP_CLEAN'] = df_order_filtered[hpp_col].apply(clean_price)
            else:
                df_order_filtered['HPP_CLEAN'] = 0.0

            st.divider()
            st.write("### 📊 Detail Transaksi & Keuangan (Komersial Eksternal)")
            
            # 1. Pemisahan Data: Komersial Eksternal vs Internal SIBIMA
            if kat_col_order:
                df_komersial = df_order_filtered[
                    (~df_order_filtered['STATUS'].astype(str).str.upper().isin(['CANCEL', 'PENDING'])) &
                    (~df_order_filtered[kat_col_order].astype(str).str.upper().str.contains('SIBIMA'))
                ]
                df_sibima_internal = df_order_filtered[
                    df_order_filtered[kat_col_order].astype(str).str.upper().str.contains('SIBIMA')
                ]
            else:
                df_komersial = df_order_filtered[
                    (~df_order_filtered['STATUS'].astype(str).str.upper().isin(['CANCEL', 'PENDING']))
                ]
                df_sibima_internal = pd.DataFrame()

            # Metrik Keuangan (Harga di sheet = Exclude PPN, Hitung Include PPN dengan dikali 1.11)
            total_revenue_exc = df_komersial['PRICE_CLEAN'].sum()
            total_revenue_inc = total_revenue_exc * 1.11  
            total_hpp_exc = df_komersial['HPP_CLEAN'].sum()
            
            # Total Transaksi dihitung unik berdasarkan Nomor PO Customer
            if po_cust_col and not df_komersial[po_cust_col].dropna().empty:
                total_transaksi = df_komersial[po_cust_col].nunique()
            else:
                total_transaksi = len(df_komersial)
                
            total_item = df_komersial['QTY_CLEAN'].sum()
            
            # Outstanding Balance Komersial (berdasarkan Exclude PPN)
            if kat_col_order:
                outstanding_df = df_order_filtered[
                    (~df_order_filtered['STATUS'].astype(str).str.upper().isin(['SUDAH DITERIMA', 'CANCEL'])) &
                    (~df_order_filtered[kat_col_order].astype(str).str.upper().str.contains('SIBIMA'))
                ]
            else:
                outstanding_df = df_order_filtered[
                    (~df_order_filtered['STATUS'].astype(str).str.upper().isin(['SUDAH DITERIMA', 'CANCEL']))
                ]
                
            balance_outstanding = outstanding_df['PRICE_CLEAN'].sum()
            top_kategori = df_komersial[kat_col_order].mode()[0] if kat_col_order and not df_komersial[kat_col_order].empty else "Tidak Ada"

            # Tampilan Metrik Utama (Komersial Bersih)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Penjualan (Exclude PPN)", f"Rp {total_revenue_exc:,.0f}".replace(',', '.'))
            m2.metric("Penjualan (Include PPN)", f"Rp {total_revenue_inc:,.0f}".replace(',', '.'))
            m3.metric("HPP (Exclude PPN)", f"Rp {total_hpp_exc:,.0f}".replace(',', '.'))
            m4.metric("Outstanding Balance", f"Rp {balance_outstanding:,.0f}".replace(',', '.'))

            m5, m6, m7, m8 = st.columns(4)
            m5.metric("Total Transaksi", total_transaksi)
            m6.metric("Total Item QTY", f"{total_item:,.0f}")
            m7.metric("Kategori Terbanyak", top_kategori)
            
            # 2. Section Tersembunyi (Hidden Expander) untuk Rekapitulasi Internal SIBIMA
            if not df_sibima_internal.empty:
                with st.expander("📁 Lihat Rekapitulasi Transaksi Internal SIBIMA"):
                    if po_cust_col and not df_sibima_internal[po_cust_col].dropna().empty:
                        sibima_transaksi = df_sibima_internal[po_cust_col].nunique()
                    else:
                        sibima_transaksi = len(df_sibima_internal)
                        
                    sibima_nominal_exc = df_sibima_internal['PRICE_CLEAN'].sum()
                    sibima_nominal_inc = sibima_nominal_exc * 1.11
                    sibima_item = df_sibima_internal['QTY_CLEAN'].sum()
                    
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric("Total Transaksi SIBIMA", sibima_transaksi)
                    sc2.metric("Total Nilai SIBIMA (Exc PPN)", f"Rp {sibima_nominal_exc:,.0f}".replace(',', '.'))
                    sc3.metric("Total QTY SIBIMA", f"{sibima_item:,.0f}")
                    
                    st.dataframe(df_sibima_internal, use_container_width=True, height=250)

            st.divider()
            
            st.write("#### 🍩 Proporsi Transaksi per Status & 🏢 Proporsi RFQ per Kategori Sales")
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                if 'STATUS' in df_order_filtered.columns:
                    status_counts = df_order_filtered['STATUS'].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Jumlah']
                    donut_chart = alt.Chart(status_counts).mark_arc(innerRadius=50).encode(theta=alt.Theta(field="Jumlah", type="quantitative"), color=alt.Color(field="Status", type="nominal"), tooltip=['Status', 'Jumlah']).properties(height=300)
                    st.altair_chart(donut_chart, use_container_width=True)
            with v_col2:
                kat_rfq_col = next((c for c in df_rfq.columns if 'KATEGORI' in str(c).upper()), None)
                if kat_rfq_col:
                    kat_counts = df_rfq[kat_rfq_col].value_counts().reset_index()
                    kat_counts.columns = ['Kategori', 'Jumlah RFQ']
                    donut_kat = alt.Chart(kat_counts).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta(field="Jumlah RFQ", type="quantitative"),
                        color=alt.Color(field="Kategori", type="nominal"),
                        tooltip=['Kategori', 'Jumlah RFQ']
                    ).properties(height=300)
                    st.altair_chart(donut_kat, use_container_width=True)

    # --- TAB 2: MONITORING RFQ (PENDING & KENDALA) ---
    with tab_i2:
        st.write("### 🔍 Monitoring RFQ: Belum Dikerjakan & Kendala")
        st.markdown("Menganalisis data dari `MASTER RFQ` untuk melacak RFQ yang statusnya belum selesai, tertunda, atau memiliki kendala operasional.")

        if not df_rfq.empty:
            stat_rfq_col = next((c for c in df_rfq.columns if any(k in str(c).upper() for k in ['STATUS', 'PROGRESS', 'KET', 'KETERANGAN'])), None)

            def is_pending_rfq(row):
                if stat_rfq_col and pd.notna(row[stat_rfq_col]):
                    val = str(row[stat_rfq_col]).upper()
                    if any(k in val for k in ['SELESAI', 'DONE', 'CLOSED', 'PO']):
                        return False
                return True

            df_rfq_pending = df_rfq[df_rfq.apply(is_pending_rfq, axis=1)].copy() if stat_rfq_col else df_rfq.copy()

            m_rfq1, m_rfq2 = st.columns(2)
            m_rfq1.metric("Total RFQ Masuk", len(df_rfq))
            m_rfq2.metric("RFQ Belum Selesai / Pending", len(df_rfq_pending))

            st.divider()
            st.write("#### 📋 Daftar RFQ Belum Selesai & Kendala")
            st.dataframe(df_rfq_pending, use_container_width=True, height=400)

            csv_rfq_pending = df_rfq_pending.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Laporan RFQ Pending (CSV)",
                data=csv_rfq_pending,
                file_name="RFQ_Pending_Kendala.csv",
                mime="text/csv"
            )
        else:
            st.warning("Data Master RFQ kosong.")

    # --- TAB 3: KONVERSI SQ KE PO ---
    with tab_i3:
        st.write("### 📈 Analisis Konversi SQ (Quotation) ke PO (Order)")
        st.markdown("Menggabungkan data dari `MASTER RFQ` dan `MASTER ORDER` untuk melihat persentase SQ yang berhasil tembus menjadi Purchase Order (PO).")

        if not df_rfq.empty and not df_order.empty:
            total_rfq_count = len(df_rfq)
            total_order_count = len(df_order)
            conversion_rate = (total_order_count / total_rfq_count * 100) if total_rfq_count > 0 else 0

            kc1, kc2, kc3 = st.columns(3)
            kc1.metric("Total SQ / RFQ Diajukan", total_rfq_count)
            kc2.metric("Total PO / Order Berhasil", total_order_count)
            kc3.metric("Conversion Rate (%)", f"{conversion_rate:.2f}%")

            st.divider()

            st.write("#### 📊 Grafik Ringkasan Konversi SQ ke PO")
            conv_summary = pd.DataFrame({
                'Tahapan': ['Total SQ / RFQ', 'Berhasil Jadi PO'],
                'Jumlah': [total_rfq_count, total_order_count]
            })
            chart_conv = alt.Chart(conv_summary).mark_bar(color='#2ca02c').encode(
                x=alt.X('Tahapan:N', sort=None),
                y=alt.Y('Jumlah:Q', title='Jumlah Dokumen'),
                tooltip=['Tahapan', 'Jumlah']
            ).properties(height=300)
            st.altair_chart(chart_conv, use_container_width=True)

            st.write("#### 📑 Detail Laporan Master Order")
            st.dataframe(df_order.head(100), use_container_width=True, height=300)
        else:
            st.warning("Data RFQ atau Order tidak lengkap untuk melakukan analisis konversi.")

    # --- TAB 4: ANALISIS VENDOR ---
    with tab_i4:
        st.write("### 📋 Analisis Performa & Transaksi Vendor")
        st.markdown("Menampilkan rincian volume transaksi dan sebaran vendor yang menangani pesanan di interco.")

        if not df_order.empty:
            vend_c = next((c for c in df_order.columns if 'VENDOR' in str(c).upper()), None)
            if vend_c:
                vendor_counts = df_order[vend_c].value_counts().reset_index()
                vendor_counts.columns = ['Vendor', 'Total Transaksi']

                st.metric("Total Vendor Aktif", len(vendor_counts))
                st.divider()

                bar_chart_full = alt.Chart(vendor_counts).mark_bar().encode(
                    x=alt.X('Total Transaksi:Q', title='Jumlah Transaksi'),
                    y=alt.Y('Vendor:N', sort='-x', title='Nama Vendor'),
                    color=alt.Color('Vendor:N', legend=None),
                    tooltip=['Vendor', 'Total Transaksi']
                ).properties(height=500)
                st.altair_chart(bar_chart_full, use_container_width=True)

                st.write("#### 📑 Tabel Rekapitulasi Transaksi per Vendor")
                st.dataframe(vendor_counts, use_container_width=True, height=350)
            else:
                st.warning("Kolom Vendor tidak ditemukan pada Master Order.")
        else:
            st.warning("Data Master Order kosong.")

    # --- TAB 5: OUTSTANDING SUPPLY VENDOR (INTERCO) ---
    with tab_i5:
        st.write("### 🚚 Monitoring Outstanding Supply Vendor (Interco)")
        st.markdown("Menampilkan daftar transaksi order interco yang barangnya atau pengirimannya masih *outstanding* (belum diterima).")

        if not df_order.empty:
            status_col = next((c for c in df_order.columns if 'STATUS' in str(c).upper()), None)
            if status_col:
                df_interco_out = df_order[
                    (~df_order[status_col].astype(str).str.upper().isin(['SUDAH DITERIMA', 'CANCEL']))
                ].copy()
            else:
                df_interco_out = df_order.copy()

            vend_col_in = next((c for c in df_interco_out.columns if 'VENDOR' in str(c).upper()), None)
            
            list_v_in = ["Semua Vendor"] + sorted([str(x) for x in df_interco_out[vend_col_in].dropna().unique()]) if vend_col_in else ["Semua Vendor"]
            pilih_v_in = st.selectbox("🔍 Filter Berdasarkan Vendor Interco:", list_v_in)

            if pilih_v_in != "Semua Vendor" and vend_col_in:
                df_interco_out = df_interco_out[df_interco_out[vend_col_in].astype(str) == pilih_v_in]

            st.metric("Total Transaksi Interco Outstanding", len(df_interco_out))
            st.dataframe(df_interco_out, use_container_width=True, height=450)

            csv_in_out = df_interco_out.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Laporan Outstanding Interco (CSV)",
                data=csv_in_out,
                file_name="Outstanding_Interco_Vendor.csv",
                mime="text/csv"
            )
        else:
            st.warning("Data Master Order kosong.")

# ==========================================
# MODE 2: PROJECT YTP (Tahap 2 & 3) [DI-HOLD SEMENTARA]
# ==========================================
elif mode == "🏗️ Project (YTP Tahap 2 & 3)":
    st.title("🏗️ DASHBOARD ANALITIK PROJECT (YTP)")
    st.info("Mode Project YTP sedang di-hold sementara sesuai permintaan. Silakan gunakan menu Central Procurement & Interco.")
