# backend/app/api/v1/router.py
from fastapi import APIRouter, Response, status, Query, Request, HTTPException
import os
from starlette.responses import FileResponse
from datetime import datetime, timedelta
import random
from typing import List, Optional
from pydantic import BaseModel

# Import new domain API routers
from app.domains.device.api.device_api import router as device_router

# 恢復領域API路由
from app.domains.coordinates.api.coordinate_api import router as coordinates_router
from app.domains.satellite.api.satellite_api import router as satellite_router
from app.domains.simulation.api.simulation_api import router as simulation_router

# Import wireless domain API router
from app.domains.wireless.api.wireless_api import router as wireless_router

# Import interference domain API router
from app.domains.interference.api.interference_api import router as interference_router

# Import CQRS services
from app.domains.satellite.services.cqrs_satellite_service import (
    CQRSSatelliteService,
    SatellitePosition,
)
from app.domains.coordinates.models.coordinate_model import GeoCoordinate

# Import Skyfield and numpy
from skyfield.api import load, wgs84, EarthSatellite
import numpy as np

# 全局狀態變數，用於調試
SKYFIELD_LOADED = False
SATELLITE_COUNT = 0

# 嘗試加載時間尺度和衛星數據
try:
    print("開始加載 Skyfield 時間尺度和衛星數據...")
    ts = load.timescale(builtin=True)
    print("時間尺度加載成功")

    # 優先使用 Celestrak 的活躍衛星數據
    print("從 Celestrak 下載衛星數據...")
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    satellites = load.tle_file(url)
    print(f"衛星數據下載成功，共 {len(satellites)} 顆衛星")

    # 建立衛星字典，以名稱為鍵
    satellites_dict = {sat.name: sat for sat in satellites}

    # 獲取各衛星類別，用於顯示
    starlink_sats = [sat for sat in satellites if "STARLINK" in sat.name.upper()]
    oneweb_sats = [sat for sat in satellites if "ONEWEB" in sat.name.upper()]
    globalstar_sats = [sat for sat in satellites if "GLOBALSTAR" in sat.name.upper()]
    iridium_sats = [sat for sat in satellites if "IRIDIUM" in sat.name.upper()]
    print(
        f"通信衛星統計: Starlink: {len(starlink_sats)}, OneWeb: {len(oneweb_sats)}, Globalstar: {len(globalstar_sats)}, Iridium: {len(iridium_sats)}"
    )

    SKYFIELD_LOADED = True
    SATELLITE_COUNT = len(satellites)

except Exception as e:
    print(f"錯誤：無法加載 Skyfield 數據: {e}")
    ts = None
    satellites = []
    satellites_dict = {}
    SKYFIELD_LOADED = False
    SATELLITE_COUNT = 0

api_router = APIRouter()

# Register domain API routers
api_router.include_router(device_router, prefix="/devices", tags=["Devices"])
# 恢復領域API路由
api_router.include_router(
    coordinates_router, prefix="/coordinates", tags=["Coordinates"]
)
api_router.include_router(satellite_router, prefix="/satellites", tags=["Satellites"])
api_router.include_router(
    simulation_router, prefix="/simulations", tags=["Simulations"]
)

# Register wireless domain API router
api_router.include_router(wireless_router, prefix="/wireless", tags=["Wireless"])

# Register interference domain API router
api_router.include_router(interference_router, tags=["Interference"])


# 添加模型資源路由
@api_router.get("/sionna/models/{model_name}", tags=["Models"])
async def get_model(model_name: str):
    """提供3D模型文件"""
    # 定義模型文件存儲路徑
    static_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "static",
    )
    models_dir = os.path.join(static_dir, "models")

    # 獲取對應的模型文件
    model_file = os.path.join(models_dir, f"{model_name}.glb")

    # 檢查文件是否存在
    if not os.path.exists(model_file):
        return Response(
            content=f"模型 {model_name} 不存在", status_code=status.HTTP_404_NOT_FOUND
        )

    # 返回模型文件
    return FileResponse(
        path=model_file, media_type="model/gltf-binary", filename=f"{model_name}.glb"
    )


# 添加場景資源路由
@api_router.get("/scenes/{scene_name}/model", tags=["Scenes"])
async def get_scene_model(scene_name: str):
    """提供3D場景模型文件"""
    # 定義場景文件存儲路徑
    static_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "static",
    )
    scenes_dir = os.path.join(static_dir, "scenes")
    scene_dir = os.path.join(scenes_dir, scene_name)

    # 獲取對應的場景模型文件
    model_file = os.path.join(scene_dir, f"{scene_name}.glb")

    # 檢查文件是否存在
    if not os.path.exists(model_file):
        return Response(
            content=f"場景 {scene_name} 的模型不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 返回場景模型文件
    return FileResponse(
        path=model_file, media_type="model/gltf-binary", filename=f"{scene_name}.glb"
    )


# 定義衛星可見性數據模型
class VisibleSatelliteInfo(BaseModel):
    norad_id: str
    name: str
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    velocity_km_s: float
    visible_for_sec: int
    orbit_altitude_km: float
    magnitude: Optional[float] = None


# 添加臨時的衛星可見性模擬端點
@api_router.get("/satellite-ops/visible_satellites", tags=["Satellites"])
async def get_visible_satellites(
    count: int = Query(10, gt=0, le=100),
    min_elevation_deg: float = Query(0, ge=0, le=90),
):
    """返回基於 24.786667, 120.996944 位置可見的真實衛星數據"""
    print(
        f"API 調用: get_visible_satellites(count={count}, min_elevation_deg={min_elevation_deg})"
    )
    print(f"Skyfield 狀態: 已加載={SKYFIELD_LOADED}, 衛星數量={SATELLITE_COUNT}")

    # 使用台灣新竹附近的固定坐標作為觀測點
    observer_lat = 24.786667
    observer_lon = 120.996944
    print(f"觀測點座標: ({observer_lat}, {observer_lon})")

    if not SKYFIELD_LOADED or ts is None or not satellites:
        # 如果 Skyfield 數據未加載成功，返回模擬數據
        print("使用模擬數據，因為 Skyfield 未成功加載")
        sim_satellites = []
        for i in range(count):
            # 生成隨機衛星數據
            elevation = random.uniform(min_elevation_deg, 90)
            satellite = VisibleSatelliteInfo(
                norad_id=f"SIM-{40000 + i}",
                name=f"SIM-SAT-{1000 + i}",
                elevation_deg=elevation,
                azimuth_deg=random.uniform(0, 360),
                distance_km=random.uniform(500, 2000),
                velocity_km_s=random.uniform(5, 8),
                visible_for_sec=int(random.uniform(300, 1200)),
                orbit_altitude_km=random.uniform(500, 1200),
                magnitude=random.uniform(1, 5),
            )
            sim_satellites.append(satellite)

        # 按仰角從高到低排序
        sim_satellites.sort(key=lambda x: x.elevation_deg, reverse=True)

        return {"satellites": sim_satellites, "status": "simulated"}

    try:
        # 計算真實衛星數據
        print("計算真實衛星數據...")

        # 使用 wgs84 創建觀測點
        observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=0)

        # 獲取當前時間
        now = ts.now()
        print(f"當前時間: {now.utc_datetime()}")

        # 計算所有衛星在觀測點的方位角、仰角和距離
        visible_satellites = []

        # 優先考慮通信衛星
        priority_sats = starlink_sats + oneweb_sats + globalstar_sats + iridium_sats
        other_sats = [sat for sat in satellites if sat not in priority_sats]
        all_sats = priority_sats + other_sats

        print(f"開始計算衛星可見性，共 {len(all_sats)} 顆衛星")
        processed_count = 0
        visible_count = 0

        # 計算每個衛星的可見性
        for sat in all_sats[:500]:  # 限制處理數量，避免超時
            processed_count += 1
            try:
                # 計算方位角、仰角和距離
                difference = sat - observer
                topocentric = difference.at(now)
                alt, az, distance = topocentric.altaz()

                # 檢查衛星是否高於最低仰角
                if alt.degrees >= min_elevation_deg:
                    visible_count += 1
                    # 計算軌道信息
                    geocentric = sat.at(now)
                    subpoint = geocentric.subpoint()

                    # 計算速度（近似值）
                    velocity = np.linalg.norm(geocentric.velocity.km_per_s)

                    # 估計可見時間（粗略計算）
                    visible_for_sec = int(1000 * (alt.degrees / 90.0))  # 粗略估計

                    # 創建衛星信息對象
                    satellite_info = VisibleSatelliteInfo(
                        norad_id=str(sat.model.satnum),
                        name=sat.name,
                        elevation_deg=round(alt.degrees, 2),
                        azimuth_deg=round(az.degrees, 2),
                        distance_km=round(distance.km, 2),
                        velocity_km_s=round(float(velocity), 2),
                        visible_for_sec=visible_for_sec,
                        orbit_altitude_km=round(subpoint.elevation.km, 2),
                        magnitude=round(random.uniform(1, 5), 1),  # 星等是粗略估計
                    )

                    visible_satellites.append(satellite_info)

                    # 如果已經收集了足夠的衛星，停止
                    if len(visible_satellites) >= count:
                        print(f"已找到足夠的衛星: {len(visible_satellites)}")
                        break
            except Exception as e:
                print(f"計算衛星 {sat.name} 位置時出錯: {e}")
                continue

        print(
            f"處理完成: 處理了 {processed_count} 顆衛星，找到 {visible_count} 顆可見衛星"
        )

        # 按仰角從高到低排序
        visible_satellites.sort(key=lambda x: x.elevation_deg, reverse=True)

        # 限制返回的衛星數量（保留這個邏輯，以防實際衛星數量超過請求數量）
        visible_satellites = visible_satellites[:count]

        return {
            "satellites": visible_satellites,
            "status": "real",
            "processed": processed_count,
            "visible": visible_count,
        }

    except Exception as e:
        print(f"計算衛星位置時發生錯誤: {e}")
        # 發生錯誤時返回模擬數據
        sim_satellites = []
        for i in range(count):
            elevation = random.uniform(min_elevation_deg, 90)
            satellite = VisibleSatelliteInfo(
                norad_id=f"SIM-ERROR-{i}",
                name=f"ERROR-SIM-{i}",
                elevation_deg=elevation,
                azimuth_deg=random.uniform(0, 360),
                distance_km=random.uniform(500, 2000),
                velocity_km_s=random.uniform(5, 8),
                visible_for_sec=int(random.uniform(300, 1200)),
                orbit_altitude_km=random.uniform(500, 1200),
                magnitude=random.uniform(1, 5),
            )
            sim_satellites.append(satellite)

        return {"satellites": sim_satellites, "status": "error", "error": str(e)}


# ===== UAV 位置追蹤端點 =====


class UAVPosition(BaseModel):
    """UAV 位置模型"""

    uav_id: str
    latitude: float
    longitude: float
    altitude: float
    timestamp: str
    speed: Optional[float] = None
    heading: Optional[float] = None


class UAVPositionResponse(BaseModel):
    """UAV 位置響應模型"""

    success: bool
    message: str
    uav_id: str
    received_at: str
    channel_update_triggered: bool = False


# UAV 位置儲存（簡單的記憶體儲存，生產環境應使用資料庫）
uav_positions = {}


@api_router.post("/uav/position", tags=["UAV Tracking"])
async def update_uav_position(position: UAVPosition):
    """
    更新 UAV 位置

    接收來自 NetStack 的 UAV 位置更新，並觸發 Sionna 信道模型重計算

    Args:
        position: UAV 位置資訊

    Returns:
        更新結果
    """
    try:
        # 儲存位置資訊
        uav_positions[position.uav_id] = {
            "latitude": position.latitude,
            "longitude": position.longitude,
            "altitude": position.altitude,
            "timestamp": position.timestamp,
            "speed": position.speed,
            "heading": position.heading,
            "last_updated": datetime.utcnow().isoformat(),
        }

        # 觸發信道模型更新（這裡可以添加實際的 Sionna 整合邏輯）
        channel_update_triggered = await trigger_channel_model_update(position)

        return UAVPositionResponse(
            success=True,
            message=f"UAV {position.uav_id} 位置更新成功",
            uav_id=position.uav_id,
            received_at=datetime.utcnow().isoformat(),
            channel_update_triggered=channel_update_triggered,
        )

    except Exception as e:
        return UAVPositionResponse(
            success=False,
            message=f"位置更新失敗: {str(e)}",
            uav_id=position.uav_id,
            received_at=datetime.utcnow().isoformat(),
        )


@api_router.get("/uav/{uav_id}/position", tags=["UAV Tracking"])
async def get_uav_position(uav_id: str):
    """
    獲取 UAV 當前位置

    Args:
        uav_id: UAV ID

    Returns:
        UAV 位置資訊
    """
    if uav_id not in uav_positions:
        return Response(
            content=f"找不到 UAV {uav_id} 的位置資訊",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return {"success": True, "uav_id": uav_id, "position": uav_positions[uav_id]}


@api_router.get("/uav/positions", tags=["UAV Tracking"])
async def get_all_uav_positions():
    """
    獲取所有 UAV 位置

    Returns:
        所有 UAV 的位置資訊
    """
    return {
        "success": True,
        "total_uavs": len(uav_positions),
        "positions": uav_positions,
    }


@api_router.delete("/uav/{uav_id}/position", tags=["UAV Tracking"])
async def delete_uav_position(uav_id: str):
    """
    刪除 UAV 位置記錄

    Args:
        uav_id: UAV ID

    Returns:
        刪除結果
    """
    if uav_id in uav_positions:
        del uav_positions[uav_id]
        return {"success": True, "message": f"UAV {uav_id} 位置記錄已刪除"}
    else:
        return Response(
            content=f"找不到 UAV {uav_id} 的位置記錄",
            status_code=status.HTTP_404_NOT_FOUND,
        )


async def trigger_channel_model_update(position: UAVPosition) -> bool:
    """
    觸發 Sionna 信道模型更新

    Args:
        position: UAV 位置

    Returns:
        是否成功觸發更新
    """
    try:
        # 這裡可以添加實際的 Sionna 信道模型更新邏輯
        # 例如：
        # 1. 計算 UAV 與衛星的距離和角度
        # 2. 更新路徑損耗模型
        # 3. 計算都卜勒頻移
        # 4. 更新多路徑衰落參數

        # 現在只是模擬觸發
        print(
            f"觸發 Sionna 信道模型更新: UAV {position.uav_id} at ({position.latitude}, {position.longitude}, {position.altitude}m)"
        )

        # 模擬一些信道參數計算
        import math

        # 假設衛星在 600km 高度
        satellite_altitude = 600000  # 米
        uav_altitude = position.altitude

        # 計算直線距離（簡化計算）
        distance_to_satellite = math.sqrt(
            (satellite_altitude - uav_altitude) ** 2
            + (position.latitude * 111000) ** 2
            + (position.longitude * 111000) ** 2
        )

        # 計算路徑損耗（自由空間損耗）
        frequency_hz = 2.15e9  # 2.15 GHz
        c = 3e8  # 光速
        path_loss_db = (
            20 * math.log10(distance_to_satellite)
            + 20 * math.log10(frequency_hz)
            + 20 * math.log10(4 * math.pi / c)
        )

        print(
            f"計算結果: 距離={distance_to_satellite/1000:.1f}km, 路徑損耗={path_loss_db:.1f}dB"
        )

        return True

    except Exception as e:
        print(f"信道模型更新失敗: {e}")
        return False


# 添加新的 CQRS 衛星端點
@api_router.post(
    "/satellite/{satellite_id}/position-cqrs",
    summary="獲取衛星位置 (CQRS)",
    description="使用 CQRS 架構獲取衛星當前位置",
)
async def get_satellite_position_cqrs(
    satellite_id: int,
    observer_lat: Optional[float] = None,
    observer_lon: Optional[float] = None,
    observer_alt: Optional[float] = None,
    request: Request = None,
):
    """使用 CQRS 架構獲取衛星位置"""
    try:
        # 獲取 CQRS 服務
        cqrs_service: CQRSSatelliteService = request.app.state.cqrs_satellite_service

        # 構建觀測者位置
        observer = None
        if observer_lat is not None and observer_lon is not None:
            observer = GeoCoordinate(
                latitude=observer_lat,
                longitude=observer_lon,
                altitude=observer_alt or 0.0,
            )

        # 查詢衛星位置（讀端）
        position = await cqrs_service.get_satellite_position(satellite_id, observer)

        if not position:
            raise HTTPException(
                status_code=404, detail=f"衛星 {satellite_id} 位置數據不存在"
            )

        return {
            "success": True,
            "architecture": "CQRS",
            "satellite_position": position.to_dict(),
            "cache_hit": True,  # CQRS 查詢總是從快取獲取
        }

    except Exception as e:
        logger.error(f"CQRS 衛星位置查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@api_router.post(
    "/satellite/batch-positions-cqrs",
    summary="批量獲取衛星位置 (CQRS)",
    description="使用 CQRS 架構批量獲取多個衛星位置",
)
async def get_batch_satellite_positions_cqrs(
    satellite_ids: List[int],
    observer_lat: Optional[float] = None,
    observer_lon: Optional[float] = None,
    observer_alt: Optional[float] = None,
    request: Request = None,
):
    """使用 CQRS 架構批量獲取衛星位置"""
    try:
        cqrs_service: CQRSSatelliteService = request.app.state.cqrs_satellite_service

        # 構建觀測者位置
        observer = None
        if observer_lat is not None and observer_lon is not None:
            observer = GeoCoordinate(
                latitude=observer_lat,
                longitude=observer_lon,
                altitude=observer_alt or 0.0,
            )

        # 批量查詢（讀端）
        positions = await cqrs_service.get_multiple_positions(satellite_ids, observer)

        return {
            "success": True,
            "architecture": "CQRS",
            "requested_count": len(satellite_ids),
            "returned_count": len(positions),
            "satellite_positions": [pos.to_dict() for pos in positions],
        }

    except Exception as e:
        logger.error(f"CQRS 批量位置查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批量查詢失敗: {str(e)}")


@api_router.post(
    "/satellite/{satellite_id}/force-update-cqrs",
    summary="強制更新衛星位置 (CQRS)",
    description="使用 CQRS 命令端強制更新衛星位置",
)
async def force_update_satellite_position_cqrs(
    satellite_id: int,
    observer_lat: Optional[float] = None,
    observer_lon: Optional[float] = None,
    observer_alt: Optional[float] = None,
    request: Request = None,
):
    """使用 CQRS 架構強制更新衛星位置（命令端）"""
    try:
        cqrs_service: CQRSSatelliteService = request.app.state.cqrs_satellite_service

        # 構建觀測者位置
        observer = None
        if observer_lat is not None and observer_lon is not None:
            observer = GeoCoordinate(
                latitude=observer_lat,
                longitude=observer_lon,
                altitude=observer_alt or 0.0,
            )

        # 命令：更新衛星位置
        position = await cqrs_service.update_satellite_position(satellite_id, observer)

        return {
            "success": True,
            "architecture": "CQRS",
            "operation": "command_update",
            "satellite_position": position.to_dict(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"CQRS 衛星位置更新失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")


@api_router.post(
    "/satellite/{satellite_id}/trajectory-cqrs",
    summary="計算衛星軌跡 (CQRS)",
    description="使用 CQRS 架構計算衛星軌跡",
)
async def calculate_satellite_trajectory_cqrs(
    satellite_id: int,
    start_time: str,  # ISO format
    end_time: str,  # ISO format
    step_seconds: int = 60,
    request: Request = None,
):
    """使用 CQRS 架構計算衛星軌跡（命令端）"""
    try:
        cqrs_service: CQRSSatelliteService = request.app.state.cqrs_satellite_service

        # 解析時間
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        # 命令：計算軌跡
        trajectory = await cqrs_service.calculate_orbit(
            satellite_id, start_dt, end_dt, step_seconds
        )

        return {
            "success": True,
            "architecture": "CQRS",
            "operation": "command_calculate_orbit",
            "satellite_id": satellite_id,
            "start_time": start_time,
            "end_time": end_time,
            "step_seconds": step_seconds,
            "trajectory_points": len(trajectory),
            "trajectory": [pos.to_dict() for pos in trajectory],
        }

    except Exception as e:
        logger.error(f"CQRS 軌跡計算失敗: {e}")
        raise HTTPException(status_code=500, detail=f"軌跡計算失敗: {str(e)}")


@api_router.get(
    "/satellite/visible-cqrs",
    summary="查詢可見衛星 (CQRS)",
    description="使用 CQRS 架構查詢指定位置可見的衛星",
)
async def find_visible_satellites_cqrs(
    observer_lat: float,
    observer_lon: float,
    observer_alt: float = 0.0,
    radius_km: float = 2000.0,
    max_results: int = 50,
    request: Request = None,
):
    """使用 CQRS 架構查詢可見衛星（查詢端）"""
    try:
        cqrs_service: CQRSSatelliteService = request.app.state.cqrs_satellite_service

        # 構建觀測者位置
        observer = GeoCoordinate(
            latitude=observer_lat, longitude=observer_lon, altitude=observer_alt
        )

        # 查詢：查找可見衛星
        visible_satellites = await cqrs_service.find_visible_satellites(
            observer, radius_km, max_results
        )

        return {
            "success": True,
            "architecture": "CQRS",
            "operation": "query_visible_satellites",
            "observer": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": observer_alt,
            },
            "search_radius_km": radius_km,
            "visible_count": len(visible_satellites),
            "visible_satellites": [sat.to_dict() for sat in visible_satellites],
        }

    except Exception as e:
        logger.error(f"CQRS 可見衛星查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@api_router.get(
    "/cqrs/satellite-service/stats",
    summary="獲取 CQRS 服務統計",
    description="獲取 CQRS 衛星服務的性能統計和指標",
)
async def get_cqrs_satellite_service_stats(request: Request):
    """獲取 CQRS 衛星服務統計"""
    try:
        cqrs_service: CQRSSatelliteService = request.app.state.cqrs_satellite_service

        # 獲取服務統計
        stats = await cqrs_service.get_service_stats()

        return {
            "success": True,
            "architecture": "CQRS",
            "service_stats": stats,
            "patterns_implemented": [
                "Command Query Responsibility Segregation (CQRS)",
                "Event Sourcing",
                "Multi-layer Caching",
                "Read/Write Separation",
                "Async Processing",
            ],
        }

    except Exception as e:
        logger.error(f"獲取 CQRS 統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"統計查詢失敗: {str(e)}")
