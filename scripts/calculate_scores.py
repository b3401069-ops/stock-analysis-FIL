#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 V1 - 計算股票評分腳本
Stock Tracking & Decision Support System V1 - Calculate Scores Script
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.scoring import score_stock
from modules.database import get_enabled_stocks, get_stock_prices, get_indicators, get_latest_fundamentals, save_score, clear_scores
from modules.console import safe_print


def calculate_and_save_scores():
    """計算並儲存所有股票的評分"""
    safe_print("=" * 50)
    safe_print("股票追蹤與決策輔助系統 V1 - 計算股票評分")
    safe_print("=" * 50)
    
    # 取得所有啟用的股票
    stocks = get_enabled_stocks()
    
    if stocks.empty:
        safe_print("⚠️  沒有啟用的股票")
        return
    
    safe_print(f"\n📊 找到 {len(stocks)} 檔自選股")
    
    # 取得基本面資料
    fundamentals = get_latest_fundamentals()
    
    # 清除舊的評分
    clear_scores()
    safe_print("🗑️  已清除舊的評分")
    
    # 計算每檔股票的評分
    today = datetime.now().strftime('%Y-%m-%d')
    total_scores = 0
    
    for _, stock in stocks.iterrows():
        stock_id = stock['stock_id']
        stock_name = stock['name']
        
        safe_print(f"\n📈 計算 {stock_id} {stock_name} 的評分...")
        
        # 取得價格資料
        prices = get_stock_prices(stock_id, days=60)
        indicators = get_indicators(stock_id, days=60)
        
        # 取得基本面資料
        fund_row = fundamentals[fundamentals['stock_id'] == stock_id]
        fund_data = fund_row.iloc[0] if not fund_row.empty else pd.Series()
        
        if prices.empty:
            safe_print(f"  ⚠️  沒有價格資料")
            continue
        
        # 計算評分
        try:
            score_data = score_stock(stock_id, prices, indicators, fund_data)
            
            # 儲存到資料庫
            save_score(stock_id, today, score_data)
            
            safe_print(f"  ✅ 評分完成：{score_data['rating']}（總分 {score_data['total_score']:.1f}）")
            safe_print(f"     技術面：{score_data['technical_score']:.1f}，基本面：{score_data['fundamental_score']:.1f}，風險：{score_data['risk_score']:.1f}")
            total_scores += 1
            
        except Exception as e:
            safe_print(f"  ❌ 計算失敗: {e}")
    
    safe_print("\n" + "=" * 50)
    safe_print(f"✅ 評分完成！共計算 {total_scores} 檔股票")
    safe_print("=" * 50)


if __name__ == "__main__":
    calculate_and_save_scores()