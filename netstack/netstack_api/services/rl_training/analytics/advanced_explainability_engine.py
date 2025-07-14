"""
Advanced Explainability Engine for RL Decision Analysis

提供先進的 Algorithm Explainability 功能，包括：
- 深度決策路径分析
- 特徵重要性分析 
- 反事實分析 (Counterfactual Analysis)
- 決策置信度分解
- 算法行為模式識別

此模組基於 Phase 2.3 的決策分析引擎，提供學術級的解釋能力。
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

# 嘗試導入額外的分析庫，如不可用則優雅降級
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, using simplified feature importance analysis")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available, using alternative explainability methods")

logger = logging.getLogger(__name__)

class ExplainabilityLevel(Enum):
    """解釋深度級別"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    RESEARCH_GRADE = "research_grade"

class AnalysisType(Enum):
    """分析類型"""
    DECISION_PATH = "decision_path"
    FEATURE_IMPORTANCE = "feature_importance"
    COUNTERFACTUAL = "counterfactual"
    SENSITIVITY = "sensitivity"
    PATTERN_RECOGNITION = "pattern_recognition"

@dataclass
class FeatureImportanceResult:
    """特徵重要性分析結果"""
    feature_name: str
    importance_score: float
    confidence_interval: Tuple[float, float]
    method: str
    interpretation: str

@dataclass
class DecisionPathNode:
    """決策路徑節點"""
    step: int
    state: Dict[str, Any]
    available_actions: List[Any]
    chosen_action: Any
    q_values: Dict[str, float]
    confidence: float
    reasoning: str

@dataclass
class DecisionPathAnalysis:
    """決策路徑分析結果"""
    episode_id: str
    algorithm_name: str
    path_nodes: List[DecisionPathNode]
    critical_decisions: List[int]  # 關鍵決策步驟索引
    alternative_paths: List[List[DecisionPathNode]]
    path_quality_score: float
    improvement_suggestions: List[str]

@dataclass
class CounterfactualAnalysis:
    """反事實分析結果"""
    original_decision: Any
    alternative_decisions: List[Any]
    outcome_differences: Dict[str, float]
    likelihood_scores: Dict[str, float]
    what_if_scenarios: List[Dict[str, Any]]

@dataclass
class ExplainabilityReport:
    """完整的可解釋性報告"""
    report_id: str
    timestamp: datetime
    episode_id: str
    algorithm_name: str
    explainability_level: ExplainabilityLevel
    
    # 核心分析結果
    decision_path: DecisionPathAnalysis
    feature_importance: List[FeatureImportanceResult]
    counterfactual: Optional[CounterfactualAnalysis]
    
    # 統計摘要
    overall_confidence: float
    prediction_accuracy: float
    decision_consistency: float
    
    # 視覺化數據
    visualization_data: Dict[str, Any]
    
    # 改進建議
    improvement_recommendations: List[str]
    research_insights: List[str]

class AdvancedExplainabilityEngine:
    """
    先進的可解釋性分析引擎
    
    提供深度的 Algorithm Explainability 功能，包括決策路徑追蹤、
    特徵重要性分析、反事實分析等高級功能。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化高級可解釋性引擎
        
        Args:
            config: 配置參數，包括分析深度、方法選擇等
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 設置分析參數
        self.default_explainability_level = ExplainabilityLevel(
            self.config.get('default_level', 'intermediate')
        )
        self.max_path_length = self.config.get('max_path_length', 100)
        self.feature_importance_threshold = self.config.get('importance_threshold', 0.01)
        
        # 初始化分析組件
        self._init_feature_analyzer()
        self._init_pattern_recognizer()
        
        self.logger.info("Advanced Explainability Engine initialized")
    
    def _init_feature_analyzer(self):
        """初始化特徵分析器"""
        self.feature_analyzer = None
        if SKLEARN_AVAILABLE:
            # 使用隨機森林進行特徵重要性分析
            self.feature_analyzer = RandomForestRegressor(
                n_estimators=100,
                random_state=42
            )
            self.logger.info("sklearn-based feature analyzer initialized")
        else:
            self.logger.warning("Using simplified feature analyzer")
    
    def _init_pattern_recognizer(self):
        """初始化模式識別器"""
        self.pattern_cache = {}
        self.behavioral_patterns = []
        self.logger.info("Pattern recognizer initialized")
    
    async def analyze_decision_explainability(
        self,
        episode_data: Dict[str, Any],
        explainability_level: Optional[ExplainabilityLevel] = None
    ) -> ExplainabilityReport:
        """
        執行完整的決策可解釋性分析
        
        Args:
            episode_data: Episode 數據，包含狀態、動作、獎勵序列
            explainability_level: 分析深度級別
            
        Returns:
            完整的可解釋性報告
        """
        level = explainability_level or self.default_explainability_level
        episode_id = episode_data.get('episode_id', f"ep_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        self.logger.info(f"Starting explainability analysis for episode {episode_id} with level {level.value}")
        
        try:
            # 1. 分析決策路徑
            decision_path = await self._analyze_decision_path(episode_data)
            
            # 2. 特徵重要性分析
            feature_importance = await self._analyze_feature_importance(episode_data, level)
            
            # 3. 反事實分析（進階級別）
            counterfactual = None
            if level in [ExplainabilityLevel.ADVANCED, ExplainabilityLevel.RESEARCH_GRADE]:
                counterfactual = await self._analyze_counterfactual(episode_data)
            
            # 4. 計算統計摘要
            stats = await self._calculate_explainability_stats(episode_data, decision_path)
            
            # 5. 生成視覺化數據
            viz_data = await self._generate_visualization_data(
                decision_path, feature_importance, counterfactual
            )
            
            # 6. 產生改進建議
            recommendations = await self._generate_improvement_recommendations(
                decision_path, feature_importance, stats
            )
            
            # 7. 研究洞察（研究級別）
            research_insights = []
            if level == ExplainabilityLevel.RESEARCH_GRADE:
                research_insights = await self._generate_research_insights(
                    episode_data, decision_path, feature_importance
                )
            
            # 生成完整報告
            report = ExplainabilityReport(
                report_id=f"exp_{episode_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                episode_id=episode_id,
                algorithm_name=episode_data.get('algorithm_name', 'Unknown'),
                explainability_level=level,
                decision_path=decision_path,
                feature_importance=feature_importance,
                counterfactual=counterfactual,
                overall_confidence=stats['overall_confidence'],
                prediction_accuracy=stats['prediction_accuracy'],
                decision_consistency=stats['decision_consistency'],
                visualization_data=viz_data,
                improvement_recommendations=recommendations,
                research_insights=research_insights
            )
            
            self.logger.info(f"Explainability analysis completed for episode {episode_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error in explainability analysis: {e}")
            # 返回基本報告
            return await self._create_fallback_report(episode_data, e)
    
    async def _analyze_decision_path(self, episode_data: Dict[str, Any]) -> DecisionPathAnalysis:
        """分析決策路徑"""
        states = episode_data.get('states', [])
        actions = episode_data.get('actions', [])
        q_values_list = episode_data.get('q_values', [])
        confidences = episode_data.get('confidences', [])
        
        path_nodes = []
        critical_decisions = []
        
        for i, (state, action) in enumerate(zip(states, actions)):
            # 獲取 Q 值和置信度
            q_values = q_values_list[i] if i < len(q_values_list) else {}
            confidence = confidences[i] if i < len(confidences) else 0.5
            
            # 分析可用動作
            available_actions = list(q_values.keys()) if q_values else [action]
            
            # 生成推理解釋
            reasoning = self._generate_step_reasoning(state, action, q_values, confidence)
            
            # 檢查是否為關鍵決策
            if self._is_critical_decision(q_values, confidence):
                critical_decisions.append(i)
            
            node = DecisionPathNode(
                step=i,
                state=state,
                available_actions=available_actions,
                chosen_action=action,
                q_values=q_values,
                confidence=confidence,
                reasoning=reasoning
            )
            path_nodes.append(node)
        
        # 生成替代路徑（簡化版）
        alternative_paths = await self._generate_alternative_paths(path_nodes, critical_decisions)
        
        # 計算路徑品質分數
        path_quality = self._calculate_path_quality(path_nodes, episode_data.get('total_reward', 0))
        
        # 生成改進建議
        suggestions = self._generate_path_improvements(path_nodes, critical_decisions)
        
        return DecisionPathAnalysis(
            episode_id=episode_data.get('episode_id', 'unknown'),
            algorithm_name=episode_data.get('algorithm_name', 'Unknown'),
            path_nodes=path_nodes,
            critical_decisions=critical_decisions,
            alternative_paths=alternative_paths,
            path_quality_score=path_quality,
            improvement_suggestions=suggestions
        )
    
    async def _analyze_feature_importance(
        self, 
        episode_data: Dict[str, Any], 
        level: ExplainabilityLevel
    ) -> List[FeatureImportanceResult]:
        """分析特徵重要性"""
        states = episode_data.get('states', [])
        actions = episode_data.get('actions', [])
        rewards = episode_data.get('rewards', [])
        
        if not states or not actions:
            return []
        
        try:
            if SKLEARN_AVAILABLE and level in [ExplainabilityLevel.ADVANCED, ExplainabilityLevel.RESEARCH_GRADE]:
                return await self._sklearn_feature_importance(states, actions, rewards)
            else:
                return await self._simple_feature_importance(states, actions, rewards)
        except Exception as e:
            self.logger.warning(f"Feature importance analysis failed: {e}")
            return []
    
    async def _sklearn_feature_importance(
        self, 
        states: List[Dict], 
        actions: List[Any], 
        rewards: List[float]
    ) -> List[FeatureImportanceResult]:
        """使用 sklearn 進行特徵重要性分析"""
        # 準備數據
        feature_data = []
        target_data = []
        feature_names = []
        
        # 提取特徵
        for i, state in enumerate(states):
            if isinstance(state, dict):
                features = []
                if not feature_names:  # 第一次建立特徵名稱
                    feature_names = list(state.keys())
                
                for key in feature_names:
                    value = state.get(key, 0)
                    if isinstance(value, (int, float)):
                        features.append(value)
                    else:
                        features.append(0)  # 非數值特徵設為 0
                
                feature_data.append(features)
                target_data.append(rewards[i] if i < len(rewards) else 0)
        
        if not feature_data:
            return []
        
        # 訓練模型並計算重要性
        X = np.array(feature_data)
        y = np.array(target_data)
        
        self.feature_analyzer.fit(X, y)
        importances = self.feature_analyzer.feature_importances_
        
        # 計算置信區間（簡化版）
        results = []
        for i, (name, importance) in enumerate(zip(feature_names, importances)):
            if importance > self.feature_importance_threshold:
                # 簡化的置信區間計算
                ci_lower = max(0, importance - 0.1)
                ci_upper = min(1, importance + 0.1)
                
                interpretation = self._interpret_feature_importance(name, importance)
                
                results.append(FeatureImportanceResult(
                    feature_name=name,
                    importance_score=importance,
                    confidence_interval=(ci_lower, ci_upper),
                    method="RandomForest",
                    interpretation=interpretation
                ))
        
        # 按重要性排序
        results.sort(key=lambda x: x.importance_score, reverse=True)
        return results
    
    async def _simple_feature_importance(
        self, 
        states: List[Dict], 
        actions: List[Any], 
        rewards: List[float]
    ) -> List[FeatureImportanceResult]:
        """簡化的特徵重要性分析"""
        if not states:
            return []
        
        # 計算特徵與獎勵的相關性
        feature_correlations = {}
        
        # 獲取所有特徵名稱
        all_features = set()
        for state in states:
            if isinstance(state, dict):
                all_features.update(state.keys())
        
        for feature_name in all_features:
            feature_values = []
            reward_values = []
            
            for i, state in enumerate(states):
                if isinstance(state, dict) and feature_name in state:
                    value = state[feature_name]
                    if isinstance(value, (int, float)):
                        feature_values.append(value)
                        reward_values.append(rewards[i] if i < len(rewards) else 0)
            
            if len(feature_values) > 1:
                # 計算相關係數
                correlation = np.corrcoef(feature_values, reward_values)[0, 1]
                if not np.isnan(correlation):
                    feature_correlations[feature_name] = abs(correlation)
        
        # 轉換為結果格式
        results = []
        for name, correlation in feature_correlations.items():
            if correlation > self.feature_importance_threshold:
                interpretation = self._interpret_feature_importance(name, correlation)
                
                results.append(FeatureImportanceResult(
                    feature_name=name,
                    importance_score=correlation,
                    confidence_interval=(max(0, correlation - 0.2), min(1, correlation + 0.2)),
                    method="Correlation",
                    interpretation=interpretation
                ))
        
        # 按重要性排序
        results.sort(key=lambda x: x.importance_score, reverse=True)
        return results[:10]  # 返回前 10 個最重要的特徵
    
    async def _analyze_counterfactual(self, episode_data: Dict[str, Any]) -> Optional[CounterfactualAnalysis]:
        """反事實分析"""
        try:
            critical_decisions = episode_data.get('critical_decisions', [])
            if not critical_decisions:
                return None
            
            # 選擇最關鍵的決策進行分析
            critical_step = critical_decisions[0] if critical_decisions else 0
            
            states = episode_data.get('states', [])
            actions = episode_data.get('actions', [])
            q_values_list = episode_data.get('q_values', [])
            
            if critical_step >= len(actions):
                return None
            
            original_action = actions[critical_step]
            q_values = q_values_list[critical_step] if critical_step < len(q_values_list) else {}
            
            # 生成替代動作
            alternative_actions = [action for action in q_values.keys() if action != original_action]
            if not alternative_actions:
                return None
            
            # 模擬不同決策的結果
            outcome_differences = {}
            likelihood_scores = {}
            what_if_scenarios = []
            
            for alt_action in alternative_actions[:3]:  # 分析前3個替代動作
                # 估計結果差異
                original_q = q_values.get(original_action, 0)
                alt_q = q_values.get(alt_action, 0)
                outcome_diff = alt_q - original_q
                
                outcome_differences[str(alt_action)] = outcome_diff
                
                # 計算選擇該動作的可能性
                likelihood = self._calculate_action_likelihood(alt_action, q_values)
                likelihood_scores[str(alt_action)] = likelihood
                
                # 生成假設情景
                scenario = {
                    "alternative_action": alt_action,
                    "expected_outcome": outcome_diff,
                    "probability": likelihood,
                    "reasoning": f"如果選擇 {alt_action} 而不是 {original_action}，預期獎勵差異為 {outcome_diff:.3f}"
                }
                what_if_scenarios.append(scenario)
            
            return CounterfactualAnalysis(
                original_decision=original_action,
                alternative_decisions=alternative_actions,
                outcome_differences=outcome_differences,
                likelihood_scores=likelihood_scores,
                what_if_scenarios=what_if_scenarios
            )
            
        except Exception as e:
            self.logger.warning(f"Counterfactual analysis failed: {e}")
            return None
    
    def _generate_step_reasoning(
        self, 
        state: Dict, 
        action: Any, 
        q_values: Dict, 
        confidence: float
    ) -> str:
        """生成單步決策推理"""
        if not q_values:
            return f"選擇動作 {action}（置信度: {confidence:.2f}）"
        
        best_action = max(q_values, key=q_values.get)
        best_q = q_values[best_action]
        chosen_q = q_values.get(action, 0)
        
        if action == best_action:
            return f"選擇最佳動作 {action}（Q值: {chosen_q:.3f}, 置信度: {confidence:.2f}）"
        else:
            q_diff = best_q - chosen_q
            return f"選擇次優動作 {action}（Q值: {chosen_q:.3f}, 與最佳差距: {q_diff:.3f}, 置信度: {confidence:.2f}）"
    
    def _is_critical_decision(self, q_values: Dict, confidence: float) -> bool:
        """判斷是否為關鍵決策"""
        if not q_values or len(q_values) < 2:
            return False
        
        # 低置信度的決策
        if confidence < 0.6:
            return True
        
        # Q值差距很小的決策
        q_list = list(q_values.values())
        q_list.sort(reverse=True)
        if len(q_list) >= 2 and (q_list[0] - q_list[1]) < 0.1:
            return True
        
        return False
    
    async def _generate_alternative_paths(
        self, 
        path_nodes: List[DecisionPathNode], 
        critical_decisions: List[int]
    ) -> List[List[DecisionPathNode]]:
        """生成替代路徑（簡化版）"""
        alternative_paths = []
        
        # 對每個關鍵決策生成一個替代路徑
        for critical_step in critical_decisions[:2]:  # 最多生成2個替代路徑
            if critical_step < len(path_nodes):
                alt_path = path_nodes.copy()
                node = alt_path[critical_step]
                
                # 選擇不同的動作
                if len(node.available_actions) > 1:
                    alt_actions = [a for a in node.available_actions if a != node.chosen_action]
                    if alt_actions:
                        alt_action = alt_actions[0]
                        
                        # 創建修改後的節點
                        alt_node = DecisionPathNode(
                            step=node.step,
                            state=node.state,
                            available_actions=node.available_actions,
                            chosen_action=alt_action,
                            q_values=node.q_values,
                            confidence=node.confidence * 0.8,  # 降低置信度
                            reasoning=f"替代選擇: {alt_action} (原選擇: {node.chosen_action})"
                        )
                        
                        alt_path[critical_step] = alt_node
                        alternative_paths.append(alt_path)
        
        return alternative_paths
    
    def _calculate_path_quality(self, path_nodes: List[DecisionPathNode], total_reward: float) -> float:
        """計算路徑品質分數"""
        if not path_nodes:
            return 0.0
        
        # 基於總獎勵的標準化分數
        reward_score = min(1.0, max(0.0, (total_reward + 100) / 200))  # 假設獎勵範圍 [-100, 100]
        
        # 基於決策置信度的分數
        confidence_scores = [node.confidence for node in path_nodes]
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
        
        # 基於決策一致性的分數
        consistency_score = self._calculate_decision_consistency(path_nodes)
        
        # 綜合分數
        quality_score = 0.4 * reward_score + 0.3 * avg_confidence + 0.3 * consistency_score
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_decision_consistency(self, path_nodes: List[DecisionPathNode]) -> float:
        """計算決策一致性"""
        if len(path_nodes) < 2:
            return 1.0
        
        consistent_decisions = 0
        total_comparisons = 0
        
        for i in range(1, len(path_nodes)):
            prev_node = path_nodes[i-1]
            curr_node = path_nodes[i]
            
            # 比較相似狀態下的決策一致性（簡化版）
            if self._states_similar(prev_node.state, curr_node.state):
                if prev_node.chosen_action == curr_node.chosen_action:
                    consistent_decisions += 1
                total_comparisons += 1
        
        return consistent_decisions / total_comparisons if total_comparisons > 0 else 1.0
    
    def _states_similar(self, state1: Dict, state2: Dict, threshold: float = 0.8) -> bool:
        """判斷兩個狀態是否相似（簡化版）"""
        if not isinstance(state1, dict) or not isinstance(state2, dict):
            return False
        
        common_keys = set(state1.keys()) & set(state2.keys())
        if not common_keys:
            return False
        
        similarities = []
        for key in common_keys:
            val1, val2 = state1[key], state2[key]
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if val1 == 0 and val2 == 0:
                    similarities.append(1.0)
                elif val1 == 0 or val2 == 0:
                    similarities.append(0.0)
                else:
                    sim = 1 - abs(val1 - val2) / max(abs(val1), abs(val2))
                    similarities.append(max(0, sim))
        
        return np.mean(similarities) > threshold if similarities else False
    
    def _generate_path_improvements(
        self, 
        path_nodes: List[DecisionPathNode], 
        critical_decisions: List[int]
    ) -> List[str]:
        """生成路徑改進建議"""
        suggestions = []
        
        if not path_nodes:
            return suggestions
        
        # 分析低置信度決策
        low_confidence_steps = [
            i for i, node in enumerate(path_nodes) 
            if node.confidence < 0.6
        ]
        
        if low_confidence_steps:
            suggestions.append(f"在步驟 {low_confidence_steps} 的決策置信度較低，建議增加探索或調整策略")
        
        # 分析關鍵決策
        if critical_decisions:
            suggestions.append(f"步驟 {critical_decisions} 為關鍵決策點，建議重點優化這些時刻的決策品質")
        
        # 分析決策一致性
        consistency = self._calculate_decision_consistency(path_nodes)
        if consistency < 0.7:
            suggestions.append("決策一致性偏低，建議檢查狀態表示和策略穩定性")
        
        # 分析 Q 值分布
        q_ranges = []
        for node in path_nodes:
            if node.q_values:
                q_vals = list(node.q_values.values())
                q_range = max(q_vals) - min(q_vals)
                q_ranges.append(q_range)
        
        if q_ranges and np.mean(q_ranges) < 0.1:
            suggestions.append("動作價值差異較小，建議增加獎勵信號的區分度")
        
        return suggestions
    
    def _interpret_feature_importance(self, feature_name: str, importance: float) -> str:
        """解釋特徵重要性"""
        if importance > 0.3:
            level = "極高"
        elif importance > 0.2:
            level = "高"
        elif importance > 0.1:
            level = "中等"
        else:
            level = "低"
        
        return f"特徵 '{feature_name}' 對決策的影響程度為{level}（{importance:.3f}），" \
               f"{'是關鍵決策因子' if importance > 0.2 else '具有一定影響力'}"
    
    def _calculate_action_likelihood(self, action: Any, q_values: Dict) -> float:
        """計算動作選擇可能性"""
        if not q_values:
            return 0.5
        
        action_q = q_values.get(action, 0)
        all_q_values = list(q_values.values())
        
        # 使用 softmax 計算概率
        exp_q = np.exp(np.array(all_q_values))
        probabilities = exp_q / np.sum(exp_q)
        
        # 找到該動作的概率
        action_index = list(q_values.keys()).index(action) if action in q_values else 0
        return float(probabilities[action_index]) if action_index < len(probabilities) else 0.0
    
    async def _calculate_explainability_stats(
        self, 
        episode_data: Dict[str, Any], 
        decision_path: DecisionPathAnalysis
    ) -> Dict[str, float]:
        """計算可解釋性統計指標"""
        # 整體置信度
        confidences = [node.confidence for node in decision_path.path_nodes]
        overall_confidence = np.mean(confidences) if confidences else 0.5
        
        # 預測準確性（基於獎勵）
        total_reward = episode_data.get('total_reward', 0)
        expected_reward = episode_data.get('expected_reward', 0)
        prediction_accuracy = 1.0 - abs(total_reward - expected_reward) / max(abs(expected_reward), 1) \
                             if expected_reward != 0 else 0.8
        prediction_accuracy = max(0.0, min(1.0, prediction_accuracy))
        
        # 決策一致性
        decision_consistency = self._calculate_decision_consistency(decision_path.path_nodes)
        
        return {
            'overall_confidence': overall_confidence,
            'prediction_accuracy': prediction_accuracy,
            'decision_consistency': decision_consistency
        }
    
    async def _generate_visualization_data(
        self,
        decision_path: DecisionPathAnalysis,
        feature_importance: List[FeatureImportanceResult],
        counterfactual: Optional[CounterfactualAnalysis]
    ) -> Dict[str, Any]:
        """生成視覺化數據"""
        viz_data = {
            # 決策路徑視覺化
            'decision_path': {
                'steps': [node.step for node in decision_path.path_nodes],
                'confidences': [node.confidence for node in decision_path.path_nodes],
                'actions': [str(node.chosen_action) for node in decision_path.path_nodes],
                'critical_points': decision_path.critical_decisions
            },
            
            # 特徵重要性視覺化
            'feature_importance': {
                'features': [fi.feature_name for fi in feature_importance[:10]],
                'importances': [fi.importance_score for fi in feature_importance[:10]],
                'methods': [fi.method for fi in feature_importance[:10]]
            },
            
            # 品質指標視覺化
            'quality_metrics': {
                'path_quality': decision_path.path_quality_score,
                'critical_decision_count': len(decision_path.critical_decisions),
                'total_steps': len(decision_path.path_nodes)
            }
        }
        
        # 反事實分析視覺化
        if counterfactual:
            viz_data['counterfactual'] = {
                'original_action': str(counterfactual.original_decision),
                'alternatives': [str(a) for a in counterfactual.alternative_decisions],
                'outcome_diffs': list(counterfactual.outcome_differences.values()),
                'likelihoods': list(counterfactual.likelihood_scores.values())
            }
        
        return viz_data
    
    async def _generate_improvement_recommendations(
        self,
        decision_path: DecisionPathAnalysis,
        feature_importance: List[FeatureImportanceResult],
        stats: Dict[str, float]
    ) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        # 基於路徑品質的建議
        if decision_path.path_quality_score < 0.6:
            recommendations.append("決策路徑品質偏低，建議檢查獎勵函數設計和策略訓練穩定性")
        
        # 基於置信度的建議
        if stats['overall_confidence'] < 0.7:
            recommendations.append("決策置信度偏低，建議增加訓練數據或調整網絡架構")
        
        # 基於特徵重要性的建議
        if len(feature_importance) < 3:
            recommendations.append("重要特徵數量較少，建議豐富狀態表示或檢查特徵工程")
        
        top_feature_importance = feature_importance[0].importance_score if feature_importance else 0
        if top_feature_importance > 0.8:
            recommendations.append("存在主導性特徵，建議檢查特徵平衡性和模型過擬合風險")
        
        # 基於決策一致性的建議
        if stats['decision_consistency'] < 0.6:
            recommendations.append("決策一致性較低，建議檢查狀態歸一化和策略穩定性")
        
        # 基於關鍵決策的建議
        if len(decision_path.critical_decisions) > len(decision_path.path_nodes) * 0.3:
            recommendations.append("關鍵決策過多，建議提高策略確定性或優化探索策略")
        
        return recommendations
    
    async def _generate_research_insights(
        self,
        episode_data: Dict[str, Any],
        decision_path: DecisionPathAnalysis,
        feature_importance: List[FeatureImportanceResult]
    ) -> List[str]:
        """生成研究洞察（研究級別專用）"""
        insights = []
        
        # 算法行為模式分析
        algorithm_name = episode_data.get('algorithm_name', 'Unknown')
        insights.append(f"{algorithm_name} 算法在此場景下的決策模式分析：")
        
        # 探索vs利用分析
        exploration_steps = len([
            node for node in decision_path.path_nodes 
            if node.confidence < 0.7
        ])
        exploration_ratio = exploration_steps / len(decision_path.path_nodes)
        insights.append(f"探索率: {exploration_ratio:.2f}, {'偏向探索' if exploration_ratio > 0.3 else '偏向利用'}")
        
        # 特徵依賴性分析
        if feature_importance:
            top_feature = feature_importance[0]
            insights.append(f"主要依賴特徵: {top_feature.feature_name} (重要性: {top_feature.importance_score:.3f})")
        
        # 決策穩定性分析
        confidence_variance = np.var([node.confidence for node in decision_path.path_nodes])
        insights.append(f"決策穩定性: {'穩定' if confidence_variance < 0.1 else '不穩定'} (方差: {confidence_variance:.3f})")
        
        # 學習效果分析
        if len(decision_path.path_nodes) > 10:
            early_confidence = np.mean([node.confidence for node in decision_path.path_nodes[:5]])
            late_confidence = np.mean([node.confidence for node in decision_path.path_nodes[-5:]])
            learning_trend = late_confidence - early_confidence
            insights.append(f"學習趨勢: {'正向' if learning_trend > 0 else '負向'} (變化: {learning_trend:+.3f})")
        
        return insights
    
    async def _create_fallback_report(
        self, 
        episode_data: Dict[str, Any], 
        error: Exception
    ) -> ExplainabilityReport:
        """創建錯誤情況下的備用報告"""
        episode_id = episode_data.get('episode_id', 'unknown')
        
        return ExplainabilityReport(
            report_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            episode_id=episode_id,
            algorithm_name=episode_data.get('algorithm_name', 'Unknown'),
            explainability_level=ExplainabilityLevel.BASIC,
            decision_path=DecisionPathAnalysis(
                episode_id=episode_id,
                algorithm_name='Unknown',
                path_nodes=[],
                critical_decisions=[],
                alternative_paths=[],
                path_quality_score=0.0,
                improvement_suggestions=[f"分析失敗: {str(error)}"]
            ),
            feature_importance=[],
            counterfactual=None,
            overall_confidence=0.0,
            prediction_accuracy=0.0,
            decision_consistency=0.0,
            visualization_data={},
            improvement_recommendations=[f"無法生成建議，錯誤: {str(error)}"],
            research_insights=[]
        )
    
    async def batch_analyze_episodes(
        self,
        episodes_data: List[Dict[str, Any]],
        explainability_level: Optional[ExplainabilityLevel] = None
    ) -> List[ExplainabilityReport]:
        """批量分析多個 episodes"""
        reports = []
        
        for episode_data in episodes_data:
            try:
                report = await self.analyze_decision_explainability(episode_data, explainability_level)
                reports.append(report)
            except Exception as e:
                self.logger.error(f"Failed to analyze episode {episode_data.get('episode_id', 'unknown')}: {e}")
                fallback_report = await self._create_fallback_report(episode_data, e)
                reports.append(fallback_report)
        
        return reports
    
    async def compare_algorithm_explainability(
        self,
        algorithm_reports: Dict[str, List[ExplainabilityReport]]
    ) -> Dict[str, Any]:
        """比較不同算法的可解釋性"""
        comparison = {
            'algorithms': list(algorithm_reports.keys()),
            'metrics': {},
            'insights': []
        }
        
        for algorithm_name, reports in algorithm_reports.items():
            if not reports:
                continue
            
            # 計算平均指標
            avg_confidence = np.mean([r.overall_confidence for r in reports])
            avg_accuracy = np.mean([r.prediction_accuracy for r in reports])
            avg_consistency = np.mean([r.decision_consistency for r in reports])
            avg_path_quality = np.mean([r.decision_path.path_quality_score for r in reports])
            
            comparison['metrics'][algorithm_name] = {
                'confidence': avg_confidence,
                'accuracy': avg_accuracy,
                'consistency': avg_consistency,
                'path_quality': avg_path_quality,
                'report_count': len(reports)
            }
        
        # 生成比較洞察
        if len(comparison['metrics']) > 1:
            best_confidence = max(comparison['metrics'].items(), key=lambda x: x[1]['confidence'])
            best_accuracy = max(comparison['metrics'].items(), key=lambda x: x[1]['accuracy'])
            
            comparison['insights'].append(f"{best_confidence[0]} 具有最高的決策置信度 ({best_confidence[1]['confidence']:.3f})")
            comparison['insights'].append(f"{best_accuracy[0]} 具有最高的預測準確性 ({best_accuracy[1]['accuracy']:.3f})")
        
        return comparison