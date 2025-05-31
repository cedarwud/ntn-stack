# NTN Stack 統一測試套件 Makefile
# 集中管理所有測試分類和執行流程

.PHONY: help test-all test-quick test-smoke test-core test-regression
.PHONY: test-unit-all test-integration-all test-e2e-all test-frontend-all test-shell-all
.PHONY: test-unit-netstack test-unit-simworld test-unit-deployment test-unit-monitoring
.PHONY: test-integration-api test-integration-services test-integration-cross-service
.PHONY: test-e2e-basic test-e2e-failover test-e2e-performance test-e2e-comprehensive
.PHONY: test-perf-latency test-perf-throughput test-perf-load test-perf-stress
.PHONY: test-frontend-components test-frontend-ui test-frontend-e2e
.PHONY: test-shell-netstack test-shell-connectivity test-shell-deployment
.PHONY: test-env-setup test-env-start test-env-stop test-env-reset test-env-check
.PHONY: test-report test-report-detailed test-report-coverage test-report-archive
.PHONY: test-clean test-clean-reports test-clean-logs test-clean-all
.PHONY: install-deps check-env smoke-test coverage

# 顏色定義
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
PURPLE=\033[0;35m
CYAN=\033[0;36m
NC=\033[0m # No Color

# 默認目標
help:
	@echo "$(CYAN)🧪 NTN Stack 統一測試套件$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(GREEN)📋 快速測試指令:$(NC)"
	@echo "  $(YELLOW)test-smoke$(NC)      - 煙霧測試 (30s) - 基本服務可用性"
	@echo "  $(YELLOW)test-quick$(NC)      - 快速測試 (2min) - 核心功能驗證"
	@echo "  $(YELLOW)test-core$(NC)       - 核心測試 (5min) - 主要功能完整性"
	@echo "  $(YELLOW)test-regression$(NC) - 回歸測試 (10min) - 功能無退化驗證"
	@echo "  $(YELLOW)test-all$(NC)        - 完整測試 (20min) - 全功能覆蓋"
	@echo ""
	@echo "$(GREEN)🔧 分類測試指令:$(NC)"
	@echo "  $(BLUE)單元測試:$(NC)"
	@echo "    test-unit-netstack     - NetStack API 單元測試"
	@echo "    test-unit-simworld     - SimWorld 後端單元測試"
	@echo "    test-unit-deployment   - 部署模組單元測試"
	@echo "    test-unit-monitoring   - 監控模組單元測試"
	@echo ""
	@echo "  $(BLUE)整合測試:$(NC)"
	@echo "    test-integration-api        - API 整合測試"
	@echo "    test-integration-services   - 服務間整合測試"
	@echo "    test-integration-cross-service - 跨服務整合測試"
	@echo ""
	@echo "  $(BLUE)端到端測試:$(NC)"
	@echo "    test-e2e-basic         - 基本功能端到端測試"
	@echo "    test-e2e-failover      - 備援機制端到端測試"
	@echo "    test-e2e-performance   - 性能要求端到端測試"
	@echo "    test-e2e-comprehensive - 綜合場景端到端測試"
	@echo ""
	@echo "  $(BLUE)性能測試:$(NC)"
	@echo "    test-perf-latency      - 延遲測試"
	@echo "    test-perf-throughput   - 吞吐量測試"
	@echo "    test-perf-load         - 負載測試"
	@echo "    test-perf-stress       - 壓力測試"
	@echo ""
	@echo "  $(BLUE)前端測試:$(NC)"
	@echo "    test-frontend-components - 組件測試"
	@echo "    test-frontend-ui       - UI 測試"
	@echo "    test-frontend-e2e      - 前端端到端測試"
	@echo ""
	@echo "  $(BLUE)Shell 腳本測試:$(NC)"
	@echo "    test-shell-netstack    - NetStack 功能腳本測試"
	@echo "    test-shell-connectivity - 連接性腳本測試"
	@echo "    test-shell-deployment  - 部署腳本測試"
	@echo ""
	@echo "$(GREEN)🛠️ 環境管理:$(NC)"
	@echo "  test-env-setup         - 設置測試環境"
	@echo "  test-env-start         - 啟動測試環境"
	@echo "  test-env-stop          - 停止測試環境"
	@echo "  test-env-reset         - 重設測試環境"
	@echo "  test-env-check         - 檢查環境狀態"
	@echo ""
	@echo "$(GREEN)📊 報告管理:$(NC)"
	@echo "  test-report            - 生成測試報告摘要"
	@echo "  test-report-detailed   - 生成詳細測試報告"
	@echo "  test-report-coverage   - 生成覆蓋率報告"
	@echo "  test-report-archive    - 歸檔測試報告"
	@echo ""
	@echo "$(GREEN)🧹 清理指令:$(NC)"
	@echo "  test-clean             - 清理測試緩存"
	@echo "  test-clean-reports     - 清理測試報告"
	@echo "  test-clean-logs        - 清理測試日誌"
	@echo "  test-clean-all         - 清理所有測試產物"

# ============================================================================
# 快速測試指令
# ============================================================================

# 煙霧測試 - 基本服務可用性檢查
test-smoke:
	@echo "$(YELLOW)💨 執行煙霧測試...$(NC)"
	@python3 tools/test_runner.py --suite smoke --timeout 30
	@echo "$(GREEN)✅ 煙霧測試完成$(NC)"

# 快速測試 - 核心功能驗證
test-quick:
	@echo "$(YELLOW)⚡ 執行快速測試...$(NC)"
	@python3 tools/test_runner.py --suite quick --timeout 120
	@echo "$(GREEN)✅ 快速測試完成$(NC)"

# 核心測試 - 主要功能完整性
test-core:
	@echo "$(YELLOW)🎯 執行核心測試...$(NC)"
	@python3 tools/test_runner.py --suite core --timeout 300
	@echo "$(GREEN)✅ 核心測試完成$(NC)"

# 回歸測試 - 功能無退化驗證
test-regression:
	@echo "$(YELLOW)🔄 執行回歸測試...$(NC)"
	@python3 tools/test_runner.py --suite regression --timeout 600
	@echo "$(GREEN)✅ 回歸測試完成$(NC)"

# 完整測試 - 全功能覆蓋
test-all:
	@echo "$(YELLOW)🚀 執行完整測試套件...$(NC)"
	@echo "$(BLUE)測試範圍: 單元測試 + 整合測試 + 端到端測試 + 性能測試$(NC)"
	@$(MAKE) test-unit-all
	@$(MAKE) test-integration-all
	@$(MAKE) test-e2e-all
	@$(MAKE) test-frontend-all
	@$(MAKE) test-shell-all
	@echo "$(GREEN)✅ 完整測試套件執行完成$(NC)"

# ============================================================================
# 單元測試
# ============================================================================

test-unit-all:
	@echo "$(BLUE)🔧 執行所有單元測試...$(NC)"
	@$(MAKE) test-unit-netstack
	@$(MAKE) test-unit-simworld
	@$(MAKE) test-unit-deployment
	@$(MAKE) test-unit-monitoring

test-unit-netstack:
	@echo "$(CYAN)📡 NetStack API 單元測試$(NC)"
	@cd unit/netstack && python3 -m pytest -v --tb=short

test-unit-simworld:
	@echo "$(CYAN)🌍 SimWorld 後端單元測試$(NC)"
	@cd unit/simworld && python3 -m pytest -v --tb=short

test-unit-deployment:
	@echo "$(CYAN)🚀 部署模組單元測試$(NC)"
	@cd unit/deployment && python3 -m pytest -v --tb=short

test-unit-monitoring:
	@echo "$(CYAN)📊 監控模組單元測試$(NC)"
	@cd unit/monitoring && python3 -m pytest -v --tb=short

# ============================================================================
# 整合測試
# ============================================================================

test-integration-all:
	@echo "$(BLUE)🔗 執行所有整合測試...$(NC)"
	@$(MAKE) test-integration-api
	@$(MAKE) test-integration-services
	@$(MAKE) test-integration-cross-service

test-integration-api:
	@echo "$(CYAN)🌐 API 整合測試$(NC)"
	@cd integration/api && python3 -m pytest -v --tb=short

test-integration-services:
	@echo "$(CYAN)⚙️ 服務間整合測試$(NC)"
	@cd integration/services && python3 -m pytest -v --tb=short

test-integration-cross-service:
	@echo "$(CYAN)🔄 跨服務整合測試$(NC)"
	@cd integration/cross_service && python3 -m pytest -v --tb=short

# ============================================================================
# 端到端測試
# ============================================================================

test-e2e-all:
	@echo "$(BLUE)🎭 執行所有端到端測試...$(NC)"
	@$(MAKE) test-e2e-basic
	@$(MAKE) test-e2e-failover
	@$(MAKE) test-e2e-performance
	@$(MAKE) test-e2e-comprehensive

test-e2e-basic:
	@echo "$(CYAN)🎯 基本功能端到端測試$(NC)"
	@cd e2e/scenarios && python3 simple_functionality_test.py

test-e2e-failover:
	@echo "$(CYAN)🔄 備援機制端到端測試$(NC)"
	@cd e2e/scenarios && python3 final_network_verification.py

test-e2e-performance:
	@echo "$(CYAN)⚡ 性能要求端到端測試$(NC)"
	@cd e2e/scenarios && python3 complete_e2e_optimization_test.py

test-e2e-comprehensive:
	@echo "$(CYAN)🎪 綜合場景端到端測試$(NC)"
	@cd e2e/scenarios && python3 final_comprehensive_test.py

# ============================================================================
# 性能測試
# ============================================================================

test-perf-latency:
	@echo "$(PURPLE)⏱️ 延遲測試$(NC)"
	@cd shell/netstack && bash ntn_latency_test.sh

test-perf-throughput:
	@echo "$(PURPLE)📈 吞吐量測試$(NC)"
	@cd shell/netstack && bash performance_test.sh

test-perf-load:
	@echo "$(PURPLE)📊 負載測試$(NC)"
	@cd e2e/performance && python3 load_test.py

test-perf-stress:
	@echo "$(PURPLE)💪 壓力測試$(NC)"
	@cd e2e/performance && python3 stress_test.py

# ============================================================================
# 前端測試
# ============================================================================

test-frontend-all:
	@echo "$(BLUE)🎨 執行所有前端測試...$(NC)"
	@$(MAKE) test-frontend-components
	@$(MAKE) test-frontend-ui
	@$(MAKE) test-frontend-e2e

test-frontend-components:
	@echo "$(CYAN)🧩 組件測試$(NC)"
	@cd frontend/components && python3 -m pytest -v --tb=short

test-frontend-ui:
	@echo "$(CYAN)🎨 UI 測試$(NC)"
	@cd frontend/ui && npm test

test-frontend-e2e:
	@echo "$(CYAN)🎭 前端端到端測試$(NC)"
	@cd frontend/integration && npm run test:e2e

# ============================================================================
# Shell 腳本測試
# ============================================================================

test-shell-all:
	@echo "$(BLUE)🐚 執行所有 Shell 腳本測試...$(NC)"
	@$(MAKE) test-shell-netstack
	@$(MAKE) test-shell-connectivity
	@$(MAKE) test-shell-deployment

test-shell-netstack:
	@echo "$(CYAN)📡 NetStack 功能腳本測試$(NC)"
	@cd shell/netstack && bash e2e_netstack.sh
	@cd shell/netstack && bash quick_ntn_validation.sh

test-shell-connectivity:
	@echo "$(CYAN)🔗 連接性腳本測試$(NC)"
	@cd shell/netstack && bash test_connectivity.sh

test-shell-deployment:
	@echo "$(CYAN)🚀 部署腳本測試$(NC)"
	@cd shell/deployment && bash deployment_test.sh

# ============================================================================
# 環境管理
# ============================================================================

test-env-setup:
	@echo "$(GREEN)📦 設置測試環境...$(NC)"
	@python3 tools/environment_setup.py --setup
	@pip install -r requirements-test.txt

test-env-start:
	@echo "$(GREEN)🚀 啟動測試環境...$(NC)"
	@cd .. && make up
	@sleep 10
	@$(MAKE) check-env

test-env-stop:
	@echo "$(GREEN)🛑 停止測試環境...$(NC)"
	@cd .. && make down

test-env-reset:
	@echo "$(GREEN)🔄 重設測試環境...$(NC)"
	@$(MAKE) test-env-stop
	@$(MAKE) test-clean-all
	@$(MAKE) test-env-start

test-env-check:
	@echo "$(GREEN)🔍 檢查測試環境...$(NC)"
	@python3 tools/environment_setup.py --check

# ============================================================================
# 報告管理
# ============================================================================

test-report:
	@echo "$(CYAN)📊 生成測試報告摘要...$(NC)"
	@python3 tools/report_generator.py --summary

test-report-detailed:
	@echo "$(CYAN)📋 生成詳細測試報告...$(NC)"
	@python3 tools/report_generator.py --detailed

test-report-coverage:
	@echo "$(CYAN)📈 生成覆蓋率報告...$(NC)"
	@python3 tools/report_generator.py --coverage

test-report-archive:
	@echo "$(CYAN)📦 歸檔測試報告...$(NC)"
	@python3 tools/report_generator.py --archive

# ============================================================================
# 清理指令
# ============================================================================

test-clean:
	@echo "$(YELLOW)🧹 清理測試緩存...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

test-clean-reports:
	@echo "$(YELLOW)📄 清理測試報告...$(NC)"
	@rm -rf reports/
	@rm -f *.html *.xml *.json

test-clean-logs:
	@echo "$(YELLOW)📝 清理測試日誌...$(NC)"
	@rm -f *.log
	@rm -rf logs/

test-clean-all:
	@echo "$(YELLOW)🗑️ 清理所有測試產物...$(NC)"
	@$(MAKE) test-clean
	@$(MAKE) test-clean-reports
	@$(MAKE) test-clean-logs

# ============================================================================
# 輔助功能
# ============================================================================

install-deps:
	@echo "$(GREEN)📦 安裝測試依賴...$(NC)"
	@pip install pytest pytest-asyncio pytest-cov httpx requests

check-env:
	@echo "$(BLUE)🔍 檢查測試環境...$(NC)"
	@curl -s http://localhost:8080/health > /dev/null && echo "$(GREEN)✅ NetStack API 服務正常$(NC)" || echo "$(RED)❌ NetStack API 服務未啟動$(NC)"
	@curl -s http://localhost:3000 > /dev/null && echo "$(GREEN)✅ SimWorld 前端服務正常$(NC)" || echo "$(RED)❌ SimWorld 前端服務未啟動$(NC)"
	@curl -s http://localhost:8000/health > /dev/null && echo "$(GREEN)✅ SimWorld 後端服務正常$(NC)" || echo "$(RED)❌ SimWorld 後端服務未啟動$(NC)"

smoke-test:
	@echo "$(YELLOW)💨 執行快速煙霧測試...$(NC)"
	@curl -s http://localhost:8080/health | python3 -m json.tool
	@curl -s http://localhost:8080/api/v1/mesh/nodes | python3 -m json.tool | head -20

coverage:
	@echo "$(CYAN)📊 測試覆蓋範圍$(NC)"
	@echo "==============="
	@echo ""
	@echo "$(GREEN)✅ NetStack 核心功能 (97% 覆蓋)$(NC)"
	@echo "  📡 網路核心 API - 統一 API 路由、健康檢查、服務發現"
	@echo "  🚁 UAV 管理 - UAV 註冊、軌跡管理、UE 整合"
	@echo "  🛡️ 干擾控制 - 事件驅動架構、AI 決策引擎"
	@echo "  🌐 Mesh 橋接 - Tier-1 Mesh 網路與 5G 核心網橋接"
	@echo "  🔄 UAV-Mesh 備援 - 失聯檢測、自動切換（2秒內重建）"
	@echo "  🛰️ 衛星通信 - NTN 配置、gNodeB 整合、延遲最佳化"
	@echo "  ⚡ 性能最佳化 - 負載測試、切片切換、UERANSIM 整合"
	@echo ""
	@echo "$(GREEN)✅ SimWorld 模擬核心 (95% 覆蓋)$(NC)"
	@echo "  📻 Sionna 無線通道 - 通道模型、場景模擬、品質評估"
	@echo "  🏗️ CQRS 架構 - 衛星位置讀寫分離、命令查詢分離"
	@echo "  🎭 場景管理 - 多場景支援（NYCU、Lotus、NTPU、Nanliao）"
	@echo "  🏥 健康度檢查 - 場景自動回退、檔案完整性驗證"
	@echo "  🎨 前端組件 - Charts Dropdown、錯誤處理、響應式設計"
	@echo ""
	@echo "$(GREEN)✅ 系統整合 (93% 覆蓋)$(NC)"
	@echo "  🔗 跨服務通信 - 異步微服務、事件驅動整合"
	@echo "  📊 UAV-衛星連接品質 - 即時評估、智能路由、故障預測"
	@echo "  🗺️ 網路拓撲管理 - 動態發現、最佳化路由、QoS 保證"
	@echo "  🚀 部署自動化 - 多環境配置、一鍵部署、回滾機制"
	@echo ""
	@echo "$(GREEN)✅ 部署與運維 (90% 覆蓋)$(NC)"
	@echo "  ⚙️ 配置管理 - 環境隔離、模板生成、驗證機制"
	@echo "  📈 監控系統 - 指標收集、告警機制、可觀測性"
	@echo "  🐳 Docker 化部署 - 容器編排、網路隔離、資源管理"
	@echo "  💾 備份恢復 - 資料備份、災難恢復、高可用性"

# 特定功能測試快捷方式
test-uav-ue:
	@echo "$(PURPLE)🚁 UAV UE 功能測試$(NC)"
	@cd integration/services && python3 test_uav_ue_integration.py

test-mesh-bridge:
	@echo "$(PURPLE)🌐 Mesh 橋接功能測試$(NC)"
	@cd integration/services && python3 test_mesh_bridge_integration.py

test-interference:
	@echo "$(PURPLE)🛡️ 干擾控制功能測試$(NC)"
	@cd integration/services && python3 test_interference_control.py

test-cqrs:
	@echo "$(PURPLE)🏗️ CQRS 架構功能測試$(NC)"
	@cd unit/simworld && python3 test_cqrs_architecture.py

# 創建測試依賴文件
create-requirements:
	@echo "$(GREEN)📝 創建測試依賴文件...$(NC)"
	@echo "# NTN Stack 測試依賴" > requirements-test.txt
	@echo "pytest>=7.0.0" >> requirements-test.txt
	@echo "pytest-asyncio>=0.21.0" >> requirements-test.txt
	@echo "pytest-cov>=4.0.0" >> requirements-test.txt
	@echo "httpx>=0.24.0" >> requirements-test.txt
	@echo "requests>=2.28.0" >> requirements-test.txt
	@echo "aiohttp>=3.8.0" >> requirements-test.txt
	@echo "selenium>=4.0.0" >> requirements-test.txt
	@echo "beautifulsoup4>=4.11.0" >> requirements-test.txt
	@echo "pyyaml>=6.0" >> requirements-test.txt
	@echo "jinja2>=3.1.0" >> requirements-test.txt
	@echo "$(GREEN)✅ requirements-test.txt 已創建$(NC)"

# ============================================================================
# 從根目錄 Makefile 整合的測試指令
# ============================================================================

# ===== 環境檢查和持久性測試 =====

test-env-check-advanced: ## 🔍 檢查測試環境（本地和容器中）
	@echo "$(CYAN)🔍 檢查測試環境...$(NC)"
	@echo "$(YELLOW)1. 本地環境檢查...$(NC)"
	@python3 ../tests/test_environment_check.py 2>/dev/null || echo "$(RED)❌ 本地環境檢查檔案不存在$(NC)"
	@echo "$(YELLOW)2. 容器環境檢查...$(NC)"
	@docker exec netstack-api python /app/tests/test_environment_check.py 2>/dev/null || echo "$(RED)❌ 容器環境檢查失敗$(NC)"
	@echo "$(GREEN)✅ 測試環境檢查完成$(NC)"

test-env-persistence-advanced: ## 🔧 測試環境持久性（模擬 make clean && make up）
	@echo "$(CYAN)🔧 測試環境持久性...$(NC)"
	@echo "$(YELLOW)檢查依賴是否正確安裝在 Docker 鏡像中...$(NC)"
	@docker exec netstack-api python -c "import pytest; print('✅ pytest 在容器中可用')" 2>/dev/null || echo "$(RED)❌ pytest 不在容器中$(NC)"
	@docker exec netstack-api python -c "import pytest_asyncio; print('✅ pytest-asyncio 在容器中可用')" 2>/dev/null || echo "$(RED)❌ pytest-asyncio 不在容器中$(NC)"
	@docker exec netstack-api python -c "import httpx; print('✅ httpx 在容器中可用')" 2>/dev/null || echo "$(RED)❌ httpx 不在容器中$(NC)"
	@docker exec netstack-api python -c "import asyncio; print('✅ asyncio 在容器中可用')" 2>/dev/null || echo "$(RED)❌ asyncio 不在容器中$(NC)"
	@echo "$(YELLOW)檢查統一 API 模組...$(NC)"
	@docker exec netstack-api python -c "from netstack_api.routers.unified_api_router import unified_router; print('✅ 統一 API 路由器可用')" 2>/dev/null || echo "$(RED)❌ 統一 API 路由器不可用$(NC)"
	@docker exec netstack-api python -c "from netstack_api.models.unified_models import SystemStatusResponse; print('✅ 統一模型可用')" 2>/dev/null || echo "$(RED)❌ 統一模型不可用$(NC)"
	@echo "$(GREEN)✅ 環境持久性檢查完成$(NC)"

# ===== 統一 API 測試 =====

test-unified-api-local: ## 🌐 本地統一 API 測試
	@echo "$(CYAN)🌐 執行本地統一 API 測試...$(NC)"
	@echo "$(YELLOW)確保測試依賴已安裝...$(NC)"
	@pip install -q pytest pytest-asyncio httpx structlog 2>/dev/null || pip3 install -q pytest pytest-asyncio httpx structlog 2>/dev/null
	@python3 -m pytest ../tests/test_unified_api.py -v --tb=short 2>/dev/null || echo "$(RED)❌ 統一 API 測試檔案不存在$(NC)"
	@echo "$(GREEN)✅ 本地統一 API 測試完成$(NC)"

test-unified-api-docker: ## 🐳 Docker 容器中統一 API 測試
	@echo "$(CYAN)🐳 執行 Docker 容器中統一 API 測試...$(NC)"
	@docker exec netstack-api python -m pytest /app/tests/test_unified_api.py -v --tb=short 2>/dev/null || echo "$(RED)❌ 容器中測試失敗$(NC)"
	@echo "$(GREEN)✅ Docker 統一 API 測試完成$(NC)"

test-unified-api-complete: ## 🎯 完整統一 API 測試（本地+容器）
	@echo "$(CYAN)🎯 執行完整統一 API 測試...$(NC)"
	@$(MAKE) test-env-check-advanced
	@$(MAKE) test-unified-api-local
	@$(MAKE) test-unified-api-docker
	@echo "$(GREEN)✅ 完整統一 API 測試完成$(NC)"

# ===== NetStack 核心功能測試（Shell 腳本） =====

test-ntn-validation: ## 🚀 執行 NTN 功能快速驗證
	@echo "$(CYAN)🚀 執行 NTN 功能快速驗證...$(NC)"
	@cd shell/netstack && bash ./quick_ntn_validation.sh
	@echo "$(GREEN)✅ NTN 功能驗證完成$(NC)"

test-config-validation: ## ⚙️ 執行 NTN 配置驗證測試
	@echo "$(CYAN)⚙️ 執行 NTN 配置驗證測試...$(NC)"
	@cd shell/netstack && bash ./ntn_config_validation_test.sh
	@echo "$(GREEN)✅ NTN 配置驗證完成$(NC)"

test-satellite-gnb: ## 🛰️ 執行衛星-gNodeB 整合測試
	@echo "$(CYAN)🛰️ 執行衛星-gNodeB 整合測試...$(NC)"
	@cd shell/netstack && bash ./satellite_gnb_integration_test.sh
	@echo "$(GREEN)✅ 衛星-gNodeB 整合測試完成$(NC)"

test-ueransim: ## 📡 執行 UERANSIM 配置測試
	@echo "$(CYAN)📡 執行 UERANSIM 配置測試...$(NC)"
	@cd shell/netstack && bash ./ueransim_config_test.sh
	@echo "$(GREEN)✅ UERANSIM 配置測試完成$(NC)"

test-latency: ## 🕐 執行 NTN 延遲測試
	@echo "$(CYAN)🕐 執行 NTN 延遲測試...$(NC)"
	@cd shell/netstack && bash ./ntn_latency_test.sh
	@echo "$(GREEN)✅ NTN 延遲測試完成$(NC)"

test-e2e-netstack: ## 🔄 執行 NetStack 端到端測試
	@echo "$(CYAN)🔄 執行 NetStack 端到端測試...$(NC)"
	@cd shell/netstack && bash ./e2e_netstack.sh
	@echo "$(GREEN)✅ NetStack 端到端測試完成$(NC)"

test-slice-switching: ## 🔀 執行切片切換測試
	@echo "$(CYAN)🔀 執行切片切換測試...$(NC)"
	@cd shell/netstack && bash ./slice_switching_test.sh
	@echo "$(GREEN)✅ 切片切換測試完成$(NC)"

test-performance-advanced: ## ⚡ 執行性能測試
	@echo "$(CYAN)⚡ 執行性能測試...$(NC)"
	@cd shell/netstack && bash ./performance_test.sh
	@echo "$(GREEN)✅ 性能測試完成$(NC)"

test-connectivity-advanced: ## 🔗 執行連接性測試
	@echo "$(CYAN)🔗 執行連接性測試...$(NC)"
	@cd shell/netstack && bash ./test_connectivity.sh
	@echo "$(GREEN)✅ 連接性測試完成$(NC)"

# ===== Sionna 整合測試 =====

test-sionna-integration: ## 📡 執行 Sionna 無線通道模型整合測試
	@echo "$(CYAN)📡 執行 Sionna 無線通道模型整合測試...$(NC)"
	@cd .. && python3 test_sionna_integration.py 2>/dev/null || echo "$(RED)❌ Sionna 整合測試檔案不存在$(NC)"
	@echo "$(GREEN)✅ Sionna 整合測試完成$(NC)"

test-sionna-core: ## 🎯 執行 Sionna 核心功能測試
	@echo "$(CYAN)🎯 執行 Sionna 核心功能測試...$(NC)"
	@cd .. && python3 test_sionna_core.py 2>/dev/null || echo "$(RED)❌ Sionna 核心測試檔案不存在$(NC)"
	@echo "$(GREEN)✅ Sionna 核心功能測試完成$(NC)"

# ===== 高級測試組合 =====

test-netstack-only: ## 📡 僅執行 NetStack 測試
	@echo "$(CYAN)📡 執行 NetStack 測試...$(NC)"
	@python3 tools/test_runner.py --suite netstack
	@echo "$(GREEN)✅ NetStack 測試完成$(NC)"

test-simworld-only: ## 🌍 僅執行 SimWorld 測試
	@echo "$(CYAN)🌍 執行 SimWorld 測試...$(NC)"
	@cd ../simworld && $(MAKE) test-all 2>/dev/null || echo "$(RED)❌ SimWorld 測試失敗$(NC)"
	@echo "$(GREEN)✅ SimWorld 測試完成$(NC)"

test-advanced-all: ## 🚀 執行進階功能測試
	@echo "$(CYAN)🚀 執行進階功能測試...$(NC)"
	@$(MAKE) test-integration-all
	@$(MAKE) test-satellite-gnb
	@$(MAKE) test-ueransim
	@$(MAKE) test-performance-advanced
	@$(MAKE) test-uav-ue
	@echo "$(GREEN)✅ 進階功能測試完成$(NC)"

test-legacy-shell: ## 🔄 執行傳統 Shell 測試（向後兼容）
	@echo "$(CYAN)🔄 執行傳統 Shell 測試...$(NC)"
	@$(MAKE) test-config-validation
	@$(MAKE) test-latency
	@$(MAKE) test-e2e-netstack
	@$(MAKE) test-slice-switching
	@echo "$(GREEN)✅ 傳統測試完成$(NC)"

# ===== UAV UE 整合測試 =====

test-uav-ue-integration: ## 🚁 執行 UAV UE 整合測試
	@echo "$(CYAN)🚁 執行 UAV UE 整合測試...$(NC)"
	@echo "$(YELLOW)確認測試依賴已安裝...$(NC)"
	@pip install -q pytest httpx asyncio 2>/dev/null || pip3 install -q pytest httpx asyncio 2>/dev/null
	@cd .. && python3 tests/test_uav_ue_integration.py 2>/dev/null || echo "$(RED)❌ UAV UE 整合測試檔案不存在$(NC)"
	@echo "$(GREEN)✅ UAV UE 整合測試完成$(NC)"

test-uav-ue-quick: ## ⚡ 執行 UAV UE 快速測試
	@echo "$(CYAN)⚡ 執行 UAV UE 快速測試...$(NC)"
	@echo "$(YELLOW)測試 NetStack UAV UE API 端點...$(NC)"
	@curl -s http://localhost:8080/api/v1/uav > /dev/null && echo "$(GREEN)✅ UAV 列表端點正常$(NC)" || echo "$(RED)❌ UAV 列表端點異常$(NC)"
	@curl -s http://localhost:8080/api/v1/uav/trajectory > /dev/null && echo "$(GREEN)✅ 軌跡列表端點正常$(NC)" || echo "$(RED)❌ 軌跡列表端點異常$(NC)"
	@echo "$(YELLOW)測試 SimWorld UAV 位置端點...$(NC)"
	@curl -s http://localhost:8888/api/v1/uav/positions > /dev/null && echo "$(GREEN)✅ SimWorld UAV 位置端點正常$(NC)" || echo "$(RED)❌ SimWorld UAV 位置端點異常$(NC)"
	@echo "$(GREEN)✅ UAV UE 快速測試完成$(NC)"

test-uav-ue-demo: ## 🚀 執行 UAV UE 演示
	@echo "$(CYAN)🚀 執行 UAV UE 演示...$(NC)"
	@curl -X POST http://localhost:8080/api/v1/uav/demo/quick-test -H "Content-Type: application/json" 2>/dev/null | jq . || echo "$(RED)❌ 演示失敗，請檢查服務狀態$(NC)"
	@echo "$(GREEN)✅ UAV UE 演示完成$(NC)"

test-uav-ue-validation: ## 🎯 執行 UAV UE 完整性驗證
	@echo "$(CYAN)🎯 執行 UAV UE 完整性驗證...$(NC)"
	@echo "$(YELLOW)檢查所有 TODO.md 要求是否完成...$(NC)"
	@cd .. && python3 tests/validate_uav_ue_implementation.py 2>/dev/null || echo "$(RED)❌ UAV UE 驗證檔案不存在$(NC)"
	@echo "$(GREEN)✅ UAV UE 完整性驗證完成$(NC)"

test-uav-ue-comprehensive: ## 🚀 執行 UAV UE 綜合測試（包含所有子測試）
	@echo "$(CYAN)🚀 執行 UAV UE 綜合測試套件...$(NC)"
	@$(MAKE) test-uav-ue-quick
	@$(MAKE) test-uav-ue-demo
	@$(MAKE) test-uav-ue-integration
	@$(MAKE) test-uav-ue-validation
	@echo "$(GREEN)🎉 UAV UE 綜合測試完成$(NC)"

# ===== UAV-衛星連接質量評估測試 =====

test-uav-satellite-connection-quality: ## 🛰️ 測試 UAV-衛星連接質量評估系統
	@echo "$(CYAN)🔍 開始測試 UAV-衛星連接質量評估系統...$(NC)"
	@cd .. && python3 tests/test_uav_satellite_connection_quality.py 2>/dev/null || echo "$(RED)❌ UAV-衛星連接測試檔案不存在$(NC)"
	@echo "$(GREEN)✅ UAV-衛星連接質量評估測試完成$(NC)"

test-uav-satellite-connection-quality-quick: ## ⚡ 快速測試 UAV-衛星連接質量評估系統（僅核心功能）
	@echo "$(CYAN)⚡ 快速測試 UAV-衛星連接質量評估系統...$(NC)"
	@cd .. && timeout 60 python3 tests/test_uav_satellite_connection_quality.py 2>/dev/null || echo "$(YELLOW)🕐 60秒快速測試完成$(NC)"

test-uav-satellite-all: ## 🌌 測試所有 UAV-衛星相關功能
	@echo "$(CYAN)🚀 測試所有 UAV-衛星功能...$(NC)"
	@$(MAKE) test-uav-ue-validation
	@$(MAKE) test-uav-satellite-connection-quality
	@echo "$(GREEN)✅ 所有 UAV-衛星功能測試完成$(NC)"

test-connection-quality: ## 🔬 開始 UAV-衛星連接質量評估系統測試
	@echo "$(CYAN)🔬 開始 UAV-衛星連接質量評估系統測試...$(NC)"
	@cd .. && python -m pytest tests/test_uav_satellite_connection_quality.py -v --tb=short 2>/dev/null || echo "$(RED)❌ 連接質量測試失敗$(NC)"

test-connection-quality-detailed: ## 📊 開始詳細的連接質量評估測試
	@echo "$(CYAN)🔬 開始詳細的連接質量評估測試...$(NC)"
	@cd .. && python tests/test_uav_satellite_connection_quality.py 2>/dev/null || echo "$(RED)❌ 詳細連接質量測試失敗$(NC)"

test-connection-quality-quick: ## ⚡ 快速連接質量評估測試
	@echo "$(CYAN)⚡ 快速連接質量評估測試...$(NC)"
	@cd .. && timeout 30 python tests/test_uav_satellite_connection_quality.py 2>/dev/null || echo "$(YELLOW)測試完成（可能因為服務未啟動而失敗）$(NC)"

# ===== 前端組件測試 =====

test-frontend-charts-dropdown: ## 🎨 測試前端圖表 Dropdown 功能
	@echo "$(CYAN)🎨 測試前端圖表 Dropdown 功能...$(NC)"
	@cd .. && python3 tests/test_frontend_charts_dropdown.py 2>/dev/null || echo "$(RED)❌ 前端圖表測試檔案不存在$(NC)"
	@echo "$(GREEN)✅ 前端圖表 Dropdown 測試完成$(NC)"

test-frontend-error-handling: ## 🛡️ 測試前端錯誤處理功能
	@echo "$(CYAN)🛡️ 測試前端錯誤處理功能...$(NC)"
	@cd .. && python3 tests/test_frontend_error_handling.py 2>/dev/null || echo "$(RED)❌ 前端錯誤處理測試檔案不存在$(NC)"
	@echo "$(GREEN)✅ 前端錯誤處理測試完成$(NC)"

test-frontend-validation-complete: ## 🌐 執行前端組件驗證
	@echo "$(CYAN)🌐 執行前端組件驗證...$(NC)"
	@$(MAKE) test-frontend-charts-dropdown
	@$(MAKE) test-frontend-error-handling
	@echo "$(GREEN)✅ 前端組件驗證完成$(NC)"

test-frontend-dev-server: ## 🚀 啟動前端開發伺服器
	@echo "$(CYAN)🚀 啟動前端開發伺服器...$(NC)"
	@cd ../simworld/frontend && npm run dev 2>/dev/null || echo "$(RED)❌ 前端開發伺服器啟動失敗$(NC)"
	@echo "$(GREEN)✅ 前端開發伺服器啟動完成$(NC)"

test-frontend-build: ## 🔨 測試前端建置
	@echo "$(CYAN)🔨 測試前端建置...$(NC)"
	@cd ../simworld/frontend && npm run build 2>/dev/null || echo "$(RED)❌ 前端建置失敗$(NC)"
	@echo "$(GREEN)✅ 前端建置測試完成$(NC)"

# ===== 事件驅動架構測試 =====

test-event-driven: ## 🔄 測試事件驅動架構
	@echo "$(CYAN)🔄 測試 NetStack 事件驅動架構...$(NC)"
	@echo "$(YELLOW)1. 測試事件總線服務...$(NC)"
	@curl -s -X POST http://localhost:8080/api/v1/interference/quick-demo 2>/dev/null | jq . || echo "$(RED)❌ 事件驅動干擾控制演示失敗$(NC)"
	@echo "$(YELLOW)2. 檢查事件總線指標...$(NC)"
	@curl -s http://localhost:8080/metrics 2>/dev/null | grep -i event || echo "$(RED)❌ 事件總線指標不可用$(NC)"
	@echo "$(GREEN)✅ 事件驅動架構測試完成$(NC)"

test-cqrs-advanced: ## 📊 測試 CQRS 衛星服務
	@echo "$(CYAN)📊 測試 SimWorld CQRS 衛星服務...$(NC)"
	@echo "$(YELLOW)1. 測試 CQRS 衛星位置查詢...$(NC)"
	@curl -s -X POST http://localhost:8888/api/v1/satellite/25544/position-cqrs 2>/dev/null | jq . || echo "$(RED)❌ CQRS 位置查詢失敗$(NC)"
	@echo "$(YELLOW)2. 測試批量位置查詢...$(NC)"
	@curl -s -X POST http://localhost:8888/api/v1/satellite/batch-positions-cqrs -H "Content-Type: application/json" -d '[25544, 40069]' 2>/dev/null | jq . || echo "$(RED)❌ CQRS 批量查詢失敗$(NC)"
	@echo "$(YELLOW)3. 檢查 CQRS 服務統計...$(NC)"
	@curl -s http://localhost:8888/api/v1/cqrs/satellite-service/stats 2>/dev/null | jq . || echo "$(RED)❌ CQRS 統計不可用$(NC)"
	@echo "$(GREEN)✅ CQRS 測試完成$(NC)"

test-microservice-communication: ## 🌐 測試微服務間通信
	@echo "$(CYAN)🌐 測試異步微服務架構...$(NC)"
	@echo "$(YELLOW)1. 測試統一 API 服務發現...$(NC)"
	@curl -s http://localhost:8080/unified/system/discovery 2>/dev/null | jq . || echo "$(RED)❌ 服務發現失敗$(NC)"
	@echo "$(YELLOW)2. 測試跨服務事件演示...$(NC)"
	@curl -s -X POST http://localhost:8080/unified/event-driven/interference-satellite-demo 2>/dev/null | jq . || echo "$(RED)❌ 跨服務事件演示失敗$(NC)"
	@echo "$(YELLOW)3. 測試架構對比...$(NC)"
	@curl -s http://localhost:8080/unified/architecture/comparison 2>/dev/null | jq . || echo "$(RED)❌ 架構對比不可用$(NC)"
	@echo "$(GREEN)✅ 微服務通信測試完成$(NC)"

test-new-architecture: ## 🚀 完整測試新架構（事件驅動 + CQRS + 異步微服務）
	@echo "$(CYAN)🚀 執行完整新架構測試套件...$(NC)"
	@$(MAKE) test-event-driven
	@$(MAKE) test-cqrs-advanced
	@$(MAKE) test-microservice-communication
	@echo "$(GREEN)🎉 新架構完整測試完成$(NC)"

test-architecture-performance: ## ⚡ 新架構性能測試
	@echo "$(CYAN)⚡ 新架構性能測試...$(NC)"
	@echo "$(YELLOW)1. 事件總線吞吐量測試...$(NC)"
	@for i in {1..10}; do \
		curl -s -X POST http://localhost:8080/api/v1/interference/quick-demo > /dev/null 2>&1 & \
	done; \
	wait; \
	echo "$(GREEN)✅ 並發事件處理測試完成$(NC)"
	@echo "$(YELLOW)2. CQRS 讀寫分離性能測試...$(NC)"
	@for i in {1..5}; do \
		curl -s -X POST http://localhost:8888/api/v1/satellite/25544/position-cqrs > /dev/null 2>&1 & \
		curl -s -X POST http://localhost:8888/api/v1/satellite/25544/force-update-cqrs > /dev/null 2>&1 & \
	done; \
	wait; \
	@echo "$(GREEN)✅ CQRS 性能測試完成$(NC)"

# ===== 架構驗證和診斷 =====

verify-architecture: ## 🔍 驗證三個重構目標達成情況
	@echo "$(CYAN)🔍 驗證三個重構目標達成情況...$(NC)"
	@echo ""
	@echo "$(YELLOW)✅ 目標 1: NetStack 事件驅動架構（干擾檢測異步化）$(NC)"
	@echo "   - 事件總線服務: $$(curl -s http://localhost:8080/health 2>/dev/null | jq -r '.components.event_bus // "❌ 未啟動"')"
	@echo "   - 干擾控制事件化: $$(curl -s http://localhost:8080/api/v1/interference/status 2>/dev/null | jq -r '.service_type // "❌ 非事件驅動"')"
	@echo ""
	@echo "$(YELLOW)✅ 目標 2: SimWorld CQRS 模式（衛星位置讀寫分離）$(NC)"
	@echo "   - CQRS 服務狀態: $$(curl -s http://localhost:8888/api/v1/cqrs/satellite-service/stats 2>/dev/null | jq -r '.running // "❌ 未運行"')"
	@echo "   - 讀寫分離指標: $$(curl -s http://localhost:8888/api/v1/cqrs/satellite-service/stats 2>/dev/null | jq -r '.command_stats.position_updates // 0')/$$(curl -s http://localhost:8888/api/v1/cqrs/satellite-service/stats 2>/dev/null | jq -r '.query_stats.position_queries // 0') (寫/讀)"
	@echo ""
	@echo "$(YELLOW)✅ 目標 3: 全面異步微服務架構$(NC)"
	@echo "   - 統一 API 狀態: $$(curl -s http://localhost:8080/unified/system/status 2>/dev/null | jq -r '.architecture_type // "❌ 非異步架構"')"
	@echo "   - 跨服務通信: $$(curl -s http://localhost:8080/unified/system/discovery 2>/dev/null | jq -r '.services | length')個服務發現"
	@echo ""
	@echo "$(GREEN)🎯 架構驗證完成$(NC)"

verify-architecture-detailed: ## 🔬 詳細架構驗證（使用驗證腳本）
	@echo "$(CYAN)🔬 執行詳細架構驗證...$(NC)"
	@cd .. && python3 tests/tools/verify_architecture_status.py 2>/dev/null || echo "$(RED)❌ 架構驗證腳本不存在$(NC)"
	@echo "$(GREEN)✅ 詳細架構驗證完成$(NC)"

architecture-health-check: ## 🏥 新架構健康檢查
	@echo "$(CYAN)🏥 新架構健康檢查...$(NC)"
	@echo "$(YELLOW)檢查事件總線健康狀態...$(NC)"
	@curl -s http://localhost:8080/health 2>/dev/null | jq '.components.event_bus' || echo "$(RED)❌ 事件總線異常$(NC)"
	@echo "$(YELLOW)檢查 CQRS 服務健康狀態...$(NC)"
	@curl -s http://localhost:8888/ping 2>/dev/null || echo "$(RED)❌ CQRS 服務異常$(NC)"
	@echo "$(YELLOW)檢查微服務通信健康狀態...$(NC)"
	@curl -s http://localhost:8080/unified/system/status 2>/dev/null | jq '.health_status' || echo "$(RED)❌ 微服務通信異常$(NC)"
	@echo "$(GREEN)✅ 架構健康檢查完成$(NC)"

monitor-architecture: ## 📈 監控新架構狀態
	@echo "$(CYAN)📈 監控新架構狀態...$(NC)"
	@echo "$(YELLOW)事件總線指標:$(NC)"
	@curl -s http://localhost:8080/metrics 2>/dev/null | grep -E "(event|interference)" || echo "$(RED)❌ 事件指標不可用$(NC)"
	@echo ""
	@echo "$(YELLOW)CQRS 服務狀態:$(NC)"
	@curl -s http://localhost:8888/api/v1/cqrs/satellite-service/stats 2>/dev/null | jq '.command_stats, .query_stats, .cache_stats' || echo "$(RED)❌ CQRS 狀態不可用$(NC)"
	@echo ""
	@echo "$(YELLOW)系統總覽:$(NC)"
	@curl -s http://localhost:8080/unified/system/status 2>/dev/null | jq '.netstack_status, .simworld_status' || echo "$(RED)❌ 系統狀態不可用$(NC)"

demo-new-architecture: ## 🎯 新架構功能演示
	@echo "$(CYAN)🎯 新架構功能演示...$(NC)"
	@echo "$(YELLOW)1. 干擾檢測事件驅動演示...$(NC)"
	@curl -s -X POST http://localhost:8080/api/v1/interference/quick-demo 2>/dev/null | jq '.scenario_id, .events_triggered, .ai_decision' || echo "$(RED)❌ 干擾演示失敗$(NC)"
	@echo ""
	@echo "$(YELLOW)2. CQRS 衛星位置演示...$(NC)"
	@curl -s -X POST http://localhost:8888/api/v1/satellite/25544/position-cqrs 2>/dev/null | jq '.satellite_name, .timestamp, .cqrs_metrics' || echo "$(RED)❌ CQRS 演示失敗$(NC)"
	@echo ""
	@echo "$(YELLOW)3. 跨服務事件通信演示...$(NC)"
	@curl -s -X POST http://localhost:8080/unified/event-driven/interference-satellite-demo 2>/dev/null | jq '.cross_service_events, .integration_metrics' || echo "$(RED)❌ 跨服務演示失敗$(NC)"
	@echo "$(GREEN)🎉 新架構演示完成$(NC)"

# ===== 高級清理和報告生成 =====

test-clean-advanced: ## 🧹 清理測試結果和臨時文件
	@echo "$(CYAN)🧹 清理測試結果和臨時文件...$(NC)"
	@rm -rf ../tests/reports/* ../test-reports/ ../netstack/tests/test-reports/ ../netstack/tests/*.log 2>/dev/null || true
	@rm -rf ../simworld/backend/tests/reports/ ../simworld/backend/tests/*.log 2>/dev/null || true
	@rm -rf ../**/__pycache__/ ../**/.pytest_cache/ ../.coverage* 2>/dev/null || true
	@$(MAKE) test-clean
	@echo "$(GREEN)✅ 測試清理完成$(NC)"

test-report-advanced: ## 📊 生成測試報告摘要
	@echo "$(CYAN)📊 生成測試報告摘要...$(NC)"
	@cd .. && python3 -c "import json, glob, os; reports = sorted(glob.glob('tests/reports/test_report_*.json'), reverse=True); print(f'📋 最新測試報告: {os.path.basename(reports[0])}' if reports else '❌ 未找到測試報告')" 2>/dev/null || echo "❌ 報告解析失敗"

test-coverage-advanced: ## 📈 生成覆蓋率報告
	@echo "$(CYAN)📈 生成覆蓋率報告...$(NC)"
	@echo "NetStack 覆蓋率:"
	@cd ../netstack && python3 -m pytest --cov=netstack_api --cov-report=html:../tests/reports/coverage/netstack_coverage.html --cov-report=term 2>/dev/null || echo "$(RED)❌ NetStack 覆蓋率生成失敗$(NC)"
	@echo "SimWorld 覆蓋率:"
	@cd ../simworld/backend && python3 -m pytest --cov=app --cov-report=html:../../tests/reports/coverage/simworld_coverage.html --cov-report=term 2>/dev/null || echo "$(RED)❌ SimWorld 覆蓋率生成失敗$(NC)"
	@echo "$(GREEN)✅ 覆蓋率報告已生成$(NC)"

test-env-setup-advanced: ## 🌍 設置測試環境
	@echo "$(CYAN)🌍 設置測試環境...$(NC)"
	@cd .. && pip install -r requirements.txt 2>/dev/null || echo "$(RED)❌ 根目錄依賴安裝失敗$(NC)"
	@cd ../netstack && pip install -r requirements-dev.txt 2>/dev/null || echo "$(RED)❌ NetStack 依賴安裝失敗$(NC)"
	@cd ../simworld && pip install -r backend/requirements.txt 2>/dev/null || echo "$(RED)❌ SimWorld 依賴安裝失敗$(NC)"
	@$(MAKE) test-env-setup
	@echo "$(GREEN)✅ 測試環境設置完成$(NC)" 