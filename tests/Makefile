# NTN Stack 測試套件 Makefile
# 簡化版本 - 支援扁平化目錄結構

.PHONY: help install test test-unit test-integration test-e2e test-api test-performance
.PHONY: test-netstack test-simworld test-deployment test-all test-smoke
.PHONY: test-priority test-critical test-high test-medium test-low
.PHONY: coverage report clean clean-all setup check-env

# 顏色定義
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
CYAN=\033[0;36m
NC=\033[0m # No Color

# 預設目標
help:
	@echo "$(CYAN)🧪 NTN Stack 測試套件$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(GREEN)📋 快速指令:$(NC)"
	@echo "  $(YELLOW)install$(NC)       - 安裝測試依賴"
	@echo "  $(YELLOW)test$(NC)          - 執行所有測試"
	@echo "  $(YELLOW)test-smoke$(NC)    - 煙霧測試"
	@echo "  $(YELLOW)test-priority$(NC) - 按優先級執行測試 (推薦)"
	@echo "  $(YELLOW)coverage$(NC)      - 執行測試並生成覆蓋率報告"
	@echo "  $(YELLOW)report$(NC)        - 生成測試摘要報告"
	@echo ""
	@echo "$(GREEN)🎯 優先級測試:$(NC)"
	@echo "  $(RED)test-critical$(NC)     - 只執行關鍵測試"
	@echo "  $(YELLOW)test-high$(NC)         - 只執行高優先級測試"
	@echo "  $(BLUE)test-medium$(NC)       - 只執行中優先級測試"
	@echo "  $(CYAN)test-low$(NC)          - 只執行低優先級測試"
	@echo ""
	@echo "$(GREEN)🔧 測試類型:$(NC)"
	@echo "  $(BLUE)test-unit$(NC)         - 單元測試"
	@echo "  $(BLUE)test-integration$(NC)  - 整合測試"
	@echo "  $(BLUE)test-e2e$(NC)          - 端到端測試"
	@echo "  $(BLUE)test-api$(NC)          - API 測試"
	@echo "  $(BLUE)test-performance$(NC)  - 性能測試"
	@echo ""
	@echo "$(GREEN)📦 模組測試:$(NC)"
	@echo "  $(BLUE)test-netstack$(NC)     - NetStack 模組測試"
	@echo "  $(BLUE)test-simworld$(NC)     - SimWorld 模組測試"
	@echo "  $(BLUE)test-deployment$(NC)   - 部署模組測試"
	@echo ""
	@echo "$(GREEN)🛠️ 工具:$(NC)"
	@echo "  $(BLUE)setup$(NC)             - 設置測試環境"
	@echo "  $(BLUE)check-env$(NC)         - 檢查環境"
	@echo "  $(BLUE)clean$(NC)             - 清理測試緩存"
	@echo "  $(BLUE)clean-all$(NC)         - 清理所有測試產物"

# ============================================================================
# 安裝和設置
# ============================================================================

install:
	@echo "$(YELLOW)📦 安裝測試依賴...$(NC)"
	@pip install -r requirements.txt
	@echo "$(GREEN)✅ 測試依賴安裝完成$(NC)"

setup: install
	@echo "$(YELLOW)🔧 設置測試環境...$(NC)"
	@mkdir -p reports/test_results reports/coverage reports/performance
	@echo "$(GREEN)✅ 測試環境設置完成$(NC)"

check-env:
	@echo "$(YELLOW)🔍 檢查測試環境...$(NC)"
	@python3 -c "import pytest, httpx, aiohttp; print('✅ 基本依賴檢查通過')"
	@ls -la reports/ 2>/dev/null && echo "✅ 報告目錄存在" || echo "❌ 報告目錄不存在"
	@echo "$(GREEN)環境檢查完成$(NC)"

# ============================================================================
# 優先級測試執行
# ============================================================================

# 按優先級執行所有測試 (推薦)
test-priority: setup
	@echo "$(RED)🎯 按優先級執行測試 - 高優先級測試必須 100% 通過$(NC)"
	@python3 priority_test_runner.py
	@echo "$(GREEN)✅ 優先級測試執行完成$(NC)"

# 關鍵測試 (最高優先級)
test-critical: setup
	@echo "$(RED)🚨 執行關鍵測試...$(NC)"
	@python3 priority_test_runner.py --priority CRITICAL
	@echo "$(GREEN)✅ 關鍵測試執行完成$(NC)"

# 高優先級測試
test-high: setup
	@echo "$(YELLOW)⚡ 執行高優先級測試...$(NC)"
	@python3 priority_test_runner.py --priority HIGH
	@echo "$(GREEN)✅ 高優先級測試執行完成$(NC)"

# 中優先級測試
test-medium: setup
	@echo "$(BLUE)🔧 執行中優先級測試...$(NC)"
	@python3 priority_test_runner.py --priority MEDIUM
	@echo "$(GREEN)✅ 中優先級測試執行完成$(NC)"

# 低優先級測試
test-low: setup
	@echo "$(CYAN)🔍 執行低優先級測試...$(NC)"
	@python3 priority_test_runner.py --priority LOW
	@echo "$(GREEN)✅ 低優先級測試執行完成$(NC)"

# 強制執行所有優先級 (即使高優先級失敗)
test-priority-all: setup
	@echo "$(YELLOW)🔄 強制執行所有優先級測試...$(NC)"
	@python3 priority_test_runner.py --continue-on-failure
	@echo "$(GREEN)✅ 所有優先級測試執行完成$(NC)"

# ============================================================================
# 傳統測試執行
# ============================================================================

# 執行所有測試
test: setup
	@echo "$(YELLOW)🚀 執行所有測試...$(NC)"
	@python3 run_tests.py --type all --summary
	@echo "$(GREEN)✅ 所有測試執行完成$(NC)"

# 煙霧測試
test-smoke: setup
	@echo "$(YELLOW)💨 執行煙霧測試...$(NC)"
	@python3 run_tests.py --type smoke --summary
	@echo "$(GREEN)✅ 煙霧測試完成$(NC)"

# 測試類型
test-unit: setup
	@echo "$(BLUE)🔧 執行單元測試...$(NC)"
	@python3 run_tests.py --type unit --summary

test-integration: setup
	@echo "$(BLUE)🔗 執行整合測試...$(NC)"
	@python3 run_tests.py --type integration --summary

test-e2e: setup
	@echo "$(BLUE)🎭 執行端到端測試...$(NC)"
	@python3 run_tests.py --type e2e --summary

test-api: setup
	@echo "$(BLUE)🌐 執行 API 測試...$(NC)"
	@python3 run_tests.py --type api --summary

test-performance: setup
	@echo "$(BLUE)⚡ 執行性能測試...$(NC)"
	@python3 run_tests.py --type performance --summary

# 模組測試
test-netstack: setup
	@echo "$(CYAN)📡 執行 NetStack 模組測試...$(NC)"
	@python3 run_tests.py --type unit --module netstack --summary

test-simworld: setup
	@echo "$(CYAN)🌍 執行 SimWorld 模組測試...$(NC)"
	@python3 run_tests.py --type unit --module simworld --summary

test-deployment: setup
	@echo "$(CYAN)🚀 執行部署模組測試...$(NC)"
	@python3 run_tests.py --type unit --module deployment --summary

# ============================================================================
# 報告和覆蓋率
# ============================================================================

coverage: setup
	@echo "$(YELLOW)📊 執行測試並生成覆蓋率報告...$(NC)"
	@python3 run_tests.py --type all --coverage --html --summary
	@echo "$(GREEN)✅ 覆蓋率報告生成完成$(NC)"
	@echo "$(BLUE)📄 HTML 報告位置: reports/test_results/$(NC)"
	@echo "$(BLUE)📊 覆蓋率報告位置: reports/coverage/html/$(NC)"

report:
	@echo "$(YELLOW)📋 生成測試摘要報告...$(NC)"
	@python3 tools/test_summary.py
	@echo "$(GREEN)✅ 測試摘要報告生成完成$(NC)"

# 優先級測試報告
report-priority:
	@echo "$(YELLOW)📊 顯示優先級測試結果...$(NC)"
	@test -f reports/priority_test_results.json && \
		python3 -c "import json; print(json.dumps(json.load(open('reports/priority_test_results.json')), indent=2, ensure_ascii=False))" || \
		echo "$(RED)❌ 未找到優先級測試結果，請先執行 make test-priority$(NC)"

# ============================================================================
# 清理
# ============================================================================

clean:
	@echo "$(YELLOW)🧹 清理測試緩存...$(NC)"
	@rm -rf .pytest_cache/ __pycache__/ .coverage
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -f temp_result.json
	@echo "$(GREEN)✅ 測試緩存清理完成$(NC)"

clean-reports:
	@echo "$(YELLOW)🗑️ 清理測試報告...$(NC)"
	@rm -rf reports/test_results/* reports/coverage/*
	@rm -f reports/priority_test_results.json
	@echo "$(GREEN)✅ 測試報告清理完成$(NC)"

clean-all: clean clean-reports
	@echo "$(YELLOW)🧽 清理所有測試產物...$(NC)"
	@rm -f *.log test_*.json uav_*.json
	@echo "$(GREEN)✅ 所有測試產物清理完成$(NC)"

# ============================================================================
# 進階用法
# ============================================================================

# 並行測試
test-parallel: setup
	@echo "$(YELLOW)⚡ 執行並行測試...$(NC)"
	@pytest -n auto unit/ integration/ e2e/ api/ --tb=short
	@echo "$(GREEN)✅ 並行測試完成$(NC)"

# 詳細測試
test-verbose: setup
	@echo "$(YELLOW)📝 執行詳細測試...$(NC)"
	@pytest -v -s unit/ integration/ e2e/ api/ --tb=long
	@echo "$(GREEN)✅ 詳細測試完成$(NC)"

# 只執行失敗的測試
test-failed: setup
	@echo "$(YELLOW)🔄 重新執行失敗的測試...$(NC)"
	@pytest --lf unit/ integration/ e2e/ api/
	@echo "$(GREEN)✅ 失敗測試重執行完成$(NC)"

# 調試模式
test-debug: setup
	@echo "$(YELLOW)🐛 執行調試模式測試...$(NC)"
	@pytest --pdb unit/ integration/ e2e/ api/
	@echo "$(GREEN)✅ 調試模式測試完成$(NC)"

# CI 模式 (適合持續整合)
test-ci: setup
	@echo "$(YELLOW)🤖 執行 CI 模式測試...$(NC)"
	@python3 priority_test_runner.py 2>&1 | tee test_output.log
	@echo "$(GREEN)✅ CI 模式測試完成$(NC)" 