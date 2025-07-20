"""
物理傳播模型

實現LEO衛星通信的電波傳播物理模型，包括：
- 自由空間路徑損耗 (Free Space Path Loss)
- 大氣衰減 (Atmospheric Attenuation)
- 降雨衰減 (Rain Attenuation - ITU-R P.618)
- 多普勒頻移 (Doppler Shift)
- 仰角相關衰減
"""

import math
import numpy as np
from typing import Tuple, Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class PhysicalPropagationModel:
    """物理傳播模型類"""

    def __init__(self):
        """初始化物理常數"""
        self.c = 299792458.0  # 光速 (m/s)
        self.earth_radius = 6371.0  # 地球半徑 (km)

    def calculate_free_space_path_loss(
        self, distance_km: float, frequency_ghz: float
    ) -> float:
        """
        計算自由空間路徑損耗 (dB)

        Args:
            distance_km: 距離 (公里)
            frequency_ghz: 頻率 (GHz)

        Returns:
            路徑損耗 (dB)
        """
        if distance_km <= 0 or frequency_ghz <= 0:
            return 0.0

        # FSPL = 20*log10(d) + 20*log10(f) + 92.45
        # d in km, f in GHz
        fspl = 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz) + 92.45
        return fspl

    def calculate_atmospheric_attenuation(
        self, elevation_angle: float, frequency_ghz: float
    ) -> float:
        """
        計算大氣衰減 (dB)

        Args:
            elevation_angle: 仰角 (度)
            frequency_ghz: 頻率 (GHz)

        Returns:
            大氣衰減 (dB)
        """
        if elevation_angle <= 0:
            return 50.0  # 極低仰角時的高衰減

        # 基於 ITU-R P.676 的簡化模型
        # 氧氣和水蒸氣吸收
        oxygen_attenuation = 0.0067 * frequency_ghz  # dB/km at sea level
        water_vapor_attenuation = 0.001 * frequency_ghz * frequency_ghz  # dB/km

        # 大氣厚度修正 (基於仰角)
        if elevation_angle < 90:
            elevation_rad = math.radians(elevation_angle)
            atmospheric_path_factor = 1.0 / math.sin(elevation_rad)
            atmospheric_path_factor = min(atmospheric_path_factor, 10.0)  # 限制最大值
        else:
            atmospheric_path_factor = 1.0

        # 假設大氣有效厚度為 10 km
        atmospheric_thickness = 10.0
        total_attenuation = (
            (oxygen_attenuation + water_vapor_attenuation)
            * atmospheric_thickness
            * atmospheric_path_factor
        )

        return total_attenuation

    def calculate_rain_attenuation(
        self, elevation_angle: float, frequency_ghz: float, rain_rate_mm_h: float = 0.0
    ) -> float:
        """
        計算降雨衰減 (dB) - 基於 ITU-R P.618

        Args:
            elevation_angle: 仰角 (度)
            frequency_ghz: 頻率 (GHz)
            rain_rate_mm_h: 降雨率 (mm/h)

        Returns:
            降雨衰減 (dB)
        """
        if rain_rate_mm_h <= 0:
            return 0.0

        # ITU-R P.618 參數 (簡化版)
        if frequency_ghz < 10:
            k = 0.0001 * (frequency_ghz**2.3)
            alpha = 1.0
        elif frequency_ghz < 20:
            k = 0.001 * (frequency_ghz**1.5)
            alpha = 1.1
        else:
            k = 0.01 * frequency_ghz
            alpha = 1.2

        # 比衰減 (dB/km)
        gamma_r = k * (rain_rate_mm_h**alpha)

        # 使用完整的 ITU-R P.618 實現
        try:
            from .itu_r_p618_rain_attenuation import itu_r_p618_model, Polarization

            result = itu_r_p618_model.calculate_rain_attenuation(
                frequency_ghz=frequency_ghz,
                elevation_angle_deg=elevation_angle,
                rain_rate_mm_h=rain_rate_mm_h,
                polarization=Polarization.CIRCULAR,  # 默認圓極化
                rain_height_km=2.0,  # 標準降雨高度
                earth_station_height_km=0.0,  # 海平面
            )

            return result["rain_attenuation_db"]

        except ImportError:
            # 降級到簡化實現（向後兼容）
            logger.warning("ITU-R P.618 完整實現不可用，使用簡化版本")

            # 有效路徑長度
            if elevation_angle > 5:
                elevation_rad = math.radians(elevation_angle)
                effective_path_length = 5.0 / math.sin(
                    elevation_rad
                )  # 假設雨層厚度 5km
            else:
                effective_path_length = 50.0  # 低仰角時的近似值

            rain_attenuation = gamma_r * effective_path_length
            return rain_attenuation

    def calculate_doppler_shift(
        self,
        satellite_velocity: Tuple[float, float, float],
        ue_velocity: Tuple[float, float, float],
        satellite_pos: Tuple[float, float, float],
        ue_pos: Tuple[float, float, float],
        frequency_hz: float,
    ) -> float:
        """
        計算多普勒頻移 (Hz)

        Args:
            satellite_velocity: 衛星速度向量 (vx, vy, vz) in m/s
            ue_velocity: UE速度向量 (vx, vy, vz) in m/s
            satellite_pos: 衛星位置 (x, y, z) in m
            ue_pos: UE位置 (x, y, z) in m
            frequency_hz: 載波頻率 (Hz)

        Returns:
            多普勒頻移 (Hz)
        """
        # 計算相對位置向量
        dx = satellite_pos[0] - ue_pos[0]
        dy = satellite_pos[1] - ue_pos[1]
        dz = satellite_pos[2] - ue_pos[2]
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        if distance == 0:
            return 0.0

        # 單位視線向量
        unit_x = dx / distance
        unit_y = dy / distance
        unit_z = dz / distance

        # 相對速度在視線方向的分量
        relative_vx = satellite_velocity[0] - ue_velocity[0]
        relative_vy = satellite_velocity[1] - ue_velocity[1]
        relative_vz = satellite_velocity[2] - ue_velocity[2]

        radial_velocity = (
            relative_vx * unit_x + relative_vy * unit_y + relative_vz * unit_z
        )

        # 多普勒頻移計算
        doppler_shift = -frequency_hz * radial_velocity / self.c

        return doppler_shift

    def calculate_elevation_dependent_gain(self, elevation_angle: float) -> float:
        """
        計算仰角相關的天線增益修正 (dB)

        Args:
            elevation_angle: 仰角 (度)

        Returns:
            增益修正 (dB)
        """
        if elevation_angle <= 0:
            return -30.0  # 地平線以下大幅衰減
        elif elevation_angle < 5:
            # 低仰角時的衰減
            return -15.0 + 2.0 * elevation_angle
        elif elevation_angle < 30:
            # 中等仰角的線性增益
            return -5.0 + 0.2 * elevation_angle
        else:
            # 高仰角時的最佳增益
            return 1.0

    def calculate_total_path_loss(
        self,
        distance_km: float,
        elevation_angle: float,
        frequency_ghz: float = 20.0,
        weather_condition: str = "clear",
        rain_rate_mm_h: float = 0.0,
    ) -> Dict[str, float]:
        """
        計算總路徑損耗及各項分量

        Args:
            distance_km: 傳播距離 (km)
            elevation_angle: 仰角 (度)
            frequency_ghz: 頻率 (GHz)
            weather_condition: 天氣狀況
            rain_rate_mm_h: 降雨率 (mm/h)

        Returns:
            包含各項損耗的字典
        """
        # 基礎自由空間損耗
        fspl = self.calculate_free_space_path_loss(distance_km, frequency_ghz)

        # 大氣衰減
        atmospheric_loss = self.calculate_atmospheric_attenuation(
            elevation_angle, frequency_ghz
        )

        # 降雨衰減
        if weather_condition == "rainy" and rain_rate_mm_h == 0.0:
            rain_rate_mm_h = 10.0  # 默認中雨
        elif weather_condition == "stormy" and rain_rate_mm_h == 0.0:
            rain_rate_mm_h = 25.0  # 默認大雨

        rain_loss = self.calculate_rain_attenuation(
            elevation_angle, frequency_ghz, rain_rate_mm_h
        )

        # 仰角相關損耗
        elevation_gain = self.calculate_elevation_dependent_gain(elevation_angle)

        # 額外的多路徑和建築物遮蔽損耗（簡化模型）
        if elevation_angle < 10:
            multipath_loss = 3.0 + (10 - elevation_angle) * 0.5
        else:
            multipath_loss = 0.0

        # 總損耗
        total_loss = (
            fspl + atmospheric_loss + rain_loss - elevation_gain + multipath_loss
        )

        return {
            "free_space_path_loss": fspl,
            "atmospheric_attenuation": atmospheric_loss,
            "rain_attenuation": rain_loss,
            "elevation_gain": elevation_gain,
            "multipath_loss": multipath_loss,
            "total_path_loss": total_loss,
            "frequency_ghz": frequency_ghz,
            "distance_km": distance_km,
            "elevation_angle": elevation_angle,
        }

    def calculate_received_power(
        self,
        transmit_power_dbm: float,
        path_loss_db: float,
        antenna_gain_db: float = 35.0,
    ) -> float:
        """
        計算接收功率

        Args:
            transmit_power_dbm: 發射功率 (dBm)
            path_loss_db: 路徑損耗 (dB)
            antenna_gain_db: 天線增益 (dB)

        Returns:
            接收功率 (dBm)
        """
        received_power = transmit_power_dbm + antenna_gain_db - path_loss_db
        return received_power

    def calculate_sinr(
        self,
        received_power_dbm: float,
        noise_power_dbm: float = -114.0,
        interference_power_dbm: float = -120.0,
    ) -> float:
        """
        計算信噪干擾比 (SINR)

        Args:
            received_power_dbm: 接收信號功率 (dBm)
            noise_power_dbm: 噪聲功率 (dBm)
            interference_power_dbm: 干擾功率 (dBm)

        Returns:
            SINR (dB)
        """
        # 轉換為線性功率
        signal_linear = 10 ** (received_power_dbm / 10.0)
        noise_linear = 10 ** (noise_power_dbm / 10.0)
        interference_linear = 10 ** (interference_power_dbm / 10.0)

        # 計算 SINR
        sinr_linear = signal_linear / (noise_linear + interference_linear)
        sinr_db = 10 * math.log10(sinr_linear)

        return sinr_db


class LEOSatelliteChannelModel:
    """LEO 衛星信道模型"""

    def __init__(self):
        self.propagation_model = PhysicalPropagationModel()

    def calculate_link_quality(
        self,
        satellite_state: Dict[str, Any],
        ue_state: Dict[str, Any],
        weather_condition: str = "clear",
        frequency_ghz: float = 20.0,
    ) -> Dict[str, float]:
        """
        計算鏈路品質指標

        Args:
            satellite_state: 衛星狀態
            ue_state: UE狀態
            weather_condition: 天氣狀況
            frequency_ghz: 頻率 (GHz)

        Returns:
            鏈路品質指標字典
        """
        # 獲取幾何參數
        distance_km = satellite_state.get("distance", 1000.0)
        elevation_angle = satellite_state.get("elevation_angle", 45.0)

        # 計算路徑損耗
        path_loss_info = self.propagation_model.calculate_total_path_loss(
            distance_km=distance_km,
            elevation_angle=elevation_angle,
            frequency_ghz=frequency_ghz,
            weather_condition=weather_condition,
        )

        # 衛星發射功率 (假設為 40 dBm)
        transmit_power_dbm = 40.0

        # 計算接收功率
        received_power = self.propagation_model.calculate_received_power(
            transmit_power_dbm=transmit_power_dbm,
            path_loss_db=path_loss_info["total_path_loss"],
            antenna_gain_db=35.0,
        )

        # 考慮系統負載對干擾的影響
        load_factor = satellite_state.get("load_factor", 0.5)
        base_interference = -120.0  # dBm
        interference_power = base_interference + 10 * math.log10(1 + load_factor * 10)

        # 計算 SINR
        sinr_db = self.propagation_model.calculate_sinr(
            received_power_dbm=received_power, interference_power_dbm=interference_power
        )

        # 估算吞吐量 (基於 Shannon 容量公式的簡化版)
        bandwidth_mhz = 100.0  # 假設頻寬
        sinr_linear = 10 ** (sinr_db / 10.0)
        shannon_capacity_mbps = bandwidth_mhz * math.log2(1 + sinr_linear)

        # 考慮協議效率和實際調製方案
        efficiency_factor = 0.7  # 70% 效率
        estimated_throughput = shannon_capacity_mbps * efficiency_factor

        # 估算延遲 (傳播延遲 + 處理延遲)
        propagation_delay_ms = distance_km / 300.0  # 光速傳播
        processing_delay_ms = 5.0 + load_factor * 10.0  # 處理延遲隨負載增加
        total_latency_ms = propagation_delay_ms + processing_delay_ms

        return {
            "received_power_dbm": received_power,
            "sinr_db": sinr_db,
            "estimated_throughput_mbps": estimated_throughput,
            "total_latency_ms": total_latency_ms,
            "path_loss_db": path_loss_info["total_path_loss"],
            "propagation_delay_ms": propagation_delay_ms,
            "processing_delay_ms": processing_delay_ms,
            **path_loss_info,
        }
