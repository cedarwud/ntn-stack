#!/bin/bash

# NetStack API 診斷腳本
# 用於快速診斷和修復 netstack-api 容器問題

set -e

echo "🔍 NetStack API 診斷腳本"
echo "========================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢查函數
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

echo -e "${BLUE}📊 步驟 1: 檢查容器狀態${NC}"
echo "======================================"

# 檢查 netstack-api 容器是否運行
if docker ps | grep -q netstack-api; then
    echo -e "${GREEN}✅ netstack-api 容器正在運行${NC}"
    
    # 檢查健康狀態
    HEALTH_STATUS=$(docker inspect netstack-api --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-health-check")
    echo "   健康狀態: $HEALTH_STATUS"
    
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        echo -e "${GREEN}✅ 容器健康狀態正常${NC}"
    else
        echo -e "${YELLOW}⚠️ 容器健康狀態異常: $HEALTH_STATUS${NC}"
    fi
else
    echo -e "${RED}❌ netstack-api 容器未運行${NC}"
fi

echo ""
echo -e "${BLUE}🌐 步驟 2: 檢查網路連接${NC}"
echo "======================================"

# 檢查基礎服務是否就緒
echo "檢查依賴服務..."
docker exec netstack-api ping -c 1 mongo > /dev/null 2>&1
check_status "MongoDB 連接"

docker exec netstack-api ping -c 1 redis > /dev/null 2>&1
check_status "Redis 連接"

docker exec netstack-api ping -c 1 nrf > /dev/null 2>&1
check_status "NRF 連接"

echo ""
echo -e "${BLUE}🏥 步驟 3: 檢查 API 健康狀態${NC}"
echo "======================================"

# 檢查 API 健康端點
curl -s -f http://localhost:8080/health > /dev/null 2>&1
check_status "API 健康檢查端點"

# 檢查 API 文檔端點
curl -s -f http://localhost:8080/docs > /dev/null 2>&1
check_status "API 文檔端點"

echo ""
echo -e "${BLUE}📝 步驟 4: 檢查最近的錯誤日誌${NC}"
echo "======================================"

echo "最近 20 行日誌:"
docker logs netstack-api 2>&1 | tail -20

echo ""
echo -e "${BLUE}🔧 步驟 5: 檢查服務初始化${NC}"
echo "======================================"

# 檢查關鍵服務是否初始化
echo "檢查服務初始化狀態..."
docker logs netstack-api 2>&1 | grep -q "NetStack API 啟動完成"
check_status "NetStack API 初始化"

docker logs netstack-api 2>&1 | grep -q "所有 AI 服務已成功初始化\|AI 服務初始化失敗"
if docker logs netstack-api 2>&1 | grep -q "所有 AI 服務已成功初始化"; then
    echo -e "${GREEN}✅ AI 服務初始化${NC}"
elif docker logs netstack-api 2>&1 | grep -q "AI 服務初始化失敗"; then
    echo -e "${RED}❌ AI 服務初始化失敗${NC}"
else
    echo -e "${YELLOW}⚠️ AI 服務初始化狀態未知${NC}"
fi

echo ""
echo -e "${BLUE}📊 步驟 6: 系統資源檢查${NC}"
echo "======================================"

# 檢查 Docker 系統資源
echo "Docker 系統資源使用:"
docker system df

echo ""
echo "容器資源使用:"
docker stats netstack-api --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo -e "${BLUE}💡 步驟 7: 修復建議${NC}"
echo "======================================"

# 基於檢查結果提供修復建議
if ! docker ps | grep -q netstack-api; then
    echo -e "${YELLOW}🛠️ 建議: 容器未運行，執行以下命令啟動:${NC}"
    echo "   make netstack-start"
elif ! curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${YELLOW}🛠️ 建議: API 健康檢查失敗，嘗試重啟容器:${NC}"
    echo "   docker restart netstack-api"
    echo "   # 或完全重建:"
    echo "   make netstack-stop && make netstack-build && make netstack-start"
else
    echo -e "${GREEN}🎉 NetStack API 運行正常！${NC}"
fi

echo ""
echo -e "${BLUE}🚑 緊急修復命令${NC}"
echo "======================================"
echo "如果問題持續存在，可以嘗試以下命令："
echo ""
echo "1. 快速重啟:"
echo "   docker restart netstack-api"
echo ""
echo "2. 完全重建:"
echo "   make netstack-stop"
echo "   docker rmi netstack-api:latest"
echo "   make netstack-build"
echo "   make netstack-start"
echo ""
echo "3. 清理並重建所有服務:"
echo "   make down"
echo "   docker system prune -f"
echo "   make up"

echo ""
echo -e "${GREEN}診斷完成！${NC}"