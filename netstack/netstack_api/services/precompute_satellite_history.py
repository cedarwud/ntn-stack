#!/usr/bin/env python3
"""
衛星歷史數據預計算器 - Phase 2 核心組件

基於真實 TLE 數據和 SGP4 算法，實現高精度的衛星軌道預計算。
符合 3GPP NTN 標準和論文研究要求的真實數據處理。
"""

import math
import structlog
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from sgp4.api import Satrec, jday
from sgp4 import omm

from .orbit_calculation_engine import TLEData, Position, SatellitePosition
from .tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)


@dataclass
class ObserverPosition:
    """觀測者位置"""

    latitude: float  # 緯度 (度)
    longitude: float  # 經度 (度)
    altitude: float  # 海拔高度 (米)


@dataclass
class PrecomputeResult:
    """預計算結果"""

    timestamp: datetime
    satellite_id: str
    norad_id: int
    satellite_name: str
    constellation: str
    observer_position: ObserverPosition
    satellite_position: Dict[str, Any]
    signal_quality: Dict[str, float]
    calculation_method: str = "SGP4"
    data_quality: float = 1.0


class SatelliteHistoryPrecomputer:
    """
    衛星歷史數據預計算器

    基於真實 TLE 數據實現高精度軌道計算：
    1. 使用 SGP4 算法進行軌道預測
    2. 計算衛星相對觀測者的位置和角度
    3. 估算信號強度和路徑損耗
    4. 支援多星座並行計算
    """

    def __init__(
        self,
        tle_data: List[Dict],
        observer_coords: Tuple[float, float, float],
        time_range: Tuple[datetime, datetime],
    ):
        """
        初始化預計算器

        Args:
            tle_data: TLE 數據列表 (來自 TLEDataManager)
            observer_coords: 觀測者坐標 (緯度, 經度, 海拔米)
            time_range: 時間範圍 (開始時間, 結束時間)
        """
        self.logger = structlog.get_logger(__name__)
        self.tle_data = tle_data
        self.observer = ObserverPosition(
            latitude=observer_coords[0],
            longitude=observer_coords[1],
            altitude=observer_coords[2],
        )
        self.time_range = time_range

        # 台灣觀測點配置 (符合 Phase 1 數據庫擴展)
        self.taiwan_observers = {
            "ntpu": ObserverPosition(24.94417, 121.37139, 50.0),  # NTPU
            "nycu": ObserverPosition(24.78717, 120.99717, 50.0),  # NYCU
            "ntu": ObserverPosition(25.01713, 121.54187, 50.0),  # NTU
            "ncku": ObserverPosition(22.99617, 120.22167, 50.0),  # NCKU
        }

        # 預處理 TLE 數據為 SGP4 衛星對象
        self.satellites = self._prepare_satellites()

        self.logger.info(
            "衛星歷史預計算器初始化完成",
            satellite_count=len(self.satellites),
            observer_lat=self.observer.latitude,
            observer_lon=self.observer.longitude,
            time_start=self.time_range[0].isoformat(),
            time_end=self.time_range[1].isoformat(),
        )

    def compute_history(
        self, time_interval_seconds: int = 30
    ) -> List[PrecomputeResult]:
        """
        預計算指定時間範圍內的所有衛星位置

        Args:
            time_interval_seconds: 時間間隔 (秒)

        Returns:
            預計算結果列表
        """
        self.logger.info(
            "開始歷史數據預計算",
            time_interval_seconds=time_interval_seconds,
            satellite_count=len(self.satellites),
        )

        results = []
        start_time = self.time_range[0]
        end_time = self.time_range[1]

        current_time = start_time
        processed_points = 0

        while current_time <= end_time:
            # 計算當前時間點所有可見衛星
            visible_satellites = self.compute_visible_satellites(current_time)
            results.extend(visible_satellites)

            processed_points += 1
            if processed_points % 100 == 0:
                progress = (
                    (current_time - start_time).total_seconds()
                    / (end_time - start_time).total_seconds()
                    * 100
                )
                self.logger.info(
                    f"預計算進度: {progress:.1f}%", processed_points=processed_points
                )

            current_time += timedelta(seconds=time_interval_seconds)

        self.logger.info(
            "歷史數據預計算完成",
            total_results=len(results),
            time_points=processed_points,
            visible_satellites=len(set(r.satellite_id for r in results)),
        )

        return results

    def compute_visible_satellites(self, timestamp: datetime) -> List[PrecomputeResult]:
        """
        計算指定時間所有可見衛星位置

        Args:
            timestamp: 計算時間點

        Returns:
            可見衛星的預計算結果列表
        """
        visible = []

        # 轉換為 Julian Day
        jd, fr = jday(
            timestamp.year,
            timestamp.month,
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second + timestamp.microsecond / 1e6,
        )

        for sat_data in self.satellites:
            try:
                # SGP4 軌道計算
                error_code, position_teme, velocity_teme = sat_data["satrec"].sgp4(
                    jd, fr
                )

                if error_code != 0:
                    continue  # 跳過計算失敗的衛星

                # 轉換 TEME 坐標到地理坐標
                sat_position = self._teme_to_geodetic(position_teme, timestamp)

                # 計算相對觀測者的位置
                elevation, azimuth, distance = self._calculate_look_angles(
                    sat_position, self.observer
                )

                # 可見性檢查 (仰角 >= -10 度以包含低軌衛星)
                if elevation >= -10.0:
                    # 計算信號品質
                    signal_quality = self._calculate_signal_quality(distance, elevation)

                    result = PrecomputeResult(
                        timestamp=timestamp,
                        satellite_id=sat_data["satellite_id"],
                        norad_id=sat_data["norad_id"],
                        satellite_name=sat_data["name"],
                        constellation=sat_data["constellation"],
                        observer_position=self.observer,
                        satellite_position={
                            "latitude": sat_position.latitude,
                            "longitude": sat_position.longitude,
                            "altitude": sat_position.altitude * 1000,  # 轉換為米
                            "elevation": elevation,
                            "azimuth": azimuth,
                            "range": distance,
                            "velocity": math.sqrt(
                                sum(v**2 for v in velocity_teme)
                            ),  # 速度大小
                        },
                        signal_quality=signal_quality,
                        calculation_method="SGP4",
                        data_quality=1.0,  # 真實 TLE 數據品質
                    )

                    visible.append(result)

            except Exception as e:
                self.logger.warning(
                    "衛星計算失敗", satellite_id=sat_data["satellite_id"], error=str(e)
                )
                continue

        return visible

    def _prepare_satellites(self) -> List[Dict]:
        """預處理 TLE 數據為 SGP4 衛星對象"""
        satellites = []

        for tle_item in self.tle_data:
            try:
                # 從 TLE 創建 SGP4 衛星對象
                satrec = Satrec.twoline2rv(tle_item["line1"], tle_item["line2"])

                # 提取衛星資訊
                satellite_info = {
                    "satellite_id": self._generate_satellite_id(tle_item),
                    "norad_id": tle_item.get(
                        "norad_id", self._extract_norad_id(tle_item["line1"])
                    ),
                    "name": tle_item["name"],
                    "constellation": tle_item.get("constellation", "unknown"),
                    "satrec": satrec,
                    "epoch": tle_item.get("epoch", datetime.now(timezone.utc)),
                }

                satellites.append(satellite_info)

            except Exception as e:
                self.logger.warning(
                    "TLE 數據處理失敗",
                    tle_name=tle_item.get("name", "unknown"),
                    error=str(e),
                )
                continue

        self.logger.info(f"成功處理 {len(satellites)} 顆衛星的 TLE 數據")
        return satellites

    def _generate_satellite_id(self, tle_item: Dict) -> str:
        """生成標準化的衛星 ID"""
        constellation = tle_item.get("constellation", "sat").lower()
        norad_id = tle_item.get("norad_id", self._extract_norad_id(tle_item["line1"]))

        prefix_map = {"starlink": "sl", "oneweb": "ow", "gps": "gps", "galileo": "gal"}

        prefix = prefix_map.get(constellation, "sat")
        return f"{prefix}_{norad_id}"

    def _extract_norad_id(self, line1: str) -> int:
        """從 TLE 第一行提取 NORAD ID"""
        try:
            return int(line1[2:7])
        except (ValueError, IndexError):
            return 0

    def _teme_to_geodetic(
        self, position_teme: Tuple[float, float, float], timestamp: datetime
    ) -> Position:
        """
        將 TEME 坐標轉換為地理坐標

        Args:
            position_teme: TEME 坐標 (x, y, z) km
            timestamp: 時間戳

        Returns:
            地理坐標位置
        """
        x, y, z = position_teme

        # 地球半徑和扁率常數
        a = 6378.137  # 地球赤道半徑 (km)
        f = 1 / 298.257223563  # 扁率
        e2 = 2 * f - f * f  # 第一偏心率平方

        # 計算經度
        longitude = math.atan2(y, x)

        # 計算緯度和高度 (迭代方法)
        p = math.sqrt(x * x + y * y)
        latitude = math.atan2(z, p)

        for _ in range(5):  # 迭代收斂
            N = a / math.sqrt(1 - e2 * math.sin(latitude) ** 2)
            altitude = p / math.cos(latitude) - N
            latitude = math.atan2(z, p * (1 - e2 * N / (N + altitude)))

        return Position(
            x=x,
            y=y,
            z=z,
            latitude=math.degrees(latitude),
            longitude=math.degrees(longitude),
            altitude=altitude,
            timestamp=timestamp,
        )

    def _calculate_look_angles(
        self, sat_position: Position, observer: ObserverPosition
    ) -> Tuple[float, float, float]:
        """
        計算衛星相對觀測者的仰角、方位角和距離

        Args:
            sat_position: 衛星地理位置
            observer: 觀測者位置

        Returns:
            (仰角, 方位角, 距離) - 度, 度, km
        """
        # 緯度經度差值 (弧度)
        lat_diff = math.radians(sat_position.latitude - observer.latitude)
        lon_diff = math.radians(sat_position.longitude - observer.longitude)

        # 地心距離計算 (Haversine)
        a = (
            math.sin(lat_diff / 2) ** 2
            + math.cos(math.radians(observer.latitude))
            * math.cos(math.radians(sat_position.latitude))
            * math.sin(lon_diff / 2) ** 2
        )
        ground_distance = 2 * 6371.0 * math.asin(math.sqrt(a))  # km

        # 高度差
        altitude_diff = sat_position.altitude - (
            observer.altitude / 1000.0
        )  # 轉換為 km

        # 空間距離
        space_distance = math.sqrt(ground_distance**2 + altitude_diff**2)

        # 仰角計算
        if ground_distance > 0:
            elevation = math.degrees(math.atan(altitude_diff / ground_distance))
        else:
            elevation = 90.0 if altitude_diff > 0 else -90.0

        # 方位角計算
        observer_lat_rad = math.radians(observer.latitude)
        sat_lat_rad = math.radians(sat_position.latitude)

        y = math.sin(lon_diff) * math.cos(sat_lat_rad)
        x = math.cos(observer_lat_rad) * math.sin(sat_lat_rad) - math.sin(
            observer_lat_rad
        ) * math.cos(sat_lat_rad) * math.cos(lon_diff)

        azimuth = math.degrees(math.atan2(y, x))
        azimuth = (azimuth + 360) % 360  # 轉換為 0-360 度

        return elevation, azimuth, space_distance

    def _calculate_signal_quality(
        self, distance: float, elevation: float
    ) -> Dict[str, float]:
        """
        計算信號品質指標

        Args:
            distance: 距離 (km)
            elevation: 仰角 (度)

        Returns:
            信號品質字典
        """
        # 自由空間路徑損耗 (28 GHz Ka 頻段)
        frequency_ghz = 28.0
        path_loss_db = 92.4 + 20 * math.log10(distance) + 20 * math.log10(frequency_ghz)

        # 大氣衰減 (簡化模型)
        if elevation > 0:
            # 仰角越低，大氣衰減越大
            atmospheric_loss = max(0, 5 * (1 - math.sin(math.radians(elevation))))
        else:
            atmospheric_loss = 10.0  # 負仰角有更大衰減

        total_path_loss = path_loss_db + atmospheric_loss

        # 信號強度估算 (假設衛星 EIRP = 50 dBW)
        eirp_dbw = 50.0
        signal_strength = eirp_dbw - total_path_loss

        # SINR 估算 (簡化)
        noise_floor = -110.0  # dBm
        sinr = signal_strength - noise_floor

        return {
            "signal_strength": round(signal_strength, 2),
            "path_loss_db": round(total_path_loss, 2),
            "atmospheric_loss": round(atmospheric_loss, 2),
            "sinr": round(sinr, 2),
            "link_margin": round(
                max(0, signal_strength + 90), 2
            ),  # 假設接收靈敏度 -90 dBm
        }

    def load_tle_data(self, tle_file_path: str) -> List[Dict]:
        """
        載入 TLE 數據文件 (向後兼容方法)

        Args:
            tle_file_path: TLE 文件路徑

        Returns:
            TLE 數據列表
        """
        self.logger.warning("使用已棄用的 load_tle_data 方法，建議使用 TLEDataManager")

        tle_data = []
        try:
            with open(tle_file_path, "r") as f:
                lines = f.readlines()

            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()

                    norad_id = int(line1[2:7])

                    tle_data.append(
                        {
                            "name": name,
                            "line1": line1,
                            "line2": line2,
                            "norad_id": norad_id,
                            "constellation": "unknown",
                        }
                    )

        except Exception as e:
            self.logger.error(f"TLE 文件載入失敗: {e}")

        return tle_data
