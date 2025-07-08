"""
事件處理器接口定義
==================

定義了3GPP事件處理的統一接口，支持 A4、D1、D2、T1 等測量事件。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
import time

@dataclass
class ProcessedEvent:
    """處理後的事件數據結構"""
    event_type: str                    # 事件類型 (A4/D1/D2/T1)
    event_data: Dict[str, Any]         # 原始事件數據
    timestamp: float                   # 事件時間戳
    confidence: float                  # 事件可信度 (0.0-1.0)
    trigger_conditions: Dict[str, Any] # 觸發條件
    ue_id: str                        # 用戶設備ID
    source_cell: str                  # 源小區ID
    target_cells: List[str]           # 候選目標小區ID列表
    measurement_values: Dict[str, float] # 測量值 (RSRP, RSRQ, SINR等)
    
    def __post_init__(self):
        """後處理驗證"""
        if self.timestamp == 0:
            self.timestamp = time.time()
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

class EventProcessorInterface(ABC):
    """事件處理器抽象接口"""
    
    @abstractmethod
    def process_event(self, event_type: str, event_data: Dict[str, Any]) -> ProcessedEvent:
        """
        處理3GPP事件並返回結構化事件數據
        
        Args:
            event_type: 事件類型 (A4/D1/D2/T1)
            event_data: 原始事件數據
            
        Returns:
            ProcessedEvent: 處理後的事件數據
            
        Raises:
            InvalidEventError: 事件數據無效
            UnsupportedEventError: 不支援的事件類型
        """
        pass
    
    @abstractmethod
    def validate_event(self, event: Dict[str, Any]) -> bool:
        """
        驗證事件的合法性和完整性
        
        Args:
            event: 事件數據
            
        Returns:
            bool: 是否通過驗證
        """
        pass
    
    @abstractmethod
    def get_trigger_conditions(self, event_type: str) -> Dict[str, Any]:
        """
        獲取事件觸發條件
        
        Args:
            event_type: 事件類型
            
        Returns:
            Dict[str, Any]: 觸發條件配置
        """
        pass
    
    @abstractmethod
    def get_supported_events(self) -> List[str]:
        """
        獲取支援的事件類型列表
        
        Returns:
            List[str]: 支援的事件類型
        """
        pass
    
    @abstractmethod
    def extract_measurement_values(self, event_data: Dict[str, Any]) -> Dict[str, float]:
        """
        提取測量值 (RSRP, RSRQ, SINR等)
        
        Args:
            event_data: 事件數據
            
        Returns:
            Dict[str, float]: 測量值字典
        """
        pass

class InvalidEventError(Exception):
    """無效事件錯誤"""
    pass

class UnsupportedEventError(Exception):
    """不支援的事件類型錯誤"""
    pass