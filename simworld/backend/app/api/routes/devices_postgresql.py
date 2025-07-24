"""
設備管理 API - PostgreSQL 版本
替代原來的 MongoDB 設備管理
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_postgresql_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic 模型定義
class DeviceCreate(BaseModel):
    name: str = Field(..., description="設備名稱")
    position_x: float = Field(..., description="X 坐標")
    position_y: float = Field(..., description="Y 坐標") 
    position_z: float = Field(..., description="Z 坐標")
    orientation_x: float = Field(..., description="X 方向角")
    orientation_y: float = Field(..., description="Y 方向角")
    orientation_z: float = Field(..., description="Z 方向角")
    role: str = Field(..., description="設備角色", pattern="^(desired|jammer|receiver)$")
    power_dbm: float = Field(..., description="功率 (dBm)")
    active: bool = Field(True, description="是否啟用")

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="設備名稱")
    position_x: Optional[float] = Field(None, description="X 坐標")
    position_y: Optional[float] = Field(None, description="Y 坐標")
    position_z: Optional[float] = Field(None, description="Z 坐標")
    orientation_x: Optional[float] = Field(None, description="X 方向角")
    orientation_y: Optional[float] = Field(None, description="Y 方向角")
    orientation_z: Optional[float] = Field(None, description="Z 方向角")
    role: Optional[str] = Field(None, description="設備角色", pattern="^(desired|jammer|receiver)$")
    power_dbm: Optional[float] = Field(None, description="功率 (dBm)")
    active: Optional[bool] = Field(None, description="是否啟用")

class DeviceResponse(BaseModel):
    id: int
    name: str
    position_x: float
    position_y: float
    position_z: float
    orientation_x: float
    orientation_y: float
    orientation_z: float
    role: str
    power_dbm: float
    active: bool

@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    active_only: bool = Query(True, description="只顯示啟用的設備"),
    db = Depends(get_postgresql_db)
):
    """獲取設備列表"""
    try:
        async with db as connection:
            if active_only:
                query = "SELECT * FROM devices WHERE active = TRUE ORDER BY id"
            else:
                query = "SELECT * FROM devices ORDER BY id"
            
            rows = await connection.fetch(query)
            
            devices = []
            for row in rows:
                devices.append(DeviceResponse(
                    id=row['id'],
                    name=row['name'],
                    position_x=row['position_x'],
                    position_y=row['position_y'],
                    position_z=row['position_z'],
                    orientation_x=row['orientation_x'],
                    orientation_y=row['orientation_y'],
                    orientation_z=row['orientation_z'],
                    role=row['role'],
                    power_dbm=row['power_dbm'],
                    active=row['active']
                ))
            
            return devices
            
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/count")
async def get_device_count(
    active_only: bool = Query(True, description="只計算啟用的設備"),
    db = Depends(get_postgresql_db)
):
    """獲取設備數量"""
    try:
        async with db as connection:
            if active_only:
                count = await connection.fetchval(
                    "SELECT COUNT(*) FROM devices WHERE active = TRUE"
                )
            else:
                count = await connection.fetchval("SELECT COUNT(*) FROM devices")
            
            return {"count": count}
            
    except Exception as e:
        logger.error(f"Error getting device count: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/ground-stations")
async def get_ground_stations(db = Depends(get_postgresql_db)):
    """獲取地面站列表"""
    try:
        async with db as connection:
            query = "SELECT * FROM ground_stations ORDER BY id"
            rows = await connection.fetch(query)
            
            stations = []
            for row in rows:
                stations.append({
                    "id": row['id'],
                    "station_identifier": row['station_identifier'],
                    "name": row['name'],
                    "latitude_deg": row['latitude_deg'],
                    "longitude_deg": row['longitude_deg'],
                    "altitude_m": row['altitude_m'],
                    "description": row['description']
                })
            
            return stations
            
    except Exception as e:
        logger.error(f"Error getting ground stations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate,
    db = Depends(get_postgresql_db)
):
    """創建新設備"""
    try:
        async with db as connection:
            query = """
                INSERT INTO devices 
                (name, position_x, position_y, position_z, orientation_x, orientation_y, 
                 orientation_z, role, power_dbm, active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING *
            """
            
            row = await connection.fetchrow(
                query,
                device.name,
                device.position_x,
                device.position_y,
                device.position_z,
                device.orientation_x,
                device.orientation_y,
                device.orientation_z,
                device.role,
                device.power_dbm,
                device.active
            )
            
            return DeviceResponse(
                id=row['id'],
                name=row['name'],
                position_x=row['position_x'],
                position_y=row['position_y'],
                position_z=row['position_z'],
                orientation_x=row['orientation_x'],
                orientation_y=row['orientation_y'],
                orientation_z=row['orientation_z'],
                role=row['role'],
                power_dbm=row['power_dbm'],
                active=row['active']
            )
            
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Device name already exists")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device_by_id(
    device_id: int,
    db = Depends(get_postgresql_db)
):
    """根據 ID 獲取設備"""
    try:
        async with db as connection:
            query = "SELECT * FROM devices WHERE id = $1"
            row = await connection.fetchrow(query, device_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Device not found")
            
            return DeviceResponse(
                id=row['id'],
                name=row['name'],
                position_x=row['position_x'],
                position_y=row['position_y'],
                position_z=row['position_z'],
                orientation_x=row['orientation_x'],
                orientation_y=row['orientation_y'],
                orientation_z=row['orientation_z'],
                role=row['role'],
                power_dbm=row['power_dbm'],
                active=row['active']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device by id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db = Depends(get_postgresql_db)
):
    """更新設備"""
    try:
        async with db as connection:
            # 檢查設備是否存在
            existing = await connection.fetchrow(
                "SELECT * FROM devices WHERE id = $1", device_id
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Device not found")
            
            # 構建更新查詢
            update_fields = []
            values = []
            param_count = 1
            
            for field, value in device_update.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            values.append(device_id)
            query = f"""
                UPDATE devices 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
                RETURNING *
            """
            
            row = await connection.fetchrow(query, *values)
            
            return DeviceResponse(
                id=row['id'],
                name=row['name'],
                position_x=row['position_x'],
                position_y=row['position_y'],
                position_z=row['position_z'],
                orientation_x=row['orientation_x'],
                orientation_y=row['orientation_y'],
                orientation_z=row['orientation_z'],
                role=row['role'],
                power_dbm=row['power_dbm'],
                active=row['active']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db = Depends(get_postgresql_db)
):
    """刪除設備"""
    try:
        async with db as connection:
            result = await connection.execute(
                "DELETE FROM devices WHERE id = $1", device_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Device not found")
            
            return {"message": "Device deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")