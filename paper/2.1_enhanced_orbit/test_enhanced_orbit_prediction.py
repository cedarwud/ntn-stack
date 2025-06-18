#!/usr/bin/env python3
"""
階段二 2.1 增強軌道預測服務測試程式

測試針對論文需求的特化增強：
1. 二分搜尋時間預測 API - 驗證 10ms 級精度的換手時機預測
2. UE 位置覆蓋判斷最佳化 - 測試快速覆蓋判斷性能
3. 高頻預測快取機制 - 驗證快取命中率和性能提升

執行方式:
cd /home/sat/ntn-stack
source venv/bin/activate
python paper/2.1_enhanced_orbit/test_enhanced_orbit_prediction.py
"""

import sys
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import statistics

# 添加 SimWorld 路徑
sys.path.insert(0, "/home/sat/ntn-stack/simworld/backend")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedOrbitPredictionTester:
    """增強軌道預測服務測試器"""

    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.service = None

    async def setup_test_environment(self) -> bool:
        """設置測試環境"""
        try:
            from app.domains.satellite.services.enhanced_orbit_prediction_service import (
                EnhancedOrbitPredictionService,
                CoverageResult,
                UECoverageInfo,
                BinarySearchPrediction,
            )
            from app.domains.coordinates.models.coordinate_model import GeoCoordinate

            # 初始化服務
            self.service = EnhancedOrbitPredictionService()

            # 保存類別引用供後續使用
            self.CoverageResult = CoverageResult
            self.UECoverageInfo = UECoverageInfo
            self.BinarySearchPrediction = BinarySearchPrediction
            self.GeoCoordinate = GeoCoordinate

            print("✅ 增強軌道預測服務初始化成功")
            return True

        except Exception as e:
            print(f"❌ 測試環境設置失敗: {e}")
            return False

    async def test_binary_search_prediction(self) -> bool:
        """測試二分搜尋時間預測 API"""
        print("\n🔬 測試二分搜尋時間預測 API")
        print("-" * 50)

        try:
            # 測試用 UE 位置 (台灣台北)
            ue_position = self.GeoCoordinate(
                latitude=25.0330, longitude=121.5654, altitude=100.0
            )

            # 測試搜尋範圍
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(seconds=10)  # 10 秒搜尋範圍

            # 記錄搜尋開始時間
            search_start = time.time()

            # 執行二分搜尋
            prediction = await self.service.binary_search_handover_prediction(
                ue_id="test_ue_001",
                source_satellite_id="sat_12345",
                target_satellite_id="sat_67890",
                ue_position=ue_position,
                search_start_time=start_time,
                search_end_time=end_time,
                precision_seconds=0.01,  # 10ms 精度
            )

            search_duration = (time.time() - search_start) * 1000  # 轉為毫秒

            # 驗證結果
            tests_passed = 0
            total_tests = 6

            # 測試 1: 預測結果有效性
            if prediction and isinstance(prediction, self.BinarySearchPrediction):
                tests_passed += 1
                print("  ✅ 預測結果結構正確")
            else:
                print("  ❌ 預測結果結構異常")

            # 測試 2: 搜尋精度
            if prediction and prediction.search_precision_seconds <= 0.01:
                tests_passed += 1
                print(f"  ✅ 搜尋精度達標: {prediction.search_precision_seconds:.3f}s")
            else:
                print(
                    f"  ❌ 搜尋精度不足: {prediction.search_precision_seconds if prediction else 'N/A'}"
                )

            # 測試 3: 搜尋效率
            if search_duration < 5000:  # 5 秒內完成
                tests_passed += 1
                print(f"  ✅ 搜尋效率良好: {search_duration:.1f}ms")
            else:
                print(f"  ❌ 搜尋效率過低: {search_duration:.1f}ms")

            # 測試 4: 迭代次數合理性
            if prediction and 1 <= prediction.search_iterations <= 20:
                tests_passed += 1
                print(f"  ✅ 迭代次數合理: {prediction.search_iterations}")
            else:
                print(
                    f"  ❌ 迭代次數異常: {prediction.search_iterations if prediction else 'N/A'}"
                )

            # 測試 5: 時間範圍正確性
            if prediction and start_time <= prediction.handover_time <= end_time:
                tests_passed += 1
                print(f"  ✅ 換手時間在範圍內: {prediction.handover_time}")
            else:
                print(
                    f"  ❌ 換手時間超出範圍: {prediction.handover_time if prediction else 'N/A'}"
                )

            # 測試 6: 信心度評分
            if prediction and 0 <= prediction.confidence_score <= 1:
                tests_passed += 1
                print(f"  ✅ 信心度評分有效: {prediction.confidence_score:.3f}")
            else:
                print(
                    f"  ❌ 信心度評分異常: {prediction.confidence_score if prediction else 'N/A'}"
                )

            # 記錄性能指標
            self.performance_metrics["binary_search"] = {
                "duration_ms": search_duration,
                "iterations": prediction.search_iterations if prediction else 0,
                "precision_achieved": (
                    prediction.search_precision_seconds if prediction else 0
                ),
                "confidence_score": prediction.confidence_score if prediction else 0,
            }

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 二分搜尋測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("二分搜尋時間預測", success_rate >= 0.8))
            return success_rate >= 0.8

        except Exception as e:
            print(f"❌ 二分搜尋測試失敗: {e}")
            self.test_results.append(("二分搜尋時間預測", False))
            return False

    async def test_ue_coverage_optimization(self) -> bool:
        """測試 UE 位置覆蓋判斷最佳化"""
        print("\n🔬 測試 UE 位置覆蓋判斷最佳化")
        print("-" * 50)

        try:
            # 測試用 UE 位置集合
            test_positions = [
                # 台灣各地
                (
                    "台北",
                    self.GeoCoordinate(
                        latitude=25.0330, longitude=121.5654, altitude=100.0
                    ),
                ),
                (
                    "台中",
                    self.GeoCoordinate(
                        latitude=24.1477, longitude=120.6736, altitude=200.0
                    ),
                ),
                (
                    "高雄",
                    self.GeoCoordinate(
                        latitude=22.6273, longitude=120.3014, altitude=50.0
                    ),
                ),
                # 極地測試
                (
                    "北極",
                    self.GeoCoordinate(latitude=89.0, longitude=0.0, altitude=0.0),
                ),
                (
                    "南極",
                    self.GeoCoordinate(latitude=-89.0, longitude=0.0, altitude=0.0),
                ),
                # 海洋測試
                (
                    "太平洋",
                    self.GeoCoordinate(latitude=0.0, longitude=180.0, altitude=0.0),
                ),
            ]

            test_satellites = ["sat_001", "sat_002", "sat_003"]
            check_time = datetime.utcnow()

            # 性能測試
            start_time = time.time()
            coverage_results = []

            for location_name, ue_pos in test_positions:
                for sat_id in test_satellites:
                    coverage_info = await self.service.check_ue_satellite_coverage(
                        ue_id=f"ue_{location_name.lower()}",
                        satellite_id=sat_id,
                        ue_position=ue_pos,
                        check_time=check_time,
                    )
                    coverage_results.append((location_name, sat_id, coverage_info))

            total_duration = (time.time() - start_time) * 1000
            avg_duration_per_check = total_duration / len(coverage_results)

            # 驗證結果
            tests_passed = 0
            total_tests = 5

            # 測試 1: 所有覆蓋檢查都有結果
            valid_results = sum(
                1 for _, _, info in coverage_results if info is not None
            )
            if valid_results == len(coverage_results):
                tests_passed += 1
                print(f"  ✅ 覆蓋檢查完整性: {valid_results}/{len(coverage_results)}")
            else:
                print(f"  ❌ 覆蓋檢查不完整: {valid_results}/{len(coverage_results)}")

            # 測試 2: 性能要求 (每次檢查 < 100ms)
            if avg_duration_per_check < 100:
                tests_passed += 1
                print(f"  ✅ 覆蓋檢查性能良好: {avg_duration_per_check:.1f}ms/次")
            else:
                print(f"  ❌ 覆蓋檢查性能不足: {avg_duration_per_check:.1f}ms/次")

            # 測試 3: 結果數據結構
            valid_structures = 0
            for _, _, info in coverage_results:
                if (
                    info
                    and hasattr(info, "coverage_result")
                    and hasattr(info, "elevation_angle_deg")
                    and hasattr(info, "signal_strength_estimate")
                ):
                    valid_structures += 1

            if valid_structures == len(coverage_results):
                tests_passed += 1
                print(
                    f"  ✅ 結果數據結構正確: {valid_structures}/{len(coverage_results)}"
                )
            else:
                print(
                    f"  ❌ 結果數據結構錯誤: {valid_structures}/{len(coverage_results)}"
                )

            # 測試 4: 覆蓋結果多樣性
            coverage_types = set()
            for location_name, sat_id, info in coverage_results:
                if info:
                    coverage_types.add(info.coverage_result)

            if len(coverage_types) >= 2:  # 至少有兩種覆蓋狀態
                tests_passed += 1
                print(f"  ✅ 覆蓋結果多樣性: {len(coverage_types)} 種狀態")
            else:
                print(f"  ❌ 覆蓋結果單一: {len(coverage_types)} 種狀態")

            # 測試 5: 信號強度合理性
            valid_signal_strengths = 0
            for _, _, info in coverage_results:
                if info and 0 <= info.signal_strength_estimate <= 1:
                    valid_signal_strengths += 1

            if valid_signal_strengths == len(coverage_results):
                tests_passed += 1
                print(
                    f"  ✅ 信號強度評估正確: {valid_signal_strengths}/{len(coverage_results)}"
                )
            else:
                print(
                    f"  ❌ 信號強度評估錯誤: {valid_signal_strengths}/{len(coverage_results)}"
                )

            # 記錄性能指標
            self.performance_metrics["coverage_optimization"] = {
                "total_checks": len(coverage_results),
                "total_duration_ms": total_duration,
                "avg_duration_per_check_ms": avg_duration_per_check,
                "coverage_types_found": len(coverage_types),
            }

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 覆蓋最佳化測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("UE覆蓋判斷最佳化", success_rate >= 0.8))
            return success_rate >= 0.8

        except Exception as e:
            print(f"❌ 覆蓋最佳化測試失敗: {e}")
            self.test_results.append(("UE覆蓋判斷最佳化", False))
            return False

    async def test_high_frequency_caching(self) -> bool:
        """測試高頻預測快取機制"""
        print("\n🔬 測試高頻預測快取機制")
        print("-" * 50)

        try:
            # 準備測試數據
            satellite_ids = ["sat_001", "sat_002", "sat_003", "sat_004", "sat_005"]
            base_time = datetime.utcnow()
            prediction_times = [
                base_time + timedelta(seconds=i * 10) for i in range(12)  # 12 個時間點
            ]

            # 第一次調用 (冷快取)
            print("  🔄 執行冷快取測試...")
            cold_start = time.time()

            results_1 = await self.service.get_high_frequency_orbit_prediction(
                satellite_ids=satellite_ids,
                prediction_times=prediction_times,
                cache_duration_seconds=60,
            )

            cold_duration = (time.time() - cold_start) * 1000

            # 第二次調用 (熱快取)
            print("  🔄 執行熱快取測試...")
            hot_start = time.time()

            results_2 = await self.service.get_high_frequency_orbit_prediction(
                satellite_ids=satellite_ids,
                prediction_times=prediction_times,
                cache_duration_seconds=60,
            )

            hot_duration = (time.time() - hot_start) * 1000

            # 驗證結果
            tests_passed = 0
            total_tests = 6

            # 測試 1: 結果數據完整性
            expected_requests = len(satellite_ids) * len(prediction_times)
            total_results_1 = sum(len(sat_data) for sat_data in results_1.values())
            total_results_2 = sum(len(sat_data) for sat_data in results_2.values())

            if (
                total_results_1 == expected_requests
                and total_results_2 == expected_requests
            ):
                tests_passed += 1
                print(f"  ✅ 數據完整性: {total_results_1}/{expected_requests}")
            else:
                print(
                    f"  ❌ 數據不完整: {total_results_1},{total_results_2}/{expected_requests}"
                )

            # 測試 2: 快取性能提升
            performance_improvement = (cold_duration - hot_duration) / cold_duration
            if performance_improvement > 0.3:  # 至少 30% 性能提升
                tests_passed += 1
                print(f"  ✅ 快取性能提升: {performance_improvement:.1%}")
            else:
                print(f"  ❌ 快取性能提升不足: {performance_improvement:.1%}")

            # 測試 3: 結果一致性
            consistency_check = True
            for sat_id in satellite_ids:
                if sat_id in results_1 and sat_id in results_2:
                    # 檢查關鍵時間點的結果一致性
                    for time_str in list(results_1[sat_id].keys())[:3]:  # 檢查前3個
                        if (
                            time_str in results_2[sat_id]
                            and results_1[sat_id][time_str]
                            != results_2[sat_id][time_str]
                        ):
                            consistency_check = False
                            break

            if consistency_check:
                tests_passed += 1
                print("  ✅ 快取結果一致性正確")
            else:
                print("  ❌ 快取結果不一致")

            # 測試 4: 快取命中率
            service_stats = await self.service.get_service_status()
            cache_hit_rate = service_stats.get("cache_info", {}).get(
                "cache_hit_rate", 0
            )

            if cache_hit_rate > 0.5:  # 快取命中率 > 50%
                tests_passed += 1
                print(f"  ✅ 快取命中率良好: {cache_hit_rate:.1%}")
            else:
                print(f"  ❌ 快取命中率過低: {cache_hit_rate:.1%}")

            # 測試 5: 冷快取性能
            cold_per_request = cold_duration / expected_requests
            if cold_per_request < 50:  # 每個請求 < 50ms
                tests_passed += 1
                print(f"  ✅ 冷快取性能良好: {cold_per_request:.1f}ms/請求")
            else:
                print(f"  ❌ 冷快取性能不足: {cold_per_request:.1f}ms/請求")

            # 測試 6: 熱快取性能
            hot_per_request = hot_duration / expected_requests
            if hot_per_request < 10:  # 每個請求 < 10ms
                tests_passed += 1
                print(f"  ✅ 熱快取性能優秀: {hot_per_request:.1f}ms/請求")
            else:
                print(f"  ❌ 熱快取性能不足: {hot_per_request:.1f}ms/請求")

            # 記錄性能指標
            self.performance_metrics["high_frequency_caching"] = {
                "cold_cache_duration_ms": cold_duration,
                "hot_cache_duration_ms": hot_duration,
                "performance_improvement": performance_improvement,
                "cold_cache_per_request_ms": cold_per_request,
                "hot_cache_per_request_ms": hot_per_request,
                "cache_hit_rate": cache_hit_rate,
                "total_requests": expected_requests,
            }

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 高頻快取測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("高頻預測快取機制", success_rate >= 0.8))
            return success_rate >= 0.8

        except Exception as e:
            print(f"❌ 高頻快取測試失敗: {e}")
            self.test_results.append(("高頻預測快取機制", False))
            return False

    async def test_service_integration(self) -> bool:
        """測試服務整合功能"""
        print("\n🔬 測試服務整合功能")
        print("-" * 50)

        try:
            # 測試服務狀態
            status = await self.service.get_service_status()

            tests_passed = 0
            total_tests = 4

            # 測試 1: 服務狀態完整性
            required_fields = [
                "service_name",
                "stage",
                "capabilities",
                "configuration",
                "statistics",
            ]
            if all(field in status for field in required_fields):
                tests_passed += 1
                print(f"  ✅ 服務狀態完整: {list(status.keys())}")
            else:
                print(
                    f"  ❌ 服務狀態不完整: 缺少 {set(required_fields) - set(status.keys())}"
                )

            # 測試 2: 功能能力聲明
            capabilities = status.get("capabilities", [])
            expected_capabilities = [
                "binary_search_prediction",
                "ue_coverage_optimization",
                "high_frequency_caching",
            ]
            if all(cap in capabilities for cap in expected_capabilities):
                tests_passed += 1
                print(f"  ✅ 功能能力完整: {capabilities}")
            else:
                print(f"  ❌ 功能能力不完整: {capabilities}")

            # 測試 3: 配置參數合理性
            config = status.get("configuration", {})
            precision = config.get("binary_search_precision_seconds", 0)
            elevation = config.get("min_elevation_angle_deg", 0)

            if 0.001 <= precision <= 0.1 and 10 <= elevation <= 45:
                tests_passed += 1
                print(f"  ✅ 配置參數合理: 精度={precision}s, 仰角={elevation}°")
            else:
                print(f"  ❌ 配置參數異常: 精度={precision}s, 仰角={elevation}°")

            # 測試 4: 統計資訊有效性
            stats = status.get("statistics", {})
            if isinstance(stats, dict) and len(stats) > 0:
                tests_passed += 1
                print(f"  ✅ 統計資訊有效: {len(stats)} 項指標")
            else:
                print(f"  ❌ 統計資訊無效: {stats}")

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 服務整合測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("服務整合功能", success_rate >= 0.8))
            return success_rate >= 0.8

        except Exception as e:
            print(f"❌ 服務整合測試失敗: {e}")
            self.test_results.append(("服務整合功能", False))
            return False

    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 70)
        print("📊 階段二 2.1 增強軌道預測服務測試報告")
        print("=" * 70)

        # 總體結果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, result in self.test_results if result)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n📋 測試結果概覽:")
        for test_name, result in self.test_results:
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"   {status} {test_name}")

        print(f"\n📊 總體統計:")
        print(f"   總測試數: {total_tests}")
        print(f"   通過測試: {passed_tests}")
        print(f"   失敗測試: {total_tests - passed_tests}")
        print(f"   成功率: {success_rate:.1f}%")

        # 性能指標總結
        if self.performance_metrics:
            print(f"\n⚡ 性能指標總結:")

            if "binary_search" in self.performance_metrics:
                bs_metrics = self.performance_metrics["binary_search"]
                print(f"   二分搜尋:")
                print(f"     - 執行時間: {bs_metrics['duration_ms']:.1f}ms")
                print(f"     - 搜尋迭代: {bs_metrics['iterations']} 次")
                print(f"     - 達成精度: {bs_metrics['precision_achieved']:.3f}s")

            if "coverage_optimization" in self.performance_metrics:
                cov_metrics = self.performance_metrics["coverage_optimization"]
                print(f"   覆蓋最佳化:")
                print(f"     - 總檢查數: {cov_metrics['total_checks']}")
                print(
                    f"     - 平均時間: {cov_metrics['avg_duration_per_check_ms']:.1f}ms/次"
                )

            if "high_frequency_caching" in self.performance_metrics:
                cache_metrics = self.performance_metrics["high_frequency_caching"]
                print(f"   高頻快取:")
                print(
                    f"     - 性能提升: {cache_metrics['performance_improvement']:.1%}"
                )
                print(f"     - 快取命中率: {cache_metrics['cache_hit_rate']:.1%}")
                print(
                    f"     - 熱快取速度: {cache_metrics['hot_cache_per_request_ms']:.1f}ms/請求"
                )

        # 階段二 2.1 完成度評估
        print(f"\n🎯 階段二 2.1 完成度評估:")

        feature_completion = {
            "二分搜尋時間預測 API": any(
                name == "二分搜尋時間預測" and result
                for name, result in self.test_results
            ),
            "UE 位置覆蓋判斷最佳化": any(
                name == "UE覆蓋判斷最佳化" and result
                for name, result in self.test_results
            ),
            "高頻預測快取機制": any(
                name == "高頻預測快取機制" and result
                for name, result in self.test_results
            ),
            "服務整合": any(
                name == "服務整合功能" and result for name, result in self.test_results
            ),
        }

        completed_features = sum(feature_completion.values())
        total_features = len(feature_completion)

        for feature, completed in feature_completion.items():
            status = "✅ 完成" if completed else "❌ 未完成"
            print(f"   {status} {feature}")

        completion_rate = (
            (completed_features / total_features * 100) if total_features > 0 else 0
        )
        print(
            f"\n   階段完成度: {completed_features}/{total_features} ({completion_rate:.1f}%)"
        )

        if success_rate >= 90.0:
            print(f"\n🎉 階段二 2.1 增強軌道預測服務實作成功！")
            print(f"✨ 針對論文需求的特化增強已完成")
        elif success_rate >= 75.0:
            print(f"\n⚠️  階段二 2.1 基本完成，建議優化失敗項目")
        else:
            print(f"\n❌ 階段二 2.1 實作需要改進")

        return success_rate >= 75.0


async def main():
    """主函數"""
    print("🚀 開始執行階段二 2.1 增強軌道預測服務測試")

    tester = EnhancedOrbitPredictionTester()

    # 設置測試環境
    if not await tester.setup_test_environment():
        print("❌ 測試環境設置失敗，無法繼續")
        return False

    # 執行測試
    test_functions = [
        tester.test_binary_search_prediction,
        tester.test_ue_coverage_optimization,
        tester.test_high_frequency_caching,
        tester.test_service_integration,
    ]

    for test_func in test_functions:
        try:
            await test_func()
            await asyncio.sleep(0.5)  # 短暫休息
        except Exception as e:
            print(f"❌ 測試執行異常: {e}")

    # 生成報告
    success = tester.generate_test_report()

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        print(f"\n測試完成，退出碼: {exit_code}")
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        exit_code = 130
    except Exception as e:
        print(f"\n💥 測試執行錯誤: {e}")
        exit_code = 1

    sys.exit(exit_code)
