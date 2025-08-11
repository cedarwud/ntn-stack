import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import or_, and_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domains.satellite.models.satellite_model import Satellite, SatellitePass
from app.domains.satellite.interfaces.satellite_repository import (
    SatelliteRepositoryInterface,
)
from app.db.base import async_session_maker

logger = logging.getLogger(__name__)


class SQLModelSatelliteRepository(SatelliteRepositoryInterface):
    """衛星儲存庫的 SQLModel 實現"""

    def __init__(self, session_factory=async_session_maker):
        self._session_factory = session_factory

    async def get_satellites(self) -> List[Satellite]:
        """獲取所有衛星"""
        async with self._session_factory() as session:
            statement = select(Satellite).order_by(Satellite.name)
            results = await session.execute(statement)
            return list(results.scalars().all())

    async def get_satellite_by_id(self, satellite_id: int) -> Optional[Satellite]:
        """根據 ID 獲取衛星"""
        async with self._session_factory() as session:
            statement = select(Satellite).where(Satellite.id == satellite_id)
            results = await session.execute(statement)
            return results.scalar_one_or_none()

    async def get_satellite_by_norad_id(self, norad_id: str) -> Optional[Satellite]:
        """根據 NORAD ID 獲取衛星"""
        async with self._session_factory() as session:
            statement = select(Satellite).where(Satellite.norad_id == norad_id)
            results = await session.execute(statement)
            return results.scalar_one_or_none()

    async def search_satellites(self, query: str) -> List[Satellite]:
        """搜尋衛星"""
        query = f"%{query}%"
        async with self._session_factory() as session:
            statement = select(Satellite).where(
                or_(
                    Satellite.name.ilike(query),
                    Satellite.norad_id.ilike(query),
                    Satellite.international_designator.ilike(query),
                )
            )
            results = await session.execute(statement)
            return list(results.scalars().all())

    async def create_satellite(self, satellite_data: Dict[str, Any]) -> Satellite:
        """創建新衛星"""
        satellite = Satellite(**satellite_data)
        async with self._session_factory() as session:
            session.add(satellite)
            await session.commit()
            await session.refresh(satellite)
            return satellite

    async def update_satellite(
        self, satellite_id: int, satellite_data: Dict[str, Any]
    ) -> Optional[Satellite]:
        """更新衛星數據"""
        async with self._session_factory() as session:
            statement = select(Satellite).where(Satellite.id == satellite_id)
            results = await session.execute(statement)
            db_satellite = results.scalar_one_or_none()

            if db_satellite is None:
                return None

            for key, value in satellite_data.items():
                setattr(db_satellite, key, value)

            await session.commit()
            await session.refresh(db_satellite)
            return db_satellite

    async def delete_satellite(self, satellite_id: int) -> bool:
        """刪除衛星"""
        async with self._session_factory() as session:
            statement = select(Satellite).where(Satellite.id == satellite_id)
            results = await session.execute(statement)
            db_satellite = results.scalar_one_or_none()

            if db_satellite is None:
                return False

            await session.delete(db_satellite)
            await session.commit()
            return True

    async def get_satellite_passes(
        self, satellite_id: int, start_time: datetime, end_time: datetime
    ) -> List[SatellitePass]:
        """獲取衛星過境數據"""
        async with self._session_factory() as session:
            statement = (
                select(SatellitePass)
                .where(
                    and_(
                        SatellitePass.satellite_id == satellite_id,
                        SatellitePass.rise_time >= start_time,
                        SatellitePass.set_time <= end_time,
                    )
                )
                .order_by(SatellitePass.rise_time)
            )

            results = await session.execute(statement)
            return list(results.scalars().all())

    async def save_satellite_pass(
        self, satellite_pass_data: Dict[str, Any]
    ) -> SatellitePass:
        """保存衛星過境數據"""
        satellite_pass = SatellitePass(**satellite_pass_data)
        async with self._session_factory() as session:
            session.add(satellite_pass)
            await session.commit()
            await session.refresh(satellite_pass)
            return satellite_pass

    async def update_tle_data(
        self, satellite_id: int, tle_data: Dict[str, Any]
    ) -> Optional[Satellite]:
        """更新衛星的 TLE 數據"""
        return await self.update_satellite(
            satellite_id, {"tle_data": tle_data, "last_updated": datetime.utcnow()}
        )
