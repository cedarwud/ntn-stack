from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Relationship, Column, JSON


class TLEData(BaseModel):
    """TLE (Two-Line Element) 資料模型"""

    line1: str = Field(..., description="TLE 第一行")
    line2: str = Field(..., description="TLE 第二行")

    @property
    def name(self) -> str:
        """從 TLE 數據中提取衛星名稱"""
        return self.line1.split()[1]

    @property
    def norad_id(self) -> str:
        """從 TLE 數據中提取 NORAD ID"""
        return self.line1.split()[2]


class Satellite(SQLModel, table=True):
    """衛星資料模型"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="衛星名稱")
    norad_id: str = Field(index=True, description="NORAD ID")
    international_designator: Optional[str] = Field(None, description="國際指定符")

    # 衛星參數
    launch_date: Optional[datetime] = Field(None, description="發射日期")
    decay_date: Optional[datetime] = Field(None, description="預計消亡日期")
    period_minutes: Optional[float] = Field(None, description="軌道周期（分鐘）")
    inclination_deg: Optional[float] = Field(None, description="軌道傾角（度）")
    apogee_km: Optional[float] = Field(None, description="遠地點高度（公里）")
    perigee_km: Optional[float] = Field(None, description="近地點高度（公里）")

    # JSON 格式存儲的 TLE 數據
    tle_data: Optional[dict] = Field(
        default=None, sa_column=Column(JSON), description="TLE 數據"
    )

    # 最後更新時間
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="最後更新時間"
    )

    # 關係
    passes: List["SatellitePass"] = Relationship(back_populates="satellite")


class SatellitePass(SQLModel, table=True):
    """衛星過境資料模型"""

    id: Optional[int] = Field(default=None, primary_key=True)
    satellite_id: int = Field(foreign_key="satellite.id")

    rise_time: datetime = Field(..., description="升起時間")
    rise_azimuth: float = Field(..., description="升起方位角（度）")
    max_alt_time: datetime = Field(..., description="最大仰角時間")
    max_alt_degree: float = Field(..., description="最大仰角（度）")
    set_time: datetime = Field(..., description="落下時間")
    set_azimuth: float = Field(..., description="落下方位角（度）")

    duration_seconds: float = Field(..., description="可見時長（秒）")
    ground_station_lat: float = Field(..., description="地面站緯度")
    ground_station_lon: float = Field(..., description="地面站經度")
    ground_station_alt: Optional[float] = Field(None, description="地面站海拔（米）")

    # 過境類型（如日間、夜間、日出/日落等）
    pass_type: str = Field("unknown", description="過境類型")

    # 關係
    satellite: "Satellite" = Relationship(back_populates="passes")


class OrbitPoint(BaseModel):
    """軌道點，表示衛星在特定時間的位置"""

    timestamp: datetime = Field(..., description="時間戳")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: float = Field(..., description="海拔（公里）")
    elevation: Optional[float] = Field(None, description="從觀測點看的仰角（度）")
    azimuth: Optional[float] = Field(None, description="從觀測點看的方位角（度）")
    range_km: Optional[float] = Field(None, description="與觀測點的距離（公里）")


class OrbitPropagationResult(BaseModel):
    """軌道傳播結果，包含一系列軌道點"""

    satellite_id: int = Field(..., description="衛星 ID")
    satellite_name: str = Field(..., description="衛星名稱")
    start_time: datetime = Field(..., description="開始時間")
    end_time: datetime = Field(..., description="結束時間")
    points: List[OrbitPoint] = Field(..., description="軌道點列表")
