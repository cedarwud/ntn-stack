"""
統一 API 模型定義

定義統一 API 所需的所有資料模型，包括系統狀態、WebSocket 更新等
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SystemStatus(str, Enum):
    """系統狀態枚舉"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    MAINTENANCE = "maintenance"


class ConnectionQuality(str, Enum):
    """連接質量枚舉"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DISCONNECTED = "disconnected"


# ===== 系統狀態模型 =====


class SystemComponentStatus(BaseModel):
    """系統組件狀態"""

    name: str = Field(..., description="組件名稱")
    healthy: bool = Field(..., description="是否健康")
    status: str = Field(..., description="狀態描述")
    version: str = Field(..., description="版本號")
    last_health_check: datetime = Field(..., description="最後健康檢查時間")
    metrics: Optional[Dict[str, Union[float, int, str]]] = Field(
        None, description="性能指標"
    )
    error: Optional[str] = Field(None, description="錯誤信息")


class SystemStatusResponse(BaseModel):
    """系統狀態響應"""

    status: SystemStatus = Field(..., description="整體系統狀態")
    timestamp: datetime = Field(..., description="狀態時間戳")
    components: Dict[str, SystemComponentStatus] = Field(..., description="各組件狀態")
    summary: Dict[str, Any] = Field(..., description="狀態摘要")


class UnifiedHealthResponse(BaseModel):
    """統一健康檢查響應"""

    status: SystemStatus
    timestamp: datetime
    services: Dict[str, Any]
    uptime_seconds: float
    version: str


# ===== 服務發現模型 =====


class APIEndpointInfo(BaseModel):
    """API 端點信息"""

    path: str = Field(..., description="端點路徑")
    method: str = Field(..., description="HTTP 方法")
    description: str = Field(..., description="端點描述")
    service: str = Field(..., description="所屬服務")
    tags: Optional[List[str]] = Field(None, description="標籤")


class ServiceDiscoveryResponse(BaseModel):
    """服務發現響應"""

    timestamp: datetime = Field(..., description="發現時間")
    total_endpoints: int = Field(..., description="端點總數")
    endpoints: Dict[str, List[APIEndpointInfo]] = Field(..., description="端點分類")
    services: Dict[str, Dict[str, Any]] = Field(..., description="服務信息")


# ===== WebSocket 更新模型 =====


class NetworkStatusUpdate(BaseModel):
    """網絡狀態更新"""

    timestamp: datetime = Field(..., description="更新時間")
    connection_count: int = Field(..., description="連接數")
    throughput_mbps: float = Field(..., description="吞吐量 (Mbps)")
    latency_ms: float = Field(..., description="延遲 (ms)")
    packet_loss_rate: float = Field(..., description="丟包率")
    alerts: List[str] = Field(..., description="告警信息")


class SatelliteInfo(BaseModel):
    """衛星信息"""

    id: int = Field(..., description="衛星 ID")
    name: str = Field(..., description="衛星名稱")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: float = Field(..., description="高度 (km)")
    velocity: List[float] = Field(..., description="速度向量 [x, y, z]")


class SatellitePositionUpdate(BaseModel):
    """衛星位置更新"""

    timestamp: datetime = Field(..., description="更新時間")
    satellites: List[SatelliteInfo] = Field(..., description="衛星列表")


class UAVInfo(BaseModel):
    """UAV 信息"""

    id: str = Field(..., description="UAV ID")
    position: List[float] = Field(..., description="位置 [lon, lat, alt]")
    velocity: List[float] = Field(..., description="速度 [x, y, z]")
    signal_strength: float = Field(..., description="信號強度 (dBm)")
    connection_quality: ConnectionQuality = Field(..., description="連接質量")


class UAVTelemetryUpdate(BaseModel):
    """UAV 遙測更新"""

    timestamp: datetime = Field(..., description="更新時間")
    uavs: List[UAVInfo] = Field(..., description="UAV 列表")


class ChannelHeatmapUpdate(BaseModel):
    """信道熱力圖更新"""

    timestamp: datetime = Field(..., description="更新時間")
    heatmap_data: Dict[str, List[List[float]]] = Field(..., description="熱力圖數據")
    grid_bounds: Dict[str, float] = Field(..., description="網格邊界")


# ===== 批量操作模型 =====


class BatchOperationRequest(BaseModel):
    """批量操作請求"""

    operation_type: str = Field(..., description="操作類型")
    targets: List[str] = Field(..., description="目標列表")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作參數")
    async_mode: bool = Field(default=False, description="是否異步執行")


class BatchOperationResponse(BaseModel):
    """批量操作響應"""

    operation_id: str = Field(..., description="操作 ID")
    total_targets: int = Field(..., description="目標總數")
    successful: int = Field(..., description="成功數量")
    failed: int = Field(..., description="失敗數量")
    results: List[Dict[str, Any]] = Field(..., description="詳細結果")
    started_at: datetime = Field(..., description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")


# ===== 認證和授權模型 =====


class UserRole(str, Enum):
    """用戶角色"""

    ADMIN = "admin"
    OPERATOR = "operator"
    OBSERVER = "observer"


class APITokenInfo(BaseModel):
    """API Token 信息"""

    token_id: str = Field(..., description="Token ID")
    user_id: str = Field(..., description="用戶 ID")
    role: UserRole = Field(..., description="用戶角色")
    permissions: List[str] = Field(..., description="權限列表")
    expires_at: datetime = Field(..., description="過期時間")
    created_at: datetime = Field(..., description="創建時間")


class AuthenticationRequest(BaseModel):
    """認證請求"""

    username: str = Field(..., description="用戶名")
    password: str = Field(..., description="密碼")
    remember_me: bool = Field(default=False, description="記住我")


class AuthenticationResponse(BaseModel):
    """認證響應"""

    access_token: str = Field(..., description="訪問令牌")
    token_type: str = Field(default="bearer", description="令牌類型")
    expires_in: int = Field(..., description="過期時間（秒）")
    user_info: Dict[str, Any] = Field(..., description="用戶信息")


# ===== 指標和監控模型 =====


class PerformanceMetrics(BaseModel):
    """性能指標"""

    timestamp: datetime = Field(..., description="指標時間")
    cpu_usage_percent: float = Field(..., description="CPU 使用率")
    memory_usage_mb: float = Field(..., description="內存使用量 (MB)")
    disk_usage_percent: float = Field(..., description="磁盤使用率")
    network_io_mbps: Dict[str, float] = Field(..., description="網絡 I/O (Mbps)")
    active_connections: int = Field(..., description="活躍連接數")
    request_rate_per_second: float = Field(..., description="請求速率 (/秒)")
    error_rate_percent: float = Field(..., description="錯誤率")


class AlertInfo(BaseModel):
    """告警信息"""

    alert_id: str = Field(..., description="告警 ID")
    severity: str = Field(..., description="嚴重程度")
    message: str = Field(..., description="告警消息")
    component: str = Field(..., description="相關組件")
    timestamp: datetime = Field(..., description="告警時間")
    acknowledged: bool = Field(default=False, description="是否已確認")


class SystemMetricsResponse(BaseModel):
    """系統指標響應"""

    timestamp: datetime = Field(..., description="採集時間")
    metrics: PerformanceMetrics = Field(..., description="性能指標")
    alerts: List[AlertInfo] = Field(..., description="當前告警")
    health_score: float = Field(..., description="健康評分 (0-100)")


# ===== 配置管理模型 =====


class ConfigurationItem(BaseModel):
    """配置項"""

    key: str = Field(..., description="配置鍵")
    value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    category: str = Field(..., description="配置分類")
    requires_restart: bool = Field(default=False, description="是否需要重啟")


class ConfigurationUpdateRequest(BaseModel):
    """配置更新請求"""

    configurations: List[ConfigurationItem] = Field(..., description="配置項列表")
    apply_immediately: bool = Field(default=True, description="是否立即應用")
    backup_current: bool = Field(default=True, description="是否備份當前配置")


class ConfigurationResponse(BaseModel):
    """配置響應"""

    timestamp: datetime = Field(..., description="響應時間")
    configurations: List[ConfigurationItem] = Field(..., description="配置項")
    total_count: int = Field(..., description="總配置數")
    last_modified: datetime = Field(..., description="最後修改時間")


# ===== 部署和版本模型 =====


class DeploymentInfo(BaseModel):
    """部署信息"""

    version: str = Field(..., description="版本號")
    build_time: datetime = Field(..., description="構建時間")
    commit_hash: str = Field(..., description="Git 提交哈希")
    environment: str = Field(..., description="環境名稱")
    deployed_at: datetime = Field(..., description="部署時間")
    deployed_by: str = Field(..., description="部署者")


class ServiceInfo(BaseModel):
    """服務信息"""

    name: str = Field(..., description="服務名稱")
    version: str = Field(..., description="服務版本")
    status: str = Field(..., description="服務狀態")
    url: str = Field(..., description="服務 URL")
    health_endpoint: str = Field(..., description="健康檢查端點")
    documentation: str = Field(..., description="文檔 URL")
    deployment: DeploymentInfo = Field(..., description="部署信息")


class SystemInfoResponse(BaseModel):
    """系統信息響應"""

    system_name: str = Field(default="NTN Stack", description="系統名稱")
    version: str = Field(..., description="系統版本")
    services: List[ServiceInfo] = Field(..., description="服務列表")
    deployment: DeploymentInfo = Field(..., description="系統部署信息")
    capabilities: List[str] = Field(..., description="系統能力")
    endpoints_summary: Dict[str, int] = Field(..., description="端點摘要")
