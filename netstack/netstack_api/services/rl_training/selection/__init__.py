"""
Phase 3: 智能算法選擇模組

此模組實現基於環境特徵的智能算法選擇，提供自動化的算法匹配和性能預測，
幫助用戶在不同場景下選擇最適合的強化學習算法。

核心功能：
- 環境特徵分析
- 算法性能預測
- 智能匹配決策
- 動態算法切換

Created for Phase 3: Algorithm Integration Optimization
"""

from .environment_analyzer import EnvironmentAnalyzer, EnvironmentFeatures, AnalysisResult
from .algorithm_matcher import AlgorithmMatcher, MatchingStrategy, MatchingResult
from .performance_predictor import PerformancePredictor, PredictionModel, PredictionResult
from .intelligent_selector_complete import IntelligentSelector, SelectionConfig, SelectionResult

__all__ = [
    "EnvironmentAnalyzer",
    "EnvironmentFeatures",
    "AnalysisResult",
    "AlgorithmMatcher",
    "MatchingStrategy",
    "MatchingResult",
    "PerformancePredictor",
    "PredictionModel",
    "PredictionResult",
    "IntelligentSelector",
    "SelectionConfig",
    "SelectionResult"
]
