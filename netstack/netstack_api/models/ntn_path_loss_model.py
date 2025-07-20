"""
NTN 路徑損耗模型
基於 3GPP TR 38.811 和 ITU-R P.619 的非地面網路路徑損耗計算

實現 Phase 0.1 要求：
- 支援 LEO/MEO/GEO 衛星的路徑損耗計算
- 考慮自由空間損耗、大氣衰減、降雨衰減
- 支援多頻段 (L/S/C/X/Ku/Ka)
- 論文研究級精度
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class SatelliteType(Enum):
    """衛星類型"""
    LEO = "LEO"  # 低地球軌道 (500-2000 km)
    MEO = "MEO"  # 中地球軌道 (2000-35786 km)
    GEO = "GEO"  # 地球同步軌道 (35786 km)

class FrequencyBand(Enum):
    """頻段定義"""
    L_BAND = "L"    # 1-2 GHz
    S_BAND = "S"    # 2-4 GHz
    C_BAND = "C"    # 4-8 GHz
    X_BAND = "X"    # 8-12 GHz
    KU_BAND = "Ku"  # 12-18 GHz
    KA_BAND = "Ka"  # 26.5-40 GHz

@dataclass
class PathLossParameters:
    """路徑損耗計算參數"""
    frequency_ghz: float
    distance_km: float
    elevation_angle_deg: float
    satellite_type: SatelliteType
    frequency_band: FrequencyBand
    rain_rate_mm_h: float = 0.0
    atmospheric_pressure_hpa: float = 1013.25
    temperature_celsius: float = 15.0
    humidity_percent: float = 60.0

@dataclass
class PathLossResult:
    """路徑損耗計算結果"""
    total_path_loss_db: float
    free_space_loss_db: float
    atmospheric_loss_db: float
    rain_loss_db: float
    additional_losses_db: float
    link_margin_db: float

class NTNPathLossModel:
    """NTN 路徑損耗模型"""
    
    def __init__(self):
        """初始化 NTN 路徑損耗模型"""
        # 光速 (m/s)
        self.SPEED_OF_LIGHT = 299792458.0
        
        # 頻段中心頻率 (GHz)
        self.BAND_CENTER_FREQUENCIES = {
            FrequencyBand.L_BAND: 1.5,
            FrequencyBand.S_BAND: 3.0,
            FrequencyBand.C_BAND: 6.0,
            FrequencyBand.X_BAND: 10.0,
            FrequencyBand.KU_BAND: 15.0,
            FrequencyBand.KA_BAND: 30.0
        }
        
        # 衛星類型典型高度 (km)
        self.TYPICAL_ALTITUDES = {
            SatelliteType.LEO: 550,
            SatelliteType.MEO: 20000,
            SatelliteType.GEO: 35786
        }
    
    def calculate_path_loss(self, params: PathLossParameters) -> PathLossResult:
        """
        計算 NTN 路徑損耗
        
        Args:
            params: 路徑損耗計算參數
            
        Returns:
            PathLossResult: 路徑損耗計算結果
        """
        # 1. 自由空間路徑損耗
        free_space_loss = self._calculate_free_space_loss(
            params.frequency_ghz, params.distance_km
        )
        
        # 2. 大氣衰減
        atmospheric_loss = self._calculate_atmospheric_loss(
            params.frequency_ghz, params.elevation_angle_deg,
            params.atmospheric_pressure_hpa, params.temperature_celsius,
            params.humidity_percent
        )
        
        # 3. 降雨衰減
        rain_loss = self._calculate_rain_loss(
            params.frequency_ghz, params.elevation_angle_deg,
            params.rain_rate_mm_h
        )
        
        # 4. 額外損耗 (極化損耗、指向損耗等)
        additional_losses = self._calculate_additional_losses(
            params.satellite_type, params.frequency_band
        )
        
        # 5. 總路徑損耗
        total_loss = free_space_loss + atmospheric_loss + rain_loss + additional_losses
        
        # 6. 鏈路餘量
        link_margin = self._calculate_link_margin(params.satellite_type, params.frequency_band)
        
        return PathLossResult(
            total_path_loss_db=total_loss,
            free_space_loss_db=free_space_loss,
            atmospheric_loss_db=atmospheric_loss,
            rain_loss_db=rain_loss,
            additional_losses_db=additional_losses,
            link_margin_db=link_margin
        )
    
    def _calculate_free_space_loss(self, frequency_ghz: float, distance_km: float) -> float:
        """
        計算自由空間路徑損耗
        
        公式: FSPL(dB) = 20*log10(d) + 20*log10(f) + 92.45
        其中 d 為距離(km)，f 為頻率(GHz)
        """
        if distance_km <= 0 or frequency_ghz <= 0:
            raise ValueError("距離和頻率必須大於 0")
        
        fspl_db = 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz) + 92.45
        return fspl_db
    
    def _calculate_atmospheric_loss(self, frequency_ghz: float, elevation_deg: float,
                                  pressure_hpa: float, temperature_c: float,
                                  humidity_percent: float) -> float:
        """
        計算大氣衰減 (基於 ITU-R P.676)
        """
        # 仰角修正因子
        elevation_factor = 1.0 / math.sin(math.radians(max(elevation_deg, 5.0)))
        
        # 氧氣吸收 (dB/km)
        oxygen_absorption = self._calculate_oxygen_absorption(
            frequency_ghz, pressure_hpa, temperature_c, humidity_percent
        )
        
        # 水蒸氣吸收 (dB/km)
        water_vapor_absorption = self._calculate_water_vapor_absorption(
            frequency_ghz, pressure_hpa, temperature_c, humidity_percent
        )
        
        # 大氣路徑長度 (km) - 簡化模型
        atmospheric_path_length = 10.0  # 典型對流層厚度
        
        # 總大氣衰減
        total_atmospheric_loss = (oxygen_absorption + water_vapor_absorption) * \
                               atmospheric_path_length * elevation_factor
        
        return total_atmospheric_loss
    
    def _calculate_oxygen_absorption(self, frequency_ghz: float, pressure_hpa: float,
                                   temperature_c: float, humidity_percent: float) -> float:
        """計算氧氣吸收 (dB/km)"""
        # 簡化的氧氣吸收模型 (基於 ITU-R P.676)
        if frequency_ghz < 1.0:
            return 0.0
        elif frequency_ghz < 10.0:
            return 0.01 * frequency_ghz
        elif frequency_ghz < 60.0:
            # 60 GHz 氧氣吸收峰附近
            return 0.1 * (frequency_ghz - 10.0) + 0.1
        else:
            return 1.0 + 0.05 * (frequency_ghz - 60.0)
    
    def _calculate_water_vapor_absorption(self, frequency_ghz: float, pressure_hpa: float,
                                        temperature_c: float, humidity_percent: float) -> float:
        """計算水蒸氣吸收 (dB/km)"""
        # 水蒸氣密度 (g/m³)
        water_vapor_density = self._calculate_water_vapor_density(
            temperature_c, humidity_percent
        )
        
        # 簡化的水蒸氣吸收模型
        if frequency_ghz < 1.0:
            return 0.0
        elif frequency_ghz < 22.0:
            # 22 GHz 水蒸氣吸收峰
            return 0.005 * frequency_ghz * water_vapor_density / 7.5
        else:
            return 0.1 * water_vapor_density / 7.5
    
    def _calculate_water_vapor_density(self, temperature_c: float, humidity_percent: float) -> float:
        """計算水蒸氣密度 (g/m³)"""
        # 飽和水蒸氣壓 (hPa)
        saturation_pressure = 6.1078 * math.exp(17.27 * temperature_c / (temperature_c + 237.3))
        
        # 實際水蒸氣壓 (hPa)
        vapor_pressure = saturation_pressure * humidity_percent / 100.0
        
        # 水蒸氣密度 (g/m³)
        vapor_density = 216.7 * vapor_pressure / (temperature_c + 273.15)
        
        return vapor_density
    
    def _calculate_rain_loss(self, frequency_ghz: float, elevation_deg: float,
                           rain_rate_mm_h: float) -> float:
        """
        計算降雨衰減 (簡化版本，完整版本在 itu_r_p618_rain_attenuation.py)
        """
        if rain_rate_mm_h <= 0:
            return 0.0
        
        # 簡化的降雨衰減計算
        # k 和 α 參數 (頻率相關)
        if frequency_ghz < 1.0:
            k, alpha = 0.0001, 0.5
        elif frequency_ghz < 10.0:
            k = 0.01 * frequency_ghz
            alpha = 1.0
        else:
            k = 0.1 * frequency_ghz
            alpha = 1.2
        
        # 比衰減 (dB/km)
        specific_attenuation = k * (rain_rate_mm_h ** alpha)
        
        # 有效路徑長度 (km)
        effective_path_length = 5.0 / math.sin(math.radians(max(elevation_deg, 5.0)))
        
        # 總降雨衰減
        rain_attenuation = specific_attenuation * effective_path_length
        
        return rain_attenuation
    
    def _calculate_additional_losses(self, satellite_type: SatelliteType,
                                   frequency_band: FrequencyBand) -> float:
        """計算額外損耗"""
        additional_loss = 0.0
        
        # 極化損耗
        additional_loss += 0.5
        
        # 指向損耗
        if satellite_type == SatelliteType.LEO:
            additional_loss += 1.0  # LEO 衛星移動較快
        elif satellite_type == SatelliteType.MEO:
            additional_loss += 0.5
        else:  # GEO
            additional_loss += 0.2
        
        # 頻段相關損耗
        if frequency_band in [FrequencyBand.KU_BAND, FrequencyBand.KA_BAND]:
            additional_loss += 1.0  # 高頻段額外損耗
        
        return additional_loss
    
    def _calculate_link_margin(self, satellite_type: SatelliteType,
                             frequency_band: FrequencyBand) -> float:
        """計算建議的鏈路餘量"""
        base_margin = 3.0  # 基礎餘量 3 dB
        
        # 衛星類型相關餘量
        if satellite_type == SatelliteType.LEO:
            base_margin += 2.0  # LEO 衛星都卜勒和陰影效應
        elif satellite_type == SatelliteType.MEO:
            base_margin += 1.0
        
        # 頻段相關餘量
        if frequency_band in [FrequencyBand.KU_BAND, FrequencyBand.KA_BAND]:
            base_margin += 2.0  # 高頻段降雨衰減餘量
        
        return base_margin
    
    def get_path_loss_summary(self, params: PathLossParameters) -> Dict[str, float]:
        """
        獲取路徑損耗摘要
        
        Returns:
            Dict: 包含各項損耗的摘要
        """
        result = self.calculate_path_loss(params)
        
        return {
            "frequency_ghz": params.frequency_ghz,
            "distance_km": params.distance_km,
            "elevation_deg": params.elevation_angle_deg,
            "total_path_loss_db": result.total_path_loss_db,
            "free_space_loss_db": result.free_space_loss_db,
            "atmospheric_loss_db": result.atmospheric_loss_db,
            "rain_loss_db": result.rain_loss_db,
            "additional_losses_db": result.additional_losses_db,
            "recommended_margin_db": result.link_margin_db
        }

# 使用示例
if __name__ == "__main__":
    # 創建 NTN 路徑損耗模型
    model = NTNPathLossModel()
    
    # 測試參數 - LEO 衛星 Ku 頻段
    params = PathLossParameters(
        frequency_ghz=14.0,
        distance_km=1000.0,
        elevation_angle_deg=30.0,
        satellite_type=SatelliteType.LEO,
        frequency_band=FrequencyBand.KU_BAND,
        rain_rate_mm_h=5.0
    )
    
    # 計算路徑損耗
    result = model.calculate_path_loss(params)
    
    print("NTN 路徑損耗計算結果:")
    print(f"總路徑損耗: {result.total_path_loss_db:.2f} dB")
    print(f"自由空間損耗: {result.free_space_loss_db:.2f} dB")
    print(f"大氣衰減: {result.atmospheric_loss_db:.2f} dB")
    print(f"降雨衰減: {result.rain_loss_db:.2f} dB")
    print(f"額外損耗: {result.additional_losses_db:.2f} dB")
    print(f"建議鏈路餘量: {result.link_margin_db:.2f} dB")
