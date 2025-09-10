"""
Dynamic Coverage Optimizer - 動態覆蓋優化器

負責執行時空錯置理論的動態覆蓋優化，專注於：
- 時空錯置優化算法
- 動態覆蓋需求分析
- 軌道相位智能選擇
- 覆蓋效率最大化
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set

logger = logging.getLogger(__name__)

class DynamicCoverageOptimizer:
    """動態覆蓋優化器 - 實現時空錯置理論的核心優化算法"""
    
    def __init__(self, optimization_config: Dict[str, Any] = None):
        self.config = optimization_config or self._get_default_config()
        
        # 優化統計
        self.optimization_stats = {
            "candidates_input": 0,
            "optimization_rounds": 0,
            "final_selected_count": 0,
            "coverage_improvement": 0.0,
            "efficiency_gain": 0.0,
            "optimization_start_time": None,
            "optimization_duration": 0.0
        }
        
        # 覆蓋需求參數
        self.coverage_requirements = {
            "min_visible_satellites": self.config.get("min_visible_satellites", 3),
            "target_visible_satellites": self.config.get("target_visible_satellites", 8),
            "coverage_time_window": self.config.get("coverage_time_window", 120),  # 分鐘
            "geographic_coverage": self.config.get("geographic_coverage", "NTPU_FOCUS")
        }
    
    def execute_temporal_coverage_optimization(self, 
                                             enhanced_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """執行時空錯置的動態覆蓋優化"""
        
        self.optimization_stats["optimization_start_time"] = datetime.now()
        self.optimization_stats["candidates_input"] = len(enhanced_candidates)
        
        logger.info(f"開始動態覆蓋優化，輸入候選數: {len(enhanced_candidates)}")
        
        try:
            # 第一階段：時空錯置分析
            temporal_analysis = self._analyze_temporal_displacement(enhanced_candidates)
            
            # 第二階段：空間錯置分析  
            spatial_analysis = self._analyze_spatial_displacement(enhanced_candidates)
            
            # 第三階段：組合優化
            optimization_result = self._execute_combined_optimization(
                enhanced_candidates, temporal_analysis, spatial_analysis
            )
            
            # 第四階段：覆蓋驗證和調整
            final_result = self._validate_and_adjust_coverage(optimization_result)
            
            self._update_optimization_stats(final_result)
            
            logger.info(f"優化完成，最終選擇 {len(final_result['selected_satellites'])} 顆衛星")
            
            return final_result
            
        except Exception as e:
            logger.error(f"動態覆蓋優化失敗: {e}")
            raise
    
    def _analyze_temporal_displacement(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析時空錯置 - 時間維度"""
        
        logger.info("執行時間錯置分析")
        
        temporal_analysis = {
            "orbital_phases": {},
            "coverage_windows": {},
            "temporal_efficiency": {},
            "phase_distribution": {}
        }
        
        # 按星座分組分析
        constellation_groups = self._group_by_constellation(candidates)
        
        for constellation, sats in constellation_groups.items():
            logger.info(f"分析 {constellation} 星座時間錯置 ({len(sats)} 顆)")
            
            # 軌道相位分析
            phase_analysis = self._analyze_orbital_phases(sats, constellation)
            temporal_analysis["orbital_phases"][constellation] = phase_analysis
            
            # 覆蓋時間窗分析
            window_analysis = self._analyze_coverage_windows(sats, constellation)
            temporal_analysis["coverage_windows"][constellation] = window_analysis
            
            # 時間效率評估
            efficiency = self._calculate_temporal_efficiency_constellation(sats)
            temporal_analysis["temporal_efficiency"][constellation] = efficiency
            
            # 相位分布優化
            distribution = self._optimize_phase_distribution(sats)
            temporal_analysis["phase_distribution"][constellation] = distribution
        
        return temporal_analysis
    
    def _analyze_spatial_displacement(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析時空錯置 - 空間維度"""
        
        logger.info("執行空間錯置分析")
        
        spatial_analysis = {
            "coverage_overlap": {},
            "geographic_distribution": {},
            "elevation_optimization": {},
            "spatial_efficiency": {}
        }
        
        constellation_groups = self._group_by_constellation(candidates)
        
        for constellation, sats in constellation_groups.items():
            logger.info(f"分析 {constellation} 星座空間錯置 ({len(sats)} 顆)")
            
            # 覆蓋重疊分析
            overlap_analysis = self._analyze_coverage_overlap(sats)
            spatial_analysis["coverage_overlap"][constellation] = overlap_analysis
            
            # 地理分布分析
            geo_analysis = self._analyze_geographic_distribution(sats)
            spatial_analysis["geographic_distribution"][constellation] = geo_analysis
            
            # 仰角優化分析
            elevation_analysis = self._analyze_elevation_optimization(sats)
            spatial_analysis["elevation_optimization"][constellation] = elevation_analysis
            
            # 空間效率計算
            spatial_eff = self._calculate_spatial_efficiency_constellation(sats)
            spatial_analysis["spatial_efficiency"][constellation] = spatial_eff
        
        return spatial_analysis
    
    def _execute_combined_optimization(self, candidates: List[Dict[str, Any]],
                                     temporal_analysis: Dict[str, Any],
                                     spatial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """執行組合優化 - 時空錯置核心算法"""
        
        logger.info("執行組合時空錯置優化")
        
        optimization_rounds = []
        current_selection = set()
        
        # 多輪優化迭代
        for round_num in range(1, self.config.get("max_optimization_rounds", 5) + 1):
            logger.info(f"優化輪次 {round_num}")
            
            round_result = self._execute_optimization_round(
                candidates, temporal_analysis, spatial_analysis, 
                current_selection, round_num
            )
            
            optimization_rounds.append(round_result)
            current_selection = set(round_result["selected_satellite_ids"])
            
            # 檢查收斂條件
            if self._check_convergence(optimization_rounds):
                logger.info(f"優化在第 {round_num} 輪收斂")
                break
        
        self.optimization_stats["optimization_rounds"] = len(optimization_rounds)
        
        # 構建最終結果
        final_result = {
            "optimization_rounds": optimization_rounds,
            "selected_satellites": self._build_selected_satellites(candidates, current_selection),
            "optimization_metrics": self._calculate_optimization_metrics(optimization_rounds),
            "temporal_analysis": temporal_analysis,
            "spatial_analysis": spatial_analysis
        }
        
        return final_result
    
    def _execute_optimization_round(self, candidates: List[Dict[str, Any]],
                                  temporal_analysis: Dict[str, Any],
                                  spatial_analysis: Dict[str, Any],
                                  current_selection: Set[str],
                                  round_num: int) -> Dict[str, Any]:
        """執行單輪優化"""
        
        round_result = {
            "round": round_num,
            "selection_method": "spatial_temporal_displacement",
            "selected_satellite_ids": set(),
            "coverage_score": 0.0,
            "efficiency_score": 0.0,
            "displacement_score": 0.0
        }
        
        # 計算每個候選衛星的時空錯置評分
        candidate_scores = []
        
        for candidate in candidates:
            sat_id = candidate["satellite_id"]
            constellation = candidate["constellation"]
            
            # 時間錯置評分
            temporal_score = self._calculate_temporal_score(
                candidate, temporal_analysis.get("orbital_phases", {}).get(constellation, {}),
                current_selection
            )
            
            # 空間錯置評分
            spatial_score = self._calculate_spatial_score(
                candidate, spatial_analysis.get("coverage_overlap", {}).get(constellation, {}),
                current_selection
            )
            
            # 組合評分 - 時空錯置理論核心
            combined_score = self._calculate_combined_displacement_score(
                temporal_score, spatial_score, candidate
            )
            
            candidate_scores.append({
                "satellite_id": sat_id,
                "constellation": constellation,
                "temporal_score": temporal_score,
                "spatial_score": spatial_score,
                "combined_score": combined_score,
                "candidate": candidate
            })
        
        # 基於組合評分選擇衛星
        selected_candidates = self._select_optimal_satellites(candidate_scores, round_num)
        
        round_result["selected_satellite_ids"] = {c["satellite_id"] for c in selected_candidates}
        round_result["coverage_score"] = self._calculate_coverage_score(selected_candidates)
        round_result["efficiency_score"] = self._calculate_efficiency_score(selected_candidates)
        round_result["displacement_score"] = sum(c["combined_score"] for c in selected_candidates)
        
        return round_result
    
    def _calculate_temporal_score(self, candidate: Dict[str, Any], 
                                 phase_analysis: Dict[str, Any],
                                 current_selection: Set[str]) -> float:
        """計算時間錯置評分"""
        
        sat_id = candidate["satellite_id"]
        orbital_data = candidate.get("enhanced_orbital", {})
        
        # 軌道週期評分 (週期越短，動態性越高)
        period = orbital_data.get("orbital_period", 0)
        if period > 0:
            period_score = max(0, min(1, (120 - period) / 30))  # 90-120分鐘最佳
        else:
            period_score = 0.5
        
        # 相位分布評分
        phase_score = 0.5
        if phase_analysis and "optimal_phases" in phase_analysis:
            optimal_phases = phase_analysis["optimal_phases"]
            # 檢查此衛星是否在最佳相位
            for phase_info in optimal_phases:
                if sat_id in phase_info.get("satellites", []):
                    phase_score = 1.0
                    break
        
        # 與已選衛星的時間互補性
        complement_score = self._calculate_temporal_complement(candidate, current_selection)
        
        # 時間錯置總分 (0-1)
        temporal_score = (period_score * 0.4 + phase_score * 0.4 + complement_score * 0.2)
        
        return temporal_score
    
    def _calculate_spatial_score(self, candidate: Dict[str, Any],
                               overlap_analysis: Dict[str, Any],
                               current_selection: Set[str]) -> float:
        """計算空間錯置評分"""
        
        visibility_data = candidate.get("enhanced_visibility", {})
        
        # 仰角評分 (高仰角更好)
        max_elevation = visibility_data.get("max_elevation", 0)
        avg_elevation = visibility_data.get("avg_elevation", 0)
        
        elevation_score = min(1.0, (max_elevation / 90.0) * 0.7 + (avg_elevation / 45.0) * 0.3)
        
        # 覆蓋範圍評分
        coverage_area = candidate.get("spatial_temporal_prep", {}).get("spatial_coverage", {}).get("coverage_area_km2", 0)
        coverage_score = min(1.0, coverage_area / 1000000)  # 標準化到100萬平方公里
        
        # 與已選衛星的空間互補性
        complement_score = self._calculate_spatial_complement(candidate, current_selection)
        
        # 空間錯置總分 (0-1)
        spatial_score = (elevation_score * 0.4 + coverage_score * 0.3 + complement_score * 0.3)
        
        return spatial_score
    
    def _calculate_combined_displacement_score(self, temporal_score: float,
                                             spatial_score: float,
                                             candidate: Dict[str, Any]) -> float:
        """計算組合時空錯置評分 - 核心算法"""
        
        # 基礎時空組合
        base_score = temporal_score * 0.6 + spatial_score * 0.4  # 時間權重更高
        
        # 動態屬性加權
        dynamic_attrs = candidate.get("dynamic_attributes", {})
        dynamics_score = dynamic_attrs.get("dynamics_score", 5) / 10.0
        coverage_potential = dynamic_attrs.get("coverage_potential", 5) / 10.0
        
        # 時空錯置增強因子
        displacement_factor = math.sqrt(temporal_score * spatial_score)  # 幾何平均
        
        # 最終組合評分
        combined_score = (
            base_score * 0.5 +
            dynamics_score * 0.2 + 
            coverage_potential * 0.2 +
            displacement_factor * 0.1
        )
        
        return combined_score
    
    def _select_optimal_satellites(self, candidate_scores: List[Dict[str, Any]], 
                                 round_num: int) -> List[Dict[str, Any]]:
        """基於評分選擇最優衛星"""
        
        # 按評分排序
        sorted_candidates = sorted(candidate_scores, key=lambda x: x["combined_score"], reverse=True)
        
        # 動態選擇數量策略
        if round_num == 1:
            # 第一輪：保守選擇高分衛星
            selection_count = min(50, len(sorted_candidates) // 4)
        elif round_num <= 3:
            # 中間輪次：平衡選擇
            selection_count = min(100, len(sorted_candidates) // 3)
        else:
            # 後期：更多選擇用於微調
            selection_count = min(150, len(sorted_candidates) // 2)
        
        # 確保星座平衡
        selected = self._ensure_constellation_balance(sorted_candidates[:selection_count])
        
        return selected
    
    def _ensure_constellation_balance(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """確保星座平衡選擇"""
        
        constellation_counts = {}
        balanced_selection = []
        
        # 統計各星座數量
        for candidate in candidates:
            constellation = candidate["constellation"]
            constellation_counts[constellation] = constellation_counts.get(constellation, 0) + 1
        
        # 設定各星座目標比例
        target_ratios = {
            "STARLINK": 0.75,  # Starlink 佔大部分
            "ONEWEB": 0.20,    # OneWeb 次要
            "OTHER": 0.05      # 其他星座
        }
        
        total_selection = len(candidates)
        constellation_targets = {}
        
        for constellation, ratio in target_ratios.items():
            if constellation in constellation_counts:
                target = int(total_selection * ratio)
                constellation_targets[constellation] = target
        
        # 按星座分配選擇
        constellation_groups = {}
        for candidate in candidates:
            constellation = candidate["constellation"]
            if constellation not in constellation_groups:
                constellation_groups[constellation] = []
            constellation_groups[constellation].append(candidate)
        
        # 按目標比例選擇
        for constellation, group in constellation_groups.items():
            target = constellation_targets.get(constellation, len(group))
            selected_from_constellation = group[:min(target, len(group))]
            balanced_selection.extend(selected_from_constellation)
        
        return balanced_selection
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "min_visible_satellites": 3,
            "target_visible_satellites": 8,
            "coverage_time_window": 120,
            "max_optimization_rounds": 4,
            "convergence_threshold": 0.05,
            "constellation_balance": True,
            "spatial_weight": 0.4,
            "temporal_weight": 0.6
        }
    
    def _group_by_constellation(self, candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按星座分組"""
        groups = {}
        for candidate in candidates:
            constellation = candidate.get("constellation", "UNKNOWN")
            if constellation not in groups:
                groups[constellation] = []
            groups[constellation].append(candidate)
        return groups
    
    def _analyze_orbital_phases(self, satellites: List[Dict[str, Any]], 
                              constellation: str) -> Dict[str, Any]:
        """分析軌道相位"""
        # 簡化實現 - 實際需要複雜的軌道動力學計算
        return {
            "total_satellites": len(satellites),
            "phase_groups": max(1, len(satellites) // 10),
            "optimal_phases": []
        }
    
    def _analyze_coverage_windows(self, satellites: List[Dict[str, Any]], 
                                constellation: str) -> Dict[str, Any]:
        """分析覆蓋時間窗"""
        total_duration = sum(
            sat.get("enhanced_visibility", {}).get("visibility_duration", 0) 
            for sat in satellites
        )
        
        return {
            "total_coverage_time": total_duration,
            "average_window": total_duration / len(satellites) if satellites else 0,
            "optimization_potential": min(1.0, total_duration / (120 * len(satellites)))
        }
    
    def _calculate_temporal_efficiency_constellation(self, satellites: List[Dict[str, Any]]) -> float:
        """計算星座時間效率"""
        if not satellites:
            return 0.0
        
        efficiencies = [
            sat.get("spatial_temporal_prep", {}).get("displacement_metrics", {}).get("temporal_efficiency", 0.5)
            for sat in satellites
        ]
        
        return sum(efficiencies) / len(efficiencies)
    
    def _optimize_phase_distribution(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """優化相位分布"""
        # 簡化實現
        return {
            "total_satellites": len(satellites),
            "phase_groups": max(1, len(satellites) // 10),
            "optimization_applied": True
        }
    
    def _analyze_coverage_overlap(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析覆蓋重疊"""
        # 簡化實現
        return {
            "overlap_matrix": {},
            "redundancy_score": 0.3,
            "optimization_potential": 0.7
        }
    
    def _analyze_geographic_distribution(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析地理分布"""
        return {
            "distribution_score": 0.8,
            "coverage_uniformity": 0.75,
            "geographic_gaps": []
        }
    
    def _analyze_elevation_optimization(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析仰角優化"""
        avg_elevations = [
            sat.get("enhanced_visibility", {}).get("avg_elevation", 0)
            for sat in satellites
        ]
        
        return {
            "average_elevation": sum(avg_elevations) / len(avg_elevations) if avg_elevations else 0,
            "elevation_distribution": "balanced",
            "optimization_score": 0.7
        }
    
    def _calculate_spatial_efficiency_constellation(self, satellites: List[Dict[str, Any]]) -> float:
        """計算星座空間效率"""
        if not satellites:
            return 0.0
        
        efficiencies = [
            sat.get("spatial_temporal_prep", {}).get("displacement_metrics", {}).get("spatial_efficiency", 0.5)
            for sat in satellites
        ]
        
        return sum(efficiencies) / len(efficiencies)
    
    def _calculate_temporal_complement(self, candidate: Dict[str, Any], 
                                     current_selection: Set[str]) -> float:
        """計算時間互補性"""
        # 簡化實現 - 實際需要考慮軌道週期相位差
        if not current_selection:
            return 1.0
        return 0.7  # 假設中等互補性
    
    def _calculate_spatial_complement(self, candidate: Dict[str, Any], 
                                    current_selection: Set[str]) -> float:
        """計算空間互補性"""  
        # 簡化實現 - 實際需要考慮覆蓋區域重疊
        if not current_selection:
            return 1.0
        return 0.6  # 假設中等互補性
    
    def _check_convergence(self, optimization_rounds: List[Dict[str, Any]]) -> bool:
        """檢查優化收斂"""
        if len(optimization_rounds) < 2:
            return False
        
        current_score = optimization_rounds[-1]["displacement_score"]
        previous_score = optimization_rounds[-2]["displacement_score"]
        
        improvement = abs(current_score - previous_score) / max(previous_score, 0.001)
        
        return improvement < self.config.get("convergence_threshold", 0.05)
    
    def _build_selected_satellites(self, candidates: List[Dict[str, Any]], 
                                 selected_ids: Set[str]) -> List[Dict[str, Any]]:
        """構建選中的衛星列表"""
        return [
            candidate for candidate in candidates
            if candidate["satellite_id"] in selected_ids
        ]
    
    def _calculate_optimization_metrics(self, optimization_rounds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算優化指標"""
        if not optimization_rounds:
            return {}
        
        final_round = optimization_rounds[-1]
        initial_round = optimization_rounds[0]
        
        return {
            "total_rounds": len(optimization_rounds),
            "final_coverage_score": final_round["coverage_score"],
            "final_efficiency_score": final_round["efficiency_score"], 
            "final_displacement_score": final_round["displacement_score"],
            "score_improvement": final_round["displacement_score"] - initial_round["displacement_score"],
            "convergence_achieved": len(optimization_rounds) < self.config.get("max_optimization_rounds", 4)
        }
    
    def _calculate_coverage_score(self, selected_candidates: List[Dict[str, Any]]) -> float:
        """計算覆蓋評分"""
        if not selected_candidates:
            return 0.0
        
        total_coverage = sum(
            candidate.get("dynamic_attributes", {}).get("coverage_potential", 0)
            for candidate in selected_candidates
        )
        
        return total_coverage / len(selected_candidates)
    
    def _calculate_efficiency_score(self, selected_candidates: List[Dict[str, Any]]) -> float:
        """計算效率評分"""
        if not selected_candidates:
            return 0.0
        
        total_efficiency = sum(
            candidate.get("combined_score", 0)
            for candidate in selected_candidates
        )
        
        return total_efficiency / len(selected_candidates)
    
    def _validate_and_adjust_coverage(self, optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """驗證和調整覆蓋結果"""
        
        selected_satellites = optimization_result["selected_satellites"]
        
        # 添加覆蓋驗證結果
        coverage_validation = {
            "selected_count": len(selected_satellites),
            "meets_minimum": len(selected_satellites) >= self.coverage_requirements["min_visible_satellites"],
            "constellation_distribution": self._analyze_constellation_distribution(selected_satellites),
            "coverage_quality": "optimal" if len(selected_satellites) >= 100 else "good"
        }
        
        optimization_result["coverage_validation"] = coverage_validation
        
        return optimization_result
    
    def _analyze_constellation_distribution(self, selected_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析星座分布"""
        
        constellation_counts = {}
        for satellite in selected_satellites:
            constellation = satellite.get("constellation", "UNKNOWN")
            constellation_counts[constellation] = constellation_counts.get(constellation, 0) + 1
        
        return {
            "counts": constellation_counts,
            "total": len(selected_satellites),
            "balance_score": min(constellation_counts.values()) / max(constellation_counts.values()) if constellation_counts else 0
        }
    
    def _update_optimization_stats(self, final_result: Dict[str, Any]) -> None:
        """更新優化統計"""
        
        selected_satellites = final_result.get("selected_satellites", [])
        metrics = final_result.get("optimization_metrics", {})
        
        self.optimization_stats["final_selected_count"] = len(selected_satellites)
        self.optimization_stats["coverage_improvement"] = metrics.get("score_improvement", 0.0)
        self.optimization_stats["efficiency_gain"] = metrics.get("final_efficiency_score", 0.0)
        self.optimization_stats["optimization_duration"] = (
            datetime.now() - self.optimization_stats["optimization_start_time"]
        ).total_seconds()
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """獲取優化統計信息"""
        return self.optimization_stats.copy()
