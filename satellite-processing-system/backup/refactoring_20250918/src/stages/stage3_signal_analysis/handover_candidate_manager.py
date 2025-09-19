"""
換手候選衛星管理系統 - Stage 4模組化組件

職責：
1. 管理多個換手候選衛星 (3-5個)
2. 實現候選衛星優先級排序
3. 基於3GPP事件進行候選選擇
4. 提供換手決策支援數據
"""

import math
import logging

# 🚨 Grade A要求：動態計算RSRP閾值
noise_floor = -120  # 3GPP典型噪聲門檻
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import heapq

logger = logging.getLogger(__name__)

class HandoverCandidateManager:
    """
    換手候選衛星管理系統
    
    基於3GPP TS 38.331標準實現：
    - 多候選衛星同時追蹤
    - 基於A4/A5/D2事件的候選選擇
    - 智能優先級排序算法
    """
    
    def __init__(self, max_candidates: int = 5, min_candidates: int = 3):
        """
        初始化換手候選管理器
        
        Args:
            max_candidates: 最大候選數量
            min_candidates: 最小候選數量
        """
        self.logger = logging.getLogger(f"{__name__}.HandoverCandidateManager")
        
        self.max_candidates = max_candidates
        self.min_candidates = min_candidates
        
        # 候選衛星池
        self.candidate_pool = []  # 使用優先級隊列
        self.active_candidates = {}  # satellite_id -> candidate_info
        
        # 評分權重配置
        self.scoring_weights = {
            "signal_quality": 0.40,    # 信號品質權重 40%
            "3gpp_events": 0.25,       # 3GPP事件權重 25%
            "stability": 0.20,         # 信號穩定性權重 20%
            "geometric": 0.15          # 幾何條件權重 15%
        }
        
        # 3GPP事件權重配置
        self.event_weights = {
            "A4": 0.50,  # A4事件權重最高 (鄰區優於門檻)
            "A5": 0.35,  # A5事件權重中等 (雙門檻條件)
            "D2": 0.15   # D2事件權重較低 (距離基礎)
        }
        
        # 統計數據
        self.management_statistics = {
            "total_evaluated": 0,
            "candidates_added": 0,
            "candidates_removed": 0,
            "handover_recommendations": 0,
            "last_update_time": datetime.now(timezone.utc).isoformat()
        }
        
        self.logger.info("✅ 換手候選管理器初始化完成")
        self.logger.info(f"   候選數量範圍: {min_candidates}-{max_candidates}")
        self.logger.info(f"   評分權重: 信號{self.scoring_weights['signal_quality']*100:.0f}% + 事件{self.scoring_weights['3gpp_events']*100:.0f}% + 穩定{self.scoring_weights['stability']*100:.0f}% + 幾何{self.scoring_weights['geometric']*100:.0f}%")
    
    def evaluate_candidates(self, signal_results: Dict[str, Any], event_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估所有候選衛星並更新候選池
        
        Args:
            signal_results: 信號品質分析結果
            event_results: 3GPP事件分析結果
            
        Returns:
            候選管理結果字典
        """
        self.logger.info("🎯 開始評估換手候選衛星...")
        
        # 清空舊的候選池
        self.candidate_pool.clear()
        evaluated_satellites = []
        
        # 評估每顆衛星
        satellites = signal_results.get("satellites", [])
        event_satellites = {sat["satellite_id"]: sat for sat in event_results.get("satellites", [])}
        
        for satellite_signal in satellites:
            satellite_id = satellite_signal.get("satellite_id")
            
            # 找到對應的事件數據
            satellite_event = event_satellites.get(satellite_id, {})
            
            try:
                candidate_score = self._calculate_candidate_score(satellite_signal, satellite_event)
                
                candidate_info = {
                    "satellite_id": satellite_id,
                    "constellation": satellite_signal.get("constellation"),
                    "candidate_score": candidate_score,
                    "signal_metrics": satellite_signal.get("signal_metrics", {}),
                    "event_analysis": satellite_event.get("events", {}),
                    "handover_suitability": satellite_event.get("handover_suitability", {}),
                    "evaluation_time": datetime.now(timezone.utc).isoformat(),
                    "score_breakdown": candidate_score.get("breakdown", {})
                }
                
                evaluated_satellites.append(candidate_info)
                self.management_statistics["total_evaluated"] += 1
                
            except Exception as e:
                self.logger.warning(f"衛星 {satellite_id} 候選評估失敗: {e}")
                continue
        
        # 按分數排序並選擇前N個候選
        evaluated_satellites.sort(key=lambda x: x["candidate_score"]["total_score"], reverse=True)
        
        # 更新候選池
        self._update_candidate_pool(evaluated_satellites)
        
        # 生成換手建議
        handover_recommendations = self._generate_handover_recommendations()
        
        # 更新統計
        self.management_statistics["last_update_time"] = datetime.now(timezone.utc).isoformat()
        
        return {
            "candidate_management": {
                "total_evaluated": len(evaluated_satellites),
                "active_candidates": len(self.active_candidates),
                "candidate_pool_size": len(self.candidate_pool),
                "evaluation_time": datetime.now(timezone.utc).isoformat()
            },
            "active_candidates": list(self.active_candidates.values()),
            "handover_recommendations": handover_recommendations,
            "candidate_rankings": evaluated_satellites[:self.max_candidates * 2],  # 返回前10名供參考
            "management_statistics": self.management_statistics
        }
    
    def _calculate_candidate_score(self, satellite_signal: Dict[str, Any], satellite_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算候選衛星的綜合評分
        
        Args:
            satellite_signal: 衛星信號數據
            satellite_event: 衛星事件數據
            
        Returns:
            評分結果字典
        """
        # 1. 信號品質評分 (40%)
        signal_score = self._score_signal_quality(satellite_signal.get("signal_metrics", {}))
        
        # 2. 3GPP事件評分 (25%)
        event_score = self._score_3gpp_events(satellite_event.get("events", {}))
        
        # 3. 信號穩定性評分 (20%)
        stability_score = self._score_signal_stability(satellite_signal.get("signal_metrics", {}))
        
        # 4. 幾何條件評分 (15%)
        geometric_score = self._score_geometric_conditions(satellite_signal.get("signal_timeseries", []))
        
        # 計算加權總分
        total_score = (
            signal_score * self.scoring_weights["signal_quality"] +
            event_score * self.scoring_weights["3gpp_events"] +
            stability_score * self.scoring_weights["stability"] +
            geometric_score * self.scoring_weights["geometric"]
        )
        
        return {
            "total_score": total_score,
            "breakdown": {
                "signal_quality": signal_score,
                "3gpp_events": event_score,
                "stability": stability_score,
                "geometric": geometric_score
            },
            "weighted_scores": {
                "signal_quality": signal_score * self.scoring_weights["signal_quality"],
                "3gpp_events": event_score * self.scoring_weights["3gpp_events"],
                "stability": stability_score * self.scoring_weights["stability"],
                "geometric": geometric_score * self.scoring_weights["geometric"]
            }
        }
    
    def _score_signal_quality(self, signal_metrics: Dict[str, Any]) -> float:
        """
        評估信號品質分數 (0-100)
        
        基於RSRP, RSRQ, RS-SINR綜合評估
        """
        if not signal_metrics:
            return 0.0
        
        # RSRP評分 (50%)
        avg_rsrp = signal_metrics.get("average_rsrp_dbm", -140)
        rsrp_score = max(0, min(100, (avg_rsrp + 140) / 0.9))  # -140 to -50 dBm -> 0 to 100
        
        # RSRQ評分 (30%)
        avg_rsrq = signal_metrics.get("average_rsrq_db", -30)
        rsrq_score = max(0, min(100, (avg_rsrq + 30) / 0.33))  # -30 to 3 dB -> 0 to 100
        
        # RS-SINR評分 (20%)
        avg_sinr = signal_metrics.get("average_rs_sinr_db", -20)
        sinr_score = max(0, min(100, (avg_sinr + 20) / 0.6))   # -20 to 40 dB -> 0 to 100
        
        # 綜合評分
        quality_score = rsrp_score * 0.5 + rsrq_score * 0.3 + sinr_score * 0.2
        
        return quality_score
    
    def _score_3gpp_events(self, events: Dict[str, Any]) -> float:
        """
        評估3GPP事件分數 (0-100)
        
        基於A4/A5/D2事件的觸發情況
        """
        if not events:
            return 0.0
        
        event_score = 0.0
        
        # A4事件評分 (權重50%)
        a4_events = events.get("A4", [])
        if a4_events:
            # 有A4事件表示鄰區信號優於門檻，是好的換手候選
            a4_score = min(100, len(a4_events) * 20)  # 每個A4事件20分，最高100分
            event_score += a4_score * self.event_weights["A4"]
        
        # A5事件評分 (權重35%)
        a5_events = events.get("A5", [])
        if a5_events:
            # A5事件表示服務小區劣化且鄰區改善，是強的換手指標
            a5_score = min(100, len(a5_events) * 30)  # 每個A5事件30分
            event_score += a5_score * self.event_weights["A5"]
        
        # D2事件評分 (權重15%)
        d2_events = events.get("D2", [])
        if d2_events:
            # D2事件基於距離，是輔助換手指標
            d2_score = min(100, len(d2_events) * 25)  # 每個D2事件25分
            event_score += d2_score * self.event_weights["D2"]
        
        return min(100, event_score)
    
    def _score_signal_stability(self, signal_metrics: Dict[str, Any]) -> float:
        """
        評估信號穩定性分數 (0-100)
        
        基於信號變異性和穩定性評估
        """
        if not signal_metrics:
            return 0.0
        
        # 使用已有的穩定性分數
        stability_score = signal_metrics.get("signal_stability_score", 0)
        
        # RSRP標準差評分 (較低的標準差表示更穩定)
        rsrp_std = signal_metrics.get("rsrp_std_deviation", 10)
        std_score = max(0, 100 - rsrp_std * 10)  # 標準差越小分數越高
        
        # 綜合穩定性評分
        final_stability_score = (stability_score * 0.7 + std_score * 0.3)
        
        return min(100, final_stability_score)
    
    def _score_geometric_conditions(self, signal_timeseries: List[Dict[str, Any]]) -> float:
        """
        評估幾何條件分數 (0-100)
        
        基於仰角、距離等幾何因素
        """
        if not signal_timeseries:
            return 0.0
        
        elevations = [p.get("elevation_deg", 0) for p in signal_timeseries if p.get("is_visible", False)]
        ranges = [p.get("range_km", 9999) for p in signal_timeseries if p.get("is_visible", False)]
        
        if not elevations:
            return 0.0
        
        # 平均仰角評分 (仰角越高越好)
        avg_elevation = sum(elevations) / len(elevations)
        elevation_score = min(100, max(0, (avg_elevation - 5) * 2))  # 5度以上線性增長
        
        # 平均距離評分 (距離適中更好)
        avg_range = sum(ranges) / len(ranges)
        optimal_range = 1500  # 最佳距離1500km
        range_deviation = abs(avg_range - optimal_range)
        range_score = max(0, 100 - range_deviation / 20)  # 偏離最佳距離的懲罰
        
        # 可見性評分 (可見點比例)
        visible_count = sum(1 for p in signal_timeseries if p.get("is_visible", False))
        visibility_score = (visible_count / len(signal_timeseries)) * 100
        
        # 綜合幾何評分
        geometric_score = elevation_score * 0.4 + range_score * 0.3 + visibility_score * 0.3
        
        return geometric_score
    
    def _update_candidate_pool(self, evaluated_satellites: List[Dict[str, Any]]) -> None:
        """更新候選池"""
        # 清空現有候選
        self.active_candidates.clear()
        
        # 選擇前N個作為活躍候選
        for i, candidate in enumerate(evaluated_satellites[:self.max_candidates]):
            satellite_id = candidate["satellite_id"]
            
            # 添加候選排名
            candidate["candidate_rank"] = i + 1
            candidate["is_active_candidate"] = True
            
            self.active_candidates[satellite_id] = candidate
            self.management_statistics["candidates_added"] += 1
        
        # 將其餘衛星加入候選池（使用負分數實現最大堆）
        for candidate in evaluated_satellites[self.max_candidates:]:
            priority = -candidate["candidate_score"]["total_score"]  # 負數實現最大堆
            heapq.heappush(self.candidate_pool, (priority, candidate["satellite_id"], candidate))
    
    def _generate_handover_recommendations(self) -> Dict[str, Any]:
        """生成換手建議"""
        if not self.active_candidates:
            return {"recommendation": "no_candidates", "reason": "無可用換手候選"}
        
        # 獲取最佳候選
        best_candidate = max(self.active_candidates.values(), 
                           key=lambda x: x["candidate_score"]["total_score"])
        
        best_score = best_candidate["candidate_score"]["total_score"]
        
        # 生成換手建議
        if best_score >= 80:
            recommendation = "immediate_handover"
            reason = f"發現優秀候選 {best_candidate['satellite_id']} (分數: {best_score:.1f})"
            priority = "high"
        elif best_score >= 60:
            recommendation = "prepare_handover" 
            reason = f"發現良好候選 {best_candidate['satellite_id']} (分數: {best_score:.1f})"
            priority = "medium"
        elif best_score >= 40:
            recommendation = "monitor_candidates"
            reason = f"候選品質一般 (最佳分數: {best_score:.1f})"
            priority = "low"
        else:
            recommendation = "no_handover"
            reason = f"候選品質不足 (最佳分數: {best_score:.1f})"
            priority = "none"
        
        self.management_statistics["handover_recommendations"] += 1
        
        return {
            "recommendation": recommendation,
            "priority": priority,
            "reason": reason,
            "best_candidate": best_candidate,
            "candidate_count": len(self.active_candidates),
            "alternatives": list(self.active_candidates.values())[1:4],  # 前3個替代選項
            "recommendation_time": datetime.now(timezone.utc).isoformat()
        }
    
    def add_candidate(self, candidate_info: Dict[str, Any]) -> bool:
        """添加新候選衛星"""
        satellite_id = candidate_info.get("satellite_id")
        
        if len(self.active_candidates) < self.max_candidates:
            candidate_info["candidate_rank"] = len(self.active_candidates) + 1
            candidate_info["is_active_candidate"] = True
            self.active_candidates[satellite_id] = candidate_info
            self.management_statistics["candidates_added"] += 1
            return True
        
        # 如果候選池已滿，檢查是否比最差的候選更好
        worst_candidate_id = min(self.active_candidates.keys(), 
                               key=lambda x: self.active_candidates[x]["candidate_score"]["total_score"])
        worst_score = self.active_candidates[worst_candidate_id]["candidate_score"]["total_score"]
        new_score = candidate_info.get("candidate_score", {}).get("total_score", 0)
        
        if new_score > worst_score:
            # 移除最差候選，添加新候選
            del self.active_candidates[worst_candidate_id]
            candidate_info["candidate_rank"] = len(self.active_candidates) + 1
            candidate_info["is_active_candidate"] = True
            self.active_candidates[satellite_id] = candidate_info
            self.management_statistics["candidates_removed"] += 1
            self.management_statistics["candidates_added"] += 1
            return True
        
        return False
    
    def remove_candidate(self, satellite_id: str) -> bool:
        """移除候選衛星"""
        if satellite_id in self.active_candidates:
            del self.active_candidates[satellite_id]
            self.management_statistics["candidates_removed"] += 1
            return True
        return False
    
    def get_candidate_summary(self) -> Dict[str, Any]:
        """獲取候選管理摘要"""
        if not self.active_candidates:
            return {"status": "no_active_candidates"}
        
        scores = [c["candidate_score"]["total_score"] for c in self.active_candidates.values()]
        
        return {
            "active_candidate_count": len(self.active_candidates),
            "candidate_scores": {
                "average": sum(scores) / len(scores),
                "highest": max(scores),
                "lowest": min(scores)
            },
            "candidate_constellations": {
                constellation: sum(1 for c in self.active_candidates.values() 
                                if c.get("constellation") == constellation)
                for constellation in set(c.get("constellation") for c in self.active_candidates.values())
            },
            "management_statistics": self.management_statistics,
            "last_update": self.management_statistics["last_update_time"]
        }