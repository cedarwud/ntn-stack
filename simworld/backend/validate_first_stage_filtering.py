#!/usr/bin/env python3
"""
驗證第一階段地理篩選邏輯
使用完整軌道週期計算，篩選掉永遠不會經過臺北大學上空的衛星
"""

import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 國立臺北大學座標
NTPU_LAT = 24.9441  # °N
NTPU_LON = 121.3714  # °E

def load_latest_tle_data(constellation: str) -> List[Dict]:
    """載入最新的 TLE 數據"""
    tle_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
    
    # 尋找最新的數據文件
    json_files = list((tle_dir / constellation / "json").glob(f"{constellation}_*.json"))
    if not json_files:
        raise FileNotFoundError(f"找不到 {constellation} 的 JSON 數據文件")
    
    # 按文件名排序，取最新的
    latest_file = sorted(json_files)[-1]
    
    print(f"載入 {constellation} 最新數據: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def extract_orbital_elements(sat_data: Dict) -> Tuple[float, float, float]:
    """提取軌道要素"""
    try:
        # 方法1：直接從 JSON 數據提取
        inclination = sat_data.get("INCLINATION")
        raan = sat_data.get("RA_OF_ASC_NODE")  # 升交點赤經
        mean_motion = sat_data.get("MEAN_MOTION")  # 平均運動
        
        if inclination is not None and raan is not None and mean_motion is not None:
            return float(inclination), float(raan), float(mean_motion)
        
        # 方法2：從 TLE line2 提取
        line2 = sat_data.get("line2", "")
        if line2 and len(line2) >= 70:
            inclination = float(line2[8:16].strip())
            raan = float(line2[17:25].strip())
            mean_motion = float(line2[52:63].strip())
            return inclination, raan, mean_motion
        
        return None, None, None
        
    except (ValueError, IndexError, TypeError) as e:
        return None, None, None

def can_satellite_pass_over_location(inclination: float, raan: float, mean_motion: float, target_lat: float, target_lon: float) -> bool:
    """
    判斷衛星是否可能經過目標位置上空
    基於軌道力學基本原理
    """
    # 1. 軌道傾角檢查：衛星軌道必須能覆蓋目標緯度
    if inclination < abs(target_lat):
        return False
    
    # 2. 極地軌道（傾角 > 80°）：幾乎可以經過地球任何位置
    if inclination > 80:
        return True
    
    # 3. 對於中等傾角軌道，需要更詳細的分析
    # 衛星軌道平面與地球自轉的相互作用會影響覆蓋範圍
    
    # 簡化的地理覆蓋判斷：
    # 在一個軌道週期內，地球自轉會讓衛星"看到"不同的經度範圍
    
    # LEO 衛星典型軌道週期約 90-100 分鐘
    # 在此期間，地球自轉約 22.5-25°
    orbital_period_hours = 24 / mean_motion if mean_motion else 1.5  # 軌道週期（小時）
    earth_rotation_degrees = orbital_period_hours * 15  # 地球自轉角度（每小時15°）
    
    # 對於非極地軌道，檢查升交點赤經與目標經度的關係
    if inclination < 80:
        # 計算軌道平面在目標緯度處的經度覆蓋範圍
        # 這是一個簡化的模型
        longitude_coverage = earth_rotation_degrees + 30  # 加上軌道傾角影響
        
        # 檢查目標經度是否在可能的覆蓋範圍內
        lon_diff = abs(target_lon - raan)
        if lon_diff > 180:
            lon_diff = 360 - lon_diff
        
        if lon_diff > longitude_coverage:
            return False
    
    return True

def analyze_constellation_coverage(constellation: str) -> Tuple[int, int, List[str]]:
    """分析星座對臺北大學的覆蓋能力"""
    
    print(f"\n🔍 分析 {constellation.upper()} 星座覆蓋能力...")
    
    # 載入數據
    tle_data = load_latest_tle_data(constellation)
    total_satellites = len(tle_data)
    
    print(f"總衛星數量: {total_satellites}")
    
    can_pass_over = []
    cannot_pass_over = []
    invalid_data = []
    
    for sat_data in tle_data:
        name = sat_data.get('name', 'Unknown')
        norad_id = sat_data.get('norad_id', 'Unknown')
        
        # 提取軌道要素
        inclination, raan, mean_motion = extract_orbital_elements(sat_data)
        
        if inclination is None or raan is None or mean_motion is None:
            invalid_data.append(f"{name} (ID: {norad_id}) - 缺少軌道參數")
            continue
        
        # 判斷是否可能經過臺北大學
        if can_satellite_pass_over_location(inclination, raan, mean_motion, NTPU_LAT, NTPU_LON):
            can_pass_over.append({
                'name': name,
                'norad_id': norad_id,
                'inclination': inclination,
                'raan': raan,
                'mean_motion': mean_motion
            })
        else:
            cannot_pass_over.append({
                'name': name,
                'norad_id': norad_id,
                'inclination': inclination,
                'raan': raan,
                'mean_motion': mean_motion,
                'reason': f'傾角 {inclination:.1f}° 無法覆蓋緯度 {NTPU_LAT}°' if inclination < abs(NTPU_LAT) else '經度覆蓋範圍不足'
            })
    
    print(f"分析結果:")
    print(f"  ✅ 可能經過: {len(can_pass_over)} 顆 ({len(can_pass_over)/total_satellites*100:.1f}%)")
    print(f"  ❌ 不會經過: {len(cannot_pass_over)} 顆 ({len(cannot_pass_over)/total_satellites*100:.1f}%)")
    print(f"  ⚠️ 數據無效: {len(invalid_data)} 顆 ({len(invalid_data)/total_satellites*100:.1f}%)")
    
    # 顯示一些被篩選掉的衛星示例
    if cannot_pass_over:
        print(f"\n❌ 被篩選掉的衛星示例 (前5顆):")
        for sat in cannot_pass_over[:5]:
            print(f"  - {sat['name']}: {sat['reason']}")
    
    # 顯示軌道傾角分布
    if can_pass_over:
        inclinations = [sat['inclination'] for sat in can_pass_over]
        print(f"\n✅ 有效衛星軌道傾角分布:")
        print(f"  - 最小傾角: {min(inclinations):.1f}°")
        print(f"  - 最大傾角: {max(inclinations):.1f}°")
        print(f"  - 平均傾角: {sum(inclinations)/len(inclinations):.1f}°")
        
        # 按傾角範圍分組
        low_inc = [i for i in inclinations if i < 45]
        mid_inc = [i for i in inclinations if 45 <= i < 75]
        high_inc = [i for i in inclinations if i >= 75]
        
        print(f"  - 低傾角 (<45°): {len(low_inc)} 顆")
        print(f"  - 中傾角 (45-75°): {len(mid_inc)} 顆")
        print(f"  - 高傾角 (≥75°): {len(high_inc)} 顆")
    
    return len(can_pass_over), len(cannot_pass_over), invalid_data

def compare_with_current_preprocessing():
    """比較當前預處理結果"""
    
    print(f"\n🔄 比較當前預處理結果...")
    
    # 載入當前預處理結果
    current_file = Path("/home/sat/ntn-stack/data/starlink_120min_timeseries.json")
    if current_file.exists():
        with open(current_file, 'r') as f:
            current_data = json.load(f)
        
        current_satellites = len(current_data.get('satellites', []))
        print(f"當前預處理選擇的 Starlink 衛星: {current_satellites} 顆")
        
        # 顯示當前選擇的衛星
        if current_data.get('satellites'):
            print("當前選擇的衛星:")
            for i, sat in enumerate(current_data['satellites'][:10]):
                name = sat.get('name', f'SAT-{i}')
                print(f"  - {name}")
    else:
        print("找不到當前預處理結果文件")

if __name__ == "__main__":
    print("🛰️ 驗證第一階段地理篩選邏輯")
    print(f"目標位置: 國立臺北大學 ({NTPU_LAT}°N, {NTPU_LON}°E)")
    
    # 分析 Starlink
    starlink_valid, starlink_invalid, starlink_errors = analyze_constellation_coverage("starlink")
    
    # 分析 OneWeb
    oneweb_valid, oneweb_invalid, oneweb_errors = analyze_constellation_coverage("oneweb")
    
    print(f"\n📊 總結:")
    print(f"Starlink: {starlink_valid} 顆有效衛星")
    print(f"OneWeb: {oneweb_valid} 顆有效衛星")
    
    # 比較當前預處理結果
    compare_with_current_preprocessing()
    
    print(f"\n💡 建議:")
    if starlink_valid < 50:
        print("- Starlink 有效衛星數量較少，可能需要放寬篩選條件")
    if oneweb_valid < 30:
        print("- OneWeb 有效衛星數量較少，可能需要放寬篩選條件")
    
    print("\n✅ 分析完成！")