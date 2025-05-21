#!/bin/bash

# NTN (非地面網絡) 模擬器
# 此腳本用於模擬非地面網絡（如衛星通信）的環境特性
# 包括延遲、抖動、丟包、帶寬限制和週期性中斷等特性

set -e

# 默認參數
MODE="sat"        # 模式：sat (衛星) 或 ground (地面)
DELAY=250         # 單向延遲（毫秒）
JITTER=50         # 延遲抖動（毫秒）
LOSS=2            # 丟包率（百分比）
BANDWIDTH=10      # 帶寬限制 (Mbps)
CONTAINER_GNB="gnb1" # 默認gNodeB容器名
CONTAINER_UE="ntn-stack-ues1-1" # 默認UE容器名
BURST=false       # 是否啟用周期性中斷模擬

# 預設配置
SAT_LEO_DELAY=250     # LEO衛星延遲
SAT_MEO_DELAY=500     # MEO衛星延遲
SAT_GEO_DELAY=750     # GEO衛星延遲
GROUND_DELAY=50       # 地面延遲

# 解析命令行參數
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --delay=*)
            DELAY="${key#*=}"
            shift
            ;;
        --jitter=*)
            JITTER="${key#*=}"
            shift
            ;;
        --loss=*)
            LOSS="${key#*=}"
            shift
            ;;
        --bandwidth=*)
            BANDWIDTH="${key#*=}"
            shift
            ;;
        --gnb=*)
            CONTAINER_GNB="${key#*=}"
            shift
            ;;
        --ue=*)
            CONTAINER_UE="${key#*=}"
            shift
            ;;
        --mode=*)
            MODE="${key#*=}"
            shift
            ;;
        --burst=*)
            BURST="${key#*=}"
            shift
            ;;
        --help)
            echo "用法: $0 [選項]"
            echo "選項:"
            echo "  --mode=TYPE      選擇模式：sat（衛星）或ground（地面）（默認：sat）"
            echo "                   sat模式還可以指定：leo, meo, geo（不同軌道高度的衛星）"
            echo "  --delay=N        設置單向延遲為N毫秒（默認：衛星250ms，地面50ms）"
            echo "  --jitter=N       設置延遲抖動為N毫秒（默認：衛星50ms，地面10ms）"
            echo "  --loss=N         設置丟包率為N%（默認：衛星2%，地面0.5%）"
            echo "  --bandwidth=N    設置帶寬限制為N Mbps（默認：衛星10Mbps，地面50Mbps）"
            echo "  --gnb=NAME       指定gNodeB容器名稱（默認：gnb1）"
            echo "  --ue=NAME        指定UE容器名稱（默認：ntn-stack-ues1-1）"
            echo "  --burst=BOOL     是否啟用周期性中斷模擬（true/false，默認：false）"
            echo "  --help           顯示此幫助信息"
            echo ""
            echo "預設模式:"
            echo "  --mode=leo       低軌道衛星配置（延遲250ms，抖動50ms，丟包2%）"
            echo "  --mode=meo       中軌道衛星配置（延遲500ms，抖動80ms，丟包3%）"
            echo "  --mode=geo       地球同步軌道衛星配置（延遲750ms，抖動100ms，丟包5%）"
            echo "  --mode=ground    地面網絡配置（延遲50ms，抖動10ms，丟包0.5%）"
            exit 0
            ;;
        *)
            echo "未知選項: $key"
            exit 1
            ;;
    esac
done

# 根據模式設置參數
case "$MODE" in
    "ground")
        DELAY=$GROUND_DELAY
        JITTER=10
        LOSS=0.5
        BANDWIDTH=50
        echo "使用地面模式設置：延遲=${DELAY}ms, 抖動=${JITTER}ms, 丟包率=${LOSS}%, 帶寬=${BANDWIDTH}Mbps"
        ;;
    "leo")
        DELAY=$SAT_LEO_DELAY
        JITTER=50
        LOSS=2
        BANDWIDTH=10
        echo "使用低軌道衛星(LEO)設置：延遲=${DELAY}ms, 抖動=${JITTER}ms, 丟包率=${LOSS}%, 帶寬=${BANDWIDTH}Mbps"
        ;;
    "meo")
        DELAY=$SAT_MEO_DELAY
        JITTER=80
        LOSS=3
        BANDWIDTH=8
        echo "使用中軌道衛星(MEO)設置：延遲=${DELAY}ms, 抖動=${JITTER}ms, 丟包率=${LOSS}%, 帶寬=${BANDWIDTH}Mbps"
        ;;
    "geo")
        DELAY=$SAT_GEO_DELAY
        JITTER=100
        LOSS=5
        BANDWIDTH=5
        echo "使用地球同步軌道衛星(GEO)設置：延遲=${DELAY}ms, 抖動=${JITTER}ms, 丟包率=${LOSS}%, 帶寬=${BANDWIDTH}Mbps"
        ;;
    "sat")
        echo "使用衛星模式設置：延遲=${DELAY}ms, 抖動=${JITTER}ms, 丟包率=${LOSS}%, 帶寬=${BANDWIDTH}Mbps"
        ;;
    *)
        echo "未知模式: $MODE，使用默認衛星設置"
        ;;
esac

# 檢查容器是否運行
check_container() {
    if ! docker ps | grep -q "$1"; then
        echo "錯誤：容器 $1 未運行"
        exit 1
    fi
}

# 獲取容器網絡接口
get_container_interface() {
    docker exec "$1" ip route | grep default | awk '{print $5}'
}

# 設置網絡延遲、丟包和帶寬限制
set_network_conditions() {
    local container=$1
    local interface=$2
    
    # 重置現有的tc設置
    docker exec "$container" tc qdisc del dev "$interface" root 2>/dev/null || true
    
    # 如果啟用了帶寬限制
    if [ $BANDWIDTH -gt 0 ]; then
        # 先創建HTB根節點
        docker exec "$container" tc qdisc add dev "$interface" root handle 1: htb default 10
        docker exec "$container" tc class add dev "$interface" parent 1: classid 1:10 htb rate ${BANDWIDTH}mbit
        
        # 然後添加延遲、抖動和丟包
        if [ "$BURST" = "true" ]; then
            # 添加周期性中斷模擬 - 每30秒中斷3秒
            docker exec "$container" tc qdisc add dev "$interface" parent 1:10 handle 10: netem \
                delay ${DELAY}ms ${JITTER}ms distribution normal \
                loss random ${LOSS}% \
                corrupt 0.1% \
                duplicate 0.1% \
                reorder 0.5% \
                gap 1000 offset 100
        else
            # 常規設置
            docker exec "$container" tc qdisc add dev "$interface" parent 1:10 handle 10: netem \
                delay ${DELAY}ms ${JITTER}ms distribution normal \
                loss random ${LOSS}% \
                corrupt 0.1% \
                duplicate 0.1% \
                reorder 0.5%
        fi
    else
        # 不限制帶寬，只添加延遲和丟包
        docker exec "$container" tc qdisc add dev "$interface" root netem \
            delay ${DELAY}ms ${JITTER}ms distribution normal \
            loss random ${LOSS}% \
            corrupt 0.1% \
            duplicate 0.1% \
            reorder 0.5%
    fi
    
    echo "已成功設置 $container 的網絡條件："
    docker exec "$container" tc qdisc show dev "$interface"
}

# 主函數
main() {
    echo "開始設置NTN網絡環境模擬..."
    
    # 檢查容器是否存在
    check_container "$CONTAINER_GNB"
    check_container "$CONTAINER_UE"
    
    # 獲取網絡接口
    GNB_INTERFACE=$(get_container_interface "$CONTAINER_GNB")
    UE_INTERFACE=$(docker exec -it $CONTAINER_UE ip link | grep "eth0" | head -1 | awk '{print $2}' | sed 's/://')
    if [ -z "$UE_INTERFACE" ]; then
        UE_INTERFACE="eth0"  # 默認使用eth0作為備選接口
    fi
    
    echo "gNodeB接口: $GNB_INTERFACE"
    echo "UE接口: $UE_INTERFACE"
    
    # 設置gNodeB延遲
    set_network_conditions "$CONTAINER_GNB" "$GNB_INTERFACE"
    
    # 設置UE容器延遲
    echo "設置UE容器網絡條件..."
    set_network_conditions "$CONTAINER_UE" "$UE_INTERFACE"
    
    echo "NTN網絡環境模擬設置完成。"
    echo "模式: $MODE"
    echo "延遲: ${DELAY}ms"
    echo "抖動: ${JITTER}ms"
    echo "丟包率: ${LOSS}%"
    echo "帶寬限制: ${BANDWIDTH}Mbps"
    
    echo "可通過以下命令測試連接狀態："
    echo "  docker exec -it $CONTAINER_UE ping -I uesimtun0 10.45.0.1 -c 20"
    echo "  docker exec -it $CONTAINER_UE ping -I uesimtun0 8.8.8.8 -c 10"
    echo "查看UE連接狀態："
    echo "  docker exec -it $CONTAINER_UE nr-cli imsi-999700000000001 -e \"status\""
}

main 