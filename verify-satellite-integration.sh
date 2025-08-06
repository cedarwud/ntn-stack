#\!/bin/bash

echo "🛰️ 衛星數據整合診斷工具"
echo "==============================="

# 檢查 API 響應狀態
echo ""
echo "📡 1. API 端點檢查"
echo "-------------------"

# NetStack API 健康檢查
echo "🔍 NetStack API 健康狀態:"
curl -s "http://localhost:8080/health" | jq '.overall_status // "ERROR"' || echo "❌ NetStack API 無法訪問"

# 衛星可見性端點檢查
echo ""
echo "🔍 衛星可見性端點測試:"
response=$(curl -s "http://localhost:8080/api/v1/satellites/visible_satellites?count=5&min_elevation_deg=0&observer_lat=24.9441667&observer_lon=121.3713889&global_view=false")
if [ $? -eq 0 ]; then
    echo "✅ 端點可訪問"
    echo "$response" | jq '.total_count' 2>/dev/null || echo "❌ 響應格式異常"
else
    echo "❌ 端點無法訪問"
fi

# 檢查軌跡端點
echo ""
echo "🔍 軌跡端點測試:"
for sat_id in 56899 63088 48692; do
    echo "測試衛星 $sat_id:"
    curl -s "http://localhost:8080/api/v1/orbits/satellite/$sat_id/trajectory" -o /dev/null -w "  HTTP %{http_code}\n" | head -1
done

echo ""
echo "📊 2. 數據異常分析"
echo "-------------------"

# 獲取衛星數據並分析異常值
echo "🔍 獲取當前衛星數據進行異常分析:"
sat_data=$(curl -s "http://localhost:8080/api/v1/satellites/visible_satellites?count=10&min_elevation_deg=0&observer_lat=24.9441667&observer_lon=121.3713889&global_view=false")

if echo "$sat_data" | jq . >/dev/null 2>&1; then
    echo "✅ 數據格式正常"
    
    # 分析仰角異常
    echo ""
    echo "📐 仰角分析:"
    echo "$sat_data" | jq -r '.satellites[]? | "衛星 \(.name // .norad_id): 仰角 \(.elevation_deg // .elevation // 0)°"' | head -5
    
    low_elevation=$(echo "$sat_data" | jq '[.satellites[]? | select((.elevation_deg // .elevation // 0) < 5)] | length')
    echo "低仰角衛星數量 (<5°): $low_elevation"
    
    # 分析距離異常
    echo ""
    echo "📏 距離分析:"
    echo "$sat_data" | jq -r '.satellites[]? | "衛星 \(.name // .norad_id): 距離 \(.distance_km // .range_km // 0)km"' | head -5
    
    high_distance=$(echo "$sat_data" | jq '[.satellites[]? | select((.distance_km // .range_km // 0) > 3000)] | length')
    echo "高距離衛星數量 (>3000km): $high_distance"
    
    # 分析方位角
    echo ""
    echo "🧭 方位角分析:"
    echo "$sat_data" | jq -r '.satellites[]? | "衛星 \(.name // .norad_id): 方位角 \(.azimuth_deg // .azimuth // 0)°"' | head -5
else
    echo "❌ 數據格式異常或為空"
fi

echo ""
echo "🔧 3. 數據源追蹤"
echo "-------------------"

# 檢查 SimWorld API
echo "🔍 SimWorld 後端狀態:"
curl -s "http://localhost:8888/health" -w " (HTTP %{http_code})\n" | head -1 || echo "❌ SimWorld 後端無法訪問"

# 檢查前端代理配置
echo ""
echo "🔍 前端代理配置:"
if [ -f "/home/sat/ntn-stack/simworld/frontend/vite.config.ts" ]; then
    echo "✅ Vite 配置存在"
    grep -A 10 "proxy" /home/sat/ntn-stack/simworld/frontend/vite.config.ts | head -10
else
    echo "❌ Vite 配置不存在"
fi

echo ""
echo "🗄️ 4. 數據庫檢查"
echo "-------------------"

# 檢查軌道緩存數據
echo "🔍 軌道緩存表檢查:"
docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT 
    COUNT(DISTINCT satellite_id) as unique_satellites,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_time,
    MAX(timestamp) as latest_time
FROM satellite_orbital_cache LIMIT 1;
" 2>/dev/null || echo "❌ 無法訪問軌道緩存數據庫"

echo ""
echo "🔍 TLE 數據表檢查:"
docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT 
    constellation,
    COUNT(*) as satellite_count
FROM satellite_tle_data 
GROUP BY constellation 
ORDER BY satellite_count DESC;
" 2>/dev/null || echo "❌ 無法訪問 TLE 數據庫"

echo ""
echo "🏥 5. 服務健康檢查"
echo "-------------------"

# 檢查 Docker 容器狀態
echo "🐳 Docker 容器狀態:"
docker-compose ps | grep -E "(netstack|simworld)" | awk '{print $1, $2, $3}'

# 檢查端口監聽
echo ""
echo "🔌 端口監聽檢查:"
ss -tlnp | grep -E ":808[08]|:5173|:8888" | awk '{print $1, $4}' | sort

echo ""
echo "📋 6. 診斷總結"
echo "-------------------"

# 生成問題總結
echo "🎯 發現的問題:"

# 檢查 404 錯誤
if \! curl -s "http://localhost:8080/api/v1/orbits/satellite/56899/trajectory" >/dev/null; then
    echo "❌ 軌跡端點 404 錯誤 - 需要修復路由或數據載入"
fi

# 檢查數據異常
if [ "$low_elevation" -gt "8" ]; then
    echo "❌ 大量低仰角衛星 ($low_elevation 顆) - 可能是篩選機制問題"
fi

if [ "$high_distance" -gt "3" ]; then
    echo "❌ 大量高距離衛星 ($high_distance 顆) - 可能是座標系統或計算問題"
fi

echo ""
echo "✅ 診斷完成！請查看上述分析結果。"
