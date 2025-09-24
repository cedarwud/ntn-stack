"""
Stage 4 Optimization Performance Monitor

This module provides comprehensive performance monitoring, metrics collection,
and benchmarking for the Stage 4 optimization decision layer.

Features:
- Real-time performance tracking
- Memory usage monitoring
- Decision quality metrics
- Algorithm convergence analysis
- Bottleneck identification
- Performance alerts and thresholds
"""

import logging
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import statistics
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""
    timestamp: str
    processing_time_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    satellites_processed: int
    decision_quality_score: float
    constraint_satisfaction_rate: float
    optimization_effectiveness: float
    algorithm_convergence: str
    error_count: int


@dataclass
class AlgorithmBenchmark:
    """算法基準測試結果"""
    algorithm_name: str
    input_size: int
    processing_time: float
    memory_peak: float
    quality_score: float
    convergence_iterations: int
    success_rate: float


class PerformanceMonitor:
    """性能監控器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.PerformanceMonitor")

        # 監控配置
        self.enable_detailed_metrics = self.config.get('enable_detailed_metrics', True)
        self.enable_real_time_monitoring = self.config.get('enable_real_time_monitoring', False)
        self.metric_collection_interval = self.config.get('metric_collection_interval', 1.0)
        self.max_history_size = self.config.get('max_history_size', 1000)

        # 性能目標
        self.benchmark_targets = self.config.get('benchmark_targets', {
            'processing_time_max_seconds': 10.0,
            'memory_usage_max_mb': 300,
            'decision_quality_min_score': 0.8,
            'constraint_satisfaction_min_rate': 0.95
        })

        # 監控數據
        self.metrics_history: deque = deque(maxlen=self.max_history_size)
        self.algorithm_benchmarks: List[AlgorithmBenchmark] = []
        self.performance_alerts: List[Dict[str, Any]] = []

        # 實時監控
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # 統計信息
        self.total_processes = 0
        self.total_errors = 0
        self.start_time = datetime.now(timezone.utc)

        # 當前處理追蹤
        self.current_process_start: Optional[float] = None
        self.current_process_metrics: Dict[str, Any] = {}

        self.logger.info("✅ 性能監控器初始化完成")

    def start_process_monitoring(self, process_info: Dict[str, Any] = None):
        """開始處理過程監控"""
        self.current_process_start = time.time()
        self.current_process_metrics = {
            'process_info': process_info or {},
            'start_time': self.current_process_start,
            'start_memory': self._get_memory_usage(),
            'start_cpu': self._get_cpu_usage(),
            'error_count': 0
        }

        if self.enable_real_time_monitoring and not self.monitoring_active:
            self._start_real_time_monitoring()

        self.logger.debug("📊 開始處理過程監控")

    def end_process_monitoring(self, results: Dict[str, Any] = None) -> PerformanceMetrics:
        """結束處理過程監控並收集指標"""
        if self.current_process_start is None:
            self.logger.warning("⚠️ 沒有正在進行的處理過程監控")
            return self._create_empty_metrics()

        end_time = time.time()
        processing_time = end_time - self.current_process_start

        # 收集性能指標
        metrics = PerformanceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_seconds=processing_time,
            memory_usage_mb=self._get_memory_usage(),
            cpu_usage_percent=self._get_cpu_usage(),
            satellites_processed=self._extract_satellites_count(results),
            decision_quality_score=self._calculate_decision_quality(results),
            constraint_satisfaction_rate=self._calculate_constraint_satisfaction(results),
            optimization_effectiveness=self._calculate_optimization_effectiveness(results),
            algorithm_convergence=self._assess_algorithm_convergence(results),
            error_count=self.current_process_metrics.get('error_count', 0)
        )

        # 存儲指標
        self.metrics_history.append(metrics)
        self.total_processes += 1

        # 檢查性能警報
        self._check_performance_alerts(metrics)

        # 重置當前處理追蹤
        self.current_process_start = None
        self.current_process_metrics = {}

        if self.enable_real_time_monitoring:
            self._stop_real_time_monitoring()

        self.logger.info(f"📊 處理監控完成: {processing_time:.3f}s")
        return metrics

    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """記錄錯誤"""
        self.total_errors += 1
        if self.current_process_metrics:
            self.current_process_metrics['error_count'] += 1

        error_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'process_info': self.current_process_metrics.get('process_info', {})
        }

        self.logger.error(f"❌ 錯誤記錄: {error_record}")

    def benchmark_algorithm(self, algorithm_name: str, algorithm_func: Callable,
                          test_inputs: List[Any], description: str = "") -> AlgorithmBenchmark:
        """算法基準測試"""
        self.logger.info(f"🏁 開始算法基準測試: {algorithm_name}")

        results = []
        total_time = 0
        peak_memory = 0
        success_count = 0

        for i, test_input in enumerate(test_inputs):
            try:
                # 記錄開始狀態
                start_time = time.time()
                start_memory = self._get_memory_usage()

                # 執行算法
                result = algorithm_func(test_input)

                # 記錄結束狀態
                end_time = time.time()
                end_memory = self._get_memory_usage()

                # 計算指標
                processing_time = end_time - start_time
                memory_used = end_memory - start_memory

                total_time += processing_time
                peak_memory = max(peak_memory, memory_used)
                success_count += 1

                results.append({
                    'input_size': len(test_input) if hasattr(test_input, '__len__') else 1,
                    'processing_time': processing_time,
                    'memory_used': memory_used,
                    'result': result,
                    'success': True
                })

            except Exception as e:
                results.append({
                    'error': str(e),
                    'success': False
                })
                self.logger.error(f"❌ 基準測試失敗 (輸入 {i}): {e}")

        # 計算基準指標
        avg_input_size = statistics.mean([r.get('input_size', 0) for r in results if r.get('success')])
        avg_processing_time = total_time / len(test_inputs) if test_inputs else 0
        success_rate = success_count / len(test_inputs) if test_inputs else 0

        # 估算質量分數 (基於成功率和處理時間)
        quality_score = success_rate * (1.0 / (1.0 + avg_processing_time))

        # 估算收斂迭代次數 (簡化)
        convergence_iterations = max(1, int(avg_processing_time * 10))

        benchmark = AlgorithmBenchmark(
            algorithm_name=algorithm_name,
            input_size=int(avg_input_size),
            processing_time=avg_processing_time,
            memory_peak=peak_memory,
            quality_score=quality_score,
            convergence_iterations=convergence_iterations,
            success_rate=success_rate
        )

        self.algorithm_benchmarks.append(benchmark)

        self.logger.info(f"✅ 算法基準測試完成: {algorithm_name} (成功率: {success_rate:.2%})")
        return benchmark

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.metrics_history:
            return {'status': 'no_data', 'total_processes': self.total_processes}

        recent_metrics = list(self.metrics_history)[-10:]  # 最近10次

        summary = {
            'total_processes': self.total_processes,
            'total_errors': self.total_errors,
            'error_rate': self.total_errors / max(1, self.total_processes),
            'uptime_hours': (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600,

            'processing_time': {
                'average': statistics.mean([m.processing_time_seconds for m in recent_metrics]),
                'median': statistics.median([m.processing_time_seconds for m in recent_metrics]),
                'max': max([m.processing_time_seconds for m in recent_metrics]),
                'min': min([m.processing_time_seconds for m in recent_metrics])
            },

            'memory_usage': {
                'average': statistics.mean([m.memory_usage_mb for m in recent_metrics]),
                'peak': max([m.memory_usage_mb for m in recent_metrics])
            },

            'decision_quality': {
                'average': statistics.mean([m.decision_quality_score for m in recent_metrics]),
                'trend': self._calculate_trend([m.decision_quality_score for m in recent_metrics])
            },

            'constraint_satisfaction': {
                'average': statistics.mean([m.constraint_satisfaction_rate for m in recent_metrics]),
                'compliance_rate': sum(1 for m in recent_metrics
                                     if m.constraint_satisfaction_rate >=
                                     self.benchmark_targets.get('constraint_satisfaction_min_rate', 0.95)) / len(recent_metrics)
            },

            'performance_alerts': len(self.performance_alerts),
            'benchmark_results': len(self.algorithm_benchmarks)
        }

        return summary

    def get_detailed_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """獲取詳細指標"""
        metrics_list = list(self.metrics_history)[-limit:]
        return [asdict(m) for m in metrics_list]

    def get_algorithm_benchmarks(self) -> List[Dict[str, Any]]:
        """獲取算法基準測試結果"""
        return [asdict(b) for b in self.algorithm_benchmarks]

    def get_performance_alerts(self, severity: str = None) -> List[Dict[str, Any]]:
        """獲取性能警報"""
        if severity:
            return [alert for alert in self.performance_alerts
                   if alert.get('severity') == severity]
        return self.performance_alerts.copy()

    def clear_performance_data(self, data_type: str = 'all'):
        """清除性能數據"""
        if data_type in ['all', 'metrics']:
            self.metrics_history.clear()
        if data_type in ['all', 'benchmarks']:
            self.algorithm_benchmarks.clear()
        if data_type in ['all', 'alerts']:
            self.performance_alerts.clear()

        self.logger.info(f"🧹 性能數據已清除: {data_type}")

    def export_performance_data(self, export_path: str, format: str = 'json'):
        """導出性能數據"""
        try:
            data = {
                'summary': self.get_performance_summary(),
                'metrics': self.get_detailed_metrics(),
                'benchmarks': self.get_algorithm_benchmarks(),
                'alerts': self.get_performance_alerts(),
                'export_timestamp': datetime.now(timezone.utc).isoformat()
            }

            if format.lower() == 'json':
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的導出格式: {format}")

            self.logger.info(f"✅ 性能數據導出成功: {export_path}")

        except Exception as e:
            self.logger.error(f"❌ 性能數據導出失敗: {e}")
            raise

    def _get_memory_usage(self) -> float:
        """獲取內存使用量 (MB)"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """獲取CPU使用率"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0

    def _extract_satellites_count(self, results: Dict[str, Any]) -> int:
        """提取處理的衛星數量"""
        if not results:
            return 0

        # 嘗試從多個可能的位置提取衛星數量
        paths = [
            ['metadata', 'optimized_satellites'],
            ['optimal_pool', 'selected_satellites'],
            ['statistics', 'satellites_processed']
        ]

        for path in paths:
            value = results
            for key in path:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break

            if isinstance(value, int):
                return value
            elif isinstance(value, list):
                return len(value)

        return 0

    def _calculate_decision_quality(self, results: Dict[str, Any]) -> float:
        """計算決策質量分數"""
        if not results:
            return 0.0

        # 基於多個因素計算質量分數
        quality_factors = []

        # 檢查是否有最優解
        if results.get('optimization_results', {}).get('pareto_solutions'):
            pareto_count = len(results['optimization_results']['pareto_solutions'])
            quality_factors.append(min(1.0, pareto_count / 10.0))

        # 檢查約束滿足
        constraint_rate = self._calculate_constraint_satisfaction(results)
        quality_factors.append(constraint_rate)

        # 檢查池規劃質量
        pools = results.get('optimal_pool', {}).get('selected_satellites', [])
        if pools:
            pool_quality = min(1.0, len(pools) / 5.0)
            quality_factors.append(pool_quality)

        return statistics.mean(quality_factors) if quality_factors else 0.5

    def _calculate_constraint_satisfaction(self, results: Dict[str, Any]) -> float:
        """計算約束滿足率"""
        # 簡化實現：基於結果結構評估
        if not results:
            return 0.0

        satisfaction_score = 0.8  # 基準分數

        # 檢查是否有錯誤
        if 'error' in results:
            satisfaction_score -= 0.3

        # 檢查關鍵結果是否存在
        required_sections = ['optimal_pool', 'handover_strategy', 'optimization_results']
        present_sections = sum(1 for section in required_sections if section in results)
        satisfaction_score *= (present_sections / len(required_sections))

        return max(0.0, min(1.0, satisfaction_score))

    def _calculate_optimization_effectiveness(self, results: Dict[str, Any]) -> float:
        """計算優化效果"""
        if not results:
            return 0.0

        effectiveness_factors = []

        # 多目標優化效果
        pareto_solutions = results.get('optimization_results', {}).get('pareto_solutions', [])
        if pareto_solutions:
            effectiveness_factors.append(min(1.0, len(pareto_solutions) / 5.0))

        # 換手策略效果
        strategies = results.get('handover_strategy', {}).get('triggers', [])
        if strategies:
            effectiveness_factors.append(min(1.0, len(strategies) / 3.0))

        return statistics.mean(effectiveness_factors) if effectiveness_factors else 0.5

    def _assess_algorithm_convergence(self, results: Dict[str, Any]) -> str:
        """評估算法收斂性"""
        if not results:
            return 'no_data'

        # 基於結果完整性評估收斂
        completeness_score = 0

        if results.get('optimal_pool', {}).get('selected_satellites'):
            completeness_score += 1

        if results.get('optimization_results', {}).get('pareto_solutions'):
            completeness_score += 1

        if results.get('handover_strategy', {}).get('triggers'):
            completeness_score += 1

        if completeness_score >= 3:
            return 'excellent_convergence'
        elif completeness_score >= 2:
            return 'good_convergence'
        elif completeness_score >= 1:
            return 'partial_convergence'
        else:
            return 'poor_convergence'

    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """檢查性能警報"""
        alerts = []

        # 處理時間警報
        max_time = self.benchmark_targets.get('processing_time_max_seconds', 10.0)
        if metrics.processing_time_seconds > max_time:
            alerts.append({
                'type': 'processing_time_exceeded',
                'severity': 'warning' if metrics.processing_time_seconds < max_time * 1.5 else 'critical',
                'value': metrics.processing_time_seconds,
                'threshold': max_time,
                'timestamp': metrics.timestamp
            })

        # 內存使用警報
        max_memory = self.benchmark_targets.get('memory_usage_max_mb', 300)
        if metrics.memory_usage_mb > max_memory:
            alerts.append({
                'type': 'memory_usage_exceeded',
                'severity': 'warning' if metrics.memory_usage_mb < max_memory * 1.5 else 'critical',
                'value': metrics.memory_usage_mb,
                'threshold': max_memory,
                'timestamp': metrics.timestamp
            })

        # 決策質量警報
        min_quality = self.benchmark_targets.get('decision_quality_min_score', 0.8)
        if metrics.decision_quality_score < min_quality:
            alerts.append({
                'type': 'decision_quality_low',
                'severity': 'warning' if metrics.decision_quality_score > min_quality * 0.8 else 'critical',
                'value': metrics.decision_quality_score,
                'threshold': min_quality,
                'timestamp': metrics.timestamp
            })

        # 存儲警報
        self.performance_alerts.extend(alerts)

        # 限制警報歷史大小
        if len(self.performance_alerts) > 100:
            self.performance_alerts = self.performance_alerts[-100:]

    def _calculate_trend(self, values: List[float]) -> str:
        """計算趨勢"""
        if len(values) < 2:
            return 'insufficient_data'

        recent_avg = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
        earlier_avg = statistics.mean(values[:-3]) if len(values) >= 6 else values[0]

        diff = recent_avg - earlier_avg
        if abs(diff) < 0.01:
            return 'stable'
        elif diff > 0:
            return 'improving'
        else:
            return 'declining'

    def _create_empty_metrics(self) -> PerformanceMetrics:
        """創建空指標"""
        return PerformanceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_seconds=0.0,
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0,
            satellites_processed=0,
            decision_quality_score=0.0,
            constraint_satisfaction_rate=0.0,
            optimization_effectiveness=0.0,
            algorithm_convergence='no_data',
            error_count=0
        )

    def _start_real_time_monitoring(self):
        """開始實時監控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._real_time_monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        self.logger.debug("🔄 實時監控已啟動")

    def _stop_real_time_monitoring(self):
        """停止實時監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)

        self.logger.debug("⏸️ 實時監控已停止")

    def _real_time_monitor_loop(self):
        """實時監控循環"""
        while self.monitoring_active:
            try:
                # 收集實時指標
                current_metrics = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'memory_usage_mb': self._get_memory_usage(),
                    'cpu_usage_percent': self._get_cpu_usage()
                }

                # 可以在這裡添加實時警報邏輯

                time.sleep(self.metric_collection_interval)

            except Exception as e:
                self.logger.error(f"❌ 實時監控錯誤: {e}")
                time.sleep(1.0)