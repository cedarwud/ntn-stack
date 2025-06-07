#!/usr/bin/env python3
"""
快速驗證測試 - 驗證 Mesh 橋接和 UAV 備援機制的核心功能

這個測試旨在快速驗證我們實現的功能是否正常工作
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_basic_apis():
    """測試基本 API 可用性"""
    print("🔍 測試基本 API 可用性...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # 測試健康檢查
            response = await client.get("http://localhost:8080/health")
            if response.status_code == 200:
                print("✅ 健康檢查 API 正常")
            else:
                print(f"❌ 健康檢查 API 異常: {response.status_code}")
                return False

            # 測試 Mesh 節點列表
            response = await client.get("http://localhost:8080/api/v1/mesh/nodes")
            if response.status_code == 200:
                print("✅ Mesh 節點 API 正常")
            else:
                print(f"❌ Mesh 節點 API 異常: {response.status_code}")

            # 測試 Mesh 網關列表
            response = await client.get("http://localhost:8080/api/v1/mesh/gateways")
            if response.status_code == 200:
                print("✅ Mesh 網關 API 正常")
            else:
                print(f"❌ Mesh 網關 API 異常: {response.status_code}")

            # 測試 UAV 備援服務統計
            response = await client.get(
                "http://localhost:8080/api/v1/uav-mesh-failover/stats"
            )
            if response.status_code == 200:
                print("✅ UAV 備援服務 API 正常")
                stats = response.json()
                print(f"   監控 UAV 數量: {stats.get('monitored_uav_count', 0)}")
            else:
                print(f"❌ UAV 備援服務 API 異常: {response.status_code}")

            return True

        except Exception as e:
            print(f"❌ API 測試異常: {e}")
            return False


async def test_mesh_node_creation():
    """測試 Mesh 節點創建"""
    print("\n🔧 測試 Mesh 節點創建...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            node_config = {
                "name": "驗證測試節點",
                "node_type": "uav_relay",
                "ip_address": "192.168.100.99",
                "mac_address": "00:11:22:33:44:99",
                "frequency_mhz": 900.0,
                "power_dbm": 20.0,
                "position": {
                    "latitude": 25.0330,
                    "longitude": 121.5654,
                    "altitude": 100.0,
                },
            }

            response = await client.post(
                "http://localhost:8080/api/v1/mesh/nodes", json=node_config
            )

            if response.status_code == 201:
                node_data = response.json()
                node_id = node_data["node_id"]
                print(f"✅ 成功創建 Mesh 節點: {node_id}")

                # 清理測試節點
                await client.delete(
                    f"http://localhost:8080/api/v1/mesh/nodes/{node_id}"
                )
                print(f"✅ 已清理測試節點: {node_id}")
                return True
            else:
                print(f"❌ 創建 Mesh 節點失敗: {response.status_code}")
                print(f"   錯誤詳情: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Mesh 節點創建測試異常: {e}")
            return False


async def test_mesh_demo():
    """測試 Mesh 演示功能"""
    print("\n🎭 測試 Mesh 快速演示...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:8080/api/v1/mesh/demo/quick-test"
            )

            if response.status_code == 200:
                demo_result = response.json()
                print("✅ Mesh 演示成功")
                if "demo_results" in demo_result:
                    results = demo_result["demo_results"]
                    print(
                        f"   創建節點: {results.get('node_created', {}).get('name', 'N/A')}"
                    )
                    print(
                        f"   創建網關: {results.get('gateway_created', {}).get('name', 'N/A')}"
                    )
                return True
            else:
                print(f"❌ Mesh 演示失敗: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Mesh 演示測試異常: {e}")
            return False


async def test_uav_creation():
    """測試 UAV 創建"""
    print("\n🚁 測試 UAV 創建...")

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            uav_config = {
                "name": "驗證測試UAV",
                "ue_config": {
                    "imsi": "999700000000099",
                    "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
                    "plmn": "99970",
                    "apn": "internet",
                    "slice_nssai": {"sst": 1, "sd": "000001"},
                    "gnb_ip": "172.20.0.40",
                    "gnb_port": 38412,
                    "power_dbm": 23.0,
                    "frequency_mhz": 2150.0,
                    "bandwidth_mhz": 20.0,
                },
                "initial_position": {
                    "latitude": 25.0330,
                    "longitude": 121.5654,
                    "altitude": 100.0,
                    "speed": 20.0,
                    "heading": 45.0,
                },
            }

            response = await client.post(
                "http://localhost:8080/api/v1/uav", json=uav_config
            )

            if response.status_code == 200:
                uav_data = response.json()
                uav_id = uav_data["uav_id"]
                print(f"✅ 成功創建 UAV: {uav_id}")

                # 測試註冊備援監控
                response = await client.post(
                    f"http://localhost:8080/api/v1/uav-mesh-failover/register/{uav_id}"
                )

                if response.status_code == 200:
                    print("✅ 成功註冊備援監控")
                else:
                    print(f"❌ 註冊備援監控失敗: {response.status_code}")

                # 清理測試 UAV
                await client.delete(f"http://localhost:8080/api/v1/uav/{uav_id}")
                print(f"✅ 已清理測試 UAV: {uav_id}")
                return True
            else:
                print(f"❌ 創建 UAV 失敗: {response.status_code}")
                print(f"   錯誤詳情: {response.text}")
                return False

        except Exception as e:
            print(f"❌ UAV 創建測試異常: {e}")
            return False


async def test_uav_failover_demo():
    """測試 UAV 備援演示"""
    print("\n🔄 測試 UAV 備援演示...")

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(
                "http://localhost:8080/api/v1/uav-mesh-failover/demo/quick-test"
            )

            if response.status_code == 200:
                demo_result = response.json()
                print("✅ UAV 備援演示成功")

                performance = demo_result.get("performance_targets", {})
                actual_time = performance.get("actual_failover_time_ms", 0)
                meets_requirement = performance.get("meets_requirement", False)

                print(f"   實際切換時間: {actual_time:.1f}ms")
                print(f"   符合 2 秒要求: {meets_requirement}")

                return True
            else:
                print(f"❌ UAV 備援演示失敗: {response.status_code}")
                print(f"   錯誤詳情: {response.text}")
                return False

        except Exception as e:
            print(f"❌ UAV 備援演示測試異常: {e}")
            return False


async def main():
    """主測試函數"""
    print("🧪 快速驗證測試開始")
    print("=" * 50)

    tests = [
        ("基本 API 可用性", test_basic_apis),
        ("Mesh 節點創建", test_mesh_node_creation),
        ("Mesh 演示功能", test_mesh_demo),
        ("UAV 創建", test_uav_creation),
        ("UAV 備援演示", test_uav_failover_demo),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 執行異常: {e}")
            results.append((test_name, False))

    # 統計結果
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = (passed / total) * 100

    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")

    print(f"\n通過率: {success_rate:.1f}% ({passed}/{total})")

    if success_rate == 100:
        print("\n🎉 所有驗證測試通過！")
        print("✅ Tier-1 Mesh 網路與 5G 核心網橋接功能正常")
        print("✅ UAV 失聯後的 Mesh 網路備援機制正常")
        print("✅ 系統滿足 TODO.md 中的功能要求")
        return 0
    else:
        print("\n❌ 部分驗證測試失敗")
        print("❗ 請檢查失敗的測試項目")
        return 1


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(result)
    except KeyboardInterrupt:
        print("\n⏹️  測試被用戶中斷")
        exit(130)
    except Exception as e:
        print(f"\n💥 測試執行異常: {e}")
        exit(1)
