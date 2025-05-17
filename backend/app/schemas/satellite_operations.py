from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# Define models for TLE synchronization
class TLESyncTriggerPayload(BaseModel):
    force_update: bool = Field(
        False, description="Force update even if within sync interval"
    )


class TLESyncResponse(BaseModel):
    message: str
    synchronized_tles: int
    source: str
    last_sync_time_utc: Optional[datetime] = None
    next_sync_time_utc: Optional[datetime] = None


# Define models for visible satellite information
class VisibleSatelliteInfo(BaseModel):
    norad_id: int
    name: str
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    line1: str
    line2: str
    # 新增 ECEF 座標 (單位: 公里)
    ecef_x_km: Optional[float] = Field(
        None, description="Earth-Centered Earth-Fixed X coordinate in km"
    )
    ecef_y_km: Optional[float] = Field(
        None, description="Earth-Centered Earth-Fixed Y coordinate in km"
    )
    ecef_z_km: Optional[float] = Field(
        None, description="Earth-Centered Earth-Fixed Z coordinate in km"
    )

    model_config = ConfigDict(from_attributes=True)


class VisibleSatellitesResponse(BaseModel):
    ground_station_identifier: str
    calculation_time_utc: datetime
    satellites: List[VisibleSatelliteInfo]
    count: int
