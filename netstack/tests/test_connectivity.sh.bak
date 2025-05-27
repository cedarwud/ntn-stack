#!/bin/bash

# NetStack 網路連線測試腳本
# 測試 UE 的網路連通性，包括 ping、traceroute 和頻寬測試

# 移除 set -e 以避免腳本在非關鍵錯誤時退出
# set -e

# 信號處理 - 確保腳本不會被意外中斷
trap 'echo "測試被中斷"; exit 1' INT TERM

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

# 測試設定
TEST_TARGETS=("8.8.8.8" "1.1.1.1" "google.com")
UE_CONTAINERS=("netstack-ues1" "netstack-ues2" "netstack-ue-test")

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# 檢查容器是否運行
check_container_running() {
    local container_name=$1
    
    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        return 0
    else
        return 1
    fi
}

# 取得 UE 網路介面
get_ue_interface() {
    local container_name=$1
    
    # 查找 uesimtun 介面
    interface=$(docker exec "$container_name" ip route | grep uesimtun | head -1 | awk '{print $3}' 2>/dev/null || echo "")
    
    if [ -n "$interface" ]; then
        echo "$interface"
        return 0
    else
        # 檢查是否有 uesimtun 接口存在
        if docker exec "$container_name" ip addr show | grep -q uesimtun; then
            echo "uesimtun0"  # 預設介面名稱
            return 0
        else
            echo ""  # 沒有 uesimtun 接口
            return 1
        fi
    fi
}

# 測試 Ping 連通性
test_ping_connectivity() {
    local container_name=$1
    local target=$2
    local interface=$3
    
    log_test "從 $container_name 測試 ping $target"
    
    if [ -n "$interface" ]; then
        ping_cmd="ping -I $interface -c 3 -W 5 $target"
    else
        ping_cmd="ping -c 3 -W 5 $target"
    fi
    
    if docker exec "$container_name" $ping_cmd > /dev/null 2>&1; then
        log_info "✅ Ping $target 成功"
        
        # 取得延遲資訊
        rtt=$(docker exec "$container_name" $ping_cmd 2>/dev/null | grep "avg" | awk -F'/' '{print $5}' || echo "N/A")
        echo "   平均 RTT: ${rtt}ms"
        return 0
    else
        log_error "❌ Ping $target 失敗"
        return 1
    fi
}

# 測試 DNS 解析
test_dns_resolution() {
    local container_name=$1
    local hostname=$2
    
    log_test "從 $container_name 測試 DNS 解析 $hostname"
    
    if docker exec "$container_name" nslookup "$hostname" > /dev/null 2>&1; then
        resolved_ip=$(docker exec "$container_name" nslookup "$hostname" 2>/dev/null | grep "Address:" | tail -1 | awk '{print $2}')
        log_info "✅ DNS 解析成功: $hostname -> $resolved_ip"
        return 0
    else
        log_error "❌ DNS 解析失敗: $hostname"
        return 1
    fi
}

# 測試 HTTP 連線
test_http_connectivity() {
    local container_name=$1
    local url=$2
    
    log_test "從 $container_name 測試 HTTP 連線 $url"
    
    if docker exec "$container_name" curl -s -f --max-time 10 "$url" > /dev/null 2>&1; then
        log_info "✅ HTTP 連線成功"
        return 0
    else
        log_error "❌ HTTP 連線失敗"
        return 1
    fi
}

# 測試路由追蹤
test_traceroute() {
    local container_name=$1
    local target=$2
    local interface=$3
    
    log_test "從 $container_name 追蹤路由到 $target"
    
    if [ -n "$interface" ]; then
        traceroute_cmd="traceroute -i $interface -m 10 $target"
    else
        traceroute_cmd="traceroute -m 10 $target"
    fi
    
    if docker exec "$container_name" $traceroute_cmd 2>/dev/null | head -10; then
        log_info "✅ Traceroute 完成"
        return 0
    else
        log_warning "⚠️  Traceroute 可能不完整"
        return 1
    fi
}

# 測試頻寬 (簡單版本)
test_bandwidth() {
    local container_name=$1
    
    log_test "從 $container_name 測試下載速度"
    
    # 嘗試多個測試 URL
    test_urls=(
        "http://httpbin.org/bytes/1048576"  # 1MB 資料
        "http://www.google.com/robots.txt"  # 備用小檔案
        "http://github.com/robots.txt"      # 另一個備用
    )
    
    for test_url in "${test_urls[@]}"; do
        if docker exec "$container_name" timeout 10 curl -s -w "速度: %{speed_download} bytes/sec\n時間: %{time_total}s\n" -o /dev/null "$test_url" 2>/dev/null; then
            log_info "✅ 頻寬測試完成"
            return 0
        fi
    done
    
    log_warning "⚠️  頻寬測試失敗或超時 (非關鍵錯誤)"
    return 1
}

# 測試特定容器的所有連線
test_container_connectivity() {
    local container_name=$1
    
    echo "=================================================="
    echo "🧪 測試容器: $container_name"
    echo "=================================================="
    
    if ! check_container_running "$container_name"; then
        log_error "容器 $container_name 未運行"
        return 1
    fi
    
    # 取得網路介面
    interface=$(get_ue_interface "$container_name")
    if [ -z "$interface" ]; then
        log_error "容器 $container_name 沒有 uesimtun 網路接口 - UE 可能未成功連接到網路"
        log_warning "跳過此容器的網路測試"
        return 1
    fi
    log_info "使用網路介面: $interface"
    
    local passed=0
    local failed=0
    
    # 測試 Ping 連通性
    for target in "${TEST_TARGETS[@]}"; do
        if [[ "$target" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            # IP 位址直接測試
            if test_ping_connectivity "$container_name" "$target" "$interface"; then
                ((passed++))
            else
                ((failed++))
            fi
        else
            # 主機名稱先測試 DNS
            if test_dns_resolution "$container_name" "$target"; then
                if test_ping_connectivity "$container_name" "$target" "$interface"; then
                    ((passed++))
                else
                    ((failed++))
                fi
            else
                ((failed++))
            fi
        fi
        echo ""
    done
    
    # 測試 HTTP 連線
    if test_http_connectivity "$container_name" "http://httpbin.org/json"; then
        ((passed++))
    else
        ((failed++))
    fi
    echo ""
    
    # 測試路由追蹤
    if test_traceroute "$container_name" "8.8.8.8" "$interface"; then
        ((passed++))
    else
        ((failed++))
    fi
    echo ""
    
    # 測試頻寬
    if test_bandwidth "$container_name"; then
        ((passed++))
    else
        ((failed++))
    fi
    echo ""
    
    echo "容器 $container_name 測試結果:"
    echo -e "通過: ${GREEN}$passed${NC}"
    echo -e "失敗: ${RED}$failed${NC}"
    echo ""
    
    # 返回 0 (成功) 如果沒有失敗，返回 1 (失敗) 如果有失敗
    if [ $failed -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# 主要測試流程
main() {
    echo "=================================================="
    echo "🌐 NetStack 網路連線測試開始"
    echo "=================================================="
    echo "預計測試 ${#UE_CONTAINERS[@]} 個容器: ${UE_CONTAINERS[*]}"
    echo ""
    
    # 檢查是否有任何 UE 容器運行
    running_containers=0
    for container in "${UE_CONTAINERS[@]}"; do
        if check_container_running "$container"; then
            ((running_containers++))
        fi
    done
    
    if [ $running_containers -eq 0 ]; then
        log_error "❌ 沒有任何 UE 容器在運行"
        log_warning "連線測試需要 UE 模擬器容器運行"
        log_warning "請先啟動 UE 模擬器："
        log_warning "  make start-ran"
        log_warning "或檢查 UE 容器配置是否正確"
        echo ""
        echo "=================================================="
        echo "📊 網路連線測試總結"
        echo "=================================================="
        echo "容器測試通過: 0"
        echo "容器測試失敗: ${#UE_CONTAINERS[@]}"
        echo "總計容器: ${#UE_CONTAINERS[@]}"
        echo ""
        echo "❌ 所有容器連線測試失敗 (容器未運行)"
        exit 1
    fi
    
    # 測試計數器
    local passed=0
    local failed=0
    
    # 測試每個容器
    for i in "${!UE_CONTAINERS[@]}"; do
        container="${UE_CONTAINERS[$i]}"
        container_num=$((i + 1))
        total_containers=${#UE_CONTAINERS[@]}
        
        echo "正在測試第 $container_num/$total_containers 個容器: $container"
        
        if test_container_connectivity "$container"; then
            log_info "✅ 容器 $container 測試通過"
            ((passed++))
        else
            log_error "❌ 容器 $container 測試失敗"
            ((failed++))
        fi
        
        echo ""
    done
    
    # 測試結果
    echo "=================================================="
    echo "📊 網路連線測試總結"
    echo "=================================================="
    echo "容器測試通過: $passed"
    echo "容器測試失敗: $failed"
    echo "總計容器: $((passed + failed))"
    echo ""
    
    if [ $failed -eq 0 ]; then
        echo "🎉 所有容器連線測試通過"
        exit 0
    else
        echo "❌ 有 $failed 個容器連線測試失敗"
        if [ $failed -eq ${#UE_CONTAINERS[@]} ]; then
            log_warning "所有容器都失敗，可能是因為："
            log_warning "1. UE 模擬器未啟動 (make start-ran)"
            log_warning "2. UE 未成功連接到網路"
            log_warning "3. 網路配置問題"
        fi
        exit 1
    fi
}

# 檢查依賴
if ! command -v docker &> /dev/null; then
    log_error "docker 命令未找到，請先安裝 Docker"
    exit 1
fi

# 執行主程式
main "$@" 