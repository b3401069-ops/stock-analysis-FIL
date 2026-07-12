# 股票追蹤與決策輔助系統 V1

一個基於 Streamlit 的股票追蹤與決策輔助系統，提供技術分析、股票評分、訊號系統等功能。

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
# 初始化資料庫、匯入範例資料、計算技術指標、計算評分、產生訊號
python scripts/init_db.py
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

## 📁 專案結構

```
stock-analysis-FIL/
├── app.py                  # Streamlit 主應用程式
├── pages/                  # Streamlit 頁面
│   ├── 1_個股分析.py       # 個股分析頁面
│   └── 2_簡易回測.py       # 簡易回測頁面
├── modules/                # 核心業務邏輯模組
│   ├── database.py         # 資料庫查詢模組
│   ├── indicators.py       # 技術指標計算
│   ├── scoring.py          # 股票評分系統
│   ├── signals.py          # 訊號產生系統
│   ├── backtest.py         # 回測引擎
│   └── alerts.py           # Telegram 警報模組
├── scripts/                # 腳本工具
│   ├── init_db.py          # 資料庫初始化
│   ├── calculate_indicators.py  # 計算技術指標
│   ├── calculate_scores.py      # 計算股票評分
│   ├── generate_signals.py      # 產生訊號
│   └── send_daily_alerts.py     # 發送每日警報
├── data/                   # 資料檔案
│   ├── stocks.db           # SQLite 資料庫（自動產生）
│   ├── sample_stocks.csv   # 範例股票資料
│   ├── sample_prices.csv   # 範例價格資料
│   └── sample_fundamentals.csv  # 範例基本面資料
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

- 📊 **自選股 Dashboard**：追蹤自選股清單、最新價格、漲跌幅
- 📈 **技術指標**：MA5/MA20/MA60、RSI、MACD、成交量均線
- ⭐ **股票評分**：規則型評分系統，技術面/基本面/風險分數
- 🚦 **訊號系統**：每日自動產生技術訊號
- 📉 **簡易回測**：驗證投資策略的勝率與報酬
- 📱 **Telegram 通知**：每日訊號摘要推送

## 📋 評級觀察詞（研究參考用）

⚠️ **免責聲明**：以下評級僅供技術分析研究參考，不構成任何投資建議。

| 觀察詞 | 說明 |
|--------|------|
| 強勢追蹤 | 多項技術指標顯示強勢，值得持續觀察 |
| 偏多觀察 | 部分技術指標偏多，可持續觀察 |
| 普通觀察 | 技術指標中性，維持觀察 |
| 風險留意 | 風險指標增加，需謹慎觀察 |
| 風險升高 | 風險指標升高，需更加謹慎觀察 |
| 暫不追蹤 | 多項技術指標不佳，暫時觀望 |

## ⚠️ 重要聲明

- 本系統僅供學習與研究用途
- **不構成任何投資建議**，所有評級僅供技術分析參考
- 投資有風險，請謹慎評估
- 目前不支援自動下單功能
- 未來接富邦 API 前需要再次 review 安全性

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

系統已內建範例資料，執行 `python scripts/init_db.py` 即可匯入。

### 自訂資料

1. **股票資料**：編輯 `data/sample_stocks.csv`
2. **價格資料**：編輯 `data/sample_prices.csv`
3. **基本面資料**：編輯 `data/sample_fundamentals.csv`

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
# 初始化資料庫（包含所有計算）
python scripts/init_db.py

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