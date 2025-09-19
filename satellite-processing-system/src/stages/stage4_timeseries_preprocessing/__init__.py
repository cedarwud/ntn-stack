"""
Stage 4: 時間序列預處理階段

核心架構:
- stage4_main_processor.py                    # 主處理器 - 流程編排和協調
- timeseries_analysis_engine.py               # 時間序列分析引擎
- coverage_analysis_engine.py                 # 覆蓋分析引擎
- timeseries_converter.py                    # 時間序列格式轉換器
- stage4_academic_standards_validator.py     # 學術標準驗證器 (主控制器)
- academic_data_precision_validator.py       # 數據精度驗證器
- academic_compliance_checker.py             # 學術合規檢查器
- output_formatter.py                       # 輸出格式化器
- unified_data_loader.py                    # 統一數據載入器
- animation_builder.py                      # 動畫建構器
- real_time_monitoring.py                  # 實時監控

設計原則:
- 主處理器只負責流程控制和模組協調
- 專注於時間序列預處理和分析
- 保持模組化和可測試性
"""

# 導入主要組件
from .stage4_main_processor import Stage4MainProcessor
from .stage4_academic_standards_validator import Stage4AcademicStandardsValidator
from .unified_data_loader import UnifiedDataLoader
from .timeseries_analysis_engine import TimeseriesAnalysisEngine
from .coverage_analysis_engine import CoverageAnalysisEngine

# 向後兼容導入
TimeseriesPreprocessingProcessor = Stage4MainProcessor

__all__ = [
    # 主要組件
    'Stage4MainProcessor',
    'Stage4AcademicStandardsValidator',
    'UnifiedDataLoader',
    'TimeseriesAnalysisEngine',
    'CoverageAnalysisEngine',

    # 向後兼容
    'TimeseriesPreprocessingProcessor'
]