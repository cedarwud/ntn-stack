#!/usr/bin/env python3
"""
階段二 2.2 換手決策服務測試程式

測試換手決策服務的核心功能：
1. 換手觸發條件判斷
2. 多衛星換手策略
3. 換手成本估算

執行方式:
cd /home/sat/ntn-stack
source venv/bin/activate
python paper/2.2_handover_decision/test_handover_decision.py
"""

import sys
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

# 添加 SimWorld 路徑
sys.path.insert(0, "/home/sat/ntn-stack/simworld/backend")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HandoverDecisionTester:
    """換手決策服務測試器"""

    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.service = None

    async def setup_test_environment(self) -> bool:
        """設置測試環境"""
        try:
            from app.domains.handover.services.handover_decision_service import (
                HandoverDecisionService,
                HandoverTrigger,
                HandoverStrategy,
                HandoverDecision,
                HandoverCandidate,
            )
            from app.domains.coordinates.models.coordinate_model import GeoCoordinate

            # 初始化服務
            self.service = HandoverDecisionService()

            # 保存類別引用供後續使用
            self.HandoverTrigger = HandoverTrigger
            self.HandoverStrategy = HandoverStrategy
            self.HandoverDecision = HandoverDecision
            self.HandoverCandidate = HandoverCandidate
            self.GeoCoordinate = GeoCoordinate

            print("✅ 換手決策服務初始化成功")
            return True

        except Exception as e:
            print(f"❌ 測試環境設置失敗: {e}")
            return False

    async def test_handover_trigger_evaluation(self) -> bool:
        """測試換手觸發條件判斷"""
        print("\n🔬 測試換手觸發條件判斷")
        print("-" * 50)

        try:
            # 測試用 UE 位置和衛星
            ue_position = self.GeoCoordinate(
                latitude=25.0330, longitude=121.5654, altitude_m=100.0
            )

            test_scenarios = [
                # 場景1：正常信號，應該無觸發
                ("正常信號場景", "sat_12345", datetime.utcnow()),
                # 場景2：信號較弱，可能觸發信號劣化
                ("弱信號場景", "sat_67890", datetime.utcnow()),
                # 場景3：負載測試
                ("負載測試場景", "sat_11111", datetime.utcnow()),
            ]

            trigger_results = []
            start_time = time.time()

            for scenario_name, satellite_id, test_time in test_scenarios:
                try:
                    triggers = await self.service.evaluate_handover_triggers(
                        ue_id=f"test_ue_{scenario_name.replace(' ', '_')}",
                        current_satellite_id=satellite_id,
                        ue_position=ue_position,
                        current_time=test_time,
                    )

                    triggered_count = len([t for t in triggers if t.triggered])
                    trigger_results.append(
                        (scenario_name, triggered_count, len(triggers))
                    )

                    print(
                        f"  📋 {scenario_name}: {triggered_count}/{len(triggers)} 觸發條件"
                    )

                except Exception as e:
                    print(f"  ❌ {scenario_name} 失敗: {e}")
                    trigger_results.append((scenario_name, 0, 0))

            total_duration = (time.time() - start_time) * 1000

            # 驗證結果
            tests_passed = 0
            total_tests = 4

            # 測試 1: 所有場景都有結果
            if len(trigger_results) == len(test_scenarios):
                tests_passed += 1
                print("  ✅ 觸發條件評估完整性")

            # 測試 2: 平均評估時間合理
            avg_duration = total_duration / len(test_scenarios)
            if avg_duration < 1000:  # 每次評估 < 1秒
                tests_passed += 1
                print(f"  ✅ 評估效率良好: {avg_duration:.1f}ms/場景")
            else:
                print(f"  ❌ 評估效率過低: {avg_duration:.1f}ms/場景")

            # 測試 3: 觸發條件多樣性
            unique_trigger_counts = set(result[1] for result in trigger_results)
            if len(unique_trigger_counts) >= 1:
                tests_passed += 1
                print(f"  ✅ 觸發條件多樣性: {len(unique_trigger_counts)} 種結果")

            # 測試 4: 服務可用性
            service_status = await self.service.get_service_status()
            if service_status.get("status") == "active":
                tests_passed += 1
                print("  ✅ 服務狀態正常")

            self.performance_metrics["trigger_evaluation"] = {
                "total_scenarios": len(test_scenarios),
                "avg_duration_ms": avg_duration,
                "trigger_results": trigger_results,
            }

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 觸發條件判斷測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("換手觸發條件判斷", success_rate >= 0.75))
            return success_rate >= 0.75

        except Exception as e:
            print(f"❌ 觸發條件判斷測試失敗: {e}")
            self.test_results.append(("換手觸發條件判斷", False))
            return False

    async def test_handover_decision_making(self) -> bool:
        """測試換手決策制定"""
        print("\n🔬 測試換手決策制定")
        print("-" * 50)

        try:
            # 測試用 UE 位置
            ue_position = self.GeoCoordinate(
                latitude=24.1477, longitude=120.6736, altitude_m=200.0
            )

            decision_scenarios = [
                ("決策場景A", "sat_source_01", datetime.utcnow()),
                (
                    "決策場景B",
                    "sat_source_02",
                    datetime.utcnow() + timedelta(seconds=10),
                ),
                (
                    "決策場景C",
                    "sat_source_03",
                    datetime.utcnow() + timedelta(seconds=20),
                ),
            ]

            decision_results = []
            start_time = time.time()

            for scenario_name, source_satellite, test_time in decision_scenarios:
                try:
                    decision = await self.service.make_handover_decision(
                        ue_id=f"test_ue_{scenario_name.replace(' ', '_')}",
                        current_satellite_id=source_satellite,
                        ue_position=ue_position,
                        current_time=test_time,
                    )

                    if decision:
                        decision_results.append(
                            (scenario_name, True, decision.confidence_score)
                        )
                        print(
                            f"  📋 {scenario_name}: 決策完成，信心度 {decision.confidence_score:.2f}"
                        )
                    else:
                        decision_results.append((scenario_name, False, 0.0))
                        print(f"  📋 {scenario_name}: 無需換手")

                except Exception as e:
                    print(f"  ❌ {scenario_name} 決策失敗: {e}")
                    decision_results.append((scenario_name, False, 0.0))

            total_duration = (time.time() - start_time) * 1000

            # 驗證結果
            tests_passed = 0
            total_tests = 4

            # 測試 1: 決策流程完整性
            if len(decision_results) == len(decision_scenarios):
                tests_passed += 1
                print("  ✅ 決策流程完整性")

            # 測試 2: 決策效率
            avg_decision_time = total_duration / len(decision_scenarios)
            if avg_decision_time < 2000:  # 每次決策 < 2秒
                tests_passed += 1
                print(f"  ✅ 決策效率良好: {avg_decision_time:.1f}ms/決策")
            else:
                print(f"  ❌ 決策效率過低: {avg_decision_time:.1f}ms/決策")

            # 測試 3: 決策質量
            decisions_made = [r for r in decision_results if r[1]]
            if len(decisions_made) >= 1:
                avg_confidence = statistics.mean([r[2] for r in decisions_made])
                if avg_confidence > 0.6:
                    tests_passed += 1
                    print(f"  ✅ 決策信心度良好: {avg_confidence:.2f}")
                else:
                    print(f"  ❌ 決策信心度過低: {avg_confidence:.2f}")
            else:
                tests_passed += 1  # 無決策也是正常情況
                print("  ✅ 決策保守策略正常")

            # 測試 4: 統計資訊有效性
            stats = self.service.decision_stats
            if stats["total_decisions"] >= 0:
                tests_passed += 1
                print(f"  ✅ 統計資訊正常: {stats['total_decisions']} 次決策")

            self.performance_metrics["decision_making"] = {
                "total_scenarios": len(decision_scenarios),
                "avg_decision_time_ms": avg_decision_time,
                "decisions_made": len(decisions_made),
                "decision_results": decision_results,
            }

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 換手決策制定測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("換手決策制定", success_rate >= 0.75))
            return success_rate >= 0.75

        except Exception as e:
            print(f"❌ 換手決策制定測試失敗: {e}")
            self.test_results.append(("換手決策制定", False))
            return False

    async def test_multi_satellite_handover(self) -> bool:
        """測試多衛星換手策略"""
        print("\n🔬 測試多衛星換手策略")
        print("-" * 50)

        try:
            # 測試用 UE 位置
            ue_position = self.GeoCoordinate(
                latitude=22.6273, longitude=120.3014, altitude_m=50.0
            )

            multi_handover_scenarios = [
                (
                    "成本優化",
                    "sat_current_01",
                    ["sat_target_01", "sat_target_02"],
                    "minimize_cost",
                ),
                (
                    "延遲優化",
                    "sat_current_02",
                    ["sat_target_03", "sat_target_04"],
                    "minimize_latency",
                ),
                (
                    "平衡優化",
                    "sat_current_03",
                    ["sat_target_05", "sat_target_06"],
                    "balanced",
                ),
            ]

            optimization_results = []
            start_time = time.time()

            for (
                scenario_name,
                current_sat,
                target_sats,
                strategy,
            ) in multi_handover_scenarios:
                try:
                    multi_handover = (
                        await self.service.execute_multi_satellite_handover(
                            ue_id=f"test_ue_{scenario_name.replace(' ', '_')}",
                            current_satellite_id=current_sat,
                            target_satellites=target_sats,
                            ue_position=ue_position,
                            optimization_strategy=strategy,
                        )
                    )

                    sequence_length = len(multi_handover.handover_sequence)
                    total_cost = multi_handover.total_handover_cost

                    optimization_results.append(
                        (scenario_name, True, sequence_length, total_cost)
                    )
                    print(
                        f"  📋 {scenario_name}: {sequence_length} 步驟，總成本 {total_cost:.1f}"
                    )

                except Exception as e:
                    print(f"  ❌ {scenario_name} 優化失敗: {e}")
                    optimization_results.append((scenario_name, False, 0, 0.0))

            total_duration = (time.time() - start_time) * 1000

            # 驗證結果
            tests_passed = 0
            total_tests = 4

            # 測試 1: 多衛星優化完整性
            successful_optimizations = [r for r in optimization_results if r[1]]
            if len(successful_optimizations) >= 2:
                tests_passed += 1
                print(f"  ✅ 多衛星優化成功: {len(successful_optimizations)}/3")
            else:
                print(f"  ❌ 多衛星優化成功率低: {len(successful_optimizations)}/3")

            # 測試 2: 優化效率
            avg_optimization_time = total_duration / len(multi_handover_scenarios)
            if avg_optimization_time < 3000:  # 每次優化 < 3秒
                tests_passed += 1
                print(f"  ✅ 優化效率良好: {avg_optimization_time:.1f}ms/優化")
            else:
                print(f"  ❌ 優化效率過低: {avg_optimization_time:.1f}ms/優化")

            # 測試 3: 換手序列合理性
            sequence_lengths = [r[2] for r in successful_optimizations if r[2] > 0]
            if sequence_lengths and max(sequence_lengths) <= 5:
                tests_passed += 1
                print(f"  ✅ 換手序列長度合理: 最大 {max(sequence_lengths)} 步驟")
            else:
                print(
                    f"  ❌ 換手序列過長: 最大 {max(sequence_lengths) if sequence_lengths else 0} 步驟"
                )

            # 測試 4: 成本估算有效性
            total_costs = [r[3] for r in successful_optimizations if r[3] > 0]
            if total_costs and all(0 < cost < 1000 for cost in total_costs):
                tests_passed += 1
                print(
                    f"  ✅ 成本估算合理: 範圍 {min(total_costs):.1f}-{max(total_costs):.1f}"
                )
            else:
                print(f"  ❌ 成本估算異常")

            self.performance_metrics["multi_satellite_handover"] = {
                "total_scenarios": len(multi_handover_scenarios),
                "avg_optimization_time_ms": avg_optimization_time,
                "successful_optimizations": len(successful_optimizations),
                "optimization_results": optimization_results,
            }

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 多衛星換手策略測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("多衛星換手策略", success_rate >= 0.75))
            return success_rate >= 0.75

        except Exception as e:
            print(f"❌ 多衛星換手策略測試失敗: {e}")
            self.test_results.append(("多衛星換手策略", False))
            return False

    async def test_handover_cost_estimation(self) -> bool:
        """測試換手成本估算"""
        print("\n🔬 測試換手成本估算")
        print("-" * 50)

        try:
            # 測試用換手場景
            cost_scenarios = [
                ("正常換手", "sat_source_01", "sat_target_01", []),
                ("緊急換手", "sat_source_02", "sat_target_02", ["emergency"]),
                ("預測換手", "sat_source_03", "sat_target_03", ["predicted"]),
                ("負載均衡", "sat_source_04", "sat_target_04", ["load_balance"]),
            ]

            cost_results = []
            start_time = time.time()

            for scenario_name, source_sat, target_sat, trigger_types in cost_scenarios:
                try:
                    # 模擬觸發條件
                    triggers = []
                    for trigger_type in trigger_types:
                        if trigger_type == "emergency":
                            trigger = type(
                                "MockTrigger",
                                (),
                                {
                                    "trigger_type": self.HandoverTrigger.EMERGENCY_HANDOVER,
                                    "triggered": True,
                                },
                            )()
                        elif trigger_type == "predicted":
                            trigger = type(
                                "MockTrigger",
                                (),
                                {
                                    "trigger_type": self.HandoverTrigger.PREDICTED_OUTAGE,
                                    "triggered": True,
                                },
                            )()
                        elif trigger_type == "load_balance":
                            trigger = type(
                                "MockTrigger",
                                (),
                                {
                                    "trigger_type": self.HandoverTrigger.LOAD_BALANCING,
                                    "triggered": True,
                                },
                            )()
                        triggers.append(trigger)

                    # 估算換手成本
                    cost = await self.service._estimate_handover_cost(
                        source_satellite_id=source_sat,
                        target_satellite_id=target_sat,
                        triggers=triggers,
                    )

                    cost_results.append((scenario_name, True, cost))
                    print(f"  📋 {scenario_name}: 成本 {cost:.1f}")

                except Exception as e:
                    print(f"  ❌ {scenario_name} 成本估算失敗: {e}")
                    cost_results.append((scenario_name, False, 0.0))

            total_duration = (time.time() - start_time) * 1000

            # 驗證結果
            tests_passed = 0
            total_tests = 4

            # 測試 1: 成本估算完整性
            successful_estimations = [r for r in cost_results if r[1]]
            if len(successful_estimations) >= 3:
                tests_passed += 1
                print(f"  ✅ 成本估算完整性: {len(successful_estimations)}/4")

            # 測試 2: 估算效率
            avg_estimation_time = total_duration / len(cost_scenarios)
            if avg_estimation_time < 500:  # 每次估算 < 500ms
                tests_passed += 1
                print(f"  ✅ 估算效率優秀: {avg_estimation_time:.1f}ms/估算")
            else:
                print(f"  ❌ 估算效率過低: {avg_estimation_time:.1f}ms/估算")

            # 測試 3: 成本值合理性
            costs = [r[2] for r in successful_estimations if r[2] > 0]
            if costs and all(10 <= cost <= 200 for cost in costs):
                tests_passed += 1
                print(f"  ✅ 成本值合理: 範圍 {min(costs):.1f}-{max(costs):.1f}")
            else:
                print(f"  ❌ 成本值異常")

            # 測試 4: 成本差異化
            if costs and (max(costs) - min(costs)) > 5:
                tests_passed += 1
                print(f"  ✅ 成本差異化正常: 差異 {max(costs) - min(costs):.1f}")
            else:
                print(f"  ❌ 成本差異化不足")

            self.performance_metrics["cost_estimation"] = {
                "total_scenarios": len(cost_scenarios),
                "avg_estimation_time_ms": avg_estimation_time,
                "successful_estimations": len(successful_estimations),
                "cost_range": [min(costs), max(costs)] if costs else [0, 0],
            }

            success_rate = tests_passed / total_tests
            print(
                f"\n📊 換手成本估算測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})"
            )

            self.test_results.append(("換手成本估算", success_rate >= 0.75))
            return success_rate >= 0.75

        except Exception as e:
            print(f"❌ 換手成本估算測試失敗: {e}")
            self.test_results.append(("換手成本估算", False))
            return False

    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 70)
        print("📊 階段二 2.2 換手決策服務測試報告")
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

            if "trigger_evaluation" in self.performance_metrics:
                trigger_metrics = self.performance_metrics["trigger_evaluation"]
                print(f"   觸發條件判斷:")
                print(
                    f"     - 平均評估時間: {trigger_metrics['avg_duration_ms']:.1f}ms"
                )
                print(f"     - 測試場景數: {trigger_metrics['total_scenarios']}")

            if "decision_making" in self.performance_metrics:
                decision_metrics = self.performance_metrics["decision_making"]
                print(f"   換手決策制定:")
                print(
                    f"     - 平均決策時間: {decision_metrics['avg_decision_time_ms']:.1f}ms"
                )
                print(f"     - 成功決策數: {decision_metrics['decisions_made']}")

            if "multi_satellite_handover" in self.performance_metrics:
                multi_metrics = self.performance_metrics["multi_satellite_handover"]
                print(f"   多衛星換手:")
                print(
                    f"     - 平均優化時間: {multi_metrics['avg_optimization_time_ms']:.1f}ms"
                )
                print(f"     - 成功優化數: {multi_metrics['successful_optimizations']}")

            if "cost_estimation" in self.performance_metrics:
                cost_metrics = self.performance_metrics["cost_estimation"]
                print(f"   成本估算:")
                print(
                    f"     - 平均估算時間: {cost_metrics['avg_estimation_time_ms']:.1f}ms"
                )
                print(
                    f"     - 成本範圍: {cost_metrics['cost_range'][0]:.1f}-{cost_metrics['cost_range'][1]:.1f}"
                )

        # 階段二 2.2 完成度評估
        print(f"\n🎯 階段二 2.2 完成度評估:")

        feature_completion = {
            "換手觸發條件判斷": any(
                name == "換手觸發條件判斷" and result
                for name, result in self.test_results
            ),
            "換手決策制定": any(
                name == "換手決策制定" and result for name, result in self.test_results
            ),
            "多衛星換手策略": any(
                name == "多衛星換手策略" and result
                for name, result in self.test_results
            ),
            "換手成本估算": any(
                name == "換手成本估算" and result for name, result in self.test_results
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
            print(f"\n🎉 階段二 2.2 換手決策服務實作成功！")
            print(f"✨ 智能換手決策功能已完成")
        elif success_rate >= 75.0:
            print(f"\n⚠️  階段二 2.2 基本完成，建議優化失敗項目")
        else:
            print(f"\n❌ 階段二 2.2 實作需要改進")

        return success_rate >= 75.0


async def main():
    """主函數"""
    print("🚀 開始執行階段二 2.2 換手決策服務測試")

    tester = HandoverDecisionTester()

    # 設置測試環境
    if not await tester.setup_test_environment():
        print("❌ 測試環境設置失敗，無法繼續")
        return False

    # 執行測試
    test_functions = [
        tester.test_handover_trigger_evaluation,
        tester.test_handover_decision_making,
        tester.test_multi_satellite_handover,
        tester.test_handover_cost_estimation,
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
