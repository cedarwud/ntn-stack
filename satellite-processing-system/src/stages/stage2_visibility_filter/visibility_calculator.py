"""
可見性計算引擎 - Stage 2模組化組件

職責：
1. 基於觀測點計算衛星相對位置
2. 計算仰角、方位角和距離
3. 判斷衛星地理可見性
4. 使用學術級標準的計算方法
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class VisibilityCalculator:
    """衛星可見性計算引擎 - 基於學術級標準"""
    
    def __init__(self, observer_coordinates: Tuple[float, float, float] = (24.9441667, 121.3713889, 50)):
        """
        初始化可見性計算引擎
        
        Args:
            observer_coordinates: 觀測點坐標 (緯度, 經度, 海拔m)，預設為NTPU
        """
        self.logger = logging.getLogger(f"{__name__}.VisibilityCalculator")
        
        self.observer_lat = observer_coordinates[0]  # 緯度 (度)
        self.observer_lon = observer_coordinates[1]  # 經度 (度) 
        self.observer_alt = observer_coordinates[2]  # 海拔 (米)
        
        self.logger.info(f"✅ 可見性計算引擎初始化成功")
        self.logger.info(f"   觀測點: 緯度={self.observer_lat:.6f}°, 經度={self.observer_lon:.6f}°, 海拔={self.observer_alt}m")
        
        # 計算統計
        self.calculation_statistics = {
            "total_satellites": 0,
            "satellites_with_visibility": 0,
            "total_position_calculations": 0,
            "visible_position_calculations": 0
        }
        
        # 地球參數 (WGS84)
        self.EARTH_RADIUS_KM = 6371.0  # 平均半徑
        self.DEG_TO_RAD = math.pi / 180.0
        self.RAD_TO_DEG = 180.0 / math.pi
    
    def calculate_satellite_visibility(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算所有衛星的可見性
        
        Args:
            satellites: 衛星軌道數據列表
            
        Returns:
            包含可見性計算結果的數據
        """
        self.logger.info(f"🔭 開始計算 {len(satellites)} 顆衛星的可見性...")
        
        self.calculation_statistics["total_satellites"] = len(satellites)
        
        visibility_results = {
            "satellites": [],
            "calculation_metadata": {
                "observer_coordinates": {
                    "latitude": self.observer_lat,
                    "longitude": self.observer_lon,
                    "altitude_m": self.observer_alt
                },
                "calculation_method": "spherical_geometry",
                "calculation_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        satellites_with_visibility = 0
        
        for satellite in satellites:
            try:
                sat_result = self._calculate_single_satellite_visibility(satellite)
                
                if sat_result:
                    visibility_results["satellites"].append(sat_result)
                    
                    # 統計可見性
                    if self._has_visible_positions(sat_result):
                        satellites_with_visibility += 1
                        
            except Exception as e:
                self.logger.error(f"計算衛星 {satellite.get('name', 'unknown')} 可見性時出錯: {e}")
                continue
        
        self.calculation_statistics["satellites_with_visibility"] = satellites_with_visibility
        visibility_results["statistics"] = self.calculation_statistics.copy()
        
        self.logger.info(f"✅ 可見性計算完成: {satellites_with_visibility}/{len(satellites)} 顆衛星有可見時間")
        
        return visibility_results
    
    def _calculate_single_satellite_visibility(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """計算單顆衛星的可見性"""
        
        try:
            position_timeseries = satellite.get("position_timeseries", [])
            
            if not position_timeseries:
                self.logger.warning(f"衛星 {satellite.get('name', 'unknown')} 缺少位置時間序列")
                return None
            
            # 計算每個時間點的相對位置
            visibility_timeseries = []
            
            for pos in position_timeseries:
                visibility_point = self._calculate_position_visibility(pos)
                
                if visibility_point:
                    visibility_timeseries.append(visibility_point)
                    self.calculation_statistics["total_position_calculations"] += 1
                    
                    if visibility_point.get("relative_to_observer", {}).get("elevation_deg", -90) > 0:
                        self.calculation_statistics["visible_position_calculations"] += 1
            
            # 構建結果
            satellite_result = satellite.copy()  # 保留原始數據
            satellite_result["position_timeseries"] = visibility_timeseries
            satellite_result["visibility_summary"] = self._calculate_visibility_summary(visibility_timeseries)
            
            return satellite_result
            
        except Exception as e:
            self.logger.error(f"計算衛星可見性時出錯: {e}")
            return None
    
    def _calculate_position_visibility(self, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """計算單個位置點的可見性"""
        
        try:
            # 獲取衛星位置
            sat_lat = position.get("latitude", 0.0)
            sat_lon = position.get("longitude", 0.0)
            sat_alt = position.get("altitude_km", 0.0)
            
            # 計算相對於觀測者的位置
            elevation, azimuth, distance = self._calculate_look_angles(
                sat_lat, sat_lon, sat_alt
            )
            
            # 構建增強的位置數據
            enhanced_position = position.copy()
            enhanced_position["relative_to_observer"] = {
                "elevation_deg": elevation,
                "azimuth_deg": azimuth,
                "range_km": distance,
                "is_visible": elevation > 0  # 地平線以上才可見
            }
            
            return enhanced_position
            
        except Exception as e:
            self.logger.error(f"計算位置可見性時出錯: {e}")
            return None
    
    def _calculate_look_angles(self, sat_lat: float, sat_lon: float, sat_alt_km: float) -> Tuple[float, float, float]:
        """
        計算觀測角度（仰角、方位角、距離）
        使用球面幾何學標準公式
        
        Returns:
            Tuple[elevation_deg, azimuth_deg, distance_km]
        """
        
        # 轉換為弧度
        obs_lat_rad = self.observer_lat * self.DEG_TO_RAD
        obs_lon_rad = self.observer_lon * self.DEG_TO_RAD
        sat_lat_rad = sat_lat * self.DEG_TO_RAD
        sat_lon_rad = sat_lon * self.DEG_TO_RAD
        
        # 計算衛星和觀測者的地心向量
        sat_radius = self.EARTH_RADIUS_KM + sat_alt_km
        obs_radius = self.EARTH_RADIUS_KM + (self.observer_alt / 1000.0)
        
        # 衛星在地心坐標系中的位置
        sat_x = sat_radius * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
        sat_y = sat_radius * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
        sat_z = sat_radius * math.sin(sat_lat_rad)
        
        # 觀測者在地心坐標系中的位置
        obs_x = obs_radius * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        obs_y = obs_radius * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        obs_z = obs_radius * math.sin(obs_lat_rad)
        
        # 衛星相對於觀測者的向量
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z
        
        # 距離
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 轉換到觀測者的本地坐標系
        # 東向單位向量
        east_x = -math.sin(obs_lon_rad)
        east_y = math.cos(obs_lon_rad)
        east_z = 0.0
        
        # 北向單位向量
        north_x = -math.sin(obs_lat_rad) * math.cos(obs_lon_rad)
        north_y = -math.sin(obs_lat_rad) * math.sin(obs_lon_rad)
        north_z = math.cos(obs_lat_rad)
        
        # 天頂單位向量
        up_x = math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        up_y = math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        up_z = math.sin(obs_lat_rad)
        
        # 在本地坐標系中的分量
        east_comp = dx*east_x + dy*east_y + dz*east_z
        north_comp = dx*north_x + dy*north_y + dz*north_z
        up_comp = dx*up_x + dy*up_y + dz*up_z
        
        # 計算仰角
        elevation_rad = math.asin(up_comp / distance) if distance > 0 else 0
        elevation_deg = elevation_rad * self.RAD_TO_DEG
        
        # 計算方位角
        azimuth_rad = math.atan2(east_comp, north_comp)
        azimuth_deg = azimuth_rad * self.RAD_TO_DEG
        
        # 確保方位角在0-360度範圍內
        if azimuth_deg < 0:
            azimuth_deg += 360.0
        
        return elevation_deg, azimuth_deg, distance
    
    def _calculate_visibility_summary(self, visibility_timeseries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算衛星可見性摘要統計"""
        
        if not visibility_timeseries:
            return {
                "total_points": 0,
                "visible_points": 0,
                "visibility_percentage": 0.0,
                "max_elevation": -90.0,
                "min_elevation": -90.0,
                "avg_elevation": -90.0,
                "visibility_windows": []
            }
        
        total_points = len(visibility_timeseries)
        visible_points = 0
        elevations = []
        
        # 統計可見點和仰角
        for point in visibility_timeseries:
            relative_pos = point.get("relative_to_observer", {})
            elevation = relative_pos.get("elevation_deg", -90)
            elevations.append(elevation)
            
            if elevation > 0:
                visible_points += 1
        
        # 計算統計值
        max_elevation = max(elevations) if elevations else -90
        min_elevation = min(elevations) if elevations else -90
        avg_elevation = sum(elevations) / len(elevations) if elevations else -90
        visibility_percentage = (visible_points / total_points * 100) if total_points > 0 else 0
        
        # 計算可見性時間窗口
        visibility_windows = self._calculate_visibility_windows(visibility_timeseries)
        
        return {
            "total_points": total_points,
            "visible_points": visible_points,
            "visibility_percentage": round(visibility_percentage, 2),
            "max_elevation": round(max_elevation, 2),
            "min_elevation": round(min_elevation, 2),
            "avg_elevation": round(avg_elevation, 2),
            "visibility_windows": visibility_windows,
            "total_visible_duration_minutes": sum(window["duration_minutes"] for window in visibility_windows)
        }
    
    def _calculate_visibility_windows(self, visibility_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """計算連續的可見性時間窗口"""
        
        windows = []
        current_window = None
        
        for i, point in enumerate(visibility_timeseries):
            elevation = point.get("relative_to_observer", {}).get("elevation_deg", -90)
            timestamp = point.get("timestamp", f"point_{i}")
            
            if elevation > 0:  # 可見
                if current_window is None:
                    # 開始新的可見窗口
                    current_window = {
                        "start_timestamp": timestamp,
                        "start_elevation": elevation,
                        "max_elevation": elevation,
                        "duration_points": 1
                    }
                else:
                    # 繼續當前窗口
                    current_window["duration_points"] += 1
                    current_window["max_elevation"] = max(current_window["max_elevation"], elevation)
            else:  # 不可見
                if current_window is not None:
                    # 結束當前窗口
                    current_window["end_timestamp"] = visibility_timeseries[i-1].get("timestamp", f"point_{i-1}")
                    current_window["end_elevation"] = visibility_timeseries[i-1].get("relative_to_observer", {}).get("elevation_deg", -90)
                    current_window["duration_minutes"] = current_window["duration_points"] * 0.5  # 假設30秒間隔
                    
                    windows.append(current_window)
                    current_window = None
        
        # 處理序列結束時仍在可見窗口的情況
        if current_window is not None:
            current_window["end_timestamp"] = visibility_timeseries[-1].get("timestamp", f"point_{len(visibility_timeseries)-1}")
            current_window["end_elevation"] = visibility_timeseries[-1].get("relative_to_observer", {}).get("elevation_deg", -90)
            current_window["duration_minutes"] = current_window["duration_points"] * 0.5
            windows.append(current_window)
        
        return windows
    
    def _has_visible_positions(self, satellite_result: Dict[str, Any]) -> bool:
        """檢查衛星是否有可見位置"""
        summary = satellite_result.get("visibility_summary", {})
        return summary.get("visible_points", 0) > 0
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return self.calculation_statistics.copy()
    
    def validate_visibility_results(self, visibility_results: Dict[str, Any]) -> Dict[str, Any]:
        """驗證可見性計算結果的合理性"""
        
        validation_result = {
            "passed": True,
            "total_satellites": len(visibility_results.get("satellites", [])),
            "validation_checks": {},
            "issues": []
        }
        
        satellites = visibility_results.get("satellites", [])
        
        if not satellites:
            validation_result["passed"] = False
            validation_result["issues"].append("無衛星可見性數據")
            return validation_result
        
        # 檢查1: 可見性計算完整性
        satellites_with_visibility_data = 0
        satellites_with_reasonable_elevation = 0
        
        for sat in satellites:
            timeseries = sat.get("position_timeseries", [])
            
            if timeseries:
                satellites_with_visibility_data += 1
                
                # 檢查是否有合理的仰角數據
                for point in timeseries[:5]:  # 檢查前5個點
                    elevation = point.get("relative_to_observer", {}).get("elevation_deg", -999)
                    if -90 <= elevation <= 90:
                        satellites_with_reasonable_elevation += 1
                        break
        
        validation_result["validation_checks"]["visibility_data_check"] = {
            "satellites_with_data": satellites_with_visibility_data,
            "satellites_with_reasonable_elevation": satellites_with_reasonable_elevation,
            "passed": satellites_with_visibility_data == len(satellites)
        }
        
        if satellites_with_visibility_data < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_visibility_data} 顆衛星缺少可見性數據")
        
        # 檢查2: 可見性統計合理性
        satellites_with_summary = 0
        satellites_with_windows = 0
        
        for sat in satellites:
            summary = sat.get("visibility_summary", {})
            
            if summary:
                satellites_with_summary += 1
                
                # 檢查可見性窗口
                windows = summary.get("visibility_windows", [])
                if windows:
                    satellites_with_windows += 1
        
        validation_result["validation_checks"]["summary_check"] = {
            "satellites_with_summary": satellites_with_summary,
            "satellites_with_windows": satellites_with_windows,
            "passed": satellites_with_summary == len(satellites)
        }
        
        if satellites_with_summary < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_summary} 顆衛星缺少可見性摘要")
        
        return validation_result