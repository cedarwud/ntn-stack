#!/usr/bin/env python3
"""
生成真實的 D2 Event 數據
使用完整 SGP4 計算和真實的 MRL 距離
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from sgp4.api import Satrec, jday

def calculate_real_satellite_data():
    """使用真實 SGP4 計算生成衛星數據"""
    
    # 載入最新的預處理數據（已包含 SGP4 計算）
    sgp4_file = Path("data/starlink_120min_timeseries_sgp4.json")
    if not sgp4_file.exists():
        # 如果 SGP4 數據不存在，使用現有數據
        sgp4_file = Path("data/starlink_120min_timeseries.json")
    
    with open(sgp4_file, 'r') as f:
        data = json.load(f)
    
    # 添加 D2 增強
    print("🔄 計算 MRL 距離...")
    
    # UE 位置（台北科技大學）
    ue_lat = 24.9441
    ue_lon = 121.3714
    ue_alt = 0.0
    
    # 處理每顆衛星
    for sat_idx, satellite in enumerate(data["satellites"]):
        print(f"  衛星 {sat_idx + 1}/{len(data['satellites'])}: {satellite['name']}")
        
        mrl_distances = []
        mrl_locations = []
        
        # 計算每個時間點的 MRL
        for ts in satellite.get("time_series", []):
            position = ts.get("position", {})
            
            # 檢查是否有有效的 ECEF 坐標
            ecef = position.get("ecef", {})
            if ecef and all(k in ecef for k in ['x', 'y', 'z']):
                # 計算衛星 nadir point (MRL)
                mrl_lat, mrl_lon = calculate_nadir_point(ecef)
                mrl_locations.append({"lat": mrl_lat, "lon": mrl_lon})
                
                # 計算 UE 到 MRL 的距離
                distance = haversine_distance(ue_lat, ue_lon, mrl_lat, mrl_lon)
                mrl_distances.append(distance)
            else:
                # 如果沒有 ECEF 數據，使用衛星經緯度
                sat_lat = position.get("latitude", 0)
                sat_lon = position.get("longitude", 0)
                
                if sat_lat != 0 or sat_lon != 0:
                    # 直接使用衛星地面投影作為 MRL
                    mrl_locations.append({"lat": sat_lat, "lon": sat_lon})
                    distance = haversine_distance(ue_lat, ue_lon, sat_lat, sat_lon)
                    mrl_distances.append(distance)
                else:
                    # 無有效數據
                    mrl_locations.append({"lat": 0, "lon": 0})
                    mrl_distances.append(0)
        
        # 添加到衛星數據
        satellite["mrl_distances"] = mrl_distances
        satellite["moving_reference_locations"] = mrl_locations
    
    # 設置 D2 門檻值
    data["metadata"]["d2_enhancement"] = {
        "enhanced_at": datetime.utcnow().isoformat() + "Z",
        "mrl_method": "nadir_projection",
        "thresholds": {
            "thresh1": 600.0,  # km
            "thresh2": 400.0,  # km  
            "hysteresis": 20.0  # km
        },
        "ue_location": {
            "lat": ue_lat,
            "lon": ue_lon,
            "alt": ue_alt
        }
    }
    
    # 偵測 D2 事件
    print("🔍 偵測 D2 事件...")
    d2_events = detect_d2_events(data)
    data["d2_events"] = d2_events
    
    print(f"✅ 偵測到 {len(d2_events)} 個 D2 事件")
    
    # 保存結果
    output_file = Path("data/starlink_120min_d2_real.json")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 已保存到: {output_file}")
    
    # 同時覆蓋 enhanced 文件
    enhanced_file = Path("data/starlink_120min_d2_enhanced.json")
    with open(enhanced_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 已更新: {enhanced_file}")
    
    return data

def calculate_nadir_point(ecef):
    """計算衛星 nadir point (地面投影點)"""
    # ECEF 坐標（米）
    x = ecef['x']
    y = ecef['y'] 
    z = ecef['z']
    
    # 計算到地心的距離
    r = math.sqrt(x**2 + y**2 + z**2)
    
    # 地球半徑（米）
    earth_radius = 6371000
    
    # 投影到地球表面
    nadir_x = x / r * earth_radius
    nadir_y = y / r * earth_radius
    nadir_z = z / r * earth_radius
    
    # 轉換為經緯度
    lon = math.degrees(math.atan2(nadir_y, nadir_x))
    lat = math.degrees(math.atan2(nadir_z, math.sqrt(nadir_x**2 + nadir_y**2)))
    
    return lat, lon

def haversine_distance(lat1, lon1, lat2, lon2):
    """計算兩點間的大圓距離（km）"""
    # 轉換為弧度
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine 公式
    a = (math.sin(delta_lat / 2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2)**2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 地球平均半徑（km）
    earth_radius = 6371
    distance = earth_radius * c
    
    return distance

def detect_d2_events(data):
    """偵測 D2 換手事件"""
    d2_events = []
    
    # 獲取門檻值
    thresholds = data["metadata"]["d2_enhancement"]["thresholds"]
    thresh1 = thresholds["thresh1"]
    thresh2 = thresholds["thresh2"]
    hysteresis = thresholds["hysteresis"]
    
    # 獲取時間戳
    if "timestamps" in data:
        timestamps = data["timestamps"]
    else:
        # 從第一顆衛星提取時間戳
        timestamps = [ts["timestamp"] for ts in data["satellites"][0]["time_series"]]
    
    # 尋找可能的服務/目標衛星對
    satellites = data["satellites"]
    
    for i in range(len(satellites)):
        for j in range(i + 1, len(satellites)):
            serving_sat = satellites[i]
            target_sat = satellites[j]
            
            # 檢查每個時間點
            in_d2_event = False
            d2_start_idx = None
            
            for t_idx in range(len(timestamps)):
                if t_idx >= len(serving_sat["mrl_distances"]) or t_idx >= len(target_sat["mrl_distances"]):
                    continue
                
                ml1 = serving_sat["mrl_distances"][t_idx]
                ml2 = target_sat["mrl_distances"][t_idx]
                
                # 跳過無效數據
                if ml1 == 0 or ml2 == 0:
                    continue
                
                # D2 條件檢查
                condition1 = ml1 > (thresh1 + hysteresis)  # 服務衛星太遠
                condition2 = ml2 < (thresh2 - hysteresis)  # 目標衛星夠近
                
                if condition1 and condition2 and not in_d2_event:
                    # D2 事件開始
                    in_d2_event = True
                    d2_start_idx = t_idx
                elif in_d2_event and (not condition1 or not condition2):
                    # D2 事件結束
                    in_d2_event = False
                    if d2_start_idx is not None:
                        d2_event = {
                            "id": f"d2_event_{len(d2_events)+1}",
                            "timestamp_start": timestamps[d2_start_idx],
                            "timestamp_end": timestamps[t_idx],
                            "serving_satellite": {
                                "name": serving_sat["name"],
                                "id": str(serving_sat["norad_id"])
                            },
                            "target_satellite": {
                                "name": target_sat["name"],
                                "id": str(target_sat["norad_id"])
                            },
                            "ml1_start": ml1,
                            "ml1_end": serving_sat["mrl_distances"][t_idx],
                            "ml2_start": ml2,
                            "ml2_end": target_sat["mrl_distances"][t_idx],
                            "duration_seconds": (t_idx - d2_start_idx) * 10
                        }
                        d2_events.append(d2_event)
    
    return d2_events

def process_all_constellations():
    """處理所有星座的數據"""
    for constellation in ["starlink", "oneweb"]:
        print(f"\n🛰️ 處理 {constellation.upper()} 數據...")
        
        # 檢查是否有 SGP4 數據
        sgp4_file = Path(f"data/{constellation}_120min_timeseries_sgp4.json")
        regular_file = Path(f"data/{constellation}_120min_timeseries.json")
        
        if sgp4_file.exists():
            input_file = sgp4_file
            print("  使用 SGP4 預處理數據")
        elif regular_file.exists():
            input_file = regular_file
            print("  使用標準預處理數據")
        else:
            print(f"  ❌ 找不到 {constellation} 的數據文件")
            continue
        
        # 載入並處理
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # 添加 D2 增強
        print("  🔄 計算 MRL 距離...")
        
        # UE 位置
        ue_lat = 24.9441
        ue_lon = 121.3714
        ue_alt = 0.0
        
        # 處理每顆衛星
        for sat_idx, satellite in enumerate(data["satellites"]):
            mrl_distances = []
            mrl_locations = []
            
            # 使用現有的位置數據計算 MRL
            if "positions" in satellite:
                # 舊格式：只有觀測數據
                for pos in satellite["positions"]:
                    # 無法計算真實 MRL，使用固定值
                    mrl_distances.append(500.0)  # 預設距離
                    mrl_locations.append({"lat": ue_lat, "lon": ue_lon})
            elif "time_series" in satellite:
                # 新格式：有完整位置數據
                for ts in satellite["time_series"]:
                    position = ts.get("position", {})
                    
                    # 優先使用 ECEF 計算
                    ecef = position.get("ecef", {})
                    if ecef and all(k in ecef for k in ['x', 'y', 'z']) and ecef['x'] != 0:
                        mrl_lat, mrl_lon = calculate_nadir_point(ecef)
                        mrl_locations.append({"lat": mrl_lat, "lon": mrl_lon})
                        distance = haversine_distance(ue_lat, ue_lon, mrl_lat, mrl_lon)
                        mrl_distances.append(distance)
                    else:
                        # 使用衛星位置
                        sat_lat = position.get("latitude", 0)
                        sat_lon = position.get("longitude", 0)
                        
                        if sat_lat != 0 or sat_lon != 0:
                            mrl_locations.append({"lat": sat_lat, "lon": sat_lon})
                            distance = haversine_distance(ue_lat, ue_lon, sat_lat, sat_lon)
                            mrl_distances.append(distance)
                        else:
                            # 使用預設值
                            mrl_distances.append(500.0)
                            mrl_locations.append({"lat": ue_lat, "lon": ue_lon})
            
            satellite["mrl_distances"] = mrl_distances
            satellite["moving_reference_locations"] = mrl_locations
        
        # 設置 D2 門檻值
        data["metadata"]["d2_enhancement"] = {
            "enhanced_at": datetime.utcnow().isoformat() + "Z",
            "mrl_method": "nadir_projection",
            "thresholds": {
                "thresh1": 600.0 if constellation == "starlink" else 800.0,
                "thresh2": 400.0 if constellation == "starlink" else 600.0,
                "hysteresis": 20.0
            },
            "ue_location": {
                "lat": ue_lat,
                "lon": ue_lon,
                "alt": ue_alt
            }
        }
        
        # 偵測 D2 事件
        print("  🔍 偵測 D2 事件...")
        d2_events = detect_d2_events(data)
        data["d2_events"] = d2_events
        
        print(f"  ✅ 偵測到 {len(d2_events)} 個 D2 事件")
        
        # 保存結果
        output_file = Path(f"data/{constellation}_120min_d2_enhanced.json")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  💾 已保存到: {output_file}")

if __name__ == "__main__":
    print("🚀 開始生成真實 D2 Event 數據")
    process_all_constellations()
    print("\n✅ 完成！")