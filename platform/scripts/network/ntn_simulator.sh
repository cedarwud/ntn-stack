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

# 新增：處理位置參數作為模式
if [[ "$1" == "leo" || "$1" == "meo" || "$1" == "geo" || "$1" == "ground" || "$1" == "default" ]]; then
    MODE="$1"
    echo "檢測到位置參數模式: $MODE"
    shift  # 消耗掉模式參數
    # 如果模式是 default，則重置為 ground，因為 default 通常意味著清除或恢復到基線
    if [[ "$MODE" == "default" ]]; then
        MODE="ground"
        echo "模式 'default' 被解釋為 'ground'"
    fi
elif [[ -n "$1" && $1 != --* ]]; then # 如果第一個參數存在且不是以 -- 開頭的選項
    echo "警告：檢測到未知的位置參數 '$1'。如果這是一個模式，請確保它是 leo, meo, geo, ground, 或 default。"
    echo "將繼續使用默認模式: $MODE 或通過 --mode 指定的模式。"
fi

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
            if [[ "$MODE" == "default" ]]; then # 如果通過 --mode=default 指定
                MODE="ground" # 也將 default 解釋為 ground
                echo "模式 'default' (通過 --mode 指定) 被解釋為 'ground'"
            fi
            shift
            ;;
        --burst=*)
            BURST="${key#*=}"
            shift
            ;;
        --help)
            echo "用法: $0 [模式] [選項] 或 $0 [選項] --mode=模式"
            echo "模式 (可作為第一個位置參數): leo, meo, geo, ground, default"
            echo "選項:"
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
    local container=$1
    
    # 特殊處理UE容器
    if [[ "$container" == *"ues"* ]]; then
        # 對於UE容器，我們直接使用eth0，因為tc命令不支持@if格式的接口名
        echo "eth0"
        return
    fi
    
    # 對於GNB和其他容器
    interface=$(docker exec $container ip route 2>/dev/null | grep default | awk '{print $5}')
    
    # 如果沒有找到接口，使用默認值
    if [ -z "$interface" ]; then
        interface="eth0"
    fi
    
    echo $interface
}

# 設置網絡延遲、丟包和帶寬限制
set_network_conditions() {
    local container=$1
    local interface=$2
    
    # 檢查接口是否存在
    if ! docker exec $container ip link show dev "$interface" >/dev/null 2>&1; then
        echo "警告: 在容器 $container 中找不到接口 $interface，跳過設置"
        return 1
    fi
    
    # 重置現有的tc設置
    docker exec $container tc qdisc del dev "$interface" root 2>/dev/null || true
    
    # 如果啟用了帶寬限制
    if [ $BANDWIDTH -gt 0 ]; then
        # 先創建HTB根節點
        docker exec $container tc qdisc add dev "$interface" root handle 1: htb default 10
        docker exec $container tc class add dev "$interface" parent 1: classid 1:10 htb rate ${BANDWIDTH}mbit
        
        # 然後添加延遲、抖動和丟包
        if [ "$BURST" = "true" ]; then
            # 添加周期性中斷模擬 - 使用更合適的參數
            docker exec $container tc qdisc add dev "$interface" parent 1:10 handle 10: netem \
                delay ${DELAY}ms ${JITTER}ms distribution normal \
                loss random ${LOSS}% \
                corrupt 0.1% \
                duplicate 0.1% \
                reorder 0.5% \
                gap 1000
        else
            # 常規設置
            docker exec $container tc qdisc add dev "$interface" parent 1:10 handle 10: netem \
                delay ${DELAY}ms ${JITTER}ms distribution normal \
                loss random ${LOSS}% \
                corrupt 0.1% \
                duplicate 0.1% \
                reorder 0.5%
        fi
    else
        # 不限制帶寬，只添加延遲和丟包
        docker exec $container tc qdisc add dev "$interface" root netem \
            delay ${DELAY}ms ${JITTER}ms distribution normal \
            loss random ${LOSS}% \
            corrupt 0.1% \
            duplicate 0.1% \
            reorder 0.5%
    fi
    
    echo "已成功設置 $container 的網絡條件："
    docker exec $container tc qdisc show dev "$interface"
    return 0
}

# 主函數
main() {
    echo "開始設置NTN網絡環境模擬..."
    
    # 檢查容器是否存在
    check_container "$CONTAINER_GNB"
    check_container "$CONTAINER_UE"
    
    # 獲取網絡接口
    GNB_INTERFACE=$(get_container_interface "$CONTAINER_GNB")
    UE_INTERFACE=$(get_container_interface "$CONTAINER_UE")
    
    echo "gNodeB接口: $GNB_INTERFACE"
    echo "UE接口: $UE_INTERFACE"
    
    # 設置gNodeB延遲
    set_network_conditions "$CONTAINER_GNB" "$GNB_INTERFACE"
    GNB_SUCCESS=$?
    
    # 設置UE容器延遲
    echo "設置UE容器網絡條件..."
    set_network_conditions "$CONTAINER_UE" "$UE_INTERFACE"
    UE_SUCCESS=$?
    
    # 顯示最終結果
    echo "NTN網絡環境模擬設置狀態:"
    echo "模式: $MODE"
    echo "延遲: ${DELAY}ms"
    echo "抖動: ${JITTER}ms"
    echo "丟包率: ${LOSS}%"
    echo "帶寬限制: ${BANDWIDTH}Mbps"
    
    # 如果兩個設置都成功，顯示測試命令
    if [ $GNB_SUCCESS -eq 0 ] && [ $UE_SUCCESS -eq 0 ]; then
        echo "設置成功，可通過以下命令測試連接狀態："
        echo "  docker exec $CONTAINER_UE ping -I uesimtun0 10.45.0.1 -c 5"
        echo "  docker exec $CONTAINER_UE ping -I uesimtun0 8.8.8.8 -c 5"
        echo "查看UE連接狀態："
        echo "  docker exec $CONTAINER_UE nr-cli imsi-999700000000001 -e \"status\""
    else
        echo "警告: 部分網絡條件設置失敗，請檢查容器接口配置"
    fi
}

main 