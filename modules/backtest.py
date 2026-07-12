"""
股票追蹤與決策輔助系統 V1 - 回測模組
Stock Tracking & Decision Support System V1 - Backtest Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def strategy_ma_cross(prices: pd.DataFrame, short_period: int = 5, long_period: int = 20) -> pd.DataFrame:
    """
    移動平均線交叉策略
    
    Args:
        prices: 價格資料
        short_period: 短期均線期間
        long_period: 長期均線期間
        
    Returns:
        包含訊號的 DataFrame
    """
    df = prices.copy()
    
    # 計算移動平均線
    df['ma_short'] = df['close'].rolling(window=short_period).mean()
    df['ma_long'] = df['close'].rolling(window=long_period).mean()
    
    # 產生訊號
    df['signal'] = 0
    df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1  # 買入
    df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1  # 賣出
    
    # 計算交叉點
    df['signal_change'] = df['signal'].diff()
    
    return df


def strategy_rsi(prices: pd.DataFrame, period: int = 14, 
                 oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
    """
    RSI 策略
    
    Args:
        prices: 價格資料
        period: RSI 期間
        oversold: 超賣門檻
        overbought: 超買門檻
        
    Returns:
        包含訊號的 DataFrame
    """
    df = prices.copy()
    
    # 計算 RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 產生訊號
    df['signal'] = 0
    df.loc[df['rsi'] < oversold, 'signal'] = 1  # 超賣買入
    df.loc[df['rsi'] > overbought, 'signal'] = -1  # 超買賣出
    
    return df


def strategy_macd(prices: pd.DataFrame, fast: int = 12, slow: int = 26, 
                  signal: int = 9) -> pd.DataFrame:
    """
    MACD 策略
    
    Args:
        prices: 價格資料
        fast: 快線期間
        slow: 慢線期間
        signal: 訊號線期間
        
    Returns:
        包含訊號的 DataFrame
    """
    df = prices.copy()
    
    # 計算 MACD
    fast_ma = df['close'].ewm(span=fast, adjust=False).mean()
    slow_ma = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = fast_ma - slow_ma
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    
    # 產生訊號
    df['signal'] = 0
    df.loc[df['macd'] > df['macd_signal'], 'signal'] = 1  # 黃金交叉
    df.loc[df['macd'] < df['macd_signal'], 'signal'] = -1  # 死亡交叉
    
    return df


def run_backtest(prices: pd.DataFrame, signals: pd.DataFrame,
                 initial_capital: float = 1000000,
                 buy_cost_rate: float = 0.0,
                 sell_cost_rate: float = 0.0,
                 risk_free_rate: Optional[float] = None) -> Dict:
    """
    執行回測

    ⚠️ 重要設計說明：
    - 訊號日在 T 日收盤後產生
    - 成交日在 T+1 日開盤時執行（避免 look-ahead bias）
    - 成交價使用 T+1 日開盤價（若無開盤價則使用收盤價）
    - Equity curve 使用實際成交價計算，反映真實損益
    - 交易成本以買入價上浮 buy_cost_rate、賣出價下折 sell_cost_rate 計入
      （台股參考值：買入 0.001425，賣出 0.004425 = 手續費 + 證交稅）

    Args:
        prices: 價格資料（需包含 date, open, close 欄位）
        signals: 訊號資料（需包含 date, signal 欄位）
        initial_capital: 初始資金
        buy_cost_rate: 買入成本率（手續費）
        sell_cost_rate: 賣出成本率（手續費 + 稅）
        risk_free_rate: 無風險利率，None 時使用 config.BACKTEST_RISK_FREE_RATE

    Returns:
        回測結果
    """
    if risk_free_rate is None:
        from modules.config import get_config
        risk_free_rate = get_config().BACKTEST_RISK_FREE_RATE
    # 合併資料
    df = prices[['date', 'open', 'close']].copy()
    df = df.merge(signals[['date', 'signal']], on='date', how='left')
    df['signal'] = df['signal'].fillna(0)
    
    # 建立交易日誌
    trades_log = []
    position = 0  # 0: 空手, 1: 持有
    entry_price = 0
    
    # 追蹤每日部位與權益
    positions = []
    equity_list = []
    current_equity = initial_capital
    
    for i in range(len(df)):
        current_row = df.iloc[i]
        
        # 計算前一日訊號決定今日部位
        if i > 0:
            prev_signal = df.iloc[i - 1]['signal']
            if prev_signal == 1 and position == 0:
                # 前一日產生買入訊號，今日開盤買入
                position = 1
                # 使用開盤價買入，若無則用收盤價；含買入成本
                fill_price = current_row['open'] if pd.notna(current_row['open']) else current_row['close']
                entry_price = fill_price * (1 + buy_cost_rate)
                trades_log.append({
                    'type': '買入',
                    'date': current_row['date'],
                    'price': fill_price,
                    'signal_date': df.iloc[i - 1]['date']
                })
            elif prev_signal == -1 and position == 1:
                # 前一日產生賣出訊號，今日開盤賣出；含賣出成本
                fill_price = current_row['open'] if pd.notna(current_row['open']) else current_row['close']
                exit_price = fill_price * (1 - sell_cost_rate)
                profit = (exit_price - entry_price) / entry_price
                # 更新權益：以賣出價計算
                current_equity = current_equity * (1 + profit)
                trades_log.append({
                    'type': '賣出',
                    'date': current_row['date'],
                    'price': fill_price,
                    'profit': profit,
                    'signal_date': df.iloc[i - 1]['date']
                })
                position = 0
                entry_price = 0
        
        positions.append(position)
        
        # 計算當日權益
        if position == 1:
            # 持有部位：以收盤價相對含成本進場價計算未實現損益
            current_price = current_row['close']
            day_equity = current_equity * (current_price / entry_price) if entry_price > 0 else current_equity
        else:
            # 空手：權益不變
            day_equity = current_equity
        
        equity_list.append(day_equity)
    
    df['position'] = positions
    df['equity'] = equity_list
    
    # 計算每日報酬（基於權益曲線）
    df['strategy_return'] = df['equity'].pct_change().fillna(0)
    
    # 計算收盤價報酬（買入持有）
    df['daily_return'] = df['close'].pct_change().fillna(0)
    df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1
    
    # 計算交易統計
    sell_trades = [t for t in trades_log if t['type'] == '賣出']
    total_trades = len(sell_trades)  # 完成的交易次數
    
    # 計算勝率（只計算已完成的交易）
    profits = [t['profit'] for t in sell_trades if 'profit' in t]
    winning_trades = sum(1 for p in profits if p > 0)
    win_rate = winning_trades / len(profits) if profits else 0
    
    # 計算平均報酬
    avg_return = np.mean(profits) if profits else 0
    
    # 計算最大回撤（基於每日權益曲線）
    df['peak'] = df['equity'].cummax()
    df['drawdown'] = (df['equity'] - df['peak']) / df['peak']
    max_drawdown = df['drawdown'].min()
    
    # 計算最終資金
    final_capital = df['equity'].iloc[-1]
    
    # 計算年化報酬率
    days = len(df)
    total_return = (final_capital - initial_capital) / initial_capital
    annual_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
    
    # 計算夏普比率
    excess_return = df['strategy_return'].mean() * 252 - risk_free_rate
    volatility = df['strategy_return'].std() * np.sqrt(252)
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0
    
    # 計算買入持有報酬
    buy_and_hold_return = df['cumulative_return'].iloc[-1]
    
    return {
        'initial_capital': initial_capital,
        'final_capital': round(final_capital, 2),
        'total_return': round(total_return * 100, 2),
        'annual_return': round(annual_return * 100, 2),
        'max_drawdown': round(max_drawdown * 100, 2),
        'total_trades': total_trades,
        'win_rate': round(win_rate * 100, 2),
        'avg_return': round(avg_return * 100, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'buy_and_hold_return': round(buy_and_hold_return * 100, 2),
        'trades': trades_log,
        'data': df
    }


def get_strategy(name: str):
    """取得策略函數"""
    strategies = {
        'ma_cross': strategy_ma_cross,
        'rsi': strategy_rsi,
        'macd': strategy_macd
    }
    return strategies.get(name)


def get_available_strategies() -> List[Dict]:
    """取得可用策略列表"""
    return [
        {
            'name': 'ma_cross',
            'description': '移動平均線交叉策略',
            'params': {'short_period': 5, 'long_period': 20}
        },
        {
            'name': 'rsi',
            'description': 'RSI 超買超賣策略',
            'params': {'period': 14, 'oversold': 30, 'overbought': 70}
        },
        {
            'name': 'macd',
            'description': 'MACD 黃金死亡交叉策略',
            'params': {'fast': 12, 'slow': 26, 'signal': 9}
        }
    ]