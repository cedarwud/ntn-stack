"""
Performance Data Aggregator Service

This service aggregates performance data from multiple sources and components.
Creates comprehensive performance reports and analytics.
Part of Phase 3 service layer refactoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import statistics
from collections import defaultdict

from ..interfaces import PerformanceAggregatorInterface, PerformanceMonitorInterface
from ..models.performance_models import (
    AggregatedPerformanceData,
    PerformanceReport,
    PerformanceMetric,
    SystemResourceMetrics,
    AlgorithmMetrics,
    OptimizationResult,
    PerformanceTrendData,
    PerformanceOptimizationSuggestion,
    NetStackIntegrationMetrics,
    PerformanceCategory
)
from .simworld_optimizer import SimWorldOptimizer
from .algorithm_calculator import AlgorithmCalculator

logger = logging.getLogger(__name__)


class PerformanceAggregator(PerformanceAggregatorInterface, PerformanceMonitorInterface):
    """
    Aggregates performance data from multiple sources
    
    Responsibilities:
    - Collect metrics from all components
    - Generate comprehensive reports
    - Analyze performance trends
    - Provide consolidated insights
    """
    
    def __init__(self):
        self.simworld_optimizer = SimWorldOptimizer()
        self.algorithm_calculator = AlgorithmCalculator()
        
        # Data storage for aggregation
        self.metrics_history: List[PerformanceMetric] = []
        self.system_metrics_history: List[SystemResourceMetrics] = []
        self.algorithm_metrics_history: Dict[str, List[AlgorithmMetrics]] = defaultdict(list)
        self.optimization_history: List[OptimizationResult] = []
        
        # Configuration
        self.retention_days = 30
        self.report_components = [
            "simulation_engine",
            "websocket_handler", 
            "data_processor",
            "rendering_engine",
            "api_server"
        ]
    
    async def aggregate_performance_data(
        self,
        time_window: timedelta,
        components: Optional[List[str]] = None
    ) -> AggregatedPerformanceData:
        """Aggregate performance data across components"""
        logger.info(f"Aggregating performance data for {time_window}")
        
        if components is None:
            components = self.report_components
        
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        # Collect current system metrics
        system_metrics = await self.simworld_optimizer.get_system_metrics()
        
        # Collect algorithm performance
        algorithm_performance = {}
        algorithms = ["ntn", "ntn-gs", "ntn-smn", "proposed"]
        
        try:
            algorithm_comparison = await self.algorithm_calculator.compare_algorithms(
                algorithms, ["latency", "success_rate", "throughput"]
            )
            algorithm_performance = algorithm_comparison
        except Exception as e:
            logger.error(f"Error collecting algorithm performance: {e}")
        
        # Get optimization history
        optimization_history = await self.simworld_optimizer.get_optimization_history()
        
        # Simulate NetStack integration metrics
        netstack_metrics = await self._get_netstack_integration_metrics()
        
        # Calculate overall health score
        health_score = await self._calculate_health_score(
            system_metrics, algorithm_performance, optimization_history
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            system_metrics, algorithm_performance
        )
        
        return AggregatedPerformanceData(
            time_window_start=start_time,
            time_window_end=end_time,
            algorithm_performance=algorithm_performance,
            system_performance=system_metrics,
            optimization_impact=optimization_history,
            integration_health=netstack_metrics,
            overall_health_score=health_score,
            recommendations=recommendations
        )
    
    async def generate_performance_report(
        self,
        time_period: str,
        include_trends: bool = True
    ) -> PerformanceReport:
        """Generate comprehensive performance analysis report"""
        logger.info(f"Generating performance report for period: {time_period}")
        
        # Parse time period
        if time_period == "last_hour":
            time_window = timedelta(hours=1)
        elif time_period == "last_day":
            time_window = timedelta(days=1)
        elif time_period == "last_week":
            time_window = timedelta(weeks=1)
        else:
            time_window = timedelta(hours=24)  # Default to 24 hours
        
        report_id = f"perf_report_{int(datetime.utcnow().timestamp())}"
        
        # Collect aggregated data
        aggregated_data = await self.aggregate_performance_data(time_window)
        
        # Generate trends if requested
        trends = []
        if include_trends:
            trends = await self._generate_performance_trends(time_window)
        
        # Get optimization suggestions
        suggestions = await self.simworld_optimizer.suggest_optimizations(aggregated_data)
        
        # Calculate overall score
        overall_score = aggregated_data.overall_health_score
        
        # Build algorithm metrics list
        algorithm_metrics = []
        for alg_name, metrics in aggregated_data.algorithm_performance.items():
            algorithm_metrics.append(metrics)
        
        # Create report summary
        summary = {
            "report_period": time_period,
            "overall_health": "good" if overall_score > 80 else "fair" if overall_score > 60 else "poor",
            "total_algorithms_tested": len(algorithm_metrics),
            "system_cpu_avg": aggregated_data.system_performance.cpu_usage_percent,
            "system_memory_avg": aggregated_data.system_performance.memory_usage_mb,
            "optimization_count": len(aggregated_data.optimization_impact),
            "recommendations_count": len(suggestions)
        }
        
        return PerformanceReport(
            report_id=report_id,
            generation_time=datetime.utcnow(),
            time_period=time_period,
            overall_score=overall_score,
            algorithm_metrics=algorithm_metrics,
            system_metrics=[aggregated_data.system_performance],
            optimization_results=aggregated_data.optimization_impact,
            suggestions=suggestions,
            trends=trends,
            summary=summary
        )
    
    async def collect_metrics(
        self,
        component: str,
        time_window: Optional[timedelta] = None
    ) -> List[PerformanceMetric]:
        """Collect performance metrics for a component"""
        logger.info(f"Collecting metrics for component: {component}")
        
        if time_window is None:
            time_window = timedelta(hours=1)
        
        # Filter metrics by component and time window
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        component_metrics = [
            metric for metric in self.metrics_history
            if (metric.metadata.get("component") == component and
                start_time <= metric.timestamp <= end_time)
        ]
        
        # If no historical data, collect current metrics
        if not component_metrics:
            current_metric = await self._collect_current_component_metrics(component)
            if current_metric:
                component_metrics = [current_metric]
        
        return component_metrics
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        logger.info("Collecting real-time metrics")
        
        try:
            # System metrics
            system_metrics = await self.simworld_optimizer.get_system_metrics()
            
            # Algorithm metrics (cached)
            algorithm_status = {}
            for algorithm in ["proposed", "ntn"]:
                try:
                    metrics = await self.algorithm_calculator._generate_simulated_metrics(algorithm)
                    algorithm_status[algorithm] = {
                        "latency_ms": metrics.latency_ms,
                        "success_rate": metrics.success_rate_percent,
                        "status": "operational"
                    }
                except:
                    algorithm_status[algorithm] = {"status": "unavailable"}
            
            # Integration metrics
            integration_metrics = await self._get_netstack_integration_metrics()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_usage_percent": system_metrics.cpu_usage_percent,
                    "memory_usage_mb": system_metrics.memory_usage_mb,
                    "disk_usage_mb": system_metrics.disk_usage_mb,
                    "network_io_mbps": system_metrics.network_io_mbps
                },
                "algorithms": algorithm_status,
                "integration": {
                    "netstack_connection": integration_metrics.connection_latency_ms < 100,
                    "api_response_time_ms": integration_metrics.api_response_time_ms,
                    "sync_success_rate": integration_metrics.sync_success_rate
                },
                "application": {
                    "active_simulations": 2,  # Simulated
                    "websocket_connections": 5,  # Simulated
                    "requests_per_second": 12.5,  # Simulated
                    "error_rate_percent": 0.1  # Simulated
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting real-time metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "degraded"
            }
    
    # Private helper methods
    
    async def _get_netstack_integration_metrics(self) -> NetStackIntegrationMetrics:
        """Get NetStack integration performance metrics"""
        # Simulate NetStack integration metrics
        # In real implementation, this would connect to NetStack APIs
        return NetStackIntegrationMetrics(
            connection_latency_ms=15.4,
            data_sync_latency_ms=23.7,
            api_response_time_ms=45.2,
            sync_success_rate=94.8,
            last_sync_timestamp=datetime.utcnow() - timedelta(minutes=2),
            pending_operations=3
        )
    
    async def _calculate_health_score(
        self,
        system_metrics: SystemResourceMetrics,
        algorithm_performance: Dict[str, AlgorithmMetrics],
        optimization_history: List[OptimizationResult]
    ) -> float:
        """Calculate overall system health score (0-100)"""
        scores = []
        
        # System health score (40% weight)
        cpu_score = max(0, 100 - system_metrics.cpu_usage_percent)
        memory_score = max(0, 100 - (system_metrics.memory_usage_mb / 40))  # Assuming 4GB = 100%
        system_score = (cpu_score + memory_score) / 2
        scores.append(system_score * 0.4)
        
        # Algorithm performance score (40% weight)
        if algorithm_performance:
            algorithm_scores = []
            for metrics in algorithm_performance.values():
                # Higher success rate = better score
                success_score = metrics.success_rate_percent
                # Lower latency = better score
                latency_score = max(0, 100 - metrics.latency_ms / 2)
                algorithm_scores.append((success_score + latency_score) / 2)
            
            avg_algorithm_score = sum(algorithm_scores) / len(algorithm_scores)
            scores.append(avg_algorithm_score * 0.4)
        else:
            scores.append(70 * 0.4)  # Default if no algorithm data
        
        # Optimization effectiveness score (20% weight)
        if optimization_history:
            successful_optimizations = [opt for opt in optimization_history if opt.success]
            optimization_score = (len(successful_optimizations) / len(optimization_history)) * 100
            scores.append(optimization_score * 0.2)
        else:
            scores.append(80 * 0.2)  # Default if no optimization history
        
        return min(100, max(0, sum(scores)))
    
    async def _generate_recommendations(
        self,
        system_metrics: SystemResourceMetrics,
        algorithm_performance: Dict[str, AlgorithmMetrics]
    ) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # System-level recommendations
        if system_metrics.cpu_usage_percent > 80:
            recommendations.append("Consider optimizing CPU-intensive operations or scaling horizontally")
        
        if system_metrics.memory_usage_mb > 3000:  # Assuming 4GB limit
            recommendations.append("Memory usage is high, consider implementing caching strategies")
        
        # Algorithm-level recommendations
        if algorithm_performance:
            for alg_name, metrics in algorithm_performance.items():
                if metrics.latency_ms > 100:
                    recommendations.append(f"Algorithm {alg_name} latency is high, consider optimization")
                
                if metrics.success_rate_percent < 90:
                    recommendations.append(f"Algorithm {alg_name} success rate is below target")
        
        # General recommendations
        if not recommendations:
            recommendations.append("System performance is optimal")
        
        return recommendations
    
    async def _generate_performance_trends(
        self,
        time_window: timedelta
    ) -> List[PerformanceTrendData]:
        """Generate performance trend analysis"""
        trends = []
        
        # Generate simulated trend data for key metrics
        metrics_to_analyze = ["cpu_usage", "memory_usage", "algorithm_latency", "success_rate"]
        
        for metric_name in metrics_to_analyze:
            # Generate sample data points
            data_points = []
            hours = int(time_window.total_seconds() / 3600)
            
            for i in range(min(hours, 24)):  # Max 24 data points
                timestamp = datetime.utcnow() - timedelta(hours=hours - i)
                
                # Generate realistic trend values
                if metric_name == "cpu_usage":
                    value = 50 + (i * 2) % 30 + (i % 3) * 5  # Oscillating trend
                elif metric_name == "memory_usage":
                    value = 1500 + (i * 10) % 500  # Gradual increase
                elif metric_name == "algorithm_latency":
                    value = 100 - (i * 1.5)  # Improving trend
                else:  # success_rate
                    value = 90 + (i * 0.5) % 8  # Stable with variations
                
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 2)
                })
            
            # Analyze trend direction
            if len(data_points) >= 2:
                trend_direction = "improving" if data_points[-1]["value"] > data_points[0]["value"] else "declining"
                if abs(data_points[-1]["value"] - data_points[0]["value"]) < 2:
                    trend_direction = "stable"
            else:
                trend_direction = "stable"
            
            # Calculate statistics
            values = [point["value"] for point in data_points]
            
            trend = PerformanceTrendData(
                metric_name=metric_name,
                time_period_hours=hours,
                data_points=data_points,
                trend_direction=trend_direction,
                average_value=round(statistics.mean(values), 2),
                min_value=min(values),
                max_value=max(values),
                variance=round(statistics.variance(values) if len(values) > 1 else 0, 2)
            )
            
            trends.append(trend)
        
        return trends
    
    async def _collect_current_component_metrics(
        self,
        component: str
    ) -> Optional[PerformanceMetric]:
        """Collect current metrics for a specific component"""
        try:
            # Simulate component-specific metric collection
            system_metrics = await self.simworld_optimizer.get_system_metrics()
            
            # Map component to appropriate metric
            if component == "simulation_engine":
                value = system_metrics.cpu_usage_percent
                unit = "percent"
            elif component == "memory_management":
                value = system_metrics.memory_usage_mb
                unit = "MB"
            elif component == "websocket_handler":
                value = system_metrics.network_io_mbps
                unit = "Mbps"
            else:
                value = 50.0  # Default metric
                unit = "units"
            
            return PerformanceMetric(
                name=f"{component}_performance",
                value=value,
                unit=unit,
                timestamp=datetime.utcnow(),
                category=PerformanceCategory.SYSTEM,
                metadata={"component": component}
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {component}: {e}")
            return None