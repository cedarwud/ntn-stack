#!/usr/bin/env python3
"""
NTN Stack 實驗室驗測主測試套件
根據 TODO.md 14. 實驗室驗測準備與執行要求實現

這是實驗室驗測的主要入口點，統一管理所有測試階段的執行
確保 100% 測試通過率，符合實驗室驗測的嚴格要求
"""

import asyncio
import json
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml
import pytest
from dataclasses import dataclass, asdict

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """測試結果數據結構"""

    test_name: str
    phase: str
    status: str  # passed, failed, error, skipped
    duration_seconds: float
    start_time: str
    end_time: str
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None


@dataclass
class PhaseResult:
    """測試階段結果"""

    phase_name: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    duration_seconds: float
    success_rate: float
    tests: List[TestResult]


class LaboratoryTestEnvironment:
    """實驗室測試環境管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "tests/configs/laboratory_test_config.yaml"
        self.config = self._load_config()
        self.start_time = datetime.utcnow()
        self.test_results: List[TestResult] = []
        self.phase_results: List[PhaseResult] = []

        # 創建報告目錄
        self.reports_dir = Path("tests/reports/laboratory")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # 當前測試會話 ID
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def _load_config(self) -> Dict:
        """載入實驗室測試配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式錯誤: {e}")
            raise

    async def validate_environment(self) -> bool:
        """驗證測試環境是否就緒"""
        logger.info("🔍 驗證實驗室測試環境...")

        validation_tasks = [
            self._check_docker_services(),
            self._check_network_connectivity(),
            self._check_service_health(),
            self._validate_test_data(),
        ]

        results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        all_passed = all(isinstance(result, bool) and result for result in results)

        if not all_passed:
            logger.error("❌ 環境驗證失敗")
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"驗證任務 {i+1} 失敗: {result}")
        else:
            logger.info("✅ 環境驗證通過")

        return all_passed

    async def _check_docker_services(self) -> bool:
        """檢查 Docker 服務狀態"""
        import docker

        try:
            client = docker.from_env()
            required_containers = [
                self.config["laboratory_test_config"]["environment"]["services"][
                    "netstack"
                ]["container_name"],
                self.config["laboratory_test_config"]["environment"]["services"][
                    "simworld"
                ]["container_name"],
            ]

            for container_name in required_containers:
                try:
                    container = client.containers.get(container_name)
                    if container.status != "running":
                        logger.error(
                            f"容器 {container_name} 未運行，狀態: {container.status}"
                        )
                        return False
                    logger.info(f"✅ 容器 {container_name} 運行正常")
                except docker.errors.NotFound:
                    logger.error(f"容器 {container_name} 不存在")
                    return False

            return True

        except Exception as e:
            logger.error(f"Docker 服務檢查失敗: {e}")
            return False

    async def _check_network_connectivity(self) -> bool:
        """檢查網路連接性"""
        import aiohttp

        services = self.config["laboratory_test_config"]["environment"]["services"]

        async with aiohttp.ClientSession() as session:
            for service_name, service_config in services.items():
                if "url" not in service_config:
                    continue

                try:
                    url = service_config["url"]
                    timeout = service_config.get("timeout", 30)

                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        if response.status < 500:  # 允許 4xx，主要排除 5xx
                            logger.info(f"✅ {service_name} 網路連接正常")
                        else:
                            logger.warning(
                                f"⚠️ {service_name} 響應異常: {response.status}"
                            )

                except Exception as e:
                    logger.error(f"❌ {service_name} 網路連接失敗: {e}")
                    return False

        return True

    async def _check_service_health(self) -> bool:
        """檢查服務健康狀態"""
        import aiohttp

        services = self.config["laboratory_test_config"]["environment"]["services"]

        async with aiohttp.ClientSession() as session:
            for service_name, service_config in services.items():
                if "health_endpoint" not in service_config:
                    continue

                try:
                    base_url = service_config["url"]
                    health_endpoint = service_config["health_endpoint"]
                    url = f"{base_url}{health_endpoint}"

                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            logger.info(f"✅ {service_name} 健康檢查通過")
                        else:
                            logger.error(
                                f"❌ {service_name} 健康檢查失敗: {response.status}"
                            )
                            return False

                except Exception as e:
                    logger.error(f"❌ {service_name} 健康檢查異常: {e}")
                    return False

        return True

    async def _validate_test_data(self) -> bool:
        """驗證測試數據和配置"""
        try:
            # 檢查配置完整性
            required_sections = [
                "performance_benchmarks",
                "test_scenarios",
                "success_criteria",
            ]

            lab_config = self.config["laboratory_test_config"]
            for section in required_sections:
                if section not in lab_config:
                    logger.error(f"配置缺少必要部分: {section}")
                    return False

            # 驗證基準值合理性
            benchmarks = lab_config["performance_benchmarks"]
            if benchmarks["latency"]["e2e_target_ms"] <= 0:
                logger.error("延遲基準值不合理")
                return False

            if benchmarks["reliability"]["connection_recovery_target_s"] <= 0:
                logger.error("恢復時間基準值不合理")
                return False

            logger.info("✅ 測試數據驗證通過")
            return True

        except Exception as e:
            logger.error(f"測試數據驗證失敗: {e}")
            return False


class LaboratoryTestExecutor:
    """實驗室測試執行器"""

    def __init__(self, environment: LaboratoryTestEnvironment):
        self.env = environment
        self.config = environment.config["laboratory_test_config"]

    async def execute_full_test_suite(self) -> bool:
        """執行完整的實驗室測試套件"""
        logger.info("🚀 開始執行實驗室驗測完整測試套件")

        # 獲取測試執行計劃
        execution_plan = self.config["test_execution"]["phases"]

        overall_success = True

        for phase_config in execution_plan:
            phase_name = phase_config["name"]
            logger.info(f"📋 開始執行測試階段: {phase_name}")

            phase_success = await self._execute_test_phase(phase_config)

            if not phase_success:
                if phase_config.get("required", False):
                    logger.error(f"❌ 必要測試階段失敗: {phase_name}")
                    overall_success = False
                    break
                else:
                    logger.warning(f"⚠️ 非必要測試階段失敗: {phase_name}")

        # 生成最終報告
        await self._generate_final_report(overall_success)

        if overall_success:
            logger.info("🎉 實驗室驗測全部通過！")
        else:
            logger.error("❌ 實驗室驗測未完全通過")

        return overall_success

    async def _execute_test_phase(self, phase_config: Dict) -> bool:
        """執行單個測試階段"""
        phase_name = phase_config["name"]
        tests = phase_config["tests"]

        phase_start_time = time.time()
        phase_results: List[TestResult] = []

        for test_name in tests:
            logger.info(f"🔧 執行測試: {test_name}")

            test_result = await self._execute_single_test(test_name, phase_name)
            phase_results.append(test_result)
            self.env.test_results.append(test_result)

            if test_result.status == "failed":
                logger.error(f"❌ 測試失敗: {test_name}")
            elif test_result.status == "passed":
                logger.info(f"✅ 測試通過: {test_name}")

        # 計算階段結果
        phase_duration = time.time() - phase_start_time
        passed_count = sum(1 for r in phase_results if r.status == "passed")
        failed_count = sum(1 for r in phase_results if r.status == "failed")
        error_count = sum(1 for r in phase_results if r.status == "error")
        skipped_count = sum(1 for r in phase_results if r.status == "skipped")

        success_rate = passed_count / len(phase_results) if phase_results else 0
        phase_success = success_rate == 1.0  # 要求 100% 通過

        phase_result = PhaseResult(
            phase_name=phase_name,
            status="passed" if phase_success else "failed",
            total_tests=len(phase_results),
            passed_tests=passed_count,
            failed_tests=failed_count,
            error_tests=error_count,
            skipped_tests=skipped_count,
            duration_seconds=phase_duration,
            success_rate=success_rate,
            tests=phase_results,
        )

        self.env.phase_results.append(phase_result)

        logger.info(
            f"📊 階段 {phase_name} 完成: "
            f"{passed_count}/{len(phase_results)} 通過 "
            f"(成功率: {success_rate:.1%})"
        )

        return phase_success

    async def _execute_single_test(self, test_name: str, phase: str) -> TestResult:
        """執行單個測試"""
        start_time = datetime.utcnow()
        test_start = time.time()

        try:
            # 根據測試名稱決定執行策略
            if test_name == "environment_setup":
                success, details = await self._test_environment_setup()
            elif test_name == "service_health_check":
                success, details = await self._test_service_health()
            elif test_name == "basic_connectivity":
                success, details = await self._test_basic_connectivity()
            elif test_name == "api_functionality":
                success, details = await self._test_api_functionality()
            elif test_name == "performance_validation":
                success, details = await self._test_performance_validation()
            elif test_name == "load_testing":
                success, details = await self._test_load_testing()
            elif test_name == "interference_testing":
                success, details = await self._test_interference()
            elif test_name == "failover_testing":
                success, details = await self._test_failover()
            elif test_name == "end_to_end_validation":
                success, details = await self._test_end_to_end()
            elif test_name == "stress_testing":
                success, details = await self._test_stress()
            else:
                logger.warning(f"未知測試類型: {test_name}")
                success, details = False, {"error": f"Unknown test: {test_name}"}

        except Exception as e:
            logger.error(f"測試執行異常: {test_name} - {e}")
            logger.error(traceback.format_exc())
            success = False
            details = {"error": str(e), "traceback": traceback.format_exc()}

        duration = time.time() - test_start
        end_time = datetime.utcnow()

        return TestResult(
            test_name=test_name,
            phase=phase,
            status="passed" if success else "failed",
            duration_seconds=duration,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            error_message=details.get("error") if not success else None,
            details=details,
            metrics=details.get("metrics", {}),
        )

    async def _test_environment_setup(self) -> Tuple[bool, Dict]:
        """環境設置測試"""
        return await self.env.validate_environment(), {"message": "環境驗證完成"}

    async def _test_service_health(self) -> Tuple[bool, Dict]:
        """服務健康檢查測試"""
        return await self.env._check_service_health(), {"message": "服務健康檢查完成"}

    async def _test_basic_connectivity(self) -> Tuple[bool, Dict]:
        """基本連接測試"""
        # 這裡應該調用專門的連接測試模組
        from tests.laboratory_modules.connectivity_tests import ConnectivityTester

        tester = ConnectivityTester(self.config)
        return await tester.run_basic_tests()

    async def _test_api_functionality(self) -> Tuple[bool, Dict]:
        """API 功能測試"""
        from tests.laboratory_modules.api_tests import APITester

        tester = APITester(self.config)
        return await tester.run_functionality_tests()

    async def _test_performance_validation(self) -> Tuple[bool, Dict]:
        """性能驗證測試"""
        from tests.laboratory_modules.performance_tests import PerformanceTester

        tester = PerformanceTester(self.config)
        return await tester.run_performance_tests()

    async def _test_load_testing(self) -> Tuple[bool, Dict]:
        """負載測試"""
        from tests.laboratory_modules.load_tests import LoadTester

        tester = LoadTester(self.config)
        return await tester.run_load_tests()

    async def _test_interference(self) -> Tuple[bool, Dict]:
        """干擾測試"""
        from tests.laboratory_modules.interference_tests import InterferenceTester

        tester = InterferenceTester(self.config)
        return await tester.run_interference_tests()

    async def _test_failover(self) -> Tuple[bool, Dict]:
        """故障切換測試"""
        from tests.laboratory_modules.failover_tests import FailoverTester

        tester = FailoverTester(self.config)
        return await tester.run_failover_tests()

    async def _test_end_to_end(self) -> Tuple[bool, Dict]:
        """端到端測試"""
        from tests.laboratory_modules.e2e_tests import E2ETester

        tester = E2ETester(self.config)
        return await tester.run_e2e_tests()

    async def _test_stress(self) -> Tuple[bool, Dict]:
        """壓力測試"""
        from tests.laboratory_modules.stress_tests import StressTester

        tester = StressTester(self.config)
        return await tester.run_stress_tests()

    async def _generate_final_report(self, overall_success: bool):
        """生成最終測試報告"""
        report_data = {
            "session_id": self.env.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "PASSED" if overall_success else "FAILED",
            "environment": "laboratory",
            "config_version": self.config["metadata"]["version"],
            "total_duration_seconds": (
                datetime.utcnow() - self.env.start_time
            ).total_seconds(),
            "phases": [asdict(phase) for phase in self.env.phase_results],
            "tests": [asdict(test) for test in self.env.test_results],
            "summary": {
                "total_phases": len(self.env.phase_results),
                "passed_phases": sum(
                    1 for p in self.env.phase_results if p.status == "passed"
                ),
                "total_tests": len(self.env.test_results),
                "passed_tests": sum(
                    1 for t in self.env.test_results if t.status == "passed"
                ),
                "overall_success_rate": (
                    sum(1 for t in self.env.test_results if t.status == "passed")
                    / len(self.env.test_results)
                    if self.env.test_results
                    else 0
                ),
            },
        }

        # 生成 JSON 報告
        json_report_path = (
            self.env.reports_dir / f"laboratory_test_report_{self.env.session_id}.json"
        )
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 測試報告已生成: {json_report_path}")


async def main():
    """主程序入口"""
    logger.info("🧪 NTN Stack 實驗室驗測開始")

    try:
        # 初始化測試環境
        test_env = LaboratoryTestEnvironment()

        # 驗證環境
        if not await test_env.validate_environment():
            logger.error("❌ 環境驗證失敗，測試中止")
            sys.exit(1)

        # 執行測試
        executor = LaboratoryTestExecutor(test_env)
        success = await executor.execute_full_test_suite()

        # 根據結果設置退出碼
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("🛑 測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 測試執行發生未預期錯誤: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
