#!/usr/bin/env python3
"""
最終覆蓋率驗證器 - 使用實際數據時間範圍
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple

def analyze_current_coverage():
    """分析當前數據的實際覆蓋情況"""
    
    print("🔍 載入並分析實際數據...")
    
    with open('/tmp/satellite_data/stage3_signal_event_analysis_output.json', 'r') as f:
        data = json.load(f)
    
    starlink_satellites = []
    oneweb_satellites = []
    
    # 收集所有衛星數據
    for constellation_name, constellation_data in data['constellations'].items():
        satellites = constellation_data.get('satellites', [])
        
        for sat in satellites:
            if sat.get('constellation') == 'starlink':
                starlink_satellites.append(sat)
            elif sat.get('constellation') == 'oneweb':
                oneweb_satellites.append(sat)
    
    print(f"📊 數據統計:")
    print(f"  Starlink: {len(starlink_satellites)} 顆")
    print(f"  OneWeb: {len(oneweb_satellites)} 顆")
    
    return starlink_satellites, oneweb_satellites

def get_time_range_from_data(satellites):
    """從數據中獲取實際的時間範圍"""
    
    all_times = []
    for sat in satellites:
        positions = sat.get('positions', [])
        for pos in positions:
            time_str = pos['time']
            time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            all_times.append(time_obj)
    
    if all_times:
        start_time = min(all_times)
        end_time = max(all_times)
        return start_time, end_time
    return None, None

def count_visible_satellites_at_time(satellites, target_time):
    """計算指定時間的可見衛星數"""
    
    visible_count = 0
    
    for sat in satellites:
        positions = sat.get('positions', [])
        
        # 找到最接近目標時間的位置
        closest_pos = None
        min_time_diff = float('inf')
        
        for pos in positions:
            pos_time = datetime.fromisoformat(pos['time'].replace('Z', '+00:00'))
            time_diff = abs((pos_time - target_time).total_seconds())
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_pos = pos
        
        # 如果找到合適的位置數據且在時間窗口內
        if closest_pos and min_time_diff <= 300:  # 5分鐘內
            if closest_pos.get('is_visible', False):
                elevation = closest_pos.get('elevation_deg', 0)
                if elevation >= 10:  # 10度仰角門檻
                    visible_count += 1
    
    return visible_count

def test_different_subsets(starlink_satellites, oneweb_satellites):
    """測試不同規模的衛星子集"""
    
    # 獲取時間範圍
    all_satellites = starlink_satellites + oneweb_satellites
    start_time, end_time = get_time_range_from_data(all_satellites)
    
    if not start_time:
        print("❌ 無法獲取時間範圍")
        return
    
    print(f"⏰ 數據時間範圍: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
    
    # 創建測試時間點（每10分鐘一個）
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    test_times = []
    
    for i in range(0, duration_minutes, 10):
        test_time = start_time + timedelta(minutes=i)
        test_times.append(test_time)
    
    print(f"🕐 測試時間點: {len(test_times)} 個")
    
    # 測試不同規模的子集
    test_sizes = [
        (20, 10, "非常小子集"),
        (50, 20, "小子集"), 
        (100, 30, "中等子集"),
        (200, 50, "大子集"),
        (len(starlink_satellites), len(oneweb_satellites), "完整數據集")
    ]
    
    results = []
    
    for starlink_count, oneweb_count, description in test_sizes:
        # 選擇子集（選前N顆）
        subset_starlink = starlink_satellites[:min(starlink_count, len(starlink_satellites))]
        subset_oneweb = oneweb_satellites[:min(oneweb_count, len(oneweb_satellites))]
        
        actual_starlink = len(subset_starlink)
        actual_oneweb = len(subset_oneweb)
        
        print(f"\n📋 {description}: Starlink {actual_starlink}, OneWeb {actual_oneweb}")
        
        # 在每個時間點計算可見性
        starlink_visibility = []
        oneweb_visibility = []
        
        for test_time in test_times:
            s_vis = count_visible_satellites_at_time(subset_starlink, test_time)
            o_vis = count_visible_satellites_at_time(subset_oneweb, test_time)
            
            starlink_visibility.append(s_vis)
            oneweb_visibility.append(o_vis)
        
        # 統計結果
        s_min, s_max, s_avg = min(starlink_visibility), max(starlink_visibility), np.mean(starlink_visibility)
        o_min, o_max, o_avg = min(oneweb_visibility), max(oneweb_visibility), np.mean(oneweb_visibility)
        
        # 計算滿足目標的時間百分比
        starlink_in_target = sum(1 for v in starlink_visibility if 10 <= v <= 15)
        oneweb_in_target = sum(1 for v in oneweb_visibility if 3 <= v <= 6)
        
        starlink_success_rate = starlink_in_target / len(test_times) * 100
        oneweb_success_rate = oneweb_in_target / len(test_times) * 100
        
        print(f"  Starlink 可見範圍: {s_min}-{s_max} 顆 (平均 {s_avg:.1f})")
        print(f"  OneWeb 可見範圍: {o_min}-{o_max} 顆 (平均 {o_avg:.1f})")
        print(f"  Starlink 目標達成率: {starlink_success_rate:.1f}% (目標: 10-15顆)")
        print(f"  OneWeb 目標達成率: {oneweb_success_rate:.1f}% (目標: 3-6顆)")
        
        # 評估是否可行
        overall_success = (starlink_success_rate + oneweb_success_rate) / 2
        status = "✅ 可行" if overall_success >= 50 else "❌ 不可行"
        print(f"  綜合評估: {overall_success:.1f}% {status}")
        
        results.append({
            'description': description,
            'size': (actual_starlink, actual_oneweb),
            'starlink_stats': (s_min, s_max, s_avg, starlink_success_rate),
            'oneweb_stats': (o_min, o_max, o_avg, oneweb_success_rate),
            'overall_success': overall_success
        })
        
        # 如果找到可行方案，可以提前停止
        if overall_success >= 75:  # 75%以上認為是很好的方案
            print(f"🎯 找到優秀的解決方案！")
    
    return results

def main():
    """主函數"""
    
    print("🚀 時空錯置理論實際驗證")
    print("=" * 50)
    
    # 載入數據
    starlink_satellites, oneweb_satellites = analyze_current_coverage()
    
    if not starlink_satellites and not oneweb_satellites:
        print("❌ 無有效衛星數據")
        return
    
    # 測試不同子集規模
    results = test_different_subsets(starlink_satellites, oneweb_satellites)
    
    print(f"\n🏆 最終驗證結果")
    print("=" * 50)
    
    # 找到最佳方案
    viable_solutions = [r for r in results if r['overall_success'] >= 50]
    
    if viable_solutions:
        best = max(viable_solutions, key=lambda x: x['overall_success'])
        print(f"🥇 最佳方案: {best['description']}")
        print(f"   規模: Starlink {best['size'][0]} + OneWeb {best['size'][1]} = {sum(best['size'])} 顆")
        print(f"   成功率: {best['overall_success']:.1f}%")
        
        # 與850/150的對比
        full_size = results[-1]['size']  # 最後一個是完整數據集
        reduction = (1 - sum(best['size']) / sum(full_size)) * 100
        print(f"   相比完整數據集減少: {reduction:.1f}%")
        
        print(f"\n💡 結論: 不需要 850/150 顆衛星!")
        print(f"   實際需要: ~{sum(best['size'])} 顆就能達到合理的覆蓋效果")
        
    else:
        print("❌ 在測試範圍內未找到完全滿足10-15/3-6目標的方案")
        print("   可能的原因:")
        print("   1. 數據時間範圍太短（僅1.5小時）")
        print("   2. 需要更長時間的軌道數據驗證")
        print("   3. 需要考慮軌道相位優化")
    
    # 輸出詳細統計
    print(f"\n📊 所有測試結果:")
    for result in results:
        size_total = sum(result['size'])
        success = result['overall_success']
        print(f"  {result['description']:12}: {size_total:4}顆 -> {success:5.1f}% 成功率")

if __name__ == "__main__":
    main()