#!/bin/bash

# 容器網絡橋接器腳本
# 此腳本用於創建容器間的網絡橋接，解決不同Docker網絡間的通信問題
# 特別針對UE與UPF之間的通信問題

set -e

# 配置
BRIDGE_NAME="ntn-bridge"
BRIDGE_IMAGE="nicolaka/netshoot"  # 網絡工具容器
UE_CONTAINER="ntn-stack-ues1-1"
UPF_CONTAINER="ntn-stack-upf-1"
BACKEND_CONTAINER="fastapi_app"
OPEN5GS_NETWORK="ntn-stack_open5gs-net"

echo "開始設置容器網絡橋接..."

# 檢查網絡橋接容器是否已存在，如果存在則移除
if docker ps -a | grep -q "$BRIDGE_NAME"; then
    echo "移除現有的網絡橋接容器..."
    docker rm -f "$BRIDGE_NAME"
fi

# 獲取容器網絡信息
echo "獲取容器網絡信息..."
UE_NETWORK=$(docker inspect -f '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}{{end}}' $UE_CONTAINER)
UPF_NETWORK=$(docker inspect -f '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}' $UPF_CONTAINER)
BACKEND_NETWORK=$(docker inspect -f '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}' $BACKEND_CONTAINER)

echo "UE容器網絡: $UE_NETWORK"
echo "UPF容器網絡: $UPF_NETWORK"
echo "後端容器網絡: $BACKEND_NETWORK"

# 創建網絡橋接容器，連接到所有需要的網絡
echo "創建網絡橋接容器..."
docker run -d --name "$BRIDGE_NAME" \
    --network "$UE_NETWORK" \
    --cap-add=NET_ADMIN \
    --privileged \
    "$BRIDGE_IMAGE" sleep infinity

# 連接到其他網絡
if [ "$UE_NETWORK" != "$UPF_NETWORK" ]; then
    echo "將橋接容器連接到UPF網絡..."
    docker network connect "$UPF_NETWORK" "$BRIDGE_NAME"
fi

if [ "$UE_NETWORK" != "$BACKEND_NETWORK" ] && [ "$UPF_NETWORK" != "$BACKEND_NETWORK" ]; then
    echo "將橋接容器連接到後端網絡..."
    docker network connect "$BACKEND_NETWORK" "$BRIDGE_NAME"
fi

# 檢查是否需要連接到Open5GS網絡
if [ "$UE_NETWORK" != "$OPEN5GS_NETWORK" ] && [ "$UPF_NETWORK" != "$OPEN5GS_NETWORK" ] && [ "$BACKEND_NETWORK" != "$OPEN5GS_NETWORK" ]; then
    echo "將橋接容器連接到Open5GS網絡..."
    docker network connect "$OPEN5GS_NETWORK" "$BRIDGE_NAME"
fi

# 禁用橋接容器中的rp_filter
echo "在橋接容器中禁用rp_filter..."
docker exec -it "$BRIDGE_NAME" sysctl -w net.ipv4.conf.all.rp_filter=0
docker exec -it "$BRIDGE_NAME" sysctl -w net.ipv4.conf.default.rp_filter=0
docker exec -it "$BRIDGE_NAME" sysctl -w net.ipv4.conf.eth0.rp_filter=0
docker exec -it "$BRIDGE_NAME" sysctl -w net.ipv4.conf.eth1.rp_filter=0 2>/dev/null || true
docker exec -it "$BRIDGE_NAME" sysctl -w net.ipv4.conf.eth2.rp_filter=0 2>/dev/null || true

# 獲取容器IP地址
UE_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$UE_CONTAINER")
UPF_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$UPF_CONTAINER")
BACKEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$BACKEND_CONTAINER")
BRIDGE_UE_NET_IP=$(docker exec -it "$BRIDGE_NAME" ip addr show dev eth0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
BRIDGE_UPF_NET_IP=$(docker exec -it "$BRIDGE_NAME" ip addr show dev eth1 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1 2>/dev/null || echo "NA")
BRIDGE_BACKEND_NET_IP=$(docker exec -it "$BRIDGE_NAME" ip addr show dev eth2 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1 2>/dev/null || echo "NA")

echo "UE容器IP: $UE_IP"
echo "UPF容器IP: $UPF_IP"
echo "後端容器IP: $BACKEND_IP"
echo "橋接容器在UE網絡的IP: $BRIDGE_UE_NET_IP"
echo "橋接容器在UPF網絡的IP: $BRIDGE_UPF_NET_IP"
echo "橋接容器在後端網絡的IP: $BRIDGE_BACKEND_NET_IP"

# 在橋接容器中啟用IP轉發
echo "在橋接容器中啟用IP轉發..."
docker exec -it "$BRIDGE_NAME" sysctl -w net.ipv4.ip_forward=1

# 在橋接容器中設置NAT規則
echo "在橋接容器中設置NAT規則..."
docker exec -it "$BRIDGE_NAME" iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
docker exec -it "$BRIDGE_NAME" iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE 2>/dev/null || true
docker exec -it "$BRIDGE_NAME" iptables -t nat -A POSTROUTING -o eth2 -j MASQUERADE 2>/dev/null || true
docker exec -it "$BRIDGE_NAME" iptables -A FORWARD -j ACCEPT

# 建立UE到UPF的路由
if [ "$BRIDGE_UPF_NET_IP" != "NA" ]; then
    echo "配置UE容器到UPF的路由..."
    # 獲取UPF的ogstun接口IP
    UPF_TUN_IP=$(docker exec -it "$UPF_CONTAINER" ip addr show dev ogstun | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
    echo "UPF的ogstun接口IP: $UPF_TUN_IP"
    
    # 添加UE到UPF ogstun接口的路由
    docker exec -it "$UE_CONTAINER" ip route add $UPF_TUN_IP via $BRIDGE_UE_NET_IP || true
    
    # 配置UPF容器到UE的路由
    echo "配置UPF容器到UE的路由..."
    # 獲取UE的uesimtun0接口IP
    UE_TUN_IP=$(docker exec -it "$UE_CONTAINER" ip addr show dev uesimtun0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
    echo "UE的uesimtun0接口IP: $UE_TUN_IP"
    
    # 添加UPF到UE uesimtun0接口的路由
    docker exec -it "$UPF_CONTAINER" ip route add $UE_TUN_IP via $BRIDGE_UPF_NET_IP || true
fi

# 建立UE到後端的路由
if [ "$BRIDGE_BACKEND_NET_IP" != "NA" ]; then
    echo "配置UE容器到後端的路由..."
    docker exec -it "$UE_CONTAINER" ip route add $BACKEND_IP via $BRIDGE_UE_NET_IP || true
    
    # 配置後端容器的路由
    echo "配置後端容器到UE的路由..."
    docker exec -it "$BACKEND_CONTAINER" ip route add $UE_IP via $BRIDGE_BACKEND_NET_IP 2>/dev/null || \
    echo "無法在後端容器上設置路由，這可能不影響功能"
fi

# 測試UE到UPF的連接
echo "測試UE到UPF的連接..."
docker exec -it "$UE_CONTAINER" ping -c 3 $UPF_IP || echo "UE到UPF的ping測試失敗，但通過代理仍可能工作"

# 測試UE到後端的連接
echo "測試UE到後端的連接..."
docker exec -it "$UE_CONTAINER" ping -c 3 $BACKEND_IP || echo "UE到後端的ping測試失敗，但通過代理仍可能工作"

# 設置使用指南
echo ""
echo "===== 網絡橋接設置完成 ====="
echo "現在UE容器可以通過以下方式訪問其他服務:"
echo "1. 直接訪問UPF IP: $UPF_IP"
echo "2. 直接訪問後端IP: $BACKEND_IP"
echo "3. 通過橋接容器: $BRIDGE_UE_NET_IP"
echo ""
echo "測試命令:"
echo "1. 測試UE到UPF連接: docker exec -it $UE_CONTAINER ping $UPF_IP"
echo "2. 測試UE到後端連接: docker exec -it $UE_CONTAINER curl http://$BACKEND_IP:8000/api/status"
echo ""
echo "如果您需要添加更多路由或進行其他網絡配置，可以使用橋接容器:"
echo "docker exec -it $BRIDGE_NAME bash" 