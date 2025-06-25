# backend/app/api/v1/router.py
from fastapi import APIRouter, Response, status, Query, Request, HTTPException
import os
from starlette.responses import FileResponse
from datetime import datetime, timedelta
import random
import time
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

# Import handover domain API router
from app.domains.handover.api.handover_api import router as handover_router
from app.domains.handover.api.fine_grained_sync_api import (
    router as fine_grained_sync_router,
)
from app.domains.handover.api.constrained_access_api import (
    router as constrained_access_router,
)

# Import testing API router
from app.api.v1.testing import router as testing_router
from app.domains.handover.api.weather_prediction_api import (
    router as weather_prediction_router,
)

# Import satellite admin API router
from app.api.v1.satellite_admin_api import router as satellite_admin_router

# Import system resource API router
from app.domains.system.api.system_api import router as system_router

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

# 全局變數初始化
ts = None
satellites = []
satellites_dict = {}
starlink_sats = []
kuiper_sats = []
oneweb_sats = []
globalstar_sats = []
iridium_sats = []


# 懶加載函數
async def initialize_satellites():
    global ts, satellites, satellites_dict, starlink_sats, kuiper_sats, oneweb_sats, globalstar_sats, iridium_sats, SKYFIELD_LOADED, SATELLITE_COUNT

    if SKYFIELD_LOADED:
        return  # 已經初始化過了

    try:
        print("開始加載 Skyfield 時間尺度和衛星數據...")
        ts = load.timescale(builtin=True)
        print("時間尺度加載成功")

        # 使用資料庫中的 Starlink + Kuiper 衛星數據
        print("從資料庫載入 Starlink + Kuiper 衛星數據...")
        from app.db.base import async_session_maker
        from app.domains.satellite.adapters.sqlmodel_satellite_repository import (
            SQLModelSatelliteRepository,
        )
        import asyncio
        import json

        async def load_satellites_from_db():
            async with async_session_maker() as session:
                repo = SQLModelSatelliteRepository()
                repo._session = session
                db_satellites = await repo.get_satellites()

                skyfield_satellites = []
                for sat in db_satellites:
                    if sat.tle_data:
                        try:
                            tle_dict = (
                                json.loads(sat.tle_data)
                                if isinstance(sat.tle_data, str)
                                else sat.tle_data
                            )
                            line1 = tle_dict["line1"]
                            line2 = tle_dict["line2"]
                            skyfield_sat = EarthSatellite(line1, line2, sat.name, ts)
                            skyfield_satellites.append(skyfield_sat)
                        except Exception as e:
                            print(f"載入衛星 {sat.name} 失敗: {e}")

                return skyfield_satellites

        satellites = await load_satellites_from_db()
        print(f"從資料庫載入衛星成功，共 {len(satellites)} 顆衛星")

        # 建立衛星字典，以名稱為鍵
        satellites_dict = {sat.name: sat for sat in satellites}

        # 獲取各衛星類別，用於顯示 (優先 Starlink + Kuiper)
        starlink_sats = [sat for sat in satellites if "STARLINK" in sat.name.upper()]
        kuiper_sats = [sat for sat in satellites if "KUIPER" in sat.name.upper()]
        oneweb_sats = [sat for sat in satellites if "ONEWEB" in sat.name.upper()]
        globalstar_sats = [
            sat for sat in satellites if "GLOBALSTAR" in sat.name.upper()
        ]
        iridium_sats = [sat for sat in satellites if "IRIDIUM" in sat.name.upper()]
        print(
            f"通信衛星統計: Starlink: {len(starlink_sats)}, Kuiper: {len(kuiper_sats)}, OneWeb: {len(oneweb_sats)}, Globalstar: {len(globalstar_sats)}, Iridium: {len(iridium_sats)}"
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

# Register handover domain API router
api_router.include_router(handover_router, prefix="/handover", tags=["Handover"])

# Register fine-grained sync API router
api_router.include_router(fine_grained_sync_router)

# Register constrained access API router
api_router.include_router(constrained_access_router)

# Register weather prediction API router
api_router.include_router(weather_prediction_router)

# Register satellite admin API router
api_router.include_router(satellite_admin_router)

# Register testing API router
api_router.include_router(testing_router, prefix="/testing", tags=["Testing"])

# Register system resource API router
api_router.include_router(system_router, prefix="/system", tags=["System"])


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


# 添加衛星軌跡端點
@api_router.get("/satellite-ops/orbit/{satellite_id}", tags=["Satellites"])
async def get_satellite_orbit(
    satellite_id: str,
    duration: int = Query(600, description="預測持續時間（秒）"),
    step: int = Query(60, description="計算步長（秒）"),
):
    """獲取指定衛星的軌跡數據"""
    try:

        # 由於目前使用模擬數據，生成基於軌道動力學的軌跡點
        import math
        from datetime import datetime, timedelta

        start_time = datetime.utcnow()
        points = []

        # 模擬OneWeb衛星軌道參數
        orbital_period = 109 * 60  # 109分鐘軌道週期
        altitude = 1200  # km
        inclination = 87.9  # 度

        # 生成多個完整的衛星過境軌跡
        total_points = duration // step
        observer_lat, observer_lon = 24.786667, 120.996944

        # 為不同衛星創建不同的過境軌跡
        satellite_hash = hash(satellite_id) % 10  # 基於衛星ID的種子

        # 每個衛星有不同的過境路徑（在循環外定義）
        base_azimuth_start = 30 + (satellite_hash * 30) % 360  # 不同起始方位
        azimuth_span = 120 + (satellite_hash * 20) % 100  # 不同跨越角度
        max_elevation = 20 + (satellite_hash * 10) % 70  # 不同最大仰角

        for i in range(total_points):
            current_time = start_time + timedelta(seconds=i * step)

            # 每次過境約12分鐘，間隔約100分鐘（符合LEO軌道特性）
            total_cycle = 100 * 60  # 100分鐘完整週期
            transit_duration = 12 * 60  # 12分鐘可見時間
            gap_duration = total_cycle - transit_duration  # 間隔時間

            # 計算在週期中的位置
            cycle_position = (i * step) % total_cycle

            if cycle_position < transit_duration:
                # 在過境階段 - 真實的升降軌跡
                transit_progress = cycle_position / transit_duration

                azimuth_deg = (
                    base_azimuth_start + azimuth_span * transit_progress
                ) % 360

                # 拋物線形仰角變化：從地平線升起，到最高點，再落下
                elevation_deg = max_elevation * math.sin(transit_progress * math.pi)
                elevation_deg = max(0, elevation_deg)

            else:
                # 在不可見階段（地平線以下）
                elevation_deg = (
                    -10 - (cycle_position - transit_duration) / gap_duration * 30
                )
                azimuth_deg = (
                    base_azimuth_start
                    + azimuth_span
                    + (cycle_position - transit_duration) / gap_duration * 240
                ) % 360

            # 計算地理位置（對所有點，包括不可見的）
            azimuth_rad = math.radians(azimuth_deg)

            # 對於地平線以下的點，使用固定距離
            if elevation_deg <= 0:
                distance_factor = 2000  # 地平線以下使用固定距離
            else:
                distance_factor = 1200 / max(math.sin(math.radians(elevation_deg)), 0.1)
                distance_factor = min(distance_factor, 2000)

            angular_distance = distance_factor / 111.32
            latitude = observer_lat + angular_distance * math.cos(azimuth_rad) * 0.1
            longitude = observer_lon + angular_distance * math.sin(azimuth_rad) * 0.1

            # 限制範圍
            latitude = max(-90, min(90, latitude))
            longitude = longitude % 360
            if longitude > 180:
                longitude -= 360

            points.append(
                {
                    "timestamp": current_time.isoformat(),
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude": altitude,
                    "elevation_deg": elevation_deg,
                    "azimuth_deg": azimuth_deg,
                }
            )

        return {
            "satellite_id": satellite_id,
            "satellite_name": f"Satellite-{satellite_id}",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(seconds=duration)).isoformat(),
            "points": points,
        }

    except Exception as e:
        print(f"Failed to get satellite orbit: {e}")  # 使用print替代logger
        import traceback

        traceback.print_exc()
        return {"error": str(e), "points": []}


# 添加臨時的衛星可見性模擬端點
@api_router.get("/satellite-ops/visible_satellites", tags=["Satellites"])
async def get_visible_satellites(
    count: int = Query(100, gt=0, le=200, description="返回衛星數量，預設100顆"),
    min_elevation_deg: float = Query(
        -10.0, ge=-90, le=90, description="最小仰角，預設-10度(全球視野)"
    ),
    observer_lat: float = Query(0.0, ge=-90, le=90, description="觀察者緯度，預設赤道"),
    observer_lon: float = Query(
        0.0, ge=-180, le=180, description="觀察者經度，預設本初子午線"
    ),
    observer_alt: float = Query(0, ge=0, le=10000, description="觀察者高度(米)"),
    global_view: bool = Query(
        True, description="全球視野模式(預設啟用，獲取所有Starlink+Kuiper衛星)"
    ),
):
    """返回全球範圍的Starlink和Kuiper衛星數據，不受地理位置限制"""
    start_time = time.time()
    print(
        f"API 調用: get_visible_satellites(count={count}, min_elevation_deg={min_elevation_deg}, observer=({observer_lat}, {observer_lon}, {observer_alt}), global_view={global_view})"
    )

    # 優化：只在必要時重新載入衛星數據
    if not SKYFIELD_LOADED:
        await initialize_satellites()

    print(f"Skyfield 狀態: 已加載={SKYFIELD_LOADED}, 衛星數量={SATELLITE_COUNT}")

    if not SKYFIELD_LOADED or ts is None or not satellites:
        # 不使用模擬數據，而是拋出錯誤確保只使用真實數據
        error_msg = f"無法載入真實衛星數據 - SKYFIELD_LOADED={SKYFIELD_LOADED}, satellites_count={len(satellites)}"
        print(f"❌ {error_msg}")
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail=error_msg)

    try:
        # 計算真實衛星數據
        print(
            f"計算真實衛星數據... 觀測點: ({observer_lat}, {observer_lon}, {observer_alt}m)"
        )

        # 使用 wgs84 創建觀測點
        observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_alt)

        # 獲取當前時間
        now = ts.now()
        print(f"當前時間: {now.utc_datetime()}")

        # 計算所有衛星在觀測點的方位角、仰角和距離
        visible_satellites = []

        # 優先考慮通信衛星 (Starlink + Kuiper 優先)
        priority_sats = (
            starlink_sats + kuiper_sats + oneweb_sats + globalstar_sats + iridium_sats
        )
        other_sats = [sat for sat in satellites if sat not in priority_sats]
        all_sats = priority_sats + other_sats

        print(f"開始計算衛星可見性，共 {len(all_sats)} 顆衛星")
        processed_count = 0
        visible_count = 0

        # 根據是否為全球視野模式調整處理邏輯
        max_process = 2000 if global_view else 500  # 全球模式處理更多衛星
        effective_min_elevation = (
            -20.0 if global_view else min_elevation_deg
        )  # 全球模式大幅降低仰角限制

        print(
            f"全球視野模式: {global_view}, 處理衛星數: {max_process}, 有效仰角限制: {effective_min_elevation}°"
        )

        # 並行計算每個衛星的可見性
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def calculate_satellite_visibility(sat):
            """計算單個衛星的可見性"""
            try:
                # 計算方位角、仰角和距離
                difference = sat - observer
                topocentric = difference.at(now)
                alt, az, distance = topocentric.altaz()

                # 全球視野模式：大幅降低仰角要求，優先獲取通信衛星
                elevation_threshold = effective_min_elevation
                if global_view:
                    # 全球模式下，接受負仰角的衛星（地平線以下也包含）
                    elevation_threshold = max(-30.0, min_elevation_deg - 10.0)

                    # 對於通信衛星（Starlink, Kuiper等），進一步放寬限制
                    sat_name_upper = sat.name.upper()
                    if any(
                        constellation in sat_name_upper
                        for constellation in ["STARLINK", "KUIPER", "ONEWEB"]
                    ):
                        elevation_threshold = -45.0  # 通信衛星可以接受更低仰角

                # 檢查衛星是否高於最低仰角
                if alt.degrees >= elevation_threshold:
                    # 計算軌道信息
                    geocentric = sat.at(now)
                    subpoint = geocentric.subpoint()

                    # 計算速度（近似值）
                    velocity = np.linalg.norm(geocentric.velocity.km_per_s)

                    # 估計可見時間（粗略計算）
                    visible_for_sec = int(
                        1000 * (max(0, alt.degrees + 30) / 120.0)
                    )  # 調整計算公式

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

                    return satellite_info
                return None
            except Exception as e:
                print(f"計算衛星 {sat.name} 位置時出錯: {e}")
                return None

        # 使用線程池並行處理衛星計算
        calc_start_time = time.time()
        with ThreadPoolExecutor(max_workers=min(16, max_process)) as executor:
            # 提交所有計算任務
            futures = [
                executor.submit(calculate_satellite_visibility, sat) 
                for sat in all_sats[:max_process]
            ]
            
            # 收集結果
            for future in futures:
                processed_count += 1
                result = future.result()
                if result is not None:
                    visible_count += 1
                    visible_satellites.append(result)
                    
                    # 如果已經收集了足夠的衛星，可以提前停止（但要等待正在運行的任務完成）
                    if len(visible_satellites) >= count * 2:  # 收集更多以便排序選擇最佳的
                        break
        
        calc_time = time.time() - calc_start_time
        print(f"並行計算完成: 耗時 {calc_time:.2f}s, 並行效率提升: {max_process/calc_time:.1f} satellites/sec")

        print(
            f"處理完成: 處理了 {processed_count} 顆衛星，找到 {visible_count} 顆可見衛星，返回 {len(visible_satellites)} 顆"
        )

        # 按仰角從高到低排序
        visible_satellites.sort(key=lambda x: x.elevation_deg, reverse=True)

        # 限制返回的衛星數量（保留這個邏輯，以防實際衛星數量超過請求數量）
        visible_satellites = visible_satellites[:count]

        total_time = time.time() - start_time
        print(f"🚀 API 性能: 總耗時 {total_time:.2f}s (計算: {calc_time:.2f}s, 其他: {total_time-calc_time:.2f}s)")

        return {
            "satellites": visible_satellites,
            "status": "real",
            "processed": processed_count,
            "visible": visible_count,
            "observer": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": observer_alt,
            },
            "global_view": global_view,
            "performance": {
                "total_time_ms": round(total_time * 1000),
                "calculation_time_ms": round(calc_time * 1000),
                "satellites_per_second": round(processed_count / calc_time, 1),
                "optimization": "parallel_processing_enabled"
            }
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
