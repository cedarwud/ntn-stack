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
    
    # 檢查基本文件是否存在 (修正文件名)
    if [ ! -f "$DATA_DIR/enhanced_satellite_data.json" ]; then
        echo "❌ 主要數據文件缺失，需要重新計算"
        return 1
    fi
    
    # 檢查文件大小（應該 > 200KB，合理的地理可見性數據大小）
    SIZE=$(stat -c%s "$DATA_DIR/enhanced_satellite_data.json" 2>/dev/null || echo 0)
    if [ "$SIZE" -lt 200000 ]; then
        echo "❌ 數據文件太小，可能損壞 (大小: ${SIZE} bytes)"
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
    
    # 獲取預計算數據的時間戳
    DATA_TIME=$(stat -c%Y "$DATA_DIR/enhanced_satellite_data.json" 2>/dev/null || echo 0)
    
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
    
    # 檢查 Python 腳本執行結果
    if python docker/build_with_phase0_data_refactored.py; then
        echo "✅ Python 腳本執行成功"
    else
        echo "❌ Python 腳本執行失敗"
        exit 1
    fi
    
    # 檢查生成是否成功
    echo "🔍 檢查數據文件是否存在: $DATA_DIR/enhanced_satellite_data.json"
    ls -la "$DATA_DIR"/ || echo "❌ 無法列出數據目錄"
    
    if [ -f "$DATA_DIR/enhanced_satellite_data.json" ]; then
        # 檢查文件大小
        FILE_SIZE=$(stat -c%s "$DATA_DIR/enhanced_satellite_data.json" 2>/dev/null || echo 0)
        echo "📊 數據文件大小: $FILE_SIZE bytes"
        
        # 創建完成標記
        echo "$(date -Iseconds)" > "$MARKER_FILE"
        echo "✅ 數據重生完成"
        
        # 顯示生成的文件信息
        echo "📊 生成的數據文件:"
        ls -lh "$DATA_DIR"/*.json 2>/dev/null || true
    else
        echo "❌ 數據生成失敗 - 文件不存在"
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