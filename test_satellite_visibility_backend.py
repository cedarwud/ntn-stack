#!/usr/bin/env python3
"""
後端衛星可見性完整週期測試
分析現在的篩選邏輯並測試96分鐘完整軌道週期內的可見衛星數量
"""

import sys
import os
sys.path.append('/home/sat/ntn-stack/netstack/src')

import json
import asyncio
from datetime import datetime, timedelta, timezone

# 導入現有的階段處理器
from stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner

async def load_stage6_data():
    """載入階段六的動態池規劃結果"""
    try:
        # 嘗試多個可能的階段六文件位置
        possible_paths = [
            "/home/sat/ntn-stack/netstack/output_from_stages/enhanced_dynamic_pools_output.json",
            "/home/sat/ntn-stack/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json",
            "/home/sat/ntn-stack/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
        ]
        
        stage6_path = None
        for path in possible_paths:
            if os.path.exists(path):
                stage6_path = path
                break
        
        if not stage6_path:
            print(f"❌ 找不到階段六文件在以下位置:")
            for path in possible_paths:
                print(f"  - {path}")
            return None
            
        with open(stage6_path, 'r') as f:
            data = json.load(f)
            
        print(f"✅ 成功載入階段六數據: {stage6_path}")
        return data
        
    except Exception as e:
        print(f"❌ 載入階段六數據失敗: {e}")
        return None

def analyze_current_filtering_logic(stage6_data):
    """分析現在的篩選邏輯"""
    print("\n" + "="*60)
    print("📊 現在的篩選邏輯分析")
    print("="*60)
    
    if not stage6_data:
        print("❌ 無法分析：階段六數據不可用")
        return
    
    # 提取衛星資訊
    satellites = stage6_data.get('dynamic_satellite_pool', {}).get('selection_details', [])
    metadata = stage6_data.get('metadata', {})
    optimization_results = stage6_data.get('optimization_results', {})
    
    print(f"總選中衛星數: {len(satellites)} 顆")
    
    # 按星座分組
    starlink_sats = [s for s in satellites if s.get('constellation', '').lower() == 'starlink']
    oneweb_sats = [s for s in satellites if s.get('constellation', '').lower() == 'oneweb']
    
    print(f"Starlink 衛星池: {len(starlink_sats)} 顆")
    print(f"OneWeb 衛星池: {len(oneweb_sats)} 顆")
    
    # 分析篩選標準
    print(f"\n📋 現在的篩選標準:")
    print(f"- 處理器: {metadata.get('processor', 'unknown')}")
    print(f"- 算法: {metadata.get('algorithm', 'unknown')}")
    print(f"- 覆蓋合規率: {optimization_results.get('visibility_compliance_percent', 0):.1f}%")
    print(f"- 時間分佈品質: {optimization_results.get('temporal_distribution_score', 0):.1f}")
    print(f"- 信號品質評分: {optimization_results.get('signal_quality_score', 0):.1f}")
    
    # 檢查時間序列數據完整性
    if starlink_sats:
        sample_sat = starlink_sats[0]
        timeseries = sample_sat.get('position_timeseries', [])
        print(f"\n⏰ 時間序列數據:")
        print(f"- 每顆衛星時間點數: {len(timeseries)} 個")
        print(f"- 預期時間點數: 192 個 (96分鐘 × 2點/分鐘)")
        print(f"- 數據完整性: {'✅ 完整' if len(timeseries) >= 192 else '⚠️ 不完整'}")

def test_visibility_over_orbit_cycle(stage6_data, constellation="starlink"):
    """測試完整軌道週期內的可見衛星數量變化"""
    print(f"\n" + "="*60)
    print(f"🛰️ {constellation.upper()} 完整週期可見性測試")
    print("="*60)
    
    if not stage6_data:
        print("❌ 無法測試：階段六數據不可用")
        return
    
    # 提取對應星座的衛星
    satellites = stage6_data.get('dynamic_satellite_pool', {}).get('selection_details', [])
    target_sats = [s for s in satellites if s.get('constellation', '').lower() == constellation.lower()]
    
    if not target_sats:
        print(f"❌ 找不到 {constellation} 衛星數據")
        return
    
    print(f"📊 分析 {len(target_sats)} 顆 {constellation} 衛星的可見性")
    
    # 設定仰角門檻
    min_elevation = 5.0 if constellation.lower() == 'starlink' else 10.0
    print(f"仰角門檻: ≥ {min_elevation}°")
    
    # 檢查時間序列長度
    first_sat = target_sats[0]
    timeseries = first_sat.get('position_timeseries', [])
    time_points = len(timeseries)
    
    if time_points < 10:
        print(f"❌ 時間序列數據太少: 只有 {time_points} 個點")
        return
    
    print(f"時間範圍: {time_points} 個時間點 ({time_points * 30 / 60:.1f} 分鐘)")
    
    # 逐時間點統計可見衛星
    visibility_stats = []
    sample_times = []
    
    print(f"\n⏰ 逐時間點可見性分析:")
    print(f"{'時間點':<8} {'時間':<12} {'可見數':<8} {'衛星ID (前5個)'}")
    print("-" * 60)
    
    for t in range(time_points):
        visible_count = 0
        visible_satellites = []
        
        # 統計這個時間點的可見衛星
        for sat in target_sats:
            sat_timeseries = sat.get('position_timeseries', [])
            if t < len(sat_timeseries):
                pos = sat_timeseries[t]
                elevation = pos.get('elevation_deg', -90)
                
                if elevation >= min_elevation:
                    visible_count += 1
                    visible_satellites.append({
                        'sat_id': sat.get('satellite_id', ''),
                        'elevation': elevation,
                        'azimuth': pos.get('azimuth_deg', 0)
                    })
        
        visibility_stats.append(visible_count)
        
        # 記錄樣本時間
        if t < len(first_sat.get('position_timeseries', [])):
            time_str = first_sat['position_timeseries'][t].get('time', '')[:19]  # 去掉毫秒
            sample_times.append(time_str)
        else:
            sample_times.append(f"T+{t*30}s")
        
        # 顯示每10個時間點的詳情（或最後一個）
        if t % 10 == 0 or t == time_points - 1:
            visible_ids = [v['sat_id'].split('_')[-1] for v in visible_satellites[:5]]  # 只顯示後綴
            ids_str = ', '.join(visible_ids) if visible_ids else "無"
            print(f"{t:<8} {sample_times[t][11:19] if len(sample_times[t]) > 11 else sample_times[t]:<12} {visible_count:<8} {ids_str}")
    
    # 統計結果
    if visibility_stats:
        avg_visible = sum(visibility_stats) / len(visibility_stats)
        max_visible = max(visibility_stats)
        min_visible = min(visibility_stats)
        
        print(f"\n📈 統計結果:")
        print(f"平均可見衛星: {avg_visible:.1f} 顆")
        print(f"最大可見衛星: {max_visible} 顆")
        print(f"最小可見衛星: {min_visible} 顆")
        print(f"變化範圍: {min_visible}-{max_visible} 顆")
        
        # 分析可見性穩定度
        variation = max_visible - min_visible
        stability = (1 - variation / avg_visible) if avg_visible > 0 else 0
        print(f"可見性穩定度: {stability:.1%}")
        
        # 檢查是否符合 handover 研究需求
        target_min = 10 if constellation.lower() == 'starlink' else 3
        target_max = 15 if constellation.lower() == 'starlink' else 6
        
        print(f"\n🎯 Handover 研究需求分析:")
        print(f"目標範圍: {target_min}-{target_max} 顆")
        print(f"實際範圍: {min_visible}-{max_visible} 顆")
        
        if min_visible >= target_min and max_visible <= target_max:
            print("✅ 符合 handover 研究需求")
        elif min_visible < target_min:
            print(f"⚠️ 最小可見數 ({min_visible}) 低於目標 ({target_min})")
        elif max_visible > target_max:
            print(f"⚠️ 最大可見數 ({max_visible}) 超過目標 ({target_max})")
            print("💡 建議：階段六需要更精確的數量控制")
        
        return {
            'avg_visible': avg_visible,
            'max_visible': max_visible,
            'min_visible': min_visible,
            'stability': stability,
            'meets_target': min_visible >= target_min and max_visible <= target_max
        }
    
    return None

def analyze_handover_opportunities(stage6_data):
    """分析 handover 機會"""
    print(f"\n" + "="*60)
    print("🔄 Handover 機會分析")
    print("="*60)
    
    if not stage6_data:
        print("❌ 無法分析：階段六數據不可用")
        return
    
    satellites = stage6_data.get('dynamic_satellite_pool', {}).get('selection_details', [])
    starlink_sats = [s for s in satellites if s.get('constellation', '').lower() == 'starlink']
    
    if not starlink_sats:
        print("❌ 找不到 Starlink 衛星數據")
        return
    
    # 分析衛星進入/離開事件
    time_points = len(starlink_sats[0].get('position_timeseries', []))
    handover_events = []
    
    for t in range(1, time_points):
        # 統計前一個時間點和當前時間點的可見衛星
        prev_visible = set()
        curr_visible = set()
        
        for sat in starlink_sats:
            sat_timeseries = sat.get('position_timeseries', [])
            sat_id = sat.get('satellite_id', '')
            
            if t-1 < len(sat_timeseries) and t < len(sat_timeseries):
                prev_elevation = sat_timeseries[t-1].get('elevation_deg', -90)
                curr_elevation = sat_timeseries[t].get('elevation_deg', -90)
                
                if prev_elevation >= 5:
                    prev_visible.add(sat_id)
                if curr_elevation >= 5:
                    curr_visible.add(sat_id)
        
        # 檢查進入/離開事件
        entering = curr_visible - prev_visible
        leaving = prev_visible - curr_visible
        
        if entering or leaving:
            handover_events.append({
                'time_point': t,
                'entering': len(entering),
                'leaving': len(leaving),
                'entering_sats': list(entering)[:3],  # 只記錄前3個
                'leaving_sats': list(leaving)[:3]
            })
    
    print(f"檢測到 {len(handover_events)} 個 handover 事件")
    
    if handover_events:
        print(f"\n前 10 個 handover 事件:")
        print(f"{'時間點':<8} {'進入':<6} {'離開':<6} {'事件詳情'}")
        print("-" * 50)
        
        for event in handover_events[:10]:
            entering = event['entering']
            leaving = event['leaving']
            details = []
            if entering > 0:
                details.append(f"+{entering}顆")
            if leaving > 0:
                details.append(f"-{leaving}顆")
            detail_str = ', '.join(details)
            
            print(f"{event['time_point']:<8} {entering:<6} {leaving:<6} {detail_str}")
        
        # 分析 handover 頻率
        total_time_minutes = time_points * 30 / 60
        handover_rate = len(handover_events) / total_time_minutes
        
        print(f"\nHandover 事件頻率: {handover_rate:.2f} 次/分鐘")
        print(f"平均每 {60/handover_rate:.1f} 秒有一次 handover 機會")

async def main():
    """主測試程序"""
    print("🛰️ 後端衛星可見性完整週期測試")
    print("="*60)
    
    # 載入階段六數據
    stage6_data = await load_stage6_data()
    
    # 分析現在的篩選邏輯
    analyze_current_filtering_logic(stage6_data)
    
    # 測試 Starlink 可見性
    starlink_results = test_visibility_over_orbit_cycle(stage6_data, "starlink")
    
    # 測試 OneWeb 可見性
    oneweb_results = test_visibility_over_orbit_cycle(stage6_data, "oneweb")
    
    # 分析 handover 機會
    analyze_handover_opportunities(stage6_data)
    
    # 總結和建議
    print(f"\n" + "="*60)
    print("💡 總結與建議")
    print("="*60)
    
    if starlink_results:
        print(f"Starlink:")
        print(f"  當前可見範圍: {starlink_results['min_visible']}-{starlink_results['max_visible']} 顆")
        print(f"  目標範圍: 10-15 顆")
        if not starlink_results['meets_target']:
            print(f"  ⚠️ 需要調整階段六選擇邏輯")
    
    if oneweb_results:
        print(f"OneWeb:")
        print(f"  當前可見範圍: {oneweb_results['min_visible']}-{oneweb_results['max_visible']} 顆")
        print(f"  目標範圍: 3-6 顆")
        if not oneweb_results['meets_target']:
            print(f"  ⚠️ 需要調整階段六選擇邏輯")

if __name__ == "__main__":
    asyncio.run(main())