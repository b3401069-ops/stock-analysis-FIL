@echo off
rem ============================================================
rem Register the daily earnings/analyst fetch task
rem Run this file ONCE (double-click or from cmd).
rem
rem Schedule: Mon-Fri 18:00 (after market close)
rem
rem To remove the task later:
rem   schtasks /Delete /TN "StockAnalysis-FetchEarnings" /F
rem To change the time, edit /ST below and re-run this file.
rem ============================================================

schtasks /Create ^
  /TN "StockAnalysis-FetchEarnings" ^
  /TR "\"%~dp0fetch_earnings_daily.bat\"" ^
  /SC WEEKLY ^
  /D MON,TUE,WED,THU,FRI ^
  /ST 18:00 ^
  /F

if %errorlevel%==0 (
    echo.
    echo OK: task "StockAnalysis-FetchEarnings" registered, Mon-Fri 18:00.
    echo Log file: logs\fetch_earnings.log
) else (
    echo.
    echo FAILED. Try running this file as Administrator.
)
pause
