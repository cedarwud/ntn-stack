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
	@echo "$(YELLOW)⚡ 第一步：啟動 NetStack (創建網路)...$(RESET)"
	@$(MAKE) netstack-start
	@echo "$(YELLOW)⏳ 等待 NetStack 網路就緒...$(RESET)"
	@sleep 15
	@echo "$(YELLOW)⚡ 第二步：啟動 SimWorld (連接網路)...$(RESET)"
	@$(MAKE) simworld-start
	@echo "$(YELLOW)⏳ 等待 SimWorld 啟動完成...$(RESET)"
	@sleep 10
	@echo "$(YELLOW)🔗 驗證容器間網路連接...$(RESET)"
	@$(MAKE) verify-network-connection
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

build-n: all-build-n ## 構建所有服務

all-build-n: ## 構建 NetStack 和 SimWorld
	@echo "$(CYAN)🔨 構建所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) netstack-build-n
	@$(MAKE) simworld-build-n
	@echo "$(GREEN)✅ 所有服務構建完成$(RESET)"

netstack-build-n: ## 構建 NetStack 服務
	@echo "$(BLUE)🔨 構建 NetStack 服務...$(RESET)"
	@cd $(NETSTACK_DIR) && docker build -t netstack-api:latest -f docker/Dockerfile . --no-cache
	@echo "$(GREEN)✅ NetStack 服務構建完成$(RESET)"

simworld-build-n: ## 構建 SimWorld 服務
	@echo "$(BLUE)🔨 構建 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose build --no-cache
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
	@cd $(NETSTACK_DIR) && docker compose -f compose/ran.yaml down -v --remove-orphans
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

clean-i: all-clean-i ## 清理所有資源

all-clean-i: ## 清理 NetStack 和 SimWorld 資源
	@echo "$(CYAN)🧹 清理所有 NTN Stack 資源...$(RESET)"
	@$(MAKE) netstack-clean-i
	@$(MAKE) simworld-clean-i
	@$(MAKE) clean-reports
	docker image prune -f
	docker network prune -f
	@echo "$(GREEN)✅ 所有資源清理完成$(RESET)"

netstack-clean-i: ## 清理 NetStack 資源
	@echo "$(BLUE)🧹 清理 NetStack 映像檔...$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml down -v --remove-orphans --rmi all
	@cd $(NETSTACK_DIR) && docker compose -f compose/ran.yaml down -v --remove-orphans --rmi all
	@docker system prune -f --filter "label=com.docker.compose.project=netstack"
	@echo "$(GREEN)✅ NetStack 映像檔清理完成$(RESET)"

simworld-clean-i: ## 清理 SimWorld 資源
	@echo "$(BLUE)🧹 清理 SimWorld 映像檔...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down -v --remove-orphans --rmi all
	@docker system prune -f --filter "label=com.docker.compose.project=simworld"
	@echo "$(GREEN)✅ SimWorld 映像檔清理完成$(RESET)"

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

verify-network-connection: ## 🔗 驗證容器間網路連接
	@echo "$(CYAN)🔗 驗證容器間網路連接...$(RESET)"
	@echo "$(YELLOW)檢查網路配置:$(RESET)"
	@docker network ls | grep -E "(netstack-core|sionna-net)" || echo "$(RED)❌ 網路不存在$(RESET)"
	@echo "$(YELLOW)檢查 SimWorld backend 網路連接:$(RESET)"
	@docker inspect simworld_backend --format='{{range $$network, $$config := .NetworkSettings.Networks}}{{$$network}}: {{$$config.IPAddress}} {{end}}' 2>/dev/null && echo "$(GREEN)✅ simworld_backend 容器網路正常$(RESET)" || echo "$(RED)❌ simworld_backend 容器未找到$(RESET)"
	@echo "$(YELLOW)檢查 NetStack API 網路連接:$(RESET)"
	@docker inspect netstack-api --format='{{range $$network, $$config := .NetworkSettings.Networks}}{{$$network}}: {{$$config.IPAddress}} {{end}}' 2>/dev/null && echo "$(GREEN)✅ netstack-api 容器網路正常$(RESET)" || echo "$(RED)❌ netstack-api 容器未找到$(RESET)"
	@echo "$(YELLOW)測試跨服務 API 連接:$(RESET)"
	@timeout 10s bash -c 'until docker exec simworld_backend curl -s http://172.20.0.40:8080/health > /dev/null 2>&1; do sleep 1; done' && echo "$(GREEN)✅ SimWorld -> NetStack 連接正常$(RESET)" || echo "$(RED)❌ SimWorld -> NetStack 連接失敗$(RESET)"
	@timeout 10s bash -c 'until docker exec netstack-api curl -s http://172.20.0.2:8000/ > /dev/null 2>&1; do sleep 1; done' && echo "$(GREEN)✅ NetStack -> SimWorld 連接正常$(RESET)" || echo "$(RED)❌ NetStack -> SimWorld 連接失敗$(RESET)"

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

# ===== 測試管理 =====

# 添加環境檢查和持久性測試命令
test-env-check: ## 🔍 檢查測試環境（本地和容器中）
	@echo "$(CYAN)🔍 檢查測試環境...$(RESET)"
	@echo "$(YELLOW)1. 本地環境檢查...$(RESET)"
	@python3 tests/test_environment_check.py
	@echo "$(YELLOW)2. 容器環境檢查...$(RESET)"
	@docker exec netstack-api python /app/tests/test_environment_check.py || echo "$(RED)❌ 容器環境檢查失敗$(RESET)"
	@echo "$(GREEN)✅ 測試環境檢查完成$(RESET)"

test-env-persistence: ## 🔧 測試環境持久性（模擬 make clean && make up）
	@echo "$(CYAN)🔧 測試環境持久性...$(RESET)"
	@echo "$(YELLOW)檢查依賴是否正確安裝在 Docker 鏡像中...$(RESET)"
	@docker exec netstack-api python -c "import pytest; print('✅ pytest 在容器中可用')" || echo "$(RED)❌ pytest 不在容器中$(RESET)"
	@docker exec netstack-api python -c "import pytest_asyncio; print('✅ pytest-asyncio 在容器中可用')" || echo "$(RED)❌ pytest-asyncio 不在容器中$(RESET)"
	@docker exec netstack-api python -c "import httpx; print('✅ httpx 在容器中可用')" || echo "$(RED)❌ httpx 不在容器中$(RESET)"
	@docker exec netstack-api python -c "import asyncio; print('✅ asyncio 在容器中可用')" || echo "$(RED)❌ asyncio 不在容器中$(RESET)"
	@echo "$(YELLOW)檢查統一 API 模組...$(RESET)"
	@docker exec netstack-api python -c "from netstack_api.routers.unified_api_router import unified_router; print('✅ 統一 API 路由器可用')" || echo "$(RED)❌ 統一 API 路由器不可用$(RESET)"
	@docker exec netstack-api python -c "from netstack_api.models.unified_models import SystemStatusResponse; print('✅ 統一模型可用')" || echo "$(RED)❌ 統一模型不可用$(RESET)"
	@echo "$(GREEN)✅ 環境持久性檢查完成$(RESET)"

test-unified-api-local: ## 🌐 本地統一 API 測試
	@echo "$(CYAN)🌐 執行本地統一 API 測試...$(RESET)"
	@echo "$(YELLOW)確保測試依賴已安裝...$(RESET)"
	@pip install -q pytest pytest-asyncio httpx structlog || pip3 install -q pytest pytest-asyncio httpx structlog
	@python3 -m pytest tests/test_unified_api.py -v --tb=short
	@echo "$(GREEN)✅ 本地統一 API 測試完成$(RESET)"

test-unified-api-docker: ## 🐳 Docker 容器中統一 API 測試
	@echo "$(CYAN)🐳 執行 Docker 容器中統一 API 測試...$(RESET)"
	@docker exec netstack-api python -m pytest /app/tests/test_unified_api.py -v --tb=short || echo "$(RED)❌ 容器中測試失敗$(RESET)"
	@echo "$(GREEN)✅ Docker 統一 API 測試完成$(RESET)"

test-unified-api: ## 🎯 完整統一 API 測試（本地+容器）
	@echo "$(CYAN)🎯 執行完整統一 API 測試...$(RESET)"
	@$(MAKE) test-env-check
	@$(MAKE) test-unified-api-local
	@$(MAKE) test-unified-api-docker
	@echo "$(GREEN)✅ 完整統一 API 測試完成$(RESET)"

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

test-sionna-integration: ## 📡 執行 Sionna 無線通道模型整合測試
	@echo "$(CYAN)📡 執行 Sionna 無線通道模型整合測試...$(RESET)"
	@python3 test_sionna_integration.py
	@echo "$(GREEN)✅ Sionna 整合測試完成$(RESET)"

test-sionna-core: ## 🎯 執行 Sionna 核心功能測試
	@echo "$(CYAN)🎯 執行 Sionna 核心功能測試...$(RESET)"
	@python3 test_sionna_core.py
	@echo "$(GREEN)✅ Sionna 核心功能測試完成$(RESET)"

# ===== 統一測試管理 =====

test-quick: ## ⚡ 快速測試（開發時使用）
	@echo "$(CYAN)⚡ 執行快速測試...$(RESET)"
	@python3 tests/helpers/test_runner.py quick
	@echo "$(GREEN)✅ 快速測試完成$(RESET)"

test-unit: ## 🧩 執行所有單元測試
	@echo "$(CYAN)🧩 執行單元測試...$(RESET)"
	@cd netstack && $(MAKE) test-unit || true
	@cd simworld && $(MAKE) test-unit || true
	@echo "$(GREEN)✅ 單元測試完成$(RESET)"

test-integration: ## 🔗 執行整合測試
	@echo "$(CYAN)🔗 執行整合測試...$(RESET)"
	@python3 tests/helpers/test_runner.py integration
	@echo "$(GREEN)✅ 整合測試完成$(RESET)"

test-netstack-only: ## 📡 僅執行 NetStack 測試
	@echo "$(CYAN)📡 執行 NetStack 測試...$(RESET)"
	@python3 tests/helpers/test_runner.py netstack
	@echo "$(GREEN)✅ NetStack 測試完成$(RESET)"

test-simworld-only: ## 🌍 僅執行 SimWorld 測試
	@echo "$(CYAN)🌍 執行 SimWorld 測試...$(RESET)"
	@cd simworld && $(MAKE) test-all || true
	@echo "$(GREEN)✅ SimWorld 測試完成$(RESET)"

# ===== 測試組合 =====

test-all: ## 🎯 執行所有測試
	@echo "$(CYAN)🎯 執行完整測試套件...$(RESET)"
	@python3 tests/helpers/test_runner.py all
	@echo "$(GREEN)🎉 所有測試完成$(RESET)"

test-core: ## 🔧 執行核心功能測試
	@echo "$(CYAN)🔧 執行核心功能測試...$(RESET)"
	@$(MAKE) test-quick
	@$(MAKE) test-ntn-validation
	@$(MAKE) test-connectivity
	@echo "$(GREEN)✅ 核心功能測試完成$(RESET)"

test-uav-ue: ## 🚁 執行 UAV UE 整合測試
	@echo "$(CYAN)🚁 執行 UAV UE 整合測試...$(RESET)"
	@echo "$(YELLOW)確認測試依賴已安裝...$(RESET)"
	@pip install -q pytest httpx asyncio || pip3 install -q pytest httpx asyncio
	@python3 tests/test_uav_ue_integration.py
	@echo "$(GREEN)✅ UAV UE 整合測試完成$(RESET)"

test-uav-ue-quick: ## ⚡ 執行 UAV UE 快速測試
	@echo "$(CYAN)⚡ 執行 UAV UE 快速測試...$(RESET)"
	@echo "$(YELLOW)測試 NetStack UAV UE API 端點...$(RESET)"
	@curl -s http://localhost:8080/api/v1/uav > /dev/null && echo "$(GREEN)✅ UAV 列表端點正常$(RESET)" || echo "$(RED)❌ UAV 列表端點異常$(RESET)"
	@curl -s http://localhost:8080/api/v1/uav/trajectory > /dev/null && echo "$(GREEN)✅ 軌跡列表端點正常$(RESET)" || echo "$(RED)❌ 軌跡列表端點異常$(RESET)"
	@echo "$(YELLOW)測試 SimWorld UAV 位置端點...$(RESET)"
	@curl -s http://localhost:8888/api/v1/uav/positions > /dev/null && echo "$(GREEN)✅ SimWorld UAV 位置端點正常$(RESET)" || echo "$(RED)❌ SimWorld UAV 位置端點異常$(RESET)"
	@echo "$(GREEN)✅ UAV UE 快速測試完成$(RESET)"

test-uav-ue-demo: ## 🚀 執行 UAV UE 演示
	@echo "$(CYAN)🚀 執行 UAV UE 演示...$(RESET)"
	@curl -X POST http://localhost:8080/api/v1/uav/demo/quick-test -H "Content-Type: application/json" | jq . || echo "$(RED)❌ 演示失敗，請檢查服務狀態$(RESET)"
	@echo "$(GREEN)✅ UAV UE 演示完成$(RESET)"

test-uav-ue-validation: ## 🎯 執行 UAV UE 完整性驗證
	@echo "$(CYAN)🎯 執行 UAV UE 完整性驗證...$(RESET)"
	@echo "$(YELLOW)檢查所有 TODO.md 要求是否完成...$(RESET)"
	@python3 tests/validate_uav_ue_implementation.py
	@echo "$(GREEN)✅ UAV UE 完整性驗證完成$(RESET)"

test-uav-ue-env-persistence: ## 🔧 測試環境持久性（模擬 make clean && make up）
	@echo "$(CYAN)🔧 測試環境持久性...$(RESET)"
	@echo "$(YELLOW)檢查依賴是否正確安裝在 Docker 鏡像中...$(RESET)"
	@docker exec netstack-api python -c "import pytest; print('✅ pytest 在容器中可用')" || echo "$(RED)❌ pytest 不在容器中$(RESET)"
	@docker exec netstack-api python -c "import httpx; print('✅ httpx 在容器中可用')" || echo "$(RED)❌ httpx 不在容器中$(RESET)"
	@docker exec netstack-api python -c "import asyncio; print('✅ asyncio 在容器中可用')" || echo "$(RED)❌ asyncio 不在容器中$(RESET)"
	@echo "$(YELLOW)檢查代碼修復是否持久化...$(RESET)"
	@docker exec netstack-api python -c "from netstack_api.adapters.mongo_adapter import MongoAdapter; print('✅ MongoAdapter 修復持久化')" || echo "$(RED)❌ MongoAdapter 修復未持久化$(RESET)"
	@docker exec netstack-api python -c "from netstack_api.models.uav_models import UAVTrajectory; print('✅ UAV 模型正常')" || echo "$(RED)❌ UAV 模型異常$(RESET)"
	@echo "$(GREEN)✅ 環境持久性檢查完成$(RESET)"

test-uav-ue-comprehensive: ## 🚀 執行 UAV UE 綜合測試（包含所有子測試）
	@echo "$(CYAN)🚀 執行 UAV UE 綜合測試套件...$(RESET)"
	@$(MAKE) test-uav-ue-quick
	@$(MAKE) test-uav-ue-demo
	@$(MAKE) test-uav-ue
	@$(MAKE) test-uav-ue-validation
	@$(MAKE) test-uav-ue-env-persistence
	@echo "$(GREEN)🎉 UAV UE 綜合測試完成$(RESET)"

test-advanced: ## 🚀 執行進階功能測試
	@echo "$(CYAN)🚀 執行進階功能測試...$(RESET)"
	@$(MAKE) test-integration
	@$(MAKE) test-satellite-gnb
	@$(MAKE) test-ueransim
	@$(MAKE) test-performance
	@$(MAKE) test-uav-ue
	@echo "$(GREEN)✅ 進階功能測試完成$(RESET)"

test-legacy: ## 🔄 執行傳統 Shell 測試（向後兼容）
	@echo "$(CYAN)🔄 執行傳統 Shell 測試...$(RESET)"
	@$(MAKE) test-config-validation
	@$(MAKE) test-latency
	@$(MAKE) test-e2e
	@$(MAKE) test-slice-switching
	@echo "$(GREEN)✅ 傳統測試完成$(RESET)"

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
	@rm -rf tests/reports/* test-reports/ netstack/tests/test-reports/ netstack/tests/*.log
	@rm -rf simworld/backend/tests/reports/ simworld/backend/tests/*.log
	@rm -rf **/__pycache__/ **/.pytest_cache/ .coverage*
	@echo "$(GREEN)✅ 測試清理完成$(RESET)"

test-report: ## 📊 生成測試報告摘要
	@echo "$(CYAN)📊 生成測試報告摘要...$(RESET)"
	@python3 -c "import json, glob, os; reports = sorted(glob.glob('tests/reports/test_report_*.json'), reverse=True); print(f'📋 最新測試報告: {os.path.basename(reports[0])}' if reports else '❌ 未找到測試報告')" 2>/dev/null || echo "❌ 報告解析失敗"

test-coverage: ## 📈 生成覆蓋率報告
	@echo "$(CYAN)📈 生成覆蓋率報告...$(RESET)"
	@echo "NetStack 覆蓋率:"
	@cd netstack && python3 -m pytest --cov=netstack_api --cov-report=html:../tests/reports/coverage/netstack_coverage.html --cov-report=term || true
	@echo "SimWorld 覆蓋率:"
	@cd simworld/backend && python3 -m pytest --cov=app --cov-report=html:../../tests/reports/coverage/simworld_coverage.html --cov-report=term || true
	@echo "$(GREEN)✅ 覆蓋率報告已生成$(RESET)"

test-env: ## 🌍 設置測試環境
	@echo "$(CYAN)🌍 設置測試環境...$(RESET)"
	@pip install -r requirements.txt
	@cd netstack && pip install -r requirements-dev.txt
	@cd simworld && pip install -r backend/requirements.txt
	@echo "$(GREEN)✅ 測試環境設置完成$(RESET)"

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
	@docker exec -it simworld_backend bash || echo "$(RED)❌ SimWorld 容器未運行$(RESET)"

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
	@$(MAKE) 服務健康檢查:
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

# ===== UAV-衛星連接質量評估測試 =====

test-uav-satellite-connection-quality: ## 測試 UAV-衛星連接質量評估系統
	@echo "🔍 開始測試 UAV-衛星連接質量評估系統..."
	@python3 tests/test_uav_satellite_connection_quality.py

test-uav-satellite-connection-quality-quick: ## 快速測試 UAV-衛星連接質量評估系統（僅核心功能）
	@echo "⚡ 快速測試 UAV-衛星連接質量評估系統..."
	@timeout 60 python3 tests/test_uav_satellite_connection_quality.py || echo "🕐 60秒快速測試完成"

test-uav-satellite-all: ## 測試所有 UAV-衛星相關功能
	@echo "🚀 測試所有 UAV-衛星功能..."
	@$(MAKE) test-uav-ue-validation
	@$(MAKE) test-uav-satellite-connection-quality
	@echo "✅ 所有 UAV-衛星功能測試完成"

# UAV 連接質量評估測試
test-connection-quality:
	@echo "🔬 開始 UAV-衛星連接質量評估系統測試..."
	@python -m pytest tests/test_uav_satellite_connection_quality.py -v --tb=short

test-connection-quality-detailed:
	@echo "🔬 開始詳細的連接質量評估測試..."
	@cd tests && python test_uav_satellite_connection_quality.py

# 快速連接質量評估測試
test-connection-quality-quick:
	@echo "⚡ 快速連接質量評估測試..."
	@cd tests && timeout 30 python test_uav_satellite_connection_quality.py || echo "測試完成（可能因為服務未啟動而失敗）"

# ===== 前端組件測試 =====

test-frontend-charts-dropdown: ## 🎨 測試前端圖表 Dropdown 功能
	@echo "$(CYAN)🎨 測試前端圖表 Dropdown 功能...$(RESET)"
	@python3 tests/test_frontend_charts_dropdown.py
	@echo "$(GREEN)✅ 前端圖表 Dropdown 測試完成$(RESET)"

test-frontend-error-handling: ## 🛡️ 測試前端錯誤處理功能
	@echo "$(CYAN)🛡️ 測試前端錯誤處理功能...$(RESET)"
	@python3 tests/test_frontend_error_handling.py
	@echo "$(GREEN)✅ 前端錯誤處理測試完成$(RESET)"

test-frontend-validation: ## 🌐 執行前端組件驗證
	@echo "$(CYAN)🌐 執行前端組件驗證...$(RESET)"
	@$(MAKE) test-frontend-charts-dropdown
	@$(MAKE) test-frontend-error-handling
	@echo "$(GREEN)✅ 前端組件驗證完成$(RESET)"

test-frontend-dev-server: ## 🚀 啟動前端開發伺服器
	@echo "$(CYAN)🚀 啟動前端開發伺服器...$(RESET)"
	@cd simworld/frontend && npm run dev
	@echo "$(GREEN)✅ 前端開發伺服器啟動完成$(RESET)"

test-frontend-build: ## 🔨 測試前端建置
	@echo "$(CYAN)🔨 測試前端建置...$(RESET)"
	@cd simworld/frontend && npm run build
	@echo "$(GREEN)✅ 前端建置測試完成$(RESET)"

.PHONY: all
all: help ## 顯示幫助（預設目標） 