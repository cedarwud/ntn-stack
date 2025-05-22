import logging
from typing import List, Optional, Dict, Any, Union, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domains.device.models.device_model import Device, DeviceRole
from app.domains.device.interfaces.device_repository import DeviceRepository
from app.domains.device.models.dto import (
    DeviceCreate,
    DeviceUpdate,
)  # 使用領域內的 DTO 模型


logger = logging.getLogger(__name__)


class SQLModelDeviceRepository(DeviceRepository):
    """SQLModel 設備存儲庫實現"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, obj_in: DeviceCreate) -> Device:
        """創建一個新的設備記錄"""
        logger.info(f"Attempting to create device: {obj_in.name}")
        try:
            # 創建 Device 記錄
            db_device = Device(
                name=obj_in.name,
                position_x=obj_in.position_x,
                position_y=obj_in.position_y,
                position_z=obj_in.position_z,
                orientation_x=obj_in.orientation_x,
                orientation_y=obj_in.orientation_y,
                orientation_z=obj_in.orientation_z,
                role=obj_in.role,
                power_dbm=obj_in.power_dbm,
                active=obj_in.active,
            )
            self.session.add(db_device)
            await self.session.commit()
            await self.session.refresh(db_device)
            logger.info(
                f"Successfully created device '{db_device.name}' with ID {db_device.id}"
            )
            return db_device
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating device '{obj_in.name}': {e}", exc_info=True)
            raise  # 重新拋出異常，讓上層處理

    async def get_by_id(self, device_id: int) -> Optional[Device]:
        """根據 ID 獲取設備"""
        logger.debug(f"Fetching device with ID: {device_id}")
        stmt = select(Device).where(Device.id == device_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Device]:
        """根據名稱獲取設備"""
        logger.debug(f"Fetching device with name: {name}")
        stmt = select(Device).where(Device.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        active_only: bool = False,
    ) -> Sequence[Device]:
        """獲取設備列表，可選按角色過濾和只返回活躍設備"""
        logger.debug(
            f"Fetching multiple devices (skip={skip}, limit={limit}, role={role}, active_only={active_only})"
        )

        # 基礎查詢
        query = select(Device)

        # 過濾條件
        if role:
            query = query.where(Device.role == role)

        if active_only:
            query = query.where(Device.active == True)

        # 添加分頁
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_active(self, *, role: Optional[str] = None) -> List[Device]:
        """獲取活躍的設備列表，可選按角色過濾"""
        return await self.get_multi(role=role, active_only=True)

    async def update(
        self, *, db_obj: Device, obj_in: Union[DeviceUpdate, Dict[str, Any]]
    ) -> Device:
        """更新設備資訊"""
        logger.debug(f"Updating device: {db_obj.name} (ID: {db_obj.id})")
        try:
            # 轉換輸入為字典
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)

            # 更新設備欄位
            for field in update_data:
                if field in update_data and hasattr(db_obj, field):
                    setattr(db_obj, field, update_data[field])

            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            logger.info(f"Successfully updated device: {db_obj.name} (ID: {db_obj.id})")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating device {db_obj.name}: {e}", exc_info=True)
            raise

    async def update_by_id(
        self, *, device_id: int, device_in: Union[DeviceUpdate, Dict[str, Any]]
    ) -> Device:
        """根據 ID 更新設備資訊"""
        logger.info(f"Attempting to update device with ID: {device_id}")
        try:
            db_device = await self.get_by_id(device_id=device_id)
            if db_device is None:
                raise ValueError(f"Device with ID {device_id} not found.")

            return await self.update(db_obj=db_device, obj_in=device_in)
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Error updating device with ID {device_id}: {e}", exc_info=True
            )
            raise

    async def remove(self, *, device_id: int) -> Optional[Device]:
        """刪除設備"""
        logger.debug(f"Removing device with ID: {device_id}")
        try:
            # 獲取設備
            db_device = await self.get_by_id(device_id=device_id)
            if db_device is None:
                logger.warning(f"Device with ID {device_id} not found for removal.")
                return None

            # 刪除設備
            await self.session.delete(db_device)
            await self.session.commit()
            logger.info(f"Successfully removed device with ID: {device_id}")

            return db_device
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Error removing device with ID {device_id}: {e}", exc_info=True
            )
            raise
