"""
Phase 2.2 統一候選衛星篩選和評分服務

基於 Phase 2.1 的評分系統，添加更先進的篩選邏輯和多維度評分機制
整合真實軌道數據、信號預測、負載平衡和預測性分析
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
import json

from ...simworld_tle_bridge_service import SimWorldTLEBridgeService
from ..environments.leo_satellite_environment import (
    LEOSatelliteEnvironment,
    SatelliteState,
    CandidateScore,
    DynamicLoadBalancer,
)

logger = logging.getLogger(__name__)


class ScoringMethod(Enum):
    """評分方法類型"""

    WEIGHTED_SUM = "weighted_sum"
    FUZZY_LOGIC = "fuzzy_logic"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"


class FilterCriteria(Enum):
    """篩選條件類型"""

    MIN_ELEVATION = "min_elevation"
    MIN_SIGNAL_QUALITY = "min_signal_quality"
    MAX_LOAD_FACTOR = "max_load_factor"
    MIN_PREDICTION_CONFIDENCE = "min_prediction_confidence"
    GEOGRAPHIC_CONSTRAINT = "geographic_constraint"


@dataclass
class ScoringWeights:
    """評分權重配置"""

    signal_quality: float = 0.35
    load_factor: float = 0.25
    elevation_angle: float = 0.15
    distance: float = 0.15
    prediction_confidence: float = 0.10

    def validate(self) -> bool:
        """驗證權重總和是否為1"""
        total = (
            self.signal_quality
            + self.load_factor
            + self.elevation_angle
            + self.distance
            + self.prediction_confidence
        )
        return abs(total - 1.0) < 0.01


@dataclass
class AdvancedCandidateScore(CandidateScore):
    """增強版候選衛星評分"""

    # 繼承基礎評分，添加新字段
    prediction_confidence: float = 0.0
    stability_score: float = 0.0
    handover_cost: float = 0.0
    future_trajectory_score: float = 0.0

    # 詳細分析
    signal_trend: str = "stable"  # "improving", "degrading", "stable"
    load_trend: str = "stable"
    elevation_trend: str = "stable"

    # 時間相關
    optimal_handover_time: Optional[datetime] = None
    service_duration_estimate: float = 0.0  # 秒

    # 風險評估
    handover_risk_level: str = "medium"  # "low", "medium", "high"
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class FilterRule:
    """篩選規則定義"""

    criteria: FilterCriteria
    threshold: float
    operator: str  # ">=", "<=", "==", "!=", "in", "not_in"
    enabled: bool = True
    priority: int = 1
    description: str = ""


class EnhancedCandidateScoringService:
    """
    增強候選衛星篩選和評分服務

    整合多種評分方法和篩選策略，提供智能的候選衛星選擇
    """

    def __init__(
        self,
        tle_bridge_service: SimWorldTLEBridgeService,
        leo_environment: LEOSatelliteEnvironment,
        load_balancer: DynamicLoadBalancer,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化評分服務

        Args:
            tle_bridge_service: SimWorld TLE 橋接服務
            leo_environment: LEO 衛星環境
            load_balancer: 動態負載平衡器
            config: 配置參數
        """
        self.tle_bridge = tle_bridge_service
        self.leo_env = leo_environment
        self.load_balancer = load_balancer
        self.config = config or {}

        # 評分配置
        self.scoring_method = ScoringMethod(
            self.config.get("scoring_method", "weighted_sum")
        )
        self.scoring_weights = ScoringWeights(**self.config.get("scoring_weights", {}))

        # 篩選規則
        self.filter_rules: List[FilterRule] = []
        self._initialize_default_filters()

        # 預測配置
        self.prediction_horizon_s = self.config.get(
            "prediction_horizon_s", 300.0
        )  # 5分鐘
        self.min_service_duration_s = self.config.get(
            "min_service_duration_s", 60.0
        )  # 1分鐘

        # 歷史數據
        self.scoring_history: Dict[str, List[Dict[str, Any]]] = {}
        self.performance_metrics: Dict[str, float] = {}

        # 統計
        self.candidates_scored = 0
        self.filtering_efficiency = 0.0

        logger.info("增強候選衛星評分服務初始化完成")

    def _initialize_default_filters(self):
        """初始化默認篩選規則"""

        # 基本篩選規則
        self.filter_rules = [
            FilterRule(
                criteria=FilterCriteria.MIN_ELEVATION,
                threshold=10.0,
                operator=">=",
                priority=1,
                description="最小仰角要求",
            ),
            FilterRule(
                criteria=FilterCriteria.MIN_SIGNAL_QUALITY,
                threshold=-85.0,
                operator=">=",
                priority=2,
                description="最小信號品質要求 (RSRP)",
            ),
            FilterRule(
                criteria=FilterCriteria.MAX_LOAD_FACTOR,
                threshold=0.9,
                operator="<=",
                priority=3,
                description="最大負載因子限制",
            ),
            FilterRule(
                criteria=FilterCriteria.MIN_PREDICTION_CONFIDENCE,
                threshold=0.6,
                operator=">=",
                priority=4,
                description="最小預測置信度要求",
            ),
        ]

    async def score_and_rank_candidates(
        self,
        satellites: List[SatelliteState],
        ue_position: Dict[str, float],
        current_serving_satellite: Optional[str] = None,
        scenario_context: Optional[Dict[str, Any]] = None,
    ) -> List[AdvancedCandidateScore]:
        """
        評分並排序候選衛星

        Args:
            satellites: 候選衛星列表
            ue_position: 用戶設備位置
            current_serving_satellite: 當前服務衛星 ID
            scenario_context: 場景上下文信息

        Returns:
            List[AdvancedCandidateScore]: 排序後的評分結果
        """
        logger.info(f"開始評分 {len(satellites)} 個候選衛星")

        try:
            # 第一步：基本篩選
            filtered_satellites = await self._apply_filters(satellites, ue_position)
            logger.info(f"篩選後剩餘 {len(filtered_satellites)} 個候選衛星")

            if not filtered_satellites:
                logger.warning("所有候選衛星都被篩選器過濾掉了")
                return []

            # 第二步：詳細評分
            scored_candidates = []
            for satellite in filtered_satellites:
                score = await self._calculate_advanced_score(
                    satellite, ue_position, current_serving_satellite, scenario_context
                )
                scored_candidates.append(score)
                self.candidates_scored += 1

            # 第三步：排序
            scored_candidates.sort(key=lambda x: x.overall_score, reverse=True)

            # 第四步：後處理優化
            optimized_candidates = await self._post_process_candidates(
                scored_candidates, ue_position, scenario_context
            )

            # 更新統計
            self.filtering_efficiency = len(filtered_satellites) / max(
                len(satellites), 1
            )

            logger.info(
                f"評分完成 - 最佳候選: {optimized_candidates[0].satellite_id if optimized_candidates else 'None'}"
            )

            return optimized_candidates

        except Exception as e:
            logger.error(f"候選衛星評分失敗: {e}")
            return []

    async def _apply_filters(
        self, satellites: List[SatelliteState], ue_position: Dict[str, float]
    ) -> List[SatelliteState]:
        """應用篩選規則"""

        filtered_satellites = satellites.copy()

        # 按優先級排序規則
        sorted_rules = sorted(
            [rule for rule in self.filter_rules if rule.enabled],
            key=lambda x: x.priority,
        )

        for rule in sorted_rules:
            initial_count = len(filtered_satellites)
            filtered_satellites = await self._apply_single_filter(
                filtered_satellites, rule, ue_position
            )

            filtered_count = len(filtered_satellites)
            logger.debug(
                f"篩選規則 {rule.criteria.value}: {initial_count} -> {filtered_count}"
            )

            if not filtered_satellites:
                logger.warning(f"篩選規則 {rule.criteria.value} 過濾掉了所有候選衛星")
                break

        return filtered_satellites

    async def _apply_single_filter(
        self,
        satellites: List[SatelliteState],
        rule: FilterRule,
        ue_position: Dict[str, float],
    ) -> List[SatelliteState]:
        """應用單個篩選規則"""

        filtered = []

        for satellite in satellites:
            try:
                if await self._evaluate_filter_condition(satellite, rule, ue_position):
                    filtered.append(satellite)
            except Exception as e:
                logger.warning(f"評估篩選條件時發生錯誤: {e}")
                # 保守策略：保留衛星
                filtered.append(satellite)

        return filtered

    async def _evaluate_filter_condition(
        self, satellite: SatelliteState, rule: FilterRule, ue_position: Dict[str, float]
    ) -> bool:
        """評估篩選條件"""

        # 獲取評估值
        if rule.criteria == FilterCriteria.MIN_ELEVATION:
            value = satellite.position.get("elevation", 0)
        elif rule.criteria == FilterCriteria.MIN_SIGNAL_QUALITY:
            value = satellite.signal_quality.get("rsrp", -150)
        elif rule.criteria == FilterCriteria.MAX_LOAD_FACTOR:
            value = satellite.load_factor
        elif rule.criteria == FilterCriteria.MIN_PREDICTION_CONFIDENCE:
            # 計算預測置信度
            value = await self._calculate_prediction_confidence(satellite, ue_position)
        else:
            return True

        # 應用操作符
        threshold = rule.threshold
        operator = rule.operator

        if operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.01
        elif operator == "!=":
            return abs(value - threshold) >= 0.01
        else:
            logger.warning(f"未知的操作符: {operator}")
            return True

    async def _calculate_prediction_confidence(
        self, satellite: SatelliteState, ue_position: Dict[str, float]
    ) -> float:
        """計算預測置信度"""

        try:
            # 基於歷史數據計算預測置信度
            satellite_id = str(satellite.id)

            # 檢查歷史記錄
            if satellite_id in self.leo_env.satellite_history:
                history = self.leo_env.satellite_history[satellite_id]
                if len(history) >= 3:
                    # 分析趨勢穩定性
                    rsrp_values = [h["signal_quality"]["rsrp"] for h in history[-5:]]
                    rsrp_variance = np.var(rsrp_values)

                    # 方差越小，預測越可靠
                    confidence = max(0.0, 1.0 - rsrp_variance / 100.0)
                    return min(confidence, 1.0)

            # 默認中等置信度
            return 0.7

        except Exception as e:
            logger.warning(f"計算預測置信度失敗: {e}")
            return 0.5

    async def _calculate_advanced_score(
        self,
        satellite: SatelliteState,
        ue_position: Dict[str, float],
        current_serving_satellite: Optional[str],
        scenario_context: Optional[Dict[str, Any]],
    ) -> AdvancedCandidateScore:
        """計算增強版評分"""

        satellite_id = satellite.id

        # 基礎評分（使用 Phase 2.1 的方法）
        basic_scores = self._calculate_basic_scores(satellite)

        # 新增評分維度
        prediction_confidence = await self._calculate_prediction_confidence(
            satellite, ue_position
        )
        stability_score = await self._calculate_stability_score(satellite)
        handover_cost = await self._calculate_handover_cost(
            satellite, current_serving_satellite, ue_position
        )
        future_trajectory_score = await self._calculate_future_trajectory_score(
            satellite, ue_position
        )

        # 趨勢分析
        trends = self._analyze_trends(satellite)

        # 時間預測
        optimal_time, service_duration = await self._predict_optimal_handover_timing(
            satellite, ue_position
        )

        # 風險評估
        risk_level, risk_factors = self._assess_handover_risks(
            satellite, scenario_context
        )

        # 綜合評分
        if self.scoring_method == ScoringMethod.WEIGHTED_SUM:
            overall_score = (
                basic_scores["signal"] * self.scoring_weights.signal_quality
                + basic_scores["load"] * self.scoring_weights.load_factor
                + basic_scores["elevation"] * self.scoring_weights.elevation_angle
                + basic_scores["distance"] * self.scoring_weights.distance
                + prediction_confidence
                * 100
                * self.scoring_weights.prediction_confidence
            )
        else:
            # 其他評分方法可以在這裡實現
            overall_score = (
                basic_scores["signal"]
                + basic_scores["load"]
                + basic_scores["elevation"]
                + basic_scores["distance"]
            ) / 4

        # 創建增強評分對象
        advanced_score = AdvancedCandidateScore(
            satellite_id=satellite_id,
            signal_score=basic_scores["signal"],
            load_score=basic_scores["load"],
            elevation_score=basic_scores["elevation"],
            distance_score=basic_scores["distance"],
            overall_score=overall_score,
            score_breakdown={
                "signal_quality": basic_scores["signal"],
                "load_factor": basic_scores["load"],
                "elevation_angle": basic_scores["elevation"],
                "distance": basic_scores["distance"],
                "prediction_confidence": prediction_confidence * 100,
                "stability": stability_score,
                "handover_cost": handover_cost,
                "future_trajectory": future_trajectory_score,
            },
            # 新增字段
            prediction_confidence=prediction_confidence,
            stability_score=stability_score,
            handover_cost=handover_cost,
            future_trajectory_score=future_trajectory_score,
            signal_trend=trends["signal"],
            load_trend=trends["load"],
            elevation_trend=trends["elevation"],
            optimal_handover_time=optimal_time,
            service_duration_estimate=service_duration,
            handover_risk_level=risk_level,
            risk_factors=risk_factors,
        )

        return advanced_score

    def _calculate_basic_scores(self, satellite: SatelliteState) -> Dict[str, float]:
        """計算基礎評分（使用 LEOSatelliteEnvironment 的方法）"""

        # 信號品質評分
        signal_score = self.leo_env._calculate_signal_score(satellite)

        # 負載評分
        load_score = self.leo_env._calculate_load_score(satellite)

        # 仰角評分
        elevation_score = self.leo_env._calculate_elevation_score(satellite)

        # 距離評分
        distance_score = self.leo_env._calculate_distance_score(satellite)

        return {
            "signal": signal_score,
            "load": load_score,
            "elevation": elevation_score,
            "distance": distance_score,
        }

    async def _calculate_stability_score(self, satellite: SatelliteState) -> float:
        """計算穩定性評分"""

        try:
            satellite_id = str(satellite.id)

            if satellite_id not in self.leo_env.satellite_history:
                return 50.0  # 默認中等穩定性

            history = self.leo_env.satellite_history[satellite_id]
            if len(history) < 3:
                return 60.0

            # 分析各項指標的穩定性
            rsrp_values = [h["signal_quality"]["rsrp"] for h in history[-10:]]
            load_values = [h["load_factor"] for h in history[-10:]]
            elevation_values = [h["position"]["elevation"] for h in history[-10:]]

            # 計算變異係數（標準差/均值）
            rsrp_cv = np.std(rsrp_values) / max(abs(np.mean(rsrp_values)), 1.0)
            load_cv = np.std(load_values) / max(np.mean(load_values), 0.1)
            elevation_cv = np.std(elevation_values) / max(
                np.mean(elevation_values), 1.0
            )

            # 穩定性評分（變異係數越小越穩定）
            rsrp_stability = max(0.0, 100.0 - rsrp_cv * 1000)
            load_stability = max(0.0, 100.0 - load_cv * 100)
            elevation_stability = max(0.0, 100.0 - elevation_cv * 100)

            # 加權平均
            stability_score = (
                rsrp_stability * 0.4 + load_stability * 0.3 + elevation_stability * 0.3
            )

            return np.clip(stability_score, 0.0, 100.0)

        except Exception as e:
            logger.warning(f"計算穩定性評分失敗: {e}")
            return 50.0

    async def _calculate_handover_cost(
        self,
        satellite: SatelliteState,
        current_serving_satellite: Optional[str],
        ue_position: Dict[str, float],
    ) -> float:
        """計算換手成本"""

        if (
            not current_serving_satellite
            or str(satellite.id) == current_serving_satellite
        ):
            return 0.0  # 不需要換手

        # 換手成本因子
        signaling_cost = 10.0  # 信令開銷
        interruption_cost = 5.0  # 服務中斷成本

        # 根據信號品質差異調整成本
        try:
            current_satellite = None
            for sat in await self.leo_env.get_satellite_data():
                if str(sat.id) == current_serving_satellite:
                    current_satellite = sat
                    break

            if current_satellite:
                current_rsrp = current_satellite.signal_quality.get("rsrp", -100)
                target_rsrp = satellite.signal_quality.get("rsrp", -100)

                # 如果目標衛星信號顯著更好，降低換手成本
                signal_improvement = target_rsrp - current_rsrp
                if signal_improvement > 5.0:
                    return max(0.0, signaling_cost - signal_improvement)
                else:
                    return signaling_cost + interruption_cost

        except Exception as e:
            logger.warning(f"計算換手成本時發生錯誤: {e}")

        return signaling_cost

    async def _calculate_future_trajectory_score(
        self, satellite: SatelliteState, ue_position: Dict[str, float]
    ) -> float:
        """計算未來軌跡評分"""

        try:
            # 使用 TLE 橋接服務預測未來軌跡
            satellite_id = str(satellite.id)
            current_time = datetime.now()
            future_time = current_time + timedelta(seconds=self.prediction_horizon_s)

            # 簡化的軌跡評分
            # 在實際實現中，這裡會使用完整的軌道預測

            current_elevation = satellite.position.get("elevation", 0)
            current_rsrp = satellite.signal_quality.get("rsrp", -100)

            # 基於當前趨勢的簡單預測
            if satellite.id in self.leo_env.satellite_history:
                history = self.leo_env.satellite_history[satellite.id][-5:]
                if len(history) >= 2:
                    # 計算仰角變化趨勢
                    elevation_trend = (
                        history[-1]["position"]["elevation"]
                        - history[0]["position"]["elevation"]
                    )

                    # 未來軌跡評分基於仰角趨勢
                    if elevation_trend > 0:  # 仰角上升
                        return min(100.0, 80.0 + elevation_trend * 2)
                    elif elevation_trend < -5:  # 仰角快速下降
                        return max(0.0, 50.0 + elevation_trend * 2)
                    else:  # 穩定
                        return 70.0

            # 默認評分
            return 60.0

        except Exception as e:
            logger.warning(f"計算未來軌跡評分失敗: {e}")
            return 50.0

    def _analyze_trends(self, satellite: SatelliteState) -> Dict[str, str]:
        """分析衛星指標趨勢"""

        trends = {"signal": "stable", "load": "stable", "elevation": "stable"}

        try:
            satellite_id = str(satellite.id)

            if satellite_id in self.leo_env.satellite_history:
                history = self.leo_env.satellite_history[satellite_id][-5:]

                if len(history) >= 3:
                    # 信號趨勢
                    rsrp_values = [h["signal_quality"]["rsrp"] for h in history]
                    rsrp_trend = rsrp_values[-1] - rsrp_values[0]

                    if rsrp_trend > 2.0:
                        trends["signal"] = "improving"
                    elif rsrp_trend < -2.0:
                        trends["signal"] = "degrading"

                    # 負載趨勢
                    load_values = [h["load_factor"] for h in history]
                    load_trend = load_values[-1] - load_values[0]

                    if load_trend > 0.1:
                        trends["load"] = "increasing"
                    elif load_trend < -0.1:
                        trends["load"] = "decreasing"

                    # 仰角趨勢
                    elevation_values = [h["position"]["elevation"] for h in history]
                    elevation_trend = elevation_values[-1] - elevation_values[0]

                    if elevation_trend > 2.0:
                        trends["elevation"] = "rising"
                    elif elevation_trend < -2.0:
                        trends["elevation"] = "falling"

        except Exception as e:
            logger.warning(f"分析趨勢時發生錯誤: {e}")

        return trends

    async def _predict_optimal_handover_timing(
        self, satellite: SatelliteState, ue_position: Dict[str, float]
    ) -> Tuple[Optional[datetime], float]:
        """預測最佳換手時機"""

        try:
            # 簡化的時機預測
            current_time = datetime.now()

            # 基於信號品質預測最佳換手窗口
            current_rsrp = satellite.signal_quality.get("rsrp", -100)
            current_elevation = satellite.position.get("elevation", 0)

            # 如果當前條件已經很好，立即換手
            if current_rsrp > -70 and current_elevation > 30:
                return current_time, self.prediction_horizon_s

            # 否則預測未來30秒的最佳時機
            optimal_time = current_time + timedelta(seconds=30)
            service_duration = max(
                self.min_service_duration_s, self.prediction_horizon_s * 0.6
            )

            return optimal_time, service_duration

        except Exception as e:
            logger.warning(f"預測最佳換手時機失敗: {e}")
            return None, self.min_service_duration_s

    def _assess_handover_risks(
        self, satellite: SatelliteState, scenario_context: Optional[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """評估換手風險"""

        risk_factors = []
        risk_level = "medium"

        try:
            # 信號風險
            rsrp = satellite.signal_quality.get("rsrp", -100)
            if rsrp < -90:
                risk_factors.append("weak_signal")

            # 仰角風險
            elevation = satellite.position.get("elevation", 0)
            if elevation < 15:
                risk_factors.append("low_elevation")

            # 負載風險
            load_factor = satellite.load_factor
            if load_factor > 0.8:
                risk_factors.append("high_load")

            # 穩定性風險
            satellite_id = str(satellite.id)
            if satellite_id in self.leo_env.satellite_history:
                history = self.leo_env.satellite_history[satellite_id]
                if len(history) < 3:
                    risk_factors.append("insufficient_history")

            # 場景風險
            if scenario_context:
                scenario_type = scenario_context.get("scenario_type", "urban")
                if scenario_type == "high_mobility":
                    risk_factors.append("high_mobility_scenario")

            # 評估總體風險等級
            if len(risk_factors) >= 3:
                risk_level = "high"
            elif len(risk_factors) >= 1:
                risk_level = "medium"
            else:
                risk_level = "low"

        except Exception as e:
            logger.warning(f"評估換手風險失敗: {e}")
            risk_factors.append("assessment_error")

        return risk_level, risk_factors

    async def _post_process_candidates(
        self,
        candidates: List[AdvancedCandidateScore],
        ue_position: Dict[str, float],
        scenario_context: Optional[Dict[str, Any]],
    ) -> List[AdvancedCandidateScore]:
        """後處理候選衛星列表"""

        if not candidates:
            return candidates

        # 多樣性優化：避免選擇過於相似的候選衛星
        diversified_candidates = self._ensure_diversity(candidates)

        # 場景適應性調整
        scenario_adjusted_candidates = self._apply_scenario_adjustments(
            diversified_candidates, scenario_context
        )

        # 重新排序
        scenario_adjusted_candidates.sort(key=lambda x: x.overall_score, reverse=True)

        return scenario_adjusted_candidates

    def _ensure_diversity(
        self, candidates: List[AdvancedCandidateScore]
    ) -> List[AdvancedCandidateScore]:
        """確保候選衛星的多樣性"""

        if len(candidates) <= 3:
            return candidates

        # 簡化的多樣性算法：確保不同象限的衛星都有代表
        diversified = [candidates[0]]  # 保留最佳候選

        for candidate in candidates[1:]:
            # 檢查是否與已選候選衛星過於相似
            is_similar = False
            for selected in diversified:
                # 比較關鍵指標的相似性
                signal_diff = abs(candidate.signal_score - selected.signal_score)
                elevation_diff = abs(
                    candidate.elevation_score - selected.elevation_score
                )

                if signal_diff < 10 and elevation_diff < 10:
                    is_similar = True
                    break

            if not is_similar:
                diversified.append(candidate)

            # 限制候選數量
            if len(diversified) >= 5:
                break

        return diversified

    def _apply_scenario_adjustments(
        self,
        candidates: List[AdvancedCandidateScore],
        scenario_context: Optional[Dict[str, Any]],
    ) -> List[AdvancedCandidateScore]:
        """應用場景特定的調整"""

        if not scenario_context:
            return candidates

        scenario_type = scenario_context.get("scenario_type", "urban")

        for candidate in candidates:
            adjustment_factor = 1.0

            # 根據場景類型調整評分
            if scenario_type == "urban":
                # 城市場景：更重視信號穩定性
                if candidate.stability_score > 80:
                    adjustment_factor = 1.1
            elif scenario_type == "high_mobility":
                # 高移動性場景：更重視服務持續時間
                if candidate.service_duration_estimate > 120:
                    adjustment_factor = 1.15
            elif scenario_type == "rural":
                # 農村場景：更重視信號強度
                if candidate.signal_score > 85:
                    adjustment_factor = 1.05

            # 應用調整
            candidate.overall_score *= adjustment_factor
            candidate.overall_score = min(candidate.overall_score, 100.0)

        return candidates

    def add_custom_filter(self, filter_rule: FilterRule):
        """添加自定義篩選規則"""
        self.filter_rules.append(filter_rule)
        logger.info(f"添加自定義篩選規則: {filter_rule.criteria.value}")

    def update_scoring_weights(self, new_weights: ScoringWeights):
        """更新評分權重"""
        if new_weights.validate():
            self.scoring_weights = new_weights
            logger.info("評分權重已更新")
        else:
            logger.error("無效的評分權重：總和不等於1")

    def get_scoring_statistics(self) -> Dict[str, Any]:
        """獲取評分統計信息"""

        return {
            "candidates_scored": self.candidates_scored,
            "filtering_efficiency": self.filtering_efficiency,
            "active_filter_rules": len([r for r in self.filter_rules if r.enabled]),
            "total_filter_rules": len(self.filter_rules),
            "scoring_method": self.scoring_method.value,
            "scoring_weights": {
                "signal_quality": self.scoring_weights.signal_quality,
                "load_factor": self.scoring_weights.load_factor,
                "elevation_angle": self.scoring_weights.elevation_angle,
                "distance": self.scoring_weights.distance,
                "prediction_confidence": self.scoring_weights.prediction_confidence,
            },
            "performance_metrics": self.performance_metrics,
        }
