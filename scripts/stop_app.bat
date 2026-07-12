@echo off
rem ============================================================
rem Stop the background Streamlit app (kills the process on port 8501)
rem ============================================================

set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :8501') do (
    taskkill /PID %%p /F >nul 2>&1
    set FOUND=1
)

if %FOUND%==1 (
    echo App stopped.
) else (
    echo App is not running.
)
pause
