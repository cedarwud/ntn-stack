#!/usr/bin/env python3
"""
NTN Stack 端到端測試系統監控器

這個工具用於監控測試過程中的系統狀態，包括資源使用、服務健康和網絡狀況。
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback

import psutil
import aiohttp
import docker
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, Counter, start_http_server

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("tests/e2e/logs/system_monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class SystemMetrics:
    """系統指標收集器"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics = {}
        self._setup_metrics()

    def _setup_metrics(self):
        """設置系統監控指標"""
        # CPU 指標
        self.metrics["cpu_percent"] = Gauge(
            "system_cpu_percent",
            "CPU usage percentage",
            ["host"],
            registry=self.registry,
        )

        self.metrics["cpu_count"] = Gauge(
            "system_cpu_count", "Number of CPU cores", ["host"], registry=self.registry
        )

        # 記憶體指標
        self.metrics["memory_percent"] = Gauge(
            "system_memory_percent",
            "Memory usage percentage",
            ["host"],
            registry=self.registry,
        )

        self.metrics["memory_available_gb"] = Gauge(
            "system_memory_available_gb",
            "Available memory in GB",
            ["host"],
            registry=self.registry,
        )

        # 磁盤指標
        self.metrics["disk_percent"] = Gauge(
            "system_disk_percent",
            "Disk usage percentage",
            ["host", "mountpoint"],
            registry=self.registry,
        )

        self.metrics["disk_free_gb"] = Gauge(
            "system_disk_free_gb",
            "Free disk space in GB",
            ["host", "mountpoint"],
            registry=self.registry,
        )

        # 網絡指標
        self.metrics["network_bytes_sent"] = Counter(
            "system_network_bytes_sent",
            "Network bytes sent",
            ["host", "interface"],
            registry=self.registry,
        )

        self.metrics["network_bytes_recv"] = Counter(
            "system_network_bytes_recv",
            "Network bytes received",
            ["host", "interface"],
            registry=self.registry,
        )

        # 進程指標
        self.metrics["process_count"] = Gauge(
            "system_process_count",
            "Number of running processes",
            ["host"],
            registry=self.registry,
        )

        # 負載指標
        self.metrics["load_average_1m"] = Gauge(
            "system_load_average_1m",
            "1-minute load average",
            ["host"],
            registry=self.registry,
        )


class ServiceHealthMonitor:
    """服務健康監控器"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics = {}
        self.docker_client = None
        self._setup_metrics()
        self._setup_docker()

    def _setup_metrics(self):
        """設置服務健康指標"""
        self.metrics["service_up"] = Gauge(
            "service_up",
            "Service health status (1=up, 0=down)",
            ["service_name", "endpoint"],
            registry=self.registry,
        )

        self.metrics["service_response_time"] = Gauge(
            "service_response_time_ms",
            "Service response time in milliseconds",
            ["service_name", "endpoint"],
            registry=self.registry,
        )

        self.metrics["container_up"] = Gauge(
            "container_up",
            "Container status (1=running, 0=stopped)",
            ["container_name", "image"],
            registry=self.registry,
        )

        self.metrics["container_cpu_percent"] = Gauge(
            "container_cpu_percent",
            "Container CPU usage percentage",
            ["container_name"],
            registry=self.registry,
        )

        self.metrics["container_memory_mb"] = Gauge(
            "container_memory_mb",
            "Container memory usage in MB",
            ["container_name"],
            registry=self.registry,
        )

    def _setup_docker(self):
        """設置 Docker 客戶端"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker 客戶端初始化成功")
        except Exception as e:
            logger.warning(f"無法連接到 Docker: {e}")
            self.docker_client = None

    async def check_service_health(
        self, service_name: str, endpoint: str, timeout: int = 5
    ) -> Dict[str, Any]:
        """檢查服務健康狀態"""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(endpoint) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        self.metrics["service_up"].labels(
                            service_name=service_name, endpoint=endpoint
                        ).set(1)
                        self.metrics["service_response_time"].labels(
                            service_name=service_name, endpoint=endpoint
                        ).set(response_time)

                        return {
                            "service": service_name,
                            "status": "healthy",
                            "response_time_ms": response_time,
                            "status_code": response.status,
                        }
                    else:
                        self.metrics["service_up"].labels(
                            service_name=service_name, endpoint=endpoint
                        ).set(0)
                        return {
                            "service": service_name,
                            "status": "unhealthy",
                            "response_time_ms": response_time,
                            "status_code": response.status,
                        }

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.metrics["service_up"].labels(
                service_name=service_name, endpoint=endpoint
            ).set(0)

            return {
                "service": service_name,
                "status": "error",
                "response_time_ms": response_time,
                "error": str(e),
            }

    def check_container_status(self) -> List[Dict[str, Any]]:
        """檢查容器狀態"""
        if not self.docker_client:
            return []

        container_stats = []

        try:
            containers = self.docker_client.containers.list(all=True)

            for container in containers:
                try:
                    # 基本狀態
                    is_running = container.status == "running"
                    self.metrics["container_up"].labels(
                        container_name=container.name,
                        image=(
                            container.image.tags[0]
                            if container.image.tags
                            else "unknown"
                        ),
                    ).set(1 if is_running else 0)

                    stats = {
                        "name": container.name,
                        "status": container.status,
                        "image": (
                            container.image.tags[0]
                            if container.image.tags
                            else "unknown"
                        ),
                        "created": container.attrs["Created"],
                        "running": is_running,
                    }

                    # 如果容器運行中，獲取資源使用情況
                    if is_running:
                        try:
                            container_stats_stream = container.stats(stream=False)

                            # CPU 使用率計算
                            cpu_stats = container_stats_stream["cpu_stats"]
                            precpu_stats = container_stats_stream["precpu_stats"]

                            cpu_delta = (
                                cpu_stats["cpu_usage"]["total_usage"]
                                - precpu_stats["cpu_usage"]["total_usage"]
                            )
                            system_delta = (
                                cpu_stats["system_cpu_usage"]
                                - precpu_stats["system_cpu_usage"]
                            )

                            if system_delta > 0:
                                cpu_percent = (
                                    (cpu_delta / system_delta)
                                    * len(cpu_stats["cpu_usage"]["percpu_usage"])
                                    * 100
                                )
                            else:
                                cpu_percent = 0

                            # 記憶體使用
                            memory_stats = container_stats_stream["memory_stats"]
                            memory_usage_mb = memory_stats["usage"] / (1024 * 1024)

                            # 記錄指標
                            self.metrics["container_cpu_percent"].labels(
                                container_name=container.name
                            ).set(cpu_percent)
                            self.metrics["container_memory_mb"].labels(
                                container_name=container.name
                            ).set(memory_usage_mb)

                            stats.update(
                                {
                                    "cpu_percent": cpu_percent,
                                    "memory_usage_mb": memory_usage_mb,
                                    "memory_limit_mb": memory_stats.get("limit", 0)
                                    / (1024 * 1024),
                                }
                            )

                        except Exception as e:
                            logger.warning(
                                f"無法獲取容器 {container.name} 的資源統計: {e}"
                            )

                    container_stats.append(stats)

                except Exception as e:
                    logger.error(f"檢查容器 {container.name} 時發生錯誤: {e}")

        except Exception as e:
            logger.error(f"獲取容器列表失敗: {e}")

        return container_stats


class NetworkMonitor:
    """網絡監控器"""

    def __init__(self):
        self.previous_stats = {}

    def get_network_stats(self) -> Dict[str, Any]:
        """獲取網絡統計信息"""
        try:
            # 網絡接口統計
            net_io = psutil.net_io_counters(pernic=True)

            network_stats = {
                "interfaces": {},
                "total": {
                    "bytes_sent": 0,
                    "bytes_recv": 0,
                    "packets_sent": 0,
                    "packets_recv": 0,
                },
            }

            for interface, stats in net_io.items():
                interface_stats = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "packets_sent": stats.packets_sent,
                    "packets_recv": stats.packets_recv,
                    "errin": stats.errin,
                    "errout": stats.errout,
                    "dropin": stats.dropin,
                    "dropout": stats.dropout,
                }

                # 計算速率 (如果有之前的數據)
                if interface in self.previous_stats:
                    time_delta = (
                        time.time() - self.previous_stats[interface]["timestamp"]
                    )
                    if time_delta > 0:
                        bytes_sent_rate = (
                            stats.bytes_sent
                            - self.previous_stats[interface]["bytes_sent"]
                        ) / time_delta
                        bytes_recv_rate = (
                            stats.bytes_recv
                            - self.previous_stats[interface]["bytes_recv"]
                        ) / time_delta

                        interface_stats.update(
                            {
                                "bytes_sent_rate": bytes_sent_rate,
                                "bytes_recv_rate": bytes_recv_rate,
                            }
                        )

                # 更新歷史數據
                self.previous_stats[interface] = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "timestamp": time.time(),
                }

                network_stats["interfaces"][interface] = interface_stats

                # 累計總數
                network_stats["total"]["bytes_sent"] += stats.bytes_sent
                network_stats["total"]["bytes_recv"] += stats.bytes_recv
                network_stats["total"]["packets_sent"] += stats.packets_sent
                network_stats["total"]["packets_recv"] += stats.packets_recv

            # 網絡連接統計
            connections = psutil.net_connections()
            connection_stats = {
                "total": len(connections),
                "by_status": {},
                "by_family": {},
            }

            for conn in connections:
                status = conn.status if conn.status else "UNKNOWN"
                family = (
                    conn.family.name
                    if hasattr(conn.family, "name")
                    else str(conn.family)
                )

                connection_stats["by_status"][status] = (
                    connection_stats["by_status"].get(status, 0) + 1
                )
                connection_stats["by_family"][family] = (
                    connection_stats["by_family"].get(family, 0) + 1
                )

            network_stats["connections"] = connection_stats

            return network_stats

        except Exception as e:
            logger.error(f"獲取網絡統計失敗: {e}")
            return {}


class SystemMonitor:
    """系統監控主類"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = False
        self.monitor_task = None

        # 初始化監控器組件
        self.system_metrics = SystemMetrics()
        self.service_monitor = ServiceHealthMonitor()
        self.network_monitor = NetworkMonitor()

        # 監控數據存儲
        self.monitoring_data = []

        # 服務配置
        self.services_to_monitor = config.get("services", [])
        self.components_to_monitor = config.get("components", [])

    async def start_monitoring(self, duration: Optional[int] = None):
        """開始監控"""
        logger.info("開始系統監控...")
        self.monitoring = True

        # 啟動 Prometheus 指標服務器
        if self.config.get("prometheus_port"):
            start_http_server(self.config["prometheus_port"])
            logger.info(
                f"Prometheus 指標服務器已啟動，端口: {self.config['prometheus_port']}"
            )

        # 創建監控任務
        tasks = [
            asyncio.create_task(self._system_monitoring_loop()),
            asyncio.create_task(self._service_monitoring_loop()),
            asyncio.create_task(self._network_monitoring_loop()),
        ]

        if duration:
            # 設置定時停止
            asyncio.create_task(self._stop_after_duration(duration))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("監控任務已取消")
        finally:
            self.monitoring = False

    async def stop_monitoring(self):
        """停止監控"""
        logger.info("停止系統監控...")
        self.monitoring = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

    async def _stop_after_duration(self, duration: int):
        """在指定時間後停止監控"""
        await asyncio.sleep(duration)
        await self.stop_monitoring()

    async def _system_monitoring_loop(self):
        """系統資源監控循環"""
        while self.monitoring:
            try:
                hostname = self.config.get("hostname", "localhost")

                # CPU 監控
                cpu_percent = psutil.cpu_percent()
                cpu_count = psutil.cpu_count()

                self.system_metrics.metrics["cpu_percent"].labels(host=hostname).set(
                    cpu_percent
                )
                self.system_metrics.metrics["cpu_count"].labels(host=hostname).set(
                    cpu_count
                )

                # 記憶體監控
                memory = psutil.virtual_memory()
                memory_available_gb = memory.available / (1024**3)

                self.system_metrics.metrics["memory_percent"].labels(host=hostname).set(
                    memory.percent
                )
                self.system_metrics.metrics["memory_available_gb"].labels(
                    host=hostname
                ).set(memory_available_gb)

                # 磁盤監控
                for partition in psutil.disk_partitions():
                    try:
                        disk_usage = psutil.disk_usage(partition.mountpoint)
                        disk_free_gb = disk_usage.free / (1024**3)

                        self.system_metrics.metrics["disk_percent"].labels(
                            host=hostname, mountpoint=partition.mountpoint
                        ).set(disk_usage.percent)

                        self.system_metrics.metrics["disk_free_gb"].labels(
                            host=hostname, mountpoint=partition.mountpoint
                        ).set(disk_free_gb)

                    except PermissionError:
                        continue

                # 進程數量
                process_count = len(psutil.pids())
                self.system_metrics.metrics["process_count"].labels(host=hostname).set(
                    process_count
                )

                # 負載平均值 (僅限 Unix 系統)
                try:
                    load_avg = psutil.getloadavg()
                    self.system_metrics.metrics["load_average_1m"].labels(
                        host=hostname
                    ).set(load_avg[0])
                except AttributeError:
                    # Windows 系統不支持 getloadavg
                    pass

                # 記錄監控數據
                timestamp = datetime.now()
                self.monitoring_data.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "type": "system",
                        "data": {
                            "cpu_percent": cpu_percent,
                            "memory_percent": memory.percent,
                            "memory_available_gb": memory_available_gb,
                            "process_count": process_count,
                        },
                    }
                )

                await asyncio.sleep(self.config.get("system_monitor_interval", 5))

            except Exception as e:
                logger.error(f"系統監控循環錯誤: {e}")
                await asyncio.sleep(5)

    async def _service_monitoring_loop(self):
        """服務健康監控循環"""
        while self.monitoring:
            try:
                # 檢查 HTTP 服務健康狀態
                for service in self.services_to_monitor:
                    service_name = service.get("name")
                    endpoint = service.get("endpoint")

                    if service_name and endpoint:
                        health_result = await self.service_monitor.check_service_health(
                            service_name, endpoint
                        )

                        timestamp = datetime.now()
                        self.monitoring_data.append(
                            {
                                "timestamp": timestamp.isoformat(),
                                "type": "service_health",
                                "data": health_result,
                            }
                        )

                # 檢查容器狀態
                container_stats = self.service_monitor.check_container_status()
                if container_stats:
                    timestamp = datetime.now()
                    self.monitoring_data.append(
                        {
                            "timestamp": timestamp.isoformat(),
                            "type": "container_stats",
                            "data": container_stats,
                        }
                    )

                await asyncio.sleep(self.config.get("service_monitor_interval", 10))

            except Exception as e:
                logger.error(f"服務監控循環錯誤: {e}")
                await asyncio.sleep(10)

    async def _network_monitoring_loop(self):
        """網絡監控循環"""
        while self.monitoring:
            try:
                network_stats = self.network_monitor.get_network_stats()

                if network_stats:
                    timestamp = datetime.now()
                    self.monitoring_data.append(
                        {
                            "timestamp": timestamp.isoformat(),
                            "type": "network",
                            "data": network_stats,
                        }
                    )

                await asyncio.sleep(self.config.get("network_monitor_interval", 15))

            except Exception as e:
                logger.error(f"網絡監控循環錯誤: {e}")
                await asyncio.sleep(15)

    def generate_report(
        self, output_format: str = "json", output_file: Optional[str] = None
    ):
        """生成監控報告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if not self.monitoring_data:
                logger.warning("沒有監控數據可生成報告")
                return

            # 數據分析
            df = pd.DataFrame(self.monitoring_data)

            # 生成摘要統計
            summary = self._generate_summary_stats(df)

            if output_format.lower() == "json":
                report = {
                    "monitoring_report_id": f"system_monitor_{timestamp}",
                    "timestamp": timestamp,
                    "monitoring_duration": self._calculate_monitoring_duration(),
                    "summary": summary,
                    "raw_data": self.monitoring_data,
                }

                if output_file:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(report, f, indent=2, ensure_ascii=False)
                    logger.info(f"JSON 報告已生成: {output_file}")
                else:
                    print(json.dumps(report, indent=2, ensure_ascii=False))

            elif output_format.lower() == "html":
                html_content = self._generate_html_report(summary)

                if output_file:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info(f"HTML 報告已生成: {output_file}")
                else:
                    print(html_content)

            else:
                logger.error(f"不支援的報告格式: {output_format}")

        except Exception as e:
            logger.error(f"生成監控報告失敗: {e}")

    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成摘要統計"""
        summary = {
            "total_data_points": len(df),
            "monitoring_types": df["type"].value_counts().to_dict(),
            "time_range": {
                "start": df["timestamp"].min() if not df.empty else None,
                "end": df["timestamp"].max() if not df.empty else None,
            },
        }

        # 系統資源摘要
        system_data = df[df["type"] == "system"]
        if not system_data.empty:
            cpu_values = [
                d["data"]["cpu_percent"] for d in system_data.to_dict("records")
            ]
            memory_values = [
                d["data"]["memory_percent"] for d in system_data.to_dict("records")
            ]

            summary["system_resources"] = {
                "cpu": {
                    "avg": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values),
                },
                "memory": {
                    "avg": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values),
                },
            }

        # 服務健康摘要
        service_data = df[df["type"] == "service_health"]
        if not service_data.empty:
            service_status = {}
            for record in service_data.to_dict("records"):
                service_name = record["data"]["service"]
                status = record["data"]["status"]
                if service_name not in service_status:
                    service_status[service_name] = {
                        "healthy": 0,
                        "unhealthy": 0,
                        "error": 0,
                    }
                service_status[service_name][status] = (
                    service_status[service_name].get(status, 0) + 1
                )

            summary["service_health"] = service_status

        return summary

    def _calculate_monitoring_duration(self) -> Optional[str]:
        """計算監控持續時間"""
        if not self.monitoring_data:
            return None

        start_time = datetime.fromisoformat(self.monitoring_data[0]["timestamp"])
        end_time = datetime.fromisoformat(self.monitoring_data[-1]["timestamp"])
        duration = end_time - start_time

        return str(duration)

    def _generate_html_report(self, summary: Dict[str, Any]) -> str:
        """生成 HTML 監控報告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>NTN Stack 系統監控報告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; }
                .metric { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .good { border-left: 5px solid #4CAF50; }
                .warning { border-left: 5px solid #ff9800; }
                .critical { border-left: 5px solid #f44336; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>NTN Stack 系統監控報告</h1>
                <p>生成時間: {timestamp}</p>
                <p>監控持續時間: {duration}</p>
            </div>
            
            <div class="section">
                <h2>系統資源摘要</h2>
                {system_resources_html}
            </div>
            
            <div class="section">
                <h2>服務健康狀態</h2>
                {service_health_html}
            </div>
        </body>
        </html>
        """

        # 生成系統資源 HTML
        system_resources_html = ""
        if "system_resources" in summary:
            cpu_avg = summary["system_resources"]["cpu"]["avg"]
            memory_avg = summary["system_resources"]["memory"]["avg"]

            cpu_class = (
                "good" if cpu_avg < 70 else "warning" if cpu_avg < 85 else "critical"
            )
            memory_class = (
                "good"
                if memory_avg < 70
                else "warning" if memory_avg < 85 else "critical"
            )

            system_resources_html = f"""
            <div class="metric {cpu_class}">
                <h3>CPU 使用率</h3>
                <p>平均: {cpu_avg:.1f}%</p>
                <p>最大: {summary['system_resources']['cpu']['max']:.1f}%</p>
                <p>最小: {summary['system_resources']['cpu']['min']:.1f}%</p>
            </div>
            <div class="metric {memory_class}">
                <h3>記憶體使用率</h3>
                <p>平均: {memory_avg:.1f}%</p>
                <p>最大: {summary['system_resources']['memory']['max']:.1f}%</p>
                <p>最小: {summary['system_resources']['memory']['min']:.1f}%</p>
            </div>
            """

        # 生成服務健康 HTML
        service_health_html = ""
        if "service_health" in summary:
            service_health_html = "<table><tr><th>服務名稱</th><th>健康</th><th>不健康</th><th>錯誤</th></tr>"
            for service, stats in summary["service_health"].items():
                service_health_html += f"""
                <tr>
                    <td>{service}</td>
                    <td>{stats.get('healthy', 0)}</td>
                    <td>{stats.get('unhealthy', 0)}</td>
                    <td>{stats.get('error', 0)}</td>
                </tr>
                """
            service_health_html += "</table>"

        return html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration=self._calculate_monitoring_duration() or "N/A",
            system_resources_html=system_resources_html,
            service_health_html=service_health_html,
        )


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="NTN Stack 系統監控器")

    parser.add_argument("--duration", type=int, help="監控持續時間 (秒)")
    parser.add_argument("--components", type=str, help="要監控的組件列表 (逗號分隔)")
    parser.add_argument(
        "--analysis",
        type=str,
        choices=["performance", "health", "network"],
        help="執行特定分析",
    )
    parser.add_argument(
        "--report", type=str, choices=["json", "html"], help="生成監控報告的格式"
    )
    parser.add_argument(
        "--prometheus-port", type=int, default=9091, help="Prometheus 指標服務器端口"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日誌級別",
    )

    args = parser.parse_args()

    # 設置日誌級別
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # 創建必要的目錄
    Path("tests/e2e/logs").mkdir(parents=True, exist_ok=True)
    Path("tests/e2e/reports").mkdir(parents=True, exist_ok=True)

    # 配置監控器
    config = {
        "hostname": "localhost",
        "prometheus_port": args.prometheus_port,
        "system_monitor_interval": 5,
        "service_monitor_interval": 10,
        "network_monitor_interval": 15,
        "services": [
            {"name": "netstack", "endpoint": "http://localhost:8000/health"},
            {"name": "simworld", "endpoint": "http://localhost:8100/health"},
            {"name": "prometheus", "endpoint": "http://localhost:9090/-/healthy"},
            {"name": "grafana", "endpoint": "http://localhost:3000/api/health"},
        ],
        "components": args.components.split(",") if args.components else [],
    }

    # 創建並運行監控器
    monitor = SystemMonitor(config)

    try:
        asyncio.run(monitor.start_monitoring(args.duration))

        # 生成報告
        if args.report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if args.report == "html":
                output_file = (
                    f"tests/e2e/reports/system_monitor_report_{timestamp}.html"
                )
            else:
                output_file = (
                    f"tests/e2e/reports/system_monitor_report_{timestamp}.json"
                )

            monitor.generate_report(args.report, output_file)

    except KeyboardInterrupt:
        logger.info("監控被用戶中斷")
    except Exception as e:
        logger.error(f"監控過程中發生錯誤: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
