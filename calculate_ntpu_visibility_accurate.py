#!/usr/bin/env python3
"""
精確計算 NTPU 上空在完整軌道週期內的平均可見衛星數量
使用最新的 TLE 數據和正確的座標轉換
"""

import json
import numpy as np
from datetime import datetime, timedelta, timezone
from sgp4.api import Satrec, jday, SGP4_ERRORS
import math

# NTPU 觀測點座標
OBSERVER_LAT = 24.9441667  # 度
OBSERVER_LON = 121.3713889  # 度
OBSERVER_ALT = 0.0  # 米

def parse_tle_file(tle_file_path):
    """解析 TLE 文件"""
    satellites = []
    with open(tle_file_path, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        if i + 2 < len(lines):
            name = lines[i].strip()
            line1 = lines[i + 1].strip()
            line2 = lines[i + 2].strip()
            
            if line1.startswith('1 ') and line2.startswith('2 '):
                try:
                    satellite = Satrec.twoline2rv(line1, line2)
                    satellites.append({
                        'name': name,
                        'satellite': satellite,
                        'line1': line1,
                        'line2': line2
                    })
                except:
                    pass
            i += 3
        else:
            break
    
    return satellites

def calculate_elevation_azimuth_accurate(sat_eci, obs_lat, obs_lon, obs_alt, current_time):
    """
    精確計算衛星相對於地面觀測站的仰角和方位角
    使用 ECI 到 topocentric 座標系轉換
    """
    from pyproj import Transformer
    
    # 地球參數
    EARTH_RADIUS_KM = 6378.137  # WGS84 赤道半徑
    EARTH_FLATTENING = 1/298.257223563  # WGS84 扁率
    
    # 將觀測點轉換為 ECEF
    lat_rad = math.radians(obs_lat)
    lon_rad = math.radians(obs_lon)
    
    # WGS84 橢球體計算
    N = EARTH_RADIUS_KM / math.sqrt(1 - EARTH_FLATTENING * (2 - EARTH_FLATTENING) * math.sin(lat_rad)**2)
    obs_x_ecef = (N + obs_alt/1000) * math.cos(lat_rad) * math.cos(lon_rad)
    obs_y_ecef = (N + obs_alt/1000) * math.cos(lat_rad) * math.sin(lon_rad)
    obs_z_ecef = (N * (1 - EARTH_FLATTENING)**2 + obs_alt/1000) * math.sin(lat_rad)
    
    # 計算 GMST (Greenwich Mean Sidereal Time)
    # 簡化計算，足夠用於演示
    days_since_j2000 = (current_time - datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)).total_seconds() / 86400
    gmst_deg = (280.46061837 + 360.98564736629 * days_since_j2000) % 360
    gmst_rad = math.radians(gmst_deg)
    
    # ECI 到 ECEF 轉換（考慮地球自轉）
    cos_gmst = math.cos(gmst_rad)
    sin_gmst = math.sin(gmst_rad)
    
    sat_x_ecef = sat_eci[0] * cos_gmst + sat_eci[1] * sin_gmst
    sat_y_ecef = -sat_eci[0] * sin_gmst + sat_eci[1] * cos_gmst
    sat_z_ecef = sat_eci[2]
    
    # 計算相對位置向量
    dx = sat_x_ecef - obs_x_ecef
    dy = sat_y_ecef - obs_y_ecef
    dz = sat_z_ecef - obs_z_ecef
    
    # 轉換到 topocentric 座標系 (ENU: East-North-Up)
    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_lon = math.sin(lon_rad)
    cos_lon = math.cos(lon_rad)
    
    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    
    # 計算距離、仰角和方位角
    horizontal_distance = math.sqrt(east**2 + north**2)
    distance = math.sqrt(east**2 + north**2 + up**2)
    
    # 仰角（從水平面算起）
    elevation_rad = math.atan2(up, horizontal_distance)
    elevation_deg = math.degrees(elevation_rad)
    
    # 方位角（從北算起，順時針）
    azimuth_rad = math.atan2(east, north)
    azimuth_deg = math.degrees(azimuth_rad)
    if azimuth_deg < 0:
        azimuth_deg += 360
    
    return elevation_deg, azimuth_deg, distance

def analyze_constellation_visibility(tle_file_path, constellation_name, orbital_period_minutes):
    """分析星座在完整軌道週期內的可見性"""
    print(f"\n{'='*60}")
    print(f"分析 {constellation_name} 可見性")
    print(f"TLE 文件: {tle_file_path}")
    print(f"軌道週期: {orbital_period_minutes} 分鐘")
    print(f"{'='*60}")
    
    # 載入 TLE 數據
    satellites = parse_tle_file(tle_file_path)
    print(f"載入 {len(satellites)} 顆衛星")
    
    # 設定時間範圍（完整軌道週期）
    start_time = datetime(2025, 8, 21, 0, 0, 0, tzinfo=timezone.utc)
    time_step_seconds = 30  # 30秒間隔
    num_steps = int(orbital_period_minutes * 60 / time_step_seconds)
    
    # 統計每個時間點的可見衛星
    visibility_stats = {
        '5deg': [],   # ≥5° 仰角
        '10deg': [],  # ≥10° 仰角
        '15deg': [],  # ≥15° 仰角
    }
    
    elevation_samples = []  # 收集所有正仰角樣本
    
    print(f"\n計算 {num_steps} 個時間點...")
    
    for step in range(num_steps):
        current_time = start_time + timedelta(seconds=step * time_step_seconds)
        
        # 轉換為 Julian Date
        jd, fr = jday(current_time.year, current_time.month, current_time.day,
                     current_time.hour, current_time.minute, current_time.second)
        
        # 統計這個時間點的可見衛星
        visible_5deg = 0
        visible_10deg = 0
        visible_15deg = 0
        
        for sat_data in satellites:
            satellite = sat_data['satellite']
            
            # SGP4 計算
            error, position, velocity = satellite.sgp4(jd, fr)
            
            if error == 0:  # 無錯誤
                # 精確計算仰角
                elevation, azimuth, distance = calculate_elevation_azimuth_accurate(
                    position, OBSERVER_LAT, OBSERVER_LON, OBSERVER_ALT, current_time
                )
                
                # 收集正仰角樣本
                if elevation > 0:
                    elevation_samples.append(elevation)
                
                # 統計不同仰角門檻
                if elevation >= 5:
                    visible_5deg += 1
                if elevation >= 10:
                    visible_10deg += 1
                if elevation >= 15:
                    visible_15deg += 1
        
        # 記錄統計
        visibility_stats['5deg'].append(visible_5deg)
        visibility_stats['10deg'].append(visible_10deg)
        visibility_stats['15deg'].append(visible_15deg)
        
        # 進度顯示
        if step % 20 == 0 or step == num_steps - 1:
            print(f"  進度: {step+1}/{num_steps} - 時間: {current_time.strftime('%H:%M:%S')} - "
                  f"可見: ≥5°:{visible_5deg}, ≥10°:{visible_10deg}, ≥15°:{visible_15deg}")
    
    # 計算統計結果
    print(f"\n📊 {constellation_name} 可見性統計結果:")
    print(f"{'='*60}")
    
    # 顯示仰角分佈
    if elevation_samples:
        print(f"仰角分佈 (所有正仰角樣本):")
        print(f"  平均仰角: {np.mean(elevation_samples):.1f}°")
        print(f"  最大仰角: {np.max(elevation_samples):.1f}°")
        print(f"  中位數仰角: {np.median(elevation_samples):.1f}°")
    
    print(f"\n仰角 ≥ 5° (低仰角門檻):")
    print(f"  平均可見: {np.mean(visibility_stats['5deg']):.1f} 顆")
    print(f"  最大可見: {np.max(visibility_stats['5deg'])} 顆")
    print(f"  最小可見: {np.min(visibility_stats['5deg'])} 顆")
    print(f"  標準差: {np.std(visibility_stats['5deg']):.1f}")
    
    print(f"\n仰角 ≥ 10° (標準門檻):")
    print(f"  平均可見: {np.mean(visibility_stats['10deg']):.1f} 顆")
    print(f"  最大可見: {np.max(visibility_stats['10deg'])} 顆")
    print(f"  最小可見: {np.min(visibility_stats['10deg'])} 顆")
    print(f"  標準差: {np.std(visibility_stats['10deg']):.1f}")
    
    print(f"\n仰角 ≥ 15° (高品質門檻):")
    print(f"  平均可見: {np.mean(visibility_stats['15deg']):.1f} 顆")
    print(f"  最大可見: {np.max(visibility_stats['15deg'])} 顆")
    print(f"  最小可見: {np.min(visibility_stats['15deg'])} 顆")
    print(f"  標準差: {np.std(visibility_stats['15deg']):.1f}")
    
    return {
        '5deg': np.mean(visibility_stats['5deg']),
        '10deg': np.mean(visibility_stats['10deg']),
        '15deg': np.mean(visibility_stats['15deg'])
    }

def main():
    """主程序"""
    print("🛰️ NTPU 衛星可見性精確分析")
    print(f"觀測點: NTPU ({OBSERVER_LAT}°N, {OBSERVER_LON}°E, {OBSERVER_ALT}m)")
    print(f"使用最新 TLE 數據和精確座標轉換進行計算")
    
    # 分析 Starlink (最新: 2025-08-21)
    starlink_tle = "/home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_20250821.tle"
    starlink_stats = analyze_constellation_visibility(
        starlink_tle, "Starlink", 96  # 96分鐘軌道週期
    )
    
    # 分析 OneWeb (最新: 2025-08-22)
    oneweb_tle = "/home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_20250822.tle"
    oneweb_stats = analyze_constellation_visibility(
        oneweb_tle, "OneWeb", 109  # 109分鐘軌道週期
    )
    
    # 總結
    print(f"\n{'='*60}")
    print("📋 總結: NTPU 上空平均可見衛星數量")
    print(f"{'='*60}")
    print(f"\n🛰️ Starlink (96分鐘軌道週期):")
    print(f"  仰角 ≥ 5°: 平均 {starlink_stats['5deg']:.1f} 顆可見")
    print(f"  仰角 ≥ 10°: 平均 {starlink_stats['10deg']:.1f} 顆可見")
    print(f"  仰角 ≥ 15°: 平均 {starlink_stats['15deg']:.1f} 顆可見")
    
    print(f"\n🛰️ OneWeb (109分鐘軌道週期):")
    print(f"  仰角 ≥ 10°: 平均 {oneweb_stats['10deg']:.1f} 顆可見")
    print(f"  仰角 ≥ 15°: 平均 {oneweb_stats['15deg']:.1f} 顆可見")
    
    print(f"\n💡 建議前端動態範圍設定:")
    print(f"  Starlink: 0-{int(starlink_stats['5deg']*2)} 顆 (平均 {int(starlink_stats['5deg'])} 顆，仰角≥5°)")
    print(f"  OneWeb: 0-{int(oneweb_stats['10deg']*2)} 顆 (平均 {int(oneweb_stats['10deg'])} 顆，仰角≥10°)")
    
    print(f"\n📊 現實情況分析:")
    print(f"  - Starlink 應該只有 10-25 顆可見（不是 3000+ 顆）")
    print(f"  - OneWeb 應該只有 3-8 顆可見（不是 300+ 顆）")
    print(f"  - 計算可能包含了所有衛星，而非只有 NTPU 上空的")

if __name__ == "__main__":
    main()