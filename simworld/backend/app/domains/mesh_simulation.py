"""
Mesh 網路模擬模組
為 NetStack Mesh 橋接服務提供模擬的 Mesh 節點數據
"""

import asyncio
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field
import numpy as np


class MeshNodeSimulation(BaseModel):
    """Mesh 節點模擬數據"""

    node_id: str = Field(..., description="節點 ID")
    name: str = Field(..., description="節點名稱")
    node_type: str = Field(..., description="節點類型")

    # 位置信息
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: float = Field(default=0.0, description="海拔高度")

    # 移動參數
    velocity_mps: float = Field(default=0.0, description="移動速度 (m/s)")
    heading_degrees: float = Field(default=0.0, description="航向角度")

    # 網路狀態
    is_active: bool = Field(default=True, description="是否活躍")
    signal_strength_dbm: float = Field(default=-70.0, description="信號強度")
    throughput_mbps: float = Field(default=10.0, description="吞吐量")
    packet_loss_rate: float = Field(default=0.01, description="封包丟失率")

    # 電源狀態
    battery_level_percent: float = Field(default=100.0, description="電池電量")
    power_consumption_w: float = Field(default=5.0, description="功耗")

    # 時間戳
    last_update: datetime = Field(
        default_factory=datetime.utcnow, description="最後更新時間"
    )


class MeshLinkSimulation(BaseModel):
    """Mesh 鏈路模擬數據"""

    link_id: str = Field(..., description="鏈路 ID")
    source_node_id: str = Field(..., description="源節點 ID")
    target_node_id: str = Field(..., description="目標節點 ID")

    # 鏈路品質
    distance_meters: float = Field(..., description="距離 (米)")
    rssi_dbm: float = Field(..., description="RSSI")
    snr_db: float = Field(..., description="SNR")
    link_quality: float = Field(..., description="鏈路品質 (0-1)")

    # 性能指標
    latency_ms: float = Field(default=50.0, description="延遲")
    bandwidth_mbps: float = Field(default=5.0, description="頻寬")

    # 狀態
    is_active: bool = Field(default=True, description="是否活躍")
    last_update: datetime = Field(
        default_factory=datetime.utcnow, description="最後更新時間"
    )


class MeshNetworkSimulator:
    """Mesh 網路模擬器"""

    def __init__(self):
        self.mesh_nodes: Dict[str, MeshNodeSimulation] = {}
        self.mesh_links: Dict[str, MeshLinkSimulation] = {}
        self.simulation_running = False
        self.simulation_task: Optional[asyncio.Task] = None

        # 模擬參數
        self.max_communication_range_m = 1000.0  # 最大通信距離
        self.signal_propagation_speed_mps = 3e8  # 電磁波傳播速度
        self.environment_noise_floor_dbm = -100.0  # 環境噪音底板

        # 場景邊界 (台灣地區示例)
        self.scenario_bounds = {
            "min_lat": 23.5,
            "max_lat": 25.5,
            "min_lon": 120.0,
            "max_lon": 122.0,
            "min_alt": 0.0,
            "max_alt": 500.0,
        }

    async def start_simulation(self) -> bool:
        """啟動 Mesh 網路模擬"""
        try:
            if self.simulation_running:
                return True

            # 初始化預設節點
            await self._initialize_default_nodes()

            # 啟動模擬循環
            self.simulation_task = asyncio.create_task(self._simulation_loop())
            self.simulation_running = True

            print("🌐 Mesh 網路模擬已啟動")
            return True

        except Exception as e:
            print(f"❌ Mesh 網路模擬啟動失敗: {e}")
            return False

    async def stop_simulation(self) -> bool:
        """停止 Mesh 網路模擬"""
        try:
            self.simulation_running = False

            if self.simulation_task:
                self.simulation_task.cancel()
                await self.simulation_task

            print("🛑 Mesh 網路模擬已停止")
            return True

        except Exception as e:
            print(f"❌ Mesh 網路模擬停止失敗: {e}")
            return False

    async def add_mesh_node(
        self, node_data: Dict[str, Any]
    ) -> Optional[MeshNodeSimulation]:
        """添加 Mesh 節點"""
        try:
            node = MeshNodeSimulation(
                node_id=node_data["node_id"],
                name=node_data["name"],
                node_type=node_data.get("node_type", "fixed_unit"),
                latitude=node_data["latitude"],
                longitude=node_data["longitude"],
                altitude=node_data.get("altitude", 0.0),
                velocity_mps=node_data.get("velocity_mps", 0.0),
                heading_degrees=node_data.get("heading_degrees", 0.0),
            )

            self.mesh_nodes[node.node_id] = node

            # 重新計算鏈路
            await self._update_mesh_links()

            print(f"✅ 添加 Mesh 節點: {node.name}")
            return node

        except Exception as e:
            print(f"❌ 添加 Mesh 節點失敗: {e}")
            return None

    async def remove_mesh_node(self, node_id: str) -> bool:
        """移除 Mesh 節點"""
        try:
            if node_id in self.mesh_nodes:
                del self.mesh_nodes[node_id]

                # 移除相關鏈路
                links_to_remove = [
                    link_id
                    for link_id, link in self.mesh_links.items()
                    if link.source_node_id == node_id or link.target_node_id == node_id
                ]

                for link_id in links_to_remove:
                    del self.mesh_links[link_id]

                print(f"✅ 移除 Mesh 節點: {node_id}")
                return True

            return False

        except Exception as e:
            print(f"❌ 移除 Mesh 節點失敗: {e}")
            return False

    async def update_node_position(
        self, node_id: str, latitude: float, longitude: float, altitude: float = 0.0
    ) -> bool:
        """更新節點位置"""
        try:
            if node_id in self.mesh_nodes:
                node = self.mesh_nodes[node_id]
                node.latitude = latitude
                node.longitude = longitude
                node.altitude = altitude
                node.last_update = datetime.utcnow()

                # 重新計算相關鏈路
                await self._update_mesh_links()

                return True

            return False

        except Exception as e:
            print(f"❌ 更新節點位置失敗: {e}")
            return False

    async def get_mesh_nodes(self) -> List[Dict[str, Any]]:
        """獲取所有 Mesh 節點"""
        try:
            nodes_data = []
            for node in self.mesh_nodes.values():
                nodes_data.append(
                    {
                        "node_id": node.node_id,
                        "name": node.name,
                        "node_type": node.node_type,
                        "position": {
                            "latitude": node.latitude,
                            "longitude": node.longitude,
                            "altitude": node.altitude,
                        },
                        "status": {
                            "is_active": node.is_active,
                            "signal_strength_dbm": node.signal_strength_dbm,
                            "throughput_mbps": node.throughput_mbps,
                            "packet_loss_rate": node.packet_loss_rate,
                            "battery_level_percent": node.battery_level_percent,
                        },
                        "last_update": node.last_update.isoformat(),
                    }
                )

            return nodes_data

        except Exception as e:
            print(f"❌ 獲取 Mesh 節點失敗: {e}")
            return []

    async def get_mesh_links(self) -> List[Dict[str, Any]]:
        """獲取所有 Mesh 鏈路"""
        try:
            links_data = []
            for link in self.mesh_links.values():
                links_data.append(
                    {
                        "link_id": link.link_id,
                        "source_node_id": link.source_node_id,
                        "target_node_id": link.target_node_id,
                        "quality": {
                            "distance_meters": link.distance_meters,
                            "rssi_dbm": link.rssi_dbm,
                            "snr_db": link.snr_db,
                            "link_quality": link.link_quality,
                            "latency_ms": link.latency_ms,
                            "bandwidth_mbps": link.bandwidth_mbps,
                        },
                        "is_active": link.is_active,
                        "last_update": link.last_update.isoformat(),
                    }
                )

            return links_data

        except Exception as e:
            print(f"❌ 獲取 Mesh 鏈路失敗: {e}")
            return []

    async def get_network_topology(self) -> Dict[str, Any]:
        """獲取網路拓撲"""
        try:
            nodes_data = await self.get_mesh_nodes()
            links_data = await self.get_mesh_links()

            # 計算網路統計
            total_nodes = len(nodes_data)
            active_nodes = sum(1 for node in nodes_data if node["status"]["is_active"])
            total_links = len(links_data)
            active_links = sum(1 for link in links_data if link["is_active"])

            avg_link_quality = (
                np.mean([link["quality"]["link_quality"] for link in links_data])
                if links_data
                else 0.0
            )

            topology = {
                "timestamp": datetime.utcnow().isoformat(),
                "network_stats": {
                    "total_nodes": total_nodes,
                    "active_nodes": active_nodes,
                    "total_links": total_links,
                    "active_links": active_links,
                    "average_link_quality": float(avg_link_quality),
                    "connectivity_ratio": active_links / max(1, total_links),
                },
                "nodes": nodes_data,
                "links": links_data,
            }

            return topology

        except Exception as e:
            print(f"❌ 獲取網路拓撲失敗: {e}")
            return {}

    async def simulate_interference(
        self, interference_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """模擬干擾效應"""
        try:
            interference_source = {
                "latitude": interference_data.get("latitude", 24.0),
                "longitude": interference_data.get("longitude", 121.0),
                "power_dbm": interference_data.get("power_dbm", 30.0),
                "frequency_mhz": interference_data.get("frequency_mhz", 900.0),
                "type": interference_data.get("type", "continuous"),
            }

            affected_nodes = []

            for node in self.mesh_nodes.values():
                # 計算距離
                distance = self._calculate_distance(
                    node.latitude,
                    node.longitude,
                    interference_source["latitude"],
                    interference_source["longitude"],
                )

                # 計算干擾影響
                if distance < 5000:  # 5km 影響範圍
                    interference_level = interference_source["power_dbm"] / (
                        1 + distance / 100
                    )

                    # 影響信號品質
                    original_signal = node.signal_strength_dbm
                    node.signal_strength_dbm -= interference_level * 0.1
                    node.packet_loss_rate += interference_level * 0.001

                    affected_nodes.append(
                        {
                            "node_id": node.node_id,
                            "distance_to_interference": distance,
                            "interference_level": interference_level,
                            "signal_degradation": original_signal
                            - node.signal_strength_dbm,
                        }
                    )

            return {
                "interference_applied": True,
                "affected_nodes_count": len(affected_nodes),
                "affected_nodes": affected_nodes,
                "interference_source": interference_source,
            }

        except Exception as e:
            print(f"❌ 模擬干擾失敗: {e}")
            return {"interference_applied": False, "error": str(e)}

    # 私有方法

    async def _initialize_default_nodes(self):
        """初始化預設節點"""
        default_nodes = [
            {
                "node_id": "mesh_gw_001",
                "name": "Gateway_Node_1",
                "node_type": "ground_station",
                "latitude": 25.0330,
                "longitude": 121.5654,
                "altitude": 0.0,
            },
            {
                "node_id": "mesh_uav_001",
                "name": "UAV_Relay_1",
                "node_type": "uav_relay",
                "latitude": 25.0430,
                "longitude": 121.5754,
                "altitude": 100.0,
                "velocity_mps": 15.0,
                "heading_degrees": 45.0,
            },
            {
                "node_id": "mesh_uav_002",
                "name": "UAV_Relay_2",
                "node_type": "uav_relay",
                "latitude": 25.0230,
                "longitude": 121.5554,
                "altitude": 120.0,
                "velocity_mps": 12.0,
                "heading_degrees": 135.0,
            },
            {
                "node_id": "mesh_mobile_001",
                "name": "Mobile_Unit_1",
                "node_type": "mobile_unit",
                "latitude": 25.0380,
                "longitude": 121.5600,
                "altitude": 5.0,
                "velocity_mps": 20.0,
                "heading_degrees": 90.0,
            },
        ]

        for node_data in default_nodes:
            await self.add_mesh_node(node_data)

    async def _simulation_loop(self):
        """模擬主循環"""
        while self.simulation_running:
            try:
                # 更新移動節點位置
                await self._update_mobile_nodes()

                # 更新節點狀態
                await self._update_node_status()

                # 更新鏈路品質
                await self._update_mesh_links()

                # 模擬環境變化
                await self._simulate_environment_changes()

                # 等待下次更新
                await asyncio.sleep(5.0)  # 5 秒更新間隔

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"模擬循環錯誤: {e}")
                await asyncio.sleep(1.0)

    async def _update_mobile_nodes(self):
        """更新移動節點位置"""
        for node in self.mesh_nodes.values():
            if node.velocity_mps > 0:
                # 計算新位置
                time_delta = 5.0  # 5 秒時間步
                distance_m = node.velocity_mps * time_delta

                # 轉換為度數變化
                lat_change = (
                    distance_m * math.cos(math.radians(node.heading_degrees))
                ) / 111320.0
                lon_change = (
                    distance_m * math.sin(math.radians(node.heading_degrees))
                ) / (111320.0 * math.cos(math.radians(node.latitude)))

                node.latitude += lat_change
                node.longitude += lon_change

                # 邊界檢查
                node.latitude = max(
                    self.scenario_bounds["min_lat"],
                    min(self.scenario_bounds["max_lat"], node.latitude),
                )
                node.longitude = max(
                    self.scenario_bounds["min_lon"],
                    min(self.scenario_bounds["max_lon"], node.longitude),
                )

                # 隨機調整航向 (模擬真實移動)
                if random.random() < 0.1:  # 10% 機率改變航向
                    node.heading_degrees += random.uniform(-30, 30)
                    node.heading_degrees %= 360

                node.last_update = datetime.utcnow()

    async def _update_node_status(self):
        """更新節點狀態"""
        for node in self.mesh_nodes.values():
            # 模擬電池消耗
            if node.node_type in ["uav_relay", "mobile_unit"]:
                consumption_rate = 0.05  # 每次更新消耗 0.05%
                node.battery_level_percent = max(
                    0.0, node.battery_level_percent - consumption_rate
                )

                # 電池低於 10% 時影響性能
                if node.battery_level_percent < 10.0:
                    node.signal_strength_dbm -= 5.0
                    node.throughput_mbps *= 0.8

            # 模擬信號變化
            node.signal_strength_dbm += random.uniform(-2.0, 2.0)
            node.signal_strength_dbm = max(-100.0, min(-30.0, node.signal_strength_dbm))

            # 模擬吞吐量變化
            node.throughput_mbps += random.uniform(-1.0, 1.0)
            node.throughput_mbps = max(0.1, min(50.0, node.throughput_mbps))

            # 模擬封包丟失率
            base_loss_rate = 0.01
            if node.signal_strength_dbm < -80.0:
                base_loss_rate += (80.0 + node.signal_strength_dbm) * 0.001

            node.packet_loss_rate = base_loss_rate + random.uniform(-0.005, 0.005)
            node.packet_loss_rate = max(0.0, min(0.5, node.packet_loss_rate))

    async def _update_mesh_links(self):
        """更新 Mesh 鏈路"""
        # 清除現有鏈路
        self.mesh_links.clear()

        node_list = list(self.mesh_nodes.values())

        for i, source_node in enumerate(node_list):
            for j, target_node in enumerate(node_list[i + 1 :], i + 1):
                # 計算距離
                distance = self._calculate_distance(
                    source_node.latitude,
                    source_node.longitude,
                    target_node.latitude,
                    target_node.longitude,
                )

                # 檢查是否在通信範圍內
                if distance <= self.max_communication_range_m:
                    link_id = f"{source_node.node_id}_{target_node.node_id}"

                    # 計算鏈路品質
                    rssi = self._calculate_rssi(
                        distance, source_node.signal_strength_dbm
                    )
                    snr = self._calculate_snr(rssi)
                    link_quality = self._calculate_link_quality(rssi, snr)

                    # 計算延遲
                    propagation_delay = (
                        distance / self.signal_propagation_speed_mps * 1000
                    )  # ms
                    processing_delay = random.uniform(10, 50)  # ms
                    latency = propagation_delay + processing_delay

                    # 計算頻寬
                    bandwidth = self._calculate_bandwidth(link_quality)

                    link = MeshLinkSimulation(
                        link_id=link_id,
                        source_node_id=source_node.node_id,
                        target_node_id=target_node.node_id,
                        distance_meters=distance,
                        rssi_dbm=rssi,
                        snr_db=snr,
                        link_quality=link_quality,
                        latency_ms=latency,
                        bandwidth_mbps=bandwidth,
                        is_active=link_quality > 0.2,  # 品質閾值
                    )

                    self.mesh_links[link_id] = link

    async def _simulate_environment_changes(self):
        """模擬環境變化"""
        # 隨機產生環境干擾
        if random.random() < 0.05:  # 5% 機率發生環境變化
            for node in self.mesh_nodes.values():
                # 模擬天氣影響
                weather_impact = random.uniform(-5.0, 2.0)
                node.signal_strength_dbm += weather_impact

                # 模擬建築物遮蔽
                if random.random() < 0.1:  # 10% 機率遮蔽
                    node.signal_strength_dbm -= random.uniform(10.0, 20.0)

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """計算兩點間距離 (Haversine 公式)"""
        R = 6371000  # 地球半徑 (米)

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    def _calculate_rssi(self, distance: float, tx_power: float) -> float:
        """計算 RSSI"""
        if distance <= 0:
            return tx_power

        # Free space path loss 模型
        path_loss_db = (
            20 * math.log10(distance)
            + 20 * math.log10(900e6)
            + 20 * math.log10(4 * math.pi / 3e8)
        )
        rssi = tx_power - path_loss_db

        # 添加隨機衰落
        fading = random.uniform(-10.0, 5.0)
        rssi += fading

        return rssi

    def _calculate_snr(self, rssi: float) -> float:
        """計算 SNR"""
        noise_power = self.environment_noise_floor_dbm
        snr = rssi - noise_power
        return max(0.0, snr)

    def _calculate_link_quality(self, rssi: float, snr: float) -> float:
        """計算鏈路品質 (0-1)"""
        # 基於 RSSI 和 SNR 的品質評估
        rssi_quality = max(
            0.0, min(1.0, (rssi + 100) / 70)
        )  # -100 到 -30 dBm 映射到 0-1
        snr_quality = max(0.0, min(1.0, snr / 40))  # 0 到 40 dB 映射到 0-1

        # 加權平均
        quality = 0.6 * rssi_quality + 0.4 * snr_quality
        return quality

    def _calculate_bandwidth(self, link_quality: float) -> float:
        """根據鏈路品質計算可用頻寬"""
        max_bandwidth = 20.0  # Mbps
        bandwidth = max_bandwidth * link_quality
        return max(0.1, bandwidth)


# 全局模擬器實例
mesh_simulator = MeshNetworkSimulator()
