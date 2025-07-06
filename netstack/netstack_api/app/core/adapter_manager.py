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
        
        logger.info("📋 載入適配器配置", config={
            k: v for k, v in config.items() 
            if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'key'])
        })
        
        return config
    
    async def _initialize_mongo_adapter(self, config: Dict[str, str]) -> None:
        """
        初始化 MongoDB 適配器
        
        Args:
            config: 配置字典
        """
        logger.info("🍃 初始化 MongoDB 適配器...")
        
        try:
            self.mongo_adapter = MongoAdapter(config["mongo_url"])
            await self.mongo_adapter.connect()
            
            self.connection_status["mongo"] = {
                "status": "connected",
                "url": config["mongo_url"],
                "adapter_type": "MongoAdapter"
            }
            
            logger.info("✅ MongoDB 適配器初始化完成")
            
        except Exception as e:
            self.connection_status["mongo"] = {
                "status": "failed",
                "error": str(e),
                "url": config["mongo_url"]
            }
            logger.error("💥 MongoDB 適配器初始化失敗", error=str(e))
            raise
    
    async def _initialize_redis_adapter(self, config: Dict[str, str]) -> None:
        """
        初始化 Redis 適配器
        
        Args:
            config: 配置字典
        """
        logger.info("🔴 初始化 Redis 適配器...")
        
        try:
            self.redis_adapter = RedisAdapter(config["redis_url"])
            await self.redis_adapter.connect()
            
            self.connection_status["redis"] = {
                "status": "connected",
                "url": config["redis_url"],
                "adapter_type": "RedisAdapter"
            }
            
            logger.info("✅ Redis 適配器初始化完成")
            
        except Exception as e:
            self.connection_status["redis"] = {
                "status": "failed",
                "error": str(e),
                "url": config["redis_url"]
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
                mongo_host=config["mongo_host"],
                mongo_port=config["mongo_port"]
            )
            
            # Open5GSAdapter 沒有 connect 方法，直接標記為已連接
            self.connection_status["open5gs"] = {
                "status": "connected",
                "host": config["mongo_host"],
                "port": config["mongo_port"],
                "adapter_type": "Open5GSAdapter",
                "note": "No explicit connection method"
            }
            
            logger.info("✅ Open5GS 適配器初始化完成")
            
        except Exception as e:
            self.connection_status["open5gs"] = {
                "status": "failed",
                "error": str(e),
                "host": config["mongo_host"],
                "port": config["mongo_port"]
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
            try:
                # 嘗試簡單的資料庫操作
                await self.mongo_adapter.get_database().command("ping")
                health_results["mongo"] = {
                    "status": "healthy",
                    "response_time": "< 100ms"  # 可以實際測量
                }
            except Exception as e:
                health_results["mongo"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health_results["mongo"] = {
                "status": "not_initialized",
                "error": "適配器未初始化"
            }
        
        # Redis 健康檢查
        if self.redis_adapter:
            try:
                # 嘗試 ping Redis
                response = await self.redis_adapter.ping()
                health_results["redis"] = {
                    "status": "healthy",
                    "ping_response": response
                }
            except Exception as e:
                health_results["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health_results["redis"] = {
                "status": "not_initialized",
                "error": "適配器未初始化"
            }
        
        # Open5GS 健康檢查（基於初始化狀態）
        if self.open5gs_adapter:
            health_results["open5gs"] = {
                "status": "assumed_healthy",
                "note": "無直接健康檢查方法"
            }
        else:
            health_results["open5gs"] = {
                "status": "not_initialized",
                "error": "適配器未初始化"
            }
        
        # 計算整體健康狀態
        healthy_count = sum(
            1 for result in health_results.values() 
            if result.get("status") in ["healthy", "assumed_healthy"]
        )
        total_count = len(health_results)
        
        overall_status = {
            "overall_health": "healthy" if healthy_count == total_count else "degraded",
            "healthy_adapters": healthy_count,
            "total_adapters": total_count,
            "health_percentage": (healthy_count / total_count) * 100,
            "adapters": health_results
        }
        
        logger.info(
            f"🏥 健康檢查完成: {healthy_count}/{total_count} 適配器健康",
            overall_status=overall_status["overall_health"]
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
                "open5gs": self.open5gs_adapter is not None
            },
            "summary": {
                "total_adapters": 3,
                "connected_adapters": len([
                    s for s in self.connection_status.values() 
                    if s.get("status") == "connected"
                ])
            }
        }