#!/bin/bash
# =============================================================================
# 智能數據清理器 - 防止衛星數據無限增長
# 功能：
# 1. 智能清理過期的 TLE 數據檔案
# 2. 清理舊的預計算數據
# 3. 管理備份檔案存儲空間
# 4. 差異化清理策略（依星座特性）
# =============================================================================

set -euo pipefail

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"  # satellite-processing-system根目錄
TLE_DATA_DIR="$PROJECT_ROOT/data/tle_data"
NETSTACK_DATA_DIR="$PROJECT_ROOT/data/outputs"  # 更新到新的輸出目錄
LOG_DIR="$PROJECT_ROOT/data/logs/tle_scheduler"
LOG_FILE="$LOG_DIR/data_cleanup.log"

# 清理策略配置
DEFAULT_TLE_RETENTION_DAYS=30        # TLE 檔案保留 30 天
DEFAULT_BACKUP_RETENTION_DAYS=7      # 備份檔案保留 7 天
DEFAULT_LOG_RETENTION_DAYS=14        # 日誌檔案保留 14 天
MAX_STORAGE_SIZE_GB=5                # 最大存儲空間 5GB

# 星座特定配置
declare -A CONSTELLATION_CONFIG=(
    ["starlink_retention_days"]=30      # Starlink 更新頻繁，保留 30 天
    ["oneweb_retention_days"]=45        # OneWeb 更新較少，保留 45 天
    ["starlink_max_files"]=50           # Starlink 最多保留 50 個檔案
    ["oneweb_max_files"]=30             # OneWeb 最多保留 30 個檔案
)

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日誌函數
log_info() { 
    local msg="${BLUE}[CLEANUP]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CLEANUP] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_success() { 
    local msg="${GREEN}[SUCCESS]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_warn() { 
    local msg="${YELLOW}[WARN]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_error() { 
    local msg="${RED}[ERROR]${NC} $@"
    echo -e "$msg" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $@" >> "$LOG_FILE" 2>/dev/null || true
}

# 獲取目錄大小（GB）
get_directory_size_gb() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        du -s "$dir" 2>/dev/null | awk '{printf "%.2f", $1/1024/1024}'
    else
        echo "0.00"
    fi
}

# 獲取檔案數量
count_files() {
    local pattern="$1"
    find $pattern -type f 2>/dev/null | wc -l
}

# 清理過期 TLE 檔案
cleanup_tle_files() {
    local constellation="$1"
    local retention_days="${CONSTELLATION_CONFIG[${constellation}_retention_days]}"
    local max_files="${CONSTELLATION_CONFIG[${constellation}_max_files]}"
    
    log_info "清理 $constellation TLE 檔案（保留 $retention_days 天，最多 $max_files 個檔案）"
    
    local tle_dir="$TLE_DATA_DIR/$constellation/tle"
    local json_dir="$TLE_DATA_DIR/$constellation/json"
    
    if [[ ! -d "$tle_dir" ]]; then
        log_warn "$constellation TLE 目錄不存在: $tle_dir"
        return 0
    fi
    
    local cleaned_count=0
    
    # 1. 基於時間的清理
    local expired_files
    expired_files=$(find "$tle_dir" -name "*.tle" -type f -mtime +$retention_days 2>/dev/null || true)
    
    if [[ -n "$expired_files" ]]; then
        while IFS= read -r file; do
            if [[ -f "$file" ]]; then
                local filename=$(basename "$file")
                log_info "刪除過期 TLE 檔案: $filename"
                rm -f "$file"
                
                # 同時刪除對應的 JSON 檔案
                local json_file="$json_dir/${filename%.tle}.json"
                if [[ -f "$json_file" ]]; then
                    rm -f "$json_file"
                    log_info "刪除對應 JSON 檔案: $(basename "$json_file")"
                fi
                
                cleaned_count=$((cleaned_count + 1))
            fi
        done <<< "$expired_files"
    fi
    
    # 2. 基於數量的清理
    local current_count
    current_count=$(count_files "$tle_dir/*.tle")
    
    if [[ $current_count -gt $max_files ]]; then
        local excess_count=$((current_count - max_files))
        log_info "$constellation: 檔案數 ($current_count) 超過限制 ($max_files)，清理最舊的 $excess_count 個檔案"
        
        # 獲取最舊的檔案
        local oldest_files
        oldest_files=$(find "$tle_dir" -name "*.tle" -type f -printf '%T+ %p\n' 2>/dev/null | sort | head -n "$excess_count" | cut -d' ' -f2- || true)
        
        if [[ -n "$oldest_files" ]]; then
            while IFS= read -r file; do
                if [[ -f "$file" ]]; then
                    local filename=$(basename "$file")
                    log_info "刪除最舊檔案: $filename"
                    rm -f "$file"
                    
                    # 同時刪除對應的 JSON 檔案
                    local json_file="$json_dir/${filename%.tle}.json"
                    if [[ -f "$json_file" ]]; then
                        rm -f "$json_file"
                    fi
                    
                    cleaned_count=$((cleaned_count + 1))
                fi
            done <<< "$oldest_files"
        fi
    fi
    
    if [[ $cleaned_count -gt 0 ]]; then
        log_success "$constellation: 清理了 $cleaned_count 個檔案"
    else
        log_info "$constellation: 無需清理檔案"
    fi
}

# 清理備份檔案
cleanup_backup_files() {
    log_info "清理過期備份檔案（保留 $DEFAULT_BACKUP_RETENTION_DAYS 天）"
    
    local backup_dir="$TLE_DATA_DIR/backups"
    if [[ ! -d "$backup_dir" ]]; then
        log_info "備份目錄不存在，跳過備份清理"
        return 0
    fi
    
    local cleaned_count=0
    
    # 清理過期的備份目錄（以日期命名的目錄）
    local expired_backup_dirs
    expired_backup_dirs=$(find "$backup_dir" -maxdepth 1 -type d -name "????????" -mtime +$DEFAULT_BACKUP_RETENTION_DAYS 2>/dev/null || true)
    
    if [[ -n "$expired_backup_dirs" ]]; then
        while IFS= read -r dir; do
            if [[ -d "$dir" ]]; then
                local dir_name=$(basename "$dir")
                local file_count=$(find "$dir" -type f | wc -l)
                log_info "刪除過期備份目錄: $dir_name ($file_count 個檔案)"
                rm -rf "$dir"
                cleaned_count=$((cleaned_count + 1))
            fi
        done <<< "$expired_backup_dirs"
    fi
    
    if [[ $cleaned_count -gt 0 ]]; then
        log_success "清理了 $cleaned_count 個備份目錄"
    else
        log_info "無需清理備份檔案"
    fi
}

# 清理預計算數據
cleanup_precomputed_data() {
    log_info "清理舊的預計算數據"
    
    if [[ ! -d "$NETSTACK_DATA_DIR" ]]; then
        log_info "NetStack 數據目錄不存在，跳過預計算數據清理"
        return 0
    fi
    
    local cleaned_count=0
    
    # 清理舊的時間序列檔案（保留最新的）
    local timeseries_files=("starlink_120min_timeseries.json" "oneweb_120min_timeseries.json")
    
    for file_pattern in "${timeseries_files[@]}"; do
        local base_name="${file_pattern%.*}"
        local extension="${file_pattern##*.}"
        
        # 查找帶日期後綴的舊檔案
        local old_files
        old_files=$(find "$NETSTACK_DATA_DIR" -name "${base_name}_*.$extension" -type f -mtime +7 2>/dev/null || true)
        
        if [[ -n "$old_files" ]]; then
            while IFS= read -r file; do
                if [[ -f "$file" ]]; then
                    log_info "刪除舊預計算檔案: $(basename "$file")"
                    rm -f "$file"
                    cleaned_count=$((cleaned_count + 1))
                fi
            done <<< "$old_files"
        fi
    done
    
    # 清理臨時檔案
    local temp_files
    temp_files=$(find "$NETSTACK_DATA_DIR" -name "*.tmp" -o -name "temp_*" -type f 2>/dev/null || true)
    
    if [[ -n "$temp_files" ]]; then
        while IFS= read -r file; do
            if [[ -f "$file" ]]; then
                log_info "刪除臨時檔案: $(basename "$file")"
                rm -f "$file"
                cleaned_count=$((cleaned_count + 1))
            fi
        done <<< "$temp_files"
    fi
    
    if [[ $cleaned_count -gt 0 ]]; then
        log_success "清理了 $cleaned_count 個預計算數據檔案"
    else
        log_info "無需清理預計算數據"
    fi
}

# 清理日誌檔案
cleanup_log_files() {
    log_info "清理過期日誌檔案（保留 $DEFAULT_LOG_RETENTION_DAYS 天）"
    
    if [[ ! -d "$LOG_DIR" ]]; then
        log_info "日誌目錄不存在，跳過日誌清理"
        return 0
    fi
    
    local cleaned_count=0
    
    # 清理壓縮日誌檔案
    local old_logs
    old_logs=$(find "$LOG_DIR" -name "*.log.gz" -type f -mtime +$DEFAULT_LOG_RETENTION_DAYS 2>/dev/null || true)
    
    if [[ -n "$old_logs" ]]; then
        while IFS= read -r file; do
            if [[ -f "$file" ]]; then
                log_info "刪除過期日誌: $(basename "$file")"
                rm -f "$file"
                cleaned_count=$((cleaned_count + 1))
            fi
        done <<< "$old_logs"
    fi
    
    if [[ $cleaned_count -gt 0 ]]; then
        log_success "清理了 $cleaned_count 個過期日誌檔案"
    else
        log_info "無需清理日誌檔案"
    fi
}

# 檢查存儲空間使用情況
check_storage_usage() {
    log_info "檢查存儲空間使用情況"
    
    local tle_size=$(get_directory_size_gb "$TLE_DATA_DIR")
    local netstack_size=$(get_directory_size_gb "$NETSTACK_DATA_DIR")
    local log_size=$(get_directory_size_gb "$LOG_DIR")
    local total_size=$(echo "$tle_size + $netstack_size + $log_size" | bc -l 2>/dev/null || echo "0.00")
    
    echo
    echo "===== 存儲使用情況 ====="
    echo "TLE 數據:      ${tle_size} GB"
    echo "NetStack 數據: ${netstack_size} GB" 
    echo "日誌檔案:      ${log_size} GB"
    echo "總計:          ${total_size} GB"
    echo "限制:          ${MAX_STORAGE_SIZE_GB}.00 GB"
    
    # 檔案統計
    local starlink_count=$(count_files "$TLE_DATA_DIR/starlink/tle/*.tle")
    local oneweb_count=$(count_files "$TLE_DATA_DIR/oneweb/tle/*.tle")
    
    echo
    echo "===== 檔案統計 ====="
    echo "Starlink TLE: $starlink_count 個檔案"
    echo "OneWeb TLE:   $oneweb_count 個檔案"
    echo "========================"
    echo
    
    # 警告檢查
    if (( $(echo "$total_size > $MAX_STORAGE_SIZE_GB" | bc -l 2>/dev/null || echo "0") )); then
        log_warn "存儲使用量 (${total_size} GB) 超過限制 (${MAX_STORAGE_SIZE_GB} GB)"
        return 1
    else
        log_success "存儲使用量在合理範圍內"
        return 0
    fi
}

# 緊急清理（存儲空間不足時）
emergency_cleanup() {
    log_warn "執行緊急清理（存儲空間不足）"
    
    # 更激進的清理策略
    local emergency_retention_days=14
    
    # 緊急清理 TLE 檔案
    for constellation in starlink oneweb; do
        local tle_dir="$TLE_DATA_DIR/$constellation/tle"
        if [[ -d "$tle_dir" ]]; then
            local emergency_files
            emergency_files=$(find "$tle_dir" -name "*.tle" -type f -mtime +$emergency_retention_days 2>/dev/null || true)
            
            if [[ -n "$emergency_files" ]]; then
                local count=0
                while IFS= read -r file; do
                    if [[ -f "$file" ]]; then
                        rm -f "$file"
                        count=$((count + 1))
                    fi
                done <<< "$emergency_files"
                log_warn "$constellation: 緊急清理了 $count 個檔案"
            fi
        fi
    done
    
    # 清理所有備份
    if [[ -d "$TLE_DATA_DIR/backups" ]]; then
        rm -rf "$TLE_DATA_DIR/backups"/*
        log_warn "緊急清理: 刪除所有備份檔案"
    fi
    
    # 清理預計算數據的舊版本
    cleanup_precomputed_data
}

# 顯示使用說明
show_help() {
    echo "智能數據清理工具"
    echo
    echo "用法: $0 [選項]"
    echo
    echo "選項:"
    echo "  --dry-run          模擬運行，不實際刪除檔案"
    echo "  --emergency        執行緊急清理（更激進的清理策略）"
    echo "  --check-only       僅檢查存儲使用情況，不執行清理"
    echo "  --help             顯示此幫助信息"
    echo
    echo "清理策略:"
    echo "  Starlink TLE:      保留 ${CONSTELLATION_CONFIG[starlink_retention_days]} 天，最多 ${CONSTELLATION_CONFIG[starlink_max_files]} 個檔案"
    echo "  OneWeb TLE:        保留 ${CONSTELLATION_CONFIG[oneweb_retention_days]} 天，最多 ${CONSTELLATION_CONFIG[oneweb_max_files]} 個檔案"
    echo "  備份檔案:          保留 $DEFAULT_BACKUP_RETENTION_DAYS 天"
    echo "  日誌檔案:          保留 $DEFAULT_LOG_RETENTION_DAYS 天"
    echo "  存儲限制:          ${MAX_STORAGE_SIZE_GB} GB"
    echo
}

# 主程序
main() {
    local dry_run=false
    local emergency_mode=false
    local check_only=false
    
    # 解析命令行參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                shift
                ;;
            --emergency)
                emergency_mode=true
                shift
                ;;
            --check-only)
                check_only=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "未知選項: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 創建日誌目錄
    mkdir -p "$LOG_DIR"
    
    local start_time=$(date +%s)
    log_info "========== 智能數據清理開始 =========="
    log_info "執行時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    
    if $dry_run; then
        log_info "模擬運行模式 - 不會實際刪除檔案"
    fi
    
    # 檢查存儲使用情況
    if ! check_storage_usage; then
        if $emergency_mode; then
            emergency_cleanup
        elif ! $check_only; then
            log_warn "存儲空間使用量偏高，建議執行緊急清理: $0 --emergency"
        fi
    fi
    
    if $check_only; then
        log_info "僅檢查模式 - 跳過實際清理"
        exit 0
    fi
    
    if ! $dry_run; then
        # 執行各類清理
        cleanup_tle_files "starlink"
        cleanup_tle_files "oneweb"
        cleanup_backup_files
        cleanup_precomputed_data
        cleanup_log_files
        
        # 重新檢查存儲使用情況
        log_info "清理後重新檢查存儲使用情況:"
        check_storage_usage
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "智能數據清理完成 ($duration 秒)"
    log_info "========== 智能數據清理結束 =========="
}

# 執行主程序
main "$@"