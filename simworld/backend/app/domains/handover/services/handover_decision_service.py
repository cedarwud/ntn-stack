#!/usr/bin/env python3
"""
階段二 2.2 - 切換決策服務整合

增強切換決策功能：
1. 切換觸發條件判斷
2. 多衛星切換策略
3. 切換成本估算

整合 NetStack 同步演算法與 SimWorld 模擬，提供智能切換決策
"""

import asyncio
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import math

import httpx
import structlog

from .fine_grained_sync_service import FineGrainedSyncService, SatelliteCandidate, TwoPointPredictionResult
from ..models.simple_handover_models import HandoverPredictionRecord
from ...satellite.services.enhanced_orbit_prediction_service import (
    EnhancedOrbitPredictionService,
    UECoverageInfo,
    CoverageResult,
    BinarySearchPrediction
)
from ...coordinates.models.coordinate_model import GeoCoordinate

logger = structlog.get_logger(__name__)


class HandoverTrigger(Enum):
    """切換觸發條件類型"""
    SIGNAL_DEGRADATION = "signal_degradation"      # 信號品質劣化
    BETTER_SATELLITE = "better_satellite"           # 更佳衛星可用
    PREDICTED_OUTAGE = "predicted_outage"           # 預測服務中斷
    LOAD_BALANCING = "load_balancing"               # 負載平衡
    EMERGENCY_HANDOVER = "emergency_handover"       # 緊急切換
    PROACTIVE_HANDOVER = "proactive_handover"       # 預測性切換


class HandoverStrategy(Enum):
    """切換策略類型"""
    REACTIVE = "reactive"                           # 反應式切換
    PREDICTIVE = "predictive"                       # 預測式切換
    MAKE_BEFORE_BREAK = "make_before_break"         # 先建後斷
    BREAK_BEFORE_MAKE = "break_before_make"         # 先斷後建
    SOFT_HANDOVER = "soft_handover"                 # 軟切換
    HARD_HANDOVER = "hard_handover"                 # 硬切換


@dataclass
class HandoverTriggerCondition:
    """切換觸發條件"""
    trigger_type: HandoverTrigger
    threshold_value: float
    current_value: float
    priority: int
    description: str
    triggered: bool = False
    trigger_time: Optional[datetime] = None


@dataclass
class HandoverCandidate:
    """切換候選衛星"""
    satellite_id: str
    satellite_name: str
    coverage_info: UECoverageInfo
    handover_cost: float
    switching_latency_ms: float
    signal_quality_improvement: float
    load_factor: float
    priority_score: float
    strategy: HandoverStrategy


@dataclass
class HandoverDecision:
    """切換決策結果"""
    ue_id: str
    source_satellite_id: str
    target_satellite_id: str
    
    # 決策詳情
    decision_time: datetime
    handover_trigger: HandoverTrigger
    handover_strategy: HandoverStrategy
    expected_handover_time: datetime
    
    # 評估指標
    handover_cost: float
    expected_latency_ms: float
    signal_improvement_db: float
    success_probability: float
    
    # 決策理由
    decision_reason: str
    alternative_candidates: List[HandoverCandidate]
    confidence_score: float


@dataclass
class MultiSatelliteHandover:
    """多衛星切換場景"""
    ue_id: str
    current_satellite: str
    available_satellites: List[str]
    handover_sequence: List[Tuple[str, str, float]]  # (source, target, time)
    total_handover_cost: float
    optimization_strategy: str


class HandoverDecisionService:
    """切換決策服務"""
    
    def __init__(
        self,
        enhanced_orbit_service: Optional[EnhancedOrbitPredictionService] = None,
        fine_grained_service: Optional[FineGrainedSyncService] = None,
        netstack_api_base_url: str = "http://localhost:8080"
    ):
        self.logger = logger.bind(service="handover_decision")
        
        # 服務依賴
        self.enhanced_orbit_service = enhanced_orbit_service or EnhancedOrbitPredictionService()
        self.fine_grained_service = fine_grained_service or FineGrainedSyncService()
        self.netstack_api_base_url = netstack_api_base_url
        
        # 切換決策配置
        self.signal_threshold_db = -90.0        # 信號強度閾值
        self.elevation_threshold_deg = 15.0     # 仰角閾值  
        self.quality_improvement_threshold = 5.0 # 品質改善閾值 (dB)
        self.max_handover_latency_ms = 50.0     # 最大切換延遲
        self.load_balance_threshold = 0.8       # 負載平衡閾值
        
        # 切換成本權重
        self.cost_weights = {
            "latency": 0.4,        # 延遲成本
            "signaling": 0.2,      # 信令成本
            "resources": 0.2,      # 資源成本
            "disruption": 0.2      # 服務中斷成本
        }
        
        # 統計資訊
        self.decision_stats = {
            "total_decisions": 0,
            "successful_handovers": 0,
            "failed_handovers": 0,
            "average_decision_time_ms": 0.0,
            "trigger_distribution": {trigger.value: 0 for trigger in HandoverTrigger},
            "strategy_usage": {strategy.value: 0 for strategy in HandoverStrategy}
        }
        
        # 決策緩存
        self._decision_cache: Dict[str, HandoverDecision] = {}
        self._trigger_history: Dict[str, List[HandoverTriggerCondition]] = {}
        
        self.logger.info(
            "切換決策服務初始化完成",
            signal_threshold=self.signal_threshold_db,
            elevation_threshold=self.elevation_threshold_deg,
            max_latency=self.max_handover_latency_ms
        )
    
    async def evaluate_handover_triggers(
        self,
        ue_id: str,
        current_satellite_id: str,
        ue_position: GeoCoordinate,
        current_time: datetime
    ) -> List[HandoverTriggerCondition]:
        """
        評估切換觸發條件
        
        檢查各種可能的切換觸發條件，判斷是否需要進行切換
        """
        triggers = []
        
        try:
            # 獲取當前衛星覆蓋資訊
            current_coverage = await self.enhanced_orbit_service.check_ue_satellite_coverage(
                ue_id=ue_id,
                satellite_id=current_satellite_id,
                ue_position=ue_position,
                check_time=current_time
            )
            
            # 1. 信號品質劣化檢查
            signal_trigger = self._check_signal_degradation(current_coverage)
            if signal_trigger:
                triggers.append(signal_trigger)
            
            # 2. 仰角過低檢查
            elevation_trigger = self._check_elevation_threshold(current_coverage)
            if elevation_trigger:
                triggers.append(elevation_trigger)
            
            # 3. 預測服務中斷檢查
            outage_trigger = await self._check_predicted_outage(
                ue_id, current_satellite_id, ue_position, current_time
            )
            if outage_trigger:
                triggers.append(outage_trigger)
            
            # 4. 更佳衛星可用性檢查
            better_satellite_trigger = await self._check_better_satellite_available(
                ue_id, current_satellite_id, ue_position, current_time, current_coverage
            )
            if better_satellite_trigger:
                triggers.append(better_satellite_trigger)
            
            # 5. 負載平衡檢查
            load_trigger = await self._check_load_balancing(current_satellite_id)
            if load_trigger:
                triggers.append(load_trigger)
            
            # 記錄觸發歷史
            if ue_id not in self._trigger_history:
                self._trigger_history[ue_id] = []
            
            for trigger in triggers:
                if trigger.triggered:
                    trigger.trigger_time = current_time
                    self._trigger_history[ue_id].append(trigger)
            
            self.logger.info(
                "切換觸發條件評估完成",
                ue_id=ue_id,
                current_satellite=current_satellite_id,
                triggers_found=len([t for t in triggers if t.triggered])
            )
            
            return triggers
            
        except Exception as e:
            self.logger.error(
                "切換觸發條件評估失敗",
                ue_id=ue_id,
                current_satellite=current_satellite_id,
                error=str(e)
            )
            return []
    
    def _check_signal_degradation(self, coverage: UECoverageInfo) -> Optional[HandoverTriggerCondition]:
        """檢查信號品質劣化"""
        trigger = HandoverTriggerCondition(
            trigger_type=HandoverTrigger.SIGNAL_DEGRADATION,
            threshold_value=self.signal_threshold_db,
            current_value=coverage.signal_strength_estimate * 100 - 100,  # 轉換為 dBm
            priority=8,
            description=f"信號強度 {coverage.signal_strength_estimate * 100 - 100:.1f}dBm 低於閾值 {self.signal_threshold_db}dBm"
        )
        
        trigger.triggered = trigger.current_value < trigger.threshold_value
        return trigger if trigger.triggered else None
    
    def _check_elevation_threshold(self, coverage: UECoverageInfo) -> Optional[HandoverTriggerCondition]:
        """檢查仰角閾值"""
        trigger = HandoverTriggerCondition(
            trigger_type=HandoverTrigger.PREDICTED_OUTAGE,
            threshold_value=self.elevation_threshold_deg,
            current_value=coverage.elevation_angle_deg,
            priority=9,
            description=f"仰角 {coverage.elevation_angle_deg:.1f}° 低於閾值 {self.elevation_threshold_deg}°"
        )
        
        trigger.triggered = trigger.current_value < trigger.threshold_value
        return trigger if trigger.triggered else None
    
    async def _check_predicted_outage(
        self,
        ue_id: str,
        satellite_id: str,
        ue_position: GeoCoordinate,
        current_time: datetime
    ) -> Optional[HandoverTriggerCondition]:
        """檢查預測服務中斷"""
        try:
            # 使用二分搜尋預測未來覆蓋情況
            future_time = current_time + timedelta(seconds=30)
            
            prediction = await self.enhanced_orbit_service.binary_search_handover_prediction(
                ue_id=ue_id,
                source_satellite_id=satellite_id,
                target_satellite_id="dummy_target",
                ue_position=ue_position,
                search_start_time=current_time,
                search_end_time=future_time,
                precision_seconds=1.0
            )
            
            # 如果信心度低，表示可能有服務中斷風險
            if prediction.confidence_score < 0.6:
                trigger = HandoverTriggerCondition(
                    trigger_type=HandoverTrigger.PREDICTED_OUTAGE,
                    threshold_value=0.6,
                    current_value=prediction.confidence_score,
                    priority=10,
                    description=f"預測信心度 {prediction.confidence_score:.2f} 低於閾值，可能發生服務中斷"
                )
                trigger.triggered = True
                return trigger
            
        except Exception as e:
            self.logger.warning("預測服務中斷檢查失敗", error=str(e))
        
        return None
    
    async def _check_better_satellite_available(
        self,
        ue_id: str,
        current_satellite_id: str,
        ue_position: GeoCoordinate,
        current_time: datetime,
        current_coverage: UECoverageInfo
    ) -> Optional[HandoverTriggerCondition]:
        """檢查是否有更佳衛星可用"""
        try:
            # 使用 FineGrainedSyncService 找到最佳衛星
            best_satellite = await self.fine_grained_service.calculate_best_satellite(
                ue_position=(ue_position.latitude, ue_position.longitude, ue_position.altitude or 0.0),
                timestamp=current_time.timestamp()
            )
            
            # 如果最佳衛星不是當前衛星，且品質顯著更好
            signal_improvement = best_satellite.signal_strength - (current_coverage.signal_strength_estimate * 100 - 100)
            if (best_satellite.satellite_id != current_satellite_id and
                signal_improvement > self.quality_improvement_threshold):
                
                trigger = HandoverTriggerCondition(
                    trigger_type=HandoverTrigger.BETTER_SATELLITE,
                    threshold_value=self.quality_improvement_threshold,
                    current_value=signal_improvement,
                    priority=6,
                    description=f"衛星 {best_satellite.satellite_id} 信號品質更佳 (+{signal_improvement:.1f}dB)"
                )
                trigger.triggered = True
                return trigger
                
        except Exception as e:
            self.logger.warning("更佳衛星檢查失敗", error=str(e))
        
        return None
    
    async def _check_load_balancing(self, satellite_id: str) -> Optional[HandoverTriggerCondition]:
        """檢查負載平衡需求"""
        current_load = 0.5  # 預設負載
        
        try:
            # 查詢 NetStack API 獲取衛星負載資訊
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.netstack_api_base_url}/api/satellite/{satellite_id}/load",
                    timeout=3.0
                )
                
                if response.status_code == 200:
                    load_data = response.json()
                    current_load = load_data.get("load_factor", 0.5)
                        
        except Exception as e:
            # API 不可用時使用模擬負載因子
            current_load = 0.3 + (hash(satellite_id) % 60) / 100.0  # 0.3-0.9範圍
            self.logger.debug("使用模擬負載因子", satellite_id=satellite_id, load=current_load)
        
        # 檢查是否超過負載閾值
        if current_load > self.load_balance_threshold:
            trigger = HandoverTriggerCondition(
                trigger_type=HandoverTrigger.LOAD_BALANCING,
                threshold_value=self.load_balance_threshold,
                current_value=current_load,
                priority=4,
                description=f"衛星負載 {current_load:.2f} 超過閾值 {self.load_balance_threshold}"
            )
            trigger.triggered = True
            return trigger
        
        return None
    
    async def generate_handover_candidates(
        self,
        ue_id: str,
        current_satellite_id: str,
        ue_position: GeoCoordinate,
        current_time: datetime,
        triggers: List[HandoverTriggerCondition]
    ) -> List[HandoverCandidate]:
        """
        生成切換候選衛星列表
        
        基於觸發條件和當前環境，生成可能的切換目標衛星
        """
        candidates = []
        
        try:
            # 使用 FineGrainedSyncService 獲取可見衛星
            visible_satellites = self.fine_grained_service._generate_mock_visible_satellites(
                (ue_position.latitude, ue_position.longitude, ue_position.altitude or 0.0),
                current_time.timestamp()
            )
            
            for sat in visible_satellites:
                if sat.norad_id == current_satellite_id:
                    continue  # 跳過當前衛星
                
                # 獲取候選衛星的覆蓋資訊
                candidate_coverage = await self.enhanced_orbit_service.check_ue_satellite_coverage(
                    ue_id=ue_id,
                    satellite_id=sat.norad_id,
                    ue_position=ue_position,
                    check_time=current_time
                )
                
                # 考慮所有可能的覆蓋狀態（除了 NOT_COVERED）
                # 包括 BLOCKED 和 MARGINAL，因為這些仍可能是可行的切換目標
                if candidate_coverage.coverage_result == CoverageResult.NOT_COVERED:
                    continue
                
                # 估算切換成本
                handover_cost = await self._estimate_handover_cost(
                    current_satellite_id, sat.norad_id, triggers
                )
                
                # 估算切換延遲
                switching_latency = self._estimate_switching_latency(triggers)
                
                # 計算信號品質改善
                current_signal = candidate_coverage.signal_strength_estimate * 100 - 100  # 轉為 dBm
                signal_improvement = max(0, current_signal - (-80.0))  # 假設當前 -80dBm
                
                # 獲取負載因子
                load_factor = await self._get_satellite_load_factor(sat.norad_id)
                
                # 選擇切換策略
                strategy = self._select_handover_strategy(triggers, candidate_coverage)
                
                # 計算優先級評分
                priority_score = self._calculate_candidate_priority(
                    candidate_coverage, handover_cost, signal_improvement, load_factor
                )
                
                candidate = HandoverCandidate(
                    satellite_id=sat.norad_id,
                    satellite_name=sat.name,
                    coverage_info=candidate_coverage,
                    handover_cost=handover_cost,
                    switching_latency_ms=switching_latency,
                    signal_quality_improvement=signal_improvement,
                    load_factor=load_factor,
                    priority_score=priority_score,
                    strategy=strategy
                )
                
                candidates.append(candidate)
            
            # 按優先級排序
            candidates.sort(key=lambda c: c.priority_score, reverse=True)
            
            self.logger.info(
                "切換候選衛星生成完成",
                ue_id=ue_id,
                current_satellite=current_satellite_id,
                candidates_found=len(candidates)
            )
            
            return candidates[:5]  # 返回前5個候選
            
        except Exception as e:
            self.logger.error(
                "切換候選衛星生成失敗",
                ue_id=ue_id,
                error=str(e)
            )
            return []
    
    async def _estimate_handover_cost(
        self,
        source_satellite_id: str,
        target_satellite_id: str,
        triggers: List[HandoverTriggerCondition]
    ) -> float:
        """估算切換成本"""
        total_cost = 0.0
        
        try:
            # 基礎成本根據衛星對差異化
            satellite_distance_factor = hash(f"{source_satellite_id}:{target_satellite_id}") % 100 / 100.0
            
            # 延遲成本 (10-30範圍)
            latency_cost = 15.0 + (satellite_distance_factor * 15.0)
            
            # 根據觸發條件調整延遲成本
            for trigger in triggers:
                if trigger.trigger_type == HandoverTrigger.EMERGENCY_HANDOVER:
                    latency_cost *= 0.6  # 緊急切換降低延遲成本權重
                elif trigger.trigger_type == HandoverTrigger.PREDICTED_OUTAGE:
                    latency_cost *= 0.8  # 預測性切換有準備時間
                elif trigger.trigger_type == HandoverTrigger.LOAD_BALANCING:
                    latency_cost *= 1.2  # 負載平衡切換增加成本
            
            # 信令成本 (8-20範圍)
            signaling_cost = 10.0 + (satellite_distance_factor * 10.0)
            
            # 資源成本 (5-15範圍)
            resource_cost = 8.0 + (satellite_distance_factor * 7.0)
            
            # 服務中斷成本 (15-35範圍)
            disruption_cost = 20.0 + (satellite_distance_factor * 15.0)
            
            # 根據觸發條件調整中斷成本
            for trigger in triggers:
                if trigger.trigger_type == HandoverTrigger.PREDICTED_OUTAGE:
                    disruption_cost *= 0.7  # 預測性切換降低中斷成本
                elif trigger.trigger_type == HandoverTrigger.EMERGENCY_HANDOVER:
                    disruption_cost *= 1.4  # 緊急切換增加中斷風險
                elif trigger.trigger_type == HandoverTrigger.BETTER_SATELLITE:
                    disruption_cost *= 0.9  # 主動切換略降低中斷成本
            
            # 計算加權總成本
            total_cost = (
                latency_cost * self.cost_weights["latency"] +
                signaling_cost * self.cost_weights["signaling"] +
                resource_cost * self.cost_weights["resources"] +
                disruption_cost * self.cost_weights["disruption"]
            )
            
        except Exception as e:
            self.logger.warning("切換成本估算失敗", error=str(e))
            total_cost = 50.0  # 預設成本
        
        return total_cost
    
    def _estimate_switching_latency(self, triggers: List[HandoverTriggerCondition]) -> float:
        """估算切換延遲"""
        base_latency = 30.0  # 基礎切換延遲 (ms)
        
        # 根據觸發條件調整延遲
        for trigger in triggers:
            if trigger.trigger_type == HandoverTrigger.EMERGENCY_HANDOVER:
                base_latency *= 0.8  # 緊急切換優先處理
            elif trigger.trigger_type == HandoverTrigger.PREDICTED_OUTAGE:
                base_latency *= 0.9  # 預測性切換有準備時間
        
        return min(base_latency, self.max_handover_latency_ms)
    
    async def _get_satellite_load_factor(self, satellite_id: str) -> float:
        """獲取衛星負載因子"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.netstack_api_base_url}/api/satellite/{satellite_id}/load",
                    timeout=3.0
                )
                
                if response.status_code == 200:
                    load_data = response.json()
                    return load_data.get("load_factor", 0.5)
                    
        except Exception:
            pass  # 忽略錯誤，使用預設值
        
        # 預設負載因子（基於衛星 ID 的模擬值）
        return 0.3 + (hash(satellite_id) % 50) / 100.0
    
    def _select_handover_strategy(
        self,
        triggers: List[HandoverTriggerCondition],
        coverage: UECoverageInfo
    ) -> HandoverStrategy:
        """選擇切換策略"""
        # 根據觸發條件選擇策略
        for trigger in triggers:
            if trigger.trigger_type == HandoverTrigger.EMERGENCY_HANDOVER:
                return HandoverStrategy.HARD_HANDOVER
            elif trigger.trigger_type == HandoverTrigger.PREDICTED_OUTAGE:
                return HandoverStrategy.MAKE_BEFORE_BREAK
            elif trigger.trigger_type == HandoverTrigger.BETTER_SATELLITE:
                return HandoverStrategy.SOFT_HANDOVER
        
        # 根據信號品質選擇策略
        if coverage.signal_strength_estimate > 0.7:
            return HandoverStrategy.SOFT_HANDOVER
        else:
            return HandoverStrategy.PREDICTIVE
    
    def _calculate_candidate_priority(
        self,
        coverage: UECoverageInfo,
        handover_cost: float,
        signal_improvement: float,
        load_factor: float
    ) -> float:
        """計算候選衛星優先級評分"""
        # 信號品質評分 (0-40分)
        signal_score = coverage.signal_strength_estimate * 40
        
        # 仰角評分 (0-30分)
        elevation_score = min(coverage.elevation_angle_deg / 90.0, 1.0) * 30
        
        # 成本評分 (0-20分，成本越低分數越高)
        cost_score = max(0, 20 - handover_cost * 0.4)
        
        # 負載評分 (0-10分，負載越低分數越高)
        load_score = (1.0 - load_factor) * 10
        
        return signal_score + elevation_score + cost_score + load_score
    
    async def make_handover_decision(
        self,
        ue_id: str,
        current_satellite_id: str,
        ue_position: GeoCoordinate,
        current_time: datetime
    ) -> Optional[HandoverDecision]:
        """
        做出切換決策
        
        綜合評估觸發條件和候選衛星，做出最終的切換決策
        """
        start_time = time.time()
        
        try:
            self.logger.info(
                "開始切換決策評估",
                ue_id=ue_id,
                current_satellite=current_satellite_id
            )
            
            # 1. 評估觸發條件
            triggers = await self.evaluate_handover_triggers(
                ue_id, current_satellite_id, ue_position, current_time
            )
            
            triggered_conditions = [t for t in triggers if t.triggered]
            if not triggered_conditions:
                self.logger.info("無觸發條件，無需切換", ue_id=ue_id)
                return None
            
            # 2. 生成候選衛星
            candidates = await self.generate_handover_candidates(
                ue_id, current_satellite_id, ue_position, current_time, triggered_conditions
            )
            
            if not candidates:
                self.logger.warning("無可用切換候選衛星", ue_id=ue_id)
                return None
            
            # 3. 選擇最佳候選
            best_candidate = candidates[0]  # 已按優先級排序
            
            # 4. 確定切換時機
            handover_time = await self._determine_handover_timing(
                ue_id, current_satellite_id, best_candidate, ue_position, current_time
            )
            
            # 5. 計算成功概率
            success_probability = self._calculate_success_probability(
                best_candidate, triggered_conditions
            )
            
            # 6. 生成決策理由
            decision_reason = self._generate_decision_reason(triggered_conditions, best_candidate)
            
            # 7. 創建決策結果
            decision = HandoverDecision(
                ue_id=ue_id,
                source_satellite_id=current_satellite_id,
                target_satellite_id=best_candidate.satellite_id,
                decision_time=current_time,
                handover_trigger=triggered_conditions[0].trigger_type,  # 主要觸發條件
                handover_strategy=best_candidate.strategy,
                expected_handover_time=handover_time,
                handover_cost=best_candidate.handover_cost,
                expected_latency_ms=best_candidate.switching_latency_ms,
                signal_improvement_db=best_candidate.signal_quality_improvement,
                success_probability=success_probability,
                decision_reason=decision_reason,
                alternative_candidates=candidates[1:4],  # 其他候選
                confidence_score=min(0.95, success_probability + 0.1)
            )
            
            # 8. 緩存決策
            self._decision_cache[ue_id] = decision
            
            # 9. 更新統計
            self._update_decision_stats(decision, time.time() - start_time)
            
            self.logger.info(
                "切換決策完成",
                ue_id=ue_id,
                target_satellite=best_candidate.satellite_id,
                strategy=best_candidate.strategy.value,
                success_probability=success_probability,
                decision_time_ms=(time.time() - start_time) * 1000
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(
                "切換決策失敗",
                ue_id=ue_id,
                current_satellite=current_satellite_id,
                error=str(e)
            )
            return None
    
    async def _determine_handover_timing(
        self,
        ue_id: str,
        source_satellite_id: str,
        candidate: HandoverCandidate,
        ue_position: GeoCoordinate,
        current_time: datetime
    ) -> datetime:
        """確定切換時機"""
        try:
            if candidate.strategy == HandoverStrategy.PREDICTIVE:
                # 預測性切換：使用二分搜尋找到最佳時機
                future_time = current_time + timedelta(seconds=60)
                
                prediction = await self.enhanced_orbit_service.binary_search_handover_prediction(
                    ue_id=ue_id,
                    source_satellite_id=source_satellite_id,
                    target_satellite_id=candidate.satellite_id,
                    ue_position=ue_position,
                    search_start_time=current_time,
                    search_end_time=future_time,
                    precision_seconds=0.1
                )
                
                return prediction.handover_time
            
            elif candidate.strategy in [HandoverStrategy.EMERGENCY_HANDOVER, HandoverStrategy.HARD_HANDOVER]:
                # 緊急或硬切換：立即執行
                return current_time + timedelta(milliseconds=candidate.switching_latency_ms)
            
            else:
                # 其他策略：預留準備時間
                return current_time + timedelta(seconds=5)
                
        except Exception as e:
            self.logger.debug("切換時機確定異常，使用預設時機", error=str(e))
            return current_time + timedelta(seconds=10)  # 預設延遲
    
    def _calculate_success_probability(
        self,
        candidate: HandoverCandidate,
        triggers: List[HandoverTriggerCondition]
    ) -> float:
        """計算切換成功概率"""
        base_probability = 0.85
        
        # 信號品質影響
        if candidate.coverage_info.signal_strength_estimate > 0.8:
            base_probability += 0.1
        elif candidate.coverage_info.signal_strength_estimate < 0.5:
            base_probability -= 0.1
        
        # 仰角影響
        if candidate.coverage_info.elevation_angle_deg > 45:
            base_probability += 0.05
        elif candidate.coverage_info.elevation_angle_deg < 20:
            base_probability -= 0.1
        
        # 觸發條件影響
        for trigger in triggers:
            if trigger.trigger_type == HandoverTrigger.EMERGENCY_HANDOVER:
                base_probability -= 0.05  # 緊急切換風險較高
            elif trigger.trigger_type == HandoverTrigger.PREDICTED_OUTAGE:
                base_probability += 0.05  # 預測性切換準備充分
        
        # 負載影響
        if candidate.load_factor < 0.5:
            base_probability += 0.05
        elif candidate.load_factor > 0.8:
            base_probability -= 0.05
        
        return max(0.1, min(0.99, base_probability))
    
    def _generate_decision_reason(
        self,
        triggers: List[HandoverTriggerCondition],
        candidate: HandoverCandidate
    ) -> str:
        """生成決策理由"""
        reasons = []
        
        for trigger in triggers:
            if trigger.triggered:
                reasons.append(trigger.description)
        
        reasons.append(f"選擇衛星 {candidate.satellite_name}，優先級評分 {candidate.priority_score:.1f}")
        reasons.append(f"預期信號改善 {candidate.signal_quality_improvement:.1f}dB")
        reasons.append(f"採用 {candidate.strategy.value} 策略")
        
        return "; ".join(reasons)
    
    def _update_decision_stats(self, decision: HandoverDecision, decision_time_seconds: float):
        """更新決策統計"""
        self.decision_stats["total_decisions"] += 1
        
        # 更新平均決策時間
        current_avg = self.decision_stats["average_decision_time_ms"]
        total_decisions = self.decision_stats["total_decisions"]
        new_time_ms = decision_time_seconds * 1000
        
        self.decision_stats["average_decision_time_ms"] = (
            (current_avg * (total_decisions - 1) + new_time_ms) / total_decisions
        )
        
        # 更新觸發條件分布
        trigger_key = decision.handover_trigger.value
        self.decision_stats["trigger_distribution"][trigger_key] += 1
        
        # 更新策略使用統計
        strategy_key = decision.handover_strategy.value
        self.decision_stats["strategy_usage"][strategy_key] += 1
    
    async def execute_multi_satellite_handover(
        self,
        ue_id: str,
        current_satellite_id: str,
        target_satellites: List[str],
        ue_position: GeoCoordinate,
        optimization_strategy: str = "minimize_cost"
    ) -> MultiSatelliteHandover:
        """
        執行多衛星切換優化
        
        在多個候選衛星中找到最佳的切換序列
        """
        try:
            self.logger.info(
                "開始多衛星切換優化",
                ue_id=ue_id,
                current_satellite=current_satellite_id,
                target_count=len(target_satellites)
            )
            
            if optimization_strategy == "minimize_cost":
                handover_sequence = await self._optimize_by_cost(
                    ue_id, current_satellite_id, target_satellites, ue_position
                )
            elif optimization_strategy == "minimize_latency":
                handover_sequence = await self._optimize_by_latency(
                    ue_id, current_satellite_id, target_satellites, ue_position
                )
            else:  # "balanced"
                handover_sequence = await self._optimize_balanced(
                    ue_id, current_satellite_id, target_satellites, ue_position
                )
            
            # 計算總切換成本
            total_cost = sum(cost for _, _, cost in handover_sequence)
            
            multi_handover = MultiSatelliteHandover(
                ue_id=ue_id,
                current_satellite=current_satellite_id,
                available_satellites=target_satellites,
                handover_sequence=handover_sequence,
                total_handover_cost=total_cost,
                optimization_strategy=optimization_strategy
            )
            
            self.logger.info(
                "多衛星切換優化完成",
                ue_id=ue_id,
                sequence_length=len(handover_sequence),
                total_cost=total_cost
            )
            
            return multi_handover
            
        except Exception as e:
            self.logger.error(
                "多衛星切換優化失敗",
                ue_id=ue_id,
                error=str(e)
            )
            raise
    
    async def _optimize_by_cost(
        self,
        ue_id: str,
        current_satellite_id: str,
        target_satellites: List[str],
        ue_position: GeoCoordinate
    ) -> List[Tuple[str, str, float]]:
        """按成本優化切換序列"""
        sequence = []
        source = current_satellite_id
        remaining_targets = target_satellites.copy()
        
        while remaining_targets:
            best_target = None
            min_cost = float('inf')
            
            for target in remaining_targets:
                cost = await self._estimate_handover_cost(source, target, [])
                if cost < min_cost:
                    min_cost = cost
                    best_target = target
            
            if best_target:
                sequence.append((source, best_target, min_cost))
                source = best_target
                remaining_targets.remove(best_target)
        
        return sequence
    
    async def _optimize_by_latency(
        self,
        ue_id: str,
        current_satellite_id: str,
        target_satellites: List[str],
        ue_position: GeoCoordinate
    ) -> List[Tuple[str, str, float]]:
        """按延遲優化切換序列"""
        sequence = []
        source = current_satellite_id
        remaining_targets = target_satellites.copy()
        
        while remaining_targets:
            best_target = None
            min_latency = float('inf')
            
            for target in remaining_targets:
                latency = self._estimate_switching_latency([])
                if latency < min_latency:
                    min_latency = latency
                    best_target = target
            
            if best_target:
                cost = await self._estimate_handover_cost(source, best_target, [])
                sequence.append((source, best_target, cost))
                source = best_target
                remaining_targets.remove(best_target)
        
        return sequence
    
    async def _optimize_balanced(
        self,
        ue_id: str,
        current_satellite_id: str,
        target_satellites: List[str],
        ue_position: GeoCoordinate
    ) -> List[Tuple[str, str, float]]:
        """平衡優化切換序列"""
        sequence = []
        source = current_satellite_id
        remaining_targets = target_satellites.copy()
        
        while remaining_targets:
            best_target = None
            best_score = -float('inf')
            
            for target in remaining_targets:
                cost = await self._estimate_handover_cost(source, target, [])
                latency = self._estimate_switching_latency([])
                
                # 平衡評分：成本和延遲各佔 50%
                score = -(cost * 0.5 + latency * 0.5)
                
                if score > best_score:
                    best_score = score
                    best_target = target
            
            if best_target:
                cost = await self._estimate_handover_cost(source, best_target, [])
                sequence.append((source, best_target, cost))
                source = best_target
                remaining_targets.remove(best_target)
        
        return sequence
    
    async def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        cache_info = {
            "decision_cache_size": len(self._decision_cache),
            "trigger_history_size": sum(len(history) for history in self._trigger_history.values())
        }
        
        return {
            "service_name": "HandoverDecisionService",
            "stage": "2.2",
            "capabilities": [
                "handover_trigger_evaluation",
                "multi_satellite_handover",
                "handover_cost_estimation"
            ],
            "configuration": {
                "signal_threshold_db": self.signal_threshold_db,
                "elevation_threshold_deg": self.elevation_threshold_deg,
                "max_handover_latency_ms": self.max_handover_latency_ms,
                "load_balance_threshold": self.load_balance_threshold
            },
            "statistics": self.decision_stats,
            "cache_info": cache_info,
            "cost_weights": self.cost_weights,
            "status": "active"
        }