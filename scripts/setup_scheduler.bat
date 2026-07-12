@echo off
rem ============================================================
rem Register the daily update task in Windows Task Scheduler
rem Run this file ONCE (double-click or from cmd).
rem
rem Schedule: Mon-Fri 21:00
rem   FinMind data availability: price ~17:30, adjusted price 17:30,
rem   institutional investors 20:00 -> 21:00 covers everything.
rem
rem To remove the task later:
rem   schtasks /Delete /TN "StockAnalysis-DailyUpdate" /F
rem To change the time, edit /ST below and re-run this file.
rem ============================================================

schtasks /Create ^
  /TN "StockAnalysis-DailyUpdate" ^
  /TR "\"%~dp0daily_update.bat\"" ^
  /SC WEEKLY ^
  /D MON,TUE,WED,THU,FRI ^
  /ST 21:00 ^
  /F

if %errorlevel%==0 (
    echo.
    echo OK: task "StockAnalysis-DailyUpdate" registered, Mon-Fri 21:00.
    echo Log file: logs\update_data.log
) else (
    echo.
    echo FAILED. Try running this file as Administrator.
)
pause
