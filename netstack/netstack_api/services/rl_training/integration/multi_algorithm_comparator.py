"""
Phase 2.3 多算法性能對比器

實現多算法 A/B 測試和性能對比：
- 並行算法性能測試
- 統計顯著性分析
- 算法優劣勢對比
- 場景適應性分析
- 性能基準測試
"""

import asyncio
import logging
import json
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from scipy import stats
import uuid

from .rl_algorithm_integrator import (
    RLAlgorithmIntegrator,
    AlgorithmType,
    AlgorithmDecision,
)
from .real_environment_bridge import (
    RealEnvironmentBridge,
    EnvironmentObservation,
    EnvironmentAction,
    EnvironmentReward,
)
from .decision_analytics_engine import DecisionAnalyticsEngine, EpisodeAnalytics

logger = logging.getLogger(__name__)


class ComparisonMetric(Enum):
    """比較指標類型"""

    TOTAL_REWARD = "total_reward"
    SUCCESS_RATE = "success_rate"
    DECISION_TIME = "decision_time"
    HANDOVER_SUCCESS_RATE = "handover_success_rate"
    AVERAGE_LATENCY = "average_latency"
    CONFIDENCE_LEVEL = "confidence_level"
    STABILITY = "stability"


class SignificanceLevel(Enum):
    """統計顯著性水平"""

    NOT_SIGNIFICANT = "not_significant"  # p > 0.05
    MARGINALLY_SIGNIFICANT = "marginally_significant"  # 0.01 < p <= 0.05
    SIGNIFICANT = "significant"  # 0.001 < p <= 0.01
    HIGHLY_SIGNIFICANT = "highly_significant"  # p <= 0.001


@dataclass
class AlgorithmPerformance:
    """算法性能數據"""

    algorithm_type: AlgorithmType
    episodes_completed: int

    # 核心性能指標
    total_reward: float
    average_reward_per_episode: float
    success_rate: float

    # 決策相關指標
    average_decision_time_ms: float
    average_confidence: float
    decision_consistency: float

    # 換手相關指標
    total_handovers: int
    handover_success_rate: float
    average_handover_latency_ms: float

    # 穩定性指標
    reward_variance: float
    performance_stability: float

    # 場景適應性
    scenario_performance: Dict[str, float]  # 不同場景下的表現

    # 詳細統計
    reward_distribution: List[float]
    decision_time_distribution: List[float]
    confidence_distribution: List[float]

    # 時間序列數據
    performance_trend: List[float]  # 性能趨勢
    learning_curve: List[float]  # 學習曲線


@dataclass
class ComparisonResult:
    """算法比較結果"""

    metric: ComparisonMetric
    algorithm_a: AlgorithmType
    algorithm_b: AlgorithmType

    # 統計數據
    mean_a: float
    mean_b: float
    std_a: float
    std_b: float

    # 統計檢驗結果
    t_statistic: float
    p_value: float
    significance_level: SignificanceLevel

    # 效應大小
    effect_size: float  # Cohen's d
    confidence_interval: Tuple[float, float]

    # 結論
    better_algorithm: Optional[AlgorithmType]
    improvement_percentage: float
    conclusion: str


@dataclass
class ABTestConfig:
    """A/B 測試配置"""

    algorithms: List[AlgorithmType]
    episodes_per_algorithm: int
    scenarios: List[str]
    metrics: List[ComparisonMetric]
    significance_threshold: float = 0.05
    minimum_effect_size: float = 0.2
    confidence_level: float = 0.95


@dataclass
class ABTestResult:
    """A/B 測試結果"""

    test_id: str
    start_time: datetime
    end_time: Optional[datetime]
    config: ABTestConfig

    # 性能數據
    algorithm_performances: Dict[AlgorithmType, AlgorithmPerformance]

    # 比較結果
    pairwise_comparisons: List[ComparisonResult]

    # 排名
    algorithm_ranking: List[Tuple[AlgorithmType, float]]  # (算法, 總分)

    # 場景適應性分析
    scenario_winners: Dict[str, AlgorithmType]
    scenario_performance_matrix: Dict[str, Dict[AlgorithmType, float]]

    # 統計摘要
    statistical_summary: Dict[str, Any]

    # 建議
    recommendations: List[str]


class MultiAlgorithmComparator:
    """多算法性能對比器"""

    def __init__(
        self,
        algorithm_integrator: RLAlgorithmIntegrator,
        environment_bridge: RealEnvironmentBridge,
        analytics_engine: DecisionAnalyticsEngine,
        config: Dict[str, Any],
    ):
        """
        初始化多算法比較器

        Args:
            algorithm_integrator: RL算法整合器
            environment_bridge: 環境橋接器
            analytics_engine: 決策分析引擎
            config: 比較器配置
        """
        self.algorithm_integrator = algorithm_integrator
        self.environment_bridge = environment_bridge
        self.analytics_engine = analytics_engine
        self.config = config

        # 測試管理
        self.active_tests: Dict[str, ABTestResult] = {}
        self.completed_tests: Dict[str, ABTestResult] = {}

        # 性能數據存儲
        self.performance_history: Dict[AlgorithmType, List[EpisodeAnalytics]] = {}

        # 比較配置
        self.default_scenarios = config.get(
            "default_scenarios", ["urban", "suburban", "rural"]
        )
        self.default_metrics = [
            ComparisonMetric.TOTAL_REWARD,
            ComparisonMetric.SUCCESS_RATE,
            ComparisonMetric.DECISION_TIME,
            ComparisonMetric.HANDOVER_SUCCESS_RATE,
        ]

        logger.info("多算法比較器初始化完成")

    async def start_ab_test(self, test_config: ABTestConfig) -> str:
        """
        開始 A/B 測試

        Args:
            test_config: 測試配置

        Returns:
            str: 測試 ID
        """
        test_id = str(uuid.uuid4())

        try:
            logger.info(f"開始 A/B 測試: {test_id}")

            # 創建測試結果對象
            test_result = ABTestResult(
                test_id=test_id,
                start_time=datetime.now(),
                end_time=None,
                config=test_config,
                algorithm_performances={},
                pairwise_comparisons=[],
                algorithm_ranking=[],
                scenario_winners={},
                scenario_performance_matrix={},
                statistical_summary={},
                recommendations=[],
            )

            self.active_tests[test_id] = test_result

            # 執行測試
            await self._execute_ab_test(test_id)

            return test_id

        except Exception as e:
            logger.error(f"A/B 測試啟動失敗: {e}")
            if test_id in self.active_tests:
                del self.active_tests[test_id]
            raise

    async def _execute_ab_test(self, test_id: str) -> None:
        """執行 A/B 測試"""
        test_result = self.active_tests[test_id]
        config = test_result.config

        try:
            logger.info(
                f"執行 A/B 測試 {test_id}，算法: {[a.value for a in config.algorithms]}"
            )

            # 為每個算法收集性能數據
            for algorithm in config.algorithms:
                logger.info(f"測試算法: {algorithm.value}")

                performance_data = await self._collect_algorithm_performance(
                    algorithm, config.episodes_per_algorithm, config.scenarios
                )

                test_result.algorithm_performances[algorithm] = performance_data

                logger.info(
                    f"算法 {algorithm.value} 測試完成，平均獎勵: {performance_data.average_reward_per_episode:.3f}"
                )

            # 執行統計比較
            await self._perform_statistical_analysis(test_id)

            # 生成排名和建議
            await self._generate_rankings_and_recommendations(test_id)

            # 完成測試
            test_result.end_time = datetime.now()
            self.completed_tests[test_id] = test_result
            del self.active_tests[test_id]

            duration = (test_result.end_time - test_result.start_time).total_seconds()
            logger.info(f"A/B 測試 {test_id} 完成，耗時: {duration:.1f} 秒")

        except Exception as e:
            logger.error(f"A/B 測試執行失敗: {e}")
            if test_id in self.active_tests:
                del self.active_tests[test_id]
            raise

    async def _collect_algorithm_performance(
        self, algorithm: AlgorithmType, episodes: int, scenarios: List[str]
    ) -> AlgorithmPerformance:
        """收集單個算法的性能數據"""

        # 切換到指定算法
        await self.algorithm_integrator.switch_algorithm(algorithm)

        # 性能數據收集
        episode_rewards = []
        episode_success_rates = []
        decision_times = []
        confidences = []
        handover_data = []
        scenario_performance = {}

        episodes_per_scenario = max(1, episodes // len(scenarios))

        for scenario in scenarios:
            scenario_rewards = []

            for episode_idx in range(episodes_per_scenario):
                try:
                    # 重置環境
                    obs = await self.environment_bridge.reset(
                        {"scenario_type": scenario, "complexity": "moderate"}
                    )

                    # 開始 episode 分析
                    episode_id = f"{algorithm.value}_{scenario}_{episode_idx}"
                    self.analytics_engine.start_episode(episode_id, algorithm, scenario)

                    episode_reward = 0.0
                    successful_decisions = 0
                    total_decisions = 0
                    episode_handovers = []

                    # 運行 episode
                    for step in range(100):  # 限制步數
                        # 算法決策
                        decision = await self.algorithm_integrator.predict(obs)

                        # 轉換為環境動作
                        action = self._convert_decision_to_action(decision)

                        # 記錄決策分析
                        decision_record = await self.analytics_engine.analyze_decision(
                            obs,
                            decision,
                            action,
                            {"scenario": scenario, "episode": episode_idx},
                        )

                        # 執行環境步驟
                        next_obs, reward, terminated, truncated, info = (
                            await self.environment_bridge.step(action)
                        )

                        # 更新決策結果
                        await self.analytics_engine.update_decision_result(
                            decision_record.decision_id,
                            reward,
                            next_obs,
                            info.get("step_duration_ms", 0),
                        )

                        # 更新算法
                        await self.algorithm_integrator.update(
                            obs,
                            action,
                            reward.total_reward,
                            next_obs,
                            terminated or truncated,
                        )

                        # 收集數據
                        episode_reward += reward.total_reward
                        total_decisions += 1
                        if reward.total_reward > 0:
                            successful_decisions += 1

                        decision_times.append(decision.decision_time_ms)
                        confidences.append(decision.confidence)

                        if action.action_type == "trigger_handover":
                            episode_handovers.append(
                                {
                                    "success": reward.successful_handover,
                                    "latency": reward.handover_latency_ms,
                                }
                            )

                        obs = next_obs

                        if terminated or truncated:
                            break

                    # 完成 episode 分析
                    episode_analytics = await self.analytics_engine.finalize_episode()

                    # 記錄性能數據
                    episode_rewards.append(episode_reward)
                    episode_success_rates.append(
                        successful_decisions / max(total_decisions, 1)
                    )
                    handover_data.extend(episode_handovers)
                    scenario_rewards.append(episode_reward)

                    logger.debug(
                        f"Episode {episode_idx} 完成，獎勵: {episode_reward:.3f}"
                    )

                except Exception as e:
                    logger.error(f"Episode 執行失敗: {e}")
                    continue

            # 計算場景平均性能
            if scenario_rewards:
                scenario_performance[scenario] = np.mean(scenario_rewards)

            logger.info(
                f"場景 {scenario} 測試完成，平均獎勵: {np.mean(scenario_rewards):.3f}"
            )

        # 計算統計指標
        total_handovers = len(handover_data)
        successful_handovers = sum(1 for h in handover_data if h["success"])

        performance = AlgorithmPerformance(
            algorithm_type=algorithm,
            episodes_completed=len(episode_rewards),
            total_reward=sum(episode_rewards),
            average_reward_per_episode=(
                np.mean(episode_rewards) if episode_rewards else 0.0
            ),
            success_rate=(
                np.mean(episode_success_rates) if episode_success_rates else 0.0
            ),
            average_decision_time_ms=np.mean(decision_times) if decision_times else 0.0,
            average_confidence=np.mean(confidences) if confidences else 0.0,
            decision_consistency=1.0 - np.std(confidences) if confidences else 0.0,
            total_handovers=total_handovers,
            handover_success_rate=successful_handovers / max(total_handovers, 1),
            average_handover_latency_ms=(
                np.mean([h["latency"] for h in handover_data if h["success"]])
                if handover_data
                else 0.0
            ),
            reward_variance=np.var(episode_rewards) if episode_rewards else 0.0,
            performance_stability=(
                1.0 / (1.0 + np.std(episode_rewards)) if episode_rewards else 0.0
            ),
            scenario_performance=scenario_performance,
            reward_distribution=episode_rewards,
            decision_time_distribution=decision_times,
            confidence_distribution=confidences,
            performance_trend=(
                episode_rewards[-20:] if len(episode_rewards) >= 20 else episode_rewards
            ),
            learning_curve=self._calculate_learning_curve(episode_rewards),
        )

        return performance

    def _convert_decision_to_action(
        self, decision: AlgorithmDecision
    ) -> EnvironmentAction:
        """將算法決策轉換為環境動作"""
        from .real_environment_bridge import EnvironmentAction

        # 處理不同的動作格式
        if isinstance(decision.action, int):
            action_mapping = {
                0: "no_handover",
                1: "prepare_handover",
                2: "trigger_handover",
            }
            action_type = action_mapping.get(decision.action, "no_handover")
        else:
            action_type = "no_handover"

        return EnvironmentAction(
            action_type=action_type,
            target_satellite_id=None,
            handover_timing=0.5,
            power_control=0.7,
            priority_level=0.6,
        )

    def _calculate_learning_curve(
        self, rewards: List[float], window_size: int = 10
    ) -> List[float]:
        """計算學習曲線（移動平均）"""
        if len(rewards) < window_size:
            return rewards

        learning_curve = []
        for i in range(len(rewards) - window_size + 1):
            window_avg = np.mean(rewards[i : i + window_size])
            learning_curve.append(window_avg)

        return learning_curve

    async def _perform_statistical_analysis(self, test_id: str) -> None:
        """執行統計分析"""
        test_result = self.active_tests[test_id]
        performances = test_result.algorithm_performances

        algorithms = list(performances.keys())

        # 執行兩兩比較
        for i, algo_a in enumerate(algorithms):
            for j, algo_b in enumerate(algorithms[i + 1 :], i + 1):

                perf_a = performances[algo_a]
                perf_b = performances[algo_b]

                # 對每個指標執行比較
                for metric in test_result.config.metrics:
                    comparison = await self._compare_algorithms(perf_a, perf_b, metric)
                    test_result.pairwise_comparisons.append(comparison)

        # 生成統計摘要
        test_result.statistical_summary = self._generate_statistical_summary(
            test_result
        )

    async def _compare_algorithms(
        self,
        perf_a: AlgorithmPerformance,
        perf_b: AlgorithmPerformance,
        metric: ComparisonMetric,
    ) -> ComparisonResult:
        """比較兩個算法在特定指標上的性能"""

        # 提取指標數據
        data_a, data_b = self._extract_metric_data(perf_a, perf_b, metric)

        # 計算基本統計
        mean_a, mean_b = np.mean(data_a), np.mean(data_b)
        std_a, std_b = np.std(data_a), np.std(data_b)

        # 執行 t 檢驗
        if len(data_a) > 1 and len(data_b) > 1:
            t_stat, p_value = stats.ttest_ind(data_a, data_b, equal_var=False)
        else:
            t_stat, p_value = 0.0, 1.0

        # 計算效應大小 (Cohen's d)
        pooled_std = np.sqrt(
            ((len(data_a) - 1) * std_a**2 + (len(data_b) - 1) * std_b**2)
            / (len(data_a) + len(data_b) - 2)
        )
        effect_size = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0

        # 計算置信區間
        se_diff = pooled_std * np.sqrt(1 / len(data_a) + 1 / len(data_b))
        margin_error = stats.t.ppf(0.975, len(data_a) + len(data_b) - 2) * se_diff
        ci_lower = (mean_a - mean_b) - margin_error
        ci_upper = (mean_a - mean_b) + margin_error

        # 確定顯著性水平
        if p_value <= 0.001:
            significance = SignificanceLevel.HIGHLY_SIGNIFICANT
        elif p_value <= 0.01:
            significance = SignificanceLevel.SIGNIFICANT
        elif p_value <= 0.05:
            significance = SignificanceLevel.MARGINALLY_SIGNIFICANT
        else:
            significance = SignificanceLevel.NOT_SIGNIFICANT

        # 確定較好的算法
        better_algorithm = None
        improvement_percentage = 0.0

        if (
            significance != SignificanceLevel.NOT_SIGNIFICANT
            and abs(effect_size) >= 0.2
        ):
            if mean_a > mean_b:
                better_algorithm = perf_a.algorithm_type
                improvement_percentage = (
                    ((mean_a - mean_b) / abs(mean_b)) * 100 if mean_b != 0 else 0
                )
            else:
                better_algorithm = perf_b.algorithm_type
                improvement_percentage = (
                    ((mean_b - mean_a) / abs(mean_a)) * 100 if mean_a != 0 else 0
                )

        # 生成結論
        conclusion = self._generate_comparison_conclusion(
            perf_a.algorithm_type,
            perf_b.algorithm_type,
            metric,
            significance,
            better_algorithm,
            improvement_percentage,
        )

        return ComparisonResult(
            metric=metric,
            algorithm_a=perf_a.algorithm_type,
            algorithm_b=perf_b.algorithm_type,
            mean_a=mean_a,
            mean_b=mean_b,
            std_a=std_a,
            std_b=std_b,
            t_statistic=t_stat,
            p_value=p_value,
            significance_level=significance,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper),
            better_algorithm=better_algorithm,
            improvement_percentage=improvement_percentage,
            conclusion=conclusion,
        )

    def _extract_metric_data(
        self,
        perf_a: AlgorithmPerformance,
        perf_b: AlgorithmPerformance,
        metric: ComparisonMetric,
    ) -> Tuple[List[float], List[float]]:
        """提取指標數據用於比較"""

        if metric == ComparisonMetric.TOTAL_REWARD:
            return perf_a.reward_distribution, perf_b.reward_distribution
        elif metric == ComparisonMetric.DECISION_TIME:
            return perf_a.decision_time_distribution, perf_b.decision_time_distribution
        elif metric == ComparisonMetric.CONFIDENCE_LEVEL:
            return perf_a.confidence_distribution, perf_b.confidence_distribution
        elif metric == ComparisonMetric.SUCCESS_RATE:
            # 對於成功率，使用 episode 級別的數據
            return (
                [perf_a.success_rate] * perf_a.episodes_completed,
                [perf_b.success_rate] * perf_b.episodes_completed,
            )
        elif metric == ComparisonMetric.HANDOVER_SUCCESS_RATE:
            return (
                [perf_a.handover_success_rate] * max(perf_a.total_handovers, 1),
                [perf_b.handover_success_rate] * max(perf_b.total_handovers, 1),
            )
        else:
            # 預設返回獎勵分佈
            return perf_a.reward_distribution, perf_b.reward_distribution

    def _generate_comparison_conclusion(
        self,
        algo_a: AlgorithmType,
        algo_b: AlgorithmType,
        metric: ComparisonMetric,
        significance: SignificanceLevel,
        better_algorithm: Optional[AlgorithmType],
        improvement: float,
    ) -> str:
        """生成比較結論"""

        metric_name = metric.value.replace("_", " ").title()

        if significance == SignificanceLevel.NOT_SIGNIFICANT:
            return f"在 {metric_name} 指標上，{algo_a.value.upper()} 和 {algo_b.value.upper()} 沒有統計顯著差異"

        if better_algorithm:
            worse_algorithm = algo_b if better_algorithm == algo_a else algo_a
            return (
                f"在 {metric_name} 指標上，{better_algorithm.value.upper()} "
                f"顯著優於 {worse_algorithm.value.upper()}（改善 {improvement:.1f}%，"
                f"顯著性: {significance.value.replace('_', ' ')}）"
            )

        return f"在 {metric_name} 指標上比較結果不確定"

    def _generate_statistical_summary(
        self, test_result: ABTestResult
    ) -> Dict[str, Any]:
        """生成統計摘要"""

        comparisons = test_result.pairwise_comparisons
        performances = test_result.algorithm_performances

        # 統計顯著性總結
        significance_counts = {}
        for comp in comparisons:
            sig_level = comp.significance_level.value
            if sig_level not in significance_counts:
                significance_counts[sig_level] = 0
            significance_counts[sig_level] += 1

        # 算法勝負統計
        win_counts = {}
        for algo in performances.keys():
            win_counts[algo.value] = 0

        for comp in comparisons:
            if comp.better_algorithm:
                win_counts[comp.better_algorithm.value] += 1

        # 平均效應大小
        effect_sizes = [abs(comp.effect_size) for comp in comparisons]
        average_effect_size = np.mean(effect_sizes) if effect_sizes else 0.0

        return {
            "total_comparisons": len(comparisons),
            "significance_distribution": significance_counts,
            "algorithm_win_counts": win_counts,
            "average_effect_size": average_effect_size,
            "strong_effects": sum(1 for es in effect_sizes if es >= 0.8),
            "medium_effects": sum(1 for es in effect_sizes if 0.5 <= es < 0.8),
            "small_effects": sum(1 for es in effect_sizes if 0.2 <= es < 0.5),
            "negligible_effects": sum(1 for es in effect_sizes if es < 0.2),
        }

    async def _generate_rankings_and_recommendations(self, test_id: str) -> None:
        """生成算法排名和建議"""
        test_result = self.active_tests[test_id]
        performances = test_result.algorithm_performances

        # 計算綜合得分
        algorithm_scores = {}

        for algo, perf in performances.items():
            # 標準化各項指標
            score = 0.0

            # 獎勵得分 (30%)
            max_reward = max(
                p.average_reward_per_episode for p in performances.values()
            )
            if max_reward > 0:
                score += 0.3 * (perf.average_reward_per_episode / max_reward)

            # 成功率得分 (25%)
            score += 0.25 * perf.success_rate

            # 決策效率得分 (20%)
            min_decision_time = min(
                p.average_decision_time_ms for p in performances.values()
            )
            if perf.average_decision_time_ms > 0:
                score += 0.2 * (min_decision_time / perf.average_decision_time_ms)

            # 置信度得分 (15%)
            score += 0.15 * perf.average_confidence

            # 穩定性得分 (10%)
            score += 0.1 * perf.performance_stability

            algorithm_scores[algo] = score

        # 排名
        test_result.algorithm_ranking = sorted(
            algorithm_scores.items(), key=lambda x: x[1], reverse=True
        )

        # 場景適應性分析
        for scenario in test_result.config.scenarios:
            scenario_scores = {}
            for algo, perf in performances.items():
                scenario_scores[algo] = perf.scenario_performance.get(scenario, 0.0)

            if scenario_scores:
                best_algo = max(
                    scenario_scores.keys(), key=lambda x: scenario_scores[x]
                )
                test_result.scenario_winners[scenario] = best_algo
                test_result.scenario_performance_matrix[scenario] = scenario_scores

        # 生成建議
        test_result.recommendations = self._generate_recommendations(test_result)

    def _generate_recommendations(self, test_result: ABTestResult) -> List[str]:
        """生成改進建議"""
        recommendations = []

        # 基於排名的建議
        if test_result.algorithm_ranking:
            best_algo = test_result.algorithm_ranking[0][0]
            worst_algo = test_result.algorithm_ranking[-1][0]

            recommendations.append(
                f"建議優先使用 {best_algo.value.upper()} 算法，"
                f"在綜合性能評估中排名第一"
            )

            if len(test_result.algorithm_ranking) > 1:
                score_gap = (
                    test_result.algorithm_ranking[0][1]
                    - test_result.algorithm_ranking[-1][1]
                )
                if score_gap > 0.2:
                    recommendations.append(
                        f"{worst_algo.value.upper()} 算法性能明顯落後，"
                        f"建議重新調整超參數或訓練策略"
                    )

        # 基於場景適應性的建議
        if test_result.scenario_winners:
            scenario_diversity = len(set(test_result.scenario_winners.values()))
            if scenario_diversity > 1:
                recommendations.append(
                    "不同場景下最佳算法有差異，建議實施動態算法選擇策略"
                )

            for scenario, winner in test_result.scenario_winners.items():
                recommendations.append(
                    f"在 {scenario} 場景下，建議使用 {winner.value.upper()} 算法"
                )

        # 基於統計分析的建議
        stat_summary = test_result.statistical_summary
        if stat_summary.get("average_effect_size", 0) < 0.2:
            recommendations.append(
                "算法間差異較小，可能需要更多樣化的測試場景或更長的訓練週期"
            )

        if (
            stat_summary.get("negligible_effects", 0)
            > stat_summary.get("total_comparisons", 1) * 0.7
        ):
            recommendations.append(
                "大部分比較結果效應大小較小，建議檢查算法配置和環境設定"
            )

        return recommendations[:10]  # 限制建議數量

    def get_test_result(self, test_id: str) -> Optional[ABTestResult]:
        """獲取測試結果"""
        if test_id in self.completed_tests:
            return self.completed_tests[test_id]
        elif test_id in self.active_tests:
            return self.active_tests[test_id]
        else:
            return None

    def get_all_test_results(self) -> Dict[str, ABTestResult]:
        """獲取所有測試結果"""
        all_results = {}
        all_results.update(self.completed_tests)
        all_results.update(self.active_tests)
        return all_results

    def export_comparison_report(
        self, test_id: str, format_type: str = "json"
    ) -> Dict[str, Any]:
        """匯出比較報告"""
        test_result = self.get_test_result(test_id)
        if not test_result:
            return {}

        report = {
            "test_summary": {
                "test_id": test_id,
                "algorithms_tested": [a.value for a in test_result.config.algorithms],
                "scenarios": test_result.config.scenarios,
                "total_episodes": sum(
                    p.episodes_completed
                    for p in test_result.algorithm_performances.values()
                ),
                "test_duration_seconds": (
                    (test_result.end_time - test_result.start_time).total_seconds()
                    if test_result.end_time
                    else None
                ),
            },
            "performance_summary": {
                algo.value: {
                    "average_reward": perf.average_reward_per_episode,
                    "success_rate": perf.success_rate,
                    "decision_time_ms": perf.average_decision_time_ms,
                    "confidence": perf.average_confidence,
                    "handover_success_rate": perf.handover_success_rate,
                }
                for algo, perf in test_result.algorithm_performances.items()
            },
            "rankings": [
                {"algorithm": algo.value, "score": score}
                for algo, score in test_result.algorithm_ranking
            ],
            "scenario_analysis": {
                scenario: winner.value
                for scenario, winner in test_result.scenario_winners.items()
            },
            "statistical_analysis": test_result.statistical_summary,
            "recommendations": test_result.recommendations,
            "detailed_comparisons": [
                {
                    "metric": comp.metric.value,
                    "algorithms": [comp.algorithm_a.value, comp.algorithm_b.value],
                    "means": [comp.mean_a, comp.mean_b],
                    "p_value": comp.p_value,
                    "significance": comp.significance_level.value,
                    "better_algorithm": (
                        comp.better_algorithm.value if comp.better_algorithm else None
                    ),
                    "improvement_percent": comp.improvement_percentage,
                    "conclusion": comp.conclusion,
                }
                for comp in test_result.pairwise_comparisons
            ],
            "export_timestamp": datetime.now().isoformat(),
            "format": format_type,
        }

        return report

    def get_status(self) -> Dict[str, Any]:
        """獲取比較器狀態"""
        return {
            "active_tests": len(self.active_tests),
            "completed_tests": len(self.completed_tests),
            "total_tests_run": len(self.completed_tests),
            "available_algorithms": [
                a.value for a in self.algorithm_integrator.get_available_algorithms()
            ],
            "default_scenarios": self.default_scenarios,
            "default_metrics": [m.value for m in self.default_metrics],
        }
