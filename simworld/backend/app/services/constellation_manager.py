"""
衛星星座管理系統 - 多衛星星座配置和管理

功能：
1. 多星座同時管理（Starlink, OneWeb, GPS等）
2. 衛星可見性計算和篩選
3. 最佳衛星選擇算法
4. 星座覆蓋分析

符合 d2.md 中 Phase 3 的要求
"""

import asyncio
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor


# TLE 數據現在由 NetStack 統一管理，移除本地 TLE 服務依賴
@dataclass
class TLEData:
    """簡化的 TLE 數據類型（用於向後兼容）"""

    name: str
    line1: str
    line2: str
    epoch: Optional[str] = None


from .sgp4_calculator import SGP4Calculator, OrbitPosition
from .distance_calculator import DistanceCalculator, Position

logger = logging.getLogger(__name__)


@dataclass
class SatelliteInfo:
    """衛星信息結構"""

    tle_data: TLEData
    current_position: Optional[OrbitPosition] = None
    elevation_angle: float = 0.0
    azimuth_angle: float = 0.0
    distance: float = 0.0
    is_visible: bool = False
    signal_strength: float = 0.0
    constellation: str = ""


@dataclass
class ConstellationConfig:
    """星座配置"""

    name: str
    min_elevation: float = 10.0  # 最小仰角（度）
    max_satellites: int = 50  # 最大同時跟蹤衛星數
    priority: int = 1  # 優先級（1最高）
    frequency_band: str = "Ku"  # 頻段
    enabled: bool = True


@dataclass
class CoverageAnalysis:
    """覆蓋分析結果"""

    total_satellites: int
    visible_satellites: int
    best_satellite: Optional[SatelliteInfo]
    coverage_percentage: float
    average_elevation: float
    constellation_distribution: Dict[str, int]


class ConstellationManager:
    """衛星星座管理器"""

    def __init__(self):
        # TLE 數據現在由 NetStack 統一管理，移除本地 TLE 服務
        # self.tle_service = TLEDataService()  # 已移除
        self.sgp4_calculator = SGP4Calculator()
        self.distance_calculator = DistanceCalculator()

        # 預定義星座配置
        self.constellation_configs = {
            "starlink": ConstellationConfig(
                name="Starlink",
                min_elevation=25.0,  # Starlink 建議最小仰角
                max_satellites=10,
                priority=1,
                frequency_band="Ku/Ka",
                enabled=True,
            ),
            "oneweb": ConstellationConfig(
                name="OneWeb",
                min_elevation=20.0,
                max_satellites=8,
                priority=2,
                frequency_band="Ku",
                enabled=True,
            ),
            "gps": ConstellationConfig(
                name="GPS",
                min_elevation=15.0,
                max_satellites=12,
                priority=3,
                frequency_band="L",
                enabled=True,
            ),
        }

        # 緩存
        self._satellite_cache: Dict[str, List[SatelliteInfo]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)  # 緩存5分鐘

        # 初始化標記
        self._initialized = False

    async def get_visible_satellites(
        self,
        observer_position: Position,
        timestamp: Optional[datetime] = None,
        constellations: Optional[List[str]] = None,
    ) -> List[SatelliteInfo]:
        """
        獲取指定位置可見的衛星

        Args:
            observer_position: 觀測者位置
            timestamp: 觀測時間（默認當前時間）
            constellations: 指定星座列表（默認所有啟用的星座）

        Returns:
            可見衛星列表
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        if constellations is None:
            constellations = [
                name
                for name, config in self.constellation_configs.items()
                if config.enabled
            ]

        try:
            # 檢查緩存
            if self._is_cache_valid():
                logger.debug("使用緩存的衛星數據")
                cached_satellites = []
                for constellation in constellations:
                    if constellation in self._satellite_cache:
                        cached_satellites.extend(self._satellite_cache[constellation])
            else:
                # 重新計算
                logger.info(f"計算可見衛星: {constellations}")
                cached_satellites = await self._calculate_satellite_positions(
                    constellations, timestamp
                )

            # 篩選可見衛星
            visible_satellites = []
            for sat_info in cached_satellites:
                if sat_info.constellation not in constellations:
                    continue

                config = self.constellation_configs.get(sat_info.constellation)
                if not config or not config.enabled:
                    continue

                # 計算相對於觀測者的角度和距離
                if sat_info.current_position:
                    elevation = self.distance_calculator.calculate_elevation_angle(
                        observer_position, sat_info.current_position
                    )
                    azimuth = self.distance_calculator.calculate_azimuth_angle(
                        observer_position, sat_info.current_position
                    )

                    # 計算距離
                    distance_result = self.distance_calculator.calculate_d2_distances(
                        observer_position, sat_info.current_position, observer_position
                    )

                    # 更新衛星信息
                    sat_info.elevation_angle = elevation
                    sat_info.azimuth_angle = azimuth
                    sat_info.distance = (
                        distance_result.satellite_distance / 1000
                    )  # 轉換為 km
                    sat_info.is_visible = elevation >= config.min_elevation
                    sat_info.signal_strength = self._calculate_signal_strength(
                        elevation, sat_info.distance
                    )

                    if sat_info.is_visible:
                        visible_satellites.append(sat_info)

            # 按優先級和信號強度排序
            visible_satellites.sort(
                key=lambda x: (
                    -self.constellation_configs[x.constellation].priority,
                    -x.signal_strength,
                    x.distance,
                )
            )

            # 限制每個星座的衛星數量
            filtered_satellites = []
            constellation_counts = {}

            for sat_info in visible_satellites:
                constellation = sat_info.constellation
                config = self.constellation_configs[constellation]

                if constellation_counts.get(constellation, 0) < config.max_satellites:
                    filtered_satellites.append(sat_info)
                    constellation_counts[constellation] = (
                        constellation_counts.get(constellation, 0) + 1
                    )

            logger.info(f"找到 {len(filtered_satellites)} 顆可見衛星")
            return filtered_satellites

        except Exception as e:
            logger.error(f"獲取可見衛星失敗: {e}")
            return []

    async def get_best_satellite(
        self,
        observer_position: Position,
        timestamp: Optional[datetime] = None,
        constellation: Optional[str] = None,
    ) -> Optional[SatelliteInfo]:
        """
        獲取最佳衛星（信號最強、仰角最高）

        Args:
            observer_position: 觀測者位置
            timestamp: 觀測時間
            constellation: 指定星座（可選）

        Returns:
            最佳衛星信息
        """
        constellations = [constellation] if constellation else None
        visible_satellites = await self.get_visible_satellites(
            observer_position, timestamp, constellations
        )

        if not visible_satellites:
            return None

        # 選擇信號最強的衛星
        best_satellite = max(visible_satellites, key=lambda x: x.signal_strength)

        logger.info(
            f"最佳衛星: {best_satellite.tle_data.satellite_name} "
            f"(仰角: {best_satellite.elevation_angle:.1f}°, "
            f"信號強度: {best_satellite.signal_strength:.2f})"
        )

        return best_satellite

    async def analyze_coverage(
        self,
        observer_position: Position,
        timestamp: Optional[datetime] = None,
        analysis_duration_minutes: int = 60,
    ) -> CoverageAnalysis:
        """
        分析指定時間段的星座覆蓋情況

        Args:
            observer_position: 觀測者位置
            timestamp: 開始時間
            analysis_duration_minutes: 分析時長（分鐘）

        Returns:
            覆蓋分析結果
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        try:
            logger.info(f"開始覆蓋分析: {analysis_duration_minutes} 分鐘")

            # 獲取當前可見衛星
            visible_satellites = await self.get_visible_satellites(
                observer_position, timestamp
            )

            if not visible_satellites:
                return CoverageAnalysis(
                    total_satellites=0,
                    visible_satellites=0,
                    best_satellite=None,
                    coverage_percentage=0.0,
                    average_elevation=0.0,
                    constellation_distribution={},
                )

            # 統計星座分布
            constellation_distribution = {}
            total_elevation = 0.0

            for sat_info in visible_satellites:
                constellation = sat_info.constellation
                constellation_distribution[constellation] = (
                    constellation_distribution.get(constellation, 0) + 1
                )
                total_elevation += sat_info.elevation_angle

            # 計算平均仰角
            average_elevation = (
                total_elevation / len(visible_satellites) if visible_satellites else 0.0
            )

            # 獲取最佳衛星
            best_satellite = max(visible_satellites, key=lambda x: x.signal_strength)

            # 計算覆蓋百分比（基於可見衛星數量和配置的最大值）
            total_max_satellites = sum(
                config.max_satellites
                for config in self.constellation_configs.values()
                if config.enabled
            )
            coverage_percentage = (
                (len(visible_satellites) / total_max_satellites) * 100
                if total_max_satellites > 0
                else 0.0
            )

            analysis_result = CoverageAnalysis(
                total_satellites=len(visible_satellites),
                visible_satellites=len(visible_satellites),
                best_satellite=best_satellite,
                coverage_percentage=min(coverage_percentage, 100.0),
                average_elevation=average_elevation,
                constellation_distribution=constellation_distribution,
            )

            logger.info(
                f"覆蓋分析完成: {len(visible_satellites)} 顆可見衛星, "
                f"覆蓋率: {coverage_percentage:.1f}%"
            )

            return analysis_result

        except Exception as e:
            logger.error(f"覆蓋分析失敗: {e}")
            return CoverageAnalysis(
                total_satellites=0,
                visible_satellites=0,
                best_satellite=None,
                coverage_percentage=0.0,
                average_elevation=0.0,
                constellation_distribution={},
            )

    async def predict_satellite_passes(
        self,
        observer_position: Position,
        satellite_id: str,
        start_time: datetime,
        duration_hours: int = 24,
    ) -> List[Dict]:
        """
        預測衛星過境時間

        Args:
            observer_position: 觀測者位置
            satellite_id: 衛星 NORAD ID
            start_time: 開始時間
            duration_hours: 預測時長（小時）

        Returns:
            過境預測列表
        """
        try:
            # 獲取衛星 TLE 數據
            satellite_tle = None
            for constellation in self.constellation_configs.keys():
                tle_data = await self.tle_service.fetch_tle_from_source(constellation)
                for tle in tle_data:
                    if str(tle.catalog_number) == str(satellite_id):
                        satellite_tle = tle
                        break
                if satellite_tle:
                    break

            if not satellite_tle:
                logger.warning(f"未找到衛星 {satellite_id} 的 TLE 數據")
                return []

            passes = []
            current_time = start_time
            end_time = start_time + timedelta(hours=duration_hours)
            step_minutes = 1  # 1分鐘步長

            in_pass = False
            pass_start = None
            max_elevation = 0.0
            max_elevation_time = None

            while current_time <= end_time:
                # 計算衛星位置
                sat_position = self.sgp4_calculator.propagate_orbit(
                    satellite_tle, current_time
                )

                if sat_position:
                    elevation = self.distance_calculator.calculate_elevation_angle(
                        observer_position, sat_position
                    )

                    if elevation > 0:  # 衛星在地平線以上
                        if not in_pass:
                            # 過境開始
                            in_pass = True
                            pass_start = current_time
                            max_elevation = elevation
                            max_elevation_time = current_time
                        else:
                            # 更新最大仰角
                            if elevation > max_elevation:
                                max_elevation = elevation
                                max_elevation_time = current_time
                    else:
                        if in_pass:
                            # 過境結束
                            in_pass = False
                            if (
                                pass_start and max_elevation > 10
                            ):  # 只記錄仰角大於10度的過境
                                azimuth = (
                                    self.distance_calculator.calculate_azimuth_angle(
                                        observer_position, sat_position
                                    )
                                )

                                passes.append(
                                    {
                                        "start_time": pass_start.isoformat(),
                                        "end_time": current_time.isoformat(),
                                        "max_elevation_time": max_elevation_time.isoformat(),
                                        "max_elevation": max_elevation,
                                        "azimuth": azimuth,
                                        "duration_minutes": (
                                            current_time - pass_start
                                        ).total_seconds()
                                        / 60,
                                    }
                                )

                current_time += timedelta(minutes=step_minutes)

            logger.info(f"預測到 {len(passes)} 次衛星過境")
            return passes

        except Exception as e:
            logger.error(f"衛星過境預測失敗: {e}")
            return []

    async def _calculate_satellite_positions(
        self, constellations: List[str], timestamp: datetime
    ) -> List[SatelliteInfo]:
        """計算所有衛星的當前位置"""
        all_satellites = []

        # 並行獲取多個星座的 TLE 數據
        tasks = []
        for constellation in constellations:
            if constellation in self.constellation_configs:
                task = self.tle_service.fetch_tle_from_source(constellation)
                tasks.append((constellation, task))

        # 等待所有 TLE 數據獲取完成
        for constellation, task in tasks:
            try:
                tle_data_list = await task

                # 並行計算衛星位置
                with ThreadPoolExecutor(max_workers=10) as executor:
                    position_tasks = []
                    for tle_data in tle_data_list:
                        future = executor.submit(
                            self.sgp4_calculator.propagate_orbit, tle_data, timestamp
                        )
                        position_tasks.append((tle_data, future))

                    # 收集結果
                    for tle_data, future in position_tasks:
                        try:
                            position = future.result(timeout=1.0)  # 1秒超時
                            if position:
                                sat_info = SatelliteInfo(
                                    tle_data=tle_data,
                                    current_position=position,
                                    constellation=constellation,
                                )
                                all_satellites.append(sat_info)
                        except Exception as e:
                            logger.debug(
                                f"衛星位置計算失敗: {tle_data.satellite_name}, {e}"
                            )

                logger.info(
                    f"{constellation} 星座: 計算了 {len([s for s in all_satellites if s.constellation == constellation])} 顆衛星位置"
                )

            except Exception as e:
                logger.error(f"獲取 {constellation} 星座數據失敗: {e}")

        # 更新緩存
        self._satellite_cache = {}
        for sat_info in all_satellites:
            if sat_info.constellation not in self._satellite_cache:
                self._satellite_cache[sat_info.constellation] = []
            self._satellite_cache[sat_info.constellation].append(sat_info)

        self._cache_timestamp = timestamp

        return all_satellites

    def _calculate_signal_strength(
        self, elevation_angle: float, distance_km: float
    ) -> float:
        """
        計算信號強度（簡化模型）

        Args:
            elevation_angle: 仰角（度）
            distance_km: 距離（公里）

        Returns:
            信號強度（0-1）
        """
        if elevation_angle <= 0:
            return 0.0

        # 基於仰角的信號強度（仰角越高信號越強）
        elevation_factor = min(elevation_angle / 90.0, 1.0)

        # 基於距離的信號衰減（自由空間路徑損耗）
        # 假設參考距離為 500km
        reference_distance = 500.0
        distance_factor = (
            reference_distance / max(distance_km, reference_distance)
        ) ** 2

        # 大氣衰減因子（仰角低時大氣衰減更嚴重）
        atmospheric_factor = 1.0 - (1.0 - elevation_factor) * 0.3

        # 綜合信號強度
        signal_strength = elevation_factor * distance_factor * atmospheric_factor

        return min(signal_strength, 1.0)

    def _is_cache_valid(self) -> bool:
        """檢查緩存是否有效"""
        if self._cache_timestamp is None:
            return False

        now = datetime.now(timezone.utc)
        return (now - self._cache_timestamp) < self._cache_duration

    def update_constellation_config(
        self, constellation: str, config: ConstellationConfig
    ) -> bool:
        """更新星座配置"""
        try:
            self.constellation_configs[constellation] = config
            logger.info(f"更新星座配置: {constellation}")

            # 清除緩存以強制重新計算
            self._satellite_cache.clear()
            self._cache_timestamp = None

            return True
        except Exception as e:
            logger.error(f"更新星座配置失敗: {e}")
            return False

    def get_constellation_configs(self) -> Dict[str, ConstellationConfig]:
        """獲取所有星座配置"""
        return self.constellation_configs.copy()

    async def get_constellation_statistics(self) -> Dict[str, Dict]:
        """獲取星座統計信息"""
        stats = {}

        for constellation_name, config in self.constellation_configs.items():
            if not config.enabled:
                continue

            try:
                # 獲取星座統計
                constellation_stats = await self.tle_service.get_constellation_stats(
                    constellation_name
                )

                stats[constellation_name] = {
                    "name": config.name,
                    "total_satellites": constellation_stats.get("totalSatellites", 0),
                    "valid_satellites": constellation_stats.get("validSatellites", 0),
                    "average_altitude": constellation_stats.get("averageAltitude", 0),
                    "inclination_range": constellation_stats.get(
                        "inclinationRange", {"min": 0, "max": 0}
                    ),
                    "last_updated": constellation_stats.get("lastUpdated"),
                    "config": {
                        "min_elevation": config.min_elevation,
                        "max_satellites": config.max_satellites,
                        "priority": config.priority,
                        "frequency_band": config.frequency_band,
                        "enabled": config.enabled,
                    },
                }
            except Exception as e:
                logger.error(f"獲取 {constellation_name} 統計信息失敗: {e}")
                stats[constellation_name] = {
                    "name": config.name,
                    "error": str(e),
                    "config": {
                        "min_elevation": config.min_elevation,
                        "max_satellites": config.max_satellites,
                        "priority": config.priority,
                        "frequency_band": config.frequency_band,
                        "enabled": config.enabled,
                    },
                }

        return stats

    async def simulate_handover_scenario(
        self,
        observer_position: Position,
        start_time: datetime,
        duration_minutes: int = 30,
    ) -> List[Dict]:
        """
        模擬衛星切換場景

        Args:
            observer_position: 觀測者位置
            start_time: 開始時間
            duration_minutes: 模擬時長（分鐘）

        Returns:
            切換事件列表
        """
        try:
            handover_events = []
            current_time = start_time
            end_time = start_time + timedelta(minutes=duration_minutes)
            step_seconds = 30  # 30秒步長

            current_best_satellite = None

            while current_time <= end_time:
                # 獲取當前最佳衛星
                best_satellite = await self.get_best_satellite(
                    observer_position, current_time
                )

                # 檢查是否需要切換
                if best_satellite and (
                    current_best_satellite is None
                    or best_satellite.tle_data.catalog_number
                    != current_best_satellite.tle_data.catalog_number
                ):
                    handover_event = {
                        "timestamp": current_time.isoformat(),
                        "event_type": (
                            "handover"
                            if current_best_satellite
                            else "initial_acquisition"
                        ),
                        "old_satellite": (
                            {
                                "name": current_best_satellite.tle_data.satellite_name,
                                "norad_id": current_best_satellite.tle_data.catalog_number,
                                "constellation": current_best_satellite.constellation,
                                "elevation": current_best_satellite.elevation_angle,
                                "signal_strength": current_best_satellite.signal_strength,
                            }
                            if current_best_satellite
                            else None
                        ),
                        "new_satellite": {
                            "name": best_satellite.tle_data.satellite_name,
                            "norad_id": best_satellite.tle_data.catalog_number,
                            "constellation": best_satellite.constellation,
                            "elevation": best_satellite.elevation_angle,
                            "signal_strength": best_satellite.signal_strength,
                        },
                        "reason": self._determine_handover_reason(
                            current_best_satellite, best_satellite
                        ),
                    }

                    handover_events.append(handover_event)
                    current_best_satellite = best_satellite

                    logger.info(
                        f"衛星切換: {handover_event['event_type']} at {current_time}"
                    )

                current_time += timedelta(seconds=step_seconds)

            logger.info(f"模擬完成: {len(handover_events)} 次切換事件")
            return handover_events

        except Exception as e:
            logger.error(f"切換場景模擬失敗: {e}")
            return []

    def _determine_handover_reason(
        self, old_satellite: Optional[SatelliteInfo], new_satellite: SatelliteInfo
    ) -> str:
        """確定切換原因"""
        if old_satellite is None:
            return "initial_acquisition"

        if old_satellite.elevation_angle < 10:
            return "low_elevation"

        if new_satellite.signal_strength > old_satellite.signal_strength * 1.2:
            return "better_signal"

        if new_satellite.constellation != old_satellite.constellation:
            priority_old = self.constellation_configs[
                old_satellite.constellation
            ].priority
            priority_new = self.constellation_configs[
                new_satellite.constellation
            ].priority
            if priority_new < priority_old:
                return "higher_priority_constellation"

        return "optimization"

    async def get_optimal_handover_targets(
        self,
        observer_position: Position,
        current_satellite: Optional[SatelliteInfo],
        timestamp: Optional[datetime] = None,
        prediction_window_minutes: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        獲取最佳切換目標衛星

        Args:
            observer_position: 觀測者位置
            current_satellite: 當前衛星
            timestamp: 時間戳
            prediction_window_minutes: 預測窗口（分鐘）

        Returns:
            排序後的切換目標列表
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        try:
            # 獲取所有可見衛星
            visible_satellites = await self.get_visible_satellites(
                observer_position, timestamp
            )

            if not visible_satellites:
                return []

            # 排除當前衛星
            if current_satellite:
                visible_satellites = [
                    sat
                    for sat in visible_satellites
                    if sat.tle_data.catalog_number
                    != current_satellite.tle_data.catalog_number
                ]

            # 計算每個衛星的切換評分
            handover_candidates = []

            for satellite in visible_satellites:
                score = await self._calculate_handover_score(
                    observer_position,
                    satellite,
                    current_satellite,
                    timestamp,
                    prediction_window_minutes,
                )

                # 預測未來軌跡
                future_trajectory = await self._predict_satellite_trajectory(
                    satellite, timestamp, prediction_window_minutes
                )

                # 計算切換時機
                optimal_handover_time = self._calculate_optimal_handover_time(
                    observer_position,
                    current_satellite,
                    satellite,
                    timestamp,
                    prediction_window_minutes,
                )

                candidate = {
                    "satellite_info": satellite,
                    "handover_score": score,
                    "predicted_trajectory": future_trajectory,
                    "optimal_handover_time": optimal_handover_time,
                    "handover_reason": self._determine_handover_reason(
                        current_satellite, satellite
                    ),
                    "quality_metrics": {
                        "elevation_stability": self._calculate_elevation_stability(
                            future_trajectory
                        ),
                        "signal_quality": satellite.signal_strength,
                        "geometric_diversity": (
                            self._calculate_geometric_diversity(
                                current_satellite, satellite
                            )
                            if current_satellite
                            else 1.0
                        ),
                        "constellation_priority": self.constellation_configs[
                            satellite.constellation
                        ].priority,
                    },
                }

                handover_candidates.append(candidate)

            # 按切換評分排序
            handover_candidates.sort(key=lambda x: x["handover_score"], reverse=True)

            logger.info(f"找到 {len(handover_candidates)} 個切換候選目標")
            return handover_candidates[:10]  # 返回前10個最佳目標

        except Exception as e:
            logger.error(f"獲取最佳切換目標失敗: {e}")
            return []

    async def _calculate_handover_score(
        self,
        observer_position: Position,
        candidate_satellite: SatelliteInfo,
        current_satellite: Optional[SatelliteInfo],
        timestamp: datetime,
        prediction_window_minutes: int,
    ) -> float:
        """
        計算衛星切換評分

        評分因子：
        1. 信號強度 (30%)
        2. 仰角穩定性 (25%)
        3. 幾何多樣性 (20%)
        4. 星座優先級 (15%)
        5. 切換成本 (10%)
        """
        try:
            # 1. 信號強度評分 (0-1)
            signal_score = candidate_satellite.signal_strength

            # 2. 仰角穩定性評分
            future_positions = []
            current_time = timestamp
            for i in range(prediction_window_minutes):
                future_time = current_time + timedelta(minutes=i)
                future_pos = self.sgp4_calculator.propagate_orbit(
                    candidate_satellite.tle_data, future_time
                )
                if future_pos:
                    elevation = self.distance_calculator.calculate_elevation_angle(
                        observer_position, future_pos
                    )
                    future_positions.append(elevation)

            if future_positions:
                elevation_variance = sum(
                    (e - sum(future_positions) / len(future_positions)) ** 2
                    for e in future_positions
                ) / len(future_positions)
                elevation_stability_score = max(
                    0, 1 - elevation_variance / 100
                )  # 歸一化
            else:
                elevation_stability_score = 0

            # 3. 幾何多樣性評分
            if current_satellite:
                geometric_diversity_score = self._calculate_geometric_diversity(
                    current_satellite, candidate_satellite
                )
            else:
                geometric_diversity_score = 1.0

            # 4. 星座優先級評分
            constellation_config = self.constellation_configs[
                candidate_satellite.constellation
            ]
            priority_score = 1.0 / constellation_config.priority  # 優先級越高分數越高

            # 5. 切換成本評分（基於角度差異）
            if current_satellite:
                angle_diff = abs(
                    candidate_satellite.elevation_angle
                    - current_satellite.elevation_angle
                )
                handover_cost_score = max(
                    0, 1 - angle_diff / 90
                )  # 角度差異越小成本越低
            else:
                handover_cost_score = 1.0

            # 加權總分
            total_score = (
                signal_score * 0.30
                + elevation_stability_score * 0.25
                + geometric_diversity_score * 0.20
                + priority_score * 0.15
                + handover_cost_score * 0.10
            )

            return min(total_score, 1.0)

        except Exception as e:
            logger.error(f"計算切換評分失敗: {e}")
            return 0.0

    async def _predict_satellite_trajectory(
        self, satellite: SatelliteInfo, start_time: datetime, duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """預測衛星軌跡"""
        try:
            trajectory = []
            current_time = start_time

            for i in range(0, duration_minutes, 2):  # 每2分鐘一個點
                future_time = current_time + timedelta(minutes=i)
                future_pos = self.sgp4_calculator.propagate_orbit(
                    satellite.tle_data, future_time
                )

                if future_pos:
                    trajectory.append(
                        {
                            "timestamp": future_time.isoformat(),
                            "latitude": future_pos.latitude,
                            "longitude": future_pos.longitude,
                            "altitude": future_pos.altitude,
                        }
                    )

            return trajectory
        except Exception as e:
            logger.error(f"預測衛星軌跡失敗: {e}")
            return []

    def _calculate_optimal_handover_time(
        self,
        observer_position: Position,
        current_satellite: Optional[SatelliteInfo],
        candidate_satellite: SatelliteInfo,
        start_time: datetime,
        window_minutes: int,
    ) -> Optional[str]:
        """計算最佳切換時機"""
        try:
            if not current_satellite:
                return start_time.isoformat()

            best_time = start_time
            best_score = 0

            # 在預測窗口內尋找最佳切換時機
            for i in range(window_minutes):
                test_time = start_time + timedelta(minutes=i)

                # 計算當前衛星在該時間的信號強度
                current_pos = self.sgp4_calculator.propagate_orbit(
                    current_satellite.tle_data, test_time
                )
                candidate_pos = self.sgp4_calculator.propagate_orbit(
                    candidate_satellite.tle_data, test_time
                )

                if current_pos and candidate_pos:
                    current_elevation = (
                        self.distance_calculator.calculate_elevation_angle(
                            observer_position, current_pos
                        )
                    )
                    candidate_elevation = (
                        self.distance_calculator.calculate_elevation_angle(
                            observer_position, candidate_pos
                        )
                    )

                    # 切換評分：候選衛星信號強度 - 當前衛星信號強度
                    current_signal = self._calculate_signal_strength(
                        current_elevation, current_pos.altitude
                    )
                    candidate_signal = self._calculate_signal_strength(
                        candidate_elevation, candidate_pos.altitude
                    )

                    score = candidate_signal - current_signal

                    if score > best_score:
                        best_score = score
                        best_time = test_time

            return best_time.isoformat()
        except Exception as e:
            logger.error(f"計算最佳切換時機失敗: {e}")
            return start_time.isoformat()

    def _calculate_elevation_stability(self, trajectory: List[Dict[str, Any]]) -> float:
        """計算仰角穩定性"""
        if len(trajectory) < 2:
            return 0.0

        try:
            # 這裡需要重新計算仰角，因為軌跡只包含位置信息
            # 簡化處理：基於高度變化評估穩定性
            altitudes = [point["altitude"] for point in trajectory]
            altitude_variance = sum(
                (alt - sum(altitudes) / len(altitudes)) ** 2 for alt in altitudes
            ) / len(altitudes)

            # 高度變化越小，穩定性越高
            stability = max(0, 1 - altitude_variance / 10000)  # 歸一化
            return stability
        except Exception as e:
            logger.error(f"計算仰角穩定性失敗: {e}")
            return 0.0

    def _calculate_geometric_diversity(
        self, satellite1: SatelliteInfo, satellite2: SatelliteInfo
    ) -> float:
        """計算幾何多樣性"""
        try:
            # 基於方位角和仰角差異計算多樣性
            azimuth_diff = abs(satellite1.azimuth_angle - satellite2.azimuth_angle)
            elevation_diff = abs(
                satellite1.elevation_angle - satellite2.elevation_angle
            )

            # 歸一化到 0-1 範圍
            azimuth_diversity = min(azimuth_diff / 180, 1.0)
            elevation_diversity = min(elevation_diff / 90, 1.0)

            # 綜合多樣性評分
            diversity = (azimuth_diversity + elevation_diversity) / 2
            return diversity
        except Exception as e:
            logger.error(f"計算幾何多樣性失敗: {e}")
            return 0.0
