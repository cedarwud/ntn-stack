#!/bin/bash

# NTN網絡啟動腳本
# 本腳本將執行所有必要的步驟以啟動高延遲容錯NTN網絡
# 包括: 容器啟動、UPF配置、UE配置、網絡橋接及網絡模擬器設置

set -e

DELAY_MODE=${1:-"sat"}  # 默認為衛星模式 (sat 或 ground)

echo "===== NTN高延遲容錯網絡啟動 - 模式: $DELAY_MODE ====="
echo "$(date)"
echo

# 1. 確保系統已啟動
echo "確認系統狀態..."
CONTAINER_COUNT=$(docker ps | grep "ntn-stack" | wc -l)
if [ "$CONTAINER_COUNT" -lt 10 ]; then
    echo "系統未完全啟動，正在啟動容器..."
    docker compose down
    docker compose up -d
    
    # 等待系統啟動 (最多等待90秒)
    MAX_WAIT=90
    echo "等待系統啟動 (最多 $MAX_WAIT 秒)..."
    for i in $(seq 1 $MAX_WAIT); do
        CONTAINER_COUNT=$(docker ps | grep "ntn-stack" | wc -l)
        if [ "$CONTAINER_COUNT" -ge 10 ]; then
            echo "系統已成功啟動!"
            break
        fi
        
        echo -n "."
        sleep 1
        
        if [ "$i" -eq "$MAX_WAIT" ]; then
            echo "系統啟動超時，請手動檢查系統狀態"
            exit 1
        fi
    done
    echo
    
    # 額外等待10秒，確保所有服務完全初始化
    echo "等待服務初始化...(10秒)"
    sleep 10
    
    # 確保ntn-proxy服務啟動
    echo "確保ntn-proxy服務啟動..."
    docker compose up -d ntn-proxy
fi

# 2. 在宿主機上設置必要的系統參數
echo "在宿主機上設置系統參數..."
sudo sysctl -w net.ipv4.conf.all.rp_filter=0 || echo "無法在宿主機上設置rp_filter，可能需要以root權限運行"
sudo sysctl -w net.ipv4.ip_forward=1 || echo "無法在宿主機上啟用IP轉發，可能需要以root權限運行"

# 3. 運行UPF設置腳本
echo "配置UPF..."
bash ./scripts/upf_setup.sh
echo

# 4. 創建網絡橋接
echo "配置網絡橋接..."
bash ./scripts/network_bridge.sh
echo 

# 5. 運行UE設置腳本
echo "配置UE..."
bash ./scripts/ue_setup.sh
echo

# 6. 修復GTP通信問題
echo "修復GTP通信問題..."
bash ./scripts/gtp_fix.sh
echo

# 7. 配置UE代理通信
echo "配置UE代理通信..."
bash ./scripts/proxy_ue_traffic.sh
echo

# 8. 應用NTN模擬器
echo "配置NTN環境模擬..."
if [ "$DELAY_MODE" == "ground" ]; then
    bash ./scripts/ntn_simulator.sh --mode=ground
else
    bash ./scripts/ntn_simulator.sh --mode=sat
fi
echo

# 9. 啟動API代理服務
echo "啟動API代理服務..."
if ! docker ps | grep -q "ntn-proxy"; then
    echo "ntn-proxy服務未運行，正在啟動..."
    docker compose up -d ntn-proxy
else
    echo "ntn-proxy服務已運行"
fi
echo

# 10. 運行增強版UE修復腳本
echo "運行增強版UE修復腳本..."
bash ./scripts/ntn_sat_ue_fix.sh
echo

# 11. 啟動自動恢復服務（一次性模式）
echo "運行自動恢復服務..."
bash ./scripts/ue_auto_recovery.sh once
echo

# 12. 運行網絡診斷
echo "執行網絡診斷..."
bash ./scripts/network_diagnostic.sh
echo

# 13. 完成
echo "===== NTN高延遲容錯網絡啟動完成 ====="
echo "網絡模式: $DELAY_MODE"
echo "您可以通過以下命令進行測試："
echo "1. 測試UE基本連接: docker exec -it ntn-stack-ues1-1 ping -I uesimtun0 10.45.0.1"
echo "2. 測試UE外部連接: docker exec -it ntn-stack-ues1-1 curl http://ntn-proxy:8888/api/proxy/http?url=https://example.com"
echo "3. 運行性能測試: ./scripts/performance_test.sh --mode=both"
echo "4. 切換網絡環境: ./scripts/ntn_simulator.sh --mode=[ground|leo|meo|geo]"
echo "5. 診斷與修復: ./scripts/ntn_setup.sh fix"
echo "6. 啟動持續自動恢復: nohup ./scripts/ue_auto_recovery.sh daemon > auto_recovery.log 2>&1 &" 