"""
股票追蹤與決策輔助系統 V1 - 訊號模組
Stock Tracking & Decision Support System V1 - Signals Module
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.signals_config import (
    RSI_SIGNALS, MACD_SIGNALS, MA_SIGNALS, 
    VOLUME_SIGNALS, PRICE_SIGNALS, SEVERITY_ICONS
)


def detect_signals(prices: pd.DataFrame, indicators: pd.DataFrame) -> List[Dict]:
    """
    偵測股票訊號
    
    Args:
        prices: 價格資料
        indicators: 技術指標資料
        
    Returns:
        訊號列表
    """
    signals = []
    
    if prices.empty or indicators.empty:
        return signals
    
    # 取得最新資料
    latest_price = prices.iloc[-1]
    latest_ind = indicators.iloc[-1]
    prev_ind = indicators.iloc[-2] if len(indicators) >= 2 else None
    
    # 1. RSI 訊號
    rsi = latest_ind.get('rsi')
    if pd.notna(rsi):
        rsi_config = RSI_SIGNALS
        overbought_threshold = rsi_config['超買']['threshold']
        oversold_threshold = rsi_config['超賣']['threshold']
        
        if rsi > overbought_threshold:
            signals.append({
                'signal_type': '技術面',
                'signal_name': 'RSI 超買',
                'severity': rsi_config['超買']['severity'],
                'description': f'RSI = {rsi:.1f}，處於超買區域，可能面臨回調風險'
            })
        elif rsi < oversold_threshold:
            signals.append({
                'signal_type': '技術面',
                'signal_name': 'RSI 超賣',
                'severity': rsi_config['超賣']['severity'],
                'description': f'RSI = {rsi:.1f}，處於超賣區域，可能存在反彈機會'
            })
    
    # 2. MACD 訊號
    macd = latest_ind.get('macd')
    macd_signal = latest_ind.get('macd_signal')
    if pd.notna(macd) and pd.notna(macd_signal) and prev_ind is not None:
        prev_macd = prev_ind.get('macd')
        prev_signal = prev_ind.get('macd_signal')
        
        if pd.notna(prev_macd) and pd.notna(prev_signal):
            # 黃金交叉
            if prev_macd <= prev_signal and macd > macd_signal:
                signals.append({
                    'signal_type': '技術面',
                    'signal_name': 'MACD 黃金交叉',
                    'severity': '偏多',
                    'description': 'MACD 線向上突破訊號線，為偏多技術訊號'
                })
            # 死亡交叉
            elif prev_macd >= prev_signal and macd < macd_signal:
                signals.append({
                    'signal_type': '技術面',
                    'signal_name': 'MACD 死亡交叉',
                    'severity': '偏空',
                    'description': 'MACD 線向下跌破訊號線，為偏空技術訊號'
                })
    
    # 3. 移動平均線訊號
    ma5 = latest_ind.get('ma5')
    ma20 = latest_ind.get('ma20')
    close = latest_price.get('close')
    
    if pd.notna(ma5) and pd.notna(ma20) and pd.notna(close):
        # 股價突破 MA20（更嚴謹的判斷：比較前一日與當日各自 MA）
        if prev_ind is not None and len(prices) >= 2:
            prev_close = prices.iloc[-2]['close']
            prev_ma20 = prev_ind.get('ma20')
            if pd.notna(prev_close) and pd.notna(prev_ma20):
                # 前一日收盤 < 前一日 MA20，且當日收盤 > 當日 MA20
                if prev_close < prev_ma20 and close > ma20:
                    signals.append({
                        'signal_type': '技術面',
                        'signal_name': '突破 MA20',
                        'severity': '偏多',
                        'description': f'股價突破 20 日均線，可能開始上漲趨勢'
                    })
                # 前一日收盤 > 前一日 MA20，且當日收盤 < 當日 MA20
                elif prev_close > prev_ma20 and close < ma20:
                    signals.append({
                        'signal_type': '技術面',
                        'signal_name': '跌破 MA20',
                        'severity': '偏空',
                        'description': f'股價跌破 20 日均線，可能開始下跌趨勢'
                    })
        
        # 多頭排列
        if close > ma5 > ma20:
            signals.append({
                'signal_type': '技術面',
                'signal_name': '多頭排列',
                'severity': '偏多',
                'description': '股價 > MA5 > MA20，為多頭排列'
            })
        # 空頭排列
        elif close < ma5 < ma20:
            signals.append({
                'signal_type': '技術面',
                'signal_name': '空頭排列',
                'severity': '偏空',
                'description': '股價 < MA5 < MA20，為空頭排列'
            })
    
    # 4. 成交量訊號
    volume = latest_price.get('volume')
    volume_ma20 = latest_ind.get('volume_ma20')
    
    if pd.notna(volume) and pd.notna(volume_ma20) and volume_ma20 > 0:
        volume_ratio = volume / volume_ma20
        volume_config = VOLUME_SIGNALS
        
        abnormal_threshold = volume_config['異常放量']['threshold']
        bullish_threshold = volume_config['放量上漲']['threshold']
        
        if volume_ratio > abnormal_threshold:
            signals.append({
                'signal_type': '成交量',
                'signal_name': '異常放量',
                'severity': volume_config['異常放量']['severity'],
                'description': f'成交量為 20 日均量的 {volume_ratio:.1f} 倍，需關注'
            })
        elif volume_ratio > bullish_threshold:
            signals.append({
                'signal_type': '成交量',
                'signal_name': '放量上漲',
                'severity': volume_config['放量上漲']['severity'],
                'description': f'成交量為 20 日均量的 {volume_ratio:.1f} 倍，配合上漲為偏多觀察'
            })
    
    # 5. 價格變動訊號
    if len(prices) >= 2:
        prev_close = prices.iloc[-2]['close']
        if pd.notna(prev_close) and prev_close > 0:
            change_pct = (close - prev_close) / prev_close * 100
            price_config = PRICE_SIGNALS
            
            surge_threshold = price_config['大幅上漲']['threshold']
            drop_threshold = price_config['大幅下跌']['threshold']
            
            if change_pct > surge_threshold:
                signals.append({
                    'signal_type': '價格',
                    'signal_name': '大幅上漲',
                    'severity': price_config['大幅上漲']['severity'],
                    'description': f'單日上漲 {change_pct:.1f}%，需注意追高風險'
                })
            elif change_pct < drop_threshold:
                signals.append({
                    'signal_type': '價格',
                    'signal_name': '大幅下跌',
                    'severity': price_config['大幅下跌']['severity'],
                    'description': f'單日下跌 {change_pct:.1f}%，需關注是否止跌'
                })
    
    return signals


def detect_chip_signals(institutional: pd.DataFrame,
                        consecutive_days: int = 3) -> List[Dict]:
    """偵測籌碼面訊號（三大法人買賣超）

    Args:
        institutional: 長格式法人買賣超資料
            （需含 date, investor_type, net 欄位，net 單位為股）
        consecutive_days: 連續買/賣超的判斷天數

    Returns:
        訊號列表（signal_type 為「籌碼面」）
    """
    signals = []

    if institutional.empty:
        return signals

    # 轉為 日期 × 法人 的淨買超矩陣
    pivot = institutional.pivot_table(index='date', columns='investor_type',
                                      values='net', aggfunc='sum').sort_index()

    def _lot(shares: float) -> str:
        """股數轉為張數字串（1 張 = 1000 股）"""
        return f"{shares / 1000:,.0f} 張"

    # 1. 外資 / 投信 連續買超或賣超
    for investor in ('外資', '投信'):
        if investor not in pivot.columns:
            continue
        recent = pivot[investor].dropna().tail(consecutive_days)
        if len(recent) < consecutive_days:
            continue

        if (recent > 0).all():
            signals.append({
                'signal_type': '籌碼面',
                'signal_name': f'{investor}連{consecutive_days}日買超',
                'severity': '偏多',
                'description': f'{investor}連續 {consecutive_days} 個交易日買超，'
                               f'合計 {_lot(recent.sum())}'
            })
        elif (recent < 0).all():
            signals.append({
                'signal_type': '籌碼面',
                'signal_name': f'{investor}連{consecutive_days}日賣超',
                'severity': '偏空',
                'description': f'{investor}連續 {consecutive_days} 個交易日賣超，'
                               f'合計 {_lot(-recent.sum())}'
            })

    # 2. 外資與投信最新一日同步動作（土洋同買 / 同賣）
    if '外資' in pivot.columns and '投信' in pivot.columns:
        last = pivot.iloc[-1]
        foreign, trust = last.get('外資'), last.get('投信')
        if pd.notna(foreign) and pd.notna(trust):
            if foreign > 0 and trust > 0:
                signals.append({
                    'signal_type': '籌碼面',
                    'signal_name': '外資投信同步買超',
                    'severity': '偏多',
                    'description': f'外資買超 {_lot(foreign)}、'
                                   f'投信買超 {_lot(trust)}，土洋同買為偏多觀察'
                })
            elif foreign < 0 and trust < 0:
                signals.append({
                    'signal_type': '籌碼面',
                    'signal_name': '外資投信同步賣超',
                    'severity': '偏空',
                    'description': f'外資賣超 {_lot(-foreign)}、'
                                   f'投信賣超 {_lot(-trust)}，土洋同賣為偏空觀察'
                })

    return signals


def get_severity_icon(severity: str) -> str:
    """取得嚴重度圖示"""
    return SEVERITY_ICONS.get(severity, '⚪')


def format_signal_message(signal: Dict, stock_name: str) -> str:
    """格式化訊號訊息"""
    icon = get_severity_icon(signal['severity'])
    return f"{icon} **{stock_name}** - {signal['signal_name']}\n{signal['description']}"