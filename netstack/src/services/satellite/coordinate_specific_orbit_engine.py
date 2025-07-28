#!/usr/bin/env python3
"""
座標特定軌道預計算引擎 - Phase 0.4
支援任意觀測點的軌道預計算，實現可見性篩選和最佳時段識別
"""

import json
import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from math import degrees, radians, sin, cos, sqrt, atan2, asin, pi

logger = logging.getLogger(__name__)

class CoordinateSpecificOrbitEngine:
    """座標特定軌道預計算引擎 - 支援任意觀測點"""
    
    def __init__(self, observer_lat: float, observer_lon: float, 
                 observer_alt: float = 0.0, min_elevation: float = 5.0):
        """
        初始化引擎
        
        Args:
            observer_lat: 觀測點緯度 (度)
            observer_lon: 觀測點經度 (度) 
            observer_alt: 觀測點海拔 (米)
            min_elevation: 最小仰角閾值 (度)
        """
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon  
        self.observer_alt = observer_alt
        self.min_elevation = min_elevation
        
        # 預計算參數
        self.earth_radius_km = 6371.0  # 地球半徑 (km)
        self.time_step_seconds = 30    # 30秒間隔
        self.orbital_period_minutes = 96  # 96分鐘軌道週期
        
        logger.info(f"CoordinateSpecificOrbitEngine 初始化")
        logger.info(f"  觀測座標: ({self.observer_lat:.5f}, {self.observer_lon:.5f})")
        logger.info(f"  海拔: {self.observer_alt:.1f}m, 最小仰角: {self.min_elevation:.1f}°")
    
    def eci_to_observer_coordinates(self, eci_position: Tuple[float, float, float], 
                                   observation_time: datetime) -> Dict[str, float]:
        """
        將 ECI 座標轉換為觀測點相對座標
        
        Args:
            eci_position: ECI 座標 (x, y, z) in km
            observation_time: 觀測時間
            
        Returns:
            Dict: 包含 elevation, azimuth, range_km 的字典
        """
        try:
            x, y, z = eci_position
            
            # 轉換為弧度
            lat_rad = radians(self.observer_lat)
            lon_rad = radians(self.observer_lon)
            
            # 計算觀測點在地心坐標系的位置
            observer_radius = self.earth_radius_km + self.observer_alt / 1000.0
            observer_x = observer_radius * cos(lat_rad) * cos(lon_rad)
            observer_y = observer_radius * cos(lat_rad) * sin(lon_rad)
            observer_z = observer_radius * sin(lat_rad)
            
            # 計算相對位置向量
            dx = x - observer_x
            dy = y - observer_y
            dz = z - observer_z
            
            # 轉換到觀測點的東北天座標系 (ENU - East, North, Up)
            # 旋轉矩陣轉換
            sin_lat, cos_lat = sin(lat_rad), cos(lat_rad)
            sin_lon, cos_lon = sin(lon_rad), cos(lon_rad)
            
            # 轉換到 ENU 座標系
            east = -sin_lon * dx + cos_lon * dy
            north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
            up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
            
            # 計算距離
            range_km = sqrt(dx*dx + dy*dy + dz*dz)
            
            # 計算仰角和方位角
            horizontal_distance = sqrt(east*east + north*north)
            elevation_rad = atan2(up, horizontal_distance)
            elevation_deg = degrees(elevation_rad)
            
            azimuth_rad = atan2(east, north)
            azimuth_deg = degrees(azimuth_rad)
            if azimuth_deg < 0:
                azimuth_deg += 360
            
            return {
                'elevation_deg': elevation_deg,
                'azimuth_deg': azimuth_deg,
                'range_km': range_km,
                'enu_coordinates': {'east': east, 'north': north, 'up': up}
            }
            
        except Exception as e:
            logger.error(f"座標轉換失敗: {e}")
            return {
                'elevation_deg': -90.0,
                'azimuth_deg': 0.0,
                'range_km': 0.0,
                'enu_coordinates': {'east': 0.0, 'north': 0.0, 'up': 0.0}
            }
    
    def compute_instantaneous_visibility(self, satellite_tle_data: Dict[str, Any], 
                                       observation_time: datetime) -> Dict[str, Any]:
        """
        計算特定時間點的瞬時可見性
        
        Args:
            satellite_tle_data: 衛星 TLE 數據
            observation_time: 觀測時間
            
        Returns:
            Dict: 瞬時可見性數據
        """
        try:
            from sgp4.api import Satrec, jday
            
            # 創建 SGP4 衛星對象
            satellite = Satrec.twoline2rv(satellite_tle_data['line1'], satellite_tle_data['line2'])
            
            # 轉換時間為 Julian Day
            jd, fr = jday(observation_time.year, observation_time.month, observation_time.day,
                         observation_time.hour, observation_time.minute, 
                         observation_time.second + observation_time.microsecond / 1e6)
            
            # 計算衛星位置
            error, position, velocity = satellite.sgp4(jd, fr)
            
            if error == 0:
                # 轉換為觀測點相對座標
                observer_coords = self.eci_to_observer_coordinates(position, observation_time)
                
                # 檢查是否可見
                is_visible = observer_coords['elevation_deg'] >= self.min_elevation
                
                return {
                    'satellite_info': {
                        'name': satellite_tle_data['name'],
                        'norad_id': satellite_tle_data['norad_id']
                    },
                    'observation_time': observation_time.isoformat(),
                    'position_eci': {'x': position[0], 'y': position[1], 'z': position[2]},
                    'observer_coordinates': observer_coords,
                    'is_visible': is_visible,
                    'elevation': observer_coords['elevation_deg'],
                    'azimuth': observer_coords['azimuth_deg'],
                    'range_km': observer_coords['range_km']
                }
            else:
                return {
                    'satellite_info': {
                        'name': satellite_tle_data['name'],
                        'norad_id': satellite_tle_data['norad_id']
                    },
                    'observation_time': observation_time.isoformat(),
                    'is_visible': False,
                    'error': f'SGP4 calculation error: {error}'
                }
                
        except Exception as e:
            return {
                'satellite_info': {
                    'name': satellite_tle_data.get('name', 'Unknown'),
                    'norad_id': satellite_tle_data.get('norad_id', 0)
                },
                'observation_time': observation_time.isoformat(),
                'is_visible': False,
                'error': str(e)
            }
    
    def compute_96min_orbital_cycle(self, satellite_tle_data: Dict[str, Any], 
                                   start_time: datetime) -> Dict[str, Any]:
        """
        計算96分鐘完整軌道週期的可見性
        
        Args:
            satellite_tle_data: 衛星 TLE 數據
            start_time: 開始時間
            
        Returns:
            Dict: 軌道週期數據
        """
        try:
            from sgp4.api import Satrec, jday
            
            # 創建 SGP4 衛星對象
            satellite = Satrec.twoline2rv(satellite_tle_data['line1'], satellite_tle_data['line2'])
            
            # 計算時間點
            total_seconds = self.orbital_period_minutes * 60
            time_points = list(range(0, total_seconds, self.time_step_seconds))
            
            orbit_data = {
                'satellite_info': {
                    'name': satellite_tle_data['name'],
                    'norad_id': satellite_tle_data['norad_id'],
                    'tle_date': satellite_tle_data.get('tle_date', 'unknown')
                },
                'computation_metadata': {
                    'start_time': start_time.isoformat(),
                    'duration_minutes': self.orbital_period_minutes,
                    'time_step_seconds': self.time_step_seconds,
                    'total_positions': len(time_points),
                    'observer_location': {
                        'lat': self.observer_lat,
                        'lon': self.observer_lon,
                        'alt': self.observer_alt
                    }
                },
                'positions': [],
                'visibility_windows': [],
                'statistics': {
                    'total_positions': 0,
                    'visible_positions': 0,
                    'visibility_percentage': 0.0,
                    'max_elevation': -90.0,
                    'calculation_errors': 0
                }
            }
            
            current_window = None
            
            for t_offset in time_points:
                current_time = start_time + timedelta(seconds=t_offset)
                
                # 轉換為 Julian Day
                jd, fr = jday(current_time.year, current_time.month, current_time.day,
                             current_time.hour, current_time.minute, current_time.second)
                
                # SGP4 計算位置和速度
                error, position, velocity = satellite.sgp4(jd, fr)
                
                if error == 0:  # 無錯誤
                    # 轉換為觀測點座標
                    observer_coords = self.eci_to_observer_coordinates(position, current_time)
                    
                    position_data = {
                        'time': current_time.isoformat(),
                        'time_offset_seconds': t_offset,
                        'position_eci': {'x': position[0], 'y': position[1], 'z': position[2]},
                        'velocity_eci': {'x': velocity[0], 'y': velocity[1], 'z': velocity[2]},
                        'elevation_deg': observer_coords['elevation_deg'],
                        'azimuth_deg': observer_coords['azimuth_deg'],
                        'range_km': observer_coords['range_km'],
                        'is_visible': observer_coords['elevation_deg'] >= self.min_elevation
                    }
                    
                    orbit_data['positions'].append(position_data)
                    orbit_data['statistics']['total_positions'] += 1
                    
                    if position_data['is_visible']:
                        orbit_data['statistics']['visible_positions'] += 1
                        orbit_data['statistics']['max_elevation'] = max(
                            orbit_data['statistics']['max_elevation'],
                            observer_coords['elevation_deg']
                        )
                    
                    # 追蹤可見性窗口
                    if observer_coords['elevation_deg'] >= self.min_elevation:
                        if current_window is None:
                            current_window = {
                                'start_time': current_time.isoformat(),
                                'start_elevation': observer_coords['elevation_deg'],
                                'max_elevation': observer_coords['elevation_deg'],
                                'end_time': current_time.isoformat(),
                                'duration_seconds': 0
                            }
                        else:
                            current_window['max_elevation'] = max(
                                current_window['max_elevation'], 
                                observer_coords['elevation_deg']
                            )
                            current_window['end_time'] = current_time.isoformat()
                            current_window['duration_seconds'] = t_offset - time_points[0]
                    else:
                        if current_window is not None:
                            orbit_data['visibility_windows'].append(current_window)
                            current_window = None
                else:
                    orbit_data['statistics']['calculation_errors'] += 1
            
            # 結束最後一個窗口
            if current_window is not None:
                orbit_data['visibility_windows'].append(current_window)
            
            # 計算可見性百分比
            if orbit_data['statistics']['total_positions'] > 0:
                orbit_data['statistics']['visibility_percentage'] = (
                    orbit_data['statistics']['visible_positions'] / 
                    orbit_data['statistics']['total_positions'] * 100
                )
            
            return orbit_data
            
        except Exception as e:
            logger.error(f"軌道計算失敗 {satellite_tle_data.get('name', 'Unknown')}: {e}")
            return {
                'error': str(e),
                'satellite_info': {
                    'name': satellite_tle_data.get('name', 'Unknown'),
                    'norad_id': satellite_tle_data.get('norad_id', 0)
                }
            }
    
    def filter_visible_satellites(self, all_satellites: List[Dict[str, Any]], 
                                 reference_time: datetime) -> List[Dict[str, Any]]:
        """
        衛星可見性篩選器
        篩選掉永遠無法到達最小仰角的衛星
        
        Args:
            all_satellites: 所有衛星數據
            reference_time: 參考時間
            
        Returns:
            List: 篩選後的可見衛星清單
        """
        logger.info(f"開始可見性篩選: {len(all_satellites)} 顆衛星")
        
        filtered_satellites = []
        filter_stats = {
            'total_input': len(all_satellites),
            'passed_filter': 0,
            'rejected_never_visible': 0,
            'rejected_errors': 0
        }
        
        for i, satellite in enumerate(all_satellites):
            try:
                # 計算完整軌道週期
                orbit_data = self.compute_96min_orbital_cycle(satellite, reference_time)
                
                if 'error' not in orbit_data:
                    # 檢查是否有可見時段
                    if (orbit_data['statistics']['visible_positions'] > 0 and 
                        orbit_data['statistics']['max_elevation'] >= self.min_elevation):
                        
                        # 添加篩選統計信息
                        satellite['visibility_stats'] = orbit_data['statistics']
                        satellite['visibility_windows'] = orbit_data['visibility_windows']
                        filtered_satellites.append(satellite)
                        filter_stats['passed_filter'] += 1
                    else:
                        filter_stats['rejected_never_visible'] += 1
                else:
                    filter_stats['rejected_errors'] += 1
                
                # 進度報告
                if (i + 1) % 500 == 0:
                    logger.info(f"篩選進度: {i + 1}/{len(all_satellites)} ({(i + 1)/len(all_satellites)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"篩選衛星 {satellite.get('name', 'Unknown')} 失敗: {e}")
                filter_stats['rejected_errors'] += 1
                continue
        
        # 計算篩選效率
        filter_efficiency = (filter_stats['rejected_never_visible'] / 
                           filter_stats['total_input'] * 100 if filter_stats['total_input'] > 0 else 0)
        
        logger.info("✅ 可見性篩選完成:")
        logger.info(f"  - 輸入衛星: {filter_stats['total_input']}")
        logger.info(f"  - 通過篩選: {filter_stats['passed_filter']}")
        logger.info(f"  - 永不可見: {filter_stats['rejected_never_visible']}")
        logger.info(f"  - 計算錯誤: {filter_stats['rejected_errors']}")
        logger.info(f"  - 篩選效率: {filter_efficiency:.1f}% 減少")
        
        return filtered_satellites
    
    def filter_instantaneous_visible_satellites(self, all_satellites: List[Dict[str, Any]], 
                                               observation_time: datetime) -> List[Dict[str, Any]]:
        """
        瞬時可見性篩選器 - 僅返回在特定時間點可見的衛星
        
        Args:
            all_satellites: 所有衛星數據
            observation_time: 觀測時間
            
        Returns:
            List: 在觀測時間可見的衛星清單
        """
        logger.info(f"開始瞬時可見性篩選: {len(all_satellites)} 顆衛星")
        logger.info(f"  觀測時間: {observation_time.isoformat()}")
        
        visible_satellites = []
        filter_stats = {
            'total_input': len(all_satellites),
            'instantaneous_visible': 0,
            'not_visible': 0,
            'calculation_errors': 0
        }
        
        for i, satellite in enumerate(all_satellites):
            try:
                # 計算瞬時可見性
                visibility_data = self.compute_instantaneous_visibility(satellite, observation_time)
                
                if 'error' not in visibility_data and visibility_data['is_visible']:
                    # 添加可見性信息到衛星數據
                    visible_satellite = satellite.copy()
                    visible_satellite['instantaneous_visibility'] = visibility_data
                    visible_satellite['elevation'] = visibility_data['elevation']
                    visible_satellite['azimuth'] = visibility_data['azimuth']
                    visible_satellite['range_km'] = visibility_data['range_km']
                    
                    visible_satellites.append(visible_satellite)
                    filter_stats['instantaneous_visible'] += 1
                elif 'error' in visibility_data:
                    filter_stats['calculation_errors'] += 1
                else:
                    filter_stats['not_visible'] += 1
                
                # 進度報告
                if (i + 1) % 200 == 0:
                    logger.info(f"瞬時篩選進度: {i + 1}/{len(all_satellites)} ({(i + 1)/len(all_satellites)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"瞬時篩選衛星 {satellite.get('name', 'Unknown')} 失敗: {e}")
                filter_stats['calculation_errors'] += 1
                continue
        
        logger.info("✅ 瞬時可見性篩選完成:")
        logger.info(f"  - 輸入衛星: {filter_stats['total_input']}")
        logger.info(f"  - 瞬時可見: {filter_stats['instantaneous_visible']}")
        logger.info(f"  - 不可見: {filter_stats['not_visible']}")
        logger.info(f"  - 計算錯誤: {filter_stats['calculation_errors']}")
        logger.info(f"  - 可見率: {filter_stats['instantaneous_visible']/filter_stats['total_input']*100:.2f}%")
        
        return visible_satellites
    
    def find_optimal_timewindow(self, filtered_satellites: List[Dict[str, Any]], 
                               window_hours: int = 6, 
                               reference_time: datetime = None) -> Dict[str, Any]:
        """
        最佳時間窗口識別
        在24小時內找出指定時長的最佳窗口
        
        Args:
            filtered_satellites: 篩選後的衛星清單
            window_hours: 窗口時長 (小時)
            reference_time: 參考時間
            
        Returns:
            Dict: 最佳時間窗口數據
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
            
        logger.info(f"尋找最佳 {window_hours} 小時時間窗口")
        logger.info(f"  參考時間: {reference_time.isoformat()}")
        logger.info(f"  衛星數量: {len(filtered_satellites)}")
        
        # 24小時內每小時評估一次
        evaluation_windows = []
        window_duration = timedelta(hours=window_hours)
        
        for hour_offset in range(0, 24, 1):  # 每小時評估
            window_start = reference_time + timedelta(hours=hour_offset)
            window_end = window_start + window_duration
            
            window_stats = {
                'start_time': window_start.isoformat(),
                'end_time': window_end.isoformat(),
                'duration_hours': window_hours,
                'visible_satellites': 0,
                'total_visibility_time': 0,
                'avg_elevation': 0.0,
                'handover_opportunities': 0,
                'quality_score': 0.0
            }
            
            total_elevation = 0
            elevation_count = 0
            
            # 評估每顆衛星在此窗口的表現
            for satellite in filtered_satellites:
                if 'visibility_windows' in satellite:
                    for vis_window in satellite['visibility_windows']:
                        vis_start = datetime.fromisoformat(vis_window['start_time'].replace('Z', '+00:00'))
                        vis_end = datetime.fromisoformat(vis_window['end_time'].replace('Z', '+00:00'))
                        
                        # 檢查可見性窗口是否與評估窗口重疊
                        if vis_start <= window_end and vis_end >= window_start:
                            window_stats['visible_satellites'] += 1
                            window_stats['total_visibility_time'] += vis_window['duration_seconds']
                            total_elevation += vis_window['max_elevation']
                            elevation_count += 1
                            
                            # 統計換手機會
                            if vis_window['max_elevation'] > 30:  # 高仰角換手機會更好
                                window_stats['handover_opportunities'] += 1
            
            # 計算平均仰角
            if elevation_count > 0:
                window_stats['avg_elevation'] = total_elevation / elevation_count
            
            # 計算綜合品質分數
            # 考慮因素：可見衛星數、平均仰角、總可見時間、換手機會
            satellite_factor = min(window_stats['visible_satellites'] / 10, 1.0)  # 正規化到0-1
            elevation_factor = min(window_stats['avg_elevation'] / 90, 1.0)  # 正規化到0-1
            time_factor = min(window_stats['total_visibility_time'] / 3600, 1.0)  # 正規化到0-1 (1小時)
            handover_factor = min(window_stats['handover_opportunities'] / 20, 1.0)  # 正規化到0-1
            
            window_stats['quality_score'] = (
                satellite_factor * 0.4 +  # 40% 衛星數量
                elevation_factor * 0.3 +   # 30% 平均仰角  
                time_factor * 0.2 +        # 20% 總可見時間
                handover_factor * 0.1      # 10% 換手機會
            ) * 100
            
            evaluation_windows.append(window_stats)
        
        # 找出最佳窗口
        best_window = max(evaluation_windows, key=lambda w: w['quality_score'])
        
        optimal_result = {
            'optimal_window': best_window,
            'all_evaluations': evaluation_windows,
            'selection_criteria': {
                'window_hours': window_hours,
                'satellite_weight': 0.4,
                'elevation_weight': 0.3,
                'visibility_time_weight': 0.2,
                'handover_weight': 0.1
            },
            'statistics': {
                'total_windows_evaluated': len(evaluation_windows),
                'best_quality_score': best_window['quality_score'],
                'avg_quality_score': sum(w['quality_score'] for w in evaluation_windows) / len(evaluation_windows)
            }
        }
        
        logger.info("✅ 最佳時間窗口識別完成:")
        logger.info(f"  - 最佳時段: {best_window['start_time']} - {best_window['end_time']}")
        logger.info(f"  - 品質分數: {best_window['quality_score']:.1f}")
        logger.info(f"  - 可見衛星: {best_window['visible_satellites']}")
        logger.info(f"  - 平均仰角: {best_window['avg_elevation']:.1f}°")
        logger.info(f"  - 換手機會: {best_window['handover_opportunities']}")
        
        return optimal_result
    
    def generate_display_optimized_data(self, optimal_window_data: Dict[str, Any], 
                                       acceleration: int = 60, 
                                       distance_scale: float = 0.1) -> Dict[str, Any]:
        """
        前端展示優化數據生成
        考慮60倍加速動畫的時間壓縮和距離縮放
        
        Args:
            optimal_window_data: 最佳窗口數據
            acceleration: 加速倍數
            distance_scale: 距離縮放係數
            
        Returns:
            Dict: 前端展示優化數據
        """
        logger.info(f"生成前端展示數據 (加速: {acceleration}x, 距離縮放: {distance_scale})")
        
        optimal_window = optimal_window_data['optimal_window']
        
        display_data = {
            'metadata': {
                'acceleration_factor': acceleration,
                'distance_scale': distance_scale,
                'original_window': optimal_window,
                'animation_duration_seconds': optimal_window['duration_hours'] * 3600 / acceleration,
                'recommended_fps': 30
            },
            'animation_keyframes': [],
            'satellite_trajectories': [],
            'handover_events': [],
            'camera_suggestions': {
                'initial_position': {
                    'lat': self.observer_lat,
                    'lon': self.observer_lon,
                    'altitude': 1000 * distance_scale  # 縮放的視覺高度
                },
                'follow_mode': 'observer_centered',
                'zoom_level': 'medium'
            }
        }
        
        # 生成動畫關鍵幀 (每分鐘一幀，加速後)
        window_start = datetime.fromisoformat(optimal_window['start_time'].replace('Z', '+00:00'))
        window_duration_minutes = optimal_window['duration_hours'] * 60
        
        for minute in range(0, window_duration_minutes, 5):  # 每5分鐘一個關鍵幀
            keyframe_time = window_start + timedelta(minutes=minute)
            animation_time = minute * 60 / acceleration  # 動畫中的時間
            
            keyframe = {
                'animation_time_seconds': animation_time,
                'real_time': keyframe_time.isoformat(),
                'visible_satellites': [],
                'recommended_view_angle': self._calculate_optimal_view_angle(minute, window_duration_minutes)
            }
            
            display_data['animation_keyframes'].append(keyframe)
        
        # 軌跡平滑化建議
        display_data['trajectory_smoothing'] = {
            'enabled': True,
            'interpolation_method': 'cubic_spline',
            'keyframe_density': 'medium',  # 平衡效能和流暢度
            'distance_fade': True  # 遠距離衛星透明度降低
        }
        
        # 換手事件動畫
        display_data['handover_animations'] = {
            'signal_strength_visualization': True,
            'beam_switching_effect': True,
            'satellite_highlight_duration': 3.0,  # 秒
            'transition_effect': 'smooth_fade'
        }
        
        logger.info("✅ 前端展示數據生成完成")
        return display_data
    
    def _calculate_optimal_view_angle(self, current_minute: int, total_minutes: int) -> Dict[str, float]:
        """計算最佳視角"""
        progress = current_minute / total_minutes
        
        # 動態調整視角以獲得最佳視覺效果
        base_elevation = 45.0
        base_azimuth = 0.0
        
        # 隨時間緩慢旋轉視角
        azimuth = base_azimuth + (progress * 360 * 0.5)  # 半圈旋轉
        elevation = base_elevation + sin(progress * 2 * pi) * 15  # 上下波動
        
        return {
            'elevation': elevation,
            'azimuth': azimuth % 360,
            'zoom': 1.0 + sin(progress * pi) * 0.3  # 縮放變化
        }


# 預設座標配置 (可擴展到其他觀測點)
NTPU_COORDINATES = {
    'lat': 24.94417,    # 24°56'39"N
    'lon': 121.37139,   # 121°22'17"E
    'alt': 50.0,        # 海拔50米
    'name': 'NTPU'
}

OBSERVER_LOCATIONS = {
    'ntpu': NTPU_COORDINATES,
    # 未來可添加其他觀測點
    # 'nctu': {'lat': 24.7881, 'lon': 120.9971, 'alt': 30.0, 'name': 'NCTU'},
    # 'ntu': {'lat': 25.0173, 'lon': 121.5397, 'alt': 10.0, 'name': 'NTU'}
}


def get_observer_coordinates(location_id: str) -> Dict[str, Any]:
    """獲取觀測點座標"""
    return OBSERVER_LOCATIONS.get(location_id.lower(), NTPU_COORDINATES)


if __name__ == "__main__":
    # 示例使用
    print("🛰️ CoordinateSpecificOrbitEngine 測試")
    
    # 初始化引擎 (NTPU 座標)
    engine = CoordinateSpecificOrbitEngine(
        observer_lat=NTPU_COORDINATES['lat'],
        observer_lon=NTPU_COORDINATES['lon'],
        observer_alt=NTPU_COORDINATES['alt'],
        min_elevation=5.0
    )
    
    print("引擎初始化完成")
    print(f"觀測點: {NTPU_COORDINATES['name']}")
    print(f"座標: ({engine.observer_lat:.5f}, {engine.observer_lon:.5f})")