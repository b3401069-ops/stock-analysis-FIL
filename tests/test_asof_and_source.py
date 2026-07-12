"""
測試 as-of date 過濾、來源欄位、CSV 結構驗證、calculate_total_score
"""
import pytest
import sqlite3
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from modules.config import Config


@pytest.fixture
def asof_db(tmp_path):
    """建立包含 as-of date 測試資料的數據庫"""
    db_path = tmp_path / "test_asof.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            market TEXT,
            industry TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    for table_sql in [
        """CREATE TABLE IF NOT EXISTS industry_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            industry_name TEXT, market_size REAL, growth_rate REAL,
            competition_level TEXT, competitive_landscape TEXT, regulatory_environment TEXT,
            technology_trends TEXT, supply_chain TEXT, score REAL, notes TEXT,
            source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
        """CREATE TABLE IF NOT EXISTS business_model (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            business_model_type TEXT, revenue_sources TEXT, competitive_advantages TEXT,
            moat_rating TEXT, scalability TEXT, diversification TEXT,
            customer_concentration TEXT, pricing_power TEXT, score REAL, notes TEXT,
            source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
        """CREATE TABLE IF NOT EXISTS management_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            ceo_name TEXT, major_shareholders TEXT, corporate_governance TEXT,
            compensation_structure TEXT, track_record TEXT, strategic_vision TEXT,
            execution_capability TEXT, score REAL, notes TEXT,
            source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
        """CREATE TABLE IF NOT EXISTS financial_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            report_period TEXT, revenue REAL, revenue_growth REAL,
            gross_margin REAL, operating_margin REAL, net_margin REAL,
            roe REAL, roa REAL, debt_to_equity REAL, current_ratio REAL,
            quick_ratio REAL, interest_coverage REAL, free_cash_flow REAL,
            cash_flow_growth REAL, earnings_quality TEXT, accounting_risks TEXT,
            score REAL, notes TEXT,
            source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
        """CREATE TABLE IF NOT EXISTS valuation_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            current_price REAL, pe_ratio REAL, pb_ratio REAL,
            ps_ratio REAL, ev_ebitda REAL, dividend_yield REAL,
            fair_value REAL, margin_of_safety REAL, growth_adjusted_pe REAL,
            relative_valuation TEXT, score REAL, notes TEXT,
            source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
        """CREATE TABLE IF NOT EXISTS investment_thesis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            thesis_type TEXT, observation_reasons TEXT, entry_strategy TEXT,
            exit_conditions TEXT, holding_period TEXT, position_size REAL,
            expected_return REAL, risk_reward_ratio TEXT, thesis_status TEXT,
            confidence_level TEXT, score REAL, notes TEXT,
            source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
        """CREATE TABLE IF NOT EXISTS risk_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            risk_level TEXT, market_risk TEXT, industry_risk TEXT,
            company_risk TEXT, financial_risk TEXT, operational_risk TEXT,
            regulatory_risk TEXT, geopolitical_risk TEXT, risk_score REAL,
            risk_mitigation TEXT, score REAL, notes TEXT,
            source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
        """CREATE TABLE IF NOT EXISTS research_5plus2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
            industry_score REAL, business_model_score REAL,
            management_score REAL, financial_score REAL,
            valuation_score REAL, investment_thesis_score REAL,
            risk_score REAL, total_score REAL, overall_rating TEXT,
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date))""",
    ]:
        cursor.execute(table_sql)

    # 插入測試股票
    cursor.execute("INSERT INTO stocks (stock_id, name, market, industry) VALUES ('2330', '台積電', 'TWSE', '半導體')")

    # 插入 2024-03-01 的資料（較早）
    tables_and_scores = [
        ('industry_analysis', 75), ('business_model', 80), ('management_analysis', 85),
        ('financial_analysis', 90), ('valuation_analysis', 70), ('investment_thesis', 78),
        ('risk_analysis', 65),
    ]
    for table, score in tables_and_scores:
        cursor.execute(f"""
            INSERT INTO {table} (stock_id, analysis_date, score, source, data_as_of)
            VALUES ('2330', '2024-03-01', ?, '研報', '2024-03-01')
        """, (score,))

    # 插入 2024-06-01 的資料（較晚），故意放更高分
    for table, score in tables_and_scores:
        cursor.execute(f"""
            INSERT INTO {table} (stock_id, analysis_date, score, source, data_as_of)
            VALUES ('2330', '2024-06-01', ?, '研報', '2024-06-01')
        """, (score + 5,))

    # 未來日期的資料（as-of 不應取到）
    for table, score in tables_and_scores:
        cursor.execute(f"""
            INSERT INTO {table} (stock_id, analysis_date, score, source, data_as_of)
            VALUES ('2330', '2025-12-01', ?, '研報', '2025-12-01')
        """, (score + 20,))

    conn.commit()
    conn.close()
    return str(db_path)


class TestAsOfDateFiltering:
    """測試七個 5+2 模組的 as-of date 過濾"""

    def _get_score(self, module_name, class_name, method_name, db_path, stock_id, as_of_date):
        with patch('modules.base_manager.get_config') as mock_config:
            cfg = type('Config', (), {'DATABASE_PATH': db_path})()
            mock_config.return_value = cfg
            mod = __import__(f'modules.{module_name}', fromlist=[class_name])
            cls = getattr(mod, class_name)
            # Patch the module-level get_config too
            with patch.object(mod, 'get_config', return_value=cfg):
                mgr = cls()
                fn = getattr(mgr, method_name)
                return fn(stock_id, as_of_date)

    def test_industry_asof_ignores_future(self, asof_db):
        result = self._get_score('industry_analysis', 'IndustryAnalysisManager',
                                 'get_industry_score', asof_db, '2330', '2024-04-15')
        assert result['score'] == 75, f"as-of 2024-04-15 應取 2024-03-01 的 75，實際 {result['score']}"

    def test_business_model_asof_ignores_future(self, asof_db):
        result = self._get_score('business_model', 'BusinessModelManager',
                                 'get_business_model_score', asof_db, '2330', '2024-04-15')
        assert result['score'] == 80, f"as-of 2024-04-15 應取 2024-03-01 的 80，實際 {result['score']}"

    def test_management_asof_ignores_future(self, asof_db):
        result = self._get_score('management_analysis', 'ManagementAnalysisManager',
                                 'get_management_score', asof_db, '2330', '2024-04-15')
        assert result['score'] == 85, f"as-of 2024-04-15 應取 2024-03-01 的 85，實際 {result['score']}"

    def test_financial_asof_ignores_future(self, asof_db):
        result = self._get_score('financial_analysis', 'FinancialAnalysisManager',
                                 'get_financial_score', asof_db, '2330', '2024-04-15')
        assert result['score'] == 90, f"as-of 2024-04-15 應取 2024-03-01 的 90，實際 {result['score']}"

    def test_valuation_asof_ignores_future(self, asof_db):
        result = self._get_score('valuation', 'ValuationAnalysisManager',
                                 'get_valuation_score', asof_db, '2330', '2024-04-15')
        assert result['score'] == 70, f"as-of 2024-04-15 應取 2024-03-01 的 70，實際 {result['score']}"

    def test_thesis_asof_ignores_future(self, asof_db):
        result = self._get_score('investment_thesis', 'InvestmentThesisManager',
                                 'get_thesis_score', asof_db, '2330', '2024-04-15')
        assert result['score'] == 78, f"as-of 2024-04-15 應取 2024-03-01 的 78，實際 {result['score']}"

    def test_risk_asof_ignores_future(self, asof_db):
        result = self._get_score('risk_analysis', 'RiskAnalysisManager',
                                 'get_risk_score', asof_db, '2330', '2024-04-15')
        assert result['score'] == 65, f"as-of 2024-04-15 應取 2024-03-01 的 65，實際 {result['score']}"

    def test_asof_picks_later_record_when_in_range(self, asof_db):
        result = self._get_score('industry_analysis', 'IndustryAnalysisManager',
                                 'get_industry_score', asof_db, '2330', '2024-07-01')
        assert result['score'] == 80, f"as-of 2024-07-01 應取 2024-06-01 的 80，實際 {result['score']}"


class TestSourceFieldsRoundTrip:
    """測試 source/data_as_of 在 manager add/query 中往返正確"""

    def test_financial_analysis_source_roundtrip(self, tmp_path):
        db_path = str(tmp_path / "test_source.db")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE TABLE stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                market TEXT, industry TEXT, enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE financial_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL, analysis_date DATE NOT NULL,
                report_period TEXT, revenue REAL, revenue_growth REAL,
                gross_margin REAL, operating_margin REAL, net_margin REAL,
                roe REAL, roa REAL, debt_to_equity REAL, current_ratio REAL,
                quick_ratio REAL, interest_coverage REAL, free_cash_flow REAL,
                cash_flow_growth REAL, earnings_quality TEXT, accounting_risks TEXT,
                score REAL, notes TEXT,
                source TEXT DEFAULT '研報', source_url TEXT, data_as_of DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
                UNIQUE(stock_id, analysis_date)
            )
        """)
        conn.execute("INSERT INTO stocks (stock_id, name) VALUES ('2330', '台積電')")
        conn.commit()
        conn.close()

        from modules.financial_analysis import FinancialAnalysisManager, get_config as fa_get_config
        with patch('modules.base_manager.get_config') as mock_config:
            cfg = type('Config', (), {'DATABASE_PATH': db_path})()
            mock_config.return_value = cfg
            mgr = FinancialAnalysisManager()
            result = mgr.add_financial_analysis({
                'stock_id': '2330', 'analysis_date': '2024-06-15',
                'report_period': '2024Q2', 'revenue': 1000,
                'score': 85, 'source': '年報', 'source_url': 'https://example.com',
                'data_as_of': '2024-06-30'
            })
            assert result is True

            analysis = mgr.get_financial_analysis('2330', '2024-06-15')
            assert analysis is not None
            assert analysis['source'] == '年報'
            assert analysis['source_url'] == 'https://example.com'
            assert analysis['data_as_of'] == '2024-06-30'

    def test_earnings_call_source_roundtrip(self, tmp_path):
        db_path = str(tmp_path / "test_source_ec.db")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE TABLE stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                market TEXT, industry TEXT, enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE earnings_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL, call_date DATE NOT NULL,
                quarter TEXT, fiscal_year TEXT, call_time TEXT,
                participants TEXT, management_guidance TEXT, key_highlights TEXT,
                revenue_guidance TEXT, earnings_guidance TEXT, margin_guidance TEXT,
                capex_guidance TEXT, analyst_questions TEXT, management_responses TEXT,
                sentiment TEXT, surprises TEXT, risk_factors TEXT,
                outlook_summary TEXT, transcript_summary TEXT, notes TEXT,
                source TEXT DEFAULT '公開資訊', source_url TEXT, data_as_of DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
                UNIQUE(stock_id, call_date, quarter)
            )
        """)
        conn.execute("INSERT INTO stocks (stock_id, name) VALUES ('2330', '台積電')")
        conn.commit()
        conn.close()

        from modules.earnings_call import EarningsCallManager
        with patch('modules.base_manager.get_config') as mock_config:
            cfg = type('Config', (), {'DATABASE_PATH': db_path})()
            mock_config.return_value = cfg
            mgr = EarningsCallManager()
            result = mgr.add_earnings_call({
                'stock_id': '2330', 'call_date': '2024-04-18',
                'quarter': 'Q1 2024', 'fiscal_year': '2024',
                'source': '官網', 'source_url': 'https://investor.tsmc.com',
                'data_as_of': '2024-04-18'
            })
            assert result is True

            call = mgr.get_latest_earnings_call('2330')
            assert call is not None
            assert call['source'] == '官網'
            assert call['source_url'] == 'https://investor.tsmc.com'
            assert call['data_as_of'] == '2024-04-18'

    def test_analyst_views_source_roundtrip(self, tmp_path):
        db_path = str(tmp_path / "test_source_av.db")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE TABLE stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                market TEXT, industry TEXT, enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE analyst_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL, report_date DATE NOT NULL,
                analyst_firm TEXT, analyst_name TEXT, rating TEXT,
                target_price REAL, previous_target REAL, recommendation TEXT,
                key_findings TEXT, strengths TEXT, weaknesses TEXT,
                opportunities TEXT, threats TEXT, financial_estimates TEXT,
                valuation_methodology TEXT, risk_factors TEXT, catalysts TEXT,
                report_summary TEXT, confidence_level TEXT, notes TEXT,
                source TEXT DEFAULT '投行研報', source_url TEXT,
                source_type TEXT DEFAULT '摘要',
                is_paid_report INTEGER DEFAULT 0, summary_only INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, data_as_of DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
                UNIQUE(stock_id, report_date, analyst_firm)
            )
        """)
        conn.execute("INSERT INTO stocks (stock_id, name) VALUES ('2330', '台積電')")
        conn.commit()
        conn.close()

        from modules.analyst_views import AnalystViewsManager
        with patch('modules.base_manager.get_config') as mock_config:
            cfg = type('Config', (), {'DATABASE_PATH': db_path})()
            mock_config.return_value = cfg
            mgr = AnalystViewsManager()
            result = mgr.add_analyst_view({
                'stock_id': '2330', 'report_date': '2024-03-10',
                'analyst_firm': '瑞銀', 'analyst_name': '張三豐',
                'rating': '買進', 'target_price': 800,
                'recommendation': '投資邏輯成立',
                'source': '付費報告', 'source_url': 'https://ubs.com/report',
                'source_type': '全文', 'is_paid_report': True,
                'summary_only': False, 'data_as_of': '2024-03-10'
            })
            assert result is True

            view = mgr.get_latest_analyst_view('2330')
            assert view is not None
            assert view['source'] == '付費報告'
            assert view['source_url'] == 'https://ubs.com/report'
            assert view['source_type'] == '全文'
            assert view['is_paid_report'] == 1
            assert view['summary_only'] == 0
            assert view['data_as_of'] == '2024-03-10'


class TestCalculateTotalScore:
    """測試 calculate_total_score() 的直接呼叫"""

    def _patch_all_manager_configs(self, cfg):
        """Patch config on all module-level singleton managers"""
        import modules.industry_analysis
        import modules.business_model
        import modules.management_analysis
        import modules.financial_analysis
        import modules.valuation
        import modules.investment_thesis
        import modules.risk_analysis

        patches = []
        for mod in [modules.industry_analysis, modules.business_model,
                    modules.management_analysis, modules.financial_analysis,
                    modules.valuation, modules.investment_thesis,
                    modules.risk_analysis]:
            patches.append(patch.object(mod.get_config(), 'DATABASE_PATH', cfg.DATABASE_PATH))
        return patches

    def test_calculate_total_score_basic(self, asof_db):
        from modules.research_5plus2 import Research5Plus2Manager
        cfg = type('Config', (), {
            'DATABASE_PATH': asof_db,
            'RESEARCH_5PLUS2_WEIGHTS': {
                'industry_analysis': 0.15,
                'business_model': 0.15,
                'management_analysis': 0.15,
                'financial_analysis': 0.15,
                'valuation': 0.15,
                'investment_thesis': 0.15,
                'risk_analysis': 0.10,
            },
            'RESEARCH_5PLUS2_THRESHOLDS': {
                'strong_buy': 85, 'buy': 75, 'hold': 60,
                'weak_hold': 45, 'sell': 30
            }
        })()
        # Patch config on singleton managers
        with patch('modules.industry_analysis.get_industry_analysis_manager') as mock_ind, \
             patch('modules.business_model.get_business_model_manager') as mock_biz, \
             patch('modules.management_analysis.get_management_analysis_manager') as mock_mgmt, \
             patch('modules.financial_analysis.get_financial_analysis_manager') as mock_fin, \
             patch('modules.valuation.get_valuation_analysis_manager') as mock_val, \
             patch('modules.investment_thesis.get_investment_thesis_manager') as mock_thesis, \
             patch('modules.risk_analysis.get_risk_analysis_manager') as mock_risk:
            # Create fresh managers with our config
            import modules.industry_analysis as iam
            import modules.business_model as bm
            import modules.management_analysis as ma
            import modules.financial_analysis as fa
            import modules.valuation as va
            import modules.investment_thesis as it
            import modules.risk_analysis as ra

            mock_ind.return_value = iam.IndustryAnalysisManager()
            mock_ind.return_value.config = cfg
            mock_biz.return_value = bm.BusinessModelManager()
            mock_biz.return_value.config = cfg
            mock_mgmt.return_value = ma.ManagementAnalysisManager()
            mock_mgmt.return_value.config = cfg
            mock_fin.return_value = fa.FinancialAnalysisManager()
            mock_fin.return_value.config = cfg
            mock_val.return_value = va.ValuationAnalysisManager()
            mock_val.return_value.config = cfg
            mock_thesis.return_value = it.InvestmentThesisManager()
            mock_thesis.return_value.config = cfg
            mock_risk.return_value = ra.RiskAnalysisManager()
            mock_risk.return_value.config = cfg

            mgr = Research5Plus2Manager()
            mgr.config = cfg
            result = mgr.calculate_total_score('2330', '2024-04-15')
            assert 'total_score' in result
            assert result['total_score'] is not None
            # 75*0.15 + 80*0.15 + 85*0.15 + 90*0.15 + 70*0.15 + 78*0.15 + 65*0.10
            expected = 75*0.15 + 80*0.15 + 85*0.15 + 90*0.15 + 70*0.15 + 78*0.15 + 65*0.10
            assert abs(result['total_score'] - expected) < 0.01

    def test_calculate_total_score_no_future_data(self, asof_db):
        from modules.research_5plus2 import Research5Plus2Manager
        cfg = type('Config', (), {
            'DATABASE_PATH': asof_db,
            'RESEARCH_5PLUS2_WEIGHTS': {
                'industry_analysis': 0.15,
                'business_model': 0.15,
                'management_analysis': 0.15,
                'financial_analysis': 0.15,
                'valuation': 0.15,
                'investment_thesis': 0.15,
                'risk_analysis': 0.10,
            },
            'RESEARCH_5PLUS2_THRESHOLDS': {
                'strong_buy': 85, 'buy': 75, 'hold': 60,
                'weak_hold': 45, 'sell': 30
            }
        })()
        with patch('modules.industry_analysis.get_industry_analysis_manager') as mock_ind, \
             patch('modules.business_model.get_business_model_manager') as mock_biz, \
             patch('modules.management_analysis.get_management_analysis_manager') as mock_mgmt, \
             patch('modules.financial_analysis.get_financial_analysis_manager') as mock_fin, \
             patch('modules.valuation.get_valuation_analysis_manager') as mock_val, \
             patch('modules.investment_thesis.get_investment_thesis_manager') as mock_thesis, \
             patch('modules.risk_analysis.get_risk_analysis_manager') as mock_risk:
            import modules.industry_analysis as iam
            import modules.business_model as bm
            import modules.management_analysis as ma
            import modules.financial_analysis as fa
            import modules.valuation as va
            import modules.investment_thesis as it
            import modules.risk_analysis as ra

            mock_ind.return_value = iam.IndustryAnalysisManager()
            mock_ind.return_value.config = cfg
            mock_biz.return_value = bm.BusinessModelManager()
            mock_biz.return_value.config = cfg
            mock_mgmt.return_value = ma.ManagementAnalysisManager()
            mock_mgmt.return_value.config = cfg
            mock_fin.return_value = fa.FinancialAnalysisManager()
            mock_fin.return_value.config = cfg
            mock_val.return_value = va.ValuationAnalysisManager()
            mock_val.return_value.config = cfg
            mock_thesis.return_value = it.InvestmentThesisManager()
            mock_thesis.return_value.config = cfg
            mock_risk.return_value = ra.RiskAnalysisManager()
            mock_risk.return_value.config = cfg

            mgr = Research5Plus2Manager()
            mgr.config = cfg
            result = mgr.calculate_total_score('2330', '2024-04-15')
            score = result['total_score']
            # 不應包含 2025-12-01 的高分（每項 +20）
            # 如果取到未來分數，total 會顯著高於 expected
            assert score < 90, f"as-of date 過濾應排除未來資料，total={score}"

    def test_calculate_total_score_no_analysis_date(self, asof_db):
        from modules.research_5plus2 import Research5Plus2Manager
        cfg = type('Config', (), {
            'DATABASE_PATH': asof_db,
            'RESEARCH_5PLUS2_WEIGHTS': {
                'industry_analysis': 0.15,
                'business_model': 0.15,
                'management_analysis': 0.15,
                'financial_analysis': 0.15,
                'valuation': 0.15,
                'investment_thesis': 0.15,
                'risk_analysis': 0.10,
            },
            'RESEARCH_5PLUS2_THRESHOLDS': {
                'strong_buy': 85, 'buy': 75, 'hold': 60,
                'weak_hold': 45, 'sell': 30
            }
        })()
        with patch('modules.industry_analysis.get_industry_analysis_manager') as mock_ind, \
             patch('modules.business_model.get_business_model_manager') as mock_biz, \
             patch('modules.management_analysis.get_management_analysis_manager') as mock_mgmt, \
             patch('modules.financial_analysis.get_financial_analysis_manager') as mock_fin, \
             patch('modules.valuation.get_valuation_analysis_manager') as mock_val, \
             patch('modules.investment_thesis.get_investment_thesis_manager') as mock_thesis, \
             patch('modules.risk_analysis.get_risk_analysis_manager') as mock_risk:
            import modules.industry_analysis as iam
            import modules.business_model as bm
            import modules.management_analysis as ma
            import modules.financial_analysis as fa
            import modules.valuation as va
            import modules.investment_thesis as it
            import modules.risk_analysis as ra

            mock_ind.return_value = iam.IndustryAnalysisManager()
            mock_ind.return_value.config = cfg
            mock_biz.return_value = bm.BusinessModelManager()
            mock_biz.return_value.config = cfg
            mock_mgmt.return_value = ma.ManagementAnalysisManager()
            mock_mgmt.return_value.config = cfg
            mock_fin.return_value = fa.FinancialAnalysisManager()
            mock_fin.return_value.config = cfg
            mock_val.return_value = va.ValuationAnalysisManager()
            mock_val.return_value.config = cfg
            mock_thesis.return_value = it.InvestmentThesisManager()
            mock_thesis.return_value.config = cfg
            mock_risk.return_value = ra.RiskAnalysisManager()
            mock_risk.return_value.config = cfg

            mgr = Research5Plus2Manager()
            mgr.config = cfg
            # 不帶 analysis_date 應使用當前日期，不會 crash
            result = mgr.calculate_total_score('2330')
            assert 'total_score' in result


class TestCSVStructureValidation:
    """測試所有 data/sample_*.csv 不得有欄位錯位（None 欄位）"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.data_dir = Path(__file__).parent.parent / "data"

    def _validate_csv(self, csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            errors = []
            for i, row in enumerate(reader, 1):
                for col in header:
                    if row.get(col) is None:
                        errors.append(f"Row {i}: column '{col}' is None (likely CSV quoting issue)")
                if len(row) != len(header):
                    errors.append(f"Row {i}: expected {len(header)} cols, got {len(row)}")
            return errors

    def test_sample_stocks_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_stocks.csv")
        assert not errors, f"sample_stocks.csv: {errors}"

    def test_sample_prices_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_prices.csv")
        assert not errors, f"sample_prices.csv: {errors}"

    def test_sample_fundamentals_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_fundamentals.csv")
        assert not errors, f"sample_fundamentals.csv: {errors}"

    def test_sample_earnings_calls_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_earnings_calls.csv")
        assert not errors, f"sample_earnings_calls.csv: {errors}"

    def test_sample_analyst_views_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_analyst_views.csv")
        assert not errors, f"sample_analyst_views.csv: {errors}"

    def test_sample_research_5plus2_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_research_5plus2.csv")
        assert not errors, f"sample_research_5plus2.csv: {errors}"

    def test_sample_macro_indicators_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_macro_indicators.csv")
        assert not errors, f"sample_macro_indicators.csv: {errors}"

    def test_sample_industry_analysis_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_industry_analysis.csv")
        assert not errors, f"sample_industry_analysis.csv: {errors}"

    def test_sample_business_model_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_business_model.csv")
        assert not errors, f"sample_business_model.csv: {errors}"

    def test_sample_management_analysis_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_management_analysis.csv")
        assert not errors, f"sample_management_analysis.csv: {errors}"

    def test_sample_financial_analysis_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_financial_analysis.csv")
        assert not errors, f"sample_financial_analysis.csv: {errors}"

    def test_sample_valuation_analysis_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_valuation_analysis.csv")
        assert not errors, f"sample_valuation_analysis.csv: {errors}"

    def test_sample_investment_thesis_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_investment_thesis.csv")
        assert not errors, f"sample_investment_thesis.csv: {errors}"

    def test_sample_risk_analysis_csv(self):
        errors = self._validate_csv(self.data_dir / "sample_risk_analysis.csv")
        assert not errors, f"sample_risk_analysis.csv: {errors}"
