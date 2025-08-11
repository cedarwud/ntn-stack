from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domains.coordinates.models.coordinate_model import GeoCoordinate
from app.domains.satellite.models.satellite_model import (
    OrbitPropagationResult,
    SatellitePass,
)


class OrbitServiceInterface(ABC):
    """軌道服務接口"""

    @abstractmethod
    async def propagate_orbit(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
    ) -> OrbitPropagationResult:
        """計算衛星軌道傳播，返回在指定時間段內的軌道點"""
        pass

    @abstractmethod
    async def calculate_passes(
        self,
        satellite_id: int,
        observer_location: GeoCoordinate,
        start_time: datetime,
        end_time: datetime,
        min_elevation: float = 10.0,
    ) -> List[SatellitePass]:
        """計算衛星過境情況"""
        pass

    @abstractmethod
    async def get_current_position(
        self, satellite_id: int, observer_location: Optional[GeoCoordinate] = None
    ) -> Dict[str, Any]:
        """獲取衛星當前位置"""
        pass

    @abstractmethod
    async def calculate_ground_track(
        self,
        satellite_id: int,
        start_time: datetime,
        revolutions: float = 1.0,
        step_seconds: int = 60,
    ) -> Dict[str, Any]:
        """計算衛星地面軌跡"""
        pass

    @abstractmethod
    async def calculate_visibility(
        self,
        satellite_id: int,
        observer_location: GeoCoordinate,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """計算衛星對於特定觀測者的可見性"""
        pass
