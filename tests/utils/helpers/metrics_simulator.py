#!/usr/bin/env python3
"""
NTN Stack 指標模擬器

生成符合統一格式規範的測試指標數據，用於儀表板開發和系統驗證
"""

import random
import time
import math
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import signal
import sys
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    start_http_server,
    generate_latest,
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class UAVConfig:
    """UAV 配置"""

    uav_id: str
    altitude: float
    velocity: float
    connection_type: str
    mission_type: str
    initial_position: tuple


@dataclass
class SimulationConfig:
    """模擬配置"""

    num_uavs: int = 5
    simulation_duration: int = 3600  # 秒
    update_interval: float = 1.0  # 秒
    enable_anomalies: bool = True
    anomaly_probability: float = 0.01
    realistic_patterns: bool = True


class MetricsSimulator:
    """指標模擬器"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.registry = CollectorRegistry()
        self.running = False
        self.uavs: List[UAVConfig] = []

        # 初始化 UAV 配置
        self._init_uavs()

        # 創建 Prometheus 指標
        self._create_prometheus_metrics()

        # 模擬狀態
        self.simulation_start_time = time.time()
        self.last_update_time = time.time()

        logger.info(f"指標模擬器已初始化，UAV 數量: {len(self.uavs)}")

    def _init_uavs(self):
        """初始化 UAV 配置"""
        mission_types = ["surveillance", "delivery", "rescue", "inspection", "research"]
        connection_types = ["satellite", "terrestrial", "mesh", "hybrid"]

        for i in range(self.config.num_uavs):
            uav = UAVConfig(
                uav_id=f"uav-{i:08x}",
                altitude=random.uniform(50, 500),  # 50-500米
                velocity=random.uniform(10, 50),  # 10-50 m/s
                connection_type=random.choice(connection_types),
                mission_type=random.choice(mission_types),
                initial_position=(
                    random.uniform(25.0, 25.1),  # 緯度 (台北附近)
                    random.uniform(121.5, 121.6),  # 經度
                ),
            )
            self.uavs.append(uav)

    def _create_prometheus_metrics(self):
        """創建 Prometheus 指標"""
        # 系統狀態指標
        self.up_metric = Gauge(
            "up",
            "Service up status",
            ["environment", "service", "component"],
            registry=self.registry,
        )

        # NTN UAV 指標
        self.ntn_uav_latency = Gauge(
            "ntn_uav_latency_ms",
            "UAV latency in milliseconds",
            ["environment", "uav_id", "connection_type"],
            registry=self.registry,
        )

        self.ntn_uav_sinr = Gauge(
            "ntn_uav_sinr_db",
            "UAV SINR in dB",
            ["environment", "uav_id", "cell_id", "frequency_band"],
            registry=self.registry,
        )

        self.ntn_uav_rsrp = Gauge(
            "ntn_uav_rsrp_dbm",
            "UAV RSRP in dBm",
            ["environment", "uav_id", "cell_id"],
            registry=self.registry,
        )

        self.ntn_uav_connection_success = Counter(
            "ntn_uav_connection_success_total",
            "UAV connection success count",
            ["environment", "uav_id", "connection_type"],
            registry=self.registry,
        )

        self.ntn_uav_connection_attempts = Counter(
            "ntn_uav_connection_attempts_total",
            "UAV connection attempts count",
            ["environment", "uav_id", "connection_type"],
            registry=self.registry,
        )

        self.ntn_uav_bytes_transmitted = Counter(
            "ntn_uav_bytes_transmitted_total",
            "UAV bytes transmitted",
            ["environment", "uav_id", "direction"],
            registry=self.registry,
        )

        self.ntn_uav_bytes_received = Counter(
            "ntn_uav_bytes_received_total",
            "UAV bytes received",
            ["environment", "uav_id", "direction"],
            registry=self.registry,
        )

        # Open5GS 指標
        self.open5gs_amf_registration_success = Counter(
            "open5gs_amf_registration_success_total",
            "AMF registration success count",
            ["environment", "component", "slice_type"],
            registry=self.registry,
        )

        self.open5gs_amf_registration_attempts = Counter(
            "open5gs_amf_registration_attempts_total",
            "AMF registration attempts count",
            ["environment", "component", "slice_type"],
            registry=self.registry,
        )

        self.open5gs_upf_bytes_transmitted = Counter(
            "open5gs_upf_bytes_transmitted_total",
            "UPF bytes transmitted",
            ["environment", "component", "direction", "slice_type"],
            registry=self.registry,
        )

        # NetStack API 指標
        self.netstack_api_requests = Counter(
            "netstack_api_requests_total",
            "API requests count",
            ["environment", "method", "endpoint", "status"],
            registry=self.registry,
        )

        self.netstack_api_request_duration = Histogram(
            "netstack_api_request_duration_seconds",
            "API request duration",
            ["environment", "method", "endpoint"],
            registry=self.registry,
        )

        # Sionna GPU 指標
        self.sionna_gpu_utilization = Gauge(
            "sionna_gpu_utilization_percent",
            "GPU utilization percentage",
            ["environment", "gpu_id", "service"],
            registry=self.registry,
        )

        self.sionna_gpu_memory_usage = Gauge(
            "sionna_gpu_memory_usage_mb",
            "GPU memory usage in MB",
            ["environment", "gpu_id", "service"],
            registry=self.registry,
        )

        # 系統資源指標 (模擬 node_exporter)
        self.node_cpu_seconds = Counter(
            "node_cpu_seconds_total",
            "CPU time in seconds",
            ["mode", "cpu"],
            registry=self.registry,
        )

        self.node_memory_available = Gauge(
            "node_memory_MemAvailable_bytes",
            "Available memory in bytes",
            [],
            registry=self.registry,
        )

        self.node_memory_total = Gauge(
            "node_memory_MemTotal_bytes",
            "Total memory in bytes",
            [],
            registry=self.registry,
        )

    def start_simulation(self):
        """開始模擬"""
        self.running = True
        logger.info("開始指標模擬")

        # 設置初始狀態
        self._setup_initial_state()

        # 主模擬循環
        while self.running:
            try:
                current_time = time.time()
                elapsed = current_time - self.simulation_start_time

                # 更新所有指標
                self._update_metrics(elapsed)

                # 計算下次更新時間
                next_update = self.last_update_time + self.config.update_interval
                sleep_time = max(0, next_update - current_time)

                if sleep_time > 0:
                    time.sleep(sleep_time)

                self.last_update_time = current_time

                # 檢查是否達到模擬時間限制
                if elapsed >= self.config.simulation_duration:
                    logger.info("達到模擬時間限制，停止模擬")
                    break

            except KeyboardInterrupt:
                logger.info("收到中斷信號，停止模擬")
                break
            except Exception as e:
                logger.error(f"模擬過程中發生錯誤: {e}")
                break

        self.running = False
        logger.info("指標模擬已停止")

    def stop_simulation(self):
        """停止模擬"""
        self.running = False

    def _setup_initial_state(self):
        """設置初始狀態"""
        # 設置系統狀態為在線
        services = [
            ("netstack-api", "api"),
            ("netstack-amf", "amf"),
            ("netstack-smf", "smf"),
            ("netstack-upf", "upf"),
            ("simworld-api", "simulation"),
        ]

        for service, component in services:
            self.up_metric.labels(
                environment="prod", service=service, component=component
            ).set(1)

        # 設置系統資源基線
        self.node_memory_total.set(16 * 1024 * 1024 * 1024)  # 16GB
        self.node_memory_available.set(8 * 1024 * 1024 * 1024)  # 8GB 可用

    def _update_metrics(self, elapsed_time: float):
        """更新指標數據"""
        # 更新 UAV 指標
        for uav in self.uavs:
            self._update_uav_metrics(uav, elapsed_time)

        # 更新 Open5GS 指標
        self._update_open5gs_metrics(elapsed_time)

        # 更新 API 指標
        self._update_api_metrics(elapsed_time)

        # 更新 GPU 指標
        self._update_gpu_metrics(elapsed_time)

        # 更新系統資源指標
        self._update_system_metrics(elapsed_time)

        logger.debug(f"指標更新完成，經過時間: {elapsed_time:.1f}s")

    def _update_uav_metrics(self, uav: UAVConfig, elapsed_time: float):
        """更新 UAV 指標"""
        # 基本延遲模擬 (目標 < 50ms)
        base_latency = 25 + 15 * math.sin(elapsed_time / 60)  # 25-40ms 基線

        # 根據連接類型調整延遲
        connection_multiplier = {
            "satellite": 1.5,
            "terrestrial": 1.0,
            "mesh": 1.2,
            "hybrid": 1.1,
        }

        latency = base_latency * connection_multiplier.get(uav.connection_type, 1.0)

        # 添加異常情況
        if (
            self.config.enable_anomalies
            and random.random() < self.config.anomaly_probability
        ):
            latency += random.uniform(50, 200)  # 異常延遲峰值

        # 添加隨機噪聲
        latency += random.uniform(-5, 5)
        latency = max(1, latency)  # 確保不為負值

        self.ntn_uav_latency.labels(
            environment="prod", uav_id=uav.uav_id, connection_type=uav.connection_type
        ).set(latency)

        # SINR 模擬 (目標 > 10dB)
        base_sinr = 15 + 10 * math.cos(elapsed_time / 120)  # 5-25dB
        sinr = base_sinr + random.uniform(-3, 3)

        self.ntn_uav_sinr.labels(
            environment="prod",
            uav_id=uav.uav_id,
            cell_id="12345678",
            frequency_band="n78",
        ).set(sinr)

        # RSRP 模擬
        base_rsrp = -85 + 15 * math.sin(elapsed_time / 180)  # -100 to -70 dBm
        rsrp = base_rsrp + random.uniform(-5, 5)

        self.ntn_uav_rsrp.labels(
            environment="prod", uav_id=uav.uav_id, cell_id="12345678"
        ).set(rsrp)

        # 連接嘗試和成功 (模擬高成功率)
        if random.random() < 0.1:  # 10% 機率產生連接事件
            self.ntn_uav_connection_attempts.labels(
                environment="prod",
                uav_id=uav.uav_id,
                connection_type=uav.connection_type,
            ).inc()

            # 95% 成功率
            if random.random() < 0.95:
                self.ntn_uav_connection_success.labels(
                    environment="prod",
                    uav_id=uav.uav_id,
                    connection_type=uav.connection_type,
                ).inc()

        # 數據傳輸模擬
        tx_bytes = random.uniform(1000, 10000)  # 1-10KB/s
        rx_bytes = random.uniform(5000, 50000)  # 5-50KB/s

        self.ntn_uav_bytes_transmitted.labels(
            environment="prod", uav_id=uav.uav_id, direction="uplink"
        ).inc(tx_bytes)

        self.ntn_uav_bytes_received.labels(
            environment="prod", uav_id=uav.uav_id, direction="downlink"
        ).inc(rx_bytes)

    def _update_open5gs_metrics(self, elapsed_time: float):
        """更新 Open5GS 指標"""
        # AMF 註冊統計
        if random.random() < 0.05:  # 5% 機率產生註冊事件
            slice_types = ["embb", "urllc", "mmtc"]
            slice_type = random.choice(slice_types)

            self.open5gs_amf_registration_attempts.labels(
                environment="prod", component="amf", slice_type=slice_type
            ).inc()

            # 98% 成功率
            if random.random() < 0.98:
                self.open5gs_amf_registration_success.labels(
                    environment="prod", component="amf", slice_type=slice_type
                ).inc()

        # UPF 數據傳輸
        uplink_bytes = random.uniform(10000, 100000)  # 10-100KB/s
        downlink_bytes = random.uniform(50000, 500000)  # 50-500KB/s

        for direction, bytes_amount in [
            ("uplink", uplink_bytes),
            ("downlink", downlink_bytes),
        ]:
            self.open5gs_upf_bytes_transmitted.labels(
                environment="prod",
                component="upf",
                direction=direction,
                slice_type="embb",
            ).inc(bytes_amount)

    def _update_api_metrics(self, elapsed_time: float):
        """更新 API 指標"""
        # 模擬 API 請求
        endpoints = ["/api/v1/uav", "/api/v1/satellite", "/api/v1/system", "/health"]
        methods = ["GET", "POST", "PUT"]

        for _ in range(random.randint(1, 5)):  # 每次更新 1-5 個請求
            endpoint = random.choice(endpoints)
            method = random.choice(methods)

            # 模擬不同的響應狀態
            status_code = "200"
            if random.random() < 0.02:  # 2% 錯誤率
                status_code = random.choice(["400", "404", "500", "503"])

            self.netstack_api_requests.labels(
                environment="prod", method=method, endpoint=endpoint, status=status_code
            ).inc()

            # 模擬響應時間
            if status_code == "200":
                duration = random.uniform(0.01, 0.1)  # 10-100ms
            else:
                duration = random.uniform(0.1, 2.0)  # 100ms-2s for errors

            self.netstack_api_request_duration.labels(
                environment="prod", method=method, endpoint=endpoint
            ).observe(duration)

    def _update_gpu_metrics(self, elapsed_time: float):
        """更新 GPU 指標"""
        # 模擬 GPU 使用率 (Sionna 計算負載)
        base_utilization = 60 + 30 * math.sin(elapsed_time / 300)  # 30-90%
        utilization = base_utilization + random.uniform(-10, 10)
        utilization = max(0, min(100, utilization))

        self.sionna_gpu_utilization.labels(
            environment="prod", gpu_id="0", service="sionna"
        ).set(utilization)

        # GPU 記憶體使用
        memory_usage = 8000 + 2000 * math.cos(elapsed_time / 200)  # 6-10GB
        memory_usage += random.uniform(-500, 500)
        memory_usage = max(0, memory_usage)

        self.sionna_gpu_memory_usage.labels(
            environment="prod", gpu_id="0", service="sionna"
        ).set(memory_usage)

    def _update_system_metrics(self, elapsed_time: float):
        """更新系統資源指標"""
        # CPU 使用率模擬
        cpu_usage = 40 + 30 * math.sin(elapsed_time / 240)  # 10-70%
        cpu_usage += random.uniform(-5, 5)
        cpu_usage = max(0, min(100, cpu_usage))

        # 模擬多核 CPU
        for cpu_id in range(8):
            cpu_variation = random.uniform(-10, 10)
            cpu_core_usage = max(0, min(100, cpu_usage + cpu_variation))

            # idle time = 100 - usage
            idle_time = 100 - cpu_core_usage

            self.node_cpu_seconds.labels(mode="idle", cpu=str(cpu_id)).inc(
                idle_time / 100
            )  # 轉換為秒

        # 記憶體使用模擬
        total_memory = 16 * 1024 * 1024 * 1024  # 16GB
        memory_usage_percent = 40 + 20 * math.sin(elapsed_time / 360)  # 20-60%
        memory_usage_percent += random.uniform(-5, 5)
        memory_usage_percent = max(10, min(90, memory_usage_percent))

        available_memory = total_memory * (1 - memory_usage_percent / 100)

        self.node_memory_available.set(available_memory)

    def get_metrics(self) -> str:
        """獲取指標數據"""
        return generate_latest(self.registry).decode("utf-8")

    def start_http_server(self, port: int = 8000):
        """啟動 HTTP 服務器"""

        def metrics_handler():
            return self.get_metrics()

        start_http_server(port, registry=self.registry)
        logger.info(f"指標 HTTP 服務器已啟動，端口: {port}")


def signal_handler(sig, frame):
    """信號處理器"""
    logger.info("收到停止信號，正在關閉...")
    sys.exit(0)


def main():
    """主程序"""
    parser = argparse.ArgumentParser(description="NTN Stack 指標模擬器")
    parser.add_argument("--num-uavs", type=int, default=5, help="UAV 數量 (默認: 5)")
    parser.add_argument(
        "--duration", type=int, default=3600, help="模擬持續時間（秒，默認: 3600）"
    )
    parser.add_argument(
        "--interval", type=float, default=1.0, help="更新間隔（秒，默認: 1.0）"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="HTTP 服務器端口 (默認: 8000)"
    )
    parser.add_argument("--enable-anomalies", action="store_true", help="啟用異常模擬")
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 設置信號處理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 創建模擬配置
    config = SimulationConfig(
        num_uavs=args.num_uavs,
        simulation_duration=args.duration,
        update_interval=args.interval,
        enable_anomalies=args.enable_anomalies,
    )

    # 創建模擬器
    simulator = MetricsSimulator(config)

    # 啟動 HTTP 服務器
    simulator.start_http_server(args.port)

    logger.info(f"指標模擬器配置:")
    logger.info(f"  UAV 數量: {config.num_uavs}")
    logger.info(f"  持續時間: {config.simulation_duration}s")
    logger.info(f"  更新間隔: {config.update_interval}s")
    logger.info(f"  異常模擬: {config.enable_anomalies}")
    logger.info(f"  HTTP 端口: {args.port}")
    logger.info(f"  指標端點: http://localhost:{args.port}/metrics")

    try:
        # 開始模擬
        simulator.start_simulation()
    except KeyboardInterrupt:
        logger.info("收到中斷信號")
    finally:
        simulator.stop_simulation()
        logger.info("模擬器已停止")


if __name__ == "__main__":
    main()
