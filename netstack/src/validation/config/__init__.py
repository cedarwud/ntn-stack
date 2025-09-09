# Validation Framework Configuration Module
"""
驗證框架配置管理模組

提供統一的配置管理功能：
- 驗證器配置
- 學術標準設定
- 系統參數配置
- 環境變數管理
"""

from .config_manager import ConfigManager, ValidationConfig
from .academic_standards_config import AcademicStandardsConfig, GRADE_A_REQUIREMENTS

__all__ = [
    "ConfigManager",
    "ValidationConfig", 
    "AcademicStandardsConfig",
    "GRADE_A_REQUIREMENTS"
]
