"""
🧠 訓練調度器接口

智能訓練任務調度，支援：
- 多算法並行訓練
- 資源優化分配
- 優先級管理
- 自動重試機制
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .rl_algorithm import TrainingConfig, TrainingResult, ScenarioType


class TrainingPriority(int, Enum):
    """訓練優先級"""
    CRITICAL = 1
    HIGH = 2  
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class SchedulingStrategy(str, Enum):
    """調度策略"""
    FIFO = "fifo"  # 先進先出
    PRIORITY = "priority"  # 優先級優先
    RESOURCE_AWARE = "resource_aware"  # 資源感知
    ROUND_ROBIN = "round_robin"  # 輪詢
    SHORTEST_JOB_FIRST = "shortest_job_first"  # 最短作業優先


@dataclass
class TrainingJob:
    """訓練作業"""
    job_id: str
    algorithm_name: str
    config: TrainingConfig
    priority: TrainingPriority = TrainingPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    resource_requirements: Dict[str, Any] = None
    estimated_duration_minutes: Optional[int] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.resource_requirements is None:
            self.resource_requirements = {
                'cpu_cores': 2,
                'memory_gb': 4,
                'gpu_required': False
            }


@dataclass 
class SchedulerStatus:
    """調度器狀態"""
    active_jobs: int
    queued_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_cpu_usage: float
    total_memory_usage: float
    gpu_utilization: Optional[float]
    average_queue_time_minutes: float
    scheduler_uptime_hours: float


@dataclass
class ResourceConstraints:
    """資源約束"""
    max_concurrent_jobs: int = 3
    max_cpu_usage_percent: float = 80.0
    max_memory_usage_percent: float = 80.0
    max_gpu_usage_percent: float = 90.0
    max_queue_size: int = 50


class ITrainingScheduler(ABC):
    """訓練調度器接口
    
    負責管理和調度多個 RL 算法的訓練任務，
    確保資源的合理分配和任務的高效執行。
    """
    
    @abstractmethod
    async def submit_training_job(self, job: TrainingJob) -> str:
        """提交訓練作業
        
        Args:
            job: 訓練作業配置
            
        Returns:
            str: 作業ID
            
        Raises:
            SchedulerError: 調度失敗時拋出
        """
        pass
    
    @abstractmethod
    async def cancel_training_job(self, job_id: str) -> bool:
        """取消訓練作業
        
        Args:
            job_id: 作業ID
            
        Returns:
            bool: 是否取消成功
        """
        pass
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """獲取作業狀態
        
        Args:
            job_id: 作業ID
            
        Returns:
            Dict: 作業狀態資訊
        """
        pass
    
    @abstractmethod
    async def get_training_queue(self) -> List[TrainingJob]:
        """獲取訓練佇列
        
        Returns:
            List[TrainingJob]: 排隊中的訓練作業
        """
        pass
    
    @abstractmethod
    async def get_scheduler_status(self) -> SchedulerStatus:
        """獲取調度器狀態
        
        Returns:
            SchedulerStatus: 調度器狀態
        """
        pass
    
    @abstractmethod
    async def set_scheduling_strategy(self, strategy: SchedulingStrategy) -> bool:
        """設定調度策略
        
        Args:
            strategy: 調度策略
            
        Returns:
            bool: 是否設定成功
        """
        pass
    
    @abstractmethod
    async def set_resource_constraints(self, constraints: ResourceConstraints) -> bool:
        """設定資源約束
        
        Args:
            constraints: 資源約束配置
            
        Returns:
            bool: 是否設定成功
        """
        pass
    
    @abstractmethod
    async def pause_scheduler(self) -> bool:
        """暫停調度器"""
        pass
    
    @abstractmethod
    async def resume_scheduler(self) -> bool:
        """恢復調度器"""
        pass
    
    @abstractmethod
    async def shutdown_scheduler(self, wait_for_completion: bool = True) -> bool:
        """關閉調度器
        
        Args:
            wait_for_completion: 是否等待當前作業完成
            
        Returns:
            bool: 是否關閉成功
        """
        pass


class IJobProgressCallback(ABC):
    """作業進度回調接口"""
    
    @abstractmethod
    async def on_job_queued(self, job: TrainingJob):
        """作業加入佇列事件"""
        pass
    
    @abstractmethod
    async def on_job_started(self, job: TrainingJob):
        """作業開始事件"""
        pass
    
    @abstractmethod
    async def on_job_progress(self, job_id: str, progress_percent: float, metrics: Dict[str, Any]):
        """作業進度更新事件"""
        pass
    
    @abstractmethod
    async def on_job_completed(self, job: TrainingJob, result: TrainingResult):
        """作業完成事件"""
        pass
    
    @abstractmethod
    async def on_job_failed(self, job: TrainingJob, error: Exception):
        """作業失敗事件"""
        pass
    
    @abstractmethod
    async def on_job_cancelled(self, job: TrainingJob):
        """作業取消事件"""
        pass


class IResourceMonitor(ABC):
    """資源監控接口"""
    
    @abstractmethod
    async def get_cpu_usage(self) -> float:
        """獲取 CPU 使用率"""
        pass
    
    @abstractmethod
    async def get_memory_usage(self) -> float:
        """獲取記憶體使用率"""
        pass
    
    @abstractmethod
    async def get_gpu_usage(self) -> Optional[float]:
        """獲取 GPU 使用率"""
        pass
    
    @abstractmethod
    async def check_resource_availability(self, requirements: Dict[str, Any]) -> bool:
        """檢查資源可用性
        
        Args:
            requirements: 資源需求
            
        Returns:
            bool: 資源是否充足
        """
        pass
    
    @abstractmethod
    async def estimate_completion_time(self, job: TrainingJob) -> Optional[timedelta]:
        """估算完成時間
        
        Args:
            job: 訓練作業
            
        Returns:
            Optional[timedelta]: 估算的完成時間
        """
        pass


# 異常定義
class SchedulerError(Exception):
    """調度器基礎異常"""
    pass


class ResourceInsufficientError(SchedulerError):
    """資源不足異常"""
    pass


class JobNotFoundError(SchedulerError):
    """作業不存在異常"""
    pass


class SchedulerBusyError(SchedulerError):
    """調度器忙碌異常"""
    pass


class InvalidJobConfigError(SchedulerError):
    """無效作業配置異常"""
    pass