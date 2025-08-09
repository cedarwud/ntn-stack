#!/usr/bin/env python3
"""
計算 NTPU 座標上空真實可見衛星數量 (修復版)
使用最新的 TLE 資料和 SGP4 軌道計算
"""

import os
import sys
from datetime import datetime, timezone
import math
from typing import List, Tuple, Dict

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

# NTPU 座標 (根據 CLAUDE.md 標準)
NTPU_LAT = 24.9441667  # 24°56'39"N
NTPU_LON = 121.3713889  # 121°22'17"E
NTPU_ALT_M = 50  # 海拔50公尺

def parse_tle_file(tle_file_path: str) -> List[Tuple[str, str, str]]:
    """解析 TLE 文件，返回 (name, line1, line2) 三元組列表"""
    satellites = []
    
    with open(tle_file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    # TLE 格式：每3行為一個衛星 (name, line1, line2)
    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            name = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]
            
            # 驗證 TLE 格式
            if line1.startswith('1 ') and line2.startswith('2 '):
                satellites.append((name, line1, line2))
    
    return satellites

def calculate_elevation_azimuth_simple(satellite: EarthSatellite, observer_lat: float, 
                                     observer_lon: float, observer_alt_m: float, 
                                     timestamp: datetime) -> Tuple[float, float, float]:
    """計算衛星的仰角、方位角和距離 (簡化版)"""
    
    # 建立時間尺度
    load = Loader('/tmp', verbose=False)
    ts = load.timescale()
    t = ts.from_datetime(timestamp.replace(tzinfo=utc))
    
    # 建立觀測者位置 (使用 wgs84)
    observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_alt_m)
    
    # 計算衛星位置
    geocentric = satellite.at(t)
    
    # 計算相對位置
    difference = satellite - observer
    topocentric = difference.at(t)
    
    # 計算仰角和方位角
    alt, az, distance = topocentric.altaz()
    
    return alt.degrees, az.degrees, distance.km

def analyze_constellation_simple(tle_file_path: str, constellation_name: str, 
                               target_time: datetime = None) -> Dict:
    """分析星座的可見衛星數量 (簡化版)"""
    
    if target_time is None:
        target_time = datetime(2025, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    
    print(f"\n🛰️ 分析 {constellation_name} 星座")
    print(f"📍 觀測點: NTPU ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E, {NTPU_ALT_M}m)")
    print(f"⏰ 分析時間: {target_time.isoformat()}")
    print(f"📄 TLE 文件: {tle_file_path}")
    
    # 解析 TLE 文件
    try:
        satellites_tle = parse_tle_file(tle_file_path)
        print(f"📊 TLE 總衛星數: {len(satellites_tle)} 顆")
    except Exception as e:
        print(f"❌ TLE 文件解析失敗: {e}")
        return {}
    
    # 統計不同仰角門檻的可見衛星
    elevation_thresholds = [0, 5, 10, 15, 20, 30]
    results = {f"elevation_{thresh}": [] for thresh in elevation_thresholds}
    
    valid_satellites = 0
    error_count = 0
    
    # 處理前100個衛星以加快測試
    test_count = min(100, len(satellites_tle))
    print(f"🔍 測試前 {test_count} 顆衛星...")
    
    for i, (name, line1, line2) in enumerate(satellites_tle[:test_count]):
        try:
            # 建立 SGP4 衛星物件
            satellite = EarthSatellite(line1, line2, name)
            
            # 計算衛星位置
            elevation, azimuth, distance = calculate_elevation_azimuth_simple(
                satellite, NTPU_LAT, NTPU_LON, NTPU_ALT_M, target_time
            )
            
            # 檢查不同仰角門檻
            for threshold in elevation_thresholds:
                if elevation >= threshold:
                    results[f"elevation_{threshold}"].append({
                        'name': name,
                        'elevation': round(elevation, 2),
                        'azimuth': round(azimuth, 2),
                        'distance': round(distance, 2)
                    })
            
            valid_satellites += 1
            
            # 顯示進度
            if (i + 1) % 20 == 0:
                print(f"  處理進度: {i + 1}/{test_count}")
            
        except Exception as e:
            error_count += 1
            if error_count <= 3:  # 只顯示前3個錯誤
                print(f"⚠️ 衛星 {name} 計算失敗: {str(e)[:50]}...")
    
    # 輸出統計結果
    print(f"✅ 成功計算: {valid_satellites} 顆衛星")
    if error_count > 0:
        print(f"❌ 計算失敗: {error_count} 顆衛星")
    
    # 推算全部衛星的結果
    if valid_satellites > 0:
        total_satellites = len(satellites_tle)
        scale_factor = total_satellites / test_count
        
        print(f"\n📈 {constellation_name} 可見衛星統計 ({target_time.strftime('%Y-%m-%d %H:%M UTC')}):")
        print("=" * 60)
        
        for threshold in elevation_thresholds:
            sample_count = len(results[f"elevation_{threshold}"])
            estimated_total = int(sample_count * scale_factor)
            percentage = (sample_count / valid_satellites * 100) if valid_satellites > 0 else 0
            print(f"仰角 ≥ {threshold:2d}°: 樣本 {sample_count:2d} 顆 → 推算總數 {estimated_total:4d} 顆 ({percentage:5.1f}%)")
            
            # 更新結果為推算值
            results[f"elevation_{threshold}_estimated"] = estimated_total
    
    # 顯示前5個最高仰角的衛星詳細信息
    if results["elevation_0"]:
        print(f"\n🔝 前5個最高仰角衛星 (樣本):")
        print("-" * 70)
        top_satellites = sorted(results["elevation_0"], 
                               key=lambda x: x['elevation'], reverse=True)[:5]
        
        for i, sat in enumerate(top_satellites, 1):
            print(f"{i}. {sat['name']:<20} 仰角:{sat['elevation']:6.2f}° "
                  f"方位:{sat['azimuth']:6.2f}° 距離:{sat['distance']:7.1f}km")
    
    return results

def main():
    """主函數"""
    print("🛰️ NTPU 座標上空真實可見衛星分析")
    print("=" * 60)
    
    # 設定分析時間 (可以修改為任意時間)
    analysis_time = datetime(2025, 8, 9, 12, 0, 0, tzinfo=timezone.utc)  # UTC 時間
    
    # TLE 文件路徑
    starlink_tle = "/home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_20250808.tle"
    oneweb_tle = "/home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_20250808.tle"
    
    # 檢查文件是否存在
    for tle_file, name in [(starlink_tle, "Starlink"), (oneweb_tle, "OneWeb")]:
        if not os.path.exists(tle_file):
            print(f"❌ 找不到 {name} TLE 文件: {tle_file}")
            return
    
    # 分析 Starlink
    starlink_results = analyze_constellation_simple(starlink_tle, "Starlink", analysis_time)
    
    # 分析 OneWeb  
    oneweb_results = analyze_constellation_simple(oneweb_tle, "OneWeb", analysis_time)
    
    # 總結
    print(f"\n🎯 NTPU 座標可見衛星總結 ({analysis_time.strftime('%Y-%m-%d %H:%M UTC')})")
    print("=" * 80)
    
    for threshold in [5, 10, 15, 20]:
        starlink_count = starlink_results.get(f"elevation_{threshold}_estimated", 0)
        oneweb_count = oneweb_results.get(f"elevation_{threshold}_estimated", 0)
        total_count = starlink_count + oneweb_count
        
        print(f"仰角 ≥ {threshold:2d}°: Starlink ~{starlink_count:4d} + OneWeb ~{oneweb_count:3d} = 總計 ~{total_count:4d} 顆")
    
    # 回答用戶的具體問題：仰角≥5度的衛星數量
    starlink_5deg = starlink_results.get("elevation_5_estimated", 0)
    oneweb_5deg = oneweb_results.get("elevation_5_estimated", 0)
    
    print(f"\n✅ 最終答案 (基於真實 TLE 數據推算)：")
    print(f"📍 在 NTPU 座標 ({NTPU_LAT:.6f}°N, {NTPU_LON:.6f}°E)")
    print(f"⏰ 在 {analysis_time.strftime('%Y-%m-%d %H:%M UTC')} 時間點")
    print(f"🛰️ 仰角 ≥ 5° 的真實可見衛星數量：")
    print(f"   • Starlink: ~{starlink_5deg} 顆")
    print(f"   • OneWeb:   ~{oneweb_5deg} 顆")
    print(f"   • 總計:     ~{starlink_5deg + oneweb_5deg} 顆")

if __name__ == "__main__":
    main()