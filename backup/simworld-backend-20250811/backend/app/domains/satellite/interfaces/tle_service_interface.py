from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class TLEServiceInterface(ABC):
    """TLE 服務接口，用於管理和更新衛星 TLE 數據"""

    @abstractmethod
    async def fetch_tle_from_celestrak(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """從 Celestrak 獲取 TLE 數據"""
        pass

    @abstractmethod
    async def fetch_tle_from_spacetrack(
        self, norad_id_list: Optional[List[str]] = None, days: int = 30
    ) -> List[Dict[str, Any]]:
        """從 Space-Track 獲取 TLE 數據"""
        pass

    @abstractmethod
    async def update_satellite_tle(self, norad_id: str) -> bool:
        """更新指定衛星的 TLE 數據"""
        pass

    @abstractmethod
    async def update_all_tles(self) -> Dict[str, Any]:
        """更新所有衛星的 TLE 數據"""
        pass

    @abstractmethod
    async def validate_tle(self, line1: str, line2: str) -> bool:
        """驗證 TLE 數據的有效性"""
        pass

    @abstractmethod
    async def parse_tle(self, line1: str, line2: str) -> Dict[str, Any]:
        """解析 TLE 數據，返回衛星參數"""
        pass
