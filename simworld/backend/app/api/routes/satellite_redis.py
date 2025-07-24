"""
Satellite API Routes - Redis 版本 (真實 TLE 數據)
使用 Redis 中的真實 TLE 數據提供基本的衛星查詢功能
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
        # Fallback: create new connection to NetStack Redis via network IP
        return Redis(host="172.20.0.50", port=6379, db=0, decode_responses=True)


async def load_satellites_from_redis(redis: Redis) -> Dict[str, EarthSatellite]:
    """從 Redis 載入真實衛星數據"""
    global ts, satellites_cache, cache_timestamp

    # 檢查緩存是否有效
    if (
        cache_timestamp
        and datetime.utcnow() - cache_timestamp < timedelta(seconds=CACHE_DURATION)
        and satellites_cache
    ):
        logger.info(f"Returning cached satellites: {len(satellites_cache)} satellites")
        return satellites_cache

    logger.info("Loading satellites from Redis...")

    # 初始化 Skyfield 時間尺度
    if ts is None:
        ts = load.timescale(builtin=True)

    satellites = {}

    try:
        # 載入真實 Starlink 數據
        starlink_data = await redis.get("tle_data:starlink")
        if starlink_data:
            starlink_tles = json.loads(starlink_data)
            for tle_data in starlink_tles:
                try:
                    name = tle_data["name"]
                    line1 = tle_data["line1"]
                    line2 = tle_data["line2"]
                    satellite = EarthSatellite(line1, line2, name, ts)
                    satellites[name] = satellite
                except Exception as e:
                    logger.debug(f"Failed to load Starlink satellite {tle_data.get('name', 'unknown')}: {e}")

        # 載入真實 Kuiper 數據
        kuiper_data = await redis.get("tle_data:kuiper")
        if kuiper_data:
            kuiper_tles = json.loads(kuiper_data)
            for tle_data in kuiper_tles:
                try:
                    name = tle_data["name"]
                    line1 = tle_data["line1"]
                    line2 = tle_data["line2"]
                    satellite = EarthSatellite(line1, line2, name, ts)
                    satellites[name] = satellite
                except Exception as e:
                    logger.debug(f"Failed to load Kuiper satellite {tle_data.get('name', 'unknown')}: {e}")

        # 更新緩存
        satellites_cache = satellites
        cache_timestamp = datetime.utcnow()

        logger.info(f"Loaded {len(satellites)} real satellites from Redis")
        return satellites

    except Exception as e:
        logger.error(f"Error loading satellites from Redis: {e}")
        # 如果 Redis 完全不可用，則返回空字典，不使用模擬數據
        return {}


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
    獲取可見衛星列表 - 僅使用真實 TLE 數據和 SGP4 軌道計算
    """
    try:
        # 獲取 Redis 客戶端並載入真實衛星數據
        redis = await get_redis_client(request)
        satellites = await load_satellites_from_redis(redis)
        
        if not satellites:
            logger.warning("No real satellite data available from Redis")
            return {
                "success": False,
                "satellites": [],
                "observer": {"latitude": observer_lat, "longitude": observer_lon, "altitude": observer_alt},
                "search_criteria": {"min_elevation": min_elevation_deg, "constellation": constellation, "max_results": count},
                "results": {"total_visible": 0, "satellites": []},
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "processed": 0, "visible": 0, "global_view": global_view,
                "error": "No real satellite TLE data available"
            }

        # 設定觀測者位置
        observer = wgs84.latlon(observer_lat, observer_lon, observer_alt / 1000.0)  # 轉換為公里
        now = ts.now()
        
        visible_satellites = []
        
        # 過濾星座
        filtered_satellites = list(satellites.values())
        if constellation:
            constellation_upper = constellation.upper()
            filtered_satellites = [sat for sat in satellites.values() 
                                 if constellation_upper in sat.name.upper()]
        
        logger.info(f"Processing {len(filtered_satellites)} real satellites for observer at {observer_lat}, {observer_lon}")
        
        # 計算可見衛星（使用真實軌道計算）
        for satellite in filtered_satellites[:min(len(filtered_satellites), count * 3)]:
            try:
                # 計算衛星相對於觀測者的位置
                difference = satellite - observer
                topocentric = difference.at(now)
                alt, az, distance = topocentric.altaz()
                
                # 檢查仰角篩選
                if alt.degrees >= min_elevation_deg:
                    # 計算衛星的地心位置
                    geocentric = satellite.at(now)
                    subpoint = wgs84.subpoint(geocentric)
                    
                    satellite_info = {
                        "id": satellite.model.satnum if hasattr(satellite.model, 'satnum') else hash(satellite.name) % 100000,
                        "name": satellite.name,
                        "norad_id": str(satellite.model.satnum) if hasattr(satellite.model, 'satnum') else str(hash(satellite.name) % 100000),
                        "position": {
                            "latitude": round(subpoint.latitude.degrees, 4),
                            "longitude": round(subpoint.longitude.degrees, 4),
                            "altitude": round(subpoint.elevation.km, 2),
                            "elevation": round(alt.degrees, 2),
                            "azimuth": round(az.degrees, 2),
                            "range": round(distance.km, 2),
                            "velocity": 7.5,  # 近似 LEO 軌道速度（km/s）
                            "doppler_shift": 0,  # 暫時設為0，可後續計算
                        },
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "signal_quality": {
                            "elevation_deg": round(alt.degrees, 2),
                            "range_km": round(distance.km, 2),
                            "estimated_signal_strength": max(50, 100 - distance.km / 20),  # 簡化的信號強度估算
                            "path_loss_db": round(120 + 20 * np.log10(distance.km), 2),  # 自由空間路徑損耗
                        },
                    }
                    
                    visible_satellites.append(satellite_info)
                    
            except Exception as e:
                logger.debug(f"Error processing satellite {satellite.name}: {e}")
                continue
        
        # 按仰角排序（從高到低）
        visible_satellites.sort(key=lambda x: x["position"]["elevation"], reverse=True)
        
        # 限制返回數量
        visible_satellites = visible_satellites[:count]
        
        logger.info(f"Found {len(visible_satellites)} visible satellites using real TLE data")
        
        return {
            "success": True,
            "satellites": visible_satellites,
            "observer": {"latitude": observer_lat, "longitude": observer_lon, "altitude": observer_alt},
            "search_criteria": {"min_elevation": min_elevation_deg, "constellation": constellation, "max_results": count},
            "results": {"total_visible": len(visible_satellites), "satellites": visible_satellites},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "processed": len(filtered_satellites), "visible": len(visible_satellites), "global_view": global_view,
        }
    
    except Exception as e:
        logger.error(f"Error in get_visible_satellites: {e}")
        return {
            "success": False,
            "satellites": [],
            "observer": {"latitude": observer_lat, "longitude": observer_lon, "altitude": observer_alt},
            "search_criteria": {"min_elevation": min_elevation_deg, "constellation": constellation, "max_results": count},
            "results": {"total_visible": 0, "satellites": []},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "processed": 0, "visible": 0, "global_view": global_view,
            "error": str(e)
        }


@router.get("/stats", tags=["Satellites"])
async def get_satellite_stats(request: Request):
    """獲取衛星統計資訊"""
    try:
        redis = await get_redis_client(request)
        satellites = await load_satellites_from_redis(redis)
        
        return {
            "total_satellites": len(satellites),
            "data_source": "Redis TLE data",
            "skyfield_loaded": ts is not None,
            "timestamp": datetime.utcnow().isoformat(),
            "real_data": True,  # 標記為真實數據
        }
    except Exception as e:
        return {
            "total_satellites": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "real_data": False,
        }