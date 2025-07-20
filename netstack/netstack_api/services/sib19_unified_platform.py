#!/usr/bin/env python3
"""
SIB19 統一基礎平台 - NTN 測量事件系統核心

實現統一改進主準則 v3.0 中定義的 SIB19 統一基礎平台：
1. SIB19 解析引擎 (全事件支援)
2. 統一位置計算系統
3. 時頻校正統一系統
4. 鄰居細胞統一管理器
5. SMTC 深度整合模組
6. SIB19 生命週期管理
7. 多衛星星座管理器

核心理念：SIB19 作為 NTN 系統的統一資訊基礎平台，
為 A4、D1、D2、T1 等所有測量事件提供共享的時空基準和配置支援
"""

import asyncio
import logging
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog

from .orbit_calculation_engine import (
    OrbitCalculationEngine, SatellitePosition, Position, 
    SatelliteConfig, TLEData, TimeRange
)
from .tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)


class ReferenceLocationType(Enum):
    """參考位置類型"""
    STATIC = "static"      # D1 事件的固定參考位置
    DYNAMIC = "dynamic"    # D2 事件的動態參考位置 (衛星軌道)
    

class SIB19BroadcastState(Enum):
    """SIB19 廣播狀態"""
    VALID = "valid"           # 有效
    EXPIRING = "expiring"     # 即將過期
    EXPIRED = "expired"       # 已過期
    UPDATING = "updating"     # 更新中
    ERROR = "error"          # 錯誤
    

@dataclass
class EphemerisData:
    """衛星星曆數據 (基於 3GPP TS 38.331)"""
    satellite_id: str
    tle_data: TLEData
    
    # 3GPP SIB19 星曆參數
    semi_major_axis: float      # 半長軸 (m)
    eccentricity: float         # 偏心率
    perigee_argument: float     # 近地點幅角 (度)
    longitude_ascending: float  # 升交點經度 (度) 
    inclination: float          # 軌道傾角 (度)
    mean_anomaly: float         # 平近點角 (度)
    
    # 時間參數
    epoch_time: datetime        # 星曆參考時間
    validity_time: float        # 有效期 (小時)
    
    # 軌道修正參數
    mean_motion_delta: float = 0.0      # 平均運動修正
    mean_motion_dot: float = 0.0        # 平均運動變化率
    

@dataclass
class ReferenceLocation:
    """參考位置 (3GPP SIB19)"""
    location_type: ReferenceLocationType
    
    # 靜態參考位置 (D1 事件)
    latitude: Optional[float] = None    # 度
    longitude: Optional[float] = None   # 度
    altitude: Optional[float] = None    # 米
    
    # 動態參考位置 (D2 事件) - 衛星軌道
    satellite_id: Optional[str] = None
    orbital_position: Optional[SatellitePosition] = None
    
    # 全球化支援
    coordinate_system: str = "WGS84"
    time_zone: Optional[str] = None
    

@dataclass
class PositionCompensation:
    """位置補償參數 ΔS,T(t) (A4 事件專用)"""
    delta_s: float     # 空間補償項 (m)
    delta_t: float     # 時間補償項 (ms)  
    
    # 計算參數
    ue_position: Position
    satellite_position: SatellitePosition
    target_satellite_position: SatellitePosition
    
    # 動態參數
    doppler_correction: float = 0.0     # 多普勒修正
    range_rate_correction: float = 0.0  # 距離變化率修正
    
    calculation_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    

@dataclass
class TimeCorrection:
    """時頻校正參數"""
    
    # GNSS 時間參數
    gnss_time_offset: float     # GNSS 時間偏移 (ms)
    delta_gnss_time: float      # GNSS 時間差 (ms)
    
    # 絕對時間基準 (T1 事件)
    epoch_time: datetime        # 絕對時間基準
    t_service: float           # 服務時間 (秒)
    
    # Doppler 參數
    doppler_shift_hz: float = 0.0       # 多普勒頻移 (Hz)
    carrier_frequency_hz: float = 0.0   # 載波頻率 (Hz)
    
    # 精度要求
    sync_accuracy_ms: float = 50.0      # 時間同步精度要求 < 50ms
    current_accuracy_ms: float = 0.0    # 當前精度
    
    last_sync_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    

@dataclass
class NeighborCellConfig:
    """鄰居細胞配置 (ntn-NeighCellConfigList)"""
    physical_cell_id: int       # 物理細胞識別碼
    carrier_frequency: float    # 載波頻率 (MHz)
    satellite_id: str          # 關聯的衛星ID
    
    # 星曆配置
    use_shared_ephemeris: bool = True   # 是否使用共用星曆
    individual_ephemeris: Optional[EphemerisData] = None
    
    # 測量配置
    measurement_priority: int = 1       # 測量優先級 (1-8)
    is_active: bool = True             # 是否激活
    

@dataclass
class SMTCConfiguration:
    """SMTC (SSB-based Measurement Timing Configuration) 配置"""
    
    # 必需字段 (無默認值)
    measurement_slots: List[int]        # 測量時隙
    
    # 可選字段 (有默認值)
    periodicity_ms: int = 20           # 週期性 (ms)
    offset_ms: int = 0                 # 偏移 (ms)
    visibility_windows: List[Tuple[datetime, datetime]] = field(default_factory=list)
    power_optimization: bool = True     # 功耗優化
    measurement_efficiency: float = 0.85  # 測量效率目標
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    

@dataclass
class SIB19Data:
    """完整的 SIB19 數據結構"""
    
    # 所有必需的字段（無默認值）
    broadcast_id: str
    broadcast_time: datetime
    validity_time: float        # 有效期 (小時)
    satellite_ephemeris: Dict[str, EphemerisData]
    reference_location: ReferenceLocation
    time_correction: TimeCorrection
    
    # 可選字段（有默認值）
    moving_reference_location: Optional[ReferenceLocation] = None
    neighbor_cells: List[NeighborCellConfig] = field(default_factory=list)
    smtc_config: SMTCConfiguration = field(default_factory=lambda: SMTCConfiguration(measurement_slots=[0, 1]))
    broadcast_state: SIB19BroadcastState = SIB19BroadcastState.VALID
    expiry_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24))
    

class SIB19UnifiedPlatform:
    """
    SIB19 統一基礎平台
    
    實現 "資訊統一、應用分化" 的理想架構：
    - 統一的 SIB19 基礎平台為所有測量事件提供共享資訊
    - 不同事件根據特點選擇性使用 SIB19 相關資訊子集
    """
    
    def __init__(
        self, 
        orbit_engine: OrbitCalculationEngine,
        tle_manager: TLEDataManager
    ):
        """
        初始化 SIB19 統一平台
        
        Args:
            orbit_engine: 軌道計算引擎
            tle_manager: TLE 數據管理器
        """
        self.logger = structlog.get_logger(__name__)
        self.orbit_engine = orbit_engine
        self.tle_manager = tle_manager
        
        # SIB19 數據存儲
        self.current_sib19: Optional[SIB19Data] = None
        self.sib19_history: List[SIB19Data] = []
        self.max_history = 10
        
        # 多衛星管理
        self.tracked_satellites: Dict[str, SatellitePosition] = {}
        self.max_tracked_satellites = 8  # 最多追蹤 8 顆鄰居衛星
        
        # 生命週期管理
        self.update_interval_minutes = 30  # SIB19 更新間隔
        self.expiry_warning_hours = 2      # 過期警告提前時間
        
        # 事件特定緩存
        self._a4_compensation_cache: Dict[str, PositionCompensation] = {}
        self._d1_reference_cache: Optional[ReferenceLocation] = None
        self._d2_reference_cache: Optional[ReferenceLocation] = None
        self._t1_time_frame_cache: Optional[TimeCorrection] = None
        
        self.logger.info(
            "SIB19 統一基礎平台初始化完成",
            max_tracked_satellites=self.max_tracked_satellites,
            update_interval_minutes=self.update_interval_minutes
        )
        
    async def initialize_sib19_platform(self) -> bool:
        """初始化 SIB19 平台"""
        try:
            # 載入可用衛星
            active_satellites = await self.tle_manager.get_active_satellites()
            
            if len(active_satellites) < 4:
                self.logger.warning(
                    "可用衛星數量不足",
                    available=len(active_satellites),
                    minimum_required=4
                )
                
            # 初始化默認 SIB19 配置
            await self._create_default_sib19()
            
            # 啟動生命週期管理
            asyncio.create_task(self._sib19_lifecycle_manager())
            
            self.logger.info(
                "SIB19 平台初始化成功",
                available_satellites=len(active_satellites)
            )
            return True
            
        except Exception as e:
            self.logger.error("SIB19 平台初始化失敗", error=str(e))
            return False
            
    async def generate_sib19_broadcast(
        self, 
        service_area_center: Position,
        target_satellites: Optional[List[str]] = None
    ) -> Optional[SIB19Data]:
        """
        生成 SIB19 廣播數據
        
        Args:
            service_area_center: 服務區域中心位置
            target_satellites: 目標衛星列表 (可選)
            
        Returns:
            SIB19 數據對象
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            # 選擇最佳衛星組合
            if not target_satellites:
                target_satellites = await self._select_optimal_satellites(
                    service_area_center, 
                    current_time
                )
                
            if not target_satellites:
                self.logger.error("無法選擇合適的衛星")
                return None
                
            # 生成星曆數據
            satellite_ephemeris = {}
            for sat_id in target_satellites:
                ephemeris = await self._generate_ephemeris_data(sat_id)
                if ephemeris:
                    satellite_ephemeris[sat_id] = ephemeris
                    
            # 創建參考位置
            reference_location = ReferenceLocation(
                location_type=ReferenceLocationType.STATIC,
                latitude=service_area_center.latitude,
                longitude=service_area_center.longitude,
                altitude=service_area_center.altitude or 0.0
            )
            
            # 動態參考位置 (選擇主服務衛星)
            primary_satellite = target_satellites[0]
            moving_reference = await self._create_moving_reference_location(primary_satellite)
            
            # 時間校正
            time_correction = await self._generate_time_correction()
            
            # 鄰居細胞配置
            neighbor_cells = await self._generate_neighbor_cell_configs(target_satellites)
            
            # SMTC 配置
            smtc_config = await self._generate_smtc_configuration(target_satellites)
            
            # 創建 SIB19 數據
            sib19_data = SIB19Data(
                broadcast_id=f"sib19_{current_time.strftime('%Y%m%d_%H%M%S')}",
                broadcast_time=current_time,
                validity_time=24.0,  # 24 小時有效期
                satellite_ephemeris=satellite_ephemeris,
                reference_location=reference_location,
                moving_reference_location=moving_reference,
                time_correction=time_correction,
                neighbor_cells=neighbor_cells,
                smtc_config=smtc_config,
                expiry_time=current_time + timedelta(hours=24)
            )
            
            # 更新當前 SIB19
            self.current_sib19 = sib19_data
            
            # 保存歷史
            self.sib19_history.append(sib19_data)
            if len(self.sib19_history) > self.max_history:
                self.sib19_history = self.sib19_history[-self.max_history:]
                
            self.logger.info(
                "SIB19 廣播數據生成完成",
                broadcast_id=sib19_data.broadcast_id,
                satellites_count=len(satellite_ephemeris),
                neighbor_cells_count=len(neighbor_cells),
                validity_hours=sib19_data.validity_time
            )
            
            return sib19_data
            
        except Exception as e:
            self.logger.error("SIB19 廣播數據生成失敗", error=str(e))
            return None
            
    async def get_a4_position_compensation(
        self,
        ue_position: Position,
        serving_satellite: str,
        target_satellite: str
    ) -> Optional[PositionCompensation]:
        """
        獲取 A4 事件的位置補償參數 ΔS,T(t)
        
        Args:
            ue_position: UE 位置
            serving_satellite: 服務衛星ID
            target_satellite: 目標衛星ID
            
        Returns:
            位置補償對象
        """
        try:
            cache_key = f"{serving_satellite}_{target_satellite}_{ue_position.latitude}_{ue_position.longitude}"
            
            # 檢查緩存
            if cache_key in self._a4_compensation_cache:
                cached = self._a4_compensation_cache[cache_key]
                if (datetime.now(timezone.utc) - cached.calculation_time).seconds < 60:
                    return cached
                    
            # 獲取衛星位置
            current_time = datetime.now(timezone.utc).timestamp()
            serving_pos = self.orbit_engine.calculate_satellite_position(serving_satellite, current_time)
            target_pos = self.orbit_engine.calculate_satellite_position(target_satellite, current_time)
            
            if not serving_pos or not target_pos:
                return None
                
            # 計算位置補償
            compensation = await self._calculate_position_compensation(
                ue_position, serving_pos, target_pos
            )
            
            # 更新緩存
            self._a4_compensation_cache[cache_key] = compensation
            
            return compensation
            
        except Exception as e:
            self.logger.error(
                "A4 位置補償計算失敗",
                serving_satellite=serving_satellite,
                target_satellite=target_satellite,
                error=str(e)
            )
            return None
            
    async def get_d1_reference_location(self) -> Optional[ReferenceLocation]:
        """獲取 D1 事件的固定參考位置"""
        if self.current_sib19:
            return self.current_sib19.reference_location
        return None
        
    async def get_d2_moving_reference_location(self) -> Optional[ReferenceLocation]:
        """獲取 D2 事件的動態參考位置"""
        if self.current_sib19:
            return self.current_sib19.moving_reference_location
        return None
        
    async def get_t1_time_frame(self) -> Optional[TimeCorrection]:
        """獲取 T1 事件的時間框架參數"""
        if self.current_sib19:
            return self.current_sib19.time_correction
        return None
        
    async def get_neighbor_cell_configs(self) -> List[NeighborCellConfig]:
        """獲取鄰居細胞配置 (所有事件共享)"""
        if self.current_sib19:
            return self.current_sib19.neighbor_cells
        return []
        
    async def get_smtc_measurement_windows(
        self, 
        satellite_ids: List[str]
    ) -> List[Tuple[datetime, datetime]]:
        """
        獲取 SMTC 測量窗口 (基於衛星可見性)
        
        Args:
            satellite_ids: 衛星ID列表
            
        Returns:
            測量窗口時間段列表
        """
        try:
            if not self.current_sib19:
                return []
                
            windows = []
            current_time = datetime.now(timezone.utc)
            
            # 計算未來 1 小時的可見性窗口
            for satellite_id in satellite_ids:
                satellite_windows = await self._calculate_visibility_windows(
                    satellite_id,
                    current_time,
                    current_time + timedelta(hours=1)
                )
                windows.extend(satellite_windows)
                
            # 去重並排序
            windows = list(set(windows))
            windows.sort(key=lambda w: w[0])
            
            return windows
            
        except Exception as e:
            self.logger.error("SMTC 測量窗口計算失敗", error=str(e))
            return []
            
    async def get_sib19_status(self) -> Dict[str, Any]:
        """獲取 SIB19 狀態資訊"""
        if not self.current_sib19:
            return {
                "status": "not_initialized",
                "message": "SIB19 未初始化"
            }
            
        current_time = datetime.now(timezone.utc)
        time_to_expiry = (self.current_sib19.expiry_time - current_time).total_seconds() / 3600
        
        # 判斷狀態
        if time_to_expiry <= 0:
            status = SIB19BroadcastState.EXPIRED
        elif time_to_expiry <= self.expiry_warning_hours:
            status = SIB19BroadcastState.EXPIRING
        else:
            status = SIB19BroadcastState.VALID
            
        return {
            "status": status.value,
            "broadcast_id": self.current_sib19.broadcast_id,
            "broadcast_time": self.current_sib19.broadcast_time.isoformat(),
            "validity_hours": self.current_sib19.validity_time,
            "time_to_expiry_hours": max(0, time_to_expiry),
            "satellites_count": len(self.current_sib19.satellite_ephemeris),
            "neighbor_cells_count": len(self.current_sib19.neighbor_cells),
            "time_sync_accuracy_ms": self.current_sib19.time_correction.current_accuracy_ms,
            "reference_location": {
                "type": self.current_sib19.reference_location.location_type.value,
                "latitude": self.current_sib19.reference_location.latitude,
                "longitude": self.current_sib19.reference_location.longitude
            } if self.current_sib19.reference_location else None
        }
        
    async def _create_default_sib19(self) -> None:
        """創建默認 SIB19 配置"""
        try:
            # 默認服務區域中心 (台北)
            default_center = Position(
                x=0, y=0, z=0,
                latitude=25.0330,
                longitude=121.5654,
                altitude=100.0
            )
            
            await self.generate_sib19_broadcast(default_center)
            
        except Exception as e:
            self.logger.error("默認 SIB19 創建失敗", error=str(e))
            
    async def _select_optimal_satellites(
        self, 
        center_position: Position, 
        target_time: datetime
    ) -> List[str]:
        """選擇最佳衛星組合"""
        try:
            active_satellites = await self.tle_manager.get_active_satellites()
            
            if len(active_satellites) < 4:
                # 如果衛星不足，返回所有可用的
                return [sat.satellite_id for sat in active_satellites]
                
            # 選擇最佳的 4-8 顆衛星
            satellite_scores = []
            
            for tle_data in active_satellites:
                sat_pos = self.orbit_engine.calculate_satellite_position(
                    tle_data.satellite_id,
                    target_time.timestamp()
                )
                
                if sat_pos:
                    # 計算評分 (基於距離、仰角等)
                    distance = self.orbit_engine.calculate_distance(sat_pos, center_position)
                    elevation = self._calculate_elevation_angle(sat_pos, center_position)
                    
                    # 評分函數：距離越近、仰角越高分數越高
                    score = (90 - elevation) / 90.0 + distance / 2000.0
                    satellite_scores.append((tle_data.satellite_id, score))
                    
            # 按評分排序，選擇最佳的 4-6 顆
            satellite_scores.sort(key=lambda x: x[1])
            selected = [sat_id for sat_id, _ in satellite_scores[:6]]
            
            return selected
            
        except Exception as e:
            self.logger.error("衛星選擇失敗", error=str(e))
            return []
            
    async def _generate_ephemeris_data(self, satellite_id: str) -> Optional[EphemerisData]:
        """生成衛星星曆數據"""
        try:
            tle_data = await self.tle_manager.get_tle_data(satellite_id)
            if not tle_data:
                return None
                
            # 從 TLE 提取軌道參數
            line2 = tle_data.line2
            
            # 軌道傾角 (第9-16位)
            inclination = float(line2[8:16])
            
            # 升交點經度 (第18-25位)
            longitude_ascending = float(line2[17:25])
            
            # 偏心率 (第27-33位, 需要加小數點)
            eccentricity = float("0." + line2[26:33])
            
            # 近地點幅角 (第35-42位)
            perigee_argument = float(line2[34:42])
            
            # 平近點角 (第44-51位)
            mean_anomaly = float(line2[43:51])
            
            # 平均運動 (第53-63位) - 轉換為軌道半長軸
            mean_motion = float(line2[52:63])  # 圈/天
            semi_major_axis = ((86400 / (mean_motion * 2 * math.pi))**2 * 3.986004418e14)**(1/3)
            
            ephemeris = EphemerisData(
                satellite_id=satellite_id,
                tle_data=tle_data,
                semi_major_axis=semi_major_axis,
                eccentricity=eccentricity,
                perigee_argument=perigee_argument,
                longitude_ascending=longitude_ascending,
                inclination=inclination,
                mean_anomaly=mean_anomaly,
                epoch_time=tle_data.epoch,
                validity_time=24.0  # 24 小時有效期
            )
            
            return ephemeris
            
        except Exception as e:
            self.logger.error(
                "星曆數據生成失敗",
                satellite_id=satellite_id,
                error=str(e)
            )
            return None
            
    async def _create_moving_reference_location(
        self, 
        satellite_id: str
    ) -> Optional[ReferenceLocation]:
        """創建動態參考位置 (D2 事件用)"""
        try:
            current_time = datetime.now(timezone.utc).timestamp()
            sat_pos = self.orbit_engine.calculate_satellite_position(satellite_id, current_time)
            
            if not sat_pos:
                return None
                
            return ReferenceLocation(
                location_type=ReferenceLocationType.DYNAMIC,
                satellite_id=satellite_id,
                orbital_position=sat_pos
            )
            
        except Exception as e:
            self.logger.error("動態參考位置創建失敗", satellite_id=satellite_id, error=str(e))
            return None
            
    async def _generate_time_correction(self) -> TimeCorrection:
        """生成時間校正參數"""
        current_time = datetime.now(timezone.utc)
        
        # 模擬 GNSS 時間同步 (實際應從 GNSS 接收器獲取)
        gnss_offset = np.random.normal(0, 10)  # 平均 0，標準差 10ms
        
        return TimeCorrection(
            gnss_time_offset=gnss_offset,
            delta_gnss_time=gnss_offset,
            epoch_time=current_time,
            t_service=3600.0,  # 1 小時服務時間
            current_accuracy_ms=abs(gnss_offset),
            last_sync_time=current_time
        )
        
    async def _generate_neighbor_cell_configs(
        self, 
        satellite_ids: List[str]
    ) -> List[NeighborCellConfig]:
        """生成鄰居細胞配置"""
        neighbor_cells = []
        
        for i, sat_id in enumerate(satellite_ids[:8]):  # 最多 8 個鄰居細胞
            config = NeighborCellConfig(
                physical_cell_id=i + 1,
                carrier_frequency=12000.0 + i * 100,  # Ku-band
                satellite_id=sat_id,
                measurement_priority=i + 1
            )
            neighbor_cells.append(config)
            
        return neighbor_cells
        
    async def _generate_smtc_configuration(
        self, 
        satellite_ids: List[str]
    ) -> SMTCConfiguration:
        """生成 SMTC 配置"""
        # 基於衛星數量調整測量時隙
        measurement_slots = list(range(min(len(satellite_ids), 4)))
        
        return SMTCConfiguration(
            measurement_slots=measurement_slots,
            periodicity_ms=20,
            offset_ms=0
        )
        
    async def _calculate_position_compensation(
        self,
        ue_pos: Position,
        serving_pos: SatellitePosition,
        target_pos: SatellitePosition
    ) -> PositionCompensation:
        """計算位置補償參數 ΔS,T(t)"""
        
        # 計算空間補償項 ΔS
        serving_distance = self.orbit_engine.calculate_distance(serving_pos, ue_pos)
        target_distance = self.orbit_engine.calculate_distance(target_pos, ue_pos)
        raw_delta_s = target_distance - serving_distance  # 距離差 (km)
        
        # A4 事件位置補償改進：
        # 對於衛星通信，主要考慮相對幾何差異而非絕對距離差
        # 使用仰角和方位角差異來計算有效的位置補償
        serving_elevation = self._calculate_elevation_angle(serving_pos, ue_pos)
        target_elevation = self._calculate_elevation_angle(target_pos, ue_pos)
        
        # 基於仰角差異的幾何補償 (更符合實際無線通信場景)
        elevation_diff = target_elevation - serving_elevation  # 度
        
        # 調試信息
        self.logger.info(
            "A4 位置補償計算",
            serving_elevation=serving_elevation,
            target_elevation=target_elevation,
            elevation_diff=elevation_diff
        )
        
        # 修正：限制仰角差異在合理範圍內 (±10度) 並使用更保守的補償係數
        elevation_diff = max(-10.0, min(10.0, elevation_diff))
        geometric_compensation_km = elevation_diff * 1.0  # 每度仰角差異約1km等效距離 (更保守)
        
        # 最終限制補償範圍在合理範圍內 (±10km)
        effective_delta_s = max(-10.0, min(10.0, geometric_compensation_km))
        delta_s = effective_delta_s * 1000  # 轉換為米
        
        # 調試信息
        self.logger.info(
            "A4 位置補償結果",
            geometric_compensation_km=geometric_compensation_km,
            effective_delta_s=effective_delta_s,
            delta_s=delta_s
        )
        
        # 計算時間補償項 ΔT (基於信號傳播時間差)
        c = 299792458  # 光速 m/s
        delta_t = (delta_s / c) * 1000  # 轉換為毫秒
        
        # 多普勒修正
        doppler_correction = self._calculate_doppler_correction(
            serving_pos, target_pos, ue_pos
        )
        
        return PositionCompensation(
            delta_s=delta_s,
            delta_t=delta_t,
            ue_position=ue_pos,
            satellite_position=serving_pos,
            target_satellite_position=target_pos,
            doppler_correction=doppler_correction
        )
        
    def _calculate_elevation_angle(
        self, 
        satellite_pos: SatellitePosition, 
        observer_pos: Position
    ) -> float:
        """計算衛星仰角"""
        try:
            # 簡化計算 - 基於地面距離和衛星高度
            distance = self.orbit_engine.calculate_distance(satellite_pos, observer_pos)
            satellite_altitude = satellite_pos.altitude or 550.0  # Starlink 高度 (km)
            
            # 使用簡化的幾何計算仰角
            # elevation = arctan(height / ground_distance)
            # 假設地面距離約等於總距離 (對於 LEO 衛星這是合理近似)
            if distance > 0:
                angle_rad = math.atan(satellite_altitude / distance)
                elevation = math.degrees(angle_rad)
                # 確保仰角在合理範圍內 (0-90度)
                return max(0.0, min(90.0, elevation))
            else:
                return 90.0  # 衛星正上方
            
        except Exception as e:
            self.logger.warning(f"仰角計算失敗: {e}")
            return 45.0  # 默認仰角
            
    def _calculate_doppler_correction(
        self,
        serving_pos: SatellitePosition,
        target_pos: SatellitePosition,
        ue_pos: Position
    ) -> float:
        """計算多普勒修正"""
        try:
            # 簡化實現 - 基於相對速度
            velocity_diff = math.sqrt(
                (target_pos.velocity_x - serving_pos.velocity_x)**2 +
                (target_pos.velocity_y - serving_pos.velocity_y)**2 +
                (target_pos.velocity_z - serving_pos.velocity_z)**2
            )
            
            # 多普勒頻移估算
            c = 299792458  # 光速
            frequency = 12e9  # 12 GHz
            doppler_shift = (velocity_diff * 1000 / c) * frequency
            
            return doppler_shift
            
        except:
            return 0.0
            
    async def _calculate_visibility_windows(
        self,
        satellite_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """計算衛星可見性窗口"""
        try:
            windows = []
            current = start_time
            interval = timedelta(minutes=5)
            
            while current < end_time:
                sat_pos = self.orbit_engine.calculate_satellite_position(
                    satellite_id, 
                    current.timestamp()
                )
                
                if sat_pos:
                    # 簡化判斷：高度 > 10 度認為可見
                    elevation = self._calculate_elevation_angle(
                        sat_pos,
                        Position(x=0, y=0, z=0, latitude=25.0, longitude=121.0)
                    )
                    
                    if elevation > 10:
                        # 找到可見窗口的開始和結束
                        window_start = current
                        window_end = current + interval
                        
                        # 簡化實現：假設每個窗口持續 10 分鐘
                        windows.append((window_start, window_start + timedelta(minutes=10)))
                        
                        current += timedelta(minutes=15)  # 跳過一段時間
                    else:
                        current += interval
                else:
                    current += interval
                    
            return windows
            
        except Exception as e:
            self.logger.error("可見性窗口計算失敗", satellite_id=satellite_id, error=str(e))
            return []
            
    async def _sib19_lifecycle_manager(self) -> None:
        """SIB19 生命週期管理"""
        while True:
            try:
                await asyncio.sleep(self.update_interval_minutes * 60)
                
                if self.current_sib19:
                    current_time = datetime.now(timezone.utc)
                    time_to_expiry = (self.current_sib19.expiry_time - current_time).total_seconds() / 3600
                    
                    # 檢查是否需要更新
                    if time_to_expiry <= self.expiry_warning_hours:
                        self.logger.info(
                            "SIB19 即將過期，準備更新",
                            current_id=self.current_sib19.broadcast_id,
                            time_to_expiry_hours=time_to_expiry
                        )
                        
                        # 生成新的 SIB19
                        if self.current_sib19.reference_location:
                            center = Position(
                                x=0, y=0, z=0,
                                latitude=self.current_sib19.reference_location.latitude,
                                longitude=self.current_sib19.reference_location.longitude,
                                altitude=self.current_sib19.reference_location.altitude
                            )
                            await self.generate_sib19_broadcast(center)
                            
            except Exception as e:
                self.logger.error("SIB19 生命週期管理異常", error=str(e))