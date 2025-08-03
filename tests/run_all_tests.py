#!/usr/bin/env python3
"""
NTN-Stack 統一測試執行器

一站式執行所有測試的入口程式，提供完整的測試控制和報告功能。

執行方式:
python run_all_tests.py [options]

選項:
--quick                快速模式（跳過耗時測試）
--type=TYPE           測試類型: unit,integration,performance,e2e,paper,frontend,all
--stage=STAGE         論文測試階段: 1,2,all
--frontend-type=TYPE  前端測試類型: components,api,e2e,console,all
--verbose             詳細輸出
--report              生成報告
"""

import sys
import os
import time
import argparse
import subprocess
import logging
from datetime import datetime
from typing import List
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnifiedTestRunner:
    """統一測試執行器"""

    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def run_test_module(
            self,
            module_name: str,
            args: List[str] = None) -> bool:
        """執行測試模組"""
        logger.info(f"🧪 執行 {module_name}...")

        cmd = [sys.executable, f"{module_name}.py"]
        if args:
            cmd.extend(args)

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
            duration = time.time() - start_time

            success = result.returncode == 0
            self.test_results[module_name] = {
                'success': success,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

            if success:
                logger.info(f"✅ {module_name} 完成 ({duration:.2f}s)")
                self.passed_tests += 1
            else:
                logger.error(f"❌ {module_name} 失敗 ({duration:.2f}s)")
                if result.stderr:
                    logger.error(f"錯誤詳情: {result.stderr}")
                self.failed_tests += 1

            self.total_tests += 1
            return success

        except Exception as e:
            logger.error(f"❌ 執行 {module_name} 時發生異常: {e}")
            self.test_results[module_name] = {
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': str(e)
            }
            self.failed_tests += 1
            self.total_tests += 1
            return False

    def run_unified_tests(
            self,
            test_type: str = "all",
            quick_mode: bool = False):
        """執行統一測試"""
        args = [f"--type={test_type}"]
        if quick_mode:
            args.append("--quick")
        return self.run_test_module("unified_tests", args)

    def run_paper_tests(self, stage: str = "all", quick_mode: bool = False):
        """執行論文測試"""
        args = [f"--stage={stage}"]
        if quick_mode:
            args.append("--quick")
        return self.run_test_module("paper_tests", args)


    def run_frontend_tests(
            self,
            frontend_type: str = "all",
            quick_mode: bool = False):
        """執行前端測試"""
        logger.info(f"🎯 執行前端測試 (類型: {frontend_type})...")

        try:
            start_time = time.time()

            # 前端項目路徑
            frontend_path = Path("/home/sat/ntn-stack/simworld/frontend")
            if not frontend_path.exists():
                logger.error("❌ 前端項目路徑不存在")
                return False

            # 檢查是否有 npm/yarn
            package_manager = None
            if (frontend_path / "package.json").exists():
                # 檢查 npm
                try:
                    subprocess.run(["npm", "--version"],
                                   capture_output=True, check=True)
                    package_manager = "npm"
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.warning("npm 不可用，嘗試使用 yarn")
                    try:
                        subprocess.run(["yarn", "--version"],
                                       capture_output=True, check=True)
                        package_manager = "yarn"
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        logger.error("❌ npm 和 yarn 都不可用")
                        return False

            if not package_manager:
                logger.error("❌ 找不到 package.json 或包管理器")
                return False

            # 構建測試命令
            test_cmd = [package_manager, "run", "test"]

            # 根據測試類型添加參數
            if frontend_type != "all":
                # Vitest 支援按文件名過濾
                if frontend_type == "components":
                    test_cmd.extend(["--", "components.test.tsx"])
                elif frontend_type == "api":
                    test_cmd.extend(["--", "api.test.ts"])
                elif frontend_type == "e2e":
                    test_cmd.extend(["--", "e2e.test.tsx"])
                elif frontend_type == "console":
                    test_cmd.extend(["--", "console-errors.test.ts"])

            # 添加測試環境變數
            env = os.environ.copy()
            env['NODE_ENV'] = 'test'
            env['VITEST_ENV'] = 'test'

            # 執行前端測試
            logger.info(f"執行命令: {' '.join(test_cmd)}")
            result = subprocess.run(
                test_cmd,
                cwd=frontend_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5分鐘超時
            )

            duration = time.time() - start_time

            # 記錄結果
            success = result.returncode == 0
            self.test_results["frontend_tests"] = {
                'success': success,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_type': frontend_type
            }

            if success:
                logger.info(f"✅ 前端測試完成 ({duration:.2f}s)")
                self.passed_tests += 1
            else:
                logger.error(f"❌ 前端測試失敗 ({duration:.2f}s)")
                if result.stderr:
                    logger.error(f"錯誤詳情: {result.stderr}")
                if result.stdout:
                    logger.info(f"測試輸出: {result.stdout}")
                self.failed_tests += 1

            self.total_tests += 1
            return success

        except subprocess.TimeoutExpired:
            logger.error("❌ 前端測試超時")
            self.test_results["frontend_tests"] = {
                'success': False,
                'duration': 300,
                'stdout': '',
                'stderr': 'Test timeout after 5 minutes',
                'test_type': frontend_type
            }
            self.failed_tests += 1
            self.total_tests += 1
            return False
        except Exception as e:
            logger.error(f"❌ 執行前端測試時發生異常: {e}")
            self.test_results["frontend_tests"] = {
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': str(e),
                'test_type': frontend_type
            }
            self.failed_tests += 1
            self.total_tests += 1
            return False

    def generate_report(self) -> str:
        """生成測試報告 - 純文字格式"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        report = "\n=== NTN-Stack 測試報告 ===\n"
        report += f"開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"總耗時: {total_duration:.2f} 秒\n\n"

        report += "測試統計:\n"
        report += f"  總測試數: {self.total_tests}\n"
        report += f"  通過數量: {self.passed_tests}\n"
        report += f"  失敗數量: {self.failed_tests}\n"
        report += f"  成功率: {(self.passed_tests/max(self.total_tests,1)*100):.1f}%\n\n"

        report += "測試詳情:\n"
        for module, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            report += f"  {module:15s} {status} ({result['duration']:6.2f}s)\n"

        return report


def main():
    parser = argparse.ArgumentParser(description='NTN-Stack 統一測試執行器')
    parser.add_argument('--quick', action='store_true', help='快速模式')
    parser.add_argument(
        '--type',
        choices=[
            'unit',
            'integration',
            'performance',
            'e2e',
            'paper',
            'frontend',
            'all'],
        default='all',
        help='測試類型')
    parser.add_argument(
        '--stage', choices=['1', '2', 'all'], default='all', help='論文測試階段')
    parser.add_argument(
        '--env',
        choices=[
            'satellite',
            'handover',
            'all'],
        default='all',
        help='Gymnasium環境')
    parser.add_argument(
        '--frontend-type',
        choices=[
            'components',
            'api',
            'e2e',
            'console',
            'all'],
        default='all',
        help='前端測試類型')
    parser.add_argument('--verbose', action='store_true', help='詳細輸出')
    parser.add_argument('--report', action='store_true', help='生成報告')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    runner = UnifiedTestRunner()

    logger.info("🚀 開始執行 NTN-Stack 測試套件...")

    # 根據指定的測試類型執行測試
    if args.type in ['all', 'unit', 'integration', 'performance', 'e2e']:
        if args.type == 'all':
            # 分別執行各類測試
            runner.run_unified_tests('unit', args.quick)
            runner.run_unified_tests('integration', args.quick)
            runner.run_unified_tests('performance', args.quick)
            runner.run_unified_tests('e2e', args.quick)
        else:
            runner.run_unified_tests(args.type, args.quick)

    if args.type in ['all', 'paper']:
        runner.run_paper_tests(args.stage, args.quick)


    if args.type in ['all', 'frontend']:
        runner.run_frontend_tests(
            getattr(args, 'frontend_type', 'all'), args.quick)

    # 生成並顯示報告
    report = runner.generate_report()
    print(report)

    if args.report:
        report_file = f"reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 報告已保存到 {report_file}")

    # 根據測試結果設置退出碼
    exit_code = 0 if runner.failed_tests == 0 else 1
    logger.info(f"🏁 測試完成，退出碼: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
