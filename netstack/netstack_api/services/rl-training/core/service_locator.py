"""
🧠 服務定位器

提供統一的服務發現和訪問入口，
作為依賴注入容器的高級封裝。
"""

import logging
from typing import Dict, Any, Type, TypeVar, Optional, List
from datetime import datetime

from .di_container import DIContainer, ServiceScope
from ..interfaces.rl_algorithm import IRLAlgorithm
from ..interfaces.training_scheduler import ITrainingScheduler
from ..interfaces.performance_monitor import IPerformanceMonitor
from ..interfaces.data_repository import IDataRepository
from ..interfaces.model_manager import IModelManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLocator:
    """服務定位器
    
    提供便捷的服務訪問接口，隱藏依賴注入的複雜性。
    支援懶加載和服務緩存機制。
    """
    
    _instance: Optional['ServiceLocator'] = None
    _container: Optional[DIContainer] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ServiceLocator':
        if cls._instance is None:
            cls._instance = super(ServiceLocator, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ServiceLocator._initialized:
            self._service_cache: Dict[Type, Any] = {}
            self._initialization_time = datetime.now()
            ServiceLocator._initialized = True
            logger.info("服務定位器初始化完成")
    
    @classmethod
    def initialize(cls, container: Optional[DIContainer] = None) -> 'ServiceLocator':
        """初始化服務定位器
        
        Args:
            container: 依賴注入容器
            
        Returns:
            ServiceLocator: 服務定位器實例
        """
        locator = cls()
        cls._container = container or DIContainer()
        
        # 註冊預設服務（如果需要）
        locator._register_default_services()
        
        logger.info("服務定位器已初始化並配置完成")
        return locator
    
    def _register_default_services(self) -> None:
        """註冊預設服務"""
        try:
            # 這裡可以註冊一些預設的服務實現
            # 例如：記憶體中的實現、模擬實現等
            logger.debug("註冊預設服務")
            
        except Exception as e:
            logger.error(f"註冊預設服務失敗: {e}")
    
    @classmethod
    def get_container(cls) -> DIContainer:
        """獲取依賴注入容器
        
        Returns:
            DIContainer: 容器實例
            
        Raises:
            RuntimeError: 容器未初始化
        """
        if cls._container is None:
            raise RuntimeError("服務定位器尚未初始化，請先調用 initialize() 方法")
        return cls._container
    
    @classmethod
    def resolve(cls, service_type: Type[T], use_cache: bool = True) -> T:
        """解析服務
        
        Args:
            service_type: 服務類型
            use_cache: 是否使用緩存
            
        Returns:
            T: 服務實例
            
        Raises:
            ServiceNotAvailableError: 服務不可用
        """
        locator = cls()
        
        try:
            # 如果使用緩存且緩存中有實例，直接返回
            if use_cache and service_type in locator._service_cache:
                logger.debug(f"從緩存返回服務實例: {service_type.__name__}")
                return locator._service_cache[service_type]
            
            # 從容器解析服務
            container = cls.get_container()
            service_instance = container.resolve(service_type)
            
            # 如果使用緩存，將實例加入緩存
            if use_cache:
                locator._service_cache[service_type] = service_instance
            
            logger.debug(f"成功解析服務: {service_type.__name__}")
            return service_instance
            
        except Exception as e:
            logger.error(f"解析服務失敗: {service_type.__name__}, 錯誤: {e}")
            raise ServiceNotAvailableError(f"無法解析服務 {service_type.__name__}: {str(e)}")
    
    @classmethod
    def get_training_scheduler(cls) -> ITrainingScheduler:
        """獲取訓練調度器
        
        Returns:
            ITrainingScheduler: 訓練調度器實例
        """
        return cls.resolve(ITrainingScheduler)
    
    @classmethod
    def get_performance_monitor(cls) -> IPerformanceMonitor:
        """獲取性能監控器
        
        Returns:
            IPerformanceMonitor: 性能監控器實例
        """
        return cls.resolve(IPerformanceMonitor)
    
    @classmethod
    def get_data_repository(cls) -> IDataRepository:
        """獲取數據儲存庫
        
        Returns:
            IDataRepository: 數據儲存庫實例
        """
        return cls.resolve(IDataRepository)
    
    @classmethod
    def get_model_manager(cls) -> IModelManager:
        """獲取模型管理器
        
        Returns:
            IModelManager: 模型管理器實例
        """
        return cls.resolve(IModelManager)
    
    @classmethod
    def register_service(
        cls,
        interface: Type[T],
        implementation: Type[T],
        scope: ServiceScope = ServiceScope.SINGLETON
    ) -> None:
        """註冊服務
        
        Args:
            interface: 服務接口
            implementation: 實現類型
            scope: 服務範圍
        """
        container = cls.get_container()
        
        if scope == ServiceScope.SINGLETON:
            container.register_singleton(interface, implementation)
        elif scope == ServiceScope.TRANSIENT:
            container.register_transient(interface, implementation)
        elif scope == ServiceScope.SCOPED:
            container.register_scoped(interface, implementation)
        
        logger.info(f"註冊服務: {interface.__name__} -> {implementation.__name__} ({scope.value})")
    
    @classmethod
    def register_instance(cls, interface: Type[T], instance: T) -> None:
        """註冊服務實例
        
        Args:
            interface: 服務接口
            instance: 服務實例
        """
        container = cls.get_container()
        container.register_instance(interface, instance)
        logger.info(f"註冊實例服務: {interface.__name__}")
    
    @classmethod
    def is_service_registered(cls, service_type: Type) -> bool:
        """檢查服務是否已註冊
        
        Args:
            service_type: 服務類型
            
        Returns:
            bool: 是否已註冊
        """
        try:
            container = cls.get_container()
            return container.is_registered(service_type)
        except RuntimeError:
            return False
    
    @classmethod
    def get_registered_services(cls) -> List[str]:
        """獲取已註冊的服務列表
        
        Returns:
            List[str]: 服務名稱列表
        """
        try:
            container = cls.get_container()
            registration_info = container.get_registration_info()
            return [info["interface"] for info in registration_info]
        except RuntimeError:
            return []
    
    @classmethod
    def clear_cache(cls) -> None:
        """清除服務緩存"""
        locator = cls()
        locator._service_cache.clear()
        logger.info("已清除服務緩存")
    
    @classmethod
    def clear_service_cache(cls, service_type: Type) -> bool:
        """清除特定服務的緩存
        
        Args:
            service_type: 服務類型
            
        Returns:
            bool: 是否清除成功
        """
        locator = cls()
        if service_type in locator._service_cache:
            del locator._service_cache[service_type]
            logger.debug(f"已清除服務緩存: {service_type.__name__}")
            return True
        return False
    
    @classmethod
    def validate_services(cls) -> Dict[str, Any]:
        """驗證服務配置
        
        Returns:
            Dict[str, Any]: 驗證結果
        """
        try:
            container = cls.get_container()
            errors = container.validate_registrations()
            
            validation_result = {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "registered_services": len(container.get_registration_info()),
                "validation_time": datetime.now()
            }
            
            if validation_result["is_valid"]:
                logger.info("服務配置驗證通過")
            else:
                logger.warning(f"服務配置驗證失敗，發現 {len(errors)} 個錯誤")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"服務驗證失敗: {e}")
            return {
                "is_valid": False,
                "errors": [str(e)],
                "registered_services": 0,
                "validation_time": datetime.now()
            }
    
    @classmethod
    def get_health_status(cls) -> Dict[str, Any]:
        """獲取服務定位器健康狀態
        
        Returns:
            Dict[str, Any]: 健康狀態資訊
        """
        locator = cls()
        
        try:
            container_health = {
                "container_initialized": cls._container is not None,
                "service_cache_size": len(locator._service_cache),
                "registered_services": len(cls.get_registered_services()),
                "initialization_time": locator._initialization_time
            }
            
            # 驗證核心服務是否可用
            core_services_status = {}
            core_services = [
                ITrainingScheduler,
                IPerformanceMonitor,
                IDataRepository,
                IModelManager
            ]
            
            for service_type in core_services:
                try:
                    service_available = cls.is_service_registered(service_type)
                    core_services_status[service_type.__name__] = {
                        "registered": service_available,
                        "resolvable": False
                    }
                    
                    if service_available:
                        # 嘗試解析服務
                        cls.resolve(service_type, use_cache=False)
                        core_services_status[service_type.__name__]["resolvable"] = True
                        
                except Exception as e:
                    core_services_status[service_type.__name__]["error"] = str(e)
            
            return {
                "status": "healthy" if container_health["container_initialized"] else "unhealthy",
                "container": container_health,
                "core_services": core_services_status,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"獲取健康狀態失敗: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    @classmethod
    def create_scope(cls, scope_id: str) -> 'ScopedServiceLocator':
        """創建範圍服務定位器
        
        Args:
            scope_id: 範圍標識
            
        Returns:
            ScopedServiceLocator: 範圍服務定位器
        """
        return ScopedServiceLocator(scope_id, cls.get_container())
    
    @classmethod
    def shutdown(cls) -> None:
        """關閉服務定位器"""
        try:
            locator = cls()
            
            # 清除緩存
            locator._service_cache.clear()
            
            # 重置狀態
            cls._container = None
            cls._initialized = False
            cls._instance = None
            
            logger.info("服務定位器已關閉")
            
        except Exception as e:
            logger.error(f"關閉服務定位器失敗: {e}")


class ScopedServiceLocator:
    """範圍服務定位器
    
    在特定範圍內管理服務實例，
    適用於需要隔離的場景（如請求範圍、測試範圍等）。
    """
    
    def __init__(self, scope_id: str, container: DIContainer):
        self.scope_id = scope_id
        self.container = container
        self._created_at = datetime.now()
        logger.debug(f"創建範圍服務定位器: {scope_id}")
    
    def resolve(self, service_type: Type[T]) -> T:
        """在當前範圍內解析服務
        
        Args:
            service_type: 服務類型
            
        Returns:
            T: 服務實例
        """
        return self.container.resolve(service_type, scope_id=self.scope_id)
    
    def clear_scope(self) -> None:
        """清除當前範圍的所有實例"""
        self.container.clear_scope(self.scope_id)
        logger.debug(f"清除範圍實例: {self.scope_id}")
    
    def get_scope_info(self) -> Dict[str, Any]:
        """獲取範圍資訊
        
        Returns:
            Dict[str, Any]: 範圍資訊
        """
        return {
            "scope_id": self.scope_id,
            "created_at": self._created_at,
            "uptime_seconds": (datetime.now() - self._created_at).total_seconds()
        }


# 異常定義
class ServiceLocatorError(Exception):
    """服務定位器基礎異常"""
    pass


class ServiceNotAvailableError(ServiceLocatorError):
    """服務不可用異常"""
    pass


class ServiceLocatorNotInitializedError(ServiceLocatorError):
    """服務定位器未初始化異常"""
    pass