"""
候選篩選策略基類

定義所有篩選策略的通用接口和基礎功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

from ...interfaces.candidate_selector import Candidate, ProcessedEvent

logger = logging.getLogger(__name__)


@dataclass
class StrategyParameters:
    """策略參數配置"""
    min_threshold: float = 0.0
    max_threshold: float = 1.0
    weight: float = 1.0
    enabled: bool = True
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


@dataclass 
class StrategyResult:
    """策略篩選結果"""
    filtered_candidates: List[Candidate]
    scores: Dict[str, float]  # satellite_id -> score
    metadata: Dict[str, Any]
    strategy_name: str
    execution_time_ms: float


class SelectionStrategy(ABC):
    """
    候選篩選策略抽象基類
    
    所有具體策略都需要繼承此類並實現核心方法
    """
    
    def __init__(self, name: str, description: str, default_params: StrategyParameters = None):
        self.name = name
        self.description = description
        self.default_params = default_params or StrategyParameters()
        self.is_enabled = True
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def evaluate_candidate(self, candidate: Candidate, 
                          event: ProcessedEvent,
                          params: StrategyParameters = None) -> float:
        """
        評估單個候選衛星
        
        Args:
            candidate: 候選衛星
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            float: 評分 (0.0-1.0)
        """
        pass
    
    @abstractmethod
    def filter_candidates(self, candidates: List[Candidate],
                         event: ProcessedEvent, 
                         params: StrategyParameters = None) -> StrategyResult:
        """
        篩選候選衛星列表
        
        Args:
            candidates: 候選衛星列表
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            StrategyResult: 篩選結果
        """
        pass
    
    async def select_candidates(self, event: ProcessedEvent, 
                               satellite_pool: List[Candidate]) -> List[Candidate]:
        """
        從衛星池中選擇候選衛星
        
        Args:
            event: 處理後的事件
            satellite_pool: 衛星池
            
        Returns:
            List[Candidate]: 選擇的候選衛星
        """
        # 默認實現：使用 filter_candidates 方法
        result = self.filter_candidates(satellite_pool, event)
        return result.filtered_candidates
    
    async def apply_advanced_filtering(self, candidates: List[Candidate],
                                     parameters: Dict[str, Any]) -> List[Candidate]:
        """
        應用高級篩選
        
        Args:
            candidates: 候選衛星列表
            parameters: 篩選參數
            
        Returns:
            List[Candidate]: 篩選後的候選列表
        """
        # 轉換參數格式
        strategy_params = StrategyParameters(
            min_threshold=parameters.get("min_threshold", self.default_params.min_threshold),
            max_threshold=parameters.get("max_threshold", self.default_params.max_threshold),
            weight=parameters.get("weight", self.default_params.weight),
            enabled=parameters.get("enabled", True),
            custom_params=parameters.get("custom_params", {})
        )
        
        # 創建虛擬事件
        dummy_event = ProcessedEvent(
            event_type="advanced_filter",
            timestamp=0.0,
            confidence=1.0,
            ue_id="dummy",
            source_cell="dummy",
            target_cells=[],
            event_data=parameters,
            trigger_conditions={},
            measurement_values={}
        )
        
        # 執行篩選
        result = self.filter_candidates(candidates, dummy_event, strategy_params)
        return result.filtered_candidates
    
    def validate_parameters(self, params: StrategyParameters) -> bool:
        """
        驗證策略參數的有效性
        
        Args:
            params: 策略參數
            
        Returns:
            bool: 參數是否有效
        """
        try:
            if params.min_threshold < 0 or params.max_threshold > 1:
                return False
            if params.min_threshold >= params.max_threshold:
                return False
            if params.weight < 0:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Parameter validation failed: {e}")
            return False
    
    def get_effective_parameters(self, params: Optional[StrategyParameters] = None) -> StrategyParameters:
        """
        獲取有效的策略參數（合併默認參數和傳入參數）
        
        Args:
            params: 傳入的參數
            
        Returns:
            StrategyParameters: 有效參數
        """
        if params is None:
            return self.default_params
        
        # 合併參數
        effective_params = StrategyParameters(
            min_threshold=params.min_threshold if params.min_threshold is not None else self.default_params.min_threshold,
            max_threshold=params.max_threshold if params.max_threshold is not None else self.default_params.max_threshold,
            weight=params.weight if params.weight is not None else self.default_params.weight,
            enabled=params.enabled if params.enabled is not None else self.default_params.enabled,
            custom_params={**self.default_params.custom_params, **(params.custom_params or {})}
        )
        
        return effective_params
    
    def normalize_score(self, raw_score: float, min_val: float, max_val: float) -> float:
        """
        正規化分數到 0.0-1.0 範圍
        
        Args:
            raw_score: 原始分數
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            float: 正規化後的分數
        """
        if max_val <= min_val:
            return 0.0
        
        normalized = (raw_score - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def apply_threshold(self, candidates: List[Candidate], 
                       scores: Dict[str, float],
                       params: StrategyParameters) -> List[Candidate]:
        """
        根據閾值篩選候選者
        
        Args:
            candidates: 候選列表
            scores: 分數字典
            params: 策略參數
            
        Returns:
            List[Candidate]: 篩選後的候選列表
        """
        filtered = []
        for candidate in candidates:
            score = scores.get(candidate.satellite_id, 0.0)
            if params.min_threshold <= score <= params.max_threshold:
                filtered.append(candidate)
        
        return filtered
    
    def enable(self):
        """啟用策略"""
        self.is_enabled = True
        self.logger.info(f"Strategy {self.name} enabled")
    
    def disable(self):
        """禁用策略"""
        self.is_enabled = False
        self.logger.info(f"Strategy {self.name} disabled")
    
    def get_info(self) -> Dict[str, Any]:
        """
        獲取策略信息
        
        Returns:
            Dict[str, Any]: 策略信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.is_enabled,
            "default_params": {
                "min_threshold": self.default_params.min_threshold,
                "max_threshold": self.default_params.max_threshold,
                "weight": self.default_params.weight,
                "custom_params": self.default_params.custom_params
            }
        }