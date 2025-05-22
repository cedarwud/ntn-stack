from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Relationship, Field, Column
from sqlalchemy import Integer, Float, String, DateTime


class TLEData(BaseModel):
    """TLE (Two-Line Element) 資料模型"""

    line1: str = PydanticField(..., description="TLE 第一行")
    line2: str = PydanticField(..., description="TLE 第二行")

    @property
    def name(self) -> str:
        """從 TLE 數據中提取衛星名稱"""
        return self.line1.split()[1]

    @property
    def norad_id(self) -> str:
        """從 TLE 數據中提取 NORAD ID"""
        return self.line1.split()[2]


# 簡化版衛星模型
class Satellite(SQLModel, table=True):
    """簡化版衛星資料模型"""

    __tablename__ = "satellite"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
        description="主鍵 ID",
    )
    name: str = Field(index=True, description="衛星名稱")
    norad_id: str = Field(index=True, description="NORAD ID")
    international_designator: Optional[str] = Field(
        default=None, description="國際指定標識符"
    )
    launch_date: Optional[datetime] = Field(default=None, description="發射日期")
    decay_date: Optional[datetime] = Field(
        default=None, description="預計衰減/墜落日期"
    )
    period_minutes: Optional[float] = Field(
        default=None, description="軌道周期（分鐘）"
    )
    inclination_deg: Optional[float] = Field(default=None, description="軌道傾角（度）")
    apogee_km: Optional[float] = Field(default=None, description="遠地點高度（公里）")
    perigee_km: Optional[float] = Field(default=None, description="近地點高度（公里）")
    tle_data: Optional[str] = Field(default=None, description="TLE 資料 JSON 字串")
    last_updated: Optional[datetime] = Field(default=None, description="最後更新時間")

    def get_tle_data(self) -> Optional[TLEData]:
        """從 JSON 字串轉換為 TLE 資料物件"""
        if not self.tle_data:
            return None
        try:
            data = json.loads(self.tle_data)
            return TLEData(**data)
        except Exception as e:
            print(f"Error parsing TLE data: {e}")
            return None

    def set_tle_data(self, tle: TLEData) -> None:
        """將 TLE 資料物件轉換為 JSON 字串存儲"""
        self.tle_data = json.dumps(tle.model_dump())  # 使用 model_dump 替代 dict


# 簡化版衛星過境模型
class SatellitePass(SQLModel, table=True):
    """簡化版衛星過境資料模型"""

    __tablename__ = "satellitepass"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
        description="主鍵 ID",
    )
    satellite_id: int = Field(foreign_key="satellite.id")
    rise_time: datetime = Field(..., description="升起時間")
    set_time: datetime = Field(..., description="落下時間")
    max_elevation: Optional[float] = Field(default=None, description="最大仰角（度）")
    observatory_lat: Optional[float] = Field(default=None, description="觀測點緯度")
    observatory_lon: Optional[float] = Field(default=None, description="觀測點經度")
    observatory_alt: Optional[float] = Field(
        default=None, description="觀測點海拔（米）"
    )


# 以下是原始完整模型的數據定義，用於參考


class OrbitPoint(BaseModel):
    """軌道點，表示衛星在特定時間的位置"""

    timestamp: datetime = PydanticField(..., description="時間戳")
    latitude: float = PydanticField(..., description="緯度")
    longitude: float = PydanticField(..., description="經度")
    altitude: float = PydanticField(..., description="海拔（公里）")
    elevation: Optional[float] = PydanticField(
        None, description="從觀測點看的仰角（度）"
    )
    azimuth: Optional[float] = PydanticField(
        None, description="從觀測點看的方位角（度）"
    )
    range_km: Optional[float] = PydanticField(
        None, description="與觀測點的距離（公里）"
    )


class OrbitPropagationResult(BaseModel):
    """軌道傳播結果，包含一系列軌道點"""

    satellite_id: int = PydanticField(..., description="衛星 ID")
    satellite_name: str = PydanticField(..., description="衛星名稱")
    start_time: datetime = PydanticField(..., description="開始時間")
    end_time: datetime = PydanticField(..., description="結束時間")
    points: List[OrbitPoint] = PydanticField(..., description="軌道點列表")
