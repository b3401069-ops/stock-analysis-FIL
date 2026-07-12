"""
5+2 投資研究框架模組測試
5+2 Research Framework Module Tests
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

# 導入被測模組
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.business_model import BusinessModelManager, get_business_model_manager
from modules.management_analysis import ManagementAnalysisManager, get_management_analysis_manager
from modules.financial_analysis import FinancialAnalysisManager, get_financial_analysis_manager
from modules.valuation import ValuationAnalysisManager, get_valuation_analysis_manager
from modules.investment_thesis import InvestmentThesisManager, get_investment_thesis_manager
from modules.risk_analysis import RiskAnalysisManager, get_risk_analysis_manager


@pytest.fixture
def temp_db(tmp_path):
    """建立臨時資料庫"""
    db_path = tmp_path / "test_5plus2.db"

    # 建立基礎資料表
    conn = sqlite3.connect(db_path)
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

    # 建立所有 5+2 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_model (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            business_model_type TEXT,
            revenue_streams TEXT,
            value_proposition TEXT,
            competitive_advantage TEXT,
            customer_segments TEXT,
            cost_structure TEXT,
            key_partners TEXT,
            scalability TEXT,
            sustainability TEXT,
            score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS management_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            ceo_name TEXT,
            ceo_background TEXT,
            management_team_size INTEGER,
            avg_tenure_years REAL,
            insider_ownership REAL,
            major_shareholders TEXT,
            corporate_governance TEXT,
            compensation_structure TEXT,
            track_record TEXT,
            strategic_vision TEXT,
            execution_capability TEXT,
            score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            report_period TEXT,
            revenue REAL,
            revenue_growth REAL,
            gross_margin REAL,
            operating_margin REAL,
            net_margin REAL,
            roe REAL,
            roa REAL,
            debt_to_equity REAL,
            current_ratio REAL,
            quick_ratio REAL,
            interest_coverage REAL,
            free_cash_flow REAL,
            cash_flow_growth REAL,
            earnings_quality TEXT,
            accounting_risks TEXT,
            score REAL,
            notes TEXT,
            source TEXT DEFAULT '研報',
            source_url TEXT,
            data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS valuation_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            current_price REAL,
            pe_ratio REAL,
            pb_ratio REAL,
            ps_ratio REAL,
            pcf_ratio REAL,
            ev_ebitda REAL,
            peg_ratio REAL,
            dividend_yield REAL,
            dcf_value REAL,
            relative_value REAL,
            historical_avg_pe REAL,
            industry_avg_pe REAL,
            margin_of_safety REAL,
            valuation_rating TEXT,
            score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investment_thesis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            thesis_summary TEXT,
            buy_reasons TEXT,
            catalysts TEXT,
            target_price REAL,
            investment_horizon TEXT,
            position_sizing TEXT,
            entry_strategy TEXT,
            exit_strategy TEXT,
            thesis_status TEXT,
            confidence_level TEXT,
            score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            business_risks TEXT,
            financial_risks TEXT,
            market_risks TEXT,
            regulatory_risks TEXT,
            competitive_risks TEXT,
            management_risks TEXT,
            liquidity_risks TEXT,
            currency_risks TEXT,
            geopolitical_risks TEXT,
            black_swan_risks TEXT,
            risk_mitigation TEXT,
            overall_risk_level TEXT,
            risk_rating TEXT,
            score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    # 插入測試股票
    cursor.execute("""
        INSERT INTO stocks (stock_id, name, market, industry)
        VALUES ('2330', '台積電', 'TWSE', '半導體')
    """)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def mock_config(temp_db, monkeypatch):
    """Mock 配置"""
    class MockConfig:
        DATABASE_PATH = str(temp_db)

    def mock_get_config():
        return MockConfig()

    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)
    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)
    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)
    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)
    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)
    monkeypatch.setattr('modules.base_manager.get_config', mock_get_config)


class TestBusinessModelManager:
    """商業模式管理器測試類別"""

    def test_add_business_model(self, mock_config):
        """測試新增商業模式分析"""
        manager = BusinessModelManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'business_model_type': '晶圓代工',
            'revenue_streams': '先進製程、成熟製程、封裝測試',
            'competitive_advantage': '技術領先、客戶黏著度高',
            'score': 90
        }

        result = manager.add_business_model(data)
        assert result is True

    def test_get_business_model(self, mock_config):
        """測試取得商業模式分析"""
        manager = BusinessModelManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'business_model_type': '晶圓代工',
            'score': 90
        }
        manager.add_business_model(data)

        analysis = manager.get_business_model('2330')
        assert analysis is not None
        assert analysis['business_model_type'] == '晶圓代工'


class TestManagementAnalysisManager:
    """經營管理層分析管理器測試類別"""

    def test_add_management_analysis(self, mock_config):
        """測試新增經營管理層分析"""
        manager = ManagementAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'ceo_name': '魏哲家',
            'ceo_background': '半導體產業資深人士',
            'management_team_size': 15,
            'insider_ownership': 0.5,
            'strategic_vision': '技術領先、客戶導向',
            'score': 92
        }

        result = manager.add_management_analysis(data)
        assert result is True

    def test_get_management_analysis(self, mock_config):
        """測試取得經營管理層分析"""
        manager = ManagementAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'ceo_name': '魏哲家',
            'score': 92
        }
        manager.add_management_analysis(data)

        analysis = manager.get_management_analysis('2330')
        assert analysis is not None
        assert analysis['ceo_name'] == '魏哲家'


class TestFinancialAnalysisManager:
    """財報分析管理器測試類別"""

    def test_add_financial_analysis(self, mock_config):
        """測試新增財報分析"""
        manager = FinancialAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'report_period': '2024Q1',
            'revenue': 180000000000,
            'revenue_growth': 16.5,
            'gross_margin': 53.0,
            'net_margin': 38.0,
            'roe': 25.0,
            'debt_to_equity': 0.3,
            'score': 88
        }

        result = manager.add_financial_analysis(data)
        assert result is True

    def test_get_financial_analysis(self, mock_config):
        """測試取得財報分析"""
        manager = FinancialAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'report_period': '2024Q1',
            'score': 88
        }
        manager.add_financial_analysis(data)

        analysis = manager.get_financial_analysis('2330')
        assert analysis is not None
        assert analysis['report_period'] == '2024Q1'


class TestValuationAnalysisManager:
    """公司估值分析管理器測試類別"""

    def test_add_valuation_analysis(self, mock_config):
        """測試新增估值分析"""
        manager = ValuationAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'current_price': 700,
            'pe_ratio': 22.5,
            'pb_ratio': 5.8,
            'dcf_value': 800,
            'margin_of_safety': 12.5,
            'valuation_rating': '估值合理',
            'score': 75
        }

        result = manager.add_valuation_analysis(data)
        assert result is True

    def test_get_valuation_analysis(self, mock_config):
        """測試取得估值分析"""
        manager = ValuationAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'current_price': 700,
            'score': 75
        }
        manager.add_valuation_analysis(data)

        analysis = manager.get_valuation_analysis('2330')
        assert analysis is not None
        assert analysis['current_price'] == 700


class TestInvestmentThesisManager:
    """投資邏輯管理器測試類別"""

    def test_add_investment_thesis(self, mock_config):
        """測試新增投資邏輯"""
        manager = InvestmentThesisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'thesis_summary': 'AI 需求帶動先進製程成長',
            'buy_reasons': '技術領先、客戶優質、AI 需求強勁',
            'target_price': 800,
            'thesis_status': '投資邏輯成立',
            'confidence_level': '高',
            'score': 85
        }

        result = manager.add_investment_thesis(data)
        assert result is True

    def test_get_investment_thesis(self, mock_config):
        """測試取得投資邏輯"""
        manager = InvestmentThesisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'thesis_summary': 'AI 需求帶動先進製程成長',
            'score': 85
        }
        manager.add_investment_thesis(data)

        thesis = manager.get_investment_thesis('2330')
        assert thesis is not None
        assert thesis['thesis_summary'] == 'AI 需求帶動先進製程成長'


class TestRiskAnalysisManager:
    """風險分析管理器測試類別"""

    def test_add_risk_analysis(self, mock_config):
        """測試新增風險分析"""
        manager = RiskAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'business_risks': '技術競爭、產能過剩風險',
            'financial_risks': '資本支出壓力',
            'market_risks': '半導體週期波動',
            'regulatory_risks': '各國加強監管',
            'overall_risk_level': '中等',
            'risk_rating': '風險中等',
            'score': 70
        }

        result = manager.add_risk_analysis(data)
        assert result is True

    def test_get_risk_analysis(self, mock_config):
        """測試取得風險分析"""
        manager = RiskAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'overall_risk_level': '中等',
            'score': 70
        }
        manager.add_risk_analysis(data)

        analysis = manager.get_risk_analysis('2330')
        assert analysis is not None
        assert analysis['overall_risk_level'] == '中等'

    def test_get_risk_heatmap(self, mock_config):
        """測試取得風險熱力圖"""
        manager = RiskAnalysisManager()
        data = {
            'stock_id': '2330',
            'analysis_date': '2024-03-31',
            'business_risks': '技術競爭風險',
            'financial_risks': '資本支出壓力',
            'market_risks': '半導體週期波動',
            'overall_risk_level': '中等'
        }
        manager.add_risk_analysis(data)

        heatmap = manager.get_risk_heatmap('2330')
        assert heatmap['has_analysis'] is True
        assert 'heatmap' in heatmap


class TestGetManagerFunctions:
    """測試取得管理器實例函數"""

    def test_get_business_model_manager(self):
        """測試取得商業模式管理器實例"""
        manager = get_business_model_manager()
        assert manager is not None
        assert isinstance(manager, BusinessModelManager)

    def test_get_management_analysis_manager(self):
        """測試取得經營管理層分析管理器實例"""
        manager = get_management_analysis_manager()
        assert manager is not None
        assert isinstance(manager, ManagementAnalysisManager)

    def test_get_financial_analysis_manager(self):
        """測試取得財報分析管理器實例"""
        manager = get_financial_analysis_manager()
        assert manager is not None
        assert isinstance(manager, FinancialAnalysisManager)

    def test_get_valuation_analysis_manager(self):
        """測試取得公司估值分析管理器實例"""
        manager = get_valuation_analysis_manager()
        assert manager is not None
        assert isinstance(manager, ValuationAnalysisManager)

    def test_get_investment_thesis_manager(self):
        """測試取得投資邏輯管理器實例"""
        manager = get_investment_thesis_manager()
        assert manager is not None
        assert isinstance(manager, InvestmentThesisManager)

    def test_get_risk_analysis_manager(self):
        """測試取得風險分析管理器實例"""
        manager = get_risk_analysis_manager()
        assert manager is not None
        assert isinstance(manager, RiskAnalysisManager)