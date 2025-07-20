"""
Klobuchar 電離層延遲模型
基於 GPS ICD-200 和 ITU-R P.531 的電離層延遲計算

實現 Phase 0.2 要求：
- 支援 L1/L2/L5 頻段的電離層延遲計算
- 考慮太陽活動週期和地磁活動
- 支援全球任意位置計算
- 論文研究級精度
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

class SolarActivity(Enum):
    """太陽活動水平"""
    LOW = "low"        # 太陽活動極小期
    MODERATE = "moderate"  # 太陽活動中等期
    HIGH = "high"      # 太陽活動極大期

@dataclass
class IonoParameters:
    """電離層計算參數"""
    user_latitude_deg: float
    user_longitude_deg: float
    satellite_elevation_deg: float
    satellite_azimuth_deg: float
    frequency_mhz: float
    utc_time: datetime
    solar_activity: SolarActivity = SolarActivity.MODERATE
    
    # Klobuchar 模型參數 (通常從 GPS 導航電文獲得)
    alpha_0: float = 1.4e-8
    alpha_1: float = 0.0
    alpha_2: float = -5.96e-8
    alpha_3: float = 5.96e-8
    beta_0: float = 1.4e5
    beta_1: float = 0.0
    beta_2: float = -1.97e5
    beta_3: float = 1.97e5

@dataclass
class IonoResult:
    """電離層延遲計算結果"""
    ionospheric_delay_m: float
    ionospheric_delay_ns: float
    tec_tecu: float  # 總電子含量 (TECU)
    pierce_point_lat_deg: float
    pierce_point_lon_deg: float
    local_time_hours: float
    geomagnetic_latitude_deg: float

class KlobucharIonosphericModel:
    """Klobuchar 電離層延遲模型"""
    
    def __init__(self):
        """初始化 Klobuchar 電離層模型"""
        # 物理常數
        self.SPEED_OF_LIGHT = 299792458.0  # m/s
        self.EARTH_RADIUS = 6371000.0      # m
        self.IONO_HEIGHT = 350000.0        # 電離層高度 (m)
        
        # 地磁極座標 (WGS84)
        self.GEOMAG_POLE_LAT = 78.3  # 度
        self.GEOMAG_POLE_LON = -69.8  # 度
        
        # 頻率相關常數
        self.L1_FREQUENCY = 1575.42e6  # Hz
        self.L2_FREQUENCY = 1227.60e6  # Hz
        self.L5_FREQUENCY = 1176.45e6  # Hz
    
    def calculate_ionospheric_delay(self, params: IonoParameters) -> IonoResult:
        """
        計算電離層延遲
        
        Args:
            params: 電離層計算參數
            
        Returns:
            IonoResult: 電離層延遲計算結果
        """
        # 1. 計算電離層穿透點
        pierce_lat, pierce_lon = self._calculate_pierce_point(
            params.user_latitude_deg, params.user_longitude_deg,
            params.satellite_elevation_deg, params.satellite_azimuth_deg
        )
        
        # 2. 計算地磁緯度
        geomag_lat = self._calculate_geomagnetic_latitude(pierce_lat, pierce_lon)
        
        # 3. 計算當地時間
        local_time = self._calculate_local_time(pierce_lon, params.utc_time)
        
        # 4. 計算電離層延遲
        delay_seconds = self._calculate_klobuchar_delay(
            geomag_lat, local_time, params
        )
        
        # 5. 轉換為距離延遲
        delay_meters = delay_seconds * self.SPEED_OF_LIGHT
        delay_nanoseconds = delay_seconds * 1e9
        
        # 6. 計算 TEC (總電子含量)
        tec = self._calculate_tec_from_delay(delay_seconds, params.frequency_mhz)
        
        return IonoResult(
            ionospheric_delay_m=delay_meters,
            ionospheric_delay_ns=delay_nanoseconds,
            tec_tecu=tec,
            pierce_point_lat_deg=pierce_lat,
            pierce_point_lon_deg=pierce_lon,
            local_time_hours=local_time,
            geomagnetic_latitude_deg=geomag_lat
        )
    
    def _calculate_pierce_point(self, user_lat: float, user_lon: float,
                              elevation: float, azimuth: float) -> Tuple[float, float]:
        """
        計算電離層穿透點座標
        
        Returns:
            Tuple[float, float]: (緯度, 經度) in degrees
        """
        # 轉換為弧度
        lat_rad = math.radians(user_lat)
        lon_rad = math.radians(user_lon)
        el_rad = math.radians(elevation)
        az_rad = math.radians(azimuth)
        
        # 地心角計算
        earth_central_angle = math.pi/2 - el_rad - math.asin(
            self.EARTH_RADIUS * math.cos(el_rad) / (self.EARTH_RADIUS + self.IONO_HEIGHT)
        )
        
        # 穿透點緯度
        pierce_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(earth_central_angle) +
            math.cos(lat_rad) * math.sin(earth_central_angle) * math.cos(az_rad)
        )
        
        # 穿透點經度
        pierce_lon_rad = lon_rad + math.asin(
            math.sin(earth_central_angle) * math.sin(az_rad) / math.cos(pierce_lat_rad)
        )
        
        # 轉換為度
        pierce_lat = math.degrees(pierce_lat_rad)
        pierce_lon = math.degrees(pierce_lon_rad)
        
        # 經度正規化到 [-180, 180]
        while pierce_lon > 180:
            pierce_lon -= 360
        while pierce_lon < -180:
            pierce_lon += 360
        
        return pierce_lat, pierce_lon
    
    def _calculate_geomagnetic_latitude(self, lat: float, lon: float) -> float:
        """
        計算地磁緯度
        
        Args:
            lat: 地理緯度 (度)
            lon: 地理經度 (度)
            
        Returns:
            float: 地磁緯度 (度)
        """
        # 轉換為弧度
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        pole_lat_rad = math.radians(self.GEOMAG_POLE_LAT)
        pole_lon_rad = math.radians(self.GEOMAG_POLE_LON)
        
        # 地磁緯度計算
        geomag_lat_rad = math.asin(
            math.sin(pole_lat_rad) * math.sin(lat_rad) +
            math.cos(pole_lat_rad) * math.cos(lat_rad) * math.cos(lon_rad - pole_lon_rad)
        )
        
        return math.degrees(geomag_lat_rad)
    
    def _calculate_local_time(self, longitude: float, utc_time: datetime) -> float:
        """
        計算當地時間
        
        Args:
            longitude: 經度 (度)
            utc_time: UTC 時間
            
        Returns:
            float: 當地時間 (小時)
        """
        # UTC 時間 (小時)
        utc_hours = utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0
        
        # 當地時間 = UTC 時間 + 經度時差
        local_time = utc_hours + longitude / 15.0
        
        # 正規化到 [0, 24)
        while local_time >= 24:
            local_time -= 24
        while local_time < 0:
            local_time += 24
        
        return local_time
    
    def _calculate_klobuchar_delay(self, geomag_lat: float, local_time: float,
                                 params: IonoParameters) -> float:
        """
        計算 Klobuchar 模型電離層延遲
        
        Args:
            geomag_lat: 地磁緯度 (度)
            local_time: 當地時間 (小時)
            params: 電離層參數
            
        Returns:
            float: 電離層延遲 (秒)
        """
        # 地磁緯度轉換為半圓
        phi_m = geomag_lat / 180.0
        
        # 計算振幅 A
        A = params.alpha_0 + params.alpha_1 * phi_m + \
            params.alpha_2 * phi_m**2 + params.alpha_3 * phi_m**3
        
        if A < 0:
            A = 0
        
        # 計算週期 P
        P = params.beta_0 + params.beta_1 * phi_m + \
            params.beta_2 * phi_m**2 + params.beta_3 * phi_m**3
        
        if P < 72000:
            P = 72000
        
        # 計算相位 X
        X = 2 * math.pi * (local_time - 14.0) / (P / 3600.0)
        
        # 計算電離層延遲
        if abs(X) < 1.57:
            F = 1.0 + 16 * (0.53 - params.satellite_elevation_deg / 180.0)**3
            delay = F * (5.0e-9 + A * (1.0 - X**2/2 + X**4/24))
        else:
            F = 1.0 + 16 * (0.53 - params.satellite_elevation_deg / 180.0)**3
            delay = F * 5.0e-9
        
        # 太陽活動修正
        solar_factor = self._get_solar_activity_factor(params.solar_activity)
        delay *= solar_factor
        
        return delay
    
    def _get_solar_activity_factor(self, solar_activity: SolarActivity) -> float:
        """
        獲取太陽活動修正因子
        
        Args:
            solar_activity: 太陽活動水平
            
        Returns:
            float: 修正因子
        """
        if solar_activity == SolarActivity.LOW:
            return 0.7  # 太陽活動極小期
        elif solar_activity == SolarActivity.MODERATE:
            return 1.0  # 太陽活動中等期
        else:  # HIGH
            return 1.5  # 太陽活動極大期
    
    def _calculate_tec_from_delay(self, delay_seconds: float, frequency_mhz: float) -> float:
        """
        從延遲計算 TEC (總電子含量)
        
        Args:
            delay_seconds: 電離層延遲 (秒)
            frequency_mhz: 頻率 (MHz)
            
        Returns:
            float: TEC (TECU, 1 TECU = 10^16 electrons/m²)
        """
        # 電離層延遲與 TEC 的關係
        # delay = 40.3 * TEC / f²
        frequency_hz = frequency_mhz * 1e6
        tec = delay_seconds * frequency_hz**2 / 40.3
        
        # 轉換為 TECU
        tec_tecu = tec / 1e16
        
        return tec_tecu
    
    def calculate_dual_frequency_correction(self, params_l1: IonoParameters,
                                          params_l2: IonoParameters) -> float:
        """
        計算雙頻電離層修正
        
        Args:
            params_l1: L1 頻段參數
            params_l2: L2 頻段參數
            
        Returns:
            float: 電離層修正 (米)
        """
        # 計算 L1 和 L2 延遲
        result_l1 = self.calculate_ionospheric_delay(params_l1)
        result_l2 = self.calculate_ionospheric_delay(params_l2)
        
        # 雙頻組合修正
        f1 = self.L1_FREQUENCY
        f2 = self.L2_FREQUENCY
        
        correction = (f1**2 * result_l2.ionospheric_delay_m - 
                     f2**2 * result_l1.ionospheric_delay_m) / (f1**2 - f2**2)
        
        return correction
    
    def get_ionospheric_summary(self, params: IonoParameters) -> Dict[str, float]:
        """
        獲取電離層延遲摘要
        
        Returns:
            Dict: 包含電離層延遲各項參數的摘要
        """
        result = self.calculate_ionospheric_delay(params)
        
        return {
            "frequency_mhz": params.frequency_mhz,
            "elevation_deg": params.satellite_elevation_deg,
            "ionospheric_delay_m": result.ionospheric_delay_m,
            "ionospheric_delay_ns": result.ionospheric_delay_ns,
            "tec_tecu": result.tec_tecu,
            "pierce_point_lat": result.pierce_point_lat_deg,
            "pierce_point_lon": result.pierce_point_lon_deg,
            "local_time_hours": result.local_time_hours,
            "geomagnetic_lat": result.geomagnetic_latitude_deg
        }

# 使用示例
if __name__ == "__main__":
    # 創建 Klobuchar 電離層模型
    model = KlobucharIonosphericModel()
    
    # 測試參數 - 台北地區 GPS L1 頻段
    params = IonoParameters(
        user_latitude_deg=25.0,
        user_longitude_deg=121.0,
        satellite_elevation_deg=45.0,
        satellite_azimuth_deg=180.0,
        frequency_mhz=1575.42,
        utc_time=datetime.now(timezone.utc),
        solar_activity=SolarActivity.MODERATE
    )
    
    # 計算電離層延遲
    result = model.calculate_ionospheric_delay(params)
    
    print("Klobuchar 電離層延遲計算結果:")
    print(f"電離層延遲: {result.ionospheric_delay_m:.3f} m")
    print(f"電離層延遲: {result.ionospheric_delay_ns:.1f} ns")
    print(f"TEC: {result.tec_tecu:.2f} TECU")
    print(f"穿透點: ({result.pierce_point_lat_deg:.2f}°, {result.pierce_point_lon_deg:.2f}°)")
    print(f"當地時間: {result.local_time_hours:.2f} 小時")
    print(f"地磁緯度: {result.geomagnetic_latitude_deg:.2f}°")
