"""
軌道計算 API 路由
提供衛星軌道計算和位置預測服務
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import structlog

from ..services.orbit_calculation_engine import OrbitCalculationEngine
from ..services.tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/orbit", tags=["orbit"])

# 全局實例
_orbit_engine = None
_tle_manager = None

async def get_orbit_engine() -> OrbitCalculationEngine:
    """獲取軌道計算引擎實例"""
    global _orbit_engine
    if _orbit_engine is None:
        _orbit_engine = OrbitCalculationEngine()
    return _orbit_engine

async def get_tle_manager() -> TLEDataManager:
    """獲取 TLE 數據管理器實例"""
    global _tle_manager
    if _tle_manager is None:
        _tle_manager = TLEDataManager()
        await _tle_manager.initialize_default_sources()
    return _tle_manager

@router.get("/satellites")
async def get_available_satellites(
    orbit_engine: OrbitCalculationEngine = Depends(get_orbit_engine)
) -> Dict[str, Any]:
    """獲取可用的衛星列表"""
    try:
        satellites = orbit_engine.get_available_satellites()
        return {
            "satellites": satellites,
            "count": len(satellites),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取衛星列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellite/{satellite_id}/position")
async def get_satellite_position(
    satellite_id: str,
    timestamp: Optional[float] = None,
    orbit_engine: OrbitCalculationEngine = Depends(get_orbit_engine)
) -> Dict[str, Any]:
    """獲取指定衛星的位置"""
    try:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).timestamp()
        
        position = orbit_engine.calculate_satellite_position(satellite_id, timestamp)
        
        if position is None:
            raise HTTPException(status_code=404, detail=f"衛星 {satellite_id} 未找到")
        
        return {
            "satellite_id": satellite_id,
            "timestamp": timestamp,
            "position": position,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"計算衛星位置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellite/{satellite_id}/trajectory")
async def get_satellite_trajectory(
    satellite_id: str,
    start_time: Optional[float] = None,
    duration_hours: float = 24,
    step_minutes: float = 10,
    orbit_engine: OrbitCalculationEngine = Depends(get_orbit_engine)
) -> Dict[str, Any]:
    """獲取衛星軌跡"""
    try:
        if start_time is None:
            start_time = datetime.now(timezone.utc).timestamp()
        
        trajectory = orbit_engine.calculate_satellite_trajectory(
            satellite_id, start_time, duration_hours, step_minutes
        )
        
        if not trajectory:
            raise HTTPException(status_code=404, detail=f"衛星 {satellite_id} 未找到")
        
        return {
            "satellite_id": satellite_id,
            "start_time": start_time,
            "duration_hours": duration_hours,
            "step_minutes": step_minutes,
            "trajectory": trajectory,
            "points_count": len(trajectory),
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"計算衛星軌跡失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tle/status")
async def get_tle_status(
    tle_manager: TLEDataManager = Depends(get_tle_manager)
) -> Dict[str, Any]:
    """獲取 TLE 數據狀態"""
    try:
        status = tle_manager.get_status()
        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取 TLE 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tle/update")
async def update_tle_data(
    tle_manager: TLEDataManager = Depends(get_tle_manager),
    orbit_engine: OrbitCalculationEngine = Depends(get_orbit_engine)
) -> Dict[str, Any]:
    """更新 TLE 數據"""
    try:
        # 更新 TLE 數據
        await tle_manager.update_all_sources()
        
        # 重新載入到軌道引擎
        satellite_count = await orbit_engine.load_starlink_tle_data()
        
        return {
            "success": True,
            "satellites_loaded": satellite_count,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"更新 TLE 數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/constellation/{constellation}/satellites")
async def get_constellation_satellites(
    constellation: str,
    orbit_engine: OrbitCalculationEngine = Depends(get_orbit_engine)
) -> Dict[str, Any]:
    """獲取指定星座的衛星"""
    try:
        satellites = orbit_engine.get_constellation_satellites(constellation)
        return {
            "constellation": constellation,
            "satellites": satellites,
            "count": len(satellites),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取星座衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "orbit_calculation",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
