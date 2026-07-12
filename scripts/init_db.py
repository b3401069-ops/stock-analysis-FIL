#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 V1 - 資料庫初始化腳本
Stock Tracking & Decision Support System V1 - Database Initialization Script
"""

import sqlite3
import csv
import os
from pathlib import Path
import sys

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.config import get_config
from modules.csv_validator import CSVValidator
from modules.console import safe_print


def init_database(db_path=None):
    """初始化資料庫
    
    Args:
        db_path: 資料庫路徑，若未指定則使用 config.DATABASE_PATH
    """
    if db_path is None:
        config = get_config()
        db_path = Path(config.DATABASE_PATH)
    else:
        db_path = Path(db_path)
    
    # 確保資料庫目錄存在
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 連接資料庫
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
    
    # 提交變更
    conn.commit()
    
    safe_print(f"✅ 資料庫 schema 建立完成: {db_path}")
    
    # 關閉連接
    conn.close()


def import_stocks(db_path: Path, csv_path: Path, validate: bool = True):
    """匯入股票資料
    
    Args:
        db_path: 資料庫路徑
        csv_path: CSV 檔案路徑
        validate: 是否進行驗證，預設為 True
    """
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    
    # 進行驗證
    if validate:
        result = CSVValidator.validate_csv(csv_path, 'stocks')
        if not result.is_valid:
            safe_print(f"❌ 股票資料驗證失敗:")
            for error in result.errors:
                safe_print(f"  - {error}")
            return False
        
        if result.warnings:
            safe_print(f"⚠️  股票資料驗證警告:")
            for warning in result.warnings:
                safe_print(f"  - {warning}")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO stocks (stock_id, name, market, industry, enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (row['stock_id'], row['name'], row['market'], row['industry'], int(row['enabled'])))
            count += 1
    
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入股票資料: {count} 筆")
    return True


def import_prices(db_path: Path, csv_path: Path, validate: bool = True):
    """匯入價格資料
    
    Args:
        db_path: 資料庫路徑
        csv_path: CSV 檔案路徑
        validate: 是否進行驗證，預設為 True
    """
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    
    # 進行驗證
    if validate:
        result = CSVValidator.validate_csv(csv_path, 'prices')
        if not result.is_valid:
            safe_print(f"❌ 價格資料驗證失敗:")
            for error in result.errors:
                safe_print(f"  - {error}")
            return False
        
        if result.warnings:
            safe_print(f"⚠️  價格資料驗證警告:")
            for warning in result.warnings:
                safe_print(f"  - {warning}")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO prices (stock_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (row['stock_id'], row['date'], float(row['open']), float(row['high']),
                  float(row['low']), float(row['close']), int(row['volume'])))
            count += 1
    
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入價格資料: {count} 筆")
    return True


def import_fundamentals(db_path: Path, csv_path: Path, validate: bool = True):
    """匯入基本面資料
    
    Args:
        db_path: 資料庫路徑
        csv_path: CSV 檔案路徑
        validate: 是否進行驗證，預設為 True
    """
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    
    # 進行驗證
    if validate:
        result = CSVValidator.validate_csv(csv_path, 'fundamentals')
        if not result.is_valid:
            safe_print(f"❌ 基本面資料驗證失敗:")
            for error in result.errors:
                safe_print(f"  - {error}")
            return False
        
        if result.warnings:
            safe_print(f"⚠️  基本面資料驗證警告:")
            for warning in result.warnings:
                safe_print(f"  - {warning}")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO fundamentals 
                (stock_id, date, pe_ratio, pb_ratio, dividend_yield, market_cap, revenue, net_income, eps, roe)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row['stock_id'], row['date'], float(row['pe_ratio']), float(row['pb_ratio']),
                  float(row['dividend_yield']), float(row['market_cap']), float(row['revenue']),
                  float(row['net_income']), float(row['eps']), float(row['roe'])))
            count += 1
    
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入基本面資料: {count} 筆")
    return True


def import_sample_data():
    """匯入所有範例資料
    
    Returns:
        bool: 整體匯入是否成功
    """
    config = get_config()
    
    db_path = Path(config.DATABASE_PATH)
    
    if not db_path.exists():
        safe_print("❌ 資料庫不存在，請先執行 init_database()")
        return False
    
    safe_print("\n📦 開始匯入範例資料...")
    
    # 匯入股票資料（import_stocks 函數內已包含驗證）
    stocks_csv = Path(config.SAMPLE_STOCKS_CSV)
    if not import_stocks(db_path, stocks_csv):
        safe_print("❌ 股票資料匯入失敗，停止後續匯入")
        return False
    
    # 匯入價格資料（import_prices 函數內已包含驗證）
    prices_csv = Path(config.SAMPLE_PRICES_CSV)
    if not import_prices(db_path, prices_csv):
        safe_print("❌ 價格資料匯入失敗，停止後續匯入")
        return False
    
    # 匯入基本面資料（import_fundamentals 函數內已包含驗證）
    fundamentals_csv = Path(config.SAMPLE_FUNDAMENTALS_CSV)
    if not import_fundamentals(db_path, fundamentals_csv):
        safe_print("❌ 基本面資料匯入失敗，停止後續匯入")
        return False
    
    safe_print("✅ 範例資料匯入完成！")
    return True


if __name__ == "__main__":
    safe_print("=" * 50)
    safe_print("股票追蹤與決策輔助系統 V1 - 資料庫初始化")
    safe_print("=" * 50)
    
    # 初始化資料庫 schema
    init_database()
    
    # 匯入範例資料
    if not import_sample_data():
        safe_print("❌ 範例資料匯入失敗，停止後續計算")
        sys.exit(1)
    
    # 計算技術指標
    safe_print("\n📊 開始計算技術指標...")
    from scripts.calculate_indicators import calculate_and_save_indicators
    calculate_and_save_indicators()
    
    # 計算股票評分
    safe_print("\n⭐ 開始計算股票評分...")
    from scripts.calculate_scores import calculate_and_save_scores
    calculate_and_save_scores()
    
    # 產生訊號
    safe_print("\n🔔 開始產生訊號...")
    from scripts.generate_signals import generate_and_save_signals
    generate_and_save_signals()
    
    safe_print("\n" + "=" * 50)
    safe_print("初始化完成！")
    safe_print("=" * 50)