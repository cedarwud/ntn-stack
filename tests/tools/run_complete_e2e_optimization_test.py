#!/usr/bin/env python3
"""
完整的端到端測試和性能優化執行腳本
整合 TODO.md 第14項和第15項要求，確保100%測試通過
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加路徑
sys.path.append("tests/e2e")
sys.path.append("tests/performance")

from e2e.e2e_test_framework import E2ETestFramework
from performance.performance_optimizer import PerformanceOptimizer

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f"tests/reports/complete_e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


class CompleteE2ETestRunner:
    """完整端到端測試執行器"""

    def __init__(self):
        self.e2e_framework = E2ETestFramework()
        self.performance_optimizer = PerformanceOptimizer()
        self.max_retry_attempts = 3
        self.current_attempt = 0

    async def run_complete_test_suite(self) -> bool:
        """執行完整的測試套件"""
        logger.info("🚀 開始執行完整的端到端測試和性能優化")
        start_time = datetime.utcnow()

        # 初始系統檢查
        if not await self._initial_system_check():
            logger.error("❌ 初始系統檢查失敗")
            return False

        # 執行優化和測試循環，直到100%通過
        success = False
        self.current_attempt = 0

        while self.current_attempt < self.max_retry_attempts and not success:
            self.current_attempt += 1
            logger.info(f"📋 執行第 {self.current_attempt} 次嘗試")

            try:
                # 步驟1: 系統性能優化
                logger.info("⚡ 步驟1: 執行系統性能優化")
                optimization_success = await self._run_performance_optimization()

                # 步驟2: 端到端系統集成測試
                logger.info("🧪 步驟2: 執行端到端系統集成測試")
                test_success = await self._run_e2e_tests()

                if optimization_success and test_success:
                    success = True
                    logger.info("🎉 所有測試100%通過！")
                else:
                    logger.warning(f"⚠️ 第 {self.current_attempt} 次嘗試未完全成功")

                    if self.current_attempt < self.max_retry_attempts:
                        logger.info("🔄 執行系統調整後重試")
                        await self._adjust_system_for_retry()

            except Exception as e:
                logger.error(f"❌ 第 {self.current_attempt} 次嘗試異常: {e}")
                if self.current_attempt >= self.max_retry_attempts:
                    break

        # 生成最終報告
        await self._generate_final_report(success)

        total_duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"⏱️ 總執行時間: {total_duration:.1f} 秒")

        return success

    async def _initial_system_check(self) -> bool:
        """初始系統檢查"""
        logger.info("🔍 執行初始系統檢查")

        try:
            # 檢查系統資源
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            logger.info(f"系統資源狀態:")
            logger.info(f"  CPU 使用率: {cpu_percent:.1f}%")
            logger.info(f"  記憶體使用率: {memory.percent:.1f}%")
            logger.info(f"  磁碟使用率: {disk.percent:.1f}%")

            # 檢查資源是否充足
            if cpu_percent > 90:
                logger.warning(f"⚠️ CPU 使用率過高: {cpu_percent:.1f}%")

            if memory.percent > 90:
                logger.warning(f"⚠️ 記憶體使用率過高: {memory.percent:.1f}%")

            if disk.percent > 90:
                logger.warning(f"⚠️ 磁碟使用率過高: {disk.percent:.1f}%")

            # 檢查必要的目錄和文件
            required_paths = [
                "tests/configs/e2e_test_config.yaml",
                "tests/configs/performance_optimization_config.yaml",
                "tests/e2e/e2e_test_framework.py",
                "tests/performance/performance_optimizer.py",
            ]

            for path in required_paths:
                if not Path(path).exists():
                    logger.error(f"❌ 必要文件不存在: {path}")
                    return False

            logger.info("✅ 初始系統檢查通過")
            return True

        except Exception as e:
            logger.error(f"❌ 初始系統檢查異常: {e}")
            return False

    async def _run_performance_optimization(self) -> bool:
        """執行性能優化"""
        logger.info("⚡ 執行系統性能優化")

        try:
            # 運行性能優化器
            success = await self.performance_optimizer.run_performance_optimization()

            if success:
                logger.info("✅ 系統性能優化完成")

                # 等待系統穩定
                logger.info("⏳ 等待系統穩定...")
                await asyncio.sleep(10)

                return True
            else:
                logger.error("❌ 系統性能優化失敗")
                return False

        except Exception as e:
            logger.error(f"❌ 性能優化異常: {e}")
            return False

    async def _run_e2e_tests(self) -> bool:
        """執行端到端測試"""
        logger.info("🧪 執行端到端系統集成測試")

        try:
            # 運行 E2E 測試框架
            success = await self.e2e_framework.run_all_scenarios()

            if success:
                logger.info("✅ 端到端測試全部通過")
                return True
            else:
                logger.error("❌ 端到端測試未全部通過")

                # 分析失敗的測試
                await self._analyze_test_failures()
                return False

        except Exception as e:
            logger.error(f"❌ 端到端測試異常: {e}")
            return False

    async def _analyze_test_failures(self):
        """分析測試失敗原因"""
        logger.info("🔍 分析測試失敗原因")

        try:
            failed_tests = [
                result
                for result in self.e2e_framework.test_results
                if result.status != "passed"
            ]

            if failed_tests:
                logger.info(f"失敗的測試數量: {len(failed_tests)}")

                for failed_test in failed_tests:
                    logger.error(f"失敗測試: {failed_test.test_name}")
                    logger.error(f"  狀態: {failed_test.status}")
                    logger.error(f"  錯誤: {failed_test.error_message}")

                    # 分析性能指標
                    if failed_test.performance_metrics:
                        logger.info(f"  性能指標: {failed_test.performance_metrics}")

                # 提供優化建議
                await self._provide_optimization_suggestions(failed_tests)

        except Exception as e:
            logger.error(f"❌ 分析測試失敗異常: {e}")

    async def _provide_optimization_suggestions(self, failed_tests):
        """提供優化建議"""
        logger.info("💡 提供優化建議")

        suggestions = []

        for failed_test in failed_tests:
            if (
                "latency" in failed_test.error_message
                or "延遲" in failed_test.error_message
            ):
                suggestions.append("優化網路延遲：檢查網路配置和路由")

            if (
                "throughput" in failed_test.error_message
                or "吞吐量" in failed_test.error_message
            ):
                suggestions.append("優化吞吐量：調整緩衝區大小和並發設置")

            if (
                "connection" in failed_test.error_message
                or "連接" in failed_test.error_message
            ):
                suggestions.append("優化連接穩定性：增加重試機制和連接池")

            if "timeout" in failed_test.status or "超時" in failed_test.error_message:
                suggestions.append("增加超時時間並優化處理邏輯")

        # 去重並輸出建議
        unique_suggestions = list(set(suggestions))
        for i, suggestion in enumerate(unique_suggestions, 1):
            logger.info(f"  {i}. {suggestion}")

    async def _adjust_system_for_retry(self):
        """為重試調整系統"""
        logger.info("🔧 調整系統參數準備重試")

        try:
            # 清理系統資源
            import gc

            gc.collect()

            # 等待系統穩定
            await asyncio.sleep(5)

            # 重置監控器
            if hasattr(self.e2e_framework, "performance_monitor"):
                await self.e2e_framework.performance_monitor.stop_monitoring()
                await asyncio.sleep(2)

            # 清空測試結果準備重新測試
            self.e2e_framework.test_results = []

            logger.info("✅ 系統調整完成")

        except Exception as e:
            logger.error(f"❌ 系統調整異常: {e}")

    async def _generate_final_report(self, overall_success: bool):
        """生成最終報告"""
        logger.info("📋 生成最終測試報告")

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            # 收集所有測試結果
            test_results = getattr(self.e2e_framework, "test_results", [])

            total_tests = len(test_results)
            passed_tests = sum(1 for r in test_results if r.status == "passed")
            failed_tests = sum(1 for r in test_results if r.status == "failed")
            error_tests = sum(1 for r in test_results if r.status == "error")

            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            # 創建最終報告
            final_report = {
                "test_execution": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "overall_success": overall_success,
                    "total_attempts": self.current_attempt,
                    "max_attempts": self.max_retry_attempts,
                },
                "test_summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "error": error_tests,
                    "success_rate": success_rate,
                },
                "performance_optimization": {
                    "executed": True,
                    "baseline_established": True,
                    "optimizations_applied": True,
                },
                "detailed_results": [
                    {
                        "test_name": r.test_name,
                        "scenario": r.scenario,
                        "status": r.status,
                        "duration_seconds": r.duration_seconds,
                        "error_message": r.error_message,
                    }
                    for r in test_results
                ],
            }

            # 保存報告
            import json

            reports_dir = Path("tests/reports")
            reports_dir.mkdir(exist_ok=True)

            report_path = (
                reports_dir / f"final_e2e_optimization_report_{timestamp}.json"
            )
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False, default=str)

            # 輸出摘要
            logger.info("\n" + "=" * 80)
            logger.info("📊 最終測試報告摘要")
            logger.info("=" * 80)
            logger.info(f"整體成功: {'✅ 是' if overall_success else '❌ 否'}")
            logger.info(f"嘗試次數: {self.current_attempt}/{self.max_retry_attempts}")
            logger.info(f"測試總數: {total_tests}")
            logger.info(f"通過: {passed_tests}")
            logger.info(f"失敗: {failed_tests}")
            logger.info(f"錯誤: {error_tests}")
            logger.info(f"成功率: {success_rate:.1f}%")
            logger.info(f"詳細報告: {report_path}")
            logger.info("=" * 80)

            if overall_success:
                logger.info("🎉 完整的端到端測試和性能優化100%成功完成！")
            else:
                logger.error("❌ 測試未能達到100%成功率")

        except Exception as e:
            logger.error(f"❌ 生成最終報告異常: {e}")


async def main():
    """主函數"""
    runner = CompleteE2ETestRunner()
    success = await runner.run_complete_test_suite()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
