"""
批量並行軌道計算服務
優化多衛星軌道計算的性能
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time
import os

from app.domains.satellite.services.orbit_service import OrbitService
from app.domains.satellite.services.satellite_cache_service import (
    SatelliteCacheService, 
    CachedSatellitePosition,
    CachedOrbitData,
    get_cache_service
)
from app.domains.satellite.interfaces.satellite_repository import SatelliteRepositoryInterface
from app.domains.coordinates.models.geo_coordinate import GeoCoordinate

logger = logging.getLogger(__name__)

@dataclass
class BatchCalculationRequest:
    """批量計算請求"""
    satellite_ids: List[int]
    observer_location: GeoCoordinate
    start_time: datetime
    end_time: datetime
    step_seconds: int = 60
    include_velocity: bool = False
    use_cache: bool = True

@dataclass
class BatchCalculationResult:
    """批量計算結果"""
    successful_calculations: Dict[int, List[CachedSatellitePosition]]
    failed_calculations: Dict[int, str]
    cache_hits: int
    cache_misses: int
    total_calculation_time: float
    parallel_efficiency: float

class BatchOrbitService:
    """批量並行軌道計算服務"""
    
    def __init__(
        self, 
        orbit_service: OrbitService,
        cache_service: Optional[SatelliteCacheService] = None
    ):
        self.orbit_service = orbit_service
        self.cache_service = cache_service or get_cache_service()
        
        # 性能配置
        self.max_concurrent_calculations = int(os.getenv('MAX_CONCURRENT_ORBIT_CALCULATIONS', '5'))
        self.batch_size = int(os.getenv('BATCH_SATELLITE_PROCESSING_SIZE', '20'))
        self.calculation_timeout = int(os.getenv('ORBIT_CALCULATION_TIMEOUT_SECONDS', '30'))
        
        # 執行器配置
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.max_concurrent_calculations,
            thread_name_prefix="orbit_calc"
        )
        
        # 並行控制
        self.semaphore = asyncio.Semaphore(self.max_concurrent_calculations)
        
        logger.info(f"批量軌道服務初始化完成 - 最大並行數: {self.max_concurrent_calculations}, "
                   f"批次大小: {self.batch_size}")

    async def calculate_positions_batch(
        self, 
        request: BatchCalculationRequest
    ) -> BatchCalculationResult:
        """批量計算衛星位置"""
        start_time = time.time()
        successful_calculations = {}
        failed_calculations = {}
        cache_hits = 0
        cache_misses = 0
        
        try:
            # 分批處理衛星
            satellite_batches = self._split_into_batches(request.satellite_ids, self.batch_size)
            
            for batch_index, satellite_batch in enumerate(satellite_batches):
                logger.debug(f"處理批次 {batch_index + 1}/{len(satellite_batches)}, "
                           f"衛星數量: {len(satellite_batch)}")
                
                # 檢查緩存
                if request.use_cache:
                    cached_positions = await self._get_cached_positions_for_batch(
                        satellite_batch, request
                    )
                    
                    for sat_id, positions in cached_positions.items():
                        successful_calculations[sat_id] = positions
                        cache_hits += 1
                    
                    # 移除已緩存的衛星
                    remaining_satellites = [
                        sat_id for sat_id in satellite_batch 
                        if sat_id not in cached_positions
                    ]
                    cache_misses += len(remaining_satellites)
                else:
                    remaining_satellites = satellite_batch
                    cache_misses += len(remaining_satellites)
                
                # 並行計算剩餘的衛星
                if remaining_satellites:
                    batch_results = await self._calculate_positions_parallel(
                        remaining_satellites, request
                    )
                    
                    for sat_id, result in batch_results.items():
                        if isinstance(result, list):
                            successful_calculations[sat_id] = result
                            # 緩存結果
                            if request.use_cache:
                                await self._cache_calculation_result(sat_id, result)
                        else:
                            failed_calculations[sat_id] = str(result)
            
            total_time = time.time() - start_time
            efficiency = self._calculate_parallel_efficiency(
                len(request.satellite_ids), total_time
            )
            
            logger.info(f"批量計算完成 - 成功: {len(successful_calculations)}, "
                       f"失敗: {len(failed_calculations)}, "
                       f"緩存命中: {cache_hits}, "
                       f"耗時: {total_time:.2f}s")
            
            return BatchCalculationResult(
                successful_calculations=successful_calculations,
                failed_calculations=failed_calculations,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                total_calculation_time=total_time,
                parallel_efficiency=efficiency
            )
            
        except Exception as e:
            logger.error(f"批量計算失敗: {e}")
            raise

    async def calculate_current_positions_batch(
        self, 
        satellite_ids: List[int],
        observer_location: GeoCoordinate,
        use_cache: bool = True
    ) -> BatchCalculationResult:
        """批量計算當前位置"""
        current_time = datetime.utcnow()
        
        request = BatchCalculationRequest(
            satellite_ids=satellite_ids,
            observer_location=observer_location,
            start_time=current_time,
            end_time=current_time,
            step_seconds=0,  # 只計算當前時刻
            use_cache=use_cache
        )
        
        return await self.calculate_positions_batch(request)

    async def calculate_passes_batch(
        self,
        satellite_ids: List[int],
        observer_location: GeoCoordinate,
        start_time: datetime,
        end_time: datetime,
        min_elevation: float = 10.0
    ) -> Dict[int, List[Dict[str, Any]]]:
        """批量計算衛星過境"""
        results = {}
        
        async def calculate_single_pass(sat_id: int):
            async with self.semaphore:
                try:
                    passes = await self.orbit_service.calculate_passes(
                        satellite_id=sat_id,
                        observer_location=observer_location,
                        start_time=start_time,
                        end_time=end_time,
                        min_elevation=min_elevation
                    )
                    return sat_id, passes
                except Exception as e:
                    logger.error(f"計算衛星 {sat_id} 過境失敗: {e}")
                    return sat_id, []
        
        # 並行計算所有衛星的過境
        tasks = [calculate_single_pass(sat_id) for sat_id in satellite_ids]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_tasks:
            if isinstance(result, tuple):
                sat_id, passes = result
                results[sat_id] = passes
            else:
                logger.error(f"過境計算異常: {result}")
        
        return results

    async def _calculate_positions_parallel(
        self, 
        satellite_ids: List[int], 
        request: BatchCalculationRequest
    ) -> Dict[int, Any]:
        """並行計算衛星位置"""
        results = {}
        
        async def calculate_single_satellite(sat_id: int):
            async with self.semaphore:
                try:
                    # 使用asyncio.wait_for設置超時
                    result = await asyncio.wait_for(
                        self._calculate_satellite_orbit(sat_id, request),
                        timeout=self.calculation_timeout
                    )
                    return sat_id, result
                except asyncio.TimeoutError:
                    error_msg = f"計算超時（{self.calculation_timeout}秒）"
                    logger.warning(f"衛星 {sat_id} {error_msg}")
                    return sat_id, error_msg
                except Exception as e:
                    error_msg = f"計算失敗: {str(e)}"
                    logger.error(f"衛星 {sat_id} {error_msg}")
                    return sat_id, error_msg
        
        # 並行執行所有計算任務
        tasks = [calculate_single_satellite(sat_id) for sat_id in satellite_ids]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_tasks:
            if isinstance(result, tuple):
                sat_id, calc_result = result
                results[sat_id] = calc_result
            else:
                logger.error(f"計算任務異常: {result}")
        
        return results

    async def _calculate_satellite_orbit(
        self, 
        satellite_id: int, 
        request: BatchCalculationRequest
    ) -> List[CachedSatellitePosition]:
        """計算單個衛星的軌道"""
        try:
            if request.start_time == request.end_time:
                # 只計算當前位置
                position_data = await self.orbit_service.get_current_position(
                    satellite_id=satellite_id,
                    observer_location=request.observer_location
                )
                
                if position_data and position_data.get("success"):
                    pos = position_data["position"]
                    cached_position = CachedSatellitePosition(
                        satellite_id=satellite_id,
                        latitude=pos["latitude"],
                        longitude=pos["longitude"],
                        altitude=pos["altitude"],
                        timestamp=datetime.fromisoformat(pos["timestamp"]),
                        ecef_x_km=pos.get("ecef_x_km"),
                        ecef_y_km=pos.get("ecef_y_km"),
                        ecef_z_km=pos.get("ecef_z_km"),
                        elevation_deg=pos.get("elevation_deg"),
                        azimuth_deg=pos.get("azimuth_deg"),
                        distance_km=pos.get("distance_km")
                    )
                    return [cached_position]
                else:
                    raise Exception("無法獲取當前位置")
            else:
                # 計算軌道傳播
                orbit_data = await self.orbit_service.propagate_orbit(
                    satellite_id=satellite_id,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    step_seconds=request.step_seconds
                )
                
                if orbit_data and orbit_data.get("success"):
                    positions = []
                    for pos in orbit_data["orbit_points"]:
                        cached_position = CachedSatellitePosition(
                            satellite_id=satellite_id,
                            latitude=pos["latitude"],
                            longitude=pos["longitude"],
                            altitude=pos["altitude"],
                            timestamp=datetime.fromisoformat(pos["timestamp"])
                        )
                        positions.append(cached_position)
                    return positions
                else:
                    raise Exception("軌道計算失敗")
                    
        except Exception as e:
            logger.error(f"衛星 {satellite_id} 軌道計算失敗: {e}")
            raise

    async def _get_cached_positions_for_batch(
        self, 
        satellite_ids: List[int], 
        request: BatchCalculationRequest
    ) -> Dict[int, List[CachedSatellitePosition]]:
        """為批次獲取緩存的位置數據"""
        cached_results = {}
        
        if request.start_time == request.end_time:
            # 當前位置緩存查詢
            cached_positions = await self.cache_service.get_cached_positions_batch(
                satellite_ids
            )
            
            for sat_id, position in cached_positions.items():
                cached_results[sat_id] = [position]
        else:
            # 軌道數據緩存查詢
            for sat_id in satellite_ids:
                cached_orbit = await self.cache_service.get_cached_orbit(
                    satellite_id=sat_id,
                    start_time=request.start_time,
                    end_time=request.end_time
                )
                
                if cached_orbit:
                    cached_results[sat_id] = cached_orbit.positions
        
        return cached_results

    async def _cache_calculation_result(
        self, 
        satellite_id: int, 
        positions: List[CachedSatellitePosition]
    ) -> None:
        """緩存計算結果"""
        try:
            if len(positions) == 1:
                # 單個位置緩存
                await self.cache_service.cache_position(positions[0])
            else:
                # 軌道數據緩存
                orbit_data = CachedOrbitData(
                    satellite_id=satellite_id,
                    start_time=positions[0].timestamp,
                    end_time=positions[-1].timestamp,
                    positions=positions,
                    calculation_time=datetime.utcnow()
                )
                await self.cache_service.cache_orbit(orbit_data)
                
        except Exception as e:
            logger.error(f"緩存衛星 {satellite_id} 計算結果失敗: {e}")

    def _split_into_batches(self, items: List[Any], batch_size: int) -> List[List[Any]]:
        """將列表分割為批次"""
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

    def _calculate_parallel_efficiency(self, total_satellites: int, total_time: float) -> float:
        """計算並行效率"""
        if total_time == 0:
            return 1.0
        
        # 估算串行時間（假設每個衛星需要1秒）
        estimated_serial_time = total_satellites * 1.0
        
        # 理論並行時間
        theoretical_parallel_time = estimated_serial_time / self.max_concurrent_calculations
        
        # 效率 = 理論並行時間 / 實際時間
        efficiency = theoretical_parallel_time / total_time
        
        return min(efficiency, 1.0)  # 效率不超過100%

    async def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        cache_stats = await self.cache_service.get_cache_stats()
        
        return {
            'max_concurrent_calculations': self.max_concurrent_calculations,
            'batch_size': self.batch_size,
            'calculation_timeout': self.calculation_timeout,
            'thread_pool_workers': self.thread_pool._max_workers,
            'cache_stats': cache_stats
        }

    async def shutdown(self):
        """關閉服務，清理資源"""
        logger.info("正在關閉批量軌道計算服務")
        
        # 關閉線程池
        self.thread_pool.shutdown(wait=True)
        
        logger.info("批量軌道計算服務已關閉")

# 優化的軌道計算工具函數
class OrbitCalculationOptimizer:
    """軌道計算優化器"""
    
    @staticmethod
    def optimize_time_steps(
        start_time: datetime, 
        end_time: datetime, 
        max_points: int = 100
    ) -> int:
        """優化時間步長以控制計算點數"""
        total_seconds = (end_time - start_time).total_seconds()
        
        if total_seconds <= 0:
            return 60  # 默認1分鐘
        
        optimal_step = max(60, int(total_seconds / max_points))
        return optimal_step

    @staticmethod
    def prioritize_satellites_by_visibility(
        satellite_ids: List[int],
        observer_location: GeoCoordinate,
        current_time: datetime
    ) -> List[int]:
        """根據可見性優先級排序衛星"""
        # 這裡可以實現更複雜的優先級邏輯
        # 例如：根據預計的最大仰角、當前距離等
        return satellite_ids  # 暫時返回原順序

    @staticmethod
    def estimate_calculation_complexity(
        satellite_count: int,
        time_span_hours: float,
        step_seconds: int
    ) -> str:
        """估算計算複雜度"""
        total_points = satellite_count * (time_span_hours * 3600 / step_seconds)
        
        if total_points < 1000:
            return "LOW"
        elif total_points < 10000:
            return "MEDIUM"
        elif total_points < 100000:
            return "HIGH"
        else:
            return "VERY_HIGH"

# 全局批量服務實例
_batch_service: Optional[BatchOrbitService] = None

def get_batch_orbit_service(orbit_service: OrbitService) -> BatchOrbitService:
    """獲取批量軌道服務實例"""
    global _batch_service
    if _batch_service is None:
        _batch_service = BatchOrbitService(orbit_service)
    return _batch_service