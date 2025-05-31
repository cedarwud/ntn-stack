"""
Wireless Channel Domain Models
包含 Sionna 無線通道模型的實體定義
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np


class ChannelPathComponent(BaseModel):
    """通道路徑分量"""

    delay_ns: float = Field(..., description="路徑延遲（奈秒）")
    power_db: float = Field(..., description="路徑功率（dB）")
    azimuth_deg: float = Field(..., description="方位角（度）")
    elevation_deg: float = Field(..., description="仰角（度）")
    doppler_hz: float = Field(default=0.0, description="多普勒頻移（Hz）")


class SionnaChannelResponse(BaseModel):
    """Sionna 無線通道響應"""

    channel_id: str = Field(..., description="通道 ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # 發送端資訊
    tx_position: List[float] = Field(..., description="發送端位置 [x, y, z] (m)")
    tx_velocity: List[float] = Field(
        default=[0.0, 0.0, 0.0], description="發送端速度 [vx, vy, vz] (m/s)"
    )

    # 接收端資訊
    rx_position: List[float] = Field(..., description="接收端位置 [x, y, z] (m)")
    rx_velocity: List[float] = Field(
        default=[0.0, 0.0, 0.0], description="接收端速度 [vx, vy, vz] (m/s)"
    )

    # 通道特性
    frequency_hz: float = Field(..., description="中心頻率（Hz）")
    bandwidth_hz: float = Field(..., description="頻寬（Hz）")
    path_loss_db: float = Field(..., description="路徑損耗（dB）")
    shadowing_db: float = Field(default=0.0, description="陰影衰落（dB）")

    # 多路徑分量
    paths: List[ChannelPathComponent] = Field(default=[], description="多路徑分量")

    # 通道矩陣（複數形式，序列化為實數+虛數）
    channel_matrix_real: List[List[float]] = Field(
        default=[], description="通道矩陣實部"
    )
    channel_matrix_imag: List[List[float]] = Field(
        default=[], description="通道矩陣虛部"
    )

    # 統計特性
    rms_delay_spread_ns: float = Field(default=0.0, description="RMS 延遲擴散（ns）")
    coherence_bandwidth_hz: float = Field(default=0.0, description="相干頻寬（Hz）")
    coherence_time_ms: float = Field(default=0.0, description="相干時間（ms）")


class UERANSIMChannelParams(BaseModel):
    """UERANSIM 通道參數"""

    ue_id: str = Field(..., description="UE ID")
    gnb_id: str = Field(..., description="gNodeB ID")

    # 從 Sionna 轉換的參數
    sinr_db: float = Field(..., description="信噪干擾比（dB）")
    rsrp_dbm: float = Field(..., description="參考信號接收功率（dBm）")
    rsrq_db: float = Field(..., description="參考信號接收品質（dB）")
    cqi: int = Field(..., description="通道品質指標", ge=1, le=15)

    # 高級參數
    throughput_mbps: float = Field(default=0.0, description="預期吞吐量（Mbps）")
    latency_ms: float = Field(default=0.0, description="通道延遲（ms）")
    error_rate: float = Field(default=0.0, description="錯誤率", ge=0.0, le=1.0)

    # 更新時間
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime = Field(..., description="參數有效期")


class ChannelSimulationRequest(BaseModel):
    """通道模擬請求"""

    simulation_id: str = Field(..., description="模擬 ID")

    # 模擬環境
    environment_type: str = Field(default="urban", description="環境類型")
    weather_condition: str = Field(default="clear", description="天氣條件")

    # 網路配置
    carrier_frequency_hz: float = Field(..., description="載波頻率（Hz）")
    bandwidth_hz: float = Field(..., description="頻寬（Hz）")

    # 節點資訊
    transmitters: List[Dict[str, Any]] = Field(..., description="發送端資訊")
    receivers: List[Dict[str, Any]] = Field(..., description="接收端資訊")

    # 模擬參數
    duration_sec: float = Field(default=1.0, description="模擬時長（秒）")
    time_step_ms: float = Field(default=1.0, description="時間步長（毫秒）")

    # Ray tracing 設定
    max_reflections: int = Field(default=3, description="最大反射次數")
    diffraction_enabled: bool = Field(default=True, description="啟用繞射")
    scattering_enabled: bool = Field(default=True, description="啟用散射")


class ChannelToRANConversionResult(BaseModel):
    """通道到 RAN 參數轉換結果"""

    conversion_id: str = Field(..., description="轉換 ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # 原始通道資料
    source_channel: SionnaChannelResponse = Field(
        ..., description="原始 Sionna 通道響應"
    )

    # 轉換後的 RAN 參數
    ran_parameters: UERANSIMChannelParams = Field(..., description="UERANSIM 通道參數")

    # 轉換品質
    conversion_accuracy: float = Field(
        default=1.0, description="轉換準確度", ge=0.0, le=1.0
    )
    confidence_level: float = Field(default=1.0, description="信心度", ge=0.0, le=1.0)

    # 除錯資訊
    debug_info: Dict[str, Any] = Field(default={}, description="除錯資訊")


class ChannelUpdateEvent(BaseModel):
    """通道更新事件"""

    event_id: str = Field(..., description="事件 ID")
    event_type: str = Field(..., description="事件類型")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # 更新的通道參數
    updated_channels: List[UERANSIMChannelParams] = Field(
        ..., description="更新的通道參數"
    )

    # 變化資訊
    change_magnitude: float = Field(default=0.0, description="變化幅度")
    requires_immediate_update: bool = Field(default=False, description="需要立即更新")


class BatchChannelConversionRequest(BaseModel):
    """批次通道轉換請求"""

    batch_id: str = Field(..., description="批次 ID")
    channels: List[SionnaChannelResponse] = Field(..., description="通道響應列表")
    target_ue_ids: List[str] = Field(..., description="目標 UE ID 列表")
    priority: int = Field(default=1, description="優先級", ge=1, le=10)
    callback_url: Optional[str] = Field(None, description="回調 URL")


class ChannelModelMetrics(BaseModel):
    """通道模型指標"""

    total_channels_processed: int = Field(default=0, description="處理的通道總數")
    average_conversion_time_ms: float = Field(
        default=0.0, description="平均轉換時間（ms）"
    )
    success_rate: float = Field(default=1.0, description="成功率", ge=0.0, le=1.0)
    gpu_utilization: float = Field(
        default=0.0, description="GPU 使用率", ge=0.0, le=1.0
    )
    memory_usage_mb: float = Field(default=0.0, description="記憶體使用（MB）")
    last_update: datetime = Field(default_factory=datetime.utcnow)
