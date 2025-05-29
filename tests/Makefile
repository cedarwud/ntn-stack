# Makefile for NTN Stack Integration Tests
# 用於執行 Mesh 橋接和 UAV 備援機制的整合測試

.PHONY: help test-mesh test-uav test-all install-deps clean logs

# 默認目標
help:
	@echo "🧪 NTN Stack Integration Tests"
	@echo "=============================="
	@echo ""
	@echo "可用目標："
	@echo "  help         - 顯示此幫助信息"
	@echo "  install-deps - 安裝測試依賴"
	@echo "  test-mesh    - 執行 Mesh 橋接功能測試"
	@echo "  test-uav     - 執行 UAV 備援機制測試"
	@echo "  test-all     - 執行所有整合測試"
	@echo "  clean        - 清理測試日誌和臨時文件"
	@echo "  logs         - 查看最新的測試日誌"
	@echo ""
	@echo "測試前提："
	@echo "  1. NetStack API 服務已啟動 (localhost:8080)"
	@echo "  2. 必要的依賴已安裝"
	@echo "  3. 測試環境已配置"

# 安裝測試依賴
install-deps:
	@echo "📦 安裝測試依賴..."
	pip install httpx pytest pytest-asyncio

# 執行 Mesh 橋接功能測試
test-mesh:
	@echo "🔧 執行 Tier-1 Mesh 網絡與 5G 核心網橋接功能測試..."
	@echo "=================================================="
	python test_mesh_bridge_integration.py

# 執行 UAV 備援機制測試
test-uav:
	@echo "🚁 執行 UAV 失聯後的 Mesh 網絡備援機制測試..."
	@echo "============================================="
	python test_uav_mesh_failover_integration.py

# 執行所有整合測試
test-all:
	@echo "🚀 執行完整的整合測試套件..."
	@echo "============================"
	@echo "測試範圍："
	@echo "  - 10. Tier-1 Mesh 網絡與 5G 核心網橋接"
	@echo "  - 11. UAV 失聯後的 Mesh 網絡備援機制"
	@echo ""
	python run_all_integration_tests.py

# 清理測試日誌和臨時文件
clean:
	@echo "🧹 清理測試文件..."
	rm -f integration_tests_*.log
	rm -f *.pyc
	rm -rf __pycache__
	rm -rf .pytest_cache
	@echo "✅ 清理完成"

# 查看最新的測試日誌
logs:
	@echo "📄 查看最新測試日誌..."
	@if ls integration_tests_*.log 1> /dev/null 2>&1; then \
		ls -t integration_tests_*.log | head -1 | xargs cat; \
	else \
		echo "沒有找到測試日誌文件"; \
	fi

# 檢查測試環境
check-env:
	@echo "🔍 檢查測試環境..."
	@echo "檢查 NetStack API 服務..."
	@curl -s http://localhost:8080/health > /dev/null && echo "✅ NetStack API 服務正常" || echo "❌ NetStack API 服務未啟動"
	@echo "檢查 Python 依賴..."
	@python -c "import httpx; print('✅ httpx 已安裝')" 2>/dev/null || echo "❌ httpx 未安裝"
	@python -c "import asyncio; print('✅ asyncio 可用')" 2>/dev/null || echo "❌ asyncio 不可用"

# 執行快速煙霧測試
smoke-test:
	@echo "💨 執行快速煙霧測試..."
	@curl -s http://localhost:8080/health | python -m json.tool
	@curl -s http://localhost:8080/api/v1/mesh/nodes | python -m json.tool | head -20

# 顯示測試覆蓋範圍
coverage:
	@echo "📊 測試覆蓋範圍"
	@echo "==============="
	@echo ""
	@echo "🔧 Mesh 橋接功能測試涵蓋："
	@echo "  ✅ Mesh 節點創建和管理"
	@echo "  ✅ 橋接網關創建和配置"
	@echo "  ✅ 網絡拓撲發現和管理"
	@echo "  ✅ 性能指標監控"
	@echo "  ✅ 路由優化算法"
	@echo "  ✅ 封包轉發機制"
	@echo "  ✅ 負載測試"
	@echo "  ✅ 故障恢復能力"
	@echo ""
	@echo "🚁 UAV 備援機制測試涵蓋："
	@echo "  ✅ UAV 失聯檢測"
	@echo "  ✅ 自動 Mesh 切換"
	@echo "  ✅ 手動網絡切換"
	@echo "  ✅ 衛星連接恢復"
	@echo "  ✅ 切換性能測試"
	@echo "  ✅ 多 UAV 並發切換"
	@echo "  ✅ 2秒內重建連線驗證"
	@echo ""
	@echo "🎯 關鍵要求驗證："
	@echo "  ✅ 協議轉換和 QoS 映射"
	@echo "  ✅ 實時連接質量監控"
	@echo "  ✅ 智能故障檢測算法"
	@echo "  ✅ 快速恢復機制"
	@echo "  ✅ 性能要求滿足（2s 內重建連線）" 