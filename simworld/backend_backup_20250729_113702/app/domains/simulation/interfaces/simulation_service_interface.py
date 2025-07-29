from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.simulation.models.simulation_model import SimulationParameters


class SimulationServiceInterface(ABC):
    """模擬服務接口，定義模擬服務的抽象方法"""

    @abstractmethod
    async def generate_empty_scene_image(self, output_path: str) -> bool:
        """生成空場景圖像"""
        pass

    @abstractmethod
    async def generate_cfr_plot(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """生成通道頻率響應(CFR)圖像"""
        pass

    @abstractmethod
    async def generate_sinr_map(
        self,
        session: AsyncSession,
        output_path: str,
        scene_name: str = "nycu",
        sinr_vmin: float = -40.0,
        sinr_vmax: float = 0.0,
        cell_size: float = 1.0,
        samples_per_tx: int = 10**7,
    ) -> bool:
        """生成SINR地圖"""
        pass

    @abstractmethod
    async def generate_doppler_plots(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """生成延遲多普勒圖"""
        pass

    @abstractmethod
    async def generate_channel_response_plots(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """生成通道響應圖"""
        pass

    @abstractmethod
    async def run_simulation(
        self, session: AsyncSession, params: SimulationParameters
    ) -> Dict[str, Any]:
        """
        根據提供的參數執行通用模擬

        Args:
            session: 數據庫會話
            params: 模擬參數

        Returns:
            Dict[str, Any]: 模擬結果，至少包含 'success' 和 'result_path' 鍵
        """
        pass
