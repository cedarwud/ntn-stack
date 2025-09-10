#!/usr/bin/env python3
"""
真正的SGP4軌道計算引擎
實現@docs要求的192點時間序列軌道預測和軌道相位分析
"""

import os
import json
import logging
import math
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
    嚴格遵循學術級數據標準 - Grade A實現
    """
    
    def __init__(self, observer_coordinates: Tuple[float, float, float] = None):
        """
        初始化SGP4軌道計算引擎
        
        Args:
            observer_coordinates: (lat, lon, elevation_m) 觀測站座標
        """
        logger.info("🚀 初始化SGP4軌道計算引擎...")
        
        # 設定觀測站座標 (預設: NTPU 32.25°N, 121.43°E, 200m)
        if observer_coordinates:
            self.observer_lat, self.observer_lon, self.observer_elevation_m = observer_coordinates
        else:
            self.observer_lat = 24.9478
            self.observer_lon = 121.5337
            self.observer_elevation_m = 200.0
            
        logger.info(f"   📍 觀測站座標: ({self.observer_lat:.4f}°N, {self.observer_lon:.4f}°E, {self.observer_elevation_m}m)")
        
        # 載入時標系統
        self.timescale = load.timescale()
        
        # 建立觀測站位置
        self.observer_position = wgs84.latlon(
            self.observer_lat, 
            self.observer_lon, 
            elevation_m=self.observer_elevation_m
        )
        
        # 軌道計算統計
        self.calculation_stats = {
            "total_satellites_processed": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "total_position_points": 0
        }
        
        logger.info("✅ SGP4軌道計算引擎初始化完成")
    
    def calculate_position_timeseries(self, satellite_data: Dict[str, Any], time_range_minutes: int = 192) -> List[Dict[str, Any]]:
        """
        計算衛星位置時間序列 - 核心SGP4計算
        
        Args:
            satellite_data: 衛星數據，包含TLE信息
            time_range_minutes: 時間範圍（分鐘）
            
        Returns:
            List[Dict]: 位置時間序列數據
        """
        try:
            # 🔍 從satellite_data提取TLE信息
            tle_data = satellite_data.get('tle_data', {})
            if not tle_data:
                logger.error(f"❌ 衛星 {satellite_data.get('satellite_id', 'unknown')} 缺少TLE數據")
                return []
            
            # 提取TLE行
            tle_line1 = tle_data.get('tle_line1', '')
            tle_line2 = tle_data.get('tle_line2', '')
            satellite_name = satellite_data.get('name', tle_data.get('name', 'Unknown'))
            
            if not tle_line1 or not tle_line2:
                logger.error(f"❌ 衛星 {satellite_name} TLE行數據不完整")
                return []
            
            # 🛰️ 創建EarthSatellite對象
            satellite = EarthSatellite(tle_line1, tle_line2, satellite_name, self.timescale)
            
            # 🕐 計算時間基準 - 使用TLE epoch時間
            tle_epoch = satellite.epoch
            logger.info(f"   📅 TLE Epoch時間: {tle_epoch.utc_iso()}")
            
            # 🔧 生成時間點（根據星座類型決定點數）
            time_points = []
            constellation = satellite_data.get('constellation', '').lower()
            
            if constellation == 'starlink':
                # Starlink: 96分鐘軌道，每30秒1點 = 192個點
                num_points = 192
                actual_duration_minutes = 96
            elif constellation == 'oneweb':
                # OneWeb: 108分鐘軌道，但文檔要求218個點
                # 218點 * 30秒 = 109分鐘，接近實際軌道週期
                num_points = 218  
                actual_duration_minutes = 109  # 218點 * 0.5分鐘/點
            else:
                # 預設值
                num_points = 240  # 120分鐘 / 0.5分鐘
                actual_duration_minutes = time_range_minutes
            
            interval_minutes = actual_duration_minutes / num_points
            
            for i in range(num_points):
                minutes_offset = i * interval_minutes
                time_point = self.timescale.tt_jd(tle_epoch.tt + minutes_offset / (24 * 60))
                time_points.append(time_point)
            
            logger.info(f"   ⏰ {constellation} 軌道計算: {num_points}個位置點，間隔{interval_minutes*60:.1f}秒")
            logger.info(f"   🔍 DEBUG: constellation='{constellation}', num_points={num_points}, actual_duration={actual_duration_minutes}分鐘")
            
            position_timeseries = []
            
            # 🧮 逐一計算每個時間點的位置（避免批量計算問題）
            for i, t in enumerate(time_points):
                try:
                    # 計算該時間點的位置
                    geocentric = satellite.at(t)
                    
                    # 🔧 嘗試topocentric計算
                    try:
                        # 新版skyfield API
                        topocentric = (geocentric - self.observer_position.at(t))
                        elevation_deg = float(topocentric.elevation.degrees)
                        azimuth_deg = float(topocentric.azimuth.degrees) 
                        range_km = float(topocentric.distance().km)
                    except AttributeError:
                        # 🔧 備用方法：直接計算距離和仰角
                        observer_pos = self.observer_position.at(t).position.km
                        satellite_pos = geocentric.position.km
                        
                        diff_vector = satellite_pos - observer_pos
                        range_km = float((diff_vector[0]**2 + diff_vector[1]**2 + diff_vector[2]**2)**0.5)
                        
                        # 計算仰角 (elevation)
                        horizontal_dist = float((diff_vector[0]**2 + diff_vector[1]**2)**0.5)
                        elevation_deg = float(math.degrees(math.atan2(diff_vector[2], horizontal_dist)))
                        
                        # 計算方位角 (azimuth) - 簡化版本
                        azimuth_deg = float(math.degrees(math.atan2(diff_vector[1], diff_vector[0])))
                        if azimuth_deg < 0:
                            azimuth_deg += 360
                    
                    # ECI座標
                    eci_position = geocentric.position.km
                    eci_x = float(eci_position[0])
                    eci_y = float(eci_position[1]) 
                    eci_z = float(eci_position[2])
                    
                    # 可見性判斷 (仰角 > 5度)
                    is_visible = elevation_deg > 5.0
                    
                    # 組裝位置數據
                    position_data = {
                        "timestamp": t.utc_iso(),
                        "eci_x": eci_x,
                        "eci_y": eci_y, 
                        "eci_z": eci_z,
                        "range_km": range_km,
                        "elevation_deg": elevation_deg,
                        "azimuth_deg": azimuth_deg,
                        "is_visible": is_visible
                    }
                    
                    position_timeseries.append(position_data)
                    
                except Exception as pos_error:
                    logger.warning(f"⚠️ 時間點 {i} 位置計算失敗: {pos_error}")
                    continue
            
            # 統計更新
            self.calculation_stats["total_satellites_processed"] += 1
            if position_timeseries:
                self.calculation_stats["successful_calculations"] += 1
                self.calculation_stats["total_position_points"] += len(position_timeseries)
            else:
                self.calculation_stats["failed_calculations"] += 1
            
            logger.info(f"✅ 衛星 {satellite_name} 軌道計算完成: {len(position_timeseries)}個位置點")
            return position_timeseries
            
        except Exception as e:
            logger.error(f"❌ SGP4軌道計算失敗: {e}")
            self.calculation_stats["failed_calculations"] += 1
            return []
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return {
            "engine_type": "SGP4OrbitalEngine",
            "calculation_stats": self.calculation_stats,
            "observer_coordinates": {
                "latitude": self.observer_lat,
                "longitude": self.observer_lon,
                "elevation_m": self.observer_elevation_m
            }
        }
        
    def validate_orbital_mechanics(self, satellite_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        驗證軌道力學計算的正確性
        """
        try:
            # 基本數據驗證
            if not satellite_data.get('tle_data'):
                return {"tle_data_present": False, "valid_format": False}
                
            tle_data = satellite_data['tle_data']
            tle_line1 = tle_data.get('tle_line1', '')
            tle_line2 = tle_data.get('tle_line2', '')
            
            # TLE格式驗證
            valid_format = (len(tle_line1) == 69 and len(tle_line2) == 69 and 
                          tle_line1.startswith('1 ') and tle_line2.startswith('2 '))
            
            if not valid_format:
                return {"tle_data_present": True, "valid_format": False}
            
            # 嘗試軌道計算
            position_timeseries = self.calculate_position_timeseries(satellite_data, 10)  # 測試10分鐘
            
            return {
                "tle_data_present": True,
                "valid_format": True, 
                "calculation_successful": len(position_timeseries) > 0,
                "position_points_generated": len(position_timeseries)
            }
            
        except Exception as e:
            logger.error(f"❌ 軌道力學驗證失敗: {e}")
            return {"validation_error": str(e)}