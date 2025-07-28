#!/bin/bash
# =============================================================================
# 增強版每日 TLE 數據自動下載腳本 - 支援智能更新檢查
# 新功能：
# 1. 檔案存在時仍檢查是否有更新版本
# 2. 比較檔案修改時間和大小
# 3. 強制更新模式
# 4. 備份舊檔案
# =============================================================================

set -euo pipefail

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TLE_DATA_DIR="$PROJECT_ROOT/tle_data"
LOG_FILE="$PROJECT_ROOT/logs/tle_download.log"
BACKUP_DIR="$TLE_DATA_DIR/backups/$(date -u '+%Y%m%d')"

# 創建必要目錄
mkdir -p "$(dirname "$LOG_FILE")" "$BACKUP_DIR"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 命令行參數
FORCE_UPDATE=false
CHECK_UPDATES=true
BACKUP_EXISTING=true

# 解析命令行參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_UPDATE=true
            shift
            ;;
        --no-update-check)
            CHECK_UPDATES=false
            shift
            ;;
        --no-backup)
            BACKUP_EXISTING=false
            shift
            ;;
        --help)
            echo "用法: $0 [選項]"
            echo "選項:"
            echo "  --force           強制重新下載所有檔案"
            echo "  --no-update-check 不檢查更新，直接跳過已存在檔案"
            echo "  --no-backup       不備份現有檔案"
            echo "  --help           顯示此幫助訊息"
            exit 0
            ;;
        *)
            echo "未知選項: $1"
            exit 1
            ;;
    esac
done

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
log_update() { echo -e "${CYAN}[UPDATE]${NC} $@" | tee -a "$LOG_FILE"; }

# 獲取當前 UTC 日期
get_current_date() {
    date -u '+%Y%m%d'
}

# 檢查檔案是否存在且有效
file_exists_and_valid() {
    local filepath="$1"
    if [[ -f "$filepath" && -s "$filepath" ]]; then
        return 0
    else
        return 1
    fi
}

# 備份現有檔案到統一備份目錄
backup_file() {
    local source_file="$1"
    local description="$2"

    if [[ ! -f "$source_file" ]]; then
        return 0
    fi

    local filename=$(basename "$source_file")
    local backup_path="$BACKUP_DIR/$filename"

    if $BACKUP_EXISTING; then
        cp "$source_file" "$backup_path"
        log_info "備份 $description: $backup_path"
    fi
}

# 清理舊的散落備份檔案
cleanup_scattered_backups() {
    local constellation="$1"

    # 清理 TLE 目錄中的 .backup_* 檔案
    find "$TLE_DATA_DIR/$constellation/tle" -name "*.backup_*" -type f -delete 2>/dev/null || true

    # 清理 JSON 目錄中的 .backup_* 檔案
    find "$TLE_DATA_DIR/$constellation/json" -name "*.backup_*" -type f -delete 2>/dev/null || true

    log_info "已清理 $constellation 的散落備份檔案"
}

# 清理過期備份檔案
cleanup_old_backups() {
    local days_to_keep=7  # 保留7天的備份

    if [[ -d "$TLE_DATA_DIR/backups" ]]; then
        # 刪除超過指定天數的備份目錄
        find "$TLE_DATA_DIR/backups" -maxdepth 1 -type d -name "????????" -mtime +$days_to_keep -exec rm -rf {} \; 2>/dev/null || true

        local deleted_count=$(find "$TLE_DATA_DIR/backups" -maxdepth 1 -type d -name "????????" -mtime +$days_to_keep 2>/dev/null | wc -l)
        if [[ $deleted_count -gt 0 ]]; then
            log_info "已清理 $deleted_count 個過期備份目錄（保留 $days_to_keep 天）"
        fi
    fi
}

# 檢查是否需要更新檔案
need_update() {
    local local_file="$1"
    local url="$2"
    local description="$3"
    
    if $FORCE_UPDATE; then
        log_update "強制更新模式：將重新下載 $description"
        return 0
    fi
    
    if ! file_exists_and_valid "$local_file"; then
        log_update "檔案不存在或無效：$description"
        return 0
    fi
    
    if ! $CHECK_UPDATES; then
        log_info "跳過更新檢查：$description"
        return 1
    fi
    
    # 檢查遠端檔案的 Last-Modified 和 Content-Length
    log_info "檢查 $description 是否有更新..."
    
    local temp_header_file=$(mktemp)
    if curl -s -I --connect-timeout 30 --max-time 60 "$url" > "$temp_header_file"; then
        
        # 獲取遠端檔案信息
        local remote_last_modified=$(grep -i "Last-Modified:" "$temp_header_file" | cut -d' ' -f2- | tr -d '\r')
        local remote_content_length=$(grep -i "Content-Length:" "$temp_header_file" | cut -d' ' -f2 | tr -d '\r')
        
        # 獲取本地檔案信息
        local local_size=$(stat -c%s "$local_file" 2>/dev/null || echo "0")
        local local_mtime=$(stat -c%Y "$local_file" 2>/dev/null || echo "0")
        
        rm -f "$temp_header_file"
        
        # 檢查大小是否不同
        if [[ -n "$remote_content_length" && "$remote_content_length" != "$local_size" ]]; then
            log_update "$description 檔案大小不同 (本地: $local_size, 遠端: $remote_content_length)"
            return 0
        fi
        
        # 檢查修改時間 (如果可用)
        if [[ -n "$remote_last_modified" ]]; then
            local remote_timestamp
            # 嘗試解析時間戳 (這可能因服務器而異)
            if command -v gdate >/dev/null 2>&1; then  # macOS
                remote_timestamp=$(gdate -d "$remote_last_modified" +%s 2>/dev/null || echo "0")
            else  # Linux
                remote_timestamp=$(date -d "$remote_last_modified" +%s 2>/dev/null || echo "0")
            fi
            
            if [[ "$remote_timestamp" -gt "$local_mtime" && "$remote_timestamp" != "0" ]]; then
                log_update "$description 遠端檔案較新 (遠端: $remote_last_modified)"
                return 0
            fi
        fi
        
        log_info "$description 本地檔案是最新的"
        return 1
    else
        log_warn "無法檢查 $description 的更新狀態，將重新下載"
        rm -f "$temp_header_file"
        return 0
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
    
    # 備份現有檔案
    backup_file "$output_path" "$description"
    
    # 使用臨時檔案下載
    local temp_file="${output_path}.tmp"
    
    if curl -L --fail --connect-timeout 30 --max-time 300 --retry 3 \
            -o "$temp_file" "$url"; then
        
        # 檢查檔案大小
        local file_size=$(stat -c%s "$temp_file")
        if [[ $file_size -lt 100 ]]; then
            log_error "$description 下載檔案過小 ($file_size bytes)，可能下載失敗"
            rm -f "$temp_file"
            return 1
        fi
        
        # 原子性移動檔案
        mv "$temp_file" "$output_path"
        
        # 設置檔案時間戳為當前時間
        touch "$output_path"
        
        log_success "$description 下載成功 ($file_size bytes)"
        return 0
    else
        log_error "$description 下載失敗"
        rm -f "$temp_file"
        return 1
    fi
}

# 從 TLE 數據提取實際日期
extract_tle_date() {
    local tle_file="$1"

    # 檢查檔案是否存在
    if [[ ! -f "$tle_file" ]]; then
        echo ""
        return 1
    fi

    # 提取第一顆衛星的 epoch
    local first_line1=$(sed -n '2p' "$tle_file" 2>/dev/null)
    if [[ -z "$first_line1" ]]; then
        echo ""
        return 1
    fi

    # 提取年份和天數
    local epoch_year=$(echo "$first_line1" | cut -c19-20)
    local epoch_day_decimal=$(echo "$first_line1" | cut -c21-32)
    local epoch_day=$(echo "$epoch_day_decimal" | cut -d'.' -f1)

    # 轉換為完整年份
    local full_year
    if [[ $epoch_year -lt 57 ]]; then  # 假設 57 以下是 20xx 年
        full_year="20$epoch_year"
    else
        full_year="19$epoch_year"
    fi

    # 轉換天數為日期
    local epoch_date
    if command -v python3 >/dev/null 2>&1; then
        epoch_date=$(python3 -c "
from datetime import datetime, timedelta
import sys
try:
    year = int('$full_year')
    day = int('$epoch_day')
    date = datetime(year, 1, 1) + timedelta(days=day-1)
    print(date.strftime('%Y%m%d'))
except:
    sys.exit(1)
" 2>/dev/null)
    else
        # 備用方法：使用 date 命令
        epoch_date=$(date -d "$full_year-01-01 +$((epoch_day-1)) days" '+%Y%m%d' 2>/dev/null)
    fi

    echo "$epoch_date"
    return 0
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

    # 提取 epoch date 進行詳細分析
    local epoch_year=$(echo "$first_line1" | cut -c19-20)
    local epoch_day=$(echo "$first_line1" | cut -c21-32)

    # 計算當前年份的後兩位
    local current_year_short=$(date -u '+%y')
    local prev_year_short=$(printf "%02d" $(( ($(date -u '+%y') - 1 + 100) % 100 )))

    # 檢查年份是否合理
    if [[ "$epoch_year" != "$current_year_short" && "$epoch_year" != "$prev_year_short" ]]; then
        log_warn "TLE epoch 年份 ($epoch_year) 可能不是最新數據"
    fi

    # 計算衛星數量和基本統計
    local satellite_count=$((line_count / 3))

    # 提取更詳細的 epoch 信息用於新鮮度檢查
    local epoch_day_decimal=$(echo "$first_line1" | cut -c21-32)
    local current_day=$(date -u '+%j')
    local current_decimal=$(echo "$current_day" | sed 's/^0*//')

    # 簡單的新鮮度檢查 (允許幾天的差異)
    local day_diff_raw=$(echo "$epoch_day_decimal - $current_decimal" | bc -l 2>/dev/null || echo "0")
    local day_diff=$(echo "$day_diff_raw" | cut -d'.' -f1 2>/dev/null || echo "0")

    # 確保 day_diff 是有效數字
    if [[ ! "$day_diff" =~ ^-?[0-9]+$ ]]; then
        day_diff=0
    fi

    local abs_day_diff=${day_diff#-}  # 取絕對值
    if [[ -n "$abs_day_diff" && "$abs_day_diff" -gt 5 ]]; then  # 絕對值大於5天
        log_warn "TLE 數據可能不夠新鮮 (epoch day: $epoch_day_decimal, current: $current_decimal, diff: $day_diff)"
    fi

    # 提取實際數據日期
    local actual_date=$(extract_tle_date "$tle_file")
    if [[ -n "$actual_date" ]]; then
        log_info "TLE 數據實際日期: $actual_date"
        # 將實際日期存儲到全局變量中，供後續使用
        export TLE_ACTUAL_DATE="$actual_date"
    fi

    log_success "TLE 驗證通過: $satellite_count 顆衛星, epoch: 20$epoch_year $epoch_day_decimal"

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
    
    # 檢查第一個元素的 EPOCH 和新鮮度
    local epoch_info=$(python3 -c "
import json
from datetime import datetime
with open('$json_file', 'r') as f:
    data = json.load(f)
    if isinstance(data, list) and len(data) > 0:
        epoch = data[0].get('EPOCH', 'N/A')
        print(f'{epoch}')
    else:
        print('N/A')
" 2>/dev/null)
    
    log_success "JSON 驗證通過: $array_length 顆衛星, first epoch: $epoch_info"
    
    return 0
}

# 檢查是否需要更新已存在的檔案
need_update_existing() {
    local existing_file="$1"
    local url="$2"
    local description="$3"

    if $FORCE_UPDATE; then
        log_update "強制更新模式：將重新下載 $description"
        return 0
    fi

    if ! file_exists_and_valid "$existing_file"; then
        return 0  # 檔案不存在或無效，需要下載
    fi

    if ! $CHECK_UPDATES; then
        log_info "跳過更新檢查：$description"
        return 1  # 不檢查更新
    fi

    # 使用原有的更新檢查邏輯
    need_update "$existing_file" "$url" "$description"
    return $?
}

# 主下載函數
download_constellation_data() {
    local constellation="$1"
    local date_str="$2"

    local tle_url="https://celestrak.org/NORAD/elements/gp.php?GROUP=$constellation&FORMAT=tle"
    local json_url="https://celestrak.org/NORAD/elements/gp.php?GROUP=$constellation&FORMAT=json"

    # 使用臨時檔案名
    local temp_tle_file="$TLE_DATA_DIR/$constellation/tle/temp_${constellation}.tle"
    local temp_json_file="$TLE_DATA_DIR/$constellation/json/temp_${constellation}.json"

    local success_count=0
    local total_count=2
    local updated_count=0

    log_info "=========================================="
    log_info "處理 $constellation 數據 (下載日期: $date_str)"
    log_info "=========================================="
    
    # 處理 TLE 檔案
    log_info "開始處理 $constellation TLE 數據..."

    # 先下載到臨時檔案
    if download_file "$tle_url" "$temp_tle_file" "$constellation TLE"; then
        if validate_tle_data "$temp_tle_file" "$date_str" "$constellation"; then
            # 提取實際數據日期
            local actual_date="$TLE_ACTUAL_DATE"
            if [[ -z "$actual_date" ]]; then
                actual_date="$date_str"  # 如果無法提取，使用下載日期
                log_warn "無法提取實際數據日期，使用下載日期: $actual_date"
            fi

            local final_tle_file="$TLE_DATA_DIR/$constellation/tle/${constellation}_${actual_date}.tle"
            log_info "數據實際日期: $actual_date"

            # 檢查是否需要更新現有檔案
            local should_update=true
            if [[ -f "$final_tle_file" ]]; then
                log_info "發現現有檔案: $(basename "$final_tle_file")"
                if need_update_existing "$final_tle_file" "$tle_url" "$constellation TLE (實際日期: $actual_date)"; then
                    log_info "現有檔案需要更新"
                    backup_file "$final_tle_file" "$constellation TLE"
                else
                    log_info "現有檔案無需更新，跳過"
                    should_update=false
                fi
            fi

            if $should_update; then
                # 移動臨時檔案到最終位置
                mv "$temp_tle_file" "$final_tle_file"
                log_success "$constellation TLE 更新成功: $(basename "$final_tle_file")"
                updated_count=$((updated_count + 1))
            else
                # 清理臨時檔案
                rm -f "$temp_tle_file"
            fi

            success_count=$((success_count + 1))
        else
            log_error "TLE 驗證失敗，刪除臨時檔案"
            rm -f "$temp_tle_file"
        fi
    fi
    
    # 處理 JSON 檔案
    log_info "開始處理 $constellation JSON 數據..."

    # 使用與 TLE 相同的實際日期
    local actual_date="$TLE_ACTUAL_DATE"
    if [[ -z "$actual_date" ]]; then
        actual_date="$date_str"  # 如果無法提取，使用下載日期
    fi

    local final_json_file="$TLE_DATA_DIR/$constellation/json/${constellation}_${actual_date}.json"

    # 檢查是否需要更新現有檔案
    local should_download=true
    if [[ -f "$final_json_file" ]]; then
        log_info "發現現有 JSON 檔案: $(basename "$final_json_file")"
        if need_update_existing "$final_json_file" "$json_url" "$constellation JSON (實際日期: $actual_date)"; then
            log_info "現有 JSON 檔案需要更新"
            backup_file "$final_json_file" "$constellation JSON"
        else
            log_info "現有 JSON 檔案無需更新，跳過"
            should_download=false
        fi
    fi

    if $should_download; then
        # 下載到臨時檔案
        if download_file "$json_url" "$temp_json_file" "$constellation JSON"; then
            if validate_json_data "$temp_json_file" "$date_str" "$constellation"; then
                # 移動臨時檔案到最終位置
                mv "$temp_json_file" "$final_json_file"
                log_success "$constellation JSON 更新成功: $(basename "$final_json_file")"
                updated_count=$((updated_count + 1))
                success_count=$((success_count + 1))
            else
                log_error "JSON 驗證失敗，刪除臨時檔案"
                rm -f "$temp_json_file"
            fi
        fi
    else
        success_count=$((success_count + 1))
    fi
    
    log_info "$constellation 處理完成: $success_count/$total_count 檔案就緒, $updated_count 個更新"
    return $((total_count - success_count))
}

# 生成增強版報告
generate_enhanced_report() {
    local date_str="$1"
    local starlink_result="$2"
    local oneweb_result="$3"
    
    echo
    echo "=========================================="
    echo "📊 增強版每日 TLE 數據下載報告"
    echo "=========================================="
    echo "📅 下載日期: $date_str (UTC)"
    echo "🕐 執行時間: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "📍 數據目錄: $TLE_DATA_DIR"
    echo "💾 備份目錄: $BACKUP_DIR"
    echo
    
    # 模式說明
    if $FORCE_UPDATE; then
        echo -e "${YELLOW}⚡ 模式: 強制更新模式${NC}"
    elif $CHECK_UPDATES; then
        echo -e "${CYAN}🔄 模式: 智能更新檢查模式${NC}"
    else
        echo -e "${BLUE}⏭️ 模式: 跳過已存在檔案模式${NC}"
    fi
    echo
    
    # 狀態顯示
    if [[ $starlink_result -eq 0 ]]; then
        echo -e "${GREEN}✅ Starlink: 全部成功${NC}"
    else
        echo -e "${RED}❌ Starlink: $starlink_result 個檔案失敗${NC}"
    fi
    
    if [[ $oneweb_result -eq 0 ]]; then
        echo -e "${GREEN}✅ OneWeb: 全部成功${NC}"
    else
        echo -e "${RED}❌ OneWeb: $oneweb_result 個檔案失敗${NC}"
    fi
    
    echo
    echo "📁 本次下載的檔案:"
    if [[ -d "$TLE_DATA_DIR" ]]; then
        # 顯示今天修改的所有檔案（不限於檔案名中的日期）
        find "$TLE_DATA_DIR" -type f -newermt "$(date '+%Y-%m-%d')" ! -path "*/backups/*" | sort | while read -r file; do
            local size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            local mtime=$(stat -c%Y "$file" 2>/dev/null || echo "0")
            local formatted_time=$(date -d "@$mtime" '+%H:%M:%S' 2>/dev/null || echo "unknown")
            local relative_path=${file#$TLE_DATA_DIR/}
            printf "  %-50s %8s bytes (更新: %s)\n" "$relative_path" "$size" "$formatted_time"
        done

        # 如果沒有找到今天的檔案，則顯示最近的檔案
        local today_files=$(find "$TLE_DATA_DIR" -type f -newermt "$(date '+%Y-%m-%d')" ! -path "*/backups/*" | wc -l)
        if [[ $today_files -eq 0 ]]; then
            echo "  (沒有找到今天修改的檔案，顯示最近的檔案:)"
            find "$TLE_DATA_DIR" -type f ! -path "*/backups/*" -exec stat -c '%Y %n' {} \; | sort -nr | head -10 | while read -r timestamp file; do
                local size=$(stat -c%s "$file" 2>/dev/null || echo "0")
                local formatted_time=$(date -d "@$timestamp" '+%H:%M:%S' 2>/dev/null || echo "unknown")
                local relative_path=${file#$TLE_DATA_DIR/}
                printf "  %-50s %8s bytes (更新: %s)\n" "$relative_path" "$size" "$formatted_time"
            done
        fi
    fi
    
    echo
    echo "💾 備份檔案:"
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -type f | sort | while read -r file; do
            local size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            local filename=$(basename "$file")
            printf "  %-30s %8s bytes\n" "$filename" "$size"
        done
    else
        echo "  (無備份檔案)"
    fi
    
    echo "=========================================="
}

# 主程序
main() {
    local date_str
    date_str=$(get_current_date)
    
    echo
    echo "🚀 增強版 LEO 衛星 TLE 數據下載工具"
    echo "📅 目標日期: $date_str (UTC)"
    echo "🕐 當前時間: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "📂 數據目錄: $TLE_DATA_DIR"
    echo "📝 日誌檔案: $LOG_FILE"
    
    if $FORCE_UPDATE; then
        echo -e "${YELLOW}⚡ 強制更新模式已啟用${NC}"
    fi
    
    if ! $CHECK_UPDATES; then
        echo -e "${BLUE}⏭️ 跳過已存在檔案模式已啟用${NC}"
    fi
    
    echo
    
    log_info "=========================================="
    log_info "開始增強版每日 TLE 數據下載任務"
    log_info "目標日期: $date_str"
    log_info "強制更新: $FORCE_UPDATE"
    log_info "檢查更新: $CHECK_UPDATES"
    log_info "備份檔案: $BACKUP_EXISTING"
    log_info "=========================================="
    
    # 檢查網路連接
    if ! curl -s --connect-timeout 10 "https://celestrak.org" > /dev/null; then
        log_error "無法連接到 CelesTrak，請檢查網路連接"
        exit 1
    fi
    
    # 確保目錄存在
    mkdir -p "$TLE_DATA_DIR"/{starlink,oneweb}/{tle,json}
    
    # 下載數據
    download_constellation_data "starlink" "$date_str"
    local starlink_result=$?
    
    download_constellation_data "oneweb" "$date_str"
    local oneweb_result=$?
    
    # 清理散落的備份檔案和過期備份
    log_info "執行備份清理..."
    cleanup_scattered_backups "starlink"
    cleanup_scattered_backups "oneweb"
    cleanup_old_backups

    # 生成報告
    generate_enhanced_report "$date_str" "$starlink_result" "$oneweb_result"

    # 總結
    local total_failures=$((starlink_result + oneweb_result))
    if [[ $total_failures -eq 0 ]]; then
        log_success "=========================================="
        log_success "所有數據處理成功完成！"
        log_success "=========================================="
        exit 0
    else
        log_error "=========================================="
        log_error "部分數據處理失敗，共 $total_failures 個檔案"
        log_error "請檢查日誌並重新執行"
        log_error "=========================================="
        exit 1
    fi
}

# 執行主程序
main "$@"