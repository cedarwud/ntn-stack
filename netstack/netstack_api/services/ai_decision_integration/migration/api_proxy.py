"""
API Proxy for AI Decision Engine Migration
==========================================

提供v1到v2 API的代理服務，支援A/B測試和漸進式遷移。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from fastapi import HTTPException, Request, Response
from dataclasses import dataclass
import httpx
import structlog

from .feature_flag_manager import get_feature_flag_manager
from ..interfaces.executor import ExecutionResult, ExecutionStatus
from ..interfaces.decision_engine import Decision

logger = structlog.get_logger(__name__)

@dataclass
class ProxyConfig:
    """代理配置"""
    old_api_base_url: str = "/api/v1/ai-decision"
    new_api_base_url: str = "/api/v2/decision"
    timeout_seconds: float = 30.0
    retry_count: int = 3
    enable_fallback: bool = True
    enable_metrics: bool = True

@dataclass
class ProxyMetrics:
    """代理指標"""
    total_requests: int = 0
    old_api_requests: int = 0
    new_api_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    fallback_count: int = 0
    avg_response_time: float = 0.0
    last_updated: datetime = None

class APIProxy:
    """API代理服務"""
    
    def __init__(self, config: ProxyConfig = None):
        self.config = config or ProxyConfig()
        self.metrics = ProxyMetrics()
        self.feature_manager = get_feature_flag_manager()
        self.client = httpx.AsyncClient(timeout=self.config.timeout_seconds)
        
    async def proxy_comprehensive_decision(self, request_data: Dict[str, Any], 
                                         request: Request) -> Dict[str, Any]:
        """
        代理綜合決策請求
        
        Args:
            request_data: 請求數據
            request: FastAPI請求對象
            
        Returns:
            Dict: 響應數據
        """
        start_time = datetime.utcnow()
        user_id = self._extract_user_id(request)
        
        # 記錄請求
        logger.info("Proxying comprehensive decision request", 
                   user_id=user_id, request_size=len(json.dumps(request_data)))
        
        # 決定使用哪個API
        use_new_api = self._should_use_new_api(user_id)
        
        try:
            if use_new_api:
                result = await self._call_new_api(request_data, "handover")
                self.metrics.new_api_requests += 1
            else:
                result = await self._call_old_api(request_data, "comprehensive-decision")
                self.metrics.old_api_requests += 1
            
            # 更新指標
            self._update_metrics(start_time, True, use_new_api)
            
            return result
            
        except Exception as e:
            logger.error("Proxy request failed", error=str(e), use_new_api=use_new_api)
            
            # 嘗試fallback
            if self.config.enable_fallback:
                try:
                    if use_new_api:
                        logger.info("Falling back to old API")
                        result = await self._call_old_api(request_data, "comprehensive-decision")
                        self.metrics.fallback_count += 1
                    else:
                        logger.info("Falling back to new API")
                        result = await self._call_new_api(request_data, "handover")
                        self.metrics.fallback_count += 1
                    
                    self._update_metrics(start_time, True, not use_new_api)
                    return result
                    
                except Exception as fallback_error:
                    logger.error("Fallback also failed", error=str(fallback_error))
            
            # 更新錯誤指標
            self._update_metrics(start_time, False, use_new_api)
            
            # 返回錯誤響應
            return {
                "success": False,
                "error": f"Decision service temporarily unavailable: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def proxy_status_request(self, request: Request) -> Dict[str, Any]:
        """
        代理狀態請求
        
        Args:
            request: FastAPI請求對象
            
        Returns:
            Dict: 狀態響應
        """
        user_id = self._extract_user_id(request)
        use_new_api = self._should_use_new_api(user_id)
        
        try:
            if use_new_api:
                result = await self._call_new_api({}, "status")
            else:
                result = await self._call_old_api({}, "status")
            
            # 添加代理信息
            result["proxy_info"] = {
                "using_new_api": use_new_api,
                "api_version": "v2" if use_new_api else "v1",
                "proxy_metrics": self._get_metrics_summary()
            }
            
            return result
            
        except Exception as e:
            logger.error("Status proxy request failed", error=str(e))
            return {
                "success": False,
                "error": f"Status service unavailable: {str(e)}",
                "proxy_info": {
                    "using_new_api": use_new_api,
                    "api_version": "v2" if use_new_api else "v1",
                    "proxy_metrics": self._get_metrics_summary()
                }
            }
    
    async def _call_new_api(self, request_data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """
        調用新API
        
        Args:
            request_data: 請求數據
            endpoint: 端點名稱
            
        Returns:
            Dict: 響應數據
        """
        # 轉換請求格式到新API格式
        transformed_data = self._transform_to_new_api_format(request_data, endpoint)
        
        # 直接調用新API服務
        from ..orchestrator import DecisionOrchestrator
        from ..config.di_container import create_default_container
        
        container = create_default_container(use_mocks=False)
        orchestrator = DecisionOrchestrator(container)
        
        if endpoint == "handover":
            result = await orchestrator.make_handover_decision(transformed_data)
            # 轉換結果格式
            return self._transform_from_new_api_format(result, endpoint)
        elif endpoint == "status":
            result = orchestrator.get_service_status()
            return result
        else:
            raise HTTPException(status_code=404, detail=f"Unknown endpoint: {endpoint}")
    
    async def _call_old_api(self, request_data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """
        調用舊API
        
        Args:
            request_data: 請求數據
            endpoint: 端點名稱
            
        Returns:
            Dict: 響應數據
        """
        # 這裡應該調用舊的ai_decision_engine
        # 為了演示，我們返回一個模擬響應
        logger.info("Calling old API", endpoint=endpoint)
        
        # 模擬舊API響應
        return {
            "success": True,
            "decision_id": f"old_api_{datetime.utcnow().timestamp()}",
            "confidence_score": 0.85,
            "comprehensive_decision": {
                "actions": ["optimize_power", "adjust_beamforming"],
                "confidence": 0.85,
                "reasoning": "Legacy algorithm decision"
            },
            "health_analysis": {
                "risk_level": "medium",
                "health_score": 0.75
            },
            "urgent_mode": request_data.get("urgent_mode", False),
            "decision_time_seconds": 0.15,
            "timestamp": datetime.utcnow().isoformat(),
            "api_version": "v1"
        }
    
    def _should_use_new_api(self, user_id: str = None) -> bool:
        """
        決定是否使用新API
        
        Args:
            user_id: 用戶ID
            
        Returns:
            bool: 是否使用新API
        """
        # 檢查API代理功能是否啟用
        if self.feature_manager.is_feature_enabled("enable_new_api_proxy", user_id):
            return True
        
        # 檢查各個核心功能是否全部啟用
        core_features = [
            "use_new_event_processor",
            "use_new_candidate_selector", 
            "use_new_rl_engine",
            "use_new_executor"
        ]
        
        for feature in core_features:
            if not self.feature_manager.is_feature_enabled(feature, user_id):
                return False
        
        return True
    
    def _extract_user_id(self, request: Request) -> str:
        """
        從請求中提取用戶ID
        
        Args:
            request: FastAPI請求對象
            
        Returns:
            str: 用戶ID
        """
        # 從header、query參數或IP地址提取用戶ID
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id
        
        # 從IP地址生成用戶ID
        client_ip = request.client.host if request.client else "unknown"
        return f"ip_{client_ip}"
    
    def _transform_to_new_api_format(self, request_data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """
        轉換請求格式到新API格式
        
        Args:
            request_data: 原始請求數據
            endpoint: 端點名稱
            
        Returns:
            Dict: 新API格式數據
        """
        if endpoint == "handover":
            # 轉換綜合決策請求到換手決策格式
            if "context" in request_data:
                context = request_data["context"]
                return {
                    "event_type": "comprehensive_decision",
                    "event_data": {
                        "system_metrics": context.get("system_metrics", {}),
                        "network_state": context.get("network_state", {}),
                        "interference_data": context.get("interference_data", {}),
                        "optimization_objectives": context.get("optimization_objectives", []),
                        "constraints": context.get("constraints", {}),
                        "urgent_mode": request_data.get("urgent_mode", False)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return request_data
    
    def _transform_from_new_api_format(self, result: Any, endpoint: str) -> Dict[str, Any]:
        """
        轉換新API結果格式到舊API格式
        
        Args:
            result: 新API結果
            endpoint: 端點名稱
            
        Returns:
            Dict: 舊API格式結果
        """
        if endpoint == "handover" and isinstance(result, ExecutionResult):
            # 轉換ExecutionResult到舊API格式
            return {
                "success": result.success,
                "decision_id": result.execution_id,
                "confidence_score": getattr(result, 'confidence', 0.85),
                "comprehensive_decision": {
                    "actions": [],  # 從result.decision中提取
                    "confidence": getattr(result, 'confidence', 0.85),
                    "reasoning": "New AI system decision"
                },
                "health_analysis": {
                    "risk_level": "low",
                    "health_score": 0.90
                },
                "urgent_mode": False,
                "decision_time_seconds": result.execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "api_version": "v2",
                "performance_metrics": result.performance_metrics
            }
        
        return result if isinstance(result, dict) else {"result": result}
    
    def _update_metrics(self, start_time: datetime, success: bool, used_new_api: bool):
        """
        更新代理指標
        
        Args:
            start_time: 開始時間
            success: 是否成功
            used_new_api: 是否使用新API
        """
        if not self.config.enable_metrics:
            return
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        self.metrics.total_requests += 1
        if success:
            self.metrics.success_count += 1
        else:
            self.metrics.error_count += 1
        
        # 更新平均響應時間
        if self.metrics.total_requests == 1:
            self.metrics.avg_response_time = response_time
        else:
            self.metrics.avg_response_time = (
                (self.metrics.avg_response_time * (self.metrics.total_requests - 1) + response_time) /
                self.metrics.total_requests
            )
        
        self.metrics.last_updated = end_time
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """
        獲取指標摘要
        
        Returns:
            Dict: 指標摘要
        """
        if not self.config.enable_metrics:
            return {}
        
        return {
            "total_requests": self.metrics.total_requests,
            "old_api_requests": self.metrics.old_api_requests,
            "new_api_requests": self.metrics.new_api_requests,
            "success_rate": (
                self.metrics.success_count / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0
            ),
            "error_rate": (
                self.metrics.error_count / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0
            ),
            "fallback_rate": (
                self.metrics.fallback_count / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0
            ),
            "avg_response_time": self.metrics.avg_response_time,
            "last_updated": self.metrics.last_updated.isoformat() if self.metrics.last_updated else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        代理健康檢查
        
        Returns:
            Dict: 健康狀態
        """
        try:
            # 檢查新API
            new_api_status = await self._call_new_api({}, "status")
            new_api_healthy = new_api_status.get("success", False)
        except Exception as e:
            logger.error("New API health check failed", error=str(e))
            new_api_healthy = False
        
        try:
            # 檢查舊API
            old_api_status = await self._call_old_api({}, "status")
            old_api_healthy = old_api_status.get("success", False)
        except Exception as e:
            logger.error("Old API health check failed", error=str(e))
            old_api_healthy = False
        
        return {
            "proxy_healthy": True,
            "new_api_healthy": new_api_healthy,
            "old_api_healthy": old_api_healthy,
            "feature_flags": self.feature_manager.get_migration_status()["feature_flags"],
            "metrics": self._get_metrics_summary()
        }
    
    async def close(self):
        """關閉代理服務"""
        await self.client.aclose()

# 全域代理實例
_api_proxy = None

def get_api_proxy() -> APIProxy:
    """獲取API代理實例"""
    global _api_proxy
    if _api_proxy is None:
        _api_proxy = APIProxy()
    return _api_proxy

async def initialize_api_proxy(config: ProxyConfig = None):
    """初始化API代理"""
    global _api_proxy
    _api_proxy = APIProxy(config)
    return _api_proxy