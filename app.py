import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

st.set_page_config(page_title="SIBIMA Performance Dashboard", layout="wide", page_icon="📈")

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
    st.title("SIBIMA Performance Dashboard - PROCUREMENT")
    st.caption("Data source: Live Sync Google Sheets. Rekonstruksi dari RFQ & MASTER ORDER.")

    URL_RFQ = "https://docs.google.com/spreadsheets/d/18isSUeBYGiM2xuhV8QsXP57_AOotJ07vu1dvd5i62GI/export?format=csv&gid=1100229590"
    URL_ORDER = "https://docs.google.com/spreadsheets/d/18isSUeBYGiM2xuhV8QsXP57_AOotJ07vu1dvd5i62GI/export?format=csv&gid=467075902"

    df_rfq = load_data(URL_RFQ, header_row=1)
    df_order = load_data(URL_ORDER, header_row=0)

    if not df_rfq.empty and not df_order.empty:
        df_rfq['TANGGAL RFQ'] = pd.to_datetime(df_rfq['TANGGAL RFQ'], errors='coerce')
        min_date = df_rfq['TANGGAL RFQ'].min().date() if not df_rfq['TANGGAL RFQ'].isnull().all() else datetime.today().date()
        max_date = df_rfq['TANGGAL RFQ'].max().date() if not df_rfq['TANGGAL RFQ'].isnull().all() else datetime.today().date()
        
        st.write("### Filter Dashboard")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1: date_range = st.date_input("Select Date Range 📅", [min_date, max_date])
        with f_col2: pilih_status = st.selectbox("Cari Status 🔍", ["Semua"] + list(df_order['STATUS'].dropna().unique()))
        with f_col3: pilih_cust = st.selectbox("Pilih Customer 👤", ["Semua"] + list(df_order['CUSTOMER'].dropna().unique()))
        with f_col4: pilih_no = st.text_input("Cari Nomor Transaksi (SO/PO) 🔍")

        df_order_filtered = df_order.copy()
        if pilih_status != "Semua": df_order_filtered = df_order_filtered[df_order_filtered['STATUS'] == pilih_status]
        if pilih_cust != "Semua": df_order_filtered = df_order_filtered[df_order_filtered['CUSTOMER'] == pilih_cust]
        if pilih_no: df_order_filtered = df_order_filtered[df_order_filtered.astype(str).apply(lambda x: x.str.contains(pilih_no, case=False, na=False)).any(axis=1)]

        price_col = next((c for c in df_order_filtered.columns if 'TOTAL HARGA JUAL' in str(c).upper() or 'HARGA JUAL' in str(c).upper()), None)
        if price_col:
            def clean_price(val):
                if pd.isna(val): return 0.0
                s = str(val).replace('Rp', '').replace('idr', '').strip()
                if ',' in s and '.' in s:
                    if s.find('.') < s.find(','):
                        s = s.replace('.', '').replace(',', '.')
                    else:
                        s = s.replace(',', '')
                elif ',' in s:
                    if len(s.split(',')[-1]) == 3:
                        s = s.replace(',', '')
                    else:
                        s = s.replace(',', '.')
                elif s.count('.') > 1:
                    s = s.replace('.', '', s.count('.') - 1)
                try:
                    return float(s)
                except:
                    return 0.0

            df_order_filtered['PRICE_CLEAN'] = df_order_filtered[price_col].apply(clean_price)
        else:
            df_order_filtered['PRICE_CLEAN'] = 0.0

        st.divider()
        st.write("### 📊 Detail Transaksi")
        total_revenue = df_order_filtered['PRICE_CLEAN'].sum()
        total_transaksi = len(df_order_filtered)
        total_item = pd.to_numeric(df_order_filtered['QTY'], errors='coerce').sum() if 'QTY' in df_order_filtered.columns else 0
        
        outstanding_df = df_order_filtered[df_order_filtered['STATUS'].astype(str).str.upper() != 'SUDAH DITERIMA']
        balance_outstanding = outstanding_df['PRICE_CLEAN'].sum()
        top_kategori = df_order_filtered['KATEGORI'].mode()[0] if 'KATEGORI' in df_order_filtered.columns and not df_order_filtered['KATEGORI'].empty else "Tidak Ada"

        # Membagi metrik menjadi 2 baris agar angka nominalnya tidak terpotong (luas area lebih lega)
        r1_c1, r1_c2, r1_c3 = st.columns(3)
        r1_c1.metric("Total Order Nominal", f"Rp {total_revenue:,.0f}".replace(',', '.'))
        r1_c2.metric("Outstanding Balance", f"Rp {balance_outstanding:,.0f}".replace(',', '.'))
        r1_c3.metric("Total Transaksi", total_transaksi)

        r2_c1, r2_c2 = st.columns(2)
        r2_c1.metric("Total Item QTY", f"{total_item:,.0f}")
        r2_c2.metric("Kategori Terbanyak", top_kategori)
        
        st.divider()
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            st.write("#### 🍩 Proporsi Transaksi per Status")
            if 'STATUS' in df_order_filtered.columns:
                status_counts = df_order_filtered['STATUS'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Jumlah']
                donut_chart = alt.Chart(status_counts).mark_arc(innerRadius=50).encode(theta=alt.Theta(field="Jumlah", type="quantitative"), color=alt.Color(field="Status", type="nominal"), tooltip=['Status', 'Jumlah']).properties(height=300)
                st.altair_chart(donut_chart, use_container_width=True)
        with v_col2:
            st.write("#### 👤 Analisis Vendor per Transaksi")
            vend_c = next((c for c in df_order_filtered.columns if 'VENDOR' in str(c).upper()), None)
            if vend_c:
                vendor_counts = df_order_filtered[vend_c].value_counts().head(10).reset_index()
                vendor_counts.columns = ['Vendor', 'Total Transaksi']
                bar_chart = alt.Chart(vendor_counts).mark_bar().encode(x=alt.X('Total Transaksi:Q', title='Jumlah Transaksi'), y=alt.Y('Vendor:N', sort='-x', title='Nama Vendor'), color=alt.Color('Vendor:N', legend=None), tooltip=['Vendor', 'Total Transaksi']).properties(height=300)
                st.altair_chart(bar_chart, use_container_width=True)

# ==========================================
# MODE 2: PROJECT YTP (Tahap 2 & 3)
# ==========================================
elif mode == "🏗️ Project (YTP Tahap 2 & 3)":
    st.title("🏗️ DASHBOARD ANALITIK PROJECT (YTP)")
    st.caption("Pusat monitoring Logistik Kapal, Prediksi Pengiriman, Kesiapan Material, dan Deteksi Kesiapan Lahan.")

    URL_YTP2 = "https://docs.google.com/spreadsheets/d/1j6oUr9MaYNxXnCSxskoNqi3g_lG2Ei5x19my0JdFuiU/export?format=csv&gid=2045075266"
    URL_PREFAB = "https://docs.google.com/spreadsheets/d/1efW0JhB1dHD3qUy-IdWOB0eT77iXDYg-ZYMyl27zSEg/export?format=csv&gid=1830474678"
    URL_BARAK  = "https://docs.google.com/spreadsheets/d/1efW0JhB1dHD3qUy-IdWOB0eT77iXDYg-ZYMyl27zSEg/export?format=csv&gid=148820439"
    URL_MATLOC_NEW = "https://docs.google.com/spreadsheets/d/1j6oUr9MaYNxXnCSxskoNqi3g_lG2Ei5x19my0JdFuiU/export?format=csv&gid=958755241"

    df_ytp2 = load_data(URL_YTP2, header_row=1)
    df_prefab = load_data(URL_PREFAB, header_row=0)
    df_barak = load_data(URL_BARAK, header_row=3)
    df_matloc = load_data(URL_MATLOC_NEW, header_row=4)

    tab_p1, tab_p2, tab_p3, tab_p4, tab_p5 = st.tabs([
        "💡 Insight & KPI Logistik",
        "📦 Fulfillment Material Lokal", 
        "📋 Monitoring Vendor",
        "🚢 Master Data Prefab", 
        "🧱 Progress Lahan & Data Lain"
    ])

    with tab_p1:
        st.write("### 📊 Ringkasan Project YTP")
        total_ytp = len(df_prefab['YTP'].unique()) if 'YTP' in df_prefab.columns else 0
        total_prefab = len(df_prefab)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total YTP (Batalyon)", total_ytp)
        c2.metric("Total Transaksi Prefab", total_prefab)
        
        if 'TGL PREFAB SAMPAI DI SITE' in df_prefab.columns and 'TGL PONDASI SELESAI' in df_prefab.columns:
            df_prefab['TGL_SAMPAI_DT'] = pd.to_datetime(df_prefab['TGL PREFAB SAMPAI DI SITE'], errors='coerce')
            df_prefab['TGL_PONDASI_DT'] = pd.to_datetime(df_prefab['TGL PONDASI SELESAI'], errors='coerce')
            clash_count = len(df_prefab[(df_prefab['TGL_SAMPAI_DT'] < df_prefab['TGL_PONDASI_DT'])])
            c3.metric("🚨 Potensi Bentrok Lahan", clash_count)
            c4.metric("✅ Jadwal On-Track", total_prefab - clash_count)

        st.divider()
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.write("#### 🚢 Volume Pengiriman per Provinsi")
            if 'PROVINSI' in df_prefab.columns:
                prov_count = df_prefab['PROVINSI'].value_counts().reset_index()
                prov_count.columns = ['Provinsi', 'Jumlah YTP']
                bar_prov = alt.Chart(prov_count).mark_bar(color='#1f77b4').encode(x=alt.X('Jumlah YTP:Q'), y=alt.Y('Provinsi:N', sort='-x'), tooltip=['Provinsi', 'Jumlah YTP']).properties(height=300)
                st.altair_chart(bar_prov, use_container_width=True)
        with col_c2:
            st.write("#### ⏳ Prediksi Upcoming Supply (ETA Terdekat)")
            if 'TGL PREFAB SAMPAI DI SITE' in df_prefab.columns:
                df_upcoming = df_prefab.dropna(subset=['TGL_SAMPAI_DT']).sort_values('TGL_SAMPAI_DT').head(10)
                if not df_upcoming.empty:
                    bar_eta = alt.Chart(df_upcoming).mark_bar(color='#ff7f0e').encode(x=alt.X('TGL_SAMPAI_DT:T', title='Tanggal Tiba di Site'), y=alt.Y('YTP:N', sort='x', title='Nama YTP (Batalyon)'), color=alt.Color('PROVINSI:N', legend=alt.Legend(title="Provinsi")), tooltip=['YTP', 'PROVINSI', 'TGL PREFAB SAMPAI DI SITE']).properties(height=300)
                    st.altair_chart(bar_eta, use_container_width=True)

    with tab_p2:
        st.subheader("📦 Section 1: Fulfillment Material Lokal (YTP Tahap 3)")
        
        if not df_matloc.empty:
            if 'BATCH/GROUP' in df_matloc.columns:
                df_matloc['BATCH/GROUP CLEAN'] = pd.to_numeric(df_matloc['BATCH/GROUP'], errors='coerce').fillna(df_matloc['BATCH/GROUP']).astype(str).str.replace('.0', '', regex=False)
            else:
                df_matloc['BATCH/GROUP CLEAN'] = '-'

            def cek_status_mat(row):
                po_val = None
                for col in row.index:
                    if any(k in str(col).upper() for k in ['PO VENDOR', 'NO PO']) and pd.notna(row[col]) and str(row[col]).strip() != '' and str(row[col]).upper() != 'NONE':
                        po_val = row[col]
                        break
                do_val = None
                for col in row.index:
                    if 'DO' in str(col).upper() and pd.notna(row[col]) and str(row[col]).strip() != '' and str(row[col]).upper() != 'NONE':
                        do_val = row[col]
                        break
                
                if po_val and do_val: return "Selesai (DO Terbit)"
                elif po_val and not do_val: return "Diproses (Sudah PO)"
                else: return "Belum Dipesan"
            
            df_matloc['FULFILLMENT STATUS'] = df_matloc.apply(cek_status_mat, axis=1)
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                list_group = ["Semua Group"] + sorted(list(df_matloc['BATCH/GROUP CLEAN'].dropna().unique()))
                pilih_group = st.selectbox("🔍 Filter Group / Batch (Tahap 3):", list_group, key="f_group_3")
            with col_f2:
                wil_col = next((c for c in df_matloc.columns if 'WILAYAH' in str(c).upper()), None)
                list_wilayah = ["Semua Wilayah"] + sorted(list(df_matloc[wil_col].dropna().unique())) if wil_col else ["Semua Wilayah"]
                pilih_wilayah = st.selectbox("🔍 Filter Wilayah (Tahap 3):", list_wilayah, key="f_wil_3")
            with col_f3:
                mat_col = next((c for c in df_matloc.columns if 'MATERIAL' in str(c).upper()), None)
                list_mat = ["Semua Material"] + sorted(list(df_matloc[mat_col].dropna().unique())) if mat_col else ["Semua Material"]
                pilih_material = st.selectbox("🔍 Filter Jenis Material (Tahap 3):", list_mat, key="f_mat_3")

            df_mat_filtered = df_matloc.copy()
            if pilih_group != "Semua Group":
                df_mat_filtered = df_mat_filtered[df_mat_filtered['BATCH/GROUP CLEAN'] == pilih_group]
            if pilih_wilayah != "Semua Wilayah" and wil_col:
                df_mat_filtered = df_mat_filtered[df_mat_filtered[wil_col] == pilih_wilayah]
            if pilih_material != "Semua Material" and mat_col:
                df_mat_filtered = df_mat_filtered[df_mat_filtered[mat_col] == pilih_material]

            st.divider()
            v1, v2 = st.columns([1, 2])
            with v1:
                st.write("**Proporsi Status (Tahap 3)**")
                status_counts = df_mat_filtered['FULFILLMENT STATUS'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Jumlah Item']
                donut_mat = alt.Chart(status_counts).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta(field="Jumlah Item", type="quantitative"),
                    color=alt.Color(field="Status", type="nominal", scale=alt.Scale(domain=['Selesai (DO Terbit)', 'Diproses (Sudah PO)', 'Belum Dipesan'], range=['#2ca02c', '#ff7f0e', '#d62728'])),
                    tooltip=['Status', 'Jumlah Item']
                ).properties(height=300)
                st.altair_chart(donut_mat, use_container_width=True)
            
            with v2:
                st.write("**Detail Material Tahap 3**")
                st.dataframe(df_mat_filtered, use_container_width=True, height=300)

            st.write("#### 🚨 Belum Dipesan (Tahap 3)")
            df_belum = df_mat_filtered[df_mat_filtered['FULFILLMENT STATUS'] == 'Belum Dipesan']
            if not df_belum.empty:
                st.dataframe(df_belum, use_container_width=True, height=250)
            else:
                st.success("🎉 Semua material Tahap 3 sudah dipesan.")
        else:
            st.error("Data YTP Tahap 3 kosong.")

        st.markdown("---")

        # --- SECTION 2: YTP TAHAP 2 ---
        st.subheader("📦 Section 2: Analisis Operasional (YTP Tahap 2)")
        
        if not df_ytp2.empty:
            def cek_status_ytp2(row):
                po_val = None
                for col in row.index:
                    if any(k in str(col).upper() for k in ['PO VENDOR', 'NO PO']) and pd.notna(row[col]) and str(row[col]).strip() != '' and str(row[col]).upper() != 'NONE':
                        po_val = row[col]
                        break
                do_val = None
                for col in row.index:
                    if 'DO' in str(col).upper() and pd.notna(row[col]) and str(row[col]).strip() != '' and str(row[col]).upper() != 'NONE':
                        do_val = row[col]
                        break
                
                if po_val and do_val: return "Selesai (DO Terbit)"
                elif po_val and not do_val: return "Diproses (Sudah PO)"
                else: return "Belum Dipesan"

            df_ytp2['FULFILLMENT STATUS'] = df_ytp2.apply(cek_status_ytp2, axis=1)

            col_2f1, col_2f2 = st.columns(2)
            with col_2f1:
                cust_col_2 = next((c for c in df_ytp2.columns if 'CUSTOMER' in str(c).upper()), None)
                list_cust_2 = ["Semua Customer"] + sorted(list(df_ytp2[cust_col_2].dropna().unique())) if cust_col_2 else ["Semua Customer"]
                pilih_cust_2 = st.selectbox("🔍 Filter Customer (Tahap 2):", list_cust_2)
            with col_2f2:
                list_stat_2 = ["Semua Status"] + sorted(list(df_ytp2['FULFILLMENT STATUS'].dropna().unique()))
                pilih_stat_2 = st.selectbox("🔍 Filter Status (Tahap 2):", list_stat_2)

            df_ytp2_filtered = df_ytp2.copy()
            if pilih_cust_2 != "Semua Customer" and cust_col_2:
                df_ytp2_filtered = df_ytp2_filtered[df_ytp2_filtered[cust_col_2] == pilih_cust_2]
            if pilih_stat_2 != "Semua Status":
                df_ytp2_filtered = df_ytp2_filtered[df_ytp2_filtered['FULFILLMENT STATUS'] == pilih_stat_2]

            st.write("**Detail Data YTP Tahap 2**")
            st.dataframe(df_ytp2_filtered, use_container_width=True, height=350)
        else:
            st.info("Data YTP Tahap 2 kosong.")

    # ----------------------------------------
    # TAB 3: MONITORING VENDOR (OUTSTANDING SUPPLY)
    # ----------------------------------------
    with tab_p3:
        st.write("### 📋 Monitoring Outstanding Supply Vendor (YTP Tahap 2 & 3)")
        st.markdown("Menampilkan daftar seluruh barang dari Project YTP Tahap 2 dan 3 yang status pengirimannya dari vendor masih *outstanding* (belum diterima / belum selesai).")

        df_out_3 = pd.DataFrame()
        if not df_matloc.empty:
            df_out_3 = df_matloc[df_matloc.apply(lambda r: cek_status_mat(r) != "Selesai (DO Terbit)", axis=1)].copy()
            df_out_3['SUMBER PROJECT'] = 'YTP Tahap 3'

        df_out_2 = pd.DataFrame()
        if not df_ytp2.empty:
            df_out_2 = df_ytp2[df_ytp2.apply(lambda r: cek_status_ytp2(r) != "Selesai (DO Terbit)", axis=1)].copy()
            df_out_2['SUMBER PROJECT'] = 'YTP Tahap 2'

        df_combined_out = pd.concat([df_out_3, df_out_2], ignore_index=True)

        if not df_combined_out.empty:
            vend_col = next((c for c in df_combined_out.columns if 'VENDOR' in str(c).upper() and 'NAMA' in str(c).upper()), None)
            if not vend_col:
                vend_col = next((c for c in df_combined_out.columns if 'VENDOR' in str(c).upper()), None)

            list_vend = ["Semua Vendor"] + sorted([str(x) for x in df_combined_out[vend_col].dropna().unique()]) if vend_col else ["Semua Vendor"]
            pilih_vend_mon = st.selectbox("🔍 Filter Berdasarkan Nama Vendor:", list_vend)

            if pilih_vend_mon != "Semua Vendor" and vend_col:
                df_combined_out = df_combined_out[df_combined_out[vend_col].astype(str) == pilih_vend_mon]

            st.metric("Total Item Outstanding Supply", len(df_combined_out))
            st.dataframe(df_combined_out, use_container_width=True, height=450)

            csv_mon = df_combined_out.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Laporan Outstanding Vendor (CSV)",
                data=csv_mon,
                file_name="Outstanding_Supply_Vendor.csv",
                mime="text/csv"
            )
        else:
            st.success("🎉 Luar biasa! Seluruh supply dari vendor untuk YTP Tahap 2 & 3 sudah selesai (DO Terbit).")

    with tab_p4:
        st.write("### 🚢 Master Data Pengiriman Prefab (China -> Site)")
        st.dataframe(df_prefab, use_container_width=True, height=500)

    with tab_p5:
        st.write("### 🧱 Master Data Kesiapan Barak & YTP 2")
        st.write("**Progress Lapangan (Kontraktor Barak):**")
        st.dataframe(df_barak, use_container_width=True, height=500)
