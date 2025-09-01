#!/bin/bash
# =============================================================================
# NetStack 建構失敗回退腳本
# 當建構時六階段處理失敗時，在運行時執行最小化處理
# =============================================================================

set -e

echo "🔧 NetStack 建構失敗回退模式..."

DATA_DIR="/app/data"
BUILD_STATUS_FILE="$DATA_DIR/.build_status"

# 檢查建構失敗狀態
check_build_failure() {
    echo "🔍 檢查建構失敗狀態..."
    
    if [ -f "$BUILD_STATUS_FILE" ]; then
        local status=$(cat "$BUILD_STATUS_FILE")
        echo "📋 建構狀態: $status"
        
        if echo "$status" | grep -q "BUILD_FAILED=true"; then
            echo "❌ 確認：建構時處理失敗"
            return 0
        elif echo "$status" | grep -q "RUNTIME_PROCESSING_REQUIRED=true"; then
            echo "⏰ 確認：需要運行時處理"
            return 0
        fi
    fi
    
    echo "❌ 未找到建構失敗標記"
    return 1
}

# 最小化運行時處理
minimal_runtime_processing() {
    echo "🚀 執行最小化運行時處理..."
    
    # 創建必要目錄
    mkdir -p "$DATA_DIR"/{tle_calculation_outputs,intelligent_filtering_outputs,signal_analysis_outputs,timeseries_preprocessing_outputs,data_integration_outputs,dynamic_pool_planning_outputs}
    
    # 設定環境
    export PYTHONPATH="/app:/app/src:/app/netstack"
    export PYTHONUNBUFFERED=1
    
    cd /app
    
    # 嘗試執行最小化六階段（較短超時）
    echo "⏰ 執行最小化六階段處理（10分鐘超時）..."
    if timeout 600 python scripts/run_six_stages.py --data-dir "$DATA_DIR" > /tmp/runtime_six_stage.log 2>&1; then
        echo "✅ 運行時六階段處理成功"
        echo "RUNTIME_PROCESSING_COMPLETED=true" > "$DATA_DIR/.runtime_status"
        return 0
    else
        echo "⚠️ 運行時六階段處理也失敗"
        echo "最後日誌："
        tail -20 /tmp/runtime_six_stage.log
        
        # 創建基本空數據結構以保持API可用
        create_minimal_data_structure
        return 1
    fi
}

# 創建基本數據結構
create_minimal_data_structure() {
    echo "🔧 創建基本數據結構以保持API可用..."
    
    # 創建空的JSON結構
    local basic_metadata='{"metadata": {"processing_timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "processing_mode": "minimal_fallback", "total_satellites": 0}, "constellations": {}}'
    
    # 創建基本文件
    echo "$basic_metadata" > "$DATA_DIR/intelligent_filtering_outputs/intelligent_filtered_output.json"
    echo "$basic_metadata" > "$DATA_DIR/signal_analysis_outputs/signal_event_analysis_output.json"
    echo "$basic_metadata" > "$DATA_DIR/data_integration_outputs/integrated_data_output.json"
    echo "$basic_metadata" > "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
    
    echo "✅ 基本數據結構已創建"
    echo "MINIMAL_STRUCTURE_CREATED=true" > "$DATA_DIR/.minimal_status"
}

# 設置回退環境
setup_fallback_env() {
    echo "⚡ 設置回退環境..."
    
    # 設置環境變數
    export PRECOMPUTED_DATA_ENABLED=false
    export ORBIT_CACHE_PRELOAD=false
    export BUILD_TIME_PREPROCESSED=false
    export FALLBACK_MODE=true
    export MINIMAL_DATA_MODE=true
    
    echo "✅ 回退環境已設置"
}

# 顯示回退信息
show_fallback_info() {
    echo
    echo "=========================================="
    echo "🔧 NetStack 回退模式啟動"
    echo "=========================================="
    echo "📂 數據目錄: $DATA_DIR"
    echo "🔧 運行模式: 建構失敗回退模式"
    echo "⚠️ 功能限制: 部分功能可能不可用"
    echo "🕒 啟動時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "=========================================="
    echo
}

# 主要回退流程
main() {
    # 1. 檢查建構失敗狀態
    if ! check_build_failure; then
        echo "❌ 不是建構失敗狀態，不應該使用回退腳本"
        exit 1
    fi
    
    # 2. 執行最小化運行時處理
    minimal_runtime_processing
    
    # 3. 設置回退環境
    setup_fallback_env
    
    # 4. 顯示回退信息
    show_fallback_info
    
    # 5. 啟動API服務
    echo "🚀 啟動 NetStack API 服務（回退模式）..."
    echo "⚡ 設置回退環境變數..."
    
    # 確保API可以啟動的最小環境
    export PRECOMPUTED_DATA_ENABLED=false
    export ORBIT_CACHE_PRELOAD=false
    export BUILD_TIME_PREPROCESSED=false
    export FALLBACK_MODE=true
    export MINIMAL_DATA_MODE=true
    
    echo "📋 啟動參數: $@"
    
    # 傳遞所有參數給主應用程式
    exec "$@"
}

# 錯誤處理
trap 'echo "❌ 回退啟動過程中發生錯誤"; exit 1' ERR

# 執行主程序
main "$@"