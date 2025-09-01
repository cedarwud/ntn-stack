#!/bin/bash
# =============================================================================
# NetStack 智能啟動選擇器
# 根據建構時處理的結果，自動選擇最適合的啟動腳本
# =============================================================================

set -e

echo "🧠 NetStack 智能啟動選擇器..."

DATA_DIR="/app/data"
BUILD_MARKER="$DATA_DIR/.build_mode"
BUILD_STATUS="$DATA_DIR/.build_status"

# 分析建構狀態並選擇啟動模式
select_startup_mode() {
    echo "🔍 分析建構狀態..."
    
    # 檢查建構時預處理是否成功
    if [ -f "$BUILD_MARKER" ]; then
        local build_mode=$(cat "$BUILD_MARKER")
        echo "📋 建構標記: $build_mode"
        
        if echo "$build_mode" | grep -q "BUILD_TIME_PREPROCESSED=true"; then
            echo "✅ 建構時預處理成功完成"
            echo "🚀 選擇模式: 直接啟動模式 (最高效能)"
            exec /usr/local/bin/build-time-direct-entrypoint.sh "$@"
        fi
        
        if echo "$build_mode" | grep -q "RUNTIME_PROCESSING_REQUIRED=true"; then
            echo "⏰ 需要運行時處理"
            echo "🚀 選擇模式: 回退處理模式"
            exec /usr/local/bin/fallback-entrypoint.sh "$@"
        fi
    fi
    
    # 檢查建構失敗狀態
    if [ -f "$BUILD_STATUS" ]; then
        local build_status=$(cat "$BUILD_STATUS")
        echo "📋 建構狀態: $build_status"
        
        if echo "$build_status" | grep -q "BUILD_FAILED=true"; then
            echo "❌ 建構時處理失敗"
            echo "🚀 選擇模式: 回退處理模式"
            exec /usr/local/bin/fallback-entrypoint.sh "$@"
        fi
        
        if echo "$build_status" | grep -q "RUNTIME_PROCESSING_REQUIRED=true"; then
            echo "⏰ 需要運行時處理"
            echo "🚀 選擇模式: 回退處理模式"
            exec /usr/local/bin/fallback-entrypoint.sh "$@"
        fi
    fi
    
    # 檢查數據目錄狀態
    if [ -d "$DATA_DIR" ]; then
        local file_count=$(find "$DATA_DIR" -name "*.json" -type f 2>/dev/null | wc -l)
        if [ "$file_count" -gt 3 ]; then
            echo "✅ 發現 $file_count 個數據文件"
            echo "🚀 選擇模式: 直接啟動模式"
            exec /usr/local/bin/build-time-direct-entrypoint.sh "$@"
        fi
    fi
    
    # 默認回退到運行時處理
    echo "⚠️ 無法確定建構狀態，使用回退模式"
    echo "🚀 選擇模式: 回退處理模式 (安全模式)"
    exec /usr/local/bin/fallback-entrypoint.sh "$@"
}

# 顯示選擇器信息
echo "=========================================="
echo "🧠 NetStack 智能啟動選擇器"
echo "=========================================="
echo "📂 數據目錄: $DATA_DIR"
echo "🔍 分析建構狀態並選擇最適啟動模式..."
echo "=========================================="

# 執行啟動模式選擇
select_startup_mode "$@"