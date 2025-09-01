#!/bin/bash
set -e

echo "🚀 NetStack Volume持久化智能啟動..."

DATA_DIR="/app/data"
VOLUME_DATA_DIR="/app/data"  # 使用現有的Volume掛載點
CACHE_MARKER="$VOLUME_DATA_DIR/.cache_ready"
CACHE_TIMESTAMP="$VOLUME_DATA_DIR/.cache_timestamp"

# 設置Python模塊搜索路徑
export PYTHONPATH="/app:/app/src:/app/netstack:$PYTHONPATH"

# 確保Volume目錄存在
mkdir -p "$VOLUME_DATA_DIR" "$DATA_DIR"

check_volume_cache() {
    echo "🔍 檢查Volume持久化緩存..."
    
    # 檢查緩存標記
    if [ ! -f "$CACHE_MARKER" ]; then
        echo "❌ 未找到Volume緩存標記"
        return 1
    fi
    
    if [ ! -f "$CACHE_TIMESTAMP" ]; then
        echo "❌ 未找到緩存時間戳"
        return 1
    fi
    
    # 檢查關鍵緩存文件（基於六階段輸出）
    critical_cached_files=(
        "$VOLUME_DATA_DIR/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
        "$VOLUME_DATA_DIR/leo_outputs/data_integration_outputs/data_integration_output.json"
        "$VOLUME_DATA_DIR/leo_outputs/timeseries_preprocessing_outputs/starlink_enhanced.json"
        "$VOLUME_DATA_DIR/leo_outputs/signal_analysis_outputs/signal_event_analysis_output.json"
    )
    
    missing_count=0
    for file in "${critical_cached_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ 缺少緩存文件: $file"
            missing_count=$((missing_count + 1))
        fi
    done
    
    if [ $missing_count -gt 0 ]; then
        echo "❌ Volume緩存不完整，缺少 $missing_count 個文件"
        return 1
    fi
    
    # 檢查緩存新鮮度
    cache_time=$(cat "$CACHE_TIMESTAMP" 2>/dev/null || echo "0")
    current_time=$(date +%s)
    age_hours=$(( (current_time - cache_time) / 3600 ))
    
    if [ "$age_hours" -gt 168 ]; then  # 7天過期
        echo "⏰ Volume緩存過期 (${age_hours}小時前)，需要更新"
        return 1
    fi
    
    echo "✅ Volume緩存有效且新鮮 (${age_hours}小時前)"
    return 0
}

load_from_volume_cache() {
    echo "📂 從Volume加載緩存數據到工作目錄..."
    
    # 由於使用統一的Volume掛載點，無需複製或連結
    echo "📂 Volume數據直接可用於API服務"
    
    echo "✅ Volume緩存數據已就緒"
}

generate_and_cache_data() {
    echo "🔨 生成數據並緩存到Volume..."
    
    # 清理舊緩存
    rm -rf "$VOLUME_DATA_DIR"/*_outputs/ 2>/dev/null || true
    
    # 執行完整六階段處理，輸出到Volume
    cd /app
    if timeout 2700 python scripts/run_six_stages.py --data-dir "$DATA_DIR"; then
        echo "✅ 數據生成完成"
        
        # 設置緩存標記
        echo "$(date +%s)" > "$CACHE_TIMESTAMP"
        echo "VOLUME_CACHE_READY=true" > "$CACHE_MARKER"
        
        # 加載到工作目錄
        load_from_volume_cache
        
        return 0
    else
        echo "❌ 數據生成失敗"
        return 1
    fi
}

check_incremental_update_needed() {
    echo "🔄 檢查是否需要增量更新..."
    
    if [ ! -f "$CACHE_TIMESTAMP" ]; then
        return 0  # 需要更新
    fi
    
    # 檢查TLE數據是否更新
    if [ -d "/app/tle_data" ]; then
        latest_tle=$(find /app/tle_data -name "*.tle" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$latest_tle" ] && [ -f "$latest_tle" ]; then
            tle_time=$(stat -c%Y "$latest_tle" 2>/dev/null || echo 0)
            cache_time=$(cat "$CACHE_TIMESTAMP" 2>/dev/null || echo 0)
            
            if [ "$tle_time" -gt "$cache_time" ]; then
                echo "🔄 檢測到TLE數據更新，需要增量更新"
                return 0
            fi
        fi
    fi
    
    echo "✅ 數據新鮮，無需增量更新"
    return 1
}

execute_incremental_update() {
    echo "⚡ 執行智能增量更新..."
    
    # 使用增量更新管理器
    cd /app
    if python -c "
from shared_core.incremental_update_manager import IncrementalUpdateManager
import sys
manager = IncrementalUpdateManager()
update_scope = manager.detect_tle_changes()
if update_scope:
    success = manager.execute_incremental_update(update_scope)
    print('✅ 增量更新完成' if success else '❌ 增量更新失敗')
    sys.exit(0 if success else 1)
else:
    print('ℹ️ 無需增量更新')
    sys.exit(0)
"; then
        # 更新緩存時間戳
        echo "$(date +%s)" > "$CACHE_TIMESTAMP"
        echo "✅ 智能增量更新完成"
        return 0
    else
        echo "⚠️ 增量更新失敗，繼續使用現有緩存"
        return 1
    fi
}

# 主邏輯：智能Volume緩存啟動決策
echo "🧠 Volume持久化智能啟動決策..."

startup_mode=""
startup_time=""

if check_volume_cache; then
    echo "✅ 使用Volume緩存數據 - 快速啟動模式"
    load_from_volume_cache
    startup_mode="Volume緩存"
    startup_time="< 10秒"
    
    # 檢查是否需要增量更新
    if check_incremental_update_needed; then
        execute_incremental_update || echo "⚠️ 增量更新失敗，繼續使用現有緩存"
    fi
    
else
    echo "⚠️ Volume緩存無效，執行完整數據生成..."
    if generate_and_cache_data; then
        startup_mode="完整重新生成"
        startup_time="20-45分鐘 (首次啟動)"
    else
        echo "❌ 數據生成失敗，嘗試緊急模式..."
        startup_mode="緊急降級模式"
        startup_time="基礎API"
    fi
fi

echo "🎯 NetStack API 服務啟動中..."
echo "   啟動模式: $startup_mode"
echo "   預估時間: $startup_time"
echo "   數據位置: Volume持久化 (跨容器重啟保留)"

# 顯示Volume使用情況
volume_usage=$(du -sh "$VOLUME_DATA_DIR" 2>/dev/null | cut -f1 || echo "未知")
echo "   Volume使用: $volume_usage"

# 執行實際的應用程式
exec "$@"