"""
Phase 3 Stage 8: 即時性能監控和問題識別系統
實現實時監控、異常檢測和自動化問題識別
"""
import asyncio
import json
import logging
import time
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import deque, defaultdict
import yaml

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    """異常類型"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_SPIKE = "error_spike"
    LATENCY_SPIKE = "latency_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SLA_VIOLATION = "sla_violation"
    HANDOVER_FAILURE = "handover_failure"
    TRAFFIC_ANOMALY = "traffic_anomaly"

class Severity(Enum):
    """嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    """性能指標"""
    timestamp: datetime
    service_name: str
    metric_name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class Anomaly:
    """異常事件"""
    id: str
    type: AnomalyType
    severity: Severity
    service_name: str
    metric_name: str
    description: str
    current_value: float
    expected_value: float
    threshold: float
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    impact_score: float = 0.0
    root_cause: Optional[str] = None
    
@dataclass
class AlertRule:
    """告警規則"""
    name: str
    metric_pattern: str
    condition: str  # >, <, ==, anomaly_detection
    threshold: float
    severity: Severity
    window_minutes: int = 5
    min_samples: int = 10
    enabled: bool = True

class StatisticalAnalyzer:
    """統計分析器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metric_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.baseline_stats: Dict[str, Dict] = {}
        
    def add_metric(self, metric: PerformanceMetric):
        """添加指標數據"""
        key = f"{metric.service_name}.{metric.metric_name}"
        self.metric_windows[key].append((metric.timestamp, metric.value))
        
        # 更新基線統計
        if len(self.metric_windows[key]) >= 10:
            values = [v for _, v in self.metric_windows[key]]
            self.baseline_stats[key] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99)
            }
    
    def detect_anomaly(self, metric: PerformanceMetric) -> Optional[Tuple[bool, float, str]]:
        """檢測異常"""
        key = f"{metric.service_name}.{metric.metric_name}"
        
        if key not in self.baseline_stats:
            return None
        
        stats = self.baseline_stats[key]
        value = metric.value
        
        # Z-score 異常檢測
        if stats["stdev"] > 0:
            z_score = abs(value - stats["mean"]) / stats["stdev"]
            if z_score > 3:  # 3-sigma 規則
                anomaly_score = min(z_score / 3, 5.0)  # 正規化到 0-5
                reason = f"Z-score異常: {z_score:.2f} (閾值: 3.0)"
                return True, anomaly_score, reason
        
        # 百分位數異常檢測
        if value > stats["p99"]:
            anomaly_score = (value - stats["p99"]) / (stats["max"] - stats["p99"]) if stats["max"] > stats["p99"] else 1.0
            reason = f"超過P99: {value:.2f} > {stats['p99']:.2f}"
            return True, min(anomaly_score * 2, 5.0), reason
        
        # 趨勢異常檢測
        if len(self.metric_windows[key]) >= 10:
            recent_values = [v for _, v in list(self.metric_windows[key])[-10:]]
            if self._detect_trend_anomaly(recent_values):
                reason = "檢測到趨勢異常"
                return True, 2.0, reason
        
        return None
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """計算百分位數"""
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        if f + 1 < len(sorted_values):
            return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
        else:
            return sorted_values[f]
    
    def _detect_trend_anomaly(self, values: List[float]) -> bool:
        """檢測趨勢異常"""
        if len(values) < 5:
            return False
        
        # 檢測持續上升趨勢（可能表示資源洩漏）
        increasing_count = 0
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increasing_count += 1
        
        # 如果 80% 以上的數據點都在上升，視為異常
        if increasing_count / (len(values) - 1) > 0.8:
            return True
        
        # 檢測突然變化
        recent_avg = statistics.mean(values[-3:])
        earlier_avg = statistics.mean(values[:3])
        
        if abs(recent_avg - earlier_avg) / earlier_avg > 0.5:  # 50% 變化
            return True
        
        return False

class RealtimePerformanceMonitor:
    """即時性能監控器"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.analyzer = StatisticalAnalyzer()
        self.alert_rules: List[AlertRule] = []
        self.active_anomalies: Dict[str, Anomaly] = {}
        self.metric_buffer: List[PerformanceMetric] = []
        self.is_monitoring = False
        
        # 性能指標
        self.metrics_processed = 0
        self.anomalies_detected = 0
        self.alerts_triggered = 0
        
        # 回調函數
        self.anomaly_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # 初始化告警規則
        self._initialize_alert_rules()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "monitoring": {
                "collection_interval": 5,
                "analysis_interval": 10,
                "anomaly_threshold": 2.0,
                "buffer_size": 1000
            },
            "sla_thresholds": {
                "error_rate": 0.001,
                "handover_latency_ms": 50.0,
                "handover_success_rate": 0.995,
                "response_time_ms": 100.0
            },
            "alert_rules": [
                {
                    "name": "high_error_rate",
                    "metric_pattern": "*.error_rate",
                    "condition": ">",
                    "threshold": 0.001,
                    "severity": "critical"
                },
                {
                    "name": "high_handover_latency",
                    "metric_pattern": "*.handover_latency_ms",
                    "condition": ">",
                    "threshold": 50.0,
                    "severity": "critical"
                }
            ]
        }
    
    def _initialize_alert_rules(self):
        """初始化告警規則"""
        rules_config = self.config.get("alert_rules", [])
        
        for rule_config in rules_config:
            rule = AlertRule(
                name=rule_config["name"],
                metric_pattern=rule_config["metric_pattern"],
                condition=rule_config["condition"],
                threshold=rule_config["threshold"],
                severity=Severity(rule_config.get("severity", "medium")),
                window_minutes=rule_config.get("window_minutes", 5),
                min_samples=rule_config.get("min_samples", 10),
                enabled=rule_config.get("enabled", True)
            )
            self.alert_rules.append(rule)
        
        logger.info(f"初始化 {len(self.alert_rules)} 條告警規則")
    
    async def start_monitoring(self):
        """啟動即時監控"""
        if self.is_monitoring:
            logger.warning("監控已在運行")
            return
        
        self.is_monitoring = True
        logger.info("🚀 啟動即時性能監控系統")
        
        # 啟動監控任務
        tasks = [
            asyncio.create_task(self._metric_collection_loop()),
            asyncio.create_task(self._analysis_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._anomaly_resolution_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("即時監控已停止")
        finally:
            self.is_monitoring = False
    
    async def stop_monitoring(self):
        """停止監控"""
        logger.info("🛑 停止即時性能監控")
        self.is_monitoring = False
    
    async def _metric_collection_loop(self):
        """指標收集循環"""
        collection_config = self.config.get("monitoring", {})
        interval = collection_config.get("collection_interval", 5)
        
        while self.is_monitoring:
            try:
                # 收集各服務指標
                metrics = await self._collect_realtime_metrics()
                
                for metric in metrics:
                    self.metric_buffer.append(metric)
                    self.analyzer.add_metric(metric)
                    self.metrics_processed += 1
                
                # 限制緩衝區大小
                buffer_size = collection_config.get("buffer_size", 1000)
                if len(self.metric_buffer) > buffer_size:
                    self.metric_buffer = self.metric_buffer[-buffer_size:]
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"指標收集失敗: {e}")
                await asyncio.sleep(interval)
    
    async def _analysis_loop(self):
        """分析循環"""
        analysis_config = self.config.get("monitoring", {})
        interval = analysis_config.get("analysis_interval", 10)
        
        while self.is_monitoring:
            try:
                # 分析最近的指標
                recent_metrics = self.metric_buffer[-100:] if len(self.metric_buffer) >= 100 else self.metric_buffer
                
                for metric in recent_metrics:
                    await self._analyze_metric(metric)
                
                # 檢查 SLA 合規性
                await self._check_sla_compliance()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"指標分析失敗: {e}")
                await asyncio.sleep(interval)
    
    async def _alert_processing_loop(self):
        """告警處理循環"""
        while self.is_monitoring:
            try:
                # 處理活躍異常
                for anomaly_id, anomaly in list(self.active_anomalies.items()):
                    await self._process_anomaly(anomaly)
                
                await asyncio.sleep(30)  # 每30秒處理一次
                
            except Exception as e:
                logger.error(f"告警處理失敗: {e}")
                await asyncio.sleep(30)
    
    async def _anomaly_resolution_loop(self):
        """異常解決循環"""
        while self.is_monitoring:
            try:
                # 檢查異常是否已解決
                resolved_anomalies = []
                
                for anomaly_id, anomaly in self.active_anomalies.items():
                    if await self._check_anomaly_resolved(anomaly):
                        anomaly.resolved_at = datetime.now()
                        resolved_anomalies.append(anomaly_id)
                        logger.info(f"✅ 異常已解決: {anomaly.description}")
                
                # 移除已解決的異常
                for anomaly_id in resolved_anomalies:
                    del self.active_anomalies[anomaly_id]
                
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
            except Exception as e:
                logger.error(f"異常解決檢查失敗: {e}")
                await asyncio.sleep(60)
    
    async def _collect_realtime_metrics(self) -> List[PerformanceMetric]:
        """收集即時指標"""
        metrics = []
        current_time = datetime.now()
        
        # 模擬從各服務收集指標
        services = ["netstack", "simworld", "frontend", "gateway"]
        
        for service in services:
            # 模擬指標收集
            import random
            
            # HTTP 指標
            metrics.append(PerformanceMetric(
                timestamp=current_time,
                service_name=service,
                metric_name="error_rate",
                value=random.uniform(0.0001, 0.002),  # 0.01-0.2% 錯誤率
                labels={"service": service}
            ))
            
            metrics.append(PerformanceMetric(
                timestamp=current_time,
                service_name=service,
                metric_name="response_time_ms",
                value=random.uniform(20, 120),  # 20-120ms 響應時間
                labels={"service": service}
            ))
            
            metrics.append(PerformanceMetric(
                timestamp=current_time,
                service_name=service,
                metric_name="throughput_rps",
                value=random.uniform(50, 500),  # 50-500 RPS
                labels={"service": service}
            ))
            
            # 資源指標
            metrics.append(PerformanceMetric(
                timestamp=current_time,
                service_name=service,
                metric_name="cpu_usage",
                value=random.uniform(0.2, 0.9),  # 20-90% CPU 使用率
                labels={"service": service}
            ))
            
            metrics.append(PerformanceMetric(
                timestamp=current_time,
                service_name=service,
                metric_name="memory_usage",
                value=random.uniform(0.3, 0.8),  # 30-80% 記憶體使用率
                labels={"service": service}
            ))
        
        # NTN 特定指標
        metrics.extend([
            PerformanceMetric(
                timestamp=current_time,
                service_name="ntn",
                metric_name="handover_latency_ms",
                value=random.uniform(25, 65),  # 25-65ms handover 延遲
                labels={"interface": "n2"}
            ),
            PerformanceMetric(
                timestamp=current_time,
                service_name="ntn",
                metric_name="handover_success_rate",
                value=random.uniform(0.993, 0.999),  # 99.3-99.9% 成功率
                labels={"interface": "n2"}
            ),
            PerformanceMetric(
                timestamp=current_time,
                service_name="ntn",
                metric_name="active_ue_contexts",
                value=random.randint(5, 50),  # 5-50 活躍 UE
                labels={"interface": "n2"}
            )
        ])
        
        return metrics
    
    async def _analyze_metric(self, metric: PerformanceMetric):
        """分析單個指標"""
        # 異常檢測
        anomaly_result = self.analyzer.detect_anomaly(metric)
        
        if anomaly_result:
            is_anomaly, anomaly_score, reason = anomaly_result
            if is_anomaly:
                await self._handle_anomaly_detection(metric, anomaly_score, reason)
        
        # 規則匹配
        for rule in self.alert_rules:
            if rule.enabled and self._match_rule(metric, rule):
                await self._trigger_alert(metric, rule)
    
    def _match_rule(self, metric: PerformanceMetric, rule: AlertRule) -> bool:
        """檢查指標是否匹配告警規則"""
        # 簡單的模式匹配
        pattern = rule.metric_pattern.replace("*", "")
        metric_path = f"{metric.service_name}.{metric.metric_name}"
        
        if pattern not in metric_path:
            return False
        
        # 檢查條件
        if rule.condition == ">":
            return metric.value > rule.threshold
        elif rule.condition == "<":
            return metric.value < rule.threshold
        elif rule.condition == "==":
            return abs(metric.value - rule.threshold) < 0.001
        
        return False
    
    async def _handle_anomaly_detection(self, metric: PerformanceMetric, anomaly_score: float, reason: str):
        """處理異常檢測"""
        anomaly_id = f"{metric.service_name}_{metric.metric_name}_{int(time.time())}"
        
        # 確定異常類型
        anomaly_type = self._classify_anomaly(metric)
        
        # 確定嚴重程度
        severity = self._determine_severity(metric, anomaly_score)
        
        # 創建異常對象
        anomaly = Anomaly(
            id=anomaly_id,
            type=anomaly_type,
            severity=severity,
            service_name=metric.service_name,
            metric_name=metric.metric_name,
            description=f"{metric.service_name} {metric.metric_name} 異常: {reason}",
            current_value=metric.value,
            expected_value=self._get_expected_value(metric),
            threshold=self._get_threshold_for_metric(metric),
            detected_at=metric.timestamp,
            impact_score=anomaly_score
        )
        
        self.active_anomalies[anomaly_id] = anomaly
        self.anomalies_detected += 1
        
        logger.warning(f"🚨 檢測到異常: {anomaly.description} (評分: {anomaly_score:.2f})")
        
        # 觸發回調
        for callback in self.anomaly_callbacks:
            try:
                await callback(anomaly)
            except Exception as e:
                logger.error(f"異常回調執行失敗: {e}")
    
    def _classify_anomaly(self, metric: PerformanceMetric) -> AnomalyType:
        """分類異常類型"""
        if "error_rate" in metric.metric_name:
            return AnomalyType.ERROR_SPIKE
        elif "latency" in metric.metric_name or "response_time" in metric.metric_name:
            return AnomalyType.LATENCY_SPIKE
        elif "handover" in metric.metric_name:
            return AnomalyType.HANDOVER_FAILURE
        elif "cpu" in metric.metric_name or "memory" in metric.metric_name:
            return AnomalyType.RESOURCE_EXHAUSTION
        else:
            return AnomalyType.PERFORMANCE_DEGRADATION
    
    def _determine_severity(self, metric: PerformanceMetric, anomaly_score: float) -> Severity:
        """確定嚴重程度"""
        # 檢查是否違反 SLA
        sla_thresholds = self.config.get("sla_thresholds", {})
        
        if metric.metric_name == "error_rate" and metric.value > sla_thresholds.get("error_rate", 0.001):
            return Severity.CRITICAL
        elif metric.metric_name == "handover_latency_ms" and metric.value > sla_thresholds.get("handover_latency_ms", 50.0):
            return Severity.CRITICAL
        elif metric.metric_name == "handover_success_rate" and metric.value < sla_thresholds.get("handover_success_rate", 0.995):
            return Severity.CRITICAL
        
        # 根據異常評分確定嚴重程度
        if anomaly_score >= 4.0:
            return Severity.CRITICAL
        elif anomaly_score >= 3.0:
            return Severity.HIGH
        elif anomaly_score >= 2.0:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _get_expected_value(self, metric: PerformanceMetric) -> float:
        """獲取預期值"""
        key = f"{metric.service_name}.{metric.metric_name}"
        if key in self.analyzer.baseline_stats:
            return self.analyzer.baseline_stats[key]["mean"]
        return 0.0
    
    def _get_threshold_for_metric(self, metric: PerformanceMetric) -> float:
        """獲取指標閾值"""
        sla_thresholds = self.config.get("sla_thresholds", {})
        return sla_thresholds.get(metric.metric_name, 0.0)
    
    async def _trigger_alert(self, metric: PerformanceMetric, rule: AlertRule):
        """觸發告警"""
        alert_data = {
            "rule_name": rule.name,
            "service": metric.service_name,
            "metric": metric.metric_name,
            "current_value": metric.value,
            "threshold": rule.threshold,
            "severity": rule.severity.value,
            "timestamp": metric.timestamp.isoformat()
        }
        
        self.alerts_triggered += 1
        logger.error(f"🚨 觸發告警: {rule.name} - {metric.service_name}.{metric.metric_name} = {metric.value} (閾值: {rule.threshold})")
        
        # 觸發告警回調
        for callback in self.alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"告警回調執行失敗: {e}")
    
    async def _check_sla_compliance(self):
        """檢查 SLA 合規性"""
        sla_thresholds = self.config.get("sla_thresholds", {})
        
        # 獲取最近的指標
        recent_metrics = self.metric_buffer[-50:] if len(self.metric_buffer) >= 50 else self.metric_buffer
        
        # 按指標類型分組
        metrics_by_type = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_type[metric.metric_name].append(metric.value)
        
        # 檢查各項 SLA
        sla_violations = []
        
        for metric_name, threshold in sla_thresholds.items():
            if metric_name in metrics_by_type:
                values = metrics_by_type[metric_name]
                
                if metric_name in ["error_rate", "handover_latency_ms", "response_time_ms"]:
                    # 這些指標需要低於閾值
                    avg_value = statistics.mean(values)
                    if avg_value > threshold:
                        sla_violations.append(f"{metric_name}: {avg_value:.4f} > {threshold}")
                
                elif metric_name in ["handover_success_rate"]:
                    # 這些指標需要高於閾值
                    avg_value = statistics.mean(values)
                    if avg_value < threshold:
                        sla_violations.append(f"{metric_name}: {avg_value:.4f} < {threshold}")
        
        if sla_violations:
            logger.error(f"🚨 SLA 違規檢測:")
            for violation in sla_violations:
                logger.error(f"  - {violation}")
    
    async def _process_anomaly(self, anomaly: Anomaly):
        """處理異常"""
        # 根異因分析
        if not anomaly.root_cause:
            anomaly.root_cause = await self._analyze_root_cause(anomaly)
        
        # 計算業務影響
        anomaly.impact_score = await self._calculate_business_impact(anomaly)
    
    async def _analyze_root_cause(self, anomaly: Anomaly) -> str:
        """分析根本原因"""
        # 簡化的根因分析
        if anomaly.type == AnomalyType.ERROR_SPIKE:
            return "可能原因: 服務異常、網路問題或負載過高"
        elif anomaly.type == AnomalyType.LATENCY_SPIKE:
            return "可能原因: 資源不足、網路延遲或資料庫查詢緩慢"
        elif anomaly.type == AnomalyType.HANDOVER_FAILURE:
            return "可能原因: 衛星信號問題、配置錯誤或算法缺陷"
        elif anomaly.type == AnomalyType.RESOURCE_EXHAUSTION:
            return "可能原因: 記憶體洩漏、CPU 密集型任務或資源配置不足"
        else:
            return "需要進一步調查"
    
    async def _calculate_business_impact(self, anomaly: Anomaly) -> float:
        """計算業務影響"""
        # 基礎影響評分
        base_impact = 0.0
        
        if anomaly.severity == Severity.CRITICAL:
            base_impact = 0.8
        elif anomaly.severity == Severity.HIGH:
            base_impact = 0.6
        elif anomaly.severity == Severity.MEDIUM:
            base_impact = 0.4
        else:
            base_impact = 0.2
        
        # 根據服務重要性調整
        service_weights = {
            "netstack": 1.0,
            "simworld": 0.8,
            "frontend": 0.6,
            "gateway": 0.9
        }
        
        service_weight = service_weights.get(anomaly.service_name, 0.5)
        
        return min(base_impact * service_weight, 1.0)
    
    async def _check_anomaly_resolved(self, anomaly: Anomaly) -> bool:
        """檢查異常是否已解決"""
        # 獲取最近的相同指標
        recent_metrics = [
            m for m in self.metric_buffer[-10:]
            if m.service_name == anomaly.service_name and m.metric_name == anomaly.metric_name
        ]
        
        if not recent_metrics:
            return False
        
        # 檢查指標是否回到正常範圍
        recent_values = [m.value for m in recent_metrics]
        avg_recent = statistics.mean(recent_values)
        
        # 根據異常類型檢查恢復條件
        if anomaly.type in [AnomalyType.ERROR_SPIKE, AnomalyType.LATENCY_SPIKE]:
            return avg_recent < anomaly.threshold
        elif anomaly.type == AnomalyType.HANDOVER_FAILURE:
            return avg_recent > anomaly.threshold  # handover_success_rate
        else:
            # 檢查是否接近預期值
            return abs(avg_recent - anomaly.expected_value) / anomaly.expected_value < 0.1
    
    def add_anomaly_callback(self, callback: Callable):
        """添加異常回調"""
        self.anomaly_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """添加告警回調"""
        self.alert_callbacks.append(callback)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """獲取監控狀態"""
        return {
            "is_monitoring": self.is_monitoring,
            "metrics_processed": self.metrics_processed,
            "anomalies_detected": self.anomalies_detected,
            "alerts_triggered": self.alerts_triggered,
            "active_anomalies": len(self.active_anomalies),
            "buffer_size": len(self.metric_buffer),
            "last_collection": datetime.now().isoformat()
        }
    
    def get_active_anomalies(self) -> List[Dict[str, Any]]:
        """獲取活躍異常列表"""
        return [
            {
                "id": anomaly.id,
                "type": anomaly.type.value,
                "severity": anomaly.severity.value,
                "service": anomaly.service_name,
                "metric": anomaly.metric_name,
                "description": anomaly.description,
                "detected_at": anomaly.detected_at.isoformat(),
                "impact_score": anomaly.impact_score,
                "root_cause": anomaly.root_cause
            }
            for anomaly in self.active_anomalies.values()
        ]

# 使用示例
async def main():
    """即時性能監控示例"""
    
    # 創建監控配置
    config = {
        "monitoring": {
            "collection_interval": 2,
            "analysis_interval": 5,
            "anomaly_threshold": 2.0
        },
        "sla_thresholds": {
            "error_rate": 0.001,
            "handover_latency_ms": 50.0,
            "handover_success_rate": 0.995,
            "response_time_ms": 100.0
        },
        "alert_rules": [
            {
                "name": "critical_error_rate",
                "metric_pattern": "*.error_rate",
                "condition": ">",
                "threshold": 0.001,
                "severity": "critical"
            },
            {
                "name": "sla_handover_latency",
                "metric_pattern": "*.handover_latency_ms", 
                "condition": ">",
                "threshold": 50.0,
                "severity": "critical"
            }
        ]
    }
    
    config_path = "/tmp/realtime_monitor_config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    # 初始化監控器
    monitor = RealtimePerformanceMonitor(config_path)
    
    # 添加回調函數
    async def anomaly_handler(anomaly):
        print(f"🚨 異常檢測: {anomaly.description} (嚴重程度: {anomaly.severity.value})")
    
    async def alert_handler(alert):
        print(f"🔔 告警觸發: {alert['rule_name']} - {alert['metric']} = {alert['current_value']}")
    
    monitor.add_anomaly_callback(anomaly_handler)
    monitor.add_alert_callback(alert_handler)
    
    # 啟動監控
    try:
        print("🚀 啟動即時性能監控系統...")
        
        # 運行監控 (示例運行 60 秒)
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # 等待一段時間後查看狀態
        await asyncio.sleep(30)
        
        # 查看監控狀態
        status = monitor.get_monitoring_status()
        print(f"監控狀態: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        # 查看活躍異常
        anomalies = monitor.get_active_anomalies()
        print(f"活躍異常: {len(anomalies)} 個")
        for anomaly in anomalies:
            print(f"  - {anomaly['severity']}: {anomaly['description']}")
        
        # 停止監控
        await monitor.stop_monitoring()
        monitoring_task.cancel()
        
    except KeyboardInterrupt:
        print("停止監控系統")
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())