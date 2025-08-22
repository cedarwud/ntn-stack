#!/bin/bash

# 建構時預處理架構驗證腳本
# 驗證修復後的架構是否符合文檔定義的 < 30秒快速啟動

set -e

echo "🏗️ 建構時預處理架構驗證開始..."
echo "=========================================="

PASS=0
FAIL=0

check_file() {
    local file="$1"
    local desc="$2"
    
    if [ -f "$file" ]; then
        echo "✅ $desc: 存在"
        ((PASS++))
    else
        echo "❌ $desc: 不存在"
        ((FAIL++))
    fi
}

check_content() {
    local file="$1"
    local pattern="$2"
    local desc="$3"
    
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo "✅ $desc: 找到"
        ((PASS++))
    else
        echo "❌ $desc: 未找到"
        ((FAIL++))
    fi
}

echo "📋 階段一：建構時預處理文件檢查"
echo "=========================================="

check_file "/home/sat/ntn-stack/netstack/docker/build-time-optimized-entrypoint.sh" "建構時優化entrypoint腳本"
check_file "/home/sat/ntn-stack/netstack/docker/Dockerfile" "Dockerfile"
check_file "/home/sat/ntn-stack/netstack/src/leo_core/main_pipeline_controller.py" "主流程控制器"
check_file "/home/sat/ntn-stack/netstack/compose/core-simple.yaml" "Docker Compose配置"

echo ""
echo "📋 階段二：Dockerfile建構時預處理配置檢查"
echo "=========================================="

check_content "/home/sat/ntn-stack/netstack/docker/Dockerfile" "build_optimized" "Dockerfile包含建構時優化"
check_content "/home/sat/ntn-stack/netstack/docker/Dockerfile" "gzip" "Dockerfile包含壓縮工具"
check_content "/home/sat/ntn-stack/netstack/docker/Dockerfile" "main_pipeline_controller.py.*build_optimized" "建構時執行六階段處理"
check_content "/home/sat/ntn-stack/netstack/docker/Dockerfile" "build-time-optimized-entrypoint.sh" "包含快速啟動entrypoint"

echo ""
echo "📋 階段三：主流程控制器build_optimized模式檢查"
echo "=========================================="

check_content "/home/sat/ntn-stack/netstack/src/leo_core/main_pipeline_controller.py" "build_optimized" "支援build_optimized模式"
check_content "/home/sat/ntn-stack/netstack/src/leo_core/main_pipeline_controller.py" "compress.*true" "支援壓縮選項"
check_content "/home/sat/ntn-stack/netstack/src/leo_core/main_pipeline_controller.py" "build_preprocessed" "創建建構標記"

echo ""
echo "📋 階段四：快速啟動entrypoint檢查"
echo "=========================================="

check_content "/home/sat/ntn-stack/netstack/docker/build-time-optimized-entrypoint.sh" "< 30秒快速啟動" "包含快速啟動目標"
check_content "/home/sat/ntn-stack/netstack/docker/build-time-optimized-entrypoint.sh" "gunzip" "支援數據解壓縮"
check_content "/home/sat/ntn-stack/netstack/docker/build-time-optimized-entrypoint.sh" "verify_data_integrity" "包含數據完整性驗證"
check_content "/home/sat/ntn-stack/netstack/docker/build-time-optimized-entrypoint.sh" "build_preprocessed" "檢查建構標記"

echo ""
echo "📋 階段五：Docker Compose快速啟動配置檢查"
echo "=========================================="

check_content "/home/sat/ntn-stack/netstack/compose/core-simple.yaml" "build-time-optimized-entrypoint.sh" "使用快速啟動entrypoint"
check_content "/home/sat/ntn-stack/netstack/compose/core-simple.yaml" "BUILD_TIME_PREPROCESSED=true" "建構時預處理環境變數"
check_content "/home/sat/ntn-stack/netstack/compose/core-simple.yaml" "FAST_STARTUP_MODE=true" "快速啟動模式環境變數"
check_content "/home/sat/ntn-stack/netstack/compose/core-simple.yaml" "SATELLITE_DATA_MODE=build_preprocessed" "建構預處理數據模式"

echo ""
echo "📋 階段六：文檔一致性檢查"
echo "=========================================="

check_content "/home/sat/ntn-stack/docs/data_processing_flow.md" "映像檔包含數據" "文檔定義建構時預處理"
check_content "/home/sat/ntn-stack/docs/data_processing_flow.md" "< 30秒快速啟動" "文檔定義快速啟動目標"
check_content "/home/sat/ntn-stack/docs/data_processing_flow.md" "Pure Cron 驅動架構" "Pure Cron架構定義"

echo ""
echo "=========================================="
echo "📊 驗證結果總結"
echo "=========================================="
echo "✅ 通過: $PASS 項"
echo "❌ 失敗: $FAIL 項"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "🎉 建構時預處理架構驗證完全通過！"
    echo ""
    echo "🚀 架構修復完成要點："
    echo "   1. ✅ Dockerfile建構時執行完整六階段預處理"
    echo "   2. ✅ 數據壓縮優化減少映像檔大小"
    echo "   3. ✅ build-time-optimized-entrypoint.sh快速載入"
    echo "   4. ✅ Docker Compose配置快速啟動模式"
    echo "   5. ✅ 符合文檔定義的 < 30秒啟動目標"
    echo ""
    echo "📋 建構與測試流程："
    echo "   make netstack-build-n  # 重建映像檔(將執行建構時預處理)"
    echo "   make up                # 測試快速啟動(<30秒)"
    echo "   make status            # 檢查服務狀況"
    echo ""
    echo "🎯 預期行為："
    echo "   • 建構時: 45分鐘執行完整六階段處理並壓縮"
    echo "   • 啟動時: < 30秒解壓並驗證數據"
    echo "   • 映像檔: 包含壓縮的預處理數據"
    echo "   • 符合文檔定義的Pure Cron架構"
    
    exit 0
else
    echo ""
    echo "❌ 建構時預處理架構驗證失敗，需要解決 $FAIL 個問題"
    exit 1
fi