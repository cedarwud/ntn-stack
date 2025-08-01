#!/usr/bin/env python3
"""
生成真實合理的 D2 演示數據
模擬兩顆 LEO 衛星連續覆蓋台灣地區的場景
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from pathlib import Path

def generate_realistic_d2_demo():
    """生成真實的 D2 演示數據"""
    
    print("🚀 生成真實 D2 演示數據...")
    
    # 載入模板
    template_file = Path("data/starlink_120min_timeseries.json")
    with open(template_file, 'r') as f:
        data = json.load(f)
    
    # 基準時間
    base_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    
    # 生成 720 個時間點（120分鐘，每10秒）
    timestamps = []
    for i in range(720):
        timestamp = base_time + timedelta(seconds=i*10)
        timestamps.append(timestamp.isoformat())
    
    # UE 位置（台北）
    ue_lat = 24.9441
    ue_lon = 121.3714
    
    # 創建兩顆衛星的真實軌道數據
    print("  📡 生成衛星軌道...")
    
    # 衛星 1: 服務衛星，開始時在頭頂，逐漸遠離
    sat1 = {
        "norad_id": 90001,
        "name": "LEO-SERVING-01",
        "constellation": "starlink",
        "mrl_distances": [],
        "moving_reference_locations": [],
        "time_series": [],
        "positions": []
    }
    
    # 衛星 2: 目標衛星，開始時較遠，逐漸接近
    sat2 = {
        "norad_id": 90002,
        "name": "LEO-TARGET-02",
        "constellation": "starlink",
        "mrl_distances": [],
        "moving_reference_locations": [],
        "time_series": [],
        "positions": []
    }
    
    # 生成軌道數據
    for i in range(720):
        time_minutes = i * 10 / 60  # 轉換為分鐘
        
        # 衛星 1 軌道（從近到遠）
        # 使用餘弦函數模擬衛星通過
        # 前 15 分鐘可見，然後遠離
        if time_minutes < 15:
            # 可見期間
            phase = time_minutes / 15 * np.pi  # 0 到 π
            # MRL 距離從 100km 增加到 800km
            mrl_dist1 = 100 + 700 * (1 - np.cos(phase)) / 2
            
            # 計算 MRL 位置（沿著軌道移動）
            # 從南向北通過台灣
            progress = time_minutes / 15
            mrl_lat1 = 22 + 6 * progress  # 22°N 到 28°N
            mrl_lon1 = 121.5 + 0.5 * np.sin(phase)  # 輕微東西擺動
            
            # 計算仰角（基於 MRL 距離）
            if mrl_dist1 < 200:
                elevation1 = 80 - mrl_dist1 * 0.2
            elif mrl_dist1 < 500:
                elevation1 = 40 - (mrl_dist1 - 200) * 0.05
            else:
                elevation1 = 25 - (mrl_dist1 - 500) * 0.05
            elevation1 = max(5, elevation1)  # 最小 5 度
            
            is_visible1 = True
        else:
            # 不可見期間
            mrl_dist1 = 800 + (time_minutes - 15) * 50  # 持續遠離
            mrl_lat1 = 28 + (time_minutes - 15) * 0.5
            mrl_lon1 = 121.5
            elevation1 = 0
            is_visible1 = False
        
        # 衛星 2 軌道（從遠到近）
        # 延遲 25 分鐘後開始接近
        if time_minutes < 25:
            # 還未接近
            mrl_dist2 = 1500 - time_minutes * 20  # 逐漸接近但還很遠
            mrl_lat2 = 15 + time_minutes * 0.3
            mrl_lon2 = 122
            elevation2 = 0
            is_visible2 = False
        elif time_minutes < 40:
            # 可見期間
            phase = (time_minutes - 25) / 15 * np.pi
            # MRL 距離從 800km 減少到 100km
            mrl_dist2 = 800 - 700 * (1 - np.cos(phase)) / 2
            
            # 從南向北通過
            progress = (time_minutes - 25) / 15
            mrl_lat2 = 20 + 8 * progress
            mrl_lon2 = 121.8 - 0.3 * np.sin(phase)
            
            # 計算仰角
            if mrl_dist2 < 200:
                elevation2 = 80 - mrl_dist2 * 0.2
            elif mrl_dist2 < 500:
                elevation2 = 40 - (mrl_dist2 - 200) * 0.05
            else:
                elevation2 = 25 - (mrl_dist2 - 500) * 0.05
            elevation2 = max(5, elevation2)
            
            is_visible2 = True
        else:
            # 通過後遠離
            mrl_dist2 = 100 + (time_minutes - 40) * 60
            mrl_lat2 = 28 + (time_minutes - 40) * 0.5
            mrl_lon2 = 121.8
            elevation2 = 0
            is_visible2 = False
        
        # 計算斜距（使用簡化的幾何關係）
        if elevation1 > 0:
            slant_range1 = mrl_dist1 / np.cos(np.radians(90 - elevation1))
        else:
            slant_range1 = 0
            
        if elevation2 > 0:
            slant_range2 = mrl_dist2 / np.cos(np.radians(90 - elevation2))
        else:
            slant_range2 = 0
        
        # 添加數據
        sat1["mrl_distances"].append(mrl_dist1)
        sat1["moving_reference_locations"].append({
            "lat": mrl_lat1,
            "lon": mrl_lon1
        })
        
        sat2["mrl_distances"].append(mrl_dist2)
        sat2["moving_reference_locations"].append({
            "lat": mrl_lat2,
            "lon": mrl_lon2
        })
        
        # 時間序列數據
        for sat, mrl_lat, mrl_lon, elevation, slant_range, is_visible in [
            (sat1, mrl_lat1, mrl_lon1, elevation1, slant_range1, is_visible1),
            (sat2, mrl_lat2, mrl_lon2, elevation2, slant_range2, is_visible2)
        ]:
            time_series_entry = {
                "timestamp": timestamps[i],
                "time_offset_seconds": i * 10,
                "position": {
                    "latitude": mrl_lat,
                    "longitude": mrl_lon,
                    "altitude": 550000,  # 550 km
                    "ecef": {"x": 0, "y": 0, "z": 0}
                },
                "observation": {
                    "elevation_deg": elevation,
                    "azimuth_deg": 0,
                    "range_km": slant_range,
                    "is_visible": is_visible,
                    "doppler_shift": 0
                },
                "handover_metrics": {
                    "signal_strength_dbm": -80 if is_visible else -150,
                    "latency_ms": 10 if is_visible else 999,
                    "data_rate_mbps": 50 if is_visible else 0
                },
                "measurement_events": {
                    "a3_condition": False,
                    "a4_condition": elevation > 15,
                    "d1_condition": False,
                    "d2_condition": False
                }
            }
            sat["time_series"].append(time_series_entry)
            
            # 位置數據（兼容舊格式）
            position_entry = {
                "elevation_deg": elevation,
                "azimuth_deg": 0,
                "range_km": slant_range,
                "is_visible": is_visible,
                "timestamp": timestamps[i]
            }
            sat["positions"].append(position_entry)
    
    # 更新數據結構
    data["satellites"] = [sat1, sat2]
    data["timestamps"] = timestamps
    
    # 設置 D2 參數
    data["metadata"]["d2_enhancement"] = {
        "enhanced_at": datetime.now(timezone.utc).isoformat(),
        "mrl_method": "nadir_projection",
        "thresholds": {
            "thresh1": 600.0,  # 服務衛星 MRL 距離門檻
            "thresh2": 400.0,  # 目標衛星 MRL 距離門檻
            "hysteresis": 20.0
        },
        "ue_location": {
            "lat": ue_lat,
            "lon": ue_lon,
            "alt": 0.0
        },
        "description": "真實 LEO 衛星換手演示"
    }
    
    # 偵測 D2 事件
    print("  🔍 偵測 D2 事件...")
    d2_events = []
    
    thresh1 = 600
    thresh2 = 400
    hysteresis = 20
    
    in_d2_event = False
    d2_start_idx = None
    
    for i in range(len(timestamps)):
        ml1 = sat1["mrl_distances"][i]
        ml2 = sat2["mrl_distances"][i]
        
        # D2 條件：服務衛星遠離且目標衛星接近
        condition1 = ml1 > (thresh1 + hysteresis)
        condition2 = ml2 < (thresh2 - hysteresis)
        
        if condition1 and condition2 and not in_d2_event:
            # D2 事件開始
            in_d2_event = True
            d2_start_idx = i
            print(f"    D2 事件開始於 {i*10/60:.1f} 分鐘")
        elif in_d2_event and (not condition1 or not condition2):
            # D2 事件結束
            in_d2_event = False
            if d2_start_idx is not None:
                d2_event = {
                    "id": f"d2_event_{len(d2_events)+1}",
                    "timestamp_start": timestamps[d2_start_idx],
                    "timestamp_end": timestamps[i],
                    "serving_satellite": {
                        "name": sat1["name"],
                        "id": str(sat1["norad_id"])
                    },
                    "target_satellite": {
                        "name": sat2["name"], 
                        "id": str(sat2["norad_id"])
                    },
                    "ml1_start": sat1["mrl_distances"][d2_start_idx],
                    "ml1_end": ml1,
                    "ml2_start": sat2["mrl_distances"][d2_start_idx],
                    "ml2_end": ml2,
                    "duration_seconds": (i - d2_start_idx) * 10,
                    "handover_reason": "serving_satellite_leaving_coverage"
                }
                d2_events.append(d2_event)
                print(f"    D2 事件結束於 {i*10/60:.1f} 分鐘，持續 {d2_event['duration_seconds']/60:.1f} 分鐘")
    
    data["d2_events"] = d2_events
    
    print(f"  ✅ 偵測到 {len(d2_events)} 個 D2 事件")
    
    # 保存檔案
    output_file = Path("data/starlink_120min_d2_enhanced.json")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  💾 已保存到: {output_file}")
    
    # 複製到主數據目錄
    import shutil
    main_data_dir = Path("/home/sat/ntn-stack/data")
    shutil.copy(output_file, main_data_dir / "starlink_120min_d2_enhanced.json")
    print(f"  📁 已複製到主數據目錄")
    
    # 同時生成 OneWeb 數據（簡化版）
    generate_oneweb_demo()

def generate_oneweb_demo():
    """生成 OneWeb 演示數據"""
    template_file = Path("data/oneweb_120min_timeseries.json")
    if template_file.exists():
        with open(template_file, 'r') as f:
            data = json.load(f)
        
        # 設置為較遠的固定距離
        for sat in data["satellites"]:
            sat["mrl_distances"] = [8000] * 720
            sat["moving_reference_locations"] = [{"lat": 0, "lon": 0}] * 720
        
        data["d2_events"] = []
        data["metadata"]["d2_enhancement"] = {
            "enhanced_at": datetime.now(timezone.utc).isoformat(),
            "thresholds": {
                "thresh1": 800.0,
                "thresh2": 600.0,
                "hysteresis": 20.0
            }
        }
        
        output_file = Path("data/oneweb_120min_d2_enhanced.json")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # 複製到主目錄
        import shutil
        main_data_dir = Path("/home/sat/ntn-stack/data")
        shutil.copy(output_file, main_data_dir / "oneweb_120min_d2_enhanced.json")

if __name__ == "__main__":
    print("🛰️ LEO 衛星 D2 換手演示數據生成器")
    print("=" * 50)
    generate_realistic_d2_demo()
    print("\n✅ 完成！")