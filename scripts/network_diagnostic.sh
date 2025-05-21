#!/bin/bash

# 全面網絡診斷腳本 - 用於診斷和解決NTN網絡中的問題
# 本腳本將檢查所有網絡組件，從UE到UPF，並提供問題解決建議

set -e

# 配置參數
UE_CONTAINER="ntn-stack-ues1-1"
UPF_CONTAINER="ntn-stack-upf-1"
SMF_CONTAINER="ntn-stack-smf-1"
GNB_CONTAINER="gnb1"
AMF_CONTAINER="ntn-stack-amf-1"
DOCKER_NETWORK="ntn-stack_open5gs-net"

# 創建診斷目錄
DIAG_DIR="network_diagnostics"
mkdir -p $DIAG_DIR

# 生成診斷文件名
timestamp=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="$DIAG_DIR/network_diagnostic_$timestamp.log"
REPORT_FILE="$DIAG_DIR/network_report_$timestamp.txt"

# 初始化診斷報告
echo "NTN網絡診斷報告" > $REPORT_FILE
echo "日期: $(date)" >> $REPORT_FILE
echo "===================================================" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 啟動診斷
echo "全面網絡診斷開始: $(date)" | tee -a $LOG_FILE
echo "===========================================================" | tee -a $LOG_FILE

# 0. 檢查容器狀態
echo "== 檢查容器狀態 ==" | tee -a $LOG_FILE
docker ps | grep -E "$UE_CONTAINER|$UPF_CONTAINER|$SMF_CONTAINER|$GNB_CONTAINER|$AMF_CONTAINER" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查是否所有容器都在運行
if ! docker ps | grep -q "$UE_CONTAINER"; then
    echo "錯誤: UE容器未運行!" | tee -a $LOG_FILE $REPORT_FILE
fi
if ! docker ps | grep -q "$UPF_CONTAINER"; then
    echo "錯誤: UPF容器未運行!" | tee -a $LOG_FILE $REPORT_FILE
fi
if ! docker ps | grep -q "$GNB_CONTAINER"; then
    echo "錯誤: GNB容器未運行!" | tee -a $LOG_FILE $REPORT_FILE
fi

# 1. 檢查Docker網絡
echo "== Docker網絡配置 ==" | tee -a $LOG_FILE
docker network inspect $DOCKER_NETWORK | grep -E "Name|Subnet|Gateway" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 2. 檢查UE配置和連接狀態
echo "== UE配置和連接狀態 ==" | tee -a $LOG_FILE
echo "UE接口配置:" | tee -a $LOG_FILE
docker exec -it $UE_CONTAINER ip a | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UE路由表:" | tee -a $LOG_FILE
docker exec -it $UE_CONTAINER ip route | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UE rp_filter設置:" | tee -a $LOG_FILE
docker exec -it $UE_CONTAINER sysctl -a | grep rp_filter | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UE防火牆規則:" | tee -a $LOG_FILE
docker exec -it $UE_CONTAINER iptables -L -v | tee -a $LOG_FILE 2>/dev/null || echo "無法獲取UE防火牆規則" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查UE是否有uesimtun0接口
if ! docker exec -it $UE_CONTAINER ip a | grep -q "uesimtun0"; then
    echo "問題: UE中未找到uesimtun0接口，PDU會話可能未建立" | tee -a $REPORT_FILE
else
    UE_IP=$(docker exec -it $UE_CONTAINER ip addr show dev uesimtun0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
    echo "UE IP地址: $UE_IP" | tee -a $REPORT_FILE
fi

echo "UE連接狀態:" | tee -a $LOG_FILE
docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "status" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UE PDU會話:" | tee -a $LOG_FILE
PDU_OUTPUT=$(docker exec -it $UE_CONTAINER nr-cli imsi-999700000000001 -e "ps-list")
echo "$PDU_OUTPUT" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查是否有PDU會話
if ! echo "$PDU_OUTPUT" | grep -q "address:"; then
    echo "問題: UE未建立PDU會話" | tee -a $REPORT_FILE
    echo "建議: 執行 './scripts/ue_setup.sh' 重新建立PDU會話" | tee -a $REPORT_FILE
fi

# 3. 檢查UPF配置
echo "== UPF配置 ==" | tee -a $LOG_FILE
echo "UPF接口配置:" | tee -a $LOG_FILE
docker exec -it $UPF_CONTAINER ip a | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UPF路由表:" | tee -a $LOG_FILE
docker exec -it $UPF_CONTAINER ip route | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UPF IP轉發設置:" | tee -a $LOG_FILE
IP_FORWARD=$(docker exec -it $UPF_CONTAINER sysctl -a | grep ip_forward)
echo "$IP_FORWARD" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UPF rp_filter設置:" | tee -a $LOG_FILE
RP_FILTER=$(docker exec -it $UPF_CONTAINER sysctl -a | grep rp_filter)
echo "$RP_FILTER" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查UPF的IP轉發是否啟用
if ! echo "$IP_FORWARD" | grep -q "net.ipv4.ip_forward = 1"; then
    echo "問題: UPF未啟用IP轉發" | tee -a $REPORT_FILE
    echo "建議: 執行 './scripts/upf_setup.sh' 修復UPF配置" | tee -a $REPORT_FILE
fi

# 檢查UPF的rp_filter是否禁用
if echo "$RP_FILTER" | grep -q "net.ipv4.conf.all.rp_filter = 1"; then
    echo "問題: UPF的反向路徑過濾(rp_filter)未禁用，可能導致'Source IP-4 Spoofing'錯誤" | tee -a $REPORT_FILE
    echo "建議: 執行 './scripts/gtp_fix.sh' 解決IP源地址驗證問題" | tee -a $REPORT_FILE
fi

echo "UPF NAT規則:" | tee -a $LOG_FILE
docker exec -it $UPF_CONTAINER iptables -t nat -L -v | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UPF防火牆規則:" | tee -a $LOG_FILE
docker exec -it $UPF_CONTAINER iptables -L -v | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查UPF是否有ogstun接口
if ! docker exec -it $UPF_CONTAINER ip a | grep -q "ogstun"; then
    echo "問題: UPF中未找到ogstun接口，GTP隧道可能未建立" | tee -a $REPORT_FILE
else
    UPF_TUN_IP=$(docker exec -it $UPF_CONTAINER ip addr show dev ogstun | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
    echo "UPF ogstun IP地址: $UPF_TUN_IP" | tee -a $REPORT_FILE
fi

# 4. 檢查SMF和AMF配置
echo "== SMF和AMF配置 ==" | tee -a $LOG_FILE
echo "SMF日誌尾部 (最新50行):" | tee -a $LOG_FILE
SMF_LOG=$(docker exec -it $SMF_CONTAINER tail -n 50 /opt/open5gs/var/log/open5gs/smf.log)
echo "$SMF_LOG" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "AMF日誌尾部 (最新50行):" | tee -a $LOG_FILE
AMF_LOG=$(docker exec -it $AMF_CONTAINER tail -n 50 /opt/open5gs/var/log/open5gs/amf.log)
echo "$AMF_LOG" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查SMF日誌中的錯誤
if echo "$SMF_LOG" | grep -i "error\|fail\|reject"; then
    echo "SMF日誌中發現錯誤:" | tee -a $REPORT_FILE
    echo "$SMF_LOG" | grep -i "error\|fail\|reject" | tail -5 | tee -a $REPORT_FILE
fi

# 檢查AMF日誌中的錯誤
if echo "$AMF_LOG" | grep -i "error\|fail\|reject"; then
    echo "AMF日誌中發現錯誤:" | tee -a $REPORT_FILE
    echo "$AMF_LOG" | grep -i "error\|fail\|reject" | tail -5 | tee -a $REPORT_FILE
fi

# 5. 連接測試
echo "== 連接測試 ==" | tee -a $LOG_FILE
echo "從UE到UPF的ping測試:" | tee -a $LOG_FILE
UE_TO_UPF=$(docker exec -it $UE_CONTAINER ping -I uesimtun0 10.45.0.1 -c 4 2>&1)
echo "$UE_TO_UPF" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "從UPF到UE的ping測試:" | tee -a $LOG_FILE
UE_IP=$(docker exec -it $UE_CONTAINER ip addr show dev uesimtun0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
UPF_TO_UE=""
if [ ! -z "$UE_IP" ]; then
    UPF_TO_UE=$(docker exec -it $UPF_CONTAINER ping -I ogstun $UE_IP -c 4 2>&1 || echo "Ping失敗")
    echo "$UPF_TO_UE" | tee -a $LOG_FILE
else
    echo "無法獲取UE IP地址，跳過測試" | tee -a $LOG_FILE
fi
echo "" | tee -a $LOG_FILE

echo "從UE到DNS服務器的ping測試:" | tee -a $LOG_FILE
UE_TO_DNS=$(docker exec -it $UE_CONTAINER ping -I uesimtun0 8.8.8.8 -c 4 2>&1 || echo "Ping失敗")
echo "$UE_TO_DNS" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查連接性問題
if ! echo "$UE_TO_UPF" | grep -q "0% packet loss"; then
    echo "問題: UE無法ping通UPF (10.45.0.1)" | tee -a $REPORT_FILE
    echo "建議:" | tee -a $REPORT_FILE
    echo "1. 確認UE和UPF配置: ./scripts/ue_setup.sh 和 ./scripts/upf_setup.sh" | tee -a $REPORT_FILE
    echo "2. 修復GTP隧道: ./scripts/gtp_fix.sh" | tee -a $REPORT_FILE
    echo "3. 設置網絡橋接: ./scripts/network_bridge.sh" | tee -a $REPORT_FILE
fi

if [ ! -z "$UPF_TO_UE" ] && ! echo "$UPF_TO_UE" | grep -q "0% packet loss"; then
    echo "問題: UPF無法ping通UE ($UE_IP)" | tee -a $REPORT_FILE
    echo "建議: 執行 './scripts/gtp_fix.sh' 修復GTP隧道" | tee -a $REPORT_FILE
fi

if ! echo "$UE_TO_DNS" | grep -q "0% packet loss"; then
    echo "問題: UE無法訪問外部網絡 (8.8.8.8)" | tee -a $REPORT_FILE
    echo "建議:" | tee -a $REPORT_FILE
    echo "1. 確認UPF NAT規則: ./scripts/upf_setup.sh" | tee -a $REPORT_FILE
    echo "2. 使用API代理: ./scripts/setup_proxy_api.sh" | tee -a $REPORT_FILE
fi

# 6. 檢查Socket和GTP信息
echo "== Socket和GTP信息 ==" | tee -a $LOG_FILE
echo "UPF GTPU Socket:" | tee -a $LOG_FILE
docker exec -it $UPF_CONTAINER ss -anup | grep 2152 | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "UPF PFCP Socket:" | tee -a $LOG_FILE
docker exec -it $UPF_CONTAINER ss -anup | grep 8805 | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

echo "SMF PFCP Socket:" | tee -a $LOG_FILE
docker exec -it $SMF_CONTAINER ss -anup | grep 8805 | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 檢查GTP端口是否開放
if ! docker exec -it $UPF_CONTAINER ss -anup | grep -q "2152"; then
    echo "問題: UPF的GTP-U端口 (2152) 未開放" | tee -a $REPORT_FILE
    echo "建議: 檢查UPF防火牆規則和服務狀態" | tee -a $REPORT_FILE
fi

# 7. 總結報告
echo "===================================================" >> $REPORT_FILE
echo "診斷總結:" >> $REPORT_FILE

# 檢查是否有報告問題
if grep -q "問題:" $REPORT_FILE; then
    echo "發現以下問題需要解決:" >> $REPORT_FILE
    grep -A2 "問題:" $REPORT_FILE >> $REPORT_FILE
    
    echo -e "\n建議的解決方案:" >> $REPORT_FILE
    echo "1. 執行 './scripts/ntn_startup.sh' 全面重置和配置系統" >> $REPORT_FILE
    echo "2. 手動執行個別修復腳本解決特定問題" >> $REPORT_FILE
else
    echo "未發現明顯問題，系統似乎正常運行" >> $REPORT_FILE
fi

echo "===========================================================" | tee -a $LOG_FILE
echo "網絡診斷完成: $(date)" | tee -a $LOG_FILE
echo "詳細診斷結果已保存到: $LOG_FILE" | tee -a $LOG_FILE
echo "診斷報告已保存到: $REPORT_FILE" | tee -a $LOG_FILE

# 顯示診斷報告
echo ""
echo "診斷報告概要:"
echo "==========================================================="
cat $REPORT_FILE
echo "==========================================================="
echo ""
echo "如需查看完整診斷結果，請使用: cat $LOG_FILE" 