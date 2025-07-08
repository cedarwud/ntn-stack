"""
負載篩選策略

基於衛星負載因子進行候選篩選。負載越低，可用資源越多，
因此優先選擇低負載的衛星以獲得更好的服務質量。
"""

import time
import math
from typing import List, Dict, Any

from .base_strategy import SelectionStrategy, StrategyParameters, StrategyResult
from ...interfaces.candidate_selector import Candidate, ProcessedEvent


class LoadStrategy(SelectionStrategy):
    """
    負載篩選策略
    
    根據衛星負載因子進行篩選和評分：
    - 負載越低，評分越高
    - 高於最大負載閾值的衛星被排除
    - 支援負載預測和趨勢分析
    - 考慮負載平衡和資源分配
    """
    
    def __init__(self):
        default_params = StrategyParameters(
            min_threshold=0.1,  # 最低負載評分閾值
            max_threshold=1.0,  # 最高負載評分閾值
            weight=1.0,         # 策略權重
            custom_params={
                "max_load_factor": 0.8,         # 最大可接受負載因子
                "optimal_load_factor": 0.3,     # 最佳負載因子
                "critical_load_factor": 0.95,   # 臨界負載因子
                "load_prediction_weight": 0.2,  # 負載預測權重
                "resource_efficiency_weight": 0.3, # 資源效率權重
                "load_balancing_consideration": True, # 是否考慮負載平衡
                "qos_degradation_threshold": 0.7,    # QoS降級閾值
                "congestion_avoidance": True     # 是否啟用擁塞避免
            }
        )
        
        super().__init__(
            name="load_strategy",
            description="基於衛星負載因子的候選篩選策略，優先選擇低負載高效率的衛星",
            default_params=default_params
        )
    
    def evaluate_candidate(self, candidate: Candidate, 
                          event: ProcessedEvent,
                          params: StrategyParameters = None) -> float:
        """
        評估候選衛星的負載分數
        
        Args:
            candidate: 候選衛星
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            float: 負載評分 (0.0-1.0)
        """
        effective_params = self.get_effective_parameters(params)
        
        if not effective_params.enabled:
            return 0.0
        
        custom_params = effective_params.custom_params
        load_factor = candidate.load_factor
        
        # 檢查是否超過臨界負載
        critical_load = custom_params.get("critical_load_factor", 0.95)
        if load_factor >= critical_load:
            return 0.0
        
        # 獲取參數
        max_load = custom_params.get("max_load_factor", 0.8)
        optimal_load = custom_params.get("optimal_load_factor", 0.3)
        prediction_weight = custom_params.get("load_prediction_weight", 0.2)
        efficiency_weight = custom_params.get("resource_efficiency_weight", 0.3)
        qos_threshold = custom_params.get("qos_degradation_threshold", 0.7)
        
        # 基礎負載評分計算 (負載越低分數越高)
        if load_factor <= optimal_load:
            base_score = 1.0  # 最高分數
        elif load_factor >= max_load:
            base_score = 0.1  # 最低可接受分數
        else:
            # 反向線性插值 (負載越高分數越低)
            base_score = 1.0 - (load_factor - optimal_load) / (max_load - optimal_load) * 0.9
        
        # QoS 降級考慮
        if load_factor >= qos_threshold:
            qos_penalty = (load_factor - qos_threshold) / (max_load - qos_threshold)
            base_score *= (1.0 - 0.5 * qos_penalty)  # 最多降低50%
        
        # 負載預測 (基於時間趨勢的簡化模型)
        predicted_score = base_score
        if prediction_weight > 0:
            # 基於事件類型預測負載變化
            event_type = event.event_type.upper()
            load_increase_prediction = 0.0
            
            if event_type in ['A4', 'HANDOVER']:
                # 換手事件會增加負載
                load_increase_prediction = 0.1
            elif event_type in ['D1', 'D2']:
                # 測量事件影響較小
                load_increase_prediction = 0.05
            
            # 考慮當前負載對預測的影響
            if load_factor > 0.5:
                load_increase_prediction *= 1.5  # 高負載時增長更快
            
            predicted_load = min(1.0, load_factor + load_increase_prediction)
            predicted_score = max(0.0, base_score - load_increase_prediction)
        
        # 資源效率評估
        efficiency_score = base_score
        if efficiency_weight > 0:
            # 基於負載和信號強度計算效率
            signal_normalized = (candidate.signal_strength + 120) / 40  # 假設信號範圍 -120 到 -80 dBm
            signal_normalized = max(0.0, min(1.0, signal_normalized))
            
            # 效率 = 信號質量 / 負載
            if load_factor > 0.1:
                efficiency = signal_normalized / load_factor
                efficiency_score = min(1.0, efficiency / 2.0)  # 正規化到 0-1
            else:
                efficiency_score = 1.0  # 極低負載給最高效率分數
        
        # 擁塞避免
        congestion_score = base_score
        if custom_params.get("congestion_avoidance", True):
            # 基於負載梯度避免擁塞
            if load_factor > 0.6:
                congestion_penalty = (load_factor - 0.6) / 0.4
                congestion_score *= (1.0 - 0.3 * congestion_penalty)
        
        # 綜合評分
        final_score = (
            (1 - prediction_weight - efficiency_weight) * base_score +
            prediction_weight * predicted_score +
            efficiency_weight * efficiency_score
        )
        
        # 應用擁塞避免
        final_score = min(final_score, congestion_score)
        
        # 確保分數在有效範圍內
        final_score = max(0.0, min(1.0, final_score))
        
        self.logger.debug(
            f"Load evaluation for {candidate.satellite_id}: "
            f"load={load_factor:.3f}, score={final_score:.3f}"
        )
        
        return final_score
    
    def filter_candidates(self, candidates: List[Candidate],
                         event: ProcessedEvent, 
                         params: StrategyParameters = None) -> StrategyResult:
        """
        根據負載因子篩選候選衛星
        
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
        load_stats = {"min": float('inf'), "max": 0.0, "avg": 0.0}
        
        if not effective_params.enabled:
            return StrategyResult(
                filtered_candidates=[],
                scores={},
                metadata={"strategy_disabled": True},
                strategy_name=self.name,
                execution_time_ms=0.0
            )
        
        # 評估所有候選者
        loads = []
        for candidate in candidates:
            score = self.evaluate_candidate(candidate, event, effective_params)
            scores[candidate.satellite_id] = score
            loads.append(candidate.load_factor)
            
            # 根據閾值篩選
            if effective_params.min_threshold <= score <= effective_params.max_threshold:
                filtered_candidates.append(candidate)
        
        # 計算統計信息
        if loads:
            load_stats = {
                "min": min(loads),
                "max": max(loads),
                "avg": sum(loads) / len(loads)
            }
        
        # 負載平衡考慮
        if effective_params.custom_params.get("load_balancing_consideration", True):
            filtered_candidates = self._apply_load_balancing(filtered_candidates, scores)
        
        # 按負載排序（低負載優先）
        filtered_candidates.sort(key=lambda c: c.load_factor)
        
        execution_time = (time.time() - start_time) * 1000
        
        metadata = {
            "total_candidates": len(candidates),
            "filtered_count": len(filtered_candidates),
            "load_stats": load_stats,
            "strategy_params": {
                "min_threshold": effective_params.min_threshold,
                "max_threshold": effective_params.max_threshold,
                "weight": effective_params.weight,
                "custom_params": effective_params.custom_params
            },
            "filtering_ratio": len(filtered_candidates) / len(candidates) if candidates else 0.0,
            "load_distribution": self._calculate_load_distribution(candidates),
            "efficiency_analysis": self._analyze_load_efficiency(candidates)
        }
        
        self.logger.info(
            f"Load filtering completed: {len(filtered_candidates)}/{len(candidates)} candidates passed, "
            f"load range: {load_stats['min']:.3f}-{load_stats['max']:.3f}"
        )
        
        return StrategyResult(
            filtered_candidates=filtered_candidates,
            scores=scores,
            metadata=metadata,
            strategy_name=self.name,
            execution_time_ms=execution_time
        )
    
    def _apply_load_balancing(self, candidates: List[Candidate], 
                            scores: Dict[str, float]) -> List[Candidate]:
        """
        應用負載平衡策略
        
        Args:
            candidates: 候選衛星列表
            scores: 評分字典
            
        Returns:
            List[Candidate]: 負載平衡後的候選列表
        """
        if len(candidates) <= 1:
            return candidates
        
        # 按負載分組
        low_load = [c for c in candidates if c.load_factor < 0.3]
        mid_load = [c for c in candidates if 0.3 <= c.load_factor < 0.6]
        high_load = [c for c in candidates if c.load_factor >= 0.6]
        
        # 優先選擇低負載，但保持一定的多樣性
        balanced_candidates = []
        
        # 取最好的低負載候選者
        if low_load:
            low_load.sort(key=lambda c: scores[c.satellite_id], reverse=True)
            balanced_candidates.extend(low_load[:max(1, len(low_load) // 2)])
        
        # 適量的中負載候選者
        if mid_load and len(balanced_candidates) < len(candidates) * 0.8:
            mid_load.sort(key=lambda c: scores[c.satellite_id], reverse=True)
            balanced_candidates.extend(mid_load[:max(1, len(mid_load) // 3)])
        
        # 少量高負載候選者（作為備選）
        if high_load and len(balanced_candidates) < len(candidates) * 0.9:
            high_load.sort(key=lambda c: scores[c.satellite_id], reverse=True)
            balanced_candidates.extend(high_load[:1])  # 只取最好的一個
        
        return balanced_candidates
    
    def _calculate_load_distribution(self, candidates: List[Candidate]) -> Dict[str, int]:
        """
        計算負載分佈
        
        Args:
            candidates: 候選衛星列表
            
        Returns:
            Dict[str, int]: 各負載等級的數量
        """
        distribution = {
            "very_low": 0,   # 0.0-0.2
            "low": 0,        # 0.2-0.4
            "medium": 0,     # 0.4-0.6
            "high": 0,       # 0.6-0.8
            "very_high": 0   # 0.8-1.0
        }
        
        for candidate in candidates:
            load = candidate.load_factor
            if load < 0.2:
                distribution["very_low"] += 1
            elif load < 0.4:
                distribution["low"] += 1
            elif load < 0.6:
                distribution["medium"] += 1
            elif load < 0.8:
                distribution["high"] += 1
            else:
                distribution["very_high"] += 1
        
        return distribution
    
    def _analyze_load_efficiency(self, candidates: List[Candidate]) -> Dict[str, float]:
        """
        分析負載效率
        
        Args:
            candidates: 候選衛星列表
            
        Returns:
            Dict[str, float]: 效率分析結果
        """
        if not candidates:
            return {}
        
        total_capacity = len(candidates)
        total_load = sum(c.load_factor for c in candidates)
        available_capacity = total_capacity - total_load
        
        efficiency_metrics = {
            "average_load": total_load / total_capacity,
            "utilization_rate": total_load / total_capacity,
            "available_capacity_ratio": available_capacity / total_capacity,
            "load_variance": self._calculate_load_variance(candidates),
            "efficiency_score": self._calculate_efficiency_score(candidates)
        }
        
        return efficiency_metrics
    
    def _calculate_load_variance(self, candidates: List[Candidate]) -> float:
        """計算負載方差"""
        if not candidates:
            return 0.0
        
        loads = [c.load_factor for c in candidates]
        mean_load = sum(loads) / len(loads)
        variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
        return variance
    
    def _calculate_efficiency_score(self, candidates: List[Candidate]) -> float:
        """計算整體效率分數"""
        if not candidates:
            return 0.0
        
        # 效率分數基於負載分佈的均勻性和整體利用率
        distribution = self._calculate_load_distribution(candidates)
        total = len(candidates)
        
        # 偏向低負載的分佈
        efficiency = (
            distribution["very_low"] * 1.0 +
            distribution["low"] * 0.8 +
            distribution["medium"] * 0.6 +
            distribution["high"] * 0.4 +
            distribution["very_high"] * 0.2
        ) / total if total > 0 else 0.0
        
        return efficiency
    
    def get_load_insights(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """
        獲取負載分佈洞察
        
        Args:
            candidates: 候選衛星列表
            
        Returns:
            Dict[str, Any]: 負載分析結果
        """
        if not candidates:
            return {"error": "No candidates provided"}
        
        loads = [c.load_factor for c in candidates]
        loads.sort()
        
        insights = {
            "total_count": len(candidates),
            "load_range": {
                "min": min(loads),
                "max": max(loads),
                "span": max(loads) - min(loads)
            },
            "distribution": {
                "mean": sum(loads) / len(loads),
                "median": loads[len(loads) // 2],
                "q1": loads[len(loads) // 4],
                "q3": loads[3 * len(loads) // 4]
            },
            "load_bands": self._calculate_load_distribution(candidates),
            "efficiency_analysis": self._analyze_load_efficiency(candidates),
            "recommendations": self._generate_load_recommendations(candidates)
        }
        
        return insights
    
    def _generate_load_recommendations(self, candidates: List[Candidate]) -> Dict[str, str]:
        """生成負載優化建議"""
        if not candidates:
            return {}
        
        avg_load = sum(c.load_factor for c in candidates) / len(candidates)
        high_load_count = len([c for c in candidates if c.load_factor > 0.7])
        
        recommendations = {}
        
        if avg_load > 0.7:
            recommendations["overall"] = "整體負載較高，建議增加候選衛星數量或提高篩選閾值"
        elif avg_load < 0.3:
            recommendations["overall"] = "整體負載較低，可以考慮更積極的資源利用策略"
        
        if high_load_count > len(candidates) * 0.3:
            recommendations["capacity"] = "高負載衛星比例過高，建議擴展衛星池或優化負載分配"
        
        return recommendations