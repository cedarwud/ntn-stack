from typing import List, Dict, Any, Optional


class UERANSIMAdapter:
    """UERANSIM 適配器，用於與平台層的 UERANSIM 交互"""

    def __init__(self, service):
        """初始化適配器

        Args:
            service: UERANSIM服務實例
        """
        self.service = service

    async def get_gnbs(self) -> List[Dict[str, Any]]:
        """獲取所有gNodeB信息

        Returns:
            gNodeB信息列表
        """
        return await self.service.get_gnbs()

    async def get_ues(self) -> List[Dict[str, Any]]:
        """獲取所有UE信息

        Returns:
            UE信息列表
        """
        return await self.service.get_ues()

    async def start_gnb(self, gnb_id: str) -> bool:
        """啟動指定的gNodeB

        Args:
            gnb_id: gNodeB的ID

        Returns:
            操作是否成功
        """
        return await self.service.start_gnb(gnb_id)

    async def stop_gnb(self, gnb_id: str) -> bool:
        """停止指定的gNodeB

        Args:
            gnb_id: gNodeB的ID

        Returns:
            操作是否成功
        """
        return await self.service.stop_gnb(gnb_id)

    async def start_ue(self, ue_id: str) -> bool:
        """啟動指定的UE

        Args:
            ue_id: UE的ID

        Returns:
            操作是否成功
        """
        return await self.service.start_ue(ue_id)

    async def stop_ue(self, ue_id: str) -> bool:
        """停止指定的UE

        Args:
            ue_id: UE的ID

        Returns:
            操作是否成功
        """
        return await self.service.stop_ue(ue_id)

    async def get_ue_status(self, ue_id: str) -> Dict[str, Any]:
        """獲取UE的狀態信息

        Args:
            ue_id: UE的ID

        Returns:
            UE狀態信息
        """
        return await self.service.get_ue_status(ue_id)

    async def get_gnb_status(self, gnb_id: str) -> Dict[str, Any]:
        """獲取gNodeB的狀態信息

        Args:
            gnb_id: gNodeB的ID

        Returns:
            gNodeB狀態信息
        """
        return await self.service.get_gnb_status(gnb_id)
