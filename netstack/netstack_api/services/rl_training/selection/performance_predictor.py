"""
性能預測器 - Phase 3 核心組件

基於環境特徵和算法特性預測強化學習算法的性能表現，
支援多種預測模型和不確定性量化。

主要功能：
- 算法性能預測
- 收斂速度預測
- 穩定性評估
- 不確定性量化
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import json

from .environment_analyzer import EnvironmentFeatures

logger = logging.getLogger(__name__)


class PredictionModel(Enum):
    """預測模型類型"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    HEURISTIC = "heuristic"


class PredictionMetric(Enum):
    """預測指標"""
    PERFORMANCE = "performance"
    CONVERGENCE_SPEED = "convergence_speed"
    STABILITY = "stability"
    SAMPLE_EFFICIENCY = "sample_efficiency"
    ROBUSTNESS = "robustness"


@dataclass
class PredictionConfig:
    """預測配置"""
    model_type: PredictionModel = PredictionModel.ENSEMBLE
    
    # 預測參數
    prediction_horizon: int = 1000
    confidence_level: float = 0.95
    
    # 模型參數
    ensemble_weights: Dict[str, float] = field(default_factory=lambda: {
        "heuristic": 0.4,
        "random_forest": 0.3,
        "neural_network": 0.3
    })
    
    # 不確定性量化
    uncertainty_estimation: bool = True
    bootstrap_samples: int = 100
    
    # 驗證參數
    cross_validation: bool = True
    validation_splits: int = 5


@dataclass
class PredictionResult:
    """預測結果"""
    prediction_id: str
    algorithm: str
    environment_id: str
    
    # 核心預測
    predicted_performance: float = 0.0
    predicted_convergence: int = 0
    predicted_episodes_to_solve: int = 0
    
    # 置信度和不確定性
    confidence_score: float = 0.0
    uncertainty_range: Tuple[float, float] = (0.0, 0.0)
    
    # 詳細指標
    stability_score: float = 0.0
    sample_efficiency: float = 0.0
    robustness_score: float = 0.0
    
    # 預測統計
    prediction_time_seconds: float = 0.0
    model_confidence: float = 0.0
    
    # 預測基礎
    feature_importance: Dict[str, float] = field(default_factory=dict)
    prediction_rationale: List[str] = field(default_factory=list)
    
    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)


class PerformancePredictor:
    """性能預測器"""
    
    def __init__(self, device: str = "cpu"):
        """
        初始化性能預測器
        
        Args:
            device: 計算設備
        """
        self.device = device
        self.prediction_history: List[PredictionResult] = []
        
        # 預測模型
        self.models = {
            PredictionModel.LINEAR_REGRESSION: LinearRegression(),
            PredictionModel.RANDOM_FOREST: RandomForestRegressor(n_estimators=100, random_state=42),
            PredictionModel.NEURAL_NETWORK: None,  # 稍後初始化
            PredictionModel.HEURISTIC: None  # 基於規則的預測
        }
        
        # 算法基準性能數據
        self.algorithm_baselines = {
            "DQN": {
                "base_performance": 0.75,
                "convergence_episodes": 800,
                "stability_factor": 0.8,
                "sample_efficiency": 0.6,
                "robustness": 0.7
            },
            "PPO": {
                "base_performance": 0.80,
                "convergence_episodes": 600,
                "stability_factor": 0.85,
                "sample_efficiency": 0.7,
                "robustness": 0.8
            },
            "SAC": {
                "base_performance": 0.85,
                "convergence_episodes": 400,
                "stability_factor": 0.9,
                "sample_efficiency": 0.8,
                "robustness": 0.85
            },
            "A2C": {
                "base_performance": 0.70,
                "convergence_episodes": 700,
                "stability_factor": 0.75,
                "sample_efficiency": 0.65,
                "robustness": 0.7
            },
            "TD3": {
                "base_performance": 0.82,
                "convergence_episodes": 500,
                "stability_factor": 0.88,
                "sample_efficiency": 0.75,
                "robustness": 0.8
            }
        }
        
        # 環境因子權重
        self.environment_factors = {
            "state_space_complexity": 0.2,
            "action_space_complexity": 0.15,
            "reward_sparsity": 0.2,
            "dynamics_complexity": 0.25,
            "overall_complexity": 0.2
        }
        
        logger.info("性能預測器初始化完成")
    
    async def predict_performance(self,
                                algorithm: str,
                                environment_features: EnvironmentFeatures,
                                model_type: PredictionModel,
                                horizon: int = 1000) -> PredictionResult:
        """
        預測算法性能
        
        Args:
            algorithm: 算法名稱
            environment_features: 環境特徵
            model_type: 預測模型類型
            horizon: 預測範圍
            
        Returns:
            預測結果
        """
        prediction_id = f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        try:
            logger.info(f"開始性能預測: {algorithm} - {model_type.value}")
            
            # 準備特徵向量
            feature_vector = self._prepare_feature_vector(environment_features)
            
            # 執行預測
            if model_type == PredictionModel.HEURISTIC:
                prediction = await self._heuristic_prediction(algorithm, environment_features, horizon)
            elif model_type == PredictionModel.RANDOM_FOREST:
                prediction = await self._random_forest_prediction(algorithm, feature_vector, horizon)
            elif model_type == PredictionModel.NEURAL_NETWORK:
                prediction = await self._neural_network_prediction(algorithm, feature_vector, horizon)
            elif model_type == PredictionModel.ENSEMBLE:
                prediction = await self._ensemble_prediction(algorithm, environment_features, feature_vector, horizon)
            else:
                prediction = await self._linear_regression_prediction(algorithm, feature_vector, horizon)
            
            # 設置基本信息
            prediction.prediction_id = prediction_id
            prediction.algorithm = algorithm
            prediction.environment_id = environment_features.environment_id
            
            # 計算預測時間
            end_time = datetime.now()
            prediction.prediction_time_seconds = (end_time - start_time).total_seconds()
            
            # 計算特徵重要性
            prediction.feature_importance = self._calculate_feature_importance(
                algorithm, environment_features
            )
            
            # 生成預測理由
            prediction.prediction_rationale = self._generate_prediction_rationale(
                algorithm, environment_features, prediction
            )
            
            # 保存預測結果
            self.prediction_history.append(prediction)
            
            logger.info(f"性能預測完成: {prediction_id}")
            return prediction
            
        except Exception as e:
            logger.error(f"性能預測失敗: {e}")
            # 返回默認預測
            return PredictionResult(
                prediction_id=prediction_id,
                algorithm=algorithm,
                environment_id=environment_features.environment_id,
                predicted_performance=0.7,
                predicted_convergence=500,
                confidence_score=0.5,
                prediction_rationale=[f"預測失敗: {str(e)}"]
            )
    
    def _prepare_feature_vector(self, environment_features: EnvironmentFeatures) -> np.ndarray:
        """準備特徵向量"""
        features = [
            # 狀態空間特徵
            environment_features.state_space.dimensions / 100,
            environment_features.state_space.sparsity,
            environment_features.state_space.entropy / 10,
            environment_features.state_space.temporal_dependency,
            environment_features.state_space.markov_property,
            
            # 動作空間特徵
            environment_features.action_space.dimensions / 10,
            environment_features.action_space.action_entropy / 5,
            float(environment_features.action_space.action_masking),
            
            # 獎勵特徵
            environment_features.reward_features.sparsity,
            environment_features.reward_features.reward_stability,
            environment_features.reward_features.reward_predictability,
            float(environment_features.reward_features.delayed_reward),
            
            # 動力學特徵
            environment_features.dynamics_features.state_transition_complexity,
            environment_features.dynamics_features.environment_complexity,
            environment_features.dynamics_features.environment_stability,
            environment_features.dynamics_features.non_stationarity,
            
            # 綜合特徵
            environment_features.overall_complexity,
            environment_features.learning_difficulty,
            environment_features.dynamics_features.episode_length / 1000,
            float(environment_features.dynamics_features.multi_agent)
        ]
        
        return np.array(features)
    
    async def _heuristic_prediction(self,
                                   algorithm: str,
                                   environment_features: EnvironmentFeatures,
                                   horizon: int) -> PredictionResult:
        """基於啟發式規則的預測"""
        logger.info("執行啟發式預測")
        
        if algorithm not in self.algorithm_baselines:
            algorithm = "DQN"  # 默認算法
        
        baseline = self.algorithm_baselines[algorithm]
        
        # 基於環境特徵調整基準性能
        performance_adjustment = 0.0
        
        # 狀態空間複雜度影響
        state_complexity_factor = min(environment_features.state_space.dimensions / 100, 1.0)
        performance_adjustment -= state_complexity_factor * 0.1
        
        # 動作空間複雜度影響
        action_complexity_factor = min(environment_features.action_space.dimensions / 10, 1.0)
        performance_adjustment -= action_complexity_factor * 0.05
        
        # 獎勵稀疏性影響
        reward_sparsity_penalty = environment_features.reward_features.sparsity * 0.15
        performance_adjustment -= reward_sparsity_penalty
        
        # 環境穩定性影響
        stability_bonus = environment_features.dynamics_features.environment_stability * 0.1
        performance_adjustment += stability_bonus
        
        # 計算最終預測
        predicted_performance = baseline["base_performance"] + performance_adjustment
        predicted_performance = max(0.1, min(0.95, predicted_performance))
        
        # 收斂速度預測
        convergence_adjustment = 1.0 + environment_features.learning_difficulty * 0.5
        predicted_convergence = int(baseline["convergence_episodes"] * convergence_adjustment)
        
        # 穩定性預測
        stability_adjustment = 1.0 - environment_features.dynamics_features.non_stationarity * 0.2
        predicted_stability = baseline["stability_factor"] * stability_adjustment
        
        # 置信度計算
        confidence = 0.8 - environment_features.overall_complexity * 0.3
        confidence = max(0.3, min(0.95, confidence))
        
        # 不確定性範圍
        uncertainty_range = (
            predicted_performance - 0.1,
            predicted_performance + 0.1
        )
        
        return PredictionResult(
            predicted_performance=predicted_performance,
            predicted_convergence=predicted_convergence,
            predicted_episodes_to_solve=predicted_convergence,
            confidence_score=confidence,
            uncertainty_range=uncertainty_range,
            stability_score=predicted_stability,
            sample_efficiency=baseline["sample_efficiency"],
            robustness_score=baseline["robustness"],
            model_confidence=0.9
        )
    
    async def _random_forest_prediction(self,
                                      algorithm: str,
                                      feature_vector: np.ndarray,
                                      horizon: int) -> PredictionResult:
        """隨機森林預測"""
        logger.info("執行隨機森林預測")
        
        # 模擬隨機森林預測
        await asyncio.sleep(0.05)  # 模擬計算時間
        
        if algorithm not in self.algorithm_baselines:
            algorithm = "DQN"
        
        baseline = self.algorithm_baselines[algorithm]
        
        # 模擬隨機森林的預測結果
        feature_impact = np.sum(feature_vector * np.random.uniform(0.5, 1.5, len(feature_vector)))
        normalized_impact = feature_impact / len(feature_vector)
        
        predicted_performance = baseline["base_performance"] * (0.8 + normalized_impact * 0.4)
        predicted_performance = max(0.1, min(0.95, predicted_performance))
        
        # 收斂預測
        convergence_factor = 1.0 + (1.0 - normalized_impact) * 0.5
        predicted_convergence = int(baseline["convergence_episodes"] * convergence_factor)
        
        # 置信度
        confidence = 0.85 - abs(normalized_impact - 0.5) * 0.3
        
        return PredictionResult(
            predicted_performance=predicted_performance,
            predicted_convergence=predicted_convergence,
            predicted_episodes_to_solve=predicted_convergence,
            confidence_score=confidence,
            uncertainty_range=(predicted_performance - 0.08, predicted_performance + 0.08),
            stability_score=baseline["stability_factor"],
            sample_efficiency=baseline["sample_efficiency"],
            robustness_score=baseline["robustness"],
            model_confidence=0.85
        )
    
    async def _neural_network_prediction(self,
                                       algorithm: str,
                                       feature_vector: np.ndarray,
                                       horizon: int) -> PredictionResult:
        """神經網絡預測"""
        logger.info("執行神經網絡預測")
        
        # 模擬神經網絡預測
        await asyncio.sleep(0.1)  # 模擬計算時間
        
        if algorithm not in self.algorithm_baselines:
            algorithm = "DQN"
        
        baseline = self.algorithm_baselines[algorithm]
        
        # 模擬神經網絡的非線性預測
        hidden_layer = np.tanh(np.dot(feature_vector, np.random.randn(len(feature_vector), 10)))
        output = np.dot(hidden_layer, np.random.randn(10, 1))[0]
        
        # 歸一化輸出
        predicted_performance = baseline["base_performance"] + output * 0.1
        predicted_performance = max(0.1, min(0.95, predicted_performance))
        
        # 收斂預測
        convergence_output = np.dot(hidden_layer, np.random.randn(10, 1))[0]
        convergence_factor = 1.0 + convergence_output * 0.3
        predicted_convergence = int(baseline["convergence_episodes"] * convergence_factor)
        
        # 置信度
        confidence = 0.9 - abs(output) * 0.2
        confidence = max(0.5, min(0.95, confidence))
        
        return PredictionResult(
            predicted_performance=predicted_performance,
            predicted_convergence=predicted_convergence,
            predicted_episodes_to_solve=predicted_convergence,
            confidence_score=confidence,
            uncertainty_range=(predicted_performance - 0.06, predicted_performance + 0.06),
            stability_score=baseline["stability_factor"],
            sample_efficiency=baseline["sample_efficiency"],
            robustness_score=baseline["robustness"],
            model_confidence=0.9
        )
    
    async def _linear_regression_prediction(self,
                                          algorithm: str,
                                          feature_vector: np.ndarray,
                                          horizon: int) -> PredictionResult:
        """線性回歸預測"""
        logger.info("執行線性回歸預測")
        
        # 模擬線性回歸預測
        await asyncio.sleep(0.02)  # 模擬計算時間
        
        if algorithm not in self.algorithm_baselines:
            algorithm = "DQN"
        
        baseline = self.algorithm_baselines[algorithm]
        
        # 模擬線性回歸的預測結果
        weights = np.random.randn(len(feature_vector))
        linear_output = np.dot(feature_vector, weights)
        
        predicted_performance = baseline["base_performance"] + linear_output * 0.05
        predicted_performance = max(0.1, min(0.95, predicted_performance))
        
        # 收斂預測
        convergence_factor = 1.0 + linear_output * 0.1
        predicted_convergence = int(baseline["convergence_episodes"] * convergence_factor)
        
        # 置信度
        confidence = 0.7 - abs(linear_output) * 0.1
        confidence = max(0.4, min(0.9, confidence))
        
        return PredictionResult(
            predicted_performance=predicted_performance,
            predicted_convergence=predicted_convergence,
            predicted_episodes_to_solve=predicted_convergence,
            confidence_score=confidence,
            uncertainty_range=(predicted_performance - 0.1, predicted_performance + 0.1),
            stability_score=baseline["stability_factor"],
            sample_efficiency=baseline["sample_efficiency"],
            robustness_score=baseline["robustness"],
            model_confidence=0.7
        )
    
    async def _ensemble_prediction(self,
                                 algorithm: str,
                                 environment_features: EnvironmentFeatures,
                                 feature_vector: np.ndarray,
                                 horizon: int) -> PredictionResult:
        """集成預測"""
        logger.info("執行集成預測")
        
        # 獲取各個模型的預測
        heuristic_pred = await self._heuristic_prediction(algorithm, environment_features, horizon)
        rf_pred = await self._random_forest_prediction(algorithm, feature_vector, horizon)
        nn_pred = await self._neural_network_prediction(algorithm, feature_vector, horizon)
        
        # 集成權重
        weights = {
            "heuristic": 0.4,
            "random_forest": 0.3,
            "neural_network": 0.3
        }
        
        # 加權平均
        ensemble_performance = (
            heuristic_pred.predicted_performance * weights["heuristic"] +
            rf_pred.predicted_performance * weights["random_forest"] +
            nn_pred.predicted_performance * weights["neural_network"]
        )
        
        ensemble_convergence = int(
            heuristic_pred.predicted_convergence * weights["heuristic"] +
            rf_pred.predicted_convergence * weights["random_forest"] +
            nn_pred.predicted_convergence * weights["neural_network"]
        )
        
        ensemble_confidence = (
            heuristic_pred.confidence_score * weights["heuristic"] +
            rf_pred.confidence_score * weights["random_forest"] +
            nn_pred.confidence_score * weights["neural_network"]
        )
        
        # 不確定性範圍
        all_performances = [
            heuristic_pred.predicted_performance,
            rf_pred.predicted_performance,
            nn_pred.predicted_performance
        ]
        uncertainty_range = (min(all_performances), max(all_performances))
        
        return PredictionResult(
            predicted_performance=ensemble_performance,
            predicted_convergence=ensemble_convergence,
            predicted_episodes_to_solve=ensemble_convergence,
            confidence_score=ensemble_confidence,
            uncertainty_range=uncertainty_range,
            stability_score=heuristic_pred.stability_score,
            sample_efficiency=heuristic_pred.sample_efficiency,
            robustness_score=heuristic_pred.robustness_score,
            model_confidence=0.95
        )
    
    def _calculate_feature_importance(self,
                                    algorithm: str,
                                    environment_features: EnvironmentFeatures) -> Dict[str, float]:
        """計算特徵重要性"""
        importance = {}
        
        # 基於算法特性調整特徵重要性
        if algorithm == "DQN":
            importance = {
                "state_space_complexity": 0.3,
                "action_space_type": 0.25,
                "reward_sparsity": 0.2,
                "environment_stability": 0.15,
                "learning_difficulty": 0.1
            }
        elif algorithm == "PPO":
            importance = {
                "environment_complexity": 0.3,
                "reward_structure": 0.25,
                "dynamics_complexity": 0.2,
                "state_space_complexity": 0.15,
                "action_space_complexity": 0.1
            }
        elif algorithm == "SAC":
            importance = {
                "action_space_continuity": 0.35,
                "reward_density": 0.25,
                "environment_stability": 0.2,
                "state_space_complexity": 0.15,
                "learning_difficulty": 0.05
            }
        else:
            # 默認重要性
            importance = {
                "overall_complexity": 0.25,
                "learning_difficulty": 0.2,
                "state_space_complexity": 0.2,
                "action_space_complexity": 0.2,
                "reward_sparsity": 0.15
            }
        
        return importance
    
    def _generate_prediction_rationale(self,
                                     algorithm: str,
                                     environment_features: EnvironmentFeatures,
                                     prediction: PredictionResult) -> List[str]:
        """生成預測理由"""
        rationale = []
        
        # 基於算法特性
        if algorithm == "DQN":
            if environment_features.action_space.space_type.value == "discrete":
                rationale.append("DQN 適合離散動作空間")
            else:
                rationale.append("DQN 對連續動作空間支持有限")
        
        elif algorithm == "PPO":
            rationale.append("PPO 對各種環境類型都有良好的適應性")
            if environment_features.overall_complexity > 0.7:
                rationale.append("PPO 在複雜環境中表現穩定")
        
        elif algorithm == "SAC":
            if environment_features.action_space.space_type.value == "continuous":
                rationale.append("SAC 在連續動作空間中表現優異")
            if environment_features.reward_features.reward_type == "dense":
                rationale.append("SAC 適合密集獎勵環境")
        
        # 基於環境特徵
        if environment_features.overall_complexity > 0.8:
            rationale.append("高複雜度環境可能需要更長的訓練時間")
        
        if environment_features.reward_features.sparsity > 0.7:
            rationale.append("稀疏獎勵環境增加了學習難度")
        
        if environment_features.dynamics_features.environment_stability > 0.9:
            rationale.append("穩定的環境有利於收斂")
        
        # 基於預測結果
        if prediction.confidence_score > 0.8:
            rationale.append("高置信度預測，模型對此配置有把握")
        elif prediction.confidence_score < 0.6:
            rationale.append("低置信度預測，建議謹慎使用")
        
        return rationale
    
    def get_prediction_history(self) -> List[PredictionResult]:
        """獲取預測歷史"""
        return self.prediction_history.copy()
    
    def get_algorithm_baselines(self) -> Dict[str, Dict[str, float]]:
        """獲取算法基準數據"""
        return self.algorithm_baselines.copy()
    
    def update_algorithm_baseline(self, algorithm: str, baseline_data: Dict[str, float]):
        """更新算法基準數據"""
        if algorithm in self.algorithm_baselines:
            self.algorithm_baselines[algorithm].update(baseline_data)
            logger.info(f"更新 {algorithm} 基準數據")
        else:
            self.algorithm_baselines[algorithm] = baseline_data
            logger.info(f"添加新算法基準數據: {algorithm}")
    
    def get_model_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """獲取模型性能統計"""
        if not self.prediction_history:
            return {}
        
        stats = {}
        
        # 按模型類型統計
        for model_type in PredictionModel:
            model_predictions = [
                p for p in self.prediction_history 
                if hasattr(p, 'model_type') and p.model_type == model_type
            ]
            
            if model_predictions:
                stats[model_type.value] = {
                    "count": len(model_predictions),
                    "avg_confidence": np.mean([p.confidence_score for p in model_predictions]),
                    "avg_prediction_time": np.mean([p.prediction_time_seconds for p in model_predictions]),
                    "avg_model_confidence": np.mean([p.model_confidence for p in model_predictions])
                }
        
        return stats
    
    async def batch_predict(self,
                          algorithms: List[str],
                          environment_features: EnvironmentFeatures,
                          model_type: PredictionModel) -> Dict[str, PredictionResult]:
        """批量預測"""
        logger.info(f"開始批量預測: {len(algorithms)} 個算法")
        
        results = {}
        
        for algorithm in algorithms:
            try:
                result = await self.predict_performance(
                    algorithm, environment_features, model_type
                )
                results[algorithm] = result
            except Exception as e:
                logger.error(f"批量預測失敗 ({algorithm}): {e}")
                # 繼續處理其他算法
        
        logger.info(f"批量預測完成: {len(results)} 個成功")
        return results
