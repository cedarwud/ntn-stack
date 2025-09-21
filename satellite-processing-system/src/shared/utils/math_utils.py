"""
數學計算工具

整合來源：
- 各Stage中的數學計算邏輯
- 軌道力學計算
- 信號處理數學函數
"""

import math
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class Vector3D:
    """3D向量類"""
    x: float
    y: float
    z: float

    def magnitude(self) -> float:
        """計算向量長度"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3D':
        """單位化向量"""
        mag = self.magnitude()
        if mag == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x/mag, self.y/mag, self.z/mag)

    def dot(self, other: 'Vector3D') -> float:
        """點積"""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3D') -> 'Vector3D':
        """叉積"""
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def distance_to(self, other: 'Vector3D') -> float:
        """計算到另一點的距離"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx**2 + dy**2 + dz**2)

    def to_dict(self) -> Dict[str, float]:
        """轉換為字典"""
        return {'x': self.x, 'y': self.y, 'z': self.z}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Vector3D':
        """從字典創建向量"""
        return cls(data.get('x', 0), data.get('y', 0), data.get('z', 0))


class MathUtils:
    """數學計算工具類"""

    @staticmethod
    def deg_to_rad(degrees: float) -> float:
        """角度轉弧度"""
        return math.radians(degrees)

    @staticmethod
    def rad_to_deg(radians: float) -> float:
        """弧度轉角度"""
        return math.degrees(radians)

    @staticmethod
    def safe_log10(value: float, default: float = -100.0) -> float:
        """安全的log10計算"""
        try:
            if value <= 0:
                return default
            return math.log10(value)
        except (ValueError, OverflowError):
            return default

    @staticmethod
    def safe_sqrt(value: float, default: float = 0.0) -> float:
        """安全的平方根計算"""
        try:
            if value < 0:
                return default
            return math.sqrt(value)
        except (ValueError, OverflowError):
            return default

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """限制值在指定範圍內"""
        return max(min_val, min(value, max_val))

    @staticmethod
    def linear_interpolation(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
        """線性插值"""
        if x2 == x1:
            return y1
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

    @staticmethod
    def calculate_distance_3d(pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """計算3D空間兩點距離"""
        try:
            dx = pos1['x'] - pos2['x']
            dy = pos1['y'] - pos2['y']
            dz = pos1['z'] - pos2['z']
            return math.sqrt(dx**2 + dy**2 + dz**2)
        except (KeyError, TypeError):
            logger.error("3D距離計算參數錯誤")
            return 0.0

    @staticmethod
    def calculate_elevation_azimuth(satellite_pos: Dict[str, float], observer_pos: Dict[str, float]) -> Dict[str, float]:
        """
        計算衛星相對於觀測者的仰角和方位角

        Args:
            satellite_pos: 衛星位置 {'x', 'y', 'z'} (km)
            observer_pos: 觀測者位置 {'lat', 'lon', 'alt'} (度, 度, km)

        Returns:
            {'elevation_deg': float, 'azimuth_deg': float, 'range_km': float}
        """
        try:
            # 簡化的計算，實際應用中需要更精確的座標轉換
            lat_rad = math.radians(observer_pos.get('lat', 0))
            lon_rad = math.radians(observer_pos.get('lon', 0))
            alt_km = observer_pos.get('alt', 0)

            # 地球半徑
            earth_radius = 6371.0  # km

            # 觀測者在ECI座標系中的位置（簡化）
            observer_radius = earth_radius + alt_km
            obs_x = observer_radius * math.cos(lat_rad) * math.cos(lon_rad)
            obs_y = observer_radius * math.cos(lat_rad) * math.sin(lon_rad)
            obs_z = observer_radius * math.sin(lat_rad)

            # 相對位置向量
            rel_x = satellite_pos['x'] - obs_x
            rel_y = satellite_pos['y'] - obs_y
            rel_z = satellite_pos['z'] - obs_z

            # 距離
            range_km = math.sqrt(rel_x**2 + rel_y**2 + rel_z**2)

            # 仰角（簡化計算）
            elevation_rad = math.asin(rel_z / range_km) if range_km > 0 else 0
            elevation_deg = math.degrees(elevation_rad)

            # 方位角（簡化計算）
            azimuth_rad = math.atan2(rel_y, rel_x)
            azimuth_deg = (math.degrees(azimuth_rad) + 360) % 360

            return {
                'elevation_deg': elevation_deg,
                'azimuth_deg': azimuth_deg,
                'range_km': range_km
            }

        except Exception as e:
            logger.error(f"仰角方位角計算失敗: {e}")
            return {'elevation_deg': 0.0, 'azimuth_deg': 0.0, 'range_km': 0.0}

    @staticmethod
    def calculate_doppler_shift(frequency_hz: float, velocity_ms: float, angle_rad: float) -> float:
        """
        計算都卜勒頻移

        Args:
            frequency_hz: 載波頻率 (Hz)
            velocity_ms: 相對速度 (m/s)
            angle_rad: 速度方向與視線的夾角 (弧度)

        Returns:
            都卜勒頻移 (Hz)
        """
        try:
            speed_of_light = 299792458.0  # m/s
            radial_velocity = velocity_ms * math.cos(angle_rad)
            doppler_hz = (radial_velocity / speed_of_light) * frequency_hz
            return doppler_hz
        except Exception as e:
            logger.error(f"都卜勒頻移計算失敗: {e}")
            return 0.0

    @staticmethod
    def calculate_free_space_path_loss(frequency_ghz: float, distance_km: float) -> float:
        """
        計算自由空間路徑損耗

        Args:
            frequency_ghz: 頻率 (GHz)
            distance_km: 距離 (km)

        Returns:
            路徑損耗 (dB)
        """
        try:
            if frequency_ghz <= 0 or distance_km <= 0:
                return float('inf')

            fspl_db = 32.45 + 20 * math.log10(frequency_ghz) + 20 * math.log10(distance_km)
            return fspl_db
        except Exception as e:
            logger.error(f"路徑損耗計算失敗: {e}")
            return float('inf')

    @staticmethod
    def calculate_antenna_gain(elevation_deg: float, gain_pattern: str = "cosine") -> float:
        """
        計算基於仰角的天線增益

        Args:
            elevation_deg: 仰角 (度)
            gain_pattern: 增益模式 ("cosine", "linear", "constant")

        Returns:
            相對增益 (dB)
        """
        try:
            elevation_rad = math.radians(max(0, elevation_deg))

            if gain_pattern == "cosine":
                # 餘弦模式：高仰角增益好
                gain_factor = math.cos(math.pi/2 - elevation_rad)
                return 20 * math.log10(max(0.1, gain_factor))

            elif gain_pattern == "linear":
                # 線性模式
                gain_factor = elevation_deg / 90.0
                return 10 * math.log10(max(0.1, gain_factor))

            else:  # constant
                return 0.0

        except Exception as e:
            logger.error(f"天線增益計算失敗: {e}")
            return 0.0

    @staticmethod
    def calculate_signal_quality_score(rsrp_dbm: float, rsrq_db: float, sinr_db: float) -> float:
        """
        計算綜合信號品質分數

        Args:
            rsrp_dbm: RSRP值 (dBm)
            rsrq_db: RSRQ值 (dB)
            sinr_db: SINR值 (dB)

        Returns:
            品質分數 (0-1)
        """
        try:
            # RSRP分數 (基於-140到-40 dBm範圍)
            rsrp_score = MathUtils.clamp((rsrp_dbm + 140) / 100, 0, 1)

            # RSRQ分數 (基於-25到-10 dB範圍)
            rsrq_score = MathUtils.clamp((rsrq_db + 25) / 15, 0, 1)

            # SINR分數 (基於-5到25 dB範圍)
            sinr_score = MathUtils.clamp((sinr_db + 5) / 30, 0, 1)

            # 加權平均
            total_score = 0.4 * rsrp_score + 0.3 * rsrq_score + 0.3 * sinr_score
            return MathUtils.clamp(total_score, 0, 1)

        except Exception as e:
            logger.error(f"信號品質分數計算失敗: {e}")
            return 0.0

    @staticmethod
    def solve_kepler_equation(mean_anomaly: float, eccentricity: float, tolerance: float = 1e-6) -> float:
        """
        求解開普勒方程

        Args:
            mean_anomaly: 平近點角 (弧度)
            eccentricity: 偏心率
            tolerance: 收斂容忍度

        Returns:
            偏近點角 (弧度)
        """
        try:
            # 牛頓-拉夫遜法求解 E - e*sin(E) = M
            eccentric_anomaly = mean_anomaly  # 初始猜測

            for _ in range(20):  # 最大迭代次數
                f = eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly) - mean_anomaly
                fp = 1 - eccentricity * math.cos(eccentric_anomaly)

                if abs(fp) < 1e-12:
                    break

                delta = f / fp
                eccentric_anomaly -= delta

                if abs(delta) < tolerance:
                    break

            return eccentric_anomaly

        except Exception as e:
            logger.error(f"開普勒方程求解失敗: {e}")
            return mean_anomaly

    @staticmethod
    def calculate_orbital_period(semi_major_axis_km: float, central_body_mu: float = 3.986004418e5) -> float:
        """
        計算軌道週期

        Args:
            semi_major_axis_km: 半長軸 (km)
            central_body_mu: 中心天體重力參數 (km³/s²)

        Returns:
            軌道週期 (秒)
        """
        try:
            period_seconds = 2 * math.pi * math.sqrt(semi_major_axis_km**3 / central_body_mu)
            return period_seconds
        except Exception as e:
            logger.error(f"軌道週期計算失敗: {e}")
            return 0.0

    @staticmethod
    def moving_average(data: List[float], window_size: int) -> List[float]:
        """
        計算移動平均

        Args:
            data: 數據列表
            window_size: 窗口大小

        Returns:
            移動平均後的數據
        """
        try:
            if window_size <= 0 or len(data) < window_size:
                return data.copy()

            averaged_data = []
            for i in range(len(data)):
                start_idx = max(0, i - window_size // 2)
                end_idx = min(len(data), i + window_size // 2 + 1)
                window_data = data[start_idx:end_idx]
                averaged_data.append(sum(window_data) / len(window_data))

            return averaged_data

        except Exception as e:
            logger.error(f"移動平均計算失敗: {e}")
            return data.copy()

    @staticmethod
    def calculate_statistics(data: List[float]) -> Dict[str, float]:
        """
        計算數據統計信息

        Args:
            data: 數據列表

        Returns:
            統計信息字典
        """
        try:
            if not data:
                return {
                    'count': 0,
                    'mean': 0.0,
                    'median': 0.0,
                    'std': 0.0,
                    'min': 0.0,
                    'max': 0.0
                }

            count = len(data)
            mean = sum(data) / count
            sorted_data = sorted(data)

            # 中位數
            if count % 2 == 0:
                median = (sorted_data[count//2 - 1] + sorted_data[count//2]) / 2
            else:
                median = sorted_data[count//2]

            # 標準差
            variance = sum((x - mean)**2 for x in data) / count
            std = math.sqrt(variance)

            return {
                'count': count,
                'mean': mean,
                'median': median,
                'std': std,
                'min': min(data),
                'max': max(data)
            }

        except Exception as e:
            logger.error(f"統計計算失敗: {e}")
            return {}


# 便捷函數
def distance_3d(pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
    """便捷函數：計算3D距離"""
    return MathUtils.calculate_distance_3d(pos1, pos2)


def deg2rad(degrees: float) -> float:
    """便捷函數：角度轉弧度"""
    return MathUtils.deg_to_rad(degrees)


def rad2deg(radians: float) -> float:
    """便捷函數：弧度轉角度"""
    return MathUtils.rad_to_deg(radians)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """便捷函數：安全除法"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def normalize_angle_deg(angle_deg: float) -> float:
    """便捷函數：將角度規範化到0-360度"""
    return angle_deg % 360


def normalize_angle_rad(angle_rad: float) -> float:
    """便捷函數：將角度規範化到0-2π弧度"""
    return angle_rad % (2 * math.pi)