"""
股票追蹤與決策輔助系統 V1 - 股票評分模組
Stock Tracking & Decision Support System V1 - Stock Scoring Module
"""

import pandas as pd
import numpy as np
from typing import Optional
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.scoring_config import (
    SCORING_WEIGHTS, RATING_THRESHOLDS, 
    TECHNICAL_SCORE_CONFIG, FUNDAMENTAL_SCORE_CONFIG, RISK_SCORE_CONFIG
)


def calculate_technical_score(indicators: pd.DataFrame) -> float:
    """
    計算技術面評分
    
    Args:
        indicators: 技術指標資料
        
    Returns:
        技術面評分 (0-100)
    """
    if indicators.empty:
        return 0.0
    
    score = 50.0  # 基礎分數
    config = TECHNICAL_SCORE_CONFIG
    
    # 取得最新指標
    latest = indicators.iloc[-1]
    
    # RSI 評分
    rsi_config = config['rsi']
    rsi = latest.get('rsi')
    if pd.notna(rsi):
        if rsi < rsi_config['oversold']:  # 超賣
            score += 15
        elif rsi < rsi_config['optimal_low']:
            score += 10
        elif rsi > rsi_config['overbought']:  # 超買
            score -= 15
        elif rsi > rsi_config['optimal_high']:
            score -= 10
    
    # MACD 評分
    macd_config = config['macd']
    macd = latest.get('macd')
    macd_signal = latest.get('macd_signal')
    if pd.notna(macd) and pd.notna(macd_signal):
        if macd > macd_signal:  # 黃金交叉
            score += 10
        else:  # 死亡交叉
            score -= 10
    
    # 移動平均線評分
    ma_config = config['ma']
    ma5 = latest.get('ma5')
    ma20 = latest.get('ma20')
    close = latest.get('close')
    
    if pd.notna(ma5) and pd.notna(ma20) and pd.notna(close):
        if close > ma5 > ma20:  # 多頭排列
            score += 15
        elif close > ma5:
            score += 10
        elif close < ma5 < ma20:  # 空頭排列
            score -= 15
        elif close < ma5:
            score -= 10
    
    # 限制分數範圍
    return max(0, min(100, score))


def calculate_fundamental_score(fundamentals: pd.Series) -> float:
    """
    計算基本面評分
    
    Args:
        fundamentals: 基本面資料
        
    Returns:
        基本面評分 (0-100)
    """
    score = 50.0  # 基礎分數
    config = FUNDAMENTAL_SCORE_CONFIG
    
    # PE Ratio 評分 (25分)
    pe_config = config['pe_ratio']
    pe_ratio = fundamentals.get('pe_ratio')
    if pd.notna(pe_ratio):
        if pe_ratio < pe_config['optimal_low']:  # 低估
            score += 12
        elif pe_ratio < pe_config['optimal_high']:
            score += 6
        elif pe_ratio > pe_config['max_value']:  # 高估
            score -= 12
        elif pe_ratio > pe_config['optimal_high']:
            score -= 6
    
    # 殖利率評分 (25分)
    div_config = config['dividend_yield']
    dividend_yield = fundamentals.get('dividend_yield')
    if pd.notna(dividend_yield):
        if dividend_yield > div_config['optimal_high']:  # 高殖利率
            score += 12
        elif dividend_yield > div_config['optimal_low']:
            score += 6
        elif dividend_yield < div_config['optimal_low'] * 0.5:  # 低殖利率
            score -= 6
    
    # ROE 評分 (25分)
    roe = fundamentals.get('roe')
    if pd.notna(roe):
        if roe > 20:  # 高 ROE
            score += 12
        elif roe > 15:
            score += 6
        elif roe < 5:  # 低 ROE
            score -= 12
        elif roe < 10:
            score -= 6
    
    # PB Ratio 評分 (25分)
    pb_config = config['pb_ratio']
    pb_ratio = fundamentals.get('pb_ratio')
    if pd.notna(pb_ratio):
        if pb_ratio < pb_config['optimal_low']:  # 低估
            score += 12
        elif pb_ratio < pb_config['optimal_high']:
            score += 6
        elif pb_ratio > pb_config['max_value']:  # 高估
            score -= 12
        elif pb_ratio > pb_config['optimal_high']:
            score -= 6
    
    # 限制分數範圍
    return max(0, min(100, score))


def calculate_risk_score(prices: pd.DataFrame, indicators: pd.DataFrame) -> float:
    """
    計算風險評分
    
    Args:
        prices: 價格資料
        indicators: 技術指標資料
        
    Returns:
        風險評分 (0-100)，分數越高風險越低
    """
    score = 50.0  # 基礎分數
    config = RISK_SCORE_CONFIG
    
    if prices.empty:
        return score
    
    # 波動率評分 (40分)
    vol_config = config['volatility']
    if len(prices) >= 20:
        returns = prices['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 年化波動率
        
        if volatility < vol_config['low_threshold']:  # 低波動
            score += 20
        elif volatility < vol_config['low_threshold'] * 1.5:
            score += 10
        elif volatility > vol_config['high_threshold']:  # 高波動
            score -= 20
        elif volatility > vol_config['high_threshold'] * 0.8:
            score -= 10
    
    # 成交量評分 (30分)
    vol_change_config = config['volume_change']
    if not indicators.empty:
        latest = indicators.iloc[-1]
        volume_ma20 = latest.get('volume_ma20')
        
        if pd.notna(volume_ma20) and volume_ma20 > 0:
            latest_volume = prices.iloc[-1]['volume']
            volume_ratio = latest_volume / volume_ma20
            
            if volume_ratio > vol_change_config['high_threshold']:  # 放量
                score -= 10
            elif volume_ratio < vol_change_config['low_threshold']:  # 縮量
                score += 10
    
    # RSI 評分 (30分)
    if not indicators.empty:
        latest = indicators.iloc[-1]
        rsi = latest.get('rsi')
        
        if pd.notna(rsi):
            if rsi > 70:  # 超買，風險高
                score -= 15
            elif rsi < 30:  # 超賣，風險低
                score += 15
    
    # 限制分數範圍
    return max(0, min(100, score))


def calculate_trend_score(stock_id: str, conn) -> float:
    """
    計算趨勢評分

    檢查三個趨勢指標：
    1. EPS 連續成長月數（基本面表）
    2. 法人連續買超天數（法人買賣超表）
    3. 價格動能（現價 > 60 日均線）

    Args:
        stock_id: 股票代號
        conn: SQLite 資料庫連線

    Returns:
        趨勢評分 (0-100)
    """
    score = 50.0  # 基礎分數

    # --- 1. EPS 連續成長月數 ---
    try:
        eps_query = """
            SELECT date, eps FROM fundamentals
            WHERE stock_id = ? AND eps IS NOT NULL
            ORDER BY date DESC
        """
        eps_df = pd.read_sql_query(eps_query, conn, params=(stock_id,))

        if len(eps_df) >= 2:
            consecutive_growth = 0
            eps_values = eps_df['eps'].tolist()
            for i in range(len(eps_values) - 1):
                if eps_values[i] > eps_values[i + 1]:
                    consecutive_growth += 1
                else:
                    break

            if consecutive_growth >= 4:
                score += 20
            elif consecutive_growth >= 2:
                score += 12
            elif consecutive_growth >= 1:
                score += 5
            elif consecutive_growth == 0 and len(eps_values) >= 2:
                if eps_values[0] < eps_values[1]:
                    score -= 5
    except Exception:
        pass

    # --- 2. 法人連續買超天數 ---
    try:
        flow_query = """
            SELECT date, SUM(net) as total_net FROM institutional_flows
            WHERE stock_id = ?
            GROUP BY date
            ORDER BY date DESC
        """
        flow_df = pd.read_sql_query(flow_query, conn, params=(stock_id,))

        if not flow_df.empty:
            consecutive_buying = 0
            for net_val in flow_df['total_net']:
                if pd.notna(net_val) and net_val > 0:
                    consecutive_buying += 1
                else:
                    break

            if consecutive_buying >= 10:
                score += 15
            elif consecutive_buying >= 5:
                score += 10
            elif consecutive_buying >= 3:
                score += 5
    except Exception:
        pass

    # --- 3. 價格動能（現價 > 60 日均線） ---
    try:
        momentum_query = """
            SELECT p.close, i.ma60
            FROM prices p
            LEFT JOIN indicators i ON p.stock_id = i.stock_id AND p.date = i.date
            WHERE p.stock_id = ?
            ORDER BY p.date DESC
            LIMIT 1
        """
        momentum_df = pd.read_sql_query(momentum_query, conn, params=(stock_id,))

        if not momentum_df.empty:
            row = momentum_df.iloc[0]
            close = row.get('close')
            ma60 = row.get('ma60')

            if pd.notna(close) and pd.notna(ma60) and ma60 > 0:
                pct_above = (close - ma60) / ma60
                if pct_above > 0.05:
                    score += 15
                elif pct_above > 0:
                    score += 8
                elif pct_above > -0.05:
                    score -= 5
                else:
                    score -= 12
    except Exception:
        pass

    return max(0, min(100, score))


def calculate_total_score(technical_score: float, fundamental_score: float, risk_score: float) -> float:
    """
    計算總評分
    
    Args:
        technical_score: 技術面評分
        fundamental_score: 基本面評分
        risk_score: 風險評分
        
    Returns:
        總評分 (0-100)
    """
    weights = SCORING_WEIGHTS
    total = (technical_score * weights['technical'] + 
             fundamental_score * weights['fundamental'] + 
             risk_score * weights['risk'])
    return round(total, 2)


def get_rating(total_score: float) -> str:
    """
    取得評級觀察詞
    
    ⚠️ 免責聲明：此評級僅供研究參考，不構成任何投資建議。
    
    Args:
        total_score: 總評分
        
    Returns:
        評級觀察詞（研究參考用）
    """
    for rating, threshold in RATING_THRESHOLDS.items():
        if total_score >= threshold:
            return rating
    return "暫不追蹤"


def get_rating_description(total_score: float, technical_score: float, 
                          fundamental_score: float, risk_score: float) -> str:
    """
    取得評級描述
    
    Args:
        total_score: 總評分
        technical_score: 技術面評分
        fundamental_score: 基本面評分
        risk_score: 風險評分
        
    Returns:
        評級描述
    """
    rating = get_rating(total_score)
    
    # 找出最強和最弱的指標
    scores = {
        '技術面': technical_score,
        '基本面': fundamental_score,
        '風險': risk_score
    }
    
    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)
    
    description = f"{rating}（總分 {total_score:.1f}）"
    
    if scores[strongest] >= 60:
        description += f"，{strongest}表現良好"
    
    if scores[weakest] < 40:
        description += f"，{weakest}需注意"
    
    return description


def score_stock(stock_id: str, prices: pd.DataFrame, indicators: pd.DataFrame,
                fundamentals: pd.Series, conn=None) -> dict:
    """
    評分單一股票
    
    Args:
        stock_id: 股票代號
        prices: 價格資料
        indicators: 技術指標資料
        fundamentals: 基本面資料
        conn: SQLite 資料庫連線（用於計算趨勢評分）
        
    Returns:
        評分結果字典
    """
    technical_score = calculate_technical_score(indicators)
    fundamental_score = calculate_fundamental_score(fundamentals)
    risk_score = calculate_risk_score(prices, indicators)

    # 計算趨勢評分
    trend_score = calculate_trend_score(stock_id, conn) if conn else 50.0

    # 新權重：技術面 34%、基本面 25.5%、風險 25.5%、趨勢 15%
    weights = {
        'technical': 0.34,
        'fundamental': 0.255,
        'risk': 0.255,
        'trend': 0.15,
    }
    total_score = round(
        technical_score * weights['technical']
        + fundamental_score * weights['fundamental']
        + risk_score * weights['risk']
        + trend_score * weights['trend'],
        2,
    )
    rating = get_rating(total_score)
    description = get_rating_description(total_score, technical_score, fundamental_score, risk_score)

    return {
        'stock_id': stock_id,
        'technical_score': round(technical_score, 2),
        'fundamental_score': round(fundamental_score, 2),
        'risk_score': round(risk_score, 2),
        'trend_score': round(trend_score, 2),
        'total_score': total_score,
        'rating': rating,
        'description': description
    }