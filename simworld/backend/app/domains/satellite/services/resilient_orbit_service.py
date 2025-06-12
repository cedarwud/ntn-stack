"""
具備容錯能力的軌道服務整合
整合錯誤處理、批量處理、緩存和降級策略
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import os

from app.domains.satellite.services.orbit_service import OrbitService
from app.domains.satellite.services.batch_orbit_service import (
    BatchOrbitService, BatchCalculationRequest, BatchCalculationResult
)
from app.domains.satellite.services.satellite_cache_service import (
    SatelliteCacheService, CachedSatellitePosition, get_cache_service
)
from app.domains.satellite.services.error_handling_service import (
    ErrorHandlingService, FallbackStrategy, get_error_handling_service
)
from app.domains.satellite.schemas.api_response import (
    ApiResponse, create_success_response, create_error_response, ErrorCode
)
from app.domains.coordinates.models.geo_coordinate import GeoCoordinate

logger = logging.getLogger(__name__)

class ResilientOrbitService:
    """具備完整容錯能力的軌道服務"""
    
    def __init__(
        self,
        orbit_service: OrbitService,
        batch_service: Optional[BatchOrbitService] = None,
        cache_service: Optional[SatelliteCacheService] = None,
        error_service: Optional[ErrorHandlingService] = None
    ):
        self.orbit_service = orbit_service
        self.batch_service = batch_service or BatchOrbitService(orbit_service)
        self.cache_service = cache_service or get_cache_service()
        self.error_service = error_service or get_error_handling_service()
        
        # 服務配置
        self.enable_batch_processing = os.getenv('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true'
        self.batch_threshold = int(os.getenv('BATCH_PROCESSING_THRESHOLD', '5'))
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_ORBIT_REQUESTS', '10'))
        
        # 請求限流器
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        logger.info(f"容錯軌道服務初始化完成 - 批量處理: {self.enable_batch_processing}, "
                   f"批量閾值: {self.batch_threshold}")

    async def get_satellite_position(
        self,
        satellite_id: int,
        observer_location: Optional[GeoCoordinate] = None,
        timestamp: Optional[datetime] = None
    ) -> ApiResponse[Dict[str, Any]]:
        """獲取單個衛星位置（含容錯）"""
        
        async with self.request_semaphore:
            context_data = {
                'satellite_id': satellite_id,
                'observer_location': observer_location,
                'timestamp': timestamp or datetime.utcnow(),
                'cache_service': self.cache_service,
                'cache_key': f"position:{satellite_id}:{timestamp or 'current'}",
                'retry_function': lambda: self.orbit_service.get_current_position(
                    satellite_id, observer_location or GeoCoordinate(24.943889, 121.370833, 0.0)
                )
            }
            
            fallback_strategies = [
                FallbackStrategy.RETRY,
                FallbackStrategy.CACHE,
                FallbackStrategy.MOCK
            ]
            
            async def get_position():
                return await self.orbit_service.get_current_position(
                    satellite_id,
                    observer_location or GeoCoordinate(24.943889, 121.370833, 0.0)
                )
            
            result = await self.error_service.handle_with_fallback(
                primary_operation=get_position,
                operation_name="satellite_position",
                fallback_strategies=fallback_strategies,
                context_data=context_data,
                expected_error_codes=[ErrorCode.SATELLITE_NOT_FOUND, ErrorCode.ORBIT_CALCULATION_FAILED]
            )
            
            if isinstance(result, ApiResponse):
                return result
            else:
                return create_success_response(result)

    async def get_satellite_positions_batch(
        self,
        satellite_ids: List[int],
        observer_location: Optional[GeoCoordinate] = None,
        use_cache: bool = True
    ) -> ApiResponse[Dict[str, Any]]:
        """批量獲取衛星位置（含容錯）"""
        
        if not satellite_ids:
            return create_error_response(
                ErrorCode.INVALID_SATELLITE_ID,
                "衛星ID列表不能為空"
            )
        
        # 決定是否使用批量處理
        if len(satellite_ids) >= self.batch_threshold and self.enable_batch_processing:
            return await self._batch_get_positions(satellite_ids, observer_location, use_cache)
        else:
            return await self._sequential_get_positions(satellite_ids, observer_location, use_cache)

    async def _batch_get_positions(
        self,
        satellite_ids: List[int],
        observer_location: Optional[GeoCoordinate],
        use_cache: bool
    ) -> ApiResponse[Dict[str, Any]]:
        """批量並行獲取位置"""
        
        observer_loc = observer_location or GeoCoordinate(24.943889, 121.370833, 0.0)
        
        context_data = {
            'satellite_ids': satellite_ids,
            'observer_location': observer_loc,
            'use_cache': use_cache,
            'cache_service': self.cache_service,
            'retry_function': lambda: self.batch_service.calculate_current_positions_batch(
                satellite_ids, observer_loc, use_cache
            )
        }
        
        fallback_strategies = [
            FallbackStrategy.RETRY,
            FallbackStrategy.CACHE,
            FallbackStrategy.GRACEFUL_DEGRADATION,
            FallbackStrategy.SIMPLIFIED
        ]
        
        async def batch_calculate():
            return await self.batch_service.calculate_current_positions_batch(
                satellite_ids, observer_loc, use_cache
            )
        
        result = await self.error_service.handle_with_fallback(
            primary_operation=batch_calculate,
            operation_name="batch_satellite_calculation",
            fallback_strategies=fallback_strategies,
            context_data=context_data
        )
        
        if isinstance(result, ApiResponse):
            return result
        elif isinstance(result, BatchCalculationResult):
            return create_success_response({
                'successful_calculations': len(result.successful_calculations),
                'failed_calculations': len(result.failed_calculations),
                'positions': result.successful_calculations,
                'errors': result.failed_calculations,
                'performance': {
                    'cache_hits': result.cache_hits,
                    'cache_misses': result.cache_misses,
                    'total_time': result.total_calculation_time,
                    'efficiency': result.parallel_efficiency
                }
            })
        else:
            return create_success_response(result)

    async def _sequential_get_positions(
        self,
        satellite_ids: List[int],
        observer_location: Optional[GeoCoordinate],
        use_cache: bool
    ) -> ApiResponse[Dict[str, Any]]:
        """順序獲取位置（小批量）"""
        
        positions = {}
        errors = {}
        
        for satellite_id in satellite_ids:
            try:
                result = await self.get_satellite_position(satellite_id, observer_location)
                
                if result.status == "success":
                    positions[satellite_id] = result.data
                else:
                    errors[satellite_id] = result.error.message if result.error else "未知錯誤"
                    
            except Exception as e:
                errors[satellite_id] = str(e)
        
        return create_success_response({
            'successful_calculations': len(positions),
            'failed_calculations': len(errors),
            'positions': positions,
            'errors': errors
        })

    async def calculate_satellite_orbit(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
        observer_location: Optional[GeoCoordinate] = None
    ) -> ApiResponse[Dict[str, Any]]:
        """計算衛星軌道（含容錯）"""
        
        async with self.request_semaphore:
            # 驗證時間範圍
            if start_time >= end_time:
                return create_error_response(
                    ErrorCode.INVALID_TIME_RANGE,
                    "開始時間必須早於結束時間"
                )
            
            if (end_time - start_time).days > 7:
                return create_error_response(
                    ErrorCode.INVALID_TIME_RANGE,
                    "時間範圍不能超過7天"
                )
            
            observer_loc = observer_location or GeoCoordinate(24.943889, 121.370833, 0.0)
            
            context_data = {
                'satellite_id': satellite_id,
                'start_time': start_time,
                'end_time': end_time,
                'step_seconds': step_seconds,
                'observer_location': observer_loc,
                'cache_service': self.cache_service,
                'cache_key': f"orbit:{satellite_id}:{start_time.isoformat()}:{end_time.isoformat()}",
                'retry_function': lambda: self.orbit_service.propagate_orbit(
                    satellite_id, start_time, end_time, step_seconds
                )
            }
            
            fallback_strategies = [
                FallbackStrategy.RETRY,
                FallbackStrategy.CACHE,
                FallbackStrategy.SIMPLIFIED,
                FallbackStrategy.ALTERNATIVE_SOURCE
            ]
            
            async def calculate_orbit():
                return await self.orbit_service.propagate_orbit(
                    satellite_id, start_time, end_time, step_seconds
                )
            
            result = await self.error_service.handle_with_fallback(
                primary_operation=calculate_orbit,
                operation_name="orbit_calculation",
                fallback_strategies=fallback_strategies,
                context_data=context_data,
                expected_error_codes=[ErrorCode.ORBIT_CALCULATION_FAILED, ErrorCode.SATELLITE_NOT_FOUND]
            )
            
            if isinstance(result, ApiResponse):
                return result
            else:
                return create_success_response(result)

    async def calculate_satellite_passes(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        observer_location: Optional[GeoCoordinate] = None,
        min_elevation: float = 10.0
    ) -> ApiResponse[Dict[str, Any]]:
        """計算衛星過境（含容錯）"""
        
        async with self.request_semaphore:
            observer_loc = observer_location or GeoCoordinate(24.943889, 121.370833, 0.0)
            
            context_data = {
                'satellite_id': satellite_id,
                'start_time': start_time,
                'end_time': end_time,
                'observer_location': observer_loc,
                'min_elevation': min_elevation,
                'retry_function': lambda: self.orbit_service.calculate_passes(
                    satellite_id, observer_loc, start_time, end_time, min_elevation
                )
            }
            
            fallback_strategies = [
                FallbackStrategy.RETRY,
                FallbackStrategy.MOCK,
                FallbackStrategy.SIMPLIFIED
            ]
            
            async def calculate_passes():
                return await self.orbit_service.calculate_passes(
                    satellite_id, observer_loc, start_time, end_time, min_elevation
                )
            
            result = await self.error_service.handle_with_fallback(
                primary_operation=calculate_passes,
                operation_name="satellite_passes",
                fallback_strategies=fallback_strategies,
                context_data=context_data
            )
            
            if isinstance(result, ApiResponse):
                return result
            else:
                return create_success_response(result)

    async def get_batch_satellite_passes(
        self,
        satellite_ids: List[int],
        start_time: datetime,
        end_time: datetime,
        observer_location: Optional[GeoCoordinate] = None,
        min_elevation: float = 10.0
    ) -> ApiResponse[Dict[str, Any]]:
        """批量計算衛星過境"""
        
        if not satellite_ids:
            return create_error_response(
                ErrorCode.INVALID_SATELLITE_ID,
                "衛星ID列表不能為空"
            )
        
        observer_loc = observer_location or GeoCoordinate(24.943889, 121.370833, 0.0)
        
        context_data = {
            'satellite_ids': satellite_ids,
            'start_time': start_time,
            'end_time': end_time,
            'observer_location': observer_loc,
            'min_elevation': min_elevation
        }
        
        fallback_strategies = [
            FallbackStrategy.RETRY,
            FallbackStrategy.GRACEFUL_DEGRADATION,
            FallbackStrategy.MOCK
        ]
        
        async def batch_calculate_passes():
            return await self.batch_service.calculate_passes_batch(
                satellite_ids, observer_loc, start_time, end_time, min_elevation
            )
        
        result = await self.error_service.handle_with_fallback(
            primary_operation=batch_calculate_passes,
            operation_name="batch_satellite_passes",
            fallback_strategies=fallback_strategies,
            context_data=context_data
        )
        
        if isinstance(result, ApiResponse):
            return result
        else:
            return create_success_response({
                'passes_by_satellite': result,
                'total_satellites': len(satellite_ids),
                'successful_calculations': len(result)
            })

    async def get_service_health(self) -> ApiResponse[Dict[str, Any]]:
        """獲取服務健康狀態"""
        try:
            # 獲取各個子服務的統計信息
            cache_stats = await self.cache_service.get_cache_stats()
            error_stats = await self.error_service.get_error_statistics()
            batch_stats = await self.batch_service.get_performance_stats()
            
            health_data = {
                'service_status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'cache_service': {
                    'status': 'operational',
                    'stats': cache_stats
                },
                'batch_service': {
                    'status': 'operational',
                    'stats': batch_stats
                },
                'error_handling': {
                    'status': 'operational',
                    'stats': error_stats
                },
                'configuration': {
                    'batch_processing_enabled': self.enable_batch_processing,
                    'batch_threshold': self.batch_threshold,
                    'max_concurrent_requests': self.max_concurrent_requests
                }
            }
            
            return create_success_response(health_data)
            
        except Exception as e:
            logger.error(f"獲取服務健康狀態失敗: {e}")
            return create_error_response(
                ErrorCode.INTERNAL_SERVER_ERROR,
                f"服務健康檢查失敗: {str(e)}"
            )

    async def clear_all_caches(self) -> ApiResponse[Dict[str, Any]]:
        """清理所有緩存"""
        try:
            # 清理過期緩存
            cleared_count = await self.cache_service.clear_expired_cache()
            
            # 重置錯誤統計
            await self.error_service.reset_statistics()
            
            return create_success_response({
                'cleared_cache_items': cleared_count,
                'error_stats_reset': True,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"清理緩存失敗: {e}")
            return create_error_response(
                ErrorCode.INTERNAL_SERVER_ERROR,
                f"清理緩存失敗: {str(e)}"
            )

    async def shutdown(self):
        """關閉服務，清理資源"""
        logger.info("正在關閉容錯軌道服務")
        
        # 關閉批量服務
        if self.batch_service:
            await self.batch_service.shutdown()
        
        logger.info("容錯軌道服務已關閉")

# 全局容錯軌道服務實例
_resilient_service: Optional[ResilientOrbitService] = None

def get_resilient_orbit_service(orbit_service: OrbitService) -> ResilientOrbitService:
    """獲取容錯軌道服務實例"""
    global _resilient_service
    if _resilient_service is None:
        _resilient_service = ResilientOrbitService(orbit_service)
    return _resilient_service