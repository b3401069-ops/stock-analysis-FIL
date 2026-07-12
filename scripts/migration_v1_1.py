#!/usr/bin/env python3
"""
資料庫 Migration 工具
Database Migration Utility

提供安全的欄位新增功能，讓既有資料庫可以平滑升級
"""

import sqlite3
from pathlib import Path
import sys

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.console import safe_print


def ensure_column(conn: sqlite3.Connection, table: str, column: str, column_def: str, default_value=None):
    """確保資料表有指定欄位，若無則新增

    Args:
        conn: 資料庫連接
        table: 資料表名稱
        column: 欄位名稱
        column_def: 欄位定義 (例如 "TEXT DEFAULT '研報'")
        default_value: 若需要設定預設值，傳入值；否則使用 column_def 中的 DEFAULT
    """
    cursor = conn.cursor()

    # 檢查欄位是否存在
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    if column not in columns:
        # 欄位不存在，新增它
        alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_def}"
        cursor.execute(alter_sql)
        safe_print(f"[OK] 新增欄位: {table}.{column}")

        # 若有指定預設值且需要更新既有資料
        if default_value is not None:
            cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} IS NULL", (default_value,))
            safe_print(f"   -> 已更新 {cursor.rowcount} 筆既有資料的預設值")
    else:
        safe_print(f"[SKIP] 欄位已存在: {table}.{column}")


def ensure_index(conn: sqlite3.Connection, table: str, index_name: str, columns: str):
    """確保索引存在

    Args:
        conn: 資料庫連接
        table: 資料表名稱
        index_name: 索引名稱
        columns: 索引欄位 (例如 "stock_id, analysis_date")
    """
    cursor = conn.cursor()
    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})")
    safe_print(f"[OK] 索引已就緒: {index_name} ON {table}({columns})")


def migrate_v1_1_source_fields(db_path=None):
    """V1.1 Migration: 新增 source 相關欄位到既有資料表

    此函數會安全地檢查並新增缺少的欄位，不會影響既有資料。

    Args:
        db_path: 資料庫路徑，若未指定則使用 config.DATABASE_PATH
    """
    if db_path is None:
        from modules.config import get_config
        config = get_config()
        db_path = Path(config.DATABASE_PATH)
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        safe_print(f"[ERROR] 資料庫不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    safe_print("")
    safe_print("=" * 60)
    safe_print("[INFO] V1.1 Migration: 新增 source 相關欄位")
    safe_print("=" * 60)

    try:
        # 1. industry_analysis - 新增 source 欄位
        safe_print("")
        safe_print("[TABLE] industry_analysis:")
        ensure_column(conn, "industry_analysis", "source", "TEXT DEFAULT '研報'")
        ensure_column(conn, "industry_analysis", "source_url", "TEXT")
        ensure_column(conn, "industry_analysis", "data_as_of", "DATE")

        # 2. business_model - 新增 source 欄位
        safe_print("")
        safe_print("[TABLE] business_model:")
        ensure_column(conn, "business_model", "source", "TEXT DEFAULT '研報'")
        ensure_column(conn, "business_model", "source_url", "TEXT")
        ensure_column(conn, "business_model", "data_as_of", "DATE")

        # 3. management_analysis - 新增 source 欄位
        safe_print("")
        safe_print("[TABLE] management_analysis:")
        ensure_column(conn, "management_analysis", "source", "TEXT DEFAULT '研報'")
        ensure_column(conn, "management_analysis", "source_url", "TEXT")
        ensure_column(conn, "management_analysis", "data_as_of", "DATE")

        # 4. financial_analysis - 補齊所有 source 相關欄位
        safe_print("")
        safe_print("[TABLE] financial_analysis:")
        ensure_column(conn, "financial_analysis", "source", "TEXT DEFAULT '研報'")
        ensure_column(conn, "financial_analysis", "source_url", "TEXT")
        ensure_column(conn, "financial_analysis", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ensure_column(conn, "financial_analysis", "data_as_of", "DATE")

        # 5. valuation_analysis - 新增 source 欄位
        safe_print("")
        safe_print("[TABLE] valuation_analysis:")
        ensure_column(conn, "valuation_analysis", "source", "TEXT DEFAULT '研報'")
        ensure_column(conn, "valuation_analysis", "source_url", "TEXT")
        ensure_column(conn, "valuation_analysis", "data_as_of", "DATE")

        # 6. investment_thesis - 新增 source 欄位
        safe_print("")
        safe_print("[TABLE] investment_thesis:")
        ensure_column(conn, "investment_thesis", "source", "TEXT DEFAULT '研報'")
        ensure_column(conn, "investment_thesis", "source_url", "TEXT")
        ensure_column(conn, "investment_thesis", "data_as_of", "DATE")

        # 7. risk_analysis - 新增 source 欄位
        safe_print("")
        safe_print("[TABLE] risk_analysis:")
        ensure_column(conn, "risk_analysis", "source", "TEXT DEFAULT '研報'")
        ensure_column(conn, "risk_analysis", "source_url", "TEXT")
        ensure_column(conn, "risk_analysis", "data_as_of", "DATE")

        # 8. earnings_calls - 補齊所有 source 相關欄位
        safe_print("")
        safe_print("[TABLE] earnings_calls:")
        ensure_column(conn, "earnings_calls", "source", "TEXT DEFAULT '公開資訊'")
        ensure_column(conn, "earnings_calls", "source_url", "TEXT")
        ensure_column(conn, "earnings_calls", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ensure_column(conn, "earnings_calls", "data_as_of", "DATE")

        # 9. analyst_views - 補齊所有 source 相關欄位
        safe_print("")
        safe_print("[TABLE] analyst_views:")
        ensure_column(conn, "analyst_views", "source", "TEXT DEFAULT '投行研報'")
        ensure_column(conn, "analyst_views", "source_url", "TEXT")
        ensure_column(conn, "analyst_views", "source_type", "TEXT DEFAULT '摘要'")
        ensure_column(conn, "analyst_views", "is_paid_report", "INTEGER DEFAULT 0")
        ensure_column(conn, "analyst_views", "summary_only", "INTEGER DEFAULT 1")
        ensure_column(conn, "analyst_views", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ensure_column(conn, "analyst_views", "data_as_of", "DATE")

        # 10. macro_indicators - 新增 data_as_of
        safe_print("")
        safe_print("[TABLE] macro_indicators:")
        ensure_column(conn, "macro_indicators", "data_as_of", "DATE")

        conn.commit()
        safe_print("")
        safe_print("=" * 60)
        safe_print("[DONE] Migration 完成！")
        safe_print("=" * 60)
        return True

    except Exception as e:
        safe_print(f"\n[ERROR] Migration 失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def run_migration(db_path=None):
    """執行所有待處理的 migration

    Args:
        db_path: 資料庫路徑
    """
    safe_print("")
    safe_print("[INFO] 開始執行資料庫 Migration...")
    success = migrate_v1_1_source_fields(db_path)
    return success


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
