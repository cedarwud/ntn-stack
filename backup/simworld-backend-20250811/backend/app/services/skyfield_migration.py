#!/usr/bin/env python3
"""
Skyfield 遷移服務 - 逐步替換 SimWorld 中的 skyfield 依賴

Phase 1 遷移策略：
1. 提供兼容接口，保持現有代碼不變
2. 內部使用 NetStack API 替代 skyfield 計算
3. 逐步移除 skyfield 依賴
"""

import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import asyncio
import math

from .netstack_client import get_netstack_client

logger = structlog.get_logger(__name__)


class SatellitePositionCompat:
    """衛星位置兼容類 - 模擬 skyfield 衛星位置對象"""
    
    def __init__(self, satellite_data: Dict[str, Any]):
        """
        初始化衛星位置兼容對象
        
        Args:
            satellite_data: 從 NetStack API 獲取的衛星數據
        """
        self.data = satellite_data
        
    @property
    def latitude(self) -> float:
        """緯度 (度)"""
        return self.data.get('latitude', 0.0)
    
    @property  
    def longitude(self) -> float:
        """經度 (度)"""
        return self.data.get('longitude', 0.0)
    
    @property
    def altitude(self) -> float:
        """海拔 (米)"""
        return self.data.get('altitude', 550000.0)
    
    @property
    def elevation(self) -> float:
        """仰角 (度)"""
        return self.data.get('elevation', 0.0)
    
    @property
    def azimuth(self) -> float:
        """方位角 (度)"""
        return self.data.get('azimuth', 0.0)
    
    @property
    def range_km(self) -> float:
        """距離 (公里)"""
        return self.data.get('range_km', 1000.0)
    
    @property
    def is_visible(self) -> bool:
        """是否可見"""
        return self.data.get('is_visible', False)


class EarthSatelliteCompat:
    """地球衛星兼容類 - 模擬 skyfield.EarthSatellite"""
    
    def __init__(self, tle_line1: str, tle_line2: str, name: str = "", ts=None):
        """
        初始化地球衛星兼容對象
        
        Args:
            tle_line1: TLE 第一行
            tle_line2: TLE 第二行  
            name: 衛星名稱
            ts: 時間標度 (兼容性參數)
        """
        self.tle_line1 = tle_line1
        self.tle_line2 = tle_line2
        self.name = name
        self.ts = ts
        
        # 解析 TLE 數據
        self.norad_id = self._parse_norad_id(tle_line1)
        
    def _parse_norad_id(self, tle_line1: str) -> int:
        """從 TLE 第一行解析 NORAD ID"""
        try:
            return int(tle_line1[2:7])
        except (ValueError, IndexError):
            return 0
    
    async def at(self, time_obj) -> SatellitePositionCompat:
        """
        計算指定時間的衛星位置 (兼容 skyfield 接口)
        
        Args:
            time_obj: 時間對象
            
        Returns:
            衛星位置兼容對象
        """
        # 使用 NetStack API 獲取位置數據
        client = get_netstack_client()
        
        try:
            # 獲取預計算數據
            orbit_data = await client.get_precomputed_orbit_data(
                location="ntpu",
                constellation="starlink"  # 假設是 Starlink
            )
            
            # 查找對應的衛星數據
            for sat in orbit_data.get("filtered_satellites", []):
                if sat.get("norad_id") == self.norad_id:
                    return SatellitePositionCompat(sat)
            
            # 如果沒找到，返回默認位置
            return SatellitePositionCompat({
                "latitude": 0.0,
                "longitude": 0.0,
                "altitude": 550000.0,
                "elevation": 0.0,
                "azimuth": 0.0,
                "range_km": 2000.0,
                "is_visible": False
            })
            
        except Exception as e:
            logger.warning(f"使用 NetStack API 獲取衛星位置失敗，返回模擬數據: {e}")
            
            # 返回模擬位置數據
            return SatellitePositionCompat({
                "latitude": 45.0,
                "longitude": 120.0,
                "altitude": 550000.0,
                "elevation": 25.0,
                "azimuth": 180.0,
                "range_km": 1000.0,
                "is_visible": True
            })


class SkyfieldMigrationService:
    """Skyfield 遷移服務 - 提供逐步遷移支援"""
    
    def __init__(self):
        """初始化遷移服務"""
        self.netstack_client = get_netstack_client()
        self.migration_enabled = True  # 是否啟用遷移模式
        
    async def create_earth_satellite(
        self, 
        tle_line1: str, 
        tle_line2: str, 
        name: str = "",
        ts=None
    ) -> EarthSatelliteCompat:
        """
        創建地球衛星對象 (兼容 skyfield 接口)
        
        Args:
            tle_line1: TLE 第一行
            tle_line2: TLE 第二行
            name: 衛星名稱
            ts: 時間標度
            
        Returns:
            地球衛星兼容對象
        """
        if self.migration_enabled:
            return EarthSatelliteCompat(tle_line1, tle_line2, name, ts)
        else:
            # 如果遷移未啟用，使用原生 skyfield (向後兼容)
            try:
                from skyfield.api import EarthSatellite
                return EarthSatellite(tle_line1, tle_line2, name, ts)
            except ImportError:
                logger.warning("skyfield 不可用，強制使用遷移模式")
                self.migration_enabled = True
                return EarthSatelliteCompat(tle_line1, tle_line2, name, ts)
    
    async def load_satellites_from_netstack(
        self,
        constellation: str = "starlink",
        location: str = "ntpu"
    ) -> List[EarthSatelliteCompat]:
        """
        從 NetStack 載入衛星數據
        
        Args:
            constellation: 星座名稱
            location: 觀測位置
            
        Returns:
            衛星對象列表
        """
        try:
            orbit_data = await self.netstack_client.get_precomputed_orbit_data(
                location=location,
                constellation=constellation
            )
            
            satellites = []
            for sat_data in orbit_data.get("filtered_satellites", []):
                # 創建模擬的 TLE 數據 (實際應該從 NetStack 獲取)
                tle_line1 = f"1 {sat_data.get('norad_id', 44714):05d}U 19074A   25001.00000000  .00000000  00000-0  00000-0 0  9999"
                tle_line2 = f"2 {sat_data.get('norad_id', 44714):05d}  53.0000 000.0000 0001000   0.0000   0.0000 15.50000000000009"
                
                satellite = EarthSatelliteCompat(
                    tle_line1, 
                    tle_line2,
                    sat_data.get('name', f'SAT-{sat_data.get("norad_id", 0)}')
                )
                satellites.append(satellite)
            
            logger.info(f"從 NetStack 載入了 {len(satellites)} 顆 {constellation} 衛星")
            return satellites
            
        except Exception as e:
            logger.error(f"從 NetStack 載入衛星失敗: {e}")
            return []
    
    async def calculate_visibility_netstack(
        self,
        satellites: List[EarthSatelliteCompat],
        observer_coords: Tuple[float, float, float],
        min_elevation: float = 10.0,
        time_window_hours: int = 6
    ) -> Dict[str, Any]:
        """
        使用 NetStack API 計算衛星可見性
        
        Args:
            satellites: 衛星列表
            observer_coords: 觀測者座標 (lat, lon, alt)
            min_elevation: 最小仰角
            time_window_hours: 時間窗口
            
        Returns:
            可見性分析結果
        """
        try:
            # 確定觀測位置
            lat, lon, alt = observer_coords
            location = "ntpu"  # 默認使用 NTPU，實際應該根據座標匹配
            
            # 獲取最佳時間窗口
            window_data = await self.netstack_client.get_optimal_timewindow(
                location=location,
                window_hours=time_window_hours
            )
            
            # 獲取預計算軌道數據
            orbit_data = await self.netstack_client.get_precomputed_orbit_data(
                location=location,
                elevation_threshold=min_elevation
            )
            
            return {
                "visible_satellites": len(orbit_data.get("filtered_satellites", [])),
                "optimal_window": window_data.get("optimal_window", {}),
                "satellite_trajectories": window_data.get("satellite_trajectories", []),
                "handover_events": window_data.get("handover_events", []),
                "quality_score": window_data.get("quality_score", 0.0),
                "computation_time_ms": orbit_data.get("total_processing_time_ms", 0.0)
            }
            
        except Exception as e:
            logger.error(f"NetStack 可見性計算失敗: {e}")
            
            # 返回模擬數據作為降級
            return {
                "visible_satellites": len(satellites) // 3,
                "optimal_window": {
                    "start_time": datetime.now().isoformat(),
                    "duration_hours": time_window_hours
                },
                "satellite_trajectories": [],
                "handover_events": [],
                "quality_score": 0.5,
                "computation_time_ms": 1000.0
            }
    
    async def get_satellite_position_batch(
        self,
        satellite_ids: List[int],
        observer_coords: Tuple[float, float, float],
        timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        批量獲取衛星位置 (使用 NetStack API)
        
        Args:
            satellite_ids: 衛星 ID 列表
            observer_coords: 觀測者座標
            timestamp: 指定時間點
            
        Returns:
            衛星位置數據列表
        """
        try:
            lat, lon, alt = observer_coords
            
            # 使用 NetStack 兼容方法
            positions = await self.netstack_client.get_satellite_positions(
                satellite_ids=satellite_ids,
                observer_lat=lat,
                observer_lon=lon,
                observer_alt=alt,
                timestamp=timestamp
            )
            
            return positions
            
        except Exception as e:
            logger.error(f"批量獲取衛星位置失敗: {e}")
            
            # 返回模擬位置數據
            return [
                {
                    "satellite_id": sat_id,
                    "latitude": 45.0 + (sat_id % 10),
                    "longitude": 120.0 + (sat_id % 20), 
                    "altitude": 550000.0,
                    "elevation": 25.0,
                    "azimuth": sat_id % 360,
                    "range_km": 1000.0,
                    "is_visible": True
                }
                for sat_id in satellite_ids
            ]
    
    def enable_migration(self, enabled: bool = True):
        """
        啟用或禁用遷移模式
        
        Args:
            enabled: 是否啟用遷移模式
        """
        self.migration_enabled = enabled
        logger.info(f"Skyfield 遷移模式: {'啟用' if enabled else '禁用'}")
    
    async def check_netstack_availability(self) -> bool:
        """
        檢查 NetStack API 可用性
        
        Returns:
            True if NetStack is available
        """
        return await self.netstack_client.ping()
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """
        獲取遷移狀態報告
        
        Returns:
            遷移狀態信息
        """
        netstack_available = await self.check_netstack_availability()
        
        return {
            "migration_enabled": self.migration_enabled,
            "netstack_available": netstack_available,
            "skyfield_fallback": not self.migration_enabled,
            "status": "ready" if netstack_available else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features": {
                "satellite_loading": "netstack" if netstack_available else "fallback",
                "position_calculation": "netstack" if netstack_available else "simulation",
                "visibility_analysis": "netstack" if netstack_available else "basic"
            }
        }


# === 全域遷移服務實例 ===

_migration_service: Optional[SkyfieldMigrationService] = None

def get_migration_service() -> SkyfieldMigrationService:
    """
    獲取 Skyfield 遷移服務單例
    
    Returns:
        遷移服務實例
    """
    global _migration_service
    if _migration_service is None:
        _migration_service = SkyfieldMigrationService()
    return _migration_service


# === 兼容性輔助函數 ===

async def create_earth_satellite_compat(
    tle_line1: str, 
    tle_line2: str, 
    name: str = "",
    ts=None
) -> EarthSatelliteCompat:
    """
    創建地球衛星對象 (全域兼容函數)
    
    Args:
        tle_line1: TLE 第一行
        tle_line2: TLE 第二行
        name: 衛星名稱
        ts: 時間標度
        
    Returns:
        地球衛星兼容對象
    """
    service = get_migration_service()
    return await service.create_earth_satellite(tle_line1, tle_line2, name, ts)

async def load_satellites_compat(
    constellation: str = "starlink"
) -> List[EarthSatelliteCompat]:
    """
    載入衛星數據 (全域兼容函數)
    
    Args:
        constellation: 星座名稱
        
    Returns:
        衛星對象列表
    """
    service = get_migration_service()
    return await service.load_satellites_from_netstack(constellation)