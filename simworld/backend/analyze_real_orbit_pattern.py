#!/usr/bin/env python3
"""
分析真實衛星軌道數據的完整120分鐘模式
驗證是否可以產生雙正弦波形
"""

import json
import math
# import matplotlib.pyplot as plt  # 暫時移除
from pathlib import Path

def calculate_mrl_distance(ue_lat: float, ue_lon: float, sat_lat: float, sat_lon: float) -> float:
    """計算 UE 到衛星 MRL (nadir point) 的大圓距離"""
    ue_lat_rad = math.radians(ue_lat)
    ue_lon_rad = math.radians(ue_lon)
    sat_lat_rad = math.radians(sat_lat)
    sat_lon_rad = math.radians(sat_lon)
    
    dlat = sat_lat_rad - ue_lat_rad
    dlon = sat_lon_rad - ue_lon_rad
    
    a = math.sin(dlat/2)**2 + math.cos(ue_lat_rad) * math.cos(sat_lat_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    earth_radius = 6371.0
    distance = earth_radius * c
    
    return distance

def analyze_real_orbit():
    """分析真實軌道數據"""
    
    print("🔍 分析真實衛星軌道的完整120分鐘模式...")
    
    # 台灣 NTPU 位置
    ue_lat, ue_lon = 24.9463, 121.367
    
    # 讀取真實數據
    input_file = Path("/home/sat/ntn-stack/data/starlink_120min_timeseries.json")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # 分析前3顆衛星的完整軌道
    for sat_idx in range(min(3, len(data['satellites']))):
        satellite = data['satellites'][sat_idx]
        time_series = satellite['time_series']
        
        print(f"\n🛰️ 衛星 {satellite['name']} ({satellite['norad_id']}):")
        
        # 計算所有720個點的距離
        distances = []
        times = []
        
        for i, point in enumerate(time_series):
            sat_lat = point['position']['latitude']
            sat_lon = point['position']['longitude']
            
            distance = calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon)
            distances.append(distance)
            times.append(i * 10 / 60)  # 轉換為分鐘
        
        # 分析軌道特徵
        min_dist = min(distances)
        max_dist = max(distances)
        avg_dist = sum(distances) / len(distances)
        
        print(f"  距離範圍: {min_dist:.1f} - {max_dist:.1f} km")
        print(f"  平均距離: {avg_dist:.1f} km")
        print(f"  變化幅度: {max_dist - min_dist:.1f} km")
        
        # 檢查是否有週期性模式
        # 分析距離變化的頻率特徵
        derivatives = [distances[i+1] - distances[i] for i in range(len(distances)-1)]
        sign_changes = 0
        for i in range(len(derivatives)-1):
            if derivatives[i] * derivatives[i+1] < 0:
                sign_changes += 1
        
        print(f"  方向變化次數: {sign_changes} (理想軌道約2-4次)")
        
        # 找出最接近和最遠的時間點
        min_time = times[distances.index(min_dist)]
        max_time = times[distances.index(max_dist)]
        
        print(f"  最近點時間: {min_time:.1f} 分鐘")
        print(f"  最遠點時間: {max_time:.1f} 分鐘")
        
        # 判斷軌道模式
        if max_dist - min_dist > 500 and sign_changes >= 2:
            print(f"  ✅ 具有明顯的軌道動力學特徵")
        else:
            print(f"  ⚠️ 軌道變化較小或缺乏週期性")
    
    # 尋找最佳的兩顆衛星組合
    print(f"\n🔍 尋找最佳D2換手組合...")
    
    satellite_profiles = []
    for sat_idx, satellite in enumerate(data['satellites'][:10]):  # 只分析前10顆
        time_series = satellite['time_series']
        distances = []
        
        for point in time_series:
            sat_lat = point['position']['latitude']
            sat_lon = point['position']['longitude']
            distance = calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon)
            distances.append(distance)
        
        if distances:
            profile = {
                'satellite': satellite,
                'distances': distances,
                'min_dist': min(distances),
                'max_dist': max(distances),
                'avg_dist': sum(distances) / len(distances),
                'range': max(distances) - min(distances)
            }
            satellite_profiles.append(profile)
    
    # 選擇距離變化模式互補的兩顆衛星
    if len(satellite_profiles) >= 2:
        # 排序：距離變化大的優先
        satellite_profiles.sort(key=lambda x: x['range'], reverse=True)
        
        sat1 = satellite_profiles[0]
        sat2 = satellite_profiles[1]
        
        print(f"推薦組合:")
        print(f"  服務衛星: {sat1['satellite']['name']} - 距離變化 {sat1['range']:.0f}km")
        print(f"  目標衛星: {sat2['satellite']['name']} - 距離變化 {sat2['range']:.0f}km")
        
        # 檢查交叉點
        crossings = 0
        for i in range(len(sat1['distances'])):
            if i > 0:
                if ((sat1['distances'][i-1] > sat2['distances'][i-1] and sat1['distances'][i] < sat2['distances'][i]) or
                    (sat1['distances'][i-1] < sat2['distances'][i-1] and sat1['distances'][i] > sat2['distances'][i])):
                    crossings += 1
        
        print(f"  距離交叉點: {crossings} 個")
        
        if crossings > 0:
            print(f"  ✅ 存在真實的D2換手機會")
        else:
            print(f"  ⚠️ 缺乏明顯的換手交叉點")

if __name__ == "__main__":
    analyze_real_orbit()