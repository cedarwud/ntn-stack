import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, select
from sqlalchemy.sql.functions import count
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import engine, async_session_maker
from app.db.models import Device, DeviceRole  # Import necessary models
from app.core.config import (
    OUTPUT_DIR,
    configure_gpu_cpu,
    configure_matplotlib,
)  # Import config functions
import os
import numpy as np

logger = logging.getLogger(__name__)


async def create_db_and_tables():
    """Creates database tables if they don't exist."""
    async with engine.begin() as conn:
        logger.info("Creating database tables...")
        # Use run_sync for SQLModel metadata operations with async engine
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created (if they didn't exist).")


async def seed_initial_data(session: AsyncSession):
    """Inserts initial device data if minimum roles (TX, RX, JAM) are not met."""
    logger.info("Checking if initial data seeding is needed based on minimum roles...")

    # Check for at least one active device of each essential role
    query_desired = select(count(Device.id)).where(
        Device.active == True, Device.role == DeviceRole.DESIRED.value
    )
    query_receiver = select(count(Device.id)).where(
        Device.active == True, Device.role == DeviceRole.RECEIVER.value
    )
    query_jammer = select(count(Device.id)).where(
        Device.active == True, Device.role == DeviceRole.JAMMER.value
    )

    result_desired = await session.execute(query_desired)
    result_receiver = await session.execute(query_receiver)
    result_jammer = await session.execute(query_jammer)

    desired_count = result_desired.scalar_one_or_none() or 0
    receiver_count = result_receiver.scalar_one_or_none() or 0
    jammer_count = result_jammer.scalar_one_or_none() or 0

    if desired_count > 0 and receiver_count > 0 and jammer_count > 0:
        logger.info(
            f"Database already contains at least one active TX ({desired_count}), RX ({receiver_count}), and Jammer ({jammer_count}). Skipping seeding."
        )
        return

    logger.info(
        f"Minimum role requirement not met (TX: {desired_count}, RX: {receiver_count}, Jammer: {jammer_count}). Seeding initial device data..."
    )

    try:
        # It's safer to first delete existing devices if we are reseeding to avoid duplicates/conflicts
        logger.info("Deleting existing devices before reseeding...")
        await session.execute(
            select(Device)
        )  # Ensure the Device model is selected for deletion if using SQLModel directly might need adjustment based on specific ORM usage
        # Correct way depends on ORM. For SQLModel/SQLAlchemy:
        delete_stmt = Device.__table__.delete()  # Or specific filtering if needed
        await session.execute(delete_stmt)
        logger.info("Existing devices deleted.")

        # 指定的發射器設備列表
        tx_list = [
            ("tx0", [-110, -110, 40], [2.61799387799, 0, 0], "desired", 30),
            ("tx1", [-106, 56, 61], [0.52359877559, 0, 0], "desired", 30),
            ("tx2", [100, -30, 40], [-1.57079632679, 0, 0], "desired", 30),
            ("jam1", [100, 60, 40], [1.57079632679, 0, 0], "jammer", 40),
            ("jam2", [-30, 53, 67], [1.57079632679, 0, 0], "jammer", 40),
            ("jam3", [-105, -31, 64], [1.57079632679, 0, 0], "jammer", 40),
        ]

        # 指定的接收器設備
        rx_config = ("rx", [0, 0, 40], [0, 0, 0], "receiver", 0)

        # 創建發射器設備
        devices_to_add = []
        for tx_name, position, orientation, role_str, power_dbm in tx_list:
            # Ensure role is DeviceRole enum member if type hint expects it
            # role_enum = DeviceRole(role) if isinstance(role, str) else role # No longer needed, directly use string value
            device = Device(
                name=tx_name,
                position_x=position[0],
                position_y=position[1],
                position_z=position[2],
                orientation_x=orientation[0],
                orientation_y=orientation[1],
                orientation_z=orientation[2],
                role=role_str,  # Directly use the string value 'desired' or 'jammer'
                power_dbm=power_dbm,
                active=True,
            )
            devices_to_add.append(device)

        # 創建接收器設備
        rx_name, rx_position, rx_orientation, rx_role_str, rx_power_dbm = rx_config
        # rx_role_enum = DeviceRole(rx_role) if isinstance(rx_role, str) else rx_role # No longer needed
        rx_device = Device(
            name=rx_name,
            position_x=rx_position[0],
            position_y=rx_position[1],
            position_z=rx_position[2],
            orientation_x=rx_orientation[0],
            orientation_y=rx_orientation[1],
            orientation_z=rx_orientation[2],
            role=rx_role_str,  # Directly use the string value 'receiver'
            power_dbm=rx_power_dbm,
            active=True,
        )
        devices_to_add.append(rx_device)

        # 添加所有設備到數據庫
        session.add_all(devices_to_add)
        await session.commit()
        logger.info(f"成功初始化 {len(devices_to_add)} 個設備到數據庫")

    except Exception as e:
        logger.error(f"Error seeding initial data: {e}", exc_info=True)
        await session.rollback()  # Rollback on error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for FastAPI startup and shutdown logic."""
    logger.info("Application startup: Configuring environment...")
    # Configure GPU/CPU and Matplotlib on startup
    configure_gpu_cpu()
    configure_matplotlib()
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info("Initializing database...")
    await create_db_and_tables()
    # Seed data based on role check
    async with async_session_maker() as session:
        await seed_initial_data(session)
    logger.info("Database initialization complete.")
    yield
    logger.info("Application shutdown.")
    # Add any other cleanup logic here if needed
