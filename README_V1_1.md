# 股票追蹤與決策輔助系統 V1.1

一個基於 Streamlit 的股票追蹤與決策輔助系統，提供技術分析、股票評分、訊號系統，以及 **5+2 投資研究框架**。

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
# 啟動 Streamlit 應用程式
streamlit run app.py

# 開啟瀏覽器
# → http://localhost:8501
```

### 5. 瀏覽功能

- **首頁**：自選股 Dashboard
- **個股分析**：K 線圖、技術指標、基本面摘要
- **簡易回測**：策略回測與績效分析
- **今日訊號**：每日自動產生的技術訊號
- **5+2 投資研究**：系統化投資分析框架
- **宏觀 Dashboard**：總體經濟資料視覺化
- **財報與電話會議**：每季財報與管理層指引
- **投行觀點**：投行研究報告觀點

## 📁 專案結構

```
stock-analysis-FIL/
├── app.py                  # Streamlit 主應用程式
├── pages/                  # Streamlit 頁面
│   ├── 1_個股分析.py       # 個股分析頁面
│   ├── 2_簡易回測.py       # 簡易回測頁面
│   ├── 6_research_5plus2.py # 5+2 投資研究框架
│   ├── 7_macro_dashboard.py # 宏觀 Dashboard
│   ├── 8_earnings_calls.py  # 財報與電話會議
│   └── 9_analyst_views.py   # 投行觀點
├── modules/                # 核心業務邏輯模組
│   ├── database.py         # 資料庫查詢模組
│   ├── indicators.py       # 技術指標計算
│   ├── scoring.py          # 股票評分系統
│   ├── signals.py          # 訊號產生系統
│   ├── backtest.py         # 回測引擎
│   ├── alerts.py           # Telegram 警報模組
│   ├── industry_analysis.py # 行業分析
│   ├── business_model.py   # 商業模式分析
│   ├── management_analysis.py # 經營管理層分析
│   ├── financial_analysis.py # 財報分析
│   ├── valuation.py        # 公司估值分析
│   ├── investment_thesis.py # 投資邏輯
│   ├── risk_analysis.py    # 風險分析
│   ├── macro_analysis.py   # 總體經濟分析
│   ├── earnings_call.py    # 電話會議紀錄
│   ├── analyst_views.py    # 投行觀點
│   └── research_5plus2.py  # 5+2 綜合評估
├── scripts/                # 腳本工具
│   ├── init_db.py          # V1 資料庫初始化
│   ├── init_db_v1_1.py     # V1.1 資料庫擴展
│   ├── calculate_indicators.py  # 計算技術指標
│   ├── calculate_scores.py      # 計算股票評分
│   ├── generate_signals.py      # 產生訊號
│   └── send_daily_alerts.py     # 發送每日警報
├── data/                   # 資料檔案
│   ├── stocks.db           # SQLite 資料庫（自動產生）
│   ├── sample_stocks.csv   # 範例股票資料
│   ├── sample_prices.csv   # 範例價格資料
│   ├── sample_fundamentals.csv  # 範例基本面資料
│   ├── sample_earnings_calls.csv # 範例電話會議資料
│   ├── sample_analyst_views.csv  # 範例投行觀點資料
│   ├── sample_research_5plus2.csv # 範例 5+2 綜合評估資料
│   └── sample_macro_indicators.csv # 範例總體經濟指標資料
├── tests/                  # 測試檔案
├── logs/                   # 日誌檔案（自動產生）
├── .env.example            # 環境變數範例
├── .gitignore              # Git 忽略規則
├── Makefile                # 常用命令集合
├── pytest.ini              # 測試配置
├── requirements.txt        # 相依套件
└── README.md               # 本說明檔案
```

## ✨ 功能特色

### V1 核心功能
- 📊 **自選股 Dashboard**：追蹤自選股清單、最新價格、漲跌幅
- 📈 **技術指標**：MA5/MA20/MA60、RSI、MACD、成交量均線
- ⭐ **股票評分**：規則型評分系統，技術面/基本面/風險分數
- 🚦 **訊號系統**：每日自動產生技術訊號
- 📉 **簡易回測**：驗證投資策略的勝率與報酬
- 📱 **Telegram 通知**：每日訊號摘要推送

### V1.1 新增功能
- 📋 **5+2 投資研究框架**：系統化投資分析方法
  - 行業分析
  - 商業模式分析
  - 經營管理層分析
  - 財報分析
  - 公司估值分析
  - 投資邏輯：為什麼要買
  - 分析風險：為什麼不買
- 🌐 **宏觀 Dashboard**：總體經濟資料視覺化儀表板
- 📞 **財報與電話會議**：每季財報與管理層指引紀錄
- 🏦 **投行觀點**：投行研究報告觀點與共識評級

## 📋 評級觀察詞（研究參考用）

⚠️ **免責聲明**：以下評級僅供技術分析研究參考，不構成任何投資建議。

| 觀察詞 | 說明 |
|--------|------|
| 投資邏輯成立 | 5+2 分析框架總評分 80 分以上 |
| 投資邏輯部分成立 | 5+2 分析框架總評分 60-79 分 |
| 投資邏輯待確認 | 5+2 分析框架總評分 40-59 分 |
| 投資邏輯轉弱 | 5+2 分析框架總評分 40 分以下 |
| 風險升高 | 風險分析評分較低 |
| 估值偏高 | 估值分析顯示股價偏高 |
| 估值合理 | 估值分析顯示股價合理 |
| 基本面轉強 | 財報與業務分析顯示改善 |
| 基本面轉弱 | 財報與業務分析顯示惡化 |
| 需要人工確認 | 資料不足，需要人工分析 |

## ⚠️ 重要聲明

- 本系統僅供學習與研究用途
- **不構成任何投資建議**，所有評級僅供技術分析參考
- 投資有風險，請謹慎評估
- 目前不支援自動下單功能
- 未來接富邦 API 前需要再次 review 安全性
- 宏觀資料僅供參考，不應直接作為買賣依據

## 🔧 技術架構

- **前端**：Streamlit
- **資料庫**：SQLite
- **資料視覺化**：Plotly
- **技術分析**：pandas-ta
- **通知**：Telegram Bot API
- **測試**：pytest

## 📱 Telegram 設定

### 1. 建立 Telegram Bot

1. 在 Telegram 搜尋 `@BotFather`
2. 發送 `/newbot`
3. 按照指示設定 Bot 名稱和使用者名稱
4. 取得 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 取得 Chat ID

1. 在 Telegram 搜尋您剛建立的 Bot
2. 發送任意訊息給 Bot
3. 開啟瀏覽器，訪問：
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
4. 在 JSON 回應中找到 `"chat":{"id":123456789}`，這就是您的 Chat ID

### 3. 設定環境變數

在 `.env` 檔案中設定：

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 4. 測試發送

```bash
# 發送每日警報
python scripts/send_daily_alerts.py
```

## 📊 資料匯入

### 使用範例資料

系統已內建範例資料，執行 `python scripts/init_db.py` 和 `python scripts/init_db_v1_1.py` 即可匯入。

### 自訂資料

1. **股票資料**：編輯 `data/sample_stocks.csv`
2. **價格資料**：編輯 `data/sample_prices.csv`
3. **基本面資料**：編輯 `data/sample_fundamentals.csv`
4. **電話會議資料**：編輯 `data/sample_earnings_calls.csv`
5. **投行觀點資料**：編輯 `data/sample_analyst_views.csv`
6. **5+2 評估資料**：編輯 `data/sample_research_5plus2.csv`
7. **總體經濟指標**：編輯 `data/sample_macro_indicators.csv`

CSV 格式範例：

```csv
stock_id,date,open,high,low,close,volume
2330,2025-07-01,1010,1020,1005,1018,38000000
```

## 🧪 測試

```bash
# 執行所有測試
python -m pytest tests/ -v

# 執行特定測試
python -m pytest tests/test_scoring.py -v

# 產生測試覆蓋率報告
python -m pytest tests/ --cov=modules --cov-report=html
```

## 📝 常用命令

```bash
# 初始化 V1 資料庫（包含所有計算）
python scripts/init_db.py

# 擴展 V1.1 資料庫
python scripts/init_db_v1_1.py

# 重新計算技術指標
python scripts/calculate_indicators.py

# 重新計算股票評分
python scripts/calculate_scores.py

# 重新產生訊號
python scripts/generate_signals.py

# 發送每日警報
python scripts/send_daily_alerts.py

# 啟動系統
streamlit run app.py
```

## 📄 授權

MIT License