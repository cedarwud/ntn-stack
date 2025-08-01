#!/usr/bin/env python3
"""
調試 OneWeb 被全部拒絕的原因
"""

import json
from pathlib import Path
from rl_optimized_satellite_filter import RLOptimizedSatelliteFilter

def debug_oneweb_rejection():
    # 載入 OneWeb 數據
    oneweb_file = Path("/home/sat/ntn-stack/netstack/tle_data/oneweb/json/oneweb_20250731.json")
    with open(oneweb_file, 'r') as f:
        oneweb_data = json.load(f)
    
    filter_system = RLOptimizedSatelliteFilter()
    
    print("🔍 調試 OneWeb 前3顆衛星的拒絕原因:")
    
    for i, sat_data in enumerate(oneweb_data[:3]):
        print(f"\n--- 衛星 {i+1} ---")
        print(f"軌道參數:")
        print(f"  INCLINATION: {sat_data.get('INCLINATION')}")
        print(f"  MEAN_MOTION: {sat_data.get('MEAN_MOTION')}")
        print(f"  RA_OF_ASC_NODE: {sat_data.get('RA_OF_ASC_NODE')}")
        
        # 逐步驗證
        valid, reason = filter_system._validate_parameters(sat_data)
        print(f"參數驗證: {'✅' if valid else '❌'} {reason}")
        
        if valid:
            valid, reason = filter_system._validate_physics(sat_data)
            print(f"物理驗證: {'✅' if valid else '❌'} {reason}")
        
        if valid:
            valid, reason = filter_system._validate_coverage(sat_data)
            print(f"覆蓋驗證: {'✅' if valid else '❌'} {reason}")
        
        if valid:
            valid, reason = filter_system._validate_rl_suitability(sat_data)
            print(f"RL適用性: {'✅' if valid else '❌'} {reason}")
            
            # 詳細分析 RL 適用性失敗的原因
            if not valid:
                inclination = float(sat_data['INCLINATION'])
                mean_motion = float(sat_data['MEAN_MOTION'])
                orbital_period_hours = 24 / mean_motion
                daily_passes = 24 / orbital_period_hours
                
                if inclination > 80:
                    effective_daily_passes = daily_passes * 0.8
                elif inclination > 50:
                    effective_daily_passes = daily_passes * 0.4
                else:
                    effective_daily_passes = daily_passes * 0.2
                
                print(f"  詳細分析:")
                print(f"    軌道週期: {orbital_period_hours:.2f} 小時")
                print(f"    理論每日通過: {daily_passes:.2f} 次")
                print(f"    有效每日通過: {effective_daily_passes:.2f} 次")
                print(f"    要求範圍: {filter_system.min_daily_passes} - {filter_system.max_daily_passes} 次")

if __name__ == "__main__":
    debug_oneweb_rejection()