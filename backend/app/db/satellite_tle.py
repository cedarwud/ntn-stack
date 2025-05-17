from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.sql import func

from app.db.base_class import Base


class SatelliteTLE(Base):
    __tablename__ = "satellite_tles"

    norad_id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String, index=True, nullable=False)
    line1 = Column(String, nullable=False)
    line2 = Column(String, nullable=False)
    epoch_year = Column(Integer, nullable=True)
    epoch_day = Column(Float, nullable=True)
    last_fetched_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    source_updated_at = Column(DateTime(timezone=True), nullable=True)
