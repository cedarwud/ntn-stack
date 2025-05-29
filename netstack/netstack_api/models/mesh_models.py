"""
Mesh 網絡數據模型
支援 Tier-1 Mesh 網絡與 5G 核心網橋接功能
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MeshNodeType(str, Enum):
    """Mesh 節點類型"""

    UAV_RELAY = "uav_relay"  # UAV 中繼節點
    GROUND_STATION = "ground_station"  # 地面基站
    MOBILE_UNIT = "mobile_unit"  # 移動單元
    FIXED_UNIT = "fixed_unit"  # 固定單元


class MeshNodeStatus(str, Enum):
    """Mesh 節點狀態"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    MAINTENANCE = "maintenance"


class MeshProtocolType(str, Enum):
    """Mesh 協議類型"""

    AODV = "aodv"  # Ad-hoc On-Demand Distance Vector
    OLSR = "olsr"  # Optimized Link State Routing
    BATMAN = "batman"  # Better Approach To Mobile Adhoc Networking
    CUSTOM = "custom"  # 自定義協議


class QoSClass(str, Enum):
    """QoS 服務類別"""

    EMERGENCY = "emergency"  # 緊急通信
    COMMAND = "command"  # 指揮控制
    VIDEO = "video"  # 視頻傳輸
    DATA = "data"  # 一般數據
    BACKGROUND = "background"  # 背景傳輸


class BridgeStatus(str, Enum):
    """橋接狀態"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SWITCHING = "switching"
    FAILED = "failed"
    STANDBY = "standby"


class MeshPosition(BaseModel):
    """Mesh 節點位置"""

    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: float = Field(default=0.0, description="海拔高度(米)")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="位置更新時間"
    )


class MeshLinkQuality(BaseModel):
    """Mesh 鏈路質量指標"""

    rssi: float = Field(..., description="接收信號強度指示 (dBm)")
    snr: float = Field(..., description="信噪比 (dB)")
    packet_loss_rate: float = Field(default=0.0, description="封包丟失率 (0-1)")
    latency_ms: float = Field(default=0.0, description="延遲 (毫秒)")
    bandwidth_mbps: float = Field(default=0.0, description="可用頻寬 (Mbps)")
    jitter_ms: float = Field(default=0.0, description="抖動 (毫秒)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="測量時間")


class MeshRouteEntry(BaseModel):
    """Mesh 路由表項"""

    destination: str = Field(..., description="目標節點 ID")
    next_hop: str = Field(..., description="下一跳節點 ID")
    hop_count: int = Field(..., description="跳數")
    metric: float = Field(..., description="路由指標")
    valid_time: datetime = Field(..., description="路由有效時間")
    route_flags: List[str] = Field(default_factory=list, description="路由標誌")


class MeshNeighbor(BaseModel):
    """Mesh 鄰居節點"""

    node_id: str = Field(..., description="鄰居節點 ID")
    node_type: MeshNodeType = Field(..., description="節點類型")
    link_quality: MeshLinkQuality = Field(..., description="鏈路質量")
    last_seen: datetime = Field(
        default_factory=datetime.utcnow, description="最後一次見到"
    )
    is_gateway: bool = Field(default=False, description="是否為網關節點")


class MeshNode(BaseModel):
    """Mesh 網絡節點"""

    node_id: str = Field(..., description="節點唯一標識")
    name: str = Field(..., description="節點名稱")
    node_type: MeshNodeType = Field(..., description="節點類型")
    status: MeshNodeStatus = Field(
        default=MeshNodeStatus.INACTIVE, description="節點狀態"
    )
    position: Optional[MeshPosition] = Field(None, description="節點位置")

    # 網絡配置
    ip_address: str = Field(..., description="IP 地址")
    mac_address: str = Field(..., description="MAC 地址")
    frequency_mhz: float = Field(default=900.0, description="工作頻率 (MHz)")
    power_dbm: float = Field(default=20.0, description="發射功率 (dBm)")

    # Mesh 配置
    protocol_type: MeshProtocolType = Field(
        default=MeshProtocolType.AODV, description="路由協議"
    )
    max_hop_count: int = Field(default=5, description="最大跳數")
    beacon_interval_ms: int = Field(default=1000, description="信標間隔 (毫秒)")

    # 鄰居和路由信息
    neighbors: List[MeshNeighbor] = Field(
        default_factory=list, description="鄰居節點列表"
    )
    routing_table: List[MeshRouteEntry] = Field(
        default_factory=list, description="路由表"
    )

    # 性能指標
    traffic_stats: Dict[str, Any] = Field(default_factory=dict, description="流量統計")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="創建時間"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="更新時間"
    )


class Bridge5GMeshGateway(BaseModel):
    """5G-Mesh 橋接網關"""

    gateway_id: str = Field(..., description="網關唯一標識")
    name: str = Field(..., description="網關名稱")
    status: BridgeStatus = Field(
        default=BridgeStatus.DISCONNECTED, description="橋接狀態"
    )

    # 5G 側配置
    upf_ip: str = Field(..., description="UPF IP 地址")
    upf_port: int = Field(default=2152, description="UPF GTP-U 端口")
    slice_info: Dict[str, Any] = Field(
        default_factory=dict, description="支援的 Slice 信息"
    )

    # Mesh 側配置
    mesh_node_id: str = Field(..., description="關聯的 Mesh 節點 ID")
    mesh_interface: str = Field(..., description="Mesh 網絡介面")

    # 橋接配置
    packet_forwarding_enabled: bool = Field(default=True, description="封包轉發啟用")
    qos_mapping: Dict[QoSClass, Dict[str, Any]] = Field(
        default_factory=dict, description="QoS 映射規則"
    )
    security_enabled: bool = Field(default=True, description="安全機制啟用")

    # 性能監控
    throughput_mbps: float = Field(default=0.0, description="吞吐量 (Mbps)")
    latency_ms: float = Field(default=0.0, description="延遲 (毫秒)")
    packet_loss_rate: float = Field(default=0.0, description="封包丟失率")

    # 狀態時間戳
    last_heartbeat: datetime = Field(
        default_factory=datetime.utcnow, description="最後心跳時間"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="創建時間"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="更新時間"
    )


class MeshTrafficFlow(BaseModel):
    """Mesh 流量流"""

    flow_id: str = Field(..., description="流量流 ID")
    source_node: str = Field(..., description="源節點 ID")
    destination_node: str = Field(..., description="目標節點 ID")
    qos_class: QoSClass = Field(..., description="QoS 類別")

    # 流量特徵
    packet_size_bytes: int = Field(default=1500, description="封包大小 (位元組)")
    flow_rate_pps: float = Field(default=100.0, description="流量速率 (packets/sec)")
    priority: int = Field(default=0, description="優先級 (0-7)")

    # 路徑信息
    current_path: List[str] = Field(default_factory=list, description="當前路徑")
    backup_paths: List[List[str]] = Field(default_factory=list, description="備用路徑")

    # 性能指標
    end_to_end_latency_ms: float = Field(default=0.0, description="端到端延遲")
    delivery_ratio: float = Field(default=1.0, description="投遞率")

    # 時間戳
    start_time: datetime = Field(
        default_factory=datetime.utcnow, description="流量開始時間"
    )
    last_update: datetime = Field(
        default_factory=datetime.utcnow, description="最後更新時間"
    )


class MeshNetworkTopology(BaseModel):
    """Mesh 網絡拓撲"""

    topology_id: str = Field(..., description="拓撲 ID")
    network_name: str = Field(..., description="網絡名稱")
    nodes: List[MeshNode] = Field(default_factory=list, description="節點列表")
    gateways: List[Bridge5GMeshGateway] = Field(
        default_factory=list, description="橋接網關列表"
    )
    active_flows: List[MeshTrafficFlow] = Field(
        default_factory=list, description="活躍流量流"
    )

    # 網絡指標
    connectivity_matrix: Dict[str, Dict[str, bool]] = Field(
        default_factory=dict, description="連通性矩陣"
    )
    network_diameter: int = Field(default=0, description="網絡直徑")
    average_path_length: float = Field(default=0.0, description="平均路徑長度")

    # 時間戳
    last_topology_update: datetime = Field(
        default_factory=datetime.utcnow, description="最後拓撲更新時間"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="創建時間"
    )


# API 請求和響應模型


class MeshNodeCreateRequest(BaseModel):
    """創建 Mesh 節點請求"""

    name: str = Field(..., description="節點名稱")
    node_type: MeshNodeType = Field(..., description="節點類型")
    ip_address: str = Field(..., description="IP 地址")
    mac_address: str = Field(..., description="MAC 地址")
    position: Optional[MeshPosition] = Field(None, description="節點位置")
    frequency_mhz: float = Field(default=900.0, description="工作頻率")
    power_dbm: float = Field(default=20.0, description="發射功率")
    protocol_type: MeshProtocolType = Field(
        default=MeshProtocolType.AODV, description="路由協議"
    )


class MeshNodeUpdateRequest(BaseModel):
    """更新 Mesh 節點請求"""

    name: Optional[str] = Field(None, description="節點名稱")
    status: Optional[MeshNodeStatus] = Field(None, description="節點狀態")
    position: Optional[MeshPosition] = Field(None, description="節點位置")
    power_dbm: Optional[float] = Field(None, description="發射功率")


class BridgeGatewayCreateRequest(BaseModel):
    """創建橋接網關請求"""

    name: str = Field(..., description="網關名稱")
    upf_ip: str = Field(..., description="UPF IP 地址")
    upf_port: int = Field(default=2152, description="UPF GTP-U 端口")
    mesh_node_id: str = Field(..., description="關聯的 Mesh 節點 ID")
    mesh_interface: str = Field(..., description="Mesh 網絡介面")
    slice_info: Optional[Dict[str, Any]] = Field(None, description="支援的 Slice 信息")


class BridgeGatewayUpdateRequest(BaseModel):
    """更新橋接網關請求"""

    name: Optional[str] = Field(None, description="網關名稱")
    status: Optional[BridgeStatus] = Field(None, description="橋接狀態")
    packet_forwarding_enabled: Optional[bool] = Field(None, description="封包轉發啟用")
    security_enabled: Optional[bool] = Field(None, description="安全機制啟用")


class MeshRoutingUpdateRequest(BaseModel):
    """Mesh 路由更新請求"""

    node_id: str = Field(..., description="節點 ID")
    routing_table: List[MeshRouteEntry] = Field(..., description="新的路由表")
    force_update: bool = Field(default=False, description="強制更新")


class NetworkTopologyResponse(BaseModel):
    """網絡拓撲響應"""

    topology: MeshNetworkTopology = Field(..., description="網絡拓撲")
    health_score: float = Field(..., description="網絡健康分數 (0-1)")
    connectivity_ratio: float = Field(..., description="連通性比率")
    average_link_quality: float = Field(..., description="平均鏈路質量")


class MeshPerformanceMetrics(BaseModel):
    """Mesh 網絡性能指標"""

    node_id: str = Field(..., description="節點 ID")

    # 流量指標
    total_packets_sent: int = Field(default=0, description="總發送封包數")
    total_packets_received: int = Field(default=0, description="總接收封包數")
    total_packets_forwarded: int = Field(default=0, description="總轉發封包數")
    total_packets_dropped: int = Field(default=0, description="總丟棄封包數")

    # 品質指標
    average_rssi_dbm: float = Field(default=0.0, description="平均 RSSI")
    average_snr_db: float = Field(default=0.0, description="平均 SNR")
    average_latency_ms: float = Field(default=0.0, description="平均延遲")
    packet_loss_ratio: float = Field(default=0.0, description="封包丟失率")

    # 能耗指標
    power_consumption_w: float = Field(default=0.0, description="功耗 (瓦特)")
    battery_level_percent: float = Field(default=100.0, description="電池電量百分比")

    # 時間範圍
    measurement_period_start: datetime = Field(..., description="測量期間開始時間")
    measurement_period_end: datetime = Field(..., description="測量期間結束時間")


class BridgePerformanceMetrics(BaseModel):
    """橋接性能指標"""

    gateway_id: str = Field(..., description="網關 ID")

    # 橋接流量指標
    packets_5g_to_mesh: int = Field(default=0, description="5G 到 Mesh 封包數")
    packets_mesh_to_5g: int = Field(default=0, description="Mesh 到 5G 封包數")
    bytes_5g_to_mesh: int = Field(default=0, description="5G 到 Mesh 位元組數")
    bytes_mesh_to_5g: int = Field(default=0, description="Mesh 到 5G 位元組數")

    # 橋接延遲指標
    bridge_latency_ms: float = Field(default=0.0, description="橋接延遲")
    conversion_time_us: float = Field(default=0.0, description="協議轉換時間 (微秒)")

    # 錯誤指標
    conversion_errors: int = Field(default=0, description="轉換錯誤數")
    bridge_failures: int = Field(default=0, description="橋接失敗數")

    # 時間範圍
    measurement_period_start: datetime = Field(..., description="測量期間開始時間")
    measurement_period_end: datetime = Field(..., description="測量期間結束時間")
