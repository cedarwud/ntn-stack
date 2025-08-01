#!/usr/bin/env python3
"""
生成平滑且真實的D2事件演示數據
符合LEO衛星物理運動特性，適合學術研究使用
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from scipy import interpolate

def generate_realistic_mrl_distances(time_points: int = 720, constellation: str = "starlink"):
    """
    生成真實的MRL距離數據，基於衛星軌道物理特性
    
    使用更真實的軌道模型，包含：
    - 連續平滑的軌道運動
    - 基於仰角的距離計算
    - 真實的可見性窗口
    """
    # 時間陣列（10秒間隔）
    t = np.linspace(0, 120 * 60, time_points)  # 120分鐘（秒）
    
    # 星座參數
    if constellation == "starlink":
        # Starlink LEO 參數
        orbit_altitude = 550  # km
        min_elevation = 10    # 度（最小仰角）
        earth_radius = 6371   # km
    else:
        # OneWeb 參數
        orbit_altitude = 1200  # km
        min_elevation = 10     # 度
        earth_radius = 6371    # km
    
    # 計算最大和最小距離
    # 最小距離：衛星在正上方（90度仰角）
    min_distance = orbit_altitude
    
    # 最大距離：衛星在最小仰角時
    # 使用球面三角學計算
    min_elev_rad = np.radians(min_elevation)
    # 地心角
    central_angle = np.pi/2 - min_elev_rad - np.arcsin((earth_radius/(earth_radius + orbit_altitude)) * np.cos(min_elev_rad))
    # 斜距
    max_distance = earth_radius * np.sin(central_angle) / np.sin(min_elev_rad)
    
    # 服務衛星（從可見到不可見的完整軌道弧）
    serving_distances = []
    serving_visible = []
    
    # 軌道週期（分鐘）
    orbital_period = 2 * np.pi * np.sqrt((earth_radius + orbit_altitude)**3 / 398600.4) / 60
    
    for i, time_sec in enumerate(t):
        # 計算衛星相對位置（使用簡化的過頂軌道模型）
        # 時間歸一化到可見窗口
        visible_window = 12 * 60  # 典型LEO衛星可見窗口約12分鐘
        
        # 服務衛星：開始時在頭頂附近，逐漸遠離
        if time_sec < visible_window:
            # 在可見窗口內
            # 使用餘弦函數模擬從頭頂到地平線的運動
            phase = (time_sec / visible_window) * np.pi
            elevation_rad = np.radians(90 - 80 * (time_sec / visible_window))
            
            # 基於仰角計算距離
            if elevation_rad > min_elev_rad:
                # 使用正弦定理計算斜距
                central_angle = np.pi/2 - elevation_rad - np.arcsin((earth_radius/(earth_radius + orbit_altitude)) * np.cos(elevation_rad))
                distance = earth_radius * np.sin(central_angle) / np.sin(elevation_rad)
                
                # 添加小幅度的大氣擾動
                distance += np.random.normal(0, 2)
                serving_distances.append(distance)
                serving_visible.append(True)
            else:
                # 低於最小仰角，不可見
                serving_distances.append(np.nan)
                serving_visible.append(False)
        else:
            # 超出可見窗口
            serving_distances.append(np.nan)
            serving_visible.append(False)
    
    # 目標衛星（從不可見到可見的軌道弧）
    target_distances = []
    target_visible = []
    
    # 目標衛星延遲出現（模擬不同軌道面）
    target_delay = 30 * 60  # 30分鐘延遲
    
    for i, time_sec in enumerate(t):
        if time_sec > target_delay and time_sec < target_delay + visible_window:
            # 在可見窗口內
            window_time = time_sec - target_delay
            # 從地平線到頭頂的運動
            elevation_rad = np.radians(10 + 80 * (window_time / visible_window))
            
            if elevation_rad > min_elev_rad:
                # 計算斜距
                central_angle = np.pi/2 - elevation_rad - np.arcsin((earth_radius/(earth_radius + orbit_altitude)) * np.cos(elevation_rad))
                distance = earth_radius * np.sin(central_angle) / np.sin(elevation_rad)
                
                # 添加小幅度的大氣擾動
                distance += np.random.normal(0, 2)
                target_distances.append(distance)
                target_visible.append(True)
            else:
                target_distances.append(np.nan)
                target_visible.append(False)
        else:
            target_distances.append(np.nan)
            target_visible.append(False)
    
    # 填補 NaN 值以便繪圖（使用線性插值）
    # 但保留可見性資訊
    serving_distances_filled = fill_nan_with_interpolation(serving_distances)
    target_distances_filled = fill_nan_with_interpolation(target_distances)
    
    return serving_distances_filled, target_distances_filled, serving_visible, target_visible

def fill_nan_with_interpolation(distances):
    """使用線性插值填補 NaN 值"""
    arr = np.array(distances)
    
    # 如果全是 NaN，返回一個常數陣列
    if np.all(np.isnan(arr)):
        return [1000.0] * len(arr)  # 返回一個大距離表示不可見
    
    # 找出非 NaN 的索引
    valid_indices = ~np.isnan(arr)
    if np.sum(valid_indices) < 2:
        # 資料點太少，無法插值
        return [1000.0] * len(arr)
    
    # 進行插值
    x = np.arange(len(arr))
    interp_func = interpolate.interp1d(
        x[valid_indices], 
        arr[valid_indices], 
        kind='linear',
        fill_value='extrapolate',
        bounds_error=False
    )
    
    # 填補 NaN 值
    filled = arr.copy()
    nan_indices = np.isnan(arr)
    if np.any(nan_indices):
        filled[nan_indices] = interp_func(x[nan_indices])
    
    # 確保所有值都是合理的
    filled = np.clip(filled, 180, 2000)
    
    return filled.tolist()

def main():
    """生成平滑的D2演示數據"""
    
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # 基準時間戳
    base_time = datetime.utcnow().replace(second=0, microsecond=0)
    
    for constellation in ["starlink", "oneweb"]:
        print(f"🛰️ 生成平滑的D2演示數據：{constellation}")
        
        # 生成真實的MRL距離
        serving_distances, target_distances, serving_vis, target_vis = generate_realistic_mrl_distances(
            constellation=constellation
        )
        
        # 載入現有數據結構作為模板
        existing_file = output_dir / f"{constellation}_120min_d2_enhanced.json"
        if existing_file.exists():
            with open(existing_file, 'r') as f:
                data = json.load(f)
        else:
            # 創建最小結構
            data = {
                "metadata": {
                    "constellation": constellation,
                    "time_span_minutes": 120,
                    "d2_enhancement": {
                        "thresholds": {
                            "thresh1": 600.0 if constellation == "starlink" else 800.0,
                            "thresh2": 400.0 if constellation == "starlink" else 600.0,
                            "hysteresis": 20.0
                        },
                        "description": "基於真實軌道物理的平滑數據"
                    }
                },
                "satellites": [],
                "timestamps": [],
                "d2_events": []
            }
        
        # 更新衛星MRL距離
        if len(data["satellites"]) >= 2:
            # 更新前兩顆衛星作為服務/目標
            data["satellites"][0]["mrl_distances"] = serving_distances
            data["satellites"][0]["name"] = f"{constellation.upper()}-SERVING"
            data["satellites"][0]["visibility"] = serving_vis
            
            data["satellites"][1]["mrl_distances"] = target_distances  
            data["satellites"][1]["name"] = f"{constellation.upper()}-TARGET"
            data["satellites"][1]["visibility"] = target_vis
            
            # 確保 time_series 存在並有正確的時間戳
            for sat_idx in range(2):
                if "time_series" not in data["satellites"][sat_idx]:
                    data["satellites"][sat_idx]["time_series"] = []
                
                # 更新或創建時間序列條目
                time_series = []
                for i in range(720):
                    timestamp = base_time + timedelta(seconds=i*10)
                    entry = {
                        "timestamp": timestamp.isoformat() + "Z",
                        "time_offset_seconds": i * 10,
                        "position": {"ecef": {"x": 0, "y": 0, "z": 0}},
                        "observation": {},
                        "handover_metrics": {},
                        "measurement_events": {}
                    }
                    time_series.append(entry)
                
                data["satellites"][sat_idx]["time_series"] = time_series
        
        # 偵測D2事件（基於平滑數據）
        thresh1 = data["metadata"]["d2_enhancement"]["thresholds"]["thresh1"]
        thresh2 = data["metadata"]["d2_enhancement"]["thresholds"]["thresh2"]
        hysteresis = data["metadata"]["d2_enhancement"]["thresholds"]["hysteresis"]
        
        d2_events = []
        in_d2_event = False
        d2_start_idx = None
        
        for i in range(len(serving_distances)):
            # 只在兩顆衛星都可見時檢查D2條件
            if i < len(serving_vis) and i < len(target_vis):
                if serving_vis[i] and target_vis[i]:
                    ml1 = serving_distances[i]
                    ml2 = target_distances[i]
                    
                    # 檢查D2條件
                    condition1 = ml1 > (thresh1 + hysteresis)  # 服務衛星太遠
                    condition2 = ml2 < (thresh2 - hysteresis)  # 目標衛星夠近
                    
                    if condition1 and condition2 and not in_d2_event:
                        # D2事件開始
                        in_d2_event = True
                        d2_start_idx = i
                    elif in_d2_event and (not condition1 or not condition2 or not serving_vis[i] or not target_vis[i]):
                        # D2事件結束
                        in_d2_event = False
                        if d2_start_idx is not None:
                            timestamp_start = base_time + timedelta(seconds=d2_start_idx*10)
                            timestamp_end = base_time + timedelta(seconds=i*10)
                            
                            d2_event = {
                                "id": f"d2_event_{len(d2_events)+1}",
                                "timestamp_start": timestamp_start.isoformat() + "Z",
                                "timestamp_end": timestamp_end.isoformat() + "Z",
                                "serving_satellite": {
                                    "name": f"{constellation.upper()}-SERVING",
                                    "id": "serving"
                                },
                                "target_satellite": {
                                    "name": f"{constellation.upper()}-TARGET",
                                    "id": "target"
                                },
                                "ml1_start": serving_distances[d2_start_idx],
                                "ml1_end": ml1,
                                "ml2_start": target_distances[d2_start_idx],
                                "ml2_end": ml2,
                                "duration_seconds": (i - d2_start_idx) * 10,
                                "handover_type": "smooth_transition"
                            }
                            d2_events.append(d2_event)
        
        data["d2_events"] = d2_events
        
        # 保存平滑數據
        smooth_file = output_dir / f"{constellation}_120min_d2_smooth.json"
        with open(smooth_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ 生成平滑數據，包含 {len(d2_events)} 個D2事件：{smooth_file}")
        
        # 同時更新 enhanced 檔案
        enhanced_file = output_dir / f"{constellation}_120min_d2_enhanced.json"
        with open(enhanced_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ 更新增強檔案：{enhanced_file}")
        
        # 輸出統計資訊
        print(f"📊 統計資訊：")
        print(f"   - 服務衛星可見時間：{sum(serving_vis)} 個時間點（{sum(serving_vis)*10/60:.1f} 分鐘）")
        print(f"   - 目標衛星可見時間：{sum(target_vis)} 個時間點（{sum(target_vis)*10/60:.1f} 分鐘）")
        print(f"   - 同時可見時間：{sum([s and t for s, t in zip(serving_vis, target_vis)])} 個時間點")
        print()

if __name__ == "__main__":
    main()