#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 V1.1 - 資料庫擴展腳本
Stock Tracking & Decision Support System V1.1 - Database Extension Script

擴展 V1 資料庫，新增 5+2 投資研究框架相關資料表
"""

import sqlite3
import csv
import os
from pathlib import Path
import sys

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.config import get_config
from modules.console import safe_print


def extend_database(db_path=None):
    """擴展資料庫，新增 V1.1 資料表

    Args:
        db_path: 資料庫路徑，若未指定則使用 config.DATABASE_PATH
    """
    if db_path is None:
        config = get_config()
        db_path = Path(config.DATABASE_PATH)
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        safe_print(f"❌ 資料庫不存在: {db_path}")
        safe_print("請先執行 V1 的 init_db.py 初始化資料庫")
        return False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # ============================================================
    # 5+2 投資研究框架資料表
    # ============================================================

    # 1. 行業分析
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS industry_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            industry_name TEXT,
            market_size TEXT,
            growth_rate REAL,
            competition_level TEXT,
            entry_barriers TEXT,
            regulatory_environment TEXT,
            industry_trends TEXT,
            key_drivers TEXT,
            threats TEXT,
            outlook TEXT,
            score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    # 2. 商業模式分析
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

    # 3. 經營管理層分析
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

    # 4. 財報分析
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    # 5. 公司估值分析
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

    # 6. 投資邏輯
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

    # 7. 風險分析
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

    # 8. 總體經濟指標
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS macro_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_name TEXT NOT NULL,
            indicator_date DATE NOT NULL,
            value REAL,
            unit TEXT,
            region TEXT,
            source TEXT,
            frequency TEXT,
            previous_value REAL,
            change REAL,
            trend TEXT,
            impact_assessment TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_name, indicator_date, region)
        )
    """)

    # 9. 電話會議紀錄
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS earnings_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            call_date DATE NOT NULL,
            quarter TEXT,
            fiscal_year TEXT,
            call_time TEXT,
            participants TEXT,
            management_guidance TEXT,
            key_highlights TEXT,
            revenue_guidance TEXT,
            earnings_guidance TEXT,
            margin_guidance TEXT,
            capex_guidance TEXT,
            analyst_questions TEXT,
            management_responses TEXT,
            sentiment TEXT,
            surprises TEXT,
            risk_factors TEXT,
            outlook_summary TEXT,
            transcript_summary TEXT,
            notes TEXT,
            source TEXT DEFAULT '公開資訊',
            source_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, call_date, quarter)
        )
    """)

    # 10. 投行觀點
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyst_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            report_date DATE NOT NULL,
            analyst_firm TEXT,
            analyst_name TEXT,
            rating TEXT,
            target_price REAL,
            previous_target REAL,
            recommendation TEXT,
            key_findings TEXT,
            strengths TEXT,
            weaknesses TEXT,
            opportunities TEXT,
            threats TEXT,
            financial_estimates TEXT,
            valuation_methodology TEXT,
            risk_factors TEXT,
            catalysts TEXT,
            report_summary TEXT,
            confidence_level TEXT,
            notes TEXT,
            source TEXT DEFAULT '投行研報',
            source_url TEXT,
            source_type TEXT DEFAULT '摘要',
            is_paid_report INTEGER DEFAULT 0,
            summary_only INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_as_of DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, report_date, analyst_firm)
        )
    """)

    # 11. 5+2 綜合評估
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_5plus2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            industry_score REAL,
            business_model_score REAL,
            management_score REAL,
            financial_score REAL,
            valuation_score REAL,
            investment_thesis_score REAL,
            risk_score REAL,
            total_score REAL,
            overall_rating TEXT,
            investment_logic TEXT,
            key_strengths TEXT,
            key_weaknesses TEXT,
            action_items TEXT,
            next_review_date DATE,
            analyst_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        )
    """)

    conn.commit()
    
    # 執行 migration 以補齊既有資料表可能缺少的欄位
    safe_print("\n🔄 執行欄位 Migration...")
    from scripts.migration_v1_1 import migrate_v1_1_source_fields
    migrate_v1_1_source_fields(db_path)
    
    safe_print("\n✅ V1.1 資料表擴展完成")
    safe_print("   新增 11 個資料表:")
    safe_print("   - industry_analysis (行業分析)")
    safe_print("   - business_model (商業模式)")
    safe_print("   - management_analysis (管理層分析)")
    safe_print("   - financial_analysis (財報分析)")
    safe_print("   - valuation_analysis (估值分析)")
    safe_print("   - investment_thesis (投資邏輯)")
    safe_print("   - risk_analysis (風險分析)")
    safe_print("   - macro_indicators (總體經濟)")
    safe_print("   - earnings_calls (電話會議)")
    safe_print("   - analyst_views (投行觀點)")
    safe_print("   - research_5plus2 (5+2 綜合評估)")
    safe_print("   - 所有表格已補齊 source/source_url/data_as_of 欄位")

    conn.close()
    return True


def import_sample_earnings_calls(db_path: Path, csv_path: Path):
    """匯入電話會議樣本資料

    Args:
        db_path: 資料庫路徑
        csv_path: CSV 檔案路徑
    """
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO earnings_calls
                (stock_id, call_date, quarter, fiscal_year, call_time,
                 management_guidance, key_highlights, revenue_guidance,
                 earnings_guidance, sentiment, outlook_summary, transcript_summary,
                 source, source_url, data_as_of, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['stock_id'], row['call_date'], row['quarter'], row['fiscal_year'],
                row.get('call_time', ''), row.get('management_guidance', ''),
                row.get('key_highlights', ''), row.get('revenue_guidance', ''),
                row.get('earnings_guidance', ''), row.get('sentiment', ''),
                row.get('outlook_summary', ''), row.get('transcript_summary', ''),
                row.get('source', '公開資訊'), row.get('source_url', ''),
                row.get('data_as_of', row['call_date']),
                row.get('notes', '')
            ))
            count += 1

    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入電話會議資料: {count} 筆")
    return True


def import_sample_analyst_views(db_path: Path, csv_path: Path):
    """匯入投行觀點樣本資料

    Args:
        db_path: 資料庫路徑
        csv_path: CSV 檔案路徑
    """
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO analyst_views
                (stock_id, report_date, analyst_firm, analyst_name, rating,
                 target_price, previous_target, recommendation, key_findings,
                 strengths, weaknesses, report_summary, confidence_level,
                 source, source_url, source_type, is_paid_report, summary_only,
                 data_as_of, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['stock_id'], row['report_date'], row['analyst_firm'],
                row.get('analyst_name', ''), row.get('rating', ''),
                float(row['target_price']) if row.get('target_price') else None,
                float(row['previous_target']) if row.get('previous_target') else None,
                row.get('recommendation', ''), row.get('key_findings', ''),
                row.get('strengths', ''), row.get('weaknesses', ''),
                row.get('report_summary', ''), row.get('confidence_level', ''),
                row.get('source', '投行研報'), row.get('source_url', ''),
                row.get('source_type', '摘要'),
                1 if row.get('is_paid_report', '0') == '1' else 0,
                1 if row.get('summary_only', '1') == '1' else 0,
                row.get('data_as_of', row['report_date']),
                row.get('notes', '')
            ))
            count += 1

    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入投行觀點資料: {count} 筆")
    return True


def import_sample_research_5plus2(db_path: Path, csv_path: Path):
    """匯入 5+2 綜合評估樣本資料

    Args:
        db_path: 資料庫路徑
        csv_path: CSV 檔案路徑
    """
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO research_5plus2
                (stock_id, analysis_date, industry_score, business_model_score,
                 management_score, financial_score, valuation_score,
                 investment_thesis_score, risk_score, total_score,
                 overall_rating, investment_logic, key_strengths, key_weaknesses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['stock_id'], row['analysis_date'],
                float(row['industry_score']), float(row['business_model_score']),
                float(row['management_score']), float(row['financial_score']),
                float(row['valuation_score']), float(row['investment_thesis_score']),
                float(row['risk_score']), float(row['total_score']),
                row['overall_rating'], row.get('investment_logic', ''),
                row.get('key_strengths', ''), row.get('key_weaknesses', '')
            ))
            count += 1

    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入 5+2 綜合評估資料: {count} 筆")
    return True


def import_sample_macro_indicators(db_path: Path, csv_path: Path):
    """匯入總體經濟指標樣本資料

    Args:
        db_path: 資料庫路徑
        csv_path: CSV 檔案路徑
    """
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO macro_indicators
                (indicator_name, indicator_date, value, unit, region,
                 source, frequency, previous_value, change, trend,
                 impact_assessment, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['indicator_name'], row['indicator_date'],
                float(row['value']), row.get('unit', ''),
                row.get('region', ''), row.get('source', ''),
                row.get('frequency', ''),
                float(row['previous_value']) if row.get('previous_value') else None,
                float(row['change']) if row.get('change') else None,
                row.get('trend', ''), row.get('impact_assessment', ''),
                row.get('notes', '')
            ))
            count += 1

    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入總體經濟指標資料: {count} 筆")
    return True


def import_sample_industry_analysis(db_path: Path, csv_path: Path):
    """匯入行業分析樣本資料"""
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO industry_analysis
                (stock_id, analysis_date, industry_name, market_size,
                 growth_rate, competition_level, entry_barriers,
                 regulatory_environment, industry_trends, key_drivers,
                 threats, outlook, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["stock_id"], row["analysis_date"],
                row.get("industry_name", ""), row.get("market_size", ""),
                float(row["growth_rate"]) if row.get("growth_rate") else None,
                row.get("competition_level", ""), row.get("entry_barriers", ""),
                row.get("regulatory_environment", ""), row.get("industry_trends", ""),
                row.get("key_drivers", ""), row.get("threats", ""),
                row.get("outlook", ""),
                float(row["score"]) if row.get("score") else None,
                row.get("notes", "")
            ))
            count += 1
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入行業分析資料: {count} 筆")
    return True

def import_sample_business_model(db_path: Path, csv_path: Path):
    """匯入商業模式分析樣本資料"""
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO business_model
                (stock_id, analysis_date, business_model_type, revenue_streams,
                 value_proposition, competitive_advantage, customer_segments,
                 cost_structure, key_partners, scalability, sustainability,
                 score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["stock_id"], row["analysis_date"],
                row.get("business_model_type", ""), row.get("revenue_streams", ""),
                row.get("value_proposition", ""), row.get("competitive_advantage", ""),
                row.get("customer_segments", ""), row.get("cost_structure", ""),
                row.get("key_partners", ""), row.get("scalability", ""),
                row.get("sustainability", ""),
                float(row["score"]) if row.get("score") else None,
                row.get("notes", "")
            ))
            count += 1
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入商業模式分析資料: {count} 筆")
    return True

def import_sample_management_analysis(db_path: Path, csv_path: Path):
    """匯入管理層分析樣本資料"""
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO management_analysis
                (stock_id, analysis_date, ceo_name, ceo_background,
                 management_team_size, avg_tenure_years, insider_ownership,
                 major_shareholders, corporate_governance, compensation_structure,
                 track_record, strategic_vision, execution_capability,
                 score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["stock_id"], row["analysis_date"],
                row.get("ceo_name", ""), row.get("ceo_background", ""),
                int(row["management_team_size"]) if row.get("management_team_size") else None,
                float(row["avg_tenure_years"]) if row.get("avg_tenure_years") else None,
                float(row["insider_ownership"]) if row.get("insider_ownership") else None,
                row.get("major_shareholders", ""), row.get("corporate_governance", ""),
                row.get("compensation_structure", ""), row.get("track_record", ""),
                row.get("strategic_vision", ""), row.get("execution_capability", ""),
                float(row["score"]) if row.get("score") else None,
                row.get("notes", "")
            ))
            count += 1
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入管理層分析資料: {count} 筆")
    return True

def import_sample_financial_analysis(db_path: Path, csv_path: Path):
    """匯入財報分析樣本資料"""
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO financial_analysis
                (stock_id, analysis_date, report_period, revenue, revenue_growth,
                 gross_margin, operating_margin, net_margin, roe, roa,
                 debt_to_equity, current_ratio, quick_ratio, interest_coverage,
                 free_cash_flow, cash_flow_growth, earnings_quality,
                 accounting_risks, score, notes, source, source_url, data_as_of)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["stock_id"], row["analysis_date"],
                row.get("report_period", ""),
                float(row["revenue"]) if row.get("revenue") else None,
                float(row["revenue_growth"]) if row.get("revenue_growth") else None,
                float(row["gross_margin"]) if row.get("gross_margin") else None,
                float(row["operating_margin"]) if row.get("operating_margin") else None,
                float(row["net_margin"]) if row.get("net_margin") else None,
                float(row["roe"]) if row.get("roe") else None,
                float(row["roa"]) if row.get("roa") else None,
                float(row["debt_to_equity"]) if row.get("debt_to_equity") else None,
                float(row["current_ratio"]) if row.get("current_ratio") else None,
                float(row["quick_ratio"]) if row.get("quick_ratio") else None,
                float(row["interest_coverage"]) if row.get("interest_coverage") else None,
                float(row["free_cash_flow"]) if row.get("free_cash_flow") else None,
                float(row["cash_flow_growth"]) if row.get("cash_flow_growth") else None,
                row.get("earnings_quality", ""), row.get("accounting_risks", ""),
                float(row["score"]) if row.get("score") else None,
                row.get("notes", ""),
                row.get("source", "研報"),
                row.get("source_url", ""),
                row.get("data_as_of", row["analysis_date"]),
            ))
            count += 1
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入財報分析資料: {count} 筆")
    return True

def import_sample_valuation_analysis(db_path: Path, csv_path: Path):
    """匯入估值分析樣本資料"""
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO valuation_analysis
                (stock_id, analysis_date, current_price, pe_ratio, pb_ratio,
                 ps_ratio, pcf_ratio, ev_ebitda, peg_ratio, dividend_yield,
                 dcf_value, relative_value, historical_avg_pe, industry_avg_pe,
                 margin_of_safety, valuation_rating, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["stock_id"], row["analysis_date"],
                float(row["current_price"]) if row.get("current_price") else None,
                float(row["pe_ratio"]) if row.get("pe_ratio") else None,
                float(row["pb_ratio"]) if row.get("pb_ratio") else None,
                float(row["ps_ratio"]) if row.get("ps_ratio") else None,
                float(row["pcf_ratio"]) if row.get("pcf_ratio") else None,
                float(row["ev_ebitda"]) if row.get("ev_ebitda") else None,
                float(row["peg_ratio"]) if row.get("peg_ratio") else None,
                float(row["dividend_yield"]) if row.get("dividend_yield") else None,
                float(row["dcf_value"]) if row.get("dcf_value") else None,
                float(row["relative_value"]) if row.get("relative_value") else None,
                float(row["historical_avg_pe"]) if row.get("historical_avg_pe") else None,
                float(row["industry_avg_pe"]) if row.get("industry_avg_pe") else None,
                float(row["margin_of_safety"]) if row.get("margin_of_safety") else None,
                row.get("valuation_rating", ""),
                float(row["score"]) if row.get("score") else None,
                row.get("notes", "")
            ))
            count += 1
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入估值分析資料: {count} 筆")
    return True

def import_sample_investment_thesis(db_path: Path, csv_path: Path):
    """匯入投資邏輯樣本資料"""
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO investment_thesis
                (stock_id, analysis_date, thesis_summary, buy_reasons,
                 catalysts, target_price, investment_horizon, position_sizing,
                 entry_strategy, exit_strategy, thesis_status, confidence_level,
                 score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["stock_id"], row["analysis_date"],
                row.get("thesis_summary", ""), row.get("buy_reasons", ""),
                row.get("catalysts", ""),
                float(row["target_price"]) if row.get("target_price") else None,
                row.get("investment_horizon", ""), row.get("position_sizing", ""),
                row.get("entry_strategy", ""), row.get("exit_strategy", ""),
                row.get("thesis_status", ""), row.get("confidence_level", ""),
                float(row["score"]) if row.get("score") else None,
                row.get("notes", "")
            ))
            count += 1
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入投資邏輯資料: {count} 筆")
    return True

def import_sample_risk_analysis(db_path: Path, csv_path: Path):
    """匯入風險分析樣本資料"""
    if not csv_path.exists():
        safe_print(f"⚠️  找不到檔案: {csv_path}")
        return False
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO risk_analysis
                (stock_id, analysis_date, business_risks, financial_risks,
                 market_risks, regulatory_risks, competitive_risks,
                 management_risks, liquidity_risks, currency_risks,
                 geopolitical_risks, black_swan_risks, risk_mitigation,
                 overall_risk_level, risk_rating, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["stock_id"], row["analysis_date"],
                row.get("business_risks", ""), row.get("financial_risks", ""),
                row.get("market_risks", ""), row.get("regulatory_risks", ""),
                row.get("competitive_risks", ""), row.get("management_risks", ""),
                row.get("liquidity_risks", ""), row.get("currency_risks", ""),
                row.get("geopolitical_risks", ""), row.get("black_swan_risks", ""),
                row.get("risk_mitigation", ""), row.get("overall_risk_level", ""),
                row.get("risk_rating", ""),
                float(row["score"]) if row.get("score") else None,
                row.get("notes", "")
            ))
            count += 1
    conn.commit()
    conn.close()
    safe_print(f"✅ 匯入風險分析資料: {count} 筆")
    return True

def import_v1_1_sample_data():
    """匯入所有 V1.1 樣本資料

    Returns:
        bool: 整體匯入是否成功
    """
    config = get_config()
    db_path = Path(config.DATABASE_PATH)

    if not db_path.exists():
        safe_print("❌ 資料庫不存在，請先執行 init_db.py")
        return False

    safe_print("\n📦 開始匯入 V1.1 樣本資料...")

    # 匯入電話會議資料
    earnings_csv = project_root / 'data' / 'sample_earnings_calls.csv'
    if not import_sample_earnings_calls(db_path, earnings_csv):
        safe_print("⚠️  電話會議資料匯入失敗，繼續匯入其他資料...")

    # 匯入投行觀點資料
    analyst_csv = project_root / 'data' / 'sample_analyst_views.csv'
    if not import_sample_analyst_views(db_path, analyst_csv):
        safe_print("⚠️  投行觀點資料匯入失敗，繼續匯入其他資料...")

    # 匯入 5+2 綜合評估資料
    research_csv = project_root / 'data' / 'sample_research_5plus2.csv'
    if not import_sample_research_5plus2(db_path, research_csv):
        safe_print("⚠️  5+2 綜合評估資料匯入失敗，繼續匯入其他資料...")

    # 匯入總體經濟指標資料
    macro_csv = project_root / 'data' / 'sample_macro_indicators.csv'
    if not import_sample_macro_indicators(db_path, macro_csv):
        safe_print("⚠️  總體經濟指標資料匯入失敗，繼續匯入其他資料...")


    # 匯入 5+2 明細分析資料
    industry_csv = project_root / "data" / "sample_industry_analysis.csv"
    if not import_sample_industry_analysis(db_path, industry_csv):
        safe_print("⚠️  行業分析資料匯入失敗，繼續匯入其他資料...")

    business_csv = project_root / "data" / "sample_business_model.csv"
    if not import_sample_business_model(db_path, business_csv):
        safe_print("⚠️  商業模式分析資料匯入失敗，繼續匯入其他資料...")

    management_csv = project_root / "data" / "sample_management_analysis.csv"
    if not import_sample_management_analysis(db_path, management_csv):
        safe_print("⚠️  管理層分析資料匯入失敗，繼續匯入其他資料...")

    financial_csv = project_root / "data" / "sample_financial_analysis.csv"
    if not import_sample_financial_analysis(db_path, financial_csv):
        safe_print("⚠️  財報分析資料匯入失敗，繼續匯入其他資料...")

    valuation_csv = project_root / "data" / "sample_valuation_analysis.csv"
    if not import_sample_valuation_analysis(db_path, valuation_csv):
        safe_print("⚠️  估值分析資料匯入失敗，繼續匯入其他資料...")

    thesis_csv = project_root / "data" / "sample_investment_thesis.csv"
    if not import_sample_investment_thesis(db_path, thesis_csv):
        safe_print("⚠️  投資邏輯資料匯入失敗，繼續匯入其他資料...")

    risk_csv = project_root / "data" / "sample_risk_analysis.csv"
    if not import_sample_risk_analysis(db_path, risk_csv):
        safe_print("⚠️  風險分析資料匯入失敗，繼續匯入其他資料...")
    safe_print("✅ V1.1 樣本資料匯入完成！")
    return True


if __name__ == "__main__":
    safe_print("=" * 60)
    safe_print("股票追蹤與決策輔助系統 V1.1 - 資料庫擴展")
    safe_print("=" * 60)

    # 擴展資料庫 schema
    if not extend_database():
        safe_print("❌ 資料庫擴展失敗")
        sys.exit(1)

    # 匯入樣本資料
    if not import_v1_1_sample_data():
        safe_print("⚠️  部分樣本資料匯入失敗")

    safe_print("\n" + "=" * 60)
    safe_print("V1.1 資料庫擴展完成！")
    safe_print("=" * 60)