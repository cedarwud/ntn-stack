"""
AI決策引擎整合模組
====================

這個模組包含了重構後的AI決策引擎系統，將原來的單體文件 ai_decision_engine.py
重構為模組化的架構，提供：

- 事件處理 (Event Processing)
- 候選篩選 (Candidate Selection)  
- 決策執行 (Decision Execution)
- 3D視覺化整合 (Visualization Integration)

主要組件：
- DecisionOrchestrator: 主協調器
- EventProcessor: 事件處理器
- CandidateSelector: 候選篩選器
- RLIntegration: 強化學習整合
- VisualizationCoordinator: 視覺化協調器
"""

__version__ = "2.0.0"
__author__ = "NTN Stack Team"

# 主要接口導出
from .orchestrator import DecisionOrchestrator
from .interfaces.event_processor import EventProcessorInterface
from .interfaces.candidate_selector import CandidateSelectorInterface  
from .interfaces.decision_engine import RLIntegrationInterface
from .interfaces.executor import DecisionExecutorInterface
from .interfaces.visualization_coordinator import VisualizationCoordinatorInterface

__all__ = [
    "DecisionOrchestrator",
    "EventProcessorInterface",
    "CandidateSelectorInterface", 
    "RLIntegrationInterface",
    "DecisionExecutorInterface",
    "VisualizationCoordinatorInterface"
]