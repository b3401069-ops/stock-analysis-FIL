@echo off
rem ============================================================
rem Daily data update for stock-analysis-FIL
rem Called by Windows Task Scheduler (see setup_scheduler.bat)
rem ============================================================

rem Change to project root (this script lives in scripts\)
cd /d "%~dp0.."

if not exist logs mkdir logs

rem Use venv python if available, otherwise system python
set PY=python
if exist "venv\Scripts\python.exe" set PY=venv\Scripts\python.exe

echo [%date% %time%] daily update start >> logs\update_data.log
"%PY%" scripts\update_data.py >> logs\update_data.log 2>&1
echo [%date% %time%] daily update end (exit %errorlevel%) >> logs\update_data.log

rem Send Telegram daily summary (skips itself if TELEGRAM_* not set in .env)
"%PY%" scripts\send_daily_alerts.py >> logs\update_data.log 2>&1
echo [%date% %time%] telegram alert end (exit %errorlevel%) >> logs\update_data.log
