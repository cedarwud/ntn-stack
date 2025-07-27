#!/usr/bin/env python3
"""
最佳時間段分析器 - Phase 0 Implementation  
找出30-45分鐘的最佳換手時間段，並產出完整的衛星配置數據

功能:
1. 找出30-45分鐘的最佳換手時間段
2. 分析候選衛星在不同時間段的可見性
3. 找出包含6-10顆衛星的最佳時間段
4. 確保時間段長度適合動畫展示（30-45分鐘）
5. 產出該時間段的完整衛星軌跡數據
"""

import asyncio
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict

from skyfield.api import EarthSatellite, utc, load, wgs84
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class SatelliteTrajectoryPoint:
    """衛星軌跡點"""
    time: str                # ISO 格式時間
    elevation: float         # 仰角 (度)
    azimuth: float          # 方位角 (度)
    latitude: float         # 衛星緯度 (度)
    longitude: float        # 衛星經度 (度)
    altitude_km: float      # 衛星高度 (km)
    distance_km: float      # 與觀察者距離 (km)
    visible: bool           # 是否可見


@dataclass
class VisibilityWindow:
    """可見性時間窗"""
    rise_time: str          # 升起時間
    peak_time: str          # 最高點時間
    set_time: str           # 落下時間
    max_elevation: float    # 最大仰角 (度)
    duration_minutes: float # 持續時間 (分鐘)


@dataclass
class SatelliteTrajectory:
    """完整衛星軌跡"""
    norad_id: int
    name: str
    trajectory: List[SatelliteTrajectoryPoint]
    visibility_window: VisibilityWindow
    handover_priority: int
    signal_strength_profile: List[float]  # 信號強度變化


@dataclass  
class OptimalTimeframe:
    """最佳時間段"""
    start_timestamp: str
    duration_minutes: int
    satellite_count: int
    satellites: List[SatelliteTrajectory]
    handover_sequence: List[Dict[str, Any]]
    coverage_quality_score: float


class OptimalTimeframeAnalyzer:
    """最佳時間段分析器"""
    
    def __init__(self, min_elevation: float = 5.0, time_step_seconds: int = 30):
        """
        初始化分析器
        
        Args:
            min_elevation: 最小仰角要求 (度)
            time_step_seconds: 軌跡計算時間步長 (秒)
        """
        self.min_elevation = min_elevation
        self.time_step_seconds = time_step_seconds
        self.ts = load.timescale()
        
        # 地球模型
        self.earth = wgs84
        
    def calculate_satellite_visibility(self, satellite_data: Dict[str, str], 
                                     observer_lat: float, observer_lon: float,
                                     start_time: datetime, duration_minutes: int) -> Optional[SatelliteTrajectory]:
        """
        計算單顆衛星在指定時間段的可見性和軌跡
        
        Args:
            satellite_data: 衛星 TLE 數據
            observer_lat: 觀察者緯度 (度)
            observer_lon: 觀察者經度 (度)  
            start_time: 開始時間
            duration_minutes: 持續時間 (分鐘)
            
        Returns:
            衛星軌跡數據，如果不可見則返回 None
        """
        try:
            # 創建衛星和觀察者對象
            satellite = EarthSatellite(satellite_data['line1'], satellite_data['line2'], satellite_data['name'])
            observer = self.earth.latlon(observer_lat, observer_lon)
            
            # 時間範圍
            end_time = start_time + timedelta(minutes=duration_minutes)
            time_points = []
            current_time = start_time
            
            while current_time <= end_time:
                time_points.append(current_time)
                current_time += timedelta(seconds=self.time_step_seconds)
            
            # 計算軌跡點
            trajectory_points = []
            visible_points = []
            elevations = []
            
            for time_point in time_points:
                t = self.ts.from_datetime(time_point)
                
                # 計算衛星位置
                geocentric = satellite.at(t)
                subpoint = geocentric.subpoint()
                
                # 計算觀察者視角
                difference = satellite - observer
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                elevation_deg = alt.degrees
                azimuth_deg = az.degrees
                distance_km = distance.km
                
                # 創建軌跡點
                point = SatelliteTrajectoryPoint(
                    time=time_point.isoformat(),
                    elevation=elevation_deg,
                    azimuth=azimuth_deg,
                    latitude=subpoint.latitude.degrees,
                    longitude=subpoint.longitude.degrees,
                    altitude_km=subpoint.elevation.km,
                    distance_km=distance_km,
                    visible=elevation_deg >= self.min_elevation
                )
                
                trajectory_points.append(point)
                
                if point.visible:
                    visible_points.append(point)
                    elevations.append(elevation_deg)
            
            # 如果沒有可見點，返回 None
            if not visible_points:
                return None
            
            # 計算可見性窗口
            visibility_window = self._calculate_visibility_window(visible_points)
            
            # 計算信號強度變化
            signal_strength_profile = self._calculate_signal_strength(trajectory_points)
            
            # 確定換手優先級（基於最大仰角和持續時間）
            handover_priority = self._calculate_handover_priority(visibility_window, len(visible_points))
            
            return SatelliteTrajectory(
                norad_id=satellite_data['norad_id'],
                name=satellite_data['name'],
                trajectory=trajectory_points,
                visibility_window=visibility_window,
                handover_priority=handover_priority,
                signal_strength_profile=signal_strength_profile
            )
            
        except Exception as e:
            logger.error(f"計算衛星 {satellite_data['name']} 可見性失敗: {e}")
            return None
    
    def _calculate_visibility_window(self, visible_points: List[SatelliteTrajectoryPoint]) -> VisibilityWindow:
        """計算可見性時間窗"""
        if not visible_points:
            return None
        
        # 找到最大仰角點
        max_elevation_point = max(visible_points, key=lambda p: p.elevation)
        
        # 計算持續時間
        start_time = datetime.fromisoformat(visible_points[0].time)
        end_time = datetime.fromisoformat(visible_points[-1].time)
        duration = (end_time - start_time).total_seconds() / 60  # 分鐘
        
        return VisibilityWindow(
            rise_time=visible_points[0].time,
            peak_time=max_elevation_point.time,
            set_time=visible_points[-1].time,
            max_elevation=max_elevation_point.elevation,
            duration_minutes=duration
        )
    
    def _calculate_signal_strength(self, trajectory_points: List[SatelliteTrajectoryPoint]) -> List[float]:
        """計算信號強度變化（基於仰角和距離）"""
        signal_strengths = []
        
        for point in trajectory_points:
            if point.visible:
                # 簡化的信號強度模型：基於仰角和距離
                # 仰角越高，信號越強；距離越近，信號越強
                elevation_factor = math.sin(math.radians(point.elevation))
                distance_factor = 1 / (point.distance_km / 1000)  # 標準化到1000km
                
                signal_strength = elevation_factor * distance_factor * 100
                signal_strength = max(0, min(100, signal_strength))  # 限制在0-100範圍
            else:
                signal_strength = 0.0
            
            signal_strengths.append(signal_strength)
        
        return signal_strengths
    
    def _calculate_handover_priority(self, visibility_window: VisibilityWindow, visible_points_count: int) -> int:
        """計算換手優先級"""
        if not visibility_window:
            return 999  # 最低優先級
        
        # 基於最大仰角和持續時間的評分
        elevation_score = visibility_window.max_elevation / 90  # 標準化到0-1
        duration_score = min(visibility_window.duration_minutes / 20, 1.0)  # 20分鐘為滿分
        
        total_score = elevation_score * 0.7 + duration_score * 0.3
        priority = int((1 - total_score) * 10) + 1  # 轉換為1-10的優先級
        
        return max(1, min(10, priority))
    
    def analyze_timeframe_coverage(self, candidate_satellites: List[Dict[str, str]],
                                 start_time_minutes: int, duration_minutes: int,
                                 observer_lat: float, observer_lon: float) -> List[SatelliteTrajectory]:
        """
        分析特定時間段的衛星覆蓋情況
        
        Args:
            candidate_satellites: 預篩選後的候選衛星
            start_time_minutes: 開始時間（相對於今天0點的分鐘數）
            duration_minutes: 持續時間 (分鐘)
            observer_lat: 觀察者緯度
            observer_lon: 觀察者經度
            
        Returns:
            該時間段內可見的衛星軌跡列表
        """
        # 計算實際開始時間
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = today + timedelta(minutes=start_time_minutes)
        
        visible_satellites = []
        
        for satellite_data in candidate_satellites:
            trajectory = self.calculate_satellite_visibility(
                satellite_data, observer_lat, observer_lon, start_time, duration_minutes
            )
            
            if trajectory:
                visible_satellites.append(trajectory)
        
        return visible_satellites
    
    def find_optimal_handover_timeframe(self, observer_lat: float, observer_lon: float,
                                      candidate_satellites: List[Dict[str, str]]) -> OptimalTimeframe:
        """
        找出30-45分鐘的最佳換手時間段
        
        Args:
            observer_lat: 觀察者緯度 (度)
            observer_lon: 觀察者經度 (度)
            candidate_satellites: 預篩選後的候選衛星
            
        Returns:
            最佳時間段配置
        """
        logger.info("開始尋找最佳換手時間段...")
        
        best_timeframe = None
        max_coverage_score = 0
        
        # 掃描96分鐘內的不同時間窗（每5分鐘檢查一次）
        for start_time_minutes in range(0, 96 * 60, 5):
            for duration in [30, 35, 40, 45]:  # 測試不同時間段長度
                if start_time_minutes + duration > 96 * 60:
                    continue
                
                logger.debug(f"分析時間段: {start_time_minutes//60:02d}:{start_time_minutes%60:02d} - {duration}分鐘")
                
                # 分析該時間段的衛星覆蓋
                timeframe_satellites = self.analyze_timeframe_coverage(
                    candidate_satellites, start_time_minutes, duration, observer_lat, observer_lon
                )
                
                if not timeframe_satellites:
                    continue
                
                # 計算覆蓋品質評分
                coverage_score = self._calculate_coverage_quality_score(timeframe_satellites, duration)
                
                # 檢查是否為最佳配置
                if (coverage_score > max_coverage_score and 
                    6 <= len(timeframe_satellites) <= 10):  # 理想衛星數量範圍
                    
                    max_coverage_score = coverage_score
                    
                    # 生成換手序列
                    handover_sequence = self._generate_handover_sequence(timeframe_satellites)
                    
                    # 計算開始時間戳
                    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                    start_timestamp = (today + timedelta(minutes=start_time_minutes)).isoformat()
                    
                    best_timeframe = OptimalTimeframe(
                        start_timestamp=start_timestamp,
                        duration_minutes=duration,
                        satellite_count=len(timeframe_satellites),
                        satellites=timeframe_satellites,
                        handover_sequence=handover_sequence,
                        coverage_quality_score=coverage_score
                    )
        
        if best_timeframe:
            logger.info(f"找到最佳時間段: {best_timeframe.start_timestamp}, "
                       f"持續 {best_timeframe.duration_minutes} 分鐘, "
                       f"{best_timeframe.satellite_count} 顆衛星, "
                       f"品質評分: {best_timeframe.coverage_quality_score:.2f}")
        else:
            logger.warning("未找到符合條件的最佳時間段")
        
        return best_timeframe
    
    def _calculate_coverage_quality_score(self, satellites: List[SatelliteTrajectory], duration_minutes: int) -> float:
        """計算覆蓋品質評分"""
        if not satellites:
            return 0.0
        
        # 評分因素：
        # 1. 衛星數量（6-10為最佳）
        # 2. 平均最大仰角
        # 3. 總覆蓋時間
        # 4. 換手連續性
        
        satellite_count = len(satellites)
        
        # 衛星數量評分
        if 6 <= satellite_count <= 10:
            count_score = 1.0
        else:
            count_score = max(0, 1 - abs(satellite_count - 8) * 0.1)
        
        # 平均最大仰角評分
        avg_max_elevation = sum(sat.visibility_window.max_elevation for sat in satellites) / satellite_count
        elevation_score = avg_max_elevation / 90  # 標準化到0-1
        
        # 總覆蓋時間評分
        total_coverage_minutes = sum(sat.visibility_window.duration_minutes for sat in satellites)
        coverage_score = min(total_coverage_minutes / (duration_minutes * 2), 1.0)  # 理想覆蓋為時間段的2倍
        
        # 換手連續性評分（時間重疊度）
        continuity_score = self._calculate_handover_continuity(satellites)
        
        # 綜合評分
        quality_score = (count_score * 0.3 + elevation_score * 0.3 + 
                        coverage_score * 0.2 + continuity_score * 0.2)
        
        return quality_score
    
    def _calculate_handover_continuity(self, satellites: List[SatelliteTrajectory]) -> float:
        """計算換手連續性評分"""
        if len(satellites) < 2:
            return 0.0
        
        # 按優先級排序衛星
        sorted_satellites = sorted(satellites, key=lambda s: s.handover_priority)
        
        overlap_count = 0
        total_transitions = len(sorted_satellites) - 1
        
        for i in range(total_transitions):
            current_sat = sorted_satellites[i]
            next_sat = sorted_satellites[i + 1]
            
            current_end = datetime.fromisoformat(current_sat.visibility_window.set_time)
            next_start = datetime.fromisoformat(next_sat.visibility_window.rise_time)
            
            # 檢查是否有時間重疊或接近（允許5分鐘間隔）
            if (current_end >= next_start or 
                (next_start - current_end).total_seconds() <= 300):
                overlap_count += 1
        
        return overlap_count / total_transitions if total_transitions > 0 else 0.0
    
    def _generate_handover_sequence(self, satellites: List[SatelliteTrajectory]) -> List[Dict[str, Any]]:
        """生成換手序列"""
        # 按優先級排序
        sorted_satellites = sorted(satellites, key=lambda s: s.handover_priority)
        
        handover_sequence = []
        
        for i in range(len(sorted_satellites) - 1):
            from_sat = sorted_satellites[i]
            to_sat = sorted_satellites[i + 1]
            
            # 計算換手時間（當前衛星設定時間和下一衛星升起時間的中點）
            from_set_time = datetime.fromisoformat(from_sat.visibility_window.set_time)
            to_rise_time = datetime.fromisoformat(to_sat.visibility_window.rise_time)
            
            if from_set_time < to_rise_time:
                handover_time = from_set_time + (to_rise_time - from_set_time) / 2
            else:
                handover_time = to_rise_time
            
            # 計算信號重疊時間
            overlap_duration = max(0, (from_set_time - to_rise_time).total_seconds())
            
            handover_sequence.append({
                'sequence_id': i + 1,
                'from_satellite': from_sat.name,
                'to_satellite': to_sat.name,
                'handover_time': handover_time.isoformat(),
                'handover_type': 'planned' if overlap_duration > 0 else 'immediate',
                'signal_overlap_duration': overlap_duration
            })
        
        return handover_sequence


async def main():
    """測試最佳時間段分析器"""
    from .starlink_tle_downloader import StarlinkTLEDownloader
    from .satellite_prefilter import SatellitePrefilter, ObserverLocation
    
    # NTPU 座標
    observer_lat = 24.9441667
    observer_lon = 121.3713889
    
    logger.info("=== Phase 0.3: 最佳時間段分析測試 ===")
    
    # 下載 TLE 數據
    downloader = StarlinkTLEDownloader()
    satellites = await downloader.get_starlink_tle_data()
    
    if not satellites:
        logger.error("無法獲取 Starlink 數據")
        return
    
    # 預篩選
    observer = ObserverLocation(observer_lat, observer_lon)
    prefilter = SatellitePrefilter()
    candidate_satellites, _ = prefilter.pre_filter_satellites_by_orbit(observer, satellites)
    
    # 分析最佳時間段
    analyzer = OptimalTimeframeAnalyzer()
    optimal_timeframe = analyzer.find_optimal_handover_timeframe(
        observer_lat, observer_lon, candidate_satellites[:100]  # 限制數量以加速測試
    )
    
    if optimal_timeframe:
        print(f"\n=== 最佳時間段 ===")
        print(f"開始時間: {optimal_timeframe.start_timestamp}")
        print(f"持續時間: {optimal_timeframe.duration_minutes} 分鐘")
        print(f"衛星數量: {optimal_timeframe.satellite_count}")
        print(f"品質評分: {optimal_timeframe.coverage_quality_score:.2f}")
        print(f"換手序列數量: {len(optimal_timeframe.handover_sequence)}")
        
        for sat in optimal_timeframe.satellites[:3]:  # 顯示前3顆衛星
            print(f"\n衛星: {sat.name}")
            print(f"  最大仰角: {sat.visibility_window.max_elevation:.1f}°")
            print(f"  持續時間: {sat.visibility_window.duration_minutes:.1f} 分鐘")
            print(f"  換手優先級: {sat.handover_priority}")
    else:
        print("未找到最佳時間段")


if __name__ == "__main__":
    asyncio.run(main())