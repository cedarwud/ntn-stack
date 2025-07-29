"""
演算法基礎類別
提供演算法的基本實現和共用功能
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.domains.handover.interfaces.algorithm_interface import AlgorithmInterface
from app.domains.satellite.services.orbit_service import OrbitService
from app.domains.coordinates.models.coordinate_model import GeoCoordinate

logger = logging.getLogger(__name__)


class BaseAlgorithm(AlgorithmInterface):
    """演算法基礎類別"""

    def __init__(self, orbit_service: OrbitService):
        self.orbit_service = orbit_service

    async def execute(self, *args, **kwargs) -> Any:
        """基礎執行方法，子類應該覆寫此方法"""
        raise NotImplementedError("子類必須實現 execute 方法")

    async def _get_visible_satellites(
        self, 
        timestamp: datetime, 
        ue_location: GeoCoordinate
    ) -> List[Dict[str, Any]]:
        """
        獲取可見衛星清單
        這是一個共用方法，可被所有演算法使用
        """
        try:
            satellites = await self.orbit_service.get_visible_satellites(
                ue_location.latitude,
                ue_location.longitude,
                ue_location.altitude,
                timestamp
            )
            
            logger.debug(f"找到 {len(satellites)} 顆可見衛星")
            return satellites
            
        except Exception as e:
            logger.error(f"獲取可見衛星時發生錯誤: {e}")
            return []

    def _calculate_elevation_angle(
        self, 
        satellite_pos: Dict[str, float], 
        ue_location: GeoCoordinate
    ) -> float:
        """
        計算仰角
        共用的數學計算方法
        """
        import math
        
        # 簡化的仰角計算
        sat_lat = satellite_pos.get('latitude', 0)
        sat_lon = satellite_pos.get('longitude', 0)
        sat_alt = satellite_pos.get('altitude', 0)
        
        # 計算距離和仰角
        lat_diff = math.radians(sat_lat - ue_location.latitude)
        lon_diff = math.radians(sat_lon - ue_location.longitude)
        alt_diff = sat_alt - ue_location.altitude
        
        # 簡化計算，實際應使用更精確的球面幾何
        horizontal_distance = math.sqrt(lat_diff**2 + lon_diff**2) * 6371000  # 地球半徑
        elevation_angle = math.atan2(alt_diff, horizontal_distance)
        
        return math.degrees(elevation_angle)

    def _calculate_signal_quality(
        self, 
        elevation_angle: float, 
        distance: float
    ) -> float:
        """
        計算信號品質
        基於仰角和距離的簡化模型
        """
        # 簡化的信號品質計算
        # 仰角越高、距離越近，信號品質越好
        elevation_factor = max(0, elevation_angle / 90.0)  # 正規化到 0-1
        distance_factor = max(0, 1 - distance / 2000000)   # 假設最大有效距離 2000km
        
        return (elevation_factor * 0.7 + distance_factor * 0.3) * 100

    async def _log_algorithm_performance(
        self, 
        algorithm_name: str, 
        start_time: datetime, 
        end_time: datetime,
        result_summary: Dict[str, Any]
    ) -> None:
        """
        記錄演算法性能
        用於監控和調試
        """
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"演算法 {algorithm_name} 執行完成:")
        logger.info(f"  執行時間: {execution_time:.3f} 秒")
        logger.info(f"  結果摘要: {result_summary}")


class BaseLatencyCalculator:
    """延遲計算器基礎類別"""

    def __init__(self):
        self.base_latencies = self._get_base_latency_config()

    def _get_base_latency_config(self) -> Dict[str, float]:
        """
        獲取基礎延遲配置
        這些是系統級的延遲參數
        """
        return {
            'processing_delay': 1.0,      # 處理延遲 (ms)
            'queuing_delay': 0.5,         # 排隊延遲 (ms)
            'transmission_delay': 0.1,    # 傳輸延遲 (ms)
            'propagation_base': 1.0,      # 基礎傳播延遲 (ms)
        }

    def _calculate_propagation_delay(self, distance_km: float) -> float:
        """
        計算傳播延遲
        基於光速和距離
        """
        speed_of_light = 299792458  # m/s
        return (distance_km * 1000) / speed_of_light * 1000  # 轉換為毫秒


class BaseScenarioAnalyzer:
    """場景分析器基礎類別"""

    def __init__(self):
        self.scenario_configs = self._get_default_scenarios()

    def _get_default_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取預設場景配置
        """
        return {
            'urban': {
                'building_density': 'high',
                'interference_level': 'high',
                'user_mobility': 'medium'
            },
            'suburban': {
                'building_density': 'medium',
                'interference_level': 'medium',
                'user_mobility': 'low'
            },
            'rural': {
                'building_density': 'low',
                'interference_level': 'low',
                'user_mobility': 'low'
            }
        }