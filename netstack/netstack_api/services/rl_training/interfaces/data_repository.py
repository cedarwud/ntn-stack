"""
🧠 數據儲存庫接口

遵循儲存庫模式，提供統一的數據存取接口，
支援多種數據庫後端（PostgreSQL、MongoDB 等）。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass

from .rl_algorithm import TrainingConfig, TrainingResult, ScenarioType
from .performance_monitor import PerformanceMetric, MetricType


@dataclass
class ExperimentSession:
    """訓練會話實體"""
    id: Optional[int]
    experiment_name: str
    algorithm_type: str
    scenario_type: ScenarioType
    paper_reference: Optional[str]
    researcher_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_episodes: int
    session_status: str
    config_hash: str
    hyperparameters: Dict[str, Any]
    environment_config: Dict[str, Any]
    research_notes: Optional[str]
    created_at: datetime


@dataclass
class TrainingEpisode:
    """訓練回合實體"""
    id: Optional[int]
    session_id: int
    episode_number: int
    total_reward: float
    success_rate: float
    handover_latency_ms: float
    throughput_mbps: float
    packet_loss_rate: float
    convergence_indicator: float
    exploration_rate: float
    episode_metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class ModelVersion:
    """模型版本實體"""
    id: Optional[int]
    algorithm_type: str
    version_number: str
    model_file_path: str
    training_session_id: int
    validation_score: float
    test_score: float
    deployment_status: str
    paper_published: bool
    benchmark_results: Dict[str, Any]
    model_size_mb: float
    inference_time_ms: float
    created_at: datetime


@dataclass
class QueryFilter:
    """查詢過濾器"""
    algorithm_types: Optional[List[str]] = None
    scenario_types: Optional[List[ScenarioType]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    session_statuses: Optional[List[str]] = None
    researcher_ids: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class IDataRepository(ABC):
    """數據儲存庫核心接口
    
    提供統一的數據存取抽象，支援：
    - CRUD 操作
    - 複雜查詢
    - 事務處理
    - 數據遷移
    """
    
    # ===== 訓練會話管理 =====
    
    @abstractmethod
    async def create_experiment_session(self, session: ExperimentSession) -> int:
        """創建訓練會話
        
        Args:
            session: 訓練會話資料
            
        Returns:
            int: 新建會話的ID
            
        Raises:
            DataRepositoryError: 數據庫操作失敗
        """
        pass
    
    @abstractmethod
    async def get_experiment_session(self, session_id: int) -> Optional[ExperimentSession]:
        """獲取訓練會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            Optional[ExperimentSession]: 會話資料，不存在則返回None
        """
        pass
    
    @abstractmethod
    async def update_experiment_session(self, session_id: int, updates: Dict[str, Any]) -> bool:
        """更新訓練會話
        
        Args:
            session_id: 會話ID
            updates: 更新欄位
            
        Returns:
            bool: 是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_experiment_session(self, session_id: int) -> bool:
        """刪除訓練會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            bool: 是否刪除成功
        """
        pass
    
    @abstractmethod
    async def query_experiment_sessions(self, filter_obj: QueryFilter) -> List[ExperimentSession]:
        """查詢訓練會話
        
        Args:
            filter_obj: 查詢過濾器
            
        Returns:
            List[ExperimentSession]: 符合條件的會話列表
        """
        pass
    
    # ===== 訓練回合管理 =====
    
    @abstractmethod
    async def create_training_episode(self, episode: TrainingEpisode) -> int:
        """創建訓練回合
        
        Args:
            episode: 回合資料
            
        Returns:
            int: 新建回合的ID
        """
        pass
    
    @abstractmethod
    async def get_training_episodes(
        self, 
        session_id: int, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[TrainingEpisode]:
        """獲取訓練回合
        
        Args:
            session_id: 會話ID
            limit: 限制數量
            offset: 偏移量
            
        Returns:
            List[TrainingEpisode]: 回合列表
        """
        pass
    
    @abstractmethod
    async def get_latest_episode(self, session_id: int) -> Optional[TrainingEpisode]:
        """獲取最新回合
        
        Args:
            session_id: 會話ID
            
        Returns:
            Optional[TrainingEpisode]: 最新回合資料
        """
        pass
    
    @abstractmethod
    async def batch_create_episodes(self, episodes: List[TrainingEpisode]) -> int:
        """批量創建回合
        
        Args:
            episodes: 回合列表
            
        Returns:
            int: 成功創建的回合數量
        """
        pass
    
    # ===== 性能指標管理 =====
    
    @abstractmethod
    async def store_performance_metric(self, metric: PerformanceMetric) -> bool:
        """存儲性能指標
        
        Args:
            metric: 性能指標
            
        Returns:
            bool: 是否存儲成功
        """
        pass
    
    @abstractmethod
    async def batch_store_metrics(self, metrics: List[PerformanceMetric]) -> int:
        """批量存儲指標
        
        Args:
            metrics: 指標列表
            
        Returns:
            int: 成功存儲的指標數量
        """
        pass
    
    @abstractmethod
    async def query_performance_metrics(
        self,
        algorithm_names: List[str],
        metric_types: List[MetricType],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        scenario_type: Optional[ScenarioType] = None
    ) -> List[PerformanceMetric]:
        """查詢性能指標
        
        Args:
            algorithm_names: 算法名稱列表
            metric_types: 指標類型列表
            start_time: 開始時間
            end_time: 結束時間
            scenario_type: 場景類型
            
        Returns:
            List[PerformanceMetric]: 指標列表
        """
        pass
    
    # ===== 模型版本管理 =====
    
    @abstractmethod
    async def create_model_version(self, model: ModelVersion) -> int:
        """創建模型版本
        
        Args:
            model: 模型資料
            
        Returns:
            int: 新建模型的ID
        """
        pass
    
    @abstractmethod
    async def get_model_versions(
        self, 
        algorithm_type: str,
        limit: Optional[int] = None
    ) -> List[ModelVersion]:
        """獲取模型版本
        
        Args:
            algorithm_type: 算法類型
            limit: 限制數量
            
        Returns:
            List[ModelVersion]: 模型版本列表
        """
        pass
    
    @abstractmethod
    async def get_best_model(self, algorithm_type: str, metric: str = "validation_score") -> Optional[ModelVersion]:
        """獲取最佳模型
        
        Args:
            algorithm_type: 算法類型
            metric: 評估指標
            
        Returns:
            Optional[ModelVersion]: 最佳模型
        """
        pass
    
    # ===== 統計分析 =====
    
    @abstractmethod
    async def get_algorithm_statistics(
        self,
        algorithm_name: str,
        scenario_type: Optional[ScenarioType] = None
    ) -> Dict[str, Any]:
        """獲取算法統計
        
        Args:
            algorithm_name: 算法名稱
            scenario_type: 場景類型
            
        Returns:
            Dict[str, Any]: 統計資料
        """
        pass
    
    @abstractmethod
    async def get_convergence_analysis(
        self,
        session_ids: List[int],
        convergence_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        """獲取收斂分析
        
        Args:
            session_ids: 會話ID列表
            convergence_threshold: 收斂閾值
            
        Returns:
            List[Dict[str, Any]]: 收斂分析結果
        """
        pass
    
    @abstractmethod
    async def compare_algorithms(
        self,
        algorithm_names: List[str],
        metric_types: List[MetricType],
        scenario_type: Optional[ScenarioType] = None
    ) -> Dict[str, Any]:
        """比較算法性能
        
        Args:
            algorithm_names: 算法名稱列表
            metric_types: 指標類型列表
            scenario_type: 場景類型
            
        Returns:
            Dict[str, Any]: 比較結果
        """
        pass
    
    # ===== 數據管理 =====
    
    @abstractmethod
    async def backup_data(self, backup_path: str) -> bool:
        """備份數據
        
        Args:
            backup_path: 備份路徑
            
        Returns:
            bool: 是否備份成功
        """
        pass
    
    @abstractmethod
    async def restore_data(self, backup_path: str) -> bool:
        """恢復數據
        
        Args:
            backup_path: 備份路徑
            
        Returns:
            bool: 是否恢復成功
        """
        pass
    
    @abstractmethod
    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """清理舊數據
        
        Args:
            days_to_keep: 保留天數
            
        Returns:
            int: 清理的記錄數量
        """
        pass
    
    @abstractmethod
    async def get_database_health(self) -> Dict[str, Any]:
        """獲取數據庫健康狀態
        
        Returns:
            Dict[str, Any]: 健康狀態資訊
        """
        pass


class ITransactionManager(ABC):
    """事務管理器接口"""
    
    @abstractmethod
    async def begin_transaction(self):
        """開始事務"""
        pass
    
    @abstractmethod
    async def commit_transaction(self):
        """提交事務"""
        pass
    
    @abstractmethod
    async def rollback_transaction(self):
        """回滾事務"""
        pass


class IMigrationManager(ABC):
    """數據遷移管理器接口"""
    
    @abstractmethod
    async def migrate_from_mongodb(self, mongo_connection_string: str) -> bool:
        """從 MongoDB 遷移數據
        
        Args:
            mongo_connection_string: MongoDB 連接字串
            
        Returns:
            bool: 是否遷移成功
        """
        pass
    
    @abstractmethod
    async def get_migration_status(self) -> Dict[str, Any]:
        """獲取遷移狀態
        
        Returns:
            Dict[str, Any]: 遷移狀態資訊
        """
        pass


# 異常定義
class DataRepositoryError(Exception):
    """數據儲存庫基礎異常"""
    pass


class ConnectionError(DataRepositoryError):
    """連接異常"""
    pass


class QueryExecutionError(DataRepositoryError):
    """查詢執行異常"""
    pass


class DataIntegrityError(DataRepositoryError):
    """數據完整性異常"""
    pass


class TransactionError(DataRepositoryError):
    """事務異常"""
    pass


class MigrationError(DataRepositoryError):
    """遷移異常"""
    pass