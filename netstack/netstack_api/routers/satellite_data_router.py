"""
衛星數據路由器 - 真實數據版本
提供基於真實 TLE 數據和軌道計算的衛星數據管理 API
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
import structlog

logger = structlog.get_logger(__name__)

from ..services.satellite_data_manager import (
    SatelliteDataManager,
    D2ScenarioConfig as SDMConfig,
    SatelliteInfo as SDMSatelliteInfo,
)
from ..data.historical_tle_data import get_data_source_info

# 路由器實例
router = APIRouter(prefix="/api/satellite-data", tags=["衛星數據"])

# 全局衛星數據管理器實例
_satellite_manager: Optional[SatelliteDataManager] = None


# 請求/響應模型
class TLEUpdateRequest(BaseModel):
    constellation: str
    force_update: bool = False


class TLEUpdateResponse(BaseModel):
    constellation: str
    satellites_updated: int
    satellites_added: int
    satellites_failed: int
    duration_seconds: float
    errors: List[str]


class SatelliteInfo(BaseModel):
    satellite_id: str
    satellite_name: str
    norad_id: int
    constellation: str
    is_active: bool
    orbital_period: float
    last_updated: str


class UEPosition(BaseModel):
    latitude: float
    longitude: float
    altitude: float


class FixedRefPosition(BaseModel):
    latitude: float
    longitude: float
    altitude: float


class D2MeasurementConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scenario_name: str
    constellation: str
    ue_position: UEPosition
    fixed_ref_position: FixedRefPosition
    thresh1: float
    thresh2: float
    hysteresis: float
    duration_minutes: int
    sample_interval_seconds: int


class D2PrecomputeResponse(BaseModel):
    scenario_name: str
    scenario_hash: str
    measurements_generated: int
    satellites_processed: int
    duration_seconds: float
    errors: List[str]


async def get_satellite_manager() -> SatelliteDataManager:
    """獲取衛星數據管理器實例"""
    global _satellite_manager
    
    if _satellite_manager is None:
        # 從環境變量獲取數據庫連接字串
        db_url = os.getenv("SATELLITE_DATABASE_URL", "postgresql://netstack_user:netstack_password@netstack-postgres:5432/netstack_db")
        
        _satellite_manager = SatelliteDataManager(db_url)
        await _satellite_manager.initialize()
        logger.info("🛰️ 衛星數據管理器初始化完成")
    
    return _satellite_manager




# API 端點
@router.get("/health")
async def health_check():
    """健康檢查"""
    try:
        manager = await get_satellite_manager()
        return {
            "status": "healthy",
            "service": "satellite-data",
            "timestamp": datetime.now().isoformat(),
            "database_connected": manager.db_pool is not None,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "satellite-data", 
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@router.post("/tle/update", response_model=TLEUpdateResponse)
async def update_tle_data(request: TLEUpdateRequest):
    """更新 TLE 數據"""
    try:
        manager = await get_satellite_manager()
        result = await manager.update_tle_data(request.constellation)
        
        return TLEUpdateResponse(
            constellation=result["constellation"],
            satellites_updated=result.get("satellites_updated", 0),
            satellites_added=result.get("satellites_added", 0),
            satellites_failed=result.get("satellites_failed", 0),
            duration_seconds=result.get("duration_seconds", 0.0),
            errors=result.get("errors", [])
        )
    except Exception as e:
        logger.error(f"❌ TLE 更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/constellations/{constellation}/satellites")
async def get_satellites(constellation: str, limit: int = 100):
    """獲取指定星座的衛星列表"""
    try:
        manager = await get_satellite_manager()
        satellites = await manager.get_active_satellites(constellation)
        
        # 限制返回數量
        limited_satellites = satellites[:limit]
        
        result = []
        for sat in limited_satellites:
            result.append({
                "satellite_id": sat.satellite_id,
                "norad_id": sat.norad_id,
                "satellite_name": sat.satellite_name,
                "constellation": sat.constellation,
                "is_active": sat.is_active,
                "orbital_period": sat.orbital_period,
                "last_updated": sat.last_updated.isoformat(),
            })
        
        # 添加數據來源信息
        data_source_info = get_data_source_info()
        
        return {
            "satellites": result,
            "data_source": data_source_info,
            "constellation": constellation,
            "total_count": len(satellites),
            "returned_count": len(result)
        }
    except Exception as e:
        logger.error(f"❌ 獲取衛星列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/constellations/{constellation}/tle")
async def get_constellation_tle_data(constellation: str, limit: int = 100):
    """獲取指定星座的歷史 TLE 數據 - 直接從歷史數據模組"""
    from ..data.historical_tle_data import get_historical_tle_data, get_data_source_info
    
    try:
        # 直接從歷史數據獲取 TLE 數據
        tle_data = get_historical_tle_data(constellation)
        
        if not tle_data:
            raise HTTPException(status_code=404, detail=f"No TLE data found for constellation: {constellation}")
        
        # 限制返回數量
        limited_data = tle_data[:limit]
        
        # 格式化響應
        result = []
        for tle_entry in limited_data:
            result.append({
                "satellite_name": tle_entry["name"],
                "norad_id": tle_entry["norad_id"],
                "constellation": tle_entry["constellation"],
                "line1": tle_entry["line1"],
                "line2": tle_entry["line2"],
                "launch_date": tle_entry.get("launch_date", "unknown")
            })
        
        # 數據來源信息
        data_source_info = get_data_source_info()
        
        return {
            "satellites": result,
            "data_source": data_source_info,
            "constellation": constellation,
            "total_count": len(tle_data),
            "returned_count": len(result)
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取 {constellation} TLE 數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/d2/precompute", response_model=D2PrecomputeResponse)
async def precompute_d2_measurements(config: D2MeasurementConfig):
    """預計算 D2 測量數據"""
    try:
        manager = await get_satellite_manager()
        
        # 轉換為內部配置格式
        scenario_config = SDMConfig(
            scenario_name=config.scenario_name,
            ue_position={
                "latitude": config.ue_position.latitude,
                "longitude": config.ue_position.longitude,
                "altitude": config.ue_position.altitude,
            },
            fixed_ref_position={
                "latitude": config.fixed_ref_position.latitude,
                "longitude": config.fixed_ref_position.longitude,
                "altitude": config.fixed_ref_position.altitude,
            },
            thresh1=config.thresh1,
            thresh2=config.thresh2,
            hysteresis=config.hysteresis,
            constellation=config.constellation,
            duration_minutes=config.duration_minutes,
            sample_interval_seconds=config.sample_interval_seconds,
        )
        
        result = await manager.precompute_d2_measurements(scenario_config)
        
        return D2PrecomputeResponse(
            scenario_name=result["scenario_name"],
            scenario_hash=result["scenario_hash"],
            measurements_generated=result.get("measurements_generated", 0),
            satellites_processed=result.get("satellites_processed", 0),
            duration_seconds=result.get("duration_seconds", 0.0),
            errors=result.get("errors", [])
        )
    except Exception as e:
        logger.error(f"❌ D2 預計算失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/d2/measurements/{scenario_hash}")
async def get_d2_measurements(scenario_hash: str, limit: int = 1000):
    """獲取 D2 測量數據"""
    try:
        manager = await get_satellite_manager()
        measurement_points = await manager.get_cached_d2_measurements(scenario_hash)
        
        # 限制返回數量
        limited_measurements = measurement_points[:limit]
        
        # 轉換為 API 響應格式
        measurements = []
        for point in limited_measurements:
            measurements.append({
                "timestamp": point.timestamp.isoformat(),
                "satellite_id": point.satellite_id,
                "constellation": point.constellation,
                "satellite_distance": point.satellite_distance,
                "ground_distance": point.ground_distance,
                "satellite_position": point.satellite_position,
                "trigger_condition_met": point.trigger_condition_met,
                "event_type": point.event_type,
            })
        
        return {
            "scenario_hash": scenario_hash,
            "measurement_count": len(measurements),
            "measurements": measurements,
        }
    except Exception as e:
        logger.error(f"❌ 獲取 D2 測量數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/constellations")
async def get_supported_constellations():
    """獲取支持的衛星星座列表"""
    try:
        manager = await get_satellite_manager()
        
        # 支持的星座列表
        supported = ["starlink", "oneweb", "gps", "galileo"]
        
        # 統計各星座的衛星數量
        constellation_info = []
        for constellation in supported:
            try:
                satellites = await manager.get_active_satellites(constellation)
                constellation_info.append({
                    "name": constellation,
                    "satellite_count": len(satellites),
                    "active_satellites": sum(1 for s in satellites if s.is_active),
                })
            except:
                constellation_info.append({
                    "name": constellation,
                    "satellite_count": 0,
                    "active_satellites": 0,
                })
        
        # 添加數據來源信息
        data_source_info = get_data_source_info()
        
        return {
            "constellations": constellation_info,
            "data_source": data_source_info
        }
    except Exception as e:
        logger.error(f"❌ 獲取星座列表失敗: {e}")
        # 返回基本列表作為後備
        fallback_constellations = [
            {"name": "starlink", "satellite_count": 0, "active_satellites": 0},
            {"name": "oneweb", "satellite_count": 0, "active_satellites": 0},
            {"name": "gps", "satellite_count": 0, "active_satellites": 0},
            {"name": "galileo", "satellite_count": 0, "active_satellites": 0},
        ]
        
        return {
            "constellations": fallback_constellations,
            "data_source": {
                "type": "fallback_empty",
                "description": "數據獲取失敗，返回空數據",
                "is_simulation": True
            }
        }



