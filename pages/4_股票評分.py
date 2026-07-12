"""
股票追蹤與決策輔助系統 V1 - 股票評分頁
Stock Tracking & Decision Support System V1 - Stock Scores Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.database import get_scores

# 設定頁面配置
st.set_page_config(
    page_title="股票評分 - 股票追蹤系統",
    page_icon="⭐",
    layout="wide"
)

from modules.ui import apply_style
apply_style()

st.title("⭐ 股票評分")
st.markdown("---")

try:
    scores = get_scores()

    if scores.empty or scores['total_score'].isna().all():
        st.info("ℹ️ 目前沒有評分資料，請先執行 `python scripts/calculate_scores.py`")
    else:
        scores = scores.dropna(subset=['total_score'])
        st.caption(f"評分日期：{scores['date'].max()}")

        # 評分表格
        display = pd.DataFrame({
            '股票': scores['stock_id'] + ' ' + scores['name'],
            '技術面': scores['technical_score'].round(1),
            '基本面': scores['fundamental_score'].round(1),
            '風險': scores['risk_score'].round(1),
            '總分': scores['total_score'].round(1),
            '評級': scores['rating'],
            '說明': scores['description']
        }).sort_values('總分', ascending=False)
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.markdown("---")

        # 分數比較圖
        st.subheader("📊 評分比較")
        fig = go.Figure()
        labels = scores['stock_id'] + ' ' + scores['name']
        fig.add_trace(go.Bar(name='技術面', x=labels, y=scores['technical_score']))
        fig.add_trace(go.Bar(name='基本面', x=labels, y=scores['fundamental_score']))
        fig.add_trace(go.Bar(name='風險', x=labels, y=scores['risk_score']))
        fig.add_trace(go.Scatter(name='總分', x=labels, y=scores['total_score'],
                                 mode='markers+lines', marker=dict(size=10)))
        fig.update_layout(barmode='group', height=450, yaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")

st.markdown("---")
st.caption("⚠️ 評分為規則型計算結果，僅供研究參考，不構成任何投資建議。")
