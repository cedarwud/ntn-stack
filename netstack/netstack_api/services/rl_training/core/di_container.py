"""
🧠 依賴注入容器

基於 SOLID 原則的依賴注入實現，支援：
- 服務註冊與解析
- 生命週期管理
- 循環依賴檢測
- 條件註冊
"""

import logging
from typing import Dict, Any, Type, TypeVar, Callable, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import inspect
import threading

from ..interfaces.rl_algorithm import IRLAlgorithm
from ..interfaces.training_scheduler import ITrainingScheduler
from ..interfaces.performance_monitor import IPerformanceMonitor
from ..interfaces.data_repository import IDataRepository
from ..interfaces.model_manager import IModelManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceScope(str, Enum):
    """服務生命週期範圍"""
    SINGLETON = "singleton"  # 單例模式
    TRANSIENT = "transient"  # 每次請求都創建新實例
    SCOPED = "scoped"        # 在特定範圍內單例


@dataclass
class ServiceDescriptor:
    """服務描述符"""
    interface: Type
    implementation: Union[Type, Callable, Any]
    scope: ServiceScope = ServiceScope.SINGLETON
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    dependencies: List[Type] = field(default_factory=list)
    condition: Optional[Callable] = None
    initialized: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DIContainer:
    """依賴注入容器
    
    提供服務註冊、依賴解析和生命週期管理功能。
    支援多種註冊方式和靈活的配置選項。
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._lock = threading.RLock()
        self._resolution_stack: List[Type] = []
        logger.info("依賴注入容器初始化完成")
    
    def register_singleton(self, interface: Type[T], implementation: Union[Type[T], T]) -> 'DIContainer':
        """註冊單例服務
        
        Args:
            interface: 服務接口類型
            implementation: 實現類型或實例
            
        Returns:
            DIContainer: 容器實例（支援鏈式調用）
        """
        return self._register_service(interface, implementation, ServiceScope.SINGLETON)
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """註冊瞬態服務
        
        Args:
            interface: 服務接口類型
            implementation: 實現類型
            
        Returns:
            DIContainer: 容器實例（支援鏈式調用）
        """
        return self._register_service(interface, implementation, ServiceScope.TRANSIENT)
    
    def register_scoped(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """註冊範圍服務
        
        Args:
            interface: 服務接口類型
            implementation: 實現類型
            
        Returns:
            DIContainer: 容器實例（支援鏈式調用）
        """
        return self._register_service(interface, implementation, ServiceScope.SCOPED)
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """註冊工廠方法
        
        Args:
            interface: 服務接口類型
            factory: 工廠方法
            
        Returns:
            DIContainer: 容器實例（支援鏈式調用）
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=factory,
                scope=ServiceScope.SINGLETON,
                factory=factory
            )
            self._services[interface] = descriptor
            logger.info(f"註冊工廠服務: {interface.__name__}")
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """註冊實例
        
        Args:
            interface: 服務接口類型
            instance: 服務實例
            
        Returns:
            DIContainer: 容器實例（支援鏈式調用）
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=instance,
                scope=ServiceScope.SINGLETON,
                instance=instance,
                initialized=True
            )
            self._services[interface] = descriptor
            logger.info(f"註冊實例服務: {interface.__name__}")
        return self
    
    def register_conditional(
        self,
        interface: Type[T],
        implementation: Type[T],
        condition: Callable[[], bool],
        scope: ServiceScope = ServiceScope.SINGLETON
    ) -> 'DIContainer':
        """條件註冊服務
        
        Args:
            interface: 服務接口類型
            implementation: 實現類型
            condition: 註冊條件
            scope: 服務範圍
            
        Returns:
            DIContainer: 容器實例（支援鏈式調用）
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                scope=scope,
                condition=condition
            )
            self._services[interface] = descriptor
            logger.info(f"條件註冊服務: {interface.__name__}")
        return self
    
    def _register_service(
        self,
        interface: Type[T],
        implementation: Union[Type[T], T],
        scope: ServiceScope
    ) -> 'DIContainer':
        """內部服務註冊方法"""
        with self._lock:
            # 檢查是否已註冊
            if interface in self._services:
                logger.warning(f"服務 {interface.__name__} 已註冊，將被覆蓋")
            
            # 分析依賴項
            dependencies = self._analyze_dependencies(implementation)
            
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                scope=scope,
                dependencies=dependencies
            )
            
            self._services[interface] = descriptor
            logger.info(f"註冊服務: {interface.__name__} -> {implementation.__name__ if hasattr(implementation, '__name__') else str(implementation)} ({scope.value})")
        
        return self
    
    def resolve(self, interface: Type[T], scope_id: Optional[str] = None) -> T:
        """解析服務
        
        Args:
            interface: 服務接口類型
            scope_id: 範圍ID（用於範圍服務）
            
        Returns:
            T: 服務實例
            
        Raises:
            ServiceNotRegisteredError: 服務未註冊
            CircularDependencyError: 循環依賴
        """
        with self._lock:
            return self._resolve_service(interface, scope_id)
    
    def _resolve_service(self, interface: Type[T], scope_id: Optional[str] = None) -> T:
        """內部服務解析方法"""
        # 檢查循環依賴
        if interface in self._resolution_stack:
            cycle = " -> ".join([t.__name__ for t in self._resolution_stack]) + f" -> {interface.__name__}"
            raise CircularDependencyError(f"檢測到循環依賴: {cycle}")
        
        # 檢查服務是否註冊
        if interface not in self._services:
            raise ServiceNotRegisteredError(f"服務 {interface.__name__} 未註冊")
        
        descriptor = self._services[interface]
        
        # 檢查條件註冊
        if descriptor.condition and not descriptor.condition():
            raise ServiceNotRegisteredError(f"服務 {interface.__name__} 的註冊條件不滿足")
        
        # 根據範圍返回實例
        if descriptor.scope == ServiceScope.SINGLETON:
            return self._get_singleton_instance(descriptor)
        elif descriptor.scope == ServiceScope.TRANSIENT:
            return self._create_transient_instance(descriptor)
        elif descriptor.scope == ServiceScope.SCOPED:
            return self._get_scoped_instance(descriptor, scope_id or "default")
        
        raise ValueError(f"未知的服務範圍: {descriptor.scope}")
    
    def _get_singleton_instance(self, descriptor: ServiceDescriptor) -> Any:
        """獲取單例實例"""
        if descriptor.instance is None:
            descriptor.instance = self._create_instance(descriptor)
            descriptor.initialized = True
        return descriptor.instance
    
    def _create_transient_instance(self, descriptor: ServiceDescriptor) -> Any:
        """創建瞬態實例"""
        return self._create_instance(descriptor)
    
    def _get_scoped_instance(self, descriptor: ServiceDescriptor, scope_id: str) -> Any:
        """獲取範圍實例"""
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}
        
        scope_instances = self._scoped_instances[scope_id]
        if descriptor.interface not in scope_instances:
            scope_instances[descriptor.interface] = self._create_instance(descriptor)
        
        return scope_instances[descriptor.interface]
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """創建服務實例"""
        self._resolution_stack.append(descriptor.interface)
        
        try:
            # 如果是工廠方法
            if descriptor.factory:
                return descriptor.factory()
            
            # 如果是已創建的實例
            if not inspect.isclass(descriptor.implementation):
                return descriptor.implementation
            
            # 創建新實例
            implementation_class = descriptor.implementation
            
            # 分析構造函數參數
            signature = inspect.signature(implementation_class.__init__)
            constructor_args = {}
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                # 如果參數有類型註解，嘗試解析依賴
                if param.annotation != param.empty:
                    if param.annotation in self._services:
                        constructor_args[param_name] = self._resolve_service(param.annotation)
                    elif param.default != param.empty:
                        # 有預設值的參數跳過
                        continue
                    else:
                        logger.warning(f"無法解析構造函數參數: {param_name} ({param.annotation})")
            
            instance = implementation_class(**constructor_args)
            logger.debug(f"創建服務實例: {descriptor.interface.__name__}")
            return instance
            
        finally:
            self._resolution_stack.pop()
    
    def _analyze_dependencies(self, implementation: Union[Type, Any]) -> List[Type]:
        """分析依賴項"""
        if not inspect.isclass(implementation):
            return []
        
        dependencies = []
        signature = inspect.signature(implementation.__init__)
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != param.empty:
                dependencies.append(param.annotation)
        
        return dependencies
    
    def is_registered(self, interface: Type) -> bool:
        """檢查服務是否已註冊
        
        Args:
            interface: 服務接口類型
            
        Returns:
            bool: 是否已註冊
        """
        return interface in self._services
    
    def unregister(self, interface: Type) -> bool:
        """註銷服務
        
        Args:
            interface: 服務接口類型
            
        Returns:
            bool: 是否註銷成功
        """
        with self._lock:
            if interface in self._services:
                del self._services[interface]
                # 清理範圍實例
                for scope_instances in self._scoped_instances.values():
                    if interface in scope_instances:
                        del scope_instances[interface]
                logger.info(f"註銷服務: {interface.__name__}")
                return True
            return False
    
    def clear_scope(self, scope_id: str) -> None:
        """清理指定範圍的實例
        
        Args:
            scope_id: 範圍ID
        """
        with self._lock:
            if scope_id in self._scoped_instances:
                del self._scoped_instances[scope_id]
                logger.info(f"清理範圍實例: {scope_id}")
    
    def get_registration_info(self) -> List[Dict[str, Any]]:
        """獲取註冊資訊
        
        Returns:
            List[Dict[str, Any]]: 註冊服務列表
        """
        info = []
        for interface, descriptor in self._services.items():
            info.append({
                "interface": interface.__name__,
                "implementation": (
                    descriptor.implementation.__name__ 
                    if hasattr(descriptor.implementation, '__name__') 
                    else str(descriptor.implementation)
                ),
                "scope": descriptor.scope.value,
                "initialized": descriptor.initialized,
                "dependencies": [dep.__name__ for dep in descriptor.dependencies],
                "created_at": descriptor.created_at
            })
        return info
    
    def validate_registrations(self) -> List[str]:
        """驗證註冊的有效性
        
        Returns:
            List[str]: 驗證錯誤列表
        """
        errors = []
        
        for interface, descriptor in self._services.items():
            # 檢查依賴項是否都已註冊
            for dependency in descriptor.dependencies:
                if dependency not in self._services:
                    errors.append(f"服務 {interface.__name__} 依賴未註冊的服務 {dependency.__name__}")
            
            # 檢查循環依賴（簡單檢查）
            visited = set()
            if self._has_circular_dependency(interface, visited):
                errors.append(f"服務 {interface.__name__} 存在循環依賴")
        
        return errors
    
    def _has_circular_dependency(self, interface: Type, visited: set) -> bool:
        """檢查循環依賴"""
        if interface in visited:
            return True
        
        if interface not in self._services:
            return False
        
        visited.add(interface)
        descriptor = self._services[interface]
        
        for dependency in descriptor.dependencies:
            if self._has_circular_dependency(dependency, visited.copy()):
                return True
        
        return False


def setup_default_container() -> DIContainer:
    """設置預設的依賴注入容器
    
    Returns:
        DIContainer: 配置好的容器實例
    """
    container = DIContainer()
    
    # 這裡將在後續添加預設的服務註冊
    logger.info("設置預設依賴注入容器")
    
    return container


# 異常定義
class DIContainerError(Exception):
    """依賴注入容器基礎異常"""
    pass


class ServiceNotRegisteredError(DIContainerError):
    """服務未註冊異常"""
    pass


class CircularDependencyError(DIContainerError):
    """循環依賴異常"""
    pass


class ServiceResolutionError(DIContainerError):
    """服務解析異常"""
    pass