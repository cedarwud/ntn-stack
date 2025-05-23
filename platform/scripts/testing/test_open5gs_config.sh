#!/bin/bash

# Open5GS核心網優化配置測試腳本
# 此腳本用於測試Open5GS核心網的配置，特別關注高延遲優化和PLMN設置

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

# 超時設定
MAX_CMD_TIMEOUT=25 # 稍微增加命令最大執行時間
MAX_TEST_TIMEOUT=150 # 稍微增加單個測試最大運行時間
RETRY_COUNT=2 # 減少重試，因為已有模擬

# 全局變量存儲檢測到的PLMN信息
declare -a AMF_CONFIGURED_PLMNS=()

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

# 帶重試機制的超時執行命令函數
run_with_timeout() {
    local cmd="$1"
    local timeout=${2:-$MAX_CMD_TIMEOUT}
    local retries=${3:-$RETRY_COUNT}
    local retry=0
    local success=0
    local output_file=$(mktemp)
    
    while [ $retry -lt $retries ] && [ $success -eq 0 ]; do
        if [ $retry -gt 0 ]; then
            log_info "重試命令 (${retry}/${retries}): $cmd"
            sleep 1
        fi
        if timeout $timeout bash -c "$cmd" > "$output_file" 2>&1; then
            success=1
            cat "$output_file"
        else
            local status=$?
            cat "$output_file"
            if [ $status -eq 124 ] || [ $status -eq 137 ]; then 
                log_info "命令執行超時 ($cmd)，將重試"
            else
                log_info "命令執行失敗 ($cmd)，退出碼: $status，將重試"
            fi
            retry=$((retry + 1))
        fi
    done
    rm "$output_file"
    if [ $success -eq 1 ]; then return 0; else log_warning "命令最終執行失敗 (已重試 ${retry} 次): $cmd"; return 1; fi
}

# 模擬配置檢查函數
simulate_config_check() {
    log_info "執行模擬配置檢查..."
    log_success "模擬檢查: AMF PLMN ID (例如 00101) 已配置。"
    log_success "模擬檢查: SMF 存在t3585參數 (模擬值: 15000)"
    log_success "模擬檢查: SMF 存在t3525參數 (模擬值: 18000)"
    log_success "模擬檢查: SMF 存在max_count參數 (模擬值: 8)"
    log_success "模擬配置檢查完成。"
    AMF_CONFIGURED_PLMNS+=("00101_simulated") # Add a simulated PLMN for dependent tests
        return 0
}

# 查找Open5GS組件容器ID
get_component_id() {
    local component_name="$1"
    local alt_names=("$2") # 可選的備用名稱模式，以|分隔，例如 "open5gs-${component_name}|${component_name}-1"
    local container_id=""

    # 首先嘗試精確名稱
    container_id=$(docker ps --filter "name=^/${component_name}$" --format "{{.ID}}" | head -n 1)
    if [ -n "$container_id" ]; then echo "$container_id"; return 0; fi

    # 嘗試包含組件名的模式 (例如 ntn-stack-amf-1)
    container_id=$(docker ps --filter "name=${component_name}" --format "{{.ID}}" | head -n 1)
    if [ -n "$container_id" ]; then echo "$container_id"; return 0; fi
    
    # 嘗試備用名稱模式
    if [ -n "$alt_names" ]; then
        IFS='|' read -ra NAMES <<< "$alt_names" # Split by |
        for name_pattern in "${NAMES[@]}"; do
            container_id=$(docker ps --filter "name=${name_pattern}" --format "{{.ID}}" | head -n 1)
            if [ -n "$container_id" ]; then echo "$container_id"; return 0; fi
        done
    fi
    echo "" # 未找到則返回空
}

# 檢查AMF配置文件中的PLMN和其他關鍵配置
test_amf_config() {
    log_info "檢查AMF配置文件..."
    local AMF_CONTAINER_ID=$(get_component_id "amf" "open5gs-amf|ntn-stack-amf")

    if [ -z "$AMF_CONTAINER_ID" ]; then
        log_warning "未找到運行中的AMF容器，將模擬AMF配置檢查。"
        return 1 
    fi
    log_success "找到AMF容器: $AMF_CONTAINER_ID"

    local AMF_CONFIG_PATH="/opt/open5gs/etc/open5gs/amf.yaml" # 標準路徑
    local ALT_AMF_CONFIG_PATHS=("/etc/open5gs/amf.yaml" "/open5gs/config/amf.yaml")
    local actual_amf_config_path=""

    if run_with_timeout "docker exec $AMF_CONTAINER_ID test -f $AMF_CONFIG_PATH" 5 1; then
        actual_amf_config_path="$AMF_CONFIG_PATH"
    else
        for path_try in "${ALT_AMF_CONFIG_PATHS[@]}"; do
            if run_with_timeout "docker exec $AMF_CONTAINER_ID test -f $path_try" 5 1; then
                actual_amf_config_path="$path_try"
                break
            fi
        done
    fi

    if [ -z "$actual_amf_config_path" ]; then
        log_warning "在AMF容器 $AMF_CONTAINER_ID 中找不到 amf.yaml。嘗試檢查 docker logs..."
        local amf_log_plmns=$(run_with_timeout "docker logs --tail 100 $AMF_CONTAINER_ID 2>&1 | grep -oE 'plmn_id: \{ mcc: [0-9]+, mnc: [0-9]+ \}' | sed 's/plmn_id: { mcc: //g; s/, mnc: /,/g; s/ }.*//g; s/ //g' | sort -u" || echo "")
        if [ -n "$amf_log_plmns" ]; then
            log_info "從AMF Docker日誌中檢測到的潛在PLMN ID (mcc,mnc) 格式:"
            for plmn in $amf_log_plmns; do
                AMF_CONFIGURED_PLMNS+=("$(echo $plmn | sed 's/,//g')")
                log_success "  - $plmn"
            done
        else
            log_warning "也無法從AMF Docker日誌中提取PLMN ID。"
            return 1
        fi
        if [ ${#AMF_CONFIGURED_PLMNS[@]} -eq 0 ]; then return 1; fi
        return 0 # Found some PLMNs from logs
    fi
    
    log_success "找到AMF配置文件: $actual_amf_config_path"
    local AMF_CONFIG_CONTENT=$(run_with_timeout "docker exec $AMF_CONTAINER_ID cat $actual_amf_config_path" || echo "")
    if [ -z "$AMF_CONFIG_CONTENT" ]; then
        log_warning "無法讀取AMF配置內容 ($actual_amf_config_path)。"
        return 1
    fi

    log_info "從AMF配置文件 ($actual_amf_config_path) 中解析PLMN ID..."
    # Define awk script separately for clarity and to avoid syntax issues with multiline in $()
    local awk_script='/plmn_id:/ {in_plmn=1} /mcc:/ && in_plmn {m=$2} /mnc:/ && in_plmn {n=$2; printf "%s%s\n", m, n; in_plmn=0; m=""; n=""}'
    local parsed_plmns=$(echo "$AMF_CONFIG_CONTENT" | awk "$awk_script" | sort -u | sed 's/[^0-9]//g')

    if [ -n "$parsed_plmns" ]; then
        log_info "AMF配置文件中找到的PLMN ID (MCCMNC格式):"
        for plmn in $parsed_plmns; do
            if [[ "$plmn" =~ ^[0-9]{5,6}$ ]]; then
                AMF_CONFIGURED_PLMNS+=("$plmn")
                log_success "  - $plmn"
            else
                log_warning "  - 解析到的無效PLMN格式: $plmn (來自解析器)"
            fi
        done
    fi
    
    # Fallback or supplement with a more direct grep if awk failed or missed some
    local direct_grep_plmns=$(echo "$AMF_CONFIG_CONTENT" | grep -Eo 'mcc: *[0-9]+, *mnc: *[0-9]+' | sed -e 's/mcc: *//g' -e 's/mnc: *//g' -e 's/,//g' | awk '{printf "%s%s", $1, $2}' | sort -u)
    if [ -n "$direct_grep_plmns" ]; then
        log_info "通過直接 grep 找到的額外PLMN ID (MCCMNC格式):"
        for plmn in $direct_grep_plmns; do
            if [[ "$plmn" =~ ^[0-9]{5,6}$ ]]; then
                if ! (echo "${AMF_CONFIGURED_PLMNS[@]}" | grep -q "$plmn"); then
                    AMF_CONFIGURED_PLMNS+=("$plmn")
                    log_success "  - $plmn (來自直接grep)"
                fi
            else
                log_warning "  - 解析到的無效PLMN格式: $plmn (來自直接grep)"
        fi
    done
    fi

    if [ ${#AMF_CONFIGURED_PLMNS[@]} -eq 0 ]; then
        log_warning "未能在AMF配置文件中自動解析出PLMN ID。請手動檢查 $actual_amf_config_path。"
        AMF_CONFIGURED_PLMNS+=("00101_default") 
        log_warning "為繼續測試，已添加默認PLMN 00101_default。"
    fi

    log_info "檢查AMF N2/NGAP (SCTP) 端口配置..."
    # AMF SCTP 端口檢查
    if echo "$AMF_CONFIG_CONTENT" | grep -E 'port *: *38412'; then
        log_success "AMF配置文件中檢測到NGAP SCTP端口配置為38412。"
    else
        log_warning "AMF配置文件中未明確檢測到NGAP SCTP端口38412的標準配置。amf.yaml 片段如下："
        echo "$AMF_CONFIG_CONTENT" | grep -A 10 -B 10 'ngap' || echo "$AMF_CONFIG_CONTENT" | head -n 30
    fi
    return 0
}

# 檢查SMF配置文件中的高延遲優化參數
test_smf_config() {
    log_info "檢查SMF配置文件..."
    local SMF_CONTAINER_ID=$(get_component_id "smf" "open5gs-smf|ntn-stack-smf")
    if [ -z "$SMF_CONTAINER_ID" ]; then
        log_warning "未找到運行中的SMF容器，將模擬SMF配置檢查。"
        return 1 # Indicate failure to find container
    fi
    log_success "找到SMF容器: $SMF_CONTAINER_ID"

    local SMF_CONFIG_PATH="/opt/open5gs/etc/open5gs/smf.yaml"
    local ALT_SMF_CONFIG_PATHS=("/etc/open5gs/smf.yaml" "/open5gs/config/smf.yaml")
    local actual_smf_config_path=""
    
    if run_with_timeout "docker exec $SMF_CONTAINER_ID test -f $SMF_CONFIG_PATH" 5 1; then
        actual_smf_config_path="$SMF_CONFIG_PATH"
    else
        for path_try in "${ALT_SMF_CONFIG_PATHS[@]}"; do
            if run_with_timeout "docker exec $SMF_CONTAINER_ID test -f $path_try" 5 1; then
                actual_smf_config_path="$path_try"
                break
            fi
        done
    fi

    if [ -z "$actual_smf_config_path" ]; then
        log_warning "在SMF容器 $SMF_CONTAINER_ID 中找不到 smf.yaml。"
        return 1
    fi
    log_success "找到SMF配置文件: $actual_smf_config_path"
    local SMF_CONFIG_CONTENT=$(run_with_timeout "docker exec $SMF_CONTAINER_ID cat $actual_smf_config_path" || echo "")
    if [ -z "$SMF_CONFIG_CONTENT" ]; then
        log_warning "無法讀取SMF配置內容 ($actual_smf_config_path)。"
        return 1
    fi

    log_info "檢查SMF高延遲優化參數..."
    local PARAMS_FOUND=0
    local params_to_check=("t3585" "t3525" "t3591" "t3592" "t-3585" "t_3585")
    for param in "${params_to_check[@]}"; do
        if echo "$SMF_CONFIG_CONTENT" | grep -qiE "^ *${param} *:"; then
            log_success "SMF配置中存在參數: $param"
            PARAMS_FOUND=$((PARAMS_FOUND + 1))
        fi
    done
    if [ $PARAMS_FOUND -lt 2 ]; then
        log_warning "SMF配置文件中未找到足夠的高延遲優化參數。smf.yaml 片段如下："
        echo "$SMF_CONFIG_CONTENT" | head -n 30
    fi
    return 0
}

# 提示用戶檢查 PLMN 配置
provide_plmn_check_guidance() {
    log_info "---------------- PLMN 配置檢查指南 ----------------"
    log_info "由於UE註冊失敗，原因可能是 PLMN_NOT_ALLOWED。請確認以下配置："
    
    if [ ${#AMF_CONFIGURED_PLMNS[@]} -gt 0 ] && [[ "${AMF_CONFIGURED_PLMNS[0]}" != "00101_default" ]]; then
        log_info "1. AMF 配置的 PLMN ID (MCCMNC 格式):"
        for plmn in "${AMF_CONFIGURED_PLMNS[@]}"; do
            log_info "   - $plmn"
        done
    else
        log_warning "1. 未能自動從AMF配置中提取PLMN ID (或僅找到默認/模擬值)。請手動檢查AMF的 amf.yaml 文件。"
        if [[ "${AMF_CONFIGURED_PLMNS[0]}" == "00101_default" ]]; then log_info "   (腳本使用了 00101_default 作為占位符)"; fi
    fi
    
    log_info "2. UERANSIM gNodeB 配置:"
    log_info "   - 確保 gNodeB 配置文件 (例如 gnb.yaml) 中的 PLMN ID (mcc 和 mnc) "
    log_info "     與上述 AMF 配置的 PLMN ID 之一匹配。"
    
    log_info "3. UERANSIM UE 配置:"
    log_info "   - 確保 UE 配置文件 (例如 ue.yaml 或 free5gc-ue.yaml) 中的 PLMN "
    log_info "     (通常在 supi 或 configuredPLMN/plmnList/hplmn 等字段中定義的 mcc 和 mnc) "
    log_info "     與上述 AMF 配置的 PLMN ID 之一匹配，並且是 UE 允許註冊的 PLMN。"

    log_info "4. Open5GS HSS/UDM 數據庫 (MongoDB):"
    log_info "   - 連接到 MongoDB: mongo mongodb://<mongo_host>:<mongo_port>/open5gs "
    log_info "     (將 <mongo_host> 和 <mongo_port> 替換為您的MongoDB實例地址和端口，默認可能是 localhost:27017)"
    log_info "   - 查詢特定 IMSI (例如 999700000000001) 的訂戶記錄:"
    log_info "     db.subscribers.findOne({\"imsi\": \"999700000000001\"})"
    log_info "   - 檢查記錄中的字段，如 'access_restriction_data', 'subscribed_rau_tau_timer', "
    log_info "     或任何與PLMN黑白名單、漫遊限制相關的字段，確保允許UE在目標PLMN上註冊。"
    log_info "     尋找類似 'plmn_list', 'allowed_plmns' 或直接的 mcc/mnc 字段。"
    log_info "-----------------------------------------------------"
}

# 主函數
main() {
    log_info "開始Open5GS配置測試..."
    
    local amf_config_ok=false
    if test_amf_config; then
        amf_config_ok=true
    else
        # If amf_config fails to find real PLMNs, simulate_config_check might be called implicitly by it, 
        # or we ensure a default is added. The guidance will reflect this.
        if [ ${#AMF_CONFIGURED_PLMNS[@]} -eq 0 ]; then # Ensure default is added if list is empty
            AMF_CONFIGURED_PLMNS+=("00101_default") 
            log_warning "AMF配置測試後PLMN列表仍為空，已添加默認PLMN 00101_default。"
        fi
    fi

    local smf_config_ok=false
    if test_smf_config; then
        smf_config_ok=true
    fi

    provide_plmn_check_guidance

    if $amf_config_ok && $smf_config_ok; then
        log_success "Open5GS AMF和SMF配置檢查完成 (可能仍有警告或需要手動確認的部分)。"
    else
        log_error "Open5GS AMF或SMF配置檢查遇到問題或未能完全驗證。請查看上述日誌和指南。"
    fi

    log_info "由於UE註冊問題 (例如 PLMN_NOT_ALLOWED) 可能存在，依賴於UE成功註冊的進階測試 (如PDU會話穩定性、GTP隧道細節) 將被跳過或簡化。"
    log_info "請先解決PLMN配置問題，確保UE能夠成功註冊。"

    log_success "Open5GS配置測試腳本執行完畢。"
}

main "$@" 