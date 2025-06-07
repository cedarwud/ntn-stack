#!/usr/bin/env python3
"""
衛星失聯到 Mesh 備援測試場景
實現 TODO.md 中的場景3：衛星失聯切換到 Mesh 場景
驗證網路備援機制和恢復時間（2秒內重建連線）
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List
import aiohttp
import json

logger = logging.getLogger(__name__)


class SatelliteMeshFailoverTest:
    """衛星失聯到 Mesh 備援測試場景"""

    def __init__(self, netstack_url: str, simworld_url: str):
        self.netstack_url = netstack_url
        self.simworld_url = simworld_url
        self.test_data = {}
        self.performance_metrics = {}
        self.failover_data = {}

    async def run_scenario(self, session: aiohttp.ClientSession) -> Dict:
        """執行衛星失聯到 Mesh 備援測試場景"""
        logger.info("🛰️➡️📡 開始執行衛星失聯到 Mesh 備援測試場景")

        scenario_start = time.time()
        results = {
            "scenario_name": "衛星失聯切換到 Mesh 場景",
            "start_time": datetime.utcnow().isoformat(),
            "steps": [],
            "performance_metrics": {},
            "success": False,
        }

        try:
            # 步驟 1: 建立衛星連接
            step1_result = await self._establish_satellite_connection(session)
            results["steps"].append(step1_result)
            if not step1_result["success"]:
                return results

            # 步驟 2: 開始數據傳輸
            step2_result = await self._start_data_transmission(session)
            results["steps"].append(step2_result)
            if not step2_result["success"]:
                return results

            # 步驟 3: 部署 Mesh 網路節點
            step3_result = await self._deploy_mesh_nodes(session)
            results["steps"].append(step3_result)
            if not step3_result["success"]:
                return results

            # 步驟 4: 模擬衛星失聯
            step4_result = await self._simulate_satellite_loss(session)
            results["steps"].append(step4_result)
            if not step4_result["success"]:
                return results

            # 步驟 5: 監控 Mesh 網路發現
            step5_result = await self._monitor_mesh_discovery(session)
            results["steps"].append(step5_result)
            if not step5_result["success"]:
                return results

            # 步驟 6: 驗證備援連接建立
            step6_result = await self._verify_backup_connection(session)
            results["steps"].append(step6_result)
            if not step6_result["success"]:
                return results

            # 步驟 7: 測試數據完整性
            step7_result = await self._test_data_integrity(session)
            results["steps"].append(step7_result)

            # 步驟 8: 驗證性能指標
            step8_result = await self._verify_performance_requirements(session)
            results["steps"].append(step8_result)

            results["success"] = step7_result["success"] and step8_result["success"]
            logger.info("✅ 衛星失聯到 Mesh 備援測試場景完成")

        except Exception as e:
            logger.error(f"❌ 衛星失聯到 Mesh 備援測試場景異常: {e}")
            results["error"] = str(e)

        finally:
            scenario_duration = time.time() - scenario_start
            results["duration_seconds"] = scenario_duration
            results["end_time"] = datetime.utcnow().isoformat()
            results["performance_metrics"] = self.performance_metrics
            results["failover_data"] = self.failover_data

        return results

    async def _establish_satellite_connection(
        self, session: aiohttp.ClientSession
    ) -> Dict:
        """步驟1: 建立衛星連接"""
        logger.info("🛰️ 建立衛星連接")
        step_start = time.time()

        # UAV 配置
        uav_config = {
            "uav_id": "failover_test_uav",
            "position": {"latitude": 25.0330, "longitude": 121.5654, "altitude": 1000},
            "communication": {
                "primary_link": "satellite",
                "backup_link": "mesh",
                "automatic_failover": True,
                "failover_detection_time_ms": 500,
                "reconnection_timeout_ms": 2000,
            },
            "mesh_capabilities": {
                "enabled": True,
                "frequency_band": "2.4GHz",
                "transmission_power": 20,  # dBm
                "range_km": 10,
                "routing_protocol": "AODV",
            },
        }

        try:
            # 創建 UAV
            async with session.post(
                f"{self.netstack_url}/api/v1/uav/create", json=uav_config
            ) as response:
                if response.status != 201:
                    error_text = await response.text()
                    return {
                        "step_name": "建立衛星連接",
                        "success": False,
                        "duration_ms": (time.time() - step_start) * 1000,
                        "error": f"UAV 創建失敗: HTTP {response.status} - {error_text}",
                    }

                uav_data = await response.json()
                self.test_data["uav_id"] = uav_data.get("uav_id", uav_config["uav_id"])

            # 建立衛星連接
            satellite_config = {
                "uav_id": self.test_data["uav_id"],
                "satellite_selection": "optimal",
                "frequency_ghz": 14.2,
                "link_redundancy": True,
                "quality_monitoring": True,
                "failover_preparation": True,
            }

            async with session.post(
                f"{self.netstack_url}/api/v1/satellite/connect", json=satellite_config
            ) as response:
                step_duration = time.time() - step_start

                if response.status == 200:
                    connection_data = await response.json()
                    self.test_data["satellite_connection_id"] = connection_data.get(
                        "connection_id"
                    )
                    self.test_data["satellite_id"] = connection_data.get("satellite_id")

                    # 記錄連接建立時間
                    self.performance_metrics["satellite_connection_time_ms"] = (
                        step_duration * 1000
                    )

                    logger.info(
                        f"✅ 衛星連接建立成功: {self.test_data['satellite_id']}"
                    )

                    return {
                        "step_name": "建立衛星連接",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"衛星ID: {self.test_data['satellite_id']}, 連接ID: {self.test_data['satellite_connection_id']}",
                    }
                else:
                    error_text = await response.text()
                    return {
                        "step_name": "建立衛星連接",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"衛星連接失敗: HTTP {response.status} - {error_text}",
                    }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 建立衛星連接異常: {e}")
            return {
                "step_name": "建立衛星連接",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _start_data_transmission(self, session: aiohttp.ClientSession) -> Dict:
        """步驟2: 開始數據傳輸"""
        logger.info("📊 開始數據傳輸")
        step_start = time.time()

        # 數據傳輸配置
        transmission_config = {
            "uav_id": self.test_data["uav_id"],
            "stream_type": "continuous",
            "data_rate_kbps": 1024,  # 1 Mbps 連續數據流
            "packet_size": 1024,  # 1KB 每包
            "transmission_interval_ms": 8,  # 8ms 間隔 (125 pps)
            "reliability_mode": "high",
            "sequence_tracking": True,
            "integrity_check": True,
        }

        try:
            # 啟動數據傳輸
            async with session.post(
                f"{self.netstack_url}/api/v1/data/stream/start",
                json=transmission_config,
            ) as response:
                step_duration = time.time() - step_start

                if response.status == 200:
                    stream_data = await response.json()
                    self.test_data["stream_id"] = stream_data.get("stream_id")
                    self.test_data["baseline_packets_sent"] = 0

                    logger.info(f"✅ 數據傳輸開始: {self.test_data['stream_id']}")

                    # 等待數據流穩定
                    await asyncio.sleep(3)

                    # 記錄基線數據包計數
                    async with session.get(
                        f"{self.netstack_url}/api/v1/data/stream/status",
                        params={"stream_id": self.test_data["stream_id"]},
                    ) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            self.test_data["baseline_packets_sent"] = status_data.get(
                                "packets_sent", 0
                            )

                    return {
                        "step_name": "開始數據傳輸",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"數據流ID: {self.test_data['stream_id']}, 基線數據包: {self.test_data['baseline_packets_sent']}",
                    }
                else:
                    error_text = await response.text()
                    return {
                        "step_name": "開始數據傳輸",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"數據傳輸啟動失敗: HTTP {response.status} - {error_text}",
                    }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 開始數據傳輸異常: {e}")
            return {
                "step_name": "開始數據傳輸",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _deploy_mesh_nodes(self, session: aiohttp.ClientSession) -> Dict:
        """步驟3: 部署 Mesh 網路節點"""
        logger.info("📡 部署 Mesh 網路節點")
        step_start = time.time()

        # Mesh 節點配置
        mesh_nodes = [
            {
                "node_id": "mesh_node_1",
                "position": {
                    "latitude": 25.0320,
                    "longitude": 121.5644,
                    "altitude": 100,
                },
                "role": "gateway",
                "connectivity": "5g_core",
            },
            {
                "node_id": "mesh_node_2",
                "position": {
                    "latitude": 25.0340,
                    "longitude": 121.5664,
                    "altitude": 80,
                },
                "role": "relay",
                "connectivity": "mesh_only",
            },
            {
                "node_id": "mesh_node_3",
                "position": {
                    "latitude": 25.0350,
                    "longitude": 121.5674,
                    "altitude": 120,
                },
                "role": "relay",
                "connectivity": "mesh_only",
            },
        ]

        try:
            deployed_nodes = []

            for node_config in mesh_nodes:
                # 部署 Mesh 節點
                async with session.post(
                    f"{self.netstack_url}/api/v1/mesh/node/deploy", json=node_config
                ) as response:
                    if response.status == 201:
                        node_data = await response.json()
                        deployed_nodes.append(
                            {
                                "node_id": node_data.get(
                                    "node_id", node_config["node_id"]
                                ),
                                "status": "active",
                                "role": node_config["role"],
                            }
                        )
                        logger.info(f"✅ Mesh 節點部署成功: {node_config['node_id']}")
                    else:
                        logger.warning(f"⚠️ Mesh 節點部署失敗: {node_config['node_id']}")

            if len(deployed_nodes) >= 2:  # 至少需要2個節點
                self.test_data["mesh_nodes"] = deployed_nodes

                # 等待 Mesh 網路建立
                await asyncio.sleep(5)

                # 驗證 Mesh 網路連通性
                async with session.get(
                    f"{self.netstack_url}/api/v1/mesh/topology"
                ) as response:
                    if response.status == 200:
                        topology_data = await response.json()
                        mesh_connectivity = topology_data.get("connectivity_matrix", {})

                        step_duration = time.time() - step_start

                        return {
                            "step_name": "部署 Mesh 網路節點",
                            "success": True,
                            "duration_ms": step_duration * 1000,
                            "details": f"部署 {len(deployed_nodes)} 個 Mesh 節點，網路連通",
                            "deployed_nodes": deployed_nodes,
                        }
                    else:
                        step_duration = time.time() - step_start
                        return {
                            "step_name": "部署 Mesh 網路節點",
                            "success": False,
                            "duration_ms": step_duration * 1000,
                            "error": "Mesh 網路連通性驗證失敗",
                        }
            else:
                step_duration = time.time() - step_start
                return {
                    "step_name": "部署 Mesh 網路節點",
                    "success": False,
                    "duration_ms": step_duration * 1000,
                    "error": f"部署的 Mesh 節點數量不足: {len(deployed_nodes)} < 2",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 部署 Mesh 網路節點異常: {e}")
            return {
                "step_name": "部署 Mesh 網路節點",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _simulate_satellite_loss(self, session: aiohttp.ClientSession) -> Dict:
        """步驟4: 模擬衛星失聯"""
        logger.info("🚨 模擬衛星失聯")
        step_start = time.time()

        # 記錄失聯前的狀態
        self.failover_data["loss_trigger_time"] = datetime.utcnow().isoformat()

        try:
            # 模擬衛星失聯
            loss_config = {
                "satellite_id": self.test_data.get("satellite_id"),
                "loss_type": "signal_blockage",  # 信號阻擋
                "severity": "complete",  # 完全失聯
                "duration_sec": 60,  # 持續60秒
                "trigger_mode": "immediate",
            }

            async with session.post(
                f"{self.simworld_url}/api/v1/satellite/simulate_loss", json=loss_config
            ) as response:
                if response.status == 200:
                    loss_data = await response.json()
                    self.failover_data["loss_simulation_id"] = loss_data.get(
                        "simulation_id"
                    )

                    logger.info(
                        f"✅ 衛星失聯模擬啟動: {self.failover_data['loss_simulation_id']}"
                    )

                    # 等待失聯檢測
                    await asyncio.sleep(1)

                    step_duration = time.time() - step_start

                    return {
                        "step_name": "模擬衛星失聯",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"失聯模擬ID: {self.failover_data['loss_simulation_id']}, 失聯類型: {loss_config['loss_type']}",
                    }
                else:
                    error_text = await response.text()
                    step_duration = time.time() - step_start
                    return {
                        "step_name": "模擬衛星失聯",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"衛星失聯模擬失敗: HTTP {response.status} - {error_text}",
                    }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 模擬衛星失聯異常: {e}")
            return {
                "step_name": "模擬衛星失聯",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _monitor_mesh_discovery(self, session: aiohttp.ClientSession) -> Dict:
        """步驟5: 監控 Mesh 網路發現"""
        logger.info("🔍 監控 Mesh 網路發現")
        step_start = time.time()

        max_discovery_time = 2.0  # 最大發現時間 2 秒 (符合要求)
        check_interval = 0.05  # 每 50ms 檢查一次

        try:
            discovery_start = time.time()
            mesh_discovered = False
            discovery_time = 0

            while (time.time() - discovery_start) < max_discovery_time:
                # 檢查 Mesh 網路發現狀態
                async with session.get(
                    f"{self.netstack_url}/api/v1/mesh/discovery",
                    params={"uav_id": self.test_data["uav_id"]},
                ) as response:
                    if response.status == 200:
                        discovery_data = await response.json()

                        # 檢查是否發現可用的 Mesh 節點
                        available_nodes = discovery_data.get("available_nodes", [])
                        if len(available_nodes) > 0:
                            discovery_time = (
                                time.time() - discovery_start
                            ) * 1000  # 轉換為毫秒
                            mesh_discovered = True

                            self.performance_metrics["mesh_discovery_time_ms"] = (
                                discovery_time
                            )
                            self.failover_data["discovered_nodes"] = available_nodes

                            logger.info(
                                f"✅ Mesh 網路發現成功: {discovery_time:.1f}ms, 發現 {len(available_nodes)} 個節點"
                            )
                            break

                await asyncio.sleep(check_interval)

            step_duration = time.time() - step_start

            if mesh_discovered:
                # 檢查發現時間是否符合要求 (< 500ms)
                if discovery_time <= 500:
                    return {
                        "step_name": "監控 Mesh 網路發現",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"Mesh 發現時間: {discovery_time:.1f}ms, 發現節點數: {len(self.failover_data['discovered_nodes'])}",
                        "discovery_time_ms": discovery_time,
                        "discovered_nodes": len(self.failover_data["discovered_nodes"]),
                    }
                else:
                    return {
                        "step_name": "監控 Mesh 網路發現",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"Mesh 發現時間過長: {discovery_time:.1f}ms > 500ms",
                        "discovery_time_ms": discovery_time,
                    }
            else:
                return {
                    "step_name": "監控 Mesh 網路發現",
                    "success": False,
                    "duration_ms": step_duration * 1000,
                    "error": f"在 {max_discovery_time} 秒內未發現 Mesh 網路",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 監控 Mesh 網路發現異常: {e}")
            return {
                "step_name": "監控 Mesh 網路發現",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _verify_backup_connection(self, session: aiohttp.ClientSession) -> Dict:
        """步驟6: 驗證備援連接建立"""
        logger.info("🔗 驗證備援連接建立")
        step_start = time.time()

        max_connection_time = 2.0  # 最大連接時間 2 秒 (符合要求)
        check_interval = 0.05  # 每 50ms 檢查一次

        try:
            connection_start = time.time()
            backup_connected = False
            connection_time = 0

            while (time.time() - connection_start) < max_connection_time:
                # 檢查備援連接狀態
                async with session.get(
                    f"{self.netstack_url}/api/v1/mesh/connection/status",
                    params={"uav_id": self.test_data["uav_id"]},
                ) as response:
                    if response.status == 200:
                        connection_data = await response.json()

                        # 檢查連接是否建立
                        if connection_data.get("connection_status") == "active":
                            connection_time = (
                                time.time() - connection_start
                            ) * 1000  # 轉換為毫秒
                            backup_connected = True

                            self.performance_metrics["backup_connection_time_ms"] = (
                                connection_time
                            )
                            self.failover_data["backup_connection_id"] = (
                                connection_data.get("connection_id")
                            )
                            self.failover_data["active_mesh_node"] = (
                                connection_data.get("connected_node_id")
                            )

                            logger.info(
                                f"✅ 備援連接建立成功: {connection_time:.1f}ms, 節點: {self.failover_data['active_mesh_node']}"
                            )
                            break

                await asyncio.sleep(check_interval)

            step_duration = time.time() - step_start

            if backup_connected:
                # 檢查連接時間是否符合要求 (< 1000ms)
                if connection_time <= 1000:
                    return {
                        "step_name": "驗證備援連接建立",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"備援連接時間: {connection_time:.1f}ms, 連接節點: {self.failover_data['active_mesh_node']}",
                        "connection_time_ms": connection_time,
                        "connected_node": self.failover_data["active_mesh_node"],
                    }
                else:
                    return {
                        "step_name": "驗證備援連接建立",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"備援連接時間過長: {connection_time:.1f}ms > 1000ms",
                        "connection_time_ms": connection_time,
                    }
            else:
                return {
                    "step_name": "驗證備援連接建立",
                    "success": False,
                    "duration_ms": step_duration * 1000,
                    "error": f"在 {max_connection_time} 秒內未建立備援連接",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 驗證備援連接建立異常: {e}")
            return {
                "step_name": "驗證備援連接建立",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _test_data_integrity(self, session: aiohttp.ClientSession) -> Dict:
        """步驟7: 測試數據完整性"""
        logger.info("🔍 測試數據完整性")
        step_start = time.time()

        try:
            # 等待一段時間讓數據通過備援連接傳輸
            await asyncio.sleep(3)

            # 獲取數據流狀態
            async with session.get(
                f"{self.netstack_url}/api/v1/data/stream/status",
                params={"stream_id": self.test_data.get("stream_id")},
            ) as response:
                if response.status == 200:
                    stream_status = await response.json()

                    total_packets_sent = stream_status.get("packets_sent", 0)
                    packets_received = stream_status.get("packets_received", 0)
                    packets_lost = stream_status.get("packets_lost", 0)

                    # 計算數據完整性
                    if total_packets_sent > 0:
                        data_integrity_percent = (
                            packets_received / total_packets_sent
                        ) * 100
                        packet_loss_percent = (packets_lost / total_packets_sent) * 100
                    else:
                        data_integrity_percent = 0
                        packet_loss_percent = 100

                    # 記錄指標
                    self.performance_metrics["data_integrity_percent"] = (
                        data_integrity_percent
                    )
                    self.performance_metrics["packet_loss_percent"] = (
                        packet_loss_percent
                    )
                    self.performance_metrics["total_packets_sent"] = total_packets_sent
                    self.performance_metrics["packets_received"] = packets_received

                    # 進行數據完整性驗證
                    async with session.post(
                        f"{self.netstack_url}/api/v1/data/verify",
                        json={
                            "stream_id": self.test_data["stream_id"],
                            "verification_type": "sequence_check",
                        },
                    ) as verify_response:
                        if verify_response.status == 200:
                            verify_data = await verify_response.json()
                            sequence_integrity = verify_data.get(
                                "sequence_integrity", False
                            )
                            checksum_valid = verify_data.get("checksum_valid", False)

                            overall_integrity = (
                                data_integrity_percent >= 95
                                and sequence_integrity
                                and checksum_valid
                            )

                            step_duration = time.time() - step_start

                            if overall_integrity:
                                logger.info(
                                    f"✅ 數據完整性驗證通過: {data_integrity_percent:.1f}%"
                                )

                                return {
                                    "step_name": "測試數據完整性",
                                    "success": True,
                                    "duration_ms": step_duration * 1000,
                                    "details": f"數據完整性: {data_integrity_percent:.1f}%, 序列完整: {sequence_integrity}, 校驗通過: {checksum_valid}",
                                    "integrity_metrics": {
                                        "data_integrity_percent": data_integrity_percent,
                                        "packet_loss_percent": packet_loss_percent,
                                        "sequence_integrity": sequence_integrity,
                                        "checksum_valid": checksum_valid,
                                    },
                                }
                            else:
                                logger.error(
                                    f"❌ 數據完整性驗證失敗: {data_integrity_percent:.1f}%"
                                )

                                return {
                                    "step_name": "測試數據完整性",
                                    "success": False,
                                    "duration_ms": step_duration * 1000,
                                    "error": f"數據完整性不符合要求: {data_integrity_percent:.1f}% < 95%",
                                    "integrity_metrics": {
                                        "data_integrity_percent": data_integrity_percent,
                                        "sequence_integrity": sequence_integrity,
                                        "checksum_valid": checksum_valid,
                                    },
                                }
                        else:
                            step_duration = time.time() - step_start
                            return {
                                "step_name": "測試數據完整性",
                                "success": False,
                                "duration_ms": step_duration * 1000,
                                "error": "無法執行數據驗證",
                            }
                else:
                    step_duration = time.time() - step_start
                    return {
                        "step_name": "測試數據完整性",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": "無法獲取數據流狀態",
                    }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 測試數據完整性異常: {e}")
            return {
                "step_name": "測試數據完整性",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _verify_performance_requirements(
        self, session: aiohttp.ClientSession
    ) -> Dict:
        """步驟8: 驗證性能指標"""
        logger.info("📈 驗證性能指標")
        step_start = time.time()

        try:
            # 性能要求
            performance_requirements = {
                "max_reconnection_time_ms": 2000,  # 2秒內重建連線
                "mesh_discovery_time_ms": 500,
                "backup_link_establishment_ms": 1000,
                "data_integrity_percentage": 95.0,
            }

            verification_results = {}
            all_requirements_met = True

            # 檢查總重連時間 (發現時間 + 連接時間)
            discovery_time = self.performance_metrics.get("mesh_discovery_time_ms", 0)
            connection_time = self.performance_metrics.get(
                "backup_connection_time_ms", 0
            )
            total_reconnection_time = discovery_time + connection_time

            self.performance_metrics["total_reconnection_time_ms"] = (
                total_reconnection_time
            )

            if (
                total_reconnection_time
                <= performance_requirements["max_reconnection_time_ms"]
            ):
                verification_results["reconnection_time_check"] = "PASS"
                logger.info(
                    f"✅ 重連時間目標達成: {total_reconnection_time:.1f}ms <= {performance_requirements['max_reconnection_time_ms']}ms"
                )
            else:
                verification_results["reconnection_time_check"] = "FAIL"
                all_requirements_met = False
                logger.error(
                    f"❌ 重連時間目標未達成: {total_reconnection_time:.1f}ms > {performance_requirements['max_reconnection_time_ms']}ms"
                )

            # 檢查 Mesh 發現時間
            if discovery_time <= performance_requirements["mesh_discovery_time_ms"]:
                verification_results["mesh_discovery_check"] = "PASS"
                logger.info(
                    f"✅ Mesh 發現時間達成: {discovery_time:.1f}ms <= {performance_requirements['mesh_discovery_time_ms']}ms"
                )
            else:
                verification_results["mesh_discovery_check"] = "FAIL"
                all_requirements_met = False
                logger.error(
                    f"❌ Mesh 發現時間未達成: {discovery_time:.1f}ms > {performance_requirements['mesh_discovery_time_ms']}ms"
                )

            # 檢查備援連接建立時間
            if (
                connection_time
                <= performance_requirements["backup_link_establishment_ms"]
            ):
                verification_results["backup_connection_check"] = "PASS"
                logger.info(
                    f"✅ 備援連接時間達成: {connection_time:.1f}ms <= {performance_requirements['backup_link_establishment_ms']}ms"
                )
            else:
                verification_results["backup_connection_check"] = "FAIL"
                all_requirements_met = False
                logger.error(
                    f"❌ 備援連接時間未達成: {connection_time:.1f}ms > {performance_requirements['backup_link_establishment_ms']}ms"
                )

            # 檢查數據完整性
            data_integrity = self.performance_metrics.get("data_integrity_percent", 0)
            if data_integrity >= performance_requirements["data_integrity_percentage"]:
                verification_results["data_integrity_check"] = "PASS"
                logger.info(
                    f"✅ 數據完整性達成: {data_integrity:.1f}% >= {performance_requirements['data_integrity_percentage']}%"
                )
            else:
                verification_results["data_integrity_check"] = "FAIL"
                all_requirements_met = False
                logger.error(
                    f"❌ 數據完整性未達成: {data_integrity:.1f}% < {performance_requirements['data_integrity_percentage']}%"
                )

            step_duration = time.time() - step_start

            if all_requirements_met:
                logger.info("✅ 所有性能要求均已達成")

                return {
                    "step_name": "驗證性能指標",
                    "success": True,
                    "duration_ms": step_duration * 1000,
                    "details": f"總重連時間: {total_reconnection_time:.1f}ms, 數據完整性: {data_integrity:.1f}%",
                    "verification_results": verification_results,
                    "performance_summary": {
                        "total_reconnection_time_ms": total_reconnection_time,
                        "mesh_discovery_time_ms": discovery_time,
                        "backup_connection_time_ms": connection_time,
                        "data_integrity_percent": data_integrity,
                    },
                }
            else:
                failed_checks = [
                    k for k, v in verification_results.items() if v == "FAIL"
                ]
                logger.error(f"❌ 部分性能要求未達成: {failed_checks}")

                return {
                    "step_name": "驗證性能指標",
                    "success": False,
                    "duration_ms": step_duration * 1000,
                    "error": f"未達成的性能要求: {failed_checks}",
                    "verification_results": verification_results,
                    "performance_summary": {
                        "total_reconnection_time_ms": total_reconnection_time,
                        "data_integrity_percent": data_integrity,
                    },
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 驗證性能指標異常: {e}")
            return {
                "step_name": "驗證性能指標",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }
