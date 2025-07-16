"""
協調器配置管理
包含協調器的各種配置選項和設置
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class OrchestratorMode(Enum):
    """協調器操作模式"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    HYBRID = "hybrid"
    LEARNING = "learning"


class DecisionStrategy(Enum):
    """決策策略"""
    PERFORMANCE_BASED = "performance_based"
    ROUND_ROBIN = "round_robin"
    WEIGHTED_AVERAGE = "weighted_average"
    ENSEMBLE_VOTING = "ensemble_voting"
    ADAPTIVE = "adaptive"


@dataclass
class OrchestratorConfig:
    """協調器配置類"""
    
    # 基本模式配置
    mode: OrchestratorMode = OrchestratorMode.AUTOMATIC
    decision_strategy: DecisionStrategy = DecisionStrategy.PERFORMANCE_BASED
    default_algorithm: str = "infocom2024"
    
    # 性能監控配置
    monitoring_enabled: bool = True
    monitoring_interval: int = 5  # 秒
    performance_window: int = 100  # 評估的歷史數據窗口
    
    # A/B 測試配置
    ab_testing_enabled: bool = False
    ab_test_duration: int = 3600  # 秒
    ab_test_traffic_split: float = 0.5  # 流量分割比例
    
    # 集成投票配置
    ensemble_enabled: bool = False
    ensemble_algorithms: List[str] = None
    ensemble_weights: Dict[str, float] = None
    
    # 自適應學習配置
    learning_enabled: bool = False
    learning_rate: float = 0.01
    exploration_rate: float = 0.1
    
    # 故障切換配置
    failover_enabled: bool = True
    failover_threshold: float = 0.3  # 性能下降閾值
    failover_algorithm: str = "simple_threshold"
    
    # 日誌和監控配置
    logging_level: str = "INFO"
    metrics_collection_enabled: bool = True
    detailed_logging_enabled: bool = False
    
    def __post_init__(self):
        """初始化後處理"""
        if self.ensemble_algorithms is None:
            self.ensemble_algorithms = ["infocom2024", "simple_threshold"]
        
        if self.ensemble_weights is None:
            self.ensemble_weights = {
                "infocom2024": 0.6,
                "simple_threshold": 0.4
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "mode": self.mode.value if isinstance(self.mode, OrchestratorMode) else self.mode,
            "decision_strategy": self.decision_strategy.value if isinstance(self.decision_strategy, DecisionStrategy) else self.decision_strategy,
            "default_algorithm": self.default_algorithm,
            "monitoring_enabled": self.monitoring_enabled,
            "monitoring_interval": self.monitoring_interval,
            "performance_window": self.performance_window,
            "ab_testing_enabled": self.ab_testing_enabled,
            "ab_test_duration": self.ab_test_duration,
            "ab_test_traffic_split": self.ab_test_traffic_split,
            "ensemble_enabled": self.ensemble_enabled,
            "ensemble_algorithms": self.ensemble_algorithms,
            "ensemble_weights": self.ensemble_weights,
            "learning_enabled": self.learning_enabled,
            "learning_rate": self.learning_rate,
            "exploration_rate": self.exploration_rate,
            "failover_enabled": self.failover_enabled,
            "failover_threshold": self.failover_threshold,
            "failover_algorithm": self.failover_algorithm,
            "logging_level": self.logging_level,
            "metrics_collection_enabled": self.metrics_collection_enabled,
            "detailed_logging_enabled": self.detailed_logging_enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrchestratorConfig':
        """從字典創建配置實例"""
        # 處理枚舉類型
        if "mode" in data and isinstance(data["mode"], str):
            data["mode"] = OrchestratorMode(data["mode"])
        
        if "decision_strategy" in data and isinstance(data["decision_strategy"], str):
            data["decision_strategy"] = DecisionStrategy(data["decision_strategy"])
        
        return cls(**data)
    
    def validate(self) -> bool:
        """驗證配置有效性"""
        try:
            # 檢查基本參數
            if not isinstance(self.monitoring_interval, int) or self.monitoring_interval <= 0:
                return False
            
            if not isinstance(self.performance_window, int) or self.performance_window <= 0:
                return False
            
            # 檢查比例參數
            if not 0 <= self.ab_test_traffic_split <= 1:
                return False
            
            if not 0 <= self.learning_rate <= 1:
                return False
            
            if not 0 <= self.exploration_rate <= 1:
                return False
            
            if not 0 <= self.failover_threshold <= 1:
                return False
            
            # 檢查集成配置
            if self.ensemble_enabled:
                if not self.ensemble_algorithms or len(self.ensemble_algorithms) < 2:
                    return False
                
                if self.ensemble_weights:
                    weight_sum = sum(self.ensemble_weights.values())
                    if abs(weight_sum - 1.0) > 0.01:  # 允許小的浮點誤差
                        return False
            
            return True
            
        except Exception:
            return False
    
    def get_optimal_config_for_scenario(self, scenario: str) -> 'OrchestratorConfig':
        """為特定場景獲取最優配置"""
        config = OrchestratorConfig()
        
        if scenario == "urban":
            config.mode = OrchestratorMode.AUTOMATIC
            config.decision_strategy = DecisionStrategy.PERFORMANCE_BASED
            config.monitoring_interval = 3
            config.performance_window = 50
            config.failover_threshold = 0.4
            
        elif scenario == "rural":
            config.mode = OrchestratorMode.AUTOMATIC
            config.decision_strategy = DecisionStrategy.ADAPTIVE
            config.monitoring_interval = 5
            config.performance_window = 100
            config.failover_threshold = 0.3
            
        elif scenario == "maritime":
            config.mode = OrchestratorMode.HYBRID
            config.decision_strategy = DecisionStrategy.ENSEMBLE_VOTING
            config.ensemble_enabled = True
            config.monitoring_interval = 10
            config.performance_window = 200
            config.failover_threshold = 0.2
            
        elif scenario == "aerial":
            config.mode = OrchestratorMode.LEARNING
            config.decision_strategy = DecisionStrategy.ADAPTIVE
            config.learning_enabled = True
            config.learning_rate = 0.05
            config.monitoring_interval = 2
            config.performance_window = 30
            
        else:
            # 默認配置
            pass
        
        return config