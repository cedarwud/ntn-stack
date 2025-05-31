#!/usr/bin/env python3
"""
簡化的干擾控制系統測試

專注於驗證核心功能：
1. SimWorld 服務可用性
2. NetStack 服務可用性
3. 干擾模擬功能
4. AI-RAN 決策功能
5. 端到端整合
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


class SimpleInterferenceTest:
    """簡化的干擾控制測試"""

    SIMWORLD_BASE_URL = "http://localhost:8888"
    NETSTACK_BASE_URL = "http://localhost:8080"

    def __init__(self):
        self.results = []

    async def setup_session(self):
        """設置 HTTP 會話"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup_session(self):
        """清理 HTTP 會話"""
        if hasattr(self, "session"):
            await self.session.close()

    def log_result(self, test_name, success, message="", duration=0):
        """記錄測試結果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if message:
            print(f"    {message}")

        self.results.append(
            {
                "test": test_name,
                "success": success,
                "message": message,
                "duration": duration,
            }
        )

    async def test_simworld_health(self):
        """測試 SimWorld 服務健康狀態"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.SIMWORLD_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if "Sionna RT Simulation API" in data.get("message", ""):
                        self.log_result(
                            "SimWorld 健康檢查",
                            True,
                            "服務正常運行",
                            time.time() - start_time,
                        )
                        return True
                    else:
                        self.log_result(
                            "SimWorld 健康檢查",
                            False,
                            f"意外響應: {data}",
                            time.time() - start_time,
                        )
                        return False
                else:
                    self.log_result(
                        "SimWorld 健康檢查",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
                    return False
        except Exception as e:
            self.log_result(
                "SimWorld 健康檢查", False, f"連接錯誤: {e}", time.time() - start_time
            )
            return False

    async def test_netstack_health(self):
        """測試 NetStack 服務健康狀態"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.NETSTACK_BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("overall_status") == "healthy":
                        self.log_result(
                            "NetStack 健康檢查",
                            True,
                            "服務正常運行",
                            time.time() - start_time,
                        )
                        return True
                    else:
                        self.log_result(
                            "NetStack 健康檢查",
                            False,
                            f"狀態異常: {data}",
                            time.time() - start_time,
                        )
                        return False
                else:
                    self.log_result(
                        "NetStack 健康檢查",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
                    return False
        except Exception as e:
            self.log_result(
                "NetStack 健康檢查", False, f"連接錯誤: {e}", time.time() - start_time
            )
            return False

    async def test_interference_quick_test(self):
        """測試干擾快速測試功能"""
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.SIMWORLD_BASE_URL}/api/v1/interference/quick-test"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        # 檢查關鍵指標
                        sim_result = data.get("test_results", {}).get(
                            "interference_simulation", {}
                        )
                        ai_result = data.get("test_results", {}).get(
                            "ai_ran_response", {}
                        )

                        if sim_result.get("success") and ai_result.get("success"):
                            ai_time = ai_result.get("decision_time_ms", 0)
                            message = f"檢測到 {sim_result.get('detections', 0)} 個干擾，AI決策時間 {ai_time:.2f}ms"
                            self.log_result(
                                "干擾快速測試", True, message, time.time() - start_time
                            )
                            return True
                        else:
                            self.log_result(
                                "干擾快速測試",
                                False,
                                "模擬或AI決策失敗",
                                time.time() - start_time,
                            )
                            return False
                    else:
                        self.log_result(
                            "干擾快速測試",
                            False,
                            f"測試失敗: {data}",
                            time.time() - start_time,
                        )
                        return False
                else:
                    self.log_result(
                        "干擾快速測試",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
                    return False
        except Exception as e:
            self.log_result(
                "干擾快速測試", False, f"請求錯誤: {e}", time.time() - start_time
            )
            return False

    async def test_interference_scenarios(self):
        """測試干擾場景預設"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.SIMWORLD_BASE_URL}/api/v1/interference/scenarios/presets"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    presets = data.get("presets", {})
                    if len(presets) >= 3:
                        scenario_types = []
                        for name, scenario in presets.items():
                            jammers = scenario.get("jammer_configs", [])
                            for jammer in jammers:
                                scenario_types.append(jammer.get("type"))

                        message = f"發現 {len(presets)} 個預設場景，支援干擾類型: {set(scenario_types)}"
                        self.log_result(
                            "干擾場景預設", True, message, time.time() - start_time
                        )
                        return True
                    else:
                        self.log_result(
                            "干擾場景預設",
                            False,
                            f"場景數量不足: {len(presets)}",
                            time.time() - start_time,
                        )
                        return False
                else:
                    self.log_result(
                        "干擾場景預設",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
                    return False
        except Exception as e:
            self.log_result(
                "干擾場景預設", False, f"請求錯誤: {e}", time.time() - start_time
            )
            return False

    async def test_netstack_interference_status(self):
        """測試 NetStack 干擾控制狀態"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.NETSTACK_BASE_URL}/api/v1/interference/status"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        status = data.get("status", {})
                        service_name = status.get("service_name")
                        is_monitoring = status.get("is_monitoring")
                        message = f"服務: {service_name}, 監控狀態: {is_monitoring}"
                        self.log_result(
                            "NetStack 干擾控制狀態",
                            True,
                            message,
                            time.time() - start_time,
                        )
                        return True
                    else:
                        self.log_result(
                            "NetStack 干擾控制狀態",
                            False,
                            f"狀態異常: {data}",
                            time.time() - start_time,
                        )
                        return False
                else:
                    self.log_result(
                        "NetStack 干擾控制狀態",
                        False,
                        f"HTTP {response.status}",
                        time.time() - start_time,
                    )
                    return False
        except Exception as e:
            self.log_result(
                "NetStack 干擾控制狀態",
                False,
                f"連接錯誤: {e}",
                time.time() - start_time,
            )
            return False

    async def test_end_to_end_demo(self):
        """測試端到端演示（允許失敗）"""
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.NETSTACK_BASE_URL}/api/v1/interference/quick-demo"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        steps = data.get("demo_steps", {})
                        message = f"演示完成，包含 {len(steps)} 個步驟"
                        self.log_result(
                            "端到端演示", True, message, time.time() - start_time
                        )
                        return True
                    else:
                        self.log_result(
                            "端到端演示",
                            False,
                            f"演示失敗: {data.get('message', '未知錯誤')}",
                            time.time() - start_time,
                        )
                        return False
                else:
                    # 網路連接問題是預期的
                    self.log_result(
                        "端到端演示",
                        False,
                        f"網路連接問題 (HTTP {response.status})",
                        time.time() - start_time,
                    )
                    return False
        except Exception as e:
            self.log_result(
                "端到端演示", False, f"網路連接問題: {e}", time.time() - start_time
            )
            return False

    async def run_all_tests(self):
        """運行所有測試"""
        print("🔬 NTN Stack 干擾控制系統測試")
        print("=" * 60)

        await self.setup_session()

        try:
            # 基礎健康檢查
            simworld_ok = await self.test_simworld_health()
            netstack_ok = await self.test_netstack_health()

            # 如果基礎服務正常，繼續功能測試
            if simworld_ok:
                await self.test_interference_quick_test()
                await self.test_interference_scenarios()

            if netstack_ok:
                await self.test_netstack_interference_status()

            # 端到端測試（允許失敗）
            if simworld_ok and netstack_ok:
                await self.test_end_to_end_demo()

        finally:
            await self.cleanup_session()

    def print_summary(self):
        """打印測試摘要"""
        print("\n" + "=" * 60)
        print("📊 測試結果摘要")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"總測試數量: {total}")
        print(f"✅ 通過: {passed}")
        print(f"❌ 失敗: {failed}")
        print(f"📈 成功率: {success_rate:.1f}%")

        if failed > 0:
            print(f"\n❌ 失敗的測試:")
            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")


async def main():
    """主函數"""
    test = SimpleInterferenceTest()
    await test.run_all_tests()
    test.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
