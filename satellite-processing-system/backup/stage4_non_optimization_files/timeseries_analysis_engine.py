#!/usr/bin/env python3
"""
時序分析引擎 - 整合重複功能

專責功能：
1. 覆蓋窗口分析
2. 時空模式識別
3. 軌道周期分析
4. 間隙分析

使用共享模組避免重複實現

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 去重複化專用
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

# 使用共享核心模組
from shared.core_modules.visibility_calculations_core import VisibilityCalculationsCore
from shared.core_modules.orbital_calculations_core import OrbitalCalculationsCore

logger = logging.getLogger(__name__)

class TimeseriesAnalysisEngine:
    """
    時序分析引擎 - 去重複化版本

    專注於時序模式分析，不重複實現基礎計算
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化時序分析引擎"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        # 使用共享模組
        self.visibility_calculator = VisibilityCalculationsCore()
        self.orbital_calculator = OrbitalCalculationsCore()

        # 分析配置
        self.analysis_config = {
            'min_visibility_elevation': 5.0,
            'coverage_gap_threshold': 300,  # 秒
            'orbital_period_hours': 1.5,
            'window_overlap_threshold': 0.1
        }

        self.analysis_stats = {
            'total_satellites_analyzed': 0,
            'coverage_windows_identified': 0,
            'coverage_gaps_found': 0,
            'orbital_cycles_analyzed': 0
        }

        self.logger.info("✅ 時序分析引擎初始化完成 (使用共享模組)")

    def analyze_timeseries_patterns(self, satellites_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析時序模式

        Args:
            satellites_data: 衛星數據列表

        Returns:
            時序分析結果
        """
        try:
            self.logger.info("🔍 開始時序模式分析")

            analysis_results = {
                'satellites': [],
                'global_coverage_analysis': {},
                'temporal_patterns': {},
                'spatial_patterns': {},
                'coverage_optimization_suggestions': []
            }

            # 分析每顆衛星
            for satellite_data in satellites_data:
                satellite_analysis = self._analyze_satellite_timeseries(satellite_data)
                if satellite_analysis:
                    analysis_results['satellites'].append(satellite_analysis)

            # 全域覆蓋分析
            analysis_results['global_coverage_analysis'] = self._analyze_global_coverage(
                analysis_results['satellites']
            )

            # 時空模式識別
            analysis_results['temporal_patterns'] = self._identify_temporal_patterns(
                analysis_results['satellites']
            )

            analysis_results['spatial_patterns'] = self._identify_spatial_patterns(
                analysis_results['satellites']
            )

            # 生成優化建議
            analysis_results['coverage_optimization_suggestions'] = self._generate_optimization_suggestions(
                analysis_results
            )

            self.logger.info(f"✅ 時序分析完成，處理 {len(analysis_results['satellites'])} 顆衛星")
            return analysis_results

        except Exception as e:
            self.logger.error(f"❌ 時序分析失敗: {e}")
            return {'error': str(e), 'satellites': []}

    def _analyze_satellite_timeseries(self, satellite_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析單顆衛星的時序數據"""
        try:
            satellite_id = satellite_data.get('satellite_id')
            position_timeseries = satellite_data.get('position_timeseries', [])

            if not position_timeseries:
                return None

            # ✅ 使用共享模組提取可見性窗口
            visibility_windows = self._extract_visibility_windows_unified(position_timeseries)

            # 軌道周期分析
            orbital_cycles = self._analyze_orbital_cycles(position_timeseries)

            # 覆蓋間隙分析
            coverage_gaps = self._analyze_coverage_gaps_unified(visibility_windows)

            # 時空窗口識別
            spatial_temporal_windows = self._identify_spatial_temporal_windows(position_timeseries)

            # 更新統計
            self.analysis_stats['total_satellites_analyzed'] += 1
            self.analysis_stats['coverage_windows_identified'] += len(visibility_windows)
            self.analysis_stats['coverage_gaps_found'] += len(coverage_gaps)
            self.analysis_stats['orbital_cycles_analyzed'] += len(orbital_cycles)

            return {
                'satellite_id': satellite_id,
                'constellation': satellite_data.get('constellation'),
                'visibility_windows': visibility_windows,
                'orbital_cycles': orbital_cycles,
                'coverage_gaps': coverage_gaps,
                'spatial_temporal_windows': spatial_temporal_windows,
                'coverage_metrics': {
                    'total_visibility_time': sum(w['duration_seconds'] for w in visibility_windows),
                    'max_gap_seconds': max([g['duration_seconds'] for g in coverage_gaps], default=0),
                    'avg_elevation': sum(w['max_elevation'] for w in visibility_windows) / len(visibility_windows) if visibility_windows else 0,
                    'coverage_efficiency': len(visibility_windows) / len(position_timeseries) if position_timeseries else 0
                }
            }

        except Exception as e:
            self.logger.error(f"❌ 衛星 {satellite_data.get('satellite_id')} 時序分析失敗: {e}")
            return None

    def _extract_visibility_windows_unified(self, position_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取可見性窗口 - 使用共享模組

        避免重複實現仰角計算邏輯
        """
        windows = []
        current_window = None
        min_elevation = self.analysis_config['min_visibility_elevation']

        for position in position_timeseries:
            # ✅ 使用共享模組獲取可見性信息
            visibility_info = self.visibility_calculator.calculate_visibility_metrics(position)

            elevation = visibility_info.get('elevation_deg', 0)
            is_visible = elevation > min_elevation

            if is_visible:
                if current_window is None:
                    # 開始新窗口
                    current_window = {
                        'start_time': position.get('timestamp'),
                        'start_elevation': elevation,
                        'max_elevation': elevation,
                        'positions_count': 1
                    }
                else:
                    # 繼續當前窗口
                    current_window['max_elevation'] = max(current_window['max_elevation'], elevation)
                    current_window['positions_count'] += 1
            else:
                if current_window is not None:
                    # 結束當前窗口
                    current_window['end_time'] = position.get('timestamp')
                    current_window['end_elevation'] = elevation
                    current_window['duration_seconds'] = (
                        current_window['end_time'] - current_window['start_time']
                    ) if isinstance(current_window.get('end_time'), (int, float)) else 0

                    windows.append(current_window)
                    current_window = None

        # 處理最後一個窗口
        if current_window is not None:
            current_window['end_time'] = position_timeseries[-1].get('timestamp')
            current_window['duration_seconds'] = (
                current_window['end_time'] - current_window['start_time']
            ) if isinstance(current_window.get('end_time'), (int, float)) else 0
            windows.append(current_window)

        return windows

    def _analyze_orbital_cycles(self, position_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析軌道周期"""
        cycles = []

        try:
            # 根據軌道週期分組
            period_seconds = self.analysis_config['orbital_period_hours'] * 3600
            total_duration = len(position_timeseries) * 30  # 假設30秒間隔

            num_cycles = max(1, int(total_duration / period_seconds))
            positions_per_cycle = len(position_timeseries) // num_cycles

            for i in range(num_cycles):
                start_idx = i * positions_per_cycle
                end_idx = min((i + 1) * positions_per_cycle, len(position_timeseries))

                cycle_positions = position_timeseries[start_idx:end_idx]

                if cycle_positions:
                    # ✅ 使用共享模組分析軌道參數
                    orbital_analysis = self.orbital_calculator.analyze_orbital_cycle(cycle_positions)

                    cycle = {
                        'cycle_number': i + 1,
                        'start_position_index': start_idx,
                        'end_position_index': end_idx,
                        'positions_count': len(cycle_positions),
                        'orbital_parameters': orbital_analysis,
                        'coverage_statistics': self._calculate_cycle_coverage_stats(cycle_positions)
                    }

                    cycles.append(cycle)

        except Exception as e:
            self.logger.error(f"❌ 軌道周期分析失敗: {e}")

        return cycles

    def _analyze_coverage_gaps_unified(self, visibility_windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分析覆蓋間隙 - 使用標準化窗口數據

        避免重複實現間隙計算邏輯
        """
        gaps = []

        try:
            for i in range(len(visibility_windows) - 1):
                current_window = visibility_windows[i]
                next_window = visibility_windows[i + 1]

                gap_start = current_window.get('end_time')
                gap_end = next_window.get('start_time')

                if gap_start and gap_end and gap_end > gap_start:
                    gap_duration = gap_end - gap_start

                    if gap_duration > self.analysis_config['coverage_gap_threshold']:
                        gap = {
                            'gap_number': i + 1,
                            'start_time': gap_start,
                            'end_time': gap_end,
                            'duration_seconds': gap_duration,
                            'severity': self._classify_gap_severity(gap_duration),
                            'preceding_window': current_window,
                            'following_window': next_window
                        }

                        gaps.append(gap)

        except Exception as e:
            self.logger.error(f"❌ 覆蓋間隙分析失敗: {e}")

        return gaps

    def _identify_spatial_temporal_windows(self, position_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """識別時空窗口"""
        windows = []

        try:
            # 基於地理區域分組
            regional_groups = self._group_positions_by_region(position_timeseries)

            for region, positions in regional_groups.items():
                if len(positions) >= 3:  # 至少需要3個位置點
                    window = {
                        'region': region,
                        'positions_count': len(positions),
                        'start_time': positions[0].get('timestamp'),
                        'end_time': positions[-1].get('timestamp'),
                        'duration_seconds': positions[-1].get('timestamp', 0) - positions[0].get('timestamp', 0),
                        'geographic_center': self._calculate_geographic_center(positions),
                        'coverage_quality': self._assess_regional_coverage_quality(positions)
                    }

                    windows.append(window)

        except Exception as e:
            self.logger.error(f"❌ 時空窗口識別失敗: {e}")

        return windows

    def _group_positions_by_region(self, positions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按地理區域分組位置"""
        regions = {}

        for position in positions:
            # 簡化的區域劃分（基於經緯度範圍）
            lat = position.get('geodetic_coordinates', {}).get('latitude_deg', 0)
            lon = position.get('geodetic_coordinates', {}).get('longitude_deg', 0)

            # 將地球分為9個區域
            lat_zone = 'N' if lat > 30 else 'M' if lat > -30 else 'S'
            lon_zone = 'E' if lon > 60 else 'C' if lon > -60 else 'W'
            region = f"{lat_zone}{lon_zone}"

            if region not in regions:
                regions[region] = []
            regions[region].append(position)

        return regions

    def _calculate_geographic_center(self, positions: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算地理中心"""
        if not positions:
            return {'latitude': 0.0, 'longitude': 0.0}

        total_lat = sum(pos.get('geodetic_coordinates', {}).get('latitude_deg', 0) for pos in positions)
        total_lon = sum(pos.get('geodetic_coordinates', {}).get('longitude_deg', 0) for pos in positions)

        return {
            'latitude': total_lat / len(positions),
            'longitude': total_lon / len(positions)
        }

    def _assess_regional_coverage_quality(self, positions: List[Dict[str, Any]]) -> float:
        """評估區域覆蓋品質"""
        if not positions:
            return 0.0

        # 基於平均仰角評估
        total_elevation = sum(
            pos.get('relative_to_observer', {}).get('elevation_deg', 0) for pos in positions
        )

        avg_elevation = total_elevation / len(positions)
        return min(1.0, avg_elevation / 45.0)  # 正規化到0-1

    def _classify_gap_severity(self, gap_duration: float) -> str:
        """分類間隙嚴重程度"""
        if gap_duration < 600:  # 10分鐘
            return 'low'
        elif gap_duration < 1800:  # 30分鐘
            return 'medium'
        else:
            return 'high'

    def _calculate_cycle_coverage_stats(self, cycle_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算周期覆蓋統計"""
        if not cycle_positions:
            return {}

        visible_positions = [
            pos for pos in cycle_positions
            if pos.get('relative_to_observer', {}).get('elevation_deg', 0) > self.analysis_config['min_visibility_elevation']
        ]

        return {
            'total_positions': len(cycle_positions),
            'visible_positions': len(visible_positions),
            'visibility_ratio': len(visible_positions) / len(cycle_positions),
            'max_elevation': max(
                pos.get('relative_to_observer', {}).get('elevation_deg', 0) for pos in cycle_positions
            ),
            'avg_elevation': sum(
                pos.get('relative_to_observer', {}).get('elevation_deg', 0) for pos in visible_positions
            ) / len(visible_positions) if visible_positions else 0
        }

    def _analyze_global_coverage(self, satellites_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析全域覆蓋情況"""
        total_windows = sum(len(sat['visibility_windows']) for sat in satellites_analysis)
        total_gaps = sum(len(sat['coverage_gaps']) for sat in satellites_analysis)

        return {
            'total_satellites': len(satellites_analysis),
            'total_visibility_windows': total_windows,
            'total_coverage_gaps': total_gaps,
            'avg_windows_per_satellite': total_windows / len(satellites_analysis) if satellites_analysis else 0,
            'coverage_continuity_score': total_windows / (total_windows + total_gaps) if (total_windows + total_gaps) > 0 else 0
        }

    def _identify_temporal_patterns(self, satellites_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """識別時間模式"""
        return {
            'peak_coverage_hours': [],  # 可以進一步實現
            'low_coverage_periods': [],
            'optimal_handover_windows': []
        }

    def _identify_spatial_patterns(self, satellites_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """識別空間模式"""
        return {
            'high_coverage_regions': [],  # 可以進一步實現
            'coverage_blind_spots': [],
            'optimal_satellite_distribution': {}
        }

    def _generate_optimization_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """生成優化建議"""
        suggestions = []

        global_analysis = analysis_results.get('global_coverage_analysis', {})
        continuity_score = global_analysis.get('coverage_continuity_score', 0)

        if continuity_score < 0.8:
            suggestions.append("覆蓋連續性偏低，建議增加衛星數量或優化軌道配置")

        avg_windows = global_analysis.get('avg_windows_per_satellite', 0)
        if avg_windows < 3:
            suggestions.append("每顆衛星平均可見窗口過少，建議調整觀測者位置或仰角門檻")

        return suggestions

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """獲取分析統計"""
        return self.analysis_stats.copy()