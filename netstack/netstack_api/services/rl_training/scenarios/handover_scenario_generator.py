"""
Phase 2.2 真實換手場景生成器

整合 SimWorld TLE 數據，生成基於真實軌道的 LEO 衛星換手決策場景
支援多種場景類型：都市、郊區、高移動性、低延遲需求等
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import json
import time

from ...simworld_tle_bridge_service import SimWorldTLEBridgeService
from ..environments.leo_satellite_environment import (
    LEOSatelliteEnvironment,
    SatelliteState,
    OrbitEvent,
    CandidateScore,
)

logger = logging.getLogger(__name__)


class HandoverTriggerType(Enum):
    """換手觸發類型"""

    SIGNAL_DEGRADATION = "signal_degradation"
    ELEVATION_THRESHOLD = "elevation_threshold"
    LOAD_BALANCING = "load_balancing"
    QUALITY_OPTIMIZATION = "quality_optimization"
    PREDICTIVE_HANDOVER = "predictive_handover"


class ScenarioComplexity(Enum):
    """場景複雜度"""

    SIMPLE = "simple"  # 2-3 顆候選衛星
    MODERATE = "moderate"  # 4-6 顆候選衛星
    COMPLEX = "complex"  # 6+ 顆候選衛星，多重約束


@dataclass
class HandoverScenario:
    """換手場景定義"""

    scenario_id: str
    scenario_type: str  # "urban", "suburban", "rural", "high_mobility"
    trigger_type: HandoverTriggerType
    complexity: ScenarioComplexity

    # 場景參數
    ue_trajectory: List[Dict[str, float]]  # 用戶軌跡
    time_duration_seconds: int
    candidate_satellites: List[str]

    # 約束條件
    constraints: Dict[str, Any]
    expected_handovers: int
    performance_targets: Dict[str, float]

    # 生成時間
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class ScenarioResult:
    """場景執行結果"""

    scenario_id: str
    algorithm_name: str

    # 性能指標
    total_handovers: int
    successful_handovers: int
    average_latency_ms: float
    average_signal_quality: float

    # 決策分析
    decision_details: List[Dict[str, Any]]
    reward_trajectory: List[float]

    # 時間序列
    execution_time_seconds: float
    timestamp: datetime


class RealTimeHandoverScenarioGenerator:
    """
    真實時間換手場景生成器

    整合 SimWorld TLE 數據，生成基於真實軌道動力學的換手決策場景
    """

    def __init__(
        self,
        tle_bridge_service: SimWorldTLEBridgeService,
        leo_environment: LEOSatelliteEnvironment,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化場景生成器

        Args:
            tle_bridge_service: SimWorld TLE 橋接服務
            leo_environment: LEO 衛星環境
            config: 配置參數
        """
        self.tle_bridge = tle_bridge_service
        self.leo_env = leo_environment
        self.config = config or {}

        # 場景生成配置
        self.scenario_duration_range = self.config.get(
            "scenario_duration_range", (60, 300)  # 1-5分鐘
        )
        self.trajectory_update_interval = self.config.get(
            "trajectory_update_interval", 5.0  # 5秒更新
        )
        self.handover_prediction_horizon = self.config.get(
            "handover_prediction_horizon", 60.0  # 60秒預測範圍
        )

        # 場景類型配置
        self.scenario_configs = {
            "urban": {
                "signal_attenuation_factor": 1.5,
                "interference_level": 0.3,
                "handover_frequency": "high",
                "min_elevation_deg": 15.0,
                "quality_threshold": -80.0,
            },
            "suburban": {
                "signal_attenuation_factor": 1.2,
                "interference_level": 0.2,
                "handover_frequency": "medium",
                "min_elevation_deg": 10.0,
                "quality_threshold": -85.0,
            },
            "rural": {
                "signal_attenuation_factor": 1.0,
                "interference_level": 0.1,
                "handover_frequency": "low",
                "min_elevation_deg": 5.0,
                "quality_threshold": -90.0,
            },
            "high_mobility": {
                "signal_attenuation_factor": 1.3,
                "interference_level": 0.25,
                "handover_frequency": "very_high",
                "min_elevation_deg": 20.0,
                "quality_threshold": -75.0,
                "velocity_factor": 2.0,
            },
        }

        # 統計追蹤
        self.scenarios_generated = 0
        self.scenarios_executed = 0
        self.performance_history = []

        logger.info("真實時間換手場景生成器初始化完成")

    async def generate_handover_scenario(
        self,
        scenario_type: str = "urban",
        complexity: ScenarioComplexity = ScenarioComplexity.MODERATE,
        trigger_type: HandoverTriggerType = HandoverTriggerType.SIGNAL_DEGRADATION,
        custom_constraints: Optional[Dict[str, Any]] = None,
    ) -> HandoverScenario:
        """
        生成真實換手場景

        Args:
            scenario_type: 場景類型 (urban/suburban/rural/high_mobility)
            complexity: 場景複雜度
            trigger_type: 換手觸發類型
            custom_constraints: 自定義約束條件

        Returns:
            HandoverScenario: 生成的換手場景
        """
        logger.info(
            f"開始生成換手場景 - 類型: {scenario_type}, 複雜度: {complexity.value}, 觸發: {trigger_type.value}"
        )

        # 獲取場景配置
        scenario_config = self.scenario_configs.get(
            scenario_type, self.scenario_configs["urban"]
        )

        # 生成場景 ID
        scenario_id = f"handover_{scenario_type}_{int(datetime.now().timestamp())}"

        # 生成用戶軌跡
        ue_trajectory = await self._generate_ue_trajectory(
            scenario_type, scenario_config
        )

        # 確定場景持續時間
        duration_range = self.scenario_duration_range
        duration = np.random.randint(duration_range[0], duration_range[1])

        # 獲取候選衛星
        candidate_satellites = await self._get_candidate_satellites_for_scenario(
            ue_trajectory[0], complexity, scenario_config
        )

        # 構建約束條件
        constraints = self._build_scenario_constraints(
            scenario_type, scenario_config, trigger_type, custom_constraints
        )

        # 預估期望換手次數
        expected_handovers = self._estimate_expected_handovers(
            scenario_type, duration, len(candidate_satellites)
        )

        # 設定性能目標
        performance_targets = self._define_performance_targets(
            scenario_type, trigger_type
        )

        # 創建場景
        scenario = HandoverScenario(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            trigger_type=trigger_type,
            complexity=complexity,
            ue_trajectory=ue_trajectory,
            time_duration_seconds=duration,
            candidate_satellites=candidate_satellites,
            constraints=constraints,
            expected_handovers=expected_handovers,
            performance_targets=performance_targets,
            created_at=datetime.now(),
            metadata={
                "generator_version": "2.2.0",
                "simworld_integration": True,
                "scenario_config": scenario_config,
            },
        )

        self.scenarios_generated += 1
        logger.info(f"場景生成完成 - ID: {scenario_id}, 持續時間: {duration}秒")

        return scenario

    async def _generate_ue_trajectory(
        self, scenario_type: str, scenario_config: Dict[str, Any]
    ) -> List[Dict[str, float]]:
        """
        生成用戶設備軌跡

        根據場景類型生成不同的移動模式：
        - urban: 城市格子移動
        - suburban: 郊區平滑移動
        - rural: 農村直線移動
        - high_mobility: 高速移動（車輛/飛機）
        """
        trajectory = []

        # 基礎位置（台灣新竹交大）
        base_lat, base_lon = 24.786667, 120.996944
        base_alt = 100.0

        # 根據場景類型調整移動參數
        if scenario_type == "urban":
            # 城市：小範圍、頻繁轉彎
            move_radius = 0.01  # ~1km
            velocity_ms = 5.0  # 5 m/s (步行/慢速車輛)
            waypoint_count = np.random.randint(8, 15)

        elif scenario_type == "suburban":
            # 郊區：中等範圍、平滑移動
            move_radius = 0.05  # ~5km
            velocity_ms = 15.0  # 15 m/s (汽車)
            waypoint_count = np.random.randint(5, 10)

        elif scenario_type == "rural":
            # 農村：大範圍、直線移動
            move_radius = 0.1  # ~10km
            velocity_ms = 25.0  # 25 m/s (高速公路)
            waypoint_count = np.random.randint(3, 6)

        elif scenario_type == "high_mobility":
            # 高移動性：很大範圍、高速移動
            move_radius = 0.2  # ~20km
            velocity_ms = 50.0  # 50 m/s (飛機)
            waypoint_count = np.random.randint(2, 5)
            velocity_ms *= scenario_config.get("velocity_factor", 1.0)
        else:
            # 默認配置
            move_radius = 0.02
            velocity_ms = 10.0
            waypoint_count = 6

        # 生成軌跡點
        for i in range(waypoint_count):
            # 隨機角度和距離
            angle = np.random.uniform(0, 2 * np.pi)
            distance = np.random.uniform(0, move_radius)

            # 計算位置
            lat = base_lat + distance * np.cos(angle)
            lon = base_lon + distance * np.sin(angle)
            alt = base_alt + np.random.uniform(-50, 100)  # 高度變化

            # 時間戳（基於速度計算）
            if i == 0:
                timestamp = 0.0
            else:
                prev_lat, prev_lon = trajectory[-1]["lat"], trajectory[-1]["lon"]
                distance_m = self._calculate_distance_meters(
                    (prev_lat, prev_lon), (lat, lon)
                )
                time_delta = distance_m / velocity_ms
                timestamp = trajectory[-1]["timestamp"] + time_delta

            trajectory.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "timestamp": timestamp,
                    "velocity_ms": velocity_ms,
                }
            )

        logger.debug(f"生成軌跡 - 場景: {scenario_type}, 軌跡點: {len(trajectory)}")
        return trajectory

    async def _get_candidate_satellites_for_scenario(
        self,
        initial_position: Dict[str, float],
        complexity: ScenarioComplexity,
        scenario_config: Dict[str, Any],
    ) -> List[str]:
        """
        獲取場景的候選衛星列表

        基於複雜度和場景配置，從 SimWorld 獲取合適的候選衛星
        """
        # 根據複雜度確定衛星數量
        satellite_counts = {
            ScenarioComplexity.SIMPLE: (2, 3),
            ScenarioComplexity.MODERATE: (4, 6),
            ScenarioComplexity.COMPLEX: (6, 10),
        }

        min_sats, max_sats = satellite_counts[complexity]
        target_count = np.random.randint(min_sats, max_sats + 1)

        try:
            # 從 SimWorld 獲取可見衛星
            observer_location = {
                "lat": initial_position["lat"],
                "lon": initial_position["lon"],
                "alt": initial_position["alt"],
            }

            # 使用 LEO 環境的衛星獲取方法
            satellites = await self.leo_env.get_satellite_data()

            # 過濾符合條件的衛星
            min_elevation = scenario_config.get("min_elevation_deg", 10.0)
            qualified_satellites = [
                sat
                for sat in satellites
                if sat.position.get("elevation", 0) >= min_elevation
            ]

            # 如果合格衛星不足，使用 fallback
            if len(qualified_satellites) < target_count:
                logger.warning(
                    f"合格衛星不足 - 合格: {len(qualified_satellites)}, 目標: {target_count}，使用 fallback 機制"
                )
                qualified_satellites = self.leo_env._get_fallback_satellite_data()

            # 選擇候選衛星
            candidate_satellites = qualified_satellites[:target_count]
            satellite_ids = [str(sat.id) for sat in candidate_satellites]

            logger.info(
                f"選擇候選衛星 - 數量: {len(satellite_ids)}, 複雜度: {complexity.value}"
            )

            return satellite_ids

        except Exception as e:
            logger.error(f"獲取候選衛星失敗: {e}")
            # 返回 fallback 衛星 ID
            fallback_ids = ["44713", "44714", "44715", "44716", "44717", "44718"]
            return fallback_ids[:target_count]

    def _build_scenario_constraints(
        self,
        scenario_type: str,
        scenario_config: Dict[str, Any],
        trigger_type: HandoverTriggerType,
        custom_constraints: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        構建場景約束條件

        基於場景類型、觸發類型和自定義約束構建完整的約束集合
        """
        constraints = {
            # 信號品質約束
            "min_rsrp_dbm": scenario_config.get("quality_threshold", -85.0),
            "min_rsrq_db": -15.0,
            "min_sinr_db": 5.0,
            # 仰角約束
            "min_elevation_deg": scenario_config.get("min_elevation_deg", 10.0),
            "max_elevation_deg": 90.0,
            # 負載約束
            "max_load_factor": 0.9,
            "load_balance_weight": 0.3,
            # 延遲約束
            "max_handover_latency_ms": 50.0,
            "max_decision_time_ms": 10.0,
            # 場景特定約束
            "signal_attenuation_factor": scenario_config.get(
                "signal_attenuation_factor", 1.0
            ),
            "interference_level": scenario_config.get("interference_level", 0.2),
        }

        # 基於觸發類型添加特定約束
        if trigger_type == HandoverTriggerType.SIGNAL_DEGRADATION:
            constraints.update(
                {"degradation_threshold_db": -3.0, "degradation_time_window_s": 5.0}
            )
        elif trigger_type == HandoverTriggerType.LOAD_BALANCING:
            constraints.update({"load_threshold": 0.8, "balance_hysteresis": 0.1})
        elif trigger_type == HandoverTriggerType.PREDICTIVE_HANDOVER:
            constraints.update(
                {"prediction_horizon_s": 30.0, "prediction_confidence_min": 0.7}
            )

        # 合併自定義約束
        if custom_constraints:
            constraints.update(custom_constraints)

        return constraints

    def _estimate_expected_handovers(
        self, scenario_type: str, duration_seconds: int, candidate_count: int
    ) -> int:
        """
        估算期望的換手次數

        基於場景類型、持續時間和候選衛星數量
        """
        # 基礎換手頻率（每分鐘）
        base_frequencies = {
            "urban": 0.5,
            "suburban": 0.3,
            "rural": 0.2,
            "high_mobility": 1.0,
        }

        base_freq = base_frequencies.get(scenario_type, 0.3)

        # 根據候選衛星數量調整
        satellite_factor = min(candidate_count / 4.0, 2.0)  # 最多2倍

        # 計算期望換手次數
        expected = base_freq * (duration_seconds / 60.0) * satellite_factor
        return max(1, int(np.round(expected)))

    def _define_performance_targets(
        self, scenario_type: str, trigger_type: HandoverTriggerType
    ) -> Dict[str, float]:
        """
        定義場景的性能目標
        """
        base_targets = {
            "handover_success_rate": 0.95,
            "average_latency_ms": 30.0,
            "signal_quality_improvement": 5.0,  # dB
            "load_balance_efficiency": 0.8,
        }

        # 根據場景類型調整
        if scenario_type == "high_mobility":
            base_targets["handover_success_rate"] = 0.90
            base_targets["average_latency_ms"] = 20.0
        elif scenario_type == "urban":
            base_targets["signal_quality_improvement"] = 3.0

        # 根據觸發類型調整
        if trigger_type == HandoverTriggerType.PREDICTIVE_HANDOVER:
            base_targets["average_latency_ms"] = 15.0
        elif trigger_type == HandoverTriggerType.LOAD_BALANCING:
            base_targets["load_balance_efficiency"] = 0.9

        return base_targets

    def _calculate_distance_meters(
        self, pos1: Tuple[float, float], pos2: Tuple[float, float]
    ) -> float:
        """
        計算兩點之間的距離（米）

        使用 Haversine 公式計算球面距離
        """
        lat1, lon1 = np.radians(pos1)
        lat2, lon2 = np.radians(pos2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        # 地球半径（米）
        earth_radius_m = 6371000

        return earth_radius_m * c

    async def execute_scenario_with_algorithm(
        self, scenario: HandoverScenario, algorithm_name: str, algorithm_instance: Any
    ) -> ScenarioResult:
        """
        使用指定算法執行換手場景

        Args:
            scenario: 要執行的場景
            algorithm_name: 算法名稱
            algorithm_instance: 算法實例

        Returns:
            ScenarioResult: 執行結果
        """
        logger.info(
            f"開始執行場景 - ID: {scenario.scenario_id}, 算法: {algorithm_name}"
        )

        start_time = time.time()
        decision_details = []
        reward_trajectory = []
        handover_count = 0
        successful_handovers = 0
        latency_measurements = []
        signal_quality_measurements = []

        try:
            # 初始化環境
            await self.leo_env.reset()

            # 模擬場景執行
            for i, ue_position in enumerate(scenario.ue_trajectory):
                step_start = time.time()

                # 獲取當前衛星狀態
                current_satellites = await self.leo_env.get_satellite_data()

                # 構建算法輸入狀態
                state = self._build_algorithm_state(
                    ue_position, current_satellites, scenario
                )

                # 執行算法決策
                action = await algorithm_instance.predict(state)

                # 執行環境步驟
                observation, reward, terminated, truncated, info = (
                    await self.leo_env.step(action)
                )

                # 記錄決策詳情
                step_latency = (time.time() - step_start) * 1000  # ms
                latency_measurements.append(step_latency)

                if info.get("total_handovers", 0) > handover_count:
                    handover_count = info["total_handovers"]
                    if info.get("handover_success_rate", 0) > 0:
                        successful_handovers = info["successful_handovers"]

                # 記錄信號品質
                if current_satellites:
                    avg_signal = np.mean(
                        [
                            sat.signal_quality.get("rsrp", -100)
                            for sat in current_satellites
                        ]
                    )
                    signal_quality_measurements.append(avg_signal)

                decision_detail = {
                    "step": i,
                    "timestamp": ue_position["timestamp"],
                    "ue_position": ue_position.copy(),
                    "selected_action": action,
                    "reward": reward,
                    "latency_ms": step_latency,
                    "serving_satellite": info.get("serving_satellite_id"),
                    "available_satellites": info.get("available_satellites", 0),
                }
                decision_details.append(decision_detail)
                reward_trajectory.append(reward)

                if terminated or truncated:
                    break

            # 計算性能指標
            execution_time = time.time() - start_time
            avg_latency = (
                float(np.mean(latency_measurements)) if latency_measurements else 0.0
            )
            avg_signal_quality = (
                float(np.mean(signal_quality_measurements))
                if signal_quality_measurements
                else -100.0
            )

            # 創建結果
            result = ScenarioResult(
                scenario_id=scenario.scenario_id,
                algorithm_name=algorithm_name,
                total_handovers=handover_count,
                successful_handovers=successful_handovers,
                average_latency_ms=avg_latency,
                average_signal_quality=avg_signal_quality,
                decision_details=decision_details,
                reward_trajectory=reward_trajectory,
                execution_time_seconds=execution_time,
                timestamp=datetime.now(),
            )

            self.scenarios_executed += 1
            self.performance_history.append(result)

            logger.info(
                f"場景執行完成 - ID: {scenario.scenario_id}, 換手: {handover_count}, 執行時間: {execution_time:.2f}s, 平均延遲: {avg_latency:.2f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"場景執行失敗: {e}")
            # 返回失敗結果
            return ScenarioResult(
                scenario_id=scenario.scenario_id,
                algorithm_name=algorithm_name,
                total_handovers=0,
                successful_handovers=0,
                average_latency_ms=float("inf"),
                average_signal_quality=-200.0,
                decision_details=[],
                reward_trajectory=[],
                execution_time_seconds=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def _build_algorithm_state(
        self,
        ue_position: Dict[str, float],
        current_satellites: List[SatelliteState],
        scenario: HandoverScenario,
    ) -> Any:
        """
        構建算法輸入狀態

        將當前環境狀態轉換為算法可處理的格式
        """
        # 對於簡單的演示，返回標準化的觀測值
        state_features = []

        max_satellites = 6  # 與環境配置一致
        for i in range(max_satellites):
            if i < len(current_satellites):
                sat = current_satellites[i]
                features = [
                    sat.signal_quality.get("rsrp", -150),
                    sat.signal_quality.get("rsrq", -20),
                    sat.signal_quality.get("sinr", -10),
                    sat.load_factor,
                    sat.position.get("elevation", 0),
                    sat.position.get("range", 2000),
                ]
            else:
                # 填充零值
                features = [-150, -20, -10, 0, 0, 2000]

            state_features.extend(features)

        return np.array(state_features, dtype=np.float32)

    async def get_scenario_statistics(self) -> Dict[str, Any]:
        """
        獲取場景生成器統計信息
        """
        recent_performance = (
            self.performance_history[-10:] if self.performance_history else []
        )

        avg_execution_time = (
            np.mean([r.execution_time_seconds for r in recent_performance])
            if recent_performance
            else 0.0
        )

        avg_handover_success = (
            np.mean(
                [
                    r.successful_handovers / max(r.total_handovers, 1)
                    for r in recent_performance
                ]
            )
            if recent_performance
            else 0.0
        )

        return {
            "scenarios_generated": self.scenarios_generated,
            "scenarios_executed": self.scenarios_executed,
            "recent_avg_execution_time": avg_execution_time,
            "recent_avg_handover_success_rate": avg_handover_success,
            "performance_history_length": len(self.performance_history),
            "supported_scenario_types": list(self.scenario_configs.keys()),
            "supported_trigger_types": [t.value for t in HandoverTriggerType],
            "supported_complexity_levels": [c.value for c in ScenarioComplexity],
        }

    async def cleanup_old_scenarios(self, max_age_hours: int = 24):
        """
        清理舊的場景記錄
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        initial_count = len(self.performance_history)

        self.performance_history = [
            result
            for result in self.performance_history
            if result.timestamp > cutoff_time
        ]

        cleaned_count = initial_count - len(self.performance_history)
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 個舊場景記錄")
