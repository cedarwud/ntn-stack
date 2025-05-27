# NTN Stack 統一管理 Makefile
# 提供一鍵管理 netstack 和 simworld 專案的功能

.PHONY: help install start stop clean test logs status deploy down restart build

# 預設目標
.DEFAULT_GOAL := help

# 顏色定義
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[1;34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# 專案配置
NETSTACK_DIR := netstack
SIMWORLD_DIR := simworld
COMPOSE_PROJECT_NAME := ntn-stack

# Docker Compose 文件
NETSTACK_COMPOSE := $(NETSTACK_DIR)/compose/core.yaml
SIMWORLD_COMPOSE := $(SIMWORLD_DIR)/docker-compose.yml

# 服務 URL
NETSTACK_URL := http://localhost:8080
SIMWORLD_URL := http://localhost:8888

# 測試報告目錄
REPORTS_DIR := test-reports
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

help: ## 顯示幫助信息
	@echo "$(CYAN)🚀 NTN Stack 統一管理工具$(RESET)"
	@echo ""
	@echo "$(YELLOW)可用命令:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)專案管理:$(RESET)"
	@echo "  $(GREEN)netstack-*$(RESET)          NetStack 專案相關操作"
	@echo "  $(GREEN)simworld-*$(RESET)          SimWorld 專案相關操作"
	@echo "  $(GREEN)all-*$(RESET)               兩個專案一起操作"
	@echo ""
	@echo "$(YELLOW)測試相關:$(RESET)"
	@echo "  $(GREEN)test$(RESET)                執行完整功能測試"
	@echo "  $(GREEN)test-quick$(RESET)          執行快速測試"
	@echo "  $(GREEN)test-report$(RESET)         生成詳細測試報告"

# ===== 服務啟動 =====

up: all-start ## 啟動所有服務

all-start: ## 啟動 NetStack 和 SimWorld
	@echo "$(CYAN)🚀 啟動所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) simworld-start
	@echo "$(YELLOW)⏳ 等待 SimWorld 啟動完成...$(RESET)"
	@sleep 10
	@$(MAKE) netstack-start
	@echo "$(YELLOW)⏳ 等待 NetStack 啟動完成...$(RESET)"
	@sleep 15
	@$(MAKE) status
	@echo "$(GREEN)✅ 所有服務啟動完成$(RESET)"
	@echo ""
	@echo "$(CYAN)🌐 服務訪問地址:$(RESET)"
	@echo "  NetStack API:  $(NETSTACK_URL)"
	@echo "  NetStack Docs: $(NETSTACK_URL)/docs"
	@echo "  SimWorld:      $(SIMWORLD_URL)"

netstack-start: ## 啟動 NetStack 服務
	@echo "$(BLUE)🚀 啟動 NetStack 服務...$(RESET)"
	@cd ${NETSTACK_DIR} && $(MAKE) dev-up
	@echo "$(GREEN)✅ NetStack 服務已啟動$(RESET)"

simworld-start: ## 啟動 SimWorld 服務
	@echo "$(BLUE)🚀 啟動 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose up -d
	@echo "$(GREEN)✅ SimWorld 服務已啟動$(RESET)"

# ===== 服務停止 =====

down: all-stop ## 停止所有服務

all-stop: ## 停止 NetStack 和 SimWorld
	@echo "$(CYAN)🛑 停止所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) netstack-stop
	@$(MAKE) simworld-stop
	@echo "$(GREEN)✅ 所有服務已停止$(RESET)"

netstack-stop: ## 停止 NetStack 服務
	@echo "$(BLUE)🛑 停止 NetStack 服務...$(RESET)"
	@cd ${NETSTACK_DIR} && $(MAKE) down
	@echo "$(GREEN)✅ NetStack 服務已停止$(RESET)"

simworld-stop: ## 停止 SimWorld 服務
	@echo "$(BLUE)🛑 停止 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down
	@echo "$(GREEN)✅ SimWorld 服務已停止$(RESET)"

down-v: all-stop-v ## 停止所有服務

all-stop-v: ## 停止 NetStack 和 SimWorld
	@echo "$(CYAN)🛑 停止所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) netstack-stop-v
	@$(MAKE) simworld-stop-v
	@echo "$(GREEN)✅ 所有服務已停止$(RESET)"

netstack-stop-v: ## 停止 NetStack 服務
	@echo "$(BLUE)🛑 停止 NetStack 服務...$(RESET)"
	@cd ${NETSTACK_DIR} && $(MAKE) down-v
	@echo "$(GREEN)✅ NetStack 服務已停止$(RESET)"

simworld-stop-v: ## 停止 SimWorld 服務
	@echo "$(BLUE)🛑 停止 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down -v
	@echo "$(GREEN)✅ SimWorld 服務已停止$(RESET)"

# ===== 服務重啟 =====

restart: all-restart ## 重啟所有服務

all-restart: ## 重啟 NetStack 和 SimWorld
	@echo "$(CYAN)🔄 重啟所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) all-stop
	@sleep 5
	@$(MAKE) all-start

netstack-restart: ## 重啟 NetStack 服務
	@echo "$(BLUE)🔄 重啟 NetStack 服務...$(RESET)"
	@$(MAKE) netstack-stop
	@sleep 3
	@$(MAKE) netstack-start

simworld-restart: ## 重啟 SimWorld 服務
	@echo "$(BLUE)🔄 重啟 SimWorld 服務...$(RESET)"
	@$(MAKE) simworld-stop
	@sleep 3
	@$(MAKE) simworld-start

# ===== 服務構建 =====

build: all-build ## 構建所有服務

all-build: ## 構建 NetStack 和 SimWorld
	@echo "$(CYAN)🔨 構建所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) netstack-build
	@$(MAKE) simworld-build
	@echo "$(GREEN)✅ 所有服務構建完成$(RESET)"

netstack-build: ## 構建 NetStack 服務
	@echo "$(BLUE)🔨 構建 NetStack 服務...$(RESET)"
	@cd $(NETSTACK_DIR) && docker build -t netstack-api:latest -f docker/Dockerfile .
	@echo "$(GREEN)✅ NetStack 服務構建完成$(RESET)"

simworld-build: ## 構建 SimWorld 服務
	@echo "$(BLUE)🔨 構建 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose build
	@echo "$(GREEN)✅ SimWorld 服務構建完成$(RESET)"

# ===== 清理 =====

clean: all-clean ## 清理所有資源

all-clean: ## 清理 NetStack 和 SimWorld 資源
	@echo "$(CYAN)🧹 清理所有 NTN Stack 資源...$(RESET)"
	@$(MAKE) netstack-clean
	@$(MAKE) simworld-clean
	@$(MAKE) clean-reports
	@echo "$(GREEN)✅ 所有資源清理完成$(RESET)"

netstack-clean: ## 清理 NetStack 資源
	@echo "$(BLUE)🧹 清理 NetStack 資源...$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml down -v --remove-orphans
	@docker system prune -f --filter "label=com.docker.compose.project=netstack"
	@echo "$(GREEN)✅ NetStack 資源清理完成$(RESET)"

simworld-clean: ## 清理 SimWorld 資源
	@echo "$(BLUE)🧹 清理 SimWorld 資源...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down -v --remove-orphans
	@docker system prune -f --filter "label=com.docker.compose.project=simworld"
	@echo "$(GREEN)✅ SimWorld 資源清理完成$(RESET)"

clean-reports: ## 清理測試報告
	@echo "$(BLUE)🧹 清理測試報告...$(RESET)"
	@rm -rf $(REPORTS_DIR)
	@echo "$(GREEN)✅ 測試報告清理完成$(RESET)"

# ===== 狀態檢查 =====

status: ## 檢查所有服務狀態
	@echo "$(CYAN)📊 檢查 NTN Stack 服務狀態...$(RESET)"
	@echo ""
	@echo "$(YELLOW)NetStack 服務狀態:$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml ps || echo "$(RED)❌ NetStack 服務未運行$(RESET)"
	@echo ""
	@echo "$(YELLOW)SimWorld 服務狀態:$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose ps || echo "$(RED)❌ SimWorld 服務未運行$(RESET)"
	@echo ""
	@echo "$(YELLOW)服務健康檢查:$(RESET)"
	@curl -s $(NETSTACK_URL)/health > /dev/null && echo "$(GREEN)✅ NetStack 健康檢查通過$(RESET)" || echo "$(RED)❌ NetStack 健康檢查失敗$(RESET)"
	@curl -s $(SIMWORLD_URL)/ > /dev/null && echo "$(GREEN)✅ SimWorld 健康檢查通過$(RESET)" || echo "$(RED)❌ SimWorld 健康檢查失敗$(RESET)"

netstack-status: ## 檢查 NetStack 狀態
	@echo "$(BLUE)📊 NetStack 服務狀態:$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml ps

simworld-status: ## 檢查 SimWorld 狀態
	@echo "$(BLUE)📊 SimWorld 服務狀態:$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose ps

# ===== 日誌查看 =====

logs: all-logs ## 查看所有服務日誌

all-logs: ## 查看 NetStack 和 SimWorld 日誌
	@echo "$(CYAN)📋 查看所有 NTN Stack 服務日誌...$(RESET)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
	@trap 'echo "結束日誌查看"; exit 0' INT; \
	(\
		cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml logs -f & netstack_pid=$$!; \
		cd $(SIMWORLD_DIR) && docker compose logs -f & simworld_pid=$$!; \
		wait $$netstack_pid $$simworld_pid \
	)

netstack-logs: ## 查看 NetStack 日誌
	@echo "$(BLUE)📋 NetStack 服務日誌:$(RESET)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml logs -f

simworld-logs: ## 查看 SimWorld 日誌
	@echo "$(BLUE)📋 SimWorld 服務日誌:$(RESET)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose logs -f

# ===== 測試 (Docker化) =====

test: test-ntn-validation ## 執行完整的本地測試套件

# ===== NetStack 核心測試 =====

test-ntn-validation: ## 🚀 執行 NTN 功能快速驗證
	@echo "$(CYAN)🚀 執行 NTN 功能快速驗證...$(RESET)"
	@cd netstack/tests && bash ./quick_ntn_validation.sh
	@echo "$(GREEN)✅ NTN 功能驗證完成$(RESET)"

test-config-validation: ## ⚙️ 執行 NTN 配置驗證測試
	@echo "$(CYAN)⚙️ 執行 NTN 配置驗證測試...$(RESET)"
	@cd netstack/tests && bash ./ntn_config_validation_test.sh
	@echo "$(GREEN)✅ NTN 配置驗證完成$(RESET)"

test-satellite-gnb: ## 🛰️ 執行衛星-gNodeB 整合測試
	@echo "$(CYAN)🛰️ 執行衛星-gNodeB 整合測試...$(RESET)"
	@cd netstack/tests && bash ./satellite_gnb_integration_test.sh
	@echo "$(GREEN)✅ 衛星-gNodeB 整合測試完成$(RESET)"

test-ueransim: ## 📡 執行 UERANSIM 配置測試
	@echo "$(CYAN)📡 執行 UERANSIM 配置測試...$(RESET)"
	@cd netstack/tests && bash ./ueransim_config_test.sh
	@echo "$(GREEN)✅ UERANSIM 配置測試完成$(RESET)"

test-latency: ## 🕐 執行 NTN 延遲測試
	@echo "$(CYAN)🕐 執行 NTN 延遲測試...$(RESET)"
	@cd netstack/tests && bash ./ntn_latency_test.sh
	@echo "$(GREEN)✅ NTN 延遲測試完成$(RESET)"

test-e2e: ## 🔄 執行端到端測試
	@echo "$(CYAN)🔄 執行端到端測試...$(RESET)"
	@cd netstack/tests && bash ./e2e_netstack.sh
	@echo "$(GREEN)✅ 端到端測試完成$(RESET)"

test-slice-switching: ## 🔀 執行切片切換測試
	@echo "$(CYAN)🔀 執行切片切換測試...$(RESET)"
	@cd netstack/tests && bash ./slice_switching_test.sh
	@echo "$(GREEN)✅ 切片切換測試完成$(RESET)"

test-performance: ## ⚡ 執行性能測試
	@echo "$(CYAN)⚡ 執行性能測試...$(RESET)"
	@cd netstack/tests && bash ./performance_test.sh
	@echo "$(GREEN)✅ 性能測試完成$(RESET)"

test-connectivity: ## 🔗 執行連接性測試
	@echo "$(CYAN)🔗 執行連接性測試...$(RESET)"
	@cd netstack/tests && bash ./test_connectivity.sh
	@echo "$(GREEN)✅ 連接性測試完成$(RESET)"

# ===== 測試組合 =====

test-all: ## 🎯 執行所有 NetStack 測試
	@echo "$(CYAN)🎯 執行所有 NetStack 測試...$(RESET)"
	@$(MAKE) test-ntn-validation
	@$(MAKE) test-config-validation
	@$(MAKE) test-satellite-gnb
	@$(MAKE) test-ueransim
	@$(MAKE) test-latency
	@$(MAKE) test-e2e
	@$(MAKE) test-slice-switching
	@$(MAKE) test-performance
	@$(MAKE) test-connectivity
	@echo "$(GREEN)🎉 所有測試完成$(RESET)"

test-core: ## 🔧 執行核心功能測試
	@echo "$(CYAN)🔧 執行核心功能測試...$(RESET)"
	@$(MAKE) test-ntn-validation
	@$(MAKE) test-config-validation
	@$(MAKE) test-e2e
	@$(MAKE) test-connectivity
	@echo "$(GREEN)✅ 核心功能測試完成$(RESET)"

test-advanced: ## 🚀 執行進階功能測試
	@echo "$(CYAN)🚀 執行進階功能測試...$(RESET)"
	@$(MAKE) test-satellite-gnb
	@$(MAKE) test-ueransim
	@$(MAKE) test-latency
	@$(MAKE) test-slice-switching
	@$(MAKE) test-performance
	@echo "$(GREEN)✅ 進階功能測試完成$(RESET)"

# ===== 從 netstack/Makefile 遷移的指令 =====

netstack-up: ## 🚀 啟動 NetStack 核心網
	@echo "$(CYAN)🚀 啟動 NetStack 核心網...$(RESET)"
	@cd netstack && $(MAKE) up

netstack-down: ## 🛑 停止 NetStack 核心網
	@echo "$(CYAN)🛑 停止 NetStack 核心網...$(RESET)"
	@cd netstack && $(MAKE) down



netstack-register-subscribers: ## 👤 註冊 NetStack 測試用戶
	@echo "$(CYAN)👤 註冊 NetStack 測試用戶...$(RESET)"
	@cd netstack && $(MAKE) register-subscribers

netstack-start-ran: ## 📡 啟動 RAN 模擬器
	@echo "$(CYAN)📡 啟動 RAN 模擬器...$(RESET)"
	@cd netstack && $(MAKE) start-ran

netstack-ping-test: ## 🏓 執行 NetStack Ping 測試
	@echo "$(CYAN)🏓 執行 NetStack Ping 測試...$(RESET)"
	@cd netstack && $(MAKE) ping-test

netstack-diagnose: ## 🔍 診斷 NetStack 連線問題
	@echo "$(CYAN)🔍 診斷 NetStack 連線問題...$(RESET)"
	@cd netstack && $(MAKE) diagnose

netstack-fix-connectivity: ## 🔧 修復 NetStack 連線問題
	@echo "$(CYAN)🔧 修復 NetStack 連線問題...$(RESET)"
	@cd netstack && $(MAKE) fix-connectivity

test-clean: ## 🧹 清理測試結果和臨時文件
	@echo "$(CYAN)🧹 清理測試結果和臨時文件...$(RESET)"
	@rm -rf test-reports/ netstack/tests/test-reports/ netstack/tests/*.log
	@echo "$(GREEN)✅ 測試清理完成$(RESET)"

# ===== 監控和診斷 =====

health-check: ## 執行健康檢查
	@echo "$(CYAN)🏥 執行 NTN Stack 健康檢查...$(RESET)"
	@echo ""
	@echo "$(YELLOW)NetStack 健康檢查:$(RESET)"
	@curl -s $(NETSTACK_URL)/health | jq . || echo "$(RED)❌ NetStack 不可用$(RESET)"
	@echo ""
	@echo "$(YELLOW)SimWorld 健康檢查:$(RESET)"
	@curl -s $(SIMWORLD_URL)/ > /dev/null && echo "$(GREEN)✅ SimWorld 正常$(RESET)" || echo "$(RED)❌ SimWorld 不可用$(RESET)"

metrics: ## 查看系統指標
	@echo "$(CYAN)📊 查看 NTN Stack 系統指標...$(RESET)"
	@curl -s $(NETSTACK_URL)/metrics

api-docs: ## 打開 API 文檔
	@echo "$(CYAN)📚 打開 NetStack API 文檔...$(RESET)"
	@echo "API 文檔地址: $(NETSTACK_URL)/docs"
	@command -v xdg-open > /dev/null && xdg-open $(NETSTACK_URL)/docs || echo "請手動打開: $(NETSTACK_URL)/docs"

# ===== 實用工具 =====

ps: status ## 查看服務狀態（別名）

top: ## 查看容器資源使用情況
	@echo "$(CYAN)📊 查看容器資源使用情況...$(RESET)"
	@docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

exec-netstack: ## 進入 NetStack 容器
	@echo "$(BLUE)🔧 進入 NetStack 容器...$(RESET)"
	@docker exec -it netstack-api bash || echo "$(RED)❌ NetStack 容器未運行$(RESET)"

exec-simworld: ## 進入 SimWorld 容器
	@echo "$(BLUE)🔧 進入 SimWorld 容器...$(RESET)"
	@docker exec -it fastapi_app bash || echo "$(RED)❌ SimWorld 容器未運行$(RESET)"

# ===== 版本信息 =====

version: ## 顯示版本信息
	@echo "$(CYAN)📋 NTN Stack 版本信息$(RESET)"
	@echo ""
	@echo "$(YELLOW)專案版本:$(RESET)"
	@echo "  NTN Stack: 1.0.0"
	@echo "  NetStack:  1.0.0"
	@echo "  SimWorld:  1.0.0"
	@echo ""
	@echo "$(YELLOW)Docker 版本:$(RESET)"
	@docker --version
	@echo ""
	@echo "$(YELLOW)Docker Compose 版本:$(RESET)"
	@docker-compose --version

# ===== 清理和維護 =====

prune: ## 清理 Docker 系統
	@echo "$(CYAN)🧹 清理 Docker 系統...$(RESET)"
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)✅ Docker 系統清理完成$(RESET)"

backup: ## 備份重要數據
	@echo "$(CYAN)💾 備份 NTN Stack 數據...$(RESET)"
	@mkdir -p backups/$(TIMESTAMP)
	@docker run --rm -v ntn-stack-netstack_mongo_data:/data -v $(PWD)/backups/$(TIMESTAMP):/backup alpine tar czf /backup/mongo_data.tar.gz -C /data .
	@echo "$(GREEN)✅ 數據備份完成: backups/$(TIMESTAMP)/$(RESET)"

# ===== 特殊目標 =====

# ===== 部署和運維 =====

deploy: ## 部署生產環境
	@echo "$(CYAN)🚀 部署 NTN Stack 生產環境...$(RESET)"
	@$(MAKE) build
	@$(MAKE) start
	@$(MAKE) test-quick
	@echo "$(GREEN)✅ 生產環境部署完成$(RESET)"

# ===== 開發工具 =====

dev-setup: ## 設置開發環境
	@echo "$(CYAN)🛠️ 設置 NTN Stack 開發環境...$(RESET)"
	@$(MAKE) install
	@$(MAKE) build
	@echo "$(GREEN)✅ 開發環境設置完成$(RESET)"

dev-start: ## 啟動開發環境
	@echo "$(CYAN)🛠️ 啟動 NTN Stack 開發環境...$(RESET)"
	@$(MAKE) start
	@echo ""
	@echo "$(CYAN)🌐 開發環境訪問地址:$(RESET)"
	@echo "  NetStack API:     $(NETSTACK_URL)"
	@echo "  NetStack Docs:    $(NETSTACK_URL)/docs"
	@echo "  NetStack Metrics: $(NETSTACK_URL)/metrics"
	@echo "  SimWorld:         $(SIMWORLD_URL)"

dev-logs: ## 查看開發環境日誌
	@$(MAKE) logs

# ===== 安裝和初始化 =====

install: ## 安裝所有依賴
	@echo "$(CYAN)📦 安裝專案依賴...$(RESET)"
	@$(MAKE) netstack-install
	@$(MAKE) simworld-install
	@echo "$(GREEN)✅ 所有依賴安裝完成$(RESET)"

netstack-install: ## 安裝 NetStack 依賴
	@echo "$(BLUE)📦 安裝 NetStack 依賴...$(RESET)"
	@cd $(NETSTACK_DIR) && pip install -r requirements.txt
	@echo "$(GREEN)✅ NetStack 依賴安裝完成$(RESET)"

simworld-install: ## 安裝 SimWorld 依賴
	@echo "$(BLUE)📦 安裝 SimWorld 依賴...$(RESET)"
	@cd $(SIMWORLD_DIR) && make install
	@echo "$(GREEN)✅ SimWorld 依賴安裝完成$(RESET)"

.PHONY: all
all: help ## 顯示幫助（預設目標） 