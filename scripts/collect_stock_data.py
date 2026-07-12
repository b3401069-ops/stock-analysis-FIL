#!/usr/bin/env python3
"""
綜合股票數據收集器 v2.0
Comprehensive Stock Data Collector

從多個數據源收集股票相關數據，用於 AI 深度分析。
支持台股（TWSE）和美股（NASDAQ/NYSE）。

數據源：
  - Yahoo Finance (yfinance): 價格、財報、分析師評級、持股結構
  - FRED: 美國宏觀經濟指標
  - Yahoo Finance Chart API: 市場指數、大宗商品、匯率
  - 鉅亨網 API: 台灣財經新聞、法說會、投行觀點
  - SEC EDGAR: 美股 10-K/10-Q 財報（未來擴展）

輸出：結構化 JSON，供 Hermes AI 進行深度分析

用法：
  python scripts/collect_stock_data.py 2330          # 台積電
  python scripts/collect_stock_data.py NVDA          # NVIDIA
  python scripts/collect_stock_data.py 2330 NVDA     # 多檔
  python scripts/collect_stock_data.py --all         # 全部自選股
  python scripts/collect_stock_data.py --macro       # 僅宏觀指標
  python scripts/collect_stock_data.py --geopolitical # 僅地緣政治
"""

import sys
import json
import time
import re
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix numpy path conflict: ensure project venv's site-packages is first
# This prevents Hermes venv's numpy (cp311) from shadowing project's (cp312)
_venv_sp = str(project_root / "venv" / "Lib" / "site-packages")
if _venv_sp in sys.path:
    sys.path.remove(_venv_sp)
    sys.path.insert(1, _venv_sp)  # After project_root, before everything else

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"ERROR: Missing package: {e}. Run: pip install yfinance pandas numpy")
    sys.exit(1)


# ============================================================
# 台股/美股代號映射
# ============================================================

# 台股代號 → yfinance symbol
TW_SYMBOL_MAP = {
    "2330": "2330.TW", "2317": "2317.TW", "2454": "2454.TW",
    "2308": "2308.TW", "2303": "2303.TW", "2881": "2881.TW",
    "2308": "2308.TW", "2412": "2412.TW", "3711": "3711.TW",
    "2882": "2882.TW", "2891": "2891.TW", "2886": "2886.TW",
    "1301": "1301.TW", "1303": "1303.TW", "1326": "1326.TW",
    "2002": "2002.TW", "2207": "2207.TW", "3008": "3008.TW",
    "3034": "3034.TW", "3037": "3037.TW", "2379": "2379.TW",
    "6505": "6505.TW", "5871": "5871.TW", "5880": "5880.TW",
    "2892": "2892.TW", "3045": "3045.TW", "2603": "2603.TW",
    "2609": "2609.TW", "2615": "2615.TW", "0050": "0050.TW",
    "0056": "0056.TW",
}

# 台股代號 → 中文名稱
TW_NAME_MAP = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科",
    "2308": "台達電", "2303": "友達", "2881": "富邦金",
    "2412": "中華電", "3711": "日月光", "2882": "國泰金",
    "2891": "中信金", "2886": "兆豐金", "1301": "台塑",
    "1303": "南亞", "1326": "台化", "2002": "中鋼",
    "2207": "和泰車", "3008": "大立光", "3034": "聯詠",
    "3037": "欣興", "2379": "瑞昱", "6505": "台塑化",
    "5871": "中租-KY", "5880": "合庫金", "2892": "第一金",
    "3045": "台灣大", "2603": "長榮", "2609": "陽明",
    "2615": "萬海", "0050": "元大台灣50", "0056": "元大高股息",
}


def detect_market(symbol: str) -> tuple:
    """偵測股票市場，回傳 (yfinance_symbol, market, name)"""
    symbol = symbol.strip().upper()
    
    # Already has .TW suffix
    if symbol.endswith(".TW"):
        code = symbol.replace(".TW", "")
        return symbol, "TWSE", TW_NAME_MAP.get(code, code)
    
    # Already has .TWO suffix (OTC)
    if symbol.endswith(".TWO"):
        code = symbol.replace(".TWO", "")
        return symbol, "TWO", code
    
    # Pure numeric → Taiwan stock
    if symbol.isdigit():
        yf_sym = f"{symbol}.TW"
        return yf_sym, "TWSE", TW_NAME_MAP.get(symbol, symbol)
    
    # Otherwise → US stock
    return symbol, "US", symbol


# ============================================================
# 數據收集：技術面
# ============================================================

def collect_technical_data(yf_symbol: str, market: str) -> Dict[str, Any]:
    """收集技術分析數據"""
    result = {
        "price_data": {},
        "technical_indicators": {},
        "volume_analysis": {},
        "support_resistance": {},
    }
    
    try:
        # Get 1 year of daily data for technical analysis
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1y", interval="1d")
        
        if hist.empty:
            return {"error": f"No price data for {yf_symbol}"}
        
        close = hist["Close"]
        volume = hist["Volume"]
        high = hist["High"]
        low = hist["Low"]
        
        # Current price info
        result["price_data"] = {
            "current_price": float(close.iloc[-1]),
            "prev_close": float(close.iloc[-2]) if len(close) > 1 else None,
            "52w_high": float(high.max()),
            "52w_low": float(low.min()),
            "price_vs_52w_high_pct": round((close.iloc[-1] / high.max() - 1) * 100, 2),
            "price_vs_52w_low_pct": round((close.iloc[-1] / low.min() - 1) * 100, 2),
            "date": str(hist.index[-1].date()),
        }
        
        # Moving averages
        result["technical_indicators"] = {
            "ma5": float(close.rolling(5).mean().iloc[-1]) if len(close) >= 5 else None,
            "ma10": float(close.rolling(10).mean().iloc[-1]) if len(close) >= 10 else None,
            "ma20": float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None,
            "ma60": float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None,
            "ma120": float(close.rolling(120).mean().iloc[-1]) if len(close) >= 120 else None,
            "ma250": float(close.rolling(250).mean().iloc[-1]) if len(close) >= 250 else None,
        }
        
        # RSI (14-day)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        result["technical_indicators"]["rsi_14"] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_hist = macd_line - signal_line
        result["technical_indicators"]["macd"] = float(macd_line.iloc[-1])
        result["technical_indicators"]["macd_signal"] = float(signal_line.iloc[-1])
        result["technical_indicators"]["macd_histogram"] = float(macd_hist.iloc[-1])
        
        # Bollinger Bands (20-day)
        if len(close) >= 20:
            bb_mid = close.rolling(20).mean()
            bb_std = close.rolling(20).std()
            result["technical_indicators"]["bb_upper"] = float((bb_mid + 2 * bb_std).iloc[-1])
            result["technical_indicators"]["bb_middle"] = float(bb_mid.iloc[-1])
            result["technical_indicators"]["bb_lower"] = float((bb_mid - 2 * bb_std).iloc[-1])
            result["technical_indicators"]["bb_position"] = round(
                (close.iloc[-1] - (bb_mid - 2*bb_std).iloc[-1]) / 
                (4 * bb_std.iloc[-1]) * 100, 1
            ) if bb_std.iloc[-1] > 0 else 50
        
        # Volume analysis
        vol_ma20 = volume.rolling(20).mean()
        result["volume_analysis"] = {
            "avg_volume_20d": int(vol_ma20.iloc[-1]) if not pd.isna(vol_ma20.iloc[-1]) else None,
            "latest_volume": int(volume.iloc[-1]),
            "volume_ratio": round(volume.iloc[-1] / vol_ma20.iloc[-1], 2) if vol_ma20.iloc[-1] > 0 else None,
            "volume_trend": "increasing" if volume.iloc[-1] > vol_ma20.iloc[-1] else "decreasing",
        }
        
        # Support/Resistance levels (simple pivot points)
        result["support_resistance"] = {
            "pivot": float((high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3),
            "r1": float(2 * (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3 - low.iloc[-1]),
            "r2": float((high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3 + (high.iloc[-1] - low.iloc[-1])),
            "s1": float(2 * (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3 - high.iloc[-1]),
            "s2": float((high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3 - (high.iloc[-1] - low.iloc[-1])),
        }
        
        # Recent price performance
        if len(close) >= 5:
            result["price_data"]["change_1d_pct"] = round((close.iloc[-1] / close.iloc[-2] - 1) * 100, 2)
        if len(close) >= 6:
            result["price_data"]["change_5d_pct"] = round((close.iloc[-1] / close.iloc[-6] - 1) * 100, 2)
        if len(close) >= 21:
            result["price_data"]["change_1m_pct"] = round((close.iloc[-1] / close.iloc[-21] - 1) * 100, 2)
        if len(close) >= 63:
            result["price_data"]["change_3m_pct"] = round((close.iloc[-1] / close.iloc[-63] - 1) * 100, 2)
        if len(close) >= 126:
            result["price_data"]["change_6m_pct"] = round((close.iloc[-1] / close.iloc[-126] - 1) * 100, 2)
        
        # Price trend analysis
        ma5 = result["technical_indicators"].get("ma5")
        ma20 = result["technical_indicators"].get("ma20")
        ma60 = result["technical_indicators"].get("ma60")
        current = close.iloc[-1]
        
        trend_signals = []
        if ma5 and ma20:
            if ma5 > ma20:
                trend_signals.append("短期均線多頭排列 (MA5 > MA20)")
            else:
                trend_signals.append("短期均線空頭排列 (MA5 < MA20)")
        if ma20 and ma60:
            if ma20 > ma60:
                trend_signals.append("中期均線多頭排列 (MA20 > MA60)")
            else:
                trend_signals.append("中期均線空頭排列 (MA20 < MA60)")
        if ma60 and current:
            if current > ma60:
                trend_signals.append("價格在半年線之上")
            else:
                trend_signals.append("價格在半年線之下")
        
        result["technical_indicators"]["trend_signals"] = trend_signals
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================
# 數據收集：基本面 / 財報
# ============================================================

def collect_fundamental_data(yf_symbol: str, market: str) -> Dict[str, Any]:
    """收集基本面和財報數據"""
    result = {
        "company_info": {},
        "valuation": {},
        "profitability": {},
        "financial_health": {},
        "growth": {},
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow": [],
        "dividends": {},
        "analyst_ratings": {},
        "ownership": {},
    }
    
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info or {}
        
        # Company info
        result["company_info"] = {
            "name": info.get("longName", info.get("shortName", "")),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "country": info.get("country", ""),
            "employees": info.get("fullTimeEmployees"),
            "description": info.get("longBusinessSummary", ""),
            "website": info.get("website", ""),
            "exchange": info.get("exchange", ""),
            "currency": info.get("currency", ""),
        }
        
        # Valuation metrics
        result["valuation"] = {
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "peg_ratio": info.get("pegRatio"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "ev_revenue": info.get("enterpriseToRevenue"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "book_value": info.get("bookValue"),
            "price_to_book": info.get("priceToBook"),
        }
        
        # Profitability
        result["profitability"] = {
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "net_margin": info.get("profitMargins"),
            "ebitda_margin": info.get("ebitdaMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
        }
        
        # Financial health
        result["financial_health"] = {
            "current_ratio": info.get("currentRatio"),
            "debt_to_equity": info.get("debtToEquity"),
            "quick_ratio": info.get("quickRatio"),
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            "free_cash_flow": info.get("freeCashflow"),
            "operating_cash_flow": info.get("operatingCashflow"),
            "revenue": info.get("totalRevenue"),
            "ebitda": info.get("ebitda"),
        }
        
        # Growth
        result["growth"] = {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
            "revenue_per_share": info.get("revenuePerShare"),
        }
        
        # Dividends
        result["dividends"] = {
            "dividend_yield": info.get("dividendYield"),
            "dividend_rate": info.get("dividendRate"),
            "payout_ratio": info.get("payoutRatio"),
            "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield"),
            "ex_dividend_date": str(info.get("exDividendDate", "")) if info.get("exDividendDate") else None,
        }
        
        # Analyst ratings
        result["analyst_ratings"] = {
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "target_mean": info.get("targetMeanPrice"),
            "target_median": info.get("targetMedianPrice"),
            "recommendation": info.get("recommendationKey", ""),
            "num_analysts": info.get("numberOfAnalystOpinions"),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
        }
        
        # Ownership
        result["ownership"] = {
            "insider_pct": info.get("heldPercentInsiders"),
            "institutional_pct": info.get("heldPercentInstitutions"),
            "float_shares": info.get("floatShares"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "short_ratio": info.get("shortRatio"),
            "short_pct_float": info.get("shortPercentOfFloat"),
        }
        
        # Get quarterly financials
        try:
            qf = ticker.quarterly_financials
            if qf is not None and not qf.empty:
                for col in list(qf.columns)[:8]:  # Last 8 quarters
                    row = {"period": str(col.date())}
                    for idx in qf.index:
                        val = qf.loc[idx, col]
                        if pd.notna(val):
                            row[str(idx)] = float(val)
                    result["income_statement"].append(row)
        except Exception:
            pass
        
        # Get quarterly balance sheet
        try:
            qbs = ticker.quarterly_balance_sheet
            if qbs is not None and not qbs.empty:
                for col in list(qbs.columns)[:8]:
                    row = {"period": str(col.date())}
                    for idx in qbs.index:
                        val = qbs.loc[idx, col]
                        if pd.notna(val):
                            row[str(idx)] = float(val)
                    result["balance_sheet"].append(row)
        except Exception:
            pass
        
        # Get quarterly cash flow
        try:
            qcf = ticker.quarterly_cashflow
            if qcf is not None and not qcf.empty:
                for col in list(qcf.columns)[:8]:
                    row = {"period": str(col.date())}
                    for idx in qcf.index:
                        val = qcf.loc[idx, col]
                        if pd.notna(val):
                            row[str(idx)] = float(val)
                    result["cash_flow"].append(row)
        except Exception:
            pass
        
        # Institutional holders
        try:
            ih = ticker.institutional_holders
            if ih is not None and not ih.empty:
                result["ownership"]["top_institutional"] = []
                for _, row in ih.head(10).iterrows():
                    holder = {}
                    for col in ih.columns:
                        val = row[col]
                        if pd.notna(val):
                            holder[str(col)] = str(val) if not isinstance(val, (int, float)) else float(val)
                    result["ownership"]["top_institutional"].append(holder)
        except Exception:
            pass
        
        # Analyst price targets
        try:
            apt = ticker.analyst_price_targets
            if apt:
                result["analyst_ratings"]["price_targets"] = apt
        except Exception:
            pass
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================
# 數據收集：新聞 / 分析師觀點
# ============================================================

def collect_news_data(symbol: str, market: str, name: str) -> Dict[str, Any]:
    """收集新聞和分析師觀點"""
    result = {
        "news": [],
        "earnings_calls": [],
        "analyst_views": [],
    }
    
    if market in ("TWSE", "TWO"):
        result = collect_tw_news(symbol, name)
    else:
        result = collect_us_news(symbol)
    
    return result


def collect_tw_news(symbol: str, name: str) -> Dict[str, Any]:
    """從鉅亨網收集台灣股票新聞"""
    result = {"news": [], "earnings_calls": [], "analyst_views": []}
    
    def safe_request(url, headers=None, timeout=15):
        if headers is None:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            return None
    
    # Search for stock news
    keywords = [
        f"{name}法說會",
        f"{name}分析",
        f"{name}營收",
        f"{name}展望",
    ]
    
    seen_ids = set()
    for keyword in keywords:
        url = f"https://api.cnyes.com/media/api/v1/search?q={urllib.parse.quote(keyword)}&page=1"
        text = safe_request(url)
        if not text:
            time.sleep(0.5)
            continue
        
        try:
            data = json.loads(text)
            items = data.get("items", {}).get("data", [])
            for item in items:
                news_id = item.get("newsId")
                if news_id in seen_ids:
                    continue
                seen_ids.add(news_id)
                
                title = re.sub(r'<[^>]+>', '', item.get("title", ""))
                content = re.sub(r'<[^>]+>', '', item.get("content", ""))
                
                # Filter: must mention the stock
                if name not in title and name not in content and symbol not in content:
                    continue
                
                pub_date = datetime.fromtimestamp(item.get("publishAt", 0)).strftime("%Y-%m-%d")
                
                entry = {
                    "title": title,
                    "date": pub_date,
                    "content": content[:500],
                    "url": f"https://news.cnyes.com/news/id/{news_id}",
                    "source": "cnyes.com",
                }
                
                # Categorize
                if "法說會" in keyword:
                    result["earnings_calls"].append(entry)
                elif "分析" in keyword:
                    result["analyst_views"].append(entry)
                else:
                    result["news"].append(entry)
        except Exception:
            pass
        
        time.sleep(0.5)
    
    return result


def collect_us_news(symbol: str) -> Dict[str, Any]:
    """收集美股新聞（從 Yahoo Finance）"""
    result = {"news": [], "earnings_calls": [], "analyst_views": []}
    
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        for item in news[:15]:
            content = item.get("content", {})
            result["news"].append({
                "title": content.get("title", item.get("title", "")),
                "date": content.get("pubDate", "")[:10],
                "summary": content.get("summary", "")[:500],
                "url": content.get("canonicalUrl", {}).get("url", ""),
                "source": content.get("provider", {}).get("displayName", "Yahoo Finance"),
            })
    except Exception:
        pass
    
    return result


# ============================================================
# 數據收集：宏觀經濟
# ============================================================

def collect_macro_data() -> Dict[str, Any]:
    """收集全球宏觀經濟指標"""
    result = {
        "us_macro": {},
        "market_indices": {},
        "commodities": {},
        "fx_rates": {},
        "bonds": {},
    }
    
    def safe_request(url, headers=None, timeout=15):
        if headers is None:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            return None
    
    def get_yf_price(symbol, name):
        encoded = urllib.parse.quote(symbol, safe="")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=5d&interval=1d"
        text = safe_request(url)
        if text:
            try:
                data = json.loads(text)
                meta = data["chart"]["result"][0]["meta"]
                return {
                    "name": name,
                    "price": meta.get("regularMarketPrice"),
                    "prev_close": meta.get("chartPreviousClose"),
                    "currency": meta.get("currency", ""),
                }
            except Exception:
                pass
        return None
    
    # Market indices
    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "道瓊工業",
        "^IXIC": "NASDAQ",
        "^RUT": "Russell 2000",
        "^SOX": "費城半導體",
        "^VIX": "VIX 恐慌指數",
        "^TWII": "台灣加權指數",
    }
    
    for sym, name in indices.items():
        data = get_yf_price(sym, name)
        if data:
            result["market_indices"][sym] = data
        time.sleep(0.2)
    
    # Commodities
    commodities = {
        "GC=F": "黃金期貨",
        "CL=F": "原油期貨 (WTI)",
        "SI=F": "白銀期貨",
    }
    
    for sym, name in commodities.items():
        data = get_yf_price(sym, name)
        if data:
            result["commodities"][sym] = data
        time.sleep(0.2)
    
    # FX
    fx = {
        "TWD=X": "USD/TWD",
        "EURUSD=X": "EUR/USD",
        "JPY=X": "USD/JPY",
        "DXY": "美元指數 (DXY)",
    }
    
    for sym, name in fx.items():
        data = get_yf_price(sym, name)
        if data:
            result["fx_rates"][sym] = data
        time.sleep(0.2)
    
    # Bonds
    bonds = {
        "^TNX": "美國10年期公債殖利率",
        "^TYX": "美國30年期公債殖利率",
        "^FVX": "美國5年期公債殖利率",
    }
    
    for sym, name in bonds.items():
        data = get_yf_price(sym, name)
        if data:
            result["bonds"][sym] = data
        time.sleep(0.2)
    
    # FRED indicators
    fred_indicators = {
        "CPIAUCSL": "CPI (消費者物價指數)",
        "UNRATE": "失業率",
        "GDP": "GDP",
        "FEDFUNDS": "聯邦基金利率",
        "DGS10": "10年期公債殖利率",
        "DGS2": "2年期公債殖利率",
        "UMCSENT": "消費者信心指數",
        "PCEPI": "PCE 物價指數",
        "ICSA": "初領失業金人數",
    }
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    for series_id, name in fred_indicators.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start_date}&coed={end_date}"
        try:
            proc = __import__("subprocess").run(
                ["curl", "-s", "--max-time", "20", url],
                capture_output=True, text=True, timeout=25
            )
            if proc.returncode == 0 and proc.stdout.strip():
                lines = proc.stdout.strip().split("\n")
                if len(lines) > 1:
                    # Get last non-empty value
                    for line in reversed(lines[1:]):
                        parts = line.split(",")
                        if len(parts) >= 2 and parts[1].strip() != ".":
                            result["us_macro"][series_id] = {
                                "name": name,
                                "value": float(parts[1].strip()),
                                "date": parts[0].strip(),
                            }
                            break
        except Exception:
            pass
        time.sleep(0.3)
    
    return result


# ============================================================
# 數據收集：行業/競爭對手
# ============================================================

def collect_industry_peers(yf_symbol: str, sector: str, industry: str) -> Dict[str, Any]:
    """收集行業同行數據"""
    result = {
        "sector": sector,
        "industry": industry,
        "peers": [],
    }
    
    try:
        ticker = yf.Ticker(yf_symbol)
        # Try to get peer info from yfinance
        info = ticker.info or {}
        
        # Get recommendations
        try:
            rec = ticker.recommendations
            if rec is not None and not rec.empty:
                result["recent_recommendations"] = []
                for _, row in rec.tail(20).iterrows():
                    entry = {}
                    for col in rec.columns:
                        val = row[col]
                        if pd.notna(val):
                            entry[str(col)] = str(val) if not isinstance(val, (int, float)) else float(val)
                    result["recent_recommendations"].append(entry)
        except Exception:
            pass
        
        # Get earnings estimates
        try:
            ee = ticker.earnings_estimate
            if ee is not None and not ee.empty:
                result["earnings_estimate"] = ee.to_dict(orient="records")
        except Exception:
            pass
        
        # Get revenue estimates
        try:
            re = ticker.revenue_estimate
            if re is not None and not re.empty:
                result["revenue_estimate"] = re.to_dict(orient="records")
        except Exception:
            pass
        
        # Get earnings history
        try:
            eh = ticker.earnings_history
            if eh is not None and not eh.empty:
                result["earnings_history"] = eh.to_dict(orient="records")
        except Exception:
            pass
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================
# 主收集流程
# ============================================================

def collect_all_for_stock(symbol: str, include_news: bool = True) -> Dict[str, Any]:
    """為單一股票收集所有數據"""
    yf_symbol, market, name = detect_market(symbol)
    
    print(f"\n{'='*60}")
    print(f"  收集 {name} ({symbol} → {yf_symbol}) 的數據...")
    print(f"  市場: {market}")
    print(f"{'='*60}")
    
    result = {
        "symbol": symbol,
        "yf_symbol": yf_symbol,
        "market": market,
        "name": name,
        "collected_at": datetime.now().isoformat(),
    }
    
    # 1. Technical data
    print("  [1/5] 技術面數據...")
    result["technical"] = collect_technical_data(yf_symbol, market)
    time.sleep(0.5)
    
    # 2. Fundamental data
    print("  [2/5] 基本面/財報數據...")
    result["fundamental"] = collect_fundamental_data(yf_symbol, market)
    time.sleep(0.5)
    
    # 3. News
    if include_news:
        print("  [3/5] 新聞/分析師觀點...")
        result["news"] = collect_news_data(symbol, market, name)
        time.sleep(0.5)
    else:
        result["news"] = {"news": [], "earnings_calls": [], "analyst_views": []}
    
    # 4. Industry peers
    sector = result["fundamental"].get("company_info", {}).get("sector", "")
    industry = result["fundamental"].get("company_info", {}).get("industry", "")
    print("  [4/5] 行業/競爭數據...")
    result["industry"] = collect_industry_peers(yf_symbol, sector, industry)
    time.sleep(0.5)
    
    # 5. Macro context
    print("  [5/5] 宏觀經濟環境...")
    result["macro"] = collect_macro_data()
    
    print(f"\n  ✅ {name} 數據收集完成")
    return result


def collect_all_watchlist(include_news: bool = True) -> Dict[str, Any]:
    """收集所有自選股數據"""
    try:
        from modules.database import get_enabled_stocks
        stocks = get_enabled_stocks()
        symbols = [s["stock_id"] for s in stocks]
    except Exception:
        # Fallback to default watchlist
        symbols = ["2330", "2317", "2454", "2308", "2303", "2881"]
    
    return collect_multiple_stocks(symbols, include_news)


def collect_multiple_stocks(symbols: List[str], include_news: bool = True) -> Dict[str, Any]:
    """收集多檔股票數據"""
    result = {
        "stocks": {},
        "macro": collect_macro_data(),
        "collected_at": datetime.now().isoformat(),
        "stock_count": len(symbols),
    }
    
    for i, symbol in enumerate(symbols):
        print(f"\n[{i+1}/{len(symbols)}] 收集 {symbol}...")
        result["stocks"][symbol] = collect_all_for_stock(symbol, include_news)
        if i < len(symbols) - 1:
            time.sleep(1)
    
    return result


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="綜合股票數據收集器")
    parser.add_argument("symbols", nargs="*", help="股票代號（台股或美股）")
    parser.add_argument("--all", action="store_true", help="收集所有自選股")
    parser.add_argument("--macro", action="store_true", help="僅收集宏觀指標")
    parser.add_argument("--geopolitical", action="store_true", help="僅收集地緣政治")
    parser.add_argument("--no-news", action="store_true", help="跳過新聞收集")
    parser.add_argument("--output", "-o", help="輸出 JSON 檔案路徑")
    parser.add_argument("--pretty", action="store_true", help="美化 JSON 輸出")
    args = parser.parse_args()
    
    if args.macro:
        data = collect_macro_data()
        data["type"] = "macro_only"
        data["collected_at"] = datetime.now().isoformat()
    elif args.all:
        data = collect_all_watchlist(not args.no_news)
    elif args.symbols:
        if len(args.symbols) == 1:
            data = collect_all_for_stock(args.symbols[0], not args.no_news)
        else:
            data = collect_multiple_stocks(args.symbols, not args.no_news)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Output
    indent = 2 if args.pretty else None
    json_str = json.dumps(data, ensure_ascii=False, indent=indent, default=str)
    
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str, encoding="utf-8")
        print(f"\n  📁 已儲存至 {out_path}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
