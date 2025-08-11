from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional

from app.domains.coordinates.models.coordinate_model import (
    GeoCoordinate,
    CartesianCoordinate,
)


class CoordinateServiceInterface(ABC):
    """座標轉換服務介面"""

    @abstractmethod
    async def geo_to_cartesian(self, geo: GeoCoordinate) -> CartesianCoordinate:
        """將地理座標轉換為笛卡爾座標"""
        pass

    @abstractmethod
    async def cartesian_to_geo(self, cartesian: CartesianCoordinate) -> GeoCoordinate:
        """將笛卡爾座標轉換為地理座標"""
        pass

    @abstractmethod
    async def geo_to_ecef(self, geo: GeoCoordinate) -> CartesianCoordinate:
        """將地理座標轉換為地球中心地固座標 (ECEF)"""
        pass

    @abstractmethod
    async def ecef_to_geo(self, ecef: CartesianCoordinate) -> GeoCoordinate:
        """將地球中心地固座標 (ECEF) 轉換為地理座標"""
        pass

    @abstractmethod
    async def bearing_distance(
        self, point1: GeoCoordinate, point2: GeoCoordinate
    ) -> Tuple[float, float]:
        """計算兩點間的方位角和距離"""
        pass

    @abstractmethod
    async def destination_point(
        self, start: GeoCoordinate, bearing: float, distance: float
    ) -> GeoCoordinate:
        """根據起點、方位角和距離計算終點座標"""
        pass

    @abstractmethod
    async def utm_to_geo(
        self, easting: float, northing: float, zone_number: int, zone_letter: str
    ) -> GeoCoordinate:
        """將 UTM 座標轉換為地理座標"""
        pass

    @abstractmethod
    async def geo_to_utm(self, geo: GeoCoordinate) -> Dict[str, Any]:
        """將地理座標轉換為 UTM 座標"""
        pass
