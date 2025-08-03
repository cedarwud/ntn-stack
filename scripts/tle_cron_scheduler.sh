#!/bin/bash
# =============================================================================
# TLE 數據自動排程下載系統
# 功能：
# 1. 設置 cron 排程（每 6 小時執行一次）
# 2. 管理排程任務（啟用/停用/狀態檢查）
# 3. 日誌管理和錯誤處理
# =============================================================================

set -euo pipefail

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TLE_SCRIPT="$SCRIPT_DIR/daily_tle_download_enhanced.sh"
LOG_DIR="$PROJECT_ROOT/logs/tle_scheduler"
LOG_FILE="$LOG_DIR/tle_download.log"
ERROR_LOG="$LOG_DIR/tle_error.log"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 簡化列印函數
log_info() { echo -e "${BLUE}[INFO]${NC} $@"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $@"; }
log_error() { echo -e "${RED}[ERROR]${NC} $@"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $@"; }

# 創建必要目錄
create_directories() {
    mkdir -p "$LOG_DIR"
    
    # 確保下載腳本可執行
    if [[ -f "$TLE_SCRIPT" ]]; then
        chmod +x "$TLE_SCRIPT"
    else
        log_error "TLE 下載腳本不存在: $TLE_SCRIPT"
        exit 1
    fi
}

# 生成 cron 條目
generate_cron_entry() {
    local cron_entry="# TLE 數據自動下載（每 6 小時執行一次）
# 分別在 02:00, 08:00, 14:00, 20:00 執行
0 2,8,14,20 * * * $TLE_SCRIPT >> $LOG_FILE 2>> $ERROR_LOG"
    
    echo "$cron_entry"
}

# 檢查 cron 是否已存在
cron_exists() {
    if crontab -l 2>/dev/null | grep -q "$TLE_SCRIPT"; then
        return 0
    else
        return 1
    fi
}

# 安裝 cron 排程
install_cron() {
    log_info "正在安裝 TLE 數據下載排程..."
    
    # 檢查是否已存在
    if cron_exists; then
        log_warn "TLE 下載排程已存在，將覆蓋舊設定"
        remove_cron
    fi
    
    # 獲取現有 crontab 內容
    local temp_cron=$(mktemp)
    crontab -l 2>/dev/null > "$temp_cron" || true
    
    # 添加新的 cron 條目
    echo "" >> "$temp_cron"
    generate_cron_entry >> "$temp_cron"
    
    # 安裝新的 crontab
    if crontab "$temp_cron"; then
        log_success "TLE 下載排程已成功安裝"
        log_info "執行時間: 每天 02:00, 08:00, 14:00, 20:00 (UTC)"
        log_info "日誌文件: $LOG_FILE"
        log_info "錯誤日誌: $ERROR_LOG"
    else
        log_error "安裝 cron 排程失敗"
        rm -f "$temp_cron"
        exit 1
    fi
    
    rm -f "$temp_cron"
}

# 移除 cron 排程
remove_cron() {
    log_info "正在移除 TLE 數據下載排程..."
    
    if ! cron_exists; then
        log_warn "TLE 下載排程不存在"
        return 0
    fi
    
    # 獲取現有 crontab 內容並移除相關條目
    local temp_cron=$(mktemp)
    crontab -l 2>/dev/null | grep -v "$TLE_SCRIPT" | grep -v "# TLE 數據自動下載" > "$temp_cron" || true
    
    # 移除空行
    sed -i '/^$/d' "$temp_cron"
    
    # 安裝修改後的 crontab
    if crontab "$temp_cron"; then
        log_success "TLE 下載排程已成功移除"
    else
        log_error "移除 cron 排程失敗"
        rm -f "$temp_cron"
        exit 1
    fi
    
    rm -f "$temp_cron"
}

# 顯示排程狀態
show_status() {
    echo
    echo "===== TLE 下載排程狀態 ====="
    
    if cron_exists; then
        log_success "排程狀態: 已啟用"
        echo
        echo "Cron 條目:"
        crontab -l 2>/dev/null | grep -A1 -B1 "$TLE_SCRIPT" || true
        echo
        
        # 檢查日誌文件
        if [[ -f "$LOG_FILE" ]]; then
            local log_size=$(du -h "$LOG_FILE" | cut -f1)
            local last_modified=$(stat -c%y "$LOG_FILE" 2>/dev/null | cut -d'.' -f1)
            echo "日誌文件: $LOG_FILE ($log_size, 最後修改: $last_modified)"
        else
            echo "日誌文件: 尚未創建"
        fi
        
        if [[ -f "$ERROR_LOG" ]]; then
            local error_size=$(du -h "$ERROR_LOG" | cut -f1)
            local error_count=$(wc -l < "$ERROR_LOG" 2>/dev/null || echo "0")
            echo "錯誤日誌: $ERROR_LOG ($error_size, $error_count 行)"
        else
            echo "錯誤日誌: 尚未創建"
        fi
        
        # 顯示下一次執行時間
        echo
        echo "下次執行時間:"
        echo "  今天: $(date -d 'today 02:00' '+%Y-%m-%d %H:%M' 2>/dev/null || echo 'N/A'), $(date -d 'today 08:00' '+%H:%M' 2>/dev/null || echo 'N/A'), $(date -d 'today 14:00' '+%H:%M' 2>/dev/null || echo 'N/A'), $(date -d 'today 20:00' '+%H:%M' 2>/dev/null || echo 'N/A')"
        echo "  明天: $(date -d 'tomorrow 02:00' '+%Y-%m-%d %H:%M' 2>/dev/null || echo 'N/A')"
        
    else
        log_warn "排程狀態: 未啟用"
    fi
    
    echo "=========================="
    echo
}

# 顯示最近的日誌
show_logs() {
    local lines=${1:-20}
    
    echo
    echo "===== 最近的執行日誌 (最近 $lines 行) ====="
    
    if [[ -f "$LOG_FILE" ]]; then
        tail -n "$lines" "$LOG_FILE"
    else
        log_warn "日誌文件不存在: $LOG_FILE"
    fi
    
    echo
    echo "===== 最近的錯誤日誌 (最近 $lines 行) ====="
    
    if [[ -f "$ERROR_LOG" ]]; then
        if [[ -s "$ERROR_LOG" ]]; then
            tail -n "$lines" "$ERROR_LOG"
        else
            log_info "無錯誤記錄"
        fi
    else
        log_warn "錯誤日誌文件不存在: $ERROR_LOG"
    fi
    
    echo "=============================="
    echo
}

# 測試下載（手動執行一次）
test_download() {
    log_info "執行測試下載..."
    echo
    
    if [[ -f "$TLE_SCRIPT" ]]; then
        # 執行下載腳本並顯示輸出
        if "$TLE_SCRIPT"; then
            log_success "測試下載完成"
        else
            log_error "測試下載失敗"
            exit 1
        fi
    else
        log_error "TLE 下載腳本不存在: $TLE_SCRIPT"
        exit 1
    fi
}

# 日誌輪替（保留最近 30 天）
rotate_logs() {
    log_info "執行日誌輪替..."
    
    # 壓縮舊日誌
    if [[ -f "$LOG_FILE" ]] && [[ $(stat -c%s "$LOG_FILE" 2>/dev/null || echo "0") -gt 1048576 ]]; then  # 1MB
        local timestamp=$(date '+%Y%m%d_%H%M%S')
        gzip -c "$LOG_FILE" > "$LOG_DIR/tle_download_$timestamp.log.gz"
        > "$LOG_FILE"  # 清空當前日誌
        log_info "日誌文件已輪替: tle_download_$timestamp.log.gz"
    fi
    
    if [[ -f "$ERROR_LOG" ]] && [[ $(stat -c%s "$ERROR_LOG" 2>/dev/null || echo "0") -gt 1048576 ]]; then  # 1MB
        local timestamp=$(date '+%Y%m%d_%H%M%S')
        gzip -c "$ERROR_LOG" > "$LOG_DIR/tle_error_$timestamp.log.gz"
        > "$ERROR_LOG"  # 清空當前錯誤日誌
        log_info "錯誤日誌文件已輪替: tle_error_$timestamp.log.gz"
    fi
    
    # 刪除 30 天前的壓縮日誌
    find "$LOG_DIR" -name "*.log.gz" -mtime +30 -delete 2>/dev/null || true
    
    log_success "日誌輪替完成"
}

# 顯示使用說明
show_help() {
    echo "TLE 數據自動排程下載系統"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  install    - 安裝 cron 排程（每 6 小時執行一次）"
    echo "  remove     - 移除 cron 排程"
    echo "  status     - 顯示排程狀態和配置信息"
    echo "  logs [n]   - 顯示最近的日誌（預設 20 行）"
    echo "  test       - 手動執行一次下載測試"
    echo "  rotate     - 執行日誌輪替"
    echo "  help       - 顯示此幫助信息"
    echo
    echo "範例:"
    echo "  $0 install          # 安裝排程"
    echo "  $0 status           # 檢查狀態"
    echo "  $0 logs 50          # 顯示最近 50 行日誌"
    echo "  $0 test             # 測試下載"
    echo
}

# 主程序
main() {
    # 創建必要目錄
    create_directories
    
    case "${1:-help}" in
        "install")
            install_cron
            ;;
        "remove")
            remove_cron
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-20}"
            ;;
        "test")
            test_download
            ;;
        "rotate")
            rotate_logs
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 執行主程序
main "$@"