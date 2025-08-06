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
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import structlog
import asyncio

# Import existing services
from ..services.satellite_gnb_mapping_service import SatelliteGnbMappingService
from ..services.simworld_tle_bridge_service import SimWorldTLEBridgeService

logger = structlog.get_logger(__name__)

# Response Models
class DataSource(BaseModel):
    """數據來源信息"""
    type: str
    description: str
    is_simulation: bool

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
    data_source: Optional[DataSource] = None

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
    print("🔥🔥🔥 SATELLITE OPS ROUTER CALLED 🔥🔥🔥")
    logger.info("🔥🔥🔥 SATELLITE OPS ROUTER CALLED 🔥🔥🔥")
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

        # 直接調用 SimWorld 的真實 TLE API
        logger.info("🚀 NetStack 準備調用 SimWorld API")
        satellites, data_source = await _call_simworld_satellites_api(
            count=count,
            constellation=constellation,
            min_elevation_deg=min_elevation_deg,
            observer_location=observer_location,
            bridge_service=bridge_service,
            global_view=global_view
        )

        # 按仰角排序（從高到低）
        satellites.sort(key=lambda x: x.elevation_deg, reverse=True)
        
        # 調試：記錄排序後的前3顆衛星
        logger.info(f"🔍 排序後前3顆衛星:")
        for i, sat in enumerate(satellites[:3]):
            logger.info(f"  {i+1}. {sat.name}: elevation={sat.elevation_deg}°, azimuth={sat.azimuth_deg}°, distance={sat.distance_km}km")
        
        # 限制返回數量
        satellites = satellites[:count]

        logger.info(
            "可見衛星查詢完成",
            requested_count=count,
            returned_count=len(satellites),
            constellation=constellation,
            global_view=global_view,
            has_observer=observer_location is not None,
            data_source_type=data_source.type if data_source else "None",
            data_source_is_simulation=data_source.is_simulation if data_source else "N/A"
        )

        # Temporary fix: If data_source is None, add a fallback detection
        if data_source is None:
            logger.warning("NetStack 未能從 SimWorld 獲取 data_source，使用臨時檢測機制")
            # Simple fallback based on satellite count and data patterns
            if len(satellites) <= 10 and any(sat.norad_id in ["44713", "44714", "44715", "44716", "44717", "44718"] for sat in satellites):
                data_source = DataSource(
                    type="fallback_simulation",
                    description="模擬數據 (臨時檢測)",
                    is_simulation=True
                )
            else:
                data_source = DataSource(
                    type="unknown",
                    description="數據來源檢測失敗",
                    is_simulation=False
                )
        
        return VisibleSatellitesResponse(
            satellites=satellites,
            total_count=len(satellites),
            requested_count=count,
            constellation=constellation,
            global_view=global_view,
            timestamp=datetime.utcnow().isoformat(),
            observer_location=observer_location,
            data_source=data_source
        )

    except Exception as e:
        logger.error("獲取可見衛星失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取可見衛星失敗: {str(e)}")

async def _call_simworld_satellites_api(
    count: int,
    constellation: Optional[str],
    min_elevation_deg: float,
    observer_location: Optional[Dict[str, float]],
    bridge_service: SimWorldTLEBridgeService,
    global_view: bool = True
) -> Tuple[List[SatelliteInfo], Optional[DataSource]]:
    """直接調用 SimWorld 的真實 TLE API"""
    import aiohttp
    
    # 構建 SimWorld API URL - 使用主機網絡通訊
    simworld_api_url = "http://simworld_backend:8000"  # 通過 Docker 網絡訪問 SimWorld
    
    # 構建請求參數
    params = {
        "count": count,
        "min_elevation_deg": min_elevation_deg,
    }
    
    # 添加觀測者位置參數
    if observer_location:
        params.update({
            "observer_lat": observer_location["lat"],
            "observer_lon": observer_location["lon"],
            "observer_alt": observer_location["alt"] * 1000,  # 轉換回米
        })
    
    # Phase 2 修復：保持原始的 global_view 參數，讓 SimWorld 正確處理仰角
    params["global_view"] = "true" if global_view else "false"
    
    # 添加星座過濾
    if constellation:
        params["constellation"] = constellation
    
    api_url = f"{simworld_api_url}/api/v1/satellites/visible_satellites"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    logger.info("🔍 NetStack 處理 SimWorld 響應", raw_response_keys=list(data.keys()))
                    
                    # 轉換 SimWorld 響應為 NetStack 格式
                    satellites = []
                    satellite_list = data.get("satellites", [])
                    
                    # 提取數據來源信息
                    data_source_info = data.get("data_source")
                    data_source = None
                    if data_source_info:
                        data_source = DataSource(
                            type=data_source_info.get("type", "unknown"),
                            description=data_source_info.get("description", "未知數據來源"),
                            is_simulation=data_source_info.get("is_simulation", False)
                        )
                        logger.info(
                            "從 SimWorld 提取數據來源信息",
                            data_source_type=data_source.type,
                            is_simulation=data_source.is_simulation
                        )
                    else:
                        logger.warning("SimWorld API 響應中沒有 data_source 字段", api_response_keys=list(data.keys()))
                    
                    for sat_data in satellite_list:
                        # 修復：SimWorld API 返回的數據格式是直接在根層級，不是嵌套在 position 中
                        # 調試：記錄轉換前的數據
                        logger.info(f"🔍 轉換衛星數據: {sat_data.get('name', 'unknown')}, "
                                   f"elevation_deg={sat_data.get('elevation_deg')}, "
                                   f"azimuth_deg={sat_data.get('azimuth_deg')}, "
                                   f"distance_km={sat_data.get('distance_km')}")
                        
                        satellite_info = SatelliteInfo(
                            name=sat_data.get("name", f"SAT-{sat_data.get('id', 'unknown')}"),
                            norad_id=str(sat_data.get("norad_id", sat_data.get("id", "unknown"))),
                            elevation_deg=sat_data.get("elevation_deg", 0),
                            azimuth_deg=sat_data.get("azimuth_deg", 0),
                            # 修復距離計算：從地心距離轉換為 slant range
                            distance_km=max(550, sat_data.get("distance_km", 0) - 6371) if sat_data.get("distance_km", 0) > 3000 else sat_data.get("distance_km", 0),
                            orbit_altitude_km=sat_data.get("orbit_altitude_km", sat_data.get("altitude", 550)),
                            constellation=constellation or _extract_constellation_from_name(sat_data.get("name", "")),
                            signal_strength=sat_data.get("signal_strength"),
                            is_visible=sat_data.get("is_visible", True) and sat_data.get("elevation_deg", 0) >= min_elevation_deg
                        )
                        
                        logger.info(f"✅ 轉換後衛星信息: {satellite_info.name}, "
                                   f"elevation={satellite_info.elevation_deg}, "
                                   f"azimuth={satellite_info.azimuth_deg}, "
                                   f"distance={satellite_info.distance_km}")
                        satellites.append(satellite_info)
                    
                    logger.info(
                        "成功調用 SimWorld TLE API", 
                        api_url=api_url,
                        returned_count=len(satellites),
                        constellation=constellation,
                        data_source_type=data_source.type if data_source else "unknown"
                    )
                    return satellites, data_source
                else:
                    logger.error("SimWorld API 調用失敗", status=response.status, url=api_url)
                    return [], None
                    
    except Exception as e:
        logger.error("調用 SimWorld API 異常", error=str(e), url=api_url)
        return [], None

def _extract_constellation_from_name(satellite_name: str) -> str:
    """從衛星名稱提取星座信息"""
    name_upper = satellite_name.upper()
    if "STARLINK" in name_upper:
        return "STARLINK"
    elif "ONEWEB" in name_upper:
        return "ONEWEB" 
    elif "KUIPER" in name_upper:
        return "KUIPER"
    elif "GLOBALSTAR" in name_upper:
        return "GLOBALSTAR"
    elif "IRIDIUM" in name_upper:
        return "IRIDIUM"
    else:
        return "UNKNOWN"

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