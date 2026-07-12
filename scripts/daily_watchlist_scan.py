#!/usr/bin/env python3
"""
自選股每日掃描腳本
Daily Watchlist Scanner

掃描所有自選股，檢測異常條件，生成警報摘要。
供 Hermes cron job 使用。

用法：
  python scripts/daily_watchlist_scan.py              # 掃描全部自選股
  python scripts/daily_watchlist_scan.py 2330 NVDA    # 掃描指定股票
  python scripts/daily_watchlist_scan.py --full       # 完整分析（更慢）
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix numpy path conflict
_venv_sp = str(project_root / "venv" / "Lib" / "site-packages")
if _venv_sp in sys.path:
    sys.path.remove(_venv_sp)
    sys.path.insert(1, _venv_sp)

import yfinance as yf


def detect_market(symbol):
    symbol = symbol.strip().upper()
    if symbol.endswith(".TW") or symbol.isdigit():
        yf_sym = symbol if symbol.endswith(".TW") else f"{symbol}.TW"
        return yf_sym, "TWSE"
    return symbol, "US"


def quick_scan(symbol):
    """快速掃描單一股票，僅抓關鍵數據"""
    yf_sym, market = detect_market(symbol)
    
    try:
        ticker = yf.Ticker(yf_sym)
        info = ticker.info or {}
        hist = ticker.history(period="1mo", interval="1d")
        
        if hist.empty:
            return {"symbol": symbol, "error": "No data"}
        
        close = hist["Close"]
        current = float(close.iloc[-1])
        
        # Calculate RSI quickly
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1]) if len(close) >= 14 else None
        
        # Key metrics
        result = {
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "market": market,
            "price": current,
            "change_1d": round((close.iloc[-1] / close.iloc[-2] - 1) * 100, 2) if len(close) >= 2 else 0,
            "change_5d": round((close.iloc[-1] / close.iloc[-6] - 1) * 100, 2) if len(close) >= 6 else 0,
            "pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "roe": info.get("returnOnEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "analyst_target": info.get("targetMeanPrice"),
            "analyst_rating": info.get("recommendationKey", ""),
            "rsi": round(rsi, 1) if rsi else None,
            "market_cap": info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
        }
        
        # Calculate upside to analyst target
        if result["analyst_target"] and current:
            result["upside_pct"] = round((result["analyst_target"] / current - 1) * 100, 1)
        
        return result
        
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def detect_alerts(stock_data):
    """檢測異常條件"""
    alerts = []
    
    if "error" in stock_data:
        return [f"❌ {stock_data['symbol']}: {stock_data['error']}"]
    
    name = stock_data.get("name", stock_data["symbol"])
    sym = stock_data["symbol"]
    
    # RSI extremes
    rsi = stock_data.get("rsi")
    if rsi:
        if rsi > 75:
            alerts.append(f"🔴 {sym} RSI {rsi} 超買警報")
        elif rsi < 25:
            alerts.append(f"🟢 {sym} RSI {rsi} 超賣機會")
    
    # Big price moves
    change_1d = stock_data.get("change_1d", 0)
    if abs(change_1d) > 3:
        direction = "暴漲" if change_1d > 0 else "暴跌"
        alerts.append(f"{'🔴' if change_1d < 0 else '🟢'} {sym} {direction} {change_1d:+.1f}%")
    
    change_5d = stock_data.get("change_5d", 0)
    if abs(change_5d) > 7:
        direction = "大漲" if change_5d > 0 else "大跌"
        alerts.append(f"⚠️ {sym} 一週{direction} {change_5d:+.1f}%")
    
    # Valuation alerts
    pe = stock_data.get("pe")
    fwd_pe = stock_data.get("forward_pe")
    if pe and fwd_pe:
        if pe > 50 and fwd_pe > 30:
            alerts.append(f"⚠️ {sym} 本益比偏高 (TTM: {pe:.1f}, Forward: {fwd_pe:.1f})")
    
    # Analyst upside
    upside = stock_data.get("upside_pct")
    if upside is not None:
        if upside > 20:
            alerts.append(f"📈 {sym} 分析師目標價上漲空間 {upside:+.1f}%")
        elif upside < -15:
            alerts.append(f"📉 {sym} 分析師目標價已高於現價 {upside:+.1f}%")
    
    return alerts


def format_quick_report(results, alerts):
    """格式化快速報告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [f"📊 自選股掃描報告 ({now})", ""]
    
    # Summary table
    lines.append("| 股票 | 價格 | 日漲跌 | 週漲跌 | RSI | PE | 分析師目標 |")
    lines.append("|------|------|--------|--------|-----|-----|-----------|")
    
    for r in results:
        if "error" in r:
            lines.append(f"| {r['symbol']} | ❌ 數據錯誤 | - | - | - | - | - |")
            continue
        
        pe_str = f"{r['pe']:.1f}" if r.get('pe') else "-"
        rsi_str = f"{r['rsi']:.0f}" if r.get('rsi') else "-"
        target_str = f"{r['analyst_target']:.0f}" if r.get('analyst_target') else "-"
        upside_str = f"({r['upside_pct']:+.0f}%)" if r.get('upside_pct') is not None else ""
        
        lines.append(
            f"| {r['symbol']} | {r['price']:.1f} | "
            f"{r['change_1d']:+.1f}% | {r['change_5d']:+.1f}% | "
            f"{rsi_str} | {pe_str} | {target_str} {upside_str} |"
        )
    
    # Alerts
    if alerts:
        lines.append("")
        lines.append("🚨 警報")
        for alert in alerts:
            lines.append(f"  {alert}")
    else:
        lines.append("")
        lines.append("✅ 無異常警報")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="自選股每日掃描")
    parser.add_argument("symbols", nargs="*", help="股票代號")
    parser.add_argument("--full", action="store_true", help="完整分析")
    args = parser.parse_args()
    
    # Get symbols
    if args.symbols:
        symbols = args.symbols
    else:
        try:
            from modules.database import get_enabled_stocks
            stocks = get_enabled_stocks()
            symbols = [s["stock_id"] for s in stocks]
        except Exception:
            symbols = ["2330", "2317", "2454", "2308", "2303", "2881"]
    
    print(f"掃描 {len(symbols)} 檔股票...")
    
    results = []
    all_alerts = []
    
    for i, sym in enumerate(symbols):
        print(f"  [{i+1}/{len(symbols)}] {sym}...")
        data = quick_scan(sym)
        results.append(data)
        alerts = detect_alerts(data)
        all_alerts.extend(alerts)
        if i < len(symbols) - 1:
            time.sleep(0.5)
    
    report = format_quick_report(results, all_alerts)
    print("\n" + report)
    
    # Save report
    out_path = project_root / "data" / f"scan_{datetime.now().strftime('%Y%m%d')}.txt"
    out_path.write_text(report, encoding="utf-8")
    print(f"\n📁 已儲存至 {out_path}")


if __name__ == "__main__":
    main()
