"""
SIB19 統一平台 API 路由
提供 SIB19 廣播資訊和鄰居細胞管理服務
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import structlog

from ..services.sib19_unified_platform import SIB19UnifiedPlatform
from ..services.orbit_calculation_engine import OrbitCalculationEngine
from ..services.tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/sib19", tags=["sib19"])

# 全局實例
_sib19_platform = None
_orbit_engine = None
_tle_manager = None

async def get_sib19_platform() -> SIB19UnifiedPlatform:
    """獲取 SIB19 統一平台實例"""
    global _sib19_platform, _orbit_engine, _tle_manager
    
    if _sib19_platform is None:
        if _orbit_engine is None:
            _orbit_engine = OrbitCalculationEngine()
        if _tle_manager is None:
            _tle_manager = TLEDataManager()
            await _tle_manager.initialize_default_sources()
        
        _sib19_platform = SIB19UnifiedPlatform(_orbit_engine, _tle_manager)
    
    return _sib19_platform

@router.get("/status")
async def get_sib19_status(
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取 SIB19 廣播狀態"""
    try:
        status = platform.get_sib19_status()
        return {
            "sib19_status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取 SIB19 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neighbor-cells")
async def get_neighbor_cells(
    event_type: Optional[str] = None,
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取鄰居細胞資訊"""
    try:
        neighbor_cells = platform.get_neighbor_cells(event_type)
        return {
            "neighbor_cells": neighbor_cells,
            "count": len(neighbor_cells),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取鄰居細胞失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smtc-windows")
async def get_smtc_windows(
    satellite_id: Optional[str] = None,
    duration_hours: float = 24,
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取 SMTC 測量窗口"""
    try:
        smtc_windows = platform.get_smtc_measurement_windows(satellite_id, duration_hours)
        return {
            "smtc_windows": smtc_windows,
            "count": len(smtc_windows),
            "satellite_id": satellite_id,
            "duration_hours": duration_hours,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取 SMTC 窗口失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/time-sync")
async def get_time_sync_info(
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取時間同步資訊"""
    try:
        time_sync = platform.get_time_synchronization_info()
        return {
            "time_sync": time_sync,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取時間同步資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reference-location")
async def get_reference_location(
    event_type: str,
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取參考位置資訊"""
    try:
        ref_location = platform.get_reference_location_info(event_type)
        return {
            "reference_location": ref_location,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取參考位置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tracked-satellites")
async def get_tracked_satellites(
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取追蹤的衛星列表"""
    try:
        satellites = platform.get_tracked_satellites()
        return {
            "tracked_satellites": satellites,
            "count": len(satellites),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取追蹤衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-configuration")
async def update_sib19_configuration(
    config: Dict[str, Any],
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """更新 SIB19 配置"""
    try:
        success = platform.update_configuration(config)
        return {
            "success": success,
            "configuration": config,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"更新 SIB19 配置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/constellation-status")
async def get_constellation_status(
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取星座狀態"""
    try:
        status = platform.get_constellation_status()
        return {
            "constellation_status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"獲取星座狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/event-specific-info/{event_type}")
async def get_event_specific_info(
    event_type: str,
    platform: SIB19UnifiedPlatform = Depends(get_sib19_platform)
) -> Dict[str, Any]:
    """獲取事件特定的 SIB19 資訊"""
    try:
        if event_type not in ['A4', 'D1', 'D2', 'T1']:
            raise HTTPException(status_code=400, detail=f"不支援的事件類型: {event_type}")
        
        info = platform.get_event_specific_sib19_info(event_type)
        return {
            "event_type": event_type,
            "sib19_info": info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取事件特定資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "sib19_unified_platform",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
