"""
Performance Domain API

This module provides the unified API layer for the performance domain.
Part of Phase 3 service layer refactoring - consolidates performance endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..services.simworld_optimizer import SimWorldOptimizer
from ..services.algorithm_calculator import AlgorithmCalculator
from ..services.performance_aggregator import PerformanceAggregator
from ..models.performance_models import (
    AlgorithmComparisonRequest,
    AlgorithmComparisonResult,
    BenchmarkConfiguration,
    BenchmarkResult,
    PerformanceReport,
    OptimizationResult,
    SystemResourceMetrics,
    AggregatedPerformanceData,
    OptimizationType
)

logger = logging.getLogger(__name__)

# Create router for performance API
router = APIRouter(prefix="/performance", tags=["Performance"])

# Initialize services
simworld_optimizer = SimWorldOptimizer()
algorithm_calculator = AlgorithmCalculator()
performance_aggregator = PerformanceAggregator()


@router.get("/health", summary="Performance system health check")
async def get_performance_health():
    """Get overall performance system health status"""
    try:
        # Get current metrics
        real_time_metrics = await performance_aggregator.get_real_time_metrics()
        
        # Determine health status
        if "error" in real_time_metrics:
            status = "degraded"
        elif real_time_metrics.get("system", {}).get("cpu_usage_percent", 0) > 90:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "optimizer": "operational",
                "calculator": "operational", 
                "aggregator": "operational"
            },
            "metrics_summary": real_time_metrics
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics/real-time", summary="Get real-time performance metrics")
async def get_real_time_metrics():
    """Get current real-time performance metrics across all components"""
    try:
        metrics = await performance_aggregator.get_real_time_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/metrics/system", summary="Get system resource metrics")
async def get_system_metrics():
    """Get current system resource utilization"""
    try:
        metrics = await simworld_optimizer.get_system_metrics()
        return {
            "cpu_usage_percent": metrics.cpu_usage_percent,
            "memory_usage_mb": metrics.memory_usage_mb,
            "disk_usage_mb": metrics.disk_usage_mb,
            "network_io_mbps": metrics.network_io_mbps,
            "timestamp": metrics.timestamp.isoformat(),
            "component": metrics.component
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/algorithms/comparison", summary="Compare algorithm performance")
async def compare_algorithms(
    algorithms: str = Query(..., description="Comma-separated list of algorithms"),
    metrics: str = Query(default="latency,success_rate,throughput", description="Metrics to compare"),
    test_duration: int = Query(default=5, description="Test duration in minutes")
):
    """Compare performance of multiple algorithms"""
    try:
        algorithm_list = [alg.strip() for alg in algorithms.split(",")]
        metric_list = [metric.strip() for metric in metrics.split(",")]
        
        results = await algorithm_calculator.compare_algorithms(algorithm_list, metric_list)
        
        # Format results for API response
        comparison_data = {}
        for alg_name, metrics_data in results.items():
            comparison_data[alg_name] = {
                "latency_ms": metrics_data.latency_ms,
                "success_rate_percent": metrics_data.success_rate_percent,
                "packet_loss_percent": metrics_data.packet_loss_percent,
                "throughput_mbps": metrics_data.throughput_mbps,
                "timestamp": metrics_data.timestamp.isoformat(),
                "test_scenario": metrics_data.test_scenario
            }
        
        return {
            "comparison_id": f"comp_{int(datetime.utcnow().timestamp())}",
            "algorithms_tested": algorithm_list,
            "metrics_evaluated": metric_list,
            "test_duration_minutes": test_duration,
            "results": comparison_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Algorithm comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/algorithms/{algorithm_name}/performance", summary="Get specific algorithm performance")
async def get_algorithm_performance(
    algorithm_name: str,
    scenarios: str = Query(default="urban,rural", description="Test scenarios"),
    duration: int = Query(default=10, description="Test duration in minutes")
):
    """Get detailed performance metrics for a specific algorithm"""
    try:
        scenario_list = [scenario.strip() for scenario in scenarios.split(",")]
        
        metrics = await algorithm_calculator.measure_algorithm_performance(
            algorithm_name, scenario_list, duration
        )
        
        # Get additional calculated metrics
        additional_metrics = await algorithm_calculator.calculate_additional_metrics(
            algorithm_name, metrics
        )
        
        return {
            "algorithm_name": algorithm_name,
            "test_scenarios": scenario_list,
            "duration_minutes": duration,
            "performance_metrics": {
                "latency_ms": metrics.latency_ms,
                "success_rate_percent": metrics.success_rate_percent,
                "packet_loss_percent": metrics.packet_loss_percent,
                "throughput_mbps": metrics.throughput_mbps,
                "timestamp": metrics.timestamp.isoformat()
            },
            "additional_metrics": {
                "power_consumption_mw": additional_metrics.power_consumption_mw,
                "prediction_accuracy_percent": additional_metrics.prediction_accuracy_percent,
                "handover_frequency_per_hour": additional_metrics.handover_frequency_per_hour,
                "signal_quality_dbm": additional_metrics.signal_quality_dbm,
                "network_overhead_percent": additional_metrics.network_overhead_percent,
                "user_satisfaction_score": additional_metrics.user_satisfaction_score
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get algorithm performance: {e}")
        raise HTTPException(status_code=500, detail=f"Performance measurement failed: {str(e)}")


@router.post("/optimization/optimize", summary="Trigger component optimization")
async def optimize_component(
    component: str = Query(..., description="Component to optimize"),
    optimization_type: str = Query(..., description="Type of optimization"),
    background_tasks: BackgroundTasks = None
):
    """Trigger performance optimization for a specific component"""
    try:
        # Validate optimization type
        if optimization_type not in [opt.value for opt in OptimizationType]:
            raise HTTPException(status_code=400, detail=f"Invalid optimization type: {optimization_type}")
        
        result = await simworld_optimizer.optimize_component(component, optimization_type)
        
        return {
            "optimization_id": f"opt_{int(datetime.utcnow().timestamp())}",
            "component": component,
            "optimization_type": optimization_type,
            "result": {
                "success": result.success,
                "before_value": result.before_value,
                "after_value": result.after_value,
                "improvement_percent": result.improvement_percent,
                "timestamp": result.timestamp.isoformat(),
                "description": result.description
            }
        }
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/optimization/suggestions", summary="Get optimization suggestions")
async def get_optimization_suggestions():
    """Get performance optimization suggestions based on current metrics"""
    try:
        # Get current performance data
        aggregated_data = await performance_aggregator.aggregate_performance_data(
            timedelta(hours=1)
        )
        
        suggestions = await simworld_optimizer.suggest_optimizations(aggregated_data)
        
        suggestion_list = []
        for suggestion in suggestions:
            suggestion_list.append({
                "component": suggestion.component,
                "issue_description": suggestion.issue_description,
                "recommended_action": suggestion.recommended_action,
                "expected_improvement_percent": suggestion.expected_improvement_percent,
                "implementation_effort": suggestion.implementation_effort,
                "priority": suggestion.priority,
                "estimated_time_hours": suggestion.estimated_time_hours
            })
        
        return {
            "suggestions": suggestion_list,
            "total_suggestions": len(suggestion_list),
            "generated_at": datetime.utcnow().isoformat(),
            "based_on_data_from": aggregated_data.time_window_start.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/reports/generate", summary="Generate performance report")
async def generate_performance_report(
    time_period: str = Query(default="last_day", description="Time period for report"),
    include_trends: bool = Query(default=True, description="Include trend analysis")
):
    """Generate comprehensive performance analysis report"""
    try:
        report = await performance_aggregator.generate_performance_report(
            time_period, include_trends
        )
        
        # Format report for API response
        formatted_report = {
            "report_id": report.report_id,
            "generation_time": report.generation_time.isoformat(),
            "time_period": report.time_period,
            "overall_score": report.overall_score,
            "summary": report.summary,
            "algorithm_metrics": [
                {
                    "algorithm_name": metric.algorithm_name,
                    "latency_ms": metric.latency_ms,
                    "success_rate_percent": metric.success_rate_percent,
                    "throughput_mbps": metric.throughput_mbps,
                    "test_scenario": metric.test_scenario
                }
                for metric in report.algorithm_metrics
            ],
            "system_metrics": [
                {
                    "cpu_usage_percent": metric.cpu_usage_percent,
                    "memory_usage_mb": metric.memory_usage_mb,
                    "timestamp": metric.timestamp.isoformat()
                }
                for metric in report.system_metrics
            ],
            "optimization_results": [
                {
                    "optimization_type": result.optimization_type.value,
                    "improvement_percent": result.improvement_percent,
                    "success": result.success,
                    "description": result.description
                }
                for result in report.optimization_results
            ],
            "suggestions": [
                {
                    "component": suggestion.component,
                    "issue_description": suggestion.issue_description,
                    "recommended_action": suggestion.recommended_action,
                    "priority": suggestion.priority
                }
                for suggestion in report.suggestions
            ]
        }
        
        if include_trends:
            formatted_report["trends"] = [
                {
                    "metric_name": trend.metric_name,
                    "trend_direction": trend.trend_direction,
                    "average_value": trend.average_value,
                    "data_points": trend.data_points
                }
                for trend in report.trends
            ]
        
        return formatted_report
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/monitor/resource-usage", summary="Monitor resource usage over time")
async def monitor_resource_usage(
    duration_minutes: int = Query(default=5, description="Monitoring duration"),
    interval_seconds: int = Query(default=30, description="Sampling interval")
):
    """Monitor system resource usage over a specified time period"""
    try:
        if duration_minutes > 60:
            raise HTTPException(status_code=400, detail="Maximum monitoring duration is 60 minutes")
        
        metrics_history = await simworld_optimizer.monitor_resource_usage(
            duration_minutes, interval_seconds
        )
        
        formatted_history = []
        for metric in metrics_history:
            formatted_history.append({
                "timestamp": metric.timestamp.isoformat(),
                "cpu_usage_percent": metric.cpu_usage_percent,
                "memory_usage_mb": metric.memory_usage_mb,
                "disk_usage_mb": metric.disk_usage_mb,
                "network_io_mbps": metric.network_io_mbps
            })
        
        return {
            "monitoring_session_id": f"monitor_{int(datetime.utcnow().timestamp())}",
            "duration_minutes": duration_minutes,
            "interval_seconds": interval_seconds,
            "data_points_collected": len(formatted_history),
            "metrics_history": formatted_history
        }
        
    except Exception as e:
        logger.error(f"Resource monitoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")


@router.get("/aggregated", summary="Get aggregated performance data")
async def get_aggregated_performance_data(
    hours: int = Query(default=24, description="Time window in hours"),
    components: str = Query(default="", description="Comma-separated components to include")
):
    """Get aggregated performance data across components"""
    try:
        time_window = timedelta(hours=hours)
        component_list = None
        
        if components:
            component_list = [comp.strip() for comp in components.split(",")]
        
        aggregated_data = await performance_aggregator.aggregate_performance_data(
            time_window, component_list
        )
        
        return {
            "time_window": {
                "start": aggregated_data.time_window_start.isoformat(),
                "end": aggregated_data.time_window_end.isoformat(),
                "hours": hours
            },
            "overall_health_score": aggregated_data.overall_health_score,
            "algorithm_performance": {
                name: {
                    "latency_ms": metrics.latency_ms,
                    "success_rate_percent": metrics.success_rate_percent,
                    "throughput_mbps": metrics.throughput_mbps
                }
                for name, metrics in aggregated_data.algorithm_performance.items()
            },
            "system_performance": {
                "cpu_usage_percent": aggregated_data.system_performance.cpu_usage_percent,
                "memory_usage_mb": aggregated_data.system_performance.memory_usage_mb,
                "network_io_mbps": aggregated_data.system_performance.network_io_mbps
            },
            "integration_health": {
                "connection_latency_ms": aggregated_data.integration_health.connection_latency_ms,
                "api_response_time_ms": aggregated_data.integration_health.api_response_time_ms,
                "sync_success_rate": aggregated_data.integration_health.sync_success_rate
            },
            "recommendations": aggregated_data.recommendations,
            "optimization_count": len(aggregated_data.optimization_impact)
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregated data: {e}")
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")