#!/usr/bin/env python3
"""
標準階段介面定義 - 跨階段數據流規範

定義所有階段必須遵循的標準介面，確保：
1. 清晰的階段責任邊界
2. 標準化的數據輸入/輸出格式
3. 禁止跨階段直接文件讀取
4. 強制通過參數傳遞數據

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 架構修正專用
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class StageInterface(ABC):
    """
    所有階段處理器的標準介面

    強制架構原則：
    1. 每個階段都必須實現此介面
    2. 禁止直接讀取其他階段的輸出文件
    3. 所有數據必須通過 process() 方法的參數傳入
    4. 輸出格式必須標準化
    """

    def __init__(self, stage_number: int, stage_name: str, config: Optional[Dict] = None):
        """初始化階段處理器"""
        self.stage_number = stage_number
        self.stage_name = stage_name
        self.config = config or {}
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        # 處理統計
        self.processing_stats = {
            'processing_start_time': None,
            'processing_end_time': None,
            'processing_duration': 0.0,
            'input_records': 0,
            'output_records': 0,
            'error_count': 0
        }

        self.logger.info(f"✅ 階段 {stage_number} ({stage_name}) 處理器初始化")

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理數據 - 所有階段的核心方法

        Args:
            input_data: 來自前階段的標準化數據，不得為空

        Returns:
            Dict[str, Any]: 標準化的輸出數據

        Raises:
            ValueError: 當 input_data 為空或格式不正確時
            RuntimeError: 當處理過程中出現錯誤時
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        驗證輸入數據格式

        Args:
            input_data: 待驗證的輸入數據

        Returns:
            bool: 驗證是否通過
        """
        pass

    @abstractmethod
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證輸出數據格式

        Args:
            output_data: 待驗證的輸出數據

        Returns:
            bool: 驗證是否通過
        """
        pass

    def get_stage_info(self) -> Dict[str, Any]:
        """獲取階段基本信息"""
        return {
            'stage_number': self.stage_number,
            'stage_name': self.stage_name,
            'processor_class': self.__class__.__name__,
            'processing_stats': self.processing_stats.copy()
        }

    def create_standard_output(self, data: Dict[str, Any],
                             additional_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        創建標準化輸出格式

        Args:
            data: 處理結果數據
            additional_metadata: 額外的元數據

        Returns:
            標準化的輸出格式
        """

        processing_time = self.processing_stats.get('processing_duration', 0.0)

        # 標準元數據
        metadata = {
            'stage_number': self.stage_number,
            'stage_name': self.stage_name,
            'processor_version': f"{self.__class__.__name__}_v1.0",
            'processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'processing_duration_seconds': processing_time,
            'input_records': self.processing_stats.get('input_records', 0),
            'output_records': self.processing_stats.get('output_records', 0),
            'data_format_version': '1.0.0',
            'academic_compliance': 'Grade_A_standardized_interface'
        }

        # 添加額外元數據
        if additional_metadata:
            metadata.update(additional_metadata)

        return {
            'data': data,
            'metadata': metadata,
            'statistics': self.processing_stats.copy(),
            'success': True,
            'status': 'completed'
        }

    def create_error_output(self, error_message: str,
                          error_details: Optional[Dict] = None) -> Dict[str, Any]:
        """
        創建標準化錯誤輸出

        Args:
            error_message: 錯誤訊息
            error_details: 錯誤詳情

        Returns:
            標準化的錯誤輸出格式
        """

        return {
            'data': {},
            'metadata': {
                'stage_number': self.stage_number,
                'stage_name': self.stage_name,
                'processor_version': f"{self.__class__.__name__}_v1.0",
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'error',
                'error_message': error_message,
                'error_details': error_details or {}
            },
            'statistics': self.processing_stats.copy(),
            'success': False,
            'status': 'error'
        }

    def _validate_input_not_empty(self, input_data: Dict[str, Any]) -> None:
        """
        驗證輸入數據不為空 - 架構強制要求

        Args:
            input_data: 輸入數據

        Raises:
            ValueError: 當輸入數據為空時
        """
        if not input_data:
            raise ValueError(
                f"❌ 架構違規：階段 {self.stage_number} ({self.stage_name}) "
                f"不得接收空的輸入數據！\n"
                f"   所有階段都必須通過標準化接口接收前階段的數據。\n"
                f"   禁止直接讀取文件或使用空輸入。"
            )

    def _update_processing_stats(self, start_time: datetime, end_time: datetime,
                               input_count: int = 0, output_count: int = 0) -> None:
        """更新處理統計信息"""
        duration = (end_time - start_time).total_seconds()

        self.processing_stats.update({
            'processing_start_time': start_time,
            'processing_end_time': end_time,
            'processing_duration': duration,
            'input_records': input_count,
            'output_records': output_count
        })

class ArchitecturalViolationError(Exception):
    """架構違規錯誤 - 當階段違反設計原則時拋出"""
    pass