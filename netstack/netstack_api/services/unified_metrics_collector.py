"""
統一指標收集服務

實現 TODO.md 第15項：可觀測性指標統一格式
統一收集來自不同組件的監控數據，確保指標格式一致性，簡化儀表板開發和維護
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
import psutil
import GPUtil
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
import yaml

from ..adapters.redis_adapter import RedisAdapter

logger = structlog.get_logger(__name__)


@dataclass
class MetricDefinition:
    """指標定義"""

    name: str
    metric_type: str  # counter, gauge, histogram, summary
    description: str
    unit: str
    labels: List[str]
    domain: str  # ntn, open5gs, ueransim, sionna, mesh, ai
    subsystem: str

    def get_full_name(self) -> str:
        """獲取完整指標名稱"""
        return f"{self.domain}_{self.subsystem}_{self.name}_{self.unit}"


@dataclass
class MetricValue:
    """指標值"""

    metric_name: str
    value: Union[float, int]
    labels: Dict[str, str]
    timestamp: float
    source_service: str


class MetricsRegistry:
    """指標註冊器"""

    def __init__(self):
        self.metrics: Dict[str, MetricDefinition] = {}
        self.prometheus_registry = CollectorRegistry()
        self.prometheus_metrics: Dict[str, Any] = {}

        # 載入標準指標定義
        self._load_standard_metrics()

    def _load_standard_metrics(self):
        """載入標準指標定義"""
        # NTN UAV 指標
        self.register_metric(
            MetricDefinition(
                name="latency",
                metric_type="histogram",
                description="UAV 端到端延遲",
                unit="ms",
                labels=["uav_id", "connection_type", "cell_id"],
                domain="ntn",
                subsystem="uav",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="sinr",
                metric_type="gauge",
                description="信號與干擾加噪聲比",
                unit="db",
                labels=["uav_id", "cell_id", "frequency_band"],
                domain="ntn",
                subsystem="uav",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="rsrp",
                metric_type="gauge",
                description="參考信號接收功率",
                unit="dbm",
                labels=["uav_id", "cell_id"],
                domain="ntn",
                subsystem="uav",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="connection_success",
                metric_type="counter",
                description="連接成功次數",
                unit="total",
                labels=["uav_id", "connection_type"],
                domain="ntn",
                subsystem="uav",
            )
        )

        # Open5GS 指標
        self.register_metric(
            MetricDefinition(
                name="registration_success",
                metric_type="counter",
                description="AMF 註冊成功次數",
                unit="total",
                labels=["component", "slice_type"],
                domain="open5gs",
                subsystem="amf",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="bytes_transmitted",
                metric_type="counter",
                description="UPF 傳輸字節數",
                unit="bytes",
                labels=["component", "direction", "slice_type"],
                domain="open5gs",
                subsystem="upf",
            )
        )

        # NetStack API 指標
        self.register_metric(
            MetricDefinition(
                name="requests",
                metric_type="counter",
                description="API 請求總數",
                unit="total",
                labels=["method", "endpoint", "status"],
                domain="netstack",
                subsystem="api",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="request_duration",
                metric_type="histogram",
                description="API 請求持續時間",
                unit="seconds",
                labels=["method", "endpoint"],
                domain="netstack",
                subsystem="api",
            )
        )

        # Sionna GPU 指標
        self.register_metric(
            MetricDefinition(
                name="utilization",
                metric_type="gauge",
                description="GPU 使用率",
                unit="percent",
                labels=["gpu_id", "service"],
                domain="sionna",
                subsystem="gpu",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="memory_usage",
                metric_type="gauge",
                description="GPU 記憶體使用量",
                unit="mb",
                labels=["gpu_id", "service"],
                domain="sionna",
                subsystem="gpu",
            )
        )

        # AI-RAN 指標
        self.register_metric(
            MetricDefinition(
                name="decision_accuracy",
                metric_type="gauge",
                description="AI 決策準確性",
                unit="percent",
                labels=["model_type", "scenario"],
                domain="ai",
                subsystem="ran",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="interference_detected",
                metric_type="counter",
                description="檢測到的干擾事件數",
                unit="total",
                labels=["interference_type", "frequency_band"],
                domain="ai",
                subsystem="ran",
            )
        )

        # 系統資源指標
        self.register_metric(
            MetricDefinition(
                name="cpu_usage",
                metric_type="gauge",
                description="CPU 使用率",
                unit="percent",
                labels=["component", "core_id"],
                domain="system",
                subsystem="resource",
            )
        )

        self.register_metric(
            MetricDefinition(
                name="memory_usage",
                metric_type="gauge",
                description="記憶體使用量",
                unit="mb",
                labels=["component", "memory_type"],
                domain="system",
                subsystem="resource",
            )
        )

    def register_metric(self, definition: MetricDefinition):
        """註冊指標"""
        full_name = definition.get_full_name()
        self.metrics[full_name] = definition

        # 創建 Prometheus 指標對象
        if definition.metric_type == "counter":
            self.prometheus_metrics[full_name] = Counter(
                full_name,
                definition.description,
                definition.labels,
                registry=self.prometheus_registry,
            )
        elif definition.metric_type == "gauge":
            self.prometheus_metrics[full_name] = Gauge(
                full_name,
                definition.description,
                definition.labels,
                registry=self.prometheus_registry,
            )
        elif definition.metric_type == "histogram":
            self.prometheus_metrics[full_name] = Histogram(
                full_name,
                definition.description,
                definition.labels,
                registry=self.prometheus_registry,
            )

    def get_metric(self, name: str) -> Optional[MetricDefinition]:
        """獲取指標定義"""
        return self.metrics.get(name)

    def get_prometheus_metric(self, name: str) -> Optional[Any]:
        """獲取 Prometheus 指標對象"""
        return self.prometheus_metrics.get(name)


class ServiceCollector:
    """服務指標收集器基類"""

    def __init__(self, service_name: str, endpoint_url: str):
        self.service_name = service_name
        self.endpoint_url = endpoint_url
        self.logger = logger.bind(service=service_name)

    async def collect_metrics(self) -> List[MetricValue]:
        """收集指標（由子類實現）"""
        raise NotImplementedError

    async def health_check(self) -> bool:
        """健康檢查"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.endpoint_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    return response.status == 200
        except Exception:
            return False


class NetStackAPICollector(ServiceCollector):
    """NetStack API 指標收集器"""

    async def collect_metrics(self) -> List[MetricValue]:
        """收集 NetStack API 指標"""
        metrics = []

        try:
            async with aiohttp.ClientSession() as session:
                # 收集 API 統計
                async with session.get(
                    f"{self.endpoint_url}/api/v1/metrics/stats"
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # API 請求指標
                        if "api_requests" in data:
                            for endpoint_data in data["api_requests"]:
                                metrics.append(
                                    MetricValue(
                                        metric_name="netstack_api_requests_total",
                                        value=endpoint_data["count"],
                                        labels={
                                            "method": endpoint_data["method"],
                                            "endpoint": endpoint_data["endpoint"],
                                            "status": str(endpoint_data["status"]),
                                        },
                                        timestamp=time.time(),
                                        source_service="netstack-api",
                                    )
                                )

                        # 響應時間指標
                        if "response_times" in data:
                            for endpoint_data in data["response_times"]:
                                metrics.append(
                                    MetricValue(
                                        metric_name="netstack_api_request_duration_seconds",
                                        value=endpoint_data["avg_duration"],
                                        labels={
                                            "method": endpoint_data["method"],
                                            "endpoint": endpoint_data["endpoint"],
                                        },
                                        timestamp=time.time(),
                                        source_service="netstack-api",
                                    )
                                )

                # 收集 UAV 指標
                async with session.get(
                    f"{self.endpoint_url}/api/v1/uav/metrics"
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        for uav_data in data.get("uav_metrics", []):
                            uav_id = uav_data["uav_id"]

                            # 延遲指標
                            metrics.append(
                                MetricValue(
                                    metric_name="ntn_uav_latency_ms",
                                    value=uav_data.get("latency_ms", 0),
                                    labels={
                                        "uav_id": uav_id,
                                        "connection_type": uav_data.get(
                                            "connection_type", "unknown"
                                        ),
                                        "cell_id": uav_data.get("cell_id", "unknown"),
                                    },
                                    timestamp=time.time(),
                                    source_service="netstack-api",
                                )
                            )

                            # SINR 指標
                            metrics.append(
                                MetricValue(
                                    metric_name="ntn_uav_sinr_db",
                                    value=uav_data.get("sinr_db", 0),
                                    labels={
                                        "uav_id": uav_id,
                                        "cell_id": uav_data.get("cell_id", "unknown"),
                                        "frequency_band": uav_data.get(
                                            "frequency_band", "unknown"
                                        ),
                                    },
                                    timestamp=time.time(),
                                    source_service="netstack-api",
                                )
                            )

                            # RSRP 指標
                            metrics.append(
                                MetricValue(
                                    metric_name="ntn_uav_rsrp_dbm",
                                    value=uav_data.get("rsrp_dbm", 0),
                                    labels={
                                        "uav_id": uav_id,
                                        "cell_id": uav_data.get("cell_id", "unknown"),
                                    },
                                    timestamp=time.time(),
                                    source_service="netstack-api",
                                )
                            )

        except Exception as e:
            self.logger.error("收集 NetStack API 指標失敗", error=str(e))

        return metrics


class SimWorldCollector(ServiceCollector):
    """SimWorld 指標收集器"""

    async def collect_metrics(self) -> List[MetricValue]:
        """收集 SimWorld 指標"""
        metrics = []

        try:
            async with aiohttp.ClientSession() as session:
                # 收集 GPU 指標
                async with session.get(
                    f"{self.endpoint_url}/api/v1/system/gpu-metrics"
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        for gpu_data in data.get("gpu_metrics", []):
                            gpu_id = str(gpu_data["gpu_id"])

                            # GPU 使用率
                            metrics.append(
                                MetricValue(
                                    metric_name="sionna_gpu_utilization_percent",
                                    value=gpu_data.get("utilization_percent", 0),
                                    labels={"gpu_id": gpu_id, "service": "simworld"},
                                    timestamp=time.time(),
                                    source_service="simworld",
                                )
                            )

                            # GPU 記憶體使用量
                            metrics.append(
                                MetricValue(
                                    metric_name="sionna_gpu_memory_usage_mb",
                                    value=gpu_data.get("memory_used_mb", 0),
                                    labels={"gpu_id": gpu_id, "service": "simworld"},
                                    timestamp=time.time(),
                                    source_service="simworld",
                                )
                            )

                # 收集通道模擬指標
                async with session.get(
                    f"{self.endpoint_url}/api/v1/wireless/simulation-metrics"
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 模擬計算時間
                        if "simulation_stats" in data:
                            for stat in data["simulation_stats"]:
                                metrics.append(
                                    MetricValue(
                                        metric_name="sionna_channel_simulation_duration_seconds",
                                        value=stat.get("computation_time_sec", 0),
                                        labels={
                                            "scenario": stat.get("scenario", "unknown"),
                                            "num_ue": str(stat.get("num_ue", 0)),
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )

        except Exception as e:
            self.logger.error("收集 SimWorld 指標失敗", error=str(e))

        return metrics


class SionnaChannelCollector(ServiceCollector):
    """Sionna 通道指標收集器"""

    async def collect_metrics(self) -> List[MetricValue]:
        """收集 Sionna 通道指標"""
        metrics = []

        try:
            async with aiohttp.ClientSession() as session:
                # 收集詳細通道指標
                async with session.get(
                    f"{self.endpoint_url}/api/v1/wireless/channel-metrics"
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 通道容量指標
                        for channel_data in data.get("channel_metrics", []):
                            ue_id = channel_data.get("ue_id", "unknown")
                            gnb_id = channel_data.get("gnb_id", "unknown")
                            frequency_band = channel_data.get("frequency_band", "unknown")
                            
                            # 通道容量
                            if "channel_capacity_mbps" in channel_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="sionna_channel_channel_capacity_mbps",
                                        value=channel_data["channel_capacity_mbps"],
                                        labels={
                                            "ue_id": ue_id,
                                            "gnb_id": gnb_id,
                                            "frequency_band": frequency_band,
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )
                            
                            # 路徑損耗
                            if "path_loss_db" in channel_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="sionna_channel_path_loss_db",
                                        value=channel_data["path_loss_db"],
                                        labels={
                                            "ue_id": ue_id,
                                            "gnb_id": gnb_id,
                                            "environment": channel_data.get("environment", "urban"),
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )
                            
                            # 多普勒頻移
                            if "doppler_shift_hz" in channel_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="sionna_channel_doppler_shift_hz",
                                        value=channel_data["doppler_shift_hz"],
                                        labels={
                                            "ue_id": ue_id,
                                            "gnb_id": gnb_id,
                                            "mobility_type": channel_data.get("mobility_type", "stationary"),
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )
                            
                            # 延遲擴散
                            if "delay_spread_ns" in channel_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="sionna_channel_delay_spread_ns",
                                        value=channel_data["delay_spread_ns"],
                                        labels={
                                            "ue_id": ue_id,
                                            "gnb_id": gnb_id,
                                            "environment": channel_data.get("environment", "urban"),
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )
                            
                            # 相干帶寬
                            if "coherence_bandwidth_hz" in channel_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="sionna_channel_coherence_bandwidth_hz",
                                        value=channel_data["coherence_bandwidth_hz"],
                                        labels={
                                            "ue_id": ue_id,
                                            "gnb_id": gnb_id,
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )
                            
                            # 衰落方差
                            if "fading_variance_db" in channel_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="sionna_channel_fading_variance_db",
                                        value=channel_data["fading_variance_db"],
                                        labels={
                                            "ue_id": ue_id,
                                            "gnb_id": gnb_id,
                                            "fading_type": channel_data.get("fading_type", "rayleigh"),
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )

                # 收集干擾控制指標
                async with session.get(
                    f"{self.endpoint_url}/api/v1/interference/metrics"
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 干擾強度指標
                        for interference_data in data.get("interference_metrics", []):
                            source_type = interference_data.get("source_type", "unknown")
                            frequency_band = interference_data.get("frequency_band", "unknown")
                            location = interference_data.get("location", "unknown")
                            
                            if "interference_level_dbm" in interference_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="interference_control_interference_level_dbm",
                                        value=interference_data["interference_level_dbm"],
                                        labels={
                                            "source_type": source_type,
                                            "frequency_band": frequency_band,
                                            "location": location,
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )

                        # 緩解成功率指標
                        for mitigation_data in data.get("mitigation_stats", []):
                            strategy_type = mitigation_data.get("strategy_type", "unknown")
                            interference_type = mitigation_data.get("interference_type", "unknown")
                            
                            if "success_rate_percent" in mitigation_data:
                                metrics.append(
                                    MetricValue(
                                        metric_name="interference_control_mitigation_success_rate_percent",
                                        value=mitigation_data["success_rate_percent"],
                                        labels={
                                            "strategy_type": strategy_type,
                                            "interference_type": interference_type,
                                        },
                                        timestamp=time.time(),
                                        source_service="simworld",
                                    )
                                )

        except Exception as e:
            self.logger.error("收集 Sionna 通道指標失敗", error=str(e))

        return metrics


class SystemResourceCollector(ServiceCollector):
    """系統資源指標收集器"""

    def __init__(self):
        super().__init__("system", "local")

    async def collect_metrics(self) -> List[MetricValue]:
        """收集系統資源指標"""
        metrics = []

        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            for i, usage in enumerate(cpu_percent):
                metrics.append(
                    MetricValue(
                        metric_name="system_resource_cpu_usage_percent",
                        value=usage,
                        labels={"component": "system", "core_id": str(i)},
                        timestamp=time.time(),
                        source_service="system",
                    )
                )

            # 記憶體使用量
            memory = psutil.virtual_memory()
            metrics.append(
                MetricValue(
                    metric_name="system_resource_memory_usage_mb",
                    value=memory.used / (1024 * 1024),
                    labels={"component": "system", "memory_type": "physical"},
                    timestamp=time.time(),
                    source_service="system",
                )
            )

            # 磁碟使用率
            disk = psutil.disk_usage("/")
            metrics.append(
                MetricValue(
                    metric_name="system_resource_disk_usage_percent",
                    value=(disk.used / disk.total) * 100,
                    labels={"component": "system", "mount_point": "/"},
                    timestamp=time.time(),
                    source_service="system",
                )
            )

            # GPU 指標（如果可用）
            try:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    metrics.append(
                        MetricValue(
                            metric_name="system_resource_gpu_usage_percent",
                            value=gpu.load * 100,
                            labels={"component": "system", "gpu_id": str(gpu.id)},
                            timestamp=time.time(),
                            source_service="system",
                        )
                    )

                    metrics.append(
                        MetricValue(
                            metric_name="system_resource_gpu_memory_usage_mb",
                            value=gpu.memoryUsed,
                            labels={"component": "system", "gpu_id": str(gpu.id)},
                            timestamp=time.time(),
                            source_service="system",
                        )
                    )
            except Exception:
                # GPU 不可用，跳過
                pass

        except Exception as e:
            self.logger.error("收集系統資源指標失敗", error=str(e))

        return metrics


class KPICollector:
    """KPI指標收集器"""
    
    def __init__(self):
        self.logger = logger.bind(component="kpi_collector")
        
    async def collect_ntn_kpis(self, session: aiohttp.ClientSession, base_url: str) -> List[MetricValue]:
        """收集NTN系統KPI指標"""
        metrics = []
        
        try:
            # 端到端延遲KPI
            async with session.get(f"{base_url}/api/v1/kpi/e2e-latency") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_e2e_latency_ms",
                            value=data.get("avg_latency_ms", 0),
                            labels={"kpi_type": "latency", "measurement": "e2e"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 覆蓋率KPI
            async with session.get(f"{base_url}/api/v1/kpi/coverage") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_coverage_percent",
                            value=data.get("coverage_percentage", 0),
                            labels={"kpi_type": "coverage", "area": "total"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 傳輸速率KPI
            async with session.get(f"{base_url}/api/v1/kpi/transmission-rate") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_transmission_rate_mbps",
                            value=data.get("avg_rate_mbps", 0),
                            labels={"kpi_type": "transmission", "direction": "total"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 可用性KPI
            async with session.get(f"{base_url}/api/v1/kpi/availability") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_availability_percent",
                            value=data.get("availability_percentage", 0),
                            labels={"kpi_type": "availability", "service": "overall"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 衛星換手成功率KPI
            async with session.get(f"{base_url}/api/v1/kpi/handover-success-rate") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_handover_success_rate_percent",
                            value=data.get("success_rate_percentage", 0),
                            labels={"kpi_type": "handover", "operation": "satellite_handover"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # AI-RAN性能KPI
            async with session.get(f"{base_url}/api/v1/kpi/ai-ran-performance") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 干擾檢測準確率
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_ai_interference_detection_accuracy_percent",
                            value=data.get("interference_detection_accuracy", 0),
                            labels={"kpi_type": "ai_performance", "function": "interference_detection"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
                    
                    # 資源分配效率
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_ai_resource_allocation_efficiency_percent",
                            value=data.get("resource_allocation_efficiency", 0),
                            labels={"kpi_type": "ai_performance", "function": "resource_allocation"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # UAV連通性KPI
            async with session.get(f"{base_url}/api/v1/kpi/uav-connectivity") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_uav_connectivity_percent",
                            value=data.get("connectivity_percentage", 0),
                            labels={"kpi_type": "connectivity", "device_type": "uav"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # Mesh網路恢復性KPI
            async with session.get(f"{base_url}/api/v1/kpi/mesh-resilience") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_mesh_resilience_score",
                            value=data.get("resilience_score", 0),
                            labels={"kpi_type": "resilience", "network_type": "mesh"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
                    
        except Exception as e:
            self.logger.error(f"收集NTN KPI指標失敗: {e}")
        
        return metrics
    
    async def collect_quality_kpis(self, session: aiohttp.ClientSession, base_url: str) -> List[MetricValue]:
        """收集服務質量KPI指標"""
        metrics = []
        
        try:
            # 呼叫建立成功率
            async with session.get(f"{base_url}/api/v1/kpi/call-setup-success-rate") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_call_setup_success_rate_percent",
                            value=data.get("success_rate_percentage", 0),
                            labels={"kpi_type": "quality", "service": "call_setup"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 呼叫中斷率
            async with session.get(f"{base_url}/api/v1/kpi/call-drop-rate") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_call_drop_rate_percent",
                            value=data.get("drop_rate_percentage", 0),
                            labels={"kpi_type": "quality", "service": "call_drop"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 封包遺失率
            async with session.get(f"{base_url}/api/v1/kpi/packet-loss-rate") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_packet_loss_rate_percent",
                            value=data.get("loss_rate_percentage", 0),
                            labels={"kpi_type": "quality", "metric": "packet_loss"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 抖動(Jitter)
            async with session.get(f"{base_url}/api/v1/kpi/jitter") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_jitter_ms",
                            value=data.get("avg_jitter_ms", 0),
                            labels={"kpi_type": "quality", "metric": "jitter"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 信號品質(SINR)
            async with session.get(f"{base_url}/api/v1/kpi/signal-quality") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_avg_sinr_db",
                            value=data.get("avg_sinr_db", 0),
                            labels={"kpi_type": "quality", "metric": "sinr"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
                    
        except Exception as e:
            self.logger.error(f"收集服務質量KPI指標失敗: {e}")
        
        return metrics
    
    async def collect_capacity_kpis(self, session: aiohttp.ClientSession, base_url: str) -> List[MetricValue]:
        """收集容量和效能KPI指標"""
        metrics = []
        
        try:
            # 頻譜效率
            async with session.get(f"{base_url}/api/v1/kpi/spectrum-efficiency") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_spectrum_efficiency_bps_hz",
                            value=data.get("efficiency_bps_hz", 0),
                            labels={"kpi_type": "capacity", "metric": "spectrum_efficiency"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 能量效率
            async with session.get(f"{base_url}/api/v1/kpi/energy-efficiency") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_energy_efficiency_mbps_watt",
                            value=data.get("efficiency_mbps_watt", 0),
                            labels={"kpi_type": "capacity", "metric": "energy_efficiency"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 系統容量利用率
            async with session.get(f"{base_url}/api/v1/kpi/capacity-utilization") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_capacity_utilization_percent",
                            value=data.get("utilization_percentage", 0),
                            labels={"kpi_type": "capacity", "metric": "utilization"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 並發用戶數
            async with session.get(f"{base_url}/api/v1/kpi/concurrent-users") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_concurrent_users_count",
                            value=data.get("user_count", 0),
                            labels={"kpi_type": "capacity", "metric": "concurrent_users"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
                    
        except Exception as e:
            self.logger.error(f"收集容量KPI指標失敗: {e}")
        
        return metrics
    
    async def collect_performance_optimizer_kpis(self, session: aiohttp.ClientSession, base_url: str) -> List[MetricValue]:
        """收集性能優化器KPI指標"""
        metrics = []
        
        try:
            # 優化執行成功率
            async with session.get(f"{base_url}/api/v1/kpi/optimization-success-rate") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_optimization_success_rate_percent",
                            value=data.get("success_rate_percentage", 0),
                            labels={"kpi_type": "optimization", "metric": "success_rate"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 平均優化改善程度
            async with session.get(f"{base_url}/api/v1/kpi/optimization-improvement") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_avg_optimization_improvement_percent",
                            value=data.get("avg_improvement_percent", 0),
                            labels={"kpi_type": "optimization", "metric": "improvement"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 性能目標達成率
            async with session.get(f"{base_url}/api/v1/kpi/performance-target-achievement") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_performance_target_achievement_percent",
                            value=data.get("achievement_percentage", 0),
                            labels={"kpi_type": "optimization", "metric": "target_achievement"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 自動優化觸發頻率
            async with session.get(f"{base_url}/api/v1/kpi/auto-optimization-frequency") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_auto_optimization_frequency_per_hour",
                            value=data.get("frequency_per_hour", 0),
                            labels={"kpi_type": "optimization", "metric": "auto_frequency"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # ML模型預測準確率
            async with session.get(f"{base_url}/api/v1/kpi/ml-prediction-accuracy") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_ml_prediction_accuracy_percent",
                            value=data.get("accuracy_percentage", 0),
                            labels={"kpi_type": "optimization", "metric": "ml_accuracy"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
                    
        except Exception as e:
            self.logger.error(f"收集性能優化器KPI指標失敗: {e}")
        
        return metrics
    
    async def collect_testing_framework_kpis(self, session: aiohttp.ClientSession, base_url: str) -> List[MetricValue]:
        """收集測試框架KPI指標"""
        metrics = []
        
        try:
            # E2E測試成功率
            async with session.get(f"{base_url}/api/v1/kpi/e2e-test-success-rate") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_e2e_test_success_rate_percent",
                            value=data.get("success_rate_percentage", 0),
                            labels={"kpi_type": "testing", "test_type": "e2e"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 負載測試最大承載能力
            async with session.get(f"{base_url}/api/v1/kpi/load-test-capacity") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_max_load_capacity_users",
                            value=data.get("max_concurrent_users", 0),
                            labels={"kpi_type": "testing", "test_type": "load"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 壓力測試系統穩定性
            async with session.get(f"{base_url}/api/v1/kpi/stress-test-stability") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_stress_test_stability_score",
                            value=data.get("stability_score", 0),
                            labels={"kpi_type": "testing", "test_type": "stress"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 性能回歸檢測準確率
            async with session.get(f"{base_url}/api/v1/kpi/regression-detection-accuracy") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_regression_detection_accuracy_percent",
                            value=data.get("detection_accuracy_percent", 0),
                            labels={"kpi_type": "testing", "test_type": "regression"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
            
            # 測試自動化覆蓋率
            async with session.get(f"{base_url}/api/v1/kpi/test-automation-coverage") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics.append(
                        MetricValue(
                            metric_name="ntn_kpi_test_automation_coverage_percent",
                            value=data.get("coverage_percentage", 0),
                            labels={"kpi_type": "testing", "metric": "automation_coverage"},
                            timestamp=time.time(),
                            source_service="netstack-api"
                        )
                    )
                    
        except Exception as e:
            self.logger.error(f"收集測試框架KPI指標失敗: {e}")
        
        return metrics


class UnifiedMetricsCollector:
    """統一指標收集服務 - 增強版本"""

    def __init__(
        self,
        redis_adapter: RedisAdapter,
        collection_interval: float = 15.0,
        retention_hours: int = 24,
    ):
        self.logger = logger.bind(service="unified_metrics_collector")
        self.redis_adapter = redis_adapter
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours

        # 初始化指標註冊器
        self.metrics_registry = MetricsRegistry()

        # 初始化收集器
        self.collectors: List[ServiceCollector] = [
            NetStackAPICollector("netstack-api", "http://netstack-api:8080"),
            SimWorldCollector("simworld", "http://simworld-backend:8000"),
            SionnaChannelCollector("sionna-integration", "http://simworld-backend:8000"),
            SystemResourceCollector(),
        ]
        
        # 初始化KPI收集器
        self.kpi_collector = KPICollector()

        # 收集統計
        self.collection_stats = {
            "total_collections": 0,
            "successful_collections": 0,
            "failed_collections": 0,
            "last_collection_time": None,
            "metrics_collected": 0,
            "kpi_metrics_collected": 0,
        }

        # 任務控制
        self.running = False
        self.collection_task: Optional[asyncio.Task] = None
        
        # KPI特定配置
        self.kpi_collection_enabled = True
        self.kpi_collection_interval = 30.0  # KPI收集間隔較長

    async def start_collection(self):
        """啟動指標收集"""
        if self.running:
            self.logger.warning("指標收集已在運行中")
            return

        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("統一指標收集已啟動", interval=self.collection_interval)

    async def stop_collection(self):
        """停止指標收集"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("統一指標收集已停止")

    async def _collection_loop(self):
        """增強的指標收集循環"""
        kpi_last_collection = 0
        
        while self.running:
            try:
                start_time = time.time()

                # 並行收集所有服務的指標
                collection_tasks = [
                    self._collect_from_service(collector)
                    for collector in self.collectors
                ]

                results = await asyncio.gather(
                    *collection_tasks, return_exceptions=True
                )

                # 合併所有指標
                all_metrics = []
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.error("收集指標異常", error=str(result))
                        continue
                    all_metrics.extend(result)

                # 檢查是否需要收集KPI指標
                kpi_metrics = []
                current_time = time.time()
                if (self.kpi_collection_enabled and 
                    current_time - kpi_last_collection >= self.kpi_collection_interval):
                    
                    self.logger.debug("開始收集KPI指標")
                    kpi_metrics = await self._collect_kpi_metrics()
                    all_metrics.extend(kpi_metrics)
                    kpi_last_collection = current_time

                # 儲存指標到 Redis 和 Prometheus
                await self._store_metrics(all_metrics)

                # 更新統計
                collection_time = time.time() - start_time
                self.collection_stats.update(
                    {
                        "total_collections": self.collection_stats["total_collections"]
                        + 1,
                        "successful_collections": self.collection_stats[
                            "successful_collections"
                        ]
                        + 1,
                        "last_collection_time": datetime.utcnow().isoformat(),
                        "metrics_collected": len(all_metrics),
                        "kpi_metrics_collected": len(kpi_metrics),
                        "collection_duration_sec": collection_time,
                    }
                )

                self.logger.debug(
                    "指標收集完成",
                    metrics_count=len(all_metrics),
                    kpi_count=len(kpi_metrics),
                    duration=f"{collection_time:.2f}s",
                )

            except Exception as e:
                self.collection_stats["failed_collections"] += 1
                self.logger.error("指標收集循環失敗", error=str(e))

            # 等待下一次收集
            await asyncio.sleep(self.collection_interval)

    async def _collect_kpi_metrics(self) -> List[MetricValue]:
        """收集KPI指標（增強版本）"""
        metrics = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # 收集NTN系統KPI
                ntn_metrics = await self.kpi_collector.collect_ntn_kpis(session, "http://netstack-api:8080")
                metrics.extend(ntn_metrics)
                
                # 收集服務質量KPI
                quality_metrics = await self.kpi_collector.collect_quality_kpis(session, "http://netstack-api:8080")
                metrics.extend(quality_metrics)
                
                # 收集容量KPI
                capacity_metrics = await self.kpi_collector.collect_capacity_kpis(session, "http://netstack-api:8080")
                metrics.extend(capacity_metrics)
                
                # 收集性能優化器KPI
                optimizer_metrics = await self.kpi_collector.collect_performance_optimizer_kpis(session, "http://netstack-api:8080")
                metrics.extend(optimizer_metrics)
                
                # 收集測試框架KPI
                testing_metrics = await self.kpi_collector.collect_testing_framework_kpis(session, "http://netstack-api:8080")
                metrics.extend(testing_metrics)
                
        except Exception as e:
            self.logger.error(f"收集KPI指標失敗: {e}")
        
        return metrics

    async def _collect_from_service(
        self, collector: ServiceCollector
    ) -> List[MetricValue]:
        """從單個服務收集指標"""
        try:
            # 檢查服務健康狀態
            if (
                hasattr(collector, "health_check")
                and not await collector.health_check()
            ):
                self.logger.warning(f"服務 {collector.service_name} 健康檢查失敗")
                return []

            return await collector.collect_metrics()

        except Exception as e:
            self.logger.error(f"從 {collector.service_name} 收集指標失敗", error=str(e))
            return []

    async def _store_metrics(self, metrics: List[MetricValue]):
        """儲存指標"""
        try:
            # 儲存到 Redis（用於短期查詢）
            redis_metrics = {}

            for metric in metrics:
                key = f"metrics:{metric.metric_name}:{metric.timestamp}"
                value = {
                    "value": metric.value,
                    "labels": metric.labels,
                    "source": metric.source_service,
                }
                redis_metrics[key] = json.dumps(value)

                # 更新 Prometheus 指標
                prometheus_metric = self.metrics_registry.get_prometheus_metric(
                    metric.metric_name
                )
                if prometheus_metric:
                    if hasattr(prometheus_metric, "labels"):
                        prometheus_metric.labels(**metric.labels).set(metric.value)
                    else:
                        prometheus_metric.set(metric.value)

            # 批量寫入 Redis
            if redis_metrics:
                pipe = self.redis_adapter.redis_client.pipeline()
                for key, value in redis_metrics.items():
                    pipe.setex(key, 3600 * self.retention_hours, value)
                await pipe.execute()

        except Exception as e:
            self.logger.error("儲存指標失敗", error=str(e))

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        try:
            # 獲取最近的指標統計
            current_time = time.time()
            one_hour_ago = current_time - 3600

            # 從 Redis 查詢最近一小時的指標
            pattern = f"metrics:*"
            keys = await self.redis_adapter.redis_client.keys(pattern)

            recent_metrics = {}
            for key in keys:
                # 解析時間戳
                parts = key.decode().split(":")
                if len(parts) >= 3:
                    timestamp = float(parts[2])
                    if timestamp >= one_hour_ago:
                        metric_name = parts[1]
                        if metric_name not in recent_metrics:
                            recent_metrics[metric_name] = 0
                        recent_metrics[metric_name] += 1

            return {
                "collection_stats": self.collection_stats,
                "recent_metrics": recent_metrics,
                "active_collectors": len(self.collectors),
                "registered_metrics": len(self.metrics_registry.metrics),
                "prometheus_metrics": len(self.metrics_registry.prometheus_metrics),
            }

        except Exception as e:
            self.logger.error("獲取指標摘要失敗", error=str(e))
            return {"error": str(e)}

    def get_prometheus_metrics(self) -> str:
        """獲取 Prometheus 格式的指標"""
        return generate_latest(self.metrics_registry.prometheus_registry)

    async def validate_metrics_format(
        self, metrics: List[MetricValue]
    ) -> Dict[str, Any]:
        """驗證指標格式是否符合標準"""
        validation_results = {
            "valid_metrics": 0,
            "invalid_metrics": 0,
            "format_errors": [],
            "missing_labels": [],
            "unknown_metrics": [],
        }

        for metric in metrics:
            # 檢查指標是否已註冊
            definition = self.metrics_registry.get_metric(metric.metric_name)
            if not definition:
                validation_results["unknown_metrics"].append(metric.metric_name)
                validation_results["invalid_metrics"] += 1
                continue

            # 檢查必需標籤
            missing_labels = []
            for required_label in definition.labels:
                if required_label not in metric.labels:
                    missing_labels.append(required_label)

            if missing_labels:
                validation_results["missing_labels"].append(
                    {"metric": metric.metric_name, "missing": missing_labels}
                )
                validation_results["invalid_metrics"] += 1
            else:
                validation_results["valid_metrics"] += 1

        return validation_results
