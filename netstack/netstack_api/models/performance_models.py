#!/usr/bin/env python3
"""
性能優化相關的 Pydantic 模型
根據 TODO.md 第17項「系統性能優化」要求設計
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class OptimizationType(str, Enum):
    """優化類型枚舉"""

    AUTO = "auto"
    COMPREHENSIVE = "comprehensive"
    API_RESPONSE = "api_response"
    MEMORY = "memory"
    CPU = "cpu"
    DATABASE = "database"
    CACHE = "cache"
    NETWORK = "network"


class PerformanceMetricCategory(str, Enum):
    """性能指標類別枚舉"""

    API = "api"
    SYSTEM = "system"
    DATABASE = "database"
    CACHE = "cache"
    NETWORK = "network"


class PerformanceOptimizationRequest(BaseModel):
    """性能優化請求模型"""

    optimization_type: OptimizationType = Field(..., description="優化類型")
    force: bool = Field(default=False, description="是否強制執行優化")
    target_metrics: Optional[List[str]] = Field(
        default=None, description="目標優化指標列表"
    )
    timeout_seconds: Optional[int] = Field(
        default=300, description="優化超時時間（秒）"
    )

    class Config:
        schema_extra = {
            "example": {
                "optimization_type": "auto",
                "force": False,
                "target_metrics": ["api_response_time_ms", "cpu_usage_percent"],
                "timeout_seconds": 300,
            }
        }


class PerformanceMetric(BaseModel):
    """性能指標模型"""

    name: str = Field(..., description="指標名稱")
    value: float = Field(..., description="指標值")
    unit: str = Field(..., description="單位")
    category: str = Field(..., description="指標類別")
    timestamp: str = Field(..., description="時間戳")
    target: Optional[float] = Field(None, description="目標值")

    class Config:
        schema_extra = {
            "example": {
                "name": "api_response_time_ms",
                "value": 85.5,
                "unit": "ms",
                "category": "api",
                "timestamp": "2024-12-19T10:30:00Z",
                "target": 100.0,
            }
        }


class PerformanceMetricsResponse(BaseModel):
    """性能指標響應模型"""

    metrics: List[PerformanceMetric] = Field(..., description="指標列表")
    total_count: int = Field(..., description="指標總數")
    time_range_minutes: int = Field(..., description="時間範圍（分鐘）")
    category: Optional[str] = Field(None, description="指標類別過濾")

    class Config:
        schema_extra = {
            "example": {
                "metrics": [
                    {
                        "name": "api_response_time_ms",
                        "value": 85.5,
                        "unit": "ms",
                        "category": "api",
                        "timestamp": "2024-12-19T10:30:00Z",
                        "target": 100.0,
                    }
                ],
                "total_count": 1,
                "time_range_minutes": 10,
                "category": "api",
            }
        }


class OptimizationResult(BaseModel):
    """優化結果模型"""

    optimization_type: str = Field(..., description="優化類型")
    before_value: Optional[float] = Field(None, description="優化前數值")
    after_value: Optional[float] = Field(None, description="優化後數值")
    improvement_percent: Optional[float] = Field(None, description="改善百分比")
    success: bool = Field(..., description="是否成功")
    timestamp: str = Field(..., description="時間戳")
    techniques_applied: List[str] = Field(default=[], description="應用的技術")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細信息")

    class Config:
        schema_extra = {
            "example": {
                "optimization_type": "api_response",
                "before_value": 120.5,
                "after_value": 85.3,
                "improvement_percent": 29.2,
                "success": True,
                "timestamp": "2024-12-19T10:30:00Z",
                "techniques_applied": ["cache_warming", "garbage_collection"],
                "details": {"cache_hit_rate": 0.85},
            }
        }


class OptimizationResultResponse(BaseModel):
    """優化結果響應模型"""

    success: bool = Field(..., description="整體是否成功")
    optimization_type: str = Field(..., description="優化類型")
    timestamp: str = Field(..., description="執行時間戳")
    results: List[Dict[str, Any]] = Field(default=[], description="優化結果列表")
    summary: Dict[str, Any] = Field(default={}, description="執行摘要")
    message: str = Field(..., description="結果消息")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "optimization_type": "auto",
                "timestamp": "2024-12-19T10:30:00Z",
                "results": [
                    {
                        "optimization_type": "api_response",
                        "improvement_percent": 25.5,
                        "success": True,
                    }
                ],
                "summary": {"total_improvements": 3},
                "message": "自動優化完成，應用了 3 項優化",
            }
        }


class PerformanceTargetStatus(BaseModel):
    """性能目標狀態模型"""

    target: float = Field(..., description="目標值")
    current: float = Field(..., description="當前值")
    meets_target: bool = Field(..., description="是否達到目標")

    class Config:
        schema_extra = {
            "example": {"target": 100.0, "current": 85.5, "meets_target": True}
        }


class CurrentMetric(BaseModel):
    """當前指標模型"""

    value: float = Field(..., description="當前值")
    unit: str = Field(..., description="單位")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "value": 85.5,
                "unit": "ms",
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class PerformanceSummaryResponse(BaseModel):
    """性能摘要響應模型"""

    timestamp: Optional[str] = Field(None, description="摘要生成時間")
    total_optimizations: int = Field(0, description="總優化次數")
    successful_optimizations: int = Field(0, description="成功優化次數")
    current_metrics: Dict[str, CurrentMetric] = Field(
        default={}, description="當前指標"
    )
    targets_status: Dict[str, PerformanceTargetStatus] = Field(
        default={}, description="目標達成狀態"
    )
    status: str = Field(..., description="監控狀態")

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2024-12-19T10:30:00Z",
                "total_optimizations": 15,
                "successful_optimizations": 12,
                "current_metrics": {
                    "api_response_time_ms": {
                        "value": 85.5,
                        "unit": "ms",
                        "timestamp": "2024-12-19T10:30:00Z",
                    }
                },
                "targets_status": {
                    "api_response_time_ms": {
                        "target": 100.0,
                        "current": 85.5,
                        "meets_target": True,
                    }
                },
                "status": "active",
            }
        }


class SystemResourceMetric(BaseModel):
    """系統資源指標模型"""

    cpu_usage_percent: float = Field(..., description="CPU 使用率")
    memory_usage_percent: float = Field(..., description="內存使用率")
    memory_available_mb: float = Field(..., description="可用內存（MB）")
    disk_usage_percent: Optional[float] = Field(None, description="磁碟使用率")
    network_io_mbps: Optional[float] = Field(None, description="網絡IO（Mbps）")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "cpu_usage_percent": 65.5,
                "memory_usage_percent": 72.3,
                "memory_available_mb": 1024.5,
                "disk_usage_percent": 45.2,
                "network_io_mbps": 15.7,
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class APIPerformanceMetric(BaseModel):
    """API 性能指標模型"""

    endpoint: str = Field(..., description="API 端點")
    response_time_ms: float = Field(..., description="響應時間（毫秒）")
    request_count: int = Field(..., description="請求次數")
    error_count: int = Field(default=0, description="錯誤次數")
    success_rate: float = Field(..., description="成功率")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "endpoint": "/api/v1/uav",
                "response_time_ms": 85.5,
                "request_count": 150,
                "error_count": 2,
                "success_rate": 98.7,
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class CachePerformanceMetric(BaseModel):
    """緩存性能指標模型"""

    cache_type: str = Field(..., description="緩存類型")
    hit_rate: float = Field(..., description="命中率")
    miss_rate: float = Field(..., description="未命中率")
    total_operations: int = Field(..., description="總操作數")
    cache_size: int = Field(..., description="緩存大小")
    timestamp: str = Field(..., description="時間戳")

    class Config:
        schema_extra = {
            "example": {
                "cache_type": "redis",
                "hit_rate": 0.85,
                "miss_rate": 0.15,
                "total_operations": 1000,
                "cache_size": 256,
                "timestamp": "2024-12-19T10:30:00Z",
            }
        }


class PerformanceAlertLevel(str, Enum):
    """性能告警級別"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PerformanceAlert(BaseModel):
    """性能告警模型"""

    alert_id: str = Field(..., description="告警ID")
    level: PerformanceAlertLevel = Field(..., description="告警級別")
    metric_name: str = Field(..., description="指標名稱")
    current_value: float = Field(..., description="當前值")
    threshold_value: float = Field(..., description="閾值")
    message: str = Field(..., description="告警消息")
    timestamp: str = Field(..., description="告警時間")
    resolved: bool = Field(default=False, description="是否已解決")

    class Config:
        schema_extra = {
            "example": {
                "alert_id": "alert_001",
                "level": "warning",
                "metric_name": "api_response_time_ms",
                "current_value": 150.5,
                "threshold_value": 100.0,
                "message": "API 響應時間超過閾值",
                "timestamp": "2024-12-19T10:30:00Z",
                "resolved": False,
            }
        }


class PerformanceReport(BaseModel):
    """性能報告模型"""

    report_id: str = Field(..., description="報告ID")
    generated_at: str = Field(..., description="生成時間")
    time_range: Dict[str, str] = Field(..., description="時間範圍")
    summary: Dict[str, Any] = Field(..., description="總結")
    metrics: List[PerformanceMetric] = Field(..., description="指標數據")
    optimizations: List[OptimizationResult] = Field(..., description="優化結果")
    recommendations: List[str] = Field(default=[], description="建議")

    class Config:
        schema_extra = {
            "example": {
                "report_id": "report_20241219_001",
                "generated_at": "2024-12-19T10:30:00Z",
                "time_range": {
                    "start": "2024-12-19T09:30:00Z",
                    "end": "2024-12-19T10:30:00Z",
                },
                "summary": {"avg_response_time": 85.5, "total_optimizations": 3},
                "metrics": [],
                "optimizations": [],
                "recommendations": ["考慮增加API緩存", "優化數據庫查詢"],
            }
        }
