"""
🎭 換手算法生態系統

多算法研究平台，支持傳統算法與強化學習算法的統一管理和協調。

核心組件：
- HandoverOrchestrator: 算法協調器
- AlgorithmRegistry: 算法註冊中心  
- EnvironmentManager: 環境管理器
- TrainingPipeline: RL 訓練管線
- InferencePipeline: 推理管線
- PerformanceAnalysisEngine: 性能分析引擎
"""

from .interfaces import (
    HandoverAlgorithm,
    RLHandoverAlgorithm,
    HandoverContext,
    HandoverDecision,
    AlgorithmInfo
)

from .registry import AlgorithmRegistry
from .orchestrator import HandoverOrchestrator
from .environment_manager import EnvironmentManager

# 導入訓練管線
try:
    from .training_pipeline import RLTrainingPipeline
    TRAINING_PIPELINE_AVAILABLE = True
except ImportError:
    TRAINING_PIPELINE_AVAILABLE = False

# 導入分析引擎
try:
    from .analysis_engine import PerformanceAnalysisEngine
    ANALYSIS_ENGINE_AVAILABLE = True
except ImportError:
    ANALYSIS_ENGINE_AVAILABLE = False

# 導入生態系統管理器
try:
    from .ecosystem_manager import AlgorithmEcosystemManager
    ECOSYSTEM_MANAGER_AVAILABLE = True
except ImportError:
    ECOSYSTEM_MANAGER_AVAILABLE = False

# 導入適配器
try:
    from .adapters.traditional_adapters import (
        InfocomAlgorithmAdapter,
        SimpleThresholdAlgorithmAdapter,
        RandomAlgorithmAdapter
    )
    TRADITIONAL_ADAPTERS_AVAILABLE = True
except ImportError:
    TRADITIONAL_ADAPTERS_AVAILABLE = False

# 導入 RL 算法
try:
    from .rl_algorithms import BaseRLHandoverAlgorithm
    RL_BASE_AVAILABLE = True
except ImportError:
    RL_BASE_AVAILABLE = False

try:
    from .rl_algorithms import DQNHandoverAgent, PPOHandoverAgent, SACHandoverAgent
    RL_ALGORITHMS_AVAILABLE = True
except ImportError:
    RL_ALGORITHMS_AVAILABLE = False

__all__ = [
    "HandoverAlgorithm",
    "RLHandoverAlgorithm", 
    "HandoverContext",
    "HandoverDecision",
    "AlgorithmInfo",
    "AlgorithmRegistry",
    "HandoverOrchestrator",
    "EnvironmentManager"
]

# 動態添加訓練管線
if TRAINING_PIPELINE_AVAILABLE:
    __all__.append("RLTrainingPipeline")

# 動態添加分析引擎
if ANALYSIS_ENGINE_AVAILABLE:
    __all__.append("PerformanceAnalysisEngine")

# 動態添加生態系統管理器
if ECOSYSTEM_MANAGER_AVAILABLE:
    __all__.append("AlgorithmEcosystemManager")

# 動態添加可用的組件
if TRADITIONAL_ADAPTERS_AVAILABLE:
    __all__.extend([
        "InfocomAlgorithmAdapter",
        "SimpleThresholdAlgorithmAdapter", 
        "RandomAlgorithmAdapter"
    ])

if RL_BASE_AVAILABLE:
    __all__.append("BaseRLHandoverAlgorithm")

if RL_ALGORITHMS_AVAILABLE:
    __all__.extend([
        "DQNHandoverAgent",
        "PPOHandoverAgent",
        "SACHandoverAgent"
    ])

__version__ = "1.0.0"