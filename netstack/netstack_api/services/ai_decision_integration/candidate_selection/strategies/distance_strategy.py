"""
距離篩選策略

基於衛星距離進行候選篩選。距離越近，信號傳輸延遲越低，
因此優先選擇距離較近的衛星以獲得更低的延遲。
"""

import time
import math
from typing import List, Dict, Any

from .base_strategy import SelectionStrategy, StrategyParameters, StrategyResult
from ...interfaces.candidate_selector import Candidate, ProcessedEvent


class DistanceStrategy(SelectionStrategy):
    """
    距離篩選策略
    
    根據衛星距離進行篩選和評分：
    - 距離越近，評分越高
    - 考慮傳輸延遲和信號衰減
    - 支援動態距離閾值調整
    """
    
    def __init__(self):
        default_params = StrategyParameters(
            min_threshold=0.2,  # 最低距離評分閾值
            max_threshold=1.0,  # 最高距離評分閾值
            weight=1.0,         # 策略權重
            custom_params={
                "max_distance_km": 2000.0,      # 最大可接受距離 (km)
                "optimal_distance_km": 800.0,   # 最佳距離 (km)
                "min_distance_km": 500.0,       # 最小距離 (km)
                "latency_weight": 0.4,          # 延遲權重
                "signal_attenuation_weight": 0.3, # 信號衰減權重
                "doppler_consideration": True,   # 是否考慮都卜勒效應
                "propagation_model": "free_space" # 傳播模型
            }
        )
        
        super().__init__(
            name="distance_strategy",
            description="基於衛星距離的候選篩選策略，優先選擇距離適中的衛星以平衡延遲和信號質量",
            default_params=default_params
        )
    
    def evaluate_candidate(self, candidate: Candidate, 
                          event: ProcessedEvent,
                          params: StrategyParameters = None) -> float:
        """
        評估候選衛星的距離分數
        
        Args:
            candidate: 候選衛星
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            float: 距離評分 (0.0-1.0)
        """
        effective_params = self.get_effective_parameters(params)
        
        if not effective_params.enabled:
            return 0.0
        
        custom_params = effective_params.custom_params
        distance_km = candidate.distance
        
        # 獲取參數
        max_distance = custom_params.get("max_distance_km", 2000.0)
        optimal_distance = custom_params.get("optimal_distance_km", 800.0)
        min_distance = custom_params.get("min_distance_km", 500.0)
        latency_weight = custom_params.get("latency_weight", 0.4)
        attenuation_weight = custom_params.get("signal_attenuation_weight", 0.3)
        consider_doppler = custom_params.get("doppler_consideration", True)
        
        # 檢查是否超過最大距離
        if distance_km > max_distance:
            return 0.0
        
        # 基礎距離評分計算
        if distance_km <= min_distance:
            # 距離太近可能有其他問題（如強烈的都卜勒效應）
            base_score = 0.7
        elif distance_km <= optimal_distance:
            # 最佳距離範圍
            base_score = 0.7 + 0.3 * (optimal_distance - distance_km) / (optimal_distance - min_distance)
        else:
            # 超過最佳距離，評分下降
            base_score = 0.1 + 0.6 * (max_distance - distance_km) / (max_distance - optimal_distance)
        
        # 延遲考慮 (光速 299,792,458 m/s)
        latency_score = base_score
        if latency_weight > 0:
            # 計算單程傳輸延遲 (ms)
            latency_ms = distance_km / 299.792458  # km -> ms
            # 正規化延遲分數 (假設最大可接受延遲為10ms)
            max_latency_ms = max_distance / 299.792458
            latency_score = max(0.0, 1.0 - latency_ms / max_latency_ms)
        
        # 信號衰減考慮
        attenuation_score = base_score
        if attenuation_weight > 0:
            # 自由空間路徑損耗 (簡化模型)
            # FSPL = 20*log10(d) + 20*log10(f) + 32.44
            # 這裡只考慮距離相關部分
            if distance_km > 0:
                # 正規化衰減分數
                attenuation_factor = min_distance / distance_km
                attenuation_score = min(1.0, attenuation_factor)
        
        # 都卜勒效應考慮
        doppler_score = base_score
        if consider_doppler and hasattr(candidate, 'doppler_shift'):
            # 都卜勒頻移越小越好
            doppler_hz = abs(candidate.doppler_shift)
            max_doppler = 50000  # 假設最大都卜勒頻移 50kHz
            doppler_score = max(0.0, 1.0 - doppler_hz / max_doppler)
        
        # 綜合評分
        final_score = (
            (1 - latency_weight - attenuation_weight) * base_score +
            latency_weight * latency_score +
            attenuation_weight * attenuation_score
        )
        
        # 如果考慮都卜勒，進一步調整分數
        if consider_doppler:
            final_score = 0.7 * final_score + 0.3 * doppler_score
        
        # 確保分數在有效範圍內
        final_score = max(0.0, min(1.0, final_score))
        
        self.logger.debug(
            f"Distance evaluation for {candidate.satellite_id}: "
            f"distance={distance_km:.1f}km, score={final_score:.3f}"
        )
        
        return final_score
    
    def filter_candidates(self, candidates: List[Candidate],
                         event: ProcessedEvent, 
                         params: StrategyParameters = None) -> StrategyResult:
        """
        根據距離篩選候選衛星
        
        Args:
            candidates: 候選衛星列表
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            StrategyResult: 篩選結果
        """
        start_time = time.time()
        effective_params = self.get_effective_parameters(params)
        
        scores = {}
        filtered_candidates = []
        distance_stats = {"min": float('inf'), "max": 0.0, "avg": 0.0}
        
        if not effective_params.enabled:
            return StrategyResult(
                filtered_candidates=[],
                scores={},
                metadata={"strategy_disabled": True},
                strategy_name=self.name,
                execution_time_ms=0.0
            )
        
        # 評估所有候選者
        distances = []
        for candidate in candidates:
            score = self.evaluate_candidate(candidate, event, effective_params)
            scores[candidate.satellite_id] = score
            distances.append(candidate.distance)
            
            # 根據閾值篩選
            if effective_params.min_threshold <= score <= effective_params.max_threshold:
                filtered_candidates.append(candidate)
        
        # 計算統計信息
        if distances:
            distance_stats = {
                "min": min(distances),
                "max": max(distances),
                "avg": sum(distances) / len(distances)
            }
        
        # 按距離排序（近距離優先，但考慮評分）
        filtered_candidates.sort(key=lambda c: (-scores[c.satellite_id], c.distance))
        
        execution_time = (time.time() - start_time) * 1000
        
        metadata = {
            "total_candidates": len(candidates),
            "filtered_count": len(filtered_candidates),
            "distance_stats_km": distance_stats,
            "strategy_params": {
                "min_threshold": effective_params.min_threshold,
                "max_threshold": effective_params.max_threshold,
                "weight": effective_params.weight,
                "custom_params": effective_params.custom_params
            },
            "filtering_ratio": len(filtered_candidates) / len(candidates) if candidates else 0.0,
            "latency_analysis": self._calculate_latency_distribution(candidates),
            "distance_distribution": self._calculate_distance_distribution(candidates)
        }
        
        self.logger.info(
            f"Distance filtering completed: {len(filtered_candidates)}/{len(candidates)} candidates passed, "
            f"distance range: {distance_stats['min']:.1f}km to {distance_stats['max']:.1f}km"
        )
        
        return StrategyResult(
            filtered_candidates=filtered_candidates,
            scores=scores,
            metadata=metadata,
            strategy_name=self.name,
            execution_time_ms=execution_time
        )
    
    def _calculate_latency_distribution(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """計算延遲分佈"""
        if not candidates:
            return {}
        
        latencies = [c.distance / 299.792458 for c in candidates]  # km -> ms
        
        return {
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "latency_bands": {
                "excellent": len([l for l in latencies if l < 2.0]),    # < 2ms
                "good": len([l for l in latencies if 2.0 <= l < 4.0]),  # 2-4ms
                "acceptable": len([l for l in latencies if 4.0 <= l < 6.0]),  # 4-6ms
                "poor": len([l for l in latencies if l >= 6.0])         # >= 6ms
            }
        }
    
    def _calculate_distance_distribution(self, candidates: List[Candidate]) -> Dict[str, int]:
        """計算距離分佈"""
        distribution = {
            "very_close": 0,    # < 600km
            "close": 0,         # 600-1000km
            "medium": 0,        # 1000-1400km
            "far": 0,          # 1400-1800km
            "very_far": 0      # > 1800km
        }
        
        for candidate in candidates:
            distance = candidate.distance
            if distance < 600:
                distribution["very_close"] += 1
            elif distance < 1000:
                distribution["close"] += 1
            elif distance < 1400:
                distribution["medium"] += 1
            elif distance < 1800:
                distribution["far"] += 1
            else:
                distribution["very_far"] += 1
        
        return distribution