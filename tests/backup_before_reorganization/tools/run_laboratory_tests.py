#!/usr/bin/env python3
"""
NTN Stack 實驗室驗測執行腳本

這是實驗室驗測的主要執行入口，提供命令行接口來運行完整的測試套件
目標是達到 100% 測試通過率，符合實驗室驗測的嚴格要求

使用方法：
  python tests/run_laboratory_tests.py                    # 執行完整測試套件
  python tests/run_laboratory_tests.py --quick           # 快速測試
  python tests/run_laboratory_tests.py --performance     # 只執行性能測試
  python tests/run_laboratory_tests.py --stress          # 只執行壓力測試
  python tests/run_laboratory_tests.py --config custom.yaml  # 使用自定義配置
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.laboratory_test_suite import (
    LaboratoryTestEnvironment,
    LaboratoryTestExecutor,
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f"tests/reports/laboratory/lab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(
        description="NTN Stack 實驗室驗測執行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
測試模式說明：
  full        執行完整的實驗室驗測套件（默認）
  quick       快速測試，跳過長時間運行的測試
  performance 只執行性能相關測試
  stress      只執行壓力測試
  connectivity 只執行連接性測試
  api         只執行 API 功能測試

示例：
  python tests/run_laboratory_tests.py --mode quick
  python tests/run_laboratory_tests.py --config tests/configs/custom_lab_config.yaml
  python tests/run_laboratory_tests.py --verbose --no-reports
        """,
    )

    parser.add_argument(
        "--mode",
        "-m",
        choices=["full", "quick", "performance", "stress", "connectivity", "api"],
        default="full",
        help="測試執行模式（默認：full）",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="tests/configs/laboratory_test_config.yaml",
        help="測試配置文件路徑（默認：laboratory_test_config.yaml）",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="啟用詳細日誌輸出")

    parser.add_argument("--no-reports", action="store_true", help="不生成測試報告")

    parser.add_argument(
        "--max-retries", type=int, default=3, help="測試失敗時的最大重試次數（默認：3）"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,  # 30 分鐘
        help="測試總體超時時間（秒，默認：1800）",
    )

    return parser.parse_args()


class LaboratoryTestRunner:
    """實驗室測試執行器"""

    def __init__(self, args):
        self.args = args
        self.start_time = datetime.utcnow()

        # 設置日誌級別
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # 初始化測試環境
        self.test_env = LaboratoryTestEnvironment(args.config)
        self.executor = LaboratoryTestExecutor(self.test_env)

    async def run_tests(self) -> bool:
        """執行測試"""
        logger.info("🧪 啟動 NTN Stack 實驗室驗測")
        logger.info(f"📋 測試模式: {self.args.mode}")
        logger.info(f"⚙️ 配置文件: {self.args.config}")
        logger.info(f"🕐 開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        try:
            # 步驟 1: 環境驗證
            logger.info("\n" + "=" * 60)
            logger.info("📋 第一階段：環境驗證")
            logger.info("=" * 60)

            if not await self.test_env.validate_environment():
                logger.error("❌ 環境驗證失敗，測試中止")
                return False

            logger.info("✅ 環境驗證通過")

            # 步驟 2: 根據模式執行測試
            logger.info("\n" + "=" * 60)
            logger.info("📋 第二階段：執行測試套件")
            logger.info("=" * 60)

            success = await self._execute_test_mode()

            # 步驟 3: 生成報告
            if not self.args.no_reports:
                logger.info("\n" + "=" * 60)
                logger.info("📋 第三階段：生成測試報告")
                logger.info("=" * 60)

                await self.executor._generate_final_report(success)

            # 步驟 4: 總結
            await self._print_summary(success)

            return success

        except asyncio.TimeoutError:
            logger.error(f"❌ 測試超時（{self.args.timeout} 秒）")
            return False

        except KeyboardInterrupt:
            logger.info("🛑 測試被用戶中斷")
            return False

        except Exception as e:
            logger.error(f"💥 測試執行發生未預期錯誤: {e}")
            logger.exception("詳細錯誤信息：")
            return False

    async def _execute_test_mode(self) -> bool:
        """根據模式執行測試"""
        if self.args.mode == "full":
            return await self.executor.execute_full_test_suite()

        elif self.args.mode == "quick":
            return await self._execute_quick_tests()

        elif self.args.mode == "performance":
            return await self._execute_performance_tests()

        elif self.args.mode == "stress":
            return await self._execute_stress_tests()

        elif self.args.mode == "connectivity":
            return await self._execute_connectivity_tests()

        elif self.args.mode == "api":
            return await self._execute_api_tests()

        else:
            logger.error(f"未知的測試模式: {self.args.mode}")
            return False

    async def _execute_quick_tests(self) -> bool:
        """執行快速測試"""
        logger.info("⚡ 執行快速測試模式")

        quick_tests = [
            ("environment_setup", await self.executor._test_environment_setup()),
            ("service_health_check", await self.executor._test_service_health()),
            ("basic_connectivity", await self.executor._test_basic_connectivity()),
            ("api_functionality", await self.executor._test_api_functionality()),
        ]

        passed_tests = sum(1 for _, passed in quick_tests if passed)
        total_tests = len(quick_tests)
        success_rate = passed_tests / total_tests

        logger.info(
            f"⚡ 快速測試完成：{passed_tests}/{total_tests} 通過 (成功率: {success_rate:.1%})"
        )

        return success_rate == 1.0

    async def _execute_performance_tests(self) -> bool:
        """執行性能測試"""
        logger.info("⚡ 執行性能測試模式")

        performance_tests = [
            (
                "performance_validation",
                await self.executor._test_performance_validation(),
            ),
            ("load_testing", await self.executor._test_load_testing()),
        ]

        passed_tests = sum(1 for _, passed in performance_tests if passed)
        total_tests = len(performance_tests)
        success_rate = passed_tests / total_tests

        logger.info(
            f"⚡ 性能測試完成：{passed_tests}/{total_tests} 通過 (成功率: {success_rate:.1%})"
        )

        return success_rate == 1.0

    async def _execute_stress_tests(self) -> bool:
        """執行壓力測試"""
        logger.info("💥 執行壓力測試模式")

        stress_result = await self.executor._test_stress()

        logger.info(f"💥 壓力測試完成：{'通過' if stress_result[0] else '失敗'}")

        return stress_result[0]

    async def _execute_connectivity_tests(self) -> bool:
        """執行連接性測試"""
        logger.info("🔗 執行連接性測試模式")

        connectivity_result = await self.executor._test_basic_connectivity()

        logger.info(
            f"🔗 連接性測試完成：{'通過' if connectivity_result[0] else '失敗'}"
        )

        return connectivity_result[0]

    async def _execute_api_tests(self) -> bool:
        """執行 API 測試"""
        logger.info("🌐 執行 API 測試模式")

        api_result = await self.executor._test_api_functionality()

        logger.info(f"🌐 API 測試完成：{'通過' if api_result[0] else '失敗'}")

        return api_result[0]

    async def _print_summary(self, success: bool):
        """打印測試總結"""
        end_time = datetime.utcnow()
        duration = end_time - self.start_time

        logger.info("\n" + "=" * 60)
        logger.info("📊 實驗室驗測總結")
        logger.info("=" * 60)
        logger.info(f"🕐 開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"🕐 結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"⏱️ 總耗時: {duration}")
        logger.info(f"📋 測試模式: {self.args.mode}")
        logger.info(f"⚙️ 配置文件: {self.args.config}")

        if hasattr(self.test_env, "phase_results") and self.test_env.phase_results:
            total_phases = len(self.test_env.phase_results)
            passed_phases = sum(
                1 for p in self.test_env.phase_results if p.status == "passed"
            )
            logger.info(f"📈 階段結果: {passed_phases}/{total_phases} 通過")

        if hasattr(self.test_env, "test_results") and self.test_env.test_results:
            total_tests = len(self.test_env.test_results)
            passed_tests = sum(
                1 for t in self.test_env.test_results if t.status == "passed"
            )
            success_rate = passed_tests / total_tests
            logger.info(
                f"📈 測試結果: {passed_tests}/{total_tests} 通過 (成功率: {success_rate:.1%})"
            )

        if success:
            logger.info("🎉 實驗室驗測成功完成！")
            logger.info("✨ 所有測試均已通過，系統達到實驗室驗測標準")
        else:
            logger.error("❌ 實驗室驗測未完全通過")
            logger.error("⚠️ 請檢查失敗的測試項目並修復相關問題")

        logger.info("=" * 60)


async def main():
    """主程序入口"""
    args = parse_arguments()

    # 確保報告目錄存在
    reports_dir = Path("tests/reports/laboratory")
    reports_dir.mkdir(parents=True, exist_ok=True)

    runner = LaboratoryTestRunner(args)

    try:
        # 設置總體超時
        success = await asyncio.wait_for(runner.run_tests(), timeout=args.timeout)

        # 設置退出碼
        sys.exit(0 if success else 1)

    except asyncio.TimeoutError:
        logger.error(f"❌ 測試執行超時（{args.timeout} 秒）")
        sys.exit(2)

    except Exception as e:
        logger.error(f"💥 程序執行異常: {e}")
        sys.exit(3)


if __name__ == "__main__":
    # 檢查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        sys.exit(1)

    # 運行主程序
    asyncio.run(main())
