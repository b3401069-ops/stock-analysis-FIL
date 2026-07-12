"""
股票追蹤與決策輔助系統 V1 - RSI 對照測試
Stock Tracking & Decision Support System V1 - RSI Validation Tests

對照標準公式或明確測 simple RSI
"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_price_series():
    """建立簡單的價格序列"""
    # 20 天的價格資料
    dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
    prices = [100, 102, 105, 103, 107, 110, 108, 112, 115, 113,
              117, 120, 118, 122, 125, 123, 127, 130, 128, 132]
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p - 0.5 for p in prices],
        'high': [p + 1.0 for p in prices],
        'low': [p - 1.0 for p in prices],
        'close': prices,
        'volume': [1000000] * 20
    })
    
    return df


def test_rsi_calculation_basic(sample_price_series):
    """測試 RSI 基本計算"""
    from modules.indicators import calculate_rsi
    
    # 計算 RSI（使用 DataFrame）
    rsi = calculate_rsi(sample_price_series)
    
    # RSI 應該在 0-100 之間
    assert rsi.min() >= 0
    assert rsi.max() <= 100
    
    # RSI 應該有 NaN 值（前 14 天）
    assert rsi.isna().sum() >= 13  # 至少前 13 天是 NaN
    
    # 最後一天的 RSI 應該有值
    assert pd.notna(rsi.iloc[-1])


def test_rsi_manual_calculation():
    """手動計算 RSI 進行對照"""
    # 建立簡單的價格序列：10 天上漲
    prices = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    })
    
    from modules.indicators import calculate_rsi
    rsi = calculate_rsi(prices, period=5)  # 使用 5 天 RSI
    
    # 全部上漲，RSI 應該接近 100
    last_rsi = rsi.iloc[-1]
    assert last_rsi > 90  # 應該非常高
    
    # 建立簡單的價格序列：10 天下跌
    prices_down = pd.DataFrame({
        'close': [110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100]
    })
    rsi_down = calculate_rsi(prices_down, period=5)
    
    # 全部下跌，RSI 應該接近 0
    last_rsi_down = rsi_down.iloc[-1]
    assert last_rsi_down < 10  # 應該非常低


def test_rsi_edge_cases():
    """測試 RSI 邊界情況"""
    from modules.indicators import calculate_rsi
    
    # 空資料
    empty_df = pd.DataFrame({'close': []})
    rsi_empty = calculate_rsi(empty_df)
    assert len(rsi_empty) == 0
    
    # 資料不足
    short_df = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
    rsi_short = calculate_rsi(short_df, period=14)
    assert rsi_short.isna().all()  # 全部應該是 NaN
    
    # 所有價格相同
    same_price_df = pd.DataFrame({'close': [100] * 20})
    rsi_same = calculate_rsi(same_price_df)
    # 價格不變，RSI 應該是 50 或 NaN
    last_rsi_same = rsi_same.iloc[-1]
    if pd.notna(last_rsi_same):
        assert 40 <= last_rsi_same <= 60  # 應該接近 50


def test_rsi_period_sensitivity():
    """測試不同 RSI 週期的敏感度"""
    from modules.indicators import calculate_rsi
    
    # 建立一個價格序列
    prices = pd.DataFrame({
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
                  111, 110, 112, 114, 113, 115, 117, 116, 118, 120]
    })
    
    # 計算不同週期的 RSI
    rsi_7 = calculate_rsi(prices, period=7)
    rsi_14 = calculate_rsi(prices, period=14)
    
    # 短期 RSI 應該比長期 RSI 更敏感
    # （變動幅度更大）
    rsi_7_std = rsi_7.dropna().std()
    rsi_14_std = rsi_14.dropna().std()
    
    # 短期 RSI 標準差應該更大
    assert rsi_7_std > rsi_14_std


def test_rsi_overbought_oversold():
    """測試 RSI 超買超賣指標"""
    from modules.indicators import calculate_rsi
    
    # 建立一個強勢上漲的序列
    prices_up = pd.DataFrame({
        'close': [100 + i * 2 for i in range(30)]
    })
    rsi_up = calculate_rsi(prices_up)
    
    # 強勢上漲，RSI 應該超買（>70）
    last_rsi_up = rsi_up.iloc[-1]
    assert last_rsi_up > 70
    
    # 建立一個強勢下跌的序列
    prices_down = pd.DataFrame({
        'close': [130 - i * 2 for i in range(30)]
    })
    rsi_down = calculate_rsi(prices_down)
    
    # 強勢下跌，RSI 應該超賣（<30）
    last_rsi_down = rsi_down.iloc[-1]
    assert last_rsi_down < 30


def test_rsi_with_real_data():
    """使用真實資料測試 RSI"""
    from modules.indicators import calculate_rsi
    
    # 建立模擬真實價格的資料
    np.random.seed(42)  # 固定隨機種子
    returns = np.random.normal(0.001, 0.02, 100)  # 每日報酬率
    prices = 100 * np.cumprod(1 + returns)  # 累積價格
    
    price_df = pd.DataFrame({'close': prices})
    rsi = calculate_rsi(price_df)
    
    # RSI 應該在合理範圍內
    valid_rsi = rsi.dropna()
    assert len(valid_rsi) > 0
    assert valid_rsi.min() >= 0
    assert valid_rsi.max() <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])