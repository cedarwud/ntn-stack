"""
📡 SMTC 測量配置優化系統
============================

基於衛星可見性預測的智能 SMTC 測量窗口配置
最大化測量效率並最小化功耗與延遲

作者: Claude Sonnet 4 (SuperClaude)
版本: v1.0
日期: 2025-08-01
符合: 3GPP TS 38.331, TS 38.101-5
"""

import time
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import math

logger = logging.getLogger(__name__)


class MeasurementType(Enum):
    """測量類型枚舉"""
    SSB_RSRP = "ssb_rsrp"
    SSB_RSRQ = "ssb_rsrq"
    SSB_SINR = "ssb_sinr"
    CSI_RSRP = "csi_rsrp"
    CSI_RSRQ = "csi_rsrq"
    CSI_SINR = "csi_sinr"


class PriorityLevel(Enum):
    """優先級枚舉"""
    CRITICAL = "critical"    # 緊急換手
    HIGH = "high"           # 高優先級測量
    NORMAL = "normal"       # 正常測量
    LOW = "low"             # 背景測量


@dataclass
class SatelliteVisibilityWindow:
    """衛星可見性窗口"""
    satellite_id: str
    start_time: float
    end_time: float
    max_elevation_deg: float
    peak_time: float
    predicted_rsrp_range: Tuple[float, float]  # (min, max)
    visibility_confidence: float  # 0-1


@dataclass
class MeasurementWindow:
    """測量窗口配置"""
    window_id: str
    start_time: float
    duration_ms: int
    measurement_types: Set[MeasurementType]
    target_satellites: List[str]
    priority: PriorityLevel
    power_budget: float  # mW
    expected_measurements: int


@dataclass
class SMTCConfig:
    """SMTC配置結果"""
    config_id: str
    periodicity_ms: int
    offset_ms: int
    duration_ms: int
    measurement_slots: List[MeasurementWindow]
    total_power_consumption: float
    efficiency_score: float
    adaptive_parameters: Dict[str, Any]


class SatelliteVisibilityPredictor:
    """
    衛星可見性預測器
    基於軌道參數預測衛星可見性窗口
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SatelliteVisibilityPredictor")
        self.prediction_horizon_hours = 2.0  # 預測2小時內的可見性
        self.elevation_threshold_deg = 10.0  # 最低仰角門檻
        
    def predict_visibility_windows(self, 
                                 satellite_positions: Dict[str, Dict],
                                 ue_position: Tuple[float, float, float],
                                 start_time: float) -> List[SatelliteVisibilityWindow]:
        """
        預測衛星可見性窗口
        
        Args:
            satellite_positions: 衛星位置數據
            ue_position: UE位置 (lat, lon, alt)
            start_time: 預測開始時間
            
        Returns:
            List[SatelliteVisibilityWindow]: 可見性窗口列表
        """
        try:
            windows = []
            end_time = start_time + self.prediction_horizon_hours * 3600
            
            for sat_id, sat_data in satellite_positions.items():
                # 預測該衛星的可見性窗口
                sat_windows = self._predict_satellite_windows(
                    sat_id, sat_data, ue_position, start_time, end_time)
                windows.extend(sat_windows)
            
            # 按開始時間排序
            windows.sort(key=lambda w: w.start_time)
            
            self.logger.info(f"預測到 {len(windows)} 個可見性窗口")
            return windows
            
        except Exception as e:
            self.logger.error(f"可見性預測失敗: {e}")
            return []
    
    def _predict_satellite_windows(self, sat_id: str, sat_data: Dict,
                                 ue_position: Tuple[float, float, float],
                                 start_time: float, end_time: float) -> List[SatelliteVisibilityWindow]:
        """預測單顆衛星的可見性窗口"""
        windows = []
        
        # 簡化的軌道預測模型
        orbit_period = sat_data.get('orbit_period_sec', 5400)  # 90分鐘軌道
        current_elevation = sat_data.get('elevation_deg', 0)
        current_azimuth = sat_data.get('azimuth_deg', 0)
        orbital_velocity = 360.0 / orbit_period  # 度/秒
        
        # 搜索可見性窗口
        time_step = 60.0  # 1分鐘步進
        current_time = start_time
        in_visibility_window = False
        window_start = None
        max_elevation = 0
        peak_time = None
        
        while current_time <= end_time:
            # 預測該時刻的衛星位置
            time_offset = current_time - start_time
            predicted_elevation = self._predict_elevation(
                current_elevation, current_azimuth, time_offset, 
                orbital_velocity, ue_position)
            
            if predicted_elevation >= self.elevation_threshold_deg:
                if not in_visibility_window:
                    # 開始新的可見性窗口
                    in_visibility_window = True
                    window_start = current_time
                    max_elevation = predicted_elevation
                    peak_time = current_time
                else:
                    # 更新最大仰角
                    if predicted_elevation > max_elevation:
                        max_elevation = predicted_elevation
                        peak_time = current_time
            else:
                if in_visibility_window:
                    # 結束當前可見性窗口
                    window = SatelliteVisibilityWindow(
                        satellite_id=sat_id,
                        start_time=window_start,
                        end_time=current_time,
                        max_elevation_deg=max_elevation,
                        peak_time=peak_time,
                        predicted_rsrp_range=self._estimate_rsrp_range(max_elevation),
                        visibility_confidence=self._calculate_confidence(max_elevation)
                    )
                    windows.append(window)
                    in_visibility_window = False
            
            current_time += time_step
        
        # 處理在結束時間仍在可見窗口內的情況
        if in_visibility_window:
            window = SatelliteVisibilityWindow(
                satellite_id=sat_id,
                start_time=window_start,
                end_time=end_time,
                max_elevation_deg=max_elevation,
                peak_time=peak_time,
                predicted_rsrp_range=self._estimate_rsrp_range(max_elevation),
                visibility_confidence=self._calculate_confidence(max_elevation)
            )
            windows.append(window)
        
        return windows
    
    def _predict_elevation(self, current_elevation: float, current_azimuth: float,
                         time_offset: float, orbital_velocity: float,
                         ue_position: Tuple[float, float, float]) -> float:
        """預測指定時間的衛星仰角"""
        # 簡化的軌道模型：假設圓軌道
        angular_change = orbital_velocity * time_offset
        
        # 模擬仰角變化（簡化模型）
        phase = math.radians(angular_change)
        elevation_variation = 30 * math.sin(phase)  # ±30度仰角變化
        
        predicted_elevation = current_elevation + elevation_variation
        
        # 限制在合理範圍內
        return max(-10.0, min(90.0, predicted_elevation))
    
    def _estimate_rsrp_range(self, max_elevation: float) -> Tuple[float, float]:
        """基於最大仰角估計RSRP範圍"""
        # 基於仰角的RSRP估計模型
        if max_elevation > 60:
            return (-95.0, -85.0)  # 高仰角，強信號
        elif max_elevation > 30:
            return (-105.0, -95.0)  # 中等仰角
        elif max_elevation > 15:
            return (-115.0, -105.0)  # 低仰角
        else:
            return (-125.0, -115.0)  # 很低仰角
    
    def _calculate_confidence(self, max_elevation: float) -> float:
        """計算預測信心度"""
        # 仰角越高，預測越可靠
        if max_elevation > 45:
            return 0.95
        elif max_elevation > 30:
            return 0.85
        elif max_elevation > 15:
            return 0.75
        else:
            return 0.6


class MeasurementWindowOptimizer:
    """
    測量窗口優化器
    基於衛星可見性和優先級優化測量窗口分配
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MeasurementWindowOptimizer")
        
        # 測量配置參數
        self.min_measurement_duration_ms = 10
        self.max_measurement_duration_ms = 500
        self.measurement_gap_ms = 5  # 測量間隔
        
        # 功耗模型參數
        self.base_power_mw = 100  # 基礎功耗
        self.measurement_power_factor = {
            MeasurementType.SSB_RSRP: 1.0,
            MeasurementType.SSB_RSRQ: 1.2,
            MeasurementType.SSB_SINR: 1.5,
            MeasurementType.CSI_RSRP: 2.0,
            MeasurementType.CSI_RSRQ: 2.5,
            MeasurementType.CSI_SINR: 3.0
        }
        
    def optimize_measurement_windows(self, 
                                   visibility_windows: List[SatelliteVisibilityWindow],
                                   measurement_requirements: Dict[str, Any],
                                   power_budget: float) -> List[MeasurementWindow]:
        """
        優化測量窗口分配
        
        Args:
            visibility_windows: 衛星可見性窗口
            measurement_requirements: 測量需求
            power_budget: 功耗預算 (mW)
            
        Returns:
            List[MeasurementWindow]: 優化後的測量窗口
        """
        try:
            # 1. 窗口優先級評估
            prioritized_windows = self._prioritize_windows(visibility_windows, measurement_requirements)
            
            # 2. 功耗約束優化
            optimized_windows = self._optimize_power_constraints(prioritized_windows, power_budget)
            
            # 3. 測量衝突解決
            resolved_windows = self._resolve_measurement_conflicts(optimized_windows)
            
            # 4. 效率評分
            for window in resolved_windows:
                window.efficiency_score = self._calculate_efficiency_score(window)
            
            self.logger.info(f"優化完成，生成 {len(resolved_windows)} 個測量窗口")
            return resolved_windows
            
        except Exception as e:
            self.logger.error(f"測量窗口優化失敗: {e}")
            return []
    
    def _prioritize_windows(self, visibility_windows: List[SatelliteVisibilityWindow],
                          requirements: Dict[str, Any]) -> List[MeasurementWindow]:
        """對可見性窗口進行優先級評估"""
        measurement_windows = []
        
        for vis_window in visibility_windows:
            # 決定測量類型
            measurement_types = self._determine_measurement_types(vis_window, requirements)
            
            # 決定優先級
            priority = self._determine_priority(vis_window, requirements)
            
            # 計算最佳測量持續時間
            duration = self._calculate_optimal_duration(vis_window, measurement_types)
            
            # 估計功耗
            power_consumption = self._estimate_power_consumption(measurement_types, duration)
            
            # 創建測量窗口
            window = MeasurementWindow(
                window_id=f"mw_{vis_window.satellite_id}_{int(vis_window.start_time)}",
                start_time=vis_window.peak_time - duration/2000,  # 以峰值時間為中心
                duration_ms=duration,
                measurement_types=measurement_types,
                target_satellites=[vis_window.satellite_id],
                priority=priority,
                power_budget=power_consumption,
                expected_measurements=len(measurement_types)
            )
            
            measurement_windows.append(window)
        
        # 按優先級和效益排序
        measurement_windows.sort(key=lambda w: (
            w.priority.value,  # 優先級
            -w.expected_measurements,  # 測量數量（越多越好）
            w.power_budget  # 功耗（越少越好）
        ))
        
        return measurement_windows
    
    def _determine_measurement_types(self, vis_window: SatelliteVisibilityWindow,
                                   requirements: Dict[str, Any]) -> Set[MeasurementType]:
        """決定該窗口需要的測量類型"""
        measurement_types = set()
        
        # 基礎測量：RSRP 總是需要的
        measurement_types.add(MeasurementType.SSB_RSRP)
        
        # 基於信號強度決定額外測量
        rsrp_min, rsrp_max = vis_window.predicted_rsrp_range
        
        if rsrp_max > -100:  # 強信號，可以進行更多測量
            measurement_types.add(MeasurementType.SSB_RSRQ)
            measurement_types.add(MeasurementType.SSB_SINR)
            
            if rsrp_max > -90:  # 非常強信號，進行 CSI 測量
                measurement_types.add(MeasurementType.CSI_RSRP)
        
        # 基於需求決定
        if requirements.get('high_accuracy_mode', False):
            measurement_types.add(MeasurementType.CSI_RSRP)
            measurement_types.add(MeasurementType.CSI_RSRQ)
        
        return measurement_types
    
    def _determine_priority(self, vis_window: SatelliteVisibilityWindow,
                          requirements: Dict[str, Any]) -> PriorityLevel:
        """決定測量優先級"""
        rsrp_min, rsrp_max = vis_window.predicted_rsrp_range
        
        # 基於信號強度決定優先級
        if rsrp_max > -90:
            return PriorityLevel.HIGH  # 強信號，高優先級
        elif rsrp_max > -100:
            return PriorityLevel.NORMAL  # 中等信號
        elif rsrp_max > -110:
            return PriorityLevel.LOW  # 弱信號，低優先級
        else:
            return PriorityLevel.LOW  # 很弱信號
        
        # 基於可見性信心度調整
        if vis_window.visibility_confidence < 0.7:
            # 降低不確定窗口的優先級
            current_priority = priority
            if current_priority == PriorityLevel.HIGH:
                return PriorityLevel.NORMAL
            elif current_priority == PriorityLevel.NORMAL:
                return PriorityLevel.LOW
        
        return priority
    
    def _calculate_optimal_duration(self, vis_window: SatelliteVisibilityWindow,
                                  measurement_types: Set[MeasurementType]) -> int:
        """計算最佳測量持續時間 (ms)"""
        # 基礎持續時間：每種測量類型需要一定時間
        base_duration_per_type = {
            MeasurementType.SSB_RSRP: 20,
            MeasurementType.SSB_RSRQ: 25,
            MeasurementType.SSB_SINR: 30,
            MeasurementType.CSI_RSRP: 50,
            MeasurementType.CSI_RSRQ: 60,
            MeasurementType.CSI_SINR: 80
        }
        
        total_duration = sum(base_duration_per_type[mt] for mt in measurement_types)
        
        # 基於可見窗口長度調整
        window_duration_sec = vis_window.end_time - vis_window.start_time
        max_allowed_duration = min(window_duration_sec * 1000 / 2, 
                                 self.max_measurement_duration_ms)
        
        # 基於信號強度調整
        rsrp_min, rsrp_max = vis_window.predicted_rsrp_range
        if rsrp_max < -110:  # 弱信號需要更長測量時間
            total_duration = int(total_duration * 1.5)
        elif rsrp_max > -90:  # 強信號可以縮短測量時間
            total_duration = int(total_duration * 0.8)
        
        return max(self.min_measurement_duration_ms, 
                  min(int(total_duration), int(max_allowed_duration)))
    
    def _estimate_power_consumption(self, measurement_types: Set[MeasurementType],
                                  duration_ms: int) -> float:
        """估計功耗 (mW)"""
        total_factor = sum(self.measurement_power_factor[mt] for mt in measurement_types)
        power_consumption = self.base_power_mw * total_factor * (duration_ms / 1000.0)
        return power_consumption
    
    def _optimize_power_constraints(self, windows: List[MeasurementWindow],
                                  power_budget: float) -> List[MeasurementWindow]:
        """基於功耗約束優化測量窗口"""
        optimized_windows = []
        current_power_usage = 0.0
        
        # 按優先級排序，優先分配高優先級窗口
        sorted_windows = sorted(windows, key=lambda w: (
            w.priority.value, -w.expected_measurements
        ))
        
        for window in sorted_windows:
            if current_power_usage + window.power_budget <= power_budget:
                optimized_windows.append(window)
                current_power_usage += window.power_budget
            else:
                # 嘗試縮減測量以適應功耗預算
                reduced_window = self._reduce_measurement_complexity(
                    window, power_budget - current_power_usage)
                
                if reduced_window:
                    optimized_windows.append(reduced_window)
                    current_power_usage += reduced_window.power_budget
        
        self.logger.info(f"功耗優化: {len(optimized_windows)}/{len(windows)} 窗口，"
                        f"功耗使用: {current_power_usage:.1f}/{power_budget:.1f} mW")
        
        return optimized_windows
    
    def _reduce_measurement_complexity(self, window: MeasurementWindow,
                                     available_power: float) -> Optional[MeasurementWindow]:
        """縮減測量複雜度以適應功耗約束"""
        if available_power <= 0:
            return None
        
        # 按功耗從高到低排序測量類型
        sorted_measurements = sorted(window.measurement_types,
                                   key=lambda mt: self.measurement_power_factor[mt],
                                   reverse=True)
        
        # 逐步移除高功耗測量
        reduced_measurements = set(sorted_measurements)
        
        while reduced_measurements:
            estimated_power = self._estimate_power_consumption(
                reduced_measurements, window.duration_ms)
            
            if estimated_power <= available_power:
                # 創建縮減後的窗口
                return MeasurementWindow(
                    window_id=window.window_id + "_reduced",
                    start_time=window.start_time,
                    duration_ms=window.duration_ms,
                    measurement_types=reduced_measurements,
                    target_satellites=window.target_satellites,
                    priority=window.priority,
                    power_budget=estimated_power,
                    expected_measurements=len(reduced_measurements)
                )
            
            # 移除最高功耗的測量
            if reduced_measurements:
                reduced_measurements.remove(sorted_measurements[len(sorted_measurements) - len(reduced_measurements)])
        
        return None
    
    def _resolve_measurement_conflicts(self, windows: List[MeasurementWindow]) -> List[MeasurementWindow]:
        """解決測量窗口時間衝突"""
        resolved_windows = []
        
        # 按開始時間排序
        sorted_windows = sorted(windows, key=lambda w: w.start_time)
        
        for window in sorted_windows:
            # 檢查與已分配窗口的衝突
            conflict_resolved = False
            
            for existing_window in resolved_windows:
                if self._windows_overlap(window, existing_window):
                    # 嘗試調整時間
                    adjusted_window = self._adjust_window_timing(
                        window, existing_window, resolved_windows)
                    
                    if adjusted_window:
                        resolved_windows.append(adjusted_window)
                        conflict_resolved = True
                        break
            
            if not conflict_resolved:
                # 無衝突或無法解決衝突，直接添加
                if not any(self._windows_overlap(window, ew) for ew in resolved_windows):
                    resolved_windows.append(window)
        
        return resolved_windows
    
    def _windows_overlap(self, window1: MeasurementWindow, 
                        window2: MeasurementWindow) -> bool:
        """檢查兩個測量窗口是否重疊"""
        end1 = window1.start_time + window1.duration_ms / 1000.0
        end2 = window2.start_time + window2.duration_ms / 1000.0
        
        return not (end1 <= window2.start_time or end2 <= window1.start_time)
    
    def _adjust_window_timing(self, new_window: MeasurementWindow,
                            existing_window: MeasurementWindow,
                            all_windows: List[MeasurementWindow]) -> Optional[MeasurementWindow]:
        """調整窗口時間以避免衝突"""
        # 嘗試將新窗口移到現有窗口之後
        existing_end = existing_window.start_time + existing_window.duration_ms / 1000.0
        adjusted_start = existing_end + self.measurement_gap_ms / 1000.0
        
        adjusted_window = MeasurementWindow(
            window_id=new_window.window_id + "_adjusted",
            start_time=adjusted_start,
            duration_ms=new_window.duration_ms,
            measurement_types=new_window.measurement_types,
            target_satellites=new_window.target_satellites,
            priority=new_window.priority,
            power_budget=new_window.power_budget,
            expected_measurements=new_window.expected_measurements
        )
        
        # 檢查調整後的窗口是否與其他窗口衝突
        if not any(self._windows_overlap(adjusted_window, ew) for ew in all_windows):
            return adjusted_window
        
        return None
    
    def _calculate_efficiency_score(self, window: MeasurementWindow) -> float:
        """計算測量窗口效率評分"""
        # 效率 = 測量價值 / 資源消耗
        measurement_value = len(window.measurement_types) * 10
        
        # 優先級加成
        priority_bonus = {
            PriorityLevel.CRITICAL: 100,
            PriorityLevel.HIGH: 50,
            PriorityLevel.NORMAL: 20,
            PriorityLevel.LOW: 10
        }
        measurement_value += priority_bonus[window.priority]
        
        # 資源消耗 = 功耗 + 時間
        resource_cost = window.power_budget + window.duration_ms / 10.0
        
        return measurement_value / max(resource_cost, 1.0)


class SMTCOptimizer:
    """
    SMTC 測量優化系統
    整合可見性預測和測量窗口優化
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SMTCOptimizer")
        self.visibility_predictor = SatelliteVisibilityPredictor()
        self.window_optimizer = MeasurementWindowOptimizer()
        
        # SMTC 配置參數
        self.default_periodicity_ms = 160  # 3GPP 標準週期
        self.adaptive_periodicity_range = (80, 640)  # 自適應範圍
        
        self.logger.info("SMTC 測量優化系統初始化完成")
    
    def optimize_smtc_configuration(self,
                                  satellite_positions: Dict[str, Dict],
                                  ue_position: Tuple[float, float, float],
                                  measurement_requirements: Dict[str, Any],
                                  power_budget: float,
                                  timestamp: float) -> SMTCConfig:
        """
        優化 SMTC 測量配置
        
        Args:
            satellite_positions: 衛星位置數據
            ue_position: UE位置
            measurement_requirements: 測量需求
            power_budget: 功耗預算 (mW)
            timestamp: 當前時間戳
            
        Returns:
            SMTCConfig: 優化後的SMTC配置
        """
        try:
            # 1. 預測衛星可見性
            visibility_windows = self.visibility_predictor.predict_visibility_windows(
                satellite_positions, ue_position, timestamp)
            
            # 2. 優化測量窗口
            measurement_windows = self.window_optimizer.optimize_measurement_windows(
                visibility_windows, measurement_requirements, power_budget)
            
            # 3. 生成 SMTC 配置
            smtc_config = self._generate_smtc_config(
                measurement_windows, measurement_requirements, timestamp)
            
            # 4. 自適應參數調整
            smtc_config.adaptive_parameters = self._calculate_adaptive_parameters(
                visibility_windows, measurement_windows)
            
            self.logger.info(f"SMTC 配置優化完成: 週期={smtc_config.periodicity_ms}ms, "
                           f"窗口數={len(smtc_config.measurement_slots)}, "
                           f"效率={smtc_config.efficiency_score:.2f}")
            
            return smtc_config
            
        except Exception as e:
            self.logger.error(f"SMTC 配置優化失敗: {e}")
            # 返回預設配置
            return self._get_default_smtc_config(timestamp)
    
    def _generate_smtc_config(self, measurement_windows: List[MeasurementWindow],
                            requirements: Dict[str, Any], timestamp: float) -> SMTCConfig:
        """生成 SMTC 配置"""
        # 計算最佳週期性
        optimal_periodicity = self._calculate_optimal_periodicity(measurement_windows)
        
        # 計算偏移量
        optimal_offset = self._calculate_optimal_offset(measurement_windows, optimal_periodicity)
        
        # 計算總持續時間
        total_duration = max((w.duration_ms for w in measurement_windows), default=self.default_periodicity_ms)
        
        # 計算總功耗
        total_power = sum(w.power_budget for w in measurement_windows)
        
        # 計算效率評分
        efficiency_score = self._calculate_overall_efficiency(measurement_windows, total_power)
        
        return SMTCConfig(
            config_id=f"smtc_{int(timestamp)}",
            periodicity_ms=optimal_periodicity,
            offset_ms=optimal_offset,
            duration_ms=total_duration,
            measurement_slots=measurement_windows,
            total_power_consumption=total_power,
            efficiency_score=efficiency_score,
            adaptive_parameters={}
        )
    
    def _calculate_optimal_periodicity(self, windows: List[MeasurementWindow]) -> int:
        """計算最佳測量週期性"""
        if not windows:
            return self.default_periodicity_ms
        
        # 基於測量窗口分布計算週期
        window_intervals = []
        sorted_windows = sorted(windows, key=lambda w: w.start_time)
        
        for i in range(1, len(sorted_windows)):
            interval = (sorted_windows[i].start_time - 
                       sorted_windows[i-1].start_time) * 1000  # 轉換為 ms
            window_intervals.append(interval)
        
        if window_intervals:
            # 使用平均間隔作為基礎週期
            avg_interval = np.mean(window_intervals)
            optimal_periodicity = max(self.adaptive_periodicity_range[0],
                                    min(int(avg_interval), self.adaptive_periodicity_range[1]))
        else:
            optimal_periodicity = self.default_periodicity_ms
        
        # 確保週期是標準值之一 (80, 160, 320, 640 ms)
        standard_periodicities = [80, 160, 320, 640]
        optimal_periodicity = min(standard_periodicities, 
                                key=lambda x: abs(x - optimal_periodicity))
        
        return optimal_periodicity
    
    def _calculate_optimal_offset(self, windows: List[MeasurementWindow],
                                periodicity: int) -> int:
        """計算最佳測量偏移量"""
        if not windows:
            return 0
        
        # 基於第一個高優先級窗口的時間計算偏移
        high_priority_windows = [w for w in windows 
                               if w.priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]]
        
        if high_priority_windows:
            first_window = min(high_priority_windows, key=lambda w: w.start_time)
            # 計算相對於當前時間的偏移
            offset_ms = int((first_window.start_time % (periodicity / 1000.0)) * 1000)
        else:
            offset_ms = 0
        
        return max(0, min(offset_ms, periodicity - 1))
    
    def _calculate_overall_efficiency(self, windows: List[MeasurementWindow],
                                    total_power: float) -> float:
        """計算整體效率評分"""
        if not windows:
            return 0.0
        
        # 效率 = 總測量價值 / 總資源消耗
        total_value = 0
        total_cost = total_power
        
        for window in windows:
            # 測量價值
            measurement_value = len(window.measurement_types) * 10
            
            # 優先級加成
            priority_multiplier = {
                PriorityLevel.CRITICAL: 4.0,
                PriorityLevel.HIGH: 2.0,
                PriorityLevel.NORMAL: 1.0,
                PriorityLevel.LOW: 0.5
            }
            measurement_value *= priority_multiplier[window.priority]
            
            total_value += measurement_value
            total_cost += window.duration_ms / 10.0  # 時間成本
        
        return total_value / max(total_cost, 1.0)
    
    def _calculate_adaptive_parameters(self, visibility_windows: List[SatelliteVisibilityWindow],
                                     measurement_windows: List[MeasurementWindow]) -> Dict[str, Any]:
        """計算自適應參數"""
        params = {}
        
        # 可見性統計
        if visibility_windows:
            avg_elevation = np.mean([w.max_elevation_deg for w in visibility_windows])
            avg_confidence = np.mean([w.visibility_confidence for w in visibility_windows])
            
            params['average_elevation_deg'] = avg_elevation
            params['average_confidence'] = avg_confidence
            params['total_visibility_windows'] = len(visibility_windows)
        
        # 測量統計
        if measurement_windows:
            priority_distribution = {}
            for priority in PriorityLevel:
                count = sum(1 for w in measurement_windows if w.priority == priority)
                priority_distribution[priority.value] = count
            
            params['priority_distribution'] = priority_distribution
            params['total_measurement_windows'] = len(measurement_windows)
            params['avg_window_duration_ms'] = np.mean([w.duration_ms for w in measurement_windows])
        
        # 自適應建議
        params['recommended_updates'] = self._generate_adaptive_recommendations(
            visibility_windows, measurement_windows)
        
        return params
    
    def _generate_adaptive_recommendations(self, 
                                         visibility_windows: List[SatelliteVisibilityWindow],
                                         measurement_windows: List[MeasurementWindow]) -> List[str]:
        """生成自適應建議"""
        recommendations = []
        
        if visibility_windows:
            # 基於可見性建議
            high_confidence_windows = [w for w in visibility_windows if w.visibility_confidence > 0.8]
            if len(high_confidence_windows) / len(visibility_windows) > 0.7:
                recommendations.append("高預測可信度，可增加測量複雜度")
            
            # 基於仰角建議
            high_elevation_windows = [w for w in visibility_windows if w.max_elevation_deg > 45]
            if len(high_elevation_windows) / len(visibility_windows) > 0.3:
                recommendations.append("多個高仰角窗口，可啟用 CSI 測量")
        
        if measurement_windows:
            # 基於功耗建議
            high_power_windows = [w for w in measurement_windows if w.power_budget > 1000]
            if len(high_power_windows) > len(measurement_windows) * 0.5:
                recommendations.append("功耗偏高，建議優化測量類型選擇")
        
        return recommendations
    
    def _get_default_smtc_config(self, timestamp: float) -> SMTCConfig:
        """獲取預設 SMTC 配置"""
        return SMTCConfig(
            config_id=f"smtc_default_{int(timestamp)}",
            periodicity_ms=self.default_periodicity_ms,
            offset_ms=0,
            duration_ms=80,
            measurement_slots=[],
            total_power_consumption=500.0,  # 預設功耗
            efficiency_score=0.5,
            adaptive_parameters={}
        )


# 測試和驗證函數
def test_smtc_optimization():
    """測試 SMTC 測量優化系統"""
    logger.info("開始 SMTC 測量優化系統測試")
    
    # 創建測試數據
    satellite_positions = {
        'STARLINK-1234': {
            'elevation_deg': 45.0,
            'azimuth_deg': 180.0,
            'orbit_period_sec': 5400,
            'position': (25.0, 122.0, 550)
        },
        'STARLINK-5678': {
            'elevation_deg': 30.0,
            'azimuth_deg': 90.0,
            'orbit_period_sec': 5400,
            'position': (24.0, 121.0, 550)
        }
    }
    
    ue_position = (24.9442, 121.3711, 0.05)  # NTPU
    
    measurement_requirements = {
        'high_accuracy_mode': True,
        'power_efficiency_mode': False,
        'priority_satellites': ['STARLINK-1234']
    }
    
    power_budget = 5000.0  # 5W
    timestamp = time.time()
    
    # 創建優化器
    smtc_optimizer = SMTCOptimizer()
    
    # 執行優化
    config = smtc_optimizer.optimize_smtc_configuration(
        satellite_positions, ue_position, measurement_requirements, 
        power_budget, timestamp)
    
    # 輸出結果
    logger.info(f"SMTC 配置結果:")
    logger.info(f"  配置ID: {config.config_id}")
    logger.info(f"  週期性: {config.periodicity_ms} ms")
    logger.info(f"  偏移量: {config.offset_ms} ms")
    logger.info(f"  持續時間: {config.duration_ms} ms")
    logger.info(f"  測量窗口數: {len(config.measurement_slots)}")
    logger.info(f"  總功耗: {config.total_power_consumption:.1f} mW")
    logger.info(f"  效率評分: {config.efficiency_score:.2f}")
    
    # 詳細窗口信息
    for i, window in enumerate(config.measurement_slots):
        logger.info(f"  窗口 {i+1}: {window.window_id}")
        logger.info(f"    開始時間: {window.start_time:.1f}")
        logger.info(f"    持續時間: {window.duration_ms} ms")
        logger.info(f"    測量類型: {[mt.value for mt in window.measurement_types]}")
        logger.info(f"    優先級: {window.priority.value}")
        logger.info(f"    功耗: {window.power_budget:.1f} mW")
    
    # 自適應參數
    if config.adaptive_parameters:
        logger.info(f"  自適應參數: {config.adaptive_parameters}")
    
    return config


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 運行測試
    test_smtc_optimization()