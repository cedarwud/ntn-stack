"""
監控基類

提供所有監控功能的基礎類和共用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging


@dataclass
class MonitoringMetric:
    """監控指標數據結構"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


@dataclass
class AlertInfo:
    """告警信息"""
    alert_id: str
    level: str  # WARNING, CRITICAL
    metric: MonitoringMetric
    message: str
    timestamp: datetime
    resolved: bool = False


@dataclass
class MetricsSummary:
    """指標摘要"""
    time_range: timedelta
    total_metrics: int
    metrics_by_type: Dict[str, int]
    average_values: Dict[str, float]
    alerts_triggered: int


@dataclass
class MonitoringConfig:
    """監控配置"""
    monitor_name: str
    collection_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    alert_enabled: bool = True
    max_history_size: int = 1000
    export_format: str = "json"


class BaseMonitor(ABC):
    """監控基類"""

    def __init__(self, monitor_name: str, config: MonitoringConfig):
        self.monitor_name = monitor_name
        self.config = config
        self.metrics_history: List[MonitoringMetric] = []
        self.alerts: List[AlertInfo] = []
        self.logger = logging.getLogger(f"monitor.{monitor_name}")

    @abstractmethod
    def collect_metrics(self) -> List[MonitoringMetric]:
        """收集監控指標"""
        pass

    def add_metric(self, metric: MonitoringMetric):
        """添加監控指標"""
        self.metrics_history.append(metric)

        # 保持歷史記錄大小限制
        if len(self.metrics_history) > self.config.max_history_size:
            self.metrics_history = self.metrics_history[-self.config.max_history_size:]

        # 檢查閾值
        if self.config.alert_enabled:
            self._check_thresholds(metric)

    def _check_thresholds(self, metric: MonitoringMetric):
        """檢查閾值並觸發告警"""
        if metric.threshold_critical and metric.value >= metric.threshold_critical:
            self._trigger_alert("CRITICAL", metric)
        elif metric.threshold_warning and metric.value >= metric.threshold_warning:
            self._trigger_alert("WARNING", metric)

    def _trigger_alert(self, level: str, metric: MonitoringMetric):
        """觸發告警"""
        alert = AlertInfo(
            alert_id=f"{self.monitor_name}_{metric.metric_name}_{datetime.now().timestamp()}",
            level=level,
            metric=metric,
            message=f"{level}: {metric.metric_name} = {metric.value} {metric.unit}",
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        self.logger.warning(f"Alert triggered: {alert.message}")

    def get_metrics_summary(self, time_range: timedelta) -> MetricsSummary:
        """獲取指標摘要"""
        cutoff_time = datetime.now() - time_range
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        # 按類型分組
        metrics_by_type = {}
        average_values = {}
        for metric in recent_metrics:
            if metric.metric_name not in metrics_by_type:
                metrics_by_type[metric.metric_name] = 0
                average_values[metric.metric_name] = 0

            metrics_by_type[metric.metric_name] += 1
            average_values[metric.metric_name] += metric.value

        # 計算平均值
        for metric_name in average_values:
            if metrics_by_type[metric_name] > 0:
                average_values[metric_name] /= metrics_by_type[metric_name]

        # 計算告警數量
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]

        return MetricsSummary(
            time_range=time_range,
            total_metrics=len(recent_metrics),
            metrics_by_type=metrics_by_type,
            average_values=average_values,
            alerts_triggered=len(recent_alerts)
        )

    def export_metrics(self, format_type: str = "json") -> str:
        """導出監控指標"""
        if format_type == "json":
            import json
            data = {
                "monitor_name": self.monitor_name,
                "export_timestamp": datetime.now().isoformat(),
                "metrics": [
                    {
                        "name": m.metric_name,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags
                    }
                    for m in self.metrics_history
                ],
                "alerts": [
                    {
                        "id": a.alert_id,
                        "level": a.level,
                        "message": a.message,
                        "timestamp": a.timestamp.isoformat(),
                        "resolved": a.resolved
                    }
                    for a in self.alerts
                ]
            }
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def get_active_alerts(self) -> List[AlertInfo]:
        """獲取未解決的告警"""
        return [alert for alert in self.alerts if not alert.resolved]

    def resolve_alert(self, alert_id: str):
        """解決告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.logger.info(f"Alert resolved: {alert_id}")
                break

    def clear_history(self):
        """清空歷史記錄"""
        self.metrics_history.clear()
        self.alerts.clear()
        self.logger.info(f"History cleared for monitor: {self.monitor_name}")