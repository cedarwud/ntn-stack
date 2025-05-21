#!/bin/bash

# UE 自動恢復腳本
# 此腳本監控 UE 容器的狀態並自動修復連接問題
# 可以作為後台服務運行，提供自動恢復機制

set -e

UE_CONTAINER="ntn-stack-ues1-1"
IMSI_LIST=("imsi-999700000000001" "imsi-999700000000002" "imsi-999700000000003")
UPF_IP="10.45.0.1"
SUBNET="10.45.0.0/16"
PROXY_CONTAINER="ntn-proxy"
CHECK_INTERVAL=60  # 檢查間隔(秒)

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 檢查容器是否運行
check_container_running() {
    local container=$1
    docker ps --format '{{.Names}}' | grep -q "^$container$"
    return $?
}

# 重啟/恢復 UE 容器
restart_ue_container() {
    log "重啟 UE 容器..."
    
    # 強制移除可能崩潰的容器
    docker rm -f $UE_CONTAINER 2>/dev/null || true
    sleep 2
    
    # 重新啟動 UE 容器
    log "啟動新的 UE 容器..."
    docker compose up -d ues1
    
    # 等待容器啟動 (最多30秒)
    local max_wait=30
    local count=0
    log "等待 UE 容器啟動..."
    while [ $count -lt $max_wait ]; do
        if check_container_running $UE_CONTAINER; then
            log "UE 容器已啟動，等待15秒確保服務初始化..."
            sleep 15
            break
        fi
        sleep 1
        count=$((count+1))
        if [ $count -eq $max_wait ]; then
            log "等待 UE 容器啟動超時"
            return 1
        fi
    done
    
    log "UE 容器重啟成功"
    return 0
}

# 優化 UE 網絡設置
optimize_ue_network() {
    log "優化 UE 網絡設置..."
    
    # 確保 IP 轉發開啟
    docker exec $UE_CONTAINER sysctl -w net.ipv4.ip_forward=1 2>/dev/null || log "無法設置 IP 轉發"
    
    # 禁用 rp_filter
    docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || log "無法禁用 rp_filter (all)"
    docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0 2>/dev/null || log "無法禁用 rp_filter (default)"
    docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0 2>/dev/null || log "無法禁用 rp_filter (lo)"
    
    # 優化 TCP 參數
    docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216" 2>/dev/null || log "無法設置 TCP 接收緩衝區"
    docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216" 2>/dev/null || log "無法設置 TCP 發送緩衝區"
    docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_window_scaling=1 2>/dev/null || log "無法啟用 TCP 窗口縮放"
    docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_timestamps=1 2>/dev/null || log "無法啟用 TCP 時間戳"
    docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_sack=1 2>/dev/null || log "無法啟用 TCP 選擇性確認"
    docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_congestion_control=cubic 2>/dev/null || log "無法設置 TCP 擁擠控制"
    
    # 設置 DNS
    docker exec $UE_CONTAINER bash -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf" 2>/dev/null || log "無法設置 DNS (8.8.8.8)"
    docker exec $UE_CONTAINER bash -c "echo 'nameserver 1.1.1.1' >> /etc/resolv.conf" 2>/dev/null || log "無法設置 DNS (1.1.1.1)"
    
    # 添加 ntn-proxy 到 hosts 文件
    PROXY_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $PROXY_CONTAINER 2>/dev/null || echo "")
    if [ -n "$PROXY_IP" ]; then
        docker exec $UE_CONTAINER bash -c "grep -q $PROXY_CONTAINER /etc/hosts || echo '$PROXY_IP $PROXY_CONTAINER' >> /etc/hosts" 2>/dev/null || log "無法添加 ntn-proxy 到 hosts 文件"
    else
        log "警告: 無法獲取 proxy 容器 IP"
    fi
    
    log "UE 網絡設置優化完成"
}

# 檢查 PDU 會話狀態
check_pdu_session() {
    local imsi=$1
    local status_output
    
    log "檢查 $imsi 的 PDU 會話狀態..."
    
    # 判斷 UE 狀態
    status_output=$(docker exec $UE_CONTAINER nr-cli $imsi -e "status" 2>/dev/null)
    echo "$status_output" | grep -q "CM-CONNECTED" && {
        log "$imsi 已連接到網絡"
        return 0
    }
    
    # 檢查是否已註冊
    if ! echo "$status_output" | grep -q "RM-REGISTERED"; then
        log "$imsi 未註冊到網絡，嘗試註冊..."
        docker exec $UE_CONTAINER nr-cli $imsi -e "ifup" 2>/dev/null || log "ifup 命令失敗"
        sleep 5
    fi
    
    # 檢查 PDU 會話列表
    local ps_list=$(docker exec $UE_CONTAINER nr-cli $imsi -e "ps-list" 2>/dev/null)
    if ! echo "$ps_list" | grep -q "PS-ACTIVE"; then
        log "$imsi 沒有活動的 PDU 會話，嘗試建立..."
        # 先釋放可能存在的 PDU 會話
        for i in {1..5}; do
            docker exec $UE_CONTAINER nr-cli $imsi -e "ps-release $i" 2>/dev/null || true
            sleep 1
        done
        
        # 嘗試建立新的 PDU 會話
        for i in {1..3}; do
            log "第 $i 次嘗試建立 PDU 會話..."
            docker exec $UE_CONTAINER nr-cli $imsi -e "ps-establish internet" 2>/dev/null && {
                log "PDU 會話建立成功"
                break
            } || log "PDU 會話建立失敗，繼續嘗試..."
            sleep 5
        done
    else
        log "$imsi 已有活動的 PDU 會話"
    fi
    
    # 再次檢查 PDU 會話
    ps_list=$(docker exec $UE_CONTAINER nr-cli $imsi -e "ps-list" 2>/dev/null)
    if echo "$ps_list" | grep -q "PS-ACTIVE"; then
        # 提取 PDU 會話 IP 地址
        local ue_ip=$(echo "$ps_list" | grep -oP 'address: \K[0-9.]+')
        log "PDU 會話 IP: $ue_ip"
        
        # 優化 UE 路由設置
        docker exec $UE_CONTAINER ip link set dev uesimtun0 up 2>/dev/null || log "無法啟用 uesimtun0 接口"
        docker exec $UE_CONTAINER ip addr add $ue_ip/16 dev uesimtun0 2>/dev/null || log "IP 地址可能已經配置"
        docker exec $UE_CONTAINER ip route del default 2>/dev/null || true
        docker exec $UE_CONTAINER ip route add default dev uesimtun0 2>/dev/null || log "無法設置默認路由"
        docker exec $UE_CONTAINER ip route add $SUBNET dev uesimtun0 2>/dev/null || log "無法添加子網路由"
        docker exec $UE_CONTAINER ip route add $UPF_IP dev uesimtun0 2>/dev/null || log "無法添加 UPF 路由"
        
        # 添加靜態 ARP 項
        docker exec $UE_CONTAINER ip neighbor add $UPF_IP dev uesimtun0 nud permanent 2>/dev/null || \
        docker exec $UE_CONTAINER ip neighbor change $UPF_IP dev uesimtun0 nud permanent 2>/dev/null || \
        log "無法添加 UPF 的 ARP 項"
        
        log "PDU 會話和路由配置完成"
        return 0
    else
        log "警告: 無法建立 PDU 會話"
        return 1
    fi
}

# 驗證網絡連接
verify_connectivity() {
    local imsi=$1
    local success=false
    
    log "驗證 $imsi 的網絡連接..."
    
    # 獲取 PDU 會話的 IP 地址
    local ps_list=$(docker exec $UE_CONTAINER nr-cli $imsi -e "ps-list" 2>/dev/null)
    local ue_ip=$(echo "$ps_list" | grep -oP 'address: \K[0-9.]+')
    
    if [ -z "$ue_ip" ]; then
        log "無法獲取 PDU 會話 IP 地址"
        return 1
    fi
    
    # 測試到 UPF 的連接
    log "測試到 UPF ($UPF_IP) 的連接..."
    if docker exec $UE_CONTAINER ping -I uesimtun0 $UPF_IP -c 3 -W 10 &>/dev/null; then
        log "到 UPF 的連接正常"
        success=true
    else
        log "警告: 無法連接到 UPF"
    fi
    
    # 測試到代理的連接
    PROXY_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $PROXY_CONTAINER 2>/dev/null || echo "")
    if [ -n "$PROXY_IP" ]; then
        log "測試到代理 ($PROXY_IP) 的連接..."
        if docker exec $UE_CONTAINER ping -I uesimtun0 $PROXY_IP -c 3 -W 10 &>/dev/null; then
            log "到代理的連接正常"
            success=true
        else
            log "警告: 無法連接到代理"
        fi
    fi
    
    if [ "$success" = true ]; then
        return 0
    else
        return 1
    fi
}

# 主要恢復流程
recover_ue() {
    local imsi=$1
    
    log "開始恢復 $imsi..."
    
    # 恢復容器
    restart_ue_container || return 1
    
    # 優化網絡設置
    optimize_ue_network
    
    # 檢查和恢復 PDU 會話
    check_pdu_session $imsi
    
    # 驗證連接
    if verify_connectivity $imsi; then
        log "$imsi 恢復成功"
        return 0
    else
        log "$imsi 恢復失敗，將在下次檢查時重試"
        return 1
    fi
}

# 啟動 UPF 修復
fix_upf() {
    log "修復 UPF..."
    
    # 檢查 UPF 容器是否運行
    if ! docker ps --format '{{.Names}}' | grep -q "ntn-stack-upf-1"; then
        log "UPF 容器未運行，嘗試重啟..."
        docker compose up -d upf || log "無法啟動 UPF 容器"
        sleep 5
    fi
    
    # 在 UPF 上全面禁用 rp_filter
    docker exec ntn-stack-upf-1 sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || log "無法在 UPF 上禁用 rp_filter (all)"
    docker exec ntn-stack-upf-1 sysctl -w net.ipv4.conf.default.rp_filter=0 2>/dev/null || log "無法在 UPF 上禁用 rp_filter (default)"
    docker exec ntn-stack-upf-1 sysctl -w net.ipv4.conf.lo.rp_filter=0 2>/dev/null || log "無法在 UPF 上禁用 rp_filter (lo)"
    docker exec ntn-stack-upf-1 sysctl -w net.ipv4.conf.ogstun.rp_filter=0 2>/dev/null || log "無法在 UPF 上禁用 rp_filter (ogstun)"
    docker exec ntn-stack-upf-1 sysctl -w net.ipv4.conf.eth0.rp_filter=0 2>/dev/null || log "無法在 UPF 上禁用 rp_filter (eth0)"
    
    # 在 UPF 上啟用 IP 轉發
    docker exec ntn-stack-upf-1 sysctl -w net.ipv4.ip_forward=1 2>/dev/null || log "無法在 UPF 上啟用 IP 轉發"
    docker exec ntn-stack-upf-1 sysctl -w net.ipv4.conf.all.forwarding=1 2>/dev/null || log "無法在 UPF 上啟用 IP 轉發 (all)"
    
    # 配置 UPF 的 iptables 規則
    docker exec ntn-stack-upf-1 iptables -P FORWARD ACCEPT 2>/dev/null || log "無法在 UPF 上設置 FORWARD 規則"
    docker exec ntn-stack-upf-1 iptables -F FORWARD 2>/dev/null || log "無法在 UPF 上清除 FORWARD 規則"
    docker exec ntn-stack-upf-1 iptables -t nat -F POSTROUTING 2>/dev/null || log "無法在 UPF 上清除 POSTROUTING 規則"
    docker exec ntn-stack-upf-1 iptables -t nat -A POSTROUTING -s 10.45.0.0/16 -o eth0 -j MASQUERADE 2>/dev/null || log "無法在 UPF 上添加 MASQUERADE 規則"
    
    log "UPF 修復完成"
}

# 主循環函數
main_loop() {
    while true; do
        log "開始檢查..."
        
        # 修復 UPF
        fix_upf
        
        # 恢復所有 IMSI
        for imsi in "${IMSI_LIST[@]}"; do
            recover_ue $imsi
        done
        
        log "檢查完成，等待 ${CHECK_INTERVAL} 秒..."
        sleep $CHECK_INTERVAL
    done
}

# 主函數
main() {
    local mode=$1
    
    log "UE 自動恢復腳本啟動"
    
    case "$mode" in
        "daemon")
            log "以守護進程模式運行"
            main_loop
            ;;
        "once")
            log "執行一次性恢復"
            fix_upf
            for imsi in "${IMSI_LIST[@]}"; do
                recover_ue $imsi
            done
            log "一次性恢復完成"
            ;;
        *)
            log "用法: $0 [once|daemon]"
            log "  once   - 執行一次性恢復"
            log "  daemon - 以守護進程模式運行"
            ;;
    esac
}

# 執行腳本
main "$@" 