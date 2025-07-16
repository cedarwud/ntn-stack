"""
智能選擇器 - Phase 3 核心組件

整合環境分析、算法匹配和性能預測，提供完整的智能算法選擇解決方案，
支援多種選擇策略和動態優化。

主要功能：
- 綜合算法選擇
- 多策略集成
- 動態優化
- 決策解釋
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import json

from .environment_analyzer import EnvironmentAnalyzer, EnvironmentFeatures
from .algorithm_matcher import AlgorithmMatcher, MatchingResult
from .performance_predictor import PerformancePredictor, PredictionResult, PredictionModel

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """選擇策略"""
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    CONVERGENCE_OPTIMIZED = "convergence_optimized"
    STABILITY_OPTIMIZED = "stability_optimized"
    BALANCED = "balanced"
    EXPLORATION_FOCUSED = "exploration_focused"
    CONSERVATIVE = "conservative"


class SelectionMode(Enum):
    """選擇模式"""
    SINGLE_BEST = "single_best"
    TOP_K = "top_k"
    ENSEMBLE = "ensemble"
    ADAPTIVE = "adaptive"


@dataclass
class SelectionConfig:
    """選擇配置"""
    strategy: SelectionStrategy = SelectionStrategy.BALANCED
    mode: SelectionMode = SelectionMode.SINGLE_BEST
    
    # 選擇參數
    top_k: int = 3
    confidence_threshold: float = 0.7
    diversity_bonus: float = 0.1
    
    # 權重配置
    performance_weight: float = 0.4
    convergence_weight: float = 0.3
    stability_weight: float = 0.2
    confidence_weight: float = 0.1
    
    # 約束條件
    max_training_time: Optional[int] = None
    min_performance_threshold: float = 0.6
    required_stability: float = 0.5
    
    # 預測配置
    prediction_model: PredictionModel = PredictionModel.ENSEMBLE
    enable_uncertainty_quantification: bool = True


@dataclass
class SelectionResult:
    """選擇結果"""
    selection_id: str
    environment_id: str
    strategy: SelectionStrategy
    mode: SelectionMode
    
    # 選擇結果
    selected_algorithms: List[str] = field(default_factory=list)
    selection_scores: Dict[str, float] = field(default_factory=dict)
    
    # 詳細分析
    environment_analysis: Optional[EnvironmentFeatures] = None
    matching_results: Dict[str, MatchingResult] = field(default_factory=dict)
    prediction_results: Dict[str, PredictionResult] = field(default_factory=dict)
    
    # 決策信息
    decision_confidence: float = 0.0
    selection_rationale: List[str] = field(default_factory=list)
    alternative_recommendations: List[str] = field(default_factory=list)
    
    # 風險評估
    risk_assessment: Dict[str, float] = field(default_factory=dict)
    uncertainty_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 優化建議
    optimization_suggestions: List[str] = field(default_factory=list)
    parameter_recommendations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 統計信息
    selection_time_seconds: float = 0.0
    analyzed_algorithms: int = 0
    
    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)


class IntelligentSelector:
    """智能選擇器"""
    
    def __init__(self, device: str = "cpu"):
        """
        初始化智能選擇器
        
        Args:
            device: 計算設備
        """
        self.device = device
        self.selection_history: List[SelectionResult] = []
        
        # 初始化核心組件
        self.environment_analyzer = EnvironmentAnalyzer(device)
        self.algorithm_matcher = AlgorithmMatcher()
        self.performance_predictor = PerformancePredictor(device)
        
        # 算法池
        self.algorithm_pool = ["DQN", "PPO", "SAC", "A2C", "TD3", "DDPG", "TRPO", "IMPALA"]
        
        # 選擇策略配置
        self.strategy_configs = {
            SelectionStrategy.PERFORMANCE_OPTIMIZED: {
                "performance_weight": 0.6,
                "convergence_weight": 0.2,
                "stability_weight": 0.1,
                "confidence_weight": 0.1
            },
            SelectionStrategy.CONVERGENCE_OPTIMIZED: {
                "performance_weight": 0.2,
                "convergence_weight": 0.6,
                "stability_weight": 0.1,
                "confidence_weight": 0.1
            },
            SelectionStrategy.STABILITY_OPTIMIZED: {
                "performance_weight": 0.2,
                "convergence_weight": 0.2,
                "stability_weight": 0.5,
                "confidence_weight": 0.1
            },
            SelectionStrategy.BALANCED: {
                "performance_weight": 0.3,
                "convergence_weight": 0.3,
                "stability_weight": 0.3,
                "confidence_weight": 0.1
            },
            SelectionStrategy.EXPLORATION_FOCUSED: {
                "performance_weight": 0.2,
                "convergence_weight": 0.2,
                "stability_weight": 0.2,
                "confidence_weight": 0.4
            },
            SelectionStrategy.CONSERVATIVE: {
                "performance_weight": 0.25,
                "convergence_weight": 0.25,
                "stability_weight": 0.4,
                "confidence_weight": 0.1
            }
        }
        
        logger.info("智能選擇器初始化完成")
    
    async def select_algorithm(self,
                             environment_data: Dict[str, Any],
                             config: SelectionConfig) -> SelectionResult:
        """
        智能選擇算法
        
        Args:
            environment_data: 環境數據
            config: 選擇配置
            
        Returns:
            選擇結果
        """
        selection_id = f"sel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"開始智能算法選擇: {config.strategy.value}")
        
        try:
            # 1. 環境分析
            logger.info("執行環境分析...")
            environment_features = await self.environment_analyzer.analyze_environment(
                environment_data
            )
            
            # 2. 算法匹配
            logger.info("執行算法匹配...")
            matching_results = {}
            for algorithm in self.algorithm_pool:
                match_result = await self.algorithm_matcher.match_algorithm(
                    algorithm, environment_features
                )
                matching_results[algorithm] = match_result
            
            # 3. 性能預測
            logger.info("執行性能預測...")
            prediction_results = await self.performance_predictor.batch_predict(
                self.algorithm_pool, environment_features, config.prediction_model
            )
            
            # 4. 綜合評分
            logger.info("計算綜合評分...")
            scores = self._calculate_comprehensive_scores(
                matching_results, prediction_results, config
            )
            
            # 5. 選擇算法
            logger.info("選擇最佳算法...")
            selected_algorithms = self._select_best_algorithms(
                scores, config
            )
            
            # 6. 生成決策分析
            logger.info("生成決策分析...")
            decision_analysis = self._generate_decision_analysis(
                selected_algorithms, matching_results, prediction_results, config
            )
            
            # 7. 風險評估
            logger.info("執行風險評估...")
            risk_assessment = self._assess_risks(
                selected_algorithms, prediction_results, environment_features
            )
            
            # 8. 優化建議
            logger.info("生成優化建議...")
            optimization_suggestions = self._generate_optimization_suggestions(
                selected_algorithms, environment_features, prediction_results
            )
            
            # 計算選擇時間
            end_time = datetime.now()
            selection_time = (end_time - start_time).total_seconds()
            
            # 構建結果
            result = SelectionResult(
                selection_id=selection_id,
                environment_id=environment_features.environment_id,
                strategy=config.strategy,
                mode=config.mode,
                selected_algorithms=selected_algorithms,
                selection_scores=scores,
                environment_analysis=environment_features,
                matching_results=matching_results,
                prediction_results=prediction_results,
                decision_confidence=decision_analysis["confidence"],
                selection_rationale=decision_analysis["rationale"],
                alternative_recommendations=decision_analysis["alternatives"],
                risk_assessment=risk_assessment,
                uncertainty_metrics=self._calculate_uncertainty_metrics(prediction_results),
                optimization_suggestions=optimization_suggestions,
                parameter_recommendations=self._generate_parameter_recommendations(
                    selected_algorithms, environment_features
                ),
                selection_time_seconds=selection_time,
                analyzed_algorithms=len(self.algorithm_pool)
            )
            
            # 保存選擇歷史
            self.selection_history.append(result)
            
            logger.info(f"智能選擇完成: {selection_id}")
            return result
            
        except Exception as e:
            logger.error(f"智能選擇失敗: {e}")
            # 返回默認選擇
            return SelectionResult(
                selection_id=selection_id,
                environment_id="unknown",
                strategy=config.strategy,
                mode=config.mode,
                selected_algorithms=["PPO"],  # 默認選擇
                selection_rationale=[f"選擇失敗，使用默認算法: {str(e)}"]
            )
    
    def _calculate_comprehensive_scores(self,
                                      matching_results: Dict[str, MatchingResult],
                                      prediction_results: Dict[str, PredictionResult],
                                      config: SelectionConfig) -> Dict[str, float]:
        """計算綜合評分"""
        scores = {}
        
        # 獲取策略權重
        weights = self.strategy_configs.get(config.strategy, {
            "performance_weight": 0.3,
            "convergence_weight": 0.3,
            "stability_weight": 0.3,
            "confidence_weight": 0.1
        })
        
        for algorithm in self.algorithm_pool:
            if algorithm not in matching_results or algorithm not in prediction_results:
                scores[algorithm] = 0.0
                continue
            
            match_result = matching_results[algorithm]
            pred_result = prediction_results[algorithm]
            
            # 匹配分數
            match_score = match_result.compatibility_score
            
            # 性能分數
            performance_score = pred_result.predicted_performance
            
            # 收斂分數（反向，收斂越快分數越高）
            max_convergence = 2000  # 假設最大收斂回合
            convergence_score = 1.0 - (pred_result.predicted_convergence / max_convergence)
            convergence_score = max(0.0, min(1.0, convergence_score))
            
            # 穩定性分數
            stability_score = pred_result.stability_score
            
            # 置信度分數
            confidence_score = pred_result.confidence_score
            
            # 綜合評分
            comprehensive_score = (
                match_score * 0.2 +  # 匹配權重
                performance_score * weights.get("performance_weight", 0.3) +
                convergence_score * weights.get("convergence_weight", 0.3) +
                stability_score * weights.get("stability_weight", 0.3) +
                confidence_score * weights.get("confidence_weight", 0.1)
            )
            
            # 應用約束條件
            if config.max_training_time:
                if pred_result.predicted_convergence > config.max_training_time:
                    comprehensive_score *= 0.5  # 懲罰超時
            
            if pred_result.predicted_performance < config.min_performance_threshold:
                comprehensive_score *= 0.3  # 懲罰低性能
            
            if pred_result.stability_score < config.required_stability:
                comprehensive_score *= 0.7  # 懲罰不穩定
            
            scores[algorithm] = comprehensive_score
        
        return scores
    
    def _select_best_algorithms(self,
                              scores: Dict[str, float],
                              config: SelectionConfig) -> List[str]:
        """選擇最佳算法"""
        # 按分數排序
        sorted_algorithms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if config.mode == SelectionMode.SINGLE_BEST:
            # 選擇單個最佳算法
            return [sorted_algorithms[0][0]] if sorted_algorithms else []
        
        elif config.mode == SelectionMode.TOP_K:
            # 選擇前K個算法
            selected = []
            for algo, score in sorted_algorithms[:config.top_k]:
                if score >= config.confidence_threshold:
                    selected.append(algo)
            return selected
        
        elif config.mode == SelectionMode.ENSEMBLE:
            # 選擇集成算法
            selected = []
            for algo, score in sorted_algorithms:
                if score >= config.confidence_threshold and len(selected) < 3:
                    selected.append(algo)
            return selected
        
        elif config.mode == SelectionMode.ADAPTIVE:
            # 自適應選擇
            if sorted_algorithms[0][1] > 0.9:  # 高置信度，選擇單個
                return [sorted_algorithms[0][0]]
            elif sorted_algorithms[0][1] > 0.7:  # 中等置信度，選擇前2個
                return [algo for algo, score in sorted_algorithms[:2] if score >= config.confidence_threshold]
            else:  # 低置信度，選擇前3個
                return [algo for algo, score in sorted_algorithms[:3] if score >= config.confidence_threshold]
        
        return []
    
    def _generate_decision_analysis(self,
                                  selected_algorithms: List[str],
                                  matching_results: Dict[str, MatchingResult],
                                  prediction_results: Dict[str, PredictionResult],
                                  config: SelectionConfig) -> Dict[str, Any]:
        """生成決策分析"""
        analysis = {
            "confidence": 0.0,
            "rationale": [],
            "alternatives": []
        }
        
        if not selected_algorithms:
            analysis["confidence"] = 0.0
            analysis["rationale"] = ["無法找到合適的算法"]
            return analysis
        
        # 計算決策置信度
        if selected_algorithms:
            primary_algo = selected_algorithms[0]
            if primary_algo in prediction_results:
                pred_result = prediction_results[primary_algo]
                analysis["confidence"] = pred_result.confidence_score
        
        # 生成決策理由
        for algo in selected_algorithms:
            if algo in matching_results and algo in prediction_results:
                match_result = matching_results[algo]
                pred_result = prediction_results[algo]
                
                rationale = f"{algo}: 匹配度 {match_result.compatibility_score:.2f}, "
                rationale += f"預測性能 {pred_result.predicted_performance:.2f}, "
                rationale += f"預測收斂 {pred_result.predicted_convergence} 回合"
                
                analysis["rationale"].append(rationale)
                
                # 添加具體原因
                if match_result.matching_reasons:
                    analysis["rationale"].extend(match_result.matching_reasons)
                
                if pred_result.prediction_rationale:
                    analysis["rationale"].extend(pred_result.prediction_rationale)
        
        # 生成替代推薦
        all_scores = {}
        for algo in matching_results:
            if algo not in selected_algorithms:
                if algo in prediction_results:
                    pred_result = prediction_results[algo]
                    all_scores[algo] = pred_result.predicted_performance
        
        # 排序並選擇前2個作為替代
        sorted_alternatives = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        analysis["alternatives"] = [algo for algo, _ in sorted_alternatives[:2]]
        
        return analysis
    
    def _assess_risks(self,
                     selected_algorithms: List[str],
                     prediction_results: Dict[str, PredictionResult],
                     environment_features: EnvironmentFeatures) -> Dict[str, float]:
        """評估風險"""
        risks = {
            "convergence_risk": 0.0,
            "stability_risk": 0.0,
            "performance_risk": 0.0,
            "overall_risk": 0.0
        }
        
        if not selected_algorithms:
            return {k: 1.0 for k in risks}
        
        # 基於預測結果評估風險
        for algo in selected_algorithms:
            if algo in prediction_results:
                pred_result = prediction_results[algo]
                
                # 收斂風險
                if pred_result.predicted_convergence > 1000:
                    risks["convergence_risk"] += 0.3
                
                # 穩定性風險
                if pred_result.stability_score < 0.7:
                    risks["stability_risk"] += 0.4
                
                # 性能風險
                if pred_result.predicted_performance < 0.7:
                    risks["performance_risk"] += 0.3
                
                # 不確定性風險
                uncertainty_span = pred_result.uncertainty_range[1] - pred_result.uncertainty_range[0]
                if uncertainty_span > 0.2:
                    risks["overall_risk"] += 0.2
        
        # 基於環境特徵評估風險
        if environment_features.overall_complexity > 0.8:
            risks["overall_risk"] += 0.3
        
        if environment_features.learning_difficulty > 0.7:
            risks["convergence_risk"] += 0.2
        
        if environment_features.dynamics_features.non_stationarity > 0.5:
            risks["stability_risk"] += 0.3
        
        # 歸一化風險值
        for key in risks:
            risks[key] = min(1.0, risks[key])
        
        # 計算綜合風險
        risks["overall_risk"] = (
            risks["convergence_risk"] * 0.3 +
            risks["stability_risk"] * 0.4 +
            risks["performance_risk"] * 0.3
        )
        
        return risks
    
    def _calculate_uncertainty_metrics(self,
                                     prediction_results: Dict[str, PredictionResult]) -> Dict[str, float]:
        """計算不確定性指標"""
        metrics = {
            "prediction_variance": 0.0,
            "confidence_variance": 0.0,
            "uncertainty_span": 0.0,
            "model_agreement": 0.0
        }
        
        if not prediction_results:
            return metrics
        
        # 預測方差
        performances = [r.predicted_performance for r in prediction_results.values()]
        if len(performances) > 1:
            metrics["prediction_variance"] = np.var(performances)
        
        # 置信度方差
        confidences = [r.confidence_score for r in prediction_results.values()]
        if len(confidences) > 1:
            metrics["confidence_variance"] = np.var(confidences)
        
        # 不確定性範圍
        uncertainty_spans = [
            r.uncertainty_range[1] - r.uncertainty_range[0]
            for r in prediction_results.values()
        ]
        if uncertainty_spans:
            metrics["uncertainty_span"] = np.mean(uncertainty_spans)
        
        # 模型一致性
        model_confidences = [r.model_confidence for r in prediction_results.values()]
        if model_confidences:
            metrics["model_agreement"] = np.mean(model_confidences)
        
        return metrics
    
    def _generate_optimization_suggestions(self,
                                         selected_algorithms: List[str],
                                         environment_features: EnvironmentFeatures,
                                         prediction_results: Dict[str, PredictionResult]) -> List[str]:
        """生成優化建議"""
        suggestions = []
        
        # 基於環境特徵的建議
        if environment_features.overall_complexity > 0.8:
            suggestions.append("考慮使用更複雜的神經網絡架構")
            suggestions.append("增加訓練時間和資源")
        
        if environment_features.reward_features.sparsity > 0.7:
            suggestions.append("考慮使用好奇心驅動的學習")
            suggestions.append("實施獎勵塑造技術")
        
        if environment_features.dynamics_features.non_stationarity > 0.6:
            suggestions.append("使用自適應學習率")
            suggestions.append("考慮在線學習策略")
        
        # 基於選中算法的建議
        for algo in selected_algorithms:
            if algo == "DQN":
                suggestions.append("DQN: 考慮使用Double DQN或Dueling DQN")
                suggestions.append("DQN: 調整經驗回放緩衝區大小")
            elif algo == "PPO":
                suggestions.append("PPO: 調整clip範圍和學習率")
                suggestions.append("PPO: 考慮使用GAE進行優勢估計")
            elif algo == "SAC":
                suggestions.append("SAC: 調整溫度參數")
                suggestions.append("SAC: 考慮自動調整熵係數")
        
        # 基於預測結果的建議
        for algo in selected_algorithms:
            if algo in prediction_results:
                pred_result = prediction_results[algo]
                
                if pred_result.predicted_convergence > 1000:
                    suggestions.append(f"{algo}: 考慮使用課程學習")
                
                if pred_result.stability_score < 0.7:
                    suggestions.append(f"{algo}: 增加正則化")
                
                if pred_result.confidence_score < 0.7:
                    suggestions.append(f"{algo}: 考慮集成學習")
        
        return list(set(suggestions))  # 去重
    
    def _generate_parameter_recommendations(self,
                                          selected_algorithms: List[str],
                                          environment_features: EnvironmentFeatures) -> Dict[str, Dict[str, Any]]:
        """生成參數推薦"""
        recommendations = {}
        
        for algo in selected_algorithms:
            if algo == "DQN":
                recommendations[algo] = {
                    "learning_rate": 0.001 if environment_features.overall_complexity > 0.7 else 0.01,
                    "batch_size": 64 if environment_features.overall_complexity > 0.7 else 32,
                    "replay_buffer_size": 100000,
                    "target_update_frequency": 1000,
                    "epsilon_decay": 0.995
                }
            elif algo == "PPO":
                recommendations[algo] = {
                    "learning_rate": 0.0003,
                    "batch_size": 256,
                    "n_epochs": 10,
                    "clip_range": 0.2,
                    "gamma": 0.99,
                    "gae_lambda": 0.95
                }
            elif algo == "SAC":
                recommendations[algo] = {
                    "learning_rate": 0.0003,
                    "batch_size": 256,
                    "tau": 0.005,
                    "gamma": 0.99,
                    "alpha": "auto"
                }
        
        return recommendations
    
    def get_selection_history(self) -> List[SelectionResult]:
        """獲取選擇歷史"""
        return self.selection_history.copy()
    
    def get_algorithm_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """獲取算法性能統計"""
        stats = {}
        
        for algo in self.algorithm_pool:
            selections = [
                s for s in self.selection_history
                if algo in s.selected_algorithms
            ]
            
            if selections:
                stats[algo] = {
                    "selection_count": len(selections),
                    "avg_score": np.mean([
                        s.selection_scores.get(algo, 0.0) for s in selections
                    ]),
                    "avg_confidence": np.mean([
                        s.decision_confidence for s in selections
                    ])
                }
        
        return stats
    
    def update_algorithm_pool(self, new_algorithms: List[str]):
        """更新算法池"""
        self.algorithm_pool = list(set(self.algorithm_pool + new_algorithms))
        logger.info(f"更新算法池: {len(self.algorithm_pool)} 個算法")
    
    async def comparative_analysis(self,
                                 environment_data: Dict[str, Any],
                                 algorithms: List[str]) -> Dict[str, Any]:
        """比較分析多個算法"""
        logger.info(f"開始比較分析: {len(algorithms)} 個算法")
        
        # 環境分析
        environment_features = await self.environment_analyzer.analyze_environment(
            environment_data
        )
        
        # 批量匹配和預測
        matching_results = {}
        prediction_results = {}
        
        for algo in algorithms:
            matching_results[algo] = await self.algorithm_matcher.match_algorithm(
                algo, environment_features
            )
            prediction_results[algo] = await self.performance_predictor.predict_performance(
                algo, environment_features, PredictionModel.ENSEMBLE
            )
        
        # 生成比較報告
        comparison = {
            "environment_summary": {
                "complexity": environment_features.overall_complexity,
                "learning_difficulty": environment_features.learning_difficulty,
                "key_characteristics": []
            },
            "algorithm_rankings": {},
            "detailed_comparison": {},
            "recommendations": []
        }
        
        # 算法排名
        scores = {}
        for algo in algorithms:
            if algo in matching_results and algo in prediction_results:
                match_score = matching_results[algo].compatibility_score
                pred_score = prediction_results[algo].predicted_performance
                scores[algo] = (match_score + pred_score) / 2
        
        comparison["algorithm_rankings"] = dict(
            sorted(scores.items(), key=lambda x: x[1], reverse=True)
        )
        
        # 詳細比較
        for algo in algorithms:
            if algo in matching_results and algo in prediction_results:
                comparison["detailed_comparison"][algo] = {
                    "compatibility": matching_results[algo].compatibility_score,
                    "predicted_performance": prediction_results[algo].predicted_performance,
                    "predicted_convergence": prediction_results[algo].predicted_convergence,
                    "stability": prediction_results[algo].stability_score,
                    "confidence": prediction_results[algo].confidence_score,
                    "pros": matching_results[algo].matching_reasons,
                    "cons": []
                }
        
        return comparison
