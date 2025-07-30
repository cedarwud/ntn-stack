#!/bin/bash
set -e

echo "🚀 NetStack 智能啟動開始..."

DATA_DIR="/app/data"
MARKER_FILE="$DATA_DIR/.data_ready"

# 確保數據目錄存在並且權限正確
mkdir -p "$DATA_DIR" || true

# 檢查數據是否存在且完整
check_data_integrity() {
    if [ ! -f "$MARKER_FILE" ]; then
        echo "❌ 數據標記文件不存在"
        return 1
    fi
    
    if [ ! -f "$DATA_DIR/phase0_precomputed_orbits.json" ]; then
        echo "❌ 主要數據文件缺失"
        return 1
    fi
    
    # 檢查數據新鮮度（7天內）
    LAST_UPDATE=$(cat "$MARKER_FILE" 2>/dev/null || echo "")
    if [ -n "$LAST_UPDATE" ]; then
        CURRENT_TIME=$(date +%s)
        LAST_UPDATE_TIME=$(date -d "$LAST_UPDATE" +%s 2>/dev/null || echo 0)
        WEEK_IN_SECONDS=604800  # 7天
        
        if [ $((CURRENT_TIME - LAST_UPDATE_TIME)) -gt $WEEK_IN_SECONDS ]; then
            echo "⏰ 數據超過1週，需要更新 (上次更新: $LAST_UPDATE)"
            return 1
        fi
        echo "📅 數據新鮮度檢查通過 (上次更新: $LAST_UPDATE)"
    else
        echo "⚠️ 無法讀取更新時間，假設數據過期"
        return 1
    fi
    
    # 檢查文件大小（應該 > 100MB）
    SIZE=$(stat -c%s "$DATA_DIR/phase0_precomputed_orbits.json" 2>/dev/null || echo 0)
    if [ "$SIZE" -lt 100000000 ]; then
        echo "❌ 數據文件太小，可能損壞 (大小: ${SIZE} bytes)"
        return 1
    fi
    
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
    echo "🔨 執行真實數據生成 (Phase 0 完整數據)..."
    python build_with_phase0_data.py
    
    # 檢查生成是否成功
    if [ -f "$DATA_DIR/phase0_precomputed_orbits.json" ]; then
        # 創建完成標記
        echo "$(date -Iseconds)" > "$MARKER_FILE"
        echo "✅ 數據重生完成"
        
        # 顯示生成的文件信息
        echo "📊 生成的數據文件:"
        ls -lh "$DATA_DIR"/*.json 2>/dev/null || true
    else
        echo "❌ 數據生成失敗"
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
exec "$@"