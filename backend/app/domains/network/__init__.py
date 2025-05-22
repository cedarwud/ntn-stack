"""
網路領域模組

包含5G網路平台相關功能，整合Open5GS和UERANSIM服務。
"""

from app.domains.network.models.network_model import (
    Subscriber,
    GNodeB,
    UE,
    SubscriberStatus,
    GNodeBStatus,
    UEStatus,
    NetworkSliceType,
)
from app.domains.network.interfaces.platform_service_interface import (
    Open5GSServiceInterface,
    UERANSIMServiceInterface,
    PlatformServiceInterface,
)
from app.domains.network.services.open5gs_service import Open5GSService
from app.domains.network.services.platform_service import (
    PlatformService,
    platform_service,
)
