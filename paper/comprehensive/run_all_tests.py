#!/usr/bin/env python3
"""
論文復現綜合測試執行器

統一執行 1.1 到 1.3 的所有測試，生成完整的論文復現報告

執行方式 (在 ntn-stack 根目錄):
source venv/bin/activate
python paper/comprehensive/run_all_tests.py

或指定特定階段:
python paper/comprehensive/run_all_tests.py --stage 1.2
python paper/comprehensive/run_all_tests.py --stage 1.3
python paper/comprehensive/run_all_tests.py --stage all
"""

import sys
import os
import asyncio
import argparse
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import traceback

# 添加 NetStack API 路徑
sys.path.insert(0, "/home/sat/ntn-stack/netstack/netstack_api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperReproductionTestRunner:
    """論文復現綜合測試執行器"""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        self.base_path = "/home/sat/ntn-stack/paper"

        # 測試階段定義 (修正路徑)
        self.test_stages = {
            "1.1": {
                "name": "衛星軌道預測模組整合",
                "script": f"{self.base_path}/1.1_satellite_orbit/test_tle_integration.py",
                "description": "NetStack ↔ SimWorld TLE 資料橋接",
            },
            "1.2": {
                "name": "同步演算法 (Algorithm 1)",
                "script": f"{self.base_path}/1.2_synchronized_algorithm/test_algorithm_1.py",
                "description": "二分搜尋換手時間預測、週期性更新機制",
            },
            "1.3": {
                "name": "快速衛星預測演算法 (Algorithm 2)",
                "script": f"{self.base_path}/1.3_fast_prediction/test_algorithm_2.py",
                "description": "地理區塊劃分、UE存取策略管理",
            },
        }

    async def run_stage_test(self, stage_id: str) -> Dict[str, Any]:
        """執行單個階段的測試"""
        stage_info = self.test_stages[stage_id]

        print(f"\n🔬 執行 {stage_id} {stage_info['name']} 測試...")
        print(f"📝 {stage_info['description']}")
        print("-" * 60)

        start_time = datetime.now()

        try:
            # 使用 venv Python 執行測試腳本
            venv_python = "/home/sat/ntn-stack/venv/bin/python"
            script_path = stage_info["script"]

            # 檢查腳本是否存在
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"測試腳本不存在: {script_path}")

            # 執行測試腳本
            process = await asyncio.create_subprocess_exec(
                venv_python,
                script_path,
                cwd="/home/sat/ntn-stack",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 解析結果
            success = process.returncode == 0
            output = stdout.decode("utf-8") if stdout else ""
            error_output = stderr.decode("utf-8") if stderr else ""

            # 提取測試統計
            passed_tests, total_tests, success_rate = self._parse_test_output(output)

            result = {
                "stage_id": stage_id,
                "stage_name": stage_info["name"],
                "description": stage_info["description"],
                "success": success,
                "duration_seconds": duration,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "success_rate": success_rate,
                "output": output,
                "error_output": error_output,
                "return_code": process.returncode,
            }

            if success:
                print(f"✅ {stage_id} 測試成功完成")
                print(
                    f"   通過測試: {passed_tests}/{total_tests} ({success_rate:.1f}%)"
                )
                print(f"   執行時間: {duration:.2f} 秒")
            else:
                print(f"❌ {stage_id} 測試失敗")
                print(f"   返回碼: {process.returncode}")
                if error_output:
                    print(f"   錯誤輸出: {error_output[:200]}...")

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            error_msg = f"執行 {stage_id} 測試時發生錯誤: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg, exc_info=True)

            return {
                "stage_id": stage_id,
                "stage_name": stage_info["name"],
                "description": stage_info["description"],
                "success": False,
                "duration_seconds": duration,
                "passed_tests": 0,
                "total_tests": 0,
                "success_rate": 0.0,
                "output": "",
                "error_output": str(e),
                "return_code": -1,
                "exception": traceback.format_exc(),
            }

    def _parse_test_output(self, output: str) -> tuple:
        """解析測試輸出，提取統計資訊"""
        passed_tests = 0
        total_tests = 0
        success_rate = 0.0

        try:
            lines = output.split("\n")
            for line in lines:
                if "總測試數:" in line:
                    total_tests = int(line.split(":")[1].strip())
                elif "通過測試:" in line:
                    passed_tests = int(line.split(":")[1].strip())
                elif "成功率:" in line and "%" in line:
                    success_rate = float(line.split(":")[1].replace("%", "").strip())
        except Exception as e:
            logger.warning(f"解析測試輸出失敗: {str(e)}")

        return passed_tests, total_tests, success_rate

    async def run_all_tests(self, stage_filter: str = "all") -> Dict[str, Any]:
        """執行所有測試或指定階段的測試"""
        self.start_time = datetime.now()

        print("🚀 開始執行論文復現綜合測試")
        print("=" * 80)
        print(f"測試範圍: {stage_filter}")
        print(f"開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"測試環境: venv Python 環境")
        print("=" * 80)

        # 確定要執行的階段
        if stage_filter == "all":
            stages_to_run = list(self.test_stages.keys())
        else:
            stages_to_run = [stage_filter] if stage_filter in self.test_stages else []

        if not stages_to_run:
            raise ValueError(f"無效的階段選擇: {stage_filter}")

        # 執行各階段測試
        for stage_id in stages_to_run:
            stage_result = await self.run_stage_test(stage_id)
            self.test_results[stage_id] = stage_result

        self.end_time = datetime.now()

        # 生成綜合報告
        comprehensive_report = self._generate_comprehensive_report()

        # 輸出報告
        self._print_comprehensive_summary(comprehensive_report)

        # 保存報告
        await self._save_comprehensive_report(comprehensive_report)

        return comprehensive_report

    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成綜合測試報告"""
        total_duration = (self.end_time - self.start_time).total_seconds()

        # 計算總體統計
        total_tests = sum(
            result.get("total_tests", 0) for result in self.test_results.values()
        )
        total_passed = sum(
            result.get("passed_tests", 0) for result in self.test_results.values()
        )
        successful_stages = sum(
            1 for result in self.test_results.values() if result.get("success", False)
        )
        total_stages = len(self.test_results)

        return {
            "test_execution_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "test_environment": "venv Python Environment",
                "python_executable": "/home/sat/ntn-stack/venv/bin/python",
            },
            "overall_summary": {
                "total_stages": total_stages,
                "successful_stages": successful_stages,
                "failed_stages": total_stages - successful_stages,
                "stage_success_rate": (
                    f"{(successful_stages/total_stages*100):.1f}%"
                    if total_stages > 0
                    else "0%"
                ),
                "total_individual_tests": total_tests,
                "total_passed_tests": total_passed,
                "total_failed_tests": total_tests - total_passed,
                "overall_test_success_rate": (
                    f"{(total_passed/total_tests*100):.1f}%"
                    if total_tests > 0
                    else "0%"
                ),
            },
            "stage_results": self.test_results,
            "paper_reproduction_validation": self._validate_paper_reproduction(),
            "recommendations": self._generate_recommendations(),
        }

    def _validate_paper_reproduction(self) -> Dict[str, str]:
        """驗證論文復現狀態"""
        validation = {
            "tle_integration": "❌ 未測試",
            "algorithm_1_implementation": "❌ 未測試",
            "algorithm_2_implementation": "❌ 未測試",
            "binary_search_precision": "❌ 未驗證",
            "geographical_block_division": "❌ 未驗證",
            "ue_access_strategy_management": "❌ 未驗證",
            "prediction_accuracy_target": "❌ 未驗證",
            "cross_container_communication": "❌ 未驗證",
        }

        # 檢查 1.1 TLE 整合
        if "1.1" in self.test_results and self.test_results["1.1"].get("success"):
            validation["tle_integration"] = "✅ 已完成"
            validation["cross_container_communication"] = "✅ 已驗證"

        # 檢查 1.2 同步演算法
        if "1.2" in self.test_results and self.test_results["1.2"].get("success"):
            validation["algorithm_1_implementation"] = "✅ 已實現"
            validation["binary_search_precision"] = "✅ 已驗證"

        # 檢查 1.3 快速衛星預測演算法
        if "1.3" in self.test_results and self.test_results["1.3"].get("success"):
            validation["algorithm_2_implementation"] = "✅ 已實現"
            validation["geographical_block_division"] = "✅ 已驗證"
            validation["ue_access_strategy_management"] = "✅ 已驗證"
            validation["prediction_accuracy_target"] = "✅ 已驗證"

        return validation

    def _generate_recommendations(self) -> List[str]:
        """生成建議和後續步驟"""
        recommendations = []

        # 檢查失敗的階段
        failed_stages = [
            stage_id
            for stage_id, result in self.test_results.items()
            if not result.get("success", False)
        ]

        if failed_stages:
            recommendations.append(
                f"🔧 需要修復失敗的測試階段: {', '.join(failed_stages)}"
            )

        # 成功情況的後續步驟
        all_success = all(
            result.get("success", False) for result in self.test_results.values()
        )

        if all_success:
            recommendations.extend(
                [
                    "🎯 1.1-1.3 階段全部通過！可以開始下一階段：1.4 UPF 修改與整合",
                    "📊 建議建立持續整合測試管道",
                    "🚀 可以開始效能最佳化和實際場景測試",
                    "📝 建議更新 CLAUDE.md 文檔以反映當前實現狀態",
                ]
            )
        else:
            recommendations.append(
                "📋 建議逐一檢查失敗的測試階段，確保論文復現的完整性"
            )

        # 效能建議
        total_duration = sum(
            result.get("duration_seconds", 0) for result in self.test_results.values()
        )
        if total_duration > 300:  # 5分鐘
            recommendations.append(
                f"⚡ 測試執行時間較長 ({total_duration:.1f}秒)，考慮優化測試效能"
            )

        return recommendations

    def _print_comprehensive_summary(self, report: Dict[str, Any]):
        """列印綜合測試摘要"""
        print("\n" + "=" * 80)
        print("🎯 論文復現綜合測試報告")
        print("=" * 80)

        # 執行資訊
        exec_info = report["test_execution_info"]
        print(f"\n📊 執行資訊:")
        print(f"   開始時間: {exec_info['start_time']}")
        print(f"   結束時間: {exec_info['end_time']}")
        print(f"   總執行時間: {exec_info['total_duration_seconds']:.1f} 秒")
        print(f"   測試環境: {exec_info['test_environment']}")

        # 總體統計
        summary = report["overall_summary"]
        print(f"\n📊 總體統計:")
        print(
            f"   測試階段: {summary['successful_stages']}/{summary['total_stages']} 成功 ({summary['stage_success_rate']})"
        )
        print(
            f"   個別測試: {summary['total_passed_tests']}/{summary['total_individual_tests']} 通過 ({summary['overall_test_success_rate']})"
        )

        # 階段詳細結果
        print(f"\n📋 階段詳細結果:")
        for stage_id, result in self.test_results.items():
            status_emoji = "✅" if result["success"] else "❌"
            print(f"   {status_emoji} {stage_id} {result['stage_name']}")
            print(
                f"      測試通過: {result['passed_tests']}/{result['total_tests']} ({result['success_rate']:.1f}%)"
            )
            print(f"      執行時間: {result['duration_seconds']:.1f} 秒")
            if not result["success"]:
                print(f"      失敗原因: 返回碼 {result['return_code']}")

        # 論文復現驗證
        print(f"\n🎓 論文復現驗證:")
        validation = report["paper_reproduction_validation"]
        for key, status in validation.items():
            feature_name = key.replace("_", " ").title()
            print(f"   {status} {feature_name}")

        # 建議
        recommendations = report["recommendations"]
        if recommendations:
            print(f"\n💡 建議和後續步驟:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

        print("\n" + "=" * 80)

    async def _save_comprehensive_report(self, report: Dict[str, Any]):
        """保存綜合測試報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = (
            f"/home/sat/paper/comprehensive/paper_reproduction_report_{timestamp}.json"
        )

        # 確保報告目錄存在
        os.makedirs(os.path.dirname(report_filename), exist_ok=True)

        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n📄 詳細測試報告已保存至: {report_filename}")
            logger.info(f"綜合測試報告已保存: {report_filename}")

        except Exception as e:
            logger.error(f"保存綜合測試報告失敗: {str(e)}")


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="論文復現綜合測試執行器")
    parser.add_argument(
        "--stage",
        choices=["1.1", "1.2", "1.3", "all"],
        default="all",
        help="指定要執行的測試階段",
    )
    parser.add_argument("--verbose", action="store_true", help="啟用詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 創建測試執行器
    runner = PaperReproductionTestRunner()

    try:
        # 執行測試
        report = await runner.run_all_tests(stage_filter=args.stage)

        # 根據結果設置退出碼
        all_success = all(
            result.get("success", False) for result in runner.test_results.values()
        )

        if all_success:
            print("\n🎉 所有測試階段成功完成！論文復現第一階段 (1.1-1.3) 驗證通過。")
            sys.exit(0)
        else:
            print("\n❌ 部分測試階段失敗，請檢查詳細報告")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 測試執行過程中發生未預期錯誤: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # 檢查 Python 版本
    if sys.version_info < (3, 7):
        print("❌ 需要 Python 3.7 或更高版本")
        sys.exit(1)

    # 檢查是否在正確的目錄
    if not os.path.exists("/home/sat/ntn-stack/netstack"):
        print("❌ 請在 ntn-stack 根目錄執行此腳本")
        sys.exit(1)

    # 運行主函數
    asyncio.run(main())
