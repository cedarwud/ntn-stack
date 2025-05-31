#!/usr/bin/env python3
"""
端到端系統集成測試框架
根據 TODO.md 第14項要求設計的完整測試框架

實現功能：
1. 測試場景自動化執行
2. 性能指標實時監控
3. 故障檢測和自動恢復
4. 詳細測試報告生成
5. Docker 容器間通信驗證
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml
import aiohttp
import docker
import psutil
import numpy as np
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import subprocess
import sys

sys.path.append("tests/e2e/scenarios")
sys.path.append("tests/performance")

from uav_satellite_connection_test import UAVSatelliteConnectionTest
from interference_avoidance_test import InterferenceAvoidanceTest
from satellite_mesh_failover_test import SatelliteMeshFailoverTest
from performance_optimizer import PerformanceOptimizer

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """測試結果數據結構"""

    test_name: str
    scenario: str
    status: str  # "passed", "failed", "error", "timeout"
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    performance_metrics: Dict[str, float] = None
    error_message: str = ""
    detailed_logs: List[str] = None

    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.detailed_logs is None:
            self.detailed_logs = []


@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""

    timestamp: datetime
    latency_ms: float
    throughput_mbps: float
    cpu_usage_percent: float
    memory_usage_mb: float
    connection_count: int
    error_rate: float

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class DockerMonitor:
    """Docker 容器監控器"""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.warning(f"無法連接到 Docker: {e}")
            self.client = None

    async def get_container_stats(self, container_name: str) -> Dict[str, Any]:
        """獲取容器統計信息"""
        if not self.client:
            return {}

        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)

            # 計算 CPU 使用率
            cpu_usage = 0.0
            if "cpu_stats" in stats and "precpu_stats" in stats:
                cpu_delta = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_delta = (
                    stats["cpu_stats"]["system_cpu_usage"]
                    - stats["precpu_stats"]["system_cpu_usage"]
                )
                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * 100.0

            # 計算記憶體使用量
            memory_usage = 0
            if "memory_stats" in stats:
                memory_usage = stats["memory_stats"].get("usage", 0) / 1024 / 1024  # MB

            return {
                "status": container.status,
                "cpu_usage_percent": cpu_usage,
                "memory_usage_mb": memory_usage,
                "network_stats": stats.get("networks", {}),
                "container_id": container.id[:12],
            }
        except Exception as e:
            logger.error(f"獲取容器 {container_name} 統計信息失敗: {e}")
            return {}

    async def check_container_health(self, container_name: str) -> bool:
        """檢查容器健康狀態"""
        if not self.client:
            return False

        try:
            container = self.client.containers.get(container_name)
            return container.status == "running"
        except Exception as e:
            logger.error(f"檢查容器 {container_name} 健康狀態失敗: {e}")
            return False

    async def get_network_info(self, network_name: str) -> Dict[str, Any]:
        """獲取網路信息"""
        if not self.client:
            return {}

        try:
            network = self.client.networks.get(network_name)
            return {
                "name": network.name,
                "driver": network.attrs.get("Driver", ""),
                "containers": list(network.attrs.get("Containers", {}).keys()),
                "ipam": network.attrs.get("IPAM", {}),
            }
        except Exception as e:
            logger.error(f"獲取網路 {network_name} 信息失敗: {e}")
            return {}


class PerformanceMonitor:
    """性能監控器"""

    def __init__(self, docker_monitor: DockerMonitor):
        self.docker_monitor = docker_monitor
        self.metrics_history = []
        self.monitoring_active = False
        self.monitor_task = None

    async def start_monitoring(self, interval_seconds: float = 1.0):
        """開始性能監控"""
        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        logger.info("性能監控已啟動")

    async def stop_monitoring(self):
        """停止性能監控"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("性能監控已停止")

    async def _monitor_loop(self, interval_seconds: float):
        """監控循環"""
        while self.monitoring_active:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)

                # 保持最近 1000 個數據點
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(interval_seconds)

    async def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指標"""
        timestamp = datetime.utcnow()

        # 系統指標
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        memory_usage_mb = memory.used / 1024 / 1024

        # 測試延遲 (模擬)
        latency_ms = await self._measure_latency()

        # 測試吞吐量 (模擬)
        throughput_mbps = await self._measure_throughput()

        # 連接數 (模擬)
        connection_count = await self._count_connections()

        # 錯誤率 (模擬)
        error_rate = await self._calculate_error_rate()

        return PerformanceMetrics(
            timestamp=timestamp,
            latency_ms=latency_ms,
            throughput_mbps=throughput_mbps,
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage_mb,
            connection_count=connection_count,
            error_rate=error_rate,
        )

    async def _measure_latency(self) -> float:
        """測量延遲"""
        try:
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8080/health", timeout=5
                ) as response:
                    if response.status == 200:
                        return (time.time() - start) * 1000  # 轉換為毫秒
            return 999.0  # 連接失敗
        except Exception:
            return 999.0

    async def _measure_throughput(self) -> float:
        """測量吞吐量 (模擬)"""
        # 這裡應該實現真實的吞吐量測試
        # 現在返回模擬值
        return np.random.normal(25.0, 5.0)

    async def _count_connections(self) -> int:
        """統計連接數 (模擬)"""
        # 這裡應該實現真實的連接統計
        # 現在返回模擬值
        return np.random.randint(1, 10)

    async def _calculate_error_rate(self) -> float:
        """計算錯誤率 (模擬)"""
        # 這裡應該實現真實的錯誤率計算
        # 現在返回模擬值
        return np.random.uniform(0.0, 0.1)

    def get_average_metrics(self, duration_minutes: int = 5) -> Dict[str, float]:
        """獲取指定時間內的平均指標"""
        if not self.metrics_history:
            return {}

        cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {}

        return {
            "avg_latency_ms": np.mean([m.latency_ms for m in recent_metrics]),
            "avg_throughput_mbps": np.mean([m.throughput_mbps for m in recent_metrics]),
            "avg_cpu_usage_percent": np.mean(
                [m.cpu_usage_percent for m in recent_metrics]
            ),
            "avg_memory_usage_mb": np.mean([m.memory_usage_mb for m in recent_metrics]),
            "avg_connection_count": np.mean(
                [m.connection_count for m in recent_metrics]
            ),
            "avg_error_rate": np.mean([m.error_rate for m in recent_metrics]),
        }


class E2ETestFramework:
    """端到端測試框架主類"""

    def __init__(self, config_path: str = "tests/configs/e2e_test_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.docker_monitor = DockerMonitor()
        self.performance_monitor = PerformanceMonitor(self.docker_monitor)
        self.test_results = []
        self.start_time = None
        self.session = None

        # 創建報告目錄
        self.reports_dir = Path("tests/reports/e2e")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # 新增性能優化器
        self.performance_optimizer = PerformanceOptimizer()

        # 測試場景映射
        self.scenario_classes = {
            "normal_uav_satellite_connection": UAVSatelliteConnectionTest,
            "interference_avoidance": InterferenceAvoidanceTest,
            "satellite_loss_mesh_failover": SatelliteMeshFailoverTest,
        }

    def _load_config(self) -> Dict:
        """載入測試配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}")
            raise

    @asynccontextmanager
    async def test_session(self):
        """測試會話上下文管理器"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        try:
            yield self.session
        finally:
            await self.session.close()
            self.session = None

    async def run_all_scenarios(self) -> bool:
        """執行所有測試場景"""
        logger.info("🚀 開始執行端到端系統集成測試")
        self.start_time = datetime.utcnow()

        # 步驟1: 執行性能優化
        logger.info("⚡ 執行系統性能優化")
        optimization_success = (
            await self.performance_optimizer.run_performance_optimization()
        )

        if not optimization_success:
            logger.warning("⚠️ 性能優化未完全成功，但繼續進行測試")

        # 檢查環境準備
        if not await self._verify_environment():
            logger.error("❌ 環境檢查失敗，無法執行測試")
            return False

        # 啟動性能監控
        await self.performance_monitor.start_monitoring()

        try:
            async with self.test_session():
                # 獲取測試場景
                scenarios = self.config["test_scenarios"]

                # 按優先級排序
                sorted_scenarios = sorted(
                    scenarios.items(), key=lambda x: x[1].get("priority", 999)
                )

                all_passed = True

                for scenario_name, scenario_config in sorted_scenarios:
                    logger.info(f"📋 執行測試場景: {scenario_config['name']}")

                    try:
                        # 使用對應的測試場景類
                        if scenario_name in self.scenario_classes:
                            scenario_class = self.scenario_classes[scenario_name]
                            env_config = self.config["environments"]["development"]

                            scenario_instance = scenario_class(
                                env_config["netstack"]["url"],
                                env_config["simworld"]["url"],
                            )

                            scenario_result = await scenario_instance.run_scenario(
                                self.session
                            )

                            # 轉換為 TestResult 格式
                            result = TestResult(
                                test_name=scenario_name,
                                scenario=scenario_config["name"],
                                status=(
                                    "passed"
                                    if scenario_result.get("success", False)
                                    else "failed"
                                ),
                                start_time=datetime.fromisoformat(
                                    scenario_result["start_time"]
                                ),
                                end_time=datetime.fromisoformat(
                                    scenario_result["end_time"]
                                ),
                                duration_seconds=scenario_result["duration_seconds"],
                                performance_metrics=scenario_result.get(
                                    "performance_metrics", {}
                                ),
                                error_message=scenario_result.get("error", ""),
                                detailed_logs=[
                                    step.get("details", "")
                                    for step in scenario_result.get("steps", [])
                                ],
                            )
                        else:
                            # 使用原來的通用方法
                            result = await self._run_scenario(
                                scenario_name, scenario_config
                            )

                        self.test_results.append(result)

                        if result.status != "passed":
                            all_passed = False
                            logger.error(f"❌ 場景失敗: {scenario_name}")
                        else:
                            logger.info(f"✅ 場景通過: {scenario_name}")

                    except Exception as e:
                        logger.error(f"❌ 場景執行異常: {scenario_name} - {e}")
                        error_result = TestResult(
                            test_name=scenario_name,
                            scenario=scenario_config["name"],
                            status="error",
                            start_time=datetime.utcnow(),
                            error_message=str(e),
                        )
                        error_result.end_time = datetime.utcnow()
                        self.test_results.append(error_result)
                        all_passed = False

        finally:
            # 停止性能監控
            await self.performance_monitor.stop_monitoring()

        # 生成報告
        await self._generate_comprehensive_report()

        return all_passed

    async def _verify_environment(self) -> bool:
        """驗證測試環境"""
        logger.info("🔍 驗證測試環境...")

        env_config = self.config["environments"]["development"]

        # 檢查服務健康狀態
        health_checks = []

        # NetStack 健康檢查
        netstack_url = env_config["netstack"]["url"]
        health_checks.append(("NetStack", f"{netstack_url}/health"))

        # SimWorld 健康檢查
        simworld_url = env_config["simworld"]["url"]
        health_checks.append(("SimWorld", f"{simworld_url}/api/v1/wireless/health"))

        async with aiohttp.ClientSession() as session:
            for service_name, health_url in health_checks:
                try:
                    async with session.get(health_url, timeout=10) as response:
                        if response.status == 200:
                            logger.info(f"✅ {service_name} 健康檢查通過")
                        else:
                            logger.error(
                                f"❌ {service_name} 健康檢查失敗: HTTP {response.status}"
                            )
                            return False
                except Exception as e:
                    logger.error(f"❌ {service_name} 健康檢查異常: {e}")
                    return False

        # 檢查 Docker 容器狀態
        containers = env_config["docker"]["containers"]
        for container_name in containers.values():
            if not await self.docker_monitor.check_container_health(container_name):
                logger.error(f"❌ 容器 {container_name} 未運行")
                return False
            logger.info(f"✅ 容器 {container_name} 運行正常")

        # 檢查網路連接
        network_name = env_config["docker"]["network_name"]
        network_info = await self.docker_monitor.get_network_info(network_name)
        if not network_info:
            logger.error(f"❌ 網路 {network_name} 不存在")
            return False
        logger.info(f"✅ 網路 {network_name} 正常")

        logger.info("✅ 環境驗證完成")
        return True

    async def _run_scenario(
        self, scenario_name: str, scenario_config: Dict
    ) -> TestResult:
        """執行單個測試場景"""
        start_time = datetime.utcnow()
        result = TestResult(
            test_name=scenario_name,
            scenario=scenario_config["name"],
            status="running",
            start_time=start_time,
        )

        try:
            # 設置超時
            timeout = scenario_config.get("timeout_seconds", 300)

            # 執行測試步驟
            async with asyncio.timeout(timeout):
                success = await self._execute_test_steps(
                    scenario_config["test_steps"],
                    scenario_config["performance_targets"],
                    result,
                )

            result.status = "passed" if success else "failed"

        except asyncio.TimeoutError:
            result.status = "timeout"
            result.error_message = f"測試超時 ({timeout} 秒)"
            logger.error(f"測試場景 {scenario_name} 超時")

        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            logger.error(f"測試場景 {scenario_name} 執行異常: {e}")

        finally:
            result.end_time = datetime.utcnow()
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

            # 收集性能指標
            result.performance_metrics = self.performance_monitor.get_average_metrics(5)

        return result

    async def _execute_test_steps(
        self, test_steps: List[Dict], performance_targets: Dict, result: TestResult
    ) -> bool:
        """執行測試步驟"""
        env_config = self.config["environments"]["development"]

        for step in test_steps:
            step_name = step["name"]
            result.detailed_logs.append(f"執行步驟: {step_name}")

            try:
                # 確定服務 URL
                if step["endpoint"].startswith("/api/v1/uav") or step[
                    "endpoint"
                ].startswith("/api/v1/satellite"):
                    base_url = env_config["netstack"]["url"]
                else:
                    base_url = env_config["simworld"]["url"]

                url = f"{base_url}{step['endpoint']}"
                method = step["method"].upper()

                # 執行 HTTP 請求
                start_time = time.time()

                async with self.session.request(method, url) as response:
                    duration_ms = (time.time() - start_time) * 1000

                    result.detailed_logs.append(
                        f"  {method} {url} -> {response.status} ({duration_ms:.1f}ms)"
                    )

                    # 檢查回應狀態
                    if response.status not in [200, 201, 202]:
                        result.detailed_logs.append(f"  錯誤: HTTP {response.status}")
                        return False

                    # 檢查性能目標
                    if not await self._check_performance_targets(
                        performance_targets, duration_ms, result
                    ):
                        return False

            except Exception as e:
                result.detailed_logs.append(f"  步驟執行失敗: {e}")
                return False

        return True

    async def _check_performance_targets(
        self, targets: Dict, step_duration_ms: float, result: TestResult
    ) -> bool:
        """檢查性能目標"""
        # 檢查端到端延遲
        if "max_e2e_latency_ms" in targets:
            max_latency = targets["max_e2e_latency_ms"]
            if step_duration_ms > max_latency:
                result.detailed_logs.append(
                    f"  性能失敗: 延遲 {step_duration_ms:.1f}ms > 目標 {max_latency}ms"
                )
                return False

        # 檢查重連時間
        if "max_reconnection_time_ms" in targets:
            max_reconnection = targets["max_reconnection_time_ms"]
            if step_duration_ms > max_reconnection:
                result.detailed_logs.append(
                    f"  性能失敗: 重連時間 {step_duration_ms:.1f}ms > 目標 {max_reconnection}ms"
                )
                return False

        return True

    async def _generate_comprehensive_report(self):
        """生成綜合測試報告"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # 計算統計信息
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == "passed")
        failed_tests = sum(1 for r in self.test_results if r.status == "failed")
        error_tests = sum(1 for r in self.test_results if r.status == "error")
        timeout_tests = sum(1 for r in self.test_results if r.status == "timeout")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        total_duration = (datetime.utcnow() - self.start_time).total_seconds()

        # 創建報告數據
        report_data = {
            "test_execution": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "total_duration_seconds": total_duration,
                "environment": "development",
            },
            "summary": {
                "total_scenarios": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "error": error_tests,
                "timeout": timeout_tests,
                "success_rate": success_rate,
            },
            "detailed_results": [asdict(result) for result in self.test_results],
            "performance_analysis": self.performance_monitor.get_average_metrics(10),
            "performance_history": [
                m.to_dict() for m in self.performance_monitor.metrics_history
            ],
        }

        # 保存 JSON 報告
        json_report_path = self.reports_dir / f"e2e_test_report_{timestamp}.json"
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        # 生成 HTML 報告
        html_report_path = self.reports_dir / f"e2e_test_report_{timestamp}.html"
        await self._generate_html_report(report_data, html_report_path)

        # 輸出摘要
        logger.info("\n" + "=" * 80)
        logger.info("📊 端到端系統集成測試報告")
        logger.info("=" * 80)
        logger.info(f"測試場景總數: {total_tests}")
        logger.info(f"通過: {passed_tests}")
        logger.info(f"失敗: {failed_tests}")
        logger.info(f"錯誤: {error_tests}")
        logger.info(f"超時: {timeout_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"總執行時間: {total_duration:.1f} 秒")
        logger.info(f"詳細報告: {json_report_path}")
        logger.info(f"HTML 報告: {html_report_path}")
        logger.info("=" * 80)

    async def _generate_html_report(self, report_data: Dict, output_path: Path):
        """生成 HTML 報告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NTN Stack E2E 測試報告</title>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .summary { background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .passed { color: #27ae60; font-weight: bold; }
        .failed { color: #e74c3c; font-weight: bold; }
        .error { color: #e67e22; font-weight: bold; }
        .timeout { color: #9b59b6; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metrics { display: flex; flex-wrap: wrap; gap: 20px; }
        .metric-card { background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 NTN Stack 端到端系統集成測試報告</h1>
        <p>生成時間: {generation_time}</p>
        <p>測試環境: {environment}</p>
    </div>
    
    <div class="summary">
        <h2>📊 測試摘要</h2>
        <div class="metrics">
            <div class="metric-card">
                <h3>總測試場景</h3>
                <h2>{total_scenarios}</h2>
            </div>
            <div class="metric-card">
                <h3>通過</h3>
                <h2 class="passed">{passed}</h2>
            </div>
            <div class="metric-card">
                <h3>失敗</h3>
                <h2 class="failed">{failed}</h2>
            </div>
            <div class="metric-card">
                <h3>成功率</h3>
                <h2>{success_rate:.1f}%</h2>
            </div>
            <div class="metric-card">
                <h3>執行時間</h3>
                <h2>{total_duration:.1f}s</h2>
            </div>
        </div>
    </div>
    
    <div class="details">
        <h2>📋 詳細結果</h2>
        <table>
            <thead>
                <tr>
                    <th>測試場景</th>
                    <th>狀態</th>
                    <th>執行時間</th>
                    <th>平均延遲</th>
                    <th>錯誤信息</th>
                </tr>
            </thead>
            <tbody>
                {test_results_rows}
            </tbody>
        </table>
    </div>
    
    <div class="performance">
        <h2>⚡ 性能分析</h2>
        <div class="metrics">
            <div class="metric-card">
                <h3>平均延遲</h3>
                <h2>{avg_latency:.1f} ms</h2>
            </div>
            <div class="metric-card">
                <h3>平均吞吐量</h3>
                <h2>{avg_throughput:.1f} Mbps</h2>
            </div>
            <div class="metric-card">
                <h3>平均 CPU 使用率</h3>
                <h2>{avg_cpu:.1f}%</h2>
            </div>
            <div class="metric-card">
                <h3>平均記憶體使用</h3>
                <h2>{avg_memory:.1f} MB</h2>
            </div>
        </div>
    </div>
</body>
</html>
        """

        # 生成測試結果行
        test_results_rows = ""
        for result in report_data["detailed_results"]:
            status_class = result["status"]
            avg_latency = result.get("performance_metrics", {}).get("avg_latency_ms", 0)
            test_results_rows += f"""
                <tr>
                    <td>{result["scenario"]}</td>
                    <td class="{status_class}">{result["status"].upper()}</td>
                    <td>{result["duration_seconds"]:.2f}s</td>
                    <td>{avg_latency:.1f}ms</td>
                    <td>{result.get("error_message", "")}</td>
                </tr>
            """

        # 格式化 HTML
        perf_analysis = report_data["performance_analysis"]
        html_content = html_template.format(
            generation_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            environment=report_data["test_execution"]["environment"],
            total_scenarios=report_data["summary"]["total_scenarios"],
            passed=report_data["summary"]["passed"],
            failed=report_data["summary"]["failed"],
            success_rate=report_data["summary"]["success_rate"],
            total_duration=report_data["test_execution"]["total_duration_seconds"],
            test_results_rows=test_results_rows,
            avg_latency=perf_analysis.get("avg_latency_ms", 0),
            avg_throughput=perf_analysis.get("avg_throughput_mbps", 0),
            avg_cpu=perf_analysis.get("avg_cpu_usage_percent", 0),
            avg_memory=perf_analysis.get("avg_memory_usage_mb", 0),
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)


async def main():
    """主函數"""
    framework = E2ETestFramework()
    success = await framework.run_all_scenarios()

    if success:
        logger.info("🎉 所有端到端測試通過！")
        return 0
    else:
        logger.error("❌ 部分端到端測試失敗！")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
