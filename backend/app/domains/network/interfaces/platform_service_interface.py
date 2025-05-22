from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.domains.network.models.network_model import Subscriber, GNodeB, UE


class Open5GSServiceInterface(ABC):
    """Open5GS 服務接口，定義 Open5GS 相關操作"""

    @abstractmethod
    async def get_subscribers(self) -> List[Dict[str, Any]]:
        """獲取所有註冊的用戶

        Returns:
            包含所有用戶信息的列表
        """
        pass

    @abstractmethod
    async def get_subscriber_by_imsi(self, imsi: str) -> Optional[Dict[str, Any]]:
        """通過 IMSI 獲取特定用戶

        Args:
            imsi: 用戶的 IMSI 識別碼

        Returns:
            用戶信息字典，如果未找到則返回 None
        """
        pass

    @abstractmethod
    async def add_subscriber(
        self,
        imsi: str,
        key: str,
        opc: str,
        apn: str = "internet",
        sst: int = 1,
        sd: str = "0xffffff",
    ) -> bool:
        """添加新用戶到 Open5GS

        Args:
            imsi: 用戶的 IMSI 識別碼
            key: 用戶的密鑰
            opc: 用戶的 OPC 值
            apn: 接入點名稱，默認為 "internet"
            sst: 切片服務類型，默認為 1
            sd: 切片區分符，默認為 "0xffffff"

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def remove_subscriber(self, imsi: str) -> bool:
        """移除用戶

        Args:
            imsi: 要移除的用戶的 IMSI 識別碼

        Returns:
            操作是否成功
        """
        pass


class UERANSIMServiceInterface(ABC):
    """UERANSIM 服務接口，定義 UERANSIM 相關操作"""

    @abstractmethod
    async def get_gnbs(self) -> List[Dict[str, Any]]:
        """獲取所有 gNodeB 信息

        Returns:
            包含所有 gNodeB 信息的列表
        """
        pass

    @abstractmethod
    async def get_ues(self) -> List[Dict[str, Any]]:
        """獲取所有 UE 信息

        Returns:
            包含所有 UE 信息的列表
        """
        pass

    @abstractmethod
    async def start_gnb(self, gnb_id: str) -> bool:
        """啟動指定的 gNodeB

        Args:
            gnb_id: gNodeB 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def stop_gnb(self, gnb_id: str) -> bool:
        """停止指定的 gNodeB

        Args:
            gnb_id: gNodeB 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def start_ue(self, ue_id: str) -> bool:
        """啟動指定的 UE

        Args:
            ue_id: UE 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def stop_ue(self, ue_id: str) -> bool:
        """停止指定的 UE

        Args:
            ue_id: UE 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def get_gnb_status(self, gnb_id: str) -> Dict[str, Any]:
        """獲取 gNodeB 的狀態信息

        Args:
            gnb_id: gNodeB 識別碼

        Returns:
            gNodeB 狀態信息
        """
        pass

    @abstractmethod
    async def get_ue_status(self, ue_id: str) -> Dict[str, Any]:
        """獲取 UE 的狀態信息

        Args:
            ue_id: UE 識別碼

        Returns:
            UE 狀態信息
        """
        pass


class PlatformServiceInterface(ABC):
    """平台服務接口，整合 Open5GS 和 UERANSIM 服務"""

    @abstractmethod
    async def get_subscribers(self) -> List[Subscriber]:
        """獲取所有註冊的用戶

        Returns:
            包含所有用戶信息的列表
        """
        pass

    @abstractmethod
    async def get_subscriber(self, imsi: str) -> Optional[Subscriber]:
        """獲取特定 IMSI 的用戶信息

        Args:
            imsi: 用戶的 IMSI 識別碼

        Returns:
            用戶信息，如果未找到則返回 None
        """
        pass

    @abstractmethod
    async def create_subscriber(
        self,
        imsi: str,
        key: str,
        opc: str,
        apn: str = "internet",
        sst: int = 1,
        sd: str = "0xffffff",
    ) -> bool:
        """創建新用戶

        Args:
            imsi: 用戶的 IMSI 識別碼
            key: 用戶的密鑰
            opc: 用戶的 OPC 值
            apn: 接入點名稱
            sst: 切片服務類型
            sd: 切片區分符

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def delete_subscriber(self, imsi: str) -> bool:
        """刪除用戶

        Args:
            imsi: 用戶的 IMSI 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def get_gnbs(self) -> List[GNodeB]:
        """獲取所有 gNodeB 信息

        Returns:
            包含所有 gNodeB 信息的列表
        """
        pass

    @abstractmethod
    async def get_ues(self) -> List[UE]:
        """獲取所有 UE 信息

        Returns:
            包含所有 UE 信息的列表
        """
        pass

    @abstractmethod
    async def start_gnb(self, gnb_id: str) -> bool:
        """啟動指定的 gNodeB

        Args:
            gnb_id: gNodeB 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def stop_gnb(self, gnb_id: str) -> bool:
        """停止指定的 gNodeB

        Args:
            gnb_id: gNodeB 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def start_ue(self, ue_id: str) -> bool:
        """啟動指定的 UE

        Args:
            ue_id: UE 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def stop_ue(self, ue_id: str) -> bool:
        """停止指定的 UE

        Args:
            ue_id: UE 識別碼

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def get_gnb_status(self, gnb_id: str) -> GNodeB:
        """獲取 gNodeB 的狀態信息

        Args:
            gnb_id: gNodeB 識別碼

        Returns:
            gNodeB 狀態信息
        """
        pass

    @abstractmethod
    async def get_ue_status(self, ue_id: str) -> UE:
        """獲取 UE 的狀態信息

        Args:
            ue_id: UE 識別碼

        Returns:
            UE 狀態信息
        """
        pass
