#!/bin/bash
# =============================================================================
# NetStack 簡化啟動腳本 - 純 Cron 驅動更新模式
# 職責：
# 1. 載入映像檔預計算的數據
# 2. 快速啟動 API 服務
# 3. 數據更新完全由 Cron 處理，不在啟動時處理
# =============================================================================

set -e

echo "🚀 NetStack 簡化啟動開始..."

DATA_DIR="/app/data"
MARKER_FILE="$DATA_DIR/.data_ready"

# 確保數據目錄存在並且權限正確
mkdir -p "$DATA_DIR" || true

# 純數據載入檢查（不做更新判斷）
check_data_availability() {
    echo "📂 檢查預計算數據可用性..."
    
    # 檢查主要數據文件是否存在
    if [ ! -f "$DATA_DIR/phase0_precomputed_orbits.json" ]; then
        echo "❌ 主要數據文件缺失: phase0_precomputed_orbits.json"
        echo "💡 提示：這通常表示映像檔建構時未包含預計算數據"
        echo "💡 解決方案：重新建構映像檔或等待 Cron 更新"
        return 1
    fi
    
    # 檢查文件基本完整性
    SIZE=$(stat -c%s "$DATA_DIR/phase0_precomputed_orbits.json" 2>/dev/null || echo 0)
    if [ "$SIZE" -lt 1000000 ]; then  # 至少 1MB
        echo "❌ 數據文件過小，可能損壞 (大小: ${SIZE} bytes)"
        return 1
    fi
    
    echo "✅ 預計算數據文件正常 (大小: ${SIZE} bytes)"
    
    # 檢查數據格式完整性
    if python3 -c "
import json
try:
    with open('$DATA_DIR/phase0_precomputed_orbits.json', 'r') as f:
        data = json.load(f)
    print('✅ JSON 格式驗證通過')
    
    # 檢查實際的數據結構
    total_satellites = 0
    if 'constellations' in data:
        for const_name, const_data in data['constellations'].items():
            if 'orbit_data' in const_data and 'satellites' in const_data['orbit_data']:
                sat_count = len(const_data['orbit_data']['satellites'])
                total_satellites += sat_count
                print(f'📊 {const_name}: {sat_count} 顆衛星')
    
    print(f'📊 總衛星數量: {total_satellites} 顆')
    
    if total_satellites == 0:
        print('❌ 警告：預計算數據中沒有衛星軌道資料')
        exit(1)
    else:
        print('✅ 數據內容驗證通過')
        
except Exception as e:
    print(f'❌ JSON 格式錯誤: {e}')
    exit(1)
" 2>/dev/null; then
        echo "✅ 數據格式驗證通過"
    else
        echo "❌ 數據格式驗證失敗"
        return 1
    fi
    
    return 0
}

# 設置數據就緒標記
mark_data_ready() {
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$MARKER_FILE"
    echo "✅ 數據載入完成標記已設置"
}

# 顯示啟動資訊
show_startup_info() {
    echo
    echo "=========================================="
    echo "🎯 NetStack 純數據載入模式"
    echo "=========================================="
    echo "📂 數據目錄: $DATA_DIR"
    echo "🔄 數據更新: 由 Cron 自動處理"
    echo "⚡ 啟動模式: 快速載入，無重算"
    echo "🕒 啟動時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    
    # 顯示數據資訊
    if [ -f "$MARKER_FILE" ]; then
        echo "📊 數據就緒時間: $(cat "$MARKER_FILE")"
    fi
    
    # 顯示主要數據文件資訊
    if [ -f "$DATA_DIR/phase0_precomputed_orbits.json" ]; then
        local file_size=$(stat -c%s "$DATA_DIR/phase0_precomputed_orbits.json" 2>/dev/null || echo 0)
        local file_time=$(stat -c%y "$DATA_DIR/phase0_precomputed_orbits.json" 2>/dev/null | cut -d'.' -f1)
        echo "📁 主數據文件: $(echo "scale=2; $file_size/1024/1024" | bc -l 2>/dev/null || echo "N/A") MB"
        echo "🕐 文件時間: $file_time"
    fi
    
    echo "=========================================="
    echo
}

# 主要啟動流程
main() {
    # 1. 檢查數據可用性
    if check_data_availability; then
        echo "✅ 數據檢查通過"
    else
        echo "❌ 數據檢查失敗"
        echo "💡 系統將嘗試使用現有數據啟動，但功能可能受限"
        echo "💡 建議重新建構映像檔或等待 Cron 更新數據"
    fi
    
    # 2. 設置就緒標記
    mark_data_ready
    
    # 3. 顯示啟動資訊
    show_startup_info
    
    # 4. 啟動 API 服務
    echo "🚀 啟動 NetStack API 服務..."
    
    # 傳遞所有參數給主應用程式
    exec "$@"
}

# 錯誤處理
trap 'echo "❌ 啟動過程中發生錯誤"; exit 1' ERR

# 執行主程序
main "$@"