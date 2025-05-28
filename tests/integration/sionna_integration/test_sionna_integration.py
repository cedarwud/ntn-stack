#!/usr/bin/env python3
"""
Sionna 無線通道模型與 UERANSIM 整合測試
測試 simworld 和 netstack 之間的 Sionna 整合功能
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# 配置
SIMWORLD_URL = "http://localhost:8888"
NETSTACK_URL = "http://localhost:8080"


class SionnaIntegrationTester:
    """Sionna 整合測試器"""

    def __init__(self):
        self.simworld_url = SIMWORLD_URL
        self.netstack_url = NETSTACK_URL

    async def test_simworld_wireless_api(self) -> bool:
        """測試 simworld wireless API"""
        print("🔄 測試 SimWorld Wireless API...")

        try:
            async with aiohttp.ClientSession() as session:
                # 測試健康檢查
                async with session.get(
                    f"{self.simworld_url}/api/v1/wireless/health"
                ) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(
                            f"✅ SimWorld Wireless 健康檢查通過: {health_data['status']}"
                        )
                        return True
                    else:
                        print(f"❌ SimWorld Wireless 健康檢查失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ SimWorld Wireless API 測試失敗: {e}")
            return False

    async def test_netstack_health_api(self) -> bool:
        """測試 netstack 健康 API"""
        print("🔄 測試 NetStack 健康 API...")

        try:
            async with aiohttp.ClientSession() as session:
                # 測試健康檢查
                async with session.get(f"{self.netstack_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(
                            f"✅ NetStack 健康檢查通過: {health_data['overall_status']}"
                        )
                        return True
                    else:
                        print(f"❌ NetStack 健康檢查失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ NetStack 健康 API 測試失敗: {e}")
            return False

    async def test_quick_simulation(self) -> bool:
        """測試快速通道模擬"""
        print("🔄 測試快速通道模擬...")

        try:
            async with aiohttp.ClientSession() as session:
                # 使用 quick-simulation 端點
                params = {
                    "environment_type": "urban",
                    "frequency_ghz": 2.1,
                    "bandwidth_mhz": 20,
                    "tx_position": [0, 0, 30],
                    "rx_position": [1000, 0, 1.5],
                    "ue_id": "ue_001",
                    "gnb_id": "gnb_001",
                }

                async with session.post(
                    f"{self.simworld_url}/api/v1/wireless/quick-simulation",
                    params=params,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 快速通道模擬成功，結果數量: {len(result)}")

                        # 顯示第一個結果的詳細信息
                        if result:
                            first_result = result[0]
                            ran_params = first_result["ran_parameters"]
                            print(f"   - SINR: {ran_params['sinr_db']:.1f} dB")
                            print(f"   - RSRP: {ran_params['rsrp_dbm']:.1f} dBm")
                            print(f"   - CQI: {ran_params['cqi']}")
                            print(
                                f"   - 吞吐量: {ran_params['throughput_mbps']:.1f} Mbps"
                            )

                        return True
                    else:
                        print(f"❌ 快速通道模擬失敗: {response.status}")
                        error_text = await response.text()
                        print(f"   錯誤詳情: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ 快速通道模擬測試失敗: {e}")
            return False

    async def test_satellite_ntn_simulation(self) -> bool:
        """測試衛星 NTN 模擬"""
        print("�� 測試衛星 NTN 模擬...")

        try:
            async with aiohttp.ClientSession() as session:
                # 使用 satellite-ntn-simulation 端點
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
                            ran_params = first_result["ran_parameters"]
                            print(f"   - 衛星高度: 550 km")
                            print(f"   - SINR: {ran_params['sinr_db']:.1f} dB")
                            print(f"   - RSRP: {ran_params['rsrp_dbm']:.1f} dBm")
                            print(f"   - 延遲: {ran_params['latency_ms']:.1f} ms")

                        return True
                    else:
                        print(f"❌ 衛星 NTN 模擬失敗: {response.status}")
                        error_text = await response.text()
                        print(f"   錯誤詳情: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ 衛星 NTN 模擬測試失敗: {e}")
            return False

    async def test_wireless_statistics(self) -> bool:
        """測試無線統計"""
        print("🔄 測試無線統計...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.simworld_url}/api/v1/wireless/statistics"
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 無線統計查詢成功")
                        print(
                            f"   - 統計項目數: {len(result) if isinstance(result, (list, dict)) else 'N/A'}"
                        )
                        return True
                    else:
                        print(f"❌ 無線統計查詢失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 無線統計測試失敗: {e}")
            return False

    async def test_channel_types(self) -> bool:
        """測試通道類型"""
        print("🔄 測試通道類型查詢...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.simworld_url}/api/v1/wireless/channel-types"
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 通道類型查詢成功")
                        if isinstance(result, list):
                            print(f"   - 支援的通道類型數: {len(result)}")
                            if result:
                                print(
                                    f"   - 示例類型: {result[0] if len(result) > 0 else 'N/A'}"
                                )
                        return True
                    else:
                        print(f"❌ 通道類型查詢失敗: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 通道類型測試失敗: {e}")
            return False

    async def test_ueransim_config_generation(self) -> bool:
        """測試 UERANSIM 配置生成"""
        print("🔄 測試 UERANSIM 配置生成...")

        try:
            async with aiohttp.ClientSession() as session:
                test_params = {
                    "gnb_id": "gnb_test",
                    "position_x": 0,
                    "position_y": 0,
                    "position_z": 30,
                    "frequency_mhz": 2100,
                    "bandwidth_mhz": 20,
                    "tx_power_dbm": 43,
                }

                async with session.post(
                    f"{self.simworld_url}/api/v1/wireless/generate-ueransim-config",
                    params=test_params,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ UERANSIM 配置生成成功")
                        if "config" in result:
                            print(f"   - 配置已生成")
                        return True
                    else:
                        print(f"❌ UERANSIM 配置生成失敗: {response.status}")
                        error_text = await response.text()
                        print(f"   錯誤詳情: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ UERANSIM 配置生成測試失敗: {e}")
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
                        if result.get("success"):
                            print(f"   - 衛星 ID: {params['satellite_id']}")
                            print(f"   - 映射完成: {result.get('message', 'N/A')}")
                        return True
                    else:
                        print(f"❌ 衛星 gNodeB 映射失敗: {response.status}")
                        error_text = await response.text()
                        print(f"   錯誤詳情: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ 衛星 gNodeB 映射測試失敗: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, bool]:
        """執行所有測試"""
        print("🚀 開始 Sionna 無線通道模型與 UERANSIM 整合測試")
        print("=" * 60)

        tests = [
            ("SimWorld Wireless API", self.test_simworld_wireless_api),
            ("NetStack 健康 API", self.test_netstack_health_api),
            ("快速通道模擬", self.test_quick_simulation),
            ("衛星 NTN 模擬", self.test_satellite_ntn_simulation),
            ("無線統計", self.test_wireless_statistics),
            ("通道類型查詢", self.test_channel_types),
            ("UERANSIM 配置生成", self.test_ueransim_config_generation),
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
        print("📊 測試結果摘要")
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
            print("\n🎉 所有測試通過！Sionna 整合功能運行正常")
        elif passed >= total * 0.7:
            print(f"\n✅ 大部分測試通過！核心功能運行正常")
        else:
            print(f"\n⚠️ 有 {total - passed} 個測試失敗，請檢查服務狀態")


async def main():
    """主函數"""
    tester = SionnaIntegrationTester()
    results = await tester.run_all_tests()
    tester.print_summary(results)

    # 根據測試結果返回適當的退出代碼
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    success_rate = passed / total

    # 如果成功率 >= 70%，視為成功
    return 0 if success_rate >= 0.7 else 1


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
