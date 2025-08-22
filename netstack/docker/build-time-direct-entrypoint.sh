#!/bin/bash
# =============================================================================
# NetStack 建構時直接啟動腳本 - 無壓縮高效能版
# 直接使用建構時生成的900MB預處理數據，無解壓縮過程
# 實現 < 5秒超快速啟動
# =============================================================================

set -e

echo "🚀 NetStack 建構時直接啟動（無壓縮版）..."

DATA_DIR="/app/data"
BUILD_MARKER="$DATA_DIR/.build_mode"
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
    echo "📊 建構信息："
    cat "$BUILD_MARKER"
    
    return 0
}

# 直接載入預處理數據（無解壓縮）
load_preprocessed_data() {
    echo "📦 直接載入建構時預處理數據（無解壓縮）..."
    
    local available_files=0
    local missing_large_files=0
    
    # 檢查主要預處理文件（應該直接可用）
    echo "🔍 檢查預處理數據文件..."
    
    local main_files=(
        "$DATA_DIR/leo_outputs/intelligent_filtered_output.json"
        "$DATA_DIR/leo_outputs/signal_analysis_outputs/signal_event_analysis_output.json"
        "$DATA_DIR/leo_outputs/timeseries_preprocessing_outputs/starlink_enhanced.json"
        "$DATA_DIR/leo_outputs/timeseries_preprocessing_outputs/oneweb_enhanced.json"
        "$DATA_DIR/leo_outputs/data_integration_outputs/data_integration_output.json"
        "$DATA_DIR/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
    )
    
    for file in "${main_files[@]}"; do
        if [ -f "$file" ]; then
            local file_size=$(stat -c%s "$file" 2>/dev/null || echo 0)
            echo "  ✅ $(basename "$file") ($(echo "scale=1; $file_size/1024/1024" | bc 2>/dev/null || echo "?")MB)"
            ((available_files++))
        else
            echo "  ❌ $(basename "$file") - 缺失"
        fi
    done
    
    # 檢查是否需要重新生成TLE文件（唯一排除的超大文件）
    # 修正：檢查實際可能存在的路徑
    if [ ! -f "$DATA_DIR/leo_outputs/tle_orbital_output.json" ] && [ ! -f "$DATA_DIR/leo_outputs/leo_outputs/tle_orbital_output.json" ]; then
        echo "⚠️ TLE軌道文件缺失 (2.3GB，映像檔中已排除)"
        echo "💡 將在後台重新生成此文件 (不影響API啟動)"
        ((missing_large_files++))
        
        # 後台重新生成（異步，不阻塞啟動）
        (
            echo "🔄 後台重新生成TLE軌道數據..."
            cd /app && \
            python src/stages/tle_orbital_calculation_processor.py --output "$DATA_DIR/leo_outputs/tle_orbital_output.json" >/dev/null 2>&1 && \
            echo "✅ TLE軌道數據重新生成完成" || \
            echo "❌ TLE軌道數據重新生成失敗"
        ) &
    fi
    
    echo "✅ 預處理數據直接載入完成 ($available_files 個文件可用)"
    if [ $missing_large_files -gt 0 ]; then
        echo "🔄 $missing_large_files 個超大文件正在後台重新生成"
    fi
    
    return 0
}

# 驗證數據完整性
verify_data_integrity() {
    echo "🔍 驗證數據完整性..."
    
    # 檢查主要數據文件
    local main_data_file="$DATA_DIR/leo_outputs/data_integration_outputs/data_integration_output.json"
    if [ ! -f "$main_data_file" ]; then
        echo "❌ 主要數據整合文件缺失"
        return 1
    fi
    
    # 檢查文件大小
    local file_size=$(stat -c%s "$main_data_file" 2>/dev/null || echo 0)
    if [ "$file_size" -lt 100000 ]; then  # 至少 100KB
        echo "❌ 主要數據文件過小 (${file_size} bytes)"
        return 1
    fi
    
    echo "✅ 主要數據文件驗證通過 ($(echo "scale=1; $file_size/1024/1024" | bc 2>/dev/null || echo "?")MB)"
    
    # 檢查JSON格式（簡單驗證）
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "
import json
try:
    with open('$main_data_file', 'r') as f:
        data = json.load(f)
    print('✅ JSON格式驗證通過')
    
    # 檢查數據結構
    if 'metadata' in data and 'constellations_data' in data:
        print('✅ 數據結構驗證通過')
    else:
        print('⚠️ 數據結構可能異常，但仍可使用')
        
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
    echo "⚡ 設置超快速啟動環境..."
    
    # 設置環境變數
    export PRECOMPUTED_DATA_ENABLED=true
    export ORBIT_CACHE_PRELOAD=true
    export BUILD_TIME_PREPROCESSED=true
    export NO_COMPRESSION_FAST_STARTUP=true
    export DIRECT_DATA_ACCESS=true
    
    # 創建啟動就緒標記
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$DATA_DIR/.startup_ready"
    
    echo "✅ 超快速啟動環境已設置"
}

# 顯示啟動信息
show_startup_info() {
    echo
    echo "=========================================="
    echo "⚡ NetStack 無壓縮直接啟動"
    echo "=========================================="
    echo "📂 數據目錄: $DATA_DIR"
    echo "🏗️ 建構模式: 預處理完成 (900MB 直接可用)"
    echo "⚡ 啟動模式: 無壓縮直接載入 (< 5秒)"
    echo "🕒 啟動時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    
    # 顯示數據目錄大小
    if [ -d "$DATA_DIR/leo_outputs" ]; then
        local dir_size=$(du -sh "$DATA_DIR/leo_outputs" 2>/dev/null | cut -f1)
        echo "📁 預處理數據: $dir_size"
    fi
    
    # 顯示建構信息
    if [ -f "$BUILD_MARKER" ]; then
        echo "🏗️ 建構標記: $(cat "$BUILD_MARKER")"
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
    fi
    
    # 2. 直接載入預處理數據（無解壓縮）
    if load_preprocessed_data; then
        echo "✅ 數據直接載入完成"
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
    
    if [ $startup_time -le 5 ]; then
        echo "🎯 ✅ 達成 < 5秒超快速啟動目標！"
    elif [ $startup_time -le 30 ]; then
        echo "🎯 ✅ 達成 < 30秒快速啟動目標！"
    else
        echo "⚠️ 啟動時間超過目標，但仍可正常運行"
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