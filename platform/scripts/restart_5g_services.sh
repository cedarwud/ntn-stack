#!/bin/bash

# 此腳本用於重啟關鍵的5G核心網組件和UE
# 作者：GitHub Copilot
# 創建日期：2025-05-23

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

# 重新配置並重啟服務
restart_services() {
    log_info "準備重啟核心網服務..."
    
    log_info "1. 應用配置文件更新..."
    # 假設配置文件已經更新
    
    log_info "2. 重啟AMF服務..."
    docker restart amf
    
    log_info "3. 重啟UDM服務..."
    docker restart udm
    
    log_info "4. 重啟UDR服務..."
    docker restart udr
    
    log_info "5. 重啟AUSF服務..."
    docker restart ausf
    
    log_info "6. 等待10秒讓核心網服務穩定..."
    sleep 10
    
    log_info "7. 重啟gNodeB服務..."
    docker restart gnb1
    docker restart gnb2
    
    log_info "8. 等待5秒讓gNodeB服務穩定..."
    sleep 5
    
    log_info "9. 重啟UE服務..."
    # 獲取ues容器名稱
    UES1_CONTAINER=$(docker ps -q --filter name=ues1)
    if [ -n "$UES1_CONTAINER" ]; then
        docker restart $UES1_CONTAINER
        log_success "已重啟ues1容器: $UES1_CONTAINER"
    else
        log_warning "找不到ues1容器"
    fi
    
    # 有可能有多個UE容器
    UES2_CONTAINER=$(docker ps -q --filter name=ues2)
    if [ -n "$UES2_CONTAINER" ]; then
        docker restart $UES2_CONTAINER
        log_success "已重啟ues2容器: $UES2_CONTAINER"
    else
        log_warning "找不到ues2容器或不需要重啟ues2"
    fi
    
    log_success "所有服務已重啟"
}

# 檢查UE註冊狀態
check_ue_status() {
    log_info "檢查UE註冊狀態..."
    sleep 15  # 給UE一些時間來註冊
    
    UES1_CONTAINER=$(docker ps -q --filter name=ues1)
    if [ -n "$UES1_CONTAINER" ]; then
        log_info "檢查ues1容器中的UE狀態..."
        docker exec $UES1_CONTAINER nr-cli -l
        
        # 檢查第一個IMSI的狀態
        log_info "檢查IMSI-999700000000001的狀態..."
        docker exec $UES1_CONTAINER nr-cli imsi-999700000000001 -e status || log_warning "無法檢查IMSI-999700000000001的狀態"
    else
        log_warning "找不到ues1容器，無法檢查UE狀態"
    fi
}

# 主函數
main() {
    log_info "開始執行5G核心網和UE重啟和配置更新..."
    
    # 執行訂閱者重置和註冊
    log_info "執行訂閱者註冊修復腳本..."
    /home/sat/ntn-stack/platform/scripts/fix_ue_registration.sh
    
    # 重啟服務
    restart_services
    
    # 檢查UE狀態
    check_ue_status
    
    log_success "腳本執行完成，請檢查UE註冊狀態"
}

# 執行主函數
main
