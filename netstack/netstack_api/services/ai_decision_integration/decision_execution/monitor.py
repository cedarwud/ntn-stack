"""
決策監控器實現
==============

監控決策執行的性能、狀態和質量指標。
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from enum import Enum

from ..interfaces.decision_engine import Decision
from ..interfaces.executor import ExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警級別"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """性能指標"""

    name: str
    value: float
    timestamp: float
    unit: str
    threshold: Optional[float] = None
    is_critical: bool = False


@dataclass
class Alert:
    """告警信息"""

    alert_id: str
    level: AlertLevel
    message: str
    timestamp: float
    component: str
    details: Dict[str, Any]
    resolved: bool = False


class DecisionMonitor:
    """
    決策監控器

    提供全面的決策執行監控功能：
    - 性能指標收集
    - 實時狀態監控
    - 告警管理
    - 趨勢分析
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化決策監控器

        Args:
            config: 配置參數
        """
        self.config = config or {}
        self.logger = logger

        # 性能指標存儲
        self.performance_metrics = deque(maxlen=10000)
        self.metric_summaries = defaultdict(
            lambda: {
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
                "avg": 0.0,
                "recent_values": deque(maxlen=100),
            }
        )

        # 告警系統
        self.alerts = deque(maxlen=1000)
        self.active_alerts = {}  # alert_id -> Alert
        self.alert_rules = self._load_alert_rules()

        # 執行狀態統計
        self.execution_stats = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "failed_decisions": 0,
            "avg_decision_time": 0.0,
            "avg_execution_time": 0.0,
            "success_rate": 0.0,
        }

        # 算法性能統計
        self.algorithm_stats = defaultdict(
            lambda: {
                "decisions": 0,
                "successes": 0,
                "failures": 0,
                "avg_confidence": 0.0,
                "avg_decision_time": 0.0,
                "confidence_trend": deque(maxlen=50),
            }
        )

        # 衛星性能統計
        self.satellite_stats = defaultdict(
            lambda: {
                "selections": 0,
                "handover_successes": 0,
                "handover_failures": 0,
                "avg_signal_quality": 0.0,
                "avg_handover_time": 0.0,
            }
        )

        # 配置參數
        self.monitoring_interval = self.config.get("monitoring_interval", 10.0)  # 秒
        self.alert_cooldown = self.config.get("alert_cooldown", 300.0)  # 5分鐘
        self.metrics_retention_hours = self.config.get("metrics_retention_hours", 24)

        # 啟動監控任務
        self.monitoring_task = None
        self.is_monitoring = False

        self.logger.info(
            "決策監控器初始化完成",
            monitoring_interval=self.monitoring_interval,
            alert_rules_count=len(self.alert_rules),
        )

    async def start_monitoring(self):
        """啟動監控"""
        if self.is_monitoring:
            self.logger.warning("監控已經在運行")
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("決策監控已啟動")

    async def stop_monitoring(self):
        """停止監控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        self.logger.info("決策監控已停止")

    def record_decision(self, decision: Decision):
        """
        記錄決策信息

        Args:
            decision: 決策結果
        """
        try:
            # 更新總體統計
            self.execution_stats["total_decisions"] += 1

            # 記錄決策時間指標
            self._record_metric("decision_time", decision.decision_time, "ms")
            self._record_metric("decision_confidence", decision.confidence, "score")

            # 更新算法統計
            algorithm = decision.algorithm_used
            algo_stats = self.algorithm_stats[algorithm]
            algo_stats["decisions"] += 1

            # 更新平均置信度
            current_avg = algo_stats["avg_confidence"]
            total_decisions = algo_stats["decisions"]
            algo_stats["avg_confidence"] = (
                current_avg * (total_decisions - 1) + decision.confidence
            ) / total_decisions

            # 更新置信度趨勢
            algo_stats["confidence_trend"].append(decision.confidence)

            # 更新平均決策時間
            current_avg_time = algo_stats["avg_decision_time"]
            algo_stats["avg_decision_time"] = (
                current_avg_time * (total_decisions - 1) + decision.decision_time
            ) / total_decisions

            # 記錄衛星選擇
            satellite = decision.selected_satellite
            self.satellite_stats[satellite]["selections"] += 1

            self.logger.debug(
                "決策記錄完成",
                algorithm=algorithm,
                satellite=satellite,
                confidence=decision.confidence,
            )

        except Exception as e:
            self.logger.error("記錄決策失敗: %s", str(e))

    def record_execution_result(self, result: ExecutionResult):
        """
        記錄執行結果

        Args:
            result: 執行結果
        """
        try:
            # 記錄執行時間指標
            self._record_metric("execution_time", result.execution_time, "ms")

            # 更新成功/失敗統計
            if result.success:
                self.execution_stats["successful_decisions"] += 1

                # 更新算法成功統計
                if result.decision:
                    algorithm = result.decision.algorithm_used
                    self.algorithm_stats[algorithm]["successes"] += 1

                    # 更新衛星換手成功統計
                    satellite = result.decision.selected_satellite
                    self.satellite_stats[satellite]["handover_successes"] += 1

                    # 記錄性能指標
                    metrics = result.performance_metrics
                    for metric_name, value in metrics.items():
                        self._record_metric(
                            metric_name, value, self._get_metric_unit(metric_name)
                        )

                    # 更新衛星性能統計
                    if "signal_quality" in metrics:
                        self._update_satellite_avg(
                            satellite, "avg_signal_quality", metrics["signal_quality"]
                        )
                    if "total_handover_time" in metrics:
                        self._update_satellite_avg(
                            satellite,
                            "avg_handover_time",
                            metrics["total_handover_time"],
                        )
            else:
                self.execution_stats["failed_decisions"] += 1

                # 更新算法失敗統計
                if result.decision:
                    algorithm = result.decision.algorithm_used
                    self.algorithm_stats[algorithm]["failures"] += 1

                    # 更新衛星換手失敗統計
                    satellite = result.decision.selected_satellite
                    self.satellite_stats[satellite]["handover_failures"] += 1

                # 檢查是否需要生成告警
                self._check_failure_alerts(result)

            # 更新總體統計
            self._update_overall_stats()

            self.logger.debug(
                "執行結果記錄完成",
                success=result.success,
                execution_time=result.execution_time,
            )

        except Exception as e:
            self.logger.error("記錄執行結果失敗: %s", str(e))

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        獲取性能摘要

        Returns:
            Dict[str, Any]: 性能摘要信息
        """
        summary = {
            "execution_stats": self.execution_stats.copy(),
            "algorithm_performance": dict(self.algorithm_stats),
            "satellite_performance": dict(self.satellite_stats),
            "recent_metrics": self._get_recent_metrics(),
            "active_alerts": len(self.active_alerts),
            "monitoring_status": "active" if self.is_monitoring else "inactive",
        }

        return summary

    def get_alerts(
        self, level: Optional[AlertLevel] = None, limit: int = 100
    ) -> List[Alert]:
        """
        獲取告警列表

        Args:
            level: 告警級別過濾
            limit: 返回數量限制

        Returns:
            List[Alert]: 告警列表
        """
        alerts = list(self.alerts)

        if level:
            alerts = [alert for alert in alerts if alert.level == level]

        # 按時間倒序排列
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return alerts[:limit]

    def get_active_alerts(self) -> List[Alert]:
        """
        獲取活躍告警

        Returns:
            List[Alert]: 活躍告警列表
        """
        return list(self.active_alerts.values())

    def resolve_alert(self, alert_id: str) -> bool:
        """
        解決告警

        Args:
            alert_id: 告警ID

        Returns:
            bool: 是否成功解決
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            del self.active_alerts[alert_id]

            self.logger.info("告警已解決", alert_id=alert_id)
            return True

        return False

    def get_trend_analysis(self, metric_name: str, hours: int = 1) -> Dict[str, Any]:
        """
        獲取趨勢分析

        Args:
            metric_name: 指標名稱
            hours: 分析時間範圍(小時)

        Returns:
            Dict[str, Any]: 趨勢分析結果
        """
        cutoff_time = time.time() - (hours * 3600)

        # 過濾時間範圍內的指標
        recent_metrics = [
            m
            for m in self.performance_metrics
            if m.name == metric_name and m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {
                "error": f"No data for metric {metric_name} in the last {hours} hours"
            }

        values = [m.value for m in recent_metrics]
        timestamps = [m.timestamp for m in recent_metrics]

        # 計算趨勢統計
        trend_analysis = {
            "metric_name": metric_name,
            "time_range_hours": hours,
            "data_points": len(values),
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values),
            "latest_value": values[-1] if values else 0,
            "trend_direction": self._calculate_trend_direction(values),
            "change_rate": self._calculate_change_rate(values),
            "timestamps": timestamps[-50:],  # 最近50個數據點
            "values": values[-50:],
        }

        return trend_analysis

    # 私有方法實現
    def _record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        threshold: Optional[float] = None,
        is_critical: bool = False,
    ):
        """記錄性能指標"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            unit=unit,
            threshold=threshold,
            is_critical=is_critical,
        )

        self.performance_metrics.append(metric)

        # 更新摘要統計
        summary = self.metric_summaries[name]
        summary["count"] += 1
        summary["sum"] += value
        summary["min"] = min(summary["min"], value)
        summary["max"] = max(summary["max"], value)
        summary["avg"] = summary["sum"] / summary["count"]
        summary["recent_values"].append(value)

        # 檢查告警
        self._check_metric_alerts(metric)

    def _update_overall_stats(self):
        """更新總體統計"""
        total = self.execution_stats["total_decisions"]
        if total > 0:
            self.execution_stats["success_rate"] = (
                self.execution_stats["successful_decisions"] / total
            )

        # 更新平均執行時間
        if "execution_time" in self.metric_summaries:
            self.execution_stats["avg_execution_time"] = self.metric_summaries[
                "execution_time"
            ]["avg"]

        # 更新平均決策時間
        if "decision_time" in self.metric_summaries:
            self.execution_stats["avg_decision_time"] = self.metric_summaries[
                "decision_time"
            ]["avg"]

    def _update_satellite_avg(
        self, satellite_id: str, stat_name: str, new_value: float
    ):
        """更新衛星平均值統計"""
        stats = self.satellite_stats[satellite_id]

        if stat_name not in stats:
            stats[stat_name] = 0.0
            stats[f"{stat_name}_count"] = 0

        count_key = f"{stat_name}_count"
        current_count = stats.get(count_key, 0)
        current_avg = stats[stat_name]

        stats[count_key] = current_count + 1
        stats[stat_name] = (current_avg * current_count + new_value) / stats[count_key]

    def _get_recent_metrics(self, minutes: int = 10) -> Dict[str, List[float]]:
        """獲取最近的指標數據"""
        cutoff_time = time.time() - (minutes * 60)

        recent_metrics = defaultdict(list)
        for metric in self.performance_metrics:
            if metric.timestamp >= cutoff_time:
                recent_metrics[metric.name].append(metric.value)

        return dict(recent_metrics)

    def _get_metric_unit(self, metric_name: str) -> str:
        """獲取指標單位"""
        unit_map = {
            "decision_time": "ms",
            "execution_time": "ms",
            "confidence": "score",
            "signal_quality": "score",
            "latency": "ms",
            "throughput": "mbps",
            "packet_loss_rate": "rate",
            "handover_success_rate": "rate",
        }
        return unit_map.get(metric_name, "unknown")

    def _load_alert_rules(self) -> List[Dict[str, Any]]:
        """載入告警規則"""
        default_rules = [
            {
                "name": "high_execution_time",
                "metric": "execution_time",
                "threshold": 10000.0,  # 10秒
                "operator": ">",
                "level": AlertLevel.WARNING,
                "message": "執行時間過長",
            },
            {
                "name": "low_success_rate",
                "metric": "success_rate",
                "threshold": 0.8,
                "operator": "<",
                "level": AlertLevel.ERROR,
                "message": "成功率過低",
            },
            {
                "name": "low_confidence",
                "metric": "decision_confidence",
                "threshold": 0.5,
                "operator": "<",
                "level": AlertLevel.WARNING,
                "message": "決策置信度過低",
            },
        ]

        return default_rules

    def _check_metric_alerts(self, metric: PerformanceMetric):
        """檢查指標告警"""
        for rule in self.alert_rules:
            if rule["metric"] == metric.name:
                if self._evaluate_alert_condition(metric.value, rule):
                    self._create_alert(rule, metric)

    def _check_failure_alerts(self, result: ExecutionResult):
        """檢查執行失敗告警"""
        if not result.success:
            alert_id = f"execution_failure_{result.execution_id}"

            alert = Alert(
                alert_id=alert_id,
                level=AlertLevel.ERROR,
                message=f"執行失敗: {result.error_message}",
                timestamp=time.time(),
                component="execution",
                details={
                    "execution_id": result.execution_id,
                    "error_message": result.error_message,
                    "execution_time": result.execution_time,
                },
            )

            self._add_alert(alert)

    def _evaluate_alert_condition(self, value: float, rule: Dict[str, Any]) -> bool:
        """評估告警條件"""
        threshold = rule["threshold"]
        operator = rule["operator"]

        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.001

        return False

    def _create_alert(self, rule: Dict[str, Any], metric: PerformanceMetric):
        """創建告警"""
        alert_id = f"{rule['name']}_{int(time.time())}"

        alert = Alert(
            alert_id=alert_id,
            level=rule["level"],
            message=f"{rule['message']}: {metric.value} {metric.unit}",
            timestamp=metric.timestamp,
            component="monitoring",
            details={
                "metric_name": metric.name,
                "metric_value": metric.value,
                "threshold": rule["threshold"],
                "rule_name": rule["name"],
            },
        )

        self._add_alert(alert)

    def _add_alert(self, alert: Alert):
        """添加告警"""
        self.alerts.append(alert)

        if not alert.resolved:
            self.active_alerts[alert.alert_id] = alert

        self.logger.warning(
            "生成告警: %s - %s - %s",
            alert.alert_id,
            alert.level.value,
            alert.message,
        )

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """計算趨勢方向"""
        if len(values) < 2:
            return "unknown"

        # 簡單的線性趨勢計算
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if second_avg > first_avg * 1.05:
            return "increasing"
        elif second_avg < first_avg * 0.95:
            return "decreasing"
        else:
            return "stable"

    def _calculate_change_rate(self, values: List[float]) -> float:
        """計算變化率"""
        if len(values) < 2:
            return 0.0

        first_value = values[0]
        last_value = values[-1]

        if first_value == 0:
            return 0.0

        return ((last_value - first_value) / first_value) * 100.0

    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                await self._perform_monitoring_checks()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("監控循環異常: %s", str(e))
                await asyncio.sleep(self.monitoring_interval)

    async def _perform_monitoring_checks(self):
        """執行監控檢查"""
        # 清理過期指標
        self._cleanup_old_metrics()

        # 檢查總體健康狀態
        self._check_system_health()

        # 清理已解決的告警
        self._cleanup_resolved_alerts()

    def _cleanup_old_metrics(self):
        """清理過期指標"""
        cutoff_time = time.time() - (self.metrics_retention_hours * 3600)

        # 移除過期指標
        while (
            self.performance_metrics
            and self.performance_metrics[0].timestamp < cutoff_time
        ):
            self.performance_metrics.popleft()

    def _check_system_health(self):
        """檢查系統健康狀態"""
        # 檢查成功率
        success_rate = self.execution_stats.get("success_rate", 1.0)
        if success_rate < 0.8:
            self._create_system_alert(
                "system_health_warning",
                AlertLevel.WARNING,
                f"系統成功率過低: {success_rate:.2%}",
            )

    def _create_system_alert(self, alert_type: str, level: AlertLevel, message: str):
        """創建系統告警"""
        alert_id = f"{alert_type}_{int(time.time())}"

        alert = Alert(
            alert_id=alert_id,
            level=level,
            message=message,
            timestamp=time.time(),
            component="system",
            details={"alert_type": alert_type},
        )

        self._add_alert(alert)

    def _cleanup_resolved_alerts(self):
        """清理已解決的告警"""
        # 清理過期的活躍告警
        current_time = time.time()
        expired_alerts = [
            alert_id
            for alert_id, alert in self.active_alerts.items()
            if current_time - alert.timestamp > self.alert_cooldown
        ]

        for alert_id in expired_alerts:
            self.resolve_alert(alert_id)
