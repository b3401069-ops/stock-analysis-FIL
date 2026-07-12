"""
股票追蹤與決策輔助系統 V1.1 - 投行觀點模組
Stock Tracking & Decision Support System V1.1 - Analyst Views Module

處理投行研究報告觀點的查詢、分析與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class AnalystViewsManager(BaseAnalysisManager):
    """投行觀點管理器"""

    TABLE = "analyst_views"
    LABEL = "投行觀點"

    def get_analyst_views(self, stock_id: Optional[str] = None,
                         limit: int = 10) -> pd.DataFrame:
        """取得投行觀點

        Args:
            stock_id: 股票代號，若為 None 則取得所有
            limit: 限制筆數

        Returns:
            投行觀點 DataFrame
        """
        conn = self.get_connection()

        if stock_id:
            query = """
                SELECT av.*, s.name as stock_name
                FROM analyst_views av
                JOIN stocks s ON av.stock_id = s.stock_id
                WHERE av.stock_id = ?
                ORDER BY av.report_date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        else:
            query = """
                SELECT av.*, s.name as stock_name
                FROM analyst_views av
                JOIN stocks s ON av.stock_id = s.stock_id
                ORDER BY av.report_date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))

        conn.close()
        return df

    def get_latest_analyst_view(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """取得最新投行觀點

        Args:
            stock_id: 股票代號

        Returns:
            最新投行觀點字典，若無則返回 None
        """
        df = self.get_analyst_views(stock_id, limit=1)
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_views_by_firm(self, stock_id: str,
                         analyst_firm: str) -> pd.DataFrame:
        """按投行取得觀點

        Args:
            stock_id: 股票代號
            analyst_firm: 投行名稱

        Returns:
            投行觀點 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT av.*, s.name as stock_name
            FROM analyst_views av
            JOIN stocks s ON av.stock_id = s.stock_id
            WHERE av.stock_id = ? AND av.analyst_firm = ?
            ORDER BY av.report_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, analyst_firm))
        conn.close()
        return df

    def get_consensus_rating(self, stock_id: str) -> Dict[str, Any]:
        """取得共識評級

        Args:
            stock_id: 股票代號

        Returns:
            共識評級字典
        """
        conn = self.get_connection()
        query = """
            SELECT
                COUNT(*) as total_reports,
                AVG(target_price) as avg_target_price,
                MIN(target_price) as min_target_price,
                MAX(target_price) as max_target_price
            FROM analyst_views
            WHERE stock_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty or df.iloc[0]['total_reports'] == 0:
            return {
                'has_consensus': False,
                'message': '無投行觀點資料'
            }

        row = df.iloc[0]

        def _optional_float(value):
            if value is None or pd.isna(value):
                return None
            return round(float(value), 2)

        # 取得評級分佈
        conn = self.get_connection()
        rating_query = """
            SELECT rating, COUNT(*) as count
            FROM analyst_views
            WHERE stock_id = ?
            GROUP BY rating
            ORDER BY count DESC
        """
        rating_df = pd.read_sql_query(rating_query, conn, params=(stock_id,))
        conn.close()

        rating_distribution = {}
        for _, r in rating_df.iterrows():
            rating_distribution[r['rating']] = int(r['count'])

        return {
            'has_consensus': True,
            'total_reports': int(row['total_reports']),
            'avg_target_price': _optional_float(row['avg_target_price']),
            'min_target_price': _optional_float(row['min_target_price']),
            'max_target_price': _optional_float(row['max_target_price']),
            'rating_distribution': rating_distribution
        }

    def get_target_price_trend(self, stock_id: str,
                              periods: int = 6) -> pd.DataFrame:
        """取得目標價趨勢

        Args:
            stock_id: 股票代號
            periods: 期數

        Returns:
            目標價趨勢 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT report_date, analyst_firm, target_price, previous_target
            FROM analyst_views
            WHERE stock_id = ?
            ORDER BY report_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, periods))
        conn.close()

        if not df.empty:
            # 計算目標價變動
            df['price_change'] = df['target_price'] - df['previous_target']
            df['price_change_pct'] = (df['price_change'] / df['previous_target']) * 100
            df.loc[df['previous_target'].isna() | (df['previous_target'] == 0), 'price_change_pct'] = None

        return df

    def get_research_conclusion_summary(self, stock_id: str) -> Dict[str, Any]:
        """取得研究結論摘要

        Args:
            stock_id: 股票代號

        Returns:
            研究結論摘要字典
        """
        latest = self.get_latest_analyst_view(stock_id)
        if not latest:
            return {
                'has_conclusion': False,
                'message': '無投行研究結論'
            }

        return {
            'has_conclusion': True,
            'analyst_firm': latest.get('analyst_firm'),
            'analyst_name': latest.get('analyst_name'),
            'rating': latest.get('rating'),
            'target_price': latest.get('target_price'),
            'conclusion': latest.get('recommendation'),
            'report_date': latest.get('report_date'),
            'key_findings': latest.get('key_findings'),
            'strengths': latest.get('strengths'),
            'weaknesses': latest.get('weaknesses')
        }

    def add_analyst_view(self, data: Dict[str, Any]) -> bool:
        """新增投行觀點

        Args:
            data: 投行觀點資料字典

        Returns:
            是否成功
        """
        required_fields = ['stock_id', 'report_date', 'analyst_firm']
        for field in required_fields:
            if field not in data:
                safe_print(f"❌ 缺少必要欄位: {field}")
                return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO analyst_views
                (stock_id, report_date, analyst_firm, analyst_name, rating,
                 target_price, previous_target, recommendation, key_findings,
                 strengths, weaknesses, opportunities, threats,
                 financial_estimates, valuation_methodology, risk_factors,
                 catalysts, report_summary, confidence_level, notes,
                 source, source_url, source_type, is_paid_report, summary_only,
                 data_as_of)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['report_date'], data['analyst_firm'],
                data.get('analyst_name', ''), data.get('rating', ''),
                data.get('target_price'), data.get('previous_target'),
                data.get('recommendation', ''), data.get('key_findings', ''),
                data.get('strengths', ''), data.get('weaknesses', ''),
                data.get('opportunities', ''), data.get('threats', ''),
                data.get('financial_estimates', ''), data.get('valuation_methodology', ''),
                data.get('risk_factors', ''), data.get('catalysts', ''),
                data.get('report_summary', ''), data.get('confidence_level', ''),
                data.get('notes', ''),
                data.get('source', '投行研報'), data.get('source_url', ''),
                data.get('source_type', '摘要'),
                1 if data.get('is_paid_report', False) else 0,
                1 if data.get('summary_only', True) else 0,
                data.get('data_as_of', data['report_date'])
            ))

            conn.commit()
            safe_print(f"✅ 新增投行觀點: {data['analyst_firm']} - {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增投行觀點失敗: {e}")
            return False
        finally:
            conn.close()

    def update_analyst_view(self, stock_id: str, report_date: str,
                           analyst_firm: str, updates: Dict[str, Any]) -> bool:
        """更新投行觀點

        Args:
            stock_id: 股票代號
            report_date: 報告日期
            analyst_firm: 投行名稱
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'report_date': report_date, 'analyst_firm': analyst_firm}, updates, f"{analyst_firm} - {stock_id}")

    def delete_analyst_view(self, stock_id: str, report_date: str,
                           analyst_firm: str) -> bool:
        """刪除投行觀點

        Args:
            stock_id: 股票代號
            report_date: 報告日期
            analyst_firm: 投行名稱

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'report_date': report_date, 'analyst_firm': analyst_firm}, f"{analyst_firm} - {stock_id}")

    def search_analyst_views(self, keyword: str) -> pd.DataFrame:
        """搜尋投行觀點

        Args:
            keyword: 搜尋關鍵字

        Returns:
            符合條件的投行觀點 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT av.*, s.name as stock_name
            FROM analyst_views av
            JOIN stocks s ON av.stock_id = s.stock_id
            WHERE av.key_findings LIKE ?
               OR av.strengths LIKE ?
               OR av.weaknesses LIKE ?
               OR av.report_summary LIKE ?
            ORDER BY av.report_date DESC
        """
        pattern = f"%{keyword}%"
        df = pd.read_sql_query(query, conn, params=(pattern, pattern, pattern, pattern))
        conn.close()
        return df

    def get_analyst_coverage(self, stock_id: str) -> pd.DataFrame:
        """取得分析師覆蓋範圍

        Args:
            stock_id: 股票代號

        Returns:
            分析師覆蓋範圍 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT
                analyst_firm,
                analyst_name,
                COUNT(*) as report_count,
                MIN(report_date) as first_report,
                MAX(report_date) as latest_report,
                AVG(target_price) as avg_target_price
            FROM analyst_views
            WHERE stock_id = ?
            GROUP BY analyst_firm, analyst_name
            ORDER BY report_count DESC
        """
        df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()
        return df


# 建立全域實例
analyst_views_manager = AnalystViewsManager()


def get_analyst_views_manager() -> AnalystViewsManager:
    """取得投行觀點管理器實例"""
    return analyst_views_manager
