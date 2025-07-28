#!/bin/bash
# =============================================================================
# 每日 TLE 數據自動下載腳本
# 用途：LEO 衛星換手 RL 研究數據收集
# 作者：自動生成
# 建議執行時間：UTC 08:00 (台灣時間 16:00)
# =============================================================================

set -euo pipefail  # 嚴格錯誤處理

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TLE_DATA_DIR="$PROJECT_ROOT/tle_data"
LOG_FILE="$PROJECT_ROOT/logs/tle_download.log"

# 創建日誌目錄
mkdir -p "$(dirname "$LOG_FILE")"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date -u '+%Y-%m-%d %H:%M:%S UTC')
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# 獲取當前 UTC 日期
get_current_date() {
    date -u '+%Y%m%d'
}

# 檢查檔案是否已存在
file_exists() {
    local filepath="$1"
    if [[ -f "$filepath" && -s "$filepath" ]]; then
        return 0  # 檔案存在且非空
    else
        return 1  # 檔案不存在或為空
    fi
}

# 下載檔案
download_file() {
    local url="$1"
    local output_path="$2"
    local description="$3"
    
    log_info "下載 $description..."
    log_info "URL: $url"
    log_info "輸出: $output_path"
    
    # 確保輸出目錄存在
    mkdir -p "$(dirname "$output_path")"
    
    # 使用 curl 下載，設定超時和重試
    if curl -L --fail --connect-timeout 30 --max-time 300 --retry 3 \
            -o "$output_path" "$url"; then
        
        # 檢查檔案大小
        local file_size=$(stat -c%s "$output_path")
        if [[ $file_size -lt 100 ]]; then
            log_error "$description 下載檔案過小 ($file_size bytes)，可能下載失敗"
            return 1
        fi
        
        log_success "$description 下載成功 ($file_size bytes)"
        return 0
    else
        log_error "$description 下載失敗"
        return 1
    fi
}

# 驗證 TLE 數據
validate_tle_data() {
    local tle_file="$1"
    local expected_date="$2"
    local constellation="$3"
    
    log_info "驗證 TLE 數據: $constellation"
    
    # 檢查檔案格式
    local line_count=$(wc -l < "$tle_file")
    if [[ $line_count -lt 6 ]]; then
        log_error "TLE 檔案行數過少 ($line_count 行)"
        return 1
    fi
    
    # 檢查是否為 TLE 格式
    local first_line1=$(sed -n '2p' "$tle_file")
    local first_line2=$(sed -n '3p' "$tle_file")
    
    if [[ ! "$first_line1" =~ ^1\  ]] || [[ ! "$first_line2" =~ ^2\  ]]; then
        log_error "TLE 格式驗證失敗"
        return 1
    fi
    
    # 提取 epoch date (簡化版檢查)
    local epoch_year=$(echo "$first_line1" | cut -c19-20)
    local epoch_day=$(echo "$first_line1" | cut -c21-23)
    
    # 計算當前年份的後兩位
    local current_year_short=$(date -u '+%y')
    
    # 檢查年份是否合理 (允許當年或前一年)
    local prev_year_short=$(printf "%02d" $(( ($(date -u '+%y') - 1 + 100) % 100 )))
    
    if [[ "$epoch_year" != "$current_year_short" && "$epoch_year" != "$prev_year_short" ]]; then
        log_warn "TLE epoch 年份 ($epoch_year) 可能不是最新數據"
    fi
    
    # 計算衛星數量
    local satellite_count=$((line_count / 3))
    log_success "TLE 驗證通過: $satellite_count 顆衛星, epoch 年份: 20$epoch_year"
    
    return 0
}

# 驗證 JSON 數據
validate_json_data() {
    local json_file="$1"
    local expected_date="$2"
    local constellation="$3"
    
    log_info "驗證 JSON 數據: $constellation"
    
    # 檢查 JSON 格式
    if ! python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
        log_error "JSON 格式驗證失敗"
        return 1
    fi
    
    # 檢查數組長度
    local array_length=$(python3 -c "
import json
with open('$json_file', 'r') as f:
    data = json.load(f)
    print(len(data) if isinstance(data, list) else 0)
" 2>/dev/null)
    
    if [[ $array_length -eq 0 ]]; then
        log_error "JSON 數據為空"
        return 1
    fi
    
    # 檢查第一個元素的 EPOCH
    local first_epoch=$(python3 -c "
import json
with open('$json_file', 'r') as f:
    data = json.load(f)
    if isinstance(data, list) and len(data) > 0:
        print(data[0].get('EPOCH', 'N/A'))
    else:
        print('N/A')
" 2>/dev/null)
    
    log_success "JSON 驗證通過: $array_length 顆衛星, first epoch: $first_epoch"
    
    return 0
}

# 主下載函數
download_constellation_data() {
    local constellation="$1"
    local date_str="$2"
    
    local tle_url="https://celestrak.org/NORAD/elements/gp.php?GROUP=$constellation&FORMAT=tle"
    local json_url="https://celestrak.org/NORAD/elements/gp.php?GROUP=$constellation&FORMAT=json"
    
    local tle_file="$TLE_DATA_DIR/$constellation/tle/${constellation}_${date_str}.tle"
    local json_file="$TLE_DATA_DIR/$constellation/json/${constellation}_${date_str}.json"
    
    local success_count=0
    local total_count=2
    
    log_info "=========================================="
    log_info "開始下載 $constellation 數據 (日期: $date_str)"
    log_info "=========================================="
    
    # 檢查 TLE 檔案
    if file_exists "$tle_file"; then
        log_warn "TLE 檔案已存在: $tle_file"
        ((success_count++))
    else
        if download_file "$tle_url" "$tle_file" "$constellation TLE"; then
            if validate_tle_data "$tle_file" "$date_str" "$constellation"; then
                ((success_count++))
            else
                log_error "TLE 驗證失敗，刪除檔案"
                rm -f "$tle_file"
            fi
        fi
    fi
    
    # 檢查 JSON 檔案
    if file_exists "$json_file"; then
        log_warn "JSON 檔案已存在: $json_file"
        ((success_count++))
    else
        if download_file "$json_url" "$json_file" "$constellation JSON"; then
            if validate_json_data "$json_file" "$date_str" "$constellation"; then
                ((success_count++))
            else
                log_error "JSON 驗證失敗，刪除檔案"
                rm -f "$json_file"
            fi
        fi
    fi
    
    log_info "$constellation 下載完成: $success_count/$total_count 檔案成功"
    return $((total_count - success_count))
}

# 生成下載報告
generate_report() {
    local date_str="$1"
    local starlink_result="$2"
    local oneweb_result="$3"
    
    echo
    echo "=========================================="
    echo "📊 每日 TLE 數據下載報告"
    echo "=========================================="
    echo "📅 下載日期: $date_str (UTC)"
    echo "🕐 執行時間: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "📍 數據目錄: $TLE_DATA_DIR"
    echo
    
    # Starlink 狀態
    if [[ $starlink_result -eq 0 ]]; then
        echo -e "${GREEN}✅ Starlink: 全部成功${NC}"
    else
        echo -e "${RED}❌ Starlink: $starlink_result 個檔案失敗${NC}"
    fi
    
    # OneWeb 狀態  
    if [[ $oneweb_result -eq 0 ]]; then
        echo -e "${GREEN}✅ OneWeb: 全部成功${NC}"
    else
        echo -e "${RED}❌ OneWeb: $oneweb_result 個檔案失敗${NC}"
    fi
    
    echo
    echo "📁 檔案結構:"
    if [[ -d "$TLE_DATA_DIR" ]]; then
        find "$TLE_DATA_DIR" -name "*${date_str}*" -type f | sort | while read -r file; do
            local size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            local relative_path=${file#$TLE_DATA_DIR/}
            printf "  %-50s %8s bytes\n" "$relative_path" "$size"
        done
    fi
    
    echo
    echo "📈 收集進度統計:"
    for constellation in starlink oneweb; do
        for format in tle json; do
            local count=$(find "$TLE_DATA_DIR/$constellation/$format" -name "*.${format}" -type f 2>/dev/null | wc -l)
            printf "  %-15s: %3d 個檔案\n" "$constellation $format" "$count"
        done
    done
    
    echo "=========================================="
}

# 主程序
main() {
    local date_str
    date_str=$(get_current_date)
    
    echo
    echo "🚀 LEO 衛星 TLE 數據每日下載工具"
    echo "📅 目標日期: $date_str (UTC)"
    echo "🕐 當前時間: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "📂 數據目錄: $TLE_DATA_DIR"
    echo "📝 日誌檔案: $LOG_FILE"
    echo
    
    log_info "=========================================="
    log_info "開始每日 TLE 數據下載任務"
    log_info "目標日期: $date_str"
    log_info "=========================================="
    
    # 檢查網路連接
    if ! curl -s --connect-timeout 10 "https://celestrak.org" > /dev/null; then
        log_error "無法連接到 CelesTrak，請檢查網路連接"
        exit 1
    fi
    
    # 確保目錄存在
    mkdir -p "$TLE_DATA_DIR"/{starlink,oneweb}/{tle,json}
    
    # 下載 Starlink 數據
    download_constellation_data "starlink" "$date_str"
    local starlink_result=$?
    
    # 下載 OneWeb 數據
    download_constellation_data "oneweb" "$date_str"  
    local oneweb_result=$?
    
    # 生成報告
    generate_report "$date_str" "$starlink_result" "$oneweb_result"
    
    # 總結
    local total_failures=$((starlink_result + oneweb_result))
    if [[ $total_failures -eq 0 ]]; then
        log_success "=========================================="
        log_success "所有數據下載成功完成！"
        log_success "=========================================="
        exit 0
    else
        log_error "=========================================="
        log_error "部分數據下載失敗，共 $total_failures 個檔案"
        log_error "請檢查日誌並重新執行"
        log_error "=========================================="
        exit 1
    fi
}

# 執行主程序
main "$@"