#!/usr/bin/env python3
"""
Tier-1 Mesh 網路與 5G 核心網橋接功能整合測試

測試完整的 Mesh 橋接功能，包括節點管理、網關創建、封包轉發、
路由優化等所有核心功能。
"""

import asyncio
import json
import pytest
import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import uuid

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeshBridgeIntegrationTest:
    """Mesh 橋接功能整合測試"""

    def __init__(self):
        self.netstack_url = "http://localhost:8080"
        self.test_nodes: List[Dict[str, Any]] = []
        self.test_gateways: List[Dict[str, Any]] = []
        self.client = httpx.AsyncClient(timeout=30.0)

    async def run_all_tests(self) -> bool:
        """執行所有測試"""
        test_results = []

        try:
            logger.info("🧪 開始 Mesh 橋接功能整合測試...")

            # 測試順序很重要，後續測試依賴前面的結果
            tests = [
                ("服務健康檢查", self._test_service_health),
                ("Mesh 節點創建", self._test_mesh_node_creation),
                ("Mesh 節點管理", self._test_mesh_node_management),
                ("橋接網關創建", self._test_bridge_gateway_creation),
                ("橋接網關管理", self._test_bridge_gateway_management),
                ("網路拓撲獲取", self._test_network_topology),
                ("性能指標監控", self._test_performance_metrics),
                ("路由優化", self._test_route_optimization),
                ("封包轉發模擬", self._test_packet_forwarding),
                ("快速演示", self._test_quick_demo),
                ("負載測試", self._test_load_testing),
                ("故障恢復", self._test_fault_recovery),
            ]

            for test_name, test_func in tests:
                logger.info(f"🔍 執行測試: {test_name}")
                try:
                    result = await test_func()
                    test_results.append({"test": test_name, "passed": result})
                    logger.info(
                        f"{'✅' if result else '❌'} {test_name}: {'通過' if result else '失敗'}"
                    )
                except Exception as e:
                    logger.error(f"❌ {test_name} 執行異常: {e}")
                    test_results.append(
                        {"test": test_name, "passed": False, "error": str(e)}
                    )

            # 清理測試資源
            await self._cleanup_test_resources()

            # 統計結果
            passed_tests = sum(1 for result in test_results if result["passed"])
            total_tests = len(test_results)
            success_rate = (passed_tests / total_tests) * 100

            logger.info(f"📊 測試結果統計:")
            logger.info(f"   通過: {passed_tests}/{total_tests} ({success_rate:.1f}%)")

            if success_rate < 100:
                logger.error("❌ 部分測試失敗:")
                for result in test_results:
                    if not result["passed"]:
                        error_msg = result.get("error", "未知錯誤")
                        logger.error(f"   - {result['test']}: {error_msg}")

            return success_rate == 100

        except Exception as e:
            logger.error(f"❌ 測試執行異常: {e}")
            return False
        finally:
            await self.client.aclose()

    async def _test_service_health(self) -> bool:
        """測試服務健康狀態"""
        try:
            # 檢查 NetStack API 健康狀態
            response = await self.client.get(f"{self.netstack_url}/health")
            if response.status_code != 200:
                logger.error(f"健康檢查失敗: {response.status_code}")
                return False

            health_data = response.json()
            if health_data.get("overall_status") != "healthy":
                logger.error(f"系統狀態不健康: {health_data}")
                return False

            logger.info("✅ 服務健康狀態正常")
            return True

        except Exception as e:
            logger.error(f"健康檢查異常: {e}")
            return False

    async def _test_mesh_node_creation(self) -> bool:
        """測試 Mesh 節點創建"""
        try:
            # 創建多種類型的 Mesh 節點
            node_configs = [
                {
                    "name": "測試UAV中繼節點",
                    "node_type": "uav_relay",
                    "ip_address": "192.168.100.10",
                    "mac_address": "00:11:22:33:44:10",
                    "frequency_mhz": 900.0,
                    "power_dbm": 20.0,
                    "position": {
                        "latitude": 25.0330,
                        "longitude": 121.5654,
                        "altitude": 100.0,
                    },
                },
                {
                    "name": "測試地面基站",
                    "node_type": "ground_station",
                    "ip_address": "192.168.100.11",
                    "mac_address": "00:11:22:33:44:11",
                    "frequency_mhz": 900.0,
                    "power_dbm": 25.0,
                    "position": {
                        "latitude": 25.0400,
                        "longitude": 121.5700,
                        "altitude": 10.0,
                    },
                },
                {
                    "name": "測試移動單元",
                    "node_type": "mobile_unit",
                    "ip_address": "192.168.100.12",
                    "mac_address": "00:11:22:33:44:12",
                    "frequency_mhz": 900.0,
                    "power_dbm": 15.0,
                },
            ]

            created_nodes = []
            for config in node_configs:
                response = await self.client.post(
                    f"{self.netstack_url}/api/v1/mesh/nodes", json=config
                )

                if response.status_code != 201:
                    logger.error(
                        f"創建節點失敗: {response.status_code}, {response.text}"
                    )
                    return False

                node_data = response.json()
                created_nodes.append(node_data)
                self.test_nodes.append(node_data)

                logger.info(
                    f"成功創建節點: {node_data['name']} ({node_data['node_id']})"
                )

            # 驗證節點列表
            response = await self.client.get(f"{self.netstack_url}/api/v1/mesh/nodes")
            if response.status_code != 200:
                logger.error("獲取節點列表失敗")
                return False

            nodes_list = response.json()
            if nodes_list["total_count"] < len(created_nodes):
                logger.error("節點列表數量不符")
                return False

            logger.info(f"✅ 成功創建 {len(created_nodes)} 個 Mesh 節點")
            return True

        except Exception as e:
            logger.error(f"Mesh 節點創建測試失敗: {e}")
            return False

    async def _test_mesh_node_management(self) -> bool:
        """測試 Mesh 節點管理功能"""
        try:
            if not self.test_nodes:
                logger.error("沒有可測試的節點")
                return False

            test_node = self.test_nodes[0]
            node_id = test_node["node_id"]

            # 測試獲取單個節點
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/mesh/nodes/{node_id}"
            )
            if response.status_code != 200:
                logger.error("獲取單個節點失敗")
                return False

            # 測試節點更新
            update_data = {
                "name": "更新後的節點名稱",
                "status": "active",
                "power_dbm": 22.0,
            }

            response = await self.client.put(
                f"{self.netstack_url}/api/v1/mesh/nodes/{node_id}", json=update_data
            )
            if response.status_code != 200:
                logger.error("更新節點失敗")
                return False

            updated_node = response.json()
            if updated_node["name"] != update_data["name"]:
                logger.error("節點更新內容不正確")
                return False

            logger.info("✅ Mesh 節點管理功能正常")
            return True

        except Exception as e:
            logger.error(f"Mesh 節點管理測試失敗: {e}")
            return False

    async def _test_bridge_gateway_creation(self) -> bool:
        """測試橋接網關創建"""
        try:
            if not self.test_nodes:
                logger.error("沒有可用的 Mesh 節點")
                return False

            # 為每個節點創建橋接網關
            gateway_configs = [
                {
                    "name": "主橋接網關",
                    "upf_ip": "172.20.0.30",
                    "upf_port": 2152,
                    "mesh_node_id": self.test_nodes[0]["node_id"],
                    "mesh_interface": "mesh0",
                    "slice_info": {
                        "supported_slices": [
                            {"sst": 1, "sd": "0x111111"},
                            {"sst": 2, "sd": "0x222222"},
                        ]
                    },
                },
                {
                    "name": "備援橋接網關",
                    "upf_ip": "172.20.0.31",
                    "upf_port": 2152,
                    "mesh_node_id": (
                        self.test_nodes[1]["node_id"]
                        if len(self.test_nodes) > 1
                        else self.test_nodes[0]["node_id"]
                    ),
                    "mesh_interface": "mesh1",
                },
            ]

            created_gateways = []
            for config in gateway_configs:
                response = await self.client.post(
                    f"{self.netstack_url}/api/v1/mesh/gateways", json=config
                )

                if response.status_code != 201:
                    logger.error(
                        f"創建橋接網關失敗: {response.status_code}, {response.text}"
                    )
                    return False

                gateway_data = response.json()
                created_gateways.append(gateway_data)
                self.test_gateways.append(gateway_data)

                logger.info(
                    f"成功創建橋接網關: {gateway_data['name']} ({gateway_data['gateway_id']})"
                )

            # 驗證網關列表
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/mesh/gateways"
            )
            if response.status_code != 200:
                logger.error("獲取網關列表失敗")
                return False

            gateways_list = response.json()
            if gateways_list["total_count"] < len(created_gateways):
                logger.error("網關列表數量不符")
                return False

            logger.info(f"✅ 成功創建 {len(created_gateways)} 個橋接網關")
            return True

        except Exception as e:
            logger.error(f"橋接網關創建測試失敗: {e}")
            return False

    async def _test_bridge_gateway_management(self) -> bool:
        """測試橋接網關管理功能"""
        try:
            if not self.test_gateways:
                logger.error("沒有可測試的網關")
                return False

            test_gateway = self.test_gateways[0]
            gateway_id = test_gateway["gateway_id"]

            # 測試獲取單個網關
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/mesh/gateways/{gateway_id}"
            )
            if response.status_code != 200:
                logger.error("獲取單個網關失敗")
                return False

            gateway_data = response.json()
            if gateway_data["gateway_id"] != gateway_id:
                logger.error("網關數據不正確")
                return False

            logger.info("✅ 橋接網關管理功能正常")
            return True

        except Exception as e:
            logger.error(f"橋接網關管理測試失敗: {e}")
            return False

    async def _test_network_topology(self) -> bool:
        """測試網路拓撲獲取"""
        try:
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/mesh/topology"
            )
            if response.status_code != 200:
                logger.error("獲取網路拓撲失敗")
                return False

            topology_data = response.json()

            # 驗證拓撲數據結構
            required_fields = [
                "topology",
                "health_score",
                "connectivity_ratio",
                "average_link_quality",
            ]
            for field in required_fields:
                if field not in topology_data:
                    logger.error(f"拓撲數據缺少字段: {field}")
                    return False

            topology = topology_data["topology"]
            if len(topology["nodes"]) < len(self.test_nodes):
                logger.error("拓撲中節點數量不足")
                return False

            if len(topology["gateways"]) < len(self.test_gateways):
                logger.error("拓撲中網關數量不足")
                return False

            logger.info(
                f"✅ 網路拓撲正常 - 節點: {len(topology['nodes'])}, 網關: {len(topology['gateways'])}"
            )
            return True

        except Exception as e:
            logger.error(f"網路拓撲測試失敗: {e}")
            return False

    async def _test_performance_metrics(self) -> bool:
        """測試性能指標監控"""
        try:
            if not self.test_nodes:
                logger.error("沒有可測試的節點")
                return False

            # 測試每個節點的性能指標
            for node in self.test_nodes:
                node_id = node["node_id"]

                response = await self.client.get(
                    f"{self.netstack_url}/api/v1/mesh/nodes/{node_id}/metrics"
                )

                if response.status_code != 200:
                    logger.error(f"獲取節點 {node_id} 性能指標失敗")
                    return False

                metrics_data = response.json()

                # 驗證指標數據結構
                required_metrics = [
                    "node_id",
                    "total_packets_sent",
                    "total_packets_received",
                    "average_rssi_dbm",
                    "average_latency_ms",
                    "packet_loss_ratio",
                ]

                for metric in required_metrics:
                    if metric not in metrics_data:
                        logger.error(f"性能指標缺少字段: {metric}")
                        return False

            logger.info("✅ 性能指標監控正常")
            return True

        except Exception as e:
            logger.error(f"性能指標測試失敗: {e}")
            return False

    async def _test_route_optimization(self) -> bool:
        """測試路由優化"""
        try:
            # 測試全局路由優化
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/mesh/routing/optimize"
            )
            if response.status_code != 200:
                logger.error("全局路由優化失敗")
                return False

            optimize_result = response.json()
            if "message" not in optimize_result:
                logger.error("路由優化響應格式不正確")
                return False

            # 測試針對特定節點的路由優化
            if self.test_nodes:
                node_id = self.test_nodes[0]["node_id"]
                response = await self.client.post(
                    f"{self.netstack_url}/api/v1/mesh/routing/optimize",
                    params={"target_node_id": node_id},
                )
                if response.status_code != 200:
                    logger.error("特定節點路由優化失敗")
                    return False

            logger.info("✅ 路由優化功能正常")
            return True

        except Exception as e:
            logger.error(f"路由優化測試失敗: {e}")
            return False

    async def _test_packet_forwarding(self) -> bool:
        """測試封包轉發功能（模擬）"""
        try:
            # 這裡測試封包轉發相關的 API 接口
            # 實際的封包轉發是在服務內部進行的

            if not self.test_gateways or not self.test_nodes:
                logger.error("沒有可用的網關或節點")
                return False

            # 模擬測試：檢查網關和節點的連接狀態
            for gateway in self.test_gateways:
                gateway_id = gateway["gateway_id"]

                response = await self.client.get(
                    f"{self.netstack_url}/api/v1/mesh/gateways/{gateway_id}"
                )

                if response.status_code != 200:
                    logger.error(f"檢查網關 {gateway_id} 狀態失敗")
                    return False

                gateway_data = response.json()
                # 網關應該處於可轉發狀態
                if not gateway_data.get("packet_forwarding_enabled", False):
                    logger.warning(f"網關 {gateway_id} 封包轉發未啟用")

            logger.info("✅ 封包轉發相關檢查通過")
            return True

        except Exception as e:
            logger.error(f"封包轉發測試失敗: {e}")
            return False

    async def _test_quick_demo(self) -> bool:
        """測試快速演示功能"""
        try:
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/mesh/demo/quick-test"
            )
            if response.status_code != 200:
                logger.error("快速演示失敗")
                return False

            demo_result = response.json()

            # 驗證演示結果
            if not demo_result.get("message"):
                logger.error("演示結果格式不正確")
                return False

            demo_data = demo_result.get("demo_results", {})
            if "node_created" not in demo_data or "gateway_created" not in demo_data:
                logger.error("演示結果缺少必要數據")
                return False

            logger.info("✅ 快速演示功能正常")
            return True

        except Exception as e:
            logger.error(f"快速演示測試失敗: {e}")
            return False

    async def _test_load_testing(self) -> bool:
        """測試負載情況"""
        try:
            # 並發測試多個 API 請求
            tasks = []

            # 同時請求多個節點的性能指標
            for node in self.test_nodes:
                node_id = node["node_id"]
                task = self.client.get(
                    f"{self.netstack_url}/api/v1/mesh/nodes/{node_id}/metrics"
                )
                tasks.append(task)

            # 同時請求多個網關狀態
            for gateway in self.test_gateways:
                gateway_id = gateway["gateway_id"]
                task = self.client.get(
                    f"{self.netstack_url}/api/v1/mesh/gateways/{gateway_id}"
                )
                tasks.append(task)

            # 執行並發請求
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 檢查結果
            success_count = 0
            for result in results:
                if (
                    not isinstance(result, Exception)
                    and hasattr(result, "status_code")
                    and result.status_code == 200
                ):
                    success_count += 1

            success_rate = (success_count / len(results)) * 100
            if success_rate < 80:  # 允許 20% 的失敗率
                logger.error(f"負載測試成功率過低: {success_rate:.1f}%")
                return False

            logger.info(f"✅ 負載測試通過，成功率: {success_rate:.1f}%")
            return True

        except Exception as e:
            logger.error(f"負載測試失敗: {e}")
            return False

    async def _test_fault_recovery(self) -> bool:
        """測試故障恢復能力"""
        try:
            if not self.test_nodes:
                logger.error("沒有可測試的節點")
                return False

            # 模擬節點故障：將節點狀態設為 maintenance
            test_node = self.test_nodes[0]
            node_id = test_node["node_id"]

            # 設置節點為維護狀態
            update_data = {"status": "maintenance"}
            response = await self.client.put(
                f"{self.netstack_url}/api/v1/mesh/nodes/{node_id}", json=update_data
            )

            if response.status_code != 200:
                logger.error("設置節點維護狀態失敗")
                return False

            # 觸發路由優化以處理故障節點
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/mesh/routing/optimize"
            )
            if response.status_code != 200:
                logger.error("故障後路由優化失敗")
                return False

            # 恢復節點狀態
            update_data = {"status": "active"}
            response = await self.client.put(
                f"{self.netstack_url}/api/v1/mesh/nodes/{node_id}", json=update_data
            )

            if response.status_code != 200:
                logger.error("恢復節點狀態失敗")
                return False

            logger.info("✅ 故障恢復測試通過")
            return True

        except Exception as e:
            logger.error(f"故障恢復測試失敗: {e}")
            return False

    async def _cleanup_test_resources(self):
        """清理測試資源"""
        try:
            logger.info("🧹 清理測試資源...")

            # 刪除測試節點
            for node in self.test_nodes:
                try:
                    node_id = node["node_id"]
                    response = await self.client.delete(
                        f"{self.netstack_url}/api/v1/mesh/nodes/{node_id}"
                    )
                    if response.status_code == 200:
                        logger.info(f"已刪除測試節點: {node_id}")
                except Exception as e:
                    logger.warning(f"刪除測試節點失敗: {e}")

            # 注意：橋接網關通常會在節點刪除時自動清理，
            # 或者可以通過 Mesh 服務的內部邏輯處理

            logger.info("✅ 測試資源清理完成")

        except Exception as e:
            logger.error(f"清理測試資源失敗: {e}")


async def main():
    """主測試函數"""
    test_suite = MeshBridgeIntegrationTest()
    success = await test_suite.run_all_tests()

    if success:
        print("\n🎉 所有 Mesh 橋接功能測試通過！")
        return 0
    else:
        print("\n❌ 部分測試失敗，請檢查日誌")
        return 1


if __name__ == "__main__":
    import sys

    result = asyncio.run(main())
    sys.exit(result)
