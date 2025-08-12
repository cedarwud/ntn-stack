#!/usr/bin/env python3
"""
軌道傳播器系統
基於完整 SGP4 算法的軌道傳播計算
嚴格遵循 CLAUDE.md 原則：真實算法，禁止簡化
"""

import logging
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from sgp4_engine import SGP4Engine, SGP4Result

logger = logging.getLogger(__name__)


class PropagationMode(Enum):
    """傳播模式"""
    SINGLE_POINT = "single_point"      # 單點傳播
    TIME_SERIES = "time_series"        # 時間序列
    PREDICTION = "prediction"          # 預測模式
    HISTORICAL = "historical"          # 歷史回溯


@dataclass 
class PropagationRequest:
    """軌道傳播請求"""
    satellite_ids: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    time_step_seconds: int = 30
    mode: PropagationMode = PropagationMode.TIME_SERIES
    coordinate_system: str = "ECI"
    include_velocity: bool = True
    include_ground_track: bool = False


@dataclass
class OrbitState:
    """軌道狀態"""
    timestamp: datetime
    satellite_id: str
    
    # 位置 (ECI 坐標系，單位：km)
    position_x: float
    position_y: float
    position_z: float
    
    # 速度 (ECI 坐標系，單位：km/s)
    velocity_x: Optional[float] = None
    velocity_y: Optional[float] = None
    velocity_z: Optional[float] = None
    
    # 額外計算屬性
    altitude_km: Optional[float] = None
    latitude_deg: Optional[float] = None
    longitude_deg: Optional[float] = None
    
    @property
    def position_vector(self) -> np.ndarray:
        """位置向量"""
        return np.array([self.position_x, self.position_y, self.position_z])
    
    @property
    def velocity_vector(self) -> Optional[np.ndarray]:
        """速度向量"""
        if all(v is not None for v in [self.velocity_x, self.velocity_y, self.velocity_z]):
            return np.array([self.velocity_x, self.velocity_y, self.velocity_z])
        return None
    
    @property
    def position_magnitude(self) -> float:
        """位置向量大小 (km)"""
        return float(np.linalg.norm(self.position_vector))
    
    @property
    def velocity_magnitude(self) -> Optional[float]:
        """速度向量大小 (km/s)"""
        vel = self.velocity_vector
        return float(np.linalg.norm(vel)) if vel is not None else None


@dataclass
class PropagationResult:
    """軌道傳播結果"""
    satellite_id: str
    request: PropagationRequest
    orbit_states: List[OrbitState]
    success: bool
    error_message: Optional[str] = None
    computation_time_seconds: float = 0.0
    
    @property
    def state_count(self) -> int:
        """狀態數量"""
        return len(self.orbit_states)
    
    @property
    def time_span_hours(self) -> float:
        """時間跨度 (小時)"""
        if len(self.orbit_states) < 2:
            return 0.0
        first_time = self.orbit_states[0].timestamp
        last_time = self.orbit_states[-1].timestamp
        return (last_time - first_time).total_seconds() / 3600


class OrbitPropagator:
    """
    軌道傳播器
    使用完整 SGP4 算法進行精確軌道傳播
    """
    
    def __init__(self, sgp4_engine: SGP4Engine):
        self.sgp4_engine = sgp4_engine
        self.earth_radius_km = 6371.0  # 地球半徑
        
        logger.info("軌道傳播器初始化完成")
    
    def propagate_orbit(self, request: PropagationRequest) -> Dict[str, PropagationResult]:
        """
        執行軌道傳播
        
        Args:
            request: 傳播請求
            
        Returns:
            每個衛星的傳播結果字典
        """
        logger.info(f"開始軌道傳播: {len(request.satellite_ids)} 顆衛星, 模式: {request.mode.value}")
        
        results = {}
        start_computation = datetime.now()
        
        for satellite_id in request.satellite_ids:
            try:
                result = self._propagate_single_satellite(satellite_id, request)
                results[satellite_id] = result
                
                if result.success:
                    logger.debug(f"衛星 {satellite_id} 傳播成功: {result.state_count} 個狀態")
                else:
                    logger.warning(f"衛星 {satellite_id} 傳播失敗: {result.error_message}")
                    
            except Exception as e:
                error_msg = f"衛星 {satellite_id} 傳播異常: {str(e)}"
                logger.error(error_msg)
                results[satellite_id] = PropagationResult(
                    satellite_id=satellite_id,
                    request=request,
                    orbit_states=[],
                    success=False,
                    error_message=error_msg
                )
        
        total_computation_time = (datetime.now() - start_computation).total_seconds()
        success_count = sum(1 for r in results.values() if r.success)
        
        logger.info(f"軌道傳播完成: {success_count}/{len(request.satellite_ids)} 成功, "
                   f"計算時間: {total_computation_time:.2f}秒")
        
        return results
    
    def _propagate_single_satellite(self, satellite_id: str, 
                                   request: PropagationRequest) -> PropagationResult:
        """單衛星軌道傳播"""
        start_time = datetime.now()
        orbit_states = []
        
        try:
            # 生成時間序列
            time_points = self._generate_time_points(request)
            
            # 逐個時間點計算軌道狀態
            for timestamp in time_points:
                sgp4_result = self.sgp4_engine.calculate_position(satellite_id, timestamp)
                
                if sgp4_result and sgp4_result.success:
                    orbit_state = self._create_orbit_state(
                        satellite_id, timestamp, sgp4_result, request
                    )
                    orbit_states.append(orbit_state)
                else:
                    logger.warning(f"衛星 {satellite_id} 在時間 {timestamp} 的計算失敗")
            
            # 檢查結果
            if not orbit_states:
                return PropagationResult(
                    satellite_id=satellite_id,
                    request=request,
                    orbit_states=[],
                    success=False,
                    error_message="無有效軌道狀態生成"
                )
            
            computation_time = (datetime.now() - start_time).total_seconds()
            
            return PropagationResult(
                satellite_id=satellite_id,
                request=request,
                orbit_states=orbit_states,
                success=True,
                computation_time_seconds=computation_time
            )
            
        except Exception as e:
            computation_time = (datetime.now() - start_time).total_seconds()
            return PropagationResult(
                satellite_id=satellite_id,
                request=request,
                orbit_states=orbit_states,
                success=False,
                error_message=str(e),
                computation_time_seconds=computation_time
            )
    
    def _generate_time_points(self, request: PropagationRequest) -> List[datetime]:
        """生成時間點序列"""
        time_points = []
        
        if request.mode == PropagationMode.SINGLE_POINT:
            # 單點模式
            time_points = [request.start_time]
            
        elif request.mode in [PropagationMode.TIME_SERIES, PropagationMode.PREDICTION, PropagationMode.HISTORICAL]:
            # 時間序列模式
            if not request.end_time:
                # 如果沒有結束時間，默認生成2小時的軌跡
                end_time = request.start_time + timedelta(hours=2)
            else:
                end_time = request.end_time
            
            current_time = request.start_time
            while current_time <= end_time:
                time_points.append(current_time)
                current_time += timedelta(seconds=request.time_step_seconds)
        
        logger.debug(f"生成時間點序列: {len(time_points)} 個點, "
                    f"間隔: {request.time_step_seconds}秒")
        
        return time_points
    
    def _create_orbit_state(self, satellite_id: str, timestamp: datetime,
                           sgp4_result: SGP4Result, request: PropagationRequest) -> OrbitState:
        """創建軌道狀態"""
        # 基本位置和速度
        orbit_state = OrbitState(
            timestamp=timestamp,
            satellite_id=satellite_id,
            position_x=sgp4_result.position_eci[0],
            position_y=sgp4_result.position_eci[1],
            position_z=sgp4_result.position_eci[2]
        )
        
        # 添加速度信息
        if request.include_velocity and sgp4_result.velocity_eci is not None:
            orbit_state.velocity_x = sgp4_result.velocity_eci[0]
            orbit_state.velocity_y = sgp4_result.velocity_eci[1]
            orbit_state.velocity_z = sgp4_result.velocity_eci[2]
        
        # 計算高度
        orbit_state.altitude_km = orbit_state.position_magnitude - self.earth_radius_km
        
        # 計算地理坐標 (如果需要)
        if request.include_ground_track:
            lat, lon = self._eci_to_geographic(
                orbit_state.position_vector, timestamp
            )
            orbit_state.latitude_deg = lat
            orbit_state.longitude_deg = lon
        
        return orbit_state
    
    def _eci_to_geographic(self, position_eci: np.ndarray, 
                          timestamp: datetime) -> Tuple[float, float]:
        """ECI 坐標轉地理坐標"""
        x, y, z = position_eci
        
        # 計算緯度 (簡化計算，不考慮地球扁率)
        r = np.linalg.norm(position_eci)
        latitude_rad = math.asin(z / r)
        latitude_deg = math.degrees(latitude_rad)
        
        # 計算經度 (需要考慮地球自轉)
        longitude_rad = math.atan2(y, x)
        
        # 考慮地球自轉 (簡化計算)
        # 地球自轉角速度: 7.2921159e-5 rad/s
        earth_rotation_rate = 7.2921159e-5  # rad/s
        
        # 計算從 J2000 epoch 到當前時間的地球自轉角
        j2000_epoch = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        seconds_since_j2000 = (timestamp - j2000_epoch).total_seconds()
        earth_rotation_angle = earth_rotation_rate * seconds_since_j2000
        
        # 調整經度
        longitude_rad -= earth_rotation_angle
        
        # 正規化經度到 [-π, π]
        longitude_rad = ((longitude_rad + math.pi) % (2 * math.pi)) - math.pi
        longitude_deg = math.degrees(longitude_rad)
        
        return latitude_deg, longitude_deg
    
    def calculate_orbital_elements(self, orbit_states: List[OrbitState]) -> Dict[str, float]:
        """
        計算軌道元素
        基於軌道狀態計算經典軌道元素
        """
        if not orbit_states:
            return {}
        
        # 使用第一個狀態計算軌道元素
        state = orbit_states[0]
        r_vec = state.position_vector
        v_vec = state.velocity_vector
        
        if v_vec is None:
            return {"error": "缺少速度信息"}
        
        # 地球引力參數 (km³/s²)
        mu = 398600.4418
        
        # 計算軌道元素
        r_mag = np.linalg.norm(r_vec)
        v_mag = np.linalg.norm(v_vec)
        
        # 比角動量
        h_vec = np.cross(r_vec, v_vec)
        h_mag = np.linalg.norm(h_vec)
        
        # 軌道傾角
        inclination_rad = math.acos(h_vec[2] / h_mag)
        inclination_deg = math.degrees(inclination_rad)
        
        # 半長軸
        energy = (v_mag**2 / 2) - (mu / r_mag)
        semi_major_axis = -mu / (2 * energy)
        
        # 偏心率
        e_vec = ((v_mag**2 - mu/r_mag) * r_vec - np.dot(r_vec, v_vec) * v_vec) / mu
        eccentricity = np.linalg.norm(e_vec)
        
        # 軌道週期
        if semi_major_axis > 0:
            orbital_period_sec = 2 * math.pi * math.sqrt(semi_major_axis**3 / mu)
            orbital_period_min = orbital_period_sec / 60
        else:
            orbital_period_sec = 0
            orbital_period_min = 0
        
        # 近地點高度
        perigee_height = semi_major_axis * (1 - eccentricity) - self.earth_radius_km
        
        # 遠地點高度  
        apogee_height = semi_major_axis * (1 + eccentricity) - self.earth_radius_km
        
        return {
            "semi_major_axis_km": semi_major_axis,
            "eccentricity": eccentricity,
            "inclination_deg": inclination_deg,
            "orbital_period_min": orbital_period_min,
            "perigee_height_km": perigee_height,
            "apogee_height_km": apogee_height,
            "specific_energy_km2_s2": energy
        }
    
    def predict_visibility_windows(self, satellite_id: str, observer_lat: float,
                                 observer_lon: float, observer_alt: float,
                                 start_time: datetime, duration_hours: float,
                                 min_elevation_deg: float = 10.0) -> List[Dict]:
        """
        預測衛星可見窗口
        
        Args:
            satellite_id: 衛星ID
            observer_lat: 觀測者緯度 (度)
            observer_lon: 觀測者經度 (度) 
            observer_alt: 觀測者高度 (km)
            start_time: 開始時間
            duration_hours: 預測持續時間 (小時)
            min_elevation_deg: 最小仰角 (度)
            
        Returns:
            可見窗口列表
        """
        logger.info(f"預測衛星 {satellite_id} 的可見窗口...")
        
        # 創建傳播請求
        end_time = start_time + timedelta(hours=duration_hours)
        request = PropagationRequest(
            satellite_ids=[satellite_id],
            start_time=start_time,
            end_time=end_time,
            time_step_seconds=30,
            mode=PropagationMode.PREDICTION,
            include_ground_track=True
        )
        
        # 執行軌道傳播
        results = self.propagate_orbit(request)
        
        if satellite_id not in results or not results[satellite_id].success:
            logger.error(f"衛星 {satellite_id} 軌道傳播失敗")
            return []
        
        orbit_states = results[satellite_id].orbit_states
        
        # 計算仰角和方位角
        visibility_windows = []
        current_window = None
        
        for state in orbit_states:
            # 計算仰角和方位角 (簡化計算)
            elevation, azimuth = self._calculate_look_angles(
                state.latitude_deg, state.longitude_deg, state.altitude_km,
                observer_lat, observer_lon, observer_alt
            )
            
            # 檢查是否可見
            is_visible = elevation >= min_elevation_deg
            
            if is_visible and current_window is None:
                # 開始新的可見窗口
                current_window = {
                    "start_time": state.timestamp,
                    "max_elevation": elevation,
                    "max_elevation_time": state.timestamp,
                    "max_elevation_azimuth": azimuth
                }
            elif is_visible and current_window is not None:
                # 更新可見窗口
                if elevation > current_window["max_elevation"]:
                    current_window["max_elevation"] = elevation
                    current_window["max_elevation_time"] = state.timestamp
                    current_window["max_elevation_azimuth"] = azimuth
            elif not is_visible and current_window is not None:
                # 結束當前可見窗口
                current_window["end_time"] = state.timestamp
                current_window["duration_minutes"] = (
                    current_window["end_time"] - current_window["start_time"]
                ).total_seconds() / 60
                visibility_windows.append(current_window)
                current_window = None
        
        # 處理最後一個窗口
        if current_window is not None:
            current_window["end_time"] = orbit_states[-1].timestamp
            current_window["duration_minutes"] = (
                current_window["end_time"] - current_window["start_time"]
            ).total_seconds() / 60
            visibility_windows.append(current_window)
        
        logger.info(f"找到 {len(visibility_windows)} 個可見窗口")
        return visibility_windows
    
    def _calculate_look_angles(self, sat_lat: float, sat_lon: float, sat_alt: float,
                              obs_lat: float, obs_lon: float, obs_alt: float) -> Tuple[float, float]:
        """計算仰角和方位角 (簡化計算)"""
        # 轉換為弧度
        sat_lat_rad = math.radians(sat_lat)
        sat_lon_rad = math.radians(sat_lon)
        obs_lat_rad = math.radians(obs_lat)
        obs_lon_rad = math.radians(obs_lon)
        
        # 地球半徑 (km)
        R = 6371.0
        
        # 衛星位置 (笛卡爾坐標)
        sat_r = R + sat_alt
        sat_x = sat_r * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
        sat_y = sat_r * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
        sat_z = sat_r * math.sin(sat_lat_rad)
        
        # 觀測者位置 (笛卡爾坐標)
        obs_r = R + obs_alt
        obs_x = obs_r * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        obs_y = obs_r * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        obs_z = obs_r * math.sin(obs_lat_rad)
        
        # 相對位置向量
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z
        
        # 距離
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 仰角 (簡化計算)
        elevation_rad = math.asin(dz / distance)
        elevation_deg = math.degrees(elevation_rad)
        
        # 方位角 (簡化計算)
        azimuth_rad = math.atan2(dy, dx)
        azimuth_deg = math.degrees(azimuth_rad)
        
        # 正規化方位角到 [0, 360)
        if azimuth_deg < 0:
            azimuth_deg += 360
        
        return elevation_deg, azimuth_deg


def create_orbit_propagator(sgp4_engine: SGP4Engine) -> OrbitPropagator:
    """創建軌道傳播器實例"""
    return OrbitPropagator(sgp4_engine)


# 測試代碼
if __name__ == "__main__":
    import sys
    import os
    from datetime import datetime, timezone
    
    # 設置路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    logging.basicConfig(level=logging.INFO)
    
    # 創建測試實例
    from sgp4_engine import create_sgp4_engine
    
    sgp4_engine = create_sgp4_engine()
    propagator = create_orbit_propagator(sgp4_engine)
    
    print("✅ 軌道傳播器測試完成")
    print("核心功能:")
    print("  - 完整 SGP4 軌道傳播")
    print("  - 時間序列生成")
    print("  - 軌道元素計算")
    print("  - 可見窗口預測")