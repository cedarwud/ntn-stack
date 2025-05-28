#!/usr/bin/env python3
"""
Sionna 核心功能測試
專注於測試已實現的核心 Sionna 無線通道模型功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# 配置
SIMWORLD_URL = "http://localhost:8888"
NETSTACK_URL = "http://localhost:8080"


class SionnaCoreTest:
    """Sionna 核心功能測試器"""

    def __init__(self):
        self.simworld_url = SIMWORLD_URL
        self.netstack_url = NETSTACK_URL

    async def test_wireless_health(self) -> bool:
        """測試無線模組健康檢查"""
        print("🔄 測試無線模組健康檢查...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.simworld_url}/api/v1/wireless/health"
                ) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ 無線模組健康: {health_data['status']}")
                        print(
                            f"   - GPU 可用: {health_data['services']['sionna_simulation']['gpu_available']}"
                        )
                        print(
                            f"   - 活躍模擬: {health_data['services']['sionna_simulation']['active_simulations']}"
                        )
                        print(
                            f"   - 處理的通道數: {health_data['metrics']['total_channels_processed']}"
                        )
                        return True
                    else:
                        print(f"❌ 無線模組健康檢查失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 無線模組健康檢查異常: {e}")
            return False

    async def test_quick_simulation(self) -> bool:
        """測試快速通道模擬"""
        print("🔄 測試快速通道模擬...")

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "environment_type": "urban",
                    "frequency_ghz": 2.1,
                    "bandwidth_mhz": 20,
                    "tx_position": [0, 0, 30],
                    "rx_position": [1000, 0, 1.5],
                    "ue_id": "ue_test",
                    "gnb_id": "gnb_test",
                }

                async with session.post(
                    f"{self.simworld_url}/api/v1/wireless/quick-simulation",
                    params=params,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 快速模擬成功，結果數量: {len(result)}")

                        if result:
                            first_result = result[0]
                            source_channel = first_result["source_channel"]
                            ran_params = first_result["ran_parameters"]

                            print(f"   📡 通道資訊:")
                            print(f"     - 通道 ID: {source_channel['channel_id']}")
                            print(
                                f"     - 頻率: {source_channel['frequency_hz']/1e9:.1f} GHz"
                            )
                            print(
                                f"     - 路徑損耗: {source_channel['path_loss_db']:.1f} dB"
                            )
                            print(f"     - 多路徑數: {len(source_channel['paths'])}")

                            print(f"   📊 RAN 參數:")
                            print(f"     - SINR: {ran_params['sinr_db']:.1f} dB")
                            print(f"     - RSRP: {ran_params['rsrp_dbm']:.1f} dBm")
                            print(f"     - RSRQ: {ran_params['rsrq_db']:.1f} dB")
                            print(f"     - CQI: {ran_params['cqi']}")
                            print(
                                f"     - 吞吐量: {ran_params['throughput_mbps']:.1f} Mbps"
                            )
                            print(f"     - 延遲: {ran_params['latency_ms']:.1f} ms")

                        return True
                    else:
                        print(f"❌ 快速模擬失敗: {response.status}")
                        error_text = await response.text()
                        print(f"   錯誤詳情: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ 快速模擬測試異常: {e}")
            return False

    async def test_satellite_ntn_simulation(self) -> bool:
        """測試衛星 NTN 模擬"""
        print("🔄 測試衛星 NTN 模擬...")

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "satellite_altitude_km": 550,
                    "frequency_ghz": 20,
                    "bandwidth_mhz": 100,
                    "ue_id": "ue_satellite",
                    "gnb_id": "gnb_satellite",
                }

                async with session.post(
                    f"{self.simworld_url}/api/v1/wireless/satellite-ntn-simulation",
                    params=params,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 衛星 NTN 模擬成功，結果數量: {len(result)}")

                        if result:
                            first_result = result[0]
                            source_channel = first_result["source_channel"]
                            ran_params = first_result["ran_parameters"]

                            print(f"   🛰️ 衛星通道資訊:")
                            print(f"     - 衛星高度: 550 km")
                            print(
                                f"     - 頻率: {source_channel['frequency_hz']/1e9:.1f} GHz"
                            )
                            print(
                                f"     - 路徑損耗: {source_channel['path_loss_db']:.1f} dB"
                            )
                            print(f"     - 發送端位置: {source_channel['tx_position']}")
                            print(f"     - 接收端位置: {source_channel['rx_position']}")

                            print(f"   📊 衛星 RAN 參數:")
                            print(f"     - SINR: {ran_params['sinr_db']:.1f} dB")
                            print(f"     - RSRP: {ran_params['rsrp_dbm']:.1f} dBm")
                            print(f"     - RSRQ: {ran_params['rsrq_db']:.1f} dB")
                            print(f"     - CQI: {ran_params['cqi']}")
                            print(f"     - 延遲: {ran_params['latency_ms']:.1f} ms")

                        return True
                    else:
                        print(f"❌ 衛星 NTN 模擬失敗: {response.status}")
                        error_text = await response.text()
                        print(f"   錯誤詳情: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ 衛星 NTN 模擬測試異常: {e}")
            return False

    async def test_channel_metrics(self) -> bool:
        """測試通道模型指標"""
        print("🔄 測試通道模型指標...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.simworld_url}/api/v1/wireless/metrics"
                ) as response:
                    if response.status == 200:
                        metrics = await response.json()
                        print(f"✅ 通道模型指標查詢成功")
                        print(
                            f"   - 處理的通道總數: {metrics['total_channels_processed']}"
                        )
                        print(
                            f"   - 平均轉換時間: {metrics['average_conversion_time_ms']:.1f} ms"
                        )
                        print(f"   - 成功率: {metrics['success_rate']*100:.1f}%")
                        print(f"   - GPU 使用率: {metrics['gpu_utilization']*100:.1f}%")
                        print(f"   - 記憶體使用: {metrics['memory_usage_mb']:.1f} MB")
                        return True
                    else:
                        print(f"❌ 通道模型指標查詢失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 通道模型指標測試異常: {e}")
            return False

    async def test_netstack_health(self) -> bool:
        """測試 NetStack 健康狀態"""
        print("🔄 測試 NetStack 健康狀態...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.netstack_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ NetStack 健康: {health_data['overall_status']}")

                        # 檢查各個服務狀態
                        services = health_data.get("services", {})
                        for service_name, service_info in services.items():
                            status = service_info.get("status", "unknown")
                            print(f"   - {service_name}: {status}")

                        return True
                    else:
                        print(f"❌ NetStack 健康檢查失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ NetStack 健康檢查異常: {e}")
            return False

    async def test_satellite_gnb_mapping(self) -> bool:
        """測試衛星 gNodeB 映射"""
        print("🔄 測試衛星 gNodeB 映射...")

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "satellite_id": 25544,  # ISS
                    "frequency": 2100,
                    "bandwidth": 20,
                }

                async with session.post(
                    f"{self.netstack_url}/api/v1/satellite-gnb/mapping", params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 衛星 gNodeB 映射成功")
                        print(f"   - 衛星 ID: {params['satellite_id']}")
                        print(f"   - 映射狀態: {result.get('message', 'N/A')}")
                        return True
                    else:
                        print(f"❌ 衛星 gNodeB 映射失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 衛星 gNodeB 映射測試異常: {e}")
            return False

    async def run_core_tests(self) -> Dict[str, bool]:
        """執行核心功能測試"""
        print("🚀 開始 Sionna 核心功能測試")
        print("=" * 60)

        tests = [
            ("無線模組健康檢查", self.test_wireless_health),
            ("快速通道模擬", self.test_quick_simulation),
            ("衛星 NTN 模擬", self.test_satellite_ntn_simulation),
            ("通道模型指標", self.test_channel_metrics),
            ("NetStack 健康狀態", self.test_netstack_health),
            ("衛星 gNodeB 映射", self.test_satellite_gnb_mapping),
        ]

        results = {}

        for test_name, test_func in tests:
            print(f"\n📋 執行測試: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    print(f"✅ {test_name} 測試通過")
                else:
                    print(f"❌ {test_name} 測試失敗")
            except Exception as e:
                print(f"❌ {test_name} 測試異常: {e}")
                results[test_name] = False

            # 測試間隔
            await asyncio.sleep(1)

        return results

    def print_summary(self, results: Dict[str, bool]):
        """印出測試摘要"""
        print("\n" + "=" * 60)
        print("📊 Sionna 核心功能測試摘要")
        print("=" * 60)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"{test_name:.<40} {status}")

        print("-" * 60)
        print(f"總測試數: {total}")
        print(f"通過數: {passed}")
        print(f"失敗數: {total - passed}")
        print(f"成功率: {passed/total*100:.1f}%")

        if passed == total:
            print("\n🎉 所有核心功能測試通過！")
            print("✨ Sionna 無線通道模型與 UERANSIM 整合功能完全正常")
        elif passed >= total * 0.8:
            print(f"\n✅ 核心功能基本正常！")
            print("🔧 建議檢查失敗的功能並進行修復")
        else:
            print(f"\n⚠️ 有多個核心功能失敗，請檢查系統狀態")


async def main():
    """主函數"""
    tester = SionnaCoreTest()
    results = await tester.run_core_tests()
    tester.print_summary(results)

    # 根據測試結果返回適當的退出代碼
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    success_rate = passed / total

    # 如果成功率 >= 80%，視為成功
    return 0 if success_rate >= 0.8 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
        exit(1)
    except Exception as e:
        print(f"\n💥 測試執行異常: {e}")
        exit(1)
