"""
相位分散優化器

確保選定的衛星在時間上錯開出現，避免衛星同時升起或落下，
從而提供連續的換手機會和穩定的可見衛星數量。
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
    np = NumpyMock()
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass 
class PhaseInfo:
    """相位資訊"""
    satellite_id: str
    mean_anomaly: float      # 平近點角 (度)
    rise_time: datetime      # 預計升起時間
    set_time: datetime       # 預計落下時間
    visible_duration: float  # 可見時長 (分鐘)
    phase_quality: float     # 相位品質分數

class PhaseDistributionOptimizer:
    """相位分散優化器"""
    
    def __init__(self):
        # 優化參數
        self.min_separation = 20.0       # 最小間隔時間 (秒)
        self.optimal_separation = 30.0   # 最佳間隔時間 (秒)
        self.phase_tolerance = 15.0      # 相位容差 (度)
        
        # NTPU 觀測點
        self.observer_lat = 24.9441667
        self.observer_lon = 121.3713889
        
        logger.info("初始化相位分散優化器")
    
    def optimize_phase_distribution(self, satellites: List[Dict], target_count: int) -> List[Dict]:
        """
        優化衛星的相位分佈
        
        Args:
            satellites: 候選衛星列表
            target_count: 目標衛星數量
            
        Returns:
            相位優化後的衛星列表
        """
        
        if len(satellites) <= target_count:
            return satellites
            
        logger.info(f"對 {len(satellites)} 顆衛星進行相位分散優化，目標選擇 {target_count} 顆")
        
        # Step 1: 計算每顆衛星的相位資訊
        phase_infos = []
        reference_time = datetime.now(timezone.utc)
        
        for sat in satellites:
            phase_info = self._calculate_phase_info(sat, reference_time)
            phase_infos.append(phase_info)
        
        # Step 2: 按升起時間排序
        phase_infos.sort(key=lambda x: x.rise_time)
        
        # Step 3: 貪心算法選擇最佳相位分散
        selected_phases = self._greedy_phase_selection(phase_infos, target_count)
        
        # Step 4: 局部優化
        optimized_phases = self._local_optimization(selected_phases)
        
        # Step 5: 轉換回衛星列表
        selected_satellites = []
        selected_ids = {phase.satellite_id for phase in optimized_phases}
        
        for sat in satellites:
            if sat.get('satellite_id', sat.get('name', '')) in selected_ids:
                selected_satellites.append(sat)
        
        logger.info(f"相位優化完成，選擇 {len(selected_satellites)} 顆衛星")
        
        return selected_satellites
    
    def _calculate_phase_info(self, satellite: Dict, reference_time: datetime) -> PhaseInfo:
        """計算衛星的相位資訊"""
        
        satellite_id = satellite.get('satellite_id', satellite.get('name', 'UNKNOWN'))
        mean_anomaly = satellite.get('mean_anomaly', 0.0)
        
        # 計算軌道週期 (分鐘)
        mean_motion = satellite.get('mean_motion', 15.5)  # 每日圈數
        orbital_period = 24 * 60 / mean_motion  # 分鐘
        
        # 估算下一次升起時間
        rise_time = self._estimate_next_rise_time(satellite, reference_time, orbital_period)
        
        # 估算落下時間
        visible_duration = self._estimate_visible_duration(satellite)
        set_time = rise_time + timedelta(minutes=visible_duration)
        
        # 計算相位品質分數
        phase_quality = self._calculate_phase_quality(satellite, mean_anomaly)
        
        return PhaseInfo(
            satellite_id=satellite_id,
            mean_anomaly=mean_anomaly,
            rise_time=rise_time,
            set_time=set_time,
            visible_duration=visible_duration,
            phase_quality=phase_quality
        )
    
    def _estimate_next_rise_time(self, satellite: Dict, reference_time: datetime, 
                                orbital_period: float) -> datetime:
        """估算下一次升起時間"""
        
        mean_anomaly = satellite.get('mean_anomaly', 0.0)
        
        # 簡化的升起時間估算
        # 基於平近點角推算衛星在軌道中的位置
        
        # 將平近點角轉換為軌道相位 (0-1)
        orbital_phase = (mean_anomaly % 360.0) / 360.0
        
        # 估算到下次過境的時間
        # 假設衛星在相位 0.2-0.8 時可見 (簡化模型)
        if 0.2 <= orbital_phase <= 0.8:
            # 衛星當前可見，計算到下次可見的時間
            next_rise_phase = 1.0 + 0.2  # 下個軌道週期的開始
        else:
            # 衛星當前不可見，計算到本次可見的時間
            if orbital_phase < 0.2:
                next_rise_phase = 0.2
            else:  # orbital_phase > 0.8
                next_rise_phase = 1.0 + 0.2
        
        # 計算時間差
        phase_diff = next_rise_phase - orbital_phase
        if phase_diff < 0:
            phase_diff += 1.0
        
        time_to_rise = phase_diff * orbital_period  # 分鐘
        rise_time = reference_time + timedelta(minutes=time_to_rise)
        
        return rise_time
    
    def _estimate_visible_duration(self, satellite: Dict) -> float:
        """估算可見時長 (分鐘)"""
        
        # 基於軌道高度的簡化估算
        altitude = satellite.get('altitude', 550.0)  # km
        
        # 地球半徑
        earth_radius = 6371.0  # km
        
        # 計算地平線距離
        horizon_distance = math.sqrt(altitude * (altitude + 2 * earth_radius))
        
        # 計算衛星速度 (km/s)
        orbital_velocity = math.sqrt(398600.4418 / (earth_radius + altitude))  # km/s
        
        # 估算可見時長
        # 簡化假設: 衛星以恆定速度穿過可見區域
        visible_arc_length = 2 * horizon_distance * 0.7  # 考慮仰角限制的係數
        visible_duration_seconds = visible_arc_length / orbital_velocity
        visible_duration_minutes = visible_duration_seconds / 60.0
        
        # 限制在合理範圍內
        return max(5.0, min(15.0, visible_duration_minutes))
    
    def _calculate_phase_quality(self, satellite: Dict, mean_anomaly: float) -> float:
        """計算相位品質分數"""
        
        quality_factors = {}
        
        # 1. 軌道穩定性 (基於TLE年齡)
        tle_age = satellite.get('tle_age_days', 7.0)
        quality_factors['stability'] = max(0.0, 1.0 - tle_age / 30.0)
        
        # 2. 軌道高度適中性
        altitude = satellite.get('altitude', 550.0)
        optimal_altitude = 550.0  # Starlink 標準高度
        altitude_factor = 1.0 - abs(altitude - optimal_altitude) / 200.0
        quality_factors['altitude'] = max(0.0, min(1.0, altitude_factor))
        
        # 3. 相位均勻性 (避免相位聚集)
        phase_uniformity = math.sin(math.radians(mean_anomaly * 2)) ** 2
        quality_factors['uniformity'] = phase_uniformity
        
        # 4. 傾角適中性 (避免極地軌道的複雜性)
        inclination = satellite.get('inclination', 53.0)
        if 45.0 <= inclination <= 60.0:
            quality_factors['inclination'] = 1.0
        elif inclination < 45.0:
            quality_factors['inclination'] = inclination / 45.0
        else:  # inclination > 60.0
            quality_factors['inclination'] = max(0.0, 1.0 - (inclination - 60.0) / 30.0)
        
        # 加權平均
        weights = {
            'stability': 0.3,
            'altitude': 0.2,
            'uniformity': 0.3,
            'inclination': 0.2
        }
        
        total_quality = sum(
            quality_factors[factor] * weights[factor]
            for factor in quality_factors
        )
        
        return total_quality
    
    def _greedy_phase_selection(self, phase_infos: List[PhaseInfo], 
                               target_count: int) -> List[PhaseInfo]:
        """貪心算法選擇相位分散最佳的衛星"""
        
        selected = []
        candidates = phase_infos.copy()
        
        # 選擇第一顆衛星 (品質最高的)
        if candidates:
            first_satellite = max(candidates, key=lambda x: x.phase_quality)
            selected.append(first_satellite)
            candidates.remove(first_satellite)
        
        # 迭代選擇剩餘衛星
        while len(selected) < target_count and candidates:
            best_candidate = None
            best_score = -float('inf')
            
            for candidate in candidates:
                # 計算與已選擇衛星的時間間隔品質
                interval_score = self._calculate_interval_score(candidate, selected)
                
                # 綜合分數 = 相位品質 + 間隔品質
                total_score = 0.4 * candidate.phase_quality + 0.6 * interval_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
                candidates.remove(best_candidate)
            else:
                break
        
        return selected
    
    def _calculate_interval_score(self, candidate: PhaseInfo, 
                                 selected: List[PhaseInfo]) -> float:
        """計算時間間隔品質分數"""
        
        if not selected:
            return 1.0
        
        min_interval = float('inf')
        
        for selected_sat in selected:
            # 計算升起時間間隔
            interval = abs((candidate.rise_time - selected_sat.rise_time).total_seconds())
            min_interval = min(min_interval, interval)
        
        # 評分函數: 間隔在最佳範圍內得滿分，過近或過遠扣分
        if min_interval >= self.optimal_separation:
            return 1.0
        elif min_interval >= self.min_separation:
            # 線性插值
            return (min_interval - self.min_separation) / (self.optimal_separation - self.min_separation)
        else:
            # 過近的懲罰
            return 0.1 * (min_interval / self.min_separation)
    
    def _local_optimization(self, selected_phases: List[PhaseInfo]) -> List[PhaseInfo]:
        """局部優化相位分佈"""
        
        # 對於小規模問題，貪心算法已經足夠
        # 這裡可以實現更高級的優化算法，如模擬退火
        
        optimized = selected_phases.copy()
        
        # 按升起時間重新排序
        optimized.sort(key=lambda x: x.rise_time)
        
        return optimized
    
    def evaluate_phase_quality(self, satellites: List[Dict]) -> float:
        """評估相位分佈的整體品質"""
        
        if len(satellites) <= 1:
            return 1.0
        
        # 計算相位資訊
        reference_time = datetime.now(timezone.utc)
        phase_infos = []
        
        for sat in satellites:
            phase_info = self._calculate_phase_info(sat, reference_time)
            phase_infos.append(phase_info)
        
        # 按升起時間排序
        phase_infos.sort(key=lambda x: x.rise_time)
        
        # 計算時間間隔統計
        intervals = []
        for i in range(1, len(phase_infos)):
            interval = (phase_infos[i].rise_time - phase_infos[i-1].rise_time).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return 1.0
        
        # 評估間隔品質
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        min_interval = np.min(intervals)
        
        # 品質指標
        quality_metrics = {}
        
        # 1. 最小間隔是否滿足要求
        quality_metrics['min_interval'] = 1.0 if min_interval >= self.min_separation else min_interval / self.min_separation
        
        # 2. 間隔均勻性
        ideal_interval = self.optimal_separation
        uniformity = 1.0 - min(1.0, std_interval / ideal_interval)
        quality_metrics['uniformity'] = uniformity
        
        # 3. 平均間隔是否接近最佳值
        interval_optimality = 1.0 - min(1.0, abs(mean_interval - ideal_interval) / ideal_interval)
        quality_metrics['optimality'] = interval_optimality
        
        # 綜合品質分數
        weights = {
            'min_interval': 0.5,   # 最重要: 避免衛星過於接近
            'uniformity': 0.3,     # 間隔均勻性
            'optimality': 0.2      # 平均間隔最佳性
        }
        
        total_quality = sum(
            quality_metrics[metric] * weights[metric]
            for metric in quality_metrics
        )
        
        return total_quality
    
    def generate_phase_report(self, satellites: List[Dict]) -> Dict:
        """生成相位分佈報告"""
        
        if not satellites:
            return {'error': 'No satellites provided'}
        
        reference_time = datetime.now(timezone.utc)
        phase_infos = []
        
        for sat in satellites:
            phase_info = self._calculate_phase_info(sat, reference_time)
            phase_infos.append(phase_info)
        
        # 排序
        phase_infos.sort(key=lambda x: x.rise_time)
        
        # 計算統計
        rise_times = [info.rise_time for info in phase_infos]
        intervals = []
        
        for i in range(1, len(rise_times)):
            interval = (rise_times[i] - rise_times[i-1]).total_seconds()
            intervals.append(interval)
        
        report = {
            'total_satellites': len(satellites),
            'reference_time': reference_time.isoformat(),
            'overall_quality': self.evaluate_phase_quality(satellites),
            'phase_details': [
                {
                    'satellite_id': info.satellite_id,
                    'rise_time': info.rise_time.isoformat(),
                    'visible_duration': info.visible_duration,
                    'phase_quality': info.phase_quality
                }
                for info in phase_infos
            ]
        }
        
        if intervals:
            report['interval_statistics'] = {
                'mean_interval_seconds': np.mean(intervals),
                'std_interval_seconds': np.std(intervals),
                'min_interval_seconds': np.min(intervals),
                'max_interval_seconds': np.max(intervals)
            }
        
        return report