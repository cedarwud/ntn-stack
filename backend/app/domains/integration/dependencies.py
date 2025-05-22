from fastapi import Depends

from app.domains.integration.open5gs.service import Open5GSService
from app.domains.integration.open5gs.adapter import Open5GSAdapter
from app.domains.integration.ueransim.service import UERANSIMService
from app.domains.integration.ueransim.adapter import UERANSIMAdapter

# 單例服務實例
_open5gs_service = None
_ueransim_service = None


def get_open5gs_service():
    """獲取Open5GS服務單例

    Returns:
        Open5GS服務實例
    """
    global _open5gs_service
    if _open5gs_service is None:
        _open5gs_service = Open5GSService()
    return _open5gs_service


def get_ueransim_service():
    """獲取UERANSIM服務單例

    Returns:
        UERANSIM服務實例
    """
    global _ueransim_service
    if _ueransim_service is None:
        _ueransim_service = UERANSIMService()
    return _ueransim_service


def get_open5gs_adapter(service: Open5GSService = Depends(get_open5gs_service)):
    """獲取Open5GS適配器

    Args:
        service: Open5GS服務實例，通過依賴注入

    Returns:
        Open5GS適配器實例
    """
    return Open5GSAdapter(service)


def get_ueransim_adapter(service: UERANSIMService = Depends(get_ueransim_service)):
    """獲取UERANSIM適配器

    Args:
        service: UERANSIM服務實例，通過依賴注入

    Returns:
        UERANSIM適配器實例
    """
    return UERANSIMAdapter(service)
