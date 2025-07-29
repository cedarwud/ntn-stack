"""
Unified Performance Models

This module defines all performance-related data models for the performance domain.
Consolidates models from multiple sources as part of Phase 3 service layer refactoring.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pydantic import BaseModel
from enum import Enum


class PerformanceCategory(str, Enum):
    """Performance metric categories"""
    SIMULATION = "simulation"
    ALGORITHM = "algorithm"
    SYSTEM = "system"
    NETWORK = "network"
    USER_EXPERIENCE = "user_experience"


class OptimizationType(str, Enum):
    """Types of optimizations"""
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    ALGORITHM = "algorithm"
    DATABASE = "database"


@dataclass
class PerformanceMetric:
    """Base performance metric data class"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: PerformanceCategory
    target: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationPerformanceMetric(PerformanceMetric):
    """Simulation-specific performance metric"""
    simulation_type: str = "general"
    simulation_id: Optional[str] = None
    particle_count: Optional[int] = None
    calculation_complexity: Optional[str] = None


@dataclass
class AlgorithmMetrics:
    """Algorithm performance metrics"""
    latency_ms: float
    success_rate_percent: float
    packet_loss_percent: float
    throughput_mbps: float
    timestamp: datetime
    algorithm_name: str
    test_scenario: str


@dataclass
class CalculatedMetrics:
    """Calculated additional performance metrics"""
    power_consumption_mw: float
    prediction_accuracy_percent: float
    handover_frequency_per_hour: float
    signal_quality_dbm: float
    network_overhead_percent: float
    user_satisfaction_score: float  # 1-5 scale


@dataclass
class LatencyBreakdown:
    """Detailed latency breakdown analysis"""
    preparation_ms: float
    rrc_reconfig_ms: float
    random_access_ms: float
    ue_context_ms: float
    path_switch_ms: float
    total_ms: float
    algorithm_name: str
    scenario: str


@dataclass
class OptimizationResult:
    """Optimization operation result"""
    optimization_type: OptimizationType
    before_value: float
    after_value: float
    improvement_percent: float
    success: bool
    timestamp: datetime
    description: str = ""
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SystemResourceMetrics:
    """System resource utilization metrics"""
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_usage_mb: float
    network_io_mbps: float
    timestamp: datetime
    process_id: Optional[int] = None
    component: str = "system"


class AlgorithmComparisonRequest(BaseModel):
    """Request model for algorithm comparison"""
    algorithms: List[str]
    metrics: List[str]
    test_scenarios: Optional[List[str]] = None
    duration_minutes: Optional[int] = 10


class AlgorithmComparisonResult(BaseModel):
    """Result model for algorithm comparison"""
    algorithm_name: str
    metrics: List[PerformanceMetric]
    success_rate: float
    avg_latency_ms: float
    throughput_mbps: Optional[float] = None
    test_duration_minutes: int
    scenarios_tested: int


class PerformanceTrendData(BaseModel):
    """Performance trend analysis data"""
    metric_name: str
    time_period_hours: int
    data_points: List[Dict[str, Union[str, float]]]
    trend_direction: str  # "improving", "declining", "stable"
    average_value: float
    min_value: float
    max_value: float
    variance: float


class BenchmarkConfiguration(BaseModel):
    """Benchmark test configuration"""
    test_name: str
    algorithms_to_test: List[str]
    duration_minutes: int
    concurrent_users: int
    test_scenarios: List[str]
    performance_targets: Dict[str, float]
    resource_limits: Optional[Dict[str, float]] = None


class BenchmarkResult(BaseModel):
    """Benchmark test result"""
    benchmark_id: str
    configuration: BenchmarkConfiguration
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str  # "running", "completed", "failed"
    results: Dict[str, AlgorithmComparisonResult]
    summary_metrics: Dict[str, float]
    resource_usage: List[SystemResourceMetrics]


@dataclass
class PerformanceOptimizationSuggestion:
    """Performance optimization suggestion"""
    component: str
    issue_description: str
    recommended_action: str
    expected_improvement_percent: float
    implementation_effort: str  # "low", "medium", "high"
    priority: str  # "low", "medium", "high", "critical"
    estimated_time_hours: float


@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report"""
    report_id: str
    generation_time: datetime
    time_period: str
    overall_score: float  # 0-100
    algorithm_metrics: List[AlgorithmMetrics]
    system_metrics: List[SystemResourceMetrics]
    optimization_results: List[OptimizationResult]
    suggestions: List[PerformanceOptimizationSuggestion]
    trends: List[PerformanceTrendData]
    summary: Dict[str, Any]


# Real-time metrics models
class RealTimeMetrics(BaseModel):
    """Real-time performance metrics"""
    timestamp: datetime
    system_metrics: Dict[str, float]
    application_metrics: Dict[str, float]
    simulation_metrics: Dict[str, float]
    active_connections: int
    requests_per_second: float
    avg_response_time_ms: float
    error_rate_percent: float


# Integration with NetStack models
class NetStackIntegrationMetrics(BaseModel):
    """Metrics for NetStack integration performance"""
    connection_latency_ms: float
    data_sync_latency_ms: float
    api_response_time_ms: float
    sync_success_rate: float
    last_sync_timestamp: datetime
    pending_operations: int


# Performance aggregation models
@dataclass
class AggregatedPerformanceData:
    """Aggregated performance data across all components"""
    time_window_start: datetime
    time_window_end: datetime
    algorithm_performance: Dict[str, AlgorithmMetrics]
    system_performance: SystemResourceMetrics
    optimization_impact: List[OptimizationResult]
    integration_health: NetStackIntegrationMetrics
    overall_health_score: float
    recommendations: List[str]


# Export all models
__all__ = [
    # Enums
    "PerformanceCategory",
    "OptimizationType",
    
    # Base models
    "PerformanceMetric",
    "SimulationPerformanceMetric",
    "AlgorithmMetrics",
    "CalculatedMetrics",
    "LatencyBreakdown",
    "OptimizationResult",
    "SystemResourceMetrics",
    
    # API models
    "AlgorithmComparisonRequest",
    "AlgorithmComparisonResult",
    "PerformanceTrendData",
    "BenchmarkConfiguration",
    "BenchmarkResult",
    "RealTimeMetrics",
    "NetStackIntegrationMetrics",
    
    # Analysis models
    "PerformanceOptimizationSuggestion",
    "PerformanceReport",
    "AggregatedPerformanceData",
]