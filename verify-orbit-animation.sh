#\!/bin/bash

echo "🛰️ 軌道動畫數據驗證工具"
echo "========================"

echo ""
echo "📡 第1步：測試 NetStack API"
echo "-------------------------"

echo "🧪 測試衛星可見性端點："
response=$(curl -s "http://localhost:8080/api/v1/satellite-ops/visible_satellites?count=6&min_elevation_deg=5&observer_lat=24.9441667&observer_lon=121.3713889")

if echo "$response" | jq . >/dev/null 2>&1; then
    total=$(echo "$response" | jq -r '.total_count')
    echo "✅ NetStack API 正常，返回 $total 顆衛星"
    
    echo ""
    echo "📊 衛星數據分析："
    echo "$response" | jq -r '.satellites[0:3][] | "  \(.name): 仰角 \(.elevation_deg)°, 距離 \(.distance_km)km, 方位角 \(.azimuth_deg)°"'
    
    # 數據質量檢查
    echo ""
    echo "🔍 數據質量檢查："
    
    # 檢查距離異常（應該是550-2000km，不是6800km+）
    wrong_distance=$(echo "$response" | jq '[.satellites[] | select(.distance_km > 3000)] | length')
    echo "  異常距離衛星 (>3000km): $wrong_distance 顆"
    
    # 檢查合理仰角
    good_elevation=$(echo "$response" | jq '[.satellites[] | select(.elevation_deg >= 5 and .elevation_deg <= 85)] | length')
    echo "  合理仰角衛星 (5-85°): $good_elevation 顆"
    
    # 檢查星座分佈
    starlink_count=$(echo "$response" | jq '[.satellites[] | select(.constellation == "STARLINK")] | length')
    echo "  STARLINK 衛星: $starlink_count 顆"
    
else
    echo "❌ NetStack API 測試失敗："
    echo "$response"
    exit 1
fi

echo ""
echo "🌍 第2步：測試 SimWorld 直接 API"
echo "-------------------------------"

echo "🧪 測試 SimWorld 衛星端點："
simworld_response=$(curl -s "http://localhost:8888/api/v1/satellites/visible_satellites?count=3&global_view=true")

if echo "$simworld_response" | jq . >/dev/null 2>&1; then
    simworld_total=$(echo "$simworld_response" | jq -r '.total_count')
    echo "✅ SimWorld API 正常，返回 $simworld_total 顆衛星"
    
    echo ""
    echo "📊 SimWorld 原始數據："
    echo "$simworld_response" | jq -r '.satellites[0:2][] | "  \(.name): 距離 \(.distance_km)km, 高度 \(.orbit_altitude_km)km"'
    
    # 分析距離問題
    echo ""
    echo "🔍 距離計算分析："
    sample_distance=$(echo "$simworld_response" | jq -r '.satellites[0].distance_km')
    sample_altitude=$(echo "$simworld_response" | jq -r '.satellites[0].orbit_altitude_km')
    
    echo "  原始距離: ${sample_distance}km"
    echo "  軌道高度: ${sample_altitude}km"
    echo "  地球半徑: ~6371km"
    echo "  預期距離: 550-2000km (slant range)"
    echo "  問題診斷: 距離可能包含了地球半徑"
    
else
    echo "❌ SimWorld API 測試失敗："
    echo "$simworld_response"
fi

echo ""
echo "🎯 第3步：前端連接測試"
echo "-------------------"

echo "🧪 測試前端衛星數據 hook："
# 模擬前端調用
frontend_test_response=$(curl -s "http://localhost:5173/api/v1/satellite-ops/visible_satellites?count=4&min_elevation_deg=5&observer_lat=24.9441667&observer_lon=121.3713889")

if echo "$frontend_test_response" | jq . >/dev/null 2>&1; then
    frontend_total=$(echo "$frontend_test_response" | jq -r '.total_count')
    echo "✅ 前端代理正常，返回 $frontend_total 顆衛星"
else
    echo "❌ 前端代理測試失敗："
    echo "$frontend_test_response"
fi

echo ""
echo "📋 診斷總結"
echo "==========="

echo "🔍 問題識別："
if [ "$wrong_distance" -gt "2" ]; then
    echo "❌ 主要問題：距離計算包含地球半徑 ($wrong_distance 顆衛星距離 >3000km)"
    echo "   解決方案：修復 SimWorld 距離計算，使用 slant range 而非地心距離"
fi

if [ "$total" -gt "0" ]; then
    echo "✅ API 連接：NetStack ↔ SimWorld 連接正常"
else
    echo "❌ API 連接：數據流中斷"
fi

if [ "$starlink_count" -gt "0" ]; then
    echo "✅ 數據源：真實 STARLINK 衛星數據"
else
    echo "❌ 數據源：缺乏真實衛星數據"
fi

echo ""
echo "🚀 修復優先級："
echo "  1. 高優先級：修復 SimWorld 距離計算 (6800km → 550-2000km)"
echo "  2. 中優先級：確保前端獲得一致的數據格式"
echo "  3. 低優先級：優化衛星可見性篩選"

echo ""
echo "✅ 軌道動畫數據驗證完成！"
EOF < /dev/null
