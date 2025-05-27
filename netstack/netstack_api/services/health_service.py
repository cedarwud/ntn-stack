"""
健康檢查服務

整合各適配器的健康狀態檢查
"""

from datetime import datetime
from typing import Dict, Any

import structlog

from ..adapters.mongo_adapter import MongoAdapter
from ..adapters.redis_adapter import RedisAdapter

logger = structlog.get_logger(__name__)


class HealthService:
    """健康檢查服務"""

    def __init__(self, mongo_adapter: MongoAdapter, redis_adapter: RedisAdapter):
        """
        初始化健康檢查服務

        Args:
            mongo_adapter: MongoDB 適配器
            redis_adapter: Redis 適配器
        """
        self.mongo_adapter = mongo_adapter
        self.redis_adapter = redis_adapter

    async def check_system_health(self) -> Dict[str, Any]:
        """
        檢查整個系統的健康狀態

        Returns:
            系統健康狀態報告
        """
        try:
            # 檢查各服務健康狀態
            mongo_health = await self.mongo_adapter.health_check()
            redis_health = await self.redis_adapter.health_check()

            # 計算整體健康狀態
            services = {"mongodb": mongo_health, "redis": redis_health}

            # 判斷整體狀態
            healthy_services = sum(
                1 for service in services.values() if service.get("status") == "healthy"
            )

            total_services = len(services)

            if healthy_services == total_services:
                overall_status = "healthy"
            elif healthy_services > 0:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"

            return {
                "overall_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "services": services,
                "healthy_services": healthy_services,
                "total_services": total_services,
                "version": "1.0.0",
            }

        except Exception as e:
            logger.error("系統健康檢查失敗", error=str(e))
            return {
                "overall_status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "version": "1.0.0",
            }

    async def check_database_connectivity(self) -> Dict[str, Any]:
        """
        檢查資料庫連接性

        Returns:
            資料庫連接狀態
        """
        try:
            mongo_health = await self.mongo_adapter.health_check()

            return {
                "status": mongo_health.get("status", "unknown"),
                "response_time": mongo_health.get("response_time", 0),
                "database": mongo_health.get("database", "open5gs"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error("資料庫連接檢查失敗", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def check_cache_connectivity(self) -> Dict[str, Any]:
        """
        檢查快取連接性

        Returns:
            快取連接狀態
        """
        try:
            redis_health = await self.redis_adapter.health_check()

            return {
                "status": redis_health.get("status", "unknown"),
                "response_time": redis_health.get("response_time", 0),
                "version": redis_health.get("version", "unknown"),
                "memory_usage": redis_health.get("memory_usage", "unknown"),
                "connected_clients": redis_health.get("connected_clients", 0),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error("快取連接檢查失敗", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_service_metrics(self) -> Dict[str, Any]:
        """
        取得服務指標

        Returns:
            服務指標資料
        """
        try:
            # 取得 MongoDB 統計
            mongo_health = await self.mongo_adapter.health_check()

            # 取得 Redis 統計
            redis_health = await self.redis_adapter.health_check()

            return {
                "mongodb": {
                    "status": mongo_health.get("status"),
                    "response_time_ms": mongo_health.get("response_time", 0) * 1000,
                    "database": mongo_health.get("database"),
                },
                "redis": {
                    "status": redis_health.get("status"),
                    "response_time_ms": redis_health.get("response_time", 0) * 1000,
                    "memory_usage": redis_health.get("memory_usage"),
                    "connected_clients": redis_health.get("connected_clients"),
                    "version": redis_health.get("version"),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error("取得服務指標失敗", error=str(e))
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
