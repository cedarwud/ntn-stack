#!/usr/bin/env python3
"""
衛星候選預篩選器 - Phase 0 Implementation
基於軌道參數進行預篩選，大幅減少後續詳細計算的工作量

功能:
1. 軌道幾何預篩選 - 基於軌道傾角判斷緯度覆蓋範圍
2. 軌道高度檢查 - 基於軌道高度計算最大可見距離  
3. 地理覆蓋檢查 - 軌道平面是否可能經過目標經度
4. 最小距離檢查 - 衛星與目標座標的最近可能距離

預期優化效果:
- 從 ~6000 顆衛星篩選到 ~500-1000 顆候選衛星
- 減少後續計算量 80-90%
- 加速整體分析時間從小時級到分鐘級
"""

import math
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from skyfield.api import EarthSatellite, utc, load
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class ObserverLocation:
    """觀察者位置"""
    latitude: float   # 緯度 (度)
    longitude: float  # 經度 (度) 
    altitude: float = 0.0  # 海拔高度 (米)


@dataclass
class OrbitParameters:
    """軌道參數"""
    inclination: float      # 軌道傾角 (度)
    semi_major_axis: float  # 半長軸 (km)
    eccentricity: float     # 離心率
    raan: float            # 升交點赤經 (度)
    argument_of_perigee: float  # 近地點幅角 (度)
    mean_anomaly: float    # 平均近點角 (度)


class SatellitePrefilter:
    """衛星候選預篩選器"""
    
    def __init__(self, min_elevation: float = 5.0, earth_radius: float = 6371.0):
        """
        初始化預篩選器
        
        Args:
            min_elevation: 最小仰角要求 (度)
            earth_radius: 地球半徑 (km)
        """
        self.min_elevation = min_elevation
        self.earth_radius = earth_radius
        self.ts = load.timescale()
        
        # 預計算常用值
        self.min_elevation_rad = math.radians(min_elevation)
        
    def extract_orbit_parameters(self, satellite_data: Dict[str, str]) -> OrbitParameters:
        """從 TLE 數據提取軌道參數"""
        try:
            line1 = satellite_data['line1']
            line2 = satellite_data['line2']
            
            # 從 TLE 第二行提取軌道參數
            inclination = float(line2[8:16])
            raan = float(line2[17:25])
            eccentricity = float('0.' + line2[26:33])
            argument_of_perigee = float(line2[34:42])
            mean_anomaly = float(line2[43:51])
            mean_motion = float(line2[52:63])  # 每日軌道圈數
            
            # 計算半長軸 (使用開普勒第三定律)
            # a = (GM / (2π * n)^2)^(1/3)
            # 其中 n = mean_motion * 2π / 86400 (rad/s)
            mu = 398600.4418  # 地球引力常數 km³/s²
            n = mean_motion * 2 * math.pi / 86400  # 轉換為 rad/s
            semi_major_axis = (mu / (n * n)) ** (1/3)
            
            return OrbitParameters(
                inclination=inclination,
                semi_major_axis=semi_major_axis,
                eccentricity=eccentricity,
                raan=raan,
                argument_of_perigee=argument_of_perigee,
                mean_anomaly=mean_anomaly
            )
            
        except Exception as e:
            logger.error(f"提取軌道參數失敗 {satellite_data['name']}: {e}")
            return None
    
    def check_latitude_coverage(self, orbit: OrbitParameters, observer_lat: float) -> bool:
        """
        檢查軌道傾角是否允許衛星經過觀察者緯度
        
        Args:
            orbit: 軌道參數
            observer_lat: 觀察者緯度 (度)
            
        Returns:
            True 如果衛星可能經過該緯度
        """
        # 衛星能到達的最大緯度等於軌道傾角
        max_reachable_lat = abs(orbit.inclination)
        
        # 考慮軌道高度的地球視線效應
        # 在軌道高度下，地平線距離更遠，可見範圍增大
        altitude_km = orbit.semi_major_axis - self.earth_radius
        horizon_angle = math.degrees(math.acos(self.earth_radius / (self.earth_radius + altitude_km)))
        
        # 有效可見緯度範圍
        effective_max_lat = max_reachable_lat + horizon_angle
        
        return abs(observer_lat) <= effective_max_lat
    
    def check_orbital_altitude_visibility(self, orbit: OrbitParameters, observer_lat: float) -> bool:
        """
        檢查軌道高度是否允許在目標緯度達到最小仰角
        
        Args:
            orbit: 軌道參數  
            observer_lat: 觀察者緯度 (度)
            
        Returns:
            True 如果理論上可能達到最小仰角
        """
        altitude_km = orbit.semi_major_axis - self.earth_radius
        
        # 計算理論最大仰角（衛星在天頂時）
        # 考慮地球曲率和軌道高度
        observer_lat_rad = math.radians(abs(observer_lat))
        
        # 地心距離
        geocentric_distance = self.earth_radius
        satellite_distance = orbit.semi_major_axis
        
        # 最大可能仰角（衛星直接在觀察者上空時）
        max_elevation = math.pi / 2  # 90度，天頂
        
        # 最小可能距離（衛星在地平線上時）
        min_distance = math.sqrt(
            satellite_distance**2 + geocentric_distance**2 - 
            2 * satellite_distance * geocentric_distance * math.cos(observer_lat_rad)
        )
        
        # 計算對應的最大仰角
        if min_distance > 0:
            # 使用余弦定理計算仰角
            cos_elevation = (min_distance**2 + geocentric_distance**2 - satellite_distance**2) / (2 * min_distance * geocentric_distance)
            cos_elevation = max(-1, min(1, cos_elevation))  # 限制在 [-1, 1] 範圍
            max_possible_elevation = math.pi / 2 - math.acos(cos_elevation)
            
            return max_possible_elevation >= self.min_elevation_rad
        
        return False
    
    def check_longitude_coverage(self, orbit: OrbitParameters, observer_lon: float, 
                                window_hours: float = 1.6) -> bool:
        """
        檢查軌道平面是否可能在時間窗內經過目標經度
        
        Args:
            orbit: 軌道參數
            observer_lon: 觀察者經度 (度)
            window_hours: 分析時間窗 (小時, 默認96分鐘)
            
        Returns:
            True 如果軌道可能經過該經度
        """
        # 計算軌道週期
        mu = 398600.4418  # 地球引力常數 km³/s²
        period_seconds = 2 * math.pi * math.sqrt(orbit.semi_major_axis**3 / mu)
        period_hours = period_seconds / 3600
        
        # 地球自轉速度 (度/小時)
        earth_rotation_rate = 360 / 24  # 15度/小時
        
        # 在分析時間窗內，軌道和地球自轉的相對運動
        relative_longitude_change = window_hours * earth_rotation_rate
        
        # 軌道平面的經度覆蓋範圍
        # 考慮升交點赤經和地球自轉
        raan_longitude = orbit.raan
        
        # 在時間窗內軌道可能覆蓋的經度範圍
        longitude_coverage = relative_longitude_change + 180  # 保守估計
        
        # 計算經度差
        lon_diff = abs(observer_lon - raan_longitude)
        lon_diff = min(lon_diff, 360 - lon_diff)  # 考慮經度環繞
        
        return lon_diff <= longitude_coverage / 2
    
    def check_minimum_distance(self, orbit: OrbitParameters, observer: ObserverLocation) -> bool:
        """
        檢查衛星與觀察者的最小可能距離
        
        Args:
            orbit: 軌道參數
            observer: 觀察者位置
            
        Returns:
            True 如果最小距離允許可見性
        """
        # 觀察者地心距離
        observer_geocentric = self.earth_radius + observer.altitude / 1000
        
        # 衛星軌道半徑
        satellite_radius = orbit.semi_major_axis
        
        # 最小可能距離（衛星和觀察者在同一地心向量上）
        min_distance = abs(satellite_radius - observer_geocentric)
        
        # 最大可能距離（衛星和觀察者在地心相對兩側）
        max_distance = satellite_radius + observer_geocentric
        
        # 檢查是否在合理的通訊距離內（2000km 以內）
        max_communication_distance = 2000  # km
        
        return min_distance <= max_communication_distance
    
    def pre_filter_satellites_by_orbit(self, observer: ObserverLocation, 
                                     all_tle_data: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        軌道幾何預篩選主函數
        
        Args:
            observer: 觀察者位置
            all_tle_data: 所有 TLE 數據
            
        Returns:
            (candidate_satellites, excluded_satellites)
        """
        logger.info(f"開始對 {len(all_tle_data)} 顆衛星進行軌道預篩選...")
        
        candidate_satellites = []
        excluded_satellites = []
        
        filter_statistics = {
            'latitude_coverage_failed': 0,
            'altitude_visibility_failed': 0,
            'longitude_coverage_failed': 0,
            'minimum_distance_failed': 0,
            'orbit_extraction_failed': 0
        }
        
        for i, satellite in enumerate(all_tle_data):
            if i % 500 == 0:
                logger.info(f"預篩選進度: {i}/{len(all_tle_data)}")
            
            try:
                # 提取軌道參數
                orbit = self.extract_orbit_parameters(satellite)
                if orbit is None:
                    filter_statistics['orbit_extraction_failed'] += 1
                    excluded_satellites.append({**satellite, 'exclusion_reason': 'orbit_extraction_failed'})
                    continue
                
                # 一系列預篩選檢查
                if not self.check_latitude_coverage(orbit, observer.latitude):
                    filter_statistics['latitude_coverage_failed'] += 1
                    excluded_satellites.append({**satellite, 'exclusion_reason': 'latitude_coverage_failed'})
                    continue
                
                if not self.check_orbital_altitude_visibility(orbit, observer.latitude):
                    filter_statistics['altitude_visibility_failed'] += 1
                    excluded_satellites.append({**satellite, 'exclusion_reason': 'altitude_visibility_failed'})
                    continue
                
                if not self.check_longitude_coverage(orbit, observer.longitude):
                    filter_statistics['longitude_coverage_failed'] += 1
                    excluded_satellites.append({**satellite, 'exclusion_reason': 'longitude_coverage_failed'})
                    continue
                
                if not self.check_minimum_distance(orbit, observer):
                    filter_statistics['minimum_distance_failed'] += 1
                    excluded_satellites.append({**satellite, 'exclusion_reason': 'minimum_distance_failed'})
                    continue
                
                # 通過所有預篩選條件
                candidate_satellites.append({
                    **satellite, 
                    'orbit_parameters': {
                        'inclination': orbit.inclination,
                        'semi_major_axis': orbit.semi_major_axis,
                        'altitude_km': orbit.semi_major_axis - self.earth_radius
                    }
                })
                
            except Exception as e:
                logger.error(f"預篩選衛星 {satellite['name']} 時發生錯誤: {e}")
                filter_statistics['orbit_extraction_failed'] += 1
                excluded_satellites.append({**satellite, 'exclusion_reason': f'processing_error: {e}'})
        
        # 輸出篩選統計
        total_satellites = len(all_tle_data)
        candidates_count = len(candidate_satellites)
        excluded_count = len(excluded_satellites)
        reduction_ratio = (excluded_count / total_satellites) * 100
        
        logger.info(f"預篩選完成:")
        logger.info(f"  原始衛星數量: {total_satellites}")
        logger.info(f"  候選衛星數量: {candidates_count}")
        logger.info(f"  排除衛星數量: {excluded_count}")
        logger.info(f"  計算量減少: {reduction_ratio:.1f}%")
        
        logger.info(f"篩選統計:")
        for reason, count in filter_statistics.items():
            logger.info(f"  {reason}: {count}")
        
        return candidate_satellites, excluded_satellites


def main():
    """測試預篩選器功能"""
    # 測試位置：NTPU
    observer = ObserverLocation(
        latitude=24.9441667,
        longitude=121.3713889,
        altitude=0
    )
    
    # 創建預篩選器
    prefilter = SatellitePrefilter(min_elevation=5.0)
    
    # 測試軌道參數
    test_orbit = OrbitParameters(
        inclination=53.0,      # Starlink 典型傾角
        semi_major_axis=6921,  # ~550km 高度
        eccentricity=0.0001,   # 近圓軌道
        raan=100.0,
        argument_of_perigee=90.0,
        mean_anomaly=0.0
    )
    
    # 測試各種檢查功能
    print("=== 預篩選器功能測試 ===")
    print(f"緯度覆蓋檢查: {prefilter.check_latitude_coverage(test_orbit, observer.latitude)}")
    print(f"高度可見性檢查: {prefilter.check_orbital_altitude_visibility(test_orbit, observer.latitude)}")
    print(f"經度覆蓋檢查: {prefilter.check_longitude_coverage(test_orbit, observer.longitude)}")
    print(f"最小距離檢查: {prefilter.check_minimum_distance(test_orbit, observer)}")


if __name__ == "__main__":
    main()