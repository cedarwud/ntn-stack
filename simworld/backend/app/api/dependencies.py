from typing import Optional
from fastapi import Request
from redis.asyncio import Redis as AsyncRedis

from app.db.mongodb_config import get_mongodb_database


async def get_mongodb_db():
    """獲取 MongoDB 數據庫實例"""
    return await get_mongodb_database()


async def get_redis_client(request: Request) -> Optional[AsyncRedis]:
    """獲取 Redis 客戶端"""
    if hasattr(request.app.state, "redis") and request.app.state.redis:
        return request.app.state.redis
    return None
