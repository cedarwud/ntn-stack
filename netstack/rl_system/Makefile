.PHONY: help setup up start stop down clean restart logs test init-db build
.DEFAULT_GOAL := help

# 顏色定義
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[1;34m
MAGENTA = \033[0;35m
CYAN = \033[0;36m
RESET = \033[0m

# 專案配置
PROJECT_NAME = rl_system
COMPOSE_FILE = docker-compose.yml

help:
	@echo "$(CYAN)🤖 RL System Management Makefile$(RESET)"
	@echo ""
	@echo "$(YELLOW)可用命令:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## 建立或更新 Docker 映像檔
	@echo "$(BLUE)🔨 正在建立 RL System 的 Docker 映像檔...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) build
	@echo "$(GREEN)✅ RL System 映像檔建立完成。$(RESET)"

build-n: ## 建立或更新 Docker 映像檔 (不使用快取)
	@echo "$(BLUE)🔨 正在建立 RL System 的 Docker 映像檔 (不使用快取)...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) build --no-cache
	@echo "$(GREEN)✅ RL System 映像檔建立完成。$(RESET)"

setup: ## 設置開發環境 (安裝依賴, 創建 .env)
	@echo "$(BLUE)🛠️  正在設置 RL System 開發環境...$(RESET)"
	@echo "$(YELLOW)  - 檢查 Python 依賴...$(RESET)"
	@python3 -m pip install -r requirements.txt
	@echo "$(YELLOW)  - 檢查 .env 文件...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(MAGENTA)    - .env 文件不存在，從 .env.example 複製...$(RESET)"; \
		cp .env.example .env; \
		echo "$(GREEN)    - .env 文件已創建。請根據需要修改。$(RESET)"; \
	else \
		echo "$(GREEN)    - .env 文件已存在。$(RESET)"; \
	fi
	@echo "$(GREEN)✅ 環境設置完成。$(RESET)"

up: ## 啟動開發環境 (PostgreSQL + FastAPI)
	@echo "$(BLUE)🚀 啟動 RL System 開發環境...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) up -d

start: up ## 'start' 是 'up' 的別名

stop: ## 停止所有服務
	@echo "$(BLUE)🛑 停止 RL System 服務...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) down

down: stop ## 'down' 是 'stop' 的別名

clean: ## 清理所有資源 (容器, 卷, 網路)
	@echo "$(RED)🧹 清理所有 RL System 資源 (包含數據庫)...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	@echo "$(GREEN)✅ RL System 資源清理完成。$(RESET)"

clean-i: ## 清理所有資源及 Docker 映像檔
	@echo "$(RED)🧹 清理所有 RL System 資源及 Docker 映像檔...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) down -v --rmi all --remove-orphans
	@echo "$(GREEN)✅ RL System 資源及映像檔清理完成。$(RESET)"

restart: ## 重啟服務
	@echo "$(BLUE)🔄 重啟 RL System 服務...$(RESET)"
	@$(MAKE) stop
	@$(MAKE) up
	@echo "$(GREEN)✅ RL System 服務已重啟。$(RESET)"

logs: ## 查看服務日誌
	@echo "$(BLUE)📋 查看 RL System 服務日誌...$(RESET)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
	@docker compose -f $(COMPOSE_FILE) logs -f

test: ## 🧪 執行 Phase 1 整合測試
	@echo "$(CYAN)🧪 執行 Phase 1 整合測試...$(RESET)"
	@echo "$(YELLOW)確保測試環境是乾淨的...$(RESET)"
	@$(MAKE) clean > /dev/null
	@echo "$(YELLOW)啟動服務進行測試...$(RESET)"
	@$(MAKE) up
	@echo "$(YELLOW)等待服務就緒...$(RESET)"
	@sleep 10
	@echo "$(YELLOW)執行 pytest...$(RESET)"
	@python3 -m pytest test_phase1.py -v
	@echo "$(CYAN)測試執行完畢。正在清理環境...$(RESET)"
	@$(MAKE) stop > /dev/null
	@echo "$(GREEN)✅ 測試流程完成。$(RESET)"

init-db: ## 初始化數據庫 (手動)
	@echo "$(BLUE)🔧 手動初始化數據庫...$(RESET)"
	@python3 database/init_database.py
	@echo "$(GREEN)✅ 數據庫初始化腳本執行完畢。$(RESET)"