#!/usr/bin/env python3
"""
進階分析模組 v2.0
Advanced Analysis Modules

參考 GitHub 上 30+ 個最佳 repo 後新增的 6 大分析維度：
  1. DCF 折現現金流估值 (參考: stock-analyst/VYNN, tech-earnings-deepdive)
  2. 新聞情緒分析 (參考: ProsusAI/finBERT, go-stock)
  3. 法說會語調分析 (參考: AlphaAnalyst, Earnings_Call_Analyzed_By_NLP)
  4. 反偏誤 / 多角度對抗框架 (參考: ai-berkshire, stock-analysis-team)
  5. 護城河量化評分 (參考: seesaw-mfses MFSES, Moat, claude-buffett-analyst)
  6. SEC 10-K/10-Q 解析 (參考: dartlab, FReader, edgar_analytics)

用法：
  python scripts/advanced_analysis.py 2330           # 完整進階分析
  python scripts/advanced_analysis.py NVDA --dcf-only # 僅 DCF
  python scripts/advanced_analysis.py 2330 --moat-only # 僅護城河評分
"""

import sys
import json
import re
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix numpy path conflict
_venv_sp = str(project_root / "venv" / "Lib" / "site-packages")
if _venv_sp in sys.path:
    sys.path.remove(_venv_sp)
    sys.path.insert(1, _venv_sp)

import yfinance as yf


# ============================================================
# 1. DCF 折現現金流估值模型
# 參考: stock-analyst/VYNN (10-tab Excel DCF)
# 參考: tech-earnings-deepdive (6 種估值法交叉驗證)
# 參考: EmanueleSturzo/DCF-Valuation-Model (Monte Carlo)
# ============================================================

def dcf_valuation(yf_symbol: str) -> Dict[str, Any]:
    """
    DCF 折現現金流估值
    
    方法論：
    1. 從財報提取 FCF (自由現金流)
    2. 預測未來 5 年 FCF 增長率
    3. 計算終值 (Terminal Value)
    4. 折現回今天得出內在價值
    5. 敏感度分析 (WACC vs 永續增長率)
    """
    result = {
        "method": "DCF (Discounted Cash Flow)",
        "inputs": {},
        "projections": [],
        "valuation": {},
        "sensitivity": [],
        "other_methods": {},
        "conclusion": {},
    }
    
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info or {}
        
        # === Step 1: Extract historical FCF ===
        cashflow = ticker.quarterly_cashflow
        if cashflow is None or cashflow.empty:
            return {"error": "No cashflow data available"}
        
        # Get annual FCF
        annual_cf = ticker.cashflow
        fcf_history = []
        if annual_cf is not None and not annual_cf.empty:
            for col in annual_cf.columns:
                operating = annual_cf.loc["Operating Cash Flow", col] if "Operating Cash Flow" in annual_cf.index else None
                capex = annual_cf.loc["Capital Expenditure", col] if "Capital Expenditure" in annual_cf.index else None
                if operating is not None and capex is not None:
                    fcf = float(operating) + float(capex)  # capex is negative
                    fcf_history.append({
                        "year": str(col.date()),
                        "operating_cf": float(operating),
                        "capex": float(capex),
                        "fcf": fcf,
                    })
        
        if len(fcf_history) < 2:
            # Fallback: use info data
            fcf_latest = info.get("freeCashflow", 0)
            if not fcf_latest:
                return {"error": "Insufficient FCF data"}
            fcf_history = [{"year": "latest", "fcf": fcf_latest}]
        
        # === Step 2: Calculate historical FCF growth rate ===
        fcfs = [h["fcf"] for h in fcf_history if h["fcf"] > 0]
        if len(fcfs) >= 2:
            # CAGR
            fcf_growth_hist = (fcfs[0] / fcfs[-1]) ** (1 / (len(fcfs) - 1)) - 1
        else:
            # Use revenue growth as proxy
            fcf_growth_hist = info.get("revenueGrowth", 0.10) or 0.10
        
        # Cap growth rate
        fcf_growth_hist = max(-0.20, min(0.50, fcf_growth_hist))
        
        latest_fcf = fcfs[0] if fcfs else info.get("freeCashflow", 0)
        
        # === Step 3: DCF Parameters ===
        # WACC (Weighted Average Cost of Cost)
        # Simplified: risk-free rate (10Y Treasury) + equity risk premium * beta
        risk_free = 0.045  # ~4.5% (10Y Treasury)
        equity_premium = 0.055  # ~5.5%
        beta = info.get("beta", 1.0) or 1.0
        wacc = risk_free + beta * equity_premium
        
        # Terminal growth rate (long-term GDP growth)
        terminal_growth = 0.025  # 2.5%
        
        # Projection period
        projection_years = 5
        
        # Growth rate for projection (decay from historical to terminal)
        revenue_growth = info.get("revenueGrowth", 0.10) or 0.10
        
        result["inputs"] = {
            "latest_fcf": round(latest_fcf / 1e9, 2) if latest_fcf else 0,
            "fcf_unit": "B",
            "currency": info.get("currency", "USD"),
            "historical_fcf_growth": round(fcf_growth_hist * 100, 1),
            "revenue_growth": round(revenue_growth * 100, 1),
            "wacc": round(wacc * 100, 1),
            "terminal_growth": round(terminal_growth * 100, 1),
            "beta": round(beta, 2),
            "risk_free_rate": round(risk_free * 100, 1),
            "equity_premium": round(equity_premium * 100, 1),
            "shares_outstanding_B": round(info.get("sharesOutstanding", 0) / 1e9, 2),
        }
        
        # === Step 4: Project future FCF ===
        # Growth decays linearly from revenue_growth to terminal_growth over 5 years
        projections = []
        projected_fcf = latest_fcf
        
        for year in range(1, projection_years + 1):
            # Growth rate decays
            year_growth = revenue_growth - (revenue_growth - terminal_growth) * (year / (projection_years + 1))
            projected_fcf = projected_fcf * (1 + year_growth)
            pv = projected_fcf / ((1 + wacc) ** year)
            projections.append({
                "year": year,
                "growth_rate": round(year_growth * 100, 1),
                "fcf": round(projected_fcf / 1e9, 2),
                "pv": round(pv / 1e9, 2),
            })
        
        result["projections"] = projections
        
        # === Step 5: Terminal Value ===
        terminal_fcf = projected_fcf * (1 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        pv_terminal = terminal_value / ((1 + wacc) ** projection_years)
        
        # === Step 6: Enterprise Value ===
        pv_fcf = sum(p["pv"] for p in projections)
        enterprise_value = pv_fcf + pv_terminal / 1e9
        
        # Net debt
        total_debt = info.get("totalDebt", 0) or 0
        total_cash = info.get("totalCash", 0) or 0
        net_debt = total_debt - total_cash
        
        # Equity value
        equity_value = enterprise_value * 1e9 - net_debt
        shares = info.get("sharesOutstanding", 1) or 1
        intrinsic_per_share = equity_value / shares
        
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0)) or 0
        
        result["valuation"] = {
            "pv_fcf_B": round(pv_fcf, 2),
            "pv_terminal_B": round(pv_terminal / 1e9, 2),
            "enterprise_value_B": round(enterprise_value, 2),
            "net_debt_B": round(net_debt / 1e9, 2),
            "equity_value_B": round(equity_value / 1e9, 2),
            "intrinsic_value_per_share": round(intrinsic_per_share, 2),
            "current_price": current_price,
            "upside_pct": round((intrinsic_per_share / current_price - 1) * 100, 1) if current_price > 0 else None,
        }
        
        # === Step 7: Sensitivity Analysis ===
        # Vary WACC and terminal growth
        wacc_range = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]
        tg_range = [0.015, 0.02, 0.025, 0.03, 0.035]
        
        sensitivity = []
        for w in wacc_range:
            row = {"wacc": round(w * 100, 1)}
            for tg in tg_range:
                if w <= tg:
                    row[f"tg_{tg*100:.1f}%"] = "N/A"
                    continue
                tv = terminal_fcf / (w - tg)
                pv_tv = tv / ((1 + w) ** projection_years)
                # Recalculate PV of FCFs with this WACC
                pv_fcf_adj = sum(
                    p["fcf"] * 1e9 / ((1 + w) ** p["year"])
                    for p in projections
                )
                ev = (pv_fcf_adj + pv_tv) / 1e9
                eq = ev * 1e9 - net_debt
                iv = eq / shares
                row[f"tg_{tg*100:.1f}%"] = round(iv, 0)
            sensitivity.append(row)
        
        result["sensitivity"] = sensitivity
        
        # === Step 8: Other Valuation Methods ===
        # Method 2: Earnings Power Value (EPV)
        net_income = info.get("netIncomeToCommon", 0) or 0
        if net_income > 0 and wacc > 0:
            epv = net_income / wacc
            epv_per_share = epv / shares
            result["other_methods"]["EPV"] = {
                "value_per_share": round(epv_per_share, 2),
                "description": "Earnings Power Value (穩定盈利折現)",
            }
        
        # Method 3: Graham Number
        eps = info.get("trailingEps", 0) or 0
        bvps = info.get("bookValue", 0) or 0
        if eps > 0 and bvps > 0:
            graham = math.sqrt(22.5 * eps * bvps)
            result["other_methods"]["Graham"] = {
                "value_per_share": round(graham, 2),
                "description": "Graham Number (22.5 × EPS × BVPS 的平方根)",
            }
        
        # Method 4: PE-based fair value
        fwd_pe = info.get("forwardPE")
        fwd_eps = info.get("forwardEps")
        if fwd_pe and fwd_eps:
            # Use sector average PE (simplified: 20x for tech, 15x for others)
            sector = info.get("sector", "")
            sector_pe = 25 if "Technology" in sector else 15
            pe_fair = fwd_eps * sector_pe
            result["other_methods"]["PE_FairValue"] = {
                "value_per_share": round(pe_fair, 2),
                "fwd_eps": round(fwd_eps, 2),
                "sector_pe": sector_pe,
                "description": f"Sector PE ({sector_pe}x) × Forward EPS",
            }
        
        # === Conclusion ===
        methods = []
        if result["valuation"].get("intrinsic_value_per_share"):
            methods.append(("DCF", result["valuation"]["intrinsic_value_per_share"]))
        for name, data in result["other_methods"].items():
            methods.append((name, data["value_per_share"]))
        
        if methods:
            avg_value = sum(v for _, v in methods) / len(methods)
            result["conclusion"] = {
                "avg_fair_value": round(avg_value, 2),
                "current_price": current_price,
                "margin_of_safety": round((1 - current_price / avg_value) * 100, 1) if avg_value > 0 else None,
                "methods_used": [m[0] for m in methods],
                "verdict": "低估" if current_price < avg_value * 0.85 else
                          "合理" if current_price < avg_value * 1.15 else
                          "高估",
            }
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================
# 2. 新聞情緒分析
# 參考: ProsusAI/finBERT (金融情緒 NLP)
# 參考: ArvinLovegood/go-stock (AI 情緒分析)
# 使用關鍵詞方法（不依賴大型模型，可在本地運行）
# ============================================================

# 金融情緒關鍵詞字典（中英文）
POSITIVE_KEYWORDS = {
    "en": ["beat", "exceed", "outperform", "upgrade", "bullish", "growth", "profit",
           "surge", "rally", "record high", "strong buy", "positive", "momentum",
           "breakthrough", "innovation", "expansion", "partnership", "win", "gain"],
    "zh": ["上漲", "突破", "利多", "看好", "買進", "成長", "獲利", "創新高",
           "加碼", "目標價上調", "營收成長", "訂單", "擴產", "領先", "市占率提升",
           "供不應求", "強勁", "優於預期", "法說會樂觀", "展望佳"],
}

NEGATIVE_KEYWORDS = {
    "en": ["miss", "downgrade", "bearish", "decline", "loss", "crash", "plunge",
           "sell", "risk", "concern", "warning", "lawsuit", "investigation",
           "bankruptcy", "debt", "recession", "layoff", "cut", "weak", "negative"],
    "zh": ["下跌", "跌破", "利空", "看空", "賣超", "衰退", "虧損", "裁員",
           "目標價下調", "營收下滑", "庫存", "供過於求", "弱勢", "低於預期",
           "法說會保守", "展望不佳", "風險", "關稅", "制裁", "禁令"],
}

def analyze_news_sentiment(news_list: List[Dict]) -> Dict[str, Any]:
    """
    分析新聞列表的情緒
    不依賴外部 NLP 模型，使用關鍵詞匹配 + 加權評分
    """
    if not news_list:
        return {"score": 0, "label": "無數據", "articles": [], "summary": "無新聞數據"}
    
    scored_articles = []
    total_score = 0
    
    for article in news_list:
        title = article.get("title", "")
        content = article.get("content", article.get("summary", ""))
        text = f"{title} {content}".lower()
        
        pos_count = 0
        neg_count = 0
        
        for lang in ["en", "zh"]:
            for kw in POSITIVE_KEYWORDS[lang]:
                if kw in text:
                    pos_count += 1
            for kw in NEGATIVE_KEYWORDS[lang]:
                if kw in text:
                    neg_count += 1
        
        # Score: -1 (very negative) to +1 (very positive)
        total = pos_count + neg_count
        if total > 0:
            score = (pos_count - neg_count) / total
        else:
            score = 0
        
        # Weight by recency (more recent = higher weight)
        date_str = article.get("date", "")
        try:
            if date_str:
                article_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                days_ago = (datetime.now() - article_date).days
                weight = max(0.5, 1.0 - days_ago * 0.05)  # Decay over 20 days
            else:
                weight = 0.5
        except Exception:
            weight = 0.5
        
        weighted_score = score * weight
        total_score += weighted_score
        
        scored_articles.append({
            "title": title[:80],
            "date": date_str,
            "score": round(score, 2),
            "weighted_score": round(weighted_score, 2),
            "pos_hits": pos_count,
            "neg_hits": neg_count,
            "sentiment": "正面" if score > 0.2 else "負面" if score < -0.2 else "中性",
        })
    
    avg_score = total_score / len(news_list) if news_list else 0
    
    # Classify overall sentiment
    if avg_score > 0.3:
        label = "🟢 強烈正面"
    elif avg_score > 0.1:
        label = "🟢 正面"
    elif avg_score > -0.1:
        label = "🟡 中性"
    elif avg_score > -0.3:
        label = "🔴 負面"
    else:
        label = "🔴 強烈負面"
    
    return {
        "score": round(avg_score, 3),
        "label": label,
        "article_count": len(news_list),
        "positive_articles": len([a for a in scored_articles if a["score"] > 0.2]),
        "negative_articles": len([a for a in scored_articles if a["score"] < -0.2]),
        "neutral_articles": len([a for a in scored_articles if -0.2 <= a["score"] <= 0.2]),
        "articles": sorted(scored_articles, key=lambda x: x["weighted_score"]),
        "summary": f"分析 {len(news_list)} 篇新聞，情緒分數 {avg_score:.2f} ({label})",
    }


# ============================================================
# 3. 法說會語調分析
# 參考: AlphaAnalyst (earnings call tone analysis)
# 參考: Earnings_Call_Analyzed_By_NLP
# ============================================================

# 管理層語氣指標詞彙
GUIDANCE_POSITIVE = ["raise", "increase", "above", "exceed", "strong", "confident",
                      "optimistic", "accelerate", "upside", "opportunity", "leadership",
                      "上調", "看好", "樂觀", "成長", "領先", "擴張", "機會", "信心"]
GUIDANCE_NEGATIVE = ["lower", "reduce", "below", "miss", "weak", "cautious",
                      "uncertain", "headwind", "challenge", "risk", "pressure",
                      "下調", "保守", "謹慎", "挑戰", "壓力", "風險", "不確定"]

def analyze_earnings_call_tone(earnings_data: List[Dict]) -> Dict[str, Any]:
    """
    分析法說會紀錄的語調
    """
    if not earnings_data:
        return {"tone": "無數據", "score": 0, "details": []}
    
    results = []
    total_score = 0
    
    for call in earnings_data:
        text = ""
        for field in ["key_highlights", "management_guidance", "outlook_summary",
                       "transcript_summary", "content"]:
            val = call.get(field, "")
            if val:
                text += f" {val}"
        
        text = text.lower()
        
        pos = sum(1 for kw in GUIDANCE_POSITIVE if kw in text)
        neg = sum(1 for kw in GUIDANCE_NEGATIVE if kw in text)
        
        total = pos + neg
        score = (pos - neg) / total if total > 0 else 0
        
        results.append({
            "date": call.get("call_date", call.get("date", "")),
            "quarter": call.get("quarter", ""),
            "positive_signals": pos,
            "negative_signals": neg,
            "tone_score": round(score, 2),
            "tone": "鷹派/樂觀" if score > 0.2 else "鴿派/保守" if score < -0.2 else "中性",
            "title": call.get("title", "")[:60],
        })
        
        total_score += score
    
    avg_score = total_score / len(results) if results else 0
    
    return {
        "tone": "管理層語氣偏樂觀" if avg_score > 0.15 else
                "管理層語氣偏保守" if avg_score < -0.15 else
                "管理層語氣中性",
        "score": round(avg_score, 3),
        "call_count": len(results),
        "details": results,
        "trend": "語氣轉趨樂觀" if len(results) >= 2 and results[0]["tone_score"] > results[-1]["tone_score"] else
                 "語氣轉趨保守" if len(results) >= 2 and results[0]["tone_score"] < results[-1]["tone_score"] else
                 "語氣穩定",
    }


# ============================================================
# 4. 反偏誤 / 多角度對抗框架
# 參考: ai-berkshire (4 master perspectives)
# 參考: stock-analysis-team (bull/bear debate)
# 參考: tech-earnings-deepdive (cognitive trap detection)
# ============================================================

def generate_anti_bias_framework(data: Dict) -> Dict[str, Any]:
    """
    生成反偏誤分析框架
    
    產生：
    1. 牛方論點 (Bull Case) — 為什麼應該買
    2. 熊方論點 (Bear Case) — 為什麼不應該買
    3. 認知陷阱檢測 — 常見的投資偏誤
    4. Pre-Mortem 分析 — 如果投資失敗，最可能的原因是什麼
    """
    fundamental = data.get("fundamental", {})
    technical = data.get("technical", {})
    valuation = fundamental.get("valuation", {})
    profitability = fundamental.get("profitability", {})
    growth = fundamental.get("growth", {})
    health = fundamental.get("financial_health", {})
    analyst = fundamental.get("analyst_ratings", {})
    
    # === Bull Case ===
    bull_points = []
    
    rev_growth = growth.get("revenue_growth")
    if rev_growth and rev_growth > 0.15:
        bull_points.append(f"營收高速增長 ({rev_growth*100:.0f}%)，成長動能強勁")
    
    roe = profitability.get("roe")
    if roe and roe > 0.20:
        bull_points.append(f"ROE 高達 {roe*100:.0f}%，資本回報優異")
    
    gross_margin = profitability.get("gross_margin")
    if gross_margin and gross_margin > 0.40:
        bull_points.append(f"毛利率 {gross_margin*100:.0f}%，具有定價權和護城河")
    
    pe_fwd = valuation.get("pe_forward")
    pe_trail = valuation.get("pe_trailing")
    if pe_fwd and pe_trail and pe_fwd < pe_trail * 0.7:
        bull_points.append(f"Forward PE ({pe_fwd:.1f}) 遠低於 Trailing PE ({pe_trail:.1f})，預期盈利大幅成長")
    
    upside = analyst.get("target_mean")
    current = analyst.get("current_price")
    if upside and current and upside > current * 1.1:
        bull_points.append(f"分析師共識目標價 {upside:.0f}，上漲空間 {(upside/current-1)*100:.0f}%")
    
    current_ratio = health.get("current_ratio")
    if current_ratio and current_ratio > 2.0:
        bull_points.append(f"流動比率 {current_ratio:.1f}，財務非常健康")
    
    if not bull_points:
        bull_points.append("無特別利多因素")
    
    # === Bear Case ===
    bear_points = []
    
    if pe_trail and pe_trail > 40:
        bear_points.append(f"本益比 {pe_trail:.1f}x 偏高，估值泡沫風險")
    
    de = health.get("debt_to_equity")
    if de and de > 100:
        bear_points.append(f"負債權益比 {de:.0f}% 偏高，財務槓桿風險")
    
    rsi = technical.get("technical_indicators", {}).get("rsi_14")
    if rsi and rsi > 70:
        bear_points.append(f"RSI {rsi:.0f} 超買，短期回調風險")
    
    price_vs_high = technical.get("price_data", {}).get("price_vs_52w_high_pct")
    if price_vs_high and price_vs_high > -5:
        bear_points.append("股價接近52週高點，追高風險")
    
    if rev_growth and rev_growth < 0:
        bear_points.append(f"營收衰退 ({rev_growth*100:.0f}%)，基本面惡化")
    
    net_margin = profitability.get("net_margin")
    if net_margin and net_margin < 0.05:
        bear_points.append(f"淨利率僅 {net_margin*100:.1f}%，獲利能力薄弱")
    
    institutional = data.get("fundamental", {}).get("ownership", {}).get("institutional_pct")
    if institutional and institutional < 0.20:
        bear_points.append(f"機構持股僅 {institutional*100:.0f}%，缺乏法人支持")
    
    if not bear_points:
        bear_points.append("無特別利空因素")
    
    # === Cognitive Trap Detection ===
    traps = []
    
    # Anchoring: if analyst target is very different from current
    if upside and current:
        gap = abs(upside / current - 1)
        if gap > 0.5:
            traps.append({
                "trap": "錨定效應 (Anchoring)",
                "risk": "分析師目標價與現價差距過大，可能被錨定在不切實際的預期",
                "mitigation": "使用多種估值方法交叉驗證，不依賴單一目標價",
            })
    
    # Confirmation bias: if all signals point same direction
    trend_signals = technical.get("technical_indicators", {}).get("trend_signals", [])
    if len(trend_signals) >= 2 and all("多頭" in s for s in trend_signals):
        traps.append({
            "trap": "確認偏誤 (Confirmation Bias)",
            "risk": "所有技術指標都指向多頭，可能忽略反面證據",
            "mitigation": "主動尋找看空理由，檢視最壞情況",
        })
    
    # Recency bias: if 6m return is very high
    change_6m = technical.get("price_data", {}).get("change_6m_pct")
    if change_6m and change_6m > 50:
        traps.append({
            "trap": "近因偏誤 (Recency Bias)",
            "risk": f"過去6個月漲幅 {change_6m:.0f}%，可能過度外推近期趨勢",
            "mitigation": "回顧歷史，高漲幅後往往面臨回調",
        })
    
    # Herding: if analyst consensus is unanimous
    num_analysts = analyst.get("num_analysts", 0)
    if num_analysts > 20:
        traps.append({
            "trap": "從眾效應 (Herding)",
            "risk": f"{num_analysts} 位分析師覆蓋，共識可能過度一致",
            "mitigation": "參考少數派觀點，獨立思考",
        })
    
    # === Pre-Mortem ===
    pre_mortem = []
    if gross_margin and gross_margin > 0.50:
        pre_mortem.append("如果毛利率無法維持（競爭加劇/成本上升），估值將大幅下修")
    if rev_growth and rev_growth > 0.30:
        pre_mortem.append("如果增長放緩（市場飽和/景氣反轉），高估值將面臨壓力")
    pre_mortem.append("如果全球經濟衰退，所有股票都將受影響")
    pre_mortem.append("如果利率持續上升，成長股估值將被壓縮")
    
    return {
        "bull_case": {
            "points": bull_points,
            "strength": "強" if len(bull_points) >= 4 else "中" if len(bull_points) >= 2 else "弱",
        },
        "bear_case": {
            "points": bear_points,
            "strength": "強" if len(bear_points) >= 4 else "中" if len(bear_points) >= 2 else "弱",
        },
        "cognitive_traps": traps,
        "pre_mortem": pre_mortem,
        "balance": "偏多" if len(bull_points) > len(bear_points) + 1 else
                   "偏空" if len(bear_points) > len(bull_points) + 1 else
                   "中性",
    }


# ============================================================
# 5. 護城河量化評分
# 參考: seesaw-mfses (MFSES: Moat + Fundamentals + Sentiment + Expectations + Safety)
# 參考: ItayShapiro801/Moat (6 investor personas)
# 參考: claude-buffett-analyst (moat/quality/valuation framework)
# ============================================================

def moat_scoring(data: Dict) -> Dict[str, Any]:
    """
    護城河量化評分系統
    
    評估 5 大護城河維度，每項 1-10 分：
    1. 無形資產 (品牌、專利、牌照)
    2. 成本優勢 (規模經濟、學習曲線)
    3. 轉換成本 (客戶鎖定)
    4. 網絡效應 (平台效應)
    5. 有效規模 (市場壁壘)
    
    加上 5 個輔助維度：
    6. 獲利穩定性 (ROE/margin 波動)
    7. 現金流品質
    8. 資本報酬率 (ROIC)
    9. 行業地位
    10. 管理層品質
    """
    fundamental = data.get("fundamental", {})
    profitability = fundamental.get("profitability", {})
    health = fundamental.get("financial_health", {})
    valuation = fundamental.get("valuation", {})
    growth = fundamental.get("growth", {})
    ownership = fundamental.get("ownership", {})
    info = fundamental.get("company_info", {})
    
    scores = {}
    
    # 1. 無形資產 (proxy: gross margin — high margin = pricing power = brand/tech moat)
    gm = profitability.get("gross_margin", 0) or 0
    scores["無形資產"] = {
        "score": min(10, max(1, int(gm * 13))),  # 50% margin → 6.5 → 7
        "reasoning": f"毛利率 {gm*100:.1f}% — " + (
            "極高，具有強大定價權" if gm > 0.50 else
            "高，具有品牌/技術優勢" if gm > 0.35 else
            "中等，競爭激烈" if gm > 0.20 else
            "低，高度競爭行業"
        ),
    }
    
    # 2. 成本優勢 (proxy: operating margin — efficiency)
    om = profitability.get("operating_margin", 0) or 0
    scores["成本優勢"] = {
        "score": min(10, max(1, int(om * 15))),
        "reasoning": f"營業利益率 {om*100:.1f}% — " + (
            "卓越的成本控制能力" if om > 0.30 else
            "良好的營運效率" if om > 0.15 else
            "中等效率" if om > 0.08 else
            "效率偏低"
        ),
    }
    
    # 3. 轉換成本 (proxy: revenue consistency + customer retention)
    rev_growth = growth.get("revenue_growth", 0) or 0
    scores["轉換成本"] = {
        "score": min(10, max(1, 5 + int(rev_growth * 15))),
        "reasoning": f"營收增長 {rev_growth*100:.1f}% — " + (
            "客戶高度依賴，轉換成本高" if rev_growth > 0.15 else
            "有一定客戶黏性" if rev_growth > 0.05 else
            "客戶黏性待觀察"
        ),
    }
    
    # 4. 網絡效應 (proxy: market cap scale — larger = more network effects)
    mcap = valuation.get("market_cap", 0) or 0
    if mcap > 5e12:  # > 5T TWD / ~150B USD
        network_score = 9
    elif mcap > 1e12:
        network_score = 7
    elif mcap > 1e11:
        network_score = 5
    else:
        network_score = 3
    scores["網絡效應"] = {
        "score": network_score,
        "reasoning": f"市值 {mcap/1e12:.1f}T — " + (
            "大型平台企業，生態系統效應強" if network_score >= 7 else
            "中型企業，有一定生態影響力" if network_score >= 5 else
            "小型企業，網絡效應有限"
        ),
    }
    
    # 5. 有效規模 (proxy: industry barriers — ROE consistency)
    roe = profitability.get("roe", 0) or 0
    scores["有效規模"] = {
        "score": min(10, max(1, int(roe * 25))),
        "reasoning": f"ROE {roe*100:.1f}% — " + (
            "資本報酬極高，進入壁壘高" if roe > 0.25 else
            "報酬良好，有一定壁壘" if roe > 0.15 else
            "報酬一般" if roe > 0.08 else
            "報酬偏低，壁壘低"
        ),
    }
    
    # 6. 獲利穩定性 (proxy: margin consistency)
    nm = profitability.get("net_margin", 0) or 0
    scores["獲利穩定性"] = {
        "score": min(10, max(1, int(nm * 18))),
        "reasoning": f"淨利率 {nm*100:.1f}%",
    }
    
    # 7. 現金流品質
    fcf = health.get("free_cash_flow", 0) or 0
    revenue = health.get("revenue", 1) or 1
    fcf_yield = fcf / revenue if revenue > 0 else 0
    scores["現金流品質"] = {
        "score": min(10, max(1, int(fcf_yield * 60))),
        "reasoning": f"FCF/營收 {fcf_yield*100:.1f}%",
    }
    
    # 8. 資本報酬率 (ROE as proxy for ROIC)
    scores["資本報酬率"] = {
        "score": min(10, max(1, int(roe * 22))),
        "reasoning": f"ROE {roe*100:.1f}%",
    }
    
    # 9. 行業地位 (proxy: analyst coverage + institutional ownership)
    num_analysts = fundamental.get("analyst_ratings", {}).get("num_analysts", 0) or 0
    inst_pct = ownership.get("institutional_pct", 0) or 0
    scores["行業地位"] = {
        "score": min(10, max(1, 3 + int(num_analysts / 5) + int(inst_pct * 5))),
        "reasoning": f"{num_analysts} 位分析師覆蓋，機構持股 {inst_pct*100:.0f}%",
    }
    
    # 10. 管理層品質 (proxy: insider ownership + earnings quality)
    insider = ownership.get("insider_pct", 0) or 0
    scores["管理層品質"] = {
        "score": min(10, max(1, 5 + int(insider * 100) + int(nm * 8))),
        "reasoning": f"內部人持股 {insider*100:.2f}%",
    }
    
    # === 總分 ===
    core_scores = ["無形資產", "成本優勢", "轉換成本", "網絡效應", "有效規模"]
    support_scores = ["獲利穩定性", "現金流品質", "資本報酬率", "行業地位", "管理層品質"]
    
    core_avg = sum(scores[k]["score"] for k in core_scores) / 5
    support_avg = sum(scores[k]["score"] for k in support_scores) / 5
    total = core_avg * 0.6 + support_avg * 0.4
    
    if total >= 8:
        moat_width = "寬護城河 (Wide Moat) ⭐⭐⭐⭐⭐"
    elif total >= 6:
        moat_width = "窄護城河 (Narrow Moat) ⭐⭐⭐⭐"
    elif total >= 4:
        moat_width = "有限護城河 (Limited Moat) ⭐⭐⭐"
    else:
        moat_width = "無護城河 (No Moat) ⭐⭐"
    
    return {
        "scores": scores,
        "core_moat_avg": round(core_avg, 1),
        "support_avg": round(support_avg, 1),
        "total_score": round(total, 1),
        "moat_width": moat_width,
        "moat_type": ", ".join(
            k for k in core_scores if scores[k]["score"] >= 7
        ) or "待確認",
    }


# ============================================================
# 6. SEC 10-K/10-Q 解析 (美股)
# 參考: dartlab (structured filing data)
# 參考: FReader (10-K textual analysis)
# 參考: edgar_analytics (automated reporting)
# ============================================================

def fetch_sec_filings(symbol: str, filing_type: str = "10-K") -> Dict[str, Any]:
    """
    從 SEC EDGAR 抓取 10-K/10-Q 財報
    
    使用 EDGAR 全文搜尋 API (免費，無需 API key)
    需要設定 User-Agent header (SEC 要求)
    """
    import urllib.request
    
    result = {
        "symbol": symbol,
        "filing_type": filing_type,
        "filings": [],
        "risk_factors": [],
        "mdna_summary": "",
    }
    
    headers = {
        "User-Agent": "StockAnalyzer research@example.com",
        "Accept": "application/json",
    }
    
    # Step 1: Get CIK number
    try:
        # Use company tickers endpoint
        cik_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{symbol}%22&dateRange=custom&startdt=2024-01-01&enddt=2026-12-31&forms={filing_type}"
        
        # Alternative: use the submissions API
        # First try the company search
        search_url = f"https://efts.sec.gov/LATEST/search-index?q={symbol}&forms={filing_type}&dateRange=custom&startdt=2025-01-01&enddt=2026-12-31"
        
        req = urllib.request.Request(search_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                filings = data.get("hits", {}).get("hits", [])
                
                for filing in filings[:5]:
                    source = filing.get("_source", {})
                    result["filings"].append({
                        "file_date": source.get("file_date", ""),
                        "form_type": source.get("form_type", ""),
                        "company": source.get("display_names", [""])[0] if source.get("display_names") else "",
                        "cik": source.get("entity_id", ""),
                    })
        except Exception as e:
            result["search_error"] = str(e)
        
        # Step 2: Try to get filing content from EDGAR full-text search
        risk_url = f"https://efts.sec.gov/LATEST/search-index?q=%22risk+factors%22+%22{symbol}%22&forms={filing_type}"
        try:
            req = urllib.request.Request(risk_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", {}).get("hits", [])
                for hit in hits[:3]:
                    source = hit.get("_source", {})
                    result["risk_factors"].append({
                        "file_date": source.get("file_date", ""),
                        "snippet": hit.get("highlight", {}).get("text", [""])[0][:200] if hit.get("highlight") else "",
                    })
        except Exception:
            pass
        
        if not result["filings"]:
            result["note"] = "SEC EDGAR 全文搜尋需要 CIK 號碼。對於美股，建議使用 yfinance 的 company description 作為替代。"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================
# 整合：完整進階分析
# ============================================================

def run_advanced_analysis(symbol: str, analysis_data: Dict = None) -> Dict[str, Any]:
    """
    運行完整的進階分析
    
    Args:
        symbol: 股票代號
        analysis_data: 已有的分析數據（從 collect_stock_data.py 的輸出）
    """
    # Detect market
    symbol_upper = symbol.strip().upper()
    if symbol_upper.isdigit() or symbol_upper.endswith(".TW"):
        yf_symbol = f"{symbol_upper.replace('.TW', '')}.TW"
        market = "TWSE"
    else:
        yf_symbol = symbol_upper
        market = "US"
    
    print(f"\n{'='*60}")
    print(f"  進階分析: {symbol} ({yf_symbol})")
    print(f"{'='*60}")
    
    result = {
        "symbol": symbol,
        "yf_symbol": yf_symbol,
        "market": market,
        "analyzed_at": datetime.now().isoformat(),
    }
    
    # If no data provided, collect basic data
    if not analysis_data:
        print("  [0/5] 收集基本數據...")
        from scripts.collect_stock_data import collect_all_for_stock
        analysis_data = collect_all_for_stock(symbol, include_news=True)
    
    # 1. DCF Valuation
    print("  [1/5] DCF 折現現金流估值...")
    result["dcf"] = dcf_valuation(yf_symbol)
    
    # 2. News Sentiment
    print("  [2/5] 新聞情緒分析...")
    news = analysis_data.get("news", {}).get("news", [])
    result["news_sentiment"] = analyze_news_sentiment(news)
    
    # 3. Earnings Call Tone
    print("  [3/5] 法說會語調分析...")
    earnings = analysis_data.get("news", {}).get("earnings_calls", [])
    result["earnings_tone"] = analyze_earnings_call_tone(earnings)
    
    # 4. Anti-Bias Framework
    print("  [4/5] 反偏誤分析框架...")
    result["anti_bias"] = generate_anti_bias_framework(analysis_data)
    
    # 5. Moat Scoring
    print("  [5/5] 護城河量化評分...")
    result["moat"] = moat_scoring(analysis_data)
    
    # 6. SEC Filings (US only)
    if market == "US":
        print("  [+] SEC 10-K 解析...")
        result["sec_filings"] = fetch_sec_filings(yf_symbol, "10-K")
        result["sec_filings_10q"] = fetch_sec_filings(yf_symbol, "10-Q")
    
    print(f"\n  ✅ 進階分析完成")
    return result


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="進階分析模組")
    parser.add_argument("symbol", help="股票代號")
    parser.add_argument("--dcf-only", action="store_true", help="僅 DCF 估值")
    parser.add_argument("--moat-only", action="store_true", help="僅護城河評分")
    parser.add_argument("--input", "-i", help="已有分析數據 JSON 路徑")
    parser.add_argument("--output", "-o", help="輸出路徑")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    
    # Load existing data if provided
    existing_data = None
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    
    if args.dcf_only:
        # Detect yf_symbol
        sym = args.symbol.strip().upper()
        yf_sym = f"{sym}.TW" if sym.isdigit() else sym
        data = dcf_valuation(yf_sym)
    elif args.moat_only:
        if not existing_data:
            print("Error: --moat-only requires --input with existing data")
            sys.exit(1)
        data = moat_scoring(existing_data)
    else:
        data = run_advanced_analysis(args.symbol, existing_data)
    
    indent = 2 if args.pretty else None
    json_str = json.dumps(data, ensure_ascii=False, indent=indent, default=str)
    
    if args.output:
        Path(args.output).write_text(json_str, encoding="utf-8")
        print(f"📁 已儲存至 {args.output}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
