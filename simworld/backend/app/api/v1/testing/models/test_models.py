"""
測試相關的數據模型
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TestStatus(str, Enum):
    """測試狀態枚舉"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class HealthCategory(str, Enum):
    """健康檢查類別"""
    CONTAINER = "container"
    API = "api"
    DATABASE = "database"
    SATELLITE = "satellite"
    SYSTEM = "system"


class PriorityLevel(str, Enum):
    """優先級等級"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PerformanceMetrics(BaseModel):
    """性能指標模型"""
    avg_response_time: float = Field(..., description="平均響應時間 (ms)")
    throughput: int = Field(..., description="吞吐量 (req/s)")
    cpu_usage: float = Field(..., description="CPU 使用率 (%)")
    memory_usage: float = Field(..., description="記憶體使用率 (%)")
    network_latency: float = Field(..., description="網路延遲 (ms)")
    bandwidth_utilization: float = Field(..., description="頻寬使用率 (%)")
    error_rate: float = Field(..., description="錯誤率 (%)")
    concurrent_users: int = Field(..., description="併發用戶數")


class AlgorithmResults(BaseModel):
    """算法效能結果模型"""
    algorithm_efficiency: float = Field(..., description="算法效率 (%)")
    convergence_time: float = Field(..., description="收斂時間 (s)")
    resource_overhead: float = Field(..., description="資源開銷 (%)")
    scalability_score: float = Field(..., description="可擴展性評分")
    stability_index: float = Field(..., description="穩定性指數")


class TimeSeriesData(BaseModel):
    """時間序列數據模型"""
    timestamps: List[str] = Field(..., description="時間戳列表")
    response_times: List[float] = Field(..., description="響應時間序列")
    cpu_usage: List[float] = Field(..., description="CPU 使用率序列")
    memory_usage: List[float] = Field(..., description="記憶體使用率序列")
    throughput: List[int] = Field(..., description="吞吐量序列")


class ContainerHealth(BaseModel):
    """容器健康狀態模型"""
    total_containers: int = Field(..., description="總容器數")
    healthy_containers: int = Field(..., description="健康容器數")
    health_percentage: float = Field(..., description="健康百分比")
    container_status: Dict[str, TestStatus] = Field(..., description="各容器狀態")
    status: TestStatus = Field(..., description="整體狀態")


class ApiPerformance(BaseModel):
    """API 性能模型"""
    total_endpoints: int = Field(..., description="總端點數")
    healthy_endpoints: int = Field(..., description="健康端點數")
    avg_response_time_ms: float = Field(..., description="平均響應時間")
    status: TestStatus = Field(..., description="API 狀態")


class DatabasePerformance(BaseModel):
    """資料庫性能模型"""
    connection_status: str = Field(..., description="連接狀態")
    query_response_time_ms: float = Field(..., description="查詢響應時間")
    pool_size: int = Field(..., description="連接池大小")
    active_connections: int = Field(..., description="活躍連接數")
    idle_connections: int = Field(..., description="空閒連接數")
    status: TestStatus = Field(..., description="資料庫狀態")
    error: Optional[str] = Field(None, description="錯誤信息")


class SatelliteProcessing(BaseModel):
    """衛星處理模型"""
    skyfield_processing: bool = Field(..., description="Skyfield 處理狀態")
    orbit_calculation: bool = Field(..., description="軌道計算狀態")
    tle_data_valid: bool = Field(..., description="TLE 數據有效性")
    prediction_accuracy: float = Field(..., description="預測準確性 (%)")
    processing_time_ms: float = Field(..., description="處理時間 (ms)")
    status: TestStatus = Field(..., description="衛星處理狀態")
    error: Optional[str] = Field(None, description="錯誤信息")


class SystemResourceMetrics(BaseModel):
    """系統資源指標模型"""
    usage_percent: float = Field(..., description="使用百分比")
    status: TestStatus = Field(..., description="資源狀態")


class CpuMetrics(SystemResourceMetrics):
    """CPU 指標模型"""
    core_count: int = Field(..., description="CPU 核心數")


class MemoryMetrics(SystemResourceMetrics):
    """記憶體指標模型"""
    total_gb: float = Field(..., description="總記憶體 (GB)")
    used_gb: float = Field(..., description="已用記憶體 (GB)")


class DiskMetrics(SystemResourceMetrics):
    """磁碟指標模型"""
    total_gb: float = Field(..., description="總磁碟空間 (GB)")
    used_gb: float = Field(..., description="已用磁碟空間 (GB)")


class NetworkMetrics(BaseModel):
    """網路指標模型"""
    bytes_sent: int = Field(..., description="發送字節數")
    bytes_recv: int = Field(..., description="接收字節數")
    packets_sent: int = Field(..., description="發送封包數")
    packets_recv: int = Field(..., description="接收封包數")
    status: TestStatus = Field(..., description="網路狀態")


class SystemMetrics(BaseModel):
    """系統指標模型"""
    cpu: CpuMetrics = Field(..., description="CPU 指標")
    memory: MemoryMetrics = Field(..., description="記憶體指標")
    disk: DiskMetrics = Field(..., description="磁碟指標")
    network: NetworkMetrics = Field(..., description="網路指標")
    error: Optional[str] = Field(None, description="錯誤信息")


class SystemRecommendation(BaseModel):
    """系統建議模型"""
    category: str = Field(..., description="建議類別")
    priority: PriorityLevel = Field(..., description="優先級")
    message: str = Field(..., description="建議信息")
    action: str = Field(..., description="建議操作")


class TestFrameworkConfig(BaseModel):
    """測試框架配置模型"""
    framework_id: str = Field(..., description="框架 ID")
    algorithm_complexity: str = Field(..., description="算法複雜度")
    base_response_time: float = Field(..., description="基礎響應時間")
    base_throughput: int = Field(..., description="基礎吞吐量")
    cpu_baseline: float = Field(..., description="CPU 基線")
    memory_baseline: float = Field(..., description="記憶體基線")
    execution_time: int = Field(..., description="執行時間 (秒)")


class ComprehensiveTestResult(BaseModel):
    """綜合測試結果模型"""
    timestamp: datetime = Field(default_factory=datetime.now, description="測試時間戳")
    overall_health: TestStatus = Field(..., description="整體健康狀態")
    health_score: float = Field(..., description="健康評分 (0-1)")
    
    # 各項檢查結果
    container_health: ContainerHealth = Field(..., description="容器健康狀態")
    api_performance: ApiPerformance = Field(..., description="API 性能")
    database_performance: DatabasePerformance = Field(..., description="資料庫性能")
    satellite_processing: SatelliteProcessing = Field(..., description="衛星處理")
    system_metrics: SystemMetrics = Field(..., description="系統指標")
    
    # 建議和分析
    recommendations: List[SystemRecommendation] = Field(..., description="系統建議")
    
    # 測試配置
    test_config: Optional[TestFrameworkConfig] = Field(None, description="測試配置")
    
    # 詳細結果（可選）
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="性能指標")
    algorithm_results: Optional[AlgorithmResults] = Field(None, description="算法結果")
    time_series_data: Optional[TimeSeriesData] = Field(None, description="時間序列數據")