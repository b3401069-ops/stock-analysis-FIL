"""
股票追蹤與決策輔助系統 V1.1 - 投資邏輯模組
Stock Tracking & Decision Support System V1.1 - Investment Thesis Module

處理投資邏輯的查詢、評估與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class InvestmentThesisManager(BaseAnalysisManager):
    """投資邏輯管理器"""

    TABLE = "investment_thesis"
    LABEL = "投資邏輯"

    def get_investment_thesis(self, stock_id: str, analysis_date: str = None) -> Optional[Dict[str, Any]]:
        """取得最新投資邏輯

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            投資邏輯字典，若無則返回 None
        """
        conn = self.get_connection()
        if analysis_date:
            query = """
                SELECT it.*, s.name as stock_name
                FROM investment_thesis it
                JOIN stocks s ON it.stock_id = s.stock_id
                WHERE it.stock_id = ? AND it.analysis_date <= ?
                ORDER BY it.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, analysis_date))
        else:
            query = """
                SELECT it.*, s.name as stock_name
                FROM investment_thesis it
                JOIN stocks s ON it.stock_id = s.stock_id
                WHERE it.stock_id = ?
                ORDER BY it.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_investment_thesis_history(self, stock_id: str,
                                     limit: int = 10) -> pd.DataFrame:
        """取得投資邏輯歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            投資邏輯歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT it.*, s.name as stock_name
            FROM investment_thesis it
            JOIN stocks s ON it.stock_id = s.stock_id
            WHERE it.stock_id = ?
            ORDER BY it.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_investment_thesis(self, data: Dict[str, Any]) -> bool:
        """新增投資邏輯

        Args:
            data: 投資邏輯資料字典

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
                INSERT OR REPLACE INTO investment_thesis
                (stock_id, analysis_date, thesis_summary, buy_reasons,
                 catalysts, target_price, investment_horizon, position_sizing,
                 entry_strategy, exit_strategy, thesis_status, confidence_level,
                 score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('thesis_summary', ''), data.get('buy_reasons', ''),
                data.get('catalysts', ''), data.get('target_price'),
                data.get('investment_horizon', ''), data.get('position_sizing', ''),
                data.get('entry_strategy', ''), data.get('exit_strategy', ''),
                data.get('thesis_status', ''), data.get('confidence_level', ''),
                data.get('score'), data.get('notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增投資邏輯: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增投資邏輯失敗: {e}")
            return False
        finally:
            conn.close()

    def update_investment_thesis(self, stock_id: str, analysis_date: str,
                                updates: Dict[str, Any]) -> bool:
        """更新投資邏輯

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_investment_thesis(self, stock_id: str, analysis_date: str) -> bool:
        """刪除投資邏輯

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def get_thesis_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """取得投資邏輯評分

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            投資邏輯評分字典
        """
        thesis = self.get_investment_thesis(stock_id, analysis_date)
        if not thesis:
            return {
                'has_thesis': False,
                'score': None,
                'status': '需要人工確認'
            }

        score = thesis.get('score')
        thesis_status = thesis.get('thesis_status', '')

        if score is None:
            status = '需要人工確認'
        elif thesis_status:
            status = thesis_status
        elif score >= 80:
            status = '投資邏輯成立'
        elif score >= 60:
            status = '投資邏輯部分成立'
        elif score >= 40:
            status = '投資邏輯待確認'
        else:
            status = '投資邏輯轉弱'

        return {
            'has_thesis': True,
            'score': score,
            'status': status,
            'thesis_summary': thesis.get('thesis_summary'),
            'target_price': thesis.get('target_price'),
            'confidence_level': thesis.get('confidence_level')
        }

    def analyze_thesis_strength(self, stock_id: str) -> Dict[str, Any]:
        """分析投資邏輯強度

        Args:
            stock_id: 股票代號

        Returns:
            投資邏輯強度分析字典
        """
        thesis = self.get_investment_thesis(stock_id)
        if not thesis:
            return {
                'has_thesis': False,
                'message': '無投資邏輯資料'
            }

        return {
            'has_thesis': True,
            'thesis_summary': thesis.get('thesis_summary'),
            'buy_reasons': thesis.get('buy_reasons'),
            'catalysts': thesis.get('catalysts'),
            'thesis_status': thesis.get('thesis_status'),
            'confidence_level': thesis.get('confidence_level')
        }

    def analyze_investment_strategy(self, stock_id: str) -> Dict[str, Any]:
        """分析投資策略

        Args:
            stock_id: 股票代號

        Returns:
            投資策略分析字典
        """
        thesis = self.get_investment_thesis(stock_id)
        if not thesis:
            return {
                'has_thesis': False,
                'message': '無投資邏輯資料'
            }

        return {
            'has_thesis': True,
            'target_price': thesis.get('target_price'),
            'investment_horizon': thesis.get('investment_horizon'),
            'position_sizing': thesis.get('position_sizing'),
            'entry_strategy': thesis.get('entry_strategy'),
            'exit_strategy': thesis.get('exit_strategy')
        }

    def get_thesis_status_trend(self, stock_id: str) -> pd.DataFrame:
        """取得投資邏輯狀態趨勢

        Args:
            stock_id: 股票代號

        Returns:
            投資邏輯狀態趨勢 DataFrame
        """
        df = self.get_investment_thesis_history(stock_id, limit=8)
        if df.empty:
            return pd.DataFrame()

        # 選取關鍵欄位
        trend_cols = ['analysis_date', 'thesis_status', 'confidence_level',
                     'target_price', 'score']
        available_cols = [col for col in trend_cols if col in df.columns]

        return df[available_cols].sort_values('analysis_date')

    def validate_thesis(self, stock_id: str) -> Dict[str, Any]:
        """驗證投資邏輯

        Args:
            stock_id: 股票代號

        Returns:
            投資邏輯驗證結果字典
        """
        thesis = self.get_investment_thesis(stock_id)
        if not thesis:
            return {
                'is_valid': False,
                'message': '無投資邏輯資料',
                'issues': ['缺少投資邏輯分析']
            }

        issues = []

        # 檢查必要欄位
        if not thesis.get('thesis_summary'):
            issues.append('缺少投資邏輯摘要')
        if not thesis.get('buy_reasons'):
            issues.append('缺少買入理由')
        if not thesis.get('target_price'):
            issues.append('缺少目標價')
        if not thesis.get('exit_strategy'):
            issues.append('缺少退出策略')

        # 檢查邏輯完整性
        thesis_status = thesis.get('thesis_status', '')
        if thesis_status == '投資邏輯轉弱':
            issues.append('投資邏輯已轉弱，建議重新評估')

        is_valid = len(issues) == 0

        return {
            'is_valid': is_valid,
            'thesis_status': thesis_status,
            'confidence_level': thesis.get('confidence_level'),
            'issues': issues
        }


# 建立全域實例
investment_thesis_manager = InvestmentThesisManager()


def get_investment_thesis_manager() -> InvestmentThesisManager:
    """取得投資邏輯管理器實例"""
    return investment_thesis_manager