"""
性能監控模組 - 從 orchestrator.py 中提取的性能監控邏輯
負責算法性能指標的記錄、統計和分析
"""
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class AlgorithmMetrics:
    """算法性能指標"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.average_response_time = 0.0
        self.min_response_time = float('inf')
        self.max_response_time = 0.0
        self.success_rate = 0.0
        self.confidence_scores = []
        self.average_confidence = 0.0
        self.last_used = None


class PerformanceMonitor:
    """性能監控器 - 負責記錄和分析算法性能指標"""
    
    def __init__(self):
        self._algorithm_metrics: Dict[str, AlgorithmMetrics] = defaultdict(AlgorithmMetrics)
        self._performance_history: Dict[str, List[Dict]] = defaultdict(list)
    
    async def record_algorithm_metrics(
        self, 
        algorithm_name: str, 
        execution_time: float, 
        success: bool, 
        confidence: float
    ) -> None:
        """記錄算法性能指標
        
        Args:
            algorithm_name: 算法名稱
            execution_time: 執行時間
            success: 是否成功
            confidence: 信心度
        """
        metrics = self._algorithm_metrics[algorithm_name]
        
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        metrics.total_response_time += execution_time
        metrics.average_response_time = metrics.total_response_time / metrics.total_requests
        
        if execution_time < metrics.min_response_time:
            metrics.min_response_time = execution_time
        if execution_time > metrics.max_response_time:
            metrics.max_response_time = execution_time
        
        metrics.success_rate = metrics.successful_requests / metrics.total_requests
        
        if success:
            metrics.confidence_scores.append(confidence)
            if len(metrics.confidence_scores) > 100:
                metrics.confidence_scores.pop(0)
            metrics.average_confidence = sum(metrics.confidence_scores) / len(metrics.confidence_scores)
        
        metrics.last_used = datetime.now()
        
        # 記錄性能歷史
        self._performance_history[algorithm_name].append({
            'timestamp': datetime.now(),
            'execution_time': execution_time,
            'success': success,
            'confidence': confidence
        })
    
    def get_algorithm_metrics(self, algorithm_name: str) -> AlgorithmMetrics:
        """獲取算法性能指標"""
        return self._algorithm_metrics[algorithm_name]
    
    def get_all_metrics(self) -> Dict[str, AlgorithmMetrics]:
        """獲取所有算法性能指標"""
        return dict(self._algorithm_metrics)
    
    def get_performance_history(self, algorithm_name: str) -> List[Dict]:
        """獲取算法性能歷史"""
        return self._performance_history[algorithm_name]
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """獲取協調器統計信息"""
        total_requests = sum(metrics.total_requests for metrics in self._algorithm_metrics.values())
        successful_requests = sum(metrics.successful_requests for metrics in self._algorithm_metrics.values())
        failed_requests = sum(metrics.failed_requests for metrics in self._algorithm_metrics.values())
        
        overall_success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'overall_success_rate': overall_success_rate,
            'algorithm_count': len(self._algorithm_metrics),
            'algorithm_stats': {name: {
                'total_requests': metrics.total_requests,
                'success_rate': metrics.success_rate,
                'average_response_time': metrics.average_response_time,
                'average_confidence': metrics.average_confidence
            } for name, metrics in self._algorithm_metrics.items()}
        }
    
    def export_metrics_for_analysis(self) -> Dict[str, Any]:
        """導出指標用於分析"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_algorithms': len(self._algorithm_metrics),
            'algorithms': {},
            'performance_history': {}
        }
        
        # 導出算法指標
        for name, metrics in self._algorithm_metrics.items():
            export_data['algorithms'][name] = {
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'failed_requests': metrics.failed_requests,
                'success_rate': metrics.success_rate,
                'average_response_time': metrics.average_response_time,
                'min_response_time': metrics.min_response_time,
                'max_response_time': metrics.max_response_time,
                'average_confidence': metrics.average_confidence,
                'last_used': metrics.last_used.isoformat() if metrics.last_used else None
            }
        
        # 導出性能歷史
        for algorithm_name in self._algorithm_metrics.keys():
            history = self._performance_history[algorithm_name]
            if history:
                export_data['performance_history'][algorithm_name] = [
                    {
                        'timestamp': record['timestamp'].isoformat(),
                        'execution_time': record['execution_time'],
                        'success': record['success'],
                        'confidence': record['confidence']
                    } for record in history[-100:]  # 只導出最近100條記錄
                ]
        
        return export_data