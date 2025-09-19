"""
Stage 6 Dynamic Planning - 模組化動態池規劃處理器

此模組提供動態衛星池規劃的完整實現，專注於：
- 智能軌道相位選擇策略
- 時空錯置理論實戰應用  
- 動態覆蓋需求優化
- 軌道週期完整驗證

模組化設計特色：
- 7個專業組件各司其職
- 革命性除錯能力
- 學術級標準合規
- 完整物理計算驗證
"""

from .stage6_processor import Stage6Processor
from .data_integration_loader import DataIntegrationLoader
from .candidate_converter import CandidateConverter  
from .dynamic_coverage_optimizer import DynamicCoverageOptimizer
from .satellite_selection_engine import SatelliteSelectionEngine
from .physics_calculation_engine import PhysicsCalculationEngine
from .validation_engine import ValidationEngine
from .output_generator import OutputGenerator

__all__ = [
    "Stage6Processor",
    "DataIntegrationLoader", 
    "CandidateConverter",
    "DynamicCoverageOptimizer",
    "SatelliteSelectionEngine",
    "PhysicsCalculationEngine",
    "ValidationEngine",
    "OutputGenerator"
]

__version__ = "1.0.0"
__module_type__ = "dynamic_planning_processor"
__academic_grade__ = "A"
