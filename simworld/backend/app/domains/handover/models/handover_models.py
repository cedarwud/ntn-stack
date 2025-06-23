from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Integer, Float, String, DateTime, Text, Enum as SQLEnum


class HandoverStatus(str, Enum):
    """換手狀態枚舉"""

    IDLE = "idle"
    PREDICTING = "predicting"
    HANDOVER = "handover"
    COMPLETE = "complete"
    FAILED = "failed"


class HandoverTriggerType(str, Enum):
    """換手觸發類型"""

    MANUAL = "manual"
    AUTOMATIC = "automatic"
    PREDICTED = "predicted"
    EMERGENCY = "emergency"


# 預測資料表 (R table) - 根據 IEEE INFOCOM 2024 論文
class HandoverPredictionTable(SQLModel, table=True):
    """
    換手預測記錄表 (R table)
    根據 IEEE INFOCOM 2024 論文的 Fine-Grained Synchronized Algorithm
    """

    __tablename__ = "handover_prediction_table"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
        description="主鍵 ID",
    )

    # 基本標識
    ue_id: int = Field(index=True, description="UE 設備 ID")
    prediction_id: str = Field(index=True, description="預測批次 ID")

    # 時間點 - T 和 T+Δt
    current_time: datetime = Field(description="當前時間 T")
    future_time: datetime = Field(description="預測時間 T+Δt")
    delta_t_seconds: int = Field(description="時間間隔 Δt (秒)")

    # 衛星選擇結果
    current_satellite_id: str = Field(description="當前最佳衛星 ID (AT)")
    future_satellite_id: str = Field(description="預測最佳衛星 ID (AT+Δt)")

    # 換手決策
    handover_required: bool = Field(default=False, description="是否需要換手")
    handover_trigger_time: Optional[datetime] = Field(
        default=None, description="換手觸發時間 Tp (如需換手)"
    )

    # Binary Search Refinement 結果
    binary_search_iterations: int = Field(
        default=0, description="Binary Search 迭代次數"
    )
    precision_achieved: float = Field(default=0.0, description="達到的精度 (秒)")
    search_details: Optional[str] = Field(
        default=None, description="搜索過程詳細資訊 JSON"
    )

    # 預測信賴水準和品質
    prediction_confidence: float = Field(description="預測信賴水準 (0-1)")
    signal_quality_current: float = Field(description="當前衛星信號品質")
    signal_quality_future: float = Field(description="預測衛星信號品質")

    # 創建和更新時間
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="創建時間"
    )
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")


# Binary Search 迭代記錄
class BinarySearchIteration(BaseModel):
    """Binary Search Refinement 迭代記錄"""

    iteration: int = PydanticField(description="迭代次數")
    start_time: float = PydanticField(description="搜索開始時間 (timestamp)")
    end_time: float = PydanticField(description="搜索結束時間 (timestamp)")
    mid_time: float = PydanticField(description="中點時間 (timestamp)")
    satellite: str = PydanticField(description="中點時間選中的衛星")
    precision: float = PydanticField(description="當前精度 (秒)")
    completed: bool = PydanticField(description="是否完成")


# 簡化的預測記錄 (用於服務層)
class HandoverPredictionRecord(BaseModel):
    """換手預測記錄 (用於內存快取)"""

    ue_id: str = PydanticField(description="UE 設備 ID")
    current_satellite: str = PydanticField(description="當前最佳衛星 (AT)")
    predicted_satellite: str = PydanticField(description="預測最佳衛星 (AT+Δt)")
    handover_time: Optional[float] = PydanticField(
        default=None, description="換手觸發時間 Tp"
    )
    prediction_confidence: float = PydanticField(description="預測信賴水準")
    last_updated: datetime = PydanticField(description="最後更新時間")


# 手動換手請求
class ManualHandoverRequest(SQLModel, table=True):
    """手動換手請求記錄"""

    __tablename__ = "manual_handover_request"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
        description="主鍵 ID",
    )

    ue_id: int = Field(index=True, description="UE 設備 ID")
    from_satellite_id: str = Field(description="源衛星 ID")
    to_satellite_id: str = Field(description="目標衛星 ID")

    trigger_type: HandoverTriggerType = Field(
        default=HandoverTriggerType.MANUAL,
        sa_column=Column(SQLEnum(HandoverTriggerType)),
        description="觸發類型",
    )

    status: HandoverStatus = Field(
        default=HandoverStatus.IDLE,
        sa_column=Column(SQLEnum(HandoverStatus)),
        description="換手狀態",
    )

    # 換手執行數據
    request_time: datetime = Field(
        default_factory=datetime.utcnow, description="請求時間"
    )
    start_time: Optional[datetime] = Field(default=None, description="開始時間")
    completion_time: Optional[datetime] = Field(default=None, description="完成時間")
    duration_seconds: Optional[float] = Field(default=None, description="持續時間 (秒)")

    # 結果和元數據
    success: Optional[bool] = Field(default=None, description="是否成功")
    error_message: Optional[str] = Field(default=None, description="錯誤訊息")
    extra_data: Optional[str] = Field(default=None, description="額外資料 JSON")


# API 請求/響應模型
class HandoverPredictionRequest(BaseModel):
    """換手預測請求"""

    ue_id: int = PydanticField(description="UE 設備 ID")
    delta_t_seconds: int = PydanticField(default=5, description="預測時間間隔 (秒)")
    precision_threshold: float = PydanticField(default=0.1, description="精度閾值 (秒)")


class HandoverPredictionResponse(BaseModel):
    """換手預測響應"""

    prediction_id: str = PydanticField(description="預測批次 ID")
    ue_id: int = PydanticField(description="UE 設備 ID")

    # 時間資訊
    current_time: float = PydanticField(description="當前時間 T (timestamp)")
    future_time: float = PydanticField(description="預測時間 T+Δt (timestamp)")
    delta_t_seconds: int = PydanticField(description="時間間隔 Δt")

    # 衛星選擇結果
    current_satellite: Dict[str, Any] = PydanticField(description="當前最佳衛星資訊")
    future_satellite: Dict[str, Any] = PydanticField(description="預測最佳衛星資訊")

    # 換手決策
    handover_required: bool = PydanticField(description="是否需要換手")
    handover_trigger_time: Optional[float] = PydanticField(
        default=None, description="換手觸發時間 Tp (timestamp)"
    )

    # Binary Search 結果
    binary_search_result: Optional[Dict[str, Any]] = PydanticField(
        default=None, description="Binary Search 精細化結果"
    )

    # 預測品質
    prediction_confidence: float = PydanticField(description="預測信賴水準")
    accuracy_percentage: float = PydanticField(description="預測準確率百分比")


class ManualHandoverTriggerRequest(BaseModel):
    """手動換手觸發請求"""

    ue_id: int = PydanticField(description="UE 設備 ID")
    target_satellite_id: str = PydanticField(description="目標衛星 ID")
    trigger_type: HandoverTriggerType = PydanticField(
        default=HandoverTriggerType.MANUAL, description="觸發類型"
    )


class ManualHandoverResponse(BaseModel):
    """手動換手響應"""

    handover_id: int = PydanticField(description="換手請求 ID")
    ue_id: int = PydanticField(description="UE 設備 ID")
    from_satellite_id: str = PydanticField(description="源衛星 ID")
    to_satellite_id: str = PydanticField(description="目標衛星 ID")

    status: HandoverStatus = PydanticField(description="當前狀態")
    request_time: datetime = PydanticField(description="請求時間")

    # 執行結果 (異步更新)
    start_time: Optional[datetime] = PydanticField(default=None, description="開始時間")
    completion_time: Optional[datetime] = PydanticField(
        default=None, description="完成時間"
    )
    success: Optional[bool] = PydanticField(default=None, description="是否成功")
    error_message: Optional[str] = PydanticField(default=None, description="錯誤訊息")


class HandoverStatusResponse(BaseModel):
    """換手狀態查詢響應"""

    handover_id: int = PydanticField(description="換手請求 ID")
    status: HandoverStatus = PydanticField(description="當前狀態")
    progress_percentage: Optional[float] = PydanticField(
        default=None, description="進度百分比 (0-100)"
    )
    estimated_completion_time: Optional[datetime] = PydanticField(
        default=None, description="預計完成時間"
    )


class HandoverLatencyBreakdownRequest(BaseModel):
    """換手延遲分解分析請求"""
    
    algorithm_type: str = PydanticField(description="算法類型 (ntn_standard, ntn_gs, ntn_smn, proposed)")
    scenario: Optional[str] = PydanticField(default=None, description="測試場景")
    ue_mobility_pattern: Optional[str] = PydanticField(default="normal", description="UE 移動模式")
    satellite_constellation: Optional[str] = PydanticField(default="starlink", description="衛星星座")


class HandoverLatencyComponent(BaseModel):
    """換手延遲組件"""
    
    component_name: str = PydanticField(description="組件名稱")
    latency_ms: float = PydanticField(description="延遲時間 (毫秒)")
    description: str = PydanticField(description="組件描述")


class HandoverLatencyBreakdownResponse(BaseModel):
    """換手延遲分解分析響應"""
    
    algorithm_type: str = PydanticField(description="算法類型")
    total_latency_ms: float = PydanticField(description="總延遲 (毫秒)")
    
    # 五個主要階段的延遲分解
    preparation_latency: float = PydanticField(description="準備階段延遲 (ms)")
    rrc_reconfiguration_latency: float = PydanticField(description="RRC 重配延遲 (ms)")
    random_access_latency: float = PydanticField(description="隨機存取延遲 (ms)")
    ue_context_latency: float = PydanticField(description="UE 上下文延遲 (ms)")
    path_switch_latency: float = PydanticField(description="Path Switch 延遲 (ms)")
    
    # 詳細組件分解
    components: List[HandoverLatencyComponent] = PydanticField(description="詳細組件列表")
    
    # 計算相關信息
    calculation_time: datetime = PydanticField(description="計算時間")
    confidence_level: float = PydanticField(description="計算置信度 (0-1)")
    measurement_count: int = PydanticField(description="測量次數")


class MultiAlgorithmLatencyComparisonRequest(BaseModel):
    """多算法延遲對比請求"""
    
    algorithms: List[str] = PydanticField(
        default=["ntn_standard", "ntn_gs", "ntn_smn", "proposed"],
        description="要對比的算法列表"
    )
    scenario: Optional[str] = PydanticField(default=None, description="測試場景")
    measurement_iterations: int = PydanticField(default=100, description="測量迭代次數")


class MultiAlgorithmLatencyComparisonResponse(BaseModel):
    """多算法延遲對比響應"""
    
    algorithms: Dict[str, HandoverLatencyBreakdownResponse] = PydanticField(
        description="各算法的延遲分解結果"
    )
    comparison_summary: Dict[str, Any] = PydanticField(description="對比摘要")
    measurement_metadata: Dict[str, Any] = PydanticField(description="測量元數據")


class SixScenarioComparisonRequest(BaseModel):
    """六場景換手延遲對比請求"""
    
    algorithms: List[str] = PydanticField(
        default=["ntn_standard", "ntn_gs", "ntn_smn", "proposed"],
        description="要對比的算法列表"
    )
    scenarios: List[str] = PydanticField(
        default=[
            "starlink_flexible_unidirectional",
            "starlink_flexible_omnidirectional", 
            "starlink_consistent_unidirectional",
            "starlink_consistent_omnidirectional",
            "kuiper_flexible_unidirectional",
            "kuiper_flexible_omnidirectional",
            "kuiper_consistent_unidirectional",
            "kuiper_consistent_omnidirectional"
        ],
        description="六場景列表"
    )
    measurement_iterations: int = PydanticField(default=100, description="測量迭代次數")


class ScenarioLatencyData(BaseModel):
    """場景延遲數據"""
    
    scenario_name: str = PydanticField(description="場景名稱")
    scenario_label: str = PydanticField(description="場景簡寫標籤")
    constellation: str = PydanticField(description="衛星星座")
    strategy: str = PydanticField(description="策略類型")
    direction: str = PydanticField(description="方向類型")
    latency_ms: float = PydanticField(description="延遲時間 (毫秒)")
    confidence_interval: List[float] = PydanticField(description="置信區間 [lower, upper]")


class SixScenarioComparisonResponse(BaseModel):
    """六場景換手延遲對比響應"""
    
    scenario_results: Dict[str, Dict[str, ScenarioLatencyData]] = PydanticField(
        description="場景結果: {algorithm: {scenario: data}}"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    performance_summary: Dict[str, Any] = PydanticField(description="性能摘要")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")


class StrategyEffectRequest(BaseModel):
    """即時策略效果比較請求"""
    
    strategy_type: str = PydanticField(description="策略類型 (flexible, consistent)")
    measurement_duration_minutes: int = PydanticField(default=5, description="測量持續時間 (分鐘)")
    sample_interval_seconds: int = PydanticField(default=30, description="取樣間隔 (秒)")


class StrategyMetrics(BaseModel):
    """策略指標"""
    
    handover_frequency: float = PydanticField(description="換手頻率 (次/小時)")
    average_latency: float = PydanticField(description="平均延遲 (ms)")
    cpu_usage: float = PydanticField(description="CPU 使用率 (%)")
    accuracy: float = PydanticField(description="預測準確率 (%)")
    success_rate: float = PydanticField(description="換手成功率 (%)")
    signaling_overhead: float = PydanticField(description="信令開銷 (bytes/sec)")


class StrategyEffectResponse(BaseModel):
    """即時策略效果比較響應"""
    
    flexible: StrategyMetrics = PydanticField(description="Flexible 策略指標")
    consistent: StrategyMetrics = PydanticField(description="Consistent 策略指標")
    comparison_summary: Dict[str, Any] = PydanticField(description="策略對比摘要")
    measurement_metadata: Dict[str, Any] = PydanticField(description="測量元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class ComplexityAnalysisRequest(BaseModel):
    """複雜度對比分析請求"""
    
    ue_scales: List[int] = PydanticField(
        default=[1000, 5000, 10000, 20000, 50000],
        description="UE 規模列表"
    )
    algorithms: List[str] = PydanticField(
        default=["ntn_standard", "proposed"],
        description="要對比的算法列表"
    )
    measurement_iterations: int = PydanticField(default=50, description="測量迭代次數")


class AlgorithmComplexityData(BaseModel):
    """算法複雜度數據"""
    
    algorithm_name: str = PydanticField(description="算法名稱")
    algorithm_label: str = PydanticField(description="算法顯示標籤")
    execution_times: List[float] = PydanticField(description="執行時間列表 (秒)")
    complexity_class: str = PydanticField(description="複雜度類別 (O(n), O(n²), etc.)")
    optimization_factor: float = PydanticField(description="優化因子")


class ComplexityAnalysisResponse(BaseModel):
    """複雜度對比分析響應"""
    
    ue_scales: List[int] = PydanticField(description="UE 規模列表")
    algorithms_data: Dict[str, AlgorithmComplexityData] = PydanticField(
        description="算法複雜度數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    performance_analysis: Dict[str, Any] = PydanticField(description="性能分析摘要")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class HandoverFailureRateRequest(BaseModel):
    """切換失敗率統計請求"""
    
    mobility_scenarios: List[str] = PydanticField(
        default=["stationary", "30kmh", "60kmh", "120kmh", "200kmh"],
        description="移動場景列表"
    )
    algorithms: List[str] = PydanticField(
        default=["ntn_standard", "proposed_flexible", "proposed_consistent"],
        description="要對比的算法列表"
    )
    measurement_duration_hours: int = PydanticField(default=24, description="測量持續時間 (小時)")
    ue_count: int = PydanticField(default=1000, description="測試 UE 數量")


class MobilityScenarioData(BaseModel):
    """移動場景失敗率數據"""
    
    scenario_name: str = PydanticField(description="場景名稱")
    scenario_label: str = PydanticField(description="場景顯示標籤")
    speed_kmh: int = PydanticField(description="移動速度 (km/h)")
    failure_rate_percent: float = PydanticField(description="失敗率 (%)")
    total_handovers: int = PydanticField(description="總換手次數")
    failed_handovers: int = PydanticField(description="失敗換手次數")
    confidence_interval: List[float] = PydanticField(description="置信區間 [lower, upper]")


class AlgorithmFailureData(BaseModel):
    """算法失敗率數據"""
    
    algorithm_name: str = PydanticField(description="算法名稱")
    algorithm_label: str = PydanticField(description="算法顯示標籤")
    scenario_data: Dict[str, MobilityScenarioData] = PydanticField(description="各場景數據")
    overall_performance: Dict[str, Any] = PydanticField(description="整體性能統計")


class HandoverFailureRateResponse(BaseModel):
    """切換失敗率統計響應"""
    
    mobility_scenarios: List[str] = PydanticField(description="移動場景列表")
    algorithms_data: Dict[str, AlgorithmFailureData] = PydanticField(
        description="算法失敗率數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    performance_comparison: Dict[str, Any] = PydanticField(description="性能對比分析")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class SystemResourceAllocationRequest(BaseModel):
    """系統架構資源分配請求"""
    
    measurement_duration_minutes: int = PydanticField(default=30, description="測量持續時間 (分鐘)")
    include_components: List[str] = PydanticField(
        default=["open5gs_core", "ueransim_gnb", "skyfield_calc", "mongodb", "sync_algorithm", "xn_coordination", "others"],
        description="要監控的系統組件列表"
    )


class ComponentResourceData(BaseModel):
    """組件資源數據"""
    
    component_name: str = PydanticField(description="組件名稱")
    component_label: str = PydanticField(description="組件顯示標籤")
    cpu_percentage: float = PydanticField(description="CPU使用率百分比")
    memory_mb: float = PydanticField(description="記憶體使用量 (MB)")
    network_io_mbps: float = PydanticField(description="網路I/O (Mbps)")
    disk_io_mbps: float = PydanticField(description="磁碟I/O (Mbps)")
    resource_percentage: float = PydanticField(description="整體資源占用百分比")


class SystemResourceAllocationResponse(BaseModel):
    """系統架構資源分配響應"""
    
    components_data: Dict[str, ComponentResourceData] = PydanticField(
        description="各組件資源數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    resource_summary: Dict[str, Any] = PydanticField(description="資源使用摘要")
    bottleneck_analysis: Dict[str, Any] = PydanticField(description="瓶頸分析")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class TimeSyncPrecisionRequest(BaseModel):
    """時間同步精度分析請求"""
    
    include_protocols: List[str] = PydanticField(
        default=["ntp", "ptpv2", "gps", "ntp_gps", "ptpv2_gps"],
        description="要分析的同步協議列表"
    )
    measurement_duration_minutes: int = PydanticField(default=60, description="測量持續時間 (分鐘)")
    satellite_count: Optional[int] = PydanticField(default=None, description="衛星數量 (影響GPS精度)")


class SyncProtocolData(BaseModel):
    """同步協議數據"""
    
    protocol_name: str = PydanticField(description="協議名稱")
    protocol_label: str = PydanticField(description="協議顯示標籤")
    precision_microseconds: float = PydanticField(description="同步精度 (微秒)")
    stability_factor: float = PydanticField(description="穩定性因子 (0-1)")
    network_dependency: float = PydanticField(description="網路依賴性 (0-1)")
    satellite_dependency: float = PydanticField(description="衛星依賴性 (0-1)")
    implementation_complexity: str = PydanticField(description="實現複雜度")


class TimeSyncPrecisionResponse(BaseModel):
    """時間同步精度分析響應"""
    
    protocols_data: Dict[str, SyncProtocolData] = PydanticField(
        description="各協議同步數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    precision_comparison: Dict[str, Any] = PydanticField(description="精度對比分析")
    recommendation: Dict[str, Any] = PydanticField(description="協議推薦")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class PerformanceRadarRequest(BaseModel):
    """性能雷達圖對比請求"""
    
    include_strategies: List[str] = PydanticField(
        default=["flexible", "consistent"],
        description="要對比的策略列表"
    )
    evaluation_duration_minutes: int = PydanticField(default=30, description="評估持續時間 (分鐘)")
    include_metrics: List[str] = PydanticField(
        default=["handover_latency", "handover_frequency", "energy_efficiency", "connection_stability", "qos_guarantee", "coverage_continuity"],
        description="要評估的性能指標"
    )


class StrategyPerformanceData(BaseModel):
    """策略性能數據"""
    
    strategy_name: str = PydanticField(description="策略名稱")
    strategy_label: str = PydanticField(description="策略顯示標籤")
    handover_latency_score: float = PydanticField(description="換手延遲評分 (0-5)")
    handover_frequency_score: float = PydanticField(description="換手頻率評分 (0-5)")
    energy_efficiency_score: float = PydanticField(description="能耗效率評分 (0-5)")
    connection_stability_score: float = PydanticField(description="連接穩定性評分 (0-5)")
    qos_guarantee_score: float = PydanticField(description="QoS保證評分 (0-5)")
    coverage_continuity_score: float = PydanticField(description="覆蓋連續性評分 (0-5)")
    overall_score: float = PydanticField(description="綜合評分")


class PerformanceRadarResponse(BaseModel):
    """性能雷達圖對比響應"""
    
    strategies_data: Dict[str, StrategyPerformanceData] = PydanticField(
        description="各策略性能數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="雷達圖表數據結構")
    performance_comparison: Dict[str, Any] = PydanticField(description="性能對比分析")
    strategy_recommendation: Dict[str, Any] = PydanticField(description="策略推薦")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class ProtocolStackDelayRequest(BaseModel):
    """協議棧延遲分析請求"""
    
    include_layers: List[str] = PydanticField(
        default=["phy", "mac", "rlc", "pdcp", "rrc", "nas", "gtp_u"],
        description="要分析的協議層列表"
    )
    algorithm_type: str = PydanticField(default="proposed", description="算法類型")
    measurement_duration_minutes: int = PydanticField(default=30, description="測量持續時間 (分鐘)")


class ProtocolLayerData(BaseModel):
    """協議層數據"""
    
    layer_name: str = PydanticField(description="協議層名稱")
    layer_label: str = PydanticField(description="協議層顯示標籤")
    delay_ms: float = PydanticField(description="延遲時間 (毫秒)")
    delay_percentage: float = PydanticField(description="延遲占比 (%)")
    optimization_potential: float = PydanticField(description="優化潛力 (0-1)")
    description: str = PydanticField(description="層級描述")


class ProtocolStackDelayResponse(BaseModel):
    """協議棧延遲分析響應"""
    
    layers_data: Dict[str, ProtocolLayerData] = PydanticField(
        description="各協議層數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    total_delay_ms: float = PydanticField(description="總延遲 (毫秒)")
    optimization_analysis: Dict[str, Any] = PydanticField(description="優化分析")
    bottleneck_analysis: Dict[str, Any] = PydanticField(description="瓶頸分析")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class ExceptionHandlingStatisticsRequest(BaseModel):
    """異常處理統計請求"""
    
    analysis_duration_hours: int = PydanticField(default=24, description="分析持續時間 (小時)")
    include_categories: List[str] = PydanticField(
        default=["prediction_error", "connection_timeout", "signaling_failure", "resource_shortage", "tle_expired", "others"],
        description="要分析的異常類別列表"
    )
    severity_filter: Optional[str] = PydanticField(default=None, description="嚴重性過濾 (low, medium, high)")


class ExceptionCategoryData(BaseModel):
    """異常類別數據"""
    
    category_name: str = PydanticField(description="異常類別名稱")
    category_label: str = PydanticField(description="異常類別顯示標籤")
    occurrence_count: int = PydanticField(description="發生次數")
    occurrence_percentage: float = PydanticField(description="發生比例 (%)")
    severity_distribution: Dict[str, int] = PydanticField(description="嚴重性分布")
    recent_trend: str = PydanticField(description="最近趨勢 (increasing, decreasing, stable)")
    impact_description: str = PydanticField(description="影響描述")


class ExceptionHandlingStatisticsResponse(BaseModel):
    """異常處理統計響應"""
    
    categories_data: Dict[str, ExceptionCategoryData] = PydanticField(
        description="各異常類別數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    total_exceptions: int = PydanticField(description="總異常次數")
    most_common_exception: str = PydanticField(description="最常見異常")
    system_stability_score: float = PydanticField(description="系統穩定性評分 (0-100)")
    trend_analysis: Dict[str, Any] = PydanticField(description="趨勢分析")
    recommendations: List[str] = PydanticField(description="改善建議")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class QoETimeSeriesRequest(BaseModel):
    """QoE時間序列分析請求"""
    
    measurement_duration_seconds: int = PydanticField(default=60, description="測量持續時間 (秒)")
    sample_interval_seconds: int = PydanticField(default=1, description="取樣間隔 (秒)")
    include_metrics: List[str] = PydanticField(
        default=["stalling_time", "ping_rtt", "packet_loss", "throughput"],
        description="要分析的QoE指標列表"
    )
    uav_filter: Optional[str] = PydanticField(default=None, description="UAV過濾條件")


class QoETimeSeriesMetric(BaseModel):
    """QoE時間序列指標"""
    
    metric_name: str = PydanticField(description="指標名稱")
    metric_label: str = PydanticField(description="指標顯示標籤")
    unit: str = PydanticField(description="單位")
    values: List[float] = PydanticField(description="時間序列數值")
    average: float = PydanticField(description="平均值")
    improvement_percentage: float = PydanticField(description="相比基準的改善百分比")
    quality_level: str = PydanticField(description="品質等級 (excellent, good, acceptable, poor)")


class QoETimeSeriesResponse(BaseModel):
    """QoE時間序列分析響應"""
    
    metrics_data: Dict[str, QoETimeSeriesMetric] = PydanticField(
        description="各QoE指標數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    overall_qoe_score: float = PydanticField(description="整體QoE評分 (0-100)")
    performance_summary: Dict[str, Any] = PydanticField(description="性能摘要")
    user_experience_level: str = PydanticField(description="用戶體驗等級")
    comparison_baseline: Dict[str, Any] = PydanticField(description="與基準的對比")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")


class GlobalCoverageRequest(BaseModel):
    """全球覆蓋率統計請求"""
    
    include_constellations: List[str] = PydanticField(
        default=["starlink", "kuiper", "oneweb"],
        description="要分析的衛星星座列表"
    )
    latitude_bands: List[str] = PydanticField(
        default=["polar_90_60", "high_60_45", "mid_45_30", "low_30_15", "equatorial_15_0", "southern_0_-30", "antarctic_-60_-90"],
        description="緯度帶列表"
    )
    coverage_threshold_db: float = PydanticField(default=-120.0, description="覆蓋閾值 (dB)")
    calculation_resolution: int = PydanticField(default=100, description="計算解析度 (km)")


class LatitudeBandCoverage(BaseModel):
    """緯度帶覆蓋數據"""
    
    band_name: str = PydanticField(description="緯度帶名稱")
    band_label: str = PydanticField(description="緯度帶顯示標籤")
    latitude_range: List[float] = PydanticField(description="緯度範圍 [min, max]")
    coverage_percentage: float = PydanticField(description="覆蓋百分比")
    visible_satellites_avg: float = PydanticField(description="平均可見衛星數量")
    signal_strength_avg: float = PydanticField(description="平均信號強度 (dB)")
    availability_99_percent: float = PydanticField(description="99%可用性覆蓋率")


class ConstellationCoverage(BaseModel):
    """星座覆蓋數據"""
    
    constellation_name: str = PydanticField(description="星座名稱")
    constellation_label: str = PydanticField(description="星座顯示標籤")
    total_satellites: int = PydanticField(description="總衛星數量")
    orbital_altitude_km: float = PydanticField(description="軌道高度 (km)")
    latitude_bands: Dict[str, LatitudeBandCoverage] = PydanticField(description="各緯度帶覆蓋")
    global_coverage_avg: float = PydanticField(description="全球平均覆蓋率")
    coverage_uniformity: float = PydanticField(description="覆蓋均勻性 (0-1)")


class GlobalCoverageResponse(BaseModel):
    """全球覆蓋率統計響應"""
    
    constellations_data: Dict[str, ConstellationCoverage] = PydanticField(
        description="各星座覆蓋數據"
    )
    chart_data: Dict[str, Any] = PydanticField(description="圖表數據結構")
    coverage_comparison: Dict[str, Any] = PydanticField(description="覆蓋率對比分析")
    optimal_constellation: str = PydanticField(description="最優星座")
    coverage_insights: List[str] = PydanticField(description="覆蓋分析洞察")
    calculation_metadata: Dict[str, Any] = PydanticField(description="計算元數據")
    calculation_time: datetime = PydanticField(description="計算時間")
