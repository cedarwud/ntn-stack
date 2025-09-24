"""
服務接口定義

定義系統中各種服務的標準接口，包括：
- 監控服務
- 預測服務
- 驗證服務
- 計算服務
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging


class ServiceStatus(Enum):
    """服務狀態枚舉"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ServiceType(Enum):
    """服務類型枚舉"""
    MONITORING = "monitoring"
    PREDICTION = "prediction"
    VALIDATION = "validation"
    CALCULATION = "calculation"
    ANALYSIS = "analysis"
    NOTIFICATION = "notification"


@dataclass
class ServiceMetrics:
    """服務指標"""
    uptime_seconds: float = 0.0
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    average_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def get_success_rate(self) -> float:
        """獲取成功率"""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count

    def get_error_rate(self) -> float:
        """獲取錯誤率"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


@dataclass
class ServiceConfig:
    """服務配置"""
    service_name: str
    service_type: ServiceType
    enabled: bool = True
    auto_start: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: float = 30.0
    health_check_interval_seconds: float = 60.0
    log_level: str = "INFO"
    custom_config: Dict[str, Any] = field(default_factory=dict)


class BaseService(ABC):
    """基礎服務接口"""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.status = ServiceStatus.STOPPED
        self.metrics = ServiceMetrics()
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None

    @abstractmethod
    def start(self) -> bool:
        """
        啟動服務

        Returns:
            是否啟動成功
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        停止服務

        Returns:
            是否停止成功
        """
        pass

    @abstractmethod
    def restart(self) -> bool:
        """
        重啟服務

        Returns:
            是否重啟成功
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查

        Returns:
            健康狀態信息
        """
        pass

    def get_status(self) -> ServiceStatus:
        """獲取服務狀態"""
        return self.status

    def get_metrics(self) -> ServiceMetrics:
        """獲取服務指標"""
        if self.start_time:
            current_time = datetime.now()
            self.metrics.uptime_seconds = (current_time - self.start_time).total_seconds()
        return self.metrics

    def get_config(self) -> ServiceConfig:
        """獲取服務配置"""
        return self.config

    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        更新配置

        Args:
            new_config: 新配置

        Returns:
            是否更新成功
        """
        try:
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    self.config.custom_config[key] = value
            return True
        except Exception as e:
            self.logger.error(f"配置更新失敗: {e}")
            return False

    def _set_status(self, status: ServiceStatus):
        """設置服務狀態（內部方法）"""
        old_status = self.status
        self.status = status
        self.logger.info(f"服務狀態變更: {old_status.value} -> {status.value}")

        if status == ServiceStatus.RUNNING and not self.start_time:
            self.start_time = datetime.now()
        elif status == ServiceStatus.STOPPED:
            self.stop_time = datetime.now()

    def _record_request(self, success: bool, response_time_ms: float = 0.0, error: Optional[str] = None):
        """記錄請求（內部方法）"""
        self.metrics.request_count += 1

        if success:
            self.metrics.success_count += 1
        else:
            self.metrics.error_count += 1
            if error:
                self.metrics.last_error = error
                self.metrics.last_error_time = datetime.now()

        # 更新平均響應時間
        if response_time_ms > 0:
            current_avg = self.metrics.average_response_time_ms
            count = self.metrics.request_count
            self.metrics.average_response_time_ms = (current_avg * (count - 1) + response_time_ms) / count


class MonitoringService(BaseService):
    """監控服務接口"""

    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """
        收集監控指標

        Returns:
            監控指標
        """
        pass

    @abstractmethod
    def register_metric(self, metric_name: str, metric_type: str, description: str) -> bool:
        """
        註冊監控指標

        Args:
            metric_name: 指標名稱
            metric_type: 指標類型
            description: 指標描述

        Returns:
            是否註冊成功
        """
        pass

    @abstractmethod
    def update_metric(self, metric_name: str, value: Union[int, float]) -> bool:
        """
        更新監控指標

        Args:
            metric_name: 指標名稱
            value: 指標值

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    def get_metric_history(self, metric_name: str, time_window: timedelta) -> List[Dict[str, Any]]:
        """
        獲取指標歷史

        Args:
            metric_name: 指標名稱
            time_window: 時間窗口

        Returns:
            指標歷史數據
        """
        pass

    @abstractmethod
    def set_alert_threshold(self, metric_name: str, threshold_type: str, value: float) -> bool:
        """
        設置告警閾值

        Args:
            metric_name: 指標名稱
            threshold_type: 閾值類型 ('warning', 'critical')
            value: 閾值

        Returns:
            是否設置成功
        """
        pass


class PredictionService(BaseService):
    """預測服務接口"""

    @abstractmethod
    def predict(self, input_data: Any, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        執行預測

        Args:
            input_data: 輸入數據
            model_name: 模型名稱

        Returns:
            預測結果
        """
        pass

    @abstractmethod
    def train_model(self, training_data: Any, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        訓練模型

        Args:
            training_data: 訓練數據
            model_config: 模型配置

        Returns:
            訓練結果
        """
        pass

    @abstractmethod
    def evaluate_model(self, test_data: Any, model_name: str) -> Dict[str, Any]:
        """
        評估模型

        Args:
            test_data: 測試數據
            model_name: 模型名稱

        Returns:
            評估結果
        """
        pass

    @abstractmethod
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        獲取模型信息

        Args:
            model_name: 模型名稱

        Returns:
            模型信息
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """
        列出所有模型

        Returns:
            模型名稱列表
        """
        pass


class ValidationService(BaseService):
    """驗證服務接口"""

    @abstractmethod
    def validate_data(self, data: Any, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證數據

        Args:
            data: 要驗證的數據
            validation_rules: 驗證規則

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def register_validator(self, validator_name: str, validator_func: Callable) -> bool:
        """
        註冊驗證器

        Args:
            validator_name: 驗證器名稱
            validator_func: 驗證函數

        Returns:
            是否註冊成功
        """
        pass

    @abstractmethod
    def get_validation_rules(self, rule_set_name: str) -> Dict[str, Any]:
        """
        獲取驗證規則

        Args:
            rule_set_name: 規則集名稱

        Returns:
            驗證規則
        """
        pass

    @abstractmethod
    def update_validation_rules(self, rule_set_name: str, rules: Dict[str, Any]) -> bool:
        """
        更新驗證規則

        Args:
            rule_set_name: 規則集名稱
            rules: 新規則

        Returns:
            是否更新成功
        """
        pass


class CalculationService(BaseService):
    """計算服務接口"""

    @abstractmethod
    def calculate(self, calculation_type: str, input_data: Any, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        執行計算

        Args:
            calculation_type: 計算類型
            input_data: 輸入數據
            params: 計算參數

        Returns:
            計算結果
        """
        pass

    @abstractmethod
    def register_calculation(self, calculation_name: str, calculation_func: Callable) -> bool:
        """
        註冊計算方法

        Args:
            calculation_name: 計算方法名稱
            calculation_func: 計算函數

        Returns:
            是否註冊成功
        """
        pass

    @abstractmethod
    def get_supported_calculations(self) -> List[str]:
        """
        獲取支持的計算類型

        Returns:
            計算類型列表
        """
        pass

    @abstractmethod
    def batch_calculate(self, calculations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量計算

        Args:
            calculations: 計算請求列表

        Returns:
            計算結果列表
        """
        pass


class NotificationService(BaseService):
    """通知服務接口"""

    @abstractmethod
    def send_notification(self, message: str, recipients: List[str],
                         notification_type: str = "info", priority: str = "normal") -> bool:
        """
        發送通知

        Args:
            message: 通知消息
            recipients: 接收者列表
            notification_type: 通知類型
            priority: 優先級

        Returns:
            是否發送成功
        """
        pass

    @abstractmethod
    def register_channel(self, channel_name: str, channel_config: Dict[str, Any]) -> bool:
        """
        註冊通知通道

        Args:
            channel_name: 通道名稱
            channel_config: 通道配置

        Returns:
            是否註冊成功
        """
        pass

    @abstractmethod
    def subscribe(self, subscriber: str, channel: str, filters: Optional[Dict[str, Any]] = None) -> bool:
        """
        訂閱通知

        Args:
            subscriber: 訂閱者
            channel: 通道
            filters: 過濾條件

        Returns:
            是否訂閱成功
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscriber: str, channel: str) -> bool:
        """
        取消訂閱

        Args:
            subscriber: 訂閱者
            channel: 通道

        Returns:
            是否取消成功
        """
        pass


class ServiceRegistry(ABC):
    """服務註冊中心接口"""

    @abstractmethod
    def register_service(self, service: BaseService) -> bool:
        """
        註冊服務

        Args:
            service: 服務實例

        Returns:
            是否註冊成功
        """
        pass

    @abstractmethod
    def unregister_service(self, service_name: str) -> bool:
        """
        註銷服務

        Args:
            service_name: 服務名稱

        Returns:
            是否註銷成功
        """
        pass

    @abstractmethod
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        獲取服務

        Args:
            service_name: 服務名稱

        Returns:
            服務實例或None
        """
        pass

    @abstractmethod
    def list_services(self, service_type: Optional[ServiceType] = None) -> List[str]:
        """
        列出服務

        Args:
            service_type: 服務類型

        Returns:
            服務名稱列表
        """
        pass

    @abstractmethod
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        檢查所有服務健康狀態

        Returns:
            所有服務的健康狀態
        """
        pass


# 便捷函數
def create_service_config(service_name: str, service_type: ServiceType, **kwargs) -> ServiceConfig:
    """便捷函數：創建服務配置"""
    return ServiceConfig(
        service_name=service_name,
        service_type=service_type,
        **kwargs
    )


def create_health_check_result(healthy: bool, details: Optional[Dict[str, Any]] = None,
                             checks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """便捷函數：創建健康檢查結果"""
    return {
        'healthy': healthy,
        'timestamp': datetime.now().isoformat(),
        'details': details or {},
        'checks': checks or []
    }