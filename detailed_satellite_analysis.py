#!/usr/bin/env python3
"""
詳細衛星可見性分析 - 使用更大樣本提高準確度
"""

import os
import sys
from datetime import datetime, timezone
import math
from typing import List, Tuple, Dict
import random

# 安裝必要的套件
def install_packages():
    import subprocess
    packages = ['skyfield', 'numpy']
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"安裝 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

try:
    install_packages()
    from skyfield.api import Loader, utc, wgs84
    from skyfield.sgp4lib import EarthSatellite
    import numpy as np
except ImportError as e:
    print(f"❌ 無法導入必要套件: {e}")
    sys.exit(1)

# NTPU 座標
NTPU_LAT = 24.9441667
NTPU_LON = 121.3713889
NTPU_ALT_M = 50

def parse_tle_file(tle_file_path: str) -> List[Tuple[str, str, str]]:
    """解析 TLE 文件"""
    satellites = []
    
    with open(tle_file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            name = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]
            
            if line1.startswith('1 ') and line2.startswith('2 '):
                satellites.append((name, line1, line2))
    
    return satellites

def calculate_satellite_visibility(satellite: EarthSatellite, observer_lat: float, 
                                  observer_lon: float, observer_alt_m: float, 
                                  timestamp: datetime) -> Tuple[float, float, float]:
    """計算衛星可見性參數"""
    
    load = Loader('/tmp', verbose=False)
    ts = load.timescale()
    t = ts.from_datetime(timestamp.replace(tzinfo=utc))
    
    observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_alt_m)
    difference = satellite - observer
    topocentric = difference.at(t)
    alt, az, distance = topocentric.altaz()
    
    return alt.degrees, az.degrees, distance.km

def detailed_analysis(tle_file_path: str, constellation_name: str, 
                     sample_size: int = 500, target_time: datetime = None) -> Dict:
    """詳細分析，使用隨機採樣提高準確度"""
    
    if target_time is None:
        target_time = datetime(2025, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    
    print(f"\n🛰️ 詳細分析 {constellation_name} 星座")
    print(f"📍 觀測點: NTPU ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E)")
    print(f"⏰ 分析時間: {target_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📄 TLE 文件: {os.path.basename(tle_file_path)}")
    
    # 解析所有衛星
    satellites_tle = parse_tle_file(tle_file_path)
    total_satellites = len(satellites_tle)
    print(f"📊 TLE 總衛星數: {total_satellites} 顆")
    
    # 隨機選擇樣本進行分析
    sample_size = min(sample_size, total_satellites)
    sample_satellites = random.sample(satellites_tle, sample_size)
    print(f"🎯 隨機採樣: {sample_size} 顆衛星")
    
    # 統計結果
    elevation_stats = {
        'all_elevations': [],
        'visible_satellites': [],  # elevation >= 0
        'above_5deg': [],
        'above_10deg': [],
        'above_15deg': [],
        'above_20deg': [],
        'above_30deg': []
    }
    
    processed = 0
    errors = 0
    
    print("🔄 處理樣本衛星...")
    for i, (name, line1, line2) in enumerate(sample_satellites):
        try:
            satellite = EarthSatellite(line1, line2, name)
            elevation, azimuth, distance = calculate_satellite_visibility(
                satellite, NTPU_LAT, NTPU_LON, NTPU_ALT_M, target_time
            )
            
            elevation_stats['all_elevations'].append(elevation)
            
            sat_info = {
                'name': name,
                'elevation': round(elevation, 2),
                'azimuth': round(azimuth, 2),
                'distance': round(distance, 2)
            }
            
            if elevation >= 0:
                elevation_stats['visible_satellites'].append(sat_info)
            if elevation >= 5:
                elevation_stats['above_5deg'].append(sat_info)
            if elevation >= 10:
                elevation_stats['above_10deg'].append(sat_info)
            if elevation >= 15:
                elevation_stats['above_15deg'].append(sat_info)
            if elevation >= 20:
                elevation_stats['above_20deg'].append(sat_info)
            if elevation >= 30:
                elevation_stats['above_30deg'].append(sat_info)
            
            processed += 1
            
            # 進度顯示
            if (i + 1) % 100 == 0:
                print(f"  進度: {i + 1}/{sample_size} ({(i + 1) * 100 / sample_size:.1f}%)")
            
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"⚠️ 計算失敗: {name} - {str(e)[:50]}...")
    
    print(f"✅ 處理完成: {processed} 顆成功, {errors} 顆失敗")
    
    # 計算統計數據
    if processed > 0:
        # 計算各仰角門檻的比例
        visible_ratio = len(elevation_stats['visible_satellites']) / processed
        above_5deg_ratio = len(elevation_stats['above_5deg']) / processed
        above_10deg_ratio = len(elevation_stats['above_10deg']) / processed
        above_15deg_ratio = len(elevation_stats['above_15deg']) / processed
        above_20deg_ratio = len(elevation_stats['above_20deg']) / processed
        above_30deg_ratio = len(elevation_stats['above_30deg']) / processed
        
        # 推算總數
        estimated_visible = int(visible_ratio * total_satellites)
        estimated_5deg = int(above_5deg_ratio * total_satellites)
        estimated_10deg = int(above_10deg_ratio * total_satellites)
        estimated_15deg = int(above_15deg_ratio * total_satellites)
        estimated_20deg = int(above_20deg_ratio * total_satellites)
        estimated_30deg = int(above_30deg_ratio * total_satellites)
        
        # 統計信息
        elevations = elevation_stats['all_elevations']
        max_elevation = max(elevations) if elevations else 0
        avg_elevation = sum(elevations) / len(elevations) if elevations else 0
        
        print(f"\n📊 {constellation_name} 詳細統計:")
        print("=" * 70)
        print(f"樣本成功率: {processed}/{sample_size} ({processed*100/sample_size:.1f}%)")
        print(f"最高仰角: {max_elevation:.2f}°")
        print(f"平均仰角: {avg_elevation:.2f}°")
        print("\n可見衛星推算:")
        print(f"仰角 ≥  0°: {len(elevation_stats['visible_satellites']):3d} 樣本 → ~{estimated_visible:4d} 顆 ({visible_ratio*100:.1f}%)")
        print(f"仰角 ≥  5°: {len(elevation_stats['above_5deg']):3d} 樣本 → ~{estimated_5deg:4d} 顆 ({above_5deg_ratio*100:.1f}%)")
        print(f"仰角 ≥ 10°: {len(elevation_stats['above_10deg']):3d} 樣本 → ~{estimated_10deg:4d} 顆 ({above_10deg_ratio*100:.1f}%)")
        print(f"仰角 ≥ 15°: {len(elevation_stats['above_15deg']):3d} 樣本 → ~{estimated_15deg:4d} 顆 ({above_15deg_ratio*100:.1f}%)")
        print(f"仰角 ≥ 20°: {len(elevation_stats['above_20deg']):3d} 樣本 → ~{estimated_20deg:4d} 顆 ({above_20deg_ratio*100:.1f}%)")
        print(f"仰角 ≥ 30°: {len(elevation_stats['above_30deg']):3d} 樣本 → ~{estimated_30deg:4d} 顆 ({above_30deg_ratio*100:.1f}%)")
        
        # 顯示最高仰角的衛星
        if elevation_stats['visible_satellites']:
            print(f"\n🔝 最高仰角前5顆衛星:")
            top_sats = sorted(elevation_stats['visible_satellites'], 
                             key=lambda x: x['elevation'], reverse=True)[:5]
            for i, sat in enumerate(top_sats, 1):
                print(f"{i}. {sat['name']:<25} {sat['elevation']:6.2f}° {sat['azimuth']:6.2f}° {sat['distance']:7.1f}km")
        
        return {
            'total_satellites': total_satellites,
            'sample_size': sample_size,
            'processed': processed,
            'estimated_visible': estimated_visible,
            'estimated_5deg': estimated_5deg,
            'estimated_10deg': estimated_10deg,
            'estimated_15deg': estimated_15deg,
            'estimated_20deg': estimated_20deg,
            'estimated_30deg': estimated_30deg,
            'max_elevation': max_elevation,
            'avg_elevation': avg_elevation,
            'visible_ratio': visible_ratio,
            'above_5deg_ratio': above_5deg_ratio
        }
    
    return {}

def main():
    """主函數"""
    print("🛰️ NTPU 座標詳細衛星可見性分析")
    print("使用真實 TLE 數據和 SGP4 軌道計算")
    print("=" * 70)
    
    # 分析時間點
    analysis_time = datetime(2025, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    print(f"📅 分析時間: {analysis_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📍 觀測位置: NTPU ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E, {NTPU_ALT_M}m)")
    
    # TLE 文件路徑
    starlink_tle = "/home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_20250808.tle"
    oneweb_tle = "/home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_20250808.tle"
    
    # 檢查文件
    if not os.path.exists(starlink_tle):
        print(f"❌ 找不到 Starlink TLE 文件: {starlink_tle}")
        return
    if not os.path.exists(oneweb_tle):
        print(f"❌ 找不到 OneWeb TLE 文件: {oneweb_tle}")
        return
    
    # 設定隨機種子確保結果可重現
    random.seed(42)
    
    # 分析 Starlink (更大樣本)
    starlink_results = detailed_analysis(starlink_tle, "Starlink", sample_size=800, target_time=analysis_time)
    
    # 分析 OneWeb (全部分析)
    oneweb_results = detailed_analysis(oneweb_tle, "OneWeb", sample_size=600, target_time=analysis_time)
    
    # 最終總結
    print(f"\n🎯 NTPU 座標可見衛星最終結果")
    print("基於真實 TLE 數據 (2025-08-08) 和 SGP4 軌道計算")
    print("=" * 80)
    
    if starlink_results and oneweb_results:
        print(f"分析時間: {analysis_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"觀測位置: NTPU ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E)")
        print()
        
        for threshold in [0, 5, 10, 15, 20]:
            starlink_count = starlink_results.get(f'estimated_{threshold}deg', starlink_results.get('estimated_visible', 0) if threshold == 0 else 0)
            oneweb_count = oneweb_results.get(f'estimated_{threshold}deg', oneweb_results.get('estimated_visible', 0) if threshold == 0 else 0)
            total_count = starlink_count + oneweb_count
            
            if threshold == 0:
                print(f"仰角 ≥  {threshold}°: Starlink ~{starlink_count:4d} + OneWeb ~{oneweb_count:3d} = 總計 ~{total_count:4d} 顆 (地平線以上)")
            else:
                print(f"仰角 ≥ {threshold:2d}°: Starlink ~{starlink_count:4d} + OneWeb ~{oneweb_count:3d} = 總計 ~{total_count:4d} 顆")
        
        # 重點回答
        starlink_5deg = starlink_results.get('estimated_5deg', 0)
        oneweb_5deg = oneweb_results.get('estimated_5deg', 0)
        total_5deg = starlink_5deg + oneweb_5deg
        
        print(f"\n✅ 用戶問題答案:")
        print(f"🛰️ 在 NTPU 座標任意時間點 (以 2025-08-09 12:00 UTC 為例)")
        print(f"📐 仰角 ≥ 5° 的真實可見衛星數量:")
        print(f"   • Starlink: ~{starlink_5deg} 顆")
        print(f"   • OneWeb:   ~{oneweb_5deg} 顆")  
        print(f"   • 總計:     ~{total_5deg} 顆")
        print(f"\n💡 這個數字會隨時間變化，因為衛星在軌道上持續移動")
        print(f"📊 使用真實 TLE 數據 (2025-08-08) 和標準 SGP4 軌道計算")

if __name__ == "__main__":
    main()