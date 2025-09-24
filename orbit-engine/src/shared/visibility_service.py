"""
統一可見性檢查服務

整合系統中所有衛星可見性判斷邏輯，
避免在各階段重複實現相同的可見性計算。

作者: NTN Stack Team
版本: 1.0.0
創建日期: 2025-08-19
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging

from .elevation_threshold_manager import get_elevation_threshold_manager

logger = logging.getLogger(__name__)


class VisibilityLevel(Enum):
    """可見性等級"""
    INVISIBLE = "invisible"      # 不可見 (低於最低仰角)
    BARELY_VISIBLE = "barely"    # 勉強可見 (最低仰角以上)
    GOOD_VISIBILITY = "good"     # 良好可見 (最佳仰角以上)
    EXCELLENT = "excellent"      # 極佳可見 (高仰角)


@dataclass
class ObserverLocation:
    """觀測者位置"""
    latitude: float   # 緯度 (度)
    longitude: float  # 經度 (度)
    altitude: float = 0.0  # 海拔高度 (米)
    location_name: str = "Unknown"
    
    def __post_init__(self):
        """驗證座標範圍"""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"緯度超出範圍: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"經度超出範圍: {self.longitude}")


@dataclass
class SatellitePosition:
    """衛星位置"""
    latitude: float   # 衛星緯度 (度)
    longitude: float  # 衛星經度 (度)
    altitude: float   # 衛星高度 (公里)
    timestamp: str    # 時間戳
    satellite_id: Optional[str] = None
    
    def get_distance_from_observer(self, observer: ObserverLocation) -> float:
        """計算與觀測者的3D距離 (公里)"""
        # 地球半徑 (公里)
        EARTH_RADIUS_KM = 6371.0
        
        # 轉換為弧度
        obs_lat_rad = math.radians(observer.latitude)
        obs_lon_rad = math.radians(observer.longitude)
        sat_lat_rad = math.radians(self.latitude)
        sat_lon_rad = math.radians(self.longitude)
        
        # 觀測者位置 (地心座標)
        obs_x = (EARTH_RADIUS_KM + observer.altitude / 1000) * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        obs_y = (EARTH_RADIUS_KM + observer.altitude / 1000) * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        obs_z = (EARTH_RADIUS_KM + observer.altitude / 1000) * math.sin(obs_lat_rad)
        
        # 衛星位置 (地心座標)
        sat_x = (EARTH_RADIUS_KM + self.altitude) * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
        sat_y = (EARTH_RADIUS_KM + self.altitude) * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
        sat_z = (EARTH_RADIUS_KM + self.altitude) * math.sin(sat_lat_rad)
        
        # 3D距離
        distance = math.sqrt((sat_x - obs_x)**2 + (sat_y - obs_y)**2 + (sat_z - obs_z)**2)
        return distance


class VisibilityResult(NamedTuple):
    """可見性檢查結果"""
    is_visible: bool
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    visibility_level: VisibilityLevel
    quality_score: float  # 0.0-1.0


class SatelliteVisibilityService:
    """
    衛星可見性檢查服務
    
    提供統一的衛星可見性判斷邏輯，整合：
    1. 仰角計算與門檻檢查
    2. 方位角計算
    3. 距離計算
    4. 可見性等級評估
    5. 批次可見性檢查
    """
    
    # 默認觀測點 (NTPU)
    DEFAULT_OBSERVER = ObserverLocation(
        latitude=24.9441667,
        longitude=121.3713889,
        altitude=50.0,  # 海拔50米
        location_name="NTPU"
    )
    
    def __init__(self, observer: Optional[ObserverLocation] = None):
        """
        初始化可見性檢查服務
        
        Args:
            observer: 觀測者位置，如果為None則使用NTPU作為默認位置
        """
        self.observer = observer if observer is not None else self.DEFAULT_OBSERVER
        self.elevation_manager = get_elevation_threshold_manager()
        
        logger.info("✅ 統一可見性檢查服務初始化完成")
        logger.info(f"  觀測點: {self.observer.location_name} ({self.observer.latitude}°, {self.observer.longitude}°)")
    
    def check_satellite_visibility(self, satellite_pos: SatellitePosition, 
                                 constellation: str) -> VisibilityResult:
        """
        檢查單顆衛星的可見性
        
        Args:
            satellite_pos: 衛星位置
            constellation: 星座名稱
        
        Returns:
            可見性檢查結果
        """
        # 計算仰角和方位角
        elevation, azimuth = self._calculate_elevation_azimuth(satellite_pos)
        
        # 計算距離
        distance = satellite_pos.get_distance_from_observer(self.observer)
        
        # 檢查可見性
        is_visible = self.elevation_manager.is_satellite_visible(elevation, constellation)
        
        # 評估可見性等級
        visibility_level = self._assess_visibility_level(elevation, constellation)
        
        # 計算品質評分
        quality_score = self.elevation_manager.get_elevation_quality_score(elevation, constellation)
        
        return VisibilityResult(
            is_visible=is_visible,
            elevation_deg=elevation,
            azimuth_deg=azimuth,
            distance_km=distance,
            visibility_level=visibility_level,
            quality_score=quality_score
        )
    
    def batch_check_visibility(self, satellites: List[Dict[str, Any]], 
                             constellation: str,
                             timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        批次檢查衛星可見性
        
        Args:
            satellites: 衛星列表
            constellation: 星座名稱
            timestamp: 指定時間點，如果為None則使用衛星數據中的時間
        
        Returns:
            增強的衛星數據列表 (包含可見性信息)
        """
        enhanced_satellites = []
        visible_count = 0
        
        logger.info(f"🔍 批次檢查 {constellation} 星座可見性: {len(satellites)} 顆衛星")
        
        for satellite in satellites:
            try:
                # 提取衛星位置信息
                satellite_id = satellite.get('satellite_id', satellite.get('name', 'Unknown'))
                
                # 處理時間序列數據或單點數據 - 修復：包含 positions 字段
                if ('position_timeseries' in satellite or 'timeseries' in satellite or 'positions' in satellite):
                    enhanced_satellite = self._process_timeseries_visibility(
                        satellite, constellation, timestamp
                    )
                else:
                    enhanced_satellite = self._process_single_point_visibility(
                        satellite, constellation
                    )
                
                if enhanced_satellite:
                    enhanced_satellites.append(enhanced_satellite)
                    
                    # 檢查是否有可見時間點
                    has_visible_points = False
                    timeseries = enhanced_satellite.get('position_timeseries', enhanced_satellite.get('timeseries', enhanced_satellite.get('positions', [])))
                    for point in timeseries:
                        if point.get('visibility_info', {}).get('is_visible', False):
                            has_visible_points = True
                            break
                    
                    if has_visible_points:
                        visible_count += 1
                
            except Exception as e:
                logger.warning(f"處理衛星 {satellite.get('satellite_id', 'Unknown')} 可見性檢查時發生錯誤: {e}")
                # 保留原始數據但標記為處理失敗
                enhanced_satellite = satellite.copy()
                enhanced_satellite['visibility_processing_error'] = str(e)
                enhanced_satellites.append(enhanced_satellite)
        
        logger.info(f"✅ 可見性檢查完成: {visible_count}/{len(satellites)} 顆衛星有可見時間點")
        
        return enhanced_satellites
    
    def filter_visible_satellites(self, satellites: List[Dict[str, Any]], 
                                constellation: str,
                                min_visibility_duration_minutes: float = 0.0) -> List[Dict[str, Any]]:
        """
        過濾出可見的衛星
        
        Args:
            satellites: 衛星列表
            constellation: 星座名稱
            min_visibility_duration_minutes: 最小可見時間 (分鐘)
        
        Returns:
            過濾後的可見衛星列表
        """
        # 先進行批次可見性檢查
        enhanced_satellites = self.batch_check_visibility(satellites, constellation)
        
        visible_satellites = []
        
        for satellite in enhanced_satellites:
            timeseries = satellite.get('position_timeseries', satellite.get('timeseries', satellite.get('positions', [])))
            
            # 計算可見時間點
            visible_points = []
            total_visible_duration = 0.0
            
            for point in timeseries:
                visibility_info = point.get('visibility_info', {})
                if visibility_info.get('is_visible', False):
                    visible_points.append(point)
            
            # 估算可見持續時間 (假設30秒間隔)
            total_visible_duration = len(visible_points) * 0.5  # 30秒 = 0.5分鐘
            
            # 檢查是否滿足最小可見時間要求
            if total_visible_duration >= min_visibility_duration_minutes:
                # 🎯 重要修復：保留完整時間序列，不截斷不可見時間點
                # 這確保後續階段能獲得完整的軌道數據 (192/240個時間點)
                filtered_satellite = satellite.copy()
                filtered_satellite['position_timeseries'] = timeseries  # 保留完整時間序列
                filtered_satellite['visibility_stats'] = {
                    'total_visible_duration_minutes': total_visible_duration,
                    'visible_points_count': len(visible_points),
                    'total_points_count': len(timeseries),
                    'visibility_ratio': len(visible_points) / len(timeseries) if timeseries else 0
                }
                visible_satellites.append(filtered_satellite)
        
        logger.info(f"📊 可見性過濾結果: {len(visible_satellites)}/{len(satellites)} 顆衛星滿足要求")
        logger.info(f"  過濾條件: 最小可見時間 {min_visibility_duration_minutes} 分鐘")
        
        return visible_satellites
    
    def get_visibility_statistics(self, satellites: List[Dict[str, Any]], 
                                constellation: str) -> Dict[str, Any]:
        """
        獲取可見性統計信息
        
        Args:
            satellites: 衛星列表
            constellation: 星座名稱
        
        Returns:
            可見性統計結果
        """
        enhanced_satellites = self.batch_check_visibility(satellites, constellation)
        
        stats = {
            'total_satellites': len(satellites),
            'visibility_levels': {level.value: 0 for level in VisibilityLevel},
            'elevation_distribution': {'0-10': 0, '10-20': 0, '20-30': 0, '30-60': 0, '60+': 0},
            'quality_scores': [],
            'distances': [],
            'satellites_with_visibility': 0
        }
        
        for satellite in enhanced_satellites:
            timeseries = satellite.get('position_timeseries', satellite.get('timeseries', satellite.get('positions', [])))
            has_visible_points = False
            
            for point in timeseries:
                visibility_info = point.get('visibility_info', {})
                
                if visibility_info:
                    elevation = visibility_info.get('elevation_deg', 0)
                    quality = visibility_info.get('quality_score', 0)
                    distance = visibility_info.get('distance_km', 0)
                    level = visibility_info.get('visibility_level', VisibilityLevel.INVISIBLE.value)
                    
                    # 統計可見性等級
                    stats['visibility_levels'][level] += 1
                    
                    # 統計仰角分佈
                    if elevation < 10:
                        stats['elevation_distribution']['0-10'] += 1
                    elif elevation < 20:
                        stats['elevation_distribution']['10-20'] += 1
                    elif elevation < 30:
                        stats['elevation_distribution']['20-30'] += 1
                    elif elevation < 60:
                        stats['elevation_distribution']['30-60'] += 1
                    else:
                        stats['elevation_distribution']['60+'] += 1
                    
                    # 收集品質和距離數據
                    stats['quality_scores'].append(quality)
                    stats['distances'].append(distance)
                    
                    if visibility_info.get('is_visible', False):
                        has_visible_points = True
            
            if has_visible_points:
                stats['satellites_with_visibility'] += 1
        
        # 計算平均值
        if stats['quality_scores']:
            stats['average_quality_score'] = sum(stats['quality_scores']) / len(stats['quality_scores'])
            stats['average_distance_km'] = sum(stats['distances']) / len(stats['distances'])
        else:
            stats['average_quality_score'] = 0.0
            stats['average_distance_km'] = 0.0
        
        return stats
    
    def _calculate_elevation_azimuth(self, satellite_pos: SatellitePosition) -> Tuple[float, float]:
        """計算仰角和方位角"""
        # 轉換為弧度
        obs_lat_rad = math.radians(self.observer.latitude)
        obs_lon_rad = math.radians(self.observer.longitude)
        sat_lat_rad = math.radians(satellite_pos.latitude)
        sat_lon_rad = math.radians(satellite_pos.longitude)
        
        # 地球半徑 (公里)
        EARTH_RADIUS_KM = 6371.0
        
        # 計算衛星相對於觀測者的位置向量
        delta_lon = sat_lon_rad - obs_lon_rad
        
        # 簡化的仰角計算 (適用於LEO衛星)
        # 考慮地球曲率的影響
        distance_surface = EARTH_RADIUS_KM * math.acos(
            math.sin(obs_lat_rad) * math.sin(sat_lat_rad) + 
            math.cos(obs_lat_rad) * math.cos(sat_lat_rad) * math.cos(delta_lon)
        )
        
        height_diff = satellite_pos.altitude - (self.observer.altitude / 1000)
        
        if distance_surface > 0:
            elevation_rad = math.atan2(height_diff, distance_surface)
            elevation_deg = math.degrees(elevation_rad)
        else:
            elevation_deg = 90.0  # 衛星在正上方
        
        # 方位角計算
        y = math.sin(delta_lon) * math.cos(sat_lat_rad)
        x = (math.cos(obs_lat_rad) * math.sin(sat_lat_rad) - 
             math.sin(obs_lat_rad) * math.cos(sat_lat_rad) * math.cos(delta_lon))
        
        azimuth_rad = math.atan2(y, x)
        azimuth_deg = (math.degrees(azimuth_rad) + 360) % 360  # 確保0-360度
        
        return elevation_deg, azimuth_deg
    
    def _assess_visibility_level(self, elevation_deg: float, constellation: str) -> VisibilityLevel:
        """評估可見性等級"""
        min_elev = self.elevation_manager.get_min_elevation(constellation)
        optimal_elev = self.elevation_manager.get_optimal_elevation(constellation)
        
        if elevation_deg < min_elev:
            return VisibilityLevel.INVISIBLE
        elif elevation_deg < optimal_elev:
            return VisibilityLevel.BARELY_VISIBLE
        elif elevation_deg < 45:
            return VisibilityLevel.GOOD_VISIBILITY
        else:
            return VisibilityLevel.EXCELLENT
    
    def _process_timeseries_visibility(self, satellite: Dict[str, Any], 
                                     constellation: str,
                                     target_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """處理時間序列數據的可見性檢查 - 使用預計算的可見性數據"""
        enhanced_satellite = satellite.copy()
        timeseries_data = satellite.get('position_timeseries', satellite.get('timeseries', satellite.get('positions', [])))
        
        enhanced_timeseries = []
        
        for point in timeseries_data:
            # 如果指定了時間戳，只處理該時間點
            if target_timestamp and point.get('time') != target_timestamp:
                enhanced_timeseries.append(point)
                continue
            
            try:
                # 檢查是否已有預計算的可見性數據
                if 'elevation_deg' in point and 'is_visible' in point:
                    # 使用預計算的可見性數據
                    elevation = point['elevation_deg']
                    is_visible = point['is_visible']
                    azimuth = point.get('azimuth_deg', 0)
                    range_km = point.get('range_km', 0)
                    
                    # 評估可見性等級
                    visibility_level = self._assess_visibility_level(elevation, constellation)
                    
                    # 計算品質評分
                    quality_score = self.elevation_manager.get_elevation_quality_score(elevation, constellation)
                    
                    # 增強時間點數據
                    enhanced_point = point.copy()
                    enhanced_point['visibility_info'] = {
                        'is_visible': is_visible,
                        'elevation_deg': elevation,
                        'azimuth_deg': azimuth,
                        'distance_km': range_km,
                        'visibility_level': visibility_level.value,
                        'quality_score': quality_score
                    }
                    
                else:
                    # 如果沒有預計算數據，嘗試使用舊方法（適用於緯度/經度數據）
                    sat_pos = SatellitePosition(
                        latitude=point.get('latitude', 0),
                        longitude=point.get('longitude', 0),
                        altitude=point.get('altitude', 0),
                        timestamp=point.get('time', ''),
                        satellite_id=satellite.get('satellite_id')
                    )
                    
                    # 檢查可見性
                    visibility_result = self.check_satellite_visibility(sat_pos, constellation)
                    
                    # 增強時間點數據
                    enhanced_point = point.copy()
                    enhanced_point['visibility_info'] = {
                        'is_visible': visibility_result.is_visible,
                        'elevation_deg': visibility_result.elevation_deg,
                        'azimuth_deg': visibility_result.azimuth_deg,
                        'distance_km': visibility_result.distance_km,
                        'visibility_level': visibility_result.visibility_level.value,
                        'quality_score': visibility_result.quality_score
                    }
                
                enhanced_timeseries.append(enhanced_point)
                
            except Exception as e:
                logger.warning(f"處理時間點可見性時發生錯誤: {e}")
                enhanced_timeseries.append(point)  # 保留原始數據
        
        enhanced_satellite['position_timeseries'] = enhanced_timeseries
        return enhanced_satellite
    
    def _process_single_point_visibility(self, satellite: Dict[str, Any], 
                                       constellation: str) -> Dict[str, Any]:
        """處理單點數據的可見性檢查"""
        enhanced_satellite = satellite.copy()
        
        try:
            sat_pos = SatellitePosition(
                latitude=satellite.get('latitude', 0),
                longitude=satellite.get('longitude', 0),
                altitude=satellite.get('altitude', 0),
                timestamp=satellite.get('timestamp', ''),
                satellite_id=satellite.get('satellite_id')
            )
            
            visibility_result = self.check_satellite_visibility(sat_pos, constellation)
            
            enhanced_satellite['visibility_info'] = {
                'is_visible': visibility_result.is_visible,
                'elevation_deg': visibility_result.elevation_deg,
                'azimuth_deg': visibility_result.azimuth_deg,
                'distance_km': visibility_result.distance_km,
                'visibility_level': visibility_result.visibility_level.value,
                'quality_score': visibility_result.quality_score
            }
            
        except Exception as e:
            logger.warning(f"處理單點可見性時發生錯誤: {e}")
            enhanced_satellite['visibility_processing_error'] = str(e)
        
        return enhanced_satellite


# 全局實例
_global_visibility_service = None

def get_visibility_service(observer: Optional[ObserverLocation] = None) -> SatelliteVisibilityService:
    """獲取全局可見性檢查服務實例"""
    global _global_visibility_service
    if _global_visibility_service is None or observer is not None:
        _global_visibility_service = SatelliteVisibilityService(observer)
    return _global_visibility_service


# 便捷函數
def check_satellite_visibility(satellite_pos: SatellitePosition, constellation: str) -> VisibilityResult:
    """快速檢查衛星可見性"""
    return get_visibility_service().check_satellite_visibility(satellite_pos, constellation)

def filter_visible_satellites(satellites: List[Dict[str, Any]], constellation: str) -> List[Dict[str, Any]]:
    """快速過濾可見衛星"""
    return get_visibility_service().filter_visible_satellites(satellites, constellation)


if __name__ == "__main__":
    # 測試統一可見性檢查服務
    service = get_visibility_service()
    
    print("🧪 測試統一可見性檢查服務")
    print("=" * 50)
    
    # 測試單點可見性檢查
    test_satellite = SatellitePosition(
        latitude=25.0,  # 台灣附近
        longitude=121.5,
        altitude=550.0,  # 550公里高度
        timestamp=datetime.now(timezone.utc).isoformat(),
        satellite_id="TEST-SAT-001"
    )
    
    result = service.check_satellite_visibility(test_satellite, "starlink")
    print(f"測試衛星可見性:")
    print(f"  可見: {'✅' if result.is_visible else '❌'}")
    print(f"  仰角: {result.elevation_deg:.1f}°")
    print(f"  方位角: {result.azimuth_deg:.1f}°")
    print(f"  距離: {result.distance_km:.1f} 公里")
    print(f"  等級: {result.visibility_level.value}")
    print(f"  品質評分: {result.quality_score:.2f}")
    
    print("\n✅ 統一可見性檢查服務測試完成")