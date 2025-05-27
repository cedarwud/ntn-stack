"""
無線通道領域模組

包含 Sionna 無線通道模型與 UERANSIM 整合的相關功能。

核心概念：
- 無線通道模型：描述物理層的電磁波傳播特性
- 通道參數轉換：將 Sionna 模擬結果轉換為 UERANSIM 參數
- RAN 配置管理：管理 UERANSIM 的無線參數配置
"""

from app.domains.wireless.models.channel_model import (
    ChannelParameters,
    ChannelResponse,
    RANParameters,
    ChannelToRANMappingRequest,
    ChannelToRANMappingResponse,
)

from app.domains.wireless.interfaces.channel_service_interface import (
    ChannelServiceInterface,
)

from app.domains.wireless.services.channel_to_ran_service import (
    ChannelToRANService,
    channel_to_ran_service,
)

__all__ = [
    "ChannelParameters",
    "ChannelResponse",
    "RANParameters",
    "ChannelToRANMappingRequest",
    "ChannelToRANMappingResponse",
    "ChannelServiceInterface",
    "ChannelToRANService",
    "channel_to_ran_service",
]
