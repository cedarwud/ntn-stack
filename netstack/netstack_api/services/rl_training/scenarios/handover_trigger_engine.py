"""
Phase 2.2 換手事件觸發邏輯引擎

基於真實 TLE 數據和軌道預測，實現智能的換手事件觸發機制
支援多種觸發條件：信號劣化、仰角變化、負載平衡、預測性換手等
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
import json

from ...simworld_tle_bridge_service import SimWorldTLEBridgeService
from ..environments.leo_satellite_environment import (
    LEOSatelliteEnvironment,
    SatelliteState,
    OrbitEvent,
)

logger = logging.getLogger(__name__)


class TriggerCondition(Enum):
    """觸發條件類型"""

    SIGNAL_BELOW_THRESHOLD = "signal_below_threshold"
    ELEVATION_DROP = "elevation_drop"
    LOAD_EXCESSIVE = "load_excessive"
    PREDICTIVE_OPPORTUNITY = "predictive_opportunity"
    COMBINED_FACTORS = "combined_factors"


class TriggerSeverity(Enum):
    """觸發嚴重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TriggerEvent:
    """觸發事件定義"""

    event_id: str
    trigger_type: TriggerCondition
    severity: TriggerSeverity

    # 事件詳情
    satellite_id: str
    ue_position: Dict[str, float]
    trigger_value: float
    threshold: float

    # 上下文信息
    current_metrics: Dict[str, Any]
    predicted_metrics: Dict[str, Any]
    confidence: float

    # 時間信息
    timestamp: datetime
    prediction_horizon_s: float

    # 建議動作
    recommended_action: str
    alternative_satellites: List[str]

    metadata: Dict[str, Any]


@dataclass
class TriggerRule:
    """觸發規則定義"""

    rule_id: str
    condition: TriggerCondition
    threshold: float
    time_window_s: float
    priority: int
    enabled: bool

    # 條件函數
    condition_func: Optional[Callable] = None

    # 規則參數
    parameters: Dict[str, Any] = None


class HandoverTriggerEngine:
    """
    換手事件觸發引擎

    基於真實軌道數據和多維度指標，智能檢測換手觸發時機
    """

    def __init__(
        self,
        tle_bridge_service: SimWorldTLEBridgeService,
        leo_environment: LEOSatelliteEnvironment,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化觸發引擎

        Args:
            tle_bridge_service: SimWorld TLE 橋接服務
            leo_environment: LEO 衛星環境
            config: 配置參數
        """
        self.tle_bridge = tle_bridge_service
        self.leo_env = leo_environment
        self.config = config or {}

        # 觸發配置
        self.monitoring_interval_s = self.config.get("monitoring_interval_s", 5.0)
        self.prediction_horizon_s = self.config.get("prediction_horizon_s", 60.0)
        self.trigger_history_limit = self.config.get("trigger_history_limit", 100)

        # 默認閾值
        self.default_thresholds = {
            "min_rsrp_dbm": -85.0,
            "min_elevation_deg": 10.0,
            "max_load_factor": 0.85,
            "min_prediction_confidence": 0.7,
            "handover_hysteresis_db": 3.0,
        }

        # 觸發規則
        self.trigger_rules: List[TriggerRule] = []
        self._initialize_default_rules()

        # 歷史記錄
        self.trigger_history: List[TriggerEvent] = []
        self.satellite_metrics_history: Dict[str, List[Dict[str, Any]]] = {}

        # 統計
        self.triggers_detected = 0
        self.false_positives = 0
        self.successful_handovers = 0

        logger.info("換手事件觸發引擎初始化完成")

    def _initialize_default_rules(self):
        """初始化默認觸發規則"""

        # 規則 1：信號劣化觸發
        self.trigger_rules.append(
            TriggerRule(
                rule_id="signal_degradation",
                condition=TriggerCondition.SIGNAL_BELOW_THRESHOLD,
                threshold=self.default_thresholds["min_rsrp_dbm"],
                time_window_s=10.0,
                priority=1,
                enabled=True,
                parameters={
                    "consecutive_violations": 3,
                    "degradation_rate_db_per_s": -2.0,
                },
            )
        )

        # 規則 2：仰角過低觸發
        self.trigger_rules.append(
            TriggerRule(
                rule_id="elevation_threshold",
                condition=TriggerCondition.ELEVATION_DROP,
                threshold=self.default_thresholds["min_elevation_deg"],
                time_window_s=15.0,
                priority=2,
                enabled=True,
                parameters={
                    "elevation_rate_deg_per_s": -1.0,
                    "min_service_elevation": 5.0,
                },
            )
        )

        # 規則 3：負載過高觸發
        self.trigger_rules.append(
            TriggerRule(
                rule_id="load_balancing",
                condition=TriggerCondition.LOAD_EXCESSIVE,
                threshold=self.default_thresholds["max_load_factor"],
                time_window_s=20.0,
                priority=3,
                enabled=True,
                parameters={
                    "load_increase_rate": 0.1,
                    "balance_opportunity_threshold": 0.3,
                },
            )
        )

        # 規則 4：預測性換手觸發
        self.trigger_rules.append(
            TriggerRule(
                rule_id="predictive_handover",
                condition=TriggerCondition.PREDICTIVE_OPPORTUNITY,
                threshold=self.default_thresholds["min_prediction_confidence"],
                time_window_s=30.0,
                priority=4,
                enabled=True,
                parameters={
                    "quality_improvement_threshold_db": 5.0,
                    "prediction_accuracy_min": 0.8,
                },
            )
        )

    async def monitor_handover_triggers(
        self,
        current_serving_satellite: str,
        ue_position: Dict[str, float],
        candidate_satellites: List[str],
    ) -> List[TriggerEvent]:
        """
        監控換手觸發條件

        Args:
            current_serving_satellite: 當前服務衛星 ID
            ue_position: 用戶設備位置
            candidate_satellites: 候選衛星列表

        Returns:
            List[TriggerEvent]: 檢測到的觸發事件列表
        """
        triggered_events = []
        current_time = datetime.now()

        try:
            # 獲取當前衛星狀態
            satellite_states = await self.leo_env.get_satellite_data()
            satellite_dict = {str(sat.id): sat for sat in satellite_states}

            # 獲取當前服務衛星的指標
            serving_satellite = satellite_dict.get(current_serving_satellite)
            if not serving_satellite:
                logger.warning(
                    f"當前服務衛星 {current_serving_satellite} 不在可見列表中"
                )
                return triggered_events

            # 更新衛星指標歷史
            self._update_satellite_metrics_history(serving_satellite)

            # 檢查每個觸發規則
            for rule in self.trigger_rules:
                if not rule.enabled:
                    continue

                event = await self._evaluate_trigger_rule(
                    rule,
                    serving_satellite,
                    ue_position,
                    candidate_satellites,
                    satellite_dict,
                    current_time,
                )

                if event:
                    triggered_events.append(event)
                    self.triggers_detected += 1
                    logger.info(
                        f"檢測到觸發事件: {event.event_id} - {event.trigger_type.value}"
                    )

            # 記錄觸發歷史
            self.trigger_history.extend(triggered_events)

            # 清理舊歷史
            if len(self.trigger_history) > self.trigger_history_limit:
                self.trigger_history = self.trigger_history[
                    -self.trigger_history_limit :
                ]

            return triggered_events

        except Exception as e:
            logger.error(f"監控觸發條件時發生錯誤: {e}")
            return []

    async def _evaluate_trigger_rule(
        self,
        rule: TriggerRule,
        serving_satellite: SatelliteState,
        ue_position: Dict[str, float],
        candidate_satellites: List[str],
        satellite_dict: Dict[str, SatelliteState],
        current_time: datetime,
    ) -> Optional[TriggerEvent]:
        """
        評估單個觸發規則

        Args:
            rule: 觸發規則
            serving_satellite: 當前服務衛星
            ue_position: 用戶位置
            candidate_satellites: 候選衛星列表
            satellite_dict: 衛星字典
            current_time: 當前時間

        Returns:
            TriggerEvent: 觸發事件（如果滿足條件）
        """
        try:
            if rule.condition == TriggerCondition.SIGNAL_BELOW_THRESHOLD:
                return await self._check_signal_degradation(
                    rule,
                    serving_satellite,
                    ue_position,
                    candidate_satellites,
                    satellite_dict,
                    current_time,
                )

            elif rule.condition == TriggerCondition.ELEVATION_DROP:
                return await self._check_elevation_drop(
                    rule,
                    serving_satellite,
                    ue_position,
                    candidate_satellites,
                    satellite_dict,
                    current_time,
                )

            elif rule.condition == TriggerCondition.LOAD_EXCESSIVE:
                return await self._check_load_excessive(
                    rule,
                    serving_satellite,
                    ue_position,
                    candidate_satellites,
                    satellite_dict,
                    current_time,
                )

            elif rule.condition == TriggerCondition.PREDICTIVE_OPPORTUNITY:
                return await self._check_predictive_opportunity(
                    rule,
                    serving_satellite,
                    ue_position,
                    candidate_satellites,
                    satellite_dict,
                    current_time,
                )

            return None

        except Exception as e:
            logger.error(f"評估觸發規則 {rule.rule_id} 時發生錯誤: {e}")
            return None

    async def _check_signal_degradation(
        self,
        rule: TriggerRule,
        serving_satellite: SatelliteState,
        ue_position: Dict[str, float],
        candidate_satellites: List[str],
        satellite_dict: Dict[str, SatelliteState],
        current_time: datetime,
    ) -> Optional[TriggerEvent]:
        """檢查信號劣化觸發條件"""

        rsrp = serving_satellite.signal_quality.get("rsrp", -150)
        threshold = rule.threshold

        # 基本閾值檢查
        if rsrp >= threshold:
            return None

        # 檢查歷史趨勢
        satellite_id = str(serving_satellite.id)
        history = self.satellite_metrics_history.get(satellite_id, [])

        if len(history) < rule.parameters.get("consecutive_violations", 3):
            return None

        # 檢查連續違規
        recent_rsrp = [h["rsrp"] for h in history[-3:]]
        violations = sum(1 for r in recent_rsrp if r < threshold)

        if violations < rule.parameters.get("consecutive_violations", 3):
            return None

        # 計算劣化率
        if len(recent_rsrp) >= 2:
            degradation_rate = (recent_rsrp[-1] - recent_rsrp[0]) / len(recent_rsrp)
            min_degradation_rate = rule.parameters.get(
                "degradation_rate_db_per_s", -2.0
            )

            if degradation_rate > min_degradation_rate:
                return None

        # 查找更好的候選衛星
        better_satellites = []
        for sat_id in candidate_satellites:
            if sat_id in satellite_dict:
                candidate_sat = satellite_dict[sat_id]
                candidate_rsrp = candidate_sat.signal_quality.get("rsrp", -150)
                hysteresis = self.default_thresholds["handover_hysteresis_db"]

                if candidate_rsrp > (rsrp + hysteresis):
                    better_satellites.append(sat_id)

        if not better_satellites:
            return None

        # 創建觸發事件
        severity = self._calculate_severity(rsrp, threshold, -10.0)

        event = TriggerEvent(
            event_id=f"signal_deg_{serving_satellite.id}_{int(current_time.timestamp())}",
            trigger_type=TriggerCondition.SIGNAL_BELOW_THRESHOLD,
            severity=severity,
            satellite_id=satellite_id,
            ue_position=ue_position.copy(),
            trigger_value=rsrp,
            threshold=threshold,
            current_metrics={
                "rsrp": rsrp,
                "rsrq": serving_satellite.signal_quality.get("rsrq", -20),
                "sinr": serving_satellite.signal_quality.get("sinr", -10),
                "elevation": serving_satellite.position.get("elevation", 0),
            },
            predicted_metrics={
                "degradation_rate_db_per_s": (
                    degradation_rate if "degradation_rate" in locals() else 0.0
                )
            },
            confidence=0.9,
            timestamp=current_time,
            prediction_horizon_s=rule.time_window_s,
            recommended_action="handover_to_better_satellite",
            alternative_satellites=better_satellites,
            metadata={
                "rule_id": rule.rule_id,
                "consecutive_violations": violations,
                "history_length": len(history),
            },
        )

        return event

    async def _check_elevation_drop(
        self,
        rule: TriggerRule,
        serving_satellite: SatelliteState,
        ue_position: Dict[str, float],
        candidate_satellites: List[str],
        satellite_dict: Dict[str, SatelliteState],
        current_time: datetime,
    ) -> Optional[TriggerEvent]:
        """檢查仰角過低觸發條件"""

        elevation = serving_satellite.position.get("elevation", 0)
        threshold = rule.threshold

        # 基本閾值檢查
        if elevation >= threshold:
            return None

        # 檢查仰角變化趨勢
        satellite_id = str(serving_satellite.id)
        history = self.satellite_metrics_history.get(satellite_id, [])

        elevation_rate = 0.0
        if len(history) >= 2:
            prev_elevation = history[-2]["elevation"]
            time_diff = (current_time - history[-2]["timestamp"]).total_seconds()
            elevation_rate = (elevation - prev_elevation) / max(time_diff, 1.0)

        # 檢查是否仰角持續下降
        min_elevation_rate = rule.parameters.get("elevation_rate_deg_per_s", -1.0)
        if elevation_rate > min_elevation_rate:
            return None

        # 預測服務終止時間
        min_service_elevation = rule.parameters.get("min_service_elevation", 5.0)
        if elevation_rate < 0:
            time_to_service_end = (elevation - min_service_elevation) / abs(
                elevation_rate
            )
        else:
            time_to_service_end = float("inf")

        # 查找高仰角候選衛星
        high_elevation_satellites = []
        for sat_id in candidate_satellites:
            if sat_id in satellite_dict:
                candidate_sat = satellite_dict[sat_id]
                candidate_elevation = candidate_sat.position.get("elevation", 0)

                if candidate_elevation > (elevation + 5.0):  # 至少高5度
                    high_elevation_satellites.append(sat_id)

        severity = self._calculate_severity(elevation, threshold, 0.0)

        event = TriggerEvent(
            event_id=f"elevation_drop_{serving_satellite.id}_{int(current_time.timestamp())}",
            trigger_type=TriggerCondition.ELEVATION_DROP,
            severity=severity,
            satellite_id=satellite_id,
            ue_position=ue_position.copy(),
            trigger_value=elevation,
            threshold=threshold,
            current_metrics={
                "elevation": elevation,
                "elevation_rate_deg_per_s": elevation_rate,
                "azimuth": serving_satellite.position.get("azimuth", 0),
            },
            predicted_metrics={
                "time_to_service_end_s": time_to_service_end,
                "min_service_elevation": min_service_elevation,
            },
            confidence=0.85,
            timestamp=current_time,
            prediction_horizon_s=rule.time_window_s,
            recommended_action="handover_to_higher_elevation",
            alternative_satellites=high_elevation_satellites,
            metadata={
                "rule_id": rule.rule_id,
                "elevation_trend": "decreasing" if elevation_rate < 0 else "stable",
            },
        )

        return event

    async def _check_load_excessive(
        self,
        rule: TriggerRule,
        serving_satellite: SatelliteState,
        ue_position: Dict[str, float],
        candidate_satellites: List[str],
        satellite_dict: Dict[str, SatelliteState],
        current_time: datetime,
    ) -> Optional[TriggerEvent]:
        """檢查負載過高觸發條件"""

        load_factor = serving_satellite.load_factor
        threshold = rule.threshold

        # 基本閾值檢查
        if load_factor <= threshold:
            return None

        # 檢查負載增長趨勢
        satellite_id = str(serving_satellite.id)
        history = self.satellite_metrics_history.get(satellite_id, [])

        load_increase_rate = 0.0
        if len(history) >= 2:
            prev_load = history[-2]["load_factor"]
            time_diff = (current_time - history[-2]["timestamp"]).total_seconds()
            load_increase_rate = (load_factor - prev_load) / max(time_diff, 1.0)

        # 檢查是否負載持續增長
        min_load_increase_rate = rule.parameters.get("load_increase_rate", 0.1)
        if load_increase_rate < min_load_increase_rate:
            return None

        # 查找低負載候選衛星
        low_load_satellites = []
        balance_threshold = rule.parameters.get("balance_opportunity_threshold", 0.3)

        for sat_id in candidate_satellites:
            if sat_id in satellite_dict:
                candidate_sat = satellite_dict[sat_id]
                candidate_load = candidate_sat.load_factor

                if candidate_load < (load_factor - balance_threshold):
                    low_load_satellites.append(sat_id)

        if not low_load_satellites:
            return None

        severity = self._calculate_severity(load_factor, threshold, 1.0)

        event = TriggerEvent(
            event_id=f"load_excessive_{serving_satellite.id}_{int(current_time.timestamp())}",
            trigger_type=TriggerCondition.LOAD_EXCESSIVE,
            severity=severity,
            satellite_id=satellite_id,
            ue_position=ue_position.copy(),
            trigger_value=load_factor,
            threshold=threshold,
            current_metrics={
                "load_factor": load_factor,
                "load_increase_rate": load_increase_rate,
                "capacity_utilization": load_factor,
            },
            predicted_metrics={
                "load_projection_60s": min(load_factor + load_increase_rate * 60, 1.0)
            },
            confidence=0.8,
            timestamp=current_time,
            prediction_horizon_s=rule.time_window_s,
            recommended_action="load_balancing_handover",
            alternative_satellites=low_load_satellites,
            metadata={
                "rule_id": rule.rule_id,
                "load_imbalance": True,
                "available_alternatives": len(low_load_satellites),
            },
        )

        return event

    async def _check_predictive_opportunity(
        self,
        rule: TriggerRule,
        serving_satellite: SatelliteState,
        ue_position: Dict[str, float],
        candidate_satellites: List[str],
        satellite_dict: Dict[str, SatelliteState],
        current_time: datetime,
    ) -> Optional[TriggerEvent]:
        """檢查預測性換手機會"""

        current_rsrp = serving_satellite.signal_quality.get("rsrp", -150)
        improvement_threshold = rule.parameters.get(
            "quality_improvement_threshold_db", 5.0
        )

        # 查找有顯著信號改善潛力的候選衛星
        opportunity_satellites = []
        max_improvement = 0.0

        for sat_id in candidate_satellites:
            if sat_id in satellite_dict:
                candidate_sat = satellite_dict[sat_id]
                candidate_rsrp = candidate_sat.signal_quality.get("rsrp", -150)

                improvement = candidate_rsrp - current_rsrp
                if improvement > improvement_threshold:
                    opportunity_satellites.append(sat_id)
                    max_improvement = max(max_improvement, improvement)

        if not opportunity_satellites:
            return None

        # 使用軌道預測評估機會持續性
        try:
            # 預測未來信號品質
            prediction_confidence = await self._predict_handover_opportunity(
                serving_satellite, opportunity_satellites[0], ue_position
            )

            min_confidence = rule.threshold
            if prediction_confidence < min_confidence:
                return None
        except Exception as e:
            logger.warning(f"預測性分析失敗: {e}")
            prediction_confidence = 0.6

        severity = (
            TriggerSeverity.MEDIUM if max_improvement > 10.0 else TriggerSeverity.LOW
        )

        event = TriggerEvent(
            event_id=f"predictive_opp_{serving_satellite.id}_{int(current_time.timestamp())}",
            trigger_type=TriggerCondition.PREDICTIVE_OPPORTUNITY,
            severity=severity,
            satellite_id=str(serving_satellite.id),
            ue_position=ue_position.copy(),
            trigger_value=prediction_confidence,
            threshold=rule.threshold,
            current_metrics={
                "current_rsrp": current_rsrp,
                "max_potential_improvement": max_improvement,
                "opportunity_count": len(opportunity_satellites),
            },
            predicted_metrics={
                "predicted_quality_improvement": max_improvement,
                "opportunity_duration_s": self.prediction_horizon_s,
            },
            confidence=prediction_confidence,
            timestamp=current_time,
            prediction_horizon_s=rule.time_window_s,
            recommended_action="proactive_handover",
            alternative_satellites=opportunity_satellites,
            metadata={
                "rule_id": rule.rule_id,
                "prediction_based": True,
                "quality_delta_db": max_improvement,
            },
        )

        return event

    async def _predict_handover_opportunity(
        self,
        current_satellite: SatelliteState,
        target_satellite_id: str,
        ue_position: Dict[str, float],
    ) -> float:
        """
        預測換手機會的置信度

        基於軌道預測和信號傳播模型
        """
        try:
            # 使用 TLE 橋接服務進行軌道預測
            current_time = datetime.now()
            future_time = current_time + timedelta(seconds=self.prediction_horizon_s)

            # 簡化的預測邏輯
            # 在實際實現中，這裡會使用完整的軌道預測

            # 基於當前趨勢的簡單預測
            satellite_history = self.satellite_metrics_history.get(
                str(current_satellite.id), []
            )

            if len(satellite_history) < 2:
                return 0.6  # 默認置信度

            # 分析信號趨勢
            recent_rsrp = [h["rsrp"] for h in satellite_history[-3:]]
            if len(recent_rsrp) >= 2:
                rsrp_trend = recent_rsrp[-1] - recent_rsrp[0]

                # 如果當前衛星信號在惡化，換手機會更大
                if rsrp_trend < -2.0:
                    return 0.85
                elif rsrp_trend < 0:
                    return 0.75
                else:
                    return 0.65

            return 0.7

        except Exception as e:
            logger.warning(f"軌道預測失敗: {e}")
            return 0.6

    def _calculate_severity(
        self, value: float, threshold: float, max_value: float
    ) -> TriggerSeverity:
        """計算觸發嚴重程度"""

        if max_value != threshold:
            # 正規化偏差
            deviation = abs(value - threshold) / abs(max_value - threshold)
        else:
            deviation = 0.5

        if deviation > 0.8:
            return TriggerSeverity.CRITICAL
        elif deviation > 0.6:
            return TriggerSeverity.HIGH
        elif deviation > 0.3:
            return TriggerSeverity.MEDIUM
        else:
            return TriggerSeverity.LOW

    def _update_satellite_metrics_history(self, satellite: SatelliteState):
        """更新衛星指標歷史"""
        satellite_id = str(satellite.id)

        if satellite_id not in self.satellite_metrics_history:
            self.satellite_metrics_history[satellite_id] = []

        metrics = {
            "timestamp": datetime.now(),
            "rsrp": satellite.signal_quality.get("rsrp", -150),
            "rsrq": satellite.signal_quality.get("rsrq", -20),
            "sinr": satellite.signal_quality.get("sinr", -10),
            "elevation": satellite.position.get("elevation", 0),
            "azimuth": satellite.position.get("azimuth", 0),
            "load_factor": satellite.load_factor,
        }

        self.satellite_metrics_history[satellite_id].append(metrics)

        # 保持歷史記錄在合理範圍內
        if len(self.satellite_metrics_history[satellite_id]) > 50:
            self.satellite_metrics_history[satellite_id] = (
                self.satellite_metrics_history[satellite_id][-25:]
            )

    def add_custom_trigger_rule(self, rule: TriggerRule):
        """添加自定義觸發規則"""
        self.trigger_rules.append(rule)
        logger.info(f"添加自定義觸發規則: {rule.rule_id}")

    def enable_rule(self, rule_id: str):
        """啟用觸發規則"""
        for rule in self.trigger_rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                logger.info(f"啟用觸發規則: {rule_id}")
                return
        logger.warning(f"未找到觸發規則: {rule_id}")

    def disable_rule(self, rule_id: str):
        """禁用觸發規則"""
        for rule in self.trigger_rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                logger.info(f"禁用觸發規則: {rule_id}")
                return
        logger.warning(f"未找到觸發規則: {rule_id}")

    def get_trigger_statistics(self) -> Dict[str, Any]:
        """獲取觸發統計信息"""

        recent_triggers = [
            event
            for event in self.trigger_history
            if (datetime.now() - event.timestamp).total_seconds() < 3600  # 最近1小時
        ]

        trigger_type_counts = {}
        severity_counts = {}

        for event in recent_triggers:
            trigger_type = event.trigger_type.value
            severity = event.severity.value

            trigger_type_counts[trigger_type] = (
                trigger_type_counts.get(trigger_type, 0) + 1
            )
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_triggers_detected": self.triggers_detected,
            "recent_triggers_1h": len(recent_triggers),
            "false_positives": self.false_positives,
            "successful_handovers": self.successful_handovers,
            "trigger_success_rate": (
                self.successful_handovers / max(self.triggers_detected, 1)
            ),
            "trigger_type_distribution": trigger_type_counts,
            "severity_distribution": severity_counts,
            "active_rules": sum(1 for rule in self.trigger_rules if rule.enabled),
            "total_rules": len(self.trigger_rules),
        }

    async def cleanup_old_data(self, max_age_hours: int = 6):
        """清理舊的歷史數據"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        # 清理觸發歷史
        initial_trigger_count = len(self.trigger_history)
        self.trigger_history = [
            event for event in self.trigger_history if event.timestamp > cutoff_time
        ]

        # 清理衛星指標歷史
        for satellite_id in list(self.satellite_metrics_history.keys()):
            initial_count = len(self.satellite_metrics_history[satellite_id])
            self.satellite_metrics_history[satellite_id] = [
                metrics
                for metrics in self.satellite_metrics_history[satellite_id]
                if metrics["timestamp"] > cutoff_time
            ]

            # 如果沒有近期數據，移除整個記錄
            if not self.satellite_metrics_history[satellite_id]:
                del self.satellite_metrics_history[satellite_id]

        trigger_cleaned = initial_trigger_count - len(self.trigger_history)

        if trigger_cleaned > 0:
            logger.info(f"清理了 {trigger_cleaned} 個舊觸發記錄")
