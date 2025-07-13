"""
🧠 RL 系統核心接口

基於 SOLID 原則設計的接口層，確保：
- 單一職責原則 (SRP)
- 開放封閉原則 (OCP)  
- 里氏替換原則 (LSP)
- 介面隔離原則 (ISP)
- 依賴反轉原則 (DIP)
"""

from .rl_algorithm import IRLAlgorithm, TrainingConfig, TrainingResult
from .training_scheduler import ITrainingScheduler
from .performance_monitor import IPerformanceMonitor
from .data_repository import IDataRepository
from .model_manager import IModelManager

__all__ = [
    'IRLAlgorithm',
    'TrainingConfig', 
    'TrainingResult',
    'ITrainingScheduler',
    'IPerformanceMonitor', 
    'IDataRepository',
    'IModelManager'
]