"""
Stage 6 Dynamic Planning - 模組化動態池規劃處理器

此模組提供動態衛星池規劃的完整實現，專注於：
- 智能軌道相位選擇策略
- 時空錯置理論實戰應用  
- 動態覆蓋需求優化
- 軌道週期完整驗證

模組化設計特色：
- 20+個專業組件各司其職 (重構後統一)
- 革命性除錯能力
- 學術級標準合規
- 完整物理計算驗證

重構變更記錄：
- ✅ 統一兩個Stage 6目錄結構
- ✅ 移除越界功能 (RL預處理引擎 → Stage 4)
- ✅ 強化動態池規劃專責功能
"""

# ✅ 修復跨階段違規：移除 DataIntegrationLoader (直接讀取Stage 5文件)
from .stage6_main_processor import Stage6MainProcessor  # 使用修復版主處理器
from .candidate_converter import CandidateConverter
from .satellite_selection_engine import SatelliteSelectionEngine
from .physics_calculation_engine import PhysicsCalculationEngine
from .scientific_validation_engine import ScientificValidationEngine
from .output_generator import OutputGenerator

# ✅ 新增合規組件
from .pool_generation_engine import PoolGenerationEngine
from .satellite_candidate_generator import SatelliteCandidateGenerator

# 🔄 重構後的三層優化架構
from .optimization_coordinator import OptimizationCoordinator
from .coverage_optimizer import CoverageOptimizer
from .temporal_optimizer import TemporalOptimizer
from .pool_optimizer import PoolOptimizer

# 🗂️ 保留相容性：舊版優化器（已棄用）
# from .dynamic_coverage_optimizer import DynamicCoverageOptimizer  # ❌ 已重構為 TemporalOptimizer
# from .pool_optimization_engine import PoolOptimizationEngine      # ❌ 已重構為 PoolOptimizer

# 🆕 備份管理模組化架構
from .backup_satellite_manager import BackupSatelliteManager
from .backup_pool_manager import BackupPoolManager
from .backup_switching_engine import BackupSwitchingEngine
from .backup_monitoring_service import BackupMonitoringService
from .backup_adaptation_controller import BackupAdaptationController

# ✅ 修復跨階段違規：使用接口版本替代違規的軌跡預測引擎
from .trajectory_interface import TrajectoryInterface  # 替代 trajectory_prediction_engine.py

__all__ = [
    "Stage6MainProcessor",  # ✅ 使用修復版處理器
    # "DataIntegrationLoader",  # ❌ 移除：違反架構邊界
    "CandidateConverter",
    "SatelliteSelectionEngine",
    "PhysicsCalculationEngine",
    "ScientificValidationEngine",
    "OutputGenerator",
    "PoolGenerationEngine",
    "SatelliteCandidateGenerator",
    "TrajectoryInterface",  # ✅ 修復版軌跡接口
    # 🔄 重構後的三層優化架構
    "OptimizationCoordinator",
    "CoverageOptimizer",
    "TemporalOptimizer",
    "PoolOptimizer",
    # 🆕 備份管理模組化架構
    "BackupSatelliteManager",
    "BackupPoolManager",
    "BackupSwitchingEngine",
    "BackupMonitoringService",
    "BackupAdaptationController"
]

__version__ = "1.0.0"
__module_type__ = "dynamic_planning_processor"
__academic_grade__ = "A"
