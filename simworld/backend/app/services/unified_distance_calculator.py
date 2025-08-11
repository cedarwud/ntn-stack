"""
統一距離計算服務 - Phase 4 重構

整合原有的多個距離計算邏輯，提供高效統一的計算接口。
支援衛星換手研究所需的所有距離和角度計算。
"""

import math
import logging
from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Position3D:
    """統一的 3D 位置數據結構"""
    latitude: float   # 度
    longitude: float  # 度
    altitude: float   # km
    # ECEF 坐標 (km)
    x: Optional[float] = None    
    y: Optional[float] = None    
    z: Optional[float] = None    
    # 速度向量 (km/s)
    velocity: Optional[Tuple[float, float, float]] = None


@dataclass
class DistanceResult:
    """完整的距離計算結果"""
    # 基本距離 (m)
    distance_m: float
    # 幾何距離 (未修正) (m)
    geometric_distance_m: float  
    # 仰角 (度)
    elevation_deg: float
    # 方位角 (度)
    azimuth_deg: float  
    # 相對速度 (m/s)
    relative_speed_ms: float
    # 大氣延遲修正 (m) - 可選
    atmospheric_delay_m: Optional[float] = None
    # 電離層延遲修正 (m) - 可選  
    ionospheric_delay_m: Optional[float] = None


class UnifiedDistanceCalculator:
    """統一距離計算服務 - 支援所有衛星換手相關計算"""
    
    def __init__(self):
        # WGS84 地球參數 (高精度)
        self.EARTH_RADIUS_M = 6378137.0  # m
        self.EARTH_RADIUS_KM = 6378.137  # km
        self.EARTH_FLATTENING = 1.0 / 298.257223563
        self.EARTH_ECCENTRICITY_SQ = 2 * self.EARTH_FLATTENING - self.EARTH_FLATTENING ** 2
        
        # 物理常數
        self.SPEED_OF_LIGHT = 299792458.0  # m/s
        
        # 大氣參數 (用於修正)
        self.TROPOSPHERE_HEIGHT = 11000.0  # m
        self.IONOSPHERE_HEIGHT = 1000000.0  # m
        
        # 預計算的轉換係數
        self._deg_to_rad = math.pi / 180.0
        self._rad_to_deg = 180.0 / math.pi
        
        logger.info("統一距離計算器初始化完成")

    def calculate_satellite_distance(
        self, 
        observer: Position3D, 
        satellite: Position3D,
        include_corrections: bool = False
    ) -> DistanceResult:
        """
        計算觀測者到衛星的完整距離信息
        
        Args:
            observer: 觀測者位置  
            satellite: 衛星位置
            include_corrections: 是否包含大氣修正
            
        Returns:
            完整的距離計算結果
        """
        # 確保 ECEF 坐標可用
        obs_ecef = self._ensure_ecef(observer)
        sat_ecef = self._ensure_ecef(satellite)
        
        # 計算基本幾何距離
        dx = sat_ecef.x - obs_ecef.x  # km
        dy = sat_ecef.y - obs_ecef.y  # km  
        dz = sat_ecef.z - obs_ecef.z  # km
        
        geometric_distance_km = math.sqrt(dx*dx + dy*dy + dz*dz)
        geometric_distance_m = geometric_distance_km * 1000.0
        
        # 計算仰角和方位角
        elevation_deg, azimuth_deg = self._calculate_elevation_azimuth(
            obs_ecef, sat_ecef
        )
        
        # 計算相對速度
        relative_speed_ms = 0.0
        if observer.velocity and satellite.velocity:
            relative_speed_ms = self._calculate_relative_speed(
                observer.velocity, satellite.velocity
            )
        
        # 基礎距離 (幾何距離)  
        distance_m = geometric_distance_m
        
        # 大氣修正 (如果需要)
        atmospheric_delay_m = None
        ionospheric_delay_m = None
        
        if include_corrections:
            atmospheric_delay_m = self._calculate_atmospheric_delay(
                elevation_deg, geometric_distance_km
            )
            ionospheric_delay_m = self._calculate_ionospheric_delay(
                elevation_deg, satellite.altitude
            )
            
            # 應用修正
            distance_m += (atmospheric_delay_m or 0) + (ionospheric_delay_m or 0)
        
        return DistanceResult(
            distance_m=distance_m,
            geometric_distance_m=geometric_distance_m,
            elevation_deg=elevation_deg,
            azimuth_deg=azimuth_deg,
            relative_speed_ms=relative_speed_ms,
            atmospheric_delay_m=atmospheric_delay_m,
            ionospheric_delay_m=ionospheric_delay_m
        )

    def calculate_great_circle_distance(
        self, 
        point1: Position3D, 
        point2: Position3D
    ) -> float:
        """
        計算球面大圓距離 (Haversine公式)
        
        Args:
            point1: 第一個點
            point2: 第二個點
            
        Returns:
            距離 (米)
        """
        lat1_rad = point1.latitude * self._deg_to_rad
        lon1_rad = point1.longitude * self._deg_to_rad
        lat2_rad = point2.latitude * self._deg_to_rad  
        lon2_rad = point2.longitude * self._deg_to_rad
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return self.EARTH_RADIUS_M * c

    def calculate_elevation_angle(
        self, 
        observer: Position3D, 
        target: Position3D
    ) -> float:
        """
        計算目標相對於觀測者的仰角
        
        Args:
            observer: 觀測者位置
            target: 目標位置
            
        Returns:
            仰角 (度)
        """
        obs_ecef = self._ensure_ecef(observer)
        tgt_ecef = self._ensure_ecef(target)
        
        elevation_deg, _ = self._calculate_elevation_azimuth(obs_ecef, tgt_ecef)
        return elevation_deg

    def batch_calculate_distances(
        self, 
        observer: Position3D, 
        targets: List[Position3D],
        include_corrections: bool = False
    ) -> List[DistanceResult]:
        """
        批量計算多個目標的距離 (性能優化)
        
        Args:
            observer: 觀測者位置
            targets: 目標位置列表  
            include_corrections: 是否包含大氣修正
            
        Returns:
            距離計算結果列表
        """
        # 預先計算觀測者 ECEF 坐標
        obs_ecef = self._ensure_ecef(observer)
        
        results = []
        for target in targets:
            result = self.calculate_satellite_distance(
                observer, target, include_corrections
            )
            results.append(result)
            
        return results

    def _ensure_ecef(self, position: Position3D) -> Position3D:
        """確保位置包含 ECEF 坐標，如果沒有則計算"""
        if position.x is not None and position.y is not None and position.z is not None:
            return position
            
        # 計算 ECEF 坐標
        lat_rad = position.latitude * self._deg_to_rad
        lon_rad = position.longitude * self._deg_to_rad
        alt_m = position.altitude * 1000.0  # km -> m
        
        # WGS84 橢圓體參數
        a = self.EARTH_RADIUS_M
        e2 = self.EARTH_ECCENTRICITY_SQ
        
        # 計算主曲率半徑
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad)**2)
        
        # ECEF 坐標 (m -> km)
        x = (N + alt_m) * math.cos(lat_rad) * math.cos(lon_rad) / 1000.0
        y = (N + alt_m) * math.cos(lat_rad) * math.sin(lon_rad) / 1000.0
        z = (N * (1 - e2) + alt_m) * math.sin(lat_rad) / 1000.0
        
        # 創建新的位置物件 (保留原有數據)
        return Position3D(
            latitude=position.latitude,
            longitude=position.longitude,
            altitude=position.altitude,
            x=x, y=y, z=z,
            velocity=position.velocity
        )

    def _calculate_elevation_azimuth(
        self, 
        observer: Position3D, 
        target: Position3D
    ) -> Tuple[float, float]:
        """計算仰角和方位角"""
        # 從觀測者指向目標的向量 (km)
        dx = target.x - observer.x
        dy = target.y - observer.y  
        dz = target.z - observer.z
        
        # 轉換到 ENU (East-North-Up) 局部座標系
        lat_rad = observer.latitude * self._deg_to_rad
        lon_rad = observer.longitude * self._deg_to_rad
        
        # 旋轉矩陣 ECEF -> ENU
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)
        
        # ENU 坐標
        e = -sin_lon * dx + cos_lon * dy
        n = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
        u = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
        
        # 計算仰角和方位角
        distance_horizontal = math.sqrt(e*e + n*n)
        
        # 仰角 (度)
        elevation_deg = math.atan2(u, distance_horizontal) * self._rad_to_deg
        
        # 方位角 (度, 從北向順時針)
        azimuth_deg = math.atan2(e, n) * self._rad_to_deg
        if azimuth_deg < 0:
            azimuth_deg += 360
            
        return elevation_deg, azimuth_deg

    def _calculate_relative_speed(
        self, 
        vel1: Tuple[float, float, float], 
        vel2: Tuple[float, float, float]
    ) -> float:
        """計算相對速度大小"""
        dvx = vel2[0] - vel1[0]  # km/s
        dvy = vel2[1] - vel1[1]  # km/s  
        dvz = vel2[2] - vel1[2]  # km/s
        
        relative_speed_kms = math.sqrt(dvx*dvx + dvy*dvy + dvz*dvz)
        return relative_speed_kms * 1000.0  # km/s -> m/s

    def _calculate_atmospheric_delay(
        self, 
        elevation_deg: float, 
        distance_km: float
    ) -> float:
        """計算大氣延遲修正 (簡化模型)"""
        if elevation_deg <= 0:
            return 0.0
            
        # 簡化的對流層延遲模型
        elevation_rad = elevation_deg * self._deg_to_rad
        zenith_delay = 2.3  # m (標準大氣條件)
        
        # 映射函數 (簡化)
        mapping_factor = 1.0 / math.sin(elevation_rad)
        if mapping_factor > 10.0:  # 限制低仰角影響
            mapping_factor = 10.0
            
        return zenith_delay * mapping_factor

    def _calculate_ionospheric_delay(
        self, 
        elevation_deg: float, 
        satellite_altitude_km: float
    ) -> float:
        """計算電離層延遲修正 (簡化模型)"""
        if elevation_deg <= 0 or satellite_altitude_km < 200:
            return 0.0
            
        # 簡化的電離層延遲模型 (頻率相關)
        elevation_rad = elevation_deg * self._deg_to_rad
        zenith_ionospheric_delay = 5.0  # m (標準條件，L1頻率)
        
        # 映射函數
        mapping_factor = 1.0 / math.cos(
            math.asin(
                self.EARTH_RADIUS_KM * math.sin(math.pi/2 - elevation_rad) / 
                (self.EARTH_RADIUS_KM + 350)  # 電離層高度約350km
            )
        )
        
        return zenith_ionospheric_delay * mapping_factor


# 全域實例 (單例模式)
_distance_calculator = None


def get_unified_distance_calculator() -> UnifiedDistanceCalculator:
    """獲取統一距離計算器實例 (單例)"""
    global _distance_calculator
    if _distance_calculator is None:
        _distance_calculator = UnifiedDistanceCalculator()
    return _distance_calculator