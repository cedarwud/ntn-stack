.PHONY: help up down status logs clean test dev-up
.DEFAULT_GOAL := help

# 顏色定義
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[1;34m
NC=\033[0m # No Color

# 專案設定
PROJECT_NAME := netstack
COMPOSE_FILE := compose/core.yaml
COMPOSE_FILE_RAN := compose/ran.yaml

help: ## 顯示可用的命令
	@echo "$(GREEN)NetStack v1.0 - 可用命令：$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🆕 核心同步服務管理：$(NC)"
	@echo "  $(GREEN)start-core-sync$(NC)     啟動核心同步服務"
	@echo "  $(GREEN)check-core-sync$(NC)     檢查核心同步服務狀態"
	@echo "  $(GREEN)stop-core-sync$(NC)      停止核心同步服務"
	@echo ""
	@echo "$(CYAN)💡 核心同步服務現在會在 dev-up 和 dev-fresh 中自動啟動$(NC)"
	@echo ""

up: ## 🚀 啟動 NetStack 核心網 (不含建構)
	@echo "$(GREEN)🚀 啟動 NetStack 核心網...$(NC)"
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ 核心網啟動完成！$(NC)"
	@echo "等待服務就緒... (約 60 秒)"
	@sleep 10
	@$(MAKE) status

start-with-setup: ## 🚀 啟動並完成開發環境設置 (不含建構)
	@echo "$(GREEN)🚀 啟動並設置開發環境...$(NC)"
	@$(MAKE) up
	@$(MAKE) register-subscribers
	@$(MAKE) start-ran
	@sleep 15
	@echo "$(YELLOW)🚁 初始化 UAV 數據和網絡拓撲...$(NC)"
	@$(MAKE) init-demo-data
	@echo "$(YELLOW)⚡ 啟動核心同步服務...$(NC)"
	@$(MAKE) start-core-sync
	@echo "$(YELLOW)🚀 NetStack 核心服務已啟動 $(NC)"
	@echo "$(GREEN)✅ 開發環境設置完成，可開始測試$(NC)"

# 完整工作流程命令
dev-up: ## 🛠️ 完整的開發環境設置 (建構並啟動，保留數據)
	@echo "$(GREEN)🛠️ 設置開發環境...$(NC)"
	@$(MAKE) build
	@$(MAKE) up
	@$(MAKE) register-subscribers
	@$(MAKE) start-ran
	@sleep 15
	@echo "$(YELLOW)🚁 初始化 UAV 數據和網絡拓撲...$(NC)"
	@$(MAKE) init-demo-data
	@echo "$(YELLOW)⚡ 啟動核心同步服務...$(NC)"
	@$(MAKE) start-core-sync
	@echo "$(YELLOW)🚀 NetStack 核心服務已啟動 $(NC)"
	@echo "$(GREEN)✅ 開發環境設置完成，可開始測試$(NC)"

dev-fresh: ## 🆕 全新環境設置 (清除所有數據)
	@echo "$(GREEN)🆕 設置全新環境...$(NC)"
	@$(MAKE) clean
	@$(MAKE) build
	@$(MAKE) up
	@$(MAKE) register-subscribers
	@$(MAKE) start-ran
	@sleep 15
	@echo "$(YELLOW)🚁 初始化 UAV 數據和網絡拓撲...$(NC)"
	@$(MAKE) init-demo-data
	@echo "$(YELLOW)⚡ 啟動核心同步服務...$(NC)"
	@$(MAKE) start-core-sync
	@echo "$(YELLOW)🚀 NetStack 核心服務已啟動 $(NC)"
	@echo "$(GREEN)✅ 全新環境設置完成，可開始測試$(NC)"

down: ## 🧹 清理容器但保留數據庫資料
	@echo "$(YELLOW)🧹 清理 NetStack 資源 (保留數據)...$(NC)"
	@echo "$(YELLOW)NetStack 核心服務運行中$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down --remove-orphans 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) down --remove-orphans
	docker network prune -f
	@echo "$(GREEN)✅ 清理完成 (數據已保留)$(NC)"

down-v: ## 🛑 停止 NetStack
	@echo "$(YELLOW)🛑 停止 NetStack...$(NC)"
	@echo "$(YELLOW)NetStack 資源管理正常$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down -v --remove-orphans 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker volume prune -f
	docker network prune -f
	@echo "$(GREEN)✅ NetStack 已停止$(NC)"

clean: ## 🧹 清理所有容器和資料
	@echo "$(YELLOW)🧹 清理 NetStack 資源...$(NC)"
	@echo "$(YELLOW)NetStack 資源管理正常$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down -v --remove-orphans 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker volume prune -f
	docker network prune -f
	docker rmi netstack-api:latest 2>/dev/null || true
	@echo "$(GREEN)✅ 清理完成$(NC)"

clean-i: ## 🧹 清理所有容器、資料及映像檔
	@echo "$(YELLOW)🧹 清理 NetStack 所有資源 (包含映像檔)...$(NC)"
	@echo "$(YELLOW)NetStack 資源管理正常$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down -v --rmi all --remove-orphans 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) down -v --rmi all --remove-orphans
	docker volume prune -f
	docker network prune -f
	@echo "$(GREEN)✅ 所有 NetStack 資源及映像檔清理完成$(NC)"

clean-data-only: ## 🗑️ 僅清理數據庫資料 (保留容器)
	@echo "$(RED)🗑️ 清理數據庫資料...$(NC)"
	@echo "$(YELLOW)⚠️ 警告: 這將刪除所有用戶資料和監控數據！$(NC)"
	@read -p "確定要繼續嗎？(y/N): " choice; \
	if [ "$$choice" = "y" ] || [ "$$choice" = "Y" ]; then \
		docker volume rm -f netstack_mongo_data netstack_redis_data netstack_prometheus_data 2>/dev/null || true; \
		echo "$(GREEN)✅ 數據清理完成$(NC)"; \
	else \
		echo "$(YELLOW)已取消數據清理$(NC)"; \
	fi

status: ## 📊 檢查服務狀態
	@echo "$(BLUE)📊 NetStack 服務狀態：$(NC)"
	@docker compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "$(BLUE)🏥 健康檢查：$(NC)"
	@curl -s http://localhost:8080/health 2>/dev/null || echo "$(RED)❌ API 服務未就緒$(NC)"
	@echo ""

logs: ## 📋 查看所有 NetStack 核心服務的日誌
	@echo "$(BLUE)📋 查看所有 NetStack 服務日誌...$(NC)"
	@echo "$(YELLOW)使用 Ctrl+C 退出日誌查看$(NC)"
	@trap 'echo "結束日誌查看"; exit 0' INT; \
	( \
		docker compose -f $(COMPOSE_FILE) logs -f & \
		echo "$(CYAN)NetStack 核心服務日誌$(NC)" & \
		wait \
	)

logs-api: ## 📋 查看 API 服務日誌
	docker compose -f $(COMPOSE_FILE) logs -f netstack-api

register-subscribers: ## 👤 註冊所有預定義測試用戶 (eMBB, uRLLC, mMTC)
	@echo "$(GREEN)👤 註冊所有預定義測試用戶 (包含三種切片類型)...$(NC)"
	@docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "db.subscribers.deleteMany({});" >/dev/null 2>&1 || true
	@./scripts/register_subscriber.sh >/dev/null 2>&1 || true
	@echo "$(BLUE)檢查註冊結果：$(NC)"
	@docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "print('總用戶數: ' + db.subscribers.countDocuments({})); var embb = db.subscribers.countDocuments({'slice.sst': 1}); var urllc = db.subscribers.countDocuments({'slice.sst': 2}); var mmtc = db.subscribers.countDocuments({'slice.sst': 3}); print('eMBB 用戶: ' + embb + ', uRLLC 用戶: ' + urllc + ', mMTC 用戶: ' + mmtc);" 2>/dev/null || echo "無法連接資料庫"
	@docker compose -f $(COMPOSE_FILE) restart amf udm udr ausf >/dev/null 2>&1
	@sleep 10
	@echo "$(GREEN)✅ 用戶註冊和服務重啟完成$(NC)"

add-subscriber: ## 👤 新增單一測試用戶 (使用: make add-subscriber IMSI=.. KEY=.. OPC=.. APN=.. SST=.. SD=..)
	@echo "$(GREEN)👤 新增單一測試用戶...$(NC)"
	@if [ -z "$(IMSI)" ] || [ -z "$(KEY)" ] || [ -z "$(OPC)" ]; then \
		echo "$(RED)❌ 缺少必要參數$(NC)"; \
		echo "使用方式: make add-subscriber IMSI=999700000000001 KEY=465B5CE8B199B49FAA5F0A2EE238A6BC OPC=E8ED289DEBA952E4283B54E88E6183CA [APN=internet] [SST=1] [SD=0x111111]"; \
		exit 1; \
	fi
	@APN_VAL=$${APN:-internet}; \
	SST_VAL=$${SST:-1}; \
	SD_VAL=$${SD:-0x111111}; \
	./scripts/register_subscriber.sh add $(IMSI) $(KEY) $(OPC) $$APN_VAL $$SST_VAL $$SD_VAL
	@echo "$(GREEN)✅ 用戶新增完成$(NC)"

show-subscribers: ## 👥 顯示用戶統計摘要
	@echo "$(BLUE)👥 用戶統計摘要：$(NC)"
	@./scripts/show_subscribers.sh summary

show-subscribers-detail: ## 📋 顯示詳細用戶列表
	@echo "$(BLUE)📋 詳細用戶列表：$(NC)"
	@./scripts/show_subscribers.sh list

show-subscribers-slice: ## 📊 顯示特定 Slice 的用戶
	@echo "$(BLUE)📊 特定 Slice 的用戶清單：$(NC)"
	@if [ -z "$(SLICE)" ]; then \
		echo "$(RED)❌ 請指定 Slice 類型$(NC)"; \
		echo "使用方式: make show-subscribers-slice SLICE=eMBB 或 SLICE=uRLLC 或 SLICE=mMTC"; \
		exit 1; \
	fi
	@./scripts/show_subscribers.sh slice $(SLICE)

search-subscriber: ## 🔍 搜尋特定用戶
	@echo "$(BLUE)🔍 搜尋用戶：$(NC)"
	@if [ -z "$(IMSI)" ]; then \
		echo "$(RED)❌ 請提供 IMSI$(NC)"; \
		echo "使用方式: make search-subscriber IMSI=999700000000001"; \
		exit 1; \
	fi
	@./scripts/show_subscribers.sh search $(IMSI)

export-subscribers: ## 📤 導出用戶資料
	@echo "$(BLUE)📤 導出用戶資料：$(NC)"
	@FILE_VAL=$${FILE:-subscribers_export.json}; \
	./scripts/show_subscribers.sh export $$FILE_VAL

delete-subscribers: ## 🗑️ 刪除所有測試用戶
	@echo "$(RED)🗑️ 刪除所有測試用戶...$(NC)"
	@-./scripts/register_subscriber.sh delete || true
	@echo "$(GREEN)✅ 測試用戶已刪除$(NC)"

subscriber-docs: ## 📘 顯示完整的用戶管理功能文檔
	@echo "$(BLUE)📘 NetStack 用戶管理完整文檔$(NC)"
	@echo "$(YELLOW)======================================================$(NC)"
	@echo "$(CYAN)1. register_subscriber.sh$(NC) - 用戶註冊與管理腳本"
	@echo "$(YELLOW)------------------------------------------------------$(NC)"
	@echo "- $(GREEN)register$(NC): 註冊所有預定義測試用戶"
	@echo "  $(MAGENTA)make register-subscribers$(NC)"
	@echo ""
	@echo "- $(GREEN)add$(NC): 新增單一用戶"
	@echo "  $(MAGENTA)make add-subscriber IMSI=.. KEY=.. OPC=.. [APN=..] [SST=..] [SD=..]$(NC)"
	@echo ""
	@echo "- $(GREEN)delete$(NC): 刪除所有測試用戶"
	@echo "  $(MAGENTA)make delete-subscribers$(NC)"
	@echo ""
	@echo "- $(GREEN)show$(NC): 簡易顯示已註冊用戶列表"
	@echo "  直接執行: $(MAGENTA)./scripts/register_subscriber.sh show$(NC)"
	@echo ""
	@echo "$(YELLOW)======================================================$(NC)"
	@echo "$(CYAN)2. show_subscribers.sh$(NC) - 用戶查詢與顯示腳本"
	@echo "$(YELLOW)------------------------------------------------------$(NC)"
	@echo "- $(GREEN)summary$(NC): 顯示用戶統計摘要"
	@echo "  $(MAGENTA)make show-subscribers$(NC)"
	@echo ""
	@echo "- $(GREEN)list$(NC): 顯示詳細用戶列表"
	@echo "  $(MAGENTA)make show-subscribers-detail$(NC)"
	@echo ""
	@echo "- $(GREEN)slice$(NC): 顯示特定 Slice 的用戶 (eMBB 或 uRLLC)"
	@echo "  $(MAGENTA)make show-subscribers-slice SLICE=eMBB$(NC)"
	@echo "  $(MAGENTA)make show-subscribers-slice SLICE=uRLLC$(NC)"
	@echo "  $(MAGENTA)make show-subscribers-slice SLICE=mMTC$(NC)"
	@echo ""
	@echo "- $(GREEN)search$(NC): 搜尋特定用戶"
	@echo "  $(MAGENTA)make search-subscriber IMSI=999700000000001$(NC)"
	@echo ""
	@echo "- $(GREEN)export$(NC): 導出用戶資料"
	@echo "  $(MAGENTA)make export-subscribers [FILE=subscribers.json]$(NC)"
	@echo ""
	@echo "$(YELLOW)======================================================$(NC)"

subscriber-help: ## 📚 顯示用戶管理相關指令說明
	@echo "$(BLUE)📚 NetStack 用戶管理指令說明：$(NC)"
	@echo ""
	@echo "$(GREEN)register-subscribers$(NC): 註冊所有預定義測試用戶"
	@echo "$(GREEN)add-subscriber$(NC): 新增單一測試用戶 (需提供 IMSI, KEY, OPC 參數)"
	@echo "$(GREEN)show-subscribers$(NC): 顯示用戶統計摘要"
	@echo "$(GREEN)show-subscribers-detail$(NC): 顯示詳細用戶列表"
	@echo "$(GREEN)show-subscribers-slice$(NC): 顯示特定 Slice 的用戶 (需提供 SLICE 參數)"
	@echo "$(GREEN)search-subscriber$(NC): 搜尋特定用戶 (需提供 IMSI 參數)"
	@echo "$(GREEN)export-subscribers$(NC): 導出用戶資料 (可選提供 FILE 參數)"
	@echo "$(GREEN)delete-subscribers$(NC): 刪除所有測試用戶"
	@echo "$(GREEN)subscriber-docs$(NC): 顯示完整的用戶管理功能文檔"
	@echo ""
	@echo "$(YELLOW)範例：$(NC)"
	@echo "make add-subscriber IMSI=999700000000001 KEY=465B5CE8B199B49FAA5F0A2EE238A6BC OPC=E8ED289DEBA952E4283B54E88E6183CA"
	@echo "make show-subscribers-slice SLICE=eMBB"
	@echo "make search-subscriber IMSI=999700000000001"
	@echo "make export-subscribers FILE=subscribers.json"
	@echo ""

start-ran: ## 📡 啟動 RAN 模擬器
	@echo "$(GREEN)📡 啟動 RAN 模擬器...$(NC)"
	@if ! docker ps --format '{{.Names}}' | grep -q "netstack-amf"; then \
		echo "$(YELLOW)⚠️ 警告: 核心網 (AMF) 未在運行。RAN 模擬器可能會啟動失敗。$(NC)"; \
		echo "$(YELLOW)建議: 請先運行 'make up' 啟動核心網，再啟動 RAN 模擬器。$(NC)"; \
		read -p "是否繼續啟動 RAN 模擬器？(y/n) " choice; \
		if [ "$$choice" != "y" ]; then \
			echo "$(YELLOW)已取消啟動 RAN 模擬器。$(NC)"; \
			exit 0; \
		fi \
	fi
	docker compose -f $(COMPOSE_FILE_RAN) up -d --remove-orphans
	@echo "$(GREEN)✅ RAN 模擬器啟動完成$(NC)"

stop-ran: ## 📡 停止 RAN 模擬器  
	@echo "$(YELLOW)📡 停止 RAN 模擬器...$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down --remove-orphans
	@echo "$(GREEN)✅ RAN 模擬器已停止$(NC)"

# ===== 測試指令 (已移至根目錄統一管理) =====
# 注意：測試指令和測試文件已完全移至根目錄的統一測試系統
# 請使用根目錄的以下指令：
#   cd ../ && make test            - 執行完整測試套件  
#   cd ../ && make test-netstack   - 執行 NetStack 測試
#   cd ../ && make test-legacy     - 執行傳統測試 (原 shell 腳本功能)
#   cd ../ && make test-integration - 執行整合測試

test-deprecated: ## ⚠️ 測試指令和文件已移至根目錄統一管理
	@echo "$(YELLOW)⚠️ NetStack 測試已完全移至根目錄統一管理$(NC)"
	@echo "$(BLUE)📁 測試文件位置：$(NC)"
	@echo "  原 netstack/tests/ → tests/shell/netstack/"
	@echo "  測試指令已整合至 tests/Makefile"
	@echo ""
	@echo "$(BLUE)請使用以下指令：$(NC)"
	@echo "  $(GREEN)cd ../tests && make help$(NC)              - 查看所有測試指令"
	@echo "  $(GREEN)cd ../tests && make test-smoke$(NC)        - 快速煙霧測試"
	@echo "  $(GREEN)cd ../tests && make test-netstack-only$(NC) - 僅執行 NetStack 測試"
	@echo "  $(GREEN)cd ../tests && make test-shell-netstack$(NC) - NetStack Shell 腳本測試"
	@echo ""
	@echo "$(CYAN)💡 統一測試系統優勢：$(NC)"
	@echo "  - 🎯 統一管理所有測試（NetStack + SimWorld）"
	@echo "  - 📊 整合報告生成和覆蓋率分析"
	@echo "  - 🔄 支援 CI/CD 自動化測試"
	@echo "  - 🧪 提供多種測試套件（煙霧/快速/完整）"

lint: ## 🔍 程式碼檢查
	@echo "$(BLUE)🔍 執行程式碼檢查...$(NC)"
	docker compose -f $(COMPOSE_FILE) run --rm netstack-api sh -c "cd netstack_api && python -m black . --check && python -m isort . --check-only && python -m flake8 . && python -m mypy ."

format: ## ✨ 格式化程式碼
	@echo "$(BLUE)✨ 格式化程式碼...$(NC)"
	docker compose -f $(COMPOSE_FILE) run --rm netstack-api sh -c "cd netstack_api && python -m black . && python -m isort ."

clean-test-runs: ## 🧹 清理測試執行所建立的容器和服務
	@echo "$(YELLOW)🧹 Cleaning up containers and services from test runs...$(NC)"
	@-docker rm netstack_api_test_unit || true
	@-docker rm netstack_api_test_integration || true
	@echo "$(YELLOW)Bringing down any services potentially started by tests defined in $(COMPOSE_FILE)...$(NC)"
	@-docker compose -f $(COMPOSE_FILE) down --remove-orphans
	@echo "$(GREEN)✅ Test run cleanup complete.$(NC)"

pull: ## 📥 拉取所有必要的第三方映像檔
	@echo "$(GREEN)📥 拉取所有必要的第三方映像檔...$(NC)"
	@echo "$(BLUE)  - 拉取 Open5GS 核心網映像...$(NC)"
	docker pull gradiant/open5gs:2.7.5
	@echo "$(BLUE)  - 拉取 MongoDB 映像...$(NC)"
	docker pull mongo:6.0
	@echo "$(BLUE)  - 拉取 Redis 映像...$(NC)"
	docker pull redis:7-alpine
	@echo "$(BLUE)  - 拉取 PostgreSQL 映像...$(NC)"
	docker pull postgres:16-alpine
	@echo "$(GREEN)✅ 所有第三方映像檔拉取完成$(NC)"

build: pull ## 🏗️ 建置所有 NetStack 核心映像 (先拉取第三方映像)
	@echo "$(GREEN)🏗️ 建置 NetStack 所有相關映像...$(NC)"
	@echo "$(BLUE)  - 建置核心網 API 映像 (production 階段)...$(NC)"
	docker build -t netstack-api:latest -f docker/Dockerfile --target production .
	@echo "$(BLUE)  - NetStack 核心映像建構完成$(NC)"
	@echo "$(GREEN)✅ 所有 NetStack 映像建置完成$(NC)"

build-n: pull ## 🏗️ 建置所有 NetStack 映像 (不使用快取，先拉取第三方映像)
	@echo "$(GREEN)🏗️ 建置 NetStack 所有相關映像 (不使用快取)...$(NC)"
	@echo "$(BLUE)  - 建置核心網 API 映像 (production 階段)...$(NC)"
	docker build -t netstack-api:latest -f docker/Dockerfile --target production . --no-cache
	@echo "$(BLUE)  - NetStack 核心映像建構完成$(NC)"
	@echo "$(GREEN)✅ 所有 NetStack 映像建置完成 (不使用快取)$(NC)"

push: ## 📤 推送映像到 Registry
	@echo "$(GREEN)📤 推送映像...$(NC)"
	@if [ -z "$(REGISTRY)" ]; then \
		echo "$(RED)❌ 請設定 REGISTRY 環境變數$(NC)"; \
		exit 1; \
	fi
	docker tag netstack-api:latest $(REGISTRY)/netstack-api:latest
	docker push $(REGISTRY)/netstack-api:latest

docs: ## 📚 生成 API 文件
	@echo "$(BLUE)📚 生成 API 文件...$(NC)"
	docker compose -f $(COMPOSE_FILE) run --rm -v $(shell pwd)/docs:/app/docs netstack-api sh -c "cd netstack_api && python -c 'from main import app; import json; print(json.dumps(app.openapi(), indent=2))' > /app/docs/openapi.json"
	@echo "$(GREEN)✅ API 文件已生成至 docs/openapi.json$(NC)"

monitor: ## 📊 開啟監控面板
	@echo "$(BLUE)📊 開啟監控面板...$(NC)"
	@echo "Swagger UI: http://localhost:8080/docs"
	@echo "Prometheus: http://localhost:9090"
	@echo "Open5GS WebUI: http://localhost:9999"

attach-ue: ## 📱 連接到 UE 容器
	@echo "$(BLUE)📱 連接到 UE 容器...$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) exec ues1 /bin/bash

ping-test: ## 🏓 執行 Ping 測試
	@echo "$(BLUE)🏓 執行 Ping 測試...$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) exec ues1 ping -c 5 -I uesimtun0 8.8.8.8

backup: ## 💾 備份配置
	@echo "$(BLUE)💾 備份配置...$(NC)"
	tar -czf netstack-backup-$(shell date +%Y%m%d_%H%M%S).tar.gz config/ compose/ scripts/
	@echo "$(GREEN)✅ 配置已備份$(NC)"

verify-setup: ## ✅ 驗證環境設置是否正確
	@echo "$(BLUE)✅ 驗證環境設置...$(NC)"
	@echo "1. 檢查核心網服務狀態..."
	@$(MAKE) status
	@echo ""
	@echo "2. 檢查用戶註冊狀態..."
	@$(MAKE) show-subscribers
	@echo ""
	@echo "3. 測試 UE 連線 (使用根目錄統一測試)..."
	@cd ../ && make test-netstack
	@echo "$(GREEN)✅ 環境驗證完成$(NC)"

diagnose: ## 🔍 診斷 UE 連線問題
	@echo "$(BLUE)🔍 執行 UE 連線診斷...$(NC)"
	@./scripts/diagnose_ue_connectivity.sh

fix-connectivity: ## 🔧 自動修復常見連線問題
	@echo "$(YELLOW)🔧 自動修復 UE 連線問題...$(NC)"
	@echo "步驟 1: 重新註冊用戶..."
	@$(MAKE) register-subscribers
	@echo "步驟 2: 重啟 RAN 模擬器..."
	@$(MAKE) stop-ran
	@sleep 5
	@$(MAKE) start-ran
	@echo "步驟 3: 等待服務穩定..."
	@sleep 15
	@echo "步驟 4: 測試連線 (使用根目錄統一測試)..."
	@cd ../ && make test-netstack
	@echo "$(GREEN)✅ 修復完成$(NC)"

init-demo-data: ## 🚁 初始化演示數據 (UAV、軌跡、網絡拓撲)
	@echo "$(GREEN)🚁 初始化 UAV 演示數據...$(NC)"
	@echo "等待 API 服務就緒..."
	@sleep 5
	@-curl -s -X POST http://localhost:8080/api/v1/uav/demo/quick-test -H "Content-Type: application/json" > /dev/null 2>&1 && echo "$(GREEN)✅ UAV 演示數據初始化成功$(NC)" || echo "$(YELLOW)⚠️ UAV 演示數據初始化失敗 (可能需要手動執行)$(NC)"
	@-curl -s -X POST http://localhost:8080/api/v1/mesh/demo/quick-test -H "Content-Type: application/json" > /dev/null 2>&1 && echo "$(GREEN)✅ Mesh 網絡拓撲初始化成功$(NC)" || echo "$(YELLOW)⚠️ Mesh 網絡拓撲初始化失敗 (可能需要手動執行)$(NC)"
	@-curl -s -X POST http://localhost:8080/api/v1/uav-mesh-failover/demo/quick-test -H "Content-Type: application/json" > /dev/null 2>&1 && echo "$(GREEN)✅ UAV 備援機制演示數據初始化成功$(NC)" || echo "$(YELLOW)⚠️ UAV 備援機制演示數據初始化失敗 (可能需要手動執行)$(NC)"
	@echo "$(BLUE)📊 初始化結果摘要：$(NC)"
	@echo "  - UAV 演示數據 (軌跡、UAV 狀態)"
	@echo "  - Mesh 網絡拓撲"
	@echo "  - UAV 備援機制演示"
	@echo "$(CYAN)💡 您可以在 dashboard 中查看這些初始化的數據$(NC)"

start-core-sync: ## ⚡ 啟動核心同步服務
	@echo "$(GREEN)⚡ 啟動核心同步服務...$(NC)"
	@echo "等待 API 服務就緒..."
	@sleep 3
	@-curl -s -X POST http://localhost:8080/api/v1/core-sync/service/start \
		-H "Content-Type: application/json" \
		-d '{"signaling_free_mode": true, "binary_search_enabled": true, "max_sync_error_ms": 10.0, "auto_resync_enabled": true, "debug_logging": false}' \
		> /dev/null 2>&1 && echo "$(GREEN)✅ 核心同步服務啟動成功$(NC)" || echo "$(YELLOW)⚠️ 核心同步服務啟動失敗 (可能需要手動執行)$(NC)"
	@echo "$(BLUE)📊 檢查同步服務狀態：$(NC)"
	@sleep 2
	@-curl -s http://localhost:8080/api/v1/core-sync/status 2>/dev/null | grep -q '"is_running": true' && echo "$(GREEN)✅ 核心同步服務運行中$(NC)" || echo "$(YELLOW)⏳ 核心同步服務仍在初始化$(NC)"

check-core-sync: ## 📊 檢查核心同步服務狀態
	@echo "$(BLUE)📊 核心同步服務狀態：$(NC)"
	@curl -s http://localhost:8080/api/v1/core-sync/status 2>/dev/null || echo "$(RED)❌ 無法連接到核心同步服務$(NC)"

stop-core-sync: ## 🛑 停止核心同步服務
	@echo "$(YELLOW)🛑 停止核心同步服務...$(NC)"
	@-curl -s -X POST http://localhost:8080/api/v1/core-sync/service/stop -H "Content-Type: application/json" > /dev/null 2>&1 && echo "$(GREEN)✅ 核心同步服務已停止$(NC)" || echo "$(YELLOW)⚠️ 核心同步服務停止失敗$(NC)"