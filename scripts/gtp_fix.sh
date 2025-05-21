#!/bin/bash

# GTP通信修復腳本
# 本腳本用於解決UE和UPF之間的GTP通信問題
# 特別解決IP源地址驗證(rp_filter)問題

set -e

UPF_CONTAINER="ntn-stack-upf-1"
UE_CONTAINER="ntn-stack-ues1-1"
GNB_CONTAINER="gnb1"

echo "開始修復GTP通信問題..."

# 1. 獲取當前UE IP地址
UE_IP=$(docker exec -it $UE_CONTAINER ip addr show dev uesimtun0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
if [ -z "$UE_IP" ]; then
    echo "錯誤: 無法獲取UE IP地址"
    exit 1
fi
echo "UE IP地址: $UE_IP"

# 2. 在UPF上全面禁用rp_filter
echo "在UPF上禁用所有rp_filter設置..."
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.ogstun.rp_filter=0
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.eth0.rp_filter=0

# 同時也在GNB容器中禁用
echo "在GNB上禁用所有rp_filter設置..."
docker exec -it $GNB_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0
docker exec -it $GNB_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0
docker exec -it $GNB_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0
docker exec -it $GNB_CONTAINER sysctl -w net.ipv4.conf.eth0.rp_filter=0

# 3. 在UPF上啟用所有IP轉發選項
echo "在UPF上啟用IP轉發選項..."
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.ip_forward=1
docker exec -it $UPF_CONTAINER sysctl -w net.ipv4.conf.all.forwarding=1

# 4. 確保UPF的iptables規則正確
echo "配置UPF的iptables規則..."
docker exec -it $UPF_CONTAINER iptables -P FORWARD ACCEPT
docker exec -it $UPF_CONTAINER iptables -F FORWARD
docker exec -it $UPF_CONTAINER iptables -t nat -F POSTROUTING
docker exec -it $UPF_CONTAINER iptables -t nat -A POSTROUTING -s 10.45.0.0/16 -o eth0 -j MASQUERADE

# 5. 修改UE的路由並確保接口正確配置
echo "配置UE的網絡路由..."
docker exec -it $UE_CONTAINER ip link set dev uesimtun0 up
docker exec -it $UE_CONTAINER ip addr add $UE_IP/24 dev uesimtun0 || true
docker exec -it $UE_CONTAINER ip route del default > /dev/null 2>&1 || true
docker exec -it $UE_CONTAINER ip route add default dev uesimtun0

# 6. 在UPF上針對UE的IP地址禁用IP源地址欺騙保護
echo "禁用UPF對UE的IP源地址欺騙保護..."
docker exec -it $UPF_CONTAINER iptables -F FORWARD
docker exec -it $UPF_CONTAINER iptables -I FORWARD 1 -s $UE_IP -j ACCEPT
docker exec -it $UPF_CONTAINER iptables -I FORWARD 2 -d $UE_IP -j ACCEPT

# 7. 在主機上設置轉發規則（如果是特權模式運行）
echo "在主機上設置轉發規則..."
sudo sysctl -w net.ipv4.conf.all.rp_filter=0 || echo "無法在主機上設置rp_filter，可能需要以root權限運行"
sudo iptables -I FORWARD -s 10.45.0.0/16 -j ACCEPT || echo "無法設置主機轉發規則，可能需要以root權限運行"
sudo iptables -I FORWARD -d 10.45.0.0/16 -j ACCEPT || echo "無法設置主機轉發規則，可能需要以root權限運行"

# 8. 顯示更新後的配置
echo "UPF的rp_filter設置:"
docker exec -it $UPF_CONTAINER sysctl -a | grep rp_filter

echo "UPF防火牆規則:"
docker exec -it $UPF_CONTAINER iptables -L FORWARD -v

echo "UE路由表:"
docker exec -it $UE_CONTAINER ip route

echo "GTP通信修復完成!"
echo "如果問題仍然存在，請嘗試重新啟動UE PDU會話" 