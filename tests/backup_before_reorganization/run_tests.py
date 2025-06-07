#!/usr/bin/env python3
"""
測試執行腳本
統一的測試執行入口，支援不同類型的測試和報告生成
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path


def run_command(cmd, description=""):
    """執行命令並處理結果"""
    print(f"🔄 {description}")
    print(f"執行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} 完成")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗")
        print(f"錯誤輸出: {e.stderr}")
        return False, e.stderr


def main():
    parser = argparse.ArgumentParser(description="NTN Stack 測試執行器")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "performance", "all"],
        default="all",
        help="測試類型",
    )
    parser.add_argument("--module", help="特定模組 (netstack, simworld, deployment)")
    parser.add_argument("--html", action="store_true", help="生成 HTML 報告")
    parser.add_argument("--coverage", action="store_true", help="生成覆蓋率報告")
    parser.add_argument("--summary", action="store_true", help="生成測試摘要")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    # 確保報告目錄存在
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # 構建 pytest 命令
    cmd = ["python", "-m", "pytest"]

    # 添加測試路徑
    if args.type == "all":
        cmd.extend(["unit", "integration", "e2e", "performance"])
    else:
        cmd.append(args.type)

    if args.module:
        if args.type == "unit":
            cmd = ["python", "-m", "pytest", f"unit/{args.module}"]
        elif args.type == "integration":
            cmd = ["python", "-m", "pytest", f"integration"]

    # 添加選項
    if args.verbose:
        cmd.append("-v")

    # 生成時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # HTML 報告
    if args.html:
        html_file = f"reports/test_report_{timestamp}.html"
        cmd.extend(["--html", html_file, "--self-contained-html"])

    # 覆蓋率報告
    if args.coverage:
        cmd.extend(
            [
                "--cov=netstack",
                "--cov=simworld",
                "--cov=deployment",
                "--cov-report=html:reports/coverage/",
                "--cov-report=xml:reports/coverage.xml",
            ]
        )

    # JUnit XML 報告
    cmd.extend(["--junitxml", f"reports/junit_{timestamp}.xml"])

    # 執行測試
    success, output = run_command(cmd, f"執行 {args.type} 測試")

    if args.summary and success:
        # 生成測試摘要
        summary_cmd = ["python", "tools/test_summary.py"]
        run_command(summary_cmd, "生成測試摘要")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
