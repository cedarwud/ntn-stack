"""
Sionna 無線通道模擬相關的數據模型
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class ChannelScenario(str, Enum):
    """通道場景類型"""

    NTN_RURAL = "ntn_rural"
    NTN_URBAN = "ntn_urban"
    NTN_SUBURBAN = "ntn_suburban"
    TERRESTRIAL_URBAN = "urban"
    TERRESTRIAL_RURAL = "rural"


class Position3D(BaseModel):
    """3D 位置"""

    x: float = Field(..., description="X 坐標 (米)")
    y: float = Field(..., description="Y 坐標 (米)")
    z: float = Field(..., description="Z 坐標 (米)")


class SionnaChannelRequest(BaseModel):
    """Sionna 通道模擬請求"""

    scenario: ChannelScenario = Field(..., description="通道場景")
    ue_positions: List[Position3D] = Field(..., description="UE 位置列表")
    gnb_positions: List[Position3D] = Field(..., description="gNB 位置列表")
    frequency_hz: float = Field(2.1e9, description="載波頻率 (Hz)")
    bandwidth_hz: float = Field(20e6, description="帶寬 (Hz)")
    enable_ray_tracing: bool = Field(True, description="啟用射線追蹤")
    enable_multipath: bool = Field(True, description="啟用多路徑效應")
    enable_doppler: bool = Field(True, description="啟用多普勒效應")
    simulation_duration_sec: float = Field(10.0, description="模擬時長 (秒)")


class PathLossParams(BaseModel):
    """路徑損耗參數"""

    free_space_loss_db: float = Field(..., description="自由空間路徑損耗 (dB)")
    atmospheric_loss_db: float = Field(0.0, description="大氣損耗 (dB)")
    rain_attenuation_db: float = Field(0.0, description="雨衰 (dB)")
    total_loss_db: float = Field(..., description="總路徑損耗 (dB)")


class SINRParameters(BaseModel):
    """SINR 參數"""

    signal_power_dbm: float = Field(..., description="信號功率 (dBm)")
    noise_power_dbm: float = Field(..., description="噪聲功率 (dBm)")
    interference_power_dbm: float = Field(0.0, description="干擾功率 (dBm)")
    sinr_db: float = Field(..., description="SINR (dB)")


class ChannelCharacteristics(BaseModel):
    """通道特性"""

    path_loss: PathLossParams = Field(..., description="路徑損耗參數")
    sinr: SINRParameters = Field(..., description="SINR 參數")
    delay_spread_ns: float = Field(..., description="延遲擴散 (納秒)")
    doppler_shift_hz: float = Field(..., description="多普勒頻移 (Hz)")
    angular_spread_deg: Dict[str, float] = Field(
        default_factory=dict, description="角度擴散 (度)"
    )
    coherence_bandwidth_hz: float = Field(..., description="相關帶寬 (Hz)")
    coherence_time_ms: float = Field(..., description="相關時間 (毫秒)")


class SionnaChannelResponse(BaseModel):
    """Sionna 通道模擬響應"""

    success: bool = Field(..., description="模擬是否成功")
    scenario: ChannelScenario = Field(..., description="模擬場景")
    simulation_result: Dict[str, Any] = Field(..., description="模擬結果")
    channel_characteristics: List[ChannelCharacteristics] = Field(
        default_factory=list, description="通道特性列表"
    )
    path_loss_matrix_db: List[List[float]] = Field(
        default_factory=list, description="路徑損耗矩陣 (dB)"
    )
    sinr_matrix_db: List[List[float]] = Field(
        default_factory=list, description="SINR 矩陣 (dB)"
    )
    doppler_shifts_hz: List[float] = Field(
        default_factory=list, description="多普勒頻移列表 (Hz)"
    )
    delay_spreads_ns: List[float] = Field(
        default_factory=list, description="延遲擴散列表 (納秒)"
    )
    computation_time_sec: float = Field(..., description="計算時間 (秒)")
    ueransim_config_updates: Optional[Dict] = Field(
        None, description="UERANSIM 配置更新建議"
    )
    message: str = Field("", description="響應訊息")


class InterferenceSource(BaseModel):
    """干擾源"""

    source_id: str = Field(..., description="干擾源 ID")
    position: Position3D = Field(..., description="干擾源位置")
    power_dbm: float = Field(..., description="干擾功率 (dBm)")
    frequency_hz: float = Field(..., description="干擾頻率 (Hz)")
    bandwidth_hz: float = Field(..., description="干擾帶寬 (Hz)")
    interference_type: str = Field("broadband", description="干擾類型")


class InterferenceSimulationRequest(BaseModel):
    """干擾模擬請求"""

    base_scenario: SionnaChannelRequest = Field(..., description="基礎場景")
    interference_sources: List[InterferenceSource] = Field(
        ..., description="干擾源列表"
    )
    enable_ai_mitigation: bool = Field(False, description="啟用 AI 抗干擾")
    mitigation_algorithm: str = Field("frequency_hopping", description="抗干擾算法")


class InterferenceSimulationResponse(BaseModel):
    """干擾模擬響應"""

    base_response: SionnaChannelResponse = Field(..., description="基礎模擬結果")
    interference_impact: Dict[str, float] = Field(..., description="干擾影響分析")
    sinr_degradation_db: List[float] = Field(..., description="SINR 降級 (dB)")
    mitigation_effectiveness: float = Field(0.0, description="抗干擾效果 (0-1)")
    recommended_actions: List[str] = Field(
        default_factory=list, description="建議的應對措施"
    )
