#!/usr/bin/env python3
"""
階段二 2.4 多方案測試支援測試執行器

執行方式:
cd /home/sat/ntn-stack
source venv/bin/activate
python paper/2.4_multi_scheme_support/run_2_4_tests.py
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "netstack"))

# 導入測試模組
sys.path.insert(0, str(Path(__file__).parent))
from test_multi_scheme_support import main as run_multi_scheme_tests


def print_header():
    """打印測試標題"""
    print("=" * 80)
    print("🚀 階段二 2.4 多方案測試支援測試執行器")
    print("=" * 80)
    print("🎯 支援四種切換方案的完整測試框架")
    print("📊 目標：方案初始化、差異化、切換、效能隔離驗證")
    print("-" * 80)


def print_test_info():
    """打印測試資訊"""
    print("\n📋 測試項目概覽:")
    print("  1. 方案初始化功能測試")
    print("     - 方案枚舉完整性驗證")
    print("     - 方案值正確性檢查")
    print("     - 測量服務方案支援驗證")
    print("     - 方案特性定義驗證")
    print()
    print("  2. 方案差異化功能測試")
    print("     - 事件生成完整性測試")
    print("     - 方案分佈均勻性驗證")
    print("     - 延遲差異化正確性檢查")
    print("     - 方案延遲範圍合理性測試")
    print()
    print("  3. 方案切換功能測試")
    print("     - 運行時方案切換測試")
    print("     - 切換序列完整性驗證")
    print("     - 切換延遲一致性檢查")
    print("     - 切換效率測試")
    print()
    print("  4. 方案效能隔離測試")
    print("     - 並行執行完整性測試")
    print("     - 方案隔離性驗證")
    print("     - 效能隔離正確性檢查")
    print("     - 並行執行效率測試")
    print()


def print_scheme_overview():
    """打印方案概覽"""
    print("🎛️  支援的切換方案:")
    print("   1. NTN Baseline  - 3GPP 標準 (~250ms)")
    print("   2. NTN-GS        - 地面站協助 (~153ms)")
    print("   3. NTN-SMN       - 衛星網路內 (~158.5ms)")
    print("   4. Proposed      - 本論文方案 (~25ms)")
    print()


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="階段二 2.4 多方案測試支援測試執行器")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    parser.add_argument("--quick", "-q", action="store_true", help="快速測試模式")
    parser.add_argument("--scheme", "-s", choices=["ntn", "ntn-gs", "ntn-smn", "proposed", "all"], 
                       default="all", help="測試特定方案")
    
    args = parser.parse_args()
    
    print_header()
    print_scheme_overview()
    
    if not args.quick:
        print_test_info()
    
    print("⏳ 正在啟動多方案測試支援測試...")
    print()
    
    try:
        # 執行測試
        success = await run_multi_scheme_tests()
        
        print("\n" + "=" * 80)
        if success:
            print("🎉 階段二 2.4 多方案測試支援測試完成！")
            print("✨ 四種切換方案測試框架驗證成功")
            print("📊 所有方案均支援完整的測試功能")
            return 0
        else:
            print("❌ 階段二 2.4 測試未完全通過")
            print("💡 請檢查測試日誌並修復失敗項目")
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        return 130
    
    except Exception as e:
        print(f"\n💥 測試執行出現異常: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"程式執行失敗: {e}")
        sys.exit(1)