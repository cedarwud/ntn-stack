#!/usr/bin/env python3
"""
NTN Stack 測試摘要工具
生成測試執行摘要和統計資訊
"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def parse_junit_xml(xml_path):
    """解析 JUnit XML 報告"""
    if not os.path.exists(xml_path):
        return None

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 查找 testsuite 元素
    testsuite = root.find(".//testsuite")
    if testsuite is None:
        return None

    # 獲取測試統計
    total_tests = int(testsuite.get("tests", 0))
    failures = int(testsuite.get("failures", 0))
    errors = int(testsuite.get("errors", 0))
    skipped = int(testsuite.get("skipped", 0))
    time = float(testsuite.get("time", 0))

    passed = total_tests - failures - errors - skipped

    # 獲取測試案例詳情
    test_cases = []
    for testcase in testsuite.findall(".//testcase"):
        case_info = {
            "name": testcase.get("name"),
            "classname": testcase.get("classname"),
            "time": float(testcase.get("time", 0)),
            "status": "passed",
        }

        if testcase.find("failure") is not None:
            case_info["status"] = "failed"
            case_info["failure"] = testcase.find("failure").text
        elif testcase.find("error") is not None:
            case_info["status"] = "error"
            case_info["error"] = testcase.find("error").text
        elif testcase.find("skipped") is not None:
            case_info["status"] = "skipped"
            case_info["skipped"] = testcase.find("skipped").text

        test_cases.append(case_info)

    return {
        "total": total_tests,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "execution_time": time,
        "test_cases": test_cases,
    }


def get_coverage_info(reports_dir):
    """獲取覆蓋率資訊"""
    coverage_file = os.path.join(reports_dir, "coverage", "coverage.xml")
    if not os.path.exists(coverage_file):
        return None

    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()

        # 獲取總體覆蓋率
        coverage_elem = root.find(".//coverage")
        if coverage_elem is not None:
            line_rate = float(coverage_elem.get("line-rate", 0)) * 100
            branch_rate = float(coverage_elem.get("branch-rate", 0)) * 100

            return {
                "line_coverage": round(line_rate, 2),
                "branch_coverage": round(branch_rate, 2),
            }
    except Exception as e:
        print(f"解析覆蓋率報告時出錯: {e}")

    return None


def generate_summary_report():
    """生成測試摘要報告"""
    reports_dir = Path(__file__).parent.parent / "reports"
    test_results_dir = reports_dir / "test_results"

    # 解析 JUnit XML
    junit_path = test_results_dir / "junit.xml"
    junit_data = parse_junit_xml(junit_path)

    # 獲取覆蓋率資訊
    coverage_data = get_coverage_info(reports_dir)

    # 生成摘要
    summary = {
        "timestamp": datetime.now().isoformat(),
        "test_execution": junit_data,
        "coverage": coverage_data,
        "reports": {
            "html_reports": list(test_results_dir.glob("*.html")),
            "junit_xml": junit_path if junit_path.exists() else None,
        },
    }

    return summary


def print_summary(summary):
    """列印測試摘要"""
    print("=" * 60)
    print("🧪 NTN Stack 測試執行摘要")
    print("=" * 60)
    print(f"📅 執行時間: {summary['timestamp']}")
    print()

    if summary["test_execution"]:
        test_data = summary["test_execution"]
        print("📊 測試統計:")
        print(f"   總測試數: {test_data['total']}")
        print(f"   ✅ 通過: {test_data['passed']}")
        print(f"   ❌ 失敗: {test_data['failed']}")
        print(f"   🚫 錯誤: {test_data['errors']}")
        print(f"   ⏭️  跳過: {test_data['skipped']}")
        print(f"   ⏱️  執行時間: {test_data['execution_time']:.2f}秒")

        success_rate = (
            (test_data["passed"] / test_data["total"]) * 100
            if test_data["total"] > 0
            else 0
        )
        print(f"   📈 成功率: {success_rate:.1f}%")
        print()

    if summary["coverage"]:
        coverage_data = summary["coverage"]
        print("📋 程式碼覆蓋率:")
        print(f"   行覆蓋率: {coverage_data['line_coverage']}%")
        print(f"   分支覆蓋率: {coverage_data['branch_coverage']}%")
        print()

    print("📄 生成的報告:")
    if summary["reports"]["html_reports"]:
        for report in summary["reports"]["html_reports"]:
            print(f"   📊 {report.name}")

    if summary["reports"]["junit_xml"]:
        print(f"   📋 junit.xml")

    print()
    print("📁 報告位置: tests/reports/test_results/")
    print("=" * 60)


def save_summary_json(summary):
    """儲存摘要為 JSON 檔案"""
    reports_dir = Path(__file__).parent.parent / "reports"
    summary_file = reports_dir / "test_summary.json"

    # 轉換 Path 物件為字串以便 JSON 序列化
    json_summary = summary.copy()
    if json_summary["reports"]["html_reports"]:
        json_summary["reports"]["html_reports"] = [
            str(p.name) for p in json_summary["reports"]["html_reports"]
        ]
    if json_summary["reports"]["junit_xml"]:
        json_summary["reports"]["junit_xml"] = str(
            json_summary["reports"]["junit_xml"].name
        )

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, indent=2, ensure_ascii=False)

    print(f"📄 測試摘要已儲存至: {summary_file}")


if __name__ == "__main__":
    try:
        summary = generate_summary_report()
        print_summary(summary)
        save_summary_json(summary)

        # 根據測試結果設定退出碼
        if summary["test_execution"]:
            test_data = summary["test_execution"]
            if test_data["failed"] > 0 or test_data["errors"] > 0:
                exit(1)  # 有失敗或錯誤

        exit(0)  # 成功

    except Exception as e:
        print(f"❌ 生成測試摘要時出錯: {e}")
        exit(1)
