"""
候選衛星評分引擎

整合多種篩選策略，為候選衛星提供綜合評分。
支援動態權重調整和多策略融合。
"""

import time
import math
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..interfaces.candidate_selector import Candidate, ScoredCandidate, ProcessedEvent
from .strategies.base_strategy import SelectionStrategy, StrategyParameters, StrategyResult


logger = logging.getLogger(__name__)


class ScoringMethod(Enum):
    """評分方法枚舉"""
    WEIGHTED_AVERAGE = "weighted_average"
    MULTIPLICATIVE = "multiplicative"
    MIN_MAX_NORMALIZED = "min_max_normalized"
    RANK_BASED = "rank_based"
    FUZZY_LOGIC = "fuzzy_logic"


@dataclass
class ScoringConfig:
    """評分配置"""
    method: ScoringMethod = ScoringMethod.WEIGHTED_AVERAGE
    normalization: bool = True
    confidence_weighting: bool = True
    outlier_handling: bool = True
    min_strategies_required: int = 2
    score_threshold: float = 0.0
    ranking_method: str = "score_desc"  # score_desc, confidence_desc, hybrid
    custom_weights: Dict[str, float] = field(default_factory=dict)
    boost_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class ScoringResult:
    """評分結果"""
    scored_candidates: List[ScoredCandidate]
    strategy_results: Dict[str, StrategyResult]
    scoring_metadata: Dict[str, Any]
    execution_time_ms: float
    total_evaluated: int
    total_scored: int


class ScoringEngine:
    """
    候選衛星評分引擎
    
    整合多種篩選策略，提供靈活的評分機制：
    - 多策略權重融合
    - 動態評分方法切換
    - 智能異常處理
    - 置信度計算
    """
    
    def __init__(self, config: ScoringConfig = None):
        self.config = config or ScoringConfig()
        self.strategies: Dict[str, SelectionStrategy] = {}
        self.strategy_weights: Dict[str, float] = {}
        self.logger = logging.getLogger(f"{__name__}.ScoringEngine")
        
        # 評分統計
        self.scoring_stats = {
            "total_scorings": 0,
            "total_candidates_scored": 0,
            "average_execution_time_ms": 0.0,
            "strategy_usage_count": {}
        }
    
    def register_strategy(self, strategy: SelectionStrategy, weight: float = 1.0):
        """
        註冊篩選策略
        
        Args:
            strategy: 篩選策略實例
            weight: 策略權重
        """
        if not isinstance(strategy, SelectionStrategy):
            raise ValueError(f"Strategy must be instance of SelectionStrategy, got {type(strategy)}")
        
        if weight <= 0:
            raise ValueError(f"Strategy weight must be positive, got {weight}")
        
        self.strategies[strategy.name] = strategy
        self.strategy_weights[strategy.name] = weight
        
        # 初始化統計
        if strategy.name not in self.scoring_stats["strategy_usage_count"]:
            self.scoring_stats["strategy_usage_count"][strategy.name] = 0
        
        self.logger.info(f"Registered strategy: {strategy.name} with weight {weight}")
    
    def unregister_strategy(self, strategy_name: str):
        """
        取消註冊策略
        
        Args:
            strategy_name: 策略名稱
        """
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            del self.strategy_weights[strategy_name]
            self.logger.info(f"Unregistered strategy: {strategy_name}")
    
    def update_strategy_weight(self, strategy_name: str, weight: float):
        """
        更新策略權重
        
        Args:
            strategy_name: 策略名稱
            weight: 新權重
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy {strategy_name} not registered")
        
        if weight <= 0:
            raise ValueError(f"Strategy weight must be positive, got {weight}")
        
        old_weight = self.strategy_weights[strategy_name]
        self.strategy_weights[strategy_name] = weight
        
        self.logger.info(f"Updated strategy {strategy_name} weight: {old_weight} -> {weight}")
    
    def score_candidates(self, candidates: List[Candidate],
                        event: ProcessedEvent,
                        strategy_params: Dict[str, StrategyParameters] = None) -> ScoringResult:
        """
        對候選衛星進行綜合評分
        
        Args:
            candidates: 候選衛星列表
            event: 處理後的事件
            strategy_params: 策略參數字典
            
        Returns:
            ScoringResult: 評分結果
        """
        start_time = time.time()
        
        if not candidates:
            return ScoringResult(
                scored_candidates=[],
                strategy_results={},
                scoring_metadata={"error": "No candidates provided"},
                execution_time_ms=0.0,
                total_evaluated=0,
                total_scored=0
            )
        
        if not self.strategies:
            raise ValueError("No strategies registered")
        
        strategy_params = strategy_params or {}
        strategy_results = {}
        
        # 執行所有策略
        self.logger.info(f"Starting scoring for {len(candidates)} candidates using {len(self.strategies)} strategies")
        
        for strategy_name, strategy in self.strategies.items():
            try:
                params = strategy_params.get(strategy_name)
                result = strategy.filter_candidates(candidates, event, params)
                strategy_results[strategy_name] = result
                
                # 更新使用統計
                self.scoring_stats["strategy_usage_count"][strategy_name] += 1
                
                self.logger.debug(f"Strategy {strategy_name} completed: {len(result.filtered_candidates)} candidates")
                
            except Exception as e:
                self.logger.error(f"Strategy {strategy_name} failed: {str(e)}", exc_info=True)
                # 創建空結果以保持一致性
                strategy_results[strategy_name] = StrategyResult(
                    filtered_candidates=[],
                    scores={},
                    metadata={"error": str(e)},
                    strategy_name=strategy_name,
                    execution_time_ms=0.0
                )
        
        # 檢查最小策略要求
        successful_strategies = [r for r in strategy_results.values() if "error" not in r.metadata]
        if len(successful_strategies) < self.config.min_strategies_required:
            self.logger.warning(f"Only {len(successful_strategies)} strategies succeeded, minimum required: {self.config.min_strategies_required}")
        
        # 融合評分
        scored_candidates = self._fuse_scores(candidates, strategy_results)
        
        # 後處理
        scored_candidates = self._post_process_scores(scored_candidates, candidates)
        
        execution_time = (time.time() - start_time) * 1000
        
        # 更新統計
        self.scoring_stats["total_scorings"] += 1
        self.scoring_stats["total_candidates_scored"] += len(scored_candidates)
        self.scoring_stats["average_execution_time_ms"] = (
            (self.scoring_stats["average_execution_time_ms"] * (self.scoring_stats["total_scorings"] - 1) + execution_time) /
            self.scoring_stats["total_scorings"]
        )
        
        # 生成評分元數據
        scoring_metadata = self._generate_scoring_metadata(strategy_results, scored_candidates, execution_time)
        
        self.logger.info(f"Scoring completed: {len(scored_candidates)} candidates scored in {execution_time:.2f}ms")
        
        return ScoringResult(
            scored_candidates=scored_candidates,
            strategy_results=strategy_results,
            scoring_metadata=scoring_metadata,
            execution_time_ms=execution_time,
            total_evaluated=len(candidates),
            total_scored=len(scored_candidates)
        )
    
    def _fuse_scores(self, candidates: List[Candidate], 
                    strategy_results: Dict[str, StrategyResult]) -> List[ScoredCandidate]:
        """
        融合多策略評分
        
        Args:
            candidates: 原始候選列表
            strategy_results: 策略結果字典
            
        Returns:
            List[ScoredCandidate]: 融合評分後的候選列表
        """
        scored_candidates = []
        
        # 正規化權重
        total_weight = sum(self.strategy_weights[name] for name in strategy_results.keys() 
                         if "error" not in strategy_results[name].metadata)
        
        if total_weight == 0:
            self.logger.warning("Total strategy weight is zero, using equal weights")
            normalized_weights = {name: 1.0 / len(strategy_results) for name in strategy_results.keys()}
        else:
            normalized_weights = {name: self.strategy_weights[name] / total_weight 
                                for name in strategy_results.keys()
                                if "error" not in strategy_results[name].metadata}
        
        for candidate in candidates:
            satellite_id = candidate.satellite_id
            
            # 收集所有策略對此候選者的評分
            strategy_scores = {}
            sub_scores = {}
            reasoning = {"strategies_used": [], "weights_applied": {}}
            
            for strategy_name, result in strategy_results.items():
                if "error" in result.metadata:
                    continue
                    
                if satellite_id in result.scores:
                    score = result.scores[satellite_id]
                    strategy_scores[strategy_name] = score
                    sub_scores[strategy_name] = score
                    reasoning["strategies_used"].append(strategy_name)
                    reasoning["weights_applied"][strategy_name] = normalized_weights.get(strategy_name, 0.0)
            
            # 如果沒有任何策略評分，跳過此候選者
            if not strategy_scores:
                continue
            
            # 根據配置的方法融合評分
            fused_score = self._calculate_fused_score(strategy_scores, normalized_weights)
            
            # 計算置信度
            confidence = self._calculate_confidence(strategy_scores, normalized_weights)
            
            # 應用自定義權重和提升因子
            fused_score = self._apply_custom_adjustments(fused_score, candidate, reasoning)
            
            # 確保分數在有效範圍內
            fused_score = max(0.0, min(1.0, fused_score))
            confidence = max(0.0, min(1.0, confidence))
            
            # 創建評分候選者
            scored_candidate = ScoredCandidate(
                candidate=candidate,
                score=fused_score,
                confidence=confidence,
                ranking=0,  # 將在後處理中設置
                sub_scores=sub_scores,
                reasoning=reasoning
            )
            
            scored_candidates.append(scored_candidate)
        
        return scored_candidates
    
    def _calculate_fused_score(self, strategy_scores: Dict[str, float], 
                              weights: Dict[str, float]) -> float:
        """
        根據配置的方法計算融合評分
        
        Args:
            strategy_scores: 策略評分字典
            weights: 正規化權重字典
            
        Returns:
            float: 融合評分
        """
        if not strategy_scores:
            return 0.0
        
        method = self.config.method
        
        if method == ScoringMethod.WEIGHTED_AVERAGE:
            # 加權平均
            weighted_sum = sum(score * weights.get(strategy, 0.0) 
                             for strategy, score in strategy_scores.items())
            return weighted_sum
        
        elif method == ScoringMethod.MULTIPLICATIVE:
            # 乘法融合 (幾何平均)
            product = 1.0
            total_weight = 0.0
            for strategy, score in strategy_scores.items():
                weight = weights.get(strategy, 0.0)
                if weight > 0:
                    product *= (score ** weight)
                    total_weight += weight
            
            return product if total_weight > 0 else 0.0
        
        elif method == ScoringMethod.MIN_MAX_NORMALIZED:
            # 最小-最大正規化後加權平均
            if len(strategy_scores) < 2:
                return list(strategy_scores.values())[0]
            
            min_score = min(strategy_scores.values())
            max_score = max(strategy_scores.values())
            
            if max_score - min_score == 0:
                return min_score
            
            normalized_scores = {
                strategy: (score - min_score) / (max_score - min_score)
                for strategy, score in strategy_scores.items()
            }
            
            weighted_sum = sum(score * weights.get(strategy, 0.0)
                             for strategy, score in normalized_scores.items())
            return weighted_sum
        
        elif method == ScoringMethod.RANK_BASED:
            # 基於排名的融合
            sorted_strategies = sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)
            rank_scores = {}
            
            for i, (strategy, _) in enumerate(sorted_strategies):
                rank_score = 1.0 - (i / len(sorted_strategies))
                rank_scores[strategy] = rank_score
            
            weighted_sum = sum(score * weights.get(strategy, 0.0)
                             for strategy, score in rank_scores.items())
            return weighted_sum
        
        elif method == ScoringMethod.FUZZY_LOGIC:
            # 模糊邏輯融合 (簡化實現)
            high_scores = [score for score in strategy_scores.values() if score > 0.7]
            medium_scores = [score for score in strategy_scores.values() if 0.3 <= score <= 0.7]
            low_scores = [score for score in strategy_scores.values() if score < 0.3]
            
            if high_scores:
                return max(high_scores) * 0.8 + sum(high_scores) / len(high_scores) * 0.2
            elif medium_scores:
                return sum(medium_scores) / len(medium_scores) * 0.6
            else:
                return sum(low_scores) / len(low_scores) * 0.3 if low_scores else 0.0
        
        else:
            # 默認使用加權平均
            weighted_sum = sum(score * weights.get(strategy, 0.0)
                             for strategy, score in strategy_scores.items())
            return weighted_sum
    
    def _calculate_confidence(self, strategy_scores: Dict[str, float], 
                            weights: Dict[str, float]) -> float:
        """
        計算評分置信度
        
        Args:
            strategy_scores: 策略評分字典
            weights: 權重字典
            
        Returns:
            float: 置信度 (0.0-1.0)
        """
        if not strategy_scores:
            return 0.0
        
        # 基於策略一致性的置信度
        scores = list(strategy_scores.values())
        mean_score = sum(scores) / len(scores)
        
        # 計算標準差
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = math.sqrt(variance)
        
        # 一致性置信度 (標準差越小，置信度越高)
        consistency_confidence = max(0.0, 1.0 - std_dev * 2)
        
        # 覆蓋率置信度 (參與評分的策略數量)
        coverage_confidence = len(strategy_scores) / len(self.strategies)
        
        # 權重置信度 (使用的策略權重總和)
        weight_confidence = sum(weights.get(strategy, 0.0) for strategy in strategy_scores.keys())
        
        # 綜合置信度
        if self.config.confidence_weighting:
            confidence = (
                0.4 * consistency_confidence +
                0.3 * coverage_confidence +
                0.3 * weight_confidence
            )
        else:
            confidence = consistency_confidence
        
        return max(0.0, min(1.0, confidence))
    
    def _apply_custom_adjustments(self, score: float, candidate: Candidate, 
                                reasoning: Dict[str, Any]) -> float:
        """
        應用自定義權重和提升因子
        
        Args:
            score: 原始融合分數
            candidate: 候選衛星
            reasoning: 推理信息
            
        Returns:
            float: 調整後的分數
        """
        adjusted_score = score
        
        # 應用自定義權重
        satellite_id = candidate.satellite_id
        if satellite_id in self.config.custom_weights:
            custom_weight = self.config.custom_weights[satellite_id]
            adjusted_score *= custom_weight
            reasoning["custom_weight_applied"] = custom_weight
        
        # 應用提升因子
        boost_applied = []
        for condition, boost_factor in self.config.boost_factors.items():
            if self._evaluate_boost_condition(condition, candidate):
                adjusted_score *= boost_factor
                boost_applied.append({"condition": condition, "factor": boost_factor})
        
        if boost_applied:
            reasoning["boost_factors_applied"] = boost_applied
        
        return adjusted_score
    
    def _evaluate_boost_condition(self, condition: str, candidate: Candidate) -> bool:
        """
        評估提升條件
        
        Args:
            condition: 條件字符串
            candidate: 候選衛星
            
        Returns:
            bool: 條件是否滿足
        """
        # 簡化的條件評估實現
        try:
            if condition.startswith("elevation>"):
                threshold = float(condition.split(">")[1])
                return candidate.elevation > threshold
            elif condition.startswith("signal>"):
                threshold = float(condition.split(">")[1])
                return candidate.signal_strength > threshold
            elif condition.startswith("load<"):
                threshold = float(condition.split("<")[1])
                return candidate.load_factor < threshold
            # 可以添加更多條件類型
        except Exception:
            pass
        
        return False
    
    def _post_process_scores(self, scored_candidates: List[ScoredCandidate],
                           original_candidates: List[Candidate]) -> List[ScoredCandidate]:
        """
        後處理評分結果
        
        Args:
            scored_candidates: 評分候選列表
            original_candidates: 原始候選列表
            
        Returns:
            List[ScoredCandidate]: 後處理後的候選列表
        """
        if not scored_candidates:
            return scored_candidates
        
        # 異常值處理
        if self.config.outlier_handling:
            scored_candidates = self._handle_outliers(scored_candidates)
        
        # 正規化處理
        if self.config.normalization:
            scored_candidates = self._normalize_scores(scored_candidates)
        
        # 排序
        scored_candidates = self._sort_candidates(scored_candidates)
        
        # 設置排名
        for i, candidate in enumerate(scored_candidates):
            candidate.ranking = i + 1
        
        # 應用分數閾值
        if self.config.score_threshold > 0:
            scored_candidates = [c for c in scored_candidates if c.score >= self.config.score_threshold]
        
        return scored_candidates
    
    def _handle_outliers(self, scored_candidates: List[ScoredCandidate]) -> List[ScoredCandidate]:
        """處理異常值"""
        if len(scored_candidates) < 3:
            return scored_candidates
        
        scores = [c.score for c in scored_candidates]
        mean_score = sum(scores) / len(scores)
        std_dev = math.sqrt(sum((s - mean_score) ** 2 for s in scores) / len(scores))
        
        # 使用 2 標準差作為異常值閾值
        outlier_threshold = 2 * std_dev
        
        for candidate in scored_candidates:
            if abs(candidate.score - mean_score) > outlier_threshold:
                # 將異常值調整到合理範圍
                if candidate.score > mean_score:
                    candidate.score = min(candidate.score, mean_score + outlier_threshold)
                else:
                    candidate.score = max(candidate.score, mean_score - outlier_threshold)
                
                candidate.reasoning["outlier_adjusted"] = True
        
        return scored_candidates
    
    def _normalize_scores(self, scored_candidates: List[ScoredCandidate]) -> List[ScoredCandidate]:
        """正規化分數"""
        if not scored_candidates:
            return scored_candidates
        
        scores = [c.score for c in scored_candidates]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score - min_score == 0:
            return scored_candidates
        
        for candidate in scored_candidates:
            original_score = candidate.score
            candidate.score = (candidate.score - min_score) / (max_score - min_score)
            candidate.reasoning["normalized"] = {
                "original_score": original_score,
                "min_score": min_score,
                "max_score": max_score
            }
        
        return scored_candidates
    
    def _sort_candidates(self, scored_candidates: List[ScoredCandidate]) -> List[ScoredCandidate]:
        """排序候選者"""
        method = self.config.ranking_method
        
        if method == "score_desc":
            return sorted(scored_candidates, key=lambda c: c.score, reverse=True)
        elif method == "confidence_desc":
            return sorted(scored_candidates, key=lambda c: c.confidence, reverse=True)
        elif method == "hybrid":
            # 混合排序：分數*置信度
            return sorted(scored_candidates, key=lambda c: c.score * c.confidence, reverse=True)
        else:
            return sorted(scored_candidates, key=lambda c: c.score, reverse=True)
    
    def _generate_scoring_metadata(self, strategy_results: Dict[str, StrategyResult],
                                 scored_candidates: List[ScoredCandidate],
                                 execution_time: float) -> Dict[str, Any]:
        """生成評分元數據"""
        metadata = {
            "scoring_config": {
                "method": self.config.method.value,
                "normalization": self.config.normalization,
                "confidence_weighting": self.config.confidence_weighting,
                "outlier_handling": self.config.outlier_handling,
                "min_strategies_required": self.config.min_strategies_required,
                "score_threshold": self.config.score_threshold
            },
            "strategy_summary": {},
            "score_distribution": {},
            "execution_stats": {
                "total_time_ms": execution_time,
                "strategies_executed": len(strategy_results),
                "candidates_scored": len(scored_candidates)
            },
            "quality_metrics": {}
        }
        
        # 策略摘要
        for name, result in strategy_results.items():
            metadata["strategy_summary"][name] = {
                "candidates_filtered": len(result.filtered_candidates),
                "execution_time_ms": result.execution_time_ms,
                "weight_used": self.strategy_weights.get(name, 0.0),
                "success": "error" not in result.metadata
            }
        
        # 分數分佈
        if scored_candidates:
            scores = [c.score for c in scored_candidates]
            confidences = [c.confidence for c in scored_candidates]
            
            metadata["score_distribution"] = {
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "std_dev": math.sqrt(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))
            }
            
            metadata["confidence_distribution"] = {
                "mean": sum(confidences) / len(confidences),
                "min": min(confidences),
                "max": max(confidences)
            }
        
        # 質量指標
        successful_strategies = [r for r in strategy_results.values() if "error" not in r.metadata]
        metadata["quality_metrics"] = {
            "strategy_success_rate": len(successful_strategies) / len(strategy_results),
            "coverage_rate": len(scored_candidates) / max(1, len(strategy_results)),
            "average_confidence": sum(c.confidence for c in scored_candidates) / len(scored_candidates) if scored_candidates else 0.0
        }
        
        return metadata
    
    def get_strategy_insights(self) -> Dict[str, Any]:
        """獲取策略使用洞察"""
        return {
            "registered_strategies": list(self.strategies.keys()),
            "strategy_weights": self.strategy_weights.copy(),
            "usage_statistics": self.scoring_stats.copy(),
            "configuration": {
                "method": self.config.method.value,
                "normalization": self.config.normalization,
                "confidence_weighting": self.config.confidence_weighting,
                "outlier_handling": self.config.outlier_handling
            }
        }
    
    def reset_statistics(self):
        """重置統計信息"""
        self.scoring_stats = {
            "total_scorings": 0,
            "total_candidates_scored": 0,
            "average_execution_time_ms": 0.0,
            "strategy_usage_count": {name: 0 for name in self.strategies.keys()}
        }
        self.logger.info("Scoring statistics reset")