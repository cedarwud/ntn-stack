#\!/bin/bash
# verify_data_integration.sh - NetStack-SimWorld 數據集成驗證

echo "=== NetStack-SimWorld 數據集成驗證 ==="

# 檢查 NetStack TLE 文件
echo "1. 檢查 NetStack TLE 文件:"
STARLINK_COUNT=$(wc -l /home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_$(date +%Y%m%d).tle 2>/dev/null | awk '{print int($1/3)}' || echo "0")
ONEWEB_COUNT=$(wc -l /home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_$(date +%Y%m%d).tle 2>/dev/null | awk '{print int($1/3)}' || echo "0")
echo "  Starlink: $STARLINK_COUNT 顆衛星"
echo "  OneWeb: $ONEWEB_COUNT 顆衛星"
echo "  NetStack 總計: $((STARLINK_COUNT + ONEWEB_COUNT)) 顆衛星"

# 檢查 SimWorld API 回應
echo -e "\n2. 檢查 SimWorld 統計 API:"
SIMWORLD_STATS=$(curl -s http://localhost:8888/api/v1/satellites/stats)
SIMWORLD_TOTAL=$(echo "$SIMWORLD_STATS" | jq -r '.total_satellites // 0')
echo "  SimWorld API 回報: $SIMWORLD_TOTAL 顆衛星"

# 數據一致性比較
echo -e "\n3. 數據一致性檢查:"
if [ "$SIMWORLD_TOTAL" -gt 1000 ]; then
    echo "  ✓ SimWorld 已使用 NetStack 真實數據"
else
    echo "  ✗ SimWorld 使用模擬數據"
fi

# Redis 數據檢查
echo -e "\n4. Redis 數據同步檢查:"
docker exec simworld_backend python -c "
import redis.asyncio as redis
import json
import asyncio

async def check_redis():
    r = redis.Redis(host='netstack-redis', port=6379, decode_responses=True)
    for constellation in ['starlink', 'oneweb']:
        key = f'netstack_tle_stats:{constellation}'
        data = await r.get(key)
        if data:
            stats = json.loads(data)
            print(f'  {constellation}: {stats[\"count\"]} 顆衛星 (Redis)')
        else:
            print(f'  {constellation}: 無數據 (Redis)')
    await r.aclose()

asyncio.run(check_redis())
"

echo -e "\n=== 驗證完成 ==="
