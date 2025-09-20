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


class SGP4Position:
    """SGP4位置結果"""
    def __init__(self, x: float, y: float, z: float):
        self.x = x  # km
        self.y = y  # km
        self.z = z  # km


class SGP4Velocity:
    """SGP4速度結果"""
    def __init__(self, x: float, y: float, z: float):
        self.x = x  # km/s
        self.y = y  # km/s
        self.z = z  # km/s


class SGP4CalculationResult:
    """SGP4計算結果"""
    def __init__(self, position: SGP4Position = None, velocity: SGP4Velocity = None, 
                 calculation_base_time: datetime = None, algorithm_used: str = "SGP4",
                 calculation_successful: bool = False, data_source_verified: bool = False,
                 time_warning: str = None, error_message: str = None, satellite_name: str = None,
                 data_lineage: Dict = None):
        self.position = position
        self.velocity = velocity
        self.calculation_base_time = calculation_base_time
        self.algorithm_used = algorithm_used
        self.calculation_successful = calculation_successful
        self.data_source_verified = data_source_verified
        self.time_warning = time_warning
        self.error_message = error_message
        self.satellite_name = satellite_name
        self.data_lineage = data_lineage or {}


class SGP4OrbitalEngine:
    """
    真正的SGP4軌道計算引擎
    嚴格遵循學術級數據標準 - Grade A實現
    """
    
    def __init__(self, observer_coordinates: Tuple[float, float, float] = None, eci_only_mode: bool = False):
        """
        初始化SGP4軌道計算引擎
        
        Args:
            observer_coordinates: (lat, lon, elevation_m) 觀測站座標 (Stage 1不需要)
            eci_only_mode: 僅輸出ECI座標模式 (Stage 1使用)
        """
        logger.info("🚀 初始化SGP4軌道計算引擎...")
        
        self.eci_only_mode = eci_only_mode
        
        # 載入時標系統
        self.timescale = load.timescale()
        
        # 只有在非ECI-only模式下才設定觀測站（Stage 2會使用）
        if not eci_only_mode and observer_coordinates:
            self.observer_lat, self.observer_lon, self.observer_elevation_m = observer_coordinates
            logger.info(f"   📍 觀測站座標: ({self.observer_lat:.4f}°N, {self.observer_lon:.4f}°E, {self.observer_elevation_m}m)")
            
            # 建立觀測站位置
            self.observer_position = wgs84.latlon(
                self.observer_lat, 
                self.observer_lon, 
                elevation_m=self.observer_elevation_m
            )
        else:
            self.observer_position = None
            if eci_only_mode:
                logger.info("   🎯 ECI-only模式: 不設定觀測站座標")
            else:
                logger.info("   ⚠️ 未提供觀測站座標，僅輸出ECI座標")
        
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
        計算衛星位置時間序列 - 純ECI座標輸出（符合Stage 1文檔規範）
        
        🚨 關鍵修復：使用TLE epoch時間作為計算基準，而非當前系統時間
        
        Args:
            satellite_data: 衛星數據，包含TLE信息
            time_range_minutes: 時間範圍（分鐘）
            
        Returns:
            List[Dict]: 僅包含ECI座標的位置時間序列數據
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
            
            # 🚨 關鍵修復：使用TLE epoch時間作為計算基準時間
            tle_epoch = satellite.epoch
            calculation_base_time = tle_epoch
            
            logger.info(f"   📅 TLE Epoch時間: {tle_epoch.utc_iso()}")
            logger.info(f"   🎯 計算基準時間: {calculation_base_time.utc_iso()}")
            
            # 檢查TLE數據新鮮度（重要：TLE精度隨時間衰減）
            current_time = self.timescale.now()

            # 正確計算時間差（以天為單位）
            time_diff_seconds = abs((current_time.utc_datetime() - tle_epoch.utc_datetime()).total_seconds())
            time_diff_days = time_diff_seconds / 86400.0  # 86400秒 = 1天

            logger.info(f"📅 TLE Epoch: {tle_epoch.utc_datetime().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            logger.info(f"🕐 當前時間: {current_time.utc_datetime().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            logger.info(f"⏱️ TLE數據年齡: {time_diff_days:.1f} 天")

            # TLE精度警告（重要：超過3天精度明顯下降）
            if time_diff_days > 7:
                logger.error(f"🚨 TLE數據過舊({time_diff_days:.1f}天)，軌道預測可能嚴重失準！")
            elif time_diff_days > 3:
                logger.warning(f"⚠️ TLE數據較舊({time_diff_days:.1f}天)，建議使用更新數據提高精度")
            elif time_diff_days > 1:
                logger.info(f"ℹ️ TLE數據年齡({time_diff_days:.1f}天)在可接受範圍內")
            else:
                logger.info(f"✅ TLE數據非常新鮮({time_diff_days:.1f}天)，預測精度最佳")
            
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
                # 🚨 關鍵修復：基於TLE epoch時間計算，而非當前時間
                time_point = self.timescale.tt_jd(tle_epoch.tt + minutes_offset / (24 * 60))
                time_points.append(time_point)
            
            logger.info(f"   ⏰ {constellation} 軌道計算: {num_points}個位置點，間隔{interval_minutes*60:.1f}秒")
            logger.info(f"   🔍 DEBUG: constellation='{constellation}', num_points={num_points}, actual_duration={actual_duration_minutes}分鐘")
            
            position_timeseries = []
            
            # 🧮 逐一計算每個時間點的位置（僅計算ECI座標）
            for i, t in enumerate(time_points):
                try:
                    # 計算該時間點的位置
                    geocentric = satellite.at(t)
                    
                    # ECI座標（地心慣性坐標系）
                    eci_position = geocentric.position.km
                    eci_x = float(eci_position[0])
                    eci_y = float(eci_position[1]) 
                    eci_z = float(eci_position[2])
                    
                    # 速度向量（如果需要）
                    eci_velocity = geocentric.velocity.km_per_s
                    eci_vx = float(eci_velocity[0])
                    eci_vy = float(eci_velocity[1])
                    eci_vz = float(eci_velocity[2])
                    
                    # 組裝純ECI位置數據（Stage 1只輸出軌道計算結果）
                    position_data = {
                        "timestamp": t.utc_iso(),
                        "position_eci": {
                            "x": eci_x,
                            "y": eci_y,
                            "z": eci_z
                        },
                        "velocity_eci": {
                            "x": eci_vx,
                            "y": eci_vy,
                            "z": eci_vz
                        },
                        # 🆕 添加計算元數據
                        "calculation_metadata": {
                            "tle_epoch": tle_epoch.utc_iso(),
                            "time_from_epoch_minutes": minutes_offset,
                            "calculation_base": "tle_epoch_time",
                            "real_sgp4_calculation": True
                        }
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
                logger.info(f"✅ 衛星 {satellite_name} ECI軌道計算完成: {len(position_timeseries)}個位置點")
            else:
                self.calculation_stats["failed_calculations"] += 1
                logger.error(f"❌ 衛星 {satellite_name} 軌道計算失敗: 無有效位置點")
            
            return position_timeseries
            
        except Exception as e:
            logger.error(f"❌ SGP4軌道計算失敗: {e}")
            self.calculation_stats["failed_calculations"] += 1
            return []
    
    def calculate_position(self, tle_data: Dict[str, Any], calculation_time: datetime) -> 'SGP4CalculationResult':
        """
        計算指定時間的衛星位置 - TDD測試專用方法
        
        Args:
            tle_data: TLE數據字典，包含line1, line2等
            calculation_time: 計算時間 (必須使用TLE epoch時間作為基準)
            
        Returns:
            SGP4CalculationResult: 計算結果對象
        """
        import warnings
        
        try:
            # 🚨 關鍵：記錄計算基準時間
            calculation_base_time = calculation_time
            
            # 提取TLE數據
            tle_line1 = tle_data.get('line1', '')
            tle_line2 = tle_data.get('line2', '')
            satellite_name = tle_data.get('satellite_name', 'Unknown')
            
            if not tle_line1 or not tle_line2:
                raise ValueError(f"TLE數據不完整: {satellite_name}")
            
            # 創建Skyfield衛星對象
            satellite = EarthSatellite(tle_line1, tle_line2, satellite_name, self.timescale)
            
            # 轉換時間到Skyfield時間對象
            skyfield_time = self.timescale.from_datetime(calculation_time)
            
            # SGP4軌道計算
            geocentric = satellite.at(skyfield_time)
            
            # 提取位置和速度 (ECI座標系)
            position = geocentric.position.km
            velocity = geocentric.velocity.km_per_s
            
            # 檢查TLE時間基準和當前計算時間的差異
            tle_epoch = tle_data.get('epoch_datetime')
            time_warning = None
            
            if tle_epoch:
                time_diff_days = abs((calculation_time - tle_epoch).days)
                if time_diff_days > 3:
                    time_warning = f"TLE數據時間差{time_diff_days}天，可能影響計算精度"
                    logger.warning(f"⚠️ {time_warning}")
                    # 🔧 修復：同時發出 Python 警告供測試檢測
                    warnings.warn(time_warning, UserWarning, stacklevel=2)
            
            # 創建結果對象
            result = SGP4CalculationResult(
                position=SGP4Position(position[0], position[1], position[2]),
                velocity=SGP4Velocity(velocity[0], velocity[1], velocity[2]),
                calculation_base_time=calculation_base_time,
                algorithm_used="SGP4",
                calculation_successful=True,
                data_source_verified=tle_data.get('is_real_data', False),
                time_warning=time_warning,
                satellite_name=satellite_name,
                data_lineage={
                    'tle_epoch': tle_epoch.isoformat() if tle_epoch else None,
                    'calculation_time': calculation_time.isoformat(),
                    'time_difference_days': abs((calculation_time - tle_epoch).days) if tle_epoch else None,
                    'data_source': tle_data.get('data_source', 'Unknown')
                }
            )
            
            # 更新統計
            self.calculation_stats["successful_calculations"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"❌ SGP4單點計算失敗: {e}")
            self.calculation_stats["failed_calculations"] += 1
            
            # 返回失敗結果
            return SGP4CalculationResult(
                position=None,
                velocity=None,
                calculation_base_time=calculation_time,
                algorithm_used="SGP4",
                calculation_successful=False,
                error_message=str(e),
                data_source_verified=False,
                satellite_name=tle_data.get('satellite_name', 'Unknown')
            )

    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return {
            "engine_type": "SGP4OrbitalEngine",
            "calculation_stats": self.calculation_stats,
            "observer_coordinates": {
                "latitude": getattr(self, 'observer_lat', None),
                "longitude": getattr(self, 'observer_lon', None),
                "elevation_m": getattr(self, 'observer_elevation_m', None)
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