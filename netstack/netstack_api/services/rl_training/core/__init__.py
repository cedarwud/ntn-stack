"""
RL System Core
==============

此核心模組協調以下部分：
- 演算法註冊與實例化
- 訓練生命週期管理
- 狀態追蹤
"""

from .algorithm_factory import get_algorithm, algorithm_plugins, AlgorithmFactory

__all__ = ["get_algorithm", "algorithm_plugins", "AlgorithmFactory"]
