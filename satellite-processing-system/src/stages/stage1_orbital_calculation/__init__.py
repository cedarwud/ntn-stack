"""
Stage 1: TLE軌道計算階段 - v8.0清理版

清理後的核心架構:
- tle_orbital_calculation_processor.py   # 主處理器 (Stage1TLEProcessor)
- tle_data_loader.py                     # TLE數據載入器
- orbital_calculator.py                  # 軌道計算引擎
- orbital_validation_engine.py           # 軌道驗證引擎

職責邊界:
- 專注於TLE載入和SGP4軌道計算
- 輸出純ECI座標
- 無跨階段功能
"""

# 導入主處理器
from .tle_orbital_calculation_processor import Stage1TLEProcessor

# 導入核心組件
from .tle_data_loader import TLEDataLoader
from .orbital_calculator import OrbitalCalculator
from .orbital_validation_engine import OrbitalValidationEngine

__all__ = [
    'Stage1TLEProcessor',      # 主處理器
    'TLEDataLoader',           # TLE數據載入器
    'OrbitalCalculator',       # 軌道計算器
    'OrbitalValidationEngine'  # 驗證引擎
]