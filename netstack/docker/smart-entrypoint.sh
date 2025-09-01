#!/bin/bash
set -e

echo "🚀 NetStack 智能啟動開始..."

# 🔧 緊急修復模式：自動檢測並跳過有問題的六階段系統
if ! python -c "import sys; sys.path.append('/app/scripts'); import run_six_stages" 2>/dev/null; then
    echo "⚡ 檢測到六階段系統導入錯誤，啟用緊急模式：跳過數據生成，直接啟動 API"
    exec "$@"
    exit 0
fi

DATA_DIR="/app/data"
MARKER_FILE="$DATA_DIR/.data_ready"

# 確保數據目錄存在並且權限正確
mkdir -p "$DATA_DIR" || true

# 混合模式：檢查數據完整性和新鮮度
check_data_integrity() {
    echo "🔍 智能數據檢查開始..."
    
    # 檢查六階段系統輸出文件是否存在 (混合模式：Stage1-2記憶體，Stage3-6檔案)
    # Stage3-6 應該有檔案輸出，Stage1-2 使用記憶體傳遞
    critical_files=(
        "$DATA_DIR/signal_analysis_outputs/signal_event_analysis_output.json"
        "$DATA_DIR/timeseries_preprocessing_outputs/enhanced_timeseries_output.json"
        "$DATA_DIR/data_integration_outputs/data_integration_output.json"
        "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
    )
    
    missing_files=0
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ 關鍵階段輸出檔案缺失: $file"
            missing_files=$((missing_files + 1))
        fi
    done
    
    if [ $missing_files -gt 0 ]; then
        echo "❌ 六階段系統輸出不完整，需要重新計算 (缺失 $missing_files 個檔案)"
        return 1
    fi
    
    # 檢查關鍵檔案大小（彈性檢查，動態池規劃作為完整性指標）
    if [ -f "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" ]; then
        SIZE=$(stat -c%s "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" 2>/dev/null || echo 0)
        if [ "$SIZE" -lt 10000 ]; then
            echo "❌ 動態池規劃輸出文件太小，可能損壞 (大小: ${SIZE} bytes)"
            return 1
        fi
        echo "✅ 動態池規劃輸出文件大小正常: ${SIZE} bytes"
    else
        echo "❌ 動態池規劃輸出文件不存在"
        return 1
    fi
    
    # 混合模式關鍵：比較 TLE 數據和預計算數據的時間戳
    echo "📊 檢查 TLE 數據 vs 預計算數據的新鮮度..."
    
    # 獲取最新 TLE 數據的修改時間
    LATEST_TLE_TIME=0
    if [ -d "/app/tle_data" ]; then
        # 找到最新的 TLE 文件時間戳
        for tle_file in $(find /app/tle_data -name "*.tle" -o -name "*.json" 2>/dev/null); do
            if [ -f "$tle_file" ]; then
                FILE_TIME=$(stat -c%Y "$tle_file" 2>/dev/null || echo 0)
                if [ "$FILE_TIME" -gt "$LATEST_TLE_TIME" ]; then
                    LATEST_TLE_TIME=$FILE_TIME
                    LATEST_TLE_FILE="$tle_file"
                fi
            fi
        done
    fi
    
    # 獲取六階段系統輸出的時間戳（使用動態池規劃作為完整性指標）
    if [ -f "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" ]; then
        DATA_TIME=$(stat -c%Y "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" 2>/dev/null || echo 0)
    else
        DATA_TIME=0
    fi
    
    # 比較時間戳
    if [ "$LATEST_TLE_TIME" -gt 0 ] && [ "$DATA_TIME" -gt 0 ]; then
        TIME_DIFF=$((LATEST_TLE_TIME - DATA_TIME))
        echo "📅 TLE 最新時間: $(date -d @$LATEST_TLE_TIME '+%Y-%m-%d %H:%M:%S')"
        echo "📅 預計算時間: $(date -d @$DATA_TIME '+%Y-%m-%d %H:%M:%S')"
        
        if [ "$TIME_DIFF" -gt 3600 ]; then  # TLE 數據比預計算數據新超過 1 小時
            echo "🔄 TLE 數據已更新，需要重新計算 (差異: $((TIME_DIFF/3600)) 小時)"
            return 1
        else
            echo "✅ 預計算數據是最新的，可以快速啟動！"
        fi
    else
        echo "⚠️ 無法比較時間戳，假設需要重新計算"
        return 1
    fi
    
    # 更新或創建標記文件
    echo "$(date -Iseconds)" > "$MARKER_FILE"
    echo "✅ 數據完整性和新鮮度檢查通過"
    return 0
}

# 重新生成數據
regenerate_data() {
    echo "🔄 開始重新生成預計算數據..."
    
    # 確保目錄存在
    mkdir -p "$DATA_DIR"
    
    # 清理舊數據（保留目錄結構）
    find "$DATA_DIR" -type f -delete 2>/dev/null || true
    
    # 執行預計算
    cd /app
    echo "🔨 執行真實數據生成 (Phase 2.5 完整數據)..."
    
    # 執行增強六階段系統 (完整流程)
    echo "🔨 增強六階段系統：完整統一管道 (TLE載入→智能篩選→信號分析→時間序列→數據整合→動態池規劃)..."
    echo "🎯 unified controller: run_six_stages.py"
    echo "⏱️ 預估處理時間：5-10分鐘 (開發模式) 或 20-45分鐘 (完整模式)"
    if timeout 2700 python scripts/run_six_stages.py --data-dir "$DATA_DIR"; then
        echo "✅ 增強六階段系統完成"
    else
        echo "❌ 增強六階段系統失敗或超時 (45分鐘)"
        echo "🔍 檢查是否有部分輸出可用..."
        if [ -f "$DATA_DIR/tle_calculation_outputs/tle_sgp4_calculation_output.json" ] || [ -f "$DATA_DIR/intelligent_filtering_outputs/intelligent_filtered_output.json" ]; then
            echo "⚠️ 發現部分輸出，繼續啟動 API 服務 (降級模式)"
        else
            exit 1
        fi
    fi
    
    # 檢查增強六階段系統輸出是否成功
    echo "🔍 檢查增強六階段系統輸出文件是否存在: $DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
    ls -la "$DATA_DIR"/ || echo "❌ 無法列出數據目錄"
    
    # 檢查輸出文件
    if [ -f "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" ]; then
        # 檢查文件大小
        FILE_SIZE=$(stat -c%s "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" 2>/dev/null || echo 0)
        echo "📊 增強六階段系統輸出文件大小: $FILE_SIZE bytes"
        
        # 創建完成標記
        echo "$(date -Iseconds)" > "$MARKER_FILE"
        echo "✅ 增強六階段系統數據生成完成"
        
        # 顯示生成的文件信息
        echo "📊 生成的增強六階段系統文件:"
        ls -lh "$DATA_DIR"/*_outputs/*.json 2>/dev/null || true
    elif [ -f "$DATA_DIR/intelligent_filtering_outputs/intelligent_filtered_output.json" ]; then
        echo "⚠️ 主要輸出文件不存在，但發現篩選結果，繼續啟動 (降級模式)"
        echo "$(date -Iseconds)" > "$MARKER_FILE"
        ls -lh "$DATA_DIR"/*_outputs/*.json 2>/dev/null || true
    else
        echo "❌ 增強六階段系統數據生成失敗 - 無可用輸出文件"
        echo "🔍 數據目錄內容:"
        ls -la "$DATA_DIR"/ || echo "無法訪問數據目錄"
        exit 1
    fi
}

# 主邏輯
echo "🔍 檢查數據狀態..."
if check_data_integrity; then
    echo "📊 使用現有數據"
    ls -lh "$DATA_DIR"/*.json 2>/dev/null | head -3
else
    echo "⚠️ 數據不完整，需要重新生成"
    regenerate_data
fi

echo "🎯 啟動 NetStack API 服務..."

# 設置Python模塊搜索路徑
export PYTHONPATH="/app:$PYTHONPATH"

exec "$@"