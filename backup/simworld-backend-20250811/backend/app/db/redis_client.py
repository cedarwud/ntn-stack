"""
Redis Client Management
Extracted from lifespan.py for unified lifecycle management
"""

import logging
import os
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[aioredis.Redis] = None


async def initialize_redis_client() -> aioredis.Redis:
    """Initialize Redis connection and return the client"""
    global _redis_client
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Attempting to connect to Redis at {redis_url}")
    
    try:
        # decode_responses=False because tle_service handles json.dumps and expects bytes from redis for json.loads(.decode())
        _redis_client = aioredis.Redis.from_url(
            redis_url, encoding="utf-8", decode_responses=False
        )
        await _redis_client.ping()
        logger.info("Successfully connected to Redis")
        return _redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}. TLE sync and other Redis features will be unavailable.")
        _redis_client = None
        raise


async def close_redis_connection():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None


def get_redis_client() -> Optional[aioredis.Redis]:
    """Get the current Redis client instance"""
    return _redis_client


def is_redis_connected() -> bool:
    """Check if Redis client is connected"""
    return _redis_client is not None