"""
Handover Domain Interfaces

This module defines the interfaces for the handover domain,
following the dependency inversion principle of clean architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class HandoverManagerInterface(ABC):
    """Interface for handover management services"""
    
    @abstractmethod
    async def initiate_handover(
        self, 
        ue_id: str, 
        source_satellite: str, 
        target_satellite: str
    ) -> Dict[str, Any]:
        """Initiate a handover process"""
        pass
    
    @abstractmethod
    async def monitor_handover_progress(
        self, 
        handover_id: str
    ) -> Dict[str, Any]:
        """Monitor the progress of an ongoing handover"""
        pass


class SatelliteAccessPredictionInterface(ABC):
    """Interface for satellite access prediction services"""
    
    @abstractmethod
    async def predict_next_satellite(
        self, 
        ue_position: Dict[str, float],
        current_time: datetime
    ) -> Dict[str, Any]:
        """Predict the next optimal satellite for handover"""
        pass


class HandoverPerformanceInterface(ABC):
    """Interface for handover performance measurement"""
    
    @abstractmethod
    async def measure_handover_latency(
        self, 
        handover_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Measure handover latency statistics"""
        pass
    
    @abstractmethod
    async def calculate_success_rate(
        self, 
        time_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculate handover success rate"""
        pass