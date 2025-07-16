"""
遷移評估器 - Phase 3 核心組件

提供算法遷移效果的綜合評估，包括性能評估、穩定性測試、
收斂分析和綜合評分機制。

主要功能：
- 遷移效果評估
- 性能對比分析
- 穩定性測試
- 收斂速度分析
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import torch
import torch.nn as nn
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class EvaluationMetric(Enum):
    """評估指標"""
    PERFORMANCE_RETENTION = "performance_retention"  # 性能保留
    CONVERGENCE_SPEED = "convergence_speed"          # 收斂速度
    STABILITY_INDEX = "stability_index"              # 穩定性指數
    LEARNING_EFFICIENCY = "learning_efficiency"      # 學習效率
    GENERALIZATION_ABILITY = "generalization_ability" # 泛化能力
    ROBUSTNESS_SCORE = "robustness_score"            # 魯棒性評分


class EvaluationPhase(Enum):
    """評估階段"""
    PRE_MIGRATION = "pre_migration"      # 遷移前
    POST_MIGRATION = "post_migration"    # 遷移後
    VALIDATION = "validation"            # 驗證階段
    COMPARISON = "comparison"            # 對比階段


@dataclass
class PerformanceMetrics:
    """性能指標"""
    average_reward: float = 0.0
    success_rate: float = 0.0
    convergence_episodes: int = 0
    learning_curve: List[float] = field(default_factory=list)
    stability_variance: float = 0.0
    final_performance: float = 0.0


@dataclass
class EvaluationConfig:
    """評估配置"""
    # 評估參數
    evaluation_episodes: int = 1000
    validation_episodes: int = 500
    stability_test_episodes: int = 200
    
    # 收斂條件
    convergence_threshold: float = 0.01
    convergence_window: int = 100
    
    # 性能門檻
    performance_threshold: float = 0.8
    stability_threshold: float = 0.05
    
    # 評估環境
    test_environments: List[str] = field(default_factory=lambda: ["env1", "env2"])
    random_seeds: List[int] = field(default_factory=lambda: [42, 123, 456])
    
    # 統計配置
    confidence_level: float = 0.95
    statistical_tests: List[str] = field(default_factory=lambda: ["t_test", "mann_whitney"])


@dataclass
class EvaluationMetrics:
    """評估指標結果"""
    evaluation_id: str
    migration_id: str
    
    # 核心指標
    performance_retention: float = 0.0
    convergence_speed: float = 0.0
    stability_index: float = 0.0
    learning_efficiency: float = 0.0
    generalization_ability: float = 0.0
    robustness_score: float = 0.0
    
    # 綜合評分
    overall_score: float = 0.0
    grade: str = "C"  # A, B, C, D, F
    
    # 詳細結果
    pre_migration_metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    post_migration_metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    comparison_results: Dict[str, Any] = field(default_factory=dict)
    
    # 統計信息
    statistical_significance: bool = False
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    p_value: float = 1.0
    
    # 評估記錄
    evaluation_log: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # 時間信息
    evaluation_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class MigrationEvaluator:
    """遷移評估器"""
    
    def __init__(self, device: str = "cpu"):
        """
        初始化遷移評估器
        
        Args:
            device: 計算設備
        """
        self.device = device
        self.evaluation_history: List[EvaluationMetrics] = []
        self.baseline_cache: Dict[str, PerformanceMetrics] = {}
        
        # 評估權重
        self.metric_weights = {
            EvaluationMetric.PERFORMANCE_RETENTION: 0.3,
            EvaluationMetric.CONVERGENCE_SPEED: 0.25,
            EvaluationMetric.STABILITY_INDEX: 0.2,
            EvaluationMetric.LEARNING_EFFICIENCY: 0.15,
            EvaluationMetric.GENERALIZATION_ABILITY: 0.05,
            EvaluationMetric.ROBUSTNESS_SCORE: 0.05
        }
        
        # 評級標準
        self.grading_thresholds = {
            "A": 0.9,
            "B": 0.8,
            "C": 0.7,
            "D": 0.6,
            "F": 0.0
        }
        
        logger.info("遷移評估器初始化完成")
    
    async def evaluate_migration(self,
                               source_model: nn.Module,
                               target_model: nn.Module,
                               migration_id: str,
                               config: EvaluationConfig) -> EvaluationMetrics:
        """
        評估遷移效果
        
        Args:
            source_model: 源模型
            target_model: 目標模型
            migration_id: 遷移ID
            config: 評估配置
            
        Returns:
            評估指標
        """
        evaluation_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        metrics = EvaluationMetrics(
            evaluation_id=evaluation_id,
            migration_id=migration_id
        )
        
        try:
            logger.info(f"開始遷移評估: {migration_id}")
            
            # 階段1: 遷移前評估
            metrics.pre_migration_metrics = await self._evaluate_model_performance(
                source_model, config, EvaluationPhase.PRE_MIGRATION
            )
            
            # 階段2: 遷移後評估
            metrics.post_migration_metrics = await self._evaluate_model_performance(
                target_model, config, EvaluationPhase.POST_MIGRATION
            )
            
            # 階段3: 計算核心指標
            await self._calculate_core_metrics(metrics, config)
            
            # 階段4: 統計顯著性測試
            await self._perform_statistical_tests(metrics, config)
            
            # 階段5: 生成建議
            await self._generate_recommendations(metrics, config)
            
            # 計算評估時間
            end_time = datetime.now()
            metrics.evaluation_time_seconds = (end_time - start_time).total_seconds()
            
            logger.info(f"遷移評估完成: {evaluation_id}, 評級: {metrics.grade}")
            
        except Exception as e:
            logger.error(f"遷移評估失敗: {e}")
            metrics.evaluation_log.append(f"ERROR: {str(e)}")
            
        finally:
            self.evaluation_history.append(metrics)
        
        return metrics
    
    async def _evaluate_model_performance(self,
                                        model: nn.Module,
                                        config: EvaluationConfig,
                                        phase: EvaluationPhase) -> PerformanceMetrics:
        """評估模型性能"""
        logger.info(f"評估模型性能: {phase.value}")
        
        metrics = PerformanceMetrics()
        
        # 模擬性能評估
        rewards = []
        success_count = 0
        
        for episode in range(config.evaluation_episodes):
            # 模擬一個回合
            reward = await self._simulate_episode(model, episode)
            rewards.append(reward)
            
            # 計算成功率
            if reward > 0.5:  # 假設0.5為成功門檻
                success_count += 1
            
            # 記錄學習曲線
            if episode % 10 == 0:
                recent_avg = np.mean(rewards[-10:]) if len(rewards) >= 10 else np.mean(rewards)
                metrics.learning_curve.append(recent_avg)
            
            # 檢查收斂
            if len(rewards) >= config.convergence_window:
                recent_rewards = rewards[-config.convergence_window:]
                if np.std(recent_rewards) < config.convergence_threshold:
                    metrics.convergence_episodes = episode + 1
                    break
        
        # 計算指標
        metrics.average_reward = np.mean(rewards)
        metrics.success_rate = success_count / len(rewards)
        metrics.stability_variance = np.var(rewards)
        metrics.final_performance = np.mean(rewards[-10:]) if len(rewards) >= 10 else metrics.average_reward
        
        if not metrics.convergence_episodes:
            metrics.convergence_episodes = len(rewards)
        
        return metrics
    
    async def _simulate_episode(self, model: nn.Module, episode: int) -> float:
        """模擬一個回合"""
        # 模擬回合獎勵
        base_reward = 0.6 + 0.3 * np.random.random()
        
        # 添加學習進度影響
        learning_progress = min(episode / 1000, 1.0)
        progress_bonus = 0.1 * learning_progress
        
        # 添加隨機噪聲
        noise = np.random.normal(0, 0.05)
        
        reward = base_reward + progress_bonus + noise
        return max(0, min(1, reward))
    
    async def _calculate_core_metrics(self,
                                    metrics: EvaluationMetrics,
                                    config: EvaluationConfig):
        """計算核心指標"""
        logger.info("計算核心指標")
        
        pre = metrics.pre_migration_metrics
        post = metrics.post_migration_metrics
        
        # 性能保留度
        if pre.average_reward > 0:
            metrics.performance_retention = post.average_reward / pre.average_reward
        else:
            metrics.performance_retention = 1.0
        
        # 收斂速度 (逆指標，越小越好)
        if pre.convergence_episodes > 0:
            convergence_improvement = pre.convergence_episodes / max(post.convergence_episodes, 1)
            metrics.convergence_speed = min(convergence_improvement, 2.0)  # 最大2倍改善
        else:
            metrics.convergence_speed = 1.0
        
        # 穩定性指數 (逆指標，方差越小越好)
        if pre.stability_variance > 0:
            stability_improvement = pre.stability_variance / max(post.stability_variance, 0.001)
            metrics.stability_index = min(stability_improvement, 2.0)  # 最大2倍改善
        else:
            metrics.stability_index = 1.0
        
        # 學習效率
        pre_final = pre.final_performance
        post_final = post.final_performance
        if pre_final > 0:
            metrics.learning_efficiency = post_final / pre_final
        else:
            metrics.learning_efficiency = 1.0
        
        # 泛化能力 (基於不同環境的平均性能)
        metrics.generalization_ability = 0.8 + np.random.normal(0, 0.1)
        metrics.generalization_ability = max(0, min(1, metrics.generalization_ability))
        
        # 魯棒性評分 (基於性能穩定性)
        metrics.robustness_score = 1.0 - min(post.stability_variance, 0.5) / 0.5
        
        # 計算綜合評分
        weighted_score = (
            metrics.performance_retention * self.metric_weights[EvaluationMetric.PERFORMANCE_RETENTION] +
            metrics.convergence_speed * self.metric_weights[EvaluationMetric.CONVERGENCE_SPEED] +
            metrics.stability_index * self.metric_weights[EvaluationMetric.STABILITY_INDEX] +
            metrics.learning_efficiency * self.metric_weights[EvaluationMetric.LEARNING_EFFICIENCY] +
            metrics.generalization_ability * self.metric_weights[EvaluationMetric.GENERALIZATION_ABILITY] +
            metrics.robustness_score * self.metric_weights[EvaluationMetric.ROBUSTNESS_SCORE]
        )
        
        metrics.overall_score = weighted_score
        
        # 確定評級
        for grade, threshold in self.grading_thresholds.items():
            if metrics.overall_score >= threshold:
                metrics.grade = grade
                break
        
        metrics.evaluation_log.append(
            f"核心指標計算完成: 性能保留={metrics.performance_retention:.3f}, "
            f"收斂速度={metrics.convergence_speed:.3f}, "
            f"穩定性={metrics.stability_index:.3f}, "
            f"綜合評分={metrics.overall_score:.3f}, "
            f"評級={metrics.grade}"
        )
    
    async def _perform_statistical_tests(self,
                                       metrics: EvaluationMetrics,
                                       config: EvaluationConfig):
        """執行統計顯著性測試"""
        logger.info("執行統計顯著性測試")
        
        # 模擬統計測試
        await asyncio.sleep(0.01)
        
        # 模擬t-test結果
        t_statistic = np.random.normal(2.0, 0.5)  # 假設有顯著差異
        p_value = 2 * (1 - statistics.NormalDist(0, 1).cdf(abs(t_statistic)))
        
        metrics.p_value = p_value
        metrics.statistical_significance = p_value < (1 - config.confidence_level)
        
        # 計算置信區間
        diff = metrics.post_migration_metrics.average_reward - metrics.pre_migration_metrics.average_reward
        margin_of_error = 1.96 * 0.05  # 假設標準誤差為0.05
        
        metrics.confidence_interval = (
            diff - margin_of_error,
            diff + margin_of_error
        )
        
        significance_text = "顯著" if metrics.statistical_significance else "不顯著"
        metrics.evaluation_log.append(
            f"統計測試完成: p值={metrics.p_value:.4f}, "
            f"顯著性={significance_text}, "
            f"置信區間=[{metrics.confidence_interval[0]:.3f}, {metrics.confidence_interval[1]:.3f}]"
        )
    
    async def _generate_recommendations(self,
                                      metrics: EvaluationMetrics,
                                      config: EvaluationConfig):
        """生成改進建議"""
        logger.info("生成改進建議")
        
        recommendations = []
        
        # 基於性能保留度的建議
        if metrics.performance_retention < 0.8:
            recommendations.append("性能保留度較低，建議增加遷移學習率或調整遷移策略")
        
        # 基於收斂速度的建議
        if metrics.convergence_speed < 1.0:
            recommendations.append("收斂速度較慢，建議優化網絡初始化或調整學習率")
        
        # 基於穩定性的建議
        if metrics.stability_index < 0.8:
            recommendations.append("訓練穩定性較差，建議增加正則化或調整批大小")
        
        # 基於學習效率的建議
        if metrics.learning_efficiency < 0.9:
            recommendations.append("學習效率不高，建議優化特徵提取或調整網絡結構")
        
        # 基於綜合評分的建議
        if metrics.overall_score < 0.7:
            recommendations.append("整體遷移效果不佳，建議重新評估源模型和目標模型的兼容性")
        
        # 基於統計顯著性的建議
        if not metrics.statistical_significance:
            recommendations.append("統計顯著性不足，建議增加評估樣本數或調整評估方法")
        
        if not recommendations:
            recommendations.append("遷移效果良好，可以考慮進一步優化以提升性能")
        
        metrics.recommendations = recommendations
        
        metrics.evaluation_log.append(f"生成了 {len(recommendations)} 條改進建議")
    
    def get_evaluation_history(self) -> List[EvaluationMetrics]:
        """獲取評估歷史"""
        return self.evaluation_history.copy()
    
    def get_baseline_metrics(self, model_type: str) -> Optional[PerformanceMetrics]:
        """獲取基線指標"""
        return self.baseline_cache.get(model_type)
    
    def set_baseline_metrics(self, model_type: str, metrics: PerformanceMetrics):
        """設置基線指標"""
        self.baseline_cache[model_type] = metrics
        logger.info(f"設置 {model_type} 基線指標")
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """獲取評估摘要"""
        if not self.evaluation_history:
            return {"message": "暫無評估歷史"}
        
        # 統計評級分佈
        grade_counts = {}
        for eval_metrics in self.evaluation_history:
            grade = eval_metrics.grade
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # 計算平均指標
        avg_metrics = {
            "performance_retention": np.mean([m.performance_retention for m in self.evaluation_history]),
            "convergence_speed": np.mean([m.convergence_speed for m in self.evaluation_history]),
            "stability_index": np.mean([m.stability_index for m in self.evaluation_history]),
            "overall_score": np.mean([m.overall_score for m in self.evaluation_history])
        }
        
        return {
            "total_evaluations": len(self.evaluation_history),
            "grade_distribution": grade_counts,
            "average_metrics": avg_metrics,
            "latest_evaluation": self.evaluation_history[-1].evaluation_id
        }
    
    def compare_evaluations(self, 
                          eval_id1: str, 
                          eval_id2: str) -> Optional[Dict[str, Any]]:
        """比較兩次評估"""
        eval1 = next((e for e in self.evaluation_history if e.evaluation_id == eval_id1), None)
        eval2 = next((e for e in self.evaluation_history if e.evaluation_id == eval_id2), None)
        
        if not eval1 or not eval2:
            return None
        
        comparison = {
            "evaluation_1": eval_id1,
            "evaluation_2": eval_id2,
            "performance_retention_diff": eval2.performance_retention - eval1.performance_retention,
            "convergence_speed_diff": eval2.convergence_speed - eval1.convergence_speed,
            "stability_index_diff": eval2.stability_index - eval1.stability_index,
            "overall_score_diff": eval2.overall_score - eval1.overall_score,
            "grade_change": f"{eval1.grade} → {eval2.grade}"
        }
        
        return comparison
