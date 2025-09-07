"""
Phase 3.1.2: SIB19 廣播機制 API 端點

提供衛星位置資訊廣播的 RESTful API 接口，包括：
- SIB19 廣播控制和監控
- 衛星星曆管理
- 可見衛星查詢
- 廣播調度配置
- 緊急廣播觸發
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

from src.protocols.sib19_broadcast import (
    SIB19BroadcastScheduler,
    SatelliteEphemeris,
    SIB19BroadcastType,
    create_sib19_broadcast_scheduler,
    create_test_satellite_ephemeris
)

logger = logging.getLogger(__name__)

# 全局 SIB19 廣播調度器實例
sib19_scheduler: Optional[SIB19BroadcastScheduler] = None

# Pydantic 模型定義
class SatelliteEphemerisRequest(BaseModel):
    """衛星星曆請求模型"""
    satellite_id: str = Field(..., description="衛星ID")
    norad_id: int = Field(..., description="NORAD ID")
    epoch_time: str = Field(..., description="曆元時間 (ISO format)")
    semi_major_axis: float = Field(..., description="半長軸 (km)")
    eccentricity: float = Field(..., description="偏心率")
    inclination: float = Field(..., description="軌道傾角 (度)")
    raan: float = Field(..., description="升交點赤經 (度)")
    argument_of_perigee: float = Field(..., description="近地點幅角 (度)")
    mean_anomaly: float = Field(..., description="平近點角 (度)")
    mean_motion: float = Field(..., description="平均運動 (revs/day)")
    latitude: Optional[float] = Field(0.0, description="當前緯度 (度)")
    longitude: Optional[float] = Field(0.0, description="當前經度 (度)")
    altitude: Optional[float] = Field(550.0, description="當前高度 (km)")

class ObserverLocationRequest(BaseModel):
    """觀測點位置請求模型"""
    latitude: float = Field(..., description="觀測點緯度 (度)")
    longitude: float = Field(..., description="觀測點經度 (度)")
    altitude: float = Field(0.1, description="觀測點高度 (km)")
    min_elevation: float = Field(5.0, description="最小仰角 (度)")

class BroadcastConfigRequest(BaseModel):
    """廣播配置請求模型"""
    periodic_interval: Optional[int] = Field(None, description="週期性廣播間隔 (秒)")
    validity_duration: Optional[int] = Field(None, description="消息有效期 (秒)")
    max_satellites_per_message: Optional[int] = Field(None, description="每條消息最大衛星數")
    emergency_priority: Optional[bool] = Field(None, description="緊急廣播優先")
    adaptive_scheduling: Optional[bool] = Field(None, description="自適應調度")

class EmergencyBroadcastRequest(BaseModel):
    """緊急廣播請求模型"""
    reason: str = Field(..., description="緊急廣播原因")
    priority: str = Field("high", description="優先級")

# API Router
router = APIRouter(prefix="/api/v1/sib19", tags=["SIB19 Satellite Broadcast"])

@router.on_event("startup")
async def initialize_sib19_scheduler():
    """初始化 SIB19 廣播調度器"""
    global sib19_scheduler
    try:
        sib19_scheduler = await create_sib19_broadcast_scheduler()
        await sib19_scheduler.start_scheduler()
        logger.info("✅ SIB19 廣播調度器初始化成功")
    except Exception as e:
        logger.error(f"❌ SIB19 廣播調度器初始化失敗: {e}")
        raise

@router.on_event("shutdown")
async def shutdown_sib19_scheduler():
    """關閉 SIB19 廣播調度器"""
    global sib19_scheduler
    if sib19_scheduler:
        await sib19_scheduler.stop_scheduler()
        logger.info("⏹️ SIB19 廣播調度器已關閉")

async def get_sib19_scheduler() -> SIB19BroadcastScheduler:
    """獲取 SIB19 廣播調度器實例"""
    global sib19_scheduler
    if sib19_scheduler is None:
        sib19_scheduler = await create_sib19_broadcast_scheduler()
        await sib19_scheduler.start_scheduler()
    return sib19_scheduler

# === 廣播控制端點 ===

@router.post("/broadcast/start", summary="Start SIB19 Broadcast Scheduler")
async def start_broadcast_scheduler() -> JSONResponse:
    """啟動 SIB19 廣播調度器"""
    try:
        scheduler = await get_sib19_scheduler()
        await scheduler.start_scheduler()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "SIB19 廣播調度器已啟動",
                "scheduler_running": scheduler.is_running,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 啟動 SIB19 廣播調度器失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast/stop", summary="Stop SIB19 Broadcast Scheduler")
async def stop_broadcast_scheduler() -> JSONResponse:
    """停止 SIB19 廣播調度器"""
    try:
        scheduler = await get_sib19_scheduler()
        await scheduler.stop_scheduler()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "SIB19 廣播調度器已停止",
                "scheduler_running": scheduler.is_running,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 停止 SIB19 廣播調度器失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast/emergency", summary="Trigger Emergency Broadcast")
async def trigger_emergency_broadcast(request: EmergencyBroadcastRequest) -> JSONResponse:
    """觸發緊急 SIB19 廣播"""
    try:
        scheduler = await get_sib19_scheduler()
        
        emergency_message = await scheduler.trigger_emergency_broadcast(request.reason)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "緊急 SIB19 廣播已觸發",
                "emergency_broadcast": {
                    "message_id": emergency_message.message_id,
                    "broadcast_time": emergency_message.broadcast_time.isoformat(),
                    "reason": request.reason,
                    "priority": request.priority,
                    "satellites_count": len(emergency_message.satellite_ephemeris_list),
                    "validity_duration": emergency_message.validity_duration
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 觸發緊急廣播失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 衛星管理端點 ===

@router.post("/satellites", summary="Add Satellite to Active List")
async def add_satellite(request: SatelliteEphemerisRequest) -> JSONResponse:
    """添加衛星到活動列表"""
    try:
        scheduler = await get_sib19_scheduler()
        
        # 創建衛星星曆對象
        ephemeris = SatelliteEphemeris(
            satellite_id=request.satellite_id,
            norad_id=request.norad_id,
            epoch_time=datetime.fromisoformat(request.epoch_time.replace('Z', '+00:00')),
            semi_major_axis=request.semi_major_axis,
            eccentricity=request.eccentricity,
            inclination=request.inclination,
            raan=request.raan,
            argument_of_perigee=request.argument_of_perigee,
            mean_anomaly=request.mean_anomaly,
            mean_motion=request.mean_motion,
            latitude=request.latitude,
            longitude=request.longitude,
            altitude=request.altitude
        )
        
        scheduler.add_satellite(ephemeris)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"衛星 {request.satellite_id} 已添加到活動列表",
                "satellite_id": request.satellite_id,
                "total_active_satellites": len(scheduler.active_satellites)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 添加衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/satellites/{satellite_id}", summary="Remove Satellite from Active List")
async def remove_satellite(satellite_id: str) -> JSONResponse:
    """從活動列表移除衛星"""
    try:
        scheduler = await get_sib19_scheduler()
        scheduler.remove_satellite(satellite_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"衛星 {satellite_id} 已從活動列表移除",
                "satellite_id": satellite_id,
                "total_active_satellites": len(scheduler.active_satellites)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 移除衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellites", summary="Get Active Satellites")
async def get_active_satellites() -> JSONResponse:
    """獲取活動衛星列表"""
    try:
        scheduler = await get_sib19_scheduler()
        
        active_satellites = []
        for satellite_id, ephemeris in scheduler.active_satellites.items():
            satellite_info = {
                "satellite_id": satellite_id,
                "norad_id": ephemeris.norad_id,
                "current_position": {
                    "latitude": ephemeris.latitude,
                    "longitude": ephemeris.longitude,
                    "altitude": ephemeris.altitude
                },
                "orbital_parameters": {
                    "inclination": ephemeris.inclination,
                    "raan": ephemeris.raan,
                    "mean_motion": ephemeris.mean_motion
                },
                "epoch_time": ephemeris.epoch_time.isoformat()
            }
            active_satellites.append(satellite_info)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "total_satellites": len(active_satellites),
                "satellites": active_satellites
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取活動衛星列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellites/visible", summary="Get Currently Visible Satellites")
async def get_visible_satellites() -> JSONResponse:
    """獲取當前可見衛星列表"""
    try:
        scheduler = await get_sib19_scheduler()
        visible_satellites = scheduler.get_current_visible_satellites()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "visible_satellites_count": len(visible_satellites),
                "observer_location": scheduler.observer_location,
                "satellites": visible_satellites,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取可見衛星列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 觀測點配置端點 ===

@router.put("/observer/location", summary="Update Observer Location")
async def update_observer_location(request: ObserverLocationRequest) -> JSONResponse:
    """更新觀測點位置"""
    try:
        scheduler = await get_sib19_scheduler()
        
        scheduler.update_observer_location(
            latitude=request.latitude,
            longitude=request.longitude,
            altitude=request.altitude,
            min_elevation=request.min_elevation
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "觀測點位置已更新",
                "observer_location": {
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "altitude": request.altitude,
                    "min_elevation": request.min_elevation
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 更新觀測點位置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/observer/location", summary="Get Observer Location")
async def get_observer_location() -> JSONResponse:
    """獲取當前觀測點位置"""
    try:
        scheduler = await get_sib19_scheduler()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "observer_location": scheduler.observer_location
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取觀測點位置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 廣播配置端點 ===

@router.put("/config", summary="Update Broadcast Configuration")
async def update_broadcast_config(request: BroadcastConfigRequest) -> JSONResponse:
    """更新廣播配置"""
    try:
        scheduler = await get_sib19_scheduler()
        
        # 更新配置
        if request.periodic_interval is not None:
            scheduler.broadcast_config['periodic_interval'] = request.periodic_interval
        if request.validity_duration is not None:
            scheduler.broadcast_config['validity_duration'] = request.validity_duration
        if request.max_satellites_per_message is not None:
            scheduler.broadcast_config['max_satellites_per_message'] = request.max_satellites_per_message
        if request.emergency_priority is not None:
            scheduler.broadcast_config['emergency_priority'] = request.emergency_priority
        if request.adaptive_scheduling is not None:
            scheduler.broadcast_config['adaptive_scheduling'] = request.adaptive_scheduling
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "廣播配置已更新",
                "broadcast_config": scheduler.broadcast_config
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 更新廣播配置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", summary="Get Broadcast Configuration")
async def get_broadcast_config() -> JSONResponse:
    """獲取廣播配置"""
    try:
        scheduler = await get_sib19_scheduler()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "broadcast_config": scheduler.broadcast_config
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取廣播配置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 廣播信息查詢端點 ===

@router.get("/messages/latest", summary="Get Latest SIB19 Message")
async def get_latest_sib19_message() -> JSONResponse:
    """獲取最新的 SIB19 廣播消息"""
    try:
        scheduler = await get_sib19_scheduler()
        latest_message = scheduler.get_latest_sib19_message()
        
        if latest_message:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "has_message": True,
                    "message": latest_message
                }
            )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "has_message": False,
                    "message": "無有效的 SIB19 廣播消息"
                }
            )
        
    except Exception as e:
        logger.error(f"❌ 獲取最新 SIB19 消息失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", summary="Get Broadcast Statistics")
async def get_broadcast_statistics() -> JSONResponse:
    """獲取廣播統計信息"""
    try:
        scheduler = await get_sib19_scheduler()
        stats = scheduler.get_broadcast_statistics()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "statistics": stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取廣播統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 健康檢查端點 ===

@router.get("/health", summary="SIB19 Broadcast Health Check")
async def health_check() -> JSONResponse:
    """SIB19 廣播系統健康檢查"""
    try:
        scheduler = await get_sib19_scheduler()
        stats = scheduler.get_broadcast_statistics()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "scheduler_running": stats["scheduler_running"],
                "active_satellites": stats["total_active_satellites"],
                "visible_satellites": stats["currently_visible_satellites"],
                "recent_broadcasts": stats["recent_broadcasts_1h"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ SIB19 廣播健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# === 測試端點 ===

@router.post("/test/satellites/add-starlink", summary="Add Test Starlink Satellites")
async def add_test_starlink_satellites() -> JSONResponse:
    """添加測試用的 Starlink 衛星"""
    try:
        scheduler = await get_sib19_scheduler()
        
        test_satellites = [
            create_test_satellite_ephemeris("STARLINK-1009", 44715),
            create_test_satellite_ephemeris("STARLINK-1010", 44716),
            create_test_satellite_ephemeris("STARLINK-1011", 44717)
        ]
        
        for satellite in test_satellites:
            scheduler.add_satellite(satellite)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"已添加 {len(test_satellites)} 顆測試 Starlink 衛星",
                "satellites": [sat.satellite_id for sat in test_satellites],
                "total_active_satellites": len(scheduler.active_satellites)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 添加測試衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/broadcast/trigger", summary="Trigger Test Broadcast")
async def trigger_test_broadcast() -> JSONResponse:
    """觸發測試廣播"""
    try:
        scheduler = await get_sib19_scheduler()
        
        # 手動觸發一次廣播循環
        await scheduler._periodic_broadcast_cycle()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "測試廣播已觸發",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 觸發測試廣播失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加到主 app 的函數
def include_sib19_broadcast_router(app):
    """將 SIB19 廣播 router 添加到主應用"""
    app.include_router(router)
    logger.info("✅ SIB19 廣播 API 路由已添加")