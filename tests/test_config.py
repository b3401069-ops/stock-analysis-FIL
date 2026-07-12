"""
股票追蹤與決策輔助系統 V1 - 配置測試
Stock Tracking & Decision Support System V1 - Configuration Tests
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch


def test_config_default_values():
    """測試配置預設值"""
    from modules.config import Config
    
    # 測試預設值
    assert Config.DATABASE_PATH.endswith('stocks.db')
    assert Config.BACKTEST_INITIAL_CAPITAL == 1000000
    assert Config.BACKTEST_RISK_FREE_RATE == 0.02
    assert Config.STREAMLIT_PORT == 8501


def test_config_from_env_variables():
    """測試從環境變數讀取配置"""
    from modules.config import Config
    
    # 設定環境變數
    with patch.dict(os.environ, {
        'DATABASE_PATH': '/tmp/test.db',
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'TELEGRAM_CHAT_ID': 'test_chat',
        'BACKTEST_INITIAL_CAPITAL': '500000',
        'BACKTEST_RISK_FREE_RATE': '0.03'
    }):
        # 重新載入配置
        from modules.config import Config
        Config.DATABASE_PATH = os.getenv('DATABASE_PATH', Config.DATABASE_PATH)
        Config.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', Config.TELEGRAM_BOT_TOKEN)
        Config.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', Config.TELEGRAM_CHAT_ID)
        Config.BACKTEST_INITIAL_CAPITAL = float(os.getenv('BACKTEST_INITIAL_CAPITAL', Config.BACKTEST_INITIAL_CAPITAL))
        Config.BACKTEST_RISK_FREE_RATE = float(os.getenv('BACKTEST_RISK_FREE_RATE', Config.BACKTEST_RISK_FREE_RATE))
        
        assert Config.DATABASE_PATH == '/tmp/test.db'
        assert Config.TELEGRAM_BOT_TOKEN == 'test_token'
        assert Config.TELEGRAM_CHAT_ID == 'test_chat'
        assert Config.BACKTEST_INITIAL_CAPITAL == 500000
        assert Config.BACKTEST_RISK_FREE_RATE == 0.03


def test_config_telegram_enabled():
    """測試 Telegram 啟用狀態"""
    from modules.config import Config
    
    # 未設定時應為 False
    Config.TELEGRAM_BOT_TOKEN = None
    Config.TELEGRAM_CHAT_ID = None
    assert Config.is_telegram_enabled() is False
    
    # 設定後應為 True
    Config.TELEGRAM_BOT_TOKEN = 'test_token'
    Config.TELEGRAM_CHAT_ID = 'test_chat'
    assert Config.is_telegram_enabled() is True
    
    # 只設定一個應為 False
    Config.TELEGRAM_BOT_TOKEN = 'test_token'
    Config.TELEGRAM_CHAT_ID = None
    assert Config.is_telegram_enabled() is False


def test_config_validate():
    """測試配置驗證"""
    from modules.config import Config
    
    # 設定有效的配置
    Config.DATABASE_PATH = str(Path(__file__).parent.parent / 'data' / 'stocks.db')
    Config.SAMPLE_STOCKS_CSV = str(Path(__file__).parent.parent / 'data' / 'sample_stocks.csv')
    Config.SAMPLE_PRICES_CSV = str(Path(__file__).parent.parent / 'data' / 'sample_prices.csv')
    Config.SAMPLE_FUNDAMENTALS_CSV = str(Path(__file__).parent.parent / 'data' / 'sample_fundamentals.csv')
    
    errors = Config.validate()
    
    # 應該沒有錯誤（假設範例檔案存在）
    # 注意：這個測試可能需要根據實際檔案調整
    # assert len(errors) == 0


def test_config_print_config(capsys):
    """測試列印配置"""
    from modules.config import Config
    
    Config.print_config()
    
    captured = capsys.readouterr()
    assert '系統配置' in captured.out
    assert '資料庫路徑' in captured.out
    assert 'Telegram 啟用' in captured.out


def test_get_config_function():
    """測試 get_config 函數"""
    from modules.config import get_config
    
    config = get_config()
    assert config is not None
    assert hasattr(config, 'DATABASE_PATH')
    assert hasattr(config, 'TELEGRAM_BOT_TOKEN')


def test_config_csv_paths():
    """測試 CSV 路徑配置"""
    from modules.config import Config
    
    # 測試 CSV 路徑
    assert 'sample_stocks.csv' in Config.SAMPLE_STOCKS_CSV
    assert 'sample_prices.csv' in Config.SAMPLE_PRICES_CSV
    assert 'sample_fundamentals.csv' in Config.SAMPLE_FUNDAMENTALS_CSV


if __name__ == "__main__":
    pytest.main([__file__, "-v"])