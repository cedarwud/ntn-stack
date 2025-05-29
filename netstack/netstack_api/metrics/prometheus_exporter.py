#!/usr/bin/env python3
"""
Prometheus 指標導出器

為 UAV-衛星連接質量評估系統提供 Prometheus 指標
"""

from prometheus_client import (
    Gauge,
    Counter,
    Histogram,
    Enum,
    CollectorRegistry,
    generate_latest,
)
from typing import Dict, List, Optional
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class UAVSatelliteMetricsExporter:
    """UAV-衛星連接質量 Prometheus 指標導出器"""

    def __init__(self):
        # 創建自定義註冊表
        self.registry = CollectorRegistry()

        # 系統概覽指標
        self.monitored_uav_count = Gauge(
            "uav_satellite_monitored_count",
            "Number of UAVs being monitored for connection quality",
            registry=self.registry,
        )

        # 信號質量指標
        self.rsrp_dbm = Gauge(
            "uav_satellite_rsrp_dbm",
            "RSRP signal strength in dBm",
            ["uav_id"],
            registry=self.registry,
        )

        self.rsrq_db = Gauge(
            "uav_satellite_rsrq_db",
            "RSRQ signal quality in dB",
            ["uav_id"],
            registry=self.registry,
        )

        self.sinr_db = Gauge(
            "uav_satellite_sinr_db",
            "SINR signal-to-interference-noise ratio in dB",
            ["uav_id"],
            registry=self.registry,
        )

        self.cqi = Gauge(
            "uav_satellite_cqi",
            "Channel Quality Indicator",
            ["uav_id"],
            registry=self.registry,
        )

        # 性能指標
        self.throughput_mbps = Gauge(
            "uav_satellite_throughput_mbps",
            "Throughput in Mbps",
            ["uav_id"],
            registry=self.registry,
        )

        self.latency_ms = Gauge(
            "uav_satellite_latency_ms",
            "End-to-end latency in milliseconds",
            ["uav_id"],
            registry=self.registry,
        )

        self.jitter_ms = Gauge(
            "uav_satellite_jitter_ms",
            "Jitter in milliseconds",
            ["uav_id"],
            registry=self.registry,
        )

        self.packet_loss_rate = Gauge(
            "uav_satellite_packet_loss_rate",
            "Packet loss rate (0-1)",
            ["uav_id"],
            registry=self.registry,
        )

        # 質量評分指標
        self.overall_quality_score = Gauge(
            "uav_satellite_overall_quality_score",
            "Overall connection quality score (0-100)",
            ["uav_id"],
            registry=self.registry,
        )

        self.signal_quality_score = Gauge(
            "uav_satellite_signal_quality_score",
            "Signal quality score (0-100)",
            ["uav_id"],
            registry=self.registry,
        )

        self.performance_score = Gauge(
            "uav_satellite_performance_score",
            "Performance score (0-100)",
            ["uav_id"],
            registry=self.registry,
        )

        self.stability_score = Gauge(
            "uav_satellite_stability_score",
            "Stability score (0-100)",
            ["uav_id"],
            registry=self.registry,
        )

        self.ntn_adaptation_score = Gauge(
            "uav_satellite_ntn_adaptation_score",
            "NTN adaptation score (0-100)",
            ["uav_id"],
            registry=self.registry,
        )

        # 擴展指標
        self.link_budget_margin_db = Gauge(
            "uav_satellite_link_budget_margin_db",
            "Link budget margin in dB",
            ["uav_id"],
            registry=self.registry,
        )

        self.doppler_shift_hz = Gauge(
            "uav_satellite_doppler_shift_hz",
            "Doppler shift in Hz",
            ["uav_id"],
            registry=self.registry,
        )

        self.beam_alignment_score = Gauge(
            "uav_satellite_beam_alignment_score",
            "Beam alignment score (0-1)",
            ["uav_id"],
            registry=self.registry,
        )

        self.interference_level_db = Gauge(
            "uav_satellite_interference_level_db",
            "Interference level in dB",
            ["uav_id"],
            registry=self.registry,
        )

        # 質量分佈指標
        self.quality_distribution = Gauge(
            "uav_satellite_quality_distribution",
            "Distribution of UAVs by quality grade",
            ["quality_grade"],
            registry=self.registry,
        )

        # 異常指標
        self.anomaly_count = Counter(
            "uav_satellite_anomaly_total",
            "Total number of anomalies detected",
            ["uav_id", "anomaly_type", "severity"],
            registry=self.registry,
        )

        # 評估延遲指標
        self.assessment_duration = Histogram(
            "uav_satellite_assessment_duration_seconds",
            "Time taken to perform quality assessment",
            ["uav_id"],
            registry=self.registry,
        )

        # 位置信息指標
        self.position_latitude = Gauge(
            "uav_satellite_position_latitude",
            "UAV latitude position",
            ["uav_id"],
            registry=self.registry,
        )

        self.position_longitude = Gauge(
            "uav_satellite_position_longitude",
            "UAV longitude position",
            ["uav_id"],
            registry=self.registry,
        )

        self.position_altitude = Gauge(
            "uav_satellite_position_altitude",
            "UAV altitude in meters",
            ["uav_id"],
            registry=self.registry,
        )

        # 數據新鮮度指標
        self.data_freshness_score = Gauge(
            "uav_satellite_data_freshness_score",
            "Data freshness score (0-1)",
            ["uav_id"],
            registry=self.registry,
        )

        # 初始化質量分佈計數器
        self._init_quality_distribution()

        logger.info("UAV-衛星連接質量 Prometheus 指標導出器已初始化")

    def _init_quality_distribution(self):
        """初始化質量分佈指標"""
        quality_grades = ["優秀", "良好", "一般", "差"]
        for grade in quality_grades:
            self.quality_distribution.labels(quality_grade=grade).set(0)

    def update_signal_metrics(self, uav_id: str, signal_quality: Dict):
        """更新信號質量指標"""
        try:
            if signal_quality.get("rsrp_dbm") is not None:
                self.rsrp_dbm.labels(uav_id=uav_id).set(signal_quality["rsrp_dbm"])

            if signal_quality.get("rsrq_db") is not None:
                self.rsrq_db.labels(uav_id=uav_id).set(signal_quality["rsrq_db"])

            if signal_quality.get("sinr_db") is not None:
                self.sinr_db.labels(uav_id=uav_id).set(signal_quality["sinr_db"])

            if signal_quality.get("cqi") is not None:
                self.cqi.labels(uav_id=uav_id).set(signal_quality["cqi"])

            if signal_quality.get("throughput_mbps") is not None:
                self.throughput_mbps.labels(uav_id=uav_id).set(
                    signal_quality["throughput_mbps"]
                )

            if signal_quality.get("latency_ms") is not None:
                self.latency_ms.labels(uav_id=uav_id).set(signal_quality["latency_ms"])

            if signal_quality.get("jitter_ms") is not None:
                self.jitter_ms.labels(uav_id=uav_id).set(signal_quality["jitter_ms"])

            if signal_quality.get("packet_loss_rate") is not None:
                self.packet_loss_rate.labels(uav_id=uav_id).set(
                    signal_quality["packet_loss_rate"]
                )

            # 擴展指標
            if signal_quality.get("link_budget_margin_db") is not None:
                self.link_budget_margin_db.labels(uav_id=uav_id).set(
                    signal_quality["link_budget_margin_db"]
                )

            if signal_quality.get("doppler_shift_hz") is not None:
                self.doppler_shift_hz.labels(uav_id=uav_id).set(
                    signal_quality["doppler_shift_hz"]
                )

            if signal_quality.get("beam_alignment_score") is not None:
                self.beam_alignment_score.labels(uav_id=uav_id).set(
                    signal_quality["beam_alignment_score"]
                )

            if signal_quality.get("interference_level_db") is not None:
                self.interference_level_db.labels(uav_id=uav_id).set(
                    signal_quality["interference_level_db"]
                )

            if signal_quality.get("data_freshness_score") is not None:
                self.data_freshness_score.labels(uav_id=uav_id).set(
                    signal_quality["data_freshness_score"]
                )

        except Exception as e:
            logger.error(f"更新信號指標失敗: {e}", uav_id=uav_id)

    def update_quality_assessment(self, uav_id: str, assessment: Dict):
        """更新質量評估指標"""
        try:
            if assessment.get("overall_quality_score") is not None:
                self.overall_quality_score.labels(uav_id=uav_id).set(
                    assessment["overall_quality_score"]
                )

            if assessment.get("signal_quality_score") is not None:
                self.signal_quality_score.labels(uav_id=uav_id).set(
                    assessment["signal_quality_score"]
                )

            if assessment.get("performance_score") is not None:
                self.performance_score.labels(uav_id=uav_id).set(
                    assessment["performance_score"]
                )

            if assessment.get("stability_score") is not None:
                self.stability_score.labels(uav_id=uav_id).set(
                    assessment["stability_score"]
                )

            if assessment.get("ntn_adaptation_score") is not None:
                self.ntn_adaptation_score.labels(uav_id=uav_id).set(
                    assessment["ntn_adaptation_score"]
                )

        except Exception as e:
            logger.error(f"更新質量評估指標失敗: {e}", uav_id=uav_id)

    def update_position_metrics(self, uav_id: str, position: Dict):
        """更新位置指標"""
        try:
            if position.get("latitude") is not None:
                self.position_latitude.labels(uav_id=uav_id).set(position["latitude"])

            if position.get("longitude") is not None:
                self.position_longitude.labels(uav_id=uav_id).set(position["longitude"])

            if position.get("altitude") is not None:
                self.position_altitude.labels(uav_id=uav_id).set(position["altitude"])

        except Exception as e:
            logger.error(f"更新位置指標失敗: {e}", uav_id=uav_id)

    def record_anomaly(self, uav_id: str, anomaly_type: str, severity: str):
        """記錄異常事件"""
        try:
            self.anomaly_count.labels(
                uav_id=uav_id, anomaly_type=anomaly_type, severity=severity
            ).inc()
        except Exception as e:
            logger.error(f"記錄異常指標失敗: {e}", uav_id=uav_id)

    def record_assessment_duration(self, uav_id: str, duration: float):
        """記錄評估耗時"""
        try:
            self.assessment_duration.labels(uav_id=uav_id).observe(duration)
        except Exception as e:
            logger.error(f"記錄評估耗時失敗: {e}", uav_id=uav_id)

    def update_monitored_count(self, count: int):
        """更新監控 UAV 數量"""
        try:
            self.monitored_uav_count.set(count)
        except Exception as e:
            logger.error(f"更新監控數量失敗: {e}")

    def update_quality_distribution(self, distribution: Dict[str, int]):
        """更新質量分佈"""
        try:
            for grade, count in distribution.items():
                self.quality_distribution.labels(quality_grade=grade).set(count)
        except Exception as e:
            logger.error(f"更新質量分佈失敗: {e}")

    def clear_uav_metrics(self, uav_id: str):
        """清除特定 UAV 的指標"""
        try:
            # 清除所有與該 UAV 相關的指標
            metric_gauges = [
                self.rsrp_dbm,
                self.rsrq_db,
                self.sinr_db,
                self.cqi,
                self.throughput_mbps,
                self.latency_ms,
                self.jitter_ms,
                self.packet_loss_rate,
                self.overall_quality_score,
                self.signal_quality_score,
                self.performance_score,
                self.stability_score,
                self.ntn_adaptation_score,
                self.link_budget_margin_db,
                self.doppler_shift_hz,
                self.beam_alignment_score,
                self.interference_level_db,
                self.position_latitude,
                self.position_longitude,
                self.position_altitude,
                self.data_freshness_score,
            ]

            for gauge in metric_gauges:
                try:
                    gauge.remove(uav_id)
                except KeyError:
                    pass  # 標籤可能不存在

        except Exception as e:
            logger.error(f"清除 UAV 指標失敗: {e}", uav_id=uav_id)

    def get_metrics(self) -> str:
        """獲取 Prometheus 格式的指標數據"""
        return generate_latest(self.registry)

    def get_registry(self):
        """獲取 Prometheus 註冊表"""
        return self.registry


# 全局單例實例
metrics_exporter = UAVSatelliteMetricsExporter()
