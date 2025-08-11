"""
地面站相關模型定義
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Integer, String, Float, DateTime


class GroundStation(SQLModel, table=True):
    """地面站資料模型"""

    __tablename__ = "groundstation"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
        description="主鍵 ID",
    )
    station_identifier: str = Field(
        sa_column=Column(String, unique=True, index=True),
        description="地面站唯一識別符",
    )
    name: str = Field(description="地面站名稱")
    latitude_deg: float = Field(sa_column=Column(Float), description="緯度（度）")
    longitude_deg: float = Field(sa_column=Column(Float), description="經度（度）")
    altitude_m: float = Field(sa_column=Column(Float), description="海拔（米）")
    description: Optional[str] = Field(default=None, description="地面站描述")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime),
        description="創建時間",
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime), description="更新時間"
    )
