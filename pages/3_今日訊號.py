"""
股票追蹤與決策輔助系統 V1 - 今日訊號頁
Stock Tracking & Decision Support System V1 - Today Signals Page
"""

import streamlit as st
import pandas as pd
from modules.database import get_latest_signals
from modules.signals import get_severity_icon

# 設定頁面配置
st.set_page_config(
    page_title="今日訊號 - 股票追蹤系統",
    page_icon="🚦",
    layout="wide"
)

from modules.ui import apply_style
apply_style()

st.title("🚦 今日訊號")
st.markdown("---")

try:
    signals = get_latest_signals()

    if signals.empty:
        st.info("ℹ️ 目前沒有訊號，請先執行 `python scripts/generate_signals.py`")
    else:
        signal_date = signals['date'].iloc[0]
        st.caption(f"訊號資料日：{signal_date}（以資料庫中最新價格日為準）")

        # 統計摘要
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("訊號總數", f"{len(signals)} 個")
        with col2:
            bullish = (signals['severity'] == '偏多').sum()
            st.metric("偏多訊號", f"{bullish} 個")
        with col3:
            bearish = (signals['severity'] == '偏空').sum()
            st.metric("偏空訊號", f"{bearish} 個")

        st.markdown("---")

        # 篩選器
        col1, col2 = st.columns(2)
        with col1:
            type_options = ['全部'] + sorted(signals['signal_type'].unique().tolist())
            selected_type = st.selectbox("訊號類型", type_options)
        with col2:
            severity_options = ['全部'] + sorted(signals['severity'].unique().tolist())
            selected_severity = st.selectbox("嚴重度", severity_options)

        filtered = signals
        if selected_type != '全部':
            filtered = filtered[filtered['signal_type'] == selected_type]
        if selected_severity != '全部':
            filtered = filtered[filtered['severity'] == selected_severity]

        # 訊號表格
        display = pd.DataFrame({
            '股票': filtered['stock_id'] + ' ' + filtered['name'],
            '類型': filtered['signal_type'],
            '訊號': filtered['signal_name'],
            '嚴重度': filtered['severity'].map(lambda s: f"{get_severity_icon(s)} {s}"),
            '說明': filtered['description']
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")

st.markdown("---")
st.caption("⚠️ 訊號僅供技術分析研究參考，不構成任何投資建議。")
