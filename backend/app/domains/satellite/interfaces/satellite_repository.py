from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domains.satellite.models.satellite_model import Satellite, SatellitePass


class SatelliteRepositoryInterface(ABC):
    """衛星儲存庫接口"""

    @abstractmethod
    async def get_satellites(self) -> List[Satellite]:
        """獲取所有衛星"""
        pass

    @abstractmethod
    async def get_satellite_by_id(self, satellite_id: int) -> Optional[Satellite]:
        """根據 ID 獲取衛星"""
        pass

    @abstractmethod
    async def get_satellite_by_norad_id(self, norad_id: str) -> Optional[Satellite]:
        """根據 NORAD ID 獲取衛星"""
        pass

    @abstractmethod
    async def search_satellites(self, query: str) -> List[Satellite]:
        """搜尋衛星"""
        pass

    @abstractmethod
    async def create_satellite(self, satellite_data: Dict[str, Any]) -> Satellite:
        """創建新衛星"""
        pass

    @abstractmethod
    async def update_satellite(
        self, satellite_id: int, satellite_data: Dict[str, Any]
    ) -> Optional[Satellite]:
        """更新衛星數據"""
        pass

    @abstractmethod
    async def delete_satellite(self, satellite_id: int) -> bool:
        """刪除衛星"""
        pass

    @abstractmethod
    async def get_satellite_passes(
        self, satellite_id: int, start_time: datetime, end_time: datetime
    ) -> List[SatellitePass]:
        """獲取衛星過境數據"""
        pass

    @abstractmethod
    async def save_satellite_pass(
        self, satellite_pass_data: Dict[str, Any]
    ) -> SatellitePass:
        """保存衛星過境數據"""
        pass

    @abstractmethod
    async def update_tle_data(
        self, satellite_id: int, tle_data: Dict[str, Any]
    ) -> Optional[Satellite]:
        """更新衛星的 TLE 數據"""
        pass
