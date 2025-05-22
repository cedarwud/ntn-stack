import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from app.domains.coordinates.models.coordinate_model import GeoCoordinate
from app.domains.satellite.models.satellite_model import (
    Satellite,
    SatellitePass,
    OrbitPoint,
    OrbitPropagationResult,
)
from app.domains.satellite.services.orbit_service import OrbitService
from app.domains.satellite.services.tle_service import TLEService
from app.domains.satellite.adapters.sqlmodel_satellite_repository import (
    SQLModelSatelliteRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# 創建服務實例
satellite_repository = SQLModelSatelliteRepository()
orbit_service = OrbitService(satellite_repository=satellite_repository)
tle_service = TLEService(satellite_repository=satellite_repository)


@router.get("/", response_model=List[Dict[str, Any]])
async def get_satellites(search: Optional[str] = Query(None, description="搜尋關鍵詞")):
    """獲取所有衛星或搜尋特定衛星"""
    try:
        if search:
            satellites = await satellite_repository.search_satellites(search)
        else:
            satellites = await satellite_repository.get_satellites()

        # 轉換為可序列化格式
        result = []
        for sat in satellites:
            sat_dict = {
                "id": sat.id,
                "name": sat.name,
                "norad_id": sat.norad_id,
                "international_designator": sat.international_designator,
                "period_minutes": sat.period_minutes,
                "inclination_deg": sat.inclination_deg,
                "apogee_km": sat.apogee_km,
                "perigee_km": sat.perigee_km,
                "last_updated": (
                    sat.last_updated.isoformat() if sat.last_updated else None
                ),
            }
            result.append(sat_dict)

        return result
    except Exception as e:
        logger.error(f"獲取衛星時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取衛星時出錯: {str(e)}",
        )


@router.get("/{satellite_id}", response_model=Dict[str, Any])
async def get_satellite_by_id(satellite_id: int = Path(..., description="衛星 ID")):
    """根據 ID 獲取特定衛星"""
    satellite = await satellite_repository.get_satellite_by_id(satellite_id)
    if not satellite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ID 為 {satellite_id} 的衛星",
        )

    # 轉換為可序列化格式
    result = {
        "id": satellite.id,
        "name": satellite.name,
        "norad_id": satellite.norad_id,
        "international_designator": satellite.international_designator,
        "launch_date": (
            satellite.launch_date.isoformat() if satellite.launch_date else None
        ),
        "decay_date": (
            satellite.decay_date.isoformat() if satellite.decay_date else None
        ),
        "period_minutes": satellite.period_minutes,
        "inclination_deg": satellite.inclination_deg,
        "apogee_km": satellite.apogee_km,
        "perigee_km": satellite.perigee_km,
        "tle_data": satellite.tle_data,
        "last_updated": (
            satellite.last_updated.isoformat() if satellite.last_updated else None
        ),
    }

    return result


@router.post("/{satellite_id}/update-tle", response_model=Dict[str, Any])
async def update_satellite_tle(
    satellite_id: int = Path(..., description="衛星 ID"),
):
    """更新特定衛星的 TLE 數據"""
    try:
        satellite = await satellite_repository.get_satellite_by_id(satellite_id)
        if not satellite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到 ID 為 {satellite_id} 的衛星",
            )

        result = await tle_service.update_satellite_tle(satellite.norad_id)

        if result:
            # 重新獲取更新後的衛星數據
            updated_satellite = await satellite_repository.get_satellite_by_id(
                satellite_id
            )
            return {
                "success": True,
                "message": f"成功更新衛星 {updated_satellite.name} 的 TLE 數據",
                "satellite": {
                    "id": updated_satellite.id,
                    "name": updated_satellite.name,
                    "norad_id": updated_satellite.norad_id,
                    "last_updated": (
                        updated_satellite.last_updated.isoformat()
                        if updated_satellite.last_updated
                        else None
                    ),
                },
            }
        else:
            return {
                "success": False,
                "message": f"更新衛星 {satellite.name} 的 TLE 數據失敗",
                "satellite": {
                    "id": satellite.id,
                    "name": satellite.name,
                    "norad_id": satellite.norad_id,
                },
            }
    except Exception as e:
        logger.error(f"更新衛星 TLE 數據時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新衛星 TLE 數據時出錯: {str(e)}",
        )


@router.post("/update-all-tles", response_model=Dict[str, Any])
async def update_all_tles():
    """更新所有衛星的 TLE 數據"""
    try:
        result = await tle_service.update_all_tles()
        return {
            "success": True,
            "message": f"更新了 {result['updated']} 個衛星的 TLE 數據，失敗 {result['failed']} 個",
            "details": result,
        }
    except Exception as e:
        logger.error(f"更新所有衛星 TLE 數據時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新所有衛星 TLE 數據時出錯: {str(e)}",
        )


@router.post("/{satellite_id}/orbit", response_model=OrbitPropagationResult)
async def propagate_satellite_orbit(
    satellite_id: int = Path(..., description="衛星 ID"),
    start_time: Optional[datetime] = Query(None, description="開始時間，UTC"),
    end_time: Optional[datetime] = Query(None, description="結束時間，UTC"),
    step_seconds: int = Query(60, description="時間步長，單位：秒"),
):
    """計算衛星軌道傳播"""
    try:
        # 如果未提供開始時間，使用當前時間
        if not start_time:
            start_time = datetime.utcnow()

        # 如果未提供結束時間，使用開始時間加 90 分鐘（典型軌道周期）
        if not end_time:
            end_time = start_time + timedelta(minutes=90)

        # 調用軌道服務
        result = await orbit_service.propagate_orbit(
            satellite_id=satellite_id,
            start_time=start_time,
            end_time=end_time,
            step_seconds=step_seconds,
        )

        return result
    except ValueError as e:
        logger.error(f"計算軌道傳播時出現值錯誤: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"計算軌道傳播時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"計算軌道傳播時出錯: {str(e)}",
        )


@router.post("/{satellite_id}/passes", response_model=List[Dict[str, Any]])
async def calculate_satellite_passes(
    satellite_id: int = Path(..., description="衛星 ID"),
    observer: GeoCoordinate = None,
    start_time: Optional[datetime] = Query(None, description="開始時間，UTC"),
    days: int = Query(3, description="計算天數"),
    min_elevation: float = Query(10.0, description="最小仰角，單位：度"),
):
    """計算衛星過境情況"""
    try:
        # 檢查觀測者位置是否提供
        if not observer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必須提供觀測者位置 (observer)",
            )

        # 如果未提供開始時間，使用當前時間
        if not start_time:
            start_time = datetime.utcnow()

        # 計算結束時間
        end_time = start_time + timedelta(days=days)

        # 調用軌道服務
        passes = await orbit_service.calculate_passes(
            satellite_id=satellite_id,
            observer_location=observer,
            start_time=start_time,
            end_time=end_time,
            min_elevation=min_elevation,
        )

        # 轉換為可序列化格式
        result = []
        for p in passes:
            pass_dict = {
                "rise_time": p.rise_time.isoformat(),
                "rise_azimuth": p.rise_azimuth,
                "max_alt_time": p.max_alt_time.isoformat() if p.max_alt_time else None,
                "max_alt_degree": p.max_alt_degree,
                "set_time": p.set_time.isoformat() if p.set_time else None,
                "set_azimuth": p.set_azimuth,
                "duration_seconds": p.duration_seconds,
                "pass_type": p.pass_type,
            }
            result.append(pass_dict)

        return result
    except ValueError as e:
        logger.error(f"計算衛星過境時出現值錯誤: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"計算衛星過境時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"計算衛星過境時出錯: {str(e)}",
        )


@router.post("/{satellite_id}/position", response_model=Dict[str, Any])
async def get_satellite_current_position(
    satellite_id: int = Path(..., description="衛星 ID"),
    observer: Optional[GeoCoordinate] = None,
):
    """獲取衛星當前位置"""
    try:
        position = await orbit_service.get_current_position(
            satellite_id=satellite_id, observer_location=observer
        )

        # 轉換 datetime 為 ISO 格式字符串
        position["timestamp"] = position["timestamp"].isoformat()

        return position
    except ValueError as e:
        logger.error(f"獲取衛星位置時出現值錯誤: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"獲取衛星位置時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取衛星位置時出錯: {str(e)}",
        )


@router.post("/{satellite_id}/ground-track", response_model=Dict[str, Any])
async def calculate_ground_track(
    satellite_id: int = Path(..., description="衛星 ID"),
    start_time: Optional[datetime] = Query(None, description="開始時間，UTC"),
    revolutions: float = Query(1.0, description="軌道圈數"),
    step_seconds: int = Query(60, description="時間步長，單位：秒"),
):
    """計算衛星地面軌跡"""
    try:
        # 如果未提供開始時間，使用當前時間
        if not start_time:
            start_time = datetime.utcnow()

        # 調用軌道服務
        result = await orbit_service.calculate_ground_track(
            satellite_id=satellite_id,
            start_time=start_time,
            revolutions=revolutions,
            step_seconds=step_seconds,
        )

        # 轉換 datetime 為 ISO 格式字符串
        result["start_time"] = result["start_time"].isoformat()
        result["end_time"] = result["end_time"].isoformat()

        return result
    except ValueError as e:
        logger.error(f"計算地面軌跡時出現值錯誤: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"計算地面軌跡時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"計算地面軌跡時出錯: {str(e)}",
        )


@router.post("/{satellite_id}/visibility", response_model=Dict[str, Any])
async def calculate_visibility(
    satellite_id: int = Path(..., description="衛星 ID"),
    observer: GeoCoordinate = None,
    timestamp: Optional[datetime] = Query(None, description="時間戳，UTC"),
):
    """計算衛星對於特定觀測者的可見性"""
    try:
        # 檢查觀測者位置是否提供
        if not observer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必須提供觀測者位置 (observer)",
            )

        result = await orbit_service.calculate_visibility(
            satellite_id=satellite_id, observer_location=observer, timestamp=timestamp
        )

        # 轉換 datetime 為 ISO 格式字符串
        result["current"]["timestamp"] = result["current"]["timestamp"].isoformat()

        # 轉換過境時間
        for pass_data in result["next_passes"]:
            pass_data["rise_time"] = pass_data["rise_time"].isoformat()
            pass_data["set_time"] = (
                pass_data["set_time"].isoformat() if pass_data["set_time"] else None
            )
            pass_data["max_alt_time"] = (
                pass_data["max_alt_time"].isoformat()
                if pass_data["max_alt_time"]
                else None
            )

        return result
    except ValueError as e:
        logger.error(f"計算衛星可見性時出現值錯誤: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"計算衛星可見性時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"計算衛星可見性時出錯: {str(e)}",
        )
