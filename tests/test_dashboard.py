"""
股票追蹤與決策輔助系統 V1 - Dashboard 測試
Stock Tracking & Decision Support System V1 - Dashboard Tests
"""

import pytest
import sqlite3
import pandas as pd
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def db_with_data(tmp_path):
    """建立包含測試資料的資料庫"""
    db_path = tmp_path / "test_stocks.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 建立資料表
    cursor.execute("""
        CREATE TABLE stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            market TEXT,
            industry TEXT,
            enabled INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            UNIQUE(stock_id, date)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            pe_ratio REAL, pb_ratio REAL, dividend_yield REAL,
            market_cap REAL, revenue REAL, net_income REAL, eps REAL, roe REAL,
            UNIQUE(stock_id, date)
        )
    """)
    
    # 插入測試資料
    cursor.execute("INSERT INTO stocks VALUES (1, '2330', '台積電', 'TWSE', '半導體', 1)")
    cursor.execute("INSERT INTO stocks VALUES (2, '2317', '鴻海', 'TWSE', '電子代工', 1)")
    
    cursor.execute("INSERT INTO prices VALUES (1, '2330', '2025-07-01', 1010, 1020, 1005, 1018, 38000000)")
    cursor.execute("INSERT INTO prices VALUES (2, '2330', '2025-07-02', 1020, 1025, 1012, 1015, 35000000)")
    cursor.execute("INSERT INTO prices VALUES (3, '2317', '2025-07-01', 190, 195, 188, 194, 65000000)")
    cursor.execute("INSERT INTO prices VALUES (4, '2317', '2025-07-02', 195, 198, 192, 195, 60000000)")
    
    cursor.execute("INSERT INTO fundamentals VALUES (1, '2330', '2025-06-30', 22.5, 8.2, 1.8, 25000000000000, 850000000000, 350000000000, 13.5, 28.5)")
    
    conn.commit()
    conn.close()
    
    return db_path


def test_get_connection():
    """測試資料庫連接"""
    from modules.database import get_connection
    conn = get_connection()
    assert conn is not None
    conn.close()


def test_get_enabled_stocks(db_with_data, monkeypatch):
    """測試取得啟用的股票"""
    from modules.database import get_enabled_stocks
    
    # 模擬資料庫路徑
    def mock_get_connection():
        return sqlite3.connect(db_with_data)
    
    monkeypatch.setattr('modules.database.get_connection', mock_get_connection)
    
    df = get_enabled_stocks()
    assert len(df) == 2
    assert df.iloc[0]['stock_id'] == '2330'
    assert df.iloc[1]['stock_id'] == '2317'


def test_get_latest_prices(db_with_data, monkeypatch):
    """測試取得最新價格"""
    from modules.database import get_latest_prices
    
    def mock_get_connection():
        return sqlite3.connect(db_with_data)
    
    monkeypatch.setattr('modules.database.get_connection', mock_get_connection)
    
    df = get_latest_prices()
    assert len(df) == 2
    assert 'latest_close' in df.columns
    # 檢查 2330 的最新收盤價
    stock_2330 = df[df['stock_id'] == '2330']
    assert stock_2330.iloc[0]['latest_close'] == 1015


def test_get_price_change(db_with_data, monkeypatch):
    """測試取得漲跌幅"""
    from modules.database import get_price_change
    
    def mock_get_connection():
        return sqlite3.connect(db_with_data)
    
    monkeypatch.setattr('modules.database.get_connection', mock_get_connection)
    
    result = get_price_change('2330')
    assert 'change' in result
    assert 'change_pct' in result
    assert result['latest_close'] == 1015
    assert result['previous_close'] == 1018
    assert result['change'] == -3


def test_get_latest_fundamentals(db_with_data, monkeypatch):
    """測試取得最新基本面資料"""
    from modules.database import get_latest_fundamentals
    
    def mock_get_connection():
        return sqlite3.connect(db_with_data)
    
    monkeypatch.setattr('modules.database.get_connection', mock_get_connection)
    
    df = get_latest_fundamentals()
    assert len(df) == 2
    # 檢查 2330 的 PE Ratio
    stock_2330 = df[df['stock_id'] == '2330']
    assert stock_2330.iloc[0]['pe_ratio'] == 22.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])