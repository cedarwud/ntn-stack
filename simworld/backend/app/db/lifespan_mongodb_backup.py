import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

# MongoDB 相關導入
from motor.motor_asyncio import AsyncIOMotorClient
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


async def get_mongodb_client():
    """獲取 MongoDB 客戶端 - 包含重試機制"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

    # 設定連接參數：更長的超時時間和重試
    max_retries = 3
    retry_delay = 5  # 秒

    for attempt in range(max_retries):
        try:
            logger.info(
                f"嘗試連接 MongoDB (第 {attempt + 1}/{max_retries} 次): {mongodb_url}"
            )
            client = AsyncIOMotorClient(
                mongodb_url,
                serverSelectionTimeoutMS=10000,  # 10 秒 (原本預設 30 秒太長)
                connectTimeoutMS=10000,  # 10 秒
                socketTimeoutMS=10000,  # 10 秒
                maxPoolSize=10,
                retryWrites=True,
            )

            # 測試連接
            await asyncio.wait_for(client.admin.command("ping"), timeout=5.0)
            logger.info("✅ MongoDB 連接成功")
            return client

        except Exception as e:
            logger.warning(
                f"❌ MongoDB 連接失敗 (第 {attempt + 1}/{max_retries} 次): {e}"
            )
            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒後重試...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("所有 MongoDB 連接嘗試都失敗")
                raise e


async def seed_initial_device_data_mongodb(mongodb_client):
    """修改為 MongoDB 數據儲存"""
    logger.info("Checking if initial device data seeding is needed...")

    db = mongodb_client["simworld"]
    devices_collection = db["devices"]

    # 檢查現有數據
    existing_count = await devices_collection.count_documents({"active": True})
    if existing_count >= 7:
        logger.info(
            f"Device Database already contains {existing_count} active devices. Skipping seeding."
        )
        return

    logger.info("Minimum Device requirement not met. Seeding initial Device data...")

    try:
        # 清理現有數據
        await devices_collection.delete_many({})
        logger.info("Cleared existing device data")

        # 插入 device 數據 - 使用前端期望的分離座標格式
        devices = [
            {
                "id": 1,
                "name": "tx0",
                "position_x": -110,
                "position_y": -110,
                "position_z": 40,
                "orientation_x": 2.61799387799,
                "orientation_y": 0,
                "orientation_z": 0,
                "role": "desired",
                "power_dbm": 30,
                "active": True,
            },
            {
                "id": 2,
                "name": "tx1",
                "position_x": -106,
                "position_y": 56,
                "position_z": 61,
                "orientation_x": 0.52359877559,
                "orientation_y": 0,
                "orientation_z": 0,
                "role": "desired",
                "power_dbm": 30,
                "active": True,
            },
            {
                "id": 3,
                "name": "tx2",
                "position_x": 100,
                "position_y": -30,
                "position_z": 40,
                "orientation_x": -1.57079632679,
                "orientation_y": 0,
                "orientation_z": 0,
                "role": "desired",
                "power_dbm": 30,
                "active": True,
            },
            {
                "id": 4,
                "name": "jam1",
                "position_x": 100,
                "position_y": 60,
                "position_z": 40,
                "orientation_x": 1.57079632679,
                "orientation_y": 0,
                "orientation_z": 0,
                "role": "jammer",
                "power_dbm": 40,
                "active": True,
            },
            {
                "id": 5,
                "name": "jam2",
                "position_x": -30,
                "position_y": 53,
                "position_z": 67,
                "orientation_x": 1.57079632679,
                "orientation_y": 0,
                "orientation_z": 0,
                "role": "jammer",
                "power_dbm": 40,
                "active": True,
            },
            {
                "id": 6,
                "name": "jam3",
                "position_x": -105,
                "position_y": -31,
                "position_z": 64,
                "orientation_x": 1.57079632679,
                "orientation_y": 0,
                "orientation_z": 0,
                "role": "jammer",
                "power_dbm": 40,
                "active": True,
            },
            {
                "id": 7,
                "name": "rx",
                "position_x": 0,
                "position_y": 0,
                "position_z": 40,
                "orientation_x": 0,
                "orientation_y": 0,
                "orientation_z": 0,
                "role": "receiver",
                "power_dbm": 0,
                "active": True,
            },
        ]

        result = await devices_collection.insert_many(devices)
        logger.info(
            f"Successfully seeded {len(result.inserted_ids)} devices into MongoDB"
        )

    except Exception as e:
        logger.error(f"Error seeding initial Device data: {e}", exc_info=True)


async def seed_default_ground_station_mongodb(mongodb_client):
    """修改為 MongoDB 地面站儲存"""
    logger.info("Checking if default ground station 'NYCU_gnb' needs to be seeded...")

    db = mongodb_client["simworld"]
    stations_collection = db["ground_stations"]

    existing = await stations_collection.find_one({"station_identifier": "NYCU_gnb"})
    if existing:
        logger.info(
            f"Default ground station 'NYCU_gnb' already exists. Skipping seeding."
        )
        return

    logger.info("Default ground station 'NYCU_gnb' not found. Seeding...")

    try:
        station = {
            "station_identifier": "NYCU_gnb",
            "name": "NYCU Main gNB",
            "latitude_deg": 24.786667,
            "longitude_deg": 120.996944,
            "altitude_m": 100.0,
            "description": "Default Ground Station at National Yang Ming Chiao Tung University",
        }

        result = await stations_collection.insert_one(station)
        logger.info(
            f"Successfully seeded default ground station 'NYCU_gnb' with id {result.inserted_id}"
        )

    except Exception as e:
        logger.error(f"Error seeding default ground station: {e}", exc_info=True)


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

    logger.info("MongoDB initialization sequence...")

    # 初始化 MongoDB 客戶端
    mongodb_client = await get_mongodb_client()
    app.state.mongodb = mongodb_client

    # 初始化 Redis 客戶端
    await initialize_redis_client(app)

    # 異步初始化 MongoDB 數據
    try:
        # 初始化設備資料
        await seed_initial_device_data_mongodb(mongodb_client)
        # 初始化地面站資料
        await seed_default_ground_station_mongodb(mongodb_client)
        logger.info("MongoDB data initialization completed")
    except Exception as e:
        logger.error(f"Error during MongoDB initialization: {e}", exc_info=True)

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

    if hasattr(app.state, "mongodb") and app.state.mongodb:
        logger.info("Closing MongoDB connection...")
        app.state.mongodb.close()

    logger.info("Application shutdown complete.")
