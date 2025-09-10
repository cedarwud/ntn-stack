"""
Stage 3: 時間序列預處理階段 - 模組化重構版

模組結構:
- stage3_processor.py              # 主處理器，繼承BaseStageProcessor
- visibility_data_loader.py        # 可見性數據載入器（從Stage 2）
- timeseries_converter.py          # 時間序列格式轉換器
- animation_builder.py             # 動畫數據建構器
- academic_validator.py            # 學術標準驗證器
- output_formatter.py              # 輸出格式化器

職責：
- 從Stage 2載入可見性過濾結果
- 轉換為增強時間序列格式
- 創建前端動畫所需的數據結構
- 進行學術級數據完整性驗證
- 輸出符合動畫標準的時序數據
"""

from .stage3_processor import Stage3Processor

__all__ = ['Stage3Processor']