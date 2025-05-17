from typing import AsyncGenerator, Optional
from fastapi import Request, HTTPException  # Added HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis as AsyncRedis

from app.db.base import async_session_maker  # Your existing session maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_redis_client(request: Request) -> Optional[AsyncRedis]:  # Return Optional
    if hasattr(request.app.state, "redis") and request.app.state.redis:
        return request.app.state.redis
    # If Redis is critical for an endpoint, the endpoint should check and raise HTTPException
    # Or raise it here if Redis is always expected to be available.
    # logger.warning("Redis client not found in app.state.redis") # Optional logging
    return None  # Allow services to handle None redis client if they can partially function
