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

up: build ## 🚀 啟動 NetStack 核心網
	@echo "$(GREEN)🚀 啟動 NetStack 核心網...$(NC)"
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ 核心網啟動完成！$(NC)"
	@echo "等待服務就緒... (約 60 秒)"
	@sleep 10
	@$(MAKE) status

# 完整工作流程命令
dev-up: ## 🛠️ 完整的開發環境設置 (保留數據)
	@echo "$(GREEN)🛠️ 設置開發環境...$(NC)"
	@$(MAKE) down
	@$(MAKE) up
	@$(MAKE) register-subscribers
	@$(MAKE) start-ran
	@sleep 15
	@echo "$(GREEN)✅ 開發環境設置完成，可開始測試$(NC)"

dev-fresh: ## 🆕 全新環境設置 (清除所有數據)
	@echo "$(GREEN)🆕 設置全新環境...$(NC)"
	@$(MAKE) clean
	@$(MAKE) up
	@$(MAKE) register-subscribers
	@$(MAKE) start-ran
	@sleep 15
	@echo "$(GREEN)✅ 全新環境設置完成，可開始測試$(NC)"

down: ## 🧹 清理容器但保留數據庫資料
	@echo "$(YELLOW)🧹 清理 NetStack 資源 (保留數據)...$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) down
	docker network prune -f
	@echo "$(GREEN)✅ 清理完成 (數據已保留)$(NC)"

down-v: ## 🛑 停止 NetStack
	@echo "$(YELLOW)🛑 停止 NetStack...$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down -v 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) down -v
	docker volume prune -f
	docker network prune -f
	@echo "$(GREEN)✅ NetStack 已停止$(NC)"

clean: ## 🧹 清理所有容器和資料
	@echo "$(YELLOW)🧹 清理 NetStack 資源...$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down -v 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) down -v
	docker volume prune -f
	docker network prune -f
	docker rmi netstack-api:latest 2>/dev/null || true
	@echo "$(GREEN)✅ 清理完成$(NC)"

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

logs: ## 📋 查看服務日誌
	@echo "$(BLUE)📋 NetStack 服務日誌：$(NC)"
	docker compose -f $(COMPOSE_FILE) logs -f

logs-api: ## 📋 查看 API 服務日誌
	docker compose -f $(COMPOSE_FILE) logs -f netstack-api

register-subscribers: ## 👤 註冊所有預定義測試用戶 (eMBB, uRLLC, mMTC)
	@echo "$(GREEN)👤 註冊所有預定義測試用戶 (包含三種切片類型)...$(NC)"
	@echo "$(YELLOW)清理並檢查資料庫狀態...$(NC)"
	@echo "檢查現有用戶數量..."
	@docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "print('刪除前用戶數: ' + db.subscribers.countDocuments({}));" 2>/dev/null || echo "無法連接資料庫"
	@echo "刪除現有用戶數據..."
	@docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "var result = db.subscribers.deleteMany({}); print('已刪除用戶數: ' + result.deletedCount);" 2>/dev/null || echo "無法連接資料庫"
	@echo "$(YELLOW)開始註冊三種切片的用戶 (eMBB, uRLLC, mMTC)...$(NC)"
	@-./scripts/register_subscriber.sh || true
	@echo "$(GREEN)✅ 用戶註冊完成$(NC)"
	@echo "$(BLUE)檢查註冊結果：$(NC)"
	@docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "print('總用戶數: ' + db.subscribers.countDocuments({})); var embb = db.subscribers.countDocuments({'slice.sst': 1}); var urllc = db.subscribers.countDocuments({'slice.sst': 2}); var mmtc = db.subscribers.countDocuments({'slice.sst': 3}); print('eMBB 用戶: ' + embb + ', uRLLC 用戶: ' + urllc + ', mMTC 用戶: ' + mmtc);" 2>/dev/null || echo "無法連接資料庫"
	@echo "$(YELLOW)重啟核心網服務以確保用戶資料生效...$(NC)"
	@docker compose -f $(COMPOSE_FILE) restart amf udm udr ausf
	@sleep 10
	@echo "$(GREEN)✅ 服務重啟完成，用戶資料已生效$(NC)"

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
	docker compose -f $(COMPOSE_FILE_RAN) up -d
	@echo "$(GREEN)✅ RAN 模擬器啟動完成$(NC)"

stop-ran: ## 📡 停止 RAN 模擬器  
	@echo "$(YELLOW)📡 停止 RAN 模擬器...$(NC)"
	docker compose -f $(COMPOSE_FILE_RAN) down
	@echo "$(GREEN)✅ RAN 模擬器已停止$(NC)"

test-e2e: ## 🧪 執行端到端測試
	@echo "$(BLUE)🧪 執行 E2E 測試...$(NC)"
	@./tests/e2e_netstack.sh

test-connectivity: ## 🌐 測試 UE 連線
	@echo "$(BLUE)🌐 測試 UE 連線...$(NC)"
	@./tests/test_connectivity.sh

test-performance: ## ⚡ 執行效能測試
	@echo "$(BLUE)⚡ 執行效能測試...$(NC)"
	@./tests/performance_test.sh

test-slice-switch: ## 🔀 執行 Slice 切換測試 (確保無註冊步驟)
	@echo "$(BLUE)🔀 執行 Slice 切換測試 (via test-slice-switch)...$(NC)"
	@./tests/slice_switching_test.sh

test-ntn-latency: ## 🛰️ 執行 NTN 高延遲場景測試
	@echo "$(BLUE)🛰️ 執行 NTN 高延遲場景測試...$(NC)"
	@./tests/ntn_latency_test.sh

test-ueransim-config: ## 📡 執行 UERANSIM 動態配置測試  
	@echo "$(BLUE)📡 執行 UERANSIM 動態配置測試...$(NC)"
	@./tests/ueransim_config_test.sh

test-ntn-config-validation: ## ✅ 執行 NTN 配置驗證測試
	@echo "$(BLUE)✅ 執行 NTN 配置驗證測試...$(NC)"
	@./tests/ntn_config_validation_test.sh

test-quick-ntn-validation: ## ⚡ 執行快速 NTN 驗證測試
	@echo "$(BLUE)⚡ 執行快速 NTN 驗證測試...$(NC)"
	@./tests/quick_ntn_validation.sh

test-all-ntn: ## 🚀 執行所有 NTN 相關測試
	@echo "$(GREEN)🚀 執行所有 NTN 相關測試...$(NC)"
	@$(MAKE) test-ntn-latency
	@$(MAKE) test-ueransim-config
	@$(MAKE) test-ntn-config-validation
	@$(MAKE) test-quick-ntn-validation
	@echo "$(GREEN)✅ 所有 NTN 測試完成$(NC)"

test-all: ## 🧪 執行所有測試 (包含 NTN 測試)
	@echo "$(GREEN)🧪 執行完整測試套件...$(NC)"
	@$(MAKE) test-e2e
	@$(MAKE) test-connectivity
	@$(MAKE) test-performance
	@$(MAKE) test-slice-switch
	@$(MAKE) test-all-ntn
	@echo "$(GREEN)✅ 所有測試完成$(NC)"

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

build: ## 🏗️ 建置 NetStack API 映像
	@echo "$(GREEN)🏗️ 建置 NetStack API 映像...$(NC)"
	docker build -t netstack-api:latest -f docker/Dockerfile .
	@echo "$(GREEN)✅ 映像建置完成$(NC)"

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
	@echo "3. 測試 UE 連線..."
	@$(MAKE) test-connectivity
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
	@echo "步驟 4: 測試連線..."
	@$(MAKE) test-connectivity
	@echo "$(GREEN)✅ 修復完成$(NC)"