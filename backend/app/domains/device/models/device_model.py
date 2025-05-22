from typing import Optional, Any
from sqlmodel import Field, SQLModel
from enum import Enum as PyEnum
from sqlalchemy import String


# --- Enum Definitions ---
class DeviceRole(str, PyEnum):
    DESIRED = "desired"
    JAMMER = "jammer"
    RECEIVER = "receiver"


# --- SQLModel Definitions ---
class DeviceBase(SQLModel):
    """設備基礎模型，定義設備的共同屬性"""

    name: str = Field(index=True, unique=True)
    position_x: int = Field(...)  # required
    position_y: int = Field(...)  # required
    position_z: int = Field(...)  # required
    orientation_x: float = Field(default=0.0)
    orientation_y: float = Field(default=0.0)
    orientation_z: float = Field(default=0.0)
    role: DeviceRole = Field(..., sa_type=String(50))
    power_dbm: int = Field(default=0)
    active: bool = Field(default=True, index=True)


# Represents the table structure, inherits validation from DeviceBase
class Device(DeviceBase, table=True):
    """設備實體模型，對應資料庫中的設備表"""

    id: Optional[int] = Field(default=None, primary_key=True)
