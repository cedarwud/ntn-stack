import logging
import math
import asyncio
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
from app.db.base import async_session_maker

logger = logging.getLogger(__name__)
router = APIRouter()

# 創建服務實例
satellite_repository = SQLModelSatelliteRepository(session_factory=async_session_maker)
orbit_service = OrbitService(satellite_repository=satellite_repository)
tle_service = TLEService(satellite_repository=satellite_repository)


# ===== LEO Satellite Handover 專用 API 端點 =====
# 注意：這些路由必須放在更通用的 /{satellite_id} 路由之前


@router.get("/visible", response_model=Dict[str, Any])
async def find_visible_satellites(
    observer_lat: float = Query(..., description="觀測者緯度"),
    observer_lon: float = Query(..., description="觀測者經度"),
    observer_alt: float = Query(0.0, description="觀測者高度 (km)"),
    min_elevation: float = Query(5.0, description="最小仰角，單位：度"),
    max_results: int = Query(50, description="最大結果數量"),
    constellation: Optional[str] = Query(
        None, description="星座篩選 (oneweb, starlink, etc.)"
    ),
):
    """發現當前可見的所有衛星 - Handover 候選衛星查找"""
    try:
        # 構建觀測者位置
        observer = GeoCoordinate(
            latitude=observer_lat, longitude=observer_lon, altitude=observer_alt
        )

        # 獲取所有衛星
        all_satellites = await satellite_repository.get_satellites()

        # 根據星座進行篩選
        if constellation:
            constellation_filter = constellation.upper()
            filtered_satellites = [
                sat
                for sat in all_satellites
                if constellation_filter in sat.name.upper()
            ]
        else:
            filtered_satellites = all_satellites

        # 優化：限制處理的衛星數量，提前終止搜索
        visible_satellites = []
        processed_count = 0
        max_to_process = min(len(filtered_satellites), max_results * 2)  # 限制最大處理數量

        for satellite in filtered_satellites[:max_to_process]:
            try:
                position = await orbit_service.get_current_position(
                    satellite_id=satellite.id, observer_location=observer
                )

                # 檢查是否滿足最小仰角要求
                if position.get("elevation", 0) >= min_elevation:
                    satellite_info = {
                        "id": satellite.id,
                        "name": satellite.name,
                        "norad_id": satellite.norad_id,
                        "position": {
                            "latitude": position["latitude"],
                            "longitude": position["longitude"],
                            "altitude": position["altitude"],
                            "elevation": position["elevation"],
                            "azimuth": position["azimuth"],
                            "range": position["range"],
                            "velocity": position["velocity"],
                            "doppler_shift": position.get("doppler_shift", 0),
                        },
                        "timestamp": position["timestamp"].isoformat(),
                        "signal_quality": {
                            "elevation_deg": position["elevation"],
                            "range_km": position["range"],
                            # 簡單的信號質量評估 (基於仰角和距離)
                            "estimated_signal_strength": min(
                                100, position["elevation"] * 2
                            ),
                            "path_loss_db": 20 * math.log10(max(1, position["range"]))
                            + 92.45
                            + 20 * math.log10(2.15),  # 2.15 GHz
                        },
                    }
                    visible_satellites.append(satellite_info)

                processed_count += 1

                # 如果已經找到足夠的可見衛星，停止搜索
                if len(visible_satellites) >= max_results:
                    break

                # 每處理50個衛星檢查一下是否已經夠了
                if processed_count % 50 == 0 and len(visible_satellites) >= max_results // 2:
                    break

            except Exception as e:
                logger.debug(f"計算衛星 {satellite.name} 可見性時出錯: {e}")
                continue

        # 按仰角排序 (最高的在前面)
        visible_satellites.sort(key=lambda x: x["position"]["elevation"], reverse=True)

        return {
            "success": True,
            "observer": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": observer_alt,
            },
            "search_criteria": {
                "min_elevation": min_elevation,
                "constellation": constellation,
                "max_results": max_results,
            },
            "results": {
                "total_visible": len(visible_satellites),
                "satellites": visible_satellites[:max_results],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"查找可見衛星時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找可見衛星時出錯: {str(e)}",
        )


@router.get("/handover/candidates", response_model=Dict[str, Any])
async def find_handover_candidates(
    current_satellite_id: int = Query(..., description="當前服務衛星 ID"),
    observer_lat: float = Query(..., description="觀測者緯度"),
    observer_lon: float = Query(..., description="觀測者經度"),
    observer_alt: float = Query(0.0, description="觀測者高度 (km)"),
    min_elevation: float = Query(10.0, description="最小仰角要求"),
    prediction_minutes: int = Query(5, description="預測時間範圍 (分鐘)"),
):
    """為 Handover 查找候選衛星"""
    try:
        observer = GeoCoordinate(
            latitude=observer_lat, longitude=observer_lon, altitude=observer_alt
        )

        # 獲取當前衛星狀態
        current_position = await orbit_service.get_current_position(
            satellite_id=current_satellite_id, observer_location=observer
        )

        # 預測當前衛星未來位置
        future_time = datetime.utcnow() + timedelta(minutes=prediction_minutes)
        current_satellite = await satellite_repository.get_satellite_by_id(
            current_satellite_id
        )

        # 查找所有可見的 OneWeb 衛星
        visible_response = await find_visible_satellites(
            observer_lat=observer_lat,
            observer_lon=observer_lon,
            observer_alt=observer_alt,
            min_elevation=min_elevation,
            max_results=20,
            constellation="oneweb",
        )

        visible_satellites = visible_response["results"]["satellites"]

        # 過濾掉當前衛星，並評估候選衛星
        handover_candidates = []
        for sat in visible_satellites:
            if sat["id"] != current_satellite_id:
                # 計算換手優先級分數
                elevation_score = sat["position"]["elevation"] / 90.0  # 仰角分數 (0-1)
                signal_score = min(
                    1.0, sat["signal_quality"]["estimated_signal_strength"] / 100.0
                )
                range_score = max(
                    0, 1.0 - (sat["position"]["range"] / 2000.0)
                )  # 距離分數

                # 綜合分數 (可以根據需要調整權重)
                priority_score = (
                    elevation_score * 0.5 + signal_score * 0.3 + range_score * 0.2
                ) * 100

                candidate = {
                    **sat,
                    "handover_score": round(priority_score, 2),
                    "handover_feasible": sat["position"]["elevation"] > min_elevation,
                    "estimated_service_time_minutes": max(
                        5, 90 - (sat["position"]["elevation"] / 90.0) * 85
                    ),  # 粗略估計
                }
                handover_candidates.append(candidate)

        # 按 handover 分數排序
        handover_candidates.sort(key=lambda x: x["handover_score"], reverse=True)

        return {
            "success": True,
            "current_satellite": {
                "id": current_satellite_id,
                "name": (
                    current_satellite.name
                    if current_satellite
                    else f"Satellite-{current_satellite_id}"
                ),
                "position": current_position,
                "needs_handover": current_position["elevation"]
                < min_elevation * 1.5,  # 預警閾值
            },
            "handover_candidates": handover_candidates[:10],  # 返回前10個候選
            "handover_recommendation": {
                "recommended_satellite": (
                    handover_candidates[0] if handover_candidates else None
                ),
                "urgency": (
                    "high"
                    if current_position["elevation"] < min_elevation
                    else (
                        "medium"
                        if current_position["elevation"] < min_elevation * 2
                        else "low"
                    )
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"查找 handover 候選衛星時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找 handover 候選衛星時出錯: {str(e)}",
        )


@router.post("/batch-positions", response_model=List[Dict[str, Any]])
async def get_batch_satellite_positions(
    satellite_ids: List[int],
    observer_lat: Optional[float] = Query(None, description="觀測者緯度"),
    observer_lon: Optional[float] = Query(None, description="觀測者經度"),
    observer_alt: Optional[float] = Query(0.0, description="觀測者高度 (km)"),
):
    """批量獲取多個衛星的當前位置 - Handover 決策用"""
    try:
        # 構建觀測者位置
        observer = None
        if observer_lat is not None and observer_lon is not None:
            observer = GeoCoordinate(
                latitude=observer_lat, longitude=observer_lon, altitude=observer_alt
            )

        # 批量查詢衛星位置
        positions = []
        for satellite_id in satellite_ids:
            try:
                position = await orbit_service.get_current_position(
                    satellite_id=satellite_id, observer_location=observer
                )
                position["satellite_id"] = satellite_id
                position["timestamp"] = position["timestamp"].isoformat()
                positions.append(position)
            except Exception as e:
                logger.warning(f"獲取衛星 {satellite_id} 位置失敗: {e}")
                # 添加錯誤記錄，但繼續處理其他衛星
                positions.append(
                    {
                        "satellite_id": satellite_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        return positions
    except Exception as e:
        logger.error(f"批量獲取衛星位置時出錯: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量獲取衛星位置時出錯: {str(e)}",
        )


# ===== 基礎衛星 API 端點 =====


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


@router.get("/{satellite_id}/position", response_model=Dict[str, Any])
async def get_satellite_current_position(
    satellite_id: int = Path(..., description="衛星 ID"),
    observer_lat: Optional[float] = Query(None, description="觀測者緯度"),
    observer_lon: Optional[float] = Query(None, description="觀測者經度"),
    observer_alt: Optional[float] = Query(0.0, description="觀測者高度 (km)"),
):
    """獲取衛星當前位置"""
    try:
        # 構建觀測者位置
        observer = None
        if observer_lat is not None and observer_lon is not None:
            observer = GeoCoordinate(
                latitude=observer_lat, longitude=observer_lon, altitude=observer_alt
            )

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


@router.get("/{satellite_id}/orbit/propagate", response_model=OrbitPropagationResult)
async def propagate_satellite_orbit(
    satellite_id: int = Path(..., description="衛星 ID"),
    start_time: Optional[str] = Query(None, description="開始時間 ISO 格式"),
    end_time: Optional[str] = Query(None, description="結束時間 ISO 格式"),
    step_minutes: int = Query(1, description="時間步長，單位：分鐘"),
):
    """計算衛星軌道傳播"""
    try:
        # 解析時間字符串
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        else:
            start_dt = datetime.utcnow()

        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        else:
            end_dt = start_dt + timedelta(minutes=90)

        # 調用軌道服務
        result = await orbit_service.propagate_orbit(
            satellite_id=satellite_id,
            start_time=start_dt,
            end_time=end_dt,
            step_seconds=step_minutes * 60,
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


@router.get("/{satellite_id}/passes", response_model=List[Dict[str, Any]])
async def calculate_satellite_passes(
    satellite_id: int = Path(..., description="衛星 ID"),
    observer_lat: float = Query(..., description="觀測者緯度"),
    observer_lon: float = Query(..., description="觀測者經度"),
    observer_alt: float = Query(0.0, description="觀測者高度 (km)"),
    start_time: Optional[str] = Query(None, description="開始時間 ISO 格式"),
    days: int = Query(1, description="計算天數"),
    min_elevation: float = Query(10.0, description="最小仰角，單位：度"),
):
    """計算衛星過境情況"""
    try:
        # 構建觀測者位置
        observer = GeoCoordinate(
            latitude=observer_lat, longitude=observer_lon, altitude=observer_alt
        )

        # 解析開始時間
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        else:
            start_dt = datetime.utcnow()

        # 計算結束時間
        end_dt = start_dt + timedelta(days=days)

        # 調用軌道服務
        passes = await orbit_service.calculate_passes(
            satellite_id=satellite_id,
            observer_location=observer,
            start_time=start_dt,
            end_time=end_dt,
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


@router.get("/{satellite_id}/ground-track", response_model=Dict[str, Any])
async def calculate_ground_track(
    satellite_id: int = Path(..., description="衛星 ID"),
    start_time: Optional[str] = Query(None, description="開始時間 ISO 格式"),
    duration_minutes: int = Query(100, description="持續時間，單位：分鐘"),
    step_minutes: int = Query(1, description="時間步長，單位：分鐘"),
):
    """計算衛星地面軌跡"""
    try:
        # 解析開始時間
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        else:
            start_dt = datetime.utcnow()

        # 調用軌道服務
        result = await orbit_service.calculate_ground_track(
            satellite_id=satellite_id,
            start_time=start_dt,
            duration_minutes=duration_minutes,
            step_seconds=step_minutes * 60,
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


@router.get("/{satellite_id}/visibility", response_model=Dict[str, Any])
async def calculate_visibility(
    satellite_id: int = Path(..., description="衛星 ID"),
    observer_lat: float = Query(..., description="觀測者緯度"),
    observer_lon: float = Query(..., description="觀測者經度"),
    observer_alt: float = Query(0.0, description="觀測者高度 (km)"),
    timestamp: Optional[str] = Query(None, description="時間戳 ISO 格式"),
):
    """計算衛星對於特定觀測者的可見性"""
    try:
        # 構建觀測者位置
        observer = GeoCoordinate(
            latitude=observer_lat, longitude=observer_lon, altitude=observer_alt
        )

        # 解析時間戳
        timestamp_dt = None
        if timestamp:
            timestamp_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        result = await orbit_service.calculate_visibility(
            satellite_id=satellite_id,
            observer_location=observer,
            timestamp=timestamp_dt,
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
