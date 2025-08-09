#!/usr/bin/env python3
"""
NTPU 座標上空所有衛星的完整可見性分析
計算全部 8,039 顆 Starlink + 651 顆 OneWeb 衛星
"""

import os
import sys
from datetime import datetime, timezone
import math
from typing import List, Tuple, Dict
import json

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

def full_constellation_analysis(tle_file_path: str, constellation_name: str, 
                               target_time: datetime = None) -> Dict:
    """全量分析所有衛星"""
    
    if target_time is None:
        target_time = datetime(2025, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    
    print(f"\n🛰️ 【全量分析】{constellation_name} 星座")
    print(f"📍 觀測點: NTPU ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E)")
    print(f"⏰ 分析時間: {target_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📄 TLE 文件: {os.path.basename(tle_file_path)}")
    
    # 解析所有衛星
    satellites_tle = parse_tle_file(tle_file_path)
    total_satellites = len(satellites_tle)
    print(f"📊 TLE 總衛星數: {total_satellites} 顆")
    print(f"🔄 開始全量計算...")
    
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
    error_details = []
    
    # 處理所有衛星
    for i, (name, line1, line2) in enumerate(satellites_tle):
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
            if (i + 1) % 500 == 0 or i + 1 == total_satellites:
                progress = (i + 1) * 100 / total_satellites
                print(f"  進度: {i + 1:,}/{total_satellites:,} ({progress:.1f}%) - 成功:{processed:,} 失敗:{errors}")
            
        except Exception as e:
            errors += 1
            if errors <= 10:  # 記錄前10個錯誤詳情
                error_details.append(f"{name}: {str(e)}")
    
    print(f"✅ 計算完成: {processed:,} 顆成功, {errors} 顆失敗")
    
    if error_details:
        print("⚠️ 錯誤詳情 (前10個):")
        for error in error_details:
            print(f"  - {error}")
    
    # 計算統計數據
    if processed > 0:
        # 精確數量 (不是推算)
        visible_count = len(elevation_stats['visible_satellites'])
        above_5deg_count = len(elevation_stats['above_5deg'])
        above_10deg_count = len(elevation_stats['above_10deg'])
        above_15deg_count = len(elevation_stats['above_15deg'])
        above_20deg_count = len(elevation_stats['above_20deg'])
        above_30deg_count = len(elevation_stats['above_30deg'])
        
        # 統計信息
        elevations = elevation_stats['all_elevations']
        max_elevation = max(elevations) if elevations else 0
        min_elevation = min(elevations) if elevations else 0
        avg_elevation = sum(elevations) / len(elevations) if elevations else 0
        
        print(f"\n📊 {constellation_name} 完整統計 (全量計算):")
        print("=" * 70)
        print(f"計算成功率: {processed:,}/{total_satellites:,} ({processed*100/total_satellites:.1f}%)")
        print(f"仰角範圍: {min_elevation:.2f}° ~ {max_elevation:.2f}°")
        print(f"平均仰角: {avg_elevation:.2f}°")
        print()
        print("精確可見衛星統計:")
        print(f"仰角 ≥  0°: {visible_count:4d} 顆 ({visible_count*100/processed:.1f}%)")
        print(f"仰角 ≥  5°: {above_5deg_count:4d} 顆 ({above_5deg_count*100/processed:.1f}%)")
        print(f"仰角 ≥ 10°: {above_10deg_count:4d} 顆 ({above_10deg_count*100/processed:.1f}%)")
        print(f"仰角 ≥ 15°: {above_15deg_count:4d} 顆 ({above_15deg_count*100/processed:.1f}%)")
        print(f"仰角 ≥ 20°: {above_20deg_count:4d} 顆 ({above_20deg_count*100/processed:.1f}%)")
        print(f"仰角 ≥ 30°: {above_30deg_count:4d} 顆 ({above_30deg_count*100/processed:.1f}%)")
        
        # 顯示最高仰角的衛星
        if elevation_stats['visible_satellites']:
            print(f"\n🔝 最高仰角前5顆衛星:")
            top_sats = sorted(elevation_stats['visible_satellites'], 
                             key=lambda x: x['elevation'], reverse=True)[:5]
            for i, sat in enumerate(top_sats, 1):
                print(f"{i}. {sat['name']:<25} {sat['elevation']:6.2f}° {sat['azimuth']:6.2f}° {sat['distance']:7.1f}km")
        
        return {
            'constellation': constellation_name,
            'timestamp': target_time.isoformat(),
            'total_satellites': total_satellites,
            'processed': processed,
            'errors': errors,
            'visible_count': visible_count,
            'above_5deg_count': above_5deg_count,
            'above_10deg_count': above_10deg_count,
            'above_15deg_count': above_15deg_count,
            'above_20deg_count': above_20deg_count,
            'above_30deg_count': above_30deg_count,
            'max_elevation': max_elevation,
            'min_elevation': min_elevation,
            'avg_elevation': avg_elevation,
            'top_satellites': top_sats[:5] if elevation_stats['visible_satellites'] else []
        }
    
    return {}

def save_results(results_data: Dict, filename: str):
    """保存結果到JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    print(f"💾 結果已保存到: {filename}")

def main():
    """主函數"""
    print("🛰️ NTPU 座標全量衛星可見性分析")
    print("計算所有真實衛星的精確可見性")
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
    
    # 全量分析 Starlink
    print("\n" + "="*70)
    starlink_results = full_constellation_analysis(starlink_tle, "Starlink", analysis_time)
    
    # 全量分析 OneWeb  
    print("\n" + "="*70)
    oneweb_results = full_constellation_analysis(oneweb_tle, "OneWeb", analysis_time)
    
    # 最終總結
    print(f"\n🎯 NTPU 座標全量衛星可見性結果")
    print("基於真實 TLE 數據 (2025-08-08) 和完整 SGP4 計算")
    print("=" * 80)
    
    if starlink_results and oneweb_results:
        print(f"分析時間: {analysis_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"觀測位置: NTPU ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E)")
        print(f"計算狀態: Starlink {starlink_results['processed']:,}/{starlink_results['total_satellites']:,}, OneWeb {oneweb_results['processed']:,}/{oneweb_results['total_satellites']:,}")
        print()
        
        # 精確統計表格
        thresholds = [0, 5, 10, 15, 20, 30]
        print("精確可見衛星統計 (不是推算):")
        print("-" * 60)
        for threshold in thresholds:
            if threshold == 0:
                starlink_count = starlink_results['visible_count']
                oneweb_count = oneweb_results['visible_count']
                desc = "(地平線以上)"
            else:
                starlink_count = starlink_results[f'above_{threshold}deg_count']
                oneweb_count = oneweb_results[f'above_{threshold}deg_count']
                desc = ""
            
            total_count = starlink_count + oneweb_count
            print(f"仰角 ≥ {threshold:2d}°: Starlink {starlink_count:4d} + OneWeb {oneweb_count:3d} = {total_count:4d} 顆 {desc}")
        
        # 關鍵答案
        starlink_5deg = starlink_results['above_5deg_count']
        oneweb_5deg = oneweb_results['above_5deg_count']
        total_5deg = starlink_5deg + oneweb_5deg
        
        print(f"\n✅ 完整答案 (基於全量真實計算):")
        print(f"📍 在 NTPU 座標 ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E)")
        print(f"⏰ 在 {analysis_time.strftime('%Y-%m-%d %H:%M UTC')} 時間點")
        print(f"🛰️ 仰角 ≥ 5° 的真實可見衛星數量:")
        print(f"   • Starlink: {starlink_5deg} 顆 (來自 {starlink_results['total_satellites']:,} 顆)")
        print(f"   • OneWeb:   {oneweb_5deg} 顆 (來自 {oneweb_results['total_satellites']} 顆)")  
        print(f"   • 總計:     {total_5deg} 顆")
        print(f"\n📊 這是基於全部 {starlink_results['total_satellites']:,} + {oneweb_results['total_satellites']} = {starlink_results['total_satellites'] + oneweb_results['total_satellites']:,} 顆衛星的完整計算")
        print(f"🎯 不是統計推算，而是精確的真實數字")
        
        # 保存詳細結果
        combined_results = {
            'analysis_metadata': {
                'timestamp': analysis_time.isoformat(),
                'observer_location': {
                    'lat': NTPU_LAT,
                    'lon': NTPU_LON,
                    'alt_m': NTPU_ALT_M
                },
                'calculation_method': 'Full SGP4 computation',
                'data_source': 'CelesTrak TLE 2025-08-08'
            },
            'starlink': starlink_results,
            'oneweb': oneweb_results,
            'summary': {
                'total_satellites': starlink_results['total_satellites'] + oneweb_results['total_satellites'],
                'total_processed': starlink_results['processed'] + oneweb_results['processed'],
                'visible_counts': {
                    'elevation_0deg': starlink_results['visible_count'] + oneweb_results['visible_count'],
                    'elevation_5deg': starlink_5deg + oneweb_5deg,
                    'elevation_10deg': starlink_results['above_10deg_count'] + oneweb_results['above_10deg_count'],
                    'elevation_15deg': starlink_results['above_15deg_count'] + oneweb_results['above_15deg_count'],
                    'elevation_20deg': starlink_results['above_20deg_count'] + oneweb_results['above_20deg_count'],
                    'elevation_30deg': starlink_results['above_30deg_count'] + oneweb_results['above_30deg_count']
                }
            }
        }
        
        # 保存結果
        save_results(combined_results, f"/home/sat/ntn-stack/ntpu_satellite_visibility_full_{analysis_time.strftime('%Y%m%d_%H%M')}.json")

if __name__ == "__main__":
    main()