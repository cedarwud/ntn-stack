"""
智能換手決策引擎 - Stage 4模組化組件

職責：
1. 基於3GPP事件進行換手決策
2. 實現多因素綜合評估
3. 支援即時決策和預測性決策
4. 提供決策解釋和置信度評估
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class HandoverDecisionType(Enum):
    """換手決策類型"""
    NO_HANDOVER = "no_handover"
    PREPARE_HANDOVER = "prepare_handover"
    IMMEDIATE_HANDOVER = "immediate_handover"
    EMERGENCY_HANDOVER = "emergency_handover"

class HandoverTriggerReason(Enum):
    """換手觸發原因"""
    SIGNAL_DEGRADATION = "signal_degradation"
    BETTER_NEIGHBOR = "better_neighbor"
    DUAL_THRESHOLD = "dual_threshold"
    DISTANCE_BASED = "distance_based"
    QUALITY_IMPROVEMENT = "quality_improvement"
    LOAD_BALANCING = "load_balancing"

class HandoverDecisionEngine:
    """
    智能換手決策引擎
    
    基於3GPP TS 38.331標準和LEO衛星特性：
    - A4/A5/D2事件驅動決策
    - 多候選衛星比較
    - 決策置信度評估
    - 預測性換手支援
    """
    
    def __init__(self):
        """初始化換手決策引擎"""
        self.logger = logging.getLogger(f"{__name__}.HandoverDecisionEngine")
        
        # 決策門檻配置
        self.decision_thresholds = {
            "immediate_handover": {
                "min_candidate_score": 80.0,
                "min_signal_improvement": 10.0,  # dB
                "min_confidence": 0.85
            },
            "prepare_handover": {
                "min_candidate_score": 60.0,
                "min_signal_improvement": 5.0,   # dB
                "min_confidence": 0.70
            },
            "emergency_handover": {
                "current_signal_threshold": -115.0,  # dBm
                "min_candidate_score": 40.0,
                "override_confidence": True
            }
        }
        
        # 3GPP事件權重 (用於決策)
        self.event_decision_weights = {
            "A4": 0.30,  # 鄰區優於門檻
            "A5": 0.50,  # 雙門檻條件 (最重要)
            "D2": 0.20   # 距離基礎
        }
        
        # 決策因素權重
        self.decision_factors = {
            "signal_improvement": 0.35,    # 信號改善
            "event_strength": 0.25,       # 3GPP事件強度
            "candidate_quality": 0.20,    # 候選品質
            "stability_risk": 0.20        # 穩定性風險
        }
        
        # 決策歷史
        self.decision_history = []
        
        # 統計數據
        self.decision_statistics = {
            "total_decisions": 0,
            "immediate_handovers": 0,
            "prepare_handovers": 0,
            "emergency_handovers": 0,
            "no_handovers": 0,
            "average_confidence": 0.0,
            "decision_accuracy": 0.0  # 需要回饋機制更新
        }
        
        self.logger.info("✅ 智能換手決策引擎初始化完成")
        self.logger.info(f"   決策因素權重: 信號改善{self.decision_factors['signal_improvement']*100:.0f}% + 事件強度{self.decision_factors['event_strength']*100:.0f}% + 候選品質{self.decision_factors['candidate_quality']*100:.0f}% + 穩定性{self.decision_factors['stability_risk']*100:.0f}%")
    
    def make_handover_decision(self, current_serving: Dict[str, Any], 
                             candidates: List[Dict[str, Any]], 
                             network_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        做出換手決策
        
        Args:
            current_serving: 當前服務衛星數據
            candidates: 候選衛星列表
            network_context: 網路環境上下文（可選）
            
        Returns:
            決策結果字典
        """
        self.logger.info(f"🎯 開始換手決策分析...")
        self.logger.info(f"   當前服務: {current_serving.get('satellite_id', 'unknown')}")
        self.logger.info(f"   候選數量: {len(candidates)}")
        
        decision_start_time = datetime.now(timezone.utc)
        
        # 如果沒有候選，直接返回
        if not candidates:
            return self._create_decision_result(
                HandoverDecisionType.NO_HANDOVER, 
                None, 
                "無可用換手候選", 
                0.0,
                decision_start_time
            )
        
        # 1. 評估當前服務狀態
        serving_status = self._evaluate_serving_status(current_serving)
        
        # 2. 評估最佳候選
        best_candidate = self._select_best_candidate(candidates, current_serving)
        
        # 3. 分析3GPP事件
        event_analysis = self._analyze_handover_events(current_serving, best_candidate)
        
        # 4. 計算決策因素
        decision_factors = self._calculate_decision_factors(
            current_serving, best_candidate, event_analysis
        )
        
        # 5. 生成決策建議
        decision_type, confidence = self._determine_handover_action(
            serving_status, decision_factors, event_analysis
        )
        
        # 6. 生成決策解釋
        decision_reasoning = self._generate_decision_reasoning(
            decision_type, serving_status, decision_factors, event_analysis
        )
        
        # 7. 創建完整決策結果
        decision_result = self._create_decision_result(
            decision_type,
            best_candidate,
            decision_reasoning,
            confidence,
            decision_start_time,
            {
                "serving_status": serving_status,
                "decision_factors": decision_factors,
                "event_analysis": event_analysis,
                "alternatives": candidates[1:4] if len(candidates) > 1 else []
            }
        )
        
        # 8. 記錄決策歷史
        self._record_decision(decision_result)
        
        self.logger.info(f"✅ 決策完成: {decision_type.value} (置信度: {confidence:.2f})")
        
        return decision_result
    
    def _evaluate_serving_status(self, serving_satellite: Dict[str, Any]) -> Dict[str, Any]:
        """評估當前服務衛星狀態"""
        signal_metrics = serving_satellite.get("signal_metrics", {})
        
        # 信號品質評估
        avg_rsrp = signal_metrics.get("average_rsrp_dbm", -140)
        avg_rsrq = signal_metrics.get("average_rsrq_db", -30)
        avg_sinr = signal_metrics.get("average_rs_sinr_db", -20)
        
        # 信號品質分級
        if avg_rsrp >= -85:
            signal_grade = "excellent"
            signal_score = 100
        elif avg_rsrp >= -95:
            signal_grade = "good"
            signal_score = 80
        elif avg_rsrp >= -105:
            signal_grade = "fair"
            signal_score = 60
        elif avg_rsrp >= -115:
            signal_grade = "poor"
            signal_score = 40
        else:
            signal_grade = "critical"
            signal_score = 20
        
        # 穩定性評估
        stability_score = signal_metrics.get("signal_stability_score", 0)
        rsrp_std = signal_metrics.get("rsrp_std_deviation", 10)
        
        # 是否需要緊急換手
        needs_emergency = avg_rsrp < self.decision_thresholds["emergency_handover"]["current_signal_threshold"]
        
        return {
            "signal_quality": {
                "rsrp_dbm": avg_rsrp,
                "rsrq_db": avg_rsrq,
                "rs_sinr_db": avg_sinr,
                "grade": signal_grade,
                "score": signal_score
            },
            "stability": {
                "stability_score": stability_score,
                "rsrp_std_deviation": rsrp_std,
                "is_stable": stability_score >= 70 and rsrp_std <= 5
            },
            "handover_urgency": {
                "needs_emergency": needs_emergency,
                "degradation_risk": signal_score < 50,
                "quality_acceptable": signal_score >= 60
            }
        }
    
    def _select_best_candidate(self, candidates: List[Dict[str, Any]], 
                             current_serving: Dict[str, Any]) -> Dict[str, Any]:
        """選擇最佳候選衛星"""
        if not candidates:
            return None
        
        # 按候選分數排序
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: x.get("candidate_score", {}).get("total_score", 0), 
            reverse=True
        )
        
        return sorted_candidates[0]
    
    def _analyze_handover_events(self, serving: Dict[str, Any], 
                                candidate: Dict[str, Any]) -> Dict[str, Any]:
        """分析換手相關的3GPP事件"""
        if not candidate:
            return {"event_strength": 0, "dominant_event": None, "event_details": {}}
        
        candidate_events = candidate.get("event_analysis", {})
        
        # 計算事件強度
        event_strength = 0.0
        event_details = {}
        dominant_event = None
        max_event_impact = 0.0
        
        # 分析A4事件
        a4_events = candidate_events.get("A4", [])
        if a4_events:
            a4_impact = len(a4_events) * self.event_decision_weights["A4"]
            event_strength += a4_impact
            event_details["A4"] = {
                "event_count": len(a4_events),
                "impact_score": a4_impact,
                "description": "鄰區信號優於門檻"
            }
            if a4_impact > max_event_impact:
                max_event_impact = a4_impact
                dominant_event = "A4"
        
        # 分析A5事件
        a5_events = candidate_events.get("A5", [])
        if a5_events:
            a5_impact = len(a5_events) * self.event_decision_weights["A5"]
            event_strength += a5_impact
            event_details["A5"] = {
                "event_count": len(a5_events),
                "impact_score": a5_impact,
                "description": "服務衛星劣化且鄰區改善"
            }
            if a5_impact > max_event_impact:
                max_event_impact = a5_impact
                dominant_event = "A5"
        
        # 分析D2事件
        d2_events = candidate_events.get("D2", [])
        if d2_events:
            d2_impact = len(d2_events) * self.event_decision_weights["D2"]
            event_strength += d2_impact
            event_details["D2"] = {
                "event_count": len(d2_events),
                "impact_score": d2_impact,
                "description": "距離基礎換手條件"
            }
            if d2_impact > max_event_impact:
                max_event_impact = d2_impact
                dominant_event = "D2"
        
        return {
            "event_strength": min(100, event_strength * 50),  # 正規化到0-100
            "dominant_event": dominant_event,
            "event_details": event_details,
            "has_strong_events": event_strength > 0.8
        }
    
    def _calculate_decision_factors(self, serving: Dict[str, Any], 
                                  candidate: Dict[str, Any], 
                                  event_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """計算決策因素"""
        if not candidate:
            return {factor: 0.0 for factor in self.decision_factors.keys()}
        
        serving_metrics = serving.get("signal_metrics", {})
        candidate_metrics = candidate.get("signal_metrics", {})
        
        # 1. 信號改善因素
        serving_rsrp = serving_metrics.get("average_rsrp_dbm", -140)
        candidate_rsrp = candidate_metrics.get("average_rsrp_dbm", -140)
        signal_improvement = candidate_rsrp - serving_rsrp
        
        # 正規化信號改善分數 (0-100)
        signal_improvement_score = max(0, min(100, (signal_improvement + 10) * 5))
        
        # 2. 3GPP事件強度 (直接使用分析結果)
        event_strength_score = event_analysis.get("event_strength", 0)
        
        # 3. 候選品質因素
        candidate_quality_score = candidate.get("candidate_score", {}).get("total_score", 0)
        
        # 4. 穩定性風險因素
        serving_stability = serving_metrics.get("signal_stability_score", 0)
        candidate_stability = candidate_metrics.get("signal_stability_score", 0)
        
        # 穩定性風險：如果候選比服務衛星不穩定，風險增加
        stability_risk = max(0, serving_stability - candidate_stability)
        stability_risk_score = max(0, 100 - stability_risk)
        
        return {
            "signal_improvement": signal_improvement_score,
            "event_strength": event_strength_score,
            "candidate_quality": candidate_quality_score,
            "stability_risk": stability_risk_score,
            "raw_values": {
                "signal_improvement_db": signal_improvement,
                "serving_rsrp": serving_rsrp,
                "candidate_rsrp": candidate_rsrp,
                "serving_stability": serving_stability,
                "candidate_stability": candidate_stability
            }
        }
    
    def _determine_handover_action(self, serving_status: Dict[str, Any], 
                                 decision_factors: Dict[str, Any], 
                                 event_analysis: Dict[str, Any]) -> Tuple[HandoverDecisionType, float]:
        """決定換手動作和置信度"""
        
        # 計算綜合決策分數
        decision_score = sum(
            decision_factors[factor] * weight 
            for factor, weight in self.decision_factors.items()
        )
        
        # 檢查緊急換手條件
        if serving_status.get("handover_urgency", {}).get("needs_emergency", False):
            if decision_factors["candidate_quality"] >= self.decision_thresholds["emergency_handover"]["min_candidate_score"]:
                confidence = 0.95  # 緊急情況下高置信度
                return HandoverDecisionType.EMERGENCY_HANDOVER, confidence
        
        # 檢查立即換手條件
        if (decision_score >= 75 and 
            decision_factors["candidate_quality"] >= self.decision_thresholds["immediate_handover"]["min_candidate_score"] and
            decision_factors["signal_improvement"] >= 60):
            
            confidence = min(0.95, 0.6 + decision_score / 200)
            return HandoverDecisionType.IMMEDIATE_HANDOVER, confidence
        
        # 檢查準備換手條件
        if (decision_score >= 55 and
            decision_factors["candidate_quality"] >= self.decision_thresholds["prepare_handover"]["min_candidate_score"]):
            
            confidence = min(0.85, 0.5 + decision_score / 200)
            return HandoverDecisionType.PREPARE_HANDOVER, confidence
        
        # 預設不換手
        confidence = max(0.3, 1.0 - decision_score / 100)
        return HandoverDecisionType.NO_HANDOVER, confidence
    
    def _generate_decision_reasoning(self, decision_type: HandoverDecisionType,
                                   serving_status: Dict[str, Any],
                                   decision_factors: Dict[str, Any],
                                   event_analysis: Dict[str, Any]) -> str:
        """生成決策解釋"""
        
        reasoning_parts = []
        
        # 基於決策類型的主要原因
        if decision_type == HandoverDecisionType.EMERGENCY_HANDOVER:
            reasoning_parts.append(f"緊急換手：當前信號嚴重劣化 (RSRP: {serving_status['signal_quality']['rsrp_dbm']:.1f} dBm)")
        
        elif decision_type == HandoverDecisionType.IMMEDIATE_HANDOVER:
            reasoning_parts.append("立即換手：")
            if decision_factors["signal_improvement"] >= 60:
                improvement = decision_factors["raw_values"]["signal_improvement_db"]
                reasoning_parts.append(f"顯著信號改善 (+{improvement:.1f} dB)")
            if event_analysis.get("has_strong_events"):
                reasoning_parts.append(f"強烈3GPP事件觸發 ({event_analysis.get('dominant_event')})")
        
        elif decision_type == HandoverDecisionType.PREPARE_HANDOVER:
            reasoning_parts.append("準備換手：")
            reasoning_parts.append(f"候選品質良好 (分數: {decision_factors['candidate_quality']:.1f})")
            if event_analysis.get("dominant_event"):
                reasoning_parts.append(f"3GPP {event_analysis['dominant_event']}事件觸發")
        
        else:  # NO_HANDOVER
            reasoning_parts.append("維持當前連接：")
            if serving_status["signal_quality"]["score"] >= 60:
                reasoning_parts.append("當前信號品質可接受")
            if decision_factors["candidate_quality"] < 60:
                reasoning_parts.append("候選品質不足")
            if decision_factors["signal_improvement"] < 40:
                reasoning_parts.append("信號改善有限")
        
        # 添加事件分析
        if event_analysis.get("dominant_event"):
            event_details = event_analysis["event_details"].get(event_analysis["dominant_event"], {})
            reasoning_parts.append(f" | 主導事件: {event_analysis['dominant_event']} ({event_details.get('description', '')})")
        
        return " ".join(reasoning_parts)
    
    def _create_decision_result(self, decision_type: HandoverDecisionType,
                              best_candidate: Dict[str, Any],
                              reasoning: str,
                              confidence: float,
                              start_time: datetime,
                              additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """創建決策結果"""
        
        result = {
            "decision": {
                "type": decision_type.value,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            },
            "recommended_target": best_candidate.get("satellite_id") if best_candidate else None,
            "target_details": best_candidate if best_candidate else None,
            "decision_engine_version": "v1.0",
            "3gpp_compliant": True
        }
        
        # 添加額外數據
        if additional_data:
            result.update(additional_data)
        
        return result
    
    def _record_decision(self, decision_result: Dict[str, Any]) -> None:
        """記錄決策歷史"""
        decision_type = decision_result["decision"]["type"]
        
        # 更新統計
        self.decision_statistics["total_decisions"] += 1
        
        if decision_type == HandoverDecisionType.IMMEDIATE_HANDOVER.value:
            self.decision_statistics["immediate_handovers"] += 1
        elif decision_type == HandoverDecisionType.PREPARE_HANDOVER.value:
            self.decision_statistics["prepare_handovers"] += 1
        elif decision_type == HandoverDecisionType.EMERGENCY_HANDOVER.value:
            self.decision_statistics["emergency_handovers"] += 1
        else:
            self.decision_statistics["no_handovers"] += 1
        
        # 更新平均置信度
        total = self.decision_statistics["total_decisions"]
        current_avg = self.decision_statistics["average_confidence"]
        new_confidence = decision_result["decision"]["confidence"]
        self.decision_statistics["average_confidence"] = (current_avg * (total - 1) + new_confidence) / total
        
        # 記錄到歷史 (保留最近100個決策)
        self.decision_history.append({
            "decision_type": decision_type,
            "confidence": new_confidence,
            "timestamp": decision_result["decision"]["timestamp"],
            "target": decision_result.get("recommended_target"),
            "reasoning": decision_result["decision"]["reasoning"]
        })
        
        if len(self.decision_history) > 100:
            self.decision_history.pop(0)
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """獲取決策統計"""
        return {
            "statistics": self.decision_statistics.copy(),
            "recent_decisions": self.decision_history[-10:],  # 最近10個決策
            "decision_distribution": {
                "immediate_handover_rate": self.decision_statistics["immediate_handovers"] / max(1, self.decision_statistics["total_decisions"]),
                "prepare_handover_rate": self.decision_statistics["prepare_handovers"] / max(1, self.decision_statistics["total_decisions"]),
                "emergency_handover_rate": self.decision_statistics["emergency_handovers"] / max(1, self.decision_statistics["total_decisions"]),
                "no_handover_rate": self.decision_statistics["no_handovers"] / max(1, self.decision_statistics["total_decisions"])
            }
        }