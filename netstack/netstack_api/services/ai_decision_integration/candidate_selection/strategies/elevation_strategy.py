"""
仰角篩選策略

基於衛星仰角進行候選篩選。仰角越高，信號質量通常越好，
大氣損耗越小，因此優先選擇高仰角的衛星。
"""

import time
import math
from typing import List, Dict, Any
from dataclasses import dataclass

from .base_strategy import SelectionStrategy, StrategyParameters, StrategyResult
from ...interfaces.candidate_selector import Candidate, ProcessedEvent


class ElevationStrategy(SelectionStrategy):
    """
    仰角篩選策略
    
    根據衛星仰角進行篩選和評分：
    - 仰角越高，評分越高
    - 低於最小仰角閾值的衛星被排除
    - 支援動態仰角閾值調整
    """
    
    def __init__(self):
        default_params = StrategyParameters(
            min_threshold=0.1,  # 最低仰角閾值 (10度對應0.1分)
            max_threshold=1.0,  # 最高仰角閾值
            weight=1.0,         # 策略權重
            custom_params={
                "min_elevation_deg": 10.0,      # 最小仰角度數
                "optimal_elevation_deg": 60.0,  # 最佳仰角度數  
                "elevation_cutoff_deg": 5.0,    # 仰角截止度數
                "use_cosine_weighting": True,   # 是否使用餘弦加權
                "atmospheric_compensation": True # 是否補償大氣損耗
            }
        )
        
        super().__init__(
            name="elevation_strategy",
            description="基於衛星仰角的候選篩選策略，優先選擇高仰角衛星以獲得更好的信號質量",
            default_params=default_params
        )
    
    def evaluate_candidate(self, candidate: Candidate, 
                          event: ProcessedEvent,
                          params: StrategyParameters = None) -> float:
        """
        評估候選衛星的仰角分數
        
        Args:
            candidate: 候選衛星
            event: 處理後的事件
            params: 策略參數
            
        Returns:
            float: 仰角評分 (0.0-1.0)
        """
        effective_params = self.get_effective_parameters(params)
        
        if not effective_params.enabled:
            return 0.0
        
        custom_params = effective_params.custom_params
        elevation_deg = candidate.elevation
        
        # 檢查是否低於截止仰角
        cutoff_elevation = custom_params.get("elevation_cutoff_deg", 5.0)
        if elevation_deg < cutoff_elevation:
            return 0.0
        
        # 獲取參數
        min_elevation = custom_params.get("min_elevation_deg", 10.0)
        optimal_elevation = custom_params.get("optimal_elevation_deg", 60.0)
        use_cosine = custom_params.get("use_cosine_weighting", True)
        atmospheric_comp = custom_params.get("atmospheric_compensation", True)
        
        # 基礎評分計算
        if elevation_deg <= min_elevation:
            base_score = 0.1  # 最低分數
        elif elevation_deg >= optimal_elevation:
            base_score = 1.0  # 最高分數
        else:
            # 線性插值
            base_score = 0.1 + (elevation_deg - min_elevation) / (optimal_elevation - min_elevation) * 0.9
        
        # 餘弦加權（模擬實際衛星信號強度與仰角的關係）
        if use_cosine:
            # 將仰角轉換為餘弦權重
            elevation_rad = math.radians(elevation_deg)
            cosine_weight = math.sin(elevation_rad)  # sin(elevation) = cos(zenith_angle)
            base_score *= cosine_weight
        
        # 大氣損耗補償
        if atmospheric_comp:
            # 簡化的大氣損耗模型：損耗與 1/sin(elevation) 成正比
            if elevation_deg > 0:
                elevation_rad = math.radians(elevation_deg) 
                atmospheric_factor = math.sin(elevation_rad)
                # 大氣損耗補償係數
                compensation = min(1.0, 0.5 + 0.5 * atmospheric_factor)
                base_score *= compensation
        
        # 確保分數在有效範圍內
        final_score = max(0.0, min(1.0, base_score))
        
        self.logger.debug(
            f"Elevation evaluation for {candidate.satellite_id}: "
            f"elevation={elevation_deg:.1f}°, score={final_score:.3f}"
        )
        
        return final_score
    
    def filter_candidates(self, candidates: List[Candidate],
                         event: ProcessedEvent, 
                         params: StrategyParameters = None) -> StrategyResult:
        """
        根據仰角篩選候選衛星
        
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
        elevation_stats = {"min": float('inf'), "max": 0.0, "avg": 0.0}
        
        if not effective_params.enabled:
            return StrategyResult(
                filtered_candidates=[],
                scores={},
                metadata={"strategy_disabled": True},
                strategy_name=self.name,
                execution_time_ms=0.0
            )
        
        # 評估所有候選者
        elevations = []
        for candidate in candidates:
            score = self.evaluate_candidate(candidate, event, effective_params)
            scores[candidate.satellite_id] = score
            elevations.append(candidate.elevation)
            
            # 根據閾值篩選
            if effective_params.min_threshold <= score <= effective_params.max_threshold:
                filtered_candidates.append(candidate)
        
        # 計算統計信息
        if elevations:
            elevation_stats = {
                "min": min(elevations),
                "max": max(elevations),
                "avg": sum(elevations) / len(elevations)
            }
        
        # 按仰角排序（高仰角優先）
        filtered_candidates.sort(key=lambda c: c.elevation, reverse=True)
        
        execution_time = (time.time() - start_time) * 1000
        
        metadata = {
            "total_candidates": len(candidates),
            "filtered_count": len(filtered_candidates),
            "elevation_stats": elevation_stats,
            "strategy_params": {
                "min_threshold": effective_params.min_threshold,
                "max_threshold": effective_params.max_threshold,
                "weight": effective_params.weight,
                "custom_params": effective_params.custom_params
            },
            "filtering_ratio": len(filtered_candidates) / len(candidates) if candidates else 0.0
        }
        
        self.logger.info(
            f"Elevation filtering completed: {len(filtered_candidates)}/{len(candidates)} candidates passed, "
            f"elevation range: {elevation_stats['min']:.1f}°-{elevation_stats['max']:.1f}°"
        )
        
        return StrategyResult(
            filtered_candidates=filtered_candidates,
            scores=scores,
            metadata=metadata,
            strategy_name=self.name,
            execution_time_ms=execution_time
        )
    
    def calculate_optimal_threshold(self, candidates: List[Candidate], 
                                  target_count: int = None) -> float:
        """
        根據候選衛星分佈計算最佳仰角閾值
        
        Args:
            candidates: 候選衛星列表
            target_count: 目標候選數量
            
        Returns:
            float: 建議的最小仰角閾值
        """
        if not candidates:
            return self.default_params.min_threshold
        
        elevations = [c.elevation for c in candidates]
        elevations.sort(reverse=True)
        
        if target_count and target_count < len(elevations):
            # 選擇第 target_count 個候選者的仰角作為閾值
            threshold_elevation = elevations[target_count - 1]
        else:
            # 使用中位數作為閾值
            threshold_elevation = elevations[len(elevations) // 2]
        
        # 轉換為評分閾值
        dummy_candidate = Candidate(
            satellite_id="dummy",
            elevation=threshold_elevation,
            signal_strength=0,
            load_factor=0,
            distance=0,
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
    
    def get_elevation_insights(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """
        獲取仰角分佈洞察
        
        Args:
            candidates: 候選衛星列表
            
        Returns:
            Dict[str, Any]: 仰角分析結果
        """
        if not candidates:
            return {"error": "No candidates provided"}
        
        elevations = [c.elevation for c in candidates]
        elevations.sort()
        
        insights = {
            "total_count": len(candidates),
            "elevation_range": {
                "min": min(elevations),
                "max": max(elevations),
                "span": max(elevations) - min(elevations)
            },
            "distribution": {
                "mean": sum(elevations) / len(elevations),
                "median": elevations[len(elevations) // 2],
                "q1": elevations[len(elevations) // 4],
                "q3": elevations[3 * len(elevations) // 4]
            },
            "quality_bands": {
                "excellent": len([e for e in elevations if e >= 60]),  # >= 60度
                "good": len([e for e in elevations if 30 <= e < 60]),  # 30-60度
                "acceptable": len([e for e in elevations if 10 <= e < 30]),  # 10-30度
                "poor": len([e for e in elevations if e < 10])  # < 10度
            }
        }
        
        return insights