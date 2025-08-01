#!/usr/bin/env python3
"""
修復衛星篩選問題，重新生成正確的預計算數據
"""

import json
import math
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_current_data():
    """分析當前預計算數據的問題"""
    
    print("🔍 分析當前預計算數據問題...")
    
    input_file = Path("/home/sat/ntn-stack/data/starlink_120min_timeseries.json")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    print(f"當前數據包含 {len(data['satellites'])} 顆衛星")
    
    problematic_satellites = []
    good_satellites = []
    
    for i, satellite in enumerate(data['satellites']):
        name = satellite.get('name', f'SAT-{i}')
        time_series = satellite.get('time_series', [])
        
        if not time_series:
            problematic_satellites.append((name, "無時間序列數據"))
            continue
            
        # 檢查前10個數據點
        null_count = 0
        valid_count = 0
        
        for j, point in enumerate(time_series[:10]):
            observation = point.get('observation', {})
            measurement_events = point.get('measurement_events', {})
            
            if (observation.get('elevation_deg') is None and 
                observation.get('range_km') is None and
                measurement_events.get('d2_satellite_distance_m') is None):
                null_count += 1
            else:
                valid_count += 1
        
        if null_count > 5:  # 超過一半的數據點是 null
            problematic_satellites.append((name, f"大量null數據 ({null_count}/10)"))
        else:
            good_satellites.append((name, f"有效數據 ({valid_count}/10)"))
            
            # 檢查距離範圍
            distances = []
            for point in time_series[:50]:  # 檢查前50個點
                obs = point.get('observation', {})
                range_km = obs.get('range_km')
                if range_km is not None:
                    distances.append(range_km)
            
            if distances:
                min_dist = min(distances)
                max_dist = max(distances)
                avg_dist = sum(distances) / len(distances)
                print(f"  ✅ {name}: 距離範圍 {min_dist:.0f}-{max_dist:.0f}km (平均 {avg_dist:.0f}km)")
    
    print(f"\n📊 分析結果:")
    print(f"  有效衛星: {len(good_satellites)} 顆")
    print(f"  問題衛星: {len(problematic_satellites)} 顆")
    
    if problematic_satellites:
        print(f"\n❌ 問題衛星列表:")
        for name, issue in problematic_satellites:
            print(f"  - {name}: {issue}")
    
    return good_satellites, problematic_satellites

def check_original_tle_data():
    """檢查原始 TLE 數據的品質"""
    
    print(f"\n🔍 檢查原始 TLE 數據...")
    
    # 檢查 TLE JSON 數據
    tle_files = [
        Path("/home/sat/ntn-stack/netstack/tle_data/starlink/json/starlink.json"),
        Path("/home/sat/ntn-stack/data/starlink_tle_data.json")
    ]
    
    for tle_file in tle_files:
        if tle_file.exists():
            print(f"📁 檢查 {tle_file}")
            
            with open(tle_file, 'r') as f:
                tle_data = json.load(f)
            
            print(f"  原始 TLE 數據包含 {len(tle_data)} 顆衛星")
            
            # 檢查前5顆衛星的軌道參數
            for i, sat_data in enumerate(tle_data[:5]):
                name = sat_data.get('name', f'SAT-{i}')
                inclination = sat_data.get('INCLINATION')
                raan = sat_data.get('RA_OF_ASC_NODE')
                
                print(f"  - {name}: 傾角={inclination}°, RAAN={raan}°")
                
                # 檢查是否符合地理相關性
                if inclination is not None:
                    if float(inclination) >= 24.9:  # 能覆蓋台灣緯度
                        print(f"    ✅ 地理相關 (傾角 {inclination}° >= 24.9°)")
                    else:
                        print(f"    ❌ 地理無關 (傾角 {inclination}° < 24.9°)")
                else:
                    print(f"    ⚠️ 缺少軌道參數")
            
            break

def regenerate_clean_data():
    """重新生成乾淨的預計算數據"""
    
    print(f"\n🔧 重新生成乾淨的預計算數據...")
    
    # 觸發重新預處理
    from preprocess_120min_timeseries import TimeSeries120MinPreprocessor
    
    preprocessor = TimeSeries120MinPreprocessor(
        data_dir=Path("/home/sat/ntn-stack/data"),
        tle_data_dir=Path("/home/sat/ntn-stack/netstack/tle_data")
    )
    
    print("重新執行預處理...")
    # 這裡可以調用預處理器重新生成數據

if __name__ == "__main__":
    # 分析當前數據問題
    good_satellites, problematic_satellites = analyze_current_data()
    
    # 檢查原始 TLE 數據
    check_original_tle_data()
    
    # 如果問題衛星太多，建議重新生成
    if len(problematic_satellites) > len(good_satellites) * 0.3:
        print(f"\n⚠️ 問題衛星比例過高 ({len(problematic_satellites)}/{len(good_satellites)})，建議重新生成預計算數據")
        print("請執行: cd /home/sat/ntn-stack/simworld/backend && python preprocess_120min_timeseries.py")
    else:
        print(f"\n✅ 數據品質可接受，有 {len(good_satellites)} 顆有效衛星")