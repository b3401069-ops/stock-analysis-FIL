"""
股票追蹤與決策輔助系統 V1.1 - 風險分析模組
Stock Tracking & Decision Support System V1.1 - Risk Analysis Module

處理風險分析的查詢、評估與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class RiskAnalysisManager(BaseAnalysisManager):
    """風險分析管理器"""

    TABLE = "risk_analysis"
    LABEL = "風險分析"

    def get_risk_analysis(self, stock_id: str, analysis_date: str = None) -> Optional[Dict[str, Any]]:
        """取得最新風險分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期，用於 as-of 篩選（預設為最新評估日期）

        Returns:
            風險分析字典，若無則返回 None
        """
        conn = self.get_connection()
        if analysis_date:
            query = """
                SELECT ra.*, s.name as stock_name
                FROM risk_analysis ra
                JOIN stocks s ON ra.stock_id = s.stock_id
                WHERE ra.stock_id = ? AND ra.analysis_date <= ?
                ORDER BY ra.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id, analysis_date))
        else:
            query = """
                SELECT ra.*, s.name as stock_name
                FROM risk_analysis ra
                JOIN stocks s ON ra.stock_id = s.stock_id
                WHERE ra.stock_id = ?
                ORDER BY ra.analysis_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(stock_id,))
        conn.close()

        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_risk_analysis_history(self, stock_id: str,
                                 limit: int = 10) -> pd.DataFrame:
        """取得風險分析歷史

        Args:
            stock_id: 股票代號
            limit: 限制筆數

        Returns:
            風險分析歷史 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT ra.*, s.name as stock_name
            FROM risk_analysis ra
            JOIN stocks s ON ra.stock_id = s.stock_id
            WHERE ra.stock_id = ?
            ORDER BY ra.analysis_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(stock_id, limit))
        conn.close()
        return df

    def add_risk_analysis(self, data: Dict[str, Any]) -> bool:
        """新增風險分析

        Args:
            data: 風險分析資料字典

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
                INSERT OR REPLACE INTO risk_analysis
                (stock_id, analysis_date, business_risks, financial_risks,
                 market_risks, regulatory_risks, competitive_risks,
                 management_risks, liquidity_risks, currency_risks,
                 geopolitical_risks, black_swan_risks, risk_mitigation,
                 overall_risk_level, risk_rating, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_id'], data['analysis_date'],
                data.get('business_risks', ''), data.get('financial_risks', ''),
                data.get('market_risks', ''), data.get('regulatory_risks', ''),
                data.get('competitive_risks', ''), data.get('management_risks', ''),
                data.get('liquidity_risks', ''), data.get('currency_risks', ''),
                data.get('geopolitical_risks', ''), data.get('black_swan_risks', ''),
                data.get('risk_mitigation', ''), data.get('overall_risk_level', ''),
                data.get('risk_rating', ''), data.get('score'),
                data.get('notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增風險分析: {data['stock_id']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增風險分析失敗: {e}")
            return False
        finally:
            conn.close()

    def update_risk_analysis(self, stock_id: str, analysis_date: str,
                            updates: Dict[str, Any]) -> bool:
        """更新風險分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'stock_id': stock_id, 'analysis_date': analysis_date}, updates, stock_id)

    def delete_risk_analysis(self, stock_id: str, analysis_date: str) -> bool:
        """刪除風險分析

        Args:
            stock_id: 股票代號
            analysis_date: 分析日期

        Returns:
            是否成功
        """
        return self._delete_row({'stock_id': stock_id, 'analysis_date': analysis_date}, stock_id)

    def get_risk_score(self, stock_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """取得風險評分

        Args:
            stock_id: 股票代號

        Returns:
            風險評分字典
        """
        analysis = self.get_risk_analysis(stock_id, analysis_date)
        if not analysis:
            return {
                'has_analysis': False,
                'score': None,
                'rating': '需要人工確認'
            }

        score = analysis.get('score')
        risk_rating = analysis.get('risk_rating', '')

        if score is None:
            rating = '需要人工確認'
        elif risk_rating:
            rating = risk_rating
        elif score >= 80:
            rating = '風險較低'
        elif score >= 60:
            rating = '風險中等'
        elif score >= 40:
            rating = '風險升高'
        else:
            rating = '風險較高'

        return {
            'has_analysis': True,
            'score': score,
            'rating': rating,
            'overall_risk_level': analysis.get('overall_risk_level'),
            'risk_mitigation': analysis.get('risk_mitigation')
        }

    def analyze_business_risks(self, stock_id: str) -> Dict[str, Any]:
        """分析業務風險

        Args:
            stock_id: 股票代號

        Returns:
            業務風險分析字典
        """
        analysis = self.get_risk_analysis(stock_id)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無風險分析資料'
            }

        return {
            'has_analysis': True,
            'business_risks': analysis.get('business_risks'),
            'competitive_risks': analysis.get('competitive_risks'),
            'market_risks': analysis.get('market_risks')
        }

    def analyze_financial_risks(self, stock_id: str) -> Dict[str, Any]:
        """分析財務風險

        Args:
            stock_id: 股票代號

        Returns:
            財務風險分析字典
        """
        analysis = self.get_risk_analysis(stock_id)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無風險分析資料'
            }

        return {
            'has_analysis': True,
            'financial_risks': analysis.get('financial_risks'),
            'liquidity_risks': analysis.get('liquidity_risks'),
            'currency_risks': analysis.get('currency_risks')
        }

    def analyze_external_risks(self, stock_id: str) -> Dict[str, Any]:
        """分析外部風險

        Args:
            stock_id: 股票代號

        Returns:
            外部風險分析字典
        """
        analysis = self.get_risk_analysis(stock_id)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無風險分析資料'
            }

        return {
            'has_analysis': True,
            'regulatory_risks': analysis.get('regulatory_risks'),
            'geopolitical_risks': analysis.get('geopolitical_risks'),
            'black_swan_risks': analysis.get('black_swan_risks')
        }

    def analyze_management_risks(self, stock_id: str) -> Dict[str, Any]:
        """分析管理層風險

        Args:
            stock_id: 股票代號

        Returns:
            管理層風險分析字典
        """
        analysis = self.get_risk_analysis(stock_id)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無風險分析資料'
            }

        return {
            'has_analysis': True,
            'management_risks': analysis.get('management_risks'),
            'risk_mitigation': analysis.get('risk_mitigation')
        }

    def get_risk_heatmap(self, stock_id: str) -> Dict[str, Any]:
        """取得風險熱力圖

        Args:
            stock_id: 股票代號

        Returns:
            風險熱力圖字典
        """
        analysis = self.get_risk_analysis(stock_id)
        if not analysis:
            return {
                'has_analysis': False,
                'message': '無風險分析資料'
            }

        # 定義風險類別和對應欄位
        risk_categories = {
            '業務風險': 'business_risks',
            '財務風險': 'financial_risks',
            '市場風險': 'market_risks',
            '監管風險': 'regulatory_risks',
            '競爭風險': 'competitive_risks',
            '管理層風險': 'management_risks',
            '流動性風險': 'liquidity_risks',
            '匯率風險': 'currency_risks',
            '地緣政治風險': 'geopolitical_risks',
            '黑天鵝風險': 'black_swan_risks'
        }

        heatmap_data = {}
        for category, field in risk_categories.items():
            risk_value = analysis.get(field, '')
            # 簡單的風險等級評估
            if not risk_value:
                level = '未知'
            elif '低' in risk_value or '較低' in risk_value:
                level = '低'
            elif '中' in risk_value or '中等' in risk_value:
                level = '中'
            elif '高' in risk_value or '較高' in risk_value:
                level = '高'
            else:
                level = '待評估'

            heatmap_data[category] = {
                'description': risk_value,
                'level': level
            }

        return {
            'has_analysis': True,
            'overall_risk_level': analysis.get('overall_risk_level'),
            'risk_rating': analysis.get('risk_rating'),
            'heatmap': heatmap_data
        }

    def get_risk_trend(self, stock_id: str) -> pd.DataFrame:
        """取得風險趨勢

        Args:
            stock_id: 股票代號

        Returns:
            風險趨勢 DataFrame
        """
        df = self.get_risk_analysis_history(stock_id, limit=8)
        if df.empty:
            return pd.DataFrame()

        # 選取關鍵欄位
        trend_cols = ['analysis_date', 'overall_risk_level', 'risk_rating',
                     'score']
        available_cols = [col for col in trend_cols if col in df.columns]

        return df[available_cols].sort_values('analysis_date')

    def compare_risk_profiles(self, stock_ids: list) -> pd.DataFrame:
        """比較多個股票的風險概況

        Args:
            stock_ids: 股票代號列表

        Returns:
            風險概況比較 DataFrame
        """
        results = []
        for stock_id in stock_ids:
            analysis = self.get_risk_analysis(stock_id)
            if analysis:
                results.append({
                    'stock_id': stock_id,
                    'stock_name': analysis.get('stock_name'),
                    'overall_risk_level': analysis.get('overall_risk_level'),
                    'risk_rating': analysis.get('risk_rating'),
                    'score': analysis.get('score')
                })

        return pd.DataFrame(results)


# 建立全域實例
risk_analysis_manager = RiskAnalysisManager()


def get_risk_analysis_manager() -> RiskAnalysisManager:
    """取得風險分析管理器實例"""
    return risk_analysis_manager