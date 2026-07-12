#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 V1 - 發送每日警報腳本
Stock Tracking & Decision Support System V1 - Send Daily Alerts Script
"""

import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.alerts import send_daily_alerts
from modules.console import safe_print


def main():
    """主函數"""
    safe_print("=" * 50)
    safe_print("股票追蹤與決策輔助系統 V1 - 發送每日警報")
    safe_print("=" * 50)
    
    success = send_daily_alerts()
    
    if success:
        safe_print("\n✅ 每日警報發送成功！")
    else:
        safe_print("\n❌ 每日警報發送失敗或未設定")
    
    safe_print("=" * 50)


if __name__ == "__main__":
    main()