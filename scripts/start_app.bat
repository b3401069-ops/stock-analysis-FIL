@echo off
rem ============================================================
rem Start the Streamlit app in a minimized console window.
rem A "StockAnalysis" item will appear in the taskbar (minimized);
rem closing that window stops the app, or run stop_app.bat.
rem ============================================================

cd /d "%~dp0.."

set PY=python
if exist "venv\Scripts\python.exe" set PY=venv\Scripts\python.exe

start "StockAnalysis" /min %PY% -m streamlit run app.py --server.headless true

echo Starting Streamlit...
timeout /t 4 /nobreak >nul
start http://localhost:8501
