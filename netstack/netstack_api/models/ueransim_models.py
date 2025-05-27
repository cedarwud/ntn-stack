"""
UERANSIM動態配置相關的數據模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ScenarioType(str, Enum):
    """場景類型"""

    LEO_SATELLITE_PASS = "leo_satellite_pass"
    UAV_FORMATION_FLIGHT = "uav_formation_flight"
    HANDOVER_BETWEEN_SATELLITES = "handover_between_satellites"
    EMERGENCY_RECONNECT = "emergency_reconnect"
    POSITION_UPDATE = "position_update"


class SatellitePosition(BaseModel):
    """衛星位置信息"""

    id: str = Field(..., description="衛星識別碼")
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    altitude: float = Field(..., gt=0, description="高度(公里)")
    elevation_angle: Optional[float] = Field(None, ge=0, le=90, description="仰角(度)")
    azimuth: Optional[float] = Field(None, ge=0, le=360, description="方位角(度)")
    signal_strength: Optional[float] = Field(None, description="信號強度(dBm)")


class UAVPosition(BaseModel):
    """無人機位置信息"""

    id: str = Field(..., description="無人機識別碼")
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    altitude: float = Field(..., gt=0, description="高度(公尺)")
    speed: Optional[float] = Field(None, ge=0, description="速度(km/h)")
    heading: Optional[float] = Field(None, ge=0, le=360, description="航向(度)")
    role: Optional[str] = Field("leader", description="角色(leader/follower)")


class NetworkParameters(BaseModel):
    """網絡參數"""

    frequency: int = Field(2100, ge=1900, le=2700, description="頻率(MHz)")
    bandwidth: int = Field(20, description="頻寬(MHz)")
    tx_power: Optional[int] = Field(23, description="發射功率(dBm)")
    expected_sinr: Optional[float] = Field(15, description="預期SINR(dB)")
    coordination_required: Optional[bool] = Field(False, description="是否需要協調")
    priority_levels: Optional[List[str]] = Field(None, description="優先級別")


class HandoverParameters(BaseModel):
    """切換參數"""

    trigger_threshold: float = Field(-90, description="觸發閾值(dBm)")
    hysteresis: float = Field(3, description="遲滯(dB)")
    time_to_trigger: int = Field(320, description="觸發時間(ms)")


class UERANSIMConfigRequest(BaseModel):
    """UERANSIM配置生成請求"""

    scenario: ScenarioType = Field(..., description="場景類型")
    satellite: Optional[SatellitePosition] = Field(None, description="衛星位置")
    source_satellite: Optional[SatellitePosition] = Field(
        None, description="源衛星位置"
    )
    target_satellite: Optional[SatellitePosition] = Field(
        None, description="目標衛星位置"
    )
    uav: Optional[UAVPosition] = Field(None, description="無人機位置")
    uav_formation: Optional[List[UAVPosition]] = Field(None, description="無人機編隊")
    network_params: Optional[NetworkParameters] = Field(None, description="網絡參數")
    handover_params: Optional[HandoverParameters] = Field(None, description="切換參數")


class GNBConfig(BaseModel):
    """gNodeB配置"""

    mcc: int = Field(999, description="移動國家代碼")
    mnc: int = Field(70, description="移動網絡代碼")
    nci: str = Field("0x000000010", description="NR小區標識")
    id_length: int = Field(32, description="ID長度")
    tac: int = Field(1, description="追蹤區域代碼")
    link_ip: str = Field("172.17.0.1", description="鏈路IP")
    ngap_ip: str = Field("172.17.0.1", description="NGAP IP")
    gtp_ip: str = Field("172.17.0.1", description="GTP IP")
    frequency: int = Field(2100, description="頻率")
    tx_power: int = Field(23, description="發射功率")


class UEConfig(BaseModel):
    """UE配置"""

    supi: str = Field(..., description="用戶識別")
    mcc: int = Field(999, description="移動國家代碼")
    mnc: int = Field(70, description="移動網絡代碼")
    op: str = Field("63bfa50ee6523365ff14c1f45f88737d", description="操作者密鑰")
    amf: str = Field("8000", description="AMF設定")
    imei: str = Field("356938035643803", description="設備識別")
    guti: Optional[str] = Field(None, description="全球唯一臨時識別")
    initial_slice: str = Field("01:111111", description="初始切片")


class ScenarioInfo(BaseModel):
    """場景信息"""

    scenario_type: str = Field(..., description="場景類型")
    generation_time: str = Field(..., description="生成時間")
    satellite_info: Optional[Dict[str, Any]] = Field(None, description="衛星信息")
    uav_info: Optional[Dict[str, Any]] = Field(None, description="無人機信息")
    network_info: Optional[Dict[str, Any]] = Field(None, description="網絡信息")


class UERANSIMConfigResponse(BaseModel):
    """UERANSIM配置生成回應"""

    success: bool = Field(..., description="是否成功")
    scenario_type: str = Field(..., description="場景類型")
    gnb_config: Optional[GNBConfig] = Field(None, description="gNodeB配置")
    gnb_configs: Optional[List[GNBConfig]] = Field(None, description="多個gNodeB配置")
    ue_config: Optional[UEConfig] = Field(None, description="UE配置")
    ue_configs: Optional[List[UEConfig]] = Field(None, description="多個UE配置")
    scenario_info: ScenarioInfo = Field(..., description="場景信息")
    config_yaml: Optional[str] = Field(None, description="生成的YAML配置")
    message: Optional[str] = Field(None, description="回應消息")


class ConfigTemplateInfo(BaseModel):
    """配置模板信息"""

    template_name: str = Field(..., description="模板名稱")
    scenario_type: str = Field(..., description="適用場景")
    description: str = Field(..., description="模板描述")
    parameters: List[str] = Field(..., description="可配置參數列表")
    last_updated: str = Field(..., description="最後更新時間")
