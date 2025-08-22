#!/bin/bash
# =============================================================================
# NetStack 建構時優化啟動腳本 - 快速載入預處理數據
# 實現文檔定義的 < 30秒快速啟動目標
# =============================================================================

set -e

echo "🚀 NetStack 建構時優化啟動..."

DATA_DIR="/app/data"
BUILD_MARKER="$DATA_DIR/.build_preprocessed"
FAST_STARTUP_MARKER="$DATA_DIR/.fast_startup"

# 檢查建構時預處理狀態
check_build_preprocessed() {
    echo "🔍 檢查建構時預處理狀態..."
    
    if [ ! -f "$BUILD_MARKER" ]; then
        echo "❌ 未找到建構時預處理標記文件"
        echo "💡 這通常表示建構時預處理失敗或未執行"
        return 1
    fi
    
    if [ ! -f "$FAST_STARTUP_MARKER" ]; then
        echo "❌ 未找到快速啟動標記"
        return 1
    fi
    
    echo "✅ 建構時預處理標記確認"
    
    # 顯示建構信息
    if command -v jq >/dev/null 2>&1; then
        echo "📊 建構信息："
        jq . "$BUILD_MARKER" 2>/dev/null || cat "$BUILD_MARKER"
    else
        echo "📊 建構信息："
        cat "$BUILD_MARKER"
    fi
    
    return 0
}

# 解壓縮並載入預處理數據
load_preprocessed_data() {
    echo "📦 載入建構時預處理數據..."
    
    local loaded_files=0
    local missing_large_files=0
    
    # 解壓縮所有壓縮的預處理文件
    echo "🗜️ 解壓縮預處理數據文件..."
    local total_compressed_size=0
    local total_uncompressed_size=0
    
    for gz_file in $(find "$DATA_DIR" -name "*.json.gz" 2>/dev/null); do
        if [ -f "$gz_file" ]; then
            local gz_size=$(stat -c%s "$gz_file" 2>/dev/null || echo 0)
            total_compressed_size=$((total_compressed_size + gz_size))
            
            echo "  解壓縮: $(basename "$gz_file") ($(echo "scale=1; $gz_size/1024/1024" | bc 2>/dev/null || echo "?")MB)"
            gunzip -f "$gz_file"
            
            local json_file="${gz_file%.gz}"
            if [ -f "$json_file" ]; then
                local json_size=$(stat -c%s "$json_file" 2>/dev/null || echo 0)
                total_uncompressed_size=$((total_uncompressed_size + json_size))
            fi
            
            ((loaded_files++))
        fi
    done
    
    if [ $loaded_files -gt 0 ]; then
        echo "📊 解壓縮統計: $loaded_files 個文件"
        echo "   壓縮總大小: $(echo "scale=1; $total_compressed_size/1024/1024" | bc 2>/dev/null || echo "?")MB"
        echo "   解壓後大小: $(echo "scale=1; $total_uncompressed_size/1024/1024" | bc 2>/dev/null || echo "?")MB"
        echo "   節省空間: $(echo "scale=1; ($total_uncompressed_size-$total_compressed_size)*100/$total_uncompressed_size" | bc 2>/dev/null || echo "?")%"
    fi
    
    # 檢查是否需要重新生成TLE文件（唯一排除的超大文件）
    if [ ! -f "$DATA_DIR/leo_outputs/leo_outputs/tle_orbital_output.json" ]; then
        echo "⚠️ TLE軌道文件缺失 (2.3GB，映像檔中已排除以節省空間)"
        echo "💡 將在後台重新生成此文件 (不影響API啟動)"
        ((missing_large_files++))
        
        # 後台重新生成（異步，不阻塞啟動）
        (
            echo "🔄 後台重新生成TLE軌道數據..."
            cd /app && \
            python src/stages/tle_orbital_calculation_processor.py --output "$DATA_DIR/leo_outputs/leo_outputs/tle_orbital_output.json" >/dev/null 2>&1 && \
            echo "✅ TLE軌道數據重新生成完成" || \
            echo "❌ TLE軌道數據重新生成失敗"
        ) &
    fi
    
    echo "✅ 預處理數據載入完成 ($loaded_files 個壓縮文件已解壓)"
    if [ $missing_large_files -gt 0 ]; then
        echo "🔄 $missing_large_files 個超大文件正在後台重新生成"
    fi
    
    return 0
}

# 驗證數據完整性
verify_data_integrity() {
    echo "🔍 驗證數據完整性..."
    
    # 檢查主要數據文件
    if [ ! -f "$DATA_DIR/enhanced_satellite_data.json" ]; then
        echo "❌ 主要數據文件缺失"
        return 1
    fi
    
    # 檢查文件大小
    local file_size=$(stat -c%s "$DATA_DIR/enhanced_satellite_data.json" 2>/dev/null || echo 0)
    if [ "$file_size" -lt 100000 ]; then  # 至少 100KB
        echo "❌ 主要數據文件過小 (${file_size} bytes)"
        return 1
    fi
    
    echo "✅ 主要數據文件驗證通過 (${file_size} bytes)"
    
    # 檢查JSON格式
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "
import json
try:
    with open('$DATA_DIR/enhanced_satellite_data.json', 'r') as f:
        data = json.load(f)
    print('✅ JSON格式驗證通過')
    
    # 檢查數據結構
    if 'constellations' in data:
        total_sats = 0
        for const_name, const_data in data['constellations'].items():
            if 'orbit_data' in const_data and 'satellites' in const_data['orbit_data']:
                sat_count = len(const_data['orbit_data']['satellites'])
                total_sats += sat_count
                print(f'📊 {const_name}: {sat_count} 顆衛星')
        print(f'📊 總衛星數: {total_sats} 顆')
        
        if total_sats == 0:
            print('❌ 數據中無衛星信息')
            exit(1)
    else:
        print('⚠️ 數據結構異常，但仍可使用')
        
except Exception as e:
    print(f'❌ JSON驗證失敗: {e}')
    exit(1)
" 2>/dev/null; then
            echo "✅ 數據結構驗證通過"
        else
            echo "❌ 數據結構驗證失敗"
            return 1
        fi
    else
        echo "⚠️ Python3 不可用，跳過JSON驗證"
    fi
    
    return 0
}

# 設置快速啟動環境
setup_fast_startup_env() {
    echo "⚡ 設置快速啟動環境..."
    
    # 設置環境變數
    export PRECOMPUTED_DATA_ENABLED=true
    export ORBIT_CACHE_PRELOAD=true
    export BUILD_TIME_PREPROCESSED=true
    export FAST_STARTUP_MODE=true
    
    # 創建啟動就緒標記
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$DATA_DIR/.startup_ready"
    
    echo "✅ 快速啟動環境已設置"
}

# 顯示啟動信息
show_startup_info() {
    echo
    echo "=========================================="
    echo "⚡ NetStack 建構時優化快速啟動"
    echo "=========================================="
    echo "📂 數據目錄: $DATA_DIR"
    echo "🏗️ 建構模式: 預處理完成"
    echo "⚡ 啟動模式: 快速載入 (< 30秒)"
    echo "🕒 啟動時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    
    # 顯示數據文件信息
    if [ -f "$DATA_DIR/enhanced_satellite_data.json" ]; then
        local file_size=$(stat -c%s "$DATA_DIR/enhanced_satellite_data.json" 2>/dev/null || echo 0)
        local file_time=$(stat -c%y "$DATA_DIR/enhanced_satellite_data.json" 2>/dev/null | cut -d'.' -f1)
        echo "📁 主數據文件: $(echo "scale=2; $file_size/1024/1024" | bc -l 2>/dev/null || echo "N/A") MB"
        echo "🕐 數據時間: $file_time"
    fi
    
    # 顯示建構信息
    if [ -f "$BUILD_MARKER" ]; then
        echo "🏗️ 建構時間: $(jq -r '.build_time // "Unknown"' "$BUILD_MARKER" 2>/dev/null || echo "Unknown")"
    fi
    
    echo "=========================================="
    echo
}

# 主要啟動流程
main() {
    local start_time=$(date +%s)
    
    # 1. 檢查建構時預處理狀態
    if check_build_preprocessed; then
        echo "✅ 建構時預處理確認通過"
    else
        echo "❌ 建構時預處理檢查失敗"
        echo "💡 將嘗試回退到運行時處理模式"
        echo "💡 這會導致較長的啟動時間"
        # 這裡可以選擇回退到其他entrypoint或直接啟動
    fi
    
    # 2. 載入預處理數據
    if load_preprocessed_data; then
        echo "✅ 數據載入完成"
    else
        echo "❌ 數據載入失敗"
        exit 1
    fi
    
    # 3. 驗證數據完整性
    if verify_data_integrity; then
        echo "✅ 數據驗證完成"
    else
        echo "❌ 數據驗證失敗"
        exit 1
    fi
    
    # 4. 設置快速啟動環境
    setup_fast_startup_env
    
    # 5. 顯示啟動信息
    show_startup_info
    
    # 計算啟動時間
    local end_time=$(date +%s)
    local startup_time=$((end_time - start_time))
    echo "⚡ 啟動時間: ${startup_time} 秒"
    
    if [ $startup_time -le 30 ]; then
        echo "🎯 ✅ 達成 < 30秒快速啟動目標！"
    else
        echo "⚠️ 啟動時間超過30秒目標，但仍可正常運行"
    fi
    
    # 6. 啟動API服務
    echo "🚀 啟動 NetStack API 服務..."
    
    # 傳遞所有參數給主應用程式
    exec "$@"
}

# 錯誤處理
trap 'echo "❌ 啟動過程中發生錯誤"; exit 1' ERR

# 執行主程序
main "$@"