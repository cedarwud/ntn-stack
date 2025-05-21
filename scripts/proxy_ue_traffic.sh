#!/bin/bash

# UE代理通信腳本
# 此腳本創建UE代理通信，通過容器網絡轉發UE流量

UE_CONTAINER="ntn-stack-ues1-1"
BACKEND_CONTAINER="fastapi_app"

echo "配置UE網絡代理通信..."

# 確保UE PDU會話已建立
echo "重置UE PDU會話..."
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-release 1" || true
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-release 2" || true
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-release 3" || true
docker exec -it $UE_CONTAINER ip addr flush dev uesimtun0 || true

echo "建立新的PDU會話..."
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-establish IPv4 --sst 1 --dnn internet"

sleep 2

# 獲取UE IP地址
UE_IP=$(docker exec -it $UE_CONTAINER ip addr show dev uesimtun0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
if [ -z "$UE_IP" ]; then
    echo "錯誤: 無法獲取UE IP地址"
    exit 1
fi
echo "UE IP地址: $UE_IP"

# 配置UE接口
docker exec -it $UE_CONTAINER ip addr flush dev uesimtun0
docker exec -it $UE_CONTAINER ip addr add $UE_IP/32 dev uesimtun0
docker exec -it $UE_CONTAINER ip route del default || true
docker exec -it $UE_CONTAINER ip route add default dev uesimtun0

# 配置UE流量轉發
echo "配置UE流量轉發..."

# 方案1: 配置UE使用容器網絡進行通信
BACKEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $BACKEND_CONTAINER)
echo "後端IP地址: $BACKEND_IP"
docker exec -it $UE_CONTAINER ip route add 172.18.0.0/16 dev eth0

# 獲取UE的默認IP
UE_CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $UE_CONTAINER)
echo "UE容器IP: $UE_CONTAINER_IP"

echo "測試UE容器網絡連接..."
docker exec -it $UE_CONTAINER ping -c 3 $BACKEND_IP
echo "UE代理通信配置完成!"

# 設置使用說明
echo ""
echo "===== 使用說明 ====="
echo "您現在可以通過UE容器的IP地址進行通信:"
echo "UE容器IP: $UE_CONTAINER_IP"
echo ""
echo "例如，使用curl測試連接:"
echo "curl http://$UE_CONTAINER_IP:8000/api/status"
echo ""
echo "或者直接訪問UE容器中的應用程序:"
echo "docker exec -it $UE_CONTAINER curl -v http://$BACKEND_IP:8000/api/status" 