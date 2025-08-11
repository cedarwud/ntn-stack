from typing import Optional, AsyncGenerator
from fastapi import Request
from redis.asyncio import Redis as AsyncRedis
from motor.motor_asyncio import AsyncIOMotorDatabase

# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# MongoDB 依賴
from app.db.mongodb_config import get_mongodb_database

# PostgreSQL 依賴已移除，改用 MongoDB
# from app.db.postgresql_config import get_postgresql_connection
# from app.core.config import DATABASE_URL

# Create async engine for SQLAlchemy - PostgreSQL 已移除
# engine = create_async_engine(DATABASE_URL, echo=False, future=True)
# async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# async def get_postgresql_db():
#     """獲取 PostgreSQL 數據庫連接 (asyncpg style)"""
#     return await get_postgresql_connection()


# async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
#     """獲取 SQLAlchemy AsyncSession"""
#     async with async_session_factory() as session:
#         try:
#             yield session
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()


async def get_redis_client(request: Request) -> Optional[AsyncRedis]:
    """獲取 Redis 客戶端"""
    if hasattr(request.app.state, "redis") and request.app.state.redis:
        return request.app.state.redis
    return None


async def get_mongodb_db() -> AsyncIOMotorDatabase:
    """獲取 MongoDB 數據庫連接"""
    return await get_mongodb_database()
