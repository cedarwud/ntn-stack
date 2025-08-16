#!/bin/bash
set -e

echo "🚀 NetStack 智能啟動開始..."

DATA_DIR="/app/data"
MARKER_FILE="$DATA_DIR/.data_ready"

# 確保數據目錄存在並且權限正確
mkdir -p "$DATA_DIR" || true

# 混合模式：檢查數據完整性和新鮮度
check_data_integrity() {
    echo "🔍 智能數據檢查開始..."
    
    # 檢查 LEO 核心系統輸出文件是否存在
    if [ ! -f "$DATA_DIR/phase1_final_report.json" ] && [ ! -f "$DATA_DIR/stage2_filtering_results.json" ]; then
        echo "❌ LEO 核心系統輸出文件缺失，需要重新計算"
        return 1
    fi
    
    # 檢查文件大小（彈性檢查，允許較小的檔案）
    if [ -f "$DATA_DIR/phase1_final_report.json" ]; then
        SIZE=$(stat -c%s "$DATA_DIR/phase1_final_report.json" 2>/dev/null || echo 0)
        if [ "$SIZE" -lt 10000 ]; then
            echo "❌ LEO 主要輸出文件太小，可能損壞 (大小: ${SIZE} bytes)"
            return 1
        fi
    elif [ -f "$DATA_DIR/stage2_filtering_results.json" ]; then
        SIZE=$(stat -c%s "$DATA_DIR/stage2_filtering_results.json" 2>/dev/null || echo 0)
        if [ "$SIZE" -lt 10000 ]; then
            echo "❌ LEO 篩選結果文件太小，可能損壞 (大小: ${SIZE} bytes)"
            return 1
        fi
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
    
    # 獲取 LEO 核心系統輸出的時間戳（彈性檢查）
    if [ -f "$DATA_DIR/phase1_final_report.json" ]; then
        DATA_TIME=$(stat -c%Y "$DATA_DIR/phase1_final_report.json" 2>/dev/null || echo 0)
    elif [ -f "$DATA_DIR/stage2_filtering_results.json" ]; then
        DATA_TIME=$(stat -c%Y "$DATA_DIR/stage2_filtering_results.json" 2>/dev/null || echo 0)
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
    
    # 執行 LEO 核心系統 (Phase 1 - 統一四組件管道)
    echo "🔨 LEO 核心系統：四組件統一管道 (TLE載入→篩選→信號分析→動態規劃)..."
    echo "🎯 分層輸出策略：F1/F2→/tmp(臨時)，F3/A1→$DATA_DIR(永久)"
    echo "⏱️ 預估處理時間：2-5分鐘 (開發模式) 或 15-30分鐘 (完整模式)"
    if timeout 1800 python src/leo_core/main.py --output-dir "$DATA_DIR" --full-test; then
        echo "✅ LEO 核心系統完成"
    else
        echo "❌ LEO 核心系統失敗或超時 (30分鐘)"
        echo "🔍 檢查是否有部分輸出可用..."
        if [ -f "$DATA_DIR/stage1_tle_loading_results.json" ] || [ -f "$DATA_DIR/stage2_filtering_results.json" ]; then
            echo "⚠️ 發現部分輸出，繼續啟動 API 服務 (降級模式)"
        else
            exit 1
        fi
    fi
    
    # 檢查 LEO 核心系統輸出是否成功
    echo "🔍 檢查 LEO 核心系統輸出文件是否存在: $DATA_DIR/phase1_final_report.json"
    ls -la "$DATA_DIR"/ || echo "❌ 無法列出數據目錄"
    
    # 檢查輸出文件
    if [ -f "$DATA_DIR/phase1_final_report.json" ]; then
        # 檢查文件大小
        FILE_SIZE=$(stat -c%s "$DATA_DIR/phase1_final_report.json" 2>/dev/null || echo 0)
        echo "📊 LEO 核心系統輸出文件大小: $FILE_SIZE bytes"
        
        # 創建完成標記
        echo "$(date -Iseconds)" > "$MARKER_FILE"
        echo "✅ LEO 核心系統數據生成完成"
        
        # 顯示生成的文件信息
        echo "📊 生成的 LEO 核心系統文件:"
        ls -lh "$DATA_DIR"/phase1_*.json 2>/dev/null || true
        ls -lh "$DATA_DIR"/stage*_*.json 2>/dev/null || true
    elif [ -f "$DATA_DIR/stage2_filtering_results.json" ]; then
        echo "⚠️ 主要輸出文件不存在，但發現篩選結果，繼續啟動 (降級模式)"
        echo "$(date -Iseconds)" > "$MARKER_FILE"
        ls -lh "$DATA_DIR"/stage*_*.json 2>/dev/null || true
    else
        echo "❌ LEO 核心系統數據生成失敗 - 無可用輸出文件"
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