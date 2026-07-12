"""
股票追蹤與決策輔助系統 - 資料庫工具模組
Stock Tracking & Decision Support System - Database Utilities
"""

import sqlite3
from typing import Dict, Any, List, Tuple


def build_set_clauses(conn: sqlite3.Connection, table: str,
                      updates: Dict[str, Any]) -> Tuple[List[str], List[Any]]:
    """建立 UPDATE 的 SET 子句，欄位名以資料表實際欄位為白名單

    欄位名無法參數化，直接串接 SQL 有注入風險；
    這裡以 PRAGMA table_info 取得的實際欄位過濾，
    不存在的欄位一律略過。

    Args:
        conn: 資料庫連接
        table: 資料表名稱（呼叫端寫死的常數，不可來自使用者輸入）
        updates: 欄位 -> 新值 的字典

    Returns:
        (set 子句列表, 參數值列表)
    """
    valid_columns = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}

    set_clauses = []
    values = []
    for key, value in updates.items():
        if key in valid_columns:
            set_clauses.append(f"{key} = ?")
            values.append(value)

    return set_clauses, values
