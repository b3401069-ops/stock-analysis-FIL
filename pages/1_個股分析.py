"""
股票追蹤與決策輔助系統 V1 - 個股分析頁
Stock Tracking & Decision Support System V1 - Stock Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from modules.database import get_enabled_stocks, get_stock_prices, get_indicators, get_latest_fundamentals

# 設定頁面配置
st.set_page_config(
    page_title="個股分析 - 股票追蹤系統",
    page_icon="📊",
    layout="wide"
)

from modules.ui import apply_style
apply_style()

# 頁面標題
st.title("📊 個股分析")
st.markdown("---")

# 取得自選股清單
try:
    stocks = get_enabled_stocks()
    
    if stocks.empty:
        st.warning("⚠️ 沒有自選股資料，請先執行 `python scripts/init_db.py`")
    else:
        # 股票選擇器
        stock_options = {f"{row['stock_id']} {row['name']}": row['stock_id'] for _, row in stocks.iterrows()}
        selected_stock_label = st.selectbox(
            "選擇股票",
            options=list(stock_options.keys()),
            index=0
        )
        selected_stock_id = stock_options[selected_stock_label]
        
        # 取得股票資料
        stock_info = stocks[stocks['stock_id'] == selected_stock_id].iloc[0]
        prices = get_stock_prices(selected_stock_id, days=60)
        indicators = get_indicators(selected_stock_id, days=60)
        fundamentals = get_latest_fundamentals()
        
        # 顯示股票基本資訊
        st.subheader(f"📈 {stock_info['name']} ({stock_info['stock_id']})")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("市場", stock_info['market'])
        with col2:
            st.metric("產業", stock_info['industry'])
        with col3:
            if not prices.empty:
                latest_price = prices.iloc[-1]['close']
                st.metric("最新收盤價", f"NT$ {latest_price:,.2f}")
        with col4:
            if len(prices) >= 2:
                change = prices.iloc[-1]['close'] - prices.iloc[-2]['close']
                change_pct = (change / prices.iloc[-2]['close']) * 100
                st.metric("漲跌", f"{change:+.2f}", f"{change_pct:+.2f}%")
        
        st.markdown("---")
        
        # K線圖
        st.subheader("📉 K線圖")
        
        if not prices.empty:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3]
            )
            
            # K線
            fig.add_trace(
                go.Candlestick(
                    x=prices['date'],
                    open=prices['open'],
                    high=prices['high'],
                    low=prices['low'],
                    close=prices['close'],
                    name='K線'
                ),
                row=1, col=1
            )
            
            # 移動平均線
            if not indicators.empty:
                fig.add_trace(
                    go.Scatter(
                        x=indicators['date'],
                        y=indicators['ma5'],
                        name='MA5',
                        line=dict(color='orange', width=1)
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=indicators['date'],
                        y=indicators['ma20'],
                        name='MA20',
                        line=dict(color='blue', width=1)
                    ),
                    row=1, col=1
                )
            
            # 成交量
            colors = ['red' if prices.iloc[i]['close'] >= prices.iloc[i]['open'] else 'green' 
                      for i in range(len(prices))]
            
            fig.add_trace(
                go.Bar(
                    x=prices['date'],
                    y=prices['volume'],
                    name='成交量',
                    marker_color=colors
                ),
                row=2, col=1
            )
            
            # 成交量均線
            if not indicators.empty:
                fig.add_trace(
                    go.Scatter(
                        x=indicators['date'],
                        y=indicators['volume_ma20'],
                        name='Volume MA20',
                        line=dict(color='purple', width=1)
                    ),
                    row=2, col=1
                )
            
            fig.update_layout(
                height=600,
                xaxis_rangeslider_visible=False,
                showlegend=True,
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # 技術指標
        st.subheader("📊 技術指標")
        
        if not indicators.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # RSI 圖表
                fig_rsi = go.Figure()
                fig_rsi.add_trace(
                    go.Scatter(
                        x=indicators['date'],
                        y=indicators['rsi'],
                        name='RSI',
                        line=dict(color='blue', width=2)
                    )
                )
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超買")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超賣")
                fig_rsi.update_layout(
                    title="RSI 指標",
                    height=300,
                    yaxis_range=[0, 100]
                )
                st.plotly_chart(fig_rsi, use_container_width=True)
            
            with col2:
                # MACD 圖表
                fig_macd = go.Figure()
                fig_macd.add_trace(
                    go.Scatter(
                        x=indicators['date'],
                        y=indicators['macd'],
                        name='MACD',
                        line=dict(color='blue', width=2)
                    )
                )
                fig_macd.add_trace(
                    go.Scatter(
                        x=indicators['date'],
                        y=indicators['macd_signal'],
                        name='Signal',
                        line=dict(color='orange', width=2)
                    )
                )
                fig_macd.add_trace(
                    go.Bar(
                        x=indicators['date'],
                        y=indicators['macd_histogram'],
                        name='Histogram',
                        marker_color=['red' if val >= 0 else 'green' for val in indicators['macd_histogram']]
                    )
                )
                fig_macd.update_layout(title="MACD 指標", height=300)
                st.plotly_chart(fig_macd, use_container_width=True)
        
        st.markdown("---")
        
        # 基本面摘要
        st.subheader("📋 基本面摘要")
        
        fund_row = fundamentals[fundamentals['stock_id'] == selected_stock_id]
        
        if not fund_row.empty:
            fund = fund_row.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("PE Ratio", f"{fund['pe_ratio']:.1f}" if pd.notna(fund['pe_ratio']) else 'N/A')
                st.metric("殖利率", f"{fund['dividend_yield']:.1f}%" if pd.notna(fund['dividend_yield']) else 'N/A')
            with col2:
                st.metric("PB Ratio", f"{fund['pb_ratio']:.1f}" if pd.notna(fund['pb_ratio']) else 'N/A')
                st.metric("ROE", f"{fund['roe']:.1f}%" if pd.notna(fund['roe']) else 'N/A')
            with col3:
                if pd.notna(fund['market_cap']):
                    market_cap_billion = fund['market_cap'] / 1e9
                    st.metric("市值", f"{market_cap_billion:,.0f} 億")
                else:
                    st.metric("市值", 'N/A')
                st.metric("EPS", f"{fund['eps']:.2f}" if pd.notna(fund['eps']) else 'N/A')
            with col4:
                if pd.notna(fund['revenue']):
                    revenue_billion = fund['revenue'] / 1e9
                    st.metric("營收", f"{revenue_billion:,.0f} 億")
                else:
                    st.metric("營收", 'N/A')
                if pd.notna(fund['net_income']):
                    net_income_billion = fund['net_income'] / 1e9
                    st.metric("淨利", f"{net_income_billion:,.0f} 億")
                else:
                    st.metric("淨利", 'N/A')
        else:
            st.info("ℹ️ 沒有基本面資料")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")

# 側邊欄
with st.sidebar:
    st.markdown(f"""
    **更新時間：**  
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

# ---------- 相關新聞（每日自動匯入） ----------
st.markdown("---")
st.subheader("📰 相關新聞")

from modules.database import get_stock_news as _get_news
try:
    _news = _get_news(selected_stock_id, limit=15)
    if _news.empty:
        st.caption("尚無新聞資料，執行 python scripts/update_data.py 後將每日自動匯入")
    else:
        for _, _n in _news.iterrows():
            _day = str(_n['date'])[:10]
            st.markdown(f"- {_day}｜[{_n['title']}]({_n['link']})　"
                        f"<span style='color:#98A2B3;font-size:0.85em'>{_n['source']}</span>",
                        unsafe_allow_html=True)
except Exception as _e:
    st.caption(f"新聞載入失敗: {_e}")
