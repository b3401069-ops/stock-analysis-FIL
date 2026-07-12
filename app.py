"""
股票追蹤與決策輔助 WebUI V1
Stock Tracking & Decision Support WebUI V1
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.database import get_enabled_stocks, get_latest_prices, get_price_change, get_latest_fundamentals

# 設定頁面配置
st.set_page_config(
    page_title="股票追蹤與決策輔助系統 V1.1",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

from modules.ui import apply_style, color_change
apply_style()

# 頁面標題橫幅
st.markdown("""
<div class="app-hero">
    <h1>📈 股票追蹤與決策輔助系統</h1>
    <p>V1.1 ・ 資料來源 FinMind ・ 僅供學習研究，不構成投資建議</p>
</div>
""", unsafe_allow_html=True)

# 自選股 Dashboard
st.header("📊 自選股 Dashboard")

# 取得資料
try:
    latest_prices = get_latest_prices()
    fundamentals = get_latest_fundamentals()
    
    if latest_prices.empty:
        st.warning("⚠️ 資料庫中沒有股票資料，請先執行 `python scripts/init_db.py`")
    else:
        # 準備 Dashboard 資料
        dashboard_data = []
        for _, row in latest_prices.iterrows():
            stock_id = row['stock_id']
            change_info = get_price_change(stock_id)
            
            # 取得基本面資料
            fund_row = fundamentals[fundamentals['stock_id'] == stock_id]
            pe_ratio = fund_row.iloc[0]['pe_ratio'] if not fund_row.empty else None
            dividend_yield = fund_row.iloc[0]['dividend_yield'] if not fund_row.empty else None
            
            dashboard_data.append({
                '股票代號': stock_id,
                '股票名稱': row['name'],
                '市場': row['market'],
                '產業': row['industry'],
                '最新收盤價': f"NT$ {change_info.get('latest_close', 0):,.2f}",
                '漲跌': f"{change_info.get('change', 0):+.2f}",
                '漲跌幅': f"{change_info.get('change_pct', 0):+.2f}%",
                '成交量': f"{row['volume']:,.0f}" if pd.notna(row['volume']) else 'N/A',
                'PE Ratio': f"{pe_ratio:.1f}" if pd.notna(pe_ratio) else 'N/A',
                '殖利率': f"{dividend_yield:.1f}%" if pd.notna(dividend_yield) else 'N/A'
            })
        
        df_dashboard = pd.DataFrame(dashboard_data)

        # 漲跌欄位紅漲綠跌著色（pandas 2.1+ 用 map，舊版用 applymap）
        styler = df_dashboard.style
        style_fn = styler.map if hasattr(styler, 'map') else styler.applymap
        styled = style_fn(color_change, subset=['漲跌', '漲跌幅'])

        # 顯示表格
        st.dataframe(
            styled,
            use_container_width=True,
            hide_index=True,
            column_config={
                '股票代號': st.column_config.TextColumn('股票代號', width='small'),
                '股票名稱': st.column_config.TextColumn('股票名稱', width='medium'),
                '市場': st.column_config.TextColumn('市場', width='small'),
                '產業': st.column_config.TextColumn('產業', width='medium'),
                '最新收盤價': st.column_config.TextColumn('最新收盤價', width='small'),
                '漲跌': st.column_config.TextColumn('漲跌', width='small'),
                '漲跌幅': st.column_config.TextColumn('漲跌幅', width='small'),
                '成交量': st.column_config.TextColumn('成交量', width='small'),
                'PE Ratio': st.column_config.TextColumn('PE Ratio', width='small'),
                '殖利率': st.column_config.TextColumn('殖利率', width='small')
            }
        )
        
        # 顯示統計資訊
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("自選股數量", f"{len(latest_prices)} 檔")
        with col2:
            latest_date = latest_prices['latest_date'].max()
            st.metric("最新資料日期", latest_date)
        with col3:
            total_volume = latest_prices['volume'].sum()
            st.metric("總成交量", f"{total_volume:,.0f}")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")

# 側邊欄
with st.sidebar:
    st.header("📋 系統資訊")
    st.markdown(f"""
    **版本：** V1.1.0
    **更新時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
    **狀態：** 運行中
    """)
    
    st.markdown("---")
    st.markdown("### ⚙️ 設定")
    st.markdown("""
    - 資料來源：FinMind
    - 資料庫：SQLite
    - 通知：Telegram
    """)

# 頁面底部
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>股票追蹤與決策輔助系統 V1.1 | 僅供學習研究使用</p>
</div>
""", unsafe_allow_html=True)