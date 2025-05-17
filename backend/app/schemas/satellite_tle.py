from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SatelliteTLEBase(BaseModel):
    name: Optional[str] = Field(None, example="ISS (ZARYA)")
    line1: Optional[str] = Field(
        None,
        example="1 25544U 98067A   23307.92629005  .00027157  00000-0  49909-3 0  9993",
    )
    line2: Optional[str] = Field(
        None,
        example="2 25544  51.6416 227.5103 0006011  63.9857  18.1076 15.49534558423738",
    )
    epoch_year: Optional[int] = Field(
        None, example=23
    )  # Assuming 2-digit year or full year
    epoch_day: Optional[float] = Field(None, example=307.92629005)
    source_updated_at: Optional[datetime] = None


class SatelliteTLECreate(SatelliteTLEBase):
    norad_id: int = Field(..., example=25544)
    name: str = Field(..., example="ISS (ZARYA)")
    line1: str = Field(
        ...,
        example="1 25544U 98067A   23307.92629005  .00027157  00000-0  49909-3 0  9993",
    )
    line2: str = Field(
        ...,
        example="2 25544  51.6416 227.5103 0006011  63.9857  18.1076 15.49534558423738",
    )


class SatelliteTLEUpdate(SatelliteTLEBase):
    # For updates, norad_id is typically not changed as it's the primary key.
    # All other fields are optional as defined in SatelliteTLEBase.
    pass


class SatelliteTLEInDBBase(SatelliteTLEBase):
    norad_id: int
    name: str
    line1: str
    line2: str
    last_fetched_at: datetime  # This is populated by the database

    # Pydantic V2 style for ORM mode
    model_config = ConfigDict(from_attributes=True)


# For API response model
class SatelliteTLE(SatelliteTLEInDBBase):
    pass


# Alias for clarity if needed, or direct use of SatelliteTLE
class SatelliteTLEResponse(SatelliteTLEInDBBase):
    pass
