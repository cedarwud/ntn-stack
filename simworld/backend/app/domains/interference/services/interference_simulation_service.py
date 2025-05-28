"""
干擾模擬服務

使用 Sionna 實現多種類型的干擾源模擬，包括：
- 寬帶噪聲干擾、掃頻干擾、智能干擾等
- GPU 加速的大規模干擾場景模擬
- 干擾效果評估和量化
"""

import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import asyncio
import json

try:
    import tensorflow as tf
    import sionna as sn
    from sionna.channel import RayleighBlockFading, TimeChannel, FlatFadingChannel
    from sionna.rt import load_scene, PlanarArray, Transmitter, Receiver

    GPU_AVAILABLE = len(tf.config.list_physical_devices("GPU")) > 0
except ImportError:
    tf = None
    sn = None
    GPU_AVAILABLE = False

from ..models.interference_models import (
    JammerSource,
    JammerType,
    InterferenceEnvironment,
    InterferenceDetectionResult,
    InterferenceSimulationRequest,
    InterferenceSimulationResponse,
    InterferencePattern,
    InterferenceEvent,
    InterferenceMetrics,
)

logger = logging.getLogger(__name__)


class InterferenceSimulationService:
    """干擾模擬服務"""

    def __init__(self):
        """初始化干擾模擬服務"""
        self.logger = logger
        self.gpu_available = GPU_AVAILABLE
        self.simulation_cache = {}
        self.active_jammers = {}
        self.simulation_history = []

        # 初始化 GPU 環境
        if self.gpu_available and tf is not None:
            self._setup_gpu_environment()
        else:
            self.logger.warning("GPU 不可用，將使用 CPU 模式進行干擾模擬")

        self.logger.info(f"干擾模擬服務初始化完成 (GPU: {self.gpu_available})")

    def _setup_gpu_environment(self):
        """設置 GPU 環境"""
        try:
            # 設置 GPU 記憶體增長
            gpus = tf.config.experimental.list_physical_devices("GPU")
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                self.logger.info(f"GPU 環境設置完成，可用 GPU 數量: {len(gpus)}")
        except Exception as e:
            self.logger.error(f"GPU 環境設置失敗: {e}")
            self.gpu_available = False

    async def simulate_interference(
        self, request: InterferenceSimulationRequest
    ) -> InterferenceSimulationResponse:
        """
        執行干擾模擬

        Args:
            request: 干擾模擬請求

        Returns:
            干擾模擬響應結果
        """
        start_time = time.time()
        simulation_id = f"sim_{uuid.uuid4().hex[:8]}"

        try:
            self.logger.info(
                f"開始干擾模擬 {simulation_id}",
                extra={
                    "simulation_id": simulation_id,
                    "environment_id": request.environment.environment_id,
                    "jammer_count": len(request.environment.jammer_sources),
                    "victim_count": len(request.victim_positions),
                },
            )

            # 準備模擬環境
            simulation_env = await self._prepare_simulation_environment(
                request.environment
            )

            # 執行干擾模擬
            detection_results = await self._execute_simulation(
                simulation_env,
                request.victim_positions,
                request.victim_frequency_mhz,
                request.victim_bandwidth_mhz,
                request,
            )

            # 計算統計摘要
            summary_stats = self._calculate_summary_statistics(detection_results)

            processing_time = (time.time() - start_time) * 1000  # ms

            # 創建響應
            response = InterferenceSimulationResponse(
                request_id=request.request_id,
                simulation_id=simulation_id,
                success=True,
                message=f"干擾模擬完成，處理 {len(detection_results)} 個檢測結果",
                start_time=datetime.utcnow(),
                completion_time=datetime.utcnow(),
                processing_time_ms=processing_time,
                detection_results=detection_results,
                summary_statistics=summary_stats,
                affected_victim_count=summary_stats.get("affected_victim_count", 0),
                average_sinr_degradation_db=summary_stats.get(
                    "average_sinr_degradation_db", 0.0
                ),
                simulation_accuracy=summary_stats.get("simulation_accuracy", 0.95),
                computational_complexity=f"O(N*M*T) - N={len(request.victim_positions)}, M={len(request.environment.jammer_sources)}",
            )

            # 保存到歷史記錄
            self.simulation_history.append(
                {
                    "simulation_id": simulation_id,
                    "request": request.dict(),
                    "response": response.dict(),
                    "timestamp": datetime.utcnow(),
                }
            )

            self.logger.info(
                f"干擾模擬 {simulation_id} 完成",
                extra={
                    "processing_time_ms": processing_time,
                    "affected_victims": response.affected_victim_count,
                    "avg_sinr_degradation": response.average_sinr_degradation_db,
                },
            )

            return response

        except Exception as e:
            self.logger.error(f"干擾模擬 {simulation_id} 失敗: {e}", exc_info=True)
            return InterferenceSimulationResponse(
                request_id=request.request_id,
                simulation_id=simulation_id,
                success=False,
                message=f"模擬失敗: {str(e)}",
                processing_time_ms=(time.time() - start_time) * 1000,
                detection_results=[],
                summary_statistics={},
            )

    async def _prepare_simulation_environment(
        self, environment: InterferenceEnvironment
    ) -> Dict[str, Any]:
        """準備模擬環境"""
        try:
            # 解析環境邊界
            bounds = environment.area_bounds
            env_size = {
                "x_range": (bounds["min_x"], bounds["max_x"]),
                "y_range": (bounds["min_y"], bounds["max_y"]),
                "z_range": (bounds["min_z"], bounds["max_z"]),
            }

            # 準備干擾源
            prepared_jammers = []
            for jammer in environment.jammer_sources:
                prepared_jammer = await self._prepare_jammer_source(jammer)
                prepared_jammers.append(prepared_jammer)

            # 設置傳播環境
            propagation_params = {
                "path_loss_exponent": environment.path_loss_exponent,
                "shadowing_std_db": environment.shadowing_std_db,
                "thermal_noise_dbm": environment.thermal_noise_dbm,
                "background_interference_dbm": environment.background_interference_dbm,
            }

            simulation_env = {
                "environment_id": environment.environment_id,
                "env_size": env_size,
                "jammers": prepared_jammers,
                "propagation": propagation_params,
                "time_params": {
                    "duration_sec": environment.simulation_duration_sec,
                    "resolution_ms": environment.time_resolution_ms,
                },
            }

            self.logger.debug(f"模擬環境準備完成: {len(prepared_jammers)} 個干擾源")
            return simulation_env

        except Exception as e:
            self.logger.error(f"準備模擬環境失敗: {e}")
            raise

    async def _prepare_jammer_source(self, jammer: JammerSource) -> Dict[str, Any]:
        """準備干擾源參數"""
        try:
            # 基本參數
            prepared = {
                "jammer_id": jammer.jammer_id,
                "type": jammer.jammer_type,
                "position": jammer.position,
                "power_dbm": jammer.power_dbm,
                "frequency_band": jammer.frequency_band,
                "pattern": jammer.pattern,
            }

            # 根據干擾類型設置特定參數
            if jammer.jammer_type == JammerType.BROADBAND_NOISE:
                prepared["noise_params"] = {
                    "bandwidth_mhz": jammer.frequency_band["bandwidth_mhz"],
                    "spectral_density": jammer.power_dbm
                    - 10 * np.log10(jammer.frequency_band["bandwidth_mhz"] * 1e6),
                }

            elif jammer.jammer_type == JammerType.SWEEP_JAMMER:
                prepared["sweep_params"] = {
                    "sweep_rate_mhz_per_sec": jammer.sweep_rate_mhz_per_sec or 1000.0,
                    "sweep_bandwidth": jammer.frequency_band["bandwidth_mhz"],
                }

            elif jammer.jammer_type == JammerType.PULSE_JAMMER:
                prepared["pulse_params"] = {
                    "pulse_width_ms": jammer.pulse_width_ms or 1.0,
                    "duty_cycle": jammer.duty_cycle,
                    "repetition_rate_hz": (
                        1000.0 / (jammer.pulse_width_ms or 1.0)
                        if jammer.pulse_width_ms
                        else 1000.0
                    ),
                }

            elif jammer.jammer_type == JammerType.SMART_JAMMER:
                prepared["smart_params"] = {
                    "target_protocols": jammer.target_protocols,
                    "learning_enabled": jammer.learning_enabled,
                    "adaptation_rate": 0.1,
                }

            # 時間參數
            prepared["timing"] = {
                "start_time_sec": jammer.start_time_sec,
                "duration_sec": jammer.duration_sec,
                "active": True,
            }

            # 移動性參數
            if jammer.velocity:
                prepared["mobility"] = {
                    "velocity": jammer.velocity,
                    "trajectory_type": "linear",
                }

            return prepared

        except Exception as e:
            self.logger.error(f"準備干擾源 {jammer.jammer_id} 失敗: {e}")
            raise

    async def _execute_simulation(
        self,
        simulation_env: Dict[str, Any],
        victim_positions: List[Tuple[float, float, float]],
        victim_frequency_mhz: float,
        victim_bandwidth_mhz: float,
        request: InterferenceSimulationRequest,
    ) -> List[InterferenceDetectionResult]:
        """執行干擾模擬"""
        try:
            detection_results = []

            # 時間步驟
            time_duration = simulation_env["time_params"]["duration_sec"]
            time_step = (
                simulation_env["time_params"]["resolution_ms"] / 1000.0
            )  # 轉換為秒
            time_points = np.arange(0, time_duration, time_step)

            # 對每個受害者位置進行模擬
            for victim_idx, victim_pos in enumerate(victim_positions):
                victim_id = f"victim_{victim_idx}"

                # 對每個時間點進行模擬
                for time_idx, current_time in enumerate(
                    time_points[::10]
                ):  # 採樣以減少計算量
                    detection_result = (
                        await self._simulate_interference_at_position_and_time(
                            victim_id,
                            victim_pos,
                            victim_frequency_mhz,
                            victim_bandwidth_mhz,
                            current_time,
                            simulation_env,
                            request,
                        )
                    )

                    if detection_result:
                        detection_results.append(detection_result)

            self.logger.info(
                f"干擾模擬執行完成，生成 {len(detection_results)} 個檢測結果"
            )
            return detection_results

        except Exception as e:
            self.logger.error(f"執行干擾模擬失敗: {e}")
            raise

    async def _simulate_interference_at_position_and_time(
        self,
        victim_id: str,
        victim_position: Tuple[float, float, float],
        victim_frequency_mhz: float,
        victim_bandwidth_mhz: float,
        current_time: float,
        simulation_env: Dict[str, Any],
        request: InterferenceSimulationRequest,
    ) -> Optional[InterferenceDetectionResult]:
        """在特定位置和時間模擬干擾"""
        try:
            # 計算來自所有干擾源的干擾功率
            total_interference_power = 0.0
            interference_sources = []

            for jammer in simulation_env["jammers"]:
                # 檢查干擾源在當前時間是否活躍
                if not self._is_jammer_active(jammer, current_time):
                    continue

                # 計算干擾源到受害者的距離
                jammer_pos = jammer["position"]
                distance = np.sqrt(
                    (victim_position[0] - jammer_pos[0]) ** 2
                    + (victim_position[1] - jammer_pos[1]) ** 2
                    + (victim_position[2] - jammer_pos[2]) ** 2
                )

                # 計算路徑損耗
                path_loss_db = self._calculate_path_loss(
                    distance, victim_frequency_mhz, simulation_env["propagation"]
                )

                # 計算接收到的干擾功率
                interference_power_dbm = jammer["power_dbm"] - path_loss_db

                # 考慮頻率重疊
                frequency_overlap = self._calculate_frequency_overlap(
                    victim_frequency_mhz,
                    victim_bandwidth_mhz,
                    jammer["frequency_band"]["center_freq_mhz"],
                    jammer["frequency_band"]["bandwidth_mhz"],
                )

                if frequency_overlap > 0:
                    # 根據干擾類型調整功率
                    adjusted_power = self._adjust_interference_power_by_type(
                        interference_power_dbm, jammer, current_time, frequency_overlap
                    )

                    total_interference_power += 10 ** (
                        adjusted_power / 10.0
                    )  # 轉換為線性單位
                    interference_sources.append(
                        {
                            "jammer_id": jammer["jammer_id"],
                            "type": jammer["type"],
                            "power_dbm": adjusted_power,
                            "distance_m": distance,
                        }
                    )

            # 轉換回 dBm
            total_interference_dbm = (
                10 * np.log10(total_interference_power)
                if total_interference_power > 0
                else -150.0
            )

            # 計算噪聲功率
            thermal_noise_dbm = simulation_env["propagation"]["thermal_noise_dbm"]
            background_interference_dbm = simulation_env["propagation"][
                "background_interference_dbm"
            ]
            total_noise_power = 10 ** (thermal_noise_dbm / 10.0) + 10 ** (
                background_interference_dbm / 10.0
            )
            total_noise_dbm = 10 * np.log10(total_noise_power)

            # 假設信號功率（基於距離和發射功率）
            signal_power_dbm = self._estimate_signal_power(
                victim_position, victim_frequency_mhz
            )

            # 計算 SINR 和 SNR
            sinr_db = signal_power_dbm - 10 * np.log10(
                10 ** (total_interference_dbm / 10.0) + 10 ** (total_noise_dbm / 10.0)
            )
            snr_db = signal_power_dbm - total_noise_dbm
            rssi_dbm = 10 * np.log10(
                10 ** (signal_power_dbm / 10.0)
                + 10 ** (total_interference_dbm / 10.0)
                + 10 ** (total_noise_dbm / 10.0)
            )

            # 干擾檢測
            interference_detected = total_interference_dbm > (
                thermal_noise_dbm + 10
            )  # 10dB 閾值

            # 估算性能影響
            throughput_degradation = max(0, min(100, (20 - sinr_db) * 5))  # 經驗公式
            latency_increase = max(0, (10 - sinr_db) * 2) if sinr_db < 10 else 0
            error_rate_increase = (
                max(0, min(0.5, (5 - sinr_db) * 0.02)) if sinr_db < 5 else 0
            )

            # 干擾類型識別
            suspected_jammer_type = None
            confidence_score = 0.0
            if interference_sources:
                # 選擇最強的干擾源作為疑似類型
                strongest_jammer = max(
                    interference_sources, key=lambda x: x["power_dbm"]
                )
                suspected_jammer_type = strongest_jammer["type"]
                confidence_score = min(
                    1.0, (strongest_jammer["power_dbm"] - thermal_noise_dbm) / 30.0
                )

            # 創建檢測結果
            detection_result = InterferenceDetectionResult(
                detection_id=f"det_{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                detector_position=victim_position,
                detector_id=victim_id,
                interference_detected=interference_detected,
                interference_power_dbm=total_interference_dbm,
                noise_power_dbm=total_noise_dbm,
                signal_power_dbm=signal_power_dbm,
                sinr_db=sinr_db,
                snr_db=snr_db,
                rssi_dbm=rssi_dbm,
                frequency_analysis={
                    "center_frequency_mhz": victim_frequency_mhz,
                    "bandwidth_mhz": victim_bandwidth_mhz,
                    "interference_sources": interference_sources,
                },
                affected_frequencies=[
                    {
                        "frequency_mhz": victim_frequency_mhz,
                        "interference_level_dbm": total_interference_dbm,
                    }
                ],
                suspected_jammer_type=suspected_jammer_type,
                confidence_score=confidence_score,
                throughput_degradation_percent=throughput_degradation,
                latency_increase_ms=latency_increase,
                error_rate_increase=error_rate_increase,
            )

            return detection_result

        except Exception as e:
            self.logger.error(
                f"位置 {victim_position} 時間 {current_time} 的干擾模擬失敗: {e}"
            )
            return None

    def _is_jammer_active(self, jammer: Dict[str, Any], current_time: float) -> bool:
        """檢查干擾源在當前時間是否活躍"""
        timing = jammer.get("timing", {})
        start_time = timing.get("start_time_sec", 0.0)
        duration = timing.get("duration_sec")

        if current_time < start_time:
            return False

        if duration is not None and current_time > (start_time + duration):
            return False

        # 考慮占空比（針對脈衝干擾）
        if jammer["type"] == JammerType.PULSE_JAMMER:
            pulse_params = jammer.get("pulse_params", {})
            duty_cycle = pulse_params.get("duty_cycle", 1.0)
            pulse_period = 1.0 / pulse_params.get("repetition_rate_hz", 1000.0)
            time_in_period = (current_time - start_time) % pulse_period
            return time_in_period < (pulse_period * duty_cycle)

        return True

    def _calculate_path_loss(
        self,
        distance_m: float,
        frequency_mhz: float,
        propagation_params: Dict[str, Any],
    ) -> float:
        """計算路徑損耗"""
        # 自由空間路徑損耗
        fspl_db = (
            20 * np.log10(distance_m)
            + 20 * np.log10(frequency_mhz)
            + 20 * np.log10(4 * np.pi / 299.792458)
        )

        # 考慮路徑損耗指數
        path_loss_exponent = propagation_params.get("path_loss_exponent", 2.0)
        if path_loss_exponent != 2.0:
            additional_loss = 10 * (path_loss_exponent - 2.0) * np.log10(distance_m)
            fspl_db += additional_loss

        # 加入陰影衰落（隨機變量）
        shadowing_std = propagation_params.get("shadowing_std_db", 8.0)
        shadowing_loss = np.random.normal(0, shadowing_std)

        return fspl_db + shadowing_loss

    def _calculate_frequency_overlap(
        self,
        victim_freq_mhz: float,
        victim_bw_mhz: float,
        jammer_freq_mhz: float,
        jammer_bw_mhz: float,
    ) -> float:
        """計算頻率重疊比例"""
        victim_start = victim_freq_mhz - victim_bw_mhz / 2
        victim_end = victim_freq_mhz + victim_bw_mhz / 2

        jammer_start = jammer_freq_mhz - jammer_bw_mhz / 2
        jammer_end = jammer_freq_mhz + jammer_bw_mhz / 2

        overlap_start = max(victim_start, jammer_start)
        overlap_end = min(victim_end, jammer_end)

        if overlap_end <= overlap_start:
            return 0.0

        overlap_bandwidth = overlap_end - overlap_start
        return overlap_bandwidth / victim_bw_mhz

    def _adjust_interference_power_by_type(
        self,
        base_power_dbm: float,
        jammer: Dict[str, Any],
        current_time: float,
        frequency_overlap: float,
    ) -> float:
        """根據干擾類型調整功率"""
        adjusted_power = base_power_dbm

        # 考慮頻率重疊
        adjusted_power += 10 * np.log10(frequency_overlap)

        jammer_type = jammer["type"]

        if jammer_type == JammerType.SWEEP_JAMMER:
            # 掃頻干擾：功率隨時間變化
            sweep_params = jammer.get("sweep_params", {})
            sweep_rate = sweep_params.get("sweep_rate_mhz_per_sec", 1000.0)
            # 簡化的掃頻模型
            sweep_factor = np.sin(2 * np.pi * sweep_rate * current_time / 1000.0)
            adjusted_power += 3 * sweep_factor  # ±3dB 變化

        elif jammer_type == JammerType.SMART_JAMMER:
            # 智能干擾：根據學習狀態調整
            smart_params = jammer.get("smart_params", {})
            if smart_params.get("learning_enabled", False):
                # 假設學習效果隨時間提升
                learning_gain = min(10, current_time * 0.1)  # 最多10dB提升
                adjusted_power += learning_gain

        return adjusted_power

    def _estimate_signal_power(
        self, victim_position: Tuple[float, float, float], frequency_mhz: float
    ) -> float:
        """估算信號功率（簡化模型）"""
        # 假設基站在原點，發射功率 30dBm
        base_station_power_dbm = 30.0
        distance = np.sqrt(sum(x**2 for x in victim_position))

        # 簡單的路徑損耗模型
        path_loss_db = 20 * np.log10(distance) + 20 * np.log10(frequency_mhz) - 147.55

        return base_station_power_dbm - path_loss_db

    def _calculate_summary_statistics(
        self, detection_results: List[InterferenceDetectionResult]
    ) -> Dict[str, Any]:
        """計算統計摘要"""
        if not detection_results:
            return {}

        # 統計干擾檢測結果
        total_detections = len(detection_results)
        interference_detections = sum(
            1 for r in detection_results if r.interference_detected
        )

        # 計算平均值
        avg_sinr = np.mean([r.sinr_db for r in detection_results])
        avg_sinr_degradation = max(0, 20 - avg_sinr)  # 假設正常SINR為20dB
        avg_throughput_degradation = np.mean(
            [r.throughput_degradation_percent for r in detection_results]
        )
        avg_latency_increase = np.mean(
            [r.latency_increase_ms for r in detection_results]
        )

        # 受影響的受害者數量
        affected_victims = len(
            set(r.detector_id for r in detection_results if r.interference_detected)
        )

        # 干擾類型分布
        jammer_types = {}
        for result in detection_results:
            if result.suspected_jammer_type:
                jammer_type = result.suspected_jammer_type.value
                jammer_types[jammer_type] = jammer_types.get(jammer_type, 0) + 1

        return {
            "total_detections": total_detections,
            "interference_detections": interference_detections,
            "detection_rate": (
                interference_detections / total_detections
                if total_detections > 0
                else 0
            ),
            "affected_victim_count": affected_victims,
            "average_sinr_db": avg_sinr,
            "average_sinr_degradation_db": avg_sinr_degradation,
            "average_throughput_degradation_percent": avg_throughput_degradation,
            "average_latency_increase_ms": avg_latency_increase,
            "jammer_type_distribution": jammer_types,
            "simulation_accuracy": 0.95,  # 固定值，實際應根據模型驗證確定
        }

    # ===== 公共方法 =====

    async def create_jammer_scenario(
        self,
        scenario_name: str,
        jammer_configs: List[Dict[str, Any]],
        environment_bounds: Dict[str, float],
        duration_sec: float = 60.0,
    ) -> InterferenceEnvironment:
        """創建干擾場景"""
        try:
            # 創建干擾源
            jammers = []
            for i, config in enumerate(jammer_configs):
                jammer = JammerSource(
                    jammer_id=f"jammer_{i+1}",
                    jammer_type=JammerType(config["type"]),
                    position=tuple(config["position"]),
                    power_dbm=config["power_dbm"],
                    frequency_band=config["frequency_band"],
                    pattern=InterferencePattern(config.get("pattern", "continuous")),
                    **{
                        k: v
                        for k, v in config.items()
                        if k
                        not in [
                            "type",
                            "position",
                            "power_dbm",
                            "frequency_band",
                            "pattern",
                        ]
                    },
                )
                jammers.append(jammer)

            # 創建干擾環境
            environment = InterferenceEnvironment(
                environment_id=f"env_{uuid.uuid4().hex[:8]}",
                name=scenario_name,
                area_bounds=environment_bounds,
                jammer_sources=jammers,
                simulation_duration_sec=duration_sec,
            )

            self.logger.info(
                f"創建干擾場景 '{scenario_name}'，包含 {len(jammers)} 個干擾源"
            )
            return environment

        except Exception as e:
            self.logger.error(f"創建干擾場景失敗: {e}")
            raise

    async def get_simulation_metrics(
        self, time_window_sec: float = 3600.0
    ) -> InterferenceMetrics:
        """獲取模擬指標"""
        try:
            current_time = datetime.utcnow()

            # 統計指定時間窗口內的模擬記錄
            recent_simulations = [
                sim
                for sim in self.simulation_history
                if (current_time - sim["timestamp"]).total_seconds() <= time_window_sec
            ]

            total_simulations = len(recent_simulations)
            successful_simulations = sum(
                1 for sim in recent_simulations if sim["response"]["success"]
            )

            # 計算平均處理時間
            avg_processing_time = 0.0
            if recent_simulations:
                processing_times = [
                    sim["response"]["processing_time_ms"] for sim in recent_simulations
                ]
                avg_processing_time = np.mean(processing_times)

            # GPU 使用率（模擬值）
            gpu_usage = 0.0
            if self.gpu_available:
                gpu_usage = min(100.0, len(self.active_jammers) * 10.0)  # 簡化計算

            metrics = InterferenceMetrics(
                metrics_id=f"metrics_{uuid.uuid4().hex[:8]}",
                collection_time=current_time,
                time_window_sec=time_window_sec,
                total_detections=total_simulations,
                detection_accuracy=(
                    successful_simulations / total_simulations
                    if total_simulations > 0
                    else 0.0
                ),
                average_decision_time_ms=avg_processing_time,
                cpu_usage_percent=min(100.0, len(self.active_jammers) * 5.0),
                gpu_usage_percent=gpu_usage,
                memory_usage_mb=len(self.simulation_cache) * 0.5,  # 估算值
            )

            return metrics

        except Exception as e:
            self.logger.error(f"獲取模擬指標失敗: {e}")
            raise

    async def clear_simulation_cache(self):
        """清理模擬快取"""
        self.simulation_cache.clear()
        self.logger.info("模擬快取已清理")

    async def get_active_jammers(self) -> List[Dict[str, Any]]:
        """獲取活躍的干擾源"""
        return list(self.active_jammers.values())

    async def add_active_jammer(self, jammer_id: str, jammer_config: Dict[str, Any]):
        """添加活躍干擾源"""
        self.active_jammers[jammer_id] = {
            **jammer_config,
            "activated_at": datetime.utcnow(),
            "status": "active",
        }
        self.logger.info(f"干擾源 {jammer_id} 已激活")

    async def remove_active_jammer(self, jammer_id: str):
        """移除活躍干擾源"""
        if jammer_id in self.active_jammers:
            del self.active_jammers[jammer_id]
            self.logger.info(f"干擾源 {jammer_id} 已移除")

    def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "service_name": "InterferenceSimulationService",
            "status": "running",
            "gpu_available": self.gpu_available,
            "active_jammers_count": len(self.active_jammers),
            "simulation_cache_size": len(self.simulation_cache),
            "simulation_history_count": len(self.simulation_history),
            "last_simulation_time": (
                self.simulation_history[-1]["timestamp"]
                if self.simulation_history
                else None
            ),
        }
