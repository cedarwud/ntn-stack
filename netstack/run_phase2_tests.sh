#!/bin/bash
# Phase 2 自動化測試框架執行腳本

set -e

echo "🧪 Phase 2.2.1: 擴展單元測試覆蓋率至90%"
echo "================================================"

# 檢查測試環境
echo "📋 檢查測試環境..."
python3 --version
python3 -c "import pytest; print(f'pytest版本: {pytest.__version__}')"

# 檢查測試文件
echo "📋 檢查測試文件..."
find tests/ -name "test_*.py" -exec echo "  ✓ {}" \;

# 運行單元測試並生成覆蓋率報告
echo "🏃 運行單元測試..."
python3 -m pytest tests/unit/ -v \
    --cov=config \
    --cov=netstack_api/services \
    --cov-report=term-missing \
    --cov-report=html:coverage_html \
    --cov-fail-under=85 \
    --tb=short

# 檢查覆蓋率結果
echo "📊 覆蓋率報告已生成至 coverage_html/"

# 運行性能測試 (如果存在)
if [ -d "tests/performance" ]; then
    echo "🚀 運行性能測試..."
    python3 -m pytest tests/performance/ -v --tb=short
fi

# 生成測試摘要
echo "📋 測試摘要："
echo "  - 單元測試：✅ 已完成"
echo "  - 覆蓋率目標：≥85%"
echo "  - HTML報告：coverage_html/index.html"

echo "✅ Phase 2.2.1 測試執行完成"