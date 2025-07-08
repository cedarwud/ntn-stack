"""
NetStack API 適配器管理器
負責統一管理所有適配器的生命週期和連接狀態
"""

import os
import structlog
from typing import Tuple, Dict, Any, Optional

# 適配器導入
from ...adapters.mongo_adapter import MongoAdapter
from ...adapters.redis_adapter import RedisAdapter
from ...adapters.open5gs_adapter import Open5GSAdapter

logger = structlog.get_logger(__name__)


class AdapterManager:
    """
    適配器管理器
    負責適配器的初始化、連接、健康檢查和清理
    """

    def __init__(self):
        """初始化適配器管理器"""
        self.mongo_adapter: Optional[MongoAdapter] = None
        self.redis_adapter: Optional[RedisAdapter] = None
        self.open5gs_adapter: Optional[Open5GSAdapter] = None
        self.connection_status = {}

    async def initialize(self) -> Tuple[MongoAdapter, RedisAdapter, Open5GSAdapter]:
        """
        初始化所有適配器

        Returns:
            Tuple[MongoAdapter, RedisAdapter, Open5GSAdapter]: 初始化完成的適配器實例
        """
        logger.info("🔧 開始初始化適配器...")

        try:
            # 從環境變數獲取配置
            config = self._load_configuration()

            # 初始化適配器實例
            await self._initialize_mongo_adapter(config)
            await self._initialize_redis_adapter(config)
            await self._initialize_open5gs_adapter(config)

            # 驗證所有連接
            await self._verify_connections()

            logger.info("✅ 所有適配器初始化完成")

            # 斷言確保類型正確
            assert self.mongo_adapter is not None
            assert self.redis_adapter is not None
            assert self.open5gs_adapter is not None

            return self.mongo_adapter, self.redis_adapter, self.open5gs_adapter

        except Exception as e:
            logger.error("💥 適配器初始化失敗", error=str(e))
            await self.cleanup()
            raise

    def _load_configuration(self) -> Dict[str, str]:
        """
        從環境變數載入配置

        Returns:
            Dict[str, str]: 配置字典
        """
        config = {
            "mongo_url": os.getenv("DATABASE_URL", "mongodb://mongo:27017/open5gs"),
            "redis_url": os.getenv("REDIS_URL", "redis://redis:6379"),
            "mongo_host": os.getenv("MONGO_HOST", "mongo"),
            "mongo_port": int(os.getenv("MONGO_PORT", "27017")),
            "redis_host": os.getenv("REDIS_HOST", "redis"),
            "redis_port": int(os.getenv("REDIS_PORT", "6379")),
        }

        logger.info(
            "📋 載入適配器配置",
            config={
                k: v
                for k, v in config.items()
                if not any(
                    sensitive in k.lower() for sensitive in ["password", "token", "key"]
                )
            },
        )

        return config

    async def _initialize_mongo_adapter(self, config: Dict[str, str]) -> None:
        """
        初始化 MongoDB 適配器

        Args:
            config: 配置字典
        """
        logger.info("🍃 初始化 MongoDB 適配器...")

        try:
            # 動態建立 MongoDB 連接字串，優先使用 .env 中的設定
            mongo_host = config.get("mongo_host", "mongo")
            mongo_port = config.get("mongo_port", 27017)
            # 從原始 mongo_url 中提取數據庫名稱，並處理 None 的情況
            mongo_url = config.get("mongo_url")
            db_name = mongo_url.split("/")[-1] if mongo_url else "open5gs"

            connection_string = f"mongodb://{mongo_host}:{mongo_port}/{db_name}"

            logger.info("🔧 使用動態連接字串", connection_string=connection_string)

            self.mongo_adapter = MongoAdapter(connection_string)
            await self.mongo_adapter.connect()

            self.connection_status["mongo"] = {
                "status": "connected",
                "url": connection_string,
                "adapter_type": "MongoAdapter",
            }

            logger.info("✅ MongoDB 適配器初始化完成")

        except Exception as e:
            # 在失敗時也使用動態生成的 URL，以便於除錯
            mongo_host = config.get("mongo_host", "mongo")
            mongo_port = config.get("mongo_port", 27017)
            mongo_url = config.get("mongo_url")
            db_name = mongo_url.split("/")[-1] if mongo_url else "open5gs"
            failed_url = f"mongodb://{mongo_host}:{mongo_port}/{db_name}"

            self.connection_status["mongo"] = {
                "status": "failed",
                "error": str(e),
                "url": failed_url,
            }
            logger.error("💥 MongoDB 適配器初始化失敗", error=str(e))
            raise

    async def _initialize_redis_adapter(self, config: Dict[str, Any]) -> None:
        """
        初始化 Redis 適配器

        Args:
            config: 配置字典
        """
        logger.info("🔴 初始化 Redis 適配器...")

        try:
            # 動態建立 Redis 連接字串
            redis_host = config.get("redis_host", "redis")
            redis_port = config.get("redis_port", 6379)
            connection_string = f"redis://{redis_host}:{redis_port}"

            logger.info(
                "🔧 使用 Redis 動態連接字串", connection_string=connection_string
            )

            self.redis_adapter = RedisAdapter(connection_string)
            await self.redis_adapter.connect()

            self.connection_status["redis"] = {
                "status": "connected",
                "url": connection_string,
                "adapter_type": "RedisAdapter",
            }

            logger.info("✅ Redis 適配器初始化完成")

        except Exception as e:
            redis_host = config.get("redis_host", "redis")
            redis_port = config.get("redis_port", 6379)
            failed_url = f"redis://{redis_host}:{redis_port}"

            self.connection_status["redis"] = {
                "status": "failed",
                "error": str(e),
                "url": failed_url,
            }
            logger.error("💥 Redis 適配器初始化失敗", error=str(e))
            raise

    async def _initialize_open5gs_adapter(self, config: Dict[str, str]) -> None:
        """
        初始化 Open5GS 適配器

        Args:
            config: 配置字典
        """
        logger.info("📡 初始化 Open5GS 適配器...")

        try:
            self.open5gs_adapter = Open5GSAdapter(
                mongo_host=config["mongo_host"], mongo_port=int(config["mongo_port"])
            )

            # Open5GSAdapter 沒有 connect 方法，直接標記為已連接
            self.connection_status["open5gs"] = {
                "status": "connected",
                "host": config["mongo_host"],
                "port": config["mongo_port"],
                "adapter_type": "Open5GSAdapter",
                "note": "No explicit connection method",
            }

            logger.info("✅ Open5GS 適配器初始化完成")

        except Exception as e:
            self.connection_status["open5gs"] = {
                "status": "failed",
                "error": str(e),
                "host": config["mongo_host"],
                "port": config["mongo_port"],
            }
            logger.error("💥 Open5GS 適配器初始化失敗", error=str(e))
            raise

    async def _verify_connections(self) -> None:
        """驗證所有適配器連接狀態"""
        logger.info("🔍 驗證適配器連接狀態...")

        failed_adapters = []

        for adapter_name, status in self.connection_status.items():
            if status["status"] != "connected":
                failed_adapters.append(adapter_name)

        if failed_adapters:
            raise Exception(f"適配器連接失敗: {', '.join(failed_adapters)}")

        logger.info("✅ 所有適配器連接驗證通過")

        # 為了類型檢查，確認所有適配器都已初始化
        assert self.mongo_adapter is not None, "MongoAdapter 未初始化"
        assert self.redis_adapter is not None, "RedisAdapter 未初始化"
        assert self.open5gs_adapter is not None, "Open5GSAdapter 未初始化"

    async def cleanup(self) -> None:
        """
        清理所有適配器連接
        """
        logger.info("🧹 開始清理適配器連接...")

        cleanup_results = {}

        # 清理 MongoDB 適配器
        if self.mongo_adapter:
            try:
                await self.mongo_adapter.disconnect()
                cleanup_results["mongo"] = "success"
                logger.info("✅ MongoDB 適配器已斷開")
            except Exception as e:
                cleanup_results["mongo"] = f"error: {str(e)}"
                logger.error("💥 MongoDB 適配器清理失敗", error=str(e))

        # 清理 Redis 適配器
        if self.redis_adapter:
            try:
                await self.redis_adapter.disconnect()
                cleanup_results["redis"] = "success"
                logger.info("✅ Redis 適配器已斷開")
            except Exception as e:
                cleanup_results["redis"] = f"error: {str(e)}"
                logger.error("💥 Redis 適配器清理失敗", error=str(e))

        # Open5GS 適配器沒有 disconnect 方法
        if self.open5gs_adapter:
            cleanup_results["open5gs"] = "no disconnect method"
            logger.info("ℹ️ Open5GS 適配器無需斷開連接")

        logger.info("🎉 適配器清理完成", results=cleanup_results)

    async def health_check(self) -> Dict[str, Any]:
        """
        執行適配器健康檢查

        Returns:
            Dict[str, Any]: 健康檢查結果
        """
        logger.info("🏥 執行適配器健康檢查...")

        health_results = {}

        # MongoDB 健康檢查
        if self.mongo_adapter:
            health_results["mongo"] = await self.mongo_adapter.health_check()
        else:
            health_results["mongo"] = {
                "status": "not_initialized",
                "error": "適配器未初始化",
            }

        # Redis 健康檢查
        if self.redis_adapter:
            health_results["redis"] = await self.redis_adapter.health_check()
        else:
            health_results["redis"] = {
                "status": "not_initialized",
                "error": "適配器未初始化",
            }

        # Open5GS 健康檢查（基於初始化狀態）
        if self.open5gs_adapter:
            health_results["open5gs"] = {
                "status": "assumed_healthy",
                "note": "無直接健康檢查方法",
            }
        else:
            health_results["open5gs"] = {
                "status": "not_initialized",
                "error": "適配器未初始化",
            }

        # 計算整體健康狀態
        healthy_count = sum(
            1
            for result in health_results.values()
            if result.get("status") in ["healthy", "assumed_healthy"]
        )
        total_count = len(health_results)

        overall_status = {
            "overall_health": "healthy" if healthy_count == total_count else "degraded",
            "healthy_adapters": healthy_count,
            "total_adapters": total_count,
            "health_percentage": (healthy_count / total_count) * 100,
            "adapters": health_results,
        }

        logger.info(
            f"🏥 健康檢查完成: {healthy_count}/{total_count} 適配器健康",
            overall_status=overall_status["overall_health"],
        )

        return overall_status

    def get_connection_status(self) -> Dict[str, Any]:
        """
        獲取連接狀態摘要

        Returns:
            Dict[str, Any]: 連接狀態摘要
        """
        return {
            "connection_status": self.connection_status,
            "initialized_adapters": {
                "mongo": self.mongo_adapter is not None,
                "redis": self.redis_adapter is not None,
                "open5gs": self.open5gs_adapter is not None,
            },
            "summary": {
                "total_adapters": 3,
                "connected_adapters": len(
                    [
                        s
                        for s in self.connection_status.values()
                        if s.get("status") == "connected"
                    ]
                ),
            },
        }
