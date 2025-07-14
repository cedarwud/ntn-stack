"""
Phase 2.3 真實環境橋接器

連接 Phase 2.2 的真實換手環境與 RL 算法：
- 狀態空間轉換和標準化
- 動作空間映射和執行
- 獎勵函數設計和計算
- 環境重置和步驟管理
- 真實衛星數據整合
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum

# Phase 2.2 環境組件導入
from ..scenarios.handover_scenario_generator import (
    RealTimeHandoverScenarioGenerator,
    HandoverScenario,
    ScenarioComplexity,
    HandoverTriggerType,
)
from ..scenarios.handover_trigger_engine import (
    HandoverTriggerEngine,
    TriggerEvent,
    TriggerCondition,
)
from ..scenarios.candidate_scoring_service import (
    EnhancedCandidateScoringService,
    AdvancedCandidateScore,
)
from ..scenarios.signal_quality_service import (
    EnhancedSignalQualityService,
    SignalQualityMetrics,
    EnvironmentScenario,
)
from ..environments.leo_satellite_environment import LEOSatelliteEnvironment
from ...simworld_tle_bridge_service import SimWorldTLEBridgeService

logger = logging.getLogger(__name__)


class EnvironmentState(Enum):
    """環境狀態"""

    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    EPISODE_COMPLETE = "episode_complete"
    ERROR = "error"


@dataclass
class EnvironmentObservation:
    """標準化的環境觀測"""

    # UE 狀態
    ue_position: np.ndarray  # [lat, lon, alt]
    ue_velocity: np.ndarray  # [v_x, v_y, v_z]

    # 當前服務衛星狀態
    serving_satellite_id: str
    serving_satellite_position: np.ndarray  # [lat, lon, alt]
    serving_satellite_signal: Dict[str, float]  # RSRP, RSRQ, SINR
    serving_satellite_elevation: float
    serving_satellite_distance: float

    # 候選衛星狀態 (最多6個)
    candidate_satellites: List[Dict[str, Any]]
    candidate_scores: List[float]
    candidate_signal_predictions: List[Dict[str, float]]

    # 觸發條件狀態
    trigger_events: List[Dict[str, Any]]
    trigger_severity: float

    # 環境上下文
    scenario_type: str
    time_step: int
    episode_time: float

    # 性能指標
    current_throughput: float
    current_latency: float
    handover_count: int


@dataclass
class EnvironmentAction:
    """標準化的環境動作"""

    action_type: str  # "no_handover", "trigger_handover", "prepare_handover"
    target_satellite_id: Optional[str]  # 目標衛星 ID
    handover_timing: float  # 換手時機 (0-1)
    power_control: float  # 功率控制 (0-1)
    priority_level: float  # 優先級 (0-1)


@dataclass
class EnvironmentReward:
    """詳細的獎勵結構"""

    total_reward: float

    # 獎勵組成部分
    signal_quality_reward: float
    latency_reward: float
    throughput_reward: float
    handover_penalty: float
    stability_reward: float

    # 額外資訊
    successful_handover: bool
    handover_latency_ms: float
    service_interruption: bool


class RealEnvironmentBridge:
    """真實環境橋接器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化環境橋接器

        Args:
            config: 橋接器配置
        """
        self.config = config
        self.state = EnvironmentState.IDLE

        # 環境參數
        self.max_episode_steps = config.get("max_episode_steps", 1000)
        self.scenario_type = config.get("scenario_type", "urban")
        self.complexity = config.get("complexity", "moderate")
        self.observation_dim = config.get("observation_dim", 152)
        self.action_dim = config.get("action_dim", 5)

        # 獎勵權重配置
        self.reward_weights = config.get(
            "reward_weights",
            {
                "signal_quality": 0.3,
                "latency": 0.25,
                "throughput": 0.2,
                "handover_penalty": -0.15,
                "stability": 0.1,
            },
        )

        # Phase 2.2 服務組件
        self.tle_bridge = None
        self.leo_env = None
        self.scenario_generator = None
        self.trigger_engine = None
        self.scoring_service = None
        self.signal_service = None

        # 當前環境狀態
        self.current_scenario = None
        self.current_step = 0
        self.episode_start_time = None
        self.last_observation = None
        self.last_action = None

        # 歷史記錄
        self.handover_history = []
        self.performance_history = []

        logger.info("真實環境橋接器初始化")

    async def initialize(self) -> bool:
        """初始化 Phase 2.2 環境組件"""
        try:
            self.state = EnvironmentState.INITIALIZING
            logger.info("開始初始化真實環境組件...")

            # 初始化基礎服務
            self.tle_bridge = SimWorldTLEBridgeService()
            self.leo_env = LEOSatelliteEnvironment(
                {
                    "simworld_url": self.config.get(
                        "simworld_url", "http://localhost:8888"
                    ),
                    "max_satellites": 6,
                    "scenario": self.scenario_type,
                    "fallback_enabled": True,
                }
            )

            # 初始化 Phase 2.2 核心服務
            self.scenario_generator = RealTimeHandoverScenarioGenerator(
                tle_bridge_service=self.tle_bridge, leo_environment=self.leo_env
            )

            self.trigger_engine = HandoverTriggerEngine(
                tle_bridge_service=self.tle_bridge, leo_environment=self.leo_env
            )

            self.scoring_service = EnhancedCandidateScoringService(
                tle_bridge_service=self.tle_bridge,
                leo_environment=self.leo_env,
                load_balancer=self.leo_env.load_balancer,
            )

            self.signal_service = EnhancedSignalQualityService(
                tle_bridge_service=self.tle_bridge, leo_environment=self.leo_env
            )

            self.state = EnvironmentState.READY
            logger.info("真實環境組件初始化完成")
            return True

        except Exception as e:
            self.state = EnvironmentState.ERROR
            logger.error(f"真實環境初始化失敗: {e}")
            return False

    async def reset(
        self, scenario_config: Optional[Dict[str, Any]] = None
    ) -> EnvironmentObservation:
        """
        重置環境，開始新的 episode

        Args:
            scenario_config: 場景配置覆蓋

        Returns:
            EnvironmentObservation: 初始觀測
        """
        try:
            logger.info("重置真實環境...")

            # 更新場景配置
            if scenario_config:
                self.scenario_type = scenario_config.get(
                    "scenario_type", self.scenario_type
                )
                self.complexity = scenario_config.get("complexity", self.complexity)

            # 生成新的換手場景
            complexity_enum = ScenarioComplexity(self.complexity.lower())
            trigger_type = HandoverTriggerType.SIGNAL_DEGRADATION

            self.current_scenario = (
                await self.scenario_generator.generate_handover_scenario(
                    scenario_type=self.scenario_type,
                    complexity=complexity_enum,
                    trigger_type=trigger_type,
                )
            )

            # 重置環境狀態
            self.current_step = 0
            self.episode_start_time = datetime.now()
            self.handover_history.clear()
            self.performance_history.clear()

            # 獲取初始觀測
            self.last_observation = await self._get_current_observation()
            self.state = EnvironmentState.RUNNING

            logger.info(f"環境重置完成，場景 ID: {self.current_scenario.scenario_id}")
            return self.last_observation

        except Exception as e:
            self.state = EnvironmentState.ERROR
            logger.error(f"環境重置失敗: {e}")
            raise

    async def step(
        self, action: Union[EnvironmentAction, int, np.ndarray]
    ) -> Tuple[EnvironmentObservation, EnvironmentReward, bool, bool, Dict[str, Any]]:
        """
        執行環境步驟

        Args:
            action: 動作（支援多種格式）

        Returns:
            observation: 新的觀測
            reward: 獎勵
            terminated: 是否終止
            truncated: 是否截斷
            info: 額外資訊
        """
        if self.state != EnvironmentState.RUNNING:
            raise RuntimeError(f"環境狀態錯誤: {self.state}")

        try:
            start_time = datetime.now()

            # 標準化動作
            standardized_action = self._standardize_action(action)
            self.last_action = standardized_action

            # 執行動作
            execution_result = await self._execute_action(standardized_action)

            # 更新環境狀態
            self.current_step += 1

            # 獲取新的觀測
            new_observation = await self._get_current_observation()

            # 計算獎勵
            reward = await self._calculate_reward(
                self.last_observation,
                standardized_action,
                new_observation,
                execution_result,
            )

            # 檢查終止條件
            terminated = self._check_termination()
            truncated = self.current_step >= self.max_episode_steps

            # 更新歷史記錄
            step_duration = (datetime.now() - start_time).total_seconds() * 1000
            self.performance_history.append(
                {
                    "step": self.current_step,
                    "action": standardized_action.__dict__,
                    "reward": reward.__dict__,
                    "step_duration_ms": step_duration,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # 構建資訊字典
            info = {
                "scenario_id": self.current_scenario.scenario_id,
                "step_duration_ms": step_duration,
                "handover_count": len(self.handover_history),
                "successful_handovers": sum(
                    1 for h in self.handover_history if h.get("success", False)
                ),
                "execution_result": execution_result,
                "trigger_events": len(new_observation.trigger_events),
            }

            self.last_observation = new_observation

            if terminated or truncated:
                self.state = EnvironmentState.EPISODE_COMPLETE
                logger.info(
                    f"Episode 完成，步數: {self.current_step}, 總獎勵: {sum(p['reward']['total_reward'] for p in self.performance_history):.2f}"
                )

            return new_observation, reward, terminated, truncated, info

        except Exception as e:
            logger.error(f"環境步驟執行失敗: {e}")
            self.state = EnvironmentState.ERROR
            raise

    def _standardize_action(
        self, action: Union[EnvironmentAction, int, np.ndarray]
    ) -> EnvironmentAction:
        """標準化動作格式"""
        if isinstance(action, EnvironmentAction):
            return action

        if isinstance(action, int):
            # 離散動作空間映射
            action_mapping = {
                0: EnvironmentAction("no_handover", None, 0.0, 0.5, 0.5),
                1: EnvironmentAction("prepare_handover", None, 0.3, 0.7, 0.6),
                2: EnvironmentAction("trigger_handover", None, 0.8, 0.8, 0.8),
            }
            return action_mapping.get(action, action_mapping[0])

        if isinstance(action, (list, np.ndarray)):
            # 連續動作空間映射
            action = np.array(action)
            if len(action) >= 5:
                action_type_idx = int(action[0] * 3)  # 0-2
                action_types = ["no_handover", "prepare_handover", "trigger_handover"]

                return EnvironmentAction(
                    action_type=action_types[min(action_type_idx, 2)],
                    target_satellite_id=None,  # 將在執行時確定
                    handover_timing=float(action[1]),
                    power_control=float(action[2]),
                    priority_level=float(action[3]),
                )

        # 預設動作
        return EnvironmentAction("no_handover", None, 0.0, 0.5, 0.5)

    async def _execute_action(self, action: EnvironmentAction) -> Dict[str, Any]:
        """執行環境動作"""
        try:
            if action.action_type == "no_handover":
                return {"type": "no_action", "success": True, "latency_ms": 0}

            elif action.action_type == "prepare_handover":
                # 準備換手：更新候選評分，但不執行
                ue_position = self.current_scenario.ue_trajectory[
                    min(self.current_step, len(self.current_scenario.ue_trajectory) - 1)
                ]

                candidates = await self.scoring_service.score_and_rank_candidates(
                    satellites=self.current_scenario.candidate_satellites,
                    ue_position=ue_position,
                    scenario_context={"scenario_type": self.scenario_type},
                )

                return {
                    "type": "prepare_handover",
                    "success": True,
                    "candidates_evaluated": len(candidates),
                    "latency_ms": 5,
                }

            elif action.action_type == "trigger_handover":
                # 執行換手
                return await self._execute_handover(action)

            else:
                return {
                    "type": "unknown",
                    "success": False,
                    "error": f"未知動作類型: {action.action_type}",
                }

        except Exception as e:
            logger.error(f"動作執行失敗: {e}")
            return {"type": "error", "success": False, "error": str(e), "latency_ms": 0}

    async def _execute_handover(self, action: EnvironmentAction) -> Dict[str, Any]:
        """執行換手操作"""
        start_time = datetime.now()

        try:
            # 獲取當前 UE 位置
            ue_position = self.current_scenario.ue_trajectory[
                min(self.current_step, len(self.current_scenario.ue_trajectory) - 1)
            ]

            # 獲取和評分候選衛星
            candidates = await self.scoring_service.score_and_rank_candidates(
                satellites=self.current_scenario.candidate_satellites,
                ue_position=ue_position,
                scenario_context={"scenario_type": self.scenario_type},
            )

            if not candidates:
                return {
                    "type": "handover_failed",
                    "success": False,
                    "error": "沒有可用的候選衛星",
                }

            # 選擇最佳候選衛星
            best_candidate = candidates[0]
            target_satellite_id = str(best_candidate.satellite_id)

            # 預測信號品質
            signal_prediction = await self.signal_service.predict_signal_quality(
                satellite={"id": target_satellite_id},
                ue_position=ue_position,
                scenario=EnvironmentScenario.URBAN,
                time_horizons=[5, 30, 60],
            )

            # 模擬換手延遲
            base_latency = 20  # 基礎延遲 ms
            complexity_factor = {"simple": 1.0, "moderate": 1.5, "complex": 2.0}
            scenario_factor = {"urban": 1.2, "suburban": 1.0, "rural": 0.8}

            handover_latency = (
                base_latency
                * complexity_factor.get(self.complexity, 1.0)
                * scenario_factor.get(self.scenario_type, 1.0)
            )

            # 計算成功概率
            success_probability = min(
                0.95,
                best_candidate.total_score * 0.9
                + signal_prediction.get("confidence", 0.8) * 0.1,
            )

            success = np.random.random() < success_probability

            handover_event = {
                "timestamp": datetime.now(),
                "source_satellite": getattr(
                    self, "current_serving_satellite", "unknown"
                ),
                "target_satellite": target_satellite_id,
                "success": success,
                "latency_ms": handover_latency,
                "candidate_score": best_candidate.total_score,
                "signal_prediction": signal_prediction,
                "step": self.current_step,
            }

            self.handover_history.append(handover_event)

            if success:
                self.current_serving_satellite = target_satellite_id

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "type": "handover_executed",
                "success": success,
                "target_satellite": target_satellite_id,
                "handover_latency_ms": handover_latency,
                "execution_time_ms": execution_time,
                "candidate_score": best_candidate.total_score,
                "total_candidates": len(candidates),
            }

        except Exception as e:
            logger.error(f"換手執行失敗: {e}")
            return {"type": "handover_error", "success": False, "error": str(e)}

    async def _get_current_observation(self) -> EnvironmentObservation:
        """獲取當前環境觀測"""
        try:
            # 獲取當前 UE 位置
            ue_position = self.current_scenario.ue_trajectory[
                min(self.current_step, len(self.current_scenario.ue_trajectory) - 1)
            ]

            # 獲取衛星狀態
            satellite_states = await self.leo_env.get_satellite_data()

            # 當前服務衛星（如果有）
            serving_satellite = None
            serving_satellite_id = getattr(self, "current_serving_satellite", None)

            if serving_satellite_id:
                serving_satellite = next(
                    (
                        sat
                        for sat in satellite_states
                        if str(sat.id) == serving_satellite_id
                    ),
                    None,
                )

            if not serving_satellite and satellite_states:
                # 選擇第一個可用衛星作為服務衛星
                serving_satellite = satellite_states[0]
                self.current_serving_satellite = str(serving_satellite.id)

            # 候選衛星評分
            candidates = await self.scoring_service.score_and_rank_candidates(
                satellites=self.current_scenario.candidate_satellites[:6],  # 最多6個
                ue_position=ue_position,
                scenario_context={"scenario_type": self.scenario_type},
            )

            # 觸發事件檢測
            trigger_events = await self.trigger_engine.monitor_handover_triggers(
                current_serving_satellite=(
                    self.current_serving_satellite
                    if hasattr(self, "current_serving_satellite")
                    else "unknown"
                ),
                ue_position=ue_position,
                candidate_satellites=[str(c.satellite_id) for c in candidates],
            )

            # 構建觀測
            observation = EnvironmentObservation(
                ue_position=np.array(
                    [ue_position["lat"], ue_position["lon"], ue_position["alt"]]
                ),
                ue_velocity=np.array([0.0, 0.0, 0.0]),  # 簡化為靜態
                serving_satellite_id=(
                    self.current_serving_satellite
                    if hasattr(self, "current_serving_satellite")
                    else "unknown"
                ),
                serving_satellite_position=np.array(
                    [
                        (
                            serving_satellite.position.get("lat", 0.0)
                            if serving_satellite
                            else 0.0
                        ),
                        (
                            serving_satellite.position.get("lon", 0.0)
                            if serving_satellite
                            else 0.0
                        ),
                        (
                            serving_satellite.position.get("alt", 550.0)
                            if serving_satellite
                            else 550.0
                        ),
                    ]
                ),
                serving_satellite_signal={
                    "rsrp": (
                        serving_satellite.signal_quality.get("rsrp", -100.0)
                        if serving_satellite
                        else -100.0
                    ),
                    "rsrq": (
                        serving_satellite.signal_quality.get("rsrq", -15.0)
                        if serving_satellite
                        else -15.0
                    ),
                    "sinr": (
                        serving_satellite.signal_quality.get("sinr", 5.0)
                        if serving_satellite
                        else 5.0
                    ),
                },
                serving_satellite_elevation=(
                    serving_satellite.position.get("elevation", 10.0)
                    if serving_satellite
                    else 10.0
                ),
                serving_satellite_distance=(
                    serving_satellite.position.get("distance", 1000.0)
                    if serving_satellite
                    else 1000.0
                ),
                candidate_satellites=[
                    {
                        "id": str(c.satellite_id),
                        "score": c.total_score,
                        "elevation": c.satellite_state.get("elevation", 0.0),
                        "distance": c.satellite_state.get("distance", 0.0),
                    }
                    for c in candidates
                ],
                candidate_scores=[c.total_score for c in candidates],
                candidate_signal_predictions=[],  # 簡化
                trigger_events=[
                    {
                        "type": e.trigger_type.value,
                        "severity": e.severity.value,
                        "confidence": e.confidence,
                    }
                    for e in trigger_events
                ],
                trigger_severity=max(
                    [e.confidence for e in trigger_events], default=0.0
                ),
                scenario_type=self.scenario_type,
                time_step=self.current_step,
                episode_time=(
                    (datetime.now() - self.episode_start_time).total_seconds()
                    if self.episode_start_time
                    else 0.0
                ),
                current_throughput=50.0,  # 模擬值
                current_latency=30.0,  # 模擬值
                handover_count=len(self.handover_history),
            )

            return observation

        except Exception as e:
            logger.error(f"獲取觀測失敗: {e}")
            # 返回預設觀測
            return EnvironmentObservation(
                ue_position=np.array([24.0, 121.0, 100.0]),
                ue_velocity=np.array([0.0, 0.0, 0.0]),
                serving_satellite_id="default",
                serving_satellite_position=np.array([0.0, 0.0, 550.0]),
                serving_satellite_signal={"rsrp": -80.0, "rsrq": -10.0, "sinr": 10.0},
                serving_satellite_elevation=30.0,
                serving_satellite_distance=800.0,
                candidate_satellites=[],
                candidate_scores=[],
                candidate_signal_predictions=[],
                trigger_events=[],
                trigger_severity=0.0,
                scenario_type=self.scenario_type,
                time_step=self.current_step,
                episode_time=0.0,
                current_throughput=0.0,
                current_latency=100.0,
                handover_count=0,
            )

    async def _calculate_reward(
        self,
        last_obs: EnvironmentObservation,
        action: EnvironmentAction,
        new_obs: EnvironmentObservation,
        execution_result: Dict[str, Any],
    ) -> EnvironmentReward:
        """計算詳細的獎勵結構"""

        # 信號品質獎勵
        old_rsrp = last_obs.serving_satellite_signal.get("rsrp", -100.0)
        new_rsrp = new_obs.serving_satellite_signal.get("rsrp", -100.0)
        signal_improvement = (new_rsrp - old_rsrp) / 20.0  # 標準化到 [-1, 1]
        signal_quality_reward = np.clip(signal_improvement, -1.0, 1.0)

        # 延遲獎勵
        latency_penalty = -new_obs.current_latency / 100.0  # 越低越好
        latency_reward = np.clip(latency_penalty, -2.0, 0.0)

        # 吞吐量獎勵
        throughput_reward = new_obs.current_throughput / 100.0  # 標準化
        throughput_reward = np.clip(throughput_reward, 0.0, 1.0)

        # 換手懲罰
        handover_penalty = 0.0
        successful_handover = False
        handover_latency_ms = 0.0

        if action.action_type == "trigger_handover":
            handover_penalty = -0.2  # 基礎換手成本
            if execution_result.get("success", False):
                successful_handover = True
                handover_latency_ms = execution_result.get("handover_latency_ms", 0.0)
                # 成功換手的額外獎勵
                if handover_latency_ms < 30:
                    handover_penalty += 0.15  # 減少懲罰
            else:
                handover_penalty -= 0.3  # 失敗懲罰

        # 穩定性獎勵
        stability_reward = 0.0
        if (
            action.action_type == "no_handover"
            and new_obs.serving_satellite_signal.get("rsrp", -100) > -85
        ):
            stability_reward = 0.1  # 信號良好時不換手給予獎勵

        # 服務中斷檢測
        service_interruption = (
            execution_result.get("type") == "handover_failed"
            or new_obs.serving_satellite_signal.get("rsrp", -100) < -100
        )

        if service_interruption:
            stability_reward -= 0.5

        # 計算總獎勵
        total_reward = (
            signal_quality_reward * self.reward_weights["signal_quality"]
            + latency_reward * self.reward_weights["latency"]
            + throughput_reward * self.reward_weights["throughput"]
            + handover_penalty * abs(self.reward_weights["handover_penalty"])
            + stability_reward * self.reward_weights["stability"]
        )

        return EnvironmentReward(
            total_reward=total_reward,
            signal_quality_reward=signal_quality_reward,
            latency_reward=latency_reward,
            throughput_reward=throughput_reward,
            handover_penalty=handover_penalty,
            stability_reward=stability_reward,
            successful_handover=successful_handover,
            handover_latency_ms=handover_latency_ms,
            service_interruption=service_interruption,
        )

    def _check_termination(self) -> bool:
        """檢查 episode 是否應該終止"""
        # 檢查是否達到場景結束時間
        if self.episode_start_time:
            elapsed_time = (datetime.now() - self.episode_start_time).total_seconds()
            if elapsed_time > self.current_scenario.duration_seconds:
                return True

        # 檢查信號是否過差
        if (
            self.last_observation
            and self.last_observation.serving_satellite_signal.get("rsrp", -100) < -110
        ):
            return True

        # 檢查換手失敗次數
        failed_handovers = sum(
            1 for h in self.handover_history if not h.get("success", True)
        )
        if failed_handovers > 3:
            return True

        return False

    def get_observation_space_size(self) -> int:
        """獲取觀測空間大小"""
        return self.observation_dim

    def get_action_space_size(self) -> int:
        """獲取動作空間大小"""
        return self.action_dim

    def get_episode_statistics(self) -> Dict[str, Any]:
        """獲取 episode 統計資訊"""
        if not self.performance_history:
            return {}

        total_reward = sum(
            p["reward"]["total_reward"] for p in self.performance_history
        )
        successful_handovers = sum(
            1 for h in self.handover_history if h.get("success", False)
        )
        total_handovers = len(self.handover_history)

        return {
            "episode_steps": self.current_step,
            "total_reward": total_reward,
            "average_reward_per_step": total_reward / max(self.current_step, 1),
            "total_handovers": total_handovers,
            "successful_handovers": successful_handovers,
            "handover_success_rate": successful_handovers / max(total_handovers, 1),
            "average_handover_latency": (
                np.mean([h["latency_ms"] for h in self.handover_history])
                if self.handover_history
                else 0.0
            ),
            "scenario_id": (
                self.current_scenario.scenario_id
                if self.current_scenario
                else "unknown"
            ),
            "scenario_type": self.scenario_type,
            "complexity": self.complexity,
            "episode_duration_seconds": (
                (datetime.now() - self.episode_start_time).total_seconds()
                if self.episode_start_time
                else 0.0
            ),
        }

    def get_status(self) -> Dict[str, Any]:
        """獲取橋接器狀態"""
        return {
            "state": self.state.value,
            "current_step": self.current_step,
            "scenario_id": (
                self.current_scenario.scenario_id if self.current_scenario else None
            ),
            "scenario_type": self.scenario_type,
            "complexity": self.complexity,
            "handover_count": len(self.handover_history),
            "performance_history_size": len(self.performance_history),
            "services_initialized": all(
                [
                    self.tle_bridge is not None,
                    self.leo_env is not None,
                    self.scenario_generator is not None,
                    self.trigger_engine is not None,
                    self.scoring_service is not None,
                    self.signal_service is not None,
                ]
            ),
        }
