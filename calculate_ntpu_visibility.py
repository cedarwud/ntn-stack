#!/usr/bin/env python3
"""
計算 NTPU 上空在完整軌道週期內的平均可見衛星數量
使用最新的 TLE 數據進行真實計算
"""

import json
import numpy as np
from datetime import datetime, timedelta, timezone
from sgp4.api import Satrec, jday
import math

# NTPU 觀測點座標
OBSERVER_LAT = 24.9441667  # 度
OBSERVER_LON = 121.3713889  # 度
OBSERVER_ALT = 0.0  # 米

# 地球參數
EARTH_RADIUS_KM = 6371.0

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

def calculate_observer_position(lat, lon, alt):
    """計算觀測點的 ECI 座標"""
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    # 簡化計算：假設地球為球體
    r = EARTH_RADIUS_KM + alt / 1000.0
    x = r * math.cos(lat_rad) * math.cos(lon_rad)
    y = r * math.cos(lat_rad) * math.sin(lon_rad)
    z = r * math.sin(lat_rad)
    
    return np.array([x, y, z])

def calculate_elevation_azimuth(sat_pos_eci, obs_pos_eci, time_utc):
    """計算衛星的仰角和方位角"""
    # 衛星相對於觀測點的向量
    rel_pos = sat_pos_eci - obs_pos_eci
    distance = np.linalg.norm(rel_pos)
    
    # 簡化的仰角計算
    # 使用地心角來估算仰角
    sat_r = np.linalg.norm(sat_pos_eci)
    obs_r = np.linalg.norm(obs_pos_eci)
    
    # 計算地心角
    cos_angle = np.dot(sat_pos_eci, obs_pos_eci) / (sat_r * obs_r)
    geocentric_angle = math.degrees(math.acos(min(1.0, max(-1.0, cos_angle))))
    
    # 粗略的仰角估算
    if geocentric_angle < 90:
        # 衛星在地平線以上
        elevation = 90 - geocentric_angle
        # 考慮衛星高度的修正
        sat_alt = sat_r - EARTH_RADIUS_KM
        if sat_alt > 0:
            elevation = elevation * (1 + sat_alt / 1000)
    else:
        elevation = -90 + (180 - geocentric_angle)
    
    # 簡化的方位角計算（不精確，但足夠用於統計）
    azimuth = math.degrees(math.atan2(rel_pos[1], rel_pos[0])) % 360
    
    return elevation, azimuth, distance

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
    
    # 觀測點位置
    obs_pos_eci = calculate_observer_position(OBSERVER_LAT, OBSERVER_LON, OBSERVER_ALT)
    
    # 統計每個時間點的可見衛星
    visibility_stats = {
        'starlink_5deg': [],  # Starlink ≥5° 仰角
        'starlink_10deg': [], # Starlink ≥10° 仰角
        'oneweb_10deg': [],   # OneWeb ≥10° 仰角
        'oneweb_15deg': []    # OneWeb ≥15° 仰角
    }
    
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
            
            if error == 0:
                # 計算仰角
                elevation, azimuth, distance = calculate_elevation_azimuth(
                    np.array(position), obs_pos_eci, current_time
                )
                
                # 統計不同仰角門檻
                if elevation >= 5:
                    visible_5deg += 1
                if elevation >= 10:
                    visible_10deg += 1
                if elevation >= 15:
                    visible_15deg += 1
        
        # 記錄統計
        if constellation_name == "Starlink":
            visibility_stats['starlink_5deg'].append(visible_5deg)
            visibility_stats['starlink_10deg'].append(visible_10deg)
        else:  # OneWeb
            visibility_stats['oneweb_10deg'].append(visible_10deg)
            visibility_stats['oneweb_15deg'].append(visible_15deg)
        
        # 進度顯示
        if step % 20 == 0:
            print(f"  進度: {step}/{num_steps} - 時間: {current_time.strftime('%H:%M:%S')} - "
                  f"可見: ≥5°:{visible_5deg}, ≥10°:{visible_10deg}, ≥15°:{visible_15deg}")
    
    # 計算統計結果
    print(f"\n📊 {constellation_name} 可見性統計結果:")
    print(f"{'='*60}")
    
    if constellation_name == "Starlink":
        stats_5deg = visibility_stats['starlink_5deg']
        stats_10deg = visibility_stats['starlink_10deg']
        
        print(f"仰角 ≥ 5° (標準門檻):")
        print(f"  平均可見: {np.mean(stats_5deg):.1f} 顆")
        print(f"  最大可見: {np.max(stats_5deg)} 顆")
        print(f"  最小可見: {np.min(stats_5deg)} 顆")
        print(f"  標準差: {np.std(stats_5deg):.1f}")
        
        print(f"\n仰角 ≥ 10° (高品質門檻):")
        print(f"  平均可見: {np.mean(stats_10deg):.1f} 顆")
        print(f"  最大可見: {np.max(stats_10deg)} 顆")
        print(f"  最小可見: {np.min(stats_10deg)} 顆")
        print(f"  標準差: {np.std(stats_10deg):.1f}")
        
        return np.mean(stats_5deg), np.mean(stats_10deg)
    
    else:  # OneWeb
        stats_10deg = visibility_stats['oneweb_10deg']
        stats_15deg = visibility_stats['oneweb_15deg']
        
        print(f"仰角 ≥ 10° (標準門檻):")
        print(f"  平均可見: {np.mean(stats_10deg):.1f} 顆")
        print(f"  最大可見: {np.max(stats_10deg)} 顆")
        print(f"  最小可見: {np.min(stats_10deg)} 顆")
        print(f"  標準差: {np.std(stats_10deg):.1f}")
        
        print(f"\n仰角 ≥ 15° (高品質門檻):")
        print(f"  平均可見: {np.mean(stats_15deg):.1f} 顆")
        print(f"  最大可見: {np.max(stats_15deg)} 顆")
        print(f"  最小可見: {np.min(stats_15deg)} 顆")
        print(f"  標準差: {np.std(stats_15deg):.1f}")
        
        return np.mean(stats_10deg), np.mean(stats_15deg)

def main():
    """主程序"""
    print("🛰️ NTPU 衛星可見性分析")
    print(f"觀測點: NTPU ({OBSERVER_LAT}°N, {OBSERVER_LON}°E)")
    print(f"使用最新 TLE 數據進行計算")
    
    # 分析 Starlink (最新: 2025-08-21)
    starlink_tle = "/home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_20250821.tle"
    starlink_avg_5deg, starlink_avg_10deg = analyze_constellation_visibility(
        starlink_tle, "Starlink", 96  # 96分鐘軌道週期
    )
    
    # 分析 OneWeb (最新: 2025-08-22)
    oneweb_tle = "/home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_20250822.tle"
    oneweb_avg_10deg, oneweb_avg_15deg = analyze_constellation_visibility(
        oneweb_tle, "OneWeb", 109  # 109分鐘軌道週期
    )
    
    # 總結
    print(f"\n{'='*60}")
    print("📋 總結: NTPU 上空平均可見衛星數量")
    print(f"{'='*60}")
    print(f"Starlink (96分鐘軌道週期):")
    print(f"  標準門檻 (≥5°): 平均 {starlink_avg_5deg:.1f} 顆可見")
    print(f"  高品質門檻 (≥10°): 平均 {starlink_avg_10deg:.1f} 顆可見")
    print(f"\nOneWeb (109分鐘軌道週期):")
    print(f"  標準門檻 (≥10°): 平均 {oneweb_avg_10deg:.1f} 顆可見")
    print(f"  高品質門檻 (≥15°): 平均 {oneweb_avg_15deg:.1f} 顆可見")
    print(f"\n建議前端動態範圍設定:")
    print(f"  Starlink: 0-{int(starlink_avg_5deg*1.5)} 顆 (平均 {int(starlink_avg_5deg)} 顆)")
    print(f"  OneWeb: 0-{int(oneweb_avg_10deg*1.5)} 顆 (平均 {int(oneweb_avg_10deg)} 顆)")

if __name__ == "__main__":
    main()