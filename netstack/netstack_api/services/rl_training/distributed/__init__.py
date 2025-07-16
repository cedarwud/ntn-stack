"""
分佈式訓練系統模組

Phase 4 核心組件 - 實現多節點分佈式 RL 訓練架構：
- 多節點協調器 (NodeCoordinator) 
- 負載均衡器 (LoadBalancer)
- 故障恢復機制 (FaultRecovery)
- 分佈式訓練管理器 (DistributedTrainingManager)

Authors: Phase 4 Development Team
Created: July 2025
"""

from .node_coordinator import (
    NodeCoordinator, 
    NodeInfo, 
    NodeStatus, 
    NodeType, 
    TrainingTask
)
from .load_balancer import (
    LoadBalancer, 
    LoadBalancingStrategy, 
    LoadMetrics,
    NodePerformanceHistory
)
from .fault_recovery import (
    FaultRecovery, 
    FailureEvent, 
    FailureType, 
    RecoveryStrategy,
    SystemSnapshot,
    RecoveryPlan
)
from .distributed_training_manager import (
    DistributedTrainingManager, 
    TrainingConfiguration, 
    TrainingSession,
    TrainingPhase,
    TrainingMode,
    TrainingMetrics
)

__all__ = [
    # 節點協調
    "NodeCoordinator",
    "NodeInfo", 
    "NodeStatus",
    "NodeType",
    "TrainingTask",
    
    # 負載均衡
    "LoadBalancer",
    "LoadBalancingStrategy",
    "LoadMetrics",
    "NodePerformanceHistory",
    
    # 故障恢復
    "FaultRecovery",
    "FailureEvent",
    "FailureType",
    "RecoveryStrategy",
    "SystemSnapshot",
    "RecoveryPlan",
    
    # 分佈式訓練管理
    "DistributedTrainingManager",
    "TrainingConfiguration",
    "TrainingSession",
    "TrainingPhase",
    "TrainingMode",
    "TrainingMetrics"
]

__version__ = "1.0.0"
