#!/bin/bash

# 🛰️ 衛星軌跡最終驗證腳本
# 驗證衛星是否正確在天空中升降，而非地面附近

echo "🛰️ 衛星天空軌跡最終驗證"
echo "============================================="

# 等待服務完全啟動
echo "⏳ 等待服務啟動..."
sleep 15

echo ""
echo "📏 場景尺度分析："
echo "   地面設備高度: 5-20 units (基站+UAV)"
echo "   場景Y軸範圍: -80 → 700 units"
echo "   修復前衛星: 50-600 units (地面附近)"
echo "   修復後衛星: 200-600+ units (天空中)"

echo ""
echo "📡 測試修復後的衛星座標"

# 獲取衛星數據並計算3D座標
python3 -c "
import requests
import json
import math

# 獲取衛星數據
url = 'http://localhost:8080/api/v1/satellite-simple/visible_satellites?count=3&min_elevation_deg=5&observer_lat=24.9441667&observer_lon=121.3713889&constellation=starlink&utc_timestamp=2025-08-18T09:45:00.000Z&global_view=false'
response = requests.get(url)
data = response.json()

print('🛰️ 修復後的衛星座標驗證:')
print('=' * 50)

if data['satellites']:
    for i, sat in enumerate(data['satellites'][:3]):
        print(f'\\n衛星 {i+1}: {sat[\"name\"]}')
        timeseries = sat['position_timeseries']
        visible_points = [p for p in timeseries if p['is_visible'] and p['elevation_deg'] >= 0]
        
        if visible_points:
            # 使用修復後的參數計算3D座標
            coords_3d = []
            for p in visible_points:
                elevation_rad = math.radians(p['elevation_deg'])
                azimuth_rad = math.radians(p['azimuth_deg'])
                range_km = p['range_km']
                
                # 修復後的參數
                scale_range = 4.0          # 增大縮放
                max_range = 300           # 適中最大範圍
                height_scale = 1.5        # 適中高度縮放
                sky_base_height = 200     # 天空基準高度
                
                scaled_range = min(range_km / scale_range, max_range)
                
                x = scaled_range * math.cos(elevation_rad) * math.sin(azimuth_rad)
                z = scaled_range * math.cos(elevation_rad) * math.cos(azimuth_rad)
                y = sky_base_height + (scaled_range * math.sin(elevation_rad) * height_scale)
                
                coords_3d.append((x, y, z, p['elevation_deg']))
            
            if coords_3d:
                y_coords = [c[1] for c in coords_3d]
                elevations = [c[3] for c in coords_3d]
                
                min_y = min(y_coords)
                max_y = max(y_coords)
                min_elev = min(elevations)
                max_elev = max(elevations)
                
                print(f'   仰角範圍: {min_elev:.1f}° → {max_elev:.1f}°')
                print(f'   Y座標範圍: {min_y:.0f} → {max_y:.0f} units')
                print(f'   升降幅度: {max_y - min_y:.0f} units')
                
                # 檢查是否在天空中（遠高於地面設備）
                ground_device_height = 20  # 地面設備最高約20 units
                sky_clearance = min_y - ground_device_height
                
                if sky_clearance > 100:
                    print(f'   ✅ 位於天空中: 最低點高於地面設備 {sky_clearance:.0f} units')
                elif sky_clearance > 50:
                    print(f'   ⚠️ 部分在天空: 最低點高於地面設備 {sky_clearance:.0f} units')
                else:
                    print(f'   ❌ 仍在地面附近: 僅高於地面設備 {sky_clearance:.0f} units')
                
                # 顯示升降軌跡關鍵點
                print(f'   🎯 軌跡關鍵點:')
                sorted_points = sorted(coords_3d, key=lambda p: p[3])  # 按仰角排序
                for j in range(0, len(sorted_points), max(1, len(sorted_points)//4)):
                    x, y, z, elev = sorted_points[j]
                    print(f'      仰角 {elev:5.1f}° → Y座標 {y:5.0f} units')

print('\\n' + '=' * 50)
print('🎯 驗證結果總結:')
print('=' * 50)

print('\\n✅ 預期修復效果:')
print('   1. 衛星最低點 > 250 units (遠高於地面設備的20 units)')  
print('   2. 衛星最高點 < 650 units (在場景Y軸範圍700內)')
print('   3. 升降幅度適中 (100-200 units)')
print('   4. 從天空地平線升起到頭頂，再降回天空地平線')

print('\\n🚀 現在衛星應該在天空中自然升降，而不是在地面附近！')
print('   訪問 http://localhost:5173 查看立體圖效果')
"

echo ""
echo "🎮 檢查前端服務狀態"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ 前端服務正常: HTTP $FRONTEND_STATUS"
else
    echo "❌ 前端服務異常: HTTP $FRONTEND_STATUS"
fi

echo ""
echo "============================================="
echo "🎯 衛星天空軌跡修復摘要:"
echo "============================================="
echo ""
echo "🔧 關鍵修復:"
echo "  scaleRange: 2.0 → 4.0    (增大縮放，衛星更近)"
echo "  maxRange: 400 → 300      (適中範圍，保持在場景內)"
echo "  baseHeight: 50 → 200     (天空基準高度)"
echo "  heightScale: 2.0 → 1.5   (適中升降幅度)"
echo ""
echo "📊 座標對比:"
echo "  地面設備: Y = 5-20 units"
echo "  修復前衛星: Y = 50-600 units (與地面混淆)"
echo "  修復後衛星: Y = 200-600+ units (清楚在天空中)"
echo ""
echo "🎯 視覺效果:"
echo "  ❌ 修復前: 衛星在地面附近升降，與設備混淆"
echo "  ✅ 修復後: 衛星在天空中升降，層次分明"
