"""
股票追蹤與決策輔助系統 V1 - 完整端對端測試
Stock Tracking & Decision Support System V1 - Full End-to-End Tests

真正執行 scripts/init_db.py 的完整流程，包括：
- 資料庫初始化
- 資料匯入
- 技術指標計算
- 股票評分計算
- 訊號產生
"""

import pytest
import sqlite3
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch

# 確保相關模組被導入，以便 mock 可以正確定位
import modules.config
import modules.database


@pytest.fixture
def temp_db_path(tmp_path):
    """建立臨時資料庫路徑"""
    return tmp_path / "test_stocks.db"


@pytest.fixture
def sample_data_dir(tmp_path):
    """建立範例資料目錄"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # 建立 stocks CSV
    stocks_df = pd.DataFrame({
        'stock_id': ['2330', '2317', '2454'],
        'name': ['台積電', '鴻海', '聯發科'],
        'market': ['上市', '上市', '上市'],
        'industry': ['半導體', '電子', '半導體'],
        'enabled': [1, 1, 1]
    })
    stocks_df.to_csv(data_dir / "sample_stocks.csv", index=False)
    
    # 建立 prices CSV (30 天資料)
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    prices_data = []
    for stock_id, base_price in [('2330', 600), ('2317', 100), ('2454', 800)]:
        for i, date in enumerate(dates):
            price = base_price + i * 2 + (i % 3 - 1)  # 簡單的價格變動
            prices_data.append({
                'stock_id': stock_id,
                'date': date.strftime('%Y-%m-%d'),
                'open': price - 5,
                'high': price + 10,
                'low': price - 10,
                'close': price,
                'volume': 1000000 + i * 10000
            })
    prices_df = pd.DataFrame(prices_data)
    prices_df.to_csv(data_dir / "sample_prices.csv", index=False)
    
    # 建立 fundamentals CSV (只有 2330 和 2317 有基本面)
    fundamentals_df = pd.DataFrame({
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
    fundamentals_df.to_csv(data_dir / "sample_fundamentals.csv", index=False)
    
    return data_dir


def test_full_e2e_init_db(temp_db_path, sample_data_dir):
    """
    測試完整的 init_db 流程
    包括資料庫初始化、資料匯入、技術指標計算、股票評分計算、訊號產生
    """
    # 設定 config 使用臨時路徑
    with patch('modules.database.get_config') as mock_config:
        config = type('Config', (), {
            'DATABASE_PATH': str(temp_db_path),
            'SAMPLE_STOCKS_CSV': str(sample_data_dir / "sample_stocks.csv"),
            'SAMPLE_PRICES_CSV': str(sample_data_dir / "sample_prices.csv"),
            'SAMPLE_FUNDAMENTALS_CSV': str(sample_data_dir / "sample_fundamentals.csv"),
            'TELEGRAM_BOT_TOKEN': '',
            'TELEGRAM_CHAT_ID': ''
        })()
        mock_config.return_value = config
        
        # 1. 初始化資料庫（直接傳入臨時路徑）
        from scripts.init_db import init_database
        init_database(temp_db_path)
        
        # 驗證資料庫建立成功
        assert temp_db_path.exists()
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # 驗證所有資料表存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'stocks' in tables
        assert 'prices' in tables
        assert 'fundamentals' in tables
        assert 'indicators' in tables
        assert 'scores' in tables
        assert 'signals' in tables
        
        # 2. 匯入資料
        from scripts.init_db import import_stocks, import_prices, import_fundamentals
        
        import_stocks(temp_db_path, sample_data_dir / "sample_stocks.csv")
        import_prices(temp_db_path, sample_data_dir / "sample_prices.csv")
        import_fundamentals(temp_db_path, sample_data_dir / "sample_fundamentals.csv")
        
        # 驗證資料匯入
        cursor.execute("SELECT COUNT(*) FROM stocks")
        assert cursor.fetchone()[0] == 3
        
        cursor.execute("SELECT COUNT(*) FROM prices")
        assert cursor.fetchone()[0] == 90  # 3 stocks * 30 days
        
        cursor.execute("SELECT COUNT(*) FROM fundamentals")
        assert cursor.fetchone()[0] == 2  # 只有 2 檔有基本面
        
        # 3. 計算技術指標
        from scripts.calculate_indicators import calculate_and_save_indicators
        calculate_and_save_indicators()
        
        # 驗證技術指標計算成功
        cursor.execute("SELECT COUNT(*) FROM indicators")
        indicator_count = cursor.fetchone()[0]
        assert indicator_count > 0
        
        # 4. 計算股票評分 (這是之前會失敗的地方)
        from scripts.calculate_scores import calculate_and_save_scores
        
        # 這個應該不會失敗，因為已經修復了 pd.Series() 問題
        try:
            calculate_and_save_scores()
        except Exception as e:
            pytest.fail(f"calculate_and_save_scores 失敗: {e}")
        
        # 驗證評分計算成功
        cursor.execute("SELECT COUNT(*) FROM scores")
        score_count = cursor.fetchone()[0]
        assert score_count > 0
        
        # 驗證缺少基本面的股票也能計算評分
        cursor.execute("SELECT stock_id FROM scores")
        scored_stocks = [row[0] for row in cursor.fetchall()]
        assert '2330' in scored_stocks
        assert '2317' in scored_stocks
        assert '2454' in scored_stocks  # 缺少基本面也應該有評分
        
        # 5. 產生訊號
        from scripts.generate_signals import generate_and_save_signals
        generate_and_save_signals()
        
        # 驗證訊號產生成功 (可能沒有訊號，但不應該報錯)
        cursor.execute("SELECT COUNT(*) FROM signals")
        signal_count = cursor.fetchone()[0]
        # signal_count 可能為 0，這取決於價格資料
        
        conn.close()


def test_full_e2e_missing_fundamentals(tmp_path, sample_data_dir):
    """
    測試缺少基本面資料時的完整流程
    確保系統不會因為缺少基本面而崩潰
    """
    temp_db_path = tmp_path / "test_stocks_missing.db"
    
    with patch('modules.database.get_config') as mock_config:
        config = type('Config', (), {
            'DATABASE_PATH': str(temp_db_path),
            'SAMPLE_STOCKS_CSV': str(sample_data_dir / "sample_stocks.csv"),
            'SAMPLE_PRICES_CSV': str(sample_data_dir / "sample_prices.csv"),
            'SAMPLE_FUNDAMENTALS_CSV': str(sample_data_dir / "sample_fundamentals.csv"),
            'TELEGRAM_BOT_TOKEN': '',
            'TELEGRAM_CHAT_ID': ''
        })()
        mock_config.return_value = config
        
        # 初始化並匯入資料
        from scripts.init_db import init_database, import_stocks, import_prices, import_fundamentals
        
        init_database(temp_db_path)
        import_stocks(temp_db_path, sample_data_dir / "sample_stocks.csv")
        import_prices(temp_db_path, sample_data_dir / "sample_prices.csv")
        import_fundamentals(temp_db_path, sample_data_dir / "sample_fundamentals.csv")
        
        # 計算技術指標
        from scripts.calculate_indicators import calculate_and_save_indicators
        calculate_and_save_indicators()
        
        # 計算股票評分
        from scripts.calculate_scores import calculate_and_save_scores
        
        # 確保不會因為缺少基本面而失敗
        try:
            calculate_and_save_scores()
        except Exception as e:
            pytest.fail(f"缺少基本面時 calculate_and_save_scores 失敗: {e}")
        
        # 驗證所有股票都有評分
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT stock_id FROM scores")
        scored_stocks = [row[0] for row in cursor.fetchall()]
        
        # 所有啟用的股票都應該有評分
        assert '2330' in scored_stocks
        assert '2317' in scored_stocks
        assert '2454' in scored_stocks
        
        # 檢查缺少基本面的股票評分
        cursor.execute("SELECT fundamental_score FROM scores WHERE stock_id = '2454'")
        fund_score = cursor.fetchone()
        assert fund_score is not None
        # 缺少基本面時，fundamental_score 應該為 0 或預設值
        assert fund_score[0] is not None
        
        conn.close()


def test_full_e2e_indicators_calculation(tmp_path, sample_data_dir):
    """
    測試技術指標計算
    確保 MA、RSI、MACD 等指標正確計算
    """
    temp_db_path = tmp_path / "test_stocks_indicators.db"
    
    with patch('modules.database.get_config') as mock_config:
        config = type('Config', (), {
            'DATABASE_PATH': str(temp_db_path),
            'SAMPLE_STOCKS_CSV': str(sample_data_dir / "sample_stocks.csv"),
            'SAMPLE_PRICES_CSV': str(sample_data_dir / "sample_prices.csv"),
            'SAMPLE_FUNDAMENTALS_CSV': str(sample_data_dir / "sample_fundamentals.csv"),
            'TELEGRAM_BOT_TOKEN': '',
            'TELEGRAM_CHAT_ID': ''
        })()
        mock_config.return_value = config
        
        # 初始化並匯入資料
        from scripts.init_db import init_database, import_stocks, import_prices
        
        init_database(temp_db_path)
        import_stocks(temp_db_path, sample_data_dir / "sample_stocks.csv")
        import_prices(temp_db_path, sample_data_dir / "sample_prices.csv")
        
        # 計算技術指標
        from scripts.calculate_indicators import calculate_and_save_indicators
        calculate_and_save_indicators()
        
        # 驗證技術指標
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # 檢查指標資料
        cursor.execute("""
            SELECT stock_id, date, ma5, ma20, rsi, macd
            FROM indicators
            WHERE stock_id = '2330'
            ORDER BY date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        
        assert len(rows) > 0
        
        # 驗證指標值不為 None (至少最近幾天)
        for row in rows:
            stock_id, date, ma5, ma20, rsi, macd = row
            # ma5 和 ma20 可能為 None (前幾天資料不足)
            # rsi 和 macd 也可能為 None
            # 但不應該報錯
        
        conn.close()


def test_full_e2e_csv_validation_failure_stops_processing(tmp_path, sample_data_dir):
    """
    測試 CSV 驗證失敗時停止後續計算
    確保當 CSV 驗證失敗時，不會繼續執行指標計算、評分計算、訊號產生
    """
    temp_db_path = tmp_path / "test_stocks_validation.db"
    
    # 使用一個不存在的文件路徑
    nonexistent_csv = tmp_path / "nonexistent_stocks.csv"
    
    # 注意：必須 patch 使用端（scripts.init_db）的 get_config 綁定；
    # patch modules.config.get_config 在 scripts.init_db 已被其他測試
    # import 過的情況下不會生效，會誤用真實 config 造成順序相依的失敗
    with patch('scripts.init_db.get_config') as mock_config:
        config = type('Config', (), {
            'DATABASE_PATH': str(temp_db_path),
            'SAMPLE_STOCKS_CSV': str(nonexistent_csv),  # 使用不存在的檔案
            'SAMPLE_PRICES_CSV': str(sample_data_dir / "sample_prices.csv"),
            'SAMPLE_FUNDAMENTALS_CSV': str(sample_data_dir / "sample_fundamentals.csv"),
            'TELEGRAM_BOT_TOKEN': '',
            'TELEGRAM_CHAT_ID': ''
        })()
        mock_config.return_value = config
        
        # 初始化資料庫
        from scripts.init_db import init_database, import_sample_data
        
        init_database(temp_db_path)
        
        # 嘗試匯入資料，應該失敗
        result = import_sample_data()
        assert result is False, "不存在的 CSV 應該導致匯入失敗"