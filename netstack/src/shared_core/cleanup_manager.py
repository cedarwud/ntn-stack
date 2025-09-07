"""
統一清理管理器 - 支援雙模式清理策略
Author: Claude Code Assistant  
Date: 2025-09-07
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
import inspect

logger = logging.getLogger(__name__)

@dataclass
class CleanupTarget:
    """清理目標定義"""
    stage: int
    output_files: List[str]
    validation_file: str
    directories: List[str] = None

class UnifiedCleanupManager:
    """統一清理管理器 - 智能雙模式清理"""
    
    # 定義所有階段的清理目標（基於實際處理器分析）
    STAGE_CLEANUP_TARGETS = {
        1: CleanupTarget(
            stage=1,
            output_files=[
                "/app/data/tle_orbital_calculation_output.json"
            ],
            validation_file="/app/data/validation_snapshots/stage1_validation.json",
            directories=[]
        ),
        2: CleanupTarget(
            stage=2,
            output_files=[
                "/app/data/satellite_visibility_filtered_output.json",
                "/app/data/intelligent_filtered_output.json"  # 當前存在的文件
            ],
            validation_file="/app/data/validation_snapshots/stage2_validation.json", 
            directories=[]
        ),
        3: CleanupTarget(
            stage=3,
            output_files=[
                "/app/data/signal_quality_analysis_output.json"
            ],
            validation_file="/app/data/validation_snapshots/stage3_validation.json",
            directories=[]
        ),
        4: CleanupTarget(
            stage=4,
            output_files=[
                "/app/data/timeseries_preprocessing_output.json"  # 如果有單一文件
            ],
            validation_file="/app/data/validation_snapshots/stage4_validation.json",
            directories=[
                "/app/data/timeseries_preprocessing_outputs"  # 階段4創建的子目錄
            ]
        ),
        5: CleanupTarget(
            stage=5,
            output_files=[
                "/app/data/data_integration_output.json"
            ],
            validation_file="/app/data/validation_snapshots/stage5_validation.json",
            directories=[
                "/app/data/handover_scenarios",      # 階段5創建的目錄
                "/app/data/layered_phase0_enhanced", # 階段5創建的目錄  
                "/app/data/processing_cache",        # 階段5創建的目錄
                "/app/data/signal_quality_analysis", # 階段5創建的目錄
                "/app/data/status_files",            # 階段5創建的目錄
                "/app/data/data_integration_outputs" # 舊子目錄（向後兼容）
            ]
        ),
        6: CleanupTarget(
            stage=6,
            output_files=[
                "/app/data/enhanced_dynamic_pools_output.json",
                "/app/data/dynamic_pool_output.json",      # 備用名稱
                "/app/data/stage6_dynamic_pool.json",      # 舊名稱
                "/app/data/dynamic_pools.json"             # API使用的文件
            ],
            validation_file="/app/data/validation_snapshots/stage6_validation.json",
            directories=[
                "/app/data/dynamic_pool_planning_outputs"  # 舊子目錄
            ]
        )
    }
    
    def __init__(self):
        self.logger = logger
    
    def detect_execution_mode(self) -> Literal["full_pipeline", "single_stage"]:
        """
        智能檢測執行模式
        
        Returns:
            "full_pipeline": 完整管道執行
            "single_stage": 單一階段測試
        """
        
        # 方法1: 檢查環境變量
        pipeline_mode = os.getenv('PIPELINE_MODE', '').lower()
        if pipeline_mode == 'full':
            self.logger.info("🔍 檢測到環境變量: PIPELINE_MODE=full")
            return "full_pipeline"
        elif pipeline_mode == 'single':
            self.logger.info("🔍 檢測到環境變量: PIPELINE_MODE=single") 
            return "single_stage"
        
        # 方法2: 檢查調用堆疊
        try:
            # 獲取調用堆疊
            frame_info = inspect.stack()
            
            # 檢查是否從管道腳本調用
            for frame in frame_info:
                filename = frame.filename
                if 'run_six_stages' in filename or 'pipeline' in filename:
                    self.logger.info(f"🔍 檢測到管道腳本調用: {Path(filename).name}")
                    return "full_pipeline"
                    
        except Exception as e:
            self.logger.warning(f"調用堆疊檢測失敗: {e}")
        
        # 預設為單一階段模式
        self.logger.info("🔍 預設檢測結果: single_stage模式")
        return "single_stage"
    
    def cleanup_full_pipeline(self) -> Dict[str, int]:
        """
        方案一：完整管道清理
        清理所有階段的輸出檔案和驗證快照
        """
        self.logger.info("🗑️ 執行完整管道清理（方案一）")
        self.logger.info("=" * 50)
        
        total_cleaned = {"files": 0, "directories": 0}
        
        for stage_num in range(1, 7):
            stage_cleaned = self._cleanup_stage_files(stage_num, include_validation=True)
            total_cleaned["files"] += stage_cleaned["files"]
            total_cleaned["directories"] += stage_cleaned["directories"]
        
        self.logger.info("=" * 50)
        self.logger.info(f"🗑️ 完整管道清理完成: {total_cleaned['files']} 檔案, {total_cleaned['directories']} 目錄")
        
        return total_cleaned
    
    def cleanup_single_stage(self, stage_number: int) -> Dict[str, int]:
        """
        方案二：單一階段清理
        只清理指定階段的相關檔案
        """
        self.logger.info(f"🗑️ 執行階段 {stage_number} 清理（方案二）")
        
        cleaned = self._cleanup_stage_files(stage_number, include_validation=True)
        
        self.logger.info(f"🗑️ 階段 {stage_number} 清理完成: {cleaned['files']} 檔案, {cleaned['directories']} 目錄")
        
        return cleaned
    
    def auto_cleanup(self, current_stage: Optional[int] = None) -> Dict[str, int]:
        """
        自動清理 - 根據執行模式選擇清理策略
        
        Args:
            current_stage: 當前執行的階段號碼（用於單一階段模式）
        """
        mode = self.detect_execution_mode()
        
        if mode == "full_pipeline":
            return self.cleanup_full_pipeline()
        else:
            if current_stage is None:
                # 嘗試從調用堆疊推斷階段號碼
                current_stage = self._infer_current_stage()
            
            if current_stage:
                return self.cleanup_single_stage(current_stage)
            else:
                self.logger.warning("⚠️ 單一階段模式但無法確定階段號碼，跳過清理")
                return {"files": 0, "directories": 0}
    
    def _cleanup_stage_files(self, stage_number: int, include_validation: bool = True) -> Dict[str, int]:
        """清理指定階段的檔案"""
        if stage_number not in self.STAGE_CLEANUP_TARGETS:
            self.logger.warning(f"⚠️ 階段 {stage_number} 沒有定義清理目標")
            return {"files": 0, "directories": 0}
        
        target = self.STAGE_CLEANUP_TARGETS[stage_number]
        cleaned_files = 0
        cleaned_dirs = 0
        
        # 清理輸出檔案
        for file_path in target.output_files:
            if self._remove_file(file_path):
                cleaned_files += 1
        
        # 清理驗證檔案
        if include_validation:
            if self._remove_file(target.validation_file):
                cleaned_files += 1
        
        # 清理目錄
        if target.directories:
            for dir_path in target.directories:
                if self._remove_directory(dir_path):
                    cleaned_dirs += 1
        
        return {"files": cleaned_files, "directories": cleaned_dirs}
    
    def _remove_file(self, file_path: str) -> bool:
        """移除檔案"""
        try:
            path = Path(file_path)
            if path.exists():
                file_size_mb = path.stat().st_size / (1024 * 1024)
                path.unlink()
                self.logger.info(f"  ✅ 已刪除: {file_path} ({file_size_mb:.1f} MB)")
                return True
        except Exception as e:
            self.logger.warning(f"  ⚠️ 刪除失敗 {file_path}: {e}")
        return False
    
    def _remove_directory(self, dir_path: str) -> bool:
        """移除目錄"""
        try:
            import shutil
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                file_count = len(list(path.rglob("*")))
                if file_count > 0:
                    shutil.rmtree(path)
                    self.logger.info(f"  🗂️ 已移除目錄: {dir_path} ({file_count} 個檔案)")
                    return True
        except Exception as e:
            self.logger.warning(f"  ⚠️ 目錄移除失敗 {dir_path}: {e}")
        return False
    
    def _infer_current_stage(self) -> Optional[int]:
        """從調用堆疊推斷當前階段"""
        try:
            frame_info = inspect.stack()
            
            for frame in frame_info:
                filename = frame.filename
                
                # 根據檔案名推斷階段
                if 'orbital_calculation' in filename:
                    return 1
                elif 'visibility_filter' in filename or 'satellite_filter' in filename:
                    return 2
                elif 'signal_analysis' in filename:
                    return 3
                elif 'timeseries_preprocessing' in filename:
                    return 4
                elif 'data_integration' in filename:
                    return 5
                elif 'dynamic_pool' in filename:
                    return 6
                    
        except Exception as e:
            self.logger.warning(f"階段推斷失敗: {e}")
            
        return None

# 全局實例
_cleanup_manager = None

def get_cleanup_manager() -> UnifiedCleanupManager:
    """獲取統一清理管理器實例"""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = UnifiedCleanupManager()
    return _cleanup_manager

# 便捷函數
def auto_cleanup(current_stage: Optional[int] = None) -> Dict[str, int]:
    """自動清理便捷函數"""
    return get_cleanup_manager().auto_cleanup(current_stage)

def cleanup_all_stages() -> Dict[str, int]:
    """清理所有階段便捷函數"""
    return get_cleanup_manager().cleanup_full_pipeline()

def cleanup_stage(stage_number: int) -> Dict[str, int]:
    """清理單一階段便捷函數"""
    return get_cleanup_manager().cleanup_single_stage(stage_number)