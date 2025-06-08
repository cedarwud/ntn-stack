#!/usr/bin/env python3
"""
統一測試運行器

單一入口點執行所有類型的測試
"""

import argparse
import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedTestRunner:
    """統一測試運行器"""
    
    def __init__(self, tests_root: Path):
        self.tests_root = Path(tests_root)
        
        # 測試套件定義
        self.test_suites = {
            "quick": {
                "description": "快速驗證測試 (5分鐘)",
                "timeout": 300,
                "includes": [
                    "unit/*/test_*.py",
                    "integration/api/test_*.py",
                    "e2e/scenarios/test_basic_functionality.py"
                ]
            },
            "integration": {
                "description": "整合測試 (15分鐘)",
                "timeout": 900,
                "includes": [
                    "integration/**/*.py",
                    "e2e/scenarios/test_essential_functionality.py"
                ]
            },
            "performance": {
                "description": "性能測試 (20分鐘)",
                "timeout": 1200,
                "includes": [
                    "performance/**/*.py"
                ]
            },
            "e2e": {
                "description": "端到端測試 (30分鐘)",
                "timeout": 1800,
                "includes": [
                    "e2e/**/*.py"
                ]
            },
            "stage_validation": {
                "description": "階段驗證測試 (25分鐘)",
                "timeout": 1500,
                "includes": [
                    "stage_validation/**/*.py"
                ]
            },
            "full": {
                "description": "完整測試套件 (60分鐘)",
                "timeout": 3600,
                "includes": [
                    "unit/**/*.py",
                    "integration/**/*.py",
                    "e2e/**/*.py",
                    "performance/**/*.py"
                ]
            }
        }
    
    def run_test_suite(self, suite_name: str) -> bool:
        """執行指定的測試套件"""
        if suite_name not in self.test_suites:
            logger.error(f"未知的測試套件: {suite_name}")
            return False
        
        suite = self.test_suites[suite_name]
        logger.info(f"🚀 執行測試套件: {suite_name}")
        logger.info(f"📋 描述: {suite['description']}")
        
        start_time = time.time()
        success = True
        
        try:
            for pattern in suite["includes"]:
                test_path = self.tests_root / pattern
                
                # 使用 pytest 執行測試
                cmd = [
                    sys.executable, "-m", "pytest",
                    str(test_path),
                    "-v",
                    "--tb=short"
                ]
                
                logger.info(f"▶️  執行: {pattern}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"❌ 測試失敗: {pattern}")
                    logger.error(result.stdout)
                    logger.error(result.stderr)
                    success = False
                else:
                    logger.info(f"✅ 測試通過: {pattern}")
        
        except Exception as e:
            logger.error(f"❌ 測試套件執行失敗: {e}")
            success = False
        
        duration = time.time() - start_time
        status = "通過" if success else "失敗"
        logger.info(f"🏁 測試套件 '{suite_name}' {status}，耗時: {duration:.2f}秒")
        
        return success
    
    def list_suites(self):
        """列出所有測試套件"""
        print("\n📋 可用的測試套件:")
        print("=" * 60)
        for name, suite in self.test_suites.items():
            print(f"{name:20} - {suite['description']}")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="統一測試運行器")
    parser.add_argument("suite", nargs="?", help="要執行的測試套件")
    parser.add_argument("--list", action="store_true", help="列出所有測試套件")
    parser.add_argument("--tests-root", default=".", help="測試根目錄")
    
    args = parser.parse_args()
    
    runner = UnifiedTestRunner(Path(args.tests_root))
    
    if args.list:
        runner.list_suites()
        return
    
    if not args.suite:
        print("❌ 請指定測試套件或使用 --list 查看可用選項")
        runner.list_suites()
        sys.exit(1)
    
    success = runner.run_test_suite(args.suite)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
