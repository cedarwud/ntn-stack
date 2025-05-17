from sqlalchemy import Column, String, Float, Integer

from app.db.base_class import Base


class GroundStation(Base):
    __tablename__ = "ground_stations"

    id = Column(Integer, primary_key=True, index=True)  # 自動增長的主鍵
    station_identifier = Column(
        String, unique=True, index=True, nullable=False
    )  # 使用者定義的唯一ID
    name = Column(String, index=True, nullable=False)
    latitude_deg = Column(Float, nullable=False)
    longitude_deg = Column(Float, nullable=False)
    altitude_m = Column(Float, nullable=False, default=0.0)
    description = Column(String, nullable=True)
