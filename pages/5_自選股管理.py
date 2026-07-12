"""
股票追蹤與決策輔助系統 - 自選股管理頁
Stock Tracking & Decision Support System - Watchlist Management Page
"""

import streamlit as st
import pandas as pd
from modules.database import get_all_stocks, add_stock, set_stock_enabled

# 設定頁面配置
st.set_page_config(
    page_title="自選股管理 - 股票追蹤系統",
    page_icon="📋",
    layout="wide"
)

from modules.ui import apply_style
apply_style()

st.title("📋 自選股管理")
st.markdown("---")

# ---------- 新增自選股 ----------
st.subheader("➕ 新增自選股")

col1, col2 = st.columns([1, 2])
with col1:
    new_stock_id = st.text_input("股票代號", placeholder="例如：2412",
                                 max_chars=10).strip()
with col2:
    st.caption("輸入台股代號後按「查詢並加入」，系統會自動向 FinMind "
               "查詢名稱與產業，並立即抓取歷史股價。")

if st.button("🔍 查詢並加入", type="primary", disabled=not new_stock_id):
    from modules.data_fetcher import FinMindFetcher, update_stock

    fetcher = FinMindFetcher()
    try:
        with st.spinner(f"查詢 {new_stock_id} 基本資料..."):
            info = fetcher.fetch_stock_info(new_stock_id)

        if info is None:
            st.error(f"❌ 查無代號 {new_stock_id}，請確認代號是否正確")
        else:
            add_stock(info['stock_id'], info['name'],
                      info['market'], info['industry'])
            st.success(f"✅ 已加入 {info['stock_id']} {info['name']}"
                       f"（{info['market']} / {info['industry']}）")

            with st.spinner(f"抓取 {info['name']} 歷史資料（約 180 天）..."):
                result = update_stock(fetcher, info['stock_id'])
            st.info(f"📥 已抓取股價 {result['prices_saved']} 筆、"
                    f"估值 {result['valuation_saved']} 筆。"
                    f"請按下方「重新計算」讓評分與訊號納入此股票。")
            st.rerun()
    except Exception as e:
        st.error(f"❌ 加入失敗: {e}")

st.markdown("---")

# ---------- 自選股清單 ----------
st.subheader("📄 自選股清單")

try:
    stocks = get_all_stocks()

    if stocks.empty:
        st.warning("⚠️ 沒有自選股資料，請先執行 `python scripts/init_db.py`")
    else:
        display = pd.DataFrame({
            '代號': stocks['stock_id'],
            '名稱': stocks['name'],
            '市場': stocks['market'],
            '產業': stocks['industry'],
            '狀態': stocks['enabled'].map(lambda e: '✅ 追蹤中' if e else '⏸️ 已停用'),
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

        # 啟用 / 停用
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            options = {f"{r['stock_id']} {r['name']}": r['stock_id']
                       for _, r in stocks.iterrows()}
            selected = st.selectbox("選擇股票", list(options.keys()))
            selected_id = options[selected]
        with col2:
            st.write("")  # 對齊
            current = bool(stocks.loc[stocks['stock_id'] == selected_id,
                                      'enabled'].iloc[0])
            label = "⏸️ 停用" if current else "▶️ 啟用"
            if st.button(label):
                set_stock_enabled(selected_id, not current)
                st.rerun()
        with col3:
            st.caption("停用後不再出現在 Dashboard、訊號與每日更新中，"
                       "歷史資料保留，隨時可重新啟用。")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")

st.markdown("---")

# ---------- 重新計算 ----------
st.subheader("🔄 重新計算")
st.caption("新增或啟用股票後，按此讓技術指標、評分、訊號涵蓋最新清單。")

if st.button("重新計算指標 / 評分 / 訊號"):
    try:
        with st.spinner("計算中，約需數秒..."):
            from scripts.calculate_indicators import calculate_and_save_indicators
            from scripts.calculate_scores import calculate_and_save_scores
            from scripts.generate_signals import generate_and_save_signals
            calculate_and_save_indicators()
            calculate_and_save_scores()
            generate_and_save_signals()
        st.success("✅ 重新計算完成！")
    except Exception as e:
        st.error(f"❌ 計算失敗: {e}")
