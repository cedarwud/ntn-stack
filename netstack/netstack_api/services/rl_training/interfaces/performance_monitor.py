"""
🧠 性能監控接口

研究級性能監控系統，支援：
- 實時指標收集
- 統計分析
- 基準比較  
- 論文數據生成
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .rl_algorithm import ScenarioType


class MetricType(str, Enum):
    """指標類型"""
    REWARD = "reward"
    LATENCY = "latency"
    THROUGHPUT = "throughput" 
    SUCCESS_RATE = "success_rate"
    CONVERGENCE_TIME = "convergence_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    GPU_USAGE = "gpu_usage"
    HANDOVER_COUNT = "handover_count"
    PACKET_LOSS = "packet_loss"


class AggregationType(str, Enum):
    """聚合類型"""
    MEAN = "mean"
    MEDIAN = "median"
    STD = "std"
    MIN = "min"
    MAX = "max"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"
    COUNT = "count"
    SUM = "sum"


@dataclass
class PerformanceMetric:
    """性能指標"""
    metric_name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    algorithm_name: str
    scenario_type: ScenarioType
    session_id: Optional[str] = None
    episode_number: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StatisticalSummary:
    """統計摘要"""
    metric_type: MetricType
    count: int
    mean: float
    std: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_50: float  # median
    percentile_75: float
    percentile_95: float
    percentile_99: float
    confidence_interval_95: Tuple[float, float]


@dataclass
class BaselineComparison:
    """基準比較結果"""
    our_algorithm: str
    baseline_algorithm: str
    metric_type: MetricType
    our_performance: StatisticalSummary
    baseline_performance: StatisticalSummary
    improvement_percent: float
    statistical_significance: float  # p-value
    effect_size: float  # Cohen's d
    is_statistically_significant: bool
    comparison_notes: str


@dataclass
class ConvergenceAnalysis:
    """收斂性分析"""
    algorithm_name: str
    scenario_type: ScenarioType
    convergence_episode: Optional[int]
    convergence_threshold: float
    final_performance: float
    convergence_rate: float  # episodes per unit improvement
    stability_score: float  # variance in final episodes
    plateau_detection: bool


class IPerformanceMonitor(ABC):
    """性能監控核心接口
    
    提供研究級的性能監控和分析功能，
    支援學術論文數據生成和基準比較。
    """
    
    @abstractmethod
    async def record_metric(self, metric: PerformanceMetric) -> bool:
        """記錄性能指標
        
        Args:
            metric: 性能指標
            
        Returns:
            bool: 是否記錄成功
        """
        pass
    
    @abstractmethod
    async def record_metrics_batch(self, metrics: List[PerformanceMetric]) -> int:
        """批量記錄指標
        
        Args:
            metrics: 指標列表
            
        Returns:
            int: 成功記錄的指標數量
        """
        pass
    
    @abstractmethod
    async def get_performance_summary(
        self, 
        algorithm_name: str,
        metric_types: Optional[List[MetricType]] = None,
        scenario_type: Optional[ScenarioType] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[MetricType, StatisticalSummary]:
        """獲取性能摘要
        
        Args:
            algorithm_name: 算法名稱
            metric_types: 指標類型列表
            scenario_type: 場景類型
            time_range: 時間範圍
            
        Returns:
            Dict[MetricType, StatisticalSummary]: 統計摘要
        """
        pass
    
    @abstractmethod
    async def compare_with_baseline(
        self,
        our_algorithm: str,
        baseline_algorithm: str,
        metric_types: List[MetricType],
        scenario_type: Optional[ScenarioType] = None
    ) -> List[BaselineComparison]:
        """與基準算法比較
        
        Args:
            our_algorithm: 我們的算法
            baseline_algorithm: 基準算法  
            metric_types: 比較的指標類型
            scenario_type: 場景類型
            
        Returns:
            List[BaselineComparison]: 比較結果
        """
        pass
    
    @abstractmethod
    async def analyze_convergence(
        self,
        algorithm_name: str,
        session_ids: Optional[List[str]] = None,
        convergence_threshold: float = 0.95
    ) -> List[ConvergenceAnalysis]:
        """分析收斂性
        
        Args:
            algorithm_name: 算法名稱
            session_ids: 會話ID列表
            convergence_threshold: 收斂閾值
            
        Returns:
            List[ConvergenceAnalysis]: 收斂分析結果
        """
        pass
    
    @abstractmethod
    async def get_real_time_metrics(
        self,
        algorithm_name: str,
        time_window_minutes: int = 5
    ) -> Dict[MetricType, List[PerformanceMetric]]:
        """獲取實時指標
        
        Args:
            algorithm_name: 算法名稱
            time_window_minutes: 時間窗口（分鐘）
            
        Returns:
            Dict[MetricType, List[PerformanceMetric]]: 實時指標
        """
        pass
    
    @abstractmethod
    async def export_metrics_for_paper(
        self,
        algorithm_names: List[str],
        metric_types: List[MetricType],
        format_type: str = "csv",  # csv, json, latex
        include_statistical_tests: bool = True
    ) -> str:
        """匯出論文數據
        
        Args:
            algorithm_names: 算法名稱列表
            metric_types: 指標類型列表
            format_type: 匯出格式
            include_statistical_tests: 是否包含統計檢驗
            
        Returns:
            str: 匯出的檔案路徑
        """
        pass
    
    @abstractmethod
    async def generate_performance_report(
        self,
        algorithm_names: List[str],
        report_type: str = "comprehensive"  # comprehensive, summary, comparison
    ) -> Dict[str, Any]:
        """生成性能報告
        
        Args:
            algorithm_names: 算法名稱列表
            report_type: 報告類型
            
        Returns:
            Dict[str, Any]: 性能報告
        """
        pass
    
    @abstractmethod
    async def set_performance_alert(
        self,
        algorithm_name: str,
        metric_type: MetricType,
        threshold: float,
        comparison_operator: str = "less_than"  # less_than, greater_than, equals
    ) -> str:
        """設定性能警報
        
        Args:
            algorithm_name: 算法名稱
            metric_type: 指標類型
            threshold: 閾值
            comparison_operator: 比較運算符
            
        Returns:
            str: 警報ID
        """
        pass
    
    @abstractmethod
    async def get_trending_analysis(
        self,
        algorithm_name: str,
        metric_type: MetricType,
        time_period_days: int = 7
    ) -> Dict[str, Any]:
        """獲取趨勢分析
        
        Args:
            algorithm_name: 算法名稱
            metric_type: 指標類型
            time_period_days: 時間周期（天）
            
        Returns:
            Dict[str, Any]: 趨勢分析結果
        """
        pass


class IMetricsCollector(ABC):
    """指標收集器接口"""
    
    @abstractmethod
    async def collect_system_metrics(self) -> List[PerformanceMetric]:
        """收集系統指標"""
        pass
    
    @abstractmethod
    async def collect_algorithm_metrics(self, algorithm_name: str) -> List[PerformanceMetric]:
        """收集算法指標"""
        pass
    
    @abstractmethod
    async def collect_network_metrics(self) -> List[PerformanceMetric]:
        """收集網路指標"""
        pass


class IMetricsAggregator(ABC):
    """指標聚合器接口"""
    
    @abstractmethod
    async def aggregate_by_time(
        self,
        metrics: List[PerformanceMetric],
        time_interval: timedelta,
        aggregation_type: AggregationType
    ) -> List[PerformanceMetric]:
        """按時間聚合指標"""
        pass
    
    @abstractmethod
    async def aggregate_by_scenario(
        self,
        metrics: List[PerformanceMetric],
        aggregation_type: AggregationType
    ) -> Dict[ScenarioType, PerformanceMetric]:
        """按場景聚合指標"""
        pass


class IAlertManager(ABC):
    """警報管理器接口"""
    
    @abstractmethod
    async def trigger_alert(self, alert_id: str, metric: PerformanceMetric):
        """觸發警報"""
        pass
    
    @abstractmethod
    async def resolve_alert(self, alert_id: str):
        """解決警報"""
        pass


# 異常定義
class PerformanceMonitorError(Exception):
    """性能監控基礎異常"""
    pass


class MetricRecordingError(PerformanceMonitorError):
    """指標記錄異常"""
    pass


class StatisticalAnalysisError(PerformanceMonitorError):
    """統計分析異常"""
    pass


class BaselineNotFoundError(PerformanceMonitorError):
    """基準數據不存在異常"""
    pass


class InsufficientDataError(PerformanceMonitorError):
    """數據不足異常"""
    pass