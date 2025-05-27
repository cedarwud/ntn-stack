"""
Sionna 通道參數到 UERANSIM RAN 參數轉換服務

實現 ChannelServiceInterface，提供完整的通道模擬與 RAN 配置整合功能。
"""

import asyncio
import logging
import uuid
import math
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.wireless.interfaces.channel_service_interface import (
    ChannelServiceInterface,
)
from app.domains.wireless.models.channel_model import (
    ChannelParameters,
    ChannelResponse,
    RANParameters,
    ChannelToRANMappingRequest,
    ChannelToRANMappingResponse,
    UERANSIMConfiguration,
    ChannelQualityMetrics,
    ChannelType,
)

logger = logging.getLogger(__name__)


class ChannelToRANService(ChannelServiceInterface):
    """Sionna 通道參數到 UERANSIM RAN 參數轉換服務實現"""

    def __init__(self):
        """初始化服務"""
        self.logger = logging.getLogger(__name__)

        # 轉換參數配置
        self.frequency_to_arfcn_map = {
            # n77 band (3.3-4.2 GHz)
            3.5e9: 632628,  # 3.5 GHz
            3.7e9: 636667,  # 3.7 GHz
            # n78 band (3.3-3.8 GHz)
            3.6e9: 634000,  # 3.6 GHz
            # n79 band (4.4-5.0 GHz)
            4.7e9: 739286,  # 4.7 GHz
        }

        # 路徑損耗模型映射
        self.path_loss_models = {
            ChannelType.LOS: "freespace",
            ChannelType.NLOS: "cost231",
            ChannelType.URBAN: "uma_los",
            ChannelType.RURAL: "rma_los",
            ChannelType.SATELLITE: "satellite",
            ChannelType.UAV: "a2a_los",
        }

    async def extract_channel_parameters_from_sionna(
        self,
        session: AsyncSession,
        scene_name: str,
        tx_device_id: int,
        rx_device_id: int,
        frequency_hz: float,
    ) -> ChannelParameters:
        """從 Sionna 模擬結果中提取通道參數"""

        self.logger.info(
            f"從 Sionna 提取通道參數: scene={scene_name}, "
            f"tx={tx_device_id}, rx={rx_device_id}, freq={frequency_hz}"
        )

        try:
            # 調用現有的 Sionna 服務獲取模擬結果
            from app.domains.simulation.services.sionna_service import sionna_service

            # 執行 Sionna 模擬獲取通道特性
            simulation_params = {
                "scene_name": scene_name,
                "tx_device_id": tx_device_id,
                "rx_device_id": rx_device_id,
                "frequency_hz": frequency_hz,
            }

            # 模擬 Sionna 結果（實際應該調用真正的 Sionna 計算）
            # 這裡先用模擬數據，後續可以整合真實的 Sionna 計算
            channel_params = await self._simulate_sionna_channel_extraction(
                scene_name, tx_device_id, rx_device_id, frequency_hz
            )

            self.logger.info(f"成功提取通道參數: {channel_params.channel_id}")
            return channel_params

        except Exception as e:
            self.logger.error(f"提取 Sionna 通道參數失敗: {e}")
            raise RuntimeError(f"提取 Sionna 通道參數失敗: {e}")

    async def convert_channel_to_ran_parameters(
        self,
        request: ChannelToRANMappingRequest,
    ) -> ChannelToRANMappingResponse:
        """將 Sionna 通道參數轉換為 UERANSIM RAN 參數"""

        start_time = time.time()
        self.logger.info(f"開始轉換通道參數到 RAN 參數: {request.request_id}")

        try:
            channel = request.channel_parameters
            warnings = []
            recommendations = []
            mapping_details = {}

            # 1. 基本配置
            ran_config_id = f"ran_config_{uuid.uuid4().hex[:8]}"

            # 2. 計算發射功率
            # 根據路徑損耗和目標覆蓋範圍計算所需功率
            tx_power_dbm = self._calculate_tx_power(
                channel.path_loss_db, channel.channel_type, mapping_details
            )

            if tx_power_dbm > 46:  # 5G gNB 最大功率限制
                warnings.append(
                    f"計算功率 {tx_power_dbm:.1f} dBm 超過法規限制，已調整至 46 dBm"
                )
                tx_power_dbm = 46

            # 3. 頻率映射
            dl_arfcn, ul_arfcn, band = self._map_frequency_to_arfcn(
                channel.frequency_hz, mapping_details
            )

            # 4. 覆蓋範圍計算
            cell_range_km = self._calculate_cell_range(
                tx_power_dbm,
                channel.path_loss_db,
                channel.channel_type,
                mapping_details,
            )

            # 5. 信號品質參數
            ref_signal_power = tx_power_dbm - 3  # RS 功率通常比總功率低 3dB
            sinr_threshold = self._calculate_sinr_threshold(
                channel.sinr_db, mapping_details
            )

            # 6. 多普勒和 NTN 參數
            elevation_angle = self._extract_elevation_angle(channel)
            doppler_compensation = (
                abs(channel.doppler_shift_hz or 0) > 100
            )  # >100Hz 需要補償

            # 7. 位置轉換 (ECEF -> LLA)
            gnb_position = self._convert_position_to_lla(channel.tx_position)

            # 8. 建立 RAN 參數
            ran_parameters = RANParameters(
                ran_config_id=ran_config_id,
                gnb_id=request.target_gnb_id,
                cell_id=request.target_cell_id,
                tx_power_dbm=tx_power_dbm,
                antenna_gain_dbi=self._get_antenna_gain(channel.channel_type),
                noise_figure_db=7.0,  # 標準 5G 值
                dl_arfcn=dl_arfcn,
                ul_arfcn=ul_arfcn,
                band=band,
                cell_range_km=cell_range_km,
                reference_signal_power_dbm=ref_signal_power,
                sinr_threshold_db=sinr_threshold,
                path_loss_model=self.path_loss_models.get(
                    channel.channel_type, "freespace"
                ),
                fading_model=self._get_fading_model(channel),
                elevation_angle_deg=elevation_angle,
                doppler_compensation=doppler_compensation,
                beam_steering=channel.channel_type
                in [ChannelType.SATELLITE, ChannelType.UAV],
                gnb_position=gnb_position,
            )

            # 9. 品質評估
            quality_score, confidence = self._assess_mapping_quality(
                channel, ran_parameters, mapping_details
            )

            # 10. 生成建議
            if channel.channel_type == ChannelType.SATELLITE:
                recommendations.append("建議啟用 NTN 特殊處理模式")
            if channel.doppler_shift_hz and abs(channel.doppler_shift_hz) > 500:
                recommendations.append("大多普勒偏移，建議增強頻率同步算法")

            processing_time = (time.time() - start_time) * 1000

            response = ChannelToRANMappingResponse(
                response_id=f"resp_{uuid.uuid4().hex[:8]}",
                request_id=request.request_id,
                success=True,
                ran_parameters=ran_parameters,
                mapping_details=mapping_details,
                mapping_quality_score=quality_score,
                confidence_level=confidence,
                warnings=warnings,
                recommendations=recommendations,
                processing_time_ms=processing_time,
            )

            self.logger.info(
                f"轉換完成: {request.request_id}, 品質評分: {quality_score:.3f}, "
                f"處理時間: {processing_time:.1f}ms"
            )
            return response

        except Exception as e:
            self.logger.error(f"轉換通道參數失敗: {e}")
            processing_time = (time.time() - start_time) * 1000

            return ChannelToRANMappingResponse(
                response_id=f"resp_{uuid.uuid4().hex[:8]}",
                request_id=request.request_id,
                success=False,
                warnings=[f"轉換失敗: {str(e)}"],
                processing_time_ms=processing_time,
            )

    async def generate_ueransim_configuration(
        self,
        ran_parameters: RANParameters,
        ue_count: int = 1,
        deployment_mode: str = "container",
    ) -> UERANSIMConfiguration:
        """根據 RAN 參數生成 UERANSIM 配置"""

        self.logger.info(
            f"生成 UERANSIM 配置: gNB={ran_parameters.gnb_id}, UE數量={ue_count}"
        )

        try:
            config_id = f"ueransim_config_{uuid.uuid4().hex[:8]}"
            config_name = (
                f"5G_NR_gNB_{ran_parameters.gnb_id}_Cell_{ran_parameters.cell_id}"
            )

            # 生成 UE 配置列表
            ue_configs = []
            for i in range(ue_count):
                ue_config = {
                    "ue_id": i + 1,
                    "imsi": f"00101000000000{i+1:02d}",
                    "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
                    "plmn": {"mcc": "001", "mnc": "01"},
                    "gnb_search_list": [f"127.0.0.1:{19300 + ran_parameters.gnb_id}"],
                    "sessions": [
                        {"type": "IPv4", "apn": "internet", "slice": {"sst": 1}}
                    ],
                }
                ue_configs.append(ue_config)

            # 生成容器名稱
            container_name = None
            if deployment_mode == "container":
                container_name = f"ueransim-gnb-{ran_parameters.gnb_id}"

            configuration = UERANSIMConfiguration(
                config_id=config_id,
                config_name=config_name,
                gnb_config=ran_parameters,
                ue_configs=ue_configs,
                deployment_mode=deployment_mode,
                container_name=container_name,
            )

            self.logger.info(f"UERANSIM 配置生成完成: {config_id}")
            return configuration

        except Exception as e:
            self.logger.error(f"生成 UERANSIM 配置失敗: {e}")
            raise RuntimeError(f"生成 UERANSIM 配置失敗: {e}")

    async def deploy_ueransim_configuration(
        self,
        configuration: UERANSIMConfiguration,
    ) -> Dict[str, Any]:
        """部署 UERANSIM 配置到容器或獨立實例"""

        self.logger.info(f"部署 UERANSIM 配置: {configuration.config_id}")

        try:
            if configuration.deployment_mode == "container":
                return await self._deploy_container_mode(configuration)
            else:
                return await self._deploy_standalone_mode(configuration)

        except Exception as e:
            self.logger.error(f"部署 UERANSIM 配置失敗: {e}")
            raise RuntimeError(f"部署 UERANSIM 配置失敗: {e}")

    async def monitor_channel_quality(
        self,
        channel_id: str,
        measurement_duration_s: float = 10.0,
    ) -> ChannelQualityMetrics:
        """監控通道品質指標"""

        self.logger.info(
            f"開始監控通道品質: {channel_id}, 持續時間: {measurement_duration_s}s"
        )

        try:
            # 模擬監控過程
            await asyncio.sleep(
                min(measurement_duration_s, 1.0)
            )  # 實際應該進行真實監控

            # 模擬測量結果
            metrics = ChannelQualityMetrics(
                metrics_id=f"metrics_{uuid.uuid4().hex[:8]}",
                channel_id=channel_id,
                rsrp_dbm=-85.0 + (hash(channel_id) % 20) - 10,  # -95 to -75 dBm
                rsrq_db=-10.0 + (hash(channel_id) % 10),  # -10 to 0 dB
                sinr_db=5.0 + (hash(channel_id) % 20),  # 5 to 25 dB
                theoretical_throughput_mbps=100.0 + (hash(channel_id) % 500),
                actual_throughput_mbps=80.0 + (hash(channel_id) % 400),
                spectral_efficiency_bps_hz=3.0 + (hash(channel_id) % 3),
                measurement_duration_s=measurement_duration_s,
            )

            self.logger.info(
                f"通道品質監控完成: SINR={metrics.sinr_db:.1f}dB, RSRP={metrics.rsrp_dbm:.1f}dBm"
            )
            return metrics

        except Exception as e:
            self.logger.error(f"監控通道品質失敗: {e}")
            raise RuntimeError(f"監控通道品質失敗: {e}")

    async def update_ran_parameters_realtime(
        self,
        gnb_id: int,
        channel_parameters: ChannelParameters,
    ) -> bool:
        """即時更新 RAN 參數以反映通道變化"""

        self.logger.info(f"即時更新 RAN 參數: gNB={gnb_id}")

        try:
            # 模擬即時更新
            await asyncio.sleep(0.1)  # 實際應該調用 UERANSIM API

            self.logger.info(f"RAN 參數更新成功: gNB={gnb_id}")
            return True

        except Exception as e:
            self.logger.error(f"更新 RAN 參數失敗: {e}")
            return False

    async def calculate_interference_impact(
        self,
        target_channel: ChannelParameters,
        interfering_channels: List[ChannelParameters],
    ) -> Dict[str, float]:
        """計算干擾對目標通道的影響"""

        self.logger.info(
            f"計算干擾影響: 目標通道={target_channel.channel_id}, 干擾源數量={len(interfering_channels)}"
        )

        try:
            total_interference_power = 0.0
            frequency_separation_penalty = 0.0
            spatial_isolation_benefit = 0.0

            for interferer in interfering_channels:
                # 計算干擾功率
                distance = self._calculate_distance(
                    target_channel.rx_position, interferer.tx_position
                )
                interference_power = self._calculate_interference_power(
                    interferer, distance
                )
                total_interference_power += interference_power

                # 頻率分離效果
                freq_sep = abs(target_channel.frequency_hz - interferer.frequency_hz)
                if freq_sep > 0:
                    frequency_separation_penalty += 10 * math.log10(1 + freq_sep / 1e6)

            # 計算 SIR (Signal-to-Interference Ratio)
            signal_power = (
                10 ** (target_channel.sinr_db / 10) if target_channel.sinr_db else 1.0
            )
            sir_db = 10 * math.log10(
                signal_power / max(total_interference_power, 1e-12)
            )

            # 計算影響評估
            impact = {
                "sir_degradation_db": (
                    max(0, target_channel.sinr_db - sir_db)
                    if target_channel.sinr_db
                    else 0
                ),
                "total_interference_power_dbm": (
                    10 * math.log10(total_interference_power)
                    if total_interference_power > 0
                    else -100
                ),
                "frequency_separation_benefit_db": frequency_separation_penalty,
                "spatial_isolation_benefit_db": spatial_isolation_benefit,
                "interference_source_count": len(interfering_channels),
                "estimated_capacity_loss_percent": (
                    min(50, max(0, (target_channel.sinr_db - sir_db) * 5))
                    if target_channel.sinr_db
                    else 0
                ),
            }

            self.logger.info(
                f"干擾影響計算完成: SIR劣化={impact['sir_degradation_db']:.1f}dB"
            )
            return impact

        except Exception as e:
            self.logger.error(f"計算干擾影響失敗: {e}")
            raise RuntimeError(f"計算干擾影響失敗: {e}")

    async def optimize_ran_configuration(
        self,
        current_ran: RANParameters,
        target_metrics: Dict[str, float],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> RANParameters:
        """根據目標指標優化 RAN 配置"""

        self.logger.info(f"優化 RAN 配置: gNB={current_ran.gnb_id}")

        try:
            # 複製當前配置作為基礎
            optimized_ran = current_ran.copy(deep=True)
            optimized_ran.ran_config_id = f"optimized_{uuid.uuid4().hex[:8]}"

            # 根據目標指標調整參數
            if "target_sinr_db" in target_metrics:
                target_sinr = target_metrics["target_sinr_db"]
                if target_sinr > current_ran.sinr_threshold_db:
                    # 需要提高 SINR，增加功率或改善天線
                    power_adjustment = min(
                        3.0, target_sinr - current_ran.sinr_threshold_db
                    )
                    optimized_ran.tx_power_dbm = min(
                        46, current_ran.tx_power_dbm + power_adjustment
                    )
                    optimized_ran.sinr_threshold_db = target_sinr

            if "target_coverage_km" in target_metrics:
                target_coverage = target_metrics["target_coverage_km"]
                if target_coverage != current_ran.cell_range_km:
                    optimized_ran.cell_range_km = target_coverage
                    # 根據覆蓋範圍調整功率
                    range_ratio = target_coverage / current_ran.cell_range_km
                    power_adjustment = 20 * math.log10(range_ratio)  # 自由空間路徑損耗
                    optimized_ran.tx_power_dbm = min(
                        46, max(10, current_ran.tx_power_dbm + power_adjustment)
                    )

            # 應用約束條件
            if constraints:
                if "max_power_dbm" in constraints:
                    optimized_ran.tx_power_dbm = min(
                        constraints["max_power_dbm"], optimized_ran.tx_power_dbm
                    )
                if "min_sinr_db" in constraints:
                    optimized_ran.sinr_threshold_db = max(
                        constraints["min_sinr_db"], optimized_ran.sinr_threshold_db
                    )

            optimized_ran.config_timestamp = datetime.utcnow()

            self.logger.info(
                f"RAN 配置優化完成: 功率={optimized_ran.tx_power_dbm:.1f}dBm, 覆蓋={optimized_ran.cell_range_km:.1f}km"
            )
            return optimized_ran

        except Exception as e:
            self.logger.error(f"優化 RAN 配置失敗: {e}")
            raise RuntimeError(f"優化 RAN 配置失敗: {e}")

    # 私有輔助方法

    async def _simulate_sionna_channel_extraction(
        self, scene_name: str, tx_device_id: int, rx_device_id: int, frequency_hz: float
    ) -> ChannelParameters:
        """模擬 Sionna 通道參數提取（後續整合真實 Sionna）"""

        # 生成模擬的通道參數
        channel_id = f"channel_{scene_name}_{tx_device_id}_{rx_device_id}_{int(frequency_hz/1e6)}"

        # 根據頻率和場景生成合理的參數
        base_path_loss = (
            32.45 + 20 * math.log10(frequency_hz / 1e6) + 20 * math.log10(1.0)
        )  # 1km 距離

        if "satellite" in scene_name.lower():
            channel_type = ChannelType.SATELLITE
            path_loss_db = base_path_loss + 190  # 衛星鏈路損耗
            doppler_shift_hz = 1500.0  # 典型衛星多普勒
        elif "urban" in scene_name.lower():
            channel_type = ChannelType.URBAN
            path_loss_db = base_path_loss + 30
            doppler_shift_hz = 50.0
        else:
            channel_type = ChannelType.LOS
            path_loss_db = base_path_loss
            doppler_shift_hz = 10.0

        return ChannelParameters(
            channel_id=channel_id,
            channel_type=channel_type,
            frequency_hz=frequency_hz,
            path_loss_db=path_loss_db,
            shadow_fading_db=3.0,
            delay_spread_s=1e-6,
            azimuth_spread_deg=30.0,
            elevation_spread_deg=15.0,
            doppler_shift_hz=doppler_shift_hz,
            doppler_spread_hz=10.0,
            sinr_db=15.0,
            snr_db=20.0,
            tx_position=(tx_device_id * 100.0, 0.0, 10.0),
            rx_position=(rx_device_id * 100.0, 0.0, 1.5),
        )

    def _calculate_tx_power(
        self, path_loss_db: float, channel_type: ChannelType, details: Dict
    ) -> float:
        """計算所需發射功率"""
        # 基本功率預算計算
        target_rsrp_dbm = -85.0  # 目標 RSRP
        noise_floor_dbm = -104.0  # 熱噪聲底
        required_sinr_db = 10.0  # 所需 SINR

        tx_power_dbm = target_rsrp_dbm + path_loss_db

        # 根據通道類型調整
        if channel_type == ChannelType.SATELLITE:
            tx_power_dbm += 10  # 衛星需要更高功率
        elif channel_type == ChannelType.NLOS:
            tx_power_dbm += 5  # NLOS 需要額外功率

        details["power_budget"] = {
            "target_rsrp_dbm": target_rsrp_dbm,
            "path_loss_db": path_loss_db,
            "calculated_tx_power_dbm": tx_power_dbm,
            "channel_type_adjustment": tx_power_dbm - (target_rsrp_dbm + path_loss_db),
        }

        return max(10.0, min(46.0, tx_power_dbm))  # 限制在合理範圍

    def _map_frequency_to_arfcn(self, frequency_hz: float, details: Dict) -> tuple:
        """將頻率映射到 ARFCN 和頻段"""

        # 找到最接近的 ARFCN
        closest_freq = min(
            self.frequency_to_arfcn_map.keys(), key=lambda x: abs(x - frequency_hz)
        )
        dl_arfcn = self.frequency_to_arfcn_map[closest_freq]

        # UL ARFCN 通常是 DL ARFCN - offset
        ul_arfcn = dl_arfcn - 120000  # 簡化的偏移

        # 根據頻率確定頻段
        if 3.3e9 <= frequency_hz <= 4.2e9:
            band = 77  # n77
        elif 3.3e9 <= frequency_hz <= 3.8e9:
            band = 78  # n78
        elif 4.4e9 <= frequency_hz <= 5.0e9:
            band = 79  # n79
        else:
            band = 77  # 默認

        details["frequency_mapping"] = {
            "input_frequency_ghz": frequency_hz / 1e9,
            "closest_frequency_ghz": closest_freq / 1e9,
            "dl_arfcn": dl_arfcn,
            "ul_arfcn": ul_arfcn,
            "band": band,
        }

        return dl_arfcn, ul_arfcn, band

    def _calculate_cell_range(
        self,
        tx_power_dbm: float,
        path_loss_db: float,
        channel_type: ChannelType,
        details: Dict,
    ) -> float:
        """計算小區覆蓋範圍"""

        # 基於 Friis 傳輸方程式反推距離
        # path_loss_db = 32.45 + 20*log10(d_km) + 20*log10(f_MHz)
        # 假設 3.5 GHz 頻率
        frequency_mhz = 3500

        # 重新整理得到距離
        range_factor = (path_loss_db - 32.45 - 20 * math.log10(frequency_mhz)) / 20
        range_km = 10**range_factor

        # 根據通道類型調整
        if channel_type == ChannelType.SATELLITE:
            range_km = min(range_km, 2000)  # 衛星最大覆蓋
        elif channel_type == ChannelType.URBAN:
            range_km = min(range_km, 5)  # 都市小區限制
        else:
            range_km = min(range_km, 20)  # 一般限制

        details["coverage_calculation"] = {
            "path_loss_db": path_loss_db,
            "frequency_mhz": frequency_mhz,
            "calculated_range_km": range_km,
            "channel_type": channel_type.value,
        }

        return max(0.1, range_km)

    def _calculate_sinr_threshold(
        self, measured_sinr_db: Optional[float], details: Dict
    ) -> float:
        """計算 SINR 門檻值"""
        if measured_sinr_db is not None:
            # 設定門檻值略低於測量值，保留餘量
            threshold = measured_sinr_db - 3.0
        else:
            # 使用標準 5G 門檻值
            threshold = -6.0

        details["sinr_threshold"] = {
            "measured_sinr_db": measured_sinr_db,
            "calculated_threshold_db": threshold,
            "margin_db": (measured_sinr_db - threshold) if measured_sinr_db else None,
        }

        return max(-10.0, min(30.0, threshold))

    def _extract_elevation_angle(self, channel: ChannelParameters) -> Optional[float]:
        """從通道參數中提取仰角"""
        if channel.channel_type in [ChannelType.SATELLITE, ChannelType.UAV]:
            # 根據 tx/rx 位置計算仰角
            dx = channel.tx_position[0] - channel.rx_position[0]
            dy = channel.tx_position[1] - channel.rx_position[1]
            dz = channel.tx_position[2] - channel.rx_position[2]

            horizontal_distance = math.sqrt(dx**2 + dy**2)
            if horizontal_distance > 0:
                elevation_rad = math.atan2(dz, horizontal_distance)
                return math.degrees(elevation_rad)
        return None

    def _get_antenna_gain(self, channel_type: ChannelType) -> float:
        """根據通道類型獲取天線增益"""
        antenna_gains = {
            ChannelType.SATELLITE: 20.0,  # 高增益天線
            ChannelType.UAV: 10.0,  # 中增益天線
            ChannelType.URBAN: 15.0,  # 都市基站天線
            ChannelType.RURAL: 18.0,  # 郊區基站天線
            ChannelType.LOS: 12.0,  # 標準天線
            ChannelType.NLOS: 12.0,  # 標準天線
        }
        return antenna_gains.get(channel_type, 12.0)

    def _get_fading_model(self, channel: ChannelParameters) -> str:
        """根據通道參數選擇衰落模型"""
        if channel.delay_spread_s and channel.delay_spread_s > 1e-6:
            return "rayleigh"
        elif channel.channel_type == ChannelType.LOS:
            return "rician"
        else:
            return "rayleigh"

    def _convert_position_to_lla(self, position: tuple) -> tuple:
        """將 ECEF 座標轉換為 LLA (lat, lon, alt)"""
        # 簡化轉換，實際應該使用精確的座標轉換算法
        x, y, z = position

        # 假設位置已經是相對地表的座標，進行簡單轉換
        # 實際應該使用 pyproj 或類似庫
        lat = z / 111000  # 粗略轉換：1度 ≈ 111km
        lon = x / (111000 * math.cos(math.radians(lat)))
        alt = y

        return (lat, lon, alt)

    def _assess_mapping_quality(
        self, channel: ChannelParameters, ran: RANParameters, details: Dict
    ) -> tuple:
        """評估映射品質"""
        quality_factors = []

        # 頻率匹配品質
        if channel.frequency_hz:
            freq_diff = abs(channel.frequency_hz - 3.5e9)  # 與標準頻率比較
            freq_quality = max(0, 1 - freq_diff / 1e9)
            quality_factors.append(freq_quality)

        # 功率適配品質
        if channel.path_loss_db:
            power_margin = 46 - ran.tx_power_dbm  # 與最大功率的差距
            power_quality = min(1.0, power_margin / 10)
            quality_factors.append(power_quality)

        # 覆蓋範圍合理性
        if ran.cell_range_km > 0:
            range_quality = 1.0 if ran.cell_range_km < 50 else 0.5
            quality_factors.append(range_quality)

        # 計算總體品質評分
        quality_score = (
            sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
        )

        # 置信水準基於可用參數的完整性
        available_params = sum(
            [
                1 if channel.path_loss_db else 0,
                1 if channel.sinr_db else 0,
                1 if channel.doppler_shift_hz is not None else 0,
                1 if channel.frequency_hz else 0,
            ]
        )
        confidence = min(1.0, available_params / 4.0)

        details["quality_assessment"] = {
            "quality_factors": quality_factors,
            "available_parameters": available_params,
            "total_parameters": 4,
        }

        return quality_score, confidence

    async def _deploy_container_mode(
        self, config: UERANSIMConfiguration
    ) -> Dict[str, Any]:
        """部署容器模式的 UERANSIM"""
        # 模擬容器部署
        await asyncio.sleep(1.0)  # 模擬部署時間

        return {
            "deployment_status": "success",
            "container_id": f"ueransim_{config.config_id}",
            "container_name": config.container_name,
            "gnb_endpoint": f"127.0.0.1:{19300 + config.gnb_config.gnb_id}",
            "management_port": 9090 + config.gnb_config.gnb_id,
            "deployment_time": time.time(),
        }

    async def _deploy_standalone_mode(
        self, config: UERANSIMConfiguration
    ) -> Dict[str, Any]:
        """部署獨立模式的 UERANSIM"""
        # 模擬獨立部署
        await asyncio.sleep(2.0)  # 模擬部署時間

        return {
            "deployment_status": "success",
            "process_id": f"ueransim_proc_{config.config_id}",
            "config_files": [
                f"/tmp/gnb_{config.gnb_config.gnb_id}.yaml",
                f"/tmp/ue_configs_{config.config_id}.yaml",
            ],
            "gnb_endpoint": f"127.0.0.1:{19300 + config.gnb_config.gnb_id}",
            "deployment_time": time.time(),
        }

    def _calculate_distance(self, pos1: tuple, pos2: tuple) -> float:
        """計算兩點間距離"""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        dz = pos1[2] - pos2[2]
        return math.sqrt(dx**2 + dy**2 + dz**2)

    def _calculate_interference_power(
        self, interferer: ChannelParameters, distance: float
    ) -> float:
        """計算干擾功率"""
        if distance == 0:
            return 1e-6  # 避免除零

        # 簡化的干擾功率計算
        path_loss_db = (
            32.45
            + 20 * math.log10(distance / 1000)
            + 20 * math.log10(interferer.frequency_hz / 1e6)
        )
        interference_power_linear = 10 ** (-path_loss_db / 10)

        return max(1e-12, interference_power_linear)


# 全局服務實例
channel_to_ran_service = ChannelToRANService()
