"""
股票追蹤與決策輔助系統 V1 - 基本測試
Stock Tracking & Decision Support System V1 - Basic Tests
"""

import pytest
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_import_indicators():
    """測試技術指標模組匯入"""
    try:
        from modules.indicators import calculate_ma, calculate_rsi, calculate_macd
        assert True
    except ImportError as e:
        pytest.fail(f"匯入技術指標模組失敗: {e}")


def test_calculate_ma():
    """測試移動平均線計算"""
    import pandas as pd
    from modules.indicators import calculate_ma
    
    # 建立測試資料
    data = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    })
    
    # 計算 5 日移動平均
    ma5 = calculate_ma(data, 5)
    
    # 檢查結果
    assert ma5 is not None
    assert len(ma5) == len(data)
    assert ma5.iloc[-1] == pytest.approx(107.0, rel=1e-2)


def test_calculate_rsi():
    """測試 RSI 計算"""
    import pandas as pd
    from modules.indicators import calculate_rsi
    
    # 建立測試資料
    data = pd.DataFrame({
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
    })
    
    # 計算 RSI
    rsi = calculate_rsi(data, period=5)
    
    # 檢查結果
    assert rsi is not None
    assert len(rsi) == len(data)
    assert 0 <= rsi.iloc[-1] <= 100


def test_calculate_macd():
    """測試 MACD 計算"""
    import pandas as pd
    from modules.indicators import calculate_macd
    
    # 建立測試資料
    data = pd.DataFrame({
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
    })
    
    # 計算 MACD
    macd, signal, histogram = calculate_macd(data)
    
    # 檢查結果
    assert macd is not None
    assert signal is not None
    assert histogram is not None
    assert len(macd) == len(data)


def test_calculate_volume_ma():
    """測試成交量移動平均線計算"""
    import pandas as pd
    from modules.indicators import calculate_volume_ma
    
    # 建立測試資料
    data = pd.DataFrame({
        'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    })
    
    # 計算 5 日成交量移動平均
    volume_ma = calculate_volume_ma(data, 5)
    
    # 檢查結果
    assert volume_ma is not None
    assert len(volume_ma) == len(data)
    assert volume_ma.iloc[-1] == pytest.approx(1700.0, rel=1e-2)


def test_calculate_all_indicators():
    """測試計算所有技術指標"""
    import pandas as pd
    from modules.indicators import calculate_all_indicators
    
    # 建立測試資料
    data = pd.DataFrame({
        'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
        'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    })
    
    # 計算所有指標
    result = calculate_all_indicators(data)
    
    # 檢查結果
    assert 'ma5' in result.columns
    assert 'ma20' in result.columns
    assert 'ma60' in result.columns
    assert 'rsi' in result.columns
    assert 'macd' in result.columns
    assert 'macd_signal' in result.columns
    assert 'macd_histogram' in result.columns
    assert 'volume_ma20' in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])