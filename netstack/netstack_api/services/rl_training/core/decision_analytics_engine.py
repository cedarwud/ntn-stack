"""
決策分析引擎 - AI 決策可解釋性和分析

提供完整的決策分析和可解釋性功能，包括：
- 決策過程記錄和分析
- AI 可解釋性數據生成
- 決策因子分析
- 決策質量評估
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import math

logger = logging.getLogger(__name__)

class DecisionAnalyticsEngine:
    """決策分析引擎"""
    
    def __init__(self):
        self.decision_history: List[Dict[str, Any]] = []
        self.analysis_cache: Dict[str, Any] = {}
    
    async def explain_decision(
        self,
        decision: Dict[str, Any],
        algorithm: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成決策解釋
        
        提供 AI 可解釋性數據，說明決策的推理過程
        """
        try:
            explanation = {
                "decision_id": f"decision_{int(datetime.now().timestamp())}",
                "algorithm": algorithm,
                "timestamp": datetime.now().isoformat(),
                "decision_factors": [],
                "confidence_breakdown": {},
                "reasoning_path": [],
                "alternative_actions": [],
                "risk_assessment": {}
            }
            
            # 分析決策因子
            decision_factors = await self._analyze_decision_factors(decision, state, algorithm)
            explanation["decision_factors"] = decision_factors
            
            # 置信度分解
            confidence_breakdown = await self._analyze_confidence(decision, algorithm)
            explanation["confidence_breakdown"] = confidence_breakdown
            
            # 推理路徑
            reasoning_path = await self._generate_reasoning_path(decision, state, algorithm)
            explanation["reasoning_path"] = reasoning_path
            
            # 替代動作分析
            alternatives = await self._analyze_alternatives(decision, state, algorithm)
            explanation["alternative_actions"] = alternatives
            
            # 風險評估
            risk_assessment = await self._assess_decision_risk(decision, state)
            explanation["risk_assessment"] = risk_assessment
            
            # 記錄決策歷史
            await self._record_decision(decision, explanation)
            
            return explanation
            
        except Exception as e:
            logger.error(f"決策解釋失敗: {e}")
            return {"error": str(e)}
    
    async def _analyze_decision_factors(
        self,
        decision: Dict[str, Any],
        state: Dict[str, Any],
        algorithm: str
    ) -> List[Dict[str, Any]]:
        """分析影響決策的因子"""
        try:
            factors = []
            
            # 模擬決策因子分析
            if algorithm == "dqn":
                factors = [
                    {"factor": "q_value", "importance": 0.4, "value": 0.75, "impact": "positive"},
                    {"factor": "exploration", "importance": 0.2, "value": 0.1, "impact": "neutral"},
                    {"factor": "state_confidence", "importance": 0.3, "value": 0.8, "impact": "positive"},
                    {"factor": "reward_prediction", "importance": 0.1, "value": 0.6, "impact": "positive"}
                ]
            elif algorithm == "ppo":
                factors = [
                    {"factor": "policy_probability", "importance": 0.5, "value": 0.85, "impact": "positive"},
                    {"factor": "value_estimate", "importance": 0.3, "value": 0.7, "impact": "positive"},
                    {"factor": "entropy_bonus", "importance": 0.1, "value": 0.05, "impact": "neutral"},
                    {"factor": "advantage", "importance": 0.1, "value": 0.4, "impact": "positive"}
                ]
            elif algorithm == "sac":
                factors = [
                    {"factor": "actor_output", "importance": 0.4, "value": 0.8, "impact": "positive"},
                    {"factor": "critic_value", "importance": 0.3, "value": 0.75, "impact": "positive"},
                    {"factor": "entropy_regularization", "importance": 0.2, "value": 0.2, "impact": "positive"},
                    {"factor": "temperature", "importance": 0.1, "value": 0.1, "impact": "neutral"}
                ]
            else:
                factors = [{"factor": "unknown", "importance": 1.0, "value": 0.5, "impact": "neutral"}]
            
            return factors
            
        except Exception as e:
            logger.error(f"決策因子分析失敗: {e}")
            return []
    
    async def _analyze_confidence(self, decision: Dict[str, Any], algorithm: str) -> Dict[str, Any]:
        """分析決策置信度"""
        try:
            base_confidence = decision.get("confidence", 0.7)
            
            confidence_breakdown = {
                "overall_confidence": base_confidence,
                "factors": {
                    "model_certainty": base_confidence * 0.4,
                    "state_clarity": base_confidence * 0.3,
                    "historical_performance": base_confidence * 0.2,
                    "context_similarity": base_confidence * 0.1
                },
                "confidence_level": self._categorize_confidence(base_confidence)
            }
            
            return confidence_breakdown
            
        except Exception as e:
            logger.error(f"置信度分析失敗: {e}")
            return {"overall_confidence": 0.5}
    
    def _categorize_confidence(self, confidence: float) -> str:
        """將置信度分類"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        elif confidence >= 0.4:
            return "low"
        else:
            return "very_low"
    
    async def _generate_reasoning_path(
        self,
        decision: Dict[str, Any],
        state: Dict[str, Any],
        algorithm: str
    ) -> List[Dict[str, Any]]:
        """生成推理路徑"""
        try:
            reasoning_steps = []
            
            # 模擬推理步驟
            reasoning_steps.append({
                "step": 1,
                "description": "狀態輸入處理",
                "details": "接收當前環境狀態並進行預處理",
                "confidence": 0.9
            })
            
            reasoning_steps.append({
                "step": 2,
                "description": f"{algorithm.upper()} 模型推理",
                "details": f"使用 {algorithm} 算法計算動作概率",
                "confidence": 0.8
            })
            
            reasoning_steps.append({
                "step": 3,
                "description": "動作選擇",
                "details": "基於模型輸出選擇最優動作",
                "confidence": decision.get("confidence", 0.7)
            })
            
            reasoning_steps.append({
                "step": 4,
                "description": "決策驗證",
                "details": "驗證選擇的動作是否符合約束條件",
                "confidence": 0.85
            })
            
            return reasoning_steps
            
        except Exception as e:
            logger.error(f"推理路徑生成失敗: {e}")
            return []
    
    async def _analyze_alternatives(
        self,
        decision: Dict[str, Any],
        state: Dict[str, Any],
        algorithm: str
    ) -> List[Dict[str, Any]]:
        """分析替代動作"""
        try:
            alternatives = []
            
            # 模擬替代動作分析
            chosen_action = decision.get("action", 0)
            
            for i in range(4):  # 假設有4個可能動作
                if i != chosen_action:
                    # 計算替代動作的分數
                    score = 0.8 - (abs(i - chosen_action) * 0.15)
                    alternatives.append({
                        "action": i,
                        "score": max(0.1, score),
                        "probability": max(0.05, score * 0.3),
                        "reason_not_chosen": f"分數比所選動作低 {(0.8 - score):.2f}"
                    })
            
            # 按分數排序
            alternatives.sort(key=lambda x: x["score"], reverse=True)
            
            return alternatives[:3]  # 返回前3個替代方案
            
        except Exception as e:
            logger.error(f"替代動作分析失敗: {e}")
            return []
    
    async def _assess_decision_risk(
        self,
        decision: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """評估決策風險"""
        try:
            # 模擬風險評估
            confidence = decision.get("confidence", 0.7)
            
            # 基礎風險評估
            base_risk = 1 - confidence
            
            risk_factors = {
                "model_uncertainty": base_risk * 0.4,
                "environment_volatility": 0.2,
                "action_consequences": base_risk * 0.3,
                "recovery_difficulty": 0.1
            }
            
            overall_risk = sum(risk_factors.values()) / len(risk_factors)
            
            risk_assessment = {
                "overall_risk": overall_risk,
                "risk_factors": risk_factors,
                "risk_level": self._categorize_risk(overall_risk),
                "mitigation_strategies": self._suggest_mitigation(overall_risk),
                "worst_case_scenario": "決策失敗可能導致性能下降",
                "recovery_plan": "切換到備用算法或回退到安全動作"
            }
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"風險評估失敗: {e}")
            return {"overall_risk": 0.5}
    
    def _categorize_risk(self, risk: float) -> str:
        """風險等級分類"""
        if risk >= 0.7:
            return "high"
        elif risk >= 0.4:
            return "medium"
        elif risk >= 0.2:
            return "low"
        else:
            return "minimal"
    
    def _suggest_mitigation(self, risk: float) -> List[str]:
        """建議風險緩解策略"""
        strategies = []
        
        if risk >= 0.7:
            strategies.extend([
                "考慮使用更保守的動作",
                "增加人工監督",
                "實施備用決策機制"
            ])
        elif risk >= 0.4:
            strategies.extend([
                "增加決策驗證步驟",
                "監控決策結果"
            ])
        else:
            strategies.append("維持當前決策策略")
        
        return strategies
    
    async def _record_decision(self, decision: Dict[str, Any], explanation: Dict[str, Any]):
        """記錄決策歷史"""
        try:
            decision_record = {
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "explanation": explanation,
                "recorded_at": datetime.now()
            }
            
            self.decision_history.append(decision_record)
            
            # 限制歷史記錄大小
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-500:]
            
        except Exception as e:
            logger.error(f"決策記錄失敗: {e}")
    
    async def get_decision_analytics(
        self,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """獲取決策分析報告"""
        try:
            cutoff_time = datetime.now().timestamp() - (time_range_hours * 3600)
            
            recent_decisions = [
                d for d in self.decision_history
                if d["recorded_at"].timestamp() > cutoff_time
            ]
            
            if not recent_decisions:
                return {"message": "指定時間範圍內無決策記錄"}
            
            analytics = {
                "time_range_hours": time_range_hours,
                "total_decisions": len(recent_decisions),
                "average_confidence": self._calculate_average_confidence(recent_decisions),
                "confidence_distribution": self._analyze_confidence_distribution(recent_decisions),
                "risk_distribution": self._analyze_risk_distribution(recent_decisions),
                "algorithm_usage": self._analyze_algorithm_usage(recent_decisions),
                "decision_patterns": self._analyze_decision_patterns(recent_decisions)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"決策分析報告生成失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_average_confidence(self, decisions: List[Dict[str, Any]]) -> float:
        """計算平均置信度"""
        if not decisions:
            return 0.0
        
        total_confidence = sum(
            d["explanation"]["confidence_breakdown"]["overall_confidence"]
            for d in decisions
            if "confidence_breakdown" in d["explanation"]
        )
        
        return total_confidence / len(decisions)
    
    def _analyze_confidence_distribution(self, decisions: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析置信度分佈"""
        distribution = {"high": 0, "medium": 0, "low": 0, "very_low": 0}
        
        for decision in decisions:
            confidence = decision["explanation"]["confidence_breakdown"]["overall_confidence"]
            level = self._categorize_confidence(confidence)
            distribution[level] += 1
        
        return distribution
    
    def _analyze_risk_distribution(self, decisions: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析風險分佈"""
        distribution = {"high": 0, "medium": 0, "low": 0, "minimal": 0}
        
        for decision in decisions:
            if "risk_assessment" in decision["explanation"]:
                risk = decision["explanation"]["risk_assessment"]["overall_risk"]
                level = self._categorize_risk(risk)
                distribution[level] += 1
        
        return distribution
    
    def _analyze_algorithm_usage(self, decisions: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析算法使用情況"""
        usage = {}
        
        for decision in decisions:
            algorithm = decision["explanation"]["algorithm"]
            usage[algorithm] = usage.get(algorithm, 0) + 1
        
        return usage
    
    def _analyze_decision_patterns(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析決策模式"""
        patterns = {
            "most_common_factors": {},
            "confidence_trends": "stable",  # 可以實現更複雜的趨勢分析
            "risk_trends": "stable",
            "decision_frequency": len(decisions) / 24 if decisions else 0  # 每小時決策數
        }
        
        # 分析最常見的決策因子
        factor_counts = {}
        for decision in decisions:
            factors = decision["explanation"]["decision_factors"]
            for factor in factors:
                factor_name = factor["factor"]
                factor_counts[factor_name] = factor_counts.get(factor_name, 0) + 1
        
        # 獲取前5個最常見因子
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        patterns["most_common_factors"] = dict(sorted_factors[:5])
        
        return patterns
    
    async def export_decision_data(
        self,
        format_type: str = "json",
        time_range_hours: int = 24
    ) -> str:
        """導出決策數據"""
        try:
            cutoff_time = datetime.now().timestamp() - (time_range_hours * 3600)
            
            recent_decisions = [
                d for d in self.decision_history
                if d["recorded_at"].timestamp() > cutoff_time
            ]
            
            if format_type == "json":
                return json.dumps(recent_decisions, default=str, indent=2)
            else:
                return "不支援的格式類型"
                
        except Exception as e:
            logger.error(f"決策數據導出失敗: {e}")
            return f"導出失敗: {str(e)}"
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取分析引擎狀態"""
        return {
            "total_decisions_recorded": len(self.decision_history),
            "cache_size": len(self.analysis_cache),
            "status": "operational",
            "capabilities": [
                "decision_explanation",
                "confidence_analysis",
                "risk_assessment",
                "alternative_analysis",
                "decision_analytics"
            ]
        }