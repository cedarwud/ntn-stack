"""
UAV UE 模擬相關的數據模型

包含軌跡管理、UAV 狀態、UE 配置等模型定義
"""

from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class UAVFlightStatus(str, Enum):
    """UAV 飛行狀態"""

    IDLE = "idle"
    FLYING = "flying"
    HOVERING = "hovering"
    LANDED = "landed"
    EMERGENCY = "emergency"


class UEConnectionStatus(str, Enum):
    """UE 連接狀態"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SWITCHING = "switching"
    ERROR = "error"


class TrajectoryPoint(BaseModel):
    """軌跡點模型"""

    timestamp: datetime = Field(..., description="時間戳")
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    altitude: float = Field(..., ge=0, le=50000, description="高度 (米)")
    speed: Optional[float] = Field(None, ge=0, description="速度 (m/s)")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="航向角 (度)")


class UAVTrajectory(BaseModel):
    """UAV 軌跡模型"""

    trajectory_id: str = Field(..., description="軌跡 ID")
    name: str = Field(..., description="軌跡名稱")
    description: Optional[str] = Field(None, description="軌跡描述")
    mission_type: str = Field(default="reconnaissance", description="任務類型")
    points: List[TrajectoryPoint] = Field(..., min_items=2, description="軌跡點列表")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="創建時間"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="更新時間"
    )

    @validator("points")
    def validate_trajectory_points(cls, v):
        if len(v) < 2:
            raise ValueError("軌跡至少需要 2 個點")

        # 檢查時間戳遞增
        timestamps = [point.timestamp for point in v]
        if timestamps != sorted(timestamps):
            raise ValueError("軌跡點時間戳必須按遞增順序排列")

        return v


class UAVPosition(BaseModel):
    """UAV 當前位置"""

    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    altitude: float = Field(..., ge=0, le=50000, description="高度 (米)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="位置時間戳"
    )
    speed: Optional[float] = Field(None, ge=0, description="速度 (m/s)")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="航向角 (度)")


class UAVUEConfig(BaseModel):
    """UAV 作為 UE 的配置"""

    imsi: str = Field(..., pattern=r"^\d{15}$", description="IMSI")
    key: str = Field(..., description="認證密鑰")
    opc: str = Field(..., description="OPC")
    plmn: str = Field(default="00101", description="PLMN")
    apn: str = Field(default="internet", description="APN")
    slice_nssai: Dict[str, Any] = Field(
        default={"sst": 1, "sd": "000001"},
        description="Network Slice Selection Assistance Information",
    )
    gnb_ip: str = Field(default="127.0.0.1", description="gNodeB IP 地址")
    gnb_port: int = Field(default=38412, description="gNodeB 端口")
    power_dbm: float = Field(default=20.0, description="發射功率 (dBm)")
    frequency_mhz: float = Field(default=2150.0, description="頻率 (MHz)")
    bandwidth_mhz: float = Field(default=20.0, description="頻寬 (MHz)")


class UAVConnectionQualityMetrics(BaseModel):
    """UAV 連接質量綜合指標"""

    # 核心信號質量指標
    sinr_db: Optional[float] = Field(None, description="信噪干擾比 (dB)")
    rsrp_dbm: Optional[float] = Field(None, description="RSRP (dBm)")
    rsrq_db: Optional[float] = Field(None, description="RSRQ (dB)")
    cqi: Optional[int] = Field(
        None, ge=0, le=15, description="Channel Quality Indicator"
    )

    # 性能指標
    throughput_mbps: Optional[float] = Field(
        None, ge=0, description="實際吞吐量 (Mbps)"
    )
    latency_ms: Optional[float] = Field(None, ge=0, description="端到端延遲 (ms)")
    jitter_ms: Optional[float] = Field(None, ge=0, description="延遲抖動 (ms)")
    packet_loss_rate: Optional[float] = Field(
        None, ge=0, le=1, description="封包遺失率"
    )

    # 連接穩定性指標
    connection_uptime_percent: Optional[float] = Field(
        None, ge=0, le=100, description="連接正常時間百分比"
    )
    handover_success_rate: Optional[float] = Field(
        None, ge=0, le=1, description="換手成功率"
    )
    reconnection_count: Optional[int] = Field(None, ge=0, description="重連次數")
    signal_stability_score: Optional[float] = Field(
        None, ge=0, le=1, description="信號穩定性評分"
    )

    # NTN 特有指標
    doppler_shift_hz: Optional[float] = Field(None, description="多普勒頻移 (Hz)")
    propagation_delay_ms: Optional[float] = Field(
        None, ge=0, description="傳播延遲 (ms)"
    )
    link_budget_margin_db: Optional[float] = Field(None, description="鏈路餘裕 (dB)")
    beam_alignment_quality: Optional[float] = Field(
        None, ge=0, le=1, description="波束對準品質"
    )

    # 測量時間和有效性
    measurement_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="測量時間戳"
    )
    measurement_window_seconds: Optional[int] = Field(
        None, ge=1, description="測量窗口時間 (秒)"
    )
    data_freshness_score: Optional[float] = Field(
        None, ge=0, le=1, description="數據新鮮度評分"
    )


class ConnectionQualityAssessment(BaseModel):
    """連接質量評估結果"""

    # 綜合評估分數
    overall_quality_score: float = Field(
        ..., ge=0, le=100, description="綜合質量評分 (0-100)"
    )
    quality_grade: str = Field(..., description="質量等級 (優秀/良好/一般/差)")

    # 各維度評分
    signal_quality_score: float = Field(..., ge=0, le=100, description="信號質量評分")
    performance_score: float = Field(..., ge=0, le=100, description="性能評分")
    stability_score: float = Field(..., ge=0, le=100, description="穩定性評分")
    ntn_adaptation_score: float = Field(..., ge=0, le=100, description="NTN 適配評分")

    # 問題識別
    identified_issues: List[str] = Field(
        default_factory=list, description="發現的問題列表"
    )
    recommendations: List[str] = Field(default_factory=list, description="改善建議")

    # 預測分析
    quality_trend: Optional[str] = Field(
        None, description="質量趨勢 (improving/stable/degrading)"
    )
    predicted_issues: List[str] = Field(
        default_factory=list, description="預測可能出現的問題"
    )

    # 評估元數據
    assessment_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="評估時間"
    )
    confidence_level: float = Field(..., ge=0, le=1, description="評估信賴水準")
    data_completeness: float = Field(..., ge=0, le=1, description="數據完整性")


class ConnectionQualityHistoricalData(BaseModel):
    """連接質量歷史數據"""

    uav_id: str = Field(..., description="UAV ID")
    start_time: datetime = Field(..., description="數據開始時間")
    end_time: datetime = Field(..., description="數據結束時間")
    sample_count: int = Field(..., ge=0, description="樣本數量")

    # 統計摘要
    metrics_summary: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="指標統計摘要 (mean, min, max, std)"
    )

    # 質量評估歷史
    quality_assessments: List[ConnectionQualityAssessment] = Field(
        default_factory=list, description="質量評估歷史記錄"
    )

    # 異常事件
    anomaly_events: List[Dict[str, Any]] = Field(
        default_factory=list, description="異常事件記錄"
    )


class ConnectionQualityThresholds(BaseModel):
    """連接質量閾值配置"""

    # 信號質量閾值
    sinr_excellent_db: float = Field(default=15.0, description="SINR 優秀閾值")
    sinr_good_db: float = Field(default=10.0, description="SINR 良好閾值")
    sinr_poor_db: float = Field(default=0.0, description="SINR 差劣閾值")

    rsrp_excellent_dbm: float = Field(default=-70.0, description="RSRP 優秀閾值")
    rsrp_good_dbm: float = Field(default=-85.0, description="RSRP 良好閾值")
    rsrp_poor_dbm: float = Field(default=-110.0, description="RSRP 差劣閾值")

    # 性能閾值
    throughput_excellent_mbps: float = Field(default=50.0, description="吞吐量優秀閾值")
    throughput_good_mbps: float = Field(default=20.0, description="吞吐量良好閾值")
    throughput_poor_mbps: float = Field(default=5.0, description="吞吐量差劣閾值")

    latency_excellent_ms: float = Field(default=50.0, description="延遲優秀閾值")
    latency_good_ms: float = Field(default=100.0, description="延遲良好閾值")
    latency_poor_ms: float = Field(default=250.0, description="延遲差劣閾值")

    # 穩定性閾值
    packet_loss_excellent: float = Field(default=0.001, description="丟包率優秀閾值")
    packet_loss_good: float = Field(default=0.01, description="丟包率良好閾值")
    packet_loss_poor: float = Field(default=0.05, description="丟包率差劣閾值")

    # 權重配置
    signal_weight: float = Field(default=0.3, description="信號質量權重")
    performance_weight: float = Field(default=0.4, description="性能權重")
    stability_weight: float = Field(default=0.3, description="穩定性權重")


class UAVSignalQuality(BaseModel):
    """UAV 信號質量（擴展版）"""

    rsrp_dbm: Optional[float] = Field(None, description="RSRP (dBm)")
    rsrq_db: Optional[float] = Field(None, description="RSRQ (dB)")
    sinr_db: Optional[float] = Field(None, description="SINR (dB)")
    cqi: Optional[int] = Field(
        None, ge=0, le=15, description="Channel Quality Indicator"
    )
    throughput_mbps: Optional[float] = Field(None, ge=0, description="吞吐量 (Mbps)")
    latency_ms: Optional[float] = Field(None, ge=0, description="延遲 (ms)")
    packet_loss_rate: Optional[float] = Field(
        None, ge=0, le=1, description="封包遺失率"
    )

    # 新增的擴展指標
    jitter_ms: Optional[float] = Field(None, ge=0, description="延遲抖動 (ms)")
    link_budget_margin_db: Optional[float] = Field(None, description="鏈路餘裕 (dB)")
    doppler_shift_hz: Optional[float] = Field(None, description="多普勒頻移 (Hz)")
    beam_alignment_score: Optional[float] = Field(
        None, ge=0, le=1, description="波束對準評分"
    )
    interference_level_db: Optional[float] = Field(None, description="干擾水平 (dB)")

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="測量時間戳"
    )
    measurement_confidence: Optional[float] = Field(
        None, ge=0, le=1, description="測量信賴水準"
    )


class UAVStatus(BaseModel):
    """UAV 整體狀態"""

    uav_id: str = Field(..., description="UAV ID")
    name: str = Field(..., description="UAV 名稱")
    flight_status: UAVFlightStatus = Field(
        default=UAVFlightStatus.IDLE, description="飛行狀態"
    )
    ue_connection_status: UEConnectionStatus = Field(
        default=UEConnectionStatus.DISCONNECTED, description="UE 連接狀態"
    )
    current_position: Optional[UAVPosition] = Field(None, description="當前位置")
    target_position: Optional[UAVPosition] = Field(None, description="目標位置")
    signal_quality: Optional[UAVSignalQuality] = Field(None, description="信號質量")
    ue_config: Optional[UAVUEConfig] = Field(None, description="UE 配置")
    trajectory_id: Optional[str] = Field(None, description="當前軌跡 ID")
    mission_start_time: Optional[datetime] = Field(None, description="任務開始時間")
    last_update: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="最後更新時間"
    )


# 請求模型
class TrajectoryCreateRequest(BaseModel):
    """創建軌跡請求"""

    name: str = Field(..., description="軌跡名稱")
    description: Optional[str] = Field(None, description="軌跡描述")
    mission_type: str = Field(default="reconnaissance", description="任務類型")
    points: List[TrajectoryPoint] = Field(..., min_items=2, description="軌跡點列表")


class TrajectoryUpdateRequest(BaseModel):
    """更新軌跡請求"""

    name: Optional[str] = Field(None, description="軌跡名稱")
    description: Optional[str] = Field(None, description="軌跡描述")
    mission_type: Optional[str] = Field(None, description="任務類型")
    points: Optional[List[TrajectoryPoint]] = Field(None, description="軌跡點列表")


class UAVCreateRequest(BaseModel):
    """創建 UAV 請求"""

    name: str = Field(..., description="UAV 名稱")
    ue_config: UAVUEConfig = Field(..., description="UE 配置")
    initial_position: Optional[UAVPosition] = Field(None, description="初始位置")


class UAVMissionStartRequest(BaseModel):
    """開始 UAV 任務請求"""

    trajectory_id: str = Field(..., description="軌跡 ID")
    start_time: Optional[datetime] = Field(
        None, description="開始時間，留空表示立即開始"
    )
    speed_factor: float = Field(default=1.0, ge=0.1, le=10.0, description="速度倍數")


class UAVPositionUpdateRequest(BaseModel):
    """UAV 位置更新請求"""

    position: UAVPosition = Field(..., description="新位置")
    signal_quality: Optional[UAVSignalQuality] = Field(None, description="信號質量")


# 響應模型
class TrajectoryResponse(BaseModel):
    """軌跡響應"""

    trajectory_id: str
    name: str
    description: Optional[str]
    mission_type: str
    points: List[TrajectoryPoint]
    created_at: datetime
    updated_at: datetime
    total_distance_km: Optional[float] = Field(None, description="總距離 (公里)")
    estimated_duration_minutes: Optional[float] = Field(
        None, description="預估飛行時間 (分鐘)"
    )


class UAVStatusResponse(BaseModel):
    """UAV 狀態響應"""

    uav_id: str
    name: str
    flight_status: UAVFlightStatus
    ue_connection_status: UEConnectionStatus
    current_position: Optional[UAVPosition]
    target_position: Optional[UAVPosition]
    signal_quality: Optional[UAVSignalQuality]
    ue_config: Optional[UAVUEConfig]
    trajectory_id: Optional[str]
    mission_start_time: Optional[datetime]
    mission_progress_percent: Optional[float] = Field(
        None, description="任務進度百分比"
    )
    last_update: datetime


class UAVListResponse(BaseModel):
    """UAV 列表響應"""

    uavs: List[UAVStatusResponse]
    total: int


class TrajectoryListResponse(BaseModel):
    """軌跡列表響應"""

    trajectories: List[TrajectoryResponse]
    total: int
