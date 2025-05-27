import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

import numpy as np
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.elementslib import osculating_elements_of
from skyfield.timelib import Time

from app.domains.coordinates.models.coordinate_model import GeoCoordinate
from app.domains.satellite.models.satellite_model import (
    OrbitPropagationResult,
    OrbitPoint,
    SatellitePass,
)
from app.domains.satellite.interfaces.orbit_service_interface import (
    OrbitServiceInterface,
)
from app.domains.satellite.interfaces.satellite_repository import (
    SatelliteRepositoryInterface,
)
from app.domains.satellite.adapters.sqlmodel_satellite_repository import (
    SQLModelSatelliteRepository,
)

logger = logging.getLogger(__name__)

# 全局 Skyfield 時間尺度對象
try:
    ts = load.timescale(builtin=True)
except Exception as e:
    logger.error(f"無法加載 Skyfield 時間尺度: {e}")
    ts = None


class OrbitService(OrbitServiceInterface):
    """軌道服務實現"""

    def __init__(
        self, satellite_repository: Optional[SatelliteRepositoryInterface] = None
    ):
        self._satellite_repository = (
            satellite_repository or SQLModelSatelliteRepository()
        )

    def _create_skyfield_satellite(
        self, tle_line1: str, tle_line2: str
    ) -> EarthSatellite:
        """根據 TLE 數據創建 Skyfield 衛星對象"""
        if ts is None:
            raise RuntimeError("Skyfield 時間尺度不可用，無法進行軌道計算")
        return EarthSatellite(tle_line1, tle_line2, ts=ts)

    async def propagate_orbit(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
    ) -> OrbitPropagationResult:
        """計算衛星軌道傳播"""
        if ts is None:
            raise RuntimeError("Skyfield 時間尺度不可用，無法進行軌道計算")

        # 獲取衛星數據
        satellite = await self._satellite_repository.get_satellite_by_id(satellite_id)
        if not satellite:
            raise ValueError(f"找不到 ID 為 {satellite_id} 的衛星")

        if (
            not satellite.tle_data
            or "line1" not in satellite.tle_data
            or "line2" not in satellite.tle_data
        ):
            raise ValueError(f"衛星 {satellite.name} 缺少有效的 TLE 數據")

        # 創建 Skyfield 衛星對象
        sf_satellite = self._create_skyfield_satellite(
            satellite.tle_data["line1"], satellite.tle_data["line2"]
        )

        # 生成時間點
        total_seconds = (end_time - start_time).total_seconds()
        steps = int(total_seconds / step_seconds) + 1

        # 計算每個時間點的軌道位置
        orbit_points = []

        for i in range(steps):
            current_time = start_time + timedelta(seconds=i * step_seconds)
            t = ts.from_datetime(current_time)

            # 計算衛星位置（地心慣性坐標系）
            geocentric = sf_satellite.at(t)

            # 轉換為地理坐標
            subpoint = geocentric.subpoint()

            orbit_points.append(
                OrbitPoint(
                    timestamp=current_time,
                    latitude=subpoint.latitude.degrees,
                    longitude=subpoint.longitude.degrees,
                    altitude=subpoint.elevation.km,
                )
            )

        return OrbitPropagationResult(
            satellite_id=satellite.id,
            satellite_name=satellite.name,
            start_time=start_time,
            end_time=end_time,
            points=orbit_points,
        )

    async def calculate_passes(
        self,
        satellite_id: int,
        observer_location: GeoCoordinate,
        start_time: datetime,
        end_time: datetime,
        min_elevation: float = 10.0,
    ) -> List[SatellitePass]:
        """計算衛星過境情況"""
        if ts is None:
            raise RuntimeError("Skyfield 時間尺度不可用，無法進行過境計算")

        # 獲取衛星數據
        satellite = await self._satellite_repository.get_satellite_by_id(satellite_id)
        if not satellite:
            raise ValueError(f"找不到 ID 為 {satellite_id} 的衛星")

        if (
            not satellite.tle_data
            or "line1" not in satellite.tle_data
            or "line2" not in satellite.tle_data
        ):
            raise ValueError(f"衛星 {satellite.name} 缺少有效的 TLE 數據")

        # 創建 Skyfield 衛星對象
        sf_satellite = self._create_skyfield_satellite(
            satellite.tle_data["line1"], satellite.tle_data["line2"]
        )

        # 創建觀測者位置
        observer = wgs84.latlon(
            latitude_degrees=observer_location.latitude,
            longitude_degrees=observer_location.longitude,
            elevation_m=observer_location.altitude or 0.0,
        )

        # 創建時間範圍
        t0 = ts.from_datetime(start_time)
        t1 = ts.from_datetime(end_time)

        # 計算衛星過境
        t, events = sf_satellite.find_events(
            observer, t0, t1, altitude_degrees=min_elevation
        )

        # 處理過境數據
        passes = []
        current_pass = None

        for ti, event in zip(t, events):
            time = ti.utc_datetime()

            # 計算當前方位角和仰角
            difference = sf_satellite - observer
            topocentric = difference.at(ti)
            alt, az, distance = topocentric.altaz()

            if event == 0:  # 升起
                current_pass = {
                    "rise_time": time,
                    "rise_azimuth": az.degrees,
                    "max_alt_time": None,
                    "max_alt_degree": 0.0,
                    "set_time": None,
                    "set_azimuth": 0.0,
                    "satellite_id": satellite_id,
                    "ground_station_lat": observer_location.latitude,
                    "ground_station_lon": observer_location.longitude,
                    "ground_station_alt": observer_location.altitude,
                }
            elif event == 1:  # 最大仰角
                if current_pass:
                    current_pass["max_alt_time"] = time
                    current_pass["max_alt_degree"] = alt.degrees
            elif event == 2:  # 落下
                if current_pass and current_pass["max_alt_time"]:
                    current_pass["set_time"] = time
                    current_pass["set_azimuth"] = az.degrees
                    duration = (
                        current_pass["set_time"] - current_pass["rise_time"]
                    ).total_seconds()

                    # 創建 SatellitePass 對象
                    passes.append(
                        SatellitePass(
                            **current_pass,
                            duration_seconds=duration,
                            pass_type=self._determine_pass_type(
                                current_pass["max_alt_degree"]
                            ),
                        )
                    )
                    current_pass = None

        # 儲存過境數據到資料庫
        saved_passes = []
        for pass_data in passes:
            # 將 Pydantic 模型轉換為字典
            pass_dict = pass_data.model_dump()

            # 保存到資料庫
            try:
                saved_pass = await self._satellite_repository.save_satellite_pass(
                    pass_dict
                )
                saved_passes.append(saved_pass)
            except Exception as e:
                logger.error(f"保存過境數據時出錯: {e}")

        return saved_passes

    def _determine_pass_type(self, max_elevation: float) -> str:
        """根據最大仰角確定過境類型"""
        if max_elevation >= 60:
            return "excellent"
        elif max_elevation >= 30:
            return "good"
        elif max_elevation >= 15:
            return "moderate"
        else:
            return "poor"

    async def get_current_position(
        self, satellite_id: int, observer_location: Optional[GeoCoordinate] = None
    ) -> Dict[str, Any]:
        """獲取衛星當前位置"""
        if ts is None:
            raise RuntimeError("Skyfield 時間尺度不可用，無法獲取衛星位置")

        # 獲取衛星數據
        satellite = await self._satellite_repository.get_satellite_by_id(satellite_id)
        if not satellite:
            raise ValueError(f"找不到 ID 為 {satellite_id} 的衛星")

        if (
            not satellite.tle_data
            or "line1" not in satellite.tle_data
            or "line2" not in satellite.tle_data
        ):
            raise ValueError(f"衛星 {satellite.name} 缺少有效的 TLE 數據")

        # 創建 Skyfield 衛星對象
        sf_satellite = self._create_skyfield_satellite(
            satellite.tle_data["line1"], satellite.tle_data["line2"]
        )

        # 當前時間
        t = ts.now()

        # 計算衛星位置
        geocentric = sf_satellite.at(t)
        subpoint = geocentric.subpoint()

        # 基本位置信息
        position = {
            "satellite_id": satellite_id,
            "satellite_name": satellite.name,
            "timestamp": t.utc_datetime(),
            "latitude": subpoint.latitude.degrees,
            "longitude": subpoint.longitude.degrees,
            "altitude": subpoint.elevation.km,
            "velocity": self._calculate_velocity(sf_satellite, t),
        }

        # 如果提供了觀測者位置，計算相對於觀測者的數據
        if observer_location:
            observer = wgs84.latlon(
                latitude_degrees=observer_location.latitude,
                longitude_degrees=observer_location.longitude,
                elevation_m=observer_location.altitude or 0.0,
            )

            difference = sf_satellite - observer
            topocentric = difference.at(t)
            alt, az, distance = topocentric.altaz()

            position.update(
                {
                    "elevation": alt.degrees,
                    "azimuth": az.degrees,
                    "range_km": distance.km,
                    "visible": alt.degrees > 0,  # 如果仰角 > 0，則衛星可見
                }
            )

        return position

    def _calculate_velocity(
        self, satellite: EarthSatellite, t: Time
    ) -> Dict[str, float]:
        """計算衛星速度"""
        try:
            # 獲取衛星位置和速度向量
            geocentric = satellite.at(t)

            # 從地心慣性坐標中提取速度分量
            _, velocity, _ = geocentric._position_and_velocity_teme_km()

            # 計算速度大小
            speed = math.sqrt(sum(v * v for v in velocity))

            return {
                "x": float(velocity[0]),
                "y": float(velocity[1]),
                "z": float(velocity[2]),
                "speed": float(speed),
            }
        except Exception as e:
            logger.error(f"計算速度時出錯: {e}")
            return {"speed": 0.0}

    async def calculate_ground_track(
        self,
        satellite_id: int,
        start_time: datetime,
        revolutions: float = 1.0,
        step_seconds: int = 60,
    ) -> Dict[str, Any]:
        """計算衛星地面軌跡"""
        if ts is None:
            raise RuntimeError("Skyfield 時間尺度不可用，無法計算地面軌跡")

        # 獲取衛星數據
        satellite = await self._satellite_repository.get_satellite_by_id(satellite_id)
        if not satellite:
            raise ValueError(f"找不到 ID 為 {satellite_id} 的衛星")

        if (
            not satellite.tle_data
            or "line1" not in satellite.tle_data
            or "line2" not in satellite.tle_data
        ):
            raise ValueError(f"衛星 {satellite.name} 缺少有效的 TLE 數據")

        # 創建 Skyfield 衛星對象
        sf_satellite = self._create_skyfield_satellite(
            satellite.tle_data["line1"], satellite.tle_data["line2"]
        )

        # 估算軌道周期（秒）
        t = ts.from_datetime(start_time)
        elements = osculating_elements_of(sf_satellite.at(t))
        period_minutes = (
            2 * math.pi * math.sqrt(elements.semi_major_axis.km**3 / 398600.4418) / 60
        )

        # 計算結束時間
        end_time = start_time + timedelta(minutes=period_minutes * revolutions)

        # 生成軌跡點
        result = await self.propagate_orbit(
            satellite_id=satellite_id,
            start_time=start_time,
            end_time=end_time,
            step_seconds=step_seconds,
        )

        # 提取軌跡點坐標
        coordinates = [(point.longitude, point.latitude) for point in result.points]

        # 處理經度跨越 180 度的情況
        processed_coordinates = []
        for i, (lon, lat) in enumerate(coordinates):
            if i > 0:
                prev_lon = coordinates[i - 1][0]
                # 如果經度差超過 180 度，說明跨越了日期變更線
                if abs(lon - prev_lon) > 180:
                    # 在軌跡中插入 None 來分隔
                    processed_coordinates.append(None)
            processed_coordinates.append((lon, lat))

        return {
            "satellite_id": satellite.id,
            "satellite_name": satellite.name,
            "start_time": start_time,
            "end_time": end_time,
            "period_minutes": period_minutes,
            "revolutions": revolutions,
            "coordinates": processed_coordinates,
        }

    async def calculate_visibility(
        self,
        satellite_id: int,
        observer_location: GeoCoordinate,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """計算衛星對於特定觀測者的可見性"""
        # 使用當前時間（如果未提供）
        timestamp = timestamp or datetime.utcnow()

        # 獲取衛星當前位置（包含可見性信息）
        position = await self.get_current_position(
            satellite_id=satellite_id, observer_location=observer_location
        )

        # 獲取未來 24 小時的過境數據
        start_time = timestamp
        end_time = timestamp + timedelta(hours=24)

        passes = await self.calculate_passes(
            satellite_id=satellite_id,
            observer_location=observer_location,
            start_time=start_time,
            end_time=end_time,
        )

        # 整理過境數據
        visibility_data = {
            "satellite_id": satellite_id,
            "satellite_name": position["satellite_name"],
            "current": {
                "visible": position.get("visible", False),
                "elevation": position.get("elevation"),
                "azimuth": position.get("azimuth"),
                "range_km": position.get("range_km"),
                "timestamp": position["timestamp"],
            },
            "next_passes": [
                {
                    "rise_time": p.rise_time,
                    "set_time": p.set_time,
                    "max_alt_time": p.max_alt_time,
                    "max_alt_degree": p.max_alt_degree,
                    "duration_seconds": p.duration_seconds,
                    "pass_type": p.pass_type,
                }
                for p in passes[:5]  # 只返回前 5 次過境
            ],
        }
