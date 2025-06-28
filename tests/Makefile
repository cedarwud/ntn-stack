# NTN-Stack 統一測試 Makefile

.PHONY: test test-quick test-unit test-integration test-performance test-e2e test-paper test-gymnasium clean help

# 預設目標
all: test

# 完整測試套件
test:
	@echo "🧪 執行完整測試套件..."
	python run_all_tests.py --type=all --report

# 快速測試
test-quick:
	@echo "⚡ 執行快速測試..."
	python run_all_tests.py --type=all --quick --report

# 單元測試
test-unit:
	@echo "🔧 執行單元測試..."
	python run_all_tests.py --type=unit

# 整合測試
test-integration:
	@echo "🔗 執行整合測試..."
	python run_all_tests.py --type=integration

# 效能測試
test-performance:
	@echo "⚡ 執行效能測試..."
	python run_all_tests.py --type=performance

# 端到端測試
test-e2e:
	@echo "🔄 執行端到端測試..."
	python run_all_tests.py --type=e2e

# 論文復現測試
test-paper:
	@echo "📚 執行論文復現測試..."
	python run_all_tests.py --type=paper

test-paper-stage1:
	@echo "📚 執行論文階段一測試..."
	python run_all_tests.py --type=paper --stage=1

test-paper-stage2:
	@echo "📚 執行論文階段二測試..."
	python run_all_tests.py --type=paper --stage=2

# Gymnasium測試
test-gymnasium:
	@echo "🤖 執行Gymnasium測試..."
	python run_all_tests.py --type=gymnasium

test-paper-stage2:
	@echo "📚 執行論文階段二測試..."
	python paper_tests.py --stage=2

# Gymnasium RL測試
test-gymnasium:
	@echo "🎮 執行Gymnasium RL測試..."
	python gymnasium_tests.py --env=all

# 清理
clean:
	@echo "🧹 清理測試相關檔案..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

# 說明
help:
	@echo "📋 NTN-Stack 統一測試系統"
	@echo ""
	@echo "可用目標："
	@echo "  test              - 執行完整測試套件"
	@echo "  test-quick        - 執行快速測試"
	@echo "  test-unit         - 執行單元測試"
	@echo "  test-integration  - 執行整合測試"
	@echo "  test-performance  - 執行效能測試"
	@echo "  test-e2e          - 執行端到端測試"
	@echo "  test-paper        - 執行論文復現測試"
	@echo "  test-paper-stage1 - 執行論文階段一測試"
	@echo "  test-paper-stage2 - 執行論文階段二測試"
	@echo "  test-gymnasium    - 執行Gymnasium RL測試"
	@echo "  clean             - 清理測試檔案"
	@echo "  help              - 顯示此說明"
