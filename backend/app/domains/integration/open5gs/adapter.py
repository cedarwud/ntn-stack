from typing import List, Dict, Any, Optional


class Open5GSAdapter:
    """Open5GS 適配器，用於與平台層的 Open5GS 交互"""

    def __init__(self, service):
        """初始化適配器

        Args:
            service: Open5GS服務實例
        """
        self.service = service

    async def get_subscribers(self) -> List[Dict[str, Any]]:
        """獲取所有註冊的用戶

        Returns:
            包含所有用戶信息的列表
        """
        return await self.service.get_subscribers()

    async def get_subscriber_by_imsi(self, imsi: str) -> Optional[Dict[str, Any]]:
        """通過IMSI獲取特定用戶

        Args:
            imsi: 用戶的IMSI識別碼

        Returns:
            用戶信息字典，如果未找到則返回None
        """
        return await self.service.get_subscriber_by_imsi(imsi)

    async def add_subscriber(
        self,
        imsi: str,
        key: str,
        opc: str,
        apn: str = "internet",
        sst: int = 1,
        sd: str = "0xffffff",
    ) -> bool:
        """添加新用戶到Open5GS

        Args:
            imsi: 用戶的IMSI識別碼
            key: 用戶的密鑰
            opc: 用戶的OPC值
            apn: 接入點名稱，默認為"internet"
            sst: 切片服務類型，默認為1
            sd: 切片區分符，默認為"0xffffff"

        Returns:
            操作是否成功
        """
        return await self.service.add_subscriber(imsi, key, opc, apn, sst, sd)

    async def remove_subscriber(self, imsi: str) -> bool:
        """移除用戶

        Args:
            imsi: 要移除的用戶的IMSI識別碼

        Returns:
            操作是否成功
        """
        return await self.service.remove_subscriber(imsi)
