# 股票追蹤與決策輔助系統 V1.1 - Makefile
# Stock Tracking & Decision Support System V1.1 - Makefile

.PHONY: help install dev test run init-db init-db-v1-1 clean

# 預設目標
help:
	@echo "🚀 股票追蹤與決策輔助系統 V1.1"
	@echo ""
	@echo "可用命令:"
	@echo "  make install        安裝相依套件"
	@echo "  make dev            安裝開發相依套件"
	@echo "  make init-db        初始化 V1 資料庫並匯入範例資料"
	@echo "  make init-db-v1-1   擴展 V1.1 資料庫並匯入範例資料"
	@echo "  make test           執行測試"
	@echo "  make run            啟動 Streamlit 應用程式"
	@echo "  make clean          清理暫存檔案"

# 安裝相依套件
install:
	pip install -r requirements.txt

# 安裝開發相依套件
dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8

# 初始化 V1 資料庫
init-db:
	python scripts/init_db.py

# 擴展 V1.1 資料庫
init-db-v1-1:
	python scripts/init_db_v1_1.py

# 執行測試
test:
	pytest tests/ -v

# 啟動 Streamlit 應用程式
run:
	streamlit run app.py

# 清理暫存檔案
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf htmlcov/
	rm -rf .coverage