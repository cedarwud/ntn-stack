#!/usr/bin/env python3
"""
NTN Stack 統一測試執行器
支援不同測試套件的執行和管理
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("test_runner.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class TestResult:
    """測試結果類別"""

    def __init__(self, name: str, status: str, duration: float, details: str = ""):
        self.name = name
        self.status = status  # passed, failed, error, skipped
        self.duration = duration
        self.details = details
        self.timestamp = datetime.now()


class TestEnvironment:
    """測試環境管理"""

    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.simworld_frontend_url = "http://localhost:3000"
        self.simworld_backend_url = "http://localhost:8000"

    async def check_services(self) -> Dict[str, bool]:
        """檢查服務狀態"""
        import aiohttp

        services = {
            "netstack": f"{self.base_url}/health",
            "simworld_frontend": self.simworld_frontend_url,
            "simworld_backend": f"{self.simworld_backend_url}/health",
        }

        results = {}
        async with aiohttp.ClientSession() as session:
            for service, url in services.items():
                try:
                    async with session.get(url, timeout=5) as response:
                        results[service] = response.status == 200
                except Exception as e:
                    logger.warning(f"Service {service} check failed: {e}")
                    results[service] = False

        return results

    def setup_environment(self):
        """設置測試環境"""
        logger.info("設置測試環境...")

        # 創建必要的目錄
        os.makedirs("reports", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        # 安裝依賴
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "pytest",
                    "pytest-asyncio",
                    "pytest-cov",
                    "httpx",
                    "requests",
                    "aiohttp",
                ],
                check=True,
                capture_output=True,
            )
            logger.info("測試依賴安裝完成")
        except subprocess.CalledProcessError as e:
            logger.error(f"依賴安裝失敗: {e}")
            return False

        return True


class TestRunner:
    """測試執行器"""

    def __init__(self):
        self.environment = TestEnvironment()
        self.results: List[TestResult] = []
        self.test_suites = self._define_test_suites()

    def _define_test_suites(self) -> Dict[str, Dict]:
        """定義測試套件"""
        return {
            "smoke": {
                "name": "煙霧測試",
                "timeout": 30,
                "tests": ["check_services", "basic_api_health"],
            },
            "quick": {
                "name": "快速測試",
                "timeout": 120,
                "tests": ["check_services", "unit_tests_critical", "basic_integration"],
            },
            "core": {
                "name": "核心測試",
                "timeout": 300,
                "tests": [
                    "check_services",
                    "unit_tests_all",
                    "integration_api",
                    "basic_e2e",
                ],
            },
            "regression": {
                "name": "回歸測試",
                "timeout": 600,
                "tests": [
                    "check_services",
                    "unit_tests_all",
                    "integration_all",
                    "e2e_critical",
                ],
            },
            "full": {
                "name": "完整測試",
                "timeout": 1200,
                "tests": [
                    "check_services",
                    "unit_tests_all",
                    "integration_all",
                    "e2e_all",
                    "performance_basic",
                ],
            },
        }

    async def run_test_suite(
        self, suite_name: str, timeout: Optional[int] = None
    ) -> Dict:
        """執行測試套件"""
        if suite_name not in self.test_suites:
            raise ValueError(f"未知的測試套件: {suite_name}")

        suite = self.test_suites[suite_name]
        suite_timeout = timeout or suite["timeout"]

        logger.info(f"開始執行測試套件: {suite['name']}")
        start_time = time.time()

        try:
            # 設置環境
            if not self.environment.setup_environment():
                raise Exception("環境設置失敗")

            # 執行測試
            for test_name in suite["tests"]:
                test_result = await self._run_single_test(test_name)
                self.results.append(test_result)

                if test_result.status == "failed":
                    logger.error(f"測試失敗: {test_name}")

            # 生成報告
            suite_results = self._generate_suite_report(suite_name)

            duration = time.time() - start_time
            logger.info(f"測試套件 {suite['name']} 執行完成，耗時 {duration:.2f} 秒")

            return {
                "suite": suite_name,
                "status": "completed",
                "duration": duration,
                "summary": {
                    "total": len(self.results),
                    "passed": sum(
                        1 for test in self.results if test.status == "passed"
                    ),
                    "failed": sum(
                        1 for test in self.results if test.status == "failed"
                    ),
                    "errors": sum(1 for test in self.results if test.status == "error"),
                    "skipped": sum(
                        1 for test in self.results if test.status == "skipped"
                    ),
                },
                "tests": [
                    {
                        "name": test.name,
                        "status": test.status,
                        "duration": test.duration,
                        "details": test.details,
                    }
                    for test in self.results
                ],
            }

        except Exception as e:
            logger.error(f"測試套件執行失敗: {e}")
            return {
                "suite": suite_name,
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time,
            }

    async def _run_single_test(self, test_name: str) -> TestResult:
        """執行單一測試"""
        logger.info(f"執行測試: {test_name}")
        test_start = time.time()

        try:
            if test_name == "check_services":
                return await self._test_check_services()
            elif test_name == "basic_api_health":
                return await self._test_basic_api_health()
            elif test_name == "unit_tests_critical":
                return await self._test_unit_critical()
            elif test_name == "unit_tests_all":
                return await self._test_unit_all()
            elif test_name == "integration_api":
                return await self._test_integration_api()
            elif test_name == "integration_all":
                return await self._test_integration_all()
            elif test_name == "basic_integration":
                return await self._test_basic_integration()
            elif test_name == "basic_e2e":
                return await self._test_basic_e2e()
            elif test_name == "e2e_critical":
                return await self._test_e2e_critical()
            elif test_name == "e2e_all":
                return await self._test_e2e_all()
            elif test_name == "performance_basic":
                return await self._test_performance_basic()
            else:
                return TestResult(
                    test_name,
                    "error",
                    time.time() - test_start,
                    f"未知的測試: {test_name}",
                )

        except Exception as e:
            test_duration = time.time() - test_start
            logger.error(f"測試 {test_name} 執行失敗: {e}")
            return TestResult(test_name, "error", test_duration, str(e))

    async def _test_check_services(self) -> TestResult:
        """檢查服務狀態測試"""
        start_time = time.time()

        try:
            services_status = await self.environment.check_services()
            failed_services = [
                name for name, status in services_status.items() if not status
            ]

            if failed_services:
                return TestResult(
                    "check_services",
                    "failed",
                    time.time() - start_time,
                    f"服務未啟動: {', '.join(failed_services)}",
                )
            else:
                return TestResult(
                    "check_services",
                    "passed",
                    time.time() - start_time,
                    "所有服務正常運行",
                )

        except Exception as e:
            return TestResult(
                "check_services", "error", time.time() - start_time, str(e)
            )

    async def _test_basic_api_health(self) -> TestResult:
        """基本 API 健康檢查測試"""
        start_time = time.time()

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.environment.base_url}/health"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return TestResult(
                            "basic_api_health",
                            "passed",
                            time.time() - start_time,
                            f"API 健康檢查通過: {data}",
                        )
                    else:
                        return TestResult(
                            "basic_api_health",
                            "failed",
                            time.time() - start_time,
                            f"API 健康檢查失敗，狀態碼: {response.status}",
                        )

        except Exception as e:
            return TestResult(
                "basic_api_health", "error", time.time() - start_time, str(e)
            )

    async def _test_unit_critical(self) -> TestResult:
        """關鍵單元測試"""
        return await self._run_pytest_tests("unit/netstack", "unit_tests_critical")

    async def _test_unit_all(self) -> TestResult:
        """所有單元測試"""
        return await self._run_pytest_tests("unit/", "unit_tests_all")

    async def _test_integration_api(self) -> TestResult:
        """API 整合測試"""
        return await self._run_pytest_tests("integration/api", "integration_api")

    async def _test_integration_all(self) -> TestResult:
        """所有整合測試"""
        return await self._run_pytest_tests("integration/", "integration_all")

    async def _test_basic_integration(self) -> TestResult:
        """基本整合測試"""
        return await self._run_pytest_tests("integration/services", "basic_integration")

    async def _test_basic_e2e(self) -> TestResult:
        """基本端到端測試"""
        return await self._run_python_script(
            "e2e/scenarios/simple_functionality_test.py", "basic_e2e"
        )

    async def _test_e2e_critical(self) -> TestResult:
        """關鍵端到端測試"""
        return await self._run_python_script(
            "e2e/scenarios/final_network_verification.py", "e2e_critical"
        )

    async def _test_e2e_all(self) -> TestResult:
        """所有端到端測試"""
        return await self._run_python_script(
            "e2e/scenarios/final_comprehensive_test.py", "e2e_all"
        )

    async def _test_performance_basic(self) -> TestResult:
        """基本性能測試"""
        return await self._run_shell_script(
            "shell/netstack/ntn_latency_test.sh", "performance_basic"
        )

    async def _run_pytest_tests(self, test_path: str, test_name: str) -> TestResult:
        """執行 pytest 測試"""
        start_time = time.time()

        try:
            if not Path(test_path).exists():
                return TestResult(
                    test_name,
                    "skipped",
                    time.time() - start_time,
                    f"測試路徑不存在: {test_path}",
                )

            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return TestResult(test_name, "passed", duration, "pytest 測試通過")
            else:
                return TestResult(
                    test_name,
                    "failed",
                    duration,
                    f"pytest 測試失敗:\n{result.stdout}\n{result.stderr}",
                )

        except subprocess.TimeoutExpired:
            return TestResult(test_name, "error", time.time() - start_time, "測試超時")
        except Exception as e:
            return TestResult(test_name, "error", time.time() - start_time, str(e))

    async def _run_python_script(self, script_path: str, test_name: str) -> TestResult:
        """執行 Python 腳本測試"""
        start_time = time.time()

        try:
            if not Path(script_path).exists():
                return TestResult(
                    test_name,
                    "skipped",
                    time.time() - start_time,
                    f"腳本不存在: {script_path}",
                )

            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300,
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return TestResult(test_name, "passed", duration, "Python 腳本執行成功")
            else:
                return TestResult(
                    test_name,
                    "failed",
                    duration,
                    f"Python 腳本執行失敗:\n{result.stdout}\n{result.stderr}",
                )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_name, "error", time.time() - start_time, "腳本執行超時"
            )
        except Exception as e:
            return TestResult(test_name, "error", time.time() - start_time, str(e))

    async def _run_shell_script(self, script_path: str, test_name: str) -> TestResult:
        """執行 Shell 腳本測試"""
        start_time = time.time()

        try:
            if not Path(script_path).exists():
                return TestResult(
                    test_name,
                    "skipped",
                    time.time() - start_time,
                    f"腳本不存在: {script_path}",
                )

            result = subprocess.run(
                ["bash", script_path], capture_output=True, text=True, timeout=300
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return TestResult(test_name, "passed", duration, "Shell 腳本執行成功")
            else:
                return TestResult(
                    test_name,
                    "failed",
                    duration,
                    f"Shell 腳本執行失敗:\n{result.stdout}\n{result.stderr}",
                )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_name, "error", time.time() - start_time, "腳本執行超時"
            )
        except Exception as e:
            return TestResult(test_name, "error", time.time() - start_time, str(e))

    def _generate_suite_report(self, suite_name: str) -> Dict:
        """生成測試套件報告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "passed")
        failed_tests = sum(1 for r in self.results if r.status == "failed")
        error_tests = sum(1 for r in self.results if r.status == "error")
        skipped_tests = sum(1 for r in self.results if r.status == "skipped")

        report = {
            "suite": suite_name,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "skipped": skipped_tests,
                "success_rate": (
                    (passed_tests / total_tests * 100) if total_tests > 0 else 0
                ),
            },
            "tests": [
                {
                    "name": test.name,
                    "status": test.status,
                    "duration": test.duration,
                    "details": test.details,
                    "timestamp": test.timestamp.isoformat(),
                }
                for test in self.results
            ],
        }

        # 保存報告
        report_file = f"reports/test_report_{suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"測試報告已保存: {report_file}")
        return report


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="NTN Stack 統一測試執行器")
    parser.add_argument(
        "--suite",
        choices=["smoke", "quick", "core", "regression", "full"],
        default="smoke",
        help="要執行的測試套件",
    )
    parser.add_argument("--timeout", type=int, help="測試超時時間（秒）")
    parser.add_argument(
        "--list-suites", action="store_true", help="列出所有可用的測試套件"
    )

    args = parser.parse_args()

    runner = TestRunner()

    if args.list_suites:
        print("可用的測試套件:")
        for suite_name, suite_info in runner.test_suites.items():
            print(
                f"  {suite_name}: {suite_info['name']} (預設超時: {suite_info['timeout']}s)"
            )
        return

    try:
        result = await runner.run_test_suite(args.suite, args.timeout)

        # 輸出結果摘要
        if result["status"] == "completed":
            summary = result["summary"]
            print(f"\n測試套件 '{args.suite}' 執行完成:")
            print(f"  總計: {summary['total']}")
            print(f"  通過: {summary['passed']}")
            print(f"  失敗: {summary['failed']}")
            print(f"  錯誤: {summary['errors']}")
            print(f"  跳過: {summary['skipped']}")
            print(f"  成功率: {summary['passed']/summary['total']*100:.1f}%")
            print(f"  執行時間: {result['duration']:.2f} 秒")

            # 如果有失敗的測試，返回非零退出碼
            if summary["failed"] > 0 or summary["errors"] > 0:
                sys.exit(1)
        else:
            print(f"測試套件執行失敗: {result.get('error', '未知錯誤')}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"測試執行器錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
