"""
MongoDB 種子數據
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def seed_initial_device_data_mongodb(db: AsyncIOMotorDatabase):
    """初始化設備種子數據到 MongoDB"""
    logger.info("Checking if initial device data seeding is needed...")

    try:
        devices_collection = db["devices"]

        # 檢查是否已有活躍設備
        existing_count = await devices_collection.count_documents({"active": True})

        if existing_count >= 7:  # 如果已有足夠的設備，跳過種子化
            logger.info(
                f"Device Database already contains {existing_count} active devices. Skipping seeding."
            )
            return True

        logger.info(
            "Minimum Device requirement not met. Seeding initial Device data..."
        )

        # 清除現有數據
        await devices_collection.delete_many({})
        logger.info("Cleared existing device data")

        # 插入 device 數據 - 使用原本 PostgreSQL 的設備配置
        devices = [
            {
                "_id": 1,
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
                "_id": 2,
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
                "_id": 3,
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
                "_id": 4,
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
                "_id": 5,
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
                "_id": 6,
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
                "_id": 7,
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
        return True

    except Exception as e:
        logger.error(f"Error seeding initial Device data: {e}", exc_info=True)
        return False
