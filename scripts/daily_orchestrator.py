#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 - 每日排程協調器
Stock Tracking & Decision Support System - Daily Orchestrator

統一協調每日作業：
  1. 備份 stocks.db → data/backups/stocks_YYYY-MM-DD.db
  2. fetch_earnings_analyst.py  (Yahoo/FRED/鉅亨網)
  3. update_data.py             (FinMind 股價/估值/宏觀/指標/評分/訊號)
  4. send_daily_alerts.py       (Telegram 摘要)

功能：
  - 結構化 JSON 日誌 → logs/orchestrator.jsonl
  - 失敗步驟最多重試 2 次，間隔 30 秒
  - Telegram 摘要通知（需 .env 設定 TELEGRAM_*）

用法：
    python scripts/daily_orchestrator.py                   # 全部步驟
    python scripts/daily_orchestrator.py --step backup     # 僅備份
    python scripts/daily_orchestrator.py --step fetch      # 僅 fetch (Yahoo/FRED/鉅亨網)
    python scripts/daily_orchestrator.py --step update     # 僅 update (FinMind)
    python scripts/daily_orchestrator.py --step notify     # 僅 Telegram 通知
    python scripts/daily_orchestrator.py --step backup --step fetch
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 專案路徑
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.config import get_config
from modules.console import safe_print

# ---------------------------------------------------------------------------
# 常數
# ---------------------------------------------------------------------------
MAX_RETRIES = 2
RETRY_DELAY_SEC = 30
LOG_DIR = PROJECT_ROOT / "logs"
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
LOG_FILE = LOG_DIR / "orchestrator.jsonl"


# ---------------------------------------------------------------------------
# 日誌工具
# ---------------------------------------------------------------------------
def _ensure_dirs():
    """確保 logs/ 和 data/backups/ 目錄存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def log_event(step: str, status: str, message: str, duration_sec: float = 0.0):
    """寫入一行結構化 JSON 日誌（同時輸出到 console）"""
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "step": step,
        "status": status,
        "message": message,
        "duration_sec": round(duration_sec, 1),
    }
    # 寫入 JSONL
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        safe_print(f"  ⚠️  日誌寫入失敗: {e}")

    # Console 輸出
    icon = {"ok": "✅", "fail": "❌", "retry": "🔄", "info": "ℹ️", "skip": "⏭️"}.get(status, "•")
    safe_print(f"  {icon} [{step}] {message}  ({duration_sec:.1f}s)")


# ---------------------------------------------------------------------------
# 步驟實作
# ---------------------------------------------------------------------------
def step_backup() -> bool:
    """備份 stocks.db 到 data/backups/stocks_YYYY-MM-DD.db"""
    config = get_config()
    db_path = Path(config.DATABASE_PATH)

    if not db_path.exists():
        log_event("backup", "fail", f"資料庫不存在: {db_path}")
        return False

    date_str = datetime.now().strftime("%Y-%m-%d")
    dest = BACKUP_DIR / f"stocks_{date_str}.db"

    t0 = time.time()
    try:
        shutil.copy2(str(db_path), str(dest))
        size_mb = dest.stat().st_size / (1024 * 1024)
        log_event("backup", "ok", f"備份完成 → {dest.name} ({size_mb:.1f} MB)", time.time() - t0)
        _prune_old_backups(BACKUP_DIR, keep=30)
        return True
    except Exception as e:
        log_event("backup", "fail", f"備份失敗: {e}", time.time() - t0)
        return False


def _prune_old_backups(backup_dir: Path, keep: int = 30):
    """保留最近 keep 份備份，刪除更早的"""
    backups = sorted(backup_dir.glob("stocks_*.db"), key=lambda p: p.name, reverse=True)
    for old in backups[keep:]:
        try:
            old.unlink()
        except OSError:
            pass


def step_fetch() -> bool:
    """執行 fetch_earnings_analyst.py（Yahoo Finance / FRED / 鉅亨網）"""
    script = PROJECT_ROOT / "scripts" / "fetch_earnings_analyst.py"
    return _run_script("fetch", str(script))


def step_update() -> bool:
    """執行 update_data.py（FinMind 股價/估值/宏觀/重算指標/評分/訊號）"""
    script = PROJECT_ROOT / "scripts" / "update_data.py"
    return _run_script("update", str(script))


def step_notify() -> bool:
    """執行 send_daily_alerts.py（Telegram 每日摘要）"""
    config = get_config()
    if not config.is_telegram_enabled():
        log_event("notify", "skip", "Telegram 未設定（TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID），跳過")
        return True

    script = PROJECT_ROOT / "scripts" / "send_daily_alerts.py"
    return _run_script("notify", str(script))


def _run_script(step_name: str, script_path: str) -> bool:
    """以 subprocess 執行子腳本，回傳成功與否"""
    python = _find_python()
    t0 = time.time()
    try:
        result = subprocess.run(
            [python, script_path],
            capture_output=True,
            text=True,
            timeout=900,  # 15 分鐘逾時
            cwd=str(PROJECT_ROOT),
        )
        duration = time.time() - t0

        if result.returncode == 0:
            log_event(step_name, "ok", "完成", duration)
            return True
        else:
            stderr_tail = (result.stderr or result.stdout or "").strip()[-300:]
            log_event(step_name, "fail", f"exit={result.returncode} {stderr_tail}", duration)
            return False
    except subprocess.TimeoutExpired:
        log_event(step_name, "fail", "逾時（>900s）", time.time() - t0)
        return False
    except Exception as e:
        log_event(step_name, "fail", str(e), time.time() - t0)
        return False


def _find_python() -> str:
    """優先使用 venv python，其次系統 python"""
    venv_py = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


# ---------------------------------------------------------------------------
# 重試封裝
# ---------------------------------------------------------------------------
def run_with_retry(step_name: str, fn) -> bool:
    """執行步驟，失敗時最多重試 MAX_RETRIES 次，間隔 RETRY_DELAY_SEC 秒"""
    for attempt in range(1, MAX_RETRIES + 2):  # 1-indexed: attempt 1 = first try
        if attempt > 1:
            log_event(step_name, "retry", f"第 {attempt - 1} 次重試，等待 {RETRY_DELAY_SEC}s…", 0)
            time.sleep(RETRY_DELAY_SEC)

        ok = fn()
        if ok:
            return True

        if attempt <= MAX_RETRIES:
            log_event(step_name, "info", f"失敗，將重試 ({attempt}/{MAX_RETRIES})", 0)

    log_event(step_name, "fail", f"重試 {MAX_RETRIES} 次後仍失敗", 0)
    return False


# ---------------------------------------------------------------------------
# Telegram 摘要
# ---------------------------------------------------------------------------
def send_orchestrator_summary(steps_summary: dict, total_duration: float):
    """若 Telegram 已設定，傳送協調器摘要"""
    config = get_config()
    if not config.is_telegram_enabled():
        return

    from modules.alerts import TelegramAlert
    alert = TelegramAlert()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    status_icon = "✅" if all(steps_summary.values()) else "⚠️"

    lines = [
        f"{status_icon} *每日資料更新摘要*",
        f"📅 {now}",
        "",
    ]

    step_labels = {
        "backup": "📦 資料庫備份",
        "fetch": "📊 市場資料 (Yahoo/FRED/鉅亨網)",
        "update": "📈 FinMind 更新 + 重算",
        "notify": "🔔 Telegram 通知",
    }

    for step, ok in steps_summary.items():
        icon = "✅" if ok else "❌"
        label = step_labels.get(step, step)
        lines.append(f"{icon} {label}")

    lines.append(f"\n⏱️ 總耗時: {total_duration:.0f}s")
    lines.append("\n_由 daily_orchestrator 自動產生_")

    alert.send_message("\n".join(lines))


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
STEPS_IN_ORDER = ["backup", "fetch", "update", "notify"]

STEP_FUNCS = {
    "backup": step_backup,
    "fetch": step_fetch,
    "update": step_update,
    "notify": step_notify,
}


def parse_args():
    parser = argparse.ArgumentParser(description="每日資料更新協調器")
    parser.add_argument(
        "--step",
        action="append",
        choices=STEPS_IN_ORDER + ["all"],
        default=None,
        help="要執行的步驟（可重複指定多個；預設 all）",
    )
    return parser.parse_args()


def main():
    _ensure_dirs()

    args = parse_args()
    requested = args.step or ["all"]
    if "all" in requested:
        steps_to_run = list(STEPS_IN_ORDER)
    else:
        # 保持定義順序
        steps_to_run = [s for s in STEPS_IN_ORDER if s in requested]

    safe_print("=" * 55)
    safe_print("股票追蹤系統 - 每日協調器 (daily_orchestrator)")
    safe_print(f"  步驟: {', '.join(steps_to_run)}")
    safe_print(f"  時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print("=" * 55)

    log_event("orchestrator", "info", f"啟動 steps={steps_to_run}")

    total_t0 = time.time()
    results: dict[str, bool] = {}

    for step_name in steps_to_run:
        safe_print(f"\n{'─' * 50}")
        safe_print(f"▶ 步驟: {step_name}")
        safe_print(f"{'─' * 50}")

        fn = STEP_FUNCS[step_name]
        ok = run_with_retry(step_name, fn)
        results[step_name] = ok

    total_duration = time.time() - total_t0

    # 匯總
    safe_print(f"\n{'=' * 55}")
    safe_print("📋 執行結果:")
    for step_name, ok in results.items():
        safe_print(f"  {'✅' if ok else '❌'} {step_name}")
    safe_print(f"⏱️  總耗時: {total_duration:.0f}s")
    safe_print("=" * 55)

    log_event("orchestrator", "info",
              f"完成 results={json.dumps(results)}", total_duration)

    # Telegram 摘要
    if "notify" not in steps_to_run:
        # 如果 notify 不在步驟清單中，仍然發送協調器摘要（若已設定）
        send_orchestrator_summary(results, total_duration)

    # 若有任何步驟失敗，回傳非零 exit code
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
