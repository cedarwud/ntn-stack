"""
視覺化協調器接口定義
====================

定義了3D視覺化和前端同步的統一接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class AnimationType(Enum):
    """動畫類型枚舉"""
    HANDOVER_STARTED = "handover_started"
    CANDIDATE_SELECTION = "candidate_selection"
    DECISION_MADE = "decision_made"
    EXECUTION_COMPLETE = "execution_complete"
    SATELLITE_MOVEMENT = "satellite_movement"
    SIGNAL_QUALITY_UPDATE = "signal_quality_update"
    NETWORK_TOPOLOGY_CHANGE = "network_topology_change"

@dataclass
class VisualizationEvent:
    """視覺化事件數據結構"""
    event_type: AnimationType           # 事件類型
    timestamp: float                   # 時間戳
    satellite_data: Dict[str, Any]     # 衛星數據
    animation_params: Dict[str, Any]   # 動畫參數
    duration_ms: int                   # 動畫持續時間
    priority: int = 0                  # 事件優先級 (0-10)
    user_id: Optional[str] = None      # 用戶ID
    session_id: Optional[str] = None   # 會話ID
    
    def __post_init__(self):
        """後處理驗證"""
        if self.duration_ms <= 0:
            self.duration_ms = 1000  # 默認1秒
        if not 0 <= self.priority <= 10:
            raise ValueError(f"Priority must be between 0 and 10, got {self.priority}")

@dataclass
class AnimationState:
    """動畫狀態"""
    animation_id: str                  # 動畫ID
    status: str                        # 狀態 (active/paused/completed/cancelled)
    progress: float                    # 進度 (0.0-1.0)
    start_time: float                  # 開始時間
    duration: float                    # 持續時間
    parameters: Dict[str, Any]         # 動畫參數

class VisualizationCoordinatorInterface(ABC):
    """視覺化協調器抽象接口"""
    
    @abstractmethod
    async def trigger_3d_animation(self, event: VisualizationEvent) -> str:
        """
        觸發3D動畫更新
        
        Args:
            event: 視覺化事件
            
        Returns:
            str: 動畫ID
        """
        pass
    
    @abstractmethod
    async def sync_with_frontend(self, state: Dict[str, Any]) -> None:
        """
        與前端同步狀態
        
        Args:
            state: 要同步的狀態數據
        """
        pass
    
    @abstractmethod
    async def stream_realtime_updates(self, decision_flow: Dict[str, Any]) -> None:
        """
        推送即時更新到前端
        
        Args:
            decision_flow: 決策流程數據
        """
        pass
    
    @abstractmethod
    async def update_satellite_positions(self, satellite_positions: List[Dict[str, Any]]) -> None:
        """
        更新衛星位置
        
        Args:
            satellite_positions: 衛星位置列表
        """
        pass
    
    @abstractmethod
    async def highlight_selected_satellite(self, satellite_id: str, 
                                         highlight_params: Dict[str, Any]) -> None:
        """
        高亮顯示選中的衛星
        
        Args:
            satellite_id: 衛星ID
            highlight_params: 高亮參數
        """
        pass
    
    @abstractmethod
    async def show_handover_path(self, source_id: str, target_id: str,
                               path_params: Dict[str, Any]) -> str:
        """
        顯示換手路徑動畫
        
        Args:
            source_id: 源衛星ID
            target_id: 目標衛星ID
            path_params: 路徑參數
            
        Returns:
            str: 動畫ID
        """
        pass
    
    @abstractmethod
    async def update_network_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        更新網路指標顯示
        
        Args:
            metrics: 網路指標數據
        """
        pass
    
    @abstractmethod
    def get_animation_state(self, animation_id: str) -> Optional[AnimationState]:
        """
        獲取動畫狀態
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            Optional[AnimationState]: 動畫狀態
        """
        pass
    
    @abstractmethod
    def get_active_animations(self) -> List[AnimationState]:
        """
        獲取所有活躍動畫
        
        Returns:
            List[AnimationState]: 活躍動畫列表
        """
        pass
    
    @abstractmethod
    async def pause_animation(self, animation_id: str) -> bool:
        """
        暫停動畫
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            bool: 是否成功暫停
        """
        pass
    
    @abstractmethod
    async def resume_animation(self, animation_id: str) -> bool:
        """
        恢復動畫
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            bool: 是否成功恢復
        """
        pass
    
    @abstractmethod
    async def cancel_animation(self, animation_id: str) -> bool:
        """
        取消動畫
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            bool: 是否成功取消
        """
        pass

class VisualizationError(Exception):
    """視覺化錯誤基類"""
    pass

class AnimationNotFoundError(VisualizationError):
    """動畫未找到錯誤"""
    pass