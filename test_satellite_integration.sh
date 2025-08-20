#!/bin/bash

echo "🔍 衛星顯示問題完整診斷測試"
echo "======================================"

echo ""
echo "1️⃣ 測試後端 API 響應"
echo "-------------------"
curl -s "http://localhost:8080/api/v1/satellite-simple/visible_satellites?count=3&constellation=starlink&min_elevation_deg=0" | jq '{satellites: (.satellites[:1] | map({name, elevation_deg, is_visible, has_timeseries: (.position_timeseries != null)}))}' 2>/dev/null || echo "❌ API 調用失敗"

echo ""
echo "2️⃣ 檢查前端 3D 模型文件"
echo "----------------------"
if [ -f "/home/sat/ntn-stack/simworld/frontend/public/static/models/sat.glb" ]; then
    echo "✅ 衛星 3D 模型文件存在"
else
    echo "❌ 衛星 3D 模型文件不存在"
fi

echo ""
echo "3️⃣ 檢查前端服務狀態"
echo "------------------"
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ 前端服務運行正常"
else
    echo "❌ 前端服務未運行"
fi

echo ""
echo "4️⃣ 檢查 Docker 容器狀態"
echo "----------------------"
echo "SimWorld 前端容器:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep simworld_frontend || echo "❌ 前端容器未運行"

echo ""
echo "NetStack API 容器:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep netstack-api || echo "❌ API 容器未運行"

echo ""
echo "5️⃣ 測試衛星數據 API 整合"
echo "-----------------------"
echo "檢查 API 響應是否包含時間序列數據："
response=$(curl -s "http://localhost:8080/api/v1/satellite-simple/visible_satellites?count=1&constellation=starlink&min_elevation_deg=0")
if echo "$response" | jq -e '.satellites[0].position_timeseries[0]' > /dev/null 2>&1; then
    echo "✅ API 返回衛星時間序列數據"
    echo "   第一個時間點數據："
    echo "$response" | jq '.satellites[0].position_timeseries[0] | {time, elevation_deg, azimuth_deg, range_km}' 2>/dev/null
else
    echo "❌ API 返回的衛星數據缺少時間序列"
fi

echo ""
echo "6️⃣ 診斷結論"
echo "-----------"
echo "如果以上檢查都通過，但衛星仍然不顯示，問題可能在於："
echo "• 前端 JavaScript 錯誤（檢查瀏覽器控制台）"
echo "• React Three Fiber 渲染問題" 
echo "• WebGL 兼容性問題"
echo "• 衛星位置計算邏輯錯誤"

echo ""
echo "🔧 快速修復建議："
echo "• 打開瀏覽器開發者工具，檢查 Console 和 Network 標籤"
echo "• 確認瀏覽器支持 WebGL"
echo "• 檢查是否有 JavaScript 運行時錯誤"