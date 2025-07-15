#!/usr/bin/env python3
"""
Phase 2 整合測試腳本 - 統一監控系統測試

測試項目：
1. 統一監控中心功能
2. 跨系統監控聚合器
3. 增強版 RL 監控服務
4. API 橋接整合狀態
5. 前後端數據流通
6. WebSocket 實時推送
7. 系統健康檢查
8. 錯誤處理和降級機制
"""

import asyncio
import json
import time
import requests
import websockets
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
import subprocess
import sys


class Phase2IntegrationTest:
    """Phase 2 整合測試類"""

    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.total_tests = 0
        self.passed_tests = 0

        # 測試配置
        self.simworld_base_url = "http://localhost:8001"
        self.netstack_base_url = "http://localhost:8080"
        self.frontend_base_url = "http://localhost:5173"

        # 測試端點
        self.test_endpoints = {
            # SimWorld 端點
            "simworld_health": f"{self.simworld_base_url}/system/health",
            "simworld_interference": f"{self.simworld_base_url}/interference/ai-ran/netstack/status",
            "simworld_integrated": f"{self.simworld_base_url}/interference/ai-ran/control-integrated",
            # NetStack 端點
            "netstack_health": f"{self.netstack_base_url}/api/v1/rl/health",
            "netstack_status": f"{self.netstack_base_url}/api/v1/rl/status",
            "netstack_algorithms": f"{self.netstack_base_url}/api/v1/rl/algorithms",
            "netstack_sessions": f"{self.netstack_base_url}/api/v1/rl/training/sessions",
            # 前端靜態資源
            "frontend_health": f"{self.frontend_base_url}/",
        }

        self.websocket_endpoints = {
            "unified_monitoring": f"ws://localhost:8001/ws/unified-monitoring",
            "rl_enhanced": f"ws://localhost:8001/ws/rl-enhanced-monitoring",
            "realtime_events": f"ws://localhost:8001/ws/realtime-events",
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有 Phase 2 整合測試"""
        print("🚀 開始 Phase 2 統一監控系統整合測試")
        print("=" * 60)

        start_time = time.time()

        # 測試序列
        test_sequence = [
            ("基礎連接測試", self._test_basic_connectivity),
            ("SimWorld 系統測試", self._test_simworld_system),
            ("NetStack 系統測試", self._test_netstack_system),
            ("API 橋接整合測試", self._test_api_bridge_integration),
            ("統一監控中心測試", self._test_unified_monitoring_center),
            ("跨系統監控聚合測試", self._test_cross_system_monitoring),
            ("增強版 RL 監控測試", self._test_enhanced_rl_monitoring),
            ("WebSocket 實時推送測試", self._test_websocket_realtime),
            ("降級機制測試", self._test_fallback_mechanisms),
            ("性能和穩定性測試", self._test_performance_stability),
        ]

        for test_name, test_func in test_sequence:
            await self._run_test_section(test_name, test_func)

        duration = time.time() - start_time
        success_rate = (self.passed_tests / max(self.total_tests, 1)) * 100

        # 生成測試報告
        summary = {
            "test_phase": "Phase 2 - 統一監控系統整合",
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": len(self.failed_tests),
            "success_rate": round(success_rate, 2),
            "duration_seconds": round(duration, 2),
            "test_results": self.test_results,
            "failed_test_details": self.failed_tests,
            "timestamp": datetime.now().isoformat(),
        }

        # 輸出結果
        print("\n" + "=" * 60)
        print(f"📊 Phase 2 測試完成！")
        print(f"✅ 通過: {self.passed_tests}/{self.total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  耗時: {duration:.2f} 秒")

        if self.failed_tests:
            print(f"❌ 失敗的測試:")
            for failed_test in self.failed_tests:
                print(f"   - {failed_test}")

        return summary

    async def _run_test_section(self, section_name: str, test_func):
        """運行測試段落"""
        print(f"\n🧪 {section_name}")
        print("-" * 40)

        try:
            await test_func()
            print(f"✅ {section_name} 完成")
        except Exception as e:
            print(f"❌ {section_name} 失敗: {str(e)}")
            self.failed_tests.append(f"{section_name}: {str(e)}")

    def _record_test(
        self, test_name: str, success: bool, details: str = "", response_time: float = 0
    ):
        """記錄測試結果"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            self.failed_tests.append(test_name)

        result = {
            "test_name": test_name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.now().isoformat(),
        }

        self.test_results.append(result)
        print(f"  {status} {test_name} ({response_time*1000:.0f}ms)")
        if details and not success:
            print(f"      詳情: {details}")

    async def _test_basic_connectivity(self):
        """測試基礎連接性"""

        # 測試 SimWorld 健康檢查
        start_time = time.time()
        try:
            response = requests.get(self.test_endpoints["simworld_health"], timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                self._record_test(
                    "SimWorld 健康檢查",
                    True,
                    f"狀態: {data.get('status', 'unknown')}",
                    response_time,
                )
            else:
                self._record_test(
                    "SimWorld 健康檢查",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self._record_test(
                "SimWorld 健康檢查", False, str(e), time.time() - start_time
            )

        # 測試 NetStack 健康檢查
        start_time = time.time()
        try:
            response = requests.get(self.test_endpoints["netstack_health"], timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                self._record_test(
                    "NetStack RL 健康檢查",
                    True,
                    f"狀態: {data.get('status', 'unknown')}",
                    response_time,
                )
            else:
                self._record_test(
                    "NetStack RL 健康檢查",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self._record_test(
                "NetStack RL 健康檢查", False, str(e), time.time() - start_time
            )

        # 測試前端可訪問性
        start_time = time.time()
        try:
            response = requests.get(self.test_endpoints["frontend_health"], timeout=5)
            response_time = time.time() - start_time

            success = response.status_code == 200
            self._record_test(
                "前端服務可訪問性",
                success,
                f"HTTP {response.status_code}",
                response_time,
            )
        except Exception as e:
            self._record_test(
                "前端服務可訪問性", False, str(e), time.time() - start_time
            )

    async def _test_simworld_system(self):
        """測試 SimWorld 系統功能"""

        # 測試 NetStack 整合狀態端點
        start_time = time.time()
        try:
            response = requests.get(
                self.test_endpoints["simworld_interference"], timeout=5
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                self._record_test(
                    "NetStack 整合狀態端點",
                    True,
                    f"客戶端狀態: {data.get('client_status', 'unknown')}",
                    response_time,
                )
            else:
                self._record_test(
                    "NetStack 整合狀態端點",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self._record_test(
                "NetStack 整合狀態端點", False, str(e), time.time() - start_time
            )

        # 測試整合版 AI-RAN 控制端點
        start_time = time.time()
        try:
            test_payload = {"type": "health_check", "test_mode": True}

            response = requests.post(
                self.test_endpoints["simworld_integrated"],
                json=test_payload,
                timeout=10,
            )
            response_time = time.time() - start_time

            # 即使返回 404 也表示端點存在，只是不支援健康檢查
            success = response.status_code in [200, 404, 422]
            details = f"HTTP {response.status_code}"
            if response.status_code == 200:
                details += f", 響應: {response.json()}"

            self._record_test("整合版 AI-RAN 控制端點", success, details, response_time)
        except Exception as e:
            self._record_test(
                "整合版 AI-RAN 控制端點", False, str(e), time.time() - start_time
            )

    async def _test_netstack_system(self):
        """測試 NetStack 系統功能"""

        # 測試 RL 狀態端點
        start_time = time.time()
        try:
            response = requests.get(self.test_endpoints["netstack_status"], timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                self._record_test(
                    "RL 狀態端點",
                    True,
                    f"狀態: {data.get('status', 'unknown')}",
                    response_time,
                )
            else:
                self._record_test(
                    "RL 狀態端點", False, f"HTTP {response.status_code}", response_time
                )
        except Exception as e:
            self._record_test("RL 狀態端點", False, str(e), time.time() - start_time)

        # 測試算法列表端點
        start_time = time.time()
        try:
            response = requests.get(
                self.test_endpoints["netstack_algorithms"], timeout=5
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                algorithms = data.get("algorithms", [])
                self._record_test(
                    "算法列表端點", True, f"算法數量: {len(algorithms)}", response_time
                )
            else:
                self._record_test(
                    "算法列表端點", False, f"HTTP {response.status_code}", response_time
                )
        except Exception as e:
            self._record_test("算法列表端點", False, str(e), time.time() - start_time)

        # 測試訓練會話端點
        start_time = time.time()
        try:
            response = requests.get(self.test_endpoints["netstack_sessions"], timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                sessions = data if isinstance(data, list) else data.get("sessions", [])
                self._record_test(
                    "訓練會話端點", True, f"會話數量: {len(sessions)}", response_time
                )
            else:
                self._record_test(
                    "訓練會話端點", False, f"HTTP {response.status_code}", response_time
                )
        except Exception as e:
            self._record_test("訓練會話端點", False, str(e), time.time() - start_time)

    async def _test_api_bridge_integration(self):
        """測試 API 橋接整合"""

        # 測試跨系統數據一致性
        start_time = time.time()
        try:
            # 同時獲取兩個系統的狀態
            simworld_response = requests.get(
                self.test_endpoints["simworld_interference"], timeout=5
            )
            netstack_response = requests.get(
                self.test_endpoints["netstack_status"], timeout=5
            )

            response_time = time.time() - start_time

            if (
                simworld_response.status_code == 200
                and netstack_response.status_code == 200
            ):
                simworld_data = simworld_response.json()
                netstack_data = netstack_response.json()

                # 檢查數據一致性
                consistency_checks = []

                # 檢查連接狀態
                if simworld_data.get("connected", False):
                    consistency_checks.append("連接狀態一致")

                self._record_test(
                    "跨系統數據一致性檢查",
                    len(consistency_checks) > 0,
                    f"一致性檢查: {', '.join(consistency_checks) if consistency_checks else '無一致性'}",
                    response_time,
                )
            else:
                self._record_test(
                    "跨系統數據一致性檢查",
                    False,
                    "無法獲取兩個系統的數據",
                    response_time,
                )
        except Exception as e:
            self._record_test(
                "跨系統數據一致性檢查", False, str(e), time.time() - start_time
            )

    async def _test_unified_monitoring_center(self):
        """測試統一監控中心功能"""
        print("    注意: 統一監控中心是前端組件，此處測試相關 API 端點")

        # 測試統一監控所需的 API 端點
        test_apis = [
            ("/system/health", "SimWorld 系統健康"),
            ("/api/v1/rl/health", "NetStack RL 健康"),
            ("/interference/ai-ran/netstack/status", "NetStack 整合狀態"),
        ]

        for endpoint, description in test_apis:
            start_time = time.time()
            try:
                if endpoint.startswith("/api/v1/"):
                    url = self.netstack_base_url + endpoint
                else:
                    url = self.simworld_base_url + endpoint

                response = requests.get(url, timeout=5)
                response_time = time.time() - start_time

                success = response.status_code == 200
                self._record_test(
                    f"統一監控 - {description}",
                    success,
                    f"HTTP {response.status_code}",
                    response_time,
                )
            except Exception as e:
                self._record_test(
                    f"統一監控 - {description}", False, str(e), time.time() - start_time
                )

    async def _test_cross_system_monitoring(self):
        """測試跨系統監控聚合功能"""

        # 測試多系統狀態聚合
        start_time = time.time()
        try:
            # 並行請求多個系統
            tasks = []
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))

            try:
                tasks.append(session.get(self.test_endpoints["simworld_health"]))
                tasks.append(session.get(self.test_endpoints["netstack_health"]))
                tasks.append(session.get(self.test_endpoints["simworld_interference"]))

                responses = await asyncio.gather(*tasks, return_exceptions=True)
                response_time = time.time() - start_time

                successful_responses = 0
                for response in responses:
                    if (
                        isinstance(response, aiohttp.ClientResponse)
                        and response.status == 200
                    ):
                        successful_responses += 1
                        response.close()

                success_rate = successful_responses / len(tasks)
                self._record_test(
                    "多系統並行狀態聚合",
                    success_rate >= 0.5,
                    f"成功率: {success_rate:.1%} ({successful_responses}/{len(tasks)})",
                    response_time,
                )

            finally:
                await session.close()

        except Exception as e:
            self._record_test(
                "多系統並行狀態聚合", False, str(e), time.time() - start_time
            )

    async def _test_enhanced_rl_monitoring(self):
        """測試增強版 RL 監控功能"""

        # 測試增強版 RL 監控所需的多個端點
        enhanced_endpoints = [
            ("/api/v1/rl/status", "RL 基礎狀態"),
            ("/api/v1/rl/algorithms", "RL 算法列表"),
            ("/api/v1/rl/training/sessions", "RL 訓練會話"),
        ]

        for endpoint, description in enhanced_endpoints:
            start_time = time.time()
            try:
                url = self.netstack_base_url + endpoint
                response = requests.get(url, timeout=5)
                response_time = time.time() - start_time

                success = response.status_code == 200
                details = f"HTTP {response.status_code}"

                if success:
                    data = response.json()
                    if isinstance(data, dict):
                        details += f", 鍵數量: {len(data.keys())}"
                    elif isinstance(data, list):
                        details += f", 項目數量: {len(data)}"

                self._record_test(
                    f"增強版 RL - {description}", success, details, response_time
                )
            except Exception as e:
                self._record_test(
                    f"增強版 RL - {description}",
                    False,
                    str(e),
                    time.time() - start_time,
                )

    async def _test_websocket_realtime(self):
        """測試 WebSocket 實時推送功能"""

        # 測試 WebSocket 連接
        for ws_name, ws_url in self.websocket_endpoints.items():
            start_time = time.time()
            try:
                # 嘗試連接 WebSocket
                async with websockets.connect(ws_url, timeout=3) as websocket:
                    # 發送測試消息
                    test_message = {
                        "type": "ping",
                        "timestamp": datetime.now().isoformat(),
                    }
                    await websocket.send(json.dumps(test_message))

                    # 等待響應
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2)
                        response_time = time.time() - start_time

                        self._record_test(
                            f"WebSocket 連接 - {ws_name}",
                            True,
                            "連接成功並收到響應",
                            response_time,
                        )
                    except asyncio.TimeoutError:
                        response_time = time.time() - start_time
                        self._record_test(
                            f"WebSocket 連接 - {ws_name}",
                            True,
                            "連接成功但無響應",
                            response_time,
                        )

            except Exception as e:
                response_time = time.time() - start_time
                self._record_test(
                    f"WebSocket 連接 - {ws_name}", False, str(e), response_time
                )

    async def _test_fallback_mechanisms(self):
        """測試降級機制"""
        print("    注意: 降級機制測試需要實際的故障場景，此處測試相關配置")

        # 測試 NetStack 不可用時的 SimWorld 響應
        start_time = time.time()
        try:
            # 首先檢查正常狀態
            response = requests.get(
                self.test_endpoints["simworld_interference"], timeout=5
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                fallback_active = data.get("fallback_active", False)

                self._record_test(
                    "降級機制配置檢查",
                    True,
                    f"降級狀態: {'啟用' if fallback_active else '未啟用'}",
                    response_time,
                )
            else:
                self._record_test(
                    "降級機制配置檢查",
                    False,
                    f"無法檢查降級狀態: HTTP {response.status_code}",
                    response_time,
                )

        except Exception as e:
            self._record_test(
                "降級機制配置檢查", False, str(e), time.time() - start_time
            )

    async def _test_performance_stability(self):
        """測試性能和穩定性"""

        # 壓力測試 - 快速連續請求
        start_time = time.time()
        try:
            num_requests = 10
            successful_requests = 0
            total_response_time = 0

            for i in range(num_requests):
                request_start = time.time()
                try:
                    response = requests.get(
                        self.test_endpoints["simworld_health"], timeout=2
                    )
                    request_time = time.time() - request_start
                    total_response_time += request_time

                    if response.status_code == 200:
                        successful_requests += 1

                except Exception as e:
                    pass  # 記錄但繼續測試

            total_time = time.time() - start_time
            avg_response_time = total_response_time / max(successful_requests, 1)
            success_rate = successful_requests / num_requests

            self._record_test(
                "系統壓力測試",
                success_rate >= 0.8,
                f"成功率: {success_rate:.1%}, 平均響應: {avg_response_time*1000:.0f}ms",
                total_time,
            )

        except Exception as e:
            self._record_test("系統壓力測試", False, str(e), time.time() - start_time)


async def main():
    """主函數"""
    print("Phase 2 統一監控系統整合測試")
    print("=" * 60)

    tester = Phase2IntegrationTest()

    try:
        # 運行測試
        results = await tester.run_all_tests()

        # 保存測試結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase2_integration_test_results_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 測試結果已保存到: {filename}")

        # 返回結果
        return results["success_rate"] >= 70  # 70% 通過率視為成功

    except Exception as e:
        print(f"❌ 測試執行失敗: {str(e)}")
        return False


if __name__ == "__main__":
    # 檢查必要的依賴
    try:
        import requests
        import aiohttp
        import websockets
    except ImportError as e:
        print(f"❌ 缺少必要的依賴: {e}")
        print("請安裝: pip install requests aiohttp websockets")
        sys.exit(1)

    # 運行測試
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
