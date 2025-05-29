#!/usr/bin/env python3
"""
UAV-衛星連接質量評估服務

實現綜合的連接質量監測、評估和預測功能
"""

import asyncio
import statistics
import numpy as np
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
import time

import structlog

from ..models.uav_models import (
    UAVConnectionQualityMetrics,
    ConnectionQualityAssessment,
    ConnectionQualityHistoricalData,
    ConnectionQualityThresholds,
    UAVSignalQuality,
    UAVPosition,
)
from ..adapters.mongo_adapter import MongoAdapter
from ..metrics.prometheus_exporter import metrics_exporter


logger = structlog.get_logger(__name__)


class ConnectionQualityService:
    """連接質量評估服務"""

    def __init__(self, mongo_adapter: MongoAdapter):
        self.mongo_adapter = mongo_adapter
        self.thresholds = ConnectionQualityThresholds()

        # 實時數據緩存
        self._cache_size = 100  # 保留最近 100 個測量點
        self._quality_cache: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self._cache_size)
        )

        # 異常檢測參數
        self._anomaly_detection_window = 20  # 異常檢測窗口大小
        self._quality_trend_window = 10  # 趨勢分析窗口大小

        # 評估任務
        self._assessment_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()

    async def start_monitoring(self, uav_id: str, assessment_interval: int = 30):
        """開始連接質量監控"""
        if uav_id in self._assessment_tasks:
            logger.warning("UAV 質量監控已在運行", uav_id=uav_id)
            return

        # 創建監控任務
        task = asyncio.create_task(
            self._continuous_assessment_loop(uav_id, assessment_interval)
        )
        self._assessment_tasks[uav_id] = task

        logger.info(
            "開始 UAV 連接質量監控", uav_id=uav_id, interval=assessment_interval
        )

    async def stop_monitoring(self, uav_id: str):
        """停止連接質量監控"""
        if uav_id in self._assessment_tasks:
            task = self._assessment_tasks[uav_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._assessment_tasks[uav_id]

        logger.info("停止 UAV 連接質量監控", uav_id=uav_id)

    async def update_signal_quality(
        self,
        uav_id: str,
        signal_quality: UAVSignalQuality,
        position: Optional[UAVPosition] = None,
    ) -> UAVConnectionQualityMetrics:
        """更新 UAV 信號質量數據"""
        try:
            timestamp = datetime.now(UTC)

            # 轉換為質量指標
            quality_metrics = self._convert_to_quality_metrics(signal_quality)

            # 儲存到緩存
            if uav_id not in self._quality_cache:
                self._quality_cache[uav_id] = deque(maxlen=self._cache_size)

            self._quality_cache[uav_id].append(
                {
                    "timestamp": timestamp,
                    "metrics": quality_metrics,
                    "position": position.dict() if position else None,
                }
            )

            # 儲存到數據庫
            await self._store_quality_data(uav_id, quality_metrics, position)

            # 更新 Prometheus 指標
            self._update_prometheus_metrics(uav_id, signal_quality, position)

            # 檢測異常（僅儲存到緩存，異常檢測通過 detect_anomalies 公共方法執行）
            try:
                await self._detect_anomalies_internal(uav_id, quality_metrics)
            except Exception as e:
                logger.warning("異常檢測失敗", uav_id=uav_id, error=str(e))

            logger.debug("信號質量已更新", uav_id=uav_id)
            return quality_metrics

        except Exception as e:
            logger.error("更新信號質量失敗", uav_id=uav_id, error=str(e))
            raise

    def _update_prometheus_metrics(
        self,
        uav_id: str,
        signal_quality: UAVSignalQuality,
        position: Optional[UAVPosition] = None,
    ):
        """更新 Prometheus 指標"""
        try:
            # 更新信號質量指標
            signal_dict = signal_quality.dict()
            metrics_exporter.update_signal_metrics(uav_id, signal_dict)

            # 更新位置指標
            if position:
                position_dict = position.dict()
                metrics_exporter.update_position_metrics(uav_id, position_dict)

            # 更新監控數量
            monitored_count = len(self._quality_cache)
            metrics_exporter.update_monitored_count(monitored_count)

        except Exception as e:
            logger.error("更新 Prometheus 指標失敗", uav_id=uav_id, error=str(e))

    async def assess_connection_quality(
        self, uav_id: str, time_window_minutes: int = 5
    ) -> ConnectionQualityAssessment:
        """評估 UAV 連接質量"""
        start_time = time.time()

        try:
            # 獲取時間窗口內的數據
            end_time = datetime.now(UTC)
            start_time_dt = end_time - timedelta(minutes=time_window_minutes)

            # 從緩存中獲取數據
            recent_data = self._get_cached_data_in_window(
                uav_id, start_time_dt, end_time
            )

            if not recent_data:
                logger.warning("無可用數據進行質量評估", uav_id=uav_id)
                return self._create_default_assessment(uav_id)

            # 執行評估算法
            assessment = await self._perform_quality_assessment(uav_id, recent_data)

            # 更新 Prometheus 指標
            assessment_dict = assessment.dict()
            metrics_exporter.update_quality_assessment(uav_id, assessment_dict)

            # 記錄評估耗時
            duration = time.time() - start_time
            metrics_exporter.record_assessment_duration(uav_id, duration)

            return assessment

        except Exception as e:
            logger.error("質量評估失敗", uav_id=uav_id, error=str(e))
            duration = time.time() - start_time
            metrics_exporter.record_assessment_duration(uav_id, duration)
            raise

    async def get_quality_history(
        self, uav_id: str, hours: int = 24
    ) -> ConnectionQualityHistoricalData:
        """獲取連接質量歷史數據"""

        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours)

        # 獲取指標數據
        metrics_data = await self._get_historical_metrics(uav_id, start_time, end_time)

        # 獲取評估歷史
        assessments = await self._get_historical_assessments(
            uav_id, start_time, end_time
        )

        # 獲取異常事件
        anomaly_events = await self._get_anomaly_events(uav_id, start_time, end_time)

        # 計算統計摘要
        metrics_summary = await self._calculate_metrics_summary(metrics_data)

        return ConnectionQualityHistoricalData(
            uav_id=uav_id,
            start_time=start_time,
            end_time=end_time,
            sample_count=len(metrics_data),
            metrics_summary=metrics_summary,
            quality_assessments=assessments,
            anomaly_events=anomaly_events,
        )

    async def detect_anomalies(self, uav_id: str) -> List[Dict[str, Any]]:
        """檢測連接質量異常"""

        cached_data = list(self._quality_cache.get(uav_id, []))
        if len(cached_data) < self._anomaly_detection_window:
            return []

        anomalies = []
        recent_data = cached_data[-self._anomaly_detection_window :]

        # 檢測各指標異常
        anomalies.extend(await self._detect_signal_anomalies(recent_data))
        anomalies.extend(await self._detect_performance_anomalies(recent_data))
        anomalies.extend(await self._detect_stability_anomalies(recent_data))

        # 保存異常事件
        for anomaly in anomalies:
            await self._save_anomaly_event(uav_id, anomaly)

        return anomalies

    async def update_thresholds(self, new_thresholds: ConnectionQualityThresholds):
        """更新質量評估閾值"""
        self.thresholds = new_thresholds
        logger.info("更新連接質量評估閾值")

    async def _build_quality_metrics(
        self,
        uav_id: str,
        signal_quality: UAVSignalQuality,
        position: Optional[UAVPosition],
    ) -> UAVConnectionQualityMetrics:
        """構建連接質量指標"""

        # 基礎信號指標
        metrics = UAVConnectionQualityMetrics(
            sinr_db=signal_quality.sinr_db,
            rsrp_dbm=signal_quality.rsrp_dbm,
            rsrq_db=signal_quality.rsrq_db,
            cqi=signal_quality.cqi,
            throughput_mbps=signal_quality.throughput_mbps,
            latency_ms=signal_quality.latency_ms,
            packet_loss_rate=signal_quality.packet_loss_rate,
            jitter_ms=signal_quality.jitter_ms,
            link_budget_margin_db=signal_quality.link_budget_margin_db,
            doppler_shift_hz=signal_quality.doppler_shift_hz,
        )

        # 計算連接穩定性指標
        if uav_id in self._quality_cache and len(self._quality_cache[uav_id]) > 1:
            recent_data = list(self._quality_cache[uav_id])[-10:]  # 最近 10 個樣本

            # 連接正常時間百分比
            good_signals = sum(
                1
                for item in recent_data
                if item["metrics"].sinr_db and item["metrics"].sinr_db > 0
            )
            metrics.connection_uptime_percent = (good_signals / len(recent_data)) * 100

            # 信號穩定性評分
            if len(recent_data) >= 5:
                sinr_values = [
                    item["metrics"].sinr_db
                    for item in recent_data
                    if item["metrics"].sinr_db is not None
                ]
                if sinr_values:
                    sinr_std = (
                        statistics.stdev(sinr_values) if len(sinr_values) > 1 else 0
                    )
                    metrics.signal_stability_score = max(
                        0, 1 - sinr_std / 20
                    )  # 標準化到 0-1

        # NTN 特有指標
        if position:
            # 基於高度和位置計算傳播延遲
            if position.altitude:
                # 簡化的傳播延遲計算（假設衛星高度 550km）
                satellite_height_km = 550
                total_distance_km = (
                    (position.altitude / 1000) ** 2 + satellite_height_km**2
                ) ** 0.5
                metrics.propagation_delay_ms = (
                    (total_distance_km * 1000) / 299792458 * 1000
                )  # 光速傳播

            # 波束對準品質（簡化模型）
            if position.altitude and position.altitude > 100:
                # 高度越高，對準越困難
                alignment_factor = max(0, 1 - (position.altitude - 100) / 10000)
                metrics.beam_alignment_quality = alignment_factor

        # 數據新鮮度評分
        now = datetime.now(UTC)
        time_diff = (now - signal_quality.timestamp).total_seconds()
        metrics.data_freshness_score = max(0, 1 - time_diff / 60)  # 1分鐘內為新鮮

        return metrics

    async def _assess_signal_quality(
        self, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> float:
        """評估信號質量"""
        if not metrics_data:
            return 0.0

        scores = []

        for metrics in metrics_data:
            score = 0.0
            components = 0

            # SINR 評分
            if metrics.sinr_db is not None:
                if metrics.sinr_db >= self.thresholds.sinr_excellent_db:
                    score += 100
                elif metrics.sinr_db >= self.thresholds.sinr_good_db:
                    score += 70
                elif metrics.sinr_db >= self.thresholds.sinr_poor_db:
                    score += 40
                else:
                    score += 10
                components += 1

            # RSRP 評分
            if metrics.rsrp_dbm is not None:
                if metrics.rsrp_dbm >= self.thresholds.rsrp_excellent_dbm:
                    score += 100
                elif metrics.rsrp_dbm >= self.thresholds.rsrp_good_dbm:
                    score += 70
                elif metrics.rsrp_dbm >= self.thresholds.rsrp_poor_dbm:
                    score += 40
                else:
                    score += 10
                components += 1

            # CQI 評分
            if metrics.cqi is not None:
                cqi_score = (metrics.cqi / 15) * 100  # CQI 0-15 映射到 0-100
                score += cqi_score
                components += 1

            if components > 0:
                scores.append(score / components)

        return statistics.mean(scores) if scores else 0.0

    async def _assess_performance(
        self, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> float:
        """評估性能"""
        if not metrics_data:
            return 0.0

        scores = []

        for metrics in metrics_data:
            score = 0.0
            components = 0

            # 吞吐量評分
            if metrics.throughput_mbps is not None:
                if metrics.throughput_mbps >= self.thresholds.throughput_excellent_mbps:
                    score += 100
                elif metrics.throughput_mbps >= self.thresholds.throughput_good_mbps:
                    score += 70
                elif metrics.throughput_mbps >= self.thresholds.throughput_poor_mbps:
                    score += 40
                else:
                    score += 10
                components += 1

            # 延遲評分
            if metrics.latency_ms is not None:
                if metrics.latency_ms <= self.thresholds.latency_excellent_ms:
                    score += 100
                elif metrics.latency_ms <= self.thresholds.latency_good_ms:
                    score += 70
                elif metrics.latency_ms <= self.thresholds.latency_poor_ms:
                    score += 40
                else:
                    score += 10
                components += 1

            # 丟包率評分
            if metrics.packet_loss_rate is not None:
                if metrics.packet_loss_rate <= self.thresholds.packet_loss_excellent:
                    score += 100
                elif metrics.packet_loss_rate <= self.thresholds.packet_loss_good:
                    score += 70
                elif metrics.packet_loss_rate <= self.thresholds.packet_loss_poor:
                    score += 40
                else:
                    score += 10
                components += 1

            if components > 0:
                scores.append(score / components)

        return statistics.mean(scores) if scores else 0.0

    async def _assess_stability(
        self, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> float:
        """評估穩定性"""
        if len(metrics_data) < 2:
            return 100.0  # 數據不足，默認穩定

        # 計算各指標的變異性
        stability_scores = []

        # SINR 穩定性
        sinr_values = [m.sinr_db for m in metrics_data if m.sinr_db is not None]
        if len(sinr_values) > 1:
            sinr_cv = statistics.stdev(sinr_values) / statistics.mean(sinr_values)
            sinr_stability = max(0, 100 * (1 - sinr_cv))
            stability_scores.append(sinr_stability)

        # 吞吐量穩定性
        throughput_values = [
            m.throughput_mbps for m in metrics_data if m.throughput_mbps is not None
        ]
        if len(throughput_values) > 1:
            throughput_cv = statistics.stdev(throughput_values) / statistics.mean(
                throughput_values
            )
            throughput_stability = max(0, 100 * (1 - throughput_cv))
            stability_scores.append(throughput_stability)

        # 連接正常時間
        uptime_values = [
            m.connection_uptime_percent
            for m in metrics_data
            if m.connection_uptime_percent is not None
        ]
        if uptime_values:
            avg_uptime = statistics.mean(uptime_values)
            stability_scores.append(avg_uptime)

        return statistics.mean(stability_scores) if stability_scores else 100.0

    async def _assess_ntn_adaptation(
        self, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> float:
        """評估 NTN 適配"""
        if not metrics_data:
            return 0.0

        scores = []

        for metrics in metrics_data:
            score = 0.0
            components = 0

            # 鏈路餘裕評分
            if metrics.link_budget_margin_db is not None:
                if metrics.link_budget_margin_db >= 15:
                    score += 100
                elif metrics.link_budget_margin_db >= 10:
                    score += 70
                elif metrics.link_budget_margin_db >= 5:
                    score += 40
                else:
                    score += 10
                components += 1

            # 多普勒補償效果
            if metrics.doppler_shift_hz is not None:
                # 多普勒頻移越小說明補償越好
                doppler_score = max(
                    0, 100 * (1 - abs(metrics.doppler_shift_hz) / 10000)
                )
                score += doppler_score
                components += 1

            # 波束對準品質
            if metrics.beam_alignment_quality is not None:
                score += metrics.beam_alignment_quality * 100
                components += 1

            if components > 0:
                scores.append(score / components)

        return statistics.mean(scores) if scores else 0.0

    def _determine_quality_grade(self, score: float) -> str:
        """確定質量等級"""
        if score >= 85:
            return "優秀"
        elif score >= 70:
            return "良好"
        elif score >= 50:
            return "一般"
        else:
            return "差"

    async def _identify_issues(
        self, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> List[str]:
        """識別問題"""
        issues = []

        if not metrics_data:
            issues.append("缺少質量數據")
            return issues

        recent_metrics = metrics_data[-5:] if len(metrics_data) >= 5 else metrics_data

        # 檢查信號質量問題
        low_sinr_count = sum(
            1
            for m in recent_metrics
            if m.sinr_db is not None and m.sinr_db < self.thresholds.sinr_poor_db
        )
        if low_sinr_count >= len(recent_metrics) * 0.6:
            issues.append("SINR 過低")

        # 檢查性能問題
        low_throughput_count = sum(
            1
            for m in recent_metrics
            if m.throughput_mbps is not None
            and m.throughput_mbps < self.thresholds.throughput_poor_mbps
        )
        if low_throughput_count >= len(recent_metrics) * 0.6:
            issues.append("吞吐量不足")

        high_latency_count = sum(
            1
            for m in recent_metrics
            if m.latency_ms is not None
            and m.latency_ms > self.thresholds.latency_poor_ms
        )
        if high_latency_count >= len(recent_metrics) * 0.6:
            issues.append("延遲過高")

        # 檢查穩定性問題
        high_loss_count = sum(
            1
            for m in recent_metrics
            if m.packet_loss_rate is not None
            and m.packet_loss_rate > self.thresholds.packet_loss_poor
        )
        if high_loss_count >= len(recent_metrics) * 0.6:
            issues.append("丟包率過高")

        return issues

    async def _generate_recommendations(
        self, issues: List[str], metrics_data: List[UAVConnectionQualityMetrics]
    ) -> List[str]:
        """生成改善建議"""
        recommendations = []

        for issue in issues:
            if "SINR" in issue:
                recommendations.append("考慮調整天線方向或增加發射功率")
                recommendations.append("檢查是否存在干擾源")
            elif "吞吐量" in issue:
                recommendations.append("優化調製方案或降低數據速率要求")
                recommendations.append("檢查網絡擁塞情況")
            elif "延遲" in issue:
                recommendations.append("優化網絡路由或減少處理節點")
                recommendations.append("考慮使用低延遲的通信協議")
            elif "丟包" in issue:
                recommendations.append("增強錯誤檢測和重傳機制")
                recommendations.append("檢查網絡穩定性")

        # 通用建議
        if issues:
            recommendations.append("監控環境變化並及時調整參數")
            recommendations.append("考慮切換到備用通信鏈路")

        return recommendations

    async def _analyze_quality_trend(self, uav_id: str) -> Optional[str]:
        """分析質量趨勢"""
        cached_data = list(self._quality_cache.get(uav_id, []))

        if len(cached_data) < self._quality_trend_window:
            return "stable"  # 數據不足，假設穩定

        recent_data = cached_data[-self._quality_trend_window :]

        # 計算 SINR 趨勢
        sinr_values = [
            item["metrics"].sinr_db
            for item in recent_data
            if item["metrics"].sinr_db is not None
        ]

        if len(sinr_values) >= 3:
            # 簡單的線性趨勢檢測
            x = list(range(len(sinr_values)))
            slope = np.polyfit(x, sinr_values, 1)[0]

            if slope > 0.5:
                return "improving"
            elif slope < -0.5:
                return "degrading"

        return "stable"

    async def _predict_issues(
        self, uav_id: str, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> List[str]:
        """預測可能出現的問題"""
        predicted_issues = []

        if not metrics_data:
            return predicted_issues

        # 基於趨勢預測
        trend = await self._analyze_quality_trend(uav_id)

        if trend == "degrading":
            recent_metrics = (
                metrics_data[-3:] if len(metrics_data) >= 3 else metrics_data
            )

            # 檢查哪些指標在下降
            for i, metrics in enumerate(recent_metrics):
                if metrics.sinr_db is not None and metrics.sinr_db < 5:
                    predicted_issues.append("信號質量可能進一步惡化")
                    break

            for i, metrics in enumerate(recent_metrics):
                if metrics.throughput_mbps is not None and metrics.throughput_mbps < 10:
                    predicted_issues.append("吞吐量可能持續下降")
                    break

        return predicted_issues

    async def _calculate_assessment_confidence(
        self, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> float:
        """計算評估置信度"""
        if not metrics_data:
            return 0.0

        # 基於數據完整性和一致性
        confidence_factors = []

        # 數據量因子
        data_count_factor = min(1.0, len(metrics_data) / 10)  # 10個樣本為滿分
        confidence_factors.append(data_count_factor)

        # 數據新鮮度因子
        freshness_scores = [
            m.data_freshness_score
            for m in metrics_data
            if m.data_freshness_score is not None
        ]
        if freshness_scores:
            freshness_factor = statistics.mean(freshness_scores)
            confidence_factors.append(freshness_factor)

        # 測量置信度因子（如果有的話）
        measurement_confidences = [
            m.measurement_confidence
            for m in metrics_data
            if hasattr(m, "measurement_confidence")
            and m.measurement_confidence is not None
        ]
        if measurement_confidences:
            measurement_factor = statistics.mean(measurement_confidences)
            confidence_factors.append(measurement_factor)

        return statistics.mean(confidence_factors) if confidence_factors else 0.5

    async def _continuous_assessment_loop(self, uav_id: str, interval: int):
        """連續評估循環"""
        try:
            while not self._shutdown_event.is_set():
                await self.assess_connection_quality(uav_id)
                await self.detect_anomalies(uav_id)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("停止 UAV 連接質量評估循環", uav_id=uav_id)
        except Exception as e:
            logger.error("連接質量評估循環錯誤", uav_id=uav_id, error=str(e))

    # 數據庫操作方法
    async def _save_quality_data(
        self, uav_id: str, metrics: UAVConnectionQualityMetrics
    ):
        """保存質量數據到數據庫"""
        document = {
            "uav_id": uav_id,
            "metrics": metrics.dict(),
            "timestamp": datetime.now(UTC),
        }
        await self.mongo_adapter.insert_one("uav_connection_quality", document)

    async def _save_assessment(
        self, uav_id: str, assessment: ConnectionQualityAssessment
    ):
        """保存評估結果到數據庫"""
        document = {
            "uav_id": uav_id,
            "assessment": assessment.dict(),
            "timestamp": datetime.now(UTC),
        }
        await self.mongo_adapter.insert_one("uav_quality_assessments", document)

    async def _save_anomaly_event(self, uav_id: str, anomaly: Dict[str, Any]):
        """保存異常事件到數據庫"""
        document = {
            "uav_id": uav_id,
            "anomaly": anomaly,
            "timestamp": datetime.now(UTC),
        }
        await self.mongo_adapter.insert_one("uav_quality_anomalies", document)

    async def _get_historical_metrics(
        self, uav_id: str, start_time: datetime, end_time: datetime
    ) -> List[UAVConnectionQualityMetrics]:
        """獲取歷史指標數據"""
        query = {"uav_id": uav_id, "timestamp": {"$gte": start_time, "$lte": end_time}}

        documents = await self.mongo_adapter.find_many("uav_connection_quality", query)

        metrics_list = []
        for doc in documents:
            try:
                metrics = UAVConnectionQualityMetrics(**doc["metrics"])
                metrics_list.append(metrics)
            except Exception as e:
                logger.warning("解析歷史指標數據失敗", error=str(e))

        return metrics_list

    async def _get_historical_assessments(
        self, uav_id: str, start_time: datetime, end_time: datetime
    ) -> List[ConnectionQualityAssessment]:
        """獲取歷史評估數據"""
        query = {"uav_id": uav_id, "timestamp": {"$gte": start_time, "$lte": end_time}}

        documents = await self.mongo_adapter.find_many("uav_quality_assessments", query)

        assessments = []
        for doc in documents:
            try:
                assessment = ConnectionQualityAssessment(**doc["assessment"])
                assessments.append(assessment)
            except Exception as e:
                logger.warning("解析歷史評估數據失敗", error=str(e))

        return assessments

    async def _get_anomaly_events(
        self, uav_id: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """獲取異常事件"""
        query = {"uav_id": uav_id, "timestamp": {"$gte": start_time, "$lte": end_time}}

        documents = await self.mongo_adapter.find_many("uav_quality_anomalies", query)
        return [doc["anomaly"] for doc in documents]

    async def _calculate_metrics_summary(
        self, metrics_data: List[UAVConnectionQualityMetrics]
    ) -> Dict[str, Dict[str, float]]:
        """計算指標統計摘要"""
        if not metrics_data:
            return {}

        summary = {}

        # 定義要統計的指標
        metrics_fields = [
            "sinr_db",
            "rsrp_dbm",
            "rsrq_db",
            "throughput_mbps",
            "latency_ms",
            "packet_loss_rate",
            "jitter_ms",
        ]

        for field in metrics_fields:
            values = [
                getattr(m, field) for m in metrics_data if getattr(m, field) is not None
            ]

            if values:
                summary[field] = {
                    "mean": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                }

        return summary

    async def _detect_signal_anomalies(
        self, recent_data: List[Dict]
    ) -> List[Dict[str, Any]]:
        """檢測信號異常"""
        anomalies = []

        # 檢測 SINR 急劇下降
        sinr_values = [
            item["metrics"].sinr_db
            for item in recent_data
            if item["metrics"].sinr_db is not None
        ]

        if len(sinr_values) >= 5:
            recent_sinr = sinr_values[-5:]
            if max(recent_sinr) - min(recent_sinr) > 15:  # 15dB 差異
                anomalies.append(
                    {
                        "type": "signal_fluctuation",
                        "severity": "high",
                        "description": "SINR 劇烈波動",
                        "timestamp": datetime.now(UTC),
                    }
                )

        return anomalies

    async def _detect_performance_anomalies(
        self, recent_data: List[Dict]
    ) -> List[Dict[str, Any]]:
        """檢測性能異常"""
        anomalies = []

        # 檢測吞吐量突然下降
        throughput_values = [
            item["metrics"].throughput_mbps
            for item in recent_data
            if item["metrics"].throughput_mbps is not None
        ]

        if len(throughput_values) >= 3:
            recent_avg = statistics.mean(throughput_values[-3:])
            overall_avg = statistics.mean(throughput_values)

            if recent_avg < overall_avg * 0.5:  # 下降超過 50%
                anomalies.append(
                    {
                        "type": "throughput_drop",
                        "severity": "medium",
                        "description": "吞吐量急劇下降",
                        "timestamp": datetime.now(UTC),
                    }
                )

        return anomalies

    async def _detect_stability_anomalies(
        self, recent_data: List[Dict]
    ) -> List[Dict[str, Any]]:
        """檢測穩定性異常"""
        anomalies = []

        # 檢測連接中斷
        connection_issues = 0
        for item in recent_data:
            if (
                item["metrics"].connection_uptime_percent is not None
                and item["metrics"].connection_uptime_percent < 80
            ):
                connection_issues += 1

        if connection_issues >= len(recent_data) * 0.5:
            anomalies.append(
                {
                    "type": "connection_instability",
                    "severity": "high",
                    "description": "連接不穩定",
                    "timestamp": datetime.now(UTC),
                }
            )

        return anomalies

    async def shutdown(self):
        """關閉服務"""
        # 停止所有監控任務
        for task in self._assessment_tasks.values():
            if not task.done():
                task.cancel()
        self._assessment_tasks.clear()

        # 清理緩存
        self._quality_cache.clear()

        logger.info("連接質量評估服務已關閉")

    # ===== 新增的輔助方法 =====

    def _convert_to_quality_metrics(
        self, signal_quality: UAVSignalQuality
    ) -> UAVConnectionQualityMetrics:
        """轉換信號質量為連接質量指標"""
        # 計算數據新鮮度評分（基於當前時間）
        now = datetime.now(UTC)

        # 確保時間戳統一處理為 UTC aware datetime
        signal_timestamp = signal_quality.timestamp
        if signal_timestamp.tzinfo is None:
            # 如果沒有時區信息，假設是 UTC 時間
            signal_timestamp = signal_timestamp.replace(tzinfo=UTC)
        elif signal_timestamp.tzinfo != UTC:
            # 如果有其他時區信息，轉換為 UTC
            signal_timestamp = signal_timestamp.astimezone(UTC)

        time_diff = abs((now - signal_timestamp).total_seconds())
        # 確保新鮮度評分在 0-1 範圍內，1 分鐘內為新鮮
        data_freshness_score = max(0.0, min(1.0, 1.0 - time_diff / 60.0))

        # 基於位置或其他因素計算連接正常運行時間（模擬）
        connection_uptime_percent = min(
            100.0, max(0.0, 95.0 + (signal_quality.measurement_confidence or 0.9) * 5.0)
        )

        # 為了存儲，轉換為 naive datetime (去除時區信息)
        measurement_timestamp_naive = signal_timestamp.replace(tzinfo=None)

        return UAVConnectionQualityMetrics(
            sinr_db=signal_quality.sinr_db,
            rsrp_dbm=signal_quality.rsrp_dbm,
            rsrq_db=signal_quality.rsrq_db,
            cqi=signal_quality.cqi,
            throughput_mbps=signal_quality.throughput_mbps,
            latency_ms=signal_quality.latency_ms,
            jitter_ms=signal_quality.jitter_ms,
            packet_loss_rate=signal_quality.packet_loss_rate,
            connection_uptime_percent=connection_uptime_percent,
            handover_success_rate=0.95,  # 模擬值
            reconnection_count=0,  # 模擬值
            signal_stability_score=signal_quality.measurement_confidence or 0.9,
            doppler_shift_hz=signal_quality.doppler_shift_hz,
            propagation_delay_ms=signal_quality.latency_ms,  # 使用延遲作為傳播延遲的近似
            link_budget_margin_db=signal_quality.link_budget_margin_db,
            beam_alignment_quality=signal_quality.beam_alignment_score,
            measurement_timestamp=measurement_timestamp_naive,
            measurement_window_seconds=30,  # 默認測量窗口
            data_freshness_score=data_freshness_score,
        )

    async def _store_quality_data(
        self,
        uav_id: str,
        metrics: UAVConnectionQualityMetrics,
        position: Optional[UAVPosition] = None,
    ):
        """儲存質量數據到數據庫"""
        try:
            data = {
                "uav_id": uav_id,
                "metrics": metrics.dict(),
                "position": position.dict() if position else None,
                "timestamp": datetime.now(UTC),
            }
            await self.mongo_adapter.insert_one("uav_connection_quality", data)
        except Exception as e:
            logger.error("儲存質量數據失敗", uav_id=uav_id, error=str(e))

    def _get_cached_data_in_window(
        self, uav_id: str, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """從緩存中獲取時間窗口內的數據"""
        cached_data = list(self._quality_cache.get(uav_id, []))
        return [
            item for item in cached_data if start_time <= item["timestamp"] <= end_time
        ]

    async def _perform_quality_assessment(
        self, uav_id: str, recent_data: List[Dict]
    ) -> ConnectionQualityAssessment:
        """執行質量評估算法"""
        # 提取指標數據
        metrics_data = [item["metrics"] for item in recent_data]

        # 轉換為 UAVConnectionQualityMetrics 對象
        quality_metrics = []
        for metrics_dict in metrics_data:
            if isinstance(metrics_dict, dict):
                quality_metrics.append(UAVConnectionQualityMetrics(**metrics_dict))
            else:
                quality_metrics.append(metrics_dict)

        # 執行各維度評估
        signal_score = await self._assess_signal_quality(quality_metrics)
        performance_score = await self._assess_performance(quality_metrics)
        stability_score = await self._assess_stability(quality_metrics)
        ntn_score = await self._assess_ntn_adaptation(quality_metrics)

        # 計算綜合評分
        overall_score = (
            signal_score * self.thresholds.signal_weight
            + performance_score * self.thresholds.performance_weight
            + stability_score * self.thresholds.stability_weight
            + ntn_score * 0.1  # NTN 適配權重較小
        )

        # 確定質量等級
        quality_grade = self._determine_quality_grade(overall_score)

        # 問題識別和建議
        issues = await self._identify_issues(quality_metrics)
        recommendations = await self._generate_recommendations(issues, quality_metrics)

        # 趨勢分析
        quality_trend = await self._analyze_quality_trend(uav_id)
        predicted_issues = await self._predict_issues(uav_id, quality_metrics)

        # 評估置信度
        confidence = await self._calculate_assessment_confidence(quality_metrics)
        data_completeness = len(quality_metrics) / max(10, 1)  # 假設理想樣本數為 10

        assessment = ConnectionQualityAssessment(
            overall_quality_score=overall_score,
            quality_grade=quality_grade,
            signal_quality_score=signal_score,
            performance_score=performance_score,
            stability_score=stability_score,
            ntn_adaptation_score=ntn_score,
            identified_issues=issues,
            recommendations=recommendations,
            quality_trend=quality_trend,
            predicted_issues=predicted_issues,
            confidence_level=confidence,
            data_completeness=min(1.0, data_completeness),
        )

        # 保存評估結果
        await self._save_assessment(uav_id, assessment)

        logger.info(
            "完成連接質量評估",
            uav_id=uav_id,
            overall_score=f"{overall_score:.1f}",
            grade=quality_grade,
        )

        return assessment

    def _create_default_assessment(self, uav_id: str) -> ConnectionQualityAssessment:
        """創建默認評估結果"""
        return ConnectionQualityAssessment(
            overall_quality_score=0.0,
            quality_grade="數據不足",
            signal_quality_score=0.0,
            performance_score=0.0,
            stability_score=0.0,
            ntn_adaptation_score=0.0,
            identified_issues=["缺少質量數據"],
            recommendations=["開始收集信號質量數據"],
            quality_trend="unknown",
            predicted_issues=[],
            confidence_level=0.0,
            data_completeness=0.0,
        )

    async def get_system_overview(self) -> Dict[str, Any]:
        """獲取系統概覽"""
        try:
            monitored_uav_count = len(self._quality_cache)

            # 統計質量分佈
            quality_distribution = {"優秀": 0, "良好": 0, "一般": 0, "差": 0}

            # 獲取最近的評估結果
            assessments = []
            for uav_id in self._quality_cache.keys():
                try:
                    assessment = await self.assess_connection_quality(
                        uav_id, time_window_minutes=1
                    )
                    assessments.append(assessment)
                    if assessment.quality_grade in quality_distribution:
                        quality_distribution[assessment.quality_grade] += 1
                except:
                    pass

            return {
                "system_status": "運行中",
                "monitored_uav_count": monitored_uav_count,
                "assessment_capabilities": {
                    "signal_quality_assessment": True,
                    "performance_assessment": True,
                    "stability_assessment": True,
                    "ntn_adaptation_assessment": True,
                    "anomaly_detection": True,
                    "trend_analysis": True,
                    "predictive_analysis": True,
                },
                "supported_metrics": [
                    "SINR",
                    "RSRP",
                    "RSRQ",
                    "CQI",
                    "Throughput",
                    "Latency",
                    "Jitter",
                    "Packet Loss",
                    "Link Budget Margin",
                    "Doppler Shift",
                ],
                "evaluation_grades": ["優秀", "良好", "一般", "差"],
                "quality_distribution": quality_distribution,
                "last_update": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.error("獲取系統概覽失敗", error=str(e))
            return {"system_status": "錯誤", "monitored_uav_count": 0, "error": str(e)}

    async def _detect_anomalies_internal(
        self, uav_id: str, quality_metrics: UAVConnectionQualityMetrics
    ):
        """內部異常檢測方法（僅記錄，不存儲）"""
        try:
            # 檢查信號強度異常
            if quality_metrics.rsrp_dbm and quality_metrics.rsrp_dbm < -110:
                logger.debug(
                    "檢測到信號強度異常", uav_id=uav_id, rsrp=quality_metrics.rsrp_dbm
                )

            # 檢查延遲異常
            if quality_metrics.latency_ms and quality_metrics.latency_ms > 300:
                logger.debug(
                    "檢測到延遲異常", uav_id=uav_id, latency=quality_metrics.latency_ms
                )

            # 檢查丟包率異常
            if (
                quality_metrics.packet_loss_rate
                and quality_metrics.packet_loss_rate > 0.1
            ):
                logger.debug(
                    "檢測到丟包率異常",
                    uav_id=uav_id,
                    packet_loss=quality_metrics.packet_loss_rate,
                )

        except Exception as e:
            logger.warning("內部異常檢測失敗", uav_id=uav_id, error=str(e))
