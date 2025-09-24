"""
Stage 1: 數據載入層 - v2.0 模組化架構

v2.0 模組化核心架構:
- stage1_data_loading_processor.py      # 主處理器 (Stage1DataLoadingProcessor) - v2.0
- tle_data_loader.py                    # TLE數據載入器
- data_validator.py                     # 數據驗證器
- time_reference_manager.py             # 時間基準管理器

職責邊界 (v2.0):
- 專注於TLE數據載入和驗證
- 建立時間基準供後續階段繼承
- 純數據層，無軌道計算
- 為Stage 2提供標準化TLE數據

傳統組件 (向後兼容):
- tle_orbital_calculation_processor.py  # 傳統處理器 (Stage1TLEProcessor) - 包含軌道計算
- orbital_calculator.py                 # 軌道計算引擎
- orbital_validation_engine.py          # 軌道驗證引擎
"""

# 導入v2.0主處理器
from .stage1_data_loading_processor import Stage1DataLoadingProcessor

# 導入核心組件
from .tle_data_loader import TLEDataLoader
from .data_validator import DataValidator
from .time_reference_manager import TimeReferenceManager

# 導入傳統組件 (向後兼容)
from .tle_orbital_calculation_processor import Stage1TLEProcessor
from .orbital_calculator import OrbitalCalculator
from .orbital_validation_engine import OrbitalValidationEngine

__all__ = [
    # v2.0 模組化架構
    'Stage1DataLoadingProcessor',  # 主處理器 (v2.0)
    'TLEDataLoader',               # TLE數據載入器
    'DataValidator',               # 數據驗證器
    'TimeReferenceManager',        # 時間基準管理器

    # 傳統組件 (向後兼容)
    'Stage1TLEProcessor',          # 傳統處理器 (包含軌道計算)
    'OrbitalCalculator',           # 軌道計算器
    'OrbitalValidationEngine'      # 軌道驗證引擎
]