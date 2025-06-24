"""
基準算法包

提供標準化的基準算法接口，用於與 RL 算法進行性能對比：
- IEEE INFOCOM 2024 算法
- 簡單閾值算法  
- 隨機基準算法
- 自定義算法接口
"""

from .base_algorithm import BaseAlgorithm, AlgorithmResult
from .infocom2024_algorithm import InfocomAlgorithm
from .simple_threshold_algorithm import SimpleThresholdAlgorithm
from .random_algorithm import RandomAlgorithm

__all__ = [
    'BaseAlgorithm',
    'AlgorithmResult', 
    'InfocomAlgorithm',
    'SimpleThresholdAlgorithm',
    'RandomAlgorithm'
]