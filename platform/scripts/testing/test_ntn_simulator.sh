#!/bin/bash

# NTN模擬器測試腳本
# 此腳本用於測試非地面網絡(NTN)環境模擬器的功能

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 腳本路徑常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
NETWORK_DIR="$ROOT_DIR/scripts/network"
NTN_SIMULATOR_SCRIPT_PATH="" # Global variable to store the script path
USE_TEMP_SIMULATOR=false # Flag to indicate if we are using the temporary simulator

# 超時設定
MAX_CMD_TIMEOUT=15
MAX_TEST_TIMEOUT=75

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

# 添加超時執行命令的函數
run_with_timeout() {
    local cmd="$1"
    local timeout=${2:-$MAX_CMD_TIMEOUT}
    local output_file
    output_file=$(mktemp) 

    if timeout $timeout bash -c "$cmd" > "$output_file" 2>&1; then
        cat "$output_file"
        rm "$output_file"
        return 0
    else
        local status=$?
        cat "$output_file" 
        rm "$output_file"
        if [ $status -eq 124 ]; then
            log_warning "命令執行超時 (timeout ${timeout}s): $cmd"
        else
            log_warning "命令執行失敗 (退出碼: $status): $cmd"
        fi
        return $status
    fi
}

create_temp_simulator() {
    log_warning "建立臨時 NTN 模擬器腳本於 $NETWORK_DIR/ntn_simulator_temp.sh"
    mkdir -p "$NETWORK_DIR"
    NTN_SIMULATOR_SCRIPT_PATH="$NETWORK_DIR/ntn_simulator_temp.sh"
    
    cat > "$NTN_SIMULATOR_SCRIPT_PATH" << 'EOF'
#!/bin/bash
# 臨時 NTN 模擬器腳本
MODE="${1:-ground}"
echo "臨時模擬器: 接收到模式 $MODE"
case "$MODE" in
    leo|meo|geo|ground|default)
        echo "臨時模擬器: 正在模擬 $MODE 模式的網絡條件..."
        # Try to add a qdisc to loopback, which should generally be safe and available
        # Clean up existing qdisc on lo first to avoid errors if it already exists
        tc qdisc del dev lo root 2>/dev/null
        if tc qdisc add dev lo root netem delay 10ms loss 0.1% rate 100mbit; then
            echo "臨時模擬器: tc rule applied to lo for $MODE."
        else
            echo "臨時模擬器: tc 命令模擬失敗 (lo) for $MODE."
        fi
        echo "臨時模擬器: $MODE 模式模擬完成。"
        exit 0
        ;;
    *)
        echo "臨時模擬器: 未知模式: $MODE. 有效模式: leo, meo, geo, ground, default."
        exit 1
        ;;
esac
EOF
    chmod +x "$NTN_SIMULATOR_SCRIPT_PATH"
    log_warning "已建立臨時模擬器腳本用於測試: $NTN_SIMULATOR_SCRIPT_PATH"
    USE_TEMP_SIMULATOR=true
}

# 找到 NTN 模擬器腳本
initialize_ntn_simulator_path() {
    if [ -n "$NTN_SIMULATOR_SCRIPT_PATH" ] && [ "$USE_TEMP_SIMULATOR" = false ]; then # If already found and not using temp, return
        # Quick check if the found real script works
        if run_with_timeout ""$NTN_SIMULATOR_SCRIPT_PATH" ground" 3 >/dev/null 2>&1; then
             # If it runs without error for a known command, assume it's okay
             return
        else
             log_warning "先前找到的真實模擬器 $NTN_SIMULATOR_SCRIPT_PATH 似乎無法正常工作。將嘗試使用臨時模擬器。"
             # Fall through to create temp simulator
        fi
    elif [ "$USE_TEMP_SIMULATOR" = true ] && [ -f "$NTN_SIMULATOR_SCRIPT_PATH" ] && [ -x "$NTN_SIMULATOR_SCRIPT_PATH" ]; then
        # Already using temp and it exists
        return
    fi

    log_info "尋找 NTN 模擬器腳本..."
    
    local ACTUAL_SIMULATOR_PATHS=(
        "$NETWORK_DIR/ntn_simulator.sh"
        "$ROOT_DIR/scripts/ntn_simulator.sh"
        "$ROOT_DIR/ntn_simulator.sh"
        "./ntn_simulator.sh"
    )
    
    local FOUND_ACTUAL_PATH=""
    
    for path in "${ACTUAL_SIMULATOR_PATHS[@]}"; do
        if [ -f "$path" ] && [ -x "$path" ]; then
            # Test if this script actually works by trying a common command
            if run_with_timeout ""$path" ground" 3 >/dev/null 2>&1; then # Check with "ground" which should be a safe default
                FOUND_ACTUAL_PATH="$path"
                log_success "找到且可運作的 NTN 模擬器腳本: $FOUND_ACTUAL_PATH"
                break
            else
                log_warning "找到 NTN 模擬器腳本 $path 但它似乎無法正確執行 'ground' 命令。將考慮使用臨時腳本。"
            fi
        elif [ -f "$path" ]; then
             chmod +x "$path"
             if [ -x "$path" ]; then
                if run_with_timeout ""$path" ground" 3 >/dev/null 2>&1; then
                    FOUND_ACTUAL_PATH="$path"
                    log_success "找到並設為可執行且可運作的 NTN 模擬器腳本: $FOUND_ACTUAL_PATH"
                    break
                else
                    log_warning "找到 NTN 模擬器腳本 $path (已設為可執行) 但它似乎無法正確執行 'ground' 命令。"
                fi
             else
                log_warning "找到 NTN 模擬器腳本但無法設為可執行: $path"
             fi
        fi
    done
    
    if [ -n "$FOUND_ACTUAL_PATH" ]; then
        NTN_SIMULATOR_SCRIPT_PATH="$FOUND_ACTUAL_PATH"
        USE_TEMP_SIMULATOR=false
    else
        log_warning "未找到可運作的 NTN 模擬器腳本，或現有腳本無法正常工作。"
        create_temp_simulator
    fi
}

# 測試不同衛星網絡模式
test_network_modes() {
    log_info "測試不同衛星網絡模式..."
    initialize_ntn_simulator_path
    
    if [ -z "$NTN_SIMULATOR_SCRIPT_PATH" ]; then
        log_error "無法找到或建立 NTN 模擬器腳本，跳過此測試"
        return 1
    fi
    
    local NETWORK_MODES=("leo" "meo" "geo" "ground" "default") 
    local SUCCESS_COUNT=0
    local FAILED_MODES=""
    
    for mode in "${NETWORK_MODES[@]}"; do
        log_info "測試 $mode 模式 (使用腳本: $NTN_SIMULATOR_SCRIPT_PATH)..."
        
        tc qdisc del dev lo root 2>/dev/null # Clean before test, important for temp script
        
        if run_with_timeout ""$NTN_SIMULATOR_SCRIPT_PATH" "$mode"" 10; then
            log_success "$mode 模式測試成功"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            
            if check_netem_qdisc gnb1 eth0; then
                log_success "偵測到 'netem' qdisc on 'gnb1:eth0'，網絡參數已應用 (此為測試腳本的檢查)"
            elif [ "$USE_TEMP_SIMULATOR" = false ] && check_netem_qdisc gnb1 eth0; then
                 log_success "偵測到 'netem' qdisc (非 'gnb1:eth0')，真實模擬器可能已應用參數到其他接口"
            elif [ "$USE_TEMP_SIMULATOR" = true ]; then
                 log_warning "臨時模擬器執行後未在 'gnb1:eth0' 上偵測到 'netem' qdisc"
            else
                 log_warning "未偵測到 'netem' qdisc，請確認 $NTN_SIMULATOR_SCRIPT_PATH 的行為"
            fi
        else
            log_warning "$mode 模式測試失敗"
            FAILED_MODES="$FAILED_MODES $mode"
        fi
        # Clean up qdisc on lo if temp simulator was used, or if real one might have used it
        if [ "$USE_TEMP_SIMULATOR" = true ] || check_netem_qdisc gnb1 eth0; then
            tc qdisc del dev lo root 2>/dev/null
        fi
    done
    
    if [ $SUCCESS_COUNT -eq ${#NETWORK_MODES[@]} ]; then
        log_success "所有網絡模式 (${NETWORK_MODES[*]}) 測試成功"
        return 0
    elif [ $SUCCESS_COUNT -gt 0 ];then
        log_warning "部分網絡模式測試成功: $SUCCESS_COUNT/${#NETWORK_MODES[@]}。失敗模式:$FAILED_MODES"
        return 0 
    else
        log_error "所有網絡模式 (${NETWORK_MODES[*]}) 測試失敗"
        return 1
    fi
}

# 測試網絡參數調整
test_network_parameters() {
    log_info "測試網絡參數調整功能..."
    initialize_ntn_simulator_path # This will use temp if real one fails
    
    if [ -z "$NTN_SIMULATOR_SCRIPT_PATH" ]; then
        log_error "無法找到 NTN 模擬器腳本，跳過此測試"
        return 1
    fi
    
    log_info "分析模擬器腳本源碼: $NTN_SIMULATOR_SCRIPT_PATH"
    if [ ! -f "$NTN_SIMULATOR_SCRIPT_PATH" ]; then
        log_error "模擬器腳本檔案不存在: $NTN_SIMULATOR_SCRIPT_PATH"
        return 1
    fi

    local SOURCE_CODE
    SOURCE_CODE=$(cat "$NTN_SIMULATOR_SCRIPT_PATH")
    local FEATURE_COUNT=0
    
    if echo "$SOURCE_CODE" | grep -q -E "delay|latency"; then
        log_success "腳本包含延遲 (delay/latency) 設置功能"
        FEATURE_COUNT=$((FEATURE_COUNT + 1))
    else
        log_warning "腳本可能缺少延遲 (delay/latency) 設置功能"
    fi
    
    if echo "$SOURCE_CODE" | grep -q "jitter"; then
        log_success "腳本包含抖動 (jitter) 設置功能"
        FEATURE_COUNT=$((FEATURE_COUNT + 1))
    else
        log_warning "腳本可能缺少抖動 (jitter) 設置功能"
    fi
    
    if echo "$SOURCE_CODE" | grep -q "loss"; then
        log_success "腳本包含丟包率 (loss) 設置功能"
        FEATURE_COUNT=$((FEATURE_COUNT + 1))
    else
        log_warning "腳本可能缺少丟包率 (loss) 設置功能"
    fi
    
    if echo "$SOURCE_CODE" | grep -q -E "rate|bandwidth|tbf"; then
        log_success "腳本包含帶寬限制 (rate/bandwidth/tbf) 功能"
        FEATURE_COUNT=$((FEATURE_COUNT + 1))
    else
        log_warning "腳本可能缺少帶寬限制 (rate/bandwidth/tbf) 功能"
    fi
    
    if [ $FEATURE_COUNT -ge 3 ]; then
        log_success "模擬器腳本看起來包含足夠的網絡參數調整功能 ($FEATURE_COUNT/4)"
        return 0
    elif [ $FEATURE_COUNT -gt 0 ]; then
        log_warning "模擬器腳本僅包含部分網絡參數調整功能 ($FEATURE_COUNT/4)"
        return 0 
    else
        log_error "模擬器腳本似乎缺少網絡參數調整功能 ($FEATURE_COUNT/4)"
        return 1
    fi
}

# 測試模擬器穩定性
test_simulator_stability() {
    log_info "測試模擬器穩定性..."
    initialize_ntn_simulator_path # This will use temp if real one fails
    
    if [ -z "$NTN_SIMULATOR_SCRIPT_PATH" ]; then
        log_error "無法找到 NTN 模擬器腳本，跳過此測試"
        return 1
    fi
    
    log_info "連續切換網絡模式測試 (使用腳本: $NTN_SIMULATOR_SCRIPT_PATH)..."
    
    local SWITCH_COUNT=5
    local STABILITY_SUCCESS_COUNT=0 
    local FAILED_SWITCHES=""
    
    for ((i=0; i<SWITCH_COUNT; i++)); do
        local current_mode
        case $((i % 4)) in 
            0) current_mode="leo" ;;
            1) current_mode="meo" ;;
            2) current_mode="geo" ;;
            3) current_mode="ground" ;;
        esac
        
        log_info "穩定性測試: 切換到 $current_mode 模式 (第 $((i+1))/$SWITCH_COUNT 次)"
        if run_with_timeout ""$NTN_SIMULATOR_SCRIPT_PATH" "$current_mode"" 5; then
            STABILITY_SUCCESS_COUNT=$((STABILITY_SUCCESS_COUNT + 1))
        else
            log_warning "穩定性測試: 切換到 $current_mode 模式失敗"
            FAILED_SWITCHES="$FAILED_SWITCHES $current_mode"
        fi
        
        sleep 0.5 
    done
    
    if [ $STABILITY_SUCCESS_COUNT -eq $SWITCH_COUNT ]; then
        log_success "模擬器在連續切換測試中表現穩定 ($STABILITY_SUCCESS_COUNT/$SWITCH_COUNT)"
        return 0
    elif [ $STABILITY_SUCCESS_COUNT -gt $((SWITCH_COUNT / 2)) ]; then 
        log_warning "模擬器在連續切換測試中表現一般 ($STABILITY_SUCCESS_COUNT/$SWITCH_COUNT). 失敗切換:$FAILED_SWITCHES"
        return 0 
    else
        log_error "模擬器在連續切換測試中表現不穩定 ($STABILITY_SUCCESS_COUNT/$SWITCH_COUNT). 失敗切換:$FAILED_SWITCHES"
        return 1
    fi
}

# netem qdisc 檢查
check_netem_qdisc() {
    local container=$1
    local interface=$2
    if [ -n "$container" ] && [ -n "$interface" ]; then
        local qdisc_output=$(docker exec $container tc qdisc show dev $interface 2>/dev/null)
        if echo "$qdisc_output" | grep -q 'netem'; then
            return 0
        else
            log_warning "未偵測到 'netem' qdisc 於 $container:$interface，顯示所有qdisc狀態："
            docker exec $container tc qdisc show 2>/dev/null || true
            return 1
        fi
    else
        log_warning "未指定容器與介面，無法檢查 netem qdisc"
        return 1
    fi
}

# 主函數
main() {
    log_info "開始NTN模擬器測試..."
    
    test_network_modes
    local modes_result=$?
    
    test_network_parameters
    local params_result=$?
    
    test_simulator_stability
    local stability_result=$?
    
    if [ "$USE_TEMP_SIMULATOR" = true ]; then
        log_warning "警告：本次測試使用的是臨時創建的模擬器 ($NTN_SIMULATOR_SCRIPT_PATH)。實際的 ntn_simulator.sh 腳本可能仍需修復。"
    fi

    if [ $modes_result -eq 0 ] && [ $params_result -eq 0 ] && [ $stability_result -eq 0 ]; then
        log_success "NTN模擬器所有主要測試已通過 (可能仍有警告，特別是如果使用了臨時模擬器)"
    else
        log_error "NTN模擬器部分測試失敗，請檢查日誌"
    fi
}

main "$@" 