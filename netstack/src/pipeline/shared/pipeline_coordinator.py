"""
管道協調器 - 統一管理所有階段的執行
"""

from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import json
from datetime import datetime, timezone

class PipelineCoordinator:
    """管道執行協調器"""
    
    def __init__(self):
        self.logger = logging.getLogger("PipelineCoordinator")
        self.stages_registry = {}
        self._load_stages_registry()
    
    def _load_stages_registry(self):
        """載入階段註冊表"""
        from pipeline.stages.stage1_orbital_calculation.stage1_processor import Stage1Processor
        from pipeline.stages.stage2_visibility_filter.stage2_processor import Stage2Processor
        from pipeline.stages.stage3_timeseries_preprocessing.stage3_processor import Stage3Processor
        from pipeline.stages.stage4_signal_analysis.stage4_processor import Stage4Processor
        from pipeline.stages.stage5_data_integration.stage5_processor import Stage5Processor
        from pipeline.stages.stage6_dynamic_planning.stage6_processor import Stage6Processor
        
        self.stages_registry = {
            1: Stage1Processor,  # ✅ Stage1Processor - 已實施
            2: Stage2Processor,  # ✅ Stage2Processor - 已實施
            3: Stage3Processor,  # ✅ Stage3Processor - 已實施
            4: Stage4Processor,  # ✅ Stage4Processor - 已實施
            5: Stage5Processor,  # ✅ Stage5Processor - 已實施
            6: Stage6Processor,  # ✅ Stage6Processor - 已實施
        }
        
        self.logger.info("✅ Stage 1-6 處理器已註冊到管道協調器")
    
    def register_stage(self, stage_number: int, processor_class):
        """註冊階段處理器"""
        self.stages_registry[stage_number] = processor_class
        self.logger.info(f"已註冊 Stage {stage_number}: {processor_class.__name__}")
    
    def execute_single_stage(self, stage_number: int, input_data: Any = None, debug_mode: bool = False) -> Dict[str, Any]:
        """
        執行單一階段
        
        Args:
            stage_number: 階段編號 (1-6)
            input_data: 輸入數據，None時自動從前一階段載入
            debug_mode: 是否啟用除錯模式
            
        Returns:
            處理結果
            
        Raises:
            ValueError: 階段編號無效或處理器未註冊
            RuntimeError: 執行過程中發生錯誤
        """
        if stage_number not in range(1, 7):
            raise ValueError(f"無效的階段編號: {stage_number}")
        
        processor_class = self.stages_registry.get(stage_number)
        if processor_class is None:
            raise ValueError(f"Stage {stage_number} 處理器尚未實施")
        
        self.logger.info(f"開始執行單階段除錯: Stage {stage_number}")
        
        try:
            # 創建處理器實例
            config = {"debug_mode": debug_mode} if debug_mode else {}
            processor = processor_class(config=config)
            
            # 設置除錯日誌等級
            if debug_mode:
                logging.getLogger(f"stage{stage_number}_{processor.stage_name}").setLevel(logging.DEBUG)
            
            # 執行處理
            result = processor.execute(input_data)
            
            self.logger.info(f"Stage {stage_number} 執行完成")
            return result
            
        except Exception as e:
            self.logger.error(f"Stage {stage_number} 執行失敗: {e}")
            if debug_mode:
                import traceback
                self.logger.debug(f"完整錯誤追蹤:\n{traceback.format_exc()}")
            raise RuntimeError(f"Stage {stage_number} 執行失敗") from e
    
    def execute_pipeline_range(self, start_stage: int, end_stage: int, debug_mode: bool = False) -> Dict[int, Dict[str, Any]]:
        """
        執行階段範圍
        
        Args:
            start_stage: 開始階段
            end_stage: 結束階段
            debug_mode: 除錯模式
            
        Returns:
            各階段執行結果
        """
        results = {}
        previous_result = None
        
        for stage_num in range(start_stage, end_stage + 1):
            self.logger.info(f"執行階段範圍: Stage {stage_num}")
            
            # 使用前一階段的輸出作為輸入
            input_data = previous_result.get('data') if previous_result else None
            
            # 執行當前階段
            stage_result = self.execute_single_stage(stage_num, input_data, debug_mode)
            results[stage_num] = stage_result
            previous_result = stage_result
        
        return results
    
    def execute_full_pipeline(self, debug_mode: bool = False) -> Dict[int, Dict[str, Any]]:
        """
        執行完整的六階段管道
        
        Args:
            debug_mode: 除錯模式
            
        Returns:
            所有階段執行結果
        """
        return self.execute_pipeline_range(1, 6, debug_mode)
    
    def get_stage_dependencies(self, stage_number: int) -> List[int]:
        """
        獲取階段依賴關係
        
        Args:
            stage_number: 階段編號
            
        Returns:
            依賴的階段列表
        """
        # 簡化的線性依賴關係
        if stage_number == 1:
            return []
        else:
            return [stage_number - 1]
    
    def validate_pipeline_state(self) -> Dict[str, Any]:
        """
        驗證管道狀態
        
        Returns:
            驗證結果
        """
        validation_result = {
            "valid": True,
            "registered_stages": [],
            "missing_stages": [],
            "data_integrity": True
        }
        
        # 檢查註冊的階段
        for stage_num in range(1, 7):
            if self.stages_registry[stage_num] is not None:
                validation_result["registered_stages"].append(stage_num)
            else:
                validation_result["missing_stages"].append(stage_num)
        
        # 檢查是否有缺少的階段
        if validation_result["missing_stages"]:
            validation_result["valid"] = False
        
        return validation_result