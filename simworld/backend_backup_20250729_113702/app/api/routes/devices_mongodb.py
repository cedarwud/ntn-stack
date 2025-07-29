"""
MongoDB 版本的設備 API 路由
提供完整的設備 CRUD 操作，替代 PostgreSQL 版本
"""
import logging
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.api.dependencies import get_mongodb_db

# 數據模型定義
class DeviceCreate(BaseModel):
    name: str
    position_x: float
    position_y: float
    position_z: float
    orientation_x: Optional[float] = 0.0
    orientation_y: Optional[float] = 0.0
    orientation_z: Optional[float] = 0.0
    role: str
    power_dbm: Optional[float] = 20.0
    active: bool = True

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    orientation_x: Optional[float] = None
    orientation_y: Optional[float] = None
    orientation_z: Optional[float] = None
    role: Optional[str] = None
    power_dbm: Optional[float] = None
    active: Optional[bool] = None

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_devices() -> List[dict]:
    """
    獲取所有設備 - MongoDB 版本 (with fallback)
    """
    try:
        # Try to get MongoDB database with timeout
        db = await get_mongodb_db()
        logger.info("Fetching devices from MongoDB")
        
        # 查詢所有活躍設備
        devices = []
        async for device in db.devices.find({"active": True}):
            # 轉換 ObjectId 為字符串
            device["_id"] = str(device["_id"])
            devices.append(device)
        
        logger.info(f"Found {len(devices)} devices in MongoDB")
        return devices
    
    except Exception as e:
        logger.warning(f"MongoDB unavailable ({e}), returning fallback device data")
        
        # FALLBACK: Return default device configuration when MongoDB is unavailable
        fallback_devices = [
            {
                "_id": "fallback_1",
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
                "active": True
            },
            {
                "_id": "fallback_2",
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
                "active": True
            },
            {
                "_id": "fallback_3",
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
                "active": True
            },
            {
                "_id": "fallback_4",
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
                "active": True
            },
            {
                "_id": "fallback_5",
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
                "active": True
            },
            {
                "_id": "fallback_6",
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
                "active": True
            },
            {
                "_id": "fallback_7",
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
                "active": True
            }
        ]
        
        logger.info(f"Returning {len(fallback_devices)} fallback devices")
        return fallback_devices


@router.get("/count")
async def get_device_count(
    db: AsyncIOMotorDatabase = Depends(get_mongodb_db)
) -> dict:
    """
    獲取設備統計 - MongoDB 版本
    """
    try:
        total = await db.devices.count_documents({})
        active = await db.devices.count_documents({"active": True})
        by_role = {}
        
        # 統計各角色數量
        for role in ["desired", "receiver", "jammer"]:
            count = await db.devices.count_documents({"role": role, "active": True})
            by_role[role] = count
        
        return {
            "total": total,
            "active": active,
            "by_role": by_role
        }
        
    except Exception as e:
        logger.error(f"Error getting device count from MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Error getting device count")


@router.get("/ground-stations")
async def get_ground_stations(
    db: AsyncIOMotorDatabase = Depends(get_mongodb_db)
) -> List[dict]:
    """
    獲取所有地面站 - MongoDB 版本
    """
    try:
        logger.info("Fetching ground stations from MongoDB")
        
        stations = []
        async for station in db.ground_stations.find({}):
            # 轉換 ObjectId 為字符串
            station["_id"] = str(station["_id"])
            stations.append(station)
        
        logger.info(f"Found {len(stations)} ground stations in MongoDB")
        return stations
        
    except Exception as e:
        logger.error(f"Error fetching ground stations from MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Error fetching ground stations")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncIOMotorDatabase = Depends(get_mongodb_db)
) -> dict:
    """
    創建新設備 - MongoDB 版本
    """
    try:
        logger.info(f"Creating device: {device_data.name}")
        
        # 獲取下一個ID
        last_device = await db.devices.find_one(sort=[("id", -1)])
        next_id = (last_device["id"] + 1) if last_device else 1
        
        # 準備設備數據
        device_dict = device_data.dict()
        device_dict["id"] = next_id
        
        # 插入設備
        result = await db.devices.insert_one(device_dict)
        
        # 返回創建的設備
        created_device = await db.devices.find_one({"_id": result.inserted_id})
        created_device["_id"] = str(created_device["_id"])
        
        logger.info(f"Created device with ID: {next_id}")
        return created_device
        
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(status_code=500, detail="Error creating device")


@router.get("/{device_id}")
async def get_device_by_id(
    device_id: int,
    db: AsyncIOMotorDatabase = Depends(get_mongodb_db)
) -> dict:
    """
    根據ID獲取設備 - MongoDB 版本
    """
    try:
        device = await db.devices.find_one({"id": device_id})
        if not device:
            raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
        
        device["_id"] = str(device["_id"])
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching device")


@router.put("/{device_id}")
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncIOMotorDatabase = Depends(get_mongodb_db)
) -> dict:
    """
    更新設備 - MongoDB 版本
    """
    try:
        logger.info(f"Updating device: {device_id}")
        
        # 檢查設備是否存在
        existing_device = await db.devices.find_one({"id": device_id})
        if not existing_device:
            raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
        
        # 準備更新數據（只包含非None的字段）
        update_dict = {k: v for k, v in device_data.dict().items() if v is not None}
        
        if update_dict:
            # 更新設備
            await db.devices.update_one({"id": device_id}, {"$set": update_dict})
        
        # 返回更新後的設備
        updated_device = await db.devices.find_one({"id": device_id})
        updated_device["_id"] = str(updated_device["_id"])
        
        logger.info(f"Updated device: {device_id}")
        return updated_device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating device")


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db: AsyncIOMotorDatabase = Depends(get_mongodb_db)
) -> dict:
    """
    刪除設備 - MongoDB 版本
    """
    try:
        logger.info(f"Deleting device: {device_id}")
        
        # 檢查設備是否存在
        existing_device = await db.devices.find_one({"id": device_id})
        if not existing_device:
            raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
        
        # 刪除設備
        await db.devices.delete_one({"id": device_id})
        
        logger.info(f"Deleted device: {device_id}")
        return {"message": f"Device {device_id} deleted successfully", "deleted_device": {
            "id": existing_device["id"],
            "name": existing_device["name"],
            "role": existing_device["role"]
        }}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting device")