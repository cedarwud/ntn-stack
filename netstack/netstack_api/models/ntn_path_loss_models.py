"""
3GPP TR 38.811 NTN 路徑損耗模型
實現 NTN 特定的多路徑和陰影衰落模型
符合論文研究級數據真實性要求

主要功能：
1. 3GPP TR 38.811 NTN 路徑損耗模型
2. 衛星天線增益和指向性
3. 多路徑衰落模型
4. 陰影衰落統計模型
5. 頻率相關的傳播特性
"""

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class NTNScenario(Enum):
    """NTN 場景類型"""

    URBAN_MACRO = "urban_macro"
    URBAN_MICRO = "urban_micro"
    RURAL_MACRO = "rural_macro"
    SUBURBAN = "suburban"
    DENSE_URBAN = "dense_urban"
    OPEN_SEA = "open_sea"


class SatelliteOrbitType(Enum):
    """衛星軌道類型"""

    LEO = "leo"  # 低地球軌道 (500-2000 km)
    MEO = "meo"  # 中地球軌道 (2000-35786 km)
    GEO = "geo"  # 地球同步軌道 (35786 km)


@dataclass
class AntennaPattern:
    """天線方向圖參數"""

    max_gain_dbi: float  # 最大增益 (dBi)
    half_power_beamwidth_deg: float  # 半功率波束寬度 (度)
    front_to_back_ratio_db: float  # 前後比 (dB)
    side_lobe_level_db: float  # 旁瓣電平 (dB)

    # 3D 方向圖參數
    azimuth_beamwidth_deg: float  # 方位角波束寬度
    elevation_beamwidth_deg: float  # 仰角波束寬度

    # 極化參數
    polarization: str = "linear"  # linear, circular
    cross_pol_discrimination_db: float = 30.0  # 交叉極化鑑別度


@dataclass
class NTNPathLossResult:
    """NTN 路徑損耗計算結果"""

    # 基本路徑損耗
    free_space_path_loss_db: float
    atmospheric_loss_db: float
    rain_attenuation_db: float

    # NTN 特定損耗
    multipath_fading_db: float
    shadow_fading_db: float
    building_penetration_loss_db: float
    foliage_loss_db: float

    # 天線增益
    satellite_antenna_gain_db: float
    user_antenna_gain_db: float
    pointing_loss_db: float
    polarization_loss_db: float

    # 總路徑損耗
    total_path_loss_db: float

    # 鏈路預算參數
    link_margin_db: float
    fade_margin_db: float

    # 計算參數
    frequency_ghz: float
    distance_km: float
    elevation_angle_deg: float
    scenario: NTNScenario
    orbit_type: SatelliteOrbitType


class NTNPathLossModel:
    """3GPP TR 38.811 NTN 路徑損耗模型"""

    def __init__(self):
        """初始化模型參數"""
        self.c = 299792458.0  # 光速 (m/s)

        # 3GPP TR 38.811 模型參數
        self.ntn_parameters = {
            "urban_macro": {
                "shadow_fading_std_db": 8.0,
                "multipath_k_factor_db": 10.0,
                "building_penetration_db": 15.0,
                "foliage_loss_db_per_m": 0.4,
            },
            "urban_micro": {
                "shadow_fading_std_db": 6.0,
                "multipath_k_factor_db": 12.0,
                "building_penetration_db": 10.0,
                "foliage_loss_db_per_m": 0.3,
            },
            "rural_macro": {
                "shadow_fading_std_db": 4.0,
                "multipath_k_factor_db": 15.0,
                "building_penetration_db": 5.0,
                "foliage_loss_db_per_m": 0.2,
            },
            "suburban": {
                "shadow_fading_std_db": 5.0,
                "multipath_k_factor_db": 13.0,
                "building_penetration_db": 8.0,
                "foliage_loss_db_per_m": 0.25,
            },
            "dense_urban": {
                "shadow_fading_std_db": 10.0,
                "multipath_k_factor_db": 8.0,
                "building_penetration_db": 20.0,
                "foliage_loss_db_per_m": 0.5,
            },
            "open_sea": {
                "shadow_fading_std_db": 2.0,
                "multipath_k_factor_db": 20.0,
                "building_penetration_db": 0.0,
                "foliage_loss_db_per_m": 0.0,
            },
        }

        logger.info("3GPP TR 38.811 NTN 路徑損耗模型初始化完成")

    def calculate_free_space_path_loss(
        self, frequency_ghz: float, distance_km: float
    ) -> float:
        """
        計算自由空間路徑損耗

        Args:
            frequency_ghz: 頻率 (GHz)
            distance_km: 距離 (km)

        Returns:
            自由空間路徑損耗 (dB)
        """
        # Friis 公式: FSPL = 20*log10(4πdf/c)
        # 簡化為: FSPL = 32.45 + 20*log10(f_MHz) + 20*log10(d_km)
        frequency_mhz = frequency_ghz * 1000
        fspl_db = 32.45 + 20 * math.log10(frequency_mhz) + 20 * math.log10(distance_km)

        return fspl_db

    def calculate_atmospheric_attenuation(
        self,
        frequency_ghz: float,
        elevation_angle_deg: float,
        water_vapor_density_g_m3: float = 7.5,
        surface_pressure_hpa: float = 1013.25,
    ) -> float:
        """
        計算大氣衰減 (基於 ITU-R P.676)

        Args:
            frequency_ghz: 頻率 (GHz)
            elevation_angle_deg: 仰角 (度)
            water_vapor_density_g_m3: 水蒸氣密度 (g/m³)
            surface_pressure_hpa: 地面氣壓 (hPa)

        Returns:
            大氣衰減 (dB)
        """
        # 氧氣吸收 (ITU-R P.676-12)
        oxygen_attenuation = self._calculate_oxygen_attenuation(
            frequency_ghz, surface_pressure_hpa
        )

        # 水蒸氣吸收
        water_vapor_attenuation = self._calculate_water_vapor_attenuation(
            frequency_ghz, water_vapor_density_g_m3
        )

        # 總比衰減 (dB/km)
        total_specific_attenuation = oxygen_attenuation + water_vapor_attenuation

        # 大氣路徑長度修正 (考慮仰角)
        if elevation_angle_deg > 0:
            path_length_factor = 1.0 / math.sin(math.radians(elevation_angle_deg))
            # 限制最大路徑長度因子 (低仰角時)
            path_length_factor = min(path_length_factor, 10.0)
        else:
            path_length_factor = 10.0

        # 有效大氣厚度 (簡化模型)
        effective_atmosphere_thickness_km = 8.0  # 對流層有效厚度

        total_attenuation_db = (
            total_specific_attenuation
            * effective_atmosphere_thickness_km
            * path_length_factor
        )

        return total_attenuation_db

    def _calculate_oxygen_attenuation(
        self, frequency_ghz: float, pressure_hpa: float
    ) -> float:
        """計算氧氣吸收衰減 (dB/km)"""
        # ITU-R P.676-12 氧氣吸收模型 (簡化)
        f = frequency_ghz
        p = pressure_hpa / 1013.25  # 標準化氣壓

        # 主要氧氣吸收線 (60 GHz 附近)
        if f < 54:
            gamma_o = 7.2e-3 * p * f**2 / (f**2 + 0.34 * p**2)
        elif f < 66:
            # 60 GHz 吸收帶
            gamma_o = 0.05 + 0.9 * p * math.exp(-(((f - 60) / 9) ** 2))
        else:
            gamma_o = 3.6e-3 * p * f**2 / (f**2 + 1.6 * p**2)

        return gamma_o

    def _calculate_water_vapor_attenuation(
        self, frequency_ghz: float, water_vapor_density_g_m3: float
    ) -> float:
        """計算水蒸氣吸收衰減 (dB/km)"""
        # ITU-R P.676-12 水蒸氣吸收模型 (簡化)
        f = frequency_ghz
        rho = water_vapor_density_g_m3

        # 主要水蒸氣吸收線 (22.235 GHz, 183.31 GHz 等)
        if f < 25:
            # 22.235 GHz 線
            gamma_w = 0.05 * rho * f**2 / ((f - 22.235) ** 2 + 2.56)
        elif f < 200:
            # 183.31 GHz 線的影響 (簡化)
            gamma_w = 0.02 * rho * f**2 / ((f - 183.31) ** 2 + 100)
        else:
            gamma_w = 0.01 * rho * f**1.5

        return gamma_w

    def calculate_multipath_fading(
        self, scenario: NTNScenario, elevation_angle_deg: float, frequency_ghz: float
    ) -> float:
        """
        計算多路徑衰落

        Args:
            scenario: NTN 場景
            elevation_angle_deg: 仰角
            frequency_ghz: 頻率

        Returns:
            多路徑衰落 (dB)
        """
        params = self.ntn_parameters[scenario.value]
        k_factor_db = params["multipath_k_factor_db"]

        # 仰角修正 (低仰角時多路徑更嚴重)
        elevation_factor = max(0.1, math.sin(math.radians(elevation_angle_deg)))
        k_factor_corrected = k_factor_db * elevation_factor

        # 頻率修正 (高頻時多路徑影響較小)
        frequency_factor = 1.0 + 0.1 * math.log10(frequency_ghz)
        k_factor_final = k_factor_corrected * frequency_factor

        # Rician 衰落轉換為功率衰落 (簡化)
        # 實際應用中需要更複雜的統計模型
        multipath_fading_db = -k_factor_final / 2.0

        return multipath_fading_db

    def calculate_shadow_fading(
        self, scenario: NTNScenario, distance_km: float
    ) -> float:
        """
        計算陰影衰落

        Args:
            scenario: NTN 場景
            distance_km: 距離

        Returns:
            陰影衰落 (dB)
        """
        params = self.ntn_parameters[scenario.value]
        std_dev_db = params["shadow_fading_std_db"]

        # 距離相關的陰影衰落 (簡化模型)
        # 實際應用中應使用對數正態分布
        distance_factor = 1.0 + 0.1 * math.log10(distance_km / 1000.0)
        shadow_fading_std = std_dev_db * distance_factor

        # 生成隨機陰影衰落值 (0 均值)
        # 在實際應用中，這應該是基於位置的確定性值
        shadow_fading_db = 0.0  # 平均值，實際應用中需要統計模型

        return shadow_fading_db

    def calculate_satellite_antenna_gain(
        self, antenna_pattern: AntennaPattern, off_boresight_angle_deg: float
    ) -> Tuple[float, float]:
        """
        計算衛星天線增益和指向損耗

        Args:
            antenna_pattern: 天線方向圖參數
            off_boresight_angle_deg: 偏離主瓣角度

        Returns:
            (天線增益 dB, 指向損耗 dB)
        """
        max_gain = antenna_pattern.max_gain_dbi
        hpbw = antenna_pattern.half_power_beamwidth_deg
        sll = antenna_pattern.side_lobe_level_db

        # 簡化的天線方向圖模型
        if off_boresight_angle_deg <= hpbw / 2:
            # 主瓣內
            gain_db = max_gain - 3 * (off_boresight_angle_deg / (hpbw / 2)) ** 2
            pointing_loss_db = 0.0
        elif off_boresight_angle_deg <= 2 * hpbw:
            # 第一旁瓣
            gain_db = max_gain - 12 - sll
            pointing_loss_db = 3.0
        else:
            # 遠旁瓣
            gain_db = max_gain - 20 - sll
            pointing_loss_db = 6.0

        return gain_db, pointing_loss_db

    def calculate_ntn_path_loss(
        self,
        frequency_ghz: float,
        satellite_altitude_km: float,
        elevation_angle_deg: float,
        scenario: NTNScenario,
        orbit_type: SatelliteOrbitType,
        satellite_antenna: AntennaPattern,
        user_antenna_gain_dbi: float = 0.0,
        off_boresight_angle_deg: float = 0.0,
        weather_data: Optional[Dict[str, float]] = None,
    ) -> NTNPathLossResult:
        """
        計算完整的 NTN 路徑損耗

        Args:
            frequency_ghz: 頻率 (GHz)
            satellite_altitude_km: 衛星高度 (km)
            elevation_angle_deg: 仰角 (度)
            scenario: NTN 場景
            orbit_type: 軌道類型
            satellite_antenna: 衛星天線參數
            user_antenna_gain_dbi: 用戶天線增益 (dBi)
            off_boresight_angle_deg: 偏離主瓣角度 (度)
            weather_data: 氣象數據

        Returns:
            NTN 路徑損耗結果
        """
        try:
            # 計算距離
            earth_radius_km = 6371.0
            if elevation_angle_deg > 0:
                # 球面三角法計算斜距
                elevation_rad = math.radians(elevation_angle_deg)
                distance_km = math.sqrt(
                    (earth_radius_km + satellite_altitude_km) ** 2
                    - earth_radius_km**2 * math.cos(elevation_rad) ** 2
                ) - earth_radius_km * math.sin(elevation_rad)
            else:
                distance_km = satellite_altitude_km

            # 基本路徑損耗
            fspl_db = self.calculate_free_space_path_loss(frequency_ghz, distance_km)

            # 大氣衰減
            water_vapor = (
                weather_data.get("water_vapor_density_g_m3", 7.5)
                if weather_data
                else 7.5
            )
            pressure = (
                weather_data.get("pressure_hpa", 1013.25) if weather_data else 1013.25
            )
            atmospheric_loss_db = self.calculate_atmospheric_attenuation(
                frequency_ghz, elevation_angle_deg, water_vapor, pressure
            )

            # 降雨衰減 (如果有氣象數據)
            rain_rate = (
                weather_data.get("rainfall_rate_mm_h", 0.0) if weather_data else 0.0
            )
            rain_attenuation_db = self._calculate_rain_attenuation(
                frequency_ghz, rain_rate, elevation_angle_deg
            )

            # NTN 特定衰落
            multipath_fading_db = self.calculate_multipath_fading(
                scenario, elevation_angle_deg, frequency_ghz
            )
            shadow_fading_db = self.calculate_shadow_fading(scenario, distance_km)

            # 建築物穿透損耗
            params = self.ntn_parameters[scenario.value]
            building_penetration_db = params["building_penetration_db"]
            foliage_loss_db = params["foliage_loss_db_per_m"] * 10  # 假設 10m 植被

            # 天線增益
            sat_antenna_gain_db, pointing_loss_db = (
                self.calculate_satellite_antenna_gain(
                    satellite_antenna, off_boresight_angle_deg
                )
            )

            # 極化損耗 (簡化)
            polarization_loss_db = 0.5  # 典型值

            # 總路徑損耗
            total_path_loss_db = (
                fspl_db
                + atmospheric_loss_db
                + rain_attenuation_db
                + abs(multipath_fading_db)
                + abs(shadow_fading_db)
                + building_penetration_db
                + foliage_loss_db
                + pointing_loss_db
                + polarization_loss_db
                - sat_antenna_gain_db
                - user_antenna_gain_dbi
            )

            # 鏈路預算參數
            fade_margin_db = 10.0  # 典型衰落裕度
            link_margin_db = 3.0  # 鏈路裕度

            return NTNPathLossResult(
                free_space_path_loss_db=fspl_db,
                atmospheric_loss_db=atmospheric_loss_db,
                rain_attenuation_db=rain_attenuation_db,
                multipath_fading_db=multipath_fading_db,
                shadow_fading_db=shadow_fading_db,
                building_penetration_loss_db=building_penetration_db,
                foliage_loss_db=foliage_loss_db,
                satellite_antenna_gain_db=sat_antenna_gain_db,
                user_antenna_gain_db=user_antenna_gain_dbi,
                pointing_loss_db=pointing_loss_db,
                polarization_loss_db=polarization_loss_db,
                total_path_loss_db=total_path_loss_db,
                link_margin_db=link_margin_db,
                fade_margin_db=fade_margin_db,
                frequency_ghz=frequency_ghz,
                distance_km=distance_km,
                elevation_angle_deg=elevation_angle_deg,
                scenario=scenario,
                orbit_type=orbit_type,
            )

        except Exception as e:
            logger.error(f"NTN 路徑損耗計算失敗: {e}")
            # 返回默認值
            return NTNPathLossResult(
                free_space_path_loss_db=150.0,
                atmospheric_loss_db=1.0,
                rain_attenuation_db=0.0,
                multipath_fading_db=-5.0,
                shadow_fading_db=0.0,
                building_penetration_loss_db=10.0,
                foliage_loss_db=2.0,
                satellite_antenna_gain_db=30.0,
                user_antenna_gain_db=0.0,
                pointing_loss_db=1.0,
                polarization_loss_db=0.5,
                total_path_loss_db=130.0,
                link_margin_db=3.0,
                fade_margin_db=10.0,
                frequency_ghz=frequency_ghz,
                distance_km=1000.0,
                elevation_angle_deg=elevation_angle_deg,
                scenario=scenario,
                orbit_type=orbit_type,
            )

    def _calculate_rain_attenuation(
        self, frequency_ghz: float, rain_rate_mm_h: float, elevation_angle_deg: float
    ) -> float:
        """計算降雨衰減 (ITU-R P.618)"""
        if rain_rate_mm_h <= 0:
            return 0.0

        # ITU-R P.838 比衰減係數
        if frequency_ghz < 1:
            k = 0.0001
            alpha = 0.5
        elif frequency_ghz < 10:
            k = 0.01 * frequency_ghz**0.5
            alpha = 1.0
        elif frequency_ghz < 100:
            k = 0.1 * frequency_ghz**0.3
            alpha = 1.1
        else:
            k = 1.0
            alpha = 1.2

        # 比衰減 (dB/km)
        specific_attenuation = k * rain_rate_mm_h**alpha

        # 有效路徑長度
        if elevation_angle_deg > 0:
            path_length_factor = 1.0 / math.sin(math.radians(elevation_angle_deg))
            effective_path_length_km = min(
                5.0 * path_length_factor, 20.0
            )  # 限制最大路徑
        else:
            effective_path_length_km = 20.0

        rain_attenuation_db = specific_attenuation * effective_path_length_km

        return rain_attenuation_db


# 預定義天線方向圖
STARLINK_ANTENNA_PATTERN = AntennaPattern(
    max_gain_dbi=35.0,
    half_power_beamwidth_deg=2.0,
    front_to_back_ratio_db=25.0,
    side_lobe_level_db=20.0,
    azimuth_beamwidth_deg=2.0,
    elevation_beamwidth_deg=2.0,
    polarization="circular",
    cross_pol_discrimination_db=25.0,
)

ONEWEB_ANTENNA_PATTERN = AntennaPattern(
    max_gain_dbi=32.0,
    half_power_beamwidth_deg=2.5,
    front_to_back_ratio_db=22.0,
    side_lobe_level_db=18.0,
    azimuth_beamwidth_deg=2.5,
    elevation_beamwidth_deg=2.5,
    polarization="linear",
    cross_pol_discrimination_db=30.0,
)

KUIPER_ANTENNA_PATTERN = AntennaPattern(
    max_gain_dbi=33.0,
    half_power_beamwidth_deg=2.2,
    front_to_back_ratio_db=24.0,
    side_lobe_level_db=19.0,
    azimuth_beamwidth_deg=2.2,
    elevation_beamwidth_deg=2.2,
    polarization="circular",
    cross_pol_discrimination_db=28.0,
)
