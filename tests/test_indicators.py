"""
股票追蹤與決策輔助系統 V1 - 技術指標測試
Stock Tracking & Decision Support System V1 - Technical Indicators Tests
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
def sample_price_data():
    """建立範例價格資料"""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 模擬價格資料
    base_price = 100
    prices = [base_price]
    for i in range(99):
        change = np.random.normal(0, 2)
        prices.append(prices[-1] + change)
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000000, 5000000) for _ in range(100)]
    })
    
    return df


def test_calculate_ma(sample_price_data):
    """測試移動平均線計算"""
    from modules.indicators import calculate_ma
    
    ma5 = calculate_ma(sample_price_data, 5)
    ma20 = calculate_ma(sample_price_data, 20)
    ma60 = calculate_ma(sample_price_data, 60)
    
    # 檢查長度
    assert len(ma5) == 100
    assert len(ma20) == 100
    assert len(ma60) == 100
    
    # 檢查前幾個值是 NaN
    assert pd.isna(ma5.iloc[0])
    assert pd.isna(ma5.iloc[3])
    assert not pd.isna(ma5.iloc[4])
    
    # 檢查 MA 計算正確
    assert ma5.iloc[4] == sample_price_data['close'].iloc[:5].mean()


def test_calculate_rsi(sample_price_data):
    """測試 RSI 計算"""
    from modules.indicators import calculate_rsi
    
    rsi = calculate_rsi(sample_price_data, 14)
    
    # 檢查長度
    assert len(rsi) == 100
    
    # 檢查 RSI 值範圍
    valid_rsi = rsi.dropna()
    assert all(0 <= val <= 100 for val in valid_rsi)


def test_calculate_macd(sample_price_data):
    """測試 MACD 計算"""
    from modules.indicators import calculate_macd
    
    macd, signal, histogram = calculate_macd(sample_price_data)
    
    # 檢查長度
    assert len(macd) == 100
    assert len(signal) == 100
    assert len(histogram) == 100
    
    # 檢查 MACD 關係
    valid_idx = ~pd.isna(macd) & ~pd.isna(signal) & ~pd.isna(histogram)
    assert all(abs(histogram[valid_idx] - (macd[valid_idx] - signal[valid_idx])) < 1e-10)


def test_calculate_volume_ma(sample_price_data):
    """測試成交量移動平均線計算"""
    from modules.indicators import calculate_volume_ma
    
    volume_ma20 = calculate_volume_ma(sample_price_data, 20)
    
    # 檢查長度
    assert len(volume_ma20) == 100
    
    # 檢查計算正確
    assert volume_ma20.iloc[19] == sample_price_data['volume'].iloc[:20].mean()


def test_calculate_all_indicators(sample_price_data):
    """測試計算所有技術指標"""
    from modules.indicators import calculate_all_indicators
    
    result = calculate_all_indicators(sample_price_data)
    
    # 檢查所有指標欄位存在
    expected_columns = ['ma5', 'ma20', 'ma60', 'rsi', 'macd', 'macd_signal', 'macd_histogram', 'volume_ma20']
    for col in expected_columns:
        assert col in result.columns
    
    # 檢查資料長度
    assert len(result) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])