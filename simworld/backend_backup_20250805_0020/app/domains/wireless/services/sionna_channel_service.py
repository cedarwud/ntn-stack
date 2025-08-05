"""
Sionna Channel Simulation Service
負責執行基於 GPU 的無線通道模擬和射線追蹤
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import json

from ..models.channel_models import (
    SionnaChannelResponse,
    ChannelSimulationRequest,
    ChannelPathComponent,
    ChannelModelMetrics,
)

logger = logging.getLogger(__name__)


class SionnaChannelSimulationService:
    """Sionna 無線通道模擬服務"""

    def __init__(self, enable_gpu: bool = True, max_concurrent_simulations: int = 10):
        self.enable_gpu = enable_gpu
        self.max_concurrent_simulations = max_concurrent_simulations
        self.active_simulations: Dict[str, Any] = {}
        self.simulation_semaphore = asyncio.Semaphore(max_concurrent_simulations)
        self.metrics = ChannelModelMetrics()

        # 模擬 Sionna 初始化
        self._init_sionna_environment()

    def _init_sionna_environment(self):
        """初始化 Sionna 模擬環境"""
        try:
            # 在實際部署中，這裡會初始化 Sionna 和 TensorFlow
            logger.info("初始化 Sionna 模擬環境...")

            # 檢查 GPU 可用性
            if self.enable_gpu:
                try:
                    # import tensorflow as tf
                    # self.gpu_available = len(tf.config.list_physical_devices('GPU')) > 0
                    self.gpu_available = True  # 模擬 GPU 可用
                    logger.info(f"GPU 加速: {'啟用' if self.gpu_available else '禁用'}")
                except Exception as e:
                    logger.warning(f"GPU 檢測失敗，使用 CPU 模式: {e}")
                    self.gpu_available = False
            else:
                self.gpu_available = False

            # 設定常用的通道模型參數
            self.channel_models = {
                "urban": {"max_reflections": 3, "typical_path_loss": 128.1},
                "suburban": {"max_reflections": 2, "typical_path_loss": 120.9},
                "rural": {"max_reflections": 1, "typical_path_loss": 113.2},
                "indoor": {"max_reflections": 5, "typical_path_loss": 89.5},
                "satellite": {"max_reflections": 0, "typical_path_loss": 162.4},
            }

            logger.info("Sionna 模擬環境初始化完成")

        except Exception as e:
            logger.error(f"Sionna 初始化失敗: {e}")
            raise

    async def simulate_channel(
        self, request: ChannelSimulationRequest
    ) -> List[SionnaChannelResponse]:
        """執行無線通道模擬"""

        async with self.simulation_semaphore:
            simulation_start = datetime.utcnow()

            try:
                logger.info(f"開始通道模擬: {request.simulation_id}")

                # 註冊活躍模擬
                self.active_simulations[request.simulation_id] = {
                    "start_time": simulation_start,
                    "request": request,
                    "status": "running",
                }

                # 執行模擬
                results = await self._run_sionna_simulation(request)

                # 更新統計
                simulation_time = (
                    datetime.utcnow() - simulation_start
                ).total_seconds() * 1000
                self._update_metrics(len(results), simulation_time, success=True)

                # 清理活躍模擬
                self.active_simulations[request.simulation_id]["status"] = "completed"

                logger.info(
                    f"通道模擬完成: {request.simulation_id}, 產生 {len(results)} 個通道響應"
                )
                return results

            except Exception as e:
                logger.error(f"通道模擬失敗: {request.simulation_id}, 錯誤: {e}")
                self._update_metrics(0, 0, success=False)
                self.active_simulations[request.simulation_id]["status"] = "failed"
                raise

    async def _run_sionna_simulation(
        self, request: ChannelSimulationRequest
    ) -> List[SionnaChannelResponse]:
        """執行實際的 Sionna 模擬"""

        # 在實際部署中，這裡會調用 Sionna 的 RT 模組
        # 現在先實現一個高保真度的模擬版本

        results = []
        environment_model = self.channel_models.get(
            request.environment_type, self.channel_models["urban"]
        )

        # 模擬 GPU 計算延遲
        if self.gpu_available:
            await asyncio.sleep(0.1)  # GPU 模擬 100ms
        else:
            await asyncio.sleep(0.5)  # CPU 模擬 500ms

        # 為每對發送端-接收端生成通道響應
        for tx_idx, tx_info in enumerate(request.transmitters):
            for rx_idx, rx_info in enumerate(request.receivers):

                channel_response = await self._simulate_link_channel(
                    tx_info, rx_info, request, environment_model, tx_idx, rx_idx
                )
                results.append(channel_response)

        return results

    async def _simulate_link_channel(
        self,
        tx_info: Dict[str, Any],
        rx_info: Dict[str, Any],
        request: ChannelSimulationRequest,
        environment_model: Dict[str, Any],
        tx_idx: int,
        rx_idx: int,
    ) -> SionnaChannelResponse:
        """模擬單一鏈路的通道響應"""

        # 計算距離和路徑損耗
        tx_pos = tx_info.get("position", [0, 0, 0])
        rx_pos = rx_info.get("position", [1000, 0, 0])

        distance_3d = np.sqrt(sum((tx_pos[i] - rx_pos[i]) ** 2 for i in range(3)))

        # 基本路徑損耗計算 (Free Space Path Loss + 環境修正)
        frequency_ghz = request.carrier_frequency_hz / 1e9
        fspl_db = 20 * np.log10(distance_3d) + 20 * np.log10(frequency_ghz) + 32.44
        path_loss_db = fspl_db + environment_model["typical_path_loss"] - 32.44

        # 生成多路徑分量
        paths = await self._generate_multipath_components(
            tx_pos, rx_pos, environment_model, request.max_reflections
        )

        # 計算通道矩陣
        channel_matrix_real, channel_matrix_imag = self._compute_channel_matrix(
            paths, request.carrier_frequency_hz
        )

        # 計算統計特性
        rms_delay_spread = self._calculate_rms_delay_spread(paths)
        coherence_bandwidth = (
            1 / (5 * rms_delay_spread / 1e9) if rms_delay_spread > 0 else 1e6
        )

        # 速度相關的計算
        tx_velocity = tx_info.get("velocity", [0, 0, 0])
        rx_velocity = rx_info.get("velocity", [0, 0, 0])
        relative_velocity = np.sqrt(
            sum((tx_velocity[i] - rx_velocity[i]) ** 2 for i in range(3))
        )
        doppler_max = relative_velocity * frequency_ghz / 3e8
        coherence_time = 9 / (16 * np.pi * doppler_max) if doppler_max > 0 else 1000

        channel_id = f"ch_{request.simulation_id}_{tx_idx}_{rx_idx}"

        return SionnaChannelResponse(
            channel_id=channel_id,
            tx_position=tx_pos,
            tx_velocity=tx_velocity,
            rx_position=rx_pos,
            rx_velocity=rx_velocity,
            frequency_hz=request.carrier_frequency_hz,
            bandwidth_hz=request.bandwidth_hz,
            path_loss_db=path_loss_db,
            shadowing_db=np.random.normal(0, 8),  # 陰影衰落
            paths=paths,
            channel_matrix_real=channel_matrix_real,
            channel_matrix_imag=channel_matrix_imag,
            rms_delay_spread_ns=rms_delay_spread,
            coherence_bandwidth_hz=coherence_bandwidth,
            coherence_time_ms=coherence_time * 1000,
        )

    async def _generate_multipath_components(
        self,
        tx_pos: List[float],
        rx_pos: List[float],
        environment_model: Dict[str, Any],
        max_reflections: int,
    ) -> List[ChannelPathComponent]:
        """生成多路徑分量"""

        paths = []

        # 直射路徑 (Line of Sight)
        distance_3d = np.sqrt(sum((tx_pos[i] - rx_pos[i]) ** 2 for i in range(3)))
        los_delay_ns = distance_3d / 3e8 * 1e9

        # 計算方位角和仰角
        dx, dy, dz = [rx_pos[i] - tx_pos[i] for i in range(3)]
        azimuth = np.degrees(np.arctan2(dy, dx))
        elevation = np.degrees(np.arctan2(dz, np.sqrt(dx**2 + dy**2)))

        # LOS 路徑
        los_path = ChannelPathComponent(
            delay_ns=los_delay_ns,
            power_db=0.0,  # 參考功率
            azimuth_deg=azimuth,
            elevation_deg=elevation,
            doppler_hz=0.0,
        )
        paths.append(los_path)

        # 反射路徑
        num_reflections = min(max_reflections, environment_model["max_reflections"])
        for i in range(num_reflections):
            # 模擬反射造成的額外延遲和功率損失
            extra_delay_ns = np.random.exponential(50) + 10  # 額外延遲
            power_loss_db = -10 - i * 6 - np.random.exponential(3)  # 功率損失

            # 反射造成的角度偏移
            azimuth_offset = np.random.normal(0, 15)
            elevation_offset = np.random.normal(0, 10)

            reflected_path = ChannelPathComponent(
                delay_ns=los_delay_ns + extra_delay_ns,
                power_db=power_loss_db,
                azimuth_deg=azimuth + azimuth_offset,
                elevation_deg=elevation + elevation_offset,
                doppler_hz=np.random.normal(0, 50),  # 多普勒頻移
            )
            paths.append(reflected_path)

        return paths

    def _compute_channel_matrix(
        self, paths: List[ChannelPathComponent], frequency_hz: float
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """計算通道矩陣"""

        # 簡化的 SISO 通道矩陣 (1x1)
        # 在實際實現中，這會是更複雜的 MIMO 矩陣

        channel_complex = 0 + 0j

        for path in paths:
            # 路徑增益
            amplitude = 10 ** (path.power_db / 20)

            # 相位（基於延遲）
            phase = 2 * np.pi * frequency_hz * path.delay_ns / 1e9

            # 複數通道係數
            path_coefficient = amplitude * np.exp(1j * phase)
            channel_complex += path_coefficient

        # 分離實部和虛部
        real_part = [[float(channel_complex.real)]]
        imag_part = [[float(channel_complex.imag)]]

        return real_part, imag_part

    def _calculate_rms_delay_spread(self, paths: List[ChannelPathComponent]) -> float:
        """計算 RMS 延遲擴散"""

        if not paths:
            return 0.0

        # 功率權重
        powers = [10 ** (path.power_db / 10) for path in paths]
        delays = [path.delay_ns for path in paths]

        total_power = sum(powers)
        if total_power == 0:
            return 0.0

        # 平均延遲
        mean_delay = sum(p * d for p, d in zip(powers, delays)) / total_power

        # RMS 延遲擴散
        rms_delay_spread = np.sqrt(
            sum(p * (d - mean_delay) ** 2 for p, d in zip(powers, delays)) / total_power
        )

        return float(rms_delay_spread)

    def _update_metrics(
        self, channels_processed: int, processing_time_ms: float, success: bool
    ):
        """更新效能指標"""

        self.metrics.total_channels_processed += channels_processed if success else 0

        # 更新平均處理時間
        if success and channels_processed > 0:
            current_avg = self.metrics.average_conversion_time_ms
            total_processed = self.metrics.total_channels_processed

            if total_processed > channels_processed:
                # 加權平均
                weight_old = (total_processed - channels_processed) / total_processed
                weight_new = channels_processed / total_processed
                self.metrics.average_conversion_time_ms = (
                    current_avg * weight_old + processing_time_ms * weight_new
                )
            else:
                self.metrics.average_conversion_time_ms = processing_time_ms

        # 更新成功率
        # 這裡簡化處理，實際應該追蹤更詳細的統計

        # 模擬 GPU 使用率
        if self.gpu_available:
            self.metrics.gpu_utilization = min(
                0.8, len(self.active_simulations) / self.max_concurrent_simulations
            )

        # 模擬記憶體使用
        self.metrics.memory_usage_mb = (
            len(self.active_simulations) * 256.0
        )  # 每個模擬約 256MB

        self.metrics.last_update = datetime.utcnow()

    async def get_simulation_status(
        self, simulation_id: str
    ) -> Optional[Dict[str, Any]]:
        """獲取模擬狀態"""
        return self.active_simulations.get(simulation_id)

    async def cancel_simulation(self, simulation_id: str) -> bool:
        """取消模擬"""
        if simulation_id in self.active_simulations:
            self.active_simulations[simulation_id]["status"] = "cancelled"
            return True
        return False

    async def get_metrics(self) -> ChannelModelMetrics:
        """獲取效能指標"""
        return self.metrics

    async def cleanup_completed_simulations(self, max_age_hours: int = 24):
        """清理已完成的模擬記錄"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        to_remove = []
        for sim_id, sim_info in self.active_simulations.items():
            if (
                sim_info["status"] in ["completed", "failed", "cancelled"]
                and sim_info["start_time"] < cutoff_time
            ):
                to_remove.append(sim_id)

        for sim_id in to_remove:
            del self.active_simulations[sim_id]

        logger.info(f"清理了 {len(to_remove)} 個過期的模擬記錄")
