"""
Simplified Handover Models
簡化的換手模型，避免 SQLModel 依賴
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List
import time


@dataclass
class HandoverPredictionRecord:
    """換手預測記錄"""
    ue_id: str
    current_satellite: str
    predicted_satellite: str
    handover_time: Optional[float] = None
    prediction_confidence: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class BinarySearchIteration:
    """Binary Search 迭代記錄"""
    iteration: int
    start_time: float
    end_time: float
    mid_time: float
    satellite: str
    precision: float
    completed: bool = False