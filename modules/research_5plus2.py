"""
股票追蹤與決策輔助系統 V1.1 - 5+2 綜合評估模組
Stock Tracking & Decision Support System V1.1 - 5+2 Research Module

整合 5+2 分析法的綜合評估管理
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class Research5Plus2Manager(BaseAnalysisManager):
    """5+2 綜合評估管理器"""

    TABLE = "research_5plus2"
    LABEL = " 5+2 綜合評估"

    def get_latest_research(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """取得最新 5+2 綜合評估

        Args:
            stock_id: 股票代號

        Returns:
            5+2 綜合評估字典，若無則返回 None
        """
        conn = self.get_connection()
        query = """
            SELECT r.*, s.name as stock_name
            FROM research_5plus2 r
            JOIN stocks s ON r.stock_id = s.stock_id
            WHERE r.stock_id = ?
            ORDER BY r.analysis_date DESC
            LIMIT 1
        """
        df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_research_history(self, stock_id: str,
                            limit: int = 10) -> pd.DataFrame:
        """取得 5+2 綜合評估歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            5+2 綜合評估歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT r.*, s.name as stock_name
            FROM research_5plus2 r
            JOIN stocks s ON r.stock_id = s.stock_id
            WHERE r.stock_id = ?
            ORDER BY r.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_research(self, data: Dict[str, Any]) -> bool:
        """新增 5+2 綜合評估

        Args:
            data: 5+2 綜合評估資料字典

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
                INSERT OR REPLACE INTO research_5plus2
                (stock_id, analysis_date, industry_score, business_model_score,
                 management_score, financial_score, valuation_score,
                 investment_thesis_score, risk_score, total_score,
                 overall_rating, investment_logic, key_strengths, key_weaknesses,
                 action_items, next_review_date, analyst_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('industry_score'), data.get('business_model_score'),
                data.get('management_score'), data.get('financial_score'),
                data.get('valuation_score'), data.get('investment_thesis_score'),
                data.get('risk_score'), data.get('total_score'),
                data.get('overall_rating', ''), data.get('investment_logic', ''),
                data.get('key_strengths', ''), data.get('key_weaknesses', ''),
                data.get('action_items', ''), data.get('next_review_date'),
                data.get('analyst_notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增 5+2 綜合評估: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增 5+2 綜合評估失敗: {e}")
            return False
        finally:
            conn.close()

    def update_research(self, stock_id: str, analysis_date: str,
                       updates: Dict[str, Any]) -> bool:
        """更新 5+2 綜合評估

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_research(self, stock_id: str, analysis_date: str) -> bool:
        """刪除 5+2 綜合評估

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def calculate_total_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """計算總評分

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為當前日期）

        Returns:
            總評分字典
        """
        from modules.industry_analysis import get_industry_analysis_manager
        from modules.business_model import get_business_model_manager
        from modules.management_analysis import get_management_analysis_manager
        from modules.financial_analysis import get_financial_analysis_manager
        from modules.valuation import get_valuation_analysis_manager
        from modules.investment_thesis import get_investment_thesis_manager
        from modules.risk_analysis import get_risk_analysis_manager

        # 設定 as-of 日期
        if analysis_date is None:
            from datetime import datetime
            analysis_date = datetime.now().strftime('%Y-%m-%d')

        # 取得各模組評分（使用 as-of 日期篩選）
        industry_score = get_industry_analysis_manager().get_industry_score(stock_id, analysis_date).get('score')
        business_score = get_business_model_manager().get_business_model_score(stock_id, analysis_date).get('score')
        management_score = get_management_analysis_manager().get_management_score(stock_id, analysis_date).get('score')
        financial_score = get_financial_analysis_manager().get_financial_score(stock_id, analysis_date).get('score')
        valuation_score = get_valuation_analysis_manager().get_valuation_score(stock_id, analysis_date).get('score')
        thesis_score = get_investment_thesis_manager().get_thesis_score(stock_id, analysis_date).get('score')
        risk_score = get_risk_analysis_manager().get_risk_score(stock_id, analysis_date).get('score')

        # 計算總分（加權平均）
        weights = self.config.RESEARCH_5PLUS2_WEIGHTS
        scores = [
            (industry_score, weights.get('industry_analysis', 0.15)),
            (business_score, weights.get('business_model', 0.15)),
            (management_score, weights.get('management_analysis', 0.15)),
            (financial_score, weights.get('financial_analysis', 0.15)),
            (valuation_score, weights.get('valuation', 0.15)),
            (thesis_score, weights.get('investment_thesis', 0.15)),
            (risk_score, weights.get('risk_analysis', 0.10))
        ]

        valid_scores = [(score, weight) for score, weight in scores if score is not None]

        if not valid_scores:
            return {
                'has_data': False,
                'total_score': None,
                'message': '無足夠評分資料'
            }

        # 計算加權平均
        total_weight = sum(weight for _, weight in valid_scores)
        weighted_sum = sum(score * weight for score, weight in valid_scores)
        total_score = weighted_sum / total_weight if total_weight > 0 else 0

        # 決定投資邏輯狀態
        thresholds = self.config.RESEARCH_5PLUS2_THRESHOLDS
        if total_score >= thresholds.get('investment_logic_established', 80):
            investment_logic = '投資邏輯成立'
        elif total_score >= thresholds.get('investment_logic_partial', 60):
            investment_logic = '投資邏輯部分成立'
        elif total_score >= thresholds.get('investment_logic_pending', 40):
            investment_logic = '投資邏輯待確認'
        else:
            investment_logic = '投資邏輯轉弱'

        return {
            'has_data': True,
            'total_score': round(total_score, 1),
            'investment_logic': investment_logic,
            'industry_score': industry_score,
            'business_score': business_score,
            'management_score': management_score,
            'financial_score': financial_score,
            'valuation_score': valuation_score,
            'thesis_score': thesis_score,
            'risk_score': risk_score
        }

    def generate_research_report(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """產生研究報告

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            研究報告字典
        """
        # 取得最新評估
        research = self.get_latest_research(stock_id)
        if not research:
            return {
                'has_report': False,
                'message': '無 5+2 綜合評估資料'
            }

        # 使用評估日期作為 as-of 日期（避免 look-ahead）
        if analysis_date is None:
            analysis_date = research.get('analysis_date')

        # 取得評分計算（使用 as-of 日期）
        score_calc = self.calculate_total_score(stock_id, analysis_date)

        # 產生報告摘要
        report = {
            'has_report': True,
            'stock_id': stock_id,
            'stock_name': research.get('stock_name'),
            'analysis_date': research.get('analysis_date'),
            'total_score': research.get('total_score'),
            'overall_rating': research.get('overall_rating'),
            'investment_logic': research.get('investment_logic'),
            'key_strengths': research.get('key_strengths'),
            'key_weaknesses': research.get('key_weaknesses'),
            'score_breakdown': score_calc
        }

        return report

    def compare_stocks(self, stock_ids: list) -> pd.DataFrame:
        """比較多個股票

        Args:
            stock_ids: 股票代號列表

        Returns:
            股票比較 DataFrame
        """
        results = []
        for stock_id in stock_ids:
            research = self.get_latest_research(stock_id)
            if research:
                results.append({
                    'stock_id': stock_id,
                    'stock_name': research.get('stock_name'),
                    'analysis_date': research.get('analysis_date'),
                    'total_score': research.get('total_score'),
                    'overall_rating': research.get('overall_rating'),
                    'investment_logic': research.get('investment_logic')
                })

        return pd.DataFrame(results)


# 建立全域實例
research_5plus2_manager = Research5Plus2Manager()


def get_research_5plus2_manager() -> Research5Plus2Manager:
    """取得 5+2 綜合評估管理器實例"""
    return research_5plus2_manager