#!/bin/bash

# 基礎 5G 網絡功能擴展測試主腳本
# 此腳本執行所有測試以確認各功能模塊已完成並正常工作

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 腳本路徑常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
TESTING_DIR="$ROOT_DIR/scripts/testing"
SCRIPT_NAME=$(basename "$0")

# 設定最大超時時間（單位：秒）
MAX_SCRIPT_TIMEOUT=300

# 日誌函數
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() { 
    echo -e "${RED}[ERROR]${NC} $1"
}

# 顯示使用幫助
show_help() {
    echo "用法: $SCRIPT_NAME [options]"
    echo
    echo "選項:"
    echo "  all         執行所有測試"
    echo "  clean       清理生成的測試文件"
    echo "  essential   只執行關鍵測試"
    echo "  help        顯示此幫助信息"
    echo
    echo "範例:"
    echo "  $SCRIPT_NAME all      執行所有測試"
    echo "  $SCRIPT_NAME clean    清理生成的測試文件"
    echo "  $SCRIPT_NAME          只執行必要的測試"
}

# 清理生成的測試文件
clean_test_files() {
    log_info "清理生成的測試文件..."
    
    # 檢查生成的配置文件目錄
    local CONFIG_DIRS=(
        "$ROOT_DIR/config/generated"
        "$ROOT_DIR/config/ueransim"
        "$ROOT_DIR/config/test"
        "$ROOT_DIR/config/temp"
    )
    
    local total_cleaned=0
    
    for config_dir in "${CONFIG_DIRS[@]}"; do
        if [ -d "$config_dir" ]; then
            # 獲取生成的文件數量
            local file_count=$(find "$config_dir" -name "test_*.yaml" 2>/dev/null | wc -l)
            
            if [ "$file_count" -gt 0 ]; then
                log_info "發現 $file_count 個測試配置文件在 $config_dir"
                
                # 只保留最新的3個文件
                if [ "$file_count" -gt 3 ]; then
                    log_info "保留最新的3個配置文件，刪除其他舊文件"
                    find "$config_dir" -name "test_*.yaml" | sort | head -n -3 | xargs rm -f 2>/dev/null || {
                        log_warning "無法刪除部分文件，可能需要更高權限"
                    }
                    total_cleaned=$((total_cleaned + file_count - 3))
                fi
            fi
        fi
    done
    
    # 清理所有可能的臨時目錄
    local TEMP_DIRS=(
        "/tmp/ntn-test-config"
        "/tmp/ueransim-test"
        "/tmp/open5gs-test"
        "/tmp/test-results"
    )
    
    for temp_dir in "${TEMP_DIRS[@]}"; do
        if [ -d "$temp_dir" ]; then
            log_info "清理臨時目錄: $temp_dir"
            rm -rf "$temp_dir" 2>/dev/null || log_warning "無法完全刪除臨時目錄: $temp_dir"
        fi
    done
    
    # 刪除超過3天的測試報告
    if [ -d "$ROOT_DIR/reports" ]; then
        local old_reports=$(find "$ROOT_DIR/reports" -name "test_report_*.txt" -mtime +3 2>/dev/null | wc -l)
        if [ "$old_reports" -gt 0 ]; then
            log_info "刪除 $old_reports 個超過3天的測試報告"
            find "$ROOT_DIR/reports" -name "test_report_*.txt" -mtime +3 -delete 2>/dev/null || log_warning "無法刪除舊測試報告"
            total_cleaned=$((total_cleaned + old_reports))
        fi
    fi
    
    # 清理可能存在的日誌文件
    find "$ROOT_DIR" -name "test_*.log" -mtime +1 -delete 2>/dev/null
    find "$ROOT_DIR" -name "config_*.log" -mtime +1 -delete 2>/dev/null
    
    log_success "清理測試文件完成，共清理 $total_cleaned 個文件"
}

# 測試前準備
prepare_tests() {
    log_info "測試前準備..."
    
    # 定義需要檢查的所有測試腳本
    local ALL_TEST_SCRIPTS=(
        "test_subscriber_management.sh"
        "test_monitor_system.sh"
        "test_system_integration.sh"
        "test_open5gs_config.sh"
        "performance_test.sh"
        "test_ueransim_config.sh"
        "ensure_templates.sh"
        "test_ntn_simulator.sh"
        "test_network_diagnostic.sh"
    )
    
    # 確保所有測試腳本可執行
    for script in "${ALL_TEST_SCRIPTS[@]}"; do
        if [ -f "$TESTING_DIR/$script" ]; then
            chmod +x "$TESTING_DIR/$script"
        else
            log_warning "測試腳本不存在: $script，將被跳過"
        fi
    done
    
    # 確保存在必要的目錄結構
    mkdir -p "$ROOT_DIR/config/ueransim" 2>/dev/null || true
    mkdir -p "$ROOT_DIR/config/generated" 2>/dev/null || true
    mkdir -p "$ROOT_DIR/reports" 2>/dev/null || true
    
    # 執行模板檢查和同步腳本，使用超時命令確保不會卡住
    if [ -f "$TESTING_DIR/ensure_templates.sh" ]; then
        timeout 30 "$TESTING_DIR/ensure_templates.sh" || log_warning "模板檢查腳本執行超時"
    else
        log_warning "模板檢查腳本不存在: ensure_templates.sh"
    fi
    
    # 檢查模板是否存在，否則創建基本模板
    check_and_create_templates
    
    return 0
}

# 檢查並創建模板
check_and_create_templates() {
    local TEMPLATE_DIR="$ROOT_DIR/config/ueransim"
    
    # 確保模板目錄存在
    mkdir -p "$TEMPLATE_DIR" 2>/dev/null || {
        log_warning "無法創建模板目錄: $TEMPLATE_DIR"
        return 1
    }
    
    # 定義必須的模板
    local REQUIRED_TEMPLATES=(
        "gnb_leo.yaml"
        "gnb_geo.yaml" 
        "gnb_meo.yaml"
        "gnb_ground.yaml"
        "ue_leo.yaml"
        "ue_geo.yaml"
        "ue_meo.yaml"
        "ue_ground.yaml"
    )
    
    local MISSING=0
    
    for template in "${REQUIRED_TEMPLATES[@]}"; do
        if [ ! -f "$TEMPLATE_DIR/$template" ]; then
            MISSING=1
            log_warning "模板文件缺失: $template，將創建基本版本"
            
            # 獲取模板類型和模式
            local TYPE=$(echo "$template" | cut -d'_' -f1)
            local MODE=$(echo "$template" | cut -d'_' -f2 | cut -d'.' -f1)
            
            # 創建基本模板
            if [ "$TYPE" == "gnb" ]; then
                cat > "$TEMPLATE_DIR/$template" << EOF
# 基本 gNodeB 配置模板 ($MODE 模式)
mcc: '999'
mnc: '70'
nci: '0x000000010'
idLength: 32
name: 'gnb-$MODE'
linkIp: 127.0.0.1
ngapIp: 127.0.0.1
gtpIp: 127.0.0.1
# $MODE 特定設置
mode: '$MODE'
EOF
            elif [ "$TYPE" == "ue" ]; then
                cat > "$TEMPLATE_DIR/$template" << EOF
# 基本 UE 配置模板 ($MODE 模式)
supi: 'imsi-999700000000001'
mcc: '999'
mnc: '70'
key: '465B5CE8B199B49FAA5F0A2EE238A6BC'
op: 'E8ED289DEBA952E4283B54E88E6183CA'
session:
  - type: 'IPv4'
    apn: 'internet'
    slice:
      sst: 1
# $MODE 特定設置
mode: '$MODE'
EOF
            fi
        fi
    done
    
    if [ $MISSING -eq 1 ]; then
        log_info "已創建缺失的模板文件"
    else
        log_success "所有必需的模板文件已存在"
    fi
    
    return 0
}

# 執行測試腳本並捕獲結果
run_test_script() {
    local script="$1"
    local script_name=$(basename "$script")
    local script_result_file="/tmp/${script_name%.sh}_result.txt"
    local start_time=$(date +%s)
    local exit_code=0
    local duration=0
    
    # 檢查腳本是否存在
    if [ ! -f "$script" ]; then
        log_error "測試腳本不存在: $script"
        echo "SKIPPED" > "$script_result_file"
        return 1
    fi
    
    log_info "運行測試腳本: $script_name"
    
    # 使用超時命令運行腳本，避免無限等待
    timeout $MAX_SCRIPT_TIMEOUT "$script" > "$script_result_file" 2>&1 || {
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_error "測試腳本執行超時: $script_name"
            echo "TIMEOUT" >> "$script_result_file"
        else
            log_error "測試腳本執行失敗: $script_name, 退出碼: $exit_code"
            echo "FAILED (Code: $exit_code)" >> "$script_result_file"
        fi
    }
    
    # 計算運行時間
    local end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    # 分析結果文件中的警告和錯誤
    local warnings=$(grep -c "\[WARNING\]" "$script_result_file" || echo 0)
    local errors=$(grep -c "\[ERROR\]" "$script_result_file" || echo 0)
    
    if grep -q "TIMEOUT" "$script_result_file"; then
        log_error "$script_name: 超時 (${duration}s)"
        return 1
    elif grep -q "FAILED" "$script_result_file"; then
        log_error "$script_name: 失敗 (${duration}s), 錯誤: $errors, 警告: $warnings"
        return 1
    elif grep -q "SKIPPED" "$script_result_file"; then
        log_warning "$script_name: 跳過"
        return 2
    else
        if [ $warnings -gt 0 ]; then
            log_warning "$script_name: 成功 (${duration}s), 但有 $warnings 個警告"
        else
            log_success "$script_name: 成功 (${duration}s)"
        fi
        return 0
    fi
}

# 運行所有測試並生成報告
run_all_tests() {
    log_info "開始執行所有測試..."
    
    # 測試開始時間
    local TEST_START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    local TEST_START_TIMESTAMP=$(date +%s)
    
    # 創建報告目錄
    mkdir -p "$ROOT_DIR/reports" 2>/dev/null || {
        log_warning "無法創建報告目錄，將使用臨時目錄"
        ROOT_DIR="/tmp"
    }
    
    # 創建報告文件
    local REPORT_FILE="$ROOT_DIR/reports/test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    # 初始化報告
    cat > "$REPORT_FILE" << EOF
===== 基礎 5G 網絡功能擴展測試報告 =====
測試時間: $TEST_START_TIME

測試項目結果:
EOF
    
    # 清理臨時結果文件
    rm -f /tmp/*_result.txt 2>/dev/null || true
    
    # 按優先順序定義測試腳本
    local TEST_SCRIPTS=(
        "$TESTING_DIR/test_open5gs_config.sh"
        "$TESTING_DIR/test_ueransim_config.sh"
        "$TESTING_DIR/test_subscriber_management.sh"
        "$TESTING_DIR/test_monitor_system.sh"
        "$TESTING_DIR/test_ntn_simulator.sh"
        "$TESTING_DIR/test_network_diagnostic.sh"
        "$TESTING_DIR/test_system_integration.sh"
    )
    
    # 運行測試腳本並收集結果
    local all_passed=true
    local test_results=""
    
    for script in "${TEST_SCRIPTS[@]}"; do
        local script_name=$(basename "$script")
        local script_base=${script_name%.sh}
        
        # 運行測試腳本
        run_test_script "$script"
        local script_status=$?
        
        # 更新測試結果
        if [ $script_status -eq 0 ]; then
            test_results="${test_results}- ${script_base}: 通過\n"
        elif [ $script_status -eq 2 ]; then
            test_results="${test_results}- ${script_base}: 跳過\n"
            all_passed=false
        else
            test_results="${test_results}- ${script_base}: 失敗\n"
            all_passed=false
        fi
    done
    
    # 檢查Docker容器狀態
    local DOCKER_STATUS=$(docker ps --format "{{.Names}}: {{.Status}}" 2>/dev/null || echo "無法獲取容器狀態")
    
    # 計算總測試時間
    local TEST_END_TIMESTAMP=$(date +%s)
    local TEST_DURATION=$((TEST_END_TIMESTAMP - TEST_START_TIMESTAMP))
    local MINS=$((TEST_DURATION / 60))
    local SECS=$((TEST_DURATION % 60))
    
    # 總結測試結果
    echo -e "$test_results" >> "$REPORT_FILE"
    echo -e "\n系統狀態:\n$DOCKER_STATUS" >> "$REPORT_FILE"
    echo -e "\n測試耗時: ${MINS}分${SECS}秒" >> "$REPORT_FILE"
    
    if $all_passed; then
        echo -e "\n總體結果: 通過 - 基礎 5G 網絡功能擴展已全部完成" >> "$REPORT_FILE"
        log_success "所有測試通過！總耗時: ${MINS}分${SECS}秒"
    else
        echo -e "\n總體結果: 部分失敗 - 某些功能可能尚未完成或存在問題" >> "$REPORT_FILE"
        log_warning "測試部分失敗，請查看詳細報告。總耗時: ${MINS}分${SECS}秒"
    fi
    
    # 顯示報告位置
    log_info "測試報告已保存至: $REPORT_FILE"
    
    # 分析和總結警告問題
    analyze_warnings
    
    return 0
}

# 運行關鍵測試
run_essential_tests() {
    log_info "開始執行關鍵測試..."
    
    # 只運行必要的測試腳本
    local ESSENTIAL_SCRIPTS=(
        "$TESTING_DIR/test_open5gs_config.sh"
        "$TESTING_DIR/test_system_integration.sh"
    )
    
    local all_passed=true
    
    for script in "${ESSENTIAL_SCRIPTS[@]}"; do
        local script_name=$(basename "$script")
        
        # 檢查腳本是否存在
        if [ ! -f "$script" ]; then
            log_warning "關鍵測試腳本不存在: $script_name，將被跳過"
            all_passed=false
            continue
        fi
        
        # 運行測試腳本
        run_test_script "$script"
        local script_status=$?
        
        # 更新測試結果
        if [ $script_status -ne 0 ]; then
            all_passed=false
        fi
    done
    
    if $all_passed; then
        log_success "所有關鍵測試通過！"
    else
        log_warning "部分關鍵測試失敗"
    fi
    
    return 0
}

# 分析和處理測試中的警告問題
analyze_warnings() {
    log_info "分析測試警告問題..."
    
    # 收集所有測試結果文件中的警告信息
    local all_warnings=$(grep "\[WARNING\]" /tmp/*_result.txt 2>/dev/null || echo "")
    local warning_count=$(echo "$all_warnings" | grep -c "\[WARNING\]" || echo 0)
    
    if [ "$warning_count" -gt 0 ]; then
        log_warning "測試中發現 $warning_count 個警告問題"
        
        # 分析最常見的警告
        log_info "最常見的警告類型:"
        echo "$all_warnings" | sed 's/.*\[WARNING\] //' | sort | uniq -c | sort -nr | head -5 | while read -r line; do
            log_warning "- $line"
        done
        
        # 提供建議修復順序
        log_info "建議的修復順序:"
        
        # 先處理超時問題
        if echo "$all_warnings" | grep -q "超時\|超過"; then
            log_warning "1. 修復腳本超時問題，可能需要調整超時設置或優化腳本效率"
        fi
        
        # 處理缺少組件或模板問題
        if echo "$all_warnings" | grep -q "找不到\|缺失\|不存在"; then
            log_warning "2. 確保所有必要的組件、模板和腳本都存在"
        fi
        
        # 處理權限問題
        if echo "$all_warnings" | grep -q "權限\|permission"; then
            log_warning "3. 修復權限相關問題"
        fi
        
        # 處理網絡連接問題
        if echo "$all_warnings" | grep -q "連接\|connection"; then
            log_warning "4. 檢查網絡連接和配置問題"
        fi
        
        # 其他問題
        log_warning "5. 解決其他警告問題"
    else
        log_success "測試中未發現警告問題！"
    fi
}

# 主函數
main() {
    # 如果沒有參數，顯示使用幫助
    if [ $# -eq 0 ]; then
        # 默認執行關鍵測試
        prepare_tests
        run_essential_tests
        return 0
    fi
    
    # 處理參數
    case "$1" in
        all)
            prepare_tests
            run_all_tests
            ;;
        clean)
            clean_test_files
            ;;
        essential)
            prepare_tests
            run_essential_tests
            ;;
        help)
            show_help
            ;;
        *)
            log_error "未知參數: $1"
            show_help
            return 1
            ;;
    esac
    
    return 0
}

# 執行主函數
main "$@" 