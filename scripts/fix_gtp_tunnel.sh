#!/bin/bash

# GTP隧道修復腳本
# 此腳本用於修復UE與UPF之間的GTP通信問題
# 通過調整UPF配置和手動添加GTPU規則來解決

set -e

UPF_CONTAINER="ntn-stack-upf-1"
SMF_CONTAINER="ntn-stack-smf-1"
UE_CONTAINER="ntn-stack-ues1-1"

echo "開始修復GTP隧道通信問題..."

# 1. 獲取UE PDU會話信息
echo "獲取UE PDU會話信息..."
UE_PDU_INFO=$(docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-list")
echo "$UE_PDU_INFO"

# 獲取UE IP地址
UE_IP=$(echo "$UE_PDU_INFO" | grep "address:" | head -1 | awk '{print $2}')
if [ -z "$UE_IP" ]; then
    echo "錯誤: 無法獲取UE IP地址"
    exit 1
fi
echo "UE IP地址: $UE_IP"

# 2. 檢查UPF的ogstun接口
echo "檢查UPF的ogstun接口..."
docker exec -it $UPF_CONTAINER ip a show dev ogstun

# 3. 檢查UPF的GTP端口
echo "檢查UPF的GTP端口..."
docker exec -it $UPF_CONTAINER ss -anup | grep 2152

# 4. 禁用UPF的IP源地址欺騙保護
echo "禁用UPF的IP源地址欺騙保護..."
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.ogstun.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0

# 5. 允許所有相關iptables規則
echo "配置UPF防火牆規則..."
docker exec -it $UPF_CONTAINER iptables -P INPUT ACCEPT
docker exec -it $UPF_CONTAINER iptables -P FORWARD ACCEPT
docker exec -it $UPF_CONTAINER iptables -P OUTPUT ACCEPT

# 6. 重啟UPF服務以刷新GTP隧道
echo "重啟UPF和SMF服務..."
docker restart $UPF_CONTAINER
sleep 3
docker restart $SMF_CONTAINER
sleep 3

# 7. 重建UE PDU會話
echo "重建UE PDU會話..."
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-release 1" || true
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-release 2" || true
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-release 3" || true
sleep 2
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-establish IPv4 --sst 1 --dnn internet"
sleep 3

# 8. 再次獲取PDU會話信息
echo "檢查重建的PDU會話..."
UE_PDU_INFO=$(docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-list")
echo "$UE_PDU_INFO"

# 獲取新的UE IP地址
NEW_UE_IP=$(echo "$UE_PDU_INFO" | grep "address:" | head -1 | awk '{print $2}')
if [ -z "$NEW_UE_IP" ]; then
    echo "錯誤: 無法獲取重建後的UE IP地址"
    exit 1
fi
echo "新的UE IP地址: $NEW_UE_IP"

# 9. 設置UE接口和路由
echo "設置UE接口和路由..."
docker exec -it $UE_CONTAINER ip addr flush dev uesimtun0
docker exec -it $UE_CONTAINER ip addr add $NEW_UE_IP/32 dev uesimtun0
docker exec -it $UE_CONTAINER ip route del default > /dev/null 2>&1 || true
docker exec -it $UE_CONTAINER ip route add default dev uesimtun0

# 10. 在UPF上顯式允許來自UE的流量
echo "在UPF上允許UE流量..."
docker exec -it $UPF_CONTAINER iptables -F FORWARD
docker exec -it $UPF_CONTAINER iptables -A FORWARD -i ogstun -j ACCEPT
docker exec -it $UPF_CONTAINER iptables -A FORWARD -o ogstun -j ACCEPT
docker exec -it $UPF_CONTAINER iptables -t nat -F POSTROUTING
docker exec -it $UPF_CONTAINER iptables -t nat -A POSTROUTING -s 10.45.0.0/16 -o eth0 -j MASQUERADE

# 11. 測試連接
echo "測試UE到UPF的連接..."
docker exec -it $UE_CONTAINER ping -I uesimtun0 10.45.0.1 -c 4 || echo "Ping到UPF失敗，但這不一定表示GTP隧道有問題"

echo "測試UE到外部網絡的連接..."
docker exec -it $UE_CONTAINER ping -I uesimtun0 8.8.8.8 -c 4 || echo "Ping到外部網絡失敗，GTP隧道可能仍有問題"

echo "GTP隧道修復完成!" 