"""
PostgreSQL 種子數據初始化
替代 MongoDB 的設備和地面站數據初始化
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

async def seed_initial_device_data_postgresql(connection):
    """使用 PostgreSQL 初始化設備數據"""
    logger.info("Checking if initial device data seeding is needed...")

    # 檢查現有數據
    existing_count = await connection.fetchval(
        "SELECT COUNT(*) FROM devices WHERE active = TRUE"
    )
    
    if existing_count >= 7:
        logger.info(
            f"Device Database already contains {existing_count} active devices. Skipping seeding."
        )
        return

    logger.info("Minimum Device requirement not met. Seeding initial Device data...")

    try:
        # 清理現有數據
        await connection.execute("DELETE FROM devices")
        logger.info("Cleared existing device data")

        # 插入 device 數據 - 使用前端期望的分離座標格式
        devices = [
            {
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

        # 批量插入設備數據
        insert_query = """
            INSERT INTO devices 
            (name, position_x, position_y, position_z, orientation_x, orientation_y, 
             orientation_z, role, power_dbm, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        
        for device in devices:
            await connection.execute(
                insert_query,
                device["name"],
                device["position_x"],
                device["position_y"], 
                device["position_z"],
                device["orientation_x"],
                device["orientation_y"],
                device["orientation_z"],
                device["role"],
                device["power_dbm"],
                device["active"]
            )

        logger.info(f"Successfully seeded {len(devices)} devices into PostgreSQL")

    except Exception as e:
        logger.error(f"Error seeding initial Device data: {e}", exc_info=True)
        raise


async def seed_default_ground_station_postgresql(connection):
    """使用 PostgreSQL 初始化地面站數據"""
    logger.info("Checking if default ground station 'NYCU_gnb' needs to be seeded...")

    # 檢查現有數據
    existing = await connection.fetchrow(
        "SELECT * FROM ground_stations WHERE station_identifier = $1",
        "NYCU_gnb"
    )
    
    if existing:
        logger.info(
            f"Default ground station 'NYCU_gnb' already exists. Skipping seeding."
        )
        return

    logger.info("Default ground station 'NYCU_gnb' not found. Seeding...")

    try:
        station_data = {
            "station_identifier": "NYCU_gnb",
            "name": "NYCU Main gNB",
            "latitude_deg": 24.786667,
            "longitude_deg": 120.996944,
            "altitude_m": 100.0,
            "description": "Default Ground Station at National Yang Ming Chiao Tung University",
        }

        insert_query = """
            INSERT INTO ground_stations 
            (station_identifier, name, latitude_deg, longitude_deg, altitude_m, description)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        
        station_id = await connection.fetchval(
            insert_query,
            station_data["station_identifier"],
            station_data["name"],
            station_data["latitude_deg"],
            station_data["longitude_deg"],
            station_data["altitude_m"],
            station_data["description"]
        )

        logger.info(
            f"Successfully seeded default ground station 'NYCU_gnb' with id {station_id}"
        )

    except Exception as e:
        logger.error(f"Error seeding default ground station: {e}", exc_info=True)
        raise