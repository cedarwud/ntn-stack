"""
IEEE INFOCOM 2024 智能回退決策引擎
實現基於機器學習的智能回退策略選擇和優化
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import numpy as np
from collections import defaultdict, deque

from .handover_fault_tolerance_service import (
    HandoverAnomaly,
    HandoverContext,
    FallbackAction,
    AnomalyType,
    AnomalySeverity,
)

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """回退策略類型"""

    ROLLBACK_TO_SOURCE = "ROLLBACK_TO_SOURCE"
    SELECT_ALTERNATIVE_SATELLITE = "SELECT_ALTERNATIVE_SATELLITE"
    DELAY_HANDOVER = "DELAY_HANDOVER"
    ADJUST_POWER_PARAMETERS = "ADJUST_POWER_PARAMETERS"
    FREQUENCY_HOPPING = "FREQUENCY_HOPPING"
    LOAD_BALANCING = "LOAD_BALANCING"
    EMERGENCY_FALLBACK = "EMERGENCY_FALLBACK"


class DecisionOutcome(Enum):
    """決策結果"""

    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"


@dataclass
class FallbackDecisionContext:
    """回退決策上下文"""

    anomaly: HandoverAnomaly
    handover_context: HandoverContext
    available_satellites: List[str]
    network_conditions: Dict[str, Any]
    system_load: float
    historical_success_rate: Dict[str, float]
    time_constraints: float
    retry_count: int


@dataclass
class FallbackOption:
    """回退選項"""

    strategy: FallbackStrategy
    target_satellite: Optional[str]
    estimated_recovery_time: float
    success_probability: float
    resource_cost: float
    risk_level: float
    description: str
    parameters: Dict[str, Any]


@dataclass
class DecisionRecord:
    """決策記錄"""

    decision_id: str
    timestamp: datetime
    context: FallbackDecisionContext
    selected_option: FallbackOption
    outcome: DecisionOutcome
    actual_recovery_time: float
    success_achieved: bool
    lessons_learned: List[str]


@dataclass
class PerformanceMetrics:
    """性能指標"""

    total_decisions: int
    successful_decisions: int
    average_recovery_time: float
    strategy_success_rates: Dict[str, float]
    accuracy_trend: List[float]
    decision_latency: float


class IntelligentFallbackService:
    """
    智能回退決策引擎

    功能：
    1. 基於歷史數據和當前環境智能選擇回退策略
    2. 機器學習驅動的決策優化
    3. 實時學習和模型更新
    4. 多維度評估回退選項
    """

    def __init__(self):
        self.decision_history: List[DecisionRecord] = []
        self.strategy_performance: Dict[FallbackStrategy, Dict] = {}
        self.learning_buffer = deque(maxlen=1000)
        self.decision_tree = self._build_initial_decision_tree()
        self.weight_factors = self._initialize_weight_factors()

        # 策略成功率統計
        for strategy in FallbackStrategy:
            self.strategy_performance[strategy] = {
                "total_attempts": 0,
                "successful_attempts": 0,
                "average_recovery_time": 0.0,
                "failure_reasons": defaultdict(int),
                "context_patterns": [],
            }

    def _initialize_weight_factors(self) -> Dict[str, float]:
        """初始化權重因子"""
        return {
            "success_probability": 0.35,
            "recovery_time": 0.25,
            "resource_cost": 0.15,
            "risk_level": 0.20,
            "historical_performance": 0.05,
        }

    def _build_initial_decision_tree(self) -> Dict:
        """建立初始決策樹"""
        return {
            AnomalyType.TIMEOUT: {
                AnomalySeverity.LOW: [
                    FallbackStrategy.DELAY_HANDOVER,
                    FallbackStrategy.ADJUST_POWER_PARAMETERS,
                ],
                AnomalySeverity.MEDIUM: [
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                    FallbackStrategy.ROLLBACK_TO_SOURCE,
                ],
                AnomalySeverity.HIGH: [
                    FallbackStrategy.ROLLBACK_TO_SOURCE,
                    FallbackStrategy.EMERGENCY_FALLBACK,
                ],
                AnomalySeverity.CRITICAL: [FallbackStrategy.EMERGENCY_FALLBACK],
            },
            AnomalyType.SIGNAL_DEGRADATION: {
                AnomalySeverity.LOW: [
                    FallbackStrategy.ADJUST_POWER_PARAMETERS,
                    FallbackStrategy.DELAY_HANDOVER,
                ],
                AnomalySeverity.MEDIUM: [
                    FallbackStrategy.FREQUENCY_HOPPING,
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                ],
                AnomalySeverity.HIGH: [
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                    FallbackStrategy.ROLLBACK_TO_SOURCE,
                ],
                AnomalySeverity.CRITICAL: [FallbackStrategy.EMERGENCY_FALLBACK],
            },
            AnomalyType.TARGET_UNAVAILABLE: {
                AnomalySeverity.LOW: [FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE],
                AnomalySeverity.MEDIUM: [
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                    FallbackStrategy.LOAD_BALANCING,
                ],
                AnomalySeverity.HIGH: [
                    FallbackStrategy.ROLLBACK_TO_SOURCE,
                    FallbackStrategy.EMERGENCY_FALLBACK,
                ],
                AnomalySeverity.CRITICAL: [FallbackStrategy.EMERGENCY_FALLBACK],
            },
            AnomalyType.INTERFERENCE_DETECTED: {
                AnomalySeverity.LOW: [
                    FallbackStrategy.FREQUENCY_HOPPING,
                    FallbackStrategy.ADJUST_POWER_PARAMETERS,
                ],
                AnomalySeverity.MEDIUM: [
                    FallbackStrategy.FREQUENCY_HOPPING,
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                ],
                AnomalySeverity.HIGH: [
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                    FallbackStrategy.ROLLBACK_TO_SOURCE,
                ],
                AnomalySeverity.CRITICAL: [FallbackStrategy.EMERGENCY_FALLBACK],
            },
            AnomalyType.NETWORK_CONGESTION: {
                AnomalySeverity.LOW: [
                    FallbackStrategy.LOAD_BALANCING,
                    FallbackStrategy.DELAY_HANDOVER,
                ],
                AnomalySeverity.MEDIUM: [
                    FallbackStrategy.LOAD_BALANCING,
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                ],
                AnomalySeverity.HIGH: [
                    FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE,
                    FallbackStrategy.ROLLBACK_TO_SOURCE,
                ],
                AnomalySeverity.CRITICAL: [FallbackStrategy.EMERGENCY_FALLBACK],
            },
        }

    async def make_intelligent_fallback_decision(
        self, decision_context: FallbackDecisionContext
    ) -> FallbackAction:
        """
        智能回退決策主函數
        """
        logger.info(
            f"開始智能回退決策 - 異常類型: {decision_context.anomaly.anomaly_type}"
        )

        # 1. 生成所有可能的回退選項
        fallback_options = await self._generate_fallback_options(decision_context)

        # 2. 評估每個選項
        evaluated_options = await self._evaluate_fallback_options(
            fallback_options, decision_context
        )

        # 3. 選擇最佳策略
        best_option = await self._select_optimal_strategy(
            evaluated_options, decision_context
        )

        # 4. 創建決策記錄
        decision_record = DecisionRecord(
            decision_id=f"decision_{int(time.time())}_{decision_context.anomaly.anomaly_id}",
            timestamp=datetime.utcnow(),
            context=decision_context,
            selected_option=best_option,
            outcome=DecisionOutcome.SUCCESS,  # 將在執行後更新
            actual_recovery_time=0.0,
            success_achieved=False,
            lessons_learned=[],
        )

        self.decision_history.append(decision_record)

        # 5. 轉換為 FallbackAction
        fallback_action = FallbackAction(
            action_id=decision_record.decision_id,
            strategy=best_option.strategy.value,
            target_satellite=best_option.target_satellite,
            estimated_recovery_time=best_option.estimated_recovery_time,
            confidence=best_option.success_probability,
            description=best_option.description,
            priority=self._calculate_priority(best_option, decision_context),
        )

        logger.info(
            f"選擇回退策略: {best_option.strategy.value} - 信心度: {best_option.success_probability:.2f}"
        )

        return fallback_action

    async def _generate_fallback_options(
        self, context: FallbackDecisionContext
    ) -> List[FallbackOption]:
        """生成所有可能的回退選項"""
        options = []

        # 從決策樹獲取推薦策略
        recommended_strategies = self.decision_tree.get(
            context.anomaly.anomaly_type, {}
        ).get(context.anomaly.severity, [])

        for strategy in recommended_strategies:
            option = await self._create_fallback_option(strategy, context)
            if option:
                options.append(option)

        return options

    async def _create_fallback_option(
        self, strategy: FallbackStrategy, context: FallbackDecisionContext
    ) -> Optional[FallbackOption]:
        """創建特定策略的回退選項"""

        if strategy == FallbackStrategy.ROLLBACK_TO_SOURCE:
            return FallbackOption(
                strategy=strategy,
                target_satellite=context.handover_context.source_satellite,
                estimated_recovery_time=2.0 + context.retry_count * 0.5,
                success_probability=0.95 - context.retry_count * 0.1,
                resource_cost=0.3,
                risk_level=0.2,
                description="回滾到源衛星",
                parameters={"rollback_type": "immediate"},
            )

        elif strategy == FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE:
            best_satellite = await self._find_best_alternative_satellite(context)
            if not best_satellite:
                return None

            return FallbackOption(
                strategy=strategy,
                target_satellite=best_satellite,
                estimated_recovery_time=3.0 + context.retry_count * 0.7,
                success_probability=0.85 - context.retry_count * 0.15,
                resource_cost=0.5,
                risk_level=0.4,
                description=f"換手到替代衛星 {best_satellite}",
                parameters={"satellite_id": best_satellite, "preemptive": True},
            )

        elif strategy == FallbackStrategy.DELAY_HANDOVER:
            delay_time = 2.0 + context.anomaly.severity.value * 1.0
            return FallbackOption(
                strategy=strategy,
                target_satellite=context.handover_context.target_satellite,
                estimated_recovery_time=delay_time,
                success_probability=0.7,
                resource_cost=0.1,
                risk_level=0.6,
                description=f"延遲換手 {delay_time} 秒",
                parameters={"delay_seconds": delay_time},
            )

        elif strategy == FallbackStrategy.ADJUST_POWER_PARAMETERS:
            return FallbackOption(
                strategy=strategy,
                target_satellite=context.handover_context.target_satellite,
                estimated_recovery_time=1.5,
                success_probability=0.6,
                resource_cost=0.2,
                risk_level=0.3,
                description="調整功率參數",
                parameters={"power_increase": 1.5, "duration": 10},
            )

        elif strategy == FallbackStrategy.FREQUENCY_HOPPING:
            return FallbackOption(
                strategy=strategy,
                target_satellite=context.handover_context.target_satellite,
                estimated_recovery_time=1.0,
                success_probability=0.75,
                resource_cost=0.4,
                risk_level=0.25,
                description="頻率跳躍",
                parameters={"frequency_band": "backup", "hop_count": 3},
            )

        elif strategy == FallbackStrategy.LOAD_BALANCING:
            return FallbackOption(
                strategy=strategy,
                target_satellite=None,
                estimated_recovery_time=4.0,
                success_probability=0.8,
                resource_cost=0.6,
                risk_level=0.3,
                description="負載均衡重分配",
                parameters={"rebalance_threshold": 0.7},
            )

        elif strategy == FallbackStrategy.EMERGENCY_FALLBACK:
            return FallbackOption(
                strategy=strategy,
                target_satellite=context.handover_context.source_satellite,
                estimated_recovery_time=1.0,
                success_probability=0.99,
                resource_cost=0.8,
                risk_level=0.1,
                description="緊急回退到穩定狀態",
                parameters={"emergency_mode": True, "bypass_checks": True},
            )

        return None

    async def _evaluate_fallback_options(
        self, options: List[FallbackOption], context: FallbackDecisionContext
    ) -> List[FallbackOption]:
        """評估回退選項"""

        for option in options:
            # 基於歷史表現調整成功概率
            historical_performance = self._get_historical_performance(
                option.strategy, context
            )
            option.success_probability *= 0.7 + 0.3 * historical_performance

            # 基於當前系統負載調整回復時間
            load_factor = max(1.0, context.system_load * 2)
            option.estimated_recovery_time *= load_factor

            # 基於重試次數調整風險等級
            retry_penalty = min(0.3, context.retry_count * 0.1)
            option.risk_level += retry_penalty

        return options

    async def _select_optimal_strategy(
        self, options: List[FallbackOption], context: FallbackDecisionContext
    ) -> FallbackOption:
        """選擇最佳策略"""

        if not options:
            # 如果沒有可用選項，創建緊急回退
            return FallbackOption(
                strategy=FallbackStrategy.EMERGENCY_FALLBACK,
                target_satellite=context.handover_context.source_satellite,
                estimated_recovery_time=1.0,
                success_probability=0.99,
                resource_cost=1.0,
                risk_level=0.05,
                description="無可用選項，執行緊急回退",
                parameters={"emergency": True},
            )

        # 多維度評分
        scored_options = []
        for option in options:
            score = self._calculate_option_score(option, context)
            scored_options.append((score, option))

        # 排序並選擇最高分
        scored_options.sort(key=lambda x: x[0], reverse=True)

        return scored_options[0][1]

    def _calculate_option_score(
        self, option: FallbackOption, context: FallbackDecisionContext
    ) -> float:
        """計算選項評分"""

        # 基礎評分組件
        success_score = (
            option.success_probability * self.weight_factors["success_probability"]
        )

        # 回復時間評分（時間越短越好）
        time_score = (
            max(0, (10.0 - option.estimated_recovery_time) / 10.0)
            * self.weight_factors["recovery_time"]
        )

        # 資源成本評分（成本越低越好）
        cost_score = (1.0 - option.resource_cost) * self.weight_factors["resource_cost"]

        # 風險評分（風險越低越好）
        risk_score = (1.0 - option.risk_level) * self.weight_factors["risk_level"]

        # 歷史表現評分
        historical_score = (
            self._get_historical_performance(option.strategy, context)
            * self.weight_factors["historical_performance"]
        )

        total_score = (
            success_score + time_score + cost_score + risk_score + historical_score
        )

        # 時間緊迫性加權
        if context.time_constraints < 3.0:
            # 時間緊迫時偏向快速策略
            if option.estimated_recovery_time < 2.0:
                total_score *= 1.3

        # 重試次數懲罰
        retry_penalty = min(0.5, context.retry_count * 0.1)
        total_score *= 1.0 - retry_penalty

        return total_score

    def _get_historical_performance(
        self, strategy: FallbackStrategy, context: FallbackDecisionContext
    ) -> float:
        """獲取策略歷史表現"""

        strategy_data = self.strategy_performance.get(strategy, {})
        total_attempts = strategy_data.get("total_attempts", 0)

        if total_attempts == 0:
            return 0.5  # 預設中等表現

        successful_attempts = strategy_data.get("successful_attempts", 0)
        return successful_attempts / total_attempts

    async def _find_best_alternative_satellite(
        self, context: FallbackDecisionContext
    ) -> Optional[str]:
        """尋找最佳替代衛星"""

        if not context.available_satellites:
            return None

        # 排除當前的源衛星和目標衛星
        candidates = [
            sat
            for sat in context.available_satellites
            if sat
            not in [
                context.handover_context.source_satellite,
                context.handover_context.target_satellite,
            ]
        ]

        if not candidates:
            return None

        # 基於歷史成功率選擇
        best_satellite = None
        best_score = 0.0

        for satellite in candidates:
            # 模擬衛星評分（實際實現中會查詢真實數據）
            signal_quality = context.handover_context.signal_quality.get("rsrp", -100)
            distance_factor = 1.0 - (abs(hash(satellite)) % 100) / 100.0  # 模擬距離因子
            load_factor = 1.0 - context.network_conditions.get("congestion_level", 0.5)

            score = (signal_quality + 100) / 50.0 * distance_factor * load_factor

            if score > best_score:
                best_score = score
                best_satellite = satellite

        return best_satellite

    def _calculate_priority(
        self, option: FallbackOption, context: FallbackDecisionContext
    ) -> int:
        """計算優先級（1-10，10為最高）"""

        base_priority = 5

        # 基於嚴重程度調整
        severity_bonus = {
            AnomalySeverity.LOW: 0,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.HIGH: 4,
            AnomalySeverity.CRITICAL: 5,
        }.get(context.anomaly.severity, 0)

        # 基於成功概率調整
        success_bonus = int(option.success_probability * 3)

        # 基於時間緊迫性調整
        urgency_bonus = 3 if context.time_constraints < 2.0 else 1

        priority = min(
            10, base_priority + severity_bonus + success_bonus + urgency_bonus
        )
        return priority

    async def record_decision_outcome(
        self,
        decision_id: str,
        outcome: DecisionOutcome,
        actual_recovery_time: float,
        success_achieved: bool,
        lessons: List[str] = None,
    ):
        """記錄決策結果用於學習"""

        # 尋找對應的決策記錄
        decision_record = None
        for record in self.decision_history:
            if record.decision_id == decision_id:
                decision_record = record
                break

        if not decision_record:
            logger.warning(f"未找到決策記錄: {decision_id}")
            return

        # 更新記錄
        decision_record.outcome = outcome
        decision_record.actual_recovery_time = actual_recovery_time
        decision_record.success_achieved = success_achieved
        decision_record.lessons_learned = lessons or []

        # 更新策略統計
        strategy = decision_record.selected_option.strategy
        strategy_stats = self.strategy_performance[strategy]
        strategy_stats["total_attempts"] += 1

        if success_achieved:
            strategy_stats["successful_attempts"] += 1

        # 更新平均回復時間
        current_avg = strategy_stats["average_recovery_time"]
        total_attempts = strategy_stats["total_attempts"]
        strategy_stats["average_recovery_time"] = (
            current_avg * (total_attempts - 1) + actual_recovery_time
        ) / total_attempts

        # 添加到學習緩衝區
        self.learning_buffer.append(
            {
                "context_features": self._extract_context_features(
                    decision_record.context
                ),
                "strategy": strategy.value,
                "outcome": outcome.value,
                "success": success_achieved,
                "recovery_time": actual_recovery_time,
            }
        )

        # 定期更新模型
        if len(self.learning_buffer) >= 50:
            await self._update_decision_model()

        logger.info(
            f"記錄決策結果: {decision_id} - {outcome.value} - 成功: {success_achieved}"
        )

    def _extract_context_features(self, context: FallbackDecisionContext) -> Dict:
        """提取上下文特徵"""
        return {
            "anomaly_type": context.anomaly.anomaly_type.value,
            "severity": context.anomaly.severity.value,
            "system_load": context.system_load,
            "retry_count": context.retry_count,
            "time_constraints": context.time_constraints,
            "available_satellites_count": len(context.available_satellites),
            "network_congestion": context.network_conditions.get("congestion_level", 0),
            "signal_quality": context.handover_context.signal_quality.get("rsrp", -100),
        }

    async def _update_decision_model(self):
        """更新決策模型"""
        logger.info("開始更新決策模型")

        # 分析學習緩衝區中的數據
        success_patterns = defaultdict(list)
        failure_patterns = defaultdict(list)

        for sample in self.learning_buffer:
            if sample["success"]:
                success_patterns[sample["strategy"]].append(sample)
            else:
                failure_patterns[sample["strategy"]].append(sample)

        # 更新權重因子
        await self._update_weight_factors(success_patterns, failure_patterns)

        # 更新決策樹
        await self._update_decision_tree(success_patterns, failure_patterns)

        logger.info("決策模型更新完成")

    async def _update_weight_factors(
        self, success_patterns: Dict, failure_patterns: Dict
    ):
        """更新權重因子"""

        # 分析哪些因子與成功相關性最高
        success_recovery_times = []
        failure_recovery_times = []

        for strategy_samples in success_patterns.values():
            success_recovery_times.extend(
                [s["recovery_time"] for s in strategy_samples]
            )

        for strategy_samples in failure_patterns.values():
            failure_recovery_times.extend(
                [s["recovery_time"] for s in strategy_samples]
            )

        # 如果成功案例的回復時間明顯更短，增加時間權重
        if success_recovery_times and failure_recovery_times:
            avg_success_time = np.mean(success_recovery_times)
            avg_failure_time = np.mean(failure_recovery_times)

            if avg_success_time < avg_failure_time * 0.8:
                self.weight_factors["recovery_time"] = min(
                    0.4, self.weight_factors["recovery_time"] * 1.1
                )
                self.weight_factors["success_probability"] = max(
                    0.2, self.weight_factors["success_probability"] * 0.9
                )

    async def _update_decision_tree(
        self, success_patterns: Dict, failure_patterns: Dict
    ):
        """更新決策樹"""

        # 找出表現最差的策略組合
        for anomaly_type in AnomalyType:
            for severity in AnomalySeverity:
                current_strategies = self.decision_tree.get(anomaly_type, {}).get(
                    severity, []
                )

                # 重新排序策略基於最新表現
                strategy_scores = {}
                for strategy in current_strategies:
                    success_count = len(success_patterns.get(strategy.value, []))
                    failure_count = len(failure_patterns.get(strategy.value, []))
                    total_count = success_count + failure_count

                    if total_count > 0:
                        strategy_scores[strategy] = success_count / total_count
                    else:
                        strategy_scores[strategy] = 0.5  # 預設值

                # 按成功率重新排序
                if strategy_scores:
                    sorted_strategies = sorted(
                        strategy_scores.items(), key=lambda x: x[1], reverse=True
                    )
                    self.decision_tree[anomaly_type][severity] = [
                        s[0] for s in sorted_strategies
                    ]

    def get_performance_metrics(self) -> PerformanceMetrics:
        """獲取性能指標"""

        total_decisions = len(self.decision_history)
        successful_decisions = sum(
            1 for d in self.decision_history if d.success_achieved
        )

        if total_decisions == 0:
            return PerformanceMetrics(
                total_decisions=0,
                successful_decisions=0,
                average_recovery_time=0.0,
                strategy_success_rates={},
                accuracy_trend=[],
                decision_latency=0.0,
            )

        average_recovery_time = (
            np.mean(
                [
                    d.actual_recovery_time
                    for d in self.decision_history
                    if d.actual_recovery_time > 0
                ]
            )
            if self.decision_history
            else 0.0
        )

        # 計算各策略成功率
        strategy_success_rates = {}
        for strategy, stats in self.strategy_performance.items():
            if stats["total_attempts"] > 0:
                success_rate = stats["successful_attempts"] / stats["total_attempts"]
                strategy_success_rates[strategy.value] = success_rate

        # 準確率趨勢（最近10個決策）
        recent_decisions = self.decision_history[-10:]
        accuracy_trend = []
        for i in range(1, len(recent_decisions) + 1):
            recent_batch = recent_decisions[:i]
            accuracy = sum(1 for d in recent_batch if d.success_achieved) / len(
                recent_batch
            )
            accuracy_trend.append(accuracy)

        return PerformanceMetrics(
            total_decisions=total_decisions,
            successful_decisions=successful_decisions,
            average_recovery_time=average_recovery_time,
            strategy_success_rates=strategy_success_rates,
            accuracy_trend=accuracy_trend,
            decision_latency=0.05,  # 模擬決策延遲
        )

    async def get_strategy_recommendations(
        self, anomaly_type: AnomalyType, severity: AnomalySeverity
    ) -> List[Dict[str, Any]]:
        """獲取策略建議"""

        strategies = self.decision_tree.get(anomaly_type, {}).get(severity, [])
        recommendations = []

        for strategy in strategies:
            stats = self.strategy_performance[strategy]
            total_attempts = stats["total_attempts"]

            if total_attempts > 0:
                success_rate = stats["successful_attempts"] / total_attempts
                avg_recovery_time = stats["average_recovery_time"]
            else:
                success_rate = 0.5
                avg_recovery_time = 0.0

            recommendations.append(
                {
                    "strategy": strategy.value,
                    "success_rate": success_rate,
                    "average_recovery_time": avg_recovery_time,
                    "total_attempts": total_attempts,
                    "recommended_scenarios": self._get_recommended_scenarios(strategy),
                }
            )

        return recommendations

    def _get_recommended_scenarios(self, strategy: FallbackStrategy) -> List[str]:
        """獲取推薦使用場景"""

        scenario_map = {
            FallbackStrategy.ROLLBACK_TO_SOURCE: [
                "超時異常",
                "目標衛星故障",
                "緊急情況",
            ],
            FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE: [
                "目標衛星不可用",
                "信號品質不佳",
                "負載均衡",
            ],
            FallbackStrategy.DELAY_HANDOVER: [
                "輕微信號劣化",
                "暫時性干擾",
                "系統負載高",
            ],
            FallbackStrategy.ADJUST_POWER_PARAMETERS: [
                "信號強度不足",
                "干擾抑制",
                "功率優化",
            ],
            FallbackStrategy.FREQUENCY_HOPPING: [
                "頻段干擾",
                "信號阻塞",
                "頻率選擇性衰落",
            ],
            FallbackStrategy.LOAD_BALANCING: ["網路擁塞", "資源不均", "容量限制"],
            FallbackStrategy.EMERGENCY_FALLBACK: ["嚴重故障", "系統崩潰", "安全模式"],
        }

        return scenario_map.get(strategy, [])


# 全局服務實例
intelligent_fallback_service = IntelligentFallbackService()
