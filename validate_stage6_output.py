#!/usr/bin/env python3
"""
直接驗證階段六產出數據的效果
模擬前端查詢邏輯，測試在不同時間點的可見衛星數量
"""

import json
import os
from datetime import datetime, timedelta, timezone

def load_stage6_data():
    """載入階段六數據"""
    possible_paths = [
        "/home/sat/ntn-stack/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json",
        "/home/sat/ntn-stack/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f), path
    
    return None, None

def simulate_frontend_query(satellites_data, min_elevation, count_limit, time_index):
    """
    模擬前端查詢邏輯
    返回在指定時間點可見的衛星（仿照 simple_satellite_router.py）
    """
    visible_satellites = []
    
    for sat_data in satellites_data:
        # 檢查時間索引範圍
        if time_index < len(sat_data.get("position_timeseries", [])):
            time_point = sat_data["position_timeseries"][time_index]
            
            # 檢查可見性和仰角門檻
            if (time_point.get("is_visible", False) and 
                time_point.get("elevation_deg", 0) >= min_elevation):
                
                # 提取 NORAD ID
                sat_id = sat_data.get("satellite_id", "")
                norad_id = sat_id.split("_")[-1] if "_" in sat_id else sat_id
                
                satellite_info = {
                    "name": sat_data["satellite_name"],
                    "norad_id": norad_id,
                    "constellation": sat_data["constellation"],
                    "satellite_id": sat_data["satellite_id"],
                    "elevation_deg": time_point["elevation_deg"],
                    "azimuth_deg": time_point["azimuth_deg"],
                    "distance_km": time_point.get("range_km", 0),
                    "signal_strength": -80.0 + (time_point["elevation_deg"] / 2),
                    "is_visible": True,
                    "exact_time": time_point["time"],
                    "time_index": time_index
                }
                
                visible_satellites.append(satellite_info)
    
    # 按仰角排序並限制數量（模擬前端邏輯）
    visible_satellites.sort(key=lambda x: x["elevation_deg"], reverse=True)
    return visible_satellites[:count_limit]

def test_complete_orbit_cycle(stage6_data):
    """測試完整軌道週期的可見衛星數量"""
    print("🛰️ 階段六數據完整週期驗證")
    print("="*70)
    
    satellites_data = stage6_data["dynamic_satellite_pool"]["selection_details"]
    
    # 按星座分組
    starlink_sats = [s for s in satellites_data if s["constellation"] == "starlink"]
    oneweb_sats = [s for s in satellites_data if s["constellation"] == "oneweb"]
    
    print(f"衛星池組成: {len(starlink_sats)} 顆 Starlink + {len(oneweb_sats)} 顆 OneWeb")
    
    # 獲取時間範圍
    if not starlink_sats:
        print("❌ 找不到 Starlink 衛星數據")
        return
        
    time_points = len(starlink_sats[0]["position_timeseries"])
    print(f"時間範圍: {time_points} 個時間點")
    
    # 測試不同的查詢參數組合（模擬前端行為）
    test_scenarios = [
        {
            "name": "前端預設參數",
            "starlink": {"count": 15, "min_elevation": 5},
            "oneweb": {"count": 6, "min_elevation": 10}
        },
        {
            "name": "較嚴格參數",
            "starlink": {"count": 20, "min_elevation": 10},
            "oneweb": {"count": 10, "min_elevation": 15}
        },
        {
            "name": "寬鬆參數",
            "starlink": {"count": 30, "min_elevation": 0},
            "oneweb": {"count": 15, "min_elevation": 5}
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*70}")
        print(f"📊 測試場景: {scenario['name']}")
        print(f"Starlink: 最多 {scenario['starlink']['count']} 顆, 仰角 ≥ {scenario['starlink']['min_elevation']}°")
        print(f"OneWeb: 最多 {scenario['oneweb']['count']} 顆, 仰角 ≥ {scenario['oneweb']['min_elevation']}°")
        print("="*70)
        
        starlink_counts = []
        oneweb_counts = []
        sample_results = []
        
        # 測試每個時間點
        for t in range(time_points):
            # 查詢 Starlink
            starlink_visible = simulate_frontend_query(
                starlink_sats, 
                scenario["starlink"]["min_elevation"], 
                scenario["starlink"]["count"], 
                t
            )
            
            # 查詢 OneWeb  
            oneweb_visible = simulate_frontend_query(
                oneweb_sats, 
                scenario["oneweb"]["min_elevation"], 
                scenario["oneweb"]["count"], 
                t
            )
            
            starlink_counts.append(len(starlink_visible))
            oneweb_counts.append(len(oneweb_visible))
            
            # 記錄樣本（每5個時間點或最後一個）
            if t % 5 == 0 or t == time_points - 1:
                sample_time = starlink_visible[0]["exact_time"][:19] if starlink_visible else "N/A"
                sample_results.append({
                    "time_index": t,
                    "time": sample_time,
                    "starlink_count": len(starlink_visible),
                    "oneweb_count": len(oneweb_visible),
                    "starlink_samples": [s["norad_id"] for s in starlink_visible[:3]],
                    "oneweb_samples": [s["norad_id"] for s in oneweb_visible[:3]]
                })
        
        # 顯示時間樣本
        print(f"{'時間點':<8} {'時間':<12} {'Starlink':<10} {'OneWeb':<8} {'樣本衛星ID'}")
        print("-" * 70)
        for sample in sample_results:
            samples_str = f"S:{','.join(sample['starlink_samples'][:2])} O:{','.join(sample['oneweb_samples'][:2])}"
            print(f"{sample['time_index']:<8} {sample['time'][11:] if len(sample['time']) > 11 else sample['time']:<12} "
                  f"{sample['starlink_count']:<10} {sample['oneweb_count']:<8} {samples_str}")
        
        # 統計結果
        if starlink_counts and oneweb_counts:
            print(f"\n📈 統計結果:")
            print(f"Starlink: 平均 {sum(starlink_counts)/len(starlink_counts):.1f} 顆 "
                  f"(範圍 {min(starlink_counts)}-{max(starlink_counts)} 顆)")
            print(f"OneWeb:   平均 {sum(oneweb_counts)/len(oneweb_counts):.1f} 顆 "
                  f"(範圍 {min(oneweb_counts)}-{max(oneweb_counts)} 顆)")
            
            # 分析是否符合 handover 研究需求
            starlink_target = (10, 15)
            oneweb_target = (3, 6)
            
            starlink_in_range = sum(1 for c in starlink_counts if starlink_target[0] <= c <= starlink_target[1])
            oneweb_in_range = sum(1 for c in oneweb_counts if oneweb_target[0] <= c <= oneweb_target[1])
            
            starlink_ratio = starlink_in_range / len(starlink_counts) * 100
            oneweb_ratio = oneweb_in_range / len(oneweb_counts) * 100
            
            print(f"\n🎯 Handover 研究適用性:")
            print(f"Starlink 目標範圍 (10-15 顆) 達成率: {starlink_ratio:.1f}% ({starlink_in_range}/{len(starlink_counts)} 時間點)")
            print(f"OneWeb 目標範圍 (3-6 顆) 達成率: {oneweb_ratio:.1f}% ({oneweb_in_range}/{len(oneweb_counts)} 時間點)")
            
            if starlink_ratio >= 80 and oneweb_ratio >= 80:
                print("✅ 適合 handover 研究")
            elif starlink_ratio >= 60 or oneweb_ratio >= 60:
                print("⚠️ 部分適合，建議調整參數")
            else:
                print("❌ 不適合，需要重新設計階段六")

def analyze_handover_scenarios(stage6_data):
    """分析 handover 場景品質"""
    print(f"\n{'='*70}")
    print("🔄 Handover 場景品質分析")
    print("="*70)
    
    satellites_data = stage6_data["dynamic_satellite_pool"]["selection_details"]
    starlink_sats = [s for s in satellites_data if s["constellation"] == "starlink"]
    
    if not starlink_sats:
        return
        
    time_points = len(starlink_sats[0]["position_timeseries"])
    
    # 使用前端預設參數
    handover_events = []
    prev_visible_ids = set()
    
    for t in range(time_points):
        # 模擬前端查詢
        visible_sats = simulate_frontend_query(starlink_sats, 5, 15, t)
        curr_visible_ids = {sat["satellite_id"] for sat in visible_sats}
        
        # 檢測進入/離開事件
        if t > 0:
            entering = curr_visible_ids - prev_visible_ids
            leaving = prev_visible_ids - curr_visible_ids
            
            if entering or leaving:
                handover_events.append({
                    "time_index": t,
                    "entering": len(entering),
                    "leaving": len(leaving),
                    "total_visible": len(visible_sats),
                    "entering_sats": list(entering)[:2],  # 前2個
                    "leaving_sats": list(leaving)[:2]
                })
        
        prev_visible_ids = curr_visible_ids
    
    print(f"檢測到 {len(handover_events)} 個 handover 事件")
    
    if handover_events:
        print(f"\n前 10 個 handover 事件:")
        print(f"{'時間點':<8} {'可見總數':<8} {'進入':<6} {'離開':<6} {'事件描述'}")
        print("-" * 60)
        
        for i, event in enumerate(handover_events[:10]):
            details = []
            if event['entering'] > 0:
                details.append(f"+{event['entering']}")
            if event['leaving'] > 0:
                details.append(f"-{event['leaving']}")
            detail_str = ','.join(details)
            
            print(f"{event['time_index']:<8} {event['total_visible']:<8} "
                  f"{event['entering']:<6} {event['leaving']:<6} {detail_str}")
        
        # 計算 handover 品質指標
        total_time_minutes = time_points * 0.5  # 假設30秒間隔
        handover_rate = len(handover_events) / total_time_minutes if total_time_minutes > 0 else 0
        
        avg_entering = sum(e['entering'] for e in handover_events) / len(handover_events)
        avg_leaving = sum(e['leaving'] for e in handover_events) / len(handover_events)
        
        print(f"\n📊 Handover 品質指標:")
        print(f"事件頻率: {handover_rate:.2f} 次/分鐘 (每 {60/handover_rate:.1f} 秒一次)")
        print(f"平均進入衛星數: {avg_entering:.1f} 顆")
        print(f"平均離開衛星數: {avg_leaving:.1f} 顆")
        
        # 評估適合度
        ideal_rate = 0.5  # 理想：每2分鐘1次 handover
        if 0.3 <= handover_rate <= 1.0:
            print("✅ Handover 頻率適中，適合研究")
        elif handover_rate < 0.3:
            print("⚠️ Handover 太少，衛星變化不夠動態")
        else:
            print("⚠️ Handover 太頻繁，可能造成系統不穩定")

def main():
    """主程序"""
    print("🔍 階段六產出數據驗證")
    print("="*70)
    
    # 載入階段六數據
    stage6_data, file_path = load_stage6_data()
    
    if not stage6_data:
        print("❌ 找不到階段六數據文件")
        return
        
    print(f"✅ 載入數據: {file_path}")
    
    # 測試完整軌道週期
    test_complete_orbit_cycle(stage6_data)
    
    # 分析 handover 場景
    analyze_handover_scenarios(stage6_data)
    
    print(f"\n{'='*70}")
    print("💡 驗證總結")
    print("="*70)
    print("1. 時間序列數據長度較短，可能影響完整週期分析")
    print("2. 建議使用「前端預設參數」進行實際測試")
    print("3. 如果達成率低於80%，需要調整階段六選擇邏輯")

if __name__ == "__main__":
    main()