"""
信號品質計算器 - Stage 4模組化組件

職責：
1. 計算RSRP信號強度 (基於Friis公式)
2. 計算大氣衰減 (ITU-R P.618標準)
3. 評估信號品質等級
4. 生成信號強度時間序列
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SignalQualityCalculator:
    """信號品質計算器 - 基於學術級物理公式進行RSRP計算"""
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889):
        """
        初始化信號品質計算器
        
        Args:
            observer_lat: 觀測點緯度
            observer_lon: 觀測點經度
        """
        self.logger = logging.getLogger(f"{__name__}.SignalQualityCalculator")
        
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        
        # 系統參數 (基於3GPP和實際系統規格)
        self.system_parameters = {
            # Starlink參數
            "starlink": {
                "satellite_eirp_dbm": 37.0,  # 37 dBm EIRP
                "frequency_ghz": 12.0,       # Ku頻段下行鏈路
                "antenna_gain_dbi": 35.0,    # 用戶終端天線增益
                "system_noise_temp_k": 150.0 # 系統雜訊溫度
            },
            # OneWeb參數
            "oneweb": {
                "satellite_eirp_dbm": 40.0,  # 40 dBm EIRP
                "frequency_ghz": 13.25,      # Ku頻段下行鏈路
                "antenna_gain_dbi": 38.0,    # 用戶終端天線增益
                "system_noise_temp_k": 140.0 # 系統雜訊溫度
            }
        }
        
        # 物理常數
        self.SPEED_OF_LIGHT = 299792458.0  # m/s
        self.BOLTZMANN_CONSTANT = 1.380649e-23  # J/K
        
        # 計算統計
        self.calculation_statistics = {
            "satellites_calculated": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "average_rsrp_dbm": 0.0,
            "rsrp_range_dbm": {"min": float('inf'), "max": float('-inf')}
        }
        
        self.logger.info("✅ 信號品質計算器初始化完成")
        self.logger.info(f"   觀測點: ({observer_lat:.4f}°N, {observer_lon:.4f}°E)")
        self.logger.info(f"   支持星座: {list(self.system_parameters.keys())}")
    
    def calculate_satellite_signal_quality(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算所有衛星的信號品質
        
        Args:
            satellites: 衛星列表，包含位置時間序列
            
        Returns:
            包含所有衛星信號品質計算結果的字典
        """
        self.logger.info(f"🔢 開始計算 {len(satellites)} 顆衛星的信號品質...")
        
        signal_results = {
            "satellites": [],
            "summary": {
                "total_satellites": len(satellites),
                "successful_calculations": 0,
                "failed_calculations": 0,
                "constellation_breakdown": {}
            }
        }
        
        constellation_counts = {}
        constellation_rsrp_sum = {}
        
        for satellite in satellites:
            self.calculation_statistics["satellites_calculated"] += 1
            
            try:
                satellite_signal = self._calculate_single_satellite_signal(satellite)
                signal_results["satellites"].append(satellite_signal)
                
                # 統計成功計算
                self.calculation_statistics["successful_calculations"] += 1
                signal_results["summary"]["successful_calculations"] += 1
                
                # 統計星座分布
                constellation = satellite.get("constellation", "unknown")
                if constellation not in constellation_counts:
                    constellation_counts[constellation] = 0
                    constellation_rsrp_sum[constellation] = 0.0
                
                constellation_counts[constellation] += 1
                avg_rsrp = satellite_signal.get("signal_metrics", {}).get("average_rsrp_dbm", 0)
                constellation_rsrp_sum[constellation] += avg_rsrp
                
                # 更新RSRP範圍
                if avg_rsrp < self.calculation_statistics["rsrp_range_dbm"]["min"]:
                    self.calculation_statistics["rsrp_range_dbm"]["min"] = avg_rsrp
                if avg_rsrp > self.calculation_statistics["rsrp_range_dbm"]["max"]:
                    self.calculation_statistics["rsrp_range_dbm"]["max"] = avg_rsrp
                
            except Exception as e:
                self.logger.warning(f"衛星 {satellite.get('satellite_id', 'unknown')} 信號計算失敗: {e}")
                self.calculation_statistics["failed_calculations"] += 1
                signal_results["summary"]["failed_calculations"] += 1
                continue
        
        # 計算星座統計
        for constellation, count in constellation_counts.items():
            avg_rsrp = constellation_rsrp_sum[constellation] / count if count > 0 else 0
            signal_results["summary"]["constellation_breakdown"][constellation] = {
                "satellite_count": count,
                "average_rsrp_dbm": avg_rsrp
            }
        
        # 更新全局平均
        if signal_results["summary"]["successful_calculations"] > 0:
            total_rsrp = sum(constellation_rsrp_sum.values())
            self.calculation_statistics["average_rsrp_dbm"] = total_rsrp / signal_results["summary"]["successful_calculations"]
        
        self.logger.info(f"✅ 信號品質計算完成: {signal_results['summary']['successful_calculations']}/{len(satellites)} 成功")
        
        return signal_results
    
    def _calculate_single_satellite_signal(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """計算單顆衛星的信號品質"""
        satellite_id = satellite.get("satellite_id", "unknown")
        constellation = satellite.get("constellation", "unknown").lower()
        
        # 獲取系統參數
        if constellation not in self.system_parameters:
            raise ValueError(f"不支持的星座: {constellation}")
        
        system_params = self.system_parameters[constellation]
        timeseries_positions = satellite.get("timeseries_positions", [])
        
        if not timeseries_positions:
            raise ValueError(f"衛星 {satellite_id} 缺少位置時間序列數據")
        
        # 計算每個時間點的信號品質
        signal_timeseries = []
        rsrp_values = []
        
        for position_point in timeseries_positions:
            try:
                rsrp_dbm = self._calculate_rsrp_at_position(position_point, system_params)
                elevation_deg = position_point.get("elevation_deg", 0)
                range_km = position_point.get("range_km", 0)
                
                signal_point = {
                    "timestamp": position_point.get("timestamp"),
                    "rsrp_dbm": rsrp_dbm,
                    "elevation_deg": elevation_deg,
                    "range_km": range_km,
                    "is_visible": position_point.get("is_visible", False),
                    "signal_quality_grade": self._grade_signal_quality(rsrp_dbm)
                }
                
                # 計算大氣衰減 (ITU-R P.618)
                atmospheric_loss_db = self._calculate_atmospheric_attenuation_p618(
                    elevation_deg, system_params["frequency_ghz"]
                )
                signal_point["atmospheric_loss_db"] = atmospheric_loss_db
                signal_point["rsrp_with_atmosphere_dbm"] = rsrp_dbm - atmospheric_loss_db
                
                signal_timeseries.append(signal_point)
                rsrp_values.append(rsrp_dbm)
                
            except Exception as e:
                self.logger.debug(f"位置點信號計算失敗: {e}")
                continue
        
        if not rsrp_values:
            raise ValueError(f"衛星 {satellite_id} 所有位置點信號計算失敗")
        
        # 計算統計指標
        signal_metrics = {
            "average_rsrp_dbm": sum(rsrp_values) / len(rsrp_values),
            "max_rsrp_dbm": max(rsrp_values),
            "min_rsrp_dbm": min(rsrp_values),
            "rsrp_std_deviation": self._calculate_std_deviation(rsrp_values),
            "signal_stability_score": self._calculate_stability_score(rsrp_values),
            "visible_points_count": sum(1 for p in signal_timeseries if p["is_visible"]),
            "total_points_count": len(signal_timeseries)
        }
        
        return {
            "satellite_id": satellite_id,
            "constellation": constellation,
            "signal_timeseries": signal_timeseries,
            "signal_metrics": signal_metrics,
            "system_parameters": system_params
        }
    
    def _calculate_rsrp_at_position(self, position_point: Dict[str, Any], system_params: Dict[str, Any]) -> float:
        """
        基於Friis公式計算特定位置的RSRP
        
        Friis公式: Pr = Pt + Gt + Gr - PL
        其中 PL = 20*log10(4*π*d/λ)
        """
        range_km = position_point.get("range_km", 0)
        elevation_deg = position_point.get("elevation_deg", 0)
        
        if range_km <= 0 or elevation_deg < 5:  # 低於5度視為不可見
            return -140.0  # 極低信號強度
        
        # Friis公式計算
        range_m = range_km * 1000.0
        frequency_hz = system_params["frequency_ghz"] * 1e9
        wavelength_m = self.SPEED_OF_LIGHT / frequency_hz
        
        # 自由空間路徑損耗
        path_loss_db = 20 * math.log10(4 * math.pi * range_m / wavelength_m)
        
        # RSRP計算: EIRP + 接收天線增益 - 路徑損耗
        satellite_eirp_dbm = system_params["satellite_eirp_dbm"]
        receiver_gain_dbi = system_params["antenna_gain_dbi"]
        
        rsrp_dbm = satellite_eirp_dbm + receiver_gain_dbi - path_loss_db
        
        # 考慮仰角影響 (低仰角有額外損耗)
        if elevation_deg < 20:
            elevation_loss = (20 - elevation_deg) * 0.2  # 每度0.2dB額外損耗
            rsrp_dbm -= elevation_loss
        
        return rsrp_dbm
    
    def _calculate_atmospheric_attenuation_p618(self, elevation_deg: float, frequency_ghz: float) -> float:
        """
        基於ITU-R P.618計算大氣衰減
        
        Args:
            elevation_deg: 仰角 (度)
            frequency_ghz: 頻率 (GHz)
            
        Returns:
            大氣衰減 (dB)
        """
        if elevation_deg <= 0:
            return 100.0  # 地平線以下，極大衰減
        
        # ITU-R P.618 模型簡化版
        # 氣體衰減 (主要是水蒸氣和氧氣)
        
        # 水蒸氣密度 (g/m³) - 使用典型值
        water_vapor_density = 7.5  # 台灣地區典型值
        
        # 氧氣衰減係數 (dB/km)
        oxygen_attenuation = 0.0067 * frequency_ghz**0.8
        
        # 水蒸氣衰減係數 (dB/km)
        water_vapor_attenuation = 0.05 * water_vapor_density * (frequency_ghz / 10)**1.6
        
        # 總衰減係數
        total_attenuation_per_km = oxygen_attenuation + water_vapor_attenuation
        
        # 有效大氣厚度 (考慮仰角)
        if elevation_deg >= 90:
            atmospheric_path_km = 8.0  # 垂直大氣厚度約8km
        else:
            # 使用簡化的secant近似
            elevation_rad = math.radians(elevation_deg)
            atmospheric_path_km = 8.0 / math.sin(elevation_rad)
            
            # 限制最大路徑長度
            atmospheric_path_km = min(atmospheric_path_km, 40.0)
        
        total_atmospheric_loss = total_attenuation_per_km * atmospheric_path_km
        
        # 考慮散射損耗 (高頻時更顯著)
        scattering_loss = 0.001 * frequency_ghz**1.2 * atmospheric_path_km
        
        return total_atmospheric_loss + scattering_loss
    
    def _grade_signal_quality(self, rsrp_dbm: float) -> str:
        """
        基於RSRP值評估信號品質等級
        
        Args:
            rsrp_dbm: RSRP值 (dBm)
            
        Returns:
            信號品質等級字符串
        """
        if rsrp_dbm >= -80:
            return "Excellent"
        elif rsrp_dbm >= -90:
            return "Good"
        elif rsrp_dbm >= -100:
            return "Fair"
        elif rsrp_dbm >= -110:
            return "Poor"
        else:
            return "Very_Poor"
    
    def _calculate_std_deviation(self, values: List[float]) -> float:
        """計算標準差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    def _calculate_stability_score(self, rsrp_values: List[float]) -> float:
        """
        計算信號穩定性分數 (0-100)
        基於RSRP變異程度
        """
        if len(rsrp_values) < 2:
            return 100.0
        
        std_dev = self._calculate_std_deviation(rsrp_values)
        
        # 標準差越小，穩定性越高
        if std_dev <= 2.0:
            return 100.0
        elif std_dev <= 5.0:
            return 100.0 - (std_dev - 2.0) * 10
        elif std_dev <= 10.0:
            return 70.0 - (std_dev - 5.0) * 6
        else:
            return max(0.0, 40.0 - (std_dev - 10.0) * 2)
    
    def calculate_constellation_performance_comparison(self, signal_results: Dict[str, Any]) -> Dict[str, Any]:
        """計算星座間性能比較"""
        constellation_performance = {}
        
        for satellite_result in signal_results.get("satellites", []):
            constellation = satellite_result.get("constellation")
            signal_metrics = satellite_result.get("signal_metrics", {})
            
            if constellation not in constellation_performance:
                constellation_performance[constellation] = {
                    "satellite_count": 0,
                    "total_avg_rsrp": 0.0,
                    "total_stability": 0.0,
                    "max_rsrp": float('-inf'),
                    "min_rsrp": float('inf')
                }
            
            perf = constellation_performance[constellation]
            perf["satellite_count"] += 1
            perf["total_avg_rsrp"] += signal_metrics.get("average_rsrp_dbm", 0)
            perf["total_stability"] += signal_metrics.get("signal_stability_score", 0)
            perf["max_rsrp"] = max(perf["max_rsrp"], signal_metrics.get("max_rsrp_dbm", 0))
            perf["min_rsrp"] = min(perf["min_rsrp"], signal_metrics.get("min_rsrp_dbm", 0))
        
        # 計算平均值
        for constellation, perf in constellation_performance.items():
            if perf["satellite_count"] > 0:
                perf["average_rsrp_dbm"] = perf["total_avg_rsrp"] / perf["satellite_count"]
                perf["average_stability_score"] = perf["total_stability"] / perf["satellite_count"]
                
                # 清理臨時字段
                del perf["total_avg_rsrp"]
                del perf["total_stability"]
        
        return constellation_performance
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return self.calculation_statistics.copy()