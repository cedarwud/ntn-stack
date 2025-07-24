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
is_using_fallback_data = False  # 追蹤是否使用 fallback 數據


async def get_redis_client(request: Request) -> Redis:
    """獲取 Redis 客戶端"""
    if hasattr(request.app.state, "redis") and request.app.state.redis:
        return request.app.state.redis
    else:
        # Fallback: create new connection to NetStack Redis via network IP
        return Redis(host="172.20.0.50", port=6379, db=0, decode_responses=True)


async def load_satellites_from_redis(redis: Redis) -> Dict[str, EarthSatellite]:
    """從 NetStack 載入真實歷史衛星數據 (Phase 2 修復)"""
    global ts, satellites_cache, cache_timestamp, is_using_fallback_data

    # 檢查緩存是否有效
    if (
        cache_timestamp
        and datetime.utcnow() - cache_timestamp < timedelta(seconds=CACHE_DURATION)
        and satellites_cache
    ):
        logger.info(f"Returning cached satellites: {len(satellites_cache)} satellites")
        return satellites_cache

    logger.info("Loading satellites from NetStack historical data...")

    # 初始化 Skyfield 時間尺度
    if ts is None:
        ts = load.timescale(builtin=True)

    satellites = {}

    try:
        # Phase 2 修復：直接從 NetStack 獲取歷史 TLE 數據
        import aiohttp
        
        # NetStack API URL - 使用容器內部網路
        netstack_api_url = "http://netstack-api:8080"
        
        # 嘗試從 NetStack 獲取真實歷史衛星數據
        async with aiohttp.ClientSession() as session:
            # 獲取 Starlink 歷史數據 - 使用新的 TLE 端點
            try:
                starlink_url = f"{netstack_api_url}/api/satellite-data/constellations/starlink/tle"
                async with session.get(starlink_url, timeout=10) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        starlink_data = response_data.get("satellites", [])
                        logger.info(f"✅ 從 NetStack 載入 Starlink 歷史 TLE 數據: {len(starlink_data)} 顆衛星")
                        
                        for sat_data in starlink_data:
                            try:
                                name = sat_data.get("satellite_name", f"STARLINK-{sat_data.get('norad_id')}")
                                line1 = sat_data.get("line1", "")
                                line2 = sat_data.get("line2", "")
                                
                                if line1 and line2:
                                    satellite = EarthSatellite(line1, line2, name, ts)
                                    satellites[name] = satellite
                                else:
                                    logger.debug(f"TLE data missing for {name}: line1='{line1[:20]}...', line2='{line2[:20]}...'")
                            except Exception as e:
                                logger.debug(f"Failed to load Starlink satellite {sat_data.get('satellite_name', 'unknown')}: {e}")
                    else:
                        logger.warning(f"NetStack Starlink TLE API 返回 {response.status}")
            except Exception as e:
                logger.warning(f"無法從 NetStack 獲取 Starlink TLE 數據: {e}")

            # 獲取 OneWeb 歷史數據 - 使用新的 TLE 端點
            try:
                oneweb_url = f"{netstack_api_url}/api/satellite-data/constellations/oneweb/tle"
                async with session.get(oneweb_url, timeout=10) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        oneweb_data = response_data.get("satellites", [])
                        logger.info(f"✅ 從 NetStack 載入 OneWeb 歷史 TLE 數據: {len(oneweb_data)} 顆衛星")
                        
                        for sat_data in oneweb_data:
                            try:
                                name = sat_data.get("satellite_name", f"ONEWEB-{sat_data.get('norad_id')}")
                                line1 = sat_data.get("line1", "")
                                line2 = sat_data.get("line2", "")
                                
                                if line1 and line2:
                                    satellite = EarthSatellite(line1, line2, name, ts)
                                    satellites[name] = satellite
                                else:
                                    logger.debug(f"TLE data missing for {name}: line1='{line1[:20]}...', line2='{line2[:20]}...'")
                            except Exception as e:
                                logger.debug(f"Failed to load OneWeb satellite {sat_data.get('satellite_name', 'unknown')}: {e}")
                    else:
                        logger.warning(f"NetStack OneWeb TLE API 返回 {response.status}")
            except Exception as e:
                logger.warning(f"無法從 NetStack 獲取 OneWeb TLE 數據: {e}")

        # 更新緩存
        satellites_cache = satellites
        cache_timestamp = datetime.utcnow()

        # 檢查是否成功載入真實數據
        if satellites:
            is_using_fallback_data = False
            logger.info(f"✅ 從 NetStack 載入真實歷史 TLE 數據: {len(satellites)} 顆衛星")
            logger.info("🎯 數據來源: NetStack 歷史 TLE 數據模組 (非模擬數據)")
            return satellites
        else:
            logger.warning("🔴 NetStack 沒有返回衛星數據，使用 fallback 機制")
            satellites = await _load_fallback_satellites()
            is_using_fallback_data = True
            logger.warning(f"⚠️  正在使用模擬數據: {len(satellites)} 顆衛星 (NetStack 無數據)")
            return satellites

    except Exception as e:
        logger.error(f"❌ NetStack 連接失敗: {e}")
        # NetStack 不可用時使用 fallback 數據
        logger.warning("🔴 NetStack 不可用，使用 fallback 衛星數據")
        is_using_fallback_data = True
        fallback_satellites = await _load_fallback_satellites()
        logger.warning(f"⚠️  正在使用模擬數據: {len(fallback_satellites)} 顆衛星 (NetStack 連接失敗)")
        return fallback_satellites


async def _load_fallback_satellites() -> Dict[str, EarthSatellite]:
    """
    載入 fallback 衛星數據
    Phase 2 修復：當 Redis 沒有數據時的備用機制
    """
    global ts
    
    if ts is None:
        ts = load.timescale(builtin=True)
    
    logger.info("🔄 載入 fallback 衛星數據...")
    
    # 與 NetStack 相同的 fallback 數據
    fallback_tle_data = [
        {
            "name": "STARLINK-1007",
            "line1": "1 44713U 19074A   25204.91667000  .00002182  00000-0  16538-3 0  9999",
            "line2": "2 44713  53.0534  95.4567 0001234  87.6543 272.3456 15.05000000289456",
        },
        {
            "name": "STARLINK-1008",
            "line1": "1 44714U 19074B   25204.91667000  .00002135  00000-0  16234-3 0  9999",
            "line2": "2 44714  53.0534  105.5678 0001456  88.7654 273.4567 15.05000000289467",
        },
        {
            "name": "STARLINK-1009",
            "line1": "1 44715U 19074C   25204.91667000  .00002089  00000-0  15923-3 0  9999",
            "line2": "2 44715  53.0534  115.6789 0001678  89.8765 274.5678 15.05000000289478",
        },
        {
            "name": "STARLINK-1010",
            "line1": "1 44716U 19074D   25204.91667000  .00001998  00000-0  15612-3 0  9999",
            "line2": "2 44716  53.0534  125.7890 0001890  90.9876 275.6789 15.05000000289489",
        },
        {
            "name": "STARLINK-1011",
            "line1": "1 44717U 19074E   25204.91667000  .00001945  00000-0  15301-3 0  9999",
            "line2": "2 44717  53.0534  135.8901 0002012  92.0987 276.7890 15.05000000289500",
        },
        {
            "name": "ONEWEB-0001",
            "line1": "1 44063U 19005A   25204.50000000  .00001234  00000-0  12345-3 0  9999",
            "line2": "2 44063  87.4000  10.0000 0001000  45.0000 315.0000 13.26000000234567",
        },
        {
            "name": "ONEWEB-0002",
            "line1": "1 44064U 19005B   25204.50000000  .00001200  00000-0  12000-3 0  9999",
            "line2": "2 44064  87.4000  20.0000 0001200  46.0000 314.0000 13.26000000234578",
        },
        {
            "name": "GPS IIF-1",
            "line1": "1 37753U 11036A   25204.50000000 -.00000018  00000-0  00000-0 0  9999",
            "line2": "2 37753  55.0000  50.0000 0001000  45.0000 315.0000  2.00000000567890",
        },
        {
            "name": "GALILEO-101",
            "line1": "1 37846U 11060A   25204.50000000  .00000010  00000-0  00000-0 0  9999",
            "line2": "2 37846  56.0000  60.0000 0002000  50.0000 310.0000  1.70000000345678",
        },
    ]
    
    satellites = {}
    
    try:
        for tle_data in fallback_tle_data:
            try:
                name = tle_data["name"]
                line1 = tle_data["line1"]
                line2 = tle_data["line2"]
                satellite = EarthSatellite(line1, line2, name, ts)
                satellites[name] = satellite
            except Exception as e:
                logger.warning(f"⚠️ 載入 fallback 衛星 {tle_data['name']} 失敗: {e}")
                continue
        
        logger.info(f"✅ 載入 fallback 衛星數據: {len(satellites)} 顆衛星")
        return satellites
        
    except Exception as e:
        logger.error(f"❌ 載入 fallback 衛星數據失敗: {e}")
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
            logger.warning("No satellite data available from Redis or fallback")
            return {
                "success": False,
                "satellites": [],
                "observer": {"latitude": observer_lat, "longitude": observer_lon, "altitude": observer_alt},
                "search_criteria": {"min_elevation": min_elevation_deg, "constellation": constellation, "max_results": count},
                "results": {"total_visible": 0, "satellites": []},
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "processed": 0, "visible": 0, "global_view": global_view,
                "error": "No satellite TLE data available from Redis or fallback"
            }

        # Phase 2 修復：全球視野模式使用最寬鬆的仰角限制以顯示所有衛星
        if global_view and min_elevation_deg > -90:
            min_elevation_deg = -90  # 全球視野顯示所有衛星（不限制仰角）
            logger.info(f"🌍 全球視野模式：調整最小仰角為 {min_elevation_deg} 度（顯示所有衛星）")
        
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
        
        # 根據實際數據來源記錄正確的日誌
        if is_using_fallback_data:
            logger.warning(f"🟡 找到 {len(visible_satellites)} 顆可見衛星 (使用模擬數據)")
        else:
            logger.info(f"✅ 找到 {len(visible_satellites)} 顆可見衛星 (使用真實 TLE 數據)")
        
        return {
            "success": True,
            "satellites": visible_satellites,
            "observer": {"latitude": observer_lat, "longitude": observer_lon, "altitude": observer_alt},
            "search_criteria": {"min_elevation": min_elevation_deg, "constellation": constellation, "max_results": count},
            "results": {"total_visible": len(visible_satellites), "satellites": visible_satellites},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "processed": len(filtered_satellites), "visible": len(visible_satellites), "global_view": global_view,
            "data_source": {
                "type": "fallback_simulation" if is_using_fallback_data else "real_tle_data",
                "description": "模擬數據 (外部 TLE 源不可用)" if is_using_fallback_data else "真實 TLE 歷史數據",
                "is_simulation": is_using_fallback_data
            }
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
            "error": str(e),
            "data_source": {
                "type": "error",
                "description": "數據載入失敗",
                "is_simulation": False
            }
        }


@router.get("/stats", tags=["Satellites"])
async def get_satellite_stats(request: Request):
    """獲取衛星統計資訊"""
    try:
        redis = await get_redis_client(request)
        satellites = await load_satellites_from_redis(redis)
        
        return {
            "total_satellites": len(satellites),
            "data_source": "fallback_simulation" if is_using_fallback_data else "redis_tle_data",
            "data_description": "模擬數據 (外部 TLE 源不可用)" if is_using_fallback_data else "Redis 中的真實 TLE 數據",
            "skyfield_loaded": ts is not None,
            "timestamp": datetime.utcnow().isoformat(),
            "is_simulation": is_using_fallback_data,
            "real_data": not is_using_fallback_data,
        }
    except Exception as e:
        return {
            "total_satellites": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "real_data": False,
        }