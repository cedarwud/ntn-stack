#!/usr/bin/env python3
"""
測量事件服務模組 - 統一改進主準則 API 實現

實現統一的測量事件服務，支援：
1. A4 - 信號強度測量事件
2. D1 - 雙重距離測量事件  
3. D2 - 移動參考位置距離事件
4. T1 - 時間條件測量事件

核心特點：
- 基於真實 SGP4 軌道計算
- 整合 SIB19 統一基礎平台
- 支援事件特定的測量邏輯
- 提供實時數據和模擬功能
"""

import asyncio
import logging
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog

from .orbit_calculation_engine import (
    OrbitCalculationEngine, SatellitePosition, Position, 
    SatelliteConfig, SignalModel
)
from .sib19_unified_platform import (
    SIB19UnifiedPlatform, PositionCompensation, ReferenceLocation,
    TimeCorrection, NeighborCellConfig
)
from .tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)


class EventType(Enum):
    """測量事件類型"""
    A4 = "A4"  # 信號強度測量事件
    D1 = "D1"  # 雙重距離測量事件
    D2 = "D2"  # 移動參考位置距離事件
    T1 = "T1"  # 時間條件測量事件


class TriggerState(Enum):
    """觸發狀態"""
    IDLE = "idle"                    # 空閒
    APPROACHING = "approaching"      # 接近觸發
    TRIGGERED = "triggered"          # 已觸發
    HYSTERESIS = "hysteresis"       # 遲滯狀態
    

@dataclass
class EventParameters:
    """測量事件參數基類"""
    event_type: EventType = EventType.A4  # 默認值，會在 __post_init__ 中被覆蓋
    time_to_trigger: int = 160  # ms
    

@dataclass
class A4Parameters(EventParameters):
    """A4 事件參數"""
    a4_threshold: float = -80.0     # dBm
    hysteresis: float = 3.0         # dB
    
    def __post_init__(self):
        self.event_type = EventType.A4


@dataclass
class D1Parameters(EventParameters):
    """D1 事件參數"""
    thresh1: float = 10000.0        # 門檻值1 (m)
    thresh2: float = 5000.0         # 門檻值2 (m)
    hysteresis: float = 500.0       # 遲滯 (m)
    
    def __post_init__(self):
        self.event_type = EventType.D1


@dataclass
class D2Parameters(EventParameters):
    """D2 事件參數"""
    thresh1: float = 800000.0       # 門檻值1 - 衛星距離 (m)
    thresh2: float = 30000.0        # 門檻值2 - 地面距離 (m)  
    hysteresis: float = 500.0       # 遲滯 (m)
    
    def __post_init__(self):
        self.event_type = EventType.D2


@dataclass
class T1Parameters(EventParameters):
    """T1 事件參數"""
    t1_threshold: float = 300.0     # 時間門檻 (秒)
    duration: float = 60.0          # 持續時間 (秒)
    
    def __post_init__(self):
        self.event_type = EventType.T1


@dataclass
class MeasurementResult:
    """測量結果"""
    event_type: EventType
    timestamp: datetime
    trigger_state: TriggerState
    
    # 事件特定數據
    measurement_values: Dict[str, float]
    satellite_positions: Dict[str, SatellitePosition]
    
    # SIB19 相關數據
    sib19_data: Optional[Dict[str, Any]] = None
    
    # 觸發條件檢查
    trigger_condition_met: bool = False
    trigger_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationScenario:
    """模擬場景"""
    # 必需字段 (無默認值)
    scenario_name: str
    ue_position: Position
    event_parameters: Union[A4Parameters, D1Parameters, D2Parameters, T1Parameters]
    
    # 可選字段 (有默認值)
    duration_minutes: int = 60
    sample_interval_seconds: int = 5
    target_satellites: List[str] = field(default_factory=list)
    

class MeasurementEventService:
    """
    測量事件服務 - 統一 API 實現
    
    功能：
    1. 統一的測量事件處理
    2. 基於 SIB19 的真實軌道計算
    3. 事件特定的觸發邏輯
    4. 實時數據和模擬支援
    """
    
    def __init__(
        self,
        orbit_engine: OrbitCalculationEngine,
        sib19_platform: SIB19UnifiedPlatform,
        tle_manager: TLEDataManager
    ):
        """
        初始化測量事件服務
        
        Args:
            orbit_engine: 軌道計算引擎
            sib19_platform: SIB19 統一平台
            tle_manager: TLE 數據管理器
        """
        self.logger = structlog.get_logger(__name__)
        self.orbit_engine = orbit_engine
        self.sib19_platform = sib19_platform
        self.tle_manager = tle_manager
        
        # 事件狀態管理
        self.event_states: Dict[str, TriggerState] = {}
        self.last_measurements: Dict[str, MeasurementResult] = {}
        
        # 參數驗證器
        self.parameter_validators = {
            EventType.A4: self._validate_a4_parameters,
            EventType.D1: self._validate_d1_parameters,
            EventType.D2: self._validate_d2_parameters,
            EventType.T1: self._validate_t1_parameters
        }
        
        # 測量處理器
        self.measurement_processors = {
            EventType.A4: self._process_a4_measurement,
            EventType.D1: self._process_d1_measurement,
            EventType.D2: self._process_d2_measurement,
            EventType.T1: self._process_t1_measurement
        }
        
        self.logger.info("測量事件服務初始化完成")
        
    async def get_real_time_measurement_data(
        self,
        event_type: EventType,
        ue_position: Position,
        event_params: Union[A4Parameters, D1Parameters, D2Parameters, T1Parameters]
    ) -> Optional[MeasurementResult]:
        """
        獲取實時測量數據
        
        Args:
            event_type: 事件類型
            ue_position: UE 位置
            event_params: 事件參數
            
        Returns:
            測量結果或 None
        """
        try:
            # 參數驗證
            validation_result = await self._validate_parameters(event_type, event_params)
            if not validation_result["valid"]:
                self.logger.error(
                    "事件參數驗證失敗",
                    event_type=event_type.value,
                    errors=validation_result["errors"]
                )
                return None
                
            # 獲取鄰居細胞配置
            neighbor_cells = await self.sib19_platform.get_neighbor_cell_configs()
            if not neighbor_cells:
                self.logger.warning("無可用的鄰居細胞配置")
                
            # 處理測量
            processor = self.measurement_processors[event_type]
            result = await processor(ue_position, event_params, neighbor_cells)
            
            if result:
                # 更新狀態
                event_key = f"{event_type.value}_{ue_position.latitude}_{ue_position.longitude}"
                self.event_states[event_key] = result.trigger_state
                self.last_measurements[event_key] = result
                
            return result
            
        except Exception as e:
            self.logger.error(
                "實時測量數據獲取失敗",
                event_type=event_type.value,
                error=str(e)
            )
            return None
            
    async def simulate_measurement_event(
        self,
        scenario: SimulationScenario
    ) -> Dict[str, Any]:
        """
        模擬測量事件
        
        Args:
            scenario: 模擬場景
            
        Returns:
            模擬結果
        """
        try:
            self.logger.info(
                "開始測量事件模擬",
                scenario_name=scenario.scenario_name,
                event_type=scenario.event_parameters.event_type.value,
                duration_minutes=scenario.duration_minutes
            )
            
            simulation_results = []
            current_time = datetime.now(timezone.utc)
            end_time = current_time + timedelta(minutes=scenario.duration_minutes)
            
            sample_interval = timedelta(seconds=scenario.sample_interval_seconds)
            
            while current_time < end_time:
                # 獲取當前時刻的測量數據
                result = await self.get_real_time_measurement_data(
                    scenario.event_parameters.event_type,
                    scenario.ue_position,
                    scenario.event_parameters
                )
                
                if result:
                    simulation_results.append({
                        "timestamp": current_time.isoformat(),
                        "trigger_state": result.trigger_state.value,
                        "trigger_condition_met": result.trigger_condition_met,
                        "measurement_values": result.measurement_values,
                        "trigger_details": result.trigger_details
                    })
                    
                current_time += sample_interval
                
                # 模擬延遲
                await asyncio.sleep(0.01)  # 10ms 延遲，避免過快執行
                
            # 生成統計
            stats = self._generate_simulation_statistics(simulation_results)
            
            return {
                "scenario": {
                    "name": scenario.scenario_name,
                    "event_type": scenario.event_parameters.event_type.value,
                    "ue_position": {
                        "latitude": scenario.ue_position.latitude,
                        "longitude": scenario.ue_position.longitude,
                        "altitude": scenario.ue_position.altitude
                    },
                    "duration_minutes": scenario.duration_minutes,
                    "sample_interval_seconds": scenario.sample_interval_seconds
                },
                "results": simulation_results,
                "statistics": stats,
                "summary": {
                    "total_samples": len(simulation_results),
                    "trigger_events": len([r for r in simulation_results if r["trigger_condition_met"]]),
                    "trigger_rate": len([r for r in simulation_results if r["trigger_condition_met"]]) / max(1, len(simulation_results))
                }
            }
            
        except Exception as e:
            self.logger.error(
                "測量事件模擬失敗",
                scenario_name=scenario.scenario_name,
                error=str(e)
            )
            return {"error": str(e)}
            
    async def _process_a4_measurement(
        self,
        ue_position: Position,
        params: A4Parameters,
        neighbor_cells: List[NeighborCellConfig]
    ) -> Optional[MeasurementResult]:
        """處理 A4 事件測量"""
        try:
            current_time = datetime.now(timezone.utc)
            measurement_values = {}
            satellite_positions = {}
            
            # 獲取主服務衛星 (假設第一個鄰居細胞)
            if not neighbor_cells:
                return None
                
            serving_cell = neighbor_cells[0]
            serving_satellite = serving_cell.satellite_id
            
            # 計算服務衛星位置和信號強度
            serving_pos = self.orbit_engine.calculate_satellite_position(
                serving_satellite, 
                current_time.timestamp()
            )
            
            if not serving_pos:
                return None
                
            satellite_positions[serving_satellite] = serving_pos
            
            # 獲取衛星配置
            serving_config = SatelliteConfig(
                satellite_id=serving_satellite,
                name=serving_satellite,
                transmit_power_dbm=30.0,
                frequency_mhz=serving_cell.carrier_frequency
            )
            
            serving_distance = self.orbit_engine.calculate_distance(serving_pos, ue_position)
            serving_rsrp = self.orbit_engine.calculate_signal_strength(
                serving_distance, 
                serving_config,
                SignalModel.ATMOSPHERIC
            )
            
            measurement_values["serving_rsrp"] = serving_rsrp
            measurement_values["serving_distance"] = serving_distance
            
            # 處理鄰居衛星
            best_neighbor_rsrp = float('-inf')
            best_neighbor_id = None
            
            for neighbor_cell in neighbor_cells[1:]:  # 跳過服務衛星
                neighbor_satellite = neighbor_cell.satellite_id
                
                neighbor_pos = self.orbit_engine.calculate_satellite_position(
                    neighbor_satellite,
                    current_time.timestamp()
                )
                
                if neighbor_pos:
                    satellite_positions[neighbor_satellite] = neighbor_pos
                    
                    neighbor_config = SatelliteConfig(
                        satellite_id=neighbor_satellite,
                        name=neighbor_satellite,
                        transmit_power_dbm=30.0,
                        frequency_mhz=neighbor_cell.carrier_frequency
                    )
                    
                    neighbor_distance = self.orbit_engine.calculate_distance(neighbor_pos, ue_position)
                    neighbor_rsrp = self.orbit_engine.calculate_signal_strength(
                        neighbor_distance,
                        neighbor_config,
                        SignalModel.ATMOSPHERIC
                    )
                    
                    measurement_values[f"{neighbor_satellite}_rsrp"] = neighbor_rsrp
                    measurement_values[f"{neighbor_satellite}_distance"] = neighbor_distance
                    
                    if neighbor_rsrp > best_neighbor_rsrp:
                        best_neighbor_rsrp = neighbor_rsrp
                        best_neighbor_id = neighbor_satellite
                        
            # A4 觸發條件檢查 (包含 SIB19 位置補償)
            trigger_condition_met = False
            trigger_details = {}
            
            if best_neighbor_id:
                # 獲取位置補償
                compensation = await self.sib19_platform.get_a4_position_compensation(
                    ue_position, serving_satellite, best_neighbor_id
                )
                
                if compensation:
                    # 修正的 A4 觸發條件: PT(t) > PS(t) + HOM + ΔS,T(t)
                    compensated_threshold = params.a4_threshold + params.hysteresis + (compensation.delta_s / 1000.0)
                    
                    trigger_condition_met = best_neighbor_rsrp > compensated_threshold
                    
                    trigger_details = {
                        "serving_rsrp": serving_rsrp,
                        "best_neighbor_rsrp": best_neighbor_rsrp,
                        "best_neighbor_id": best_neighbor_id,
                        "original_threshold": params.a4_threshold + params.hysteresis,
                        "position_compensation_m": compensation.delta_s,
                        "time_compensation_ms": compensation.delta_t,
                        "compensated_threshold": compensated_threshold,
                        "condition_met": trigger_condition_met
                    }
                    
                    measurement_values["position_compensation"] = compensation.delta_s
                    measurement_values["time_compensation"] = compensation.delta_t
                else:
                    # 無補償的標準 A4 條件
                    standard_threshold = params.a4_threshold + params.hysteresis
                    trigger_condition_met = best_neighbor_rsrp > standard_threshold
                    
                    trigger_details = {
                        "serving_rsrp": serving_rsrp,
                        "best_neighbor_rsrp": best_neighbor_rsrp,
                        "best_neighbor_id": best_neighbor_id,
                        "threshold": standard_threshold,
                        "condition_met": trigger_condition_met,
                        "compensation_available": False
                    }
                    
            # 確定觸發狀態
            trigger_state = TriggerState.TRIGGERED if trigger_condition_met else TriggerState.IDLE
            
            return MeasurementResult(
                event_type=EventType.A4,
                timestamp=current_time,
                trigger_state=trigger_state,
                measurement_values=measurement_values,
                satellite_positions=satellite_positions,
                trigger_condition_met=trigger_condition_met,
                trigger_details=trigger_details,
                sib19_data={
                    "neighbor_cells_count": len(neighbor_cells),
                    "compensation_enabled": compensation is not None if 'compensation' in locals() else False
                }
            )
            
        except Exception as e:
            self.logger.error("A4 測量處理失敗", error=str(e))
            return None
            
    async def _process_d1_measurement(
        self,
        ue_position: Position,
        params: D1Parameters,
        neighbor_cells: List[NeighborCellConfig]
    ) -> Optional[MeasurementResult]:
        """處理 D1 事件測量"""
        try:
            current_time = datetime.now(timezone.utc)
            measurement_values = {}
            satellite_positions = {}
            
            # 獲取 SIB19 固定參考位置
            reference_location = await self.sib19_platform.get_d1_reference_location()
            
            if not reference_location:
                # 使用默認參考位置
                reference_position = Position(
                    x=0, y=0, z=0,
                    latitude=25.0330,   # 台北
                    longitude=121.5654,
                    altitude=0.0
                )
            else:
                reference_position = Position(
                    x=0, y=0, z=0,
                    latitude=reference_location.latitude,
                    longitude=reference_location.longitude,
                    altitude=reference_location.altitude or 0.0
                )
                
            # 計算服務衛星距離 (Ml1)
            if neighbor_cells:
                serving_satellite = neighbor_cells[0].satellite_id
                serving_pos = self.orbit_engine.calculate_satellite_position(
                    serving_satellite,
                    current_time.timestamp()
                )
                
                if serving_pos:
                    satellite_positions[serving_satellite] = serving_pos
                    ml1_distance = self.orbit_engine.calculate_distance(serving_pos, ue_position) * 1000  # 轉換為米
                    measurement_values["ml1_distance"] = ml1_distance
                    
            # 計算 UE 到參考位置距離 (Ml2)
            ml2_distance = self._calculate_ground_distance(ue_position, reference_position)
            measurement_values["ml2_distance"] = ml2_distance
            measurement_values["reference_latitude"] = reference_position.latitude
            measurement_values["reference_longitude"] = reference_position.longitude
            
            # D1 觸發條件檢查
            # 進入: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2
            # 離開: Ml1 + Hys < Thresh1 OR Ml2 - Hys > Thresh2
            
            trigger_condition_met = False
            trigger_details = {}
            
            if "ml1_distance" in measurement_values:
                condition1 = ml1_distance - params.hysteresis > params.thresh1
                condition2 = ml2_distance + params.hysteresis < params.thresh2
                
                trigger_condition_met = condition1 and condition2
                
                trigger_details = {
                    "ml1_distance": ml1_distance,
                    "ml2_distance": ml2_distance,
                    "thresh1": params.thresh1,
                    "thresh2": params.thresh2,
                    "hysteresis": params.hysteresis,
                    "condition1_met": condition1,
                    "condition2_met": condition2,
                    "overall_condition_met": trigger_condition_met
                }
                
            trigger_state = TriggerState.TRIGGERED if trigger_condition_met else TriggerState.IDLE
            
            return MeasurementResult(
                event_type=EventType.D1,
                timestamp=current_time,
                trigger_state=trigger_state,
                measurement_values=measurement_values,
                satellite_positions=satellite_positions,
                trigger_condition_met=trigger_condition_met,
                trigger_details=trigger_details,
                sib19_data={
                    "reference_type": "static",
                    "reference_location": {
                        "latitude": reference_position.latitude,
                        "longitude": reference_position.longitude,
                        "altitude": reference_position.altitude
                    }
                }
            )
            
        except Exception as e:
            self.logger.error("D1 測量處理失敗", error=str(e))
            return None
            
    async def _process_d2_measurement(
        self,
        ue_position: Position,
        params: D2Parameters,
        neighbor_cells: List[NeighborCellConfig]
    ) -> Optional[MeasurementResult]:
        """處理 D2 事件測量"""
        try:
            current_time = datetime.now(timezone.utc)
            measurement_values = {}
            satellite_positions = {}
            
            # 獲取 SIB19 動態參考位置 (衛星軌道)
            moving_reference = await self.sib19_platform.get_d2_moving_reference_location()
            
            if not moving_reference or not moving_reference.satellite_id:
                return None
                
            # 計算參考衛星位置
            reference_satellite = moving_reference.satellite_id
            reference_pos = self.orbit_engine.calculate_satellite_position(
                reference_satellite,
                current_time.timestamp()
            )
            
            if not reference_pos:
                return None
                
            satellite_positions[reference_satellite] = reference_pos
            
            # 計算服務衛星到參考衛星距離 (衛星間距離)
            if neighbor_cells:
                serving_satellite = neighbor_cells[0].satellite_id
                serving_pos = self.orbit_engine.calculate_satellite_position(
                    serving_satellite,
                    current_time.timestamp()
                )
                
                if serving_pos:
                    satellite_positions[serving_satellite] = serving_pos
                    
                    # 衛星間距離 (應 > Thresh1)
                    satellite_distance = self.orbit_engine.calculate_distance(serving_pos, reference_pos) * 1000
                    measurement_values["satellite_distance"] = satellite_distance
                    
            # 計算 UE 到參考衛星地面投影點距離 (應 < Thresh2)
            # 參考衛星的地面投影點
            reference_ground_position = Position(
                x=0, y=0, z=0,
                latitude=reference_pos.latitude,
                longitude=reference_pos.longitude,
                altitude=0.0
            )
            
            ground_distance = self._calculate_ground_distance(ue_position, reference_ground_position)
            measurement_values["ground_distance"] = ground_distance
            measurement_values["reference_satellite_lat"] = reference_pos.latitude
            measurement_values["reference_satellite_lon"] = reference_pos.longitude
            measurement_values["reference_satellite_alt"] = reference_pos.altitude
            
            # D2 觸發條件檢查
            # 服務衛星距離 > Thresh1 且 目標衛星地面距離 < Thresh2
            trigger_condition_met = False
            trigger_details = {}
            
            if "satellite_distance" in measurement_values:
                condition1 = satellite_distance > params.thresh1
                condition2 = ground_distance < params.thresh2
                
                trigger_condition_met = condition1 and condition2
                
                trigger_details = {
                    "satellite_distance": satellite_distance,
                    "ground_distance": ground_distance,
                    "thresh1": params.thresh1,
                    "thresh2": params.thresh2,
                    "hysteresis": params.hysteresis,
                    "condition1_met": condition1,
                    "condition2_met": condition2,
                    "overall_condition_met": trigger_condition_met,
                    "reference_satellite": reference_satellite
                }
                
            trigger_state = TriggerState.TRIGGERED if trigger_condition_met else TriggerState.IDLE
            
            return MeasurementResult(
                event_type=EventType.D2,
                timestamp=current_time,
                trigger_state=trigger_state,
                measurement_values=measurement_values,
                satellite_positions=satellite_positions,
                trigger_condition_met=trigger_condition_met,
                trigger_details=trigger_details,
                sib19_data={
                    "reference_type": "dynamic",
                    "reference_satellite": reference_satellite,
                    "orbital_period_minutes": reference_pos.orbital_period
                }
            )
            
        except Exception as e:
            self.logger.error("D2 測量處理失敗", error=str(e))
            return None
            
    async def _process_t1_measurement(
        self,
        ue_position: Position,
        params: T1Parameters,
        neighbor_cells: List[NeighborCellConfig]
    ) -> Optional[MeasurementResult]:
        """處理 T1 事件測量"""
        try:
            current_time = datetime.now(timezone.utc)
            measurement_values = {}
            satellite_positions = {}
            
            # 獲取 SIB19 時間框架
            time_correction = await self.sib19_platform.get_t1_time_frame()
            
            if not time_correction:
                return None
                
            # 計算時間相關參數
            epoch_time = time_correction.epoch_time
            t_service = time_correction.t_service
            
            # 計算自 epoch 以來的時間
            elapsed_time = (current_time - epoch_time).total_seconds()
            measurement_values["elapsed_time"] = elapsed_time
            measurement_values["epoch_time"] = epoch_time.isoformat()
            measurement_values["t_service"] = t_service
            measurement_values["time_sync_accuracy_ms"] = time_correction.current_accuracy_ms
            
            # T1 觸發條件檢查
            # 當經過的時間超過設定的門檻值
            trigger_condition_met = elapsed_time > params.t1_threshold
            
            # 如果觸發，檢查持續時間
            remaining_service_time = max(0, t_service - elapsed_time)
            duration_met = remaining_service_time >= params.duration
            
            trigger_details = {
                "elapsed_time": elapsed_time,
                "t1_threshold": params.t1_threshold,
                "required_duration": params.duration,
                "remaining_service_time": remaining_service_time,
                "threshold_condition_met": trigger_condition_met,
                "duration_condition_met": duration_met,
                "overall_condition_met": trigger_condition_met and duration_met,
                "gnss_time_offset_ms": time_correction.gnss_time_offset,
                "sync_accuracy_ms": time_correction.current_accuracy_ms
            }
            
            # 最終觸發條件
            final_trigger = trigger_condition_met and duration_met
            
            trigger_state = TriggerState.TRIGGERED if final_trigger else TriggerState.IDLE
            
            return MeasurementResult(
                event_type=EventType.T1,
                timestamp=current_time,
                trigger_state=trigger_state,
                measurement_values=measurement_values,
                satellite_positions=satellite_positions,
                trigger_condition_met=final_trigger,
                trigger_details=trigger_details,
                sib19_data={
                    "time_frame_type": "absolute",
                    "epoch_time": epoch_time.isoformat(),
                    "service_duration": t_service,
                    "sync_accuracy_requirement_ms": time_correction.sync_accuracy_ms
                }
            )
            
        except Exception as e:
            self.logger.error("T1 測量處理失敗", error=str(e))
            return None
            
    def _calculate_ground_distance(self, pos1: Position, pos2: Position) -> float:
        """計算兩點間地面距離 (米)"""
        try:
            # 使用 Haversine 公式計算球面距離
            lat1, lon1 = math.radians(pos1.latitude), math.radians(pos1.longitude)
            lat2, lon2 = math.radians(pos2.latitude), math.radians(pos2.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = (math.sin(dlat/2)**2 + 
                 math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            
            # 地球半徑 (米)
            earth_radius = 6371000
            
            distance = earth_radius * c
            return distance
            
        except Exception:
            return float('inf')
            
    def _generate_simulation_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模擬統計"""
        if not results:
            return {}
            
        trigger_events = [r for r in results if r["trigger_condition_met"]]
        
        stats = {
            "total_samples": len(results),
            "trigger_events": len(trigger_events),
            "trigger_rate": len(trigger_events) / len(results),
            "states_distribution": {}
        }
        
        # 狀態分佈統計
        state_counts = {}
        for result in results:
            state = result["trigger_state"]
            state_counts[state] = state_counts.get(state, 0) + 1
            
        stats["states_distribution"] = {
            state: count / len(results) for state, count in state_counts.items()
        }
        
        # 測量值統計
        if results[0]["measurement_values"]:
            measurement_stats = {}
            for key in results[0]["measurement_values"].keys():
                values = [r["measurement_values"].get(key, 0) for r in results if key in r["measurement_values"]]
                if values:
                    measurement_stats[key] = {
                        "mean": np.mean(values),
                        "std": np.std(values),
                        "min": np.min(values),
                        "max": np.max(values)
                    }
            stats["measurement_statistics"] = measurement_stats
            
        return stats
        
    async def _validate_parameters(
        self, 
        event_type: EventType,
        params: Union[A4Parameters, D1Parameters, D2Parameters, T1Parameters]
    ) -> Dict[str, Any]:
        """驗證事件參數"""
        validator = self.parameter_validators.get(event_type)
        if validator:
            return validator(params)
        return {"valid": False, "errors": ["未支援的事件類型"]}
        
    def _validate_a4_parameters(self, params: A4Parameters) -> Dict[str, Any]:
        """驗證 A4 參數"""
        errors = []
        
        if not (-100 <= params.a4_threshold <= -40):
            errors.append("A4 門檻值應在 -100 到 -40 dBm 之間")
            
        if not (0 <= params.hysteresis <= 10):
            errors.append("遲滯值應在 0 到 10 dB 之間")
            
        if params.time_to_trigger not in [0, 40, 64, 80, 100, 128, 160, 256, 320, 480, 512, 640]:
            errors.append("觸發時間必須是 3GPP 標準值之一")
            
        return {"valid": len(errors) == 0, "errors": errors}
        
    def _validate_d1_parameters(self, params: D1Parameters) -> Dict[str, Any]:
        """驗證 D1 參數"""
        errors = []
        
        if not (50 <= params.thresh1 <= 50000):
            errors.append("Thresh1 應在 50 到 50000 米之間")
            
        if not (10 <= params.thresh2 <= 10000):
            errors.append("Thresh2 應在 10 到 10000 米之間")
            
        if not (1 <= params.hysteresis <= 1000):
            errors.append("遲滯值應在 1 到 1000 米之間")
            
        return {"valid": len(errors) == 0, "errors": errors}
        
    def _validate_d2_parameters(self, params: D2Parameters) -> Dict[str, Any]:
        """驗證 D2 參數"""
        errors = []
        
        if not (400000 <= params.thresh1 <= 2000000):
            errors.append("Thresh1 應在 400000 到 2000000 米之間")
            
        if not (100 <= params.thresh2 <= 50000):
            errors.append("Thresh2 應在 100 到 50000 米之間")
            
        if not (100 <= params.hysteresis <= 5000):
            errors.append("遲滯值應在 100 到 5000 米之間")
            
        return {"valid": len(errors) == 0, "errors": errors}
        
    def _validate_t1_parameters(self, params: T1Parameters) -> Dict[str, Any]:
        """驗證 T1 參數"""
        errors = []
        
        if not (1 <= params.t1_threshold <= 3600):
            errors.append("T1 門檻值應在 1 到 3600 秒之間")
            
        if not (1 <= params.duration <= 300):
            errors.append("持續時間應在 1 到 300 秒之間")
            
        return {"valid": len(errors) == 0, "errors": errors}