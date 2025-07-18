"""
🧠 模型管理器接口

統一的 RL 模型生命週期管理，支援：
- 模型版本控制
- 自動化部署
- A/B 測試
- 性能監控
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from .rl_algorithm import ScenarioType


class DeploymentStatus(str, Enum):
    """部署狀態"""
    CREATED = "created"
    VALIDATED = "validated" 
    STAGED = "staged"
    DEPLOYED = "deployed"
    RETIRED = "retired"
    FAILED = "failed"


class ModelFormat(str, Enum):
    """模型格式"""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    PICKLE = "pickle"
    CUSTOM = "custom"


class ValidationStatus(str, Enum):
    """驗證狀態"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ModelMetadata:
    """模型元數據"""
    model_id: str
    algorithm_name: str
    version: str
    format: ModelFormat
    file_path: str
    file_size_bytes: int
    checksum: str
    training_session_id: str
    hyperparameters: Dict[str, Any]
    training_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]
    test_metrics: Optional[Dict[str, float]] = None
    scenario_type: Optional[ScenarioType] = None
    created_at: datetime = None
    created_by: str = "system"
    tags: List[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []


@dataclass
class DeploymentConfig:
    """部署配置"""
    deployment_id: str
    model_id: str
    environment: str  # development, staging, production
    replica_count: int = 1
    resource_limits: Dict[str, str] = None
    auto_scaling: bool = False
    health_check_config: Dict[str, Any] = None
    routing_config: Dict[str, Any] = None
    deployment_notes: Optional[str] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                'cpu': '1000m',
                'memory': '2Gi'
            }
        if self.health_check_config is None:
            self.health_check_config = {
                'path': '/health',
                'interval_seconds': 30,
                'timeout_seconds': 5
            }


@dataclass
class ABTestConfig:
    """A/B 測試配置"""
    test_id: str
    name: str
    model_a_id: str  # 對照組
    model_b_id: str  # 訓練組
    traffic_split_percent: int  # B組流量百分比
    success_metrics: List[str]
    minimum_sample_size: int = 1000
    confidence_level: float = 0.95
    max_duration_days: int = 30
    auto_winner_selection: bool = True
    early_stopping_config: Optional[Dict[str, Any]] = None


@dataclass
class ValidationReport:
    """驗證報告"""
    validation_id: str
    model_id: str
    status: ValidationStatus
    score: float
    metrics: Dict[str, float]
    test_cases_passed: int
    test_cases_failed: int
    validation_time_seconds: float
    error_messages: List[str] = None
    recommendations: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
        if self.recommendations is None:
            self.recommendations = []
        if self.created_at is None:
            self.created_at = datetime.now()


class IModelManager(ABC):
    """模型管理器核心接口
    
    提供完整的模型生命週期管理功能，
    從訓練到部署的端到端支援。
    """
    
    # ===== 模型註冊與管理 =====
    
    @abstractmethod
    async def register_model(self, metadata: ModelMetadata) -> str:
        """註冊新模型
        
        Args:
            metadata: 模型元數據
            
        Returns:
            str: 模型ID
            
        Raises:
            ModelRegistrationError: 註冊失敗時拋出
        """
        pass
    
    @abstractmethod
    async def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """獲取模型元數據
        
        Args:
            model_id: 模型ID
            
        Returns:
            Optional[ModelMetadata]: 模型元數據
        """
        pass
    
    @abstractmethod
    async def update_model_metadata(self, model_id: str, updates: Dict[str, Any]) -> bool:
        """更新模型元數據
        
        Args:
            model_id: 模型ID
            updates: 更新內容
            
        Returns:
            bool: 是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_model(self, model_id: str, force: bool = False) -> bool:
        """刪除模型
        
        Args:
            model_id: 模型ID
            force: 是否強制刪除（即使已部署）
            
        Returns:
            bool: 是否刪除成功
        """
        pass
    
    @abstractmethod
    async def list_models(
        self,
        algorithm_name: Optional[str] = None,
        scenario_type: Optional[ScenarioType] = None,
        status: Optional[DeploymentStatus] = None,
        limit: Optional[int] = None
    ) -> List[ModelMetadata]:
        """列出模型
        
        Args:
            algorithm_name: 算法名稱
            scenario_type: 場景類型
            status: 部署狀態
            limit: 限制數量
            
        Returns:
            List[ModelMetadata]: 模型列表
        """
        pass
    
    # ===== 模型驗證 =====
    
    @abstractmethod
    async def validate_model(
        self,
        model_id: str,
        validation_dataset: str,
        validation_config: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """驗證模型
        
        Args:
            model_id: 模型ID
            validation_dataset: 驗證數據集路徑
            validation_config: 驗證配置
            
        Returns:
            ValidationReport: 驗證報告
        """
        pass
    
    @abstractmethod
    async def get_validation_report(self, validation_id: str) -> Optional[ValidationReport]:
        """獲取驗證報告
        
        Args:
            validation_id: 驗證ID
            
        Returns:
            Optional[ValidationReport]: 驗證報告
        """
        pass
    
    @abstractmethod
    async def set_validation_pipeline(
        self,
        algorithm_name: str,
        validation_steps: List[Callable]
    ) -> bool:
        """設定驗證管道
        
        Args:
            algorithm_name: 算法名稱
            validation_steps: 驗證步驟列表
            
        Returns:
            bool: 是否設定成功
        """
        pass
    
    # ===== 模型部署 =====
    
    @abstractmethod
    async def deploy_model(self, config: DeploymentConfig) -> str:
        """部署模型
        
        Args:
            config: 部署配置
            
        Returns:
            str: 部署ID
            
        Raises:
            ModelDeploymentError: 部署失敗時拋出
        """
        pass
    
    @abstractmethod
    async def undeploy_model(self, deployment_id: str) -> bool:
        """撤銷部署
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            bool: 是否撤銷成功
        """
        pass
    
    @abstractmethod
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """獲取部署狀態
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            Dict[str, Any]: 部署狀態資訊
        """
        pass
    
    @abstractmethod
    async def list_deployments(
        self,
        environment: Optional[str] = None,
        status: Optional[DeploymentStatus] = None
    ) -> List[Dict[str, Any]]:
        """列出部署
        
        Args:
            environment: 環境名稱
            status: 部署狀態
            
        Returns:
            List[Dict[str, Any]]: 部署列表
        """
        pass
    
    @abstractmethod
    async def scale_deployment(self, deployment_id: str, replica_count: int) -> bool:
        """縮放部署
        
        Args:
            deployment_id: 部署ID
            replica_count: 副本數量
            
        Returns:
            bool: 是否縮放成功
        """
        pass
    
    # ===== A/B 測試 =====
    
    @abstractmethod
    async def start_ab_test(self, config: ABTestConfig) -> str:
        """開始 A/B 測試
        
        Args:
            config: A/B 測試配置
            
        Returns:
            str: 測試ID
        """
        pass
    
    @abstractmethod
    async def stop_ab_test(self, test_id: str) -> Dict[str, Any]:
        """停止 A/B 測試
        
        Args:
            test_id: 測試ID
            
        Returns:
            Dict[str, Any]: 測試結果
        """
        pass
    
    @abstractmethod
    async def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """獲取 A/B 測試結果
        
        Args:
            test_id: 測試ID
            
        Returns:
            Dict[str, Any]: 測試結果
        """
        pass
    
    @abstractmethod
    async def list_ab_tests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出 A/B 測試
        
        Args:
            status: 測試狀態
            
        Returns:
            List[Dict[str, Any]]: 測試列表
        """
        pass
    
    # ===== 模型監控 =====
    
    @abstractmethod
    async def monitor_model_performance(
        self,
        model_id: str,
        metrics: List[str],
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """監控模型性能
        
        Args:
            model_id: 模型ID
            metrics: 監控指標列表
            time_window_minutes: 時間窗口
            
        Returns:
            Dict[str, Any]: 性能指標
        """
        pass
    
    @abstractmethod
    async def set_performance_alert(
        self,
        model_id: str,
        metric_name: str,
        threshold: float,
        alert_callback: Callable
    ) -> str:
        """設定性能警報
        
        Args:
            model_id: 模型ID
            metric_name: 指標名稱
            threshold: 閾值
            alert_callback: 警報回調函數
            
        Returns:
            str: 警報ID
        """
        pass
    
    @abstractmethod
    async def get_model_health(self, model_id: str) -> Dict[str, Any]:
        """獲取模型健康狀態
        
        Args:
            model_id: 模型ID
            
        Returns:
            Dict[str, Any]: 健康狀態
        """
        pass
    
    # ===== 版本管理 =====
    
    @abstractmethod
    async def create_model_version(
        self,
        base_model_id: str,
        new_version: str,
        changes: Dict[str, Any]
    ) -> str:
        """創建模型版本
        
        Args:
            base_model_id: 基礎模型ID
            new_version: 新版本號
            changes: 變更內容
            
        Returns:
            str: 新模型ID
        """
        pass
    
    @abstractmethod
    async def compare_model_versions(
        self,
        model_id_a: str,
        model_id_b: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """比較模型版本
        
        Args:
            model_id_a: 模型A的ID
            model_id_b: 模型B的ID
            metrics: 比較指標
            
        Returns:
            Dict[str, Any]: 比較結果
        """
        pass
    
    @abstractmethod
    async def rollback_to_version(self, deployment_id: str, target_model_id: str) -> bool:
        """回滾到指定版本
        
        Args:
            deployment_id: 部署ID
            target_model_id: 目標模型ID
            
        Returns:
            bool: 是否回滾成功
        """
        pass


# 異常定義
class ModelManagerError(Exception):
    """模型管理器基礎異常"""
    pass


class ModelRegistrationError(ModelManagerError):
    """模型註冊異常"""
    pass


class ModelValidationError(ModelManagerError):
    """模型驗證異常"""
    pass


class ModelDeploymentError(ModelManagerError):
    """模型部署異常"""
    pass


class ABTestError(ModelManagerError):
    """A/B 測試異常"""
    pass


class ModelNotFoundError(ModelManagerError):
    """模型不存在異常"""
    pass


class DeploymentNotFoundError(ModelManagerError):
    """部署不存在異常"""
    pass