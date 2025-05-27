#!/bin/bash

# NetStack API 健康檢查腳本
# 用於 Docker 容器健康檢查

set -e

# 設定變數
API_URL="http://localhost:8080"
HEALTH_ENDPOINT="$API_URL/health"
TIMEOUT=5

# 檢查 API 是否回應
check_api_health() {
    local response
    local http_code
    
    # 發送健康檢查請求
    response=$(curl -s -w "%{http_code}" --max-time $TIMEOUT "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")
    http_code="${response: -3}"
    
    if [ "$http_code" == "200" ]; then
        echo "✅ NetStack API 健康檢查通過"
        return 0
    else
        echo "❌ NetStack API 健康檢查失敗 (HTTP: $http_code)"
        return 1
    fi
}

# 檢查進程是否運行
check_process() {
    if pgrep -f "uvicorn.*netstack_api" > /dev/null; then
        echo "✅ NetStack API 進程正在運行"
        return 0
    else
        echo "❌ NetStack API 進程未運行"
        return 1
    fi
}

# 主要健康檢查
main() {
    local exit_code=0
    
    # 檢查進程
    if ! check_process; then
        exit_code=1
    fi
    
    # 檢查 API 健康
    if ! check_api_health; then
        exit_code=1
    fi
    
    if [ $exit_code -eq 0 ]; then
        echo "🎉 所有健康檢查通過"
    else
        echo "💥 健康檢查失敗"
    fi
    
    exit $exit_code
}

# 執行健康檢查
main "$@" 