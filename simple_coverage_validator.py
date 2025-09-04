#!/usr/bin/env python3
"""
簡化覆蓋率驗證器 - 直接使用現有數據驗證時空錯置理論
"""

import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def load_processed_data():
    """載入階段三處理的數據"""
    
    file_path = "/tmp/satellite_data/stage3_signal_event_analysis_output.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    satellites = []
    for constellation_data in data['constellations'].values():
        if 'satellites' in constellation_data:
            satellites.extend(constellation_data['satellites'])
    
    print(f"載入 {len(satellites)} 顆衛星")
    
    # 檢查有位置數據的衛星
    satellites_with_positions = []
    for sat in satellites:
        if 'positions' in sat and sat['positions']:
            satellites_with_positions.append(sat)
    
    print(f"具有位置數據的衛星: {len(satellites_with_positions)} 顆")
    return satellites_with_positions

def analyze_visibility_at_time(satellites, target_time_str="2025-01-01T12:00:00Z"):
    """分析特定時間的可見性"""
    
    target_time = datetime.fromisoformat(target_time_str.replace('Z', '+00:00'))
    
    starlink_visible = 0
    oneweb_visible = 0
    
    for sat in satellites:
        constellation = sat.get('constellation', 'unknown')
        positions = sat.get('positions', [])
        
        if not positions:
            continue
            
        # 找到最接近目標時間的位置
        closest_pos = None
        min_time_diff = float('inf')
        
        for pos in positions:
            pos_time = datetime.fromisoformat(pos['time'].replace('Z', '+00:00'))
            time_diff = abs((pos_time - target_time).total_seconds())
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_pos = pos
        
        if closest_pos and min_time_diff <= 1800:  # 30分鐘內的數據有效
            elevation = closest_pos.get('elevation_deg', 0)
            if elevation >= 10:  # 10度仰角門檻
                if constellation == 'starlink':
                    starlink_visible += 1
                elif constellation == 'oneweb':
                    oneweb_visible += 1
    
    return starlink_visible, oneweb_visible

def test_different_subset_sizes():
    """測試不同規模的子集"""
    
    print("🚀 開始時空錯置理論驗證")
    
    satellites = load_processed_data()
    
    # 按星座分組
    starlink_sats = [s for s in satellites if s.get('constellation') == 'starlink']
    oneweb_sats = [s for s in satellites if s.get('constellation') == 'oneweb']
    
    print(f"Starlink 衛星: {len(starlink_sats)} 顆")
    print(f"OneWeb 衛星: {len(oneweb_sats)} 顆")
    
    # 測試不同規模子集在多個時間點的表現
    test_sizes = [
        (20, 10),
        (50, 20), 
        (100, 30),
        (200, 50),
        (len(starlink_sats), len(oneweb_sats))  # 全部
    ]
    
    test_times = [
        "2025-01-01T00:00:00Z",
        "2025-01-01T06:00:00Z", 
        "2025-01-01T12:00:00Z",
        "2025-01-01T18:00:00Z"
    ]
    
    results = []
    
    for starlink_size, oneweb_size in test_sizes:
        subset_starlink = starlink_sats[:starlink_size]
        subset_oneweb = oneweb_sats[:oneweb_size]
        subset_all = subset_starlink + subset_oneweb
        
        time_results = []
        
        print(f"\n📊 測試子集規模: Starlink {starlink_size}, OneWeb {oneweb_size}")
        
        for time_str in test_times:
            starlink_vis, oneweb_vis = analyze_visibility_at_time(subset_all, time_str)
            time_results.append((starlink_vis, oneweb_vis))
            
            time_hour = time_str[11:16]
            status_s = "✅" if 10 <= starlink_vis <= 15 else "❌"
            status_o = "✅" if 3 <= oneweb_vis <= 6 else "❌"
            
            print(f"  {time_hour}: Starlink {starlink_vis} {status_s}, OneWeb {oneweb_vis} {status_o}")
        
        # 統計結果
        starlink_values = [r[0] for r in time_results]
        oneweb_values = [r[1] for r in time_results]
        
        starlink_in_range = sum(1 for v in starlink_values if 10 <= v <= 15)
        oneweb_in_range = sum(1 for v in oneweb_values if 3 <= v <= 6)
        
        success_rate = (starlink_in_range + oneweb_in_range) / (len(test_times) * 2)
        
        print(f"  成功率: {success_rate*100:.1f}% (目標: ≥95%)")
        print(f"  Starlink 範圍內: {starlink_in_range}/{len(test_times)} 次")
        print(f"  OneWeb 範圍內: {oneweb_in_range}/{len(test_times)} 次")
        
        # 如果這個規模已經滿足要求，就找到最小需求了
        if success_rate >= 0.75:  # 75%作為可接受的門檻
            print(f"🎯 找到可行的子集規模!")
            results.append({
                'size': (starlink_size, oneweb_size),
                'success_rate': success_rate,
                'starlink_range': (min(starlink_values), max(starlink_values)),
                'oneweb_range': (min(oneweb_values), max(oneweb_values))
            })
            if success_rate >= 0.95:
                break
    
    return results

if __name__ == "__main__":
    results = test_different_subset_sizes()
    
    print("\n🏆 驗證結果總結:")
    
    if results:
        for i, result in enumerate(results):
            size = result['size']
            rate = result['success_rate'] * 100
            s_range = result['starlink_range']
            o_range = result['oneweb_range']
            
            print(f"方案 {i+1}: Starlink {size[0]} + OneWeb {size[1]} 顆")
            print(f"  成功率: {rate:.1f}%")
            print(f"  Starlink 可見範圍: {s_range[0]}-{s_range[1]} 顆")
            print(f"  OneWeb 可見範圍: {o_range[0]}-{o_range[1]} 顆")
            print()
    else:
        print("❌ 未找到滿足要求的子集規模")
    
    print("💡 結論: 基於實際軌道數據的驗證")