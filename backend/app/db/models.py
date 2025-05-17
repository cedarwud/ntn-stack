from typing import Optional, Any
from sqlmodel import Field, SQLModel
from enum import Enum as PyEnum


# --- Enum Definitions ---
class DeviceRole(PyEnum):
    DESIRED = "desired"
    JAMMER = "jammer"
    RECEIVER = "receiver"


# --- SQLModel Definitions ---
class DeviceBase(SQLModel):
    name: str = Field(index=True, unique=True)
    position_x: int = Field(...)  # required
    position_y: int = Field(...)  # required
    position_z: int = Field(...)  # required
    orientation_x: float = Field(default=0.0)
    orientation_y: float = Field(default=0.0)
    orientation_z: float = Field(default=0.0)
    role: str = Field(...)  # required
    power_dbm: int = Field(default=0)
    active: bool = Field(default=True, index=True)


# Represents the table structure, inherits validation from DeviceBase
class Device(DeviceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
