#!/bin/bash

# UE配置腳本 - 自動設置UE連接
# 本腳本將處理UE網絡連接的所有必要步驟
# 包括: 釋放現有會話、建立新會話、配置網絡接口、設置路由和DNS

set -e

UE_CONTAINER="ntn-stack-ues1-1"
UE_ID="imsi-999700000000001"
MTU=1400  # 設置較小的MTU以適應GTP封裝

echo "開始配置UE $UE_ID 在容器 $UE_CONTAINER 中..."

# 1. 釋放任何現有PDU會話
echo "釋放任何現有PDU會話..."
docker exec -it $UE_CONTAINER nr-cli $UE_ID -e "ps-release 1" 2>/dev/null || true
docker exec -it $UE_CONTAINER nr-cli $UE_ID -e "ps-release 2" 2>/dev/null || true
docker exec -it $UE_CONTAINER nr-cli $UE_ID -e "ps-release 3" 2>/dev/null || true
docker exec -it $UE_CONTAINER nr-cli $UE_ID -e "ps-release 4" 2>/dev/null || true
docker exec -it $UE_CONTAINER nr-cli $UE_ID -e "ps-release 5" 2>/dev/null || true

# 2. 清除uesimtun0接口
echo "清除uesimtun0接口..."
docker exec -it $UE_CONTAINER ip link set dev uesimtun0 down 2>/dev/null || true
docker exec -it $UE_CONTAINER ip addr flush dev uesimtun0 2>/dev/null || true

# 3. 確保UE中已開啟IP轉發和禁用rp_filter
echo "在UE中禁用rp_filter和開啟IP轉發..."
docker exec -it $UE_CONTAINER sysctl -w net.ipv4.ip_forward=1
docker exec -it $UE_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0
docker exec -it $UE_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0
docker exec -it $UE_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0
docker exec -it $UE_CONTAINER sysctl -w net.ipv4.conf.eth0.rp_filter=0
docker exec -it $UE_CONTAINER sysctl -w net.ipv4.conf.uesimtun0.rp_filter=0 2>/dev/null || true

# 4. 建立新的PDU會話
echo "建立新的PDU會話..."
docker exec -it $UE_CONTAINER nr-cli $UE_ID -e "ps-establish IPv4 --sst 1 --dnn internet"

# 5. 等待PDU會話建立
echo "等待PDU會話建立..."
sleep 3

# 6. 獲取PDU會話信息
PS_INFO=$(docker exec -it $UE_CONTAINER nr-cli $UE_ID -e "ps-list")
IP_ADDR=$(echo "$PS_INFO" | grep -oP 'address: \K[0-9.]+')

if [ -z "$IP_ADDR" ]; then
    echo "錯誤: 未能獲取IP地址，PDU會話可能未成功建立"
    exit 1
fi

echo "分配的IP地址: $IP_ADDR"

# 7. 優化uesimtun0接口配置
echo "配置uesimtun0接口..."
docker exec -it $UE_CONTAINER ip link set dev uesimtun0 up
docker exec -it $UE_CONTAINER ip link set dev uesimtun0 mtu $MTU
docker exec -it $UE_CONTAINER ip addr flush dev uesimtun0
docker exec -it $UE_CONTAINER ip addr add $IP_ADDR/24 dev uesimtun0

# 8. 設置默認路由
echo "設置默認路由..."
docker exec -it $UE_CONTAINER ip route del default 2>/dev/null || true
docker exec -it $UE_CONTAINER ip route add default dev uesimtun0

# 9. 添加DNS配置
echo "設置DNS..."
docker exec -it $UE_CONTAINER bash -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
docker exec -it $UE_CONTAINER bash -c "echo 'nameserver 1.1.1.1' >> /etc/resolv.conf"

# 10. 添加到UPF的明確路由
echo "添加到UPF的路由..."
docker exec -it $UE_CONTAINER ip route add 10.45.0.1 dev uesimtun0

# 11. 測試連接
echo "測試到UPF的連接..."
docker exec -it $UE_CONTAINER ping -c 2 10.45.0.1 || echo "警告: 無法連接到UPF (10.45.0.1)"

echo "測試外部連接..."
docker exec -it $UE_CONTAINER ping -I uesimtun0 -c 2 8.8.8.8 || echo "警告: 無法連接到外部網絡 (8.8.8.8)"

# 12. 顯示最終網絡配置
echo "UE網絡配置:"
docker exec -it $UE_CONTAINER ip addr show dev uesimtun0
docker exec -it $UE_CONTAINER ip route

echo "UE配置完成!" 