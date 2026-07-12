#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 V1 - 計算技術指標腳本
Stock Tracking & Decision Support System V1 - Calculate Indicators Script
"""

import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.indicators import calculate_all_indicators
from modules.database import get_connection, get_stock_prices, get_enabled_stocks, save_indicators, clear_indicators
from modules.console import safe_print


def calculate_and_save_indicators():
    """計算並儲存所有股票的技術指標"""
    safe_print("=" * 50)
    safe_print("股票追蹤與決策輔助系統 V1 - 計算技術指標")
    safe_print("=" * 50)
    
    # 取得所有啟用的股票
    stocks = get_enabled_stocks()
    
    if stocks.empty:
        safe_print("⚠️  沒有啟用的股票")
        return
    
    safe_print(f"\n📊 找到 {len(stocks)} 檔自選股")
    
    # 清除舊的技術指標
    clear_indicators()
    safe_print("🗑️  已清除舊的技術指標")
    
    # 計算每檔股票的技術指標
    total_indicators = 0
    for _, stock in stocks.iterrows():
        stock_id = stock['stock_id']
        stock_name = stock['name']
        
        safe_print(f"\n📈 計算 {stock_id} {stock_name} 的技術指標...")
        
        # 取得價格資料
        prices = get_stock_prices(stock_id, days=100)
        
        if len(prices) < 20:
            safe_print(f"  ⚠️  資料不足（{len(prices)} 筆），需要至少 20 筆")
            continue
        
        # 計算技術指標
        try:
            indicators_df = calculate_all_indicators(prices)
            
            # 儲存到資料庫
            count = 0
            for _, row in indicators_df.iterrows():
                indicators = {
                    'ma5': row.get('ma5'),
                    'ma20': row.get('ma20'),
                    'ma60': row.get('ma60'),
                    'rsi': row.get('rsi'),
                    'macd': row.get('macd'),
                    'macd_signal': row.get('macd_signal'),
                    'macd_histogram': row.get('macd_histogram'),
                    'volume_ma20': row.get('volume_ma20')
                }
                save_indicators(stock_id, row['date'], indicators)
                count += 1
            
            safe_print(f"  ✅ 已儲存 {count} 筆技術指標")
            total_indicators += count
            
        except Exception as e:
            safe_print(f"  ❌ 計算失敗: {e}")
    
    safe_print("\n" + "=" * 50)
    safe_print(f"✅ 計算完成！共儲存 {total_indicators} 筆技術指標")
    safe_print("=" * 50)


if __name__ == "__main__":
    calculate_and_save_indicators()