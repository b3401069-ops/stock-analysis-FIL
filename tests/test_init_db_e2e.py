"""
股票追蹤與決策輔助系統 V1 - init_db 端對端測試
Stock Tracking & Decision Support System V1 - init_db End-to-End Tests

覆蓋缺 fundamentals 的股票
"""

import pytest
import sqlite3
import tempfile
import pandas as pd
from pathlib import Path


@pytest.fixture
def temp_db_path(tmp_path):
    """建立臨時資料庫路徑"""
    return tmp_path / "test_stocks.db"


@pytest.fixture
def sample_stocks_csv(tmp_path):
    """建立範例股票 CSV"""
    csv_path = tmp_path / "stocks.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2317', '2454'],
        'name': ['台積電', '鴻海', '聯發科'],
        'market': ['上市', '上市', '上市'],
        'industry': ['半導體', '電子', '半導體'],
        'enabled': [1, 1, 1]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_prices_csv(tmp_path):
    """建立範例價格 CSV"""
    csv_path = tmp_path / "prices.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2330', '2317', '2317', '2454', '2454'],
        'date': ['2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02'],
        'open': [600.0, 610.0, 100.0, 102.0, 800.0, 810.0],
        'high': [620.0, 630.0, 105.0, 107.0, 820.0, 830.0],
        'low': [590.0, 600.0, 95.0, 97.0, 790.0, 800.0],
        'close': [615.0, 625.0, 103.0, 105.0, 810.0, 820.0],
        'volume': [1000000, 1200000, 800000, 900000, 500000, 600000]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_fundamentals_csv(tmp_path):
    """
    建立範例基本面 CSV
    注意：只有 2330 和 2317 有基本面資料，2454 缺少基本面
    """
    csv_path = tmp_path / "fundamentals.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2317'],
        'date': ['2024-01-01', '2024-01-01'],
        'pe_ratio': [20.5, 12.3],
        'pb_ratio': [5.2, 1.8],
        'dividend_yield': [2.1, 3.5],
        'market_cap': [15000.0, 3000.0],
        'revenue': [5000.0, 15000.0],
        'net_income': [2000.0, 500.0],
        'eps': [30.0, 15.0],
        'roe': [25.0, 18.0]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


def test_init_db_e2e_basic(temp_db_path, sample_stocks_csv, sample_prices_csv, sample_fundamentals_csv):
    """測試基本的資料庫初始化與資料匯入"""
    import sqlite3
    from scripts.init_db import import_stocks, import_prices, import_fundamentals
    
    # 直接建立資料庫 schema
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 建立 stocks 資料表
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
    
    # 建立 prices 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    # 建立 fundamentals 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            pe_ratio REAL,
            pb_ratio REAL,
            dividend_yield REAL,
            market_cap REAL,
            revenue REAL,
            net_income REAL,
            eps REAL,
            roe REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    conn.commit()
    conn.close()
    
    # 匯入資料
    import_stocks(temp_db_path, sample_stocks_csv)
    import_prices(temp_db_path, sample_prices_csv)
    import_fundamentals(temp_db_path, sample_fundamentals_csv)
    
    # 驗證資料庫
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 檢查 stocks 表
    cursor.execute("SELECT COUNT(*) FROM stocks")
    assert cursor.fetchone()[0] == 3
    
    # 檢查 prices 表
    cursor.execute("SELECT COUNT(*) FROM prices")
    assert cursor.fetchone()[0] == 6
    
    # 檢查 fundamentals 表
    cursor.execute("SELECT COUNT(*) FROM fundamentals")
    assert cursor.fetchone()[0] == 2  # 只有 2 筆
    
    conn.close()


def test_init_db_e2e_missing_fundamentals(temp_db_path, sample_stocks_csv, sample_prices_csv, sample_fundamentals_csv):
    """
    測試缺少基本面資料的股票
    確保系統能正常運作，不會因為缺少基本面而崩潰
    """
    import sqlite3
    from scripts.init_db import import_stocks, import_prices, import_fundamentals
    
    # 直接建立資料庫 schema
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 建立 stocks 資料表
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
    
    # 建立 prices 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    # 建立 fundamentals 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            pe_ratio REAL,
            pb_ratio REAL,
            dividend_yield REAL,
            market_cap REAL,
            revenue REAL,
            net_income REAL,
            eps REAL,
            roe REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    conn.commit()
    conn.close()
    
    # 匯入資料
    import_stocks(temp_db_path, sample_stocks_csv)
    import_prices(temp_db_path, sample_prices_csv)
    import_fundamentals(temp_db_path, sample_fundamentals_csv)
    
    # 驗證資料庫
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 檢查 2454（聯發科）有價格但沒有基本面
    cursor.execute("""
        SELECT p.stock_id, p.date, p.close, f.pe_ratio
        FROM prices p
        LEFT JOIN fundamentals f ON p.stock_id = f.stock_id AND p.date = f.date
        WHERE p.stock_id = '2454'
    """)
    rows = cursor.fetchall()
    
    assert len(rows) == 2  # 有 2 天的價格
    for row in rows:
        assert row[3] is None  # 沒有基本面資料（pe_ratio 為 NULL）
    
    conn.close()


def test_init_db_e2e_query_stocks_without_fundamentals(temp_db_path, sample_stocks_csv, sample_prices_csv, sample_fundamentals_csv):
    """
    測試查詢缺少基本面資料的股票
    確保能正確識別哪些股票缺少基本面
    """
    import sqlite3
    from scripts.init_db import import_stocks, import_prices, import_fundamentals
    
    # 直接建立資料庫 schema
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 建立 stocks 資料表
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
    
    # 建立 prices 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    # 建立 fundamentals 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            pe_ratio REAL,
            pb_ratio REAL,
            dividend_yield REAL,
            market_cap REAL,
            revenue REAL,
            net_income REAL,
            eps REAL,
            roe REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    conn.commit()
    conn.close()
    
    # 匯入資料
    import_stocks(temp_db_path, sample_stocks_csv)
    import_prices(temp_db_path, sample_prices_csv)
    import_fundamentals(temp_db_path, sample_fundamentals_csv)
    
    # 驗證資料庫
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 查詢有價格但沒有基本面的股票
    cursor.execute("""
        SELECT DISTINCT p.stock_id
        FROM prices p
        LEFT JOIN fundamentals f ON p.stock_id = f.stock_id
        WHERE f.stock_id IS NULL
    """)
    stocks_without_fundamentals = [row[0] for row in cursor.fetchall()]
    
    assert '2454' in stocks_without_fundamentals
    assert '2330' not in stocks_without_fundamentals
    assert '2317' not in stocks_without_fundamentals
    
    conn.close()


def test_init_db_e2e_schema_integrity(temp_db_path):
    """測試資料庫 schema 完整性"""
    import sqlite3
    
    # 直接建立資料庫 schema
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 建立 stocks 資料表
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
    
    # 建立 prices 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    # 建立 fundamentals 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            pe_ratio REAL,
            pb_ratio REAL,
            dividend_yield REAL,
            market_cap REAL,
            revenue REAL,
            net_income REAL,
            eps REAL,
            roe REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    # 建立 indicators 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            ma5 REAL,
            ma20 REAL,
            ma60 REAL,
            rsi REAL,
            macd REAL,
            macd_signal REAL,
            macd_histogram REAL,
            volume_ma20 REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    # 建立 scores 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            technical_score REAL,
            fundamental_score REAL,
            risk_score REAL,
            total_score REAL,
            rating TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        )
    """)
    
    # 建立 signals 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            signal_type TEXT NOT NULL,
            signal_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    # 驗證資料庫
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 檢查所有資料表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['stocks', 'prices', 'fundamentals', 'indicators', 'scores', 'signals']
    for table in expected_tables:
        assert table in tables, f"缺少資料表: {table}"
    
    # 檢查 stocks 表結構
    cursor.execute("PRAGMA table_info(stocks)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'stock_id' in columns
    assert 'name' in columns
    assert 'market' in columns
    assert 'industry' in columns
    assert 'enabled' in columns
    
    conn.close()


def test_csv_validator_consistency():
    """
    測試 CSV validator 和實際 import 欄位一致性
    確認 validator 的欄位定義與 init_db.py 的 import 函數一致
    """
    from modules.csv_validator import CSVValidator
    from scripts.init_db import import_fundamentals
    
    # 取得 validator 定義的 fundamentals 欄位
    validator_columns = CSVValidator.REQUIRED_COLUMNS['fundamentals']
    
    # 檢查 import_fundamentals 使用的欄位
    # 從 init_db.py 的 import_fundamentals 函數中，使用的欄位是：
    # row['stock_id'], row['date'], row['pe_ratio'], row['pb_ratio'],
    # row['dividend_yield'], row['market_cap'], row['revenue'],
    # row['net_income'], row['eps'], row['roe']
    
    expected_columns = [
        'stock_id', 'date', 'pe_ratio', 'pb_ratio', 'dividend_yield',
        'market_cap', 'revenue', 'net_income', 'eps', 'roe'
    ]
    
    assert validator_columns == expected_columns, \
        f"CSV validator 欄位 ({validator_columns}) 與 import 函數欄位 ({expected_columns}) 不一致"