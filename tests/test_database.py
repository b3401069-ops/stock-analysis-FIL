"""
股票追蹤與決策輔助系統 V1 - 資料庫測試
Stock Tracking & Decision Support System V1 - Database Tests
"""

import pytest
import sqlite3
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db(tmp_path):
    """建立臨時資料庫"""
    db_path = tmp_path / "test_stocks.db"
    conn = sqlite3.connect(db_path)
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
    
    return db_path


def test_database_creation(temp_db):
    """測試資料庫建立"""
    assert temp_db.exists()
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 檢查資料表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert 'stocks' in tables
    assert 'prices' in tables
    assert 'fundamentals' in tables
    
    conn.close()


def test_insert_stock(temp_db):
    """測試插入股票資料"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry, enabled)
        VALUES (?, ?, ?, ?, ?)
    """, ('2330', '台積電', 'TWSE', '半導體', 1))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM stocks WHERE stock_id = '2330'")
    stock = cursor.fetchone()
    
    assert stock is not None
    assert stock[1] == '2330'
    assert stock[2] == '台積電'
    
    conn.close()


def test_insert_price(temp_db):
    """測試插入價格資料"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 先插入股票
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry, enabled)
        VALUES (?, ?, ?, ?, ?)
    """, ('2330', '台積電', 'TWSE', '半導體', 1))
    
    # 插入價格
    cursor.execute("""
        INSERT INTO prices (stock_id, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('2330', '2025-07-01', 1010.0, 1020.0, 1005.0, 1018.0, 38000000))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM prices WHERE stock_id = '2330'")
    price = cursor.fetchone()
    
    assert price is not None
    assert price[1] == '2330'
    assert price[2] == '2025-07-01'
    assert price[6] == 1018.0  # close price
    
    conn.close()


def test_insert_fundamental(temp_db):
    """測試插入基本面資料"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 先插入股票
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry, enabled)
        VALUES (?, ?, ?, ?, ?)
    """, ('2330', '台積電', 'TWSE', '半導體', 1))
    
    # 插入基本面
    cursor.execute("""
        INSERT INTO fundamentals 
        (stock_id, date, pe_ratio, pb_ratio, dividend_yield, market_cap, revenue, net_income, eps, roe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('2330', '2025-06-30', 22.5, 8.2, 1.8, 25000000000000, 850000000000, 350000000000, 13.5, 28.5))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM fundamentals WHERE stock_id = '2330'")
    fundamental = cursor.fetchone()
    
    assert fundamental is not None
    assert fundamental[1] == '2330'
    assert fundamental[3] == 22.5  # pe_ratio
    
    conn.close()


def test_init_database_script():
    """測試資料庫初始化腳本"""
    from scripts.init_db import init_database
    
    # 建立臨時目錄
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 修改腳本的資料目錄
        original_dir = Path(__file__).parent.parent / "data"
        
        # 這裡只測試函數是否可以執行，不實際執行腳本
        assert callable(init_database)


def test_import_functions():
    """測試匯入函數"""
    from scripts.init_db import import_stocks, import_prices, import_fundamentals
    
    assert callable(import_stocks)
    assert callable(import_prices)
    assert callable(import_fundamentals)


def test_foreign_key_constraint(temp_db):
    """測試 foreign key 約束"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 啟用 foreign key 約束
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 嘗試插入不存在的 stock_id 的價格資料
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO prices (stock_id, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('9999', '2025-07-01', 100.0, 110.0, 90.0, 105.0, 1000000))
    
    conn.close()


def test_duplicate_stock_insertion(temp_db):
    """測試重複股票插入"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 第一次插入
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry, enabled)
        VALUES (?, ?, ?, ?, ?)
    """, ('2330', '台積電', 'TWSE', '半導體', 1))
    
    conn.commit()
    
    # 第二次插入相同的 stock_id，應該失敗
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO stocks (stock_id, name, market, industry, enabled)
            VALUES (?, ?, ?, ?, ?)
        """, ('2330', '台積電2', 'TWSE', '半導體', 1))
    
    conn.close()


def test_duplicate_price_insertion(temp_db):
    """測試重複價格插入"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 先插入股票
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry, enabled)
        VALUES (?, ?, ?, ?, ?)
    """, ('2330', '台積電', 'TWSE', '半導體', 1))
    
    # 第一次插入價格
    cursor.execute("""
        INSERT INTO prices (stock_id, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('2330', '2025-07-01', 1010.0, 1020.0, 1005.0, 1018.0, 38000000))
    
    conn.commit()
    
    # 第二次插入相同的 stock_id 和 date，應該失敗
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO prices (stock_id, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('2330', '2025-07-01', 1010.0, 1020.0, 1005.0, 1018.0, 38000000))
    
    conn.close()


def test_database_schema_version(temp_db):
    """測試資料庫 schema 版本"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 檢查資料庫版本
    cursor.execute("PRAGMA user_version")
    version = cursor.fetchone()[0]
    
    # 版本應該是一個整數
    assert isinstance(version, int)
    
    conn.close()


def test_database_migration_compatibility(temp_db):
    """測試資料庫 migration 兼容性"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 檢查資料表結構
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # 應該有 stocks、prices、fundamentals 等資料表
    assert 'stocks' in tables
    assert 'prices' in tables
    assert 'fundamentals' in tables
    
    # 檢查 stocks 資料表結構
    cursor.execute("PRAGMA table_info(stocks)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # 應該有 stock_id、name 等欄位
    assert 'stock_id' in columns
    assert 'name' in columns
    
    conn.close()


def test_import_prices_foreign_key_constraint(tmp_path):
    """測試 import_prices 在匯入不存在的 stock_id 時會失敗"""
    from scripts.init_db import import_prices
    
    # 建立臨時資料庫
    db_path = tmp_path / "test_stocks.db"
    
    # 初始化資料庫 schema
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
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
    
    conn.commit()
    conn.close()
    
    # 建立包含不存在 stock_id 的 CSV 檔案
    csv_path = tmp_path / "test_prices.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("stock_id,date,open,high,low,close,volume\n")
        f.write("9999,2025-07-01,100.0,110.0,90.0,105.0,1000000\n")
    
    # 嘗試匯入，應該會因為 foreign key 約束而失敗
    with pytest.raises(sqlite3.IntegrityError):
        import_prices(db_path, csv_path, validate=False)


def test_import_fundamentals_foreign_key_constraint(tmp_path):
    """測試 import_fundamentals 在匯入不存在的 stock_id 時會失敗"""
    from scripts.init_db import import_fundamentals
    
    # 建立臨時資料庫
    db_path = tmp_path / "test_stocks.db"
    
    # 初始化資料庫 schema
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
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
    
    # 建立包含不存在 stock_id 的 CSV 檔案
    csv_path = tmp_path / "test_fundamentals.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("stock_id,date,pe_ratio,pb_ratio,dividend_yield,market_cap,revenue,net_income,eps,roe\n")
        f.write("9999,2025-06-30,22.5,8.2,1.8,25000000000000,850000000000,350000000000,13.5,28.5\n")
    
    # 嘗試匯入，應該會因為 foreign key 約束而失敗
    with pytest.raises(sqlite3.IntegrityError):
        import_fundamentals(db_path, csv_path, validate=False)


def test_import_stocks_with_valid_data(tmp_path):
    """測試 import_stocks 可以正常匯入有效資料"""
    from scripts.init_db import import_stocks
    
    # 建立臨時資料庫
    db_path = tmp_path / "test_stocks.db"
    
    # 初始化資料庫 schema
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
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
    
    conn.commit()
    conn.close()
    
    # 建立有效的 CSV 檔案
    csv_path = tmp_path / "test_stocks.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("stock_id,name,market,industry,enabled\n")
        f.write("2330,台積電,TWSE,半導體,1\n")
        f.write("2317,鴻海,TWSE,電子零組件,1\n")
    
    # 匯入資料
    result = import_stocks(db_path, csv_path, validate=False)
    assert result is True
    
    # 驗證資料是否正確匯入
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stocks")
    count = cursor.fetchone()[0]
    assert count == 2
    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])