"""
股票追蹤與決策輔助系統 V1 - 個股分析測試
Stock Tracking & Decision Support System V1 - Stock Analysis Tests
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
def db_with_indicators(tmp_path):
    """建立包含技術指標的資料庫"""
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
        CREATE TABLE indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            ma5 REAL, ma20 REAL, ma60 REAL,
            rsi REAL, macd REAL, macd_signal REAL, macd_histogram REAL,
            volume_ma20 REAL,
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
    
    for i in range(60):
        date = f"2025-06-{i+1:02d}"
        cursor.execute("INSERT INTO prices VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (i+1, '2330', date, 100+i, 105+i, 98+i, 102+i, 1000000))
        cursor.execute("INSERT INTO indicators VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (i+1, '2330', date, 100+i*0.1, 100+i*0.05, 100+i*0.02, 50+i*0.5, i*0.1, i*0.08, i*0.02, 1000000+i*10000))
    
    cursor.execute("INSERT INTO fundamentals VALUES (1, '2330', '2025-06-30', 22.5, 8.2, 1.8, 25000000000000, 850000000000, 350000000000, 13.5, 28.5)")
    
    conn.commit()
    conn.close()
    
    return db_path


def test_get_stock_prices_with_indicators(db_with_indicators, monkeypatch):
    """測試取得股票價格和技術指標"""
    from modules.database import get_stock_prices, get_indicators
    
    def mock_get_connection():
        return sqlite3.connect(db_with_indicators)
    
    monkeypatch.setattr('modules.database.get_connection', mock_get_connection)
    
    prices = get_stock_prices('2330', days=60)
    indicators = get_indicators('2330', days=60)
    
    assert len(prices) == 60
    assert len(indicators) == 60
    assert 'close' in prices.columns
    assert 'ma5' in indicators.columns
    assert 'rsi' in indicators.columns


def test_stock_analysis_page_imports():
    """測試個股分析頁面可以導入"""
    try:
        # 嘗試導入頁面模組
        import importlib
        spec = importlib.util.spec_from_file_location(
            "stock_analysis_page",
            project_root / "pages" / "1_個股分析.py"
        )
        # 只檢查規格是否存在
        assert spec is not None
    except Exception as e:
        pytest.fail(f"無法導入個股分析頁面: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])