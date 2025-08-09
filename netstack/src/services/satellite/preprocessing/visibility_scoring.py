"""
可見性評分器

評估衛星對特定觀測點的可見性品質，考慮仰角、信號強度、
可見時長等多個因素，為衛星選擇提供量化指標。
"""

import logging
import math

# Numpy 替代方案
try:
    import numpy as np
except ImportError:
    class NumpyMock:
        def std(self, data): 
            if not data or len(data) <= 1: return 0.0
            mean_val = sum(data) / len(data)
            variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
            return variance ** 0.5
        def mean(self, data): return sum(data) / len(data) if data else 0.0
        def min(self, data): return min(data) if data else 0.0
        def max(self, data): return max(data) if data else 0.0
        def median(self, data): 
            sorted_data = sorted(data)
            n = len(sorted_data)
            if n == 0: return 0.0
            if n % 2 == 0: return (sorted_data[n//2-1] + sorted_data[n//2]) / 2
            return sorted_data[n//2]
    np = NumpyMock()
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VisibilityMetrics:
    """可見性指標"""
    satellite_id: str
    peak_elevation: float        # 最高仰角 (度)
    visible_duration: float      # 可見時長 (分鐘)
    pass_frequency: float        # 每日過境次數
    signal_quality: float        # 預估信號品質
    orbital_stability: float     # 軌道穩定性
    overall_score: float         # 整體評分

class VisibilityScorer:
    """可見性評分器"""
    
    def __init__(self):
        # 評分權重
        self.score_weights = {
            "peak_elevation": 0.30,      # 最高仰角
            "visible_duration": 0.25,    # 可見時長
            "pass_frequency": 0.20,      # 過境頻率
            "signal_quality": 0.15,      # 信號品質
            "orbital_stability": 0.10    # 軌道穩定性
        }
        
        # 物理常數
        self.earth_radius = 6371.0        # km
        self.gravitational_parameter = 398600.4418  # km³/s²
        
        # 信號模型參數
        self.frequency_ghz = 28.0         # Ka 頻段 (GHz)
        self.tx_power_dbm = 40.0          # 發射功率 (dBm)
        self.antenna_gain_dbi = 30.0      # 天線增益 (dBi)
        
        logger.info("初始化可見性評分器")
    
    def calculate_visibility_score(self, satellite: Dict, observer_lat: float, 
                                 observer_lon: float) -> float:
        """
        計算衛星的可見性評分
        
        Args:
            satellite: 衛星資訊
            observer_lat: 觀測者緯度 (度)
            observer_lon: 觀測者經度 (度)
            
        Returns:
            可見性評分 (0-1)
        """
        
        satellite_id = satellite.get('satellite_id', satellite.get('name', 'UNKNOWN'))
        
        try:
            # 計算各項指標
            metrics = self._calculate_detailed_metrics(satellite, observer_lat, observer_lon)
            
            # 返回正規化後的分數，確保在 0-1 範圍內
            score = max(0.0, min(1.0, metrics.overall_score))
            
            logger.debug(f"{satellite_id} 可見性評分: {score:.3f}")
            
            return score
            
        except Exception as e:
            logger.error(f"計算 {satellite_id} 可見性評分時出錯: {e}")
            return 0.0
    
    def _calculate_detailed_metrics(self, satellite: Dict, observer_lat: float, 
                                  observer_lon: float) -> VisibilityMetrics:
        """計算詳細的可見性指標"""
        
        satellite_id = satellite.get('satellite_id', satellite.get('name', 'UNKNOWN'))
        
        # 軌道參數
        altitude = satellite.get('altitude', 550.0)          # km
        inclination = satellite.get('inclination', 53.0)     # 度
        mean_motion = satellite.get('mean_motion', 15.5)     # 每日圈數
        eccentricity = satellite.get('eccentricity', 0.0)    # 離心率
        
        # 計算各項指標
        peak_elevation = self._calculate_peak_elevation(
            altitude, inclination, observer_lat
        )
        
        visible_duration = self._calculate_visible_duration(
            altitude, observer_lat, peak_elevation
        )
        
        pass_frequency = self._calculate_pass_frequency(
            mean_motion, inclination, observer_lat
        )
        
        signal_quality = self._calculate_signal_quality(
            altitude, peak_elevation
        )
        
        orbital_stability = self._calculate_orbital_stability(
            satellite, eccentricity
        )
        
        # 正規化到 0-1 範圍
        normalized_metrics = {
            'peak_elevation': self._normalize_elevation(peak_elevation),
            'visible_duration': self._normalize_duration(visible_duration),
            'pass_frequency': self._normalize_frequency(pass_frequency),
            'signal_quality': signal_quality,
            'orbital_stability': orbital_stability
        }
        
        # 計算整體評分
        overall_score = sum(
            normalized_metrics[component] * self.score_weights[component]
            for component in normalized_metrics
        )
        
        return VisibilityMetrics(
            satellite_id=satellite_id,
            peak_elevation=peak_elevation,
            visible_duration=visible_duration,
            pass_frequency=pass_frequency,
            signal_quality=signal_quality,
            orbital_stability=orbital_stability,
            overall_score=overall_score
        )
    
    def _calculate_peak_elevation(self, altitude: float, inclination: float, 
                                observer_lat: float) -> float:
        """計算最高仰角"""
        
        # 簡化的最高仰角計算
        # 基於軌道傾角和觀測者緯度的幾何關係
        
        # 衛星軌道半徑
        orbital_radius = self.earth_radius + altitude
        
        # 最小地心距離 (衛星正上方通過時)
        lat_diff = abs(observer_lat - inclination)
        if lat_diff > 90:
            lat_diff = 180 - lat_diff
        
        # 地心角
        central_angle = math.radians(lat_diff)
        
        # 觀測者到衛星的直線距離
        observer_radius = self.earth_radius
        slant_distance = math.sqrt(
            orbital_radius**2 + observer_radius**2 - 
            2 * orbital_radius * observer_radius * math.cos(central_angle)
        )
        
        # 仰角計算 (使用餘弦定理)
        cos_elevation = (
            observer_radius**2 + slant_distance**2 - orbital_radius**2
        ) / (2 * observer_radius * slant_distance)
        
        # 防止數值誤差
        cos_elevation = max(-1.0, min(1.0, cos_elevation))
        elevation_angle = 90.0 - math.degrees(math.acos(cos_elevation))
        
        return max(0.0, elevation_angle)
    
    def _calculate_visible_duration(self, altitude: float, observer_lat: float, 
                                  peak_elevation: float) -> float:
        """計算可見時長 (分鐘)"""
        
        if peak_elevation <= 0:
            return 0.0
        
        # 軌道速度
        orbital_radius = self.earth_radius + altitude
        orbital_velocity = math.sqrt(self.gravitational_parameter / orbital_radius)  # km/s
        
        # 地平線角距離
        min_elevation_rad = math.radians(10.0)  # 10度最小仰角
        
        # 可見弧長的地心角 (簡化計算)
        horizon_angle = 2 * math.acos(self.earth_radius / orbital_radius)
        
        # 考慮最小仰角限制的修正
        elevation_factor = math.sin(math.radians(peak_elevation)) * 0.5
        effective_angle = horizon_angle * elevation_factor
        
        # 弧長距離
        arc_length = effective_angle * orbital_radius
        
        # 可見時長
        visible_time_seconds = arc_length / orbital_velocity
        visible_time_minutes = visible_time_seconds / 60.0
        
        return min(15.0, max(2.0, visible_time_minutes))  # 限制在合理範圍
    
    def _calculate_pass_frequency(self, mean_motion: float, inclination: float, 
                                observer_lat: float) -> float:
        """計算每日過境頻率"""
        
        # 基於軌道傾角和觀測者緯度的過境頻率估算
        
        # 軌道週期 (分鐘)
        orbital_period = 24 * 60 / mean_motion
        
        # 基礎過境次數 (每個軌道週期最多一次)
        base_passes = mean_motion
        
        # 緯度覆蓋因子
        lat_coverage = self._calculate_latitude_coverage_factor(inclination, observer_lat)
        
        # 實際過境次數
        daily_passes = base_passes * lat_coverage
        
        return daily_passes
    
    def _calculate_latitude_coverage_factor(self, inclination: float, 
                                          observer_lat: float) -> float:
        """計算緯度覆蓋因子"""
        
        observer_lat_abs = abs(observer_lat)
        
        # 軌道最大覆蓋緯度
        max_coverage_lat = inclination
        
        if observer_lat_abs <= max_coverage_lat:
            # 觀測者在軌道覆蓋範圍內
            if inclination >= 50:
                # 傾斜軌道，良好覆蓋
                return 1.0 - (observer_lat_abs / max_coverage_lat) * 0.3
            else:
                # 低傾角軌道，覆蓋有限
                return 0.5 + (max_coverage_lat - observer_lat_abs) / max_coverage_lat * 0.5
        else:
            # 觀測者在軌道覆蓋範圍外
            return 0.1
    
    def _calculate_signal_quality(self, altitude: float, peak_elevation: float) -> float:
        """計算信號品質評分"""
        
        if peak_elevation <= 0:
            return 0.0
        
        # 自由空間路徑損耗
        slant_range = altitude / math.sin(math.radians(peak_elevation))
        fspl_db = (20 * math.log10(slant_range) + 
                   20 * math.log10(self.frequency_ghz) + 32.45)
        
        # 接收信號強度
        received_power = self.tx_power_dbm + self.antenna_gain_dbi - fspl_db
        
        # 大氣衰減 (簡化模型)
        if peak_elevation < 30:
            atmospheric_loss = 2.0 * (30 - peak_elevation) / 30  # dB
        else:
            atmospheric_loss = 0.0
        
        effective_power = received_power - atmospheric_loss
        
        # 轉換為品質分數 (0-1)
        # 假設 -120 dBm 為最低可用信號，-70 dBm 為優秀信號
        min_power = -120.0
        max_power = -70.0
        
        if effective_power >= max_power:
            return 1.0
        elif effective_power <= min_power:
            return 0.0
        else:
            return (effective_power - min_power) / (max_power - min_power)
    
    def _calculate_orbital_stability(self, satellite: Dict, eccentricity: float) -> float:
        """計算軌道穩定性評分"""
        
        stability_factors = {}
        
        # 1. TLE 年齡 (越新越好)
        tle_age = satellite.get('tle_age_days', 7.0)
        stability_factors['freshness'] = max(0.0, 1.0 - tle_age / 30.0)
        
        # 2. 軌道離心率 (越圓越穩定)
        stability_factors['circularity'] = max(0.0, 1.0 - eccentricity * 10.0)
        
        # 3. 拖曳係數 (較低表示較穩定)
        drag_coeff = satellite.get('bstar', 0.0)
        stability_factors['drag_resistance'] = max(0.0, 1.0 - abs(drag_coeff) * 10000.0)
        
        # 加權平均
        weights = {'freshness': 0.5, 'circularity': 0.3, 'drag_resistance': 0.2}
        stability_score = sum(
            stability_factors.get(factor, 0.0) * weight
            for factor, weight in weights.items()
        )
        
        return stability_score
    
    def _normalize_elevation(self, elevation: float) -> float:
        """正規化仰角評分"""
        # 90度為滿分，10度為及格線
        return min(1.0, max(0.0, (elevation - 10.0) / 80.0))
    
    def _normalize_duration(self, duration: float) -> float:
        """正規化可見時長評分"""
        # 15分鐘為滿分，5分鐘為及格線
        return min(1.0, max(0.0, (duration - 5.0) / 10.0))
    
    def _normalize_frequency(self, frequency: float) -> float:
        """正規化過境頻率評分"""
        # 15次/天為滿分，5次/天為及格線
        return min(1.0, max(0.0, (frequency - 5.0) / 10.0))
    
    def batch_score_satellites(self, satellites: List[Dict], observer_lat: float, 
                              observer_lon: float) -> List[Tuple[Dict, float]]:
        """批量評分衛星"""
        
        logger.info(f"批量評分 {len(satellites)} 顆衛星")
        
        scored_satellites = []
        
        for satellite in satellites:
            score = self.calculate_visibility_score(satellite, observer_lat, observer_lon)
            scored_satellites.append((satellite, score))
        
        # 按評分排序
        scored_satellites.sort(key=lambda x: x[1], reverse=True)
        
        return scored_satellites
    
    def generate_scoring_report(self, satellites: List[Dict], observer_lat: float, 
                               observer_lon: float) -> Dict:
        """生成評分報告"""
        
        if not satellites:
            return {'error': 'No satellites provided'}
        
        scored_satellites = self.batch_score_satellites(satellites, observer_lat, observer_lon)
        
        scores = [score for _, score in scored_satellites]
        
        report = {
            'total_satellites': len(satellites),
            'observer_location': {'lat': observer_lat, 'lon': observer_lon},
            'score_statistics': {
                'mean_score': np.mean(scores),
                'std_score': np.std(scores),
                'min_score': np.min(scores),
                'max_score': np.max(scores),
                'median_score': np.median(scores)
            },
            'score_distribution': {
                'excellent': sum(1 for s in scores if s >= 0.8),    # >= 0.8
                'good': sum(1 for s in scores if 0.6 <= s < 0.8),   # 0.6-0.8
                'average': sum(1 for s in scores if 0.4 <= s < 0.6), # 0.4-0.6
                'poor': sum(1 for s in scores if s < 0.4)            # < 0.4
            },
            'top_satellites': [
                {
                    'satellite_id': sat.get('satellite_id', sat.get('name', 'UNKNOWN')),
                    'constellation': sat.get('constellation', 'unknown'),
                    'score': score,
                    'rank': i + 1
                }
                for i, (sat, score) in enumerate(scored_satellites[:10])
            ]
        }
        
        return report