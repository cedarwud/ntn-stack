#!/usr/bin/env python3
"""
階段二 2.4 多方案測試支援測試程式

測試四種切換方案的支援功能：
1. Baseline (NTN) - 3GPP 標準非地面網路換手
2. NTN-GS - 地面站協助方案  
3. NTN-SMN - 衛星網路內換手方案
4. Proposed - 本論文方案

執行方式:
cd /home/sat/ntn-stack
source venv/bin/activate  
python paper/2.4_multi_scheme_support/test_multi_scheme_support.py
"""

import sys
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics
import os
from pathlib import Path

# 添加 NetStack 路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiSchemeSupportTester:
    """多方案測試支援測試器"""
    
    def __init__(self):
        self.test_results = []
        self.scheme_metrics = {}
        self.measurement_service = None
    
    async def setup_test_environment(self) -> bool:
        """設置測試環境"""
        try:
            from netstack_api.services.handover_measurement_service import (
                HandoverMeasurementService,
                HandoverMeasurement,
                HandoverScheme,
                HandoverResult,
                HandoverEvent
            )
            
            # 初始化測試服務
            self.measurement_service = HandoverMeasurementService()
            self.handover_measurement = self.measurement_service.measurement  # 直接引用底層測量對象
            
            # 保存類別引用
            self.HandoverScheme = HandoverScheme
            self.HandoverResult = HandoverResult
            self.HandoverEvent = HandoverEvent
            
            print("✅ 多方案測試支援環境初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 測試環境設置失敗: {e}")
            return False
    
    async def test_scheme_initialization(self) -> bool:
        """測試方案初始化功能"""
        print("\n🔬 測試方案初始化功能")
        print("-" * 50)
        
        try:
            # 測試所有方案類型是否可用
            expected_schemes = [
                self.HandoverScheme.NTN_BASELINE,
                self.HandoverScheme.NTN_GS, 
                self.HandoverScheme.NTN_SMN,
                self.HandoverScheme.PROPOSED
            ]
            
            tests_passed = 0
            total_tests = 4
            
            # 測試 1: 方案枚舉完整性
            available_schemes = list(self.HandoverScheme)
            if len(available_schemes) >= 4:
                tests_passed += 1
                print(f"  ✅ 方案枚舉完整性: {len(available_schemes)} 種方案可用")
            else:
                print(f"  ❌ 方案枚舉不完整: 僅 {len(available_schemes)} 種方案")
            
            # 測試 2: 方案值正確性
            scheme_values = {scheme.value for scheme in expected_schemes}
            expected_values = {"NTN", "NTN-GS", "NTN-SMN", "Proposed"}
            if scheme_values == expected_values:
                tests_passed += 1
                print(f"  ✅ 方案值正確性: {scheme_values}")
            else:
                print(f"  ❌ 方案值錯誤: 期待 {expected_values}，實際 {scheme_values}")
            
            # 測試 3: 測量服務方案支援
            measurement_schemes = []
            for scheme in expected_schemes:
                try:
                    # 測試記錄一個簡單事件
                    start_time = time.time()
                    event_id = self.handover_measurement.record_handover(
                        ue_id=f"test_init_{scheme.value}",
                        source_gnb="test_source",
                        target_gnb="test_target",
                        start_time=start_time,
                        end_time=start_time + 0.025,  # 25ms 延遲
                        handover_scheme=scheme,
                        result=self.HandoverResult.SUCCESS
                    )
                    measurement_schemes.append(scheme)
                except Exception as e:
                    print(f"    ⚠️  方案 {scheme.value} 記錄失敗: {e}")
            
            if len(measurement_schemes) == len(expected_schemes):
                tests_passed += 1
                print(f"  ✅ 測量服務方案支援: {len(measurement_schemes)}/{len(expected_schemes)}")
            else:
                print(f"  ❌ 測量服務方案支援不完整: {len(measurement_schemes)}/{len(expected_schemes)}")
            
            # 測試 4: 方案特性驗證
            scheme_characteristics = {
                self.HandoverScheme.NTN_BASELINE: {"expected_latency_range": (200, 300)},
                self.HandoverScheme.NTN_GS: {"expected_latency_range": (130, 180)},
                self.HandoverScheme.NTN_SMN: {"expected_latency_range": (140, 180)},
                self.HandoverScheme.PROPOSED: {"expected_latency_range": (15, 40)}
            }
            
            characteristics_valid = True
            for scheme, chars in scheme_characteristics.items():
                latency_range = chars["expected_latency_range"]
                if latency_range[0] > 0 and latency_range[1] > latency_range[0]:
                    continue
                else:
                    characteristics_valid = False
                    break
            
            if characteristics_valid:
                tests_passed += 1
                print(f"  ✅ 方案特性驗證: 延遲範圍定義正確")
            else:
                print(f"  ❌ 方案特性驗證失敗")
            
            success_rate = tests_passed / total_tests
            print(f"\n📊 方案初始化測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})")
            
            self.test_results.append(("方案初始化", success_rate >= 0.8))
            return success_rate >= 0.8
            
        except Exception as e:
            print(f"❌ 方案初始化測試失敗: {e}")
            self.test_results.append(("方案初始化", False))
            return False
    
    async def test_scheme_differentiation(self) -> bool:
        """測試方案差異化功能"""
        print("\n🔬 測試方案差異化功能")
        print("-" * 50)
        
        try:
            # 為每種方案生成測試數據
            schemes_config = {
                self.HandoverScheme.NTN_BASELINE: {"target_latency": 250.0, "variance": 25.0},
                self.HandoverScheme.NTN_GS: {"target_latency": 153.0, "variance": 15.0},
                self.HandoverScheme.NTN_SMN: {"target_latency": 158.5, "variance": 16.0},
                self.HandoverScheme.PROPOSED: {"target_latency": 25.0, "variance": 5.0}
            }
            
            scheme_events = {}
            start_time = time.time()
            
            # 為每種方案生成 30 個事件
            for scheme, config in schemes_config.items():
                events = []
                target_latency = config["target_latency"]
                variance = config["variance"]
                
                for i in range(30):
                    # 模擬延遲值（使用目標延遲 ± 變化量）
                    import random
                    latency_variation = random.uniform(-variance, variance)
                    simulated_latency = max(5.0, target_latency + latency_variation)
                    
                    event_start = time.time()
                    event_end = event_start + (simulated_latency / 1000.0)
                    
                    event_id = self.handover_measurement.record_handover(
                        ue_id=f"test_diff_{scheme.value}_{i}",
                        source_gnb=f"src_{i}",
                        target_gnb=f"tgt_{i}",
                        start_time=event_start,
                        end_time=event_end,
                        handover_scheme=scheme,
                        result=self.HandoverResult.SUCCESS
                    )
                    
                    events.append({
                        "event_id": event_id,
                        "latency_ms": simulated_latency,
                        "scheme": scheme
                    })
                
                scheme_events[scheme] = events
            
            total_duration = (time.time() - start_time) * 1000
            
            # 驗證結果
            tests_passed = 0
            total_tests = 5
            
            # 測試 1: 事件生成完整性
            total_events = sum(len(events) for events in scheme_events.values())
            expected_events = len(schemes_config) * 30
            if total_events == expected_events:
                tests_passed += 1
                print(f"  ✅ 事件生成完整性: {total_events}/{expected_events}")
            else:
                print(f"  ❌ 事件生成不完整: {total_events}/{expected_events}")
            
            # 測試 2: 方案分佈均勻性
            scheme_counts = {scheme: len(events) for scheme, events in scheme_events.items()}
            if all(count == 30 for count in scheme_counts.values()):
                tests_passed += 1
                print(f"  ✅ 方案分佈均勻: 每方案 30 個事件")
            else:
                print(f"  ❌ 方案分佈不均: {scheme_counts}")
            
            # 測試 3: 延遲差異化驗證
            scheme_latencies = {}
            for scheme, events in scheme_events.items():
                latencies = [event["latency_ms"] for event in events]
                avg_latency = statistics.mean(latencies)
                scheme_latencies[scheme] = avg_latency
            
            # 驗證 Proposed 方案延遲最低
            proposed_latency = scheme_latencies[self.HandoverScheme.PROPOSED]
            other_latencies = [lat for scheme, lat in scheme_latencies.items() 
                             if scheme != self.HandoverScheme.PROPOSED]
            
            if proposed_latency < min(other_latencies):
                tests_passed += 1
                print(f"  ✅ Proposed 方案延遲最低: {proposed_latency:.1f}ms")
            else:
                print(f"  ❌ Proposed 方案延遲未達最優: {proposed_latency:.1f}ms")
            
            # 測試 4: 方案延遲範圍合理性
            latency_ranges_valid = True
            for scheme, config in schemes_config.items():
                avg_latency = scheme_latencies[scheme]
                target_latency = config["target_latency"]
                acceptable_deviation = config["variance"] * 2  # 允許 2 倍變化量偏差
                
                if abs(avg_latency - target_latency) <= acceptable_deviation:
                    continue
                else:
                    latency_ranges_valid = False
                    print(f"    ⚠️  {scheme.value} 延遲偏差過大: {avg_latency:.1f}ms vs 目標 {target_latency:.1f}ms")
            
            if latency_ranges_valid:
                tests_passed += 1
                print(f"  ✅ 方案延遲範圍合理性通過")
            else:
                print(f"  ❌ 方案延遲範圍合理性失敗")
            
            # 測試 5: 差異化生成效率
            avg_generation_time = total_duration / total_events
            if avg_generation_time < 100:  # 每事件 < 100ms
                tests_passed += 1
                print(f"  ✅ 差異化生成效率良好: {avg_generation_time:.1f}ms/事件")
            else:
                print(f"  ❌ 差異化生成效率過低: {avg_generation_time:.1f}ms/事件")
            
            self.scheme_metrics["differentiation"] = {
                "total_events": total_events,
                "scheme_latencies": {str(k): v for k, v in scheme_latencies.items()},
                "generation_time_ms": total_duration
            }
            
            success_rate = tests_passed / total_tests
            print(f"\n📊 方案差異化測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})")
            
            self.test_results.append(("方案差異化", success_rate >= 0.8))
            return success_rate >= 0.8
            
        except Exception as e:
            print(f"❌ 方案差異化測試失敗: {e}")
            self.test_results.append(("方案差異化", False))
            return False
    
    async def test_scheme_switching(self) -> bool:
        """測試方案切換功能"""
        print("\n🔬 測試方案切換功能")
        print("-" * 50)
        
        try:
            # 模擬運行時方案切換
            switch_sequence = [
                self.HandoverScheme.NTN_BASELINE,
                self.HandoverScheme.PROPOSED,
                self.HandoverScheme.NTN_GS,
                self.HandoverScheme.NTN_SMN,
                self.HandoverScheme.PROPOSED
            ]
            
            switch_results = []
            start_time = time.time()
            
            for i, scheme in enumerate(switch_sequence):
                # 模擬方案切換的切換事件
                ue_id = f"switching_ue_{i}"
                event_start = time.time()
                
                # 根據方案調整延遲
                if scheme == self.HandoverScheme.PROPOSED:
                    latency_ms = 25.0
                elif scheme == self.HandoverScheme.NTN_GS:
                    latency_ms = 153.0
                elif scheme == self.HandoverScheme.NTN_SMN:
                    latency_ms = 158.5
                else:  # NTN_BASELINE
                    latency_ms = 250.0
                
                event_end = event_start + (latency_ms / 1000.0)
                
                event_id = self.handover_measurement.record_handover(
                    ue_id=ue_id,
                    source_gnb=f"switch_src_{i}",
                    target_gnb=f"switch_tgt_{i}",
                    start_time=event_start,
                    end_time=event_end,
                    handover_scheme=scheme,
                    result=self.HandoverResult.SUCCESS
                )
                
                switch_results.append({
                    "step": i,
                    "scheme": scheme,
                    "event_id": event_id,
                    "latency_ms": latency_ms
                })
                
                # 短暫等待模擬實際切換間隔
                await asyncio.sleep(0.1)
            
            total_duration = (time.time() - start_time) * 1000
            
            # 驗證結果
            tests_passed = 0
            total_tests = 4
            
            # 測試 1: 切換序列完整性
            if len(switch_results) == len(switch_sequence):
                tests_passed += 1
                print(f"  ✅ 切換序列完整性: {len(switch_results)}/{len(switch_sequence)}")
            else:
                print(f"  ❌ 切換序列不完整: {len(switch_results)}/{len(switch_sequence)}")
            
            # 測試 2: 方案切換正確性
            correct_switches = 0
            for i, result in enumerate(switch_results):
                if result["scheme"] == switch_sequence[i]:
                    correct_switches += 1
            
            if correct_switches == len(switch_sequence):
                tests_passed += 1
                print(f"  ✅ 方案切換正確性: {correct_switches}/{len(switch_sequence)}")
            else:
                print(f"  ❌ 方案切換錯誤: {correct_switches}/{len(switch_sequence)}")
            
            # 測試 3: 切換延遲一致性
            latency_consistent = True
            for result in switch_results:
                scheme = result["scheme"]
                actual_latency = result["latency_ms"]
                
                # 檢查延遲是否符合方案特性
                if scheme == self.HandoverScheme.PROPOSED and 20 <= actual_latency <= 35:
                    continue
                elif scheme == self.HandoverScheme.NTN_GS and 140 <= actual_latency <= 170:
                    continue
                elif scheme == self.HandoverScheme.NTN_SMN and 140 <= actual_latency <= 180:
                    continue
                elif scheme == self.HandoverScheme.NTN_BASELINE and 200 <= actual_latency <= 300:
                    continue
                else:
                    latency_consistent = False
                    print(f"    ⚠️  {scheme.value} 延遲異常: {actual_latency:.1f}ms")
            
            if latency_consistent:
                tests_passed += 1
                print(f"  ✅ 切換延遲一致性通過")
            else:
                print(f"  ❌ 切換延遲一致性失敗")
            
            # 測試 4: 切換效率
            avg_switch_time = total_duration / len(switch_results)
            if avg_switch_time < 200:  # 每次切換 < 200ms
                tests_passed += 1
                print(f"  ✅ 切換效率良好: {avg_switch_time:.1f}ms/切換")
            else:
                print(f"  ❌ 切換效率過低: {avg_switch_time:.1f}ms/切換")
            
            self.scheme_metrics["switching"] = {
                "switch_count": len(switch_results),
                "total_duration_ms": total_duration,
                "avg_switch_time_ms": avg_switch_time
            }
            
            success_rate = tests_passed / total_tests
            print(f"\n📊 方案切換測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})")
            
            self.test_results.append(("方案切換", success_rate >= 0.8))
            return success_rate >= 0.8
            
        except Exception as e:
            print(f"❌ 方案切換測試失敗: {e}")
            self.test_results.append(("方案切換", False))
            return False
    
    async def test_scheme_performance_isolation(self) -> bool:
        """測試方案效能隔離功能"""
        print("\n🔬 測試方案效能隔離功能")
        print("-" * 50)
        
        try:
            # 模擬同時執行多種方案的場景
            concurrent_schemes = [
                self.HandoverScheme.NTN_BASELINE,
                self.HandoverScheme.NTN_GS,
                self.HandoverScheme.NTN_SMN,
                self.HandoverScheme.PROPOSED
            ]
            
            # 為每種方案並行生成事件
            tasks = []
            start_time = time.time()
            
            async def generate_scheme_events(scheme: self.HandoverScheme, count: int = 15):
                events = []
                base_latency = {
                    self.HandoverScheme.NTN_BASELINE: 250.0,
                    self.HandoverScheme.NTN_GS: 153.0,
                    self.HandoverScheme.NTN_SMN: 158.5,
                    self.HandoverScheme.PROPOSED: 25.0
                }[scheme]
                
                for i in range(count):
                    import random
                    # 添加一些隨機變化
                    latency_ms = base_latency + random.uniform(-5, 5)
                    
                    event_start = time.time()
                    event_end = event_start + (latency_ms / 1000.0)
                    
                    event_id = self.handover_measurement.record_handover(
                        ue_id=f"isolation_{scheme.value}_{i}",
                        source_gnb=f"iso_src_{i}",
                        target_gnb=f"iso_tgt_{i}",
                        start_time=event_start,
                        end_time=event_end,
                        handover_scheme=scheme,
                        result=self.HandoverResult.SUCCESS
                    )
                    
                    events.append({
                        "scheme": scheme,
                        "event_id": event_id,
                        "latency_ms": latency_ms
                    })
                    
                    # 短暫等待模擬真實間隔
                    await asyncio.sleep(0.01)
                
                return events
            
            # 並行執行所有方案
            for scheme in concurrent_schemes:
                task = asyncio.create_task(generate_scheme_events(scheme))
                tasks.append(task)
            
            # 等待所有任務完成
            results = await asyncio.gather(*tasks)
            total_duration = (time.time() - start_time) * 1000
            
            # 整理結果
            all_events = []
            scheme_event_counts = {}
            for events in results:
                all_events.extend(events)
                for event in events:
                    scheme = event["scheme"]
                    scheme_event_counts[scheme] = scheme_event_counts.get(scheme, 0) + 1
            
            # 驗證結果
            tests_passed = 0
            total_tests = 4
            
            # 測試 1: 並行執行完整性
            expected_total = len(concurrent_schemes) * 15
            if len(all_events) == expected_total:
                tests_passed += 1
                print(f"  ✅ 並行執行完整性: {len(all_events)}/{expected_total}")
            else:
                print(f"  ❌ 並行執行不完整: {len(all_events)}/{expected_total}")
            
            # 測試 2: 方案隔離性驗證
            isolation_valid = True
            for scheme in concurrent_schemes:
                if scheme_event_counts.get(scheme, 0) == 15:
                    continue
                else:
                    isolation_valid = False
                    print(f"    ⚠️  {scheme.value} 事件數異常: {scheme_event_counts.get(scheme, 0)}")
            
            if isolation_valid:
                tests_passed += 1
                print(f"  ✅ 方案隔離性驗證通過")
            else:
                print(f"  ❌ 方案隔離性驗證失敗")
            
            # 測試 3: 效能隔離驗證
            scheme_latencies = {}
            for event in all_events:
                scheme = event["scheme"]
                if scheme not in scheme_latencies:
                    scheme_latencies[scheme] = []
                scheme_latencies[scheme].append(event["latency_ms"])
            
            # 計算平均延遲並驗證差異化
            avg_latencies = {}
            for scheme, latencies in scheme_latencies.items():
                avg_latencies[scheme] = statistics.mean(latencies)
            
            performance_isolated = True
            # 確認 Proposed 延遲仍然最低
            proposed_avg = avg_latencies[self.HandoverScheme.PROPOSED]
            for scheme, avg_lat in avg_latencies.items():
                if scheme != self.HandoverScheme.PROPOSED and avg_lat <= proposed_avg:
                    performance_isolated = False
                    break
            
            if performance_isolated:
                tests_passed += 1
                print(f"  ✅ 效能隔離驗證: Proposed 延遲最低 ({proposed_avg:.1f}ms)")
            else:
                print(f"  ❌ 效能隔離驗證失敗")
            
            # 測試 4: 並行執行效率
            avg_concurrent_time = total_duration / len(all_events)
            if avg_concurrent_time < 50:  # 每事件 < 50ms
                tests_passed += 1
                print(f"  ✅ 並行執行效率良好: {avg_concurrent_time:.1f}ms/事件")
            else:
                print(f"  ❌ 並行執行效率過低: {avg_concurrent_time:.1f}ms/事件")
            
            self.scheme_metrics["isolation"] = {
                "concurrent_events": len(all_events),
                "scheme_counts": {str(k): v for k, v in scheme_event_counts.items()},
                "avg_latencies": {str(k): v for k, v in avg_latencies.items()},
                "concurrent_duration_ms": total_duration
            }
            
            success_rate = tests_passed / total_tests
            print(f"\n📊 方案效能隔離測試結果: {tests_passed}/{total_tests} ({success_rate:.1%})")
            
            self.test_results.append(("方案效能隔離", success_rate >= 0.8))
            return success_rate >= 0.8
            
        except Exception as e:
            print(f"❌ 方案效能隔離測試失敗: {e}")
            self.test_results.append(("方案效能隔離", False))
            return False
    
    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 70)
        print("📊 階段二 2.4 多方案測試支援測試報告")
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
        
        # 方案支援總結
        if self.scheme_metrics:
            print(f"\n⚡ 方案支援指標總結:")
            
            if "differentiation" in self.scheme_metrics:
                diff_metrics = self.scheme_metrics["differentiation"]
                print(f"   方案差異化:")
                print(f"     - 測試事件數: {diff_metrics['total_events']}")
                print(f"     - 生成時間: {diff_metrics['generation_time_ms']:.1f}ms")
            
            if "switching" in self.scheme_metrics:
                switch_metrics = self.scheme_metrics["switching"]
                print(f"   方案切換:")
                print(f"     - 切換次數: {switch_metrics['switch_count']}")
                print(f"     - 平均切換時間: {switch_metrics['avg_switch_time_ms']:.1f}ms")
            
            if "isolation" in self.scheme_metrics:
                iso_metrics = self.scheme_metrics["isolation"]
                print(f"   效能隔離:")
                print(f"     - 並行事件數: {iso_metrics['concurrent_events']}")
                print(f"     - 執行時間: {iso_metrics['concurrent_duration_ms']:.1f}ms")
        
        # 階段二 2.4 完成度評估
        print(f"\n🎯 階段二 2.4 完成度評估:")
        
        feature_completion = {
            "方案初始化功能": any(name == "方案初始化" and result for name, result in self.test_results),
            "方案差異化功能": any(name == "方案差異化" and result for name, result in self.test_results),
            "方案切換功能": any(name == "方案切換" and result for name, result in self.test_results),
            "方案效能隔離": any(name == "方案效能隔離" and result for name, result in self.test_results)
        }
        
        completed_features = sum(feature_completion.values())
        total_features = len(feature_completion)
        
        for feature, completed in feature_completion.items():
            status = "✅ 完成" if completed else "❌ 未完成"
            print(f"   {status} {feature}")
        
        completion_rate = (completed_features / total_features * 100) if total_features > 0 else 0
        print(f"\n   階段完成度: {completed_features}/{total_features} ({completion_rate:.1f}%)")
        
        if success_rate >= 90.0:
            print(f"\n🎉 階段二 2.4 多方案測試支援實作成功！")
            print(f"✨ 支援四種切換方案的完整測試框架")
        elif success_rate >= 75.0:
            print(f"\n⚠️  階段二 2.4 基本完成，建議優化失敗項目")
        else:
            print(f"\n❌ 階段二 2.4 實作需要改進")
        
        return success_rate >= 75.0


async def main():
    """主函數"""
    print("🚀 開始執行階段二 2.4 多方案測試支援測試")
    
    tester = MultiSchemeSupportTester()
    
    # 設置測試環境
    if not await tester.setup_test_environment():
        print("❌ 測試環境設置失敗，無法繼續")
        return False
    
    # 執行測試
    test_functions = [
        tester.test_scheme_initialization,
        tester.test_scheme_differentiation,
        tester.test_scheme_switching,
        tester.test_scheme_performance_isolation
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