"""
app.py — E-Commerce Product Intelligence Dashboard
=====================================================
Çalıştırmak için:
    pip install streamlit pandas plotly
    streamlit run app.py
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Product Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }

    [data-testid="stSidebar"] { background-color: #161822 !important; border-right: 1px solid #2a2d3a; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stMarkdown { color: #9ca3af; }

    .metric-card {
        background: linear-gradient(135deg, #1a1d2e, #222640);
        border: 1px solid #2e3250;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
    }
    .metric-card .val { font-size: 2rem; font-weight: 700; color: #7dd3fc; }
    .metric-card .lbl { font-size: 0.72rem; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
    .metric-card .sub { font-size: 0.7rem; color: #4ade80; margin-top: 3px; }

    .product-card {
        background: #1a1d2e;
        border: 1px solid #2e3250;
        border-radius: 10px;
        padding: 13px 16px;
        margin-bottom: 2px;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .product-card:hover { border-color: #7dd3fc; }
    .product-card .pc-top { display: flex; align-items: center; gap: 12px; }
    .product-card .pc-id { font-size: 0.65rem; color: #4b5563; font-family: monospace; min-width: 90px; }
    .product-card .pc-name { flex: 1; font-size: 0.82rem; color: #e2e8f0; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 380px; }
    .product-card .pc-price { color: #7dd3fc; font-weight: 600; font-size: 0.82rem; min-width: 80px; text-align: right; }
    .product-card .pc-stars { color: #fbbf24; font-size: 0.75rem; margin-top: 4px; }
    .product-card .pc-rating { color: #9ca3af; font-size: 0.7rem; margin-left: 6px; }

    .ai-panel {
        background: linear-gradient(135deg, #1a1d2e, #1e2038);
        border: 1px solid #7dd3fc33;
        border-radius: 14px;
        padding: 22px;
        height: 100%;
    }
    .ai-panel .ai-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
    .ai-panel .ai-header h3 { color: #7dd3fc; font-size: 0.95rem; margin: 0; }
    .ai-badge { background: #7dd3fc18; color: #7dd3fc; font-size: 0.58rem; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 1px; }
    .ai-panel .ai-name { color: #e2e8f0; font-size: 0.88rem; font-weight: 600; margin-bottom: 6px; }
    .ai-panel .ai-id { color: #4b5563; font-size: 0.65rem; font-family: monospace; margin-bottom: 14px; }
    .ai-panel .ai-summary { color: #cbd5e1; font-size: 0.82rem; line-height: 1.65; margin-bottom: 16px; }
    .ai-panel .ai-stars { color: #fbbf24; font-size: 0.9rem; margin-bottom: 4px; }

    .section-title { color: #7dd3fc; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; opacity: 0.7; }
    
    .info-box {
        background-color: #1e293b;
        border-left: 4px solid #7dd3fc;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 20px;
        color: #cbd5e1;
        font-size: 0.9rem;
    }
    .info-box strong { color: #e2e8f0; }

    .stDataFrame { background: #1a1d2e !important; }
    div[data-testid="stMetric"] { background: #1a1d2e; border: 1px solid #2e3250; border-radius: 12px; padding: 12px; }
    div[data-testid="stMetric"] label { color: #6b7280 !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="stMetric"] div { color: #7dd3fc !important; font-size: 1.6rem !important; font-weight: 700; }
    
    /* Button Override */
    .stButton button { 
        background: #1e293b !important; 
        color: #94a3b8 !important; 
        border: 1px solid #334155 !important; 
        border-radius: 8px !important; 
        font-weight: 500 !important;
        width: 100%;
    }
    .stButton button:hover { 
        background: #334155 !important; 
        color: #f8fafc !important; 
        border-color: #7dd3fc !important;
    }
    
    .stTabs [data-baseid] { color: #6b7280; font-size: 0.82rem; }
    .stTabs [aria-selected="true"] { color: #7dd3fc !important; border-bottom-color: #7dd3fc !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("urunler_ai_ozetli.csv")
    except FileNotFoundError:
        st.error("CSV dosyası bulunamadı. Lütfen 'urunler_ai_ozetli.csv' dosyasını ekleyin.")
        return pd.DataFrame()

    def parse_price(val):
        if pd.isna(val): return 0.0
        val = str(val).replace("TL", "").strip()
        val = val.replace(".", "").replace(",", ".")
        try: return float(val)
        except ValueError: return 0.0

    df["fiyat_num"] = df["fiyat"].apply(parse_price)

    # Toplam yorum sayısı
    cols = ["5star", "4star", "3star", "2star", "1star"]
    if set(cols).issubset(df.columns):
        df["toplam_yorum"] = df[cols].sum(axis=1)
    else:
        df["toplam_yorum"] = 0

    def price_range(p):
        if p < 100: return "0–100 ₺"
        elif p < 500: return "100–500 ₺"
        elif p < 1000: return "500–1K ₺"
        elif p < 5000: return "1K–5K ₺"
        else: return "5K+ ₺"

    df["fiyat_araligi"] = df["fiyat_num"].apply(price_range)

    if "ai_ozet" not in df.columns: df["ai_ozet"] = None
    if "yorum_ozeti" not in df.columns: df["yorum_ozeti"] = None

    return df

df = load_data()
if df.empty: st.stop()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ E-Commerce Intelligence")
    st.markdown("---")
    search = st.text_input("🔍 Ürün ara...", placeholder="Bugatti, telefon kılıf...")
    
    min_val, max_val = int(df["fiyat_num"].min()), int(df["fiyat_num"].max()) + 1
    min_p, max_p = st.slider("💰 Fiyat Aralığı (₺)", min_value=0, max_value=max_val, value=(0, max_val), step=50)

    max_reviews = int(df["toplam_yorum"].max()) if df["toplam_yorum"].max() > 0 else 100
    min_reviews = st.slider("💬 Min Yorum Sayısı", 0, max_reviews, value=0, step=100)

    sort_by = st.selectbox("📊 Sıralama", ["Puana Göre ↓", "Yoruma Göre ↓", "Fiyata Göre ↑", "Fiyata Göre ↓"])
    st.markdown("---")
    st.markdown(f"<div style='color:#4b5563; font-size:0.7rem;'>Toplam veri: {len(df)} ürün</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILTER & SORTING (AI Priority Logic)
# ─────────────────────────────────────────────
filtered = df.copy()
if search: filtered = filtered[filtered["urun_adi"].str.contains(search, case=False, na=False)]
filtered = filtered[
    (filtered["fiyat_num"] >= min_p) &
    (filtered["fiyat_num"] <= max_p) &
    (filtered["toplam_yorum"] >= min_reviews)
]

# AI Analizi Var mı Kontrolü (Hata içermeyen ve uzunluğu >20 olanlar)
def has_valid_ai(text):
    text = str(text)
    # Hata mesajı varsa veya boşsa 0, değilse 1
    if len(text) > 20 and "Error" not in text and "context_length" not in text:
        return 1
    return 0

filtered["ai_priority"] = filtered["ai_ozet"].apply(has_valid_ai)

# Sıralama: Önce AI Priority (1 olanlar üste), Sonra Seçilen Filtre
if sort_by == "Puana Göre ↓":
    filtered = filtered.sort_values(by=["ai_priority", "ortalama_star_puani"], ascending=[False, False])
elif sort_by == "Yoruma Göre ↓":
    filtered = filtered.sort_values(by=["ai_priority", "toplam_yorum"], ascending=[False, False])
elif sort_by == "Fiyata Göre ↑":
    filtered = filtered.sort_values(by=["ai_priority", "fiyat_num"], ascending=[False, True])
else: # Fiyata Göre ↓
    filtered = filtered.sort_values(by=["ai_priority", "fiyat_num"], ascending=[False, False])


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_dashboard, tab_products, tab_analysis = st.tabs(["📊 Dashboard", "📦 Ürünler", "🤖 AI Analiz"])

# ═══════════════════════════════════════════════
# TAB 1: DASHBOARD
# ═══════════════════════════════════════════════
with tab_dashboard:
    # --- YENİ EKLENEN: Ana Sayfa Bilgi Kartı ---
    st.markdown("""
    <div class="info-box">
        <h4 style="margin:0 0 10px 0; color:#7dd3fc;">🚀 Hızlı Başlangıç Rehberi</h4>
        Bu panel, e-ticaret rakiplerini yapay zeka ile analiz etmeni sağlar.
        <ul style="margin:10px 0 0 20px;">
            <li><b>Adım 1:</b> Sol menüden fiyat veya yorum sayısı filtresi yapın.</li>
            <li><b>Adım 2:</b> <b>"Ürünler"</b> sekmesine geçin ve <b>"🔍 İncele"</b> butonuna basın.</li>
            <li><b>Adım 3:</b> Sağ tarafta açılan panelden yapay zeka (AI) yorum özetini okuyun.</li>
        </ul>
        <small style="color:#6b7280; margin-top:5px; display:block;">Not: AI analizi yapılmış ürünler listede en üstte görünür.</small>
    </div>
    """, unsafe_allow_html=True)
    # -------------------------------------------

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="val">{len(df):,}</div><div class="lbl">Toplam Ürün</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="val">{df["toplam_yorum"].sum():,}</div><div class="lbl">Toplam Yorum</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="val">{df["ortalama_star_puani"].mean():.2f}</div><div class="lbl">Ort. Puan</div></div>""", unsafe_allow_html=True)
    with col4:
        # Başarılı AI sayısını hesapla
        valid_count = filtered["ai_priority"].sum()
        st.markdown(f"""<div class="metric-card"><div class="val">{valid_count:,}</div><div class="lbl">AI Analizli Ürün</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown('<div class="section-title">Fiyat Aralığı Dağılımı</div>', unsafe_allow_html=True)
        price_order = ["0–100 ₺", "100–500 ₺", "500–1K ₺", "1K–5K ₺", "5K+ ₺"]
        price_counts = df["fiyat_araligi"].value_counts().reindex(price_order, fill_value=0)
        fig = go.Figure(data=[go.Bar(
            x=price_counts.index.tolist(), y=price_counts.values.tolist(),
            marker_color=["#7dd3fc", "#38bdf8", "#0ea5e9", "#0284c7", "#0369a1"],
            text=price_counts.values.tolist(), textposition="outside",
            textfont=dict(color="#9ca3af", size=11),
        )])
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1a1d2e",
            font=dict(color="#9ca3af", size=11),
            xaxis=dict(showgrid=False, showline=False),
            yaxis=dict(showgrid=True, gridcolor="#2e3250", showline=False),
            margin=dict(t=10, b=30, l=10, r=10), height=260,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with chart_col2:
        st.markdown('<div class="section-title">Puan Dağılımı</div>', unsafe_allow_html=True)
        fig2 = go.Figure(data=[go.Histogram(
            x=df["ortalama_star_puani"], nbinsx=20,
            marker_color="#7dd3fc", marker_line_color="#0f1117", marker_line_width=1,
        )])
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1a1d2e",
            font=dict(color="#9ca3af", size=11),
            xaxis=dict(showgrid=False, showline=False, title="Puan"),
            yaxis=dict(showgrid=True, gridcolor="#2e3250", showline=False),
            margin=dict(t=10, b=30, l=10, r=10), height=260,
        )
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

# ═══════════════════════════════════════════════
# TAB 2: ÜRÜNLER
# ═══════════════════════════════════════════════
with tab_products:
    left_col, right_col = st.columns([1, 1], gap="medium")

    with left_col:
        st.markdown(f'<div class="section-title">Ürün Listesi ({len(filtered)} sonuç)</div>', unsafe_allow_html=True)
        if "selected_idx" not in st.session_state: st.session_state.selected_idx = 0
        
        show_count = 80
        display_df = filtered.head(show_count).reset_index(drop=True)

        for i, row in display_df.iterrows():
            stars_filled = int(round(row["ortalama_star_puani"]))
            stars_str = "⭐" * stars_filled + "☆" * (5 - stars_filled)
            border_color = "#7dd3fc" if st.session_state.selected_idx == i else "#2e3250"
            
            # AI ikonu ekle (Varsa)
            ai_badge = "🤖" if row["ai_priority"] == 1 else ""

            st.markdown(f"""<div class="product-card" style="border-color:{border_color};">
                <div class="pc-top">
                    <span class="pc-id">{row['urun_id']} {ai_badge}</span>
                    <span class="pc-name">{row['urun_adi'][:55]}</span>
                    <span class="pc-price">{row['fiyat']}</span>
                </div>
                <div class="pc-stars">{stars_str} <span class="pc-rating">{row['ortalama_star_puani']:.1f} · {row['toplam_yorum']:,} yorum</span></div>
            </div>""", unsafe_allow_html=True)

            if st.button("🔍 İncele", key=f"btn_{i}", use_container_width=True):
                st.session_state.selected_idx = i
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

        if len(filtered) > show_count:
            st.markdown(f"<div style='color:#4b5563; font-size:0.7rem; text-align:center; padding:8px;'>... ve {len(filtered) - show_count} ürün daha</div>", unsafe_allow_html=True)

    with right_col:
        if len(display_df) > 0:
            idx = st.session_state.selected_idx
            if idx >= len(display_df):
                idx = 0
                st.session_state.selected_idx = 0
            
            sel = display_df.iloc[idx]
            stars_filled = int(round(sel["ortalama_star_puani"]))
            stars_str = "⭐" * stars_filled + "☆" * (5 - stars_filled)

            raw_ai = str(sel["ai_ozet"]) if pd.notna(sel["ai_ozet"]) else ""
            raw_yorum = str(sel["yorum_ozeti"]) if pd.notna(sel["yorum_ozeti"]) else ""

            # Hata mesajı kontrolü
            is_error = "context_length_exceeded" in raw_ai or "Error code:" in raw_ai
            
            if is_error:
                ai_text = "⚠️ <b>Analiz Başarısız:</b> Bu ürünün yorum sayısı yapay zeka modelinin (GPT) kelime sınırını aştığı için analiz tamamlanamadı."
                border_style = "border:1px solid #ef4444; color:#fca5a5;"
            elif len(raw_ai) < 5:
                ai_text = "Bu ürün için henüz bir AI özeti bulunmuyor."
                border_style = "border:1px dashed #4b5563; color:#6b7280;"
            else:
                ai_text = raw_ai
                border_style = "border:1px solid #2e3250; color:#cbd5e1;"

            star_vals = [sel.get("5star",0), sel.get("4star",0), sel.get("3star",0), sel.get("2star",0), sel.get("1star",0)]
            fig_star = go.Figure(data=[go.Bar(
                y=["5 ⭐", "4 ⭐", "3 ⭐", "2 ⭐", "1 ⭐"], x=star_vals, orientation="h",
                marker_color=["#22c55e", "#4ade80", "#fbbf24", "#fb923c", "#ef4444"],
                text=[f"{v:,}" for v in star_vals], textposition="outside",
                textfont=dict(color="#9ca3af", size=10),
            )])
            fig_star.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1a1d2e",
                font=dict(color="#9ca3af", size=10),
                xaxis=dict(showgrid=True, gridcolor="#2e3250", showline=False),
                yaxis=dict(showgrid=False, showline=False),
                margin=dict(t=5, b=5, l=40, r=50), height=160,
            )

            st.markdown(f"""<div class="ai-panel">
                <div class="ai-header"><span class="ai-badge">🤖 AI Özet</span></div>
                <div class="ai-name">{sel['urun_adi'][:70]}</div>
                <div class="ai-id">{sel['urun_id']} · {sel['fiyat']}</div>
                <div class="ai-stars">{stars_str} <span style="color:#9ca3af; font-size:0.75rem;">{sel['ortalama_star_puani']:.1f} / 5.0 · {sel['toplam_yorum']:,} yorum</span></div>
            </div>""", unsafe_allow_html=True)

            st.plotly_chart(fig_star, width="stretch", config={"displayModeBar": False})

            st.markdown('<div class="section-title" style="margin-top:10px;">AI Analizi</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="background:#1a1d2e; {border_style} border-radius:10px; padding:14px; font-size:0.82rem; line-height:1.7;">{ai_text}</div>', unsafe_allow_html=True)

            if len(raw_yorum) > 5:
                st.markdown('<div class="section-title" style="margin-top:14px;">Kullanıcı Yorum Özeti</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#1a1d2e; border:1px solid #2e3250; border-radius:10px; padding:14px; color:#9ca3af; font-size:0.78rem; line-height:1.7;">{raw_yorum}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB 3: AI ANALIZ
# ═══════════════════════════════════════════════
with tab_analysis:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Puan Dağılımı</div>', unsafe_allow_html=True)
        bins = [0, 2, 3, 4, 4.5, 5.1]
        labels = ["0–2 ⭐", "2–3 ⭐", "3–4 ⭐", "4–4.5 ⭐", "4.5–5 ⭐"]
        df["puan_grup"] = pd.cut(df["ortalama_star_puani"], bins=bins, labels=labels, right=False)
        grup_counts = df["puan_grup"].value_counts().reindex(labels, fill_value=0)
        fig_pie = go.Figure(data=[go.Pie(
            labels=grup_counts.index.tolist(), values=grup_counts.values.tolist(),
            marker_colors=["#ef4444", "#fb923c", "#fbbf24", "#4ade80", "#22c55e"],
            hole=0.5, textinfo="label+percent", textfont=dict(color="#e2e8f0", size=11),
        )])
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#9ca3af"),
            margin=dict(t=10, b=10, l=10, r=10), height=280,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_pie, width="stretch", config={"displayModeBar": False})

    with col_b:
        st.markdown('<div class="section-title">Fiyat vs Puan</div>', unsafe_allow_html=True)
        plot_df = df[df["fiyat_num"] < df["fiyat_num"].quantile(0.95)]
        fig_scatter = go.Figure(data=[go.Scatter(
            x=plot_df["fiyat_num"], y=plot_df["ortalama_star_puani"], mode="markers",
            marker=dict(
                size=5, color=plot_df["ortalama_star_puani"], colorscale="RdYlGn", cmin=1, cmax=5, showscale=True,
                colorbar=dict(title=dict(text="Puan", font=dict(color="#9ca3af")), tickfont=dict(color="#9ca3af")),
            ),
        )])
        fig_scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1a1d2e",
            font=dict(color="#9ca3af", size=10),
            xaxis=dict(title="Fiyat (₺)", showgrid=True, gridcolor="#2e3250", showline=False),
            yaxis=dict(title="Puan", showgrid=True, gridcolor="#2e3250", showline=False, range=[0, 5.2]),
            margin=dict(t=10, b=30, l=10, r=40), height=280,
        )
        st.plotly_chart(fig_scatter, width="stretch", config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)
    col_top, col_bot = st.columns(2)
    with col_top:
        st.markdown('<div class="section-title">🏆 Top 5 Ürün</div>', unsafe_allow_html=True)
        for _, r in df.nlargest(5, "ortalama_star_puani").iterrows():
             st.markdown(f"""<div style="background:#1a1d2e; border:1px solid #166534; border-radius:8px; padding:10px; margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between; color:#e2e8f0; font-size:0.8rem;">
                    <span>{r['urun_adi'][:45]}</span><span style="color:#4ade80;">{r['ortalama_star_puani']:.1f} ⭐</span>
                </div></div>""", unsafe_allow_html=True)
    with col_bot:
        st.markdown('<div class="section-title">📉 Flop 5 Ürün</div>', unsafe_allow_html=True)
        for _, r in df.nsmallest(5, "ortalama_star_puani").iterrows():
             st.markdown(f"""<div style="background:#1a1d2e; border:1px solid #7f1d1d; border-radius:8px; padding:10px; margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between; color:#e2e8f0; font-size:0.8rem;">
                    <span>{r['urun_adi'][:45]}</span><span style="color:#fca5a5;">{r['ortalama_star_puani']:.1f} ⭐</span>
                </div></div>""", unsafe_allow_html=True)