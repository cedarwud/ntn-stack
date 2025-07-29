from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Column, Field
from sqlalchemy import Integer, String, Column as SAColumn


class GeoCoordinate(BaseModel):
    """地理座標模型，表示地球上的位置"""

    latitude: float = Field(..., description="緯度，範圍 -90 到 90")
    longitude: float = Field(..., description="經度，範圍 -180 到 180")
    altitude: Optional[float] = Field(None, description="海拔高度，單位:米")


class CartesianCoordinate(BaseModel):
    """笛卡爾座標模型，表示 3D 空間中的位置"""

    x: float = Field(..., description="X 座標")
    y: float = Field(..., description="Y 座標")
    z: float = Field(..., description="Z 座標")


class CoordinateTransformation(SQLModel, table=True):
    """座標轉換記錄，用於追蹤常用的座標轉換"""

    __tablename__ = "coordinatetransformation"

    id: int = Field(primary_key=True, default=None)
    source_system: str = Field(index=True)
    target_system: str = Field(index=True)
    transformation_parameters: str
    description: Optional[str] = None
