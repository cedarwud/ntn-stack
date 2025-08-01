#!/usr/bin/env python3
"""
平滑化 MRL 數據，移除不合理的跳躍
只保留連續的軌道段落
"""

import json
import math
from pathlib import Path
from datetime import datetime

def calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon):
    """計算 UE 到衛星 MRL 的大圓距離"""
    lat1_rad = math.radians(ue_lat)
    lat2_rad = math.radians(sat_lat)
    delta_lat = math.radians(sat_lat - ue_lat)
    delta_lon = math.radians(sat_lon - ue_lon)
    
    a = (math.sin(delta_lat / 2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2)**2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    earth_radius = 6371.0
    return earth_radius * c

def smooth_satellite_data(satellite, ue_lat, ue_lon):
    """平滑化單顆衛星的數據"""
    
    # 找出所有連續的軌道段落
    segments = []
    current_segment = {'start': 0, 'end': 0}
    
    for i in range(1, len(satellite["time_series"])):
        prev_pos = satellite["time_series"][i-1]["position"]
        curr_pos = satellite["time_series"][i]["position"]
        
        # 計算位置變化
        lat_diff = abs(curr_pos["latitude"] - prev_pos["latitude"])
        lon_diff = abs(curr_pos["longitude"] - prev_pos["longitude"])
        
        # 如果有大跳躍（緯度超過10度或經度超過20度），結束當前段落
        if lat_diff > 10 or lon_diff > 20:
            current_segment['end'] = i - 1
            if current_segment['end'] - current_segment['start'] > 10:  # 至少要有10個點
                segments.append(current_segment)
            current_segment = {'start': i, 'end': i}
        else:
            current_segment['end'] = i
    
    # 添加最後一個段落
    if current_segment['end'] - current_segment['start'] > 10:
        segments.append(current_segment)
    
    # 重建平滑的數據
    new_mrl_distances = []
    new_mrl_locations = []
    new_time_series = []
    
    for seg in segments:
        # 對每個連續段落，重新計算 MRL 距離
        for i in range(seg['start'], seg['end'] + 1):
            ts_entry = satellite["time_series"][i]
            sat_lat = ts_entry["position"]["latitude"]
            sat_lon = ts_entry["position"]["longitude"]
            
            # 計算 MRL 距離
            mrl_distance = calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon)
            
            new_mrl_distances.append(mrl_distance)
            new_mrl_locations.append({"lat": sat_lat, "lon": sat_lon})
            new_time_series.append(ts_entry)
    
    return new_mrl_distances, new_mrl_locations, new_time_series

def smooth_mrl_data():
    """平滑化所有衛星的 MRL 數據"""
    
    print("🔧 平滑化 MRL 數據...")
    
    for constellation in ["starlink", "oneweb"]:
        input_file = Path(f"/home/sat/ntn-stack/data/{constellation}_120min_d2_enhanced.json")
        if not input_file.exists():
            continue
        
        print(f"\n📡 處理 {constellation}...")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # UE 位置
        ue_location = data["metadata"]["d2_enhancement"]["ue_location"]
        ue_lat = ue_location["lat"]
        ue_lon = ue_location["lon"]
        
        # 找出最好的兩顆衛星（最接近 UE 的）
        best_satellites = []
        
        for sat_idx, satellite in enumerate(data["satellites"]):
            # 計算平均 MRL 距離
            if satellite["mrl_distances"]:
                # 只考慮合理範圍內的距離（<5000km）
                reasonable_distances = [d for d in satellite["mrl_distances"] if d < 5000]
                if reasonable_distances:
                    avg_distance = sum(reasonable_distances) / len(reasonable_distances)
                    min_distance = min(reasonable_distances)
                    best_satellites.append({
                        'index': sat_idx,
                        'satellite': satellite,
                        'avg_distance': avg_distance,
                        'min_distance': min_distance,
                        'coverage_ratio': len(reasonable_distances) / len(satellite["mrl_distances"])
                    })
        
        # 按最小距離排序，選擇最好的衛星
        best_satellites.sort(key=lambda x: x['min_distance'])
        
        # 重建數據，只保留最好的衛星
        new_satellites = []
        
        # 選擇會經過 UE 附近的衛星
        for sat_info in best_satellites[:10]:  # 最多保留10顆
            satellite = sat_info['satellite']
            
            # 平滑化數據
            new_mrl_distances, new_mrl_locations, new_time_series = smooth_satellite_data(
                satellite, ue_lat, ue_lon
            )
            
            if new_mrl_distances:  # 如果有有效數據
                # 創建新的衛星數據
                new_satellite = {
                    "norad_id": satellite["norad_id"],
                    "name": satellite["name"],
                    "constellation": satellite["constellation"],
                    "mrl_distances": new_mrl_distances,
                    "moving_reference_locations": new_mrl_locations,
                    "time_series": new_time_series
                }
                
                # 填充缺失的時間點為無效值
                if len(new_mrl_distances) < 720:
                    # 用大距離值填充
                    padding_count = 720 - len(new_mrl_distances)
                    new_satellite["mrl_distances"].extend([20000] * padding_count)
                    new_satellite["moving_reference_locations"].extend([{"lat": 0, "lon": 0}] * padding_count)
                
                new_satellites.append(new_satellite)
                
                print(f"  ✅ {satellite['name']}: {len(new_mrl_distances)} 個有效點, " +
                      f"最小距離 {min(new_mrl_distances):.1f} km")
        
        # 更新數據
        data["satellites"] = new_satellites[:2]  # 只保留前兩顆最好的衛星
        
        # 更新元數據
        data["metadata"]["d2_enhancement"]["smoothed"] = True
        data["metadata"]["d2_enhancement"]["enhanced_at"] = datetime.utcnow().isoformat() + "Z"
        
        # 保存
        output_file = Path(f"data/{constellation}_120min_d2_smoothed.json")
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # 複製到主目錄
        import shutil
        main_file = Path(f"/home/sat/ntn-stack/data/{constellation}_120min_d2_enhanced.json")
        shutil.copy(output_file, main_file)
        
        print(f"  💾 已保存平滑化數據")

if __name__ == "__main__":
    smooth_mrl_data()
    print("\n✅ 完成！")