"""
環境分析器 - Phase 3 核心組件

分析強化學習環境的特徵，提供多維度的環境分析結果，
為智能算法選擇提供基礎數據支撐。

主要功能：
- 狀態空間分析
- 動作空間分析
- 獎勵結構分析
- 環境動力學分析
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import torch
import torch.nn as nn
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """環境類型"""
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    MIXED = "mixed"
    MULTI_DISCRETE = "multi_discrete"


class StateSpaceType(Enum):
    """狀態空間類型"""
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    IMAGE = "image"
    SEQUENCE = "sequence"
    GRAPH = "graph"


class ActionSpaceType(Enum):
    """動作空間類型"""
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    MULTI_DISCRETE = "multi_discrete"
    MULTI_BINARY = "multi_binary"


@dataclass
class StateSpaceFeatures:
    """狀態空間特徵"""
    space_type: StateSpaceType
    dimensions: int
    shape: Tuple[int, ...]
    
    # 數值特徵
    min_values: Optional[List[float]] = None
    max_values: Optional[List[float]] = None
    mean_values: Optional[List[float]] = None
    std_values: Optional[List[float]] = None
    
    # 分布特徵
    sparsity: float = 0.0
    entropy: float = 0.0
    correlation_matrix: Optional[np.ndarray] = None
    
    # 時序特徵
    temporal_dependency: float = 0.0
    markov_property: float = 0.0


@dataclass
class ActionSpaceFeatures:
    """動作空間特徵"""
    space_type: ActionSpaceType
    dimensions: int
    shape: Tuple[int, ...]
    
    # 動作範圍
    min_actions: Optional[List[float]] = None
    max_actions: Optional[List[float]] = None
    discrete_actions: Optional[List[int]] = None
    
    # 動作分布
    action_distribution: Optional[Dict[str, float]] = None
    action_entropy: float = 0.0
    
    # 約束特徵
    constraints: List[str] = field(default_factory=list)
    action_masking: bool = False


@dataclass
class RewardFeatures:
    """獎勵特徵"""
    reward_type: str  # sparse, dense, mixed
    reward_range: Tuple[float, float]
    
    # 獎勵統計
    mean_reward: float = 0.0
    std_reward: float = 0.0
    reward_distribution: Optional[Dict[str, float]] = None
    
    # 獎勵結構
    sparsity: float = 0.0
    delayed_reward: bool = False
    reward_shaping: bool = False
    
    # 獎勵動力學
    reward_stability: float = 0.0
    reward_predictability: float = 0.0


@dataclass
class DynamicsFeatures:
    """動力學特徵"""
    # 環境特性
    stochastic: bool = False
    deterministic: bool = True
    stationary: bool = True
    
    # 複雜度指標
    state_transition_complexity: float = 0.0
    environment_complexity: float = 0.0
    
    # 時間特徵
    episode_length: int = 0
    time_horizon: str = "finite"  # finite, infinite
    
    # 多智能體特徵
    multi_agent: bool = False
    agent_interactions: float = 0.0
    
    # 環境穩定性
    environment_stability: float = 0.0
    non_stationarity: float = 0.0


@dataclass
class EnvironmentFeatures:
    """環境特徵集合"""
    environment_id: str
    environment_type: EnvironmentType
    
    # 核心特徵
    state_space: StateSpaceFeatures
    action_space: ActionSpaceFeatures
    reward_features: RewardFeatures
    dynamics_features: DynamicsFeatures
    
    # 複雜度指標
    overall_complexity: float = 0.0
    learning_difficulty: float = 0.0
    
    # 元數據
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    sample_size: int = 0
    confidence_level: float = 0.0


@dataclass
class AnalysisResult:
    """分析結果"""
    analysis_id: str
    environment_features: EnvironmentFeatures
    
    # 分析統計
    analysis_time_seconds: float = 0.0
    data_quality_score: float = 0.0
    
    # 算法建議
    recommended_algorithms: List[str] = field(default_factory=list)
    algorithm_suitability: Dict[str, float] = field(default_factory=dict)
    
    # 分析報告
    analysis_report: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)


class EnvironmentAnalyzer:
    """環境分析器"""
    
    def __init__(self, cache_size: int = 100):
        """
        初始化環境分析器
        
        Args:
            cache_size: 分析結果緩存大小
        """
        self.cache_size = cache_size
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        self.analysis_history: List[AnalysisResult] = []
        
        # 算法適用性矩陣
        self.algorithm_suitability_matrix = {
            "DQN": {
                "discrete_action": 1.0,
                "continuous_action": 0.2,
                "discrete_state": 0.8,
                "continuous_state": 0.9,
                "sparse_reward": 0.7,
                "dense_reward": 0.9,
                "high_complexity": 0.6,
                "low_complexity": 0.8
            },
            "PPO": {
                "discrete_action": 0.8,
                "continuous_action": 0.9,
                "discrete_state": 0.7,
                "continuous_state": 0.8,
                "sparse_reward": 0.8,
                "dense_reward": 0.8,
                "high_complexity": 0.9,
                "low_complexity": 0.7
            },
            "SAC": {
                "discrete_action": 0.3,
                "continuous_action": 1.0,
                "discrete_state": 0.6,
                "continuous_state": 0.9,
                "sparse_reward": 0.6,
                "dense_reward": 0.8,
                "high_complexity": 0.8,
                "low_complexity": 0.6
            }
        }
        
        logger.info("環境分析器初始化完成")
    
    async def analyze_environment(self,
                                environment_data: Dict[str, Any],
                                environment_id: str,
                                sample_size: int = 1000) -> AnalysisResult:
        """
        分析環境特徵
        
        Args:
            environment_data: 環境數據
            environment_id: 環境ID
            sample_size: 樣本大小
            
        Returns:
            分析結果
        """
        # 檢查緩存
        if environment_id in self.analysis_cache:
            logger.info(f"使用緩存的分析結果: {environment_id}")
            return self.analysis_cache[environment_id]
        
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        try:
            logger.info(f"開始環境分析: {environment_id}")
            
            # 分析狀態空間
            state_space = await self._analyze_state_space(environment_data, sample_size)
            
            # 分析動作空間
            action_space = await self._analyze_action_space(environment_data, sample_size)
            
            # 分析獎勵結構
            reward_features = await self._analyze_reward_structure(environment_data, sample_size)
            
            # 分析環境動力學
            dynamics_features = await self._analyze_environment_dynamics(environment_data, sample_size)
            
            # 確定環境類型
            env_type = self._determine_environment_type(state_space, action_space)
            
            # 計算複雜度指標
            overall_complexity = self._calculate_overall_complexity(
                state_space, action_space, reward_features, dynamics_features
            )
            
            learning_difficulty = self._calculate_learning_difficulty(
                state_space, action_space, reward_features, dynamics_features
            )
            
            # 構建環境特徵
            environment_features = EnvironmentFeatures(
                environment_id=environment_id,
                environment_type=env_type,
                state_space=state_space,
                action_space=action_space,
                reward_features=reward_features,
                dynamics_features=dynamics_features,
                overall_complexity=overall_complexity,
                learning_difficulty=learning_difficulty,
                sample_size=sample_size,
                confidence_level=0.95
            )
            
            # 生成算法建議
            recommended_algorithms, algorithm_suitability = await self._generate_algorithm_recommendations(
                environment_features
            )
            
            # 計算分析時間
            end_time = datetime.now()
            analysis_time = (end_time - start_time).total_seconds()
            
            # 構建分析結果
            result = AnalysisResult(
                analysis_id=analysis_id,
                environment_features=environment_features,
                analysis_time_seconds=analysis_time,
                data_quality_score=0.9,  # 模擬數據質量評分
                recommended_algorithms=recommended_algorithms,
                algorithm_suitability=algorithm_suitability
            )
            
            # 生成分析報告
            await self._generate_analysis_report(result)
            
            # 緩存結果
            self._cache_result(environment_id, result)
            
            logger.info(f"環境分析完成: {analysis_id}")
            return result
            
        except Exception as e:
            logger.error(f"環境分析失敗: {e}")
            # 返回默認結果
            return AnalysisResult(
                analysis_id=analysis_id,
                environment_features=EnvironmentFeatures(
                    environment_id=environment_id,
                    environment_type=EnvironmentType.DISCRETE,
                    state_space=StateSpaceFeatures(
                        space_type=StateSpaceType.DISCRETE,
                        dimensions=1,
                        shape=(1,)
                    ),
                    action_space=ActionSpaceFeatures(
                        space_type=ActionSpaceType.DISCRETE,
                        dimensions=1,
                        shape=(1,)
                    ),
                    reward_features=RewardFeatures(
                        reward_type="sparse",
                        reward_range=(0.0, 1.0)
                    ),
                    dynamics_features=DynamicsFeatures()
                ),
                warnings=[f"分析失敗: {str(e)}"]
            )
    
    async def _analyze_state_space(self, environment_data: Dict[str, Any], sample_size: int) -> StateSpaceFeatures:
        """分析狀態空間"""
        logger.info("分析狀態空間特徵")
        
        # 模擬狀態空間分析
        await asyncio.sleep(0.05)
        
        # 從環境數據中提取狀態信息
        state_info = environment_data.get("state_space", {})
        
        # 確定狀態空間類型
        if state_info.get("type") == "image":
            space_type = StateSpaceType.IMAGE
            dimensions = np.prod(state_info.get("shape", (84, 84, 3)))
            shape = tuple(state_info.get("shape", (84, 84, 3)))
        elif state_info.get("type") == "continuous":
            space_type = StateSpaceType.CONTINUOUS
            dimensions = state_info.get("dimensions", 4)
            shape = (dimensions,)
        else:
            space_type = StateSpaceType.DISCRETE
            dimensions = state_info.get("dimensions", 10)
            shape = (dimensions,)
        
        # 生成模擬統計數據
        mean_values = [np.random.normal(0, 1) for _ in range(dimensions)]
        std_values = [np.random.uniform(0.5, 2.0) for _ in range(dimensions)]
        
        return StateSpaceFeatures(
            space_type=space_type,
            dimensions=dimensions,
            shape=shape,
            mean_values=mean_values,
            std_values=std_values,
            sparsity=np.random.uniform(0.1, 0.5),
            entropy=np.random.uniform(2.0, 5.0),
            temporal_dependency=np.random.uniform(0.3, 0.8),
            markov_property=np.random.uniform(0.7, 0.95)
        )
    
    async def _analyze_action_space(self, environment_data: Dict[str, Any], sample_size: int) -> ActionSpaceFeatures:
        """分析動作空間"""
        logger.info("分析動作空間特徵")
        
        # 模擬動作空間分析
        await asyncio.sleep(0.03)
        
        # 從環境數據中提取動作信息
        action_info = environment_data.get("action_space", {})
        
        # 確定動作空間類型
        if action_info.get("type") == "continuous":
            space_type = ActionSpaceType.CONTINUOUS
            dimensions = action_info.get("dimensions", 2)
            shape = (dimensions,)
            min_actions = [-1.0] * dimensions
            max_actions = [1.0] * dimensions
            discrete_actions = None
        else:
            space_type = ActionSpaceType.DISCRETE
            dimensions = action_info.get("dimensions", 4)
            shape = (dimensions,)
            min_actions = None
            max_actions = None
            discrete_actions = list(range(dimensions))
        
        return ActionSpaceFeatures(
            space_type=space_type,
            dimensions=dimensions,
            shape=shape,
            min_actions=min_actions,
            max_actions=max_actions,
            discrete_actions=discrete_actions,
            action_entropy=np.random.uniform(1.0, 3.0),
            action_masking=action_info.get("masking", False)
        )
    
    async def _analyze_reward_structure(self, environment_data: Dict[str, Any], sample_size: int) -> RewardFeatures:
        """分析獎勵結構"""
        logger.info("分析獎勵結構特徵")
        
        # 模擬獎勵分析
        await asyncio.sleep(0.02)
        
        # 從環境數據中提取獎勵信息
        reward_info = environment_data.get("reward_structure", {})
        
        reward_type = reward_info.get("type", "sparse")
        reward_range = tuple(reward_info.get("range", (-1.0, 1.0)))
        
        return RewardFeatures(
            reward_type=reward_type,
            reward_range=reward_range,
            mean_reward=np.random.uniform(reward_range[0], reward_range[1]),
            std_reward=np.random.uniform(0.1, 0.5),
            sparsity=0.8 if reward_type == "sparse" else 0.2,
            delayed_reward=reward_info.get("delayed", False),
            reward_shaping=reward_info.get("shaping", False),
            reward_stability=np.random.uniform(0.7, 0.9),
            reward_predictability=np.random.uniform(0.6, 0.8)
        )
    
    async def _analyze_environment_dynamics(self, environment_data: Dict[str, Any], sample_size: int) -> DynamicsFeatures:
        """分析環境動力學"""
        logger.info("分析環境動力學特徵")
        
        # 模擬動力學分析
        await asyncio.sleep(0.04)
        
        # 從環境數據中提取動力學信息
        dynamics_info = environment_data.get("dynamics", {})
        
        return DynamicsFeatures(
            stochastic=dynamics_info.get("stochastic", True),
            deterministic=not dynamics_info.get("stochastic", True),
            stationary=dynamics_info.get("stationary", True),
            state_transition_complexity=np.random.uniform(0.3, 0.8),
            environment_complexity=np.random.uniform(0.4, 0.9),
            episode_length=dynamics_info.get("episode_length", 200),
            time_horizon=dynamics_info.get("time_horizon", "finite"),
            multi_agent=dynamics_info.get("multi_agent", False),
            agent_interactions=np.random.uniform(0.0, 0.5),
            environment_stability=np.random.uniform(0.8, 0.95),
            non_stationarity=np.random.uniform(0.0, 0.2)
        )
    
    def _determine_environment_type(self, state_space: StateSpaceFeatures, action_space: ActionSpaceFeatures) -> EnvironmentType:
        """確定環境類型"""
        if action_space.space_type == ActionSpaceType.CONTINUOUS:
            return EnvironmentType.CONTINUOUS
        elif action_space.space_type == ActionSpaceType.DISCRETE:
            return EnvironmentType.DISCRETE
        elif action_space.space_type == ActionSpaceType.MULTI_DISCRETE:
            return EnvironmentType.MULTI_DISCRETE
        else:
            return EnvironmentType.MIXED
    
    def _calculate_overall_complexity(self,
                                    state_space: StateSpaceFeatures,
                                    action_space: ActionSpaceFeatures,
                                    reward_features: RewardFeatures,
                                    dynamics_features: DynamicsFeatures) -> float:
        """計算整體複雜度"""
        # 狀態空間複雜度
        state_complexity = min(np.log(state_space.dimensions) / 10, 1.0)
        
        # 動作空間複雜度
        action_complexity = min(np.log(action_space.dimensions) / 10, 1.0)
        
        # 獎勵複雜度
        reward_complexity = reward_features.sparsity * 0.5 + (1 - reward_features.reward_stability) * 0.5
        
        # 動力學複雜度
        dynamics_complexity = dynamics_features.state_transition_complexity
        
        # 綜合複雜度
        overall_complexity = (
            state_complexity * 0.3 +
            action_complexity * 0.2 +
            reward_complexity * 0.2 +
            dynamics_complexity * 0.3
        )
        
        return min(overall_complexity, 1.0)
    
    def _calculate_learning_difficulty(self,
                                     state_space: StateSpaceFeatures,
                                     action_space: ActionSpaceFeatures,
                                     reward_features: RewardFeatures,
                                     dynamics_features: DynamicsFeatures) -> float:
        """計算學習難度"""
        # 基於各種因素計算學習難度
        difficulty_factors = [
            reward_features.sparsity,  # 獎勵稀疏性
            1 - reward_features.reward_stability,  # 獎勵不穩定性
            dynamics_features.state_transition_complexity,  # 狀態轉換複雜度
            dynamics_features.non_stationarity,  # 非平穩性
            1 - state_space.markov_property  # 非馬爾科夫性
        ]
        
        return np.mean(difficulty_factors)
    
    async def _generate_algorithm_recommendations(self, features: EnvironmentFeatures) -> Tuple[List[str], Dict[str, float]]:
        """生成算法建議"""
        logger.info("生成算法建議")
        
        suitability_scores = {}
        
        for algorithm, criteria in self.algorithm_suitability_matrix.items():
            score = 0.0
            
            # 動作空間適應性
            if features.action_space.space_type == ActionSpaceType.DISCRETE:
                score += criteria["discrete_action"] * 0.3
            else:
                score += criteria["continuous_action"] * 0.3
            
            # 狀態空間適應性
            if features.state_space.space_type in [StateSpaceType.DISCRETE, StateSpaceType.IMAGE]:
                score += criteria["discrete_state"] * 0.2
            else:
                score += criteria["continuous_state"] * 0.2
            
            # 獎勵結構適應性
            if features.reward_features.reward_type == "sparse":
                score += criteria["sparse_reward"] * 0.2
            else:
                score += criteria["dense_reward"] * 0.2
            
            # 複雜度適應性
            if features.overall_complexity > 0.7:
                score += criteria["high_complexity"] * 0.3
            else:
                score += criteria["low_complexity"] * 0.3
            
            suitability_scores[algorithm] = score
        
        # 排序算法
        sorted_algorithms = sorted(suitability_scores.items(), key=lambda x: x[1], reverse=True)
        recommended_algorithms = [alg for alg, _ in sorted_algorithms]
        
        return recommended_algorithms, suitability_scores
    
    async def _generate_analysis_report(self, result: AnalysisResult):
        """生成分析報告"""
        features = result.environment_features
        report = []
        
        # 環境概述
        report.append(f"環境類型: {features.environment_type.value}")
        report.append(f"整體複雜度: {features.overall_complexity:.2f}")
        report.append(f"學習難度: {features.learning_difficulty:.2f}")
        
        # 狀態空間分析
        report.append(f"狀態空間: {features.state_space.space_type.value}, 維度: {features.state_space.dimensions}")
        report.append(f"狀態空間稀疏性: {features.state_space.sparsity:.2f}")
        
        # 動作空間分析
        report.append(f"動作空間: {features.action_space.space_type.value}, 維度: {features.action_space.dimensions}")
        
        # 獎勵分析
        report.append(f"獎勵類型: {features.reward_features.reward_type}")
        report.append(f"獎勵稀疏性: {features.reward_features.sparsity:.2f}")
        
        # 算法建議
        top_algorithm = result.recommended_algorithms[0] if result.recommended_algorithms else "無"
        report.append(f"推薦算法: {top_algorithm}")
        
        result.analysis_report = report
    
    def _cache_result(self, environment_id: str, result: AnalysisResult):
        """緩存分析結果"""
        # 添加到緩存
        self.analysis_cache[environment_id] = result
        
        # 添加到歷史
        self.analysis_history.append(result)
        
        # 維護緩存大小
        if len(self.analysis_cache) > self.cache_size:
            # 移除最舊的條目
            oldest_id = min(self.analysis_cache.keys(), 
                          key=lambda x: self.analysis_cache[x].timestamp)
            del self.analysis_cache[oldest_id]
    
    def get_analysis_history(self) -> List[AnalysisResult]:
        """獲取分析歷史"""
        return self.analysis_history.copy()
    
    def clear_cache(self):
        """清除緩存"""
        self.analysis_cache.clear()
        logger.info("分析緩存已清除")
    
    def get_cached_analysis(self, environment_id: str) -> Optional[AnalysisResult]:
        """獲取緩存的分析結果"""
        return self.analysis_cache.get(environment_id)
    
    def update_suitability_matrix(self, algorithm: str, criteria: Dict[str, float]):
        """更新算法適用性矩陣"""
        if algorithm in self.algorithm_suitability_matrix:
            self.algorithm_suitability_matrix[algorithm].update(criteria)
            logger.info(f"更新 {algorithm} 適用性矩陣")
        else:
            logger.warning(f"算法 {algorithm} 不存在於適用性矩陣中")
