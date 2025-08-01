#!/usr/bin/env python3
"""
生成台灣地區的 D2 Event 演示數據
選擇會經過台灣上空的衛星，產生合理的 MRL 距離
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def generate_taiwan_satellite_data():
    """生成適合台灣地區的衛星數據"""
    
    # 載入現有數據作為模板
    template_file = Path("data/starlink_120min_timeseries.json")
    with open(template_file, 'r') as f:
        data = json.load(f)
    
    # UE 位置（台北科技大學）
    ue_lat = 24.9441
    ue_lon = 121.3714
    
    print("🛰️ 生成台灣地區衛星數據...")
    
    # 基準時間
    base_time = datetime.utcnow().replace(second=0, microsecond=0)
    
    # 生成時間戳
    timestamps = []
    for i in range(720):  # 120分鐘，每10秒一個點
        timestamp = base_time + timedelta(seconds=i*10)
        timestamps.append(timestamp.isoformat() + "Z")
    
    data["timestamps"] = timestamps
    
    # 創建兩顆示範衛星
    # 衛星 1: 從南向北經過台灣的 LEO 衛星
    sat1_data = create_passing_satellite(
        name="DEMO-SAT-1",
        norad_id=99001,
        start_lat=10.0,  # 從南方開始
        end_lat=40.0,    # 向北移動
        center_lon=121.5, # 經過台灣
        altitude=550,     # km
        pass_time_minutes=12,  # 可見窗口
        timestamps=timestamps,
        ue_lat=ue_lat,
        ue_lon=ue_lon
    )
    
    # 衛星 2: 稍後從另一個軌道經過
    sat2_data = create_passing_satellite(
        name="DEMO-SAT-2", 
        norad_id=99002,
        start_lat=35.0,   # 從北方開始
        end_lat=5.0,      # 向南移動
        center_lon=122.0, # 稍偏東
        altitude=550,     # km
        pass_time_minutes=12,
        timestamps=timestamps,
        ue_lat=ue_lat,
        ue_lon=ue_lon,
        delay_minutes=30  # 延遲30分鐘出現
    )
    
    # 更新數據
    data["satellites"] = [sat1_data, sat2_data]
    
    # 添加其他衛星（不可見）
    for i in range(2, min(10, len(data["satellites"]))):
        if i < len(data["satellites"]):
            sat = data["satellites"][i]
            # 設置為遠處的衛星
            sat["mrl_distances"] = [8000 + i * 1000] * 720  # 固定在遠處
            sat["moving_reference_locations"] = [{"lat": 0, "lon": 180}] * 720
    
    # 設置 D2 門檻值
    data["metadata"]["d2_enhancement"] = {
        "enhanced_at": datetime.utcnow().isoformat() + "Z",
        "mrl_method": "nadir_projection",
        "thresholds": {
            "thresh1": 600.0,  # km - 服務衛星離開門檻
            "thresh2": 400.0,  # km - 目標衛星進入門檻
            "hysteresis": 20.0 # km
        },
        "ue_location": {
            "lat": ue_lat,
            "lon": ue_lon,
            "alt": 0.0
        },
        "note": "台灣地區示範數據"
    }
    
    # 偵測 D2 事件
    print("🔍 偵測 D2 事件...")
    d2_events = []
    
    # 手動創建一個 D2 事件（當衛星1離開，衛星2接近時）
    # 尋找交叉點
    for i in range(100, len(timestamps)-100):  # 避免邊界
        ml1 = sat1_data["mrl_distances"][i]
        ml2 = sat2_data["mrl_distances"][i]
        
        # 檢查 D2 條件
        if ml1 > 500 and ml2 < 300 and len(d2_events) == 0:
            # 創建 D2 事件
            d2_event = {
                "id": "d2_event_1",
                "timestamp_start": timestamps[i],
                "timestamp_end": timestamps[min(i+30, len(timestamps)-1)],  # 持續5分鐘
                "serving_satellite": {
                    "name": "DEMO-SAT-1",
                    "id": "99001"
                },
                "target_satellite": {
                    "name": "DEMO-SAT-2",
                    "id": "99002"
                },
                "ml1_start": ml1,
                "ml1_end": sat1_data["mrl_distances"][min(i+30, len(timestamps)-1)],
                "ml2_start": ml2,
                "ml2_end": sat2_data["mrl_distances"][min(i+30, len(timestamps)-1)],
                "duration_seconds": 300,
                "type": "planned_handover"
            }
            d2_events.append(d2_event)
            break
    
    data["d2_events"] = d2_events
    
    print(f"✅ 生成 {len(d2_events)} 個 D2 事件")
    
    # 保存數據
    output_file = Path("data/starlink_120min_d2_enhanced.json")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 已保存到: {output_file}")
    
    # 同時生成 OneWeb 數據
    generate_oneweb_data()

def create_passing_satellite(name, norad_id, start_lat, end_lat, center_lon, 
                           altitude, pass_time_minutes, timestamps, 
                           ue_lat, ue_lon, delay_minutes=0):
    """創建一顆經過指定區域的衛星"""
    
    satellite_data = {
        "norad_id": norad_id,
        "name": name,
        "constellation": "demo",
        "time_series": [],
        "positions": [],
        "mrl_distances": [],
        "moving_reference_locations": []
    }
    
    total_points = len(timestamps)
    pass_points = int(pass_time_minutes * 6)  # 每10秒一個點
    delay_points = int(delay_minutes * 6)
    
    for i in range(total_points):
        # 計算衛星位置
        if i < delay_points:
            # 延遲期間，衛星在遠處
            sat_lat = start_lat - 20
            sat_lon = center_lon + 50
            is_visible = False
        elif i < delay_points + pass_points:
            # 可見窗口內
            progress = (i - delay_points) / pass_points
            sat_lat = start_lat + (end_lat - start_lat) * progress
            
            # 添加一些橫向運動（模擬軌道傾角）
            lon_offset = 5 * math.sin(progress * math.pi)
            sat_lon = center_lon + lon_offset
            is_visible = True
        else:
            # 通過後，衛星遠離
            sat_lat = end_lat + 20
            sat_lon = center_lon - 50
            is_visible = False
        
        # 計算 MRL（衛星 nadir point）到 UE 的距離
        mrl_distance = haversine_distance(ue_lat, ue_lon, sat_lat, sat_lon)
        
        # 添加數據點
        timestamp = timestamps[i]
        
        # 計算仰角（簡化）
        if is_visible:
            # 基於距離估算仰角
            if mrl_distance < 100:
                elevation = 90 - mrl_distance * 0.3
            elif mrl_distance < 500:
                elevation = 60 - (mrl_distance - 100) * 0.1
            else:
                elevation = 20 - (mrl_distance - 500) * 0.02
            elevation = max(0, min(90, elevation))
        else:
            elevation = 0
        
        # 計算斜距
        if elevation > 0:
            # 使用簡化的幾何關係
            earth_radius = 6371  # km
            sat_height = altitude
            
            # 地心角
            central_angle = math.radians(mrl_distance / earth_radius * 180 / math.pi)
            
            # 餘弦定理計算斜距
            slant_range = math.sqrt(
                earth_radius**2 + (earth_radius + sat_height)**2 - 
                2 * earth_radius * (earth_radius + sat_height) * math.cos(central_angle)
            )
        else:
            slant_range = 0
        
        # 時間序列數據
        time_series_entry = {
            "timestamp": timestamp,
            "time_offset_seconds": i * 10,
            "position": {
                "latitude": sat_lat,
                "longitude": sat_lon,
                "altitude": altitude * 1000,  # 轉換為米
                "ecef": {
                    "x": 0,  # 簡化
                    "y": 0,
                    "z": 0
                }
            },
            "observation": {
                "elevation_deg": elevation,
                "azimuth_deg": 0,  # 簡化
                "range_km": slant_range,
                "is_visible": is_visible
            },
            "handover_metrics": {},
            "measurement_events": {}
        }
        
        satellite_data["time_series"].append(time_series_entry)
        
        # 位置數據（舊格式兼容）
        position_entry = {
            "elevation_deg": elevation,
            "azimuth_deg": 0,
            "range_km": slant_range,
            "is_visible": is_visible,
            "timestamp": timestamp
        }
        satellite_data["positions"].append(position_entry)
        
        # MRL 數據
        satellite_data["mrl_distances"].append(mrl_distance)
        satellite_data["moving_reference_locations"].append({
            "lat": sat_lat,
            "lon": sat_lon
        })
    
    return satellite_data

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

def generate_oneweb_data():
    """生成 OneWeb 演示數據"""
    # 類似的邏輯，但使用不同的軌道參數
    template_file = Path("data/oneweb_120min_timeseries.json")
    if template_file.exists():
        with open(template_file, 'r') as f:
            data = json.load(f)
        
        # 簡單處理：設置所有衛星為遠距離
        for sat in data["satellites"]:
            sat["mrl_distances"] = [8000] * 720
            sat["moving_reference_locations"] = [{"lat": 0, "lon": 0}] * 720
        
        data["d2_events"] = []
        
        output_file = Path("data/oneweb_120min_d2_enhanced.json")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 已保存 OneWeb 數據")

if __name__ == "__main__":
    print("🚀 生成台灣地區 D2 演示數據")
    generate_taiwan_satellite_data()
    print("\n✅ 完成！")