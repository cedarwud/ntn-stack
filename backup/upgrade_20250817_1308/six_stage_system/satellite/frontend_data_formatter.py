#!/usr/bin/env python3
"""
前端數據源格式化器 - Phase 0 Implementation
將最佳時間段數據格式化為側邊欄和立體圖動畫所需的數據源

功能:
1. 側邊欄「衛星 gNB」數據源
2. 立體圖動畫軌跡數據源  
3. 換手序列展示數據
4. 支援任意座標的相同分析
"""

import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .optimal_timeframe_analyzer import OptimalTimeframe, SatelliteTrajectory


logger = logging.getLogger(__name__)


class FrontendDataFormatter:
    """前端數據源格式化器"""
    
    def __init__(self):
        """初始化格式化器"""
        pass
    
    def format_sidebar_satellite_list(self, optimal_timeframe: OptimalTimeframe) -> Dict[str, Any]:
        """
        格式化側邊欄「衛星 gNB」數據源
        
        Args:
            optimal_timeframe: 最佳時間段數據
            
        Returns:
            側邊欄數據源
        """
        satellite_gnb_list = []
        
        for satellite in optimal_timeframe.satellites:
            # 計算當前狀態（基於時間段開始時的狀態）
            current_trajectory_point = satellite.trajectory[0] if satellite.trajectory else None
            
            if current_trajectory_point:
                # 計算信號強度（基於仰角和距離）
                signal_strength = self._calculate_signal_strength_percentage(
                    current_trajectory_point.elevation,
                    current_trajectory_point.distance_km
                )
                
                # 格式化可用性時間窗
                availability_window = self._format_time_window(satellite.visibility_window)
                
                satellite_info = {
                    "id": f"STARLINK-{satellite.norad_id}",
                    "name": satellite.name,
                    "status": "visible" if current_trajectory_point.visible else "approaching",
                    "signal_strength": signal_strength,
                    "elevation": round(current_trajectory_point.elevation, 1),
                    "azimuth": round(current_trajectory_point.azimuth, 1),
                    "distance_km": round(current_trajectory_point.distance_km, 1),
                    "handover_priority": satellite.handover_priority,
                    "availability_window": availability_window,
                    "max_elevation": round(satellite.visibility_window.max_elevation, 1),
                    "duration_minutes": round(satellite.visibility_window.duration_minutes, 1)
                }
                
                satellite_gnb_list.append(satellite_info)
        
        # 按換手優先級排序
        satellite_gnb_list.sort(key=lambda x: x["handover_priority"])
        
        return {
            "satellite_gnb_list": satellite_gnb_list,
            "metadata": {
                "total_satellites": len(satellite_gnb_list),
                "timeframe_start": optimal_timeframe.start_timestamp,
                "timeframe_duration": optimal_timeframe.duration_minutes,
                "coverage_quality": round(optimal_timeframe.coverage_quality_score, 2)
            }
        }
    
    def format_3d_animation_trajectories(self, optimal_timeframe: OptimalTimeframe,
                                       observer_lat: float, observer_lon: float) -> Dict[str, Any]:
        """
        格式化立體圖動畫軌跡數據源
        
        Args:
            optimal_timeframe: 最佳時間段數據
            observer_lat: 觀察者緯度
            observer_lon: 觀察者經度
            
        Returns:
            動畫軌跡數據源
        """
        animation_trajectories = []
        
        for satellite in optimal_timeframe.satellites:
            # 轉換軌跡點為3D座標
            trajectory_points = []
            
            for i, point in enumerate(satellite.trajectory):
                # 計算3D位置（相對於觀察者的極座標系統）
                x, y, z = self._convert_to_3d_coordinates(
                    point.elevation, point.azimuth, point.distance_km,
                    observer_lat, observer_lon
                )
                
                trajectory_point = {
                    "time_offset": i * 30,  # 30秒間隔
                    "x": round(x, 2),
                    "y": round(y, 2), 
                    "z": round(z, 2),
                    "visible": point.visible,
                    "elevation": round(point.elevation, 1),
                    "azimuth": round(point.azimuth, 1),
                    "signal_strength": satellite.signal_strength_profile[i] if i < len(satellite.signal_strength_profile) else 0
                }
                
                trajectory_points.append(trajectory_point)
            
            # 選擇軌跡顏色（基於優先級）
            color = self._get_satellite_color(satellite.handover_priority)
            
            trajectory_data = {
                "satellite_id": f"STARLINK-{satellite.norad_id}",
                "satellite_name": satellite.name,
                "trajectory_points": trajectory_points,
                "animation_config": {
                    "color": color,
                    "trail_length": 10,  # 軌跡拖尾長度
                    "visibility_threshold": 5.0,  # 可見性閾值
                    "priority": satellite.handover_priority,
                    "max_elevation": satellite.visibility_window.max_elevation
                }
            }
            
            animation_trajectories.append(trajectory_data)
        
        # 計算動畫設置
        total_points = len(optimal_timeframe.satellites[0].trajectory) if optimal_timeframe.satellites else 0
        total_duration_seconds = total_points * 30  # 30秒間隔
        
        animation_settings = {
            "total_duration_seconds": total_duration_seconds,
            "playback_speed_multiplier": 10,  # 10倍速播放
            "camera_follow_mode": "overview",
            "time_step_seconds": 30,
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "name": "NTPU"
            }
        }
        
        return {
            "animation_trajectories": animation_trajectories,
            "animation_settings": animation_settings,
            "metadata": {
                "timeframe_info": {
                    "start_time": optimal_timeframe.start_timestamp,
                    "duration_minutes": optimal_timeframe.duration_minutes,
                    "satellite_count": optimal_timeframe.satellite_count
                }
            }
        }
    
    def format_handover_sequence(self, optimal_timeframe: OptimalTimeframe) -> Dict[str, Any]:
        """
        格式化換手序列展示數據
        
        Args:
            optimal_timeframe: 最佳時間段數據
            
        Returns:
            換手序列數據
        """
        handover_sequence = []
        
        for handover in optimal_timeframe.handover_sequence:
            # 計算換手品質評分
            quality_score = self._calculate_handover_quality(handover, optimal_timeframe.satellites)
            
            handover_event = {
                "sequence_id": handover["sequence_id"],
                "from_satellite": handover["from_satellite"],
                "to_satellite": handover["to_satellite"],
                "handover_time": handover["handover_time"],
                "handover_type": handover["handover_type"],
                "signal_overlap_duration": round(handover["signal_overlap_duration"], 1),
                "quality_score": quality_score,
                "timing_analysis": self._analyze_handover_timing(handover, optimal_timeframe.satellites)
            }
            
            handover_sequence.append(handover_event)
        
        # 計算整體換手序列統計
        total_handovers = len(handover_sequence)
        avg_overlap = sum(h["signal_overlap_duration"] for h in handover_sequence) / total_handovers if total_handovers > 0 else 0
        seamless_handovers = sum(1 for h in handover_sequence if h["handover_type"] == "planned")
        
        return {
            "handover_sequence": handover_sequence,
            "sequence_statistics": {
                "total_handovers": total_handovers,
                "seamless_handovers": seamless_handovers,
                "seamless_percentage": round(seamless_handovers / total_handovers * 100, 1) if total_handovers > 0 else 0,
                "average_overlap_duration": round(avg_overlap, 1),
                "sequence_quality": self._calculate_sequence_quality(handover_sequence)
            }
        }
    
    def format_for_frontend_display(self, optimal_timeframe: OptimalTimeframe,
                                   observer_location: Dict[str, float]) -> Dict[str, Any]:
        """
        格式化數據以支援前端展示需求
        
        Args:
            optimal_timeframe: 最佳時間段數據
            observer_location: 觀察者位置 {"lat": float, "lon": float}
            
        Returns:
            完整的前端數據源
        """
        observer_lat = observer_location["lat"]
        observer_lon = observer_location["lon"]
        
        # 格式化各個數據源
        sidebar_data = self.format_sidebar_satellite_list(optimal_timeframe)
        animation_data = self.format_3d_animation_trajectories(optimal_timeframe, observer_lat, observer_lon)
        handover_sequence_data = self.format_handover_sequence(optimal_timeframe)
        
        return {
            "sidebar_data": sidebar_data,
            "animation_data": animation_data,
            "handover_sequence": handover_sequence_data,
            "metadata": {
                "observer_location": observer_location,
                "timeframe_info": asdict(optimal_timeframe),
                "generation_time": datetime.now(timezone.utc).isoformat(),
                "data_format_version": "1.0"
            }
        }
    
    def _calculate_signal_strength_percentage(self, elevation: float, distance_km: float) -> int:
        """計算信號強度百分比"""
        if elevation < 5:
            return 0
        
        # 基於仰角和距離的簡化信號強度模型
        elevation_factor = math.sin(math.radians(elevation))
        distance_factor = 1 / (distance_km / 1000)  # 標準化到1000km
        
        signal_strength = elevation_factor * distance_factor * 100
        return max(0, min(100, int(signal_strength)))
    
    def _format_time_window(self, visibility_window) -> str:
        """格式化時間窗顯示"""
        try:
            rise_time = datetime.fromisoformat(visibility_window.rise_time)
            set_time = datetime.fromisoformat(visibility_window.set_time)
            
            rise_str = rise_time.strftime("%H:%M:%S")
            set_str = set_time.strftime("%H:%M:%S")
            
            return f"{rise_str} - {set_str}"
        except:
            return "Unknown"
    
    def _convert_to_3d_coordinates(self, elevation: float, azimuth: float, distance_km: float,
                                 observer_lat: float, observer_lon: float) -> tuple:
        """轉換為3D座標系統"""
        # 轉換為弧度
        elev_rad = math.radians(elevation)
        azim_rad = math.radians(azimuth)
        
        # 極座標轉笛卡爾座標
        # x: 東西方向（東為正）
        # y: 南北方向（北為正） 
        # z: 高度方向（上為正）
        
        horizontal_distance = distance_km * math.cos(elev_rad)
        
        x = horizontal_distance * math.sin(azim_rad)   # 東西
        y = horizontal_distance * math.cos(azim_rad)   # 南北
        z = distance_km * math.sin(elev_rad)           # 高度
        
        return x, y, z
    
    def _get_satellite_color(self, priority: int) -> str:
        """根據優先級獲取衛星顏色"""
        color_map = {
            1: "#ff0000",  # 紅色 - 最高優先級
            2: "#ff6600",  # 橙紅色
            3: "#ff9900",  # 橙色
            4: "#ffcc00",  # 黃橙色
            5: "#ffff00",  # 黃色
            6: "#ccff00",  # 黃綠色
            7: "#99ff00",  # 綠黃色
            8: "#66ff00",  # 綠色
            9: "#33ff00",  # 亮綠色
            10: "#00ff00"  # 純綠色 - 最低優先級
        }
        return color_map.get(priority, "#888888")  # 默認灰色
    
    def _calculate_handover_quality(self, handover: Dict[str, Any], satellites: List[SatelliteTrajectory]) -> float:
        """計算換手品質評分"""
        # 基於信號重疊時間和換手類型的評分
        overlap_duration = handover["signal_overlap_duration"]
        handover_type = handover["handover_type"]
        
        # 重疊時間評分（120秒為滿分）
        overlap_score = min(overlap_duration / 120, 1.0)
        
        # 換手類型評分
        type_score = 1.0 if handover_type == "planned" else 0.5
        
        # 綜合評分
        quality_score = (overlap_score * 0.7 + type_score * 0.3) * 100
        
        return round(quality_score, 1)
    
    def _analyze_handover_timing(self, handover: Dict[str, Any], satellites: List[SatelliteTrajectory]) -> Dict[str, Any]:
        """分析換手時機"""
        from_sat_name = handover["from_satellite"]
        to_sat_name = handover["to_satellite"]
        
        # 找到對應的衛星
        from_sat = next((s for s in satellites if s.name == from_sat_name), None)
        to_sat = next((s for s in satellites if s.name == to_sat_name), None)
        
        if not from_sat or not to_sat:
            return {"timing_quality": "unknown"}
        
        # 分析時機品質
        overlap_duration = handover["signal_overlap_duration"]
        
        if overlap_duration > 60:
            timing_quality = "excellent"
        elif overlap_duration > 30:
            timing_quality = "good"
        elif overlap_duration > 0:
            timing_quality = "fair"
        else:
            timing_quality = "poor"
        
        return {
            "timing_quality": timing_quality,
            "from_satellite_max_elevation": from_sat.visibility_window.max_elevation,
            "to_satellite_max_elevation": to_sat.visibility_window.max_elevation,
            "elevation_difference": abs(from_sat.visibility_window.max_elevation - to_sat.visibility_window.max_elevation)
        }
    
    def _calculate_sequence_quality(self, handover_sequence: List[Dict[str, Any]]) -> float:
        """計算整體序列品質"""
        if not handover_sequence:
            return 0.0
        
        total_quality = sum(h["quality_score"] for h in handover_sequence)
        average_quality = total_quality / len(handover_sequence)
        
        return round(average_quality, 1)


def generate_optimal_timeframe_for_coordinates(lat: float, lon: float, alt: float = 0) -> Dict[str, Any]:
    """
    對任意座標執行相同的最佳時間段分析
    
    Args:
        lat: 緯度 (度)
        lon: 經度 (度)  
        alt: 海拔高度 (米)
        
    Returns:
        完整的分析結果和前端數據源
    """
    import asyncio
    from .starlink_tle_downloader import StarlinkTLEDownloader
    from .satellite_prefilter import SatellitePrefilter, ObserverLocation
    from .optimal_timeframe_analyzer import OptimalTimeframeAnalyzer
    
    async def analyze_coordinates():
        logger.info(f"開始分析座標 ({lat}, {lon}) 的最佳時間段...")
        
        # 下載 TLE 數據
        downloader = StarlinkTLEDownloader()
        satellites = await downloader.get_starlink_tle_data()
        
        if not satellites:
            return None
        
        # 預篩選候選衛星
        observer = ObserverLocation(lat, lon, alt)
        prefilter = SatellitePrefilter()
        candidate_satellites, excluded_satellites = prefilter.pre_filter_satellites_by_orbit(observer, satellites)
        
        # 分析最佳時間段
        analyzer = OptimalTimeframeAnalyzer()
        optimal_timeframe = analyzer.find_optimal_handover_timeframe(lat, lon, candidate_satellites)
        
        if not optimal_timeframe:
            return None
        
        # 格式化前端數據
        formatter = FrontendDataFormatter()
        frontend_data = formatter.format_for_frontend_display(
            optimal_timeframe, {"lat": lat, "lon": lon}
        )
        
        return {
            "coordinates": {"lat": lat, "lon": lon, "alt": alt},
            "optimal_timeframe": asdict(optimal_timeframe),
            "frontend_data": frontend_data,
            "statistics": {
                "total_satellites_analyzed": len(satellites),
                "candidate_satellites": len(candidate_satellites),
                "excluded_satellites": len(excluded_satellites),
                "reduction_ratio": len(excluded_satellites) / len(satellites) * 100
            }
        }
    
    return asyncio.run(analyze_coordinates())


def main():
    """測試前端數據格式化器"""
    # 測試任意座標分析
    result = generate_optimal_timeframe_for_coordinates(24.9441667, 121.3713889)
    
    if result:
        print("=== 座標分析結果 ===")
        print(f"座標: {result['coordinates']}")
        print(f"最佳時間段: {result['optimal_timeframe']['start_timestamp']}")
        print(f"衛星數量: {result['optimal_timeframe']['satellite_count']}")
        print(f"品質評分: {result['optimal_timeframe']['coverage_quality_score']}")
        print(f"前端數據源已生成: {len(result['frontend_data'])} 個數據源")
    else:
        print("分析失敗")


if __name__ == "__main__":
    main()