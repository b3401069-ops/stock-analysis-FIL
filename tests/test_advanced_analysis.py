"""Smoke tests for advanced_analysis.py"""
import sys
from pathlib import Path

import pytest

# Fix path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
_venv_sp = str(project_root / "venv" / "Lib" / "site-packages")
if _venv_sp in sys.path:
    sys.path.remove(_venv_sp)
    sys.path.insert(1, _venv_sp)

from scripts.advanced_analysis import (
    dcf_valuation,
    analyze_news_sentiment,
    analyze_earnings_call_tone,
    generate_anti_bias_framework,
    moat_scoring,
    fetch_sec_filings,
)


# ---- Fixtures ----

@pytest.fixture
def mock_fundamental():
    return {
        "fundamental": {
            "profitability": {
                "gross_margin": 0.62, "operating_margin": 0.58,
                "net_margin": 0.47, "roe": 0.36,
            },
            "financial_health": {
                "free_cash_flow": 7e11, "revenue": 4e12,
            },
            "valuation": {"market_cap": 6e13, "pe_trailing": 32.8, "pe_forward": 18.9},
            "growth": {"revenue_growth": 0.35},
            "analyst_ratings": {
                "num_analysts": 34, "current_price": 2415, "target_mean": 2834,
            },
            "ownership": {"institutional_pct": 0.44, "insider_pct": 0.0002},
            "company_info": {"sector": "Technology"},
        },
        "technical": {
            "price_data": {"price_vs_52w_high_pct": -4.7, "change_6m_pct": 60},
            "technical_indicators": {
                "rsi_14": 40.6,
                "trend_signals": ["短期均線多頭排列 (MA5 > MA20)"],
            },
        },
    }


@pytest.fixture
def sample_news():
    return [
        {"title": "台積電營收大增看好", "date": "2026-07-10", "content": "成長突破創新高利多"},
        {"title": "半導體面臨關稅風險", "date": "2026-07-09", "content": "下跌壓力挑戰衰退"},
    ]


# ---- News Sentiment ----

class TestNewsSentiment:
    def test_basic_scoring(self, sample_news):
        r = analyze_news_sentiment(sample_news)
        assert r["article_count"] == 2
        assert -1 <= r["score"] <= 1
        assert len(r["articles"]) == 2
        assert r["label"] != ""

    def test_empty_news(self):
        r = analyze_news_sentiment([])
        assert r["score"] == 0
        assert r["label"] == "無數據"

    def test_all_positive(self):
        news = [
            {"title": "營收成長突破看好", "date": "2026-07-10", "content": "利多創新高加碼"},
        ]
        r = analyze_news_sentiment(news)
        assert r["score"] > 0
        assert "正面" in r["label"]

    def test_all_negative(self):
        news = [
            {"title": "下跌衰退風險壓力", "date": "2026-07-10", "content": "利空虧損裁員挑戰"},
        ]
        r = analyze_news_sentiment(news)
        assert r["score"] < 0
        assert "負面" in r["label"]


# ---- Earnings Call Tone ----

class TestEarningsTone:
    def test_basic(self):
        earnings = [
            {"key_highlights": "營收成長看好樂觀擴張", "call_date": "2026-04-15"},
            {"key_highlights": "挑戰壓力謹慎下調風險", "call_date": "2026-01-15"},
        ]
        r = analyze_earnings_call_tone(earnings)
        assert r["call_count"] == 2
        assert -1 <= r["score"] <= 1

    def test_empty(self):
        r = analyze_earnings_call_tone([])
        assert r["tone"] == "無數據"


# ---- Moat Scoring ----

class TestMoatScoring:
    def test_strong_moat(self, mock_fundamental):
        m = moat_scoring(mock_fundamental)
        assert 1 <= m["total_score"] <= 10
        assert "護城河" in m["moat_width"]
        assert len(m["scores"]) == 10
        assert m["total_score"] >= 7  # TSMC-like data → strong moat

    def test_weak_moat(self):
        weak = {
            "fundamental": {
                "profitability": {"gross_margin": 0.10, "operating_margin": 0.05, "net_margin": 0.03, "roe": 0.05},
                "financial_health": {"free_cash_flow": 1e8, "revenue": 1e10},
                "valuation": {"market_cap": 1e10},
                "growth": {"revenue_growth": 0.02},
                "analyst_ratings": {"num_analysts": 2},
                "ownership": {"institutional_pct": 0.10, "insider_pct": 0.01},
            }
        }
        m = moat_scoring(weak)
        assert m["total_score"] < 5  # low moat


# ---- Anti-Bias ----

class TestAntiBias:
    def test_framework_completeness(self, mock_fundamental):
        ab = generate_anti_bias_framework(mock_fundamental)
        assert "bull_case" in ab
        assert "bear_case" in ab
        assert "cognitive_traps" in ab
        assert "pre_mortem" in ab
        assert len(ab["bull_case"]["points"]) >= 1
        assert len(ab["bear_case"]["points"]) >= 1
        assert len(ab["pre_mortem"]) >= 1

    def test_bias_direction(self, mock_fundamental):
        ab = generate_anti_bias_framework(mock_fundamental)
        # TSMC-like data should be biased bullish
        assert ab["balance"] == "偏多"


# ---- DCF (live API) ----

class TestDCF:
    def test_tsmc_dcf(self):
        dcf = dcf_valuation("2330.TW")
        if "error" in dcf:
            pytest.skip(f"DCF data unavailable: {dcf['error']}")
        assert "valuation" in dcf
        assert "projections" in dcf
        assert "sensitivity" in dcf
        assert "other_methods" in dcf
        assert len(dcf["projections"]) == 5
        assert dcf["valuation"]["intrinsic_value_per_share"] > 0

    def test_nvda_dcf(self):
        dcf = dcf_valuation("NVDA")
        if "error" in dcf:
            pytest.skip(f"DCF data unavailable: {dcf['error']}")
        assert dcf["valuation"]["intrinsic_value_per_share"] > 0
