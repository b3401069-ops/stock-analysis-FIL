#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 V1 - 產生訊號腳本
Stock Tracking & Decision Support System V1 - Generate Signals Script
"""

import sys
from pathlib import Path
from datetime import datetime

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.signals import detect_signals, detect_chip_signals
from modules.database import (get_enabled_stocks, get_stock_prices, get_indicators,
                              get_institutional_flows, save_signal, clear_signals)
from modules.console import safe_print


def generate_and_save_signals():
    """產生並儲存所有股票的訊號"""
    safe_print("=" * 50)
    safe_print("股票追蹤與決策輔助系統 V1 - 產生訊號")
    safe_print("=" * 50)
    
    # 取得所有啟用的股票
    stocks = get_enabled_stocks()
    
    if stocks.empty:
        safe_print("⚠️  沒有啟用的股票")
        return
    
    safe_print(f"\n📊 找到 {len(stocks)} 檔自選股")
    
    # 清除舊的訊號
    clear_signals()
    safe_print("🗑️  已清除舊的訊號")
    
    # 產生每檔股票的訊號（訊號日期使用該股最新價格日，而非執行日）
    total_signals = 0
    
    for _, stock in stocks.iterrows():
        stock_id = stock['stock_id']
        stock_name = stock['name']
        
        safe_print(f"\n📈 偵測 {stock_id} {stock_name} 的訊號...")
        
        # 取得價格資料
        prices = get_stock_prices(stock_id, days=60)
        indicators = get_indicators(stock_id, days=60)
        
        if prices.empty:
            safe_print(f"  ⚠️  沒有價格資料")
            continue
        
        # 偵測訊號（技術面 + 籌碼面）
        try:
            signals = detect_signals(prices, indicators)

            # 籌碼面：三大法人買賣超（無資料時回傳空列表，不影響技術面訊號）
            institutional = get_institutional_flows(stock_id, days=10)
            signals.extend(detect_chip_signals(institutional))

            if signals:
                signal_date = str(prices.iloc[-1]['date'])
                safe_print(f"  ✅ 發現 {len(signals)} 個訊號（資料日 {signal_date}）：")
                for signal in signals:
                    save_signal(stock_id, signal_date, signal)
                    safe_print(f"     - {signal['signal_name']} ({signal['severity']})")
                    total_signals += 1
            else:
                safe_print(f"  ℹ️  沒有發現訊號")
            
        except Exception as e:
            safe_print(f"  ❌ 偵測失敗: {e}")
    
    safe_print("\n" + "=" * 50)
    safe_print(f"✅ 訊號產生完成！共產生 {total_signals} 個訊號")
    safe_print("=" * 50)


if __name__ == "__main__":
    generate_and_save_signals()