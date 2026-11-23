import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

st.set_page_config(
    page_title="SIBIMA Purchasing & Procurement Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# ==========================================
# CUSTOM CSS: GAYA PURCHASING DASHBOARD MODERN
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f4f7fb;
            color: #1e293b;
        }
        .stApp {
            background-color: #f4f7fb;
        }
        .main .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.5rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100%;
        }
        /* Top Header Bar */
        .top-banner {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 18px 24px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }
        .banner-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .version-pill {
            background: #e0edff;
            color: #1d4ed8;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 999px;
        }
        .banner-sub {
            font-size: 0.82rem;
            color: #64748b;
            margin-top: 3px;
        }
        .sync-badge {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 0.78rem;
            padding: 6px 12px;
            border-radius: 10px;
            text-align: right;
        }
        /* Section Header */
        .sec-card-header {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 16px 20px;
            margin-top: 10px;
            margin-bottom: 14px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }
        .sec-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0f172a;
            margin: 0;
        }
        .sec-desc {
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 2px;
        }
        /* Custom KPI Card */
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            height: 100%;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
        }
        .kpi-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .kpi-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: #64748b;
        }
        .kpi-icon {
            width: 30px;
            height: 30px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.95rem;
        }
        .kpi-val {
            font-size: 1.45rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
            word-break: break-word;
        }
        .kpi-sub {
            font-size: 0.74rem;
            color: #94a3b8;
            margin-top: 5px;
        }
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #ffffff;
            padding: 6px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 0.85rem;
            color: #475569;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1d4ed8 !important;
            color: #ffffff !important;
        }
        /* Dataframe Container */
        [data-testid="stDataFrame"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 6px;
            width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)

def render_kpi_card(label, value, sublabel, icon, bg_icon="#eff6ff", color_icon="#2563eb"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-top">
            <span class="kpi-label">{label}</span>
            <span class="kpi-icon" style="background:{bg_icon}; color:{color_icon};">{icon}</span>
        </div>
        <div class="kpi-val">{value}</div>
        <div class="kpi-sub">{sublabel}</div>
    </div>
    """

# ==========================================
# HELPER FUNCTIONS (TANGGAL INDO & FILTER)
# ==========================================
BULAN_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def make_unique_cols(cols):
    seen = {}
    out = []
    for c in cols:
        s = str(c).replace('\n', ' ').strip()
        if not s:
            s = "KOLOM"
        if s in seen:
            seen[s] += 1
            out.append(f"{s} ({seen[s]})")
        else:
            seen[s] = 0
            out.append(s)
    return out

def ensure_unique_cols(df):
    if df is None or df.empty:
        return df
    out = df.copy()
    out.columns = make_unique_cols(out.columns)
    return out

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
    df_out = ensure_unique_cols(df)
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

@st.cache_data(ttl=15)
def load_data(url, header_row=0):
    try:
        df = pd.read_csv(url, header=header_row)
        df.columns = make_unique_cols(df.columns)
        return df
    except Exception:
        return pd.DataFrame()

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSuPAMy4KN4jFEnYc3C6xHVWnXsylZ6c0wMrIkFSuRY3IphB8EOdoVf1gII&s=10", width=90)
st.sidebar.title("Navigasi Procurement")
mode = st.sidebar.radio("Pilih Dashboard:", [
    "🏢 Central Procurement & Interco",
    "🏗️ Project (YTP Tahap 2 & 3)"
])
st.sidebar.divider()
if st.sidebar.button("🔄 Refresh Data Live"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# MODE 1: CENTRAL PROCUREMENT & INTERCO
# ==========================================
if mode == "🏢 Central Procurement & Interco":
    URL_RFQ = "https://docs.google.com/spreadsheets/d/18isSUeBYGiM2xuhV8QsXP57_AOotJ07vu1dvd5i62GI/export?format=csv&gid=1100229590"
    URL_ORDER = "https://docs.google.com/spreadsheets/d/18isSUeBYGiM2xuhV8QsXP57_AOotJ07vu1dvd5i62GI/export?format=csv&gid=467075902"

    df_rfq = load_data(URL_RFQ, header_row=1)
    df_order = load_data(URL_ORDER, header_row=0)

    now_str = datetime.now().strftime("%d/%m/%Y, %H:%M WIB")
    st.markdown(f"""
        <div class="top-banner">
            <div>
                <div class="banner-title">
                    📊 Purchasing & Procurement Dashboard
                    <span class="version-pill">v2.0 Live</span>
                </div>
                <div class="banner-sub">Div. Procurement & Interco • Data langsung dari Google Sheets (MASTER RFQ & MASTER ORDER)</div>
            </div>
            <div class="sync-badge">
                <strong>Sinkronisasi Live:</strong> {now_str}<br/>
                {len(df_rfq):,} baris RFQ • {len(df_order):,} baris Order
            </div>
        </div>
    """, unsafe_allow_html=True)

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
            vend_col_order = next((c for c in df_order.columns if 'VENDOR' in str(c).upper()), None)

            list_cust_options = sorted(list(df_order[kat_col_order].dropna().unique())) if kat_col_order else []
            list_status_options = sorted(list(df_order[status_col].dropna().unique())) if status_col else []
            list_vendor_options = sorted(list(df_order[vend_col_order].dropna().unique())) if vend_col_order else []

            # Bar Filter Horizontal
            f1, f2, f3, f4, f5 = st.columns([1.2, 1.1, 1.2, 1.2, 1.3])
            with f1:
                date_range = st.date_input("📅 Kalender Aktif", [min_date, max_date], key="i_date")
            with f2:
                pilih_status = st.selectbox("🔽 Status Order", ["Semua"] + list_status_options, key="i_stat")
            with f3:
                pilih_cust = st.multiselect("🏢 Kategori / Customer", list_cust_options, placeholder="Semua Kategori", key="i_cust")
            with f4:
                pilih_vend = st.selectbox("🏭 Supplier / Vendor", ["Semua"] + list_vendor_options, key="i_vend")
            with f5:
                pilih_no = st.text_input("🔍 Cari No PO / SO / Item", placeholder="Ketik kata kunci...", key="i_no")

            df_order_filtered = df_order.copy()
            if pilih_status != "Semua" and status_col:
                df_order_filtered = df_order_filtered[df_order_filtered[status_col] == pilih_status]
            if pilih_cust and kat_col_order:
                df_order_filtered = df_order_filtered[df_order_filtered[kat_col_order].isin(pilih_cust)]
            if pilih_vend != "Semua" and vend_col_order:
                df_order_filtered = df_order_filtered[df_order_filtered[vend_col_order] == pilih_vend]
            if pilih_no:
                df_order_filtered = df_order_filtered[
                    df_order_filtered.astype(str).apply(lambda x: x.str.contains(pilih_no, case=False, na=False)).any(axis=1)
                ]

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
            st.markdown("""
                <div class="sec-card-header">
                    <div class="sec-title">📦 Jalur Komersial Eksternal (Termasuk SIBIMATECH)</div>
                    <div class="sec-desc">Siklus penuh: Permintaan (RFQ) → Sudah Terbit SQ → Jadi PO User / Order → Proses → Sudah Diterima</div>
                </div>
            """, unsafe_allow_html=True)

            kat_rfq_c = next((c for c in df_rfq.columns if 'KATEGORI' in str(c).upper()), None)
            cust_rfq_c = next((c for c in df_rfq.columns if 'CUSTOMER' in str(c).upper() and 'PIC' not in str(c).upper()), None)
            sq_rfq_c = next((c for c in df_rfq.columns if 'NO SQ' in str(c).upper()), None)

            mask_rfq_int = df_rfq.apply(lambda r: is_internal_row(r, kat_rfq_c, cust_rfq_c), axis=1)
            df_rfq_ext = df_rfq[~mask_rfq_int].copy()
            if pilih_cust and kat_rfq_c:
                df_rfq_ext = df_rfq_ext[df_rfq_ext[kat_rfq_c].isin(pilih_cust)]

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
            total_margin_exc = total_revenue_exc - total_hpp_exc
            margin_pct = (total_margin_exc / total_revenue_exc * 100) if total_revenue_exc > 0 else 0
            total_transaksi_unik = df_komersial[po_cust_col].nunique() if (po_cust_col and not df_komersial[po_cust_col].dropna().empty) else len(df_komersial)

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(render_kpi_card("Permintaan RFQ Eksternal", f"{total_permintaan_rfq:,}", "Item masuk dari customer", "📩", "#eff6ff", "#2563eb"), unsafe_allow_html=True)
            c2.markdown(render_kpi_card("Sudah Terbit SQ", f"{sudah_sq_rfq:,}", "RFQ memiliki nomor SQ", "📄", "#f5f3ff", "#7c3aed"), unsafe_allow_html=True)
            c3.markdown(render_kpi_card("Jadi PO User / Order", f"{jadi_po_user:,}", f"{total_transaksi_unik} PO Customer unik", "🛒", "#ecfeff", "#0891b2"), unsafe_allow_html=True)
            c4.markdown(render_kpi_card("Sudah Diterima", f"{sudah_diterima_ext:,}", "Terkirim & diterima user", "✅", "#ecfdf5", "#059669"), unsafe_allow_html=True)

            st.write("")
            c5, c6, c7, c8 = st.columns(4)
            c5.markdown(render_kpi_card("Total Pembelian (HPP)", f"Rp {total_hpp_exc:,.0f}".replace(',', '.'), "Exclude PPN", "🏷️", "#fefce8", "#ca8a04"), unsafe_allow_html=True)
            c6.markdown(render_kpi_card("Penjualan (Exclude PPN)", f"Rp {total_revenue_exc:,.0f}".replace(',', '.'), "Nilai jual bersih", "💰", "#eff6ff", "#1d4ed8"), unsafe_allow_html=True)
            c7.markdown(render_kpi_card("Penjualan (Include PPN)", f"Rp {total_revenue_inc:,.0f}".replace(',', '.'), "Termasuk PPN 11%", "🧾", "#f0fdf4", "#15803d"), unsafe_allow_html=True)
            c8.markdown(render_kpi_card("Estimasi Margin", f"Rp {total_margin_exc:,.0f}".replace(',', '.'), f"{margin_pct:.1f}% dari penjualan", "📈", "#fdf2f8", "#db2777"), unsafe_allow_html=True)

            st.write("")
            st.markdown("**📑 Tabel Detail Item / Transaksi Komersial Eksternal**")
            ext_priority_cols = []
            for c in [
                kat_col_order, cust_col_order, po_cust_col, 'TGL PO CUSTOMER',
                sq_order_col, 'TGL SQ', 'NO SO', 'NO PO', 'ITEM', qty_col,
                price_col, hpp_col, status_col, 'TGL ESTIMASI SAMPAI', 'TGL GRN', 'TGL DO', 'TGL CUST TERIMA'
            ]:
                if c and c in df_komersial.columns and c not in ext_priority_cols:
                    ext_priority_cols.append(c)
            ext_rest_cols = [c for c in df_komersial.columns if c not in ext_priority_cols and not str(c).endswith('_CLEAN')]
            df_komersial_view = ensure_unique_cols(df_komersial[ext_priority_cols + ext_rest_cols]) if not df_komersial.empty else df_komersial
            st.dataframe(format_date_columns(df_komersial_view), use_container_width=True, height=340)

            # =========================================================
            # BAGIAN 2: TRANSAKSI INTERNAL (SIBIMA & AMIN)
            # =========================================================
            st.markdown("""
                <div class="sec-card-header" style="margin-top:24px;">
                    <div class="sec-title">🏢 Jalur Operasional Internal (SIBIMA & AMIN)</div>
                    <div class="sec-desc">Pantauan operasional internal: Sudah diproses belum • Pembayaran sudah diajukan belum (BPV) • Sudah sampai belum</div>
                </div>
            """, unsafe_allow_html=True)

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
                ic1.markdown(render_kpi_card("Total Item Internal", f"{len(df_internal_all):,}", "SIBIMA & AMIN", "📋", "#f1f5f9", "#334155"), unsafe_allow_html=True)
                ic2.markdown(render_kpi_card("Sudah Diproses", f"{int(sudah_diproses.sum()):,}", f"Belum: {int((~sudah_diproses).sum())} item", "⚙️", "#eff6ff", "#2563eb"), unsafe_allow_html=True)
                ic3.markdown(render_kpi_card("Pembayaran Diajukan", f"{int(has_bpv.sum()):,}", f"Belum BPV: {int((~has_bpv).sum())} item", "💳", "#fefce8", "#ca8a04"), unsafe_allow_html=True)
                ic4.markdown(render_kpi_card("Sudah Sampai", f"{int(has_sampai.sum()):,}", f"Belum sampai: {int((~has_sampai).sum())} item", "📦", "#ecfdf5", "#059669"), unsafe_allow_html=True)

                st.write("")
                df_internal_disp = df_internal_all.copy()
                df_internal_disp.insert(0, "Status Sampai", has_sampai.map({True: "✅ Sudah Sampai", False: "⏳ Belum Sampai"}))
                df_internal_disp.insert(0, "Pembayaran (BPV)", has_bpv.map({True: "✅ Sudah Diajukan", False: "⏳ Belum Diajukan"}))
                df_internal_disp.insert(0, "Status Proses", sudah_diproses.map({True: "✅ Sudah Diproses", False: "⏳ Belum Diproses"}))

                int_priority = []
                for c in [
                    "Status Proses", "Pembayaran (BPV)", "Status Sampai",
                    kat_col_order, cust_col_order, 'ITEM', qty_col, status_col,
                    pr_col, 'TGL PR', po_col, 'TGL PO', bpv_col, 'TGL BPV',
                    'TGL ESTIMASI SAMPAI', grn_col, 'TGL GRN', do_col, terima_col
                ]:
                    if c and c in df_internal_disp.columns and c not in int_priority:
                        int_priority.append(c)
                int_rest = [c for c in df_internal_disp.columns if c not in int_priority and not str(c).endswith('_CLEAN')]

                st.markdown("**📑 Tabel Detail Item / Transaksi Internal (SIBIMA & AMIN)**")
                st.dataframe(format_date_columns(ensure_unique_cols(df_internal_disp[int_priority + int_rest])), use_container_width=True, height=340)
            else:
                st.info("Tidak ada data transaksi internal (SIBIMA & AMIN) pada filter saat ini.")

    # --- TAB 2: MONITORING RFQ (PENDING & KENDALA) ---
    with tab_i2:
        st.markdown("""
            <div class="sec-card-header">
                <div class="sec-title">🔍 Monitoring RFQ: Belum Dikerjakan & Kendala</div>
                <div class="sec-desc">Melacak antrean RFQ aktif di luar COMPLETE/CANCEL, serta memisahkan item PENDING dengan kendala HOLD untuk follow-up hingga CLOSE.</div>
            </div>
        """, unsafe_allow_html=True)

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
                return ('PENDING' in status_val and 'HOLD' in kendala_val and 'CLOSE' not in status_val)

            def is_pending_rfq(row):
                if is_pending_hold_followup(row):
                    return False
                if stat_rfq_col and pd.notna(row[stat_rfq_col]):
                    val = str(row[stat_rfq_col]).upper().strip()
                    if any(k in val for k in ['COMPLETE', 'DONE', 'CLOSED', 'SELESAI', 'PO', 'CLOSE', 'CANCEL']):
                        return False
                return True

            df_rfq_pending = reorder_kendala_first(df_rfq[df_rfq.apply(is_pending_rfq, axis=1)].copy()) if stat_rfq_col else df_rfq.copy()
            df_rfq_hold_followup = reorder_kendala_first(df_rfq[df_rfq.apply(is_pending_hold_followup, axis=1)].copy()) if stat_rfq_col else pd.DataFrame(columns=df_rfq.columns)

            r1, r2, r3 = st.columns(3)
            r1.markdown(render_kpi_card("Total RFQ Masuk", f"{len(df_rfq):,}", "Seluruh baris MASTER RFQ", "📥", "#eff6ff", "#2563eb"), unsafe_allow_html=True)
            r2.markdown(render_kpi_card("RFQ Belum Selesai", f"{len(df_rfq_pending):,}", "Antrean aktif perlu diproses", "🔥", "#fef2f2", "#dc2626"), unsafe_allow_html=True)
            r3.markdown(render_kpi_card("RFQ Di-hold (Follow-up)", f"{len(df_rfq_hold_followup):,}", "Dipantau sampai CLOSE", "⏸️", "#fefce8", "#ca8a04"), unsafe_allow_html=True)

            st.write("")
            st.markdown("**📋 Daftar RFQ Belum Selesai & Kendala**")
            st.dataframe(format_date_columns(df_rfq_pending), use_container_width=True, height=400)

            csv_rfq_pending = format_date_columns(df_rfq_pending).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Laporan RFQ Pending (CSV)", data=csv_rfq_pending, file_name="RFQ_Pending_Kendala.csv", mime="text/csv")

            if not df_rfq_hold_followup.empty:
                with st.expander("📌 Daftar RFQ Di-hold (Sementara Selesai — Perlu Follow-up sampai CLOSE)"):
                    st.dataframe(format_date_columns(df_rfq_hold_followup), use_container_width=True, height=300)
                    csv_rfq_hold = format_date_columns(df_rfq_hold_followup).to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Laporan RFQ Di-hold (CSV)", data=csv_rfq_hold, file_name="RFQ_Hold_FollowUp.csv", mime="text/csv", key="dl_rfq_hold")
        else:
            st.warning("Data Master RFQ kosong.")

    # --- TAB 3: KONVERSI SQ KE PO ---
    with tab_i3:
        st.markdown("""
            <div class="sec-card-header">
                <div class="sec-title">📈 Analisis Konversi NO SQ (MASTER RFQ → MASTER ORDER)</div>
                <div class="sec-desc">Memeriksa setiap nomor SQ unik yang terbit di MASTER RFQ apakah sudah tercatat masuk ke MASTER ORDER.</div>
            </div>
        """, unsafe_allow_html=True)

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

            s1, s2, s3, s4 = st.columns(4)
            s1.markdown(render_kpi_card("Total NO SQ Unik", f"{total_sq_rfq:,}", "Tercatat di MASTER RFQ", "📄", "#eff6ff", "#2563eb"), unsafe_allow_html=True)
            s2.markdown(render_kpi_card("Masuk Master Order", f"{masuk_order_count:,}", "Sudah konversi ke PO/Order", "✅", "#ecfdf5", "#059669"), unsafe_allow_html=True)
            s3.markdown(render_kpi_card("Belum Masuk Order", f"{belum_masuk_count:,}", "Belum ditemukan di Order", "⏳", "#fef2f2", "#dc2626"), unsafe_allow_html=True)
            s4.markdown(render_kpi_card("Conversion Rate SQ", f"{conversion_rate:.2f}%", "Rasio SQ tembus Order", "🎯", "#f5f3ff", "#7c3aed"), unsafe_allow_html=True)

            st.write("")
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
                    "Status Masuk Order": "✅ Masuk Order" if is_in_order else "⏳ Belum Masuk Order",
                    "Jumlah Item RFQ": len(sub),
                    "Kategori": ", ".join(sorted(set(sub[kat_rfq_c].dropna().astype(str)))) if kat_rfq_c else "-",
                    "Customer": ", ".join(sorted(set(sub[cust_rfq_c].dropna().astype(str)))) if cust_rfq_c else "-",
                    "Status RFQ": ", ".join(sorted(set(sub[stat_rfq_c].dropna().astype(str)))) if stat_rfq_c else "-"
                })

            df_sq_track = pd.DataFrame(sq_rows)
            filter_sq_status = st.selectbox("🔍 Filter Status SQ pada Master Order:", ["Semua", "✅ Masuk Order", "⏳ Belum Masuk Order"], key="sq_track_filter")
            df_sq_track_view = df_sq_track[df_sq_track["Status Masuk Order"] == filter_sq_status] if filter_sq_status != "Semua" else df_sq_track

            st.dataframe(df_sq_track_view, use_container_width=True, height=380)
            csv_sq_track = df_sq_track_view.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Laporan Tracking SQ ke Order (CSV)", data=csv_sq_track, file_name="Tracking_SQ_ke_Master_Order.csv", mime="text/csv")
        else:
            st.warning("Data RFQ atau Order kosong, atau kolom NO SQ tidak ditemukan.")

    # --- TAB 4: ANALISIS VENDOR ---
    with tab_i4:
        st.markdown("""
            <div class="sec-card-header">
                <div class="sec-title">📋 Analisis Performa & Transaksi Vendor</div>
                <div class="sec-desc">Sebaran volume item transaksi berdasarkan nama vendor pada MASTER ORDER.</div>
            </div>
        """, unsafe_allow_html=True)

        if not df_order.empty:
            vend_c = next((c for c in df_order.columns if 'VENDOR' in str(c).upper()), None)
            if vend_c:
                vendor_counts = df_order[vend_c].value_counts().reset_index()
                vendor_counts.columns = ['Vendor', 'Total Transaksi']
                st.markdown(render_kpi_card("Total Vendor Aktif", f"{len(vendor_counts):,}", "Vendor terdaftar pada transaksi order", "🏭", "#eff6ff", "#2563eb"), unsafe_allow_html=True)
                st.write("")
                bar_chart_full = alt.Chart(vendor_counts.head(20)).mark_bar(cornerRadiusEnd=6, color="#2563eb").encode(
                    x=alt.X('Total Transaksi:Q', title='Jumlah Item Order'),
                    y=alt.Y('Vendor:N', sort='-x', title='Nama Vendor'),
                    tooltip=['Vendor', 'Total Transaksi']
                ).properties(height=460)
                st.altair_chart(bar_chart_full, use_container_width=True)
                st.dataframe(vendor_counts, use_container_width=True, height=340)
            else:
                st.warning("Kolom Vendor tidak ditemukan pada Master Order.")

    # --- TAB 5: OUTSTANDING SUPPLY VENDOR ---
    with tab_i5:
        st.markdown("""
            <div class="sec-card-header">
                <div class="sec-title">🚚 Monitoring Outstanding Supply Vendor</div>
                <div class="sec-desc">Daftar item order yang statusnya belum Sudah Diterima dan bukan Cancel.</div>
            </div>
        """, unsafe_allow_html=True)

        if not df_order.empty:
            status_col = next((c for c in df_order.columns if 'STATUS' in str(c).upper()), None)
            if status_col:
                df_interco_out = df_order[~df_order[status_col].astype(str).str.upper().str.strip().isin(['SUDAH DITERIMA', 'CANCEL'])].copy()
            else:
                df_interco_out = df_order.copy()

            vend_col_in = next((c for c in df_interco_out.columns if 'VENDOR' in str(c).upper()), None)
            list_v_in = ["Semua Vendor"] + sorted([str(x) for x in df_interco_out[vend_col_in].dropna().unique()]) if vend_col_in else ["Semua Vendor"]
            pilih_v_in = st.selectbox("🔍 Filter Berdasarkan Vendor:", list_v_in)

            if pilih_v_in != "Semua Vendor" and vend_col_in:
                df_interco_out = df_interco_out[df_interco_out[vend_col_in].astype(str) == pilih_v_in]

            st.markdown(render_kpi_card("Total Item Outstanding", f"{len(df_interco_out):,}", "Menunggu pengiriman / penerimaan", "🚚", "#fefce8", "#ca8a04"), unsafe_allow_html=True)
            st.write("")
            st.dataframe(format_date_columns(df_interco_out), use_container_width=True, height=450)
            csv_in_out = format_date_columns(df_interco_out).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Laporan Outstanding (CSV)", data=csv_in_out, file_name="Outstanding_Interco_Vendor.csv", mime="text/csv")

# ==========================================
# MODE 2: PROJECT YTP (DI-HOLD SEMENTARA)
# ==========================================
elif mode == "🏗️ Project (YTP Tahap 2 & 3)":
    st.title("🏗️ DASHBOARD ANALITIK PROJECT (YTP)")
    st.info("Mode Project YTP sedang di-hold sementara sesuai permintaan. Silakan gunakan menu Central Procurement & Interco.")
