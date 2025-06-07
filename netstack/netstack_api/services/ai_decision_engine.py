"""
進階 AI 智慧決策引擎

階段八：進階 AI 智慧決策與自動化調優
擴展現有的 AI-RAN 抗干擾功能，實現全域智慧決策和自動化系統調優
"""

import asyncio
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import structlog
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
from dataclasses import dataclass
from collections import deque, defaultdict
import pickle
import joblib

from ..adapters.redis_adapter import RedisAdapter
from .ai_ran_anti_interference_service import AIRANAntiInterferenceService

logger = structlog.get_logger(__name__)

@dataclass
class OptimizationObjective:
    """優化目標定義"""
    name: str
    weight: float
    target_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_maximize: bool = True

@dataclass
class SystemMetrics:
    """系統性能指標"""
    latency_ms: float
    throughput_mbps: float
    coverage_percentage: float
    power_consumption_w: float
    sinr_db: float
    packet_loss_rate: float
    handover_success_rate: float
    interference_level_db: float
    resource_utilization: float
    cost_efficiency: float
    timestamp: datetime

@dataclass
class DecisionContext:
    """決策上下文"""
    system_metrics: SystemMetrics
    network_state: Dict
    interference_data: Dict
    historical_performance: List[SystemMetrics]
    optimization_objectives: List[OptimizationObjective]
    constraints: Dict

class MultiObjectiveOptimizer:
    """多目標優化器"""
    
    def __init__(self, objectives: List[OptimizationObjective]):
        self.objectives = objectives
        self.pareto_solutions = []
        self.weights = torch.tensor([obj.weight for obj in objectives])
        
    def evaluate_solution(self, solution: Dict, metrics: SystemMetrics) -> float:
        """評估解決方案的總體適應度"""
        scores = []
        metric_values = {
            'latency': metrics.latency_ms,
            'throughput': metrics.throughput_mbps,
            'coverage': metrics.coverage_percentage,
            'power': metrics.power_consumption_w,
            'sinr': metrics.sinr_db,
            'packet_loss': metrics.packet_loss_rate,
            'handover_success': metrics.handover_success_rate,
            'interference': metrics.interference_level_db,
            'resource_utilization': metrics.resource_utilization,
            'cost_efficiency': metrics.cost_efficiency
        }
        
        for obj in self.objectives:
            metric_name = obj.name.lower().replace('_', '')
            if metric_name in metric_values:
                value = metric_values[metric_name]
                
                # 正規化分數
                if obj.min_value is not None and obj.max_value is not None:
                    normalized_value = (value - obj.min_value) / (obj.max_value - obj.min_value)
                else:
                    normalized_value = value / 100.0  # 假設百分比
                
                if not obj.is_maximize:
                    normalized_value = 1.0 - normalized_value
                    
                scores.append(normalized_value * obj.weight)
            else:
                scores.append(0.0)
        
        return sum(scores)
    
    def is_pareto_optimal(self, solution: Dict, metrics: SystemMetrics) -> bool:
        """檢查解決方案是否為帕累托最優"""
        current_scores = self._get_objective_scores(metrics)
        
        for existing_solution, existing_scores in self.pareto_solutions:
            if self._dominates(existing_scores, current_scores):
                return False
        
        # 移除被當前解決方案支配的解決方案
        self.pareto_solutions = [
            (sol, scores) for sol, scores in self.pareto_solutions
            if not self._dominates(current_scores, scores)
        ]
        
        return True
    
    def _get_objective_scores(self, metrics: SystemMetrics) -> List[float]:
        """獲取目標分數"""
        metric_values = {
            'latency': metrics.latency_ms,
            'throughput': metrics.throughput_mbps,
            'coverage': metrics.coverage_percentage,
            'power': metrics.power_consumption_w,
            'sinr': metrics.sinr_db
        }
        
        scores = []
        for obj in self.objectives:
            metric_name = obj.name.lower()
            if metric_name in metric_values:
                value = metric_values[metric_name]
                scores.append(value if obj.is_maximize else -value)
            else:
                scores.append(0.0)
        
        return scores
    
    def _dominates(self, scores1: List[float], scores2: List[float]) -> bool:
        """檢查scores1是否支配scores2"""
        better_in_at_least_one = False
        for s1, s2 in zip(scores1, scores2):
            if s1 < s2:
                return False
            elif s1 > s2:
                better_in_at_least_one = True
        return better_in_at_least_one

class AdaptiveLearningModule:
    """自適應學習模組"""
    
    def __init__(self, learning_rate: float = 0.001):
        self.learning_rate = learning_rate
        self.performance_history = deque(maxlen=1000)
        self.decision_feedback = deque(maxlen=500)
        self.adaptation_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def add_performance_sample(self, metrics: SystemMetrics, decision: Dict, outcome: Dict):
        """添加性能樣本"""
        sample = {
            'metrics': metrics,
            'decision': decision,
            'outcome': outcome,
            'timestamp': datetime.utcnow()
        }
        self.performance_history.append(sample)
        
        # 計算決策反饋
        improvement = self._calculate_improvement(metrics, outcome)
        self.decision_feedback.append({
            'decision': decision,
            'improvement': improvement,
            'timestamp': datetime.utcnow()
        })
        
    def _calculate_improvement(self, before_metrics: SystemMetrics, outcome: Dict) -> float:
        """計算改善程度"""
        # 這裡實現具體的改善計算邏輯
        baseline_score = (
            before_metrics.throughput_mbps / 100.0 +
            (100 - before_metrics.latency_ms) / 100.0 +
            before_metrics.coverage_percentage / 100.0
        ) / 3.0
        
        after_score = (
            outcome.get('throughput_improvement', 0) / 100.0 +
            outcome.get('latency_improvement', 0) / 100.0 +
            outcome.get('coverage_improvement', 0) / 100.0
        ) / 3.0
        
        return after_score - baseline_score
    
    def update_model(self):
        """更新自適應模型"""
        if len(self.performance_history) < 50:
            return
            
        # 準備訓練數據
        features, targets = self._prepare_training_data()
        
        if features.shape[0] < 10:
            return
            
        # 訓練模型
        self.adaptation_model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        
        X_scaled = self.scaler.fit_transform(features)
        self.adaptation_model.fit(X_scaled, targets)
        self.is_trained = True
        
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """準備訓練數據"""
        features = []
        targets = []
        
        for sample in list(self.performance_history)[-200:]:  # 使用最近200個樣本
            metrics = sample['metrics']
            decision = sample['decision']
            outcome = sample['outcome']
            
            # 特徵提取
            feature_vector = [
                metrics.latency_ms,
                metrics.throughput_mbps,
                metrics.coverage_percentage,
                metrics.power_consumption_w,
                metrics.sinr_db,
                metrics.packet_loss_rate,
                metrics.handover_success_rate,
                metrics.interference_level_db,
                metrics.resource_utilization,
                metrics.cost_efficiency,
                len(decision.get('actions', [])),
                decision.get('confidence', 0.5),
                decision.get('priority_level', 1)
            ]
            
            # 目標值（改善指標）
            target_vector = [
                outcome.get('latency_improvement', 0),
                outcome.get('throughput_improvement', 0),
                outcome.get('coverage_improvement', 0),
                outcome.get('power_improvement', 0)
            ]
            
            features.append(feature_vector)
            targets.append(target_vector)
        
        return np.array(features), np.array(targets)
    
    def predict_outcome(self, metrics: SystemMetrics, decision: Dict) -> Dict:
        """預測決策結果"""
        if not self.is_trained or self.adaptation_model is None:
            return {
                'predicted_improvement': 0.0,
                'confidence': 0.0,
                'recommendation': 'insufficient_data'
            }
        
        # 準備特徵
        feature_vector = np.array([[
            metrics.latency_ms,
            metrics.throughput_mbps,
            metrics.coverage_percentage,
            metrics.power_consumption_w,
            metrics.sinr_db,
            metrics.packet_loss_rate,
            metrics.handover_success_rate,
            metrics.interference_level_db,
            metrics.resource_utilization,
            metrics.cost_efficiency,
            len(decision.get('actions', [])),
            decision.get('confidence', 0.5),
            decision.get('priority_level', 1)
        ]])
        
        # 預測
        X_scaled = self.scaler.transform(feature_vector)
        prediction = self.adaptation_model.predict(X_scaled)[0]
        
        # 計算預測改善程度
        predicted_improvement = np.mean(prediction)
        
        # 計算信心度（基於歷史相似性）
        confidence = self._calculate_prediction_confidence(feature_vector[0])
        
        return {
            'predicted_improvement': predicted_improvement,
            'confidence': confidence,
            'detailed_predictions': {
                'latency_improvement': prediction[0],
                'throughput_improvement': prediction[1],
                'coverage_improvement': prediction[2],
                'power_improvement': prediction[3]
            }
        }
    
    def _calculate_prediction_confidence(self, features: np.ndarray) -> float:
        """計算預測信心度"""
        if len(self.performance_history) == 0:
            return 0.0
        
        # 找到最相似的歷史樣本
        similarities = []
        for sample in list(self.performance_history)[-100:]:
            metrics = sample['metrics']
            hist_features = np.array([
                metrics.latency_ms,
                metrics.throughput_mbps,
                metrics.coverage_percentage,
                metrics.power_consumption_w,
                metrics.sinr_db
            ])
            
            # 計算歐氏距離相似度
            distance = np.linalg.norm(features[:5] - hist_features)
            similarity = 1.0 / (1.0 + distance)
            similarities.append(similarity)
        
        return np.mean(similarities)

class PredictiveMaintenanceSystem:
    """預測性維護系統"""
    
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.failure_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.maintenance_history = deque(maxlen=1000)
        self.alert_thresholds = {
            'high_risk': 0.8,
            'medium_risk': 0.6,
            'low_risk': 0.4
        }
        self.is_trained = False
        
    def analyze_system_health(self, metrics: SystemMetrics, network_state: Dict) -> Dict:
        """分析系統健康狀況"""
        health_indicators = self._extract_health_indicators(metrics, network_state)
        
        if not self.is_trained:
            return {
                'health_score': 0.5,
                'risk_level': 'unknown',
                'anomalies': [],
                'recommendations': ['需要更多數據進行分析'],
                'predicted_issues': []
            }
        
        # 異常檢測
        health_array = np.array([list(health_indicators.values())]).reshape(1, -1)
        anomaly_score = self.anomaly_detector.decision_function(health_array)[0]
        is_anomaly = self.anomaly_detector.predict(health_array)[0] == -1
        
        # 故障風險預測
        risk_score = self._predict_failure_risk(health_indicators)
        
        # 生成建議
        recommendations = self._generate_maintenance_recommendations(
            health_indicators, risk_score, is_anomaly
        )
        
        return {
            'health_score': self._calculate_health_score(health_indicators),
            'risk_level': self._categorize_risk(risk_score),
            'anomaly_detected': is_anomaly,
            'anomaly_score': float(anomaly_score),
            'risk_score': risk_score,
            'health_indicators': health_indicators,
            'recommendations': recommendations,
            'predicted_issues': self._predict_potential_issues(health_indicators),
            'maintenance_window': self._suggest_maintenance_window(risk_score)
        }
    
    def _extract_health_indicators(self, metrics: SystemMetrics, network_state: Dict) -> Dict:
        """提取健康指標"""
        return {
            'cpu_utilization': network_state.get('cpu_utilization', 50),
            'memory_utilization': network_state.get('memory_utilization', 60),
            'disk_utilization': network_state.get('disk_utilization', 70),
            'network_utilization': metrics.resource_utilization,
            'error_rate': metrics.packet_loss_rate * 100,
            'response_time': metrics.latency_ms,
            'throughput_deviation': abs(metrics.throughput_mbps - 50) / 50,  # 假設目標50Mbps
            'temperature': network_state.get('temperature_celsius', 45),
            'power_consumption': metrics.power_consumption_w,
            'signal_quality': metrics.sinr_db
        }
    
    def _calculate_health_score(self, indicators: Dict) -> float:
        """計算健康分數"""
        weights = {
            'cpu_utilization': 0.15,
            'memory_utilization': 0.15,
            'disk_utilization': 0.1,
            'network_utilization': 0.2,
            'error_rate': 0.15,
            'response_time': 0.1,
            'throughput_deviation': 0.1,
            'signal_quality': 0.05
        }
        
        score = 0.0
        for indicator, value in indicators.items():
            if indicator in weights:
                # 正規化並反轉某些指標（使用率、錯誤率等越低越好）
                if indicator in ['cpu_utilization', 'memory_utilization', 'disk_utilization', 'error_rate', 'response_time', 'throughput_deviation']:
                    normalized = max(0, 1.0 - value / 100.0)
                else:
                    normalized = min(1.0, value / 100.0)
                score += normalized * weights[indicator]
        
        return min(1.0, score)
    
    def _predict_failure_risk(self, indicators: Dict) -> float:
        """預測故障風險"""
        if not hasattr(self, 'failure_predictor') or not self.is_trained:
            return 0.5
        
        feature_vector = np.array([list(indicators.values())]).reshape(1, -1)
        risk_score = self.failure_predictor.predict(feature_vector)[0]
        return np.clip(risk_score, 0.0, 1.0)
    
    def _categorize_risk(self, risk_score: float) -> str:
        """分類風險等級"""
        if risk_score >= self.alert_thresholds['high_risk']:
            return 'high'
        elif risk_score >= self.alert_thresholds['medium_risk']:
            return 'medium'
        elif risk_score >= self.alert_thresholds['low_risk']:
            return 'low'
        else:
            return 'minimal'
    
    def _generate_maintenance_recommendations(self, indicators: Dict, risk_score: float, is_anomaly: bool) -> List[str]:
        """生成維護建議"""
        recommendations = []
        
        if is_anomaly:
            recommendations.append("檢測到系統異常，建議立即檢查")
        
        if risk_score > 0.7:
            recommendations.append("故障風險較高，建議安排緊急維護")
        elif risk_score > 0.5:
            recommendations.append("建議在下次維護窗口進行檢查")
        
        # 針對具體指標的建議
        if indicators.get('cpu_utilization', 0) > 80:
            recommendations.append("CPU使用率過高，考慮負載均衡或擴容")
        
        if indicators.get('memory_utilization', 0) > 85:
            recommendations.append("記憶體使用率過高，檢查記憶體洩漏")
        
        if indicators.get('error_rate', 0) > 5:
            recommendations.append("錯誤率偏高，檢查網路配置和硬體狀態")
        
        if indicators.get('temperature', 0) > 70:
            recommendations.append("設備溫度過高，檢查散熱系統")
        
        return recommendations if recommendations else ["系統狀態正常"]
    
    def _predict_potential_issues(self, indicators: Dict) -> List[Dict]:
        """預測潛在問題"""
        issues = []
        
        # 趨勢分析（需要歷史數據）
        if len(self.maintenance_history) > 10:
            recent_data = list(self.maintenance_history)[-10:]
            # 這裡可以實現趨勢分析邏輯
            pass
        
        # 基於當前指標的問題預測
        if indicators.get('cpu_utilization', 0) > 70:
            issues.append({
                'type': 'performance_degradation',
                'probability': 0.7,
                'description': 'CPU使用率持續升高可能導致性能下降',
                'recommended_action': '監控負載情況，考慮擴容'
            })
        
        if indicators.get('error_rate', 0) > 3:
            issues.append({
                'type': 'connectivity_issues',
                'probability': 0.6,
                'description': '錯誤率升高可能導致連接問題',
                'recommended_action': '檢查網路配置和信號品質'
            })
        
        return issues
    
    def _suggest_maintenance_window(self, risk_score: float) -> str:
        """建議維護窗口"""
        if risk_score > 0.8:
            return "立即"
        elif risk_score > 0.6:
            return "24小時內"
        elif risk_score > 0.4:
            return "一週內"
        else:
            return "下次定期維護"
    
    def update_maintenance_history(self, health_data: Dict):
        """更新維護歷史"""
        self.maintenance_history.append({
            'timestamp': datetime.utcnow(),
            'health_data': health_data
        })
        
        # 定期重新訓練模型
        if len(self.maintenance_history) % 100 == 0:
            self._retrain_models()
    
    def _retrain_models(self):
        """重新訓練模型"""
        if len(self.maintenance_history) < 50:
            return
        
        # 準備訓練數據
        features = []
        targets = []
        
        for i, record in enumerate(list(self.maintenance_history)[:-10]):
            health_data = record['health_data']
            features.append(list(health_data['health_indicators'].values()))
            
            # 目標：未來是否發生故障（簡化為高風險）
            future_records = list(self.maintenance_history)[i+1:i+11]
            max_future_risk = max([r['health_data'].get('risk_score', 0) for r in future_records])
            targets.append(max_future_risk)
        
        if len(features) > 10:
            X = np.array(features)
            y = np.array(targets)
            
            # 訓練異常檢測器
            self.anomaly_detector.fit(X)
            
            # 訓練故障預測器
            self.failure_predictor.fit(X, y)
            
            self.is_trained = True

class AIDecisionEngine:
    """進階 AI 智慧決策引擎"""
    
    def __init__(
        self,
        redis_adapter: RedisAdapter,
        ai_ran_service: AIRANAntiInterferenceService,
        model_save_path: str = "/tmp/ai_decision_models"
    ):
        self.logger = logger.bind(service="ai_decision_engine")
        self.redis_adapter = redis_adapter
        self.ai_ran_service = ai_ran_service
        self.model_save_path = Path(model_save_path)
        self.model_save_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化子系統
        self.multi_objective_optimizer = None  # 將在設置目標時初始化
        self.adaptive_learning = AdaptiveLearningModule()
        self.predictive_maintenance = PredictiveMaintenanceSystem()
        
        # 決策歷史和統計
        self.decision_history = deque(maxlen=1000)
        self.performance_metrics = deque(maxlen=500)
        
        # 智能推薦系統
        self.recommendation_engine = None
        
        # 自動調優參數
        self.auto_tuning_enabled = True
        self.tuning_interval_seconds = 300  # 5分鐘
        self.last_tuning_time = datetime.utcnow()
        
        # 載入已保存的模型
        self._load_models()
    
    async def comprehensive_decision_making(
        self,
        context: DecisionContext,
        urgent_mode: bool = False
    ) -> Dict:
        """綜合智慧決策"""
        try:
            decision_start_time = datetime.utcnow()
            
            # 1. 系統健康分析
            health_analysis = self.predictive_maintenance.analyze_system_health(
                context.system_metrics, context.network_state
            )
            
            # 2. 多目標優化分析
            if self.multi_objective_optimizer is None:
                self.multi_objective_optimizer = MultiObjectiveOptimizer(context.optimization_objectives)
            
            # 3. AI-RAN 抗干擾決策
            ai_ran_decision = await self.ai_ran_service.ai_mitigation_decision(
                context.interference_data,
                context.network_state,
                fast_mode=urgent_mode
            )
            
            # 4. 自適應學習預測
            learning_prediction = self.adaptive_learning.predict_outcome(
                context.system_metrics,
                {'ai_ran_decision': ai_ran_decision}
            )
            
            # 5. 綜合決策生成
            comprehensive_decision = self._generate_comprehensive_decision(
                context, health_analysis, ai_ran_decision, learning_prediction, urgent_mode
            )
            
            # 6. 決策評估和調優
            if not urgent_mode:
                comprehensive_decision = await self._optimize_decision(
                    comprehensive_decision, context
                )
            
            decision_time = (datetime.utcnow() - decision_start_time).total_seconds()
            
            # 7. 記錄決策
            decision_record = {
                'decision_id': f"decision_{datetime.utcnow().timestamp()}",
                'timestamp': decision_start_time.isoformat(),
                'context': self._serialize_context(context),
                'health_analysis': health_analysis,
                'ai_ran_decision': ai_ran_decision,
                'learning_prediction': learning_prediction,
                'comprehensive_decision': comprehensive_decision,
                'decision_time_seconds': decision_time,
                'urgent_mode': urgent_mode
            }
            
            self.decision_history.append(decision_record)
            
            # 8. 異步更新學習模型
            if not urgent_mode:
                asyncio.create_task(self._update_learning_models(decision_record))
            
            return {
                'success': True,
                'decision_id': decision_record['decision_id'],
                'comprehensive_decision': comprehensive_decision,
                'health_analysis': health_analysis,
                'ai_ran_decision': ai_ran_decision,
                'learning_prediction': learning_prediction,
                'decision_time_seconds': decision_time,
                'confidence_score': comprehensive_decision.get('confidence', 0.5),
                'recommendations': self._generate_action_recommendations(comprehensive_decision),
                'timestamp': decision_start_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error("綜合智慧決策失敗", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _generate_comprehensive_decision(
        self,
        context: DecisionContext,
        health_analysis: Dict,
        ai_ran_decision: Dict,
        learning_prediction: Dict,
        urgent_mode: bool
    ) -> Dict:
        """生成綜合決策"""
        decision = {
            'actions': [],
            'priority_level': 1,
            'confidence': 0.5,
            'expected_improvements': {},
            'implementation_order': [],
            'resource_requirements': {},
            'estimated_execution_time': 0
        }
        
        # 基於健康分析的決策
        if health_analysis['risk_level'] in ['high', 'medium']:
            decision['actions'].extend([
                {
                    'type': 'maintenance',
                    'action': 'schedule_maintenance',
                    'urgency': health_analysis['risk_level'],
                    'recommendations': health_analysis['recommendations']
                }
            ])
            decision['priority_level'] = max(decision['priority_level'], 3 if health_analysis['risk_level'] == 'high' else 2)
        
        # 基於 AI-RAN 決策的行動
        if ai_ran_decision.get('success', False):
            mitigation_action = {
                'type': 'interference_mitigation',
                'strategy': ai_ran_decision['selected_strategy'],
                'confidence': ai_ran_decision['action_confidence'],
                'parameters': ai_ran_decision['mitigation_result']
            }
            decision['actions'].append(mitigation_action)
            decision['confidence'] = max(decision['confidence'], ai_ran_decision['action_confidence'])
        
        # 基於學習預測的優化
        if learning_prediction['confidence'] > 0.6:
            predicted_improvement = learning_prediction['predicted_improvement']
            if predicted_improvement > 0.1:  # 顯著改善
                optimization_action = {
                    'type': 'performance_optimization',
                    'predicted_improvement': predicted_improvement,
                    'confidence': learning_prediction['confidence'],
                    'details': learning_prediction['detailed_predictions']
                }
                decision['actions'].append(optimization_action)
        
        # 多目標優化調整
        if self.multi_objective_optimizer and not urgent_mode:
            optimization_adjustments = self._apply_multi_objective_optimization(
                decision, context.system_metrics, context.optimization_objectives
            )
            decision['actions'].extend(optimization_adjustments)
        
        # 計算總體信心度
        if decision['actions']:
            action_confidences = [
                action.get('confidence', 0.5) for action in decision['actions']
                if 'confidence' in action
            ]
            if action_confidences:
                decision['confidence'] = np.mean(action_confidences)
        
        # 設置實施順序
        decision['implementation_order'] = self._determine_implementation_order(decision['actions'])
        
        # 估算執行時間
        decision['estimated_execution_time'] = self._estimate_execution_time(decision['actions'])
        
        return decision
    
    def _apply_multi_objective_optimization(
        self,
        decision: Dict,
        metrics: SystemMetrics,
        objectives: List[OptimizationObjective]
    ) -> List[Dict]:
        """應用多目標優化"""
        optimization_actions = []
        
        # 評估當前解決方案
        current_score = self.multi_objective_optimizer.evaluate_solution(decision, metrics)
        
        # 生成優化建議
        for objective in objectives:
            if objective.name.lower() == 'latency' and metrics.latency_ms > 50:
                optimization_actions.append({
                    'type': 'latency_optimization',
                    'target_latency_ms': objective.target_value or 30,
                    'current_latency_ms': metrics.latency_ms,
                    'confidence': 0.7
                })
            
            elif objective.name.lower() == 'throughput' and metrics.throughput_mbps < (objective.target_value or 50):
                optimization_actions.append({
                    'type': 'throughput_optimization',
                    'target_throughput_mbps': objective.target_value or 50,
                    'current_throughput_mbps': metrics.throughput_mbps,
                    'confidence': 0.6
                })
            
            elif objective.name.lower() == 'power' and metrics.power_consumption_w > (objective.target_value or 100):
                optimization_actions.append({
                    'type': 'power_optimization',
                    'target_power_w': objective.target_value or 100,
                    'current_power_w': metrics.power_consumption_w,
                    'confidence': 0.8
                })
        
        return optimization_actions
    
    def _determine_implementation_order(self, actions: List[Dict]) -> List[int]:
        """確定實施順序"""
        # 按優先級和依賴關係排序
        action_priorities = []
        for i, action in enumerate(actions):
            priority = 1
            
            if action['type'] == 'maintenance' and action.get('urgency') == 'high':
                priority = 10
            elif action['type'] == 'interference_mitigation':
                priority = 8
            elif action['type'] == 'performance_optimization':
                priority = 5
            elif action['type'] == 'latency_optimization':
                priority = 7
            elif action['type'] == 'throughput_optimization':
                priority = 6
            elif action['type'] == 'power_optimization':
                priority = 4
            
            action_priorities.append((i, priority))
        
        # 按優先級排序
        action_priorities.sort(key=lambda x: x[1], reverse=True)
        
        return [i for i, _ in action_priorities]
    
    def _estimate_execution_time(self, actions: List[Dict]) -> float:
        """估算執行時間（秒）"""
        total_time = 0
        
        time_estimates = {
            'maintenance': 300,  # 5分鐘
            'interference_mitigation': 60,  # 1分鐘
            'performance_optimization': 180,  # 3分鐘
            'latency_optimization': 120,  # 2分鐘
            'throughput_optimization': 150,  # 2.5分鐘
            'power_optimization': 90  # 1.5分鐘
        }
        
        for action in actions:
            action_type = action['type']
            total_time += time_estimates.get(action_type, 60)
        
        return total_time
    
    async def _optimize_decision(self, decision: Dict, context: DecisionContext) -> Dict:
        """優化決策"""
        # 這裡可以實現更複雜的決策優化邏輯
        # 例如：成本效益分析、資源約束檢查等
        
        # 檢查資源約束
        if context.constraints:
            decision = self._apply_constraints(decision, context.constraints)
        
        # 成本效益分析
        decision['cost_benefit_analysis'] = self._calculate_cost_benefit(decision, context.system_metrics)
        
        return decision
    
    def _apply_constraints(self, decision: Dict, constraints: Dict) -> Dict:
        """應用約束條件"""
        # 移除違反約束的行動
        filtered_actions = []
        
        for action in decision['actions']:
            if self._check_action_constraints(action, constraints):
                filtered_actions.append(action)
            else:
                self.logger.warning("行動因約束被過濾", action=action['type'])
        
        decision['actions'] = filtered_actions
        return decision
    
    def _check_action_constraints(self, action: Dict, constraints: Dict) -> bool:
        """檢查行動約束"""
        # 實現具體的約束檢查邏輯
        max_power = constraints.get('max_power_w', 1000)
        max_cost = constraints.get('max_cost', 10000)
        
        # 示例約束檢查
        if action['type'] == 'power_optimization':
            target_power = action.get('target_power_w', 0)
            if target_power > max_power:
                return False
        
        return True
    
    def _calculate_cost_benefit(self, decision: Dict, metrics: SystemMetrics) -> Dict:
        """計算成本效益"""
        total_cost = 0
        total_benefit = 0
        
        cost_estimates = {
            'maintenance': 500,
            'interference_mitigation': 100,
            'performance_optimization': 200,
            'latency_optimization': 150,
            'throughput_optimization': 180,
            'power_optimization': 80
        }
        
        for action in decision['actions']:
            action_type = action['type']
            cost = cost_estimates.get(action_type, 100)
            total_cost += cost
            
            # 估算效益（基於改善程度）
            confidence = action.get('confidence', 0.5)
            benefit = cost * confidence * 1.5  # 假設成功時效益為成本的1.5倍
            total_benefit += benefit
        
        return {
            'total_cost': total_cost,
            'total_benefit': total_benefit,
            'roi': (total_benefit - total_cost) / total_cost if total_cost > 0 else 0,
            'payback_period_hours': total_cost / (total_benefit / 24) if total_benefit > 0 else float('inf')
        }
    
    def _generate_action_recommendations(self, decision: Dict) -> List[str]:
        """生成行動建議"""
        recommendations = []
        
        if not decision['actions']:
            recommendations.append("系統狀態良好，無需立即行動")
            return recommendations
        
        implementation_order = decision.get('implementation_order', [])
        actions = decision['actions']
        
        for i in implementation_order:
            if i < len(actions):
                action = actions[i]
                action_type = action['type']
                confidence = action.get('confidence', 0.5)
                
                if action_type == 'maintenance':
                    urgency = action.get('urgency', 'low')
                    recommendations.append(f"建議進行{urgency}級別維護檢查")
                
                elif action_type == 'interference_mitigation':
                    strategy = action.get('strategy', '未知策略')
                    recommendations.append(f"執行{strategy}抗干擾策略（信心度: {confidence:.2f}）")
                
                elif action_type == 'performance_optimization':
                    improvement = action.get('predicted_improvement', 0)
                    recommendations.append(f"執行性能優化，預期改善{improvement:.1%}")
                
                elif action_type.endswith('_optimization'):
                    opt_type = action_type.replace('_optimization', '')
                    recommendations.append(f"優化{opt_type}參數以提升系統性能")
        
        # 添加執行時間建議
        exec_time = decision.get('estimated_execution_time', 0)
        if exec_time > 0:
            recommendations.append(f"預計執行時間: {exec_time/60:.1f}分鐘")
        
        return recommendations
    
    async def _update_learning_models(self, decision_record: Dict):
        """更新學習模型"""
        try:
            # 更新自適應學習模型
            self.adaptive_learning.update_model()
            
            # 更新預測性維護模型
            if 'health_analysis' in decision_record:
                self.predictive_maintenance.update_maintenance_history(decision_record['health_analysis'])
            
            # 保存模型
            await self._save_models()
            
        except Exception as e:
            self.logger.error("更新學習模型失敗", error=str(e))
    
    def _serialize_context(self, context: DecisionContext) -> Dict:
        """序列化決策上下文"""
        return {
            'system_metrics': {
                'latency_ms': context.system_metrics.latency_ms,
                'throughput_mbps': context.system_metrics.throughput_mbps,
                'coverage_percentage': context.system_metrics.coverage_percentage,
                'power_consumption_w': context.system_metrics.power_consumption_w,
                'sinr_db': context.system_metrics.sinr_db,
                'packet_loss_rate': context.system_metrics.packet_loss_rate,
                'handover_success_rate': context.system_metrics.handover_success_rate,
                'interference_level_db': context.system_metrics.interference_level_db,
                'resource_utilization': context.system_metrics.resource_utilization,
                'cost_efficiency': context.system_metrics.cost_efficiency,
                'timestamp': context.system_metrics.timestamp.isoformat()
            },
            'network_state': context.network_state,
            'interference_data': context.interference_data,
            'optimization_objectives': [
                {
                    'name': obj.name,
                    'weight': obj.weight,
                    'target_value': obj.target_value,
                    'is_maximize': obj.is_maximize
                }
                for obj in context.optimization_objectives
            ],
            'constraints': context.constraints
        }
    
    async def _save_models(self):
        """保存模型"""
        try:
            # 保存自適應學習模型
            if self.adaptive_learning.is_trained and self.adaptive_learning.adaptation_model:
                model_path = self.model_save_path / "adaptive_learning_model.joblib"
                scaler_path = self.model_save_path / "adaptive_learning_scaler.joblib"
                
                joblib.dump(self.adaptive_learning.adaptation_model, model_path)
                joblib.dump(self.adaptive_learning.scaler, scaler_path)
            
            # 保存預測性維護模型
            if self.predictive_maintenance.is_trained:
                anomaly_path = self.model_save_path / "anomaly_detector.joblib"
                failure_path = self.model_save_path / "failure_predictor.joblib"
                
                joblib.dump(self.predictive_maintenance.anomaly_detector, anomaly_path)
                joblib.dump(self.predictive_maintenance.failure_predictor, failure_path)
            
            self.logger.info("AI決策引擎模型已保存")
            
        except Exception as e:
            self.logger.error("保存模型失敗", error=str(e))
    
    def _load_models(self):
        """載入已保存的模型"""
        try:
            # 載入自適應學習模型
            model_path = self.model_save_path / "adaptive_learning_model.joblib"
            scaler_path = self.model_save_path / "adaptive_learning_scaler.joblib"
            
            if model_path.exists() and scaler_path.exists():
                self.adaptive_learning.adaptation_model = joblib.load(model_path)
                self.adaptive_learning.scaler = joblib.load(scaler_path)
                self.adaptive_learning.is_trained = True
                self.logger.info("自適應學習模型已載入")
            
            # 載入預測性維護模型
            anomaly_path = self.model_save_path / "anomaly_detector.joblib"
            failure_path = self.model_save_path / "failure_predictor.joblib"
            
            if anomaly_path.exists() and failure_path.exists():
                self.predictive_maintenance.anomaly_detector = joblib.load(anomaly_path)
                self.predictive_maintenance.failure_predictor = joblib.load(failure_path)
                self.predictive_maintenance.is_trained = True
                self.logger.info("預測性維護模型已載入")
        
        except Exception as e:
            self.logger.warning("載入模型失敗", error=str(e))
    
    async def get_service_status(self) -> Dict:
        """獲取服務狀態"""
        return {
            'service_name': '進階 AI 智慧決策引擎',
            'adaptive_learning_trained': self.adaptive_learning.is_trained,
            'predictive_maintenance_trained': self.predictive_maintenance.is_trained,
            'decision_history_count': len(self.decision_history),
            'performance_metrics_count': len(self.performance_metrics),
            'auto_tuning_enabled': self.auto_tuning_enabled,
            'last_tuning_time': self.last_tuning_time.isoformat(),
            'model_save_path': str(self.model_save_path),
            'multi_objective_optimizer_initialized': self.multi_objective_optimizer is not None
        }
    
    async def enable_auto_tuning(self, interval_seconds: int = 300):
        """啟用自動調優"""
        self.auto_tuning_enabled = True
        self.tuning_interval_seconds = interval_seconds
        self.logger.info("自動調優已啟用", interval_seconds=interval_seconds)
    
    async def disable_auto_tuning(self):
        """停用自動調優"""
        self.auto_tuning_enabled = False
        self.logger.info("自動調優已停用")
    
    async def manual_optimization(self, context: DecisionContext) -> Dict:
        """手動優化"""
        return await self.comprehensive_decision_making(context, urgent_mode=False)