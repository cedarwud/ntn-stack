"""
🌍 時空錯置優化器 (Spatiotemporal Diversity Optimizer)
==================================================

目的：實現衛星時空錯置篩選，確保在完整軌道週期內
持續維持指定數量的可見衛星。

核心概念：
1. 時間錯置：選擇不同軌道相位的衛星，確保連續覆蓋
2. 空間錯置：選擇不同軌道面的衛星，增加空間多樣性
3. 軌道週期驗證：確保完整軌道週期內的覆蓋連續性

作者：NTN Stack Development Team
日期：2025-01-04
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class OrbitalPhaseInfo:
    """軌道相位信息"""
    satellite_id: str
    constellation: str
    inclination: float  # 軌道傾角
    raan: float  # 升交點赤經 (Right Ascension of Ascending Node)
    mean_anomaly: float  # 平均近點角
    period_minutes: float  # 軌道週期（分鐘）
    visible_windows: List[Tuple[float, float]]  # 可見時間窗口 [(start, end), ...]
    
@dataclass
class SpatiotemporalCoverage:
    """時空覆蓋分析結果"""
    time_coverage_ratio: float  # 時間覆蓋率 (0-1)
    min_visible_satellites: int  # 最小可見衛星數
    max_visible_satellites: int  # 最大可見衛星數
    average_visible_satellites: float  # 平均可見衛星數
    coverage_gaps: List[Tuple[float, float]]  # 覆蓋空隙 [(start, end), ...]
    phase_diversity_score: float  # 相位多樣性得分

class SpatiotemporalDiversityOptimizer:
    """時空錯置優化器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化時空錯置優化器"""
        self.config = config or {}
        
        # 覆蓋目標配置
        self.coverage_targets = {
            'starlink': {
                'min_visible': 10,  # 最少可見衛星數
                'max_visible': 15,  # 最多可見衛星數
                'elevation_threshold': 5.0,  # 仰角閾值（度）
                'orbit_period': 93.63,  # 軌道週期（分鐘）
            },
            'oneweb': {
                'min_visible': 3,
                'max_visible': 6,
                'elevation_threshold': 10.0,
                'orbit_period': 109.64,
            }
        }
        
        # 優化參數
        self.phase_bins = 12  # 將軌道週期分為12個相位區間
        self.raan_bins = 8  # 將RAAN分為8個區間
        self.time_resolution = 30  # 時間解析度（秒）
        
        logger.info("✅ 時空錯置優化器初始化完成")
        
    def select_spatiotemporal_diverse_pool(
        self, 
        candidates: List[Dict],
        constellation: str,
        target_pool_size: int
    ) -> Tuple[List[Dict], SpatiotemporalCoverage]:
        """
        選擇時空錯置的衛星池
        
        Args:
            candidates: 候選衛星列表
            constellation: 星座類型 ('starlink' or 'oneweb')
            target_pool_size: 目標衛星池大小
            
        Returns:
            (selected_satellites, coverage_analysis)
        """
        logger.info(f"🛰️ 開始時空錯置篩選: {constellation}, 目標數量: {target_pool_size}")
        
        # 1. 提取軌道相位信息
        phase_info_list = self._extract_orbital_phases(candidates, constellation)
        
        # 2. 計算相位分佈
        phase_distribution = self._calculate_phase_distribution(phase_info_list)
        
        # 3. 選擇時空錯置的衛星
        selected_indices = self._select_diverse_satellites(
            phase_info_list,
            phase_distribution,
            target_pool_size,
            constellation
        )
        
        # 4. 驗證覆蓋連續性
        selected_satellites = [candidates[i] for i in selected_indices]
        coverage_analysis = self._analyze_coverage_continuity(
            selected_satellites,
            constellation
        )
        
        # 5. 如果覆蓋不足，進行補充選擇
        if coverage_analysis.time_coverage_ratio < 0.95:
            selected_satellites = self._supplement_coverage_gaps(
                selected_satellites,
                candidates,
                coverage_analysis,
                constellation,
                target_pool_size
            )
            # 重新分析覆蓋
            coverage_analysis = self._analyze_coverage_continuity(
                selected_satellites,
                constellation
            )
        
        logger.info(f"✅ 時空錯置篩選完成: 選擇 {len(selected_satellites)} 顆衛星")
        logger.info(f"   覆蓋率: {coverage_analysis.time_coverage_ratio:.1%}")
        logger.info(f"   可見衛星數: {coverage_analysis.min_visible_satellites}-{coverage_analysis.max_visible_satellites}")
        logger.info(f"   相位多樣性: {coverage_analysis.phase_diversity_score:.2f}")
        
        return selected_satellites, coverage_analysis
        
    def _extract_orbital_phases(self, candidates: List[Dict], constellation: str) -> List[OrbitalPhaseInfo]:
        """提取軌道相位信息"""
        phase_info_list = []
        
        for sat in candidates:
            # 從TLE數據提取軌道要素
            tle_data = sat.get('tle_data', {})
            
            phase_info = OrbitalPhaseInfo(
                satellite_id=sat.get('satellite_id', ''),
                constellation=constellation,
                inclination=tle_data.get('inclination', 0),
                raan=tle_data.get('raan', 0),
                mean_anomaly=tle_data.get('mean_anomaly', 0),
                period_minutes=self.coverage_targets[constellation]['orbit_period'],
                visible_windows=self._extract_visibility_windows(sat)
            )
            phase_info_list.append(phase_info)
            
        return phase_info_list
        
    def _extract_visibility_windows(self, satellite: Dict) -> List[Tuple[float, float]]:
        """提取衛星可見時間窗口"""
        windows = []
        position_timeseries = satellite.get('position_timeseries', [])
        
        if not position_timeseries:
            return windows
            
        # 找出連續可見的時間段
        in_window = False
        window_start = None
        
        for i, pos in enumerate(position_timeseries):
            time_offset = pos.get('time_offset_seconds', i * 30)
            is_visible = pos.get('is_visible', False)
            
            if is_visible and not in_window:
                # 開始新的可見窗口
                window_start = time_offset
                in_window = True
            elif not is_visible and in_window:
                # 結束當前可見窗口
                windows.append((window_start, time_offset))
                in_window = False
                
        # 處理最後一個窗口
        if in_window and window_start is not None:
            last_time = position_timeseries[-1].get('time_offset_seconds', len(position_timeseries) * 30)
            windows.append((window_start, last_time))
            
        return windows
        
    def _calculate_phase_distribution(self, phase_info_list: List[OrbitalPhaseInfo]) -> Dict:
        """計算相位分佈"""
        distribution = {
            'mean_anomaly_bins': {i: [] for i in range(self.phase_bins)},
            'raan_bins': {i: [] for i in range(self.raan_bins)},
            'coverage_matrix': np.zeros((self.phase_bins, self.raan_bins))
        }
        
        for i, phase_info in enumerate(phase_info_list):
            # 計算平均近點角所在區間
            ma_bin = int((phase_info.mean_anomaly % 360) / (360 / self.phase_bins))
            ma_bin = min(ma_bin, self.phase_bins - 1)
            distribution['mean_anomaly_bins'][ma_bin].append(i)
            
            # 計算RAAN所在區間
            raan_bin = int((phase_info.raan % 360) / (360 / self.raan_bins))
            raan_bin = min(raan_bin, self.raan_bins - 1)
            distribution['raan_bins'][raan_bin].append(i)
            
            # 更新覆蓋矩陣
            distribution['coverage_matrix'][ma_bin][raan_bin] += 1
            
        return distribution
        
    def _select_diverse_satellites(
        self,
        phase_info_list: List[OrbitalPhaseInfo],
        phase_distribution: Dict,
        target_size: int,
        constellation: str
    ) -> List[int]:
        """選擇時空多樣化的衛星"""
        selected_indices = []
        selected_set = set()
        
        # 優先從每個相位區間選擇衛星，確保時間錯置
        satellites_per_bin = max(1, target_size // self.phase_bins)
        
        # 第一輪：從每個平均近點角區間選擇
        for ma_bin in range(self.phase_bins):
            bin_satellites = phase_distribution['mean_anomaly_bins'][ma_bin]
            if not bin_satellites:
                continue
                
            # 按可見時間長度排序
            bin_satellites_sorted = sorted(
                bin_satellites,
                key=lambda i: len(phase_info_list[i].visible_windows),
                reverse=True
            )
            
            # 選擇該區間最好的衛星
            for sat_idx in bin_satellites_sorted[:satellites_per_bin]:
                if sat_idx not in selected_set:
                    selected_indices.append(sat_idx)
                    selected_set.add(sat_idx)
                    
                if len(selected_indices) >= target_size:
                    break
                    
            if len(selected_indices) >= target_size:
                break
                
        # 第二輪：如果數量不足，從不同RAAN區間補充
        if len(selected_indices) < target_size:
            for raan_bin in range(self.raan_bins):
                bin_satellites = phase_distribution['raan_bins'][raan_bin]
                
                for sat_idx in bin_satellites:
                    if sat_idx not in selected_set:
                        selected_indices.append(sat_idx)
                        selected_set.add(sat_idx)
                        
                    if len(selected_indices) >= target_size:
                        break
                        
                if len(selected_indices) >= target_size:
                    break
                    
        # 第三輪：如果還是不足，選擇剩餘最佳的衛星
        if len(selected_indices) < target_size:
            remaining = [i for i in range(len(phase_info_list)) if i not in selected_set]
            remaining_sorted = sorted(
                remaining,
                key=lambda i: len(phase_info_list[i].visible_windows),
                reverse=True
            )
            
            for sat_idx in remaining_sorted:
                selected_indices.append(sat_idx)
                if len(selected_indices) >= target_size:
                    break
                    
        return selected_indices[:target_size]
        
    def _analyze_coverage_continuity(
        self,
        satellites: List[Dict],
        constellation: str
    ) -> SpatiotemporalCoverage:
        """分析覆蓋連續性"""
        orbit_period = self.coverage_targets[constellation]['orbit_period']
        min_visible_target = self.coverage_targets[constellation]['min_visible']
        
        # 計算完整軌道週期的時間點
        time_points = int(orbit_period * 60 / self.time_resolution)  # 週期內的時間點數
        visible_count = np.zeros(time_points)
        
        # 統計每個時間點的可見衛星數
        for sat in satellites:
            position_timeseries = sat.get('position_timeseries', [])
            
            for pos in position_timeseries[:time_points]:
                if pos.get('is_visible', False):
                    time_idx = pos.get('time_offset_seconds', 0) // self.time_resolution
                    if time_idx < time_points:
                        visible_count[time_idx] += 1
                        
        # 計算覆蓋統計
        coverage_ratio = np.sum(visible_count >= min_visible_target) / len(visible_count)
        min_visible = int(np.min(visible_count))
        max_visible = int(np.max(visible_count))
        avg_visible = float(np.mean(visible_count))
        
        # 找出覆蓋空隙
        coverage_gaps = []
        in_gap = False
        gap_start = None
        
        for i, count in enumerate(visible_count):
            if count < min_visible_target and not in_gap:
                gap_start = i * self.time_resolution
                in_gap = True
            elif count >= min_visible_target and in_gap:
                gap_end = i * self.time_resolution
                coverage_gaps.append((gap_start, gap_end))
                in_gap = False
                
        if in_gap:
            coverage_gaps.append((gap_start, len(visible_count) * self.time_resolution))
            
        # 計算相位多樣性得分
        phase_diversity = self._calculate_phase_diversity_score(satellites)
        
        return SpatiotemporalCoverage(
            time_coverage_ratio=coverage_ratio,
            min_visible_satellites=min_visible,
            max_visible_satellites=max_visible,
            average_visible_satellites=avg_visible,
            coverage_gaps=coverage_gaps,
            phase_diversity_score=phase_diversity
        )
        
    def _calculate_phase_diversity_score(self, satellites: List[Dict]) -> float:
        """計算相位多樣性得分"""
        if not satellites:
            return 0.0
            
        # 提取所有衛星的軌道要素
        mean_anomalies = []
        raans = []
        
        for sat in satellites:
            tle_data = sat.get('tle_data', {})
            mean_anomalies.append(tle_data.get('mean_anomaly', 0))
            raans.append(tle_data.get('raan', 0))
            
        # 計算分佈均勻度
        ma_std = np.std(mean_anomalies) if mean_anomalies else 0
        raan_std = np.std(raans) if raans else 0
        
        # 理想的標準差（完全均勻分佈）
        ideal_std = 360 / (2 * math.sqrt(3))  # 約104度
        
        # 計算多樣性得分 (0-1)
        ma_diversity = min(ma_std / ideal_std, 1.0)
        raan_diversity = min(raan_std / ideal_std, 1.0)
        
        return (ma_diversity + raan_diversity) / 2
        
    def _supplement_coverage_gaps(
        self,
        selected_satellites: List[Dict],
        all_candidates: List[Dict],
        coverage_analysis: SpatiotemporalCoverage,
        constellation: str,
        max_size: int
    ) -> List[Dict]:
        """補充覆蓋空隙"""
        if len(selected_satellites) >= max_size:
            return selected_satellites
            
        logger.info(f"⚠️ 覆蓋不足，補充衛星以填補空隙")
        
        # 找出未選擇的衛星
        selected_ids = {sat.get('satellite_id') for sat in selected_satellites}
        unselected = [sat for sat in all_candidates 
                     if sat.get('satellite_id') not in selected_ids]
        
        # 針對每個覆蓋空隙，選擇最佳衛星
        supplemented = selected_satellites.copy()
        
        for gap_start, gap_end in coverage_analysis.coverage_gaps:
            if len(supplemented) >= max_size:
                break
                
            # 找出在空隙期間可見的衛星
            gap_coverage_scores = []
            
            for sat in unselected:
                score = self._calculate_gap_coverage_score(sat, gap_start, gap_end)
                if score > 0:
                    gap_coverage_scores.append((sat, score))
                    
            # 選擇得分最高的衛星
            gap_coverage_scores.sort(key=lambda x: x[1], reverse=True)
            
            for sat, score in gap_coverage_scores[:3]:  # 每個空隙最多補充3顆
                if sat.get('satellite_id') not in selected_ids:
                    supplemented.append(sat)
                    selected_ids.add(sat.get('satellite_id'))
                    
                if len(supplemented) >= max_size:
                    break
                    
        return supplemented[:max_size]
        
    def _calculate_gap_coverage_score(self, satellite: Dict, gap_start: float, gap_end: float) -> float:
        """計算衛星對特定空隙的覆蓋得分"""
        position_timeseries = satellite.get('position_timeseries', [])
        
        if not position_timeseries:
            return 0.0
            
        coverage_time = 0
        
        for pos in position_timeseries:
            time_offset = pos.get('time_offset_seconds', 0)
            
            # 檢查是否在空隙時間範圍內
            if gap_start <= time_offset <= gap_end:
                if pos.get('is_visible', False):
                    coverage_time += self.time_resolution
                    
        # 計算覆蓋比例
        gap_duration = gap_end - gap_start
        if gap_duration > 0:
            return coverage_time / gap_duration
        return 0.0
        
    def validate_orbit_period_coverage(
        self,
        satellites: List[Dict],
        constellation: str
    ) -> Dict:
        """驗證完整軌道週期的覆蓋"""
        orbit_period = self.coverage_targets[constellation]['orbit_period']
        min_visible = self.coverage_targets[constellation]['min_visible']
        max_visible = self.coverage_targets[constellation]['max_visible']
        
        logger.info(f"🔍 驗證 {constellation} 完整軌道週期覆蓋 ({orbit_period:.1f} 分鐘)")
        
        # 分析覆蓋
        coverage = self._analyze_coverage_continuity(satellites, constellation)
        
        # 驗證結果
        validation = {
            'constellation': constellation,
            'orbit_period_minutes': orbit_period,
            'satellite_count': len(satellites),
            'coverage_ratio': coverage.time_coverage_ratio,
            'min_visible': coverage.min_visible_satellites,
            'max_visible': coverage.max_visible_satellites,
            'avg_visible': coverage.average_visible_satellites,
            'target_range': (min_visible, max_visible),
            'gaps_count': len(coverage.coverage_gaps),
            'max_gap_duration': max([g[1]-g[0] for g in coverage.coverage_gaps], default=0) / 60,  # 分鐘
            'phase_diversity': coverage.phase_diversity_score,
            'validation_passed': (
                coverage.time_coverage_ratio >= 0.95 and
                coverage.min_visible_satellites >= min_visible * 0.8 and  # 允許80%的最小值
                coverage.average_visible_satellites >= min_visible
            )
        }
        
        # 輸出驗證報告
        logger.info(f"📊 驗證結果:")
        logger.info(f"   衛星數量: {validation['satellite_count']}")
        logger.info(f"   覆蓋率: {validation['coverage_ratio']:.1%}")
        logger.info(f"   可見衛星: {validation['min_visible']}-{validation['max_visible']} (平均 {validation['avg_visible']:.1f})")
        logger.info(f"   目標範圍: {min_visible}-{max_visible}")
        logger.info(f"   覆蓋空隙: {validation['gaps_count']} 個")
        logger.info(f"   最大空隙: {validation['max_gap_duration']:.1f} 分鐘")
        logger.info(f"   相位多樣性: {validation['phase_diversity']:.2f}")
        logger.info(f"   ✅ 驗證: {'通過' if validation['validation_passed'] else '❌ 未通過'}")
        
        return validation