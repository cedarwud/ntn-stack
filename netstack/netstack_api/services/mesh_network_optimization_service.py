"""
Mesh 網路優化服務 (Mesh Network Optimization Service)

實現智能Mesh網路優化、動態路由選擇和網路拓撲自動調整。
基於現有 MeshBridgeService 和 UAVMeshFailoverService 架構。
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json

import structlog
import numpy as np
from pydantic import BaseModel

from ..models.uav_models import UAVPosition, UAVSignalQuality

logger = structlog.get_logger(__name__)


class NetworkProtocol(Enum):
    """網路協議類型"""
    SATELLITE_5G = "satellite_5g"
    UAV_MESH = "uav_mesh"
    TERRESTRIAL_4G = "terrestrial_4g"
    WIFI_DIRECT = "wifi_direct"
    LORA_WAN = "lora_wan"


class RoutingAlgorithm(Enum):
    """路由演算法"""
    SHORTEST_PATH = "shortest_path"        # 最短路徑
    LEAST_LATENCY = "least_latency"       # 最小延遲
    HIGHEST_BANDWIDTH = "highest_bandwidth" # 最大頻寬
    LOAD_BALANCED = "load_balanced"       # 負載平衡
    ENERGY_EFFICIENT = "energy_efficient" # 節能優化


class NetworkTopologyType(Enum):
    """網路拓撲類型"""
    STAR = "star"           # 星型
    MESH = "mesh"           # 網狀
    TREE = "tree"           # 樹型
    RING = "ring"           # 環型
    HYBRID = "hybrid"       # 混合型


@dataclass
class NetworkNode:
    """網路節點"""
    node_id: str
    node_type: str  # "uav", "satellite", "ground_station", "mesh_relay"
    position: UAVPosition
    protocol_support: List[NetworkProtocol] = field(default_factory=list)
    bandwidth_mbps: float = 100.0
    latency_ms: float = 50.0
    packet_loss_rate: float = 0.01
    energy_level: float = 100.0  # 能量水平 (%)
    cpu_usage: float = 30.0      # CPU使用率 (%)
    memory_usage: float = 40.0   # 記憶體使用率 (%)
    connection_count: int = 0    # 連接數
    is_active: bool = True
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class NetworkLink:
    """網路連結"""
    link_id: str
    source_node: str
    target_node: str
    protocol: NetworkProtocol
    bandwidth_mbps: float = 100.0
    latency_ms: float = 50.0
    reliability: float = 0.95     # 可靠性 (0-1)
    signal_strength: float = -70.0 # 信號強度 (dBm)
    distance_km: float = 1.0
    cost_metric: float = 1.0      # 路由成本
    traffic_load: float = 0.3     # 流量負載 (0-1)
    is_active: bool = True
    established_at: datetime = field(default_factory=datetime.now)


@dataclass
class RoutingPath:
    """路由路徑"""
    path_id: str
    source_node: str
    destination_node: str
    hops: List[str] = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_bandwidth_mbps: float = 0.0
    path_reliability: float = 1.0
    total_cost: float = 0.0
    algorithm_used: RoutingAlgorithm = RoutingAlgorithm.SHORTEST_PATH
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class NetworkTopology:
    """網路拓撲"""
    topology_id: str
    topology_type: NetworkTopologyType
    nodes: Dict[str, NetworkNode] = field(default_factory=dict)
    links: Dict[str, NetworkLink] = field(default_factory=dict)
    routing_paths: Dict[str, RoutingPath] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_optimization: Optional[datetime] = None


class RouteOptimizationRequest(BaseModel):
    """路由優化請求"""
    source_node: str
    destination_node: str
    algorithm: RoutingAlgorithm = RoutingAlgorithm.SHORTEST_PATH
    bandwidth_requirement_mbps: float = 10.0
    latency_requirement_ms: float = 100.0
    reliability_requirement: float = 0.9


class TopologyOptimizationRequest(BaseModel):
    """拓撲優化請求"""
    optimize_for: str = "performance"  # "performance", "energy", "reliability"
    max_hops: int = 5
    min_redundancy: int = 2


class MeshNetworkOptimizationService:
    """Mesh網路優化服務"""

    def __init__(self, mesh_bridge_service=None, uav_mesh_failover_service=None):
        self.logger = structlog.get_logger(__name__)
        self.mesh_bridge_service = mesh_bridge_service
        self.uav_mesh_failover_service = uav_mesh_failover_service
        
        # 網路拓撲
        self.network_topology = NetworkTopology(
            topology_id=f"topology_{uuid.uuid4().hex[:8]}",
            topology_type=NetworkTopologyType.HYBRID
        )
        
        # 優化參數
        self.optimization_interval = 30.0  # 優化間隔(秒)
        self.link_quality_threshold = 0.7  # 連結品質閾值
        self.load_balance_threshold = 0.8  # 負載平衡閾值
        self.energy_efficiency_weight = 0.3
        
        # 路由表和快取
        self.routing_table: Dict[Tuple[str, str], RoutingPath] = {}
        self.path_cache: Dict[str, RoutingPath] = {}
        
        # 優化任務
        self.optimization_task: Optional[asyncio.Task] = None
        self.is_optimizing = False
        
    async def start_optimization_service(self):
        """啟動優化服務"""
        if self.optimization_task is None:
            self.optimization_task = asyncio.create_task(self._optimization_loop())
            self.logger.info("Mesh網路優化服務已啟動")
    
    async def stop_optimization_service(self):
        """停止優化服務"""
        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
            self.optimization_task = None
            self.logger.info("Mesh網路優化服務已停止")
    
    async def _optimization_loop(self):
        """優化循環"""
        while True:
            try:
                await self._perform_network_optimization()
                await asyncio.sleep(self.optimization_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"網路優化循環異常: {e}")
                await asyncio.sleep(5.0)
    
    async def _perform_network_optimization(self):
        """執行網路優化"""
        if self.is_optimizing:
            return
            
        self.is_optimizing = True
        try:
            # 1. 更新網路拓撲
            await self._update_network_topology()
            
            # 2. 評估連結品質
            await self._evaluate_link_quality()
            
            # 3. 優化路由路徑
            await self._optimize_routing_paths()
            
            # 4. 負載平衡調整
            await self._perform_load_balancing()
            
            # 5. 拓撲自動調整
            await self._auto_adjust_topology()
            
            self.network_topology.last_optimization = datetime.now()
            
            self.logger.debug(
                "網路優化完成",
                nodes=len(self.network_topology.nodes),
                links=len(self.network_topology.links),
                paths=len(self.network_topology.routing_paths)
            )
            
        finally:
            self.is_optimizing = False
    
    async def _update_network_topology(self):
        """更新網路拓撲"""
        # 發現新節點
        await self._discover_network_nodes()
        
        # 檢測連結狀態
        await self._detect_network_links()
        
        # 清理非活躍節點和連結
        await self._cleanup_inactive_elements()
    
    async def _discover_network_nodes(self):
        """發現網路節點"""
        # 從UAV服務獲取UAV節點
        if self.uav_mesh_failover_service:
            try:
                # 模擬獲取UAV列表
                uav_nodes = await self._get_active_uav_nodes()
                
                for uav_id, uav_info in uav_nodes.items():
                    if uav_id not in self.network_topology.nodes:
                        node = NetworkNode(
                            node_id=uav_id,
                            node_type="uav",
                            position=uav_info["position"],
                            protocol_support=[
                                NetworkProtocol.SATELLITE_5G,
                                NetworkProtocol.UAV_MESH,
                                NetworkProtocol.WIFI_DIRECT
                            ],
                            bandwidth_mbps=100.0,
                            energy_level=uav_info.get("battery_level", 100.0)
                        )
                        self.network_topology.nodes[uav_id] = node
                        
                        self.logger.debug(f"發現新UAV節點: {uav_id}")
                        
            except Exception as e:
                self.logger.warning(f"獲取UAV節點失敗: {e}")
        
        # 添加衛星和地面站節點 (模擬)
        await self._add_infrastructure_nodes()
    
    async def _get_active_uav_nodes(self) -> Dict:
        """獲取活躍UAV節點"""
        # 模擬UAV節點數據
        return {
            "uav_001": {
                "position": UAVPosition(latitude=25.0, longitude=121.0, altitude=100.0),
                "battery_level": 85.0
            },
            "uav_002": {
                "position": UAVPosition(latitude=25.01, longitude=121.01, altitude=120.0),
                "battery_level": 92.0
            },
            "uav_003": {
                "position": UAVPosition(latitude=25.02, longitude=121.02, altitude=110.0),
                "battery_level": 78.0
            }
        }
    
    async def _add_infrastructure_nodes(self):
        """添加基礎設施節點"""
        # 衛星節點
        if "satellite_001" not in self.network_topology.nodes:
            satellite_node = NetworkNode(
                node_id="satellite_001",
                node_type="satellite",
                position=UAVPosition(latitude=25.0, longitude=121.0, altitude=550000.0),
                protocol_support=[NetworkProtocol.SATELLITE_5G],
                bandwidth_mbps=1000.0,
                latency_ms=250.0,
                energy_level=100.0
            )
            self.network_topology.nodes["satellite_001"] = satellite_node
        
        # 地面站節點
        if "ground_station_001" not in self.network_topology.nodes:
            ground_node = NetworkNode(
                node_id="ground_station_001",
                node_type="ground_station",
                position=UAVPosition(latitude=25.0, longitude=121.0, altitude=10.0),
                protocol_support=[
                    NetworkProtocol.SATELLITE_5G,
                    NetworkProtocol.TERRESTRIAL_4G
                ],
                bandwidth_mbps=500.0,
                latency_ms=20.0,
                energy_level=100.0
            )
            self.network_topology.nodes["ground_station_001"] = ground_node
    
    async def _detect_network_links(self):
        """檢測網路連結"""
        nodes = list(self.network_topology.nodes.values())
        
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                link_key = f"{node_a.node_id}_{node_b.node_id}"
                
                # 檢查是否可以建立連結
                if await self._can_establish_link(node_a, node_b):
                    if link_key not in self.network_topology.links:
                        # 創建新連結
                        link = await self._create_network_link(node_a, node_b)
                        self.network_topology.links[link_key] = link
                        
                        # 創建反向連結
                        reverse_link_key = f"{node_b.node_id}_{node_a.node_id}"
                        reverse_link = await self._create_network_link(node_b, node_a)
                        self.network_topology.links[reverse_link_key] = reverse_link
                        
                        self.logger.debug(f"建立新連結: {node_a.node_id} <-> {node_b.node_id}")
                else:
                    # 檢查現有連結是否仍有效
                    if link_key in self.network_topology.links:
                        self.network_topology.links[link_key].is_active = False
    
    async def _can_establish_link(self, node_a: NetworkNode, node_b: NetworkNode) -> bool:
        """判斷是否可以建立連結"""
        # 檢查協議兼容性
        common_protocols = set(node_a.protocol_support) & set(node_b.protocol_support)
        if not common_protocols:
            return False
        
        # 檢查距離限制
        distance = self._calculate_distance(node_a.position, node_b.position)
        
        # 根據節點類型設定最大通信距離
        if node_a.node_type == "uav" and node_b.node_type == "uav":
            max_distance = 5000.0  # UAV間5km
        elif "satellite" in [node_a.node_type, node_b.node_type]:
            max_distance = 1000000.0  # 衛星通信無限制
        else:
            max_distance = 10000.0  # 其他情況10km
        
        return distance <= max_distance
    
    async def _create_network_link(self, source: NetworkNode, target: NetworkNode) -> NetworkLink:
        """創建網路連結"""
        # 選擇最佳協議
        common_protocols = set(source.protocol_support) & set(target.protocol_support)
        protocol = self._select_best_protocol(common_protocols, source, target)
        
        # 計算連結參數
        distance = self._calculate_distance(source.position, target.position)
        bandwidth, latency = self._calculate_link_parameters(protocol, distance, source, target)
        
        link = NetworkLink(
            link_id=f"link_{uuid.uuid4().hex[:8]}",
            source_node=source.node_id,
            target_node=target.node_id,
            protocol=protocol,
            bandwidth_mbps=bandwidth,
            latency_ms=latency,
            distance_km=distance / 1000.0,
            reliability=self._calculate_link_reliability(protocol, distance),
            signal_strength=self._calculate_signal_strength(protocol, distance)
        )
        
        return link
    
    def _select_best_protocol(
        self, 
        protocols: Set[NetworkProtocol], 
        source: NetworkNode, 
        target: NetworkNode
    ) -> NetworkProtocol:
        """選擇最佳協議"""
        protocol_priority = {
            NetworkProtocol.SATELLITE_5G: 5,
            NetworkProtocol.UAV_MESH: 4,
            NetworkProtocol.TERRESTRIAL_4G: 3,
            NetworkProtocol.WIFI_DIRECT: 2,
            NetworkProtocol.LORA_WAN: 1
        }
        
        # 根據節點類型調整優先級
        if source.node_type == "uav" and target.node_type == "uav":
            # UAV間優先使用Mesh
            if NetworkProtocol.UAV_MESH in protocols:
                return NetworkProtocol.UAV_MESH
        
        # 選擇優先級最高的協議
        best_protocol = max(protocols, key=lambda p: protocol_priority.get(p, 0))
        return best_protocol
    
    def _calculate_link_parameters(
        self, 
        protocol: NetworkProtocol, 
        distance: float,
        source: NetworkNode,
        target: NetworkNode
    ) -> Tuple[float, float]:
        """計算連結參數"""
        base_params = {
            NetworkProtocol.SATELLITE_5G: (1000.0, 250.0),
            NetworkProtocol.UAV_MESH: (100.0, 20.0),
            NetworkProtocol.TERRESTRIAL_4G: (50.0, 30.0),
            NetworkProtocol.WIFI_DIRECT: (200.0, 10.0),
            NetworkProtocol.LORA_WAN: (0.3, 100.0)
        }
        
        base_bandwidth, base_latency = base_params.get(protocol, (50.0, 50.0))
        
        # 距離影響
        distance_factor = min(1.0, 1000.0 / (distance + 100.0))
        bandwidth = base_bandwidth * distance_factor
        latency = base_latency * (1.0 + distance / 10000.0)
        
        return bandwidth, latency
    
    def _calculate_link_reliability(self, protocol: NetworkProtocol, distance: float) -> float:
        """計算連結可靠性"""
        base_reliability = {
            NetworkProtocol.SATELLITE_5G: 0.95,
            NetworkProtocol.UAV_MESH: 0.90,
            NetworkProtocol.TERRESTRIAL_4G: 0.92,
            NetworkProtocol.WIFI_DIRECT: 0.88,
            NetworkProtocol.LORA_WAN: 0.85
        }
        
        reliability = base_reliability.get(protocol, 0.8)
        distance_penalty = min(0.2, distance / 50000.0)
        
        return max(0.5, reliability - distance_penalty)
    
    def _calculate_signal_strength(self, protocol: NetworkProtocol, distance: float) -> float:
        """計算信號強度"""
        # 簡化的信號強度模型
        if protocol == NetworkProtocol.SATELLITE_5G:
            return -70.0  # 衛星信號相對穩定
        else:
            # 自由空間路徑損耗模型
            path_loss = 20 * np.log10(distance) + 20 * np.log10(2400) - 147.55
            return max(-120.0, -40.0 - path_loss)
    
    async def _evaluate_link_quality(self):
        """評估連結品質"""
        for link in self.network_topology.links.values():
            if not link.is_active:
                continue
                
            # 更新連結狀態
            quality_score = await self._calculate_link_quality_score(link)
            
            # 根據品質調整連結參數
            if quality_score < self.link_quality_threshold:
                link.reliability *= 0.9
                link.traffic_load = min(1.0, link.traffic_load * 1.1)
                
                self.logger.debug(
                    f"連結品質下降: {link.source_node} -> {link.target_node}, score: {quality_score}"
                )
    
    async def _calculate_link_quality_score(self, link: NetworkLink) -> float:
        """計算連結品質分數"""
        # 綜合評估：可靠性、延遲、頻寬、負載
        reliability_score = link.reliability
        latency_score = max(0, 1.0 - link.latency_ms / 500.0)
        bandwidth_score = min(1.0, link.bandwidth_mbps / 100.0)
        load_score = max(0, 1.0 - link.traffic_load)
        
        quality_score = (
            reliability_score * 0.3 +
            latency_score * 0.3 +
            bandwidth_score * 0.2 +
            load_score * 0.2
        )
        
        return quality_score
    
    async def optimize_route(self, request: RouteOptimizationRequest) -> RoutingPath:
        """優化路由"""
        # 檢查快取
        cache_key = f"{request.source_node}_{request.destination_node}_{request.algorithm.value}"
        if cache_key in self.path_cache:
            cached_path = self.path_cache[cache_key]
            if (datetime.now() - cached_path.created_at).seconds < 60:  # 1分鐘快取
                return cached_path
        
        # 計算最佳路徑
        if request.algorithm == RoutingAlgorithm.SHORTEST_PATH:
            path = await self._find_shortest_path(request.source_node, request.destination_node)
        elif request.algorithm == RoutingAlgorithm.LEAST_LATENCY:
            path = await self._find_least_latency_path(request.source_node, request.destination_node)
        elif request.algorithm == RoutingAlgorithm.HIGHEST_BANDWIDTH:
            path = await self._find_highest_bandwidth_path(request.source_node, request.destination_node)
        elif request.algorithm == RoutingAlgorithm.LOAD_BALANCED:
            path = await self._find_load_balanced_path(request.source_node, request.destination_node)
        else:
            path = await self._find_energy_efficient_path(request.source_node, request.destination_node)
        
        path.algorithm_used = request.algorithm
        
        # 驗證路徑是否滿足需求
        if (path.total_bandwidth_mbps >= request.bandwidth_requirement_mbps and
            path.total_latency_ms <= request.latency_requirement_ms and
            path.path_reliability >= request.reliability_requirement):
            
            # 加入快取
            self.path_cache[cache_key] = path
            
            # 更新路由表
            self.routing_table[(request.source_node, request.destination_node)] = path
            self.network_topology.routing_paths[path.path_id] = path
            
            self.logger.info(
                "路由優化完成",
                source=request.source_node,
                destination=request.destination_node,
                algorithm=request.algorithm.value,
                hops=len(path.hops),
                latency=path.total_latency_ms,
                bandwidth=path.total_bandwidth_mbps
            )
            
            return path
        else:
            raise ValueError("無法找到滿足需求的路由路徑")
    
    async def _find_shortest_path(self, source: str, destination: str) -> RoutingPath:
        """尋找最短路徑 (Dijkstra演算法)"""
        # 簡化的Dijkstra實現
        distances = {node_id: float('inf') for node_id in self.network_topology.nodes}
        distances[source] = 0
        previous = {}
        unvisited = set(self.network_topology.nodes.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda x: distances[x])
            if current == destination:
                break
                
            unvisited.remove(current)
            
            # 檢查所有鄰居
            for link in self.network_topology.links.values():
                if link.source_node == current and link.is_active:
                    neighbor = link.target_node
                    if neighbor in unvisited:
                        distance = distances[current] + 1  # 跳數作為距離
                        if distance < distances[neighbor]:
                            distances[neighbor] = distance
                            previous[neighbor] = current
        
        # 重建路徑
        path_nodes = []
        current = destination
        while current in previous:
            path_nodes.append(current)
            current = previous[current]
        path_nodes.append(source)
        path_nodes.reverse()
        
        # 計算路徑指標
        total_latency, total_bandwidth, path_reliability = await self._calculate_path_metrics(path_nodes)
        
        return RoutingPath(
            path_id=f"path_{uuid.uuid4().hex[:8]}",
            source_node=source,
            destination_node=destination,
            hops=path_nodes,
            total_latency_ms=total_latency,
            total_bandwidth_mbps=total_bandwidth,
            path_reliability=path_reliability
        )
    
    async def _calculate_path_metrics(self, path_nodes: List[str]) -> Tuple[float, float, float]:
        """計算路徑指標"""
        total_latency = 0.0
        min_bandwidth = float('inf')
        path_reliability = 1.0
        
        for i in range(len(path_nodes) - 1):
            source_node = path_nodes[i]
            target_node = path_nodes[i + 1]
            
            # 尋找連結
            link_key = f"{source_node}_{target_node}"
            link = self.network_topology.links.get(link_key)
            
            if link and link.is_active:
                total_latency += link.latency_ms
                min_bandwidth = min(min_bandwidth, link.bandwidth_mbps)
                path_reliability *= link.reliability
        
        return total_latency, min_bandwidth, path_reliability
    
    def _calculate_distance(self, pos1: UAVPosition, pos2: UAVPosition) -> float:
        """計算兩點距離(米)"""
        lat_diff = (pos2.latitude - pos1.latitude) * 111000
        lon_diff = (pos2.longitude - pos1.longitude) * 111000
        alt_diff = pos2.altitude - pos1.altitude
        
        return np.sqrt(lat_diff**2 + lon_diff**2 + alt_diff**2)
    
    async def get_network_status(self) -> Dict:
        """獲取網路狀態"""
        active_nodes = sum(1 for node in self.network_topology.nodes.values() if node.is_active)
        active_links = sum(1 for link in self.network_topology.links.values() if link.is_active)
        
        # 計算網路指標
        avg_latency = np.mean([
            link.latency_ms for link in self.network_topology.links.values() 
            if link.is_active
        ]) if self.network_topology.links else 0
        
        total_bandwidth = sum([
            link.bandwidth_mbps for link in self.network_topology.links.values() 
            if link.is_active
        ])
        
        network_reliability = np.mean([
            link.reliability for link in self.network_topology.links.values() 
            if link.is_active
        ]) if self.network_topology.links else 0
        
        return {
            "topology_id": self.network_topology.topology_id,
            "topology_type": self.network_topology.topology_type.value,
            "status": {
                "total_nodes": len(self.network_topology.nodes),
                "active_nodes": active_nodes,
                "total_links": len(self.network_topology.links),
                "active_links": active_links,
                "routing_paths": len(self.network_topology.routing_paths)
            },
            "performance": {
                "average_latency_ms": round(avg_latency, 2),
                "total_bandwidth_mbps": round(total_bandwidth, 2),
                "network_reliability": round(network_reliability, 3),
                "optimization_enabled": self.optimization_task is not None
            },
            "last_optimization": self.network_topology.last_optimization.isoformat() if self.network_topology.last_optimization else None,
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "is_active": node.is_active,
                    "energy_level": node.energy_level,
                    "connection_count": node.connection_count
                }
                for node in self.network_topology.nodes.values()
            ]
        }