#!/usr/bin/env python3
"""
NTN Stack 統一測試執行器
提供跨專案的測試執行、報告生成和結果分析功能
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import aiohttp
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEnvironment:
    """測試環境管理"""

    def __init__(self, env_name: str = "development"):
        self.env_name = env_name
        self.config = self._load_config()
        self.netstack_url = self.config["environments"][env_name]["netstack"]["url"]
        self.simworld_url = self.config["environments"][env_name]["simworld"]["url"]

    def _load_config(self) -> Dict:
        """載入測試配置"""
        config_path = (
            Path(__file__).parent.parent / "configs" / "test_environments.yaml"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    async def check_services_health(self) -> Dict[str, bool]:
        """檢查服務健康狀態"""
        results = {}

        async with aiohttp.ClientSession() as session:
            # 檢查 NetStack
            try:
                async with session.get(
                    f"{self.netstack_url}/health", timeout=10
                ) as response:
                    results["netstack"] = response.status == 200
            except Exception as e:
                logger.warning(f"NetStack 健康檢查失敗: {e}")
                results["netstack"] = False

            # 檢查 SimWorld
            try:
                async with session.get(
                    f"{self.simworld_url}/api/v1/wireless/health", timeout=10
                ) as response:
                    results["simworld"] = response.status == 200
            except Exception as e:
                logger.warning(f"SimWorld 健康檢查失敗: {e}")
                results["simworld"] = False

        return results


class TestRunner:
    """統一測試執行器"""

    def __init__(self, environment: str = "development"):
        self.environment = TestEnvironment(environment)
        self.start_time = datetime.utcnow()
        self.results = []
        self.reports_dir = Path(__file__).parent.parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    async def run_test_suite(self, suite_name: str, test_paths: List[str]) -> Dict:
        """執行測試套件"""
        logger.info(f"🚀 開始執行測試套件: {suite_name}")

        suite_start = time.time()
        suite_results = {
            "suite_name": suite_name,
            "start_time": datetime.utcnow().isoformat(),
            "environment": self.environment.env_name,
            "tests": [],
            "summary": {},
        }

        # 檢查服務狀態
        health_status = await self.environment.check_services_health()
        suite_results["service_health"] = health_status

        if not all(health_status.values()):
            logger.error(f"❌ 服務健康檢查失敗: {health_status}")
            suite_results["status"] = "failed"
            suite_results["error"] = "Service health check failed"
            return suite_results

        # 執行測試
        for test_path in test_paths:
            test_result = await self._run_single_test(test_path)
            suite_results["tests"].append(test_result)

        # 計算摘要
        suite_duration = time.time() - suite_start
        passed_count = sum(
            1 for test in suite_results["tests"] if test["status"] == "passed"
        )
        total_count = len(suite_results["tests"])

        suite_results.update(
            {
                "duration_seconds": suite_duration,
                "end_time": datetime.utcnow().isoformat(),
                "summary": {
                    "total": total_count,
                    "passed": passed_count,
                    "failed": total_count - passed_count,
                    "success_rate": (
                        passed_count / total_count if total_count > 0 else 0
                    ),
                },
            }
        )

        suite_results["status"] = "passed" if passed_count == total_count else "failed"

        logger.info(
            f"✅ 測試套件完成: {suite_name} ({passed_count}/{total_count} 通過)"
        )
        return suite_results

    async def _run_single_test(self, test_path: str) -> Dict:
        """執行單個測試"""
        test_start = time.time()
        test_name = Path(test_path).stem

        logger.info(f"📋 執行測試: {test_name}")

        try:
            # 根據文件類型決定執行方式
            if test_path.endswith(".py"):
                result = await self._run_python_test(test_path)
            elif test_path.endswith(".sh"):
                result = await self._run_shell_test(test_path)
            else:
                raise ValueError(f"不支援的測試文件類型: {test_path}")

            test_duration = time.time() - test_start

            return {
                "test_name": test_name,
                "test_path": test_path,
                "status": "passed" if result["success"] else "failed",
                "duration_seconds": test_duration,
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "details": result.get("details", {}),
            }

        except Exception as e:
            test_duration = time.time() - test_start
            logger.error(f"❌ 測試執行異常: {test_name} - {e}")

            return {
                "test_name": test_name,
                "test_path": test_path,
                "status": "error",
                "duration_seconds": test_duration,
                "output": "",
                "error": str(e),
                "details": {},
            }

    async def _run_python_test(self, test_path: str) -> Dict:
        """執行 Python 測試"""
        try:
            # 使用 subprocess 執行 Python 測試
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                test_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent.parent.parent,
            )

            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8"),
                "error": stderr.decode("utf-8") if stderr else "",
                "return_code": process.returncode,
            }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"執行異常: {str(e)}",
                "return_code": -1,
            }

    async def _run_shell_test(self, test_path: str) -> Dict:
        """執行 Shell 測試"""
        try:
            process = await asyncio.create_subprocess_exec(
                "bash",
                test_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(test_path).parent,
            )

            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8"),
                "error": stderr.decode("utf-8") if stderr else "",
                "return_code": process.returncode,
            }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"執行異常: {str(e)}",
                "return_code": -1,
            }

    def generate_report(self, results: List[Dict]) -> str:
        """生成測試報告"""
        report_file = (
            self.reports_dir
            / f"test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )

        total_duration = (datetime.utcnow() - self.start_time).total_seconds()

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment.env_name,
            "total_duration_seconds": total_duration,
            "test_suites": results,
            "overall_summary": self._calculate_overall_summary(results),
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 測試報告已生成: {report_file}")
        return str(report_file)

    def _calculate_overall_summary(self, results: List[Dict]) -> Dict:
        """計算總體摘要"""
        total_tests = sum(result["summary"]["total"] for result in results)
        total_passed = sum(result["summary"]["passed"] for result in results)
        total_failed = sum(result["summary"]["failed"] for result in results)

        return {
            "total_suites": len(results),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_success_rate": (
                total_passed / total_tests if total_tests > 0 else 0
            ),
            "suites_summary": [
                {
                    "suite": result["suite_name"],
                    "status": result["status"],
                    "success_rate": result["summary"]["success_rate"],
                }
                for result in results
            ],
        }

    def print_summary(self, results: List[Dict]):
        """印出測試摘要"""
        print("\n" + "=" * 80)
        print("📊 NTN Stack 測試結果摘要")
        print("=" * 80)

        for result in results:
            status_icon = "✅" if result["status"] == "passed" else "❌"
            success_rate = result["summary"]["success_rate"] * 100
            duration = result["duration_seconds"]

            print(
                f"{status_icon} {result['suite_name']:.<40} "
                f"{result['summary']['passed']}/{result['summary']['total']} "
                f"({success_rate:.1f}%) - {duration:.1f}s"
            )

        overall = self._calculate_overall_summary(results)
        print("-" * 80)
        print(
            f"總計: {overall['total_passed']}/{overall['total_tests']} "
            f"({overall['overall_success_rate']*100:.1f}%) 測試通過"
        )

        if overall["overall_success_rate"] >= 0.9:
            print("🎉 優秀！所有測試幾乎都通過了！")
        elif overall["overall_success_rate"] >= 0.7:
            print("✅ 良好！大部分測試通過")
        else:
            print("⚠️ 需要注意！多個測試失敗")


# 預定義測試套件
TEST_SUITES = {
    "quick": {
        "name": "快速測試",
        "paths": ["tests/integration/sionna_integration/test_sionna_core.py"],
    },
    "integration": {
        "name": "整合測試",
        "paths": [
            "tests/integration/sionna_integration/test_sionna_integration.py",
            "tests/integration/sionna_integration/test_sionna_core.py",
        ],
    },
    "netstack": {
        "name": "NetStack 測試",
        "paths": [
            "netstack/tests/e2e_netstack.sh",
            "netstack/tests/test_connectivity.sh",
        ],
    },
    "all": {
        "name": "完整測試",
        "paths": [
            "tests/integration/sionna_integration/test_sionna_core.py",
            "tests/integration/sionna_integration/test_sionna_integration.py",
            "netstack/tests/quick_ntn_validation.sh",
        ],
    },
}


async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="NTN Stack 統一測試執行器")
    parser.add_argument(
        "suite", choices=list(TEST_SUITES.keys()) + ["custom"], help="要執行的測試套件"
    )
    parser.add_argument(
        "--environment",
        "-e",
        default="development",
        choices=["development", "ci", "staging"],
        help="測試環境",
    )
    parser.add_argument("--paths", nargs="+", help="自訂測試路徑 (使用 custom 套件時)")

    args = parser.parse_args()

    runner = TestRunner(args.environment)

    if args.suite == "custom":
        if not args.paths:
            print("❌ 使用 custom 套件時必須提供 --paths 參數")
            sys.exit(1)
        test_paths = args.paths
        suite_name = "自訂測試"
    else:
        suite_config = TEST_SUITES[args.suite]
        test_paths = suite_config["paths"]
        suite_name = suite_config["name"]

    try:
        # 執行測試套件
        result = await runner.run_test_suite(suite_name, test_paths)

        # 生成報告
        report_file = runner.generate_report([result])

        # 印出摘要
        runner.print_summary([result])

        # 返回適當的退出代碼
        success_rate = result["summary"]["success_rate"]
        exit_code = 0 if success_rate >= 0.7 else 1

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 測試執行異常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
