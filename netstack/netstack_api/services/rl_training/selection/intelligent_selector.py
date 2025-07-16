"""
智能選擇器 - Phase 3 核心組件

整合環境分析、算法匹配和性能預測功能，提供完整的智能算法選擇服務。
支援動態算法切換和實時性能監控。

主要功能：
- 綜合智能選擇
- 動態算法切換
- 實時性能監控
- 選擇效果評估
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
import json

from .environment_analyzer import EnvironmentAnalyzer, EnvironmentFeatures
from .algorithm_matcher import AlgorithmMatcher, MatchingStrategy
from .performance_predictor import PerformancePredictor, PredictionModel

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """選擇策略"""
    BEST_MATCH = "best_match"                    # 最佳匹配
    ENSEMBLE = "ensemble"                        # 集成選擇
    ADAPTIVE = "adaptive"                        # 自適應選擇
    CONSERVATIVE = "conservative"                # 保守選擇
    EXPLORATORY = "exploratory"                  # 探索性選擇


class SwitchingTrigger(Enum):
    """切換觸發器"""
    PERFORMANCE_DEGRADATION = "performance_degradation"  # 性能下降
    CONVERGENCE_STAGNATION = "convergence_stagnation"    # 收斂停滯
    ENVIRONMENT_CHANGE = "environment_change"            # 環境變化
    SCHEDULED_SWITCH = "scheduled_switch"                # 計劃切換
    MANUAL_TRIGGER = "manual_trigger"                    # 手動觸發


@dataclass
class SelectionConfig:
    """選擇配置"""
    strategy: SelectionStrategy = SelectionStrategy.BEST_MATCH
    
    # 選擇參數
    confidence_threshold: float = 0.8
    performance_threshold: float = 0.75
    switch_cooldown_episodes: int = 100
    
    # 預測參數
    prediction_horizon: int = 500
    prediction_confidence: float = 0.9
    
    # 切換條件
    switching_triggers: List[SwitchingTrigger] = field(default_factory=lambda: [
        SwitchingTrigger.PERFORMANCE_DEGRADATION,
        SwitchingTrigger.CONVERGENCE_STAGNATION
    ])
    
    # 性能監控
    monitoring_window: int = 100
    degradation_threshold: float = 0.1
    stagnation_threshold: float = 0.05
    
    # 安全設置
    fallback_algorithm: str = "DQN"
    max_switches_per_session: int = 3
    
    # 評估設置
    evaluation_episodes: int = 100
    validation_frequency: int = 50


@dataclass
class AlgorithmCandidate:
    """算法候選"""
    algorithm_name: str
    confidence_score: float
    predicted_performance: float
    
    # 匹配信息
    matching_score: float
    suitability_reasons: List[str] = field(default_factory=list)
    
    # 預測信息
    convergence_episodes: int = 0
    stability_score: float = 0.0
    
    # 風險評估
    risk_score: float = 0.0
    uncertainty: float = 0.0


@dataclass
class SelectionResult:
    """選擇結果"""
    selection_id: str
    environment_id: str
    
    # 選擇結果
    selected_algorithm: str
    confidence_score: float
    selection_reason: str
    
    # 候選算法
    candidates: List[AlgorithmCandidate] = field(default_factory=list)
    
    # 環境分析
    environment_features: Optional[EnvironmentFeatures] = None
    
    # 性能預測
    predicted_performance: float = 0.0
    convergence_prediction: int = 0
    
    # 選擇統計
    selection_time_seconds: float = 0.0
    analysis_time_seconds: float = 0.0
    
    # 歷史信息
    previous_selections: List[str] = field(default_factory=list)
    switch_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 監控信息
    monitoring_active: bool = False
    next_evaluation_episode: int = 0
    
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
        
        # 初始化組件
        self.environment_analyzer = EnvironmentAnalyzer()
        self.algorithm_matcher = AlgorithmMatcher()
        self.performance_predictor = PerformancePredictor()
        
        # 選擇歷史
        self.selection_history: List[SelectionResult] = []
        self.active_sessions: Dict[str, SelectionResult] = {}
        
        # 性能監控
        self.performance_monitors: Dict[str, deque] = {}
        
        # 算法性能統計
        self.algorithm_performance_stats: Dict[str, Dict[str, float]] = {
            "DQN": {"success_rate": 0.75, "avg_convergence": 800, "stability": 0.8},
            "PPO": {"success_rate": 0.80, "avg_convergence": 600, "stability": 0.85},
            "SAC": {"success_rate": 0.85, "avg_convergence": 400, "stability": 0.9}
        }
        
        logger.info("智能選擇器初始化完成")
    
    async def select_algorithm(self,
                             environment_data: Dict[str, Any],
                             environment_id: str,
                             config: SelectionConfig) -> SelectionResult:
        """
        智能選擇算法
        
        Args:
            environment_data: 環境數據
            environment_id: 環境ID
            config: 選擇配置
            
        Returns:
            選擇結果
        """
        selection_id = f"selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        try:
            logger.info(f"開始智能算法選擇: {environment_id}")
            
            # 階段1: 環境分析
            analysis_start = datetime.now()
            analysis_result = await self.environment_analyzer.analyze_environment(
                environment_data, environment_id
            )
            analysis_time = (datetime.now() - analysis_start).total_seconds()
            
            # 階段2: 算法匹配
            matching_result = await self.algorithm_matcher.match_algorithms(
                analysis_result.environment_features,
                MatchingStrategy.COMPREHENSIVE
            )
            
            # 階段3: 性能預測
            prediction_results = await self._predict_algorithm_performance(
                analysis_result.environment_features,
                matching_result.matched_algorithms,
                config
            )
            
            # 階段4: 生成候選算法
            candidates = await self._generate_candidates(
                matching_result,
                prediction_results,
                config
            )
            
            # 階段5: 執行選擇策略
            selected_algorithm, confidence, reason = await self._execute_selection_strategy(
                candidates,
                config
            )
            
            # 階段6: 構建結果
            selection_time = (datetime.now() - start_time).total_seconds()
            
            result = SelectionResult(
                selection_id=selection_id,
                environment_id=environment_id,
                selected_algorithm=selected_algorithm,
                confidence_score=confidence,
                selection_reason=reason,
                candidates=candidates,
                environment_features=analysis_result.environment_features,
                predicted_performance=prediction_results.get(selected_algorithm, {}).get("performance", 0.0),
                convergence_prediction=prediction_results.get(selected_algorithm, {}).get("convergence", 0),
                selection_time_seconds=selection_time,
                analysis_time_seconds=analysis_time,
                monitoring_active=True,
                next_evaluation_episode=config.validation_frequency
            )
            
            # 階段7: 設置監控
            await self._setup_monitoring(result, config)
            
            # 保存結果
            self.selection_history.append(result)
            self.active_sessions[environment_id] = result
            
            logger.info(f"算法選擇完成: {selected_algorithm} (置信度: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"算法選擇失敗: {e}")
            # 返回默認選擇
            return SelectionResult(
                selection_id=selection_id,
                environment_id=environment_id,
                selected_algorithm=config.fallback_algorithm,
                confidence_score=0.5,
                selection_reason=f"選擇失敗，使用默認算法: {str(e)}",
                selection_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    async def _predict_algorithm_performance(self,
                                           environment_features: EnvironmentFeatures,
                                           matched_algorithms: List[str],
                                           config: SelectionConfig) -> Dict[str, Dict[str, float]]:
        """預測算法性能"""
        logger.info("預測算法性能")
        
        predictions = {}
        
        for algorithm in matched_algorithms:
            # 使用性能預測器
            prediction_result = await self.performance_predictor.predict_performance(
                algorithm,
                environment_features,
                PredictionModel.ENSEMBLE,
                config.prediction_horizon
            )
            
            predictions[algorithm] = {
                "performance": prediction_result.predicted_performance,
                "convergence": prediction_result.predicted_convergence,
                "confidence": prediction_result.confidence_score,
                "stability": prediction_result.stability_score
            }
        
        return predictions
    
    async def _generate_candidates(self,
                                 matching_result: Any,
                                 prediction_results: Dict[str, Dict[str, float]],
                                 config: SelectionConfig) -> List[AlgorithmCandidate]:
        """生成算法候選"""
        logger.info("生成算法候選")
        
        candidates = []
        
        for algorithm in matching_result.matched_algorithms:
            matching_score = matching_result.algorithm_scores.get(algorithm, 0.0)
            prediction_data = prediction_results.get(algorithm, {})
            
            # 計算綜合置信度
            confidence = self._calculate_confidence(
                matching_score,
                prediction_data.get("confidence", 0.0),
                algorithm
            )
            
            # 計算風險評分
            risk_score = self._calculate_risk_score(
                algorithm,
                prediction_data,
                matching_score
            )
            
            candidate = AlgorithmCandidate(
                algorithm_name=algorithm,
                confidence_score=confidence,
                predicted_performance=prediction_data.get("performance", 0.0),
                matching_score=matching_score,
                suitability_reasons=matching_result.suitability_reasons.get(algorithm, []),
                convergence_episodes=int(prediction_data.get("convergence", 0)),
                stability_score=prediction_data.get("stability", 0.0),
                risk_score=risk_score,
                uncertainty=1.0 - prediction_data.get("confidence", 0.0)
            )
            
            candidates.append(candidate)
        
        # 按置信度排序
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return candidates
    
    def _calculate_confidence(self,
                            matching_score: float,
                            prediction_confidence: float,
                            algorithm: str) -> float:
        """計算置信度"""
        # 歷史成功率
        historical_success = self.algorithm_performance_stats.get(algorithm, {}).get("success_rate", 0.5)
        
        # 加權平均
        confidence = (
            matching_score * 0.4 +
            prediction_confidence * 0.4 +
            historical_success * 0.2
        )
        
        return min(confidence, 1.0)
    
    def _calculate_risk_score(self,
                            algorithm: str,
                            prediction_data: Dict[str, float],
                            matching_score: float) -> float:
        """計算風險評分"""
        # 基礎風險
        base_risk = 1.0 - matching_score
        
        # 不確定性風險
        uncertainty_risk = 1.0 - prediction_data.get("confidence", 0.0)
        
        # 穩定性風險
        stability_risk = 1.0 - prediction_data.get("stability", 0.0)
        
        # 綜合風險
        risk_score = (
            base_risk * 0.4 +
            uncertainty_risk * 0.3 +
            stability_risk * 0.3
        )
        
        return min(risk_score, 1.0)
    
    async def _execute_selection_strategy(self,
                                        candidates: List[AlgorithmCandidate],
                                        config: SelectionConfig) -> Tuple[str, float, str]:
        """執行選擇策略"""
        logger.info(f"執行選擇策略: {config.strategy.value}")
        
        if not candidates:
            return config.fallback_algorithm, 0.5, "無可用候選算法"
        
        if config.strategy == SelectionStrategy.BEST_MATCH:
            # 選擇最佳匹配
            best_candidate = candidates[0]
            return (
                best_candidate.algorithm_name,
                best_candidate.confidence_score,
                f"最佳匹配，置信度: {best_candidate.confidence_score:.3f}"
            )
        
        elif config.strategy == SelectionStrategy.CONSERVATIVE:
            # 保守選擇：選擇風險最低的算法
            conservative_candidate = min(candidates, key=lambda x: x.risk_score)
            return (
                conservative_candidate.algorithm_name,
                conservative_candidate.confidence_score,
                f"保守選擇，風險評分: {conservative_candidate.risk_score:.3f}"
            )
        
        elif config.strategy == SelectionStrategy.EXPLORATORY:
            # 探索性選擇：平衡置信度和新穎性
            exploratory_scores = []
            for candidate in candidates:
                # 計算探索性評分
                novelty_bonus = 0.1 if candidate.algorithm_name != "DQN" else 0.0
                exploratory_score = candidate.confidence_score + novelty_bonus
                exploratory_scores.append((candidate, exploratory_score))
            
            best_exploratory = max(exploratory_scores, key=lambda x: x[1])
            candidate = best_exploratory[0]
            return (
                candidate.algorithm_name,
                candidate.confidence_score,
                f"探索性選擇，探索評分: {best_exploratory[1]:.3f}"
            )
        
        elif config.strategy == SelectionStrategy.ADAPTIVE:
            # 自適應選擇：根據環境特徵動態調整
            adaptive_candidate = await self._adaptive_selection(candidates, config)
            return (
                adaptive_candidate.algorithm_name,
                adaptive_candidate.confidence_score,
                "自適應選擇"
            )
        
        elif config.strategy == SelectionStrategy.ENSEMBLE:
            # 集成選擇：選擇多個算法的組合
            ensemble_algorithm = await self._ensemble_selection(candidates, config)
            return (
                ensemble_algorithm,
                candidates[0].confidence_score,
                "集成選擇"
            )
        
        # 默認選擇
        return candidates[0].algorithm_name, candidates[0].confidence_score, "默認選擇"
    
    async def _adaptive_selection(self,
                                candidates: List[AlgorithmCandidate],
                                config: SelectionConfig) -> AlgorithmCandidate:
        """自適應選擇"""
        # 根據最近的性能表現調整選擇
        recent_performance = self._get_recent_performance_trends()
        
        adjusted_candidates = []
        for candidate in candidates:
            # 根據最近表現調整置信度
            recent_multiplier = recent_performance.get(candidate.algorithm_name, 1.0)
            adjusted_confidence = candidate.confidence_score * recent_multiplier
            
            adjusted_candidate = AlgorithmCandidate(
                algorithm_name=candidate.algorithm_name,
                confidence_score=adjusted_confidence,
                predicted_performance=candidate.predicted_performance,
                matching_score=candidate.matching_score,
                suitability_reasons=candidate.suitability_reasons,
                convergence_episodes=candidate.convergence_episodes,
                stability_score=candidate.stability_score,
                risk_score=candidate.risk_score,
                uncertainty=candidate.uncertainty
            )
            adjusted_candidates.append(adjusted_candidate)
        
        # 選擇調整後置信度最高的算法
        return max(adjusted_candidates, key=lambda x: x.confidence_score)
    
    async def _ensemble_selection(self,
                                candidates: List[AlgorithmCandidate],
                                config: SelectionConfig) -> str:
        """集成選擇"""
        # 選擇前兩個最佳算法進行集成
        if len(candidates) >= 2:
            top_two = candidates[:2]
            return f"Ensemble_{top_two[0].algorithm_name}_{top_two[1].algorithm_name}"
        else:
            return candidates[0].algorithm_name
    
    def _get_recent_performance_trends(self) -> Dict[str, float]:
        """獲取最近的性能趨勢"""
        trends = {}
        
        for algorithm in self.algorithm_performance_stats:
            # 模擬最近的性能趨勢
            base_performance = self.algorithm_performance_stats[algorithm]["success_rate"]
            trend = base_performance + np.random.normal(0, 0.1)
            trends[algorithm] = max(0.5, min(1.5, trend))
        
        return trends
    
    async def _setup_monitoring(self, result: SelectionResult, config: SelectionConfig):
        """設置性能監控"""
        logger.info(f"設置性能監控: {result.environment_id}")
        
        # 初始化監控緩衝區
        if result.environment_id not in self.performance_monitors:
            self.performance_monitors[result.environment_id] = deque(maxlen=config.monitoring_window)
        
        # 設置監控參數
        result.monitoring_active = True
        result.next_evaluation_episode = config.validation_frequency
    
    async def monitor_performance(self,
                                environment_id: str,
                                episode: int,
                                performance_data: Dict[str, float]) -> Optional[str]:
        """
        監控性能並決定是否需要切換算法
        
        Args:
            environment_id: 環境ID
            episode: 當前回合
            performance_data: 性能數據
            
        Returns:
            如果需要切換，返回新算法名稱
        """
        if environment_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[environment_id]
        
        if not session.monitoring_active:
            return None
        
        # 記錄性能數據
        monitor = self.performance_monitors[environment_id]
        monitor.append(performance_data)
        
        # 檢查是否需要評估
        if episode < session.next_evaluation_episode:
            return None
        
        # 執行性能評估
        switch_decision = await self._evaluate_switching_conditions(
            environment_id,
            session,
            performance_data
        )
        
        if switch_decision:
            logger.info(f"觸發算法切換: {environment_id} -> {switch_decision}")
            
            # 更新會話信息
            session.switch_history.append({
                "episode": episode,
                "from_algorithm": session.selected_algorithm,
                "to_algorithm": switch_decision,
                "trigger": "performance_monitoring",
                "timestamp": datetime.now()
            })
            
            session.selected_algorithm = switch_decision
            session.next_evaluation_episode = episode + session.next_evaluation_episode
            
            return switch_decision
        
        # 更新下次評估時間
        session.next_evaluation_episode = episode + 50  # 模擬評估間隔
        
        return None
    
    async def _evaluate_switching_conditions(self,
                                           environment_id: str,
                                           session: SelectionResult,
                                           current_performance: Dict[str, float]) -> Optional[str]:
        """評估切換條件"""
        monitor = self.performance_monitors[environment_id]
        
        if len(monitor) < 10:  # 需要足夠的數據
            return None
        
        # 檢查性能下降
        recent_performance = [data.get("reward", 0.0) for data in list(monitor)[-10:]]
        earlier_performance = [data.get("reward", 0.0) for data in list(monitor)[-20:-10]]
        
        if len(earlier_performance) >= 10:
            recent_avg = np.mean(recent_performance)
            earlier_avg = np.mean(earlier_performance)
            
            if earlier_avg > 0 and (earlier_avg - recent_avg) / earlier_avg > 0.1:
                # 性能下降超過10%，考慮切換
                return await self._suggest_alternative_algorithm(session)
        
        # 檢查收斂停滯
        if len(recent_performance) >= 10:
            performance_variance = np.var(recent_performance)
            if performance_variance < 0.001:  # 幾乎沒有變化
                return await self._suggest_alternative_algorithm(session)
        
        return None
    
    async def _suggest_alternative_algorithm(self, session: SelectionResult) -> str:
        """建議替代算法"""
        # 從候選算法中選擇下一個最佳選項
        for candidate in session.candidates:
            if candidate.algorithm_name != session.selected_algorithm:
                return candidate.algorithm_name
        
        # 如果沒有其他候選，使用默認算法
        return "PPO" if session.selected_algorithm != "PPO" else "DQN"
    
    def get_selection_history(self) -> List[SelectionResult]:
        """獲取選擇歷史"""
        return self.selection_history.copy()
    
    def get_active_sessions(self) -> Dict[str, SelectionResult]:
        """獲取活躍會話"""
        return self.active_sessions.copy()
    
    def get_performance_statistics(self) -> Dict[str, Dict[str, float]]:
        """獲取性能統計"""
        return self.algorithm_performance_stats.copy()
    
    def update_performance_statistics(self, algorithm: str, stats: Dict[str, float]):
        """更新性能統計"""
        if algorithm in self.algorithm_performance_stats:
            self.algorithm_performance_stats[algorithm].update(stats)
            logger.info(f"更新 {algorithm} 性能統計")
    
    async def stop_monitoring(self, environment_id: str):
        """停止監控"""
        if environment_id in self.active_sessions:
            self.active_sessions[environment_id].monitoring_active = False
            logger.info(f"停止監控: {environment_id}")
    
    def get_monitoring_status(self, environment_id: str) -> Dict[str, Any]:
        """獲取監控狀態"""
        if environment_id not in self.active_sessions:
            return {"status": "inactive", "reason": "no_active_session"}
        
        session = self.active_sessions[environment_id]
        monitor = self.performance_monitors.get(environment_id, deque())
        
        return {
            "status": "active" if session.monitoring_active else "inactive",
            "selected_algorithm": session.selected_algorithm,
            "confidence_score": session.confidence_score,
            "next_evaluation_episode": session.next_evaluation_episode,
            "performance_history_length": len(monitor),
            "switch_count": len(session.switch_history)
        }
