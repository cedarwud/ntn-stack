#!/bin/bash
# Phase 1 部署執行腳本

set -e

echo "🚀 Phase 1 部署執行開始..."

# 停止舊服務
echo "停止現有服務..."
docker-compose -f docker-compose.phase1.yml down --remove-orphans || true

# 清理舊鏡像
echo "清理舊鏡像..."
docker system prune -f

# 建構新鏡像
echo "建構 Phase 1 增強鏡像..."
docker-compose -f docker-compose.phase1.yml build --no-cache

# 啟動服務
echo "啟動 Phase 1 服務..."
docker-compose -f docker-compose.phase1.yml up -d

# 等待服務啟動
echo "等待服務啟動..."
sleep 30

# 檢查服務狀態
echo "檢查服務狀態..."
docker-compose -f docker-compose.phase1.yml ps

# 等待健康檢查
echo "等待健康檢查..."
for i in {1..30}; do
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        echo "✅ 服務健康檢查通過"
        break
    fi
    echo "等待健康檢查... ($i/30)"
    sleep 2
done

# 執行部署後驗證
echo "執行部署後驗證..."
python ../05_integration/integration_test.py

if [ $? -eq 0 ]; then
    echo "✅ 部署後驗證通過"
else
    echo "❌ 部署後驗證失敗"
    echo "回滾部署..."
    docker-compose -f docker-compose.phase1.yml down
    exit 1
fi

echo "🎉 Phase 1 部署完成！"
echo "API 端點: http://localhost:8080"
echo "Phase 1 API: http://localhost:8001"
echo "健康檢查: http://localhost:8080/health"
