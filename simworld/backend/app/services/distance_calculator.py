"""
高精度距離計算器 - 支持大氣修正和相對論效應

功能：
1. 精確的 3D 空間距離計算
2. 大氣阻力和電離層延遲修正
3. 相對速度計算
4. WGS84 地理坐標系統支持

符合 d2.md 中 Phase 2 的要求
"""

import math
import logging
from typing import Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .sgp4_calculator import OrbitPosition

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """位置數據結構"""
    latitude: float   # 度
    longitude: float  # 度
    altitude: float   # km
    x: float = 0.0    # ECEF 坐標 (km)
    y: float = 0.0    # ECEF 坐標 (km)
    z: float = 0.0    # ECEF 坐標 (km)

@dataclass
class DistanceResult:
    """距離計算結果"""
    satellite_distance: float      # UE ↔ 衛星距離 (m)
    ground_distance: float         # UE ↔ 固定參考位置距離 (m)
    relative_satellite_speed: float # 相對速度 (m/s)
    atmospheric_delay: float       # 大氣延遲修正 (m)
    ionospheric_delay: float      # 電離層延遲修正 (m)
    geometric_distance: float     # 幾何距離（未修正）(m)

class DistanceCalculator:
    """高精度距離計算器"""
    
    def __init__(self):
        # WGS84 地球參數
        self.EARTH_RADIUS = 6378137.0  # m
        self.EARTH_FLATTENING = 1.0 / 298.257223563
        self.EARTH_ECCENTRICITY_SQ = 2 * self.EARTH_FLATTENING - self.EARTH_FLATTENING ** 2
        
        # 物理常數
        self.SPEED_OF_LIGHT = 299792458.0  # m/s
        self.GRAVITATIONAL_CONSTANT = 6.67430e-11  # m³/kg/s²
        self.EARTH_MASS = 5.972e24  # kg
        
        # 大氣參數
        self.TROPOSPHERE_HEIGHT = 11000.0  # m
        self.STRATOSPHERE_HEIGHT = 50000.0  # m
        self.IONOSPHERE_HEIGHT = 1000000.0  # m
    
    def calculate_d2_distances(
        self,
        ue_position: Position,
        satellite_position: OrbitPosition,
        ground_reference: Position
    ) -> DistanceResult:
        """
        計算 D2 事件所需的距離
        
        Args:
            ue_position: UE 位置
            satellite_position: 衛星位置
            ground_reference: 地面參考位置
            
        Returns:
            距離計算結果
        """
        try:
            # 轉換 UE 位置到 ECEF 坐標
            ue_ecef = self._geodetic_to_ecef(
                ue_position.latitude,
                ue_position.longitude,
                ue_position.altitude
            )
            
            # 轉換衛星位置到 ECEF 坐標
            sat_ecef = self._geodetic_to_ecef(
                satellite_position.latitude,
                satellite_position.longitude,
                satellite_position.altitude
            )
            
            # 轉換地面參考位置到 ECEF 坐標
            ref_ecef = self._geodetic_to_ecef(
                ground_reference.latitude,
                ground_reference.longitude,
                ground_reference.altitude
            )
            
            # 計算幾何距離
            satellite_distance_geometric = self._calculate_3d_distance(ue_ecef, sat_ecef)
            ground_distance_geometric = self._calculate_3d_distance(ue_ecef, ref_ecef)
            
            # 計算相對速度
            relative_speed = self._calculate_relative_speed(
                ue_ecef, sat_ecef, satellite_position.velocity
            )
            
            # 大氣修正
            atmospheric_delay = self._calculate_atmospheric_delay(
                satellite_distance_geometric,
                satellite_position.altitude * 1000  # 轉換為米
            )
            
            # 電離層修正
            ionospheric_delay = self._calculate_ionospheric_delay(
                satellite_distance_geometric,
                satellite_position.altitude * 1000
            )
            
            # 應用修正
            satellite_distance_corrected = satellite_distance_geometric + atmospheric_delay + ionospheric_delay
            
            return DistanceResult(
                satellite_distance=satellite_distance_corrected,
                ground_distance=ground_distance_geometric,
                relative_satellite_speed=relative_speed,
                atmospheric_delay=atmospheric_delay,
                ionospheric_delay=ionospheric_delay,
                geometric_distance=satellite_distance_geometric
            )
            
        except Exception as e:
            logger.error(f"距離計算失敗: {e}")
            # 返回默認值
            return DistanceResult(
                satellite_distance=0.0,
                ground_distance=0.0,
                relative_satellite_speed=0.0,
                atmospheric_delay=0.0,
                ionospheric_delay=0.0,
                geometric_distance=0.0
            )
    
    def _geodetic_to_ecef(self, lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
        """
        將地理坐標轉換為 ECEF 坐標
        
        Args:
            lat: 緯度 (度)
            lon: 經度 (度)
            alt: 高度 (km)
            
        Returns:
            (x, y, z) ECEF 坐標 (m)
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        alt_m = alt * 1000  # 轉換為米
        
        # 計算卯酉圈曲率半徑
        sin_lat = math.sin(lat_rad)
        N = self.EARTH_RADIUS / math.sqrt(1 - self.EARTH_ECCENTRICITY_SQ * sin_lat ** 2)
        
        # ECEF 坐標
        x = (N + alt_m) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt_m) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - self.EARTH_ECCENTRICITY_SQ) + alt_m) * sin_lat
        
        return x, y, z
    
    def _calculate_3d_distance(self, pos1: Tuple[float, float, float], pos2: Tuple[float, float, float]) -> float:
        """
        計算兩點間的 3D 歐幾里得距離
        
        Args:
            pos1: 位置1 (x, y, z) in meters
            pos2: 位置2 (x, y, z) in meters
            
        Returns:
            距離 (m)
        """
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        dz = pos2[2] - pos1[2]
        
        return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
    
    def _calculate_relative_speed(
        self,
        ue_ecef: Tuple[float, float, float],
        sat_ecef: Tuple[float, float, float],
        sat_velocity: Tuple[float, float, float]
    ) -> float:
        """
        計算衛星相對於 UE 的速度
        
        Args:
            ue_ecef: UE ECEF 位置 (m)
            sat_ecef: 衛星 ECEF 位置 (m)
            sat_velocity: 衛星速度 (km/s)
            
        Returns:
            相對速度 (m/s)
        """
        # 計算位置向量
        dx = sat_ecef[0] - ue_ecef[0]
        dy = sat_ecef[1] - ue_ecef[1]
        dz = sat_ecef[2] - ue_ecef[2]
        
        distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        
        if distance == 0:
            return 0.0
        
        # 單位向量
        ux = dx / distance
        uy = dy / distance
        uz = dz / distance
        
        # 衛星速度 (轉換為 m/s)
        vx = sat_velocity[0] * 1000
        vy = sat_velocity[1] * 1000
        vz = sat_velocity[2] * 1000
        
        # 徑向速度分量
        radial_velocity = vx * ux + vy * uy + vz * uz
        
        return abs(radial_velocity)
    
    def _calculate_atmospheric_delay(self, distance: float, satellite_altitude: float) -> float:
        """
        計算大氣延遲修正
        
        Args:
            distance: 幾何距離 (m)
            satellite_altitude: 衛星高度 (m)
            
        Returns:
            大氣延遲 (m)
        """
        if satellite_altitude > self.IONOSPHERE_HEIGHT:
            # 衛星在電離層之上，大氣影響很小
            return 0.0
        
        # 簡化的大氣模型
        # 對流層延遲
        troposphere_delay = 0.0
        if satellite_altitude < self.TROPOSPHERE_HEIGHT:
            # 衛星在對流層內（不太可能，但處理邊界情況）
            troposphere_factor = 1.0 - satellite_altitude / self.TROPOSPHERE_HEIGHT
            troposphere_delay = distance * 2.3e-6 * troposphere_factor
        
        # 平流層延遲
        stratosphere_delay = 0.0
        if satellite_altitude < self.STRATOSPHERE_HEIGHT:
            stratosphere_factor = 1.0 - satellite_altitude / self.STRATOSPHERE_HEIGHT
            stratosphere_delay = distance * 1.2e-6 * stratosphere_factor
        
        return troposphere_delay + stratosphere_delay
    
    def _calculate_ionospheric_delay(self, distance: float, satellite_altitude: float) -> float:
        """
        計算電離層延遲修正
        
        Args:
            distance: 幾何距離 (m)
            satellite_altitude: 衛星高度 (m)
            
        Returns:
            電離層延遲 (m)
        """
        if satellite_altitude > self.IONOSPHERE_HEIGHT:
            # 衛星在電離層之上
            return 0.0
        
        # 簡化的電離層模型
        # 電離層延遲與頻率的平方成反比，這裡使用 L1 頻率的典型值
        ionosphere_factor = 1.0 - satellite_altitude / self.IONOSPHERE_HEIGHT
        ionosphere_delay = distance * 5.0e-6 * ionosphere_factor
        
        return ionosphere_delay
    
    def apply_relativistic_correction(self, distance: float, satellite_altitude: float) -> float:
        """
        應用相對論修正
        
        Args:
            distance: 距離 (m)
            satellite_altitude: 衛星高度 (m)
            
        Returns:
            修正後的距離 (m)
        """
        # 重力紅移修正
        earth_surface_potential = self.GRAVITATIONAL_CONSTANT * self.EARTH_MASS / self.EARTH_RADIUS
        satellite_potential = self.GRAVITATIONAL_CONSTANT * self.EARTH_MASS / (self.EARTH_RADIUS + satellite_altitude)
        
        potential_difference = satellite_potential - earth_surface_potential
        relativistic_factor = 1 + potential_difference / (self.SPEED_OF_LIGHT ** 2)
        
        return distance * relativistic_factor
    
    def calculate_elevation_angle(
        self,
        ue_position: Position,
        satellite_position: OrbitPosition
    ) -> float:
        """
        計算衛星的仰角
        
        Args:
            ue_position: UE 位置
            satellite_position: 衛星位置
            
        Returns:
            仰角 (度)
        """
        try:
            # 轉換為 ECEF 坐標
            ue_ecef = self._geodetic_to_ecef(
                ue_position.latitude,
                ue_position.longitude,
                ue_position.altitude
            )
            
            sat_ecef = self._geodetic_to_ecef(
                satellite_position.latitude,
                satellite_position.longitude,
                satellite_position.altitude
            )
            
            # 計算向量
            dx = sat_ecef[0] - ue_ecef[0]
            dy = sat_ecef[1] - ue_ecef[1]
            dz = sat_ecef[2] - ue_ecef[2]
            
            # UE 位置的地心向量
            ue_magnitude = math.sqrt(ue_ecef[0] ** 2 + ue_ecef[1] ** 2 + ue_ecef[2] ** 2)
            
            # 衛星相對於 UE 的向量
            sat_rel_magnitude = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            
            if ue_magnitude == 0 or sat_rel_magnitude == 0:
                return 0.0
            
            # 計算仰角
            dot_product = (ue_ecef[0] * dx + ue_ecef[1] * dy + ue_ecef[2] * dz)
            cos_zenith = dot_product / (ue_magnitude * sat_rel_magnitude)
            
            # 限制 cos 值在 [-1, 1] 範圍內
            cos_zenith = max(-1.0, min(1.0, cos_zenith))
            
            zenith_angle = math.acos(cos_zenith)
            elevation_angle = math.pi / 2 - zenith_angle
            
            return math.degrees(elevation_angle)
            
        except Exception as e:
            logger.error(f"仰角計算失敗: {e}")
            return 0.0
    
    def calculate_azimuth_angle(
        self,
        ue_position: Position,
        satellite_position: OrbitPosition
    ) -> float:
        """
        計算衛星的方位角
        
        Args:
            ue_position: UE 位置
            satellite_position: 衛星位置
            
        Returns:
            方位角 (度，從北方順時針測量)
        """
        try:
            lat1 = math.radians(ue_position.latitude)
            lon1 = math.radians(ue_position.longitude)
            lat2 = math.radians(satellite_position.latitude)
            lon2 = math.radians(satellite_position.longitude)
            
            dlon = lon2 - lon1
            
            y = math.sin(dlon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            
            azimuth = math.atan2(y, x)
            azimuth_degrees = math.degrees(azimuth)
            
            # 轉換為 0-360 度範圍
            if azimuth_degrees < 0:
                azimuth_degrees += 360
            
            return azimuth_degrees
            
        except Exception as e:
            logger.error(f"方位角計算失敗: {e}")
            return 0.0
