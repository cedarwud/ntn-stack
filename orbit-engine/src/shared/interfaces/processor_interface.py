"""
處理器接口定義

整合來源：
- shared/core_modules/stage_interface.py (階段接口)
- shared/base_processor.py (基礎處理器)
- 各Stage的處理器接口

定義統一的處理器接口規範
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import logging


class ProcessingStatus(Enum):
    """處理狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    VALIDATION_FAILED = "validation_failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingMetrics:
    """處理指標"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    input_records: int = 0
    output_records: int = 0
    processed_records: int = 0
    error_count: int = 0
    success_rate: float = 0.0
    throughput_per_second: float = 0.0
    memory_usage_mb: float = 0.0


@dataclass
class ProcessingResult:
    """處理結果"""
    status: ProcessingStatus
    data: Optional[Dict[str, Any]] = None
    metrics: Optional[ProcessingMetrics] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_successful(self) -> bool:
        """判斷是否處理成功"""
        return self.status in [ProcessingStatus.SUCCESS, ProcessingStatus.COMPLETED] and not self.errors

    def has_warnings(self) -> bool:
        """判斷是否有警告"""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'status': self.status.value,
            'data': self.data,
            'metrics': self.metrics.__dict__ if self.metrics else None,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


class BaseProcessor(ABC):
    """基礎處理器接口"""

    def __init__(self, processor_name: str, config: Optional[Dict[str, Any]] = None):
        self.processor_name = processor_name
        self.config = config or {}
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.status = ProcessingStatus.PENDING
        self.metrics = ProcessingMetrics()

    @abstractmethod
    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """
        驗證輸入數據

        Args:
            input_data: 輸入數據

        Returns:
            驗證結果 {'valid': bool, 'errors': List[str], 'warnings': List[str]}
        """
        pass

    @abstractmethod
    def process(self, input_data: Any) -> ProcessingResult:
        """
        執行主要處理邏輯

        Args:
            input_data: 輸入數據

        Returns:
            處理結果
        """
        pass

    @abstractmethod
    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """
        驗證輸出數據

        Args:
            output_data: 輸出數據

        Returns:
            驗證結果 {'valid': bool, 'errors': List[str], 'warnings': List[str]}
        """
        pass

    def get_status(self) -> ProcessingStatus:
        """獲取當前處理狀態"""
        return self.status

    def get_metrics(self) -> ProcessingMetrics:
        """獲取處理指標"""
        return self.metrics

    def get_config(self) -> Dict[str, Any]:
        """獲取配置"""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        更新配置

        Args:
            new_config: 新配置

        Returns:
            是否更新成功
        """
        try:
            self.config.update(new_config)
            self.logger.info(f"配置已更新: {self.processor_name}")
            return True
        except Exception as e:
            self.logger.error(f"配置更新失敗: {e}")
            return False

    def _start_processing(self):
        """開始處理（內部方法）"""
        self.status = ProcessingStatus.RUNNING
        self.metrics.start_time = datetime.now(timezone.utc)
        self.logger.info(f"開始處理: {self.processor_name}")

    def _end_processing(self, status: ProcessingStatus):
        """結束處理（內部方法）"""
        self.status = status
        self.metrics.end_time = datetime.now(timezone.utc)

        if self.metrics.start_time:
            duration = self.metrics.end_time - self.metrics.start_time
            self.metrics.duration_seconds = duration.total_seconds()

        # 計算成功率
        if self.metrics.processed_records > 0:
            success_count = self.metrics.processed_records - self.metrics.error_count
            self.metrics.success_rate = success_count / self.metrics.processed_records

        # 計算吞吐量
        if self.metrics.duration_seconds > 0:
            self.metrics.throughput_per_second = self.metrics.processed_records / self.metrics.duration_seconds

        self.logger.info(f"處理完成: {self.processor_name}, 狀態: {status.value}, "
                        f"耗時: {self.metrics.duration_seconds:.2f}秒")


class StageProcessor(BaseProcessor):
    """階段處理器接口"""

    def __init__(self, stage_number: int, stage_name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(f"Stage{stage_number}_{stage_name}", config)
        self.stage_number = stage_number
        self.stage_name = stage_name

    @abstractmethod
    def execute(self, input_data: Optional[Any] = None) -> ProcessingResult:
        """
        執行階段處理（兼容現有接口）

        Args:
            input_data: 輸入數據

        Returns:
            處理結果
        """
        pass

    def get_stage_info(self) -> Dict[str, Any]:
        """獲取階段信息"""
        return {
            'stage_number': self.stage_number,
            'stage_name': self.stage_name,
            'processor_name': self.processor_name,
            'status': self.status.value,
            'config': self.config
        }


class DataProcessor(BaseProcessor):
    """數據處理器接口"""

    @abstractmethod
    def load_data(self, source: Any) -> Any:
        """
        載入數據

        Args:
            source: 數據源

        Returns:
            載入的數據
        """
        pass

    @abstractmethod
    def transform_data(self, data: Any) -> Any:
        """
        轉換數據

        Args:
            data: 原始數據

        Returns:
            轉換後的數據
        """
        pass

    @abstractmethod
    def save_data(self, data: Any, destination: Any) -> bool:
        """
        保存數據

        Args:
            data: 要保存的數據
            destination: 目標位置

        Returns:
            是否保存成功
        """
        pass


class AnalysisProcessor(BaseProcessor):
    """分析處理器接口"""

    @abstractmethod
    def analyze(self, data: Any) -> Dict[str, Any]:
        """
        執行分析

        Args:
            data: 分析數據

        Returns:
            分析結果
        """
        pass

    @abstractmethod
    def generate_report(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成報告

        Args:
            analysis_result: 分析結果

        Returns:
            報告數據
        """
        pass


class PredictionProcessor(BaseProcessor):
    """預測處理器接口"""

    @abstractmethod
    def predict(self, input_data: Any) -> Dict[str, Any]:
        """
        執行預測

        Args:
            input_data: 輸入數據

        Returns:
            預測結果
        """
        pass

    @abstractmethod
    def evaluate_prediction(self, prediction: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估預測結果

        Args:
            prediction: 預測結果
            actual: 實際結果

        Returns:
            評估結果
        """
        pass


class ValidationProcessor(BaseProcessor):
    """驗證處理器接口"""

    @abstractmethod
    def validate(self, data: Any, rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        執行驗證

        Args:
            data: 要驗證的數據
            rules: 驗證規則

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        獲取驗證規則

        Returns:
            驗證規則
        """
        pass


class MonitoringProcessor(BaseProcessor):
    """監控處理器接口"""

    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """
        收集監控指標

        Returns:
            監控指標
        """
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """
        健康檢查

        Returns:
            健康狀態
        """
        pass

    @abstractmethod
    def generate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成告警

        Args:
            metrics: 監控指標

        Returns:
            告警列表
        """
        pass


# 便捷函數
def create_processing_result(status: ProcessingStatus, data: Optional[Dict[str, Any]] = None,
                           errors: Optional[List[str]] = None,
                           warnings: Optional[List[str]] = None,
                           message: Optional[str] = None) -> ProcessingResult:
    """便捷函數：創建處理結果"""
    result = ProcessingResult(
        status=status,
        data=data,
        errors=errors or [],
        warnings=warnings or []
    )
    if message:
        result.metadata['message'] = message
    return result


def create_success_result(data: Dict[str, Any]) -> ProcessingResult:
    """便捷函數：創建成功結果"""
    return create_processing_result(ProcessingStatus.SUCCESS, data)


def create_error_result(errors: List[str]) -> ProcessingResult:
    """便捷函數：創建錯誤結果"""
    return create_processing_result(ProcessingStatus.FAILED, errors=errors)