@echo off
cd /d "C:\Users\User\Documents\Codex\stock-analysis-FIL"
start "Stock Analysis FIL" /min venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
timeout /t 5 /nobreak >nul
start http://127.0.0.1:8501
