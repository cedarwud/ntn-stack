"""
A/B測試模組 - 從 orchestrator.py 中提取的A/B測試邏輯
負責A/B測試的配置、執行和結果分析
"""
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

from ..interfaces import HandoverDecision

logger = logging.getLogger(__name__)


class ABTestManager:
    """A/B測試管理器 - 負責A/B測試的全生命週期管理"""
    
    def __init__(self):
        self._ab_test_weights: Dict[str, float] = {}
        self._ab_test_results: Dict[str, List[float]] = defaultdict(list)
        self._active_ab_tests: Dict[str, Dict[str, float]] = {}
    
    async def initialize_ab_testing(self, ab_test_config: Optional[Dict] = None) -> None:
        """初始化 A/B 測試
        
        Args:
            ab_test_config: A/B測試配置
        """
        if not ab_test_config:
            return
        
        traffic_split = ab_test_config.get('traffic_split', {})
        total_weight = sum(traffic_split.values())
        
        if total_weight > 0:
            self._ab_test_weights = {
                name: weight / total_weight 
                for name, weight in traffic_split.items()
            }
        
        logger.info(f"A/B 測試配置: {self._ab_test_weights}")
    
    async def record_ab_test_result(self, algorithm_name: str, decision: HandoverDecision) -> None:
        """記錄 A/B 測試結果
        
        Args:
            algorithm_name: 算法名稱
            decision: 決策結果
        """
        # 這裡可以記錄各種指標，如信心度、決策類型等
        self._ab_test_results[algorithm_name].append(decision.confidence)
        
        # 限制歷史記錄大小
        if len(self._ab_test_results[algorithm_name]) > 1000:
            self._ab_test_results[algorithm_name].pop(0)
    
    def set_ab_test_config(self, test_id: str, traffic_split: Dict[str, float]) -> None:
        """設置 A/B 測試配置
        
        Args:
            test_id: 測試ID
            traffic_split: 流量分配比例
        """
        self._active_ab_tests[test_id] = traffic_split
        self._ab_test_weights = traffic_split
        
        logger.info(f"設置 A/B 測試配置: {test_id} -> {traffic_split}")
    
    def clear_ab_test_config(self, test_id: str) -> None:
        """清除 A/B 測試配置
        
        Args:
            test_id: 測試ID
        """
        if test_id in self._active_ab_tests:
            del self._active_ab_tests[test_id]
            
            # 如果沒有其他活躍測試，清除權重
            if not self._active_ab_tests:
                self._ab_test_weights = {}
            
            logger.info(f"清除 A/B 測試配置: {test_id}")
        else:
            logger.warning(f"測試 {test_id} 不存在，無法清除")
    
    def get_ab_test_performance(self, test_id: str) -> Dict[str, Any]:
        """獲取 A/B 測試性能數據
        
        Args:
            test_id: 測試ID
            
        Returns:
            Dict: 性能數據
        """
        if test_id not in self._active_ab_tests:
            logger.warning(f"測試 {test_id} 不存在")
            return {}
        
        traffic_split = self._active_ab_tests[test_id]
        performance_data = {}
        
        for algorithm_name in traffic_split:
            if algorithm_name in self._ab_test_results:
                results = self._ab_test_results[algorithm_name]
                if results:
                    performance_data[algorithm_name] = {
                        'sample_count': len(results),
                        'average_confidence': sum(results) / len(results),
                        'min_confidence': min(results),
                        'max_confidence': max(results),
                        'traffic_allocation': traffic_split[algorithm_name]
                    }
                else:
                    performance_data[algorithm_name] = {
                        'sample_count': 0,
                        'average_confidence': 0.0,
                        'min_confidence': 0.0,
                        'max_confidence': 0.0,
                        'traffic_allocation': traffic_split[algorithm_name]
                    }
        
        return {
            'test_id': test_id,
            'performance_data': performance_data,
            'total_samples': sum(data.get('sample_count', 0) for data in performance_data.values())
        }
    
    def get_ab_test_weights(self) -> Dict[str, float]:
        """獲取當前A/B測試權重"""
        return dict(self._ab_test_weights)
    
    def get_active_tests(self) -> Dict[str, Dict[str, float]]:
        """獲取活躍的A/B測試"""
        return dict(self._active_ab_tests)
    
    def is_ab_testing_active(self) -> bool:
        """檢查是否有活躍的A/B測試"""
        return bool(self._active_ab_tests)
    
    def get_test_results_summary(self) -> Dict[str, Any]:
        """獲取測試結果摘要"""
        summary = {
            'active_tests': len(self._active_ab_tests),
            'total_algorithms_tested': len(self._ab_test_results),
            'algorithm_results': {}
        }
        
        for algorithm_name, results in self._ab_test_results.items():
            if results:
                summary['algorithm_results'][algorithm_name] = {
                    'total_samples': len(results),
                    'average_confidence': sum(results) / len(results),
                    'confidence_variance': sum((x - sum(results) / len(results)) ** 2 for x in results) / len(results)
                }
        
        return summary