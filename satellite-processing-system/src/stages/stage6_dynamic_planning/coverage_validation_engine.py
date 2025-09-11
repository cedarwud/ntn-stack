#!/usr/bin/env python3
"""
95%+ 覆蓋率量化驗證引擎

根據 @satellite-processing-system/docs/stages/stage6-dynamic-pool.md 第494-653行要求實現：
- 95%+覆蓋率精確量化指標
- 覆蓋間隙分析 (最大容許間隙 ≤ 2分鐘)
- 詳細時間線統計
- 軌道週期驗證
- 學術級覆蓋統計分析
"""

import logging
import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class CoverageValidationEngine:
    """
    95%+ 覆蓋率量化驗證引擎
    
    實現文檔第494-653行要求的完整覆蓋率驗證功能：
    - Starlink: ≥95% 時間保持10+顆可見（5°仰角）
    - OneWeb: ≥95% 時間保持3+顆可見（10°仰角）
    - 綜合覆蓋率: ≥95% 時間同時滿足兩個星座要求
    - 最大覆蓋間隙: ≤2分鐘連續覆蓋不足時段
    """
    
    def __init__(self, 
                 observer_lat: float = 24.9441667, 
                 observer_lon: float = 121.3713889,
                 sampling_interval_sec: int = 30,
                 validation_window_hours: float = 2.0):
        """
        初始化覆蓋驗證引擎
        
        Args:
            observer_lat: 觀測點緯度 (NTPU)
            observer_lon: 觀測點經度 (NTPU)
            sampling_interval_sec: 採樣間隔 (秒)
            validation_window_hours: 驗證時間窗口 (小時)
        """
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.sampling_interval_sec = sampling_interval_sec
        self.validation_window_hours = validation_window_hours
        
        # 覆蓋要求配置 (文檔507-509行)
        self.coverage_requirements = {
            'starlink': {
                'min_elevation': 5.0,           # 5° 仰角
                'min_satellites': 10,           # 最少10顆
                'target_coverage': 0.95         # 95%覆蓋率
            },
            'oneweb': {
                'min_elevation': 10.0,          # 10° 仰角  
                'min_satellites': 3,            # 最少3顆
                'target_coverage': 0.95         # 95%覆蓋率
            }
        }
        
        # 間隙容忍配置
        self.max_acceptable_gap_minutes = 2.0    # 最大2分鐘間隙
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.validation_stats = {
            "validations_performed": 0,
            "coverage_validations_passed": 0,
            "academic_compliance": "Grade_A_95_percent_coverage_validation"
        }
    
    def calculate_coverage_ratio(self, selected_satellites: Dict[str, Any], 
                                time_window_hours: Optional[float] = None) -> Dict[str, Any]:
        """
        計算95%+覆蓋率的精確量化指標 (文檔511-609行)
        
        Args:
            selected_satellites: 選中的衛星池
            time_window_hours: 時間窗口 (默認2小時)
            
        Returns:
            Dict: 詳細覆蓋統計結果
        """
        if time_window_hours is None:
            time_window_hours = self.validation_window_hours
            
        # 計算總採樣點數 (文檔513行)
        total_timepoints = int((time_window_hours * 3600) / self.sampling_interval_sec)
        
        self.logger.info(f"🔍 開始95%+覆蓋率驗證: {time_window_hours}h窗口, {total_timepoints}個採樣點")
        
        coverage_stats = {
            'starlink_coverage_ratio': 0.0,
            'oneweb_coverage_ratio': 0.0, 
            'combined_coverage_ratio': 0.0,
            'coverage_gaps': [],
            'detailed_timeline': [],
            'validation_metadata': {
                'total_timepoints': total_timepoints,
                'sampling_interval_sec': self.sampling_interval_sec,
                'time_window_hours': time_window_hours,
                'observer_location': (self.observer_lat, self.observer_lon),
                'coverage_requirements': self.coverage_requirements,
                'academic_compliance': 'Grade_A_precise_quantification'
            }
        }
        
        # 遍歷每個時間點進行覆蓋分析 (文檔531-572行)
        starlink_satisfied_count = 0
        oneweb_satisfied_count = 0
        combined_satisfied_count = 0
        
        current_gap_start = None
        gaps = []
        
        for timepoint in range(total_timepoints):
            current_time_sec = timepoint * self.sampling_interval_sec
            
            # 計算當前時間點的可見衛星數 (文檔534-545行)
            starlink_visible = self._count_visible_satellites(
                selected_satellites.get('starlink', []), 
                current_time_sec,
                min_elevation=self.coverage_requirements['starlink']['min_elevation']
            )
            
            oneweb_visible = self._count_visible_satellites(
                selected_satellites.get('oneweb', []),
                current_time_sec, 
                min_elevation=self.coverage_requirements['oneweb']['min_elevation']
            )
            
            # 檢查是否滿足覆蓋要求 (文檔547-550行)
            starlink_satisfied = starlink_visible >= self.coverage_requirements['starlink']['min_satellites']
            oneweb_satisfied = oneweb_visible >= self.coverage_requirements['oneweb']['min_satellites']
            combined_satisfied = starlink_satisfied and oneweb_satisfied
            
            # 累計滿足要求的時間點 (文檔552-558行)
            if starlink_satisfied:
                starlink_satisfied_count += 1
            if oneweb_satisfied:
                oneweb_satisfied_count += 1
            if combined_satisfied:
                combined_satisfied_count += 1
            
            # 記錄覆蓋間隙 (文檔560-572行)
            if not combined_satisfied:
                if current_gap_start is None:
                    current_gap_start = timepoint
            else:
                if current_gap_start is not None:
                    gap_duration_min = (timepoint - current_gap_start) * self.sampling_interval_sec / 60
                    gaps.append({
                        'start_timepoint': current_gap_start,
                        'end_timepoint': timepoint,
                        'duration_minutes': gap_duration_min,
                        'start_time_sec': current_gap_start * self.sampling_interval_sec,
                        'end_time_sec': timepoint * self.sampling_interval_sec
                    })
                    current_gap_start = None
            
            # 記錄詳細時間線（採樣記錄）(文檔574-584行)
            if timepoint % 20 == 0:  # 每10分鐘記錄一次詳情
                coverage_stats['detailed_timeline'].append({
                    'timepoint': timepoint,
                    'time_minutes': current_time_sec / 60,
                    'time_formatted': f"{current_time_sec // 3600:02.0f}:{(current_time_sec % 3600) // 60:02.0f}:{current_time_sec % 60:02.0f}",
                    'starlink_visible': starlink_visible,
                    'oneweb_visible': oneweb_visible,
                    'starlink_satisfied': starlink_satisfied,
                    'oneweb_satisfied': oneweb_satisfied,
                    'combined_satisfied': combined_satisfied
                })
        
        # 處理最後一個間隙 (文檔586-593行)
        if current_gap_start is not None:
            gap_duration_min = (total_timepoints - current_gap_start) * self.sampling_interval_sec / 60
            gaps.append({
                'start_timepoint': current_gap_start,
                'end_timepoint': total_timepoints,
                'duration_minutes': gap_duration_min,
                'start_time_sec': current_gap_start * self.sampling_interval_sec,
                'end_time_sec': total_timepoints * self.sampling_interval_sec
            })
        
        # 計算覆蓋率百分比 (文檔595-608行)
        coverage_stats.update({
            'starlink_coverage_ratio': starlink_satisfied_count / total_timepoints,
            'oneweb_coverage_ratio': oneweb_satisfied_count / total_timepoints,
            'combined_coverage_ratio': combined_satisfied_count / total_timepoints,
            'coverage_gaps': [gap for gap in gaps if gap['duration_minutes'] > self.max_acceptable_gap_minutes],
            'all_gaps': gaps,  # 包含所有間隙用於詳細分析
            'coverage_gap_analysis': {
                'total_gaps': len([gap for gap in gaps if gap['duration_minutes'] > self.max_acceptable_gap_minutes]),
                'total_gaps_all': len(gaps),
                'max_gap_minutes': max([gap['duration_minutes'] for gap in gaps], default=0),
                'avg_gap_minutes': np.mean([gap['duration_minutes'] for gap in gaps]) if gaps else 0,
                'gap_frequency_per_hour': len(gaps) / time_window_hours if gaps else 0
            }
        })
        
        # 記錄統計信息
        self.logger.info(f"📊 覆蓋率統計:")
        self.logger.info(f"   Starlink: {coverage_stats['starlink_coverage_ratio']:.1%} ({starlink_satisfied_count}/{total_timepoints})")
        self.logger.info(f"   OneWeb: {coverage_stats['oneweb_coverage_ratio']:.1%} ({oneweb_satisfied_count}/{total_timepoints})")
        self.logger.info(f"   綜合: {coverage_stats['combined_coverage_ratio']:.1%} ({combined_satisfied_count}/{total_timepoints})")
        self.logger.info(f"   間隙分析: {len(gaps)}個間隙, 最大{coverage_stats['coverage_gap_analysis']['max_gap_minutes']:.1f}分鐘")
        
        return coverage_stats
    
    def _count_visible_satellites(self, satellites: List[Dict[str, Any]], 
                                 time_sec: float, min_elevation: float) -> int:
        """
        計算指定時間點的可見衛星數量 (文檔611-628行)
        
        Args:
            satellites: 衛星列表
            time_sec: 當前時間 (秒)
            min_elevation: 最小仰角要求
            
        Returns:
            int: 可見衛星數量
        """
        visible_count = 0
        
        for satellite in satellites:
            position_timeseries = satellite.get('position_timeseries', [])
            
            if not position_timeseries:
                continue
                
            # 找到最接近的時間點
            target_timepoint = int(time_sec / self.sampling_interval_sec)
            
            if target_timepoint < len(position_timeseries):
                position_data = position_timeseries[target_timepoint]
                elevation = position_data.get('elevation_deg', -90)
                
                if elevation >= min_elevation:
                    visible_count += 1
        
        return visible_count
    
    def validate_coverage_requirements(self, coverage_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證是否滿足95%+覆蓋率要求 (文檔630-652行)
        
        Args:
            coverage_stats: 覆蓋統計數據
            
        Returns:
            Dict: 驗證結果
        """
        validation_result = {
            'overall_passed': False,
            'starlink_passed': False,
            'oneweb_passed': False,
            'combined_passed': False,
            'gap_analysis_passed': False,
            'detailed_checks': {},
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'academic_compliance': 'Grade_A_95_percent_coverage_requirements'
        }
        
        # 檢查各項覆蓋率要求
        starlink_coverage = coverage_stats.get('starlink_coverage_ratio', 0.0)
        oneweb_coverage = coverage_stats.get('oneweb_coverage_ratio', 0.0)
        combined_coverage = coverage_stats.get('combined_coverage_ratio', 0.0)
        
        validation_result['starlink_passed'] = starlink_coverage >= self.coverage_requirements['starlink']['target_coverage']
        validation_result['oneweb_passed'] = oneweb_coverage >= self.coverage_requirements['oneweb']['target_coverage']
        validation_result['combined_passed'] = combined_coverage >= self.coverage_requirements['starlink']['target_coverage']
        
        # 檢查間隙分析
        gap_analysis = coverage_stats.get('coverage_gap_analysis', {})
        max_gap_minutes = gap_analysis.get('max_gap_minutes', 999.0)
        validation_result['gap_analysis_passed'] = max_gap_minutes <= self.max_acceptable_gap_minutes
        
        # 詳細檢查結果
        validation_result['detailed_checks'] = {
            'starlink_coverage_percentage': f"{starlink_coverage:.1%}",
            'starlink_target_percentage': f"{self.coverage_requirements['starlink']['target_coverage']:.0%}",
            'starlink_requirement': f"≥{self.coverage_requirements['starlink']['min_satellites']}顆@{self.coverage_requirements['starlink']['min_elevation']}°仰角",
            'oneweb_coverage_percentage': f"{oneweb_coverage:.1%}",
            'oneweb_target_percentage': f"{self.coverage_requirements['oneweb']['target_coverage']:.0%}",
            'oneweb_requirement': f"≥{self.coverage_requirements['oneweb']['min_satellites']}顆@{self.coverage_requirements['oneweb']['min_elevation']}°仰角",
            'combined_coverage_percentage': f"{combined_coverage:.1%}",
            'max_gap_duration': f"{max_gap_minutes:.1f} 分鐘",
            'max_gap_target': f"≤{self.max_acceptable_gap_minutes} 分鐘",
            'total_gaps': gap_analysis.get('total_gaps', 0),
            'gap_frequency': f"{gap_analysis.get('gap_frequency_per_hour', 0):.1f} 次/小時"
        }
        
        # 總體通過判定 (文檔646-650行)
        validation_result['overall_passed'] = (
            validation_result['starlink_passed'] and 
            validation_result['oneweb_passed'] and
            validation_result['gap_analysis_passed']
        )
        
        # 記錄驗證結果
        if validation_result['overall_passed']:
            self.logger.info("✅ 95%+覆蓋率要求驗證通過!")
            self.validation_stats["coverage_validations_passed"] += 1
        else:
            failed_items = []
            if not validation_result['starlink_passed']:
                failed_items.append(f"Starlink覆蓋率{starlink_coverage:.1%}<95%")
            if not validation_result['oneweb_passed']:
                failed_items.append(f"OneWeb覆蓋率{oneweb_coverage:.1%}<95%") 
            if not validation_result['gap_analysis_passed']:
                failed_items.append(f"最大間隙{max_gap_minutes:.1f}min>2min")
            
            self.logger.warning(f"⚠️ 95%+覆蓋率要求驗證失敗: {', '.join(failed_items)}")
        
        self.validation_stats["validations_performed"] += 1
        return validation_result
    
    def calculate_phase_diversity_score(self, selected_satellites: Dict[str, Any]) -> float:
        """
        計算軌道相位多樣性分數
        
        根據文檔要求分析平近點角(Mean Anomaly)和升交點經度(RAAN)的分散程度
        
        Args:
            selected_satellites: 選中的衛星池
            
        Returns:
            float: 相位多樣性分數 (0-1)
        """
        diversity_scores = []
        
        for constellation, satellites in selected_satellites.items():
            if not satellites:
                continue
                
            mean_anomalies = []
            raan_values = []
            
            for satellite in satellites:
                # 嘗試從軌道數據中提取相位信息
                orbital_data = satellite.get('orbital_data', {})
                if 'mean_anomaly' in orbital_data:
                    mean_anomalies.append(orbital_data['mean_anomaly'])
                if 'raan' in orbital_data:
                    raan_values.append(orbital_data['raan'])
            
            # 計算分散程度
            ma_diversity = self._calculate_angular_diversity(mean_anomalies) if mean_anomalies else 0.5
            raan_diversity = self._calculate_angular_diversity(raan_values) if raan_values else 0.5
            
            constellation_diversity = (ma_diversity + raan_diversity) / 2
            diversity_scores.append(constellation_diversity)
            
            self.logger.info(f"📐 {constellation} 相位多樣性: MA={ma_diversity:.2f}, RAAN={raan_diversity:.2f}, 總計={constellation_diversity:.2f}")
        
        overall_diversity = np.mean(diversity_scores) if diversity_scores else 0.5
        
        self.logger.info(f"🎯 總體軌道相位多樣性分數: {overall_diversity:.2f}")
        return overall_diversity
    
    def _calculate_angular_diversity(self, angles: List[float]) -> float:
        """計算角度分散程度"""
        if len(angles) < 2:
            return 0.5
        
        # 將角度轉換為弧度並計算分散程度
        angles_rad = [math.radians(angle) for angle in angles]
        
        # 計算角度的標準差 (考慮圓周性)
        x_coords = [math.cos(angle) for angle in angles_rad]
        y_coords = [math.sin(angle) for angle in angles_rad]
        
        x_mean = np.mean(x_coords)
        y_mean = np.mean(y_coords)
        
        # 計算向量長度，越小表示越分散
        vector_length = math.sqrt(x_mean**2 + y_mean**2)
        
        # 轉換為多樣性分數 (0-1，越大越好)
        diversity_score = 1.0 - vector_length
        
        return max(0.0, min(1.0, diversity_score))
    
    def generate_coverage_validation_report(self, coverage_stats: Dict[str, Any], 
                                          validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整的覆蓋驗證報告
        
        Args:
            coverage_stats: 覆蓋統計數據
            validation_result: 驗證結果
            
        Returns:
            Dict: 完整驗證報告
        """
        report = {
            'validation_summary': {
                'overall_status': 'PASSED' if validation_result['overall_passed'] else 'FAILED',
                'validation_timestamp': validation_result['validation_timestamp'],
                'academic_compliance': validation_result['academic_compliance'],
                'validation_criteria': '95%+覆蓋率，≤2分鐘間隙'
            },
            'coverage_performance': {
                'starlink': {
                    'coverage_ratio': coverage_stats['starlink_coverage_ratio'],
                    'requirement_met': validation_result['starlink_passed'],
                    'target_requirement': f"≥{self.coverage_requirements['starlink']['min_satellites']}顆@{self.coverage_requirements['starlink']['min_elevation']}°仰角",
                    'performance_grade': self._get_performance_grade(coverage_stats['starlink_coverage_ratio'])
                },
                'oneweb': {
                    'coverage_ratio': coverage_stats['oneweb_coverage_ratio'],
                    'requirement_met': validation_result['oneweb_passed'],
                    'target_requirement': f"≥{self.coverage_requirements['oneweb']['min_satellites']}顆@{self.coverage_requirements['oneweb']['min_elevation']}°仰角",
                    'performance_grade': self._get_performance_grade(coverage_stats['oneweb_coverage_ratio'])
                },
                'combined': {
                    'coverage_ratio': coverage_stats['combined_coverage_ratio'],
                    'requirement_met': validation_result['combined_passed'],
                    'performance_grade': self._get_performance_grade(coverage_stats['combined_coverage_ratio'])
                }
            },
            'gap_analysis': coverage_stats['coverage_gap_analysis'],
            'detailed_timeline_sample': coverage_stats['detailed_timeline'][:10],  # 前10個採樣點
            'validation_metadata': coverage_stats['validation_metadata'],
            'recommendations': self._generate_recommendations(coverage_stats, validation_result)
        }
        
        return report
    
    def _get_performance_grade(self, coverage_ratio: float) -> str:
        """根據覆蓋率判定性能等級"""
        if coverage_ratio >= 0.98:
            return "A+"
        elif coverage_ratio >= 0.95:
            return "A"
        elif coverage_ratio >= 0.90:
            return "B"
        elif coverage_ratio >= 0.85:
            return "C"
        else:
            return "F"
    
    def _generate_recommendations(self, coverage_stats: Dict[str, Any], 
                                 validation_result: Dict[str, Any]) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if not validation_result['starlink_passed']:
            recommendations.append("增加Starlink衛星數量或降低仰角門檻以提升覆蓋率")
        
        if not validation_result['oneweb_passed']:
            recommendations.append("增加OneWeb衛星數量或優化軌道平面選擇")
        
        if not validation_result['gap_analysis_passed']:
            max_gap = coverage_stats['coverage_gap_analysis']['max_gap_minutes']
            recommendations.append(f"優化軌道相位分散以減少覆蓋間隙(當前最大{max_gap:.1f}分鐘)")
        
        if coverage_stats['combined_coverage_ratio'] < 0.98:
            recommendations.append("考慮實施動態候補衛星策略以提升整體可靠性")
        
        if not recommendations:
            recommendations.append("覆蓋性能優異，建議保持當前配置")
        
        return recommendations
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計信息"""
        return self.validation_stats.copy()