"""
Prediction Accuracy Optimization System
預測準確率優化系統
實現動態調整和機器學習增強以達到 >95% 準確率目標
"""

import asyncio
import time
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class PredictionAccuracyLevel(str, Enum):
    """預測準確率等級"""
    EXCELLENT = "excellent"    # >95%
    GOOD = "good"             # 90-95%
    AVERAGE = "average"       # 80-90%
    POOR = "poor"             # 70-80%
    CRITICAL = "critical"     # <70%


@dataclass
class PredictionAccuracyRecord:
    """預測準確率記錄"""
    ue_id: str
    predicted_satellite: str
    actual_satellite: str
    prediction_timestamp: float
    verification_timestamp: float
    is_accurate: bool
    accuracy_score: float  # 0-1
    delta_t_used: int
    weather_condition: str
    satellite_count: int
    context_factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccuracyOptimizationConfig:
    """準確率優化配置"""
    target_accuracy: float = 0.95
    min_accuracy_threshold: float = 0.8
    delta_t_min: int = 3
    delta_t_max: int = 30
    delta_t_adjustment_step: int = 2
    evaluation_window_size: int = 50
    ml_enhancement_enabled: bool = True
    adaptive_adjustment_enabled: bool = True


@dataclass
class AccuracyMetrics:
    """準確率指標"""
    current_accuracy: float
    rolling_accuracy: float
    accuracy_trend: str  # "improving", "stable", "declining"
    predictions_evaluated: int
    target_achievement: bool
    confidence_interval: Tuple[float, float]
    accuracy_by_context: Dict[str, float]


class PredictionAccuracyOptimizer:
    """預測準確率優化器"""
    
    def __init__(self, config: Optional[AccuracyOptimizationConfig] = None):
        self.config = config or AccuracyOptimizationConfig()
        
        # 準確率追蹤
        self.accuracy_records: List[PredictionAccuracyRecord] = []
        self.accuracy_history: List[float] = []
        
        # 動態參數
        self.current_delta_t = 10  # 初始預測間隔
        self.current_accuracy = 0.0
        self.last_optimization_time = time.time()
        
        # 機器學習模型 (簡化版)
        self.ml_model_weights: Dict[str, float] = {
            "weather_factor": 0.3,
            "satellite_count_factor": 0.2,
            "time_of_day_factor": 0.1,
            "ue_mobility_factor": 0.25,
            "signal_strength_factor": 0.15
        }
        
        # 優化統計
        self.optimization_history: List[Dict] = []
        self.performance_baseline: Optional[float] = None
    
    async def record_prediction_result(
        self,
        ue_id: str,
        predicted_satellite: str,
        actual_satellite: str,
        prediction_timestamp: float,
        delta_t_used: int,
        context: Dict[str, Any] = None
    ):
        """
        記錄預測結果用於準確率評估
        """
        context = context or {}
        verification_timestamp = time.time()
        
        # 計算準確率評分
        is_accurate = predicted_satellite == actual_satellite
        accuracy_score = 1.0 if is_accurate else 0.0
        
        # 如果不是完全準確，檢查部分匹配
        if not is_accurate and predicted_satellite and actual_satellite:
            # 簡化的部分匹配評分 (基於衛星 ID 相似性)
            if predicted_satellite[:3] == actual_satellite[:3]:  # 同一星座
                accuracy_score = 0.5
        
        # 創建記錄
        record = PredictionAccuracyRecord(
            ue_id=ue_id,
            predicted_satellite=predicted_satellite,
            actual_satellite=actual_satellite,
            prediction_timestamp=prediction_timestamp,
            verification_timestamp=verification_timestamp,
            is_accurate=is_accurate,
            accuracy_score=accuracy_score,
            delta_t_used=delta_t_used,
            weather_condition=context.get("weather_condition", "unknown"),
            satellite_count=context.get("satellite_count", 0),
            context_factors=context
        )
        
        self.accuracy_records.append(record)
        self.accuracy_history.append(accuracy_score)
        
        # 保持記錄在合理範圍內
        if len(self.accuracy_records) > 1000:
            self.accuracy_records = self.accuracy_records[-500:]
            self.accuracy_history = self.accuracy_history[-500:]
        
        # 更新當前準確率
        await self._update_current_accuracy()
        
        # 觸發優化檢查
        if len(self.accuracy_records) % 10 == 0:  # 每10次記錄檢查一次
            await self._trigger_optimization_check()
        
        logger.debug(f"記錄預測結果 - UE: {ue_id}, 準確: {is_accurate}, 評分: {accuracy_score:.2f}")
    
    async def _update_current_accuracy(self):
        """更新當前準確率"""
        if not self.accuracy_history:
            self.current_accuracy = 0.0
            return
        
        # 計算滾動準確率 (最近 N 次預測)
        window_size = min(self.config.evaluation_window_size, len(self.accuracy_history))
        recent_scores = self.accuracy_history[-window_size:]
        self.current_accuracy = sum(recent_scores) / len(recent_scores)
    
    async def _trigger_optimization_check(self):
        """觸發優化檢查"""
        try:
            # 檢查是否需要調整 delta_t
            if self.config.adaptive_adjustment_enabled:
                await self._adaptive_delta_t_adjustment()
            
            # 檢查是否需要 ML 優化
            if self.config.ml_enhancement_enabled:
                await self._ml_model_optimization()
            
            # 記錄優化歷史
            await self._record_optimization_state()
            
        except Exception as e:
            logger.error(f"優化檢查失敗: {e}")
    
    async def _adaptive_delta_t_adjustment(self):
        """自適應 delta_t 調整"""
        if len(self.accuracy_records) < 20:  # 需要足夠的數據
            return
        
        current_accuracy = self.current_accuracy
        target_accuracy = self.config.target_accuracy
        
        # 基於準確率調整 delta_t
        if current_accuracy < self.config.min_accuracy_threshold:
            # 準確率過低，縮短預測間隔
            new_delta_t = max(
                self.config.delta_t_min,
                self.current_delta_t - self.config.delta_t_adjustment_step
            )
            adjustment_reason = "accuracy_too_low"
            
        elif current_accuracy > target_accuracy:
            # 準確率很高，可以延長間隔以節省計算資源
            new_delta_t = min(
                self.config.delta_t_max,
                self.current_delta_t + self.config.delta_t_adjustment_step
            )
            adjustment_reason = "accuracy_excellent"
            
        else:
            # 準確率在可接受範圍內，保持現狀
            new_delta_t = self.current_delta_t
            adjustment_reason = "accuracy_acceptable"
        
        # 應用調整
        if new_delta_t != self.current_delta_t:
            old_delta_t = self.current_delta_t
            self.current_delta_t = new_delta_t
            
            logger.info(f"Delta_t 自適應調整: {old_delta_t}s -> {new_delta_t}s "
                       f"(準確率: {current_accuracy:.3f}, 原因: {adjustment_reason})")
    
    async def _ml_model_optimization(self):
        """機器學習模型優化"""
        if len(self.accuracy_records) < 50:  # 需要足夠的訓練數據
            return
        
        try:
            # 提取特徵和標籤
            features, labels = await self._extract_ml_features()
            
            if len(features) < 10:
                return
            
            # 簡化的特徵重要性分析
            await self._analyze_feature_importance(features, labels)
            
            # 更新模型權重
            await self._update_ml_weights(features, labels)
            
            logger.info("ML 模型權重已更新")
            
        except Exception as e:
            logger.error(f"ML 模型優化失敗: {e}")
    
    async def _extract_ml_features(self) -> Tuple[List[List[float]], List[float]]:
        """提取機器學習特徵"""
        features = []
        labels = []
        
        for record in self.accuracy_records[-100:]:  # 使用最近100條記錄
            # 提取特徵向量
            feature_vector = [
                self._encode_weather_condition(record.weather_condition),
                record.satellite_count / 20.0,  # 正規化衛星數量
                self._encode_time_of_day(record.prediction_timestamp),
                record.delta_t_used / 30.0,  # 正規化 delta_t
                record.context_factors.get("signal_strength", -80.0) / -100.0  # 正規化信號強度
            ]
            
            features.append(feature_vector)
            labels.append(record.accuracy_score)
        
        return features, labels
    
    def _encode_weather_condition(self, weather_condition: str) -> float:
        """編碼天氣條件"""
        weather_map = {
            "clear": 1.0,
            "partly_cloudy": 0.8,
            "cloudy": 0.6,
            "light_rain": 0.4,
            "moderate_rain": 0.2,
            "heavy_rain": 0.1,
            "thunderstorm": 0.0
        }
        return weather_map.get(weather_condition, 0.5)
    
    def _encode_time_of_day(self, timestamp: float) -> float:
        """編碼時間因子"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        # 簡化的時間編碼 (假設白天準確率更高)
        if 6 <= hour <= 18:
            return 1.0  # 白天
        else:
            return 0.5  # 夜間
    
    async def _analyze_feature_importance(self, features: List[List[float]], labels: List[float]):
        """分析特徵重要性"""
        if not features or not labels:
            return
        
        features_array = np.array(features)
        labels_array = np.array(labels)
        
        # 簡化的相關性分析
        feature_names = ["weather", "satellite_count", "time_of_day", "delta_t", "signal_strength"]
        correlations = {}
        
        for i, name in enumerate(feature_names):
            if features_array.shape[1] > i:
                correlation = np.corrcoef(features_array[:, i], labels_array)[0, 1]
                if not np.isnan(correlation):
                    correlations[name] = abs(correlation)
        
        # 更新特徵重要性
        total_correlation = sum(correlations.values())
        if total_correlation > 0:
            for name, corr in correlations.items():
                weight_key = f"{name}_factor"
                if weight_key in self.ml_model_weights:
                    self.ml_model_weights[weight_key] = corr / total_correlation
        
        logger.debug(f"特徵重要性分析: {correlations}")
    
    async def _update_ml_weights(self, features: List[List[float]], labels: List[float]):
        """更新機器學習權重"""
        # 簡化的權重更新 (基於性能反饋)
        current_performance = self.current_accuracy
        
        if self.performance_baseline is None:
            self.performance_baseline = current_performance
        else:
            performance_change = current_performance - self.performance_baseline
            
            # 如果性能提升，保持當前權重；如果下降，調整權重
            if performance_change < -0.05:  # 性能下降超過5%
                # 輕微調整權重
                for key in self.ml_model_weights:
                    self.ml_model_weights[key] *= 0.95  # 減少權重影響
                    
                logger.info("檢測到性能下降，調整 ML 權重")
            
            self.performance_baseline = current_performance
    
    async def _record_optimization_state(self):
        """記錄優化狀態"""
        state = {
            "timestamp": time.time(),
            "current_accuracy": self.current_accuracy,
            "current_delta_t": self.current_delta_t,
            "total_predictions": len(self.accuracy_records),
            "ml_weights": self.ml_model_weights.copy(),
            "accuracy_level": self._classify_accuracy_level(self.current_accuracy)
        }
        
        self.optimization_history.append(state)
        
        # 保持歷史記錄在合理範圍內
        if len(self.optimization_history) > 200:
            self.optimization_history = self.optimization_history[-100:]
    
    def _classify_accuracy_level(self, accuracy: float) -> str:
        """分類準確率等級"""
        if accuracy >= 0.95:
            return PredictionAccuracyLevel.EXCELLENT.value
        elif accuracy >= 0.90:
            return PredictionAccuracyLevel.GOOD.value
        elif accuracy >= 0.80:
            return PredictionAccuracyLevel.AVERAGE.value
        elif accuracy >= 0.70:
            return PredictionAccuracyLevel.POOR.value
        else:
            return PredictionAccuracyLevel.CRITICAL.value
    
    def get_current_metrics(self) -> AccuracyMetrics:
        """獲取當前準確率指標"""
        if not self.accuracy_history:
            return AccuracyMetrics(
                current_accuracy=0.0,
                rolling_accuracy=0.0,
                accuracy_trend="stable",
                predictions_evaluated=0,
                target_achievement=False,
                confidence_interval=(0.0, 0.0),
                accuracy_by_context={}
            )
        
        # 計算滾動準確率
        recent_window = min(20, len(self.accuracy_history))
        rolling_accuracy = sum(self.accuracy_history[-recent_window:]) / recent_window
        
        # 計算趨勢
        trend = self._calculate_accuracy_trend()
        
        # 計算置信區間
        confidence_interval = self._calculate_confidence_interval()
        
        # 按上下文分析準確率
        accuracy_by_context = self._analyze_accuracy_by_context()
        
        return AccuracyMetrics(
            current_accuracy=self.current_accuracy,
            rolling_accuracy=rolling_accuracy,
            accuracy_trend=trend,
            predictions_evaluated=len(self.accuracy_records),
            target_achievement=self.current_accuracy >= self.config.target_accuracy,
            confidence_interval=confidence_interval,
            accuracy_by_context=accuracy_by_context
        )
    
    def _calculate_accuracy_trend(self) -> str:
        """計算準確率趨勢"""
        if len(self.accuracy_history) < 10:
            return "stable"
        
        # 比較最近的準確率與之前的準確率
        recent_avg = sum(self.accuracy_history[-5:]) / 5
        previous_avg = sum(self.accuracy_history[-10:-5]) / 5
        
        diff = recent_avg - previous_avg
        
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"
    
    def _calculate_confidence_interval(self) -> Tuple[float, float]:
        """計算置信區間"""
        if len(self.accuracy_history) < 5:
            return (0.0, 1.0)
        
        recent_scores = self.accuracy_history[-20:]
        mean_accuracy = sum(recent_scores) / len(recent_scores)
        
        # 簡化的置信區間計算
        variance = sum((x - mean_accuracy) ** 2 for x in recent_scores) / len(recent_scores)
        std_dev = math.sqrt(variance)
        
        # 95% 置信區間
        margin = 1.96 * std_dev / math.sqrt(len(recent_scores))
        
        return (
            max(0.0, mean_accuracy - margin),
            min(1.0, mean_accuracy + margin)
        )
    
    def _analyze_accuracy_by_context(self) -> Dict[str, float]:
        """按上下文分析準確率"""
        context_accuracies = {}
        
        # 按天氣條件分析
        weather_groups = {}
        for record in self.accuracy_records[-100:]:
            weather = record.weather_condition
            if weather not in weather_groups:
                weather_groups[weather] = []
            weather_groups[weather].append(record.accuracy_score)
        
        for weather, scores in weather_groups.items():
            if len(scores) >= 3:  # 至少需要3個樣本
                context_accuracies[f"weather_{weather}"] = sum(scores) / len(scores)
        
        # 按衛星數量分析
        satellite_groups = {"low": [], "medium": [], "high": []}
        for record in self.accuracy_records[-100:]:
            count = record.satellite_count
            if count <= 5:
                satellite_groups["low"].append(record.accuracy_score)
            elif count <= 10:
                satellite_groups["medium"].append(record.accuracy_score)
            else:
                satellite_groups["high"].append(record.accuracy_score)
        
        for level, scores in satellite_groups.items():
            if len(scores) >= 3:
                context_accuracies[f"satellites_{level}"] = sum(scores) / len(scores)
        
        return context_accuracies
    
    def get_optimization_recommendations(self) -> List[str]:
        """獲取優化建議"""
        recommendations = []
        
        if self.current_accuracy < self.config.min_accuracy_threshold:
            recommendations.append("準確率過低，建議縮短預測間隔 (delta_t)")
            recommendations.append("檢查天氣整合模組是否正常工作")
            recommendations.append("增加衛星候選者數量")
        
        if self.current_accuracy < self.config.target_accuracy:
            recommendations.append("啟用機器學習增強模組")
            recommendations.append("調整約束式選擇策略參數")
        
        # 基於趨勢的建議
        trend = self._calculate_accuracy_trend()
        if trend == "declining":
            recommendations.append("檢測到準確率下降趨勢，建議檢查系統參數")
        elif trend == "improving":
            recommendations.append("準確率正在改善，可考慮逐步優化其他參數")
        
        # 基於上下文分析的建議
        context_accuracies = self._analyze_accuracy_by_context()
        for context, accuracy in context_accuracies.items():
            if accuracy < 0.8:
                recommendations.append(f"在 {context} 條件下準確率較低，需要特別優化")
        
        return recommendations if recommendations else ["系統運行正常，無需特別調整"]
    
    def get_detailed_statistics(self) -> Dict[str, Any]:
        """獲取詳細統計信息"""
        metrics = self.get_current_metrics()
        
        return {
            "accuracy_metrics": {
                "current_accuracy": metrics.current_accuracy,
                "rolling_accuracy": metrics.rolling_accuracy,
                "accuracy_trend": metrics.accuracy_trend,
                "target_achievement": metrics.target_achievement,
                "accuracy_level": self._classify_accuracy_level(metrics.current_accuracy),
                "confidence_interval": metrics.confidence_interval
            },
            "optimization_status": {
                "current_delta_t": self.current_delta_t,
                "adaptive_adjustment_enabled": self.config.adaptive_adjustment_enabled,
                "ml_enhancement_enabled": self.config.ml_enhancement_enabled,
                "target_accuracy": self.config.target_accuracy,
                "optimization_cycles": len(self.optimization_history)
            },
            "performance_analysis": {
                "predictions_evaluated": metrics.predictions_evaluated,
                "accuracy_by_context": metrics.accuracy_by_context,
                "ml_model_weights": self.ml_model_weights.copy(),
                "performance_baseline": self.performance_baseline
            },
            "recommendations": self.get_optimization_recommendations(),
            "last_optimization": self.optimization_history[-1] if self.optimization_history else None
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新優化配置"""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"優化配置已更新: {key} = {value}")
    
    def get_recommended_delta_t(self) -> int:
        """獲取建議的 delta_t 值"""
        return self.current_delta_t