"""
建議引擎 - Stage 4模組化組件

職責：
1. 基於信號分析和3GPP事件生成衛星選擇建議
2. 計算綜合評分
3. 生成換手策略
4. 提供決策支持信息
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """建議引擎 - 基於多維度分析生成衛星選擇建議"""
    
    def __init__(self):
        """初始化建議引擎"""
        self.logger = logging.getLogger(f"{__name__}.RecommendationEngine")
        
        # 評分權重配置
        self.scoring_weights = {
            "signal_quality": 0.35,      # 信號品質權重 35%
            "stability": 0.25,           # 穩定性權重 25%
            "handover_suitability": 0.20, # 換手適用性權重 20%
            "event_frequency": 0.10,     # 事件頻率權重 10%
            "visibility": 0.10          # 可見性權重 10%
        }
        
        # 建議統計
        self.recommendation_statistics = {
            "satellites_evaluated": 0,
            "recommendations_generated": 0,
            "top_tier_satellites": 0,
            "handover_recommendations": 0
        }
        
        self.logger.info("✅ 建議引擎初始化完成")
        self.logger.info(f"   評分權重: 信號品質{self.scoring_weights['signal_quality']*100:.0f}%, "
                        f"穩定性{self.scoring_weights['stability']*100:.0f}%, "
                        f"換手適用性{self.scoring_weights['handover_suitability']*100:.0f}%")
    
    def generate_satellite_recommendations(self, 
                                         signal_results: Dict[str, Any],
                                         event_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成衛星選擇建議
        
        Args:
            signal_results: 信號品質計算結果
            event_results: 3GPP事件分析結果
            
        Returns:
            包含衛星建議的字典
        """
        self.logger.info("💡 生成衛星選擇建議...")
        
        # 整合數據
        integrated_data = self._integrate_analysis_results(signal_results, event_results)
        
        # 計算綜合評分
        scored_satellites = []
        for satellite_data in integrated_data:
            self.recommendation_statistics["satellites_evaluated"] += 1
            
            comprehensive_score = self._calculate_comprehensive_score(satellite_data)
            satellite_data["comprehensive_score"] = comprehensive_score
            satellite_data["recommendation_tier"] = self._determine_recommendation_tier(comprehensive_score)
            
            scored_satellites.append(satellite_data)
        
        # 排序衛星
        scored_satellites.sort(key=lambda x: x["comprehensive_score"], reverse=True)
        
        # 生成建議
        recommendations = {
            "satellite_rankings": scored_satellites,
            "top_recommendations": self._generate_top_recommendations(scored_satellites),
            "constellation_comparison": self._generate_constellation_comparison(scored_satellites),
            "handover_strategy": self._generate_handover_strategy(scored_satellites),
            "usage_recommendations": self._generate_usage_recommendations(scored_satellites)
        }
        
        self.recommendation_statistics["recommendations_generated"] = len(scored_satellites)
        self.recommendation_statistics["top_tier_satellites"] = len([s for s in scored_satellites if s["recommendation_tier"] == "Tier_1"])
        
        self.logger.info(f"✅ 衛星建議生成完成: {len(scored_satellites)} 顆衛星評分")
        self.logger.info(f"   頂級衛星: {self.recommendation_statistics['top_tier_satellites']} 顆")
        
        return recommendations
    
    def _integrate_analysis_results(self, signal_results: Dict[str, Any], 
                                  event_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """整合信號分析和事件分析結果"""
        
        integrated_data = []
        
        # 建立衛星ID到事件數據的映射
        event_map = {}
        for satellite_event in event_results.get("satellites", []):
            satellite_id = satellite_event.get("satellite_id")
            event_map[satellite_id] = satellite_event
        
        # 整合信號和事件數據
        for satellite_signal in signal_results.get("satellites", []):
            satellite_id = satellite_signal.get("satellite_id")
            
            integrated_satellite = {
                "satellite_id": satellite_id,
                "constellation": satellite_signal.get("constellation"),
                
                # 信號數據
                "signal_data": satellite_signal,
                
                # 事件數據
                "event_data": event_map.get(satellite_id, {}),
                
                # 基本指標
                "average_rsrp_dbm": satellite_signal.get("signal_metrics", {}).get("average_rsrp_dbm", -140),
                "signal_stability": satellite_signal.get("signal_metrics", {}).get("signal_stability_score", 0),
                "visibility_rate": self._calculate_visibility_rate(satellite_signal),
                "event_count": self._count_total_events(event_map.get(satellite_id, {}))
            }
            
            integrated_data.append(integrated_satellite)
        
        return integrated_data
    
    def _calculate_comprehensive_score(self, satellite_data: Dict[str, Any]) -> float:
        """計算衛星綜合評分 (0-100)"""
        
        # 信號品質評分 (35%)
        signal_score = self._score_signal_quality(satellite_data["average_rsrp_dbm"])
        
        # 穩定性評分 (25%) 
        stability_score = satellite_data["signal_stability"]
        
        # 換手適用性評分 (20%)
        handover_score = self._score_handover_suitability(satellite_data["event_data"])
        
        # 事件頻率評分 (10%) - 事件越少越好
        event_score = self._score_event_frequency(satellite_data["event_count"], satellite_data)
        
        # 可見性評分 (10%)
        visibility_score = satellite_data["visibility_rate"] * 100
        
        # 加權計算綜合評分
        comprehensive_score = (
            signal_score * self.scoring_weights["signal_quality"] +
            stability_score * self.scoring_weights["stability"] +
            handover_score * self.scoring_weights["handover_suitability"] +
            event_score * self.scoring_weights["event_frequency"] +
            visibility_score * self.scoring_weights["visibility"]
        )
        
        return round(comprehensive_score, 2)
    
    def _score_signal_quality(self, avg_rsrp_dbm: float) -> float:
        """評分信號品質 (0-100)"""
        if avg_rsrp_dbm >= -80:
            return 100.0
        elif avg_rsrp_dbm >= -90:
            return 85.0
        elif avg_rsrp_dbm >= -100:
            return 70.0
        elif avg_rsrp_dbm >= -110:
            return 50.0
        elif avg_rsrp_dbm >= -120:
            return 25.0
        else:
            return 5.0
    
    def _score_handover_suitability(self, event_data: Dict[str, Any]) -> float:
        """評分換手適用性 (0-100)"""
        handover_suitability = event_data.get("handover_suitability", {})
        
        if handover_suitability.get("is_handover_candidate", False):
            return handover_suitability.get("suitability_score", 0)
        else:
            return 20.0  # 基本分數
    
    def _score_event_frequency(self, event_count: int, satellite_data: Dict[str, Any]) -> float:
        """評分事件頻率 (0-100) - 事件少更好"""
        signal_data = satellite_data.get("signal_data", {})
        signal_timeseries = signal_data.get("signal_timeseries", [])
        
        if len(signal_timeseries) == 0:
            return 50.0
        
        event_rate = event_count / len(signal_timeseries)
        
        if event_rate <= 0.05:
            return 100.0
        elif event_rate <= 0.10:
            return 80.0
        elif event_rate <= 0.15:
            return 60.0
        elif event_rate <= 0.25:
            return 40.0
        else:
            return 20.0
    
    def _calculate_visibility_rate(self, satellite_signal: Dict[str, Any]) -> float:
        """計算可見性比率"""
        signal_metrics = satellite_signal.get("signal_metrics", {})
        visible_points = signal_metrics.get("visible_points_count", 0)
        total_points = signal_metrics.get("total_points_count", 1)
        
        return visible_points / total_points if total_points > 0 else 0
    
    def _count_total_events(self, event_data: Dict[str, Any]) -> int:
        """計算總事件數"""
        events = event_data.get("events", {})
        return len(events.get("A4", [])) + len(events.get("A5", [])) + len(events.get("D2", []))
    
    def _determine_recommendation_tier(self, score: float) -> str:
        """根據分數確定建議等級"""
        if score >= 85:
            return "Tier_1"  # 頂級推薦
        elif score >= 70:
            return "Tier_2"  # 優秀推薦
        elif score >= 55:
            return "Tier_3"  # 良好推薦
        elif score >= 40:
            return "Tier_4"  # 可用推薦
        else:
            return "Tier_5"  # 不推薦
    
    def _generate_top_recommendations(self, scored_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成頂級建議"""
        
        # 按等級分組
        tier_groups = {}
        for satellite in scored_satellites:
            tier = satellite["recommendation_tier"]
            if tier not in tier_groups:
                tier_groups[tier] = []
            tier_groups[tier].append(satellite)
        
        # 選出每個星座的最佳衛星
        constellation_best = {}
        for satellite in scored_satellites:
            constellation = satellite["constellation"]
            if constellation not in constellation_best or satellite["comprehensive_score"] > constellation_best[constellation]["comprehensive_score"]:
                constellation_best[constellation] = satellite
        
        return {
            "top_10_overall": scored_satellites[:10],
            "tier_1_satellites": tier_groups.get("Tier_1", []),
            "best_per_constellation": constellation_best,
            "primary_recommendation": scored_satellites[0] if scored_satellites else None,
            "backup_recommendations": scored_satellites[1:4]
        }
    
    def _generate_constellation_comparison(self, scored_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成星座間比較"""
        
        constellation_stats = {}
        
        for satellite in scored_satellites:
            constellation = satellite["constellation"]
            if constellation not in constellation_stats:
                constellation_stats[constellation] = {
                    "satellites": [],
                    "avg_score": 0,
                    "best_score": 0,
                    "tier_1_count": 0
                }
            
            stats = constellation_stats[constellation]
            stats["satellites"].append(satellite)
            stats["best_score"] = max(stats["best_score"], satellite["comprehensive_score"])
            
            if satellite["recommendation_tier"] == "Tier_1":
                stats["tier_1_count"] += 1
        
        # 計算平均分數
        for constellation, stats in constellation_stats.items():
            if stats["satellites"]:
                stats["avg_score"] = sum(s["comprehensive_score"] for s in stats["satellites"]) / len(stats["satellites"])
                stats["satellite_count"] = len(stats["satellites"])
        
        # 排序星座
        constellation_ranking = sorted(
            constellation_stats.items(),
            key=lambda x: x[1]["avg_score"],
            reverse=True
        )
        
        return {
            "constellation_statistics": constellation_stats,
            "constellation_ranking": [{"constellation": k, **v} for k, v in constellation_ranking],
            "best_constellation": constellation_ranking[0][0] if constellation_ranking else None
        }
    
    def _generate_handover_strategy(self, scored_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成換手策略"""
        
        # 識別換手候選
        handover_candidates = []
        for satellite in scored_satellites:
            event_data = satellite.get("event_data", {})
            handover_suitability = event_data.get("handover_suitability", {})
            
            if handover_suitability.get("is_handover_candidate", False):
                handover_candidates.append({
                    "satellite_id": satellite["satellite_id"],
                    "constellation": satellite["constellation"],
                    "comprehensive_score": satellite["comprehensive_score"],
                    "suitability_score": handover_suitability.get("suitability_score", 0),
                    "signal_strength": satellite["average_rsrp_dbm"]
                })
        
        self.recommendation_statistics["handover_recommendations"] = len(handover_candidates)
        
        # 排序換手候選
        handover_candidates.sort(key=lambda x: x["comprehensive_score"], reverse=True)
        
        # 生成策略
        if not handover_candidates:
            strategy = "maintain_current"
            strategy_reason = "無合適換手候選，建議維持當前連接"
        elif len(handover_candidates) >= 3:
            strategy = "multi_option_handover"
            strategy_reason = "多個優質換手候選可用，可靈活選擇"
        elif handover_candidates[0]["comprehensive_score"] >= 80:
            strategy = "immediate_handover"
            strategy_reason = "發現優質換手候選，建議立即準備換手"
        else:
            strategy = "conditional_handover"
            strategy_reason = "有可用換手候選，在信號惡化時考慮換手"
        
        return {
            "strategy": strategy,
            "strategy_reason": strategy_reason,
            "handover_candidates": handover_candidates,
            "primary_target": handover_candidates[0] if handover_candidates else None,
            "backup_targets": handover_candidates[1:3]
        }
    
    def _generate_usage_recommendations(self, scored_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成使用建議"""
        
        if not scored_satellites:
            return {"recommendation": "no_satellites_available"}
        
        top_satellite = scored_satellites[0]
        top_score = top_satellite["comprehensive_score"]
        top_constellation = top_satellite["constellation"]
        
        # 基於最高分衛星生成使用建議
        if top_score >= 85:
            usage_recommendation = {
                "priority": "high_priority_usage",
                "description": "建議優先使用，信號品質優秀",
                "suitable_applications": ["高清視頻", "實時通訊", "數據傳輸"],
                "expected_performance": "優秀"
            }
        elif top_score >= 70:
            usage_recommendation = {
                "priority": "recommended_usage",
                "description": "建議使用，信號品質良好",
                "suitable_applications": ["標清視頻", "語音通話", "一般數據"],
                "expected_performance": "良好"
            }
        elif top_score >= 55:
            usage_recommendation = {
                "priority": "conditional_usage", 
                "description": "條件性使用，信號品質中等",
                "suitable_applications": ["語音通話", "文字通訊", "低速數據"],
                "expected_performance": "中等"
            }
        else:
            usage_recommendation = {
                "priority": "limited_usage",
                "description": "建議限制使用，信號品質不佳",
                "suitable_applications": ["緊急通訊"],
                "expected_performance": "不佳"
            }
        
        return {
            "primary_recommendation": usage_recommendation,
            "recommended_constellation": top_constellation,
            "service_quality_expectation": self._map_score_to_quality(top_score),
            "alternative_options": len([s for s in scored_satellites if s["recommendation_tier"] in ["Tier_1", "Tier_2"]])
        }
    
    def _map_score_to_quality(self, score: float) -> str:
        """將分數映射到服務品質等級"""
        if score >= 85:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 55:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Very_Poor"
    
    def get_recommendation_statistics(self) -> Dict[str, Any]:
        """獲取建議統計信息"""
        return self.recommendation_statistics.copy()