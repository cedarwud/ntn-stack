# 🛰️ 共享數據模型
"""
Shared Data Models - Phase 1系統共享數據結構
功能: 定義通用數據模型，確保階段間數據一致性
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class ConstellationType(Enum):
    """星座類型"""
    STARLINK = "starlink"
    ONEWEB = "oneweb"
    PLANET = "planet"
    SPIRE = "spire"
    OTHER = "other"

class EventType(Enum):
    """3GPP事件類型"""
    A4 = "A4"  # 鄰近衛星信號優於門檻
    A5 = "A5"  # 服務衛星劣化且鄰近衛星良好
    D2 = "D2"  # LEO衛星距離優化換手

@dataclass
class CoordinatePoint:
    """座標點"""
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    
    def __str__(self):
        return f"({self.latitude:.4f}°N, {self.longitude:.4f}°E, {self.altitude_m}m)"

@dataclass
class SatelliteBasicInfo:
    """衛星基本信息"""
    satellite_id: str
    satellite_name: str
    constellation: ConstellationType
    norad_id: Optional[int] = None
    
    def __str__(self):
        return f"{self.constellation.value.upper()}_{self.satellite_id}"

@dataclass
class TLEParameters:
    """TLE軌道參數"""
    line1: str
    line2: str
    epoch: datetime
    
    # 軌道要素
    inclination_deg: float
    raan_deg: float
    eccentricity: float
    arg_perigee_deg: float
    mean_anomaly_deg: float
    mean_motion_revs_per_day: float
    
    # 計算參數
    semi_major_axis_km: float
    orbital_period_minutes: float
    apogee_altitude_km: float
    perigee_altitude_km: float

@dataclass
class SatellitePosition:
    """衛星位置數據"""
    timestamp: datetime
    satellite_id: str
    
    # 地理座標
    latitude_deg: float
    longitude_deg: float
    altitude_km: float
    
    # 觀測者相對位置
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    
    # 運動參數
    velocity_km_s: float
    
    def is_visible(self, min_elevation_deg: float = 5.0) -> bool:
        """檢查是否可見"""
        return self.elevation_deg >= min_elevation_deg

@dataclass
class SignalCharacteristics:
    """信號特性"""
    rsrp_dbm: float
    rsrq_db: float
    sinr_db: float
    path_loss_db: float
    doppler_shift_hz: float
    propagation_delay_ms: float

@dataclass
class SatelliteState:
    """衛星狀態 (位置+信號)"""
    basic_info: SatelliteBasicInfo
    position: SatellitePosition
    signal: SignalCharacteristics
    
    @property
    def satellite_id(self) -> str:
        return self.basic_info.satellite_id
    
    @property
    def constellation(self) -> ConstellationType:
        return self.basic_info.constellation

@dataclass
class FilterScore:
    """篩選評分"""
    satellite_id: str
    constellation: ConstellationType
    total_score: float
    
    # 分項評分
    geographic_relevance: float
    orbital_characteristics: float
    signal_quality: float
    temporal_distribution: float
    
    # 評分詳情
    scoring_details: Dict[str, Any]
    is_selected: bool

@dataclass
class HandoverEventData:
    """換手事件數據"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    
    serving_satellite: SatelliteState
    neighbor_satellite: SatelliteState
    
    trigger_conditions: Dict[str, float]
    confidence_score: float
    handover_recommended: bool

@dataclass
class VisibilityMetrics:
    """可見性指標"""
    timestamp: datetime
    constellation: ConstellationType
    
    total_satellites_in_pool: int
    visible_satellites_count: int
    meets_target_range: bool
    
    target_min: int
    target_max: int
    
    average_elevation: float
    average_rsrp: float

@dataclass
class PoolSolution:
    """衛星池解決方案"""
    solution_id: str
    timestamp: datetime
    
    starlink_satellites: List[str]
    oneweb_satellites: List[str]
    
    # 評估指標
    total_cost: float
    visibility_compliance: float
    temporal_distribution: float
    signal_quality: float
    
    # 約束滿足
    constraints_satisfied: Dict[str, bool]
    
    def get_total_count(self) -> int:
        return len(self.starlink_satellites) + len(self.oneweb_satellites)
    
    def get_constellation_count(self, constellation: ConstellationType) -> int:
        if constellation == ConstellationType.STARLINK:
            return len(self.starlink_satellites)
        elif constellation == ConstellationType.ONEWEB:
            return len(self.oneweb_satellites)
        else:
            return 0

@dataclass
class PhaseExecutionResult:
    """階段執行結果"""
    phase_name: str
    stage_name: str
    execution_time: datetime
    duration_seconds: float
    
    input_count: int
    output_count: int
    success: bool
    
    statistics: Dict[str, Any]
    output_path: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class SystemConfiguration:
    """系統配置"""
    observer_location: CoordinatePoint
    
    # 目標規格
    starlink_target_visible: tuple  # (min, max)
    oneweb_target_visible: tuple    # (min, max)
    
    # 門檻值
    starlink_elevation_threshold: float
    oneweb_elevation_threshold: float
    
    # 時間參數
    simulation_duration_minutes: int
    time_resolution_seconds: int
    
    # 3GPP事件門檻
    a4_threshold_dbm: float
    a5_serving_threshold_dbm: float
    a5_neighbor_threshold_dbm: float
    d2_distance_threshold_km: float

# 預設配置
def create_ntpu_config() -> SystemConfiguration:
    """創建NTPU觀測點配置"""
    return SystemConfiguration(
        observer_location=CoordinatePoint(24.9441667, 121.3713889, 50.0),
        starlink_target_visible=(10, 15),
        oneweb_target_visible=(3, 6),
        starlink_elevation_threshold=5.0,
        oneweb_elevation_threshold=10.0,
        simulation_duration_minutes=200,
        time_resolution_seconds=30,
        a4_threshold_dbm=-100.0,
        a5_serving_threshold_dbm=-110.0,
        a5_neighbor_threshold_dbm=-100.0,
        d2_distance_threshold_km=5000.0
    )

# 常用函數
def create_satellite_id(constellation: ConstellationType, norad_id: int) -> str:
    """創建標準化衛星ID"""
    return f"{constellation.value}_{norad_id}"

def parse_constellation_from_id(satellite_id: str) -> ConstellationType:
    """從衛星ID解析星座類型"""
    if satellite_id.startswith("starlink_"):
        return ConstellationType.STARLINK
    elif satellite_id.startswith("oneweb_"):
        return ConstellationType.ONEWEB
    elif satellite_id.startswith("planet_"):
        return ConstellationType.PLANET
    elif satellite_id.startswith("spire_"):
        return ConstellationType.SPIRE
    else:
        return ConstellationType.OTHER