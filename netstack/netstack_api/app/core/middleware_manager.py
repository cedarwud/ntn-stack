"""
NetStack API 中間件管理器
負責統一管理所有中間件的設定和配置
"""

import structlog
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram
from typing import List, Optional

logger = structlog.get_logger(__name__)


class MiddlewareManager:
    """
    中間件管理器
    負責設定 CORS、日誌、指標等中間件
    """
    
    def __init__(self, app: FastAPI):
        """
        初始化中間件管理器
        
        Args:
            app: FastAPI 應用程式實例
        """
        self.app = app
        self.enabled_middleware = []
        
        # Prometheus 指標設定
        self.request_count = Counter(
            "netstack_requests_total",
            "Total number of requests",
            ["method", "endpoint", "status"]
        )
        
        self.request_duration = Histogram(
            "netstack_request_duration_seconds", 
            "Request duration in seconds",
            ["method", "endpoint"]
        )
        
    def setup_cors(self, 
                   allowed_origins: List[str] = None,
                   allow_credentials: bool = True,
                   allowed_methods: List[str] = None,
                   allowed_headers: List[str] = None) -> None:
        """
        設定 CORS 中間件
        
        Args:
            allowed_origins: 允許的來源域名列表，預設為 ["*"]
            allow_credentials: 是否允許憑證，預設為 True
            allowed_methods: 允許的 HTTP 方法列表，預設為 ["*"]  
            allowed_headers: 允許的 HTTP 標頭列表，預設為 ["*"]
        """
        logger.info("🌐 設定 CORS 中間件...")
        
        # 設定預設值
        if allowed_origins is None:
            allowed_origins = ["*"]
        if allowed_methods is None:
            allowed_methods = ["*"]
        if allowed_headers is None:
            allowed_headers = ["*"]
        
        try:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=allowed_origins,
                allow_credentials=allow_credentials,
                allow_methods=allowed_methods,
                allow_headers=allowed_headers,
            )
            
            self.enabled_middleware.append({
                "name": "CORSMiddleware",
                "config": {
                    "allow_origins": allowed_origins,
                    "allow_credentials": allow_credentials,
                    "allow_methods": allowed_methods,
                    "allow_headers": allowed_headers
                },
                "status": "enabled"
            })
            
            logger.info("✅ CORS 中間件設定完成", 
                       origins=allowed_origins,
                       credentials=allow_credentials)
            
        except Exception as e:
            logger.error("💥 CORS 中間件設定失敗", error=str(e))
            raise
    
    def setup_metrics_logging(self) -> None:
        """
        設定指標收集和日誌記錄中間件
        """
        logger.info("📊 設定指標和日誌中間件...")
        
        try:
            @self.app.middleware("http")
            async def log_and_metrics_middleware(request: Request, call_next):
                """
                HTTP 請求日誌和指標收集中間件
                
                Args:
                    request: HTTP 請求
                    call_next: 下一個中間件或路由處理器
                    
                Returns:
                    HTTP 回應
                """
                start_time = datetime.utcnow()
                
                # 記錄請求開始
                logger.info(
                    "HTTP請求開始",
                    method=request.method,
                    url=str(request.url),
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent", "unknown")
                )
                
                try:
                    # 處理請求
                    response = await call_next(request)
                    
                    # 計算處理時間
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    # 記錄 Prometheus 指標
                    method = request.method
                    endpoint = request.url.path
                    
                    self.request_count.labels(
                        method=method, 
                        endpoint=endpoint, 
                        status=response.status_code
                    ).inc()
                    
                    self.request_duration.labels(
                        method=method, 
                        endpoint=endpoint
                    ).observe(duration)
                    
                    # 記錄請求完成
                    logger.info(
                        "HTTP請求完成",
                        method=method,
                        url=endpoint,
                        status_code=response.status_code,
                        duration=duration,
                        response_size=response.headers.get("content-length", "unknown")
                    )
                    
                    return response
                    
                except Exception as e:
                    # 計算錯誤處理時間
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    # 記錄錯誤指標
                    self.request_count.labels(
                        method=request.method, 
                        endpoint=request.url.path, 
                        status=500
                    ).inc()
                    
                    # 記錄錯誤日誌
                    logger.error(
                        "HTTP請求失敗",
                        method=request.method,
                        url=str(request.url),
                        error=str(e),
                        duration=duration,
                        exc_info=True
                    )
                    
                    raise
            
            self.enabled_middleware.append({
                "name": "LogAndMetricsMiddleware",
                "config": {
                    "metrics_enabled": True,
                    "logging_enabled": True,
                    "prometheus_metrics": ["request_count", "request_duration"]
                },
                "status": "enabled"
            })
            
            logger.info("✅ 指標和日誌中間件設定完成")
            
        except Exception as e:
            logger.error("💥 指標和日誌中間件設定失敗", error=str(e))
            raise
    
    def setup_security_headers(self) -> None:
        """
        設定安全標頭中間件
        """
        logger.info("🔒 設定安全標頭中間件...")
        
        try:
            @self.app.middleware("http")
            async def security_headers_middleware(request: Request, call_next):
                """
                安全標頭中間件
                
                Args:
                    request: HTTP 請求
                    call_next: 下一個中間件或路由處理器
                    
                Returns:
                    HTTP 回應
                """
                response = await call_next(request)
                
                # 添加安全標頭
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["X-XSS-Protection"] = "1; mode=block"
                response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                response.headers["Server"] = "NetStack-API/1.0"
                
                return response
            
            self.enabled_middleware.append({
                "name": "SecurityHeadersMiddleware",
                "config": {
                    "headers": [
                        "X-Content-Type-Options",
                        "X-Frame-Options", 
                        "X-XSS-Protection",
                        "Referrer-Policy",
                        "Server"
                    ]
                },
                "status": "enabled"
            })
            
            logger.info("✅ 安全標頭中間件設定完成")
            
        except Exception as e:
            logger.error("💥 安全標頭中間件設定失敗", error=str(e))
            raise
    
    def setup_request_size_limit(self, max_size: int = 16 * 1024 * 1024) -> None:
        """
        設定請求大小限制中間件
        
        Args:
            max_size: 最大請求大小（位元組），預設 16MB
        """
        logger.info(f"📏 設定請求大小限制中間件 (最大: {max_size/1024/1024:.1f}MB)...")
        
        try:
            @self.app.middleware("http")
            async def request_size_limit_middleware(request: Request, call_next):
                """
                請求大小限制中間件
                
                Args:
                    request: HTTP 請求
                    call_next: 下一個中間件或路由處理器
                    
                Returns:
                    HTTP 回應
                """
                content_length = request.headers.get("content-length")
                
                if content_length:
                    content_length = int(content_length)
                    if content_length > max_size:
                        logger.warning(
                            "請求大小超過限制",
                            content_length=content_length,
                            max_size=max_size,
                            url=str(request.url)
                        )
                        
                        from fastapi import HTTPException
                        raise HTTPException(
                            status_code=413,
                            detail=f"請求大小超過限制 ({max_size/1024/1024:.1f}MB)"
                        )
                
                return await call_next(request)
            
            self.enabled_middleware.append({
                "name": "RequestSizeLimitMiddleware",
                "config": {
                    "max_size_bytes": max_size,
                    "max_size_mb": max_size / 1024 / 1024
                },
                "status": "enabled"
            })
            
            logger.info("✅ 請求大小限制中間件設定完成")
            
        except Exception as e:
            logger.error("💥 請求大小限制中間件設定失敗", error=str(e))
            raise
    
    def get_middleware_status(self) -> dict:
        """
        獲取所有中間件的狀態
        
        Returns:
            dict: 中間件狀態摘要
        """
        total_middleware = len(self.enabled_middleware)
        enabled_middleware = sum(1 for m in self.enabled_middleware if m["status"] == "enabled")
        
        return {
            "total_middleware": total_middleware,
            "enabled_middleware": enabled_middleware,
            "middleware_list": self.enabled_middleware,
            "metrics": {
                "prometheus_enabled": True,
                "request_counting": True,
                "duration_tracking": True
            }
        }
    
    def get_metrics_summary(self) -> dict:
        """
        獲取指標收集摘要
        
        Returns:
            dict: 指標摘要
        """
        try:
            # 獲取當前指標值
            request_count_sample = list(self.request_count.collect())[0]
            duration_sample = list(self.request_duration.collect())[0] 
            
            return {
                "request_count": {
                    "name": request_count_sample.name,
                    "help": request_count_sample.help,
                    "type": request_count_sample.type,
                    "samples": len(request_count_sample.samples)
                },
                "request_duration": {
                    "name": duration_sample.name,
                    "help": duration_sample.help,
                    "type": duration_sample.type,
                    "samples": len(duration_sample.samples)
                }
            }
        except Exception as e:
            logger.error("獲取指標摘要失敗", error=str(e))
            return {"error": str(e)}