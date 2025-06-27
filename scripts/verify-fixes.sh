#!/bin/bash

# NetStack API 修復驗證腳本
# 驗證 NET.md 中描述的問題是否已修復

echo "🔍 NetStack API 修復驗證"
echo "========================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS: $1${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL: $1${NC}"
        ((FAIL++))
    fi
}

echo -e "${BLUE}🔧 檢查架構重構導入問題修復${NC}"
echo "================================================"

# 檢查服務適配器是否存在
test -f netstack/netstack_api/services/service_adapters.py
check_result "服務適配器文件存在"

# 檢查是否有 ModuleNotFoundError
! docker logs netstack-api 2>&1 | grep -q "ModuleNotFoundError"
check_result "無 ModuleNotFoundError 錯誤"

# 檢查 AI 服務初始化
docker logs netstack-api 2>&1 | grep -q "所有 AI 服務已成功初始化\|AI決策引擎適配器初始化完成"
check_result "AI 服務初始化成功"

echo ""
echo -e "${BLUE}🌐 檢查 Redis 連接配置問題修復${NC}"
echo "================================================"

# 檢查是否還有硬編碼 IP
! grep -r "172\.20\.0\.60" netstack/netstack_api/services/ >/dev/null 2>&1
check_result "無硬編碼 Redis IP 地址"

# 檢查 Redis 連接是否正常
docker exec netstack-api ping -c 1 redis >/dev/null 2>&1
check_result "Redis 網路連接正常"

# 檢查是否有 aioredis 錯誤
! docker logs netstack-api 2>&1 | grep -q "duplicate base class TimeoutError"
check_result "無 aioredis 版本衝突錯誤"

# 檢查 Redis 連接日誌
docker logs netstack-api 2>&1 | grep -q "Redis 緩存連接成功\|使用現有 Redis 適配器"
check_result "Redis 連接成功"

echo ""
echo -e "${BLUE}⚡ 檢查服務初始化順序問題修復${NC}"
echo "================================================"

# 檢查健康檢查配置
docker inspect netstack-api | grep -q "healthcheck"
check_result "健康檢查配置存在"

# 檢查服務依賴配置
docker-compose -f netstack/compose/core.yaml config | grep -A 10 "netstack-api" | grep -q "condition: service_healthy"
check_result "服務依賴健康檢查配置正確"

# 檢查 NetStack API 完整啟動
docker logs netstack-api 2>&1 | grep -q "NetStack API 啟動完成\|Application startup complete"
check_result "NetStack API 完整啟動"

echo ""
echo -e "${BLUE}📦 檢查容器資源和配置問題修復${NC}"
echo "================================================"

# 檢查容器健康狀態
[ "$(docker inspect netstack-api --format='{{.State.Health.Status}}')" = "healthy" ]
check_result "容器健康狀態正常"

# 檢查資源限制配置
docker-compose -f netstack/compose/core.yaml config | grep -A 20 "netstack-api" | grep -q "limits"
check_result "資源限制配置存在"

# 檢查環境變量
docker exec netstack-api env | grep -q "REDIS_TIMEOUT"
check_result "Redis 超時環境變量配置"

docker exec netstack-api env | grep -q "PYTHONUNBUFFERED"
check_result "Python 環境變量配置"

echo ""
echo -e "${BLUE}🧪 檢查 API 功能性${NC}"
echo "================================================"

# 檢查 API 健康端點
curl -s -f http://localhost:8080/health >/dev/null 2>&1
check_result "API 健康端點正常"

# 檢查 API 文檔端點
curl -s -f http://localhost:8080/docs >/dev/null 2>&1
check_result "API 文檔端點正常"

# 檢查根端點
curl -s -f http://localhost:8080/ >/dev/null 2>&1
check_result "API 根端點正常"

# 檢查 UE 管理端點
curl -s -f http://localhost:8080/api/v1/ue/stats >/dev/null 2>&1
check_result "UE 管理端點正常"

echo ""
echo -e "${BLUE}📊 修復驗證結果${NC}"
echo "================================================"

TOTAL=$((PASS + FAIL))
SUCCESS_RATE=$((PASS * 100 / TOTAL))

echo "總檢查項目: $TOTAL"
echo -e "通過項目: ${GREEN}$PASS${NC}"
echo -e "失敗項目: ${RED}$FAIL${NC}"
echo "成功率: $SUCCESS_RATE%"

echo ""
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 所有檢查通過！NetStack API 修復完成！${NC}"
    echo -e "${GREEN}系統運行狀態: 優秀${NC}"
elif [ $SUCCESS_RATE -ge 90 ]; then
    echo -e "${YELLOW}⚠️ 大部分檢查通過，系統基本正常${NC}"
    echo -e "${YELLOW}建議檢查失敗的項目並進行微調${NC}"
elif [ $SUCCESS_RATE -ge 70 ]; then
    echo -e "${YELLOW}⚠️ 部分檢查失敗，需要進一步修復${NC}"
    echo -e "${YELLOW}建議執行 NET.md 中的修復步驟${NC}"
else
    echo -e "${RED}❌ 多項檢查失敗，需要完整修復${NC}"
    echo -e "${RED}請按照 NET.md 中的完整修復流程執行${NC}"
fi

echo ""
echo -e "${BLUE}💡 後續建議${NC}"
echo "================================================"
echo "1. 定期運行此驗證腳本: ./scripts/verify-fixes.sh"
echo "2. 監控容器日誌: docker logs -f netstack-api"
echo "3. 運行診斷腳本: ./scripts/diagnose-netstack-api.sh"
echo "4. 參考完整指南: 查看 NET.md 和 CLAUDE.md"