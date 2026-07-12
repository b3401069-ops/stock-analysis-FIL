"""
股票追蹤與決策輔助系統 V1 - 回測模組測試
Stock Tracking & Decision Support System V1 - Backtest Module Tests
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

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


@pytest.fixture
def fixed_price_data():
    """固定的價格資料（10 天）"""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
    
    # 建立一個簡單的價格序列：先漲後跌
    prices = [100, 102, 105, 108, 110, 107, 105, 103, 100, 98]
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p - 0.5 for p in prices],
        'high': [p + 1.0 for p in prices],
        'low': [p - 1.0 for p in prices],
        'close': prices,
        'volume': [1000000] * 10
    })
    
    return df


@pytest.fixture
def fixed_signal_data():
    """固定的訊號資料（模擬簡單策略）"""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
    
    # 訊號：1=買入, -1=賣出, 0=持有
    # 設計：第 2 天買入，第 7 天賣出
    signals = [0, 0, 1, 0, 0, 0, 0, -1, 0, 0]
    
    df = pd.DataFrame({
        'date': dates,
        'signal': signals
    })
    
    return df


def test_strategy_ma_cross(sample_price_data):
    """測試移動平均線交叉策略"""
    from modules.backtest import strategy_ma_cross
    
    result = strategy_ma_cross(sample_price_data, short_period=5, long_period=20)
    
    assert 'ma_short' in result.columns
    assert 'ma_long' in result.columns
    assert 'signal' in result.columns
    assert len(result) == 100


def test_strategy_rsi(sample_price_data):
    """測試 RSI 策略"""
    from modules.backtest import strategy_rsi
    
    result = strategy_rsi(sample_price_data, period=14, oversold=30, overbought=70)
    
    assert 'rsi' in result.columns
    assert 'signal' in result.columns
    assert len(result) == 100


def test_strategy_macd(sample_price_data):
    """測試 MACD 策略"""
    from modules.backtest import strategy_macd
    
    result = strategy_macd(sample_price_data, fast=12, slow=26, signal=9)
    
    assert 'macd' in result.columns
    assert 'macd_signal' in result.columns
    assert 'signal' in result.columns
    assert len(result) == 100


def test_run_backtest(sample_price_data):
    """測試回測執行"""
    from modules.backtest import strategy_ma_cross, run_backtest
    
    signals = strategy_ma_cross(sample_price_data, short_period=5, long_period=20)
    result = run_backtest(sample_price_data, signals)
    
    assert 'initial_capital' in result
    assert 'final_capital' in result
    assert 'total_return' in result
    assert 'annual_return' in result
    assert 'max_drawdown' in result
    assert 'total_trades' in result
    assert 'win_rate' in result
    assert 'avg_return' in result
    assert 'sharpe_ratio' in result
    assert 'buy_and_hold_return' in result
    assert 'trades' in result
    assert 'data' in result


def test_get_strategy():
    """測試取得策略函數"""
    from modules.backtest import get_strategy
    
    assert get_strategy('ma_cross') is not None
    assert get_strategy('rsi') is not None
    assert get_strategy('macd') is not None
    assert get_strategy('unknown') is None


def test_get_available_strategies():
    """測試取得可用策略列表"""
    from modules.backtest import get_available_strategies
    
    strategies = get_available_strategies()
    
    assert len(strategies) == 3
    assert all('name' in s for s in strategies)
    assert all('description' in s for s in strategies)
    assert all('params' in s for s in strategies)


def test_backtest_fixed_path_basic(fixed_price_data, fixed_signal_data):
    """測試回測基本功能"""
    from modules.backtest import run_backtest
    
    result = run_backtest(fixed_price_data, fixed_signal_data)
    
    # 檢查回測結果包含所有必要欄位
    required_keys = [
        'initial_capital', 'final_capital', 'total_return', 'annual_return',
        'max_drawdown', 'total_trades', 'win_rate', 'avg_return',
        'sharpe_ratio', 'buy_and_hold_return', 'trades', 'data'
    ]
    
    for key in required_keys:
        assert key in result, f"缺少回測結果欄位: {key}"


def test_backtest_fixed_path_trades(fixed_price_data, fixed_signal_data):
    """測試回測交易記錄"""
    from modules.backtest import run_backtest
    
    result = run_backtest(fixed_price_data, fixed_signal_data)
    
    # 應該有一筆完整的交易（買入 + 賣出）
    assert result['total_trades'] == 1
    
    # 檢查交易記錄格式
    trades = result['trades']
    assert len(trades) == 2  # 買入 + 賣出
    
    # 買入交易
    buy_trade = trades[0]
    assert buy_trade['type'] == '買入'
    assert 'date' in buy_trade
    assert 'price' in buy_trade
    assert 'signal_date' in buy_trade
    
    # 賣出交易
    sell_trade = trades[1]
    assert sell_trade['type'] == '賣出'
    assert 'profit' in sell_trade
    assert 'signal_date' in sell_trade


def test_backtest_fixed_path_look_ahead(fixed_price_data, fixed_signal_data):
    """測試 look-ahead bias 避免"""
    from modules.backtest import run_backtest
    
    result = run_backtest(fixed_price_data, fixed_signal_data)
    
    # 訊號在第 2 天產生（index=2），應在第 3 天執行
    buy_trade = result['trades'][0]
    signal_date = fixed_signal_data.iloc[2]['date']  # 訊號日
    execution_date = buy_trade['date']  # 執行日
    
    # 執行日應在訊號日之後
    assert execution_date > signal_date, "回測應避免 look-ahead bias，執行日應在訊號日之後"


def test_backtest_fixed_path_win_rate(fixed_price_data, fixed_signal_data):
    """測試勝率計算"""
    from modules.backtest import run_backtest
    
    result = run_backtest(fixed_price_data, fixed_signal_data)
    
    # 計算預期勝率
    # 買入價：第 3 天開盤價（105 - 0.5 = 104.5）
    # 賣出價：第 8 天開盤價（103 - 0.5 = 102.5）
    # 報酬率：(102.5 - 104.5) / 104.5 ≈ -1.91%
    # 這是一筆虧損交易，勝率應為 0%
    
    assert result['win_rate'] == 0.0


def test_backtest_fixed_path_max_drawdown(fixed_price_data, fixed_signal_data):
    """測試最大回撤計算"""
    from modules.backtest import run_backtest
    
    result = run_backtest(fixed_price_data, fixed_signal_data)
    
    # 最大回撤應為負數或零
    assert result['max_drawdown'] <= 0
    
    # 檢查回撤計算是否合理
    # 在這個例子中，價格從最高點 110 跌到 98，跌幅約 10.9%
    assert result['max_drawdown'] < -5  # 應該有明顯的回撤


def test_backtest_fixed_path_equity_curve(fixed_price_data, fixed_signal_data):
    """測試權益曲線"""
    from modules.backtest import run_backtest
    
    result = run_backtest(fixed_price_data, fixed_signal_data)
    df = result['data']
    
    # 檢查權益曲線欄位存在
    assert 'equity' in df.columns
    assert 'position' in df.columns
    
    # 檢查權益曲線不會出現異常值
    assert df['equity'].min() > 0  # 權益不應為負
    assert not df['equity'].isna().any()  # 不應有缺失值


def test_backtest_fixed_path_initial_capital(fixed_price_data, fixed_signal_data):
    """測試初始資金"""
    from modules.backtest import run_backtest
    
    initial_capital = 500000  # 使用不同的初始資金
    result = run_backtest(fixed_price_data, fixed_signal_data, initial_capital)
    
    assert result['initial_capital'] == initial_capital
    assert result['final_capital'] > 0


def test_backtest_open_gap():
    """
    測試 open gap 情境：
    T+1 open 和前日 close 差很多時，equity 必須反映真實成交價
    """
    from modules.backtest import run_backtest
    
    # 建立有明顯 gap 的價格資料
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    prices = pd.DataFrame({
        'date': dates,
        'open':  [100, 100, 120, 125, 130],  # 第 3 天開盤跳空 20%
        'high':  [105, 105, 125, 130, 135],
        'low':   [95, 95, 115, 120, 125],
        'close': [100, 100, 122, 128, 132],
        'volume': [1000000] * 5
    })
    
    # 訊號：第 2 天產生買入訊號，第 4 天產生賣出訊號
    signals = pd.DataFrame({
        'date': dates,
        'signal': [0, 1, 0, -1, 0]
    })
    
    result = run_backtest(prices, signals)
    trades = result['trades']
    
    # 應該有 2 筆交易（買入 + 賣出）
    assert len(trades) == 2
    
    # 買入交易：第 3 天開盤買入，價格應為 120（跳空後的開盤價）
    buy_trade = trades[0]
    assert buy_trade['type'] == '買入'
    assert buy_trade['price'] == 120  # 跳空後的開盤價
    assert buy_trade['date'] == dates[2]
    
    # 賣出交易：第 5 天開盤賣出，價格應為 130
    sell_trade = trades[1]
    assert sell_trade['type'] == '賣出'
    assert sell_trade['price'] == 130
    
    # 驗證最終權益反映真實成交價
    # 買入 120，賣出 130，報酬率 = (130-120)/120 = 8.33%
    expected_return = (130 - 120) / 120
    actual_return = (result['final_capital'] - result['initial_capital']) / result['initial_capital']
    assert abs(actual_return - expected_return) < 0.01  # 允許小誤差


def test_backtest_last_day_execution():
    """
    測試最後一日執行：
    倒數第二天訊號應在最後一天成交
    """
    from modules.backtest import run_backtest
    
    # 建立 5 天的價格資料
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    prices = pd.DataFrame({
        'date': dates,
        'open':  [100, 102, 105, 108, 112],
        'high':  [105, 107, 110, 113, 117],
        'low':   [95, 97, 100, 103, 107],
        'close': [100, 102, 105, 108, 115],
        'volume': [1000000] * 5
    })
    
    # 訊號：倒數第二天（第 4 天）產生買入訊號
    signals = pd.DataFrame({
        'date': dates,
        'signal': [0, 0, 0, 1, 0]
    })
    
    result = run_backtest(prices, signals)
    trades = result['trades']
    
    # 應該有 1 筆買入交易（最後一天執行）
    assert len(trades) == 1
    
    # 買入交易應在最後一天執行
    buy_trade = trades[0]
    assert buy_trade['type'] == '買入'
    assert buy_trade['date'] == dates[4]  # 最後一天
    assert buy_trade['price'] == 112  # 最後一天開盤價
    assert buy_trade['signal_date'] == dates[3]  # 倒數第二天產生訊號


def test_backtest_last_day_sell():
    """
    測試最後一天賣出：
    如果最後一天產生賣出訊號，不應執行（因為沒有下一天）
    """
    from modules.backtest import run_backtest
    
    # 建立 5 天的價格資料
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    prices = pd.DataFrame({
        'date': dates,
        'open':  [100, 102, 105, 108, 112],
        'high':  [105, 107, 110, 113, 117],
        'low':   [95, 97, 100, 103, 107],
        'close': [100, 102, 105, 108, 115],
        'volume': [1000000] * 5
    })
    
    # 訊號：第 2 天買入，最後一天賣出
    signals = pd.DataFrame({
        'date': dates,
        'signal': [0, 1, 0, 0, -1]
    })
    
    result = run_backtest(prices, signals)
    trades = result['trades']
    
    # 應該只有 1 筆買入交易，沒有賣出（因為最後一天的賣出訊號無法執行）
    assert len(trades) == 1
    assert trades[0]['type'] == '買入'
    
    # 最終權益應反映持有部位的未實現損益
    assert result['final_capital'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])