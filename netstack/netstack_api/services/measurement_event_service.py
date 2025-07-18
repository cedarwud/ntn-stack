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
                
                # Phase 2.1 改進：對於 D2 事件，即使沒有鄰居細胞配置也繼續執行
                if event_type != EventType.D2:
                    self.logger.error(f"{event_type.value} 事件需要鄰居細胞配置")
                    return None
                
            # 處理測量
            processor = self.measurement_processors[event_type]
            result = await processor(ue_position, event_params, neighbor_cells or [])
            
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
    
    async def _select_d2_reference_satellite(self, ue_position: Position) -> Optional[str]:
        """
        Phase 2.1 強化：D2 事件移動參考位置衛星選擇
        
        符合 3GPP TS 38.331 movingReferenceLocation 標準：
        1. 基於多因子評分系統選擇最佳參考衛星
        2. 考慮距離適合度、軌道穩定性、可見性持續時間
        3. 支援動態參考位置更新和切換優化
        4. 符合 D2 事件雙重距離條件要求
        """
        try:
            current_time = datetime.now(timezone.utc)
            timestamp = current_time.timestamp()
            available_satellites = []
            
            # 獲取所有可用衛星
            all_satellites = list(self.orbit_engine.sgp4_cache.keys())
            
            if len(all_satellites) < 2:
                self.logger.warning("可用衛星數量不足，無法執行 D2 測量")
                return None
            
            # 計算每顆衛星的適合度評分
            for satellite_id in all_satellites:
                sat_pos = self.orbit_engine.calculate_satellite_position(satellite_id, timestamp)
                if sat_pos:
                    distance = self.orbit_engine.calculate_distance(sat_pos, ue_position)
                    
                    # 計算適合度評分
                    score = await self._calculate_d2_reference_score(
                        satellite_id, sat_pos, ue_position, distance, current_time
                    )
                    
                    available_satellites.append({
                        'satellite_id': satellite_id,
                        'distance': distance,
                        'position': sat_pos,
                        'score': score,
                        'elevation': self._calculate_elevation_angle(sat_pos, ue_position)
                    })
            
            if not available_satellites:
                self.logger.warning("D2 事件：無可用衛星")
                return None
            
            # 過濾掉不符合基本條件的衛星
            qualified_satellites = [
                sat for sat in available_satellites 
                if sat['distance'] > 400 and sat['elevation'] > 10  # 最小距離和仰角要求
            ]
            
            if not qualified_satellites:
                # 如果沒有完全符合條件的，放寬條件
                qualified_satellites = [
                    sat for sat in available_satellites 
                    if sat['distance'] > 300  # 放寬距離要求
                ]
            
            if not qualified_satellites:
                qualified_satellites = available_satellites  # 最後備選
            
            # 按適合度評分排序，選擇最佳參考衛星
            qualified_satellites.sort(key=lambda x: x['score'], reverse=True)
            
            selected = qualified_satellites[0]
            self.logger.info(
                f"D2 事件選擇參考衛星: {selected['satellite_id']}, "
                f"距離: {selected['distance']:.1f}km, 評分: {selected['score']:.2f}, "
                f"仰角: {selected['elevation']:.1f}°"
            )
            return selected['satellite_id']
            
        except Exception as e:
            self.logger.error("D2 參考衛星選擇失敗", error=str(e))
            return None
    
    async def _calculate_d2_reference_score(
        self, 
        satellite_id: str, 
        sat_pos: SatellitePosition, 
        ue_position: Position,
        distance: float, 
        current_time: datetime
    ) -> float:
        """
        計算 D2 參考衛星適合度評分
        
        評分因子：
        1. 距離適合度 (60%) - 符合 D2 雙重距離條件的最佳距離
        2. 軌道穩定性 (25%) - 軌道預測準確性和數據新鮮度
        3. 可見性持續時間 (15%) - 長期可見性和仰角優勢
        """
        try:
            score = 0.0
            
            # 1. 距離適合度評分 (60%)
            # D2 事件 Thresh1 默認值為 800km，最佳參考衛星距離應在此範圍
            optimal_distance = 600.0  # 600km 最佳距離
            distance_km = distance
            distance_deviation = abs(distance_km - optimal_distance)
            
            if distance_deviation <= 100:  # 500-700km 範圍
                distance_score = 1.0
            elif distance_deviation <= 200:  # 400-800km 範圍
                distance_score = 0.9 - (distance_deviation - 100) / 100 * 0.2
            elif distance_deviation <= 400:  # 200-1000km 範圍
                distance_score = 0.7 - (distance_deviation - 200) / 200 * 0.3
            else:
                distance_score = 0.4 - min(distance_deviation - 400, 600) / 600 * 0.4
                
            score += distance_score * 0.6
            
            # 2. 軌道穩定性評分 (25%)
            orbit_stability_score = 0.8  # 預設穩定性分數
            
            try:
                # 檢查未來軌道預測的一致性
                future_time = current_time.timestamp() + 600  # 10分鐘後
                future_pos = self.orbit_engine.calculate_satellite_position(satellite_id, future_time)
                if future_pos:
                    # 計算軌道運動的合理性
                    future_distance = self.orbit_engine.calculate_distance(future_pos, ue_position)
                    distance_change = abs(future_distance - distance_km)
                    
                    # 期望的距離變化應該合理（衛星運動速度約 7-8 km/s）
                    expected_change = 7.5 * 600 / 1000  # 約 4.5km 變化
                    if distance_change < expected_change * 2:  # 合理範圍內
                        orbit_stability_score = 0.95
                    else:
                        orbit_stability_score = 0.7
                else:
                    orbit_stability_score = 0.5
            except:
                orbit_stability_score = 0.6
                
            score += orbit_stability_score * 0.25
            
            # 3. 可見性持續時間評分 (15%)
            visibility_score = 0.8  # 預設可見性分數
            
            # 基於衛星高度和仰角估算可見性
            elevation = self._calculate_elevation_angle(sat_pos, ue_position)
            
            if elevation > 30:  # 高仰角，長期可見
                visibility_score = 0.95
            elif elevation > 15:  # 中等仰角
                visibility_score = 0.85
            elif elevation > 5:   # 低仰角
                visibility_score = 0.7
            else:  # 極低仰角，可能很快消失
                visibility_score = 0.4
                
            score += visibility_score * 0.15
            
            self.logger.debug(
                f"D2 參考衛星評分 {satellite_id}: "
                f"距離={distance_score:.2f}({distance_km:.0f}km), "
                f"軌道={orbit_stability_score:.2f}, "
                f"可見性={visibility_score:.2f}(仰角{elevation:.1f}°), "
                f"總分={score:.2f}"
            )
            
            return score
            
        except Exception as e:
            self.logger.warning(f"計算衛星評分失敗 {satellite_id}: {str(e)}")
            return 0.0
    
    def _calculate_elevation_angle(self, sat_pos: SatellitePosition, ue_position: Position) -> float:
        """
        計算衛星相對於 UE 的仰角
        
        Returns:
            仰角 (度)，範圍 0-90 度
        """
        try:
            import math
            
            # 地球半徑 (km)
            earth_radius = 6371.0
            
            # 將緯度經度轉換為弧度
            ue_lat_rad = math.radians(ue_position.latitude)
            ue_lon_rad = math.radians(ue_position.longitude)
            sat_lat_rad = math.radians(sat_pos.latitude)
            sat_lon_rad = math.radians(sat_pos.longitude)
            
            # 計算 UE 到衛星的直線距離
            distance_3d = self.orbit_engine.calculate_distance(sat_pos, ue_position)
            
            # 計算地面距離（大圓距離）
            dlat = sat_lat_rad - ue_lat_rad
            dlon = sat_lon_rad - ue_lon_rad
            a = math.sin(dlat/2)**2 + math.cos(ue_lat_rad) * math.cos(sat_lat_rad) * math.sin(dlon/2)**2
            ground_distance = 2 * earth_radius * math.asin(math.sqrt(a))
            
            # 衛星高度（相對於地面）
            sat_height = sat_pos.altitude
            
            # 計算仰角
            if ground_distance > 0:
                elevation_rad = math.atan(sat_height / ground_distance)
                elevation_deg = math.degrees(elevation_rad)
                
                # 確保仰角在合理範圍內
                elevation_deg = max(0, min(90, elevation_deg))
            else:
                elevation_deg = 90.0  # 衛星正在頭頂
                
            return elevation_deg
            
        except Exception as e:
            self.logger.warning(f"仰角計算失敗: {str(e)}")
            return 10.0  # 預設仰角
    
    async def _select_d2_serving_satellite(self, ue_position: Position, reference_satellite: str) -> Optional[str]:
        """
        Phase 2.1 改進：自動選擇 D2 事件服務衛星
        
        選擇策略：
        1. 選擇離 UE 最近的可見衛星
        2. 確保不是參考衛星
        3. 用於模擬模式中缺少鄰居細胞配置時
        """
        try:
            current_time = datetime.now(timezone.utc).timestamp()
            available_satellites = []
            
            # 獲取所有可用衛星 (排除參考衛星)
            all_satellites = [s for s in self.orbit_engine.sgp4_cache.keys() if s != reference_satellite]
            
            if not all_satellites:
                self.logger.warning("沒有可用的服務衛星")
                return None
            
            # 計算每顆衛星到 UE 的距離
            for satellite_id in all_satellites:
                sat_pos = self.orbit_engine.calculate_satellite_position(satellite_id, current_time)
                if sat_pos:
                    distance = self.orbit_engine.calculate_distance(sat_pos, ue_position)
                    available_satellites.append({
                        'satellite_id': satellite_id,
                        'distance': distance,
                        'position': sat_pos
                    })
            
            if not available_satellites:
                return None
            
            # 按距離排序，選擇最近的衛星作為服務衛星
            available_satellites.sort(key=lambda x: x['distance'])
            
            selected = available_satellites[0]
            self.logger.info(
                f"D2 事件選擇服務衛星: {selected['satellite_id']}, "
                f"距離: {selected['distance']:.1f}km"
            )
            return selected['satellite_id']
            
        except Exception as e:
            self.logger.error("D2 服務衛星選擇失敗", error=str(e))
            return None
            
    async def _process_d2_measurement(
        self,
        ue_position: Position,
        params: D2Parameters,
        neighbor_cells: List[NeighborCellConfig]
    ) -> Optional[MeasurementResult]:
        """
        處理 D2 事件測量 - Phase 2.1 改進版本
        
        D2 事件：移動參考位置距離事件
        - 雙重距離條件：衛星間距離 (Thresh1) 和地面距離 (Thresh2)
        - 自動選擇參考衛星，不依賴 SIB19 初始化
        - 符合 3GPP TS 38.331 標準
        """
        try:
            current_time = datetime.now(timezone.utc)
            measurement_values = {}
            satellite_positions = {}
            
            # Phase 2.1 改進：自動選擇參考衛星
            reference_satellite = await self._select_d2_reference_satellite(ue_position)
            
            if not reference_satellite:
                self.logger.warning("D2 事件：無法選擇參考衛星")
                return None
                
            # 計算參考衛星位置
            reference_pos = self.orbit_engine.calculate_satellite_position(
                reference_satellite,
                current_time.timestamp()
            )
            
            if not reference_pos:
                self.logger.warning(f"D2 事件：無法計算參考衛星位置 {reference_satellite}")
                return None
                
            satellite_positions[reference_satellite] = reference_pos
            measurement_values["reference_satellite"] = reference_satellite
            
            # Phase 2.1 改進：計算服務衛星到參考衛星距離 (衛星間距離)
            serving_satellite = None
            
            if neighbor_cells:
                serving_satellite = neighbor_cells[0].satellite_id
            else:
                # 模擬模式：自動選擇服務衛星 (選擇離 UE 最近的非參考衛星)
                serving_satellite = await self._select_d2_serving_satellite(ue_position, reference_satellite)
            
            if serving_satellite:
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
                    try:
                        # 只對數值型數據進行統計計算
                        numeric_values = []
                        for val in values:
                            if isinstance(val, (int, float)):
                                numeric_values.append(float(val))
                        
                        if numeric_values:
                            measurement_stats[key] = {
                                "mean": np.mean(numeric_values),
                                "std": np.std(numeric_values),
                                "min": np.min(numeric_values),
                                "max": np.max(numeric_values),
                                "count": len(numeric_values)
                            }
                        else:
                            # 對於非數值數據，只統計數量
                            measurement_stats[key] = {
                                "type": "non_numeric",
                                "unique_values": len(set(str(v) for v in values)),
                                "count": len(values)
                            }
                    except Exception as e:
                        # 統計計算失敗時的回退方案
                        measurement_stats[key] = {
                            "error": f"統計計算失敗: {str(e)}",
                            "count": len(values)
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