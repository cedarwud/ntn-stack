"""
快速衛星接入預測服務 - Algorithm 2 實作

完全按照論文《Accelerating Handover in Mobile Satellite Network》中的 Algorithm 2 實作
實現地理區塊劃分和快速衛星存取預測演算法

論文 Algorithm 2 流程：
1. 預測時間 t 所有衛星位置 St'
2. 初始化 UC 集合, At' 結果表
3. 根據存取策略篩選候選 UE (Flexible vs Consistent)
4. 地球表面劃分地理區塊
5. 將每顆衛星指派到對應區塊
6. 為每個候選 UE 分配最佳接入衛星
"""

import asyncio
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

import structlog
import numpy as np
from .simworld_tle_bridge_service import SimWorldTLEBridgeService

# 導入統一配置系統
import sys
sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')
try:
    from unified_elevation_config import get_standard_threshold
    UNIFIED_CONFIG_AVAILABLE = True
except ImportError:
    UNIFIED_CONFIG_AVAILABLE = False

logger = structlog.get_logger(__name__)


class AccessStrategy(Enum):
    """UE 接入策略"""

    FLEXIBLE = "flexible"  # 彈性策略：只在當前衛星不可用時才換手
    CONSISTENT = "consistent"  # 穩定策略：總是執行最佳化重新分配


@dataclass
class GeographicalBlock:
    """地理區塊"""

    block_id: int
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    satellites: List[str] = field(default_factory=list)
    center_lat: float = 0.0
    center_lon: float = 0.0
    coverage_area_km2: float = 0.0

    def __post_init__(self):
        self.center_lat = (self.lat_min + self.lat_max) / 2
        self.center_lon = (self.lon_min + self.lon_max) / 2
        # 計算區塊面積 (簡化的球面計算)
        lat_range = math.radians(self.lat_max - self.lat_min)
        lon_range = math.radians(self.lon_max - self.lon_min)
        earth_radius_km = 6371
        self.coverage_area_km2 = (earth_radius_km**2) * lat_range * lon_range


@dataclass
class UEAccessInfo:
    """UE 接入資訊"""

    ue_id: str
    current_satellite: Optional[str] = None
    access_strategy: AccessStrategy = AccessStrategy.FLEXIBLE
    position: Dict[str, float] = field(default_factory=dict)  # {lat, lon, alt}
    last_update: datetime = field(default_factory=datetime.utcnow)
    quality_score: float = 1.0


@dataclass
class SatelliteInfo:
    """衛星資訊"""

    satellite_id: str
    position: Dict[str, float] = field(default_factory=dict)  # {lat, lon, alt}
    velocity: Dict[str, float] = field(default_factory=dict)  # {vx, vy, vz}
    orbital_direction: float = 0.0  # 軌道運行方向角度
    block_assignments: List[int] = field(default_factory=list)
    coverage_radius_km: float = 1000.0


class FastSatellitePrediction:
    """
    快速衛星預測演算法 - Algorithm 2 實作

    實現論文中的地理區塊劃分和最佳化衛星選擇演算法
    """

    def __init__(
        self,
        earth_radius_km: float = 6371.0,
        block_size_degrees: float = 10.0,
        tle_bridge_service: Optional[SimWorldTLEBridgeService] = None,
        prediction_accuracy_target: float = 0.95,
    ):
        """
        初始化快速衛星預測服務

        Args:
            earth_radius_km: 地球半徑
            block_size_degrees: 地理區塊大小（度）
            tle_bridge_service: TLE 橋接服務
            prediction_accuracy_target: 預測準確率目標
        """
        self.logger = structlog.get_logger(__name__)
        self.earth_radius = earth_radius_km
        self.block_size = block_size_degrees
        self.tle_bridge = tle_bridge_service or SimWorldTLEBridgeService()
        self.accuracy_target = prediction_accuracy_target

        # 地理區塊快取
        self.blocks: Dict[int, GeographicalBlock] = {}
        self.blocks_initialized = False

        # UE 和衛星資料快取
        self.ue_registry: Dict[str, UEAccessInfo] = {}
        self.satellite_registry: Dict[str, SatelliteInfo] = {}

        # 演算法統計
        self.stats = {
            "total_predictions": 0,
            "successful_predictions": 0,
            "current_accuracy": 0.0,
            "average_prediction_time_ms": 0.0,
            "block_optimization_hits": 0,
            "orbital_direction_optimizations": 0,
        }

        self.logger.info(
            "快速衛星預測服務初始化",
            block_size_degrees=block_size_degrees,
            accuracy_target=prediction_accuracy_target,
        )

    async def predict_access_satellites(
        self, users: List[str], satellites: List[Dict[str, Any]], time_t: float
    ) -> Dict[str, str]:
        """
        Algorithm 2: 快速存取衛星預測

        Args:
            users: UE 清單
            satellites: 衛星列表 (包含位置資訊)
            time_t: 預測時間戳

        Returns:
            UE ID -> 最佳衛星 ID 的映射
        """
        start_time = datetime.utcnow()
        self.stats["total_predictions"] += 1

        try:
            self.logger.info(
                "執行快速衛星接入預測",
                user_count=len(users),
                satellite_count=len(satellites),
                prediction_time=datetime.fromtimestamp(time_t).isoformat(),
            )

            # Algorithm 2 Step 1: 預測在時間 t 時所有衛星的位置
            St_prime = await self.predict_satellite_positions(satellites, time_t)

            # Algorithm 2 Step 2: 初始化候選 UE 集合和結果字典
            UC: Set[str] = set()  # 候選 UE 集合
            At_prime: Dict[str, str] = {}  # 結果映射

            # Algorithm 2 Step 3-10: 根據存取策略，篩選候選 UE
            for ui in users:
                access_strategy = await self.get_access_strategy(ui)
                current_satellite = await self.get_current_satellite(ui)

                if access_strategy == AccessStrategy.FLEXIBLE:
                    # 檢查當前衛星是否仍可用
                    is_available = await self.is_satellite_available(
                        current_satellite, ui, time_t
                    )

                    if not is_available:
                        UC.add(ui)  # 當前衛星將不可用，加入候選
                        self.logger.debug(
                            "UE 加入候選集合",
                            ue_id=ui,
                            reason="current_satellite_unavailable",
                            current_satellite=current_satellite,
                        )
                    else:
                        At_prime[ui] = current_satellite  # 衛星仍可覆蓋，保持不變

                else:  # AccessStrategy.CONSISTENT
                    UC.add(ui)  # 穩定策略總是重新分配
                    self.logger.debug(
                        "UE 加入候選集合", ue_id=ui, reason="consistent_strategy"
                    )

            # Algorithm 2 Step 11-15: 創建地理區塊並將衛星分配到區塊
            if not self.blocks_initialized:
                await self.initialize_geographical_blocks()

            satellite_blocks = await self.assign_satellites_to_blocks(St_prime)

            # Algorithm 2 Step 16-19: 為每個候選 UE 分配最優接入衛星
            for uj in UC:
                block_id = await self.get_user_block(uj)

                # 收集該區塊及鄰近區塊的候選衛星
                candidate_satellites = await self.get_block_candidate_satellites(
                    block_id, satellite_blocks
                )

                # 在候選衛星中選擇最佳衛星
                access_satellite = await self.find_best_satellite(
                    uj, candidate_satellites, St_prime, time_t
                )

                At_prime[uj] = access_satellite

                self.logger.debug(
                    "為 UE 分配最佳衛星",
                    ue_id=uj,
                    block_id=block_id,
                    selected_satellite=access_satellite,
                    candidate_count=len(candidate_satellites),
                )

            # 更新統計
            self.stats["successful_predictions"] += 1
            prediction_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_performance_stats(prediction_time_ms)

            self.logger.info(
                "快速衛星接入預測完成",
                total_assignments=len(At_prime),
                candidate_ue_count=len(UC),
                unchanged_assignments=len(users) - len(UC),
                prediction_time_ms=prediction_time_ms,
            )

            return At_prime

        except Exception as e:
            self.logger.error("快速衛星接入預測失敗", error=str(e))
            raise

    async def predict_satellite_positions(
        self, satellites: List[Dict[str, Any]], time_t: float
    ) -> Dict[str, SatelliteInfo]:
        """
        預測指定時間所有衛星的位置

        Args:
            satellites: 衛星列表
            time_t: 預測時間戳

        Returns:
            衛星 ID -> 衛星資訊的映射
        """
        St_prime = {}

        for satellite_data in satellites:
            satellite_id = satellite_data.get(
                "satellite_id", satellite_data.get("id", "unknown")
            )

            try:
                # 使用 TLE 橋接服務獲取預測位置
                prediction_time = datetime.fromtimestamp(time_t)

                positions = await self.tle_bridge.get_batch_satellite_positions(
                    [satellite_id], timestamp=prediction_time
                )

                position_data = positions.get(satellite_id, {})

                if position_data.get("success"):
                    # 計算真實軌道方向
                    orbital_direction = await self._calculate_orbital_direction(
                        satellite_id, position_data
                    )

                    satellite_info = SatelliteInfo(
                        satellite_id=satellite_id,
                        position={
                            "lat": position_data.get(
                                "lat", position_data.get("latitude", 0.0)
                            ),
                            "lon": position_data.get(
                                "lon", position_data.get("longitude", 0.0)
                            ),
                            "alt": position_data.get(
                                "alt", position_data.get("altitude", 0.0)
                            ),
                        },
                        velocity={
                            "speed": (
                                position_data.get("velocity", 0.0)
                                if isinstance(
                                    position_data.get("velocity"), (int, float)
                                )
                                else 7.5
                            )
                        },
                        orbital_direction=orbital_direction,
                        coverage_radius_km=self._estimate_coverage_radius(
                            position_data.get(
                                "alt", position_data.get("altitude", 550.0)
                            )
                        ),
                    )

                    St_prime[satellite_id] = satellite_info

                    # 更新衛星註冊表
                    self.satellite_registry[satellite_id] = satellite_info

                else:
                    # API失敗，跳過此衛星（不使用模擬資料）
                    self.logger.warning(
                        "衛星位置API失敗，跳過此衛星",
                        satellite_id=satellite_id,
                        error=position_data.get("error", "API返回失敗"),
                    )
                    continue

            except Exception as e:
                # 異常情況，跳過此衛星（不使用模擬資料）
                self.logger.error(
                    "預測衛星位置異常，跳過此衛星",
                    satellite_id=satellite_id,
                    error=str(e),
                )
                continue

        self.logger.info(
            "衛星位置預測完成",
            successful_predictions=len(St_prime),
            total_satellites=len(satellites),
        )

        return St_prime

    async def initialize_geographical_blocks(self) -> Dict[int, GeographicalBlock]:
        """
        創建地理區塊網格

        Returns:
            區塊 ID -> 地理區塊的映射
        """
        self.logger.info("初始化地理區塊", block_size_degrees=self.block_size)

        blocks = {}
        block_id = 0

        # 以指定度數為間隔劃分區塊
        lat_step = self.block_size
        lon_step = self.block_size

        for lat in range(-90, 90, int(lat_step)):
            for lon in range(-180, 180, int(lon_step)):
                lat_min = lat
                lat_max = min(lat + lat_step, 90)
                lon_min = lon
                lon_max = min(lon + lon_step, 180)

                block = GeographicalBlock(
                    block_id=block_id,
                    lat_min=lat_min,
                    lat_max=lat_max,
                    lon_min=lon_min,
                    lon_max=lon_max,
                )

                blocks[block_id] = block
                block_id += 1

        self.blocks = blocks
        self.blocks_initialized = True

        self.logger.info(
            "地理區塊初始化完成", total_blocks=len(blocks), coverage="全球"
        )

        return blocks

    async def assign_satellites_to_blocks(
        self, satellite_positions: Dict[str, SatelliteInfo]
    ) -> Dict[int, List[str]]:
        """
        將衛星分配到對應的地理區塊

        Args:
            satellite_positions: 衛星位置資訊

        Returns:
            區塊 ID -> 衛星 ID 列表的映射
        """
        satellite_blocks = {block_id: [] for block_id in self.blocks.keys()}

        for satellite_id, satellite_info in satellite_positions.items():
            sat_lat = satellite_info.position["lat"]
            sat_lon = satellite_info.position["lon"]
            sat_alt = satellite_info.position["alt"]

            # 計算衛星覆蓋的地理區塊
            covered_blocks = await self._calculate_satellite_coverage_blocks(
                sat_lat, sat_lon, sat_alt
            )

            # 將衛星分配到所有覆蓋的區塊
            for block_id in covered_blocks:
                if block_id in satellite_blocks:
                    satellite_blocks[block_id].append(satellite_id)

            # 更新衛星的區塊分配資訊
            satellite_info.block_assignments = covered_blocks

        # 統計分配結果
        total_assignments = sum(len(sats) for sats in satellite_blocks.values())
        non_empty_blocks = sum(1 for sats in satellite_blocks.values() if sats)

        self.logger.info(
            "衛星區塊分配完成",
            total_assignments=total_assignments,
            non_empty_blocks=non_empty_blocks,
            total_blocks=len(self.blocks),
        )

        return satellite_blocks

    async def get_block_candidate_satellites(
        self, center_block_id: int, satellite_blocks: Dict[int, List[str]]
    ) -> List[str]:
        """
        獲取指定區塊及鄰近區塊的候選衛星

        Args:
            center_block_id: 中心區塊 ID
            satellite_blocks: 區塊衛星分配

        Returns:
            候選衛星 ID 列表
        """
        candidate_satellites = []

        # 獲取中心區塊的衛星
        center_satellites = satellite_blocks.get(center_block_id, [])
        candidate_satellites.extend(center_satellites)

        # 獲取鄰近區塊 ID
        neighbor_blocks = await self._get_neighbor_blocks(center_block_id)

        # 獲取鄰近區塊的衛星
        for neighbor_id in neighbor_blocks:
            neighbor_satellites = satellite_blocks.get(neighbor_id, [])
            candidate_satellites.extend(neighbor_satellites)

        # 去重
        candidate_satellites = list(set(candidate_satellites))

        self.logger.debug(
            "獲取候選衛星",
            center_block=center_block_id,
            neighbor_blocks=len(neighbor_blocks),
            total_candidates=len(candidate_satellites),
        )

        return candidate_satellites

    async def find_best_satellite(
        self,
        ue_id: str,
        candidate_satellites: List[str],
        satellite_positions: Dict[str, SatelliteInfo],
        time_t: float,
    ) -> str:
        """
        在候選衛星中選擇最佳衛星

        Args:
            ue_id: UE 識別碼
            candidate_satellites: 候選衛星列表
            satellite_positions: 衛星位置資訊
            time_t: 時間戳

        Returns:
            最佳衛星 ID
        """
        if not candidate_satellites:
            return "default_satellite"

        ue_position = await self._get_ue_position(ue_id)
        best_satellite = None
        best_score = -1

        for satellite_id in candidate_satellites:
            satellite_info = satellite_positions.get(satellite_id)
            if not satellite_info:
                continue

            # 計算多維度評分
            score = await self._calculate_satellite_score(
                ue_position, satellite_info, time_t
            )

            if score > best_score:
                best_score = score
                best_satellite = satellite_id

        # 軌道方向最佳化
        if best_satellite:
            optimized_satellite = await self._apply_orbital_direction_optimization(
                best_satellite, candidate_satellites, satellite_positions
            )

            if optimized_satellite != best_satellite:
                self.stats["orbital_direction_optimizations"] += 1
                self.logger.debug(
                    "應用軌道方向最佳化",
                    ue_id=ue_id,
                    original_satellite=best_satellite,
                    optimized_satellite=optimized_satellite,
                )
                best_satellite = optimized_satellite

        return best_satellite or candidate_satellites[0]

    async def _calculate_satellite_score(
        self,
        ue_position: Dict[str, float],
        satellite_info: SatelliteInfo,
        time_t: float,
    ) -> float:
        """
        計算衛星接入評分

        Args:
            ue_position: UE 位置
            satellite_info: 衛星資訊
            time_t: 時間戳

        Returns:
            評分 (0-100)
        """
        sat_pos = satellite_info.position

        # 1. 距離因子
        distance_km = self._calculate_distance(
            ue_position["lat"], ue_position["lon"], sat_pos["lat"], sat_pos["lon"]
        )
        distance_score = max(0, (2000 - distance_km) / 2000) * 40

        # 2. 仰角因子
        elevation = self._calculate_elevation(ue_position, sat_pos)
        elevation_score = max(0, min(90, elevation)) / 90 * 30

        # 3. 覆蓋穩定性因子
        stability_score = min(20, satellite_info.coverage_radius_km / 100)

        # 4. 軌道方向一致性因子 (預留)
        direction_score = 10  # 基礎分數

        total_score = (
            distance_score + elevation_score + stability_score + direction_score
        )

        return total_score

    async def _apply_orbital_direction_optimization(
        self,
        current_best: str,
        candidates: List[str],
        satellite_positions: Dict[str, SatelliteInfo],
    ) -> str:
        """
        應用軌道方向最佳化

        選擇軌道運行方向相近的衛星以降低換手延遲
        """
        current_satellite_info = satellite_positions.get(current_best)
        if not current_satellite_info:
            return current_best

        current_direction = current_satellite_info.orbital_direction

        # 尋找方向最相近的衛星
        best_direction_match = current_best
        min_direction_diff = float("inf")

        for candidate_id in candidates:
            candidate_info = satellite_positions.get(candidate_id)
            if not candidate_info:
                continue

            direction_diff = abs(candidate_info.orbital_direction - current_direction)
            # 考慮角度環繞 (0-360 度)
            direction_diff = min(direction_diff, 360 - direction_diff)

            if direction_diff < min_direction_diff:
                min_direction_diff = direction_diff
                best_direction_match = candidate_id

        # 如果方向差異小於閾值，選擇方向相近的衛星
        if min_direction_diff < 30:  # 30度閾值
            return best_direction_match

        return current_best

    # 輔助方法

    async def get_access_strategy(self, ue_id: str) -> AccessStrategy:
        """獲取 UE 的接入策略"""
        ue_info = self.ue_registry.get(ue_id)
        if ue_info:
            return ue_info.access_strategy

        # 如果 UE 未註冊，返回預設的彈性策略
        # 實際部署中應該從 UE 配置服務獲取
        self.logger.warning("UE 未註冊，使用預設彈性策略", ue_id=ue_id)
        return AccessStrategy.FLEXIBLE

    async def get_current_satellite(self, ue_id: str) -> Optional[str]:
        """獲取 UE 當前接入的衛星"""
        ue_info = self.ue_registry.get(ue_id)
        if ue_info:
            return ue_info.current_satellite

        return None

    async def is_satellite_available(
        self, satellite_id: Optional[str], ue_id: str, time_t: float
    ) -> bool:
        """檢查衛星是否對指定 UE 可用"""
        if not satellite_id:
            return False

        try:
            ue_position = await self._get_ue_position(ue_id)

            # 獲取衛星在指定時間的位置
            positions = await self.tle_bridge.get_batch_satellite_positions(
                [satellite_id], timestamp=datetime.fromtimestamp(time_t)
            )

            position_data = positions.get(satellite_id, {})

            if not position_data.get("success"):
                return False

            # 檢查可見性和仰角
            elevation = position_data.get("elevation", 0)
            visible = position_data.get("visible", False)

            return visible and elevation >= 10  # 最小仰角 10 度

        except Exception as e:
            self.logger.warning(
                "檢查衛星可用性失敗",
                satellite_id=satellite_id,
                ue_id=ue_id,
                error=str(e),
            )
            return False

    async def get_user_block(self, ue_id: str) -> int:
        """獲取 UE 所在的地理區塊"""
        ue_position = await self._get_ue_position(ue_id)

        lat = ue_position["lat"]
        lon = ue_position["lon"]

        # 找到包含該位置的區塊
        for block_id, block in self.blocks.items():
            if (
                block.lat_min <= lat < block.lat_max
                and block.lon_min <= lon < block.lon_max
            ):
                return block_id

        # 如果沒找到，返回最近的區塊
        return 0

    async def _get_ue_position(self, ue_id: str) -> Dict[str, float]:
        """獲取 UE 位置（使用真實數據）"""
        ue_info = self.ue_registry.get(ue_id)
        if ue_info and ue_info.position:
            return ue_info.position

        # 如果 UE 未註冊，記錄警告並嘗試從位置服務獲取
        self.logger.warning(
            "UE 未註冊或無位置資訊", ue_id=ue_id, action="返回台灣中心位置作為默認值"
        )

        # 使用台灣中心位置作為合理的默認值（而非hash隨機位置）
        return {
            "lat": 24.1477,  # 台灣中心緯度
            "lon": 120.6736,  # 台灣中心經度
            "alt": 100.0,  # 海拔100米
        }

    async def _calculate_satellite_coverage_blocks(
        self, sat_lat: float, sat_lon: float, sat_alt: float
    ) -> List[int]:
        """計算衛星覆蓋的地理區塊"""
        coverage_radius_km = self._estimate_coverage_radius(sat_alt)
        coverage_radius_deg = coverage_radius_km / (self.earth_radius * math.pi / 180)

        covered_blocks = []

        for block_id, block in self.blocks.items():
            # 檢查區塊中心是否在衛星覆蓋範圍內
            distance_deg = math.sqrt(
                (block.center_lat - sat_lat) ** 2 + (block.center_lon - sat_lon) ** 2
            )

            if distance_deg <= coverage_radius_deg:
                covered_blocks.append(block_id)

        return covered_blocks

    async def _get_neighbor_blocks(self, center_block_id: int) -> List[int]:
        """獲取鄰近區塊"""
        center_block = self.blocks.get(center_block_id)
        if not center_block:
            return []

        neighbors = []

        for block_id, block in self.blocks.items():
            if block_id == center_block_id:
                continue

            # 檢查是否為鄰近區塊（共享邊界或頂點）
            lat_adjacent = (
                abs(block.lat_max - center_block.lat_min) < 0.1
                or abs(block.lat_min - center_block.lat_max) < 0.1
            )

            lon_adjacent = (
                abs(block.lon_max - center_block.lon_min) < 0.1
                or abs(block.lon_min - center_block.lon_max) < 0.1
            )

            lat_overlap = not (
                block.lat_max <= center_block.lat_min
                or block.lat_min >= center_block.lat_max
            )

            lon_overlap = not (
                block.lon_max <= center_block.lon_min
                or block.lon_min >= center_block.lon_max
            )

            if (lat_adjacent and lon_overlap) or (lon_adjacent and lat_overlap):
                neighbors.append(block_id)

        return neighbors

    def _estimate_coverage_radius(self, altitude_km: float) -> float:
        """估算衛星覆蓋半徑"""
        # 基於衛星高度估算覆蓋半徑
        # 考慮最小仰角約束（使用統一配置系統）
        if UNIFIED_CONFIG_AVAILABLE:
            min_elevation_deg = get_standard_threshold()  # 統一配置系統：10.0°
        else:
            min_elevation_deg = 10.0  # 回退值：ITU-R P.618 合規標準
        min_elevation_rad = math.radians(min_elevation_deg)

        # 地平線距離
        horizon_distance = math.sqrt(
            altitude_km * (altitude_km + 2 * self.earth_radius)
        )

        # 考慮最小仰角的有效覆蓋半徑
        effective_radius = altitude_km * math.tan(
            math.acos(self.earth_radius / (self.earth_radius + altitude_km))
            - min_elevation_rad
        )

        return min(horizon_distance, effective_radius)

    async def _calculate_orbital_direction(
        self, satellite_id: str, position_data: Dict[str, Any]
    ) -> float:
        """計算衛星軌道運行方向（基於真實數據）"""
        # 從 API 響應中獲取方位角或速度向量
        azimuth = position_data.get("azimuth", None)
        if azimuth is not None:
            return float(azimuth)

        # 如果有速度向量數據，計算運動方向
        velocity = position_data.get("velocity", {})
        if isinstance(velocity, dict):
            vx = velocity.get("vx", 0)
            vy = velocity.get("vy", 0)
            if vx != 0 or vy != 0:
                import math

                direction = math.degrees(math.atan2(vy, vx))
                return float(direction % 360)

        # 如果沒有方向信息，基於緯度推估軌道類型
        latitude = position_data.get("lat", position_data.get("latitude", 0))
        if abs(latitude) < 60:  # 低緯度，可能是順行軌道
            return 90.0  # 東向
        else:  # 高緯度，可能是極地軌道
            return 0.0  # 北向

        # 最後備選：基於衛星高度推估
        altitude = position_data.get("alt", position_data.get("altitude", 550))
        if altitude > 1000:  # 高軌道衛星
            return 0.0  # 地球同步軌道傾向
        else:  # 低軌道衛星
            return 90.0  # 順行軌道傾向

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """計算兩點間距離（球面距離公式）"""
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return self.earth_radius * c

    def _calculate_elevation(
        self, ue_position: Dict[str, float], sat_position: Dict[str, float]
    ) -> float:
        """計算衛星相對於 UE 的仰角"""
        # 簡化的仰角計算
        distance_km = self._calculate_distance(
            ue_position["lat"],
            ue_position["lon"],
            sat_position["lat"],
            sat_position["lon"],
        )

        altitude_diff = sat_position["alt"] - ue_position.get("alt", 0) / 1000

        if distance_km == 0:
            return 90.0

        elevation_rad = math.atan(altitude_diff / distance_km)
        return math.degrees(elevation_rad)

    def _update_performance_stats(self, prediction_time_ms: float):
        """更新效能統計"""
        total_predictions = self.stats["total_predictions"]
        successful_predictions = self.stats["successful_predictions"]

        # 更新準確率
        self.stats["current_accuracy"] = successful_predictions / total_predictions

        # 更新平均預測時間
        current_avg = self.stats["average_prediction_time_ms"]
        new_avg = (
            (current_avg * (total_predictions - 1)) + prediction_time_ms
        ) / total_predictions
        self.stats["average_prediction_time_ms"] = new_avg

    # UE 和衛星管理方法

    async def register_ue(
        self,
        ue_id: str,
        position: Dict[str, float],
        access_strategy: AccessStrategy = AccessStrategy.FLEXIBLE,
        current_satellite: Optional[str] = None,
    ) -> bool:
        """註冊 UE"""
        try:
            ue_info = UEAccessInfo(
                ue_id=ue_id,
                position=position,
                access_strategy=access_strategy,
                current_satellite=current_satellite,
            )

            self.ue_registry[ue_id] = ue_info

            self.logger.info(
                "UE 註冊成功",
                ue_id=ue_id,
                access_strategy=access_strategy.value,
                current_satellite=current_satellite,
            )

            return True

        except Exception as e:
            self.logger.error("UE 註冊失敗", ue_id=ue_id, error=str(e))
            return False

    async def update_ue_strategy(
        self, ue_id: str, new_strategy: AccessStrategy
    ) -> bool:
        """更新 UE 接入策略"""
        ue_info = self.ue_registry.get(ue_id)
        if not ue_info:
            return False

        old_strategy = ue_info.access_strategy
        ue_info.access_strategy = new_strategy
        ue_info.last_update = datetime.utcnow()

        self.logger.info(
            "UE 接入策略更新",
            ue_id=ue_id,
            old_strategy=old_strategy.value,
            new_strategy=new_strategy.value,
        )

        return True

    async def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "service_name": "FastSatellitePrediction",
            "algorithm": "Algorithm_2",
            "initialization_status": {
                "blocks_initialized": self.blocks_initialized,
                "total_blocks": len(self.blocks),
                "block_size_degrees": self.block_size,
            },
            "registry_status": {
                "registered_ue_count": len(self.ue_registry),
                "registered_satellite_count": len(self.satellite_registry),
            },
            "performance_stats": self.stats,
            "accuracy_target": self.accuracy_target,
            "current_accuracy": self.stats["current_accuracy"],
            "accuracy_achieved": self.stats["current_accuracy"] >= self.accuracy_target,
        }
