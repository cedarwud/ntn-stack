#!/usr/bin/env python3
"""
即時性能監控和告警系統
實現階段七要求的即時性能監控、告警和自動響應機制

功能：
1. 即時性能監控
2. 智能告警系統
3. 告警規則引擎
4. 自動響應機制
5. 告警聚合和去重
6. 告警升級策略
7. 性能異常檢測
8. 監控儀表板數據源
"""

import asyncio
import time
import statistics
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog
import aiohttp
import numpy as np
from collections import defaultdict, deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .unified_metrics_collector import UnifiedMetricsCollector, MetricValue
from .enhanced_performance_optimizer import EnhancedPerformanceOptimizer

logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """告警嚴重級別"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(Enum):
    """告警狀態"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class MonitoringStatus(Enum):
    """監控狀態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class AlertRule:
    """告警規則"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    severity: AlertSeverity
    duration_seconds: int = 60  # 持續時間閾值
    evaluation_interval: int = 30  # 評估間隔(秒)
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)
    suppression_rules: List[str] = field(default_factory=list)


@dataclass
class Alert:
    """告警"""
    alert_id: str
    rule_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus
    message: str
    timestamp: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringDashboard:
    """監控儀表板數據"""
    timestamp: datetime
    overall_status: MonitoringStatus
    active_alerts_count: int
    critical_alerts_count: int
    high_alerts_count: int
    services_status: Dict[str, MonitoringStatus]
    key_metrics: Dict[str, float]
    performance_trends: Dict[str, List[float]]
    system_health_score: float


class AnomalyDetector:
    """異常檢測器"""
    
    def __init__(self):
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.baseline_stats: Dict[str, Dict[str, float]] = {}
        
    def add_metric_value(self, metric_name: str, value: float, timestamp: float):
        """添加指標值"""
        self.metric_history[metric_name].append((timestamp, value))
        
        # 更新基線統計
        if len(self.metric_history[metric_name]) >= 10:
            values = [v for _, v in self.metric_history[metric_name]]
            self.baseline_stats[metric_name] = {
                'mean': statistics.mean(values),
                'std': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
                'median': statistics.median(values)
            }
    
    def detect_anomaly(self, metric_name: str, value: float) -> Dict[str, Any]:
        """檢測異常"""
        if metric_name not in self.baseline_stats:
            return {"is_anomaly": False, "confidence": 0.0, "reason": "insufficient_data"}
        
        stats = self.baseline_stats[metric_name]
        
        # Z-score 異常檢測
        if stats['std'] > 0:
            z_score = abs(value - stats['mean']) / stats['std']
            is_anomaly = z_score > 3.0  # 3-sigma規則
            confidence = min(z_score / 3.0, 1.0)
        else:
            z_score = 0
            is_anomaly = False
            confidence = 0.0
        
        # 範圍異常檢測
        iqr_factor = 1.5
        q1_approx = stats['mean'] - 0.675 * stats['std']
        q3_approx = stats['mean'] + 0.675 * stats['std']
        iqr = q3_approx - q1_approx
        lower_bound = q1_approx - iqr_factor * iqr
        upper_bound = q3_approx + iqr_factor * iqr
        
        range_anomaly = value < lower_bound or value > upper_bound
        
        final_anomaly = is_anomaly or range_anomaly
        reason = []
        if z_score > 3.0:
            reason.append(f"z_score_{z_score:.2f}")
        if range_anomaly:
            reason.append("out_of_range")
        
        return {
            "is_anomaly": final_anomaly,
            "confidence": confidence,
            "z_score": z_score,
            "reason": "_".join(reason) if reason else "normal",
            "baseline_mean": stats['mean'],
            "baseline_std": stats['std']
        }


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.rule_states: Dict[str, Dict] = {}  # 規則狀態追踪
        self.notification_channels: List[Callable] = []
        self.suppression_groups: Dict[str, List[str]] = {}
        
    def add_rule(self, rule: AlertRule):
        """添加告警規則"""
        self.rules[rule.rule_id] = rule
        self.rule_states[rule.rule_id] = {
            'last_evaluation': 0,
            'trigger_start': None,
            'consecutive_violations': 0
        }
        logger.info(f"添加告警規則: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """移除告警規則"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            if rule_id in self.rule_states:
                del self.rule_states[rule_id]
            logger.info(f"移除告警規則: {rule_id}")
    
    def evaluate_rules(self, metrics: List[MetricValue]) -> List[Alert]:
        """評估告警規則"""
        new_alerts = []
        current_time = time.time()
        
        # 按指標名稱組織指標值
        metrics_by_name = defaultdict(list)
        for metric in metrics:
            metrics_by_name[metric.metric_name].append(metric)
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
                
            # 檢查評估間隔
            state = self.rule_states[rule_id]
            if current_time - state['last_evaluation'] < rule.evaluation_interval:
                continue
                
            state['last_evaluation'] = current_time
            
            # 獲取相關指標
            relevant_metrics = metrics_by_name.get(rule.metric_name, [])
            if not relevant_metrics:
                continue
            
            # 使用最新值進行評估
            latest_metric = max(relevant_metrics, key=lambda m: m.timestamp)
            current_value = latest_metric.value
            
            # 評估條件
            violation = self._evaluate_condition(current_value, rule.condition, rule.threshold)
            
            if violation:
                state['consecutive_violations'] += 1
                if state['trigger_start'] is None:
                    state['trigger_start'] = current_time
                
                # 檢查持續時間
                if current_time - state['trigger_start'] >= rule.duration_seconds:
                    # 生成告警
                    alert = self._create_alert(rule, latest_metric, current_value)
                    if alert and not self._is_suppressed(alert):
                        new_alerts.append(alert)
                        self.active_alerts[alert.alert_id] = alert
                        
            else:
                # 重置狀態
                state['consecutive_violations'] = 0
                state['trigger_start'] = None
                
                # 解決相關的活躍告警
                self._resolve_alerts_for_rule(rule_id)
        
        return new_alerts
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """評估條件"""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return abs(value - threshold) < 0.001
        elif condition == "!=":
            return abs(value - threshold) >= 0.001
        else:
            return False
    
    def _create_alert(self, rule: AlertRule, metric: MetricValue, current_value: float) -> Optional[Alert]:
        """創建告警"""
        alert_id = f"{rule.rule_id}_{int(time.time())}"
        
        # 檢查是否已存在相同告警
        for alert in self.active_alerts.values():
            if (alert.rule_id == rule.rule_id and 
                alert.metric_name == rule.metric_name and
                alert.status == AlertStatus.ACTIVE):
                return None  # 避免重複告警
        
        message = (f"{rule.name}: {rule.metric_name} is {current_value:.2f} "
                  f"(threshold: {rule.condition} {rule.threshold})")
        
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=message,
            timestamp=datetime.now(),
            labels=metric.labels.copy(),
            annotations={
                "rule_name": rule.name,
                "description": rule.description,
                "source_service": metric.source_service
            }
        )
        
        return alert
    
    def _is_suppressed(self, alert: Alert) -> bool:
        """檢查告警是否被抑制"""
        rule = self.rules.get(alert.rule_id)
        if not rule or not rule.suppression_rules:
            return False
        
        # 檢查抑制規則
        for suppression_rule in rule.suppression_rules:
            if self._check_suppression_condition(alert, suppression_rule):
                return True
        
        return False
    
    def _check_suppression_condition(self, alert: Alert, suppression_rule: str) -> bool:
        """檢查抑制條件"""
        # 簡單的抑制邏輯，可以根據需要擴展
        if suppression_rule.startswith("higher_severity_exists"):
            higher_severities = []
            if alert.severity == AlertSeverity.HIGH:
                higher_severities = [AlertSeverity.CRITICAL]
            elif alert.severity == AlertSeverity.MEDIUM:
                higher_severities = [AlertSeverity.CRITICAL, AlertSeverity.HIGH]
            elif alert.severity == AlertSeverity.LOW:
                higher_severities = [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM]
            
            for active_alert in self.active_alerts.values():
                if (active_alert.severity in higher_severities and 
                    active_alert.status == AlertStatus.ACTIVE):
                    return True
        
        return False
    
    def _resolve_alerts_for_rule(self, rule_id: str):
        """解決規則相關的告警"""
        current_time = datetime.now()
        for alert in list(self.active_alerts.values()):
            if alert.rule_id == rule_id and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = current_time
                self.alert_history.append(alert)
                del self.active_alerts[alert.alert_id]
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """確認告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            logger.info(f"告警已確認: {alert_id} by {acknowledged_by}")
    
    def resolve_alert(self, alert_id: str):
        """手動解決告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            self.alert_history.append(alert)
            del self.active_alerts[alert_id]
            logger.info(f"告警已解決: {alert_id}")
    
    def add_notification_channel(self, channel: Callable):
        """添加通知渠道"""
        self.notification_channels.append(channel)
    
    async def send_notifications(self, alerts: List[Alert]):
        """發送通知"""
        for alert in alerts:
            for channel in self.notification_channels:
                try:
                    await channel(alert)
                except Exception as e:
                    logger.error(f"發送通知失敗: {e}")


class RealTimeMonitoringAlerting:
    """即時性能監控和告警系統"""
    
    def __init__(self, metrics_collector: UnifiedMetricsCollector, 
                 performance_optimizer: EnhancedPerformanceOptimizer):
        self.logger = structlog.get_logger(__name__)
        
        # 依賴服務
        self.metrics_collector = metrics_collector
        self.performance_optimizer = performance_optimizer
        
        # 核心組件
        self.alert_manager = AlertManager()
        self.anomaly_detector = AnomalyDetector()
        
        # 監控狀態
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # 監控配置
        self.monitoring_interval = 10.0  # 10秒監控間隔
        self.dashboard_update_interval = 30.0  # 30秒儀表板更新間隔
        
        # 性能數據
        self.recent_metrics: deque = deque(maxlen=1000)
        self.dashboard_data: Optional[MonitoringDashboard] = None
        
        # 自動響應開關
        self.auto_response_enabled = True
        
        # 統計信息
        self.monitoring_stats = {
            "total_evaluations": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0,
            "anomalies_detected": 0,
            "auto_responses_triggered": 0
        }
        
        # 初始化預設告警規則
        self._initialize_default_rules()
        
        # 初始化通知渠道
        self._initialize_notification_channels()
    
    def _initialize_default_rules(self):
        """初始化預設告警規則"""
        default_rules = [
            AlertRule(
                rule_id="e2e_latency_critical",
                name="E2E延遲臨界告警",
                description="端到端延遲超過臨界閾值",
                metric_name="ntn_kpi_e2e_latency_ms",
                condition=">",
                threshold=100.0,
                severity=AlertSeverity.CRITICAL,
                duration_seconds=30
            ),
            AlertRule(
                rule_id="e2e_latency_high",
                name="E2E延遲高告警",
                description="端到端延遲超過目標值",
                metric_name="ntn_kpi_e2e_latency_ms",
                condition=">",
                threshold=50.0,
                severity=AlertSeverity.HIGH,
                duration_seconds=60
            ),
            AlertRule(
                rule_id="transmission_rate_low",
                name="傳輸速率低告警",
                description="傳輸速率低於目標值",
                metric_name="ntn_kpi_transmission_rate_mbps",
                condition="<",
                threshold=65.0,
                severity=AlertSeverity.MEDIUM,
                duration_seconds=90
            ),
            AlertRule(
                rule_id="coverage_low",
                name="覆蓋率低告警",
                description="系統覆蓋率低於目標值",
                metric_name="ntn_kpi_coverage_percent",
                condition="<",
                threshold=75.0,
                severity=AlertSeverity.HIGH,
                duration_seconds=120
            ),
            AlertRule(
                rule_id="cpu_utilization_high",
                name="CPU使用率高告警",
                description="CPU使用率過高",
                metric_name="system_resource_cpu_usage_percent",
                condition=">",
                threshold=90.0,
                severity=AlertSeverity.HIGH,
                duration_seconds=60
            ),
            AlertRule(
                rule_id="memory_utilization_critical",
                name="記憶體使用率臨界告警",
                description="記憶體使用率臨界",
                metric_name="system_resource_memory_usage_mb",
                condition=">",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration_seconds=30
            ),
            AlertRule(
                rule_id="handover_success_rate_low",
                name="換手成功率低告警",
                description="衛星換手成功率過低",
                metric_name="ntn_kpi_handover_success_rate_percent",
                condition="<",
                threshold=95.0,
                severity=AlertSeverity.HIGH,
                duration_seconds=120
            ),
            AlertRule(
                rule_id="ai_interference_detection_low",
                name="AI干擾檢測準確率低告警",
                description="AI干擾檢測準確率過低",
                metric_name="ntn_kpi_ai_interference_detection_accuracy_percent",
                condition="<",
                threshold=85.0,
                severity=AlertSeverity.MEDIUM,
                duration_seconds=300
            )
        ]
        
        for rule in default_rules:
            self.alert_manager.add_rule(rule)
    
    def _initialize_notification_channels(self):
        """初始化通知渠道"""
        # 添加日誌通知渠道
        self.alert_manager.add_notification_channel(self._log_notification)
        
        # 可以添加其他通知渠道如email、webhook等
        # self.alert_manager.add_notification_channel(self._email_notification)
        # self.alert_manager.add_notification_channel(self._webhook_notification)
    
    async def _log_notification(self, alert: Alert):
        """日誌通知渠道"""
        self.logger.warn(
            f"🚨 告警觸發: {alert.message}",
            alert_id=alert.alert_id,
            severity=alert.severity.value,
            metric=alert.metric_name,
            value=alert.current_value,
            threshold=alert.threshold
        )
    
    async def start_monitoring(self):
        """啟動即時監控"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("即時性能監控已啟動")
    
    async def stop_monitoring(self):
        """停止即時監控"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("即時性能監控已停止")
    
    async def _monitoring_loop(self):
        """監控主循環"""
        last_dashboard_update = 0
        
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # 收集指標
                await self._collect_and_process_metrics()
                
                # 更新儀表板數據
                current_time = time.time()
                if current_time - last_dashboard_update >= self.dashboard_update_interval:
                    await self._update_dashboard_data()
                    last_dashboard_update = current_time
                
                # 統計更新
                self.monitoring_stats["total_evaluations"] += 1
                
                # 等待下次監控
                elapsed = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"監控循環異常: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_and_process_metrics(self):
        """收集和處理指標"""
        try:
            # 從統一指標收集器獲取最新指標
            latest_metrics = await self._get_latest_metrics()
            
            if not latest_metrics:
                return
            
            # 添加到歷史數據
            self.recent_metrics.extend(latest_metrics)
            
            # 異常檢測
            await self._perform_anomaly_detection(latest_metrics)
            
            # 評估告警規則
            new_alerts = self.alert_manager.evaluate_rules(latest_metrics)
            
            if new_alerts:
                self.monitoring_stats["alerts_generated"] += len(new_alerts)
                
                # 發送通知
                await self.alert_manager.send_notifications(new_alerts)
                
                # 自動響應
                if self.auto_response_enabled:
                    await self._trigger_auto_response(new_alerts)
                    
        except Exception as e:
            self.logger.error(f"指標收集和處理失敗: {e}")
    
    async def _get_latest_metrics(self) -> List[MetricValue]:
        """獲取最新指標"""
        # 這裡應該從 UnifiedMetricsCollector 獲取最新的指標
        # 暫時使用模擬數據
        return []
    
    async def _perform_anomaly_detection(self, metrics: List[MetricValue]):
        """執行異常檢測"""
        anomalies_detected = 0
        
        for metric in metrics:
            # 添加到異常檢測器
            self.anomaly_detector.add_metric_value(
                metric.metric_name, 
                metric.value, 
                metric.timestamp
            )
            
            # 檢測異常
            anomaly_result = self.anomaly_detector.detect_anomaly(
                metric.metric_name, 
                metric.value
            )
            
            if anomaly_result["is_anomaly"] and anomaly_result["confidence"] > 0.8:
                anomalies_detected += 1
                
                # 記錄異常
                self.logger.warning(
                    f"檢測到異常: {metric.metric_name}",
                    value=metric.value,
                    confidence=anomaly_result["confidence"],
                    reason=anomaly_result["reason"],
                    baseline_mean=anomaly_result.get("baseline_mean"),
                    z_score=anomaly_result.get("z_score")
                )
                
                # 可以創建異常告警
                await self._create_anomaly_alert(metric, anomaly_result)
        
        if anomalies_detected > 0:
            self.monitoring_stats["anomalies_detected"] += anomalies_detected
    
    async def _create_anomaly_alert(self, metric: MetricValue, anomaly_result: Dict):
        """創建異常告警"""
        # 創建動態異常告警規則
        rule_id = f"anomaly_{metric.metric_name}_{int(time.time())}"
        
        rule = AlertRule(
            rule_id=rule_id,
            name=f"異常檢測: {metric.metric_name}",
            description=f"檢測到 {metric.metric_name} 異常，置信度: {anomaly_result['confidence']:.2f}",
            metric_name=metric.metric_name,
            condition="!=",  # 用於異常檢測
            threshold=anomaly_result.get("baseline_mean", metric.value),
            severity=AlertSeverity.MEDIUM if anomaly_result["confidence"] > 0.9 else AlertSeverity.LOW,
            duration_seconds=0  # 立即觸發
        )
        
        # 暫時添加規則並立即評估
        self.alert_manager.add_rule(rule)
        new_alerts = self.alert_manager.evaluate_rules([metric])
        
        if new_alerts:
            await self.alert_manager.send_notifications(new_alerts)
        
        # 移除臨時規則
        self.alert_manager.remove_rule(rule_id)
    
    async def _trigger_auto_response(self, alerts: List[Alert]):
        """觸發自動響應"""
        for alert in alerts:
            try:
                response_triggered = False
                
                # 根據告警類型和嚴重性決定響應動作
                if alert.severity == AlertSeverity.CRITICAL:
                    if "latency" in alert.metric_name.lower():
                        # 觸發延遲優化
                        await self.performance_optimizer.manual_optimization(
                            domain=self.performance_optimizer.OptimizationDomain.LATENCY,
                            strategy=self.performance_optimizer.OptimizationStrategy.AGGRESSIVE
                        )
                        response_triggered = True
                        
                    elif "cpu" in alert.metric_name.lower():
                        # 觸發CPU優化
                        await self.performance_optimizer.manual_optimization(
                            domain=self.performance_optimizer.OptimizationDomain.RESOURCE_UTILIZATION,
                            strategy=self.performance_optimizer.OptimizationStrategy.AGGRESSIVE
                        )
                        response_triggered = True
                        
                elif alert.severity == AlertSeverity.HIGH:
                    if "throughput" in alert.metric_name.lower() or "transmission" in alert.metric_name.lower():
                        # 觸發吞吐量優化
                        await self.performance_optimizer.manual_optimization(
                            domain=self.performance_optimizer.OptimizationDomain.THROUGHPUT,
                            strategy=self.performance_optimizer.OptimizationStrategy.BALANCED
                        )
                        response_triggered = True
                        
                    elif "handover" in alert.metric_name.lower():
                        # 觸發衛星換手優化
                        await self.performance_optimizer.manual_optimization(
                            domain=self.performance_optimizer.OptimizationDomain.SATELLITE_HANDOVER,
                            strategy=self.performance_optimizer.OptimizationStrategy.BALANCED
                        )
                        response_triggered = True
                
                if response_triggered:
                    self.monitoring_stats["auto_responses_triggered"] += 1
                    self.logger.info(
                        f"自動響應已觸發",
                        alert_id=alert.alert_id,
                        metric=alert.metric_name,
                        severity=alert.severity.value
                    )
                    
            except Exception as e:
                self.logger.error(f"自動響應失敗 {alert.alert_id}: {e}")
    
    async def _update_dashboard_data(self):
        """更新儀表板數據"""
        try:
            current_time = datetime.now()
            
            # 統計活躍告警
            active_alerts = list(self.alert_manager.active_alerts.values())
            critical_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL)
            high_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.HIGH)
            
            # 計算整體狀態
            if critical_count > 0:
                overall_status = MonitoringStatus.CRITICAL
            elif high_count > 0 or len(active_alerts) > 5:
                overall_status = MonitoringStatus.WARNING
            else:
                overall_status = MonitoringStatus.HEALTHY
            
            # 服務狀態（模擬）
            services_status = {
                "netstack-api": MonitoringStatus.HEALTHY,
                "simworld-backend": MonitoringStatus.HEALTHY,
                "performance-optimizer": MonitoringStatus.HEALTHY,
                "metrics-collector": MonitoringStatus.HEALTHY
            }
            
            # 關鍵指標（從最近的指標中提取）
            key_metrics = {}
            if self.recent_metrics:
                recent_by_name = defaultdict(list)
                for metric in list(self.recent_metrics)[-50:]:  # 最近50個指標
                    recent_by_name[metric.metric_name].append(metric.value)
                
                for metric_name, values in recent_by_name.items():
                    if values:
                        key_metrics[metric_name] = values[-1]  # 最新值
            
            # 性能趨勢（最近10個值）
            performance_trends = {}
            if self.recent_metrics:
                recent_by_name = defaultdict(list)
                for metric in list(self.recent_metrics)[-100:]:
                    recent_by_name[metric.metric_name].append(metric.value)
                
                for metric_name, values in recent_by_name.items():
                    if len(values) >= 2:
                        performance_trends[metric_name] = values[-10:]  # 最近10個值
            
            # 計算系統健康分數
            health_score = self._calculate_system_health_score(active_alerts, key_metrics)
            
            self.dashboard_data = MonitoringDashboard(
                timestamp=current_time,
                overall_status=overall_status,
                active_alerts_count=len(active_alerts),
                critical_alerts_count=critical_count,
                high_alerts_count=high_count,
                services_status=services_status,
                key_metrics=key_metrics,
                performance_trends=performance_trends,
                system_health_score=health_score
            )
            
        except Exception as e:
            self.logger.error(f"更新儀表板數據失敗: {e}")
    
    def _calculate_system_health_score(self, active_alerts: List[Alert], key_metrics: Dict[str, float]) -> float:
        """計算系統健康分數 (0-100)"""
        base_score = 100.0
        
        # 根據告警扣分
        for alert in active_alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                base_score -= 20
            elif alert.severity == AlertSeverity.HIGH:
                base_score -= 10
            elif alert.severity == AlertSeverity.MEDIUM:
                base_score -= 5
            elif alert.severity == AlertSeverity.LOW:
                base_score -= 2
        
        # 根據關鍵指標調整
        if "ntn_kpi_e2e_latency_ms" in key_metrics:
            latency = key_metrics["ntn_kpi_e2e_latency_ms"]
            if latency > 100:
                base_score -= 15
            elif latency > 50:
                base_score -= 8
        
        if "ntn_kpi_coverage_percent" in key_metrics:
            coverage = key_metrics["ntn_kpi_coverage_percent"]
            if coverage < 60:
                base_score -= 20
            elif coverage < 75:
                base_score -= 10
        
        return max(0.0, min(100.0, base_score))
    
    def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """獲取儀表板數據"""
        if not self.dashboard_data:
            return None
        
        return {
            "timestamp": self.dashboard_data.timestamp.isoformat(),
            "overall_status": self.dashboard_data.overall_status.value,
            "alerts": {
                "active_count": self.dashboard_data.active_alerts_count,
                "critical_count": self.dashboard_data.critical_alerts_count,
                "high_count": self.dashboard_data.high_alerts_count,
                "details": [
                    {
                        "id": alert.alert_id,
                        "rule_id": alert.rule_id,
                        "severity": alert.severity.value,
                        "status": alert.status.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metric": alert.metric_name,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold
                    }
                    for alert in self.alert_manager.active_alerts.values()
                ]
            },
            "services_status": {
                service: status.value 
                for service, status in self.dashboard_data.services_status.items()
            },
            "key_metrics": self.dashboard_data.key_metrics,
            "performance_trends": self.dashboard_data.performance_trends,
            "system_health_score": self.dashboard_data.system_health_score,
            "monitoring_stats": self.monitoring_stats
        }
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """獲取告警規則列表"""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "metric_name": rule.metric_name,
                "condition": rule.condition,
                "threshold": rule.threshold,
                "severity": rule.severity.value,
                "duration_seconds": rule.duration_seconds,
                "enabled": rule.enabled,
                "tags": rule.tags
            }
            for rule in self.alert_manager.rules.values()
        ]
    
    def add_custom_rule(self, rule_data: Dict[str, Any]) -> bool:
        """添加自定義告警規則"""
        try:
            rule = AlertRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                description=rule_data.get("description", ""),
                metric_name=rule_data["metric_name"],
                condition=rule_data["condition"],
                threshold=float(rule_data["threshold"]),
                severity=AlertSeverity(rule_data["severity"]),
                duration_seconds=rule_data.get("duration_seconds", 60),
                evaluation_interval=rule_data.get("evaluation_interval", 30),
                enabled=rule_data.get("enabled", True),
                tags=rule_data.get("tags", {})
            )
            
            self.alert_manager.add_rule(rule)
            return True
            
        except Exception as e:
            self.logger.error(f"添加自定義規則失敗: {e}")
            return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """更新告警規則"""
        try:
            if rule_id not in self.alert_manager.rules:
                return False
            
            rule = self.alert_manager.rules[rule_id]
            
            if "threshold" in updates:
                rule.threshold = float(updates["threshold"])
            if "enabled" in updates:
                rule.enabled = bool(updates["enabled"])
            if "severity" in updates:
                rule.severity = AlertSeverity(updates["severity"])
            if "duration_seconds" in updates:
                rule.duration_seconds = int(updates["duration_seconds"])
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新規則失敗 {rule_id}: {e}")
            return False
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """獲取監控摘要"""
        return {
            "monitoring_active": self.monitoring_active,
            "auto_response_enabled": self.auto_response_enabled,
            "monitoring_interval": self.monitoring_interval,
            "dashboard_update_interval": self.dashboard_update_interval,
            "total_rules": len(self.alert_manager.rules),
            "active_alerts": len(self.alert_manager.active_alerts),
            "recent_metrics_count": len(self.recent_metrics),
            "stats": self.monitoring_stats.copy(),
            "system_health_score": self.dashboard_data.system_health_score if self.dashboard_data else 0
        }


async def main():
    """主函數 - 示例用法"""
    # 這裡需要實際的依賴注入
    from .unified_metrics_collector import UnifiedMetricsCollector
    from .enhanced_performance_optimizer import EnhancedPerformanceOptimizer
    from ..adapters.redis_adapter import RedisAdapter
    
    # 初始化依賴
    redis_adapter = RedisAdapter()
    metrics_collector = UnifiedMetricsCollector(redis_adapter)
    performance_optimizer = EnhancedPerformanceOptimizer()
    
    # 創建監控系統
    monitoring_system = RealTimeMonitoringAlerting(metrics_collector, performance_optimizer)
    
    # 啟動監控
    print("🔍 啟動即時性能監控和告警系統...")
    await monitoring_system.start_monitoring()
    
    # 運行一段時間
    await asyncio.sleep(60)
    
    # 獲取監控摘要
    summary = monitoring_system.get_monitoring_summary()
    print(f"📊 監控摘要: {summary}")
    
    # 獲取儀表板數據
    dashboard = monitoring_system.get_dashboard_data()
    if dashboard:
        print(f"📈 儀表板數據: 系統健康分數 {dashboard['system_health_score']:.1f}")
        print(f"   活躍告警: {dashboard['alerts']['active_count']}")
        print(f"   關鍵指標數量: {len(dashboard['key_metrics'])}")
    
    # 停止監控
    await monitoring_system.stop_monitoring()
    print("✅ 即時性能監控系統已停止")


if __name__ == "__main__":
    asyncio.run(main())