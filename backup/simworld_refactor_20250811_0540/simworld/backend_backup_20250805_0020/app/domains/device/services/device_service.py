import logging
from typing import List, Optional, Dict, Any, Union, Sequence
from fastapi import HTTPException, status

from app.domains.device.models.device_model import Device, DeviceRole
from app.domains.device.interfaces.device_repository import DeviceRepository
from app.domains.device.models.dto import (
    DeviceCreate,
    DeviceUpdate,
)  # 使用領域內的 DTO 模型

logger = logging.getLogger(__name__)


class DeviceService:
    """設備服務層，實現設備相關的業務邏輯"""

    def __init__(self, device_repository: DeviceRepository):
        self.device_repository = device_repository

    async def create_device(self, device_data: DeviceCreate) -> Device:
        """創建新設備，並檢查名稱是否已存在"""
        # 檢查名稱是否已存在
        existing_device = await self.device_repository.get_by_name(
            name=device_data.name
        )
        if existing_device:
            logger.warning(f"Device name '{device_data.name}' already exists.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A device with this name already exists.",
            )

        return await self.device_repository.create(obj_in=device_data)

    async def get_device_by_id(self, device_id: int) -> Device:
        """根據 ID 獲取設備，如果不存在則拋出 404 異常"""
        device = await self.device_repository.get_by_id(device_id=device_id)
        if not device:
            logger.warning(f"Device with ID {device_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
            )
        return device

    async def get_devices(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        active_only: bool = False,
    ) -> Sequence[Device]:
        """獲取設備列表，可選按角色過濾和只返回活躍設備"""
        return await self.device_repository.get_multi(
            skip=skip, limit=limit, role=role, active_only=active_only
        )

    async def update_device(self, device_id: int, device_data: DeviceUpdate) -> Device:
        """更新設備資訊"""
        # 先檢查設備是否存在
        await self.get_device_by_id(device_id=device_id)

        # 更新設備
        return await self.device_repository.update_by_id(
            device_id=device_id, device_in=device_data
        )

    async def delete_device(self, device_id: int) -> Device:
        """刪除設備，並檢查系統中是否仍有足夠的必要設備"""
        # 先查出要刪除的設備
        device = await self.get_device_by_id(device_id=device_id)

        # 查詢活躍設備列表
        all_active_devices = await self.device_repository.get_active()

        # 排除即將刪除的這個設備
        remaining_devices = [d for d in all_active_devices if d.id != device_id]

        # 檢查剩餘設備數量
        tx_count = sum(
            1 for d in remaining_devices if d.role == DeviceRole.DESIRED.value
        )
        rx_count = sum(
            1 for d in remaining_devices if d.role == DeviceRole.RECEIVER.value
        )
        jammer_count = sum(
            1 for d in remaining_devices if d.role == DeviceRole.JAMMER.value
        )

        if tx_count < 1 or rx_count < 1 or jammer_count < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系統必須至少有一個發射器 (tx)、接收器 (rx)、干擾源 (jammer)。刪除失敗。",
            )

        # 通過檢查才實際刪除
        deleted_device = await self.device_repository.remove(device_id=device_id)
        return deleted_device
