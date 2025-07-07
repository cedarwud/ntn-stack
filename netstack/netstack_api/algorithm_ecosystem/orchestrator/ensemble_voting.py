"""
集成投票模組 - 從 orchestrator.py 中提取的集成投票邏輯
負責多算法協調與投票決策，實現算法集成功能
"""
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from ..interfaces import HandoverDecision, HandoverContext

logger = logging.getLogger(__name__)


class EnsembleVotingManager:
    """集成投票管理器 - 負責多算法集成決策和投票邏輯"""
    
    def __init__(self, algorithm_metrics: Dict):
        self._ensemble_decisions: List[Tuple[str, HandoverDecision, datetime]] = []
        self._algorithm_metrics = algorithm_metrics
    
    async def initialize_ensemble(self) -> None:
        """初始化集成決策"""
        self._ensemble_decisions = []
        logger.info("集成決策已初始化")
    
    async def handle_ensemble_decision(
        self, 
        context: HandoverContext, 
        current_decision: HandoverDecision, 
        algorithm_name: str,
        ensemble_config: Dict[str, Any]
    ) -> HandoverDecision:
        """處理集成決策
        
        Args:
            context: 換手上下文
            current_decision: 當前決策
            algorithm_name: 算法名稱
            ensemble_config: 集成配置
            
        Returns:
            HandoverDecision: 最終集成決策
        """
        # 記錄當前決策
        self._ensemble_decisions.append((algorithm_name, current_decision, datetime.now()))
        
        # 清理舊決策（只保留最近一段時間的）
        cutoff_time = datetime.now() - timedelta(seconds=1)
        self._ensemble_decisions = [
            (name, decision, timestamp) for name, decision, timestamp in self._ensemble_decisions
            if timestamp > cutoff_time
        ]
        
        min_algorithms = ensemble_config.get('min_algorithms', 2)
        
        # 如果決策數量不足，直接返回當前決策
        if len(self._ensemble_decisions) < min_algorithms:
            return current_decision
        
        # 執行集成投票
        voting_strategy = ensemble_config.get('voting_strategy', 'majority')
        
        if voting_strategy == 'majority':
            return self._majority_voting()
        elif voting_strategy == 'weighted':
            return self._weighted_voting()
        elif voting_strategy == 'confidence_based':
            return self._confidence_voting()
        else:
            return current_decision
    
    def _majority_voting(self) -> HandoverDecision:
        """多數投票
        
        Returns:
            HandoverDecision: 多數投票結果
        """
        decisions = [decision for _, decision, _ in self._ensemble_decisions]
        
        # 統計決策類型
        decision_counts = defaultdict(int)
        for decision in decisions:
            decision_counts[decision.handover_decision] += 1
        
        # 找出多數決策
        majority_decision = max(decision_counts.items(), key=lambda x: x[1])[0]
        
        # 找出具有該決策類型且信心度最高的決策
        best_decision = None
        highest_confidence = 0.0
        
        for decision in decisions:
            if decision.handover_decision == majority_decision and decision.confidence > highest_confidence:
                highest_confidence = decision.confidence
                best_decision = decision
        
        if best_decision:
            best_decision.algorithm_name += " (ensemble)"
            best_decision.metadata['ensemble_voting'] = 'majority'
            best_decision.metadata['ensemble_count'] = len(decisions)
        
        return best_decision or decisions[0]
    
    def _weighted_voting(self) -> HandoverDecision:
        """加權投票
        
        Returns:
            HandoverDecision: 加權投票結果
        """
        decisions = [decision for _, decision, _ in self._ensemble_decisions]
        algorithm_names = [name for name, _, _ in self._ensemble_decisions]
        
        # 根據算法性能計算權重
        weights = []
        for name in algorithm_names:
            metrics = self._algorithm_metrics[name]
            weight = metrics.success_rate * metrics.average_confidence if metrics.total_requests > 0 else 0.5
            weights.append(weight)
        
        # 加權投票
        decision_scores = defaultdict(float)
        for i, decision in enumerate(decisions):
            decision_scores[decision.handover_decision] += weights[i]
        
        # 選擇得分最高的決策類型
        best_decision_type = max(decision_scores.items(), key=lambda x: x[1])[0]
        
        # 找出該類型中信心度最高的決策
        best_decision = None
        highest_confidence = 0.0
        
        for decision in decisions:
            if decision.handover_decision == best_decision_type and decision.confidence > highest_confidence:
                highest_confidence = decision.confidence
                best_decision = decision
        
        if best_decision:
            best_decision.algorithm_name += " (ensemble)"
            best_decision.metadata['ensemble_voting'] = 'weighted'
            best_decision.metadata['ensemble_count'] = len(decisions)
        
        return best_decision or decisions[0]
    
    def _confidence_voting(self) -> HandoverDecision:
        """基於信心度的投票
        
        Returns:
            HandoverDecision: 信心度最高的決策
        """
        decisions = [decision for _, decision, _ in self._ensemble_decisions]
        
        # 直接選擇信心度最高的決策
        best_decision = max(decisions, key=lambda x: x.confidence)
        best_decision.algorithm_name += " (ensemble)"
        best_decision.metadata['ensemble_voting'] = 'confidence_based'
        best_decision.metadata['ensemble_count'] = len(decisions)
        
        return best_decision
    
    def get_current_ensemble_state(self) -> Dict[str, Any]:
        """獲取當前集成狀態
        
        Returns:
            Dict: 集成狀態信息
        """
        return {
            'active_decisions': len(self._ensemble_decisions),
            'algorithms_involved': list(set(name for name, _, _ in self._ensemble_decisions)),
            'decision_types': list(set(decision.handover_decision for _, decision, _ in self._ensemble_decisions)),
            'average_confidence': sum(decision.confidence for _, decision, _ in self._ensemble_decisions) / len(self._ensemble_decisions) if self._ensemble_decisions else 0.0
        }
    
    def clear_ensemble_history(self) -> None:
        """清除集成歷史"""
        self._ensemble_decisions = []
        logger.info("集成決策歷史已清除")
    
    def get_ensemble_statistics(self) -> Dict[str, Any]:
        """獲取集成統計信息
        
        Returns:
            Dict: 統計信息
        """
        if not self._ensemble_decisions:
            return {'total_decisions': 0}
        
        # 算法參與統計
        algorithm_participation = defaultdict(int)
        decision_type_distribution = defaultdict(int)
        confidence_scores = []
        
        for name, decision, timestamp in self._ensemble_decisions:
            algorithm_participation[name] += 1
            decision_type_distribution[decision.handover_decision] += 1
            confidence_scores.append(decision.confidence)
        
        return {
            'total_decisions': len(self._ensemble_decisions),
            'algorithm_participation': dict(algorithm_participation),
            'decision_type_distribution': dict(decision_type_distribution),
            'average_confidence': sum(confidence_scores) / len(confidence_scores),
            'confidence_range': {
                'min': min(confidence_scores),
                'max': max(confidence_scores)
            }
        }