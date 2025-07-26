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
# MONITORING_DIR := monitoring  # 暫時不使用 monitoring
# RL System 已整合到 NetStack 服務中
COMPOSE_PROJECT_NAME := ntn-stack

# 環境變數配置
# 嘗試從 .env 文件載入環境變數
ifneq (,$(wildcard .env))
    include .env
    export $(shell sed 's/=.*//' .env)
endif

# 如果 .env 不存在或未設定，使用預設值
EXTERNAL_IP ?= 127.0.0.1
export EXTERNAL_IP

# Docker Compose 文件
NETSTACK_COMPOSE := $(NETSTACK_DIR)/compose/core.yaml
SIMWORLD_COMPOSE := $(SIMWORLD_DIR)/docker-compose.yml
# MONITORING_COMPOSE := $(MONITORING_DIR)/docker-compose.simple.yml  # 暫時不使用

# 服務 URL
NETSTACK_URL := http://localhost:8080
SIMWORLD_URL := http://localhost:8888
# PROMETHEUS_URL := http://localhost:9090
# GRAFANA_URL := http://localhost:3000
# ALERTMANAGER_URL := http://localhost:9093

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
	@echo "  $(GREEN)netstack-*$(RESET)          NetStack 專案相關操作 (包含 RL System)"
	@echo "  $(GREEN)simworld-*$(RESET)          SimWorld 專案相關操作"
	@echo "  $(GREEN)# monitoring-*$(RESET)      階段8監控系統操作 (暫時禁用)"
	@echo "  $(GREEN)rl-system-*$(RESET)       RL System 專案相關操作"
	@echo "  $(GREEN)all-*$(RESET)               所有專案一起操作"
	@echo ""
	@echo "$(YELLOW)測試相關:$(RESET)"
	@echo "  $(GREEN)test$(RESET)                執行完整功能測試"
	@echo "  $(GREEN)test-quick$(RESET)          執行快速測試"
	@echo "  $(GREEN)test-report$(RESET)         生成詳細測試報告"

# ===== 服務啟動 =====

fresh-up: clean-i build-n up ## 重新啟動所有服務

up: all-start ## 啟動所有服務

# start-monitoring: ## [獨立] 啟動階段8的監控服務 (暫時禁用)
#	@echo "$(BLUE)🚀 啟動監控系統...$(RESET)"
#	@$(MAKE) monitoring-start
#	@sleep 5
#	@echo "$(GREEN)✅ 監控系統已啟動。請訪問 Grafana: $(GRAFANA_URL)$(RESET)"

dev: ## 開發環境啟動 (使用 127.0.0.1)
	@echo "$(CYAN)🚀 啟動開發環境 (EXTERNAL_IP=127.0.0.1)...$(RESET)"
	@$(MAKE) all-start EXTERNAL_IP=127.0.0.1

dev-setup: ## 🛠️ 開發環境設置 (僅在需要時執行)
	@echo "$(CYAN)🛠️ 設置開發環境 (用戶註冊 + 演示數據)...$(RESET)"
	@$(MAKE) netstack-start-full
	@echo "$(GREEN)✅ 開發環境設置完成$(RESET)"

all-start: ## 啟動所有核心服務 (NetStack 含整合 RL System, SimWorld)
	@echo "$(CYAN)🚀 啟動所有 NTN Stack 服務...$(RESET)"
	@echo "$(YELLOW)⚡ 第一步：啟動 NetStack (包含 PostgreSQL 基礎服務)...$(RESET)"
	@$(MAKE) netstack-start
	@echo "$(YELLOW)⏳ 等待 NetStack 服務完全就緒...$(RESET)"
	@sleep 20
	@echo "$(YELLOW)⚡ 第二步：啟動 SimWorld (連接到 NetStack 資料庫)...$(RESET)"
	@$(MAKE) simworld-start
	@echo "$(YELLOW)⏳ 等待 SimWorld 服務啟動完成...$(RESET)"
	@sleep 10
	@echo "$(YELLOW)🔗 建立跨服務網路連接...$(RESET)"
	@$(MAKE) connect-cross-service-networks
	@echo "$(YELLOW)🔗 驗證容器間網路連接...$(RESET)"
	@$(MAKE) verify-network-connection
	@$(MAKE) status
	@echo "$(GREEN)✅ 所有服務啟動完成$(RESET)"
	@echo ""
	@echo "$(CYAN)🌐 服務訪問地址:$(RESET)"
	@echo "  NetStack API:  $(NETSTACK_URL)"
	@echo "  NetStack Docs: $(NETSTACK_URL)/docs"
	@echo "  RL System:     http://localhost:8080/api/v1/rl (統一到 NetStack)"
	@echo "  RL System Docs:http://localhost:8080/docs (統一到 NetStack)"
	@echo "  SimWorld:      $(SIMWORLD_URL)"

netstack-start: ## 啟動 NetStack 服務
	@echo "$(BLUE)🚀 啟動 NetStack 服務...$(RESET)"
	@cd ${NETSTACK_DIR} && $(MAKE) up
	@echo "$(GREEN)✅ NetStack 服務已啟動$(RESET)"

netstack-start-smart: ## 啟動 NetStack 服務 (智能等待健康檢查)
	@echo "$(BLUE)🚀 啟動 NetStack 服務 (智能等待)...$(RESET)"
	@cd ${NETSTACK_DIR} && docker compose -f compose/core.yaml up -d
	@echo "$(YELLOW)⏳ 等待 NetStack API 健康檢查通過...$(RESET)"
	@timeout=180; \
	while [ $$timeout -gt 0 ]; do \
		if curl -s -f http://localhost:8080/health >/dev/null 2>&1; then \
			echo "$(GREEN)✅ NetStack API 健康檢查通過 ($$((180-timeout)) 秒)$(RESET)"; \
			break; \
		fi; \
		echo "$(BLUE)  等待中... (剩餘 $$timeout 秒)$(RESET)"; \
		sleep 5; \
		timeout=$$((timeout-5)); \
	done; \
	if [ $$timeout -le 0 ]; then \
		echo "$(RED)❌ NetStack API 啟動超時 (180秒)$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ NetStack 服務已啟動並通過健康檢查$(RESET)"

netstack-start-full: ## 啟動 NetStack 服務並完成開發環境設置
	@echo "$(BLUE)🚀 啟動 NetStack 服務並設置開發環境...$(RESET)"
	@cd ${NETSTACK_DIR} && $(MAKE) start-with-setup
	@echo "$(GREEN)✅ NetStack 開發環境設置完成$(RESET)"

simworld-start: ## 啟動 SimWorld 服務
	@echo "$(BLUE)🚀 啟動 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose up -d
	@echo "$(GREEN)✅ SimWorld 服務已啟動$(RESET)"

# monitoring-start: ## 啟動監控系統 (階段8: Prometheus, Grafana, AlertManager) - 暫時禁用
#	@echo "$(BLUE)🚀 啟動監控系統...$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml up -d
#	@echo "$(GREEN)✅ 監控系統已啟動$(RESET)"

# ===== 服務停止 =====

down: all-stop ## 停止所有服務

all-stop: ## 停止 NetStack (含整合 RL System), SimWorld 和監控系統
	@echo "$(CYAN)🛑 停止所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) simworld-stop
	@$(MAKE) netstack-stop # netstack-stop 現在會處理 rl-system
	@echo "$(GREEN)✅ 所有服務已停止$(RESET)"

netstack-stop: ## 停止 NetStack 服務 (包含 RL System)
	@echo "$(BLUE)🛑 停止 NetStack 服務...$(RESET)"
	@cd ${NETSTACK_DIR} && $(MAKE) down
	@echo "$(GREEN)✅ NetStack 服務已停止$(RESET)"

simworld-stop: ## 停止 SimWorld 服務
	@echo "$(BLUE)🛑 停止 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down
	@echo "$(GREEN)✅ SimWorld 服務已停止$(RESET)"

# monitoring-stop: ## 停止監控系統
#	@echo "$(BLUE)🛑 停止監控系統...$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml down
#	@echo "$(GREEN)✅ 監控系統已停止$(RESET)"

# ===== 服務停止 (清除卷) =====

down-v: all-stop-v ## 停止所有服務並清除卷

all-stop-v: ## 停止 NetStack (含整合 RL System), SimWorld (清除卷)
	@echo "$(CYAN)🛑 停止所有 NTN Stack 服務 (清除卷)...$(RESET)"
	@echo "$(YELLOW)斷開跨服務網路連接...$(RESET)"
	@docker network disconnect compose_netstack-core simworld_backend 2>/dev/null || true
	@docker network disconnect compose_netstack-core simworld_frontend 2>/dev/null || true
	@docker network disconnect simworld_sionna-net netstack-api 2>/dev/null || true
	@$(MAKE) simworld-stop-v # 先停止 SimWorld 服務
	@$(MAKE) netstack-stop-v # 後停止 NetStack 服務
	@echo "$(GREEN)✅ 所有服務已停止並清除卷$(RESET)"

netstack-stop-v: ## 停止 NetStack 服務並清除卷 (包含 RL System)
	@echo "$(BLUE)🛑 停止 NetStack 服務 (清除卷)...$(RESET)"
	@cd ${NETSTACK_DIR} && $(MAKE) down-v
	@echo "$(GREEN)✅ NetStack 服務已停止並清除卷$(RESET)"

simworld-stop-v: ## 停止 SimWorld 服務並清除卷
	@echo "$(BLUE)🛑 停止 SimWorld 服務 (清除卷)...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down -v
	@echo "$(GREEN)✅ SimWorld 服務已停止並清除卷$(RESET)"

# monitoring-stop-v: ## 停止監控系統 (清除卷)
#	@echo "$(BLUE)🛑 停止監控系統 (清除卷)...$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml down -v
#	@echo "$(GREEN)✅ 監控系統已停止 (卷已清除)$(RESET)"

# ===== 服務重啟 =====

restart: all-restart ## 重啟所有服務

restart-v: all-restart-v ## 重啟所有服務 (智能等待版本)

# restart-monitoring: ## [獨立] 重啟階段8的監控服務 (暫時禁用)
#	@echo "$(BLUE)🔄 重啟監控系統...$(RESET)"
#	@$(MAKE) monitoring-restart
#	@sleep 5
#	@echo "$(GREEN)✅ 監控系統已重啟。$(RESET)"

all-restart: ## 重啟所有核心服務 (NetStack 含整合 RL System, SimWorld) - 智能等待版本
	@echo "$(CYAN)🔄 重啟所有 NTN Stack 核心服務 (智能等待)...$(RESET)"
	@$(MAKE) all-stop
	@echo "$(YELLOW)⏳ 等待系統清理完成...$(RESET)"
	@sleep 3
	@echo "$(YELLOW)🚀 啟動 NetStack (使用預載衛星數據)...$(RESET)"
	@$(MAKE) netstack-start-smart
	@echo "$(YELLOW)🚀 啟動 SimWorld...$(RESET)"
	@$(MAKE) simworld-start
	@echo "$(YELLOW)⏳ 等待 SimWorld 服務啟動...$(RESET)"
	@sleep 10
	@echo "$(YELLOW)🔗 建立跨服務連接...$(RESET)"
	@$(MAKE) connect-cross-service-networks
	@echo "$(GREEN)✅ 智能重啟完成，系統已就緒$(RESET)"

all-restart-v: ## 重啟所有核心服務 (NetStack 含整合 RL System, SimWorld) - 智能等待版本
	@echo "$(CYAN)🔄 重啟所有 NTN Stack 核心服務 (智能等待)...$(RESET)"
	@$(MAKE) all-stop-v
	@echo "$(YELLOW)⏳ 等待系統清理完成...$(RESET)"
	@sleep 3
	@echo "$(YELLOW)🚀 啟動 NetStack (使用預載衛星數據)...$(RESET)"
	@$(MAKE) netstack-start-smart
	@echo "$(YELLOW)🚀 啟動 SimWorld...$(RESET)"
	@$(MAKE) simworld-start
	@echo "$(YELLOW)⏳ 等待 SimWorld 服務啟動...$(RESET)"
	@sleep 10
	@echo "$(YELLOW)🔗 建立跨服務連接...$(RESET)"
	@$(MAKE) connect-cross-service-networks
	@echo "$(GREEN)✅ 智能重啟完成，系統已就緒$(RESET)"

netstack-restart: ## 重啟 NetStack 服務 (包含 RL System)
	@echo "$(BLUE)🔄 重啟 NetStack 服務...$(RESET)"
	@$(MAKE) netstack-stop
	@sleep 3
	@$(MAKE) netstack-start

simworld-restart: ## 重啟 SimWorld 服務
	@echo "$(BLUE)🔄 重啟 SimWorld 服務...$(RESET)"
	@$(MAKE) simworld-stop
	@sleep 3
	@$(MAKE) simworld-start

# monitoring-restart: ## 重啟監控系統
#	@echo "$(BLUE)🔄 重啟監控系統...$(RESET)"
#	# @.*monitoring-stop
#	@sleep 3
#	# @.*monitoring-start

# ===== 服務構建 =====

build: all-build ## 構建所有服務

all-build: ## 構建 NetStack 和 SimWorld
	@echo "$(CYAN)🔨 構建所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) netstack-build
	@$(MAKE) simworld-build
	@echo "$(GREEN)✅ 所有服務構建完成$(RESET)"

netstack-build: ## 構建 NetStack 服務 (包含 RL System)
	@echo "$(BLUE)🔨 構建 NetStack 服務...$(RESET)"
	@cd $(NETSTACK_DIR) && $(MAKE) build
	@echo "$(GREEN)✅ NetStack 服務構建完成$(RESET)"

simworld-build: ## 構建 SimWorld 服務
	@echo "$(BLUE)🔨 構建 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose build
	@echo "$(GREEN)✅ SimWorld 服務構建完成$(RESET)"

# monitoring-build: ## 構建監控系統服務
#	@echo "$(BLUE)🔨 構建監控系統服務...$(RESET)"
#	@echo "$(YELLOW)注意：監控服務主要使用預構建映像檔，此操作主要為拉取最新映像檔。$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml pull
#	@echo "$(GREEN)✅ 監控系統服務映像檔拉取完成$(RESET)"

build-n: all-build-n ## 構建所有服務

all-build-n: ## 構建 NetStack 和 SimWorld
	@echo "$(CYAN)🔨 構建所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) netstack-build-n
	@$(MAKE) simworld-build-n
	@echo "$(GREEN)✅ 所有服務構建完成$(RESET)"

netstack-build-n: ## 構建 NetStack 服務 (不使用緩存)
	@echo "$(BLUE)🔨 構建 NetStack 服務 (不使用緩存)...$(RESET)"
	@cd $(NETSTACK_DIR) && $(MAKE) build-n
	@echo "$(GREEN)✅ NetStack 服務構建完成 (不使用緩存)$(RESET)"

simworld-build-n: ## 構建 SimWorld 服務 (不使用緩存)
	@echo "$(BLUE)🔨 構建 SimWorld 服務 (不使用緩存)...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose build --no-cache
	@echo "$(GREEN)✅ SimWorld 服務構建完成$(RESET)"

# monitoring-build-n: ## 構建監控系統服務 (不使用緩存)
#	@echo "$(BLUE)🔨 構建監控系統服務 (不使用緩存)...$(RESET)"
#	@echo "$(YELLOW)注意：監控服務主要使用預構建映像檔，此操作主要為拉取最新映像檔。$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml pull
#	@echo "$(GREEN)✅ 監控系統服務映像檔拉取完成$(RESET)"

# ===== 清理 =====

clean: all-clean ## 清理所有資源

all-clean: ## 清理所有資源
	@echo "$(CYAN)🧹 清理所有 NTN Stack 資源...$(RESET)"
	@$(MAKE) netstack-clean # netstack-clean 會處理 rl-system
	@$(MAKE) simworld-clean
	@$(MAKE) clean-reports
	@echo "$(GREEN)✅ 所有資源清理完成$(RESET)"

netstack-clean: ## 清理 NetStack 資源 (包含 RL System)
	@echo "$(BLUE)🧹 清理 NetStack 資源...$(RESET)"
	@cd $(NETSTACK_DIR) && $(MAKE) clean
	@docker system prune -f --filter "label=com.docker.compose.project=netstack"
	@echo "$(GREEN)✅ NetStack 資源清理完成$(RESET)"

simworld-clean: ## 清理 SimWorld 資源
	@echo "$(BLUE)🧹 清理 SimWorld 資源...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down -v --remove-orphans
	@docker system prune -f --filter "label=com.docker.compose.project=simworld"
	@echo "$(GREEN)✅ SimWorld 資源清理完成$(RESET)"

# monitoring-clean: ## 清理監控系統資源
#	@echo "$(BLUE)🧹 清理監控系統資源...$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml down -v --remove-orphans
#	# @.*monitoring"
#	@echo "$(GREEN)✅ 監控系統資源清理完成$(RESET)"

clean-reports: ## 清理測試報告
	@echo "$(BLUE)🧹 清理測試報告...$(RESET)"
	@rm -rf $(REPORTS_DIR)
	@echo "$(GREEN)✅ 測試報告清理完成$(RESET)"

clean-project: ## 🧹 完整專案清理（移除不必要的檔案和目錄）
	@echo "$(CYAN)🧹 執行完整專案清理...$(RESET)"
	@bash scripts/cleanup_project.sh
	@echo "$(GREEN)✅ 完整專案清理完成$(RESET)"

clean-i: all-clean-i ## 清理所有資源

all-clean-i: ## 清理 NetStack 和 SimWorld 資源
	@echo "$(CYAN)🧹 清理所有 NTN Stack 資源...$(RESET)"
	@$(MAKE) netstack-clean-i
	@$(MAKE) simworld-clean-i
	@$(MAKE) clean-reports
	@echo "$(YELLOW)🧹 執行全局 Docker 資源清理...$(RESET)"
	@docker image prune -a -f
	@docker network prune -f
	@echo "$(GREEN)✅ 所有資源清理完成$(RESET)"

netstack-clean-i: ## 清理 NetStack 資源
	@echo "$(BLUE)🧹 清理 NetStack 映像檔...$(RESET)"
	@cd $(NETSTACK_DIR) && $(MAKE) clean-i
	@docker system prune -f --filter "label=com.docker.compose.project=netstack"
	@echo "$(GREEN)✅ NetStack 映像檔清理完成$(RESET)"

simworld-clean-i: ## 清理 SimWorld 資源
	@echo "$(BLUE)🧹 清理 SimWorld 映像檔...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down -v --remove-orphans --rmi all
	@docker system prune -f --filter "label=com.docker.compose.project=simworld"
	@echo "$(GREEN)✅ SimWorld 映像檔清理完成$(RESET)"

# monitoring-clean-i: ## 清理監控系統資源和映像檔
#	@echo "$(BLUE)🧹 清理監控系統映像檔...$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml down -v --remove-orphans --rmi all
#	# @.*monitoring"
#	@echo "$(GREEN)✅ 監控系統映像檔清理完成$(RESET)"

# ===== 狀態檢查 =====

status: ## 檢查所有服務狀態
	@echo "$(CYAN)📊 檢查 NTN Stack 服務狀態...$(RESET)"
	@echo ""
	@echo "$(YELLOW)NetStack 服務狀態:$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml ps || echo "$(RED)❌ NetStack 核心網服務未運行$(RESET)"
	@echo ""
	@echo "$(YELLOW)RL System 狀態: 已整合到 NetStack 服務中$(RESET)"
	@echo ""
	@echo "$(YELLOW)SimWorld 服務狀態:$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose ps || echo "$(RED)❌ SimWorld 服務未運行$(RESET)"
	@echo ""
	@echo "$(YELLOW)服務健康檢查:$(RESET)"
	@curl -s $(NETSTACK_URL)/health > /dev/null && echo "$(GREEN)✅ NetStack 健康檢查通過 (宿主機)$(RESET)" || echo "$(RED)❌ NetStack 健康檢查失敗$(RESET)"
	@curl -s http://localhost:8080/api/v1/rl/health > /dev/null && echo "$(GREEN)✅ RL System 健康檢查通過 (統一到 NetStack)$(RESET)" || echo "$(RED)❌ RL System 健康檢查失敗$(RESET)"
	@curl -s $(SIMWORLD_URL)/ > /dev/null && echo "$(GREEN)✅ SimWorld 健康檢查通過 (宿主機)$(RESET)" || echo "$(RED)❌ SimWorld 健康檢查失敗$(RESET)"
	@echo "$(YELLOW)跨服務連接檢查:$(RESET)"
	@timeout 10s bash -c 'docker exec simworld_backend curl -s http://netstack-api:8080/health > /dev/null 2>&1' && echo "$(GREEN)✅ SimWorld → NetStack 跨服務連接正常$(RESET)" || (echo "$(YELLOW)⚠️ SimWorld → NetStack 跨服務連接失敗，嘗試重新配置 DNS...$(RESET)" && $(MAKE) configure-cross-service-dns >/dev/null 2>&1 && sleep 2 && timeout 5s bash -c 'docker exec simworld_backend curl -s http://netstack-api:8080/health > /dev/null 2>&1' && echo "$(GREEN)✅ SimWorld → NetStack 跨服務連接已修復$(RESET)" || echo "$(RED)❌ SimWorld → NetStack 跨服務連接仍然失敗$(RESET)")
	@timeout 10s bash -c 'docker exec netstack-api curl -s http://simworld_backend:8000/ > /dev/null 2>&1' && echo "$(GREEN)✅ NetStack → SimWorld 跨服務連接正常$(RESET)" || echo "$(YELLOW)⚠️ NetStack → SimWorld 跨服務連接失敗$(RESET)"

connect-cross-service-networks: ## 🔗 建立跨服務網路連接
	@echo "$(CYAN)🔗 建立跨服務網路連接...$(RESET)"
	@echo "$(YELLOW)連接 NetStack API 到 SimWorld 網路...$(RESET)"
	@docker network connect simworld_sionna-net netstack-api 2>/dev/null && echo "$(GREEN)✅ NetStack API 已連接到 SimWorld 網路$(RESET)" || echo "$(BLUE)ℹ️  NetStack API 已連接到 SimWorld 網路$(RESET)"
	@echo "$(YELLOW)連接 SimWorld backend 到 NetStack 網路...$(RESET)"
	@docker network connect compose_netstack-core simworld_backend 2>/dev/null && echo "$(GREEN)✅ SimWorld backend 已連接到 NetStack 網路$(RESET)" || echo "$(BLUE)ℹ️  SimWorld backend 已連接到 NetStack 網路$(RESET)"
	@echo "$(YELLOW)配置容器間 DNS 解析...$(RESET)"
	@$(MAKE) configure-cross-service-dns
	@echo "$(GREEN)✅ 跨服務網路連接完成$(RESET)"

configure-cross-service-dns: ## 🌐 配置容器間 DNS 解析
	@echo "$(CYAN)🌐 配置容器間 DNS 解析...$(RESET)"
	@echo "$(YELLOW)獲取容器 IP 地址...$(RESET)"
	@NETSTACK_IP=$$(docker inspect netstack-api --format='{{range $$network, $$config := .NetworkSettings.Networks}}{{if eq $$network "compose_netstack-core"}}{{$$config.IPAddress}}{{end}}{{end}}' 2>/dev/null || echo ""); \
	SIMWORLD_IP=$$(docker inspect simworld_backend --format='{{range $$network, $$config := .NetworkSettings.Networks}}{{if eq $$network "compose_netstack-core"}}{{$$config.IPAddress}}{{end}}{{end}}' 2>/dev/null || echo ""); \
	if [ -n "$$NETSTACK_IP" ] && [ -n "$$SIMWORLD_IP" ]; then \
		echo "$(YELLOW)NetStack API: $$NETSTACK_IP, SimWorld Backend: $$SIMWORLD_IP$(RESET)"; \
		echo "$(YELLOW)配置 SimWorld → NetStack DNS...$(RESET)"; \
		docker exec simworld_backend sh -c "grep -q 'netstack-api' /etc/hosts || echo \"$$NETSTACK_IP    netstack-api\" >> /etc/hosts" 2>/dev/null || true; \
		echo "$(YELLOW)配置 NetStack → SimWorld DNS...$(RESET)"; \
		docker exec -u root netstack-api sh -c "grep -q 'simworld_backend' /etc/hosts || echo \"$$SIMWORLD_IP    simworld_backend\" >> /etc/hosts" 2>/dev/null || true; \
		echo "$(GREEN)✅ DNS 解析配置完成$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️ 無法獲取容器 IP 地址 (容器可能尚未創建): NetStack=$$NETSTACK_IP, SimWorld=$$SIMWORLD_IP$(RESET)"; \
		echo "$(YELLOW)跳過 DNS 配置，將在容器可用時再次嘗試$(RESET)"; \
	fi

verify-network-connection: ## 🔗 驗證容器間網路連接
	@echo "$(CYAN)🔗 驗證容器間網路連接...$(RESET)"
	@echo "$(YELLOW)檢查網路配置:$(RESET)"
	@docker network ls | grep -E "(netstack-core|sionna-net)" || echo "$(RED)❌ 網路不存在$(RESET)"
	@echo "$(YELLOW)檢查 SimWorld backend 網路連接:$(RESET)"
	@docker inspect simworld_backend --format='{{range $$network, $$config := .NetworkSettings.Networks}}{{$$network}}: {{$$config.IPAddress}} {{end}}' 2>/dev/null && echo "$(GREEN)✅ simworld_backend 容器網路正常$(RESET)" || echo "$(RED)❌ simworld_backend 容器未找到$(RESET)"
	@echo "$(YELLOW)檢查 NetStack API 網路連接:$(RESET)"
	@docker inspect netstack-api --format='{{range $$network, $$config := .NetworkSettings.Networks}}{{$$network}}: {{$$config.IPAddress}} {{end}}' 2>/dev/null && echo "$(GREEN)✅ netstack-api 容器網路正常$(RESET)" || echo "$(RED)❌ netstack-api 容器未找到$(RESET)"
	@echo "$(YELLOW)測試跨服務 API 連接:$(RESET)"
	@echo "$(BLUE)等待 DNS 配置生效...$(RESET)"
	@sleep 3
	@timeout 15s bash -c 'until docker exec simworld_backend curl -s http://netstack-api:8080/health > /dev/null 2>&1; do sleep 2; done' && echo "$(GREEN)✅ SimWorld -> NetStack 連接正常$(RESET)" || echo "$(YELLOW)⚠️ SimWorld -> NetStack 跨服務連接失敗$(RESET)"
	@timeout 15s bash -c 'until docker exec netstack-api curl -s http://simworld_backend:8000/ > /dev/null 2>&1; do sleep 2; done' && echo "$(GREEN)✅ NetStack -> SimWorld 連接正常$(RESET)" || echo "$(YELLOW)⚠️ NetStack -> SimWorld 跨服務連接失敗$(RESET)"

fix-network-connection: ## 🔧 修復網路連接問題（緊急備用）
	@echo "$(CYAN)🔧 修復網路連接問題...$(RESET)"
	@echo "$(YELLOW)檢查是否需要手動連接網路...$(RESET)"
	@docker inspect simworld_backend --format='{{range .NetworkSettings.Networks}}{{.NetworkMode}} {{end}}' | grep -q "compose_netstack-core" && echo "$(GREEN)✅ 網路已連接$(RESET)" || \
	(echo "$(YELLOW)⚠️  需要手動連接網路，正在修復...$(RESET)" && \
	 docker network connect compose_netstack-core simworld_backend && \
	 echo "$(GREEN)✅ 網路連接已修復$(RESET)")

netstack-status: ## 檢查 NetStack 狀態
	@echo "$(BLUE)📊 NetStack 服務狀態:$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml ps

simworld-status: ## 檢查 SimWorld 狀態
	@echo "$(BLUE)📊 SimWorld 服務狀態:$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose ps

# monitoring-status: ## 檢查監控系統狀態
#	@echo "$(BLUE)📊 監控系統狀態:$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml ps

# ===== 日誌查看 =====

logs: all-logs ## 查看所有服務日誌

# monitoring-logs: ## 查看監控系統日誌 (暫時禁用)
#	@echo "$(BLUE)📋 監控系統日誌:$(RESET)"
#	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml logs -f

all-logs: ## 查看所有服務日誌 (NetStack, SimWorld)
	@echo "$(CYAN)📋 查看所有 NTN Stack 服務日誌...$(RESET)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
	@trap 'echo "結束日誌查看"; exit 0' INT; \
	( \
		(cd $(NETSTACK_DIR) && $(MAKE) logs) & \
		(cd $(SIMWORLD_DIR) && docker compose logs -f) & \
		wait \
	)

netstack-logs: ## 查看 NetStack 日誌 (包含 RL System)
	@echo "$(BLUE)📋 NetStack 服務日誌:$(RESET)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
	@cd $(NETSTACK_DIR) && $(MAKE) logs

simworld-logs: ## 查看 SimWorld 日誌
	@echo "$(BLUE)📋 SimWorld 服務日誌:$(RESET)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose logs -f

# ===== RL System 已整合到 NetStack 服務中 =====
# 所有 RL System 相關功能現在通過 NetStack 服務提供
# 使用 netstack-* 指令即可管理整合後的服務

# ===== 安裝與初始化 =====

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

# ===== 測試指令重定向 =====

test: ## 🧪 執行測試（重定向到 tests/Makefile）
	@echo "$(CYAN)🧪 執行測試...$(RESET)"
	@echo "$(YELLOW)測試指令已統一移至 tests/ 目錄管理$(RESET)"
	@echo "$(BLUE)請使用以下指令：$(RESET)"
	@echo "  $(GREEN)cd tests && make help$(RESET)       - 查看所有測試指令"
	@echo "  $(GREEN)cd tests && make test-smoke$(RESET)  - 快速煙霧測試"
	@echo "  $(GREEN)cd tests && make test-all$(RESET)    - 完整測試套件"
	@echo ""
	@echo "$(YELLOW)或直接執行：$(RESET)"
	@cd tests && $(MAKE) test-smoke

.PHONY: all help start stop restart build clean status logs test \
        all-start all-stop all-restart all-build all-clean \
        netstack-start netstack-stop netstack-restart netstack-build netstack-clean netstack-status netstack-logs \
        simworld-start simworld-stop simworld-restart simworld-build simworld-clean simworld-status simworld-logs \
        dev-setup dev-start dev-logs install netstack-install simworld-install verify-network-connection fix-network-connection

# ==============================================================================
# 請注意：
# 以下 monitoring-* 和 rl-system-* 相關的目標已被整合或禁用。
# 保留註釋是為了歷史參考，請不要直接取消註釋或使用。
# ==============================================================================

# monitoring-start: ## 啟動監控系統 (階段8: Prometheus, Grafana, AlertManager) - 暫時禁用
#	@echo "$(BLUE)🚀 啟動監控系統...$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml up -d
#	@echo "$(GREEN)✅ 監控系統已啟動$(RESET)"

# monitoring-logs: ## 查看監控系統日誌 (暫時禁用)
#	@echo "$(BLUE)📋 監控系統日誌:$(RESET)"
#	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(RESET)"
#	@cd $(MONITORING_DIR) && docker compose -f docker-compose.simple.yml logs -f

# rl-system-start:
# rl-system-stop:
# rl-system-restart:
# rl-system-logs:
# rl-system-clean:
# rl-system-test:
#	@echo "$(YELLOW)RL System 已整合到 NetStack 服務中，請使用 netstack-* 指令。$(RESET)" 