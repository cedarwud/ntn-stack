"""
Satellite TLE Bridge API Router

提供衛星軌道預測和 TLE 資料橋接服務的 REST API 端點

主要功能：
1. 衛星軌道預測與快取管理
2. TLE 資料同步與健康檢查
3. 切換時機預測（二分搜尋算法）
4. 批量衛星位置獲取
5. 關鍵衛星資料預載
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
import redis.asyncio as redis

# Import services
from ..services.satellite_gnb_mapping_service import SatelliteGnbMappingService
from ..services.simworld_tle_bridge_service import SimWorldTLEBridgeService
from ..models.ueransim_models import UAVPosition

logger = structlog.get_logger(__name__)

# Request/Response Models
class OrbitPredictionRequest(BaseModel):
    """軌道預測請求"""
    satellite_id: str = Field(..., description="衛星 ID")
    time_range_hours: int = Field(2, ge=1, le=24, description="預測時間範圍（小時）")
    step_seconds: int = Field(60, ge=1, le=300, description="時間步長（秒）")
    observer_lat: Optional[float] = Field(None, ge=-90, le=90, description="觀測者緯度")
    observer_lon: Optional[float] = Field(None, ge=-180, le=180, description="觀測者經度")
    observer_alt: Optional[float] = Field(None, ge=0, description="觀測者高度（米）")


class BatchPositionRequest(BaseModel):
    """批量位置請求"""
    satellite_ids: List[str] = Field(..., description="衛星 ID 列表")
    timestamp: Optional[datetime] = Field(None, description="指定時間點（UTC）")
    observer_lat: Optional[float] = Field(None, ge=-90, le=90, description="觀測者緯度")
    observer_lon: Optional[float] = Field(None, ge=-180, le=180, description="觀測者經度")
    observer_alt: Optional[float] = Field(None, ge=0, description="觀測者高度（米）")


class HandoverPredictionRequest(BaseModel):
    """切換預測請求"""
    ue_id: str = Field(..., description="UE 識別碼")
    ue_lat: float = Field(..., ge=-90, le=90, description="UE 緯度")
    ue_lon: float = Field(..., ge=-180, le=180, description="UE 經度")
    ue_alt: float = Field(0, ge=0, description="UE 高度（米）")
    current_satellite: str = Field(..., description="當前接入衛星 ID")
    candidate_satellites: List[str] = Field(..., description="候選切換衛星列表")
    search_range_seconds: int = Field(300, ge=60, le=3600, description="搜尋範圍（秒）")


class BinarySearchHandoverRequest(BaseModel):
    """二分搜尋切換時間請求"""
    ue_id: str = Field(..., description="UE 識別碼")
    ue_lat: float = Field(..., ge=-90, le=90, description="UE 緯度")
    ue_lon: float = Field(..., ge=-180, le=180, description="UE 經度")
    ue_alt: float = Field(0, ge=0, description="UE 高度（米）")
    source_satellite: str = Field(..., description="源衛星 ID")
    target_satellite: str = Field(..., description="目標衛星 ID")
    search_start_timestamp: float = Field(..., description="搜尋開始時間戳")
    search_end_timestamp: float = Field(..., description="搜尋結束時間戳")
    precision_seconds: Optional[float] = Field(0.01, ge=0.001, le=1.0, description="搜尋精度（秒）")


class CacheManagementRequest(BaseModel):
    """快取管理請求"""
    satellite_ids: List[str] = Field(..., description="衛星 ID 列表")
    time_range_hours: int = Field(2, ge=1, le=12, description="預快取時間範圍（小時）")
    step_seconds: int = Field(60, ge=30, le=300, description="時間步長（秒）")


class TLEHealthCheckResponse(BaseModel):
    """TLE 健康檢查響應"""
    success: bool
    simworld_status: str
    tle_health: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    check_time: str


# Global service instances - 強制重置以應用環境變數變更
satellite_service: Optional[SatelliteGnbMappingService] = None
tle_bridge_service: Optional[SimWorldTLEBridgeService] = None

# 強制重置服務實例以應用新的環境變數
def reset_service_instances():
    global satellite_service, tle_bridge_service
    satellite_service = None
    tle_bridge_service = None


def get_satellite_service() -> SatelliteGnbMappingService:
    """獲取衛星服務實例"""
    import os
    global satellite_service
    if satellite_service is None:
        # 這裡可以配置 Redis 連接
        redis_client = None  # 可以根據需要配置
        
        # 根據環境選擇 SimWorld URL
        simworld_url = os.getenv(
            "SIMWORLD_API_URL", 
            "http://localhost:8888"  # 修改默認為主機環境，容器會覆蓋
        )
        
        satellite_service = SatelliteGnbMappingService(
            simworld_api_url=simworld_url,
            redis_client=redis_client
        )
    return satellite_service


def get_tle_bridge_service() -> SimWorldTLEBridgeService:
    """獲取 TLE 橋接服務實例"""
    import os
    global tle_bridge_service
    
    # 每次都檢查環境變數，確保使用最新配置
    current_simworld_url = os.getenv("SIMWORLD_API_URL", "http://localhost:8888")
    
    if tle_bridge_service is None or tle_bridge_service.simworld_api_url != current_simworld_url:
        # 這裡可以配置 Redis 連接
        redis_client = None  # 可以根據需要配置
        
        tle_bridge_service = SimWorldTLEBridgeService(
            simworld_api_url=current_simworld_url,
            redis_client=redis_client
        )
    return tle_bridge_service


# 創建路由器
router = APIRouter(
    prefix="/api/v1/satellite-tle",
    tags=["Satellite TLE Bridge"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.post("/orbit/predict", 
             summary="獲取衛星軌道預測",
             description="獲取指定衛星的軌道預測資料")
async def predict_satellite_orbit(
    request: OrbitPredictionRequest,
    service: SatelliteGnbMappingService = Depends(get_satellite_service)
):
    """獲取衛星軌道預測"""
    try:
        # 構建觀測者位置
        observer_position = None
        if all(x is not None for x in [request.observer_lat, request.observer_lon]):
            observer_position = UAVPosition(
                latitude=request.observer_lat,
                longitude=request.observer_lon,
                altitude=request.observer_alt or 0
            )

        # 獲取軌道預測
        orbit_data = await service.get_satellite_orbit_prediction(
            satellite_id=int(request.satellite_id),
            time_range_hours=request.time_range_hours,
            step_seconds=request.step_seconds,
            observer_position=observer_position
        )

        logger.info(
            "軌道預測請求完成",
            satellite_id=request.satellite_id,
            time_range_hours=request.time_range_hours,
            data_points=len(orbit_data.get("positions", []))
        )

        return {
            "success": True,
            "satellite_id": request.satellite_id,
            "orbit_data": orbit_data,
            "request_params": {
                "time_range_hours": request.time_range_hours,
                "step_seconds": request.step_seconds,
                "has_observer": observer_position is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("軌道預測失敗", error=str(e), satellite_id=request.satellite_id)
        raise HTTPException(status_code=500, detail=f"軌道預測失敗: {str(e)}")


@router.post("/positions/batch",
             summary="批量獲取衛星位置",
             description="批量獲取多個衛星的即時位置")
async def get_batch_satellite_positions(
    request: BatchPositionRequest,
    bridge_service: SimWorldTLEBridgeService = Depends(get_tle_bridge_service)
):
    """批量獲取衛星位置"""
    try:
        # 構建觀測者位置
        observer_location = None
        if all(x is not None for x in [request.observer_lat, request.observer_lon]):
            observer_location = {
                "lat": request.observer_lat,
                "lon": request.observer_lon,
                "alt": (request.observer_alt or 0) / 1000  # 轉換為公里
            }

        # 獲取批量位置
        positions = await bridge_service.get_batch_satellite_positions(
            satellite_ids=request.satellite_ids,
            timestamp=request.timestamp,
            observer_location=observer_location
        )

        # 統計成功和失敗數量
        success_count = sum(1 for pos in positions.values() if pos.get("success"))
        failed_count = len(positions) - success_count

        logger.info(
            "批量位置獲取完成",
            requested_count=len(request.satellite_ids),
            success_count=success_count,
            failed_count=failed_count
        )

        return {
            "success": True,
            "positions": positions,
            "statistics": {
                "requested_count": len(request.satellite_ids),
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count / len(request.satellite_ids) if request.satellite_ids else 0
            },
            "request_params": {
                "timestamp": request.timestamp.isoformat() if request.timestamp else None,
                "has_observer": observer_location is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("批量位置獲取失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"批量位置獲取失敗: {str(e)}")


@router.post("/handover/predict",
             summary="預測切換時機",
             description="預測 UE 的衛星切換時機")
async def predict_handover_timing(
    request: HandoverPredictionRequest,
    service: SatelliteGnbMappingService = Depends(get_satellite_service)
):
    """預測切換時機"""
    try:
        # 構建 UE 位置
        ue_position = UAVPosition(
            latitude=request.ue_lat,
            longitude=request.ue_lon,
            altitude=request.ue_alt
        )

        # 轉換衛星 ID 為整數
        current_satellite_int = int(request.current_satellite)
        candidate_satellites_int = [int(sid) for sid in request.candidate_satellites]

        # 執行切換預測
        prediction_result = await service.predict_handover_timing(
            ue_id=request.ue_id,
            ue_position=ue_position,
            current_satellite=current_satellite_int,
            candidate_satellites=candidate_satellites_int,
            search_range_seconds=request.search_range_seconds
        )

        logger.info(
            "切換時機預測完成",
            ue_id=request.ue_id,
            current_satellite=request.current_satellite,
            predicted_handovers=len(prediction_result.get("handover_predictions", []))
        )

        return {
            "success": True,
            "prediction_result": prediction_result,
            "request_params": {
                "ue_id": request.ue_id,
                "current_satellite": request.current_satellite,
                "candidate_count": len(request.candidate_satellites),
                "search_range_seconds": request.search_range_seconds
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("切換時機預測失敗", error=str(e), ue_id=request.ue_id)
        raise HTTPException(status_code=500, detail=f"切換時機預測失敗: {str(e)}")


@router.post("/handover/binary-search",
             summary="二分搜尋切換時間",
             description="使用二分搜尋算法計算精確的切換時間點")
async def binary_search_handover_time(
    request: BinarySearchHandoverRequest,
    bridge_service: SimWorldTLEBridgeService = Depends(get_tle_bridge_service)
):
    """二分搜尋切換時間"""
    try:
        # 構建 UE 位置
        ue_position = {
            "lat": request.ue_lat,
            "lon": request.ue_lon,
            "alt": request.ue_alt / 1000  # 轉換為公里
        }

        # 執行二分搜尋
        handover_time = await bridge_service.binary_search_handover_time(
            ue_id=request.ue_id,
            ue_position=ue_position,
            source_satellite=request.source_satellite,
            target_satellite=request.target_satellite,
            t_start=request.search_start_timestamp,
            t_end=request.search_end_timestamp,
            precision_seconds=request.precision_seconds
        )

        # 計算相關時間資訊
        current_time = datetime.utcnow().timestamp()
        time_to_handover = handover_time - current_time
        search_duration = request.search_end_timestamp - request.search_start_timestamp

        logger.info(
            "二分搜尋切換時間完成",
            ue_id=request.ue_id,
            source_satellite=request.source_satellite,
            target_satellite=request.target_satellite,
            handover_time=datetime.fromtimestamp(handover_time).isoformat(),
            time_to_handover_seconds=time_to_handover
        )

        return {
            "success": True,
            "handover_time": datetime.fromtimestamp(handover_time).isoformat(),
            "handover_timestamp": handover_time,
            "time_to_handover_seconds": time_to_handover,
            "search_info": {
                "search_start": datetime.fromtimestamp(request.search_start_timestamp).isoformat(),
                "search_end": datetime.fromtimestamp(request.search_end_timestamp).isoformat(),
                "search_duration_seconds": search_duration,
                "precision_achieved_seconds": request.precision_seconds
            },
            "ue_info": {
                "ue_id": request.ue_id,
                "position": {
                    "lat": request.ue_lat,
                    "lon": request.ue_lon,
                    "alt": request.ue_alt
                }
            },
            "satellite_info": {
                "source_satellite": request.source_satellite,
                "target_satellite": request.target_satellite
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("二分搜尋切換時間失敗", error=str(e), ue_id=request.ue_id)
        raise HTTPException(status_code=500, detail=f"二分搜尋切換時間失敗: {str(e)}")


@router.post("/cache/preload",
             summary="預載衛星軌道資料",
             description="批量預載衛星軌道預測資料到快取")
async def preload_orbit_cache(
    request: CacheManagementRequest,
    bridge_service: SimWorldTLEBridgeService = Depends(get_tle_bridge_service)
):
    """預載軌道快取"""
    try:
        # 執行批量快取
        cache_result = await bridge_service.cache_orbit_predictions(
            satellite_ids=request.satellite_ids,
            time_range_hours=request.time_range_hours,
            step_seconds=request.step_seconds
        )

        logger.info(
            "軌道快取預載完成",
            satellite_count=len(request.satellite_ids),
            cached_count=cache_result.get("cached_count"),
            failed_count=cache_result.get("failed_count")
        )

        return {
            "success": True,
            "cache_result": cache_result,
            "request_params": {
                "satellite_count": len(request.satellite_ids),
                "time_range_hours": request.time_range_hours,
                "step_seconds": request.step_seconds
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("軌道快取預載失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"軌道快取預載失敗: {str(e)}")


@router.post("/critical/preload",
             summary="預載關鍵衛星資料",
             description="預載關鍵衛星的完整資料以確保低延遲存取")
async def preload_critical_satellites(
    satellite_ids: List[str],
    service: SatelliteGnbMappingService = Depends(get_satellite_service)
):
    """預載關鍵衛星資料"""
    try:
        # 轉換衛星 ID 為整數
        satellite_ids_int = [int(sid) for sid in satellite_ids]

        # 執行關鍵衛星預載
        preload_result = await service.preload_critical_satellites(satellite_ids_int)

        logger.info(
            "關鍵衛星預載完成",
            critical_count=len(satellite_ids),
            preloaded_count=preload_result.get("preloaded_satellites"),
            success_count=preload_result.get("position_success_count")
        )

        return {
            "success": True,
            "preload_result": preload_result,
            "critical_satellites": satellite_ids,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("關鍵衛星預載失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"關鍵衛星預載失敗: {str(e)}")


@router.post("/tle/sync",
             summary="同步 TLE 資料",
             description="從 SimWorld 同步最新的 TLE 資料")
async def sync_tle_data(
    service: SatelliteGnbMappingService = Depends(get_satellite_service)
):
    """同步 TLE 資料"""
    try:
        sync_result = await service.sync_tle_data()

        logger.info(
            "TLE 資料同步完成",
            success=sync_result.get("success"),
            synchronized_count=sync_result.get("synchronized_count")
        )

        return {
            "success": True,
            "sync_result": sync_result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("TLE 資料同步失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"TLE 資料同步失敗: {str(e)}")


@router.get("/tle/health",
            response_model=TLEHealthCheckResponse,
            summary="TLE 健康檢查",
            description="檢查 TLE 資料和 SimWorld 連接的健康狀態")
async def tle_health_check(
    service: SatelliteGnbMappingService = Depends(get_satellite_service)
):
    """TLE 健康檢查"""
    try:
        health_status = await service.get_tle_health_status()

        logger.debug(
            "TLE 健康檢查完成",
            simworld_status=health_status.get("simworld_status"),
            success=health_status.get("success")
        )

        return TLEHealthCheckResponse(**health_status)

    except Exception as e:
        logger.error("TLE 健康檢查失敗", error=str(e))
        return TLEHealthCheckResponse(
            success=False,
            simworld_status="error",
            error=str(e),
            check_time=datetime.utcnow().isoformat()
        )


@router.get("/status",
            summary="服務狀態總覽",
            description="獲取 TLE 橋接服務的整體狀態")
async def get_service_status(
    service: SatelliteGnbMappingService = Depends(get_satellite_service),
    bridge_service: SimWorldTLEBridgeService = Depends(get_tle_bridge_service)
):
    """獲取服務狀態"""
    try:
        # 獲取 TLE 健康狀態
        tle_health = await service.get_tle_health_status()

        # 檢查服務可用性
        satellite_service_available = True
        bridge_service_available = True

        try:
            # 測試衛星服務（獲取一個測試位置）
            test_positions = await bridge_service.get_batch_satellite_positions(
                ["1"], timestamp=datetime.utcnow()
            )
        except:
            bridge_service_available = False

        status_info = {
            "service_status": {
                "satellite_gnb_mapping": {
                    "available": satellite_service_available,
                    "service_name": "SatelliteGnbMappingService"
                },
                "tle_bridge": {
                    "available": bridge_service_available,
                    "service_name": "SimWorldTLEBridgeService"
                }
            },
            "simworld_connection": {
                "status": tle_health.get("simworld_status"),
                "success": tle_health.get("success"),
                "last_check": tle_health.get("check_time")
            },
            "overall_health": {
                "healthy": (
                    satellite_service_available and 
                    bridge_service_available and 
                    tle_health.get("success", False)
                ),
                "services_online": (
                    int(satellite_service_available) + 
                    int(bridge_service_available)
                ),
                "total_services": 2
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return status_info

    except Exception as e:
        logger.error("獲取服務狀態失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取服務狀態失敗: {str(e)}")


# Health check endpoint
@router.get("/health",
            summary="簡單健康檢查",
            description="檢查 TLE 橋接服務的基本健康狀態")
async def health_check():
    """健康檢查"""
    try:
        # 簡單的健康檢查
        return JSONResponse(
            content={
                "healthy": True,
                "service": "satellite-tle-bridge",
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=200
        )
    except Exception as e:
        logger.error("健康檢查失敗", error=str(e))
        return JSONResponse(
            content={
                "healthy": False,
                "service": "satellite-tle-bridge",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )