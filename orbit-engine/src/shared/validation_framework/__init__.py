"""
驗證框架 - 真實業務邏輯驗證系統

替代硬編碼 'passed' 狀態的虛假驗證，建立基於真實業務邏輯的動態驗證系統。

核心組件：
- ValidationEngine: 驗證引擎核心
- BaseValidator: 驗證器基礎類
- ValidationResult: 驗證結果管理
- FailureCriteria: 動態失敗判定
- StageXValidator: 各階段專用驗證器

作者: Claude & Human
版本: v1.0 - 真實驗證系統
"""

from .validation_engine import (
    ValidationEngine,
    BaseValidator,
    ValidationResult,
    CheckResult,
    ValidationStatus,
    FailureCriteria,
    ValidationRegistry
)

from .stage2_validator import Stage2VisibilityValidator
from .stage3_validator import Stage3SignalValidator
from .stage4_validator import Stage4TimeseriesValidator

__all__ = [
    'ValidationEngine',
    'BaseValidator',
    'ValidationResult',
    'CheckResult',
    'ValidationStatus',
    'FailureCriteria',
    'ValidationRegistry',
    'Stage2VisibilityValidator',
    'Stage3SignalValidator',
    'Stage4TimeseriesValidator'
]