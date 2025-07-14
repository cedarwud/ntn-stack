"""
Phase 2.3: RL 算法實戰應用整合模組

提供統一的 RL 算法與真實環境整合服務：
- 算法適配器和接口統一
- 真實環境與算法的橋接
- 決策過程記錄和分析
- Algorithm Explainability 引擎
- 多算法性能對比
- 實時決策狀態推送
"""

try:
    from .rl_algorithm_integrator import RLAlgorithmIntegrator

    RL_INTEGRATOR_AVAILABLE = True
except ImportError:
    RL_INTEGRATOR_AVAILABLE = False
    RLAlgorithmIntegrator = None

try:
    from .real_environment_bridge import RealEnvironmentBridge

    ENV_BRIDGE_AVAILABLE = True
except ImportError:
    ENV_BRIDGE_AVAILABLE = False
    RealEnvironmentBridge = None

try:
    from .decision_analytics_engine import DecisionAnalyticsEngine

    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    DecisionAnalyticsEngine = None

try:
    from .multi_algorithm_comparator import MultiAlgorithmComparator

    COMPARATOR_AVAILABLE = True
except ImportError:
    COMPARATOR_AVAILABLE = False
    MultiAlgorithmComparator = None

try:
    from .realtime_decision_service import RealtimeDecisionService

    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False
    RealtimeDecisionService = None

# 只導出成功加載的組件
__all__ = []
if RL_INTEGRATOR_AVAILABLE:
    __all__.append("RLAlgorithmIntegrator")
if ENV_BRIDGE_AVAILABLE:
    __all__.append("RealEnvironmentBridge")
if ANALYTICS_AVAILABLE:
    __all__.append("DecisionAnalyticsEngine")
if COMPARATOR_AVAILABLE:
    __all__.append("MultiAlgorithmComparator")
if REALTIME_AVAILABLE:
    __all__.append("RealtimeDecisionService")
