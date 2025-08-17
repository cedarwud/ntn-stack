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
    """從 NetStack Redis 中載入真實 TLE 數據 (Phase 2 集成)"""
    global ts, satellites_cache, cache_timestamp, is_using_fallback_data

    # 檢查緩存是否有效
    if (
        cache_timestamp
        and datetime.utcnow() - cache_timestamp < timedelta(seconds=CACHE_DURATION)
        and satellites_cache
    ):
        logger.info(f"Returning cached satellites: {len(satellites_cache)} satellites")
        return satellites_cache

    logger.info("Loading satellites from NetStack Redis TLE data...")

    # 初始化 Skyfield 時間尺度
    if ts is None:
        ts = load.timescale(builtin=True)

    satellites = {}

    try:
        # Phase 2 集成：直接從 Redis 中讀取 NetStack TLE 數據
        constellation_keys = ["starlink", "oneweb"]
        total_satellites_loaded = 0
        
        for constellation in constellation_keys:
            try:
                # 從 Redis 讀取 NetStack TLE 數據
                redis_key = f"netstack_tle_data:{constellation}"
                tle_data_json = await redis.get(redis_key)
                
                if tle_data_json:
                    tle_data_list = json.loads(tle_data_json)
                    logger.info(f"✅ 從 NetStack Redis 載入 {constellation} TLE 數據: {len(tle_data_list)} 顆衛星")
                    
                    for sat_data in tle_data_list:
                        try:
                            name = sat_data.get("name", f"{constellation.upper()}-{sat_data.get('norad_id')}")
                            line1 = sat_data.get("line1", "")
                            line2 = sat_data.get("line2", "")
                            
                            if line1 and line2:
                                satellite = EarthSatellite(line1, line2, name, ts)
                                satellites[name] = satellite
                                total_satellites_loaded += 1
                            else:
                                logger.debug(f"TLE data missing for {name}")
                        except Exception as e:
                            logger.debug(f"Failed to load {constellation} satellite {sat_data.get('name', 'unknown')}: {e}")
                            continue
                else:
                    logger.warning(f"No NetStack TLE data found in Redis for {constellation}")
                    
            except Exception as e:
                logger.warning(f"Error loading {constellation} from NetStack Redis: {e}")
                continue

        # 更新緩存
        satellites_cache = satellites
        cache_timestamp = datetime.utcnow()

        # 檢查是否成功載入真實數據
        if satellites and total_satellites_loaded > 100:  # 至少需要100顆衛星才算成功
            is_using_fallback_data = False
            logger.info(f"✅ 從 NetStack Redis 載入真實 TLE 數據: {len(satellites)} 顆衛星")
            logger.info("🎯 數據來源: NetStack 本地 TLE 文件 (真實軌道數據)")
            return satellites
        else:
            logger.warning(f"🔴 NetStack Redis 衛星數據不足 ({total_satellites_loaded} 顆)，使用 fallback 機制")
            satellites = await _load_fallback_satellites()
            is_using_fallback_data = True
            logger.warning(f"⚠️  正在使用模擬數據: {len(satellites)} 顆衛星 (NetStack 數據不足)")
            return satellites

    except Exception as e:
        logger.error(f"❌ NetStack Redis 連接失敗: {e}")
        # Redis 不可用時使用 fallback 數據
        logger.warning("🔴 NetStack Redis 不可用，使用 fallback 衛星數據")
        is_using_fallback_data = True
        fallback_satellites = await _load_fallback_satellites()
        logger.warning(f"⚠️  正在使用模擬數據: {len(fallback_satellites)} 顆衛星 (Redis 連接失敗)")
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
    獲取可見衛星列表 - 使用預處理數據 (enhanced_satellite_data.json)
    """
    try:
        # 優先使用預處理數據
        from app.services.local_volume_data_service import LocalVolumeDataService
        local_service = LocalVolumeDataService()
        
        # 嘗試從預處理數據獲取衛星位置
        satellites_from_precomputed = await local_service.get_visible_satellites_from_precomputed(
            observer_lat=observer_lat,
            observer_lon=observer_lon,
            min_elevation_deg=min_elevation_deg,
            constellation=constellation,
            count=count,
            global_view=global_view
        )
        
        if satellites_from_precomputed:
            logger.info(f"✅ 使用預處理數據: {len(satellites_from_precomputed)} 顆可見衛星")
            return {
                "satellites": satellites_from_precomputed[:count],
                "total_count": len(satellites_from_precomputed),
                "requested_count": count,
                "constellation": constellation,
                "global_view": global_view,
                "timestamp": datetime.utcnow().isoformat(),
                "observer_location": {
                    "lat": observer_lat,
                    "lon": observer_lon,
                    "alt": observer_alt / 1000.0
                },
                "data_source": {
                    "type": "f3_a1_precomputed",
                    "description": "F3/A1階段預處理軌道數據 (2250 顆真實衛星)",
                    "is_simulation": False
                }
            }
        
        # Fallback: 嘗試從 Redis 載入
        logger.warning("⚠️ 預處理數據不可用，嘗試從 Redis 載入")
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
    """獲取衛星統計資訊 - 基於 NetStack TLE 數據"""
    try:
        redis = await get_redis_client(request)
        
        # 直接從 Redis 讀取 NetStack 統計信息
        total_satellites = 0
        constellations = {}
        
        for constellation in ["starlink", "oneweb"]:
            stats_key = f"netstack_tle_stats:{constellation}"
            stats_data = await redis.get(stats_key)
            
            if stats_data:
                stats = json.loads(stats_data)
                count = stats.get("count", 0)
                total_satellites += count
                constellations[constellation] = {
                    "count": count,
                    "last_updated": stats.get("last_updated"),
                    "source": stats.get("source", "netstack_local_file")
                }
        
        # 載入衛星以檢查是否使用 fallback
        satellites = await load_satellites_from_redis(redis)
        
        return {
            "total_satellites": total_satellites,
            "constellations": constellations,
            "data_source": "netstack_tle_files",
            "data_description": "NetStack 本地 TLE 數據文件數據",
            "is_real_time": True,
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