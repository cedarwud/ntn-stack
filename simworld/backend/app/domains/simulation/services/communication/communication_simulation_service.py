"""
Communication Simulation Service

This service handles Sionna-based communication simulations including:
- CFR (Channel Frequency Response) generation
- SINR (Signal-to-Interference-plus-Noise Ratio) mapping
- Delay-Doppler analysis
- Channel response visualization
"""

import logging
import os
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

# Sionna imports
from sionna.rt import (
    load_scene,
    Transmitter as SionnaTransmitter,
    Receiver as SionnaReceiver,
    PlanarArray,
    PathSolver,
    subcarrier_frequencies,
    RadioMapSolver,
)

# Device domain imports
from app.domains.device.models.device_model import Device, DeviceRole
from app.domains.device.services.device_service import DeviceService
from app.domains.device.adapters.sqlmodel_device_repository import SQLModelDeviceRepository

# Config imports
from app.core.config import (
    CFR_PLOT_IMAGE_PATH,
    DOPPLER_IMAGE_PATH,
    CHANNEL_RESPONSE_IMAGE_PATH,
    SINR_MAP_IMAGE_PATH,
)

# Scene management import
from ..scene.scene_management_service import SceneManagementService

logger = logging.getLogger(__name__)


class CommunicationSimulationService:
    """
    Communication Simulation Service
    
    Provides Sionna-based communication system simulation capabilities
    """

    def __init__(self, scene_service: Optional[SceneManagementService] = None):
        """
        Initialize the communication simulation service
        
        Args:
            scene_service: Scene management service instance
        """
        self.scene_service = scene_service or SceneManagementService()
        self._setup_gpu()

    def _setup_gpu(self) -> bool:
        """
        Set up GPU environment with memory growth enabled
        
        Returns:
            True if GPU is available, False if using CPU
        """
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
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
        生成通道頻率響應(CFR)圖像
        
        Args:
            session: 資料庫會話
            output_path: 輸出路徑
            scene_name: 場景名稱
            
        Returns:
            bool: 生成是否成功
        """
        logger.info(f"開始生成 CFR 圖像，場景: {scene_name}")
        
        try:
            # 載入場景和設備
            scene, devices = await self._load_scene_and_devices(session, scene_name)
            if not scene or not devices:
                return False

            # 設置發射器和接收器
            transmitters, receivers = self._setup_transceivers(scene, devices)
            if not transmitters or not receivers:
                logger.error("未找到有效的發射器或接收器")
                return False

            # 執行路徑求解
            logger.info("執行路徑求解...")
            path_solver = PathSolver(scene, method="exhaustive")
            paths = path_solver(
                transmitters, receivers, 
                check_scene=False, 
                max_depth=5
            )

            # 生成子載波頻率
            subcarrier_freq = subcarrier_frequencies(num_subcarriers=76, subcarrier_spacing=15e3)

            # 計算通道頻率響應
            logger.info("計算通道頻率響應...")
            cfr = paths.apply_frequency_response(subcarrier_freq)
            
            # 生成圖表
            return self._generate_cfr_plots(cfr, output_path)

        except Exception as e:
            logger.error(f"生成 CFR 圖像失敗: {e}", exc_info=True)
            plt.close("all")
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
        生成 SINR 地圖
        
        Args:
            session: 資料庫會話
            output_path: 輸出路徑
            scene_name: 場景名稱
            sinr_vmin: SINR 最小值 (dB)
            sinr_vmax: SINR 最大值 (dB)
            cell_size: 網格大小 (m)
            samples_per_tx: 每個發射器的樣本數
            
        Returns:
            bool: 生成是否成功
        """
        logger.info(f"開始生成 SINR 地圖，場景: {scene_name}")
        
        try:
            # 載入場景和設備
            scene, devices = await self._load_scene_and_devices(session, scene_name)
            if not scene or not devices:
                return False

            # 設置發射器
            transmitters, _ = self._setup_transceivers(scene, devices)
            if not transmitters:
                logger.error("未找到有效的發射器")
                return False

            # 設置 RadioMapSolver
            logger.info("設置 RadioMapSolver...")
            radio_map_solver = RadioMapSolver(
                scene=scene,
                solver_sample_spacing=cell_size,
                dtype=tf.complex64
            )

            # 計算 SINR 地圖
            logger.info("計算 SINR 地圖...")
            sinr_map = radio_map_solver(
                transmitters=transmitters,
                max_depth=5,
                num_samples=samples_per_tx
            )

            # 生成圖表
            return self._generate_sinr_plots(sinr_map, output_path, sinr_vmin, sinr_vmax)

        except Exception as e:
            logger.error(f"生成 SINR 地圖失敗: {e}", exc_info=True)
            plt.close("all")
            return False

    async def generate_doppler_plots(
        self,
        session: AsyncSession,
        output_path: str,
        scene_name: str = "nycu"
    ) -> bool:
        """
        生成延遲多普勒圖
        
        Args:
            session: 資料庫會話
            output_path: 輸出路徑
            scene_name: 場景名稱
            
        Returns:
            bool: 生成是否成功
        """
        logger.info(f"開始生成延遲多普勒圖，場景: {scene_name}")
        
        try:
            # 載入場景和設備
            scene, devices = await self._load_scene_and_devices(session, scene_name)
            if not scene or not devices:
                return False

            # 設置發射器和接收器
            transmitters, receivers = self._setup_transceivers(scene, devices)
            if not transmitters or not receivers:
                logger.error("未找到有效的發射器或接收器")
                return False

            # 執行路徑求解
            logger.info("執行路徑求解...")
            path_solver = PathSolver(scene, method="exhaustive")
            paths = path_solver(
                transmitters, receivers,
                check_scene=False,
                max_depth=5
            )

            # 計算延遲多普勒響應
            logger.info("計算延遲多普勒響應...")
            tau = np.linspace(0, 100e-9, 100)  # 延遲軸
            fD = np.linspace(-1000, 1000, 200)  # 多普勒軸
            
            # 這裡應該有實際的延遲多普勒計算邏輯
            # 暫時使用模擬數據
            delay_doppler = self._compute_delay_doppler_response(paths, tau, fD)
            
            # 生成圖表
            return self._generate_doppler_plots(delay_doppler, tau, fD, output_path)

        except Exception as e:
            logger.error(f"生成延遲多普勒圖失敗: {e}", exc_info=True)
            plt.close("all")
            return False

    async def generate_channel_response_plots(
        self,
        session: AsyncSession,
        output_path: str,
        scene_name: str = "nycu"
    ) -> bool:
        """
        生成通道響應圖
        
        Args:
            session: 資料庫會話
            output_path: 輸出路徑
            scene_name: 場景名稱
            
        Returns:
            bool: 生成是否成功
        """
        logger.info(f"開始生成通道響應圖，場景: {scene_name}")
        
        try:
            # 載入場景和設備
            scene, devices = await self._load_scene_and_devices(session, scene_name)
            if not scene or not devices:
                return False

            # 設置發射器和接收器
            transmitters, receivers = self._setup_transceivers(scene, devices)
            if not transmitters or not receivers:
                logger.error("未找到有效的發射器或接收器")
                return False

            # 執行路徑求解
            logger.info("執行路徑求解...")
            path_solver = PathSolver(scene, method="exhaustive")
            paths = path_solver(
                transmitters, receivers,
                check_scene=False,
                max_depth=5
            )

            # 生成子載波頻率
            subcarrier_freq = subcarrier_frequencies(num_subcarriers=64, subcarrier_spacing=15e3)

            # 計算通道響應
            logger.info("計算通道響應...")
            channel_response = paths.apply_frequency_response(subcarrier_freq)
            
            # 生成圖表
            return self._generate_channel_response_plots(channel_response, output_path)

        except Exception as e:
            logger.error(f"生成通道響應圖失敗: {e}", exc_info=True)
            plt.close("all")
            return False

    async def _load_scene_and_devices(
        self, 
        session: AsyncSession, 
        scene_name: str
    ) -> Tuple[Optional[Any], List[Device]]:
        """載入場景和設備"""
        try:
            # 這裡需要實際的場景載入邏輯
            # 暫時返回 None 和空列表
            scene = None
            devices = []
            
            # 獲取設備
            device_repository = SQLModelDeviceRepository(session)
            device_service = DeviceService(device_repository)
            devices = await device_service.get_all_devices()
            
            logger.info(f"載入了 {len(devices)} 個設備")
            return scene, devices
            
        except Exception as e:
            logger.error(f"載入場景和設備失敗: {e}")
            return None, []

    def _setup_transceivers(self, scene: Any, devices: List[Device]) -> Tuple[List[Any], List[Any]]:
        """設置發射器和接收器"""
        transmitters = []
        receivers = []
        
        try:
            for device in devices:
                if device.role == DeviceRole.TRANSMITTER:
                    # 創建發射器
                    tx = self._create_transmitter(device)
                    if tx:
                        transmitters.append(tx)
                elif device.role == DeviceRole.RECEIVER:
                    # 創建接收器
                    rx = self._create_receiver(device)
                    if rx:
                        receivers.append(rx)
                        
            logger.info(f"設置了 {len(transmitters)} 個發射器和 {len(receivers)} 個接收器")
            return transmitters, receivers
            
        except Exception as e:
            logger.error(f"設置收發器失敗: {e}")
            return [], []

    def _create_transmitter(self, device: Device) -> Optional[Any]:
        """創建發射器"""
        try:
            # 這裡需要實際的發射器創建邏輯
            # 暫時返回 None
            return None
        except Exception as e:
            logger.error(f"創建發射器失敗: {e}")
            return None

    def _create_receiver(self, device: Device) -> Optional[Any]:
        """創建接收器"""
        try:
            # 這裡需要實際的接收器創建邏輯
            # 暫時返回 None
            return None
        except Exception as e:
            logger.error(f"創建接收器失敗: {e}")
            return None

    def _compute_delay_doppler_response(self, paths: Any, tau: np.ndarray, fD: np.ndarray) -> np.ndarray:
        """計算延遲多普勒響應"""
        # 暫時使用模擬數據
        return np.random.random((len(tau), len(fD)))

    def _generate_cfr_plots(self, cfr: Any, output_path: str) -> bool:
        """生成 CFR 圖表"""
        try:
            # 實際的 CFR 圖表生成邏輯
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 暫時使用模擬數據
            data = np.random.random((64, 76))
            im = ax.imshow(data, aspect='auto', cmap='viridis')
            
            ax.set_title('Channel Frequency Response (CFR)')
            ax.set_xlabel('Subcarrier Index')
            ax.set_ylabel('OFDM Symbol')
            
            plt.colorbar(im, ax=ax)
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            return True
            
        except Exception as e:
            logger.error(f"生成 CFR 圖表失敗: {e}")
            return False

    def _generate_sinr_plots(self, sinr_map: Any, output_path: str, vmin: float, vmax: float) -> bool:
        """生成 SINR 圖表"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 暫時使用模擬數據
            data = np.random.uniform(vmin, vmax, (100, 100))
            im = ax.imshow(data, extent=[-50, 50, -50, 50], cmap='RdYlBu_r', vmin=vmin, vmax=vmax)
            
            ax.set_title('SINR Map')
            ax.set_xlabel('X Position (m)')
            ax.set_ylabel('Y Position (m)')
            
            plt.colorbar(im, ax=ax, label='SINR (dB)')
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            return True
            
        except Exception as e:
            logger.error(f"生成 SINR 圖表失敗: {e}")
            return False

    def _generate_doppler_plots(self, delay_doppler: np.ndarray, tau: np.ndarray, fD: np.ndarray, output_path: str) -> bool:
        """生成延遲多普勒圖表"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            im = ax.imshow(
                20 * np.log10(np.abs(delay_doppler) + 1e-10),
                extent=[fD[0], fD[-1], tau[-1]*1e9, tau[0]*1e9],
                aspect='auto',
                cmap='viridis'
            )
            
            ax.set_title('Delay-Doppler Response')
            ax.set_xlabel('Doppler Frequency (Hz)')
            ax.set_ylabel('Delay (ns)')
            
            plt.colorbar(im, ax=ax, label='Magnitude (dB)')
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            return True
            
        except Exception as e:
            logger.error(f"生成延遲多普勒圖表失敗: {e}")
            return False

    def _generate_channel_response_plots(self, channel_response: Any, output_path: str) -> bool:
        """生成通道響應圖表"""
        try:
            fig = plt.figure(figsize=(18, 5))
            
            # 暫時使用模擬數據
            T, F = 14, 64  # OFDM 符號數和子載波數
            H_des = np.random.random((T, F)) + 1j * np.random.random((T, F))
            H_jam = np.random.random((T, F)) + 1j * np.random.random((T, F))
            H_all = H_des + H_jam
            
            t_axis = np.arange(T)
            f_axis = np.arange(F)
            T_mesh, F_mesh = np.meshgrid(t_axis, f_axis, indexing="ij")

            # 子圖 1: H_des
            ax1 = fig.add_subplot(131, projection="3d")
            ax1.plot_surface(F_mesh, T_mesh, np.abs(H_des), cmap="viridis", edgecolor="none")
            ax1.set_xlabel("子載波")
            ax1.set_ylabel("OFDM 符號")
            ax1.set_title("‖H_des‖")

            # 子圖 2: H_jam
            ax2 = fig.add_subplot(132, projection="3d")
            ax2.plot_surface(F_mesh, T_mesh, np.abs(H_jam), cmap="viridis", edgecolor="none")
            ax2.set_xlabel("子載波")
            ax2.set_ylabel("OFDM 符號")
            ax2.set_title("‖H_jam‖")

            # 子圖 3: H_all
            ax3 = fig.add_subplot(133, projection="3d")
            ax3.plot_surface(F_mesh, T_mesh, np.abs(H_all), cmap="viridis", edgecolor="none")
            ax3.set_xlabel("子載波")
            ax3.set_ylabel("OFDM 符號")
            ax3.set_title("‖H_all‖")

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            
            return True
            
        except Exception as e:
            logger.error(f"生成通道響應圖表失敗: {e}")
            return False