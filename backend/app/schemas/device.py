# backend/app/schemas/device.py
from typing import Optional
from pydantic import BaseModel  # BaseModel 仍然需要用於 DeviceUpdate
from app.db.device import (
    DeviceBase as DBDeviceBase,
    DeviceRole,
)  # 導入 SQLModel 的 DeviceBase 和 Enum


# 基礎 Schema，包含 DeviceBase 的核心欄位
# 這個 Pydantic 的 DeviceBase 不再需要，因為我們將直接使用 SQLModel 的 DeviceBase
# class DeviceBase(BaseModel):
# name: str
# position_x: int
# position_y: int
# position_z: int
# orientation_x: float = PydanticField(default=0.0)
# orientation_y: float = PydanticField(default=0.0)
# orientation_z: float = PydanticField(default=0.0)
# role: str # 將改為 DeviceRole
# power_dbm: int = PydanticField(default=0)
# active: bool = PydanticField(default=True)


# 用於創建 Device 的 Schema
class DeviceCreate(DBDeviceBase):  # 直接繼承 SQLModel 的 DeviceBase
    # SQLModel 的 DeviceBase 已經包含了所有創建時需要的欄位和驗證
    # 並且 role 欄位在 DBDeviceBase 中已經是 str，SQLModel/SQLAlchemy 會處理 Enum
    # 如果希望在創建時也嚴格使用 Enum，可以在這裡覆寫
    # role: DeviceRole
    pass


# 用於更新 Device 的 Schema (所有欄位都是可選的)
class DeviceUpdate(BaseModel):  # 保持使用 Pydantic BaseModel
    name: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    position_z: Optional[int] = None
    orientation_x: Optional[float] = None
    orientation_y: Optional[float] = None
    orientation_z: Optional[float] = None
    role: Optional[DeviceRole] = None  # 明確使用 Enum
    power_dbm: Optional[int] = None
    active: Optional[bool] = None


# 資料庫中 Device 的基礎 Schema (包含 ID)
# DeviceInDBBase 可以用 Device (SQLModel, table=True) 的特性替代，
# 或者如果需要不同的 Pydantic 配置，可以這樣定義
class DeviceInDBBase(DBDeviceBase):
    id: int

    class Config:
        from_attributes = True  # Pydantic V2: model_config = {"from_attributes": True}


# 用於 API 返回的 Device 完整 Schema
class Device(DBDeviceBase):  # 直接繼承 SQLModel 的 DeviceBase
    id: int  # 確保 id 存在，因為 DBDeviceBase (SQLModel Base) 通常不含 id

    class Config:
        from_attributes = True  # Pydantic V2: model_config = {"from_attributes": True}


# 可設定參數版本，用於 Response 的 Schema
# DeviceParameters 也可考慮繼承 DBDeviceBase
class DeviceParameters(DBDeviceBase):
    id: int
    # role: DeviceRole # 如果希望 API 回應中的 role 也是 Enum 型別

    class Config:
        from_attributes = True  # Pydantic V2: model_config = {"from_attributes": True}
