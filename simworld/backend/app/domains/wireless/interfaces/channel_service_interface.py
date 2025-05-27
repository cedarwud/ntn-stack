"""
無線通道服務介面

定義 Sionna 通道模擬與 UERANSIM 整合的服務契約。
遵循 DDD 的依賴反轉原則，由 domain 層定義介面，
infrastructure 層實現具體的服務。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.wireless.models.channel_model import (
    ChannelParameters,
    ChannelResponse,
    RANParameters,
    ChannelToRANMappingRequest,
    ChannelToRANMappingResponse,
    UERANSIMConfiguration,
    ChannelQualityMetrics,
)


class ChannelServiceInterface(ABC):
    """無線通道服務介面"""

    @abstractmethod
    async def extract_channel_parameters_from_sionna(
        self,
        session: AsyncSession,
        scene_name: str,
        tx_device_id: int,
        rx_device_id: int,
        frequency_hz: float,
    ) -> ChannelParameters:
        """
        從 Sionna 模擬結果中提取通道參數

        Args:
            session: 資料庫會話
            scene_name: 場景名稱
            tx_device_id: 發射器設備 ID
            rx_device_id: 接收器設備 ID
            frequency_hz: 載波頻率

        Returns:
            ChannelParameters: 提取的通道參數

        Raises:
            ValueError: 參數無效
            RuntimeError: Sionna 模擬失敗
        """
        pass

    @abstractmethod
    async def convert_channel_to_ran_parameters(
        self,
        request: ChannelToRANMappingRequest,
    ) -> ChannelToRANMappingResponse:
        """
        將 Sionna 通道參數轉換為 UERANSIM RAN 參數

        Args:
            request: 轉換請求

        Returns:
            ChannelToRANMappingResponse: 轉換結果

        Raises:
            ValueError: 轉換參數無效
            RuntimeError: 轉換失敗
        """
        pass

    @abstractmethod
    async def generate_ueransim_configuration(
        self,
        ran_parameters: RANParameters,
        ue_count: int = 1,
        deployment_mode: str = "container",
    ) -> UERANSIMConfiguration:
        """
        根據 RAN 參數生成 UERANSIM 配置

        Args:
            ran_parameters: RAN 參數
            ue_count: UE 數量
            deployment_mode: 部署模式

        Returns:
            UERANSIMConfiguration: UERANSIM 配置

        Raises:
            ValueError: 參數無效
            RuntimeError: 配置生成失敗
        """
        pass

    @abstractmethod
    async def deploy_ueransim_configuration(
        self,
        configuration: UERANSIMConfiguration,
    ) -> Dict[str, Any]:
        """
        部署 UERANSIM 配置到容器或獨立實例

        Args:
            configuration: UERANSIM 配置

        Returns:
            Dict[str, Any]: 部署結果

        Raises:
            RuntimeError: 部署失敗
        """
        pass

    @abstractmethod
    async def monitor_channel_quality(
        self,
        channel_id: str,
        measurement_duration_s: float = 10.0,
    ) -> ChannelQualityMetrics:
        """
        監控通道品質指標

        Args:
            channel_id: 通道 ID
            measurement_duration_s: 測量持續時間

        Returns:
            ChannelQualityMetrics: 通道品質指標

        Raises:
            ValueError: 參數無效
            RuntimeError: 監控失敗
        """
        pass

    @abstractmethod
    async def update_ran_parameters_realtime(
        self,
        gnb_id: int,
        channel_parameters: ChannelParameters,
    ) -> bool:
        """
        即時更新 RAN 參數以反映通道變化

        Args:
            gnb_id: gNodeB ID
            channel_parameters: 最新通道參數

        Returns:
            bool: 更新是否成功

        Raises:
            ValueError: 參數無效
            RuntimeError: 更新失敗
        """
        pass

    @abstractmethod
    async def calculate_interference_impact(
        self,
        target_channel: ChannelParameters,
        interfering_channels: List[ChannelParameters],
    ) -> Dict[str, float]:
        """
        計算干擾對目標通道的影響

        Args:
            target_channel: 目標通道參數
            interfering_channels: 干擾通道參數列表

        Returns:
            Dict[str, float]: 干擾影響評估

        Raises:
            ValueError: 參數無效
            RuntimeError: 計算失敗
        """
        pass

    @abstractmethod
    async def optimize_ran_configuration(
        self,
        current_ran: RANParameters,
        target_metrics: Dict[str, float],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> RANParameters:
        """
        根據目標指標優化 RAN 配置

        Args:
            current_ran: 當前 RAN 參數
            target_metrics: 目標性能指標
            constraints: 優化約束條件

        Returns:
            RANParameters: 優化後的 RAN 參數

        Raises:
            ValueError: 參數無效
            RuntimeError: 優化失敗
        """
        pass
