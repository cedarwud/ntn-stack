# Validation Framework Core Module
"""
NTN Stack 驗證框架核心模組

這個模組實現了學術級數據驗證框架，確保：
- 零容忍學術造假檢測
- Grade A 數據標準強制執行  
- 多層次數據品質保證
- 自動化驗證流程控制
"""

__version__ = "1.0.0"
__author__ = "NTN Stack Validation Team"

from .base_validator import BaseValidator, ValidationResult
from .validation_engine import ValidationEngine
from .error_handler import ValidationError, ValidationWarning

__all__ = [
    "BaseValidator",
    "ValidationResult", 
    "ValidationEngine",
    "ValidationError",
    "ValidationWarning"
]
