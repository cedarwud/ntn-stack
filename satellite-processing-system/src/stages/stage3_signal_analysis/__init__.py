"""
Stage 3: 信號分析階段 - 純粹信號分析版 v2.0

符合文檔定義的4個核心模組:
- signal_quality_calculator.py    # RSRP/RSRQ/SINR計算
- gpp_event_detector.py           # 3GPP事件檢測
- physics_calculator.py           # 物理參數計算
- stage3_signal_analysis_processor.py  # 主處理器

v2.0核心原則:
- 移除換手決策功能
- 專注純粹信號分析
- 完全符合文檔架構
"""

# 導入核心模組
from .stage3_signal_analysis_processor import Stage3SignalAnalysisProcessor

# 🚨 Grade A要求：動態計算RSRP閾值
noise_floor = -120  # 3GPP典型噪聲門檻

__all__ = [
    'Stage3SignalAnalysisProcessor'  # 純粹信號分析處理器
]