"""
股票追蹤與決策輔助系統 V1 - 資料庫查詢模組
Stock Tracking & Decision Support System V1 - Database Query Module
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional
from modules.config import get_config


def get_connection() -> sqlite3.Connection:
    """取得資料庫連接"""
    config = get_config()
    db_path = Path(config.DATABASE_PATH)
    conn = sqlite3.connect(db_path)
    # 啟用 foreign key 約束
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_enabled_stocks() -> pd.DataFrame:
    """取得所有啟用的自選股"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM stocks WHERE enabled = 1", conn)
    conn.close()
    return df


def get_stock_prices(stock_id: str, days: int = 60) -> pd.DataFrame:
    """取得股票價格資料"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM prices 
        WHERE stock_id = ? 
        ORDER BY date DESC 
        LIMIT ?
    """, conn, params=(stock_id, days))
    conn.close()
    return df.sort_values('date').reset_index(drop=True)


def get_all_stocks() -> pd.DataFrame:
    """取得所有自選股（含停用的）"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM stocks ORDER BY stock_id", conn)
    conn.close()
    return df


def add_stock(stock_id: str, name: str, market: str = 'TWSE',
              industry: str = '') -> bool:
    """新增自選股（已存在則更新名稱並重新啟用）"""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO stocks (stock_id, name, market, industry, enabled)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(stock_id) DO UPDATE SET
                name = excluded.name,
                market = excluded.market,
                industry = excluded.industry,
                enabled = 1
        """, (stock_id.strip(), name.strip(), market, industry))
        conn.commit()
        return True
    finally:
        conn.close()


def set_stock_enabled(stock_id: str, enabled: bool) -> bool:
    """啟用 / 停用自選股（停用後不再出現在各頁面與每日更新，資料保留）"""
    conn = get_connection()
    try:
        cursor = conn.execute("UPDATE stocks SET enabled = ? WHERE stock_id = ?",
                              (1 if enabled else 0, stock_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_stock_prices_adj(stock_id: str, days: int = 60) -> pd.DataFrame:
    """取得還原權值股價資料（供長期回測使用）

    prices_adj 表由 scripts/update_data.py 抓取 FinMind 還原股價建立；
    尚未建立或無資料時回傳空 DataFrame。
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT * FROM prices_adj
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT ?
        """, conn, params=(stock_id, days))
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()
    return df.sort_values('date').reset_index(drop=True)


def get_institutional_flows(stock_id: str, days: int = 10) -> pd.DataFrame:
    """取得三大法人買賣超（最近 N 個交易日，長格式）

    institutional_flows 表由 scripts/update_data.py 建立；
    尚未建立或無資料時回傳空 DataFrame。
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT * FROM institutional_flows
            WHERE stock_id = ?
              AND date IN (
                  SELECT DISTINCT date FROM institutional_flows
                  WHERE stock_id = ?
                  ORDER BY date DESC LIMIT ?
              )
            ORDER BY date
        """, conn, params=(stock_id, stock_id, days))
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()
    return df


def get_stock_news(stock_id: str, limit: int = 20) -> pd.DataFrame:
    """取得個股最新新聞（stock_news 表由每日更新建立，無資料時回傳空）"""
    conn = get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT date, title, link, source FROM stock_news
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT ?
        """, conn, params=(stock_id, limit))
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()
    return df


def get_latest_prices() -> pd.DataFrame:
    """取得所有自選股的最新價格"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT s.stock_id, s.name, s.market, s.industry,
               p.date as latest_date, p.close as latest_close,
               p.open, p.high, p.low, p.volume
        FROM stocks s
        LEFT JOIN (
            SELECT stock_id, date, close, open, high, low, volume,
                   ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY date DESC) as rn
            FROM prices
        ) p ON s.stock_id = p.stock_id AND p.rn = 1
        WHERE s.enabled = 1
        ORDER BY s.stock_id
    """, conn)
    conn.close()
    return df


def get_price_change(stock_id: str) -> dict:
    """取得股票漲跌幅"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT date, close FROM prices 
        WHERE stock_id = ? 
        ORDER BY date DESC 
        LIMIT 2
    """, conn, params=(stock_id,))
    conn.close()
    
    if len(df) < 2:
        return {'change': 0, 'change_pct': 0}
    
    latest = df.iloc[0]['close']
    previous = df.iloc[1]['close']
    change = latest - previous
    change_pct = (change / previous) * 100
    
    return {
        'latest_close': latest,
        'previous_close': previous,
        'change': round(change, 2),
        'change_pct': round(change_pct, 2)
    }


def get_latest_fundamentals() -> pd.DataFrame:
    """取得所有自選股的最新基本面資料"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT s.stock_id, s.name,
               f.date as fundamental_date,
               f.pe_ratio, f.pb_ratio, f.dividend_yield,
               f.market_cap, f.revenue, f.net_income, f.eps, f.roe
        FROM stocks s
        LEFT JOIN (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY date DESC) as rn
            FROM fundamentals
        ) f ON s.stock_id = f.stock_id AND f.rn = 1
        WHERE s.enabled = 1
        ORDER BY s.stock_id
    """, conn)
    conn.close()
    return df


def get_indicators(stock_id: str, days: int = 60) -> pd.DataFrame:
    """取得股票技術指標"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM indicators 
        WHERE stock_id = ? 
        ORDER BY date DESC 
        LIMIT ?
    """, conn, params=(stock_id, days))
    conn.close()
    return df.sort_values('date').reset_index(drop=True)


def save_indicators(stock_id: str, date: str, indicators: dict):
    """儲存技術指標"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO indicators 
        (stock_id, date, ma5, ma20, ma60, rsi, macd, macd_signal, macd_histogram, volume_ma20)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        stock_id, date,
        indicators.get('ma5'),
        indicators.get('ma20'),
        indicators.get('ma60'),
        indicators.get('rsi'),
        indicators.get('macd'),
        indicators.get('macd_signal'),
        indicators.get('macd_histogram'),
        indicators.get('volume_ma20')
    ))
    
    conn.commit()
    conn.close()


def clear_indicators():
    """清除所有技術指標"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM indicators")
    conn.commit()
    conn.close()


def save_score(stock_id: str, date: str, score_data: dict):
    """儲存股票評分"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO scores 
        (stock_id, date, technical_score, fundamental_score, risk_score, total_score, rating, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        stock_id, date,
        score_data.get('technical_score'),
        score_data.get('fundamental_score'),
        score_data.get('risk_score'),
        score_data.get('total_score'),
        score_data.get('rating'),
        score_data.get('description')
    ))
    
    conn.commit()
    conn.close()


def get_scores(stock_id: Optional[str] = None) -> pd.DataFrame:
    """取得股票評分"""
    conn = get_connection()
    
    if stock_id:
        df = pd.read_sql_query("""
            SELECT * FROM scores 
            WHERE stock_id = ? 
            ORDER BY date DESC
        """, conn, params=(stock_id,))
    else:
        df = pd.read_sql_query("""
            SELECT s.stock_id, s.name, sc.date, sc.technical_score,
                   sc.fundamental_score, sc.risk_score, sc.total_score,
                   sc.rating, sc.description
            FROM stocks s
            LEFT JOIN (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY date DESC) as rn
                FROM scores
            ) sc ON s.stock_id = sc.stock_id AND sc.rn = 1
            WHERE s.enabled = 1
            ORDER BY s.stock_id
        """, conn)
    
    conn.close()
    return df


def clear_scores():
    """清除所有股票評分"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scores")
    conn.commit()
    conn.close()


def save_signal(stock_id: str, date: str, signal_data: dict):
    """儲存訊號"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO signals 
        (stock_id, date, signal_type, signal_name, severity, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        stock_id, date,
        signal_data.get('signal_type'),
        signal_data.get('signal_name'),
        signal_data.get('severity'),
        signal_data.get('description')
    ))
    
    conn.commit()
    conn.close()


def get_signals(stock_id: Optional[str] = None, date: Optional[str] = None, 
                signal_type: Optional[str] = None) -> pd.DataFrame:
    """取得訊號"""
    conn = get_connection()
    
    query = """
        SELECT sig.stock_id, s.name, sig.date, sig.signal_type,
               sig.signal_name, sig.severity, sig.description
        FROM stocks s
        INNER JOIN signals sig ON s.stock_id = sig.stock_id
        WHERE s.enabled = 1
    """
    params = []
    
    if stock_id:
        query += " AND sig.stock_id = ?"
        params.append(stock_id)
    
    if date:
        query += " AND sig.date = ?"
        params.append(date)
    
    if signal_type:
        query += " AND sig.signal_type = ?"
        params.append(signal_type)
    
    query += " ORDER BY sig.date DESC, sig.severity"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_latest_signals() -> pd.DataFrame:
    """取得最新一批訊號（以資料庫中最大訊號日期為準）

    訊號日期為產生訊號時所用的最新價格日，
    因此以最大日期篩選，而非以執行當天日期篩選，
    避免資料未更新時查不到任何訊號。
    """
    conn = get_connection()
    # 明確列出欄位，避免 sig.* 與 s.stock_id 產生重複欄位
    df = pd.read_sql_query("""
        SELECT sig.stock_id, s.name, sig.date, sig.signal_type,
               sig.signal_name, sig.severity, sig.description
        FROM stocks s
        INNER JOIN signals sig ON s.stock_id = sig.stock_id
        WHERE s.enabled = 1
          AND sig.date = (SELECT MAX(date) FROM signals)
        ORDER BY sig.severity
    """, conn)
    conn.close()
    return df


def get_today_signals() -> pd.DataFrame:
    """取得今日訊號（相容舊介面，回傳最新一批訊號）"""
    return get_latest_signals()


def clear_signals():
    """清除所有訊號"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM signals")
    conn.commit()
    conn.close()