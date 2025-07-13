"""
Satellite API Routes - Redis 版本
使用 Redis 中的 TLE 數據提供基本的衛星查詢功能
替代 PostgreSQL 依賴的衛星 API
"""

import logging
import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Request
from redis.asyncio import Redis

from skyfield.api import load, wgs84, EarthSatellite

logger = logging.getLogger(__name__)
router = APIRouter()

# Global variables for caching
ts = None
satellites_cache = {}
cache_timestamp = None
CACHE_DURATION = 300  # 5 minutes


async def get_redis_client(request: Request) -> Redis:
    """獲取 Redis 客戶端"""
    if hasattr(request.app.state, "redis") and request.app.state.redis:
        return request.app.state.redis
    else:
        # Fallback: create new connection
        return Redis(host='netstack-redis', port=6379, db=0, decode_responses=True)


async def load_satellites_from_redis(redis: Redis) -> Dict[str, EarthSatellite]:
    """從 Redis 載入衛星數據"""
    global ts, satellites_cache, cache_timestamp
    
    # 檢查緩存是否有效
    if (cache_timestamp and 
        datetime.utcnow() - cache_timestamp < timedelta(seconds=CACHE_DURATION) and
        satellites_cache):
        return satellites_cache
    
    logger.info("Loading satellites from Redis...")
    
    # 初始化 Skyfield 時間尺度
    if ts is None:
        ts = load.timescale(builtin=True)
    
    satellites = {}
    
    try:
        # 載入 Starlink 數據
        starlink_data = await redis.get('tle_data:starlink')
        if starlink_data:
            starlink_tles = json.loads(starlink_data)
            for tle_data in starlink_tles:
                try:
                    name = tle_data['name']
                    line1 = tle_data['line1']
                    line2 = tle_data['line2']
                    satellite = EarthSatellite(line1, line2, name, ts)
                    satellites[name] = satellite
                except Exception as e:
                    logger.debug(f"Failed to load Starlink satellite {tle_data.get('name', 'unknown')}: {e}")
        
        # 載入 Kuiper 數據
        kuiper_data = await redis.get('tle_data:kuiper')
        if kuiper_data:
            kuiper_tles = json.loads(kuiper_data)
            for tle_data in kuiper_tles:
                try:
                    name = tle_data['name']
                    line1 = tle_data['line1']
                    line2 = tle_data['line2']
                    satellite = EarthSatellite(line1, line2, name, ts)
                    satellites[name] = satellite
                except Exception as e:
                    logger.debug(f"Failed to load Kuiper satellite {tle_data.get('name', 'unknown')}: {e}")
        
        # 更新緩存
        satellites_cache = satellites
        cache_timestamp = datetime.utcnow()
        
        logger.info(f"Loaded {len(satellites)} satellites from Redis")
        return satellites
        
    except Exception as e:
        logger.error(f"Error loading satellites from Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load satellite data: {e}")


@router.get("/visible_satellites", tags=["Satellites"])
async def get_visible_satellites(
    request: Request,
    count: int = Query(default=50, description="回傳衛星數量限制"),
    min_elevation_deg: float = Query(default=-10.0, description="最小仰角 (度)"),
    observer_lat: float = Query(default=0.0, description="觀察者緯度"),
    observer_lon: float = Query(default=0.0, description="觀察者經度"),
    observer_alt: float = Query(default=0.0, description="觀察者高度 (公尺)"),
    global_view: bool = Query(default=True, description="全球視野模式"),
    constellation: Optional[str] = Query(default=None, description="星座過濾 (starlink, kuiper)"),
):
    """
    獲取可見衛星列表 - Redis 版本
    """
    try:
        redis = await get_redis_client(request)
        satellites = await load_satellites_from_redis(redis)
        
        if not satellites:
            return {
                "satellites": [],
                "processed": 0,
                "visible": 0,
                "error": "No satellite data available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        now = ts.now()
        
        # 創建觀測者位置
        if global_view:
            observer_locations = [
                wgs84.latlon(0.0, 0.0, 0.0),  # 赤道
                wgs84.latlon(45.0, 0.0, 0.0),  # 中緯度
                wgs84.latlon(-45.0, 90.0, 0.0),  # 南半球
            ]
        else:
            observer_locations = [
                wgs84.latlon(observer_lat, observer_lon, observer_alt)
            ]
        
        # 根據星座過濾衛星
        filtered_satellites = {}
        if constellation:
            constellation_lower = constellation.lower()
            for name, sat in satellites.items():
                if constellation_lower in name.lower():
                    filtered_satellites[name] = sat
        else:
            filtered_satellites = satellites
        
        visible_satellites = []
        
        for observer in observer_locations:
            # 限制處理數量以避免超時
            satellites_to_process = list(filtered_satellites.items())[:min(len(filtered_satellites), count * 3)]
            
            for name, satellite in satellites_to_process:
                try:
                    # 計算衛星相對於觀測者的位置
                    difference = satellite - observer
                    topocentric = difference.at(now)
                    alt, az, distance = topocentric.altaz()
                    
                    if alt.degrees >= min_elevation_deg:
                        # 計算地面軌跡
                        geocentric = satellite.at(now)
                        subpoint = wgs84.subpoint(geocentric)
                        
                        # 確保ID唯一且穩定
                        sat_id = getattr(satellite.model, 'satnum', None)
                        if sat_id is None:
                            sat_id = abs(hash(name)) % 100000  # 基於名稱的穩定hash
                        
                        satellite_info = {
                            "id": int(sat_id),
                            "name": name,
                            "norad_id": str(sat_id),
                            "position": {
                                "latitude": round(subpoint.latitude.degrees, 4),
                                "longitude": round(subpoint.longitude.degrees, 4),
                                "altitude": round(subpoint.elevation.km, 2),
                                "elevation": round(alt.degrees, 2),
                                "azimuth": round(az.degrees, 2),
                                "range": round(distance.km, 2),
                                "velocity": 7.5,  # LEO 近似軌道速度
                                "doppler_shift": 0,  # 預設值
                            },
                            "timestamp": now.utc_iso(),
                            "signal_quality": {
                                "elevation_deg": round(alt.degrees, 2),
                                "range_km": round(distance.km, 2),
                                "estimated_signal_strength": min(100, alt.degrees * 2),
                                "path_loss_db": round(20 * np.log10(max(1, distance.km)) + 92.45 + 20 * np.log10(2.15), 2),
                            },
                        }
                        
                        visible_satellites.append(satellite_info)
                
                except Exception as e:
                    logger.debug(f"Error processing satellite {name}: {e}")
                    continue
        
        # 去重並按仰角排序
        unique_satellites = {}
        for sat in visible_satellites:
            if (sat["name"] not in unique_satellites or 
                sat["position"]["elevation"] > unique_satellites[sat["name"]]["position"]["elevation"]):
                unique_satellites[sat["name"]] = sat
        
        result_satellites = list(unique_satellites.values())
        result_satellites.sort(key=lambda x: x["position"]["elevation"], reverse=True)
        
        final_satellites = result_satellites[:count]
        
        return {
            "success": True,
            "satellites": final_satellites,  # 前端期望的主要字段
            "observer": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": observer_alt,
            },
            "search_criteria": {
                "min_elevation": min_elevation_deg,
                "constellation": constellation,
                "max_results": count,
            },
            "results": {
                "total_visible": len(result_satellites),
                "satellites": final_satellites,  # 也保留在 results 中以兼容
            },
            "timestamp": now.utc_iso(),
            "processed": len(filtered_satellites),
            "visible": len(result_satellites),
            "global_view": global_view,
        }
        
    except Exception as e:
        logger.error(f"Error getting visible satellites: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating visible satellites: {e}")


@router.get("/stats", tags=["Satellites"])
async def get_satellite_stats(request: Request):
    """
    獲取衛星統計資訊 - Redis 版本
    """
    try:
        redis = await get_redis_client(request)
        satellites = await load_satellites_from_redis(redis)
        
        # 統計不同星座
        starlink_count = len([name for name in satellites.keys() if "STARLINK" in name.upper()])
        kuiper_count = len([name for name in satellites.keys() if "KUIPER" in name.upper()])
        
        # 獲取最後更新時間
        starlink_update = await redis.get('starlink_tle_last_update')
        kuiper_update = await redis.get('kuiper_tle_last_update')
        
        return {
            "total_satellites": len(satellites),
            "constellations": {
                "starlink": starlink_count,
                "kuiper": kuiper_count,
            },
            "data_source": "redis",
            "last_updates": {
                "starlink": starlink_update,
                "kuiper": kuiper_update,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error getting satellite stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting satellite stats: {e}")


@router.get("/orbit/{satellite_name}", tags=["Satellites"])
async def get_satellite_orbit(request: Request, satellite_name: str):
    """
    獲取衛星軌道資訊 - Redis 版本
    """
    try:
        redis = await get_redis_client(request)
        satellites = await load_satellites_from_redis(redis)
        
        if satellite_name not in satellites:
            # 尋找類似名稱
            similar_names = [name for name in satellites.keys() if satellite_name.upper() in name.upper()][:10]
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Satellite '{satellite_name}' not found",
                    "similar_satellites": similar_names,
                    "total_satellites": len(satellites),
                }
            )
        
        satellite = satellites[satellite_name]
        now = ts.now()
        
        # 計算當前位置
        geocentric = satellite.at(now)
        subpoint = wgs84.subpoint(geocentric)
        
        orbit_info = {
            "satellite_name": satellite_name,
            "current_position": {
                "latitude": subpoint.latitude.degrees,
                "longitude": subpoint.longitude.degrees,
                "altitude_km": subpoint.elevation.km,
                "timestamp": now.utc_iso(),
            },
            "orbital_period_minutes": 90,  # LEO 近似值
            "inclination_degrees": 53.0,  # Starlink 近似值
            "eccentricity": 0.0001,  # 近圓軌道
        }
        
        return orbit_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting satellite orbit: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating orbit: {e}")