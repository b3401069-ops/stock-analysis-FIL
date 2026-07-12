"""
股票追蹤與決策輔助系統 V1 - 訊號系統測試
Stock Tracking & Decision Support System V1 - Signals System Tests
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_data_for_signals():
    """建立範例資料用於訊號偵測"""
    dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
    np.random.seed(42)
    
    # 價格資料
    prices = [100]
    for i in range(59):
        change = np.random.normal(0, 2)
        prices.append(prices[-1] + change)
    
    prices_df = pd.DataFrame({
        'date': dates,
        'open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000000, 5000000) for _ in range(60)]
    })
    
    # 技術指標資料
    indicators_df = pd.DataFrame({
        'date': dates,
        'ma5': [100 + i * 0.1 for i in range(60)],
        'ma20': [100 + i * 0.05 for i in range(60)],
        'ma60': [100 + i * 0.02 for i in range(60)],
        'rsi': [50 + i * 0.5 for i in range(60)],
        'macd': [i * 0.1 for i in range(60)],
        'macd_signal': [i * 0.08 for i in range(60)],
        'macd_histogram': [i * 0.02 for i in range(60)],
        'volume_ma20': [1000000 + i * 10000 for i in range(60)]
    })
    
    return prices_df, indicators_df


def test_detect_signals_basic(sample_data_for_signals):
    """測試基本訊號偵測"""
    from modules.signals import detect_signals
    
    prices, indicators = sample_data_for_signals
    signals = detect_signals(prices, indicators)
    
    assert isinstance(signals, list)
    # 每個訊號應該包含必要的欄位
    for signal in signals:
        assert 'signal_type' in signal
        assert 'signal_name' in signal
        assert 'severity' in signal
        assert 'description' in signal


def test_detect_signals_rsi(sample_data_for_signals):
    """測試 RSI 訊號偵測"""
    from modules.signals import detect_signals
    
    prices, indicators = sample_data_for_signals
    
    # 修改 RSI 為超買
    indicators_modified = indicators.copy()
    indicators_modified.iloc[-1, indicators_modified.columns.get_loc('rsi')] = 75
    
    signals = detect_signals(prices, indicators_modified)
    rsi_signals = [s for s in signals if 'RSI' in s['signal_name']]
    
    assert len(rsi_signals) > 0
    assert any('超買' in s['signal_name'] for s in rsi_signals)


def test_detect_signals_macd(sample_data_for_signals):
    """測試 MACD 訊號偵測"""
    from modules.signals import detect_signals
    
    prices, indicators = sample_data_for_signals
    
    # 修改 MACD 為黃金交叉
    indicators_modified = indicators.copy()
    indicators_modified.iloc[-2, indicators_modified.columns.get_loc('macd')] = -1
    indicators_modified.iloc[-2, indicators_modified.columns.get_loc('macd_signal')] = 0
    indicators_modified.iloc[-1, indicators_modified.columns.get_loc('macd')] = 1
    indicators_modified.iloc[-1, indicators_modified.columns.get_loc('macd_signal')] = 0
    
    signals = detect_signals(prices, indicators_modified)
    macd_signals = [s for s in signals if 'MACD' in s['signal_name']]
    
    assert len(macd_signals) > 0
    assert any('黃金交叉' in s['signal_name'] for s in macd_signals)


def test_detect_signals_empty_data():
    """測試空資料"""
    from modules.signals import detect_signals
    
    empty_df = pd.DataFrame()
    signals = detect_signals(empty_df, empty_df)
    
    assert signals == []


def test_get_severity_icon():
    """測試嚴重度圖示"""
    from modules.signals import get_severity_icon
    
    assert get_severity_icon('偏多') == '🟢'
    assert get_severity_icon('偏空') == '🔴'
    assert get_severity_icon('警告') == '🟡'
    assert get_severity_icon('機會') == '🔵'
    assert get_severity_icon('未知') == '⚪'


def test_format_signal_message():
    """測試訊號訊息格式化"""
    from modules.signals import format_signal_message
    
    signal = {
        'signal_type': '技術面',
        'signal_name': 'RSI 超買',
        'severity': '警告',
        'description': 'RSI = 75，處於超買區域'
    }
    
    message = format_signal_message(signal, '台積電')
    
    assert '台積電' in message
    assert 'RSI 超買' in message
    assert '🟡' in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])