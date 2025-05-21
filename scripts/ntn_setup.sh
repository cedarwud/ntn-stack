#!/bin/bash

# NTN網絡總體設置腳本
# 此腳本提供了一個統一的界面來配置和管理NTN網絡
# 包括啟動系統、切換網絡模式、診斷問題和性能測試

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 無顏色

# 使用幫助函數
show_help() {
    echo -e "${BLUE}NTN網絡總體設置工具${NC}"
    echo "此腳本提供了一個統一的界面來配置和管理NTN網絡"
    echo ""
    echo "用法: $0 [命令] [選項]"
    echo ""
    echo "可用命令:"
    echo "  start          啟動NTN網絡 (默認為衛星模式)"
    echo "  stop           停止系統"
    echo "  restart        重啟系統"
    echo "  mode <模式>    切換網絡模式 (可選: sat, leo, meo, geo, ground)"
    echo "  diagnose       執行網絡診斷"
    echo "  test           執行性能測試"
    echo "  fix            嘗試修復常見問題"
    echo "  status         顯示系統狀態"
    echo "  help           顯示此幫助信息"
    echo ""
    echo "示例:"
    echo "  $0 start                  - 以默認配置啟動NTN網絡"
    echo "  $0 start leo              - 以LEO衛星模式啟動NTN網絡"
    echo "  $0 mode ground            - 切換到地面網絡模式"
    echo "  $0 diagnose               - 執行網絡診斷"
    echo "  $0 fix                    - 嘗試修復常見問題"
    echo ""
}

# 啟動網絡功能
start_network() {
    local mode=${1:-"sat"}
    echo -e "${GREEN}正在啟動NTN網絡 (模式: $mode)...${NC}"
    
    # 調用ntn_startup.sh腳本
    ./scripts/ntn_startup.sh $mode
    
    echo -e "${GREEN}NTN網絡啟動完成!${NC}"
}

# 停止系統功能
stop_system() {
    echo -e "${YELLOW}正在停止系統...${NC}"
    
    # 停止所有容器
    docker compose down
    
    echo -e "${GREEN}系統已停止${NC}"
}

# 重啟系統功能
restart_system() {
    echo -e "${YELLOW}正在重啟系統...${NC}"
    
    # 先停止系統
    stop_system
    
    # 等待幾秒鐘
    echo "等待系統關閉..."
    sleep 3
    
    # 再啟動系統 (使用默認模式或指定模式)
    local mode=${1:-"sat"}
    start_network $mode
    
    echo -e "${GREEN}系統已重啟${NC}"
}

# 切換網絡模式功能
switch_mode() {
    local mode=$1
    
    if [ -z "$mode" ]; then
        echo -e "${RED}錯誤: 未指定網絡模式${NC}"
        echo "可用模式: sat, leo, meo, geo, ground"
        return 1
    fi
    
    case "$mode" in
        sat|leo|meo|geo|ground)
            echo -e "${YELLOW}正在切換到 $mode 模式...${NC}"
            ./scripts/ntn_simulator.sh --mode=$mode
            echo -e "${GREEN}已切換到 $mode 模式${NC}"
            ;;
        *)
            echo -e "${RED}錯誤: 未知的網絡模式 '$mode'${NC}"
            echo "可用模式: sat, leo, meo, geo, ground"
            return 1
            ;;
    esac
}

# 執行網絡診斷功能
run_diagnosis() {
    echo -e "${YELLOW}正在執行網絡診斷...${NC}"
    
    # 調用診斷腳本
    ./scripts/network_diagnostic.sh
    
    echo -e "${GREEN}診斷完成${NC}"
}

# 執行性能測試功能
run_performance_test() {
    local mode=${1:-"both"}
    
    echo -e "${YELLOW}正在執行性能測試 (模式: $mode)...${NC}"
    
    # 調用性能測試腳本
    if [ -f "./scripts/performance_test.sh" ]; then
        ./scripts/performance_test.sh --mode=$mode
    else
        echo -e "${RED}錯誤: 性能測試腳本不存在${NC}"
        return 1
    fi
    
    echo -e "${GREEN}性能測試完成${NC}"
}

# 修復常見問題功能
fix_common_issues() {
    echo -e "${YELLOW}正在嘗試修復常見問題...${NC}"
    
    # 1. 修復GTP隧道
    echo -e "${BLUE}1. 修復GTP隧道...${NC}"
    ./scripts/gtp_fix.sh
    
    # 2. 重新配置UE
    echo -e "${BLUE}2. 重新配置UE...${NC}"
    ./scripts/ue_setup.sh
    
    # 3. 重新配置UPF
    echo -e "${BLUE}3. 重新配置UPF...${NC}"
    ./scripts/upf_setup.sh
    
    # 4. 設置網絡橋接
    echo -e "${BLUE}4. 設置網絡橋接...${NC}"
    ./scripts/network_bridge.sh
    
    # 5. 配置代理服務
    echo -e "${BLUE}5. 配置代理服務...${NC}"
    ./scripts/setup_proxy_api.sh
    
    echo -e "${GREEN}修復嘗試完成!${NC}"
    echo "請使用 '$0 diagnose' 命令檢查是否解決了問題"
}

# 顯示系統狀態功能
show_status() {
    echo -e "${BLUE}系統狀態:${NC}"
    echo "======================="
    
    # 檢查容器運行狀態
    echo -e "${YELLOW}容器狀態:${NC}"
    docker ps | grep -E "ntn-stack|gnb|ue"
    
    # 簡單的UE診斷
    echo -e "\n${YELLOW}UE連接狀態:${NC}"
    if docker ps | grep -q "ntn-stack-ues1-1"; then
        docker exec -it ntn-stack-ues1-1 nr-cli imsi-999700000000001 -e "status" 2>/dev/null || echo "無法獲取UE狀態"
        docker exec -it ntn-stack-ues1-1 ip addr show dev uesimtun0 2>/dev/null || echo "uesimtun0接口未創建"
    else
        echo "UE容器未運行"
    fi
    
    # 簡單的連接性測試
    echo -e "\n${YELLOW}基本連接性:${NC}"
    if docker ps | grep -q "ntn-stack-ues1-1"; then
        echo "從UE到UPF的PING:"
        docker exec -it ntn-stack-ues1-1 ping -I uesimtun0 10.45.0.1 -c 2 2>/dev/null || echo "Ping失敗"
    else
        echo "UE容器未運行"
    fi
    
    echo -e "\n${YELLOW}當前網絡模式:${NC}"
    # 嘗試從正在運行的配置中確定網絡模式
    if docker ps | grep -q "gnb1"; then
        GNB_DELAY=$(docker exec -it gnb1 tc qdisc show dev eth0 2>/dev/null | grep -oP 'delay \K[0-9.]+ms' | cut -d'.' -f1 | head -1)
        
        if [ -z "$GNB_DELAY" ]; then
            echo "未檢測到延遲設置"
        elif [ "$GNB_DELAY" -lt 100 ]; then
            echo "當前模式: ground (地面網絡)"
        elif [ "$GNB_DELAY" -lt 400 ]; then
            echo "當前模式: leo/sat (低軌道衛星)"
        elif [ "$GNB_DELAY" -lt 600 ]; then
            echo "當前模式: meo (中軌道衛星)"
        else
            echo "當前模式: geo (地球同步軌道衛星)"
        fi
    else
        echo "GNB容器未運行"
    fi
    
    echo "======================="
}

# 主函數
main() {
    local command=$1
    local option=$2
    
    # 如果沒有命令，顯示幫助信息
    if [ -z "$command" ]; then
        show_help
        return 0
    fi
    
    # 根據命令執行相應的操作
    case "$command" in
        start)
            start_network $option
            ;;
        stop)
            stop_system
            ;;
        restart)
            restart_system $option
            ;;
        mode)
            switch_mode $option
            ;;
        diagnose)
            run_diagnosis
            ;;
        test)
            run_performance_test $option
            ;;
        fix)
            fix_common_issues
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}錯誤: 未知命令 '$command'${NC}"
            show_help
            return 1
            ;;
    esac
}

# 執行主函數
main "$@" 