"""
Base Stage Processor - 基礎階段處理器

提供所有階段處理器的統一基類，包含：
- 標準化處理接口
- 統一配置管理
- 錯誤處理機制
- 日誌管理
- 性能監控
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseStageProcessor(ABC):
    """
    基礎階段處理器抽象類
    
    所有階段處理器都應該繼承此類，提供統一的處理接口。
    """
    
    def __init__(self, stage_name: str, config: Dict[str, Any] = None):
        """
        初始化基礎處理器
        
        Args:
            stage_name: 階段名稱
            config: 配置字典
        """
        self.stage_name = stage_name
        self.config = config or {}
        
        # 處理統計
        self.stats = {
            "stage_name": stage_name,
            "start_time": None,
            "end_time": None,
            "duration": 0.0,
            "success": False,
            "error_message": None
        }
        
        logger.info(f"初始化 {stage_name} 處理器")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        執行處理邏輯 (抽象方法)
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        pass
    
    def execute_with_monitoring(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        執行帶監控的處理
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果，包含統計信息
        """
        self.stats["start_time"] = datetime.now()
        
        try:
            logger.info(f"開始執行 {self.stage_name}")
            
            result = self.process(input_data)
            
            self.stats["success"] = True
            logger.info(f"成功完成 {self.stage_name}")
            
            return result
            
        except Exception as e:
            self.stats["success"] = False
            self.stats["error_message"] = str(e)
            logger.error(f"執行 {self.stage_name} 失敗: {e}")
            raise
            
        finally:
            self.stats["end_time"] = datetime.now()
            if self.stats["start_time"]:
                self.stats["duration"] = (
                    self.stats["end_time"] - self.stats["start_time"]
                ).total_seconds()
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取處理統計"""
        return self.stats.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """獲取配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置"""
        self.config.update(new_config)
        logger.info(f"更新 {self.stage_name} 配置")
