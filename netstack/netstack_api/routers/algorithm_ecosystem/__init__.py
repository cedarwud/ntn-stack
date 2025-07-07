"""
重構後的算法生態系統 API 路由器包
按功能分離：schemas(模型)、dependencies(依賴注入)、endpoints(端點實現)、router(路由註冊)
"""

from .router import router
from .schemas import *
from .dependencies import (
    get_algorithm_registry,
    get_environment_manager,
    get_handover_orchestrator,
    LifecycleManager
)
from .endpoints import AlgorithmEcosystemEndpoints

__all__ = [
    "router",
    "get_algorithm_registry",
    "get_environment_manager", 
    "get_handover_orchestrator",
    "LifecycleManager",
    "AlgorithmEcosystemEndpoints"
]