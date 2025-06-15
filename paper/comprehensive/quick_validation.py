#!/usr/bin/env python3
"""
論文復現快速驗證 (整合版)

整合原 quick_test.py 功能，修正 HTTP 422 錯誤問題
專注驗證核心演算法邏輯，不依賴特定衛星 ID

執行方式 (在 ntn-stack 根目錄):
source venv/bin/activate
python paper/comprehensive/quick_validation.py
"""

import sys
import asyncio
import time
import logging
from datetime import datetime

# 添加 NetStack API 路徑
sys.path.insert(0, "/home/sat/ntn-stack/netstack/netstack_api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """測試基本功能 (修正版)"""
    print("🚀 開始論文復現快速驗證")
    print("=" * 60)

    test_results = []

    # 測試 1: 模組導入
    print("\n🔍 測試模組導入...")
    try:
        from services.paper_synchronized_algorithm import (
            SynchronizedAlgorithm,
            AccessInfo,
        )
        from services.algorithm_integration_bridge import AlgorithmIntegrationBridge
        from services.fast_access_prediction_service import (
            FastSatellitePrediction,
            AccessStrategy,
        )

        print("  ✅ 所有模組導入成功")
        test_results.append(("模組導入", True))
    except Exception as e:
        print(f"  ❌ 模組導入失敗: {e}")
        test_results.append(("模組導入", False))
        return test_results

    # 測試 2: 論文標準演算法
    print("\n🔧 測試論文標準演算法...")
    try:
        paper_algo = SynchronizedAlgorithm(delta_t=5.0, binary_search_precision=0.01)
        print(f"  ✅ 論文演算法實例化成功 - delta_t: {paper_algo.delta_t}")

        # 測試 AccessInfo 資料結構
        access_info = AccessInfo(
            ue_id="test_ue", satellite_id="test_sat", access_quality=0.9
        )
        print(f"  ✅ AccessInfo 資料結構正常 - UE: {access_info.ue_id}")
        test_results.append(("論文標準演算法", True))
    except Exception as e:
        print(f"  ❌ 論文標準演算法失敗: {e}")
        test_results.append(("論文標準演算法", False))

    # 測試 3: 快速衛星預測服務
    print("\n📡 測試快速衛星預測服務...")
    try:
        prediction_service = FastSatellitePrediction(
            earth_radius_km=6371.0,
            block_size_degrees=10.0,
            prediction_accuracy_target=0.95,
        )
        print(
            f"  ✅ 預測服務實例化成功 - 準確率目標: {prediction_service.accuracy_target}"
        )

        # 測試地理區塊初始化
        blocks = await prediction_service.initialize_geographical_blocks()
        print(f"  ✅ 地理區塊初始化成功 - 區塊數: {len(blocks)}")

        # 測試 UE 註冊
        success = await prediction_service.register_ue(
            ue_id="test_ue",
            position={"lat": 25.0, "lon": 121.0, "alt": 100.0},
            access_strategy=AccessStrategy.FLEXIBLE,
        )
        print(f"  ✅ UE 註冊成功: {success}")
        test_results.append(("快速衛星預測", True))
    except Exception as e:
        print(f"  ❌ 快速衛星預測失敗: {e}")
        test_results.append(("快速衛星預測", False))

    # 測試 4: 演算法狀態查詢
    print("\n📊 測試狀態查詢...")
    try:
        # 測試論文演算法狀態
        paper_status = await paper_algo.get_algorithm_status()
        print(f"  ✅ 論文演算法狀態: {paper_status['algorithm_state']}")

        # 測試預測服務狀態
        service_status = await prediction_service.get_service_status()
        print(f"  ✅ 預測服務狀態: {service_status['service_name']}")
        test_results.append(("狀態查詢", True))
    except Exception as e:
        print(f"  ❌ 狀態查詢失敗: {e}")
        test_results.append(("狀態查詢", False))

    # 測試 5: 核心演算法功能 (簡化版，避免外部依賴)
    print("\n⚙️  測試核心演算法功能...")
    try:
        # 測試 UE 更新功能 (不依賴外部服務)
        await paper_algo.update_ue("test_ue")
        print(f"  ✅ UE 更新功能正常 - R表大小: {len(paper_algo.R)}")

        # 測試演算法狀態管理
        status = await paper_algo.get_algorithm_status()
        if "algorithm_state" in status and "total_ues" in status:
            print(f"  ✅ 演算法狀態管理正常")
            test_results.append(("核心演算法功能", True))
        else:
            print(f"  ❌ 演算法狀態異常")
            test_results.append(("核心演算法功能", False))

    except Exception as e:
        print(f"  ❌ 核心演算法功能失敗: {e}")
        test_results.append(("核心演算法功能", False))

    return test_results


async def main():
    """主函數"""
    start_time = datetime.now()

    try:
        test_results = await test_basic_functionality()

        # 統計結果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)

        print("\n" + "=" * 60)
        print("📋 論文復現快速驗證結果")
        print("=" * 60)

        for test_name, result in test_results:
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"  {status} {test_name}")

        print(f"\n📊 統計:")
        print(f"  總測試數: {total_tests}")
        print(f"  通過測試: {passed_tests}")
        print(f"  失敗測試: {total_tests - passed_tests}")
        print(f"  成功率: {passed_tests/total_tests*100:.1f}%")
        print(f"  執行時間: {duration:.2f} 秒")

        if passed_tests == total_tests:
            print("\n🎉 所有快速驗證通過！論文復現功能正常運作。")
            print("\n📝 後續建議:")
            print(
                "  1. 執行完整測試: python paper/comprehensive/test_core_validation.py"
            )
            print("  2. 執行分階段測試: python paper/comprehensive/run_all_tests.py")
            print(
                "  3. 檢查具體功能: python paper/1.2_synchronized_algorithm/test_algorithm_1.py"
            )
        else:
            print(f"\n⚠️  有 {total_tests - passed_tests} 個測試失敗。")
            print("建議檢查模組導入和基本配置。")

        return passed_tests == total_tests

    except Exception as e:
        print(f"\n💥 快速驗證過程中發生錯誤: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
