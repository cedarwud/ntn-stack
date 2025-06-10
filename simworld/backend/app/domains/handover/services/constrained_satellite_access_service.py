"""
Constrained Satellite Access Strategy Implementation
實作 IEEE INFOCOM 2024 論文中的約束式衛星接入策略

這個服務實現了 Fast Access Satellite Prediction Algorithm 的核心約束機制：
1. 軌道可預測性約束 (Orbit Predictability Constraints)
2. 信號品質約束 (Signal Quality Constraints) 
3. 空間分布優化 (Spatial Distribution Optimization)
4. 負載平衡策略 (Load Balancing Strategy)
"""

import asyncio
import time
import math
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SatelliteConstraintType(str, Enum):
    """衛星約束類型"""
    ELEVATION_MIN = "elevation_min"           # 最小仰角約束
    SIGNAL_STRENGTH_MIN = "signal_strength_min"  # 最小信號強度約束
    DISTANCE_MAX = "distance_max"             # 最大距離約束
    ORBITAL_VELOCITY = "orbital_velocity"     # 軌道速度約束
    LOAD_BALANCE = "load_balance"             # 負載平衡約束
    SPATIAL_SEPARATION = "spatial_separation" # 空間分離約束


@dataclass
class SatelliteConstraint:
    """衛星約束定義"""
    constraint_type: SatelliteConstraintType
    threshold_value: float
    weight: float = 1.0  # 約束權重 (0-1)
    is_hard_constraint: bool = True  # 硬約束vs軟約束
    description: str = ""


@dataclass
class SatelliteAccessCandidate:
    """衛星接入候選者"""
    satellite_id: str
    satellite_name: str
    
    # 位置和信號參數
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    signal_strength_dbm: float
    
    # 軌道特性
    orbital_velocity_km_s: float
    coverage_duration_sec: float
    next_pass_time_sec: float
    
    # 約束評分
    constraint_scores: Dict[SatelliteConstraintType, float]
    overall_score: float
    
    # 負載信息
    current_ue_count: int = 0
    max_ue_capacity: int = 100
    load_ratio: float = 0.0


class ConstrainedSatelliteAccessService:
    """約束式衛星接入服務"""
    
    def __init__(self):
        # 約束配置
        self.constraints = self._initialize_default_constraints()
        
        # 衛星負載追蹤
        self.satellite_loads: Dict[str, int] = {}  # satellite_id -> current_ue_count
        self.ue_assignments: Dict[str, str] = {}    # ue_id -> satellite_id
        
        # 性能統計
        self.selection_history: List[Dict] = []
        self.constraint_violations: Dict[SatelliteConstraintType, int] = {}
        
    def _initialize_default_constraints(self) -> List[SatelliteConstraint]:
        """初始化預設約束條件"""
        return [
            SatelliteConstraint(
                constraint_type=SatelliteConstraintType.ELEVATION_MIN,
                threshold_value=10.0,  # 最小仰角 10 度
                weight=0.9,
                is_hard_constraint=True,
                description="最小仰角約束，確保良好的信號接收"
            ),
            SatelliteConstraint(
                constraint_type=SatelliteConstraintType.SIGNAL_STRENGTH_MIN,
                threshold_value=-90.0,  # 最小信號強度 -90 dBm
                weight=0.8,
                is_hard_constraint=True,
                description="最小信號強度約束，保證通信品質"
            ),
            SatelliteConstraint(
                constraint_type=SatelliteConstraintType.DISTANCE_MAX,
                threshold_value=2000.0,  # 最大距離 2000 km
                weight=0.7,
                is_hard_constraint=False,
                description="最大距離約束，控制傳播延遲"
            ),
            SatelliteConstraint(
                constraint_type=SatelliteConstraintType.LOAD_BALANCE,
                threshold_value=0.8,  # 最大負載率 80%
                weight=0.6,
                is_hard_constraint=False,
                description="負載平衡約束，避免單一衛星過載"
            ),
            SatelliteConstraint(
                constraint_type=SatelliteConstraintType.SPATIAL_SEPARATION,
                threshold_value=500.0,  # 最小空間分離 500 km
                weight=0.5,
                is_hard_constraint=False,
                description="空間分離約束，確保切換候選衛星的多樣性"
            )
        ]
    
    async def select_optimal_satellite(
        self,
        ue_id: str,
        ue_position: Tuple[float, float, float],
        available_satellites: List[Dict],
        timestamp: float,
        consider_future: bool = True
    ) -> Optional[SatelliteAccessCandidate]:
        """
        使用約束式策略選擇最佳衛星
        
        Args:
            ue_id: UE 設備 ID
            ue_position: UE 位置 (lat, lon, alt)
            available_satellites: 可用衛星列表
            timestamp: 時間戳
            consider_future: 是否考慮未來軌道預測
            
        Returns:
            選擇的最佳衛星候選者
        """
        try:
            logger.info(f"開始為 UE {ue_id} 執行約束式衛星選擇")
            
            # 1. 建立衛星候選者列表
            candidates = await self._build_satellite_candidates(
                available_satellites, ue_position, timestamp
            )
            
            if not candidates:
                logger.warning(f"沒有可用的衛星候選者 for UE {ue_id}")
                return None
            
            # 2. 應用硬約束過濾
            filtered_candidates = self._apply_hard_constraints(candidates)
            
            if not filtered_candidates:
                logger.warning(f"所有候選者都被硬約束過濾 for UE {ue_id}")
                # 記錄約束違反統計
                await self._record_constraint_violations(candidates)
                return None
            
            # 3. 計算軟約束評分
            scored_candidates = await self._calculate_constraint_scores(
                filtered_candidates, ue_position, timestamp
            )
            
            # 4. 負載平衡優化
            if consider_future:
                scored_candidates = await self._apply_load_balancing(
                    scored_candidates, ue_id
                )
            
            # 5. 選擇最佳候選者
            best_candidate = self._select_best_candidate(scored_candidates)
            
            # 6. 更新分配記錄
            if best_candidate:
                await self._update_assignment(ue_id, best_candidate.satellite_id)
                await self._record_selection_history(ue_id, best_candidate, scored_candidates)
                
            logger.info(f"為 UE {ue_id} 選擇衛星: {best_candidate.satellite_name if best_candidate else 'None'}")
            
            return best_candidate
            
        except Exception as e:
            logger.error(f"約束式衛星選擇失敗: {e}")
            return None
    
    async def _build_satellite_candidates(
        self,
        available_satellites: List[Dict],
        ue_position: Tuple[float, float, float],
        timestamp: float
    ) -> List[SatelliteAccessCandidate]:
        """建立衛星候選者列表"""
        candidates = []
        
        for sat in available_satellites:
            try:
                # 計算衛星相對於 UE 的位置參數
                elevation, azimuth, distance = self._calculate_satellite_geometry(
                    sat, ue_position
                )
                
                # 計算信號強度（簡化模型）
                signal_strength = self._calculate_signal_strength(distance, elevation)
                
                # 計算軌道特性
                orbital_velocity = sat.get('velocity_km_s', 7.5)
                coverage_duration = self._estimate_coverage_duration(elevation, orbital_velocity)
                next_pass_time = self._estimate_next_pass_time(sat, ue_position)
                
                # 建立候選者
                candidate = SatelliteAccessCandidate(
                    satellite_id=sat.get('norad_id', f"sat_{len(candidates)}"),
                    satellite_name=sat.get('name', f"Satellite-{len(candidates)}"),
                    elevation_deg=elevation,
                    azimuth_deg=azimuth,
                    distance_km=distance,
                    signal_strength_dbm=signal_strength,
                    orbital_velocity_km_s=orbital_velocity,
                    coverage_duration_sec=coverage_duration,
                    next_pass_time_sec=next_pass_time,
                    constraint_scores={},
                    overall_score=0.0,
                    current_ue_count=self.satellite_loads.get(sat.get('norad_id', ''), 0),
                    max_ue_capacity=100,
                    load_ratio=0.0
                )
                
                # 計算負載率
                candidate.load_ratio = candidate.current_ue_count / candidate.max_ue_capacity
                
                candidates.append(candidate)
                
            except Exception as e:
                logger.error(f"建立衛星候選者失敗: {sat} - {e}")
                continue
        
        logger.info(f"建立了 {len(candidates)} 個衛星候選者")
        return candidates
    
    def _calculate_satellite_geometry(
        self,
        satellite: Dict,
        ue_position: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """計算衛星相對於 UE 的幾何參數"""
        # 從衛星數據中獲取位置參數
        elevation = satellite.get('elevation_deg', 45.0)
        azimuth = satellite.get('azimuth_deg', 180.0) 
        distance = satellite.get('distance_km', 1000.0)
        
        return elevation, azimuth, distance
    
    def _calculate_signal_strength(self, distance_km: float, elevation_deg: float) -> float:
        """計算信號強度 (簡化的自由空間路徑損耗模型)"""
        # 修正的自由空間路徑損耗公式 (使用 2.4 GHz)
        frequency_ghz = 2.4
        
        # FSPL (dB) = 20*log10(d) + 20*log10(f) + 32.45
        # 其中 d 是距離(km)，f 是頻率(GHz)  
        path_loss_db = 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz) + 32.45
        
        # 仰角修正 (仰角越高，大氣衰減越小)
        elevation_factor = max(math.sin(math.radians(elevation_deg)), 0.1)  # 避免除零
        atmospheric_loss = 3.0 / elevation_factor  # 降低大氣損耗影響
        
        # 衛星通信典型參數
        tx_power_dbm = 40.0      # 衛星發射功率 40 dBm
        tx_antenna_gain_dbi = 35.0  # 衛星天線增益 35 dBi
        rx_antenna_gain_dbi = 25.0  # 地面終端天線增益 25 dBi
        
        # 計算接收信號強度
        signal_strength = (tx_power_dbm + tx_antenna_gain_dbi + rx_antenna_gain_dbi 
                          - path_loss_db - atmospheric_loss)
        
        return signal_strength
    
    def _estimate_coverage_duration(self, elevation_deg: float, orbital_velocity_km_s: float) -> float:
        """估計衛星覆蓋持續時間"""
        # 簡化模型：基於仰角和軌道速度估計
        if elevation_deg < 10:
            return 60.0  # 低仰角，短暫覆蓋
        elif elevation_deg < 30:
            return 300.0  # 中等仰角
        elif elevation_deg < 60:
            return 600.0  # 高仰角
        else:
            return 900.0  # 接近天頂，最長覆蓋
    
    def _estimate_next_pass_time(self, satellite: Dict, ue_position: Tuple[float, float, float]) -> float:
        """估計下次經過時間"""
        # 簡化模型：基於軌道週期估計
        orbital_period_sec = 90 * 60  # LEO 衛星典型軌道週期 90 分鐘
        return orbital_period_sec
    
    def _apply_hard_constraints(
        self,
        candidates: List[SatelliteAccessCandidate]
    ) -> List[SatelliteAccessCandidate]:
        """應用硬約束過濾候選者"""
        filtered = []
        
        for candidate in candidates:
            passes_all_hard_constraints = True
            
            for constraint in self.constraints:
                if not constraint.is_hard_constraint:
                    continue
                    
                passes_constraint = self._evaluate_hard_constraint(candidate, constraint)
                if not passes_constraint:
                    passes_all_hard_constraints = False
                    break
            
            if passes_all_hard_constraints:
                filtered.append(candidate)
        
        logger.info(f"硬約束過濾: {len(candidates)} -> {len(filtered)} 候選者")
        return filtered
    
    def _evaluate_hard_constraint(
        self,
        candidate: SatelliteAccessCandidate,
        constraint: SatelliteConstraint
    ) -> bool:
        """評估硬約束"""
        if constraint.constraint_type == SatelliteConstraintType.ELEVATION_MIN:
            return candidate.elevation_deg >= constraint.threshold_value
        
        elif constraint.constraint_type == SatelliteConstraintType.SIGNAL_STRENGTH_MIN:
            return candidate.signal_strength_dbm >= constraint.threshold_value
        
        elif constraint.constraint_type == SatelliteConstraintType.DISTANCE_MAX:
            return candidate.distance_km <= constraint.threshold_value
        
        else:
            return True  # 其他約束類型作為軟約束處理
    
    async def _calculate_constraint_scores(
        self,
        candidates: List[SatelliteAccessCandidate],
        ue_position: Tuple[float, float, float],
        timestamp: float
    ) -> List[SatelliteAccessCandidate]:
        """計算軟約束評分"""
        for candidate in candidates:
            total_score = 0.0
            total_weight = 0.0
            
            for constraint in self.constraints:
                if constraint.is_hard_constraint:
                    continue  # 硬約束已經在過濾階段處理
                
                score = self._calculate_constraint_score(candidate, constraint)
                candidate.constraint_scores[constraint.constraint_type] = score
                
                weighted_score = score * constraint.weight
                total_score += weighted_score
                total_weight += constraint.weight
            
            # 正規化總分
            candidate.overall_score = total_score / total_weight if total_weight > 0 else 0.0
        
        return candidates
    
    def _calculate_constraint_score(
        self,
        candidate: SatelliteAccessCandidate,
        constraint: SatelliteConstraint
    ) -> float:
        """計算單一約束的評分 (0-1)"""
        if constraint.constraint_type == SatelliteConstraintType.DISTANCE_MAX:
            # 距離越近越好 (歸一化到 0-1)
            normalized = 1.0 - min(candidate.distance_km / constraint.threshold_value, 1.0)
            return normalized
        
        elif constraint.constraint_type == SatelliteConstraintType.LOAD_BALANCE:
            # 負載越低越好
            return 1.0 - min(candidate.load_ratio / constraint.threshold_value, 1.0)
        
        elif constraint.constraint_type == SatelliteConstraintType.SPATIAL_SEPARATION:
            # 這需要與其他已選擇的衛星比較，暫時返回固定值
            return 0.8
        
        else:
            return 1.0  # 預設評分
    
    async def _apply_load_balancing(
        self,
        candidates: List[SatelliteAccessCandidate],
        ue_id: str
    ) -> List[SatelliteAccessCandidate]:
        """應用負載平衡優化"""
        # 根據當前負載調整候選者評分
        for candidate in candidates:
            # 負載懲罰：負載越高，評分越低
            load_penalty = candidate.load_ratio * 0.3  # 最大 30% 懲罰
            candidate.overall_score = max(0.0, candidate.overall_score - load_penalty)
        
        return candidates
    
    def _select_best_candidate(
        self,
        candidates: List[SatelliteAccessCandidate]
    ) -> Optional[SatelliteAccessCandidate]:
        """選擇最佳候選者"""
        if not candidates:
            return None
        
        # 按總評分排序，選擇最高分的
        candidates.sort(key=lambda c: c.overall_score, reverse=True)
        return candidates[0]
    
    async def _update_assignment(self, ue_id: str, satellite_id: str):
        """更新 UE 分配記錄"""
        # 如果 UE 之前已分配給其他衛星，更新負載
        if ue_id in self.ue_assignments:
            old_satellite_id = self.ue_assignments[ue_id]
            if old_satellite_id in self.satellite_loads:
                self.satellite_loads[old_satellite_id] = max(0, self.satellite_loads[old_satellite_id] - 1)
        
        # 更新新分配
        self.ue_assignments[ue_id] = satellite_id
        self.satellite_loads[satellite_id] = self.satellite_loads.get(satellite_id, 0) + 1
    
    async def _record_selection_history(
        self,
        ue_id: str,
        selected_candidate: SatelliteAccessCandidate,
        all_candidates: List[SatelliteAccessCandidate]
    ):
        """記錄選擇歷史"""
        history_entry = {
            "timestamp": time.time(),
            "ue_id": ue_id,
            "selected_satellite": selected_candidate.satellite_id,
            "selected_score": selected_candidate.overall_score,
            "total_candidates": len(all_candidates),
            "constraint_scores": selected_candidate.constraint_scores.copy()
        }
        
        self.selection_history.append(history_entry)
        
        # 保持歷史記錄在合理範圍內
        if len(self.selection_history) > 1000:
            self.selection_history = self.selection_history[-500:]
    
    async def _record_constraint_violations(self, candidates: List[SatelliteAccessCandidate]):
        """記錄約束違反統計"""
        for candidate in candidates:
            for constraint in self.constraints:
                if not constraint.is_hard_constraint:
                    continue
                
                if not self._evaluate_hard_constraint(candidate, constraint):
                    count = self.constraint_violations.get(constraint.constraint_type, 0)
                    self.constraint_violations[constraint.constraint_type] = count + 1
    
    # === 管理和監控方法 ===
    
    def get_constraint_configuration(self) -> List[Dict]:
        """獲取約束配置"""
        return [
            {
                "type": constraint.constraint_type.value,
                "threshold": constraint.threshold_value,
                "weight": constraint.weight,
                "is_hard": constraint.is_hard_constraint,
                "description": constraint.description
            }
            for constraint in self.constraints
        ]
    
    def update_constraint(
        self,
        constraint_type: SatelliteConstraintType,
        threshold_value: Optional[float] = None,
        weight: Optional[float] = None,
        is_hard_constraint: Optional[bool] = None
    ):
        """更新約束配置"""
        for constraint in self.constraints:
            if constraint.constraint_type == constraint_type:
                if threshold_value is not None:
                    constraint.threshold_value = threshold_value
                if weight is not None:
                    constraint.weight = weight
                if is_hard_constraint is not None:
                    constraint.is_hard_constraint = is_hard_constraint
                break
    
    def get_performance_statistics(self) -> Dict:
        """獲取性能統計"""
        total_selections = len(self.selection_history)
        avg_score = sum(entry["selected_score"] for entry in self.selection_history) / total_selections if total_selections > 0 else 0
        
        return {
            "total_selections": total_selections,
            "average_selection_score": round(avg_score, 3),
            "current_satellite_loads": self.satellite_loads.copy(),
            "total_ue_assignments": len(self.ue_assignments),
            "constraint_violations": self.constraint_violations.copy(),
            "load_balance_ratio": self._calculate_load_balance_ratio()
        }
    
    def _calculate_load_balance_ratio(self) -> float:
        """計算負載平衡比率"""
        if not self.satellite_loads:
            return 1.0
        
        loads = list(self.satellite_loads.values())
        if not loads:
            return 1.0
        
        avg_load = sum(loads) / len(loads)
        max_load = max(loads)
        
        return avg_load / max_load if max_load > 0 else 1.0