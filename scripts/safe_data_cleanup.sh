#!/bin/bash
# =============================================================================
# 安全數據清理器 - 只清理可重新生成的數據，保護原始 TLE 數據
# 清理策略：
# 1. 【保留】原始 TLE 數據 (.tle 檔案) - 避免重新下載失敗
# 2. 【清理】預計算數據 (時間序列 JSON 檔案) - 可重新計算
# 3. 【清理】容器內預計算數據 (Docker Volume) - 可重新計算  
# 4. 【清理】日誌和備份檔案 - 定期清理
# =============================================================================

set -euo pipefail

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TLE_DATA_DIR="$PROJECT_ROOT/netstack/tle_data"
NETSTACK_DATA_DIR="$PROJECT_ROOT/netstack/data"
LOG_DIR="$PROJECT_ROOT/logs/tle_scheduler"
LOG_FILE="$LOG_DIR/safe_cleanup.log"

# 清理策略配置 - 保守策略
PRECOMPUTED_RETENTION_DAYS=14    # 預計算數據保留 14 天
BACKUP_RETENTION_DAYS=7          # 備份檔案保留 7 天  
LOG_RETENTION_DAYS=30            # 日誌檔案保留 30 天
MAX_STORAGE_SIZE_GB=10           # 最大存儲空間 10GB

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日誌函數
log_info() { 
    local msg="${BLUE}[SAFE_CLEANUP]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SAFE_CLEANUP] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_success() { 
    local msg="${GREEN}[SUCCESS]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_warn() { 
    local msg="${YELLOW}[WARNING]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_error() { 
    local msg="${RED}[ERROR]${NC} $@"
    echo -e "$msg" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $@" >> "$LOG_FILE" 2>/dev/null || true
}

# 清理預計算數據（可重新生成）
cleanup_precomputed_data() {
    log_info "清理過期的預計算數據（保留原始 TLE 數據）"
    
    if [[ ! -d "$NETSTACK_DATA_DIR" ]]; then
        log_info "NetStack 數據目錄不存在，跳過預計算數據清理"
        return 0
    fi
    
    local cleaned_count=0
    
    # 清理舊的時間序列檔案（保留最新的）
    local timeseries_patterns=(
        "starlink_*_timeseries.json"
        "oneweb_*_timeseries.json"
        "starlink_*_d2_*.json"
        "oneweb_*_d2_*.json"
        "phase0_precomputed_orbits_*.json"
    )
    
    for pattern in "${timeseries_patterns[@]}"; do
        local old_files
        old_files=$(find "$NETSTACK_DATA_DIR" -name "$pattern" -type f -mtime +$PRECOMPUTED_RETENTION_DAYS 2>/dev/null || true)
        
        if [[ -n "$old_files" ]]; then
            while IFS= read -r file; do
                if [[ -f "$file" ]]; then
                    log_info "刪除過期預計算檔案: $(basename "$file")"
                    rm -f "$file"
                    cleaned_count=$((cleaned_count + 1))
                fi
            done <<< "$old_files"
        fi
    done
    
    log_success "預計算數據清理完成，清理了 $cleaned_count 個檔案"
}

# 清理容器內預計算數據（Docker Volume）
cleanup_container_precomputed_data() {
    log_info "清理容器內過期預計算數據"
    
    # 檢查是否有運行中的 netstack-api 容器
    if ! docker ps --format "table {{.Names}}" | grep -q "netstack-api"; then
        log_warn "netstack-api 容器未運行，跳過容器內數據清理"
        return 0
    fi
    
    # 在容器內執行清理
    local cleanup_result
    cleanup_result=$(docker exec netstack-api find /app/data -name "*.json" -type f -mtime +$PRECOMPUTED_RETENTION_DAYS -delete 2>/dev/null | wc -l || echo "0")
    
    if [[ "$cleanup_result" -gt 0 ]]; then
        log_success "容器內清理了 $cleanup_result 個過期預計算檔案"
    else
        log_info "容器內無需清理過期檔案"
    fi
}

# 清理備份檔案
cleanup_backup_files() {
    log_info "清理過期備份檔案（保留 $BACKUP_RETENTION_DAYS 天）"
    
    local backup_dirs=(
        "$PROJECT_ROOT/backup"
        "$PROJECT_ROOT/backups"
        "/tmp/tle_backup"
    )
    
    local cleaned_count=0
    
    for backup_dir in "${backup_dirs[@]}"; do
        if [[ -d "$backup_dir" ]]; then
            local old_backups
            old_backups=$(find "$backup_dir" -type f -mtime +$BACKUP_RETENTION_DAYS 2>/dev/null || true)
            
            if [[ -n "$old_backups" ]]; then
                while IFS= read -r file; do
                    if [[ -f "$file" ]]; then
                        log_info "刪除過期備份: $(basename "$file")"
                        rm -f "$file"
                        cleaned_count=$((cleaned_count + 1))
                    fi
                done <<< "$old_backups"
            fi
        fi
    done
    
    log_success "備份檔案清理完成，清理了 $cleaned_count 個檔案"
}

# 清理日誌檔案
cleanup_log_files() {
    log_info "清理過期日誌檔案（保留 $LOG_RETENTION_DAYS 天）"
    
    local log_dirs=(
        "$LOG_DIR"
        "/tmp"
    )
    
    local cleaned_count=0
    
    for log_dir in "${log_dirs[@]}"; do
        if [[ -d "$log_dir" ]]; then
            # 清理 TLE 相關日誌
            local old_logs
            old_logs=$(find "$log_dir" -name "*tle*.log" -type f -mtime +$LOG_RETENTION_DAYS 2>/dev/null || true)
            old_logs="$old_logs"$'\n'$(find "$log_dir" -name "*cleanup*.log" -type f -mtime +$LOG_RETENTION_DAYS 2>/dev/null || true)
            old_logs="$old_logs"$'\n'$(find "$log_dir" -name "*incremental*.log" -type f -mtime +$LOG_RETENTION_DAYS 2>/dev/null || true)
            
            if [[ -n "$old_logs" && "$old_logs" != $'\n\n' ]]; then
                while IFS= read -r file; do
                    if [[ -f "$file" && -n "$file" ]]; then
                        log_info "刪除過期日誌: $(basename "$file")"
                        rm -f "$file"
                        cleaned_count=$((cleaned_count + 1))
                    fi
                done <<< "$old_logs"
            fi
        fi
    done
    
    log_success "日誌檔案清理完成，清理了 $cleaned_count 個檔案"
}

# 檢查存儲使用情況
check_storage_usage() {
    log_info "檢查存儲使用情況"
    
    local usage_gb
    usage_gb=$(du -sb "$PROJECT_ROOT" 2>/dev/null | awk '{print int($1/1024/1024/1024)}' || echo "0")
    
    log_info "當前專案存儲使用量: ${usage_gb}GB / ${MAX_STORAGE_SIZE_GB}GB"
    
    if [[ $usage_gb -gt $MAX_STORAGE_SIZE_GB ]]; then
        log_warn "存儲使用量超過限制 (${usage_gb}GB > ${MAX_STORAGE_SIZE_GB}GB)"
        return 1
    fi
    
    return 0
}

# 顯示清理統計
show_cleanup_summary() {
    log_info "========== 清理統計摘要 =========="
    
    # TLE 數據統計（保留不清理）
    local tle_count=0
    if [[ -d "$TLE_DATA_DIR" ]]; then
        tle_count=$(find "$TLE_DATA_DIR" -name "*.tle" -type f 2>/dev/null | wc -l || echo "0")
    fi
    log_info "原始 TLE 數據: $tle_count 個檔案 (已保留，不清理)"
    
    # 預計算數據統計
    local precomputed_count=0
    if [[ -d "$NETSTACK_DATA_DIR" ]]; then
        precomputed_count=$(find "$NETSTACK_DATA_DIR" -name "*.json" -type f 2>/dev/null | wc -l || echo "0")
    fi
    log_info "預計算數據: $precomputed_count 個檔案"
    
    # 存儲使用統計
    check_storage_usage
}

# 主函數
main() {
    local dry_run=false
    local check_only=false
    
    # 解析命令行參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                shift
                ;;
            --check-only)
                check_only=true
                shift
                ;;
            --help)
                echo "安全數據清理器 - 只清理可重新生成的數據"
                echo "使用方法: $0 [選項]"
                echo "選項:"
                echo "  --dry-run     模擬運行，不實際刪除檔案"
                echo "  --check-only  僅檢查，不執行清理"
                echo "  --help        顯示此幫助信息"
                exit 0
                ;;
            *)
                echo "未知選項: $1"
                exit 1
                ;;
        esac
    done
    
    # 創建日誌目錄
    mkdir -p "$LOG_DIR"
    
    local start_time=$(date +%s)
    log_info "========== 安全數據清理開始 =========="
    log_info "執行時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    log_info "清理策略: 只清理可重新生成的數據，保護原始 TLE 數據"
    
    if $dry_run; then
        log_info "模擬運行模式 - 不會實際刪除檔案"
    fi
    
    if $check_only; then
        show_cleanup_summary
        log_info "僅檢查模式 - 跳過實際清理"
        exit 0
    fi
    
    if ! $dry_run; then
        # 執行安全清理（不清理原始 TLE 數據）
        cleanup_precomputed_data
        cleanup_container_precomputed_data
        cleanup_backup_files
        cleanup_log_files
    fi
    
    # 顯示清理統計
    show_cleanup_summary
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "安全數據清理完成，耗時 ${duration} 秒"
    log_info "========== 安全數據清理結束 =========="
}

# 執行主函數
main "$@"