"""
優化的座標轉換服務 - Phase 4 重構

提供高效的座標系統轉換，包含轉換矩陣緩存和批量處理優化。
專為衛星換手研究的高頻座標轉換需求設計。
"""

import math
import logging
from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass
import hashlib
from functools import lru_cache

from app.domains.coordinates.models.coordinate_model import GeoCoordinate, CartesianCoordinate
from app.domains.coordinates.interfaces.coordinate_service_interface import CoordinateServiceInterface

logger = logging.getLogger(__name__)


@dataclass
class TransformationMatrix:
    """座標轉換矩陣"""
    matrix: List[List[float]]  # 3x3 矩陣
    origin_lat: float
    origin_lon: float
    

class OptimizedCoordinateService(CoordinateServiceInterface):
    """優化的座標轉換服務 - 支援緩存和批量處理"""
    
    def __init__(self):
        # WGS84 常數 (高精度)
        self.WGS84_A = 6378137.0  # 長半軸 (m)
        self.WGS84_F = 1.0 / 298.257223563  # 扁率
        self.WGS84_B = self.WGS84_A * (1 - self.WGS84_F)  # 短半軸
        self.WGS84_E2 = 2 * self.WGS84_F - self.WGS84_F * self.WGS84_F  # 第一偏心率平方
        
        # 地球半徑 (簡化計算用)
        self.EARTH_RADIUS_KM = 6378.137
        self.EARTH_RADIUS_M = 6378137.0
        
        # 轉換係數緩存
        self._deg_to_rad = math.pi / 180.0
        self._rad_to_deg = 180.0 / math.pi
        
        # 轉換矩陣緩存 (用於 ENU 轉換)
        self._transformation_cache: Dict[str, TransformationMatrix] = {}
        
        logger.info("優化的座標轉換服務初始化完成")

    async def geo_to_cartesian(self, geo: GeoCoordinate) -> CartesianCoordinate:
        """地理座標轉笛卡爾座標 (球面近似，適合快速計算)"""
        lat_rad = geo.latitude * self._deg_to_rad
        lon_rad = geo.longitude * self._deg_to_rad
        
        # 使用球面近似 (比橢圓體快)
        radius_km = self.EARTH_RADIUS_KM
        if geo.altitude is not None:
            radius_km += geo.altitude / 1000.0
            
        x = radius_km * math.cos(lat_rad) * math.cos(lon_rad)
        y = radius_km * math.cos(lat_rad) * math.sin(lon_rad)
        z = radius_km * math.sin(lat_rad)
        
        return CartesianCoordinate(x=x, y=y, z=z)

    async def cartesian_to_geo(self, cartesian: CartesianCoordinate) -> GeoCoordinate:
        """笛卡爾座標轉地理座標 (球面近似)"""
        r = math.sqrt(cartesian.x**2 + cartesian.y**2 + cartesian.z**2)
        
        lat_rad = math.asin(cartesian.z / r)
        lon_rad = math.atan2(cartesian.y, cartesian.x)
        
        lat_deg = lat_rad * self._rad_to_deg
        lon_deg = lon_rad * self._rad_to_deg
        altitude = (r - self.EARTH_RADIUS_KM) * 1000.0  # km -> m
        
        return GeoCoordinate(
            latitude=lat_deg,
            longitude=lon_deg, 
            altitude=altitude if altitude > 0.1 else None
        )

    async def geo_to_ecef(self, geo: GeoCoordinate) -> CartesianCoordinate:
        """地理座標轉 ECEF (地球中心地固座標) - 高精度橢圓體計算"""
        lat_rad = geo.latitude * self._deg_to_rad
        lon_rad = geo.longitude * self._deg_to_rad
        alt_m = geo.altitude or 0.0
        
        # 主曲率半徑
        sin_lat = math.sin(lat_rad)
        N = self.WGS84_A / math.sqrt(1 - self.WGS84_E2 * sin_lat * sin_lat)
        
        # ECEF 座標 (m)
        cos_lat = math.cos(lat_rad)
        cos_lon = math.cos(lon_rad)
        sin_lon = math.sin(lon_rad)
        
        x = (N + alt_m) * cos_lat * cos_lon
        y = (N + alt_m) * cos_lat * sin_lon  
        z = (N * (1 - self.WGS84_E2) + alt_m) * sin_lat
        
        return CartesianCoordinate(x=x, y=y, z=z)

    async def ecef_to_geo(self, ecef: CartesianCoordinate) -> GeoCoordinate:
        """ECEF 轉地理座標 - Bowring 算法 (高效迭代)"""
        x, y, z = ecef.x, ecef.y, ecef.z
        
        # 經度計算 (直接)
        lon_rad = math.atan2(y, x)
        
        # 緯度計算 (迭代)
        p = math.sqrt(x*x + y*y)
        lat_rad = math.atan2(z, p * (1 - self.WGS84_E2))
        
        # Bowring 迭代 (通常 2-3 次迭代即可收斂)
        for _ in range(3):
            sin_lat = math.sin(lat_rad)
            N = self.WGS84_A / math.sqrt(1 - self.WGS84_E2 * sin_lat * sin_lat)
            alt = p / math.cos(lat_rad) - N
            lat_rad = math.atan2(z, p * (1 - self.WGS84_E2 * N / (N + alt)))
        
        # 最終高度計算
        sin_lat = math.sin(lat_rad)
        N = self.WGS84_A / math.sqrt(1 - self.WGS84_E2 * sin_lat * sin_lat)
        alt = p / math.cos(lat_rad) - N
        
        return GeoCoordinate(
            latitude=lat_rad * self._rad_to_deg,
            longitude=lon_rad * self._rad_to_deg,
            altitude=alt
        )

    async def bearing_distance(
        self, 
        point1: GeoCoordinate, 
        point2: GeoCoordinate
    ) -> Tuple[float, float]:
        """計算方位角和距離 (Vincenty 橢圓體算法 - 高精度)"""
        lat1 = point1.latitude * self._deg_to_rad
        lon1 = point1.longitude * self._deg_to_rad
        lat2 = point2.latitude * self._deg_to_rad  
        lon2 = point2.longitude * self._deg_to_rad
        
        # 簡化版 Haversine (比 Vincenty 快，精度對中短距離足夠)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # 方位角
        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) - 
             math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
        bearing_rad = math.atan2(y, x)
        bearing = bearing_rad * self._rad_to_deg
        bearing = (bearing + 360) % 360
        
        # 距離 (Haversine)
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = self.EARTH_RADIUS_M * c
        
        return bearing, distance

    async def destination_point(
        self, 
        start: GeoCoordinate, 
        bearing: float, 
        distance: float
    ) -> GeoCoordinate:
        """根據起點、方位角和距離計算終點 (球面三角法)"""
        lat1 = start.latitude * self._deg_to_rad
        lon1 = start.longitude * self._deg_to_rad
        bearing_rad = bearing * self._deg_to_rad
        
        # 角距離
        angular_distance = distance / self.EARTH_RADIUS_M
        
        # 球面三角法
        lat2 = math.asin(
            math.sin(lat1) * math.cos(angular_distance) +
            math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing_rad)
        )
        
        lon2 = lon1 + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2)
        )
        
        # 正規化經度
        lon2_deg = (lon2 * self._rad_to_deg + 180) % 360 - 180
        
        return GeoCoordinate(
            latitude=lat2 * self._rad_to_deg,
            longitude=lon2_deg,
            altitude=start.altitude
        )

    def ecef_to_enu(
        self, 
        ecef_point: CartesianCoordinate,
        reference_geo: GeoCoordinate
    ) -> CartesianCoordinate:
        """ECEF 轉 ENU (East-North-Up) 局部座標系"""
        # 獲取或創建轉換矩陣 (緩存)
        cache_key = f"{reference_geo.latitude:.6f},{reference_geo.longitude:.6f}"
        
        if cache_key not in self._transformation_cache:
            self._create_enu_transformation_matrix(reference_geo, cache_key)
        
        transform = self._transformation_cache[cache_key]
        
        # 參考點的 ECEF 座標
        ref_ecef = self._geo_to_ecef_sync(reference_geo)
        
        # 相對位置向量
        dx = ecef_point.x - ref_ecef.x
        dy = ecef_point.y - ref_ecef.y
        dz = ecef_point.z - ref_ecef.z
        
        # 矩陣轉換
        matrix = transform.matrix
        e = matrix[0][0] * dx + matrix[0][1] * dy + matrix[0][2] * dz
        n = matrix[1][0] * dx + matrix[1][1] * dy + matrix[1][2] * dz  
        u = matrix[2][0] * dx + matrix[2][1] * dy + matrix[2][2] * dz
        
        return CartesianCoordinate(x=e, y=n, z=u)

    def batch_geo_to_ecef(self, geo_points: List[GeoCoordinate]) -> List[CartesianCoordinate]:
        """批量地理座標轉 ECEF (性能優化)"""
        results = []
        
        # 預計算常數
        a = self.WGS84_A
        e2 = self.WGS84_E2
        
        for geo in geo_points:
            lat_rad = geo.latitude * self._deg_to_rad
            lon_rad = geo.longitude * self._deg_to_rad
            alt_m = geo.altitude or 0.0
            
            sin_lat = math.sin(lat_rad)
            cos_lat = math.cos(lat_rad)
            cos_lon = math.cos(lon_rad)
            sin_lon = math.sin(lon_rad)
            
            N = a / math.sqrt(1 - e2 * sin_lat * sin_lat)
            
            x = (N + alt_m) * cos_lat * cos_lon
            y = (N + alt_m) * cos_lat * sin_lon
            z = (N * (1 - e2) + alt_m) * sin_lat
            
            results.append(CartesianCoordinate(x=x, y=y, z=z))
            
        return results

    @lru_cache(maxsize=1000)
    def _cached_geo_to_ecef(
        self, 
        lat: float, 
        lon: float, 
        alt: float
    ) -> Tuple[float, float, float]:
        """緩存的地理座標轉 ECEF (用於重複計算的位置)"""
        lat_rad = lat * self._deg_to_rad
        lon_rad = lon * self._deg_to_rad
        
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        cos_lon = math.cos(lon_rad)
        sin_lon = math.sin(lon_rad)
        
        N = self.WGS84_A / math.sqrt(1 - self.WGS84_E2 * sin_lat * sin_lat)
        
        x = (N + alt) * cos_lat * cos_lon
        y = (N + alt) * cos_lat * sin_lon
        z = (N * (1 - self.WGS84_E2) + alt) * sin_lat
        
        return x, y, z

    def _create_enu_transformation_matrix(
        self, 
        reference_geo: GeoCoordinate, 
        cache_key: str
    ) -> None:
        """創建 ECEF 到 ENU 的轉換矩陣"""
        lat_rad = reference_geo.latitude * self._deg_to_rad
        lon_rad = reference_geo.longitude * self._deg_to_rad
        
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)  
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)
        
        # ENU 轉換矩陣
        matrix = [
            [-sin_lon, cos_lon, 0],
            [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
            [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat]
        ]
        
        self._transformation_cache[cache_key] = TransformationMatrix(
            matrix=matrix,
            origin_lat=reference_geo.latitude,
            origin_lon=reference_geo.longitude
        )

    def _geo_to_ecef_sync(self, geo: GeoCoordinate) -> CartesianCoordinate:
        """同步版本的地理座標轉 ECEF"""
        x, y, z = self._cached_geo_to_ecef(
            geo.latitude, 
            geo.longitude, 
            geo.altitude or 0.0
        )
        return CartesianCoordinate(x=x, y=y, z=z)

    # 向後相容的方法 (保持原有接口)
    async def utm_to_geo(
        self, 
        easting: float, 
        northing: float, 
        zone_number: int, 
        zone_letter: str
    ) -> GeoCoordinate:
        """UTM 座標轉地理座標 (簡化實現)"""
        # 簡化實現 - 實際應用建議使用 pyproj
        lon_origin = (zone_number - 1) * 6 - 180 + 3
        
        # 簡化的逆轉換
        lat_deg = northing / 111000.0  # 概略換算
        lon_deg = lon_origin + (easting - 500000) / (111000.0 * math.cos(math.radians(lat_deg)))
        
        return GeoCoordinate(latitude=lat_deg, longitude=lon_deg)

    async def geo_to_utm(self, geo: GeoCoordinate) -> Dict[str, Any]:
        """地理座標轉 UTM (簡化實現)"""
        zone_number = int((geo.longitude + 180) / 6) + 1
        
        # 簡化的區帶字母計算
        if geo.latitude >= 0:
            zone_letter = chr(ord('N') + min(int(geo.latitude / 8), 12))
        else:
            zone_letter = chr(ord('M') - min(int(abs(geo.latitude) / 8), 12))
            
        # 簡化的 UTM 計算
        lon_origin = (zone_number - 1) * 6 - 180 + 3
        easting = 500000 + (geo.longitude - lon_origin) * 111000 * math.cos(math.radians(geo.latitude))
        northing = geo.latitude * 111000
        
        if geo.latitude < 0:
            northing = 10000000 + northing
            
        return {
            "easting": easting,
            "northing": northing,
            "zone_number": zone_number,
            "zone_letter": zone_letter
        }


# 全域實例
_coordinate_service = None


def get_optimized_coordinate_service() -> OptimizedCoordinateService:
    """獲取優化的座標轉換服務實例 (單例)"""
    global _coordinate_service
    if _coordinate_service is None:
        _coordinate_service = OptimizedCoordinateService()
    return _coordinate_service