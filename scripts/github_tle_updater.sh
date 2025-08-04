#!/bin/bash
# =============================================================================
# GitHub TLE 數據更新器 - 適用於被封鎖 IP 的環境
# 解決方案：
# 1. 從 GitHub 倉庫下載最新 TLE 數據
# 2. 替代直接從 CelesTrak 下載
# 3. 保持與原有系統相同的檔案格式
# 4. 支援錯誤處理和降級操作
# =============================================================================

set -euo pipefail

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TLE_DATA_DIR="$PROJECT_ROOT/netstack/tle_data"
LOG_DIR="$PROJECT_ROOT/logs/tle_scheduler"  
LOG_FILE="$LOG_DIR/github_tle_update.log"
ERROR_LOG="$LOG_DIR/github_tle_error.log"

# GitHub 倉庫配置（需要用戶提供實際倉庫資訊）
GITHUB_REPO="${GITHUB_TLE_REPO:-your-username/tle-data-repo}"  # 用戶需要設置
GITHUB_BRANCH="${GITHUB_TLE_BRANCH:-main}"
GITHUB_API_TOKEN="${GITHUB_TLE_TOKEN:-}"  # 可選：私有倉庫需要

# 創建必要目錄
mkdir -p "$TLE_DATA_DIR"/{starlink,oneweb}/{tle,json} "$LOG_DIR"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日誌函數
log_info() { 
    local msg="${BLUE}[GITHUB_TLE]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_success() { 
    local msg="${GREEN}[SUCCESS]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_error() { 
    local msg="${RED}[ERROR]${NC} $@"
    echo -e "$msg" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $@" >> "$ERROR_LOG" 2>/dev/null || true
}

log_warn() { 
    local msg="${YELLOW}[WARNING]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $@" >> "$LOG_FILE" 2>/dev/null || true
}

# 檢查 GitHub 倉庫配置
check_github_config() {
    if [[ "$GITHUB_REPO" == "your-username/tle-data-repo" ]]; then
        log_error "GitHub 倉庫未配置！請設置環境變數 GITHUB_TLE_REPO"
        log_error "範例: export GITHUB_TLE_REPO=\"username/tle-data-repository\""
        return 1
    fi
    
    log_info "GitHub 倉庫: $GITHUB_REPO"
    log_info "分支: $GITHUB_BRANCH"
    return 0
}

# 從 GitHub 下載檔案
download_from_github() {
    local constellation="$1"
    local file_type="$2"  # "tle" or "json"
    local date_str="$3"
    
    # 構建 GitHub raw URL
    local github_base_url="https://raw.githubusercontent.com/$GITHUB_REPO/$GITHUB_BRANCH"
    local remote_filename="${constellation}_${date_str}.${file_type}"
    local github_url="$github_base_url/data/$constellation/$file_type/$remote_filename"
    
    # 本地檔案路徑
    local local_file="$TLE_DATA_DIR/$constellation/$file_type/$remote_filename"
    
    log_info "下載 $constellation $file_type 數據從 GitHub..."
    log_info "URL: $github_url"
    
    # 添加 GitHub token 支援（如果提供）
    local curl_opts=()
    if [[ -n "$GITHUB_API_TOKEN" ]]; then
        curl_opts+=("-H" "Authorization: token $GITHUB_API_TOKEN")
    fi
    
    # 使用臨時檔案下載
    local temp_file="${local_file}.tmp"
    
    if curl -L --fail --connect-timeout 30 --max-time 300 --retry 3 \
            "${curl_opts[@]}" -o "$temp_file" "$github_url" 2>/dev/null; then
        
        # 檢查檔案大小
        local file_size=$(stat -c%s "$temp_file")
        if [[ $file_size -lt 100 ]]; then
            log_error "$constellation $file_type 檔案過小 ($file_size bytes)"
            rm -f "$temp_file"
            return 1
        fi
        
        # 原子性移動檔案
        mv "$temp_file" "$local_file"
        touch "$local_file"  # 更新時間戳
        
        log_success "成功下載: $remote_filename ($file_size bytes)"
        return 0
    else
        rm -f "$temp_file"
        log_error "下載失敗: $remote_filename"
        return 1
    fi
}

# 嘗試下載最新可用的 TLE 數據
download_latest_available() {
    local constellation="$1"
    local current_date="$2"
    
    local success_count=0
    local dates_to_try=()
    
    # 構建要嘗試的日期列表（當前日期往前推 7 天）
    for i in {0..7}; do
        local test_date=$(date -u -d "$current_date -$i days" '+%Y%m%d' 2>/dev/null || \
                         date -u -v-${i}d -j -f "%Y%m%d" "$current_date" '+%Y%m%d' 2>/dev/null)
        if [[ -n "$test_date" ]]; then
            dates_to_try+=("$test_date")
        fi
    done
    
    log_info "嘗試下載 $constellation 數據，日期範圍: ${dates_to_try[0]} - ${dates_to_try[-1]}"
    
    # 嘗試下載 TLE 和 JSON 檔案
    for date_str in "${dates_to_try[@]}"; do
        log_info "嘗試日期: $date_str"
        
        local tle_success=false
        local json_success=false
        
        # 嘗試下載 TLE 檔案
        if download_from_github "$constellation" "tle" "$date_str"; then
            tle_success=true
        fi
        
        # 嘗試下載 JSON 檔案
        if download_from_github "$constellation" "json" "$date_str"; then
            json_success=true
        fi
        
        # 如果兩個檔案都成功，停止嘗試
        if $tle_success && $json_success; then
            log_success "$constellation 數據下載完成 (日期: $date_str)"
            success_count=2
            break
        elif $tle_success || $json_success; then
            log_warn "$constellation 部分數據下載成功 (日期: $date_str)"
            success_count=1
        fi
    done
    
    if [[ $success_count -eq 0 ]]; then
        log_error "$constellation 數據下載完全失敗"
        return 1
    elif [[ $success_count -eq 1 ]]; then
        log_warn "$constellation 數據部分下載成功"
        return 0
    else
        log_success "$constellation 數據下載完全成功"
        return 0
    fi
}

# 降級到使用現有數據
fallback_to_existing_data() {
    log_warn "GitHub 下載失敗，檢查是否有現有可用數據..."
    
    local existing_files=0
    
    # 檢查 Starlink 數據
    if ls "$TLE_DATA_DIR/starlink/tle/"*.tle 1> /dev/null 2>&1; then
        local latest_starlink=$(ls -t "$TLE_DATA_DIR/starlink/tle/"*.tle | head -1)
        local file_age=$(($(date +%s) - $(stat -c%Y "$latest_starlink")))
        local days_old=$((file_age / 86400))
        
        log_info "找到現有 Starlink 數據: $(basename "$latest_starlink") (${days_old} 天前)"
        existing_files=$((existing_files + 1))
    fi
    
    # 檢查 OneWeb 數據
    if ls "$TLE_DATA_DIR/oneweb/tle/"*.tle 1> /dev/null 2>&1; then
        local latest_oneweb=$(ls -t "$TLE_DATA_DIR/oneweb/tle/"*.tle | head -1)
        local file_age=$(($(date +%s) - $(stat -c%Y "$latest_oneweb")))
        local days_old=$((file_age / 86400))
        
        log_info "找到現有 OneWeb 數據: $(basename "$latest_oneweb") (${days_old} 天前)"
        existing_files=$((existing_files + 1))
    fi
    
    if [[ $existing_files -gt 0 ]]; then
        log_success "找到 $existing_files 組現有數據，系統可以繼續運行"
        return 0
    else
        log_error "未找到任何現有 TLE 數據，系統可能無法正常運行"
        return 1
    fi
}

# 主程序
main() {
    local start_time=$(date +%s)
    local current_date=$(date -u '+%Y%m%d')
    
    log_info "========== GitHub TLE 數據更新開始 =========="
    log_info "執行時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    log_info "目標日期: $current_date"
    
    # 檢查配置
    if ! check_github_config; then
        exit 1
    fi
    
    # 檢查網路連接
    log_info "檢查 GitHub 連接..."
    if ! curl -s --connect-timeout 10 "https://github.com" > /dev/null; then
        log_error "無法連接到 GitHub，請檢查網路連接"
        fallback_to_existing_data
        exit $?
    fi
    
    # 下載數據
    local starlink_result=1
    local oneweb_result=1
    
    echo "📡 開始從 GitHub 下載 Starlink 數據..."
    if download_latest_available "starlink" "$current_date"; then
        starlink_result=0
    fi
    
    echo "🛰️ 開始從 GitHub 下載 OneWeb 數據..."
    if download_latest_available "oneweb" "$current_date"; then
        oneweb_result=0
    fi
    
    # 結果統計
    local total_failures=$((starlink_result + oneweb_result))
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo
    echo "===== GitHub TLE 數據更新完成 ====="
    
    if [[ $starlink_result -eq 0 ]]; then
        echo -e "${GREEN}✅ Starlink: 更新成功${NC}"
    else
        echo -e "${RED}❌ Starlink: 更新失敗${NC}"
    fi
    
    if [[ $oneweb_result -eq 0 ]]; then
        echo -e "${GREEN}✅ OneWeb: 更新成功${NC}"
    else
        echo -e "${RED}❌ OneWeb: 更新失敗${NC}"
    fi
    
    echo "耗時: ${duration} 秒"
    echo "================================="
    
    if [[ $total_failures -eq 2 ]]; then
        log_error "所有數據更新失敗，嘗試降級處理..."
        fallback_to_existing_data
        exit $?
    elif [[ $total_failures -eq 1 ]]; then
        log_warn "部分數據更新失敗，但系統仍可運行"
        exit 0
    else
        log_success "所有數據更新成功"
        exit 0
    fi
}

# 顯示幫助信息
show_help() {
    echo "GitHub TLE 數據更新器"
    echo
    echo "用法: $0 [選項]"
    echo
    echo "環境變數:"
    echo "  GITHUB_TLE_REPO    GitHub 倉庫 (格式: username/repo-name)"
    echo "  GITHUB_TLE_BRANCH  分支名稱 (預設: main)"
    echo "  GITHUB_TLE_TOKEN   GitHub API Token (可選，私有倉庫需要)"
    echo
    echo "範例:"
    echo "  export GITHUB_TLE_REPO=\"myuser/tle-data\""
    echo "  export GITHUB_TLE_BRANCH=\"main\""
    echo "  $0"
    echo
    echo "選項:"
    echo "  --help    顯示此幫助信息"
}

# 命令行參數處理
if [[ $# -gt 0 ]] && [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# 執行主程序
main "$@"