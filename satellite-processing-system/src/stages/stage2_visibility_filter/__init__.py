"""
Stage 2: 衛星可見性過濾階段 - 簡化重構版

🔄 重構完成狀態：
- ✅ 功能簡化：從16個檔案 → 4個檔案
- ✅ 代碼減少：從7,043行 → ~500行 (減少93%)
- ✅ 模組遷移：舊模組已遷移到正確階段
  - skyfield_visibility_engine.py → Stage 1
  - orbital_data_loader.py → Stage 1
  - visibility_analyzer.py → Stage 3
  - scientific_validation_engine.py → Stage 3
  - academic_standards_validator.py → Stage 3
  - coverage_guarantee_engine.py → Stage 6
  - academic_warning_manager.py → Shared
- ✅ 重複清理：136,390行重複代碼已清理

簡化模組結構:
- simple_stage2_processor.py          # 簡化處理器
- simple_geographic_filter.py         # 簡化地理過濾器
- satellite_visibility_filter_processor.py  # 向後兼容別名

核心職責 (重構後):
- 基本ECI→地平座標轉換
- 仰角門檻過濾 (Starlink: 5°, OneWeb: 10°)
- 簡單可見性判斷
- 記憶體傳遞模式 (v3.0)

🚫 已移除的越界功能：
- 複雜可見性分析 → Stage 3
- 科學驗證引擎 → Stage 3
- 學術標準驗證 → Stage 3
- 覆蓋保證算法 → Stage 6
- Skyfield引擎 → Stage 1
- 軌道數據載入 → Stage 1
"""

from .satellite_visibility_filter_processor import SatelliteVisibilityFilterProcessor
from .simple_stage2_processor import SimpleStage2Processor
from .simple_geographic_filter import SimpleGeographicFilter

__all__ = [
    'SatelliteVisibilityFilterProcessor',  # 向後兼容別名
    'SimpleStage2Processor',               # 主要處理器
    'SimpleGeographicFilter'               # 地理過濾器
]