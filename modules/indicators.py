"""
股票追蹤與決策輔助系統 V1 - 技術指標模組
Stock Tracking & Decision Support System V1 - Technical Indicators Module
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_ma(data: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
    """
    計算移動平均線
    
    Args:
        data: 包含價格資料的 DataFrame
        period: 移動平均期間
        column: 價格欄位名稱
        
    Returns:
        移動平均線序列
    """
    return data[column].rolling(window=period).mean()


def calculate_rsi(data: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """
    計算 RSI 指標
    
    Args:
        data: 包含價格資料的 DataFrame
        period: RSI 期間
        column: 價格欄位名稱
        
    Returns:
        RSI 序列
        
    Note:
        使用簡單移動平均 (SMA) 計算 RSI，而非 Wilder's smoothing。
        這是一個簡化版本，適合教學和研究用途。
    """
    delta = data[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, 
                   column: str = 'close') -> tuple:
    """
    計算 MACD 指標
    
    Args:
        data: 包含價格資料的 DataFrame
        fast: 快線期間
        slow: 慢線期間
        signal: 訊號線期間
        column: 價格欄位名稱
        
    Returns:
        (MACD, 訊號線, 柱狀圖) 序列
    """
    # 計算快慢線
    fast_ma = data[column].ewm(span=fast, adjust=False).mean()
    slow_ma = data[column].ewm(span=slow, adjust=False).mean()
    
    # 計算 MACD 線
    macd_line = fast_ma - slow_ma
    
    # 計算訊號線
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # 計算柱狀圖
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_volume_ma(data: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    計算成交量移動平均線
    
    Args:
        data: 包含成交量資料的 DataFrame
        period: 移動平均期間
        
    Returns:
        成交量移動平均線序列
    """
    return data['volume'].rolling(window=period).mean()


def calculate_all_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    計算所有技術指標
    
    Args:
        data: 包含 OHLCV 資料的 DataFrame
        
    Returns:
        包含所有技術指標的 DataFrame
    """
    result = data.copy()
    
    # 計算移動平均線
    result['ma5'] = calculate_ma(data, 5)
    result['ma20'] = calculate_ma(data, 20)
    result['ma60'] = calculate_ma(data, 60)
    
    # 計算 RSI
    result['rsi'] = calculate_rsi(data)
    
    # 計算 MACD
    macd, signal, histogram = calculate_macd(data)
    result['macd'] = macd
    result['macd_signal'] = signal
    result['macd_histogram'] = histogram
    
    # 計算成交量移動平均線
    result['volume_ma20'] = calculate_volume_ma(data, 20)
    
    return result