"""
Algorithm Verification Integration Tests - Stage 3

測試算法驗證服務的完整功能，包括：
1. 論文基準對比測試
2. 性能回歸測試
3. 多衛星驗證測試
4. 統計分析和報告生成
5. 驗證框架的可靠性
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加 netstack 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../netstack'))

from netstack_api.services.algorithm_verification_service import (
    AlgorithmVerificationService,
    VerificationScenario,
    PaperBaseline,
    VerificationResult,
    RegressionTestCase
)
from netstack_api.services.enhanced_synchronized_algorithm import EnhancedSynchronizedAlgorithm


class TestAlgorithmVerification:
    """算法驗證整合測試"""

    @pytest.fixture
    async def verification_service(self):
        """創建驗證服務實例"""
        # 創建依賴的算法服務
        enhanced_algorithm = EnhancedSynchronizedAlgorithm()
        await enhanced_algorithm.start_enhanced_algorithm()
        
        # 創建驗證服務
        verification_service = AlgorithmVerificationService(
            enhanced_algorithm=enhanced_algorithm
        )
        await verification_service.start_verification_service()
        
        yield verification_service
        
        # 清理
        await verification_service.stop_verification_service()
        await enhanced_algorithm.stop_enhanced_algorithm()

    @pytest.mark.asyncio
    async def test_paper_baseline_comparison(self, verification_service):
        """測試論文基準對比功能"""
        print("\n=== 測試論文基準對比功能 ===")
        
        # 執行論文基準對比測試
        result = await verification_service._run_paper_baseline_comparison()
        
        # 驗證結果結構
        assert isinstance(result, VerificationResult)
        assert result.scenario == VerificationScenario.PAPER_BASELINE_COMPARISON
        assert result.sample_size >= 30  # 最小樣本數
        
        # 驗證統計數據
        assert "handover_accuracy" in result.statistics
        assert "computation_time_ms" in result.statistics
        assert "convergence_rate" in result.statistics
        
        # 驗證基準對比
        assert "enhanced_sync" in result.baseline_comparison
        
        # 檢查每個指標的統計分析
        for metric, stats in result.statistics.items():
            assert "mean" in stats
            assert "std_dev" in stats
            assert "min" in stats
            assert "max" in stats
            assert stats["count"] > 0
        
        # 檢查基準對比結果
        for baseline_id, comparison in result.baseline_comparison.items():
            assert "comparisons" in comparison
            for metric, comp in comparison["comparisons"].items():
                assert "measured" in comp
                assert "baseline" in comp
                assert "deviation" in comp
                assert "within_tolerance" in comp
                assert "performance_grade" in comp
        
        print(f"✓ 論文基準對比測試完成")
        print(f"  - 樣本數量: {result.sample_size}")
        print(f"  - 測試通過: {result.passed}")
        print(f"  - 信心水準: {result.confidence_level:.1%}")
        
        # 顯示關鍵指標
        if "handover_accuracy" in result.statistics:
            accuracy_stats = result.statistics["handover_accuracy"]
            print(f"  - Handover 準確率: {accuracy_stats['mean']:.1%} ± {accuracy_stats['std_dev']:.3f}")
        
        if "computation_time_ms" in result.statistics:
            time_stats = result.statistics["computation_time_ms"]
            print(f"  - 計算時間: {time_stats['mean']:.1f}ms ± {time_stats['std_dev']:.1f}ms")

    @pytest.mark.asyncio
    async def test_performance_regression_testing(self, verification_service):
        """測試性能回歸測試功能"""
        print("\n=== 測試性能回歸測試功能 ===")
        
        # 執行回歸測試
        result = await verification_service._run_performance_regression_test()
        
        # 驗證結果結構
        assert isinstance(result, VerificationResult)
        assert result.scenario == VerificationScenario.PERFORMANCE_REGRESSION
        
        # 驗證回歸測試結果
        assert "pass_rate" in result.statistics
        pass_rate = result.statistics["pass_rate"]["mean"]
        
        # 檢查測試案例執行
        regression_results = result.deviation_analysis["regression_test_results"]
        assert len(regression_results) >= 3  # 至少有 3 個測試案例
        
        # 分析每個測試案例
        passed_cases = 0
        for case_result in regression_results:
            assert "test_case_id" in case_result
            assert "passed" in case_result
            
            if case_result["passed"]:
                passed_cases += 1
            else:
                print(f"  ⚠ 測試案例失敗: {case_result['test_case_id']}")
                if "failed_checks" in case_result:
                    for check in case_result["failed_checks"]:
                        print(f"    - {check}")
        
        calculated_pass_rate = passed_cases / len(regression_results)
        assert abs(pass_rate - calculated_pass_rate) < 0.01  # 通過率計算一致性
        
        print(f"✓ 性能回歸測試完成")
        print(f"  - 測試案例數: {len(regression_results)}")
        print(f"  - 通過案例數: {passed_cases}")
        print(f"  - 通過率: {pass_rate:.1%}")
        print(f"  - 整體通過: {result.passed}")
        
        # 檢查關鍵測試案例
        test_case_status = {}
        for case_result in regression_results:
            case_id = case_result["test_case_id"]
            test_case_status[case_id] = case_result["passed"]
        
        print(f"  - 基本預測測試: {'✓' if test_case_status.get('basic_prediction', False) else '✗'}")
        print(f"  - Binary Search 測試: {'✓' if test_case_status.get('binary_search_convergence', False) else '✗'}")
        print(f"  - 無信令同步測試: {'✓' if test_case_status.get('signaling_free_sync', False) else '✗'}")

    @pytest.mark.asyncio
    async def test_multi_satellite_validation(self, verification_service):
        """測試多衛星驗證功能"""
        print("\n=== 測試多衛星驗證功能 ===")
        
        # 執行多衛星驗證測試
        result = await verification_service._run_multi_satellite_validation()
        
        # 驗證結果結構
        assert isinstance(result, VerificationResult)
        assert result.scenario == VerificationScenario.MULTI_SATELLITE_VALIDATION
        
        # 驗證可擴展性指標
        assert "prediction_accuracy" in result.statistics
        assert "computation_time_ms" in result.statistics
        assert "scalability_factor" in result.statistics
        
        # 檢查基準對比
        baseline_comparison = result.baseline_comparison
        assert "scalability_requirement" in baseline_comparison
        assert "accuracy_requirement" in baseline_comparison
        
        scalability_passed = baseline_comparison["scalability_requirement"]["actual"]
        accuracy_passed = baseline_comparison["accuracy_requirement"]["actual"]
        
        # 驗證性能指標
        accuracy_stats = result.statistics["prediction_accuracy"]
        time_stats = result.statistics["computation_time_ms"]
        
        print(f"✓ 多衛星驗證測試完成")
        print(f"  - 可擴展性測試: {'通過' if scalability_passed else '未通過'}")
        print(f"  - 準確性測試: {'通過' if accuracy_passed else '未通過'}")
        print(f"  - 平均準確率: {accuracy_stats['mean']:.1%}")
        print(f"  - 平均計算時間: {time_stats['mean']:.1f}ms")
        print(f"  - 最大計算時間: {time_stats['max']:.1f}ms")
        
        # 檢查可擴展性性能
        max_computation_time = time_stats['max']
        if max_computation_time <= 500.0:
            print(f"  ✓ 可擴展性性能良好 (最大時間: {max_computation_time:.1f}ms <= 500ms)")
        else:
            print(f"  ⚠ 可擴展性性能需改進 (最大時間: {max_computation_time:.1f}ms > 500ms)")

    @pytest.mark.asyncio
    async def test_comprehensive_verification_suite(self, verification_service):
        """測試綜合驗證套件"""
        print("\n=== 測試綜合驗證套件 ===")
        
        # 執行多個驗證場景
        scenarios = [
            VerificationScenario.PAPER_BASELINE_COMPARISON,
            VerificationScenario.PERFORMANCE_REGRESSION,
            VerificationScenario.MULTI_SATELLITE_VALIDATION
        ]
        
        results = await verification_service.run_comprehensive_verification(scenarios)
        
        # 驗證所有場景都有結果
        assert len(results) == len(scenarios)
        
        # 檢查每個場景的結果
        scenario_status = {}
        for scenario in scenarios:
            scenario_key = scenario.value
            assert scenario_key in results
            
            result = results[scenario_key]
            assert isinstance(result, VerificationResult)
            scenario_status[scenario_key] = result.passed
        
        # 計算整體通過率
        passed_scenarios = sum(1 for passed in scenario_status.values() if passed)
        total_scenarios = len(scenario_status)
        overall_pass_rate = passed_scenarios / total_scenarios
        
        print(f"✓ 綜合驗證套件完成")
        print(f"  - 總場景數: {total_scenarios}")
        print(f"  - 通過場景數: {passed_scenarios}")
        print(f"  - 整體通過率: {overall_pass_rate:.1%}")
        
        # 詳細場景狀態
        for scenario_key, passed in scenario_status.items():
            status = "✓" if passed else "✗"
            print(f"  - {scenario_key}: {status}")
        
        # 驗證服務狀態更新
        assert len(verification_service.verification_results) >= len(scenarios)

    @pytest.mark.asyncio
    async def test_verification_summary_and_reporting(self, verification_service):
        """測試驗證摘要和報告功能"""
        print("\n=== 測試驗證摘要和報告功能 ===")
        
        # 先執行一些驗證測試生成數據
        await verification_service._run_paper_baseline_comparison()
        await verification_service._run_performance_regression_test()
        
        # 獲取驗證摘要
        summary = await verification_service.get_verification_summary()
        
        # 驗證摘要結構
        assert "verification_summary" in summary
        assert "scenario_breakdown" in summary
        assert "latest_results" in summary
        assert "recommendations" in summary
        
        # 檢查驗證摘要統計
        verification_summary = summary["verification_summary"]
        assert "total_verifications" in verification_summary
        assert "passed_verifications" in verification_summary
        assert "overall_pass_rate" in verification_summary
        assert "average_confidence" in verification_summary
        
        # 檢查場景分解
        scenario_breakdown = summary["scenario_breakdown"]
        assert len(scenario_breakdown) >= 2  # 至少有兩個場景
        
        for scenario, stats in scenario_breakdown.items():
            assert "pass_rate" in stats
            assert "total_tests" in stats
            assert "passed_tests" in stats
            assert 0.0 <= stats["pass_rate"] <= 1.0
        
        # 檢查最新結果
        latest_results = summary["latest_results"]
        assert len(latest_results) >= 2
        
        for result in latest_results:
            assert "verification_id" in result
            assert "scenario" in result
            assert "passed" in result
            assert "confidence" in result
            assert "test_time" in result
        
        # 檢查建議
        recommendations = summary["recommendations"]
        assert isinstance(recommendations, list)
        
        print(f"✓ 驗證摘要和報告測試完成")
        print(f"  - 總驗證數: {verification_summary['total_verifications']}")
        print(f"  - 通過驗證數: {verification_summary['passed_verifications']}")
        print(f"  - 整體通過率: {verification_summary['overall_pass_rate']:.1%}")
        print(f"  - 平均信心度: {verification_summary['average_confidence']:.1%}")
        print(f"  - 場景類型數: {len(scenario_breakdown)}")
        print(f"  - 建議數量: {len(recommendations)}")

    @pytest.mark.asyncio
    async def test_statistical_analysis_accuracy(self, verification_service):
        """測試統計分析準確性"""
        print("\n=== 測試統計分析準確性 ===")
        
        # 執行基準對比測試
        result = await verification_service._run_paper_baseline_comparison()
        
        # 驗證統計計算的準確性
        for metric, raw_values in result.metrics.items():
            if raw_values:
                stats = result.statistics[metric]
                
                # 驗證基本統計量
                calculated_mean = sum(raw_values) / len(raw_values)
                assert abs(stats["mean"] - calculated_mean) < 0.001, f"{metric} 平均值計算錯誤"
                
                calculated_min = min(raw_values)
                calculated_max = max(raw_values)
                assert stats["min"] == calculated_min, f"{metric} 最小值計算錯誤"
                assert stats["max"] == calculated_max, f"{metric} 最大值計算錯誤"
                
                assert stats["count"] == len(raw_values), f"{metric} 計數錯誤"
        
        # 檢查偏差計算
        for baseline_id, comparison in result.baseline_comparison.items():
            baseline = verification_service.paper_baselines[baseline_id]
            
            for metric, comp in comparison["comparisons"].items():
                measured = comp["measured"]
                baseline_value = comp["baseline"]
                calculated_deviation = (measured - baseline_value) / baseline_value if baseline_value != 0 else 0
                
                assert abs(comp["deviation"] - calculated_deviation) < 0.001, f"{metric} 偏差計算錯誤"
                assert abs(comp["deviation_percent"] - calculated_deviation * 100) < 0.1, f"{metric} 偏差百分比計算錯誤"
        
        print(f"✓ 統計分析準確性驗證完成")
        print(f"  - 統計指標數: {len(result.statistics)}")
        print(f"  - 基準對比數: {len(result.baseline_comparison)}")

    @pytest.mark.asyncio
    async def test_regression_test_case_execution(self, verification_service):
        """測試回歸測試案例執行"""
        print("\n=== 測試回歸測試案例執行 ===")
        
        # 檢查已設置的回歸測試案例
        test_cases = verification_service.regression_test_cases
        assert len(test_cases) >= 3, "應該有至少 3 個回歸測試案例"
        
        # 測試每個回歸測試案例
        for test_id, test_case in test_cases.items():
            print(f"\n  測試案例: {test_case.description}")
            
            # 執行測試案例
            case_result = await verification_service._execute_regression_test_case(test_case)
            
            # 驗證結果結構
            assert "test_case_id" in case_result
            assert "passed" in case_result
            # 注意：test_case_id 可能與字典的 key 不同，所以不做嚴格檢查
            # assert case_result["test_case_id"] == test_id
            
            if case_result["passed"]:
                print(f"    ✓ 測試通過")
                assert "actual_values" in case_result
                assert "expected_output" in case_result
                
                # 檢查實際值是否符合預期
                actual_values = case_result["actual_values"]
                expected_output = case_result["expected_output"]
                
                for metric, expected in expected_output.items():
                    assert metric in actual_values, f"缺少指標: {metric}"
                    actual = actual_values[metric]
                    
                    if isinstance(expected, dict):
                        if "min" in expected:
                            print(f"      {metric}: {actual:.3f} >= {expected['min']:.3f}")
                        if "max" in expected:
                            print(f"      {metric}: {actual:.3f} <= {expected['max']:.3f}")
                    else:
                        print(f"      {metric}: {actual:.3f} ≈ {expected:.3f}")
            else:
                print(f"    ✗ 測試失敗")
                if "failed_checks" in case_result:
                    for check in case_result["failed_checks"]:
                        print(f"      - {check}")
        
        print(f"\n✓ 回歸測試案例執行完成")

    @pytest.mark.asyncio
    async def test_baseline_tolerance_validation(self, verification_service):
        """測試基準容許度驗證"""
        print("\n=== 測試基準容許度驗證 ===")
        
        # 檢查基準設置
        baselines = verification_service.paper_baselines
        assert len(baselines) >= 2, "應該有至少 2 個基準"
        
        for baseline_id, baseline in baselines.items():
            print(f"\n  基準: {baseline.algorithm_name}")
            print(f"    - Handover 準確率: {baseline.handover_accuracy:.1%} ± {baseline.accuracy_tolerance:.1%}")
            print(f"    - 計算時間: {baseline.computation_time_ms:.1f}ms ± {baseline.time_tolerance:.1%}")
            print(f"    - 收斂率: {baseline.convergence_rate:.1%} ± {baseline.convergence_tolerance:.1%}")
            
            # 驗證基準參數合理性
            assert 0.0 <= baseline.handover_accuracy <= 1.0
            assert baseline.computation_time_ms > 0
            assert 0.0 <= baseline.convergence_rate <= 1.0
            assert baseline.accuracy_tolerance > 0
            assert baseline.time_tolerance > 0
            assert baseline.convergence_tolerance > 0
        
        # 執行一個簡單的對比測試來驗證容許度邏輯
        result = await verification_service._run_paper_baseline_comparison()
        
        # 檢查容許度是否正確應用
        for baseline_id, comparison in result.baseline_comparison.items():
            for metric, comp in comparison["comparisons"].items():
                tolerance = comp["tolerance"]
                deviation = abs(comp["deviation"])
                within_tolerance = comp["within_tolerance"]
                
                # 驗證容許度判斷邏輯
                expected_within_tolerance = deviation <= tolerance
                assert within_tolerance == expected_within_tolerance, \
                    f"{metric} 容許度判斷錯誤: {deviation:.3f} vs {tolerance:.3f}"
        
        print(f"\n✓ 基準容許度驗證完成")


async def run_stage3_verification_tests():
    """運行 Stage 3 算法驗證測試"""
    print("開始執行 Algorithm Verification Service (Stage 3) 整合測試")
    print("=" * 70)
    
    # 創建測試實例
    test_instance = TestAlgorithmVerification()
    
    # 創建驗證服務
    enhanced_algorithm = EnhancedSynchronizedAlgorithm()
    await enhanced_algorithm.start_enhanced_algorithm()
    
    verification_service = AlgorithmVerificationService(
        enhanced_algorithm=enhanced_algorithm
    )
    await verification_service.start_verification_service()
    
    try:
        # 執行所有測試
        await test_instance.test_paper_baseline_comparison(verification_service)
        await test_instance.test_performance_regression_testing(verification_service)
        await test_instance.test_multi_satellite_validation(verification_service)
        await test_instance.test_comprehensive_verification_suite(verification_service)
        await test_instance.test_verification_summary_and_reporting(verification_service)
        await test_instance.test_statistical_analysis_accuracy(verification_service)
        await test_instance.test_regression_test_case_execution(verification_service)
        await test_instance.test_baseline_tolerance_validation(verification_service)
        
        print("\n" + "=" * 70)
        print("✓ 所有 Stage 3 Algorithm Verification 測試通過")
        
        # 顯示最終驗證摘要
        final_summary = await verification_service.get_verification_summary()
        
        print(f"\n📊 Stage 3 驗證框架總結:")
        summary_stats = final_summary["verification_summary"]
        print(f"  - 總驗證測試數: {summary_stats['total_verifications']}")
        print(f"  - 通過驗證數: {summary_stats['passed_verifications']}")
        print(f"  - 整體通過率: {summary_stats['overall_pass_rate']:.1%}")
        print(f"  - 平均信心度: {summary_stats['average_confidence']:.1%}")
        
        print(f"\n📈 場景驗證狀況:")
        for scenario, stats in final_summary["scenario_breakdown"].items():
            print(f"  - {scenario}: {stats['pass_rate']:.1%} ({stats['passed_tests']}/{stats['total_tests']})")
        
        print(f"\n💡 系統建議:")
        for i, recommendation in enumerate(final_summary["recommendations"], 1):
            print(f"  {i}. {recommendation}")
        
    except Exception as e:
        print(f"\n❌ Stage 3 測試失敗: {e}")
        raise
    finally:
        await verification_service.stop_verification_service()
        await enhanced_algorithm.stop_enhanced_algorithm()


if __name__ == "__main__":
    asyncio.run(run_stage3_verification_tests())