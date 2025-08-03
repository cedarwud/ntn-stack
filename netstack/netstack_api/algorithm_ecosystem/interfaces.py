"""
🔌 統一算法接口定義

定義換手算法生態系統的核心接口和數據結構。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import numpy as np

# Gymnasium dependency removed
GYMNASIUM_AVAILABLE = False


class AlgorithmType(Enum):
    """算法類型枚舉"""
    TRADITIONAL = "traditional"
    # REINFORCEMENT_LEARNING = "rl"  # Removed
    HYBRID = "hybrid"
    HEURISTIC = "heuristic"


class HandoverDecisionType(Enum):
    """換手決策類型"""
    NO_HANDOVER = 0
    IMMEDIATE_HANDOVER = 1
    PREPARE_HANDOVER = 2


@dataclass
class GeoCoordinate:
    """地理坐標"""
    latitude: float
    longitude: float
    altitude: float = 0.0


@dataclass
class SignalMetrics:
    """信號質量指標"""
    rsrp: float  # 參考信號接收功率
    rsrq: float  # 參考信號接收質量
    sinr: float  # 信噪干擾比
    throughput: float = 0.0
    latency: float = 0.0


@dataclass
class SatelliteInfo:
    """衛星信息"""
    satellite_id: str
    position: GeoCoordinate
    velocity: Optional[GeoCoordinate] = None
    signal_metrics: Optional[SignalMetrics] = None
    load_factor: float = 0.0
    coverage_area: Optional[List[GeoCoordinate]] = None


@dataclass
class HandoverContext:
    """統一的換手決策上下文"""
    ue_id: str
    current_satellite: Optional[str]
    ue_location: GeoCoordinate
    ue_velocity: Optional[GeoCoordinate]
    current_signal_metrics: Optional[SignalMetrics]
    candidate_satellites: List[SatelliteInfo]
    network_state: Dict[str, Any]
    timestamp: datetime
    scenario_info: Optional[Dict[str, Any]] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    traffic_load: Optional[Dict[str, Any]] = None


@dataclass
class HandoverDecision:
    """統一的換手決策結果"""
    target_satellite: Optional[str]
    handover_decision: HandoverDecisionType
    confidence: float  # 決策信心度 [0.0, 1.0]
    timing: Optional[datetime]  # 建議執行時間
    decision_reason: str
    algorithm_name: str
    decision_time: float  # 決策耗時 (毫秒)
    metadata: Dict[str, Any]
    priority: int = 1  # 決策優先級


@dataclass
class AlgorithmInfo:
    """算法元數據"""
    name: str
    version: str
    algorithm_type: AlgorithmType
    description: str
    parameters: Dict[str, Any]
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    performance_metrics: Optional[Dict[str, float]] = None
    supported_scenarios: Optional[List[str]] = None


class HandoverAlgorithm(ABC):
    """換手算法基類
    
    所有換手算法必須繼承此類並實現其抽象方法。
    提供統一的算法接口和基本功能。
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """初始化算法
        
        Args:
            name: 算法名稱
            config: 算法配置參數
        """
        self.name = name
        self.config = config or {}
        self._is_initialized = False
        self._statistics = {
            'total_decisions': 0,
            'total_decision_time': 0.0,
            'average_decision_time': 0.0,
            'handover_decisions': 0,
            'no_handover_decisions': 0,
            'preparation_decisions': 0
        }
    
    @abstractmethod
    async def predict_handover(self, context: HandoverContext) -> HandoverDecision:
        """執行換手預測決策
        
        Args:
            context: 換手決策上下文
            
        Returns:
            HandoverDecision: 決策結果
        """
        pass
    
    @abstractmethod
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取算法信息
        
        Returns:
            AlgorithmInfo: 算法元數據
        """
        pass
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """算法初始化
        
        Args:
            config: 初始化配置
        """
        if config:
            self.config.update(config)
        await self._initialize_algorithm()
        self._is_initialized = True
    
    async def _initialize_algorithm(self) -> None:
        """算法特定初始化邏輯 - 子類可重寫"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取算法統計信息"""
        return self._statistics.copy()
    
    def reset_statistics(self) -> None:
        """重置統計信息"""
        for key in self._statistics:
            self._statistics[key] = 0 if isinstance(self._statistics[key], (int, float)) else 0.0
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新算法配置"""
        self.config.update(new_config)
    
    @property
    def is_initialized(self) -> bool:
        """檢查算法是否已初始化"""
        return self._is_initialized


# RLHandoverAlgorithm class removed - RL functionality deprecated