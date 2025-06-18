"""
Mesh 橋接服務 (Enhanced for Stage 5)
實現 Tier-1 Mesh 網路與 5G 核心網的橋接功能
新增動態路由最佳化和智能換手決策算法
"""

import asyncio
import json
import logging
import socket
import struct
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

import structlog
from ..adapters.mongo_adapter import MongoAdapter
from ..adapters.redis_adapter import RedisAdapter
from ..adapters.open5gs_adapter import Open5GSAdapter
from ..models.mesh_models import (
    MeshNode,
    MeshNodeType,
    MeshNodeStatus,
    Bridge5GMeshGateway,
    BridgeStatus,
    QoSClass,
    MeshNetworkTopology,
    MeshTrafficFlow,
    MeshLinkQuality,
    MeshPerformanceMetrics,
    BridgePerformanceMetrics,
    MeshPosition,
    MeshNeighbor,
    MeshRouteEntry,
)

logger = structlog.get_logger(__name__)


class MeshProtocolAdapter:
    """Mesh 協議適配器"""

    def __init__(self):
        self.protocol_handlers = {
            "aodv": self._handle_aodv_packet,
            "olsr": self._handle_olsr_packet,
            "batman": self._handle_batman_packet,
            "custom": self._handle_custom_packet,
        }

    async def _handle_aodv_packet(self, packet_data: bytes) -> Dict[str, Any]:
        """處理 AODV 協議封包"""
        # 簡化的 AODV 封包解析
        try:
            # AODV 報頭結構 (簡化版)
            if len(packet_data) < 8:
                return {"error": "packet_too_short"}

            type_byte = packet_data[0]
            hop_count = packet_data[1]
            rreq_id = struct.unpack(">I", packet_data[2:6])[0]

            packet_info = {
                "protocol": "aodv",
                "type": (
                    "rreq" if type_byte == 1 else "rrep" if type_byte == 2 else "rerr"
                ),
                "hop_count": hop_count,
                "rreq_id": rreq_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return packet_info

        except Exception as e:
            logger.error(f"AODV packet parsing error: {e}")
            return {"error": str(e)}

    async def _handle_olsr_packet(self, packet_data: bytes) -> Dict[str, Any]:
        """處理 OLSR 協議封包"""
        # 簡化的 OLSR 封包解析
        return {
            "protocol": "olsr",
            "message_type": "hello",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _handle_batman_packet(self, packet_data: bytes) -> Dict[str, Any]:
        """處理 BATMAN 協議封包"""
        # 簡化的 BATMAN 封包解析
        return {
            "protocol": "batman",
            "message_type": "ogm",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _handle_custom_packet(self, packet_data: bytes) -> Dict[str, Any]:
        """處理自定義協議封包"""
        return {
            "protocol": "custom",
            "data_length": len(packet_data),
            "timestamp": datetime.utcnow().isoformat(),
        }


class GTPTunnelManager:
    """GTP 隧道管理器"""

    def __init__(self, upf_ip: str, upf_port: int = 2152):
        self.upf_ip = upf_ip
        self.upf_port = upf_port
        self.active_tunnels: Dict[str, Dict[str, Any]] = {}
        self.tunnel_stats: Dict[str, Dict[str, int]] = {}

    async def create_tunnel(
        self, tunnel_id: str, ue_ip: str, mesh_node_id: str
    ) -> bool:
        """建立 GTP 隧道"""
        try:
            tunnel_info = {
                "tunnel_id": tunnel_id,
                "ue_ip": ue_ip,
                "mesh_node_id": mesh_node_id,
                "upf_ip": self.upf_ip,
                "upf_port": self.upf_port,
                "created_at": datetime.utcnow(),
                "status": "active",
            }

            self.active_tunnels[tunnel_id] = tunnel_info
            self.tunnel_stats[tunnel_id] = {
                "packets_up": 0,
                "packets_down": 0,
                "bytes_up": 0,
                "bytes_down": 0,
            }

            logger.info(
                f"Created GTP tunnel {tunnel_id} for UE {ue_ip} -> Mesh node {mesh_node_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create GTP tunnel {tunnel_id}: {e}")
            return False

    async def forward_uplink_packet(self, tunnel_id: str, packet_data: bytes) -> bool:
        """轉發上行封包 (Mesh -> 5G)"""
        if tunnel_id not in self.active_tunnels:
            logger.warning(f"Tunnel {tunnel_id} not found for uplink forwarding")
            return False

        try:
            # 封裝為 GTP-U 封包
            gtp_packet = self._encapsulate_gtp(packet_data, tunnel_id)

            # 更新統計
            self.tunnel_stats[tunnel_id]["packets_up"] += 1
            self.tunnel_stats[tunnel_id]["bytes_up"] += len(packet_data)

            # 實際轉發到 UPF (這裡模擬)
            logger.debug(
                f"Forwarding uplink packet via tunnel {tunnel_id}, size: {len(gtp_packet)} bytes"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to forward uplink packet via tunnel {tunnel_id}: {e}")
            return False

    async def forward_downlink_packet(self, tunnel_id: str, packet_data: bytes) -> bool:
        """轉發下行封包 (5G -> Mesh)"""
        if tunnel_id not in self.active_tunnels:
            logger.warning(f"Tunnel {tunnel_id} not found for downlink forwarding")
            return False

        try:
            # 解封裝 GTP-U 封包
            user_packet = self._decapsulate_gtp(packet_data)

            # 更新統計
            self.tunnel_stats[tunnel_id]["packets_down"] += 1
            self.tunnel_stats[tunnel_id]["bytes_down"] += len(user_packet)

            # 實際轉發到 Mesh 網路 (這裡模擬)
            logger.debug(
                f"Forwarding downlink packet via tunnel {tunnel_id}, size: {len(user_packet)} bytes"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to forward downlink packet via tunnel {tunnel_id}: {e}"
            )
            return False

    def _encapsulate_gtp(self, user_data: bytes, tunnel_id: str) -> bytes:
        """封裝為 GTP-U 封包"""
        # 簡化的 GTP-U 報頭 (8 位元組)
        gtp_header = struct.pack(
            ">BBHIHH",
            0x30,  # Version=1, PT=1, E=0, S=0, PN=0
            0xFF,  # Message Type: G-PDU
            len(user_data) + 8,  # Length
            (
                int(tunnel_id.replace("-", "")[:8], 16)
                if tunnel_id.replace("-", "").isdigit()
                else 0x12345678
            ),  # TEID
            0,  # Sequence Number
            0,  # N-PDU Number + Next Extension Header
        )
        return gtp_header + user_data

    def _decapsulate_gtp(self, gtp_packet: bytes) -> bytes:
        """解封裝 GTP-U 封包"""
        if len(gtp_packet) < 8:
            raise ValueError("Invalid GTP packet: too short")

        # 跳過 GTP 報頭
        return gtp_packet[8:]

    async def remove_tunnel(self, tunnel_id: str) -> bool:
        """移除 GTP 隧道"""
        if tunnel_id in self.active_tunnels:
            del self.active_tunnels[tunnel_id]
            if tunnel_id in self.tunnel_stats:
                del self.tunnel_stats[tunnel_id]
            logger.info(f"Removed GTP tunnel {tunnel_id}")
            return True
        return False


class QoSManager:
    """QoS 管理器"""

    def __init__(self):
        self.qos_policies: Dict[QoSClass, Dict[str, Any]] = {
            QoSClass.EMERGENCY: {
                "priority": 7,
                "max_latency_ms": 10,
                "min_bandwidth_mbps": 1.0,
                "packet_loss_threshold": 0.001,
            },
            QoSClass.COMMAND: {
                "priority": 6,
                "max_latency_ms": 50,
                "min_bandwidth_mbps": 0.5,
                "packet_loss_threshold": 0.01,
            },
            QoSClass.VIDEO: {
                "priority": 4,
                "max_latency_ms": 100,
                "min_bandwidth_mbps": 2.0,
                "packet_loss_threshold": 0.05,
            },
            QoSClass.DATA: {
                "priority": 2,
                "max_latency_ms": 500,
                "min_bandwidth_mbps": 0.1,
                "packet_loss_threshold": 0.1,
            },
            QoSClass.BACKGROUND: {
                "priority": 1,
                "max_latency_ms": 1000,
                "min_bandwidth_mbps": 0.05,
                "packet_loss_threshold": 0.2,
            },
        }

    async def classify_traffic(
        self, packet_data: bytes, source_ip: str, dest_ip: str
    ) -> QoSClass:
        """流量分類"""
        # 簡化的流量分類邏輯
        # 實際實現會根據封包內容、端口、IP 等進行分類

        if len(packet_data) < 100:
            return QoSClass.COMMAND  # 小封包通常是控制訊息
        elif len(packet_data) > 1000:
            return QoSClass.VIDEO  # 大封包可能是視頻
        else:
            return QoSClass.DATA  # 中等大小封包

    async def apply_qos_policy(
        self, qos_class: QoSClass, packet_data: bytes
    ) -> Dict[str, Any]:
        """應用 QoS 策略"""
        policy = self.qos_policies.get(qos_class, self.qos_policies[QoSClass.DATA])

        return {
            "qos_class": qos_class.value,
            "priority": policy["priority"],
            "max_latency_ms": policy["max_latency_ms"],
            "min_bandwidth_mbps": policy["min_bandwidth_mbps"],
            "packet_loss_threshold": policy["packet_loss_threshold"],
            "packet_size": len(packet_data),
        }


class MeshBridgeService:
    """Mesh 橋接服務主類"""

    def __init__(
        self,
        mongo_adapter: MongoAdapter,
        redis_adapter: RedisAdapter,
        open5gs_adapter: Open5GSAdapter,
        upf_ip: str = "172.20.0.30",
        upf_port: int = 2152,
    ):
        self.mongo_adapter = mongo_adapter
        self.redis_adapter = redis_adapter
        self.open5gs_adapter = open5gs_adapter

        # 組件初始化
        self.protocol_adapter = MeshProtocolAdapter()
        self.gtp_manager = GTPTunnelManager(upf_ip, upf_port)
        self.qos_manager = QoSManager()

        # 狀態管理
        self.mesh_nodes: Dict[str, MeshNode] = {}
        self.bridge_gateways: Dict[str, Bridge5GMeshGateway] = {}
        self.active_flows: Dict[str, MeshTrafficFlow] = {}

        # 監控數據
        self.performance_data: Dict[str, Any] = {}
        self.routing_table: Dict[str, List[MeshRouteEntry]] = {}

        # 運行狀態
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None

    async def start_service(self) -> bool:
        """啟動橋接服務"""
        try:
            logger.info("🌉 啟動 Mesh 橋接服務...")

            # 載入現有配置
            await self._load_mesh_configuration()

            # 初始化橋接網關
            await self._initialize_bridge_gateways()

            # 啟動監控任務
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

            self.is_running = True
            logger.info("✅ Mesh 橋接服務啟動成功")
            return True

        except Exception as e:
            logger.error(f"❌ 橋接服務啟動失敗: {e}")
            return False

    async def stop_service(self) -> bool:
        """停止橋接服務"""
        try:
            logger.info("🛑 停止 Mesh 橋接服務...")

            self.is_running = False

            if self.monitoring_task:
                self.monitoring_task.cancel()
                await self.monitoring_task

            # 清理活躍連接
            for gateway_id in list(self.bridge_gateways.keys()):
                await self._disconnect_bridge_gateway(gateway_id)

            logger.info("✅ Mesh 橋接服務已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 橋接服務停止失敗: {e}")
            return False

    async def create_mesh_node(self, node_data: Dict[str, Any]) -> Optional[MeshNode]:
        """創建 Mesh 節點"""
        try:
            node_id = str(uuid4())

            mesh_node = MeshNode(
                node_id=node_id,
                name=node_data["name"],
                node_type=MeshNodeType(node_data["node_type"]),
                ip_address=node_data["ip_address"],
                mac_address=node_data["mac_address"],
                frequency_mhz=node_data.get("frequency_mhz", 900.0),
                power_dbm=node_data.get("power_dbm", 20.0),
                position=(
                    MeshPosition(**node_data["position"])
                    if "position" in node_data
                    else None
                ),
            )

            # 儲存到資料庫
            await self.mongo_adapter.insert_one("mesh_nodes", mesh_node.dict())

            # 快取到記憶體
            self.mesh_nodes[node_id] = mesh_node

            logger.info(f"✅ 創建 Mesh 節點: {mesh_node.name} ({node_id})")
            return mesh_node

        except Exception as e:
            logger.error(f"❌ 創建 Mesh 節點失敗: {e}")
            return None

    async def create_bridge_gateway(
        self, gateway_data: Dict[str, Any]
    ) -> Optional[Bridge5GMeshGateway]:
        """創建橋接網關"""
        try:
            gateway_id = str(uuid4())

            # 檢查關聯的 Mesh 節點是否存在
            mesh_node_id = gateway_data["mesh_node_id"]
            if mesh_node_id not in self.mesh_nodes:
                mesh_node = await self._load_mesh_node(mesh_node_id)
                if not mesh_node:
                    raise ValueError(f"Mesh 節點 {mesh_node_id} 不存在")

            bridge_gateway = Bridge5GMeshGateway(
                gateway_id=gateway_id,
                name=gateway_data["name"],
                upf_ip=gateway_data["upf_ip"],
                upf_port=gateway_data.get("upf_port", 2152),
                mesh_node_id=mesh_node_id,
                mesh_interface=gateway_data["mesh_interface"],
                slice_info=gateway_data.get("slice_info", {}),
            )

            # 儲存到資料庫
            await self.mongo_adapter.insert_one(
                "bridge_gateways", bridge_gateway.dict()
            )

            # 快取到記憶體
            self.bridge_gateways[gateway_id] = bridge_gateway

            # 啟動橋接連接
            await self._connect_bridge_gateway(gateway_id)

            logger.info(f"✅ 創建橋接網關: {bridge_gateway.name} ({gateway_id})")
            return bridge_gateway

        except Exception as e:
            logger.error(f"❌ 創建橋接網關失敗: {e}")
            return None

    async def forward_packet_5g_to_mesh(
        self, gateway_id: str, packet_data: bytes, destination_mesh_node: str
    ) -> bool:
        """轉發封包從 5G 到 Mesh"""
        try:
            if gateway_id not in self.bridge_gateways:
                logger.error(f"橋接網關 {gateway_id} 不存在")
                return False

            gateway = self.bridge_gateways[gateway_id]
            if gateway.status != BridgeStatus.CONNECTED:
                logger.warning(f"橋接網關 {gateway_id} 未連接")
                return False

            # QoS 分類
            qos_class = await self.qos_manager.classify_traffic(
                packet_data, "5g_core", destination_mesh_node
            )

            # 應用 QoS 策略
            qos_policy = await self.qos_manager.apply_qos_policy(qos_class, packet_data)

            # 路由決策
            route_path = await self._find_mesh_route(
                gateway.mesh_node_id, destination_mesh_node
            )
            if not route_path:
                logger.warning(f"無法找到到 {destination_mesh_node} 的路由")
                return False

            # 協議轉換和封包轉發
            await self._forward_to_mesh_network(packet_data, route_path, qos_policy)

            # 更新統計
            await self._update_gateway_stats(gateway_id, "5g_to_mesh", len(packet_data))

            logger.debug(f"✅ 成功轉發封包從 5G 到 Mesh: {len(packet_data)} bytes")
            return True

        except Exception as e:
            logger.error(f"❌ 5G 到 Mesh 封包轉發失敗: {e}")
            return False

    async def forward_packet_mesh_to_5g(
        self, gateway_id: str, packet_data: bytes, source_mesh_node: str, tunnel_id: str
    ) -> bool:
        """轉發封包從 Mesh 到 5G"""
        try:
            if gateway_id not in self.bridge_gateways:
                logger.error(f"橋接網關 {gateway_id} 不存在")
                return False

            gateway = self.bridge_gateways[gateway_id]
            if gateway.status != BridgeStatus.CONNECTED:
                logger.warning(f"橋接網關 {gateway_id} 未連接")
                return False

            # QoS 分類
            qos_class = await self.qos_manager.classify_traffic(
                packet_data, source_mesh_node, "5g_core"
            )

            # 應用 QoS 策略
            qos_policy = await self.qos_manager.apply_qos_policy(qos_class, packet_data)

            # 轉發到 5G 核心網
            success = await self.gtp_manager.forward_uplink_packet(
                tunnel_id, packet_data
            )

            if success:
                # 更新統計
                await self._update_gateway_stats(
                    gateway_id, "mesh_to_5g", len(packet_data)
                )

                logger.debug(f"✅ 成功轉發封包從 Mesh 到 5G: {len(packet_data)} bytes")
                return True
            else:
                logger.error("GTP 隧道轉發失敗")
                return False

        except Exception as e:
            logger.error(f"❌ Mesh 到 5G 封包轉發失敗: {e}")
            return False

    async def get_network_topology(self) -> Optional[MeshNetworkTopology]:
        """獲取網路拓撲"""
        try:
            topology_id = str(uuid4())

            # 計算連通性矩陣
            connectivity_matrix = await self._calculate_connectivity_matrix()

            # 計算網路指標
            network_diameter = await self._calculate_network_diameter()
            average_path_length = await self._calculate_average_path_length()

            topology = MeshNetworkTopology(
                topology_id=topology_id,
                network_name="NTN_Mesh_Network",
                nodes=list(self.mesh_nodes.values()),
                gateways=list(self.bridge_gateways.values()),
                active_flows=list(self.active_flows.values()),
                connectivity_matrix=connectivity_matrix,
                network_diameter=network_diameter,
                average_path_length=average_path_length,
            )

            return topology

        except Exception as e:
            logger.error(f"❌ 獲取網路拓撲失敗: {e}")
            return None

    async def get_performance_metrics(
        self, node_id: str
    ) -> Optional[MeshPerformanceMetrics]:
        """獲取性能指標"""
        try:
            if node_id not in self.mesh_nodes:
                return None

            # 從監控數據中提取指標
            node_stats = self.performance_data.get(node_id, {})

            metrics = MeshPerformanceMetrics(
                node_id=node_id,
                total_packets_sent=node_stats.get("packets_sent", 0),
                total_packets_received=node_stats.get("packets_received", 0),
                total_packets_forwarded=node_stats.get("packets_forwarded", 0),
                total_packets_dropped=node_stats.get("packets_dropped", 0),
                average_rssi_dbm=node_stats.get("avg_rssi", -70.0),
                average_snr_db=node_stats.get("avg_snr", 20.0),
                average_latency_ms=node_stats.get("avg_latency", 50.0),
                packet_loss_ratio=node_stats.get("packet_loss_ratio", 0.01),
                power_consumption_w=node_stats.get("power_consumption", 5.0),
                battery_level_percent=node_stats.get("battery_level", 80.0),
                measurement_period_start=datetime.utcnow() - timedelta(hours=1),
                measurement_period_end=datetime.utcnow(),
            )

            return metrics

        except Exception as e:
            logger.error(f"❌ 獲取性能指標失敗: {e}")
            return None

    async def trigger_route_optimization(
        self, target_node_id: Optional[str] = None
    ) -> bool:
        """觸發路由優化"""
        try:
            logger.info("🔄 開始路由優化...")

            nodes_to_optimize = (
                [target_node_id] if target_node_id else list(self.mesh_nodes.keys())
            )

            for node_id in nodes_to_optimize:
                if node_id in self.mesh_nodes:
                    # 重新計算最優路由
                    await self._recalculate_routes(node_id)

                    # 更新路由表
                    await self._update_mesh_routing_table(node_id)

            logger.info("✅ 路由優化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 路由優化失敗: {e}")
            return False

    # 私有方法實現

    async def _load_mesh_configuration(self):
        """載入 Mesh 配置"""
        try:
            # 從資料庫載入 Mesh 節點
            nodes_data = await self.mongo_adapter.find_many("mesh_nodes", {})
            for node_data in nodes_data:
                node = MeshNode(**node_data)
                self.mesh_nodes[node.node_id] = node

            # 從資料庫載入橋接網關
            gateways_data = await self.mongo_adapter.find_many("bridge_gateways", {})
            for gateway_data in gateways_data:
                gateway = Bridge5GMeshGateway(**gateway_data)
                self.bridge_gateways[gateway.gateway_id] = gateway

            logger.info(
                f"載入 {len(self.mesh_nodes)} 個 Mesh 節點，{len(self.bridge_gateways)} 個橋接網關"
            )

        except Exception as e:
            logger.error(f"載入 Mesh 配置失敗: {e}")

    async def _initialize_bridge_gateways(self):
        """初始化橋接網關"""
        for gateway_id, gateway in self.bridge_gateways.items():
            await self._connect_bridge_gateway(gateway_id)

    async def _connect_bridge_gateway(self, gateway_id: str) -> bool:
        """連接橋接網關"""
        try:
            gateway = self.bridge_gateways[gateway_id]
            gateway.status = BridgeStatus.CONNECTING

            # 測試 UPF 連接
            upf_reachable = await self._test_upf_connection(
                gateway.upf_ip, gateway.upf_port
            )

            if upf_reachable:
                gateway.status = BridgeStatus.CONNECTED
                gateway.last_heartbeat = datetime.utcnow()
                logger.info(f"✅ 橋接網關 {gateway.name} 連接成功")
                return True
            else:
                gateway.status = BridgeStatus.FAILED
                logger.error(f"❌ 橋接網關 {gateway.name} 連接失敗")
                return False

        except Exception as e:
            logger.error(f"橋接網關連接異常: {e}")
            return False

    async def _disconnect_bridge_gateway(self, gateway_id: str):
        """斷開橋接網關"""
        if gateway_id in self.bridge_gateways:
            self.bridge_gateways[gateway_id].status = BridgeStatus.DISCONNECTED

    async def _test_upf_connection(self, upf_ip: str, upf_port: int) -> bool:
        """測試 UPF 連接"""
        try:
            # 簡化的連接測試
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)

            # 發送測試封包
            test_packet = b"test"
            sock.sendto(test_packet, (upf_ip, upf_port))
            sock.close()

            return True
        except:
            return False

    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 更新節點狀態
                await self._update_node_status()

                # 更新鏈路品質
                await self._update_link_quality()

                # 檢查橋接網關健康狀態
                await self._check_gateway_health()

                # 更新性能指標
                await self._update_performance_metrics()

                # 等待下次監控
                await asyncio.sleep(10)  # 10 秒監控間隔

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"監控循環異常: {e}")
                await asyncio.sleep(5)

    async def _update_node_status(self):
        """更新節點狀態"""
        # 模擬節點狀態更新
        for node_id, node in self.mesh_nodes.items():
            # 實際實現中會透過網路檢測節點狀態
            node.updated_at = datetime.utcnow()

    async def _update_link_quality(self):
        """更新鏈路品質"""
        # 模擬鏈路品質測量
        pass

    async def _check_gateway_health(self):
        """檢查橋接網關健康狀態"""
        for gateway_id, gateway in self.bridge_gateways.items():
            if gateway.status == BridgeStatus.CONNECTED:
                # 檢查心跳
                time_since_heartbeat = datetime.utcnow() - gateway.last_heartbeat
                if time_since_heartbeat.total_seconds() > 60:  # 60 秒超時
                    gateway.status = BridgeStatus.FAILED
                    logger.warning(f"橋接網關 {gateway.name} 心跳超時")

    async def _update_performance_metrics(self):
        """更新性能指標"""
        # 模擬性能指標更新
        for node_id in self.mesh_nodes.keys():
            if node_id not in self.performance_data:
                self.performance_data[node_id] = {}

            # 模擬數據 (實際實現會從真實監控獲取)
            self.performance_data[node_id].update(
                {
                    "packets_sent": self.performance_data[node_id].get(
                        "packets_sent", 0
                    )
                    + 100,
                    "packets_received": self.performance_data[node_id].get(
                        "packets_received", 0
                    )
                    + 95,
                    "avg_rssi": -65.0 + (hash(node_id) % 20 - 10),
                    "avg_snr": 25.0 + (hash(node_id) % 10 - 5),
                    "avg_latency": 30.0 + (hash(node_id) % 40),
                    "packet_loss_ratio": 0.01 + (hash(node_id) % 100) / 10000.0,
                }
            )

    async def _find_mesh_route(
        self, source_node: str, destination_node: str
    ) -> Optional[List[str]]:
        """尋找 Mesh 路由"""
        # 簡化的路由尋找算法 (實際會使用 AODV/OLSR 等協議)
        if source_node == destination_node:
            return [source_node]

        # 檢查直接連接
        if destination_node in [
            neighbor.node_id
            for neighbor in self.mesh_nodes.get(
                source_node,
                MeshNode(
                    node_id="",
                    name="",
                    node_type=MeshNodeType.FIXED_UNIT,
                    ip_address="",
                    mac_address="",
                ),
            ).neighbors
        ]:
            return [source_node, destination_node]

        # 多跳路由 (簡化實現)
        return [source_node, "intermediate_node", destination_node]

    async def _forward_to_mesh_network(
        self, packet_data: bytes, route_path: List[str], qos_policy: Dict[str, Any]
    ):
        """轉發到 Mesh 網路"""
        # 模擬封包轉發
        logger.debug(f"轉發封包路徑: {' -> '.join(route_path)}")

    async def _update_gateway_stats(
        self, gateway_id: str, direction: str, bytes_count: int
    ):
        """更新網關統計"""
        gateway = self.bridge_gateways[gateway_id]
        if direction == "5g_to_mesh":
            gateway.throughput_mbps = bytes_count * 8 / 1024 / 1024  # 簡化計算
        elif direction == "mesh_to_5g":
            gateway.throughput_mbps = bytes_count * 8 / 1024 / 1024  # 簡化計算

    async def _calculate_connectivity_matrix(self) -> Dict[str, Dict[str, bool]]:
        """計算連通性矩陣"""
        matrix = {}
        for node_id in self.mesh_nodes.keys():
            matrix[node_id] = {}
            for other_node_id in self.mesh_nodes.keys():
                matrix[node_id][other_node_id] = node_id == other_node_id
        return matrix

    async def _calculate_network_diameter(self) -> int:
        """計算網路直徑"""
        return len(self.mesh_nodes)  # 簡化計算

    async def _calculate_average_path_length(self) -> float:
        """計算平均路徑長度"""
        return 2.5  # 簡化計算

    async def _load_mesh_node(self, node_id: str) -> Optional[MeshNode]:
        """載入 Mesh 節點"""
        try:
            node_data = await self.mongo_adapter.find_one(
                "mesh_nodes", {"node_id": node_id}
            )
            if node_data:
                return MeshNode(**node_data)
            return None
        except Exception as e:
            logger.error(f"載入 Mesh 節點失敗: {e}")
            return None

    async def _recalculate_routes(self, node_id: str):
        """重新計算路由"""
        # 實現路由重新計算邏輯
        pass

    async def _update_mesh_routing_table(self, node_id: str):
        """更新 Mesh 路由表"""
        # 實現路由表更新邏輯
        pass

    # ===== Stage 5: 動態路由最佳化擴展 =====

    async def optimize_dynamic_routing(
        self, optimization_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """動態路由最佳化"""
        try:
            # 分析當前網路狀態
            network_state = await self._analyze_network_state()

            # 檢測瓶頸和擁塞
            bottlenecks = await self._detect_network_bottlenecks()

            # 計算最佳路由
            optimized_routes = await self._calculate_optimized_routes(
                network_state, bottlenecks, optimization_params
            )

            # 應用路由優化
            optimization_results = await self._apply_route_optimization(
                optimized_routes
            )

            # 監控優化效果
            await self._monitor_optimization_effects(optimization_results)

            return {
                "success": True,
                "optimization_id": f"opt_{uuid4().hex[:8]}",
                "network_state": network_state,
                "bottlenecks_detected": len(bottlenecks),
                "routes_optimized": len(optimized_routes),
                "improvement_metrics": optimization_results,
            }

        except Exception as e:
            logger.error(f"動態路由最佳化失敗: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_network_state(self) -> Dict[str, Any]:
        """分析網路狀態"""
        active_nodes = sum(
            1
            for node in self.mesh_nodes.values()
            if node.status == MeshNodeStatus.ACTIVE
        )

        total_links = 0
        total_bandwidth = 0.0
        total_latency = 0.0
        link_utilization = []

        for node in self.mesh_nodes.values():
            if node.status == MeshNodeStatus.ACTIVE:
                total_links += len(node.neighbors)
                for neighbor in node.neighbors:
                    total_bandwidth += neighbor.link_quality.bandwidth_mbps
                    total_latency += neighbor.link_quality.latency_ms
                    link_utilization.append(neighbor.link_quality.utilization)

        avg_latency = total_latency / max(1, total_links)
        avg_utilization = sum(link_utilization) / max(1, len(link_utilization))

        return {
            "active_nodes": active_nodes,
            "total_nodes": len(self.mesh_nodes),
            "total_links": total_links,
            "average_latency_ms": avg_latency,
            "average_bandwidth_mbps": total_bandwidth / max(1, total_links),
            "average_utilization": avg_utilization,
            "network_connectivity": active_nodes / max(1, len(self.mesh_nodes)),
            "topology_stability": await self._calculate_topology_stability(),
        }

    async def _detect_network_bottlenecks(self) -> List[Dict[str, Any]]:
        """檢測網路瓶頸"""
        bottlenecks = []

        # 檢測高負載節點
        for node_id, node in self.mesh_nodes.items():
            if node.status == MeshNodeStatus.ACTIVE:
                cpu_utilization = getattr(node, "cpu_utilization", 50.0)
                memory_utilization = getattr(node, "memory_utilization", 40.0)

                if cpu_utilization > 80.0 or memory_utilization > 85.0:
                    bottlenecks.append(
                        {
                            "type": "high_load_node",
                            "node_id": node_id,
                            "cpu_utilization": cpu_utilization,
                            "memory_utilization": memory_utilization,
                            "severity": "high" if cpu_utilization > 90.0 else "medium",
                        }
                    )

        # 檢測擁塞連結
        for node in self.mesh_nodes.values():
            for neighbor in node.neighbors:
                if neighbor.link_quality.utilization > 0.8:
                    bottlenecks.append(
                        {
                            "type": "congested_link",
                            "source_node": node.node_id,
                            "target_node": neighbor.node_id,
                            "utilization": neighbor.link_quality.utilization,
                            "bandwidth_mbps": neighbor.link_quality.bandwidth_mbps,
                            "severity": (
                                "high"
                                if neighbor.link_quality.utilization > 0.9
                                else "medium"
                            ),
                        }
                    )

        # 檢測孤立節點
        for node_id, node in self.mesh_nodes.items():
            if node.status == MeshNodeStatus.ACTIVE and len(node.neighbors) < 2:
                bottlenecks.append(
                    {
                        "type": "isolated_node",
                        "node_id": node_id,
                        "neighbor_count": len(node.neighbors),
                        "severity": "high" if len(node.neighbors) == 0 else "medium",
                    }
                )

        return bottlenecks

    async def _calculate_optimized_routes(
        self,
        network_state: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """計算最佳化路由"""
        optimized_routes = []

        # 獲取所有活躍的源-目標節點對
        active_nodes = [
            node_id
            for node_id, node in self.mesh_nodes.items()
            if node.status == MeshNodeStatus.ACTIVE
        ]

        optimization_algorithm = params.get("algorithm", "load_balanced")

        for source in active_nodes:
            for destination in active_nodes:
                if source != destination:
                    # 計算不同類型的最佳路由
                    if optimization_algorithm == "load_balanced":
                        route = await self._find_load_balanced_route(
                            source, destination, bottlenecks
                        )
                    elif optimization_algorithm == "low_latency":
                        route = await self._find_low_latency_route(source, destination)
                    elif optimization_algorithm == "high_bandwidth":
                        route = await self._find_high_bandwidth_route(
                            source, destination
                        )
                    else:
                        route = await self._find_adaptive_route(
                            source, destination, network_state, bottlenecks
                        )

                    if route:
                        optimized_routes.append(route)

        return optimized_routes

    async def _find_load_balanced_route(
        self, source: str, destination: str, bottlenecks: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """尋找負載平衡路由"""
        # 獲取高負載節點列表
        high_load_nodes = {
            b["node_id"] for b in bottlenecks if b["type"] == "high_load_node"
        }

        # 使用修改過的Dijkstra算法，避開高負載節點
        distances = {node_id: float("inf") for node_id in self.mesh_nodes}
        distances[source] = 0
        previous = {}
        unvisited = set(self.mesh_nodes.keys())

        while unvisited:
            current = min(unvisited, key=lambda x: distances[x])
            if current == destination:
                break

            unvisited.remove(current)

            current_node = self.mesh_nodes[current]
            for neighbor in current_node.neighbors:
                neighbor_id = neighbor.node_id
                if neighbor_id in unvisited:
                    # 計算權重：考慮負載和距離
                    base_weight = 1.0

                    # 高負載節點權重懲罰
                    if neighbor_id in high_load_nodes:
                        base_weight += 5.0

                    # 連結利用率懲罰
                    utilization_penalty = neighbor.link_quality.utilization * 3.0
                    weight = base_weight + utilization_penalty

                    alt_distance = distances[current] + weight
                    if alt_distance < distances[neighbor_id]:
                        distances[neighbor_id] = alt_distance
                        previous[neighbor_id] = current

        # 重建路徑
        if destination not in previous and destination != source:
            return None

        path = []
        current = destination
        while current in previous:
            path.append(current)
            current = previous[current]
        path.append(source)
        path.reverse()

        return {
            "route_id": f"route_{uuid4().hex[:8]}",
            "source": source,
            "destination": destination,
            "path": path,
            "algorithm": "load_balanced",
            "cost_metric": distances[destination],
            "avoids_bottlenecks": len(set(path) & high_load_nodes) == 0,
        }

    async def _find_adaptive_route(
        self,
        source: str,
        destination: str,
        network_state: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """尋找自適應路由"""
        # 根據網路狀態動態選擇路由策略

        network_load = network_state.get("average_utilization", 0.5)
        network_latency = network_state.get("average_latency_ms", 50.0)

        if network_load > 0.8:
            # 高負載：優先負載平衡
            return await self._find_load_balanced_route(
                source, destination, bottlenecks
            )
        elif network_latency > 100.0:
            # 高延遲：優先低延遲路由
            return await self._find_low_latency_route(source, destination)
        else:
            # 正常狀態：綜合優化
            return await self._find_balanced_optimal_route(
                source, destination, network_state
            )

    async def _find_balanced_optimal_route(
        self, source: str, destination: str, network_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """尋找平衡最佳路由"""
        # 多目標優化：延遲、頻寬、負載

        distances = {node_id: float("inf") for node_id in self.mesh_nodes}
        distances[source] = 0
        previous = {}
        unvisited = set(self.mesh_nodes.keys())

        while unvisited:
            current = min(unvisited, key=lambda x: distances[x])
            if current == destination:
                break

            unvisited.remove(current)

            current_node = self.mesh_nodes[current]
            for neighbor in current_node.neighbors:
                neighbor_id = neighbor.node_id
                if neighbor_id in unvisited:
                    # 多因子權重計算
                    latency_weight = neighbor.link_quality.latency_ms / 100.0
                    bandwidth_weight = 100.0 / max(
                        1.0, neighbor.link_quality.bandwidth_mbps
                    )
                    utilization_weight = neighbor.link_quality.utilization * 2.0

                    total_weight = (
                        latency_weight * 0.4
                        + bandwidth_weight * 0.3
                        + utilization_weight * 0.3
                    )

                    alt_distance = distances[current] + total_weight
                    if alt_distance < distances[neighbor_id]:
                        distances[neighbor_id] = alt_distance
                        previous[neighbor_id] = current

        # 重建路徑
        if destination not in previous and destination != source:
            return None

        path = []
        current = destination
        while current in previous:
            path.append(current)
            current = previous[current]
        path.append(source)
        path.reverse()

        return {
            "route_id": f"route_{uuid4().hex[:8]}",
            "source": source,
            "destination": destination,
            "path": path,
            "algorithm": "balanced_optimal",
            "cost_metric": distances[destination],
            "optimization_factors": ["latency", "bandwidth", "load"],
        }

    async def _apply_route_optimization(
        self, optimized_routes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """應用路由優化"""
        applied_routes = 0
        improved_paths = 0
        total_improvement = 0.0

        for route in optimized_routes:
            try:
                # 更新路由表
                route_key = f"{route['source']}_{route['destination']}"

                # 記錄舊路由指標
                old_metrics = await self._get_current_route_metrics(
                    route["source"], route["destination"]
                )

                # 應用新路由
                await self._update_route_in_topology(route)

                # 計算改善效果
                new_metrics = await self._calculate_route_metrics(route["path"])
                improvement = await self._calculate_route_improvement(
                    old_metrics, new_metrics
                )

                if improvement > 0:
                    improved_paths += 1
                    total_improvement += improvement

                applied_routes += 1

            except Exception as e:
                logger.warning(f"應用路由 {route['route_id']} 失敗: {e}")

        avg_improvement = total_improvement / max(1, improved_paths)

        return {
            "total_routes": len(optimized_routes),
            "applied_routes": applied_routes,
            "improved_paths": improved_paths,
            "average_improvement_percent": avg_improvement,
            "optimization_timestamp": datetime.now().isoformat(),
        }

    async def _calculate_topology_stability(self) -> float:
        """計算拓撲穩定性"""
        # 簡化的穩定性計算
        active_ratio = sum(
            1
            for node in self.mesh_nodes.values()
            if node.status == MeshNodeStatus.ACTIVE
        ) / max(1, len(self.mesh_nodes))

        connectivity_score = 0.0
        if self.mesh_nodes:
            total_connections = sum(
                len(node.neighbors) for node in self.mesh_nodes.values()
            )
            max_possible = len(self.mesh_nodes) * (len(self.mesh_nodes) - 1)
            connectivity_score = total_connections / max(1, max_possible)

        stability = active_ratio * 0.6 + connectivity_score * 0.4
        return min(1.0, stability)

    async def implement_intelligent_switching(
        self, switching_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """實現智能換手決策"""
        try:
            # 分析換手觸發條件
            switch_triggers = await self._analyze_switch_triggers(switching_params)

            # 評估換手候選
            switch_candidates = await self._evaluate_switch_candidates(switch_triggers)

            # 執行智能換手決策
            switch_decisions = await self._make_intelligent_switch_decisions(
                switch_candidates
            )

            # 執行換手操作
            switch_results = await self._execute_network_switches(switch_decisions)

            return {
                "success": True,
                "switching_session_id": f"switch_{uuid4().hex[:8]}",
                "triggers_detected": len(switch_triggers),
                "candidates_evaluated": len(switch_candidates),
                "switches_executed": len(switch_results),
                "switching_summary": switch_results,
            }

        except Exception as e:
            logger.error(f"智能換手決策失敗: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_switch_triggers(
        self, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """分析換手觸發條件"""
        triggers = []

        # 信號質量觸發
        signal_threshold = params.get("signal_threshold_dbm", -85.0)

        # 負載觸發
        load_threshold = params.get("load_threshold", 0.8)

        # 延遲觸發
        latency_threshold = params.get("latency_threshold_ms", 100.0)

        for node_id, node in self.mesh_nodes.items():
            if node.status == MeshNodeStatus.ACTIVE:
                # 檢查信號質量
                avg_signal = sum(
                    neighbor.link_quality.signal_strength for neighbor in node.neighbors
                ) / max(1, len(node.neighbors))

                if avg_signal < signal_threshold:
                    triggers.append(
                        {
                            "type": "poor_signal_quality",
                            "node_id": node_id,
                            "current_signal": avg_signal,
                            "threshold": signal_threshold,
                            "severity": (
                                "high"
                                if avg_signal < signal_threshold - 10
                                else "medium"
                            ),
                        }
                    )

                # 檢查負載
                avg_load = sum(
                    neighbor.link_quality.utilization for neighbor in node.neighbors
                ) / max(1, len(node.neighbors))

                if avg_load > load_threshold:
                    triggers.append(
                        {
                            "type": "high_load",
                            "node_id": node_id,
                            "current_load": avg_load,
                            "threshold": load_threshold,
                            "severity": "high" if avg_load > 0.9 else "medium",
                        }
                    )

        return triggers

    async def get_enhanced_bridge_performance(self) -> Dict[str, Any]:
        """獲取增強橋接性能指標"""
        base_performance = await self.get_bridge_performance()

        # 添加新的階段五指標
        routing_efficiency = await self._calculate_routing_efficiency()
        switching_performance = await self._calculate_switching_performance()
        optimization_status = await self._get_optimization_status()

        enhanced_metrics = {
            **base_performance,
            "stage5_enhancements": {
                "routing_efficiency": routing_efficiency,
                "switching_performance": switching_performance,
                "optimization_status": optimization_status,
                "adaptive_algorithms_active": True,
                "intelligent_switching_enabled": True,
            },
        }

        return enhanced_metrics

    async def _calculate_routing_efficiency(self) -> Dict[str, float]:
        """計算路由效率"""
        total_routes = len(self.mesh_nodes) * (len(self.mesh_nodes) - 1)
        if total_routes == 0:
            return {"efficiency_score": 0.0, "optimal_paths_ratio": 0.0}

        optimal_paths = 0
        total_hops = 0

        # 簡化計算
        for node in self.mesh_nodes.values():
            if node.status == MeshNodeStatus.ACTIVE:
                optimal_paths += len(node.neighbors)
                total_hops += len(node.neighbors) * 1.5  # 假設平均1.5跳

        efficiency_score = optimal_paths / max(1, total_routes) * 100
        avg_hops = total_hops / max(1, optimal_paths)

        return {
            "efficiency_score": min(100.0, efficiency_score),
            "average_hops": avg_hops,
            "optimal_paths_ratio": optimal_paths / max(1, total_routes),
        }
