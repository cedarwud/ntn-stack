#!/usr/bin/env python3
"""
SimWorld 性能優化相關的 Pydantic 模型
根據 TODO.md 第17項「系統性能優化」要求設計
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SimulationOptimizationType(str, Enum):
    """仿真優化類型枚舉"""

    SIONNA_COMPUTATION = "sionna_computation"
    UAV_POSITION_UPDATE = "uav_position_update"
    WIRELESS_CHANNEL_CALCULATION = "wireless_channel_calculation"
    SYSTEM_RESOURCES = "system_resources"
    COMPREHENSIVE = "comprehensive"


class SimulationType(str, Enum):
    """仿真類型枚舉"""

    SIONNA = "sionna"
    UAV = "uav"
    WIRELESS = "wireless"
    RENDERING = "rendering"
    GENERAL = "general"


class SimulationOptimizationRequest(BaseModel):
    """仿真優化請求模型"""

    optimization_type: SimulationOptimizationType = Field(
        ..., description="仿真優化類型"
    )
    simulation_parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="仿真參數配置"
    )
    force_optimization: bool = Field(default=False, description="是否強制執行優化")
    target_improvement_percent: Optional[float] = Field(
        default=None, description="目標改善百分比"
    )

    class Config:
        schema_extra = {
            "example": {
                "optimization_type": "sionna_computation",
                "simulation_parameters": {"frequency_ghz": 2.4, "antenna_count": 64},
                "force_optimization": False,
                "target_improvement_percent": 20.0,
            }
        }


class SimulationPerformanceMetric(BaseModel):
    """仿真性能指標模型"""

    name: str = Field(..., description="指標名稱")
    value: float = Field(..., description="指標值")
    unit: str = Field(..., description="單位")
    category: str = Field(..., description="指標類別")
    simulation_type: str = Field(..., description="仿真類型")
    timestamp: str = Field(..., description="時間戳")
    target: Optional[float] = Field(None, description="目標值")

    class Config:
        schema_extra = {
            "example": {
                "name": "sionna_computation_ms",
                "value": 250.5,
                "unit": "ms",
                "category": "simulation",
                "simulation_type": "sionna",
                "timestamp": "2024-12-19T10:30:00Z",
                "target": 1000.0,
            }
        }


class SimulationPerformanceResponse(BaseModel):
    """仿真性能響應模型"""

    simulation_metrics: List[SimulationPerformanceMetric] = Field(
        ..., description="仿真指標列表"
    )
    total_count: int = Field(..., description="指標總數")
    time_range_minutes: int = Field(..., description="時間範圍（分鐘）")
    simulation_type: Optional[str] = Field(None, description="仿真類型過濾")

    class Config:
        schema_extra = {
            "example": {
                "simulation_metrics": [
                    {
                        "name": "sionna_computation_ms",
                        "value": 250.5,
                        "unit": "ms",
                        "category": "simulation",
                        "simulation_type": "sionna",
                        "timestamp": "2024-12-19T10:30:00Z",
                        "target": 1000.0,
                    }
                ],
                "total_count": 1,
                "time_range_minutes": 10,
                "simulation_type": "sionna",
            }
        }


class SimulationOptimizationResult(BaseModel):
    """仿真優化結果模型"""

    optimization_type: str = Field(..., description="優化類型")
    before_value: float = Field(..., description="優化前數值")
    after_value: float = Field(..., description="優化後數值")
    improvement_percent: float = Field(..., description="改善百分比")
    success: bool = Field(..., description="是否成功")
    timestamp: str = Field(..., description="時間戳")
    techniques_applied: List[str] = Field(default=[], description="應用的技術")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細信息")

    class Config:
        schema_extra = {
            "example": {
                "optimization_type": "sionna_computation",
                "before_value": 350.2,
                "after_value": 250.5,
                "improvement_percent": 28.5,
                "success": True,
                "timestamp": "2024-12-19T10:30:00Z",
                "techniques_applied": ["result_caching", "parameter_optimization"],
                "details": {"cache_size": 15},
            }
        }


class CacheStatus(BaseModel):
    """緩存狀態模型"""

    total_cached_items: int = Field(..., description="總緩存項目數")
    cache_categories: Dict[str, int] = Field(..., description="各類別緩存數量")
    cache_details: Dict[str, Any] = Field(default={}, description="緩存詳細信息")

    class Config:
        schema_extra = {
            "example": {
                "total_cached_items": 45,
                "cache_categories": {
                    "channel_models": 15,
                    "uav_trajectories": 20,
                    "computed_results": 10,
                },
                "cache_details": {
                    "channel_models": {
                        "size": 15,
                        "recent_items": [
                            {
                                "key": "sionna_channel_model_default",
                                "last_updated": "2024-12-19T10:25:00Z",
                            }
                        ],
                    }
                },
            }
        }


class SimulationPerformanceSummary(BaseModel):
    """仿真性能摘要模型"""

    timestamp: str = Field(..., description="摘要生成時間")
    total_optimizations: int = Field(..., description="總優化次數")
    successful_optimizations: int = Field(..., description="成功優化次數")
    last_optimization: Optional[str] = Field(None, description="上次優化時間")
    current_metrics: Dict[str, Any] = Field(default={}, description="當前指標")
    performance_targets: Dict[str, float] = Field(default={}, description="性能目標")
    cache_status: CacheStatus = Field(..., description="緩存狀態")
    component: str = Field(default="simworld", description="組件名稱")
    optimization_capabilities: List[str] = Field(default=[], description="優化能力列表")

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2024-12-19T10:30:00Z",
                "total_optimizations": 8,
                "successful_optimizations": 7,
                "last_optimization": "2024-12-19T10:25:00Z",
                "current_metrics": {
                    "sionna_computation_ms": {
                        "current": 250.5,
                        "average": 275.2,
                        "unit": "ms",
                        "target": 1000.0,
                        "meets_target": True,
                    }
                },
                "performance_targets": {
                    "sionna_computation_ms": 1000.0,
                    "uav_position_update_ms": 100.0,
                },
                "cache_status": {
                    "total_cached_items": 45,
                    "cache_categories": {"channel_models": 15},
                },
                "component": "simworld",
                "optimization_capabilities": [
                    "sionna_computation",
                    "uav_position_update",
                ],
            }
        }


class SimulationBenchmarkResult(BaseModel):
    """仿真基準測試結果模型"""

    benchmark_results: Dict[str, float] = Field(..., description="基準測試結果")
    target_comparison: Dict[str, Any] = Field(..., description="與目標的比較")
    timestamp: str = Field(..., description="測試時間戳")
    summary: Dict[str, Any] = Field(..., description="結果摘要")
    message: str = Field(..., description="結果消息")

    class Config:
        schema_extra = {
            "example": {
                "benchmark_results": {
                    "sionna_computation_ms": 250.5,
                    "uav_position_update_ms": 85.2,
                    "wireless_channel_calc_ms": 180.7,
                    "simulation_fps": 28.5,
                },
                "target_comparison": {
                    "sionna_computation_ms": {
                        "current": 250.5,
                        "target": 1000.0,
                        "meets_target": True,
                        "deviation_percent": -74.95,
                    }
                },
                "timestamp": "2024-12-19T10:30:00Z",
                "summary": {
                    "total_metrics": 4,
                    "targets_met": 3,
                    "overall_performance": "good",
                },
                "message": "SimWorld 性能基準測試完成",
            }
        }


class SionnaComputationMetric(BaseModel):
    """Sionna 計算指標模型"""

    computation_time_ms: float = Field(..., description="計算時間（毫秒）")
    frequency_ghz: float = Field(..., description="頻率（GHz）")
    antenna_count: int = Field(..., description="天線數量")
    cache_hit: bool = Field(..., description="是否緩存命中")
    memory_usage_mb: float = Field(..., description="內存使用量（MB）")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "computation_time_ms": 250.5,
                "frequency_ghz": 2.4,
                "antenna_count": 64,
                "cache_hit": True,
                "memory_usage_mb": 128.5,
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class UAVPositionMetric(BaseModel):
    """UAV 位置更新指標模型"""

    update_time_ms: float = Field(..., description="更新時間（毫秒）")
    uav_count: int = Field(..., description="UAV 數量")
    trajectory_cache_hit_rate: float = Field(..., description="軌跡緩存命中率")
    position_accuracy_m: float = Field(..., description="位置精度（米）")
    batch_size: int = Field(..., description="批處理大小")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "update_time_ms": 85.2,
                "uav_count": 10,
                "trajectory_cache_hit_rate": 0.75,
                "position_accuracy_m": 0.5,
                "batch_size": 5,
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class WirelessChannelMetric(BaseModel):
    """無線通道計算指標模型"""

    calculation_time_ms: float = Field(..., description="計算時間（毫秒）")
    path_loss_db: float = Field(..., description="路徑損耗（dB）")
    distance_km: float = Field(..., description="距離（公里）")
    frequency_ghz: float = Field(..., description="頻率（GHz）")
    cache_hit: bool = Field(..., description="是否緩存命中")
    algorithm_type: str = Field(..., description="算法類型")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "calculation_time_ms": 180.7,
                "path_loss_db": 125.5,
                "distance_km": 5.2,
                "frequency_ghz": 12.0,
                "cache_hit": False,
                "algorithm_type": "free_space",
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class SimulationFrameRateMetric(BaseModel):
    """仿真幀率指標模型"""

    fps: float = Field(..., description="每秒幀數")
    frame_time_ms: float = Field(..., description="幀時間（毫秒）")
    dropped_frames: int = Field(..., description="丟幀數")
    cpu_usage_percent: float = Field(..., description="CPU 使用率")
    gpu_usage_percent: Optional[float] = Field(None, description="GPU 使用率")
    rendering_quality: str = Field(..., description="渲染質量")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "fps": 28.5,
                "frame_time_ms": 35.1,
                "dropped_frames": 2,
                "cpu_usage_percent": 65.2,
                "gpu_usage_percent": 45.8,
                "rendering_quality": "high",
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class OptimizationTechnique(str, Enum):
    """優化技術枚舉"""

    RESULT_CACHING = "result_caching"
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    MEMORY_CLEANUP = "memory_cleanup"
    TRAJECTORY_CACHING = "trajectory_caching"
    BATCH_PROCESSING = "batch_processing"
    VECTORIZED_COMPUTATION = "vectorized_computation"
    COMPUTATION_CACHING = "computation_caching"
    PRECOMPUTATION = "precomputation"
    ALGORITHM_OPTIMIZATION = "algorithm_optimization"
    GARBAGE_COLLECTION = "garbage_collection"
    CACHE_CLEANUP = "cache_cleanup"
    MEMORY_OPTIMIZATION = "memory_optimization"


class OptimizationReport(BaseModel):
    """優化報告模型"""

    report_id: str = Field(..., description="報告ID")
    generated_at: str = Field(..., description="生成時間")
    optimization_period: Dict[str, str] = Field(..., description="優化期間")
    optimizations_performed: List[SimulationOptimizationResult] = Field(
        ..., description="執行的優化"
    )
    performance_improvements: Dict[str, float] = Field(..., description="性能改善情況")
    recommendations: List[str] = Field(default=[], description="建議")
    next_optimization_schedule: Optional[str] = Field(
        None, description="下次優化計劃時間"
    )

    class Config:
        schema_extra = {
            "example": {
                "report_id": "opt_report_20241219_001",
                "generated_at": "2024-12-19T10:30:00Z",
                "optimization_period": {
                    "start": "2024-12-19T09:00:00Z",
                    "end": "2024-12-19T10:30:00Z",
                },
                "optimizations_performed": [],
                "performance_improvements": {
                    "sionna_computation_ms": 28.5,
                    "uav_position_update_ms": 15.2,
                },
                "recommendations": [
                    "增加 Sionna 計算緩存大小",
                    "實施更高效的 UAV 軌跡算法",
                ],
                "next_optimization_schedule": "2024-12-19T16:00:00Z",
            }
        }
