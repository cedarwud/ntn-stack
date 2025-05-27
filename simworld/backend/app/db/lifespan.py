import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Ensure SQLModel specific imports are correctly managed if you mix ORMs
from sqlmodel import (
    SQLModel,
    select as sqlmodel_select,
)  # SQLModel used for Device model
from sqlalchemy.sql.functions import count
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sqlalchemy_select  # For SQLAlchemy models

from app.db.base import engine, async_session_maker

# 更新為領域驅動設計後的模型導入
from app.domains.device.models.device_model import Device, DeviceRole  # 從領域模型導入

# 取消註釋 ground_station 相關導入
from app.domains.satellite.models.ground_station_model import (
    GroundStation,
)  # 從領域模型導入
from app.domains.satellite.models.dto import GroundStationCreate  # 新的 DTO 路徑

from app.core.config import (
    OUTPUT_DIR,
    configure_gpu_cpu,
    configure_matplotlib,
)
import os

# import numpy as np # numpy seems unused directly in this file now

# New import for TLE synchronization service
from app.domains.satellite.services.tle_service import synchronize_oneweb_tles

# For Redis client management
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


async def create_db_and_tables():
    """Creates database tables if they don't exist."""
    async with engine.begin() as conn:
        logger.info("Creating database tables...")
        # This will create tables for all models registered with SQLModel.metadata
        # AND tables for models registered with SQLAlchemy Base.metadata if they share the same engine connection strategy
        # Ensure SatelliteTLE and GroundStation (SQLAlchemy Base) are covered.
        # If they use a different Base.metadata, that needs to be created too.
        # For simplicity, assuming all tables are findable via engine used by SQLModel or share metadata.
        # The `app.db.base.py` imports SatelliteTLE and GroundStation, making them known to `Base.metadata`
        # if `Base` is the SQLAlchemy declarative_base they inherit from.
        # If `SQLModel.metadata` is separate, tables for SatelliteTLE and GroundStation also need creation here.
        # Assuming they are part of the same metadata scope that `engine` is aware of.
        # The `app.db.base_class.Base` is the SQLAlchemy declarative base.
        from app.db.base_class import Base as SQLAlchemyBase

        await conn.run_sync(
            SQLAlchemyBase.metadata.create_all
        )  # Creates SatelliteTLE, GroundStation tables
        await conn.run_sync(
            SQLModel.metadata.create_all
        )  # Creates Device table (and any other SQLModels)
        logger.info("Database tables created (if they didn't exist).")


async def seed_default_ground_station(session: AsyncSession):
    """Seeds a default ground station if it doesn't exist."""
    # 還原種子數據函數內容
    logger.info("Checking if default ground station 'NYCU_gnb' needs to be seeded...")
    stmt = sqlalchemy_select(GroundStation).where(
        GroundStation.station_identifier == "NYCU_gnb"
    )
    result = await session.execute(stmt)
    existing_station = result.scalar_one_or_none()

    if existing_station:
        logger.info(
            f"Default ground station 'NYCU_gnb' already exists with id {existing_station.id}. Skipping seeding."
        )
    else:
        logger.info("Default ground station 'NYCU_gnb' not found. Seeding...")
        default_station_data = GroundStationCreate(
            station_identifier="NYCU_gnb",
            name="NYCU Main gNB",
            latitude_deg=24.786667,
            longitude_deg=120.996944,
            altitude_m=100.0,
            description="Default Ground Station at National Yang Ming Chiao Tung University",
        )
        # We need to create an instance of the DB model GroundStation
        db_station = GroundStation(**default_station_data.model_dump())
        try:
            session.add(db_station)
            await session.commit()
            await session.refresh(
                db_station
            )  # To get the auto-generated ID if needed later
            logger.info(
                f"Successfully seeded default ground station 'NYCU_gnb' with id {db_station.id}."
            )
        except Exception as e:
            await session.rollback()
            logger.error(
                f"Error seeding default ground station 'NYCU_gnb': {e}", exc_info=True
            )


async def seed_initial_device_data(session: AsyncSession):
    """Inserts initial device data if minimum roles (TX, RX, JAM) are not met."""
    logger.info("Checking if initial data seeding is needed for Devices...")

    query_desired = sqlmodel_select(count(Device.id)).where(
        Device.active == True, Device.role == DeviceRole.DESIRED
    )
    query_receiver = sqlmodel_select(count(Device.id)).where(
        Device.active == True, Device.role == DeviceRole.RECEIVER
    )
    query_jammer = sqlmodel_select(count(Device.id)).where(
        Device.active == True, Device.role == DeviceRole.JAMMER
    )

    result_desired = await session.execute(query_desired)
    result_receiver = await session.execute(query_receiver)
    result_jammer = await session.execute(query_jammer)

    desired_count = result_desired.scalar_one_or_none() or 0
    receiver_count = result_receiver.scalar_one_or_none() or 0
    jammer_count = result_jammer.scalar_one_or_none() or 0

    if desired_count > 0 and receiver_count > 0 and jammer_count > 0:
        logger.info(
            f"Device Database already contains active TX ({desired_count}), RX ({receiver_count}), Jammer ({jammer_count}). Skipping Device seeding."
        )
        return

    logger.info(
        f"Minimum Device role requirement not met. Seeding initial Device data..."
    )
    try:
        logger.info("Deleting existing Devices before reseeding...")
        select_existing_stmt = sqlmodel_select(Device)
        existing_devices_result = await session.execute(select_existing_stmt)
        deleted_count = 0
        for dev_instance in existing_devices_result.scalars().all():
            await session.delete(dev_instance)
            deleted_count += 1

        if deleted_count > 0:
            await session.commit()  # Commit deletions first
            logger.info(f"Committed deletion of {deleted_count} existing devices.")
        else:
            logger.info("No existing devices found to delete prior to seeding.")

        # Now add new devices
        tx_list = [
            ("tx0", [-110, -110, 40], [2.61799387799, 0, 0], "desired", 30),
            ("tx1", [-106, 56, 61], [0.52359877559, 0, 0], "desired", 30),
            ("tx2", [100, -30, 40], [-1.57079632679, 0, 0], "desired", 30),
            ("jam1", [100, 60, 40], [1.57079632679, 0, 0], "jammer", 40),
            ("jam2", [-30, 53, 67], [1.57079632679, 0, 0], "jammer", 40),
            ("jam3", [-105, -31, 64], [1.57079632679, 0, 0], "jammer", 40),
        ]
        # Correcting the role for 'rx' device as per observation from logs/common sense.
        # The log showed 'jammer' for 'rx', which is unusual for a device named 'rx'.
        # Assuming 'rx' should be a 'receiver'. If it's intended to be a 'jammer', this change is incorrect.
        rx_config = (
            "rx",
            [0, 0, 40],
            [0, 0, 0],
            "receiver",
            0,
        )  # Changed role to "receiver"

        devices_to_add = []
        for tx_name, position, orientation, role_str, power_dbm in tx_list:
            device = Device(
                name=tx_name,
                position_x=position[0],
                position_y=position[1],
                position_z=position[2],
                orientation_x=orientation[0],
                orientation_y=orientation[1],
                orientation_z=orientation[2],
                role=DeviceRole(role_str),
                power_dbm=power_dbm,
                active=True,
            )
            devices_to_add.append(device)

        rx_name, rx_position, rx_orientation, rx_role_str, rx_power_dbm = rx_config
        rx_device = Device(
            name=rx_name,
            position_x=rx_position[0],
            position_y=rx_position[1],
            position_z=rx_position[2],
            orientation_x=rx_orientation[0],
            orientation_y=rx_orientation[1],
            orientation_z=rx_orientation[2],
            role=DeviceRole(rx_role_str),  # Role will now be DeviceRole.RECEIVER
            power_dbm=rx_power_dbm,
            active=True,
        )
        devices_to_add.append(rx_device)

        logger.info(f"Attempting to add {len(devices_to_add)} new devices.")
        for dev_to_add in devices_to_add:
            session.add(dev_to_add)

        await session.commit()  # Commit additions
        logger.info(
            f"Successfully initialized {len(devices_to_add)} Devices into the database."
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error seeding initial Device data: {e}", exc_info=True)


async def initialize_redis_client(app: FastAPI):
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Attempting to connect to Redis at {redis_url}")
    try:
        # decode_responses=False because tle_service handles json.dumps and expects bytes from redis for json.loads(.decode())
        redis_client = aioredis.Redis.from_url(
            redis_url, encoding="utf-8", decode_responses=False
        )
        await redis_client.ping()
        app.state.redis = redis_client
        logger.info(
            "Successfully connected to Redis and stored client in app.state.redis"
        )
    except Exception as e:
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

    logger.info("Database initialization sequence...")
    await create_db_and_tables()

    await initialize_redis_client(app)

    # 異步初始化資料庫
    async with async_session_maker() as db_session:
        # 初始化設備資料
        await seed_initial_device_data(db_session)
        # 恢復地面站相關初始化
        await seed_default_ground_station(db_session)

    # 恢復 TLE 相關同步
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            # 自動同步 OneWeb TLE 資料
            logger.info("Synchronizing OneWeb TLE data in the background...")
            await synchronize_oneweb_tles(async_session_maker, app.state.redis)
        except Exception as e:
            logger.error(f"Error during OneWeb TLE synchronization: {e}", exc_info=True)
    else:
        logger.warning("Redis unavailable, skipping OneWeb TLE synchronization")

    logger.info("Application startup complete.")

    yield

    # 在應用程式關閉前執行
    if hasattr(app.state, "redis") and app.state.redis:
        logger.info("Closing Redis connection...")
        await app.state.redis.close()

    logger.info("Application shutdown complete.")
