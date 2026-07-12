"""
股票追蹤與決策輔助系統 - 跨指標相關性分析頁
Stock Tracking & Decision Support System - Cross-Indicator Correlation Page

宏觀指標與股價之間的相關性視覺化分析
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="跨指標相關性 - 股票追蹤系統",
    page_icon="🔗",
    layout="wide",
)

from modules.ui import apply_style
apply_style()
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "stocks.db"


def _get_conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def load_macro(indicator_name: str) -> pd.DataFrame:
    """Load a macro indicator time series, returned sorted by date."""
    conn = _get_conn()
    df = pd.read_sql_query(
        "SELECT indicator_date AS date, value "
        "FROM macro_indicators WHERE indicator_name = ? "
        "ORDER BY indicator_date",
        conn,
        params=(indicator_name,),
    )
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    return df


def load_price(stock_id: str) -> pd.DataFrame:
    """Load closing prices for a stock, returned sorted by date."""
    conn = _get_conn()
    df = pd.read_sql_query(
        "SELECT date, close FROM prices WHERE stock_id = ? ORDER BY date",
        conn,
        params=(stock_id,),
    )
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])
    return df


def merge_on_date(df_left: pd.DataFrame, col_left: str,
                  df_right: pd.DataFrame, col_right: str) -> pd.DataFrame:
    """Inner-join two single-value DataFrames on their 'date' column."""
    merged = pd.merge(
        df_left[["date", col_left]].rename(columns={col_left: "left"}),
        df_right[["date", col_right]].rename(columns={col_right: "right"}),
        on="date",
        how="inner",
    ).sort_values("date")
    return merged


def pearson_r(x: pd.Series, y: pd.Series):
    """Return (r, p_value) for Pearson correlation."""
    mask = x.notna() & y.notna()
    x_clean, y_clean = x[mask], y[mask]
    if len(x_clean) < 3:
        return float("nan"), float("nan")
    r, p = stats.pearsonr(x_clean, y_clean)
    return r, p


# ---------------------------------------------------------------------------
# Correlation chart builder
# ---------------------------------------------------------------------------
# Template colours – consistent across all charts
LEFT_COLOR = "#4F46E5"   # indigo
RIGHT_COLOR = "#D64545"  # red (台股慣例: red=up)


def build_correlation_chart(
    left_label: str, right_label: str,
    merged: pd.DataFrame,
    chart_title: str,
) -> go.Figure:
    """Return a dual-Y Plotly figure with Pearson r annotated."""
    r, p = pearson_r(merged["left"], merged["right"])

    fig = go.Figure()

    # Left axis trace
    fig.add_trace(go.Scatter(
        x=merged["date"], y=merged["left"],
        name=left_label,
        mode="lines",
        line=dict(width=2, color=LEFT_COLOR),
        yaxis="y",
        hovertemplate=f"{left_label}: "+"%{y:.2f}<br>%{x|%Y-%m-%d}<extra></extra>",
    ))

    # Right axis trace
    fig.add_trace(go.Scatter(
        x=merged["date"], y=merged["right"],
        name=right_label,
        mode="lines",
        line=dict(width=2, color=RIGHT_COLOR, dash="dash"),
        yaxis="y2",
        hovertemplate=f"{right_label}: "+"%{y:.2f}<br>%{x|%Y-%m-%d}<extra></extra>",
    ))

    # Pearson annotation
    if not np.isnan(r):
        strength = "強" if abs(r) >= 0.7 else ("中" if abs(r) >= 0.4 else "弱")
        direction = "正" if r > 0 else "負"
        sig = "顯著" if p < 0.05 else "不顯著"
        annotation_text = (
            f"Pearson r = <b>{r:.4f}</b>　"
            f"({strength}{direction}相關，{sig} p={p:.4f})<br>"
            f"<span style='font-size:0.8rem;color:#667085;'>"
            f"資料筆數: {len(merged)}</span>"
        )
    else:
        annotation_text = "資料不足，無法計算相關係數"

    fig.update_layout(
        title=dict(text=chart_title, font=dict(size=18)),
        xaxis=dict(title="日期", gridcolor="#E6E8EF"),
        yaxis=dict(
            title=f"<b>{left_label}</b>",
            titlefont=dict(color=LEFT_COLOR),
            tickfont=dict(color=LEFT_COLOR),
            gridcolor="#E6E8EF",
        ),
        yaxis2=dict(
            title=f"<b>{right_label}</b>",
            titlefont=dict(color=RIGHT_COLOR),
            tickfont=dict(color=RIGHT_COLOR),
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=60, r=60, t=80, b=40),
        height=450,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(
                text=annotation_text,
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                showarrow=False,
                font=dict(size=13),
                xanchor="center",
            )
        ],
    )
    return fig


# ---------------------------------------------------------------------------
# Correlation pairs configuration
# ---------------------------------------------------------------------------
CORRELATION_PAIRS = [
    {
        "title": "費城半導體指數 vs 台積電 (2330) 股價",
        "left_macro": "費城半導體指數",
        "right_stock": "2330",
        "right_label": "台積電 (2330)",
        "left_label": "費城半導體指數",
    },
    {
        "title": "S&P 500 vs 台灣加權指數",
        "left_macro": "S&P 500",
        "right_macro": "台灣加權指數",
        "right_label": "台灣加權指數",
        "left_label": "S&P 500",
    },
    {
        "title": "VIX 恐慌指數 vs 台積電 (2330) 股價",
        "left_macro": "VIX 恐慌指數",
        "right_stock": "2330",
        "right_label": "台積電 (2330)",
        "left_label": "VIX 恐慌指數",
    },
    {
        "title": "美國 10 年期公債殖利率 vs 台灣加權指數",
        "left_macro": "美國 10 年期公債殖利率",
        "right_macro": "台灣加權指數",
        "right_label": "台灣加權指數",
        "left_label": "美國 10 年期公債殖利率",
    },
]


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------
st.title("🔗 跨指標相關性分析")
st.markdown("宏觀指標與股價之間的 Pearson 相關性視覺化，使用雙 Y 軸對照圖表")
st.markdown("---")

available = DB_PATH.exists()

if not available:
    st.warning("⚠️ 找不到資料庫，請先執行資料匯入。")
    st.stop()

# Let user choose lookback window
lookback_options = {"近 90 天": 90, "近 180 天": 180, "近 365 天": 365, "全部資料": None}
lookback_label = st.radio(
    "選擇時間範圍",
    options=list(lookback_options.keys()),
    index=1,
    horizontal=True,
    key="corr_lookback",
)
lookback_days = lookback_options[lookback_label]

st.markdown("")

for idx, pair in enumerate(CORRELATION_PAIRS):
    left_label = pair["left_label"]
    right_label = pair["right_label"]

    # Load left side (always a macro indicator)
    df_left = load_macro(pair["left_macro"])
    if df_left.empty:
        st.warning(f"⚠️ 找不到指標「{pair['left_macro']}」的資料，跳過此圖表。")
        continue

    # Load right side – either stock price or macro indicator
    if "right_stock" in pair:
        df_right = load_price(pair["right_stock"])
        right_col = "close"
    else:
        df_right = load_macro(pair["right_macro"])
        right_col = "value"

    if df_right.empty:
        src = f"股票 {pair['right_stock']}" if "right_stock" in pair else f"指標「{pair.get('right_macro', '')}」"
        st.warning(f"⚠️ 找不到{src}的資料，跳過此圖表。")
        continue

    # Apply lookback
    if lookback_days is not None:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=lookback_days)
        df_left = df_left[df_left["date"] >= cutoff]
        df_right = df_right[df_right["date"] >= cutoff]

    # Merge
    merged = merge_on_date(df_left, "value", df_right, right_col)

    if merged.empty or len(merged) < 3:
        st.info(f"ℹ️ 「{pair['title']}」的共同日期資料不足（僅 {len(merged)} 筆），無法繪圖。")
        continue

    fig = build_correlation_chart(left_label, right_label, merged, pair["title"])
    st.plotly_chart(fig, use_container_width=True)

    if idx < len(CORRELATION_PAIRS) - 1:
        st.markdown("---")

# ---------------------------------------------------------------------------
# Correlation matrix summary
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 相關係數總覽")

# Build a summary table
summary_rows = []
all_series = {}

# Pre-load all needed series
unique_macros = set()
unique_stocks = set()
for pair in CORRELATION_PAIRS:
    unique_macros.add(pair["left_macro"])
    if "right_macro" in pair:
        unique_macros.add(pair["right_macro"])
    if "right_stock" in pair:
        unique_stocks.add(pair["right_stock"])

for m in unique_macros:
    df_m = load_macro(m)
    if lookback_days is not None:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=lookback_days)
        df_m = df_m[df_m["date"] >= cutoff]
    all_series[m] = df_m

for s in unique_stocks:
    df_s = load_price(s)
    if lookback_days is not None:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=lookback_days)
        df_s = df_s[df_s["date"] >= cutoff]
    all_series[s] = df_s

for pair in CORRELATION_PAIRS:
    left_name = pair["left_macro"]
    if "right_stock" in pair:
        right_name = f"台積電 ({pair['right_stock']})"
        df_l = all_series.get(left_name, pd.DataFrame())
        df_r = all_series.get(pair["right_stock"], pd.DataFrame())
        right_col = "close"
    else:
        right_name = pair.get("right_macro", "")
        df_l = all_series.get(left_name, pd.DataFrame())
        df_r = all_series.get(right_name, pd.DataFrame())
        right_col = "value"

    if df_l.empty or df_r.empty:
        continue

    merged = merge_on_date(df_l, "value", df_r, right_col)
    if len(merged) < 3:
        continue

    r, p = pearson_r(merged["left"], merged["right"])
    strength = "強" if abs(r) >= 0.7 else ("中" if abs(r) >= 0.4 else "弱")
    direction = "正" if r > 0 else "負"
    sig = "✅ 顯著" if p < 0.05 else "❌ 不顯著"

    summary_rows.append({
        "配對": f"{left_name} vs {right_name}",
        "相關係數 (r)": f"{r:.4f}",
        "相關強度": strength,
        "方向": direction,
        "顯著性 (p<0.05)": sig,
        "樣本數": len(merged),
    })

if summary_rows:
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ 資料不足，無法計算相關係數。")

# Footer
st.markdown("---")
st.caption("資料來源: macro_indicators / prices 表 ｜ 相關係數: Pearson r ｜ 資料以共同交易日對齊")
