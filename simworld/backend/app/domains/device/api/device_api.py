import logging
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.domains.device.models.device_model import Device
from app.domains.device.services.device_service import DeviceService
from app.domains.device.adapters.sqlmodel_device_repository import (
    SQLModelDeviceRepository,
)
from app.domains.device.models.dto import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse as DeviceSchema,
)  # 使用領域內的 DTO 模型

logger = logging.getLogger(__name__)
router = APIRouter()


# 依賴注入函數，創建設備服務實例
async def get_device_service(
    session: AsyncSession = Depends(get_session),
) -> DeviceService:
    """獲取設備服務實例，用於依賴注入"""
    repository = SQLModelDeviceRepository(session=session)
    return DeviceService(device_repository=repository)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DeviceSchema)
async def create_new_device(
    *,
    device_service: DeviceService = Depends(get_device_service),
    device_in: DeviceCreate,
) -> Any:
    """
    創建一個新的設備。
    """
    logger.info(f"API: Received request to create device: {device_in.name}")
    try:
        created_device = await device_service.create_device(device_data=device_in)
        return DeviceSchema.from_orm(created_device)
    except HTTPException:
        # 直接重新拋出 HTTPException
        raise
    except Exception as e:
        # 記錄並包裝其他異常
        logger.error(f"API Error creating device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the device: {str(e)}",
        )


@router.get("/", response_model=List[DeviceSchema])
async def read_devices(
    device_service: DeviceService = Depends(get_device_service),
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = Query(None, description="Filter by device role"),
    active_only: bool = Query(False, description="Get only active devices"),
) -> Any:
    """
    獲取設備列表，可選按角色過濾。
    """
    logger.info(
        f"API: Received request to read devices (skip={skip}, limit={limit}, role={role}, active_only={active_only})"
    )

    devices = await device_service.get_devices(
        skip=skip, limit=limit, role=role, active_only=active_only
    )

    return [DeviceSchema.from_orm(device) for device in devices]


@router.get("/{device_id}", response_model=DeviceSchema)
async def read_device_by_id(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service),
) -> Any:
    """
    根據 ID 獲取單個設備。
    """
    logger.info(f"API: Received request to read device with ID: {device_id}")
    try:
        device = await device_service.get_device_by_id(device_id=device_id)
        return DeviceSchema.from_orm(device)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API Error reading device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while reading the device: {str(e)}",
        )


@router.put("/{device_id}", response_model=DeviceSchema)
async def update_existing_device(
    *,
    device_service: DeviceService = Depends(get_device_service),
    device_id: int,
    device_in: DeviceUpdate,
) -> Any:
    """
    更新現有設備。
    """
    logger.info(f"API: Received request to update device with ID: {device_id}")
    try:
        updated_device = await device_service.update_device(
            device_id=device_id, device_data=device_in
        )
        return DeviceSchema.from_orm(updated_device)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API Error updating device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the device: {str(e)}",
        )


@router.delete("/{device_id}", response_model=DeviceSchema)
async def delete_device_by_id(
    *,
    device_service: DeviceService = Depends(get_device_service),
    device_id: int,
) -> Any:
    """
    刪除一個設備，並檢查系統中是否仍有足夠的必要設備。
    """
    logger.info(f"API: Received request to delete device with ID: {device_id}")
    try:
        deleted_device = await device_service.delete_device(device_id=device_id)
        return DeviceSchema.from_orm(deleted_device)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API Error deleting device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the device: {str(e)}",
        )
