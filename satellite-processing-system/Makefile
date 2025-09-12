# 衛星處理系統 Makefile
# 簡化開發和部署流程

.PHONY: help build up down dev-up dev-down logs status clean test health tle-setup tle-status tle-download tle-cleanup
.PHONY: test-runner test-sgp4 test-fast test-coverage check lint performance install-deps setup dev-check release-check view-coverage test-status

# 默認目標
help:
	@echo "🚀 衛星處理系統 Docker 管理"
	@echo ""
	@echo "📦 基本命令:"
	@echo "  build       - 構建 Docker 映像檔"
	@echo "  up          - 啟動生產環境服務"
	@echo "  down        - 停止生產環境服務"
	@echo "  logs        - 查看服務日誌"
	@echo "  status      - 檢查服務狀態"
	@echo ""
	@echo "🛠️ 開發命令:"
	@echo "  dev-up      - 啟動開發環境 (支援熱重載)"
	@echo "  dev-down    - 停止開發環境"
	@echo "  dev-logs    - 查看開發環境日誌"
	@echo "  dev-exec    - 進入開發容器"
	@echo ""
	@echo "📡 TLE 數據管理:"
	@echo "  tle-setup   - 安裝 TLE 自動下載排程"
	@echo "  tle-status  - 檢查 TLE 下載狀態"
	@echo "  tle-download- 手動下載 TLE 數據"
	@echo "  tle-cleanup - 清理過期 TLE 數據"
	@echo ""
	@echo "🧪 處理命令:"
	@echo "  run-stages  - 執行完整多階段處理"
	@echo "  run-stage1  - 只執行階段1"
	@echo "  run-fast    - 使用 FAST 驗證模式執行"
	@echo "  health      - 健康檢查"
	@echo ""
	@echo "🛠️ 維護命令:"
	@echo "  clean       - 清理未使用的 Docker 資源"
	@echo "  clean-data  - 清理輸出數據 (謹慎使用!)"
	@echo "  test        - 執行測試套件"

# 📦 基本 Docker 命令
build:
	@echo "🔨 構建六階段處理系統映像檔..."
	docker-compose build

up:
	@echo "🚀 啟動六階段處理系統 (生產模式)..."
	docker-compose up -d
	@echo "✅ 服務已啟動，使用 'make status' 檢查狀態"

down:
	@echo "🛑 停止六階段處理系統..."
	docker-compose down

logs:
	@echo "📋 查看服務日誌..."
	docker-compose logs -f --tail=100

status:
	@echo "📊 服務狀態:"
	docker-compose ps
	@echo ""
	@echo "🔍 健康狀態:"
	@docker exec satellite-processor python /satellite-processing/scripts/health_check.py 2>/dev/null || echo "❌ 容器未運行或健康檢查失敗"

# 📡 TLE 數據管理命令
tle-setup:
	@echo "📡 安裝 TLE 自動下載排程..."
	@docker exec satellite-processor /satellite-processing/scripts/tle_management/tle_cron_scheduler.sh install || \
	 docker exec satellite-dev /satellite-processing/scripts/tle_management/tle_cron_scheduler.sh install

tle-status:
	@echo "📊 TLE 下載狀態檢查..."
	@docker exec satellite-processor /satellite-processing/scripts/tle_management/tle_cron_scheduler.sh status || \
	 docker exec satellite-dev /satellite-processing/scripts/tle_management/tle_cron_scheduler.sh status

tle-download:
	@echo "🌐 手動下載 TLE 數據..."
	@docker exec satellite-processor /satellite-processing/scripts/tle_management/daily_tle_download_enhanced.sh || \
	 docker exec satellite-dev /satellite-processing/scripts/tle_management/daily_tle_download_enhanced.sh

tle-download-force:
	@echo "⚡ 強制重新下載 TLE 數據..."
	@docker exec satellite-processor /satellite-processing/scripts/tle_management/daily_tle_download_enhanced.sh --force || \
	 docker exec satellite-dev /satellite-processing/scripts/tle_management/daily_tle_download_enhanced.sh --force

tle-cleanup:
	@echo "🧹 清理過期 TLE 數據..."
	@docker exec satellite-processor /satellite-processing/scripts/tle_management/intelligent_data_cleanup.sh || \
	 docker exec satellite-dev /satellite-processing/scripts/tle_management/intelligent_data_cleanup.sh

tle-logs:
	@echo "📋 查看 TLE 下載日誌..."
	@docker exec satellite-processor /satellite-processing/scripts/tle_management/tle_cron_scheduler.sh logs 50 || \
	 docker exec satellite-dev /satellite-processing/scripts/tle_management/tle_cron_scheduler.sh logs 50

# 🛠️ 開發環境命令
dev-up:
	@echo "🛠️ 啟動開發環境..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ 開發環境已啟動"
	@echo "💡 進入容器: make dev-exec"
	@echo "🚀 執行處理: make dev-run-stages"

dev-down:
	@echo "🛑 停止開發環境..."
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	@echo "📋 開發環境日誌..."
	docker-compose -f docker-compose.dev.yml logs -f --tail=50

dev-exec:
	@echo "🖥️ 進入開發容器..."
	docker exec -it satellite-dev bash

dev-status:
	@echo "📊 開發環境狀態:"
	docker-compose -f docker-compose.dev.yml ps

# 🧪 六階段處理命令
run-stages:
	@echo "🚀 執行完整六階段處理..."
	docker exec satellite-processor python /satellite-processing/scripts/run_six_stages_with_validation.py --validation-level=STANDARD

run-fast:
	@echo "⚡ 執行六階段處理 (FAST 模式)..."
	docker exec satellite-processor python /satellite-processing/scripts/run_six_stages_with_validation.py --validation-level=FAST

run-comprehensive:
	@echo "🔍 執行六階段處理 (COMPREHENSIVE 模式)..."
	docker exec satellite-processor python /satellite-processing/scripts/run_six_stages_with_validation.py --validation-level=COMPREHENSIVE

run-stage1:
	@echo "📡 執行階段1 (TLE軌道計算)..."
	docker exec satellite-processor python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=1

run-stage6:
	@echo "🌐 執行階段6 (動態池規劃)..."
	docker exec satellite-processor python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=6

# 開發環境處理命令
dev-run-stages:
	@echo "🛠️ 開發環境：執行完整六階段處理..."
	docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --validation-level=FAST

dev-run-stage:
	@echo "🛠️ 開發環境：執行階段 $(STAGE)..."
	docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=$(STAGE) --validation-level=FAST

# 🔍 健康和監控
health:
	@echo "🔍 執行健康檢查..."
	@docker exec satellite-processor python /satellite-processing/scripts/health_check.py || \
	 docker exec satellite-dev python /satellite-processing/scripts/health_check.py 2>/dev/null || \
	 echo "❌ 無法執行健康檢查 - 請確認容器運行狀態"

show-outputs:
	@echo "📂 查看輸出目錄:"
	@docker exec satellite-processor ls -la /satellite-processing/data/outputs/ 2>/dev/null || \
	 docker exec satellite-dev ls -la /satellite-processing/data/outputs/ 2>/dev/null || \
	 echo "❌ 無法訪問輸出目錄"

show-validation:
	@echo "📋 查看驗證快照:"
	@docker exec satellite-processor ls -la /satellite-processing/data/validation_snapshots/ 2>/dev/null || \
	 docker exec satellite-dev ls -la /satellite-processing/data/validation_snapshots/ 2>/dev/null || \
	 echo "❌ 無法訪問驗證目錄"

# 🧪 測試命令
test:
	@echo "🧪 執行測試套件..."
	@docker exec satellite-processor python -m pytest /satellite-processing/tests/ -v 2>/dev/null || \
	 docker exec satellite-dev python -m pytest /satellite-processing/tests/ -v 2>/dev/null || \
	 echo "❌ 無法執行測試 - 請確認容器運行狀態"

# 🛠️ 維護命令
clean:
	@echo "🧹 清理未使用的 Docker 資源..."
	docker system prune -f
	docker volume prune -f

clean-data:
	@echo "⚠️ 清理輸出數據目錄..."
	@read -p "確定要清理所有輸出數據嗎? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker exec satellite-processor rm -rf /satellite-processing/data/outputs/* 2>/dev/null || true; \
		docker exec satellite-processor rm -rf /satellite-processing/data/validation_snapshots/* 2>/dev/null || true; \
		docker exec satellite-dev rm -rf /satellite-processing/data/outputs/* 2>/dev/null || true; \
		docker exec satellite-dev rm -rf /satellite-processing/data/validation_snapshots/* 2>/dev/null || true; \
		echo "✅ 數據已清理"; \
	else \
		echo "❌ 取消清理"; \
	fi

restart:
	@echo "🔄 重啟服務..."
	make down
	make up

dev-restart:
	@echo "🔄 重啟開發環境..."
	make dev-down
	make dev-up

# 📊 信息命令
info:
	@echo "ℹ️ 六階段處理系統信息:"
	@echo "  🏗️ 項目名稱: Six Stages Satellite Processing System"
	@echo "  📦 Docker 映像: satellite-processing-system"
	@echo "  🌐 網路: satellite-network (172.30.0.0/16)"
	@echo "  📂 數據目錄: ./data/"
	@echo "  🔧 配置文件: ./config/"
	@echo "  📝 源碼目錄: ./src/"
	@echo ""
	@echo "📋 快速啟動:"
	@echo "  1. make build        # 首次構建"
	@echo "  2. make up          # 啟動服務"  
	@echo "  3. make run-stages  # 執行處理"
	@echo ""
	@echo "🛠️ 開發模式:"
	@echo "  1. make dev-up       # 啟動開發環境"
	@echo "  2. make dev-exec     # 進入容器"
	@echo "  3. make dev-run-stages  # 執行處理"

# =============================================================================
# 🧪 測試和CI/CD命令 (TDD重構)
# =============================================================================

# 顏色定義
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m

# 測試相關命令
test-runner: ## 執行完整測試套件 (推薦)
	@echo "$(BLUE)🚀 執行完整測試套件$(NC)"
	@./scripts/test-runner.sh

test-sgp4: ## 僅執行SGP4軌道引擎測試
	@echo "$(BLUE)🛰️ 執行SGP4測試$(NC)"
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py -v

test-fast: ## 快速測試 (僅關鍵測試)
	@echo "$(BLUE)⚡ 快速測試$(NC)"
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_tle_epoch_time_usage_mandatory -v

test-coverage: ## 生成測試覆蓋率報告
	@echo "$(BLUE)📊 生成覆蓋率報告$(NC)"
	python -m pytest tests/unit/ --cov=src --cov-report=html:tests/reports/coverage_html --cov-report=term-missing
	@echo "$(GREEN)📈 覆蓋率報告: tests/reports/coverage_html/index.html$(NC)"

# 代碼品質檢查
check: ## 執行預提交檢查
	@echo "$(BLUE)🛡️ 執行預提交檢查$(NC)"
	@./scripts/pre-commit-check.sh

lint: ## 檢查代碼語法 (輕量級)
	@echo "$(BLUE)🐍 檢查Python語法$(NC)"
	python -m py_compile src/shared/engines/sgp4_orbital_engine.py
	@echo "$(GREEN)✅ 語法檢查通過$(NC)"

# 性能測試
performance: ## 執行性能基準測試
	@echo "$(BLUE)⚡ 性能基準測試$(NC)"
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_sgp4_calculation_performance -v
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_batch_calculation_performance -v

# 開發流程快捷命令
dev-check: check test-sgp4 ## 開發檢查 (預提交 + 核心測試)
	@echo "$(GREEN)🎉 開發檢查完成！$(NC)"

release-check: test-runner test-coverage ## 發布檢查 (完整測試 + 覆蓋率)
	@echo "$(GREEN)🚀 發布檢查完成！$(NC)"

# 測試環境設置
install-deps: ## 安裝測試依賴
	@echo "$(BLUE)📦 安裝測試依賴$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ 依賴安裝完成$(NC)"

test-setup: install-deps ## 初始化測試環境
	@echo "$(BLUE)🔧 初始化測試環境$(NC)"
	mkdir -p tests/reports
	@echo "$(GREEN)✅ 測試環境設置完成$(NC)"

# 狀態檢查
test-status: ## 顯示測試環境狀態
	@echo "$(BLUE)📊 測試環境狀態$(NC)"
	@echo "================================================================"
	@echo "Python版本: $$(python --version)"
	@echo "pytest版本: $$(python -m pytest --version)"
	@echo "TLE數據文件: $$(ls data/tle_data/starlink/tle/*.tle 2>/dev/null | wc -l) 個"
	@echo "最近測試: $$(ls -t tests/reports/*.html 2>/dev/null | head -1 | xargs ls -l 2>/dev/null || echo '無')"
	@echo "================================================================"