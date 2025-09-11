"""
Stage 2: 衛星可見性過濾階段 - 模組化重構版

模組結構:
- stage2_processor.py          # 主處理器，繼承BaseStageProcessor
- orbital_data_loader.py       # 軌道數據載入器（從Stage 1）
- visibility_calculator.py     # 可見性計算引擎
- elevation_filter.py          # 仰角過濾器（ITU-R標準）
- visibility_analyzer.py       # 可見性時間窗口分析器
- result_formatter.py          # 結果格式化器

職責：
- 從Stage 1載入軌道計算結果
- 基於觀測點計算衛星可見性
- 應用動態仰角門檻（ITU-R標準）
- 進行智能可見性過濾
- 輸出符合下一階段的標準化結果
"""

from .satellite_visibility_filter_processor import SatelliteVisibilityFilterProcessor
from .orbital_data_loader import OrbitalDataLoader
from .visibility_calculator import VisibilityCalculator
from .elevation_filter import ElevationFilter
from .visibility_analyzer import VisibilityAnalyzer
from .result_formatter import ResultFormatter

__all__ = [
    'SatelliteVisibilityFilterProcessor',
    'OrbitalDataLoader', 
    'VisibilityCalculator',
    'ElevationFilter',
    'VisibilityAnalyzer',
    'ResultFormatter'
]