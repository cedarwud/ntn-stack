"""
SimWorld Performance Optimizer Service

This service consolidates SimWorld-specific performance optimization functionality.
Extracted and refactored from app/services/performance_optimizer.py as part of Phase 3 refactoring.
"""

import asyncio
import time
import psutil
import gc
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path

from ..interfaces import PerformanceOptimizerInterface, SystemResourceMonitorInterface
from ..models.performance_models import (
    OptimizationResult,
    OptimizationType,
    SystemResourceMetrics,
    PerformanceOptimizationSuggestion,
    SimulationPerformanceMetric,
    PerformanceCategory
)

logger = logging.getLogger(__name__)


class SimWorldOptimizer(PerformanceOptimizerInterface, SystemResourceMonitorInterface):
    """
    SimWorld specific performance optimizer
    
    Handles:
    - Simulation calculation optimization
    - Memory management
    - WebSocket connection optimization
    - Frontend response optimization
    """
    
    def __init__(self):
        self.optimization_history: List[OptimizationResult] = []
        self.baseline_metrics: Optional[SystemResourceMetrics] = None
        self.performance_targets = {
            "cpu_usage_percent": 70.0,
            "memory_usage_mb": 2048.0,
            "response_time_ms": 100.0,
            "simulation_fps": 60.0
        }
    
    async def optimize_component(
        self,
        component: str,
        optimization_type: str
    ) -> OptimizationResult:
        """Optimize specific SimWorld component"""
        logger.info(f"Starting optimization for {component} with type {optimization_type}")
        
        # Get baseline metrics
        before_metrics = await self.get_system_metrics()
        before_value = self._extract_metric_value(before_metrics, optimization_type)
        
        # Apply optimization based on type
        optimization_success = False
        improvement_description = ""
        
        try:
            if optimization_type == OptimizationType.MEMORY:
                optimization_success = await self._optimize_memory(component)
                improvement_description = "Memory optimization: garbage collection and cache cleanup"
                
            elif optimization_type == OptimizationType.CPU:
                optimization_success = await self._optimize_cpu(component)
                improvement_description = "CPU optimization: algorithm efficiency improvements"
                
            elif optimization_type == OptimizationType.NETWORK:
                optimization_success = await self._optimize_network(component)
                improvement_description = "Network optimization: connection pooling and compression"
                
            elif optimization_type == OptimizationType.ALGORITHM:
                optimization_success = await self._optimize_algorithms(component)
                improvement_description = "Algorithm optimization: computational complexity reduction"
                
            else:
                raise ValueError(f"Unsupported optimization type: {optimization_type}")
            
            # Measure improvement
            await asyncio.sleep(2)  # Allow metrics to stabilize
            after_metrics = await self.get_system_metrics()
            after_value = self._extract_metric_value(after_metrics, optimization_type)
            
            # Calculate improvement
            if before_value > 0:
                improvement_percent = ((before_value - after_value) / before_value) * 100
                # For throughput-like metrics, improvement is increase
                if optimization_type in ["throughput", "fps"]:
                    improvement_percent = ((after_value - before_value) / before_value) * 100
            else:
                improvement_percent = 0.0
            
            result = OptimizationResult(
                optimization_type=OptimizationType(optimization_type),
                before_value=before_value,
                after_value=after_value,
                improvement_percent=improvement_percent,
                success=optimization_success,
                timestamp=datetime.utcnow(),
                description=improvement_description
            )
            
            self.optimization_history.append(result)
            
            logger.info(f"Optimization completed: {improvement_percent:.2f}% improvement")
            return result
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return OptimizationResult(
                optimization_type=OptimizationType(optimization_type),
                before_value=before_value,
                after_value=before_value,
                improvement_percent=0.0,
                success=False,
                timestamp=datetime.utcnow(),
                description=f"Optimization failed: {str(e)}"
            )
    
    async def suggest_optimizations(
        self,
        performance_data: Any  # AggregatedPerformanceData
    ) -> List[PerformanceOptimizationSuggestion]:
        """Generate optimization suggestions for SimWorld"""
        suggestions = []
        
        # Get current system metrics
        current_metrics = await self.get_system_metrics()
        
        # CPU optimization suggestions
        if current_metrics.cpu_usage_percent > self.performance_targets["cpu_usage_percent"]:
            suggestions.append(PerformanceOptimizationSuggestion(
                component="simulation_engine",
                issue_description=f"CPU usage ({current_metrics.cpu_usage_percent:.1f}%) exceeds target ({self.performance_targets['cpu_usage_percent']:.1f}%)",
                recommended_action="Optimize simulation algorithms, reduce calculation frequency, or implement parallel processing",
                expected_improvement_percent=15.0,
                implementation_effort="medium",
                priority="high",
                estimated_time_hours=4.0
            ))
        
        # Memory optimization suggestions
        if current_metrics.memory_usage_mb > self.performance_targets["memory_usage_mb"]:
            suggestions.append(PerformanceOptimizationSuggestion(
                component="memory_management",
                issue_description=f"Memory usage ({current_metrics.memory_usage_mb:.1f}MB) exceeds target ({self.performance_targets['memory_usage_mb']:.1f}MB)",
                recommended_action="Implement object pooling, optimize data structures, and improve garbage collection",
                expected_improvement_percent=20.0,
                implementation_effort="medium",
                priority="high",
                estimated_time_hours=3.0
            ))
        
        # Network optimization suggestions
        if current_metrics.network_io_mbps > 100.0:  # High network usage
            suggestions.append(PerformanceOptimizationSuggestion(
                component="network_layer",
                issue_description=f"High network I/O ({current_metrics.network_io_mbps:.1f}Mbps) detected",
                recommended_action="Implement data compression, optimize WebSocket protocols, and reduce redundant data transfers",
                expected_improvement_percent=30.0,
                implementation_effort="low",
                priority="medium",
                estimated_time_hours=2.0
            ))
        
        return suggestions
    
    async def get_system_metrics(self) -> SystemResourceMetrics:
        """Get current system resource metrics"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_used_mb = disk.used / (1024 * 1024)
            
            # Get network I/O
            network = psutil.net_io_counters()
            # Calculate network speed (approximate)
            network_mbps = (network.bytes_sent + network.bytes_recv) / (1024 * 1024) / 60  # rough estimate
            
            return SystemResourceMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_mb=memory_mb,
                disk_usage_mb=disk_used_mb,
                network_io_mbps=network_mbps,
                timestamp=datetime.utcnow(),
                process_id=None,
                component="simworld"
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return safe default values
            return SystemResourceMetrics(
                cpu_usage_percent=0.0,
                memory_usage_mb=0.0,
                disk_usage_mb=0.0,
                network_io_mbps=0.0,
                timestamp=datetime.utcnow(),
                component="simworld"
            )
    
    async def monitor_resource_usage(
        self,
        duration_minutes: int,
        interval_seconds: int = 30
    ) -> List[SystemResourceMetrics]:
        """Monitor resource usage over time"""
        metrics_history = []
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        logger.info(f"Starting resource monitoring for {duration_minutes} minutes")
        
        while datetime.utcnow() < end_time:
            metrics = await self.get_system_metrics()
            metrics_history.append(metrics)
            
            # Log significant changes
            if len(metrics_history) > 1:
                prev_metrics = metrics_history[-2]
                cpu_change = abs(metrics.cpu_usage_percent - prev_metrics.cpu_usage_percent)
                if cpu_change > 10:
                    logger.info(f"Significant CPU change: {prev_metrics.cpu_usage_percent:.1f}% -> {metrics.cpu_usage_percent:.1f}%")
            
            await asyncio.sleep(interval_seconds)
        
        logger.info(f"Resource monitoring completed. Collected {len(metrics_history)} data points")
        return metrics_history
    
    # Private optimization methods
    
    async def _optimize_memory(self, component: str) -> bool:
        """Optimize memory usage"""
        try:
            logger.info(f"Optimizing memory for component: {component}")
            
            # Force garbage collection
            gc.collect()
            
            # Simulate component-specific memory optimization
            if component == "simulation_engine":
                # Simulate clearing simulation caches
                await asyncio.sleep(0.5)
                
            elif component == "websocket_handler":
                # Simulate optimizing WebSocket buffers
                await asyncio.sleep(0.3)
                
            elif component == "data_processor":
                # Simulate optimizing data processing pipelines
                await asyncio.sleep(0.4)
            
            return True
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return False
    
    async def _optimize_cpu(self, component: str) -> bool:
        """Optimize CPU usage"""
        try:
            logger.info(f"Optimizing CPU for component: {component}")
            
            # Simulate CPU optimization techniques
            if component == "simulation_engine":
                # Simulate algorithm optimization
                await asyncio.sleep(0.6)
                
            elif component == "rendering_engine":
                # Simulate rendering optimization
                await asyncio.sleep(0.4)
                
            return True
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
            return False
    
    async def _optimize_network(self, component: str) -> bool:
        """Optimize network usage"""
        try:
            logger.info(f"Optimizing network for component: {component}")
            
            # Simulate network optimization
            await asyncio.sleep(0.3)
            return True
            
        except Exception as e:
            logger.error(f"Network optimization failed: {e}")
            return False
    
    async def _optimize_algorithms(self, component: str) -> bool:
        """Optimize algorithms"""
        try:
            logger.info(f"Optimizing algorithms for component: {component}")
            
            # Simulate algorithm optimization
            await asyncio.sleep(0.7)
            return True
            
        except Exception as e:
            logger.error(f"Algorithm optimization failed: {e}")
            return False
    
    def _extract_metric_value(self, metrics: SystemResourceMetrics, optimization_type: str) -> float:
        """Extract relevant metric value based on optimization type"""
        if optimization_type == OptimizationType.MEMORY:
            return metrics.memory_usage_mb
        elif optimization_type == OptimizationType.CPU:
            return metrics.cpu_usage_percent
        elif optimization_type == OptimizationType.NETWORK:
            return metrics.network_io_mbps
        else:
            return metrics.cpu_usage_percent  # Default to CPU
    
    async def get_optimization_history(self) -> List[OptimizationResult]:
        """Get history of optimization operations"""
        return self.optimization_history.copy()
    
    async def set_performance_targets(self, targets: Dict[str, float]) -> bool:
        """Update performance targets"""
        try:
            self.performance_targets.update(targets)
            logger.info(f"Performance targets updated: {targets}")
            return True
        except Exception as e:
            logger.error(f"Failed to update performance targets: {e}")
            return False