"""
性能指標收集器
==============

收集和監控決策引擎的性能指標，支持 Prometheus 格式輸出。
"""

import time
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MetricPoint:
    """指標數據點"""

    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class MetricsCollector:
    """
    性能指標收集器主類

    收集決策引擎的各種性能指標：
    - 決策延遲
    - 成功率
    - 錯誤統計
    - 吞吐量
    - 資源使用率
    """

    def __init__(self, max_history: int = 10000):
        """
        初始化指標收集器

        Args:
            max_history: 最大歷史記錄數
        """
        self.max_history = max_history

        # 指標存儲
        self._decision_latencies: deque = deque(maxlen=max_history)
        self._decision_successes: deque = deque(maxlen=max_history)
        self._decision_errors: deque = deque(maxlen=max_history)
        self._throughput_data: deque = deque(maxlen=max_history)

        # 擴充指標，用於前端圖表
        self._policy_losses: deque = deque(maxlen=max_history)
        self._handover_delays: deque = deque(maxlen=max_history)
        self._signal_drop_times: deque = deque(maxlen=max_history)
        self._energy_efficiencies: deque = deque(maxlen=max_history)

        # 累計統計
        self._total_decisions = 0
        self._total_successes = 0
        self._total_errors = 0
        self._total_latency = 0.0

        # 錯誤分類統計
        self._error_categories: defaultdict = defaultdict(int)

        # 算法性能統計
        self._algorithm_stats: defaultdict = defaultdict(
            lambda: {"count": 0, "success": 0, "avg_latency": 0.0, "total_latency": 0.0}
        )

        # 時間窗口統計 (最近1分鐘, 5分鐘, 15分鐘)
        self._time_windows = {
            "1m": deque(maxlen=60),  # 1分鐘，每秒一個點
            "5m": deque(maxlen=300),  # 5分鐘，每秒一個點
            "15m": deque(maxlen=900),  # 15分鐘，每秒一個點
        }

        self._start_time = time.time()

        logger.info("Metrics collector initialized", max_history=max_history)

    def record_decision_latency(
        self, latency: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        記錄決策延遲

        Args:
            latency: 延遲時間 (秒)
            labels: 額外標籤
        """
        timestamp = time.time()
        point = MetricPoint(timestamp, latency * 1000, labels or {})  # 轉換為毫秒

        self._decision_latencies.append(point)
        self._total_latency += latency

        # 更新時間窗口統計
        self._update_time_windows("latency", point)

        logger.debug(
            "Decision latency recorded", latency_ms=latency * 1000, labels=labels
        )

    def record_decision_success(
        self,
        success: bool,
        algorithm: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        記錄決策成功/失敗

        Args:
            success: 是否成功
            algorithm: 使用的算法
            labels: 額外標籤
        """
        timestamp = time.time()
        point = MetricPoint(timestamp, 1.0 if success else 0.0, labels or {})

        self._decision_successes.append(point)
        self._total_decisions += 1

        if success:
            self._total_successes += 1

        # 更新算法統計
        if algorithm:
            stats = self._algorithm_stats[algorithm]
            stats["count"] += 1
            if success:
                stats["success"] += 1

        # 更新時間窗口統計
        self._update_time_windows("success", point)

        logger.debug(
            "Decision result recorded",
            success=success,
            algorithm=algorithm,
            labels=labels,
        )

    def record_decision_error(
        self,
        error: str,
        error_category: str = "general",
        algorithm: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        記錄決策錯誤

        Args:
            error: 錯誤訊息
            error_category: 錯誤分類
            algorithm: 使用的算法
            labels: 額外標籤
        """
        timestamp = time.time()
        point = MetricPoint(timestamp, 1.0, labels or {})

        self._decision_errors.append(point)
        self._total_errors += 1
        self._error_categories[error_category] += 1

        # 更新時間窗口統計
        self._update_time_windows("error", point)

        logger.warning(
            "Decision error recorded",
            error=error,
            category=error_category,
            algorithm=algorithm,
            labels=labels,
        )

    def record_throughput(
        self, requests_per_second: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        記錄吞吐量

        Args:
            requests_per_second: 每秒請求數
            labels: 額外標籤
        """
        timestamp = time.time()
        point = MetricPoint(timestamp, requests_per_second, labels or {})

        self._throughput_data.append(point)

        # 更新時間窗口統計
        self._update_time_windows("throughput", point)

        logger.debug("Throughput recorded", rps=requests_per_second, labels=labels)

    def record_handover_details(
        self, details: Dict[str, Any], labels: Optional[Dict[str, str]] = None
    ):
        """
        記錄與一次成功換手相關的詳細性能指標。

        Args:
            details: 包含詳細指標的字典，例如:
                     {
                         "policy_loss": 0.1,
                         "handover_delay": 25.5,
                         "signal_drop_time": 10.2,
                         "energy_efficiency": 0.95
                     }
            labels: 額外標籤
        """
        timestamp = time.time()
        current_labels = labels or {}

        if "policy_loss" in details:
            self._policy_losses.append(
                MetricPoint(timestamp, details["policy_loss"], current_labels)
            )
        if "handover_delay" in details:
            self._handover_delays.append(
                MetricPoint(timestamp, details["handover_delay"], current_labels)
            )
        if "signal_drop_time" in details:
            self._signal_drop_times.append(
                MetricPoint(timestamp, details["signal_drop_time"], current_labels)
            )
        if "energy_efficiency" in details:
            self._energy_efficiencies.append(
                MetricPoint(timestamp, details["energy_efficiency"], current_labels)
            )

        logger.debug(
            "Handover details recorded", details=details, labels=current_labels
        )

    def record_algorithm_latency(self, algorithm: str, latency: float):
        """
        記錄算法延遲

        Args:
            algorithm: 算法名稱
            latency: 延遲時間 (秒)
        """
        stats = self._algorithm_stats[algorithm]
        stats["total_latency"] += latency
        if stats["count"] > 0:
            stats["avg_latency"] = stats["total_latency"] / stats["count"]

    def _update_time_windows(self, metric_type: str, point: MetricPoint):
        """更新時間窗口統計"""
        for window_name, window_data in self._time_windows.items():
            window_data.append(
                {
                    "timestamp": point.timestamp,
                    "metric_type": metric_type,
                    "value": point.value,
                    "labels": point.labels,
                }
            )

    def get_summary(self) -> Dict[str, Any]:
        """
        獲取指標摘要

        Returns:
            Dict[str, Any]: 指標摘要數據
        """
        current_time = time.time()
        uptime = current_time - self._start_time

        # 計算平均延遲
        avg_latency = (
            self._total_latency / self._total_decisions
            if self._total_decisions > 0
            else 0
        )

        # 計算成功率
        success_rate = (
            self._total_successes / self._total_decisions
            if self._total_decisions > 0
            else 0
        )

        # 計算錯誤率
        error_rate = (
            self._total_errors / self._total_decisions
            if self._total_decisions > 0
            else 0
        )

        return {
            "uptime_seconds": uptime,
            "total_decisions": self._total_decisions,
            "total_successes": self._total_successes,
            "total_errors": self._total_errors,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_latency_ms": avg_latency * 1000,
            "throughput_rps": (
                self._throughput_data[-1].value if self._throughput_data else 0
            ),
            "error_categories": dict(self._error_categories),
            "algorithm_stats": dict(self._algorithm_stats),
            "detailed_handover_metrics": {
                "avg_policy_loss": self._calculate_avg(self._policy_losses),
                "avg_handover_delay_ms": self._calculate_avg(self._handover_delays),
                "avg_signal_drop_time_ms": self._calculate_avg(self._signal_drop_times),
                "avg_energy_efficiency": self._calculate_avg(self._energy_efficiencies),
            },
            "time_window_stats": self._get_time_window_stats(),
        }

    def _get_time_window_stats(self) -> Dict[str, Any]:
        """獲取各時間窗口的統計數據"""
        window_stats = {}
        current_time = time.time()

        for window_name, window_data in self._time_windows.items():
            window_duration = {"1m": 60, "5m": 300, "15m": 900}[window_name]
            cutoff_time = current_time - window_duration

            # 過濾時間窗口內的數據
            recent_data = [d for d in window_data if d["timestamp"] >= cutoff_time]

            # 計算統計
            latency_data = [
                d["value"] for d in recent_data if d["metric_type"] == "latency"
            ]
            success_data = [
                d["value"] for d in recent_data if d["metric_type"] == "success"
            ]
            error_data = [
                d["value"] for d in recent_data if d["metric_type"] == "error"
            ]

            window_stats[f"total_requests_{window_name}"] = len(recent_data)
            window_stats[f"avg_latency_ms_{window_name}"] = (
                sum(latency_data) / len(latency_data) if latency_data else 0
            )
            window_stats[f"success_rate_{window_name}"] = (
                sum(success_data) / len(success_data) if success_data else 0
            )
            window_stats[f"error_count_{window_name}"] = len(error_data)
            window_stats[f"requests_per_second_{window_name}"] = (
                len(recent_data) / window_duration if recent_data else 0
            )
            window_stats[f"errors_{window_name}"] = len(error_data)

        return window_stats

    def _calculate_avg(self, deq: deque) -> Optional[float]:
        """計算 deque 中 MetricPoint 的平均值"""
        if not deq:
            return None
        return sum(p.value for p in deq) / len(deq)

    def get_prometheus_metrics(self) -> str:
        """
        生成 Prometheus 格式的指標

        Returns:
            str: Prometheus 格式的指標字符串
        """
        metrics = []

        # 基本計數器
        metrics.append(f"ntn_decisions_total {self._total_decisions}")
        metrics.append(f"ntn_decisions_success_total {self._total_successes}")
        metrics.append(f"ntn_decisions_error_total {self._total_errors}")

        # 平均延遲
        avg_latency = (
            self._total_latency / self._total_decisions
            if self._total_decisions > 0
            else 0
        )
        metrics.append(f"ntn_decision_latency_avg_seconds {avg_latency}")

        # 成功率
        success_rate = (
            self._total_successes / self._total_decisions
            if self._total_decisions > 0
            else 0
        )
        metrics.append(f"ntn_decision_success_rate {success_rate}")

        # 錯誤分類統計
        for category, count in self._error_categories.items():
            metrics.append(
                f'ntn_decision_errors_by_category{{category="{category}"}} {count}'
            )

        # 算法統計
        for algorithm, stats in self._algorithm_stats.items():
            metrics.append(
                f'ntn_algorithm_decisions_total{{algorithm="{algorithm}"}} {stats["count"]}'
            )
            metrics.append(
                f'ntn_algorithm_success_total{{algorithm="{algorithm}"}} {stats["success"]}'
            )
            metrics.append(
                f'ntn_algorithm_latency_avg_seconds{{algorithm="{algorithm}"}} {stats["avg_latency"]}'
            )

        return "\n".join(metrics)

    def get_recent_latencies(self, window_seconds: int = 300) -> List[float]:
        """
        獲取最近的延遲數據

        Args:
            window_seconds: 時間窗口 (秒)

        Returns:
            List[float]: 延遲數據列表 (毫秒)
        """
        cutoff_time = time.time() - window_seconds
        return [
            point.value
            for point in self._decision_latencies
            if point.timestamp >= cutoff_time
        ]

    def reset_metrics(self):
        """重置所有指標"""
        self._decision_latencies.clear()
        self._decision_successes.clear()
        self._decision_errors.clear()
        self._throughput_data.clear()

        self._total_decisions = 0
        self._total_successes = 0
        self._total_errors = 0
        self._total_latency = 0.0

        self._error_categories.clear()
        self._algorithm_stats.clear()

        for window_data in self._time_windows.values():
            window_data.clear()

        self._start_time = time.time()

        logger.info("Metrics reset")
