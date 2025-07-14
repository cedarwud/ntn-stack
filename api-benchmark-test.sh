#\!/bin/bash
# API 性能基準測試腳本

echo '🚀 Phase 4 API 性能基準測試'
echo '=================================='

BASE_URL='http://localhost:8080'
TEST_RESULTS=()

# 測試函數
test_api() {
    local endpoint=$1
    local method=$2
    local data=$3
    
    echo "測試: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        result=$(curl -w '%{time_total},%{http_code}' -s -o /dev/null "$BASE_URL$endpoint")
    else
        result=$(curl -w '%{time_total},%{http_code}' -s -o /dev/null -X $method -H 'Content-Type: application/json' -d "$data" "$BASE_URL$endpoint")
    fi
    
    time=$(echo $result  < /dev/null |  cut -d',' -f1)
    code=$(echo $result | cut -d',' -f2)
    time_ms=$(echo "$time * 1000" | bc)
    
    if (( $(echo "$time_ms > 50" | bc -l) )); then
        status="❌ SLOW"
    else
        status="✅ FAST"
    fi
    
    echo "  響應時間: ${time_ms}ms | 狀態碼: $code | $status"
    TEST_RESULTS+=("$endpoint|$method|${time_ms}ms|$code|$status")
    echo ""
}

echo '📡 RL 系統 API 測試'
echo '------------------'
test_api '/api/v1/rl/health' 'GET'
test_api '/api/v1/rl/algorithms' 'GET'  
test_api '/api/v1/rl/status' 'GET'
test_api '/api/v1/rl/training/status-summary' 'GET'

echo '🔄 Phase 2.2 API 測試'
echo '------------------'
test_api '/api/v1/rl/phase-2-2/health' 'GET'
test_api '/api/v1/rl/phase-2-2/status' 'GET'

echo '🎯 Phase 2.3 API 測試'
echo '------------------'
test_api '/api/v1/rl/phase-2-3/health' 'GET'
test_api '/api/v1/rl/phase-2-3/system/status' 'GET'
test_api '/api/v1/rl/phase-2-3/algorithms/available' 'GET'

echo '⚡ 性能測試 API'
echo '------------------'
test_api '/api/v1/performance/metrics/real-time' 'GET'
test_api '/api/v1/performance/health' 'GET'
test_api '/system/health' 'GET'

echo '📊 測試結果摘要'
echo '================'
echo 'Endpoint|Method|Time|Code|Status'
for result in "${TEST_RESULTS[@]}"; do
    echo $result
done

echo ''
echo '🎯 需要優化的 API (> 50ms):'
for result in "${TEST_RESULTS[@]}"; do
    if [[ $result == *"❌ SLOW"* ]]; then
        endpoint=$(echo $result | cut -d'|' -f1)
        time=$(echo $result | cut -d'|' -f3)
        echo "  $endpoint - $time"
    fi
done

