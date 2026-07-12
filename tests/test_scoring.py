"""
股票追蹤與決策輔助系統 V1 - 評分系統測試
Stock Tracking & Decision Support System V1 - Scoring System Tests
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
def sample_indicators():
    """建立範例技術指標資料"""
    dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
    np.random.seed(42)
    
    df = pd.DataFrame({
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
    
    return df


@pytest.fixture
def sample_prices():
    """建立範例價格資料"""
    dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
    np.random.seed(42)
    
    prices = [100]
    for i in range(59):
        change = np.random.normal(0, 2)
        prices.append(prices[-1] + change)
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000000, 5000000) for _ in range(60)]
    })
    
    return df


@pytest.fixture
def sample_fundamentals():
    """建立範例基本面資料"""
    return pd.Series({
        'pe_ratio': 22.5,
        'pb_ratio': 8.2,
        'dividend_yield': 1.8,
        'roe': 28.5,
        'market_cap': 25000000000000,
        'revenue': 850000000000,
        'net_income': 350000000000,
        'eps': 13.5
    })


def test_calculate_technical_score(sample_indicators):
    """測試技術面評分計算"""
    from modules.scoring import calculate_technical_score
    
    score = calculate_technical_score(sample_indicators)
    
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_calculate_fundamental_score(sample_fundamentals):
    """測試基本面評分計算"""
    from modules.scoring import calculate_fundamental_score
    
    score = calculate_fundamental_score(sample_fundamentals)
    
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_calculate_risk_score(sample_prices, sample_indicators):
    """測試風險評分計算"""
    from modules.scoring import calculate_risk_score
    
    score = calculate_risk_score(sample_prices, sample_indicators)
    
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_calculate_total_score():
    """測試總評分計算"""
    from modules.scoring import calculate_total_score
    
    # 測試不同組合
    assert calculate_total_score(80, 70, 60) == 71.0
    assert calculate_total_score(50, 50, 50) == 50.0
    assert calculate_total_score(100, 0, 0) == 40.0


def test_get_rating():
    """測試評級觀察詞"""
    from modules.scoring import get_rating
    
    assert get_rating(85) == "強勢追蹤"
    assert get_rating(75) == "偏多觀察"
    assert get_rating(65) == "普通觀察"
    assert get_rating(55) == "風險留意"
    assert get_rating(45) == "風險升高"
    assert get_rating(35) == "暫不追蹤"


def test_score_stock(sample_prices, sample_indicators, sample_fundamentals):
    """測試單一股票評分"""
    from modules.scoring import score_stock
    
    result = score_stock('2330', sample_prices, sample_indicators, sample_fundamentals)
    
    assert 'stock_id' in result
    assert 'technical_score' in result
    assert 'fundamental_score' in result
    assert 'risk_score' in result
    assert 'total_score' in result
    assert 'rating' in result
    assert 'description' in result
    
    assert result['stock_id'] == '2330'
    assert 0 <= result['technical_score'] <= 100
    assert 0 <= result['fundamental_score'] <= 100
    assert 0 <= result['risk_score'] <= 100
    assert 0 <= result['total_score'] <= 100
    assert result['rating'] in ['強勢追蹤', '偏多觀察', '普通觀察', '風險留意', '風險升高', '暫不追蹤']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])