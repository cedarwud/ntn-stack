"""
性能監控器

整合來源：
- stage4_timeseries_preprocessing/real_time_monitoring.py (時序處理監控)
- 各Stage的處理時間監控
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .base_monitor import BaseMonitor, MonitoringMetric, MonitoringConfig


class ProcessingStatus(Enum):
    """處理狀態"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ProcessingEvent:
    """處理事件"""
    event_id: str
    stage_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: ProcessingStatus
    input_count: int
    output_count: int
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class AnomalyDetectionResult:
    """異常檢測結果"""
    anomalies_detected: List[str]
    confidence_score: float
    recommended_actions: List[str]


@dataclass
class PerformanceMonitoringConfig(MonitoringConfig):
    """性能監控配置"""
    stage_timeout_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'Stage1': 300.0,  # 5分鐘
        'Stage2': 60.0,   # 1分鐘
        'Stage3': 30.0,   # 30秒
        'Stage4': 120.0,  # 2分鐘
        'Stage5': 60.0,   # 1分鐘
        'Stage6': 10.0    # 10秒
    })
    throughput_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'Stage1': 50.0,    # satellites/second
        'Stage2': 100.0,   # satellites/second
        'Stage3': 200.0,   # satellites/second
        'Stage4': 50.0,    # satellites/second
        'Stage5': 100.0,   # satellites/second
        'Stage6': 500.0    # requests/second
    })
    anomaly_detection_enabled: bool = True


class PerformanceMonitor(BaseMonitor):
    """性能監控器 - 整合Stage 4的時序監控功能"""

    def __init__(self, config: PerformanceMonitoringConfig):
        super().__init__("PerformanceMonitor", config)
        self.stage_timeout_thresholds = config.stage_timeout_thresholds
        self.throughput_thresholds = config.throughput_thresholds
        self.anomaly_detection_enabled = config.anomaly_detection_enabled

        # 處理事件歷史
        self.processing_events: List[ProcessingEvent] = []

        # 性能統計
        self.performance_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'average_processing_time': 0.0,
            'throughput_per_minute': 0.0
        }

    def collect_metrics(self) -> List[MonitoringMetric]:
        """收集性能相關指標"""
        metrics = []

        # 處理時間指標
        processing_time_metrics = self._collect_processing_time_metrics()
        metrics.extend(processing_time_metrics)

        # 吞吐量指標
        throughput_metrics = self._collect_throughput_metrics()
        metrics.extend(throughput_metrics)

        # 成功率指標
        success_rate_metrics = self._collect_success_rate_metrics()
        metrics.extend(success_rate_metrics)

        return metrics

    def monitor_processing_pipeline(self, stage_name: str, processing_time: float, data_count: int):
        """監控處理管道性能"""
        throughput = data_count / processing_time if processing_time > 0 else 0

        # 添加處理時間指標
        processing_metric = MonitoringMetric(
            metric_name=f"{stage_name}_processing_time",
            value=processing_time,
            unit="seconds",
            timestamp=datetime.now(),
            tags={"stage": stage_name, "type": "performance"},
            threshold_warning=self.stage_timeout_thresholds.get(stage_name, 60.0) * 0.8,
            threshold_critical=self.stage_timeout_thresholds.get(stage_name, 60.0)
        )
        self.add_metric(processing_metric)

        # 添加吞吐量指標
        throughput_metric = MonitoringMetric(
            metric_name=f"{stage_name}_throughput",
            value=throughput,
            unit="items_per_second",
            timestamp=datetime.now(),
            tags={"stage": stage_name, "type": "throughput"},
            threshold_warning=self.throughput_thresholds.get(stage_name, 10.0) * 0.8,
            threshold_critical=self.throughput_thresholds.get(stage_name, 10.0) * 0.5
        )
        self.add_metric(throughput_metric)

        # 更新統計
        self.performance_stats['total_processed'] += data_count
        self._update_average_processing_time(processing_time)

        self.logger.info(f"監控 {stage_name}: 處理時間={processing_time:.2f}s, 吞吐量={throughput:.2f} items/s")

    def start_processing_event(self, stage_name: str, input_count: int) -> str:
        """開始處理事件"""
        event_id = f"{stage_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        event = ProcessingEvent(
            event_id=event_id,
            stage_name=stage_name,
            start_time=datetime.now(),
            end_time=None,
            status=ProcessingStatus.RUNNING,
            input_count=input_count,
            output_count=0
        )

        self.processing_events.append(event)
        return event_id

    def end_processing_event(self, event_id: str, output_count: int, status: ProcessingStatus = ProcessingStatus.COMPLETED, error_message: Optional[str] = None):
        """結束處理事件"""
        for event in self.processing_events:
            if event.event_id == event_id:
                event.end_time = datetime.now()
                event.status = status
                event.output_count = output_count
                event.error_message = error_message

                if event.start_time and event.end_time:
                    event.processing_time = (event.end_time - event.start_time).total_seconds()

                # 監控處理管道
                if event.processing_time:
                    self.monitor_processing_pipeline(event.stage_name, event.processing_time, output_count)

                # 更新統計
                if status == ProcessingStatus.COMPLETED:
                    self.performance_stats['successful_processed'] += output_count
                else:
                    self.performance_stats['failed_processed'] += event.input_count

                break

    def detect_processing_anomalies(self) -> AnomalyDetectionResult:
        """檢測處理異常"""
        if not self.anomaly_detection_enabled:
            return AnomalyDetectionResult(
                anomalies_detected=[],
                confidence_score=0.0,
                recommended_actions=[]
            )

        anomalies = []
        recommended_actions = []

        # 檢查最近的處理事件
        recent_events = self._get_recent_events(timedelta(minutes=30))

        # 檢測處理時間異常
        time_anomalies = self._detect_processing_time_anomalies(recent_events)
        anomalies.extend(time_anomalies)

        # 檢測吞吐量異常
        throughput_anomalies = self._detect_throughput_anomalies(recent_events)
        anomalies.extend(throughput_anomalies)

        # 檢測失敗率異常
        failure_anomalies = self._detect_failure_rate_anomalies(recent_events)
        anomalies.extend(failure_anomalies)

        # 生成建議行動
        if anomalies:
            recommended_actions = self._generate_recommended_actions(anomalies)

        # 計算信心度
        confidence_score = len(anomalies) / 10.0 if anomalies else 0.0  # 簡化計算
        confidence_score = min(1.0, confidence_score)

        return AnomalyDetectionResult(
            anomalies_detected=anomalies,
            confidence_score=confidence_score,
            recommended_actions=recommended_actions
        )

    def get_stage_performance_summary(self, stage_name: str, time_window: timedelta) -> Dict[str, Any]:
        """獲取階段性能摘要"""
        cutoff_time = datetime.now() - time_window
        stage_events = [
            e for e in self.processing_events
            if e.stage_name == stage_name and e.start_time >= cutoff_time and e.processing_time is not None
        ]

        if not stage_events:
            return {"stage_name": stage_name, "no_data": True}

        processing_times = [e.processing_time for e in stage_events if e.processing_time]
        throughputs = [
            e.output_count / e.processing_time
            for e in stage_events
            if e.processing_time and e.processing_time > 0
        ]

        return {
            "stage_name": stage_name,
            "time_window_hours": time_window.total_seconds() / 3600,
            "total_executions": len(stage_events),
            "successful_executions": len([e for e in stage_events if e.status == ProcessingStatus.COMPLETED]),
            "failed_executions": len([e for e in stage_events if e.status == ProcessingStatus.FAILED]),
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
            "min_processing_time": min(processing_times) if processing_times else 0,
            "max_processing_time": max(processing_times) if processing_times else 0,
            "average_throughput": sum(throughputs) / len(throughputs) if throughputs else 0,
            "success_rate": len([e for e in stage_events if e.status == ProcessingStatus.COMPLETED]) / len(stage_events) if stage_events else 0
        }

    def _collect_processing_time_metrics(self) -> List[MonitoringMetric]:
        """收集處理時間指標"""
        metrics = []
        recent_events = self._get_recent_events(self.config.collection_interval)

        for stage_name in self.stage_timeout_thresholds.keys():
            stage_events = [e for e in recent_events if e.stage_name == stage_name and e.processing_time]

            if stage_events:
                avg_time = sum(e.processing_time for e in stage_events) / len(stage_events)
                metrics.append(MonitoringMetric(
                    metric_name=f"{stage_name}_avg_processing_time",
                    value=avg_time,
                    unit="seconds",
                    timestamp=datetime.now(),
                    tags={"stage": stage_name, "type": "processing_time"},
                    threshold_warning=self.stage_timeout_thresholds[stage_name] * 0.8,
                    threshold_critical=self.stage_timeout_thresholds[stage_name]
                ))

        return metrics

    def _collect_throughput_metrics(self) -> List[MonitoringMetric]:
        """收集吞吐量指標"""
        metrics = []
        recent_events = self._get_recent_events(timedelta(minutes=1))

        for stage_name in self.throughput_thresholds.keys():
            stage_events = [e for e in recent_events if e.stage_name == stage_name and e.processing_time]

            if stage_events:
                total_output = sum(e.output_count for e in stage_events)
                total_time = sum(e.processing_time for e in stage_events)
                throughput = total_output / total_time if total_time > 0 else 0

                metrics.append(MonitoringMetric(
                    metric_name=f"{stage_name}_throughput",
                    value=throughput,
                    unit="items_per_second",
                    timestamp=datetime.now(),
                    tags={"stage": stage_name, "type": "throughput"},
                    threshold_warning=self.throughput_thresholds[stage_name] * 0.8,
                    threshold_critical=self.throughput_thresholds[stage_name] * 0.5
                ))

        return metrics

    def _collect_success_rate_metrics(self) -> List[MonitoringMetric]:
        """收集成功率指標"""
        metrics = []
        recent_events = self._get_recent_events(timedelta(minutes=10))

        if recent_events:
            successful = len([e for e in recent_events if e.status == ProcessingStatus.COMPLETED])
            success_rate = successful / len(recent_events)

            metrics.append(MonitoringMetric(
                metric_name="overall_success_rate",
                value=success_rate,
                unit="ratio",
                timestamp=datetime.now(),
                tags={"type": "success_rate"},
                threshold_warning=0.9,
                threshold_critical=0.8
            ))

        return metrics

    def _get_recent_events(self, time_window: timedelta) -> List[ProcessingEvent]:
        """獲取最近的處理事件"""
        cutoff_time = datetime.now() - time_window
        return [e for e in self.processing_events if e.start_time >= cutoff_time]

    def _detect_processing_time_anomalies(self, events: List[ProcessingEvent]) -> List[str]:
        """檢測處理時間異常"""
        anomalies = []

        for stage_name in self.stage_timeout_thresholds.keys():
            stage_events = [e for e in events if e.stage_name == stage_name and e.processing_time]

            if stage_events:
                max_time = max(e.processing_time for e in stage_events)
                threshold = self.stage_timeout_thresholds[stage_name]

                if max_time > threshold:
                    anomalies.append(f"{stage_name} 處理時間超過閾值: {max_time:.2f}s > {threshold}s")

        return anomalies

    def _detect_throughput_anomalies(self, events: List[ProcessingEvent]) -> List[str]:
        """檢測吞吐量異常"""
        anomalies = []

        for stage_name in self.throughput_thresholds.keys():
            stage_events = [e for e in events if e.stage_name == stage_name and e.processing_time]

            if stage_events:
                throughputs = [e.output_count / e.processing_time for e in stage_events if e.processing_time > 0]
                if throughputs:
                    min_throughput = min(throughputs)
                    threshold = self.throughput_thresholds[stage_name] * 0.5

                    if min_throughput < threshold:
                        anomalies.append(f"{stage_name} 吞吐量過低: {min_throughput:.2f} < {threshold:.2f} items/s")

        return anomalies

    def _detect_failure_rate_anomalies(self, events: List[ProcessingEvent]) -> List[str]:
        """檢測失敗率異常"""
        anomalies = []

        if events:
            failed = len([e for e in events if e.status == ProcessingStatus.FAILED])
            failure_rate = failed / len(events)

            if failure_rate > 0.1:  # 失敗率超過10%
                anomalies.append(f"整體失敗率過高: {failure_rate:.2%}")

        return anomalies

    def _generate_recommended_actions(self, anomalies: List[str]) -> List[str]:
        """生成建議行動"""
        actions = []

        for anomaly in anomalies:
            if "處理時間超過閾值" in anomaly:
                actions.append("考慮增加並行處理線程或優化算法")
            elif "吞吐量過低" in anomaly:
                actions.append("檢查系統資源使用情況，可能需要擴容")
            elif "失敗率過高" in anomaly:
                actions.append("檢查錯誤日誌並修復相關問題")

        return actions

    def _update_average_processing_time(self, new_time: float):
        """更新平均處理時間"""
        current_avg = self.performance_stats['average_processing_time']
        total_processed = self.performance_stats['total_processed']

        if total_processed > 1:
            # 累積平均值更新
            self.performance_stats['average_processing_time'] = (
                (current_avg * (total_processed - 1) + new_time) / total_processed
            )
        else:
            self.performance_stats['average_processing_time'] = new_time

    def measure_operation(self, operation_name: str):
        """測量操作時間的上下文管理器"""
        return OperationTimer(self, operation_name)


class OperationTimer:
    """操作計時器上下文管理器"""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            operation_time = (datetime.now() - self.start_time).total_seconds()
            # 記錄操作時間到性能監控器
            self.monitor.logger.debug(f"操作 '{self.operation_name}' 耗時: {operation_time:.3f}秒")