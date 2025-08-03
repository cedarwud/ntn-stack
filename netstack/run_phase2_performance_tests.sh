#!/bin/bash

# Phase 2.2.3 性能回歸測試執行腳本
# 
# 此腳本執行完整的性能回歸測試套件，包括：
# - API 響應時間測試
# - 系統資源使用測試  
# - 數據庫性能測試
# - 並發處理能力測試
# - 性能基準報告生成

set -e

echo "🚀 Phase 2.2.3: 性能回歸測試開始"
echo "=================================="

# 檢查依賴
echo "📋 檢查測試依賴..."
python -c "import psutil, requests, statistics" 2>/dev/null || {
    echo "❌ 缺少必要的 Python 套件"
    echo "請安裝: pip install psutil requests"
    exit 1
}

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "❌ NetStack API (8080) 不可用"
    echo "請先啟動服務: make up"
    exit 1
fi

if ! curl -s http://localhost:8888/health > /dev/null; then
    echo "⚠️ SimWorld Backend (8888) 不可用，部分測試將被跳過"
fi

echo "✅ 服務檢查完成"

# 創建性能測試目錄
mkdir -p tests/performance

# 設置測試環境變量
export PYTHONPATH="$PWD:$PYTHONPATH"

# 執行性能測試
echo ""
echo "🏃 執行性能回歸測試..."
echo "========================"

# API 性能測試
echo "📡 API 性能回歸測試..."
python -m pytest tests/performance/test_phase2_performance_regression.py::TestAPIPerformanceRegression -v -s

# 系統資源測試
echo ""
echo "💾 系統資源回歸測試..."
python -m pytest tests/performance/test_phase2_performance_regression.py::TestSystemResourceRegression -v -s

# 數據庫性能測試
echo ""
echo "🗄️ 數據庫性能回歸測試..."
python -m pytest tests/performance/test_phase2_performance_regression.py::TestDatabasePerformanceRegression -v -s

# 生成性能報告
echo ""
echo "📊 生成性能測試報告..."
python -m pytest tests/performance/test_phase2_performance_regression.py::TestPerformanceReporting::test_generate_performance_report -v -s

# 檢查報告文件
if [ -f "tests/performance/performance_report.json" ]; then
    echo ""
    echo "📋 性能測試報告摘要:"
    echo "==================="
    
    # 使用 jq 解析報告 (如果可用)
    if command -v jq &> /dev/null; then
        echo "測試時間: $(jq -r '.timestamp' tests/performance/performance_report.json)"
        echo "總測試數: $(jq -r '.total_tests' tests/performance/performance_report.json)"
        echo ""
        echo "性能基準:"
        jq -r '.benchmarks[] | "  \(.test_name): 響應時間 \(.response_time_ms | floor)ms, 成功率 \(.success_rate * 100 | floor)%"' tests/performance/performance_report.json
    else
        echo "詳細報告: tests/performance/performance_report.json"
    fi
else
    echo "⚠️ 性能報告文件未生成"
fi

echo ""
echo "✅ Phase 2.2.3 性能回歸測試完成"
echo "================================"

# 性能測試驗證
echo ""
echo "🎯 性能基準驗證:"
echo "==============="

# 檢查基本性能要求
api_available=false
if curl -s http://localhost:8080/health > /dev/null; then
    api_available=true
    
    # 測試單次響應時間
    response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8080/health)
    response_time_ms=$(echo "$response_time * 1000" | bc -l 2>/dev/null || echo "$(($response_time * 1000))")
    
    echo "API 響應時間: ${response_time_ms%.*}ms"
    
    # 基準檢查
    if (( $(echo "$response_time < 0.2" | bc -l 2>/dev/null || echo "0") )); then
        echo "✅ API 響應時間符合基準 (<200ms)"
    else
        echo "⚠️ API 響應時間可能需要優化"
    fi
fi

if [ "$api_available" = true ]; then
    echo "✅ 性能回歸測試驗證通過"
    exit 0
else
    echo "❌ 性能回歸測試驗證失敗"
    exit 1
fi