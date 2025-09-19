"""
全局學術標準配置警告管理器
避免多個模組重複顯示相同警告造成無限循環
"""

# 使用全局變量避免類變量可能的重置問題
_ACADEMIC_WARNING_SHOWN = False

class AcademicConfigWarningManager:
    """統一管理學術標準配置警告，避免無限循環"""

    @classmethod
    def show_warning_once(cls, logger):
        """只顯示一次警告 - 現在完全靜默"""
        global _ACADEMIC_WARNING_SHOWN
        if not _ACADEMIC_WARNING_SHOWN:
            # 完全靜默，不顯示任何警告避免無限循環
            _ACADEMIC_WARNING_SHOWN = True

    @classmethod
    def reset_warning_flag(cls):
        """重置警告標記（用於測試）"""
        global _ACADEMIC_WARNING_SHOWN
        _ACADEMIC_WARNING_SHOWN = False