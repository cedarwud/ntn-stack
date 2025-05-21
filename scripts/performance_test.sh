#!/bin/bash

# 5G NTN性能測試腳本
# 用於比較不同網絡條件下的5G網絡性能

set -e

# 默認參數
UE_CONTAINER="ntn-stack-ues1-1"
TEST_DURATION=60  # 測試時間（秒）
OUTPUT_DIR="./performance_results"
TEST_MODE="both"  # sat, ground, both

# 解析命令行參數
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --ue=*)
            UE_CONTAINER="${key#*=}"
            shift
            ;;
        --duration=*)
            TEST_DURATION="${key#*=}"
            shift
            ;;
        --output=*)
            OUTPUT_DIR="${key#*=}"
            shift
            ;;
        --mode=*)
            TEST_MODE="${key#*=}"
            shift
            ;;
        --help)
            echo "用法: $0 [選項]"
            echo "選項:"
            echo "  --ue=NAME        指定UE容器名稱（默認：ntn-stack-ues1-1）"
            echo "  --duration=N     測試持續時間，秒（默認：60）"
            echo "  --output=DIR     結果輸出目錄（默認：./performance_results）"
            echo "  --mode=TYPE      測試模式：sat（衛星）、ground（地面）或both（兩者）（默認：both）"
            echo "  --help           顯示此幫助信息"
            exit 0
            ;;
        *)
            echo "未知選項: $key"
            exit 1
            ;;
    esac
done

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="$OUTPUT_DIR/performance_test_$TIMESTAMP.log"

# 檢查UE容器是否運行
if ! docker ps | grep -q "$UE_CONTAINER"; then
    echo "錯誤：UE容器 $UE_CONTAINER 未運行"
    exit 1
fi

# 檢查uesimtun0介面是否存在
if ! docker exec "$UE_CONTAINER" ip a | grep -q "uesimtun0"; then
    echo "錯誤：uesimtun0介面在UE容器中不存在，請確保UE已成功註冊到網絡"
    exit 1
fi

# 記錄系統信息
log_system_info() {
    {
        echo "===== 測試開始時間: $(date) ====="
        echo "UE容器: $UE_CONTAINER"
        echo "測試時長: $TEST_DURATION 秒"
        echo ""
        
        echo "===== UE連接狀態 ====="
        docker exec "$UE_CONTAINER" nr-cli imsi-999700000000001 -e "status" || echo "無法獲取狀態信息"
        echo ""
        
        echo "===== 網絡接口信息 ====="
        docker exec "$UE_CONTAINER" ip a show dev uesimtun0 || echo "無法獲取介面信息"
        echo ""
    } >> "$RESULT_FILE"
}

# 執行ping測試
run_ping_test() {
    local mode=$1
    local count=20
    
    {
        echo "===== PING測試 ($mode模式) ====="
        echo "開始時間: $(date)"
        docker exec "$UE_CONTAINER" ping -I uesimtun0 8.8.8.8 -c $count -i 1
        echo "結束時間: $(date)"
        echo ""
    } >> "$RESULT_FILE"
}

# 執行iperf測試
run_iperf_test() {
    local mode=$1
    local server_ip="10.45.0.1"  # 使用UPF的IP作為目標
    
    # 啟動暫時的iperf服務器
    echo "啟動iperf服務器..." >> "$RESULT_FILE"
    
    # 在背景啟動iperf服務器
    docker run --rm --name=iperf-server --network=open5gs-net -d nicolaka/netshoot iperf -s
    IPERF_SERVER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' iperf-server)
    
    sleep 2
    
    {
        echo "===== IPERF吞吐量測試 ($mode模式) ====="
        echo "開始時間: $(date)"
        echo "iperf服務器IP: $IPERF_SERVER_IP"
        
        # TCP測試
        echo "--- TCP測試 ---"
        docker exec "$UE_CONTAINER" iperf -c "$IPERF_SERVER_IP" -t 10 -i 1
        
        # UDP測試
        echo "--- UDP測試 ---"
        docker exec "$UE_CONTAINER" iperf -c "$IPERF_SERVER_IP" -u -b 5M -t 10 -i 1
        
        echo "結束時間: $(date)"
        echo ""
    } >> "$RESULT_FILE"
    
    # 停止iperf服務器
    docker stop iperf-server
}

# 執行延遲穩定性測試
run_latency_stability_test() {
    local mode=$1
    local duration=30  # 持續30秒
    
    {
        echo "===== 延遲穩定性測試 ($mode模式) ====="
        echo "開始時間: $(date)"
        echo "持續時間: $duration 秒"
        
        # 連續ping測試
        docker exec "$UE_CONTAINER" ping -I uesimtun0 8.8.8.8 -c $duration -i 1
        
        echo "結束時間: $(date)"
        echo ""
    } >> "$RESULT_FILE"
}

# 主測試流程
main() {
    echo "開始性能測試，結果將保存到: $RESULT_FILE"
    echo "測試開始..." > "$RESULT_FILE"
    
    # 記錄基本系統信息
    log_system_info
    
    # 地面模式測試
    if [[ "$TEST_MODE" == "ground" || "$TEST_MODE" == "both" ]]; then
        echo "配置地面模式網絡條件..."
        ./scripts/ntn_simulator.sh --mode=ground
        sleep 5
        
        run_ping_test "地面"
        run_iperf_test "地面"
        run_latency_stability_test "地面"
    fi
    
    # 衛星模式測試
    if [[ "$TEST_MODE" == "sat" || "$TEST_MODE" == "both" ]]; then
        echo "配置衛星模式網絡條件..."
        ./scripts/ntn_simulator.sh --mode=sat
        sleep 5
        
        run_ping_test "衛星"
        run_iperf_test "衛星"
        run_latency_stability_test "衛星"
    fi
    
    echo "===== 測試完成 =====" >> "$RESULT_FILE"
    echo "結果已保存到: $RESULT_FILE"
}

main 