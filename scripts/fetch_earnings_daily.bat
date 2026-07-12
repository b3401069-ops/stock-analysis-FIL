@echo off
rem ============================================================
rem Daily market data fetch for stock-analysis-FIL
rem Called by Windows Task Scheduler (Mon-Fri 18:00)
rem
rem Fetches:
rem   - US/TW market indices (S&P 500, NASDAQ, VIX, TAIEX, yields)
rem   - Earnings call news (鉅亨網)
rem   - Analyst views (鉅亨網)
rem ============================================================

cd /d "%~dp0.."

if not exist logs mkdir logs

set PY=python
if exist "venv\Scripts\python.exe" set PY=venv\Scripts\python.exe

echo [%date% %time%] market data fetch start >> logs\fetch_earnings.log
"%PY%" scripts\fetch_earnings_analyst.py >> logs\fetch_earnings.log 2>&1
echo [%date% %time%] market data fetch end (exit %errorlevel%) >> logs\fetch_earnings.log
