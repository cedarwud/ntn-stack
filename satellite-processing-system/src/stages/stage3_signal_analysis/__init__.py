"""
Stage 3: 信號分析階段 - 精簡化重構版

精簡化後的架構(目標: 主處理器<400行):
- stage3_main_processor.py               # 精簡主處理器 (新) - 只負責流程編排
- stage3_signal_analysis_processor.py    # 舊版主處理器 (向後兼容)
- signal_quality_calculator.py           # 信號品質計算器
- stage3_academic_standards_validator.py # 學術標準驗證器
- physics_validator.py                   # 物理參數驗證器
- gpp_event_analyzer.py                  # 3GPP事件分析器
- handover_decision_engine.py            # 換手決策引擎
- recommendation_engine.py               # 推薦引擎
- signal_prediction_engine.py            # 信號預測引擎
- signal_output_formatter.py             # 輸出格式化器

精簡化原則:
- 主處理器只負責流程控制和模組協調
- 所有複雜實現都委派給專業模組
- 保持向後兼容性
"""

# 導入精簡主處理器 (推薦)
from .stage3_main_processor import Stage3MainProcessor

# 向後兼容 (舊版)
try:
    from .stage3_signal_analysis_processor import Stage3SignalAnalysisProcessor
except ImportError:
    # 如果舊版不存在，使用新版作為替代
    Stage3SignalAnalysisProcessor = Stage3MainProcessor

# 🚨 Grade A要求：動態計算RSRP閾值
noise_floor = -120  # 3GPP典型噪聲門檻

__all__ = [
    'Stage3MainProcessor',           # 新版精簡處理器
    'Stage3SignalAnalysisProcessor'  # 向後兼容
]