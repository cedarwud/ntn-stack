"""
驗證引擎模組初始化
Validation Engines Module Initialization

導出所有驗證引擎和相關類別
"""

from .academic_standards_engine import (
    GradeADataValidator,
    PhysicalParameterValidator, 
    TimeBaseContinuityChecker,
    ZeroValueDetector,
    ECICoordinateValidationResult,
    TLEValidationResult,
    PhysicalParameterValidationResult
)

from .data_quality_engine import (
    DataStructureValidator,
    StatisticalAnalyzer,
    CrossStageConsistencyChecker,
    MetadataComplianceValidator,
    StructureValidationResult,
    StatisticalAnalysisResult,
    ConsistencyCheckResult
)

from .execution_control_engine import (
    ValidationOrchestrator,
    StageGatekeeper,
    ErrorRecoveryManager,
    ValidationSnapshotManager,
    ExecutionStage,
    ExecutionSnapshot,
    RecoveryPlan,
    ExecutionStatus,
    QualityGateStatus,
    RecoveryAction
)

# 主要驗證引擎列表
ACADEMIC_VALIDATORS = [
    GradeADataValidator,
    PhysicalParameterValidator,
    TimeBaseContinuityChecker,
    ZeroValueDetector
]

DATA_QUALITY_VALIDATORS = [
    DataStructureValidator,
    StatisticalAnalyzer,
    CrossStageConsistencyChecker,
    MetadataComplianceValidator
]

EXECUTION_CONTROL_COMPONENTS = [
    ValidationOrchestrator,
    StageGatekeeper,
    ErrorRecoveryManager,
    ValidationSnapshotManager
]

# 所有驗證器
ALL_VALIDATORS = ACADEMIC_VALIDATORS + DATA_QUALITY_VALIDATORS

# 版本信息
__version__ = "1.0.0"
__author__ = "NTN Stack Validation Framework Team"
__description__ = "Academic-grade validation engines for satellite data processing"

# 導出的公共接口
__all__ = [
    # Academic Standards Engine
    'GradeADataValidator',
    'PhysicalParameterValidator',
    'TimeBaseContinuityChecker', 
    'ZeroValueDetector',
    'ECICoordinateValidationResult',
    'TLEValidationResult',
    'PhysicalParameterValidationResult',
    
    # Data Quality Engine
    'DataStructureValidator',
    'StatisticalAnalyzer',
    'CrossStageConsistencyChecker',
    'MetadataComplianceValidator',
    'StructureValidationResult',
    'StatisticalAnalysisResult',
    'ConsistencyCheckResult',
    
    # Execution Control Engine
    'ValidationOrchestrator',
    'StageGatekeeper',
    'ErrorRecoveryManager',
    'ValidationSnapshotManager',
    'ExecutionStage',
    'ExecutionSnapshot',
    'RecoveryPlan',
    'ExecutionStatus',
    'QualityGateStatus',
    'RecoveryAction',
    
    # 集合
    'ACADEMIC_VALIDATORS',
    'DATA_QUALITY_VALIDATORS',
    'EXECUTION_CONTROL_COMPONENTS',
    'ALL_VALIDATORS'
]