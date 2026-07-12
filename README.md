# 股票追蹤與決策輔助系統 V2.0

一個基於 Streamlit 的全方位股票分析系統，支持**台股 + 美股**，提供 12 維度深度分析、AI 驅動的買賣建議、定時推播。

## ✨ V2.0 新功能

### 🆕 6 大進階分析維度
- **DCF 折現現金流估值** — 5 年 FCF 預測 + 4 種方法交叉驗證 + 敏感度分析
- **新聞情緒分析** — 中英文關鍵詞量化評分 (-1 ~ +1)，時效加權
- **法說會語調分析** — 管理層語氣判斷（鷹派/鴿派/中性）
- **護城河量化評分** — 10 項指標，1-10 分制，自動判定寬/窄/有限護城河
- **反偏誤框架** — 牛熊辯論 + 認知陷阱偵測 + Pre-Mortem 分析
- **SEC 10-K/10-Q 解析** — 美股年報自動搜尋

### 🆕 多源數據整合
- **Yahoo Finance (yfinance)** — 價格、財報、分析師評級、持股結構
- **FRED API** — 美國宏觀經濟指標（CPI、GDP、利率、失業率）
- **鉅亨網 API** — 台灣財經新聞、法說會紀錄、投行觀點
- **FinMind API** — 台股融資融券、法人買賣超

### 🆕 自動化推播
- 每日盤後自選股掃描（異常警報）
- 每週深度分析報告（輪流分析 6 檔自選股）
- Telegram 即時推播

## 🚀 快速開始

### 1. 安裝相依套件

```bash
# 建議使用虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安裝相依套件
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env 檔案
# 設定 Telegram 相關參數（選擇性）
```

### 3. 初始化資料庫並匯入範例資料

```bash
# V1 初始化：初始化資料庫、匯入範例資料、計算技術指標、計算評分、產生訊號
python scripts/init_db.py

# V1.1 擴展：擴展資料庫、匯入 5+2 研究框架資料
python scripts/init_db_v1_1.py
```

### 4. 啟動系統

```bash
# 前景執行（關閉終端機即停止）
python -m streamlit run app.py

# 或背景執行（Windows：不佔用終端機視窗）
scripts/start_app.bat    # 啟動並自動開啟瀏覽器
scripts/stop_app.bat     # 停止

# 開啟瀏覽器
# → http://localhost:8501
```

### 5. 使用 AI 分析（命令列）

```bash
# 收集股票數據
python scripts/collect_stock_data.py 2330 --pretty -o data/analysis_2330.json
python scripts/collect_stock_data.py NVDA --pretty -o data/analysis_nvda.json

# 進階分析（DCF、情緒、護城河、反偏誤）
python scripts/advanced_analysis.py 2330 --input data/analysis_2330.json --pretty -o data/advanced_2330.json

# 快速掃描自選股
python scripts/daily_watchlist_scan.py 2330 2317 2454

# 僅 DCF 估值
python scripts/advanced_analysis.py NVDA --dcf-only --pretty

# 僅護城河評分
python scripts/advanced_analysis.py 2330 --moat-only --input data/analysis_2330.json
```

## 📊 12 維度分析框架

| # | 維度 | 數據來源 | 說明 |
|---|------|---------|------|
| 1 | 技術分析 | Yahoo Finance | MA/RSI/MACD/布林通道/支撐壓力 |
| 2 | 基本面 | yfinance | PE/PB/ROE/毛利率/淨利率 |
| 3 | 財報分析 | yfinance | 季度損益表/資產負債表/現金流量表 |
| 4 | 分析師評級 | yfinance | 目標價/評級分佈/上漲空間 |
| 5 | 宏觀指標 | FRED + Yahoo | CPI/GDP/利率/VIX/匯率/大宗商品 |
| 6 | 行業分析 | yfinance | 行業規模/生命週期/競爭格局 |
| 7 | 護城河評分 | 量化模型 | 10 項指標 → 寬/窄/有限護城河 |
| 8 | DCF 估值 | yfinance 現金流 | 4 種方法交叉驗證 + 敏感度矩陣 |
| 9 | 新聞情緒 | 鉅亨網 + Yahoo | 中英文關鍵詞量化 (-1~+1) |
| 10 | 法說會語調 | 鉅亨網 | 管理層語氣分析 |
| 11 | 反偏誤框架 | 自動生成 | 牛熊辯論 + 認知陷阱 + Pre-Mortem |
| 12 | 管理層分析 | yfinance | 持股結構/機構持股/內部人持股 |

## 📁 專案結構

```
stock-analysis-FIL/
├── app.py                          # Streamlit 主應用程式
├── pages/                          # Streamlit 頁面（10 個）
│   ├── 1_個股分析.py               # 個股分析頁面
│   ├── 2_簡易回測.py               # 簡易回測頁面
│   ├── 3_今日訊號.py               # 每日訊號
│   ├── 4_股票評分.py               # 股票評分
│   ├── 5_自選股管理.py             # 自選股管理
│   ├── 6_research_5plus2.py        # 5+2 投資研究框架
│   ├── 7_macro_dashboard.py        # 宏觀 Dashboard
│   ├── 8_earnings_calls.py         # 財報與電話會議
│   ├── 9_analyst_views.py          # 投行觀點
│   └── 10_correlation.py           # 宏觀-個股相關性分析
├── modules/                        # 核心業務邏輯模組
│   ├── database.py                 # 資料庫查詢模組
│   ├── indicators.py               # 技術指標計算
│   ├── scoring.py                  # 評分系統
│   ├── signals.py                  # 訊號系統
│   ├── alerts.py                   # Telegram 警報
│   ├── macro_analysis.py           # 宏觀分析
│   ├── earnings_call.py            # 法說會管理
│   ├── analyst_views.py            # 投行觀點管理
│   ├── industry_analysis.py        # 行業分析
│   ├── management_analysis.py      # 管理層分析
│   ├── financial_analysis.py       # 財報分析
│   ├── valuation.py                # 估值分析
│   ├── business_model.py           # 商業模式分析
│   ├── investment_thesis.py        # 投資邏輯
│   ├── risk_analysis.py            # 風險分析
│   ├── research_5plus2.py          # 5+2 綜合評估
│   └── backtest.py                 # 回測引擎
├── scripts/                        # 自動化腳本
│   ├── collect_stock_data.py       # 🆕 多源數據收集器
│   ├── advanced_analysis.py        # 🆕 進階分析（DCF/情緒/護城河/反偏誤）
│   ├── daily_watchlist_scan.py     # 🆕 自選股快速掃描
│   ├── daily_orchestrator.py       # 統一排程器
│   ├── fetch_earnings_analyst.py   # 每日市場數據抓取
│   ├── threshold_alerts.py         # 閾值警報系統
│   ├── update_data.py              # FinMind 數據更新
│   ├── calculate_indicators.py     # 計算技術指標
│   ├── calculate_scores.py         # 計算評分
│   └── generate_signals.py         # 產生訊號
├── tests/                          # 測試（24 個檔案）
├── data/
│   └── stocks.db                   # SQLite 資料庫
├── config/
│   ├── scoring_config.py           # 評分設定
│   └── signals_config.py           # 訊號設定
└── requirements.txt
```

## 🔧 技術架構

| 層級 | 技術 |
|------|------|
| **前端** | Streamlit + Plotly |
| **後端** | Python 3.12 |
| **資料庫** | SQLite |
| **數據源** | Yahoo Finance / FRED / 鉅亨網 / FinMind / SEC EDGAR |
| **分析引擎** | yfinance + pandas + scipy + 自建模型 |
| **推播** | Telegram Bot API |
| **排程** | Windows Task Scheduler / Hermes Cron |
| **測試** | pytest |

## 📈 支持的市場

| 市場 | 格式 | 範例 |
|------|------|------|
| 台灣 TWSE | 4 位數字 | 2330, 2317, 2454 |
| 美股 NASDAQ/NYSE | 股票代號 | NVDA, AAPL, TSLA |

## 📋 預設自選股

| 代號 | 名稱 | 市場 |
|------|------|------|
| 2330 | 台積電 | TWSE |
| 2317 | 鴻海 | TWSE |
| 2454 | 聯發科 | TWSE |
| 2308 | 台達電 | TWSE |
| 2303 | 友達 | TWSE |
| 2881 | 富邦金 | TWSE |

## 📜 版本歷史

- **V2.0** (2026-07) — 多源數據整合、6 大進階分析維度、自動化推播
- **V1.1** — 5+2 投資研究框架、宏觀 Dashboard、法說會/投行觀點
- **V1.0** — 基礎技術分析、評分系統、訊號系統
