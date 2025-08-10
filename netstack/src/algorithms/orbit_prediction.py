#!/usr/bin/env python3
"""
軌道預測算法模組 - 精簡版

專注於核心 SGP4 軌道預測功能，移除未使用的引擎管理系統。

核心功能：
- SGP4/SDP4 軌道傳播算法
- TLE 數據處理
- 衛星位置和速度計算
- 大氣阻力和重力攝動建模

移除功能：
- 複雜的引擎管理系統
- 未使用的批量處理方法
- 實驗性預測功能
- 過度複雜的工廠函數
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import structlog

# 第三方依賴 - 保留核心計算需要的
try:
    from sgp4.earth_gravity import wgs72
    from sgp4.io import twoline2rv
    from sgp4 import exporter
    SGP4_AVAILABLE = True
except ImportError:
    SGP4_AVAILABLE = False

logger = structlog.get_logger(__name__)


class OrbitModelType(Enum):
    """軌道模型類型"""
    SGP4 = "sgp4"
    SDP4 = "sdp4"  # 用於深空軌道
    

class TLEData:
    """TLE 數據類 - 簡化版"""
    
    def __init__(self, satellite_id: str, satellite_name: str, 
                 line1: str, line2: str, epoch: datetime):
        self.satellite_id = satellite_id
        self.satellite_name = satellite_name
        self.line1 = line1
        self.line2 = line2 
        self.epoch = epoch
        
        # 從 TLE 解析軌道參數
        self._parse_tle_parameters()
    
    def _parse_tle_parameters(self):
        """解析 TLE 參數"""
        try:
            # 解析 Line 1
            self.catalog_number = int(self.line1[2:7])
            self.mean_motion_revs_per_day = float(self.line2[52:63])
            
            # 解析 Line 2  
            self.inclination_deg = float(self.line2[8:16])
            self.raan_deg = float(self.line2[17:25])
            self.eccentricity = float('0.' + self.line2[26:33])
            self.argument_of_perigee_deg = float(self.line2[34:42])
            self.mean_anomaly_deg = float(self.line2[43:51])
            
        except (ValueError, IndexError) as e:
            logger.error(f"TLE 參數解析失敗: {e}")
            # 設置默認值
            self.catalog_number = 0
            self.mean_motion_revs_per_day = 15.0
            self.inclination_deg = 53.0
            self.raan_deg = 0.0
            self.eccentricity = 0.0
            self.argument_of_perigee_deg = 0.0
            self.mean_anomaly_deg = 0.0


@dataclass
class SatelliteState:
    """衛星狀態 - 簡化版"""
    satellite_id: str
    timestamp: datetime
    
    # 位置 (km, ECI 坐標系)
    position_x: float
    position_y: float  
    position_z: float
    
    # 速度 (km/s)
    velocity_x: float
    velocity_y: float
    velocity_z: float
    
    # 軌道參數
    altitude_km: float = 0.0
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0


class OrbitPredictionEngine:
    """軌道預測引擎 - 精簡版"""
    
    def __init__(self, engine_id: str = "default"):
        """
        初始化軌道預測引擎
        
        Args:
            engine_id: 引擎識別ID
        """
        self.engine_id = engine_id
        self.logger = logger.bind(engine=engine_id)
        
        # 簡化的內部狀態
        self.tle_database: Dict[str, TLEData] = {}
        self.sgp4_models: Dict[str, Any] = {}
        
        # 檢查 SGP4 可用性
        if not SGP4_AVAILABLE:
            self.logger.warning("SGP4 庫不可用，將使用簡化軌道模型")

    def add_satellite_tle(self, satellite_id: str, tle_data: TLEData) -> bool:
        """添加衛星 TLE 數據"""
        try:
            self.tle_database[satellite_id] = tle_data
            
            # 創建 SGP4 模型
            if SGP4_AVAILABLE:
                satellite = twoline2rv(tle_data.line1, tle_data.line2, wgs72)
                self.sgp4_models[satellite_id] = satellite
            
            self.logger.info(f"成功添加衛星 TLE: {satellite_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加 TLE 數據失敗 {satellite_id}: {e}")
            return False

    def predict_satellite_position(
        self, satellite_id: str, target_time: datetime
    ) -> Optional[SatelliteState]:
        """
        預測衛星位置 - 核心方法
        
        Args:
            satellite_id: 衛星 ID
            target_time: 目標時間
            
        Returns:
            衛星狀態或 None
        """
        try:
            if satellite_id not in self.tle_database:
                self.logger.error(f"找不到衛星 TLE 數據: {satellite_id}")
                return None
            
            tle_data = self.tle_database[satellite_id]
            
            # 使用 SGP4 計算
            if SGP4_AVAILABLE and satellite_id in self.sgp4_models:
                return self._sgp4_propagate(satellite_id, target_time)
            else:
                # 回退到簡化模型
                return self._simple_propagate(satellite_id, target_time)
                
        except Exception as e:
            self.logger.error(f"軌道預測失敗 {satellite_id}: {e}")
            return None

    def _sgp4_propagate(self, satellite_id: str, target_time: datetime) -> Optional[SatelliteState]:
        """SGP4 軌道傳播 - 核心算法"""
        try:
            satellite = self.sgp4_models[satellite_id]
            tle_data = self.tle_database[satellite_id]
            
            # 計算時間差 (分鐘)
            time_diff = (target_time - tle_data.epoch).total_seconds() / 60.0
            
            # SGP4 計算
            position, velocity = satellite.propagate(
                target_time.year, target_time.month, target_time.day,
                target_time.hour, target_time.minute, target_time.second
            )
            
            if position is None or velocity is None:
                self.logger.error(f"SGP4 傳播失敗: {satellite_id}")
                return None
            
            # 轉換為衛星狀態
            altitude = math.sqrt(sum(p**2 for p in position)) - 6371.0  # 地球半徑
            
            # 簡化的經緯度轉換
            lat, lon = self._eci_to_geodetic(position, target_time)
            
            return SatelliteState(
                satellite_id=satellite_id,
                timestamp=target_time,
                position_x=position[0],
                position_y=position[1], 
                position_z=position[2],
                velocity_x=velocity[0],
                velocity_y=velocity[1],
                velocity_z=velocity[2],
                altitude_km=altitude,
                latitude_deg=lat,
                longitude_deg=lon
            )
            
        except Exception as e:
            self.logger.error(f"SGP4 傳播計算失敗: {e}")
            return None

    def _simple_propagate(self, satellite_id: str, target_time: datetime) -> Optional[SatelliteState]:
        """簡化軌道傳播 (備用方法)"""
        try:
            tle_data = self.tle_database[satellite_id]
            
            # 計算時間差
            time_diff_hours = (target_time - tle_data.epoch).total_seconds() / 3600.0
            
            # 簡化的軌道計算
            mean_motion_rad_per_sec = tle_data.mean_motion_revs_per_day * 2 * math.pi / 86400
            orbit_angle = (tle_data.mean_anomaly_deg + 
                          mean_motion_rad_per_sec * time_diff_hours * 3600 * 180 / math.pi) % 360
            
            # 簡化的軌道半徑 (假設圓軌道)
            orbit_radius = 6371.0 + 550.0  # 地球半徑 + 典型 LEO 高度
            
            # 軌道位置計算
            orbit_angle_rad = math.radians(orbit_angle)
            inclination_rad = math.radians(tle_data.inclination_deg)
            raan_rad = math.radians(tle_data.raan_deg)
            
            # ECI 坐標計算 (簡化)
            x = orbit_radius * math.cos(orbit_angle_rad) * math.cos(raan_rad)
            y = orbit_radius * math.cos(orbit_angle_rad) * math.sin(raan_rad)  
            z = orbit_radius * math.sin(orbit_angle_rad) * math.sin(inclination_rad)
            
            # 簡化速度計算
            orbital_velocity = math.sqrt(398600.4418 / orbit_radius)  # GM_earth
            vx = -orbital_velocity * math.sin(orbit_angle_rad) * math.cos(raan_rad)
            vy = -orbital_velocity * math.sin(orbit_angle_rad) * math.sin(raan_rad)
            vz = orbital_velocity * math.cos(orbit_angle_rad) * math.sin(inclination_rad)
            
            # 經緯度轉換
            lat, lon = self._eci_to_geodetic([x, y, z], target_time)
            
            return SatelliteState(
                satellite_id=satellite_id,
                timestamp=target_time,
                position_x=x,
                position_y=y,
                position_z=z,
                velocity_x=vx,
                velocity_y=vy, 
                velocity_z=vz,
                altitude_km=orbit_radius - 6371.0,
                latitude_deg=lat,
                longitude_deg=lon
            )
            
        except Exception as e:
            self.logger.error(f"簡化軌道傳播失敗: {e}")
            return None

    def _eci_to_geodetic(self, position: List[float], timestamp: datetime) -> Tuple[float, float]:
        """ECI 到經緯度轉換 - 簡化版"""
        try:
            x, y, z = position
            
            # 計算緯度
            r_xy = math.sqrt(x*x + y*y)
            latitude = math.degrees(math.atan2(z, r_xy))
            
            # 計算經度 (考慮地球自轉)
            greenwich_hour_angle = (timestamp.hour + timestamp.minute/60.0) * 15.0
            longitude = math.degrees(math.atan2(y, x)) - greenwich_hour_angle
            
            # 標準化經度到 [-180, 180]
            longitude = ((longitude + 180) % 360) - 180
            
            return latitude, longitude
            
        except Exception as e:
            self.logger.error(f"坐標轉換失敗: {e}")
            return 0.0, 0.0

    def predict_multiple_satellites(
        self, satellite_ids: List[str], target_time: datetime
    ) -> Dict[str, Optional[SatelliteState]]:
        """批量預測多個衛星位置"""
        results = {}
        
        for satellite_id in satellite_ids:
            results[satellite_id] = self.predict_satellite_position(satellite_id, target_time)
        
        return results

    def get_satellite_count(self) -> int:
        """獲取已載入的衛星數量"""
        return len(self.tle_database)

    def get_satellite_list(self) -> List[str]:
        """獲取衛星 ID 列表"""
        return list(self.tle_database.keys())

    def remove_satellite(self, satellite_id: str) -> bool:
        """移除衛星數據"""
        try:
            if satellite_id in self.tle_database:
                del self.tle_database[satellite_id]
                
            if satellite_id in self.sgp4_models:
                del self.sgp4_models[satellite_id]
                
            self.logger.info(f"成功移除衛星: {satellite_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除衛星失敗 {satellite_id}: {e}")
            return False

    def clear_all_satellites(self) -> bool:
        """清除所有衛星數據"""
        try:
            self.tle_database.clear()
            self.sgp4_models.clear()
            self.logger.info("成功清除所有衛星數據")
            return True
            
        except Exception as e:
            self.logger.error(f"清除衛星數據失敗: {e}")
            return False


# 簡化的工廠函數
def create_orbit_prediction_engine(engine_id: str = "default") -> OrbitPredictionEngine:
    """創建軌道預測引擎 - 簡化版"""
    return OrbitPredictionEngine(engine_id)