import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domains.network.models.network_model import (
    Subscriber,
    GNodeB,
    UE,
    SubscriberStatus,
    GNodeBStatus,
    UEStatus,
)
from app.domains.network.interfaces.platform_service_interface import (
    PlatformServiceInterface,
    Open5GSServiceInterface,
    UERANSIMServiceInterface,
)
from app.domains.network.services.open5gs_service import Open5GSService


logger = logging.getLogger(__name__)


class PlatformService(PlatformServiceInterface):
    """平台服務，整合Open5GS和UERANSIM服務"""

    def __init__(
        self,
        open5gs_service: Optional[Open5GSServiceInterface] = None,
        ueransim_service: Optional[UERANSIMServiceInterface] = None,
    ):
        """初始化平台服務

        Args:
            open5gs_service: Open5GS服務實例，如果為None則創建默認實例
            ueransim_service: UERANSIM服務實例，如果為None則使用默認實例
        """
        self.open5gs_service = open5gs_service or Open5GSService()
        self.ueransim_service = ueransim_service
        logger.info("平台服務初始化完成")

    async def get_subscribers(self) -> List[Subscriber]:
        """獲取所有註冊的用戶

        Returns:
            包含所有用戶信息的列表
        """
        try:
            # 從Open5GS獲取原始用戶數據
            raw_subscribers = await self.open5gs_service.get_subscribers()

            # 轉換為領域模型
            subscribers = []
            for raw_sub in raw_subscribers:
                sub = self._convert_to_subscriber_model(raw_sub)
                if sub:
                    subscribers.append(sub)

            return subscribers
        except Exception as e:
            logger.error(f"獲取用戶列表失敗: {e}")
            return []

    async def get_subscriber(self, imsi: str) -> Optional[Subscriber]:
        """獲取特定IMSI的用戶信息

        Args:
            imsi: 用戶的IMSI識別碼

        Returns:
            用戶信息，如果未找到則返回None
        """
        try:
            # 從Open5GS獲取原始用戶數據
            raw_subscriber = await self.open5gs_service.get_subscriber_by_imsi(imsi)
            if not raw_subscriber:
                return None

            # 轉換為領域模型
            return self._convert_to_subscriber_model(raw_subscriber)
        except Exception as e:
            logger.error(f"獲取用戶 {imsi} 失敗: {e}")
            return None

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
            imsi: 用戶的IMSI識別碼
            key: 用戶的密鑰
            opc: 用戶的OPC值
            apn: 接入點名稱
            sst: 切片服務類型
            sd: 切片區分符

        Returns:
            操作是否成功
        """
        try:
            return await self.open5gs_service.add_subscriber(
                imsi, key, opc, apn, sst, sd
            )
        except Exception as e:
            logger.error(f"創建用戶 {imsi} 失敗: {e}")
            return False

    async def delete_subscriber(self, imsi: str) -> bool:
        """刪除用戶

        Args:
            imsi: 用戶的IMSI識別碼

        Returns:
            操作是否成功
        """
        try:
            return await self.open5gs_service.remove_subscriber(imsi)
        except Exception as e:
            logger.error(f"刪除用戶 {imsi} 失敗: {e}")
            return False

    async def get_gnbs(self) -> List[GNodeB]:
        """獲取所有gNodeB信息

        Returns:
            包含所有gNodeB信息的列表
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return []

        try:
            # 從UERANSIM獲取原始gNodeB數據
            raw_gnbs = await self.ueransim_service.get_gnbs()

            # 轉換為領域模型
            gnbs = []
            for raw_gnb in raw_gnbs:
                gnb = self._convert_to_gnodeb_model(raw_gnb)
                if gnb:
                    gnbs.append(gnb)

            return gnbs
        except Exception as e:
            logger.error(f"獲取gNodeB列表失敗: {e}")
            return []

    async def get_ues(self) -> List[UE]:
        """獲取所有UE信息

        Returns:
            包含所有UE信息的列表
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return []

        try:
            # 從UERANSIM獲取原始UE數據
            raw_ues = await self.ueransim_service.get_ues()

            # 轉換為領域模型
            ues = []
            for raw_ue in raw_ues:
                ue = self._convert_to_ue_model(raw_ue)
                if ue:
                    ues.append(ue)

            return ues
        except Exception as e:
            logger.error(f"獲取UE列表失敗: {e}")
            return []

    async def start_gnb(self, gnb_id: str) -> bool:
        """啟動指定的gNodeB

        Args:
            gnb_id: gNodeB識別碼

        Returns:
            操作是否成功
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return False

        try:
            return await self.ueransim_service.start_gnb(gnb_id)
        except Exception as e:
            logger.error(f"啟動gNodeB {gnb_id} 失敗: {e}")
            return False

    async def stop_gnb(self, gnb_id: str) -> bool:
        """停止指定的gNodeB

        Args:
            gnb_id: gNodeB識別碼

        Returns:
            操作是否成功
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return False

        try:
            return await self.ueransim_service.stop_gnb(gnb_id)
        except Exception as e:
            logger.error(f"停止gNodeB {gnb_id} 失敗: {e}")
            return False

    async def start_ue(self, ue_id: str) -> bool:
        """啟動指定的UE

        Args:
            ue_id: UE識別碼

        Returns:
            操作是否成功
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return False

        try:
            return await self.ueransim_service.start_ue(ue_id)
        except Exception as e:
            logger.error(f"啟動UE {ue_id} 失敗: {e}")
            return False

    async def stop_ue(self, ue_id: str) -> bool:
        """停止指定的UE

        Args:
            ue_id: UE識別碼

        Returns:
            操作是否成功
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return False

        try:
            return await self.ueransim_service.stop_ue(ue_id)
        except Exception as e:
            logger.error(f"停止UE {ue_id} 失敗: {e}")
            return False

    async def get_gnb_status(self, gnb_id: str) -> GNodeB:
        """獲取gNodeB的狀態信息

        Args:
            gnb_id: gNodeB識別碼

        Returns:
            gNodeB狀態信息
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return GNodeB(
                id=gnb_id,
                status=GNodeBStatus.UNKNOWN,
                mcc="000",
                mnc="00",
                tac="0",
                nci="0",
            )

        try:
            raw_status = await self.ueransim_service.get_gnb_status(gnb_id)
            return self._convert_to_gnodeb_model(raw_status)
        except Exception as e:
            logger.error(f"獲取gNodeB {gnb_id} 狀態失敗: {e}")
            return GNodeB(
                id=gnb_id,
                status=GNodeBStatus.ERROR,
                mcc="000",
                mnc="00",
                tac="0",
                nci="0",
            )

    async def get_ue_status(self, ue_id: str) -> UE:
        """獲取UE的狀態信息

        Args:
            ue_id: UE識別碼

        Returns:
            UE狀態信息
        """
        if not self.ueransim_service:
            logger.warning("UERANSIM服務未配置")
            return UE(
                id=ue_id,
                imsi="000000000000000",
                status=UEStatus.UNKNOWN,
                mcc="000",
                mnc="00",
                key="00000000000000000000000000000000",
                opc="00000000000000000000000000000000",
            )

        try:
            raw_status = await self.ueransim_service.get_ue_status(ue_id)
            return self._convert_to_ue_model(raw_status)
        except Exception as e:
            logger.error(f"獲取UE {ue_id} 狀態失敗: {e}")
            return UE(
                id=ue_id,
                imsi="000000000000000",
                status=UEStatus.ERROR,
                mcc="000",
                mnc="00",
                key="00000000000000000000000000000000",
                opc="00000000000000000000000000000000",
            )

    # 輔助方法：將原始數據轉換為領域模型
    def _convert_to_subscriber_model(
        self, raw_data: Dict[str, Any]
    ) -> Optional[Subscriber]:
        """將Open5GS用戶數據轉換為領域模型

        Args:
            raw_data: 原始用戶數據

        Returns:
            轉換後的領域模型，如果轉換失敗則返回None
        """
        try:
            # 獲取基本信息
            imsi = raw_data.get("imsi")
            if not imsi:
                return None

            # 獲取安全信息
            security = raw_data.get("security", {})
            key = security.get("k", "")
            opc = security.get("opc", "")

            # 獲取切片信息
            slices = raw_data.get("slice", [])
            apn = "internet"
            sst = 1
            sd = "0xffffff"

            if slices and len(slices) > 0:
                slice_info = slices[0]
                sst = slice_info.get("sst", 1)
                sd = slice_info.get("sd", "0xffffff")

                sessions = slice_info.get("session", [])
                if sessions and len(sessions) > 0:
                    apn = sessions[0].get("name", "internet")

            # 創建領域模型
            return Subscriber(
                imsi=imsi,
                key=key,
                opc=opc,
                status=SubscriberStatus.ACTIVE,
                apn=apn,
                sst=sst,
                sd=sd,
                created_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"轉換用戶數據失敗: {e}")
            return None

    def _convert_to_gnodeb_model(self, raw_data: Dict[str, Any]) -> GNodeB:
        """將UERANSIM gNodeB數據轉換為領域模型

        Args:
            raw_data: 原始gNodeB數據

        Returns:
            轉換後的領域模型
        """
        try:
            # 獲取基本信息
            gnb_id = raw_data.get("id", "unknown")
            name = raw_data.get("name")
            status_str = raw_data.get("status", "unknown")

            # 映射狀態
            status_map = {
                "running": GNodeBStatus.RUNNING,
                "stopped": GNodeBStatus.STOPPED,
                "error": GNodeBStatus.ERROR,
                "unknown": GNodeBStatus.UNKNOWN,
            }
            status = status_map.get(status_str.lower(), GNodeBStatus.UNKNOWN)

            # 獲取網絡配置
            mcc = raw_data.get("mcc", "000")
            mnc = raw_data.get("mnc", "00")
            tac = raw_data.get("tac", "0")
            nci = raw_data.get("nci", "0")

            # 獲取其他配置
            amf_addr = raw_data.get("amf_addr")
            gnb_addr = raw_data.get("gnb_addr")

            # 創建領域模型
            return GNodeB(
                id=gnb_id,
                name=name,
                status=status,
                mcc=mcc,
                mnc=mnc,
                tac=tac,
                nci=nci,
                amf_addr=amf_addr,
                gnb_addr=gnb_addr,
                config=raw_data,
            )
        except Exception as e:
            logger.error(f"轉換gNodeB數據失敗: {e}")
            return GNodeB(
                id=raw_data.get("id", "unknown"),
                status=GNodeBStatus.ERROR,
                mcc="000",
                mnc="00",
                tac="0",
                nci="0",
            )

    def _convert_to_ue_model(self, raw_data: Dict[str, Any]) -> UE:
        """將UERANSIM UE數據轉換為領域模型

        Args:
            raw_data: 原始UE數據

        Returns:
            轉換後的領域模型
        """
        try:
            # 獲取基本信息
            ue_id = raw_data.get("id", "unknown")
            name = raw_data.get("name")
            imsi = raw_data.get("imsi", "000000000000000")
            status_str = raw_data.get("status", "unknown")

            # 映射狀態
            status_map = {
                "connected": UEStatus.CONNECTED,
                "disconnected": UEStatus.DISCONNECTED,
                "registering": UEStatus.REGISTERING,
                "error": UEStatus.ERROR,
                "unknown": UEStatus.UNKNOWN,
            }
            status = status_map.get(status_str.lower(), UEStatus.UNKNOWN)

            # 獲取網絡配置
            mcc = raw_data.get("mcc", "000")
            mnc = raw_data.get("mnc", "00")
            key = raw_data.get("key", "00000000000000000000000000000000")
            opc = raw_data.get("opc", "00000000000000000000000000000000")

            # 獲取其他信息
            apn = raw_data.get("apn", "internet")
            sst = raw_data.get("sst", 1)
            sd = raw_data.get("sd", "0xffffff")
            connected_gnb = raw_data.get("connected_gnb")
            ip_addr = raw_data.get("ip_addr")

            # 創建領域模型
            return UE(
                id=ue_id,
                name=name,
                imsi=imsi,
                status=status,
                mcc=mcc,
                mnc=mnc,
                key=key,
                opc=opc,
                apn=apn,
                sst=sst,
                sd=sd,
                connected_gnb=connected_gnb,
                ip_addr=ip_addr,
                config=raw_data,
            )
        except Exception as e:
            logger.error(f"轉換UE數據失敗: {e}")
            return UE(
                id=raw_data.get("id", "unknown"),
                imsi=raw_data.get("imsi", "000000000000000"),
                status=UEStatus.ERROR,
                mcc="000",
                mnc="00",
                key="00000000000000000000000000000000",
                opc="00000000000000000000000000000000",
            )


# 創建服務實例
platform_service = PlatformService()
