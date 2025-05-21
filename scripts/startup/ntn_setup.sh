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

# 腳本路徑常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 各模塊腳本路徑
STARTUP_DIR="$ROOT_DIR/scripts/startup"
NETWORK_DIR="$ROOT_DIR/scripts/network"  
DIAGNOSTIC_DIR="$ROOT_DIR/scripts/diagnostic"
CONFIG_DIR="$ROOT_DIR/scripts/config"
RECOVERY_DIR="$ROOT_DIR/scripts/recovery"
PROXY_DIR="$ROOT_DIR/scripts/proxy"
TESTING_DIR="$ROOT_DIR/scripts/testing"

# 日誌函數
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1" 
}

log_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $1" 
}

log_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $1" 
}

log_error() { 
    echo -e "${RED}[ERROR]${NC} $1" 
}

# 使用幫助函數
show_help() {
    echo -e "${GREEN}NTN（非地面網絡）系統管理腳本${NC}"
    echo 
    echo "用法: $0 [命令] [選項]"
    echo
    echo "命令:"
    echo "  start [模式]    啟動NTN網絡 (可選模式: sat, leo, meo, geo, ground)"
    echo "  stop            停止NTN網絡"
    echo "  restart [模式]  重新啟動NTN網絡"
    echo "  status          顯示NTN網絡狀態"
    echo "  logs [服務]     查看服務日誌 (可選服務: all, gnb, ue, upf, smf, amf)"
    echo "  shell [服務]    進入服務的shell (可選服務: gnb, ue, upf, smf, amf)"
    echo "  mode <模式>    切換網絡模式 (可選: sat, leo, meo, geo, ground)"
    echo "  sim <選項>     運行網絡模擬器 (選項將傳遞給ntn_simulator.sh)"
    echo "  diagnose       執行網絡診斷"
    echo "  fix            執行問題修復"
    echo "  perf [模式]    執行性能測試 (可選模式: both, uplink, downlink)"
    echo "  config [模式]  生成並應用網絡模式配置 (可選: leo, meo, geo, ground)"
    echo "  help           顯示此幫助信息"
    echo
    echo "示例:"
    echo "  $0 start leo             - 啟動NTN網絡，使用LEO衛星模式"
    echo "  $0 status                - 顯示NTN網絡狀態"
    echo "  $0 logs gnb              - 顯示gNodeB日誌"
    echo "  $0 mode ground            - 切換到地面網絡模式"
    echo "  $0 config leo --sat-lat 23.5 --sat-lon 120.3  - 生成並應用LEO模式配置，帶衛星位置參數"
    echo
    echo "動態配置功能:"
    echo "  系統現在支持根據網絡模式自動生成和應用最佳配置"
    echo "  - 當切換網絡模式時，將自動生成並應用對應模式的配置"
    echo "  - 通過'config'命令可直接指定配置參數"
    echo "  - 支持根據衛星位置動態計算配置參數"
}

# 啟動網絡功能
start_network() {
    local mode=${1:-"sat"}
    echo -e "${GREEN}正在啟動NTN網絡 (模式: $mode)...${NC}"
    
    # 調用ntn_startup.sh腳本
    "$STARTUP_DIR/ntn_startup.sh" $mode
    
    # 確保ntn-proxy服務啟動
    echo -e "${BLUE}啟動ntn-proxy服務...${NC}"
    docker compose up -d ntn-proxy
    
    # 啟動自動恢復服務
    echo -e "${BLUE}啟動自動恢復服務...${NC}"
    "$RECOVERY_DIR/ue_auto_recovery.sh" once
    
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
        return 1
    fi
    
    case "$mode" in
        sat|leo|meo|geo|ground)
            echo -e "${YELLOW}正在切換到 $mode 模式...${NC}"
            
            # 1. 生成配置文件
            echo -e "${BLUE}正在生成 $mode 模式的配置文件...${NC}"
            "$CONFIG_DIR/config_generator.py" --mode $mode
            if [ $? -ne 0 ]; then
                echo -e "${RED}配置生成失敗${NC}"
                return 1
            fi
            
            # 2. 應用配置文件
            echo -e "${BLUE}正在應用 $mode 模式的配置文件...${NC}"
            "$CONFIG_DIR/apply_config.sh" --mode $mode
            if [ $? -ne 0 ]; then
                echo -e "${RED}配置應用失敗${NC}"
                return 1
            fi
            
            # 3. 設置網絡仿真參數
            echo -e "${BLUE}正在設置 $mode 模式的網絡參數...${NC}"
            "$NETWORK_DIR/ntn_simulator.sh" --mode=$mode
            
            echo -e "${GREEN}已切換到 $mode 模式${NC}"
            ;;
        *)
            echo -e "${RED}錯誤: 未知的網絡模式 '$mode'${NC}"
            echo -e "${YELLOW}可用的網絡模式: sat, leo, meo, geo, ground${NC}"
            return 1
            ;;
    esac
}

# 執行網絡診斷功能
run_diagnosis() {
    echo -e "${YELLOW}正在執行網絡診斷...${NC}"
    
    # 調用診斷腳本
    "$DIAGNOSTIC_DIR/network_diagnostic.sh"
    
    echo -e "${GREEN}診斷完成${NC}"
}

# 執行性能測試功能
run_performance_test() {
    local mode=${1:-"both"}
    
    echo -e "${YELLOW}正在執行性能測試 (模式: $mode)...${NC}"
    
    # 調用性能測試腳本
    if [ -f "$TESTING_DIR/performance_test.sh" ]; then
        "$TESTING_DIR/performance_test.sh" --mode=$mode
    else
        echo -e "${RED}錯誤: 性能測試腳本不存在${NC}"
        return 1
    fi
    
    echo -e "${GREEN}性能測試完成${NC}"
}

# 修復常見問題功能
fix_common_issues() {
    echo -e "${YELLOW}正在嘗試修復常見問題...${NC}"
    
    # 0. 首先檢查 ntn-proxy 服務是否正在運行
    echo -e "${BLUE}0. 檢查代理服務狀態...${NC}"
    if ! docker ps | grep -q "ntn-proxy"; then
        echo "重新啟動 ntn-proxy 服務..."
        docker rm -f ntn-proxy 2>/dev/null || true
        docker compose up -d ntn-proxy || {
            echo "啟動 ntn-proxy 失敗，嘗試從命令行啟動..."
            cd "$PROXY_DIR" && ./start_proxy.sh && cd ..
        }
    else
        echo "ntn-proxy 服務正在運行"
    fi
    
    # 1. 修復GTP隧道
    echo -e "${BLUE}1. 修復GTP隧道...${NC}"
    "$DIAGNOSTIC_DIR/gtp_fix.sh"
    
    # 2. 檢查所有容器的健康狀態
    echo -e "${BLUE}2. 檢查容器健康狀態...${NC}"
    if ! docker ps | grep -q "ntn-stack-ues1-1"; then
        echo "UE容器未運行，正在重啟..."
        docker compose up -d ues1
        sleep 15
    fi
    
    # 3. 使用增強版UE修復腳本
    echo -e "${BLUE}3. 修復UE連接...${NC}"
    "$RECOVERY_DIR/ntn_sat_ue_fix.sh"
    
    # 4. 重新配置UPF
    echo -e "${BLUE}4. 重新配置UPF...${NC}"
    "$NETWORK_DIR/upf_setup.sh"
    
    # 5. 設置網絡橋接
    echo -e "${BLUE}5. 設置網絡橋接...${NC}"
    "$NETWORK_DIR/network_bridge.sh"
    
    # 6. 重新設置網絡模式
    echo -e "${BLUE}6. 重新設置網絡模式...${NC}"
    current_mode=$(docker exec -it gnb1 tc qdisc show dev eth0 2>/dev/null | grep -oP 'delay \K[0-9.]+ms' | cut -d'.' -f1 | head -1)
    if [ -z "$current_mode" ] || [ "$current_mode" -lt 100 ]; then
        echo "當前為地面模式，切換到LEO模式..."
        "$NETWORK_DIR/ntn_simulator.sh" --mode=leo
    else
        echo "保持當前網絡模式"
    fi
    
    # 7. 運行一次性自動恢復
    echo -e "${BLUE}7. 運行自動恢復腳本...${NC}"
    "$RECOVERY_DIR/ue_auto_recovery.sh" once
    
    echo -e "${GREEN}修復嘗試完成!${NC}"
    echo "請使用 '$0 status' 命令檢查修復結果"
}

# 顯示系統狀態功能
show_status() {
    echo -e "${BLUE}系統狀態:${NC}"
    echo "======================="
    
    # 檢查容器運行狀態
    echo -e "${YELLOW}容器狀態:${NC}"
    docker ps | grep -E "ntn-stack|gnb|ue|ntn-proxy"
    
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
    
    # 檢查ntn-proxy狀態
    echo -e "\n${YELLOW}代理服務狀態:${NC}"
    if docker ps | grep -q "ntn-proxy"; then
        echo "ntn-proxy服務正在運行"
        curl -s http://localhost:8888/api/status || echo "API服務無響應"
    else
        echo "ntn-proxy服務未運行"
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

# 配置處理函數
generate_config() {
    local mode=$1
    shift
    
    if [ -z "$mode" ]; then
        echo -e "${RED}錯誤: 未指定網絡模式${NC}"
        echo -e "${YELLOW}可用的網絡模式: leo, meo, geo, ground${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}正在生成 $mode 模式的配置...${NC}"
    
    # 構建命令
    cmd="$CONFIG_DIR/config_generator.py --mode $mode"
    
    # 添加其他參數
    while [[ $# -gt 0 ]]; do
        cmd="$cmd $1"
        shift
    done
    
    # 執行命令
    echo -e "${BLUE}執行: $cmd${NC}"
    eval $cmd
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}配置生成失敗${NC}"
        return 1
    fi
    
    echo -e "${GREEN}是否要立即應用此配置? [y/N]${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        "$CONFIG_DIR/apply_config.sh" --mode $mode
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}配置應用失敗${NC}"
            return 1
        fi
        
        echo -e "${GREEN}配置已成功應用${NC}"
    else
        echo -e "${YELLOW}配置已生成但未應用。你可以稍後使用以下命令應用:${NC}"
        echo -e "  $CONFIG_DIR/apply_config.sh --mode $mode"
    fi
    
    return 0
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
        test|perf)
            run_performance_test $option
            ;;
        fix)
            fix_common_issues
            ;;
        status)
            show_status
            ;;
        config)
            shift
            generate_config "$@"
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