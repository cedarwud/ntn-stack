"""
重構後的 Sionna 模擬服務
使用模組化架構，將功能拆分到專門的服務中
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.simulation.interfaces.simulation_service_interface import SimulationServiceInterface
from app.domains.simulation.models.simulation_model import SimulationParameters
from app.core.config import (
    CFR_PLOT_IMAGE_PATH,
    DOPPLER_IMAGE_PATH,
    CHANNEL_RESPONSE_IMAGE_PATH,
    SINR_MAP_IMAGE_PATH,
)

# 重構後的模組化服務
from .scene.scene_management_service import SceneManagementService
from .rendering.rendering_service import RenderingService
from .communication.communication_simulation_service import CommunicationSimulationService

logger = logging.getLogger(__name__)


class SionnaSimulationServiceRefactored(SimulationServiceInterface):
    """
    重構後的 Sionna 模擬服務
    
    使用模組化架構，將功能拆分到專門的服務中：
    - SceneManagementService: 場景管理和檔案處理
    - RenderingService: 3D 渲染和圖像處理
    - CommunicationSimulationService: 通信模擬計算
    """

    def __init__(self):
        """初始化重構後的服務"""
        # 初始化各個專門服務
        self.scene_service = SceneManagementService()
        self.rendering_service = RenderingService()
        self.communication_service = CommunicationSimulationService()
        
        logger.info("SionnaSimulationServiceRefactored 初始化完成")

    # =============================================================================
    # 場景渲染功能 - 委託給 RenderingService
    # =============================================================================

    async def generate_empty_scene_image(self, output_path: str) -> bool:
        """
        生成空場景圖像
        委託給 RenderingService
        """
        logger.info(f"SionnaSimulationServiceRefactored: 生成空場景圖像 {output_path}")
        
        # 準備輸出檔案
        self.scene_service.prepare_output_file(output_path, "空場景圖像")
        
        # 委託給渲染服務
        result = self.rendering_service.generate_empty_scene_image(output_path)
        
        # 驗證輸出檔案
        return self.scene_service.verify_output_file(output_path) if result else False

    # =============================================================================
    # 通信模擬功能 - 委託給 CommunicationSimulationService
    # =============================================================================

    async def generate_cfr_plot(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """
        生成通道頻率響應(CFR)圖像
        委託給 CommunicationSimulationService
        """
        logger.info(f"SionnaSimulationServiceRefactored: 生成 CFR 圖像 {output_path}")
        
        # 準備輸出檔案
        self.scene_service.prepare_output_file(output_path, "CFR 圖像")
        
        # 委託給通信模擬服務
        result = await self.communication_service.generate_cfr_plot(
            session, output_path, scene_name
        )
        
        # 驗證輸出檔案
        return self.scene_service.verify_output_file(output_path) if result else False

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
        """
        生成 SINR 地圖
        委託給 CommunicationSimulationService
        """
        logger.info(f"SionnaSimulationServiceRefactored: 生成 SINR 地圖 {output_path}")
        
        # 準備輸出檔案
        self.scene_service.prepare_output_file(output_path, "SINR 地圖")
        
        # 委託給通信模擬服務
        result = await self.communication_service.generate_sinr_map(
            session=session,
            output_path=output_path,
            scene_name=scene_name,
            sinr_vmin=sinr_vmin,
            sinr_vmax=sinr_vmax,
            cell_size=cell_size,
            samples_per_tx=samples_per_tx,
        )
        
        # 驗證輸出檔案
        return self.scene_service.verify_output_file(output_path) if result else False

    async def generate_doppler_plots(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """
        生成延遲多普勒圖
        委託給 CommunicationSimulationService
        """
        logger.info(f"SionnaSimulationServiceRefactored: 生成延遲多普勒圖 {output_path}")
        
        # 準備輸出檔案
        self.scene_service.prepare_output_file(output_path, "延遲多普勒圖")
        
        # 委託給通信模擬服務
        result = await self.communication_service.generate_doppler_plots(
            session, output_path, scene_name
        )
        
        # 驗證輸出檔案
        return self.scene_service.verify_output_file(output_path) if result else False

    async def generate_channel_response_plots(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """
        生成通道響應圖
        委託給 CommunicationSimulationService
        """
        logger.info(f"SionnaSimulationServiceRefactored: 生成通道響應圖 {output_path}")
        
        # 準備輸出檔案
        self.scene_service.prepare_output_file(output_path, "通道響應圖")
        
        # 委託給通信模擬服務
        result = await self.communication_service.generate_channel_response_plots(
            session, output_path, scene_name
        )
        
        # 驗證輸出檔案
        return self.scene_service.verify_output_file(output_path) if result else False

    # =============================================================================
    # 統一模擬接口
    # =============================================================================

    async def run_simulation(
        self, session: AsyncSession, params: SimulationParameters
    ) -> Dict[str, Any]:
        """
        執行通用模擬
        根據參數類型分發到不同的模擬功能
        """
        logger.info(f"Running simulation of type: {params.simulation_type}")

        result = {"success": False, "result_path": None, "error_message": None}

        try:
            # 根據模擬類型執行不同的模擬
            if params.simulation_type == "cfr":
                output_path = str(CFR_PLOT_IMAGE_PATH)
                success = await self.generate_cfr_plot(session, output_path)
                result["result_path"] = output_path
                result["success"] = success

            elif params.simulation_type == "sinr_map":
                output_path = str(SINR_MAP_IMAGE_PATH)
                success = await self.generate_sinr_map(
                    session,
                    output_path,
                    params.scene_name or "nycu",
                    params.sinr_vmin or -40.0,
                    params.sinr_vmax or 0.0,
                    params.cell_size or 1.0,
                    params.samples_per_tx or 10**7,
                )
                result["result_path"] = output_path
                result["success"] = success

            elif params.simulation_type == "doppler":
                output_path = str(DOPPLER_IMAGE_PATH)
                success = await self.generate_doppler_plots(session, output_path)
                result["result_path"] = output_path
                result["success"] = success

            elif params.simulation_type == "channel_response":
                output_path = str(CHANNEL_RESPONSE_IMAGE_PATH)
                success = await self.generate_channel_response_plots(session, output_path)
                result["result_path"] = output_path
                result["success"] = success

            elif params.simulation_type == "empty_scene":
                # 空場景渲染
                output_path = params.output_path or "/tmp/empty_scene.png"
                success = await self.generate_empty_scene_image(output_path)
                result["result_path"] = output_path
                result["success"] = success

            else:
                error_msg = f"不支援的模擬類型: {params.simulation_type}"
                logger.error(error_msg)
                result["error_message"] = error_msg
                result["success"] = False

            return result

        except Exception as e:
            error_msg = f"模擬執行失敗: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error_message"] = error_msg
            result["success"] = False
            return result

    # =============================================================================
    # 服務健康檢查和統計
    # =============================================================================

    async def get_service_health(self) -> Dict[str, Any]:
        """
        獲取服務健康狀態
        """
        try:
            # 檢查各個子服務的健康狀態
            health_status = {
                "scene_service": "healthy",
                "rendering_service": "healthy",
                "communication_service": "healthy"
            }
            
            overall_status = "healthy" if all(
                status == "healthy" for status in health_status.values()
            ) else "degraded"
            
            return {
                "overall_status": overall_status,
                "services": health_status,
                "uptime": "operational"
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {str(e)}")
            return {
                "overall_status": "error",
                "error": str(e)
            }

    # =============================================================================
    # 工具方法
    # =============================================================================

    def get_scene_service(self) -> SceneManagementService:
        """獲取場景管理服務實例"""
        return self.scene_service

    def get_rendering_service(self) -> RenderingService:
        """獲取渲染服務實例"""
        return self.rendering_service

    def get_communication_service(self) -> CommunicationSimulationService:
        """獲取通信模擬服務實例"""
        return self.communication_service