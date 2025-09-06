#!/usr/bin/env python3
"""
真正的SGP4軌道計算引擎
實現@docs要求的192點時間序列軌道預測和軌道相位分析
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

# 天體力學計算庫
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.timelib import Time
from sgp4.api import Satrec, jday
from sgp4 import omm

logger = logging.getLogger(__name__)

class SGP4OrbitalEngine:
    """
    真正的SGP4軌道計算引擎
    實現@docs中軌道相位位移算法所需的核心功能
    """
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889, observer_elevation_m: float = 50):
        """
        初始化SGP4軌道引擎
        
        Args:
            observer_lat: NTPU觀測點緯度 (度)
            observer_lon: NTPU觀測點經度 (度) 
            observer_elevation_m: 觀測點海拔高度 (米)
        """
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon  
        self.observer_elevation_m = observer_elevation_m
        
        # 初始化skyfield時間載入器
        self.ts = load.timescale()
        
        # NTPU觀測點
        self.observer_position = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_elevation_m)
        
        logger.info(f"🌍 SGP4軌道引擎初始化完成")
        logger.info(f"  觀測點: NTPU ({observer_lat:.6f}°N, {observer_lon:.6f}°E, {observer_elevation_m}m)")
        logger.info(f"  🎯 星座特定仰角門檻: Starlink 5°, OneWeb 10°")
    
    def _calculate_visibility(self, elevation_deg: float, constellation: str) -> bool:
        """
        根據星座計算可見性（符合用戶真實需求）
        
        Args:
            elevation_deg: 仰角（度）
            constellation: 星座名稱
            
        Returns:
            是否可見
        """
        # 用戶真實需求：Starlink 5°, OneWeb 10°
        if constellation.lower() == 'starlink':
            return elevation_deg >= 5.0  # Starlink: 5度仰角閾值
        elif constellation.lower() == 'oneweb':
            return elevation_deg >= 10.0  # OneWeb: 10度仰角閾值
        else:
            # 未知星座默認使用5度
            return elevation_deg >= 5.0
    
    def parse_tle_line(self, tle_lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        解析TLE三行數據並提取軌道元素
        
        Args:
            tle_lines: TLE三行數據列表
            
        Returns:
            包含衛星信息和軌道元素的字典，失敗返回None
        """
        try:
            if len(tle_lines) != 3:
                return None
                
            sat_name = tle_lines[0].strip()
            line1 = tle_lines[1].strip()
            line2 = tle_lines[2].strip()
            
            # 使用skyfield創建EarthSatellite對象
            satellite = EarthSatellite(line1, line2, sat_name, self.ts)
            
            # 提取軌道元素（從sgp4模型）
            satrec = satellite.model
            
            orbital_elements = {
                'epoch_year': satrec.epochyr,
                'epoch_days': satrec.epochdays,
                'mean_motion_revs_per_day': satrec.no_kozai * (1440.0 / (2.0 * np.pi)),  # 轉換為每天軌道數
                'eccentricity': satrec.ecco,
                'inclination_deg': np.degrees(satrec.inclo),
                'raan_deg': np.degrees(satrec.nodeo),  # 升交點赤經
                'argument_of_perigee_deg': np.degrees(satrec.argpo),
                'mean_anomaly_deg': np.degrees(satrec.mo),
                'mean_motion_rad_min': satrec.no_kozai,  # 原始平均運動（弧度/分鐘）
            }
            
            # 計算軌道週期（分鐘）
            orbital_period_minutes = (2 * np.pi) / satrec.no_kozai
            
            return {
                'satellite_name': sat_name,
                'norad_id': satrec.satnum,
                'tle_line1': line1,
                'tle_line2': line2, 
                'satellite_object': satellite,
                'orbital_elements': orbital_elements,
                'orbital_period_minutes': orbital_period_minutes
            }
            
        except Exception as e:
            logger.error(f"TLE解析失敗: {e}")
            return None
    
    def calculate_position_timeseries(self, satellite_data: Dict[str, Any], 
                                    start_time: Optional[datetime] = None,
                                    duration_minutes: int = 96,
                                    time_step_seconds: int = 30,
                                    constellation: str = 'unknown') -> Dict[str, Any]:
        """
        計算衛星192點時間序列軌道數據 - 修復版：正確使用TLE基準時間
        
        Args:
            satellite_data: 衛星數據（包含skyfield satellite對象）
            start_time: 起始時間，符合@docs要求使用TLE文件日期
            duration_minutes: 預測時間窗口（分鐘）
            time_step_seconds: 時間步長（秒）
            
        Returns:
            包含192個時間點軌道數據的字典
        """
        
        # 🎯 修復：絕不使用當前時間作為默認值，符合@docs要求
        if start_time is None:
            # 如果沒有提供start_time，這是一個嚴重錯誤，應該拋出異常
            raise ValueError("start_time 不能為 None！@docs要求必須使用TLE文件日期作為基準時間")
        
        # 🎯 驗證時間基準符合@docs要求
        current_time = datetime.now(timezone.utc)
        time_diff_hours = abs((start_time - current_time).total_seconds() / 3600)
        
        # 如果時間差異小於1小時，很可能傳遞了錯誤的當前時間
        if time_diff_hours < 1:
            logger.warning(f"⚠️  時間基準可能錯誤：start_time={start_time.isoformat()}, 與當前時間差異僅{time_diff_hours:.1f}小時")
            logger.warning("⚠️  @docs要求：必須使用TLE文件日期作為基準時間，而非當前時間！")
        
        logger.info(f"🕐 使用TLE基準時間: {start_time.isoformat()}")
        logger.info(f"📊 計算參數: {duration_minutes}分鐘, {time_step_seconds}秒間隔, 預期{(duration_minutes*60)//time_step_seconds}個時間點")
        
        satellite = satellite_data['satellite_object']
        
        # 生成時間點序列
        time_points = []
        current_time = start_time
        
        total_points = (duration_minutes * 60) // time_step_seconds
        
        for i in range(total_points):
            time_points.append(current_time + timedelta(seconds=i * time_step_seconds))
        
        # 轉換為skyfield時間對象 (確保UTC時區)
        skyfield_times = []
        for t in time_points:
            # 確保時間有UTC時區信息
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            # 轉換為skyfield時間格式
            skyfield_times.append(self.ts.utc(t.year, t.month, t.day, t.hour, t.minute, t.second))
        
        position_timeseries = []
        
        for i, (dt, t) in enumerate(zip(time_points, skyfield_times)):
            try:
                # 計算衛星在ECI座標系中的位置和速度
                geocentric = satellite.at(t)
                
                # 地理座標
                subpoint = wgs84.subpoint(geocentric)
                lat_deg = float(subpoint.latitude.degrees)
                lon_deg = float(subpoint.longitude.degrees)  
                altitude_km = float(subpoint.elevation.km)
                
                # 相對觀測者的位置
                difference = satellite.at(t) - self.observer_position.at(t)
                topocentric = difference.altaz()
                
                # 提取位置、速度、觀測角度
                position_km = geocentric.position.km
                velocity_km_s = geocentric.velocity.km_per_s if hasattr(geocentric, 'velocity') else [0, 0, 0]
                
                # 確保位置和速度是列表格式
                if hasattr(position_km, 'tolist'):
                    position_km = position_km.tolist()
                if hasattr(velocity_km_s, 'tolist'):
                    velocity_km_s = velocity_km_s.tolist()
                
                # Skyfield的topocentric返回(elevation, azimuth, distance)
                elevation = topocentric[0] 
                azimuth = topocentric[1]
                distance = topocentric[2]
                
                # 安全提取純量值
                elevation_deg = float(elevation.degrees) if hasattr(elevation, 'degrees') else float(elevation)
                azimuth_deg = float(azimuth.degrees) if hasattr(azimuth, 'degrees') else float(azimuth)  
                range_km = float(distance.km) if hasattr(distance, 'km') else float(distance)
                
                # 計算range rate (逼向速度)
                range_rate_km_s = 0.0  # 簡化版本，可以通過數值微分計算
                
                position_data = {
                    'time_index': i,
                    'utc_time': dt.isoformat(),
                    'julian_date': t.ut1,
                    
                    # ECI位置和速度
                    'eci_position_km': position_km,
                    'eci_velocity_km_s': velocity_km_s,
                    
                    # 地理座標
                    'geodetic': {
                        'latitude_deg': lat_deg,
                        'longitude_deg': lon_deg,
                        'altitude_km': altitude_km
                    },
                    
                    # 相對NTPU觀測者
                    'relative_to_observer': {
                        'elevation_deg': elevation_deg,
                        'azimuth_deg': azimuth_deg,
                        'range_km': range_km,
                        'range_rate_km_s': range_rate_km_s,
                        'is_visible': self._calculate_visibility(elevation_deg, constellation)
                    }
                }
                
                position_timeseries.append(position_data)
                
            except Exception as e:
                logger.error(f"時間點{i}計算失敗: {e}")
                continue
        
        # 分析可見性窗口
        visibility_analysis = self._analyze_visibility_windows(position_timeseries)
        
        # 🎯 修復後的調試信息
        visible_count = sum(1 for pos in position_timeseries if pos['relative_to_observer']['is_visible'])
        visibility_pct = (visible_count / len(position_timeseries) * 100) if position_timeseries else 0
        
        logger.info(f"✅ {satellite_data['satellite_name']}: 計算完成 {len(position_timeseries)}/{total_points} 時間點")
        logger.info(f"📊 可見性: {visible_count}個時間點 ({visibility_pct:.1f}%)")
        
        result = {
            'satellite_id': satellite_data['satellite_name'],
            'norad_id': satellite_data['norad_id'],
            'orbital_elements': satellite_data['orbital_elements'],
            'orbital_period_minutes': satellite_data['orbital_period_minutes'],
            
            'timeseries_metadata': {
                'start_time': start_time.isoformat(),  # 🎯 記錄實際使用的TLE基準時間
                'duration_minutes': duration_minutes,
                'time_step_seconds': time_step_seconds,
                'total_points': len(position_timeseries),
                'calculation_timestamp': datetime.now(timezone.utc).isoformat(),
                # 🎯 新增：時間基準策略記錄
                'time_base_strategy': 'tle_file_date_based_for_reproducible_research',
                'time_base_verification': {
                    'tle_base_time_used': start_time.isoformat(),
                    'current_time_for_reference': current_time.isoformat(),
                    'time_difference_hours': time_diff_hours
                }
            },
            
            'position_timeseries': position_timeseries,
            'visibility_analysis': visibility_analysis
        }
        
        return result
    
    def _analyze_visibility_windows(self, position_timeseries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析可見性窗口，用於軌道相位算法
        
        Args:
            position_timeseries: 位置時間序列數據
            
        Returns:
            可見性分析結果
        """
        # 修復數組判斷問題
        visible_points = []
        for p in position_timeseries:
            is_visible = p['relative_to_observer']['is_visible']
            # 確保is_visible是boolean值
            if isinstance(is_visible, (list, tuple, np.ndarray)):
                is_visible = bool(is_visible[0]) if len(is_visible) > 0 else False
            if is_visible:
                visible_points.append(p)
        
        # 統計可見性
        total_points = len(position_timeseries)
        visible_points_count = len(visible_points)
        visibility_percentage = (visible_points_count / total_points * 100) if total_points > 0 else 0
        
        # 尋找連續可見窗口
        visibility_windows = []
        current_window_start = None
        
        for i, point in enumerate(position_timeseries):
            is_visible = point['relative_to_observer']['is_visible']
            # 確保is_visible是boolean值
            if isinstance(is_visible, (list, tuple, np.ndarray)):
                is_visible = bool(is_visible[0]) if len(is_visible) > 0 else False
            
            if is_visible and current_window_start is None:
                current_window_start = i
            elif not is_visible and current_window_start is not None:
                # 窗口結束
                visibility_windows.append({
                    'start_index': current_window_start,
                    'end_index': i - 1,
                    'duration_minutes': (i - current_window_start) * 0.5,  # 30秒間隔
                    'max_elevation_deg': max([p['relative_to_observer']['elevation_deg'] 
                                            for p in position_timeseries[current_window_start:i]])
                })
                current_window_start = None
        
        # 處理最後一個窗口
        if current_window_start is not None:
            visibility_windows.append({
                'start_index': current_window_start,
                'end_index': len(position_timeseries) - 1,
                'duration_minutes': (len(position_timeseries) - current_window_start) * 0.5,
                'max_elevation_deg': max([p['relative_to_observer']['elevation_deg'] 
                                        for p in position_timeseries[current_window_start:]])
            })
        
        return {
            'total_points': total_points,
            'visible_points': visible_points_count,
            'visibility_percentage': visibility_percentage,
            'visibility_windows_count': len(visibility_windows),
            'visibility_windows': visibility_windows,
            
            # 軌道相位分析關鍵指標
            'orbital_phase_metrics': {
                'current_mean_anomaly_deg': position_timeseries[0]['relative_to_observer'].get('mean_anomaly_deg', 0) if position_timeseries else 0,
                'mean_anomaly_at_peak_elevation': 0,  # 可以進一步計算
                'optimal_handover_phase': 0  # 為軌道相位位移算法預留
            }
        }

    def process_constellation_tle(self, tle_file_path: Path, constellation_name: str, 
                              tle_base_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        處理整個星座的TLE文件，生成192點時間序列數據 - 修復版：正確使用TLE基準時間
        
        Args:
            tle_file_path: TLE檔案路徑
            constellation_name: 星座名稱（starlink或oneweb）
            tle_base_time: TLE基準時間，符合@docs要求使用TLE文件日期
            
        Returns:
            整個星座的軌道計算結果
        """
        logger.info(f"📡 開始處理 {constellation_name} 星座TLE數據")
        logger.info(f"  檔案: {tle_file_path}")
        
        # 🎯 修復：檢查TLE基準時間
        if tle_base_time is None:
            # 從檔案名提取TLE日期作為基準時間
            import re
            file_name = tle_file_path.name
            date_match = re.search(r'(\d{8})', file_name)  # 提取YYYYMMDD格式
            
            if date_match:
                date_str = date_match.group(1)
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                tle_base_time = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
                logger.info(f"🕐 從檔案名提取TLE基準時間: {tle_base_time.isoformat()}")
            else:
                # 如果無法提取日期，拋出錯誤
                raise ValueError(f"無法從TLE檔案名 '{file_name}' 提取日期，且未提供tle_base_time參數")
        else:
            logger.info(f"🕐 使用提供的TLE基準時間: {tle_base_time.isoformat()}")
        
        if not tle_file_path.exists():
            logger.error(f"TLE檔案不存在: {tle_file_path}")
            return {'satellites': [], 'metadata': {'error': 'TLE file not found'}}
        
        satellites_data = []
        
        try:
            with open(tle_file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # 每3行為一組TLE數據
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    tle_group = lines[i:i+3]
                    
                    # 解析TLE
                    satellite_data = self.parse_tle_line(tle_group)
                    if satellite_data is None:
                        continue
                    
                    # 🎯 關鍵修復：傳遞TLE基準時間給軌道計算
                    orbital_data = self.calculate_position_timeseries(
                        satellite_data, 
                        start_time=tle_base_time,  # 🎯 使用TLE基準時間而非當前時間
                        constellation=constellation_name
                    )
                    satellites_data.append(orbital_data)
                    
                    if len(satellites_data) % 100 == 0:
                        logger.info(f"  已處理 {len(satellites_data)} 顆衛星...")
        
        except Exception as e:
            logger.error(f"處理TLE檔案失敗: {e}")
            return {'satellites': [], 'metadata': {'error': str(e)}}
        
        # 🎯 修復：提取TLE檔案日期並記錄數據血統
        file_date = 'unknown'
        import re
        date_match = re.search(r'(\d{8})', tle_file_path.name)
        if date_match:
            file_date = date_match.group(1)
        
        result = {
            'constellation': constellation_name,
            'satellites': satellites_data,
            'metadata': {
                'total_satellites': len(satellites_data),
                'tle_file': str(tle_file_path),
                'tle_file_date': file_date,  # 🎯 記錄TLE檔案日期
                'tle_base_time_used': tle_base_time.isoformat(),  # 🎯 記錄實際使用的基準時間
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'observer_position': {
                    'latitude_deg': self.observer_lat,
                    'longitude_deg': self.observer_lon,
                    'elevation_m': self.observer_elevation_m
                },
                # 🎯 新增數據血統追蹤
                'data_lineage': {
                    'time_base_strategy': 'tle_file_date_based_for_reproducible_research',
                    'tle_file_date': file_date,
                    'tle_base_time': tle_base_time.isoformat(),
                    'processing_execution_time': datetime.now(timezone.utc).isoformat()
                }
            }
        }
        
        logger.info(f"✅ {constellation_name} 星座處理完成: {len(satellites_data)} 顆衛星")
        return result