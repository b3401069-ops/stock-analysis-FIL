"""
資料源模組（FinMind）測試
所有測試皆 mock API 與資料庫，不需要網路與 token
"""

import sqlite3
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from modules.data_fetcher import (
    FinMindFetcher, save_prices, save_valuation,
    get_last_price_date, compute_start_date, update_stock,
    save_fundamental_extras, save_macro_indicators,
    get_last_macro_date, update_macro_indicators
)


# ---------- 測試用資料 ----------

FINMIND_PRICE_PAYLOAD = {
    'msg': 'success',
    'status': 200,
    'data': [
        {'date': '2025-07-01', 'stock_id': '2330', 'Trading_Volume': 30000000,
         'Trading_money': 1, 'open': 1000.0, 'max': 1020.0, 'min': 995.0,
         'close': 1015.0, 'spread': 5.0, 'Trading_turnover': 1},
        {'date': '2025-07-02', 'stock_id': '2330', 'Trading_Volume': 28000000,
         'Trading_money': 1, 'open': 1015.0, 'max': 1030.0, 'min': 1010.0,
         'close': 1025.0, 'spread': 10.0, 'Trading_turnover': 1},
        # 停牌日：open/close 為 0，應被剔除
        {'date': '2025-07-03', 'stock_id': '2330', 'Trading_Volume': 0,
         'Trading_money': 0, 'open': 0.0, 'max': 0.0, 'min': 0.0,
         'close': 0.0, 'spread': 0.0, 'Trading_turnover': 0},
    ]
}

FINMIND_PER_PAYLOAD = {
    'msg': 'success',
    'status': 200,
    'data': [
        {'date': '2025-07-01', 'stock_id': '2330',
         'dividend_yield': 1.8, 'PER': 22.5, 'PBR': 8.2},
    ]
}

FINMIND_REVENUE_PAYLOAD = {
    'msg': 'success', 'status': 200,
    'data': [
        {'date': '2025-05-10', 'stock_id': '2330', 'country': 'Taiwan',
         'revenue': 250000000000, 'revenue_month': 4, 'revenue_year': 2025},
        {'date': '2025-06-10', 'stock_id': '2330', 'country': 'Taiwan',
         'revenue': 260000000000, 'revenue_month': 5, 'revenue_year': 2025},
    ]
}

FINMIND_STATEMENTS_PAYLOAD = {
    'msg': 'success', 'status': 200,
    'data': [
        {'date': '2025-03-31', 'stock_id': '2330', 'type': 'EPS',
         'value': 13.9, 'origin_name': '基本每股盈餘'},
        {'date': '2025-03-31', 'stock_id': '2330', 'type': 'IncomeAfterTaxes',
         'value': 360000000000.0, 'origin_name': '本期淨利'},
        {'date': '2024-12-31', 'stock_id': '2330', 'type': 'EPS',
         'value': 14.2, 'origin_name': '基本每股盈餘'},
    ]
}

FINMIND_INTEREST_PAYLOAD = {
    'msg': 'success', 'status': 200,
    'data': [
        {'country': 'FED', 'date': '2025-06-18',
         'full_country_name': 'United States', 'interest_rate': 4.5},
        # 負利率不可被過濾
        {'country': 'FED', 'date': '2025-06-19',
         'full_country_name': 'United States', 'interest_rate': -0.1},
    ]
}

INTEREST_SPEC = {'dataset': 'InterestRate', 'data_id': 'FED', 'indicator_name': 'FED 利率',
                 'value_column': 'interest_rate', 'unit': '%', 'region': 'US',
                 'frequency': '不定期'}

FINMIND_INSTITUTIONAL_PAYLOAD = {
    'msg': 'success', 'status': 200,
    'data': [
        {'date': '2025-07-01', 'stock_id': '2330',
         'name': 'Foreign_Investor', 'buy': 5000000, 'sell': 3000000},
        {'date': '2025-07-01', 'stock_id': '2330',
         'name': 'Investment_Trust', 'buy': 800000, 'sell': 200000},
        {'date': '2025-07-02', 'stock_id': '2330',
         'name': 'Foreign_Investor', 'buy': 2000000, 'sell': 4000000},
    ]
}


def _mock_response(payload, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


@pytest.fixture
def temp_db(tmp_path):
    """建立含 prices / fundamentals 表的暫存資料庫，並 patch get_connection"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE stocks (stock_id TEXT PRIMARY KEY, name TEXT,
                             market TEXT, industry TEXT, enabled INTEGER);
        CREATE TABLE prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, date DATE NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            UNIQUE(stock_id, date));
        CREATE TABLE fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, date DATE NOT NULL,
            pe_ratio REAL, pb_ratio REAL, dividend_yield REAL,
            market_cap REAL, revenue REAL, net_income REAL, eps REAL, roe REAL,
            UNIQUE(stock_id, date));
        CREATE TABLE macro_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_name TEXT NOT NULL, indicator_date DATE NOT NULL,
            value REAL, unit TEXT, region TEXT, source TEXT, frequency TEXT,
            previous_value REAL, change REAL, trend TEXT,
            impact_assessment TEXT, notes TEXT,
            UNIQUE(indicator_name, indicator_date, region));
    """)
    conn.commit()
    conn.close()

    def _connect():
        c = sqlite3.connect(db_path)
        c.execute("PRAGMA foreign_keys = ON")
        return c

    with patch('modules.database.get_connection', side_effect=_connect):
        yield db_path


# ---------- FinMindFetcher ----------

class TestFinMindFetcher:

    def test_fetch_prices_maps_columns(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(FINMIND_PRICE_PAYLOAD)) as mock_get:
            df = fetcher.fetch_prices('2330', '2025-07-01')

        assert list(df.columns) == ['date', 'stock_id', 'open', 'high', 'low', 'close', 'volume']
        assert len(df) == 2  # 停牌日被剔除
        assert df.iloc[0]['high'] == 1020.0
        assert df.iloc[0]['volume'] == 30000000

        # 驗證 API 參數：token 以 Bearer header 傳遞，不在 query 參數中
        params = mock_get.call_args.kwargs['params']
        headers = mock_get.call_args.kwargs['headers']
        assert params['dataset'] == 'TaiwanStockPrice'
        assert params['data_id'] == '2330'
        assert 'token' not in params
        assert headers['Authorization'] == 'Bearer test-token'

    def test_fetch_valuation_maps_columns(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(FINMIND_PER_PAYLOAD)):
            df = fetcher.fetch_valuation('2330', '2025-07-01')

        assert list(df.columns) == ['date', 'stock_id', 'pe_ratio', 'pb_ratio', 'dividend_yield']
        assert df.iloc[0]['pe_ratio'] == 22.5
        assert df.iloc[0]['pb_ratio'] == 8.2

    def test_fetch_prices_empty_data(self):
        fetcher = FinMindFetcher(token='test-token')
        payload = {'msg': 'success', 'status': 200, 'data': []}
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(payload)):
            df = fetcher.fetch_prices('2330', '2025-07-01')
        assert df.empty

    def test_api_error_status_raises(self):
        fetcher = FinMindFetcher(token='bad-token')
        payload = {'msg': 'token error', 'status': 400, 'data': []}
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(payload)):
            with pytest.raises(RuntimeError, match='FinMind API 錯誤'):
                fetcher.fetch_prices('2330', '2025-07-01')

    def test_quota_exceeded_raises_friendly_error(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response({}, status_code=402)):
            with pytest.raises(RuntimeError, match='額度已用盡'):
                fetcher.fetch_prices('2330', '2025-07-01')

    def test_connection_error_raises(self):
        import requests as req
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   side_effect=req.ConnectionError('boom')):
            with pytest.raises(RuntimeError, match='連線失敗'):
                fetcher.fetch_prices('2330', '2025-07-01')

    def test_anonymous_without_token(self):
        with patch('modules.data_fetcher.get_config') as mock_config:
            mock_config.return_value = MagicMock(FINMIND_TOKEN=None)
            fetcher = FinMindFetcher()
        assert fetcher.token is None


# ---------- 資料庫寫入 ----------

class TestSaveToDb:

    def test_save_prices_and_upsert(self, temp_db):
        df = pd.DataFrame([
            {'stock_id': '2330', 'date': '2025-07-01', 'open': 1000.0,
             'high': 1020.0, 'low': 995.0, 'close': 1015.0, 'volume': 30000000},
        ])
        assert save_prices(df) == 1

        # 同日再寫一次（更新後的收盤價），應覆蓋不重複
        df2 = df.copy()
        df2.loc[0, 'close'] = 1018.0
        assert save_prices(df2) == 1

        conn = sqlite3.connect(temp_db)
        rows = conn.execute("SELECT close FROM prices WHERE stock_id='2330'").fetchall()
        conn.close()
        assert rows == [(1018.0,)]

    def test_save_valuation_preserves_other_columns(self, temp_db):
        conn = sqlite3.connect(temp_db)
        conn.execute("""INSERT INTO fundamentals (stock_id, date, eps, roe)
                        VALUES ('2330', '2025-07-01', 13.5, 28.5)""")
        conn.commit()
        conn.close()

        df = pd.DataFrame([
            {'stock_id': '2330', 'date': '2025-07-01',
             'pe_ratio': 22.5, 'pb_ratio': 8.2, 'dividend_yield': 1.8},
        ])
        assert save_valuation(df) == 1

        conn = sqlite3.connect(temp_db)
        row = conn.execute("""SELECT pe_ratio, eps, roe FROM fundamentals
                              WHERE stock_id='2330' AND date='2025-07-01'""").fetchone()
        conn.close()
        # 估值已更新，且既有的 eps/roe 未被清成 NULL
        assert row == (22.5, 13.5, 28.5)

    def test_save_empty_returns_zero(self, temp_db):
        assert save_prices(pd.DataFrame()) == 0
        assert save_valuation(pd.DataFrame()) == 0


# ---------- 增量更新 ----------

class TestIncrementalUpdate:

    def test_get_last_price_date(self, temp_db):
        assert get_last_price_date('2330') is None

        conn = sqlite3.connect(temp_db)
        conn.execute("""INSERT INTO prices (stock_id, date, close)
                        VALUES ('2330', '2025-07-02', 1025.0)""")
        conn.commit()
        conn.close()
        assert get_last_price_date('2330') == '2025-07-02'

    def test_compute_start_date_incremental(self, temp_db):
        conn = sqlite3.connect(temp_db)
        conn.execute("""INSERT INTO prices (stock_id, date, close)
                        VALUES ('2330', '2025-07-02', 1025.0)""")
        conn.commit()
        conn.close()
        # 有資料：最後日期 + 1 天
        assert compute_start_date('2330') == '2025-07-03'

    def test_compute_start_date_no_data_uses_lookback(self, temp_db):
        from datetime import datetime, timedelta
        expected = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        assert compute_start_date('2330', lookback_days=90) == expected

    def test_update_stock_end_to_end(self, temp_db):
        fetcher = FinMindFetcher(token='test-token')

        def fake_get(url, params=None, headers=None, timeout=None):
            dataset = params['dataset']
            if dataset in ('TaiwanStockPrice', 'TaiwanStockPriceAdj'):
                return _mock_response(FINMIND_PRICE_PAYLOAD)
            if dataset == 'TaiwanStockInstitutionalInvestorsBuySell':
                return _mock_response(FINMIND_INSTITUTIONAL_PAYLOAD)
            if dataset == 'TaiwanStockMonthRevenue':
                return _mock_response(FINMIND_REVENUE_PAYLOAD)
            if dataset == 'TaiwanStockFinancialStatements':
                return _mock_response(FINMIND_STATEMENTS_PAYLOAD)
            return _mock_response(FINMIND_PER_PAYLOAD)

        with patch('modules.data_fetcher.requests.get', side_effect=fake_get):
            result = update_stock(fetcher, '2330', lookback_days=90)

        assert result['prices_saved'] == 2
        assert result['valuation_saved'] == 1
        assert result['adj_saved'] == 2
        assert result['institutional_saved'] == 3
        assert result['extras_saved'] is True

        conn = sqlite3.connect(temp_db)
        price_count = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
        # 最新 fundamentals 列應同時有估值與月營收/財報
        row = conn.execute("""SELECT pe_ratio, revenue, eps, net_income
                              FROM fundamentals WHERE stock_id='2330'
                              ORDER BY date DESC LIMIT 1""").fetchone()
        conn.close()
        assert price_count == 2
        assert row == (22.5, 260000000000.0, 13.9, 360000000000.0)

    def test_update_stock_up_to_date_skips_fetch(self, temp_db):
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO prices (stock_id, date, close) VALUES ('2330', ?, 1000.0)",
                     (today,))
        conn.commit()
        conn.close()

        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get') as mock_get:
            result = update_stock(fetcher, '2330')

        mock_get.assert_not_called()
        assert result['prices_saved'] == 0


# ---------- 還原股價 / 三大法人 ----------

class TestAdjAndInstitutional:

    def test_fetch_institutional_maps_and_computes_net(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(FINMIND_INSTITUTIONAL_PAYLOAD)):
            df = fetcher.fetch_institutional('2330', '2025-07-01')

        assert len(df) == 3
        assert set(df['investor_type']) == {'外資', '投信'}
        foreign_d1 = df[(df['date'] == '2025-07-01') & (df['investor_type'] == '外資')]
        assert foreign_d1.iloc[0]['net'] == 2000000  # 買 500 萬 - 賣 300 萬

    def test_save_institutional_creates_table_and_upserts(self, temp_db):
        from modules.data_fetcher import save_institutional
        df = pd.DataFrame([
            {'stock_id': '2330', 'date': '2025-07-01', 'investor_type': '外資',
             'buy': 5000000, 'sell': 3000000, 'net': 2000000},
        ])
        assert save_institutional(df) == 1
        # 同鍵重寫應覆蓋
        df.loc[0, 'net'] = 2500000
        df.loc[0, 'buy'] = 5500000
        assert save_institutional(df) == 1

        conn = sqlite3.connect(temp_db)
        rows = conn.execute("SELECT net FROM institutional_flows").fetchall()
        conn.close()
        assert rows == [(2500000,)]

    def test_save_prices_adj_creates_table(self, temp_db):
        from modules.data_fetcher import save_prices_adj
        df = pd.DataFrame([
            {'stock_id': '2330', 'date': '2025-07-01', 'open': 1000.0,
             'high': 1020.0, 'low': 995.0, 'close': 1015.0, 'volume': 30000000},
        ])
        assert save_prices_adj(df) == 1
        conn = sqlite3.connect(temp_db)
        count = conn.execute("SELECT COUNT(*) FROM prices_adj").fetchone()[0]
        conn.close()
        assert count == 1

    def test_get_last_table_date_missing_table(self, temp_db):
        from modules.data_fetcher import get_last_table_date
        # 表尚未建立時回傳 None 而非丟例外
        assert get_last_table_date('prices_adj', '2330') is None
        assert get_last_table_date('institutional_flows', '2330') is None

    def test_get_last_table_date_rejects_unknown_table(self, temp_db):
        from modules.data_fetcher import get_last_table_date
        with pytest.raises(ValueError):
            get_last_table_date('stocks; DROP TABLE stocks', '2330')


    def test_update_stock_survives_tier_blocked_adj(self, temp_db):
        """還原股價方案等級不足時，核心更新（股價/估值）仍須成功"""
        from modules.data_fetcher import update_stock as us
        fetcher = FinMindFetcher(token='test-token')

        def fake_get(url, params=None, headers=None, timeout=None):
            dataset = params['dataset']
            if dataset == 'TaiwanStockPriceAdj':
                return _mock_response(
                    {'msg': 'Your level is free. Please update your user level.',
                     'status': 400}, status_code=400)
            if dataset == 'TaiwanStockPrice':
                return _mock_response(FINMIND_PRICE_PAYLOAD)
            if dataset == 'TaiwanStockInstitutionalInvestorsBuySell':
                return _mock_response(FINMIND_INSTITUTIONAL_PAYLOAD)
            if dataset == 'TaiwanStockMonthRevenue':
                return _mock_response(FINMIND_REVENUE_PAYLOAD)
            if dataset == 'TaiwanStockFinancialStatements':
                return _mock_response(FINMIND_STATEMENTS_PAYLOAD)
            return _mock_response(FINMIND_PER_PAYLOAD)

        with patch('modules.data_fetcher.requests.get', side_effect=fake_get) as mock_get:
            result = us(fetcher, '2330', lookback_days=90)

        # 核心資料照常寫入，僅還原股價略過
        assert result['prices_saved'] == 2
        assert result['valuation_saved'] == 1
        assert result['adj_saved'] == 0
        assert result['institutional_saved'] == 3
        assert 'TaiwanStockPriceAdj' in fetcher.tier_blocked

        # 第二檔股票不應再請求被封鎖的 dataset
        with patch('modules.data_fetcher.requests.get', side_effect=fake_get) as mock_get2:
            us(fetcher, '2317', lookback_days=90)
        datasets = [c.kwargs['params']['dataset'] for c in mock_get2.call_args_list]
        assert 'TaiwanStockPriceAdj' not in datasets


# ---------- 個股新聞 ----------

class TestStockNews:

    NEWS_PAYLOAD = {'msg': 'success', 'status': 200, 'data': [
        {'date': '2026-07-04 08:30:00', 'stock_id': '2330',
         'title': '台積電法說會前瞻', 'link': 'https://example.com/a1',
         'source': '測試新聞', 'description': ''},
        {'date': '2026-07-04 10:00:00', 'stock_id': '2330',
         'title': '外資調升目標價', 'link': 'https://example.com/a2',
         'source': '測試新聞', 'description': ''},
    ]}

    def test_fetch_news_maps_columns(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(self.NEWS_PAYLOAD)):
            df = fetcher.fetch_news('2330', '2026-07-04')
        assert list(df.columns) == ['stock_id', 'date', 'title', 'link', 'source']
        assert len(df) == 2

    def test_save_news_dedup_by_link(self, temp_db):
        from modules.data_fetcher import save_news
        df = pd.DataFrame(self.NEWS_PAYLOAD['data'])[
            ['stock_id', 'date', 'title', 'link', 'source']]
        assert save_news(df) == 2
        assert save_news(df) == 0  # 同 link 重複匯入不新增

    def test_update_news_only_fetches_missing_days(self, temp_db):
        from modules.data_fetcher import update_news, save_news
        from datetime import datetime
        fetcher = FinMindFetcher(token='test-token')

        # 先塞今天的新聞，update_news 就不該再抓今天
        today = datetime.now().strftime('%Y-%m-%d')
        save_news(pd.DataFrame([{'stock_id': '2330', 'date': f'{today} 09:00:00',
                                 'title': 't', 'link': 'https://example.com/x',
                                 'source': 's'}]))

        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(
                       {'msg': 'success', 'status': 200, 'data': []})) as mock_get:
            update_news(fetcher, '2330', days_back=3)

        fetched_days = [c.kwargs['params']['start_date']
                        for c in mock_get.call_args_list]
        assert today not in fetched_days
        assert len(fetched_days) == 2  # 只抓缺少的前兩天


# ---------- 籌碼面訊號 ----------

class TestChipSignals:

    def _inst_df(self, rows):
        return pd.DataFrame(rows, columns=['date', 'investor_type', 'net'])

    def test_foreign_consecutive_buy_signal(self):
        from modules.signals import detect_chip_signals
        inst = self._inst_df([
            ('2025-07-01', '外資', 1000000),
            ('2025-07-02', '外資', 2000000),
            ('2025-07-03', '外資', 1500000),
        ])
        signals = detect_chip_signals(inst)
        names = [s['signal_name'] for s in signals]
        assert '外資連3日買超' in names
        sig = next(s for s in signals if s['signal_name'] == '外資連3日買超')
        assert sig['severity'] == '偏多'
        assert sig['signal_type'] == '籌碼面'
        assert '4,500 張' in sig['description']

    def test_trust_consecutive_sell_signal(self):
        from modules.signals import detect_chip_signals
        inst = self._inst_df([
            ('2025-07-01', '投信', -500000),
            ('2025-07-02', '投信', -300000),
            ('2025-07-03', '投信', -200000),
        ])
        signals = detect_chip_signals(inst)
        assert any(s['signal_name'] == '投信連3日賣超' and s['severity'] == '偏空'
                   for s in signals)

    def test_synchronized_buy_signal(self):
        from modules.signals import detect_chip_signals
        inst = self._inst_df([
            ('2025-07-03', '外資', 1000000),
            ('2025-07-03', '投信', 500000),
        ])
        signals = detect_chip_signals(inst)
        assert any(s['signal_name'] == '外資投信同步買超' for s in signals)

    def test_no_signal_when_mixed(self):
        from modules.signals import detect_chip_signals
        inst = self._inst_df([
            ('2025-07-01', '外資', 1000000),
            ('2025-07-02', '外資', -2000000),
            ('2025-07-03', '外資', 1500000),
        ])
        # 買賣交錯：無連續訊號；最新日只有外資無投信：無同步訊號
        assert detect_chip_signals(inst) == []

    def test_insufficient_days_no_signal(self):
        from modules.signals import detect_chip_signals
        inst = self._inst_df([
            ('2025-07-02', '外資', 1000000),
            ('2025-07-03', '外資', 1500000),
        ])
        names = [s['signal_name'] for s in detect_chip_signals(inst)]
        assert '外資連3日買超' not in names

    def test_empty_input(self):
        from modules.signals import detect_chip_signals
        assert detect_chip_signals(pd.DataFrame()) == []


# ---------- 月營收 / 季財報 ----------

class TestFundamentalExtras:

    def test_fetch_month_revenue_takes_latest(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(FINMIND_REVENUE_PAYLOAD)):
            result = fetcher.fetch_month_revenue('2330', '2025-01-01')
        assert result['revenue'] == 260000000000.0
        assert result['revenue_month'] == 5

    def test_fetch_latest_financials_picks_latest_quarter(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(FINMIND_STATEMENTS_PAYLOAD)):
            result = fetcher.fetch_latest_financials('2330', '2024-01-01')
        # 應取 2025-03-31 那季，而非 2024-12-31
        assert result['date'] == '2025-03-31'
        assert result['eps'] == 13.9
        assert result['net_income'] == 360000000000.0

    def test_save_fundamental_extras_updates_latest_row(self, temp_db):
        conn = sqlite3.connect(temp_db)
        conn.executescript("""
            INSERT INTO fundamentals (stock_id, date, pe_ratio) VALUES ('2330', '2025-07-01', 22.0);
            INSERT INTO fundamentals (stock_id, date, pe_ratio) VALUES ('2330', '2025-07-02', 22.5);
        """)
        conn.commit()
        conn.close()

        assert save_fundamental_extras('2330', {'revenue': 1.0, 'eps': 2.0}) is True

        conn = sqlite3.connect(temp_db)
        rows = conn.execute("""SELECT date, revenue, eps, pe_ratio FROM fundamentals
                               WHERE stock_id='2330' ORDER BY date""").fetchall()
        conn.close()
        # 只更新最新列，且不動 pe_ratio
        assert rows[0] == ('2025-07-01', None, None, 22.0)
        assert rows[1] == ('2025-07-02', 1.0, 2.0, 22.5)

    def test_save_fundamental_extras_inserts_when_no_row(self, temp_db):
        assert save_fundamental_extras('2330', {'revenue': 5.0}) is True
        conn = sqlite3.connect(temp_db)
        count = conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0]
        conn.close()
        assert count == 1

    def test_save_fundamental_extras_rejects_unknown_columns(self, temp_db):
        # 不在白名單的欄位應被忽略
        assert save_fundamental_extras('2330', {'pe_ratio': 99.0, 'evil': 1}) is False


# ---------- 宏觀指標 ----------

class TestMacroIndicators:

    def test_fetch_macro_maps_and_keeps_negative_rates(self):
        fetcher = FinMindFetcher(token='test-token')
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(FINMIND_INTEREST_PAYLOAD)):
            df = fetcher.fetch_macro(INTEREST_SPEC, '2025-01-01')

        assert len(df) == 2  # 負利率保留
        assert df.iloc[0]['indicator_name'] == 'FED 利率'
        assert df.iloc[0]['value'] == 4.5
        assert df.iloc[1]['value'] == -0.1
        assert df.iloc[0]['source'] == 'FinMind'

    def test_fetch_macro_positive_only_filters(self):
        fetcher = FinMindFetcher(token='test-token')
        payload = {'msg': 'success', 'status': 200, 'data': [
            {'date': '2025-07-01', 'currency': 'USD', 'cash_buy': 32.0,
             'cash_sell': 32.5, 'spot_buy': 32.1, 'spot_sell': 32.3},
            {'date': '2025-07-02', 'currency': 'USD', 'cash_buy': -1.0,
             'cash_sell': -1.0, 'spot_buy': -1.0, 'spot_sell': -1.0},
        ]}
        spec = {'dataset': 'TaiwanExchangeRate', 'data_id': 'USD',
                'indicator_name': 'USD/TWD 匯率', 'value_column': 'spot_sell',
                'unit': 'TWD', 'region': 'TW', 'frequency': '每日',
                'positive_only': True}
        with patch('modules.data_fetcher.requests.get',
                   return_value=_mock_response(payload)):
            df = fetcher.fetch_macro(spec, '2025-07-01')
        assert len(df) == 1  # -1 缺值被剔除
        assert df.iloc[0]['value'] == 32.3

    def test_save_macro_upsert_preserves_notes(self, temp_db):
        conn = sqlite3.connect(temp_db)
        conn.execute("""INSERT INTO macro_indicators
                        (indicator_name, indicator_date, region, value, notes)
                        VALUES ('FED 利率', '2025-06-18', 'US', 4.25, '人工筆記')""")
        conn.commit()
        conn.close()

        df = pd.DataFrame([{
            'indicator_name': 'FED 利率', 'indicator_date': '2025-06-18',
            'value': 4.5, 'unit': '%', 'region': 'US',
            'source': 'FinMind', 'frequency': '不定期'}])
        assert save_macro_indicators(df) == 1

        conn = sqlite3.connect(temp_db)
        row = conn.execute("""SELECT value, notes FROM macro_indicators
                              WHERE indicator_name='FED 利率'""").fetchone()
        conn.close()
        assert row == (4.5, '人工筆記')  # 值更新、人工筆記保留

    def test_get_last_macro_date(self, temp_db):
        assert get_last_macro_date('FED 利率', 'US') is None
        conn = sqlite3.connect(temp_db)
        conn.execute("""INSERT INTO macro_indicators
                        (indicator_name, indicator_date, region, value)
                        VALUES ('FED 利率', '2025-06-18', 'US', 4.5)""")
        conn.commit()
        conn.close()
        assert get_last_macro_date('FED 利率', 'US') == '2025-06-18'

    def test_update_macro_indicators_failure_isolation(self, temp_db):
        """單一指標失敗（如 Sponsor tier 不足）不影響其他指標"""
        fetcher = FinMindFetcher(token='test-token')
        specs = [
            INTEREST_SPEC,
            {'dataset': 'TaiwanBusinessIndicator', 'data_id': None,
             'indicator_name': '景氣對策信號分數', 'value_column': 'monitoring',
             'unit': '分', 'region': 'TW', 'frequency': '每月'},
        ]

        def fake_get(url, params=None, headers=None, timeout=None):
            if params['dataset'] == 'InterestRate':
                return _mock_response(FINMIND_INTEREST_PAYLOAD)
            return _mock_response({'msg': 'tier not allowed', 'status': 400, 'data': []})

        with patch('modules.data_fetcher.requests.get', side_effect=fake_get):
            result = update_macro_indicators(fetcher, specs)

        assert result['saved'] == 2
        assert result['failures'] == ['景氣對策信號分數']

    def test_update_macro_indicators_skips_disabled(self, temp_db):
        fetcher = FinMindFetcher(token='test-token')
        specs = [dict(INTEREST_SPEC, enabled=False)]
        with patch('modules.data_fetcher.requests.get') as mock_get:
            result = update_macro_indicators(fetcher, specs)
        mock_get.assert_not_called()
        assert result['saved'] == 0
