"""
Stage 4信號分析處理 - 模組化組件

本模組將原本1,862行的SignalQualityAnalysisProcessor
重構為7個專用組件，提供：

核心組件：
- TimseriesDataLoader: 載入Stage 3時間序列輸出
- SignalQualityCalculator: RSRP信號強度計算  
- GPPEventAnalyzer: 3GPP NTN事件分析
- PhysicsValidator: Friis公式和都卜勒頻率驗證
- RecommendationEngine: 最終衛星選擇建議生成
- SignalOutputFormatter: 信號分析結果格式化
- Stage4Processor: 主處理器整合

特性：
- 學術級標準合規 (Grade A)
- 模組化設計，單一職責
- 完整的物理公式驗證
- 與Stage 1-3架構統一
- 支持3GPP NTN標準事件分析
"""

from .stage4_processor import Stage4Processor

__all__ = ['Stage4Processor']