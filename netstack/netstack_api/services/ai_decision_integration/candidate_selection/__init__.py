"""
候選篩選層 - 衛星候選篩選和評分系統

此模組實現了智能的候選衛星篩選和評分機制，包括：
- 多策略候選篩選
- 智能評分引擎  
- 動態策略切換
- 可見性計算

主要組件：
- CandidateSelector: 主要篩選器
- SelectionStrategy: 篩選策略基類
- ScoringEngine: 評分引擎
- 各種具體策略實現
"""

from .selector import CandidateSelector
from .scoring import ScoringEngine

__all__ = [
    "CandidateSelector",
    "ScoringEngine",
]

__version__ = "1.0.0"
__author__ = "NTN Stack Team"