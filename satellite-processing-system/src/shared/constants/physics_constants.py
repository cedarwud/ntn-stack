"""
物理常數統一定義

整合來源：
- stage3_signal_analysis/stage3_physics_constants.py (Stage3專用物理常數)
- stage6_dynamic_pool_planning/physics_calculation_engine.py (物理計算引擎)
- shared/core_modules/signal_calculations_core.py (信號計算核心)
"""

import math
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PhysicsConstants:
    """統一物理常數定義"""

    # 基礎物理常數 (CODATA 2018)
    SPEED_OF_LIGHT: float = 299792458.0  # m/s - 精確定義值
    BOLTZMANN_CONSTANT: float = 1.380649e-23  # J/K - 2019重新定義
    PLANCK_CONSTANT: float = 6.62607015e-34  # J·s - 2019重新定義

    # 地球相關常數
    EARTH_RADIUS: float = 6371000.0  # m - 平均半徑
    EARTH_GM: float = 3.986004418e14  # m³/s² - 地球重力參數
    EARTH_J2: float = 1.08262668e-3  # J2攝動項
    EARTH_ROTATION_RATE: float = 7.2921159e-5  # rad/s - 地球自轉角速度

    # 電磁頻譜常數
    KU_BAND_FREQUENCY: float = 12.0e9  # Hz - Ku波段中心頻率
    KA_BAND_FREQUENCY: float = 30.0e9  # Hz - Ka波段中心頻率

    # 熱雜訊參數 (ITU-R P.372-13)
    THERMAL_NOISE_FLOOR_DBM_HZ: float = -174.0  # dBm/Hz - 標準熱雜訊底線
    SYSTEM_NOISE_TEMPERATURE: float = 290.0  # K - 標準系統雜訊溫度

    # SGP4軌道計算常數
    SGP4_XKE: float = 7.43669161e-2  # 單位轉換常數
    SGP4_QOMS2T: float = 1.88027916e-9  # (QOMS)^(2/3)
    SGP4_S: float = 1.01222928  # S常數

    # 3GPP NTN標準參數
    NTN_MIN_ELEVATION: float = 5.0  # degrees - 最小仰角
    NTN_HANDOVER_THRESHOLD: float = 10.0  # degrees - 換手仰角閾值
    NTN_RSRP_MIN: float = -140.0  # dBm - 最小RSRP閾值
    NTN_RSRP_MAX: float = -44.0  # dBm - 最大RSRP閾值


@dataclass
class SignalConstants:
    """信號計算相關常數"""

    # RSRP門檻 (基於3GPP TS 36.133)
    RSRP_EXCELLENT: float = -70.0  # dBm
    RSRP_GOOD: float = -85.0  # dBm
    RSRP_FAIR: float = -100.0  # dBm
    RSRP_POOR: float = -110.0  # dBm

    # RSRQ門檻 (基於3GPP TS 36.133)
    RSRQ_EXCELLENT: float = -10.0  # dB
    RSRQ_GOOD: float = -15.0  # dB
    RSRQ_FAIR: float = -20.0  # dB
    RSRQ_POOR: float = -25.0  # dB

    # SINR門檻
    SINR_EXCELLENT: float = 20.0  # dB
    SINR_GOOD: float = 13.0  # dB
    SINR_FAIR: float = 3.0  # dB
    SINR_POOR: float = 0.0  # dB

    # 信號品質權重
    RSRP_WEIGHT: float = 0.4
    RSRQ_WEIGHT: float = 0.3
    SINR_WEIGHT: float = 0.3


@dataclass
class ConstellationConstants:
    """衛星星座參數常數"""

    # Starlink參數 (基於FCC申報和公開技術文件)
    STARLINK_EIRP: float = 37.0  # dBm
    STARLINK_ANTENNA_GAIN: float = 35.0  # dB
    STARLINK_FREQUENCY: float = 12.0e9  # Hz
    STARLINK_ALTITUDE: float = 550000.0  # m

    # OneWeb參數
    ONEWEB_EIRP: float = 35.0  # dBm
    ONEWEB_ANTENNA_GAIN: float = 32.0  # dB
    ONEWEB_FREQUENCY: float = 11.7e9  # Hz
    ONEWEB_ALTITUDE: float = 1200000.0  # m

    # Amazon Kuiper參數
    KUIPER_EIRP: float = 36.0  # dBm
    KUIPER_ANTENNA_GAIN: float = 34.0  # dB
    KUIPER_FREQUENCY: float = 12.2e9  # Hz
    KUIPER_ALTITUDE: float = 630000.0  # m


class PhysicsConstantsManager:
    """物理常數管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.physics = PhysicsConstants()
        self.signal = SignalConstants()
        self.constellation = ConstellationConstants()

        # 載入時間戳
        self.loaded_at = datetime.now()

        self.logger.info("物理常數管理器已初始化")

    def get_physics_constants(self) -> PhysicsConstants:
        """獲取基礎物理常數"""
        return self.physics

    def get_signal_constants(self) -> SignalConstants:
        """獲取信號相關常數"""
        return self.signal

    def get_constellation_constants(self) -> ConstellationConstants:
        """獲取星座參數常數"""
        return self.constellation

    def calculate_thermal_noise_floor(self, bandwidth_hz: float, noise_figure_db: float = 7.0) -> float:
        """
        計算熱雜訊底線

        基於ITU-R P.372-13標準
        Formula: N = -174 + 10*log10(BW) + NF
        """
        bandwidth_db = 10 * math.log10(bandwidth_hz)
        thermal_noise = self.physics.THERMAL_NOISE_FLOOR_DBM_HZ + bandwidth_db + noise_figure_db
        return thermal_noise

    def calculate_free_space_path_loss(self, frequency_hz: float, distance_km: float) -> float:
        """
        計算自由空間路徑損耗

        基於Friis公式: FSPL = 32.45 + 20*log10(f) + 20*log10(d)
        """
        frequency_ghz = frequency_hz / 1e9
        fspl_db = 32.45 + 20 * math.log10(frequency_ghz) + 20 * math.log10(distance_km)
        return fspl_db

    def calculate_doppler_shift(self, frequency_hz: float, velocity_ms: float, elevation_rad: float) -> float:
        """
        計算都卜勒頻移

        Formula: Δf = (v * cos(θ) / c) * f
        """
        radial_velocity = velocity_ms * math.cos(elevation_rad)
        doppler_hz = (radial_velocity / self.physics.SPEED_OF_LIGHT) * frequency_hz
        return doppler_hz

    def get_constellation_parameters(self, constellation: str) -> Dict[str, float]:
        """獲取指定星座的參數"""
        constellation_map = {
            'starlink': {
                'eirp_dbm': self.constellation.STARLINK_EIRP,
                'antenna_gain_db': self.constellation.STARLINK_ANTENNA_GAIN,
                'frequency_hz': self.constellation.STARLINK_FREQUENCY,
                'altitude_m': self.constellation.STARLINK_ALTITUDE
            },
            'oneweb': {
                'eirp_dbm': self.constellation.ONEWEB_EIRP,
                'antenna_gain_db': self.constellation.ONEWEB_ANTENNA_GAIN,
                'frequency_hz': self.constellation.ONEWEB_FREQUENCY,
                'altitude_m': self.constellation.ONEWEB_ALTITUDE
            },
            'kuiper': {
                'eirp_dbm': self.constellation.KUIPER_EIRP,
                'antenna_gain_db': self.constellation.KUIPER_ANTENNA_GAIN,
                'frequency_hz': self.constellation.KUIPER_FREQUENCY,
                'altitude_m': self.constellation.KUIPER_ALTITUDE
            }
        }

        return constellation_map.get(constellation.lower(), constellation_map['starlink'])

    def get_signal_quality_thresholds(self, metric: str) -> Dict[str, float]:
        """獲取信號品質門檻值"""
        thresholds_map = {
            'rsrp': {
                'excellent': self.signal.RSRP_EXCELLENT,
                'good': self.signal.RSRP_GOOD,
                'fair': self.signal.RSRP_FAIR,
                'poor': self.signal.RSRP_POOR
            },
            'rsrq': {
                'excellent': self.signal.RSRQ_EXCELLENT,
                'good': self.signal.RSRQ_GOOD,
                'fair': self.signal.RSRQ_FAIR,
                'poor': self.signal.RSRQ_POOR
            },
            'sinr': {
                'excellent': self.signal.SINR_EXCELLENT,
                'good': self.signal.SINR_GOOD,
                'fair': self.signal.SINR_FAIR,
                'poor': self.signal.SINR_POOR
            }
        }

        return thresholds_map.get(metric.lower(), {})

    def validate_constants(self) -> Dict[str, Any]:
        """驗證物理常數的合理性"""
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'validation_passed': True,
            'errors': [],
            'warnings': []
        }

        try:
            # 驗證基礎物理常數
            if abs(self.physics.SPEED_OF_LIGHT - 299792458.0) > 1e-6:
                validation_result['errors'].append('光速常數不正確')
                validation_result['validation_passed'] = False

            if abs(self.physics.BOLTZMANN_CONSTANT - 1.380649e-23) > 1e-28:
                validation_result['errors'].append('玻爾茲曼常數不正確')
                validation_result['validation_passed'] = False

            # 驗證地球參數
            if not (6.3e6 <= self.physics.EARTH_RADIUS <= 6.4e6):
                validation_result['warnings'].append('地球半徑參數可能不準確')

            # 驗證信號門檻合理性
            if not (self.signal.RSRP_POOR < self.signal.RSRP_FAIR < self.signal.RSRP_GOOD < self.signal.RSRP_EXCELLENT):
                validation_result['errors'].append('RSRP門檻值順序不正確')
                validation_result['validation_passed'] = False

            # 驗證權重總和
            total_weight = self.signal.RSRP_WEIGHT + self.signal.RSRQ_WEIGHT + self.signal.SINR_WEIGHT
            if abs(total_weight - 1.0) > 0.01:
                validation_result['warnings'].append(f'信號品質權重總和不為1.0: {total_weight}')

        except Exception as e:
            validation_result['errors'].append(f'驗證過程發生錯誤: {str(e)}')
            validation_result['validation_passed'] = False

        return validation_result

    def export_constants(self) -> Dict[str, Any]:
        """導出所有常數配置"""
        return {
            'export_timestamp': datetime.now().isoformat(),
            'loaded_at': self.loaded_at.isoformat(),
            'physics_constants': {
                'speed_of_light': self.physics.SPEED_OF_LIGHT,
                'boltzmann_constant': self.physics.BOLTZMANN_CONSTANT,
                'planck_constant': self.physics.PLANCK_CONSTANT,
                'earth_radius': self.physics.EARTH_RADIUS,
                'earth_gm': self.physics.EARTH_GM,
                'earth_j2': self.physics.EARTH_J2,
                'earth_rotation_rate': self.physics.EARTH_ROTATION_RATE
            },
            'signal_constants': {
                'rsrp_thresholds': {
                    'excellent': self.signal.RSRP_EXCELLENT,
                    'good': self.signal.RSRP_GOOD,
                    'fair': self.signal.RSRP_FAIR,
                    'poor': self.signal.RSRP_POOR
                },
                'rsrq_thresholds': {
                    'excellent': self.signal.RSRQ_EXCELLENT,
                    'good': self.signal.RSRQ_GOOD,
                    'fair': self.signal.RSRQ_FAIR,
                    'poor': self.signal.RSRQ_POOR
                },
                'quality_weights': {
                    'rsrp': self.signal.RSRP_WEIGHT,
                    'rsrq': self.signal.RSRQ_WEIGHT,
                    'sinr': self.signal.SINR_WEIGHT
                }
            },
            'constellation_parameters': {
                'starlink': self.get_constellation_parameters('starlink'),
                'oneweb': self.get_constellation_parameters('oneweb'),
                'kuiper': self.get_constellation_parameters('kuiper')
            }
        }


# 全局實例 (單例模式)
_physics_constants_instance: Optional[PhysicsConstantsManager] = None


def get_physics_constants() -> PhysicsConstantsManager:
    """獲取物理常數管理器實例 (單例模式)"""
    global _physics_constants_instance
    if _physics_constants_instance is None:
        _physics_constants_instance = PhysicsConstantsManager()
    return _physics_constants_instance


def get_thermal_noise_floor(bandwidth_hz: float = 20e6, noise_figure_db: float = 7.0) -> float:
    """便捷函數：計算熱雜訊底線"""
    return get_physics_constants().calculate_thermal_noise_floor(bandwidth_hz, noise_figure_db)


def get_free_space_path_loss(frequency_hz: float, distance_km: float) -> float:
    """便捷函數：計算自由空間路徑損耗"""
    return get_physics_constants().calculate_free_space_path_loss(frequency_hz, distance_km)


def get_constellation_params(constellation: str) -> Dict[str, float]:
    """便捷函數：獲取星座參數"""
    return get_physics_constants().get_constellation_parameters(constellation)


def get_signal_thresholds(metric: str) -> Dict[str, float]:
    """便捷函數：獲取信號品質門檻"""
    return get_physics_constants().get_signal_quality_thresholds(metric)


# 常用常數的快速訪問
SPEED_OF_LIGHT = PhysicsConstants.SPEED_OF_LIGHT
EARTH_RADIUS = PhysicsConstants.EARTH_RADIUS
EARTH_GM = PhysicsConstants.EARTH_GM
BOLTZMANN_CONSTANT = PhysicsConstants.BOLTZMANN_CONSTANT