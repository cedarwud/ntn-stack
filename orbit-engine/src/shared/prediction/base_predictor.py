"""
預測基類

提供所有預測功能的基礎類和共用接口
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging


@dataclass
class PredictionResult:
    """預測結果基類"""
    prediction_id: str
    predictor_name: str
    timestamp: datetime
    prediction_horizon: timedelta
    confidence_score: float
    model_version: str
    accuracy_estimation: Optional[float] = None


@dataclass
class TrainingResult:
    """訓練結果"""
    training_id: str
    model_version: str
    training_timestamp: datetime
    training_duration: timedelta
    training_accuracy: float
    validation_accuracy: float
    training_samples: int


@dataclass
class ValidationResult:
    """驗證結果"""
    validation_id: str
    validation_timestamp: datetime
    accuracy_score: float
    precision: float
    recall: float
    f1_score: float
    mse: Optional[float] = None  # for regression
    mae: Optional[float] = None  # for regression


@dataclass
class PredictionConfig:
    """預測配置基類"""
    predictor_name: str
    model_type: str = "statistical"  # statistical, ml, hybrid
    prediction_horizon: timedelta = field(default_factory=lambda: timedelta(hours=1))
    confidence_threshold: float = 0.7
    max_history_size: int = 1000
    retrain_interval: timedelta = field(default_factory=lambda: timedelta(days=1))


class BasePrediction(ABC):
    """預測基類"""

    def __init__(self, predictor_name: str, config: PredictionConfig):
        self.predictor_name = predictor_name
        self.config = config
        self.model = None
        self.training_history: List[TrainingResult] = []
        self.prediction_history: List[PredictionResult] = []
        self.logger = logging.getLogger(f"predictor.{predictor_name}")

        # 初始化模型
        self._initialize_model()

    @abstractmethod
    def predict(self, input_data: Any) -> PredictionResult:
        """執行預測"""
        pass

    @abstractmethod
    def train(self, training_data: Any) -> TrainingResult:
        """訓練模型"""
        pass

    @abstractmethod
    def _initialize_model(self):
        """初始化模型"""
        pass

    def validate_prediction(self, actual_data: Any, predicted_data: Any) -> ValidationResult:
        """驗證預測準確性"""
        # 基礎實現，子類可重寫
        validation_id = f"val_{self.predictor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # 簡化的準確性計算
            if hasattr(actual_data, '__len__') and hasattr(predicted_data, '__len__'):
                if len(actual_data) == len(predicted_data):
                    # 計算絕對誤差
                    errors = [abs(a - p) for a, p in zip(actual_data, predicted_data)]
                    mae = sum(errors) / len(errors) if errors else 0.0
                    mse = sum(e ** 2 for e in errors) / len(errors) if errors else 0.0

                    # 簡化的準確性分數
                    max_error = max(errors) if errors else 0.0
                    accuracy_score = max(0.0, 1.0 - (max_error / 100.0))  # 假設100為最大可能誤差

                    return ValidationResult(
                        validation_id=validation_id,
                        validation_timestamp=datetime.now(),
                        accuracy_score=accuracy_score,
                        precision=accuracy_score,  # 簡化
                        recall=accuracy_score,     # 簡化
                        f1_score=accuracy_score,   # 簡化
                        mse=mse,
                        mae=mae
                    )

            # 默認返回
            return ValidationResult(
                validation_id=validation_id,
                validation_timestamp=datetime.now(),
                accuracy_score=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            )

        except Exception as e:
            self.logger.error(f"預測驗證失敗: {e}")
            return ValidationResult(
                validation_id=validation_id,
                validation_timestamp=datetime.now(),
                accuracy_score=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            )

    def get_prediction_confidence(self, prediction: PredictionResult) -> float:
        """獲取預測信心度"""
        return prediction.confidence_score

    def add_prediction_result(self, result: PredictionResult):
        """添加預測結果到歷史記錄"""
        self.prediction_history.append(result)

        # 保持歷史記錄大小限制
        if len(self.prediction_history) > self.config.max_history_size:
            self.prediction_history = self.prediction_history[-self.config.max_history_size:]

    def get_recent_predictions(self, time_window: timedelta) -> List[PredictionResult]:
        """獲取最近的預測結果"""
        cutoff_time = datetime.now() - time_window
        return [p for p in self.prediction_history if p.timestamp >= cutoff_time]

    def should_retrain(self) -> bool:
        """判斷是否需要重新訓練"""
        if not self.training_history:
            return True

        last_training = max(self.training_history, key=lambda x: x.training_timestamp)
        time_since_training = datetime.now() - last_training.training_timestamp

        return time_since_training >= self.config.retrain_interval

    def get_model_performance_summary(self) -> Dict[str, Any]:
        """獲取模型性能摘要"""
        if not self.prediction_history:
            return {"no_predictions": True}

        recent_predictions = self.get_recent_predictions(timedelta(hours=24))
        confidence_scores = [p.confidence_score for p in recent_predictions]

        summary = {
            "predictor_name": self.predictor_name,
            "total_predictions": len(self.prediction_history),
            "recent_predictions_24h": len(recent_predictions),
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
            "max_confidence": max(confidence_scores) if confidence_scores else 0.0,
            "model_version": self.training_history[-1].model_version if self.training_history else "unknown",
            "last_training": self.training_history[-1].training_timestamp if self.training_history else None,
            "needs_retraining": self.should_retrain()
        }

        return summary

    def cleanup_old_history(self, retention_period: timedelta):
        """清理舊的歷史記錄"""
        cutoff_time = datetime.now() - retention_period

        # 清理預測歷史
        self.prediction_history = [
            p for p in self.prediction_history
            if p.timestamp >= cutoff_time
        ]

        # 清理訓練歷史
        self.training_history = [
            t for t in self.training_history
            if t.training_timestamp >= cutoff_time
        ]

        self.logger.info(f"清理 {self.predictor_name} 的舊歷史記錄，保留時間: {retention_period}")

    def export_model_info(self) -> Dict[str, Any]:
        """導出模型信息"""
        return {
            "predictor_name": self.predictor_name,
            "config": {
                "model_type": self.config.model_type,
                "prediction_horizon": self.config.prediction_horizon.total_seconds(),
                "confidence_threshold": self.config.confidence_threshold
            },
            "performance_summary": self.get_model_performance_summary(),
            "training_history_count": len(self.training_history),
            "prediction_history_count": len(self.prediction_history)
        }