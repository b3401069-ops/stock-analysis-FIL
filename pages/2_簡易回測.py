"""
股票追蹤與決策輔助系統 V1 - 簡易回測頁
Stock Tracking & Decision Support System V1 - Simple Backtest Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from modules.database import get_enabled_stocks, get_stock_prices
from modules.backtest import get_strategy, get_available_strategies, run_backtest
from modules.database import get_stock_prices_adj

# 設定頁面配置
st.set_page_config(
    page_title="簡易回測 - 股票追蹤系統",
    page_icon="📈",
    layout="wide"
)

from modules.ui import apply_style
apply_style()

# 頁面標題
st.title("📈 簡易回測")
st.markdown("---")

# 取得自選股清單
try:
    stocks = get_enabled_stocks()
    strategies = get_available_strategies()
    
    if stocks.empty:
        st.warning("⚠️ 沒有自選股資料，請先執行 `python scripts/init_db.py`")
    else:
        # 控制面板
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 股票選擇器
            stock_options = {f"{row['stock_id']} {row['name']}": row['stock_id'] for _, row in stocks.iterrows()}
            selected_stock_label = st.selectbox(
                "選擇股票",
                options=list(stock_options.keys()),
                index=0
            )
            selected_stock_id = stock_options[selected_stock_label]
        
        with col2:
            # 策略選擇器
            strategy_options = {s['description']: s['name'] for s in strategies}
            selected_strategy_label = st.selectbox(
                "選擇策略",
                options=list(strategy_options.keys()),
                index=0
            )
            selected_strategy_name = strategy_options[selected_strategy_label]
        
        with col3:
            # 日期範圍
            days = st.slider("回測天數", min_value=30, max_value=365, value=180)
        
        # 策略參數
        st.subheader("⚙️ 策略參數")
        
        strategy_func = get_strategy(selected_strategy_name)
        
        if selected_strategy_name == 'ma_cross':
            col1, col2 = st.columns(2)
            with col1:
                short_period = st.slider("短期均線", min_value=3, max_value=30, value=5)
            with col2:
                long_period = st.slider("長期均線", min_value=10, max_value=120, value=20)
            
            params = {'short_period': short_period, 'long_period': long_period}
        
        elif selected_strategy_name == 'rsi':
            col1, col2, col3 = st.columns(3)
            with col1:
                period = st.slider("RSI 期間", min_value=5, max_value=30, value=14)
            with col2:
                oversold = st.slider("超賣門檻", min_value=10, max_value=40, value=30)
            with col3:
                overbought = st.slider("超買門檻", min_value=60, max_value=90, value=70)
            
            params = {'period': period, 'oversold': oversold, 'overbought': overbought}
        
        elif selected_strategy_name == 'macd':
            col1, col2, col3 = st.columns(3)
            with col1:
                fast = st.slider("快線", min_value=5, max_value=20, value=12)
            with col2:
                slow = st.slider("慢線", min_value=15, max_value=40, value=26)
            with col3:
                signal = st.slider("訊號線", min_value=5, max_value=20, value=9)
            
            params = {'fast': fast, 'slow': slow, 'signal': signal}

        # 價格資料來源
        use_adj = st.checkbox(
            "使用還原權值股價（已調整除權息，長期回測建議勾選）",
            value=False,
            help="需先執行 python scripts/update_data.py 抓取還原股價；"
                 "無資料時自動改用原始股價")

        # 交易成本設定
        st.subheader("💰 交易成本")
        include_costs = st.checkbox("計入交易成本（台股：手續費 0.1425%、證交稅 0.3%）", value=True)
        if include_costs:
            col1, col2 = st.columns(2)
            with col1:
                buy_cost_rate = st.number_input("買入成本率 (%)", min_value=0.0, max_value=1.0,
                                                value=0.1425, step=0.0125, format="%.4f") / 100
            with col2:
                sell_cost_rate = st.number_input("賣出成本率 (%)", min_value=0.0, max_value=1.0,
                                                 value=0.4425, step=0.0125, format="%.4f") / 100
        else:
            buy_cost_rate = 0.0
            sell_cost_rate = 0.0

        # 執行回測
        if st.button("🚀 執行回測", type="primary"):
            st.markdown("---")
            st.subheader("📊 回測結果")
            
            # 取得價格資料
            if use_adj:
                prices = get_stock_prices_adj(selected_stock_id, days=days)
                if prices.empty:
                    st.warning("⚠️ 沒有還原權值股價資料，改用原始股價"
                               "（執行 python scripts/update_data.py 可抓取）")
                    prices = get_stock_prices(selected_stock_id, days=days)
                else:
                    st.caption("📌 使用還原權值股價（已調整除權息）")
            else:
                prices = get_stock_prices(selected_stock_id, days=days)

            if prices.empty:
                st.error("❌ 沒有足夠的價格資料")
            else:
                # 執行策略
                signals = strategy_func(prices, **params)
                
                # 執行回測
                result = run_backtest(prices, signals,
                                      buy_cost_rate=buy_cost_rate,
                                      sell_cost_rate=sell_cost_rate)
                
                # 顯示結果指標
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("總報酬率", f"{result['total_return']:.2f}%")
                    st.metric("年化報酬率", f"{result['annual_return']:.2f}%")
                
                with col2:
                    st.metric("最大回撤", f"{result['max_drawdown']:.2f}%")
                    st.metric("夏普比率", f"{result['sharpe_ratio']:.2f}")
                
                with col3:
                    st.metric("交易次數", f"{result['total_trades']} 次")
                    st.metric("勝率", f"{result['win_rate']:.2f}%")
                
                with col4:
                    st.metric("初始資金", f"NT$ {result['initial_capital']:,.0f}")
                    st.metric("最終資金", f"NT$ {result['final_capital']:,.0f}")
                
                # 買入持有比較
                st.markdown("---")
                st.subheader("📈 策略 vs 買入持有")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("策略報酬", f"{result['total_return']:.2f}%")
                with col2:
                    st.metric("買入持有報酬", f"{result['buy_and_hold_return']:.2f}%")
                
                excess = result['total_return'] - result['buy_and_hold_return']
                st.metric("超額報酬", f"{excess:+.2f}%")
                
                # 繪製圖表
                st.markdown("---")
                st.subheader("📉 累積報酬圖表")
                
                data = result['data']
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=data['date'],
                    y=data['strategy_cumulative_return'] * 100,
                    name='策略報酬',
                    line=dict(color='blue', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=data['date'],
                    y=data['cumulative_return'] * 100,
                    name='買入持有',
                    line=dict(color='gray', width=1, dash='dash')
                ))
                
                fig.update_layout(
                    title="累積報酬率比較",
                    xaxis_title="日期",
                    yaxis_title="報酬率 (%)",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 繪製回撤圖表
                st.subheader("📉 回撤圖表")
                
                fig_drawdown = go.Figure()
                
                fig_drawdown.add_trace(go.Scatter(
                    x=data['date'],
                    y=data['drawdown'] * 100,
                    fill='tozeroy',
                    name='回撤',
                    line=dict(color='red', width=1)
                ))
                
                fig_drawdown.update_layout(
                    title="策略回撤",
                    xaxis_title="日期",
                    yaxis_title="回撤 (%)",
                    height=400
                )
                
                st.plotly_chart(fig_drawdown, use_container_width=True)
                
                # 交易統計
                st.markdown("---")
                st.subheader("📊 交易統計")
                
                # 設計說明
                st.caption("""
                ⚠️ 回測設計說明：
                - 訊號日在 T 日收盤後產生
                - 成交日在 T+1 日開盤時執行（避免 look-ahead bias）
                - 成交價使用 T+1 日開盤價
                """)
                
                if result['trades']:
                    # 整理交易記錄
                    trades_display = []
                    for i, trade in enumerate(result['trades']):
                        if trade['type'] == '買入':
                            trades_display.append({
                                '交易': f"第 {i//2 + 1} 筆",
                                '類型': '買入',
                                '日期': trade['date'],
                                '價格': f"{trade['price']:.2f}",
                                '訊號日': trade['signal_date'],
                                '報酬率': '-',
                                '結果': '-'
                            })
                        elif trade['type'] == '賣出':
                            profit = trade.get('profit', 0)
                            trades_display.append({
                                '交易': f"第 {i//2 + 1} 筆",
                                '類型': '賣出',
                                '日期': trade['date'],
                                '價格': f"{trade['price']:.2f}",
                                '訊號日': trade['signal_date'],
                                '報酬率': f"{profit*100:.2f}%",
                                '結果': '獲利' if profit > 0 else '虧損'
                            })
                    
                    trades_df = pd.DataFrame(trades_display)
                    st.dataframe(trades_df, use_container_width=True, hide_index=True)
                    
                    # 獲利/虧損統計
                    sell_trades = [t for t in result['trades'] if t['type'] == '賣出']
                    profits = [t['profit'] for t in sell_trades if t.get('profit', 0) > 0]
                    losses = [t['profit'] for t in sell_trades if t.get('profit', 0) < 0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("獲利次數", f"{len(profits)} 次")
                    with col2:
                        st.metric("虧損次數", f"{len(losses)} 次")
                    with col3:
                        avg_profit = sum(profits) / len(profits) * 100 if profits else 0
                        st.metric("平均獲利", f"{avg_profit:.2f}%")
                else:
                    st.info("ℹ️ 沒有交易記錄")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")

# 側邊欄
with st.sidebar:
    st.header("📋 導航")
    st.markdown("""
    - [首頁](/)
    - [個股分析](/1_個股分析)
    - [簡易回測](/2_簡易回測)
    - [今日訊號](#)
    """)
    
    st.markdown("---")
    st.markdown(f"""
    **更新時間：**  
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)