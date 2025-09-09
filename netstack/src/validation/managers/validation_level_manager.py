#!/usr/bin/env python3
"""
驗證級別管理器 - Phase 3+ 重構版
===================================

提供可配置的驗證級別管理，支持 FAST/STANDARD/COMPREHENSIVE 三級模式
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """驗證級別枚舉"""
    FAST = "fast"                    # 快速模式：僅關鍵檢查
    STANDARD = "standard"            # 標準模式：平衡檢查 
    COMPREHENSIVE = "comprehensive"  # 完整模式：全面檢查

class ValidationLevelManager:
    """驗證級別管理器"""
    
    def __init__(self):
        """初始化驗證級別管理器"""
        self.stage_levels = {
            'stage1': ValidationLevel.STANDARD,
            'stage2': ValidationLevel.STANDARD,
            'stage3': ValidationLevel.STANDARD,
            'stage4': ValidationLevel.FAST,        # 時序處理用快速級別
            'stage5': ValidationLevel.STANDARD,
            'stage6': ValidationLevel.COMPREHENSIVE # 最終規劃用完整級別
        }
        
        self.performance_stats = {
            'total_validations': 0,
            'avg_execution_time_ms': 0.0,
            'validation_success_rate': 1.0
        }
        
        logger.debug("ValidationLevelManager 初始化完成")
    
    def get_validation_level(self, stage_name: str) -> str:
        """
        獲取指定階段的驗證級別
        
        Args:
            stage_name: 階段名稱 (如 'stage1', 'stage2' 等)
            
        Returns:
            驗證級別字符串 ('fast', 'standard', 'comprehensive')
        """
        level = self.stage_levels.get(stage_name, ValidationLevel.STANDARD)
        return level.value
    
    def set_validation_level(self, stage_name: str, level: str):
        """
        設置指定階段的驗證級別
        
        Args:
            stage_name: 階段名稱
            level: 驗證級別 ('fast', 'standard', 'comprehensive')
        """
        try:
            validation_level = ValidationLevel(level.lower())
            self.stage_levels[stage_name] = validation_level
            logger.info(f"設置 {stage_name} 驗證級別為 {level}")
        except ValueError:
            logger.warning(f"無效的驗證級別: {level}，使用預設 STANDARD")
            self.stage_levels[stage_name] = ValidationLevel.STANDARD
    
    def get_all_levels(self) -> Dict[str, str]:
        """獲取所有階段的驗證級別"""
        return {stage: level.value for stage, level in self.stage_levels.items()}
    
    def set_global_level(self, level: str):
        """設置所有階段的驗證級別"""
        for stage in self.stage_levels.keys():
            self.set_validation_level(stage, level)
        logger.info(f"設置全局驗證級別為 {level}")
    
    def get_recommended_level(self, system_load: float = 50.0, time_constraint: float = 120.0) -> str:
        """
        根據系統負載和時間約束推薦驗證級別
        
        Args:
            system_load: 系統負載百分比 (0-100)
            time_constraint: 時間約束(秒)
            
        Returns:
            推薦的驗證級別
        """
        if system_load > 80 or time_constraint < 30:  # 高負載或時間緊迫
            return ValidationLevel.FAST.value
        elif system_load > 50 or time_constraint < 60:  # 中等負載
            return ValidationLevel.STANDARD.value
        else:  # 低負載且時間充裕
            return ValidationLevel.COMPREHENSIVE.value
    
    def update_performance_stats(self, execution_time_ms: float, success: bool = True):
        """更新性能統計"""
        self.performance_stats['total_validations'] += 1
        
        # 更新平均執行時間 (移動平均)
        current_avg = self.performance_stats['avg_execution_time_ms']
        total_validations = self.performance_stats['total_validations']
        
        self.performance_stats['avg_execution_time_ms'] = (
            (current_avg * (total_validations - 1) + execution_time_ms) / total_validations
        )
        
        # 更新成功率
        if success:
            success_count = int(self.performance_stats['validation_success_rate'] * (total_validations - 1)) + 1
        else:
            success_count = int(self.performance_stats['validation_success_rate'] * (total_validations - 1))
            
        self.performance_stats['validation_success_rate'] = success_count / total_validations
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        return {
            'performance_stats': self.performance_stats.copy(),
            'current_levels': self.get_all_levels(),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> Dict[str, str]:
        """生成優化建議"""
        recommendations = {}
        avg_time = self.performance_stats['avg_execution_time_ms']
        success_rate = self.performance_stats['validation_success_rate']
        
        if avg_time > 1000:  # 超過1秒
            recommendations['performance'] = "考慮降級到FAST模式以提升性能"
        elif avg_time < 100:  # 小於100毫秒
            recommendations['performance'] = "可以升級到COMPREHENSIVE模式提供更完整驗證"
            
        if success_rate < 0.95:  # 成功率低於95%
            recommendations['reliability'] = "建議升級到COMPREHENSIVE模式提高檢查覆蓋率"
            
        return recommendations

# 全局實例
_global_manager = None

def get_validation_level_manager() -> ValidationLevelManager:
    """獲取全局驗證級別管理器實例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = ValidationLevelManager()
    return _global_manager