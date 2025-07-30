#!/bin/bash
set -e

echo "🧪 開始 Volume 優化測試..."

# 1. 完全清理
echo "🧹 清理現有容器和 volumes..."
cd /home/sat/ntn-stack
make down
docker volume rm $(docker volume ls -q | grep -E "(satellite|netstack)") 2>/dev/null || true

# 2. 重新建構
echo "🔨 重新建構 NetStack..."
cd netstack
docker compose -f compose/core.yaml build netstack-api --no-cache

# 3. 啟動 NetStack
echo "🚀 啟動 NetStack..."
docker compose -f compose/core.yaml up -d netstack-api

# 4. 等待數據生成完成
echo "⏳ 等待數據生成..."
timeout 300 bash -c '
while ! docker exec netstack-api ls /app/data/.data_ready >/dev/null 2>&1; do
    echo "等待數據生成..."
    sleep 10
done
'

# 5. 檢查數據
echo "🔍 檢查數據完整性..."
docker exec netstack-api ls -la /app/data/
docker exec netstack-api wc -c /app/data/phase0_precomputed_orbits.json

# 6. 啟動 SimWorld
echo "🌍 啟動 SimWorld..."
cd ../simworld
docker compose up -d frontend

# 7. 測試前端訪問
echo "🌐 測試前端數據訪問..."
sleep 10
curl -s -I http://localhost:5173/data/phase0_precomputed_orbits.json | head -n 1

echo "✅ Volume 優化測試完成！"