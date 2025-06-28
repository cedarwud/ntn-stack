#!/usr/bin/env python3
"""
NTN-Stack 統一測試執行器

一站式執行所有測試的入口程式，提供完整的測試控制和報告功能。

執行方式:
python run_all_tests.py [options]

選項:
--quick                快速模式（跳過耗時測試）
--type=TYPE           測試類型: unit,integration,performance,e2e,paper,gymnasium,all
--stage=STAGE         論文測試階段: 1,2,all
--env=ENV             Gymnasium環境: satellite,handover,all
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
from typing import Dict, List, Any
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedTestRunner:
    """統一測試執行器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_test_module(self, module_name: str, args: List[str] = None) -> bool:
        """執行測試模組"""
        logger.info(f"🧪 執行 {module_name}...")
        
        cmd = [sys.executable, f"{module_name}.py"]
        if args:
            cmd.extend(args)
            
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
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
    
    def run_unified_tests(self, test_type: str = "all", quick_mode: bool = False):
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
    
    def run_gymnasium_tests(self, env: str = "all", quick_mode: bool = False):
        """執行Gymnasium測試"""
        args = [f"--env={env}"]
        if quick_mode:
            args.append("--quick")
        return self.run_test_module("gymnasium_tests", args)
    
    def generate_report(self) -> str:
        """生成測試報告"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    NTN-Stack 測試報告                        ║
╠══════════════════════════════════════════════════════════════╣
║ 開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}                        ║
║ 結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}                        ║
║ 總耗時:   {total_duration:.2f} 秒                                  ║
╠══════════════════════════════════════════════════════════════╣
║ 測試統計:                                                    ║
║   總測試數: {self.total_tests:3d}                                     ║
║   通過數量: {self.passed_tests:3d}                                     ║
║   失敗數量: {self.failed_tests:3d}                                     ║
║   成功率:   {(self.passed_tests/max(self.total_tests,1)*100):6.1f}%                           ║
╠══════════════════════════════════════════════════════════════╣
║ 測試詳情:                                                    ║"""

        for module, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            report += f"\n║   {module:15s} {status} ({result['duration']:6.2f}s)       ║"
        
        report += f"""
╚══════════════════════════════════════════════════════════════╝
        """
        
        return report

def main():
    parser = argparse.ArgumentParser(description='NTN-Stack 統一測試執行器')
    parser.add_argument('--quick', action='store_true', help='快速模式')
    parser.add_argument('--type', choices=['unit', 'integration', 'performance', 'e2e', 'paper', 'gymnasium', 'all'], 
                       default='all', help='測試類型')
    parser.add_argument('--stage', choices=['1', '2', 'all'], default='all', help='論文測試階段')
    parser.add_argument('--env', choices=['satellite', 'handover', 'all'], default='all', help='Gymnasium環境')
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
    
    if args.type in ['all', 'gymnasium']:
        runner.run_gymnasium_tests(args.env, args.quick)
    
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
