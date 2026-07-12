"""
股票追蹤與決策輔助系統 - 分析管理器基底類別
Stock Tracking & Decision Support System - Base Analysis Manager

十個分析模組（行業/商業模式/管理層/財報/估值/投資邏輯/風險/
5+2 綜合評估/電話會議/投行觀點/宏觀指標）共用的
資料庫連接與更新/刪除操作。
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict
from modules.config import get_config
from modules.console import safe_print
from modules.db_utils import build_set_clauses


class BaseAnalysisManager:
    """分析管理器基底類別

    子類別需定義：
        TABLE: 資料表名稱
        LABEL: 中文名稱（用於訊息輸出）
    """

    TABLE: str = ''
    LABEL: str = ''

    def __init__(self):
        self._config_override = None

    @property
    def config(self):
        """取得 config

        未覆寫時每次動態解析（測試可 patch modules.base_manager.get_config）；
        直接指定 manager.config = xxx 則優先使用覆寫值。
        """
        return self._config_override if self._config_override is not None else get_config()

    @config.setter
    def config(self, value):
        self._config_override = value

    def get_connection(self) -> sqlite3.Connection:
        """取得資料庫連接"""
        db_path = Path(self.config.DATABASE_PATH)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _update_row(self, where: Dict[str, Any], updates: Dict[str, Any],
                    subject: str) -> bool:
        """依鍵值更新一筆資料

        欄位名以資料表實際欄位為白名單（見 build_set_clauses）；
        where 的鍵一律來自呼叫端程式碼常數，不可來自使用者輸入。

        Args:
            where: 鍵欄位 -> 值（決定要更新哪一筆）
            updates: 欄位 -> 新值
            subject: 訊息輸出時的主體描述（如股票代號）

        Returns:
            是否成功
        """
        conn = self.get_connection()
        try:
            set_clauses, values = build_set_clauses(conn, self.TABLE, updates)
            if not set_clauses:
                return False

            where_sql = ' AND '.join(f"{k} = ?" for k in where)
            conn.execute(
                f"UPDATE {self.TABLE} SET {', '.join(set_clauses)} WHERE {where_sql}",
                values + list(where.values()))
            conn.commit()

            safe_print(f"✅ 更新{self.LABEL}: {subject}")
            return True
        except Exception as e:
            safe_print(f"❌ 更新{self.LABEL}失敗: {e}")
            return False
        finally:
            conn.close()

    def _delete_row(self, where: Dict[str, Any], subject: str) -> bool:
        """依鍵值刪除資料

        Args:
            where: 鍵欄位 -> 值
            subject: 訊息輸出時的主體描述

        Returns:
            是否成功
        """
        conn = self.get_connection()
        try:
            where_sql = ' AND '.join(f"{k} = ?" for k in where)
            conn.execute(f"DELETE FROM {self.TABLE} WHERE {where_sql}",
                         list(where.values()))
            conn.commit()

            safe_print(f"✅ 刪除{self.LABEL}: {subject}")
            return True
        except Exception as e:
            safe_print(f"❌ 刪除{self.LABEL}失敗: {e}")
            return False
        finally:
            conn.close()
