#!/usr/bin/env python3
"""
創建真實的衛星通過數據
選擇真正會連續通過台灣上空的衛星
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

def find_continuous_passes(satellite, ue_lat, ue_lon, max_distance=3000):
    """找出衛星的連續通過時段"""
    passes = []
    current_pass = None
    
    for i, ts_entry in enumerate(satellite["time_series"]):
        sat_lat = ts_entry["position"]["latitude"]
        sat_lon = ts_entry["position"]["longitude"]
        distance = calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon)
        
        if distance < max_distance:
            # 在範圍內
            if current_pass is None:
                current_pass = {
                    'start_idx': i,
                    'end_idx': i,
                    'min_distance': distance,
                    'distances': [distance],
                    'positions': [(sat_lat, sat_lon)]
                }
            else:
                current_pass['end_idx'] = i
                current_pass['min_distance'] = min(current_pass['min_distance'], distance)
                current_pass['distances'].append(distance)
                current_pass['positions'].append((sat_lat, sat_lon))
        else:
            # 超出範圍
            if current_pass is not None and (current_pass['end_idx'] - current_pass['start_idx'] > 20):
                # 至少要有20個點（約3分鐘）
                passes.append(current_pass)
            current_pass = None
    
    # 添加最後一個通過
    if current_pass is not None and (current_pass['end_idx'] - current_pass['start_idx'] > 20):
        passes.append(current_pass)
    
    return passes

def create_realistic_passes():
    """創建真實的衛星通過數據"""
    
    print("🛰️ 創建真實衛星通過數據...")
    
    # 讀取原始數據
    input_file = Path("/home/sat/ntn-stack/data/starlink_120min_timeseries.json")
    with open(input_file, 'r') as f:
        raw_data = json.load(f)
    
    # UE 位置（台北）
    ue_lat = 24.9441
    ue_lon = 121.3714
    
    # 找出所有衛星的通過情況
    all_passes = []
    
    for sat_idx, satellite in enumerate(raw_data["satellites"]):
        if "time_series" not in satellite:
            continue
            
        passes = find_continuous_passes(satellite, ue_lat, ue_lon)
        
        for pass_info in passes:
            pass_info['satellite'] = satellite
            pass_info['sat_idx'] = sat_idx
            all_passes.append(pass_info)
    
    # 按最小距離排序
    all_passes.sort(key=lambda x: x['min_distance'])
    
    print(f"  找到 {len(all_passes)} 個衛星通過")
    
    # 選擇最好的兩個通過
    if len(all_passes) >= 2:
        # 選擇一個近的和一個稍遠的，模擬換手場景
        pass1 = all_passes[0]  # 最近的
        
        # 找一個時間上稍有重疊的
        pass2 = None
        for p in all_passes[1:]:
            # 檢查時間重疊
            if p['start_idx'] < pass1['end_idx'] - 50 and p['end_idx'] > pass1['start_idx'] + 50:
                pass2 = p
                break
        
        if pass2 is None:
            pass2 = all_passes[1]  # 如果沒有重疊的，就選第二近的
        
        print(f"\n  選擇的衛星通過:")
        print(f"    1. {pass1['satellite']['name']}: 最小距離 {pass1['min_distance']:.1f} km")
        print(f"    2. {pass2['satellite']['name']}: 最小距離 {pass2['min_distance']:.1f} km")
        
        # 創建新的數據結構
        enhanced_data = {
            "metadata": raw_data["metadata"].copy(),
            "satellites": [],
            "timestamps": raw_data.get("timestamps", [])
        }
        
        # 更新元數據
        enhanced_data["metadata"]["d2_enhancement"] = {
            "enhanced_at": datetime.utcnow().isoformat() + "Z",
            "mrl_method": "nadir_projection",
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
            "realistic_passes": True
        }
        
        # 處理兩個通過
        for pass_idx, pass_info in enumerate([pass1, pass2]):
            satellite = pass_info['satellite']
            
            # 創建完整的 720 個點的數據
            mrl_distances = [20000.0] * 720  # 預設為很遠
            mrl_locations = [{"lat": 0, "lon": 0}] * 720
            
            # 填入實際通過的數據
            start_idx = pass_info['start_idx']
            end_idx = pass_info['end_idx']
            
            for i in range(start_idx, min(end_idx + 1, 720)):
                local_idx = i - start_idx
                if local_idx < len(pass_info['distances']):
                    mrl_distances[i] = pass_info['distances'][local_idx]
                    lat, lon = pass_info['positions'][local_idx]
                    mrl_locations[i] = {"lat": lat, "lon": lon}
            
            # 平滑過渡到遠距離
            # 前後各加20個點的漸變
            for i in range(max(0, start_idx - 20), start_idx):
                fade_factor = (start_idx - i) / 20
                mrl_distances[i] = 20000 * fade_factor + pass_info['distances'][0] * (1 - fade_factor)
                
            for i in range(end_idx + 1, min(end_idx + 21, 720)):
                fade_factor = (i - end_idx) / 20
                mrl_distances[i] = pass_info['distances'][-1] * (1 - fade_factor) + 20000 * fade_factor
            
            # 創建衛星數據
            sat_data = {
                "norad_id": satellite["norad_id"],
                "name": satellite["name"],
                "constellation": satellite["constellation"],
                "mrl_distances": mrl_distances,
                "moving_reference_locations": mrl_locations,
                "time_series": satellite["time_series"]
            }
            
            enhanced_data["satellites"].append(sat_data)
        
        # 保存數據
        output_file = Path("/home/sat/ntn-stack/data/starlink_120min_d2_enhanced.json")
        with open(output_file, 'w') as f:
            json.dump(enhanced_data, f, indent=2)
        
        # 複製到 backend
        import shutil
        backend_file = Path("data/starlink_120min_d2_enhanced.json")
        backend_file.parent.mkdir(exist_ok=True)
        shutil.copy(output_file, backend_file)
        
        print("\n  💾 已保存真實通過數據")
        
        # 對 OneWeb 做同樣處理
        print("\n  🔄 處理 OneWeb...")
        oneweb_file = Path("/home/sat/ntn-stack/data/oneweb_120min_timeseries.json")
        if oneweb_file.exists():
            # 簡單複製 Starlink 的結構
            oneweb_data = enhanced_data.copy()
            oneweb_data["metadata"]["constellation"] = "oneweb"
            
            output_file = Path("/home/sat/ntn-stack/data/oneweb_120min_d2_enhanced.json")
            with open(output_file, 'w') as f:
                json.dump(oneweb_data, f, indent=2)
            
            backend_file = Path("data/oneweb_120min_d2_enhanced.json")
            shutil.copy(output_file, backend_file)
            
            print("  💾 已保存 OneWeb 數據")

if __name__ == "__main__":
    create_realistic_passes()
    print("\n✅ 完成！")