"""
干擾模型與抗干擾機制的核心領域模型

實現5G NTN系統中的干擾模擬和抗干擾相關的領域實體和值對象。
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import numpy as np


class JammerType(str, Enum):
    """干擾源類型"""

    BROADBAND_NOISE = "broadband_noise"  # 寬帶噪聲干擾
    SWEEP_JAMMER = "sweep_jammer"  # 掃頻干擾
    BARRAGE_JAMMER = "barrage_jammer"  # 阻塞式干擾
    SMART_JAMMER = "smart_jammer"  # 智能干擾
    PULSE_JAMMER = "pulse_jammer"  # 脈衝干擾
    SPOT_JAMMER = "spot_jammer"  # 點頻干擾
    PROTOCOL_AWARE_JAMMER = "protocol_aware_jammer"  # 協議感知干擾


class InterferencePattern(str, Enum):
    """干擾模式"""

    CONTINUOUS = "continuous"  # 連續干擾
    PERIODIC = "periodic"  # 週期性干擾
    RANDOM = "random"  # 隨機干擾
    ADAPTIVE = "adaptive"  # 自適應干擾


class FrequencyHopStrategy(str, Enum):
    """跳頻策略"""

    FIXED_PATTERN = "fixed_pattern"  # 固定模式
    PSEUDO_RANDOM = "pseudo_random"  # 偽隨機
    ADAPTIVE_ML = "adaptive_ml"  # 機器學習自適應
    THREAT_AWARE = "threat_aware"  # 威脅感知


class BeamformingStrategy(str, Enum):
    """波束成形策略"""

    FIXED_BEAM = "fixed_beam"  # 固定波束
    ADAPTIVE_BEAM = "adaptive_beam"  # 自適應波束
    NULLING = "nulling"  # 零點置零
    MAXIMAL_RATIO = "maximal_ratio"  # 最大比合併


class AIRANDecisionType(str, Enum):
    """AI-RAN決策類型"""

    FREQUENCY_HOP = "frequency_hop"  # 頻率跳變
    BEAM_STEERING = "beam_steering"  # 波束控制
    POWER_CONTROL = "power_control"  # 功率控制
    PROTOCOL_SWITCH = "protocol_switch"  # 協議切換
    EMERGENCY_SHUTDOWN = "emergency_shutdown"  # 緊急關閉


@dataclass
class Position3D:
    """3D位置坐標"""

    x: float
    y: float
    z: float

    def distance_to(self, other: "Position3D") -> float:
        """計算到另一點的距離"""
        return np.sqrt(
            (self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2
        )


@dataclass
class FrequencyBand:
    """頻率頻段"""

    center_freq_mhz: float
    bandwidth_mhz: float

    @property
    def start_freq_mhz(self) -> float:
        return self.center_freq_mhz - self.bandwidth_mhz / 2

    @property
    def end_freq_mhz(self) -> float:
        return self.center_freq_mhz + self.bandwidth_mhz / 2


class JammerSource(BaseModel):
    """干擾源模型"""

    jammer_id: str = Field(..., description="干擾源唯一標識")
    jammer_type: JammerType = Field(..., description="干擾類型")
    position: Tuple[float, float, float] = Field(
        ..., description="干擾源位置[x,y,z] (m)"
    )
    power_dbm: float = Field(..., description="發射功率 (dBm)")
    frequency_band: Dict[str, float] = Field(
        ..., description="頻率範圍 {center_freq_mhz, bandwidth_mhz}"
    )
    pattern: InterferencePattern = Field(
        default=InterferencePattern.CONTINUOUS, description="干擾模式"
    )

    # 干擾特性參數
    duty_cycle: float = Field(default=1.0, ge=0.0, le=1.0, description="占空比")
    pulse_width_ms: Optional[float] = Field(default=None, description="脈衝寬度 (ms)")
    sweep_rate_mhz_per_sec: Optional[float] = Field(
        default=None, description="掃頻速率"
    )
    modulation_type: Optional[str] = Field(default=None, description="調制類型")

    # 智能干擾參數
    target_protocols: List[str] = Field(
        default_factory=list, description="目標協議列表"
    )
    learning_enabled: bool = Field(default=False, description="是否啟用學習模式")

    # 時間參數
    start_time_sec: float = Field(default=0.0, description="開始時間 (s)")
    duration_sec: Optional[float] = Field(default=None, description="持續時間 (s)")

    # 移動性參數
    velocity: Optional[Tuple[float, float, float]] = Field(
        default=None, description="速度向量 [vx,vy,vz] (m/s)"
    )

    class Config:
        json_encoders = {
            JammerType: lambda v: v.value,
            InterferencePattern: lambda v: v.value,
        }


class InterferenceEnvironment(BaseModel):
    """干擾環境模型"""

    environment_id: str = Field(..., description="環境唯一標識")
    name: str = Field(..., description="環境名稱")
    description: str = Field(default="", description="環境描述")

    # 地理和物理環境
    area_bounds: Dict[str, float] = Field(
        ..., description="區域邊界 {min_x, max_x, min_y, max_y, min_z, max_z}"
    )
    environment_type: str = Field(default="urban", description="環境類型")

    # 干擾源配置
    jammer_sources: List[JammerSource] = Field(
        default_factory=list, description="干擾源列表"
    )

    # 背景噪聲
    thermal_noise_dbm: float = Field(default=-120.0, description="熱噪聲功率 (dBm)")
    background_interference_dbm: float = Field(
        default=-110.0, description="背景干擾功率 (dBm)"
    )

    # 傳播模型參數
    path_loss_exponent: float = Field(default=2.0, description="路徑損耗指數")
    shadowing_std_db: float = Field(default=8.0, description="陰影衰落標準差 (dB)")

    # 時間參數
    simulation_duration_sec: float = Field(default=60.0, description="模擬持續時間 (s)")
    time_resolution_ms: float = Field(default=1.0, description="時間解析度 (ms)")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InterferenceDetectionResult(BaseModel):
    """干擾檢測結果"""

    detection_id: str = Field(..., description="檢測結果唯一標識")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="檢測時間")

    # 檢測位置和設備
    detector_position: Tuple[float, float, float] = Field(..., description="檢測器位置")
    detector_id: str = Field(..., description="檢測器標識")

    # 干擾檢測結果
    interference_detected: bool = Field(..., description="是否檢測到干擾")
    interference_power_dbm: float = Field(..., description="干擾功率 (dBm)")
    noise_power_dbm: float = Field(..., description="噪聲功率 (dBm)")
    signal_power_dbm: float = Field(..., description="信號功率 (dBm)")

    # 信號品質指標
    sinr_db: float = Field(..., description="信干噪比 (dB)")
    snr_db: float = Field(..., description="信噪比 (dB)")
    rssi_dbm: float = Field(..., description="接收信號強度 (dBm)")

    # 頻譜分析
    frequency_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="頻譜分析結果"
    )
    affected_frequencies: List[Dict[str, float]] = Field(
        default_factory=list, description="受影響頻率"
    )

    # 干擾特徵識別
    suspected_jammer_type: Optional[JammerType] = Field(
        default=None, description="疑似干擾類型"
    )
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="置信度分數"
    )

    # 影響評估
    throughput_degradation_percent: float = Field(
        default=0.0, description="吞吐量下降百分比"
    )
    latency_increase_ms: float = Field(default=0.0, description="延遲增加 (ms)")
    error_rate_increase: float = Field(default=0.0, description="錯誤率增加")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            JammerType: lambda v: v.value if v else None,
        }


class FrequencyHopPattern(BaseModel):
    """跳頻模式"""

    pattern_id: str = Field(..., description="跳頻模式唯一標識")
    strategy: FrequencyHopStrategy = Field(..., description="跳頻策略")

    # 頻率序列
    frequency_list_mhz: List[float] = Field(..., description="頻率列表 (MHz)")
    hop_duration_ms: float = Field(..., description="每跳持續時間 (ms)")
    dwell_time_ms: float = Field(..., description="駐留時間 (ms)")

    # 模式參數
    seed: Optional[int] = Field(default=None, description="偽隨機種子")
    repeat_count: int = Field(default=1, description="重複次數")

    # 自適應參數
    adaptation_threshold_db: float = Field(default=-80.0, description="自適應閾值 (dB)")
    blacklist_frequencies: List[float] = Field(
        default_factory=list, description="黑名單頻率"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)


class BeamformingConfig(BaseModel):
    """波束成形配置"""

    config_id: str = Field(..., description="配置唯一標識")
    strategy: BeamformingStrategy = Field(..., description="波束成形策略")

    # 天線陣列參數
    antenna_count: int = Field(..., description="天線數量")
    antenna_spacing_m: float = Field(default=0.15, description="天線間距 (m)")
    array_geometry: str = Field(default="linear", description="陣列幾何")

    # 波束參數
    target_direction_deg: Tuple[float, float] = Field(
        ..., description="目標方向 [azimuth, elevation]"
    )
    beam_width_deg: float = Field(default=30.0, description="波束寬度 (度)")
    sidelobe_level_db: float = Field(default=-20.0, description="副瓣電平 (dB)")

    # 零點配置
    null_directions_deg: List[Tuple[float, float]] = Field(
        default_factory=list, description="零點方向列表"
    )
    null_depth_db: float = Field(default=-40.0, description="零點深度 (dB)")

    # 自適應參數
    adaptation_enabled: bool = Field(default=False, description="是否啟用自適應")
    update_interval_ms: float = Field(default=100.0, description="更新間隔 (ms)")

    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIRANDecision(BaseModel):
    """AI-RAN決策結果"""

    decision_id: str = Field(..., description="決策唯一標識")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="決策時間")

    # 決策上下文
    trigger_event: str = Field(..., description="觸發事件")
    interference_level_db: float = Field(..., description="干擾水平 (dB)")
    urgency_level: int = Field(default=1, ge=1, le=5, description="緊急程度 1-5")

    # 決策內容
    decision_type: AIRANDecisionType = Field(..., description="決策類型")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="決策置信度")

    # 具體行動參數
    target_frequencies_mhz: List[float] = Field(
        default_factory=list, description="目標頻率列表"
    )
    hop_pattern_id: Optional[str] = Field(default=None, description="跳頻模式ID")
    beam_config_id: Optional[str] = Field(default=None, description="波束配置ID")
    power_adjustment_db: float = Field(default=0.0, description="功率調整 (dB)")

    # 執行時間參數
    execution_delay_ms: float = Field(default=0.0, description="執行延遲 (ms)")
    duration_ms: Optional[float] = Field(default=None, description="持續時間 (ms)")

    # 預期效果
    expected_sinr_improvement_db: float = Field(
        default=0.0, description="預期SINR改善 (dB)"
    )
    expected_throughput_improvement_percent: float = Field(
        default=0.0, description="預期吞吐量改善百分比"
    )

    # 風險評估
    interference_risk_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="干擾風險分數"
    )
    collision_probability: float = Field(
        default=0.0, ge=0.0, le=1.0, description="衝突概率"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            AIRANDecisionType: lambda v: v.value,
        }


# ===== 請求和響應模型 =====


class InterferenceSimulationRequest(BaseModel):
    """干擾模擬請求"""

    request_id: str = Field(..., description="請求唯一標識")
    environment: InterferenceEnvironment = Field(..., description="干擾環境")

    # 受害者（通信設備）位置
    victim_positions: List[Tuple[float, float, float]] = Field(
        ..., description="受害者位置列表"
    )
    victim_frequency_mhz: float = Field(..., description="受害者工作頻率 (MHz)")
    victim_bandwidth_mhz: float = Field(..., description="受害者頻寬 (MHz)")

    # 模擬參數
    simulation_time_step_ms: float = Field(default=1.0, description="模擬時間步長 (ms)")
    include_propagation_effects: bool = Field(
        default=True, description="是否包含傳播效應"
    )
    include_multipath: bool = Field(default=True, description="是否包含多路徑")

    # GPU加速參數
    use_gpu_acceleration: bool = Field(default=True, description="是否使用GPU加速")
    batch_size: int = Field(default=1000, description="批處理大小")

    class Config:
        arbitrary_types_allowed = True


class InterferenceSimulationResponse(BaseModel):
    """干擾模擬響應"""

    request_id: str = Field(..., description="對應的請求ID")
    simulation_id: str = Field(..., description="模擬唯一標識")
    success: bool = Field(..., description="模擬是否成功")
    message: str = Field(default="", description="結果信息")

    # 時間信息
    start_time: datetime = Field(
        default_factory=datetime.utcnow, description="開始時間"
    )
    completion_time: datetime = Field(
        default_factory=datetime.utcnow, description="完成時間"
    )
    processing_time_ms: float = Field(..., description="處理時間 (ms)")

    # 模擬結果
    detection_results: List[InterferenceDetectionResult] = Field(
        default_factory=list, description="檢測結果列表"
    )

    # 統計摘要
    summary_statistics: Dict[str, Any] = Field(
        default_factory=dict, description="統計摘要"
    )
    affected_victim_count: int = Field(default=0, description="受影響受害者數量")
    average_sinr_degradation_db: float = Field(
        default=0.0, description="平均SINR下降 (dB)"
    )

    # 性能指標
    simulation_accuracy: float = Field(default=0.0, description="模擬精度")
    computational_complexity: str = Field(default="", description="計算複雜度")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AIRANControlRequest(BaseModel):
    """AI-RAN控制請求"""

    request_id: str = Field(..., description="請求唯一標識")
    scenario_description: str = Field(..., description="場景描述")

    # 當前狀態
    current_interference_state: List[InterferenceDetectionResult] = Field(
        ..., description="當前干擾狀態"
    )
    current_network_performance: Dict[str, Any] = Field(..., description="當前網路性能")

    # 約束條件
    available_frequencies_mhz: List[float] = Field(..., description="可用頻率列表")
    power_constraints_dbm: Dict[str, float] = Field(..., description="功率約束")
    latency_requirements_ms: float = Field(default=1.0, description="延遲要求 (ms)")

    # AI模型參數
    model_type: str = Field(default="DQN", description="AI模型類型")
    use_historical_data: bool = Field(default=True, description="是否使用歷史數據")
    risk_tolerance: float = Field(default=0.1, ge=0.0, le=1.0, description="風險容忍度")

    class Config:
        arbitrary_types_allowed = True


class AIRANControlResponse(BaseModel):
    """AI-RAN控制響應"""

    request_id: str = Field(..., description="對應的請求ID")
    control_id: str = Field(..., description="控制唯一標識")
    success: bool = Field(..., description="控制是否成功")
    message: str = Field(default="", description="結果信息")

    # 決策結果
    ai_decision: AIRANDecision = Field(..., description="AI決策結果")
    alternative_decisions: List[AIRANDecision] = Field(
        default_factory=list, description="備選決策"
    )

    # 執行計劃
    execution_plan: List[Dict[str, Any]] = Field(
        default_factory=list, description="執行計劃"
    )
    rollback_plan: List[Dict[str, Any]] = Field(
        default_factory=list, description="回滾計劃"
    )

    # 預期效果評估
    performance_prediction: Dict[str, Any] = Field(
        default_factory=dict, description="性能預測"
    )
    risk_assessment: Dict[str, Any] = Field(
        default_factory=dict, description="風險評估"
    )

    # 時間信息
    decision_time_ms: float = Field(..., description="決策時間 (ms)")
    estimated_execution_time_ms: float = Field(..., description="估計執行時間 (ms)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# ===== 事件和指標模型 =====


class InterferenceEvent(BaseModel):
    """干擾事件"""

    event_id: str = Field(..., description="事件唯一標識")
    event_type: str = Field(..., description="事件類型")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="事件時間")

    # 事件內容
    interference_source_id: str = Field(..., description="干擾源ID")
    affected_devices: List[str] = Field(..., description="受影響設備列表")
    severity_level: int = Field(..., ge=1, le=5, description="嚴重程度 1-5")

    # 響應信息
    response_action: Optional[str] = Field(default=None, description="響應行動")
    response_time_ms: Optional[float] = Field(default=None, description="響應時間 (ms)")
    recovery_time_ms: Optional[float] = Field(default=None, description="恢復時間 (ms)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class InterferenceMetrics(BaseModel):
    """干擾系統指標"""

    metrics_id: str = Field(..., description="指標唯一標識")
    collection_time: datetime = Field(
        default_factory=datetime.utcnow, description="收集時間"
    )
    time_window_sec: float = Field(..., description="時間窗口 (s)")

    # 干擾檢測指標
    total_detections: int = Field(default=0, description="總檢測次數")
    false_positive_rate: float = Field(default=0.0, description="誤檢率")
    false_negative_rate: float = Field(default=0.0, description="漏檢率")
    detection_accuracy: float = Field(default=0.0, description="檢測準確率")

    # AI-RAN性能指標
    total_decisions: int = Field(default=0, description="總決策次數")
    successful_mitigations: int = Field(default=0, description="成功緩解次數")
    average_decision_time_ms: float = Field(
        default=0.0, description="平均決策時間 (ms)"
    )
    average_response_time_ms: float = Field(
        default=0.0, description="平均響應時間 (ms)"
    )

    # 網路性能指標
    throughput_improvement_percent: float = Field(
        default=0.0, description="吞吐量改善百分比"
    )
    latency_reduction_ms: float = Field(default=0.0, description="延遲減少 (ms)")
    reliability_improvement_percent: float = Field(
        default=0.0, description="可靠性改善百分比"
    )

    # 資源使用指標
    cpu_usage_percent: float = Field(default=0.0, description="CPU使用率")
    memory_usage_mb: float = Field(default=0.0, description="內存使用量 (MB)")
    gpu_usage_percent: float = Field(default=0.0, description="GPU使用率")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
