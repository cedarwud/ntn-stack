"""
MongoDB 配置和連接管理
"""

import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# 全局變量來保存 MongoDB 客戶端
_mongodb_client = None
_mongodb_database = None


async def get_mongodb_client() -> AsyncIOMotorClient:
    """獲取 MongoDB 客戶端"""
    global _mongodb_client

    if _mongodb_client is None:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        logger.info(f"Connecting to MongoDB at {mongodb_url}")
        _mongodb_client = AsyncIOMotorClient(mongodb_url)

    return _mongodb_client


async def get_mongodb_database() -> AsyncIOMotorDatabase:
    """獲取 MongoDB 數據庫"""
    global _mongodb_database

    if _mongodb_database is None:
        client = await get_mongodb_client()
        database_name = os.getenv("MONGODB_DATABASE", "satellite_db")
        _mongodb_database = client[database_name]
        logger.info(f"Using MongoDB database: {database_name}")

    return _mongodb_database


async def close_mongodb_connection():
    """關閉 MongoDB 連接"""
    global _mongodb_client, _mongodb_database

    if _mongodb_client:
        _mongodb_client.close()
        _mongodb_client = None
        _mongodb_database = None
        logger.info("MongoDB connection closed")


async def initialize_mongodb(app: FastAPI):
    """初始化 MongoDB 連接"""
    try:
        # 測試連接
        client = await get_mongodb_client()
        db = await get_mongodb_database()

        # 嘗試ping數據庫來測試連接
        await client.admin.command("ping")
        logger.info("MongoDB connection established successfully")

        # 將連接存儲到應用狀態
        app.state.mongodb_client = client
        app.state.mongodb_database = db

        return True
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        return False
