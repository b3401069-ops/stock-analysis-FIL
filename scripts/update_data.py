#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 - 每日資料更新腳本（FinMind）
Stock Tracking & Decision Support System - Daily Data Update Script

流程：
1. 讀取自選股清單（stocks 表 enabled=1）
2. 對每檔股票增量抓取股價與估值（只抓資料庫缺少的區間）
3. 重新計算技術指標、評分、訊號

用法：
    python scripts/update_data.py                # 更新股票 + 宏觀 + 重算指標/評分/訊號
    python scripts/update_data.py --skip-recalc  # 不重算指標/評分/訊號
    python scripts/update_data.py --skip-macro   # 不更新宏觀指標
"""

import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.config import get_config
from modules.console import safe_print
from modules.database import get_enabled_stocks
from modules.data_fetcher import FinMindFetcher, update_stock, update_macro_indicators


def update_all_stocks() -> bool:
    """更新所有自選股的資料

    Returns:
        是否至少有一檔股票更新成功
    """
    safe_print("=" * 50)
    safe_print("股票追蹤與決策輔助系統 - 每日資料更新（FinMind）")
    safe_print("=" * 50)

    config = get_config()
    stocks = get_enabled_stocks()

    if stocks.empty:
        safe_print("⚠️  沒有啟用的自選股，請先執行 python scripts/init_db.py")
        return False

    safe_print(f"\n📊 找到 {len(stocks)} 檔自選股")

    fetcher = FinMindFetcher()
    lookback = config.DATA_UPDATE_LOOKBACK_DAYS
    success_count = 0
    failures = []

    for _, stock in stocks.iterrows():
        stock_id = stock['stock_id']
        stock_name = stock['name']
        safe_print(f"\n📈 更新 {stock_id} {stock_name}...")

        try:
            result = update_stock(fetcher, stock_id, lookback_days=lookback)
            if result['prices_saved'] == 0 and result['valuation_saved'] == 0:
                safe_print(f"  ℹ️  無新資料（起始日 {result['start_date']}）")
            else:
                extras_note = "、月營收/財報已補" if result.get('extras_saved') else ""
                safe_print(f"  ✅ 股價 {result['prices_saved']} 筆、"
                           f"還原股價 {result.get('adj_saved', 0)} 筆、"
                           f"估值 {result['valuation_saved']} 筆、"
                           f"法人買賣超 {result.get('institutional_saved', 0)} 筆、"
                           f"新聞 {result.get('news_saved', 0)} 則"
                           f"（自 {result['start_date']}）{extras_note}")
            success_count += 1
        except Exception as e:
            safe_print(f"  ❌ 更新失敗: {e}")
            failures.append(stock_id)

    safe_print("\n" + "=" * 50)
    safe_print(f"✅ 更新完成：成功 {success_count} 檔、失敗 {len(failures)} 檔")
    if failures:
        safe_print(f"❌ 失敗清單: {', '.join(failures)}")
    safe_print("=" * 50)

    return success_count > 0


def update_macro() -> bool:
    """更新宏觀經濟指標

    Returns:
        是否全部成功（部分失敗回傳 False，但已成功的仍會寫入）
    """
    safe_print("\n🌐 更新宏觀經濟指標...")
    config = get_config()
    fetcher = FinMindFetcher()
    result = update_macro_indicators(fetcher, config.MACRO_FETCH_SPECS)
    safe_print(f"🌐 宏觀指標更新完成：{result['saved']} 筆")
    if result['failures']:
        safe_print(f"❌ 失敗指標: {', '.join(result['failures'])}")
    return not result['failures']


def recalculate_all():
    """重新計算技術指標、評分、訊號"""
    safe_print("\n🔄 重新計算技術指標...")
    from scripts.calculate_indicators import calculate_and_save_indicators
    calculate_and_save_indicators()

    safe_print("\n🔄 重新計算股票評分...")
    from scripts.calculate_scores import calculate_and_save_scores
    calculate_and_save_scores()

    safe_print("\n🔄 重新產生訊號...")
    from scripts.generate_signals import generate_and_save_signals
    generate_and_save_signals()


def main():
    skip_recalc = '--skip-recalc' in sys.argv
    skip_macro = '--skip-macro' in sys.argv

    updated = update_all_stocks()

    if not skip_macro:
        update_macro()

    if updated and not skip_recalc:
        recalculate_all()
    elif not updated:
        safe_print("⚠️  沒有任何股票更新成功，略過重新計算")
        sys.exit(1)


if __name__ == "__main__":
    main()
