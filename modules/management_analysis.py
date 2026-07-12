"""
股票追蹤與決策輔助系統 V1.1 - 經營管理層分析模組
Stock Tracking & Decision Support System V1.1 - Management Analysis Module

處理經營管理層分析的查詢、評估與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class ManagementAnalysisManager(BaseAnalysisManager):
    """經營管理層分析管理器"""

    TABLE = "management_analysis"
    LABEL = "經營管理層分析"

    def get_management_analysis(self, stock_id: str, analysis_date: str = None) -> Optional[Dict[str, Any]]:
        """取得最新經營管理層分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            經營管理層分析字典，若無則返回 None
        """
        conn = self.get_connection()
        if analysis_date:
            query = """
                SELECT ma.*, s.name as stock_name
                FROM management_analysis ma
                JOIN stocks s ON ma.stock_id = s.stock_id
                WHERE ma.stock_id = ? AND ma.analysis_date <= ?
                ORDER BY ma.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, analysis_date))
        else:
            query = """
                SELECT ma.*, s.name as stock_name
                FROM management_analysis ma
                JOIN stocks s ON ma.stock_id = s.stock_id
                WHERE ma.stock_id = ?
                ORDER BY ma.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_management_analysis_history(self, stock_id: str,
                                       limit: int = 10) -> pd.DataFrame:
        """取得經營管理層分析歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            經營管理層分析歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT ma.*, s.name as stock_name
            FROM management_analysis ma
            JOIN stocks s ON ma.stock_id = s.stock_id
            WHERE ma.stock_id = ?
            ORDER BY ma.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_management_analysis(self, data: Dict[str, Any]) -> bool:
        """新增經營管理層分析

        Args:
            data: 經營管理層分析資料字典

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
                INSERT OR REPLACE INTO management_analysis
                (stock_id, analysis_date, ceo_name, ceo_background,
                 management_team_size, avg_tenure_years, insider_ownership,
                 major_shareholders, corporate_governance, compensation_structure,
                 track_record, strategic_vision, execution_capability,
                 score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('ceo_name', ''), data.get('ceo_background', ''),
                data.get('management_team_size'), data.get('avg_tenure_years'),
                data.get('insider_ownership'), data.get('major_shareholders', ''),
                data.get('corporate_governance', ''), data.get('compensation_structure', ''),
                data.get('track_record', ''), data.get('strategic_vision', ''),
                data.get('execution_capability', ''), data.get('score'),
                data.get('notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增經營管理層分析: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增經營管理層分析失敗: {e}")
            return False
        finally:
            conn.close()

    def update_management_analysis(self, stock_id: str, analysis_date: str,
                                  updates: Dict[str, Any]) -> bool:
        """更新經營管理層分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_management_analysis(self, stock_id: str, analysis_date: str) -> bool:
        """刪除經營管理層分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def get_management_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """取得經營管理層評分

        Args:
            stock_id: 股票代號

        Returns:
            經營管理層評分字典
        """
        analysis = self.get_management_analysis(stock_id, analysis_date)
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
            'ceo_name': analysis.get('ceo_name'),
            'strategic_vision': analysis.get('strategic_vision')
        }

    def analyze_leadership(self, stock_id: str) -> Dict[str, Any]:
        """分析領導團隊

        Args:
            stock_id: 股票代號

        Returns:
            領導團隊分析字典
        """
        analysis = self.get_management_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無經營管理層分析資料'
            }

        return {
            'has_analysis': True,
            'ceo_name': analysis.get('ceo_name'),
            'ceo_background': analysis.get('ceo_background'),
            'management_team_size': analysis.get('management_team_size'),
            'avg_tenure_years': analysis.get('avg_tenure_years'),
            'insider_ownership': analysis.get('insider_ownership')
        }

    def analyze_corporate_governance(self, stock_id: str) -> Dict[str, Any]:
        """分析公司治理

        Args:
            stock_id: 股票代號

        Returns:
            公司治理分析字典
        """
        analysis = self.get_management_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無經營管理層分析資料'
            }

        return {
            'has_analysis': True,
            'corporate_governance': analysis.get('corporate_governance'),
            'compensation_structure': analysis.get('compensation_structure'),
            'major_shareholders': analysis.get('major_shareholders'),
            'track_record': analysis.get('track_record')
        }


# 建立全域實例
management_analysis_manager = ManagementAnalysisManager()


def get_management_analysis_manager() -> ManagementAnalysisManager:
    """取得經營管理層分析管理器實例"""
    return management_analysis_manager