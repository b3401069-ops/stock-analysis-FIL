#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 - 清除 V1.1 範例研究資料
Stock Tracking & Decision Support System - Clear V1.1 Sample Research Data

清除安裝時匯入的示範資料（財報電話會議、投行觀點、5+2 研究、
七大分析明細、非 FinMind 來源的宏觀指標），
讓研究筆記頁面從乾淨狀態開始。

不影響：股價、指標、評分、訊號、FinMind 抓取的宏觀指標。

用法：
    python scripts/clear_sample_research.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.database import get_connection
from modules.console import safe_print

# 研究筆記類資料表（全量清除）
RESEARCH_TABLES = [
    'earnings_calls',
    'analyst_views',
    'research_5plus2',
    'industry_analysis',
    'business_model',
    'management_analysis',
    'financial_analysis',
    'valuation_analysis',
    'investment_thesis',
    'risk_analysis',
]


def clear_sample_research():
    safe_print("=" * 50)
    safe_print("清除 V1.1 範例研究資料")
    safe_print("=" * 50)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        total = 0

        for table in RESEARCH_TABLES:
            try:
                count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                cursor.execute(f"DELETE FROM {table}")
                safe_print(f"  🗑️  {table}: 刪除 {count} 筆")
                total += count
            except Exception as e:
                safe_print(f"  ⚠️  {table}: 略過（{e}）")

        # 宏觀指標只清除非 FinMind 來源的範例列，保留真實資料
        try:
            count = cursor.execute(
                "SELECT COUNT(*) FROM macro_indicators "
                "WHERE source IS NULL OR source != 'FinMind'").fetchone()[0]
            cursor.execute(
                "DELETE FROM macro_indicators "
                "WHERE source IS NULL OR source != 'FinMind'")
            safe_print(f"  🗑️  macro_indicators（範例列）: 刪除 {count} 筆")
            total += count
        except Exception as e:
            safe_print(f"  ⚠️  macro_indicators: 略過（{e}）")

        conn.commit()
        safe_print("=" * 50)
        safe_print(f"✅ 完成，共清除 {total} 筆範例資料")
        safe_print("   之後請在各頁面的「記錄管理」區直接輸入你自己的研究筆記")
        safe_print("=" * 50)
    finally:
        conn.close()


if __name__ == "__main__":
    clear_sample_research()
