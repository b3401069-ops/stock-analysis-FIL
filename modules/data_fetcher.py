"""
股票追蹤與決策輔助系統 - 真實資料源模組（FinMind）
Stock Tracking & Decision Support System - Real Data Fetcher (FinMind)

透過 FinMind REST API 抓取台股股價與估值資料，寫入 SQLite。
API 文件：https://finmind.github.io/
免費 token 註冊：https://finmindtrade.com/
"""

import sqlite3
import pandas as pd
import requests
from typing import Optional
from datetime import datetime, timedelta
from modules.config import get_config
from modules.console import safe_print

FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"


class FinMindTierError(RuntimeError):
    """FinMind 方案等級不足（該 dataset 需要 Backer/Sponsor 贊助方案）"""

# FinMind 欄位 -> 本系統 prices 表欄位
PRICE_COLUMN_MAP = {
    'date': 'date',
    'stock_id': 'stock_id',
    'open': 'open',
    'max': 'high',
    'min': 'low',
    'close': 'close',
    'Trading_Volume': 'volume',
}

# FinMind 三大法人代碼 -> 中文名稱
INSTITUTIONAL_NAME_MAP = {
    'Foreign_Investor': '外資',
    'Investment_Trust': '投信',
    'Dealer_self': '自營商(自行買賣)',
    'Dealer_Hedging': '自營商(避險)',
    'Foreign_Dealer_Self': '外資自營商',
}

# FinMind TaiwanStockPER 欄位 -> 本系統 fundamentals 表欄位
VALUATION_COLUMN_MAP = {
    'date': 'date',
    'stock_id': 'stock_id',
    'PER': 'pe_ratio',
    'PBR': 'pb_ratio',
    'dividend_yield': 'dividend_yield',
}


class FinMindFetcher:
    """FinMind 資料抓取器"""

    def __init__(self, token: Optional[str] = None,
                 api_url: str = FINMIND_API_URL,
                 timeout: int = 30):
        config = get_config()
        self.token = token if token is not None else getattr(config, 'FINMIND_TOKEN', None)
        self.api_url = api_url
        self.timeout = timeout
        # 記錄本次執行中確認為方案等級不足的 dataset，避免重複請求
        self.tier_blocked = set()

        if not self.token:
            safe_print("⚠️  未設定 FINMIND_TOKEN，將以匿名方式呼叫（300 次/小時，有 token 為 600 次/小時）")
            safe_print("    可至 https://finmindtrade.com/ 註冊免費 token 並填入 .env")

    def _request(self, dataset: str, data_id: Optional[str],
                 start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """呼叫 FinMind API，回傳原始 DataFrame

        Args:
            dataset: FinMind dataset 名稱
            data_id: 資料代號（股票代號、幣別、央行代碼等），
                     部分 dataset（如 GoldPrice）不需要，傳 None
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 結束日期，None 表示到最新

        Returns:
            原始資料 DataFrame，無資料時為空 DataFrame

        Raises:
            RuntimeError: API 回應錯誤（HTTP 錯誤或 FinMind status != 200）
        """
        params = {
            'dataset': dataset,
            'start_date': start_date,
        }
        if data_id:
            params['data_id'] = data_id
        if end_date:
            params['end_date'] = end_date

        # token 以 Bearer header 傳遞（官方建議），避免出現在 URL 與 log
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            response = requests.get(self.api_url, params=params,
                                    headers=headers, timeout=self.timeout)
            if response.status_code == 402:
                raise RuntimeError(
                    "FinMind API 額度已用盡（HTTP 402），請等待下一小時或升級方案。"
                    "可至 https://api.web.finmindtrade.com/v2/user_info 查詢用量")
            if response.status_code == 400:
                # FinMind 以 HTTP 400 + JSON msg 回報方案等級不足等錯誤
                try:
                    msg = response.json().get('msg', '')
                except ValueError:
                    msg = response.text[:200]
                if 'level' in msg.lower():
                    raise FinMindTierError(
                        f"dataset {dataset} 需要 FinMind 贊助方案（{msg}）")
                raise RuntimeError(f"FinMind API 錯誤: {msg}")
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"FinMind API 連線失敗: {e}") from e

        payload = response.json()
        if payload.get('status') != 200:
            raise RuntimeError(f"FinMind API 錯誤: {payload.get('msg', payload)}")

        return pd.DataFrame(payload.get('data', []))

    def fetch_prices(self, stock_id: str, start_date: str,
                     end_date: Optional[str] = None) -> pd.DataFrame:
        """抓取日 K 股價（TaiwanStockPrice）

        Returns:
            欄位為 stock_id, date, open, high, low, close, volume 的 DataFrame
        """
        raw = self._request('TaiwanStockPrice', stock_id, start_date, end_date)
        if raw.empty:
            return pd.DataFrame(columns=list(PRICE_COLUMN_MAP.values()))

        df = raw[list(PRICE_COLUMN_MAP.keys())].rename(columns=PRICE_COLUMN_MAP)
        # 剔除無效資料列（例如停牌日 open/close 為 0）
        df = df[(df['close'] > 0) & (df['open'] > 0)].reset_index(drop=True)
        return df

    def fetch_valuation(self, stock_id: str, start_date: str,
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """抓取估值資料（TaiwanStockPER：PER / PBR / 殖利率，日頻）

        Returns:
            欄位為 stock_id, date, pe_ratio, pb_ratio, dividend_yield 的 DataFrame
        """
        raw = self._request('TaiwanStockPER', stock_id, start_date, end_date)
        if raw.empty:
            return pd.DataFrame(columns=list(VALUATION_COLUMN_MAP.values()))

        return raw[list(VALUATION_COLUMN_MAP.keys())].rename(columns=VALUATION_COLUMN_MAP)

    def fetch_news(self, stock_id: str, day: str) -> pd.DataFrame:
        """抓取個股單日新聞（TaiwanStockNews，一次請求限單日）

        Args:
            stock_id: 股票代號
            day: 日期 (YYYY-MM-DD)

        Returns:
            欄位為 stock_id, date, title, link, source 的 DataFrame
        """
        raw = self._request('TaiwanStockNews', stock_id, day)
        if raw.empty:
            return pd.DataFrame(columns=['stock_id', 'date', 'title', 'link', 'source'])

        return pd.DataFrame({
            'stock_id': raw['stock_id'],
            'date': raw['date'],
            'title': raw['title'],
            'link': raw['link'],
            'source': raw['source'],
        })

    def fetch_stock_info(self, stock_id: str) -> Optional[dict]:
        """查詢股票基本資料（TaiwanStockInfo：名稱、產業、市場別）

        Returns:
            {'stock_id', 'name', 'industry', 'market'}，查無此股票時 None
        """
        raw = self._request('TaiwanStockInfo', stock_id, '2020-01-01')
        if raw.empty:
            return None
        row = raw.iloc[0]
        market_map = {'twse': 'TWSE', 'tpex': 'TPEx', 'emerging': '興櫃'}
        return {
            'stock_id': str(row['stock_id']),
            'name': str(row['stock_name']),
            'industry': str(row.get('industry_category', '')),
            'market': market_map.get(str(row.get('type', '')).lower(),
                                     str(row.get('type', ''))),
        }

    def fetch_prices_adj(self, stock_id: str, start_date: str,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """抓取還原權值日 K（TaiwanStockPriceAdj）

        還原權值股價已調整除權息，適合長期回測，
        欄位格式與 fetch_prices 相同。
        """
        raw = self._request('TaiwanStockPriceAdj', stock_id, start_date, end_date)
        if raw.empty:
            return pd.DataFrame(columns=list(PRICE_COLUMN_MAP.values()))

        df = raw[list(PRICE_COLUMN_MAP.keys())].rename(columns=PRICE_COLUMN_MAP)
        df = df[(df['close'] > 0) & (df['open'] > 0)].reset_index(drop=True)
        return df

    def fetch_institutional(self, stock_id: str, start_date: str,
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """抓取三大法人買賣超（TaiwanStockInstitutionalInvestorsBuySell）

        Returns:
            欄位為 stock_id, date, investor_type, buy, sell, net 的 DataFrame
            （buy/sell/net 單位為股，net = buy - sell）
        """
        raw = self._request('TaiwanStockInstitutionalInvestorsBuySell',
                            stock_id, start_date, end_date)
        if raw.empty:
            return pd.DataFrame(columns=['stock_id', 'date', 'investor_type',
                                         'buy', 'sell', 'net'])

        df = pd.DataFrame({
            'stock_id': raw['stock_id'],
            'date': raw['date'],
            'investor_type': raw['name'].map(
                lambda n: INSTITUTIONAL_NAME_MAP.get(n, n)),
            'buy': raw['buy'].astype('int64'),
            'sell': raw['sell'].astype('int64'),
        })
        df['net'] = df['buy'] - df['sell']
        return df

    def fetch_month_revenue(self, stock_id: str, start_date: str) -> Optional[dict]:
        """抓取最新一筆月營收（TaiwanStockMonthRevenue）

        Returns:
            {'date', 'revenue', 'revenue_year', 'revenue_month'}，無資料時 None
        """
        raw = self._request('TaiwanStockMonthRevenue', stock_id, start_date)
        if raw.empty:
            return None
        latest = raw.sort_values('date').iloc[-1]
        return {
            'date': latest['date'],
            'revenue': float(latest['revenue']),
            'revenue_year': int(latest['revenue_year']),
            'revenue_month': int(latest['revenue_month']),
        }

    def fetch_latest_financials(self, stock_id: str, start_date: str) -> dict:
        """抓取最新一季財報的 EPS 與稅後淨利（TaiwanStockFinancialStatements）

        資料為長格式（date, stock_id, type, value, origin_name），
        取最新一季，抽出 EPS 與 IncomeAfterTaxes。

        Returns:
            {'date', 'eps', 'net_income'}，缺項為 None；完全無資料時空 dict
        """
        raw = self._request('TaiwanStockFinancialStatements', stock_id, start_date)
        if raw.empty:
            return {}
        latest_date = raw['date'].max()
        latest = raw[raw['date'] == latest_date]

        def _pick(type_name):
            rows = latest[latest['type'] == type_name]
            return float(rows.iloc[0]['value']) if not rows.empty else None

        return {
            'date': latest_date,
            'eps': _pick('EPS'),
            'net_income': _pick('IncomeAfterTaxes'),
        }

    def fetch_macro(self, spec: dict, start_date: str) -> pd.DataFrame:
        """依 spec 抓取單一宏觀指標

        Args:
            spec: {'dataset', 'data_id', 'indicator_name', 'value_column',
                   'unit', 'region', 'frequency'}
            start_date: 起始日期

        Returns:
            欄位為 indicator_name, indicator_date, value, unit, region,
            source, frequency 的 DataFrame
        """
        raw = self._request(spec['dataset'], spec.get('data_id'), start_date)
        if raw.empty or spec['value_column'] not in raw.columns:
            return pd.DataFrame(columns=['indicator_name', 'indicator_date', 'value',
                                         'unit', 'region', 'source', 'frequency'])

        df = pd.DataFrame({
            'indicator_name': spec['indicator_name'],
            'indicator_date': raw['date'],
            'value': pd.to_numeric(raw[spec['value_column']], errors='coerce'),
            'unit': spec.get('unit', ''),
            'region': spec.get('region', ''),
            'source': 'FinMind',
            'frequency': spec.get('frequency', ''),
        })
        # 剔除無效值；positive_only 的指標（如匯率）再濾掉 FinMind 以 -1/0 標記的缺值
        # 注意：利率可能為 0 或負值（如 BOJ），不可一律過濾
        df = df.dropna(subset=['value'])
        if spec.get('positive_only'):
            df = df[df['value'] > 0]
        return df.reset_index(drop=True)


def get_last_price_date(stock_id: str) -> Optional[str]:
    """取得資料庫中該股票最後一筆價格日期，無資料時回傳 None"""
    from modules.database import get_connection
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT MAX(date) FROM prices WHERE stock_id = ?", (stock_id,)
        ).fetchone()
        return row[0] if row and row[0] else None
    finally:
        conn.close()


def save_prices(df: pd.DataFrame) -> int:
    """將價格 DataFrame 寫入 prices 表（以 stock_id+date 去重覆蓋）

    Returns:
        寫入筆數
    """
    if df.empty:
        return 0

    from modules.database import get_connection
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO prices (stock_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (row['stock_id'], row['date'], row['open'], row['high'],
                  row['low'], row['close'], int(row['volume'])))
        conn.commit()
        return len(df)
    finally:
        conn.close()


PRICES_ADJ_SCHEMA = """
    CREATE TABLE IF NOT EXISTS prices_adj (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        open REAL, high REAL, low REAL, close REAL, volume INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock_id, date)
    )
"""

INSTITUTIONAL_SCHEMA = """
    CREATE TABLE IF NOT EXISTS institutional_flows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        investor_type TEXT NOT NULL,
        buy INTEGER, sell INTEGER, net INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock_id, date, investor_type)
    )
"""


def save_prices_adj(df: pd.DataFrame) -> int:
    """將還原權值價格寫入 prices_adj 表（表不存在時自動建立）

    Returns:
        寫入筆數
    """
    if df.empty:
        return 0

    from modules.database import get_connection
    conn = get_connection()
    try:
        conn.execute(PRICES_ADJ_SCHEMA)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO prices_adj (stock_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (row['stock_id'], row['date'], row['open'], row['high'],
                  row['low'], row['close'], int(row['volume'])))
        conn.commit()
        return len(df)
    finally:
        conn.close()


def save_institutional(df: pd.DataFrame) -> int:
    """將三大法人買賣超寫入 institutional_flows 表（表不存在時自動建立）

    Returns:
        寫入筆數
    """
    if df.empty:
        return 0

    from modules.database import get_connection
    conn = get_connection()
    try:
        conn.execute(INSTITUTIONAL_SCHEMA)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO institutional_flows
                    (stock_id, date, investor_type, buy, sell, net)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (row['stock_id'], row['date'], row['investor_type'],
                  int(row['buy']), int(row['sell']), int(row['net'])))
        conn.commit()
        return len(df)
    finally:
        conn.close()


NEWS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS stock_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date TEXT NOT NULL,
        title TEXT,
        link TEXT,
        source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock_id, link)
    )
"""


def save_news(df: pd.DataFrame) -> int:
    """將新聞寫入 stock_news 表（以 stock_id+link 去重，表不存在時自動建立）

    Returns:
        實際新增筆數（重複的略過）
    """
    if df.empty:
        return 0

    from modules.database import get_connection
    conn = get_connection()
    try:
        conn.execute(NEWS_SCHEMA)
        cursor = conn.cursor()
        added = 0
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT OR IGNORE INTO stock_news (stock_id, date, title, link, source)
                VALUES (?, ?, ?, ?, ?)
            """, (row['stock_id'], row['date'], row['title'],
                  row['link'], row['source']))
            added += cursor.rowcount
        conn.commit()
        return added
    finally:
        conn.close()


def update_news(fetcher: 'FinMindFetcher', stock_id: str,
                days_back: int = 3) -> int:
    """更新個股新聞（TaiwanStockNews 一次請求限單日，只補最近 N 天缺少的日子）

    Returns:
        新增筆數
    """
    from modules.database import get_connection

    # 找出最近 N 天中資料庫尚無新聞的日子
    missing = []
    conn = get_connection()
    try:
        for i in range(days_back):
            day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                count = conn.execute(
                    "SELECT COUNT(*) FROM stock_news WHERE stock_id = ? AND date LIKE ?",
                    (stock_id, day + '%')).fetchone()[0]
            except sqlite3.OperationalError:
                count = 0  # 資料表尚未建立
            if count == 0:
                missing.append(day)
    finally:
        conn.close()

    added = 0
    for day in missing:
        added += save_news(fetcher.fetch_news(stock_id, day))
    return added


def get_last_table_date(table: str, stock_id: str) -> Optional[str]:
    """取得指定資料表中該股票的最後日期（表不存在時回傳 None）"""
    if table not in ('prices', 'prices_adj', 'institutional_flows'):
        raise ValueError(f"不支援的資料表: {table}")

    from modules.database import get_connection
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT MAX(date) FROM {table} WHERE stock_id = ?", (stock_id,)
        ).fetchone()
        return row[0] if row and row[0] else None
    except sqlite3.OperationalError:
        return None  # 資料表尚未建立
    finally:
        conn.close()


def save_valuation(df: pd.DataFrame) -> int:
    """將估值 DataFrame 寫入 fundamentals 表

    只更新 pe_ratio / pb_ratio / dividend_yield；
    其餘欄位（營收、EPS 等）維持 NULL 或既有值。

    Returns:
        寫入筆數
    """
    if df.empty:
        return 0

    from modules.database import get_connection
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            # 已有同日資料時保留其他欄位，只覆蓋估值三欄
            cursor.execute("""
                INSERT INTO fundamentals (stock_id, date, pe_ratio, pb_ratio, dividend_yield)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(stock_id, date) DO UPDATE SET
                    pe_ratio = excluded.pe_ratio,
                    pb_ratio = excluded.pb_ratio,
                    dividend_yield = excluded.dividend_yield
            """, (row['stock_id'], row['date'], row['pe_ratio'],
                  row['pb_ratio'], row['dividend_yield']))
        conn.commit()
        return len(df)
    finally:
        conn.close()


def compute_start_date(stock_id: str, lookback_days: int = 180) -> str:
    """計算增量更新的起始日期

    有既有資料：最後日期 + 1 天；
    無既有資料：今天往回 lookback_days 天。
    """
    last_date = get_last_price_date(stock_id)
    if last_date:
        start = datetime.strptime(str(last_date)[:10], '%Y-%m-%d') + timedelta(days=1)
    else:
        start = datetime.now() - timedelta(days=lookback_days)
    return start.strftime('%Y-%m-%d')


def update_stock(fetcher: FinMindFetcher, stock_id: str,
                 lookback_days: int = 180) -> dict:
    """更新單一股票的價格與估值資料

    Returns:
        {'stock_id', 'prices_saved', 'valuation_saved', 'start_date'}
    """
    start_date = compute_start_date(stock_id, lookback_days)
    today = datetime.now().strftime('%Y-%m-%d')

    if start_date > today:
        return {'stock_id': stock_id, 'prices_saved': 0,
                'valuation_saved': 0, 'start_date': start_date}

    prices = fetcher.fetch_prices(stock_id, start_date)
    prices_saved = save_prices(prices)

    valuation = fetcher.fetch_valuation(stock_id, start_date)
    valuation_saved = save_valuation(valuation)

    # 以下為加值資料：任一項失敗（如方案等級不足）只警告，不中斷核心更新

    def _incremental_start(table: str) -> str:
        last = get_last_table_date(table, stock_id)
        if last:
            return (datetime.strptime(str(last)[:10], '%Y-%m-%d')
                    + timedelta(days=1)).strftime('%Y-%m-%d')
        return (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    # 還原權值股價（FinMind 目前需 Backer/Sponsor 方案）
    adj_saved = 0
    if 'TaiwanStockPriceAdj' not in fetcher.tier_blocked:
        adj_start = _incremental_start('prices_adj')
        if adj_start <= today:
            try:
                adj_saved = save_prices_adj(fetcher.fetch_prices_adj(stock_id, adj_start))
            except FinMindTierError:
                fetcher.tier_blocked.add('TaiwanStockPriceAdj')
                safe_print("  ⚠️  還原權值股價需 FinMind 贊助方案，本次略過"
                           "（回測將使用原始股價）")
            except Exception as e:
                safe_print(f"  ⚠️  還原權值股價抓取失敗，略過: {e}")

    # 三大法人買賣超
    inst_saved = 0
    if 'TaiwanStockInstitutionalInvestorsBuySell' not in fetcher.tier_blocked:
        inst_start = _incremental_start('institutional_flows')
        if inst_start <= today:
            try:
                inst_saved = save_institutional(
                    fetcher.fetch_institutional(stock_id, inst_start))
            except FinMindTierError:
                fetcher.tier_blocked.add('TaiwanStockInstitutionalInvestorsBuySell')
                safe_print("  ⚠️  三大法人買賣超需 FinMind 贊助方案，本次略過")
            except Exception as e:
                safe_print(f"  ⚠️  三大法人買賣超抓取失敗，略過: {e}")

    # 個股新聞（最近 3 天缺少的日子）
    news_saved = 0
    try:
        news_saved = update_news(fetcher, stock_id)
    except FinMindTierError:
        pass  # 理論上為免費 dataset，保險起見
    except Exception as e:
        safe_print(f"  ⚠️  新聞抓取失敗，略過: {e}")

    # 月營收與季財報（往回 400 天確保涵蓋最新一季），補進最新 fundamentals 列
    extras_saved = False
    try:
        lookback_start = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        extras = {}
        revenue = fetcher.fetch_month_revenue(stock_id, lookback_start)
        if revenue:
            extras['revenue'] = revenue['revenue']
        financials = fetcher.fetch_latest_financials(stock_id, lookback_start)
        if financials.get('eps') is not None:
            extras['eps'] = financials['eps']
        if financials.get('net_income') is not None:
            extras['net_income'] = financials['net_income']
        extras_saved = save_fundamental_extras(stock_id, extras)
    except Exception as e:
        safe_print(f"  ⚠️  月營收/財報抓取失敗，略過: {e}")

    return {'stock_id': stock_id, 'prices_saved': prices_saved,
            'valuation_saved': valuation_saved,
            'adj_saved': adj_saved, 'institutional_saved': inst_saved,
            'news_saved': news_saved,
            'extras_saved': extras_saved, 'start_date': start_date}


def save_fundamental_extras(stock_id: str, extras: dict) -> bool:
    """將月營收 / EPS / 淨利補進該股最新一筆 fundamentals 列

    估值（save_valuation）為日頻寫入，最新列可能缺營收與財報欄位；
    此函式把最新已知的月營收/季財報值補到最新日期列，
    讓 get_latest_fundamentals 一次取得完整資料。

    Args:
        stock_id: 股票代號
        extras: 欄位 -> 值，只接受 revenue / eps / net_income

    Returns:
        是否有實際更新
    """
    allowed = {'revenue', 'eps', 'net_income'}
    updates = {k: v for k, v in extras.items() if k in allowed and v is not None}
    if not updates:
        return False

    from modules.database import get_connection
    conn = get_connection()
    try:
        cursor = conn.cursor()
        set_sql = ', '.join(f"{k} = ?" for k in updates)
        cursor.execute(f"""
            UPDATE fundamentals SET {set_sql}
            WHERE stock_id = ?
              AND date = (SELECT MAX(date) FROM fundamentals WHERE stock_id = ?)
        """, list(updates.values()) + [stock_id, stock_id])

        if cursor.rowcount == 0:
            # 尚無任何 fundamentals 列（例如 PER 抓取失敗），建立一筆
            today = datetime.now().strftime('%Y-%m-%d')
            columns = ['stock_id', 'date'] + list(updates)
            placeholders = ', '.join('?' * len(columns))
            cursor.execute(
                f"INSERT OR REPLACE INTO fundamentals ({', '.join(columns)}) "
                f"VALUES ({placeholders})",
                [stock_id, today] + list(updates.values()))

        conn.commit()
        return True
    finally:
        conn.close()


def get_last_macro_date(indicator_name: str, region: str) -> Optional[str]:
    """取得某宏觀指標在資料庫中的最後日期，無資料時回傳 None"""
    from modules.database import get_connection
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT MAX(indicator_date) FROM macro_indicators
            WHERE indicator_name = ? AND region = ?
        """, (indicator_name, region)).fetchone()
        return row[0] if row and row[0] else None
    finally:
        conn.close()


def save_macro_indicators(df: pd.DataFrame) -> int:
    """將宏觀指標 DataFrame 寫入 macro_indicators 表

    以 (indicator_name, indicator_date, region) 去重，
    只覆蓋數值相關欄位，保留人工填寫的 impact_assessment / notes。

    Returns:
        寫入筆數
    """
    if df.empty:
        return 0

    from modules.database import get_connection
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO macro_indicators
                    (indicator_name, indicator_date, value, unit, region, source, frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(indicator_name, indicator_date, region) DO UPDATE SET
                    value = excluded.value,
                    unit = excluded.unit,
                    source = excluded.source,
                    frequency = excluded.frequency
            """, (row['indicator_name'], row['indicator_date'], row['value'],
                  row['unit'], row['region'], row['source'], row['frequency']))
        conn.commit()
        return len(df)
    finally:
        conn.close()


def update_macro_indicators(fetcher: FinMindFetcher, specs: list,
                            lookback_days: int = 365) -> dict:
    """更新所有已啟用的宏觀指標

    Args:
        fetcher: FinMind 抓取器
        specs: 宏觀指標 spec 列表（config.MACRO_FETCH_SPECS）
        lookback_days: 無既有資料時往回抓的天數

    Returns:
        {'saved': 總寫入筆數, 'failures': [失敗的指標名稱]}
    """
    total_saved = 0
    failures = []

    for spec in specs:
        if not spec.get('enabled', True):
            continue

        name = spec['indicator_name']
        last_date = get_last_macro_date(name, spec.get('region', ''))
        if last_date:
            start = (datetime.strptime(str(last_date)[:10], '%Y-%m-%d')
                     + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            start = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

        today = datetime.now().strftime('%Y-%m-%d')
        if start > today:
            continue

        try:
            df = fetcher.fetch_macro(spec, start)
            saved = save_macro_indicators(df)
            total_saved += saved
            if saved:
                safe_print(f"  ✅ {name}: {saved} 筆（自 {start}）")
            else:
                safe_print(f"  ℹ️  {name}: 無新資料")
        except Exception as e:
            safe_print(f"  ❌ {name}: {e}")
            failures.append(name)

    return {'saved': total_saved, 'failures': failures}
