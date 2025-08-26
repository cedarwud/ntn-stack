#!/usr/bin/env python3
"""
OneWeb 可見性檢測調試腳本
單獨測試 OneWeb 衛星的可見性計算邏輯
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

# 添加 netstack 模塊路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')
sys.path.insert(0, '/home/sat/ntn-stack/netstack')

from shared_core.observer_config_service import ObserverConfigService
from shared_core.visibility_service import SatelliteVisibilityService
from services.satellite.coordinate_specific_orbit_engine import CoordinateSpecificOrbitEngine
from data.tle_data_loader import TLEDataLoader


def debug_oneweb_visibility():
    """調試 OneWeb 可見性檢測失敗問題"""
    print("🔍 OneWeb 可見性檢測調試")
    print("=" * 60)
    
    # 1. 初始化配置和服務
    print("📐 初始化觀測配置...")
    observer_config = ObserverConfigService()
    observer_lat, observer_lon = observer_config.get_observer_coordinates()
    print(f"   觀測座標: ({observer_lat:.6f}°, {observer_lon:.6f}°)")
    
    print("🛰️ 初始化軌道引擎...")
    orbit_engine = CoordinateSpecificOrbitEngine()
    
    print("👁️ 初始化可見性服務...")
    visibility_service = SatelliteVisibilityService()
    
    # 2. 載入測試 OneWeb TLE 數據
    print("\n📡 載入 OneWeb TLE 數據...")
    tle_loader = TLEDataLoader()
    
    # 找到最新的 OneWeb TLE 文件
    oneweb_tle_dir = "/home/sat/ntn-stack/netstack/tle_data/oneweb/tle"
    tle_files = [f for f in os.listdir(oneweb_tle_dir) if f.endswith('.tle')]
    tle_files.sort()  # 按文件名排序，最新的在最後
    
    if not tle_files:
        print("❌ 未找到 OneWeb TLE 文件")
        return
    
    latest_tle_file = os.path.join(oneweb_tle_dir, tle_files[-1])
    print(f"   使用 TLE 文件: {latest_tle_file}")
    
    # 載入前5顆衛星進行測試
    oneweb_satellites = tle_loader.load_constellation_tle_data("oneweb", latest_tle_file)
    test_satellites = list(oneweb_satellites.items())[:5]  # 只測試前5顆
    
    print(f"   載入測試衛星: {len(test_satellites)} 顆")
    
    # 3. 對每顆衛星執行詳細的可見性檢測
    print("\n🔬 詳細可見性檢測分析:")
    print("-" * 60)
    
    for i, (sat_id, tle_data) in enumerate(test_satellites):
        print(f"\n📡 衛星 {i+1}: {sat_id}")
        print(f"   TLE Line1: {tle_data.line1}")
        print(f"   TLE Line2: {tle_data.line2}")
        
        try:
            # 計算 OneWeb 軌道週期 (120分鐘)
            orbit_result = orbit_engine.compute_120min_orbital_cycle(tle_data, tle_data.epoch)
            
            if not orbit_result or not orbit_result.position_timeseries:
                print("   ❌ 軌道計算失敗")
                continue
            
            print(f"   ✅ 軌道計算完成: {len(orbit_result.position_timeseries)} 個時間點")
            
            # 檢查前幾個位置點
            for j, pos in enumerate(orbit_result.position_timeseries[:3]):
                print(f"      點 {j}: 緯度={pos['latitude']:.2f}°, 經度={pos['longitude']:.2f}°, 高度={pos['altitude']:.0f}km")
            
            # 執行可見性檢測
            print("   🔍 執行可見性檢測...")
            
            # 準備衛星數據格式 (模仿 Stage 2 的格式)
            satellite_data = {
                'satellite_id': sat_id,
                'constellation': 'oneweb',
                'position_timeseries': orbit_result.position_timeseries
            }
            
            # 執行批量可見性檢測
            visibility_results = visibility_service.batch_check_visibility(
                satellites=[satellite_data],
                constellation='oneweb'
            )
            
            print(f"   📊 可見性檢測結果: {len(visibility_results)} 個結果")
            
            if visibility_results:
                enhanced_satellite = visibility_results[0]
                timeseries = enhanced_satellite.get('position_timeseries', [])
                
                # 統計可見時間點
                visible_count = 0
                max_elevation = -90.0
                visible_elevations = []
                
                for point in timeseries:
                    vis_info = point.get('visibility_info', {})
                    elevation = vis_info.get('elevation_deg', -90.0)
                    max_elevation = max(max_elevation, elevation)
                    
                    if vis_info.get('is_visible', False):
                        visible_count += 1
                        visible_elevations.append(elevation)
                
                total_visibility_minutes = visible_count * 0.5  # 30秒間隔 = 0.5分鐘
                
                print(f"      可見時間點: {visible_count}/{len(timeseries)}")
                print(f"      總可見時間: {total_visibility_minutes:.1f} 分鐘")
                print(f"      最高仰角: {max_elevation:.2f}° (門檻: 10°)")
                
                if visible_count > 0:
                    print("   ✅ 衛星有可見時間！")
                    avg_visible_elevation = sum(visible_elevations) / len(visible_elevations)
                    print(f"      平均可見仰角: {avg_visible_elevation:.2f}°")
                    print(f"      可見時間比例: {visible_count/len(timeseries)*100:.1f}%")
                else:
                    print("   ❌ 衛星無可見時間")
                    
                    if max_elevation < 10.0:
                        print(f"      ❌ 原因: 最高仰角 {max_elevation:.2f}° < 門檻 10°")
                    else:
                        print(f"      🤔 異常: 最高仰角 {max_elevation:.2f}° >= 門檻 10°，但未檢測到可見時間")
                        
                        # 顯示幾個高仰角點的詳細信息
                        high_elevation_points = [p for p in timeseries 
                                               if p.get('visibility_info', {}).get('elevation_deg', -90) > 5.0]
                        print(f"      🔍 仰角 > 5° 的時間點: {len(high_elevation_points)} 個")
                        for k, point in enumerate(high_elevation_points[:3]):
                            vis_info = point.get('visibility_info', {})
                            print(f"         點 {k+1}: 仰角={vis_info.get('elevation_deg', -90):.2f}°, 可見={vis_info.get('is_visible', False)}")
            else:
                print("   ❌ 可見性檢測返回空結果")
            
        except Exception as e:
            print(f"   ❌ 處理失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 OneWeb 可見性調試完成")


if __name__ == '__main__':
    debug_oneweb_visibility()