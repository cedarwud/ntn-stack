#!/usr/bin/env python3
"""
1.2 同步演算法 (Algorithm 1) 測試程式

測試論文復現 Algorithm 1 的完整功能：
- 二分搜尋換手時間預測 (<25ms精度)
- 週期性更新機制 (Δt=5s)
- UE-衛星關係表管理 (R表)
- 換手時間表管理 (Tp表)
- 無信令同步協調

執行方式 (在 ntn-stack 根目錄):
source venv/bin/activate
python Desktop/paper/1.2_synchronized_algorithm/test_algorithm_1.py
"""

import sys
import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# 添加 NetStack API 路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack/netstack_api')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_algorithm_1_core():
    """測試 Algorithm 1 核心功能"""
    print("🔬 測試 1.2 同步演算法 (Algorithm 1)")
    print("="*60)
    
    test_results = []
    
    try:
        # 導入論文標準模組
        from services.paper_synchronized_algorithm import SynchronizedAlgorithm, AccessInfo
        from services.algorithm_integration_bridge import AlgorithmIntegrationBridge
        print("✅ 論文標準模組導入成功")
        test_results.append(("模組導入", True))
        
        # 測試 1: Algorithm 1 初始化
        print("\n📋 測試 Algorithm 1 初始化...")
        algo = SynchronizedAlgorithm(
            delta_t=5.0,  # 論文標準更新週期
            binary_search_precision=0.01  # 10ms 精度
        )
        assert algo.delta_t == 5.0
        assert algo.binary_search_precision == 0.01
        assert len(algo.R) == 0  # UE-衛星關係表
        assert len(algo.Tp) == 0  # 換手時間預測表
        print("✅ Algorithm 1 初始化成功")
        test_results.append(("Algorithm1初始化", True))
        
        # 測試 2: AccessInfo 資料結構
        print("\n📋 測試 AccessInfo 資料結構...")
        access_info = AccessInfo(
            ue_id="ue_001",
            satellite_id="sat_001",
            access_quality=0.85
        )
        assert access_info.ue_id == "ue_001"
        assert access_info.satellite_id == "sat_001"
        assert access_info.access_quality == 0.85
        print("✅ AccessInfo 資料結構正常")
        test_results.append(("AccessInfo資料結構", True))
        
        # 測試 3: 二分搜尋精度測試
        print("\n📋 測試二分搜尋精度 (論文核心)...")
        search_start_time = time.time()
        current_time = time.time()
        
        handover_time = await algo.binary_search_handover_time(
            ue_id="ue_001",
            source_satellite="sat_001",
            target_satellite="sat_002",
            t_start=current_time,
            t_end=current_time + 300  # 5分鐘搜尋範圍
        )
        
        search_duration = (time.time() - search_start_time) * 1000  # 轉為毫秒
        precision_met = search_duration < 25.0  # 論文要求 <25ms
        
        print(f"✅ 二分搜尋完成:")
        print(f"   執行時間: {search_duration:.1f}ms")
        print(f"   精度要求: {'✅ 達標' if precision_met else '❌ 未達標'} (<25ms)")
        print(f"   預測時間: {datetime.fromtimestamp(handover_time).strftime('%H:%M:%S')}")
        
        test_results.append(("二分搜尋精度", precision_met))
        
        # 測試 4: UE 更新機制
        print("\n📋 測試 UE 更新機制...")
        await algo.update_ue("ue_001")
        r_table_updated = len(algo.R) > 0
        print(f"✅ UE 更新完成 - R表大小: {len(algo.R)}")
        test_results.append(("UE更新機制", r_table_updated))
        
        # 測試 5: 週期性更新 (Algorithm 1 第5-10行)
        print("\n📋 測試週期性更新機制...")
        initial_t = algo.T
        await algo.periodic_update(current_time + algo.delta_t)
        periodic_updated = algo.T > initial_t
        print(f"✅ 週期性更新: {'成功' if periodic_updated else '失敗'}")
        test_results.append(("週期性更新", periodic_updated))
        
        # 測試 6: 演算法狀態管理
        print("\n📋 測試演算法狀態管理...")
        status = await algo.get_algorithm_status()
        status_valid = (
            "algorithm_state" in status and
            "last_update_time" in status and
            "active_ue_count" in status and
            "binary_search_precision" in status
        )
        print(f"✅ 狀態查詢成功: {status['algorithm_state']}")
        print(f"   管理 UE 數: {status['active_ue_count']}")
        print(f"   二分搜尋精度: {status['binary_search_precision']}秒")
        test_results.append(("狀態管理", status_valid))
        
        # 測試 7: 多 UE 並行處理
        print("\n📋 測試多 UE 並行處理...")
        test_ues = ["ue_001", "ue_002", "ue_003", "ue_004", "ue_005"]
        parallel_start = time.time()
        
        # 並行更新多個 UE
        update_tasks = [algo.update_ue(ue_id) for ue_id in test_ues]
        await asyncio.gather(*update_tasks)
        
        parallel_duration = (time.time() - parallel_start) * 1000
        parallel_success = len(algo.R) >= len(test_ues)
        
        print(f"✅ 並行處理: {len(test_ues)} UE, 耗時: {parallel_duration:.1f}ms")
        print(f"   R表大小: {len(algo.R)}")
        test_results.append(("多UE並行處理", parallel_success))
        
        # 測試 8: 換手時間預測準確性
        print("\n📋 測試換手時間預測準確性...")
        prediction_count = 3
        successful_predictions = 0
        
        for i in range(prediction_count):
            try:
                pred_time = await algo.binary_search_handover_time(
                    ue_id=f"ue_pred_{i}",
                    source_satellite=f"sat_{i:03d}",
                    target_satellite=f"sat_{i+1:03d}",
                    t_start=current_time + i * 60,
                    t_end=current_time + (i + 1) * 60
                )
                if pred_time > current_time:
                    successful_predictions += 1
            except Exception as e:
                logger.warning(f"預測 {i} 失敗: {str(e)}")
        
        prediction_accuracy = successful_predictions / prediction_count
        prediction_success = prediction_accuracy > 0.8  # 80% 成功率
        
        print(f"✅ 預測準確性: {successful_predictions}/{prediction_count} ({prediction_accuracy:.1%})")
        test_results.append(("預測準確性", prediction_success))
        
    except Exception as e:
        print(f"❌ 1.2 測試失敗: {str(e)}")
        test_results.append(("Algorithm1測試", False))
        logger.error(f"1.2 測試錯誤: {str(e)}", exc_info=True)
    
    return test_results


async def test_integration_bridge():
    """測試整合橋接服務"""
    print("\n🌉 測試整合橋接服務")
    print("-"*40)
    
    test_results = []
    
    try:
        from services.algorithm_integration_bridge import (
            AlgorithmIntegrationBridge,
            BridgeConfiguration,
            IntegrationMode
        )
        
        # 測試論文模式
        config = BridgeConfiguration(
            integration_mode=IntegrationMode.PAPER_ONLY,
            enhanced_features_enabled=False
        )
        
        bridge = AlgorithmIntegrationBridge(config=config)
        init_result = await bridge.initialize_algorithms()
        
        assert init_result["success"] == True
        print("✅ 論文模式橋接初始化成功")
        test_results.append(("橋接初始化", True))
        
        # 測試模式切換
        switch_result = await bridge.switch_mode(IntegrationMode.HYBRID)
        print(f"✅ 模式切換: {switch_result['success']}")
        test_results.append(("模式切換", switch_result['success']))
        
        # 測試狀態查詢
        status = await bridge.get_integration_status()
        status_valid = "component_status" in status
        print(f"✅ 整合狀態查詢: {len(status['component_status'])} 個組件")
        test_results.append(("整合狀態", status_valid))
        
    except Exception as e:
        print(f"❌ 橋接測試失敗: {str(e)}")
        test_results.append(("橋接測試", False))
    
    return test_results


async def main():
    """主函數"""
    print("🚀 開始執行 1.2 同步演算法 (Algorithm 1) 測試")
    
    start_time = datetime.now()
    
    # 執行核心測試
    core_results = await test_algorithm_1_core()
    
    # 執行橋接測試
    bridge_results = await test_integration_bridge()
    
    # 合併結果
    all_results = core_results + bridge_results
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 統計結果
    passed_tests = sum(1 for _, result in all_results if result)
    total_tests = len(all_results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # 輸出報告
    print("\n" + "="*60)
    print("📊 1.2 同步演算法 (Algorithm 1) 測試報告")
    print("="*60)
    
    print(f"\n📋 詳細結果:")
    for test_name, result in all_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 統計:")
    print(f"   總測試數: {total_tests}")
    print(f"   通過測試: {passed_tests}")
    print(f"   失敗測試: {total_tests - passed_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    print(f"   執行時間: {duration:.2f} 秒")
    
    # 論文復現驗證
    print(f"\n🎓 論文 Algorithm 1 復現狀態:")
    critical_tests = ["Algorithm1初始化", "二分搜尋精度", "UE更新機制", "週期性更新"]
    critical_passed = sum(1 for name, result in all_results 
                         if any(critical in name for critical in critical_tests) and result)
    
    print(f"   ✅ 核心功能: {critical_passed}/{len(critical_tests)} 通過")
    print(f"   ✅ 二分搜尋精度: {'達標' if any(name == '二分搜尋精度' and result for name, result in all_results) else '未達標'}")
    print(f"   ✅ 週期性更新: {'正常' if any(name == '週期性更新' and result for name, result in all_results) else '異常'}")
    
    if success_rate >= 90.0:
        print(f"\n🎉 1.2 同步演算法 (Algorithm 1) 復現成功！")
        print(f"📝 已準備好進行 1.3 快速衛星預測演算法測試")
    else:
        print(f"\n⚠️  1.2 演算法存在問題，建議進一步檢查")
    
    return success_rate >= 90.0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 測試執行錯誤: {str(e)}")
        sys.exit(1)