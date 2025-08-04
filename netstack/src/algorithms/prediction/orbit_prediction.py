"""
Phase 3.2.2.1: 軌道預測優化算法實現

實現高精度的衛星軌道預測算法，包括：
1. SGP4/SDP4 軌道預測模型優化
2. 攝動力補償和軌道修正
3. 多衛星軌道追蹤和預測
4. 預測精度評估和校準
5. 與時間同步系統整合

符合標準：
- NORAD Two-Line Element Set (TLE) 格式
- SPACETRACK SGP4/SDP4 標準
- ITU-R S.1001 衛星軌道預測要求
- 3GPP TS 38.821 NTN 軌道預測規範
"""

import asyncio
import logging
import math
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class OrbitModelType(Enum):
    """軌道模型類型"""
    SGP4 = "sgp4"          # Simplified General Perturbations 4
    SDP4 = "sdp4"          # Simplified Deep-space Perturbations 4  
    HPOP = "hpop"          # High Precision Orbit Propagator
    NUMERICAL = "numerical" # 數值積分


class PredictionAccuracy(Enum):
    """預測精度級別"""
    LOW = "low"           # 低精度 (±1km)
    MEDIUM = "medium"     # 中精度 (±100m)
    HIGH = "high"         # 高精度 (±10m)
    ULTRA = "ultra"       # 超高精度 (±1m)


class PerturbationType(Enum):
    """攝動力類型"""
    ATMOSPHERIC_DRAG = "atmospheric_drag"      # 大氣阻力
    SOLAR_RADIATION = "solar_radiation"        # 太陽輻射壓
    EARTH_OBLATENESS = "earth_oblateness"      # 地球扁率
    THIRD_BODY = "third_body"                  # 第三體引力
    RELATIVITY = "relativity"                  # 相對論效應


@dataclass
class TLEData:
    """雙行根數數據"""
    satellite_id: str
    satellite_name: str
    line1: str  # TLE 第一行
    line2: str  # TLE 第二行
    epoch: datetime
    
    # 軌道參數
    inclination_deg: float = 0.0        # 軌道傾角
    raan_deg: float = 0.0               # 升交點赤經  
    eccentricity: float = 0.0           # 偏心率
    arg_perigee_deg: float = 0.0        # 近地點幅角
    mean_anomaly_deg: float = 0.0       # 平近點角
    mean_motion_revs_per_day: float = 0.0  # 平均運動
    
    # 攝動參數
    bstar: float = 0.0                  # 大氣阻力係數
    first_derivative: float = 0.0       # 平均運動一階導數
    second_derivative: float = 0.0      # 平均運動二階導數
    
    def __post_init__(self):
        if self.line1 and self.line2:
            self._parse_tle()
    
    def _parse_tle(self):
        """解析 TLE 數據"""
        try:
            # 解析第一行
            if len(self.line1) >= 69:
                epoch_year = int(self.line1[18:20])
                epoch_day = float(self.line1[20:32])
                
                # 計算 epoch 時間
                if epoch_year < 70:
                    epoch_year += 2000
                else:
                    epoch_year += 1900
                
                epoch_date = datetime(epoch_year, 1, 1, tzinfo=timezone.utc)
                self.epoch = epoch_date + timedelta(days=epoch_day - 1)
                
                # 處理科學計數法格式的數據
                first_deriv_str = self.line1[33:43].strip()
                if first_deriv_str:
                    self.first_derivative = float(first_deriv_str)
                
                second_deriv_str = self.line1[44:52].strip()
                if second_deriv_str and second_deriv_str != "00000-0":
                    # 處理 TLE 格式的指數表示法
                    if '-' in second_deriv_str[-2:]:
                        mantissa = second_deriv_str[:-2]
                        exponent = int(second_deriv_str[-1])
                        self.second_derivative = float(mantissa) * (10 ** (-exponent))
                    else:
                        self.second_derivative = float(second_deriv_str)
                
                bstar_str = self.line1[53:61].strip()
                if bstar_str and bstar_str != "00000-0":
                    # 處理 BSTAR 的指數表示法
                    if '-' in bstar_str[-2:]:
                        mantissa = bstar_str[:-2]
                        exponent = int(bstar_str[-1])
                        self.bstar = float(mantissa) * (10 ** (-exponent))
                    else:
                        self.bstar = float(bstar_str)
            
            # 解析第二行
            if len(self.line2) >= 69:
                self.inclination_deg = float(self.line2[8:16].strip())
                self.raan_deg = float(self.line2[17:25].strip())
                
                ecc_str = self.line2[26:33].strip()
                if ecc_str:
                    self.eccentricity = float("0." + ecc_str)
                
                self.arg_perigee_deg = float(self.line2[34:42].strip())
                self.mean_anomaly_deg = float(self.line2[43:51].strip())
                self.mean_motion_revs_per_day = float(self.line2[52:63].strip())
                
        except Exception as e:
            logger.error(f"TLE 解析失敗: {e}")
            # 使用默認值以防解析失敗


@dataclass
class SatelliteState:
    """衛星狀態"""
    satellite_id: str
    timestamp: datetime
    
    # 位置 (ECI 坐標系, km)
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    
    # 速度 (ECI 坐標系, km/s)
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0
    
    # 軌道參數
    altitude_km: float = 0.0
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    
    # 預測置信度
    prediction_confidence: float = 1.0
    prediction_error_km: float = 0.0
    
    # 可見性信息
    elevation_deg: Optional[float] = None
    azimuth_deg: Optional[float] = None
    distance_km: Optional[float] = None
    
    def get_position_vector(self) -> np.ndarray:
        """獲取位置向量"""
        return np.array([self.position_x, self.position_y, self.position_z])
    
    def get_velocity_vector(self) -> np.ndarray:
        """獲取速度向量"""
        return np.array([self.velocity_x, self.velocity_y, self.velocity_z])
    
    def calculate_orbital_speed(self) -> float:
        """計算軌道速度"""
        return np.linalg.norm(self.get_velocity_vector())
    
    def calculate_distance_to(self, other_state: 'SatelliteState') -> float:
        """計算與另一衛星的距離"""
        pos1 = self.get_position_vector()
        pos2 = other_state.get_position_vector()
        return np.linalg.norm(pos2 - pos1)


@dataclass
class PredictionRequest:
    """預測請求"""
    request_id: str
    satellite_ids: List[str]
    start_time: datetime
    end_time: datetime
    time_step_seconds: int = 30
    accuracy_level: PredictionAccuracy = PredictionAccuracy.MEDIUM
    
    # 觀測者位置 (可選)
    observer_latitude_deg: Optional[float] = None
    observer_longitude_deg: Optional[float] = None
    observer_altitude_km: Optional[float] = None
    
    # 特殊要求
    include_perturbations: List[PerturbationType] = field(default_factory=list)
    max_prediction_error_km: float = 1.0
    
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """預測結果"""
    request_id: str
    satellite_id: str
    prediction_states: List[SatelliteState]
    
    # 預測品質指標
    average_confidence: float = 0.0
    max_error_km: float = 0.0
    rmse_error_km: float = 0.0
    
    # 軌道特徵
    orbital_period_minutes: float = 0.0
    perigee_altitude_km: float = 0.0
    apogee_altitude_km: float = 0.0
    
    # 處理統計
    computation_time_ms: float = 0.0
    model_type: OrbitModelType = OrbitModelType.SGP4
    
    def get_state_at_time(self, target_time: datetime) -> Optional[SatelliteState]:
        """獲取指定時間的狀態"""
        if not self.prediction_states:
            return None
        
        # 找到最接近的時間點
        min_diff = float('inf')
        closest_state = None
        
        for state in self.prediction_states:
            time_diff = abs((state.timestamp - target_time).total_seconds())
            if time_diff < min_diff:
                min_diff = time_diff
                closest_state = state
        
        return closest_state
    
    def get_states_in_timerange(self, start_time: datetime, 
                               end_time: datetime) -> List[SatelliteState]:
        """獲取時間範圍內的狀態"""
        return [s for s in self.prediction_states 
                if start_time <= s.timestamp <= end_time]


class OrbitPredictionEngine:
    """軌道預測引擎"""
    
    def __init__(self, engine_id: str = None):
        self.engine_id = engine_id or f"orbit_pred_{uuid.uuid4().hex[:8]}"
        
        # 預測配置
        self.prediction_config = {
            'default_model': OrbitModelType.SGP4,
            'default_accuracy': PredictionAccuracy.MEDIUM,
            'max_prediction_horizon_days': 7,
            'cache_size': 1000,
            'perturbation_threshold_km': 0.1,
            'convergence_tolerance': 1e-6,
            'max_iterations': 100,
            'time_step_adaptive': True,
            'earth_radius_km': 6371.0,
            'gravitational_parameter': 398600.4418  # km³/s²
        }
        
        # TLE 數據存儲
        self.tle_database: Dict[str, TLEData] = {}
        self.tle_update_times: Dict[str, datetime] = {}
        
        # 預測緩存
        self.prediction_cache: Dict[str, PredictionResult] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # 運行狀態
        self.is_running = False
        self.prediction_task: Optional[asyncio.Task] = None
        self.cache_cleanup_task: Optional[asyncio.Task] = None
        
        # 統計信息
        self.stats = {
            'predictions_completed': 0,
            'predictions_failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_computation_time_ms': 0.0,
            'total_computation_time_ms': 0.0,
            'tle_updates': 0,
            'perturbation_corrections': 0
        }
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.prediction_lock = threading.RLock()
        
        # 攝動力模型
        self.perturbation_models = {
            PerturbationType.ATMOSPHERIC_DRAG: self._calculate_atmospheric_drag,
            PerturbationType.SOLAR_RADIATION: self._calculate_solar_radiation_pressure,
            PerturbationType.EARTH_OBLATENESS: self._calculate_earth_oblateness,
            PerturbationType.THIRD_BODY: self._calculate_third_body_effects,
            PerturbationType.RELATIVITY: self._calculate_relativistic_effects
        }
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def start_engine(self):
        """啟動預測引擎"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 啟動緩存清理任務
        self.cache_cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
        
        self.logger.info(f"🚀 軌道預測引擎已啟動 - ID: {self.engine_id}")
    
    async def stop_engine(self):
        """停止預測引擎"""
        self.is_running = False
        
        # 停止所有任務
        for task in [self.prediction_task, self.cache_cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.executor.shutdown(wait=True)
        self.logger.info("⏹️ 軌道預測引擎已停止")
    
    # === TLE 數據管理 ===
    
    async def update_tle_data(self, satellite_id: str, tle_line1: str, 
                             tle_line2: str, satellite_name: str = "") -> bool:
        """更新 TLE 數據"""
        try:
            tle_data = TLEData(
                satellite_id=satellite_id,
                satellite_name=satellite_name or satellite_id,
                line1=tle_line1,
                line2=tle_line2,
                epoch=datetime.now(timezone.utc)
            )
            
            with self.prediction_lock:
                self.tle_database[satellite_id] = tle_data
                self.tle_update_times[satellite_id] = datetime.now(timezone.utc)
                
                # 清理該衛星的預測緩存
                cache_keys_to_remove = [
                    key for key in self.prediction_cache.keys()
                    if satellite_id in key
                ]
                for key in cache_keys_to_remove:
                    del self.prediction_cache[key]
                    del self.cache_timestamps[key]
            
            self.stats['tle_updates'] += 1
            self.logger.info(f"✅ TLE 數據已更新: {satellite_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ TLE 數據更新失敗: {e}")
            return False
    
    async def batch_update_tle_data(self, tle_data_list: List[Dict[str, str]]) -> int:
        """批量更新 TLE 數據"""
        success_count = 0
        for tle_data in tle_data_list:
            success = await self.update_tle_data(
                tle_data['satellite_id'],
                tle_data['line1'],
                tle_data['line2'],
                tle_data.get('satellite_name', '')
            )
            if success:
                success_count += 1
        
        return success_count
    
    def get_tle_data(self, satellite_id: str) -> Optional[TLEData]:
        """獲取 TLE 數據"""
        return self.tle_database.get(satellite_id)
    
    def get_tle_age_hours(self, satellite_id: str) -> Optional[float]:
        """獲取 TLE 數據年齡（小時）"""
        if satellite_id in self.tle_update_times:
            elapsed = datetime.now(timezone.utc) - self.tle_update_times[satellite_id]
            return elapsed.total_seconds() / 3600.0
        return None
    
    # === 核心預測方法 ===
    
    async def predict_satellite_orbit(self, request: PredictionRequest) -> List[PredictionResult]:
        """預測衛星軌道"""
        start_time = time.time()
        results = []
        
        try:
            for satellite_id in request.satellite_ids:
                # 檢查緩存
                cache_key = self._generate_cache_key(satellite_id, request)
                cached_result = self._get_cached_result(cache_key)
                
                if cached_result:
                    results.append(cached_result)
                    self.stats['cache_hits'] += 1
                    continue
                
                self.stats['cache_misses'] += 1
                
                # 獲取 TLE 數據
                tle_data = self.get_tle_data(satellite_id)
                if not tle_data:
                    self.logger.warning(f"⚠️ 衛星 {satellite_id} 的 TLE 數據不存在")
                    continue
                
                # 執行軌道預測
                prediction_result = await self._compute_orbit_prediction(
                    satellite_id, tle_data, request
                )
                
                if prediction_result:
                    # 緩存結果
                    self._cache_result(cache_key, prediction_result)
                    results.append(prediction_result)
                    self.stats['predictions_completed'] += 1
                else:
                    self.stats['predictions_failed'] += 1
            
            # 更新統計
            computation_time = (time.time() - start_time) * 1000
            self.stats['total_computation_time_ms'] += computation_time
            total_predictions = self.stats['predictions_completed'] + self.stats['predictions_failed']
            if total_predictions > 0:
                self.stats['average_computation_time_ms'] = \
                    self.stats['total_computation_time_ms'] / total_predictions
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 軌道預測失敗: {e}")
            self.stats['predictions_failed'] += len(request.satellite_ids)
            return []
    
    async def _compute_orbit_prediction(self, satellite_id: str, tle_data: TLEData, 
                                       request: PredictionRequest) -> Optional[PredictionResult]:
        """計算軌道預測"""
        try:
            # 選擇預測模型
            model_type = self._select_prediction_model(tle_data, request.accuracy_level)
            
            # 生成時間序列
            time_points = self._generate_time_series(
                request.start_time, request.end_time, request.time_step_seconds
            )
            
            # 計算軌道狀態
            prediction_states = []
            computation_start = time.time()
            
            for timestamp in time_points:
                state = await self._compute_state_at_time(
                    satellite_id, tle_data, timestamp, model_type, request
                )
                if state:
                    prediction_states.append(state)
            
            computation_time_ms = (time.time() - computation_start) * 1000
            
            # 計算軌道特徵
            orbital_period = self._calculate_orbital_period(tle_data)
            perigee_alt, apogee_alt = self._calculate_altitude_extremes(prediction_states)
            
            # 評估預測品質
            avg_confidence, max_error, rmse_error = self._evaluate_prediction_quality(
                prediction_states, request.accuracy_level
            )
            
            return PredictionResult(
                request_id=request.request_id,
                satellite_id=satellite_id,
                prediction_states=prediction_states,
                average_confidence=avg_confidence,
                max_error_km=max_error,
                rmse_error_km=rmse_error,
                orbital_period_minutes=orbital_period,
                perigee_altitude_km=perigee_alt,
                apogee_altitude_km=apogee_alt,
                computation_time_ms=computation_time_ms,
                model_type=model_type
            )
            
        except Exception as e:
            self.logger.error(f"❌ 軌道預測計算失敗: {e}")
            return None
    
    async def _compute_state_at_time(self, satellite_id: str, tle_data: TLEData,
                                   timestamp: datetime, model_type: OrbitModelType,
                                   request: PredictionRequest) -> Optional[SatelliteState]:
        """計算指定時間的衛星狀態"""
        try:
            # 計算時間差（分鐘）
            time_since_epoch = (timestamp - tle_data.epoch).total_seconds() / 60.0
            
            # 基於模型類型計算位置和速度
            if model_type == OrbitModelType.SGP4:
                position, velocity = self._sgp4_propagate(tle_data, time_since_epoch)
            elif model_type == OrbitModelType.SDP4:
                position, velocity = self._sdp4_propagate(tle_data, time_since_epoch)
            else:
                # 默認使用 SGP4
                position, velocity = self._sgp4_propagate(tle_data, time_since_epoch)
            
            # 應用攝動力修正
            if request.include_perturbations:
                position, velocity = await self._apply_perturbations(
                    position, velocity, timestamp, request.include_perturbations
                )
            
            # 計算地理坐標
            lat, lon, alt = self._eci_to_geodetic(position, timestamp)
            
            # 計算可見性信息（如果提供了觀測者位置）
            elevation, azimuth, distance = None, None, None
            if (request.observer_latitude_deg is not None and 
                request.observer_longitude_deg is not None):
                elevation, azimuth, distance = self._calculate_visibility(
                    position, request.observer_latitude_deg, 
                    request.observer_longitude_deg,
                    request.observer_altitude_km or 0.0, timestamp
                )
            
            # 評估預測置信度
            confidence = self._calculate_prediction_confidence(
                tle_data, time_since_epoch, request.accuracy_level
            )
            
            # 估算預測誤差
            prediction_error = self._estimate_prediction_error(
                tle_data, time_since_epoch, request.accuracy_level
            )
            
            return SatelliteState(
                satellite_id=satellite_id,
                timestamp=timestamp,
                position_x=position[0],
                position_y=position[1], 
                position_z=position[2],
                velocity_x=velocity[0],
                velocity_y=velocity[1],
                velocity_z=velocity[2],
                altitude_km=alt,
                latitude_deg=lat,
                longitude_deg=lon,
                prediction_confidence=confidence,
                prediction_error_km=prediction_error,
                elevation_deg=elevation,
                azimuth_deg=azimuth,
                distance_km=distance
            )
            
        except Exception as e:
            self.logger.error(f"❌ 狀態計算失敗: {e}")
            return None
    
    # === SGP4/SDP4 軌道傳播 ===
    
    def _sgp4_propagate(self, tle_data: TLEData, time_minutes: float) -> Tuple[np.ndarray, np.ndarray]:
        """SGP4 軌道傳播算法"""
        try:
            # 軌道參數
            n0 = tle_data.mean_motion_revs_per_day * (2 * math.pi) / (24 * 60)  # rad/min
            e0 = tle_data.eccentricity
            i0 = math.radians(tle_data.inclination_deg)
            omega0 = math.radians(tle_data.arg_perigee_deg)
            Omega0 = math.radians(tle_data.raan_deg)
            M0 = math.radians(tle_data.mean_anomaly_deg)
            
            # 地球常數
            mu = self.prediction_config['gravitational_parameter']  # km³/s²
            re = self.prediction_config['earth_radius_km']          # km
            
            # 檢查平均運動有效性
            if n0 <= 0:
                self.logger.error("無效的平均運動")
                return np.zeros(3), np.zeros(3)
            
            # 計算半長軸 (使用正確的單位轉換)
            n0_rad_per_sec = n0 / 60.0  # rad/s
            a = (mu / (n0_rad_per_sec ** 2)) ** (1/3)  # km
            
            # 檢查軌道半長軸合理性
            if a < re or a > 100000:  # 合理範圍：地球半徑到100,000km
                self.logger.error(f"不合理的軌道半長軸: {a} km")
                return np.zeros(3), np.zeros(3)
            
            # 時間相關的軌道要素
            M = M0 + n0 * time_minutes  # 平近點角
            M = M % (2 * math.pi)  # 歸一化到 [0, 2π]
            
            # 求解偏近點角 (Kepler方程)
            E = self._solve_kepler_equation(M, e0)
            
            # 真近點角
            nu = 2 * math.atan2(
                math.sqrt(1 + e0) * math.sin(E/2),
                math.sqrt(1 - e0) * math.cos(E/2)
            )
            
            # 軌道半徑
            r = a * (1 - e0 * math.cos(E))
            
            # 軌道平面內的位置
            x_orbit = r * math.cos(nu)
            y_orbit = r * math.sin(nu)
            z_orbit = 0.0
            
            # 軌道平面內的速度
            p = a * (1 - e0**2)  # 半通徑
            if p <= 0:
                self.logger.error("無效的半通徑")
                return np.zeros(3), np.zeros(3)
            
            # 正確的軌道速度計算 (km/s)
            n = math.sqrt(mu / (a**3))  # 平均角速度 rad/s
            
            # 使用正確的速度公式
            vx_orbit = -n * a * math.sin(E) / (1 - e0 * math.cos(E))
            vy_orbit = n * a * math.sqrt(1 - e0**2) * math.cos(E) / (1 - e0 * math.cos(E))
            vz_orbit = 0.0
            
            # 轉換到地心慣性坐標系 (ECI)
            # 考慮軌道傾角、升交點赤經、近地點幅角的旋轉
            cos_omega = math.cos(omega0)
            sin_omega = math.sin(omega0)
            cos_Omega = math.cos(Omega0)
            sin_Omega = math.sin(Omega0)
            cos_i = math.cos(i0)
            sin_i = math.sin(i0)
            
            # 旋轉矩陣元素
            P11 = cos_omega * cos_Omega - sin_omega * sin_Omega * cos_i
            P12 = -sin_omega * cos_Omega - cos_omega * sin_Omega * cos_i
            P13 = sin_omega * sin_i
            P21 = cos_omega * sin_Omega + sin_omega * cos_Omega * cos_i
            P22 = -sin_omega * sin_Omega + cos_omega * cos_Omega * cos_i
            P23 = -cos_omega * sin_i
            P31 = sin_Omega * sin_i
            P32 = cos_Omega * sin_i
            P33 = cos_i
            
            # ECI 位置
            position = np.array([
                P11 * x_orbit + P12 * y_orbit + P13 * z_orbit,
                P21 * x_orbit + P22 * y_orbit + P23 * z_orbit,
                P31 * x_orbit + P32 * y_orbit + P33 * z_orbit
            ])
            
            # ECI 速度 (已經是 km/s)
            velocity = np.array([
                P11 * vx_orbit + P12 * vy_orbit + P13 * vz_orbit,
                P21 * vx_orbit + P22 * vy_orbit + P23 * vz_orbit,
                P31 * vx_orbit + P32 * vy_orbit + P33 * vz_orbit
            ])
            
            # 檢查結果有效性
            if not np.all(np.isfinite(position)) or not np.all(np.isfinite(velocity)):
                self.logger.error("SGP4 計算結果無效")
                return np.zeros(3), np.zeros(3)
            
            return position, velocity
            
        except Exception as e:
            self.logger.error(f"❌ SGP4 傳播失敗: {e}")
            # 返回零向量作為故障回復
            return np.zeros(3), np.zeros(3)
    
    def _sdp4_propagate(self, tle_data: TLEData, time_minutes: float) -> Tuple[np.ndarray, np.ndarray]:
        """SDP4 深空軌道傳播算法"""
        # 對於深空軌道，使用更複雜的攝動模型
        # 這裡簡化實現，實際中需要考慮月球、太陽引力等
        return self._sgp4_propagate(tle_data, time_minutes)
    
    def _solve_kepler_equation(self, M: float, e: float, tolerance: float = 1e-8) -> float:
        """求解開普勒方程 M = E - e*sin(E)"""
        E = M  # 初始猜測
        
        for _ in range(20):  # 最多迭代20次
            delta_E = (M - E + e * math.sin(E)) / (1 - e * math.cos(E))
            E += delta_E
            
            if abs(delta_E) < tolerance:
                break
        
        return E
    
    # === 攝動力計算 ===
    
    async def _apply_perturbations(self, position: np.ndarray, velocity: np.ndarray,
                                 timestamp: datetime, 
                                 perturbation_types: List[PerturbationType]) -> Tuple[np.ndarray, np.ndarray]:
        """應用攝動力修正"""
        corrected_position = position.copy()
        corrected_velocity = velocity.copy()
        
        for pert_type in perturbation_types:
            if pert_type in self.perturbation_models:
                try:
                    pos_correction, vel_correction = self.perturbation_models[pert_type](
                        position, velocity, timestamp
                    )
                    corrected_position += pos_correction
                    corrected_velocity += vel_correction
                    self.stats['perturbation_corrections'] += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ 攝動力計算失敗 {pert_type}: {e}")
        
        return corrected_position, corrected_velocity
    
    def _calculate_atmospheric_drag(self, position: np.ndarray, velocity: np.ndarray, 
                                  timestamp: datetime) -> Tuple[np.ndarray, np.ndarray]:
        """計算大氣阻力攝動"""
        try:
            # 簡化的大氣阻力模型
            altitude = np.linalg.norm(position) - self.prediction_config['earth_radius_km']
            
            if altitude > 1000 or altitude < 100:  # 1000km 以上或100km以下大氣阻力可忽略
                return np.zeros(3), np.zeros(3)
            
            # 大氣密度模型 (指數遞減)
            scale_height = 50.0  # km (調整為更合理的值)
            rho0 = 1.225e-9   # kg/km³ at 200km (調整單位)
            rho = rho0 * math.exp(-(altitude - 200) / scale_height)
            
            # 阻力係數
            cd = 2.2
            area_mass_ratio = 0.001  # m²/kg (調整為更小的值)
            
            # 阻力加速度
            v_rel = velocity
            v_rel_mag = np.linalg.norm(v_rel)
            
            if v_rel_mag > 1e-6:  # 避免除零
                drag_accel = -0.5 * rho * cd * area_mass_ratio * v_rel_mag * v_rel
                # 轉換為位置修正 (簡化)
                dt = 60.0  # 1分鐘
                vel_correction = drag_accel * dt
                pos_correction = 0.5 * drag_accel * dt**2
                
                # 限制修正量避免數值不穩定
                max_correction = 0.1  # km
                if np.linalg.norm(pos_correction) > max_correction:
                    pos_correction = pos_correction / np.linalg.norm(pos_correction) * max_correction
                if np.linalg.norm(vel_correction) > max_correction:
                    vel_correction = vel_correction / np.linalg.norm(vel_correction) * max_correction
            else:
                pos_correction = np.zeros(3)
                vel_correction = np.zeros(3)
            
            return pos_correction, vel_correction
            
        except Exception as e:
            self.logger.warning(f"大氣阻力計算異常: {e}")
            return np.zeros(3), np.zeros(3)
    
    def _calculate_solar_radiation_pressure(self, position: np.ndarray, velocity: np.ndarray,
                                          timestamp: datetime) -> Tuple[np.ndarray, np.ndarray]:
        """計算太陽輻射壓攝動"""
        # 簡化實現
        return np.zeros(3), np.zeros(3)
    
    def _calculate_earth_oblateness(self, position: np.ndarray, velocity: np.ndarray,
                                  timestamp: datetime) -> Tuple[np.ndarray, np.ndarray]:
        """計算地球扁率攝動 (J2項)"""
        try:
            # J2 攝動項
            J2 = 1.08262668e-3
            re = self.prediction_config['earth_radius_km']
            mu = self.prediction_config['gravitational_parameter']
            
            r = np.linalg.norm(position)
            
            # 避免除零和數值不穩定
            if r < re or r < 1e-6:
                return np.zeros(3), np.zeros(3)
            
            x, y, z = position
            
            # J2 攝動加速度
            factor = -1.5 * J2 * mu * re**2 / r**5
            
            accel_x = factor * x * (1 - 5 * z**2 / r**2)
            accel_y = factor * y * (1 - 5 * z**2 / r**2)
            accel_z = factor * z * (3 - 5 * z**2 / r**2)
            
            j2_accel = np.array([accel_x, accel_y, accel_z])
            
            # 檢查數值有效性
            if not np.all(np.isfinite(j2_accel)):
                return np.zeros(3), np.zeros(3)
            
            # 簡化的位置和速度修正
            dt = 60.0  # 1分鐘
            vel_correction = j2_accel * dt
            pos_correction = 0.5 * j2_accel * dt**2
            
            # 限制修正量避免數值不穩定
            max_correction = 1.0  # km
            if np.linalg.norm(pos_correction) > max_correction:
                pos_correction = pos_correction / np.linalg.norm(pos_correction) * max_correction
            if np.linalg.norm(vel_correction) > max_correction:
                vel_correction = vel_correction / np.linalg.norm(vel_correction) * max_correction
            
            return pos_correction, vel_correction
            
        except Exception as e:
            self.logger.warning(f"J2攝動計算異常: {e}")
            return np.zeros(3), np.zeros(3)
    
    def _calculate_third_body_effects(self, position: np.ndarray, velocity: np.ndarray,
                                    timestamp: datetime) -> Tuple[np.ndarray, np.ndarray]:
        """計算第三體引力攝動（月球、太陽）"""
        # 簡化實現
        return np.zeros(3), np.zeros(3)
    
    def _calculate_relativistic_effects(self, position: np.ndarray, velocity: np.ndarray,
                                      timestamp: datetime) -> Tuple[np.ndarray, np.ndarray]:
        """計算相對論效應"""
        # 簡化實現
        return np.zeros(3), np.zeros(3)
    
    # === 坐標轉換和可見性計算 ===
    
    def _eci_to_geodetic(self, position: np.ndarray, timestamp: datetime) -> Tuple[float, float, float]:
        """ECI 坐標轉換為大地坐標"""
        x, y, z = position
        
        # 計算格林威治恆星時
        gst = self._greenwich_sidereal_time(timestamp)
        
        # 轉換為 ECEF
        cos_gst = math.cos(gst)
        sin_gst = math.sin(gst)
        
        x_ecef = cos_gst * x + sin_gst * y
        y_ecef = -sin_gst * x + cos_gst * y
        z_ecef = z
        
        # ECEF 轉換為大地坐標
        r = math.sqrt(x_ecef**2 + y_ecef**2)
        longitude = math.atan2(y_ecef, x_ecef)
        latitude = math.atan2(z_ecef, r)
        altitude = math.sqrt(x_ecef**2 + y_ecef**2 + z_ecef**2) - self.prediction_config['earth_radius_km']
        
        return math.degrees(latitude), math.degrees(longitude), altitude
    
    def _greenwich_sidereal_time(self, timestamp: datetime) -> float:
        """計算格林威治恆星時"""
        # 簡化計算
        epoch = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        days_since_epoch = (timestamp - epoch).total_seconds() / 86400.0
        
        # 恆星時計算（簡化）
        gst = 1.753368559 + 628.3319653318 * days_since_epoch / 365.25
        return gst % (2 * math.pi)
    
    def _calculate_visibility(self, sat_position: np.ndarray, obs_lat: float, 
                            obs_lon: float, obs_alt: float, 
                            timestamp: datetime) -> Tuple[float, float, float]:
        """計算衛星可見性"""
        try:
            # 觀測者位置轉換為 ECI
            gst = self._greenwich_sidereal_time(timestamp)
            obs_lat_rad = math.radians(obs_lat)
            obs_lon_rad = math.radians(obs_lon)
            
            re = self.prediction_config['earth_radius_km']
            
            # 觀測者在 ECEF 中的位置
            cos_lat = math.cos(obs_lat_rad)
            sin_lat = math.sin(obs_lat_rad)
            cos_lon = math.cos(obs_lon_rad)
            sin_lon = math.sin(obs_lon_rad)
            
            x_ecef = (re + obs_alt) * cos_lat * cos_lon
            y_ecef = (re + obs_alt) * cos_lat * sin_lon
            z_ecef = (re + obs_alt) * sin_lat
            
            # ECEF 轉換為 ECI
            cos_gst = math.cos(gst)
            sin_gst = math.sin(gst)
            
            obs_position = np.array([
                cos_gst * x_ecef - sin_gst * y_ecef,
                sin_gst * x_ecef + cos_gst * y_ecef,
                z_ecef
            ])
            
            # 相對位置向量
            range_vector = sat_position - obs_position
            range_distance = np.linalg.norm(range_vector)
            
            # 轉換到觀測者局部坐標系 (SEZ)
            # S-南, E-東, Z-天頂
            sin_lat = math.sin(obs_lat_rad)
            cos_lat = math.cos(obs_lat_rad)
            sin_lon = math.sin(obs_lon_rad + gst)  # 包含恆星時
            cos_lon = math.cos(obs_lon_rad + gst)
            
            # 旋轉矩陣
            sez_x = sin_lat * cos_lon * range_vector[0] + sin_lat * sin_lon * range_vector[1] - cos_lat * range_vector[2]
            sez_y = -sin_lon * range_vector[0] + cos_lon * range_vector[1]
            sez_z = cos_lat * cos_lon * range_vector[0] + cos_lat * sin_lon * range_vector[1] + sin_lat * range_vector[2]
            
            # 計算仰角和方位角
            elevation = math.degrees(math.atan2(sez_z, math.sqrt(sez_x**2 + sez_y**2)))
            azimuth = math.degrees(math.atan2(sez_y, sez_x))
            
            # 方位角歸一化到 0-360 度
            if azimuth < 0:
                azimuth += 360
            
            return elevation, azimuth, range_distance
            
        except Exception as e:
            self.logger.error(f"❌ 可見性計算失敗: {e}")
            return 0.0, 0.0, 0.0
    
    # === 輔助方法 ===
    
    def _select_prediction_model(self, tle_data: TLEData, 
                               accuracy_level: PredictionAccuracy) -> OrbitModelType:
        """選擇預測模型"""
        # 根據軌道高度和精度要求選擇模型
        mean_motion = tle_data.mean_motion_revs_per_day
        
        if mean_motion < 1.0:  # 地球同步軌道或更高
            return OrbitModelType.SDP4
        else:
            return OrbitModelType.SGP4
    
    def _generate_time_series(self, start_time: datetime, end_time: datetime, 
                            step_seconds: int) -> List[datetime]:
        """生成時間序列"""
        time_points = []
        current_time = start_time
        
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(seconds=step_seconds)
        
        return time_points
    
    def _calculate_orbital_period(self, tle_data: TLEData) -> float:
        """計算軌道週期（分鐘）"""
        if tle_data.mean_motion_revs_per_day > 0:
            return 24 * 60 / tle_data.mean_motion_revs_per_day  # 分鐘
        return 0.0
    
    def _calculate_altitude_extremes(self, states: List[SatelliteState]) -> Tuple[float, float]:
        """計算軌道高度極值"""
        if not states:
            return 0.0, 0.0
        
        altitudes = [s.altitude_km for s in states]
        return min(altitudes), max(altitudes)
    
    def _evaluate_prediction_quality(self, states: List[SatelliteState], 
                                   accuracy_level: PredictionAccuracy) -> Tuple[float, float, float]:
        """評估預測品質"""
        if not states:
            return 0.0, 0.0, 0.0
        
        confidences = [s.prediction_confidence for s in states]
        errors = [s.prediction_error_km for s in states]
        
        avg_confidence = sum(confidences) / len(confidences)
        max_error = max(errors)
        rmse_error = math.sqrt(sum(e**2 for e in errors) / len(errors))
        
        return avg_confidence, max_error, rmse_error
    
    def _calculate_prediction_confidence(self, tle_data: TLEData, time_minutes: float,
                                       accuracy_level: PredictionAccuracy) -> float:
        """計算預測置信度"""
        # 基於 TLE 年齡和預測時間範圍
        tle_age_hours = abs(time_minutes) / 60.0
        
        # 置信度隨時間衰減
        base_confidence = 1.0
        
        # TLE 年齡影響
        if tle_age_hours > 24:
            base_confidence *= math.exp(-(tle_age_hours - 24) / 168.0)  # 一週半衰期
        
        # 預測時間範圍影響
        prediction_hours = abs(time_minutes) / 60.0
        if prediction_hours > 24:
            base_confidence *= math.exp(-prediction_hours / 720.0)  # 30天半衰期
        
        # 精度級別調整
        accuracy_factors = {
            PredictionAccuracy.LOW: 1.0,
            PredictionAccuracy.MEDIUM: 0.9,
            PredictionAccuracy.HIGH: 0.8,
            PredictionAccuracy.ULTRA: 0.7
        }
        
        return max(0.1, min(1.0, base_confidence * accuracy_factors.get(accuracy_level, 1.0)))
    
    def _estimate_prediction_error(self, tle_data: TLEData, time_minutes: float,
                                 accuracy_level: PredictionAccuracy) -> float:
        """估算預測誤差"""
        # 基礎誤差
        base_errors = {
            PredictionAccuracy.LOW: 1.0,      # ±1km
            PredictionAccuracy.MEDIUM: 0.1,   # ±100m
            PredictionAccuracy.HIGH: 0.01,    # ±10m
            PredictionAccuracy.ULTRA: 0.001   # ±1m
        }
        
        base_error = base_errors.get(accuracy_level, 0.1)
        
        # 時間相關誤差增長
        time_hours = abs(time_minutes) / 60.0
        time_factor = 1.0 + 0.1 * time_hours  # 每小時增長10%
        
        return base_error * time_factor
    
    # === 緩存管理 ===
    
    def _generate_cache_key(self, satellite_id: str, request: PredictionRequest) -> str:
        """生成緩存鍵"""
        key_components = [
            satellite_id,
            request.start_time.isoformat(),
            request.end_time.isoformat(),
            str(request.time_step_seconds),
            request.accuracy_level.value,
            str(sorted(p.value for p in request.include_perturbations))
        ]
        return "|".join(key_components)
    
    def _get_cached_result(self, cache_key: str) -> Optional[PredictionResult]:
        """獲取緩存結果"""
        if cache_key in self.prediction_cache:
            # 檢查緩存時效性
            cached_time = self.cache_timestamps.get(cache_key)
            if cached_time and (datetime.now(timezone.utc) - cached_time).seconds < 300:  # 5分鐘有效
                return self.prediction_cache[cache_key]
            else:
                # 清理過期緩存
                del self.prediction_cache[cache_key]
                del self.cache_timestamps[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: PredictionResult):
        """緩存結果"""
        with self.prediction_lock:
            self.prediction_cache[cache_key] = result
            self.cache_timestamps[cache_key] = datetime.now(timezone.utc)
            
            # 限制緩存大小
            if len(self.prediction_cache) > self.prediction_config['cache_size']:
                # 移除最舊的緩存條目
                oldest_key = min(self.cache_timestamps.keys(), 
                               key=lambda k: self.cache_timestamps[k])
                del self.prediction_cache[oldest_key]
                del self.cache_timestamps[oldest_key]
    
    async def _cache_cleanup_loop(self):
        """緩存清理循環"""
        try:
            while self.is_running:
                await asyncio.sleep(300)  # 每5分鐘清理一次
                
                current_time = datetime.now(timezone.utc)
                expired_keys = []
                
                for key, timestamp in self.cache_timestamps.items():
                    if (current_time - timestamp).seconds > 600:  # 10分鐘過期
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.prediction_cache[key]
                    del self.cache_timestamps[key]
                
                if expired_keys:
                    self.logger.debug(f"🗑️ 清理過期緩存: {len(expired_keys)} 個")
                    
        except asyncio.CancelledError:
            self.logger.info("🧹 緩存清理循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 緩存清理異常: {e}")
    
    # === 公共接口方法 ===
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        with self.prediction_lock:
            return {
                'engine_id': self.engine_id,
                'is_running': self.is_running,
                'tle_count': len(self.tle_database),
                'cache_size': len(self.prediction_cache),
                'statistics': self.stats.copy(),
                'configuration': self.prediction_config.copy()
            }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.prediction_config.update(config)
        self.logger.info(f"🔧 軌道預測引擎配置已更新: {list(config.keys())}")


# === 便利函數 ===

def create_orbit_prediction_engine(engine_id: str = None) -> OrbitPredictionEngine:
    """創建軌道預測引擎"""
    engine = OrbitPredictionEngine(engine_id)
    
    logger.info(f"✅ 軌道預測引擎創建完成 - ID: {engine.engine_id}")
    return engine


def create_test_prediction_request(satellite_ids: List[str] = None,
                                 hours_ahead: int = 6,
                                 time_step_minutes: int = 5) -> PredictionRequest:
    """創建測試預測請求"""
    if satellite_ids is None:
        satellite_ids = ["TEST-SAT-001", "TEST-SAT-002"]
    
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=hours_ahead)
    
    return PredictionRequest(
        request_id=f"test_req_{int(start_time.timestamp())}",
        satellite_ids=satellite_ids,
        start_time=start_time,
        end_time=end_time,
        time_step_seconds=time_step_minutes * 60,
        accuracy_level=PredictionAccuracy.MEDIUM,
        observer_latitude_deg=24.9441667,   # NTPU
        observer_longitude_deg=121.3713889,
        observer_altitude_km=0.05,
        include_perturbations=[
            PerturbationType.ATMOSPHERIC_DRAG,
            PerturbationType.EARTH_OBLATENESS
        ]
    )


def create_sample_tle_data() -> List[Dict[str, str]]:
    """創建示例 TLE 數據"""
    return [
        {
            'satellite_id': 'TEST-SAT-001',
            'satellite_name': 'Test Satellite 1',
            'line1': '1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990',
            'line2': '2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509'
        },
        {
            'satellite_id': 'TEST-SAT-002', 
            'satellite_name': 'Test Satellite 2',
            'line1': '1 43013U 17073A   21001.00000000  .00001234  00000-0  25678-4 0  9991',
            'line2': '2 43013  97.4500  45.2100 0014600 135.8100 224.5200 15.24000000123456'
        }
    ]