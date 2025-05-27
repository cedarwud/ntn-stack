#!/bin/bash

# NetStack Slice 切換測試腳本
# 測試 eMBB 和 uRLLC 切片之間的動態切換功能

# 注意：移除 set -e，改為各部分獨立處理錯誤
# set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

# 測試設定
API_BASE_URL="http://localhost:8080"
TEST_IMSI="999700000000099"
SLICE_TYPES=("eMBB" "uRLLC")

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

# 檢查測試用戶是否存在
check_test_user_exists() {
    log_info "檢查測試 UE ($TEST_IMSI) 是否存在..."
    
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/ue/$TEST_IMSI" 2>/dev/null || echo "000")
    http_code="${response: -3}"
    
    if [ "$http_code" == "200" ]; then
        body="${response%???}"
        current_slice=$(echo "$body" | jq -r '.slice.slice_type' 2>/dev/null || echo "unknown")
        log_info "當前 Slice: $current_slice"
        return 0
    elif [ "$http_code" == "404" ]; then
        log_error "❌ 測試 UE $TEST_IMSI 不存在"
        log_warning "請先執行以下命令註冊測試用戶："
        log_warning "  make register-subscribers"
        log_warning "或手動添加測試用戶："
        log_warning "  make add-subscriber IMSI=$TEST_IMSI KEY=465B5CE8B199B49FAA5F0A2EE238A6BC OPC=E8ED289DEBA952E4283B54E88E6183CA"
        return 1
    else
        log_error "❌ 檢查測試 UE 時發生錯誤，HTTP 狀態碼: $http_code"
        return 1
    fi
}

# 取得當前 Slice 類型
get_current_slice() {
    local imsi=$1
    
    response=$(curl -s "$API_BASE_URL/api/v1/ue/$imsi" 2>/dev/null || echo "")
    
    if [ -n "$response" ]; then
        current_slice=$(echo "$response" | jq -r '.slice.slice_type' 2>/dev/null || echo "unknown")
        echo "$current_slice"
    else
        echo "unknown"
    fi
}

# 執行 Slice 切換
perform_slice_switch() {
    local imsi=$1
    local target_slice=$2
    
    payload=$(cat <<EOF
{
  "imsi": "$imsi",
  "target_slice": "$target_slice"
}
EOF
)
    
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$API_BASE_URL/api/v1/slice/switch")
    
    http_code="${response: -3}"
    body="${response%???}"
    
    echo "$http_code|$body"
}

# 測試單次 Slice 切換
test_single_slice_switch() {
    local target_slice=$1
    local current_slice=$(get_current_slice "$TEST_IMSI")
    
    log_test "測試切換 $TEST_IMSI 從 $current_slice 到 $target_slice"
    
    start_time=$(date +%s%3N)
    result=$(perform_slice_switch "$TEST_IMSI" "$target_slice")
    end_time=$(date +%s%3N)
    
    http_code=$(echo "$result" | cut -d'|' -f1)
    response_body=$(echo "$result" | cut -d'|' -f2-)
    switch_time=$((end_time - start_time))
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ Slice 切換成功 (${switch_time}ms)"
        
        # 驗證切換結果
        new_slice=$(get_current_slice "$TEST_IMSI")
        if [ "$new_slice" == "$target_slice" ]; then
            log_info "✅ Slice 切換驗證成功: $new_slice"
            echo "$switch_time"
            return 0
        else
            log_error "❌ Slice 切換驗證失敗: 期望 $target_slice，實際 $new_slice"
            return 1
        fi
    else
        log_error "❌ Slice 切換失敗，HTTP 狀態碼: $http_code"
        echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
        return 1
    fi
}

# 測試單次 Slice 切換 (靜默版本，只返回時間)
test_single_slice_switch_silent() {
    local target_slice=$1
    
    start_time=$(date +%s%3N)
    result=$(perform_slice_switch "$TEST_IMSI" "$target_slice")
    end_time=$(date +%s%3N)
    
    http_code=$(echo "$result" | cut -d'|' -f1)
    switch_time=$((end_time - start_time))
    
    if [ "$http_code" == "200" ]; then
        # 驗證切換結果
        new_slice=$(get_current_slice "$TEST_IMSI")
        if [ "$new_slice" == "$target_slice" ]; then
            echo "$switch_time"
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# 測試連續 Slice 切換
test_continuous_slice_switching() {
    local rounds=$1
    
    log_test "測試連續 Slice 切換 ($rounds 輪)"
    
    local success_count=0
    local total_time=0
    local switch_times=()
    
    for ((i=1; i<=rounds; i++)); do
        # 交替切換 Slice
        if [ $((i % 2)) -eq 1 ]; then
            target_slice="uRLLC"
        else
            target_slice="eMBB"
        fi
        
        log_info "第 $i 輪: 切換到 $target_slice"
        
        if switch_time=$(test_single_slice_switch_silent "$target_slice" 2>/dev/null); then
            ((success_count++))
            switch_times+=("$switch_time")
            total_time=$((total_time + switch_time))
            log_info "✅ 切換成功 (${switch_time}ms)"
        else
            log_error "❌ 切換失敗"
        fi
        
        # 間隔時間
        sleep 2
        echo ""
    done
    
    # 計算統計
    if [ ${#switch_times[@]} -gt 0 ]; then
        avg_time=$((total_time / ${#switch_times[@]}))
        
        # 找出最快和最慢的切換時間
        min_time=${switch_times[0]}
        max_time=${switch_times[0]}
        
        for time in "${switch_times[@]}"; do
            if [ "$time" -lt "$min_time" ]; then
                min_time=$time
            fi
            if [ "$time" -gt "$max_time" ]; then
                max_time=$time
            fi
        done
        
        log_info "📊 連續切換統計:"
        echo "   成功次數: $success_count/$rounds"
        echo "   平均時間: ${avg_time}ms"
        echo "   最快時間: ${min_time}ms"
        echo "   最慢時間: ${max_time}ms"
        
        success_rate=$((success_count * 100 / rounds))
        if [ $success_rate -ge 90 ]; then
            log_info "✅ 連續切換測試通過 (成功率: $success_rate%)"
            return 0
        else
            log_error "❌ 連續切換測試失敗 (成功率: $success_rate%)"
            return 1
        fi
    else
        log_error "❌ 沒有成功的切換"
        return 1
    fi
}

# 測試並發 Slice 切換
test_concurrent_slice_switching() {
    local concurrent_count=$1
    
    log_test "測試並發 Slice 切換 ($concurrent_count 個並發請求)"
    
    # 建立臨時檔案來收集結果
    local temp_dir=$(mktemp -d)
    local pids=()
    
    # 啟動並發請求
    for ((i=1; i<=concurrent_count; i++)); do
        (
            target_slice="eMBB"
            if [ $((i % 2)) -eq 0 ]; then
                target_slice="uRLLC"
            fi
            
            result=$(perform_slice_switch "$TEST_IMSI" "$target_slice")
            http_code=$(echo "$result" | cut -d'|' -f1)
            
            echo "$i:$target_slice:$http_code" > "$temp_dir/result_$i"
        ) &
        
        pids+=($!)
    done
    
    # 等待所有請求完成
    for pid in "${pids[@]}"; do
        wait $pid
    done
    
    # 分析結果
    local success_count=0
    local total_requests=$concurrent_count
    
    for ((i=1; i<=concurrent_count; i++)); do
        if [ -f "$temp_dir/result_$i" ]; then
            result=$(cat "$temp_dir/result_$i")
            http_code=$(echo "$result" | cut -d':' -f3)
            
            if [ "$http_code" == "200" ]; then
                ((success_count++))
            fi
        fi
    done
    
    # 清理臨時檔案
    rm -rf "$temp_dir"
    
    success_rate=$((success_count * 100 / total_requests))
    
    log_info "📊 並發切換統計:"
    echo "   成功次數: $success_count/$total_requests"
    echo "   成功率: $success_rate%"
    
    if [ $success_rate -ge 70 ]; then
        log_info "✅ 並發切換測試通過"
        return 0
    else
        log_error "❌ 並發切換測試失敗"
        return 1
    fi
}

# 測試錯誤處理
test_error_handling() {
    log_test "測試錯誤處理"
    
    local passed=0
    local failed=0
    
    # 測試無效 IMSI
    log_info "測試無效 IMSI"
    result=$(perform_slice_switch "invalid_imsi" "eMBB")
    http_code=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$http_code" == "422" ] || [ "$http_code" == "400" ] || [ "$http_code" == "404" ]; then
        log_info "✅ 無效 IMSI 錯誤處理正確 (HTTP $http_code)"
        ((passed++))
    else
        log_error "❌ 無效 IMSI 錯誤處理失敗 (HTTP $http_code)"
        ((failed++))
    fi
    
    # 測試無效 Slice 類型
    log_info "測試無效 Slice 類型"
    result=$(perform_slice_switch "$TEST_IMSI" "InvalidSlice")
    http_code=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$http_code" == "422" ] || [ "$http_code" == "400" ]; then
        log_info "✅ 無效 Slice 類型錯誤處理正確 (HTTP $http_code)"
        ((passed++))
    else
        log_error "❌ 無效 Slice 類型錯誤處理失敗 (HTTP $http_code)"
        ((failed++))
    fi
    
    if [ $failed -eq 0 ]; then
        log_info "✅ 錯誤處理測試通過"
        return 0
    else
        log_error "❌ 錯誤處理測試失敗"
        return 1
    fi
}

# 測試 Slice 效能差異
test_slice_performance() {
    log_test "測試 Slice 效能差異"
    
    local embb_times=()
    local urllc_times=()
    
    # 測試 eMBB 切換效能
    log_info "測試 eMBB 切換效能"
    for ((i=1; i<=3; i++)); do
        if switch_time=$(test_single_slice_switch_silent "eMBB" 2>/dev/null); then
            embb_times+=("$switch_time")
        fi
        sleep 1
    done
    
    # 測試 uRLLC 切換效能
    log_info "測試 uRLLC 切換效能"
    for ((i=1; i<=3; i++)); do
        if switch_time=$(test_single_slice_switch_silent "uRLLC" 2>/dev/null); then
            urllc_times+=("$switch_time")
        fi
        sleep 1
    done
    
    # 計算平均時間
    if [ ${#embb_times[@]} -gt 0 ] && [ ${#urllc_times[@]} -gt 0 ]; then
        embb_avg=0
        for time in "${embb_times[@]}"; do
            embb_avg=$((embb_avg + time))
        done
        embb_avg=$((embb_avg / ${#embb_times[@]}))
        
        urllc_avg=0
        for time in "${urllc_times[@]}"; do
            urllc_avg=$((urllc_avg + time))
        done
        urllc_avg=$((urllc_avg / ${#urllc_times[@]}))
        
        log_info "📊 Slice 效能比較:"
        echo "   eMBB 平均切換時間: ${embb_avg}ms"
        echo "   uRLLC 平均切換時間: ${urllc_avg}ms"
        
        # uRLLC 應該比 eMBB 快或相近
        if [ $urllc_avg -le $((embb_avg + 100)) ]; then
            log_info "✅ Slice 效能測試通過"
            return 0
        else
            log_warning "⚠️  uRLLC 切換時間較長，可能需要調整"
            return 0
        fi
    else
        log_error "❌ Slice 效能測試失敗"
        return 1
    fi
}

# 主要測試流程
main() {
    echo "=================================================="
    echo "🔀 NetStack Slice 切換測試開始"
    echo "=================================================="
    
    # 檢查測試用戶是否存在
    if ! check_test_user_exists; then
        exit 1
    fi
    
    # 測試計數器
    local passed=0
    local failed=0
    
    # 基本 Slice 切換測試
    echo "📋 執行基本 Slice 切換測試..."
    for slice_type in "${SLICE_TYPES[@]}"; do
        if test_single_slice_switch "$slice_type" > /dev/null; then
            ((passed++))
        else
            ((failed++))
        fi
        echo ""
    done
    
    # 連續切換測試
    echo "🔄 執行連續 Slice 切換測試..."
    if test_continuous_slice_switching 6; then
        ((passed++))
    else
        ((failed++))
    fi
    echo ""
    
    # 並發切換測試
    echo "⚡ 執行並發 Slice 切換測試..."
    if test_concurrent_slice_switching 5; then
        ((passed++))
    else
        ((failed++))
    fi
    echo ""
    
    # 錯誤處理測試
    echo "🛡️ 執行錯誤處理測試..."
    if test_error_handling; then
        ((passed++))
    else
        ((failed++))
    fi
    echo ""
    
    # 效能測試
    echo "🏎️ 執行 Slice 效能測試..."
    if test_slice_performance; then
        ((passed++))
    else
        ((failed++))
    fi
    echo ""
    
    # 測試結果
    echo "=================================================="
    echo "📊 Slice 切換測試結果統計"
    echo "=================================================="
    echo -e "通過: ${GREEN}$passed${NC}"
    echo -e "失敗: ${RED}$failed${NC}"
    echo -e "總計: $((passed + failed))"
    
    if [ $failed -eq 0 ]; then
        echo -e "\n🎉 ${GREEN}所有 Slice 切換測試通過！${NC}"
        exit 0
    else
        echo -e "\n❌ ${RED}有 $failed 個測試失敗${NC}"
        exit 1
    fi
}

# 檢查依賴
if ! command -v curl &> /dev/null; then
    log_error "curl 命令未找到，請先安裝 curl"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_warning "jq 命令未找到，JSON 解析將受限"
fi

# 執行主程式
main "$@" 