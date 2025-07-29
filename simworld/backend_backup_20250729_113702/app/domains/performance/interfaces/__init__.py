"""
Performance Domain Interfaces

This module defines the interfaces for the performance domain,
following the dependency inversion principle of clean architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..models.performance_models import (
    PerformanceMetric,
    AlgorithmMetrics,
    OptimizationResult,
    SystemResourceMetrics,
    BenchmarkConfiguration,
    BenchmarkResult,
    PerformanceReport,
    AggregatedPerformanceData
)


class PerformanceMonitorInterface(ABC):
    """Interface for performance monitoring services"""
    
    @abstractmethod
    async def collect_metrics(
        self, 
        component: str,
        time_window: Optional[timedelta] = None
    ) -> List[PerformanceMetric]:
        """Collect performance metrics for a component"""
        pass
    
    @abstractmethod
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        pass


class AlgorithmPerformanceInterface(ABC):
    """Interface for algorithm performance measurement"""
    
    @abstractmethod
    async def measure_algorithm_performance(
        self,
        algorithm_name: str,
        test_scenarios: List[str],
        duration_minutes: int = 10
    ) -> AlgorithmMetrics:
        """Measure performance of a specific algorithm"""
        pass
    
    @abstractmethod
    async def compare_algorithms(
        self,
        algorithms: List[str],
        metrics: List[str]
    ) -> Dict[str, AlgorithmMetrics]:
        """Compare performance of multiple algorithms"""
        pass


class PerformanceOptimizerInterface(ABC):
    """Interface for performance optimization services"""
    
    @abstractmethod
    async def optimize_component(
        self,
        component: str,
        optimization_type: str
    ) -> OptimizationResult:
        """Optimize performance of a specific component"""
        pass
    
    @abstractmethod
    async def suggest_optimizations(
        self,
        performance_data: AggregatedPerformanceData
    ) -> List[str]:
        """Generate optimization suggestions based on performance data"""
        pass


class BenchmarkInterface(ABC):
    """Interface for benchmark testing services"""
    
    @abstractmethod
    async def run_benchmark(
        self,
        config: BenchmarkConfiguration
    ) -> BenchmarkResult:
        """Run a performance benchmark test"""
        pass
    
    @abstractmethod
    async def get_benchmark_status(
        self,
        benchmark_id: str
    ) -> Dict[str, Any]:
        """Get status of a running benchmark"""
        pass


class PerformanceAggregatorInterface(ABC):
    """Interface for performance data aggregation"""
    
    @abstractmethod
    async def aggregate_performance_data(
        self,
        time_window: timedelta,
        components: Optional[List[str]] = None
    ) -> AggregatedPerformanceData:
        """Aggregate performance data across components"""
        pass
    
    @abstractmethod
    async def generate_performance_report(
        self,
        time_period: str,
        include_trends: bool = True
    ) -> PerformanceReport:
        """Generate comprehensive performance report"""
        pass


class SystemResourceMonitorInterface(ABC):
    """Interface for system resource monitoring"""
    
    @abstractmethod
    async def get_system_metrics(self) -> SystemResourceMetrics:
        """Get current system resource metrics"""
        pass
    
    @abstractmethod
    async def monitor_resource_usage(
        self,
        duration_minutes: int,
        interval_seconds: int = 30
    ) -> List[SystemResourceMetrics]:
        """Monitor resource usage over time"""
        pass


class PerformanceStorageInterface(ABC):
    """Interface for performance data storage"""
    
    @abstractmethod
    async def store_metrics(
        self,
        metrics: List[PerformanceMetric]
    ) -> bool:
        """Store performance metrics"""
        pass
    
    @abstractmethod
    async def retrieve_metrics(
        self,
        component: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[PerformanceMetric]:
        """Retrieve stored performance metrics"""
        pass


class PerformanceNotificationInterface(ABC):
    """Interface for performance alerting and notifications"""
    
    @abstractmethod
    async def check_performance_thresholds(
        self,
        metrics: List[PerformanceMetric]
    ) -> List[str]:
        """Check if metrics exceed defined thresholds"""
        pass
    
    @abstractmethod
    async def send_performance_alert(
        self,
        alert_type: str,
        message: str,
        severity: str
    ) -> bool:
        """Send performance alert notification"""
        pass