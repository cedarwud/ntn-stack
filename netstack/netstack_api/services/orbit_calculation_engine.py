#!/usr/bin/env python3
"""
軌道計算引擎 - 基於 SGP4 算法的真實衛星軌道計算

實現統一改進主準則中定義的軌道計算引擎，提供：
1. 真實 TLE 軌道計算
2. 衛星位置預測  
3. 信號強度計算
4. 軌道路徑預測
5. 切換機會預測
"""

import asyncio
import logging
import numpy as np
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import structlog
from sgp4.api import Satrec, jday
from sgp4 import omm
import math

logger = structlog.get_logger(__name__)


@dataclass
class Position:
    """3D 位置"""
    x: float  # km
    y: float  # km 
    z: float  # km
    latitude: Optional[float] = None   # 度
    longitude: Optional[float] = None  # 度
    altitude: Optional[float] = None   # km
    timestamp: Optional[datetime] = None


@dataclass
class SatellitePosition(Position):
    """衛星位置 (繼承 Position)"""
    satellite_id: str = ""
    velocity_x: float = 0.0  # km/s
    velocity_y: float = 0.0  # km/s
    velocity_z: float = 0.0  # km/s
    orbital_period: float = 0.0  # 分鐘
    
    
@dataclass
class SatelliteConfig:
    """衛星配置參數"""
    satellite_id: str
    name: str
    transmit_power_dbm: float = 30.0  # 發射功率
    antenna_gain_dbi: float = 15.0    # 天線增益
    frequency_mhz: float = 2000.0     # 載波頻率
    beam_width_degrees: float = 10.0  # 波束寬度
    
    
@dataclass
class TLEData:
    """TLE 軌道數據"""
    satellite_id: str
    satellite_name: str
    line1: str  # TLE 第一行
    line2: str  # TLE 第二行
    epoch: datetime
    classification: str = "U"  # 分類 (U=未分類)
    international_designator: str = ""
    element_set_number: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    

@dataclass  
class OrbitPath:
    """軌道路徑"""
    satellite_id: str
    positions: List[SatellitePosition]
    start_time: datetime
    end_time: datetime
    orbital_period: float  # 分鐘
    

@dataclass
class HandoverPrediction:
    """切換預測"""
    source_satellite: str
    target_satellite: str
    predicted_time: datetime
    confidence: float  # 0-1
    signal_quality: float  # dBm
    duration_seconds: float
    

@dataclass
class TimeRange:
    """時間範圍"""
    start: datetime
    end: datetime
    

class SignalModel(Enum):
    """信號傳播模型"""
    FREE_SPACE = "free_space"
    ATMOSPHERIC = "atmospheric"  
    IONOSPHERIC = "ionospheric"
    

class OrbitCalculationEngine:
    """
    軌道計算引擎 - 統一改進主準則實現
    
    功能：
    1. 基於 SGP4 的真實軌道計算
    2. TLE 數據管理和更新
    3. 信號強度預測
    4. 軌道路徑預測
    5. 切換機會預測
    """
    
    def __init__(self, update_interval_hours: int = 24):
        """
        初始化軌道計算引擎
        
        Args:
            update_interval_hours: TLE 數據更新間隔（小時）
        """
        self.logger = structlog.get_logger(__name__)
        self.update_interval_hours = update_interval_hours
        
        # TLE 數據存儲
        self.tle_database: Dict[str, TLEData] = {}
        self.satellite_configs: Dict[str, SatelliteConfig] = {}
        
        # SGP4 計算對象緩存
        self.sgp4_cache: Dict[str, Satrec] = {}
        
        # 軌道預計算緩存
        self.orbit_cache: Dict[str, List[SatellitePosition]] = {}
        self.cache_duration_hours = 1  # 緩存有效期 1 小時
        
        # 技術規範參數
        self.position_accuracy_km = 1.0  # 位置精度要求 < 1km
        self.signal_accuracy_db = 3.0    # 信號預測誤差 < 3dB
        
        self.logger.info(
            "軌道計算引擎初始化完成",
            update_interval_hours=update_interval_hours,
            position_accuracy_km=self.position_accuracy_km,
            signal_accuracy_db=self.signal_accuracy_db
        )
        
    def add_tle_data(self, tle_data: TLEData) -> bool:
        """
        添加 TLE 軌道數據
        
        Args:
            tle_data: TLE 數據對象
            
        Returns:
            是否成功添加
        """
        try:
            # 驗證 TLE 數據格式
            if not self._validate_tle_format(tle_data.line1, tle_data.line2):
                self.logger.error("TLE 數據格式無效", satellite_id=tle_data.satellite_id)
                return False
                
            # 創建 SGP4 對象
            satellite = Satrec.twoline2rv(tle_data.line1, tle_data.line2)
            
            if satellite.error != 0:
                self.logger.error(
                    "SGP4 初始化失敗", 
                    satellite_id=tle_data.satellite_id,
                    error_code=satellite.error
                )
                return False
                
            # 存儲數據
            self.tle_database[tle_data.satellite_id] = tle_data
            self.sgp4_cache[tle_data.satellite_id] = satellite
            
            # 清除相關軌道緩存
            if tle_data.satellite_id in self.orbit_cache:
                del self.orbit_cache[tle_data.satellite_id]
                
            self.logger.info(
                "TLE 數據添加成功",
                satellite_id=tle_data.satellite_id,
                satellite_name=tle_data.satellite_name,
                epoch=tle_data.epoch.isoformat()
            )
            return True
            
        except Exception as e:
            self.logger.error(
                "TLE 數據添加失敗",
                satellite_id=tle_data.satellite_id,
                error=str(e)
            )
            return False
            
    def add_satellite_config(self, config: SatelliteConfig) -> None:
        """添加衛星配置"""
        self.satellite_configs[config.satellite_id] = config
        self.logger.info(
            "衛星配置添加成功",
            satellite_id=config.satellite_id,
            name=config.name
        )
        
    def calculate_satellite_position(
        self, 
        satellite_id: str, 
        timestamp: float
    ) -> Optional[SatellitePosition]:
        """
        計算指定時間的衛星位置
        
        Args:
            satellite_id: 衛星ID
            timestamp: Unix 時間戳
            
        Returns:
            衛星位置對象或 None
        """
        try:
            if satellite_id not in self.sgp4_cache:
                self.logger.error("衛星SGP4對象不存在", satellite_id=satellite_id)
                return None
                
            satellite = self.sgp4_cache[satellite_id]
            
            # 轉換時間格式
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            
            # SGP4 計算
            error, position_teme, velocity_teme = satellite.sgp4(jd, fr)
            
            if error != 0:
                self.logger.error(
                    "SGP4 計算錯誤",
                    satellite_id=satellite_id,
                    error_code=error,
                    timestamp=timestamp
                )
                return None
                
            # 轉換座標 (TEME -> ECI)
            x, y, z = position_teme  # km
            vx, vy, vz = velocity_teme  # km/s
            
            # 計算地理座標
            lat, lon, alt = self._eci_to_geodetic(x, y, z, dt)
            
            # 計算軌道週期
            orbital_period = self._calculate_orbital_period(satellite)
            
            satellite_pos = SatellitePosition(
                satellite_id=satellite_id,
                x=x, y=y, z=z,
                latitude=lat, longitude=lon, altitude=alt,
                velocity_x=vx, velocity_y=vy, velocity_z=vz,
                orbital_period=orbital_period,
                timestamp=dt
            )
            
            return satellite_pos
            
        except Exception as e:
            self.logger.error(
                "衛星位置計算失敗",
                satellite_id=satellite_id,
                timestamp=timestamp,
                error=str(e)
            )
            return None
            
    def calculate_distance(
        self, 
        satellite_pos: SatellitePosition, 
        ue_pos: Position
    ) -> float:
        """
        計算衛星與 UE 之間的距離
        
        Args:
            satellite_pos: 衛星位置
            ue_pos: UE 位置
            
        Returns:
            距離 (km)
        """
        try:
            # 如果 UE 位置是地理座標，轉換為 ECI 座標
            if ue_pos.latitude is not None and ue_pos.longitude is not None:
                ue_x, ue_y, ue_z = self._geodetic_to_eci(
                    ue_pos.latitude, 
                    ue_pos.longitude, 
                    ue_pos.altitude or 0.0,
                    satellite_pos.timestamp or datetime.now(timezone.utc)
                )
            else:
                ue_x, ue_y, ue_z = ue_pos.x, ue_pos.y, ue_pos.z
                
            # 計算歐幾里得距離
            distance = math.sqrt(
                (satellite_pos.x - ue_x)**2 + 
                (satellite_pos.y - ue_y)**2 + 
                (satellite_pos.z - ue_z)**2
            )
            
            return distance
            
        except Exception as e:
            self.logger.error(
                "距離計算失敗",
                satellite_id=satellite_pos.satellite_id,
                error=str(e)
            )
            return float('inf')
            
    def calculate_signal_strength(
        self, 
        distance: float, 
        satellite_params: SatelliteConfig,
        model: SignalModel = SignalModel.FREE_SPACE
    ) -> float:
        """
        計算信號強度
        
        Args:
            distance: 距離 (km)
            satellite_params: 衛星參數
            model: 信號傳播模型
            
        Returns:
            信號強度 (dBm)
        """
        try:
            if distance <= 0:
                return float('-inf')
                
            # 基本自由空間路徑損耗
            frequency_hz = satellite_params.frequency_mhz * 1e6
            fspl_db = 20 * math.log10(distance * 1000) + \
                     20 * math.log10(frequency_hz) + \
                     20 * math.log10(4 * math.pi / 3e8)
            
            # 計算接收信號強度
            rsrp_dbm = (satellite_params.transmit_power_dbm + 
                       satellite_params.antenna_gain_dbi - 
                       fspl_db)
            
            # 根據模型添加額外損耗
            if model == SignalModel.ATMOSPHERIC:
                rsrp_dbm -= self._calculate_atmospheric_loss(distance)
            elif model == SignalModel.IONOSPHERIC:
                rsrp_dbm -= self._calculate_ionospheric_loss(
                    distance, satellite_params.frequency_mhz
                )
                
            return rsrp_dbm
            
        except Exception as e:
            self.logger.error(
                "信號強度計算失敗",
                distance=distance,
                satellite_id=satellite_params.satellite_id,
                error=str(e)
            )
            return float('-inf')
            
    def predict_orbit_path(
        self, 
        satellite_id: str, 
        time_range: TimeRange,
        sample_interval_minutes: int = 5
    ) -> Optional[OrbitPath]:
        """
        預測軌道路徑
        
        Args:
            satellite_id: 衛星ID
            time_range: 預測時間範圍
            sample_interval_minutes: 採樣間隔（分鐘）
            
        Returns:
            軌道路徑對象
        """
        try:
            if satellite_id not in self.sgp4_cache:
                self.logger.error("衛星不存在", satellite_id=satellite_id)
                return None
                
            positions = []
            current_time = time_range.start
            interval_delta = timedelta(minutes=sample_interval_minutes)
            
            while current_time <= time_range.end:
                timestamp = current_time.timestamp()
                pos = self.calculate_satellite_position(satellite_id, timestamp)
                
                if pos:
                    positions.append(pos)
                    
                current_time += interval_delta
                
            if not positions:
                return None
                
            # 計算軌道週期
            orbital_period = positions[0].orbital_period if positions else 90.0
            
            orbit_path = OrbitPath(
                satellite_id=satellite_id,
                positions=positions,
                start_time=time_range.start,
                end_time=time_range.end,
                orbital_period=orbital_period
            )
            
            self.logger.info(
                "軌道路徑預測完成",
                satellite_id=satellite_id,
                positions_count=len(positions),
                duration_hours=(time_range.end - time_range.start).total_seconds() / 3600
            )
            
            return orbit_path
            
        except Exception as e:
            self.logger.error(
                "軌道路徑預測失敗",
                satellite_id=satellite_id,
                error=str(e)
            )
            return None
            
    def predict_handover_opportunity(
        self, 
        ue_pos: Position, 
        time_window: int
    ) -> List[HandoverPrediction]:
        """
        預測切換機會
        
        Args:
            ue_pos: UE 位置
            time_window: 預測時間窗口（秒）
            
        Returns:
            切換預測列表
        """
        try:
            predictions = []
            current_time = datetime.now(timezone.utc)
            end_time = current_time + timedelta(seconds=time_window)
            
            # 獲取所有可用衛星
            available_satellites = list(self.sgp4_cache.keys())
            
            if len(available_satellites) < 2:
                self.logger.warning("可用衛星數量不足，無法預測切換", count=len(available_satellites))
                return predictions
                
            # 分析每對衛星的切換機會
            for i, source_sat in enumerate(available_satellites):
                for target_sat in available_satellites[i+1:]:
                    prediction = self._analyze_handover_opportunity(
                        source_sat, target_sat, ue_pos, current_time, end_time
                    )
                    
                    if prediction:
                        predictions.append(prediction)
                        
            # 按預測時間排序
            predictions.sort(key=lambda p: p.predicted_time)
            
            self.logger.info(
                "切換機會預測完成",
                ue_position=f"({ue_pos.latitude:.3f}, {ue_pos.longitude:.3f})",
                time_window_seconds=time_window,
                predictions_count=len(predictions)
            )
            
            return predictions
            
        except Exception as e:
            self.logger.error(
                "切換機會預測失敗",
                time_window=time_window,
                error=str(e)
            )
            return []
            
    def _validate_tle_format(self, line1: str, line2: str) -> bool:
        """驗證 TLE 格式"""
        try:
            if len(line1) != 69 or len(line2) != 69:
                return False
            if line1[0] != '1' or line2[0] != '2':
                return False
            return True
        except:
            return False
            
    def _eci_to_geodetic(
        self, 
        x: float, y: float, z: float, 
        dt: datetime
    ) -> Tuple[float, float, float]:
        """ECI 座標轉地理座標"""
        try:
            # 簡化實現 - 實際項目中應使用更精確的轉換
            r = math.sqrt(x*x + y*y + z*z)
            lat = math.degrees(math.asin(z / r))
            lon = math.degrees(math.atan2(y, x))
            alt = r - 6371.0  # 地球半徑 6371 km
            
            return lat, lon, alt
        except:
            return 0.0, 0.0, 0.0
            
    def _geodetic_to_eci(
        self, 
        lat: float, lon: float, alt: float, 
        dt: datetime
    ) -> Tuple[float, float, float]:
        """地理座標轉 ECI 座標"""
        try:
            # 簡化實現
            r = 6371.0 + alt
            lat_rad = math.radians(lat)
            lon_rad = math.radians(lon)
            
            x = r * math.cos(lat_rad) * math.cos(lon_rad)
            y = r * math.cos(lat_rad) * math.sin(lon_rad)
            z = r * math.sin(lat_rad)
            
            return x, y, z
        except:
            return 0.0, 0.0, 0.0
            
    def _calculate_orbital_period(self, satellite: Satrec) -> float:
        """計算軌道週期（分鐘）"""
        try:
            # 從 SGP4 參數計算
            n = satellite.no_kozai  # 平均運動 (rad/min)
            if n > 0:
                period_minutes = 2 * math.pi / n
                return period_minutes
            return 90.0  # 默認值
        except:
            return 90.0
            
    def _calculate_atmospheric_loss(self, distance: float) -> float:
        """計算大氣損耗 (dB)"""
        if distance > 500:  # > 500km 認為在太空
            return 2.0  # 基本大氣損耗
        return 0.1 * distance  # 線性近似
        
    def _calculate_ionospheric_loss(self, distance: float, frequency_mhz: float) -> float:
        """計算電離層損耗 (dB)"""
        if frequency_mhz < 1000:  # 低頻段
            return 3.0
        return 1.0  # 高頻段損耗較小
        
    def _analyze_handover_opportunity(
        self,
        source_sat: str,
        target_sat: str, 
        ue_pos: Position,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[HandoverPrediction]:
        """分析特定衛星對的切換機會"""
        try:
            # 簡化實現 - 尋找信號交叉點
            best_time = None
            best_confidence = 0.0
            best_signal = float('-inf')
            
            current = start_time
            interval = timedelta(minutes=5)
            
            while current <= end_time:
                timestamp = current.timestamp()
                
                # 計算兩顆衛星的信號強度
                source_pos = self.calculate_satellite_position(source_sat, timestamp)
                target_pos = self.calculate_satellite_position(target_sat, timestamp)
                
                if source_pos and target_pos:
                    source_dist = self.calculate_distance(source_pos, ue_pos)
                    target_dist = self.calculate_distance(target_pos, ue_pos)
                    
                    # 獲取衛星配置
                    source_config = self.satellite_configs.get(
                        source_sat, 
                        SatelliteConfig(source_sat, "unknown")
                    )
                    target_config = self.satellite_configs.get(
                        target_sat,
                        SatelliteConfig(target_sat, "unknown")
                    )
                    
                    source_signal = self.calculate_signal_strength(source_dist, source_config)
                    target_signal = self.calculate_signal_strength(target_dist, target_config)
                    
                    # 檢查是否為好的切換時機 (目標信號 > 源信號 + 3dB)
                    if target_signal > source_signal + 3.0:
                        confidence = min(1.0, (target_signal - source_signal) / 10.0)
                        if confidence > best_confidence:
                            best_time = current
                            best_confidence = confidence
                            best_signal = target_signal
                            
                current += interval
                
            if best_time and best_confidence > 0.5:
                return HandoverPrediction(
                    source_satellite=source_sat,
                    target_satellite=target_sat,
                    predicted_time=best_time,
                    confidence=best_confidence,
                    signal_quality=best_signal,
                    duration_seconds=300.0  # 假設 5 分鐘窗口
                )
                
            return None
            
        except Exception as e:
            self.logger.error(
                "切換機會分析失敗",
                source=source_sat,
                target=target_sat,
                error=str(e)
            )
            return None
            
    async def load_starlink_tle_data(self) -> int:
        """
        載入 Starlink 星座 TLE 數據 (示例實現)
        
        Returns:
            載入的衛星數量
        """
        try:
            # 示例 TLE 數據 (實際應從 NORAD/CelesTrak 獲取)
            example_tles = [
                {
                    "name": "STARLINK-1007",
                    "id": "starlink_1007", 
                    "line1": "1 44713U 19074A   24001.00000000  .00002182  00000-0  16538-3 0  9992",
                    "line2": "2 44713  53.0000 194.8273 0001950  92.9929 267.1872 15.06906744267896"
                },
                {
                    "name": "STARLINK-1008",
                    "id": "starlink_1008",
                    "line1": "1 44714U 19074B   24001.00000000  .00001743  00000-0  13322-3 0  9999",
                    "line2": "2 44714  53.0000 194.8294 0001982  93.1188 267.0632 15.06908856267893"
                },
                {
                    "name": "STARLINK-1009", 
                    "id": "starlink_1009",
                    "line1": "1 44715U 19074C   24001.00000000  .00001895  00000-0  14443-3 0  9996",
                    "line2": "2 44715  53.0000 194.8314 0001967  93.2447 266.9393 15.06907950267890"
                },
                {
                    "name": "STARLINK-1010",
                    "id": "starlink_1010", 
                    "line1": "1 44716U 19074D   24001.00000000  .00001654  00000-0  12689-3 0  9993",
                    "line2": "2 44716  53.0000 194.8335 0001953  93.3706 266.8154 15.06909762267897"
                }
            ]
            
            loaded_count = 0
            current_time = datetime.now(timezone.utc)
            
            for tle_data in example_tles:
                tle = TLEData(
                    satellite_id=tle_data["id"],
                    satellite_name=tle_data["name"],
                    line1=tle_data["line1"],
                    line2=tle_data["line2"],
                    epoch=current_time,
                    last_updated=current_time
                )
                
                if self.add_tle_data(tle):
                    # 添加默認配置
                    config = SatelliteConfig(
                        satellite_id=tle_data["id"],
                        name=tle_data["name"],
                        transmit_power_dbm=30.0,
                        antenna_gain_dbi=15.0,
                        frequency_mhz=12000.0,  # Ku-band
                        beam_width_degrees=5.0
                    )
                    self.add_satellite_config(config)
                    loaded_count += 1
                    
            self.logger.info(
                "Starlink TLE 數據載入完成",
                loaded_count=loaded_count,
                total_attempted=len(example_tles)
            )
            
            return loaded_count
            
        except Exception as e:
            self.logger.error("Starlink TLE 數據載入失敗", error=str(e))
            return 0