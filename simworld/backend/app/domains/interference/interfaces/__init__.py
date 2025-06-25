"""
Interference Domain Interfaces

This module defines the interfaces for the interference domain,
following the dependency inversion principle of clean architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class InterferenceDetectorInterface(ABC):
    """Interface for interference detection services"""
    
    @abstractmethod
    async def detect_interference(
        self, 
        ue_positions: List[Dict], 
        gnb_positions: List[Dict],
        current_sinr: List[float]
    ) -> Dict[str, Any]:
        """Detect interference in the network"""
        pass


class AntiInterferenceInterface(ABC):
    """Interface for anti-interference services"""
    
    @abstractmethod
    async def mitigate_interference(
        self, 
        interference_data: Dict[str, Any],
        network_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply anti-interference mitigation strategies"""
        pass


class AlgorithmPerformanceInterface(ABC):
    """Interface for algorithm performance measurement"""
    
    @abstractmethod
    async def measure_performance(
        self, 
        algorithm_name: str,
        test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Measure algorithm performance metrics"""
        pass