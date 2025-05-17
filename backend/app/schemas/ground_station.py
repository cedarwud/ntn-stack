from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GroundStationBase(BaseModel):
    station_identifier: Optional[str] = Field(
        None,
        example="gnb_main_site_1",
        description="User-defined unique identifier for the ground station",
    )
    name: Optional[str] = Field(None, example="Main Ground Station Alpha")
    latitude_deg: Optional[float] = Field(None, example=24.786667)
    longitude_deg: Optional[float] = Field(None, example=120.996944)
    altitude_m: Optional[float] = Field(None, example=50.0)
    description: Optional[str] = Field(None, example="Primary gNB for NTN simulation")


class GroundStationCreate(GroundStationBase):
    station_identifier: str = Field(..., example="gnb_main_site_1")
    name: str = Field(..., example="Main Ground Station Alpha")
    latitude_deg: float = Field(..., example=24.786667)
    longitude_deg: float = Field(..., example=120.996944)
    altitude_m: float = Field(
        default=0.0, example=50.0
    )  # Default in schema, matches DB model default


class GroundStationUpdate(GroundStationBase):
    # station_identifier is typically not updated as it's a unique business key.
    # All other fields are optional as defined in GroundStationBase.
    pass


class GroundStationInDBBase(GroundStationBase):
    id: int  # The auto-incrementing primary key from the database
    station_identifier: str
    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    # description is Optional as inherited from GroundStationBase

    # Pydantic V2 style for ORM mode
    model_config = ConfigDict(from_attributes=True)


# For API response model
class GroundStation(GroundStationInDBBase):
    pass


# Alias for clarity if needed
class GroundStationResponse(GroundStationInDBBase):
    pass
