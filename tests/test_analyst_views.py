"""
投行觀點模組測試
Analyst Views Module Tests
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

# 導入被測模組
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.analyst_views import AnalystViewsManager, get_analyst_views_manager


@pytest.fixture
def temp_db(tmp_path):
    """建立臨時資料庫"""
    db_path = tmp_path / "test_analyst.db"

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
        CREATE TABLE IF NOT EXISTS analyst_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            report_date DATE NOT NULL,
            analyst_firm TEXT,
            analyst_name TEXT,
            rating TEXT,
            target_price REAL,
            previous_target REAL,
            recommendation TEXT,
            key_findings TEXT,
            strengths TEXT,
            weaknesses TEXT,
            opportunities TEXT,
            threats TEXT,
            financial_estimates TEXT,
            valuation_methodology TEXT,
            risk_factors TEXT,
            catalysts TEXT,
            report_summary TEXT,
            confidence_level TEXT,
            notes TEXT,
            source TEXT DEFAULT '投行研報',
            source_url TEXT,
            source_type TEXT DEFAULT '摘要',
            is_paid_report INTEGER DEFAULT 0,
            summary_only INTEGER DEFAULT 1,
            data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, report_date, analyst_firm)
        )
    """)

    # 插入測試股票
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry)
        VALUES ('2330', '台積電', 'TWSE', '半導體')
    """)

    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry)
        VALUES ('2317', '鴻海', 'TWSE', '電子代工')
    """)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def analyst_manager(temp_db, monkeypatch):
    """建立投行觀點管理器"""
    # Mock config
    class MockConfig:
        DATABASE_PATH = str(temp_db)

    def mock_get_config():
        return MockConfig()

    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)

    manager = AnalystViewsManager()
    return manager


class TestAnalystViewsManager:
    """投行觀點管理器測試類別"""

    def test_initialization(self, analyst_manager):
        """測試初始化"""
        assert analyst_manager is not None
        assert analyst_manager.config is not None

    def test_get_connection(self, analyst_manager):
        """測試取得資料庫連接"""
        conn = analyst_manager.get_connection()
        assert conn is not None
        conn.close()

    def test_add_analyst_view(self, analyst_manager):
        """測試新增投行觀點"""
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750,
            'previous_target': 700,
            'recommendation': '投資邏輯成立',
            'key_findings': 'AI 需求帶動先進製程成長',
            'strengths': '技術領先優勢',
            'weaknesses': '資本支出壓力',
            'report_summary': '台積電 AI 需求強勁',
            'confidence_level': '高'
        }

        result = analyst_manager.add_analyst_view(data)
        assert result is True

    def test_get_analyst_views(self, analyst_manager):
        """測試取得投行觀點"""
        # 先新增資料
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750,
            'recommendation': '投資邏輯成立'
        }
        analyst_manager.add_analyst_view(data)

        # 查詢資料
        df = analyst_manager.get_analyst_views('2330')
        assert len(df) > 0
        assert df.iloc[0]['stock_id'] == '2330'

    def test_get_analyst_views_all(self, analyst_manager):
        """測試取得所有投行觀點"""
        # 新增多筆資料
        data1 = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'rating': '買進',
            'target_price': 750
        }
        data2 = {
            'stock_id': '2317',
            'report_date': '2024-03-20',
            'analyst_firm': '美林',
            'rating': '買進',
            'target_price': 200
        }
        analyst_manager.add_analyst_view(data1)
        analyst_manager.add_analyst_view(data2)

        # 查詢所有資料
        df = analyst_manager.get_analyst_views()
        assert len(df) >= 2

    def test_get_latest_analyst_view(self, analyst_manager):
        """測試取得最新投行觀點"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750
        }
        analyst_manager.add_analyst_view(data)

        # 查詢最新資料
        latest = analyst_manager.get_latest_analyst_view('2330')
        assert latest is not None
        assert latest['stock_id'] == '2330'

    def test_get_latest_analyst_view_empty(self, analyst_manager):
        """測試取得最新投行觀點（無資料）"""
        latest = analyst_manager.get_latest_analyst_view('9999')
        assert latest is None

    def test_get_views_by_firm(self, analyst_manager):
        """測試按投行取得觀點"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750
        }
        analyst_manager.add_analyst_view(data)

        # 按投行查詢
        df = analyst_manager.get_views_by_firm('2330', '摩根士丹利')
        assert len(df) > 0
        assert df.iloc[0]['analyst_firm'] == '摩根士丹利'

    def test_get_consensus_rating(self, analyst_manager):
        """測試取得共識評級"""
        # 新增多筆資料
        data1 = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'rating': '買進',
            'target_price': 750
        }
        data2 = {
            'stock_id': '2330',
            'report_date': '2024-02-15',
            'analyst_firm': '高盛',
            'rating': '買進',
            'target_price': 780
        }
        analyst_manager.add_analyst_view(data1)
        analyst_manager.add_analyst_view(data2)

        # 查詢共識評級
        consensus = analyst_manager.get_consensus_rating('2330')
        assert consensus['has_consensus'] is True
        assert consensus['total_reports'] == 2
        assert consensus['avg_target_price'] == 765.0

    def test_get_consensus_rating_empty(self, analyst_manager):
        """測試取得共識評級（無資料）"""
        consensus = analyst_manager.get_consensus_rating('9999')
        assert consensus['has_consensus'] is False

    def test_get_target_price_trend(self, analyst_manager):
        """測試取得目標價趨勢"""
        # 新增多筆資料
        data1 = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'target_price': 750,
            'previous_target': 700
        }
        data2 = {
            'stock_id': '2330',
            'report_date': '2024-02-15',
            'analyst_firm': '高盛',
            'target_price': 780,
            'previous_target': 750
        }
        analyst_manager.add_analyst_view(data1)
        analyst_manager.add_analyst_view(data2)

        # 查詢目標價趨勢
        trend = analyst_manager.get_target_price_trend('2330')
        assert not trend.empty
        assert 'price_change' in trend.columns

    def test_get_research_conclusion_summary(self, analyst_manager):
        """測試取得研究結論摘要"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750,
            'recommendation': '投資邏輯成立',
            'key_findings': 'AI 需求帶動先進製程成長',
            'strengths': '技術領先優勢',
            'weaknesses': '資本支出壓力'
        }
        analyst_manager.add_analyst_view(data)

        # 查詢研究結論摘要
        summary = analyst_manager.get_research_conclusion_summary('2330')
        assert summary['has_conclusion'] is True
        assert summary['analyst_firm'] == '摩根士丹利'
        assert summary['rating'] == '買進'

    def test_get_research_conclusion_summary_empty(self, analyst_manager):
        """測試取得研究結論摘要（無資料）"""
        summary = analyst_manager.get_research_conclusion_summary('9999')
        assert summary['has_conclusion'] is False

    def test_update_analyst_view(self, analyst_manager):
        """測試更新投行觀點"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750
        }
        analyst_manager.add_analyst_view(data)

        # 更新資料
        updates = {'target_price': 800, 'rating': '強力買進'}
        result = analyst_manager.update_analyst_view('2330', '2024-01-20', '摩根士丹利', updates)
        assert result is True

    def test_delete_analyst_view(self, analyst_manager):
        """測試刪除投行觀點"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750
        }
        analyst_manager.add_analyst_view(data)

        # 刪除資料
        result = analyst_manager.delete_analyst_view('2330', '2024-01-20', '摩根士丹利')
        assert result is True

        # 確認已刪除
        latest = analyst_manager.get_latest_analyst_view('2330')
        assert latest is None

    def test_search_analyst_views(self, analyst_manager):
        """測試搜尋投行觀點"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'rating': '買進',
            'target_price': 750,
            'key_findings': 'AI 需求帶動先進製程成長',
            'strengths': '技術領先優勢',
            'weaknesses': '資本支出壓力',
            'report_summary': '台積電 AI 需求強勁'
        }
        analyst_manager.add_analyst_view(data)

        # 搜尋
        df = analyst_manager.search_analyst_views('AI')
        assert len(df) > 0

    def test_get_analyst_coverage(self, analyst_manager):
        """測試取得分析師覆蓋範圍"""
        # 新增多筆資料
        data1 = {
            'stock_id': '2330',
            'report_date': '2024-01-20',
            'analyst_firm': '摩根士丹利',
            'analyst_name': '王大明',
            'target_price': 750
        }
        data2 = {
            'stock_id': '2330',
            'report_date': '2024-02-15',
            'analyst_firm': '高盛',
            'analyst_name': '李小華',
            'target_price': 780
        }
        analyst_manager.add_analyst_view(data1)
        analyst_manager.add_analyst_view(data2)

        # 查詢分析師覆蓋範圍
        coverage = analyst_manager.get_analyst_coverage('2330')
        assert len(coverage) >= 2

    def test_add_analyst_view_missing_fields(self, analyst_manager):
        """測試新增投行觀點（缺少欄位）"""
        data = {
            'stock_id': '2330',
            # 缺少 report_date, analyst_firm
            'rating': '買進'
        }

        result = analyst_manager.add_analyst_view(data)
        assert result is False

    def test_get_analyst_views_manager(self):
        """測試取得全域管理器實例"""
        manager = get_analyst_views_manager()
        assert manager is not None
        assert isinstance(manager, AnalystViewsManager)