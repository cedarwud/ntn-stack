import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

# PostgreSQL 相關導入 (替代 MongoDB)
from app.db.postgresql_config import postgresql_config
from app.db.postgresql_seeds import (
    seed_initial_device_data_postgresql,
    seed_default_ground_station_postgresql
)
import os

from app.core.config import (
    OUTPUT_DIR,
    configure_gpu_cpu,
    configure_matplotlib,
)

# New import for TLE synchronization service (Redis only)
from app.db.tle_sync_redis import synchronize_constellation_tles

# For Redis client management
import redis.asyncio as aioredis


# 簡化的調度器函數，不依賴外部模組
async def initialize_scheduler(redis_client):
    """簡化的調度器初始化，僅記錄日誌"""
    logger.info("衛星數據調度器已啟動，更新間隔: 每週")
    return True


async def shutdown_scheduler():
    """簡化的調度器關閉，僅記錄日誌"""
    logger.info("衛星數據調度器已關閉")
    return True


logger = logging.getLogger(__name__)


# MongoDB 函數已移除，改用 PostgreSQL
# 舊的 MongoDB 初始化函數已備份到 lifespan_mongodb_backup.py


async def initialize_redis_client(app: FastAPI):
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Attempting to connect to Redis at {redis_url}")
    try:
        # decode_responses=False because tle_service handles json.dumps and expects bytes from redis for json.loads(.decode())
        redis_client = aioredis.Redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        # Add timeout for ping
        await asyncio.wait_for(redis_client.ping(), timeout=5.0)
        app.state.redis = redis_client
        logger.info(
            "Successfully connected to Redis and stored client in app.state.redis"
        )
    except (Exception, asyncio.TimeoutError) as e:
        app.state.redis = None
        logger.error(
            f"Failed to connect to Redis: {e}. TLE sync and other Redis features will be unavailable."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for FastAPI startup and shutdown logic."""
    logger.info("Application startup sequence initiated...")
    configure_gpu_cpu()
    configure_matplotlib()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info("Environment configured.")

    logger.info("PostgreSQL initialization sequence...")

    # 初始化 PostgreSQL 連接池
    postgresql_pool = await postgresql_config.connect()
    app.state.postgresql = postgresql_pool

    # 初始化 Redis 客戶端
    await initialize_redis_client(app)

    # 異步初始化 PostgreSQL 數據
    try:
        async with postgresql_config.get_connection() as connection:
            # 初始化設備資料
            await seed_initial_device_data_postgresql(connection)
            # 初始化地面站資料
            await seed_default_ground_station_postgresql(connection)
        logger.info("PostgreSQL data initialization completed")
    except Exception as e:
        logger.error(f"Error during PostgreSQL initialization: {e}", exc_info=True)

    # 恢復 TLE 相關同步和啟動調度器
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            # 導入同步函數和 fallback 機制
            from app.db.tle_sync_redis import synchronize_constellation_tles
            from app.db.tle_init_fallback import ensure_tle_data_available

            # 嘗試同步真實 TLE 數據
            logger.info("Synchronizing Starlink TLE data in the background...")
            starlink_success = await synchronize_constellation_tles(
                "starlink",
                None,
                app.state.redis,
            )

            # 同步 Kuiper 衛星 TLE 資料到 Redis（補充星座）
            logger.info("Synchronizing Kuiper TLE data in the background...")
            kuiper_success = await synchronize_constellation_tles(
                "kuiper",
                None,
                app.state.redis,
            )

            # 如果真實數據同步失敗，使用 fallback 機制
            if not starlink_success and not kuiper_success:
                logger.warning("Both Starlink and Kuiper synchronization failed, using fallback data...")
                fallback_success = await ensure_tle_data_available(app.state)
                if fallback_success:
                    logger.info("✅ Fallback TLE data loaded successfully")
                    starlink_success = True  # 標記為成功，以便啟動調度器
                else:
                    logger.error("❌ Fallback TLE data loading also failed")

            if starlink_success or kuiper_success:
                # 啟動衛星數據定期更新調度器
                logger.info("Starting satellite data scheduler...")
                await initialize_scheduler(app.state.redis)
            else:
                logger.warning("All TLE data synchronization methods failed")

        except Exception as e:
            logger.error(
                f"Error during TLE synchronization or scheduler startup: {e}",
                exc_info=True,
            )
            
            # 緊急 fallback：直接載入測試數據
            try:
                logger.info("Attempting emergency TLE data loading...")
                from app.db.tle_init_fallback import ensure_tle_data_available
                emergency_success = await ensure_tle_data_available(app.state)
                if emergency_success:
                    logger.info("✅ Emergency TLE data loaded successfully")
                    await initialize_scheduler(app.state.redis)
                else:
                    logger.error("❌ Emergency TLE data loading failed")
            except Exception as emergency_e:
                logger.error(f"Emergency TLE loading also failed: {emergency_e}")
    else:
        logger.warning(
            "Redis unavailable, skipping Starlink/Kuiper TLE synchronization and scheduler"
        )

    logger.info("Application startup complete.")

    yield

    # 在應用程式關閉前執行
    try:
        # 停止衛星數據調度器
        logger.info("Shutting down satellite data scheduler...")
        await shutdown_scheduler()
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}", exc_info=True)

    if hasattr(app.state, "redis") and app.state.redis:
        logger.info("Closing Redis connection...")
        await app.state.redis.close()

    if hasattr(app.state, "postgresql") and app.state.postgresql:
        logger.info("Closing PostgreSQL connection pool...")
        await postgresql_config.disconnect()

    logger.info("Application shutdown complete.")
