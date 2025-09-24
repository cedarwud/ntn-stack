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

# 🚨 Grade A要求：動態計算RSRP閾值
noise_floor = -120  # 3GPP典型噪聲門檻
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    AI-powered recommendation engine for satellite handover optimization.
    
    Provides intelligent recommendations for handover decisions based on
    machine learning models, signal prediction, and network optimization.
    """
    
    def __init__(self):
        """Initialize recommendation engine."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Recommendation weights
        self.weights = {
            'signal_quality': 0.35,
            'stability': 0.25,
            'prediction': 0.20,
            'latency': 0.10,
            'energy': 0.10
        }
        
        # Learning parameters
        self.learning_rate = 0.01
        self.confidence_threshold = 0.7
        
    def generate_recommendations(self, handover_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate intelligent handover recommendations.
        
        Args:
            handover_data: Handover decision data from decision engine
            
        Returns:
            Dict containing AI-powered recommendations
        """
        try:
            candidates = handover_data.get('handover_decisions', [])
            best_candidate = handover_data.get('best_candidate')
            
            if not candidates:
                return self._generate_no_candidate_recommendation()
            
            # Generate recommendations for each candidate
            candidate_recommendations = []
            for candidate in candidates:
                rec = self._analyze_candidate(candidate)
                candidate_recommendations.append(rec)
            
            # Generate overall strategy
            strategy = self._generate_handover_strategy(candidate_recommendations, best_candidate)
            
            # Create optimization suggestions
            optimizations = self._suggest_optimizations(candidate_recommendations)
            
            # Risk assessment
            risk_analysis = self._assess_handover_risks(candidate_recommendations)
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_candidates': len(candidates),
                'candidate_recommendations': candidate_recommendations,
                'handover_strategy': strategy,
                'optimization_suggestions': optimizations,
                'risk_analysis': risk_analysis,
                'confidence_score': self._calculate_confidence(candidate_recommendations),
                'next_review_time': self._calculate_next_review()
            }
            
        except Exception as e:
            self.logger.error(f"推薦引擎失敗: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _analyze_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual handover candidate."""
        satellite_id = candidate.get('satellite_id', 'unknown')
        handover_score = candidate.get('handover_score', 0)
        signal_metrics = candidate.get('signal_metrics', {})
        prediction = candidate.get('prediction', {})
        
        # Calculate recommendation score
        rec_score = self._calculate_recommendation_score(candidate)
        
        # Generate specific recommendations
        recommendations = self._generate_candidate_recommendations(candidate)
        
        # Assess suitability
        suitability = self._assess_candidate_suitability(candidate)
        
        return {
            'satellite_id': satellite_id,
            'recommendation_score': round(rec_score, 1),
            'handover_score': handover_score,
            'suitability': suitability,
            'recommendations': recommendations,
            'pros': self._identify_pros(candidate),
            'cons': self._identify_cons(candidate),
            'optimal_timing': self._suggest_optimal_timing(candidate),
            'preparation_steps': self._suggest_preparation_steps(candidate)
        }
    
    def _calculate_recommendation_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate AI-powered recommendation score."""
        
        # Signal quality factor
        signal_metrics = candidate.get('signal_metrics', {})
        signal_score = signal_metrics.get('quality_score', 0)
        
        # Stability factor
        prediction = candidate.get('prediction', {})
        trend = prediction.get('trend', 'STABLE')
        stability_score = {'IMPROVING': 90, 'STABLE': 70, 'DEGRADING': 30}.get(trend, 50)
        
        # Prediction confidence
        confidence = prediction.get('confidence', 0.5)
        prediction_score = confidence * 100
        
        # Latency factor (based on handover type)
        handover_type = candidate.get('handover_type', 'UNKNOWN')
        latency_score = {'SEAMLESS': 95, 'MAKE_BEFORE_BREAK': 80, 'BREAK_BEFORE_MAKE': 60}.get(handover_type, 50)
        
        # Energy efficiency (based on signal strength)
        rsrp = signal_metrics.get('rsrp_dbm', -100)
        energy_score = max(0, min(100, (rsrp + 120) * 5))  # -120 to -70 dBm range
        
        # Weighted score
        total_score = (
            signal_score * self.weights['signal_quality'] +
            stability_score * self.weights['stability'] +
            prediction_score * self.weights['prediction'] +
            latency_score * self.weights['latency'] +
            energy_score * self.weights['energy']
        )
        
        return min(100, max(0, total_score))
    
    def _generate_candidate_recommendations(self, candidate: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for candidate."""
        recommendations = []
        
        signal_metrics = candidate.get('signal_metrics', {})
        rsrp = signal_metrics.get('rsrp_dbm', -100)
        prediction = candidate.get('prediction', {})
        
        # Signal quality recommendations
        if rsrp >= -80:
            recommendations.append("優秀信號強度，建議立即執行無縫切換")
        elif rsrp >= -95:
            recommendations.append("良好信號品質，可安全執行切換")
        else:
            recommendations.append("信號較弱，建議等待更好時機或選擇其他候選")
        
        # Trend-based recommendations
        trend = prediction.get('trend', 'STABLE')
        if trend == 'IMPROVING':
            recommendations.append("信號趨勢向好，未來5分鐘內執行最佳")
        elif trend == 'DEGRADING':
            recommendations.append("信號衰減中，建議盡快執行或考慮其他選項")
        
        # Timing recommendations
        window_sec = prediction.get('handover_window_sec', 0)
        if window_sec > 300:
            recommendations.append(f"切換窗口充足({window_sec}秒)，可從容準備")
        else:
            recommendations.append(f"切換窗口較短({window_sec}秒)，需快速決策")
        
        return recommendations
    
    def _assess_candidate_suitability(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall suitability of candidate."""
        rec_score = self._calculate_recommendation_score(candidate)
        priority = candidate.get('priority', 'LOW')
        
        if rec_score >= 85 and priority == 'HIGH':
            suitability = 'HIGHLY_SUITABLE'
        elif rec_score >= 70:
            suitability = 'SUITABLE'
        elif rec_score >= 50:
            suitability = 'MARGINAL'
        else:
            suitability = 'NOT_SUITABLE'
        
        return {
            'level': suitability,
            'score': rec_score,
            'confidence': min(1.0, rec_score / 100),
            'recommendation': self._get_suitability_recommendation(suitability)
        }
    
    def _get_suitability_recommendation(self, suitability: str) -> str:
        """Get recommendation based on suitability."""
        recommendations = {
            'HIGHLY_SUITABLE': '強烈推薦立即執行切換',
            'SUITABLE': '推薦執行切換，風險可控',
            'MARGINAL': '謹慎考慮，建議監控後決定',
            'NOT_SUITABLE': '不建議切換，尋找其他選項'
        }
        return recommendations.get(suitability, '需要進一步分析')
    
    def _identify_pros(self, candidate: Dict[str, Any]) -> List[str]:
        """Identify pros of handover candidate."""
        pros = []
        
        signal_metrics = candidate.get('signal_metrics', {})
        rsrp = signal_metrics.get('rsrp_dbm', -100)
        handover_type = candidate.get('handover_type', 'UNKNOWN')
        prediction = candidate.get('prediction', {})
        
        # 🔧 修復：使用3GPP標準閾值
        from shared.constants.physics_constants import SignalConstants
        signal_consts = SignalConstants()

        if rsrp >= signal_consts.RSRP_GOOD:
            pros.append("信號強度優秀")
        if handover_type == 'SEAMLESS':
            pros.append("支援無縫切換")
        if prediction.get('trend') == 'IMPROVING':
            pros.append("信號品質持續改善")
        if prediction.get('confidence', 0) > 0.8:
            pros.append("預測可信度高")
        
        return pros
    
    def _identify_cons(self, candidate: Dict[str, Any]) -> List[str]:
        """Identify cons of handover candidate."""
        cons = []
        
        signal_metrics = candidate.get('signal_metrics', {})
        rsrp = signal_metrics.get('rsrp_dbm', -100)
        handover_type = candidate.get('handover_type', 'UNKNOWN')
        prediction = candidate.get('prediction', {})
        
        if rsrp < -100:
            cons.append("信號強度較弱")
        if handover_type == 'BREAK_BEFORE_MAKE':
            cons.append("可能出現服務中斷")
        if prediction.get('trend') == 'DEGRADING':
            cons.append("信號品質趨於惡化")
        if prediction.get('handover_window_sec', 0) < 120:
            cons.append("切換時間窗口較短")
        
        return cons
    
    def _suggest_optimal_timing(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal timing for handover."""
        prediction = candidate.get('prediction', {})
        trend = prediction.get('trend', 'STABLE')
        
        if trend == 'IMPROVING':
            delay_sec = 60  # Wait for signal to improve
            reason = "等待信號進一步改善"
        elif trend == 'DEGRADING':
            delay_sec = 0   # Execute immediately
            reason = "信號衰減中，立即執行"
        else:
            delay_sec = 30  # Brief preparation time
            reason = "信號穩定，可適當準備"
        
        return {
            'recommended_delay_sec': delay_sec,
            'reason': reason,
            'optimal_time': (datetime.now(timezone.utc) + timedelta(seconds=delay_sec)).isoformat()
        }
    
    def _suggest_preparation_steps(self, candidate: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest preparation steps for handover."""
        handover_type = candidate.get('handover_type', 'UNKNOWN')
        
        steps = [
            {'step': '驗證目標衛星狀態', 'duration': '10s'},
            {'step': '預配置無線資源', 'duration': '20s'},
        ]
        
        if handover_type == 'SEAMLESS':
            steps.extend([
                {'step': '建立雙連接', 'duration': '30s'},
                {'step': '執行無縫切換', 'duration': '5s'}
            ])
        elif handover_type == 'MAKE_BEFORE_BREAK':
            steps.extend([
                {'step': '建立新連接', 'duration': '50s'},
                {'step': '數據路徑切換', 'duration': '10s'},
                {'step': '釋放舊連接', 'duration': '20s'}
            ])
        else:
            steps.extend([
                {'step': '釋放當前連接', 'duration': '20s'},
                {'step': '建立新連接', 'duration': '80s'}
            ])
        
        return steps
    
    def _generate_handover_strategy(self, recommendations: List[Dict[str, Any]], 
                                  best_candidate: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate overall handover strategy."""
        if not best_candidate:
            return {
                'strategy': 'MAINTAIN_CURRENT',
                'reason': '無合適切換候選',
                'next_action': '繼續監控信號品質'
            }
        
        highly_suitable = [r for r in recommendations if r['suitability']['level'] == 'HIGHLY_SUITABLE']
        
        if highly_suitable:
            return {
                'strategy': 'IMMEDIATE_HANDOVER',
                'target': best_candidate['satellite_id'],
                'reason': '發現高度合適的切換目標',
                'next_action': '立即準備切換程序'
            }
        else:
            return {
                'strategy': 'CONDITIONAL_HANDOVER',
                'target': best_candidate['satellite_id'],
                'reason': '候選可行但需謹慎評估',
                'next_action': '繼續監控並準備切換'
            }
    
    def _suggest_optimizations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest system optimizations."""
        optimizations = []
        
        # Analyze common issues
        weak_signals = sum(1 for r in recommendations if any('信號較弱' in rec for rec in r.get('recommendations', [])))
        short_windows = sum(1 for r in recommendations if any('窗口較短' in rec for rec in r.get('recommendations', [])))
        
        if weak_signals > len(recommendations) * 0.5:
            optimizations.append({
                'type': 'ANTENNA_OPTIMIZATION',
                'description': '考慮調整天線配置以改善信號接收',
                'expected_improvement': '提升RSRP 3-5 dB'
            })
        
        if short_windows > len(recommendations) * 0.3:
            optimizations.append({
                'type': 'PREDICTION_ENHANCEMENT',
                'description': '改善軌道預測算法以延長切換窗口',
                'expected_improvement': '延長切換窗口 30-60 秒'
            })
        
        return optimizations
    
    def _assess_handover_risks(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risks associated with handover decisions."""
        high_risk_count = sum(1 for r in recommendations if r['suitability']['level'] == 'NOT_SUITABLE')
        total_count = len(recommendations)
        
        risk_level = 'LOW'
        if high_risk_count / max(1, total_count) > 0.5:
            risk_level = 'HIGH'
        elif high_risk_count / max(1, total_count) > 0.2:
            risk_level = 'MEDIUM'
        
        return {
            'overall_risk': risk_level,
            'high_risk_candidates': high_risk_count,
            'risk_factors': self._identify_risk_factors(recommendations),
            'mitigation_strategies': self._suggest_risk_mitigation(risk_level)
        }
    
    def _identify_risk_factors(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Identify common risk factors."""
        factors = []
        
        weak_signals = any('信號較弱' in ' '.join(r.get('recommendations', [])) for r in recommendations)
        service_interruption = any('服務中斷' in ' '.join(r.get('cons', [])) for r in recommendations)
        
        if weak_signals:
            factors.append('整體信號強度偏低')
        if service_interruption:
            factors.append('可能出現服務中斷')
        
        return factors
    
    def _suggest_risk_mitigation(self, risk_level: str) -> List[str]:
        """Suggest risk mitigation strategies."""
        strategies = {
            'HIGH': [
                '延遲切換決策，等待更好機會',
                '考慮多衛星分集接收',
                '準備備用通信方案'
            ],
            'MEDIUM': [
                '增強信號監控頻率',
                '預先配置備用連接',
                '優化切換時序'
            ],
            'LOW': [
                '保持正常監控',
                '按計劃執行切換'
            ]
        }
        return strategies.get(risk_level, ['需要進一步評估'])
    
    def _calculate_confidence(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in recommendations."""
        if not recommendations:
            return 0.0
        
        confidences = [r['suitability']['confidence'] for r in recommendations]
        return round(sum(confidences) / len(confidences), 3)
    
    def _calculate_next_review(self) -> str:
        """Calculate next review time."""
        return (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    
    def _generate_no_candidate_recommendation(self) -> Dict[str, Any]:
        """Generate recommendation when no candidates available."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_candidates': 0,
            'handover_strategy': {
                'strategy': 'MAINTAIN_CURRENT',
                'reason': '無可用切換候選',
                'next_action': '繼續監控衛星狀態'
            },
            'optimization_suggestions': [
                {
                    'type': 'COVERAGE_ANALYSIS',
                    'description': '分析當前區域衛星覆蓋情況',
                    'expected_improvement': '識別潛在切換機會'
                }
            ],
            'next_review_time': self._calculate_next_review()
        }