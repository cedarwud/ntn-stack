from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .device_model import DeviceBase, DeviceRole


class DeviceCreate(DeviceBase):
    """創建設備的資料傳輸對象"""

    pass


class DeviceUpdate(BaseModel):
    """更新設備的資料傳輸對象"""

    name: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    position_z: Optional[int] = None
    orientation_x: Optional[float] = None
    orientation_y: Optional[float] = None
    orientation_z: Optional[float] = None
    role: Optional[DeviceRole] = None
    power_dbm: Optional[int] = None
    active: Optional[bool] = None

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


class DeviceResponse(DeviceBase):
    """設備響應的資料傳輸對象"""

    id: int

    class Config:
        orm_mode = True
