#!/usr/bin/env python3
"""
NTN Stack 端到端測試場景執行器

這個工具用於執行標準化的端到端測試場景，支援並行執行、實時監控和自動報告生成。
"""

import argparse
import asyncio
import json
import logging
import sys
import time
import yaml
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import traceback

import requests
import psutil
import aiohttp
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("tests/e2e/logs/scenario_executor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class E2EMetricsCollector:
    """端到端測試指標收集器"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics = {}
        self._setup_metrics()

    def _setup_metrics(self):
        """設置基本指標"""
        self.metrics["latency"] = Histogram(
            "e2e_latency_ms",
            "End-to-end latency in milliseconds",
            ["scenario", "component"],
            registry=self.registry,
        )

        self.metrics["throughput"] = Gauge(
            "e2e_throughput_mbps",
            "Throughput in Mbps",
            ["scenario", "direction"],
            registry=self.registry,
        )

        self.metrics["success_rate"] = Gauge(
            "e2e_success_rate",
            "Success rate percentage",
            ["scenario", "operation"],
            registry=self.registry,
        )

        self.metrics["error_count"] = Counter(
            "e2e_error_count",
            "Error count",
            ["scenario", "error_type"],
            registry=self.registry,
        )

        self.metrics["resource_usage"] = Gauge(
            "e2e_resource_usage_percent",
            "Resource usage percentage",
            ["scenario", "resource_type"],
            registry=self.registry,
        )

    def record_latency(self, scenario: str, component: str, latency_ms: float):
        """記錄延遲指標"""
        self.metrics["latency"].labels(scenario=scenario, component=component).observe(
            latency_ms
        )

    def record_throughput(self, scenario: str, direction: str, throughput_mbps: float):
        """記錄吞吐量指標"""
        self.metrics["throughput"].labels(scenario=scenario, direction=direction).set(
            throughput_mbps
        )

    def record_success_rate(self, scenario: str, operation: str, rate: float):
        """記錄成功率指標"""
        self.metrics["success_rate"].labels(scenario=scenario, operation=operation).set(
            rate
        )

    def record_error(self, scenario: str, error_type: str):
        """記錄錯誤指標"""
        self.metrics["error_count"].labels(
            scenario=scenario, error_type=error_type
        ).inc()

    def record_resource_usage(
        self, scenario: str, resource_type: str, usage_percent: float
    ):
        """記錄資源使用指標"""
        self.metrics["resource_usage"].labels(
            scenario=scenario, resource_type=resource_type
        ).set(usage_percent)


class SystemMonitor:
    """系統資源監控器"""

    def __init__(self, metrics_collector: E2EMetricsCollector):
        self.metrics_collector = metrics_collector
        self.monitoring = False
        self.monitor_task = None

    async def start_monitoring(self, scenario: str):
        """開始監控系統資源"""
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(scenario))

    async def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self, scenario: str):
        """監控循環"""
        while self.monitoring:
            try:
                # CPU 使用率
                cpu_percent = psutil.cpu_percent()
                self.metrics_collector.record_resource_usage(
                    scenario, "cpu", cpu_percent
                )

                # 記憶體使用率
                memory = psutil.virtual_memory()
                self.metrics_collector.record_resource_usage(
                    scenario, "memory", memory.percent
                )

                # 網絡使用率 (簡化計算)
                network = psutil.net_io_counters()
                network_percent = min(
                    (network.bytes_sent + network.bytes_recv)
                    / (1024 * 1024 * 100)
                    * 100,
                    100,
                )
                self.metrics_collector.record_resource_usage(
                    scenario, "network", network_percent
                )

                await asyncio.sleep(5)  # 每5秒監控一次

            except Exception as e:
                logger.error(f"監控系統資源時發生錯誤: {e}")
                await asyncio.sleep(5)


class TestEnvironment:
    """測試環境管理"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services = {}
        self.health_checks = {}

    async def setup(self) -> bool:
        """設置測試環境"""
        try:
            logger.info("設置測試環境...")

            # 檢查系統需求
            if not await self._check_system_requirements():
                return False

            # 啟動必要服務
            if not await self._start_services():
                return False

            # 等待服務就緒
            if not await self._wait_for_services():
                return False

            logger.info("測試環境設置完成")
            return True

        except Exception as e:
            logger.error(f"設置測試環境失敗: {e}")
            return False

    async def teardown(self):
        """清理測試環境"""
        try:
            logger.info("清理測試環境...")
            # 這裡可以添加清理邏輯
            await asyncio.sleep(1)  # 模擬清理時間
            logger.info("測試環境清理完成")
        except Exception as e:
            logger.error(f"清理測試環境失敗: {e}")

    async def _check_system_requirements(self) -> bool:
        """檢查系統需求"""
        try:
            # 檢查 CPU 核心數
            cpu_count = psutil.cpu_count()
            min_cpu = self.config.get("min_cpu_cores", 4)
            if cpu_count < min_cpu:
                logger.error(f"CPU 核心數不足: {cpu_count} < {min_cpu}")
                return False

            # 檢查記憶體
            memory = psutil.virtual_memory()
            min_memory_gb = self.config.get("min_memory_gb", 8)
            if memory.total / (1024**3) < min_memory_gb:
                logger.error(
                    f"記憶體不足: {memory.total / (1024**3):.1f}GB < {min_memory_gb}GB"
                )
                return False

            # 檢查磁盤空間
            disk = psutil.disk_usage("/")
            min_disk_gb = self.config.get("min_disk_gb", 20)
            if disk.free / (1024**3) < min_disk_gb:
                logger.error(
                    f"磁盤空間不足: {disk.free / (1024**3):.1f}GB < {min_disk_gb}GB"
                )
                return False

            logger.info("系統需求檢查通過")
            return True

        except Exception as e:
            logger.error(f"系統需求檢查失敗: {e}")
            return False

    async def _start_services(self) -> bool:
        """啟動必要服務"""
        try:
            # 這裡可以添加啟動 Docker 容器的邏輯
            # 目前簡化為檢查服務是否已運行
            logger.info("檢查服務狀態...")
            await asyncio.sleep(2)  # 模擬啟動時間
            return True
        except Exception as e:
            logger.error(f"啟動服務失敗: {e}")
            return False

    async def _wait_for_services(self) -> bool:
        """等待服務就緒"""
        try:
            services = [
                {"name": "netstack", "url": "http://localhost:8000/health"},
                {"name": "simworld", "url": "http://localhost:8100/health"},
            ]

            for service in services:
                if not await self._check_service_health(
                    service["name"], service["url"]
                ):
                    return False

            return True
        except Exception as e:
            logger.error(f"等待服務就緒失敗: {e}")
            return False

    async def _check_service_health(
        self, service_name: str, health_url: str, max_retries: int = 30
    ) -> bool:
        """檢查服務健康狀態"""
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as session:
                    async with session.get(health_url) as response:
                        if response.status == 200:
                            logger.info(f"服務 {service_name} 已就緒")
                            return True
            except Exception:
                pass

            logger.info(
                f"等待服務 {service_name} 就緒... ({attempt + 1}/{max_retries})"
            )
            await asyncio.sleep(2)

        logger.error(f"服務 {service_name} 未能在預期時間內就緒")
        return False


class TestScenario:
    """測試場景基類"""

    def __init__(
        self, name: str, config: Dict[str, Any], metrics_collector: E2EMetricsCollector
    ):
        self.name = name
        self.config = config
        self.metrics_collector = metrics_collector
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.errors = []

    async def execute(self) -> Dict[str, Any]:
        """執行測試場景"""
        logger.info(f"開始執行測試場景: {self.name}")
        self.start_time = datetime.now()

        try:
            # 前置設置
            await self.setup()

            # 執行測試步驟
            for step in self.config.get("test_steps", []):
                await self.execute_step(step)

            # 後置清理
            await self.cleanup()

            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()

            # 評估結果
            passed = await self.evaluate_results()

            result = {
                "scenario": self.name,
                "status": "PASSED" if passed else "FAILED",
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "results": self.results,
                "errors": self.errors,
            }

            logger.info(f"測試場景 {self.name} 完成: {result['status']}")
            return result

        except Exception as e:
            self.end_time = datetime.now()
            error_msg = f"測試場景 {self.name} 執行失敗: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            return {
                "scenario": self.name,
                "status": "ERROR",
                "duration_seconds": (
                    (self.end_time - self.start_time).total_seconds()
                    if self.start_time
                    else 0
                ),
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat(),
                "results": self.results,
                "errors": self.errors + [error_msg],
            }

    async def setup(self):
        """前置設置"""
        pass

    async def cleanup(self):
        """後置清理"""
        pass

    async def execute_step(self, step: str):
        """執行測試步驟"""
        logger.info(f"執行測試步驟: {step}")

        # 根據步驟類型執行不同邏輯
        if step == "initialize_uav_terminal":
            await self._initialize_uav_terminal()
        elif step == "establish_satellite_connection":
            await self._establish_satellite_connection()
        elif step == "measure_connection_quality":
            await self._measure_connection_quality()
        elif step == "perform_data_transfer":
            await self._perform_data_transfer()
        elif step == "verify_data_integrity":
            await self._verify_data_integrity()
        else:
            logger.warning(f"未知的測試步驟: {step}")

    async def evaluate_results(self) -> bool:
        """評估測試結果"""
        pass_criteria = self.config.get("pass_criteria", {})

        for criterion_name, expected_value in pass_criteria.items():
            if criterion_name in self.results:
                actual_value = self.results[criterion_name]
                if actual_value != expected_value:
                    logger.warning(
                        f"測試標準 {criterion_name} 未通過: {actual_value} != {expected_value}"
                    )
                    return False

        return len(self.errors) == 0

    # 以下是具體的測試步驟實現
    async def _initialize_uav_terminal(self):
        """初始化 UAV 終端"""
        try:
            # 模擬 UAV 終端初始化
            await asyncio.sleep(1)
            self.results["uav_terminal_initialized"] = True
            logger.info("UAV 終端初始化完成")
        except Exception as e:
            self.errors.append(f"UAV 終端初始化失敗: {e}")
            self.results["uav_terminal_initialized"] = False

    async def _establish_satellite_connection(self):
        """建立衛星連接"""
        try:
            start_time = time.time()

            # 模擬連接建立過程
            await asyncio.sleep(0.5)

            end_time = time.time()
            connection_time_ms = (end_time - start_time) * 1000

            # 記錄連接延遲
            self.metrics_collector.record_latency(
                self.name, "satellite_connection", connection_time_ms
            )

            self.results["connection_established"] = True
            self.results["connection_time_ms"] = connection_time_ms
            self.results["latency_within_target"] = (
                connection_time_ms
                <= self.config.get("kpi_targets", {})
                .get("e2e_latency", "<= 50ms")
                .replace("<= ", "")
                .replace("ms", "")
            )

            logger.info(f"衛星連接建立完成，耗時: {connection_time_ms:.2f}ms")

        except Exception as e:
            self.errors.append(f"建立衛星連接失敗: {e}")
            self.results["connection_established"] = False
            self.results["latency_within_target"] = False

    async def _measure_connection_quality(self):
        """測量連接質量"""
        try:
            # 模擬連接質量測量
            await asyncio.sleep(0.2)

            # 模擬質量指標
            signal_strength = 85.5  # dBm
            snr = 15.2  # dB
            error_rate = 0.001  # 0.1%

            self.results["signal_strength_dbm"] = signal_strength
            self.results["snr_db"] = snr
            self.results["error_rate"] = error_rate

            # 記錄成功率
            success_rate = (1 - error_rate) * 100
            self.metrics_collector.record_success_rate(
                self.name, "connection", success_rate
            )

            logger.info(
                f"連接質量測量完成: 信號強度={signal_strength}dBm, SNR={snr}dB, 錯誤率={error_rate*100:.3f}%"
            )

        except Exception as e:
            self.errors.append(f"測量連接質量失敗: {e}")

    async def _perform_data_transfer(self):
        """執行數據傳輸"""
        try:
            # 模擬數據傳輸
            transfer_size_mb = 10
            start_time = time.time()

            # 模擬傳輸過程
            await asyncio.sleep(0.8)

            end_time = time.time()
            transfer_time_s = end_time - start_time
            throughput_mbps = (transfer_size_mb * 8) / transfer_time_s

            # 記錄吞吐量
            self.metrics_collector.record_throughput(
                self.name, "upload", throughput_mbps
            )

            self.results["data_transfer_completed"] = True
            self.results["throughput_mbps"] = throughput_mbps
            self.results["transfer_time_s"] = transfer_time_s

            logger.info(
                f"數據傳輸完成: {transfer_size_mb}MB, 吞吐量={throughput_mbps:.2f}Mbps"
            )

        except Exception as e:
            self.errors.append(f"數據傳輸失敗: {e}")
            self.results["data_transfer_completed"] = False

    async def _verify_data_integrity(self):
        """驗證數據完整性"""
        try:
            # 模擬數據完整性檢查
            await asyncio.sleep(0.1)

            # 模擬檢查結果 (假設 99.9% 完整性)
            integrity_rate = 99.9

            self.results["data_integrity_verified"] = True
            self.results["data_integrity_rate"] = integrity_rate
            self.results["no_data_corruption"] = integrity_rate >= 99.5

            logger.info(f"數據完整性驗證完成: {integrity_rate}%")

        except Exception as e:
            self.errors.append(f"數據完整性驗證失敗: {e}")
            self.results["data_integrity_verified"] = False
            self.results["no_data_corruption"] = False


class ScenarioExecutor:
    """測試場景執行器主類"""

    def __init__(self):
        self.metrics_collector = E2EMetricsCollector()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self.test_environment = None
        self.scenarios_config = {}
        self.results = []

    def load_configurations(self):
        """載入配置文件"""
        try:
            # 載入測試場景配置
            scenarios_file = Path("tests/e2e/standards/test_scenarios_spec.yaml")
            if scenarios_file.exists():
                with open(scenarios_file, "r", encoding="utf-8") as f:
                    self.scenarios_config = yaml.safe_load(f)
                logger.info("測試場景配置載入成功")
            else:
                logger.error(f"測試場景配置文件不存在: {scenarios_file}")
                return False

            # 載入環境配置
            env_file = Path("tests/e2e/standards/test_environment_spec.yaml")
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    env_config = yaml.safe_load(f)
                self.test_environment = TestEnvironment(env_config)
                logger.info("測試環境配置載入成功")
            else:
                logger.error(f"測試環境配置文件不存在: {env_file}")
                return False

            return True

        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}")
            return False

    async def execute_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """執行單個測試場景"""
        if scenario_name not in self.scenarios_config.get("test_scenarios", {}):
            raise ValueError(f"未知的測試場景: {scenario_name}")

        scenario_config = self.scenarios_config["test_scenarios"][scenario_name]
        scenario = TestScenario(scenario_name, scenario_config, self.metrics_collector)

        # 開始系統監控
        await self.system_monitor.start_monitoring(scenario_name)

        try:
            result = await scenario.execute()
            self.results.append(result)
            return result
        finally:
            # 停止系統監控
            await self.system_monitor.stop_monitoring()

    async def execute_suite(self, suite_name: str) -> List[Dict[str, Any]]:
        """執行測試套件"""
        if suite_name not in self.scenarios_config.get("test_suites", {}):
            raise ValueError(f"未知的測試套件: {suite_name}")

        suite_config = self.scenarios_config["test_suites"][suite_name]
        scenarios = suite_config["scenarios"]

        suite_results = []

        for scenario_name in scenarios:
            logger.info(f"執行套件 {suite_name} 中的場景: {scenario_name}")
            result = await self.execute_scenario(scenario_name)
            suite_results.append(result)

        return suite_results

    async def execute_all_scenarios(self) -> List[Dict[str, Any]]:
        """執行所有測試場景"""
        all_scenarios = list(self.scenarios_config.get("test_scenarios", {}).keys())

        all_results = []

        for scenario_name in all_scenarios:
            logger.info(f"執行場景: {scenario_name}")
            result = await self.execute_scenario(scenario_name)
            all_results.append(result)

        return all_results

    def generate_report(
        self, output_format: str = "json", output_file: Optional[str] = None
    ):
        """生成測試報告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if output_format.lower() == "json":
                report = {
                    "test_run_id": f"e2e_test_{timestamp}",
                    "timestamp": timestamp,
                    "total_scenarios": len(self.results),
                    "passed_scenarios": len(
                        [r for r in self.results if r["status"] == "PASSED"]
                    ),
                    "failed_scenarios": len(
                        [r for r in self.results if r["status"] == "FAILED"]
                    ),
                    "error_scenarios": len(
                        [r for r in self.results if r["status"] == "ERROR"]
                    ),
                    "overall_success_rate": (
                        len([r for r in self.results if r["status"] == "PASSED"])
                        / len(self.results)
                        * 100
                        if self.results
                        else 0
                    ),
                    "scenarios": self.results,
                }

                if output_file:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(report, f, indent=2, ensure_ascii=False)
                    logger.info(f"JSON 報告已生成: {output_file}")
                else:
                    print(json.dumps(report, indent=2, ensure_ascii=False))

            elif output_format.lower() == "html":
                html_content = self._generate_html_report()

                if output_file:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info(f"HTML 報告已生成: {output_file}")
                else:
                    print(html_content)

            else:
                logger.error(f"不支援的報告格式: {output_format}")

        except Exception as e:
            logger.error(f"生成報告失敗: {e}")

    def _generate_html_report(self) -> str:
        """生成 HTML 格式報告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>NTN Stack E2E 測試報告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .summary { margin: 20px 0; }
                .scenario { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .passed { border-left: 5px solid #4CAF50; }
                .failed { border-left: 5px solid #f44336; }
                .error { border-left: 5px solid #ff9800; }
                .metrics { background-color: #f9f9f9; padding: 10px; margin: 10px 0; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>NTN Stack 端到端測試報告</h1>
                <p>生成時間: {timestamp}</p>
            </div>
            
            <div class="summary">
                <h2>測試摘要</h2>
                <table>
                    <tr><th>指標</th><th>值</th></tr>
                    <tr><td>總測試場景數</td><td>{total_scenarios}</td></tr>
                    <tr><td>通過場景數</td><td>{passed_scenarios}</td></tr>
                    <tr><td>失敗場景數</td><td>{failed_scenarios}</td></tr>
                    <tr><td>錯誤場景數</td><td>{error_scenarios}</td></tr>
                    <tr><td>總體成功率</td><td>{success_rate:.1f}%</td></tr>
                </table>
            </div>
            
            <div class="scenarios">
                <h2>場景詳情</h2>
                {scenarios_html}
            </div>
        </body>
        </html>
        """

        # 生成場景詳情 HTML
        scenarios_html = ""
        for result in self.results:
            status_class = result["status"].lower()
            scenarios_html += f"""
            <div class="scenario {status_class}">
                <h3>{result['scenario']} - {result['status']}</h3>
                <p><strong>執行時間:</strong> {result.get('duration_seconds', 0):.2f} 秒</p>
                <p><strong>開始時間:</strong> {result.get('start_time', 'N/A')}</p>
                <p><strong>結束時間:</strong> {result.get('end_time', 'N/A')}</p>
                
                <div class="metrics">
                    <h4>測試結果</h4>
                    <ul>
            """

            for key, value in result.get("results", {}).items():
                scenarios_html += f"<li><strong>{key}:</strong> {value}</li>"

            scenarios_html += "</ul></div>"

            if result.get("errors"):
                scenarios_html += "<div class='metrics'><h4>錯誤信息</h4><ul>"
                for error in result["errors"]:
                    scenarios_html += f"<li>{error}</li>"
                scenarios_html += "</ul></div>"

            scenarios_html += "</div>"

        return html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_scenarios=len(self.results),
            passed_scenarios=len([r for r in self.results if r["status"] == "PASSED"]),
            failed_scenarios=len([r for r in self.results if r["status"] == "FAILED"]),
            error_scenarios=len([r for r in self.results if r["status"] == "ERROR"]),
            success_rate=(
                len([r for r in self.results if r["status"] == "PASSED"])
                / len(self.results)
                * 100
                if self.results
                else 0
            ),
            scenarios_html=scenarios_html,
        )

    async def run(self, args):
        """主要運行邏輯"""
        try:
            # 載入配置
            if not self.load_configurations():
                return 1

            # 設置測試環境
            if self.test_environment:
                if not await self.test_environment.setup():
                    logger.error("測試環境設置失敗")
                    return 1

            # 執行測試
            if args.scenario:
                if args.scenario == "all":
                    await self.execute_all_scenarios()
                else:
                    await self.execute_scenario(args.scenario)
            elif args.suite:
                await self.execute_suite(args.suite)
            else:
                logger.error("必須指定 --scenario 或 --suite 參數")
                return 1

            # 生成報告
            if args.report:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if args.report == "html":
                    output_file = f"tests/e2e/reports/e2e_test_report_{timestamp}.html"
                else:
                    output_file = f"tests/e2e/reports/e2e_test_report_{timestamp}.json"

                self.generate_report(args.report, output_file)

            # 清理測試環境
            if self.test_environment:
                await self.test_environment.teardown()

            # 返回適當的退出碼
            failed_count = len(
                [r for r in self.results if r["status"] in ["FAILED", "ERROR"]]
            )
            return 1 if failed_count > 0 else 0

        except Exception as e:
            logger.error(f"執行測試時發生錯誤: {e}")
            logger.error(traceback.format_exc())
            return 1


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="NTN Stack 端到端測試場景執行器")

    parser.add_argument(
        "--scenario", type=str, help='要執行的測試場景名稱 (或 "all" 執行所有場景)'
    )
    parser.add_argument("--suite", type=str, help="要執行的測試套件名稱")
    parser.add_argument(
        "--report", type=str, choices=["json", "html"], help="生成測試報告的格式"
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

    # 檢查參數
    if not args.scenario and not args.suite:
        parser.error("必須指定 --scenario 或 --suite 參數")

    if args.scenario and args.suite:
        parser.error("不能同時指定 --scenario 和 --suite 參數")

    # 創建必要的目錄
    Path("tests/e2e/logs").mkdir(parents=True, exist_ok=True)
    Path("tests/e2e/reports").mkdir(parents=True, exist_ok=True)

    # 執行測試
    executor = ScenarioExecutor()
    exit_code = asyncio.run(executor.run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
