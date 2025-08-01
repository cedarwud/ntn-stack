#!/usr/bin/env python3
"""
零容忍衛星篩選系統 - 專為45天強化學習訓練優化
嚴格篩選出能產生有意義換手場景的高品質衛星數據
"""

import json
import math
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RLOptimizedSatelliteFilter:
    """
    強化學習優化的衛星篩選器
    零容忍：任何一項不符合就直接淘汰
    """
    
    def __init__(self, target_lat: float = 24.9441, target_lon: float = 121.3714):
        self.target_lat = target_lat
        self.target_lon = target_lon
        
        # RL 訓練的嚴格標準
        self.min_elevation = 10.0        # 最低可見仰角（度）
        self.min_pass_duration = 180     # 最短通過時間（秒）
        self.min_daily_passes = 2        # 每日最少通過次數
        self.max_daily_passes = 15       # 每日最多通過次數（為極地軌道放寬）
        self.min_orbital_period = 85     # 最短軌道週期（分鐘）
        self.max_orbital_period = 120    # 最長軌道週期（分鐘）
        
        # 物理約束參數
        self.constraints = {
            'INCLINATION': (25.0, 180.0),    # 必須能覆蓋台灣緯度
            'MEAN_MOTION': (11.0, 17.0),     # 對應LEO軌道範圍
            'ECCENTRICITY': (0.0, 0.25),     # 近圓軌道，避免高橢圓軌道
            'RA_OF_ASC_NODE': (0.0, 360.0),  # 升交點赤經
            'ARG_OF_PERICENTER': (0.0, 360.0), # 近地點幅角
            'MEAN_ANOMALY': (0.0, 360.0),    # 平近點角
        }
        
        self.stats = {
            'total_processed': 0,
            'parameter_failures': 0,
            'physics_failures': 0,
            'coverage_failures': 0,
            'suitability_failures': 0,
            'accepted': 0
        }
    
    def filter_constellation(self, tle_data: List[Dict], constellation: str) -> Dict[str, Any]:
        """
        對整個星座進行零容忍篩選
        """
        logger.info(f"🔍 開始對 {constellation.upper()} 進行零容忍篩選")
        logger.info(f"輸入衛星數量: {len(tle_data)}")
        
        results = {
            'constellation': constellation,
            'accepted': [],
            'rejected': [],
            'rejection_reasons': {},
            'statistics': {}
        }
        
        self.stats = {key: 0 for key in self.stats.keys()}
        self.stats['total_processed'] = len(tle_data)
        
        for i, sat_data in enumerate(tle_data):
            if i % 1000 == 0:
                logger.info(f"處理進度: {i}/{len(tle_data)} ({i/len(tle_data)*100:.1f}%)")
            
            satellite_name = sat_data.get('name', f'SAT-{sat_data.get("norad_id", i)}')
            
            # 零容忍驗證管道
            valid, reason = self._strict_validation_pipeline(sat_data)
            
            if valid:
                results['accepted'].append(sat_data)
                self.stats['accepted'] += 1
            else:
                results['rejected'].append(satellite_name)
                results['rejection_reasons'][satellite_name] = reason
        
        # 統計結果
        results['statistics'] = self._generate_statistics()
        
        logger.info(f"✅ {constellation.upper()} 篩選完成:")
        logger.info(f"  接受: {self.stats['accepted']} 顆 ({self.stats['accepted']/len(tle_data)*100:.1f}%)")
        logger.info(f"  拒絕: {len(tle_data) - self.stats['accepted']} 顆")
        
        return results
    
    def _strict_validation_pipeline(self, sat_data: Dict) -> Tuple[bool, str]:
        """
        嚴格的四階段驗證管道
        任何一階段失敗就直接淘汰
        """
        
        # 階段1：參數完整性驗證（零容忍）
        valid, reason = self._validate_parameters(sat_data)
        if not valid:
            self.stats['parameter_failures'] += 1
            return False, f"Parameter: {reason}"
        
        # 階段2：物理合理性驗證（零容忍）
        valid, reason = self._validate_physics(sat_data)
        if not valid:
            self.stats['physics_failures'] += 1
            return False, f"Physics: {reason}"
        
        # 階段3：覆蓋能力驗證（零容忍）
        valid, reason = self._validate_coverage(sat_data)
        if not valid:
            self.stats['coverage_failures'] += 1
            return False, f"Coverage: {reason}"
        
        # 階段4：RL訓練適用性驗證（零容忍）
        valid, reason = self._validate_rl_suitability(sat_data)
        if not valid:
            self.stats['suitability_failures'] += 1
            return False, f"RL_Suitability: {reason}"
        
        return True, "Fully qualified for RL training"
    
    def _validate_parameters(self, sat_data: Dict) -> Tuple[bool, str]:
        """
        階段1：嚴格的參數完整性驗證
        所有必要參數必須存在且為有效數值
        """
        required_params = ['INCLINATION', 'RA_OF_ASC_NODE', 'MEAN_MOTION', 
                          'ECCENTRICITY', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY']
        
        for param in required_params:
            # 檢查參數是否存在
            if param not in sat_data or sat_data[param] is None:
                return False, f"Missing {param}"
            
            # 檢查是否為有效數值
            try:
                value = float(sat_data[param])
                if math.isnan(value) or math.isinf(value):
                    return False, f"Invalid {param}: {value}"
            except (ValueError, TypeError):
                return False, f"Non-numeric {param}: {sat_data[param]}"
        
        # 檢查 TLE 行數據（如果存在）
        if 'line1' in sat_data and 'line2' in sat_data:
            line1 = sat_data['line1']
            line2 = sat_data['line2']
            
            if not line1 or not line2 or len(line1) < 69 or len(line2) < 69:
                return False, "Invalid TLE format"
        
        return True, "Parameters complete"
    
    def _validate_physics(self, sat_data: Dict) -> Tuple[bool, str]:
        """
        階段2：物理合理性驗證
        所有軌道參數必須在LEO衛星的合理範圍內
        """
        
        for param, (min_val, max_val) in self.constraints.items():
            value = float(sat_data[param])
            
            if not (min_val <= value <= max_val):
                return False, f"{param}={value:.2f} outside [{min_val}, {max_val}]"
        
        # 特殊的物理一致性檢查
        inclination = float(sat_data['INCLINATION'])
        mean_motion = float(sat_data['MEAN_MOTION'])
        eccentricity = float(sat_data['ECCENTRICITY'])
        
        # 軌道週期計算
        orbital_period_minutes = 24 * 60 / mean_motion
        
        if not (self.min_orbital_period <= orbital_period_minutes <= self.max_orbital_period):
            return False, f"Orbital period {orbital_period_minutes:.1f}min outside [{self.min_orbital_period}, {self.max_orbital_period}]"
        
        # 軌道傾角必須能覆蓋目標緯度
        if inclination < abs(self.target_lat):
            return False, f"Inclination {inclination:.1f}° cannot cover latitude {self.target_lat:.1f}°"
        
        # 避免極高離心率（不穩定軌道）
        if eccentricity > 0.2:
            return False, f"High eccentricity {eccentricity:.3f} unsuitable for communications"
        
        return True, "Physics valid"
    
    def _validate_coverage(self, sat_data: Dict) -> Tuple[bool, str]:
        """
        階段3：精確的覆蓋能力驗證
        使用軌道力學計算衛星是否能有效覆蓋目標區域
        """
        inclination = float(sat_data['INCLINATION'])
        raan = float(sat_data['RA_OF_ASC_NODE'])
        mean_motion = float(sat_data['MEAN_MOTION'])
        
        # 極地軌道（>80°）：幾乎必然經過任何緯度
        if inclination > 80:
            return True, "Polar orbit coverage guaranteed"
        
        # 對於中等傾角軌道，進行更精細的計算
        orbital_period_hours = 24 / mean_motion
        earth_rotation_per_orbit = orbital_period_hours * 15  # 地球每小時自轉15°
        
        # 計算軌道平面與目標位置的幾何關係
        # 這是一個簡化但比原版更準確的模型
        
        # 軌道傾角對應的緯度覆蓋範圍
        max_coverage_lat = inclination
        min_coverage_lat = -inclination
        
        if not (min_coverage_lat <= self.target_lat <= max_coverage_lat):
            return False, f"Target lat {self.target_lat}° outside coverage [{min_coverage_lat:.1f}°, {max_coverage_lat:.1f}°]"
        
        # 經度覆蓋的近似計算
        # 考慮地球自轉和軌道進動的影響
        longitude_coverage_range = earth_rotation_per_orbit + 45  # 加上軌道幾何的影響
        
        # 檢查升交點赤經與目標經度的關係
        lon_diff = abs(self.target_lon - raan)
        if lon_diff > 180:
            lon_diff = 360 - lon_diff
        
        if lon_diff > longitude_coverage_range / 2:
            return False, f"Longitude difference {lon_diff:.1f}° > coverage range {longitude_coverage_range/2:.1f}°"
        
        return True, "Coverage validated"
    
    def _validate_rl_suitability(self, sat_data: Dict) -> Tuple[bool, str]:
        """
        階段4：RL訓練適用性驗證
        確保衛星能產生有意義的換手訓練場景
        """
        inclination = float(sat_data['INCLINATION'])
        mean_motion = float(sat_data['MEAN_MOTION'])
        
        # 估算每日通過次數
        # 這是基於軌道週期和地球自轉的簡化計算
        orbital_period_hours = 24 / mean_motion
        daily_passes = 24 / orbital_period_hours
        
        # 考慮軌道傾角對通過次數的影響
        if inclination > 80:  # 極地軌道
            effective_daily_passes = daily_passes * 0.8  # 不是每次都經過目標區域
        elif inclination > 50:  # 中等傾角
            effective_daily_passes = daily_passes * 0.4
        else:  # 低傾角
            effective_daily_passes = daily_passes * 0.2
        
        if effective_daily_passes < self.min_daily_passes:
            return False, f"Daily passes {effective_daily_passes:.1f} < minimum {self.min_daily_passes}"
        
        if effective_daily_passes > self.max_daily_passes:
            return False, f"Daily passes {effective_daily_passes:.1f} > maximum {self.max_daily_passes} (too frequent)"
        
        # 軌道多樣性檢查 - 避免選擇過於相似的軌道
        # 這可以在後處理階段進一步優化
        
        return True, "RL training suitable"
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """生成詳細的篩選統計報告"""
        total = self.stats['total_processed']
        
        return {
            'total_satellites': total,
            'accepted': self.stats['accepted'],
            'rejected': total - self.stats['accepted'],
            'acceptance_rate': self.stats['accepted'] / total * 100 if total > 0 else 0,
            'failure_breakdown': {
                'parameter_failures': self.stats['parameter_failures'],
                'physics_failures': self.stats['physics_failures'],
                'coverage_failures': self.stats['coverage_failures'],
                'suitability_failures': self.stats['suitability_failures']
            },
            'failure_rates': {
                'parameter_failure_rate': self.stats['parameter_failures'] / total * 100 if total > 0 else 0,
                'physics_failure_rate': self.stats['physics_failures'] / total * 100 if total > 0 else 0,
                'coverage_failure_rate': self.stats['coverage_failures'] / total * 100 if total > 0 else 0,
                'suitability_failure_rate': self.stats['suitability_failures'] / total * 100 if total > 0 else 0
            }
        }

def main():
    """測試零容忍篩選系統"""
    
    # 載入最新的 TLE 數據
    tle_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
    
    filter_system = RLOptimizedSatelliteFilter()
    
    # 測試 Starlink
    starlink_file = tle_dir / "starlink/json/starlink_20250731.json"
    if starlink_file.exists():
        with open(starlink_file, 'r') as f:
            starlink_data = json.load(f)
        
        starlink_results = filter_system.filter_constellation(starlink_data, "starlink")
        
        print(f"\n📊 Starlink 篩選結果:")
        print(f"接受: {starlink_results['statistics']['accepted']} 顆")
        print(f"拒絕: {starlink_results['statistics']['rejected']} 顆")
        print(f"接受率: {starlink_results['statistics']['acceptance_rate']:.1f}%")
        
        # 輸出失敗原因分析
        failures = starlink_results['statistics']['failure_breakdown']
        print(f"\n失敗原因分析:")
        for reason, count in failures.items():
            print(f"  {reason}: {count} ({count/len(starlink_data)*100:.1f}%)")
    
    # 測試 OneWeb
    oneweb_file = tle_dir / "oneweb/json/oneweb_20250731.json"
    if oneweb_file.exists():
        with open(oneweb_file, 'r') as f:
            oneweb_data = json.load(f)
        
        oneweb_results = filter_system.filter_constellation(oneweb_data, "oneweb")
        
        print(f"\n📊 OneWeb 篩選結果:")
        print(f"接受: {oneweb_results['statistics']['accepted']} 顆")
        print(f"拒絕: {oneweb_results['statistics']['rejected']} 顆")
        print(f"接受率: {oneweb_results['statistics']['acceptance_rate']:.1f}%")
        
        # 輸出失敗原因分析
        failures = oneweb_results['statistics']['failure_breakdown']
        print(f"\n失敗原因分析:")
        for reason, count in failures.items():
            print(f"  {reason}: {count} ({count/len(oneweb_data)*100:.1f}%)")

if __name__ == "__main__":
    main()