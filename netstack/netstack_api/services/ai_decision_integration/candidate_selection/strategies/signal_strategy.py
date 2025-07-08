"""
信號強度篩選策略

基於衛星信號強度進行候選篩選。信號強度越強，通信質量越好，
因此優先選擇信號強度高的衛星。
"""

import time
import math
from typing import List, Dict, Any

from .base_strategy import SelectionStrategy, StrategyParameters, StrategyResult
from ...interfaces.candidate_selector import Candidate, ProcessedEvent


class SignalStrategy(SelectionStrategy):
    """
    信號強度篩選策略
    
    根據衛星信號強度進行篩選和評分：
    - 信號強度越高，評分越高
    - 低於最小信號強度閾值的衛星被排除
    - 支援信號強度動態範圍調整
    - 考慮信號品質和穩定性
    """
    
    def __init__(self):
        default_params = StrategyParameters(
            min_threshold=0.2,  # 最低信號強度閾值
            max_threshold=1.0,  # 最高信號強度閾值  
            weight=1.0,         # 策略權重
            custom_params={
                "min_signal_dbm": -110.0,       # 最小可接受信號強度 (dBm)
                "optimal_signal_dbm": -80.0,    # 最佳信號強度 (dBm)
                "cutoff_signal_dbm": -120.0,    # 信號截止強度 (dBm)
                "signal_stability_weight": 0.3, # 信號穩定性權重
                "snr_consideration": True,       # 是否考慮信噪比
                "interference_compensation": True, # 是否補償干擾
                "dynamic_range_adjustment": True   # 是否動態調整範圍
            }
        )
        
        super().__init__(
            name="signal_strategy", 
            description="基於衛星信號強度的候選篩選策略，優先選擇信號強度高且穩定的衛星",
            default_params=default_params
        )
    
    def evaluate_candidate(self, candidate: Candidate, 
                          event: ProcessedEvent,
                          params: StrategyParameters = None) -> float:
        """
        評估候選衛星的信號強度分數
        
        Args:
            candidate: 候選衛星
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            float: 信號強度評分 (0.0-1.0)
        """
        effective_params = self.get_effective_parameters(params)
        
        if not effective_params.enabled:
            return 0.0
        
        custom_params = effective_params.custom_params
        signal_dbm = candidate.signal_strength
        
        # 檢查是否低於截止信號強度
        cutoff_signal = custom_params.get("cutoff_signal_dbm", -120.0)
        if signal_dbm < cutoff_signal:
            return 0.0
        
        # 獲取參數
        min_signal = custom_params.get("min_signal_dbm", -110.0)
        optimal_signal = custom_params.get("optimal_signal_dbm", -80.0)
        stability_weight = custom_params.get("signal_stability_weight", 0.3)
        consider_snr = custom_params.get("snr_consideration", True)
        interference_comp = custom_params.get("interference_compensation", True)
        
        # 基礎信號強度評分計算
        if signal_dbm <= min_signal:
            base_score = 0.1  # 最低可接受分數
        elif signal_dbm >= optimal_signal:
            base_score = 1.0  # 最高分數
        else:
            # 線性插值 (dBm 是對數尺度，但我們使用線性插值簡化)
            base_score = 0.1 + (signal_dbm - min_signal) / (optimal_signal - min_signal) * 0.9
        
        # 信號穩定性評估 (基於仰角和距離推算穩定性)
        stability_score = 1.0
        if stability_weight > 0:
            # 仰角越高，信號越穩定
            elevation_stability = min(1.0, candidate.elevation / 60.0)
            
            # 距離越近，信號越穩定 (假設最大距離為2000km)
            distance_stability = max(0.0, 1.0 - candidate.distance / 2000.0)
            
            # 綜合穩定性
            stability_score = 0.6 * elevation_stability + 0.4 * distance_stability
        
        # 結合穩定性
        combined_score = (1 - stability_weight) * base_score + stability_weight * base_score * stability_score
        
        # 信噪比考慮 (簡化模型)
        if consider_snr:
            # 基於仰角估算信噪比影響
            elevation_rad = math.radians(candidate.elevation)
            snr_factor = 0.8 + 0.2 * math.sin(elevation_rad)  # 仰角越高，SNR越好
            combined_score *= snr_factor
        
        # 干擾補償 (基於負載因子推算干擾)
        if interference_comp:
            # 負載因子越高，干擾越大
            interference_factor = max(0.5, 1.0 - 0.3 * candidate.load_factor)
            combined_score *= interference_factor
        
        # 確保分數在有效範圍內
        final_score = max(0.0, min(1.0, combined_score))
        
        self.logger.debug(
            f"Signal evaluation for {candidate.satellite_id}: "
            f"signal={signal_dbm:.1f}dBm, score={final_score:.3f}"
        )
        
        return final_score
    
    def filter_candidates(self, candidates: List[Candidate],
                         event: ProcessedEvent, 
                         params: StrategyParameters = None) -> StrategyResult:
        """
        根據信號強度篩選候選衛星
        
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
        signal_stats = {"min": float('inf'), "max": float('-inf'), "avg": 0.0}
        
        if not effective_params.enabled:
            return StrategyResult(
                filtered_candidates=[],
                scores={},
                metadata={"strategy_disabled": True},
                strategy_name=self.name,
                execution_time_ms=0.0
            )
        
        # 評估所有候選者
        signals = []
        for candidate in candidates:
            score = self.evaluate_candidate(candidate, event, effective_params)
            scores[candidate.satellite_id] = score
            signals.append(candidate.signal_strength)
            
            # 根據閾值篩選
            if effective_params.min_threshold <= score <= effective_params.max_threshold:
                filtered_candidates.append(candidate)
        
        # 計算統計信息
        if signals:
            signal_stats = {
                "min": min(signals),
                "max": max(signals),
                "avg": sum(signals) / len(signals)
            }
        
        # 動態範圍調整
        if effective_params.custom_params.get("dynamic_range_adjustment", True) and filtered_candidates:
            # 如果篩選後候選者太少，放寬閾值
            if len(filtered_candidates) < max(2, len(candidates) * 0.2):
                relaxed_threshold = effective_params.min_threshold * 0.8
                additional_candidates = []
                
                for candidate in candidates:
                    score = scores[candidate.satellite_id]
                    if relaxed_threshold <= score < effective_params.min_threshold:
                        additional_candidates.append(candidate)
                
                filtered_candidates.extend(additional_candidates)
                self.logger.info(f"Applied dynamic range adjustment, added {len(additional_candidates)} candidates")
        
        # 按信號強度排序（高信號優先）
        filtered_candidates.sort(key=lambda c: c.signal_strength, reverse=True)
        
        execution_time = (time.time() - start_time) * 1000
        
        metadata = {
            "total_candidates": len(candidates),
            "filtered_count": len(filtered_candidates),
            "signal_stats_dbm": signal_stats,
            "strategy_params": {
                "min_threshold": effective_params.min_threshold,
                "max_threshold": effective_params.max_threshold,
                "weight": effective_params.weight,
                "custom_params": effective_params.custom_params
            },
            "filtering_ratio": len(filtered_candidates) / len(candidates) if candidates else 0.0,
            "quality_distribution": self._calculate_signal_quality_distribution(candidates)
        }
        
        self.logger.info(
            f"Signal filtering completed: {len(filtered_candidates)}/{len(candidates)} candidates passed, "
            f"signal range: {signal_stats['min']:.1f}dBm to {signal_stats['max']:.1f}dBm"
        )
        
        return StrategyResult(
            filtered_candidates=filtered_candidates,
            scores=scores,
            metadata=metadata,
            strategy_name=self.name,
            execution_time_ms=execution_time
        )
    
    def _calculate_signal_quality_distribution(self, candidates: List[Candidate]) -> Dict[str, int]:
        """
        計算信號質量分佈
        
        Args:
            candidates: 候選衛星列表
            
        Returns:
            Dict[str, int]: 各質量等級的數量
        """
        distribution = {
            "excellent": 0,  # >= -80 dBm
            "good": 0,       # -90 to -80 dBm
            "fair": 0,       # -100 to -90 dBm
            "poor": 0,       # -110 to -100 dBm
            "very_poor": 0   # < -110 dBm
        }
        
        for candidate in candidates:
            signal = candidate.signal_strength
            if signal >= -80:
                distribution["excellent"] += 1
            elif signal >= -90:
                distribution["good"] += 1
            elif signal >= -100:
                distribution["fair"] += 1
            elif signal >= -110:
                distribution["poor"] += 1
            else:
                distribution["very_poor"] += 1
        
        return distribution
    
    def calculate_optimal_signal_threshold(self, candidates: List[Candidate], 
                                         target_count: int = None) -> float:
        """
        根據候選衛星分佈計算最佳信號強度閾值
        
        Args:
            candidates: 候選衛星列表
            target_count: 目標候選數量
            
        Returns:
            float: 建議的最小信號強度閾值
        """
        if not candidates:
            return self.default_params.min_threshold
        
        signals = [c.signal_strength for c in candidates]
        signals.sort(reverse=True)
        
        if target_count and target_count < len(signals):
            threshold_signal = signals[target_count - 1]
        else:
            # 使用75分位數作為閾值
            threshold_signal = signals[len(signals) // 4]
        
        # 轉換為評分閾值
        dummy_candidate = Candidate(
            satellite_id="dummy",
            elevation=30,
            signal_strength=threshold_signal,
            load_factor=0.5,
            distance=1000,
            azimuth=0,
            doppler_shift=0,
            position={},
            velocity={},
            visibility_time=0
        )
        
        dummy_event = ProcessedEvent(
            event_type="dummy",
            event_data={},
            timestamp=time.time(),
            confidence=1.0,
            trigger_conditions={}
        )
        
        return self.evaluate_candidate(dummy_candidate, dummy_event)
    
    def get_signal_insights(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """
        獲取信號強度分佈洞察
        
        Args:
            candidates: 候選衛星列表
            
        Returns:
            Dict[str, Any]: 信號分析結果
        """
        if not candidates:
            return {"error": "No candidates provided"}
        
        signals = [c.signal_strength for c in candidates]
        signals.sort(reverse=True)
        
        insights = {
            "total_count": len(candidates),
            "signal_range_dbm": {
                "min": min(signals),
                "max": max(signals),
                "span": max(signals) - min(signals)
            },
            "distribution": {
                "mean": sum(signals) / len(signals),
                "median": signals[len(signals) // 2],
                "q1": signals[len(signals) // 4],
                "q3": signals[3 * len(signals) // 4]
            },
            "quality_bands": self._calculate_signal_quality_distribution(candidates),
            "recommended_thresholds": {
                "conservative": signals[len(signals) // 10] if signals else -90,  # Top 10%
                "moderate": signals[len(signals) // 4] if signals else -95,       # Top 25%
                "aggressive": signals[len(signals) // 2] if signals else -100     # Top 50%
            }
        }
        
        return insights