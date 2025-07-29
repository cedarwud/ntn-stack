"""
Performance Domain

This domain handles all performance-related functionality including:
- Algorithm performance measurement and comparison
- System resource monitoring and optimization
- Performance data aggregation and reporting
- Real-time metrics collection

Created as part of Phase 3 service layer refactoring.
"""

from .api.performance_api import router as performance_router
from .services.simworld_optimizer import SimWorldOptimizer
from .services.algorithm_calculator import AlgorithmCalculator
from .services.performance_aggregator import PerformanceAggregator

__all__ = [
    "performance_router",
    "SimWorldOptimizer", 
    "AlgorithmCalculator",
    "PerformanceAggregator"
]