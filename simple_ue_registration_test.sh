#!/bin/bash

# 腳本：simple_ue_registration_test.sh
# 用於測試 Open5GS 和 UERANSIM 的 UE 註冊 (已調整為使用 platform 配置)

# --- 配置 ---
BASE_DIR=$(pwd) # 假設在 ntn-stack 目錄下執行

# 更新為 platform 路徑
PLATFORM_DIR="$BASE_DIR/platform"
OPEN5GS_CONFIG_DIR="$PLATFORM_DIR/config/open5gs"
UERANSIM_CONFIG_DIR="$PLATFORM_DIR/config/ueransim"
SCRIPTS_DIR="$PLATFORM_DIR/scripts"

# 假設 platform 使用類似的 docker-compose 結構
# 您可能需要確認這些檔案的確切名稱和位置
NGC_COMPOSE_FILE="$UERANSIM_CONFIG_DIR/ngc.yaml" # 假設核心網路的 compose 檔在此
GNB_COMPOSE_FILE="$UERANSIM_CONFIG_DIR/gnb1.yaml" # 假設 RAN/UE 的 compose 檔在此

# 更新為 platform 的註冊腳本路徑
REGISTER_SCRIPT="$SCRIPTS_DIR/register_subscriber.sh/register_subscriber.sh" # 假設腳本在該目錄下且名為 register_subscriber.sh

# UE IMSI (移除 'imsi-' 前綴，用於 nr-cli)
# 根據您的日誌，IMSI 是 999700000000001, 002, 003。我們將繼續測試 001，但請注意其日誌顯示問題。
TEST_IMSI_FOR_NR_CLI="999700000000001"
# 用於日誌過濾的 IMSI (可以包含前綴，如果日誌中是這樣顯示的)
TEST_IMSI_FOR_LOGS="imsi-999700000000001"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- 函數 ---
log_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

cleanup_docker() {
    log_info "清理舊的 Docker 容器 (如果存在)..."
    docker compose -f "$GNB_COMPOSE_FILE" down --remove-orphans 2>/dev/null
    docker compose -f "$NGC_COMPOSE_FILE" down -v --remove-orphans 2>/dev/null # -v 移除 volume
    log_success "舊容器和相關 volume 已清理。"
}

start_core_network() {
    log_info "啟動 Open5GS 核心網路 (NGC)..."
    # 確保 docker-compose 指令在正確的目錄下執行，或者 NGC_COMPOSE_FILE 使用絕對路徑
    # 假設 NGC_COMPOSE_FILE 包含相對於 $BASE_DIR 的路徑，或者是一個絕對路徑
    docker compose -f "$NGC_COMPOSE_FILE" up -d
    if [ $? -ne 0 ]; then
        log_error "啟動 Open5GS 核心網路失敗。"
        exit 1
    fi
    log_success "Open5GS 核心網路已啟動。"

    log_info "嘗試明確重新啟動 AMF 服務以確保配置載入..."
    # 假設 AMF 服務在 $NGC_COMPOSE_FILE 中被命名為 'amf'
    docker compose -f "$NGC_COMPOSE_FILE" restart amf
    if [ $? -ne 0 ]; then
        log_warning "重新啟動 AMF 服務失敗，但仍繼續測試..."
    else
        log_success "AMF 服務已重新啟動。"
    fi

    log_info "等待核心網路組件穩定 (45 秒)..."
    sleep 45
}

register_subscribers() {
    log_info "註冊/更新用戶 (IMSI: $TEST_IMSI_FOR_NR_CLI) 使用 platform 腳本..."
    if [ ! -f "$REGISTER_SCRIPT" ]; then
        log_error "找不到註冊腳本: $REGISTER_SCRIPT"
        log_warning "請確保 $REGISTER_SCRIPT 存在並且可執行。"
        log_warning "如果沒有此腳本或腳本不正確，SQN 和用戶配置問題很可能持續存在。"
        return 1 # 改為返回錯誤碼，讓主流程決定是否繼續
    fi

    chmod +x "$REGISTER_SCRIPT"
    # 執行註冊腳本。
    # 注意：platform 的註冊腳本可能需要不同的執行方式或環境變數
    # 例如，它可能不需要在特定目錄下執行，或者依賴於 platform 環境中的其他配置
    # 此處假設它可以直接執行
    "$REGISTER_SCRIPT" # 直接執行，如果需要特定目錄，請修改
    if [ $? -ne 0 ]; then
        log_error "執行 platform 用戶註冊腳本失敗。這可能會導致認證問題。"
        # 即使失敗也繼續，以便觀察後續行為
    else
        log_success "Platform 用戶註冊腳本已執行。"
    fi
    # 短暫等待資料庫同步
    sleep 5
}

start_ran_ue() {
    log_info "啟動 UERANSIM gNodeB 和 UE (gnb1)..."
    docker compose -f "$GNB_COMPOSE_FILE" up -d
    if [ $? -ne 0 ]; then
        log_error "啟動 UERANSIM gNodeB 和 UE 失敗。"
        exit 1
    fi
    log_success "UERANSIM gNodeB 和 UE 已啟動。"
    log_info "等待 UE 嘗試註冊 (60 秒)..."
    sleep 60
}

check_ue_status() {
    local ue_service_name="ues1" # 根據 gnb1.yaml 中的 ueransim UE 服務名稱
    UE_CONTAINER_ID=$(docker compose -f "$GNB_COMPOSE_FILE" ps -q "$ue_service_name")

    if [ -z "$UE_CONTAINER_ID" ]; then
        log_error "找不到 UE 容器 (服務名: $ue_service_name)。請檢查 'docker compose -f $GNB_COMPOSE_FILE ps'"
        return 1
    fi
    log_info "UE 容器 ID: $UE_CONTAINER_ID"

    log_info "檢查 UE (IMSI: $TEST_IMSI_FOR_NR_CLI) 註冊狀態..."
    NR_CLI_PATH_CHECK=$(docker exec "$UE_CONTAINER_ID" sh -c "command -v nr-cli || echo ''")
    if [ -z "$NR_CLI_PATH_CHECK" ]; then
        log_error "nr-cli 在 UE 容器 $UE_CONTAINER_ID 中找不到。"
        return 1
    fi
    log_info "在 UE 容器 $UE_CONTAINER_ID 中找到 nr-cli 於 $NR_CLI_PATH_CHECK"

    log_info "-----------------------------------------------------"
    log_info "顯示來自 UE 容器的 nr-cli --help 輸出:"
    NR_CLI_HELP_OUTPUT=$(docker exec "$UE_CONTAINER_ID" nr-cli --help 2>&1)
    echo "${NR_CLI_HELP_OUTPUT}"
    log_info "-----------------------------------------------------"

    log_info "嘗試使用 'nr-cli --dump' 列出所有 UE 和 gNB 節點:"
    NR_CLI_DUMP_OUTPUT=$(docker exec "$UE_CONTAINER_ID" "$NR_CLI_PATH_CHECK" --dump 2>&1)
    echo "${NR_CLI_DUMP_OUTPUT}"
    if [[ "$NR_CLI_DUMP_OUTPUT" == *"imsi-${TEST_IMSI_FOR_NR_CLI}"* ]]; then
        log_success "nr-cli --dump 輸出中找到了測試 UE (imsi-${TEST_IMSI_FOR_NR_CLI})。"
    elif [[ "$NR_CLI_DUMP_OUTPUT" == *"ERROR"* || "$NR_CLI_DUMP_OUTPUT" == *"Option not recognized"* ]]; then
        log_warning "nr-cli --dump 命令執行時發生錯誤或無法識別。"
        log_info "nr-cli --dump 輸出:\\n${NR_CLI_DUMP_OUTPUT}"
    else
        log_warning "nr-cli --dump 輸出中未找到測試 UE (imsi-${TEST_IMSI_FOR_NR_CLI})。可能所有 UE 都已註銷或 --dump 未按預期工作。"
        log_info "nr-cli --dump 輸出:\\n${NR_CLI_DUMP_OUTPUT}"
    fi
    log_info "-----------------------------------------------------"

    local cli_ue_name="imsi-${TEST_IMSI_FOR_NR_CLI}"
    log_info "嘗試使用 'nr-cli ${cli_ue_name} -e status' 獲取 UE 狀態..."
    # 清除舊的輸出，以防命令失敗且變數未被覆寫
    UE_STATUS_OUTPUT=""
    UE_STATUS_OUTPUT=$(docker exec "$UE_CONTAINER_ID" "$NR_CLI_PATH_CHECK" "${cli_ue_name}" -e status 2>&1)
    log_info "UE (${cli_ue_name}) 狀態 (來自 nr-cli -e status):"
    echo "$UE_STATUS_OUTPUT"

    # 檢查 mm-state 是否為 MM-REGISTERED/NORMAL-SERVICE 或類似的成功狀態
    # 或者 rm-state 是否為 RM-REGISTERED
    if echo "$UE_STATUS_OUTPUT" | grep -iq "mm-state: MM-REGISTERED/NORMAL-SERVICE" || \
       echo "$UE_STATUS_OUTPUT" | grep -iq "rm-state: RM-REGISTERED"; then
        log_success "UE (${cli_ue_name}) 已成功註冊 (根據 nr-cli -e status 的 mm-state/rm-state)！"
    elif echo "$UE_STATUS_OUTPUT" | grep -q "ERROR: Only one node name is expected"; then
        log_error "nr-cli ${cli_ue_name} -e status 仍然回報 'ERROR: Only one node name is expected'。"
        log_info "這可能表示 '-e status' 不是預期的用法，或者 'status' 命令本身在此上下文中不起作用。"
        log_info "重要：UE 的內部日誌和 'nr-cli --dump' 的輸出 (如果 UE 在其中列出) 仍然是註冊狀態的主要指標。"
    elif echo "$UE_STATUS_OUTPUT" | grep -iq "not found\\|no such node"; then
        log_error "nr-cli 回報找不到節點 '${cli_ue_name}'。請檢查 'nr-cli --dump' 的輸出以確認正確的 UE 名稱。"
    elif echo "$UE_STATUS_OUTPUT" | grep -iq "Unknown command"; then
        log_error "nr-cli 回報 'status' 為未知命令，即使使用了 '-e'。nr-cli 的此版本可能不支援以這種方式查詢狀態。"
        log_info "請再次參考 'nr-cli --help' 或嘗試互動模式：docker exec -it $UE_CONTAINER_ID $NR_CLI_PATH_CHECK ${cli_ue_name}"
    else
        log_error "UE (${cli_ue_name}) 未註冊或狀態未知 (根據 nr-cli -e status)。請檢查上面的 nr-cli 輸出以及 UE/AMF 日誌。"
        log_info "再次強調，UE 內部日誌和 'nr-cli --dump' 的輸出可能顯示不同的情況。"
    fi
}

show_logs() {
    local ue_service_name="ues1"
    UE_CONTAINER_ID=$(docker compose -f "$GNB_COMPOSE_FILE" ps -q "$ue_service_name")
    AMF_CONTAINER_ID=$(docker compose -f "$NGC_COMPOSE_FILE" ps -q amf)

    if [ ! -z "$UE_CONTAINER_ID" ]; then
        log_info "顯示 UE ($TEST_IMSI_FOR_LOGS) 日誌 (最近 100 行):"
        docker logs --tail 100 "$UE_CONTAINER_ID" # 顯示所有日誌，因為過濾可能丟失上下文
    else
        log_error "無法獲取 UE 容器 ID 以顯示日誌。"
    fi

    if [ ! -z "$AMF_CONTAINER_ID" ]; then
        log_info "AMF 容器 ID: $AMF_CONTAINER_ID"
        log_info "顯示 AMF 日誌 (最近 100 行，可嘗試過濾 IMSI $TEST_IMSI_FOR_LOGS 或錯誤關鍵字):"
        # docker logs --tail 100 "$AMF_CONTAINER_ID" 2>&1 | grep -E "$TEST_IMSI_FOR_LOGS|Authentication failure|SQN|PLMN|Reject" || docker logs --tail 100 "$AMF_CONTAINER_ID"
        docker logs --tail 100 "$AMF_CONTAINER_ID" # 顯示所有日誌
    else
        log_error "無法獲取 AMF 容器 ID 以顯示日誌。"
    fi
}

# --- 主流程 ---
# 檢查必要文件
if [ ! -f "$NGC_COMPOSE_FILE" ] || [ ! -f "$GNB_COMPOSE_FILE" ]; then
    log_error "找不到必要的 platform docker-compose 文件 ($NGC_COMPOSE_FILE or $GNB_COMPOSE_FILE)。"
    log_error "請確保您在正確的目錄下執行此腳本，並且 platform 的路徑和檔案名稱正確。"
    exit 1
fi


cleanup_docker
start_core_network
register_subscribers
if [ $? -ne 0 ]; then
    log_warning "用戶註冊步驟遇到問題，但仍繼續測試..."
fi
start_ran_ue
check_ue_status
show_logs

log_info "測試完成 (使用 platform 配置)。"
log_info "如果 UE 仍然無法註冊，請仔細檢查以下幾點："
log_info "1. '$REGISTER_SCRIPT' 的內容和執行結果，確保它正確更新了 MongoDB 中的用戶數據 (IMSI, K, OPC, SQN)。"
log_info "   特別是 SQN 應該被重設為一個初始值 (例如全零 '000000000000')。"
log_info "2. Platform UERANSIM gNodeB 和 UE 的配置文件 ($GNB_COMPOSE_FILE 內部或其引用的文件) 中的 PLMN ID (MCC/MNC) 是否與核心網路 (AMF) 和用戶數據庫中的配置一致。"
log_info "3. Platform Open5GS AMF 的配置文件 (例如 $OPEN5GS_CONFIG_DIR/amf.yaml) 是否允許此 PLMN ID。"
log_info "4. MongoDB (open5gs.subscribers collection) 中的用戶條目是否正確，'slice' 配置是否正確並與允許的 PLMN 相關聯。"
log_info "如需手動清理，請執行:"
echo "docker compose -f \\"$GNB_COMPOSE_FILE\\" down --remove-orphans"
echo "docker compose -f \\"$NGC_COMPOSE_FILE\\" down -v --remove-orphans"
