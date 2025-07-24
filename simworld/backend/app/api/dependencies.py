from typing import Optional
from fastapi import Request
from redis.asyncio import Redis as AsyncRedis

from app.db.postgresql_config import get_postgresql_connection


async def get_postgresql_db():
    """獲取 PostgreSQL 數據庫連接"""
    return await get_postgresql_connection()


async def get_redis_client(request: Request) -> Optional[AsyncRedis]:
    """獲取 Redis 客戶端"""
    if hasattr(request.app.state, "redis") and request.app.state.redis:
        return request.app.state.redis
    return None
