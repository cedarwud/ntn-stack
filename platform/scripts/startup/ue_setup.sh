#!/bin/bash

# UE配置腳本 - 自動設置UE連接
# 本腳本將處理UE網絡連接的所有必要步驟
# 包括: 釋放現有會話、建立新會話、配置網絡接口、設置路由和DNS

# 設置錯誤處理，允許部分命令失敗但繼續執行
set +e

UE_CONTAINER="ntn-stack-ues1-1"
UE_ID="imsi-999700000000001"
MTU=1400  # 設置較小的MTU以適應GTP封裝

echo "開始配置UE $UE_ID 在容器 $UE_CONTAINER 中..."

# 1. 釋放任何現有PDU會話
echo "釋放任何現有PDU會話..."
docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-release 1" 2>/dev/null || true
docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-release 2" 2>/dev/null || true
docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-release 3" 2>/dev/null || true
docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-release 4" 2>/dev/null || true
docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-release 5" 2>/dev/null || true

# 2. 清除uesimtun0接口
echo "清除uesimtun0接口..."
docker exec $UE_CONTAINER ip link set dev uesimtun0 down 2>/dev/null || true
docker exec $UE_CONTAINER ip addr flush dev uesimtun0 2>/dev/null || true

# 3. 確保UE中已開啟IP轉發和禁用rp_filter
echo "在UE中禁用rp_filter和開啟IP轉發..."
docker exec $UE_CONTAINER sysctl -w net.ipv4.ip_forward=1 || echo "設置ip_forward失敗，但繼續執行"
docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0 || echo "設置rp_filter失敗，但繼續執行"
docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0 || echo "設置rp_filter失敗，但繼續執行"
docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0 || echo "設置rp_filter失敗，但繼續執行"
docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.eth0.rp_filter=0 || echo "設置rp_filter失敗，但繼續執行"
docker exec $UE_CONTAINER sysctl -w net.ipv4.conf.uesimtun0.rp_filter=0 2>/dev/null || true

# 4. 建立新的PDU會話
echo "建立新的PDU會話..."
docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-establish IPv4 --sst 1 --dnn internet" || echo "PDU會話建立可能失敗，但繼續執行"
echo "嘗試替代命令建立PDU會話..."
docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-establish internet" || echo "替代PDU會話建立命令也失敗，但繼續執行"

# 5. 等待PDU會話建立
echo "等待PDU會話建立..."
sleep 5

# 6. 獲取PDU會話信息和IP地址
PS_INFO=$(docker exec $UE_CONTAINER nr-cli $UE_ID -e "ps-list" 2>/dev/null)
IP_ADDR=$(echo "$PS_INFO" | grep -oP 'address: \K[0-9.]+' 2>/dev/null)

if [ -z "$IP_ADDR" ]; then
    echo "警告: 未能從ps-list獲取IP地址，使用默認值 10.45.0.2"
    IP_ADDR="10.45.0.2"
else
    echo "從PDU會話獲取的IP地址: $IP_ADDR"
fi

# 檢查uesimtun0接口是否存在
if ! docker exec $UE_CONTAINER ip link show dev uesimtun0 >/dev/null 2>&1; then
    echo "警告: uesimtun0接口不存在，PDU會話可能未成功建立"
    echo "嘗試手動創建uesimtun0接口..."
    docker exec $UE_CONTAINER ip tuntap add dev uesimtun0 mode tun || echo "無法創建uesimtun0接口，但繼續執行"
fi

# 7. 優化uesimtun0接口配置
echo "配置uesimtun0接口..."
docker exec $UE_CONTAINER ip link set dev uesimtun0 up 2>/dev/null || echo "無法啟用uesimtun0接口，但繼續執行"
docker exec $UE_CONTAINER ip link set dev uesimtun0 mtu $MTU 2>/dev/null || echo "無法設置MTU，但繼續執行"
docker exec $UE_CONTAINER ip addr flush dev uesimtun0 2>/dev/null || echo "無法清除地址，但繼續執行"
docker exec $UE_CONTAINER ip addr add $IP_ADDR/16 dev uesimtun0 2>/dev/null || echo "無法添加IP地址，但繼續執行"

# 8. 設置默認路由
echo "設置默認路由..."
docker exec $UE_CONTAINER ip route del default 2>/dev/null || true
docker exec $UE_CONTAINER ip route add default dev uesimtun0 2>/dev/null || echo "無法設置默認路由，但繼續執行"

# 9. 添加DNS配置
echo "設置DNS..."
docker exec $UE_CONTAINER bash -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
docker exec $UE_CONTAINER bash -c "echo 'nameserver 1.1.1.1' >> /etc/resolv.conf"

# 10. 添加到UPF的明確路由
echo "添加到UPF的路由..."
docker exec $UE_CONTAINER ip route add 10.45.0.1 dev uesimtun0 2>/dev/null || echo "無法添加UPF路由，但繼續執行"

# 11. 添加ntn-proxy的hosts條目
echo "添加ntn-proxy到hosts文件..."
PROXY_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ntn-proxy)
if [ -n "$PROXY_IP" ]; then
    echo "ntn-proxy IP: $PROXY_IP"
    docker exec $UE_CONTAINER bash -c "grep -q ntn-proxy /etc/hosts || echo '$PROXY_IP ntn-proxy' >> /etc/hosts"
else
    echo "警告: 無法獲取ntn-proxy的IP地址"
fi

# 12. 測試連接
echo "測試到UPF的連接..."
docker exec $UE_CONTAINER ping -c 2 -W 1 10.45.0.1 || echo "警告: 無法連接到UPF (10.45.0.1)"

echo "測試到ntn-proxy的連接..."
docker exec $UE_CONTAINER ping -c 2 -W 1 ntn-proxy || echo "警告: 無法連接到ntn-proxy"

echo "測試外部連接..."
docker exec $UE_CONTAINER ping -I uesimtun0 -c 2 -W 1 8.8.8.8 || echo "警告: 無法連接到外部網絡 (8.8.8.8)"

# 13. 顯示最終網絡配置
echo "UE網絡配置:"
docker exec $UE_CONTAINER ip addr show dev uesimtun0 2>/dev/null || echo "無法顯示uesimtun0配置"
docker exec $UE_CONTAINER ip route || echo "無法顯示路由表"
docker exec $UE_CONTAINER cat /etc/hosts || echo "無法顯示hosts文件"

echo "UE配置完成!" 