from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel


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

    id: Optional[int] = Field(default=None, primary_key=True)
    source_system: str = Field(..., description="源座標系統")
    target_system: str = Field(..., description="目標座標系統")
    transformation_parameters: str = Field(..., description="轉換參數 (JSON 格式)")
    description: Optional[str] = Field(None, description="轉換描述")
