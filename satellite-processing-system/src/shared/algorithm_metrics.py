"""
真實算法性能監控 - 專注於學術研究需求

提供 LEO 衛星切換算法研究所需的完整性能測量：
1. 算法執行時間測量
2. 切換延遲統計
3. 系統資源使用監控
4. 基本的性能報告
"""

import time
import psutil
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmMetrics:
    """算法性能指標"""
    algorithm_name: str
    execution_times: List[float] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    start_time: Optional[float] = None
    
    def start_timing(self):
        """開始計時"""
        self.start_time = time.time()
    
    def end_timing(self, success: bool = True):
        """結束計時並記錄結果"""
        if self.start_time is not None:
            execution_time = time.time() - self.start_time
            self.execution_times.append(execution_time)
            
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
            
            self.start_time = None
            return execution_time
        return 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        if not self.execution_times:
            return {
                'algorithm_name': self.algorithm_name,
                'total_executions': 0,
                'success_rate': 0.0,
                'avg_execution_time': 0.0,
                'min_execution_time': 0.0,
                'max_execution_time': 0.0,
                'median_execution_time': 0.0
            }
        
        return {
            'algorithm_name': self.algorithm_name,
            'total_executions': len(self.execution_times),
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / (self.success_count + self.failure_count) * 100,
            'avg_execution_time': statistics.mean(self.execution_times),
            'min_execution_time': min(self.execution_times),
            'max_execution_time': max(self.execution_times),
            'median_execution_time': statistics.median(self.execution_times),
            'std_execution_time': statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0.0
        }


class SimplePerformanceMonitor:
    """真實性能監控器 - 專注於算法研究"""
    
    def __init__(self, monitor_id: str = "algorithm_monitor"):
        self.monitor_id = monitor_id
        self.algorithm_metrics: Dict[str, AlgorithmMetrics] = {}
        self.system_metrics_history = deque(maxlen=1000)
        self.start_time = datetime.now(timezone.utc)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_algorithm_metrics(self, algorithm_name: str) -> AlgorithmMetrics:
        """獲取或創建算法指標"""
        if algorithm_name not in self.algorithm_metrics:
            self.algorithm_metrics[algorithm_name] = AlgorithmMetrics(algorithm_name)
        return self.algorithm_metrics[algorithm_name]
    
    def time_algorithm(self, algorithm_name: str, func, *args, **kwargs):
        """計時執行算法"""
        metrics = self.get_algorithm_metrics(algorithm_name)
        metrics.start_timing()
        
        try:
            result = func(*args, **kwargs)
            metrics.end_timing(success=True)
            return result
        except Exception as e:
            metrics.end_timing(success=False)
            self.logger.error(f"Algorithm {algorithm_name} failed: {e}")
            raise
    
    def record_handover_latency(self, source_satellite: str, target_satellite: str, 
                              latency_ms: float, success: bool = True):
        """記錄衛星切換延遲"""
        handover_key = f"handover_{source_satellite}_to_{target_satellite}"
        metrics = self.get_algorithm_metrics(handover_key)
        
        # 模擬計時記錄
        metrics.execution_times.append(latency_ms / 1000.0)  # 轉換為秒
        if success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
        
        self.logger.info(f"Handover {source_satellite} -> {target_satellite}: {latency_ms}ms, Success: {success}")
    
    def record_prediction_accuracy(self, prediction_algorithm: str, accuracy: float):
        """記錄預測算法準確性"""
        metrics = self.get_algorithm_metrics(f"prediction_{prediction_algorithm}")
        metrics.execution_times.append(accuracy)  # 使用執行時間字段存儲準確性
        metrics.success_count += 1
        
        self.logger.info(f"Prediction {prediction_algorithm} accuracy: {accuracy:.2%}")
    
    def collect_system_metrics(self):
        """收集系統性能指標"""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_mb': memory.available / 1024 / 1024,
                'memory_used_mb': memory.used / 1024 / 1024
            }
            
            self.system_metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return None
    
    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能報告"""
        report = {
            'monitor_id': self.monitor_id,
            'report_generated_at': datetime.now(timezone.utc).isoformat(),
            'monitoring_duration_hours': (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600,
            'algorithm_statistics': {},
            'system_metrics_summary': {}
        }
        
        # 算法統計
        for algo_name, metrics in self.algorithm_metrics.items():
            report['algorithm_statistics'][algo_name] = metrics.get_statistics()
        
        # 系統指標摘要
        if self.system_metrics_history:
            recent_metrics = list(self.system_metrics_history)
            cpu_values = [m['cpu_usage_percent'] for m in recent_metrics]
            memory_values = [m['memory_usage_percent'] for m in recent_metrics]
            
            report['system_metrics_summary'] = {
                'avg_cpu_usage': statistics.mean(cpu_values) if cpu_values else 0,
                'max_cpu_usage': max(cpu_values) if cpu_values else 0,
                'avg_memory_usage': statistics.mean(memory_values) if memory_values else 0,
                'max_memory_usage': max(memory_values) if memory_values else 0,
                'samples_collected': len(recent_metrics)
            }
        
        return report
    
    def get_handover_statistics(self) -> Dict[str, Any]:
        """獲取切換統計（專門用於論文分析）"""
        handover_stats = {}
        
        for algo_name, metrics in self.algorithm_metrics.items():
            if algo_name.startswith('handover_'):
                stats = metrics.get_statistics()
                # 將執行時間轉換回毫秒延遲
                stats['avg_latency_ms'] = stats['avg_execution_time'] * 1000
                stats['min_latency_ms'] = stats['min_execution_time'] * 1000
                stats['max_latency_ms'] = stats['max_execution_time'] * 1000
                stats['median_latency_ms'] = stats['median_execution_time'] * 1000
                
                handover_stats[algo_name.replace('handover_', '')] = stats
        
        return handover_stats
    
    def export_metrics_for_analysis(self, filename: str = None) -> str:
        """導出指標用於學術分析"""
        import json
        
        report = self.get_performance_report()
        report['handover_statistics'] = self.get_handover_statistics()
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Metrics exported to {filename}")
            return filename
        else:
            return json.dumps(report, indent=2, ensure_ascii=False)


# === 便利函數 ===

def create_performance_monitor(monitor_id: str = "default") -> SimplePerformanceMonitor:
    """創建性能監控器"""
    monitor = SimplePerformanceMonitor(monitor_id)
    logger.info(f"✅ 算法性能監控器創建完成 - ID: {monitor_id}")
    return monitor


def time_algorithm_execution(monitor: SimplePerformanceMonitor, algorithm_name: str):
    """裝飾器：自動計時算法執行"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return monitor.time_algorithm(algorithm_name, func, *args, **kwargs)
        return wrapper
    return decorator


# === 全域監控器實例 ===
_global_monitor: Optional[SimplePerformanceMonitor] = None


def get_global_monitor() -> SimplePerformanceMonitor:
    """獲取全域性能監控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = create_performance_monitor("global_algorithm_monitor")
    return _global_monitor