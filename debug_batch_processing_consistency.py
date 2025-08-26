#!/usr/bin/env python3
"""
批量處理一致性調試腳本
測試 Stage 2 的完整數據流路徑，與個別測試進行對比
"""

import json
import os
import sys

# 添加 netstack 模塊路徑
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')

from shared_core.visibility_service import SatelliteVisibilityService

def debug_batch_processing_consistency():
    """調試批量處理與個別處理的一致性問題"""
    print("🔍 批量處理一致性調試")
    print("=" * 60)
    
    # 載入 Stage 1 的 OneWeb 數據
    stage1_output_file = "/app/data/tle_orbital_calculation_output.json"
    
    if not os.path.exists(stage1_output_file):
        print("❌ Stage 1 輸出文件不存在")
        return
    
    with open(stage1_output_file, 'r', encoding='utf-8') as f:
        stage1_data = json.load(f)
    
    # 提取 OneWeb 數據
    oneweb_data = stage1_data.get('constellations', {}).get('oneweb', {})
    satellites_dict = oneweb_data.get('orbit_data', {}).get('satellites', {})
    
    if not satellites_dict:
        print("❌ 未找到 OneWeb 衛星數據")
        return
    
    # 轉換字典為列表
    satellites_list = []
    for sat_id, sat_data in satellites_dict.items():
        sat_data['satellite_id'] = sat_id
        satellites_list.append(sat_data)
    
    print(f"📡 載入 {len(satellites_list)} 顆 OneWeb 衛星數據")
    
    # 測試不同規模的批量處理
    test_sizes = [5, 10, 20, 50, 100, 200, 651]
    
    visibility_service = SatelliteVisibilityService()
    
    for test_size in test_sizes:
        if test_size > len(satellites_list):
            continue
            
        print(f"\n🧪 測試批量大小: {test_size} 顆衛星")
        print("-" * 40)
        
        # 選擇測試衛星
        test_satellites = satellites_list[:test_size]
        
        # 執行與 Stage 2 相同的數據格式轉換
        print("  🔧 執行數據格式轉換...")
        converted_satellites = []
        
        for satellite in test_satellites:
            converted_satellite = satellite.copy()
            
            # 轉換數據格式 (模擬 Stage 2 的轉換邏輯)
            if 'positions' in satellite:
                positions = satellite['positions']
                converted_positions = []
                
                for pos in positions:
                    threshold = 10.0  # OneWeb 10° 門檻
                    
                    converted_pos = {
                        'latitude': pos.get('lat', 0),
                        'longitude': pos.get('lon', 0), 
                        'altitude': pos.get('alt_km', 0),
                        'timestamp': pos.get('time', ''),
                        'elevation_deg': pos.get('elevation_deg', 0),
                        'azimuth_deg': pos.get('azimuth_deg', 0),
                        'range_km': pos.get('range_km', 0),
                        'is_visible': pos.get('elevation_deg', 0) >= threshold
                    }
                    converted_positions.append(converted_pos)
                
                converted_satellite['position_timeseries'] = converted_positions
                print(f"    衛星 {satellite.get('satellite_id', 'Unknown')}: {len(converted_positions)} 個時間點")
            
            converted_satellites.append(converted_satellite)
        
        # 執行批量可見性檢查
        print("  🔍 執行批量可見性檢查...")
        
        try:
            visible_satellites = visibility_service.filter_visible_satellites(
                converted_satellites, 
                'oneweb', 
                min_visibility_duration_minutes=2.0
            )
            
            visible_count = len(visible_satellites)
            print(f"  ✅ 結果: {visible_count}/{test_size} 顆衛星通過可見性檢查")
            
            if visible_count > 0:
                print("  📊 通過檢查的衛星:")
                for i, sat in enumerate(visible_satellites[:3]):  # 只顯示前3顆
                    stats = sat.get('visibility_stats', {})
                    visible_duration = stats.get('total_visible_duration_minutes', 0)
                    print(f"    {i+1}. {sat.get('satellite_id', 'Unknown')}: {visible_duration:.1f} 分鐘")
            else:
                print("  ❌ 沒有衛星通過可見性檢查")
                
                # 深入調試第一顆衛星
                if converted_satellites:
                    first_sat = converted_satellites[0]
                    print(f"  🔬 調試第一顆衛星: {first_sat.get('satellite_id', 'Unknown')}")
                    
                    timeseries = first_sat.get('position_timeseries', [])
                    visible_points = sum(1 for p in timeseries if p.get('is_visible', False))
                    max_elevation = max((p.get('elevation_deg', -90) for p in timeseries), default=-90)
                    
                    print(f"     時間序列點數: {len(timeseries)}")
                    print(f"     可見時間點: {visible_points}")
                    print(f"     最高仰角: {max_elevation:.2f}°")
                    print(f"     可見時間: {visible_points * 0.5:.1f} 分鐘")
                    
                    if visible_points * 0.5 >= 2.0:
                        print(f"     🤔 異常: 可見時間 {visible_points * 0.5:.1f} 分鐘 >= 門檻 2.0 分鐘，但未通過檢查")
        
        except Exception as e:
            print(f"  ❌ 批量處理失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 批量處理一致性調試完成")

if __name__ == '__main__':
    debug_batch_processing_consistency()