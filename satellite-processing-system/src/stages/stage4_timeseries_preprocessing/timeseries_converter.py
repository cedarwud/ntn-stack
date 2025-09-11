"""
時間序列轉換器 - Stage 3模組化組件

職責：
1. 將可見性數據轉換為時間序列格式
2. 創建動畫所需的時序結構
3. 進行時間標準化和同步
4. 生成前端友善的數據格式
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class TimeseriesConverter:
    """時間序列轉換器 - 將可見性數據轉換為動畫時序格式"""
    
    def __init__(self, time_resolution: int = 30, animation_fps: int = 24):
        """
        初始化時間序列轉換器
        
        Args:
            time_resolution: 時間解析度（秒）
            animation_fps: 動畫幀率
        """
        self.logger = logging.getLogger(f"{__name__}.TimeseriesConverter")
        
        self.time_resolution = time_resolution
        self.animation_fps = animation_fps
        
        # 轉換統計
        self.conversion_statistics = {
            "total_satellites_processed": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "total_timeseries_points": 0,
            "total_animation_frames": 0
        }
        
        self.logger.info("✅ 時間序列轉換器初始化完成")
        self.logger.info(f"   時間解析度: {time_resolution}秒")
        self.logger.info(f"   動畫幀率: {animation_fps}fps")
    
    def convert_visibility_to_timeseries(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        將可見性數據轉換為時間序列格式
        
        Args:
            satellites: 含可見性數據的衛星列表
            
        Returns:
            時間序列轉換結果
        """
        self.logger.info(f"🔄 開始轉換 {len(satellites)} 顆衛星的時間序列數據...")
        
        self.conversion_statistics["total_satellites_processed"] = len(satellites)
        
        converted_satellites = []
        total_frames = 0
        total_points = 0
        
        for satellite in satellites:
            try:
                converted_sat = self._convert_single_satellite_timeseries(satellite)
                
                if converted_sat:
                    converted_satellites.append(converted_sat)
                    self.conversion_statistics["successful_conversions"] += 1
                    
                    # 統計數據點和幀數
                    timeseries = converted_sat.get("timeseries", [])
                    total_points += len(timeseries)
                    
                    animation_frames = converted_sat.get("animation_frames", 0)
                    total_frames += animation_frames
                    
                else:
                    self.conversion_statistics["failed_conversions"] += 1
                    
            except Exception as e:
                self.logger.error(f"轉換衛星 {satellite.get('name', 'unknown')} 時間序列失敗: {e}")
                self.conversion_statistics["failed_conversions"] += 1
                continue
        
        self.conversion_statistics.update({
            "total_timeseries_points": total_points,
            "total_animation_frames": total_frames
        })
        
        conversion_result = {
            "satellites": converted_satellites,
            "conversion_metadata": {
                "time_resolution_seconds": self.time_resolution,
                "animation_fps": self.animation_fps,
                "total_satellites": len(converted_satellites),
                "conversion_timestamp": datetime.now(timezone.utc).isoformat()
            },
            "conversion_statistics": self.conversion_statistics.copy()
        }
        
        self.logger.info(f"✅ 時間序列轉換完成: {self.conversion_statistics['successful_conversions']}/{len(satellites)} 成功")
        
        return conversion_result
    
    def _convert_single_satellite_timeseries(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """轉換單顆衛星的時間序列"""
        
        position_timeseries = satellite.get("position_timeseries", [])
        if not position_timeseries:
            return None
        
        # 轉換位置時間序列為標準化格式
        standardized_timeseries = self._standardize_timeseries(position_timeseries)
        
        # 創建動畫軌跡數據
        animation_trajectory = self._create_animation_trajectory(standardized_timeseries)
        
        # 生成信號品質時間線
        signal_timeline = self._generate_signal_timeline(
            standardized_timeseries, 
            satellite.get("visibility_summary", {})
        )
        
        # 計算動畫幀數
        animation_frames = len(standardized_timeseries)
        
        # 構建轉換後的衛星數據
        converted_satellite = {
            **satellite,  # 保留原始數據
            
            # 標準化時間序列
            "timeseries": standardized_timeseries,
            
            # 動畫相關數據
            "animation_trajectory": animation_trajectory,
            "signal_timeline": signal_timeline,
            "animation_frames": animation_frames,
            
            # 時序統計
            "timeseries_statistics": self._calculate_timeseries_statistics(standardized_timeseries),
            
            # 動畫元數據
            "animation_metadata": {
                "trajectory_type": self._determine_trajectory_type(standardized_timeseries),
                "visibility_duration_frames": len([p for p in standardized_timeseries if p.get("is_visible", False)]),
                "max_elevation_frame": self._find_max_elevation_frame(standardized_timeseries),
                "animation_quality": self._assess_animation_quality(standardized_timeseries)
            }
        }
        
        return converted_satellite
    
    def _standardize_timeseries(self, position_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """標準化時間序列格式"""
        
        standardized_points = []
        
        for i, point in enumerate(position_timeseries):
            try:
                # 標準化時間
                time_offset = i * self.time_resolution  # 相對時間偏移（秒）
                frame_number = int(time_offset * self.animation_fps / 60)  # 動畫幀號
                
                # 標準化位置數據
                standardized_point = {
                    "time_index": i,
                    "time_offset_seconds": time_offset,
                    "frame_number": frame_number,
                    "timestamp": point.get("timestamp", f"T+{time_offset}s"),
                    
                    # 基本位置
                    "latitude": float(point.get("latitude", 0.0)),
                    "longitude": float(point.get("longitude", 0.0)),
                    "altitude_km": float(point.get("altitude_km", 0.0)),
                    "velocity_kmps": float(point.get("velocity_kmps", 0.0)),
                    
                    # 可見性數據
                    "is_visible": point.get("relative_to_observer", {}).get("is_visible", False),
                    "elevation_deg": float(point.get("relative_to_observer", {}).get("elevation_deg", -90)),
                    "azimuth_deg": float(point.get("relative_to_observer", {}).get("azimuth_deg", 0)),
                    "range_km": float(point.get("relative_to_observer", {}).get("range_km", 0))
                }
                
                # 如果有ECI坐標
                if "eci" in point:
                    eci = point["eci"]
                    standardized_point["eci"] = {
                        "x": float(eci.get("x", 0.0)),
                        "y": float(eci.get("y", 0.0)),
                        "z": float(eci.get("z", 0.0))
                    }
                
                # 如果有品質評級
                if "elevation_quality" in point:
                    standardized_point["elevation_quality"] = point["elevation_quality"]
                
                standardized_points.append(standardized_point)
                
            except Exception as e:
                self.logger.warning(f"標準化時間序列點 {i} 時出錯: {e}")
                continue
        
        return standardized_points
    
    def _create_animation_trajectory(self, timeseries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """創建動畫軌跡數據"""
        
        if not timeseries:
            return {"trajectory_points": [], "trajectory_type": "empty"}
        
        trajectory_points = []
        
        for point in timeseries:
            trajectory_point = {
                "frame": point["frame_number"],
                "position": {
                    "lat": point["latitude"],
                    "lon": point["longitude"],
                    "alt": point["altitude_km"]
                },
                "visibility": {
                    "is_visible": point["is_visible"],
                    "elevation": point["elevation_deg"],
                    "azimuth": point["azimuth_deg"]
                },
                "motion": {
                    "velocity": point["velocity_kmps"],
                    "range": point["range_km"]
                }
            }
            
            trajectory_points.append(trajectory_point)
        
        # 計算軌跡特徵
        visible_points = [p for p in timeseries if p["is_visible"]]
        
        trajectory = {
            "trajectory_points": trajectory_points,
            "trajectory_type": self._determine_trajectory_type(timeseries),
            "total_frames": len(trajectory_points),
            "visible_frames": len(visible_points),
            "visibility_ratio": len(visible_points) / len(trajectory_points) if trajectory_points else 0
        }
        
        if visible_points:
            trajectory["peak_elevation"] = max(p["elevation_deg"] for p in visible_points)
            trajectory["peak_frame"] = next(
                (i for i, p in enumerate(timeseries) 
                 if p["is_visible"] and p["elevation_deg"] == trajectory["peak_elevation"]), 0
            )
        
        return trajectory
    
    def _generate_signal_timeline(self, timeseries: List[Dict[str, Any]], 
                                visibility_summary: Dict[str, Any]) -> Dict[str, Any]:
        """生成信號品質時間線"""
        
        if not timeseries:
            return {"signal_points": [], "quality_profile": "no_data"}
        
        signal_points = []
        
        for point in timeseries:
            # 基於仰角估算信號品質
            elevation = point["elevation_deg"]
            signal_quality = self._estimate_signal_quality(elevation, point["range_km"])
            
            signal_point = {
                "frame": point["frame_number"],
                "time_offset": point["time_offset_seconds"],
                "signal_strength": signal_quality["rsrp_dbm"],
                "signal_quality": signal_quality["quality_level"],
                "elevation_deg": elevation,
                "is_above_threshold": elevation > 10  # ITU-R標準
            }
            
            signal_points.append(signal_point)
        
        # 分析信號品質概況
        visible_signals = [p for p in signal_points if p["is_above_threshold"]]
        
        timeline = {
            "signal_points": signal_points,
            "quality_profile": self._assess_signal_quality_profile(signal_points),
            "signal_statistics": {
                "total_points": len(signal_points),
                "points_above_threshold": len(visible_signals),
                "signal_availability_ratio": len(visible_signals) / len(signal_points) if signal_points else 0
            }
        }
        
        if visible_signals:
            timeline["signal_statistics"].update({
                "max_signal_strength": max(p["signal_strength"] for p in visible_signals),
                "min_signal_strength": min(p["signal_strength"] for p in visible_signals),
                "avg_signal_strength": sum(p["signal_strength"] for p in visible_signals) / len(visible_signals)
            })
        
        return timeline
    
    def _estimate_signal_quality(self, elevation_deg: float, range_km: float) -> Dict[str, Any]:
        """基於仰角和距離估算信號品質"""
        
        # 使用學術級信號傳播模型（Friis公式變形）
        if elevation_deg <= 0:
            return {
                "rsrp_dbm": -140,  # 最低信號強度
                "quality_level": "no_signal"
            }
        
        # 基本自由空間路徑損耗（28GHz頻段）
        frequency_hz = 28e9
        c = 3e8  # 光速
        wavelength = c / frequency_hz
        
        # 路徑損耗計算
        range_m = range_km * 1000
        path_loss_db = 20 * math.log10(4 * math.pi * range_m / wavelength)
        
        # 大氣衰減（基於仰角）
        atmosphere_loss_db = max(0, 5 * (1 / math.sin(math.radians(max(elevation_deg, 1)))) - 5)
        
        # 假設衛星EIRP為55dBm（典型LEO衛星）
        satellite_eirp_dbm = 55
        
        # 接收信號功率
        rsrp_dbm = satellite_eirp_dbm - path_loss_db - atmosphere_loss_db
        
        # 確保在合理範圍內
        rsrp_dbm = max(-140, min(-50, rsrp_dbm))
        
        # 品質等級評估
        if rsrp_dbm >= -80:
            quality_level = "excellent"
        elif rsrp_dbm >= -90:
            quality_level = "good"
        elif rsrp_dbm >= -110:
            quality_level = "fair"
        elif rsrp_dbm >= -130:
            quality_level = "poor"
        else:
            quality_level = "very_poor"
        
        return {
            "rsrp_dbm": round(rsrp_dbm, 1),
            "quality_level": quality_level,
            "path_loss_db": round(path_loss_db, 1),
            "atmosphere_loss_db": round(atmosphere_loss_db, 1)
        }
    
    def _determine_trajectory_type(self, timeseries: List[Dict[str, Any]]) -> str:
        """判斷軌跡類型"""
        
        if len(timeseries) < 3:
            return "insufficient_data"
        
        visible_points = [p for p in timeseries if p["is_visible"]]
        
        if not visible_points:
            return "not_visible"
        
        if len(visible_points) < 3:
            return "brief_pass"
        
        # 分析仰角變化模式
        elevations = [p["elevation_deg"] for p in visible_points]
        
        # 找到最高點
        max_elevation = max(elevations)
        max_index = elevations.index(max_elevation)
        
        # 檢查是否為過境軌跡
        if max_index > 0 and max_index < len(elevations) - 1:
            # 檢查上升和下降趨勢
            rising_trend = all(elevations[i] <= elevations[i+1] for i in range(max_index))
            falling_trend = all(elevations[i] >= elevations[i+1] for i in range(max_index, len(elevations)-1))
            
            if rising_trend and falling_trend:
                return "complete_transit"
        
        # 其他軌跡類型
        if max_index == 0:
            return "setting_pass"
        elif max_index == len(elevations) - 1:
            return "rising_pass"
        else:
            return "partial_transit"
    
    def _find_max_elevation_frame(self, timeseries: List[Dict[str, Any]]) -> int:
        """找到最大仰角對應的幀號"""
        
        visible_points = [(i, p) for i, p in enumerate(timeseries) if p["is_visible"]]
        
        if not visible_points:
            return 0
        
        max_elevation_index, max_point = max(visible_points, key=lambda x: x[1]["elevation_deg"])
        return max_point["frame_number"]
    
    def _assess_animation_quality(self, timeseries: List[Dict[str, Any]]) -> str:
        """評估動畫品質"""
        
        visible_points = [p for p in timeseries if p["is_visible"]]
        
        if not visible_points:
            return "no_visibility"
        
        visibility_duration = len(visible_points)
        max_elevation = max(p["elevation_deg"] for p in visible_points)
        
        if max_elevation >= 60 and visibility_duration >= 100:
            return "excellent"
        elif max_elevation >= 45 and visibility_duration >= 60:
            return "good"
        elif max_elevation >= 30 and visibility_duration >= 30:
            return "fair"
        elif max_elevation >= 15 and visibility_duration >= 10:
            return "poor"
        else:
            return "very_poor"
    
    def _assess_signal_quality_profile(self, signal_points: List[Dict[str, Any]]) -> str:
        """評估信號品質概況"""
        
        above_threshold = [p for p in signal_points if p["is_above_threshold"]]
        
        if not above_threshold:
            return "no_signal"
        
        avg_strength = sum(p["signal_strength"] for p in above_threshold) / len(above_threshold)
        
        if avg_strength >= -80:
            return "high_quality"
        elif avg_strength >= -100:
            return "medium_quality"
        elif avg_strength >= -120:
            return "low_quality"
        else:
            return "very_low_quality"
    
    def _calculate_timeseries_statistics(self, timeseries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算時間序列統計信息"""
        
        if not timeseries:
            return {"total_points": 0, "visible_points": 0}
        
        visible_points = [p for p in timeseries if p["is_visible"]]
        
        stats = {
            "total_points": len(timeseries),
            "visible_points": len(visible_points),
            "visibility_ratio": len(visible_points) / len(timeseries),
            "total_duration_seconds": len(timeseries) * self.time_resolution,
            "visible_duration_seconds": len(visible_points) * self.time_resolution,
            "animation_frames": len(timeseries)
        }
        
        if visible_points:
            elevations = [p["elevation_deg"] for p in visible_points]
            ranges = [p["range_km"] for p in visible_points]
            
            stats.update({
                "max_elevation_deg": max(elevations),
                "min_elevation_deg": min(elevations),
                "avg_elevation_deg": sum(elevations) / len(elevations),
                "min_range_km": min(ranges),
                "max_range_km": max(ranges),
                "avg_range_km": sum(ranges) / len(ranges)
            })
        
        return stats
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """獲取轉換統計信息"""
        return self.conversion_statistics.copy()
    
    def validate_timeseries_conversion(self, conversion_result: Dict[str, Any]) -> Dict[str, Any]:
        """驗證時間序列轉換結果"""
        
        validation_result = {
            "passed": True,
            "total_satellites": len(conversion_result.get("satellites", [])),
            "validation_checks": {},
            "issues": []
        }
        
        satellites = conversion_result.get("satellites", [])
        
        if not satellites:
            validation_result["passed"] = False
            validation_result["issues"].append("無時間序列轉換結果")
            return validation_result
        
        # 檢查時間序列完整性
        satellites_with_timeseries = 0
        satellites_with_trajectories = 0
        
        for sat in satellites:
            timeseries = sat.get("timeseries", [])
            trajectory = sat.get("animation_trajectory", {})
            
            if timeseries:
                satellites_with_timeseries += 1
            
            if trajectory and trajectory.get("trajectory_points"):
                satellites_with_trajectories += 1
        
        validation_result["validation_checks"]["timeseries_integrity_check"] = {
            "satellites_with_timeseries": satellites_with_timeseries,
            "satellites_with_trajectories": satellites_with_trajectories,
            "passed": satellites_with_timeseries == len(satellites) and satellites_with_trajectories == len(satellites)
        }
        
        if satellites_with_timeseries < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_timeseries} 顆衛星缺少時間序列數據")
        
        if satellites_with_trajectories < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_trajectories} 顆衛星缺少動畫軌跡")
        
        return validation_result