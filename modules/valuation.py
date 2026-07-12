"""
股票追蹤與決策輔助系統 V1.1 - 公司估值分析模組
Stock Tracking & Decision Support System V1.1 - Valuation Analysis Module

處理公司估值分析的查詢、評估與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class ValuationAnalysisManager(BaseAnalysisManager):
    """公司估值分析管理器"""

    TABLE = "valuation_analysis"
    LABEL = "估值分析"

    def get_valuation_analysis(self, stock_id: str, analysis_date: str = None) -> Optional[Dict[str, Any]]:
        """取得最新估值分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            估值分析字典，若無則返回 None
        """
        conn = self.get_connection()
        if analysis_date:
            query = """
                SELECT va.*, s.name as stock_name
                FROM valuation_analysis va
                JOIN stocks s ON va.stock_id = s.stock_id
                WHERE va.stock_id = ? AND va.analysis_date <= ?
                ORDER BY va.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, analysis_date))
        else:
            query = """
                SELECT va.*, s.name as stock_name
                FROM valuation_analysis va
                JOIN stocks s ON va.stock_id = s.stock_id
                WHERE va.stock_id = ?
                ORDER BY va.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_valuation_analysis_history(self, stock_id: str,
                                      limit: int = 10) -> pd.DataFrame:
        """取得估值分析歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            估值分析歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT va.*, s.name as stock_name
            FROM valuation_analysis va
            JOIN stocks s ON va.stock_id = s.stock_id
            WHERE va.stock_id = ?
            ORDER BY va.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_valuation_analysis(self, data: Dict[str, Any]) -> bool:
        """新增估值分析

        Args:
            data: 估值分析資料字典

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
                INSERT OR REPLACE INTO valuation_analysis
                (stock_id, analysis_date, current_price, pe_ratio, pb_ratio,
                 ps_ratio, pcf_ratio, ev_ebitda, peg_ratio, dividend_yield,
                 dcf_value, relative_value, historical_avg_pe, industry_avg_pe,
                 margin_of_safety, valuation_rating, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('current_price'), data.get('pe_ratio'),
                data.get('pb_ratio'), data.get('ps_ratio'),
                data.get('pcf_ratio'), data.get('ev_ebitda'),
                data.get('peg_ratio'), data.get('dividend_yield'),
                data.get('dcf_value'), data.get('relative_value'),
                data.get('historical_avg_pe'), data.get('industry_avg_pe'),
                data.get('margin_of_safety'), data.get('valuation_rating', ''),
                data.get('score'), data.get('notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增估值分析: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增估值分析失敗: {e}")
            return False
        finally:
            conn.close()

    def update_valuation_analysis(self, stock_id: str, analysis_date: str,
                                 updates: Dict[str, Any]) -> bool:
        """更新估值分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_valuation_analysis(self, stock_id: str, analysis_date: str) -> bool:
        """刪除估值分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def get_valuation_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """取得估值評分

        Args:
            stock_id: 股票代號

        Returns:
            估值評分字典
        """
        analysis = self.get_valuation_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'score': None,
                'rating': '需要人工確認'
            }

        score = analysis.get('score')
        valuation_rating = analysis.get('valuation_rating', '')

        if score is None:
            rating = '需要人工確認'
        elif valuation_rating:
            rating = valuation_rating
        elif score >= 80:
            rating = '估值偏低'
        elif score >= 60:
            rating = '估值合理'
        elif score >= 40:
            rating = '估值偏高'
        else:
            rating = '估值過高'

        return {
            'has_analysis': True,
            'score': score,
            'rating': rating,
            'current_price': analysis.get('current_price'),
            'pe_ratio': analysis.get('pe_ratio'),
            'pb_ratio': analysis.get('pb_ratio'),
            'dcf_value': analysis.get('dcf_value'),
            'margin_of_safety': analysis.get('margin_of_safety')
        }

    def analyze_relative_valuation(self, stock_id: str) -> Dict[str, Any]:
        """分析相對估值

        Args:
            stock_id: 股票代號

        Returns:
            相對估值分析字典
        """
        analysis = self.get_valuation_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無估值分析資料'
            }

        return {
            'has_analysis': True,
            'pe_ratio': analysis.get('pe_ratio'),
            'pb_ratio': analysis.get('pb_ratio'),
            'ps_ratio': analysis.get('ps_ratio'),
            'ev_ebitda': analysis.get('ev_ebitda'),
            'peg_ratio': analysis.get('peg_ratio'),
            'historical_avg_pe': analysis.get('historical_avg_pe'),
            'industry_avg_pe': analysis.get('industry_avg_pe')
        }

    def analyze_absolute_valuation(self, stock_id: str) -> Dict[str, Any]:
        """分析絕對估值

        Args:
            stock_id: 股票代號

        Returns:
            絕對估值分析字典
        """
        analysis = self.get_valuation_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無估值分析資料'
            }

        return {
            'has_analysis': True,
            'current_price': analysis.get('current_price'),
            'dcf_value': analysis.get('dcf_value'),
            'relative_value': analysis.get('relative_value'),
            'margin_of_safety': analysis.get('margin_of_safety'),
            'dividend_yield': analysis.get('dividend_yield')
        }

    def calculate_margin_of_safety(self, stock_id: str) -> Dict[str, Any]:
        """計算安全邊際

        Args:
            stock_id: 股票代號

        Returns:
            安全邊際分析字典
        """
        analysis = self.get_valuation_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無估值分析資料'
            }

        current_price = analysis.get('current_price')
        dcf_value = analysis.get('dcf_value')
        margin_of_safety = analysis.get('margin_of_safety')

        if current_price and dcf_value:
            # 重新計算安全邊際
            calculated_margin = ((dcf_value - current_price) / dcf_value) * 100
        else:
            calculated_margin = margin_of_safety

        if calculated_margin is None:
            rating = '需要人工確認'
        elif calculated_margin >= 30:
            rating = '估值偏低'
        elif calculated_margin >= 10:
            rating = '估值合理'
        elif calculated_margin >= 0:
            rating = '估值偏高'
        else:
            rating = '估值過高'

        return {
            'has_analysis': True,
            'current_price': current_price,
            'dcf_value': dcf_value,
            'margin_of_safety': calculated_margin,
            'rating': rating
        }

    def get_valuation_comparison(self, stock_ids: list) -> pd.DataFrame:
        """比較多個股票的估值

        Args:
            stock_ids: 股票代號列表

        Returns:
            估值比較 DataFrame
        """
        results = []
        for stock_id in stock_ids:
            analysis = self.get_valuation_analysis(stock_id, analysis_date)
            if analysis:
                results.append({
                    'stock_id': stock_id,
                    'stock_name': analysis.get('stock_name'),
                    'current_price': analysis.get('current_price'),
                    'pe_ratio': analysis.get('pe_ratio'),
                    'pb_ratio': analysis.get('pb_ratio'),
                    'dividend_yield': analysis.get('dividend_yield'),
                    'margin_of_safety': analysis.get('margin_of_safety'),
                    'valuation_rating': analysis.get('valuation_rating')
                })

        return pd.DataFrame(results)


# 建立全域實例
valuation_analysis_manager = ValuationAnalysisManager()


def get_valuation_analysis_manager() -> ValuationAnalysisManager:
    """取得公司估值分析管理器實例"""
    return valuation_analysis_manager