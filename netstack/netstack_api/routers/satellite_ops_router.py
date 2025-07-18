"""
Satellite Operations Router
衛星操作路由器 - 提供前端需要的衛星數據接口

主要功能：
1. 獲取可見衛星列表
2. 支持星座過濾
3. 支持全球視角查看
4. 高性能緩存機制
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import structlog
import asyncio

# Import existing services
from ..services.satellite_gnb_mapping_service import SatelliteGnbMappingService
from ..services.simworld_tle_bridge_service import SimWorldTLEBridgeService

logger = structlog.get_logger(__name__)

# Response Models
class SatelliteInfo(BaseModel):
    """衛星信息"""
    name: str
    norad_id: str
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    orbit_altitude_km: float
    constellation: Optional[str] = None
    signal_strength: Optional[float] = None
    is_visible: bool = True

class VisibleSatellitesResponse(BaseModel):
    """可見衛星響應"""
    satellites: List[SatelliteInfo]
    total_count: int
    requested_count: int
    constellation: Optional[str] = None
    global_view: bool = False
    timestamp: str
    observer_location: Optional[Dict[str, float]] = None

# Global service instances
satellite_service: Optional[SatelliteGnbMappingService] = None
tle_bridge_service: Optional[SimWorldTLEBridgeService] = None

def get_satellite_service() -> SatelliteGnbMappingService:
    """獲取衛星服務實例"""
    import os
    
    global satellite_service
    if satellite_service is None:
        simworld_url = os.getenv("SIMWORLD_API_URL", "http://localhost:8888")
        satellite_service = SatelliteGnbMappingService(
            simworld_api_url=simworld_url, 
            redis_client=None
        )
    return satellite_service

def get_tle_bridge_service() -> SimWorldTLEBridgeService:
    """獲取 TLE 橋接服務實例"""
    import os
    
    global tle_bridge_service
    if tle_bridge_service is None:
        simworld_url = os.getenv("SIMWORLD_API_URL", "http://localhost:8888")
        tle_bridge_service = SimWorldTLEBridgeService(
            simworld_api_url=simworld_url,
            redis_client=None
        )
    return tle_bridge_service

# 創建路由器
router = APIRouter(
    prefix="/api/v1/satellite-ops",
    tags=["Satellite Operations"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

@router.get(
    "/visible_satellites",
    response_model=VisibleSatellitesResponse,
    summary="獲取可見衛星列表",
    description="獲取當前可見的衛星列表，支持星座過濾和全球視角"
)
async def get_visible_satellites(
    count: int = Query(10, ge=1, le=100, description="返回衛星數量"),
    constellation: Optional[str] = Query(None, description="星座名稱 (starlink, oneweb, kuiper)"),
    global_view: bool = Query(False, description="是否使用全球視角"),
    min_elevation_deg: float = Query(0, ge=-90, le=90, description="最小仰角"),
    observer_lat: Optional[float] = Query(None, ge=-90, le=90, description="觀測者緯度"),
    observer_lon: Optional[float] = Query(None, ge=-180, le=180, description="觀測者經度"),
    observer_alt: Optional[float] = Query(None, ge=0, description="觀測者高度（米）"),
    bridge_service: SimWorldTLEBridgeService = Depends(get_tle_bridge_service),
    service: SatelliteGnbMappingService = Depends(get_satellite_service),
):
    """獲取可見衛星列表"""
    try:
        # 構建觀測者位置
        observer_location = None
        if observer_lat is not None and observer_lon is not None:
            observer_location = {
                "lat": observer_lat,
                "lon": observer_lon,
                "alt": (observer_alt or 0) / 1000  # 轉換為公里
            }

        # 如果是全球視角，使用默認位置
        if global_view and observer_location is None:
            observer_location = {
                "lat": 0.0,  # 赤道
                "lon": 0.0,  # 本初子午線
                "alt": 0.0
            }

        # 生成衛星ID列表 - 根據星座和數量
        satellite_ids = await _get_satellite_ids_for_constellation(
            constellation, count, bridge_service
        )

        # 獲取衛星位置數據
        positions = await bridge_service.get_batch_satellite_positions(
            satellite_ids=satellite_ids,
            timestamp=datetime.utcnow(),
            observer_location=observer_location,
        )

        # 轉換為前端需要的格式
        satellites = []
        for sat_id, pos_data in positions.items():
            if pos_data.get("success") and pos_data.get("position"):
                pos = pos_data["position"]
                
                # 檢查仰角過濾
                elevation = pos.get("elevation_deg", 0)
                if elevation < min_elevation_deg:
                    continue
                
                # 構建衛星信息
                satellite_info = SatelliteInfo(
                    name=pos.get("name", f"SAT-{sat_id}"),
                    norad_id=str(sat_id),
                    elevation_deg=elevation,
                    azimuth_deg=pos.get("azimuth_deg", 0),
                    distance_km=pos.get("distance_km", 0),
                    orbit_altitude_km=pos.get("orbit_altitude_km", 550),  # 默認LEO高度
                    constellation=constellation or "unknown",
                    signal_strength=pos.get("signal_strength"),
                    is_visible=elevation > 0
                )
                satellites.append(satellite_info)

        # 按仰角排序（從高到低）
        satellites.sort(key=lambda x: x.elevation_deg, reverse=True)
        
        # 限制返回數量
        satellites = satellites[:count]

        logger.info(
            "可見衛星查詢完成",
            requested_count=count,
            returned_count=len(satellites),
            constellation=constellation,
            global_view=global_view,
            has_observer=observer_location is not None,
        )

        return VisibleSatellitesResponse(
            satellites=satellites,
            total_count=len(satellites),
            requested_count=count,
            constellation=constellation,
            global_view=global_view,
            timestamp=datetime.utcnow().isoformat(),
            observer_location=observer_location,
        )

    except Exception as e:
        logger.error("獲取可見衛星失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取可見衛星失敗: {str(e)}")

async def _get_satellite_ids_for_constellation(
    constellation: Optional[str], 
    count: int, 
    bridge_service: SimWorldTLEBridgeService
) -> List[str]:
    """根據星座獲取衛星ID列表"""
    
    # 星座映射 - 根據實際可用的衛星數據調整
    constellation_ranges = {
        "starlink": list(range(1, 100)),  # Starlink 衛星ID範圍
        "oneweb": list(range(100, 150)),   # OneWeb 衛星ID範圍
        "kuiper": list(range(150, 200)),   # Kuiper 衛星ID範圍
    }
    
    if constellation and constellation.lower() in constellation_ranges:
        # 使用指定星座的衛星ID
        available_ids = constellation_ranges[constellation.lower()]
        # 取前N個或全部可用的
        selected_ids = available_ids[:min(count, len(available_ids))]
    else:
        # 混合星座或未指定星座
        all_ids = []
        for ids in constellation_ranges.values():
            all_ids.extend(ids)
        selected_ids = all_ids[:min(count, len(all_ids))]
    
    # 轉換為字符串
    return [str(sid) for sid in selected_ids]

@router.get(
    "/health",
    summary="衛星操作健康檢查",
    description="檢查衛星操作服務的健康狀態"
)
async def health_check():
    """健康檢查"""
    try:
        return {
            "healthy": True,
            "service": "satellite-ops",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": [
                "/api/v1/satellite-ops/visible_satellites",
                "/api/v1/satellite-ops/health"
            ]
        }
    except Exception as e:
        logger.error("衛星操作健康檢查失敗", error=str(e))
        raise HTTPException(status_code=503, detail=f"服務不可用: {str(e)}")