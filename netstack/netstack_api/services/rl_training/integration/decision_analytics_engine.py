"""
Phase 2.3 決策分析引擎

實現 Algorithm Explainability 和決策過程詳細記錄：
- 決策路徑追蹤和分析
- 算法可解釋性數據生成
- 決策因子重要性分析
- 性能指標詳細記錄
- 決策品質評估
"""

import asyncio
import logging
import json
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

from .rl_algorithm_integrator import AlgorithmDecision, AlgorithmType
from .real_environment_bridge import (
    EnvironmentObservation,
    EnvironmentAction,
    EnvironmentReward,
)

logger = logging.getLogger(__name__)


class DecisionConfidence(Enum):
    """決策置信度級別"""

    VERY_LOW = "very_low"  # < 0.3
    LOW = "low"  # 0.3 - 0.5
    MEDIUM = "medium"  # 0.5 - 0.7
    HIGH = "high"  # 0.7 - 0.85
    VERY_HIGH = "very_high"  # > 0.85


class DecisionQuality(Enum):
    """決策品質評估"""

    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class DecisionFactor:
    """決策因子"""

    factor_name: str
    value: float
    weight: float
    influence: float  # 對最終決策的影響 (-1 到 1)
    description: str
    confidence: float


@dataclass
class AlgorithmExplanation:
    """算法解釋"""

    algorithm_type: AlgorithmType
    decision_reasoning: str
    key_factors: List[DecisionFactor]
    alternative_actions: List[Dict[str, Any]]
    confidence_breakdown: Dict[str, float]
    uncertainty_sources: List[str]
    model_attention: Optional[Dict[str, float]] = None  # 注意力權重（適用於神經網路）


@dataclass
class DecisionRecord:
    """完整的決策記錄"""

    # 基本資訊
    decision_id: str
    timestamp: datetime
    episode_id: str
    step_number: int

    # 輸入資訊
    observation: EnvironmentObservation
    algorithm_decision: AlgorithmDecision
    environment_action: EnvironmentAction

    # 結果資訊
    reward: Optional[EnvironmentReward]
    next_observation: Optional[EnvironmentObservation]

    # 分析資訊
    explanation: AlgorithmExplanation
    decision_confidence: DecisionConfidence
    decision_quality: Optional[DecisionQuality]

    # 性能指標
    decision_time_ms: float
    execution_time_ms: float
    success: bool

    # 上下文資訊
    scenario_context: Dict[str, Any]
    environmental_factors: Dict[str, Any]

    # 元數據
    metadata: Dict[str, Any]


@dataclass
class EpisodeAnalytics:
    """Episode 級別的分析"""

    episode_id: str
    start_time: datetime
    end_time: Optional[datetime]
    algorithm_type: AlgorithmType
    scenario_type: str

    # 決策統計
    total_decisions: int
    successful_decisions: int
    average_confidence: float
    decision_quality_distribution: Dict[DecisionQuality, int]

    # 性能統計
    total_reward: float
    average_reward_per_step: float
    handover_count: int
    successful_handover_rate: float
    average_decision_time_ms: float

    # 因子分析
    most_influential_factors: List[str]
    factor_importance_scores: Dict[str, float]
    uncertainty_analysis: Dict[str, float]

    # 學習曲線
    reward_progression: List[float]
    confidence_progression: List[float]

    # 錯誤分析
    common_errors: List[Dict[str, Any]]
    improvement_suggestions: List[str]


class DecisionAnalyticsEngine:
    """決策分析引擎"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化決策分析引擎

        Args:
            config: 分析引擎配置
        """
        self.config = config

        # 分析配置
        self.enable_detailed_logging = config.get("enable_detailed_logging", True)
        self.enable_explainability = config.get("enable_explainability", True)
        self.max_records_per_episode = config.get("max_records_per_episode", 10000)
        self.confidence_thresholds = config.get(
            "confidence_thresholds",
            {"very_low": 0.3, "low": 0.5, "medium": 0.7, "high": 0.85},
        )

        # 存儲
        self.decision_records: Dict[str, List[DecisionRecord]] = (
            {}
        )  # episode_id -> records
        self.episode_analytics: Dict[str, EpisodeAnalytics] = {}
        self.current_episode_id: Optional[str] = None

        # 統計
        self.total_decisions_analyzed = 0
        self.total_episodes_analyzed = 0

        logger.info("決策分析引擎初始化完成")

    def start_episode(
        self, episode_id: str, algorithm_type: AlgorithmType, scenario_type: str
    ) -> bool:
        """開始新的 episode 分析"""
        try:
            self.current_episode_id = episode_id
            self.decision_records[episode_id] = []

            # 初始化 episode 分析
            self.episode_analytics[episode_id] = EpisodeAnalytics(
                episode_id=episode_id,
                start_time=datetime.now(),
                end_time=None,
                algorithm_type=algorithm_type,
                scenario_type=scenario_type,
                total_decisions=0,
                successful_decisions=0,
                average_confidence=0.0,
                decision_quality_distribution={q: 0 for q in DecisionQuality},
                total_reward=0.0,
                average_reward_per_step=0.0,
                handover_count=0,
                successful_handover_rate=0.0,
                average_decision_time_ms=0.0,
                most_influential_factors=[],
                factor_importance_scores={},
                uncertainty_analysis={},
                reward_progression=[],
                confidence_progression=[],
                common_errors=[],
                improvement_suggestions=[],
            )

            logger.info(
                f"開始 episode 分析: {episode_id}, 算法: {algorithm_type.value}, 場景: {scenario_type}"
            )
            return True

        except Exception as e:
            logger.error(f"開始 episode 分析失敗: {e}")
            return False

    async def analyze_decision(
        self,
        observation: EnvironmentObservation,
        algorithm_decision: AlgorithmDecision,
        environment_action: EnvironmentAction,
        scenario_context: Dict[str, Any],
    ) -> DecisionRecord:
        """
        分析單個決策

        Args:
            observation: 環境觀測
            algorithm_decision: 算法決策
            environment_action: 環境動作
            scenario_context: 場景上下文

        Returns:
            DecisionRecord: 決策記錄
        """
        try:
            if not self.current_episode_id:
                raise ValueError("必須先開始 episode")

            # 生成決策 ID
            decision_id = str(uuid.uuid4())

            # 生成算法解釋
            explanation = await self._generate_algorithm_explanation(
                observation, algorithm_decision, environment_action
            )

            # 評估決策置信度
            confidence_level = self._evaluate_decision_confidence(
                algorithm_decision.confidence
            )

            # 構建決策記錄
            record = DecisionRecord(
                decision_id=decision_id,
                timestamp=datetime.now(),
                episode_id=self.current_episode_id,
                step_number=observation.time_step,
                observation=observation,
                algorithm_decision=algorithm_decision,
                environment_action=environment_action,
                reward=None,  # 將在 update_decision_result 中更新
                next_observation=None,
                explanation=explanation,
                decision_confidence=confidence_level,
                decision_quality=None,  # 將在獲得結果後評估
                decision_time_ms=algorithm_decision.decision_time_ms,
                execution_time_ms=0.0,  # 將在後續更新
                success=False,  # 將在後續更新
                scenario_context=scenario_context,
                environmental_factors=self._extract_environmental_factors(observation),
                metadata=algorithm_decision.metadata or {},
            )

            # 存儲記錄
            self.decision_records[self.current_episode_id].append(record)
            self.total_decisions_analyzed += 1

            # 限制記錄數量
            if (
                len(self.decision_records[self.current_episode_id])
                > self.max_records_per_episode
            ):
                self.decision_records[self.current_episode_id] = self.decision_records[
                    self.current_episode_id
                ][-self.max_records_per_episode :]

            logger.debug(f"決策分析完成: {decision_id}")
            return record

        except Exception as e:
            logger.error(f"決策分析失敗: {e}")
            raise

    async def update_decision_result(
        self,
        decision_id: str,
        reward: EnvironmentReward,
        next_observation: EnvironmentObservation,
        execution_time_ms: float,
    ) -> bool:
        """
        更新決策結果

        Args:
            decision_id: 決策 ID
            reward: 獎勵
            next_observation: 下一個觀測
            execution_time_ms: 執行時間

        Returns:
            bool: 更新是否成功
        """
        try:
            if not self.current_episode_id:
                return False

            # 找到對應的決策記錄
            records = self.decision_records[self.current_episode_id]
            record = next((r for r in records if r.decision_id == decision_id), None)

            if not record:
                logger.warning(f"未找到決策記錄: {decision_id}")
                return False

            # 更新結果
            record.reward = reward
            record.next_observation = next_observation
            record.execution_time_ms = execution_time_ms
            record.success = reward.total_reward > 0

            # 評估決策品質
            record.decision_quality = self._evaluate_decision_quality(record, reward)

            # 更新 episode 統計
            await self._update_episode_statistics(record)

            logger.debug(f"決策結果更新完成: {decision_id}")
            return True

        except Exception as e:
            logger.error(f"更新決策結果失敗: {e}")
            return False

    async def finalize_episode(self) -> Optional[EpisodeAnalytics]:
        """完成 episode 分析"""
        try:
            if not self.current_episode_id:
                return None

            episode_id = self.current_episode_id
            analytics = self.episode_analytics[episode_id]

            # 更新結束時間
            analytics.end_time = datetime.now()

            # 執行深度分析
            await self._perform_deep_analysis(episode_id)

            # 生成改進建議
            analytics.improvement_suggestions = self._generate_improvement_suggestions(
                episode_id
            )

            self.total_episodes_analyzed += 1
            self.current_episode_id = None

            logger.info(
                f"Episode 分析完成: {episode_id}, 總決策數: {analytics.total_decisions}"
            )
            return analytics

        except Exception as e:
            logger.error(f"完成 episode 分析失敗: {e}")
            return None

    async def _generate_algorithm_explanation(
        self,
        observation: EnvironmentObservation,
        algorithm_decision: AlgorithmDecision,
        environment_action: EnvironmentAction,
    ) -> AlgorithmExplanation:
        """生成算法解釋"""

        # 提取關鍵決策因子
        key_factors = []

        # 信號品質因子
        rsrp = observation.serving_satellite_signal.get("rsrp", -100.0)
        rsrp_factor = DecisionFactor(
            factor_name="signal_rsrp",
            value=rsrp,
            weight=0.3,
            influence=(rsrp + 100) / 40,  # 標準化 [-100, -60] -> [0, 1]
            description=f"當前信號強度 RSRP: {rsrp:.1f} dBm",
            confidence=0.9,
        )
        key_factors.append(rsrp_factor)

        # 候選衛星數量因子
        candidate_count = len(observation.candidate_satellites)
        candidate_factor = DecisionFactor(
            factor_name="candidate_count",
            value=candidate_count,
            weight=0.2,
            influence=min(candidate_count / 6, 1.0),
            description=f"可用候選衛星數量: {candidate_count}",
            confidence=0.95,
        )
        key_factors.append(candidate_factor)

        # 觸發事件嚴重程度因子
        trigger_severity = observation.trigger_severity
        trigger_factor = DecisionFactor(
            factor_name="trigger_severity",
            value=trigger_severity,
            weight=0.25,
            influence=trigger_severity,
            description=f"觸發事件嚴重程度: {trigger_severity:.2f}",
            confidence=0.8,
        )
        key_factors.append(trigger_factor)

        # 延遲因子
        latency = observation.current_latency
        latency_factor = DecisionFactor(
            factor_name="current_latency",
            value=latency,
            weight=0.15,
            influence=max(0, (100 - latency) / 100),
            description=f"當前延遲: {latency:.1f} ms",
            confidence=0.85,
        )
        key_factors.append(latency_factor)

        # 歷史換手次數因子
        handover_count = observation.handover_count
        handover_factor = DecisionFactor(
            factor_name="handover_history",
            value=handover_count,
            weight=0.1,
            influence=max(0, (5 - handover_count) / 5),  # 換手次數越多影響越負面
            description=f"已執行換手次數: {handover_count}",
            confidence=1.0,
        )
        key_factors.append(handover_factor)

        # 生成決策推理
        reasoning = self._generate_decision_reasoning(
            algorithm_decision.algorithm_type, environment_action, key_factors
        )

        # 分析替代動作
        alternative_actions = self._analyze_alternative_actions(
            observation, algorithm_decision, key_factors
        )

        # 置信度分解
        confidence_breakdown = {
            "signal_quality": rsrp_factor.influence * rsrp_factor.weight,
            "candidate_availability": candidate_factor.influence
            * candidate_factor.weight,
            "trigger_conditions": trigger_factor.influence * trigger_factor.weight,
            "performance_metrics": latency_factor.influence * latency_factor.weight,
            "historical_context": handover_factor.influence * handover_factor.weight,
        }

        # 不確定性來源
        uncertainty_sources = []
        if algorithm_decision.confidence < 0.7:
            uncertainty_sources.append("低算法置信度")
        if candidate_count < 3:
            uncertainty_sources.append("候選衛星不足")
        if trigger_severity > 0.8:
            uncertainty_sources.append("高嚴重度觸發事件")
        if rsrp < -90:
            uncertainty_sources.append("信號品質較差")

        return AlgorithmExplanation(
            algorithm_type=algorithm_decision.algorithm_type,
            decision_reasoning=reasoning,
            key_factors=key_factors,
            alternative_actions=alternative_actions,
            confidence_breakdown=confidence_breakdown,
            uncertainty_sources=uncertainty_sources,
            model_attention=algorithm_decision.reasoning,  # 如果有的話
        )

    def _generate_decision_reasoning(
        self,
        algorithm_type: AlgorithmType,
        action: EnvironmentAction,
        factors: List[DecisionFactor],
    ) -> str:
        """生成決策推理說明"""

        # 獲取主要影響因子
        primary_factors = sorted(
            factors, key=lambda f: abs(f.influence * f.weight), reverse=True
        )[:3]

        # 基於算法類型的解釋模板
        if algorithm_type == AlgorithmType.DQN:
            base_explanation = "DQN 算法基於 Q-value 估計選擇動作。"
        elif algorithm_type == AlgorithmType.PPO:
            base_explanation = "PPO 算法基於策略梯度和價值估計進行決策。"
        elif algorithm_type == AlgorithmType.SAC:
            base_explanation = "SAC 算法平衡探索和利用，基於軟價值函數決策。"
        else:
            base_explanation = "算法基於當前狀態進行決策。"

        # 動作解釋
        if action.action_type == "no_handover":
            action_explanation = "決定保持當前連接"
        elif action.action_type == "prepare_handover":
            action_explanation = "決定準備換手但暫不執行"
        elif action.action_type == "trigger_handover":
            action_explanation = "決定立即執行換手"
        else:
            action_explanation = "執行預設動作"

        # 因子解釋
        factor_explanations = []
        for factor in primary_factors:
            if factor.influence > 0.5:
                impact = "強烈支持"
            elif factor.influence > 0.2:
                impact = "支持"
            elif factor.influence > -0.2:
                impact = "中性影響"
            elif factor.influence > -0.5:
                impact = "反對"
            else:
                impact = "強烈反對"

            factor_explanations.append(f"{factor.description}（{impact}此決策）")

        reasoning = (
            f"{base_explanation} {action_explanation}。主要考慮因素："
            + "；".join(factor_explanations)
            + "。"
        )

        return reasoning

    def _analyze_alternative_actions(
        self,
        observation: EnvironmentObservation,
        decision: AlgorithmDecision,
        factors: List[DecisionFactor],
    ) -> List[Dict[str, Any]]:
        """分析替代動作選項"""

        alternatives = []

        # 計算因子總分
        total_score = sum(f.influence * f.weight for f in factors)

        # 分析 "不換手" 選項
        if decision.action != 0:  # 如果當前不是 "不換手"
            no_handover_score = total_score * 0.8  # 保守估計
            alternatives.append(
                {
                    "action": "no_handover",
                    "estimated_score": no_handover_score,
                    "reasoning": "保持當前連接，避免換手成本",
                    "pros": ["無換手延遲", "連接穩定"],
                    "cons": ["可能錯過更好信號", "無法解決當前問題"],
                }
            )

        # 分析 "準備換手" 選項
        if decision.action != 1:
            prepare_score = total_score * 0.9
            alternatives.append(
                {
                    "action": "prepare_handover",
                    "estimated_score": prepare_score,
                    "reasoning": "準備換手但觀察情況發展",
                    "pros": ["保留選擇權", "可觀察信號變化"],
                    "cons": ["可能延誤最佳時機", "增加計算開銷"],
                }
            )

        # 分析 "立即換手" 選項
        if decision.action != 2:
            trigger_score = (
                total_score * 1.1
                if observation.trigger_severity > 0.5
                else total_score * 0.7
            )
            alternatives.append(
                {
                    "action": "trigger_handover",
                    "estimated_score": trigger_score,
                    "reasoning": "立即執行換手以改善服務品質",
                    "pros": ["快速改善信號", "解決當前問題"],
                    "cons": ["換手延遲成本", "可能失敗風險"],
                }
            )

        return sorted(alternatives, key=lambda x: x["estimated_score"], reverse=True)

    def _evaluate_decision_confidence(
        self, confidence_value: float
    ) -> DecisionConfidence:
        """評估決策置信度級別"""
        if confidence_value < self.confidence_thresholds["very_low"]:
            return DecisionConfidence.VERY_LOW
        elif confidence_value < self.confidence_thresholds["low"]:
            return DecisionConfidence.LOW
        elif confidence_value < self.confidence_thresholds["medium"]:
            return DecisionConfidence.MEDIUM
        elif confidence_value < self.confidence_thresholds["high"]:
            return DecisionConfidence.HIGH
        else:
            return DecisionConfidence.VERY_HIGH

    def _evaluate_decision_quality(
        self, record: DecisionRecord, reward: EnvironmentReward
    ) -> DecisionQuality:
        """評估決策品質"""

        # 基於獎勵的基礎評分
        if reward.total_reward > 0.5:
            base_quality = DecisionQuality.EXCELLENT
        elif reward.total_reward > 0.0:
            base_quality = DecisionQuality.GOOD
        elif reward.total_reward > -0.3:
            base_quality = DecisionQuality.FAIR
        else:
            base_quality = DecisionQuality.POOR

        # 調整因子
        # 1. 置信度調整
        if record.decision_confidence in [
            DecisionConfidence.VERY_LOW,
            DecisionConfidence.LOW,
        ]:
            if base_quality == DecisionQuality.EXCELLENT:
                base_quality = DecisionQuality.GOOD
            elif base_quality == DecisionQuality.GOOD:
                base_quality = DecisionQuality.FAIR

        # 2. 成功率調整
        if reward.successful_handover and reward.handover_latency_ms < 30:
            # 快速成功換手提升品質
            if base_quality == DecisionQuality.GOOD:
                base_quality = DecisionQuality.EXCELLENT
        elif (
            not reward.successful_handover
            and record.environment_action.action_type == "trigger_handover"
        ):
            # 換手失敗降低品質
            if base_quality == DecisionQuality.EXCELLENT:
                base_quality = DecisionQuality.GOOD
            elif base_quality == DecisionQuality.GOOD:
                base_quality = DecisionQuality.FAIR

        return base_quality

    def _extract_environmental_factors(
        self, observation: EnvironmentObservation
    ) -> Dict[str, Any]:
        """提取環境因子"""
        return {
            "scenario_type": observation.scenario_type,
            "signal_strength": observation.serving_satellite_signal.get("rsrp", -100),
            "satellite_elevation": observation.serving_satellite_elevation,
            "candidate_count": len(observation.candidate_satellites),
            "trigger_events_count": len(observation.trigger_events),
            "current_latency": observation.current_latency,
            "current_throughput": observation.current_throughput,
            "episode_time": observation.episode_time,
            "handover_history_count": observation.handover_count,
        }

    async def _update_episode_statistics(self, record: DecisionRecord) -> None:
        """更新 episode 統計"""
        if not self.current_episode_id:
            return

        analytics = self.episode_analytics[self.current_episode_id]

        # 基本統計更新
        analytics.total_decisions += 1
        if record.success:
            analytics.successful_decisions += 1

        # 置信度統計
        total_conf = (
            analytics.average_confidence * (analytics.total_decisions - 1)
            + record.algorithm_decision.confidence
        )
        analytics.average_confidence = total_conf / analytics.total_decisions

        # 決策品質分佈
        if record.decision_quality:
            analytics.decision_quality_distribution[record.decision_quality] += 1

        # 獎勵統計
        if record.reward:
            analytics.total_reward += record.reward.total_reward
            analytics.average_reward_per_step = (
                analytics.total_reward / analytics.total_decisions
            )
            analytics.reward_progression.append(record.reward.total_reward)

            # 換手統計
            if record.environment_action.action_type == "trigger_handover":
                analytics.handover_count += 1
                if record.reward.successful_handover:
                    handover_success_count = sum(
                        1
                        for r in self.decision_records[self.current_episode_id]
                        if r.reward and r.reward.successful_handover
                    )
                    analytics.successful_handover_rate = (
                        handover_success_count / analytics.handover_count
                    )

        # 決策時間統計
        total_time = (
            analytics.average_decision_time_ms * (analytics.total_decisions - 1)
            + record.decision_time_ms
        )
        analytics.average_decision_time_ms = total_time / analytics.total_decisions

        # 置信度進展
        analytics.confidence_progression.append(record.algorithm_decision.confidence)

    async def _perform_deep_analysis(self, episode_id: str) -> None:
        """執行深度分析"""
        records = self.decision_records[episode_id]
        analytics = self.episode_analytics[episode_id]

        if not records:
            return

        # 因子重要性分析
        factor_scores = {}
        for record in records:
            for factor in record.explanation.key_factors:
                if factor.factor_name not in factor_scores:
                    factor_scores[factor.factor_name] = []
                factor_scores[factor.factor_name].append(
                    abs(factor.influence * factor.weight)
                )

        # 計算平均重要性
        analytics.factor_importance_scores = {
            name: np.mean(scores) for name, scores in factor_scores.items()
        }

        # 最具影響力的因子
        analytics.most_influential_factors = sorted(
            analytics.factor_importance_scores.keys(),
            key=lambda x: analytics.factor_importance_scores[x],
            reverse=True,
        )[:5]

        # 不確定性分析
        low_confidence_decisions = [
            r for r in records if r.algorithm_decision.confidence < 0.6
        ]
        high_confidence_decisions = [
            r for r in records if r.algorithm_decision.confidence > 0.8
        ]

        analytics.uncertainty_analysis = {
            "low_confidence_rate": len(low_confidence_decisions) / len(records),
            "high_confidence_rate": len(high_confidence_decisions) / len(records),
            "average_uncertainty_sources": np.mean(
                [len(r.explanation.uncertainty_sources) for r in records]
            ),
        }

        # 錯誤模式分析
        poor_decisions = [
            r for r in records if r.decision_quality == DecisionQuality.POOR
        ]
        if poor_decisions:
            error_patterns = {}
            for record in poor_decisions:
                # 分析錯誤原因
                error_context = {
                    "action_type": record.environment_action.action_type,
                    "confidence": record.algorithm_decision.confidence,
                    "signal_strength": record.observation.serving_satellite_signal.get(
                        "rsrp", -100
                    ),
                    "trigger_severity": record.observation.trigger_severity,
                }

                # 簡化錯誤分類
                if error_context["confidence"] < 0.3:
                    error_type = "low_confidence_error"
                elif (
                    error_context["action_type"] == "trigger_handover"
                    and error_context["signal_strength"] > -80
                ):
                    error_type = "unnecessary_handover"
                elif (
                    error_context["action_type"] == "no_handover"
                    and error_context["trigger_severity"] > 0.8
                ):
                    error_type = "missed_handover_opportunity"
                else:
                    error_type = "general_decision_error"

                if error_type not in error_patterns:
                    error_patterns[error_type] = 0
                error_patterns[error_type] += 1

            analytics.common_errors = [
                {
                    "error_type": error_type,
                    "count": count,
                    "percentage": count / len(poor_decisions),
                }
                for error_type, count in error_patterns.items()
            ]

    def _generate_improvement_suggestions(self, episode_id: str) -> List[str]:
        """生成改進建議"""
        analytics = self.episode_analytics[episode_id]
        suggestions = []

        # 基於置信度的建議
        if analytics.average_confidence < 0.6:
            suggestions.append("考慮增加訓練數據或調整模型參數以提升決策置信度")

        # 基於成功率的建議
        if analytics.successful_decisions / max(analytics.total_decisions, 1) < 0.7:
            suggestions.append("優化獎勵函數設計，提供更明確的性能反饋信號")

        # 基於換手性能的建議
        if analytics.successful_handover_rate < 0.8 and analytics.handover_count > 0:
            suggestions.append("改進候選衛星評分機制，提高換手成功率")

        # 基於決策時間的建議
        if analytics.average_decision_time_ms > 50:
            suggestions.append("優化算法計算效率，降低決策延遲")

        # 基於錯誤模式的建議
        if analytics.common_errors:
            most_common_error = max(analytics.common_errors, key=lambda x: x["count"])
            if most_common_error["error_type"] == "low_confidence_error":
                suggestions.append("增強模型訓練，提升複雜場景下的決策置信度")
            elif most_common_error["error_type"] == "unnecessary_handover":
                suggestions.append("調整換手觸發閾值，減少不必要的換手操作")
            elif most_common_error["error_type"] == "missed_handover_opportunity":
                suggestions.append("提高算法對觸發事件的敏感度，及時響應換手需求")

        # 基於因子分析的建議
        if "signal_rsrp" not in analytics.most_influential_factors[:3]:
            suggestions.append("加強信號品質因子在決策中的權重")

        return suggestions[:5]  # 限制建議數量

    def get_decision_records(
        self, episode_id: Optional[str] = None
    ) -> List[DecisionRecord]:
        """獲取決策記錄"""
        if episode_id:
            return self.decision_records.get(episode_id, [])
        elif self.current_episode_id:
            return self.decision_records.get(self.current_episode_id, [])
        else:
            return []

    def get_episode_analytics(
        self, episode_id: Optional[str] = None
    ) -> Optional[EpisodeAnalytics]:
        """獲取 episode 分析"""
        if episode_id:
            return self.episode_analytics.get(episode_id)
        elif self.current_episode_id:
            return self.episode_analytics.get(self.current_episode_id)
        else:
            return None

    def export_analytics_data(
        self, episode_id: str, format_type: str = "json"
    ) -> Dict[str, Any]:
        """匯出分析數據"""
        analytics = self.episode_analytics.get(episode_id)
        records = self.decision_records.get(episode_id, [])

        if not analytics:
            return {}

        export_data = {
            "episode_analytics": asdict(analytics),
            "decision_records": [asdict(record) for record in records],
            "summary": {
                "total_decisions": len(records),
                "algorithm_type": analytics.algorithm_type.value,
                "scenario_type": analytics.scenario_type,
                "total_reward": analytics.total_reward,
                "success_rate": analytics.successful_decisions
                / max(analytics.total_decisions, 1),
                "average_confidence": analytics.average_confidence,
            },
            "export_timestamp": datetime.now().isoformat(),
            "format": format_type,
        }

        return export_data

    def get_status(self) -> Dict[str, Any]:
        """獲取分析引擎狀態"""
        return {
            "current_episode_id": self.current_episode_id,
            "total_decisions_analyzed": self.total_decisions_analyzed,
            "total_episodes_analyzed": self.total_episodes_analyzed,
            "active_episodes": len(self.decision_records),
            "enable_detailed_logging": self.enable_detailed_logging,
            "enable_explainability": self.enable_explainability,
            "confidence_thresholds": self.confidence_thresholds,
        }
