"""
Fine-Grained Synchronized Algorithm Integration Tests

測試論文中實現的細粒度同步算法，驗證：
1. 二點預測方法的準確性
2. Binary search refinement 的收斂性
3. 無信令同步機制的有效性
4. 預測誤差是否達到論文要求 (<50ms)
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加 netstack 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../netstack'))

from netstack_api.services.fine_grained_sync_service import (
    FineGrainedSyncService,
    SatelliteAccessPrediction,
    SynchronizationPoint,
    BinarySearchState,
    SyncState,
    PredictionAccuracy
)


class TestFineGrainedSyncIntegration:
    """細粒度同步算法整合測試"""

    @pytest.fixture
    async def sync_service(self):
        """創建同步服務實例"""
        service = FineGrainedSyncService()
        await service.start_sync_service()
        yield service
        await service.stop_sync_service()

    @pytest.mark.asyncio
    async def test_two_point_prediction_method(self, sync_service):
        """測試二點預測方法"""
        print("\n=== 測試二點預測方法 ===")
        
        ue_id = "test_ue_001"
        satellite_id = "oneweb_001"
        
        # 執行衛星接入預測
        prediction = await sync_service.predict_satellite_access(
            ue_id=ue_id,
            satellite_id=satellite_id,
            time_horizon_minutes=30.0
        )
        
        # 驗證預測結果
        assert isinstance(prediction, SatelliteAccessPrediction)
        assert prediction.ue_id == ue_id
        assert prediction.satellite_id == satellite_id
        
        # 驗證二點預測
        assert prediction.prediction_time_t is not None
        assert prediction.prediction_time_t_delta is not None
        time_delta = (prediction.prediction_time_t_delta - prediction.prediction_time_t).total_seconds()
        expected_delta = 2 * 60  # 2分鐘（根據修正的參數）
        assert abs(time_delta - expected_delta) < 10  # 允許10秒誤差
        
        # 驗證預測結果合理性
        assert prediction.confidence_score >= 0.0
        assert prediction.confidence_score <= 1.0
        assert prediction.predicted_access_time > datetime.now()
        
        print(f"✓ 二點預測完成")
        print(f"  - 預測時間 T: {prediction.prediction_time_t}")
        print(f"  - 預測時間 T+Δt: {prediction.prediction_time_t_delta}")
        print(f"  - 預測接入時間: {prediction.predicted_access_time}")
        print(f"  - 信心度: {prediction.confidence_score:.3f}")

    @pytest.mark.asyncio
    async def test_binary_search_refinement(self, sync_service):
        """測試二進制搜索精化算法"""
        print("\n=== 測試二進制搜索精化算法 ===")
        
        ue_id = "test_ue_002"
        satellite_id = "oneweb_002"
        
        # 執行預測並檢查 binary search 結果
        prediction = await sync_service.predict_satellite_access(
            ue_id=ue_id,
            satellite_id=satellite_id,
            time_horizon_minutes=60.0
        )
        
        # 驗證 binary search 參數
        assert prediction.binary_search_iterations >= 1
        assert prediction.binary_search_iterations <= 10  # 最大迭代次數
        
        # 驗證誤差邊界
        assert prediction.error_bound_ms > 0
        print(f"  - 二進制搜索迭代次數: {prediction.binary_search_iterations}")
        print(f"  - 收斂狀態: {prediction.convergence_achieved}")
        print(f"  - 誤差邊界: {prediction.error_bound_ms:.1f} ms")
        
        # 驗證論文要求：誤差應低於 RAN 層切換程序時間 (通常 < 50ms)
        if prediction.convergence_achieved:
            assert prediction.error_bound_ms <= 50.0, f"誤差 {prediction.error_bound_ms}ms 超過論文要求的 50ms"
            print(f"✓ 達到論文精度要求 (<50ms)")
        else:
            print(f"⚠ 未達到收斂，需要調整算法參數")

    @pytest.mark.asyncio
    async def test_signaling_free_synchronization(self, sync_service):
        """測試無信令同步機制"""
        print("\n=== 測試無信令同步機制 ===")
        
        # 獲取同步狀態
        sync_status = await sync_service.get_sync_status()
        
        # 驗證服務狀態
        assert sync_status["service_status"]["is_running"] is True
        assert sync_status["service_status"]["sync_accuracy_ms"] <= 10.0  # 目標同步精度
        
        # 驗證同步點
        assert sync_status["current_state"]["sync_points"] >= 1
        
        # 驗證時鐘偏移在合理範圍內
        clock_offsets = sync_status["current_state"]["clock_offsets"]
        for network, offset in clock_offsets.items():
            assert abs(offset) <= 100.0, f"{network} 時鐘偏移 {offset}ms 過大"
        
        print(f"✓ 無信令同步機制運行正常")
        print(f"  - 同步精度: {sync_status['service_status']['sync_accuracy_ms']} ms")
        print(f"  - 活躍同步點: {sync_status['current_state']['sync_points']}")
        print(f"  - 時鐘偏移: {clock_offsets}")

    @pytest.mark.asyncio
    async def test_prediction_accuracy_requirements(self, sync_service):
        """測試預測精度要求"""
        print("\n=== 測試預測精度要求 ===")
        
        # 執行多次預測測試
        test_cases = [
            ("ue_001", "oneweb_001"),
            ("ue_002", "oneweb_002"),
            ("ue_003", "oneweb_003")
        ]
        
        predictions = []
        for ue_id, satellite_id in test_cases:
            prediction = await sync_service.predict_satellite_access(
                ue_id=ue_id,
                satellite_id=satellite_id,
                time_horizon_minutes=45.0
            )
            predictions.append(prediction)
        
        # 分析預測結果
        converged_predictions = [p for p in predictions if p.convergence_achieved]
        high_confidence_predictions = [p for p in predictions if p.confidence_score >= 0.8]
        low_error_predictions = [p for p in predictions if p.error_bound_ms <= 50.0]
        
        print(f"  - 總預測數: {len(predictions)}")
        print(f"  - 收斂預測數: {len(converged_predictions)}")
        print(f"  - 高信心度預測數 (≥0.8): {len(high_confidence_predictions)}")
        print(f"  - 低誤差預測數 (≤50ms): {len(low_error_predictions)}")
        
        # 驗證論文要求
        convergence_rate = len(converged_predictions) / len(predictions)
        assert convergence_rate >= 0.8, f"收斂率 {convergence_rate:.2f} 低於預期 (≥0.8)"
        
        if converged_predictions:
            avg_error = sum(p.error_bound_ms for p in converged_predictions) / len(converged_predictions)
            print(f"  - 平均誤差: {avg_error:.1f} ms")
            assert avg_error <= 50.0, f"平均誤差 {avg_error:.1f}ms 超過論文要求"
        
        print(f"✓ 預測精度符合論文要求")

    @pytest.mark.asyncio
    async def test_algorithm_performance(self, sync_service):
        """測試算法性能"""
        print("\n=== 測試算法性能 ===")
        
        start_time = datetime.now()
        
        # 並發執行多個預測
        tasks = []
        for i in range(5):
            task = sync_service.predict_satellite_access(
                ue_id=f"perf_ue_{i:03d}",
                satellite_id=f"oneweb_{(i % 3) + 1:03d}",
                time_horizon_minutes=30.0
            )
            tasks.append(task)
        
        predictions = await asyncio.gather(*tasks)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
        
        # 獲取性能統計
        sync_status = await sync_service.get_sync_status()
        
        print(f"  - 5次並發預測執行時間: {execution_time:.1f} ms")
        print(f"  - 平均單次預測時間: {execution_time/5:.1f} ms")
        print(f"  - 總預測數: {sync_status['statistics']['total_predictions']}")
        print(f"  - 成功預測數: {sync_status['statistics']['successful_predictions']}")
        print(f"  - 收斂率: {sync_status['statistics']['convergence_rate']:.3f}")
        
        # 驗證性能要求
        avg_time_per_prediction = execution_time / 5
        assert avg_time_per_prediction <= 1000.0, f"單次預測時間 {avg_time_per_prediction:.1f}ms 過長"
        
        # 驗證所有預測都成功返回
        assert len(predictions) == 5
        for prediction in predictions:
            assert isinstance(prediction, SatelliteAccessPrediction)
        
        print(f"✓ 算法性能符合要求")

    @pytest.mark.asyncio
    async def test_multi_satellite_coordination(self, sync_service):
        """測試多衛星協調預測"""
        print("\n=== 測試多衛星協調預測 ===")
        
        ue_id = "coord_ue_001"
        satellites = ["oneweb_001", "oneweb_002", "oneweb_003"]
        
        # 為同一個 UE 預測多顆衛星
        predictions = {}
        for satellite_id in satellites:
            prediction = await sync_service.predict_satellite_access(
                ue_id=ue_id,
                satellite_id=satellite_id,
                time_horizon_minutes=40.0
            )
            predictions[satellite_id] = prediction
        
        # 分析預測結果的協調性
        access_times = [p.predicted_access_time for p in predictions.values()]
        confidence_scores = [p.confidence_score for p in predictions.values()]
        
        print(f"  - 衛星數量: {len(satellites)}")
        print(f"  - 預測接入時間範圍: {max(access_times) - min(access_times)}")
        print(f"  - 平均信心度: {sum(confidence_scores)/len(confidence_scores):.3f}")
        
        # 驗證預測時間的合理性（不應該有太大差異）
        time_spread = (max(access_times) - min(access_times)).total_seconds() / 60  # 分鐘
        assert time_spread <= 120.0, f"多衛星預測時間差異 {time_spread:.1f}分鐘 過大"
        
        # 顯示每顆衛星的預測結果
        for satellite_id, prediction in predictions.items():
            print(f"  - {satellite_id}: {prediction.predicted_access_time.strftime('%H:%M:%S')} "
                  f"(信心度: {prediction.confidence_score:.3f}, "
                  f"誤差: {prediction.error_bound_ms:.1f}ms)")
        
        print(f"✓ 多衛星協調預測完成")

    @pytest.mark.asyncio
    async def test_real_time_prediction_updates(self, sync_service):
        """測試實時預測更新"""
        print("\n=== 測試實時預測更新 ===")
        
        ue_id = "realtime_ue_001"
        satellite_id = "oneweb_001"
        
        # 初始預測
        initial_prediction = await sync_service.predict_satellite_access(
            ue_id=ue_id,
            satellite_id=satellite_id,
            time_horizon_minutes=30.0
        )
        
        # 等待一段時間後再次預測
        await asyncio.sleep(2)  # 等待2秒
        
        updated_prediction = await sync_service.predict_satellite_access(
            ue_id=ue_id,
            satellite_id=satellite_id,
            time_horizon_minutes=30.0
        )
        
        # 比較預測結果
        time_diff = abs((updated_prediction.predicted_access_time - 
                        initial_prediction.predicted_access_time).total_seconds())
        
        print(f"  - 初始預測時間: {initial_prediction.predicted_access_time}")
        print(f"  - 更新預測時間: {updated_prediction.predicted_access_time}")
        print(f"  - 預測差異: {time_diff:.1f} 秒")
        
        # 驗證預測的一致性（差異不應太大）
        assert time_diff <= 30.0, f"預測時間差異 {time_diff:.1f}秒 過大"
        
        # 驗證信心度變化合理
        confidence_diff = abs(updated_prediction.confidence_score - initial_prediction.confidence_score)
        assert confidence_diff <= 0.2, f"信心度變化 {confidence_diff:.3f} 過大"
        
        print(f"✓ 實時預測更新一致性良好")


async def run_integration_tests():
    """運行整合測試"""
    print("開始執行 Fine-Grained Synchronized Algorithm 整合測試")
    print("=" * 60)
    
    # 創建測試實例
    test_instance = TestFineGrainedSyncIntegration()
    
    # 創建同步服務
    sync_service = FineGrainedSyncService()
    await sync_service.start_sync_service()
    
    try:
        # 執行所有測試
        await test_instance.test_two_point_prediction_method(sync_service)
        await test_instance.test_binary_search_refinement(sync_service)
        await test_instance.test_signaling_free_synchronization(sync_service)
        await test_instance.test_prediction_accuracy_requirements(sync_service)
        await test_instance.test_algorithm_performance(sync_service)
        await test_instance.test_multi_satellite_coordination(sync_service)
        await test_instance.test_real_time_prediction_updates(sync_service)
        
        print("\n" + "=" * 60)
        print("✓ 所有 Fine-Grained Synchronized Algorithm 測試通過")
        
        # 顯示最終統計
        final_status = await sync_service.get_sync_status()
        print(f"\n最終統計:")
        print(f"  - 總預測數: {final_status['statistics']['total_predictions']}")
        print(f"  - 成功預測數: {final_status['statistics']['successful_predictions']}")
        print(f"  - 收斂率: {final_status['statistics']['convergence_rate']:.3f}")
        print(f"  - 平均精度: {final_status['statistics']['average_accuracy_ms']:.1f} ms")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    finally:
        await sync_service.stop_sync_service()


if __name__ == "__main__":
    asyncio.run(run_integration_tests())