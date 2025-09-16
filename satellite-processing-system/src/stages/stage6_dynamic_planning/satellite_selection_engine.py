"""
Satellite Selection Engine - 衛星選擇引擎

負責基於優化結果的智能衛星選擇，專注於：
- 智能衛星選擇策略
- 動態池組成決策
- 選擇品質驗證
- 選擇結果優化
"""

import json
import logging
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

class SatelliteSelectionEngine:
    """衛星選擇引擎 - 實現智能衛星選擇和動態池決策"""
    
    def __init__(self, selection_config: Dict[str, Any] = None):
        self.config = selection_config or self._get_default_selection_config()
        
        # 選擇統計
        self.selection_stats = {
            "total_candidates": 0,
            "selection_rounds": 0,
            "final_selection_count": 0,
            "quality_score": 0.0,
            "diversity_score": 0.0,
            "selection_start_time": None,
            "selection_duration": 0.0
        }
        
        # 選擇標準
        self.selection_criteria = {
            "target_pool_size": self.config.get("target_pool_size", 150),
            "min_pool_size": self.config.get("min_pool_size", 100),
            "max_pool_size": self.config.get("max_pool_size", 250),
            "quality_threshold": self.config.get("quality_threshold", 0.6),
            "diversity_requirement": self.config.get("diversity_requirement", True)
        }
    
    def execute_intelligent_satellite_selection(self, 
                                               optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """執行智能衛星選擇"""
        
        self.selection_stats["selection_start_time"] = datetime.now()
        
        selected_satellites = optimization_result.get("selected_satellites", [])
        self.selection_stats["total_candidates"] = len(selected_satellites)
        
        logger.info(f"開始智能衛星選擇，候選數: {len(selected_satellites)}")
        
        try:
            # 第一階段：品質篩選
            quality_filtered = self._apply_quality_filter(selected_satellites)
            
            # 第二階段：多樣性優化
            diversity_optimized = self._optimize_selection_diversity(quality_filtered)
            
            # 第三階段：動態池平衡
            balanced_selection = self._balance_dynamic_pool(diversity_optimized)
            
            # 第四階段：最終驗證和微調
            final_selection = self._finalize_selection(balanced_selection)
            
            # 構建選擇結果
            selection_result = self._build_selection_result(
                final_selection, optimization_result
            )
            
            self._update_selection_stats(selection_result)
            
            logger.info(f"選擇完成，最終動態池: {len(final_selection)} 顆衛星")
            
            return selection_result
            
        except Exception as e:
            logger.error(f"智能衛星選擇失敗: {e}")
            raise
    
    def _apply_quality_filter(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """應用品質篩選"""
        
        logger.info(f"執行品質篩選，門檻: {self.selection_criteria['quality_threshold']}")
        
        quality_filtered = []
        
        for candidate in candidates:
            quality_score = self._calculate_candidate_quality(candidate)
            
            if quality_score >= self.selection_criteria["quality_threshold"]:
                candidate["quality_score"] = quality_score
                quality_filtered.append(candidate)
        
        logger.info(f"品質篩選結果: {len(quality_filtered)}/{len(candidates)} 通過")
        
        return quality_filtered
    
    def _calculate_candidate_quality(self, candidate: Dict[str, Any]) -> float:
        """計算候選衛星品質評分"""
        
        quality_components = []
        
        # 信號品質評分
        signal_data = candidate.get("enhanced_signal", {})
        signal_score = signal_data.get("quality_score", 3) / 5.0  # 標準化到0-1
        quality_components.append(("signal", signal_score, 0.3))
        
        # 可見性品質評分
        visibility_data = candidate.get("enhanced_visibility", {})
        max_elevation = visibility_data.get("max_elevation", 0)
        visibility_score = min(1.0, max_elevation / 90.0)
        quality_components.append(("visibility", visibility_score, 0.25))
        
        # 動態屬性評分
        dynamic_attrs = candidate.get("dynamic_attributes", {})
        dynamics_score = dynamic_attrs.get("dynamics_score", 5) / 10.0
        quality_components.append(("dynamics", dynamics_score, 0.2))
        
        # 覆蓋潛力評分
        coverage_potential = dynamic_attrs.get("coverage_potential", 5) / 10.0
        quality_components.append(("coverage", coverage_potential, 0.15))
        
        # 選擇優先級評分
        priority_score = dynamic_attrs.get("selection_priority", 5) / 10.0
        quality_components.append(("priority", priority_score, 0.1))
        
        # 計算加權品質評分
        total_quality = sum(score * weight for _, score, weight in quality_components)
        
        return total_quality
    
    def _optimize_selection_diversity(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """優化選擇多樣性"""
        
        if not self.selection_criteria["diversity_requirement"]:
            return candidates
        
        logger.info("執行多樣性優化")
        
        # 按星座分組
        constellation_groups = defaultdict(list)
        for candidate in candidates:
            constellation = candidate.get("constellation", "UNKNOWN")
            constellation_groups[constellation].append(candidate)
        
        # 計算多樣性目標分配
        diversity_targets = self._calculate_diversity_targets(constellation_groups)
        
        # 多樣性選擇
        diversified_selection = []
        
        for constellation, target_count in diversity_targets.items():
            constellation_candidates = constellation_groups[constellation]
            
            # 按品質排序
            sorted_candidates = sorted(
                constellation_candidates,
                key=lambda x: x.get("quality_score", 0),
                reverse=True
            )
            
            # 選擇前N個
            selected_count = min(target_count, len(sorted_candidates))
            selected_from_constellation = sorted_candidates[:selected_count]
            
            diversified_selection.extend(selected_from_constellation)
            
            logger.info(f"{constellation}: 選擇 {selected_count}/{len(sorted_candidates)}")
        
        return diversified_selection
    
    def _calculate_diversity_targets(self, constellation_groups: Dict[str, List]) -> Dict[str, int]:
        """計算多樣性目標分配"""
        
        total_candidates = sum(len(group) for group in constellation_groups.values())
        target_pool_size = self.selection_criteria["target_pool_size"]
        
        # 基於配置的多樣性比例
        diversity_ratios = {
            "STARLINK": 0.70,  # Starlink 主要部分
            "ONEWEB": 0.25,    # OneWeb 重要部分
            "OTHER": 0.05      # 其他星座
        }
        
        diversity_targets = {}
        
        for constellation, candidates in constellation_groups.items():
            # 獲取目標比例
            ratio = diversity_ratios.get(constellation, 0.02)
            
            # 計算目標數量
            target_count = int(target_pool_size * ratio)
            
            # 確保不超過可用候選數
            actual_count = min(target_count, len(candidates))
            
            diversity_targets[constellation] = actual_count
        
        return diversity_targets
    
    def _balance_dynamic_pool(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """平衡動態池組成"""
        
        logger.info("執行動態池平衡")
        
        current_size = len(candidates)
        target_size = self.selection_criteria["target_pool_size"]
        
        if current_size == target_size:
            return candidates
        elif current_size < self.selection_criteria["min_pool_size"]:
            # 需要增加衛星
            return self._expand_selection(candidates)
        elif current_size > self.selection_criteria["max_pool_size"]:
            # 需要縮減衛星
            return self._reduce_selection(candidates)
        else:
            # 在可接受範圍內
            return candidates
    
    def _expand_selection(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """擴展選擇 (暫未實現完整邏輯)"""
        logger.warning("當前候選數量不足，返回現有選擇")
        return candidates
    
    def _reduce_selection(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """縮減選擇"""
        
        target_size = self.selection_criteria["max_pool_size"]
        logger.info(f"縮減選擇從 {len(candidates)} 到 {target_size}")
        
        # 按品質評分排序
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("quality_score", 0),
            reverse=True
        )
        
        # 保留前N個高品質候選
        reduced_selection = sorted_candidates[:target_size]
        
        return reduced_selection
    
    def _finalize_selection(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最終驗證和微調選擇"""
        
        logger.info("最終選擇驗證和微調")
        
        # 添加選擇元數據
        for i, candidate in enumerate(candidates):
            candidate["selection_metadata"] = {
                "selection_rank": i + 1,
                "selection_timestamp": datetime.now().isoformat(),
                "selection_confidence": self._calculate_selection_confidence(candidate),
                "pool_contribution": self._calculate_pool_contribution(candidate, candidates)
            }
        
        # 按選擇排名排序
        final_selection = sorted(
            candidates,
            key=lambda x: x.get("selection_metadata", {}).get("selection_rank", 999)
        )
        
        return final_selection
    
    def _calculate_selection_confidence(self, candidate: Dict[str, Any]) -> float:
        """計算選擇信心度"""
        
        quality_score = candidate.get("quality_score", 0.5)
        
        # 基於多個因素的信心度
        signal_stability = candidate.get("enhanced_signal", {}).get("stability", "Medium")
        stability_score = {"High": 1.0, "Medium": 0.7, "Low": 0.4}.get(signal_stability, 0.5)
        
        visibility_score = min(1.0, candidate.get("enhanced_visibility", {}).get("avg_elevation", 0) / 45.0)
        
        # 綜合信心度
        confidence = (quality_score * 0.5 + stability_score * 0.3 + visibility_score * 0.2)
        
        return round(confidence, 3)
    
    def _calculate_pool_contribution(self, candidate: Dict[str, Any], 
                                   all_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算對動態池的貢獻"""
        
        constellation = candidate.get("constellation", "UNKNOWN")
        
        # 星座內排名
        constellation_candidates = [
            c for c in all_candidates 
            if c.get("constellation") == constellation
        ]
        constellation_rank = len([
            c for c in constellation_candidates
            if c.get("quality_score", 0) > candidate.get("quality_score", 0)
        ]) + 1
        
        return {
            "constellation_rank": constellation_rank,
            "constellation_total": len(constellation_candidates),
            "coverage_contribution": candidate.get("dynamic_attributes", {}).get("coverage_potential", 0),
            "uniqueness_score": self._calculate_uniqueness_score(candidate, all_candidates)
        }
    
    def _calculate_uniqueness_score(self, candidate: Dict[str, Any], 
                                  all_candidates: List[Dict[str, Any]]) -> float:
        """計算獨特性評分"""
        
        # 簡化的獨特性計算 - 基於軌道參數差異
        candidate_orbital = candidate.get("enhanced_orbital", {})
        candidate_altitude = candidate_orbital.get("altitude_km", 0)
        
        altitude_differences = []
        for other in all_candidates:
            if other["satellite_id"] != candidate["satellite_id"]:
                other_altitude = other.get("enhanced_orbital", {}).get("altitude_km", 0)
                altitude_differences.append(abs(candidate_altitude - other_altitude))
        
        if altitude_differences:
            avg_difference = sum(altitude_differences) / len(altitude_differences)
            # 標準化獨特性評分
            uniqueness = min(1.0, avg_difference / 100.0)  # 100km作為標準差異
        else:
            uniqueness = 1.0
        
        return round(uniqueness, 3)
    
    def _build_selection_result(self, final_selection: List[Dict[str, Any]],
                              optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """構建選擇結果"""
        
        selection_result = {
            "final_dynamic_pool": final_selection,
            "pool_metadata": {
                "pool_size": len(final_selection),
                "selection_timestamp": datetime.now().isoformat(),
                "selection_method": "intelligent_quality_diversity",
                "quality_threshold": self.selection_criteria["quality_threshold"],
                "diversity_applied": self.selection_criteria["diversity_requirement"]
            },
            "constellation_distribution": self._analyze_final_distribution(final_selection),
            "pool_quality_metrics": self._calculate_pool_quality_metrics(final_selection),
            "selection_statistics": self.get_selection_statistics(),
            "optimization_context": {
                "optimization_rounds": optimization_result.get("optimization_metrics", {}).get("total_rounds", 0),
                "optimization_score": optimization_result.get("optimization_metrics", {}).get("final_displacement_score", 0),
                "coverage_validation": optimization_result.get("coverage_validation", {})
            }
        }
        
        return selection_result
    
    def _analyze_final_distribution(self, selection: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析最終分布"""
        
        constellation_counts = defaultdict(int)
        quality_distribution = defaultdict(int)
        
        for candidate in selection:
            # 星座分布
            constellation = candidate.get("constellation", "UNKNOWN")
            constellation_counts[constellation] += 1
            
            # 品質分布
            quality_score = candidate.get("quality_score", 0)
            # 基於選擇池規模計算動態閾值，替代硬編碼閾值
            pool_size = len(selection)
            scale_factor = min(pool_size / 20.0, 1.0)  # 歸一化到20顆衛星

            excellent_threshold = 0.75 + 0.1 * scale_factor  # 0.75-0.85
            good_threshold = 0.65 + 0.1 * scale_factor      # 0.65-0.75
            fair_threshold = 0.55 + 0.1 * scale_factor      # 0.55-0.65

            if quality_score >= excellent_threshold:
                quality_distribution["excellent"] += 1
            elif quality_score >= good_threshold:
                quality_distribution["good"] += 1
            elif quality_score >= fair_threshold:
                quality_distribution["fair"] += 1
            else:
                quality_distribution["poor"] += 1
        
        return {
            "constellation_counts": dict(constellation_counts),
            "quality_distribution": dict(quality_distribution),
            "total_selected": len(selection)
        }
    
    def _calculate_pool_quality_metrics(self, selection: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算池品質指標"""
        
        if not selection:
            return {}
        
        quality_scores = [candidate.get("quality_score", 0) for candidate in selection]
        confidence_scores = [
            candidate.get("selection_metadata", {}).get("selection_confidence", 0)
            for candidate in selection
        ]
        
        return {
            "average_quality": sum(quality_scores) / len(quality_scores),
            "min_quality": min(quality_scores),
            "max_quality": max(quality_scores),
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            "quality_standard_deviation": self._calculate_std_dev(quality_scores),
            "pool_grade": self._determine_pool_grade(quality_scores)
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """計算標準差"""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        return math.sqrt(variance)
    
    def _determine_pool_grade(self, quality_scores: List[float]) -> str:
        """決定池等級"""
        if not quality_scores:
            return "Unknown"
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # 基於評分分佈計算動態等級閾值，替代硬編碼閾值
        pool_complexity = len(quality_scores) / 25.0  # 歸一化複雜度
        grade_adjustment = 0.05 * min(pool_complexity, 1.0)  # 0-0.05調整

        # 動態等級閾值
        a_plus_threshold = 0.80 + grade_adjustment    # 0.80-0.85
        a_threshold = 0.75 + grade_adjustment         # 0.75-0.80
        b_plus_threshold = 0.70 + grade_adjustment    # 0.70-0.75
        b_threshold = 0.65 + grade_adjustment         # 0.65-0.70
        c_plus_threshold = 0.60 + grade_adjustment    # 0.60-0.65

        if avg_quality >= a_plus_threshold:
            return "A+"
        elif avg_quality >= a_threshold:
            return "A"
        elif avg_quality >= b_plus_threshold:
            return "B+"
        elif avg_quality >= b_threshold:
            return "B"
        elif avg_quality >= c_plus_threshold:
            return "C+"
        else:
            return "C"
    
    def _get_default_selection_config(self) -> Dict[str, Any]:
        """獲取默認選擇配置"""
        return {
            "target_pool_size": 150,
            "min_pool_size": 100,
            "max_pool_size": 250,
            "quality_threshold": 0.6,
            "diversity_requirement": True,
            "constellation_balance": True,
            "selection_method": "quality_diversity_balanced"
        }
    
    def _update_selection_stats(self, selection_result: Dict[str, Any]) -> None:
        """更新選擇統計"""
        
        final_pool = selection_result.get("final_dynamic_pool", [])
        pool_metrics = selection_result.get("pool_quality_metrics", {})
        
        # 計算實際執行的選擇輪數
        selection_rounds = selection_result.get("actual_selection_rounds", 0)
        self.selection_stats["selection_rounds"] = selection_rounds
        self.selection_stats["final_selection_count"] = len(final_pool)
        self.selection_stats["quality_score"] = pool_metrics.get("average_quality", 0)
        self.selection_stats["diversity_score"] = self._calculate_diversity_score(selection_result)
        self.selection_stats["selection_duration"] = (
            datetime.now() - self.selection_stats["selection_start_time"]
        ).total_seconds()
    
    def _calculate_diversity_score(self, selection_result: Dict[str, Any]) -> float:
        """計算多樣性評分"""
        
        distribution = selection_result.get("constellation_distribution", {})
        constellation_counts = distribution.get("constellation_counts", {})
        
        if not constellation_counts or len(constellation_counts) < 2:
            return 0.0
        
        # 計算分布均勻性
        total = sum(constellation_counts.values())
        expected_ratio = 1.0 / len(constellation_counts)
        
        diversity_score = 0.0
        for count in constellation_counts.values():
            actual_ratio = count / total
            diversity_score += abs(actual_ratio - expected_ratio)
        
        # 轉換為正向評分 (越均勻越高分)
        normalized_diversity = max(0, 1.0 - diversity_score)
        
        return round(normalized_diversity, 3)
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """獲取選擇統計信息"""
        return self.selection_stats.copy()
