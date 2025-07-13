"""
🚀 RL 系統初始化器
統一管理系統啟動流程和依賴注入配置
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from .di_container import DIContainer, ServiceScope
from .service_locator import ServiceLocator
from .repository_factory import RepositoryFactory, RepositoryType
from .config_manager import ConfigDrivenAlgorithmManager, create_default_config

from ..interfaces.data_repository import IDataRepository
from ..interfaces.training_scheduler import ITrainingScheduler
from ..interfaces.performance_monitor import IPerformanceMonitor
from ..interfaces.model_manager import IModelManager

logger = logging.getLogger(__name__)


class RLSystemInitializer:
    """RL 系統初始化器
    
    負責系統啟動時的各種初始化工作：
    - 配置加載
    - 依賴注入容器設置
    - 數據庫連接建立
    - 服務註冊
    - 算法管理器初始化
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.container: Optional[DIContainer] = None
        self.config_manager: Optional[ConfigDrivenAlgorithmManager] = None
        self.service_locator: Optional[ServiceLocator] = None
        self._initialized = False
        
        logger.info(f"RL系統初始化器創建，配置文件: {self.config_path}")
    
    def _get_default_config_path(self) -> str:
        """獲取預設配置文件路徑"""
        # 嘗試多個可能的配置文件位置
        possible_paths = [
            os.getenv("RL_CONFIG_PATH"),
            "./config/rl_config.yaml",
            "./rl_system/config/rl_config.yaml",
            "/app/config/rl_config.yaml",
            str(Path(__file__).parent.parent / "config" / "rl_config.yaml")
        ]
        
        for path in possible_paths:
            if path and Path(path).exists():
                return path
        
        # 如果都不存在，返回預設路徑（後續會創建）
        default_path = str(Path(__file__).parent.parent / "config" / "rl_config.yaml")
        logger.warning(f"未找到配置文件，將使用預設路徑: {default_path}")
        return default_path
    
    async def initialize(self) -> Dict[str, Any]:
        """初始化整個 RL 系統
        
        Returns:
            Dict[str, Any]: 初始化結果報告
        """
        if self._initialized:
            logger.warning("系統已初始化，跳過重複初始化")
            return {"status": "already_initialized"}
        
        try:
            initialization_report = {
                "status": "success",
                "components": {},
                "errors": []
            }
            
            # Step 1: 確保配置文件存在
            await self._ensure_config_file_exists()
            initialization_report["components"]["config_file"] = "created/verified"
            
            # Step 2: 創建依賴注入容器
            self.container = DIContainer()
            initialization_report["components"]["di_container"] = "created"
            
            # Step 3: 初始化數據倉庫
            repository_result = await self._initialize_repository()
            initialization_report["components"]["repository"] = repository_result
            
            # Step 4: 註冊核心服務
            services_result = await self._register_core_services()
            initialization_report["components"]["core_services"] = services_result
            
            # Step 5: 初始化服務定位器
            self.service_locator = ServiceLocator.initialize(self.container)
            initialization_report["components"]["service_locator"] = "initialized"
            
            # Step 6: 初始化配置管理器
            config_manager_result = await self._initialize_config_manager()
            initialization_report["components"]["config_manager"] = config_manager_result
            
            # Step 7: 驗證系統健康狀態
            health_check_result = await self._perform_health_check()
            initialization_report["components"]["health_check"] = health_check_result
            
            self._initialized = True
            logger.info("RL系統初始化完成")
            
            return initialization_report
            
        except Exception as e:
            logger.error(f"RL系統初始化失敗: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "components": {}
            }
    
    async def _ensure_config_file_exists(self) -> None:
        """確保配置文件存在"""
        config_path = Path(self.config_path)
        
        if not config_path.exists():
            logger.info(f"配置文件不存在，創建預設配置: {config_path}")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            create_default_config(config_path)
        else:
            logger.info(f"使用現有配置文件: {config_path}")
    
    async def _initialize_repository(self) -> str:
        """初始化數據倉庫"""
        try:
            # 從環境變數或配置推斷倉庫類型
            repository = await RepositoryFactory.create_repository()
            
            # 註冊倉庫到容器
            self.container.register_instance(IDataRepository, repository)
            
            # 測試倉庫連接
            health_status = await repository.get_database_health()
            if health_status.get("status") == "healthy":
                logger.info("數據倉庫初始化成功")
                return f"initialized ({type(repository).__name__})"
            else:
                logger.warning(f"數據倉庫健康檢查警告: {health_status}")
                return f"initialized_with_warnings ({type(repository).__name__})"
                
        except Exception as e:
            logger.error(f"數據倉庫初始化失敗: {e}")
            # 回退到 Mock 倉庫
            logger.info("回退到 Mock 數據倉庫")
            mock_repository = await RepositoryFactory.create_repository(
                repository_type=RepositoryType.MOCK
            )
            self.container.register_instance(IDataRepository, mock_repository)
            return f"fallback_to_mock ({e})"
    
    async def _register_core_services(self) -> Dict[str, str]:
        """註冊核心服務"""
        services_status = {}
        
        try:
            # 嘗試導入和註冊各種服務實現
            
            # 1. 訓練調度器
            try:
                from ..implementations.training_scheduler import TrainingScheduler
                self.container.register_singleton(ITrainingScheduler, TrainingScheduler)
                services_status["training_scheduler"] = "registered"
            except ImportError:
                logger.warning("TrainingScheduler 實現不可用")
                services_status["training_scheduler"] = "not_available"
            
            # 2. 性能監控器
            try:
                from ..implementations.performance_monitor import PerformanceMonitor
                self.container.register_singleton(IPerformanceMonitor, PerformanceMonitor)
                services_status["performance_monitor"] = "registered"
            except ImportError:
                logger.warning("PerformanceMonitor 實現不可用")
                services_status["performance_monitor"] = "not_available"
            
            # 3. 模型管理器
            try:
                from ..implementations.model_manager import ModelManager
                self.container.register_singleton(IModelManager, ModelManager)
                services_status["model_manager"] = "registered"
            except ImportError:
                logger.warning("ModelManager 實現不可用")
                services_status["model_manager"] = "not_available"
            
            return services_status
            
        except Exception as e:
            logger.error(f"核心服務註冊失敗: {e}")
            return {"error": str(e)}
    
    async def _initialize_config_manager(self) -> str:
        """初始化配置管理器"""
        try:
            self.config_manager = ConfigDrivenAlgorithmManager(
                config_path=self.config_path,
                container=self.container
            )
            await self.config_manager.initialize()
            
            available_algorithms = self.config_manager.get_available_algorithms()
            logger.info(f"配置管理器初始化完成，可用算法: {available_algorithms}")
            
            return f"initialized ({len(available_algorithms)} algorithms)"
            
        except Exception as e:
            logger.error(f"配置管理器初始化失敗: {e}")
            return f"failed ({e})"
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """執行系統健康檢查"""
        try:
            health_status = {
                "overall": "healthy",
                "components": {}
            }
            
            # 檢查服務定位器
            if self.service_locator:
                locator_health = ServiceLocator.get_health_status()
                health_status["components"]["service_locator"] = locator_health["status"]
            
            # 檢查數據倉庫
            try:
                repository = ServiceLocator.get_data_repository()
                db_health = await repository.get_database_health()
                health_status["components"]["repository"] = db_health["status"]
            except Exception as e:
                health_status["components"]["repository"] = f"error: {e}"
                health_status["overall"] = "degraded"
            
            # 檢查配置管理器
            if self.config_manager:
                config_stats = self.config_manager.get_manager_stats()
                health_status["components"]["config_manager"] = (
                    "healthy" if config_stats["initialized"] else "not_initialized"
                )
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "overall": "unhealthy",
                "error": str(e)
            }
    
    def get_container(self) -> DIContainer:
        """獲取依賴注入容器
        
        Returns:
            DIContainer: 容器實例
            
        Raises:
            RuntimeError: 系統未初始化
        """
        if not self._initialized or not self.container:
            raise RuntimeError("系統尚未初始化，請先調用 initialize() 方法")
        return self.container
    
    def get_service_locator(self) -> ServiceLocator:
        """獲取服務定位器
        
        Returns:
            ServiceLocator: 服務定位器實例
            
        Raises:
            RuntimeError: 系統未初始化
        """
        if not self._initialized or not self.service_locator:
            raise RuntimeError("系統尚未初始化，請先調用 initialize() 方法")
        return self.service_locator
    
    def get_config_manager(self) -> ConfigDrivenAlgorithmManager:
        """獲取配置管理器
        
        Returns:
            ConfigDrivenAlgorithmManager: 配置管理器實例
            
        Raises:
            RuntimeError: 系統未初始化
        """
        if not self._initialized or not self.config_manager:
            raise RuntimeError("系統尚未初始化，請先調用 initialize() 方法")
        return self.config_manager
    
    async def shutdown(self) -> None:
        """關閉系統"""
        try:
            logger.info("開始關閉 RL 系統...")
            
            # 關閉配置管理器
            if self.config_manager:
                await self.config_manager.shutdown()
            
            # 關閉所有倉庫實例
            await RepositoryFactory.shutdown_all()
            
            # 關閉服務定位器
            if self.service_locator:
                ServiceLocator.shutdown()
            
            self._initialized = False
            logger.info("RL 系統已關閉")
            
        except Exception as e:
            logger.error(f"關閉系統失敗: {e}")
    
    def is_initialized(self) -> bool:
        """檢查系統是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized
    
    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊
        
        Returns:
            Dict[str, Any]: 系統資訊
        """
        info = {
            "initialized": self._initialized,
            "config_path": self.config_path,
        }
        
        if self._initialized:
            # 添加各組件的詳細資訊
            if self.container:
                info["container"] = {
                    "registered_services": len(self.container.get_registration_info())
                }
            
            if self.config_manager:
                info["config_manager"] = self.config_manager.get_manager_stats()
            
            if self.service_locator:
                info["service_locator"] = ServiceLocator.get_health_status()
        
        return info


# 全局初始化器實例
_global_initializer: Optional[RLSystemInitializer] = None


async def initialize_rl_system(config_path: Optional[str] = None) -> RLSystemInitializer:
    """初始化 RL 系統（全局函數）
    
    Args:
        config_path: 配置文件路徑
        
    Returns:
        RLSystemInitializer: 初始化器實例
    """
    global _global_initializer
    
    if _global_initializer is None:
        _global_initializer = RLSystemInitializer(config_path)
    
    if not _global_initializer.is_initialized():
        await _global_initializer.initialize()
    
    return _global_initializer


def get_global_initializer() -> Optional[RLSystemInitializer]:
    """獲取全局初始化器實例
    
    Returns:
        Optional[RLSystemInitializer]: 初始化器實例
    """
    return _global_initializer


async def shutdown_rl_system() -> None:
    """關閉 RL 系統（全局函數）"""
    global _global_initializer
    
    if _global_initializer:
        await _global_initializer.shutdown()
        _global_initializer = None