"""
NetStack API 異常管理器
負責統一管理所有異常處理器的設定和配置
"""

import structlog
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

logger = structlog.get_logger(__name__)


class ExceptionManager:
    """
    異常管理器
    負責設定各種異常處理器並提供統一的錯誤回應格式
    """
    
    def __init__(self, app: FastAPI):
        """
        初始化異常管理器
        
        Args:
            app: FastAPI 應用程式實例
        """
        self.app = app
        self.exception_handlers = []
        
    def setup_handlers(self) -> None:
        """
        設定所有異常處理器
        """
        logger.info("🛡️ 設定異常處理器...")
        
        try:
            self._setup_404_handler()
            self._setup_500_handler()
            self._setup_http_exception_handler()
            self._setup_validation_error_handler()
            self._setup_generic_exception_handler()
            
            logger.info(f"✅ 所有異常處理器設定完成 ({len(self.exception_handlers)} 個)")
            
        except Exception as e:
            logger.error("💥 異常處理器設定失敗", error=str(e))
            raise
    
    def _setup_404_handler(self) -> None:
        """設定 404 Not Found 處理器"""
        @self.app.exception_handler(404)
        async def not_found_handler(request: Request, exc):
            """處理 404 錯誤"""
            error_response = self._create_error_response(
                status_code=404,
                error_type="Not Found",
                message=f"路徑 {request.url.path} 不存在",
                request=request,
                additional_info={
                    "available_docs": "/docs",
                    "api_info": "/",
                    "health_check": "/health"
                }
            )
            
            logger.warning(
                "404 錯誤",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else None
            )
            
            return JSONResponse(
                status_code=404,
                content=error_response
            )
        
        self.exception_handlers.append({
            "status_code": 404,
            "error_type": "Not Found",
            "description": "處理路徑不存在的錯誤"
        })
    
    def _setup_500_handler(self) -> None:
        """設定 500 Internal Server Error 處理器"""
        @self.app.exception_handler(500)
        async def internal_server_error_handler(request: Request, exc):
            """處理 500 錯誤"""
            error_response = self._create_error_response(
                status_code=500,
                error_type="Internal Server Error",
                message="服務器內部錯誤",
                request=request,
                additional_info={
                    "contact_support": "請聯繫技術支援",
                    "error_id": f"ERR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                }
            )
            
            logger.error(
                "500 內部服務器錯誤",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response
            )
        
        self.exception_handlers.append({
            "status_code": 500,
            "error_type": "Internal Server Error",
            "description": "處理內部服務器錯誤"
        })
    
    def _setup_http_exception_handler(self) -> None:
        """設定 HTTP 異常處理器"""
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """處理 HTTP 異常"""
            error_response = self._create_error_response(
                status_code=exc.status_code,
                error_type=f"HTTP {exc.status_code}",
                message=exc.detail,
                request=request,
                additional_info={
                    "exception_type": "HTTPException"
                }
            )
            
            logger.warning(
                "HTTP異常",
                status_code=exc.status_code,
                detail=exc.detail,
                path=request.url.path,
                method=request.method
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response
            )
        
        self.exception_handlers.append({
            "status_code": "variable",
            "error_type": "HTTPException",
            "description": "處理 FastAPI HTTP 異常"
        })
    
    def _setup_validation_error_handler(self) -> None:
        """設定請求驗證錯誤處理器"""
        from fastapi.exceptions import RequestValidationError
        from pydantic import ValidationError
        
        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            """處理請求驗證錯誤"""
            error_details = []
            
            for error in exc.errors():
                error_details.append({
                    "field": " -> ".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            error_response = self._create_error_response(
                status_code=422,
                error_type="Validation Error",
                message="請求參數驗證失敗",
                request=request,
                additional_info={
                    "validation_errors": error_details,
                    "total_errors": len(error_details)
                }
            )
            
            logger.warning(
                "請求驗證錯誤",
                path=request.url.path,
                method=request.method,
                error_count=len(error_details),
                errors=error_details
            )
            
            return JSONResponse(
                status_code=422,
                content=error_response
            )
        
        self.exception_handlers.append({
            "status_code": 422,
            "error_type": "Validation Error",
            "description": "處理請求參數驗證錯誤"
        })
    
    def _setup_generic_exception_handler(self) -> None:
        """設定通用異常處理器"""
        @self.app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            """處理所有未捕獲的異常"""
            error_id = f"ERR-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
            
            error_response = self._create_error_response(
                status_code=500,
                error_type="Unexpected Error",
                message="發生未預期的錯誤",
                request=request,
                additional_info={
                    "error_id": error_id,
                    "exception_type": type(exc).__name__,
                    "contact_support": "請提供錯誤ID聯繫技術支援"
                }
            )
            
            logger.error(
                "未捕獲的異常",
                path=request.url.path,
                method=request.method,
                error_id=error_id,
                exception_type=type(exc).__name__,
                error=str(exc),
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response
            )
        
        self.exception_handlers.append({
            "status_code": 500,
            "error_type": "Generic Exception",
            "description": "處理所有未捕獲的異常"
        })
    
    def _create_error_response(self, 
                              status_code: int,
                              error_type: str,
                              message: str,
                              request: Request,
                              additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        創建統一格式的錯誤回應
        
        Args:
            status_code: HTTP 狀態碼
            error_type: 錯誤類型
            message: 錯誤訊息
            request: HTTP 請求
            additional_info: 額外資訊
            
        Returns:
            Dict[str, Any]: 錯誤回應字典
        """
        error_response = {
            "error": error_type,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path,
            "method": request.method
        }
        
        if additional_info:
            error_response.update(additional_info)
        
        return error_response
    
    def get_handler_status(self) -> Dict[str, Any]:
        """
        獲取異常處理器狀態
        
        Returns:
            Dict[str, Any]: 處理器狀態摘要
        """
        return {
            "total_handlers": len(self.exception_handlers),
            "handlers": self.exception_handlers,
            "coverage": [
                "404 Not Found",
                "500 Internal Server Error", 
                "HTTP Exceptions",
                "Validation Errors",
                "Generic Exceptions"
            ]
        }
    
    def test_error_handlers(self) -> Dict[str, Any]:
        """
        測試錯誤處理器（僅供測試環境使用）
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.warning("⚠️ 錯誤處理器測試模式 - 僅供測試環境使用")
        
        # 在這裡可以添加測試邏輯，例如：
        # - 觸發不同類型的錯誤
        # - 驗證錯誤回應格式
        # - 檢查日誌記錄
        
        return {
            "test_mode": True,
            "warning": "此功能僅供測試環境使用",
            "handlers_configured": len(self.exception_handlers),
            "test_recommendation": "在測試環境中訪問不存在的端點來測試 404 處理器"
        }