#!/bin/bash

# NetStack 效能測試腳本
# 測試系統在不同負載下的表現，包括 API 響應時間和 Slice 切換效能

# 注意：移除 set -e，改為各部分獨立處理錯誤
# set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 測試設定
API_BASE_URL="http://localhost:8080"
TEST_IMSI="999700000000099"
WARMUP_REQUESTS=10
PERFORMANCE_REQUESTS=50
CONCURRENT_USERS=5

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

log_perf() {
    echo -e "${CYAN}[PERF]${NC} $1"
}

# 測量單一 API 請求的響應時間
measure_api_response_time() {
    local endpoint=$1
    local method=${2:-GET}
    local payload=${3:-""}
    
    local start_time=$(date +%s%3N)
    
    if [ "$method" == "POST" ] && [ -n "$payload" ]; then
        response=$(curl -s -w "%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$endpoint" 2>/dev/null)
    else
        response=$(curl -s -w "%{http_code}" "$endpoint" 2>/dev/null)
    fi
    
    local end_time=$(date +%s%3N)
    local http_code="${response: -3}"
    local response_time=$((end_time - start_time))
    
    echo "$response_time:$http_code"
}

# 熱身測試
warmup_test() {
    log_test "執行系統熱身測試 ($WARMUP_REQUESTS 個請求)"
    
    local success_count=0
    
    for ((i=1; i<=WARMUP_REQUESTS; i++)); do
        result=$(measure_api_response_time "$API_BASE_URL/health")
        http_code=$(echo "$result" | cut -d':' -f2)
        
        if [ "$http_code" == "200" ]; then
            ((success_count++))
        fi
        
        # 進度指示
        if [ $((i % 5)) -eq 0 ]; then
            echo -n "."
        fi
    done
    
    echo ""
    log_info "熱身完成: $success_count/$WARMUP_REQUESTS 成功"
}

# API 響應時間測試
test_api_response_times() {
    log_test "測試 API 響應時間 ($PERFORMANCE_REQUESTS 個請求)"
    
    local endpoints=(
        "$API_BASE_URL/health"
        "$API_BASE_URL/api/v1/ue"
        "$API_BASE_URL/api/v1/ue/$TEST_IMSI"
        "$API_BASE_URL/api/v1/ue/$TEST_IMSI/stats"
        "$API_BASE_URL/api/v1/slice/types"
    )
    
    local endpoint_names=(
        "Health Check"
        "List UEs"
        "Get UE Info"
        "Get UE Stats"
        "Get Slice Types"
    )
    
    for i in "${!endpoints[@]}"; do
        local endpoint="${endpoints[$i]}"
        local name="${endpoint_names[$i]}"
        
        log_perf "測試 $name"
        
        local response_times=()
        local success_count=0
        local total_time=0
        
        for ((j=1; j<=PERFORMANCE_REQUESTS; j++)); do
            result=$(measure_api_response_time "$endpoint")
            response_time=$(echo "$result" | cut -d':' -f1)
            http_code=$(echo "$result" | cut -d':' -f2)
            
            if [ "$http_code" == "200" ]; then
                response_times+=("$response_time")
                total_time=$((total_time + response_time))
                ((success_count++))
            fi
        done
        
        if [ ${#response_times[@]} -gt 0 ]; then
            # 計算統計
            local avg_time=$((total_time / ${#response_times[@]}))
            local min_time=${response_times[0]}
            local max_time=${response_times[0]}
            
            for time in "${response_times[@]}"; do
                if [ "$time" -lt "$min_time" ]; then
                    min_time=$time
                fi
                if [ "$time" -gt "$max_time" ]; then
                    max_time=$time
                fi
            done
            
            # 計算 95th percentile
            local sorted_times=($(printf '%s\n' "${response_times[@]}" | sort -n))
            local p95_index=$(((${#sorted_times[@]} * 95) / 100))
            local p95_time=${sorted_times[$p95_index]}
            
            log_info "  📊 $name 效能統計:"
            echo "    成功率: $success_count/$PERFORMANCE_REQUESTS ($((success_count * 100 / PERFORMANCE_REQUESTS))%)"
            echo "    平均響應時間: ${avg_time}ms"
            echo "    最小響應時間: ${min_time}ms"
            echo "    最大響應時間: ${max_time}ms"
            echo "    95th 百分位: ${p95_time}ms"
            
            # 效能評估
            if [ $avg_time -lt 100 ]; then
                echo -e "    評等: ${GREEN}優秀${NC} (<100ms)"
            elif [ $avg_time -lt 500 ]; then
                echo -e "    評等: ${YELLOW}良好${NC} (<500ms)"
            else
                echo -e "    評等: ${RED}需要改善${NC} (>=500ms)"
            fi
        else
            log_error "  ❌ $name 測試失敗"
        fi
        
        echo ""
    done
}

# Slice 切換效能測試
test_slice_switching_performance() {
    log_test "測試 Slice 切換效能"
    
    local slice_types=("eMBB" "uRLLC")
    local switch_times=()
    local success_count=0
    
    for ((i=1; i<=20; i++)); do
        # 交替切換 Slice
        local target_slice=${slice_types[$((i % 2))]}
        
        local payload=$(cat <<EOF
{
  "imsi": "$TEST_IMSI",
  "target_slice": "$target_slice"
}
EOF
)
        
        result=$(measure_api_response_time "$API_BASE_URL/api/v1/slice/switch" "POST" "$payload")
        response_time=$(echo "$result" | cut -d':' -f1)
        http_code=$(echo "$result" | cut -d':' -f2)
        
        if [ "$http_code" == "200" ]; then
            switch_times+=("$response_time")
            ((success_count++))
        fi
        
        # 等待間隔
        sleep 1
    done
    
    if [ ${#switch_times[@]} -gt 0 ]; then
        local total_time=0
        for time in "${switch_times[@]}"; do
            total_time=$((total_time + time))
        done
        
        local avg_time=$((total_time / ${#switch_times[@]}))
        local min_time=${switch_times[0]}
        local max_time=${switch_times[0]}
        
        for time in "${switch_times[@]}"; do
            if [ "$time" -lt "$min_time" ]; then
                min_time=$time
            fi
            if [ "$time" -gt "$max_time" ]; then
                max_time=$time
            fi
        done
        
        log_info "📊 Slice 切換效能統計:"
        echo "  成功次數: $success_count/20"
        echo "  平均切換時間: ${avg_time}ms"
        echo "  最快切換時間: ${min_time}ms"
        echo "  最慢切換時間: ${max_time}ms"
        
        # 效能評估
        if [ $avg_time -lt 1000 ]; then
            echo -e "  評等: ${GREEN}優秀${NC} (<1s)"
        elif [ $avg_time -lt 3000 ]; then
            echo -e "  評等: ${YELLOW}良好${NC} (<3s)"
        else
            echo -e "  評等: ${RED}需要改善${NC} (>=3s)"
        fi
    else
        log_error "❌ Slice 切換效能測試失敗"
    fi
    
    echo ""
}

# 並發測試
test_concurrent_load() {
    log_test "測試並發負載 ($CONCURRENT_USERS 個並發用戶)"
    
    local temp_dir=$(mktemp -d)
    local pids=()
    
    # 啟動並發用戶
    for ((i=1; i<=CONCURRENT_USERS; i++)); do
        (
            local user_success=0
            local user_total=10
            local user_total_time=0
            
            for ((j=1; j<=user_total; j++)); do
                result=$(measure_api_response_time "$API_BASE_URL/health")
                response_time=$(echo "$result" | cut -d':' -f1)
                http_code=$(echo "$result" | cut -d':' -f2)
                
                if [ "$http_code" == "200" ]; then
                    ((user_success++))
                    user_total_time=$((user_total_time + response_time))
                fi
                
                sleep 0.1
            done
            
            local user_avg_time=0
            if [ $user_success -gt 0 ]; then
                user_avg_time=$((user_total_time / user_success))
            fi
            
            echo "$i:$user_success:$user_total:$user_avg_time" > "$temp_dir/user_$i"
        ) &
        
        pids+=($!)
    done
    
    # 等待所有用戶完成
    for pid in "${pids[@]}"; do
        wait $pid
    done
    
    # 分析結果
    local total_requests=0
    local total_success=0
    local total_response_time=0
    local user_avg_times=()
    
    for ((i=1; i<=CONCURRENT_USERS; i++)); do
        if [ -f "$temp_dir/user_$i" ]; then
            result=$(cat "$temp_dir/user_$i")
            user_success=$(echo "$result" | cut -d':' -f2)
            user_total=$(echo "$result" | cut -d':' -f3)
            user_avg_time=$(echo "$result" | cut -d':' -f4)
            
            total_requests=$((total_requests + user_total))
            total_success=$((total_success + user_success))
            
            if [ $user_avg_time -gt 0 ]; then
                user_avg_times+=("$user_avg_time")
                total_response_time=$((total_response_time + user_avg_time))
            fi
        fi
    done
    
    # 清理臨時檔案
    rm -rf "$temp_dir"
    
    if [ ${#user_avg_times[@]} -gt 0 ]; then
        local overall_avg_time=$((total_response_time / ${#user_avg_times[@]}))
        local success_rate=$((total_success * 100 / total_requests))
        
        log_info "📊 並發負載測試結果:"
        echo "  並發用戶數: $CONCURRENT_USERS"
        echo "  總請求數: $total_requests"
        echo "  成功請求數: $total_success"
        echo "  成功率: $success_rate%"
        echo "  平均響應時間: ${overall_avg_time}ms"
        
        # 效能評估
        if [ $success_rate -ge 95 ] && [ $overall_avg_time -lt 200 ]; then
            echo -e "  評等: ${GREEN}優秀${NC}"
        elif [ $success_rate -ge 90 ] && [ $overall_avg_time -lt 500 ]; then
            echo -e "  評等: ${YELLOW}良好${NC}"
        else
            echo -e "  評等: ${RED}需要改善${NC}"
        fi
    else
        log_error "❌ 並發負載測試失敗"
    fi
    
    echo ""
}

# 系統資源監控
monitor_system_resources() {
    log_test "監控系統資源使用"
    
    # 取得 Docker 容器資源使用情況
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
        $(docker ps --filter "name=netstack-" --format "{{.Names}}") 2>/dev/null || {
        log_warning "無法取得 Docker 容器統計資訊"
        return
    }
    
    echo ""
}

# 主要測試流程
main() {
    echo "=================================================="
    echo "⚡ NetStack 效能測試開始"
    echo "=================================================="
    
    # 檢查測試 UE 是否存在
    log_info "檢查測試環境..."
    response=$(curl -s "$API_BASE_URL/health" 2>/dev/null || echo "")
    if [ -z "$response" ]; then
        log_error "NetStack API 無法連接，請確認系統已啟動"
        exit 1
    fi
    
    # 檢查測試 UE
    response=$(curl -s "$API_BASE_URL/api/v1/ue/$TEST_IMSI" 2>/dev/null || echo "")
    if [[ "$response" == *"404"* ]]; then
        log_warning "測試 UE $TEST_IMSI 不存在，部分測試將跳過"
        SKIP_UE_TESTS=true
    fi
    
    echo ""
    
    # 執行測試
    warmup_test
    echo ""
    
    test_api_response_times
    
    if [ "$SKIP_UE_TESTS" != "true" ]; then
        test_slice_switching_performance
    else
        log_warning "跳過 Slice 切換效能測試 (測試 UE 不存在)"
        echo ""
    fi
    
    test_concurrent_load
    
    monitor_system_resources
    
    # 測試結果總結
    echo "=================================================="
    echo "📊 效能測試完成"
    echo "=================================================="
    echo "✅ API 響應時間測試完成"
    
    if [ "$SKIP_UE_TESTS" != "true" ]; then
        echo "✅ Slice 切換效能測試完成"
    fi
    
    echo "✅ 並發負載測試完成"
    echo "✅ 系統資源監控完成"
    
    log_info "🎉 所有效能測試已完成！"
    log_info "💡 建議: 定期執行效能測試以監控系統效能變化"
}

# 檢查依賴
if ! command -v curl &> /dev/null; then
    log_error "curl 命令未找到，請先安裝 curl"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_warning "docker 命令未找到，將跳過系統資源監控"
fi

# 執行主程式
main "$@" 