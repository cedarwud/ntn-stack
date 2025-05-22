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
UE_IP=$(docker exec $UE_CONTAINER ip addr show dev uesimtun0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
if [ -z "$UE_IP" ]; then
    echo "警告: 無法獲取UE IP地址，使用默認值 10.45.0.2"
    UE_IP="10.45.0.2"
fi
echo "UE IP地址: $UE_IP"

# 2. 在UPF上全面禁用rp_filter
echo "在UPF上禁用所有rp_filter設置..."
docker exec $UPF_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0
docker exec $UPF_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0
docker exec $UPF_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0
docker exec $UPF_CONTAINER sysctl -w net.ipv4.conf.ogstun.rp_filter=0
docker exec $UPF_CONTAINER sysctl -w net.ipv4.conf.eth0.rp_filter=0

# 同時也在GNB容器中禁用
echo "在GNB上禁用所有rp_filter設置..."
docker exec $GNB_CONTAINER sysctl -w net.ipv4.conf.all.rp_filter=0 || echo "GNB rp_filter設置失敗，忽略並繼續"
docker exec $GNB_CONTAINER sysctl -w net.ipv4.conf.default.rp_filter=0 || echo "GNB rp_filter設置失敗，忽略並繼續"
docker exec $GNB_CONTAINER sysctl -w net.ipv4.conf.lo.rp_filter=0 || echo "GNB rp_filter設置失敗，忽略並繼續"
docker exec $GNB_CONTAINER sysctl -w net.ipv4.conf.eth0.rp_filter=0 || echo "GNB rp_filter設置失敗，忽略並繼續"

# 3. 在UPF上啟用所有IP轉發選項
echo "在UPF上啟用IP轉發選項..."
docker exec $UPF_CONTAINER sysctl -w net.ipv4.ip_forward=1
docker exec $UPF_CONTAINER sysctl -w net.ipv4.conf.all.forwarding=1

# 4. 確保UPF的iptables規則正確
echo "配置UPF的iptables規則..."
docker exec $UPF_CONTAINER iptables -P FORWARD ACCEPT
docker exec $UPF_CONTAINER iptables -F FORWARD
docker exec $UPF_CONTAINER iptables -t nat -F POSTROUTING
docker exec $UPF_CONTAINER iptables -t nat -A POSTROUTING -s 10.45.0.0/16 -o eth0 -j MASQUERADE

# 5. 修改UE的路由並確保接口正確配置
echo "配置UE的網絡路由..."
docker exec $UE_CONTAINER ip link set dev uesimtun0 up 2>/dev/null || echo "uesimtun0接口尚未建立，將嘗試建立PDU會話"

# 嘗試建立PDU會話
echo "嘗試建立PDU會話..."
docker exec $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-establish internet" || echo "PDU會話建立命令執行失敗，但繼續執行腳本"

# 再次嘗試配置uesimtun0接口
sleep 3
docker exec $UE_CONTAINER ip link set dev uesimtun0 up 2>/dev/null || echo "uesimtun0接口仍未建立，繼續執行..."
docker exec $UE_CONTAINER ip addr add $UE_IP/16 dev uesimtun0 2>/dev/null || echo "無法設置IP地址，可能已經設置"
docker exec $UE_CONTAINER ip route del default 2>/dev/null || true
docker exec $UE_CONTAINER ip route add default dev uesimtun0 2>/dev/null || echo "無法設置默認路由"

# 6. 在UPF上針對UE的IP地址禁用IP源地址欺騙保護
echo "禁用UPF對UE的IP源地址欺騙保護..."
docker exec $UPF_CONTAINER iptables -F FORWARD
docker exec $UPF_CONTAINER iptables -I FORWARD 1 -s $UE_IP -j ACCEPT
docker exec $UPF_CONTAINER iptables -I FORWARD 2 -d $UE_IP -j ACCEPT

# 7. 在主機上設置轉發規則（如果是特權模式運行）
echo "在主機上設置轉發規則..."
sudo sysctl -w net.ipv4.conf.all.rp_filter=0 || echo "無法在主機上設置rp_filter，可能需要以root權限運行"
sudo iptables -I FORWARD -s 10.45.0.0/16 -j ACCEPT || echo "無法設置主機轉發規則，可能需要以root權限運行"
sudo iptables -I FORWARD -d 10.45.0.0/16 -j ACCEPT || echo "無法設置主機轉發規則，可能需要以root權限運行"

# 8. 配置DNS解析
echo "設置DNS解析..."
# 在UE中添加DNS配置
docker exec $UE_CONTAINER bash -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
docker exec $UE_CONTAINER bash -c "echo 'nameserver 1.1.1.1' >> /etc/resolv.conf"

# 確保ntn-proxy主機名能夠被解析
docker exec $UE_CONTAINER bash -c "grep -q ntn-proxy /etc/hosts || echo '$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ntn-proxy) ntn-proxy' >> /etc/hosts"

# 9. 顯示更新後的配置
echo "UPF的rp_filter設置:"
docker exec $UPF_CONTAINER sysctl -a | grep rp_filter

echo "UPF防火牆規則:"
docker exec $UPF_CONTAINER iptables -L FORWARD -v

echo "UE路由表:"
docker exec $UE_CONTAINER ip route

echo "UE DNS配置:"
docker exec $UE_CONTAINER cat /etc/resolv.conf

echo "UE hosts配置:"
docker exec $UE_CONTAINER cat /etc/hosts

echo "GTP通信修復完成!"
echo "如果問題仍然存在，請嘗試重新啟動UE PDU會話" 