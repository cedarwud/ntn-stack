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

start: all-start ## 啟動所有服務

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
	@echo "$(YELLOW)⏳ 先構建 NetStack API 映像...$(RESET)"
	@cd $(NETSTACK_DIR) && docker build -t netstack-api:latest -f docker/Dockerfile .
	@echo "$(YELLOW)⏳ 啟動 NetStack 服務...$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml up -d
	@echo "$(GREEN)✅ NetStack 服務已啟動$(RESET)"

simworld-start: ## 啟動 SimWorld 服務
	@echo "$(BLUE)🚀 啟動 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose up -d
	@echo "$(GREEN)✅ SimWorld 服務已啟動$(RESET)"

# ===== 服務停止 =====

stop: all-stop ## 停止所有服務

all-stop: ## 停止 NetStack 和 SimWorld
	@echo "$(CYAN)🛑 停止所有 NTN Stack 服務...$(RESET)"
	@$(MAKE) netstack-stop
	@$(MAKE) simworld-stop
	@echo "$(GREEN)✅ 所有服務已停止$(RESET)"

netstack-stop: ## 停止 NetStack 服務
	@echo "$(BLUE)🛑 停止 NetStack 服務...$(RESET)"
	@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml down
	@echo "$(GREEN)✅ NetStack 服務已停止$(RESET)"

simworld-stop: ## 停止 SimWorld 服務
	@echo "$(BLUE)🛑 停止 SimWorld 服務...$(RESET)"
	@cd $(SIMWORLD_DIR) && docker compose down
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

test: test-docker ## 執行完整的 Docker 化測試套件

test-docker: ## 執行完整的 Docker 化測試套件
	@echo "$(CYAN)🧪 執行完整的 Docker 化測試套件...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@echo "$(GREEN)✅ 測試完成，報告可在 test-reports/ 目錄中查看$(RESET)"

test-quick: ## 執行快速測試（只測試核心功能）
	@echo "$(CYAN)⚡ 執行快速測試...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/test_integration.py::TestNTNStackIntegration::test_services_health -v
	@echo "$(GREEN)✅ 快速測試完成$(RESET)"

test-unit: ## 執行單元測試
	@echo "$(CYAN)🔬 執行單元測試...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/ -m "not integration" -v
	@echo "$(GREEN)✅ 單元測試完成$(RESET)"

test-integration: ## 執行整合測試
	@echo "$(CYAN)🔗 執行整合測試...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/test_integration.py -v
	@echo "$(GREEN)✅ 整合測試完成$(RESET)"

test-netstack: ## 測試 NetStack API 功能
	@echo "$(CYAN)🔧 測試 NetStack API 功能...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/test_netstack_api.py -v
	@echo "$(GREEN)✅ NetStack 測試完成$(RESET)"

test-simworld: ## 測試 SimWorld API 功能
	@echo "$(CYAN)🌍 測試 SimWorld API 功能...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/test_simworld_api.py -v
	@echo "$(GREEN)✅ SimWorld 測試完成$(RESET)"

test-satellite-mapping: ## 測試衛星映射功能
	@echo "$(CYAN)🛰️  測試衛星映射功能...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/test_netstack_api.py::TestNetStackAPI::test_satellite_gnb_mapping -v
	@echo "$(GREEN)✅ 衛星映射測試完成$(RESET)"

test-oneweb: ## 測試 OneWeb 星座功能
	@echo "$(CYAN)🌐 測試 OneWeb 星座功能...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/test_netstack_api.py::TestNetStackAPI::test_oneweb_constellation_initialize -v
	@echo "$(GREEN)✅ OneWeb 星座測試完成$(RESET)"

test-legacy: ## 執行 NetStack 傳統測試 (原 shell 腳本功能的 pytest 版本)
	@echo "$(CYAN)🔄 執行 NetStack 傳統測試...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		python -m pytest tests/test_netstack_legacy.py -v
	@echo "$(GREEN)✅ NetStack 傳統測試執行完成$(RESET)"

test-netstack-shell: ## 執行 NetStack Shell 腳本測試
	@echo "$(CYAN)🐚 執行 NetStack Shell 腳本測試...$(RESET)"
	@mkdir -p test-reports
	@docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
		bash -c "cd netstack/tests && ./quick_ntn_validation.sh && ./test_connectivity.sh"
	@echo "$(GREEN)✅ NetStack Shell 腳本測試完成$(RESET)"

test-netstack-full: ## 執行完整 NetStack 測試（Python + Shell）
	@echo "$(CYAN)🔧 執行完整 NetStack 測試...$(RESET)"
	@$(MAKE) test-netstack
	@$(MAKE) test-netstack-shell
	@echo "$(GREEN)✅ 完整 NetStack 測試完成$(RESET)"

test-reports: ## 啟動測試報告服務器
	@echo "$(CYAN)📊 啟動測試報告服務器...$(RESET)"
	@docker compose -f docker-compose.test.yml up test-reporter -d
	@echo "$(GREEN)✅ 測試報告可在 http://localhost:8090 查看$(RESET)"

test-clean: ## 清理測試環境
	@echo "$(CYAN)🧹 清理測試環境...$(RESET)"
	@docker compose -f docker-compose.test.yml down -v --remove-orphans
	@docker system prune -f --filter "label=com.docker.compose.project=ntn-stack-test"
	@echo "$(GREEN)✅ 測試環境清理完成$(RESET)"

# ===== 部署和運維 =====

deploy: ## 部署生產環境
	@echo "$(CYAN)🚀 部署 NTN Stack 生產環境...$(RESET)"
	@$(MAKE) build
	@$(MAKE) start
	@$(MAKE) test-quick
	@echo "$(GREEN)✅ 生產環境部署完成$(RESET)"

down: stop ## 停止所有服務（別名）

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