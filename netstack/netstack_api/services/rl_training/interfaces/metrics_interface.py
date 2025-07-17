"""
🧠 統一指標計算接口
確保前後端指標計算的一致性和標準化
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    """指標類型枚舉"""
    SUCCESS_RATE = "success_rate"
    STABILITY = "stability"
    LEARNING_EFFICIENCY = "learning_efficiency"
    CONVERGENCE_SPEED = "convergence_speed"
    PERFORMANCE_TREND = "performance_trend"
    CONFIDENCE_SCORE = "confidence_score"


class TrendType(Enum):
    """趨勢類型枚舉"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    MIXED = "mixed"
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"


@dataclass
class MetricDefinition:
    """指標定義"""
    name: str
    description: str
    unit: str
    range_min: float
    range_max: float
    calculation_method: str
    confidence_threshold: float


@dataclass
class StandardizedMetrics:
    """標準化指標結構"""
    # 核心指標 (0.0 - 1.0)
    success_rate: float
    stability: float
    learning_efficiency: float
    confidence_score: float
    
    # 輔助指標
    average_reward: float
    convergence_episode: Optional[int]
    performance_trend: TrendType
    
    # 元數據
    calculation_timestamp: str
    data_points_count: int
    calculation_method: str
    
    def to_percentage_dict(self) -> Dict[str, Any]:
        """轉換為百分比格式的字典（前端使用）"""
        return {
            "success_rate": self.success_rate * 100,
            "stability": self.stability * 100,
            "learning_efficiency": self.learning_efficiency * 100,
            "confidence_score": self.confidence_score * 100,
            "average_reward": self.average_reward,
            "convergence_episode": self.convergence_episode,
            "performance_trend": self.performance_trend.value,
            "calculation_timestamp": self.calculation_timestamp,
            "data_points_count": self.data_points_count,
            "calculation_method": self.calculation_method
        }
    
    def to_decimal_dict(self) -> Dict[str, Any]:
        """轉換為小數格式的字典（後端使用）"""
        return {
            "success_rate": self.success_rate,
            "stability": self.stability,
            "learning_efficiency": self.learning_efficiency,
            "confidence_score": self.confidence_score,
            "average_reward": self.average_reward,
            "convergence_episode": self.convergence_episode,
            "performance_trend": self.performance_trend.value,
            "calculation_timestamp": self.calculation_timestamp,
            "data_points_count": self.data_points_count,
            "calculation_method": self.calculation_method
        }


class IMetricsCalculator(ABC):
    """指標計算器接口"""
    
    @abstractmethod
    async def calculate_metrics(
        self, 
        data: List[Dict[str, Any]], 
        algorithm: str,
        session_id: str
    ) -> StandardizedMetrics:
        """
        計算標準化指標
        
        Args:
            data: 訓練數據列表
            algorithm: 算法名稱
            session_id: 會話ID
            
        Returns:
            StandardizedMetrics: 標準化指標
        """
        pass
    
    @abstractmethod
    def get_metric_definition(self, metric_type: MetricType) -> MetricDefinition:
        """
        獲取指標定義
        
        Args:
            metric_type: 指標類型
            
        Returns:
            MetricDefinition: 指標定義
        """
        pass
    
    @abstractmethod
    def validate_metrics(self, metrics: StandardizedMetrics) -> bool:
        """
        驗證指標有效性
        
        Args:
            metrics: 指標數據
            
        Returns:
            bool: 是否有效
        """
        pass


class MetricsStandardizer:
    """指標標準化器"""
    
    # 標準指標定義
    METRIC_DEFINITIONS = {
        MetricType.SUCCESS_RATE: MetricDefinition(
            name="Success Rate",
            description="訓練成功率，基於獎勵閾值和明確成功標記計算",
            unit="percentage",
            range_min=0.0,
            range_max=1.0,
            calculation_method="weighted_average_of_boolean_reward_trend",
            confidence_threshold=0.3
        ),
        MetricType.STABILITY: MetricDefinition(
            name="Training Stability",
            description="訓練穩定性，基於獎勵變異係數和滑動窗口標準差",
            unit="percentage",
            range_min=0.0,
            range_max=1.0,
            calculation_method="inverse_coefficient_of_variation",
            confidence_threshold=0.3
        ),
        MetricType.LEARNING_EFFICIENCY: MetricDefinition(
            name="Learning Efficiency",
            description="學習效率，基於改善速度和收斂速度",
            unit="percentage",
            range_min=0.0,
            range_max=1.0,
            calculation_method="improvement_rate_and_convergence_speed",
            confidence_threshold=0.2
        ),
        MetricType.CONFIDENCE_SCORE: MetricDefinition(
            name="Confidence Score",
            description="指標可信度，基於數據量、質量和時間跨度",
            unit="percentage",
            range_min=0.0,
            range_max=1.0,
            calculation_method="data_volume_quality_timespan",
            confidence_threshold=0.1
        )
    }
    
    @classmethod
    def normalize_value(cls, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """標準化數值到指定範圍"""
        return max(min_val, min(max_val, value))
    
    @classmethod
    def convert_to_percentage(cls, decimal_value: float) -> float:
        """將小數轉換為百分比"""
        return decimal_value * 100
    
    @classmethod
    def convert_to_decimal(cls, percentage_value: float) -> float:
        """將百分比轉換為小數"""
        return percentage_value / 100
    
    @classmethod
    def validate_metric_range(cls, metric_type: MetricType, value: float) -> bool:
        """驗證指標值是否在有效範圍內"""
        definition = cls.METRIC_DEFINITIONS.get(metric_type)
        if not definition:
            return False
        return definition.range_min <= value <= definition.range_max
    
    @classmethod
    def get_confidence_level(cls, confidence_score: float) -> str:
        """獲取可信度等級"""
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.5:
            return "medium"
        elif confidence_score >= 0.3:
            return "low"
        else:
            return "very_low"
    
    @classmethod
    def format_for_frontend(cls, metrics: StandardizedMetrics) -> Dict[str, Any]:
        """格式化指標供前端使用"""
        formatted = metrics.to_percentage_dict()
        
        # 添加額外的前端友好字段
        formatted.update({
            "confidence_level": cls.get_confidence_level(metrics.confidence_score),
            "trend_emoji": cls._get_trend_emoji(metrics.performance_trend),
            "confidence_emoji": cls._get_confidence_emoji(metrics.confidence_score),
            "is_reliable": metrics.confidence_score >= 0.3,
            "display_precision": 1  # 小數點後位數
        })
        
        return formatted
    
    @classmethod
    def format_for_backend(cls, metrics: StandardizedMetrics) -> Dict[str, Any]:
        """格式化指標供後端使用"""
        formatted = metrics.to_decimal_dict()
        
        # 添加後端分析字段
        formatted.update({
            "validation_passed": cls._validate_all_metrics(metrics),
            "quality_score": cls._calculate_quality_score(metrics),
            "reliability_flag": metrics.confidence_score >= 0.3
        })
        
        return formatted
    
    @classmethod
    def _get_trend_emoji(cls, trend: TrendType) -> str:
        """獲取趨勢表情符號"""
        emoji_map = {
            TrendType.IMPROVING: "📈",
            TrendType.STABLE: "➡️",
            TrendType.DECLINING: "📉",
            TrendType.MIXED: "🔄",
            TrendType.INSUFFICIENT_DATA: "❓",
            TrendType.ERROR: "❌"
        }
        return emoji_map.get(trend, "❓")
    
    @classmethod
    def _get_confidence_emoji(cls, confidence: float) -> str:
        """獲取可信度表情符號"""
        if confidence >= 0.7:
            return "🟢"
        elif confidence >= 0.4:
            return "🟡"
        else:
            return "🔴"
    
    @classmethod
    def _validate_all_metrics(cls, metrics: StandardizedMetrics) -> bool:
        """驗證所有指標"""
        validations = [
            cls.validate_metric_range(MetricType.SUCCESS_RATE, metrics.success_rate),
            cls.validate_metric_range(MetricType.STABILITY, metrics.stability),
            cls.validate_metric_range(MetricType.LEARNING_EFFICIENCY, metrics.learning_efficiency),
            cls.validate_metric_range(MetricType.CONFIDENCE_SCORE, metrics.confidence_score)
        ]
        return all(validations)
    
    @classmethod
    def _calculate_quality_score(cls, metrics: StandardizedMetrics) -> float:
        """計算整體質量分數"""
        # 基於可信度和數據點數量
        data_score = min(1.0, metrics.data_points_count / 50.0)
        confidence_score = metrics.confidence_score
        
        return (data_score * 0.4 + confidence_score * 0.6)


# 全局標準化器實例
metrics_standardizer = MetricsStandardizer()


def get_metrics_standardizer() -> MetricsStandardizer:
    """獲取指標標準化器實例"""
    return metrics_standardizer
