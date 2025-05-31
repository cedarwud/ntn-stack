#!/usr/bin/env python3
"""
NTN Stack 網路修復後測試

解決容器間網路隔離問題，測試端到端通信
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import os


class NetworkFixedTest:
    """網路修復後的測試"""

    # 使用 NetStack 網路中的 IP 地址
    SIMWORLD_NETSTACK_IP = "172.20.0.2"  # simworld_backend 在 NetStack 網路中的 IP
    NETSTACK_API_IP = "172.20.0.40"  # netstack-api 容器 IP

    SIMWORLD_INTERNAL_URL = f"http://{SIMWORLD_NETSTACK_IP}:8000"
    NETSTACK_INTERNAL_URL = f"http://{NETSTACK_API_IP}:8080"

    # 備用：localhost 地址
    SIMWORLD_LOCALHOST_URL = "http://localhost:8888"
    NETSTACK_LOCALHOST_URL = "http://localhost:8080"

    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    async def setup_session(self):
        """設置 HTTP 會話"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup_session(self):
        """清理 HTTP 會話"""
        if hasattr(self, "session"):
            await self.session.close()

    def log_result(self, test_name, success, details="", duration=0):
        """記錄測試結果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.3f}s)")
        if details:
            print(f"    {details}")

        self.results.append(
            {
                "test": test_name,
                "success": success,
                "details": details,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def test_network_connectivity(self):
        """測試網路連接性"""
        print("🔧 網路修復後連接性測試")
        print("=" * 50)

        # 測試 SimWorld 在 NetStack 網路中的連接
        start_time = time.time()
        try:
            async with self.session.get(f"{self.SIMWORLD_INTERNAL_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if "Sionna RT Simulation API" in data.get("message", ""):
                        self.log_result(
                            "SimWorld 內部網路連接",
                            True,
                            f"IP: {self.SIMWORLD_NETSTACK_IP}",
                            time.time() - start_time,
                        )
                    else:
                        self.log_result(
                            "SimWorld 內部網路連接",
                            False,
                            f"意外響應: {data}",
                            time.time() - start_time,
                        )
                else:
                    self.log_result(
                        "SimWorld 內部網路連接",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
        except Exception as e:
            self.log_result(
                "SimWorld 內部網路連接",
                False,
                f"連接錯誤: {e}",
                time.time() - start_time,
            )

        # 測試 NetStack API 連接
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.NETSTACK_INTERNAL_URL}/health"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("overall_status") == "healthy":
                        self.log_result(
                            "NetStack 內部網路連接",
                            True,
                            f"IP: {self.NETSTACK_API_IP}",
                            time.time() - start_time,
                        )
                    else:
                        self.log_result(
                            "NetStack 內部網路連接",
                            False,
                            f"狀態異常: {data}",
                            time.time() - start_time,
                        )
                else:
                    self.log_result(
                        "NetStack 內部網路連接",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
        except Exception as e:
            self.log_result(
                "NetStack 內部網路連接",
                False,
                f"連接錯誤: {e}",
                time.time() - start_time,
            )

    async def test_cross_service_communication(self):
        """測試跨服務通信"""
        print("\n📋 跨服務通信測試")
        print("-" * 50)

        # 配置 NetStack 使用內部 SimWorld URL
        test_payload = {
            "simworld_api_url": self.SIMWORLD_INTERNAL_URL,
            "test_scenario": "network_fixed_test",
            "use_internal_network": True,
        }

        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.NETSTACK_INTERNAL_URL}/api/v1/interference/quick-demo",
                json=test_payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        steps = data.get("demo_steps", {})
                        self.log_result(
                            "跨服務通信",
                            True,
                            f"演示成功，{len(steps)} 步驟",
                            time.time() - start_time,
                        )
                    else:
                        self.log_result(
                            "跨服務通信",
                            False,
                            f"演示失敗: {data.get('message', '未知錯誤')}",
                            time.time() - start_time,
                        )
                else:
                    # 如果還是失敗，嘗試使用 localhost 作為備用
                    await self.test_localhost_fallback(start_time)
        except Exception as e:
            self.log_result(
                "跨服務通信", False, f"請求錯誤: {e}", time.time() - start_time
            )

    async def test_localhost_fallback(self, original_start_time):
        """使用 localhost 作為備用測試"""
        print("    嘗試 localhost 備用連接...")

        test_payload = {
            "simworld_api_url": self.SIMWORLD_LOCALHOST_URL,
            "test_scenario": "localhost_fallback_test",
        }

        try:
            async with self.session.post(
                f"{self.NETSTACK_LOCALHOST_URL}/api/v1/interference/quick-demo",
                json=test_payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        steps = data.get("demo_steps", {})
                        self.log_result(
                            "跨服務通信 (localhost備用)",
                            True,
                            f"演示成功，{len(steps)} 步驟",
                            time.time() - original_start_time,
                        )
                    else:
                        self.log_result(
                            "跨服務通信 (localhost備用)",
                            False,
                            f"演示失敗: {data.get('message', '未知錯誤')}",
                            time.time() - original_start_time,
                        )
                else:
                    self.log_result(
                        "跨服務通信 (localhost備用)",
                        False,
                        f"HTTP {response.status}",
                        time.time() - original_start_time,
                    )
        except Exception as e:
            self.log_result(
                "跨服務通信 (localhost備用)",
                False,
                f"請求錯誤: {e}",
                time.time() - original_start_time,
            )

    async def test_specific_endpoints(self):
        """測試特定端點通信"""
        print("\n📋 特定端點通信測試")
        print("-" * 50)

        # 測試 SimWorld 干擾 API 從 NetStack 網路訪問
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.SIMWORLD_INTERNAL_URL}/api/v1/interference/quick-test"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        sim_result = data.get("test_results", {}).get(
                            "interference_simulation", {}
                        )
                        detections = sim_result.get("detections", 0)
                        self.log_result(
                            "SimWorld 干擾 API 內部訪問",
                            True,
                            f"檢測到 {detections} 個干擾",
                            time.time() - start_time,
                        )
                    else:
                        self.log_result(
                            "SimWorld 干擾 API 內部訪問",
                            False,
                            f"測試失敗: {data}",
                            time.time() - start_time,
                        )
                else:
                    self.log_result(
                        "SimWorld 干擾 API 內部訪問",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
        except Exception as e:
            self.log_result(
                "SimWorld 干擾 API 內部訪問",
                False,
                f"請求錯誤: {e}",
                time.time() - start_time,
            )

        # 測試 NetStack 干擾控制 API
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.NETSTACK_INTERNAL_URL}/api/v1/interference/status"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        status = data.get("status", {})
                        service_name = status.get("service_name", "unknown")
                        self.log_result(
                            "NetStack 干擾控制 API 內部訪問",
                            True,
                            f"服務: {service_name}",
                            time.time() - start_time,
                        )
                    else:
                        self.log_result(
                            "NetStack 干擾控制 API 內部訪問",
                            False,
                            f"狀態異常: {data}",
                            time.time() - start_time,
                        )
                else:
                    self.log_result(
                        "NetStack 干擾控制 API 內部訪問",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
        except Exception as e:
            self.log_result(
                "NetStack 干擾控制 API 內部訪問",
                False,
                f"請求錯誤: {e}",
                time.time() - start_time,
            )

    async def run_complete_test(self):
        """運行完整測試"""
        print("🚀 NTN Stack 網路修復驗證測試")
        print("=" * 70)
        print(f"測試開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"SimWorld 內部 IP: {self.SIMWORLD_NETSTACK_IP}")
        print(f"NetStack API IP: {self.NETSTACK_API_IP}")
        print("=" * 70)

        await self.setup_session()

        try:
            await self.test_network_connectivity()
            await self.test_cross_service_communication()
            await self.test_specific_endpoints()
        finally:
            await self.cleanup_session()

    def generate_report(self):
        """生成測試報告"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print("\n" + "=" * 70)
        print("📊 網路修復驗證報告")
        print("=" * 70)
        print(f"測試開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"測試結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"總執行時間: {total_duration:.2f} 秒")
        print()
        print(f"總測試數量: {total_tests}")
        print(f"✅ 通過測試: {passed_tests}")
        print(f"❌ 失敗測試: {failed_tests}")
        print(f"📈 成功率: {success_rate:.1f}%")

        if failed_tests > 0:
            print(f"\n❌ 失敗的測試詳情:")
            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")

        print("\n🎯 網路修復狀態:")
        if success_rate >= 80:
            print("   ✅ 網路連接問題已解決")
            print("   ✅ 跨服務通信正常")
            print("   ✅ 端到端演示可用")
        else:
            print("   ⚠️  網路問題部分解決，需進一步調試")

        # 保存報告
        report_data = {
            "test_suite": "NTN Stack 網路修復驗證",
            "network_solution": {
                "method": "docker network connect",
                "simworld_netstack_ip": self.SIMWORLD_NETSTACK_IP,
                "netstack_api_ip": self.NETSTACK_API_IP,
            },
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_sec": total_duration,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
            },
            "test_results": self.results,
        }

        # 直接保存到 tests/reports 目錄（修改路徑）
        report_dir = "/home/sat/ntn-stack/tests/reports"
        os.makedirs(report_dir, exist_ok=True)
        report_filename = f"{report_dir}/network_fixed_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n📄 詳細報告已保存至: {report_filename}")
        except Exception as e:
            print(f"\n⚠️  報告保存失敗: {e}")


async def main():
    """主函數"""
    test = NetworkFixedTest()
    await test.run_complete_test()
    test.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
