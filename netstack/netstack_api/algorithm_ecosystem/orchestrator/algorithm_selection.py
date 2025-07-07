"""
算法選擇策略模組 - 從 orchestrator.py 中提取的算法選擇邏輯
處理各種算法選擇策略，避免在主協調器中過度複雜化
"""
from typing import List, Optional, Tuple
import numpy as np

from ..interfaces import HandoverAlgorithm, HandoverContext
from ..registry import AlgorithmRegistry


class OrchestratorMode:
    """協調器模式枚舉"""
    SINGLE_ALGORITHM = "single_algorithm"
    MULTI_ALGORITHM = "multi_algorithm"
    AB_TESTING = "ab_testing"
    ENSEMBLE = "ensemble"


class DecisionStrategy:
    """決策策略枚舉"""
    PRIORITY_BASED = "priority_based"
    PERFORMANCE_BASED = "performance_based"
    ROUND_ROBIN = "round_robin"
    WEIGHTED_RANDOM = "weighted_random"
    CONFIDENCE_BASED = "confidence_based"


class AlgorithmSelector:
    """算法選擇器 - 負責根據不同策略選擇最適合的算法"""
    
    def __init__(self, algorithm_registry: AlgorithmRegistry, algorithm_metrics: dict):
        self.algorithm_registry = algorithm_registry
        self._algorithm_metrics = algorithm_metrics
        self._round_robin_counter = 0
    
    async def select_algorithm(self, context: HandoverContext, mode: str, 
                             strategy: str, default_algorithm: Optional[str] = None) -> Tuple[Optional[HandoverAlgorithm], Optional[str]]:
        """選擇算法
        
        Args:
            context: 換手上下文
            mode: 協調器模式
            strategy: 決策策略
            default_algorithm: 默認算法
            
        Returns:
            Tuple[HandoverAlgorithm, str]: 選擇的算法和名稱
        """
        available_algorithms = self.algorithm_registry.list_enabled_algorithms()
        
        if not available_algorithms:
            return None, None
        
        if mode == OrchestratorMode.SINGLE_ALGORITHM:
            # 單一算法模式
            algorithm_name = default_algorithm or available_algorithms[0]
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        elif strategy == DecisionStrategy.PRIORITY_BASED:
            # 優先級選擇
            algorithm = self.algorithm_registry.get_best_algorithm("priority")
            algorithm_name = algorithm.name if algorithm else None
            return algorithm, algorithm_name
        
        elif strategy == DecisionStrategy.PERFORMANCE_BASED:
            # 性能選擇
            best_algorithm_name = self._get_best_performing_algorithm()
            algorithm = self.algorithm_registry.get_algorithm(best_algorithm_name)
            return algorithm, best_algorithm_name
        
        elif strategy == DecisionStrategy.ROUND_ROBIN:
            # 輪詢選擇
            algorithm_name = available_algorithms[self._round_robin_counter % len(available_algorithms)]
            self._round_robin_counter += 1
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        elif strategy == DecisionStrategy.WEIGHTED_RANDOM:
            # 加權隨機選擇
            algorithm_name = self._weighted_random_selection(available_algorithms)
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        elif strategy == DecisionStrategy.CONFIDENCE_BASED:
            # 基於歷史信心度選擇
            algorithm_name = self._confidence_based_selection(available_algorithms)
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        else:
            # 默認選擇第一個可用算法
            algorithm_name = available_algorithms[0]
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
    
    def _get_best_performing_algorithm(self) -> str:
        """獲取性能最佳的算法"""
        available_algorithms = self.algorithm_registry.list_enabled_algorithms()
        
        if not available_algorithms:
            return None
        
        best_algorithm = available_algorithms[0]
        best_score = 0.0
        
        for algorithm_name in available_algorithms:
            metrics = self._algorithm_metrics[algorithm_name]
            if metrics.total_requests > 0:
                # 綜合評分：成功率 * 0.6 + (1 - 標準化響應時間) * 0.3 + 平均信心度 * 0.1
                success_score = metrics.success_rate * 0.6
                
                # 標準化響應時間（越小越好）
                if metrics.average_response_time > 0:
                    time_score = max(0, 1 - metrics.average_response_time / 1000) * 0.3
                else:
                    time_score = 0.3
                
                confidence_score = metrics.average_confidence * 0.1
                
                total_score = success_score + time_score + confidence_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_algorithm = algorithm_name
        
        return best_algorithm
    
    def _weighted_random_selection(self, algorithms: List[str]) -> str:
        """加權隨機選擇"""
        weights = []
        for algorithm_name in algorithms:
            metrics = self._algorithm_metrics[algorithm_name]
            if metrics.total_requests > 0:
                # 權重基於成功率和信心度
                weight = metrics.success_rate * metrics.average_confidence
            else:
                weight = 0.5  # 默認權重
            weights.append(weight)
        
        # 歸一化權重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(algorithms)] * len(algorithms)
        
        # 隨機選擇
        return np.random.choice(algorithms, p=weights)
    
    def _confidence_based_selection(self, algorithms: List[str]) -> str:
        """基於信心度的選擇"""
        best_algorithm = algorithms[0]
        highest_confidence = 0.0
        
        for algorithm_name in algorithms:
            metrics = self._algorithm_metrics[algorithm_name]
            if metrics.average_confidence > highest_confidence:
                highest_confidence = metrics.average_confidence
                best_algorithm = algorithm_name
        
        return best_algorithm