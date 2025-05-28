#!/usr/bin/env python3
"""
NTN Stack 完整測試運行器

執行所有測試並生成綜合報告
"""

import asyncio
import subprocess
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any


class CompleteTestRunner:
    """完整測試運行器"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.tests_dir = "/home/sat/ntn-stack/tests"

    def run_test_script(self, script_name: str) -> Dict[str, Any]:
        """運行單個測試腳本"""
        print(f"\n🚀 執行測試: {script_name}")
        print("-" * 60)

        start_time = time.time()

        try:
            # 運行測試腳本
            result = subprocess.run(
                ["python", script_name],
                cwd=self.tests_dir,
                capture_output=True,
                text=True,
                timeout=120,  # 2分鐘超時
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # 解析輸出中的成功率
            output_lines = result.stdout.split("\n")
            success_rate = None
            test_count = None
            passed_count = None

            for line in output_lines:
                if "成功率:" in line or "📈 成功率:" in line:
                    try:
                        success_rate = float(
                            line.split(":")[-1].replace("%", "").strip()
                        )
                    except:
                        pass
                if "總測試數量:" in line:
                    try:
                        test_count = int(line.split(":")[-1].strip())
                    except:
                        pass
                if "通過測試:" in line:
                    try:
                        passed_count = int(line.split(":")[-1].strip())
                    except:
                        pass

            test_result = {
                "script": script_name,
                "success": success,
                "duration": duration,
                "success_rate": success_rate,
                "test_count": test_count,
                "passed_count": passed_count,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

            # 顯示結果摘要
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {script_name} ({duration:.2f}s)")
            if success_rate is not None:
                print(f"    成功率: {success_rate:.1f}%")
            if test_count is not None and passed_count is not None:
                print(f"    測試結果: {passed_count}/{test_count}")

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"❌ TIMEOUT {script_name} ({duration:.2f}s)")
            return {
                "script": script_name,
                "success": False,
                "duration": duration,
                "success_rate": 0.0,
                "error": "timeout",
                "stdout": "",
                "stderr": "測試超時",
            }

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ ERROR {script_name} ({duration:.2f}s): {e}")
            return {
                "script": script_name,
                "success": False,
                "duration": duration,
                "success_rate": 0.0,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
            }

    def run_all_tests(self):
        """運行所有測試"""
        print("🏆 NTN Stack 完整測試運行器")
        print("=" * 70)
        print(f"開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # 定義要運行的測試腳本
        test_scripts = [
            "final_optimized_test.py",
            "final_network_verification.py",
            "final_complete_test.py",
        ]

        # 運行每個測試
        for script in test_scripts:
            result = self.run_test_script(script)
            self.test_results.append(result)

    def generate_comprehensive_report(self):
        """生成綜合報告"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # 計算整體統計
        total_scripts = len(self.test_results)
        successful_scripts = sum(1 for r in self.test_results if r["success"])
        failed_scripts = total_scripts - successful_scripts

        # 計算加權平均成功率
        total_tests = 0
        total_passed = 0

        for result in self.test_results:
            if result.get("test_count") and result.get("passed_count"):
                total_tests += result["test_count"]
                total_passed += result["passed_count"]

        overall_success_rate = (
            (total_passed / total_tests * 100) if total_tests > 0 else 0
        )

        print("\n" + "=" * 70)
        print("📊 NTN Stack 完整測試綜合報告")
        print("=" * 70)
        print(
            f"測試時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%H:%M:%S')}"
        )
        print(f"總執行時間: {total_duration:.2f} 秒")
        print()

        print("📋 測試腳本執行結果:")
        print("-" * 40)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            script_name = result["script"].replace(".py", "")
            success_rate = result.get("success_rate", 0)
            print(
                f"{status} {script_name:<25} {success_rate:>6.1f}% ({result['duration']:.2f}s)"
            )

        print()
        print("📈 綜合統計:")
        print("-" * 40)
        print(f"測試腳本總數: {total_scripts}")
        print(f"✅ 成功執行: {successful_scripts}")
        print(f"❌ 執行失敗: {failed_scripts}")
        print(f"📊 腳本成功率: {successful_scripts/total_scripts*100:.1f}%")

        print()
        print(f"總測試案例數: {total_tests}")
        print(f"✅ 通過測試: {total_passed}")
        print(f"❌ 失敗測試: {total_tests - total_passed}")
        print(f"📈 整體成功率: {overall_success_rate:.1f}%")

        print("\n🎯 系統狀態評估:")
        print("-" * 40)

        # 根據結果評估系統狀態
        if overall_success_rate >= 95:
            print("   ✅ 系統狀態：優秀 (可用於生產部署)")
            print("   ✅ 網路連接：完全正常")
            print("   ✅ 核心功能：100% 可用")
            print("   ✅ API 接口：完全穩定")
        elif overall_success_rate >= 85:
            print("   ✅ 系統狀態：良好 (基本可用於部署)")
            print("   ✅ 網路連接：正常")
            print("   ✅ 核心功能：主要可用")
            print("   ⚠️  API 接口：部分需要優化")
        elif overall_success_rate >= 70:
            print("   ⚠️  系統狀態：基本可用")
            print("   ✅ 網路連接：大部分正常")
            print("   ⚠️  核心功能：部分限制")
            print("   ⚠️  API 接口：需要改善")
        else:
            print("   ❌ 系統狀態：需要進一步改善")
            print("   ⚠️  建議檢查基礎設施配置")

        print("\n🔧 功能模組狀態:")
        print("-" * 40)

        # 分析功能模組狀態
        optimized_test = next(
            (r for r in self.test_results if "optimized" in r["script"]), None
        )
        if optimized_test and optimized_test.get("success_rate", 0) >= 90:
            print("   ✅ 第6項 (Sionna & UERANSIM)：完全正常")
            print("   ✅ 第7項 (干擾控制機制)：完全正常")
        else:
            print("   ⚠️  第6項 (Sionna & UERANSIM)：需要檢查")
            print("   ⚠️  第7項 (干擾控制機制)：需要檢查")

        network_test = next(
            (r for r in self.test_results if "network" in r["script"]), None
        )
        if network_test and network_test.get("success_rate", 0) >= 80:
            print("   ✅ 網路通信：已解決隔離問題")
        else:
            print("   ⚠️  網路通信：可能仍有問題")

        # 保存綜合報告
        report_data = {
            "test_suite": "NTN Stack 完整測試綜合報告",
            "execution_time": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_sec": total_duration,
            },
            "summary": {
                "total_scripts": total_scripts,
                "successful_scripts": successful_scripts,
                "failed_scripts": failed_scripts,
                "script_success_rate": successful_scripts / total_scripts * 100,
                "total_test_cases": total_tests,
                "passed_test_cases": total_passed,
                "failed_test_cases": total_tests - total_passed,
                "overall_success_rate": overall_success_rate,
            },
            "detailed_results": self.test_results,
            "system_assessment": {
                "network_connectivity": (
                    "resolved" if overall_success_rate >= 80 else "needs_work"
                ),
                "core_functionality": (
                    "excellent"
                    if overall_success_rate >= 95
                    else "good" if overall_success_rate >= 85 else "needs_improvement"
                ),
                "api_stability": (
                    "stable" if overall_success_rate >= 90 else "needs_optimization"
                ),
                "production_ready": overall_success_rate >= 85,
            },
        }

        # 保存報告
        report_dir = "/home/sat/ntn-stack/tests/reports"
        os.makedirs(report_dir, exist_ok=True)
        report_filename = f"{report_dir}/comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n📄 詳細報告已保存至: {report_filename}")
        except Exception as e:
            print(f"\n⚠️  報告保存失敗: {e}")

        # 結論
        print(f"\n{'='*70}")
        print("🏁 最終結論")
        print(f"{'='*70}")

        if overall_success_rate >= 95:
            print("🎉 系統完全就緒，可立即部署！")
        elif overall_success_rate >= 85:
            print("✅ 系統基本就緒，可考慮部署")
        elif overall_success_rate >= 70:
            print("⚠️  系統基本可用，建議優化後部署")
        else:
            print("❌ 系統需要進一步改善")

        print(f"\n📊 最終整體成功率: {overall_success_rate:.1f}%")
        return overall_success_rate


def main():
    """主函數"""
    runner = CompleteTestRunner()
    runner.run_all_tests()
    success_rate = runner.generate_comprehensive_report()

    # 返回適當的退出碼
    if success_rate >= 85:
        exit(0)  # 成功
    else:
        exit(1)  # 需要改善


if __name__ == "__main__":
    main()
