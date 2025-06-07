#!/usr/bin/env python3
"""
性能測試自動化執行和報告系統
實現階段七要求的自動化性能測試執行、調度和綜合報告生成

功能：
1. 自動化測試調度和執行
2. 多類型測試編排（E2E、負載、壓力、回歸）
3. 測試環境管理
4. 結果收集和分析
5. 綜合報告生成
6. 測試執行監控
7. 失敗自動重試機制
8. 測試資源管理
"""

import asyncio
import os
import time
import json
import yaml
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog
from pathlib import Path
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import aiofiles
import schedule

logger = structlog.get_logger(__name__)


class TestType(Enum):
    """測試類型"""
    E2E = "e2e"
    LOAD = "load"
    STRESS = "stress"
    REGRESSION = "regression"
    INTEGRATION = "integration"
    SMOKE = "smoke"


class TestStatus(Enum):
    """測試狀態"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    """執行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"


@dataclass
class TestConfiguration:
    """測試配置"""
    test_id: str
    test_type: TestType
    name: str
    description: str
    script_path: str
    timeout_seconds: int = 3600
    retry_count: int = 3
    retry_delay: int = 60
    environment_requirements: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 1  # 1-10, 10最高
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestExecutionResult:
    """測試執行結果"""
    test_id: str
    test_type: TestType
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    artifacts: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    retry_count: int = 0
    resource_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """測試套件"""
    suite_id: str
    name: str
    description: str
    tests: List[TestConfiguration] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_parallel_tests: int = 4
    suite_timeout_seconds: int = 7200
    environment_setup: Optional[str] = None
    environment_teardown: Optional[str] = None
    enabled: bool = True


@dataclass
class TestExecution:
    """測試執行實例"""
    execution_id: str
    suite_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TestStatus = TestStatus.PENDING
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    test_results: List[TestExecutionResult] = field(default_factory=list)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    execution_log: List[str] = field(default_factory=list)


class EnvironmentManager:
    """環境管理器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.environments: Dict[str, Dict[str, Any]] = {}
        self.active_environments: Dict[str, str] = {}  # execution_id -> env_id
        
    async def setup_environment(self, execution_id: str, requirements: Dict[str, Any]) -> str:
        """設置測試環境"""
        env_id = f"env_{execution_id}_{int(time.time())}"
        env_dir = self.base_dir / "environments" / env_id
        env_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 複製基礎環境
            if "base_environment" in requirements:
                base_env = requirements["base_environment"]
                if base_env in self.environments:
                    await self._copy_environment(self.environments[base_env]["path"], str(env_dir))
            
            # 安裝依賴
            if "dependencies" in requirements:
                await self._install_dependencies(str(env_dir), requirements["dependencies"])
            
            # 設置環境變量
            if "env_vars" in requirements:
                await self._setup_env_vars(str(env_dir), requirements["env_vars"])
            
            # 配置服務
            if "services" in requirements:
                await self._configure_services(str(env_dir), requirements["services"])
            
            self.environments[env_id] = {
                "path": str(env_dir),
                "requirements": requirements,
                "created_at": datetime.now(),
                "execution_id": execution_id
            }
            
            self.active_environments[execution_id] = env_id
            
            logger.info(f"測試環境已設置: {env_id}", execution_id=execution_id)
            return env_id
            
        except Exception as e:
            logger.error(f"環境設置失敗: {e}", execution_id=execution_id)
            await self.cleanup_environment(execution_id)
            raise
    
    async def _copy_environment(self, source: str, dest: str):
        """複製環境"""
        if os.path.exists(source):
            shutil.copytree(source, dest, dirs_exist_ok=True)
    
    async def _install_dependencies(self, env_dir: str, dependencies: List[str]):
        """安裝依賴"""
        if not dependencies:
            return
            
        # 創建虛擬環境
        venv_path = os.path.join(env_dir, "venv")
        subprocess.run([
            "python", "-m", "venv", venv_path
        ], check=True)
        
        # 安裝依賴
        pip_path = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")
        for dep in dependencies:
            subprocess.run([
                pip_path, "install", dep
            ], check=True)
    
    async def _setup_env_vars(self, env_dir: str, env_vars: Dict[str, str]):
        """設置環境變量"""
        env_file = os.path.join(env_dir, ".env")
        async with aiofiles.open(env_file, "w") as f:
            for key, value in env_vars.items():
                await f.write(f"{key}={value}\n")
    
    async def _configure_services(self, env_dir: str, services: Dict[str, Any]):
        """配置服務"""
        config_dir = os.path.join(env_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        for service_name, config in services.items():
            config_file = os.path.join(config_dir, f"{service_name}.yaml")
            async with aiofiles.open(config_file, "w") as f:
                await f.write(yaml.dump(config))
    
    async def cleanup_environment(self, execution_id: str):
        """清理環境"""
        if execution_id in self.active_environments:
            env_id = self.active_environments[execution_id]
            if env_id in self.environments:
                env_path = self.environments[env_id]["path"]
                try:
                    shutil.rmtree(env_path)
                    logger.info(f"環境已清理: {env_id}")
                except Exception as e:
                    logger.error(f"環境清理失敗: {e}")
                
                del self.environments[env_id]
            del self.active_environments[execution_id]


class ResourceMonitor:
    """資源監控器"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.resource_data: Dict[str, List[Dict]] = {}
        
    async def start_monitoring(self, execution_id: str):
        """開始監控資源"""
        if execution_id in self.resource_data:
            return
            
        self.resource_data[execution_id] = []
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"開始監控資源", execution_id=execution_id)
    
    async def stop_monitoring(self, execution_id: str):
        """停止監控資源"""
        if execution_id in self.resource_data:
            logger.info(f"停止監控資源", execution_id=execution_id, 
                       data_points=len(self.resource_data[execution_id]))
    
    async def _monitor_loop(self):
        """監控循環"""
        while self.monitoring_active:
            try:
                timestamp = time.time()
                
                # 收集系統資源數據
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                resource_snapshot = {
                    "timestamp": timestamp,
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "disk_percent": disk.percent,
                    "network_bytes_sent": network.bytes_sent,
                    "network_bytes_recv": network.bytes_recv
                }
                
                # 添加到所有活躍的執行實例
                for execution_id in list(self.resource_data.keys()):
                    self.resource_data[execution_id].append(resource_snapshot.copy())
                    
                    # 保持最近1000個數據點
                    if len(self.resource_data[execution_id]) > 1000:
                        self.resource_data[execution_id] = self.resource_data[execution_id][-1000:]
                
                await asyncio.sleep(5)  # 每5秒監控一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"資源監控錯誤: {e}")
                await asyncio.sleep(5)
    
    def get_resource_summary(self, execution_id: str) -> Dict[str, Any]:
        """獲取資源使用摘要"""
        if execution_id not in self.resource_data or not self.resource_data[execution_id]:
            return {}
        
        data = self.resource_data[execution_id]
        
        cpu_values = [d["cpu_percent"] for d in data]
        memory_values = [d["memory_percent"] for d in data]
        
        return {
            "duration_seconds": data[-1]["timestamp"] - data[0]["timestamp"] if len(data) > 1 else 0,
            "cpu_avg": sum(cpu_values) / len(cpu_values),
            "cpu_max": max(cpu_values),
            "memory_avg": sum(memory_values) / len(memory_values),
            "memory_max": max(memory_values),
            "data_points": len(data)
        }


class TestExecutor:
    """測試執行器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.environment_manager = EnvironmentManager(str(self.base_dir))
        self.resource_monitor = ResourceMonitor()
        self.active_executions: Dict[str, TestExecution] = {}
        self.execution_history: List[TestExecution] = []
        
    async def execute_test(self, test_config: TestConfiguration, execution_id: str) -> TestExecutionResult:
        """執行單個測試"""
        result = TestExecutionResult(
            test_id=test_config.test_id,
            test_type=test_config.test_type,
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            # 檢查依賴
            if not await self._check_dependencies(test_config.dependencies):
                result.status = TestStatus.SKIPPED
                result.error_message = "依賴檢查失敗"
                return result
            
            # 設置環境
            if test_config.environment_requirements:
                env_id = await self.environment_manager.setup_environment(
                    execution_id, test_config.environment_requirements
                )
            
            # 開始資源監控
            await self.resource_monitor.start_monitoring(execution_id)
            
            # 執行測試（支持重試）
            for attempt in range(test_config.retry_count + 1):
                try:
                    result.retry_count = attempt
                    
                    # 執行測試腳本
                    exit_code, stdout, stderr = await self._run_test_script(
                        test_config, execution_id
                    )
                    
                    result.exit_code = exit_code
                    result.stdout = stdout
                    result.stderr = stderr
                    
                    if exit_code == 0:
                        result.status = TestStatus.PASSED
                        break
                    else:
                        if attempt < test_config.retry_count:
                            logger.warning(f"測試失敗，準備重試 {attempt + 1}/{test_config.retry_count}",
                                         test_id=test_config.test_id)
                            await asyncio.sleep(test_config.retry_delay)
                        else:
                            result.status = TestStatus.FAILED
                            result.error_message = f"測試失敗，退出碼: {exit_code}"
                
                except asyncio.TimeoutError:
                    result.status = TestStatus.TIMEOUT
                    result.error_message = f"測試超時: {test_config.timeout_seconds}秒"
                    break
                except Exception as e:
                    if attempt < test_config.retry_count:
                        logger.warning(f"測試異常，準備重試: {e}", test_id=test_config.test_id)
                        await asyncio.sleep(test_config.retry_delay)
                    else:
                        result.status = TestStatus.FAILED
                        result.error_message = f"測試異常: {str(e)}"
                        break
            
            # 收集測試產物
            result.artifacts = await self._collect_artifacts(test_config, execution_id)
            
            # 解析測試指標
            result.metrics = await self._parse_test_metrics(test_config, result.stdout, result.stderr)
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.error_message = f"執行測試時發生錯誤: {str(e)}"
            logger.error(f"測試執行異常: {e}", test_id=test_config.test_id)
        
        finally:
            result.end_time = datetime.now()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            # 停止資源監控並收集摘要
            await self.resource_monitor.stop_monitoring(execution_id)
            result.resource_usage = self.resource_monitor.get_resource_summary(execution_id)
            
            # 清理環境
            await self.environment_manager.cleanup_environment(execution_id)
        
        return result
    
    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """檢查依賴"""
        for dep in dependencies:
            # 檢查服務是否運行
            if dep.startswith("service:"):
                service_name = dep.replace("service:", "")
                if not await self._check_service_running(service_name):
                    return False
            
            # 檢查端口是否可用
            elif dep.startswith("port:"):
                port = int(dep.replace("port:", ""))
                if not await self._check_port_available(port):
                    return False
            
            # 檢查文件是否存在
            elif dep.startswith("file:"):
                file_path = dep.replace("file:", "")
                if not os.path.exists(file_path):
                    return False
        
        return True
    
    async def _check_service_running(self, service_name: str) -> bool:
        """檢查服務是否運行"""
        try:
            result = subprocess.run([
                "systemctl", "is-active", service_name
            ], capture_output=True, text=True)
            return result.returncode == 0 and "active" in result.stdout
        except:
            return True  # 如果無法檢查，假設可用
    
    async def _check_port_available(self, port: int) -> bool:
        """檢查端口是否可用"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0  # 0表示連接成功，端口可用
        except:
            return False
    
    async def _run_test_script(self, test_config: TestConfiguration, execution_id: str) -> Tuple[int, str, str]:
        """運行測試腳本"""
        script_path = test_config.script_path
        if not os.path.isabs(script_path):
            script_path = str(self.base_dir / script_path)
        
        # 準備環境變量
        env = os.environ.copy()
        env.update({
            "TEST_ID": test_config.test_id,
            "EXECUTION_ID": execution_id,
            "TEST_TYPE": test_config.test_type.value
        })
        
        # 添加參數到環境變量
        for key, value in test_config.parameters.items():
            env[f"TEST_PARAM_{key.upper()}"] = str(value)
        
        # 執行腳本
        process = await asyncio.create_subprocess_exec(
            "python", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(self.base_dir)
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=test_config.timeout_seconds
            )
            
            return process.returncode, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise
    
    async def _collect_artifacts(self, test_config: TestConfiguration, execution_id: str) -> List[str]:
        """收集測試產物"""
        artifacts = []
        
        # 查找常見的測試產物
        artifact_patterns = [
            f"*{test_config.test_id}*.log",
            f"*{test_config.test_id}*.json",
            f"*{test_config.test_id}*.xml",
            f"*{test_config.test_id}*.html",
            f"*{execution_id}*.log",
            "test-results.xml",
            "coverage.xml",
            "performance-report.json"
        ]
        
        # 搜索產物
        for pattern in artifact_patterns:
            for file_path in self.base_dir.rglob(pattern):
                if file_path.is_file():
                    artifacts.append(str(file_path))
        
        return artifacts
    
    async def _parse_test_metrics(self, test_config: TestConfiguration, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析測試指標"""
        metrics = {}
        
        # 根據測試類型解析不同的指標
        if test_config.test_type == TestType.LOAD:
            # 解析負載測試指標
            metrics.update(self._parse_load_test_metrics(stdout))
        elif test_config.test_type == TestType.STRESS:
            # 解析壓力測試指標
            metrics.update(self._parse_stress_test_metrics(stdout))
        elif test_config.test_type == TestType.E2E:
            # 解析E2E測試指標
            metrics.update(self._parse_e2e_test_metrics(stdout))
        
        # 通用指標解析
        metrics.update(self._parse_common_metrics(stdout, stderr))
        
        return metrics
    
    def _parse_load_test_metrics(self, output: str) -> Dict[str, Any]:
        """解析負載測試指標"""
        metrics = {}
        
        # 簡單的正則表達式解析
        import re
        
        # 響應時間
        response_time_match = re.search(r"avg_response_time[:\s]+(\d+\.?\d*)", output)
        if response_time_match:
            metrics["avg_response_time_ms"] = float(response_time_match.group(1))
        
        # 成功率
        success_rate_match = re.search(r"success_rate[:\s]+(\d+\.?\d*)", output)
        if success_rate_match:
            metrics["success_rate"] = float(success_rate_match.group(1))
        
        # 每秒請求數
        rps_match = re.search(r"requests_per_second[:\s]+(\d+\.?\d*)", output)
        if rps_match:
            metrics["requests_per_second"] = float(rps_match.group(1))
        
        return metrics
    
    def _parse_stress_test_metrics(self, output: str) -> Dict[str, Any]:
        """解析壓力測試指標"""
        metrics = {}
        
        import re
        
        # 峰值負載
        peak_load_match = re.search(r"peak_load[:\s]+(\d+)", output)
        if peak_load_match:
            metrics["peak_load"] = int(peak_load_match.group(1))
        
        # 系統穩定性
        stability_match = re.search(r"system_stable[:\s]+(true|false)", output, re.IGNORECASE)
        if stability_match:
            metrics["system_stable"] = stability_match.group(1).lower() == "true"
        
        return metrics
    
    def _parse_e2e_test_metrics(self, output: str) -> Dict[str, Any]:
        """解析E2E測試指標"""
        metrics = {}
        
        import re
        
        # 測試通過數
        passed_match = re.search(r"(\d+)\s+passed", output)
        if passed_match:
            metrics["tests_passed"] = int(passed_match.group(1))
        
        # 測試失敗數
        failed_match = re.search(r"(\d+)\s+failed", output)
        if failed_match:
            metrics["tests_failed"] = int(failed_match.group(1))
        
        return metrics
    
    def _parse_common_metrics(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析通用指標"""
        metrics = {}
        
        # 輸出長度（作為活動指標）
        metrics["stdout_length"] = len(stdout)
        metrics["stderr_length"] = len(stderr)
        
        # 檢查是否有常見的錯誤關鍵字
        error_keywords = ["error", "exception", "failed", "timeout"]
        metrics["error_indicators"] = sum(
            1 for keyword in error_keywords 
            if keyword.lower() in stdout.lower() or keyword.lower() in stderr.lower()
        )
        
        return metrics


class TestSuiteExecutor:
    """測試套件執行器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.test_executor = TestExecutor(str(self.base_dir))
        self.active_executions: Dict[str, TestExecution] = {}
        
    async def execute_suite(self, suite: TestSuite) -> TestExecution:
        """執行測試套件"""
        execution_id = f"exec_{suite.suite_id}_{int(time.time())}"
        
        execution = TestExecution(
            execution_id=execution_id,
            suite_id=suite.suite_id,
            start_time=datetime.now(),
            total_tests=len([t for t in suite.tests if t.enabled]),
            environment_info=await self._collect_environment_info()
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            execution.execution_log.append(f"開始執行測試套件: {suite.name}")
            
            # 環境設置
            if suite.environment_setup:
                await self._run_setup_script(suite.environment_setup, execution_id)
                execution.execution_log.append("環境設置完成")
            
            # 過濾啟用的測試
            enabled_tests = [test for test in suite.tests if test.enabled]
            
            # 根據執行模式執行測試
            if suite.execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(enabled_tests, execution)
            elif suite.execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(enabled_tests, execution, suite.max_parallel_tests)
            elif suite.execution_mode == ExecutionMode.PIPELINE:
                await self._execute_pipeline(enabled_tests, execution)
            
            # 統計結果
            execution.passed_tests = sum(1 for r in execution.test_results if r.status == TestStatus.PASSED)
            execution.failed_tests = sum(1 for r in execution.test_results if r.status == TestStatus.FAILED)
            execution.skipped_tests = sum(1 for r in execution.test_results if r.status == TestStatus.SKIPPED)
            
            # 確定整體狀態
            if execution.failed_tests == 0:
                execution.status = TestStatus.PASSED
            else:
                execution.status = TestStatus.FAILED
            
            execution.execution_log.append(
                f"測試套件執行完成: {execution.passed_tests}通過, {execution.failed_tests}失敗, {execution.skipped_tests}跳過"
            )
            
        except Exception as e:
            execution.status = TestStatus.FAILED
            execution.execution_log.append(f"測試套件執行異常: {str(e)}")
            logger.error(f"測試套件執行異常: {e}", suite_id=suite.suite_id)
        
        finally:
            execution.end_time = datetime.now()
            
            # 環境清理
            if suite.environment_teardown:
                await self._run_teardown_script(suite.environment_teardown, execution_id)
                execution.execution_log.append("環境清理完成")
            
            del self.active_executions[execution_id]
        
        return execution
    
    async def _execute_sequential(self, tests: List[TestConfiguration], execution: TestExecution):
        """順序執行測試"""
        for test in tests:
            execution.execution_log.append(f"開始執行測試: {test.name}")
            
            result = await self.test_executor.execute_test(test, execution.execution_id)
            execution.test_results.append(result)
            
            execution.execution_log.append(
                f"測試完成: {test.name} - {result.status.value} ({result.duration_seconds:.1f}s)"
            )
            
            # 如果是關鍵測試失敗，可以選擇停止
            if result.status == TestStatus.FAILED and "critical" in test.tags:
                execution.execution_log.append("關鍵測試失敗，停止執行")
                break
    
    async def _execute_parallel(self, tests: List[TestConfiguration], execution: TestExecution, max_parallel: int):
        """並行執行測試"""
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def execute_with_semaphore(test):
            async with semaphore:
                execution.execution_log.append(f"開始執行測試: {test.name}")
                result = await self.test_executor.execute_test(test, execution.execution_id)
                execution.test_results.append(result)
                execution.execution_log.append(
                    f"測試完成: {test.name} - {result.status.value} ({result.duration_seconds:.1f}s)"
                )
                return result
        
        # 創建所有任務
        tasks = [execute_with_semaphore(test) for test in tests]
        
        # 等待所有任務完成
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_pipeline(self, tests: List[TestConfiguration], execution: TestExecution):
        """流水線執行測試"""
        # 按依賴關係排序測試
        sorted_tests = self._sort_tests_by_dependencies(tests)
        
        # 順序執行但允許並行無依賴的測試
        completed_tests = set()
        
        while len(completed_tests) < len(sorted_tests):
            # 找到可以執行的測試（依賴已完成）
            ready_tests = []
            for test in sorted_tests:
                if test.test_id not in completed_tests:
                    if all(dep in completed_tests for dep in test.dependencies):
                        ready_tests.append(test)
            
            if not ready_tests:
                break  # 防止死鎖
            
            # 並行執行準備好的測試
            tasks = []
            for test in ready_tests:
                execution.execution_log.append(f"開始執行測試: {test.name}")
                task = asyncio.create_task(
                    self.test_executor.execute_test(test, execution.execution_id)
                )
                tasks.append((test, task))
            
            # 等待完成
            for test, task in tasks:
                result = await task
                execution.test_results.append(result)
                completed_tests.add(test.test_id)
                execution.execution_log.append(
                    f"測試完成: {test.name} - {result.status.value} ({result.duration_seconds:.1f}s)"
                )
    
    def _sort_tests_by_dependencies(self, tests: List[TestConfiguration]) -> List[TestConfiguration]:
        """按依賴關係排序測試"""
        # 簡單的拓撲排序
        result = []
        remaining = tests.copy()
        test_map = {t.test_id: t for t in tests}
        
        while remaining:
            # 找到沒有未滿足依賴的測試
            ready = []
            for test in remaining:
                deps_satisfied = all(
                    dep not in test_map or any(r.test_id == dep for r in result)
                    for dep in test.dependencies
                )
                if deps_satisfied:
                    ready.append(test)
            
            if not ready:
                # 如果沒有準備好的測試，可能有循環依賴，直接添加剩餘的
                result.extend(remaining)
                break
            
            # 添加準備好的測試並從剩餘列表中移除
            result.extend(ready)
            for test in ready:
                remaining.remove(test)
        
        return result
    
    async def _collect_environment_info(self) -> Dict[str, Any]:
        """收集環境信息"""
        import platform
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_setup_script(self, script_path: str, execution_id: str):
        """運行設置腳本"""
        if not os.path.isabs(script_path):
            script_path = str(self.base_dir / script_path)
        
        if os.path.exists(script_path):
            process = await asyncio.create_subprocess_exec(
                "python", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "EXECUTION_ID": execution_id}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"設置腳本失敗: {stderr.decode()}")
    
    async def _run_teardown_script(self, script_path: str, execution_id: str):
        """運行清理腳本"""
        if not os.path.isabs(script_path):
            script_path = str(self.base_dir / script_path)
        
        if os.path.exists(script_path):
            process = await asyncio.create_subprocess_exec(
                "python", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "EXECUTION_ID": execution_id}
            )
            
            await process.communicate()
            # 清理腳本失敗不會阻止執行完成


class AutomationScheduler:
    """自動化調度器"""
    
    def __init__(self, suite_executor: TestSuiteExecutor):
        self.suite_executor = suite_executor
        self.scheduled_jobs: List[Dict[str, Any]] = []
        self.scheduler_active = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
    def schedule_suite(self, suite: TestSuite, cron_expression: str, enabled: bool = True):
        """調度測試套件"""
        job = {
            "suite": suite,
            "cron": cron_expression,
            "enabled": enabled,
            "last_run": None,
            "next_run": self._calculate_next_run(cron_expression)
        }
        
        self.scheduled_jobs.append(job)
        logger.info(f"已調度測試套件: {suite.name}", cron=cron_expression)
    
    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """計算下次運行時間（簡化實現）"""
        # 這裡可以使用專業的cron庫如croniter
        # 暫時使用簡單的實現
        if cron_expression == "daily":
            return datetime.now() + timedelta(days=1)
        elif cron_expression == "hourly":
            return datetime.now() + timedelta(hours=1)
        elif cron_expression.startswith("every"):
            # 例如 "every 30 minutes"
            parts = cron_expression.split()
            if len(parts) >= 3:
                interval = int(parts[1])
                unit = parts[2]
                if unit.startswith("minute"):
                    return datetime.now() + timedelta(minutes=interval)
                elif unit.startswith("hour"):
                    return datetime.now() + timedelta(hours=interval)
        
        # 默認1小時後
        return datetime.now() + timedelta(hours=1)
    
    async def start_scheduler(self):
        """啟動調度器"""
        if self.scheduler_active:
            return
            
        self.scheduler_active = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("測試調度器已啟動")
    
    async def stop_scheduler(self):
        """停止調度器"""
        self.scheduler_active = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("測試調度器已停止")
    
    async def _scheduler_loop(self):
        """調度器主循環"""
        while self.scheduler_active:
            try:
                current_time = datetime.now()
                
                for job in self.scheduled_jobs:
                    if (job["enabled"] and 
                        job["next_run"] and 
                        current_time >= job["next_run"]):
                        
                        # 執行測試套件
                        logger.info(f"調度執行測試套件: {job['suite'].name}")
                        
                        try:
                            execution = await self.suite_executor.execute_suite(job["suite"])
                            logger.info(f"調度測試完成: {job['suite'].name}, 狀態: {execution.status.value}")
                        except Exception as e:
                            logger.error(f"調度測試失敗: {e}", suite=job['suite'].name)
                        
                        # 更新調度信息
                        job["last_run"] = current_time
                        job["next_run"] = self._calculate_next_run(job["cron"])
                
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"調度器異常: {e}")
                await asyncio.sleep(60)


class PerformanceTestAutomation:
    """性能測試自動化主類"""
    
    def __init__(self, base_dir: str = "/home/sat/ntn-stack/tests"):
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "automation" / "config"
        self.results_dir = self.base_dir / "automation" / "results"
        
        # 確保目錄存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化組件
        self.suite_executor = TestSuiteExecutor(str(self.base_dir))
        self.scheduler = AutomationScheduler(self.suite_executor)
        
        # 測試套件
        self.test_suites: Dict[str, TestSuite] = {}
        self.execution_history: List[TestExecution] = []
        
        # 初始化預設配置
        self._initialize_default_suites()
    
    def _initialize_default_suites(self):
        """初始化預設測試套件"""
        
        # E2E測試套件
        e2e_suite = TestSuite(
            suite_id="e2e_performance",
            name="E2E性能測試套件",
            description="端到端性能和功能測試",
            execution_mode=ExecutionMode.SEQUENTIAL,
            tests=[
                TestConfiguration(
                    test_id="e2e_basic_functionality",
                    test_type=TestType.E2E,
                    name="基礎功能測試",
                    description="驗證基本系統功能",
                    script_path="e2e/test_e2e_quick.py",
                    timeout_seconds=1800,
                    priority=10,
                    tags=["critical", "basic"]
                ),
                TestConfiguration(
                    test_id="e2e_performance_scenarios",
                    test_type=TestType.E2E,
                    name="性能場景測試",
                    description="複雜性能場景測試",
                    script_path="e2e/e2e_tests.py",
                    timeout_seconds=3600,
                    priority=8,
                    tags=["performance", "scenarios"]
                )
            ]
        )
        
        # 負載測試套件
        load_suite = TestSuite(
            suite_id="load_performance",
            name="負載性能測試套件",
            description="系統負載能力測試",
            execution_mode=ExecutionMode.PARALLEL,
            max_parallel_tests=2,
            tests=[
                TestConfiguration(
                    test_id="load_concurrent_users",
                    test_type=TestType.LOAD,
                    name="並發用戶負載測試",
                    description="測試並發用戶負載",
                    script_path="performance/load_tests.py",
                    timeout_seconds=2400,
                    priority=8,
                    parameters={"concurrent_users": 50, "duration_seconds": 300},
                    tags=["load", "concurrent"]
                ),
                TestConfiguration(
                    test_id="load_ramp_up",
                    test_type=TestType.LOAD,
                    name="階梯負載測試",
                    description="漸進式負載增長測試",
                    script_path="performance/load_tests.py",
                    timeout_seconds=3600,
                    priority=7,
                    parameters={"test_type": "ramp_up", "max_users": 100},
                    tags=["load", "ramp"]
                )
            ]
        )
        
        # 壓力測試套件
        stress_suite = TestSuite(
            suite_id="stress_performance",
            name="壓力性能測試套件",
            description="系統極限和恢復能力測試",
            execution_mode=ExecutionMode.SEQUENTIAL,
            tests=[
                TestConfiguration(
                    test_id="stress_extreme_load",
                    test_type=TestType.STRESS,
                    name="極限負載壓力測試",
                    description="測試系統極限負載能力",
                    script_path="performance/stress_tests.py",
                    timeout_seconds=3600,
                    priority=6,
                    parameters={"test_type": "extreme_load"},
                    tags=["stress", "extreme"]
                ),
                TestConfiguration(
                    test_id="stress_resource_exhaustion",
                    test_type=TestType.STRESS,
                    name="資源耗盡測試",
                    description="測試資源耗盡情況下的系統表現",
                    script_path="performance/stress_tests.py",
                    timeout_seconds=2400,
                    priority=5,
                    parameters={"test_type": "resource_exhaustion"},
                    tags=["stress", "resources"]
                )
            ]
        )
        
        # 回歸測試套件
        regression_suite = TestSuite(
            suite_id="regression_performance",
            name="性能回歸測試套件",
            description="性能回歸檢測測試",
            execution_mode=ExecutionMode.SEQUENTIAL,
            tests=[
                TestConfiguration(
                    test_id="regression_baseline",
                    test_type=TestType.REGRESSION,
                    name="性能基準回歸測試",
                    description="建立和比較性能基準",
                    script_path="performance/performance_regression_tester.py",
                    timeout_seconds=3600,
                    priority=7,
                    parameters={"mode": "regression_test"},
                    tags=["regression", "baseline"]
                )
            ]
        )
        
        # 添加到套件字典
        self.test_suites = {
            "e2e_performance": e2e_suite,
            "load_performance": load_suite,
            "stress_performance": stress_suite,
            "regression_performance": regression_suite
        }
    
    async def run_suite(self, suite_id: str) -> Optional[TestExecution]:
        """運行指定的測試套件"""
        if suite_id not in self.test_suites:
            logger.error(f"測試套件不存在: {suite_id}")
            return None
        
        suite = self.test_suites[suite_id]
        
        logger.info(f"開始執行測試套件: {suite.name}")
        execution = await self.suite_executor.execute_suite(suite)
        
        # 保存結果
        await self._save_execution_result(execution)
        self.execution_history.append(execution)
        
        logger.info(f"測試套件執行完成: {suite.name}, 狀態: {execution.status.value}")
        
        return execution
    
    async def run_all_suites(self) -> List[TestExecution]:
        """運行所有測試套件"""
        results = []
        
        # 按優先級排序套件
        sorted_suites = sorted(
            self.test_suites.items(),
            key=lambda x: max((t.priority for t in x[1].tests), default=1),
            reverse=True
        )
        
        for suite_id, suite in sorted_suites:
            if suite.enabled:
                execution = await self.run_suite(suite_id)
                if execution:
                    results.append(execution)
        
        return results
    
    async def schedule_automatic_runs(self):
        """設置自動化運行調度"""
        
        # 每日 E2E 測試
        self.scheduler.schedule_suite(
            self.test_suites["e2e_performance"],
            "daily",
            True
        )
        
        # 每6小時負載測試
        self.scheduler.schedule_suite(
            self.test_suites["load_performance"],
            "every 6 hours",
            True
        )
        
        # 每週壓力測試
        self.scheduler.schedule_suite(
            self.test_suites["stress_performance"],
            "weekly",
            True
        )
        
        # 每日性能回歸測試
        self.scheduler.schedule_suite(
            self.test_suites["regression_performance"],
            "daily",
            True
        )
        
        # 啟動調度器
        await self.scheduler.start_scheduler()
        
        logger.info("自動化測試調度已啟動")
    
    async def _save_execution_result(self, execution: TestExecution):
        """保存執行結果"""
        timestamp = execution.start_time.strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"execution_{execution.suite_id}_{timestamp}.json"
        
        # 轉換為可序列化的字典
        result_data = {
            "execution_id": execution.execution_id,
            "suite_id": execution.suite_id,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "status": execution.status.value,
            "total_tests": execution.total_tests,
            "passed_tests": execution.passed_tests,
            "failed_tests": execution.failed_tests,
            "skipped_tests": execution.skipped_tests,
            "environment_info": execution.environment_info,
            "execution_log": execution.execution_log,
            "test_results": [
                {
                    "test_id": r.test_id,
                    "test_type": r.test_type.value,
                    "status": r.status.value,
                    "start_time": r.start_time.isoformat(),
                    "end_time": r.end_time.isoformat() if r.end_time else None,
                    "duration_seconds": r.duration_seconds,
                    "exit_code": r.exit_code,
                    "stdout_length": len(r.stdout),
                    "stderr_length": len(r.stderr),
                    "artifacts": r.artifacts,
                    "metrics": r.metrics,
                    "error_message": r.error_message,
                    "retry_count": r.retry_count,
                    "resource_usage": r.resource_usage
                }
                for r in execution.test_results
            ]
        }
        
        async with aiofiles.open(result_file, "w") as f:
            await f.write(json.dumps(result_data, indent=2, ensure_ascii=False))
        
        logger.info(f"執行結果已保存: {result_file}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """獲取執行摘要"""
        total_executions = len(self.execution_history)
        
        if total_executions == 0:
            return {
                "total_executions": 0,
                "summary": "尚無執行記錄"
            }
        
        passed_executions = sum(1 for e in self.execution_history if e.status == TestStatus.PASSED)
        failed_executions = sum(1 for e in self.execution_history if e.status == TestStatus.FAILED)
        
        # 最近執行
        recent_executions = sorted(self.execution_history, key=lambda x: x.start_time, reverse=True)[:10]
        
        # 按套件統計
        suite_stats = {}
        for execution in self.execution_history:
            suite_id = execution.suite_id
            if suite_id not in suite_stats:
                suite_stats[suite_id] = {"total": 0, "passed": 0, "failed": 0}
            
            suite_stats[suite_id]["total"] += 1
            if execution.status == TestStatus.PASSED:
                suite_stats[suite_id]["passed"] += 1
            elif execution.status == TestStatus.FAILED:
                suite_stats[suite_id]["failed"] += 1
        
        return {
            "total_executions": total_executions,
            "passed_executions": passed_executions,
            "failed_executions": failed_executions,
            "success_rate": passed_executions / total_executions if total_executions > 0 else 0,
            "suite_statistics": suite_stats,
            "recent_executions": [
                {
                    "execution_id": e.execution_id,
                    "suite_id": e.suite_id,
                    "status": e.status.value,
                    "start_time": e.start_time.isoformat(),
                    "duration": (e.end_time - e.start_time).total_seconds() if e.end_time else 0,
                    "passed_tests": e.passed_tests,
                    "failed_tests": e.failed_tests
                }
                for e in recent_executions
            ],
            "test_suites": list(self.test_suites.keys()),
            "scheduler_active": self.scheduler.scheduler_active
        }


async def main():
    """主函數 - 示例用法"""
    automation = PerformanceTestAutomation()
    
    print("🚀 性能測試自動化執行和報告系統")
    print("=" * 60)
    
    # 執行單個套件示例
    print("📋 執行E2E性能測試套件...")
    e2e_execution = await automation.run_suite("e2e_performance")
    
    if e2e_execution:
        print(f"✅ E2E測試完成: {e2e_execution.status.value}")
        print(f"   通過: {e2e_execution.passed_tests}")
        print(f"   失敗: {e2e_execution.failed_tests}")
        print(f"   持續時間: {(e2e_execution.end_time - e2e_execution.start_time).total_seconds():.1f}秒")
    
    # 獲取摘要
    summary = automation.get_execution_summary()
    print(f"\n📊 執行摘要:")
    print(f"   總執行次數: {summary['total_executions']}")
    print(f"   成功率: {summary['success_rate']:.1%}")
    print(f"   可用測試套件: {', '.join(summary['test_suites'])}")
    
    # 設置自動化調度（示例）
    print(f"\n⏰ 設置自動化調度...")
    await automation.schedule_automatic_runs()
    
    print("✅ 性能測試自動化系統已準備就緒")
    
    # 運行一小段時間以演示調度
    await asyncio.sleep(5)
    
    await automation.scheduler.stop_scheduler()
    print("🔚 系統已停止")


if __name__ == "__main__":
    asyncio.run(main())