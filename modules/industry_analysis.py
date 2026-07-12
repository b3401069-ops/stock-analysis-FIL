"""
股票追蹤與決策輔助系統 V1.1 - 行業分析模組
Stock Tracking & Decision Support System V1.1 - Industry Analysis Module

處理行業分析的查詢、評估與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class IndustryAnalysisManager(BaseAnalysisManager):
    """行業分析管理器"""

    TABLE = "industry_analysis"
    LABEL = "行業分析"

    def get_industry_analysis(self, stock_id: str, analysis_date: str = None) -> Optional[Dict[str, Any]]:
        """取得最新行業分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            行業分析字典，若無則返回 None
        """
        conn = self.get_connection()
        if analysis_date:
            query = """
                SELECT ia.*, s.name as stock_name
                FROM industry_analysis ia
                JOIN stocks s ON ia.stock_id = s.stock_id
                WHERE ia.stock_id = ? AND ia.analysis_date <= ?
                ORDER BY ia.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, analysis_date))
        else:
            query = """
                SELECT ia.*, s.name as stock_name
                FROM industry_analysis ia
                JOIN stocks s ON ia.stock_id = s.stock_id
                WHERE ia.stock_id = ?
                ORDER BY ia.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_industry_analysis_history(self, stock_id: str,
                                     limit: int = 10) -> pd.DataFrame:
        """取得行業分析歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            行業分析歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT ia.*, s.name as stock_name
            FROM industry_analysis ia
            JOIN stocks s ON ia.stock_id = s.stock_id
            WHERE ia.stock_id = ?
            ORDER BY ia.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_industry_analysis(self, data: Dict[str, Any]) -> bool:
        """新增行業分析

        Args:
            data: 行業分析資料字典

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
                INSERT OR REPLACE INTO industry_analysis
                (stock_id, analysis_date, industry_name, market_size,
                 growth_rate, competition_level, entry_barriers,
                 regulatory_environment, industry_trends, key_drivers,
                 threats, outlook, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('industry_name', ''), data.get('market_size', ''),
                data.get('growth_rate'), data.get('competition_level', ''),
                data.get('entry_barriers', ''), data.get('regulatory_environment', ''),
                data.get('industry_trends', ''), data.get('key_drivers', ''),
                data.get('threats', ''), data.get('outlook', ''),
                data.get('score'), data.get('notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增行業分析: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增行業分析失敗: {e}")
            return False
        finally:
            conn.close()

    def update_industry_analysis(self, stock_id: str, analysis_date: str,
                                updates: Dict[str, Any]) -> bool:
        """更新行業分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_industry_analysis(self, stock_id: str, analysis_date: str) -> bool:
        """刪除行業分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def get_industry_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """取得行業評分

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            行業評分字典
        """
        analysis = self.get_industry_analysis(stock_id, analysis_date)
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
            'industry_name': analysis.get('industry_name'),
            'outlook': analysis.get('outlook')
        }

    def compare_industries(self, stock_ids: list) -> pd.DataFrame:
        """比較多個行業

        Args:
            stock_ids: 股票代號列表

        Returns:
            行業比較 DataFrame
        """
        results = []
        for stock_id in stock_ids:
            analysis = self.get_industry_analysis(stock_id)
            if analysis:
                results.append({
                    'stock_id': stock_id,
                    'stock_name': analysis.get('stock_name'),
                    'industry_name': analysis.get('industry_name'),
                    'growth_rate': analysis.get('growth_rate'),
                    'competition_level': analysis.get('competition_level'),
                    'score': analysis.get('score'),
                    'outlook': analysis.get('outlook')
                })

        return pd.DataFrame(results)

    def get_industry_trends(self, industry_name: str) -> pd.DataFrame:
        """取得行業趨勢

        Args:
            industry_name: 行業名稱

        Returns:
            行業趨勢 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT ia.*, s.stock_id, s.name as stock_name
            FROM industry_analysis ia
            JOIN stocks s ON ia.stock_id = s.stock_id
            WHERE ia.industry_name = ?
            ORDER BY ia.analysis_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(industry_name,))
        conn.close()
        return df


# 建立全域實例
industry_analysis_manager = IndustryAnalysisManager()


def get_industry_analysis_manager() -> IndustryAnalysisManager:
    """取得行業分析管理器實例"""
    return industry_analysis_manager