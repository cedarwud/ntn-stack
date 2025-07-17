"""
🧠 真實 RL 訓練指標計算服務
移除硬編碼模擬數據，實現基於真實訓練過程的指標計算
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass

# 導入統一接口
from ..interfaces.metrics_interface import (
    IMetricsCalculator,
    StandardizedMetrics,
    MetricType,
    TrendType,
    MetricDefinition,
    MetricsStandardizer,
)

logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """訓練指標數據結構"""

    success_rate: float  # 成功率 (0.0 - 1.0)
    stability: float  # 穩定性 (0.0 - 1.0)
    average_reward: float
    convergence_episode: Optional[int]
    learning_efficiency: float
    performance_trend: str  # "improving", "stable", "declining"
    confidence_score: float  # 指標可信度 (0.0 - 1.0)


@dataclass
class EpisodeData:
    """單個回合數據"""

    episode_number: int
    total_reward: float
    steps: int
    success: bool
    handover_count: int
    average_latency: float
    timestamp: datetime


class RealMetricsCalculator(IMetricsCalculator):
    """真實指標計算器 - 實現統一接口"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.standardizer = MetricsStandardizer()

        # 指標計算參數
        self.success_reward_threshold = 100.0  # 成功回合的最低獎勵閾值
        self.stability_window_size = 20  # 穩定性計算的滑動窗口大小
        self.convergence_patience = 10  # 收斂判斷的耐心值
        self.min_episodes_for_metrics = 5  # 計算指標所需的最少回合數

    # 實現統一接口方法
    async def calculate_metrics(
        self, data: List[Dict[str, Any]], algorithm: str, session_id: str
    ) -> StandardizedMetrics:
        """實現統一接口的指標計算方法"""
        # 轉換數據格式
        episodes_data = []
        for item in data:
            if hasattr(item, "episode_number"):  # EpisodeData 對象
                episodes_data.append(item)
            else:  # 字典格式
                episode_data = EpisodeData(
                    episode_number=item.get("episode_number", 0),
                    total_reward=item.get("total_reward", 0.0),
                    steps=item.get("steps", 0),
                    success=item.get("success", False),
                    handover_count=item.get("handover_count", 0),
                    average_latency=item.get("average_latency", 0.0),
                    timestamp=datetime.fromisoformat(
                        item.get("timestamp", datetime.now().isoformat())
                    ),
                )
                episodes_data.append(episode_data)

        # 使用原有的計算邏輯
        legacy_metrics = await self.calculate_training_metrics(
            session_id, algorithm, episodes_data
        )

        # 轉換為標準化格式
        return StandardizedMetrics(
            success_rate=self.standardizer.normalize_value(legacy_metrics.success_rate),
            stability=self.standardizer.normalize_value(legacy_metrics.stability),
            learning_efficiency=self.standardizer.normalize_value(
                legacy_metrics.learning_efficiency
            ),
            confidence_score=self.standardizer.normalize_value(
                legacy_metrics.confidence_score
            ),
            average_reward=legacy_metrics.average_reward,
            convergence_episode=legacy_metrics.convergence_episode,
            performance_trend=(
                TrendType(legacy_metrics.performance_trend)
                if legacy_metrics.performance_trend in [t.value for t in TrendType]
                else TrendType.INSUFFICIENT_DATA
            ),
            calculation_timestamp=datetime.now().isoformat(),
            data_points_count=len(episodes_data),
            calculation_method="real_training_data",
        )

    def get_metric_definition(self, metric_type: MetricType) -> MetricDefinition:
        """獲取指標定義"""
        return self.standardizer.METRIC_DEFINITIONS.get(metric_type)

    def validate_metrics(self, metrics: StandardizedMetrics) -> bool:
        """驗證指標有效性"""
        return self.standardizer._validate_all_metrics(metrics)

    async def calculate_training_metrics(
        self, session_id: str, algorithm: str, episodes_data: List[EpisodeData]
    ) -> TrainingMetrics:
        """
        計算真實的訓練指標

        Args:
            session_id: 訓練會話ID
            algorithm: 算法名稱
            episodes_data: 回合數據列表

        Returns:
            TrainingMetrics: 計算得出的真實指標
        """
        self.logger.info(
            f"🧮 [指標計算] 開始計算 {algorithm} 會話 {session_id} 的真實指標"
        )

        if len(episodes_data) < self.min_episodes_for_metrics:
            self.logger.warning(
                f"⚠️ [指標計算] 回合數不足 ({len(episodes_data)} < {self.min_episodes_for_metrics})，返回初始指標"
            )
            return self._get_initial_metrics()

        try:
            # 提取基礎數據
            rewards = [ep.total_reward for ep in episodes_data]
            successes = [ep.success for ep in episodes_data]
            latencies = [ep.average_latency for ep in episodes_data]

            # 計算各項指標
            success_rate = await self._calculate_success_rate(successes, rewards)
            stability = await self._calculate_stability(rewards)
            average_reward = statistics.mean(rewards)
            convergence_episode = await self._detect_convergence(rewards)
            learning_efficiency = await self._calculate_learning_efficiency(rewards)
            performance_trend = await self._analyze_performance_trend(rewards)
            confidence_score = await self._calculate_confidence_score(episodes_data)

            metrics = TrainingMetrics(
                success_rate=success_rate,
                stability=stability,
                average_reward=average_reward,
                convergence_episode=convergence_episode,
                learning_efficiency=learning_efficiency,
                performance_trend=performance_trend,
                confidence_score=confidence_score,
            )

            self.logger.info(
                f"✅ [指標計算] {algorithm} 指標計算完成: 成功率={success_rate:.3f}, 穩定性={stability:.3f}"
            )
            return metrics

        except Exception as e:
            self.logger.error(f"❌ [指標計算] 計算失敗: {e}")
            return self._get_error_metrics()

    async def _calculate_success_rate(
        self, successes: List[bool], rewards: List[float]
    ) -> float:
        """
        計算真實成功率
        結合布爾成功標記和獎勵閾值
        """
        if not successes and not rewards:
            return 0.0

        # 方法1: 基於明確的成功標記
        boolean_success_rate = sum(successes) / len(successes) if successes else 0.0

        # 方法2: 基於獎勵閾值
        reward_success_count = sum(
            1 for r in rewards if r >= self.success_reward_threshold
        )
        reward_success_rate = reward_success_count / len(rewards) if rewards else 0.0

        # 方法3: 基於獎勵趨勢（最近回合表現）
        if len(rewards) >= 10:
            recent_rewards = rewards[-10:]
            recent_avg = statistics.mean(recent_rewards)
            overall_avg = statistics.mean(rewards)
            trend_success_rate = min(1.0, max(0.0, recent_avg / max(overall_avg, 1.0)))
        else:
            trend_success_rate = reward_success_rate

        # 加權平均三種方法
        if successes:  # 如果有明確的成功標記
            final_success_rate = (
                boolean_success_rate * 0.5
                + reward_success_rate * 0.3
                + trend_success_rate * 0.2
            )
        else:  # 只基於獎勵計算
            final_success_rate = reward_success_rate * 0.7 + trend_success_rate * 0.3

        return max(0.0, min(1.0, final_success_rate))

    async def _calculate_stability(self, rewards: List[float]) -> float:
        """
        計算訓練穩定性
        基於獎勵的變異係數和滑動窗口標準差
        """
        if len(rewards) < 3:
            return 0.0

        # 方法1: 整體變異係數
        mean_reward = statistics.mean(rewards)
        if mean_reward == 0:
            overall_cv = float("inf")
        else:
            std_reward = statistics.stdev(rewards)
            overall_cv = std_reward / abs(mean_reward)

        # 方法2: 滑動窗口穩定性
        window_size = min(self.stability_window_size, len(rewards) // 2)
        if window_size < 3:
            window_stability = 1.0 - min(1.0, overall_cv)
        else:
            window_stds = []
            for i in range(window_size, len(rewards)):
                window_rewards = rewards[i - window_size : i]
                window_std = statistics.stdev(window_rewards)
                window_stds.append(window_std)

            if window_stds:
                avg_window_std = statistics.mean(window_stds)
                window_stability = 1.0 - min(
                    1.0, avg_window_std / max(abs(mean_reward), 1.0)
                )
            else:
                window_stability = 1.0 - min(1.0, overall_cv)

        # 方法3: 趨勢穩定性（最近是否穩定）
        if len(rewards) >= 10:
            recent_rewards = rewards[-10:]
            recent_std = statistics.stdev(recent_rewards)
            recent_mean = statistics.mean(recent_rewards)
            trend_stability = 1.0 - min(1.0, recent_std / max(abs(recent_mean), 1.0))
        else:
            trend_stability = window_stability

        # 加權平均
        final_stability = (
            (1.0 - min(1.0, overall_cv)) * 0.3
            + window_stability * 0.4
            + trend_stability * 0.3
        )

        return max(0.0, min(1.0, final_stability))

    async def _detect_convergence(self, rewards: List[float]) -> Optional[int]:
        """
        檢測收斂點
        基於獎勵變化率和穩定性
        """
        if len(rewards) < self.convergence_patience * 2:
            return None

        # 計算滑動平均
        window_size = self.convergence_patience
        moving_averages = []

        for i in range(window_size, len(rewards)):
            window_avg = statistics.mean(rewards[i - window_size : i])
            moving_averages.append(window_avg)

        # 檢測收斂：連續多個窗口的變化率小於閾值
        convergence_threshold = 0.05  # 5% 變化率閾值
        stable_windows = 0

        for i in range(1, len(moving_averages)):
            if len(moving_averages) > i:
                change_rate = abs(moving_averages[i] - moving_averages[i - 1]) / max(
                    abs(moving_averages[i - 1]), 1.0
                )
                if change_rate < convergence_threshold:
                    stable_windows += 1
                    if stable_windows >= self.convergence_patience // 2:
                        convergence_episode = window_size + i - stable_windows
                        return convergence_episode
                else:
                    stable_windows = 0

        return None

    async def _calculate_learning_efficiency(self, rewards: List[float]) -> float:
        """
        計算學習效率
        基於獎勵改善速度和收斂速度
        """
        if len(rewards) < 5:
            return 0.0

        # 計算改善速度
        initial_avg = statistics.mean(rewards[:5])
        final_avg = statistics.mean(rewards[-5:])
        improvement = final_avg - initial_avg

        # 正規化改善幅度
        max_possible_improvement = max(abs(max(rewards)), abs(min(rewards)), 100.0)
        normalized_improvement = improvement / max_possible_improvement

        # 計算學習速度（早期改善）
        if len(rewards) >= 20:
            early_improvement = statistics.mean(rewards[10:15]) - statistics.mean(
                rewards[:5]
            )
            early_speed = early_improvement / max_possible_improvement
        else:
            early_speed = normalized_improvement

        # 綜合效率分數
        efficiency = normalized_improvement * 0.6 + early_speed * 0.4
        return max(0.0, min(1.0, (efficiency + 1.0) / 2.0))  # 轉換到 [0,1] 範圍

    async def _analyze_performance_trend(self, rewards: List[float]) -> str:
        """
        分析性能趨勢
        """
        if len(rewards) < 10:
            return "insufficient_data"

        # 比較前半段和後半段
        mid_point = len(rewards) // 2
        first_half_avg = statistics.mean(rewards[:mid_point])
        second_half_avg = statistics.mean(rewards[mid_point:])

        # 比較最近10個回合和之前的平均
        recent_avg = statistics.mean(rewards[-10:])
        earlier_avg = statistics.mean(rewards[:-10])

        improvement_threshold = 0.1  # 10% 改善閾值

        long_term_improvement = (second_half_avg - first_half_avg) / max(
            abs(first_half_avg), 1.0
        )
        recent_improvement = (recent_avg - earlier_avg) / max(abs(earlier_avg), 1.0)

        if (
            long_term_improvement > improvement_threshold
            and recent_improvement > improvement_threshold
        ):
            return "improving"
        elif (
            abs(long_term_improvement) <= improvement_threshold
            and abs(recent_improvement) <= improvement_threshold
        ):
            return "stable"
        elif (
            long_term_improvement < -improvement_threshold
            or recent_improvement < -improvement_threshold
        ):
            return "declining"
        else:
            return "mixed"

    async def _calculate_confidence_score(
        self, episodes_data: List[EpisodeData]
    ) -> float:
        """
        計算指標可信度分數
        基於數據量、數據質量和時間跨度
        """
        if not episodes_data:
            return 0.0

        # 數據量分數
        data_volume_score = min(1.0, len(episodes_data) / 50.0)  # 50個回合為滿分

        # 數據質量分數（基於獎勵分佈的合理性）
        rewards = [ep.total_reward for ep in episodes_data]
        if len(rewards) > 1:
            reward_range = max(rewards) - min(rewards)
            reward_std = statistics.stdev(rewards)
            # 合理的變異性表示真實的學習過程
            quality_score = min(1.0, reward_std / max(reward_range, 1.0))
        else:
            quality_score = 0.5

        # 時間跨度分數
        if len(episodes_data) > 1:
            time_span = (
                episodes_data[-1].timestamp - episodes_data[0].timestamp
            ).total_seconds()
            time_score = min(1.0, time_span / 3600.0)  # 1小時為滿分
        else:
            time_score = 0.1

        # 綜合可信度
        confidence = data_volume_score * 0.5 + quality_score * 0.3 + time_score * 0.2
        return max(0.1, min(1.0, confidence))

    def _get_initial_metrics(self) -> TrainingMetrics:
        """返回初始指標（數據不足時）"""
        return TrainingMetrics(
            success_rate=0.0,
            stability=0.0,
            average_reward=0.0,
            convergence_episode=None,
            learning_efficiency=0.0,
            performance_trend="insufficient_data",
            confidence_score=0.1,
        )

    def _get_error_metrics(self) -> TrainingMetrics:
        """返回錯誤指標（計算失敗時）"""
        return TrainingMetrics(
            success_rate=0.0,
            stability=0.0,
            average_reward=0.0,
            convergence_episode=None,
            learning_efficiency=0.0,
            performance_trend="error",
            confidence_score=0.0,
        )


# 全局實例
real_metrics_calculator = RealMetricsCalculator()


async def get_real_metrics_calculator() -> RealMetricsCalculator:
    """獲取真實指標計算器實例"""
    return real_metrics_calculator
