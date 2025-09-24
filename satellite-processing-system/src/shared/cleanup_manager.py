"""
統一清理管理器 - 六階段處理器的智能清理系統

提供完整管道清理和單一階段清理兩種模式
"""

import os
import json
import inspect
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CleanupTarget:
    """清理目標配置"""
    stage: int
    output_files: List[str]
    validation_file: str
    directories: List[str] = None

class UnifiedCleanupManager:
    """統一清理管理器 - 智能雙模式清理"""

    def __init__(self):
        self.logger = logger

        # 定義所有階段的清理目標（基於實際處理器分析）
        self.STAGE_CLEANUP_TARGETS = {
            # 階段一：TLE載入與SGP4軌道計算
            1: CleanupTarget(
                stage=1,
                output_files=[],  # 統一清理整個目錄
                validation_file="data/validation_snapshots/stage1_validation.json",
                directories=[
                    "data/outputs/stage1"  # 只清理標準輸出目錄
                ]
            ),

            # 階段二：智能衛星篩選
            2: CleanupTarget(
                stage=2,
                output_files=[],  # 統一清理整個目錄
                validation_file="data/validation_snapshots/stage2_validation.json",
                directories=[
                    "data/outputs/stage2"  # 只清理標準輸出目錄
                ]
            ),

            # 階段三：信號品質分析
            3: CleanupTarget(
                stage=3,
                output_files=[],  # 統一清理整個目錄
                validation_file="data/validation_snapshots/stage3_validation.json",
                directories=[
                    "data/outputs/stage3"  # 只清理標準輸出目錄
                ]
            ),

            # 階段四：時間序列預處理
            4: CleanupTarget(
                stage=4,
                output_files=[],  # 統一清理整個目錄
                validation_file="data/validation_snapshots/stage4_validation.json",
                directories=[
                    "data/outputs/stage4"  # 只清理標準輸出目錄
                ]
            ),

            # 階段五：資料整合
            5: CleanupTarget(
                stage=5,
                output_files=[],  # 統一清理整個目錄
                validation_file="data/validation_snapshots/stage5_validation.json",
                directories=[
                    "data/outputs/stage5"  # 只清理標準輸出目錄
                ]
            ),

            # 階段六：動態池規劃
            6: CleanupTarget(
                stage=6,
                output_files=[],  # 統一清理整個目錄
                validation_file="data/validation_snapshots/stage6_validation.json",
                directories=[
                    "data/outputs/stage6"  # 只清理標準輸出目錄
                ]
            )
        }

    def detect_execution_mode(self) -> Literal["full_pipeline", "single_stage"]:
        """
        智能檢測執行模式

        Returns:
            "full_pipeline": 完整管道執行
            "single_stage": 單一階段測試
        """

        # 方法1: 檢查環境變數
        pipeline_mode = os.getenv('PIPELINE_MODE', '').lower()
        if pipeline_mode == 'full':
            self.logger.info("🔍 檢測到環境變數: PIPELINE_MODE=full")
            return "full_pipeline"
        elif pipeline_mode == 'single':
            self.logger.info("🔍 檢測到環境變數: PIPELINE_MODE=single")
            return "single_stage"

        # 方法2: 檢查調用堆棧 - 改進邏輯
        try:
            # 獲取調用堆棧
            frame_info = inspect.stack()

            # 檢查是否從管道腳本調用，且是否為單階段執行
            pipeline_script_detected = False
            for frame in frame_info:
                filename = frame.filename
                if 'run_six_stages' in filename or 'pipeline' in filename:
                    pipeline_script_detected = True
                    
                    # 檢查sys.argv是否包含--stage參數，表示單階段執行
                    import sys
                    args = sys.argv
                    if '--stage' in args:
                        stage_index = args.index('--stage')
                        if stage_index + 1 < len(args):
                            stage_num = args[stage_index + 1]
                            self.logger.info(f"🔍 檢測到管道腳本單階段執行: stage {stage_num}")
                            return "single_stage"  # 單階段執行，使用單階段清理策略
                    
                    # 沒有--stage參數，是完整管道執行
                    self.logger.info(f"🔍 檢測到管道腳本完整執行: {Path(filename).name}")
                    return "full_pipeline"
                    
        except Exception as e:
            self.logger.warning(f"調用堆棧檢測失敗: {e}")

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


    def cleanup_from_stage(self, start_stage: int) -> Dict[str, int]:
        """
        智能分階段清理
        清理從指定階段開始的所有後續階段，保留前面階段作為輸入依賴

        Args:
            start_stage: 開始清理的階段號碼（1-6）

        Returns:
            清理統計結果
        """
        if start_stage < 1 or start_stage > 6:
            self.logger.warning(f"⚠️ 無效的階段號碼: {start_stage}，應為 1-6")
            return {"files": 0, "directories": 0}

        self.logger.info(f"🗑️ 智能清理：從階段 {start_stage} 開始清理（保留階段 1-{start_stage-1} 作為輸入）")
        self.logger.info("=" * 60)

        total_cleaned = {"files": 0, "directories": 0}

        # 清理從指定階段開始的所有後續階段
        for stage_num in range(start_stage, 7):
            stage_cleaned = self._cleanup_stage_files(stage_num, include_validation=True)
            total_cleaned["files"] += stage_cleaned["files"]
            total_cleaned["directories"] += stage_cleaned["directories"]

            # 記錄每階段清理結果
            if stage_cleaned["files"] > 0 or stage_cleaned["directories"] > 0:
                self.logger.info(f"  📂 階段 {stage_num}: {stage_cleaned['files']} 檔案, {stage_cleaned['directories']} 目錄")

        # 顯示保留的階段
        if start_stage > 1:
            preserved_stages = list(range(1, start_stage))
            self.logger.info(f"🛡️ 已保留階段 {preserved_stages} 的輸出作為後續處理的輸入依賴")

        self.logger.info("=" * 60)
        self.logger.info(f"🗑️ 智能清理完成: {total_cleaned['files']} 檔案, {total_cleaned['directories']} 目錄")

        return total_cleaned

    def auto_cleanup(self, current_stage: Optional[int] = None) -> Dict[str, int]:
        """
        智能自動清理 - 根據執行模式和階段選擇最適合的清理策略

        Args:
            current_stage: 當前執行的階段號碼

        Returns:
            清理統計結果
        """
        mode = self.detect_execution_mode()

        if mode == "full_pipeline":
            # 完整管道模式：在第一階段執行完整清理
            if current_stage == 1:
                self.logger.info("🔧 完整管道模式：在階段一執行完整清理")
                return self.cleanup_full_pipeline()
            else:
                self.logger.info(f"🔧 完整管道模式：階段 {current_stage} 跳過清理，保護數據流")
                return {"files": 0, "directories": 0}
        else:
            # 單一階段模式：使用智能清理策略
            if current_stage is None:
                # 嘗試從調用堆棧推斷階段號碼
                current_stage = self._infer_current_stage()

            if current_stage:
                self.logger.info(f"🧠 單一階段模式：使用智能清理策略（階段 {current_stage}）")
                return self.cleanup_from_stage(current_stage)
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

        # 清理驗證檔案
        if include_validation:
            if self._remove_file(target.validation_file):
                cleaned_files += 1

        # 清理目錄 - 優先嘗試直接刪除整個目錄
        if target.directories:
            for dir_path in target.directories:
                if self._remove_directory(dir_path):
                    cleaned_dirs += 1
                else:
                    # 如果無法刪除目錄，則清理目錄內檔案後刪除空目錄
                    cleaned_count = self._cleanup_directory_contents(dir_path)
                    cleaned_files += cleaned_count
                    # 嘗試刪除空目錄
                    if self._remove_empty_directory(dir_path):
                        cleaned_dirs += 1

        return {"files": cleaned_files, "directories": cleaned_dirs}

    def _cleanup_directory_contents(self, dir_path: str) -> int:
        """清理目錄內的所有檔案"""
        cleaned_count = 0
        try:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        try:
                            file_size_mb = file_path.stat().st_size / (1024 * 1024)
                            file_path.unlink()
                            self.logger.info(f"  ✅ 已刪除檔案: {file_path} ({file_size_mb:.1f} MB)")
                            cleaned_count += 1
                        except Exception as e:
                            self.logger.warning(f"  ⚠️ 檔案刪除失敗 {file_path}: {e}")
        except Exception as e:
            self.logger.warning(f"  ⚠️ 清理目錄內容失敗 {dir_path}: {e}")

        return cleaned_count

    def _remove_empty_directory(self, dir_path: str) -> bool:
        """移除空目錄（遞迴移除所有空的子目錄）"""
        try:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                # 遞迴處理所有子目錄
                for subdir in sorted(path.rglob('*'), key=lambda x: len(x.parts), reverse=True):
                    if subdir.is_dir() and subdir != path:
                        try:
                            if not any(subdir.iterdir()):
                                subdir.rmdir()
                                self.logger.info(f"  🗂️ 已移除空子目錄: {subdir}")
                        except Exception as e:
                            self.logger.warning(f"  ⚠️ 子目錄移除失敗 {subdir}: {e}")

                # 檢查主目錄是否為空
                if not any(path.iterdir()):
                    path.rmdir()
                    self.logger.info(f"  🗂️ 已移除空目錄: {dir_path}")
                    return True
                else:
                    self.logger.info(f"  📁 目錄非空，保留: {dir_path}")
        except Exception as e:
            self.logger.warning(f"  ⚠️ 空目錄移除失敗 {dir_path}: {e}")
        return False

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
        """移除目錄（包含空目錄）"""
        try:
            import shutil
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                file_count = len(list(path.rglob("*")))
                shutil.rmtree(path)
                if file_count > 0:
                    self.logger.info(f"  🗂️ 已移除目錄: {dir_path} ({file_count} 個檔案)")
                else:
                    self.logger.info(f"  🗂️ 已移除空目錄: {dir_path}")
                return True
        except Exception as e:
            self.logger.warning(f"  ⚠️ 目錄移除失敗 {dir_path}: {e}")
        return False

    def _infer_current_stage(self) -> Optional[int]:
        """從調用堆棧推斷當前階段"""
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


# 全域清理管理器單例
_cleanup_manager: Optional[UnifiedCleanupManager] = None

def get_cleanup_manager() -> UnifiedCleanupManager:
    """獲取全域清理管理器單例"""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = UnifiedCleanupManager()
    return _cleanup_manager

def auto_cleanup(current_stage: Optional[int] = None) -> Dict[str, int]:
    """便捷的自動清理功能"""
    manager = get_cleanup_manager()
    return manager.auto_cleanup(current_stage)

def cleanup_all_stages() -> Dict[str, int]:
    """清理所有階段的輸出檔案"""
    manager = get_cleanup_manager()
    return manager.cleanup_full_pipeline()

def cleanup_from_stage(start_stage: int) -> Dict[str, int]:
    """從指定階段開始清理所有後續階段"""
    manager = get_cleanup_manager()
    return manager.cleanup_from_stage(start_stage)