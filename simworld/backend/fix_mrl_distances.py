#!/usr/bin/env python3
"""
修復 MRL 距離計算問題
使用真實的衛星位置數據重新計算 MRL 距離
"""

import json
import math
from pathlib import Path
from datetime import datetime

def calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon):
    """計算 UE 到衛星 MRL (nadir point) 的大圓距離"""
    # 轉換為弧度
    lat1_rad = math.radians(ue_lat)
    lat2_rad = math.radians(sat_lat)
    delta_lat = math.radians(sat_lat - ue_lat)
    delta_lon = math.radians(sat_lon - ue_lon)
    
    # Haversine 公式
    a = (math.sin(delta_lat / 2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2)**2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 地球平均半徑（km）
    earth_radius = 6371.0
    distance = earth_radius * c
    
    return distance

def fix_mrl_distances():
    """修復所有預處理數據的 MRL 距離"""
    
    print("🔧 修復 MRL 距離計算...")
    
    # 處理兩個星座
    for constellation in ["starlink", "oneweb"]:
        # 使用主數據目錄的文件
        input_file = Path(f"/home/sat/ntn-stack/data/{constellation}_120min_d2_enhanced.json")
        if not input_file.exists():
            print(f"  ⚠️  {input_file} 不存在，跳過")
            continue
            
        print(f"  📡 處理 {constellation}...")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # UE 位置
        ue_location = data["metadata"]["d2_enhancement"]["ue_location"]
        ue_lat = ue_location["lat"]
        ue_lon = ue_location["lon"]
        
        # 處理每顆衛星
        for sat_idx, satellite in enumerate(data["satellites"]):
            print(f"    衛星 {sat_idx + 1}/{len(data['satellites'])}: {satellite['name']}")
            
            # 重新計算 MRL 距離
            new_mrl_distances = []
            new_mrl_locations = []
            
            # 使用時間序列數據中的位置
            for ts_entry in satellite["time_series"]:
                # 衛星位置就是 MRL（nadir point）
                sat_lat = ts_entry["position"]["latitude"]
                sat_lon = ts_entry["position"]["longitude"]
                
                # 計算距離
                mrl_distance = calculate_mrl_distance(ue_lat, ue_lon, sat_lat, sat_lon)
                
                new_mrl_distances.append(mrl_distance)
                new_mrl_locations.append({
                    "lat": sat_lat,
                    "lon": sat_lon
                })
            
            # 更新數據
            satellite["mrl_distances"] = new_mrl_distances
            satellite["moving_reference_locations"] = new_mrl_locations
            
            # 顯示統計
            if new_mrl_distances:
                min_dist = min(new_mrl_distances)
                max_dist = max(new_mrl_distances)
                print(f"      MRL 距離範圍: {min_dist:.1f} - {max_dist:.1f} km")
        
        # 重新偵測 D2 事件
        print("    🔍 重新偵測 D2 事件...")
        d2_events = detect_d2_events(data)
        data["d2_events"] = d2_events
        print(f"    ✅ 偵測到 {len(d2_events)} 個 D2 事件")
        
        # 更新時間戳
        data["metadata"]["d2_enhancement"]["enhanced_at"] = datetime.utcnow().isoformat() + "Z"
        data["metadata"]["d2_enhancement"]["fix_applied"] = "real_mrl_distances"
        
        # 保存修復後的數據
        with open(input_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  💾 已保存到: {input_file}")
        
        # 複製到 backend 數據目錄
        import shutil
        backend_data_dir = Path("data")
        backend_data_dir.mkdir(exist_ok=True)
        shutil.copy(input_file, backend_data_dir / input_file.name)
        print(f"  📁 已更新 backend 數據目錄")

def detect_d2_events(data):
    """偵測 D2 事件"""
    d2_events = []
    
    # 獲取門檻值
    thresholds = data["metadata"]["d2_enhancement"]["thresholds"]
    thresh1 = thresholds["thresh1"]
    thresh2 = thresholds["thresh2"]
    hysteresis = thresholds["hysteresis"]
    
    # 獲取時間戳
    timestamps = []
    if "timestamps" in data:
        timestamps = data["timestamps"]
    else:
        # 從第一顆衛星的時間序列獲取
        if data["satellites"] and data["satellites"][0]["time_series"]:
            timestamps = [ts["timestamp"] for ts in data["satellites"][0]["time_series"]]
    
    # 檢查是否有足夠的衛星
    if len(data["satellites"]) < 2:
        return d2_events
    
    # 假設前兩顆衛星是服務衛星和目標衛星
    serving_sat = data["satellites"][0]
    target_sat = data["satellites"][1]
    
    # 檢查 D2 事件
    in_d2_event = False
    d2_start_idx = None
    
    for i in range(len(timestamps)):
        if i < len(serving_sat["mrl_distances"]) and i < len(target_sat["mrl_distances"]):
            ml1 = serving_sat["mrl_distances"][i]
            ml2 = target_sat["mrl_distances"][i]
            
            # D2 條件
            condition1 = ml1 > (thresh1 + hysteresis)
            condition2 = ml2 < (thresh2 - hysteresis)
            
            if condition1 and condition2 and not in_d2_event:
                # D2 事件開始
                in_d2_event = True
                d2_start_idx = i
            elif in_d2_event and (not condition1 or not condition2):
                # D2 事件結束
                in_d2_event = False
                if d2_start_idx is not None:
                    d2_event = {
                        "id": f"d2_event_{len(d2_events)+1}",
                        "timestamp_start": timestamps[d2_start_idx],
                        "timestamp_end": timestamps[i],
                        "serving_satellite": {
                            "name": serving_sat["name"],
                            "id": str(serving_sat["norad_id"])
                        },
                        "target_satellite": {
                            "name": target_sat["name"],
                            "id": str(target_sat["norad_id"])
                        },
                        "ml1_start": serving_sat["mrl_distances"][d2_start_idx],
                        "ml1_end": ml1,
                        "ml2_start": target_sat["mrl_distances"][d2_start_idx],
                        "ml2_end": ml2,
                        "duration_seconds": (i - d2_start_idx) * 10
                    }
                    d2_events.append(d2_event)
    
    return d2_events

if __name__ == "__main__":
    print("🛰️ 修復 MRL 距離計算")
    print("=" * 50)
    fix_mrl_distances()
    print("\n✅ 完成！")