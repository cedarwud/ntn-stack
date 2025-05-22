#!/bin/bash

# UERANSIM配置應用腳本
# 此腳本用於將生成的配置文件應用到UERANSIM容器

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 腳本路徑常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# 默認容器名稱
DEFAULT_GNB="gnb1"

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
    echo "用法: $0 [-g <gNodeB配置文件>] [-u <UE配置文件>] [-c <容器名稱>]"
    echo "  -g 指定gNodeB配置文件路徑"
    echo "  -u 指定UE配置文件路徑"
    echo "  -c 指定容器名稱 (默認: gnb1)"
    echo "  -h 顯示此幫助信息"
}

# 解析命令行參數
parse_args() {
    while getopts ":g:u:c:h" opt; do
        case $opt in
            g)
                GNB_CONFIG="$OPTARG"
                ;;
            u)
                UE_CONFIG="$OPTARG"
                ;;
            c)
                CONTAINER_NAME="$OPTARG"
                ;;
            h)
                show_help
                exit 0
                ;;
            \?)
                log_error "無效的選項: -$OPTARG"
                show_help
                exit 1
                ;;
            :)
                log_error "選項 -$OPTARG 需要參數"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 設置默認容器名稱
    if [ -z "$CONTAINER_NAME" ]; then
        CONTAINER_NAME="$DEFAULT_GNB"
    fi
}

# 應用gNodeB配置
apply_gnb_config() {
    if [ -z "$GNB_CONFIG" ]; then
        log_warning "未指定gNodeB配置文件"
        return 0
    fi
    
    log_info "正在應用gNodeB配置..."
    
    if [ ! -f "$GNB_CONFIG" ]; then
        log_error "gNodeB配置文件不存在: $GNB_CONFIG"
        return 1
    fi
    
    # 確保容器在運行
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        log_error "容器 $CONTAINER_NAME 未運行"
        return 1
    fi
    
    # 獲取配置文件名
    local config_name=$(basename "$GNB_CONFIG")
    
    # 複製配置文件到容器內
    log_info "複製配置到容器 $CONTAINER_NAME..."
    docker cp "$GNB_CONFIG" "$CONTAINER_NAME:/tmp/$config_name"
    
    # 應用配置
    log_info "重啟UERANSIM服務使用新配置..."
    docker exec "$CONTAINER_NAME" sh -c "cp /tmp/$config_name /etc/ueransim/gnb.yaml"
    docker restart "$CONTAINER_NAME"
    
    # 等待服務重啟
    sleep 5
    if docker ps | grep -q "$CONTAINER_NAME"; then
        log_success "gNodeB配置已應用並重啟服務"
    else
        log_error "容器 $CONTAINER_NAME 未能成功重啟"
        return 1
    fi
    
    return 0
}

# 應用UE配置
apply_ue_config() {
    if [ -z "$UE_CONFIG" ]; then
        log_warning "未指定UE配置文件"
        return 0
    fi
    
    log_info "正在應用UE配置..."
    
    if [ ! -f "$UE_CONFIG" ]; then
        log_error "UE配置文件不存在: $UE_CONFIG"
        return 1
    fi
    
    # 獲取UE容器名稱
    local UE_CONTAINER="${CONTAINER_NAME/gnb/ue}"
    
    # 確保容器在運行
    if ! docker ps | grep -q "$UE_CONTAINER"; then
        log_error "UE容器 $UE_CONTAINER 未運行"
        return 1
    fi
    
    # 獲取配置文件名
    local config_name=$(basename "$UE_CONFIG")
    
    # 複製配置文件到容器內
    log_info "複製配置到UE容器 $UE_CONTAINER..."
    docker cp "$UE_CONFIG" "$UE_CONTAINER:/tmp/$config_name"
    
    # 應用配置
    log_info "重啟UE服務使用新配置..."
    docker exec "$UE_CONTAINER" sh -c "cp /tmp/$config_name /etc/ueransim/ue.yaml"
    docker restart "$UE_CONTAINER"
    
    # 等待服務重啟
    sleep 5
    if docker ps | grep -q "$UE_CONTAINER"; then
        log_success "UE配置已應用並重啟服務"
    else
        log_error "UE容器 $UE_CONTAINER 未能成功重啟"
        return 1
    fi
    
    return 0
}

# 主函數
main() {
    parse_args "$@"
    
    log_info "開始應用UERANSIM配置..."
    log_info "gNodeB配置: $GNB_CONFIG"
    log_info "UE配置: $UE_CONFIG"
    log_info "目標容器: $CONTAINER_NAME"
    
    # 應用配置
    apply_gnb_config || return 1
    apply_ue_config || return 1
    
    log_success "UERANSIM配置應用完成"
    return 0
}

# 執行主函數
main "$@"
exit $? 