"""
候選篩選器接口定義
==================

定義了衛星候選篩選和評分的統一接口，支持多種篩選策略。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
from .event_processor import ProcessedEvent

@dataclass
class Candidate:
    """候選衛星數據結構"""
    satellite_id: str              # 衛星ID
    elevation: float               # 仰角 (度)
    signal_strength: float         # 信號強度 (dBm)
    load_factor: float            # 負載因子 (0.0-1.0)
    distance: float               # 距離 (km)
    azimuth: float                # 方位角 (度)
    doppler_shift: float          # 都卜勒頻移 (Hz)
    position: Dict[str, float]    # 3D座標 {x, y, z}
    velocity: Dict[str, float]    # 3D速度 {vx, vy, vz}
    visibility_time: float        # 可見時間 (秒)
    
    def __post_init__(self):
        """後處理驗證"""
        if not 0.0 <= self.load_factor <= 1.0:
            raise ValueError(f"Load factor must be between 0.0 and 1.0, got {self.load_factor}")
        if self.elevation < 0 or self.elevation > 90:
            raise ValueError(f"Elevation must be between 0 and 90 degrees, got {self.elevation}")

@dataclass
class ScoredCandidate:
    """評分後的候選衛星"""
    candidate: Candidate           # 候選衛星數據
    score: float                  # 綜合評分 (0.0-1.0)
    confidence: float             # 評分置信度 (0.0-1.0)
    ranking: int                  # 排名 (1-based)
    sub_scores: Dict[str, float]  # 子項評分 (仰角、信號、負載等)
    reasoning: Dict[str, Any]     # 評分理由
    
    def __post_init__(self):
        """後處理驗證"""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

class CandidateSelectorInterface(ABC):
    """候選篩選器抽象接口"""
    
    @abstractmethod
    async def select_candidates(self, processed_event: ProcessedEvent, 
                         satellite_pool: List[Dict]) -> List[Candidate]:
        """
        從衛星池中選擇候選衛星
        
        Args:
            processed_event: 處理後的事件數據
            satellite_pool: 可用衛星池
            
        Returns:
            List[Candidate]: 候選衛星列表
        """
        pass
    
    @abstractmethod
    async def score_candidates(self, candidates: List[Candidate], 
                        context: Dict[str, Any] = None) -> List[ScoredCandidate]:
        """
        對候選衛星進行評分
        
        Args:
            candidates: 候選衛星列表
            context: 額外上下文信息
            
        Returns:
            List[ScoredCandidate]: 評分後的候選列表
        """
        pass
    
    @abstractmethod
    def filter_candidates(self, candidates: List[Candidate], 
                         criteria: Dict[str, Any]) -> List[Candidate]:
        """
        根據條件篩選候選衛星
        
        Args:
            candidates: 候選衛星列表
            criteria: 篩選條件
            
        Returns:
            List[Candidate]: 篩選後的候選列表
        """
        pass
    
    @abstractmethod
    def get_selection_strategies(self) -> List[str]:
        """
        獲取可用的篩選策略列表
        
        Returns:
            List[str]: 策略名稱列表
        """
        pass
    
    @abstractmethod
    async def apply_strategy(self, strategy_name: str, 
                      candidates: List[Candidate],
                      parameters: Dict[str, Any] = None) -> List[Candidate]:
        """
        應用特定的篩選策略
        
        Args:
            strategy_name: 策略名稱
            candidates: 候選列表
            parameters: 策略參數
            
        Returns:
            List[Candidate]: 策略篩選後的候選列表
        """
        pass
    
    @abstractmethod
    def calculate_visibility_window(self, candidate: Candidate, 
                                  user_position: Dict[str, float]) -> float:
        """
        計算候選衛星的可見時間窗口
        
        Args:
            candidate: 候選衛星
            user_position: 用戶位置
            
        Returns:
            float: 可見時間 (秒)
        """
        pass

class SelectionStrategyError(Exception):
    """篩選策略錯誤"""
    pass