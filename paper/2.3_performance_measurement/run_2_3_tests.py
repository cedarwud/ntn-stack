#!/usr/bin/env python3
"""
階段二 2.3 論文標準效能測量框架測試執行器

執行方式:
cd /home/sat/ntn-stack
source venv/bin/activate
python paper/2.3_performance_measurement/run_2_3_tests.py
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
from test_performance_measurement import main as run_performance_tests


def print_header():
    """打印測試標題"""
    print("=" * 80)
    print("🚀 階段二 2.3 論文標準效能測量框架測試執行器")
    print("=" * 80)
    print("📊 支援四種方案對比測試與論文標準分析")
    print("🎯 目標：HandoverMeasurement 服務驗證、CDF 曲線生成、數據匯出")
    print("-" * 80)


def print_test_info():
    """打印測試資訊"""
    print("\n📋 測試項目概覽:")
    print("  1. HandoverMeasurement 服務測試")
    print("     - 事件記錄完整性驗證")
    print("     - 數據結構正確性檢查")
    print("     - 延遲值合理性測試")
    print("     - 方案差異化驗證")
    print()
    print("  2. 四種方案對比測試")
    print("     - NTN Baseline (~250ms)")
    print("     - NTN-GS (~153ms)")
    print("     - NTN-SMN (~158.5ms)")
    print("     - Proposed (~25ms)")
    print()
    print("  3. CDF 曲線生成測試")
    print("     - 報告生成驗證")
    print("     - 統計數據有效性")
    print("     - CDF 文件生成")
    print()
    print("  4. 論文標準數據匯出測試")
    print("     - JSON 格式匯出")
    print("     - CSV 格式匯出")
    print("     - 數據完整性檢查")
    print()


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="階段二 2.3 論文標準效能測量框架測試執行器")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    parser.add_argument("--quick", "-q", action="store_true", help="快速測試模式")
    
    args = parser.parse_args()
    
    print_header()
    
    if not args.quick:
        print_test_info()
    
    print("⏳ 正在啟動測試...")
    print()
    
    try:
        # 執行測試
        success = await run_performance_tests()
        
        print("\n" + "=" * 80)
        if success:
            print("🎉 階段二 2.3 論文標準效能測量框架測試完成！")
            print("✨ 所有測試項目均成功通過")
            return 0
        else:
            print("❌ 階段二 2.3 測試未完全通過")
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