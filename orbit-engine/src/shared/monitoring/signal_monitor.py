"""
信號監控器

整合來源：
- stage3_signal_analysis/real_time_monitoring.py (文檔提到但未實作)
- stage6_dynamic_pool_planning/backup_monitoring_service.py (部分信號監控)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .base_monitor import BaseMonitor, MonitoringMetric, MonitoringConfig


class SignalQualityGrade(Enum):
    """信號品質等級"""
    EXCELLENT = "excellent"  # RSRP > -70dBm
    GOOD = "good"           # -70dBm >= RSRP > -85dBm
    FAIR = "fair"           # -85dBm >= RSRP > -100dBm
    POOR = "poor"           # RSRP <= -100dBm


@dataclass
class SignalQualityResult:
    """信號品質結果（從現有代碼複用）"""
    satellite_id: int
    rsrp_dbm: float
    rsrq_db: float
    sinr_db: float
    elevation_angle: float
    quality_grade: SignalQualityGrade
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SignalDegradationEvent:
    """信號劣化事件"""
    satellite_id: int
    metric_type: str  # RSRP, RSRQ, SINR
    current_value: float
    threshold: float
    severity: str  # WARNING, CRITICAL
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SignalDegradationReport:
    """信號劣化報告"""
    timestamp: datetime
    total_satellites_monitored: int
    degradation_events: List[SignalDegradationEvent]
    overall_health_score: float


@dataclass
class SignalTrendAnalysis:
    """信號趨勢分析"""
    time_window: timedelta
    trend_direction: str  # improving, stable, declining
    average_rsrp: float
    rsrp_variance: float
    degradation_probability: float


@dataclass
class SignalMonitoringConfig(MonitoringConfig):
    """信號監控配置"""
    signal_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'rsrp_warning': -90.0,
        'rsrp_critical': -110.0,
        'rsrq_warning': -15.0,
        'rsrq_critical': -20.0,
        'sinr_warning': 3.0,
        'sinr_critical': 0.0
    })
    monitoring_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    trend_analysis_window: timedelta = field(default_factory=lambda: timedelta(minutes=30))


class SignalMonitor(BaseMonitor):
    """信號監控器 - 整合Stage 3的信號監控功能"""

    def __init__(self, config: SignalMonitoringConfig):
        super().__init__("SignalMonitor", config)
        self.signal_thresholds = config.signal_thresholds
        self.monitoring_interval = config.monitoring_interval
        self.trend_analysis_window = config.trend_analysis_window

        # 信號歷史記錄
        self.signal_history: List[SignalQualityResult] = []
        self.degradation_events: List[SignalDegradationEvent] = []

    def collect_metrics(self) -> List[MonitoringMetric]:
        """收集信號相關指標"""
        metrics = []

        # 從signal_history收集最新數據
        if self.signal_history:
            latest_signals = self._get_recent_signals(self.monitoring_interval)

            # RSRP指標
            rsrp_metrics = self._collect_rsrp_metrics(latest_signals)
            metrics.extend(rsrp_metrics)

            # RSRQ指標
            rsrq_metrics = self._collect_rsrq_metrics(latest_signals)
            metrics.extend(rsrq_metrics)

            # SINR指標
            sinr_metrics = self._collect_sinr_metrics(latest_signals)
            metrics.extend(sinr_metrics)

        return metrics

    def add_signal_quality_result(self, signal_result: SignalQualityResult):
        """添加信號品質結果"""
        self.signal_history.append(signal_result)

        # 保持歷史記錄大小限制
        if len(self.signal_history) > self.config.max_history_size:
            self.signal_history = self.signal_history[-self.config.max_history_size:]

        # 檢查信號劣化
        self._check_signal_degradation(signal_result)

    def monitor_signal_degradation(self, signal_results: List[SignalQualityResult]) -> SignalDegradationReport:
        """監控信號劣化"""
        degradation_events = []

        for result in signal_results:
            # 檢查RSRP劣化
            if result.rsrp_dbm < self.signal_thresholds['rsrp_critical']:
                degradation_events.append(
                    SignalDegradationEvent(
                        satellite_id=result.satellite_id,
                        metric_type="RSRP",
                        current_value=result.rsrp_dbm,
                        threshold=self.signal_thresholds['rsrp_critical'],
                        severity="CRITICAL"
                    )
                )
            elif result.rsrp_dbm < self.signal_thresholds['rsrp_warning']:
                degradation_events.append(
                    SignalDegradationEvent(
                        satellite_id=result.satellite_id,
                        metric_type="RSRP",
                        current_value=result.rsrp_dbm,
                        threshold=self.signal_thresholds['rsrp_warning'],
                        severity="WARNING"
                    )
                )

            # 檢查RSRQ劣化
            if result.rsrq_db < self.signal_thresholds['rsrq_critical']:
                degradation_events.append(
                    SignalDegradationEvent(
                        satellite_id=result.satellite_id,
                        metric_type="RSRQ",
                        current_value=result.rsrq_db,
                        threshold=self.signal_thresholds['rsrq_critical'],
                        severity="CRITICAL"
                    )
                )

            # 檢查SINR劣化
            if result.sinr_db < self.signal_thresholds['sinr_critical']:
                degradation_events.append(
                    SignalDegradationEvent(
                        satellite_id=result.satellite_id,
                        metric_type="SINR",
                        current_value=result.sinr_db,
                        threshold=self.signal_thresholds['sinr_critical'],
                        severity="CRITICAL"
                    )
                )

        # 計算整體健康評分
        overall_health_score = self._calculate_signal_health_score(signal_results)

        return SignalDegradationReport(
            timestamp=datetime.now(),
            total_satellites_monitored=len(signal_results),
            degradation_events=degradation_events,
            overall_health_score=overall_health_score
        )

    def track_signal_trends(self, time_window: timedelta) -> SignalTrendAnalysis:
        """追蹤信號趨勢"""
        cutoff_time = datetime.now() - time_window
        recent_signals = [s for s in self.signal_history if s.timestamp >= cutoff_time]

        if len(recent_signals) < 2:
            return SignalTrendAnalysis(
                time_window=time_window,
                trend_direction="stable",
                average_rsrp=0.0,
                rsrp_variance=0.0,
                degradation_probability=0.0
            )

        # 計算RSRP趨勢
        rsrp_values = [s.rsrp_dbm for s in recent_signals]
        average_rsrp = sum(rsrp_values) / len(rsrp_values)

        # 計算變異數
        rsrp_variance = sum((x - average_rsrp) ** 2 for x in rsrp_values) / len(rsrp_values)

        # 判斷趨勢方向
        if len(rsrp_values) >= 3:
            recent_avg = sum(rsrp_values[-3:]) / 3
            early_avg = sum(rsrp_values[:3]) / 3

            if recent_avg > early_avg + 2.0:  # 改善2dBm以上
                trend_direction = "improving"
            elif recent_avg < early_avg - 2.0:  # 劣化2dBm以上
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"

        # 計算劣化概率
        degradation_probability = self._calculate_degradation_probability(rsrp_values)

        return SignalTrendAnalysis(
            time_window=time_window,
            trend_direction=trend_direction,
            average_rsrp=average_rsrp,
            rsrp_variance=rsrp_variance,
            degradation_probability=degradation_probability
        )

    def _collect_rsrp_metrics(self, signals: List[SignalQualityResult]) -> List[MonitoringMetric]:
        """收集RSRP指標"""
        metrics = []

        if signals:
            rsrp_values = [s.rsrp_dbm for s in signals]
            avg_rsrp = sum(rsrp_values) / len(rsrp_values)
            min_rsrp = min(rsrp_values)
            max_rsrp = max(rsrp_values)

            metrics.append(MonitoringMetric(
                metric_name="rsrp_average",
                value=avg_rsrp,
                unit="dBm",
                timestamp=datetime.now(),
                tags={"type": "signal_quality", "metric": "rsrp"},
                threshold_warning=self.signal_thresholds['rsrp_warning'],
                threshold_critical=self.signal_thresholds['rsrp_critical']
            ))

            metrics.append(MonitoringMetric(
                metric_name="rsrp_minimum",
                value=min_rsrp,
                unit="dBm",
                timestamp=datetime.now(),
                tags={"type": "signal_quality", "metric": "rsrp"},
                threshold_critical=self.signal_thresholds['rsrp_critical']
            ))

        return metrics

    def _collect_rsrq_metrics(self, signals: List[SignalQualityResult]) -> List[MonitoringMetric]:
        """收集RSRQ指標"""
        metrics = []

        if signals:
            rsrq_values = [s.rsrq_db for s in signals]
            avg_rsrq = sum(rsrq_values) / len(rsrq_values)

            metrics.append(MonitoringMetric(
                metric_name="rsrq_average",
                value=avg_rsrq,
                unit="dB",
                timestamp=datetime.now(),
                tags={"type": "signal_quality", "metric": "rsrq"},
                threshold_warning=self.signal_thresholds['rsrq_warning'],
                threshold_critical=self.signal_thresholds['rsrq_critical']
            ))

        return metrics

    def _collect_sinr_metrics(self, signals: List[SignalQualityResult]) -> List[MonitoringMetric]:
        """收集SINR指標"""
        metrics = []

        if signals:
            sinr_values = [s.sinr_db for s in signals]
            avg_sinr = sum(sinr_values) / len(sinr_values)

            metrics.append(MonitoringMetric(
                metric_name="sinr_average",
                value=avg_sinr,
                unit="dB",
                timestamp=datetime.now(),
                tags={"type": "signal_quality", "metric": "sinr"},
                threshold_warning=self.signal_thresholds['sinr_warning'],
                threshold_critical=self.signal_thresholds['sinr_critical']
            ))

        return metrics

    def _get_recent_signals(self, time_window: timedelta) -> List[SignalQualityResult]:
        """獲取最近的信號數據"""
        cutoff_time = datetime.now() - time_window
        return [s for s in self.signal_history if s.timestamp >= cutoff_time]

    def _check_signal_degradation(self, signal_result: SignalQualityResult):
        """檢查單個信號是否劣化"""
        events = []

        # 檢查RSRP
        if signal_result.rsrp_dbm < self.signal_thresholds['rsrp_critical']:
            events.append(SignalDegradationEvent(
                satellite_id=signal_result.satellite_id,
                metric_type="RSRP",
                current_value=signal_result.rsrp_dbm,
                threshold=self.signal_thresholds['rsrp_critical'],
                severity="CRITICAL"
            ))

        self.degradation_events.extend(events)

    def _calculate_signal_health_score(self, signals: List[SignalQualityResult]) -> float:
        """計算整體信號健康評分"""
        if not signals:
            return 0.0

        total_score = 0.0
        for signal in signals:
            # RSRP評分 (40%)
            rsrp_score = self._normalize_rsrp_score(signal.rsrp_dbm)

            # RSRQ評分 (30%)
            rsrq_score = self._normalize_rsrq_score(signal.rsrq_db)

            # SINR評分 (30%)
            sinr_score = self._normalize_sinr_score(signal.sinr_db)

            signal_score = 0.4 * rsrp_score + 0.3 * rsrq_score + 0.3 * sinr_score
            total_score += signal_score

        return total_score / len(signals)

    def _normalize_rsrp_score(self, rsrp: float) -> float:
        """正規化RSRP評分 (0-1)"""
        if rsrp >= -70:
            return 1.0
        elif rsrp >= -85:
            return 0.8
        elif rsrp >= -100:
            return 0.6
        elif rsrp >= -110:
            return 0.3
        else:
            return 0.0

    def _normalize_rsrq_score(self, rsrq: float) -> float:
        """正規化RSRQ評分 (0-1)"""
        if rsrq >= -10:
            return 1.0
        elif rsrq >= -15:
            return 0.8
        elif rsrq >= -20:
            return 0.6
        else:
            return 0.3

    def _normalize_sinr_score(self, sinr: float) -> float:
        """正規化SINR評分 (0-1)"""
        if sinr >= 20:
            return 1.0
        elif sinr >= 13:
            return 0.8
        elif sinr >= 3:
            return 0.6
        elif sinr >= 0:
            return 0.3
        else:
            return 0.0

    def _calculate_degradation_probability(self, rsrp_values: List[float]) -> float:
        """計算劣化概率"""
        if len(rsrp_values) < 3:
            return 0.0

        # 基於最近的趨勢計算劣化概率
        recent_values = rsrp_values[-3:]
        if len(recent_values) >= 2:
            trend = recent_values[-1] - recent_values[0]
            if trend < -5:  # 快速劣化
                return 0.8
            elif trend < -2:  # 輕微劣化
                return 0.4
            else:
                return 0.1

        return 0.0