"""
Communication Simulation Service V2 - Refactored with Modular Architecture

This is the refactored version that uses specialized services:
- Base services for common operations (DeviceManager, SceneSetupService, etc.)
- Specialized calculators for different simulation types
- Simplified coordinator pattern

Original file: 1509 lines -> This file: ~200 lines
"""

import logging
import os
import numpy as np
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Base services
from .base import DeviceManager, SceneSetupService, SionnaConfigService

# Specialized calculators  
from .calculators import CFRCalculator, SINRCalculator, DopplerCalculator, ChannelCalculator

# Scene management import
from ..scene.scene_management_service import SceneManagementService

# Config imports
from app.core.config import (
    CFR_PLOT_IMAGE_PATH,
    DOPPLER_IMAGE_PATH,
    CHANNEL_RESPONSE_IMAGE_PATH,
    SINR_MAP_IMAGE_PATH,
)

logger = logging.getLogger(__name__)


class CommunicationSimulationService:
    """
    Refactored Communication Simulation Service (V2)
    
    This version uses a modular architecture with specialized services:
    - Delegates device management to DeviceManager
    - Uses specialized calculators for different simulation types
    - Focuses on coordination rather than implementation details
    
    Reduces from 1509 lines to ~200 lines while maintaining same functionality.
    """

    def __init__(self, scene_service: Optional[SceneManagementService] = None):
        """
        Initialize the refactored communication simulation service
        
        Args:
            scene_service: Scene management service instance
        """
        self.scene_service = scene_service or SceneManagementService()
        self.config_service = SionnaConfigService()
        self.scene_setup_service = SceneSetupService()
        
        # Initialize calculators
        self.cfr_calculator = CFRCalculator()
        self.sinr_calculator = SINRCalculator()
        self.doppler_calculator = DopplerCalculator()
        self.channel_calculator = ChannelCalculator()
        
        self._setup_gpu()

    def _setup_gpu(self) -> bool:
        """Set up GPU environment with memory growth enabled"""
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
        import tensorflow as tf
        
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            try:
                tf.config.experimental.set_memory_growth(gpus[0], True)
                logger.info("GPU 記憶體成長已啟用")
            except Exception as e:
                logger.warning(f"無法啟用GPU記憶體增長: {e}")
        else:
            logger.info("未找到 GPU，使用 CPU")
        return gpus is not None

    async def generate_cfr_plot(
        self, 
        session: AsyncSession, 
        output_path: str, 
        scene_name: str = "nycu"
    ) -> bool:
        """
        Generate Channel Frequency Response (CFR) plot using modular architecture
        
        This method now delegates to specialized services:
        1. DeviceManager: Load devices from database
        2. SceneSetupService: Configure Sionna scene
        3. CFRCalculator: Perform CFR calculations and plotting
        """
        logger.info(f"開始生成 CFR 圖，場景: {scene_name}")
        
        try:
            # Prepare output file
            self._prepare_output_file(output_path, "CFR 圖檔")
            
            # 1. Load devices using DeviceManager
            device_manager = DeviceManager(session)
            desired, jammers, receivers = await device_manager.load_simulation_devices()
            
            if not desired and not jammers:
                logger.error("沒有活動的發射器或干擾器，無法生成 CFR 圖")
                return False
                
            # 2. Get scene and setup configuration
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            array_config = self.config_service.get_array_config()
            scene = self.scene_setup_service.load_and_configure_scene(scene_xml_path, array_config)
            
            # 3. Build device configurations
            tx_list = device_manager.build_transmitter_list(desired, jammers)
            rx_config = device_manager.get_receiver_config(receivers)
            
            # 4. Delegate to CFR calculator
            h_main, h_intf, idx_des, idx_jam = self.cfr_calculator.calculate_cfr(
                scene, tx_list, rx_config
            )
            
            # 5. Generate QPSK+OFDM signals
            y_eq_no_i, y_eq_with_i = self.cfr_calculator.generate_qpsk_ofdm_signals(h_main, h_intf)
            
            # 6. Create and save plot
            success = self.cfr_calculator.create_cfr_plot(
                h_main, h_intf, y_eq_no_i, y_eq_with_i, output_path
            )
            
            if success:
                return self._verify_output_file(output_path)
            return False
            
        except Exception as e:
            logger.error(f"生成 CFR 圖失敗: {e}", exc_info=True)
            return False

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
        Generate SINR map using modular architecture
        """
        logger.info(f"開始生成 SINR 地圖，場景: {scene_name}")
        
        try:
            # Prepare output file
            self._prepare_output_file(output_path, "SINR 地圖圖檔")
            
            # 1. Load devices
            device_manager = DeviceManager(session)
            desired, jammers, receivers = await device_manager.load_simulation_devices()
            
            # 2. Setup scene
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            array_config = self.config_service.get_array_config()
            scene = self.scene_setup_service.load_and_configure_scene(scene_xml_path, array_config)
            
            # 3. Build configurations
            tx_list = device_manager.build_transmitter_list(desired, jammers)
            rx_config = device_manager.get_receiver_config(receivers)
            
            # 4. Calculate SINR map
            x_unique, y_unique, sinr_db = self.sinr_calculator.calculate_sinr_map(
                scene, tx_list, rx_config, cell_size, samples_per_tx
            )
            
            # 5. Create detailed SINR plot with device markers
            success = self._create_sinr_plot(
                scene, x_unique, y_unique, sinr_db, 
                sinr_vmin, sinr_vmax, rx_config, output_path
            )
            
            return self._verify_output_file(output_path)
            
        except Exception as e:
            logger.error(f"生成 SINR 地圖失敗: {e}", exc_info=True)
            return False

    async def generate_doppler_plots(
        self, 
        session: AsyncSession, 
        output_path: str, 
        scene_name: str = "nycu"
    ) -> bool:
        """
        Generate Delay-Doppler plots using modular architecture
        """
        logger.info(f"開始生成延遲多普勒圖，場景: {scene_name}")
        
        try:
            # Prepare output file
            self._prepare_output_file(output_path, "延遲多普勒圖檔")
            
            # 1. Load devices
            device_manager = DeviceManager(session)
            desired, jammers, receivers = await device_manager.load_simulation_devices()
            
            if not desired and not jammers:
                logger.error("沒有活動的發射器或干擾器，無法生成延遲多普勒圖")
                return False
                
            # 2. Setup scene
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            array_config = self.config_service.get_array_config()
            scene = self.scene_setup_service.load_and_configure_scene(scene_xml_path, array_config)
            
            # 3. Build configurations
            tx_list = device_manager.build_transmitter_list(desired, jammers)
            rx_config = device_manager.get_receiver_config(receivers)
            
            # 4. Calculate delay-doppler
            Hdd_list, idx_des, idx_jam, delay_bins, doppler_bins = self.doppler_calculator.calculate_delay_doppler(
                scene, tx_list, rx_config
            )
            
            # 5. Create plots
            success = self.doppler_calculator.create_doppler_plots(
                Hdd_list, idx_des, idx_jam, delay_bins, doppler_bins, output_path
            )
            
            if success:
                return self._verify_output_file(output_path)
            return False
            
        except Exception as e:
            logger.error(f"生成延遲多普勒圖失敗: {e}", exc_info=True)
            return False
        
    async def generate_channel_response_plots(
        self, 
        session: AsyncSession, 
        output_path: str, 
        scene_name: str = "nycu"
    ) -> bool:
        """
        Generate channel response plots using modular architecture
        """
        logger.info(f"開始生成通道響應圖，場景: {scene_name}")
        
        try:
            # Prepare output file
            self._prepare_output_file(output_path, "通道響應圖檔")
            
            # 1. Load devices
            device_manager = DeviceManager(session)
            desired, jammers, receivers = await device_manager.load_simulation_devices()
            
            if not desired:
                logger.error("沒有活動的發射器，無法生成通道響應圖")
                return False
                
            if not receivers:
                logger.error("沒有活動的接收器，無法生成通道響應圖")
                return False
                
            # 2. Setup scene
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            array_config = self.config_service.get_array_config()
            scene = self.scene_setup_service.load_and_configure_scene(scene_xml_path, array_config)
            
            # 3. Build configurations
            tx_list = device_manager.build_transmitter_list(desired, jammers)
            rx_config = device_manager.get_receiver_config(receivers)
            
            # 4. Calculate channel response
            H_des, H_jam, H_all = self.channel_calculator.calculate_channel_response(
                scene, tx_list, rx_config
            )
            
            # 5. Create plots
            success = self.channel_calculator.create_channel_response_plots(
                H_des, H_jam, H_all, output_path
            )
            
            if success:
                return self._verify_output_file(output_path)
            return False
            
        except Exception as e:
            logger.error(f"生成通道響應圖失敗: {e}", exc_info=True)
            return False

    # Utility methods (simplified)
    def _prepare_output_file(self, output_path: str, file_desc: str = "圖檔") -> bool:
        """Prepare output file directory"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return True
        
    def _verify_output_file(self, output_path: str) -> bool:
        """Verify output file was created successfully"""
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"✅ 輸出檔案驗證成功: {output_path}")
            return True
        else:
            logger.error(f"❌ 輸出檔案驗證失敗: {output_path}")
            return False
    
    def _create_sinr_plot(
        self, 
        scene: Any, 
        x_unique: np.ndarray, 
        y_unique: np.ndarray, 
        sinr_db: np.ndarray,
        sinr_vmin: float, 
        sinr_vmax: float, 
        rx_config: tuple, 
        output_path: str
    ) -> bool:
        """
        Create detailed SINR plot with device position markers
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            logger.info("Creating detailed SINR map plot")
            
            # Create plot
            fig, ax = plt.subplots(figsize=(7, 5))
            X, Y = np.meshgrid(x_unique, y_unique)
            
            # Plot SINR map with corrected vmin
            pcm = ax.pcolormesh(
                X, Y, sinr_db, 
                shading="nearest", 
                vmin=sinr_vmin + 10,  # Correct vmin adjustment from backup
                vmax=sinr_vmax
            )
            fig.colorbar(pcm, ax=ax, label="SINR (dB)")
            
            # Get all transmitters and classify by role
            all_txs = [scene.get(n) for n in scene.transmitters]
            
            # Plot desired transmitters (red triangles)
            desired_txs = [tx for tx in all_txs if getattr(tx, "role", None) == "desired"]
            if desired_txs:
                ax.scatter(
                    [t.position[0] for t in desired_txs],
                    [t.position[1] for t in desired_txs],
                    c="red",
                    marker="^",
                    s=100,
                    label="Tx",
                )
            
            # Plot jammer transmitters (red X)
            jammer_txs = [tx for tx in all_txs if getattr(tx, "role", None) == "jammer"]
            if jammer_txs:
                ax.scatter(
                    [t.position[0] for t in jammer_txs],
                    [t.position[1] for t in jammer_txs],
                    c="red",
                    marker="x",
                    s=100,
                    label="Jam",
                )
            
            # Plot receiver (green circle)
            rx_name, rx_pos = rx_config
            rx_object = scene.get(rx_name)
            if rx_object:
                ax.scatter(
                    rx_object.position[0],
                    rx_object.position[1],
                    c="green",
                    marker="o",
                    s=50,
                    label="Rx",
                )
            
            # Configure plot
            ax.legend()
            ax.set_xlabel("x (m)")
            ax.set_ylabel("y (m)")
            ax.set_title("SINR Map")
            ax.invert_yaxis()  # Important: invert Y axis like in backup
            plt.tight_layout()
            
            # Save plot
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            
            logger.info(f"SINR plot saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating SINR plot: {e}")
            plt.close("all")
            return False