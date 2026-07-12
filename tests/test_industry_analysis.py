"""
行業分析模組測試
Industry Analysis Module Tests
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

# 導入被測模組
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.industry_analysis import IndustryAnalysisManager, get_industry_analysis_manager


@pytest.fixture
def temp_db(tmp_path):
    """建立臨時資料庫"""
    db_path = tmp_path / "test_industry.db"

    # 建立基礎資料表
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            market TEXT,
            industry TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS industry_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            industry_name TEXT,
            market_size TEXT,
            growth_rate REAL,
            competition_level TEXT,
            entry_barriers TEXT,
            regulatory_environment TEXT,
            industry_trends TEXT,
            key_drivers TEXT,
            threats TEXT,
            outlook TEXT,
            score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    # 插入測試股票
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry)
        VALUES ('2330', '台積電', 'TWSE', '半導體')
    """)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def industry_manager(temp_db, monkeypatch):
    """建立行業分析管理器"""
    # Mock config
    class MockConfig:
        DATABASE_PATH = str(temp_db)

    def mock_get_config():
        return MockConfig()

    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)

    manager = IndustryAnalysisManager()
    return manager


class TestIndustryAnalysisManager:
    """行業分析管理器測試類別"""

    def test_initialization(self, industry_manager):
        """測試初始化"""
        assert industry_manager is not None
        assert industry_manager.config is not None

    def test_get_connection(self, industry_manager):
        """測試取得資料庫連接"""
        conn = industry_manager.get_connection()
        assert conn is not None
        conn.close()

    def test_add_industry_analysis(self, industry_manager):
        """測試新增行業分析"""
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'market_size': '全球半導體市場規模約 5,000 億美元',
            'growth_rate': 8.5,
            'competition_level': '高',
            'entry_barriers': '技術門檻高、資本密集',
            'regulatory_environment': '各國加強半導體產業監管',
            'industry_trends': 'AI 需求帶動先進製程成長',
            'key_drivers': 'AI、5G、車用電子',
            'threats': '地緣政治風險、產能過剩',
            'outlook': '正面',
            'score': 85,
            'notes': '半導體產業前景樂觀'
        }

        result = industry_manager.add_industry_analysis(data)
        assert result is True

    def test_get_industry_analysis(self, industry_manager):
        """測試取得行業分析"""
        # 先新增資料
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'score': 85,
            'outlook': '正面'
        }
        industry_manager.add_industry_analysis(data)

        # 查詢資料
        analysis = industry_manager.get_industry_analysis('2330')
        assert analysis is not None
        assert analysis['stock_id'] == '2330'
        assert analysis['industry_name'] == '半導體'

    def test_get_industry_analysis_empty(self, industry_manager):
        """測試取得行業分析（無資料）"""
        analysis = industry_manager.get_industry_analysis('9999')
        assert analysis is None

    def test_get_industry_analysis_history(self, industry_manager):
        """測試取得行業分析歷史"""
        # 新增多筆資料
        data1 = {
            'stock_id': '2330',
            'analysis_date': '2024-01-01',
            'industry_name': '半導體',
            'score': 80
        }
        data2 = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'score': 85
        }
        industry_manager.add_industry_analysis(data1)
        industry_manager.add_industry_analysis(data2)

        # 查詢歷史
        history = industry_manager.get_industry_analysis_history('2330')
        assert len(history) >= 2

    def test_update_industry_analysis(self, industry_manager):
        """測試更新行業分析"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'score': 85
        }
        industry_manager.add_industry_analysis(data)

        # 更新資料
        updates = {'score': 90, 'outlook': '非常正面'}
        result = industry_manager.update_industry_analysis('2330', '2024-03-31', updates)
        assert result is True

    def test_delete_industry_analysis(self, industry_manager):
        """測試刪除行業分析"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'score': 85
        }
        industry_manager.add_industry_analysis(data)

        # 刪除資料
        result = industry_manager.delete_industry_analysis('2330', '2024-03-31')
        assert result is True

        # 確認已刪除
        analysis = industry_manager.get_industry_analysis('2330')
        assert analysis is None

    def test_get_industry_score(self, industry_manager):
        """測試取得行業評分"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'score': 85,
            'outlook': '正面'
        }
        industry_manager.add_industry_analysis(data)

        # 查詢評分
        score_data = industry_manager.get_industry_score('2330')
        assert score_data['has_analysis'] is True
        assert score_data['score'] == 85
        assert score_data['rating'] == '基本面轉強'

    def test_get_industry_score_empty(self, industry_manager):
        """測試取得行業評分（無資料）"""
        score_data = industry_manager.get_industry_score('9999')
        assert score_data['has_analysis'] is False
        assert score_data['rating'] == '需要人工確認'

    def test_compare_industries(self, industry_manager):
        """測試比較行業"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'growth_rate': 8.5,
            'competition_level': '高',
            'score': 85,
            'outlook': '正面'
        }
        industry_manager.add_industry_analysis(data)

        # 比較行業
        comparison = industry_manager.compare_industries(['2330'])
        assert len(comparison) > 0

    def test_get_industry_trends(self, industry_manager):
        """測試取得行業趨勢"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'industry_name': '半導體',
            'industry_trends': 'AI 需求帶動先進製程成長'
        }
        industry_manager.add_industry_analysis(data)

        # 查詢趨勢
        trends = industry_manager.get_industry_trends('半導體')
        assert len(trends) > 0

    def test_add_industry_analysis_missing_fields(self, industry_manager):
        """測試新增行業分析（缺少欄位）"""
        data = {
            'stock_id': '2330',
            # 缺少 analysis_date
            'industry_name': '半導體'
        }

        result = industry_manager.add_industry_analysis(data)
        assert result is False

    def test_get_industry_analysis_manager(self):
        """測試取得全域管理器實例"""
        manager = get_industry_analysis_manager()
        assert manager is not None
        assert isinstance(manager, IndustryAnalysisManager)