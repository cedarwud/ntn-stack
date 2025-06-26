"""
統一錯誤處理中間件

為FastAPI應用程序提供統一的錯誤處理中間件，
實現全局異常捕獲、標準化錯誤響應、自動恢復等功能。
"""

import time
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from ..core.exceptions import (
    BaseException as UnifiedBaseException,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    global_error_handler,
    NetworkException,
    DatabaseException,
    AuthenticationException,
    ValidationException,
    BusinessLogicException,
    ExternalServiceException,
    PerformanceException,
    ConfigurationException,
    ResourceException,
    create_error_context
)

logger = structlog.get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """統一錯誤處理中間件"""
    
    def __init__(self, app, enable_auto_recovery: bool = True, enable_detailed_errors: bool = False):
        super().__init__(app)
        self.enable_auto_recovery = enable_auto_recovery
        self.enable_detailed_errors = enable_detailed_errors
        
        # 錯誤統計
        self.request_count = 0
        self.error_count = 0
        self.recovery_count = 0

    async def dispatch(self, request: Request, call_next):
        """處理請求和響應"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 在請求上下文中添加request_id
        request.state.request_id = request_id
        
        try:
            self.request_count += 1
            
            # 執行請求
            response = await call_next(request)
            
            # 檢查響應時間性能
            duration_ms = (time.time() - start_time) * 1000
            if duration_ms > 5000:  # 5秒閾值
                await self._handle_performance_issue(request, duration_ms)
            
            return response
            
        except Exception as e:
            self.error_count += 1
            
            # 創建錯誤上下文
            error_context = self._create_request_context(request, request_id)
            
            # 處理異常
            return await self._handle_exception(e, error_context, request)

    def _create_request_context(self, request: Request, request_id: str) -> ErrorContext:
        """創建請求錯誤上下文"""
        # 嘗試從請求中提取用戶信息
        user_id = None
        session_id = None
        
        # 從headers或token中提取用戶信息
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        elif 'authorization' in request.headers:
            # 簡化的用戶ID提取邏輯
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                # 在實際環境中會解析JWT token
                user_id = 'authenticated_user'
        
        # 從cookies中提取session_id
        session_id = request.cookies.get('session_id')
        
        return create_error_context(
            service_name="netstack_api",
            function_name=f"{request.method} {request.url.path}",
            user_id=user_id,
            request_id=request_id,
            session_id=session_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
        )

    async def _handle_exception(
        self, 
        exception: Exception, 
        context: ErrorContext, 
        request: Request
    ) -> JSONResponse:
        """處理異常並返回適當的響应"""
        
        # 轉換為統一異常
        unified_exception = await self._convert_to_unified_exception(exception, context)
        
        # 使用全局錯誤處理器處理
        recovery_result = await global_error_handler.handle_exception(
            unified_exception, 
            auto_recover=self.enable_auto_recovery
        )
        
        if recovery_result is not None:
            self.recovery_count += 1
            logger.info(f"異常已自動恢復: {unified_exception.error_id}")
        
        # 生成錯誤響應
        return self._create_error_response(unified_exception, request)

    async def _convert_to_unified_exception(
        self, 
        exception: Exception, 
        context: ErrorContext
    ) -> UnifiedBaseException:
        """將標準異常轉換為統一異常"""
        
        if isinstance(exception, UnifiedBaseException):
            # 已經是統一異常，更新上下文
            exception.context = context
            return exception
        
        # 根據異常類型創建適當的統一異常
        if isinstance(exception, HTTPException):
            return self._convert_http_exception(exception, context)
        elif isinstance(exception, ConnectionError):
            return NetworkException(
                message=f"網路連接錯誤: {str(exception)}",
                context=context,
                caused_by=exception
            )
        elif isinstance(exception, TimeoutError):
            return PerformanceException(
                message=f"操作超時: {str(exception)}",
                metric_name="response_time",
                threshold=30.0,
                actual_value=30.0,
                context=context,
                caused_by=exception
            )
        elif isinstance(exception, ValueError):
            return ValidationException(
                message=f"數據驗證錯誤: {str(exception)}",
                context=context,
                caused_by=exception
            )
        elif isinstance(exception, PermissionError):
            return AuthenticationException(
                message=f"權限錯誤: {str(exception)}",
                context=context,
                caused_by=exception
            )
        elif isinstance(exception, FileNotFoundError):
            return ConfigurationException(
                message=f"配置文件未找到: {str(exception)}",
                context=context,
                caused_by=exception
            )
        elif isinstance(exception, MemoryError):
            return ResourceException(
                message=f"內存不足: {str(exception)}",
                resource_type="memory",
                context=context,
                caused_by=exception
            )
        else:
            # 通用系統異常
            return UnifiedBaseException(
                message=f"系統異常: {str(exception)}",
                error_code="SYS_001",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.SYSTEM,
                context=context,
                caused_by=exception
            )

    def _convert_http_exception(self, http_exception: HTTPException, context: ErrorContext) -> UnifiedBaseException:
        """轉換HTTP異常"""
        status_code = http_exception.status_code
        
        if status_code == 401:
            return AuthenticationException(
                message=http_exception.detail,
                context=context,
                caused_by=http_exception
            )
        elif status_code == 403:
            return AuthenticationException(
                message="權限不足",
                context=context,
                caused_by=http_exception
            )
        elif status_code == 404:
            return BusinessLogicException(
                message="資源未找到",
                context=context,
                caused_by=http_exception
            )
        elif status_code == 422:
            return ValidationException(
                message="請求數據驗證失敗",
                context=context,
                caused_by=http_exception
            )
        elif 500 <= status_code < 600:
            return UnifiedBaseException(
                message=f"伺服器內部錯誤: {http_exception.detail}",
                error_code="HTTP_500",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.SYSTEM,
                context=context,
                caused_by=http_exception
            )
        else:
            return UnifiedBaseException(
                message=f"HTTP錯誤 {status_code}: {http_exception.detail}",
                error_code=f"HTTP_{status_code}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.SYSTEM,
                context=context,
                caused_by=http_exception
            )

    def _create_error_response(self, exception: UnifiedBaseException, request: Request) -> JSONResponse:
        """創建錯誤響應"""
        
        # 根據異常類型確定HTTP狀態碼
        status_code = self._get_http_status_code(exception)
        
        # 基本錯誤響應
        error_response = {
            "error": {
                "error_id": exception.error_id,
                "error_code": exception.error_code,
                "message": exception.user_message,
                "severity": exception.severity.value,
                "category": exception.category.value,
                "timestamp": exception.occurred_at.isoformat(),
            },
            "request_id": exception.context.request_id if exception.context else None,
        }
        
        # 如果啟用詳細錯誤信息
        if self.enable_detailed_errors:
            error_response["error"]["technical_details"] = {
                "technical_message": exception.message,
                "technical_details": exception.technical_details,
                "stack_trace": exception.stack_trace,
                "context": exception.context.additional_context if exception.context else {},
                "recovery_attempts": len(exception.recovery_attempts),
                "recovered": exception.recovered,
            }
        
        # 添加恢復信息
        if exception.recovered:
            error_response["recovery"] = {
                "recovered": True,
                "recovery_time_ms": exception.recovery_time_ms,
                "recovery_attempts": len(exception.recovery_attempts),
            }
        
        # 添加重試建議
        if exception.recovery_strategy.value in ["retry", "fallback"]:
            error_response["suggestion"] = {
                "action": "retry",
                "message": "此錯誤可能是暫時性的，請稍後重試",
                "retry_after_seconds": self._calculate_retry_delay(exception),
            }
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={
                "X-Error-ID": exception.error_id,
                "X-Request-ID": exception.context.request_id if exception.context else "",
            }
        )

    def _get_http_status_code(self, exception: UnifiedBaseException) -> int:
        """根據異常類型獲取HTTP狀態碼"""
        status_mapping = {
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.VALIDATION: 422,
            ErrorCategory.BUSINESS_LOGIC: 400,
            ErrorCategory.NETWORK: 503,
            ErrorCategory.DATABASE: 503,
            ErrorCategory.EXTERNAL_SERVICE: 503,
            ErrorCategory.PERFORMANCE: 503,
            ErrorCategory.CONFIGURATION: 500,
            ErrorCategory.RESOURCE: 503,
            ErrorCategory.SYSTEM: 500,
        }
        
        base_status = status_mapping.get(exception.category, 500)
        
        # 根據嚴重程度調整
        if exception.severity == ErrorSeverity.CRITICAL:
            return 500
        elif exception.severity == ErrorSeverity.HIGH:
            return base_status
        else:
            return base_status

    def _calculate_retry_delay(self, exception: UnifiedBaseException) -> int:
        """計算重試延遲時間"""
        attempt_count = len(exception.recovery_attempts)
        
        # 指數退避，最大60秒
        delay = min(2 ** attempt_count, 60)
        
        return delay

    async def _handle_performance_issue(self, request: Request, duration_ms: float):
        """處理性能問題"""
        context = self._create_request_context(request, getattr(request.state, 'request_id', 'unknown'))
        
        performance_exception = PerformanceException(
            message=f"請求響應時間過長: {duration_ms:.2f}ms",
            metric_name="response_time",
            threshold=5000.0,
            actual_value=duration_ms,
            context=context
        )
        
        # 記錄性能異常但不中斷請求
        await global_error_handler.handle_exception(performance_exception, auto_recover=False)

    def get_middleware_statistics(self) -> Dict[str, Any]:
        """獲取中間件統計信息"""
        error_rate = (self.error_count / self.request_count) if self.request_count > 0 else 0
        recovery_rate = (self.recovery_count / self.error_count) if self.error_count > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "total_recoveries": self.recovery_count,
            "error_rate": error_rate,
            "recovery_rate": recovery_rate,
            "auto_recovery_enabled": self.enable_auto_recovery,
            "detailed_errors_enabled": self.enable_detailed_errors,
        }


def create_error_handling_middleware(
    enable_auto_recovery: bool = True,
    enable_detailed_errors: bool = False
) -> ErrorHandlingMiddleware:
    """創建錯誤處理中間件"""
    return lambda app: ErrorHandlingMiddleware(
        app,
        enable_auto_recovery=enable_auto_recovery,
        enable_detailed_errors=enable_detailed_errors
    )


class ErrorResponseModel:
    """錯誤響應模型（用於API文檔）"""
    
    @staticmethod
    def get_error_responses() -> Dict[int, Dict[str, Any]]:
        """獲取標準錯誤響應定義"""
        return {
            400: {
                "description": "業務邏輯錯誤",
                "content": {
                    "application/json": {
                        "example": {
                            "error": {
                                "error_id": "uuid-string",
                                "error_code": "BL_001",
                                "message": "操作無法完成，請聯絡系統管理員",
                                "severity": "medium",
                                "category": "business_logic",
                                "timestamp": "2024-01-01T00:00:00Z"
                            },
                            "request_id": "uuid-string"
                        }
                    }
                }
            },
            401: {
                "description": "認證失敗",
                "content": {
                    "application/json": {
                        "example": {
                            "error": {
                                "error_id": "uuid-string",
                                "error_code": "AUTH_001",
                                "message": "身份驗證失敗，請重新登入",
                                "severity": "high",
                                "category": "authentication",
                                "timestamp": "2024-01-01T00:00:00Z"
                            },
                            "request_id": "uuid-string"
                        }
                    }
                }
            },
            422: {
                "description": "資料驗證錯誤",
                "content": {
                    "application/json": {
                        "example": {
                            "error": {
                                "error_id": "uuid-string",
                                "error_code": "VAL_001",
                                "message": "輸入的資料格式不正確，請檢查後重新輸入",
                                "severity": "low",
                                "category": "validation",
                                "timestamp": "2024-01-01T00:00:00Z"
                            },
                            "request_id": "uuid-string"
                        }
                    }
                }
            },
            500: {
                "description": "內部伺服器錯誤",
                "content": {
                    "application/json": {
                        "example": {
                            "error": {
                                "error_id": "uuid-string",
                                "error_code": "SYS_001",
                                "message": "系統發生未知錯誤，請聯絡管理員",
                                "severity": "high",
                                "category": "system",
                                "timestamp": "2024-01-01T00:00:00Z"
                            },
                            "request_id": "uuid-string",
                            "recovery": {
                                "recovered": false,
                                "recovery_attempts": 1
                            }
                        }
                    }
                }
            },
            503: {
                "description": "服務暫時不可用",
                "content": {
                    "application/json": {
                        "example": {
                            "error": {
                                "error_id": "uuid-string",
                                "error_code": "NET_001",
                                "message": "網路連線發生問題，請檢查網路設定",
                                "severity": "medium",
                                "category": "network",
                                "timestamp": "2024-01-01T00:00:00Z"
                            },
                            "request_id": "uuid-string",
                            "suggestion": {
                                "action": "retry",
                                "message": "此錯誤可能是暫時性的，請稍後重試",
                                "retry_after_seconds": 5
                            }
                        }
                    }
                }
            }
        }


# 錯誤響應助手函數
def raise_validation_error(message: str, field_name: Optional[str] = None, **context):
    """拋出驗證錯誤"""
    error_context = create_error_context(
        service_name="api_validation",
        function_name="validate_request",
        **context
    )
    
    raise ValidationException(
        message=message,
        field_name=field_name,
        context=error_context
    )


def raise_business_error(message: str, **context):
    """拋出業務邏輯錯誤"""
    error_context = create_error_context(
        service_name="business_logic",
        function_name="process_request",
        **context
    )
    
    raise BusinessLogicException(
        message=message,
        context=error_context
    )


def raise_auth_error(message: str, **context):
    """拋出認證錯誤"""
    error_context = create_error_context(
        service_name="authentication",
        function_name="authenticate_user",
        **context
    )
    
    raise AuthenticationException(
        message=message,
        context=error_context
    )