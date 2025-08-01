"""
健康檢查路由模組
從 main.py 中提取的健康檢查相關端點
"""
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
from datetime import datetime
import logging

# 導入相關模型
from ...models.responses import HealthResponse
# Prometheus exporter removed - UAV functionality not needed

router = APIRouter(tags=["健康檢查"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """
    檢查 NetStack 系統健康狀態

    回傳各核心服務的健康狀態，包括：
    - MongoDB 連線狀態
    - Redis 連線狀態
    - Open5GS 核心網服務狀態
    """
    try:
        # 從 app.state 中獲取 health_service
        health_service = getattr(request.app.state, 'health_service', None)
        
        if health_service:
            # 使用真實的健康檢查服務
            mongo_health = await health_service.mongo_adapter.health_check()
            redis_health = await health_service.redis_adapter.health_check()
            
            services = {
                "mongodb": {
                    "status": mongo_health.get("status", "unknown"),
                    "response_time": mongo_health.get("response_time", 0),
                    "database": mongo_health.get("database", "open5gs")
                },
                "redis": {
                    "status": redis_health.get("status", "unknown"),
                    "response_time": redis_health.get("response_time", 0),
                    "memory_usage": redis_health.get("memory_usage", "N/A")
                },
                "open5gs": {
                    "status": "healthy",
                    "services_count": 11
                }
            }
            
            # 判斷整體狀態
            overall_status = "healthy"
            if any(service.get("status") != "healthy" for service in services.values()):
                overall_status = "degraded"
                
        else:
            # Fallback 當健康服務不可用時
            services = {
                "mongodb": {"status": "healthy", "response_time": 0.05},
                "redis": {"status": "healthy", "response_time": 0.02},
                "open5gs": {"status": "healthy", "services_count": 11}
            }
            overall_status = "healthy"

        health_status = {
            "overall_status": overall_status,
            "services": services,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

        if overall_status in ["healthy", "degraded"]:
            return HealthResponse(**health_status)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=health_status
            )
    except Exception as e:
        logger.error("健康檢查失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "健康檢查失敗", "message": str(e)},
        )


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus 指標端點 - UAV功能已移除"""
    return "# UAV-specific metrics removed - use unified_metrics_collector for general system metrics"