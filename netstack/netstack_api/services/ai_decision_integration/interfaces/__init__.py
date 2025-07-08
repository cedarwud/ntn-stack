"""
AI決策引擎接口定義
==================

定義了所有核心組件的抽象接口，確保模組間的鬆耦合和可測試性。
"""

from .event_processor import EventProcessorInterface, ProcessedEvent
from .candidate_selector import CandidateSelectorInterface, Candidate, ScoredCandidate
from .decision_engine import RLIntegrationInterface, Decision
from .executor import DecisionExecutorInterface, ExecutionResult
from .visualization_coordinator import VisualizationCoordinatorInterface, VisualizationEvent

__all__ = [
    "EventProcessorInterface",
    "ProcessedEvent", 
    "CandidateSelectorInterface",
    "Candidate",
    "ScoredCandidate",
    "RLIntegrationInterface", 
    "Decision",
    "DecisionExecutorInterface",
    "ExecutionResult",
    "VisualizationCoordinatorInterface",
    "VisualizationEvent"
]