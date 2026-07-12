"""
股票追蹤與決策輔助系統 V1 - 閾值警報腳本
Stock Tracking & Decision Support System V1 - Threshold Alert Script

Checks four threshold conditions and sends a consolidated Telegram alert:
  1. VIX > 25  (macro_indicators)
  2. Analyst target_price decreased >10% vs previous_target  (analyst_views)
  3. RSI > 70 or RSI < 30  (indicators, latest per stock)
  4. 3+ consecutive days of net selling  (institutional_flows)

Skips silently if Telegram is not configured.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.database import get_connection, get_enabled_stocks
from modules.alerts import TelegramAlert


# ---------------------------------------------------------------------------
# Threshold queries
# ---------------------------------------------------------------------------

def check_vix_high(conn) -> list:
    """1) VIX > 25 from macro_indicators (latest value)."""
    rows = conn.execute(
        """
        SELECT indicator_date, value
        FROM macro_indicators
        WHERE indicator_name = 'VIX'
        ORDER BY indicator_date DESC
        LIMIT 1
        """
    ).fetchall()
    alerts = []
    for date, value in rows:
        if value is not None and value > 25:
            alerts.append(f"🔴 VIX = {value:.2f}（{date}）> 25，市場恐慌情緒偏高")
    return alerts


def check_analyst_downgrade(conn) -> list:
    """2) analyst_views where target_price decreased >10% from previous_target."""
    rows = conn.execute(
        """
        SELECT s.name, av.analyst_firm, av.target_price, av.previous_target,
               av.report_date
        FROM analyst_views av
        JOIN stocks s ON s.stock_id = av.stock_id
        WHERE av.target_price IS NOT NULL
          AND av.previous_target IS NOT NULL
          AND av.previous_target > 0
          AND av.target_price < av.previous_target
          AND (av.previous_target - av.target_price) / av.previous_target > 0.10
        ORDER BY (av.previous_target - av.target_price) / av.previous_target DESC
        """
    ).fetchall()
    alerts = []
    for name, firm, tp, pt, date in rows:
        drop_pct = (pt - tp) / pt * 100
        alerts.append(
            f"📉 {name}（{firm}）目標價 {pt} → {tp}，下調 {drop_pct:.1f}%（{date}）"
        )
    return alerts


def check_rsi_extreme(conn) -> list:
    """3) Latest RSI > 70 or RSI < 30 for each enabled stock."""
    rows = conn.execute(
        """
        SELECT s.stock_id, s.name, i.rsi, i.date
        FROM stocks s
        JOIN indicators i ON i.stock_id = s.stock_id
        WHERE s.enabled = 1
          AND i.date = (
              SELECT MAX(date) FROM indicators WHERE stock_id = s.stock_id
          )
          AND (i.rsi > 70 OR i.rsi < 30)
        ORDER BY i.rsi DESC
        """
    ).fetchall()
    alerts = []
    for sid, name, rsi, date in rows:
        if rsi > 70:
            alerts.append(f"📈 {name}（{sid}）RSI = {rsi:.1f} > 70，超買（{date}）")
        else:
            alerts.append(f"📉 {name}（{sid}）RSI = {rsi:.1f} < 30，超賣（{date}）")
    return alerts


def check_consecutive_net_selling(conn) -> list:
    """4) 3+ consecutive trading days of net selling for any investor type.

    Uses a window-function approach: for each (stock_id, investor_type, date)
    row where net < 0, compute a streak by subtracting a row_number from the
    date so that consecutive days share the same group key. Then keep groups
    with count >= 3.
    """
    rows = conn.execute(
        """
        WITH neg AS (
            SELECT stock_id, investor_type, date, net
            FROM institutional_flows
            WHERE net < 0
        ),
        streaks AS (
            SELECT stock_id, investor_type, date, net,
                   date(date, '-' || ROW_NUMBER() OVER (
                       PARTITION BY stock_id, investor_type ORDER BY date
                   ) || ' days') AS grp
            FROM neg
        ),
        long_streaks AS (
            SELECT stock_id, investor_type, MIN(date) AS start_date,
                   MAX(date) AS end_date, COUNT(*) AS days,
                   SUM(net) AS total_net
            FROM streaks
            GROUP BY stock_id, investor_type, grp
            HAVING COUNT(*) >= 3
        )
        SELECT s.name, ls.investor_type, ls.start_date, ls.end_date,
               ls.days, ls.total_net
        FROM long_streaks ls
        JOIN stocks s ON s.stock_id = ls.stock_id
        WHERE s.enabled = 1
        ORDER BY ls.days DESC
        """
    ).fetchall()
    alerts = []
    for name, inv_type, start, end, days, total in rows:
        alerts.append(
            f"🔻 {name} 連續 {days} 日淨賣出（{inv_type}）"
            f"  {start}~{end}，累計 {total:,}"
        )
    return alerts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_threshold_alerts():
    """Run all threshold checks and send a consolidated Telegram alert."""
    alert = TelegramAlert()

    # Skip silently if Telegram not configured
    if not alert.enabled:
        return

    conn = get_connection()
    try:
        all_alerts: list[str] = []

        vix = check_vix_high(conn)
        if vix:
            all_alerts.append("🏦 *VIX 恐慌指數*")
            all_alerts.extend(vix)

        analyst = check_analyst_downgrade(conn)
        if analyst:
            all_alerts.append("\n📊 *投行大幅調降目標價*")
            all_alerts.extend(analyst)

        rsi = check_rsi_extreme(conn)
        if rsi:
            all_alerts.append("\n📉 *RSI 極端值*")
            all_alerts.extend(rsi)

        selling = check_consecutive_net_selling(conn)
        if selling:
            all_alerts.append("\n💰 *連續賣超警報*")
            all_alerts.extend(selling)
    finally:
        conn.close()

    if not all_alerts:
        return  # nothing triggered – stay silent

    now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"🚨 *閾值警報 — {now}*\n"
    body = "\n".join(all_alerts)
    message = header + "\n" + body

    alert.send_message(message)


if __name__ == "__main__":
    run_threshold_alerts()
