"""
總體經濟分析模組測試
Macro Analysis Module Tests
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

# 導入被測模組
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.macro_analysis import MacroAnalysisManager, get_macro_analysis_manager


@pytest.fixture
def temp_db(tmp_path):
    """建立臨時資料庫"""
    db_path = tmp_path / "test_macro.db"

    # 建立基礎資料表
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS macro_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_name TEXT NOT NULL,
            indicator_date DATE NOT NULL,
            value REAL,
            unit TEXT,
            region TEXT,
            source TEXT,
            frequency TEXT,
            previous_value REAL,
            change REAL,
            trend TEXT,
            impact_assessment TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_name, indicator_date, region)
        )
    """)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def macro_manager(temp_db, monkeypatch):
    """建立總體經濟分析管理器"""
    # Mock config
    class MockConfig:
        DATABASE_PATH = str(temp_db)

    def mock_get_config():
        return MockConfig()

    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)

    manager = MacroAnalysisManager()
    return manager


class TestMacroAnalysisManager:
    """總體經濟分析管理器測試類別"""

    def test_initialization(self, macro_manager):
        """測試初始化"""
        assert macro_manager is not None
        assert macro_manager.config is not None

    def test_get_connection(self, macro_manager):
        """測試取得資料庫連接"""
        conn = macro_manager.get_connection()
        assert conn is not None
        conn.close()

    def test_add_macro_indicator(self, macro_manager):
        """測試新增總體經濟指標"""
        data = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'unit': '%',
            'region': '台灣',
            'source': '主計處',
            'frequency': '季',
            'previous_value': 2.42,
            'change': 0.65,
            'trend': '上升',
            'impact_assessment': '經濟成長穩健',
            'notes': '2024Q1 GDP成長率優於預期'
        }

        result = macro_manager.add_macro_indicator(data)
        assert result is True

    def test_get_macro_indicators(self, macro_manager):
        """測試取得總體經濟指標"""
        # 先新增資料
        data = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        macro_manager.add_macro_indicator(data)

        # 查詢資料
        df = macro_manager.get_macro_indicators()
        assert len(df) > 0
        assert df.iloc[0]['indicator_name'] == 'GDP成長率'

    def test_get_macro_indicators_with_filter(self, macro_manager):
        """測試取得總體經濟指標（帶過濾）"""
        # 新增多筆資料
        data1 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        data2 = {
            'indicator_name': '消費者物價指數',
            'indicator_date': '2024-03-31',
            'value': 2.14,
            'region': '台灣'
        }
        macro_manager.add_macro_indicator(data1)
        macro_manager.add_macro_indicator(data2)

        # 按指標名稱過濾
        df = macro_manager.get_macro_indicators(indicator_name='GDP成長率')
        assert len(df) == 1
        assert df.iloc[0]['indicator_name'] == 'GDP成長率'

    def test_get_latest_macro_indicators(self, macro_manager):
        """測試取得最新總體經濟指標"""
        # 新增多筆資料
        data1 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2023-12-31',
            'value': 2.42,
            'region': '台灣'
        }
        data2 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        macro_manager.add_macro_indicator(data1)
        macro_manager.add_macro_indicator(data2)

        # 查詢最新資料
        df = macro_manager.get_latest_macro_indicators('台灣')
        assert len(df) > 0
        assert df.iloc[0]['value'] == 3.07

    def test_update_macro_indicator(self, macro_manager):
        """測試更新總體經濟指標"""
        # 新增資料
        data = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        macro_manager.add_macro_indicator(data)

        # 更新資料
        updates = {'value': 3.20, 'notes': '更新後的資料'}
        result = macro_manager.update_macro_indicator('GDP成長率', '2024-03-31', '台灣', updates)
        assert result is True

    def test_delete_macro_indicator(self, macro_manager):
        """測試刪除總體經濟指標"""
        # 新增資料
        data = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        macro_manager.add_macro_indicator(data)

        # 刪除資料
        result = macro_manager.delete_macro_indicator('GDP成長率', '2024-03-31', '台灣')
        assert result is True

        # 確認已刪除
        df = macro_manager.get_macro_indicators(indicator_name='GDP成長率')
        assert len(df) == 0

    def test_get_indicator_trend(self, macro_manager):
        """測試取得指標趨勢"""
        # 新增多筆資料
        data1 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2023-09-30',
            'value': 1.74,
            'region': '台灣'
        }
        data2 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2023-12-31',
            'value': 2.42,
            'region': '台灣'
        }
        data3 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        macro_manager.add_macro_indicator(data1)
        macro_manager.add_macro_indicator(data2)
        macro_manager.add_macro_indicator(data3)

        # 查詢趨勢
        trend = macro_manager.get_indicator_trend('GDP成長率', '台灣')
        assert len(trend) == 3
        assert trend.iloc[-1]['value'] == 3.07

    def test_get_macro_dashboard_data(self, macro_manager):
        """測試取得宏觀 Dashboard 資料"""
        # 新增資料
        data = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣',
            'trend': '上升'
        }
        macro_manager.add_macro_indicator(data)

        # 查詢 Dashboard 資料
        dashboard = macro_manager.get_macro_dashboard_data('台灣')
        assert dashboard['has_data'] is True
        assert 'categories' in dashboard

    def test_get_macro_dashboard_data_empty(self, macro_manager):
        """測試取得宏觀 Dashboard 資料（無資料）"""
        dashboard = macro_manager.get_macro_dashboard_data('美國')
        assert dashboard['has_data'] is False

    def test_analyze_macro_environment(self, macro_manager):
        """測試分析總體經濟環境"""
        # 新增資料
        data1 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣',
            'trend': '上升'
        }
        data2 = {
            'indicator_name': '消費者物價指數',
            'indicator_date': '2024-03-31',
            'value': 2.14,
            'region': '台灣',
            'trend': '下降'
        }
        macro_manager.add_macro_indicator(data1)
        macro_manager.add_macro_indicator(data2)

        # 分析環境
        analysis = macro_manager.analyze_macro_environment('台灣')
        assert analysis['has_analysis'] is True
        assert 'overall_assessment' in analysis

    def test_get_regional_comparison(self, macro_manager):
        """測試比較區域指標"""
        # 新增不同區域資料
        data1 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        data2 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 2.5,
            'region': '韓國'
        }
        macro_manager.add_macro_indicator(data1)
        macro_manager.add_macro_indicator(data2)

        # 比較區域
        comparison = macro_manager.get_regional_comparison('GDP成長率', ['台灣', '韓國'])
        assert len(comparison) == 2

    def test_search_macro_indicators(self, macro_manager):
        """測試搜尋總體經濟指標"""
        # 新增資料
        data = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'notes': '經濟成長穩健'
        }
        macro_manager.add_macro_indicator(data)

        # 搜尋
        df = macro_manager.search_macro_indicators('GDP')
        assert len(df) > 0

    def test_get_available_indicators(self, macro_manager):
        """測試取得可用指標列表"""
        # 新增資料
        data1 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        data2 = {
            'indicator_name': '消費者物價指數',
            'indicator_date': '2024-03-31',
            'value': 2.14,
            'region': '台灣'
        }
        macro_manager.add_macro_indicator(data1)
        macro_manager.add_macro_indicator(data2)

        # 取得指標列表
        indicators = macro_manager.get_available_indicators()
        assert 'GDP成長率' in indicators
        assert '消費者物價指數' in indicators

    def test_get_available_regions(self, macro_manager):
        """測試取得可用區域列表"""
        # 新增資料
        data1 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 3.07,
            'region': '台灣'
        }
        data2 = {
            'indicator_name': 'GDP成長率',
            'indicator_date': '2024-03-31',
            'value': 2.5,
            'region': '韓國'
        }
        macro_manager.add_macro_indicator(data1)
        macro_manager.add_macro_indicator(data2)

        # 取得區域列表
        regions = macro_manager.get_available_regions()
        assert '台灣' in regions
        assert '韓國' in regions

    def test_add_macro_indicator_missing_fields(self, macro_manager):
        """測試新增總體經濟指標（缺少欄位）"""
        data = {
            'indicator_name': 'GDP成長率',
            # 缺少 indicator_date, value
            'region': '台灣'
        }

        result = macro_manager.add_macro_indicator(data)
        assert result is False

    def test_get_macro_analysis_manager(self):
        """測試取得全域管理器實例"""
        manager = get_macro_analysis_manager()
        assert manager is not None
        assert isinstance(manager, MacroAnalysisManager)