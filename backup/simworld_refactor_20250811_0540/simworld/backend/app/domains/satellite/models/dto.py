"""
衛星領域 DTO（資料傳輸物件）
"""

from typing import Optional
from pydantic import BaseModel, Field


class GroundStationCreate(BaseModel):
    """創建地面站的資料傳輸物件"""

    station_identifier: str = Field(..., description="地面站唯一識別符")
    name: str = Field(..., description="地面站名稱")
    latitude_deg: float = Field(..., description="緯度（度）")
    longitude_deg: float = Field(..., description="經度（度）")
    altitude_m: float = Field(..., description="海拔（米）")
    description: Optional[str] = Field(default=None, description="地面站描述")
