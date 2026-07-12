"""
股票追蹤與決策輔助系統 V1.1 - 總體經濟分析模組
Stock Tracking & Decision Support System V1.1 - Macro Analysis Module

處理總體經濟指標的查詢、分析與儲存
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from modules.config import get_config
from modules.console import safe_print
from modules.base_manager import BaseAnalysisManager


class MacroAnalysisManager(BaseAnalysisManager):
    """總體經濟分析管理器"""

    TABLE = "macro_indicators"
    LABEL = "總體經濟指標"

    def get_macro_indicators(self, indicator_name: Optional[str] = None,
                            region: Optional[str] = None,
                            limit: int = 100) -> pd.DataFrame:
        """取得總體經濟指標

        Args:
            indicator_name: 指標名稱，若為 None 則取得所有
            region: 區域，若為 None 則取得所有
            limit: 限制筆數

        Returns:
            總體經濟指標 DataFrame
        """
        conn = self.get_connection()

        conditions = []
        params = []

        if indicator_name:
            conditions.append("indicator_name = ?")
            params.append(indicator_name)

        if region:
            conditions.append("region = ?")
            params.append(region)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT *
            FROM macro_indicators
            WHERE {where_clause}
            ORDER BY indicator_date DESC
            LIMIT ?
        """
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def get_latest_macro_indicators(self, region: Optional[str] = None) -> pd.DataFrame:
        """取得最新總體經濟指標

        Args:
            region: 區域，若為 None 則取得所有

        Returns:
            最新總體經濟指標 DataFrame
        """
        conn = self.get_connection()

        if region:
            query = """
                SELECT mi.*
                FROM macro_indicators mi
                INNER JOIN (
                    SELECT indicator_name, MAX(indicator_date) as max_date
                    FROM macro_indicators
                    WHERE region = ?
                    GROUP BY indicator_name
                ) latest ON mi.indicator_name = latest.indicator_name
                        AND mi.indicator_date = latest.max_date
                        AND mi.region = ?
                ORDER BY mi.indicator_name
            """
            df = pd.read_sql_query(query, conn, params=(region, region))
        else:
            query = """
                SELECT mi.*
                FROM macro_indicators mi
                INNER JOIN (
                    SELECT indicator_name, MAX(indicator_date) as max_date
                    FROM macro_indicators
                    GROUP BY indicator_name
                ) latest ON mi.indicator_name = latest.indicator_name
                        AND mi.indicator_date = latest.max_date
                ORDER BY mi.indicator_name
            """
            df = pd.read_sql_query(query, conn)

        conn.close()
        return df

    def add_macro_indicator(self, data: Dict[str, Any]) -> bool:
        """新增總體經濟指標

        Args:
            data: 總體經濟指標資料字典

        Returns:
            是否成功
        """
        required_fields = ['indicator_name', 'indicator_date', 'value']
        for field in required_fields:
            if field not in data:
                safe_print(f"❌ 缺少必要欄位: {field}")
                return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO macro_indicators
                (indicator_name, indicator_date, value, unit, region,
                 source, frequency, previous_value, change, trend,
                 impact_assessment, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['indicator_name'], data['indicator_date'],
                data['value'], data.get('unit', ''),
                data.get('region', ''), data.get('source', ''),
                data.get('frequency', ''), data.get('previous_value'),
                data.get('change'), data.get('trend', ''),
                data.get('impact_assessment', ''), data.get('notes', '')
            ))

            conn.commit()
            safe_print(f"✅ 新增總體經濟指標: {data['indicator_name']}")
            return True

        except Exception as e:
            safe_print(f"❌ 新增總體經濟指標失敗: {e}")
            return False
        finally:
            conn.close()

    def update_macro_indicator(self, indicator_name: str, indicator_date: str,
                              region: str, updates: Dict[str, Any]) -> bool:
        """更新總體經濟指標

        Args:
            indicator_name: 指標名稱
            indicator_date: 指標日期
            region: 區域
            updates: 更新資料字典

        Returns:
            是否成功
        """
        return self._update_row({'indicator_name': indicator_name, 'indicator_date': indicator_date, 'region': region}, updates, indicator_name)

    def delete_macro_indicator(self, indicator_name: str, indicator_date: str,
                              region: str) -> bool:
        """刪除總體經濟指標

        Args:
            indicator_name: 指標名稱
            indicator_date: 指標日期
            region: 區域

        Returns:
            是否成功
        """
        return self._delete_row({'indicator_name': indicator_name, 'indicator_date': indicator_date, 'region': region}, indicator_name)

    def get_indicator_trend(self, indicator_name: str, region: str,
                           periods: int = 12) -> pd.DataFrame:
        """取得指標趨勢

        Args:
            indicator_name: 指標名稱
            region: 區域
            periods: 期數

        Returns:
            指標趨勢 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT indicator_date, value, change, trend
            FROM macro_indicators
            WHERE indicator_name = ? AND region = ?
            ORDER BY indicator_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(indicator_name, region, periods))
        conn.close()

        if not df.empty:
            df = df.sort_values('indicator_date')

        return df

    def get_macro_dashboard_data(self, region: str) -> Dict[str, Any]:
        """取得宏觀 Dashboard 資料

        Args:
            region: 區域

        Returns:
            宏觀 Dashboard 資料字典
        """
        # 取得最新指標
        latest = self.get_latest_macro_indicators(region)

        if latest.empty:
            return {
                'has_data': False,
                'message': '無總體經濟資料'
            }

        # 分類指標
        categories = {}
        for _, row in latest.iterrows():
            category = self._categorize_indicator(row['indicator_name'])
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'name': row['indicator_name'],
                'value': row['value'],
                'unit': row['unit'],
                'change': row['change'],
                'trend': row['trend'],
                'date': row['indicator_date']
            })

        return {
            'has_data': True,
            'region': region,
            'update_date': latest['indicator_date'].max(),
            'categories': categories
        }

    def _categorize_indicator(self, indicator_name: str) -> str:
        """分類指標

        Args:
            indicator_name: 指標名稱

        Returns:
            指標類別
        """
        indicator_lower = indicator_name.lower()

        if any(keyword in indicator_lower for keyword in ['gdp', '國內生產毛額']):
            return '經濟成長'
        elif any(keyword in indicator_lower for keyword in ['cpi', '消費者物價', '通膨', 'inflation']):
            return '物價指數'
        elif any(keyword in indicator_lower for keyword in ['利率', 'interest', 'rate']):
            return '利率政策'
        elif any(keyword in indicator_lower for keyword in ['失業', 'unemployment', '就業']):
            return '就業市場'
        elif any(keyword in indicator_lower for keyword in ['出口', 'import', 'export', '貿易']):
            return '貿易數據'
        elif any(keyword in indicator_lower for keyword in ['pmi', '採購經理']):
            return '景氣指標'
        elif any(keyword in indicator_lower for keyword in ['股市', 'stock', '指數']):
            return '金融市場'
        else:
            return '其他'

    def analyze_macro_environment(self, region: str) -> Dict[str, Any]:
        """分析總體經濟環境

        Args:
            region: 區域

        Returns:
            總體經濟環境分析字典
        """
        latest = self.get_latest_macro_indicators(region)

        if latest.empty:
            return {
                'has_analysis': False,
                'message': '無總體經濟資料'
            }

        # 分析關鍵指標
        key_indicators = {}
        for _, row in latest.iterrows():
            key_indicators[row['indicator_name']] = {
                'value': row['value'],
                'change': row['change'],
                'trend': row['trend'],
                'impact': row['impact_assessment']
            }

        # 評估整體環境
        positive_count = sum(1 for ind in key_indicators.values()
                           if ind.get('trend') in ['上升', '改善', '正面'])
        negative_count = sum(1 for ind in key_indicators.values()
                           if ind.get('trend') in ['下降', '惡化', '負面'])

        if positive_count > negative_count:
            overall_assessment = '經濟環境正面'
        elif negative_count > positive_count:
            overall_assessment = '經濟環境負面'
        else:
            overall_assessment = '經濟環境中性'

        return {
            'has_analysis': True,
            'region': region,
            'overall_assessment': overall_assessment,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'key_indicators': key_indicators
        }

    def get_regional_comparison(self, indicator_name: str,
                               regions: List[str]) -> pd.DataFrame:
        """比較區域指標

        Args:
            indicator_name: 指標名稱
            regions: 區域列表

        Returns:
            區域比較 DataFrame
        """
        conn = self.get_connection()

        results = []
        for region in regions:
            query = """
                SELECT *
                FROM macro_indicators
                WHERE indicator_name = ? AND region = ?
                ORDER BY indicator_date DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(indicator_name, region))
            if not df.empty:
                results.append(df.iloc[0].to_dict())

        conn.close()
        return pd.DataFrame(results)

    def search_macro_indicators(self, keyword: str) -> pd.DataFrame:
        """搜尋總體經濟指標

        Args:
            keyword: 搜尋關鍵字

        Returns:
            符合條件的總體經濟指標 DataFrame
        """
        conn = self.get_connection()
        query = """
            SELECT *
            FROM macro_indicators
            WHERE indicator_name LIKE ?
               OR notes LIKE ?
               OR impact_assessment LIKE ?
            ORDER BY indicator_date DESC
        """
        pattern = f"%{keyword}%"
        df = pd.read_sql_query(query, conn, params=(pattern, pattern, pattern))
        conn.close()
        return df

    def get_available_indicators(self, region: Optional[str] = None) -> List[str]:
        """取得可用指標列表

        Args:
            region: 區域，若為 None 則取得所有

        Returns:
            指標名稱列表
        """
        conn = self.get_connection()
        if region:
            query = """
                SELECT DISTINCT indicator_name
                FROM macro_indicators
                WHERE region = ?
                ORDER BY indicator_name
            """
            df = pd.read_sql_query(query, conn, params=(region,))
        else:
            query = """
                SELECT DISTINCT indicator_name
                FROM macro_indicators
                ORDER BY indicator_name
            """
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df['indicator_name'].tolist()

    def get_common_indicators(self, regions: List[str]) -> List[str]:
        """取得所有指定區域共有的指標名稱"""
        if not regions:
            return self.get_available_indicators()
        conn = self.get_connection()
        placeholders = ','.join(['?'] * len(regions))
        query = f"""
            SELECT indicator_name
            FROM macro_indicators
            WHERE region IN ({placeholders})
            GROUP BY indicator_name
            HAVING COUNT(DISTINCT region) = ?
            ORDER BY indicator_name
        """
        params = regions + [len(regions)]
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df['indicator_name'].tolist()

    def get_available_regions(self) -> List[str]:
        """取得可用區域列表

        Returns:
            區域名稱列表
        """
        conn = self.get_connection()
        query = """
            SELECT DISTINCT region
            FROM macro_indicators
            WHERE region IS NOT NULL AND region != ''
            ORDER BY region
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df['region'].tolist()


# 建立全域實例
macro_analysis_manager = MacroAnalysisManager()


def get_macro_analysis_manager() -> MacroAnalysisManager:
    """取得總體經濟分析管理器實例"""
    return macro_analysis_manager
