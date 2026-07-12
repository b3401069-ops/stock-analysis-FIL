#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 - 每日市場資料抓取（整合版）
Daily Market Data Fetcher (Integrated)

每天收盤後自動抓取：
1. 美股大盤指數（Yahoo Finance：S&P 500、NASDAQ、VIX）
2. 台股加權指數（Yahoo Finance：TAIEX）
3. 美國公債殖利率（Yahoo Finance：10Y、30Y）
4. 美國宏觀經濟（FRED API：CPI、失業率、GDP、聯邦基金利率）
5. 法說會紀錄（鉅亨網 API）
6. 投行觀點（鉅亨網 API）

用法：
    python scripts/fetch_earnings_analyst.py              # 全部抓取
    python scripts/fetch_earnings_analyst.py --dry-run    # 只顯示，不寫入
    python scripts/fetch_earnings_analyst.py --macro-only # 只抓 macro
    python scripts/fetch_earnings_analyst.py --earnings-only # 只抓法說會/投行
"""

import sys, json, re, time
import urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.console import safe_print
from modules.database import get_enabled_stocks, get_connection


# ============================================================
# 共用工具
# ============================================================

def safe_request(url: str, headers: dict = None, timeout: int = 15) -> str | None:
    """安全的 HTTP GET，回傳文字或 None"""
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        safe_print(f"    ⚠️  請求失敗: {e}")
        return None


def macro_exists(cursor, name: str, date: str) -> bool:
    cursor.execute("SELECT 1 FROM macro_indicators WHERE indicator_name=? AND indicator_date=?",
                   (name, date))
    return cursor.fetchone() is not None


def save_macro(cursor, name: str, date: str, value: float,
               unit: str, region: str, source: str,
               prev: float = None, change: float = None, trend: str = "") -> bool:
    if macro_exists(cursor, name, date):
        return False
    cursor.execute("""
        INSERT OR REPLACE INTO macro_indicators
        (indicator_name, indicator_date, value, unit, region, source,
         frequency, previous_value, change, trend, data_as_of)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, date, value, unit, region, source, "日", prev, change, trend, date))
    return True


def strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)


def ts_to_date(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""


# ============================================================
# 1. Yahoo Finance（美股 / 台股指數 + 公債殖利率）
# ============================================================

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"

MARKET_INDICES = [
    # 美股大盤
    {"symbol": "^GSPC",  "name": "S&P 500",            "region": "US", "unit": "點"},
    {"symbol": "^DJI",   "name": "道瓊工業指數",          "region": "US", "unit": "點"},
    {"symbol": "^IXIC",  "name": "NASDAQ",              "region": "US", "unit": "點"},
    {"symbol": "^RUT",   "name": "Russell 2000",        "region": "US", "unit": "點"},
    # 半導體（台股科技股高度相關）
    {"symbol": "^SOX",   "name": "費城半導體指數",        "region": "US", "unit": "點"},
    # 恐慌指數
    {"symbol": "^VIX",   "name": "VIX 恐慌指數",         "region": "US", "unit": ""},
    # 台股
    {"symbol": "^TWII",  "name": "台灣加權指數",          "region": "TW", "unit": "點"},
    # 公債殖利率
    {"symbol": "^TNX",   "name": "美國 10 年期公債殖利率",  "region": "US", "unit": "%"},
    {"symbol": "^TYX",   "name": "美國 30 年期公債殖利率",  "region": "US", "unit": "%"},
    # 原物料
    {"symbol": "GC=F",   "name": "黃金期貨",              "region": "US", "unit": "美元"},
    {"symbol": "CL=F",   "name": "原油期貨(WTI)",          "region": "US", "unit": "美元"},
    # 匯率
    {"symbol": "TWD=X",  "name": "USD/TWD 匯率",          "region": "TW", "unit": ""},
    # 加密貨幣
    {"symbol": "BTC-USD","name": "比特幣",                "region": "US", "unit": "美元"},
]


def fetch_yahoo_quote(symbol: str) -> dict | None:
    encoded = urllib.parse.quote(symbol, safe="")
    text = safe_request(f"{YAHOO_CHART}/{encoded}?range=5d&interval=1d")
    if not text:
        return None
    try:
        data = json.loads(text)
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev = meta.get("chartPreviousClose", 0)
        ts = meta.get("regularMarketTime", 0)
        return {
            "price": price, "previous": prev,
            "change": round(price - prev, 2) if prev else 0,
            "change_pct": round((price - prev) / prev * 100, 2) if prev else 0,
            "trade_date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "",
        }
    except Exception:
        return None


def fetch_market_indices(cursor, dry_run: bool = False) -> int:
    safe_print("\n📊 [1/3] 美股 / 台股大盤指數（Yahoo Finance）")
    saved = 0
    for idx in MARKET_INDICES:
        q = fetch_yahoo_quote(idx["symbol"])
        if not q:
            continue
        trend = "上升" if q["change_pct"] > 0.5 else "下降" if q["change_pct"] < -0.5 else "持平"
        label = f"{idx['name']}: {q['price']:.2f} {idx['unit']} ({q['change']:+.2f}, {q['change_pct']:+.2f}%)"
        if dry_run:
            safe_print(f"  📝 [DRY-RUN] {label}")
        else:
            ok = save_macro(cursor, idx["name"], q["trade_date"], q["price"],
                            idx["unit"], idx["region"], "Yahoo Finance",
                            prev=q["previous"], change=q["change_pct"], trend=trend)
            safe_print(f"  {'✅' if ok else 'ℹ️'} {label}" + ("" if ok else " (已存在)"))
            if ok:
                saved += 1
        time.sleep(0.3)
    return saved


# ============================================================
# 2. FRED API（美國宏觀經濟）
# ============================================================

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"

FRED_INDICATORS = [
    # 通膨
    {"id": "CPIAUCSL",  "name": "美國 CPI",                      "unit": "",  "region": "US"},
    {"id": "PCEPI",     "name": "美國 PCE 物價指數",                "unit": "",  "region": "US"},
    # 就業
    {"id": "UNRATE",    "name": "美國失業率",                      "unit": "%", "region": "US"},
    {"id": "ICSA",      "name": "美國初次申請失業救濟人數",           "unit": "人", "region": "US"},
    # 經濟成長
    {"id": "GDP",       "name": "美國 GDP",                       "unit": "十億美元", "region": "US"},
    # 利率
    {"id": "FEDFUNDS",  "name": "美國聯邦基金利率",                  "unit": "%", "region": "US"},
    # 公債殖利率
    {"id": "DGS10",     "name": "美國 10 年期國債殖利率",            "unit": "%", "region": "US"},
    {"id": "DGS2",      "name": "美國 2 年期國債殖利率",             "unit": "%", "region": "US"},
    # 消費者信心
    {"id": "UMCSENT",   "name": "美國密西根消費者信心指數",           "unit": "",  "region": "US"},
]


def fetch_fred_latest(indicator_id: str) -> list[dict] | None:
    """從 FRED 取得最近資料，回傳 [{date, value}, ...]"""
    import subprocess
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    url = f"{FRED_CSV}?id={indicator_id}&cosd={start}&coed={end}"
    try:
        result = subprocess.run(["curl", "-s", "--max-time", "20", url],
                                capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            return None
        text = result.stdout
    except Exception as e:
        safe_print(f"    ⚠️  FRED {indicator_id} 失敗: {e}")
        return None
    if not text:
        return None
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return None
    results = []
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) == 2 and parts[1] != ".":
            try:
                results.append({"date": parts[0], "value": float(parts[1])})
            except ValueError:
                continue
    return results if results else None


def fetch_fred_indicators(cursor, dry_run: bool = False) -> int:
    safe_print("\n📊 [2/3] 美國宏觀經濟（FRED API）")
    saved = 0
    for ind in FRED_INDICATORS:
        data = fetch_fred_latest(ind["id"])
        if not data:
            safe_print(f"  ⚠️  {ind['name']}: 無資料")
            continue
        # 取最新 2 筆計算變化
        latest = data[-1]
        prev = data[-2] if len(data) > 1 else None
        change = round(latest["value"] - prev["value"], 2) if prev else None
        change_pct = round(change / prev["value"] * 100, 2) if prev and prev["value"] else None
        trend = "上升" if change and change > 0 else "下降" if change and change < 0 else "持平"
        label = f"{ind['name']}: {latest['value']:.2f}{ind['unit']} ({latest['date']})"
        if change is not None:
            label += f" 變化: {change:+.2f}"
        if dry_run:
            safe_print(f"  📝 [DRY-RUN] {label}")
        else:
            ok = save_macro(cursor, ind["name"], latest["date"], latest["value"],
                            ind["unit"], ind["region"], "FRED",
                            prev=prev["value"] if prev else None,
                            change=change_pct, trend=trend)
            safe_print(f"  {'✅' if ok else 'ℹ️'} {label}" + ("" if ok else " (已存在)"))
            if ok:
                saved += 1
        time.sleep(1)  # FRED 需要較長間隔
    return saved


# ============================================================
# 3. 鉅亨網 API（法說會 / 投行觀點）
# ============================================================

CNYES_API = "https://api.cnyes.com/media/api/v1/search"
EC_KEYWORDS = ["法說會", "法說", "電話會議", "財報", "季報", "營收展望", "EPS", "稅後淨利"]
AV_KEYWORDS = ["目標價", "評等", "評級", "買進", "賣出", "增持", "減持", "中立", "投行", "研報", "分析師", "上修", "下修"]


def search_cnyes(keyword: str, max_pages: int = 5) -> list:
    """搜尋鉅亨網，支援分頁（每頁 20 筆）"""
    all_results = []
    for page in range(1, max_pages + 1):
        url = f"{CNYES_API}?{urllib.parse.urlencode({'q': keyword, 'page': page})}"
        text = safe_request(url)
        if not text:
            break
        try:
            items = json.loads(text).get("items", {}).get("data", [])
            if not items:
                break
            all_results.extend(items)
            total = json.loads(text).get("items", {}).get("total", 0)
            if len(all_results) >= total:
                break
        except Exception:
            break
        time.sleep(0.3)
    return all_results


def is_related(title: str, content: str, keywords: list) -> bool:
    text = title + content
    return any(kw in text for kw in keywords)


def is_stock_match(title: str, content: str, stock_id: str, stock_name: str) -> bool:
    text = title + content
    return stock_id in text or stock_name in text


def extract_sentiment(text: str) -> str:
    pos = sum(1 for k in ["樂觀", "看好", "成長", "上修", "強勁", "優於", "亮眼", "新高"] if k in text)
    neg = sum(1 for k in ["保守", "下修", "衰退", "低於", "疲弱", "下滑", "惡化"] if k in text)
    return "正面" if pos > neg else "負面" if neg > pos else "中性"


def extract_rating(text: str) -> str:
    for kw in ["強力買進", "買進", "增持", "賣出", "減持", "中立"]:
        if kw in text:
            return kw
    return ""


def extract_target_price(text: str) -> float | None:
    for pat in [r'目標價[至到]?[：:]?\s*[\$NT]*\s*([\d,]+)', r'目標價[上修下調]*至\s*[\$NT]*\s*([\d,]+)']:
        m = re.search(pat, text)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def extract_firm(text: str) -> str:
    for key, firm in {"摩根士丹利": "摩根士丹利", "大摩": "摩根士丹利", "高盛": "高盛",
                       "瑞銀": "瑞銀", "摩根大通": "摩根大通", "小摩": "摩根大通",
                       "美林": "美林", "野村": "野村", "花旗": "花旗", "麥格理": "麥格理",
                       "匯豐": "匯豐", "巴克萊": "巴克萊", "凱基": "凱基", "元大": "元大"}.items():
        if key in text:
            return firm
    return ""


def ec_exists(cursor, sid: str, date: str, q: str) -> bool:
    cursor.execute("SELECT 1 FROM earnings_calls WHERE stock_id=? AND call_date=? AND quarter=?", (sid, date, q))
    return cursor.fetchone() is not None


def av_exists(cursor, sid: str, date: str, firm: str) -> bool:
    cursor.execute("SELECT 1 FROM analyst_views WHERE stock_id=? AND report_date=? AND analyst_firm=?", (sid, date, firm))
    return cursor.fetchone() is not None


def insert_ec(cursor, d: dict) -> bool:
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO earnings_calls
            (stock_id, call_date, quarter, fiscal_year, call_time,
             management_guidance, key_highlights, revenue_guidance, earnings_guidance,
             sentiment, outlook_summary, transcript_summary, source, source_url, data_as_of)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (d["stock_id"], d["call_date"], d.get("quarter", ""), d.get("fiscal_year", ""),
              "", "", d.get("key_highlights", ""), "", "",
              d.get("sentiment", "中性"), "", d.get("transcript_summary", ""),
              d.get("source", "鉅亨網"), d.get("source_url", ""), d.get("data_as_of", d["call_date"])))
        return True
    except Exception as e:
        safe_print(f"    ❌ EC write fail: {e}")
        return False


def insert_av(cursor, d: dict) -> bool:
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO analyst_views
            (stock_id, report_date, analyst_firm, analyst_name, rating,
             target_price, previous_target, recommendation, key_findings,
             report_summary, confidence_level, source, source_url, source_type,
             is_paid_report, summary_only, data_as_of)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (d["stock_id"], d["report_date"], d.get("analyst_firm", ""), "",
              d.get("rating", ""), d.get("target_price"), None, "",
              d.get("key_findings", ""), d.get("report_summary", ""), "中",
              d.get("source", "鉅亨網"), d.get("source_url", ""), "摘要",
              0, 1, d.get("data_as_of", d["report_date"])))
        return True
    except Exception as e:
        safe_print(f"    ❌ AV write fail: {e}")
        return False

def fetch_earnings_analyst(cursor, dry_run: bool = False, days: int = 7) -> tuple[int, int]:
    """抓取並寫入法說會與投行觀點，回傳 (earnings_new, analyst_new)"""
    safe_print(f"\n📰 [3/3] 法說會 + 投行觀點（鉅亨網，搜尋 {days} 天）")
    stocks = get_enabled_stocks()
    if stocks.empty:
        safe_print("  ⚠️  沒有自選股")
        return 0, 0
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    ec_n, av_n = 0, 0
    for _, s in stocks.iterrows():
        sid, sname = s["stock_id"], s["name"]
        safe_print(f"\n  🔍 {sid} {sname}...")
        # 法說會
        for item in search_cnyes(f"{sname}法說會"):
            t, c = strip_html(item.get("title", "")), strip_html(item.get("content", ""))
            d = ts_to_date(item.get("publishAt", 0))
            nid = item.get("newsId", "")
            if not is_related(t, c, EC_KEYWORDS) or not is_stock_match(t, c, sid, sname) or d < cutoff:
                continue
            dt = datetime.strptime(d, "%Y-%m-%d")
            q = f"Q{(dt.month-1)//3+1} {dt.year}"
            if ec_exists(cursor, sid, d, q):
                safe_print(f"    ℹ️  已存在: {t[:35]}...")
                continue
            data = {"stock_id": sid, "call_date": d, "quarter": q, "fiscal_year": str(dt.year),
                    "sentiment": extract_sentiment(t+c), "key_highlights": t,
                    "transcript_summary": c[:500] or t, "source": "鉅亨網",
                    "source_url": f"https://news.cnyes.com/news/id/{nid}" if nid else "", "data_as_of": d}
            if dry_run:
                safe_print(f"    📝 [DRY-RUN] 法說會: {t[:35]}... ({d})")
            elif insert_ec(cursor, data):
                safe_print(f"    ✅ 法說會: {t[:35]}... ({d})")
                ec_n += 1
            time.sleep(0.3)
        # 投行觀點
        for item in search_cnyes(f"{sname}目標價") + search_cnyes(f"{sname}評等"):
            t, c = strip_html(item.get("title", "")), strip_html(item.get("content", ""))
            d = ts_to_date(item.get("publishAt", 0))
            nid = item.get("newsId", "")
            if not is_related(t, c, AV_KEYWORDS) or not is_stock_match(t, c, sid, sname) or d < cutoff:
                continue
            firm = extract_firm(t+c) or "市場共識"
            if av_exists(cursor, sid, d, firm):
                safe_print(f"    ℹ️  已存在: {t[:35]}...")
                continue
            text = t + c
            data = {"stock_id": sid, "report_date": d, "analyst_firm": firm,
                    "rating": extract_rating(text) or "中立", "target_price": extract_target_price(text),
                    "key_findings": t, "report_summary": c[:500] or t,
                    "source": "鉅亨網", "source_url": f"https://news.cnyes.com/news/id/{nid}" if nid else "", "data_as_of": d}
            if dry_run:
                safe_print(f"    📝 [DRY-RUN] 投行: {firm} {data['rating']} {t[:30]}... ({d})")
            elif insert_av(cursor, data):
                safe_print(f"    ✅ 投行: {firm} {data['rating']} {t[:30]}... ({d})")
                av_n += 1
            time.sleep(0.3)
    return ec_n, av_n


# ============================================================
# 4. FinMind 融資融券
# ============================================================

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"


def ensure_margin_table(cursor):
    """建立融資融券資料表"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS margin_trading (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            margin_purchase_buy INTEGER DEFAULT 0,
            margin_purchase_sell INTEGER DEFAULT 0,
            margin_purchase_today_balance INTEGER DEFAULT 0,
            short_sale_buy INTEGER DEFAULT 0,
            short_sale_sell INTEGER DEFAULT 0,
            short_sale_today_balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_id, date)
        )
    """)


def fetch_margin_trading(cursor, stock_id: str, start_date: str) -> int:
    """從 FinMind 抓取融資融券資料"""
    url = f"{FINMIND_API}?dataset=TaiwanStockMarginPurchaseShortSale&data_id={stock_id}&start_date={start_date}"
    text = safe_request(url)
    if not text:
        return 0
    try:
        data = json.loads(text)
        if data.get("status") != 200:
            return 0
        records = data.get("data", [])
    except Exception:
        return 0

    saved = 0
    for r in records:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO margin_trading
                (stock_id, date, margin_purchase_buy, margin_purchase_sell,
                 margin_purchase_today_balance, short_sale_buy, short_sale_sell,
                 short_sale_today_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("stock_id", stock_id), r.get("date", ""),
                r.get("MarginPurchaseBuy", 0), r.get("MarginPurchaseSell", 0),
                r.get("MarginPurchaseTodayBalance", 0),
                r.get("ShortSaleBuy", 0), r.get("ShortSaleSell", 0),
                r.get("ShortSaleTodayBalance", 0),
            ))
            if cursor.rowcount > 0:
                saved += 1
        except Exception:
            pass
    return saved


def detect_margin_signals(cursor, stock_id: str) -> list[str]:
    """偵測融資融券異常訊號"""
    signals = []
    cursor.execute("""
        SELECT date, margin_purchase_today_balance, short_sale_today_balance
        FROM margin_trading WHERE stock_id=?
        ORDER BY date DESC LIMIT 5
    """, (stock_id,))
    rows = cursor.fetchall()
    if len(rows) < 3:
        return signals

    # 融資餘額連續增加
    mp = [r[1] for r in rows]
    if mp[0] > mp[1] > mp[2]:
        signals.append(f"⚠️ {stock_id} 融資餘額連續增加（{mp[2]}→{mp[1]}→{mp[0]}）")

    # 融券餘額連續增加
    ss = [r[2] for r in rows]
    if ss[0] > ss[1] > ss[2]:
        signals.append(f"⚠️ {stock_id} 融券餘額連續增加（{ss[2]}→{ss[1]}→{ss[0]}）")

    return signals


def fetch_and_save_margin(cursor, dry_run: bool = False) -> tuple[int, list[str]]:
    """抓取所有自選股的融資融券資料"""
    safe_print("\n💰 [4/4] 融資融券（FinMind）")
    stocks = get_enabled_stocks()
    if stocks.empty:
        return 0, []

    ensure_margin_table(cursor)
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    total_saved = 0
    all_signals = []

    for _, s in stocks.iterrows():
        sid = s["stock_id"]
        sname = s["name"]
        safe_print(f"  🔍 {sid} {sname}...")

        if dry_run:
            safe_print(f"    📝 [DRY-RUN] 融資融券 {sid}")
            continue

        n = fetch_margin_trading(cursor, sid, start_date)
        if n > 0:
            safe_print(f"    ✅ 融資融券: {n} 筆")
            total_saved += n
        else:
            safe_print(f"    ℹ️  無新資料")

        sigs = detect_margin_signals(cursor, sid)
        all_signals.extend(sigs)
        for sig in sigs:
            safe_print(f"    {sig}")

        time.sleep(0.5)

    return total_saved, all_signals


# ============================================================
# 主流程
# ============================================================

def main():
    dry_run = "--dry-run" in sys.argv
    macro_only = "--macro-only" in sys.argv
    earnings_only = "--earnings-only" in sys.argv

    # 支援 --days N 參數（預設 7 天，可用 --days 180 抓半年）
    days = 7
    for i, arg in enumerate(sys.argv):
        if arg == "--days" and i + 1 < len(sys.argv):
            try:
                days = int(sys.argv[i + 1])
            except ValueError:
                pass

    if dry_run:
        safe_print("🔍 DRY-RUN 模式\n")
    safe_print("=" * 55)
    safe_print("每日市場資料抓取（整合版）")
    safe_print("  Yahoo Finance → 美股/台股指數")
    safe_print("  FRED API      → 美國宏觀經濟")
    safe_print("  鉅亨網 API    → 法說會/投行觀點")
    safe_print("  FinMind       → 融資融券")
    safe_print("=" * 55)

    conn = get_connection()
    cursor = conn.cursor()
    m, e, a, mg = 0, 0, 0, 0
    margin_signals = []

    if not earnings_only:
        m += fetch_market_indices(cursor, dry_run)
        m += fetch_fred_indicators(cursor, dry_run)
    if not macro_only:
        e, a = fetch_earnings_analyst(cursor, dry_run, days=days)
        mg, margin_signals = fetch_and_save_margin(cursor, dry_run)

    if not dry_run:
        conn.commit()
    conn.close()

    safe_print("\n" + "=" * 55)
    parts = []
    if m: parts.append(f"{m} 筆指標")
    if e: parts.append(f"{e} 筆法說會")
    if a: parts.append(f"{a} 筆投行觀點")
    if mg: parts.append(f"{mg} 筆融資融券")
    if margin_signals:
        parts.append(f"{len(margin_signals)} 個融資融券警訊")
    safe_print(f"✅ 新增: {'、'.join(parts)}" if parts else "ℹ️  無新資料")
    safe_print("=" * 55)


if __name__ == "__main__":
    main()
