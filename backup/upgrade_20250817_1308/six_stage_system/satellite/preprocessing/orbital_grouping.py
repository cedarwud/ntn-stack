"""
軌道平面分群器

負責將衛星按軌道平面分組，確保選擇的衛星在軌道空間中均勻分佈。
基於 RAAN (升交點赤經) 和 inclination (傾角) 進行分組。
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
from typing import Dict, List, Tuple
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OrbitalPlaneInfo:
    """軌道平面資訊"""
    plane_id: str
    inclination: float      # 傾角 (度)
    raan: float            # 升交點赤經 (度) 
    satellite_count: int   # 衛星數量
    satellites: List[Dict] # 衛星列表

class OrbitalPlaneGrouper:
    """軌道平面分群器"""
    
    def __init__(self):
        # Starlink 的軌道結構參數
        self.starlink_params = {
            'inclination_groups': [53.0, 70.0, 97.6],  # 主要傾角群
            'shells': {
                'shell1': {'altitude': 550, 'inclination': 53.0, 'planes': 72, 'sats_per_plane': 22},
                'shell2': {'altitude': 540, 'inclination': 53.2, 'planes': 72, 'sats_per_plane': 22}, 
                'shell3': {'altitude': 570, 'inclination': 70.0, 'planes': 36, 'sats_per_plane': 20},
                'shell4': {'altitude': 560, 'inclination': 97.6, 'planes': 6, 'sats_per_plane': 58}
            }
        }
        
        # OneWeb 的軌道結構參數  
        self.oneweb_params = {
            'inclination_groups': [87.4],  # 近極地軌道
            'shells': {
                'shell1': {'altitude': 1200, 'inclination': 87.4, 'planes': 18, 'sats_per_plane': 40}
            }
        }
        
        # 分群容差
        self.inclination_tolerance = 2.0    # 傾角容差 (度)
        self.raan_tolerance = 5.0          # RAAN 容差 (度)
        
        logger.info("初始化軌道平面分群器")
    
    def group_by_orbital_plane(self, satellites: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按軌道平面分組衛星
        
        Args:
            satellites: 衛星列表
            
        Returns:
            按軌道平面分組的衛星字典
        """
        if not satellites:
            return {}
            
        constellation = self._detect_constellation(satellites[0])
        logger.info(f"為 {constellation} 星座的 {len(satellites)} 顆衛星進行軌道平面分群")
        
        if constellation == 'starlink':
            return self._group_starlink_satellites(satellites)
        elif constellation == 'oneweb':
            return self._group_oneweb_satellites(satellites)
        else:
            return self._group_generic_satellites(satellites)
    
    def _detect_constellation(self, satellite: Dict) -> str:
        """檢測星座類型"""
        constellation = satellite.get('constellation', '').lower()
        if not constellation:
            # 從衛星名稱推斷
            name = satellite.get('name', '').upper()
            if 'STARLINK' in name:
                return 'starlink'
            elif 'ONEWEB' in name:
                return 'oneweb'
        return constellation
    
    def _group_starlink_satellites(self, satellites: List[Dict]) -> Dict[str, List[Dict]]:
        """針對 Starlink 的特殊分群邏輯"""
        orbital_planes = defaultdict(list)
        
        for sat in satellites:
            inclination = sat.get('inclination', 53.0)
            raan = sat.get('raan', 0.0)
            
            # 確定所屬的 Shell
            shell_info = self._identify_starlink_shell(inclination, sat.get('altitude', 550))
            
            # 確定軌道平面
            plane_index = self._calculate_starlink_plane_index(raan, shell_info['planes'])
            
            # 生成平面 ID
            plane_id = f"starlink_{shell_info['shell']}_{plane_index:02d}"
            orbital_planes[plane_id].append(sat)
        
        logger.debug(f"Starlink 分為 {len(orbital_planes)} 個軌道平面")
        return dict(orbital_planes)
    
    def _identify_starlink_shell(self, inclination: float, altitude: float) -> Dict:
        """識別 Starlink 的軌道殼層"""
        
        # 基於傾角和高度識別殼層
        for shell_name, params in self.starlink_params['shells'].items():
            if (abs(inclination - params['inclination']) < self.inclination_tolerance and
                abs(altitude - params['altitude']) < 50):  # 50km 高度容差
                return {'shell': shell_name, **params}
        
        # 預設到 shell1
        return {'shell': 'shell1', **self.starlink_params['shells']['shell1']}
    
    def _calculate_starlink_plane_index(self, raan: float, total_planes: int) -> int:
        """計算 Starlink 軌道平面索引"""
        
        # 將 RAAN 正規化到 0-360 度範圍
        normalized_raan = raan % 360.0
        
        # 計算平面間隔
        plane_spacing = 360.0 / total_planes
        
        # 計算最近的平面索引
        plane_index = round(normalized_raan / plane_spacing) % total_planes
        
        return plane_index
    
    def _group_oneweb_satellites(self, satellites: List[Dict]) -> Dict[str, List[Dict]]:
        """針對 OneWeb 的分群邏輯"""
        orbital_planes = defaultdict(list)
        
        for sat in satellites:
            raan = sat.get('raan', 0.0)
            
            # OneWeb 有 18 個軌道平面，間隔 20 度
            plane_index = self._calculate_oneweb_plane_index(raan)
            plane_id = f"oneweb_plane_{plane_index:02d}"
            
            orbital_planes[plane_id].append(sat)
        
        logger.debug(f"OneWeb 分為 {len(orbital_planes)} 個軌道平面")
        return dict(orbital_planes)
    
    def _calculate_oneweb_plane_index(self, raan: float) -> int:
        """計算 OneWeb 軌道平面索引"""
        
        # OneWeb 18 個平面，每個平面間隔 20 度
        plane_spacing = 360.0 / 18
        normalized_raan = raan % 360.0
        plane_index = round(normalized_raan / plane_spacing) % 18
        
        return plane_index
    
    def _group_generic_satellites(self, satellites: List[Dict]) -> Dict[str, List[Dict]]:
        """通用的衛星分群邏輯"""
        orbital_planes = defaultdict(list)
        
        for sat in satellites:
            inclination = sat.get('inclination', 0.0)
            raan = sat.get('raan', 0.0)
            
            # 量化傾角和 RAAN 到格點
            inc_bin = self._quantize_inclination(inclination)
            raan_bin = self._quantize_raan(raan)
            
            plane_id = f"generic_{inc_bin:.1f}_{raan_bin:.1f}"
            orbital_planes[plane_id].append(sat)
        
        logger.debug(f"通用分群: {len(orbital_planes)} 個軌道平面")
        return dict(orbital_planes)
    
    def _quantize_inclination(self, inclination: float) -> float:
        """量化傾角到離散值"""
        # 將傾角量化到 5 度間隔
        bin_size = 5.0
        return round(inclination / bin_size) * bin_size
    
    def _quantize_raan(self, raan: float) -> float:
        """量化 RAAN 到離散值"""
        # 將 RAAN 量化到 30 度間隔
        bin_size = 30.0
        normalized_raan = raan % 360.0
        return round(normalized_raan / bin_size) * bin_size
    
    def analyze_orbital_distribution(self, orbital_groups: Dict[str, List[Dict]]) -> Dict:
        """分析軌道分佈品質"""
        
        analysis = {
            'total_planes': len(orbital_groups),
            'total_satellites': sum(len(sats) for sats in orbital_groups.values()),
            'satellites_per_plane': {},
            'plane_utilization': {},
            'distribution_quality': {}
        }
        
        # 計算每個平面的衛星數量
        for plane_id, satellites in orbital_groups.items():
            analysis['satellites_per_plane'][plane_id] = len(satellites)
        
        # 計算分佈統計
        sat_counts = list(analysis['satellites_per_plane'].values())
        if sat_counts:
            analysis['distribution_quality'] = {
                'mean_sats_per_plane': np.mean(sat_counts),
                'std_sats_per_plane': np.std(sat_counts),
                'min_sats_per_plane': np.min(sat_counts),
                'max_sats_per_plane': np.max(sat_counts),
                'uniformity_score': 1.0 - (np.std(sat_counts) / np.mean(sat_counts))
            }
        
        return analysis
    
    def optimize_plane_selection(self, orbital_groups: Dict[str, List[Dict]], 
                                target_total: int) -> Dict[str, int]:
        """
        優化軌道平面選擇策略
        
        Args:
            orbital_groups: 軌道平面分組
            target_total: 目標總衛星數
            
        Returns:
            每個平面應選擇的衛星數量
        """
        
        plane_allocation = {}
        total_planes = len(orbital_groups)
        
        if total_planes == 0:
            return plane_allocation
        
        # 基礎分配: 平均分配
        base_allocation = target_total // total_planes
        remaining = target_total % total_planes
        
        # 按平面大小排序，優先分配給較大的平面
        sorted_planes = sorted(orbital_groups.items(), 
                              key=lambda x: len(x[1]), reverse=True)
        
        for i, (plane_id, satellites) in enumerate(sorted_planes):
            # 基礎分配
            allocation = min(base_allocation, len(satellites))
            
            # 分配剩餘衛星
            if i < remaining:
                allocation += 1
            
            # 確保不超過該平面的實際衛星數量
            allocation = min(allocation, len(satellites))
            
            plane_allocation[plane_id] = allocation
        
        # 驗證總數
        total_allocated = sum(plane_allocation.values())
        if total_allocated != target_total:
            logger.warning(f"分配總數 {total_allocated} 與目標 {target_total} 不符")
        
        return plane_allocation
    
    def calculate_orbital_diversity_score(self, selected_satellites: List[Dict]) -> float:
        """
        計算軌道多樣性分數
        
        Args:
            selected_satellites: 已選擇的衛星列表
            
        Returns:
            多樣性分數 (0-1，越高越好)
        """
        
        if len(selected_satellites) <= 1:
            return 0.0
        
        # 提取軌道參數
        inclinations = [sat.get('inclination', 0.0) for sat in selected_satellites]
        raans = [sat.get('raan', 0.0) for sat in selected_satellites]
        
        # 計算傾角分散度
        inc_std = np.std(inclinations) if len(set(inclinations)) > 1 else 0.0
        inc_diversity = min(1.0, inc_std / 45.0)  # 正規化到 0-1
        
        # 計算 RAAN 分散度 (考慮圓形特性)
        raan_diversity = self._calculate_circular_diversity(raans)
        
        # 綜合多樣性分數
        diversity_score = 0.6 * inc_diversity + 0.4 * raan_diversity
        
        return diversity_score
    
    def _calculate_circular_diversity(self, angles: List[float]) -> float:
        """計算圓形角度的分散度"""
        
        if len(angles) <= 1:
            return 0.0
        
        # 轉換為單位向量
        radians = [math.radians(angle % 360.0) for angle in angles]
        
        # 計算平均向量
        x_mean = np.mean([math.cos(r) for r in radians])
        y_mean = np.mean([math.sin(r) for r in radians])
        
        # 計算結果向量的長度
        r_length = math.sqrt(x_mean**2 + y_mean**2)
        
        # 分散度分數 (1 - r_length)
        # r_length 接近 0 表示高度分散，接近 1 表示高度集中
        diversity_score = 1.0 - r_length
        
        return diversity_score