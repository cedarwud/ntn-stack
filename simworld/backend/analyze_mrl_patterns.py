#!/usr/bin/env python3
"""
分析 MRL 距離模式，找出不合理的跳躍
"""

import json
from pathlib import Path

def analyze_mrl_patterns():
    """分析 MRL 距離的變化模式"""
    
    # 讀取數據
    data_file = Path("/home/sat/ntn-stack/data/starlink_120min_d2_enhanced.json")
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # 分析前兩顆衛星
    for sat_idx in range(min(2, len(data["satellites"]))):
        satellite = data["satellites"][sat_idx]
        mrl_distances = satellite["mrl_distances"]
        
        print(f"\n衛星 {satellite['name']}:")
        print(f"  數據點數: {len(mrl_distances)}")
        print(f"  最小距離: {min(mrl_distances):.1f} km")
        print(f"  最大距離: {max(mrl_distances):.1f} km")
        
        # 找出大的跳躍
        jumps = []
        for i in range(1, len(mrl_distances)):
            diff = abs(mrl_distances[i] - mrl_distances[i-1])
            if diff > 1000:  # 超過 1000 km 的跳躍
                jumps.append({
                    'index': i,
                    'from': mrl_distances[i-1],
                    'to': mrl_distances[i],
                    'diff': diff,
                    'time': i * 10 / 60  # 分鐘
                })
        
        print(f"  大跳躍 (>1000km): {len(jumps)} 個")
        for jump in jumps[:5]:  # 顯示前5個
            print(f"    {jump['time']:.1f}分: {jump['from']:.1f} -> {jump['to']:.1f} km (差異: {jump['diff']:.1f} km)")
        
        # 檢查時間序列數據
        if "time_series" in satellite and satellite["time_series"]:
            print(f"\n  檢查對應的位置數據:")
            for jump in jumps[:3]:
                idx = jump['index']
                if idx < len(satellite["time_series"]):
                    ts_before = satellite["time_series"][idx-1]
                    ts_after = satellite["time_series"][idx]
                    
                    lat_before = ts_before["position"]["latitude"]
                    lon_before = ts_before["position"]["longitude"]
                    lat_after = ts_after["position"]["latitude"]
                    lon_after = ts_after["position"]["longitude"]
                    
                    print(f"    索引 {idx}: ({lat_before:.2f}, {lon_before:.2f}) -> ({lat_after:.2f}, {lon_after:.2f})")
                    
                    # 檢查是否有大的位置跳躍
                    lat_diff = abs(lat_after - lat_before)
                    lon_diff = abs(lon_after - lon_before)
                    if lat_diff > 30 or lon_diff > 30:
                        print(f"      ⚠️  大位置跳躍: 緯度差 {lat_diff:.1f}°, 經度差 {lon_diff:.1f}°")

if __name__ == "__main__":
    analyze_mrl_patterns()