"""
股票追蹤與決策輔助系統 V1.1 - 投行觀點頁
Stock Tracking & Decision Support System V1.1 - Analyst Views Page

投行研究報告觀點頁面
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from modules.database import get_enabled_stocks
from modules.analyst_views import get_analyst_views_manager

# 設定頁面配置
st.set_page_config(
    page_title="投行觀點 - 股票追蹤系統",
    page_icon="🏦",
    layout="wide"
)

from modules.ui import apply_style
apply_style()
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)


def clean_text(value, fallback="N/A"):
    if value is None or pd.isna(value):
        return fallback
    text = str(value).strip()
    return text if text else fallback


def money_text(value):
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"NT$ {float(value):,.0f}"
    except (TypeError, ValueError):
        return "N/A"


def stock_label(stock_id, name):
    return f"{stock_id} {clean_text(name, '')}".strip()


def set_selected_stock(stock_id):
    st.session_state["analyst_selected_stock_id"] = stock_id

# 頁面標題
st.title("🏦 投行觀點")
st.markdown("投行研究報告觀點")
st.markdown("---")

# 取得自選股清單
try:
    stocks = get_enabled_stocks()

    if stocks.empty:
        st.warning("⚠️ 沒有自選股資料，請先執行 `python scripts/init_db.py`")
    else:
        # 初始化管理器
        analyst_manager = get_analyst_views_manager()

        # 股票選擇器。用按鈕直接寫入股票代號，避免瀏覽器翻譯或舊 selectbox 狀態造成錯配。
        stock_ids = [str(row['stock_id']) for _, row in stocks.iterrows()]
        if "analyst_selected_stock_id" not in st.session_state:
            st.session_state["analyst_selected_stock_id"] = stock_ids[0]
        if st.session_state["analyst_selected_stock_id"] not in stock_ids:
            st.session_state["analyst_selected_stock_id"] = stock_ids[0]

        st.markdown("**選擇股票**")
        stock_cols = st.columns(min(len(stock_ids), 4))
        for idx, (_, row) in enumerate(stocks.iterrows()):
            stock_id = str(row['stock_id'])
            label = stock_label(stock_id, row['name'])
            button_type = "primary" if stock_id == st.session_state["analyst_selected_stock_id"] else "secondary"
            stock_cols[idx % len(stock_cols)].button(
                label,
                key=f"analyst_stock_button_{stock_id}",
                type=button_type,
                on_click=set_selected_stock,
                args=(stock_id,),
                use_container_width=True,
            )

        selected_stock_id = st.session_state["analyst_selected_stock_id"]
        selected_stock_name = clean_text(
            stocks.loc[stocks['stock_id'].astype(str) == selected_stock_id, 'name'].iloc[0],
            ""
        )
        st.markdown(
            f'<div translate="no" class="notranslate" '
            f'style="color:#6b7280;font-size:0.95rem;margin:0.5rem 0 1rem;">'
            f'目前查詢股票：{stock_label(selected_stock_id, selected_stock_name)}</div>',
            unsafe_allow_html=True,
        )

        # 取得投行觀點
        analyst_views = analyst_manager.get_analyst_views(selected_stock_id, limit=10)

        if not analyst_views.empty:
            st.subheader(f"📊 {selected_stock_id} 投行觀點")

            # 顯示共識評級
            consensus = analyst_manager.get_consensus_rating(selected_stock_id)

            if consensus['has_consensus']:
                st.subheader("📊 共識評級")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("報告數量", consensus['total_reports'])
                with col2:
                    st.metric("平均目標價", money_text(consensus.get('avg_target_price')))
                with col3:
                    st.metric("最低目標價", money_text(consensus.get('min_target_price')))
                with col4:
                    st.metric("最高目標價", money_text(consensus.get('max_target_price')))

                # 顯示評級分佈
                st.subheader("📈 評級分佈")
                rating_distribution = consensus.get('rating_distribution', {})

                if rating_distribution:
                    # 建立評級分佈圖
                    fig = go.Figure(data=[go.Pie(
                        labels=list(rating_distribution.keys()),
                        values=list(rating_distribution.values()),
                        hole=.3
                    )])
                    fig.update_layout(title="投行評級分佈")
                    st.plotly_chart(fig, use_container_width=True)

                    # 顯示評級統計
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("評級統計")
                        for rating, count in rating_distribution.items():
                            st.write(f"**{rating}**: {count} 家")
                    with col2:
                        st.subheader("評級比例")
                        total = sum(rating_distribution.values())
                        for rating, count in rating_distribution.items():
                            percentage = (count / total) * 100
                            st.write(f"**{rating}**: {percentage:.1f}%")

            # 顯示最新投行觀點
            st.subheader("📋 最新投行觀點")
            latest = analyst_manager.get_latest_analyst_view(selected_stock_id)

            if latest:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("投行", clean_text(latest.get('analyst_firm')))
                with col2:
                    st.metric("分析師", clean_text(latest.get('analyst_name')))
                with col3:
                    rating = clean_text(latest.get('rating'))
                    if '買進' in rating:
                        st.success(f"投行原始評等: {rating}")
                    elif '賣出' in rating:
                        st.error(f"投行原始評等: {rating}")
                    else:
                        st.info(f"投行原始評等: {rating}")
                with col4:
                    st.metric("目標價", money_text(latest.get('target_price')))

                # 顯示詳細資訊
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 關鍵發現", "💪 優勢", "⚠️ 弱點", "📝 報告摘要"
                ])

                with tab1:
                    st.subheader("📊 關鍵發現")
                    st.write(latest.get('key_findings', 'N/A'))

                with tab2:
                    st.subheader("💪 優勢")
                    st.write(latest.get('strengths', 'N/A'))

                with tab3:
                    st.subheader("⚠️ 弱點")
                    st.write(latest.get('weaknesses', 'N/A'))

                with tab4:
                    st.subheader("📝 報告摘要")
                    st.write(latest.get('report_summary', 'N/A'))

            # 顯示目標價趨勢
            st.subheader("📈 目標價趨勢")
            target_trend = analyst_manager.get_target_price_trend(selected_stock_id, periods=8)

            if not target_trend.empty:
                target_trend = target_trend.dropna(subset=['target_price'])

            if not target_trend.empty:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=target_trend['report_date'],
                    y=target_trend['target_price'],
                    mode='lines+markers',
                    name='目標價',
                    line=dict(width=2),
                    marker=dict(size=8)
                ))

                if 'previous_target' in target_trend.columns and target_trend['previous_target'].notna().any():
                    fig.add_trace(go.Scatter(
                        x=target_trend['report_date'],
                        y=target_trend['previous_target'],
                        mode='lines+markers',
                        name='前次目標價',
                        line=dict(width=2, dash='dash'),
                        marker=dict(size=8)
                    ))

                fig.update_layout(
                    title=f"{selected_stock_id} 目標價趨勢",
                    xaxis_title="日期",
                    yaxis_title="目標價 (NT$)",
                    hovermode='x unified',
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ 尚無可繪製的目標價資料")

            # 顯示投行觀點摘要
            st.subheader("📊 投行觀點摘要")
            conclusion = analyst_manager.get_research_conclusion_summary(selected_stock_id)

            if conclusion['has_conclusion']:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("投行", clean_text(conclusion.get('analyst_firm')))
                with col2:
                    st.metric("分析師", clean_text(conclusion.get('analyst_name')))
                with col3:
                    st.metric("評級", clean_text(conclusion.get('rating')))
                with col4:
                    st.metric("目標價", money_text(conclusion.get('target_price')))

                # 顯示研究結論
                st.subheader("🎯 研究結論")
                conclusion_text = conclusion.get('conclusion', 'N/A')
                if '成立' in conclusion_text:
                    st.success(conclusion_text)
                elif '轉弱' in conclusion_text:
                    st.error(conclusion_text)
                elif '待確認' in conclusion_text:
                    st.warning(conclusion_text)
                else:
                    st.info(conclusion_text)

            # 顯示分析師覆蓋範圍
            st.subheader("👥 分析師覆蓋範圍")
            coverage = analyst_manager.get_analyst_coverage(selected_stock_id)

            if not coverage.empty:
                st.dataframe(
                    coverage,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'analyst_firm': st.column_config.TextColumn('投行'),
                        'analyst_name': st.column_config.TextColumn('分析師'),
                        'report_count': st.column_config.NumberColumn('報告數量'),
                        'first_report': st.column_config.TextColumn('首次報告'),
                        'latest_report': st.column_config.TextColumn('最新報告'),
                        'avg_target_price': st.column_config.NumberColumn('平均目標價', format="NT$ %d")
                    }
                )

            # 顯示歷史紀錄
            st.subheader("📅 歷史紀錄")
            st.dataframe(
                analyst_views[['report_date', 'analyst_firm', 'analyst_name', 'rating', 'target_price', 'recommendation', 'source', 'source_type', 'data_as_of']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'report_date': st.column_config.TextColumn('日期'),
                    'analyst_firm': st.column_config.TextColumn('投行'),
                    'analyst_name': st.column_config.TextColumn('分析師'),
                    'rating': st.column_config.TextColumn('評級'),
                    'target_price': st.column_config.NumberColumn('目標價', format="NT$ %d"),
                    'recommendation': st.column_config.TextColumn('投行原文觀點'),
                    'source': st.column_config.TextColumn('來源'),
                    'source_type': st.column_config.TextColumn('資料類型'),
                    'data_as_of': st.column_config.TextColumn('資料日期')
                }
            )

        else:
            st.warning(f"⚠️ {selected_stock_id} 尚無投行觀點")

        # 搜尋功能
        st.markdown("---")
        st.subheader("🔍 搜尋投行觀點")

        search_keyword = st.text_input("輸入搜尋關鍵字", placeholder="例如: AI、成長、技術")

        if search_keyword:
            search_results = analyst_manager.search_analyst_views(search_keyword)

            if not search_results.empty:
                st.subheader(f"搜尋結果: {len(search_results)} 筆")
                st.dataframe(
                    search_results[['stock_id', 'stock_name', 'report_date', 'analyst_firm', 'rating', 'target_price']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"ℹ️ 沒有找到包含「{search_keyword}」的投行觀點")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")
    st.exception(e)

# 側邊欄
with st.sidebar:
    st.header("🏦 投行觀點")
    st.markdown("""
    本頁面顯示投行研究報告觀點，包括：

    - 共識評級
    - 目標價趨勢
    - 分析師覆蓋範圍
    - 研究結論
    - 歷史紀錄
    """)

    st.markdown("---")
    st.markdown("### 📊 評級說明")
    st.markdown("""
    - **投行原始評等**：買進（預期股價將上漲）
    - **投行原始評等**：持有（預期股價將持平）
    - **投行原始評等**：賣出（預期股價將下跌）
    - **投行原始評等**：強力買進（強烈預期股價將上漲）
    - **投行原始評等**：中立（對股價無明確看法）
    """)

    st.markdown("---")
    st.markdown("### ⚙️ 免責聲明")
    st.markdown("""
    本系統僅供學習與研究用途，不構成任何投資建議。
    投行觀點僅供參考，投資有風險，請謹慎評估。
    """)

# 頁面底部
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>投行觀點 | 僅供學習研究使用</p>
</div>
""", unsafe_allow_html=True)

# ---------- 記錄管理（新增 / 刪除） ----------
from modules.research_forms import render_analyst_view_forms
render_analyst_view_forms()
