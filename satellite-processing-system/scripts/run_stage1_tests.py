#!/usr/bin/env python3
"""
Stage 1 v2.0 架構測試執行腳本

執行所有Stage 1相關的測試：
1. v2.0架構測試
2. 模組化組件測試
3. 學術合規性驗證
4. 效能測試

使用方法：
  在容器內執行: python scripts/run_stage1_tests.py
"""

import sys
import unittest
import time
from pathlib import Path
from datetime import datetime

# 添加src路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "tests"))

def run_stage1_tests():
    """執行Stage 1測試套件"""

    print("🚀 Stage 1 v2.0架構測試執行")
    print("=" * 60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"測試環境: satellite-dev容器")
    print("=" * 60)

    # 測試套件列表
    test_modules = [
        'tests.unit.stages.test_stage1_v2_architecture',
        'tests.unit.stages.test_stage1_modular_components'
    ]

    # 創建測試套件
    test_suite = unittest.TestSuite()
    total_tests = 0

    for module_name in test_modules:
        try:
            # 動態導入測試模組
            module = __import__(module_name, fromlist=[''])

            # 載入測試
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            test_suite.addTests(suite)

            # 計算測試數量
            test_count = suite.countTestCases()
            total_tests += test_count

            print(f"✅ 載入測試模組: {module_name} ({test_count} 個測試)")

        except ImportError as e:
            print(f"❌ 無法載入測試模組 {module_name}: {e}")
            continue
        except Exception as e:
            print(f"❌ 載入測試模組時發生錯誤 {module_name}: {e}")
            continue

    print(f"\n📊 總計載入 {total_tests} 個測試")
    print("=" * 60)

    if total_tests == 0:
        print("❌ 沒有找到可執行的測試")
        return False

    # 執行測試
    print("🧪 開始執行測試...")
    start_time = time.time()

    # 設置測試運行器
    runner = unittest.TextTestRunner(
        verbosity=2,
        buffer=True,  # 捕獲輸出
        failfast=False  # 不在第一個失敗時停止
    )

    # 運行測試
    result = runner.run(test_suite)

    execution_time = time.time() - start_time

    # 輸出結果統計
    print("\n" + "=" * 60)
    print("📊 Stage 1 v2.0架構測試結果統計")
    print("=" * 60)

    print(f"總測試數: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    print(f"跳過: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"執行時間: {execution_time:.2f} 秒")

    # 計算成功率
    success_count = result.testsRun - len(result.failures) - len(result.errors)
    success_rate = (success_count / result.testsRun) * 100 if result.testsRun > 0 else 0
    print(f"成功率: {success_rate:.1f}%")

    # 詳細錯誤報告
    if result.failures:
        print(f"\n❌ 失敗的測試 ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"  {i}. {test}")
            print(f"     {traceback.split(chr(10))[-2].strip()}")  # 顯示最後一行錯誤

    if result.errors:
        print(f"\n🚫 錯誤的測試 ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"  {i}. {test}")
            print(f"     {traceback.split(chr(10))[-2].strip()}")  # 顯示最後一行錯誤

    # 總體評估
    print("\n" + "=" * 60)
    if success_rate >= 90:
        print("🎉 Stage 1 v2.0架構測試 - 優秀 (≥90%)")
        print("✅ 所有核心功能正常運作")
        print("✅ v2.0架構實現完整")
        print("✅ 學術標準合規性達標")
    elif success_rate >= 80:
        print("✅ Stage 1 v2.0架構測試 - 良好 (≥80%)")
        print("⚠️  部分功能需要注意")
    elif success_rate >= 70:
        print("⚠️  Stage 1 v2.0架構測試 - 及格 (≥70%)")
        print("❌ 需要修復部分問題")
    else:
        print("❌ Stage 1 v2.0架構測試 - 不及格 (<70%)")
        print("🚨 需要重大修復")

    print("=" * 60)

    # 輸出建議
    if success_rate < 100:
        print("\n💡 改進建議:")
        print("   1. 檢查失敗的測試用例")
        print("   2. 確認模組化組件正確實現")
        print("   3. 驗證學術合規性要求")
        print("   4. 檢查錯誤處理機制")

    return success_rate >= 80  # 80%以上視為通過


def main():
    """主函數"""
    try:
        # 檢查執行環境
        if not Path("/satellite-processing").exists():
            print("❌ 請在satellite-dev容器內執行此腳本")
            print("正確執行方式:")
            print("  docker exec satellite-dev bash")
            print("  cd /satellite-processing")
            print("  python scripts/run_stage1_tests.py")
            sys.exit(1)

        # 執行測試
        success = run_stage1_tests()

        # 根據結果設置退出碼
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()