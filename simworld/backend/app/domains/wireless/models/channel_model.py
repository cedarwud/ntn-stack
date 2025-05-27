"""
無線通道領域模型

定義 Sionna 無線通道參數和 UERANSIM RAN 參數的數據結構，
以及它們之間的轉換映射關係。
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import numpy as np


class ChannelType(str, Enum):
    """通道類型枚舉"""

    LOS = "line_of_sight"  # 視距傳播
    NLOS = "non_line_of_sight"  # 非視距傳播
    URBAN = "urban"  # 都市環境
    RURAL = "rural"  # 郊區環境
    SATELLITE = "satellite"  # 衛星通道
    UAV = "uav"  # 無人機通道


class ChannelParameters(BaseModel):
    """Sionna 通道參數模型"""

    # 基本通道資訊
    channel_id: str = Field(..., description="通道唯一識別碼")
    channel_type: ChannelType = Field(..., description="通道類型")
    frequency_hz: float = Field(..., description="載波頻率 (Hz)")

    # 路徑損耗參數
    path_loss_db: float = Field(..., description="路徑損耗 (dB)")
    shadow_fading_db: Optional[float] = Field(None, description="陰影衰落 (dB)")

    # 多徑參數
    multipath_components: List[Dict[str, float]] = Field(
        default_factory=list,
        description="多徑分量 [{'delay_s': float, 'power_db': float, 'aoa_deg': float, 'aod_deg': float}]",
    )
    delay_spread_s: Optional[float] = Field(None, description="延遲擴散 (s)")

    # 角度參數
    azimuth_spread_deg: Optional[float] = Field(None, description="方位角擴散 (deg)")
    elevation_spread_deg: Optional[float] = Field(None, description="仰角擴散 (deg)")

    # 多普勒參數
    doppler_shift_hz: Optional[float] = Field(None, description="多普勒頻移 (Hz)")
    doppler_spread_hz: Optional[float] = Field(None, description="多普勒擴散 (Hz)")

    # 信號品質參數
    sinr_db: Optional[float] = Field(None, description="信噪干擾比 (dB)")
    snr_db: Optional[float] = Field(None, description="信噪比 (dB)")

    # 位置資訊
    tx_position: Tuple[float, float, float] = Field(
        ..., description="發射器位置 (x, y, z) meters"
    )
    rx_position: Tuple[float, float, float] = Field(
        ..., description="接收器位置 (x, y, z) meters"
    )

    # 時間戳
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="參數生成時間"
    )

    # 額外參數
    additional_params: Optional[Dict[str, Any]] = Field(
        None, description="額外通道參數"
    )


class ChannelResponse(BaseModel):
    """通道響應模型"""

    # 基本資訊
    response_id: str = Field(..., description="響應唯一識別碼")
    channel_id: str = Field(..., description="對應的通道 ID")

    # 頻域響應
    frequency_response: Optional[List[complex]] = Field(
        None, description="頻域響應 H(f)"
    )
    frequencies_hz: Optional[List[float]] = Field(None, description="頻率點 (Hz)")

    # 時域響應
    impulse_response: Optional[List[complex]] = Field(None, description="脈衝響應 h(t)")
    time_samples_s: Optional[List[float]] = Field(None, description="時間採樣點 (s)")

    # 通道矩陣 (MIMO)
    channel_matrix: Optional[List[List[complex]]] = Field(
        None, description="MIMO 通道矩陣"
    )

    # 生成時間
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="響應生成時間"
    )


class RANParameters(BaseModel):
    """UERANSIM RAN 參數模型"""

    # 基本配置
    ran_config_id: str = Field(..., description="RAN 配置唯一識別碼")
    gnb_id: int = Field(..., description="gNodeB ID")
    cell_id: int = Field(..., description="Cell ID")

    # 無線參數
    tx_power_dbm: float = Field(..., description="發射功率 (dBm)")
    antenna_gain_dbi: float = Field(0.0, description="天線增益 (dBi)")
    noise_figure_db: float = Field(7.0, description="噪聲系數 (dB)")

    # 頻率配置
    dl_arfcn: int = Field(..., description="下行 ARFCN")
    ul_arfcn: int = Field(..., description="上行 ARFCN")
    band: int = Field(..., description="頻段編號")

    # 覆蓋參數
    cell_range_km: float = Field(..., description="小區覆蓋範圍 (km)")

    # 信號品質參數
    reference_signal_power_dbm: float = Field(..., description="參考信號功率 (dBm)")
    sinr_threshold_db: float = Field(-6.0, description="SINR 門檻值 (dB)")

    # 通道模型參數
    path_loss_model: str = Field("freespace", description="路徑損耗模型")
    fading_model: str = Field("none", description="衰落模型")

    # NTN 特殊參數 (衛星/UAV 場景)
    elevation_angle_deg: Optional[float] = Field(None, description="仰角 (deg)")
    doppler_compensation: bool = Field(False, description="是否啟用多普勒補償")
    beam_steering: bool = Field(False, description="是否啟用波束成形")

    # 位置資訊
    gnb_position: Tuple[float, float, float] = Field(
        ..., description="gNodeB 位置 (lat, lon, alt)"
    )

    # 時間戳
    config_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="配置時間戳"
    )

    # 生效狀態
    is_active: bool = Field(True, description="配置是否生效")


class ChannelToRANMappingRequest(BaseModel):
    """通道參數到 RAN 參數轉換請求模型"""

    # 請求資訊
    request_id: str = Field(..., description="請求唯一識別碼")

    # 輸入通道參數
    channel_parameters: ChannelParameters = Field(..., description="Sionna 通道參數")

    # 目標 RAN 配置
    target_gnb_id: int = Field(..., description="目標 gNodeB ID")
    target_cell_id: int = Field(..., description="目標 Cell ID")

    # 轉換選項
    mapping_mode: str = Field(
        "automatic", description="轉換模式: 'automatic', 'conservative', 'aggressive'"
    )
    preserve_coverage: bool = Field(True, description="是否保持覆蓋範圍")

    # 請求時間
    requested_at: datetime = Field(
        default_factory=datetime.utcnow, description="請求時間"
    )


class ChannelToRANMappingResponse(BaseModel):
    """通道參數到 RAN 參數轉換回應模型"""

    # 回應資訊
    response_id: str = Field(..., description="回應唯一識別碼")
    request_id: str = Field(..., description="對應的請求 ID")

    # 轉換結果
    success: bool = Field(..., description="轉換是否成功")
    ran_parameters: Optional[RANParameters] = Field(
        None, description="轉換後的 RAN 參數"
    )

    # 轉換詳情
    mapping_details: Dict[str, Any] = Field(
        default_factory=dict, description="轉換詳情和中間計算結果"
    )

    # 品質評估
    mapping_quality_score: float = Field(0.0, description="轉換品質評分 (0-1)")
    confidence_level: float = Field(0.0, description="置信水準 (0-1)")

    # 警告和建議
    warnings: List[str] = Field(default_factory=list, description="轉換警告")
    recommendations: List[str] = Field(default_factory=list, description="建議")

    # 回應時間
    processed_at: datetime = Field(
        default_factory=datetime.utcnow, description="處理完成時間"
    )
    processing_time_ms: float = Field(0.0, description="處理時間 (毫秒)")


class UERANSIMConfiguration(BaseModel):
    """UERANSIM 完整配置模型"""

    # 配置資訊
    config_id: str = Field(..., description="配置唯一識別碼")
    config_name: str = Field(..., description="配置名稱")
    config_version: str = Field("1.0", description="配置版本")

    # gNodeB 配置
    gnb_config: RANParameters = Field(..., description="gNodeB 配置參數")

    # UE 配置列表
    ue_configs: List[Dict[str, Any]] = Field(
        default_factory=list, description="UE 配置列表"
    )

    # 網絡配置
    amf_address: str = Field("127.0.0.1", description="AMF 地址")
    plmn_list: List[Dict[str, str]] = Field(
        default_factory=lambda: [{"mcc": "001", "mnc": "01"}], description="PLMN 列表"
    )

    # 部署配置
    deployment_mode: str = Field(
        "container", description="部署模式: 'container', 'standalone'"
    )
    container_name: Optional[str] = Field(None, description="容器名稱")

    # 配置狀態
    is_deployed: bool = Field(False, description="是否已部署")
    deployment_timestamp: Optional[datetime] = Field(None, description="部署時間戳")

    # 創建和更新時間
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="創建時間"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="更新時間"
    )


class ChannelQualityMetrics(BaseModel):
    """通道品質指標模型"""

    # 基本資訊
    metrics_id: str = Field(..., description="指標唯一識別碼")
    channel_id: str = Field(..., description="對應的通道 ID")

    # 基本指標
    rsrp_dbm: Optional[float] = Field(None, description="參考信號接收功率 (dBm)")
    rsrq_db: Optional[float] = Field(None, description="參考信號接收品質 (dB)")
    sinr_db: Optional[float] = Field(None, description="信噪干擾比 (dB)")

    # 吞吐量指標
    theoretical_throughput_mbps: Optional[float] = Field(
        None, description="理論吞吐量 (Mbps)"
    )
    actual_throughput_mbps: Optional[float] = Field(
        None, description="實際吞吐量 (Mbps)"
    )
    spectral_efficiency_bps_hz: Optional[float] = Field(
        None, description="頻譜效率 (bps/Hz)"
    )

    # 干擾指標
    interference_level_db: Optional[float] = Field(None, description="干擾電平 (dB)")
    interference_sources: List[str] = Field(
        default_factory=list, description="干擾源列表"
    )

    # 移動性指標
    handover_probability: Optional[float] = Field(None, description="切換機率")
    connection_stability: Optional[float] = Field(None, description="連接穩定性")

    # 測量時間
    measurement_time: datetime = Field(
        default_factory=datetime.utcnow, description="測量時間"
    )
    measurement_duration_s: float = Field(1.0, description="測量持續時間 (s)")
