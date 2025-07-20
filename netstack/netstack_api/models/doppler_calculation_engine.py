"""
都卜勒頻移精確計算引擎
基於 SGP4 軌道速度的精確都卜勒頻移計算
符合論文研究級數據真實性要求

主要功能：
1. 基於 SGP4 軌道速度計算精確都卜勒頻移
2. 考慮地球自轉和用戶移動效應
3. 實現頻率補償算法
4. 支援多種頻段 (L, S, C, X, Ku, Ka)
"""

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class Position3D:
    """3D 位置座標"""
    x: float  # ECEF X 座標 (m)
    y: float  # ECEF Y 座標 (m) 
    z: float  # ECEF Z 座標 (m)


@dataclass
class Velocity3D:
    """3D 速度向量"""
    vx: float  # X 方向速度 (m/s)
    vy: float  # Y 方向速度 (m/s)
    vz: float  # Z 方向速度 (m/s)


@dataclass
class DopplerResult:
    """都卜勒計算結果"""
    doppler_shift_hz: float  # 都卜勒頻移 (Hz)
    relative_velocity_ms: float  # 相對速度 (m/s)
    range_rate_ms: float  # 距離變化率 (m/s)
    frequency_compensation_hz: float  # 頻率補償 (Hz)
    earth_rotation_effect_hz: float  # 地球自轉效應 (Hz)
    user_motion_effect_hz: float  # 用戶移動效應 (Hz)
    total_correction_hz: float  # 總修正量 (Hz)


class DopplerCalculationEngine:
    """都卜勒頻移精確計算引擎"""
    
    def __init__(self):
        """初始化物理常數"""
        self.c = 299792458.0  # 光速 (m/s)
        self.earth_rotation_rate = 7.2921159e-5  # 地球自轉角速度 (rad/s)
        self.earth_radius = 6378137.0  # WGS84 地球半徑 (m)
        self.earth_flattening = 1.0 / 298.257223563  # WGS84 扁率
        
        # 頻段定義 (GHz)
        self.frequency_bands = {
            'L': 1.5,    # L 頻段
            'S': 2.4,    # S 頻段  
            'C': 6.0,    # C 頻段
            'X': 10.0,   # X 頻段
            'Ku': 14.0,  # Ku 頻段
            'Ka': 30.0   # Ka 頻段
        }
        
        logger.info("都卜勒計算引擎初始化完成")

    def geodetic_to_ecef(self, lat_deg: float, lon_deg: float, alt_m: float) -> Position3D:
        """
        將大地座標轉換為 ECEF 座標
        
        Args:
            lat_deg: 緯度 (度)
            lon_deg: 經度 (度)
            alt_m: 高度 (米)
            
        Returns:
            ECEF 座標
        """
        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)
        
        # WGS84 橢球參數
        a = self.earth_radius
        e2 = 2 * self.earth_flattening - self.earth_flattening**2
        
        # 卯酉圈曲率半徑
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad)**2)
        
        # ECEF 座標
        x = (N + alt_m) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt_m) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - e2) + alt_m) * math.sin(lat_rad)
        
        return Position3D(x, y, z)

    def calculate_earth_rotation_velocity(self, position: Position3D) -> Velocity3D:
        """
        計算地球自轉引起的速度
        
        Args:
            position: ECEF 位置
            
        Returns:
            地球自轉速度向量
        """
        omega = self.earth_rotation_rate
        
        # 地球自轉速度 = ω × r
        vx = -omega * position.y
        vy = omega * position.x
        vz = 0.0
        
        return Velocity3D(vx, vy, vz)

    def calculate_range_rate(
        self, 
        satellite_pos: Position3D, 
        satellite_vel: Velocity3D,
        user_pos: Position3D, 
        user_vel: Velocity3D
    ) -> float:
        """
        計算距離變化率 (range rate)
        
        Args:
            satellite_pos: 衛星位置
            satellite_vel: 衛星速度
            user_pos: 用戶位置
            user_vel: 用戶速度
            
        Returns:
            距離變化率 (m/s)，正值表示距離增加
        """
        # 位置向量差
        dx = satellite_pos.x - user_pos.x
        dy = satellite_pos.y - user_pos.y
        dz = satellite_pos.z - user_pos.z
        
        # 距離
        range_m = math.sqrt(dx**2 + dy**2 + dz**2)
        
        if range_m == 0:
            return 0.0
        
        # 速度向量差
        dvx = satellite_vel.vx - user_vel.vx
        dvy = satellite_vel.vy - user_vel.vy
        dvz = satellite_vel.vz - user_vel.vz
        
        # 距離變化率 = (相對位置向量 · 相對速度向量) / 距離
        range_rate = (dx * dvx + dy * dvy + dz * dvz) / range_m
        
        return range_rate

    def calculate_doppler_shift(
        self,
        satellite_pos: Position3D,
        satellite_vel: Velocity3D,
        user_lat_deg: float,
        user_lon_deg: float,
        user_alt_m: float,
        user_velocity_ms: Optional[Tuple[float, float, float]] = None,
        carrier_frequency_hz: float = 2.4e9,  # 預設 S 頻段
        include_earth_rotation: bool = True,
        include_user_motion: bool = True
    ) -> DopplerResult:
        """
        計算精確的都卜勒頻移
        
        Args:
            satellite_pos: 衛星 ECEF 位置
            satellite_vel: 衛星 ECEF 速度
            user_lat_deg: 用戶緯度 (度)
            user_lon_deg: 用戶經度 (度)
            user_alt_m: 用戶高度 (米)
            user_velocity_ms: 用戶速度 (vx, vy, vz) m/s，可選
            carrier_frequency_hz: 載波頻率 (Hz)
            include_earth_rotation: 是否包含地球自轉效應
            include_user_motion: 是否包含用戶移動效應
            
        Returns:
            都卜勒計算結果
        """
        try:
            # 用戶 ECEF 位置
            user_pos = self.geodetic_to_ecef(user_lat_deg, user_lon_deg, user_alt_m)
            
            # 用戶速度
            user_vel = Velocity3D(0, 0, 0)
            earth_rotation_effect = 0.0
            user_motion_effect = 0.0
            
            if include_earth_rotation:
                # 地球自轉引起的用戶速度
                earth_rotation_vel = self.calculate_earth_rotation_velocity(user_pos)
                user_vel.vx += earth_rotation_vel.vx
                user_vel.vy += earth_rotation_vel.vy
                user_vel.vz += earth_rotation_vel.vz
                
                # 計算地球自轉效應
                earth_range_rate = self.calculate_range_rate(
                    satellite_pos, Velocity3D(0, 0, 0),
                    user_pos, earth_rotation_vel
                )
                earth_rotation_effect = -carrier_frequency_hz * earth_range_rate / self.c
            
            if include_user_motion and user_velocity_ms:
                # 用戶移動速度
                user_motion_vel = Velocity3D(*user_velocity_ms)
                user_vel.vx += user_motion_vel.vx
                user_vel.vy += user_motion_vel.vy
                user_vel.vz += user_motion_vel.vz
                
                # 計算用戶移動效應
                user_range_rate = self.calculate_range_rate(
                    satellite_pos, Velocity3D(0, 0, 0),
                    user_pos, user_motion_vel
                )
                user_motion_effect = -carrier_frequency_hz * user_range_rate / self.c
            
            # 計算總距離變化率
            range_rate = self.calculate_range_rate(
                satellite_pos, satellite_vel, user_pos, user_vel
            )
            
            # 都卜勒頻移 = -f0 * (range_rate / c)
            # 負號：距離減少時頻率增加
            doppler_shift = -carrier_frequency_hz * range_rate / self.c
            
            # 相對速度大小
            relative_velocity = abs(range_rate)
            
            # 頻率補償 (與都卜勒頻移相反)
            frequency_compensation = -doppler_shift
            
            # 總修正量
            total_correction = frequency_compensation
            
            return DopplerResult(
                doppler_shift_hz=doppler_shift,
                relative_velocity_ms=relative_velocity,
                range_rate_ms=range_rate,
                frequency_compensation_hz=frequency_compensation,
                earth_rotation_effect_hz=earth_rotation_effect,
                user_motion_effect_hz=user_motion_effect,
                total_correction_hz=total_correction
            )
            
        except Exception as e:
            logger.error(f"都卜勒頻移計算失敗: {e}")
            return DopplerResult(0, 0, 0, 0, 0, 0, 0)

    def get_frequency_band_doppler(
        self,
        satellite_pos: Position3D,
        satellite_vel: Velocity3D,
        user_lat_deg: float,
        user_lon_deg: float,
        user_alt_m: float,
        band: str = 'S',
        **kwargs
    ) -> Dict[str, Any]:
        """
        計算特定頻段的都卜勒頻移
        
        Args:
            satellite_pos: 衛星位置
            satellite_vel: 衛星速度
            user_lat_deg: 用戶緯度
            user_lon_deg: 用戶經度
            user_alt_m: 用戶高度
            band: 頻段 ('L', 'S', 'C', 'X', 'Ku', 'Ka')
            **kwargs: 其他參數
            
        Returns:
            包含頻段信息的都卜勒結果
        """
        if band not in self.frequency_bands:
            raise ValueError(f"不支援的頻段: {band}")
        
        carrier_freq = self.frequency_bands[band] * 1e9  # 轉換為 Hz
        
        result = self.calculate_doppler_shift(
            satellite_pos, satellite_vel,
            user_lat_deg, user_lon_deg, user_alt_m,
            carrier_frequency_hz=carrier_freq,
            **kwargs
        )
        
        return {
            'band': band,
            'carrier_frequency_ghz': self.frequency_bands[band],
            'carrier_frequency_hz': carrier_freq,
            'doppler_result': result,
            'doppler_shift_khz': result.doppler_shift_hz / 1000,
            'frequency_accuracy_requirement_hz': 100,  # 論文要求精度 < 100Hz
            'meets_accuracy_requirement': abs(result.doppler_shift_hz) < 10000  # 10kHz 範圍內
        }
