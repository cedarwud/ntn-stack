"""
MongoDB 配置模組
提供 MongoDB 客戶端連接和配置管理
"""
import logging
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class MongoDBConfig:
    """MongoDB 配置類"""
    
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://netstack-mongo:27017")
        self.database_name = os.getenv("MONGODB_DATABASE", "simworld")
        self.client: Optional[AsyncIOMotorClient] = None
        
    async def connect(self) -> AsyncIOMotorClient:
        """建立 MongoDB 連接"""
        if self.client is None:
            try:
                logger.info(f"Connecting to MongoDB at {self.mongodb_url}")
                self.client = AsyncIOMotorClient(self.mongodb_url)
                # 測試連接
                await self.client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                self.client = None
                raise
        return self.client
    
    async def disconnect(self):
        """關閉 MongoDB 連接"""
        if self.client:
            logger.info("Closing MongoDB connection")
            self.client.close()
            self.client = None
    
    def get_database(self):
        """獲取數據庫實例"""
        if self.client is None:
            raise RuntimeError("MongoDB client not connected. Call connect() first.")
        return self.client[self.database_name]

# 全局 MongoDB 配置實例
mongodb_config = MongoDBConfig()

async def get_mongodb_client() -> AsyncIOMotorClient:
    """獲取 MongoDB 客戶端"""
    return await mongodb_config.connect()

async def get_mongodb_database():
    """獲取 MongoDB 數據庫"""
    client = await get_mongodb_client()
    return client[mongodb_config.database_name]