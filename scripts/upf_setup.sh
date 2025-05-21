#!/bin/bash

# UPF配置腳本 - 設置UPF轉發和NAT規則
# 本腳本將處理UPF網絡轉發所需的所有配置
# 適用於高延遲NTN環境，包括更多的容錯設置

set -e

UPF_CONTAINER="ntn-stack-upf-1"
UE_SUBNET="10.45.0.0/16"

echo "開始配置UPF在容器 $UPF_CONTAINER 中..."

# 1. 檢查UPF容器是否運行
if ! docker ps | grep -q "$UPF_CONTAINER"; then
    echo "錯誤: UPF容器 $UPF_CONTAINER 未運行"
    exit 1
fi

# 2. 檢查ogstun接口是否存在
if ! docker exec -it $UPF_CONTAINER ip link show dev ogstun 2>/dev/null; then
    echo "警告: ogstun接口不存在，等待Open5GS創建接口..."
    # 這裡可以添加一些邏輯來等待接口創建
    sleep 5
fi

# 3. 啟用IP轉發
echo "啟用IP轉發..."
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.ip_forward=1
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.all.forwarding=1

# 4. 禁用反向路徑過濾(rp_filter)
echo "禁用反向路徑過濾..."
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.ogstun.rp_filter=0 2>/dev/null || true
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.eth0.rp_filter=0

# 5. 設置UDP緩衝區大小，適用於高延遲環境
echo "設置UDP緩衝區大小..."
docker exec -it $UPF_CONTAINER sysctl -w net.core.rmem_max=8388608
docker exec -it $UPF_CONTAINER sysctl -w net.core.wmem_max=8388608
docker exec -it $UPF_CONTAINER sysctl -w net.core.rmem_default=1048576
docker exec -it $UPF_CONTAINER sysctl -w net.core.wmem_default=1048576

# 6. 配置TCP擁塞控制和窗口大小
echo "優化TCP參數..."
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.tcp_rmem="4096 87380 8388608"
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.tcp_wmem="4096 65536 8388608"
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.tcp_congestion_control=cubic

# 7. 確保已啟用NAT
echo "設置NAT規則..."
# 清除現有的NAT規則
docker exec -it $UPF_CONTAINER iptables -t nat -F POSTROUTING

# 新增NAT規則
docker exec -it $UPF_CONTAINER iptables -t nat -A POSTROUTING -s $UE_SUBNET -o eth0 -j MASQUERADE

# 8. 確保已啟用轉發規則
echo "設置轉發規則..."
# 清除現有的轉發規則
docker exec -it $UPF_CONTAINER iptables -F FORWARD

# 新增轉發規則
docker exec -it $UPF_CONTAINER iptables -P FORWARD ACCEPT
docker exec -it $UPF_CONTAINER iptables -A FORWARD -s $UE_SUBNET -j ACCEPT
docker exec -it $UPF_CONTAINER iptables -A FORWARD -d $UE_SUBNET -j ACCEPT

# 9. 確保GTP-U端口允許流量
echo "確保GTP-U端口(2152)開放..."
docker exec -it $UPF_CONTAINER iptables -A INPUT -p udp --dport 2152 -j ACCEPT
docker exec -it $UPF_CONTAINER iptables -A OUTPUT -p udp --sport 2152 -j ACCEPT

# 10. 顯示當前設置
echo "當前NAT規則:"
docker exec -it $UPF_CONTAINER iptables -t nat -L POSTROUTING -v

echo "當前轉發規則:"
docker exec -it $UPF_CONTAINER iptables -L FORWARD -v

echo "ogstun接口設置:"
docker exec -it $UPF_CONTAINER ip addr show dev ogstun 2>/dev/null || echo "ogstun接口尚未創建"

echo "IP轉發和rp_filter設置:"
docker exec -it $UPF_CONTAINER sysctl -a | grep -E "ipv4.ip_forward|rp_filter"

echo "UPF配置完成!" 