"""
階段二：衛星可見性過濾處理器 - 方案一簡化版本
只處理基本地理可見性過濾，避免功能重疊

功能移轉說明：
- 信號分析功能 → Stage 3 (Stage3SignalAnalysisProcessor)
- 換手決策邏輯 → Stage 3 (handover_decision_engine)
- 覆蓋規劃算法 → Stage 6 (dynamic_coverage_optimizer)
- 學術驗證系統 → 系統級功能
"""

from .simple_stage2_processor import SimpleStage2Processor

# 為了向後兼容，使用別名
SatelliteVisibilityFilterProcessor = SimpleStage2Processor

__all__ = ['SatelliteVisibilityFilterProcessor']