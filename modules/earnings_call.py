"""
股票追蹤與決策輔助系統 V1.1 - 電話會議紀錄模組
Stock Tracking & Decision Support System V1.1 - Earnings Call Module

處理電話會議紀錄的查詢、分析與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class EarningsCallManager(BaseAnalysisManager):
    """電話會議管理器"""

    TABLE = "earnings_calls"
    LABEL = "電話會議紀錄"

    def get_earnings_calls(self, stock_id: Optional[str] = None,
                          limit: int = 10) -> pd.DataFrame:
        """取得電話會議紀錄

        Args:
            stock_id: 股票代號，若為 None 則取得所有
            limit: 限制筆數

        Returns:
            電話會議紀錄 DataFrame
        """
        conn = self.get_connection()

        if stock_id:
            query = """
                SELECT ec.*, s.name as stock_name
                FROM earnings_calls ec
                JOIN stocks s ON ec.stock_id = s.stock_id
                WHERE ec.stock_id = ?
                ORDER BY ec.call_date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        else:
            query = """
                SELECT ec.*, s.name as stock_name
                FROM earnings_calls ec
                JOIN stocks s ON ec.stock_id = s.stock_id
                ORDER BY ec.call_date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))

        conn.close()
        return df

    def get_latest_earnings_call(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """取得最新電話會議紀錄

        Args:
            stock_id: 股票代號

        Returns:
            最新電話會議紀錄字典，若無則返回 None
        """
        df = self.get_earnings_calls(stock_id, limit=1)
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_earnings_calls_by_quarter(self, stock_id: str,
                                      fiscal_year: str) -> pd.DataFrame:
        """按季度取得電話會議紀錄

        Args:
            stock_id: 股票代號
            fiscal_year: 會計年度

        Returns:
            電話會議紀錄 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT ec.*, s.name as stock_name
            FROM earnings_calls ec
            JOIN stocks s ON ec.stock_id = s.stock_id
            WHERE ec.stock_id = ? AND ec.fiscal_year = ?
            ORDER BY ec.call_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, fiscal_year))
        conn.close()
        return df

    def get_sentiment_trend(self, stock_id: str,
                           periods: int = 4) -> pd.DataFrame:
        """取得情緒趨勢

        Args:
            stock_id: 股票代號
            periods: 期數

        Returns:
            情緒趨勢 DataFrame
        """
        df = self.get_earnings_calls(stock_id, limit=periods)
        if df.empty:
            return pd.DataFrame()

        # 計算情緒統計
        sentiment_counts = df['sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['sentiment', 'count']

        return sentiment_counts

    def get_guidance_summary(self, stock_id: str) -> Dict[str, Any]:
        """取得指引摘要

        Args:
            stock_id: 股票代號

        Returns:
            指引摘要字典
        """
        latest = self.get_latest_earnings_call(stock_id)
        if not latest:
            return {
                'has_guidance': False,
                'message': '無電話會議紀錄'
            }

        return {
            'has_guidance': True,
            'call_date': latest.get('call_date'),
            'quarter': latest.get('quarter'),
            'revenue_guidance': latest.get('revenue_guidance'),
            'earnings_guidance': latest.get('earnings_guidance'),
            'sentiment': latest.get('sentiment'),
            'outlook_summary': latest.get('outlook_summary')
        }

    def add_earnings_call(self, data: Dict[str, Any]) -> bool:
        """新增電話會議紀錄

        Args:
            data: 電話會議資料字典

        Returns:
            是否成功
        """
        required_fields = ['stock_id', 'call_date', 'quarter', 'fiscal_year']
        for field in required_fields:
            if field not in data:
                safe_print(f"❌ 缺少必要欄位: {field}")
                return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO earnings_calls
                (stock_id, call_date, quarter, fiscal_year, call_time,
                 participants, management_guidance, key_highlights,
                 revenue_guidance, earnings_guidance, margin_guidance,
                 capex_guidance, analyst_questions, management_responses,
                 sentiment, surprises, risk_factors, outlook_summary,
                 transcript_summary, notes, source, source_url, data_as_of)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['call_date'], data['quarter'],
                data['fiscal_year'], data.get('call_time', ''),
                data.get('participants', ''), data.get('management_guidance', ''),
                data.get('key_highlights', ''), data.get('revenue_guidance', ''),
                data.get('earnings_guidance', ''), data.get('margin_guidance', ''),
                data.get('capex_guidance', ''), data.get('analyst_questions', ''),
                data.get('management_responses', ''), data.get('sentiment', ''),
                data.get('surprises', ''), data.get('risk_factors', ''),
                data.get('outlook_summary', ''), data.get('transcript_summary', ''),
                data.get('notes', ''),
                data.get('source', '公開資訊'), data.get('source_url', ''),
                data.get('data_as_of', data['call_date'])
            ))

            conn.commit()
            safe_print(f"✅ 新增電話會議紀錄: {data['stock_id']} {data['quarter']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增電話會議紀錄失敗: {e}")
            return False
        finally:
            conn.close()

    def update_earnings_call(self, stock_id: str, call_date: str,
                            quarter: str, updates: Dict[str, Any]) -> bool:
        """更新電話會議紀錄

        Args:
            stock_id: 股票代號
            call_date: 電話會議日期
            quarter: 季度
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'call_date': call_date, 'quarter': quarter}, updates, f"{stock_id} {quarter}")

    def delete_earnings_call(self, stock_id: str, call_date: str,
                            quarter: str) -> bool:
        """刪除電話會議紀錄

        Args:
            stock_id: 股票代號
            call_date: 電話會議日期
            quarter: 季度

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'call_date': call_date, 'quarter': quarter}, f"{stock_id} {quarter}")

    def search_earnings_calls(self, keyword: str) -> pd.DataFrame:
        """搜尋電話會議紀錄

        Args:
            keyword: 搜尋關鍵字

        Returns:
            符合條件的電話會議紀錄 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT ec.*, s.name as stock_name
            FROM earnings_calls ec
            JOIN stocks s ON ec.stock_id = s.stock_id
            WHERE ec.key_highlights LIKE ?
               OR ec.management_guidance LIKE ?
               OR ec.outlook_summary LIKE ?
               OR ec.transcript_summary LIKE ?
            ORDER BY ec.call_date DESC
        """
        pattern = f"%{keyword}%"
        df = pd.read_sql_query(query, conn, params=(pattern, pattern, pattern, pattern))
        conn.close()
        return df

    def get_earnings_calendar(self, start_date: str,
                             end_date: str) -> pd.DataFrame:
        """取得電話會議日曆

        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            電話會議日曆 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT ec.stock_id, s.name as stock_name, ec.call_date,
                   ec.quarter, ec.fiscal_year, ec.sentiment
            FROM earnings_calls ec
            JOIN stocks s ON ec.stock_id = s.stock_id
            WHERE ec.call_date BETWEEN ? AND ?
            ORDER BY ec.call_date
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df


# 建立全域實例
earnings_call_manager = EarningsCallManager()


def get_earnings_call_manager() -> EarningsCallManager:
    """取得電話會議管理器實例"""
    return earnings_call_manager