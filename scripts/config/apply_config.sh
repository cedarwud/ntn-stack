#!/bin/bash

# 配置應用腳本 - 將生成的UERANSIM配置文件應用到容器中

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 顯示幫助信息
show_help() {
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -g, --gnb-config FILE    指定gNodeB配置文件"
    echo "  -u, --ue-config FILE     指定UE配置文件"
    echo "  -c, --container NAME     指定容器名稱 (默認: gnb1 和 ntn-stack-ues1-1)"
    echo "  -h, --help               顯示幫助信息"
    echo ""
    echo "示例:"
    echo "  $0 -g config/generated/gnb_gnb1_latest.yaml -u config/generated/ue_ue1_latest.yaml"
    echo "  $0 -g config/ueransim/gnb_leo.yaml -u config/ueransim/ue_leo.yaml -c custom-gnb"
    exit 0
}

# 檢查容器狀態
check_container() {
    local container_name=$1
    if ! docker ps -q -f name="$container_name" | grep -q .; then
        log_error "$container_name容器未運行"
        return 1
    fi
    return 0
}

# 應用gNodeB配置
apply_gnb_config() {
    local config_file=$1
    local container_name=$2

    if [ ! -f "$config_file" ]; then
        log_error "gNodeB配置文件不存在: $config_file"
        return 1
    fi

    if ! check_container "$container_name"; then
        return 1
    fi

    # 創建臨時目錄
    local temp_dir=$(mktemp -d)
    cp "$config_file" "$temp_dir/gnb.yaml"

    # 將配置複製到容器
    docker cp "$temp_dir/gnb.yaml" "$container_name:/etc/nr-gnb.yaml"
    if [ $? -ne 0 ]; then
        log_error "無法將配置複製到容器 $container_name"
        rm -rf "$temp_dir"
        return 1
    fi

    # 重啟服務
    docker restart "$container_name"
    if [ $? -ne 0 ]; then
        log_error "無法重啟容器 $container_name"
        rm -rf "$temp_dir"
        return 1
    fi

    # 清理臨時文件
    rm -rf "$temp_dir"
    log_success "已成功將gNodeB配置應用到 $container_name"
    return 0
}

# 應用UE配置
apply_ue_config() {
    local config_file=$1
    local container_name=$2

    if [ ! -f "$config_file" ]; then
        log_error "UE配置文件不存在: $config_file"
        return 1
    fi

    if ! check_container "$container_name"; then
        return 1
    fi

    # 創建臨時目錄
    local temp_dir=$(mktemp -d)
    cp "$config_file" "$temp_dir/ue.yaml"

    # 將配置複製到容器
    docker cp "$temp_dir/ue.yaml" "$container_name:/etc/nr-ue.yaml"
    if [ $? -ne 0 ]; then
        log_error "無法將配置複製到容器 $container_name"
        rm -rf "$temp_dir"
        return 1
    fi

    # 重啟服務
    docker restart "$container_name"
    if [ $? -ne 0 ]; then
        log_error "無法重啟容器 $container_name"
        rm -rf "$temp_dir"
        return 1
    fi

    # 清理臨時文件
    rm -rf "$temp_dir"
    log_success "已成功將UE配置應用到 $container_name"
    return 0
}

# 主函數
main() {
    log_info "UERANSIM配置應用腳本開始執行..."

    # 默認值
    GNB_CONFIG=""
    UE_CONFIG=""
    GNB_CONTAINER="gnb1"
    UE_CONTAINER="ntn-stack-ues1-1"

    # 解析命令行參數
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -g|--gnb-config)
                GNB_CONFIG="$2"
                shift 2
                ;;
            -u|--ue-config)
                UE_CONFIG="$2"
                shift 2
                ;;
            -c|--container)
                GNB_CONTAINER="$2"
                UE_CONTAINER="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                ;;
            *)
                log_error "未知選項: $1"
                show_help
                ;;
        esac
    done

    # 應用配置
    local success=true

    # 應用gNodeB配置
    if [ -n "$GNB_CONFIG" ]; then
        apply_gnb_config "$GNB_CONFIG" "$GNB_CONTAINER" || success=false
    fi

    # 應用UE配置
    if [ -n "$UE_CONFIG" ]; then
        apply_ue_config "$UE_CONFIG" "$UE_CONTAINER" || success=false
    fi

    # 顯示結果
    if [ "$success" = true ]; then
        log_success "配置應用完成"
    else
        log_error "配置應用過程中出現錯誤"
        exit 1
    fi
}

# 執行主函數
main "$@"
