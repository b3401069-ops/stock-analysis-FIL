"""
股票追蹤與決策輔助系統 V1.1 - 財報與電話會議頁
Stock Tracking & Decision Support System V1.1 - Earnings Calls Page

每季財報與電話會議紀錄頁面
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from modules.database import get_enabled_stocks
from modules.earnings_call import get_earnings_call_manager

# 設定頁面配置
st.set_page_config(
    page_title="財報與電話會議 - 股票追蹤系統",
    page_icon="📞",
    layout="wide"
)

from modules.ui import apply_style
apply_style()

# 頁面標題
st.title("📞 財報與電話會議")
st.markdown("每季財報與電話會議紀錄")
st.markdown("---")

# 取得自選股清單
try:
    stocks = get_enabled_stocks()

    if stocks.empty:
        st.warning("⚠️ 沒有自選股資料，請先執行 `python scripts/init_db.py`")
    else:
        # 初始化管理器
        earnings_manager = get_earnings_call_manager()

        # 股票選擇器
        stock_options = {f"{row['stock_id']} {row['name']}": row['stock_id'] for _, row in stocks.iterrows()}
        selected_stock_label = st.selectbox(
            "選擇股票",
            options=list(stock_options.keys()),
            index=0
        )
        selected_stock_id = stock_options[selected_stock_label]

        # 取得電話會議紀錄
        earnings_calls = earnings_manager.get_earnings_calls(selected_stock_id, limit=10)

        if not earnings_calls.empty:
            st.subheader(f"📊 {selected_stock_id} 電話會議紀錄")

            # 顯示最新電話會議
            latest = earnings_manager.get_latest_earnings_call(selected_stock_id)
            if latest:
                st.subheader("📞 最新電話會議")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("日期", latest.get('call_date', 'N/A'))
                with col2:
                    st.metric("季度", latest.get('quarter', 'N/A'))
                with col3:
                    st.metric("年度", latest.get('fiscal_year', 'N/A'))
                with col4:
                    sentiment = latest.get('sentiment', 'N/A')
                    if '正面' in sentiment:
                        st.success(f"情緒: {sentiment}")
                    elif '負面' in sentiment:
                        st.error(f"情緒: {sentiment}")
                    else:
                        st.info(f"情緒: {sentiment}")

                # 顯示詳細資訊
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📋 管理層指引", "📊 關鍵重點", "🔮 展望", "📝 摘要"
                ])

                with tab1:
                    st.subheader("📋 管理層指引")
                    st.write(f"**營收指引：** {latest.get('revenue_guidance', 'N/A')}")
                    st.write(f"**獲利指引：** {latest.get('earnings_guidance', 'N/A')}")
                    st.write(f"**毛利率指引：** {latest.get('margin_guidance', 'N/A')}")
                    st.write(f"**資本支出指引：** {latest.get('capex_guidance', 'N/A')}")

                with tab2:
                    st.subheader("📊 關鍵重點")
                    st.write(latest.get('key_highlights', 'N/A'))

                with tab3:
                    st.subheader("🔮 展望")
                    st.write(latest.get('outlook_summary', 'N/A'))

                with tab4:
                    st.subheader("📝 會議摘要")
                    st.write(latest.get('transcript_summary', 'N/A'))

                st.markdown("---")

            # 顯示情緒趨勢
            st.subheader("📈 情緒趨勢")
            sentiment_trend = earnings_manager.get_sentiment_trend(selected_stock_id, periods=6)

            if not sentiment_trend.empty:
                # 統計情緒分佈
                sentiment_counts = earnings_calls['sentiment'].value_counts()

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("情緒分佈")
                    fig = go.Figure(data=[go.Pie(
                        labels=sentiment_counts.index,
                        values=sentiment_counts.values,
                        hole=.3
                    )])
                    fig.update_layout(title="電話會議情緒分佈")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("情緒統計")
                    for sentiment, count in sentiment_counts.items():
                        st.write(f"**{sentiment}**: {count} 次")

            # 顯示歷史紀錄
            st.subheader("📅 歷史紀錄")
            st.dataframe(
                earnings_calls[['call_date', 'quarter', 'fiscal_year', 'sentiment', 'outlook_summary']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'call_date': st.column_config.TextColumn('日期'),
                    'quarter': st.column_config.TextColumn('季度'),
                    'fiscal_year': st.column_config.TextColumn('年度'),
                    'sentiment': st.column_config.TextColumn('情緒'),
                    'outlook_summary': st.column_config.TextColumn('展望')
                }
            )

            # 顯示指引摘要
            st.subheader("📊 指引摘要")
            guidance_summary = earnings_manager.get_guidance_summary(selected_stock_id)

            if guidance_summary['has_guidance']:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("日期", guidance_summary.get('call_date', 'N/A'))
                with col2:
                    st.metric("季度", guidance_summary.get('quarter', 'N/A'))
                with col3:
                    st.metric("情緒", guidance_summary.get('sentiment', 'N/A'))
                with col4:
                    st.metric("營收指引", guidance_summary.get('revenue_guidance', 'N/A')[:20] + "...")
            else:
                st.info("ℹ️ 尚無指引資料")

        else:
            st.warning(f"⚠️ {selected_stock_id} 尚無電話會議紀錄")

        # 搜尋功能
        st.markdown("---")
        st.subheader("🔍 搜尋電話會議")

        search_keyword = st.text_input("輸入搜尋關鍵字", placeholder="例如: AI、營收、成長")

        if search_keyword:
            search_results = earnings_manager.search_earnings_calls(search_keyword)

            if not search_results.empty:
                st.subheader(f"搜尋結果: {len(search_results)} 筆")
                st.dataframe(
                    search_results[['stock_id', 'stock_name', 'call_date', 'quarter', 'key_highlights']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"ℹ️ 沒有找到包含「{search_keyword}」的電話會議紀錄")

        # 電話會議日曆
        st.markdown("---")
        st.subheader("📅 電話會議日曆")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日期", value=datetime.now().date())
        with col2:
            end_date = st.date_input("結束日期", value=datetime.now().date())

        if start_date and end_date:
            calendar = earnings_manager.get_earnings_calendar(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            if not calendar.empty:
                st.dataframe(
                    calendar,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("ℹ️ 所選日期範圍內沒有電話會議")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")
    st.exception(e)

# 側邊欄
with st.sidebar:
    st.header("📞 財報與電話會議")
    st.markdown("""
    本頁面顯示每季財報與電話會議紀錄，包括：

    - 管理層指引
    - 關鍵重點
    - 展望摘要
    - 情緒分析
    - 歷史紀錄
    """)

    st.markdown("---")
    st.markdown("### 📊 情緒說明")
    st.markdown("""
    - **正面**：管理層對前景樂觀
    - **中性**：管理層對前景持中性態度
    - **負面**：管理層對前景較為保守
    - **中性偏正**：略為樂觀
    - **中性偏負**：略為保守
    """)

    st.markdown("---")
    st.markdown("### ⚙️ 免責聲明")
    st.markdown("""
    本系統僅供學習與研究用途，不構成任何投資建議。
    電話會議內容僅供參考，投資有風險，請謹慎評估。
    """)

# 頁面底部
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>財報與電話會議 | 僅供學習研究使用</p>
</div>
""", unsafe_allow_html=True)

# ---------- 記錄管理（新增 / 刪除） ----------
from modules.research_forms import render_earnings_call_forms
render_earnings_call_forms()
