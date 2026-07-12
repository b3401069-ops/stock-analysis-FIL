"""
股票追蹤與決策輔助系統 V1.1 - 財報分析模組
Stock Tracking & Decision Support System V1.1 - Financial Analysis Module

處理財報分析的查詢、評估與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class FinancialAnalysisManager(BaseAnalysisManager):
    """財報分析管理器"""

    TABLE = "financial_analysis"
    LABEL = "財報分析"

    def get_financial_analysis(self, stock_id: str, analysis_date: str = None) -> Optional[Dict[str, Any]]:
        """取得最新財報分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            財報分析字典，若無則返回 None
        """
        conn = self.get_connection()
        if analysis_date:
            query = """
                SELECT fa.*, s.name as stock_name
                FROM financial_analysis fa
                JOIN stocks s ON fa.stock_id = s.stock_id
                WHERE fa.stock_id = ? AND fa.analysis_date <= ?
                ORDER BY fa.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, analysis_date))
        else:
            query = """
                SELECT fa.*, s.name as stock_name
                FROM financial_analysis fa
                JOIN stocks s ON fa.stock_id = s.stock_id
                WHERE fa.stock_id = ?
                ORDER BY fa.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_financial_analysis_history(self, stock_id: str,
                                      limit: int = 10) -> pd.DataFrame:
        """取得財報分析歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            財報分析歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT fa.*, s.name as stock_name
            FROM financial_analysis fa
            JOIN stocks s ON fa.stock_id = s.stock_id
            WHERE fa.stock_id = ?
            ORDER BY fa.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_financial_analysis(self, data: Dict[str, Any]) -> bool:
        """新增財報分析

        Args:
            data: 財報分析資料字典

        Returns:
            是否成功
        """
        required_fields = ['stock_id', 'analysis_date']
        for field in required_fields:
            if field not in data:
                safe_print(f"❌ 缺少必要欄位: {field}")
                return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO financial_analysis
                (stock_id, analysis_date, report_period, revenue, revenue_growth,
                 gross_margin, operating_margin, net_margin, roe, roa,
                 debt_to_equity, current_ratio, quick_ratio, interest_coverage,
                 free_cash_flow, cash_flow_growth, earnings_quality,
                 accounting_risks, score, notes, source, source_url, data_as_of)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('report_period', ''), data.get('revenue'),
                data.get('revenue_growth'), data.get('gross_margin'),
                data.get('operating_margin'), data.get('net_margin'),
                data.get('roe'), data.get('roa'),
                data.get('debt_to_equity'), data.get('current_ratio'),
                data.get('quick_ratio'), data.get('interest_coverage'),
                data.get('free_cash_flow'), data.get('cash_flow_growth'),
                data.get('earnings_quality', ''), data.get('accounting_risks', ''),
                data.get('score'), data.get('notes', ''),
                data.get('source', '研報'), data.get('source_url', ''),
                data.get('data_as_of', data['analysis_date'])
            ))

            conn.commit()
            safe_print(f"✅ 新增財報分析: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增財報分析失敗: {e}")
            return False
        finally:
            conn.close()

    def update_financial_analysis(self, stock_id: str, analysis_date: str,
                                 updates: Dict[str, Any]) -> bool:
        """更新財報分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_financial_analysis(self, stock_id: str, analysis_date: str) -> bool:
        """刪除財報分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def get_financial_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """取得財報評分

        Args:
            stock_id: 股票代號

        Returns:
            財報評分字典
        """
        analysis = self.get_financial_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'score': None,
                'rating': '需要人工確認'
            }

        score = analysis.get('score')
        if score is None:
            rating = '需要人工確認'
        elif score >= 80:
            rating = '基本面轉強'
        elif score >= 60:
            rating = '估值合理'
        elif score >= 40:
            rating = '基本面轉弱'
        else:
            rating = '風險升高'

        return {
            'has_analysis': True,
            'score': score,
            'rating': rating,
            'report_period': analysis.get('report_period'),
            'revenue': analysis.get('revenue'),
            'revenue_growth': analysis.get('revenue_growth')
        }

    def analyze_profitability(self, stock_id: str) -> Dict[str, Any]:
        """分析獲利能力

        Args:
            stock_id: 股票代號

        Returns:
            獲利能力分析字典
        """
        analysis = self.get_financial_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無財報分析資料'
            }

        return {
            'has_analysis': True,
            'gross_margin': analysis.get('gross_margin'),
            'operating_margin': analysis.get('operating_margin'),
            'net_margin': analysis.get('net_margin'),
            'roe': analysis.get('roe'),
            'roa': analysis.get('roa')
        }

    def analyze_solvency(self, stock_id: str) -> Dict[str, Any]:
        """分析償債能力

        Args:
            stock_id: 股票代號

        Returns:
            償債能力分析字典
        """
        analysis = self.get_financial_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無財報分析資料'
            }

        return {
            'has_analysis': True,
            'debt_to_equity': analysis.get('debt_to_equity'),
            'current_ratio': analysis.get('current_ratio'),
            'quick_ratio': analysis.get('quick_ratio'),
            'interest_coverage': analysis.get('interest_coverage')
        }

    def analyze_cash_flow(self, stock_id: str) -> Dict[str, Any]:
        """分析現金流

        Args:
            stock_id: 股票代號

        Returns:
            現金流分析字典
        """
        analysis = self.get_financial_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無財報分析資料'
            }

        return {
            'has_analysis': True,
            'free_cash_flow': analysis.get('free_cash_flow'),
            'cash_flow_growth': analysis.get('cash_flow_growth'),
            'earnings_quality': analysis.get('earnings_quality')
        }

    def analyze_financial_trends(self, stock_id: str) -> pd.DataFrame:
        """分析財務趨勢

        Args:
            stock_id: 股票代號

        Returns:
            財務趨勢 DataFrame
        """
        df = self.get_financial_analysis_history(stock_id, limit=8)
        if df.empty:
            return pd.DataFrame()

        # 選取關鍵指標
        trend_cols = ['analysis_date', 'report_period', 'revenue', 'revenue_growth',
                     'gross_margin', 'net_margin', 'roe', 'debt_to_equity']
        available_cols = [col for col in trend_cols if col in df.columns]

        return df[available_cols].sort_values('analysis_date')


# 建立全域實例
financial_analysis_manager = FinancialAnalysisManager()


def get_financial_analysis_manager() -> FinancialAnalysisManager:
    """取得財報分析管理器實例"""
    return financial_analysis_manager