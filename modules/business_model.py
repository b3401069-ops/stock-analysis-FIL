"""
股票追蹤與決策輔助系統 V1.1 - 商業模式分析模組
Stock Tracking & Decision Support System V1.1 - Business Model Analysis Module

處理商業模式分析的查詢、評估與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class BusinessModelManager(BaseAnalysisManager):
    """商業模式管理器"""

    TABLE = "business_model"
    LABEL = "商業模式分析"

    def get_business_model(self, stock_id: str, analysis_date: str = None) -> Optional[Dict[str, Any]]:
        """取得最新商業模式分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            商業模式分析字典，若無則返回 None
        """
        conn = self.get_connection()
        if analysis_date:
            query = """
                SELECT bm.*, s.name as stock_name
                FROM business_model bm
                JOIN stocks s ON bm.stock_id = s.stock_id
                WHERE bm.stock_id = ? AND bm.analysis_date <= ?
                ORDER BY bm.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, analysis_date))
        else:
            query = """
                SELECT bm.*, s.name as stock_name
                FROM business_model bm
                JOIN stocks s ON bm.stock_id = s.stock_id
                WHERE bm.stock_id = ?
                ORDER BY bm.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_business_model_history(self, stock_id: str,
                                  limit: int = 10) -> pd.DataFrame:
        """取得商業模式分析歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            商業模式分析歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT bm.*, s.name as stock_name
            FROM business_model bm
            JOIN stocks s ON bm.stock_id = s.stock_id
            WHERE bm.stock_id = ?
            ORDER BY bm.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_business_model(self, data: Dict[str, Any]) -> bool:
        """新增商業模式分析

        Args:
            data: 商業模式分析資料字典

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
                INSERT OR REPLACE INTO business_model
                (stock_id, analysis_date, business_model_type, revenue_streams,
                 value_proposition, competitive_advantage, customer_segments,
                 cost_structure, key_partners, scalability, sustainability,
                 score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('business_model_type', ''), data.get('revenue_streams', ''),
                data.get('value_proposition', ''), data.get('competitive_advantage', ''),
                data.get('customer_segments', ''), data.get('cost_structure', ''),
                data.get('key_partners', ''), data.get('scalability', ''),
                data.get('sustainability', ''), data.get('score'),
                data.get('notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增商業模式分析: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增商業模式分析失敗: {e}")
            return False
        finally:
            conn.close()

    def update_business_model(self, stock_id: str, analysis_date: str,
                             updates: Dict[str, Any]) -> bool:
        """更新商業模式分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_business_model(self, stock_id: str, analysis_date: str) -> bool:
        """刪除商業模式分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def get_business_model_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """取得商業模式評分

        Args:
            stock_id: 股票代號

        Returns:
            商業模式評分字典
        """
        analysis = self.get_business_model(stock_id, analysis_date)
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
            'business_model_type': analysis.get('business_model_type'),
            'competitive_advantage': analysis.get('competitive_advantage')
        }

    def analyze_competitive_advantage(self, stock_id: str) -> Dict[str, Any]:
        """分析競爭優勢

        Args:
            stock_id: 股票代號

        Returns:
            競爭優勢分析字典
        """
        analysis = self.get_business_model(stock_id)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無商業模式分析資料'
            }

        return {
            'has_analysis': True,
            'competitive_advantage': analysis.get('competitive_advantage'),
            'value_proposition': analysis.get('value_proposition'),
            'scalability': analysis.get('scalability'),
            'sustainability': analysis.get('sustainability')
        }

    def get_revenue_streams(self, stock_id: str) -> Dict[str, Any]:
        """取得收入來源

        Args:
            stock_id: 股票代號

        Returns:
            收入來源字典
        """
        analysis = self.get_business_model(stock_id)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無商業模式分析資料'
            }

        return {
            'has_analysis': True,
            'revenue_streams': analysis.get('revenue_streams'),
            'business_model_type': analysis.get('business_model_type'),
            'customer_segments': analysis.get('customer_segments')
        }


# 建立全域實例
business_model_manager = BusinessModelManager()


def get_business_model_manager() -> BusinessModelManager:
    """取得商業模式管理器實例"""
    return business_model_manager