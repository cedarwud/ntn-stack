#!/usr/bin/env python3
"""
創建乾淨的 D2 事件數據 - 僅包含衛星可見期間
專注於真實的衛星通過，移除不可見期間的數據
"""

import json
import math
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

def calculate_mrl_distance(ue_lat: float, ue_lon: float, sat_lat: float, sat_lon: float) -> float:
    """計算 UE 到衛星 MRL (nadir point) 的大圓距離"""
    # 將經緯度轉換為弧度
    ue_lat_rad = math.radians(ue_lat)
    ue_lon_rad = math.radians(ue_lon)
    sat_lat_rad = math.radians(sat_lat)
    sat_lon_rad = math.radians(sat_lon)
    
    # Haversine 公式
    dlat = sat_lat_rad - ue_lat_rad
    dlon = sat_lon_rad - ue_lon_rad
    
    a = math.sin(dlat/2)**2 + math.cos(ue_lat_rad) * math.cos(sat_lat_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 地球半徑 (km)
    earth_radius = 6371.0
    distance = earth_radius * c
    
    return distance

def find_visible_periods(satellite: Dict, ue_lat: float, ue_lon: float, max_distance: float = 2000) -> List[Dict]:
    """找出衛星可見期間"""
    time_series = satellite.get("time_series", [])
    if not time_series:
        return []
    
    visible_periods = []
    current_period = None
    
    for i, timestamp_data in enumerate(time_series):
        # 提取衛星位置
        sat_lat = timestamp_data.get('position', {}).get('latitude', 0)
        sat_lon = timestamp_data.get('position', {}).get('longitude', 0)
        
        if sat_lat == 0 and sat_lon == 0:
            continue
            
        # 計算距離
        distance = calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon)
        
        if distance < max_distance:
            # 在可見範圍內
            if current_period is None:
                current_period = {
                    'start_idx': i,
                    'end_idx': i,
                    'min_distance': distance,
                    'max_distance': distance,
                    'avg_distance': distance,
                    'distances': [distance],
                    'positions': [(sat_lat, sat_lon)],
                    'timestamps': [timestamp_data]
                }
            else:
                current_period['end_idx'] = i
                current_period['min_distance'] = min(current_period['min_distance'], distance)
                current_period['max_distance'] = max(current_period['max_distance'], distance)
                current_period['distances'].append(distance)
                current_period['positions'].append((sat_lat, sat_lon))
                current_period['timestamps'].append(timestamp_data)
        else:
            # 超出可見範圍
            if current_period is not None and len(current_period['distances']) > 30:
                # 至少要有30個點（約5分鐘）
                current_period['avg_distance'] = sum(current_period['distances']) / len(current_period['distances'])
                visible_periods.append(current_period)
            current_period = None
    
    # 添加最後一個可見期間
    if current_period is not None and len(current_period['distances']) > 30:
        current_period['avg_distance'] = sum(current_period['distances']) / len(current_period['distances'])
        visible_periods.append(current_period)
    
    return visible_periods

def create_clean_d2_passes():
    """創建乾淨的 D2 通過數據"""
    
    print("🛰️ 創建乾淨的 D2 衛星通過數據...")
    
    # 台灣 NTPU 位置
    ue_lat, ue_lon = 24.9463, 121.367
    
    # 讀取原始數據
    input_file = Path("/home/sat/ntn-stack/data/starlink_120min_timeseries.json")
    if not input_file.exists():
        print(f"❌ 輸入文件不存在: {input_file}")
        return
    
    with open(input_file, 'r') as f:
        raw_data = json.load(f)
    
    print(f"原始數據包含 {len(raw_data['satellites'])} 顆衛星")
    
    # 找出所有衛星的可見期間
    all_visible_periods = []
    
    for sat_idx, satellite in enumerate(raw_data["satellites"]):
        if "time_series" not in satellite:
            continue
            
        periods = find_visible_periods(satellite, ue_lat, ue_lon)
        
        for period in periods:
            period['satellite'] = satellite
            period['sat_idx'] = sat_idx
            all_visible_periods.append(period)
    
    print(f"找到 {len(all_visible_periods)} 個可見期間")
    
    # 選擇最佳的兩個期間進行 D2 事件模擬
    if len(all_visible_periods) < 2:
        print("❌ 可見期間不足，無法創建 D2 事件")
        return
    
    # 按平均距離排序，選擇一個近的和一個遠的
    all_visible_periods.sort(key=lambda x: x['avg_distance'])
    
    serving_period = all_visible_periods[0]  # 最近的作為服務衛星
    
    # 找一個距離適中的作為目標衛星
    target_period = None
    for period in all_visible_periods[1:]:
        # 選擇平均距離在合理範圍內的
        if 400 < period['avg_distance'] < 1000:
            target_period = period
            break
    
    if target_period is None:
        target_period = all_visible_periods[1]  # 備選方案
    
    print(f"選擇的衛星:")
    print(f"  服務衛星: {serving_period['satellite']['name']} (平均距離: {serving_period['avg_distance']:.1f}km)")
    print(f"  目標衛星: {target_period['satellite']['name']} (平均距離: {target_period['avg_distance']:.1f}km)")
    
    # 創建乾淨的數據結構
    enhanced_data = {
        "metadata": raw_data["metadata"].copy(),
        "satellites": [],
        "timestamps": []
    }
    
    # 更新元數據
    enhanced_data["metadata"]["d2_enhancement"] = {
        "enhanced_at": datetime.utcnow().isoformat() + "Z",
        "mrl_method": "nadir_projection_clean",
        "thresholds": {
            "thresh1": 600.0,
            "thresh2": 400.0,
            "hysteresis": 20.0
        },
        "ue_location": {
            "lat": ue_lat,
            "lon": ue_lon,
            "alt": 0.0
        },
        "clean_passes_only": True,
        "data_points": max(len(serving_period['distances']), len(target_period['distances']))
    }
    
    # 確定數據長度（使用較長的那個期間）
    max_length = max(len(serving_period['distances']), len(target_period['distances']))
    
    # 創建時間戳數組
    if serving_period['timestamps']:
        enhanced_data["timestamps"] = serving_period['timestamps'][:max_length]
    
    # 處理服務衛星
    serving_sat = {
        "norad_id": serving_period['satellite']["norad_id"],
        "name": serving_period['satellite']["name"],
        "constellation": serving_period['satellite']["constellation"],
        "mrl_distances": serving_period['distances'][:max_length],
        "moving_reference_locations": [
            {"lat": pos[0], "lon": pos[1]} 
            for pos in serving_period['positions'][:max_length]
        ],
        "time_series": serving_period['timestamps'][:max_length]
    }
    
    # 處理目標衛星
    target_sat = {
        "norad_id": target_period['satellite']["norad_id"],
        "name": target_period['satellite']["name"],
        "constellation": target_period['satellite']["constellation"],
        "mrl_distances": target_period['distances'][:max_length],
        "moving_reference_locations": [
            {"lat": pos[0], "lon": pos[1]} 
            for pos in target_period['positions'][:max_length]
        ],
        "time_series": target_period['timestamps'][:max_length]
    }
    
    # 如果長度不匹配，補齊較短的那個
    if len(serving_sat['mrl_distances']) < max_length:
        last_distance = serving_sat['mrl_distances'][-1]
        last_pos = serving_sat['moving_reference_locations'][-1]
        while len(serving_sat['mrl_distances']) < max_length:
            serving_sat['mrl_distances'].append(last_distance)
            serving_sat['moving_reference_locations'].append(last_pos)
    
    if len(target_sat['mrl_distances']) < max_length:
        last_distance = target_sat['mrl_distances'][-1]
        last_pos = target_sat['moving_reference_locations'][-1]
        while len(target_sat['mrl_distances']) < max_length:
            target_sat['mrl_distances'].append(last_distance)
            target_sat['moving_reference_locations'].append(last_pos)
    
    enhanced_data["satellites"] = [serving_sat, target_sat]
    
    print(f"乾淨數據包含 {len(enhanced_data['satellites'])} 顆衛星，每顆 {max_length} 個數據點")
    print(f"服務衛星距離範圍: {min(serving_sat['mrl_distances']):.1f} - {max(serving_sat['mrl_distances']):.1f} km")
    print(f"目標衛星距離範圍: {min(target_sat['mrl_distances']):.1f} - {max(target_sat['mrl_distances']):.1f} km")
    
    # 儲存到主數據目錄
    output_file = Path("/home/sat/ntn-stack/data/starlink_120min_d2_enhanced.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 主數據文件已儲存: {output_file}")
    
    # 複製到後端數據目錄
    backend_file = Path("data/starlink_120min_d2_enhanced.json")
    backend_file.parent.mkdir(exist_ok=True)
    with open(backend_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 後端數據文件已儲存: {backend_file}")

if __name__ == "__main__":
    create_clean_d2_passes()