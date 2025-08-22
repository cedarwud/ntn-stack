#!/bin/bash
set -e

echo "🚀 NetStack 運行時智能啟動..."

DATA_DIR="/app/data"
BUILD_TIMESTAMP_FILE="$DATA_DIR/.build_timestamp"
BUILD_MODE_FILE="$DATA_DIR/.build_mode"

# 設置Python模塊搜索路徑
export PYTHONPATH="/app:/app/src:/app/netstack:$PYTHONPATH"

# 檢查是否有建構時預處理的數據
check_build_time_data() {
    echo "🔍 檢查建構時預處理數據..."
    
    # 檢查建構標記文件
    if [ ! -f "$BUILD_MODE_FILE" ]; then
        echo "❌ 未找到建構模式標記，需要運行時處理"
        return 1
    fi
    
    if [ ! -f "$BUILD_TIMESTAMP_FILE" ]; then
        echo "❌ 未找到建構時間戳，需要運行時處理"
        return 1
    fi
    
    # 檢查關鍵預處理文件
    critical_files=(
        "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
        "$DATA_DIR/data_integration_outputs/data_integration_output.json"
        "$DATA_DIR/timeseries_preprocessing_outputs/enhanced_timeseries_output.json"
        "$DATA_DIR/signal_analysis_outputs/signal_event_analysis_output.json"
    )
    
    missing_count=0
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ 缺少關鍵文件: $file"
            missing_count=$((missing_count + 1))
        fi
    done
    
    if [ $missing_count -gt 0 ]; then
        echo "❌ 預處理數據不完整，缺少 $missing_count 個關鍵文件"
        return 1
    fi
    
    # 檢查數據新鮮度（如果需要）
    build_time=$(cat "$BUILD_TIMESTAMP_FILE")
    echo "✅ 建構時預處理數據完整且可用"
    echo "   建構時間: $build_time"
    echo "   數據文件: $((4 - missing_count))/4 完整"
    
    return 0
}

# 智能增量更新檢查
check_incremental_update_needed() {
    echo "🔄 檢查是否需要增量更新..."
    
    # 檢查TLE數據是否更新
    if [ -d "/app/tle_data" ]; then
        # 找到最新的TLE文件
        latest_tle=$(find /app/tle_data -name "*.tle" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$latest_tle" ] && [ -f "$latest_tle" ]; then
            tle_time=$(stat -c%Y "$latest_tle" 2>/dev/null || echo 0)
            build_time_epoch=$(date -d "$(cat "$BUILD_TIMESTAMP_FILE")" +%s 2>/dev/null || echo 0)
            
            if [ "$tle_time" -gt "$build_time_epoch" ]; then
                echo "🔄 檢測到TLE數據更新，建議執行增量更新"
                return 0
            fi
        fi
    fi
    
    echo "✅ 數據新鮮，無需增量更新"
    return 1
}

# 執行增量更新
execute_incremental_update() {
    echo "🔄 執行智能增量更新..."
    
    # 使用增量更新管理器
    cd /app
    if python -c "
from shared_core.incremental_update_manager import IncrementalUpdateManager
manager = IncrementalUpdateManager()
update_needed = manager.detect_tle_changes()
if update_needed:
    manager.execute_incremental_update(update_needed)
    print('✅ 增量更新完成')
else:
    print('ℹ️ 無需更新')
    "; then
        echo "✅ 智能增量更新完成"
        return 0
    else
        echo "⚠️ 增量更新失敗，繼續使用現有數據"
        return 1
    fi
}

# 運行時緊急重新生成（最後手段）
emergency_regenerate() {
    echo "🚨 緊急模式：執行運行時完整重新生成..."
    
    # 清理可能損壞的數據
    find "$DATA_DIR" -name "*.json" -type f -delete 2>/dev/null || true
    
    # 執行完整六階段處理
    cd /app
    if timeout 2700 python src/leo_core/main_pipeline_controller.py --mode full --data-dir "$DATA_DIR"; then
        echo "✅ 緊急重新生成完成"
        echo "$(date -Iseconds)" > "$DATA_DIR/.runtime_generation"
        return 0
    else
        echo "❌ 緊急重新生成失敗"
        return 1
    fi
}

# 主邏輯：智能啟動決策
echo "🧠 智能啟動決策開始..."

if check_build_time_data; then
    echo "✅ 使用建構時預處理數據 - 快速啟動模式"
    
    # 檢查是否需要增量更新
    if check_incremental_update_needed; then
        execute_incremental_update || echo "⚠️ 增量更新失敗，繼續使用現有數據"
    fi
    
    startup_time="< 10秒"
    
elif [ -f "/app/data/.runtime_generation" ]; then
    echo "✅ 使用運行時生成數據"
    startup_time="已就緒"
    
else
    echo "⚠️ 無可用預處理數據，執行緊急重新生成..."
    if emergency_regenerate; then
        startup_time="45分鐘 (緊急模式)"
    else
        echo "❌ 所有數據生成方案都失敗，啟動基礎API服務"
        startup_time="基礎模式"
    fi
fi

echo "🎯 NetStack API 服務啟動中..."
echo "   預估啟動時間: $startup_time"
echo "   數據模式: $([ -f "$BUILD_MODE_FILE" ] && echo "建構時預處理" || echo "運行時處理")"

# 執行實際的應用程式
exec "$@"