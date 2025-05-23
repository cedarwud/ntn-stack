#!/bin/bash

# 此腳本用於初始化系統並解決UE註冊問題
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

# 確保系統啟動
init_system() {
    log_info "確認系統服務啟動狀態..."
    
    NETWORK_SERVICES=("mongo" "amf" "ausf" "bsf" "nrf" "nssf" "pcf" "scp" "smf" "udm" "udr" "upf" "gnb1" "gnb2")
    
    for service in "${NETWORK_SERVICES[@]}"; do
        if docker ps --filter "name=$service" | grep -q "$service"; then
            log_success "$service 服務已運行"
        else
            log_warning "$service 服務未運行，嘗試啟動..."
            docker-compose up -d $service
            sleep 2
            if docker ps --filter "name=$service" | grep -q "$service"; then
                log_success "$service 服務已成功啟動"
            else
                log_error "$service 服務啟動失敗"
            fi
        fi
    done
}

# 重新註冊訂閱者信息
reinit_subscribers() {
    log_info "重新註冊訂閱者信息..."
    
    # 嘗試直接與MongoDB連接
    if ! docker exec -it mongo mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        log_error "MongoDB不可用，無法重新註冊訂閱者"
        return 1
    fi
    
    log_info "清除現有訂閱者數據..."
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl reset
    
    log_info "添加新訂閱者..."
    # 使用與ues1和ues2中相同的KEY和OPC
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl add 999700000000001 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl add 999700000000002 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl add 999700000000003 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl add 999700000000011 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl add 999700000000012 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl add 999700000000013 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA
    
    log_info "驗證訂閱者註冊..."
    docker run --rm --net=ntn-stack_open5gs-net -e DB_URI=mongodb://mongo/open5gs gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl showfiltered
    
    log_success "訂閱者重新註冊完成"
}

# 重啟UE容器
restart_ues() {
    log_info "重啟UE容器，應用新配置..."
    
    log_info "停止並移除ues1容器..."
    docker-compose stop ues1
    docker-compose rm -f ues1
    
    log_info "停止並移除ues2容器..."
    docker-compose stop ues2
    docker-compose rm -f ues2
    
    log_info "啟動更新後的ues1容器..."
    docker-compose up -d ues1
    
    log_info "啟動更新後的ues2容器..."
    docker-compose up -d ues2
    
    log_success "UE容器已重新啟動"
}

# 檢查UE註冊狀態
check_ue_status() {
    log_info "等待UE啟動和連接 (30秒)..."
    sleep 30
    
    log_info "檢查ues1註冊狀態..."
    if docker exec -it $(docker ps --filter name=ues1 -q) nr-cli imsi-999700000000001 -e status | grep -q "5GMM-REGISTERED"; then
        log_success "ues1 (IMSI-999700000000001) 已成功註冊到網絡"
        docker exec -it $(docker ps --filter name=ues1 -q) nr-cli imsi-999700000000001 -e status | head -20
    else
        log_warning "ues1 (IMSI-999700000000001) 未註冊到網絡"
        docker exec -it $(docker ps --filter name=ues1 -q) nr-cli imsi-999700000000001 -e status
    fi
    
    log_info "檢查PDU會話狀態..."
    docker exec -it $(docker ps --filter name=ues1 -q) nr-cli imsi-999700000000001 -e ps-list
}

# 主函數
main() {
    log_info "開始系統初始化和UE註冊修復流程..."
    
    init_system
    reinit_subscribers
    restart_ues
    check_ue_status
    
    log_success "系統初始化和UE註冊修復流程完成"
    log_info "如果仍然有問題，請檢查docker日誌：docker logs \$(docker ps -qf name=ues1) --tail 100"
}

# 執行主函數
main "$@"
