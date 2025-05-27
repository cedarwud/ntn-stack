#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NTN Stack 整合測試腳本
此腳本負責測試 NTN 堆棧的各個組件的整合情況
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Any

import requests

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


class NTNStackTester:
    """NTN 堆棧測試器"""

    def __init__(self, netstack_url: str, simworld_url: str):
        """初始化測試器"""
        self.netstack_url = netstack_url
        self.simworld_url = simworld_url
        self.results = {
            "success": True,
            "tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0},
        }

    def run_all_tests(self) -> Dict:
        """運行所有測試"""
        self._test_netstack_health()
        self._test_simworld_health()
        
        # 更新總結
        self.results["summary"]["total"] = len(self.results["tests"])
        self.results["summary"]["passed"] = sum(
            1 for test in self.results["tests"] if test["success"]
        )
        self.results["summary"]["failed"] = sum(
            1 for test in self.results["tests"] if not test["success"]
        )
        
        # 如果有任何測試失敗，整體測試失敗
        self.results["success"] = self.results["summary"]["failed"] == 0
        
        return self.results

    def _test_netstack_health(self) -> None:
        """測試 NetStack 健康狀況"""
        log.info("測試 NetStack 健康狀況...")
        try:
            response = requests.get(f"{self.netstack_url}/health", timeout=10)
            success = response.status_code == 200
            self.results["tests"].append(
                {
                    "name": "netstack_health",
                    "success": success,
                    "message": "NetStack 健康檢查成功" if success else "NetStack 健康檢查失敗",
                    "status_code": response.status_code,
                    "response": response.json() if success else {},
                }
            )
            log.info(
                f"NetStack 健康檢查: {'成功' if success else '失敗'} ({response.status_code})"
            )
        except Exception as e:
            self.results["tests"].append(
                {
                    "name": "netstack_health",
                    "success": False,
                    "message": f"NetStack 健康檢查失敗: {str(e)}",
                    "error": str(e),
                }
            )
            log.error(f"NetStack 健康檢查錯誤: {e}")

    def _test_simworld_health(self) -> None:
        """測試 SimWorld 健康狀況"""
        log.info("測試 SimWorld 健康狀況...")
        try:
            response = requests.get(f"{self.simworld_url}/health", timeout=10)
            success = response.status_code == 200
            self.results["tests"].append(
                {
                    "name": "simworld_health",
                    "success": success,
                    "message": "SimWorld 健康檢查成功" if success else "SimWorld 健康檢查失敗",
                    "status_code": response.status_code,
                    "response": response.json() if success else {},
                }
            )
            log.info(
                f"SimWorld 健康檢查: {'成功' if success else '失敗'} ({response.status_code})"
            )
        except Exception as e:
            self.results["tests"].append(
                {
                    "name": "simworld_health",
                    "success": False,
                    "message": f"SimWorld 健康檢查失敗: {str(e)}",
                    "error": str(e),
                }
            )
            log.error(f"SimWorld 健康檢查錯誤: {e}")


def parse_args() -> argparse.Namespace:
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="NTN Stack 整合測試")
    parser.add_argument(
        "--netstack-url",
        default=os.environ.get("NETSTACK_URL", "http://localhost:8080"),
        help="NetStack API URL",
    )
    parser.add_argument(
        "--simworld-url",
        default=os.environ.get("SIMWORLD_URL", "http://localhost:8000"),
        help="SimWorld API URL",
    )
    parser.add_argument(
        "--output",
        default="integration_report.json",
        help="輸出報告檔案",
    )
    return parser.parse_args()


def main() -> None:
    """主函數"""
    args = parse_args()
    log.info(f"開始 NTN Stack 整合測試")
    log.info(f"NetStack URL: {args.netstack_url}")
    log.info(f"SimWorld URL: {args.simworld_url}")

    # 執行測試
    tester = NTNStackTester(args.netstack_url, args.simworld_url)
    results = tester.run_all_tests()

    # 保存結果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log.info(f"測試完成. 結果已保存至 {args.output}")
    log.info(
        f"總結: 總計 {results['summary']['total']} 測試, "
        f"通過 {results['summary']['passed']}, "
        f"失敗 {results['summary']['failed']}"
    )

    # 如果測試失敗，退出代碼非 0
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
