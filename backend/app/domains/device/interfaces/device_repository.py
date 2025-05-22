from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union, Sequence

from app.domains.device.models.device_model import Device
from app.domains.device.models.dto import (
    DeviceCreate,
    DeviceUpdate,
)  # 使用領域內的 DTO 模型


class DeviceRepository(ABC):
    """設備存儲庫接口，定義對設備數據的操作方法"""

    @abstractmethod
    async def create(self, obj_in: DeviceCreate) -> Device:
        """創建一個新的設備記錄"""
        pass

    @abstractmethod
    async def get_by_id(self, device_id: int) -> Optional[Device]:
        """根據 ID 獲取設備"""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Device]:
        """根據名稱獲取設備"""
        pass

    @abstractmethod
    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        active_only: bool = False
    ) -> Sequence[Device]:
        """獲取設備列表，可選按角色過濾和只返回活躍設備"""
        pass

    @abstractmethod
    async def get_active(self, *, role: Optional[str] = None) -> List[Device]:
        """獲取活躍的設備列表，可選按角色過濾"""
        pass

    @abstractmethod
    async def update(
        self, *, db_obj: Device, obj_in: Union[DeviceUpdate, Dict[str, Any]]
    ) -> Device:
        """更新設備資訊"""
        pass

    @abstractmethod
    async def update_by_id(
        self, *, device_id: int, device_in: Union[DeviceUpdate, Dict[str, Any]]
    ) -> Device:
        """根據 ID 更新設備資訊"""
        pass

    @abstractmethod
    async def remove(self, *, device_id: int) -> Optional[Device]:
        """刪除設備"""
        pass
