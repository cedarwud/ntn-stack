"""
演算法介面定義
定義換手演算法的抽象介面，為將來的重構提供基礎
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from app.domains.coordinates.models.coordinate_model import GeoCoordinate
from app.domains.handover.models.handover_models import (
    HandoverPredictionRequest,
    HandoverPredictionResponse,
    BinarySearchIteration
)


class AlgorithmInterface(ABC):
    """演算法基礎介面"""

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """執行演算法的抽象方法"""
        pass


class TwoPointPredictionInterface(AlgorithmInterface):
    """二點預測演算法介面"""

    @abstractmethod
    async def predict(
        self, 
        request: HandoverPredictionRequest, 
        ue_location: GeoCoordinate
    ) -> HandoverPredictionResponse:
        """執行二點預測"""
        pass


class BinarySearchInterface(AlgorithmInterface):
    """二元搜尋演算法介面"""

    @abstractmethod
    async def search(
        self,
        start_time: datetime,
        end_time: datetime,
        ue_location: GeoCoordinate,
        precision_threshold: float
    ) -> Tuple[Optional[datetime], Optional[BinarySearchIteration]]:
        """執行二元搜尋找出精確換手時間"""
        pass


class SatelliteSelectionInterface(AlgorithmInterface):
    """衛星選擇演算法介面"""

    @abstractmethod
    async def select_best_satellite(
        self,
        timestamp: datetime,
        ue_location: GeoCoordinate
    ) -> Dict[str, Any]:
        """選擇最佳衛星"""
        pass


class LatencyCalculatorInterface(ABC):
    """延遲計算器介面"""

    @abstractmethod
    async def calculate_latency(
        self,
        algorithm_type: str,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """計算延遲"""
        pass


class ScenarioAnalyzerInterface(ABC):
    """場景分析器介面"""

    @abstractmethod
    async def analyze_scenario(
        self,
        scenario_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析場景"""
        pass