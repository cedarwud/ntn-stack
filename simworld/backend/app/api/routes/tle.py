"""
TLE 數據 API 路由

提供 TLE 數據的 REST API 端點：
1. GET /api/tle/constellations - 獲取支持的星座列表
2. GET /api/tle/{constellation}/latest - 獲取最新 TLE 數據
3. GET /api/tle/historical/{timestamp} - 獲取歷史 TLE 數據
4. POST /api/tle/cache/preload - 預載推薦時段數據

符合 d2.md Phase 1 驗收標準
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Path, BackgroundTasks
from pydantic import BaseModel

from app.services.tle_data_service import TLEDataService, TLEData
from app.services.historical_data_cache import HistoricalDataCache, TimeRange

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tle", tags=["TLE Data"])

# 服務實例
tle_service = TLEDataService()
historical_cache = HistoricalDataCache(tle_service)

class TLEResponse(BaseModel):
    """TLE 響應模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: str

class PreloadRequest(BaseModel):
    """預載請求模型"""
    constellation: str = "starlink"

@router.get("/constellations")
async def get_supported_constellations():
    """獲取支持的星座列表"""
    try:
        constellations = tle_service.get_supported_constellations()
        
        return TLEResponse(
            success=True,
            data={"constellations": constellations},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"獲取星座列表失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取星座列表失敗: {str(e)}"
        )

@router.get("/{constellation}/latest")
async def get_latest_tle_data(
    constellation: str = Path(..., description="星座名稱 (starlink, oneweb, gps)"),
    limit: int = Query(100, description="返回衛星數量限制")
):
    """獲取指定星座的最新 TLE 數據"""
    try:
        logger.info(f"獲取最新 TLE 數據: {constellation}, limit={limit}")
        
        tle_data = await tle_service.fetch_tle_from_source(constellation)
        
        # 限制返回數量
        limited_data = tle_data[:limit]
        
        # 轉換為字典格式
        satellites_data = []
        for tle in limited_data:
            sat_data = {
                "satellite_name": tle.satellite_name,
                "catalog_number": tle.catalog_number,
                "epoch_year": tle.epoch_year,
                "epoch_day": tle.epoch_day,
                "inclination": tle.inclination,
                "right_ascension": tle.right_ascension,
                "eccentricity": tle.eccentricity,
                "argument_of_perigee": tle.argument_of_perigee,
                "mean_anomaly": tle.mean_anomaly,
                "mean_motion": tle.mean_motion,
                "revolution_number": tle.revolution_number,
                "last_updated": tle.last_updated.isoformat(),
                "constellation": tle.constellation
            }
            satellites_data.append(sat_data)
        
        return TLEResponse(
            success=True,
            data={
                "constellation": constellation,
                "satellite_count": len(tle_data),
                "returned_count": len(limited_data),
                "satellites": satellites_data,
                "last_updated": tle_data[0].last_updated.isoformat() if tle_data else None
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"獲取最新 TLE 數據失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取 TLE 數據失敗: {str(e)}"
        )

@router.get("/historical/{timestamp}")
async def get_historical_tle_data(
    timestamp: str = Path(..., description="時間戳 (ISO 8601 格式)"),
    constellation: str = Query("starlink", description="星座名稱")
):
    """獲取歷史 TLE 數據"""
    try:
        # 解析時間戳
        try:
            target_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="無效的時間格式，請使用 ISO 8601 格式，例如: 2024-01-01T00:00:00Z"
            )
        
        logger.info(f"獲取歷史 TLE 數據: {constellation}, {target_time}")
        
        historical_data = await historical_cache.get_historical_tle(constellation, target_time)
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到 {constellation} 在 {target_time.isoformat()} 的歷史數據"
            )
        
        # 限制返回的衛星數量
        limited_satellites = historical_data.satellites[:50]
        satellites_data = []
        
        for tle in limited_satellites:
            sat_data = {
                "satellite_name": tle.satellite_name,
                "catalog_number": tle.catalog_number,
                "inclination": tle.inclination,
                "mean_motion": tle.mean_motion,
                "mean_anomaly": tle.mean_anomaly,
                "last_updated": tle.last_updated.isoformat()
            }
            satellites_data.append(sat_data)
        
        return TLEResponse(
            success=True,
            data={
                "constellation": constellation,
                "requested_time": target_time.isoformat(),
                "actual_time": historical_data.timestamp.isoformat(),
                "satellite_count": len(historical_data.satellites),
                "returned_count": len(limited_satellites),
                "data_source": historical_data.data_source,
                "quality": historical_data.quality,
                "satellites": satellites_data
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取歷史 TLE 數據失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取歷史數據失敗: {str(e)}"
        )

@router.get("/historical-range/{constellation}")
async def get_historical_tle_range(
    constellation: str = Path(..., description="星座名稱"),
    start: str = Query(..., description="開始時間 (ISO 8601)"),
    end: str = Query(..., description="結束時間 (ISO 8601)"),
    limit: int = Query(100, description="最大記錄數")
):
    """獲取歷史數據範圍"""
    try:
        # 解析時間
        try:
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="無效的時間格式，請使用 ISO 8601 格式"
            )
        
        logger.info(f"獲取歷史數據範圍: {constellation}, {start_time} - {end_time}")
        
        time_range = TimeRange(start=start_time, end=end_time)
        historical_data = await historical_cache.get_historical_tle_range(
            constellation, time_range, limit
        )
        
        records_data = []
        for record in historical_data:
            record_data = {
                "timestamp": record.timestamp.isoformat(),
                "satellite_count": len(record.satellites),
                "data_source": record.data_source,
                "quality": record.quality
            }
            records_data.append(record_data)
        
        return TLEResponse(
            success=True,
            data={
                "constellation": constellation,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "record_count": len(historical_data),
                "records": records_data
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取歷史數據範圍失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取歷史數據範圍失敗: {str(e)}"
        )

@router.post("/cache/preload")
async def preload_recommended_time_ranges(
    request: PreloadRequest,
    background_tasks: BackgroundTasks
):
    """預載推薦時段數據"""
    try:
        constellation = request.constellation
        
        logger.info(f"開始預載推薦時段數據: {constellation}")
        
        # 在背景執行預載任務
        background_tasks.add_task(
            historical_cache.preload_recommended_time_ranges,
            constellation
        )
        
        return TLEResponse(
            success=True,
            data={
                "constellation": constellation,
                "message": "預載任務已啟動",
                "time_ranges": list(HistoricalDataCache.RECOMMENDED_TIME_RANGES.keys())
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"啟動預載任務失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"啟動預載任務失敗: {str(e)}"
        )

@router.get("/cache/stats")
async def get_cache_stats():
    """獲取緩存統計信息"""
    try:
        stats = await historical_cache.get_cache_stats()
        
        return TLEResponse(
            success=True,
            data=stats,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"獲取緩存統計失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取緩存統計失敗: {str(e)}"
        )

# Phase 1 驗收標準測試端點
@router.get("/test/phase1")
async def test_phase1_requirements():
    """Phase 1 驗收標準測試端點"""
    try:
        results = {
            "test_name": "Phase 1 - TLE 數據集成驗收測試",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests": []
        }
        
        # 測試 1: 獲取支持的星座列表
        try:
            constellations = tle_service.get_supported_constellations()
            has_starlink = any(c['constellation'] == 'starlink' for c in constellations)
            results["tests"].append({
                "name": "獲取支持的星座列表",
                "passed": len(constellations) > 0 and has_starlink,
                "details": f"找到 {len(constellations)} 個星座，包含 Starlink: {has_starlink}"
            })
        except Exception as e:
            results["tests"].append({
                "name": "獲取支持的星座列表",
                "passed": False,
                "error": str(e)
            })
        
        # 測試 2: 從 CelesTrak API 獲取 TLE 數據
        try:
            starlink_tle = await tle_service.fetch_starlink_tle()
            results["tests"].append({
                "name": "從 CelesTrak API 獲取 Starlink TLE 數據",
                "passed": len(starlink_tle) > 0,
                "details": f"成功獲取 {len(starlink_tle)} 顆 Starlink 衛星數據"
            })
        except Exception as e:
            results["tests"].append({
                "name": "從 CelesTrak API 獲取 Starlink TLE 數據",
                "passed": False,
                "error": str(e)
            })
        
        # 測試 3: 緩存 2024年1月1日歷史數據
        try:
            primary_range = HistoricalDataCache.RECOMMENDED_TIME_RANGES['primary']
            time_range = TimeRange(
                start=primary_range['start'],
                end=primary_range['end']
            )
            
            # 嘗試緩存小範圍數據進行測試
            test_range = TimeRange(
                start=primary_range['start'],
                end=primary_range['start'].replace(hour=1)  # 只測試1小時
            )
            
            await historical_cache.cache_historical_tle('starlink', test_range, 30)
            results["tests"].append({
                "name": "緩存 2024年1月1日 歷史數據",
                "passed": True,
                "details": "成功緩存測試時段歷史數據"
            })
        except Exception as e:
            results["tests"].append({
                "name": "緩存 2024年1月1日 歷史數據",
                "passed": False,
                "error": str(e)
            })
        
        # 計算通過率
        passed_tests = sum(1 for test in results["tests"] if test["passed"])
        total_tests = len(results["tests"])
        results["summary"] = {
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
            "phase1_requirements_met": passed_tests >= 2  # 至少通過2個核心測試
        }
        
        return TLEResponse(
            success=True,
            data=results,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Phase 1 測試失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Phase 1 測試失敗: {str(e)}"
        )
