#!/bin/bash

# NetStack E2E 測試腳本
# 完整測試 NetStack 系統功能，包括 UE 註冊、Slice 切換和連線測試

# 注意：移除 set -e，改為各部分獨立處理錯誤
# set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

# 測試設定
API_BASE_URL="http://localhost:8080"
TEST_IMSI="999700000000001"
TIMEOUT=30
DEBUG=true  # 設置為 true 以查看更詳細的輸出

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

log_debug() {
    if [ "$DEBUG" = true ]; then
        echo -e "${YELLOW}[DEBUG]${NC} $1"
    fi
}

# 檢查並確保測試用戶存在
check_and_register_test_user() {
    log_info "檢查測試用戶 $TEST_IMSI 是否存在..."
    
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/ue/$TEST_IMSI" 2>/dev/null || echo "000")
    http_code="${response: -3}"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ 測試用戶 $TEST_IMSI 已存在"
        return 0
    elif [ "$http_code" == "404" ]; then
        log_warning "⚠️  測試用戶 $TEST_IMSI 不存在"
        log_info "嘗試註冊測試用戶..."
        
        # 嘗試運行註冊腳本
        if [ -f "../scripts/register_subscriber.sh" ]; then
            log_info "執行用戶註冊腳本..."
            if ../scripts/register_subscriber.sh register 2>/dev/null; then
                log_info "✅ 測試用戶註冊完成"
                
                # 再次檢查用戶是否存在
                sleep 3
                response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/ue/$TEST_IMSI" 2>/dev/null || echo "000")
                http_code="${response: -3}"
                
                if [ "$http_code" == "200" ]; then
                    log_info "✅ 測試用戶註冊驗證成功"
                    return 0
                else
                    log_error "❌ 測試用戶註冊後仍無法找到"
                    return 1
                fi
            else
                log_error "❌ 測試用戶註冊失敗"
                return 1
            fi
        else
            log_error "❌ 找不到用戶註冊腳本"
            log_warning "請手動執行: make register-subscribers"
            return 1
        fi
    else
        log_error "❌ 檢查測試用戶時發生錯誤，HTTP 狀態碼: $http_code"
        return 1
    fi
}

# 等待服務就緒
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    log_info "等待 $service_name 服務就緒..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_info "$service_name 服務已就緒"
            return 0
        fi
        
        log_warning "等待 $service_name 服務... (嘗試 $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "$service_name 服務未能在指定時間內就緒"
    return 1
}

# 測試 API 健康檢查
test_health_check() {
    log_test "測試 API 健康檢查"
    
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/health")
    http_code="${response: -3}"
    body="${response%???}"
    
    log_debug "健康檢查回應: $body (HTTP 狀態碼: $http_code)"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ 健康檢查通過"
        return 0
    else
        log_error "❌ 健康檢查失敗，HTTP 狀態碼: $http_code"
        return 1
    fi
}

# 測試取得 UE 資訊
test_get_ue_info() {
    log_test "測試取得 UE 資訊"
    
    log_debug "請求 URL: $API_BASE_URL/api/v1/ue/$TEST_IMSI"
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/ue/$TEST_IMSI")
    http_code="${response: -3}"
    body="${response%???}"
    
    log_debug "獲取 UE 資訊回應: $body (HTTP 狀態碼: $http_code)"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ 成功取得 UE 資訊"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        return 0
    elif [ "$http_code" == "404" ]; then
        log_warning "⚠️  UE 不存在，需要先註冊"
        return 1
    else
        log_error "❌ 取得 UE 資訊失敗，HTTP 狀態碼: $http_code"
        echo "回應正文: $body"
        return 1
    fi
}

# 測試 Slice 切換
test_slice_switch() {
    local target_slice=$1
    log_test "測試切換到 $target_slice Slice"
    
    payload=$(cat <<EOF
{
  "imsi": "$TEST_IMSI",
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
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ Slice 切換到 $target_slice 成功"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        return 0
    else
        log_error "❌ Slice 切換失敗，HTTP 狀態碼: $http_code"
        echo "$body"
        return 1
    fi
}

# 測試 UE 統計
test_ue_stats() {
    log_test "測試取得 UE 統計資料"
    
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/ue/$TEST_IMSI/stats")
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ 成功取得 UE 統計資料"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        return 0
    else
        log_error "❌ 取得 UE 統計資料失敗，HTTP 狀態碼: $http_code"
        return 1
    fi
}

# 測試列出所有 UE
test_list_ues() {
    log_test "測試列出所有 UE"
    
    log_debug "請求 URL: $API_BASE_URL/api/v1/ue"
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/ue")
    http_code="${response: -3}"
    body="${response%???}"
    
    log_debug "列出 UE 回應: ${body:0:100}... (HTTP 狀態碼: $http_code)"
    
    if [ "$http_code" == "200" ]; then
        # 檢查是否為有效的 JSON 並包含陣列
        if echo "$body" | jq -e '. | if type=="array" then true else false end' >/dev/null 2>&1; then
            ue_count=$(echo "$body" | jq '. | length')
            log_info "✅ 成功列出 UE，共 $ue_count 個"
            return 0
        else
            log_error "❌ 回應不是一個有效的 JSON 陣列"
            echo "回應正文: $body"
            return 1
        fi
    else
        log_error "❌ 列出 UE 失敗，HTTP 狀態碼: $http_code"
        echo "回應正文: $body"
        return 1
    fi
}

# 測試取得 Slice 類型
test_slice_types() {
    log_test "測試取得 Slice 類型"
    
    log_debug "請求 URL: $API_BASE_URL/api/v1/slice/types"
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/slice/types")
    http_code="${response: -3}"
    body="${response%???}"
    
    log_debug "獲取 Slice 類型回應: $body (HTTP 狀態碼: $http_code)"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ 成功取得 Slice 類型"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        return 0
    else
        log_error "❌ 取得 Slice 類型失敗，HTTP 狀態碼: $http_code"
        echo "回應正文: $body"
        return 1
    fi
}

# 壓力測試
stress_test() {
    log_test "執行壓力測試 (連續 Slice 切換)"
    
    local success_count=0
    local total_requests=10
    
    for i in $(seq 1 $total_requests); do
        target_slice="eMBB"
        if [ $((i % 2)) -eq 0 ]; then
            target_slice="uRLLC"
        fi
        
        if test_slice_switch "$target_slice" > /dev/null 2>&1; then
            ((success_count++))
        fi
        
        sleep 1
    done
    
    success_rate=$((success_count * 100 / total_requests))
    log_info "壓力測試完成: $success_count/$total_requests 成功 (成功率: $success_rate%)"
    
    if [ $success_rate -ge 80 ]; then
        log_info "✅ 壓力測試通過"
        return 0
    else
        log_error "❌ 壓力測試失敗，成功率過低"
        return 1
    fi
}

# 主要測試流程
main() {
    echo "=================================================="
    echo "🧪 NetStack E2E 測試開始"
    echo "=================================================="
    
    # 等待服務就緒
    if ! wait_for_service "$API_BASE_URL/health" "NetStack API"; then
        exit 1
    fi
    
    # 檢查並確保測試用戶存在
    if ! check_and_register_test_user; then
        log_error "❌ 無法確保測試用戶存在，請手動執行: make register-subscribers"
        log_warning "測試將繼續進行，但可能會有部分測試失敗"
    fi
    
    # 測試計數器
    local passed=0
    local failed=0
    local overall_status=0
    
    # 執行測試
    echo -e "\n📋 執行基本功能測試..."
    
    test_health_check
    health_status=$?
    if [ $health_status -eq 0 ]; then ((passed++)); else ((failed++)); overall_status=1; fi
    echo ""
    
    test_list_ues
    list_ues_status=$?
    if [ $list_ues_status -eq 0 ]; then ((passed++)); else ((failed++)); overall_status=1; fi
    echo ""
    
    test_slice_types
    slice_types_status=$?
    if [ $slice_types_status -eq 0 ]; then ((passed++)); else ((failed++)); overall_status=1; fi
    echo ""
    
    # 檢查測試 UE 是否存在
    test_get_ue_info
    ue_exists=$?
    
    if [ $ue_exists -eq 0 ]; then
        ((passed++))
        
        test_ue_stats
        stats_status=$?
        if [ $stats_status -eq 0 ]; then ((passed++)); else ((failed++)); overall_status=1; fi
        echo ""
        
        test_slice_switch "uRLLC"
        switch_urllc_status=$?
        if [ $switch_urllc_status -eq 0 ]; then ((passed++)); else ((failed++)); overall_status=1; fi
        echo ""
        
        test_slice_switch "eMBB"
        switch_embb_status=$?
        if [ $switch_embb_status -eq 0 ]; then ((passed++)); else ((failed++)); overall_status=1; fi
        echo ""
        
        # 壓力測試
        echo -e "\n🔥 執行壓力測試..."
        stress_test
        stress_status=$?
        if [ $stress_status -eq 0 ]; then ((passed++)); else ((failed++)); overall_status=1; fi
    else
        log_error "❌ 測試 UE $TEST_IMSI 不存在或無法訪問"
        log_warning "請確保已註冊測試用戶: make register-subscribers"
        failed=$((failed + 5))
        overall_status=1
    fi
    
    # 測試結果
    echo ""
    echo "=================================================="
    echo "📊 測試結果統計"
    echo "=================================================="
    echo -e "通過: ${GREEN}$passed${NC}"
    echo -e "失敗: ${RED}$failed${NC}"
    echo -e "總計: $((passed + failed))"
    
    if [ $failed -eq 0 ]; then
        echo -e "\n🎉 ${GREEN}所有測試通過！${NC}"
        exit 0
    else
        echo -e "\n❌ ${RED}有 $failed 個測試失敗${NC}"
        exit $overall_status
    fi
}

# 檢查依賴
if ! command -v curl &> /dev/null; then
    log_error "curl 命令未找到，請先安裝 curl"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_warning "jq 命令未找到，JSON 輸出將以原始格式顯示"
fi

# 執行主程式
main "$@" 