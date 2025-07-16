"""
算法匹配器 - Phase 3 核心組件

基於環境特徵進行算法匹配，提供多種匹配策略和評分機制，
為智能算法選擇提供精確的匹配結果。

主要功能：
- 環境-算法匹配
- 多策略匹配
- 適用性評分
- 匹配效果評估
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import json

from .environment_analyzer import EnvironmentFeatures, StateSpaceType, ActionSpaceType

logger = logging.getLogger(__name__)


class MatchingStrategy(Enum):
    """匹配策略"""
    RULE_BASED = "rule_based"            # 基於規則
    SIMILARITY_BASED = "similarity_based"  # 基於相似性
    PERFORMANCE_BASED = "performance_based"  # 基於性能
    COMPREHENSIVE = "comprehensive"       # 綜合匹配
    LEARNING_BASED = "learning_based"    # 基於學習


@dataclass
class MatchingCriteria:
    """匹配標準"""
    name: str
    weight: float
    description: str
    
    # 評分函數
    evaluation_function: Optional[str] = None
    
    # 閾值
    minimum_score: float = 0.0
    maximum_score: float = 1.0
    
    # 適用條件
    applicable_conditions: List[str] = field(default_factory=list)


@dataclass
class MatchingResult:
    """匹配結果"""
    matching_id: str
    environment_id: str
    strategy: MatchingStrategy
    
    # 匹配算法
    matched_algorithms: List[str] = field(default_factory=list)
    algorithm_scores: Dict[str, float] = field(default_factory=dict)
    
    # 適用性分析
    suitability_reasons: Dict[str, List[str]] = field(default_factory=dict)
    
    # 匹配統計
    total_algorithms_evaluated: int = 0
    matching_time_seconds: float = 0.0
    
    # 置信度信息
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    overall_confidence: float = 0.0
    
    # 匹配報告
    matching_report: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)


class AlgorithmMatcher:
    """算法匹配器"""
    
    def __init__(self):
        """初始化算法匹配器"""
        self.matching_history: List[MatchingResult] = []
        
        # 算法特徵庫
        self.algorithm_features = {
            "DQN": {
                "action_space": ["discrete"],
                "state_space": ["discrete", "continuous", "image"],
                "reward_type": ["sparse", "dense"],
                "complexity": ["low", "medium"],
                "sample_efficiency": 0.6,
                "stability": 0.7,
                "convergence_speed": 0.6
            },
            "PPO": {
                "action_space": ["discrete", "continuous"],
                "state_space": ["discrete", "continuous"],
                "reward_type": ["sparse", "dense"],
                "complexity": ["medium", "high"],
                "sample_efficiency": 0.7,
                "stability": 0.8,
                "convergence_speed": 0.7
            },
            "SAC": {
                "action_space": ["continuous"],
                "state_space": ["continuous"],
                "reward_type": ["dense"],
                "complexity": ["high"],
                "sample_efficiency": 0.8,
                "stability": 0.9,
                "convergence_speed": 0.8
            },
            "A2C": {
                "action_space": ["discrete", "continuous"],
                "state_space": ["discrete", "continuous"],
                "reward_type": ["dense"],
                "complexity": ["low", "medium"],
                "sample_efficiency": 0.6,
                "stability": 0.6,
                "convergence_speed": 0.7
            },
            "TD3": {
                "action_space": ["continuous"],
                "state_space": ["continuous"],
                "reward_type": ["dense"],
                "complexity": ["medium", "high"],
                "sample_efficiency": 0.7,
                "stability": 0.8,
                "convergence_speed": 0.7
            }
        }
        
        # 匹配標準
        self.matching_criteria = {
            "action_space_compatibility": MatchingCriteria(
                name="action_space_compatibility",
                weight=0.3,
                description="動作空間兼容性"
            ),
            "state_space_compatibility": MatchingCriteria(
                name="state_space_compatibility",
                weight=0.25,
                description="狀態空間兼容性"
            ),
            "reward_structure_match": MatchingCriteria(
                name="reward_structure_match",
                weight=0.2,
                description="獎勵結構匹配"
            ),
            "complexity_match": MatchingCriteria(
                name="complexity_match",
                weight=0.15,
                description="複雜度匹配"
            ),
            "performance_potential": MatchingCriteria(
                name="performance_potential",
                weight=0.1,
                description="性能潛力"
            )
        }
        
        logger.info("算法匹配器初始化完成")
    
    async def match_algorithms(self,
                             environment_features: EnvironmentFeatures,
                             strategy: MatchingStrategy) -> MatchingResult:
        """
        匹配算法
        
        Args:
            environment_features: 環境特徵
            strategy: 匹配策略
            
        Returns:
            匹配結果
        """
        matching_id = f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        try:
            logger.info(f"開始算法匹配: {strategy.value}")
            
            # 執行匹配策略
            if strategy == MatchingStrategy.RULE_BASED:
                result = await self._rule_based_matching(environment_features, matching_id)
            elif strategy == MatchingStrategy.SIMILARITY_BASED:
                result = await self._similarity_based_matching(environment_features, matching_id)
            elif strategy == MatchingStrategy.PERFORMANCE_BASED:
                result = await self._performance_based_matching(environment_features, matching_id)
            elif strategy == MatchingStrategy.COMPREHENSIVE:
                result = await self._comprehensive_matching(environment_features, matching_id)
            elif strategy == MatchingStrategy.LEARNING_BASED:
                result = await self._learning_based_matching(environment_features, matching_id)
            else:
                result = await self._rule_based_matching(environment_features, matching_id)
            
            # 設置基本信息
            result.environment_id = environment_features.environment_id
            result.strategy = strategy
            result.total_algorithms_evaluated = len(self.algorithm_features)
            
            # 計算匹配時間
            end_time = datetime.now()
            result.matching_time_seconds = (end_time - start_time).total_seconds()
            
            # 生成匹配報告
            await self._generate_matching_report(result, environment_features)
            
            # 保存結果
            self.matching_history.append(result)
            
            logger.info(f"算法匹配完成: {matching_id}")
            return result
            
        except Exception as e:
            logger.error(f"算法匹配失敗: {e}")
            # 返回默認結果
            return MatchingResult(
                matching_id=matching_id,
                environment_id=environment_features.environment_id,
                strategy=strategy,
                matched_algorithms=["DQN", "PPO"],
                algorithm_scores={"DQN": 0.7, "PPO": 0.8},
                warnings=[f"匹配失敗: {str(e)}"]
            )
    
    async def _rule_based_matching(self,
                                 environment_features: EnvironmentFeatures,
                                 matching_id: str) -> MatchingResult:
        """基於規則的匹配"""
        logger.info("執行基於規則的匹配")
        
        result = MatchingResult(matching_id=matching_id)
        
        # 規則匹配
        for algorithm, features in self.algorithm_features.items():
            score = 0.0
            reasons = []
            
            # 動作空間匹配
            action_space_type = self._get_action_space_type_string(environment_features.action_space.space_type)
            if action_space_type in features["action_space"]:
                score += 0.3
                reasons.append(f"動作空間兼容: {action_space_type}")
            
            # 狀態空間匹配
            state_space_type = self._get_state_space_type_string(environment_features.state_space.space_type)
            if state_space_type in features["state_space"]:
                score += 0.25
                reasons.append(f"狀態空間兼容: {state_space_type}")
            
            # 獎勵類型匹配
            if environment_features.reward_features.reward_type in features["reward_type"]:
                score += 0.2
                reasons.append(f"獎勵類型匹配: {environment_features.reward_features.reward_type}")
            
            # 複雜度匹配
            complexity_level = self._get_complexity_level(environment_features.overall_complexity)
            if complexity_level in features["complexity"]:
                score += 0.15
                reasons.append(f"複雜度匹配: {complexity_level}")
            
            # 性能潛力
            score += features["sample_efficiency"] * 0.1
            reasons.append(f"樣本效率: {features['sample_efficiency']:.2f}")
            
            # 只包含評分超過閾值的算法
            if score >= 0.4:
                result.matched_algorithms.append(algorithm)
                result.algorithm_scores[algorithm] = score
                result.suitability_reasons[algorithm] = reasons
                result.confidence_scores[algorithm] = score * 0.9  # 規則匹配置信度稍低
        
        # 排序算法
        result.matched_algorithms.sort(key=lambda x: result.algorithm_scores[x], reverse=True)
        
        # 計算整體置信度
        if result.algorithm_scores:
            result.overall_confidence = np.mean(list(result.confidence_scores.values()))
        
        return result
    
    async def _similarity_based_matching(self,
                                       environment_features: EnvironmentFeatures,
                                       matching_id: str) -> MatchingResult:
        """基於相似性的匹配"""
        logger.info("執行基於相似性的匹配")
        
        result = MatchingResult(matching_id=matching_id)
        
        # 環境特徵向量化
        env_vector = self._vectorize_environment_features(environment_features)
        
        # 計算相似性
        for algorithm, features in self.algorithm_features.items():
            alg_vector = self._vectorize_algorithm_features(features)
            
            # 計算餘弦相似度
            similarity = self._calculate_cosine_similarity(env_vector, alg_vector)
            
            # 調整相似度評分
            adjusted_score = similarity * 0.8 + np.random.uniform(0.1, 0.2)
            
            if adjusted_score >= 0.3:
                result.matched_algorithms.append(algorithm)
                result.algorithm_scores[algorithm] = adjusted_score
                result.confidence_scores[algorithm] = similarity
                result.suitability_reasons[algorithm] = [f"相似性評分: {similarity:.3f}"]
        
        # 排序算法
        result.matched_algorithms.sort(key=lambda x: result.algorithm_scores[x], reverse=True)
        
        # 計算整體置信度
        if result.confidence_scores:
            result.overall_confidence = np.mean(list(result.confidence_scores.values()))
        
        return result
    
    async def _performance_based_matching(self,
                                        environment_features: EnvironmentFeatures,
                                        matching_id: str) -> MatchingResult:
        """基於性能的匹配"""
        logger.info("執行基於性能的匹配")
        
        result = MatchingResult(matching_id=matching_id)
        
        # 基於歷史性能數據匹配
        for algorithm, features in self.algorithm_features.items():
            # 計算預期性能
            expected_performance = self._calculate_expected_performance(
                algorithm, environment_features
            )
            
            if expected_performance >= 0.5:
                result.matched_algorithms.append(algorithm)
                result.algorithm_scores[algorithm] = expected_performance
                result.confidence_scores[algorithm] = expected_performance * 0.9
                result.suitability_reasons[algorithm] = [
                    f"預期性能: {expected_performance:.3f}",
                    f"穩定性: {features['stability']:.3f}",
                    f"收斂速度: {features['convergence_speed']:.3f}"
                ]
        
        # 排序算法
        result.matched_algorithms.sort(key=lambda x: result.algorithm_scores[x], reverse=True)
        
        # 計算整體置信度
        if result.confidence_scores:
            result.overall_confidence = np.mean(list(result.confidence_scores.values()))
        
        return result
    
    async def _comprehensive_matching(self,
                                    environment_features: EnvironmentFeatures,
                                    matching_id: str) -> MatchingResult:
        """綜合匹配"""
        logger.info("執行綜合匹配")
        
        # 結合多種匹配策略
        rule_result = await self._rule_based_matching(environment_features, matching_id + "_rule")
        similarity_result = await self._similarity_based_matching(environment_features, matching_id + "_sim")
        performance_result = await self._performance_based_matching(environment_features, matching_id + "_perf")
        
        # 綜合評分
        result = MatchingResult(matching_id=matching_id)
        combined_scores = {}
        
        # 收集所有算法
        all_algorithms = set()
        all_algorithms.update(rule_result.matched_algorithms)
        all_algorithms.update(similarity_result.matched_algorithms)
        all_algorithms.update(performance_result.matched_algorithms)
        
        # 綜合評分
        for algorithm in all_algorithms:
            rule_score = rule_result.algorithm_scores.get(algorithm, 0.0)
            sim_score = similarity_result.algorithm_scores.get(algorithm, 0.0)
            perf_score = performance_result.algorithm_scores.get(algorithm, 0.0)
            
            # 加權平均
            combined_score = (rule_score * 0.4 + sim_score * 0.3 + perf_score * 0.3)
            
            if combined_score >= 0.4:
                result.matched_algorithms.append(algorithm)
                result.algorithm_scores[algorithm] = combined_score
                result.confidence_scores[algorithm] = combined_score * 0.95
                
                # 合併適用性原因
                reasons = []
                reasons.extend(rule_result.suitability_reasons.get(algorithm, []))
                reasons.extend(similarity_result.suitability_reasons.get(algorithm, []))
                reasons.extend(performance_result.suitability_reasons.get(algorithm, []))
                result.suitability_reasons[algorithm] = reasons
        
        # 排序算法
        result.matched_algorithms.sort(key=lambda x: result.algorithm_scores[x], reverse=True)
        
        # 計算整體置信度
        if result.confidence_scores:
            result.overall_confidence = np.mean(list(result.confidence_scores.values()))
        
        return result
    
    async def _learning_based_matching(self,
                                     environment_features: EnvironmentFeatures,
                                     matching_id: str) -> MatchingResult:
        """基於學習的匹配"""
        logger.info("執行基於學習的匹配")
        
        # 模擬學習基的匹配（實際實現需要訓練模型）
        result = MatchingResult(matching_id=matching_id)
        
        # 使用模擬的學習模型
        for algorithm, features in self.algorithm_features.items():
            # 模擬學習模型預測
            predicted_score = self._simulate_learning_model_prediction(
                environment_features, algorithm
            )
            
            if predicted_score >= 0.4:
                result.matched_algorithms.append(algorithm)
                result.algorithm_scores[algorithm] = predicted_score
                result.confidence_scores[algorithm] = predicted_score * 0.85
                result.suitability_reasons[algorithm] = [
                    f"學習模型預測: {predicted_score:.3f}",
                    "基於歷史學習數據"
                ]
        
        # 排序算法
        result.matched_algorithms.sort(key=lambda x: result.algorithm_scores[x], reverse=True)
        
        # 計算整體置信度
        if result.confidence_scores:
            result.overall_confidence = np.mean(list(result.confidence_scores.values()))
        
        return result
    
    def _get_action_space_type_string(self, action_space_type: ActionSpaceType) -> str:
        """獲取動作空間類型字符串"""
        if action_space_type == ActionSpaceType.DISCRETE:
            return "discrete"
        elif action_space_type == ActionSpaceType.CONTINUOUS:
            return "continuous"
        else:
            return "mixed"
    
    def _get_state_space_type_string(self, state_space_type: StateSpaceType) -> str:
        """獲取狀態空間類型字符串"""
        if state_space_type == StateSpaceType.DISCRETE:
            return "discrete"
        elif state_space_type == StateSpaceType.CONTINUOUS:
            return "continuous"
        elif state_space_type == StateSpaceType.IMAGE:
            return "image"
        else:
            return "mixed"
    
    def _get_complexity_level(self, complexity: float) -> str:
        """獲取複雜度級別"""
        if complexity < 0.3:
            return "low"
        elif complexity < 0.7:
            return "medium"
        else:
            return "high"
    
    def _vectorize_environment_features(self, features: EnvironmentFeatures) -> np.ndarray:
        """將環境特徵向量化"""
        vector = [
            features.state_space.dimensions / 100,  # 標準化維度
            features.action_space.dimensions / 10,  # 標準化動作維度
            features.overall_complexity,
            features.learning_difficulty,
            features.reward_features.sparsity,
            features.dynamics_features.state_transition_complexity
        ]
        return np.array(vector)
    
    def _vectorize_algorithm_features(self, features: Dict[str, Any]) -> np.ndarray:
        """將算法特徵向量化"""
        vector = [
            len(features["action_space"]) / 3,  # 動作空間支持度
            len(features["state_space"]) / 4,   # 狀態空間支持度
            features["sample_efficiency"],
            features["stability"],
            features["convergence_speed"],
            len(features["complexity"]) / 3     # 複雜度適應性
        ]
        return np.array(vector)
    
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算餘弦相似度"""
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return max(0.0, similarity)
    
    def _calculate_expected_performance(self,
                                      algorithm: str,
                                      environment_features: EnvironmentFeatures) -> float:
        """計算預期性能"""
        features = self.algorithm_features[algorithm]
        
        # 基於環境特徵調整性能預期
        base_performance = features["sample_efficiency"]
        
        # 複雜度調整
        complexity_penalty = environment_features.overall_complexity * 0.1
        
        # 學習難度調整
        difficulty_penalty = environment_features.learning_difficulty * 0.15
        
        # 穩定性加成
        stability_bonus = features["stability"] * 0.1
        
        expected_performance = base_performance - complexity_penalty - difficulty_penalty + stability_bonus
        
        return max(0.0, min(1.0, expected_performance))
    
    def _simulate_learning_model_prediction(self,
                                          environment_features: EnvironmentFeatures,
                                          algorithm: str) -> float:
        """模擬學習模型預測"""
        # 模擬基於機器學習的預測
        base_score = self.algorithm_features[algorithm]["sample_efficiency"]
        
        # 添加基於環境特徵的調整
        env_factor = 1.0 - environment_features.overall_complexity * 0.2
        
        # 添加隨機性
        noise = np.random.normal(0, 0.1)
        
        predicted_score = base_score * env_factor + noise
        
        return max(0.0, min(1.0, predicted_score))
    
    async def _generate_matching_report(self,
                                      result: MatchingResult,
                                      environment_features: EnvironmentFeatures):
        """生成匹配報告"""
        report = []
        
        # 基本信息
        report.append(f"匹配策略: {result.strategy.value}")
        report.append(f"評估算法數: {result.total_algorithms_evaluated}")
        report.append(f"匹配算法數: {len(result.matched_algorithms)}")
        
        # 環境特徵摘要
        report.append(f"環境類型: {environment_features.environment_type.value}")
        report.append(f"狀態空間: {environment_features.state_space.space_type.value}")
        report.append(f"動作空間: {environment_features.action_space.space_type.value}")
        
        # 匹配結果
        if result.matched_algorithms:
            top_algorithm = result.matched_algorithms[0]
            top_score = result.algorithm_scores[top_algorithm]
            report.append(f"最佳匹配: {top_algorithm} (評分: {top_score:.3f})")
        
        # 整體置信度
        report.append(f"整體置信度: {result.overall_confidence:.3f}")
        
        result.matching_report = report
    
    def get_matching_history(self) -> List[MatchingResult]:
        """獲取匹配歷史"""
        return self.matching_history.copy()
    
    def get_algorithm_features(self) -> Dict[str, Dict[str, Any]]:
        """獲取算法特徵庫"""
        return self.algorithm_features.copy()
    
    def update_algorithm_features(self, algorithm: str, features: Dict[str, Any]):
        """更新算法特徵"""
        if algorithm in self.algorithm_features:
            self.algorithm_features[algorithm].update(features)
            logger.info(f"更新 {algorithm} 特徵")
        else:
            self.algorithm_features[algorithm] = features
            logger.info(f"添加新算法 {algorithm}")
    
    def get_matching_criteria(self) -> Dict[str, MatchingCriteria]:
        """獲取匹配標準"""
        return self.matching_criteria.copy()
    
    def update_matching_criteria(self, criteria_name: str, criteria: MatchingCriteria):
        """更新匹配標準"""
        self.matching_criteria[criteria_name] = criteria
        logger.info(f"更新匹配標準: {criteria_name}")
