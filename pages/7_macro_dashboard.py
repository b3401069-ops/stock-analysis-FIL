"""
股票追蹤與決策輔助系統 V1.1 - 宏觀 Dashboard 頁
Stock Tracking & Decision Support System V1.1 - Macro Dashboard Page

總體經濟資料視覺化儀表板
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from modules.macro_analysis import get_macro_analysis_manager

# 設定頁面配置
st.set_page_config(
    page_title="宏觀 Dashboard - 股票追蹤系統",
    page_icon="🌐",
    layout="wide"
)

from modules.ui import apply_style
apply_style()
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def clean_text(value):
    """Return a display-safe string for optional text fields."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


REGION_LABELS = {
    'TW': 'TW 台灣',
    'US': 'US 美國',
    'EU': 'EU 歐盟',
    'JP': 'JP 日本',
}

REGION_ORDER = ['TW', 'US', 'EU', 'JP']

# Yahoo Finance index indicators stored in the macro_indicators table
MARKET_PULSE_INDICATORS = [
    'S&P 500',
    'NASDAQ',
    '費城半導體指數',
    'TAIEX',
    'VIX',
]

# Mapping for display labels in Market Pulse
MARKET_PULSE_LABELS = {
    'S&P 500': 'S&P 500',
    'NASDAQ': 'NASDAQ',
    '費城半導體指數': 'SOX 半導體',
    'TAIEX': 'TAIEX 加權',
    'VIX': 'VIX 恐慌',
}

# Pairs for TW vs US comparison charts
TW_US_COMPARISON_PAIRS = [
    ('台灣CPI', '美國CPI', 'CPI 消費者物價指數 (TW vs US)'),
    ('台灣GDP', '美國GDP', 'GDP 經濟成長率 (TW vs US)'),
    ('台灣失業率', '美國失業率', '失業率 (TW vs US)'),
    ('台灣PMI', '美國PMI', 'PMI 採購經理人指數 (TW vs US)' if False else None),  # placeholder
]
# Filter out None entries
TW_US_COMPARISON_PAIRS = [(tw, us, label) for tw, us, label in TW_US_COMPARISON_PAIRS if label]


def region_label(region):
    """Display stable region names while keeping code values for queries."""
    region = clean_text(region)
    return REGION_LABELS.get(region, region)


def no_translate(text):
    """Render text without browser auto-translation changing region codes."""
    return f'<span translate="no" class="notranslate">{text}</span>'


def region_code(label):
    """Convert a displayed region label back to its database code."""
    for code, display_label in REGION_LABELS.items():
        if label == display_label:
            return code
    return label


def sort_regions(regions):
    return sorted(
        regions,
        key=lambda region: (
            REGION_ORDER.index(region) if region in REGION_ORDER else len(REGION_ORDER),
            region_label(region),
        )
    )


def set_region(region):
    st.session_state["macro_selected_region_code"] = region


def _color_for_change(change_val):
    """Return hex colour for a numeric change (台股慣例: red=up, green=down)."""
    if change_val is None:
        return "#6b7280"
    try:
        v = float(change_val)
    except (TypeError, ValueError):
        return "#6b7280"
    if v > 0:
        return "#D64545"   # red – up
    elif v < 0:
        return "#12876F"   # green – down
    return "#6b7280"


def _arrow_for_change(change_val):
    """Return an arrow character based on the direction of change."""
    if change_val is None:
        return ""
    try:
        v = float(change_val)
    except (TypeError, ValueError):
        return ""
    if v > 0:
        return "▲"
    elif v < 0:
        return "▼"
    return "—"


# ---------------------------------------------------------------------------
# Page Title
# ---------------------------------------------------------------------------
st.title("🌐 宏觀 Dashboard")
st.markdown("總體經濟資料視覺化儀表板")
st.markdown("---")

# 初始化管理器
macro_manager = get_macro_analysis_manager()

try:
    # ========================================================================
    # SECTION 1 — Market Pulse (Yahoo Finance indices)
    # ========================================================================
    st.subheader("⚡ Market Pulse — 即時市場指數")

    pulse_records = []
    for ind_name in MARKET_PULSE_INDICATORS:
        df_ind = macro_manager.get_macro_indicators(
            indicator_name=ind_name, limit=30
        )
        if df_ind.empty:
            continue
        latest = df_ind.sort_values('indicator_date', ascending=False).iloc[0]
        pulse_records.append({
            'name': ind_name,
            'label': MARKET_PULSE_LABELS.get(ind_name, ind_name),
            'value': latest.get('value'),
            'change': latest.get('change'),
            'trend': clean_text(latest.get('trend', '')),
            'date': latest.get('indicator_date', 'N/A'),
            'unit': clean_text(latest.get('unit', '')),
        })

    if pulse_records:
        pulse_cols = st.columns(len(pulse_records))
        for idx, rec in enumerate(pulse_records):
            with pulse_cols[idx]:
                val_str = f"{rec['value']:,.2f}" if rec['value'] is not None else "N/A"
                change = rec['change']
                chg_color = _color_for_change(change)
                arrow = _arrow_for_change(change)
                if change is not None:
                    chg_str = f"{arrow} {change:+.2f}"
                else:
                    chg_str = "—"

                st.markdown(
                    f"""
                    <div style="
                        background:#fff;
                        border:1px solid #E6E8EF;
                        border-left:4px solid {chg_color};
                        border-radius:12px;
                        padding:16px 18px;
                        text-align:center;
                        box-shadow:0 1px 3px rgba(16,24,40,0.06);
                        min-height:120px;">
                        <div style="font-size:0.85rem;color:#667085;font-weight:600;">
                            {rec['label']}
                        </div>
                        <div style="font-size:1.6rem;font-weight:700;margin:6px 0 2px;">
                            {val_str} <span style="font-size:0.8rem;color:#667085;">{rec['unit']}</span>
                        </div>
                        <div style="font-size:1rem;font-weight:700;color:{chg_color};">
                            {chg_str}
                        </div>
                        <div style="font-size:0.75rem;color:#98A2B3;margin-top:4px;">
                            {rec['date']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("ℹ️ 尚無 Yahoo Finance 市場指數資料")

    st.markdown("---")

    # ========================================================================
    # SECTION 2 — Original region-based dashboard (preserved)
    # ========================================================================

    # 取得可用區域
    regions = sort_regions(macro_manager.get_available_regions())
    region_options = [region_label(region) for region in regions]

    if not regions:
        st.warning("⚠️ 沒有總體經濟資料，請先執行 V1.1 資料匯入")
    else:
        if "macro_selected_region_code" not in st.session_state:
            st.session_state["macro_selected_region_code"] = regions[0]

        active_region = st.session_state["macro_selected_region_code"]
        if active_region not in regions:
            active_region = regions[0]
            st.session_state["macro_selected_region_code"] = active_region

        # 區域切換。使用按鈕寫入區域代碼，避免瀏覽器翻譯或舊 selectbox 狀態造成錯配。
        st.markdown("**選擇區域**")
        region_cols = st.columns(len(regions))
        for idx, region in enumerate(regions):
            button_type = "primary" if region == active_region else "secondary"
            region_cols[idx].button(
                region_label(region),
                key=f"macro_region_button_{region}",
                type=button_type,
                on_click=set_region,
                args=(region,),
                use_container_width=True,
            )

        selected_region = st.session_state["macro_selected_region_code"]
        selected_region_label = region_label(selected_region)
        st.markdown(
            f'<div translate="no" class="notranslate" '
            f'style="color:#6b7280;font-size:0.95rem;margin:0.5rem 0 1rem;">'
            f'目前查詢區域：{selected_region_label}</div>',
            unsafe_allow_html=True,
        )

        # 取得宏觀 Dashboard 資料
        dashboard_data = macro_manager.get_macro_dashboard_data(selected_region)

        if dashboard_data['has_data']:
            data_region = dashboard_data.get('region', selected_region)
            data_region_label = region_label(data_region)
            st.markdown(
                f'<h2 translate="no" class="notranslate" '
                f'style="font-size:2rem;line-height:1.25;margin:1rem 0 0.5rem;">'
                f'📊 {data_region_label} 總體經濟指標</h2>',
                unsafe_allow_html=True,
            )

            # 顯示更新時間
            st.caption(f"資料更新時間: {dashboard_data.get('update_date', 'N/A')}")

            # 顯示各類別指標
            categories = dashboard_data.get('categories', {})

            for category, indicators in categories.items():
                st.markdown(f"### 📈 {category}")

                # 建立指標卡片
                cols = st.columns(min(len(indicators), 4))
                for idx, indicator in enumerate(indicators):
                    with cols[idx % 4]:
                        # 計算變化百分比
                        change = indicator.get('change')
                        if change is not None:
                            if change > 0:
                                delta_color = "normal"
                                delta_text = f"+{change:.2f}"
                            elif change < 0:
                                delta_color = "inverse"
                                delta_text = f"{change:.2f}"
                            else:
                                delta_color = "off"
                                delta_text = "0.00"
                        else:
                            delta_color = "off"
                            delta_text = "N/A"

                        st.metric(
                            label=indicator['name'],
                            value=f"{indicator['value']:.2f} {indicator.get('unit', '')}",
                            delta=delta_text,
                            delta_color=delta_color
                        )

                        # 顯示趨勢
                        trend = clean_text(indicator.get('trend', ''))
                        if trend:
                            if '上升' in trend or '改善' in trend:
                                st.success(f"趨勢: {trend}")
                            elif '下降' in trend or '惡化' in trend:
                                st.error(f"趨勢: {trend}")
                            else:
                                st.info(f"趨勢: {trend}")

                st.markdown("---")

            # ----------------------------------------------------------------
            # SECTION 3 — Time-series trend charts (last 30 data points each)
            # ----------------------------------------------------------------
            st.subheader("📈 指標趨勢圖 (近 30 筆資料)")
            indicators = macro_manager.get_available_indicators(selected_region)

            if indicators:
                selected_indicator = st.selectbox(
                    "選擇指標",
                    options=indicators,
                    index=0,
                    key=f"macro_indicator_{selected_region}_v4"
                )

                trend_data = macro_manager.get_indicator_trend(
                    selected_indicator, selected_region, periods=30
                )

                if not trend_data.empty:
                    fig = go.Figure()

                    # Fill-area line chart
                    fig.add_trace(go.Scatter(
                        x=trend_data['indicator_date'],
                        y=trend_data['value'],
                        mode='lines+markers',
                        name=selected_indicator,
                        line=dict(width=2.5, color='#4F46E5'),
                        marker=dict(size=6, color='#4F46E5'),
                        fill='tozeroy',
                        fillcolor='rgba(79,70,229,0.08)',
                        hovertemplate='%{x}<br>數值: %{y:.2f}<extra></extra>',
                    ))

                    fig.update_layout(
                        title=f"{selected_indicator} 趨勢圖 ({selected_region_label})",
                        xaxis_title="日期",
                        yaxis_title="數值",
                        hovermode='x unified',
                        showlegend=False,
                        margin=dict(l=40, r=20, t=60, b=40),
                        height=420,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(gridcolor='#E6E8EF'),
                        yaxis=dict(gridcolor='#E6E8EF'),
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"ℹ️ {selected_indicator} 趨勢資料不足")
            else:
                st.info("ℹ️ 目前無可用指標")

            # ----------------------------------------------------------------
            # SECTION 4 — TW vs US indicator comparison overlay charts
            # ----------------------------------------------------------------
            st.markdown("---")
            st.subheader("🔀 台灣 vs 美國 指標比較")

            # Dynamically discover which pairs have data for both TW and US
            all_indicators_all_regions = macro_manager.get_available_indicators()
            available_pairs = []
            for tw_name, us_name, pair_label in TW_US_COMPARISON_PAIRS:
                if tw_name in all_indicators_all_regions and us_name in all_indicators_all_regions:
                    available_pairs.append((tw_name, us_name, pair_label))

            # Also let the user pick a custom pair
            tw_indicators = [i for i in all_indicators_all_regions
                             if macro_manager.get_macro_indicators(i, 'TW', limit=1).shape[0] > 0]
            us_indicators = [i for i in all_indicators_all_regions
                             if macro_manager.get_macro_indicators(i, 'US', limit=1).shape[0] > 0]

            st.markdown("#### 預設比較組合")
            if available_pairs:
                selected_pair_label = st.radio(
                    "選擇比較項目",
                    options=[p[2] for p in available_pairs],
                    key="tw_us_pair_radio",
                    horizontal=True,
                )
                chosen = next(p for p in available_pairs if p[2] == selected_pair_label)
                tw_name, us_name, _ = chosen

                tw_df = macro_manager.get_indicator_trend(tw_name, 'TW', periods=30)
                us_df = macro_manager.get_indicator_trend(us_name, 'US', periods=30)

                fig_cmp = go.Figure()
                if not tw_df.empty:
                    fig_cmp.add_trace(go.Scatter(
                        x=tw_df['indicator_date'], y=tw_df['value'],
                        mode='lines+markers', name=f'TW {tw_name}',
                        line=dict(width=2.5, color='#D64545'),
                        marker=dict(size=5),
                        hovertemplate='%{x}<br>TW: %{y:.2f}<extra></extra>',
                    ))
                if not us_df.empty:
                    fig_cmp.add_trace(go.Scatter(
                        x=us_df['indicator_date'], y=us_df['value'],
                        mode='lines+markers', name=f'US {us_name}',
                        line=dict(width=2.5, color='#4F46E5'),
                        marker=dict(size=5),
                        hovertemplate='%{x}<br>US: %{y:.2f}<extra></extra>',
                    ))

                fig_cmp.update_layout(
                    title=selected_pair_label,
                    xaxis_title="日期",
                    yaxis_title="數值",
                    hovermode='x unified',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    margin=dict(l=40, r=20, t=60, b=40),
                    height=420,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='#E6E8EF'),
                    yaxis=dict(gridcolor='#E6E8EF'),
                )
                st.plotly_chart(fig_cmp, use_container_width=True)
            else:
                st.info("ℹ️ 暫無可用的 TW vs US 預設比較組合")

            # Custom comparison
            st.markdown("#### 自訂比較")
            cust_cols = st.columns(2)
            with cust_cols[0]:
                cust_tw = st.selectbox(
                    "台灣指標", options=tw_indicators or ["(無資料)"],
                    key="cust_tw_sel",
                )
            with cust_cols[1]:
                cust_us = st.selectbox(
                    "美國指標", options=us_indicators or ["(無資料)"],
                    key="cust_us_sel",
                )

            if st.button("繪製自訂比較圖", key="btn_custom_compare"):
                cust_tw_df = macro_manager.get_indicator_trend(cust_tw, 'TW', periods=30)
                cust_us_df = macro_manager.get_indicator_trend(cust_us, 'US', periods=30)

                fig_cust = go.Figure()
                if not cust_tw_df.empty:
                    fig_cust.add_trace(go.Scatter(
                        x=cust_tw_df['indicator_date'], y=cust_tw_df['value'],
                        mode='lines+markers', name=f'TW {cust_tw}',
                        line=dict(width=2.5, color='#D64545'),
                        marker=dict(size=5),
                    ))
                if not cust_us_df.empty:
                    fig_cust.add_trace(go.Scatter(
                        x=cust_us_df['indicator_date'], y=cust_us_df['value'],
                        mode='lines+markers', name=f'US {cust_us}',
                        line=dict(width=2.5, color='#4F46E5'),
                        marker=dict(size=5),
                    ))

                fig_cust.update_layout(
                    title=f'{cust_tw} (TW) vs {cust_us} (US)',
                    xaxis_title="日期",
                    yaxis_title="數值",
                    hovermode='x unified',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    margin=dict(l=40, r=20, t=60, b=40),
                    height=420,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='#E6E8EF'),
                    yaxis=dict(gridcolor='#E6E8EF'),
                )
                st.plotly_chart(fig_cust, use_container_width=True)

            # ---------------------------------------------------------------
            # Original analysis sections (preserved)
            # ---------------------------------------------------------------
            st.markdown("---")
            st.subheader("🔍 總體經濟環境分析")
            analysis = macro_manager.analyze_macro_environment(selected_region)

            if analysis['has_analysis']:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("整體評估", analysis['overall_assessment'])
                with col2:
                    st.metric("正面指標", analysis['positive_indicators'])
                with col3:
                    st.metric("負面指標", analysis['negative_indicators'])

                # 顯示關鍵指標
                st.subheader("📋 關鍵指標詳情")
                key_indicators = analysis.get('key_indicators', {})
                for name, data in key_indicators.items():
                    with st.expander(f"📊 {name}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**數值：** {data.get('value', 'N/A')}")
                            st.write(f"**變化：** {data.get('change', 'N/A')}")
                        with col2:
                            trend_text = clean_text(data.get('trend')) or 'N/A'
                            impact_text = clean_text(data.get('impact')) or 'N/A'
                            st.write(f"**趨勢：** {trend_text}")
                            st.write(f"**影響評估：** {impact_text}")
            else:
                st.info("ℹ️ 尚無總體經濟環境分析")

            # ----------------------------------------------------------------
            # Original trend chart (selectbox-driven, preserved)
            # ----------------------------------------------------------------
            st.markdown("---")
            st.subheader("📈 指標趨勢圖 (詳細)")
            indicators = macro_manager.get_available_indicators(selected_region)

            if indicators:
                selected_indicator_detail = st.selectbox(
                    "選擇指標",
                    options=indicators,
                    index=0,
                    key=f"macro_indicator_detail_{selected_region}_v4"
                )

                trend_data_detail = macro_manager.get_indicator_trend(
                    selected_indicator_detail, selected_region
                )

                if not trend_data_detail.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=trend_data_detail['indicator_date'],
                        y=trend_data_detail['value'],
                        mode='lines+markers',
                        name=selected_indicator_detail,
                        line=dict(width=2),
                        marker=dict(size=8)
                    ))

                    fig.update_layout(
                        title=f"{selected_indicator_detail} 趨勢圖 ({selected_region_label})",
                        xaxis_title="日期",
                        yaxis_title="數值",
                        hovermode='x unified',
                        showlegend=True
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"ℹ️ {selected_indicator_detail} 趨勢資料不足")

        else:
            st.warning(f"⚠️ {region_label(selected_region)} 尚無總體經濟資料")

        # ====================================================================
        # SECTION 5 — Regional comparison (original, preserved)
        # ====================================================================
        st.markdown("---")
        st.subheader("🌍 區域比較")

        if len(regions) > 1:
            default_comparison = [
                region_label(region) for region in regions
                if region in {selected_region, 'TW'}
            ][:2]
            if not default_comparison:
                default_comparison = region_options[:2]

            comparison_regions = st.multiselect(
                "選擇比較區域",
                options=region_options,
                default=default_comparison,
                key="macro_comparison_regions_v4"
            )

            comparison_region_codes = [region_code(region) for region in comparison_regions]

            if comparison_region_codes:
                comparison_indicators = macro_manager.get_common_indicators(comparison_region_codes)
                if comparison_indicators:
                    comparison_indicator = st.selectbox(
                        "選擇比較指標",
                        options=comparison_indicators,
                        index=0,
                        key=f"comparison_indicator_{selected_region}_v4"
                    )

                    comparison_data = macro_manager.get_regional_comparison(
                        comparison_indicator, comparison_region_codes
                    )

                    if not comparison_data.empty:
                        fig = go.Figure()

                        for _, row in comparison_data.iterrows():
                            row_region_label = region_label(row['region'])
                            fig.add_trace(go.Bar(
                                name=row_region_label,
                                x=[row_region_label],
                                y=[row['value']],
                                text=[f"{row['value']:.2f}"],
                                textposition='auto'
                            ))

                        fig.update_layout(
                            title=f"{comparison_indicator} 區域比較",
                            xaxis_title="區域",
                            yaxis_title="數值",
                            showlegend=True
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # 時間趨勢比較圖
                        st.subheader(f"📈 {comparison_indicator} 趨勢比較")
                        trend_fig = go.Figure()
                        for region_code in comparison_region_codes:
                            region_data = macro_manager.get_macro_indicators(
                                indicator_name=comparison_indicator,
                                region=region_code,
                                limit=30
                            )
                            if not region_data.empty:
                                region_data = region_data.sort_values('indicator_date')
                                trend_fig.add_trace(go.Scatter(
                                    x=region_data['indicator_date'],
                                    y=region_data['value'],
                                    mode='lines+markers',
                                    name=region_label(region_code),
                                    line=dict(width=2),
                                    marker=dict(size=5)
                                ))
                        trend_fig.update_layout(
                            title=f"{comparison_indicator} 趨勢比較（近 30 筆）",
                            xaxis_title="日期",
                            yaxis_title="數值",
                            hovermode='x unified',
                            showlegend=True
                        )
                        st.plotly_chart(trend_fig, use_container_width=True)

                        # 顯示比較表格
                        comparison_data['region'] = comparison_data['region'].map(region_label)
                        comparison_data['trend'] = comparison_data['trend'].map(
                            lambda value: clean_text(value) or 'N/A'
                        )
                        st.dataframe(
                            comparison_data[['region', 'value', 'unit', 'trend']],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info(f"ℹ️ {comparison_indicator} 在所選區域暫無資料")
                else:
                    st.warning("⚠️ 所選區域沒有共同的指標可供比較，請選擇其他區域")
        else:
            st.info("ℹ️ 需要至少兩個區域才能進行比較")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")
    st.exception(e)

# 側邊欄
with st.sidebar:
    st.header("🌐 宏觀 Dashboard")
    st.markdown("""
    本頁面顯示總體經濟資料視覺化儀表板，包括：

    - ⚡ Market Pulse 即時市場指數
    - 經濟成長指標
    - 物價指數
    - 利率政策
    - 就業市場
    - 貿易數據
    - 景氣指標
    - 金融市場
    - 📈 近 30 筆趨勢圖
    - 🔀 TW vs US 指標比較
    """)

    st.markdown("---")
    st.markdown("### 📊 指標說明")
    st.markdown("""
    - **GDP 成長率**：國內生產毛額成長率
    - **CPI**：消費者物價指數
    - **PMI**：採購經理人指數
    - **失業率**：勞動力市場指標
    - **利率**：中央銀行利率政策
    - **S&P 500 / NASDAQ / SOX / TAIEX / VIX**：Yahoo Finance 市場指數
    """)

    st.markdown("---")
    st.markdown("### ⚙️ 免責聲明")
    st.markdown("""
    本系統僅供學習與研究用途，不構成任何投資建議。
    宏觀資料僅供參考，不應直接作為買賣依據。
    """)

# 頁面底部
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>宏觀 Dashboard | 僅供學習研究使用</p>
</div>
""", unsafe_allow_html=True)
