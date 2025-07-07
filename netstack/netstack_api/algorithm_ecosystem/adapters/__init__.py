"""
🔧 算法適配器模組

將現有算法包裝為統一接口的適配器。
"""

from .traditional_adapters import (
    InfocomAlgorithmAdapter,
    SimpleThresholdAlgorithmAdapter,
    RandomAlgorithmAdapter
)

__all__ = [
    "InfocomAlgorithmAdapter",
    "SimpleThresholdAlgorithmAdapter", 
    "RandomAlgorithmAdapter"
]