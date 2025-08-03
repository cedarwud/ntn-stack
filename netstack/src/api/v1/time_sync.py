"""
Phase 3.1.3: 時間同步和頻率補償 API 端點

提供時間同步和頻率補償的 RESTful API 接口，包括：
- 時間同步控制和監控
- 頻率基準管理
- 都卜勒補償配置
- GNSS/NTP 時間源管理
- 同步狀態查詢
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import logging

from src.protocols.sync.time_frequency_sync import (
    TimeFrequencySynchronizer,
    DopplerCompensator,
    TimeReference,
    FrequencyReference,
    DopplerParameters,
    TimeReferenceType,
    FrequencyBand,
    create_time_frequency_synchronizer,
    create_doppler_compensator,
    create_test_doppler_parameters
)

logger = logging.getLogger(__name__)

# 全局時間頻率同步器實例
time_sync_instance: Optional[TimeFrequencySynchronizer] = None

# Pydantic 模型定義
class SyncConfigRequest(BaseModel):
    """同步配置請求模型"""
    time_sync_interval: Optional[int] = Field(None, description="時間同步間隔 (秒)")
    freq_sync_interval: Optional[int] = Field(None, description="頻率同步間隔 (秒)")
    doppler_update_interval: Optional[int] = Field(None, description="都卜勒更新間隔 (秒)")
    max_time_offset_ns: Optional[float] = Field(None, description="最大時間偏移 (奈秒)")
    max_freq_offset_hz: Optional[float] = Field(None, description="最大頻率偏移 (Hz)")
    primary_time_source: Optional[str] = Field(None, description="主要時間源")
    backup_time_source: Optional[str] = Field(None, description="備用時間源")

class DopplerCompensatorRequest(BaseModel):
    """都卜勒補償器請求模型"""
    satellite_id: str = Field(..., description="衛星ID")
    carrier_frequency_hz: float = Field(..., description="載波頻率 (Hz)")
    prediction_window_s: Optional[int] = Field(60, description="預測窗口 (秒)")
    max_compensation_hz: Optional[float] = Field(50000, description="最大補償範圍 (Hz)")

class DopplerParametersRequest(BaseModel):
    """都卜勒參數請求模型"""
    satellite_id: str = Field(..., description="衛星ID")
    satellite_velocity: List[float] = Field(..., description="衛星速度 [vx, vy, vz] (km/s)")
    satellite_position: List[float] = Field(..., description="衛星位置 [x, y, z] (km)")
    observer_position: List[float] = Field(..., description="觀測點位置 [lat, lon, alt]")
    carrier_frequency_hz: float = Field(..., description="載波頻率 (Hz)")

class FrequencyReferenceRequest(BaseModel):
    """頻率基準請求模型"""
    reference_id: str = Field(..., description="頻率基準ID")
    center_frequency_hz: float = Field(..., description="中心頻率 (Hz)")
    frequency_band: str = Field(..., description="頻段類型")
    stability_ppb: float = Field(..., description="穩定度 (十億分之一)")
    accuracy_ppb: float = Field(..., description="精度 (十億分之一)")
    temperature_coefficient: Optional[float] = Field(0.1, description="溫度係數 (ppm/°C)")
    aging_rate: Optional[float] = Field(0.5, description="老化率 (ppb/年)")

# API Router
router = APIRouter(prefix="/api/v1/time-sync", tags=["Time Frequency Synchronization"])

@router.on_event("startup")
async def initialize_time_synchronizer():
    """初始化時間頻率同步器"""
    global time_sync_instance
    try:
        time_sync_instance = await create_time_frequency_synchronizer()
        await time_sync_instance.start_synchronizer()
        logger.info("✅ 時間頻率同步器初始化成功")
    except Exception as e:
        logger.error(f"❌ 時間頻率同步器初始化失敗: {e}")
        raise

@router.on_event("shutdown")
async def shutdown_time_synchronizer():
    """關閉時間頻率同步器"""
    global time_sync_instance
    if time_sync_instance:
        await time_sync_instance.stop_synchronizer()
        logger.info("⏹️ 時間頻率同步器已關閉")

async def get_time_synchronizer() -> TimeFrequencySynchronizer:
    """獲取時間頻率同步器實例"""
    global time_sync_instance
    if time_sync_instance is None:
        time_sync_instance = await create_time_frequency_synchronizer()
        await time_sync_instance.start_synchronizer()
    return time_sync_instance

# === 同步控制端點 ===

@router.post("/synchronizer/start", summary="Start Time Frequency Synchronizer")
async def start_time_synchronizer() -> JSONResponse:
    """啟動時間頻率同步器"""
    try:
        synchronizer = await get_time_synchronizer()
        await synchronizer.start_synchronizer()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "時間頻率同步器已啟動",
                "is_running": synchronizer.is_running,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 啟動時間頻率同步器失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synchronizer/stop", summary="Stop Time Frequency Synchronizer")
async def stop_time_synchronizer() -> JSONResponse:
    """停止時間頻率同步器"""
    try:
        synchronizer = await get_time_synchronizer()
        await synchronizer.stop_synchronizer()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "時間頻率同步器已停止",
                "is_running": synchronizer.is_running,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 停止時間頻率同步器失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", summary="Get Synchronization Status")
async def get_sync_status() -> JSONResponse:
    """獲取同步狀態"""
    try:
        synchronizer = await get_time_synchronizer()
        status = synchronizer.get_sync_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "sync_status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取同步狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 配置管理端點 ===

@router.put("/config", summary="Update Synchronization Configuration")
async def update_sync_config(request: SyncConfigRequest) -> JSONResponse:
    """更新同步配置"""
    try:
        synchronizer = await get_time_synchronizer()
        
        # 構建配置更新字典
        config_updates = {}
        if request.time_sync_interval is not None:
            config_updates['time_sync_interval'] = request.time_sync_interval
        if request.freq_sync_interval is not None:
            config_updates['freq_sync_interval'] = request.freq_sync_interval
        if request.doppler_update_interval is not None:
            config_updates['doppler_update_interval'] = request.doppler_update_interval
        if request.max_time_offset_ns is not None:
            config_updates['max_time_offset_ns'] = request.max_time_offset_ns
        if request.max_freq_offset_hz is not None:
            config_updates['max_freq_offset_hz'] = request.max_freq_offset_hz
        if request.primary_time_source is not None:
            try:
                config_updates['primary_time_source'] = TimeReferenceType(request.primary_time_source)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無效的時間源類型: {request.primary_time_source}")
        if request.backup_time_source is not None:
            try:
                config_updates['backup_time_source'] = TimeReferenceType(request.backup_time_source)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無效的時間源類型: {request.backup_time_source}")
        
        if config_updates:
            synchronizer.update_sync_config(config_updates)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "同步配置已更新",
                "updated_fields": list(config_updates.keys()),
                "current_config": {
                    k: v.value if isinstance(v, TimeReferenceType) else v
                    for k, v in synchronizer.sync_config.items()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 更新同步配置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", summary="Get Synchronization Configuration")
async def get_sync_config() -> JSONResponse:
    """獲取同步配置"""
    try:
        synchronizer = await get_time_synchronizer()
        
        config = synchronizer.sync_config.copy()
        # 轉換枚舉值為字符串
        for key, value in config.items():
            if isinstance(value, TimeReferenceType):
                config[key] = value.value
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "sync_config": config
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取同步配置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 都卜勒補償管理端點 ===

@router.post("/doppler/compensators", summary="Add Doppler Compensator")
async def add_doppler_compensator(request: DopplerCompensatorRequest) -> JSONResponse:
    """添加都卜勒補償器"""
    try:
        synchronizer = await get_time_synchronizer()
        
        # 創建都卜勒補償器
        compensator = create_doppler_compensator(
            request.satellite_id,
            request.carrier_frequency_hz
        )
        
        # 更新配置
        if request.prediction_window_s:
            compensator.config['prediction_window_s'] = request.prediction_window_s
        if request.max_compensation_hz:
            compensator.config['max_compensation_hz'] = request.max_compensation_hz
        
        synchronizer.add_doppler_compensator(request.satellite_id, compensator)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"都卜勒補償器已添加: {request.satellite_id}",
                "satellite_id": request.satellite_id,
                "carrier_frequency_hz": request.carrier_frequency_hz,
                "total_compensators": len(synchronizer.doppler_compensators)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 添加都卜勒補償器失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/doppler/compensators/{satellite_id}", summary="Remove Doppler Compensator")
async def remove_doppler_compensator(satellite_id: str) -> JSONResponse:
    """移除都卜勒補償器"""
    try:
        synchronizer = await get_time_synchronizer()
        synchronizer.remove_doppler_compensator(satellite_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"都卜勒補償器已移除: {satellite_id}",
                "satellite_id": satellite_id,
                "total_compensators": len(synchronizer.doppler_compensators)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 移除都卜勒補償器失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/doppler/compensators", summary="Get All Doppler Compensators")
async def get_doppler_compensators() -> JSONResponse:
    """獲取所有都卜勒補償器"""
    try:
        synchronizer = await get_time_synchronizer()
        
        compensators_info = []
        for satellite_id, compensator in synchronizer.doppler_compensators.items():
            info = compensator.get_compensation_info()
            compensators_info.append(info)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "total_compensators": len(compensators_info),
                "compensators": compensators_info
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取都卜勒補償器列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/doppler/parameters/{satellite_id}", summary="Update Doppler Parameters")
async def update_doppler_parameters(satellite_id: str, request: DopplerParametersRequest) -> JSONResponse:
    """更新都卜勒參數"""
    try:
        synchronizer = await get_time_synchronizer()
        
        if satellite_id not in synchronizer.doppler_compensators:
            raise HTTPException(status_code=404, detail=f"找不到衛星 {satellite_id} 的都卜勒補償器")
        
        # 創建都卜勒參數
        doppler_params = DopplerParameters(
            satellite_id=request.satellite_id,
            satellite_velocity=tuple(request.satellite_velocity),
            satellite_position=tuple(request.satellite_position),
            observer_position=tuple(request.observer_position),
            carrier_frequency_hz=request.carrier_frequency_hz,
            timestamp=datetime.now(timezone.utc)
        )
        
        # 更新補償器參數
        compensator = synchronizer.doppler_compensators[satellite_id]
        await compensator.update_doppler_parameters(doppler_params)
        
        # 獲取更新後的補償信息
        compensation_info = compensator.get_compensation_info()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"都卜勒參數已更新: {satellite_id}",
                "satellite_id": satellite_id,
                "doppler_shift_hz": doppler_params.calculate_doppler_shift(),
                "compensation_info": compensation_info
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 更新都卜勒參數失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 頻率基準管理端點 ===

@router.post("/frequency/references", summary="Add Frequency Reference")
async def add_frequency_reference(request: FrequencyReferenceRequest) -> JSONResponse:
    """添加頻率基準"""
    try:
        synchronizer = await get_time_synchronizer()
        
        # 驗證頻段類型
        try:
            freq_band = FrequencyBand(request.frequency_band.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的頻段類型: {request.frequency_band}")
        
        # 創建頻率基準
        freq_ref = FrequencyReference(
            center_frequency_hz=request.center_frequency_hz,
            frequency_band=freq_band,
            stability_ppb=request.stability_ppb,
            accuracy_ppb=request.accuracy_ppb,
            temperature_coefficient=request.temperature_coefficient,
            aging_rate=request.aging_rate,
            timestamp=datetime.now(timezone.utc)
        )
        
        synchronizer.frequency_references[request.reference_id] = freq_ref
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"頻率基準已添加: {request.reference_id}",
                "reference_id": request.reference_id,
                "center_frequency_hz": request.center_frequency_hz,
                "frequency_band": request.frequency_band,
                "total_references": len(synchronizer.frequency_references)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 添加頻率基準失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/frequency/references", summary="Get All Frequency References")
async def get_frequency_references() -> JSONResponse:
    """獲取所有頻率基準"""
    try:
        synchronizer = await get_time_synchronizer()
        
        references_info = []
        for ref_id, freq_ref in synchronizer.frequency_references.items():
            ref_info = {
                "reference_id": ref_id,
                "center_frequency_hz": freq_ref.center_frequency_hz,
                "frequency_band": freq_ref.frequency_band.value,
                "stability_ppb": freq_ref.stability_ppb,
                "accuracy_ppb": freq_ref.accuracy_ppb,
                "temperature_coefficient": freq_ref.temperature_coefficient,
                "aging_rate": freq_ref.aging_rate,
                "timestamp": freq_ref.timestamp.isoformat()
            }
            references_info.append(ref_info)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "total_references": len(references_info),
                "frequency_references": references_info
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取頻率基準列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 健康檢查端點 ===

@router.get("/health", summary="Time Sync Health Check")
async def health_check() -> JSONResponse:
    """時間同步系統健康檢查"""
    try:
        synchronizer = await get_time_synchronizer()
        status = synchronizer.get_sync_status()
        
        health_status = "healthy" if status["is_synchronized"] else "degraded"
        status_code = 200 if status["is_synchronized"] else 206
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": health_status,
                "is_running": status["is_synchronized"],
                "time_sync_achieved": status["time_sync_achieved"],
                "frequency_sync_achieved": status["frequency_sync_achieved"],
                "active_compensators": status["active_compensators"],
                "quality_indicator": status["quality_indicator"],
                "sync_source": status["sync_source"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 時間同步健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# === 測試端點 ===

@router.post("/test/add-test-doppler-compensators", summary="Add Test Doppler Compensators")
async def add_test_doppler_compensators() -> JSONResponse:
    """添加測試用的都卜勒補償器"""
    try:
        synchronizer = await get_time_synchronizer()
        
        test_satellites = [
            ("STARLINK-TEST-1", 2.0e9),
            ("STARLINK-TEST-2", 2.1e9),
            ("STARLINK-TEST-3", 1.9e9)
        ]
        
        added_compensators = []
        for sat_id, freq in test_satellites:
            compensator = create_doppler_compensator(sat_id, freq)
            synchronizer.add_doppler_compensator(sat_id, compensator)
            
            # 添加測試都卜勒參數
            test_params = create_test_doppler_parameters(sat_id)
            await compensator.update_doppler_parameters(test_params)
            
            added_compensators.append({
                "satellite_id": sat_id,
                "carrier_frequency_hz": freq,
                "doppler_shift_hz": test_params.calculate_doppler_shift()
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"已添加 {len(test_satellites)} 個測試都卜勒補償器",
                "compensators": added_compensators,
                "total_compensators": len(synchronizer.doppler_compensators)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 添加測試都卜勒補償器失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/trigger-sync", summary="Trigger Manual Synchronization")
async def trigger_manual_sync() -> JSONResponse:
    """手動觸發同步"""
    try:
        synchronizer = await get_time_synchronizer()
        
        # 手動執行同步週期
        await synchronizer._perform_time_sync()
        await synchronizer._perform_frequency_sync()
        await synchronizer._update_doppler_compensation()
        
        # 獲取同步後狀態
        status = synchronizer.get_sync_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "手動同步已完成",
                "sync_status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 手動觸發同步失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加到主 app 的函數
def include_time_sync_router(app):
    """將時間同步 router 添加到主應用"""
    app.include_router(router)
    logger.info("✅ 時間同步 API 路由已添加")