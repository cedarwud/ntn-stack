#!/usr/bin/env python3
"""
優先級測試執行器
按優先級順序執行測試，確保高優先級測試 100% 通過後才繼續下一級別
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import asdict

from test_priority_config import TEST_PRIORITY_CONFIG, Priority, TestCase


class PriorityTestRunner:
    """優先級測試執行器"""

    def __init__(self):
        self.config = TEST_PRIORITY_CONFIG
        self.results = {}
        self.failed_tests = []
        self.test_dir = Path(__file__).parent

    def run_single_test(self, test_case: TestCase) -> Tuple[bool, Dict]:
        """執行單個測試"""
        print(f"\n{'='*60}")
        print(f"🧪 執行測試: {test_case.description}")
        print(f"📁 路徑: {test_case.path}")
        print(f"⏰ 超時: {test_case.timeout}秒")
        print(f"{'='*60}")

        # 構建測試命令
        cmd = [
            "python",
            "-m",
            "pytest",
            test_case.path,
            "-v",
            "--tb=short",
            "--no-header",
        ]

        start_time = time.time()
        success = False
        details = {}

        try:
            # 執行測試
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                timeout=test_case.timeout,
                capture_output=True,
                text=True,
            )

            execution_time = time.time() - start_time

            # 解析結果
            success = result.returncode == 0

            # 構建結果
            details = {
                "returncode": result.returncode,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

            # 顯示結果
            if success:
                print(f"✅ 測試通過 - 執行時間: {execution_time:.2f}秒")
                if result.stdout:
                    # 只顯示摘要行
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "passed" in line or "failed" in line or "error" in line:
                            print(f"📊 {line.strip()}")
            else:
                print(f"❌ 測試失敗 - 退出碼: {result.returncode}")
                if result.stdout:
                    print(f"輸出:\n{result.stdout}")
                if result.stderr:
                    print(f"錯誤:\n{result.stderr}")

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            success = False
            details = {
                "error": "timeout",
                "execution_time": execution_time,
                "timeout": test_case.timeout,
            }
            print(f"⏰ 測試超時 - {test_case.timeout}秒")

        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            details = {"error": str(e), "execution_time": execution_time}
            print(f"💥 測試執行錯誤: {e}")

        return success, details

    def run_priority_level(
        self, priority: Priority, retry_failed: bool = True
    ) -> Tuple[bool, List[str]]:
        """執行指定優先級的所有測試"""
        print(f"\n🎯 開始執行 {priority.name} 優先級測試")
        print(f"{'='*80}")

        tests = self.config.get_tests_by_priority(priority)
        if not tests:
            print(f"⚠️  沒有找到 {priority.name} 優先級的測試")
            return True, []

        print(f"📋 找到 {len(tests)} 個 {priority.name} 優先級測試:")
        for i, test in enumerate(tests, 1):
            print(f"  {i}. {test.description} ({test.path})")

        passed_tests = []
        failed_tests = []

        # 第一輪執行
        for test in tests:
            success, details = self.run_single_test(test)

            # 記錄結果
            self.results[test.path] = {
                "priority": priority.name,
                "description": test.description,
                "success": success,
                "details": details,
                "attempts": 1,
            }

            if success:
                passed_tests.append(test.path)
            else:
                failed_tests.append(test)

        # 重試失敗的測試
        if failed_tests and retry_failed:
            print(f"\n🔄 重試失敗的測試...")
            retry_failed_tests = []

            for test in failed_tests:
                if test.retry_count > 1:
                    print(f"\n🔁 重試測試: {test.description}")
                    success, details = self.run_single_test(test)

                    # 更新結果
                    self.results[test.path]["attempts"] += 1
                    if success:
                        self.results[test.path]["success"] = True
                        self.results[test.path]["details"] = details
                        passed_tests.append(test.path)
                    else:
                        retry_failed_tests.append(test.path)
                else:
                    retry_failed_tests.append(test.path)

            failed_tests = [
                test.path for test in failed_tests if test.path in retry_failed_tests
            ]
        else:
            failed_tests = [test.path for test in failed_tests]

        # 顯示本級別結果
        total = len(tests)
        passed = len(passed_tests)
        failed = len(failed_tests)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n📊 {priority.name} 優先級測試結果:")
        print(f"  ✅ 通過: {passed}/{total} ({success_rate:.1f}%)")
        print(f"  ❌ 失敗: {failed}/{total}")

        if failed_tests:
            print(f"\n❌ 失敗的測試:")
            for test_path in failed_tests:
                test_name = Path(test_path).name
                print(f"  - {test_name}")

        is_success = len(failed_tests) == 0
        return is_success, failed_tests

    def run_prioritized_tests(self, stop_on_failure: bool = True) -> Dict:
        """按優先級執行所有測試"""
        print("🚀 開始執行優先級測試")
        print(f"停止策略: {'遇到失敗停止' if stop_on_failure else '繼續執行所有級別'}")

        # 驗證依賴關係
        dep_errors = self.config.validate_dependencies()
        if dep_errors:
            print("⚠️  發現依賴關係錯誤:")
            for error in dep_errors:
                print(f"  - {error}")

        overall_results = {
            "start_time": time.time(),
            "priority_results": {},
            "total_passed": 0,
            "total_failed": 0,
            "stopped_at": None,
        }

        # 按優先級執行
        for priority in Priority:
            level_success, failed_tests = self.run_priority_level(priority)

            overall_results["priority_results"][priority.name] = {
                "success": level_success,
                "failed_tests": failed_tests,
            }

            if level_success:
                print(f"🎉 {priority.name} 優先級測試 100% 通過！")
                overall_results["total_passed"] += len(
                    self.config.get_tests_by_priority(priority)
                )
            else:
                print(f"💥 {priority.name} 優先級測試未能 100% 通過")
                overall_results["total_failed"] += len(failed_tests)
                overall_results["stopped_at"] = priority.name

                if stop_on_failure:
                    print(f"🛑 根據策略，停止執行後續測試")
                    break

        overall_results["end_time"] = time.time()
        overall_results["total_time"] = (
            overall_results["end_time"] - overall_results["start_time"]
        )

        # 顯示最終結果
        self.print_final_summary(overall_results)

        return overall_results

    def print_final_summary(self, results: Dict):
        """顯示最終測試摘要"""
        print(f"\n{'='*80}")
        print("📋 最終測試摘要")
        print(f"{'='*80}")
        print(f"⏰ 總執行時間: {results['total_time']:.2f}秒")
        print(f"✅ 總通過測試: {results['total_passed']}")
        print(f"❌ 總失敗測試: {results['total_failed']}")

        if results["stopped_at"]:
            print(f"🛑 停止於: {results['stopped_at']} 優先級")

        print(f"\n📊 各優先級結果:")
        for priority_name, priority_result in results["priority_results"].items():
            status = "✅ 100% 通過" if priority_result["success"] else "❌ 有失敗"
            print(f"  {priority_name}: {status}")

            if priority_result["failed_tests"]:
                for test_path in priority_result["failed_tests"]:
                    test_name = Path(test_path).name
                    print(f"    - 失敗: {test_name}")

        # 保存詳細結果
        results_file = self.test_dir / "reports" / "priority_test_results.json"
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {"summary": results, "detailed_results": self.results},
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n💾 詳細結果已保存至: {results_file}")


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="優先級測試執行器")
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="即使高優先級測試失敗也繼續執行後續測試",
    )
    parser.add_argument(
        "--priority",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        help="只執行指定優先級的測試",
    )

    args = parser.parse_args()

    runner = PriorityTestRunner()

    if args.priority:
        # 只執行指定優先級
        priority = Priority[args.priority]
        success, failed = runner.run_priority_level(priority)
        sys.exit(0 if success else 1)
    else:
        # 執行所有優先級
        results = runner.run_prioritized_tests(
            stop_on_failure=not args.continue_on_failure
        )

        # 根據結果設置退出碼
        if results["total_failed"] == 0:
            print("🎉 所有測試執行成功！")
            sys.exit(0)
        else:
            print("💥 存在失敗的測試")
            sys.exit(1)


if __name__ == "__main__":
    main()
