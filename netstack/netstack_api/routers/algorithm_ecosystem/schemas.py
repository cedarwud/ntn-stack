"""
API 模型定義 - 從 algorithm_ecosystem_router.py 中提取的 Pydantic 模型
集中管理所有請求/響應模型，便於API結構修改
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class GeoCoordinateModel(BaseModel):
    """地理坐標模型"""
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: float = Field(default=0.0, description="海拔高度 (米)")


class SignalMetricsModel(BaseModel):
    """信號質量指標模型"""
    rsrp: float = Field(..., description="參考信號接收功率")
    rsrq: float = Field(..., description="參考信號接收質量")
    sinr: float = Field(..., description="信噪干擾比")
    throughput: float = Field(default=0.0, description="吞吐量")
    latency: float = Field(default=0.0, description="延遲")


class SatelliteInfoModel(BaseModel):
    """衛星信息模型"""
    satellite_id: str = Field(..., description="衛星ID")
    position: GeoCoordinateModel = Field(..., description="衛星位置")
    velocity: Optional[GeoCoordinateModel] = Field(None, description="衛星速度")
    signal_metrics: Optional[SignalMetricsModel] = Field(None, description="信號指標")
    load_factor: float = Field(default=0.0, description="負載因子")


class HandoverPredictionRequest(BaseModel):
    """換手預測請求"""
    ue_id: str = Field(..., description="用戶設備ID")
    current_satellite: Optional[str] = Field(None, description="當前衛星ID")
    ue_location: GeoCoordinateModel = Field(..., description="UE位置")
    ue_velocity: Optional[GeoCoordinateModel] = Field(None, description="UE速度")
    current_signal_metrics: Optional[SignalMetricsModel] = Field(None, description="當前信號指標")
    candidate_satellites: List[SatelliteInfoModel] = Field(..., description="候選衛星列表")
    network_state: Dict[str, Any] = Field(default_factory=dict, description="網路狀態")
    scenario_info: Optional[Dict[str, Any]] = Field(None, description="場景信息")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="天氣條件")
    traffic_load: Optional[Dict[str, Any]] = Field(None, description="流量負載")
    algorithm_name: Optional[str] = Field(None, description="指定算法名稱")
    use_cache: Optional[bool] = Field(None, description="是否使用緩存")


class HandoverDecisionResponse(BaseModel):
    """換手決策響應"""
    target_satellite: Optional[str] = Field(None, description="目標衛星ID")
    handover_decision: int = Field(..., description="換手決策類型")
    confidence: float = Field(..., description="決策信心度")
    timing: Optional[datetime] = Field(None, description="建議執行時間")
    decision_reason: str = Field(..., description="決策原因")
    algorithm_name: str = Field(..., description="執行算法名稱")
    decision_time: float = Field(..., description="決策耗時 (毫秒)")
    metadata: Dict[str, Any] = Field(..., description="額外元數據")


class AlgorithmInfoResponse(BaseModel):
    """算法信息響應"""
    name: str = Field(..., description="算法名稱")
    version: str = Field(..., description="算法版本")
    algorithm_type: str = Field(..., description="算法類型")
    enabled: bool = Field(..., description="是否啟用")
    description: Optional[str] = Field(None, description="算法描述")
    priority: int = Field(default=0, description="優先級")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="算法配置")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="性能指標")


class AlgorithmRegistrationRequest(BaseModel):
    """算法註冊請求"""
    name: str = Field(..., description="算法名稱")
    algorithm_type: str = Field(..., description="算法類型")
    version: str = Field(default="1.0.0", description="算法版本")
    description: Optional[str] = Field(None, description="算法描述")
    priority: int = Field(default=0, description="優先級")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="算法配置")
    enable_immediately: bool = Field(default=True, description="是否立即啟用")


class OrchestratorConfigRequest(BaseModel):
    """協調器配置請求"""
    mode: str = Field(..., description="協調器模式")
    decision_strategy: str = Field(..., description="決策策略")
    default_algorithm: Optional[str] = Field(None, description="默認算法")
    enable_caching: bool = Field(default=True, description="是否啟用緩存")
    cache_ttl_seconds: int = Field(default=60, description="緩存TTL")
    max_concurrent_requests: int = Field(default=100, description="最大併發請求數")
    ab_test_config: Optional[Dict[str, Any]] = Field(None, description="A/B測試配置")
    ensemble_config: Optional[Dict[str, Any]] = Field(None, description="集成配置")


class EnvironmentCreateRequest(BaseModel):
    """環境創建請求"""
    environment_type: str = Field(..., description="環境類型")
    config: Dict[str, Any] = Field(default_factory=dict, description="環境配置")
    enable_gymnasium: bool = Field(default=False, description="是否啟用Gymnasium")


class EnvironmentActionRequest(BaseModel):
    """環境動作請求"""
    action: Dict[str, Any] = Field(..., description="動作數據")
    environment_id: Optional[str] = Field(None, description="環境ID")


class TrainingStartRequest(BaseModel):
    """訓練開始請求"""
    algorithm_name: str = Field(..., description="算法名稱")
    environment_type: str = Field(..., description="環境類型")
    training_config: Dict[str, Any] = Field(default_factory=dict, description="訓練配置")
    max_episodes: int = Field(default=1000, description="最大訓練回合")
    target_reward: Optional[float] = Field(None, description="目標獎勵")


class ABTestConfigRequest(BaseModel):
    """A/B測試配置請求"""
    test_id: str = Field(..., description="測試ID")
    traffic_split: Dict[str, float] = Field(..., description="流量分配")
    duration_hours: Optional[int] = Field(None, description="測試持續時間（小時）")
    success_criteria: Optional[Dict[str, Any]] = Field(None, description="成功標準")


class MetricsExportRequest(BaseModel):
    """指標導出請求"""
    format: str = Field(default="json", description="導出格式")
    time_range: Optional[Dict[str, datetime]] = Field(None, description="時間範圍")
    algorithms: Optional[List[str]] = Field(None, description="指定算法")
    include_raw_data: bool = Field(default=False, description="是否包含原始數據")


# === 響應模型 ===

class HealthCheckResponse(BaseModel):
    """健康檢查響應"""
    status: str = Field(..., description="服務狀態")
    timestamp: datetime = Field(..., description="檢查時間")
    services: Dict[str, Dict[str, Any]] = Field(..., description="各服務狀態")


class StatsResponse(BaseModel):
    """統計信息響應"""
    component: str = Field(..., description="組件名稱")
    timestamp: datetime = Field(..., description="統計時間")
    data: Dict[str, Any] = Field(..., description="統計數據")


class TrainingStatusResponse(BaseModel):
    """訓練狀態響應"""
    algorithm_name: str = Field(..., description="算法名稱")
    status: str = Field(..., description="訓練狀態")
    current_episode: int = Field(..., description="當前回合")
    total_episodes: int = Field(..., description="總回合數")
    current_reward: float = Field(..., description="當前獎勵")
    best_reward: float = Field(..., description="最佳獎勵")
    training_time: float = Field(..., description="訓練時間")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="訓練指標")


class EnvironmentStatusResponse(BaseModel):
    """環境狀態響應"""
    environment_id: str = Field(..., description="環境ID")
    environment_type: str = Field(..., description="環境類型")
    status: str = Field(..., description="環境狀態")
    current_step: int = Field(..., description="當前步數")
    total_reward: float = Field(..., description="總獎勵")
    observation: Optional[Dict[str, Any]] = Field(None, description="當前觀測")
    info: Dict[str, Any] = Field(default_factory=dict, description="環境信息")


class OperationResponse(BaseModel):
    """操作響應"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作消息")
    data: Optional[Dict[str, Any]] = Field(None, description="返回數據")
    timestamp: datetime = Field(default_factory=datetime.now, description="操作時間")