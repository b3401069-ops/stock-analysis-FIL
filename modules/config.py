"""
股票追蹤與決策輔助系統 V1 - 配置模組
Stock Tracking & Decision Support System V1 - Configuration Module
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()


class Config:
    """配置類別"""
    
    # 專案根目錄
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    
    # 資料庫配置
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'data' / 'stocks.db'))
    
    # Telegram 配置
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')
    
    # 資料匯入配置
    SAMPLE_STOCKS_CSV: str = os.getenv('SAMPLE_STOCKS_CSV', str(PROJECT_ROOT / 'data' / 'sample_stocks.csv'))
    SAMPLE_PRICES_CSV: str = os.getenv('SAMPLE_PRICES_CSV', str(PROJECT_ROOT / 'data' / 'sample_prices.csv'))
    SAMPLE_FUNDAMENTALS_CSV: str = os.getenv('SAMPLE_FUNDAMENTALS_CSV', str(PROJECT_ROOT / 'data' / 'sample_fundamentals.csv'))

    # V1.1 資料匯入配置
    SAMPLE_EARNINGS_CALLS_CSV: str = os.getenv('SAMPLE_EARNINGS_CALLS_CSV', str(PROJECT_ROOT / 'data' / 'sample_earnings_calls.csv'))
    SAMPLE_ANALYST_VIEWS_CSV: str = os.getenv('SAMPLE_ANALYST_VIEWS_CSV', str(PROJECT_ROOT / 'data' / 'sample_analyst_views.csv'))
    SAMPLE_RESEARCH_5PLUS2_CSV: str = os.getenv('SAMPLE_RESEARCH_5PLUS2_CSV', str(PROJECT_ROOT / 'data' / 'sample_research_5plus2.csv'))
    SAMPLE_MACRO_INDICATORS_CSV: str = os.getenv('SAMPLE_MACRO_INDICATORS_CSV', str(PROJECT_ROOT / 'data' / 'sample_macro_indicators.csv'))

    # 5+2 明細分析樣本資料
    SAMPLE_INDUSTRY_ANALYSIS_CSV: str = os.getenv('SAMPLE_INDUSTRY_ANALYSIS_CSV', str(PROJECT_ROOT / 'data' / 'sample_industry_analysis.csv'))
    SAMPLE_BUSINESS_MODEL_CSV: str = os.getenv('SAMPLE_BUSINESS_MODEL_CSV', str(PROJECT_ROOT / 'data' / 'sample_business_model.csv'))
    SAMPLE_MANAGEMENT_ANALYSIS_CSV: str = os.getenv('SAMPLE_MANAGEMENT_ANALYSIS_CSV', str(PROJECT_ROOT / 'data' / 'sample_management_analysis.csv'))
    SAMPLE_FINANCIAL_ANALYSIS_CSV: str = os.getenv('SAMPLE_FINANCIAL_ANALYSIS_CSV', str(PROJECT_ROOT / 'data' / 'sample_financial_analysis.csv'))
    SAMPLE_VALUATION_ANALYSIS_CSV: str = os.getenv('SAMPLE_VALUATION_ANALYSIS_CSV', str(PROJECT_ROOT / 'data' / 'sample_valuation_analysis.csv'))
    SAMPLE_INVESTMENT_THESIS_CSV: str = os.getenv('SAMPLE_INVESTMENT_THESIS_CSV', str(PROJECT_ROOT / 'data' / 'sample_investment_thesis.csv'))
    SAMPLE_RISK_ANALYSIS_CSV: str = os.getenv('SAMPLE_RISK_ANALYSIS_CSV', str(PROJECT_ROOT / 'data' / 'sample_risk_analysis.csv'))
    
    # FinMind 資料源配置
    FINMIND_TOKEN: Optional[str] = os.getenv('FINMIND_TOKEN')
    # 增量更新時，資料庫無資料的股票往回抓的天數
    DATA_UPDATE_LOOKBACK_DAYS: int = int(os.getenv('DATA_UPDATE_LOOKBACK_DAYS', '180'))

    # 宏觀指標抓取清單（FinMind dataset）
    # enabled=False 者不抓取；TaiwanBusinessIndicator 需 FinMind Backer/Sponsor 方案
    MACRO_FETCH_SPECS: list = [
        {'dataset': 'InterestRate', 'data_id': 'FED', 'indicator_name': 'FED 利率',
         'value_column': 'interest_rate', 'unit': '%', 'region': 'US', 'frequency': '不定期'},
        {'dataset': 'InterestRate', 'data_id': 'ECB', 'indicator_name': 'ECB 利率',
         'value_column': 'interest_rate', 'unit': '%', 'region': 'EU', 'frequency': '不定期'},
        {'dataset': 'InterestRate', 'data_id': 'BOJ', 'indicator_name': 'BOJ 利率',
         'value_column': 'interest_rate', 'unit': '%', 'region': 'JP', 'frequency': '不定期'},
        {'dataset': 'TaiwanExchangeRate', 'data_id': 'USD', 'indicator_name': 'USD/TWD 匯率',
         'value_column': 'spot_sell', 'unit': 'TWD', 'region': 'TW', 'frequency': '每日',
         'positive_only': True},
        {'dataset': 'GovernmentBondsYield', 'data_id': 'United States 10-Year',
         'indicator_name': '美國 10 年期公債殖利率',
         'value_column': 'value', 'unit': '%', 'region': 'US', 'frequency': '每日'},
        {'dataset': 'GovernmentBondsYield', 'data_id': 'United States 2-Year',
         'indicator_name': '美國 2 年期公債殖利率',
         'value_column': 'value', 'unit': '%', 'region': 'US', 'frequency': '每日'},
        # 景氣對策信號需 FinMind Backer/Sponsor 方案，贊助後改 enabled=True
        {'dataset': 'TaiwanBusinessIndicator', 'data_id': None,
         'indicator_name': '景氣對策信號分數',
         'value_column': 'monitoring', 'unit': '分', 'region': 'TW', 'frequency': '每月',
         'enabled': False},
    ]

    # 回測配置
    BACKTEST_INITIAL_CAPITAL: float = float(os.getenv('BACKTEST_INITIAL_CAPITAL', '1000000'))
    BACKTEST_RISK_FREE_RATE: float = float(os.getenv('BACKTEST_RISK_FREE_RATE', '0.02'))

    # 5+2 研究框架配置
    RESEARCH_5PLUS2_WEIGHTS: dict = {
        'industry_analysis': 0.15,
        'business_model': 0.15,
        'management_analysis': 0.15,
        'financial_analysis': 0.15,
        'valuation': 0.15,
        'investment_thesis': 0.15,
        'risk_analysis': 0.10
    }

    RESEARCH_5PLUS2_THRESHOLDS: dict = {
        'investment_logic_established': 80,
        'investment_logic_partial': 60,
        'investment_logic_pending': 40,
        'investment_logic_weakening': 0
    }
    
    # Streamlit 配置
    STREAMLIT_PORT: int = int(os.getenv('STREAMLIT_PORT', '8501'))
    # 預設僅監聽本機；需區網存取時再以環境變數改為 0.0.0.0
    STREAMLIT_HOST: str = os.getenv('STREAMLIT_HOST', '127.0.0.1')
    
    @classmethod
    def get_database_url(cls) -> str:
        """取得資料庫 URL"""
        return f"sqlite:///{cls.DATABASE_PATH}"
    
    @classmethod
    def is_telegram_enabled(cls) -> bool:
        """檢查 Telegram 是否已設定"""
        return bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID)
    
    @classmethod
    def get_telegram_config(cls) -> dict:
        """取得 Telegram 配置"""
        return {
            'bot_token': cls.TELEGRAM_BOT_TOKEN,
            'chat_id': cls.TELEGRAM_CHAT_ID,
            'enabled': cls.is_telegram_enabled()
        }
    
    @classmethod
    def validate(cls) -> list:
        """驗證配置"""
        errors = []
        
        # 檢查資料庫路徑
        db_path = Path(cls.DATABASE_PATH)
        if not db_path.parent.exists():
            errors.append(f"資料庫目錄不存在: {db_path.parent}")
        
        # 檢查 CSV 檔案
        csv_files = [
            ('SAMPLE_STOCKS_CSV', cls.SAMPLE_STOCKS_CSV),
            ('SAMPLE_PRICES_CSV', cls.SAMPLE_PRICES_CSV),
            ('SAMPLE_FUNDAMENTALS_CSV', cls.SAMPLE_FUNDAMENTALS_CSV),
            ('SAMPLE_EARNINGS_CALLS_CSV', cls.SAMPLE_EARNINGS_CALLS_CSV),
            ('SAMPLE_ANALYST_VIEWS_CSV', cls.SAMPLE_ANALYST_VIEWS_CSV),
            ('SAMPLE_RESEARCH_5PLUS2_CSV', cls.SAMPLE_RESEARCH_5PLUS2_CSV),
            ('SAMPLE_MACRO_INDICATORS_CSV', cls.SAMPLE_MACRO_INDICATORS_CSV),
            ('SAMPLE_INDUSTRY_ANALYSIS_CSV', cls.SAMPLE_INDUSTRY_ANALYSIS_CSV),
            ('SAMPLE_BUSINESS_MODEL_CSV', cls.SAMPLE_BUSINESS_MODEL_CSV),
            ('SAMPLE_MANAGEMENT_ANALYSIS_CSV', cls.SAMPLE_MANAGEMENT_ANALYSIS_CSV),
            ('SAMPLE_FINANCIAL_ANALYSIS_CSV', cls.SAMPLE_FINANCIAL_ANALYSIS_CSV),
            ('SAMPLE_VALUATION_ANALYSIS_CSV', cls.SAMPLE_VALUATION_ANALYSIS_CSV),
            ('SAMPLE_INVESTMENT_THESIS_CSV', cls.SAMPLE_INVESTMENT_THESIS_CSV),
            ('SAMPLE_RISK_ANALYSIS_CSV', cls.SAMPLE_RISK_ANALYSIS_CSV)
        ]
        
        for name, path in csv_files:
            if not Path(path).exists():
                errors.append(f"{name} 檔案不存在: {path}")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """列印配置（隱藏敏感資訊）"""
        print("=" * 60)
        print("系統配置")
        print("=" * 60)
        print(f"專案根目錄: {cls.PROJECT_ROOT}")
        print(f"資料庫路徑: {cls.DATABASE_PATH}")
        print(f"Telegram 啟用: {cls.is_telegram_enabled()}")
        print(f"初始資金: {cls.BACKTEST_INITIAL_CAPITAL:,.0f}")
        print(f"無風險利率: {cls.BACKTEST_RISK_FREE_RATE:.2%}")
        print()
        print("V1.1 資料檔:")
        print(f"  電話會議: {cls.SAMPLE_EARNINGS_CALLS_CSV}")
        print(f"  投行觀點: {cls.SAMPLE_ANALYST_VIEWS_CSV}")
        print(f"  5+2 評估: {cls.SAMPLE_RESEARCH_5PLUS2_CSV}")
        print(f"  宏觀指標: {cls.SAMPLE_MACRO_INDICATORS_CSV}")
        print("=" * 60)


# 建立全域配置實例
config = Config()


def get_config() -> Config:
    """取得配置實例"""
    return config