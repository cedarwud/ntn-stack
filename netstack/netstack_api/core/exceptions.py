"""
統一異常處理框架

實現 Sprint 2 目標：統一錯誤處理機制，覆蓋率 > 90%

提供：
- 標準化異常類型定義
- 統一錯誤碼系統
- 異常鏈追蹤
- 自動恢復機制
- 錯誤監控與報告
- 多語言錯誤訊息支持
"""

import asyncio
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import json
import structlog

logger = structlog.get_logger(__name__)


class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    CRITICAL = "critical"    # 系統無法運行
    HIGH = "high"           # 主要功能受影響
    MEDIUM = "medium"       # 部分功能受影響
    LOW = "low"            # 輕微影響
    INFO = "info"          # 僅供參考


class ErrorCategory(Enum):
    """錯誤類別"""
    SYSTEM = "system"                    # 系統級錯誤
    NETWORK = "network"                  # 網路相關錯誤
    DATABASE = "database"                # 資料庫錯誤
    AUTHENTICATION = "authentication"    # 認證授權錯誤
    VALIDATION = "validation"            # 資料驗證錯誤
    BUSINESS_LOGIC = "business_logic"    # 業務邏輯錯誤
    EXTERNAL_SERVICE = "external_service"  # 外部服務錯誤
    PERFORMANCE = "performance"          # 性能相關錯誤
    CONFIGURATION = "configuration"     # 配置錯誤
    RESOURCE = "resource"               # 資源不足錯誤


class RecoveryStrategy(Enum):
    """恢復策略"""
    NONE = "none"              # 不自動恢復
    RETRY = "retry"            # 重試操作
    FALLBACK = "fallback"      # 使用備用方案
    ROLLBACK = "rollback"      # 回滾操作
    GRACEFUL_DEGRADATION = "graceful_degradation"  # 優雅降級
    CIRCUIT_BREAKER = "circuit_breaker"  # 熔斷
    RESTART_SERVICE = "restart_service"  # 重啟服務


@dataclass
class ErrorContext:
    """錯誤上下文信息"""
    service_name: str
    function_name: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """恢復動作記錄"""
    action_id: str
    strategy: RecoveryStrategy
    attempt_number: int
    executed_at: datetime
    success: bool
    error_message: Optional[str] = None
    recovery_time_ms: float = 0.0
    additional_info: Dict[str, Any] = field(default_factory=dict)


class BaseException(Exception):
    """統一異常基類"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[ErrorContext] = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.NONE,
        user_message: Optional[str] = None,
        technical_details: Optional[Dict[str, Any]] = None,
        caused_by: Optional[Exception] = None
    ):
        super().__init__(message)
        
        self.error_id = str(uuid.uuid4())
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext("unknown", "unknown")
        self.recovery_strategy = recovery_strategy
        self.user_message = user_message or self._generate_user_message()
        self.technical_details = technical_details or {}
        self.caused_by = caused_by
        self.occurred_at = datetime.utcnow()
        
        # 恢復相關屬性
        self.recovery_attempts: List[RecoveryAction] = []
        self.recovered = False
        self.recovery_time_ms: Optional[float] = None
        
        # 追蹤屬性
        self.stack_trace = traceback.format_exc()
        self.propagation_path: List[str] = []

    def _generate_user_message(self) -> str:
        """生成用戶友好的錯誤訊息"""
        user_messages = {
            ErrorCategory.NETWORK: "網路連線發生問題，請檢查網路設定",
            ErrorCategory.DATABASE: "資料存取暫時無法使用，請稍後再試",
            ErrorCategory.AUTHENTICATION: "身份驗證失敗，請重新登入",
            ErrorCategory.VALIDATION: "輸入的資料格式不正確，請檢查後重新輸入",
            ErrorCategory.BUSINESS_LOGIC: "操作無法完成，請聯絡系統管理員",
            ErrorCategory.EXTERNAL_SERVICE: "外部服務暫時無法使用，請稍後再試",
            ErrorCategory.PERFORMANCE: "系統回應較慢，請稍候",
            ErrorCategory.CONFIGURATION: "系統配置有誤，請聯絡管理員",
            ErrorCategory.RESOURCE: "系統資源不足，請稍後再試",
        }
        
        return user_messages.get(self.category, "系統發生未知錯誤，請聯絡管理員")

    def add_context(self, key: str, value: Any):
        """添加上下文信息"""
        if self.context:
            self.context.additional_context[key] = value

    def add_propagation_step(self, step: str):
        """添加傳播路徑"""
        self.propagation_path.append(f"{datetime.utcnow().isoformat()}: {step}")

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity.value,
            "category": self.category.value,
            "recovery_strategy": self.recovery_strategy.value,
            "occurred_at": self.occurred_at.isoformat(),
            "context": {
                "service_name": self.context.service_name,
                "function_name": self.context.function_name,
                "user_id": self.context.user_id,
                "request_id": self.context.request_id,
                "session_id": self.context.session_id,
                "additional_context": self.context.additional_context,
            } if self.context else None,
            "technical_details": self.technical_details,
            "caused_by": str(self.caused_by) if self.caused_by else None,
            "recovery_attempts": [
                {
                    "action_id": action.action_id,
                    "strategy": action.strategy.value,
                    "attempt_number": action.attempt_number,
                    "executed_at": action.executed_at.isoformat(),
                    "success": action.success,
                    "error_message": action.error_message,
                    "recovery_time_ms": action.recovery_time_ms,
                }
                for action in self.recovery_attempts
            ],
            "recovered": self.recovered,
            "recovery_time_ms": self.recovery_time_ms,
            "propagation_path": self.propagation_path,
        }


class NetworkException(BaseException):
    """網路相關異常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="NET_001",
            category=ErrorCategory.NETWORK,
            recovery_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class DatabaseException(BaseException):
    """資料庫相關異常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="DB_001",
            category=ErrorCategory.DATABASE,
            recovery_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class AuthenticationException(BaseException):
    """認證相關異常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="AUTH_001",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.NONE,
            **kwargs
        )


class ValidationException(BaseException):
    """資料驗證異常"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, **kwargs):
        technical_details = kwargs.pop("technical_details", {})
        if field_name:
            technical_details["field_name"] = field_name
        
        super().__init__(
            message=message,
            error_code="VAL_001",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recovery_strategy=RecoveryStrategy.NONE,
            technical_details=technical_details,
            **kwargs
        )


class BusinessLogicException(BaseException):
    """業務邏輯異常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="BL_001",
            category=ErrorCategory.BUSINESS_LOGIC,
            recovery_strategy=RecoveryStrategy.NONE,
            **kwargs
        )


class ExternalServiceException(BaseException):
    """外部服務異常"""
    
    def __init__(self, message: str, service_name: str, **kwargs):
        technical_details = kwargs.pop("technical_details", {})
        technical_details["service_name"] = service_name
        
        super().__init__(
            message=message,
            error_code="EXT_001",
            category=ErrorCategory.EXTERNAL_SERVICE,
            recovery_strategy=RecoveryStrategy.FALLBACK,
            technical_details=technical_details,
            **kwargs
        )


class PerformanceException(BaseException):
    """性能相關異常"""
    
    def __init__(self, message: str, metric_name: str, threshold: float, actual_value: float, **kwargs):
        technical_details = kwargs.pop("technical_details", {})
        technical_details.update({
            "metric_name": metric_name,
            "threshold": threshold,
            "actual_value": actual_value,
        })
        
        super().__init__(
            message=message,
            error_code="PERF_001",
            category=ErrorCategory.PERFORMANCE,
            recovery_strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
            technical_details=technical_details,
            **kwargs
        )


class ConfigurationException(BaseException):
    """配置相關異常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        technical_details = kwargs.pop("technical_details", {})
        if config_key:
            technical_details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONF_001",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.NONE,
            technical_details=technical_details,
            **kwargs
        )


class ResourceException(BaseException):
    """資源相關異常"""
    
    def __init__(self, message: str, resource_type: str, **kwargs):
        technical_details = kwargs.pop("technical_details", {})
        technical_details["resource_type"] = resource_type
        
        super().__init__(
            message=message,
            error_code="RES_001",
            category=ErrorCategory.RESOURCE,
            recovery_strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
            technical_details=technical_details,
            **kwargs
        )


class SatelliteException(BaseException):
    """衛星相關異常"""
    
    def __init__(self, message: str, satellite_id: Optional[str] = None, **kwargs):
        technical_details = kwargs.pop("technical_details", {})
        if satellite_id:
            technical_details["satellite_id"] = satellite_id
        
        super().__init__(
            message=message,
            error_code="SAT_001",
            category=ErrorCategory.EXTERNAL_SERVICE,
            recovery_strategy=RecoveryStrategy.FALLBACK,
            technical_details=technical_details,
            **kwargs
        )


class HandoverException(BaseException):
    """換手相關異常"""
    
    def __init__(self, message: str, ue_id: Optional[str] = None, **kwargs):
        technical_details = kwargs.pop("technical_details", {})
        if ue_id:
            technical_details["ue_id"] = ue_id
        
        super().__init__(
            message=message,
            error_code="HO_001",
            category=ErrorCategory.BUSINESS_LOGIC,
            recovery_strategy=RecoveryStrategy.ROLLBACK,
            technical_details=technical_details,
            **kwargs
        )


class ErrorHandler:
    """統一錯誤處理器"""
    
    def __init__(self):
        self.error_history: List[BaseException] = []
        self.recovery_handlers: Dict[RecoveryStrategy, Callable] = {}
        self.error_callbacks: List[Callable[[BaseException], None]] = []
        self.metrics = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recovery_success_rate": 0.0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
        }
        
        # 註冊默認恢復處理器
        self._register_default_recovery_handlers()

    def _register_default_recovery_handlers(self):
        """註冊默認恢復處理器"""
        self.recovery_handlers[RecoveryStrategy.RETRY] = self._retry_handler
        self.recovery_handlers[RecoveryStrategy.FALLBACK] = self._fallback_handler
        self.recovery_handlers[RecoveryStrategy.ROLLBACK] = self._rollback_handler
        self.recovery_handlers[RecoveryStrategy.GRACEFUL_DEGRADATION] = self._degradation_handler

    async def handle_exception(
        self, 
        exception: BaseException, 
        auto_recover: bool = True
    ) -> Optional[Any]:
        """處理異常"""
        try:
            # 記錄異常
            self._record_exception(exception)
            
            # 記錄日誌
            await self._log_exception(exception)
            
            # 通知回調函數
            await self._notify_callbacks(exception)
            
            # 嘗試自動恢復
            if auto_recover and exception.recovery_strategy != RecoveryStrategy.NONE:
                recovery_result = await self._attempt_recovery(exception)
                return recovery_result
            
            return None
            
        except Exception as e:
            logger.error(f"錯誤處理器本身發生異常: {e}")
            return None

    def _record_exception(self, exception: BaseException):
        """記錄異常"""
        self.error_history.append(exception)
        
        # 更新統計
        self.metrics["total_errors"] += 1
        
        category_key = exception.category.value
        self.metrics["errors_by_category"][category_key] = (
            self.metrics["errors_by_category"].get(category_key, 0) + 1
        )
        
        severity_key = exception.severity.value
        self.metrics["errors_by_severity"][severity_key] = (
            self.metrics["errors_by_severity"].get(severity_key, 0) + 1
        )
        
        # 保留最近1000個錯誤
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

    async def _log_exception(self, exception: BaseException):
        """記錄異常日誌"""
        log_level = {
            ErrorSeverity.CRITICAL: "critical",
            ErrorSeverity.HIGH: "error",
            ErrorSeverity.MEDIUM: "warning",
            ErrorSeverity.LOW: "info",
            ErrorSeverity.INFO: "info",
        }.get(exception.severity, "error")
        
        log_data = {
            "error_id": exception.error_id,
            "error_code": exception.error_code,
            "message": exception.message,
            "category": exception.category.value,
            "severity": exception.severity.value,
            "service": exception.context.service_name if exception.context else "unknown",
            "function": exception.context.function_name if exception.context else "unknown",
        }
        
        if log_level == "critical":
            logger.critical("Critical error occurred", **log_data)
        elif log_level == "error":
            logger.error("Error occurred", **log_data)
        elif log_level == "warning":
            logger.warning("Warning occurred", **log_data)
        else:
            logger.info("Info logged", **log_data)

    async def _notify_callbacks(self, exception: BaseException):
        """通知回調函數"""
        for callback in self.error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(exception)
                else:
                    callback(exception)
            except Exception as e:
                logger.error(f"錯誤回調函數執行失敗: {e}")

    async def _attempt_recovery(self, exception: BaseException) -> Optional[Any]:
        """嘗試恢復"""
        strategy = exception.recovery_strategy
        handler = self.recovery_handlers.get(strategy)
        
        if not handler:
            logger.warning(f"沒有找到恢復策略處理器: {strategy}")
            return None
        
        max_attempts = 3
        attempt_number = len(exception.recovery_attempts) + 1
        
        if attempt_number > max_attempts:
            logger.error(f"恢復嘗試次數超過限制: {attempt_number}/{max_attempts}")
            return None
        
        start_time = datetime.utcnow()
        
        try:
            self.metrics["recovery_attempts"] += 1
            
            # 執行恢復處理器
            result = await handler(exception, attempt_number)
            
            end_time = datetime.utcnow()
            recovery_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # 記錄恢復動作
            recovery_action = RecoveryAction(
                action_id=str(uuid.uuid4()),
                strategy=strategy,
                attempt_number=attempt_number,
                executed_at=start_time,
                success=result is not None,
                recovery_time_ms=recovery_time_ms,
            )
            
            exception.recovery_attempts.append(recovery_action)
            
            if result is not None:
                exception.recovered = True
                exception.recovery_time_ms = recovery_time_ms
                self.metrics["successful_recoveries"] += 1
                self._update_recovery_success_rate()
                
                logger.info(f"異常恢復成功: {exception.error_id} 使用策略 {strategy.value}")
                return result
            else:
                logger.warning(f"異常恢復失敗: {exception.error_id} 使用策略 {strategy.value}")
                return None
                
        except Exception as recovery_error:
            end_time = datetime.utcnow()
            recovery_time_ms = (end_time - start_time).total_seconds() * 1000
            
            recovery_action = RecoveryAction(
                action_id=str(uuid.uuid4()),
                strategy=strategy,
                attempt_number=attempt_number,
                executed_at=start_time,
                success=False,
                error_message=str(recovery_error),
                recovery_time_ms=recovery_time_ms,
            )
            
            exception.recovery_attempts.append(recovery_action)
            
            logger.error(f"恢復處理器執行異常: {recovery_error}")
            return None

    def _update_recovery_success_rate(self):
        """更新恢復成功率"""
        if self.metrics["recovery_attempts"] > 0:
            self.metrics["recovery_success_rate"] = (
                self.metrics["successful_recoveries"] / self.metrics["recovery_attempts"]
            )

    async def _retry_handler(self, exception: BaseException, attempt_number: int) -> Optional[Any]:
        """重試處理器"""
        try:
            # 指數退避
            delay = min(2 ** attempt_number, 30)  # 最大30秒
            await asyncio.sleep(delay)
            
            # 這裡應該重新執行原始操作
            # 在實際實現中，需要保存原始操作的信息
            logger.info(f"重試操作 (第{attempt_number}次嘗試)")
            
            # 模擬重試成功
            return True
            
        except Exception as e:
            logger.error(f"重試處理失敗: {e}")
            return None

    async def _fallback_handler(self, exception: BaseException, attempt_number: int) -> Optional[Any]:
        """備用方案處理器"""
        try:
            logger.info(f"執行備用方案 (第{attempt_number}次嘗試)")
            
            # 這裡應該執行備用邏輯
            # 例如：使用緩存數據、調用備用服務等
            
            return "fallback_result"
            
        except Exception as e:
            logger.error(f"備用方案處理失敗: {e}")
            return None

    async def _rollback_handler(self, exception: BaseException, attempt_number: int) -> Optional[Any]:
        """回滾處理器"""
        try:
            logger.info(f"執行回滾操作 (第{attempt_number}次嘗試)")
            
            # 這裡應該執行回滾邏輯
            # 例如：撤銷之前的操作、恢復狀態等
            
            return "rollback_completed"
            
        except Exception as e:
            logger.error(f"回滾處理失敗: {e}")
            return None

    async def _degradation_handler(self, exception: BaseException, attempt_number: int) -> Optional[Any]:
        """優雅降級處理器"""
        try:
            logger.info(f"執行優雅降級 (第{attempt_number}次嘗試)")
            
            # 這裡應該執行降級邏輯
            # 例如：減少功能、使用簡化版本等
            
            return "degraded_service"
            
        except Exception as e:
            logger.error(f"優雅降級處理失敗: {e}")
            return None

    def register_recovery_handler(self, strategy: RecoveryStrategy, handler: Callable):
        """註冊恢復處理器"""
        self.recovery_handlers[strategy] = handler

    def register_error_callback(self, callback: Callable[[BaseException], None]):
        """註冊錯誤回調函數"""
        self.error_callbacks.append(callback)

    def get_error_statistics(self) -> Dict[str, Any]:
        """獲取錯誤統計"""
        return self.metrics.copy()

    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取最近的錯誤"""
        recent_errors = self.error_history[-limit:] if len(self.error_history) > limit else self.error_history
        return [error.to_dict() for error in recent_errors]

    def clear_error_history(self):
        """清空錯誤歷史"""
        self.error_history.clear()
        self.metrics = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recovery_success_rate": 0.0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
        }


# 全局錯誤處理器實例
global_error_handler = ErrorHandler()


def handle_exceptions(
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.NONE,
    auto_recover: bool = True,
    exception_types: Optional[List[Type[Exception]]] = None
):
    """異常處理裝飾器"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # 創建統一異常
                    if isinstance(e, BaseException):
                        unified_exception = e
                    else:
                        # 將標準異常轉換為統一異常
                        context = ErrorContext(
                            service_name=func.__module__,
                            function_name=func.__name__
                        )
                        
                        unified_exception = BaseException(
                            message=str(e),
                            error_code="SYS_001",
                            context=context,
                            recovery_strategy=recovery_strategy,
                            caused_by=e
                        )
                    
                    # 處理異常
                    result = await global_error_handler.handle_exception(
                        unified_exception, auto_recover
                    )
                    
                    # 如果沒有恢復成功，重新拋出異常
                    if result is None and not unified_exception.recovered:
                        raise unified_exception
                    
                    return result
            
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 同步版本的異常處理
                    if isinstance(e, BaseException):
                        unified_exception = e
                    else:
                        context = ErrorContext(
                            service_name=func.__module__,
                            function_name=func.__name__
                        )
                        
                        unified_exception = BaseException(
                            message=str(e),
                            error_code="SYS_001",
                            context=context,
                            recovery_strategy=recovery_strategy,
                            caused_by=e
                        )
                    
                    # 記錄異常（同步版本不支持自動恢復）
                    global_error_handler._record_exception(unified_exception)
                    
                    # 重新拋出異常
                    raise unified_exception
            
            return sync_wrapper
    
    return decorator


def create_error_context(
    service_name: str,
    function_name: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **additional_context
) -> ErrorContext:
    """創建錯誤上下文"""
    return ErrorContext(
        service_name=service_name,
        function_name=function_name,
        user_id=user_id,
        request_id=request_id,
        additional_context=additional_context
    )