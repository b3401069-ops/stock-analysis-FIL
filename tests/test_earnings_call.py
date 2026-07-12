"""
電話會議模組測試
Earnings Call Module Tests
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

# 導入被測模組
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.earnings_call import EarningsCallManager, get_earnings_call_manager


@pytest.fixture
def temp_db(tmp_path):
    """建立臨時資料庫"""
    db_path = tmp_path / "test_earnings.db"

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
        CREATE TABLE IF NOT EXISTS earnings_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            call_date DATE NOT NULL,
            quarter TEXT,
            fiscal_year TEXT,
            call_time TEXT,
            participants TEXT,
            management_guidance TEXT,
            key_highlights TEXT,
            revenue_guidance TEXT,
            earnings_guidance TEXT,
            margin_guidance TEXT,
            capex_guidance TEXT,
            analyst_questions TEXT,
            management_responses TEXT,
            sentiment TEXT,
            surprises TEXT,
            risk_factors TEXT,
            outlook_summary TEXT,
            transcript_summary TEXT,
            notes TEXT,
            source TEXT DEFAULT '公開資訊',
            source_url TEXT,
            data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, call_date, quarter)
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
def earnings_manager(temp_db, monkeypatch):
    """建立電話會議管理器"""
    # Mock config
    class MockConfig:
        DATABASE_PATH = str(temp_db)

    def mock_get_config():
        return MockConfig()

    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)

    manager = EarningsCallManager()
    return manager


class TestEarningsCallManager:
    """電話會議管理器測試類別"""

    def test_initialization(self, earnings_manager):
        """測試初始化"""
        assert earnings_manager is not None
        assert earnings_manager.config is not None

    def test_get_connection(self, earnings_manager):
        """測試取得資料庫連接"""
        conn = earnings_manager.get_connection()
        assert conn is not None
        conn.close()

    def test_add_earnings_call(self, earnings_manager):
        """測試新增電話會議紀錄"""
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'call_time': '14:00',
            'management_guidance': '管理層表示 2024 年營收將逐季成長',
            'key_highlights': 'AI 需求帶動先進製程成長',
            'revenue_guidance': '2024Q1 營收預估 180-185 億美元',
            'earnings_guidance': '2024Q1 毛利率預估 52-54%',
            'sentiment': '正面',
            'outlook_summary': '管理層對 AI 需求前景樂觀',
            'transcript_summary': '台積電 2023Q4 法說會重點'
        }

        result = earnings_manager.add_earnings_call(data)
        assert result is True

    def test_get_earnings_calls(self, earnings_manager):
        """測試取得電話會議紀錄"""
        # 先新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面',
            'outlook_summary': '樂觀展望'
        }
        earnings_manager.add_earnings_call(data)

        # 查詢資料
        df = earnings_manager.get_earnings_calls('2330')
        assert len(df) > 0
        assert df.iloc[0]['stock_id'] == '2330'

    def test_get_earnings_calls_all(self, earnings_manager):
        """測試取得所有電話會議紀錄"""
        # 新增多筆資料
        data1 = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面'
        }
        data2 = {
            'stock_id': '2317',
            'call_date': '2024-03-14',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '中性偏正'
        }
        earnings_manager.add_earnings_call(data1)
        earnings_manager.add_earnings_call(data2)

        # 查詢所有資料
        df = earnings_manager.get_earnings_calls()
        assert len(df) >= 2

    def test_get_latest_earnings_call(self, earnings_manager):
        """測試取得最新電話會議紀錄"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面'
        }
        earnings_manager.add_earnings_call(data)

        # 查詢最新資料
        latest = earnings_manager.get_latest_earnings_call('2330')
        assert latest is not None
        assert latest['stock_id'] == '2330'

    def test_get_latest_earnings_call_empty(self, earnings_manager):
        """測試取得最新電話會議紀錄（無資料）"""
        latest = earnings_manager.get_latest_earnings_call('9999')
        assert latest is None

    def test_get_earnings_calls_by_quarter(self, earnings_manager):
        """測試按季度取得電話會議紀錄"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面'
        }
        earnings_manager.add_earnings_call(data)

        # 按季度查詢
        df = earnings_manager.get_earnings_calls_by_quarter('2330', '2023')
        assert len(df) > 0

    def test_get_sentiment_trend(self, earnings_manager):
        """測試取得情緒趨勢"""
        # 新增多筆資料
        data1 = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面'
        }
        data2 = {
            'stock_id': '2330',
            'call_date': '2024-04-18',
            'quarter': 'Q1 2024',
            'fiscal_year': '2024',
            'sentiment': '正面'
        }
        earnings_manager.add_earnings_call(data1)
        earnings_manager.add_earnings_call(data2)

        # 查詢情緒趨勢
        trend = earnings_manager.get_sentiment_trend('2330')
        assert not trend.empty

    def test_get_guidance_summary(self, earnings_manager):
        """測試取得指引摘要"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'revenue_guidance': '2024Q1 營收預估 180-185 億美元',
            'earnings_guidance': '2024Q1 毛利率預估 52-54%',
            'sentiment': '正面',
            'outlook_summary': '管理層對 AI 需求前景樂觀'
        }
        earnings_manager.add_earnings_call(data)

        # 查詢指引摘要
        summary = earnings_manager.get_guidance_summary('2330')
        assert summary['has_guidance'] is True
        assert summary['revenue_guidance'] == '2024Q1 營收預估 180-185 億美元'

    def test_get_guidance_summary_empty(self, earnings_manager):
        """測試取得指引摘要（無資料）"""
        summary = earnings_manager.get_guidance_summary('9999')
        assert summary['has_guidance'] is False

    def test_update_earnings_call(self, earnings_manager):
        """測試更新電話會議紀錄"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面'
        }
        earnings_manager.add_earnings_call(data)

        # 更新資料
        updates = {'sentiment': '非常正面', 'outlook_summary': '更新後的展望'}
        result = earnings_manager.update_earnings_call('2330', '2024-01-18', 'Q4 2023', updates)
        assert result is True

    def test_delete_earnings_call(self, earnings_manager):
        """測試刪除電話會議紀錄"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面'
        }
        earnings_manager.add_earnings_call(data)

        # 刪除資料
        result = earnings_manager.delete_earnings_call('2330', '2024-01-18', 'Q4 2023')
        assert result is True

        # 確認已刪除
        latest = earnings_manager.get_latest_earnings_call('2330')
        assert latest is None

    def test_search_earnings_calls(self, earnings_manager):
        """測試搜尋電話會議紀錄"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'key_highlights': 'AI 需求帶動先進製程成長',
            'outlook_summary': '管理層對 AI 需求前景樂觀'
        }
        earnings_manager.add_earnings_call(data)

        # 搜尋
        df = earnings_manager.search_earnings_calls('AI')
        assert len(df) > 0

    def test_get_earnings_calendar(self, earnings_manager):
        """測試取得電話會議日曆"""
        # 新增資料
        data = {
            'stock_id': '2330',
            'call_date': '2024-01-18',
            'quarter': 'Q4 2023',
            'fiscal_year': '2023',
            'sentiment': '正面'
        }
        earnings_manager.add_earnings_call(data)

        # 查詢日曆
        calendar = earnings_manager.get_earnings_calendar('2024-01-01', '2024-12-31')
        assert len(calendar) > 0

    def test_add_earnings_call_missing_fields(self, earnings_manager):
        """測試新增電話會議紀錄（缺少欄位）"""
        data = {
            'stock_id': '2330',
            # 缺少 call_date, quarter, fiscal_year
            'sentiment': '正面'
        }

        result = earnings_manager.add_earnings_call(data)
        assert result is False

    def test_get_earnings_call_manager(self):
        """測試取得全域管理器實例"""
        manager = get_earnings_call_manager()
        assert manager is not None
        assert isinstance(manager, EarningsCallManager)