"""
Phase 3: 決策透明化與視覺化分析模組

此模組提供先進的強化學習決策分析、透明化解釋和視覺化功能，
為學術研究和生產環境提供完整的 Algorithm Explainability 支援。

核心功能：
- 高級決策透明化分析
- 收斂性分析和學習曲線追蹤
- 統計顯著性測試和多算法性能對比
- 學術標準數據匯出
- 先進視覺化和實時監控

Created for Phase 3: Decision Transparency & Visualization Optimization
"""

from .advanced_explainability_engine import (
    AdvancedExplainabilityEngine,
    ExplainabilityReport,
    DecisionPathAnalysis,
    FeatureImportanceResult
)

from .convergence_analyzer import (
    ConvergenceAnalyzer,
    ConvergenceMetrics,
    LearningCurveAnalysis,
    PerformanceTrend
)

from .statistical_testing_engine import (
    StatisticalTestingEngine,
    StatisticalTest,
    TestResult,
    SignificanceAnalysis
)

from .academic_data_exporter import (
    AcademicDataExporter,
    ExportFormat,
    ResearchDataPackage,
    PublicationReadyReport
)

from .visualization_engine import (
    VisualizationEngine,
    DashboardData,
    RealtimeVisualizationService
)

__all__ = [
    # Advanced Explainability
    'AdvancedExplainabilityEngine',
    'ExplainabilityReport',
    'DecisionPathAnalysis', 
    'FeatureImportanceResult',
    
    # Convergence Analysis
    'ConvergenceAnalyzer',
    'ConvergenceMetrics',
    'LearningCurveAnalysis',
    'PerformanceTrend',
    
    # Statistical Testing
    'StatisticalTestingEngine',
    'StatisticalTest',
    'TestResult', 
    'SignificanceAnalysis',
    
    # Academic Export
    'AcademicDataExporter',
    'ExportFormat',
    'ResearchDataPackage',
    'PublicationReadyReport',
    
    # Visualization
    'VisualizationEngine',
    'DashboardData',
    'RealtimeVisualizationService'
]

# Version information
__version__ = "3.0.0"
__phase__ = "Phase 3: Decision Transparency & Visualization Optimization"