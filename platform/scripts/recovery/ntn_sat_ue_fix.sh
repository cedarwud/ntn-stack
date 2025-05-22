#!/bin/bash

# 衛星高延遲環境下UE PDU會話修復腳本
# 此腳本專門針對衛星高延遲環境優化UE配置

set -e

UE_CONTAINER="ntn-stack-ues1-1"
UPF_IP="10.45.0.1"
IMSI="imsi-999700000000001"
SUBNET="10.45.0.0/16"
PROXY_CONTAINER="ntn-proxy"

echo "===== 開始衛星環境UE修復 ====="

# 檢查容器是否運行
if ! docker ps | grep -q "$UE_CONTAINER"; then
    echo "嘗試重啟 UE 容器..."
    docker rm -f $UE_CONTAINER 2>/dev/null || true
    docker compose up -d ues1
    echo "等待容器啟動 (15秒)..."
    sleep 15
    
    # 再次檢查
    if ! docker ps | grep -q "$UE_CONTAINER"; then
        echo "錯誤: 無法啟動 UE 容器，請檢查 Docker 日誌"
        exit 1
    fi
fi

echo "UE 容器已確認運行"

# 在UE容器中清理網絡設置
echo "清理UE網絡設置..."
docker exec $UE_CONTAINER sysctl -w net.ipv4.ip_forward=1 || echo "無法設置 IP 轉發"
docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0 || echo "無法禁用 rp_filter"
docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0 || echo "無法禁用 default rp_filter"

# 釋放所有PDU會話
echo "釋放現有PDU會話..."
for i in {1..5}; do
    docker exec $UE_CONTAINER nr-cli $IMSI -e "ps-release $i" 2>/dev/null || true
    sleep 1
done

# 配置DNS解析
echo "配置DNS解析..."
docker exec $UE_CONTAINER bash -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf" || echo "無法設置 DNS 8.8.8.8"
docker exec $UE_CONTAINER bash -c "echo 'nameserver 1.1.1.1' >> /etc/resolv.conf" || echo "無法設置 DNS 1.1.1.1"

# 確保接口正常初始化
echo "檢查和優化介面..."
docker exec $UE_CONTAINER ip link set lo up || echo "無法啟用 lo 介面"
if docker exec $UE_CONTAINER ip link | grep -q "uesimtun0"; then
    docker exec $UE_CONTAINER ip link set dev uesimtun0 up || echo "無法啟用 uesimtun0 介面"
else
    echo "介面 uesimtun0 不存在，檢查註冊狀態..."
fi

# 檢查註冊狀態
echo "檢查 UE 註冊狀態..."
status_output=$(docker exec $UE_CONTAINER nr-cli $IMSI -e "status" 2>/dev/null) || {
    echo "無法獲取 UE 狀態，嘗試重新初始化..."
    docker exec $UE_CONTAINER nr-cli $IMSI -e "ifup" 2>/dev/null || echo "ifup 命令失敗"
    sleep 5
}

# 重新註冊
echo "嘗試重新註冊..."
docker exec $UE_CONTAINER nr-cli $IMSI -e "deregister" 2>/dev/null || echo "取消註冊失敗 (可能已取消註冊)"
sleep 3
docker exec $UE_CONTAINER nr-cli $IMSI -e "register" 2>/dev/null || echo "註冊命令失敗"
sleep 8

# 嘗試啟動新PDU會話
echo "啟動新PDU會話 (多次嘗試)..."
ps_activated=false
for i in {1..5}; do
    echo "嘗試 $i/5..."
    if docker exec $UE_CONTAINER nr-cli $IMSI -e "ps-establish internet" 2>/dev/null; then
        echo "第 $i 次嘗試成功"
        ps_activated=true
        break
    else
        echo "第 $i 次嘗試失敗，暫停 5 秒..."
        sleep 5
    fi
done

# 檢查PDU會話狀態
echo "檢查PDU會話狀態..."
ps_info=$(docker exec $UE_CONTAINER nr-cli $IMSI -e "ps-list" 2>/dev/null) || {
    echo "無法獲取 PDU 會話列表"
    ps_info=""
}
echo "$ps_info"

# 從PDU會話信息中提取IP地址
ue_ip=$(echo "$ps_info" | grep -oP 'address: \K[0-9.]+' || echo "10.45.0.6")
echo "UE IP: $ue_ip"

# 手動配置uesimtun0接口 (無論 PDU 會話成功與否，都嘗試配置)
echo "配置uesimtun0接口..."

# 創建接口如果不存在
if ! docker exec $UE_CONTAINER ip link | grep -q "uesimtun0"; then
    echo "嘗試手動創建 uesimtun0 接口..."
    docker exec $UE_CONTAINER ip tuntap add dev uesimtun0 mode tun || echo "無法創建 uesimtun0"
fi

# 配置接口
docker exec $UE_CONTAINER ip link set dev uesimtun0 up 2>/dev/null || echo "uesimtun0接口未創建或無法啟動"
docker exec $UE_CONTAINER ip addr add $ue_ip/16 dev uesimtun0 2>/dev/null || echo "IP地址可能已經配置"

# 配置路由表
echo "配置路由表..."
docker exec $UE_CONTAINER ip route del default 2>/dev/null || true
docker exec $UE_CONTAINER ip route add default dev uesimtun0 2>/dev/null || echo "無法設置默認路由"
docker exec $UE_CONTAINER ip route add $SUBNET dev uesimtun0 2>/dev/null || echo "無法添加子網路由"
docker exec $UE_CONTAINER ip route add $UPF_IP dev uesimtun0 2>/dev/null || echo "無法添加 UPF 路由"

# 添加proxy到hosts文件
echo "添加proxy到hosts文件..."
PROXY_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $PROXY_CONTAINER 2>/dev/null || echo "")
if [ -n "$PROXY_IP" ]; then
    docker exec $UE_CONTAINER bash -c "grep -q $PROXY_CONTAINER /etc/hosts || echo '$PROXY_IP $PROXY_CONTAINER' >> /etc/hosts" || echo "無法添加 proxy 到 hosts 文件"
    echo "Proxy IP: $PROXY_IP 已添加到hosts"
else
    echo "警告: 無法獲取proxy容器IP"
fi

# 配置TCP參數優化，適應高延遲環境
echo "優化TCP參數..."
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216" 2>/dev/null || echo "無法設置 TCP 接收緩衝區"
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216" 2>/dev/null || echo "無法設置 TCP 發送緩衝區"
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_window_scaling=1 2>/dev/null || echo "無法啟用 TCP 窗口縮放"
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_timestamps=1 2>/dev/null || echo "無法啟用 TCP 時間戳"
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_sack=1 2>/dev/null || echo "無法啟用 TCP 選擇性確認"
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_congestion_control=cubic 2>/dev/null || echo "無法設置 TCP 擁擠控制"

# 高延遲環境下的TCP連接保持配置
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_keepalive_time=120 2>/dev/null || echo "無法設置 TCP keepalive 時間"
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_keepalive_intvl=30 2>/dev/null || echo "無法設置 TCP keepalive 間隔"
docker exec $UE_CONTAINER sysctl -w net.ipv4.tcp_keepalive_probes=8 2>/dev/null || echo "無法設置 TCP keepalive 探測次數"

# 強制添加ARP項，確保路由正確
echo "添加ARP項..."
docker exec $UE_CONTAINER ip neighbor add $UPF_IP dev uesimtun0 nud permanent 2>/dev/null || \
docker exec $UE_CONTAINER ip neighbor change $UPF_IP dev uesimtun0 nud permanent 2>/dev/null || \
echo "無法添加UPF的ARP項"

# 測試網絡連接
echo "測試網絡連接..."
echo "1. 測試到UPF的連接"
if docker exec $UE_CONTAINER ping -I uesimtun0 $UPF_IP -c 2 -W 5; then
    echo "到 UPF 的連接正常"
else
    echo "警告: 無法連接到UPF，嘗試最後修復..."
    docker exec $UE_CONTAINER nr-cli $IMSI -e "ps-release 1" 2>/dev/null || true
    sleep 2
    docker exec $UE_CONTAINER nr-cli $IMSI -e "ps-establish internet" 2>/dev/null || echo "最終嘗試建立 PDU 會話失敗"
    sleep 3
    docker exec $UE_CONTAINER ip route add $UPF_IP dev uesimtun0 2>/dev/null || true
    docker exec $UE_CONTAINER ping -I uesimtun0 $UPF_IP -c 1 -W 2 || echo "最終連接測試失敗"
fi

# 顯示最終網絡配置
echo "===== UE網絡配置 ====="
echo "接口:"
docker exec $UE_CONTAINER ip addr show dev uesimtun0 2>/dev/null || echo "uesimtun0 接口不存在"
echo "路由表:"
docker exec $UE_CONTAINER ip route
echo "DNS配置:"
docker exec $UE_CONTAINER cat /etc/resolv.conf
echo "hosts文件:"
docker exec $UE_CONTAINER cat /etc/hosts

echo "衛星環境UE修復完成!" 