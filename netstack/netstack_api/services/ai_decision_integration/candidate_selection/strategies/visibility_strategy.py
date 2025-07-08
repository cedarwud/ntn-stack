"""
可見性篩選策略

基於衛星可見時間進行候選篩選。可見時間越長，連接穩定性越好，
因此優先選擇可見時間較長的衛星以減少頻繁換手。
"""

import time
import math
from typing import List, Dict, Any

from .base_strategy import SelectionStrategy, StrategyParameters, StrategyResult
from ...interfaces.candidate_selector import Candidate, ProcessedEvent


class VisibilityStrategy(SelectionStrategy):
    """
    可見性篩選策略
    
    根據衛星可見時間進行篩選和評分：
    - 可見時間越長，評分越高
    - 考慮軌道特性和預測精度
    - 支援多時間窗口分析
    """
    
    def __init__(self):
        default_params = StrategyParameters(
            min_threshold=0.3,  # 最低可見性評分閾值
            max_threshold=1.0,  # 最高可見性評分閾值
            weight=1.0,         # 策略權重
            custom_params={
                "min_visibility_seconds": 120.0,   # 最小可見時間 (秒)
                "optimal_visibility_seconds": 600.0, # 最佳可見時間 (秒)
                "handover_preparation_time": 30.0,  # 換手準備時間 (秒)
                "prediction_accuracy_weight": 0.2,  # 預測精度權重
                "orbit_stability_weight": 0.3,     # 軌道穩定性權重
                "continuity_bonus": True,          # 是否給予連續性獎勵
                "weather_impact_consideration": False, # 是否考慮天氣影響
                "multi_window_analysis": True      # 是否進行多時間窗口分析
            }
        )
        
        super().__init__(
            name="visibility_strategy",
            description="基於衛星可見時間的候選篩選策略，優先選擇可見時間長且穩定的衛星",
            default_params=default_params
        )
    
    def evaluate_candidate(self, candidate: Candidate, 
                          event: ProcessedEvent,
                          params: StrategyParameters = None) -> float:
        """
        評估候選衛星的可見性分數
        
        Args:
            candidate: 候選衛星
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            float: 可見性評分 (0.0-1.0)
        """
        effective_params = self.get_effective_parameters(params)
        
        if not effective_params.enabled:
            return 0.0
        
        custom_params = effective_params.custom_params
        visibility_time = candidate.visibility_time
        
        # 獲取參數
        min_visibility = custom_params.get("min_visibility_seconds", 120.0)
        optimal_visibility = custom_params.get("optimal_visibility_seconds", 600.0)
        preparation_time = custom_params.get("handover_preparation_time", 30.0)
        accuracy_weight = custom_params.get("prediction_accuracy_weight", 0.2)
        stability_weight = custom_params.get("orbit_stability_weight", 0.3)
        continuity_bonus = custom_params.get("continuity_bonus", True)
        
        # 檢查最小可見時間要求
        if visibility_time < min_visibility:
            return 0.0
        
        # 基礎可見性評分計算
        if visibility_time >= optimal_visibility:
            base_score = 1.0  # 最高分數
        else:
            # 線性插值
            base_score = 0.1 + (visibility_time - min_visibility) / (optimal_visibility - min_visibility) * 0.9
        
        # 預測精度評估 (基於軌道參數的穩定性)
        prediction_score = base_score
        if accuracy_weight > 0:
            # 基於仰角變化率估算預測精度
            elevation = candidate.elevation
            distance = candidate.distance
            
            # 計算角速度 (簡化模型)
            if hasattr(candidate, 'velocity') and candidate.velocity:
                velocity_magnitude = math.sqrt(
                    candidate.velocity.get('vx', 0)**2 + 
                    candidate.velocity.get('vy', 0)**2 + 
                    candidate.velocity.get('vz', 0)**2
                )
                angular_velocity = velocity_magnitude / distance if distance > 0 else 0
                
                # 角速度越小，預測越準確
                max_angular_velocity = 0.01  # rad/s
                prediction_accuracy = max(0.0, 1.0 - angular_velocity / max_angular_velocity)
                prediction_score = base_score * (0.5 + 0.5 * prediction_accuracy)
        
        # 軌道穩定性評估
        stability_score = base_score
        if stability_weight > 0:
            # 基於仰角和距離評估穩定性
            elevation_stability = min(1.0, elevation / 45.0)  # 45度以上認為穩定
            
            # 距離穩定性 (中等距離最穩定)
            optimal_distance = 1000.0  # km
            distance_stability = max(0.0, 1.0 - abs(candidate.distance - optimal_distance) / optimal_distance)
            
            stability_score = base_score * (0.5 * elevation_stability + 0.5 * distance_stability)
        
        # 連續性獎勵
        continuity_score = base_score
        if continuity_bonus:
            # 如果可見時間遠超過最佳時間，給予額外獎勵
            if visibility_time > optimal_visibility * 1.5:
                continuity_multiplier = min(1.2, 1.0 + (visibility_time - optimal_visibility) / optimal_visibility * 0.1)
                continuity_score = base_score * continuity_multiplier
        
        # 換手準備時間考慮
        effective_visibility = max(0, visibility_time - preparation_time)
        if effective_visibility < min_visibility * 0.8:
            # 如果扣除準備時間後可見時間不足，降低評分
            preparation_penalty = 1.0 - (min_visibility * 0.8 - effective_visibility) / (min_visibility * 0.8)
            base_score *= max(0.1, preparation_penalty)
        
        # 綜合評分
        final_score = (
            (1 - accuracy_weight - stability_weight) * base_score +
            accuracy_weight * prediction_score +
            stability_weight * stability_score
        )
        
        # 應用連續性獎勵
        if continuity_bonus and continuity_score != base_score:
            final_score = min(1.0, final_score * (continuity_score / base_score))
        
        # 確保分數在有效範圍內
        final_score = max(0.0, min(1.0, final_score))
        
        self.logger.debug(
            f"Visibility evaluation for {candidate.satellite_id}: "
            f"visibility={visibility_time:.1f}s, score={final_score:.3f}"
        )
        
        return final_score
    
    def filter_candidates(self, candidates: List[Candidate],
                         event: ProcessedEvent, 
                         params: StrategyParameters = None) -> StrategyResult:
        """
        根據可見性篩選候選衛星
        
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
        visibility_stats = {"min": float('inf'), "max": 0.0, "avg": 0.0}
        
        if not effective_params.enabled:
            return StrategyResult(
                filtered_candidates=[],
                scores={},
                metadata={"strategy_disabled": True},
                strategy_name=self.name,
                execution_time_ms=0.0
            )
        
        # 評估所有候選者
        visibilities = []
        for candidate in candidates:
            score = self.evaluate_candidate(candidate, event, effective_params)
            scores[candidate.satellite_id] = score
            visibilities.append(candidate.visibility_time)
            
            # 根據閾值篩選
            if effective_params.min_threshold <= score <= effective_params.max_threshold:
                filtered_candidates.append(candidate)
        
        # 計算統計信息
        if visibilities:
            visibility_stats = {
                "min": min(visibilities),
                "max": max(visibilities),
                "avg": sum(visibilities) / len(visibilities)
            }
        
        # 多時間窗口分析
        if effective_params.custom_params.get("multi_window_analysis", True):
            filtered_candidates = self._apply_multi_window_analysis(filtered_candidates, scores)
        
        # 按可見時間排序（長可見時間優先）
        filtered_candidates.sort(key=lambda c: c.visibility_time, reverse=True)
        
        execution_time = (time.time() - start_time) * 1000
        
        metadata = {
            "total_candidates": len(candidates),
            "filtered_count": len(filtered_candidates),
            "visibility_stats_seconds": visibility_stats,
            "strategy_params": {
                "min_threshold": effective_params.min_threshold,
                "max_threshold": effective_params.max_threshold,
                "weight": effective_params.weight,
                "custom_params": effective_params.custom_params
            },
            "filtering_ratio": len(filtered_candidates) / len(candidates) if candidates else 0.0,
            "visibility_distribution": self._calculate_visibility_distribution(candidates),
            "handover_frequency_analysis": self._analyze_handover_frequency(candidates)
        }
        
        self.logger.info(
            f"Visibility filtering completed: {len(filtered_candidates)}/{len(candidates)} candidates passed, "
            f"visibility range: {visibility_stats['min']:.1f}s to {visibility_stats['max']:.1f}s"
        )
        
        return StrategyResult(
            filtered_candidates=filtered_candidates,
            scores=scores,
            metadata=metadata,
            strategy_name=self.name,
            execution_time_ms=execution_time
        )
    
    def _apply_multi_window_analysis(self, candidates: List[Candidate], 
                                   scores: Dict[str, float]) -> List[Candidate]:
        """
        應用多時間窗口分析
        
        Args:
            candidates: 候選衛星列表
            scores: 評分字典
            
        Returns:
            List[Candidate]: 多窗口分析後的候選列表
        """
        if len(candidates) <= 1:
            return candidates
        
        # 按可見時間分組
        short_visibility = [c for c in candidates if c.visibility_time < 300]   # < 5分鐘
        medium_visibility = [c for c in candidates if 300 <= c.visibility_time < 900]  # 5-15分鐘
        long_visibility = [c for c in candidates if c.visibility_time >= 900]   # >= 15分鐘
        
        # 優先選擇長可見時間，但保持一定的多樣性
        multi_window_candidates = []
        
        # 取最好的長可見時間候選者
        if long_visibility:
            long_visibility.sort(key=lambda c: scores[c.satellite_id], reverse=True)
            multi_window_candidates.extend(long_visibility[:max(1, len(long_visibility) // 2)])
        
        # 適量的中等可見時間候選者
        if medium_visibility and len(multi_window_candidates) < len(candidates) * 0.8:
            medium_visibility.sort(key=lambda c: scores[c.satellite_id], reverse=True)
            multi_window_candidates.extend(medium_visibility[:max(1, len(medium_visibility) // 2)])
        
        # 少量短可見時間候選者（作為緊急備選）
        if short_visibility and len(multi_window_candidates) < len(candidates) * 0.9:
            short_visibility.sort(key=lambda c: scores[c.satellite_id], reverse=True)
            multi_window_candidates.extend(short_visibility[:1])
        
        return multi_window_candidates
    
    def _calculate_visibility_distribution(self, candidates: List[Candidate]) -> Dict[str, int]:
        """計算可見性分佈"""
        distribution = {
            "very_short": 0,   # < 2分鐘
            "short": 0,        # 2-5分鐘
            "medium": 0,       # 5-10分鐘
            "long": 0,         # 10-20分鐘
            "very_long": 0     # > 20分鐘
        }
        
        for candidate in candidates:
            visibility = candidate.visibility_time
            if visibility < 120:
                distribution["very_short"] += 1
            elif visibility < 300:
                distribution["short"] += 1
            elif visibility < 600:
                distribution["medium"] += 1
            elif visibility < 1200:
                distribution["long"] += 1
            else:
                distribution["very_long"] += 1
        
        return distribution
    
    def _analyze_handover_frequency(self, candidates: List[Candidate]) -> Dict[str, float]:
        """分析換手頻率"""
        if not candidates:
            return {}
        
        # 估算每小時的換手次數
        visibilities = [c.visibility_time for c in candidates]
        avg_visibility = sum(visibilities) / len(visibilities)
        
        # 假設連續覆蓋，計算每小時換手次數
        handovers_per_hour = 3600 / avg_visibility if avg_visibility > 0 else float('inf')
        
        return {
            "average_visibility_seconds": avg_visibility,
            "estimated_handovers_per_hour": handovers_per_hour,
            "stability_rating": self._calculate_stability_rating(handovers_per_hour),
            "recommended_window_size": self._recommend_window_size(visibilities)
        }
    
    def _calculate_stability_rating(self, handovers_per_hour: float) -> str:
        """計算穩定性評級"""
        if handovers_per_hour <= 2:
            return "excellent"
        elif handovers_per_hour <= 4:
            return "good"
        elif handovers_per_hour <= 8:
            return "acceptable"
        elif handovers_per_hour <= 15:
            return "poor"
        else:
            return "very_poor"
    
    def _recommend_window_size(self, visibilities: List[float]) -> int:
        """推薦時間窗口大小"""
        if not visibilities:
            return 5
        
        avg_visibility = sum(visibilities) / len(visibilities)
        
        # 推薦窗口大小為平均可見時間的1.5倍
        recommended_size = max(3, min(10, int(avg_visibility / 120)))  # 轉換為分鐘並限制範圍
        
        return recommended_size
    
    def calculate_visibility_window(self, candidate: Candidate, 
                                  user_position: Dict[str, float]) -> float:
        """
        計算候選衛星的可見時間窗口
        
        Args:
            candidate: 候選衛星
            user_position: 用戶位置 {lat, lon, alt}
            
        Returns:
            float: 可見時間 (秒)
        """
        # 簡化的可見性計算模型
        # 實際實現中需要考慮軌道力學和地球遮擋
        
        elevation = candidate.elevation
        distance = candidate.distance
        
        # 基於仰角和距離的簡化可見性計算
        if elevation < 10:  # 低仰角
            return max(0, 60 + elevation * 10)  # 60-160秒
        elif elevation < 45:  # 中仰角
            return 180 + (elevation - 10) * 15  # 180-705秒
        else:  # 高仰角
            return 600 + (elevation - 45) * 10  # 600-1050秒
    
    def get_visibility_insights(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """
        獲取可見性分佈洞察
        
        Args:
            candidates: 候選衛星列表
            
        Returns:
            Dict[str, Any]: 可見性分析結果
        """
        if not candidates:
            return {"error": "No candidates provided"}
        
        visibilities = [c.visibility_time for c in candidates]
        visibilities.sort(reverse=True)
        
        insights = {
            "total_count": len(candidates),
            "visibility_range_seconds": {
                "min": min(visibilities),
                "max": max(visibilities),
                "span": max(visibilities) - min(visibilities)
            },
            "distribution": {
                "mean": sum(visibilities) / len(visibilities),
                "median": visibilities[len(visibilities) // 2],
                "q1": visibilities[len(visibilities) // 4],
                "q3": visibilities[3 * len(visibilities) // 4]
            },
            "visibility_bands": self._calculate_visibility_distribution(candidates),
            "handover_analysis": self._analyze_handover_frequency(candidates),
            "continuity_recommendations": self._generate_continuity_recommendations(candidates)
        }
        
        return insights
    
    def _generate_continuity_recommendations(self, candidates: List[Candidate]) -> Dict[str, str]:
        """生成連續性建議"""
        if not candidates:
            return {}
        
        avg_visibility = sum(c.visibility_time for c in candidates) / len(candidates)
        long_visibility_count = len([c for c in candidates if c.visibility_time > 600])
        
        recommendations = {}
        
        if avg_visibility < 300:
            recommendations["overall"] = "平均可見時間較短，建議增加衛星密度或優化軌道設計"
        elif avg_visibility > 900:
            recommendations["overall"] = "可見時間良好，可以提供穩定的連接服務"
        
        if long_visibility_count < len(candidates) * 0.3:
            recommendations["coverage"] = "長可見時間衛星比例較低，建議優化候選篩選策略"
        
        return recommendations