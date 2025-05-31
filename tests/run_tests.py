#!/usr/bin/env python3
"""
NTN Stack 測試執行腳本
提供簡單的命令行介面來執行不同類型的測試
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """執行命令並顯示結果"""
    print(f"\n🚀 {description}")
    print(f"執行命令: {cmd}")
    print("-" * 50)

    result = subprocess.run(cmd, shell=True, capture_output=False)

    if result.returncode == 0:
        print(f"✅ {description} 完成")
    else:
        print(f"❌ {description} 失敗 (退出碼: {result.returncode})")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="NTN Stack 測試執行器")
    parser.add_argument(
        "--type",
        "-t",
        choices=["unit", "integration", "e2e", "api", "performance", "all", "smoke"],
        default="all",
        help="測試類型 (預設: all)",
    )
    parser.add_argument(
        "--module",
        "-m",
        choices=["netstack", "simworld", "deployment", "all"],
        default="all",
        help="測試模組 (預設: all)",
    )
    parser.add_argument("--coverage", "-c", action="store_true", help="生成覆蓋率報告")
    parser.add_argument("--html", action="store_true", help="生成 HTML 報告")
    parser.add_argument("--summary", "-s", action="store_true", help="顯示測試摘要")

    args = parser.parse_args()

    # 確保在正確的目錄
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    # 構建測試命令
    cmd_parts = ["python", "-m", "pytest"]

    # 選擇測試路徑
    if args.type == "unit":
        if args.module == "all":
            cmd_parts.append("unit/")
        else:
            cmd_parts.append(f"unit/{args.module}/")
    elif args.type == "integration":
        cmd_parts.append("integration/")
    elif args.type == "e2e":
        cmd_parts.append("e2e/")
    elif args.type == "api":
        cmd_parts.append("api/")
    elif args.type == "performance":
        cmd_parts.append("performance/")
    elif args.type == "smoke":
        cmd_parts.extend(["-m", "smoke"])
    else:  # all
        if args.module == "all":
            cmd_parts.extend(["unit/", "integration/", "e2e/", "api/", "performance/"])
        else:
            cmd_parts.append(f"unit/{args.module}/")

    # 添加選項
    cmd_parts.extend(["-v", "--tb=short"])

    if args.coverage:
        cmd_parts.extend(["--cov=."])

    if args.html:
        timestamp = subprocess.check_output(["date", "+%Y%m%d_%H%M%S"]).decode().strip()
        report_name = f"test_report_{timestamp}.html"
        cmd_parts.extend(["--html", f"reports/test_results/{report_name}"])

    # 總是生成 JUnit XML
    cmd_parts.extend(["--junitxml", "reports/test_results/junit.xml"])

    # 執行測試
    cmd = " ".join(cmd_parts)
    exit_code = run_command(cmd, f"執行 {args.type} 測試")

    # 顯示摘要
    if args.summary or exit_code == 0:
        print("\n" + "=" * 60)
        summary_cmd = "python tools/test_summary.py"
        run_command(summary_cmd, "生成測試摘要")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
