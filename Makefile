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

fresh-up: clean-i build-n up ## 重新啟動所有服務

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
	@docker image prune -f
	@docker network prune -f
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
        health-check metrics api-docs ps top exec-netstack exec-simworld version prune backup deploy \
        dev-setup dev-start dev-logs install netstack-install simworld-install verify-network-connection fix-network-connection 