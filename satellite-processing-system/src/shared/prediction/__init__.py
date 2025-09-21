"""
共享預測模組

統一所有階段的預測功能，包括：
- 基礎預測類
- 信號預測
- 軌跡預測
- 覆蓋預測
"""

from .base_predictor import BasePrediction, PredictionResult, PredictionConfig, TrainingResult, ValidationResult
from .signal_predictor import SignalPredictor, SignalQualityPrediction
from .trajectory_predictor import TrajectoryPredictor, TrajectoryPrediction

__all__ = [
    'BasePrediction',
    'PredictionResult',
    'PredictionConfig',
    'TrainingResult',
    'ValidationResult',
    'SignalPredictor',
    'SignalQualityPrediction',
    'TrajectoryPredictor',
    'TrajectoryPrediction'
]