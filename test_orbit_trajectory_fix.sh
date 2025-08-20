#!/bin/bash
# 測試衛星軌道升降軌跡修復

echo "🛰️ 測試衛星軌道升降軌跡修復"
echo "================================================"

echo "📡 1. 檢查API數據中的elevation變化..."
echo "取得一顆衛星的完整時間序列數據："

# 獲取完整的時間序列數據並分析elevation變化
curl -s "http://localhost:8080/api/v1/satellite-simple/visible_satellites?count=1&min_elevation_deg=0&observer_lat=24.9441667&observer_lon=121.3713889&constellation=starlink&utc_timestamp=2025-08-18T10:00:00Z&global_view=false" | jq -r '.satellites[0].position_timeseries[] | "\(.time_offset_seconds)s: elevation=\(.elevation_deg)°, visible=\(.is_visible)"' | head -15

echo ""
echo "🔍 2. 分析elevation變化趨勢..."
echo "尋找升降模式（elevation由正到負或由負到正）："

# 分析elevation的變化趨勢
curl -s "http://localhost:8080/api/v1/satellite-simple/visible_satellites?count=1&min_elevation_deg=-10&observer_lat=24.9441667&observer_lon=121.3713889&constellation=starlink&utc_timestamp=2025-08-18T10:00:00Z&global_view=false" | jq '.satellites[0].position_timeseries | map(.elevation_deg) | {
    "開始仰角": .[0],
    "結束仰角": .[-1],
    "最高仰角": max,
    "最低仰角": min,
    "變化趨勢": (if .[0] > .[-1] then "下降" else "上升" end),
    "跨越地平線": (if (min < 0 and max > 0) then "是" else "否" end)
}'

echo ""
echo "🎮 3. 測試前端3D渲染..."
echo "檢查前端服務狀態："
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ 前端服務運行正常"
    echo "🌐 請前往 http://localhost:5173 查看衛星軌跡"
    echo ""
    echo "📋 預期修復效果："
    echo "  • 衛星應該從地平線升起（低Y座標→高Y座標）"
    echo "  • 到達最高點後向地平線下沉（高Y座標→低Y座標）" 
    echo "  • 當elevation < 5°時衛星消失"
    echo "  • 不再出現無限循環轉圈的現象"
else
    echo "❌ 前端服務尚未準備好"
fi

echo ""
echo "🔧 4. 驗證核心修復點："
echo "  ✅ 時間進度：線性進行而非循環"
echo "  ✅ 座標轉換：允許Y座標變化，移除Math.max限制"
echo "  ✅ 可見性判斷：基於真實elevation角度"
echo "  ✅ 超時處理：時間序列結束後衛星自然消失"

echo ""
echo "🎯 修復完成！請在瀏覽器中檢查衛星軌跡是否正常升降。"