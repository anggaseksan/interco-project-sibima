import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

st.set_page_config(page_title="SIBIMA Performance Dashboard", layout="wide", page_icon="📈")

# Tambahan CSS Global untuk Responsivitas & Mencegah Konten Terpotong di Berbagai Ukuran Layar
st.markdown("""
    <style>
        .main .block-container {
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100%;
        }
        [data-testid="stMetricValue"] {
            font-size: clamp(1.2rem, 2.5vw, 1.8rem) !important;
            word-break: break-word;
        }
        [data-testid="stDataFrame"] {
            width: 100% !important;
            overflow-x: auto;
        }
        .stMultiSelect, .stSelectbox, .stDateInput {
            width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)

BULAN_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def _fmt_tgl_indo(val):
    if val is None or isinstance(val, (list, tuple, dict, set, np.ndarray, pd.Series, pd.Index)):
        return val
    try:
        if pd.isna(val):
            return val
    except (ValueError, TypeError):
        return val
    if isinstance(val, str) and any(b in val for b in BULAN_ID.values()):
        return val.strip()
    dt = pd.to_datetime(val, errors='coerce')
    if pd.isna(dt):
        return val
    return f"{dt.day} {BULAN_ID[dt.month]} {dt.year}"

def format_date_columns(df):
    if df is None or df.empty:
        return df
    df_out = df.copy()
    for col in df_out.columns:
        col_u = str(col).upper()
        if any(k in col_u for k in ['TGL', 'TANGGAL', 'DATE']):
            target = df_out[col]
            if isinstance(target, pd.Series):
                df_out[col] = target.astype(object).apply(_fmt_tgl_indo)
    return df_out

def _has_value(series):
    if series is None:
        return pd.Series(False, index=[])
    s_str = series.fillna('').astype(str).str.strip().str.upper()
    return ~s_str.isin(['', 'NAN', 'NAT', 'NONE', '-'])

def is_internal_row(row, kat_col=None, cust_col=None):
    kat = str(row[kat_col]).upper().strip() if (kat_col and pd.notna(row.get(kat_col))) else ""
    cust = str(row[cust_col]).upper().strip() if (cust_col and pd.notna(row.get(cust_col))) else ""
    if 'SIBIMATECH' in kat or 'SIBIMA TECH' in kat or 'SIBIMATECH' in cust or 'SIBIMA TECH' in cust:
        return False
    return (
        kat in ['SIBIMA', 'GA SIBIMA', 'AMIN', 'GA AMIIN', 'GA AMIN']
        or 'SIBIMA BERKARYA MANDIRI' in kat
        or 'SIBIMA BERKARYA MANDIRI' in cust
        or 'AGRO MINA INTI NUSANTARA' in kat
        or 'AGRO MINA INTI NUSANTARA' in cust
        or 'AGRO MINA' in kat
        or 'AGRO MINA' in cust
    )

# Fungsi load data dengan cache dinamis
@st.cache_data(ttl=10)
def load_data(url, header_row=0):
    try:
        df = pd.read_csv(url, header=header_row)
        df.columns = df.columns.str.replace('\n', ' ').str.strip()
        return df
    except Exception:
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
            tgl_rfq_col = next((c for c in df_rfq.columns if 'TANGGAL RFQ' in str(c).upper() or 'TGL RFQ' in str(c).upper()), None)
            if tgl_rfq_col:
                df_rfq[tgl_rfq_col] = pd.to_datetime(df_rfq[tgl_rfq_col], errors='coerce')
                min_date = df_rfq[tgl_rfq_col].min().date() if not df_rfq[tgl_rfq_col].isnull().all() else datetime.today().date()
                max_date = df_rfq[tgl_rfq_col].max().date() if not df_rfq[tgl_rfq_col].isnull().all() else datetime.today().date()
            else:
                min_date = max_date = datetime.today().date()

            kat_col_order = next((c for c in df_order.columns if 'KATEGORI' in str(c).upper()), None)
            cust_col_order = next((c for c in df_order.columns if 'CUSTOMER' in str(c).upper() and 'PIC' not in str(c).upper() and 'NO' not in str(c).upper() and 'TGL' not in str(c).upper()), None)
            status_col = next((c for c in df_order.columns if 'STATUS' in str(c).upper()), None)

            list_cust_options = sorted(list(df_order[kat_col_order].dropna().unique())) if kat_col_order and not df_order[kat_col_order].dropna().empty else []
            list_status_options = sorted(list(df_order[status_col].dropna().unique())) if status_col and not df_order[status_col].dropna().empty else []

            st.write("### Filter Dashboard Interco")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1: date_range = st.date_input("Select Date Range 📅", [min_date, max_date], key="i_date")
            with f_col2: pilih_status = st.selectbox("Cari Status 🔍", ["Semua"] + list_status_options, key="i_stat")
            with f_col3: pilih_cust = st.multiselect("Pilih Customer (Kategori) 👤", list_cust_options, key="i_cust")
            with f_col4: pilih_no = st.text_input("Cari Nomor Transaksi / Item 🔍", key="i_no")

            df_order_filtered = df_order.copy()
            if pilih_status != "Semua" and status_col:
                df_order_filtered = df_order_filtered[df_order_filtered[status_col] == pilih_status]
            if pilih_cust and kat_col_order:
                df_order_filtered = df_order_filtered[df_order_filtered[kat_col_order].isin(pilih_cust)]
            if pilih_no:
                df_order_filtered = df_order_filtered[df_order_filtered.astype(str).apply(lambda x: x.str.contains(pilih_no, case=False, na=False)).any(axis=1)]

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

            qty_col = next((c for c in df_order_filtered.columns if str(c).upper().strip() == 'QTY' or 'QTY' in str(c).upper()), None)
            price_col = next((c for c in df_order_filtered.columns if 'TOTAL HARGA JUAL' in str(c).upper()), None) or next((c for c in df_order_filtered.columns if 'HARGA JUAL' in str(c).upper()), None)
            hpp_col = next((c for c in df_order_filtered.columns if 'TOTAL HARGA BELI' in str(c).upper()), None) or next((c for c in df_order_filtered.columns if 'HARGA BELI' in str(c).upper()), None)
            po_cust_col = next((c for c in df_order_filtered.columns if 'NO PO CUSTOMER' in str(c).upper() or 'PO CUSTOMER' in str(c).upper()), None)
            sq_order_col = next((c for c in df_order_filtered.columns if 'NO SQ' in str(c).upper()), None)

            df_order_filtered['QTY_CLEAN'] = pd.to_numeric(df_order_filtered[qty_col], errors='coerce').fillna(0) if qty_col else 1.0
            df_order_filtered['PRICE_CLEAN'] = df_order_filtered[price_col].apply(clean_price) if price_col else 0.0
            df_order_filtered['HPP_CLEAN'] = df_order_filtered[hpp_col].apply(clean_price) if hpp_col else 0.0

            mask_internal = df_order_filtered.apply(lambda r: is_internal_row(r, kat_col_order, cust_col_order), axis=1)
            df_internal_all = df_order_filtered[mask_internal].copy()

            if status_col:
                mask_not_cancel_pending = ~df_order_filtered[status_col].astype(str).str.upper().str.strip().isin(['CANCEL', 'PENDING'])
            else:
                mask_not_cancel_pending = pd.Series(True, index=df_order_filtered.index)

            df_komersial = df_order_filtered[mask_not_cancel_pending & (~mask_internal)].copy()

            # =========================================================
            # BAGIAN 1: KOMERSIAL EKSTERNAL
            # =========================================================
            st.divider()
            st.write("### 📊 Ringkasan & Detail Transaksi Komersial Eksternal")
            st.caption("Alur pantauan: Permintaan (RFQ) → Sudah SQ → Jadi PO User / Order → Proses → Sudah Diterima.")

            kat_rfq_c = next((c for c in df_rfq.columns if 'KATEGORI' in str(c).upper()), None)
            cust_rfq_c = next((c for c in df_rfq.columns if 'CUSTOMER' in str(c).upper() and 'PIC' not in str(c).upper()), None)
            sq_rfq_c = next((c for c in df_rfq.columns if 'NO SQ' in str(c).upper()), None)

            if not df_rfq.empty:
                mask_rfq_int = df_rfq.apply(lambda r: is_internal_row(r, kat_rfq_c, cust_rfq_c), axis=1)
                df_rfq_ext = df_rfq[~mask_rfq_int].copy()
                if pilih_cust and kat_rfq_c:
                    df_rfq_ext = df_rfq_ext[df_rfq_ext[kat_rfq_c].isin(pilih_cust)]
            else:
                df_rfq_ext = pd.DataFrame()

            total_permintaan_rfq = len(df_rfq_ext)
            sudah_sq_rfq = int(_has_value(df_rfq_ext[sq_rfq_c]).sum()) if (not df_rfq_ext.empty and sq_rfq_c) else 0

            jadi_po_user = int(_has_value(df_komersial[po_cust_col]).sum()) if (not df_komersial.empty and po_cust_col) else len(df_komersial)
            if status_col and not df_komersial.empty:
                m_status_terima = df_komersial[status_col].astype(str).str.upper().str.strip() == 'SUDAH DITERIMA'
                m_tgl_terima = _has_value(df_komersial['TGL CUST TERIMA']) if 'TGL CUST TERIMA' in df_komersial.columns else pd.Series(False, index=df_komersial.index)
                m_tgl_grn = _has_value(df_komersial['TGL GRN']) if 'TGL GRN' in df_komersial.columns else pd.Series(False, index=df_komersial.index)
                sudah_diterima_ext = int((m_status_terima | m_tgl_terima | m_tgl_grn).sum())
            else:
                sudah_diterima_ext = 0

            total_revenue_exc = df_komersial['PRICE_CLEAN'].sum()
            total_revenue_inc = total_revenue_exc * 1.11
            total_hpp_exc = df_komersial['HPP_CLEAN'].sum()
            total_transaksi_unik = df_komersial[po_cust_col].nunique() if (po_cust_col and not df_komersial[po_cust_col].dropna().empty) else len(df_komersial)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Permintaan RFQ Eksternal", total_permintaan_rfq)
            k2.metric("Sudah Terbit SQ (RFQ)", sudah_sq_rfq)
            k3.metric("Jadi PO User (Order Aktif)", jadi_po_user)
            k4.metric("Sudah Diterima (Order)", sudah_diterima_ext)

            k5, k6, k7, k8 = st.columns(4)
            k5.metric("Total Transaksi Unik (PO Cust)", total_transaksi_unik)
            k6.metric("Penjualan (Exclude PPN)", f"Rp {total_revenue_exc:,.0f}".replace(',', '.'))
            k7.metric("Penjualan (Include PPN)", f"Rp {total_revenue_inc:,.0f}".replace(',', '.'))
            k8.metric("HPP (Exclude PPN)", f"Rp {total_hpp_exc:,.0f}".replace(',', '.'))

            st.write("#### 📑 Tabel Detail Item / Transaksi Komersial Eksternal")
            ext_priority_cols = [c for c in [
                kat_col_order, cust_col_order, po_cust_col, 'TGL PO CUSTOMER',
                sq_order_col, 'TGL SQ', 'NO SO', 'NO PO', 'ITEM', qty_col,
                price_col, hpp_col, status_col, 'TGL ESTIMASI SAMPAI', 'TGL GRN', 'TGL DO', 'TGL CUST TERIMA'
            ] if c and c in df_komersial.columns]
            ext_rest_cols = [c for c in df_komersial.columns if c not in ext_priority_cols and not str(c).endswith('_CLEAN')]
            df_komersial_view = df_komersial[ext_priority_cols + ext_rest_cols] if not df_komersial.empty else df_komersial
            st.dataframe(format_date_columns(df_komersial_view), use_container_width=True, height=340)

            # =========================================================
            # BAGIAN 2: TRANSAKSI INTERNAL (SIBIMA & AMIN)
            # =========================================================
            st.divider()
            st.write("### 🏢 Ringkasan & Detail Transaksi Internal (SIBIMA & AMIN)")
            st.caption("Pantauan khusus internal: sudah diproses belum, sudah diajukan pembayarannya belum (BPV), dan apakah sudah sampai.")

            if not df_internal_all.empty:
                pr_col = next((c for c in df_internal_all.columns if 'NO PR' in str(c).upper()), None)
                po_col = next((c for c in df_internal_all.columns if str(c).upper().strip() == 'NO PO' or ('NO PO' in str(c).upper() and 'CUSTOMER' not in str(c).upper())), None)
                bpv_col = next((c for c in df_internal_all.columns if 'BPV' in str(c).upper()), None)
                grn_col = next((c for c in df_internal_all.columns if 'GRN' in str(c).upper()), None)
                do_col = next((c for c in df_internal_all.columns if str(c).upper().strip() == 'NO DO' or 'TGL DO' in str(c).upper()), None)
                terima_col = next((c for c in df_internal_all.columns if 'CUST TERIMA' in str(c).upper() or 'TERIMA' in str(c).upper()), None)

                has_pr = _has_value(df_internal_all[pr_col]) if pr_col else pd.Series(False, index=df_internal_all.index)
                has_po = _has_value(df_internal_all[po_col]) if po_col else pd.Series(False, index=df_internal_all.index)
                has_bpv = _has_value(df_internal_all[bpv_col]) if bpv_col else pd.Series(False, index=df_internal_all.index)
                has_sampai = (
                    (df_internal_all[status_col].astype(str).str.upper().str.strip() == 'SUDAH DITERIMA' if status_col else pd.Series(False, index=df_internal_all.index))
                    | (_has_value(df_internal_all[terima_col]) if terima_col else pd.Series(False, index=df_internal_all.index))
                    | (_has_value(df_internal_all[grn_col]) if grn_col else pd.Series(False, index=df_internal_all.index))
                )
                sudah_diproses = has_pr | has_po | has_bpv | has_sampai

                ic1, ic2, ic3, ic4 = st.columns(4)
                ic1.metric("Total Item Internal", len(df_internal_all))
                ic2.metric("Sudah Diproses", int(sudah_diproses.sum()))
                ic3.metric("Pembayaran Diajukan (BPV)", int(has_bpv.sum()))
                ic4.metric("Sudah Sampai", int(has_sampai.sum()))

                df_internal_disp = df_internal_all.copy()
                df_internal_disp.insert(0, "Status Sampai", has_sampai.map({True: "Sudah Sampai", False: "Belum Sampai"}))
                df_internal_disp.insert(0, "Pembayaran (BPV)", has_bpv.map({True: "Sudah Diajukan", False: "Belum Diajukan"}))
                df_internal_disp.insert(0, "Status Proses", sudah_diproses.map({True: "Sudah Diproses", False: "Belum Diproses"}))

                int_priority = [c for c in [
                    "Status Proses", "Pembayaran (BPV)", "Status Sampai",
                    kat_col_order, cust_col_order, 'ITEM', qty_col, status_col,
                    pr_col, 'TGL PR', po_col, 'TGL PO', bpv_col, 'TGL BPV',
                    'TGL ESTIMASI SAMPAI', grn_col, 'TGL GRN', do_col, terima_col
                ] if c and c in df_internal_disp.columns]
                int_rest = [c for c in df_internal_disp.columns if c not in int_priority and not str(c).endswith('_CLEAN')]

                st.write("#### 📑 Tabel Detail Item / Transaksi Internal (SIBIMA & AMIN)")
                st.dataframe(format_date_columns(df_internal_disp[int_priority + int_rest]), use_container_width=True, height=340)
            else:
                st.info("Tidak ada data transaksi internal (SIBIMA & AMIN) pada filter saat ini.")

    # --- TAB 2: MONITORING RFQ (PENDING & KENDALA) ---
    with tab_i2:
        st.write("### 🔍 Monitoring RFQ: Belum Dikerjakan & Kendala")
        st.markdown("Menganalisis data dari `MASTER RFQ` untuk melacak RFQ yang statusnya belum selesai, tertunda, atau memiliki kendala operasional.")

        if not df_rfq.empty:
            stat_rfq_col = next((c for c in df_rfq.columns if 'STATUS' in str(c).upper()), None)
            kendala_col = next((c for c in df_rfq.columns if 'KENDALA' in str(c).upper()), None)

            def reorder_kendala_first(df_target):
                if kendala_col and kendala_col in df_target.columns:
                    other_cols = [col for col in df_target.columns if col != kendala_col]
                    status_idx = other_cols.index(stat_rfq_col) if (stat_rfq_col and stat_rfq_col in other_cols) else 1
                    new_cols_order = other_cols[:status_idx+1] + [kendala_col] + other_cols[status_idx+1:]
                    return df_target[new_cols_order]
                return df_target

            def is_pending_hold_followup(row):
                status_val = str(row[stat_rfq_col]).upper().strip() if (stat_rfq_col and pd.notna(row[stat_rfq_col])) else ""
                kendala_val = str(row[kendala_col]).upper().strip() if (kendala_col and pd.notna(row[kendala_col])) else ""
                if 'PENDING' in status_val and 'HOLD' in kendala_val and 'CLOSE' not in status_val:
                    return True
                return False

            def is_pending_rfq(row):
                if is_pending_hold_followup(row):
                    return False
                if stat_rfq_col and pd.notna(row[stat_rfq_col]):
                    val = str(row[stat_rfq_col]).upper().strip()
                    if any(k in val for k in ['COMPLETE', 'DONE', 'CLOSED', 'SELESAI', 'PO', 'CLOSE', 'CANCEL']):
                        return False
                return True

            df_rfq_pending = df_rfq[df_rfq.apply(is_pending_rfq, axis=1)].copy() if stat_rfq_col else df_rfq.copy()
            df_rfq_hold_followup = df_rfq[df_rfq.apply(is_pending_hold_followup, axis=1)].copy() if stat_rfq_col else pd.DataFrame(columns=df_rfq.columns)

            df_rfq_pending = reorder_kendala_first(df_rfq_pending)
            df_rfq_hold_followup = reorder_kendala_first(df_rfq_hold_followup)

            m_rfq1, m_rfq2, m_rfq3 = st.columns(3)
            m_rfq1.metric("Total RFQ Masuk", len(df_rfq))
            m_rfq2.metric("RFQ Belum Selesai / Pending", len(df_rfq_pending))
            m_rfq3.metric("RFQ Di-hold (Follow-up s/d Close)", len(df_rfq_hold_followup))

            st.divider()
            st.write("#### 📋 Daftar RFQ Belum Selesai & Kendala")
            st.dataframe(format_date_columns(df_rfq_pending), use_container_width=True, height=400)

            csv_rfq_pending = format_date_columns(df_rfq_pending).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Laporan RFQ Pending (CSV)",
                data=csv_rfq_pending,
                file_name="RFQ_Pending_Kendala.csv",
                mime="text/csv"
            )

            if not df_rfq_hold_followup.empty:
                st.divider()
                with st.expander("📌 Daftar RFQ Di-hold (Sementara Selesai — Perlu Follow-up sampai CLOSE)"):
                    st.dataframe(format_date_columns(df_rfq_hold_followup), use_container_width=True, height=300)
                    csv_rfq_hold = format_date_columns(df_rfq_hold_followup).to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Laporan RFQ Di-hold / Follow-up (CSV)",
                        data=csv_rfq_hold,
                        file_name="RFQ_Hold_FollowUp.csv",
                        mime="text/csv",
                        key="dl_rfq_hold"
                    )
        else:
            st.warning("Data Master RFQ kosong.")

    # --- TAB 3: KONVERSI SQ KE PO ---
    with tab_i3:
        st.write("### 📈 Analisis Konversi SQ (Quotation) ke PO (Order)")
        st.markdown("Mengecek setiap **NO SQ** yang ada di `MASTER RFQ` apakah sudah masuk ke `MASTER ORDER`.")

        sq_rfq_col = next((c for c in df_rfq.columns if 'NO SQ' in str(c).upper() or str(c).upper().strip() == 'SQ'), None)
        sq_order_col = next((c for c in df_order.columns if 'NO SQ' in str(c).upper() or str(c).upper().strip() == 'SQ'), None)

        if not df_rfq.empty and not df_order.empty and sq_rfq_col and sq_order_col:
            rfq_sq_series = df_rfq[sq_rfq_col].dropna().astype(str).str.strip()
            rfq_sq_series = rfq_sq_series[rfq_sq_series != '']

            order_sq_series = df_order[sq_order_col].dropna().astype(str).str.strip()
            order_sq_series = order_sq_series[order_sq_series != '']
            order_sq_set = set(order_sq_series.unique())

            unique_rfq_sq = sorted(list(rfq_sq_series.unique()))
            total_sq_rfq = len(unique_rfq_sq)
            matched_sq_list = [sq for sq in unique_rfq_sq if sq in order_sq_set]
            unmatched_sq_list = [sq for sq in unique_rfq_sq if sq not in order_sq_set]

            masuk_order_count = len(matched_sq_list)
            belum_masuk_count = len(unmatched_sq_list)
            conversion_rate = (masuk_order_count / total_sq_rfq * 100) if total_sq_rfq > 0 else 0

            kc1, kc2, kc3, kc4 = st.columns(4)
            kc1.metric("Total NO SQ Unik (Master RFQ)", total_sq_rfq)
            kc2.metric("SQ Masuk Master Order", masuk_order_count)
            kc3.metric("SQ Belum Masuk Order", belum_masuk_count)
            kc4.metric("Conversion Rate SQ -> Order", f"{conversion_rate:.2f}%")

            st.divider()

            kat_rfq_c = next((c for c in df_rfq.columns if 'KATEGORI' in str(c).upper()), None)
            cust_rfq_c = next((c for c in df_rfq.columns if 'CUSTOMER' in str(c).upper()), None)
            stat_rfq_c = next((c for c in df_rfq.columns if 'STATUS' in str(c).upper()), None)

            df_rfq_sq_valid = df_rfq[df_rfq[sq_rfq_col].notna()].copy()
            df_rfq_sq_valid['NO_SQ_CLEAN'] = df_rfq_sq_valid[sq_rfq_col].astype(str).str.strip()
            df_rfq_sq_valid = df_rfq_sq_valid[df_rfq_sq_valid['NO_SQ_CLEAN'] != '']

            sq_rows = []
            for sq_val in unique_rfq_sq:
                sub = df_rfq_sq_valid[df_rfq_sq_valid['NO_SQ_CLEAN'] == sq_val]
                is_in_order = sq_val in order_sq_set
                sq_rows.append({
                    "NO SQ": sq_val,
                    "Status Masuk Order": "Masuk Order" if is_in_order else "Belum Masuk Order",
                    "Jumlah Item RFQ": len(sub),
                    "Kategori": ", ".join(sorted(set(sub[kat_rfq_c].dropna().astype(str)))) if kat_rfq_c else "-",
                    "Customer": ", ".join(sorted(set(sub[cust_rfq_c].dropna().astype(str)))) if cust_rfq_c else "-",
                    "Status RFQ": ", ".join(sorted(set(sub[stat_rfq_c].dropna().astype(str)))) if stat_rfq_c else "-"
                })

            df_sq_track = pd.DataFrame(sq_rows)
            filter_sq_status = st.selectbox("🔍 Filter Status SQ pada Master Order:", ["Semua", "Masuk Order", "Belum Masuk Order"], key="sq_track_filter")
            df_sq_track_view = df_sq_track[df_sq_track["Status Masuk Order"] == filter_sq_status] if filter_sq_status != "Semua" else df_sq_track

            st.write("#### 📑 Daftar Pelacakan NO SQ dari Master RFQ ke Master Order")
            st.dataframe(df_sq_track_view, use_container_width=True, height=380)

            csv_sq_track = df_sq_track_view.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Laporan Tracking SQ ke Order (CSV)",
                data=csv_sq_track,
                file_name="Tracking_SQ_ke_Master_Order.csv",
                mime="text/csv"
            )
        else:
            st.warning("Data RFQ atau Order kosong, atau kolom NO SQ tidak ditemukan.")

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
                    (~df_order[status_col].astype(str).str.upper().str.strip().isin(['SUDAH DITERIMA', 'CANCEL']))
                ].copy()
            else:
                df_interco_out = df_order.copy()

            vend_col_in = next((c for c in df_interco_out.columns if 'VENDOR' in str(c).upper()), None)
            list_v_in = ["Semua Vendor"] + sorted([str(x) for x in df_interco_out[vend_col_in].dropna().unique()]) if vend_col_in else ["Semua Vendor"]
            pilih_v_in = st.selectbox("🔍 Filter Berdasarkan Vendor Interco:", list_v_in)

            if pilih_v_in != "Semua Vendor" and vend_col_in:
                df_interco_out = df_interco_out[df_interco_out[vend_col_in].astype(str) == pilih_v_in]

            st.metric("Total Transaksi Interco Outstanding", len(df_interco_out))
            st.dataframe(format_date_columns(df_interco_out), use_container_width=True, height=450)

            csv_in_out = format_date_columns(df_interco_out).to_csv(index=False).encode('utf-8')
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
