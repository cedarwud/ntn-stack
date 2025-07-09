"""
依賴注入容器
============

實現依賴注入模式，管理組件的創建和依賴關係。
"""

from typing import Dict, Any, Type, Callable, Optional, TypeVar, List
import inspect
import structlog
from unittest.mock import Mock, AsyncMock
import time
import asyncio

# 延遲導入以避免循環依賴
from ..interfaces import (
    EventProcessorInterface,
    CandidateSelectorInterface,
    RLIntegrationInterface,
    DecisionExecutorInterface,
    VisualizationCoordinatorInterface,
)
from ..interfaces.event_processor import ProcessedEvent
from ..interfaces.candidate_selector import Candidate, ScoredCandidate
from ..interfaces.decision_engine import Decision
from ..interfaces.executor import ExecutionResult, ExecutionStatus
from ..utils.state_manager import StateManager

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class DIContainer:
    """
    依賴注入容器主類

    管理組件的註冊、解析和生命週期。
    """

    def __init__(self, use_mocks: bool = False):
        """初始化容器"""
        self.registry: Dict[Type, Dict[str, Any]] = {}
        self.instances: Dict[Type, Any] = {}
        self.use_mocks = use_mocks

        logger.info(
            "DIContainer initialized", use_mocks=self.use_mocks, container_id=id(self)
        )

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        instance: Optional[T] = None,
    ) -> "DIContainer":
        """
        註冊單例服務

        Args:
            interface: 接口類型
            implementation: 實現類型 (可選)
            instance: 已創建的實例 (可選)

        Returns:
            DIContainer: 自身，支持鏈式調用
        """
        if instance is not None:
            self.instances[interface] = instance
        elif implementation is not None:
            self.registry[interface] = {
                "type": "singleton",
                "implementation": implementation,
            }
        else:
            self.registry[interface] = {
                "type": "singleton",
                "implementation": interface,
            }

        logger.debug(
            "Singleton registered",
            interface=interface.__name__,
        )

        return self

    def register_transient(
        self, interface: Type[T], implementation: Optional[Type[T]] = None
    ) -> "DIContainer":
        """
        註冊瞬態服務 (每次獲取都創建新實例)

        Args:
            interface: 接口類型
            implementation: 實現類型 (可選)

        Returns:
            DIContainer: 自身，支持鏈式調用
        """
        implementation = implementation or interface
        self.registry[interface] = {
            "type": "transient",
            "implementation": implementation,
        }

        logger.debug(
            "Transient registered",
            interface=interface.__name__,
        )

        return self

    def register_factory(
        self, interface: Type[T], factory: Callable[[], T]
    ) -> "DIContainer":
        """
        註冊工廠函數

        Args:
            interface: 接口類型
            factory: 工廠函數

        Returns:
            DIContainer: 自身，支持鏈式調用
        """
        self.registry[interface] = {"type": "factory", "factory": factory}

        logger.debug("Factory registered", interface=interface.__name__)

        return self

    def register_instance(self, interface: Type[T], instance: T) -> "DIContainer":
        """
        註冊實例

        Args:
            interface: 接口類型
            instance: 實例對象

        Returns:
            DIContainer: 自身，支持鏈式調用
        """
        self.instances[interface] = instance

        logger.debug(
            "Instance registered",
            interface=interface.__name__,
        )

        return self

    def get(self, interface: Type[T]) -> T:
        """
        獲取服務實例

        Args:
            interface: 接口類型

        Returns:
            T: 服務實例

        Raises:
            DIContainerError: 服務未註冊或創建失敗
        """
        try:
            if self.use_mocks:
                # 如果使用模擬，返回一個 AsyncMock 實例
                logger.debug(
                    "Providing mock for interface", interface=interface.__name__
                )
                if interface not in self.instances:
                    mock_instance = AsyncMock(spec=interface)  # 使用 AsyncMock

                    # 為關鍵的模擬組件添加默認的異步健康檢查方法
                    if hasattr(interface, "health_check"):

                        async def mock_health_check():
                            return True

                        mock_instance.health_check = mock_health_check

                    self.instances[interface] = mock_instance
                return self.instances[interface]

            if interface in self.instances:
                return self.instances[interface]

            # 2. 檢查工廠函數
            if (
                interface in self.registry
                and self.registry[interface]["type"] == "factory"
            ):
                return self.registry[interface]["factory"]()

            # 3. 檢查註冊的服務
            if interface in self.registry:
                implementation, lifecycle = (
                    self.registry[interface]["implementation"],
                    self.registry[interface]["type"],
                )
                instance = self._create_instance(implementation)

                if lifecycle == "singleton":
                    self.instances[interface] = instance

                return instance

            # 4. 嘗試直接創建 (如果是具體類)
            if not inspect.isabstract(interface):
                instance = self._create_instance(interface)
                return instance

            raise DIContainerError(f"Service not registered: {interface.__name__}")

        except Exception as e:
            logger.error(
                "Failed to resolve service", interface=interface.__name__, error=str(e)
            )
            raise DIContainerError(f"Failed to resolve {interface.__name__}: {str(e)}")

    def _create_instance(self, implementation: Type[T]) -> T:
        """
        創建實例並自動注入依賴

        Args:
            implementation: 實現類型

        Returns:
            T: 創建的實例
        """
        try:
            # 獲取構造函數參數
            constructor = implementation.__init__
            signature = inspect.signature(constructor)

            # 收集依賴
            dependencies = {}
            for param_name, param in signature.parameters.items():
                if param_name == "self":
                    continue

                # 跳過沒有類型註釋的參數
                if param.annotation == inspect.Parameter.empty:
                    continue

                # 跳過有默認值的參數
                if param.default != inspect.Parameter.empty:
                    continue

                # 遞歸解析依賴
                dependency = self.get(param.annotation)
                dependencies[param_name] = dependency

            # 創建實例
            instance = implementation(**dependencies)

            logger.debug(
                "Instance created",
                implementation=implementation.__name__,
                dependencies=list(dependencies.keys()),
            )

            return instance

        except Exception as e:
            logger.error(
                "Failed to create instance",
                implementation=implementation.__name__,
                error=str(e),
            )
            raise

    def has(self, interface: Type) -> bool:
        """
        檢查服務是否已註冊

        Args:
            interface: 接口類型

        Returns:
            bool: 是否已註冊
        """
        return interface in self.registry or interface in self.instances

    def clear(self):
        """清空容器"""
        self.registry.clear()
        self.instances.clear()

        logger.info("DI container cleared")

    def get_registered_services(self) -> Dict[str, str]:
        """
        獲取已註冊的服務列表

        Returns:
            Dict[str, str]: 服務名稱到類型的映射
        """
        services = {}

        # 註冊的服務
        for interface, (implementation, lifecycle) in self.registry.items():
            services[interface.__name__] = f"{implementation.__name__} ({lifecycle})"

        # 單例實例
        for interface, instance in self.instances.items():
            if interface not in services:  # 避免重複
                services[interface.__name__] = (
                    f"{type(instance).__name__} (singleton instance)"
                )

        # 工廠函數
        for interface, factory in self.registry.items():
            if factory["type"] == "factory":
                services[interface.__name__] = (
                    f"{factory['factory'].__name__} (factory)"
                )

        return services

    def validate_dependencies(self) -> List[str]:
        """
        驗證依賴關係

        Returns:
            List[str]: 錯誤列表
        """
        errors = []

        for interface, (implementation, _) in self.registry.items():
            try:
                # 嘗試解析所有依賴
                constructor = implementation.__init__
                signature = inspect.signature(constructor)

                for param_name, param in signature.parameters.items():
                    if param_name == "self":
                        continue

                    if param.annotation == inspect.Parameter.empty:
                        continue

                    if param.default != inspect.Parameter.empty:
                        continue

                    # 檢查依賴是否可以解析
                    if not self.has(param.annotation):
                        errors.append(
                            f"{implementation.__name__} requires {param.annotation.__name__} "
                            f"for parameter '{param_name}', but it's not registered"
                        )

            except Exception as e:
                errors.append(f"Error validating {implementation.__name__}: {str(e)}")

        return errors


class DIContainerError(Exception):
    """依賴注入容器錯誤"""

    pass


def create_default_container(use_mocks: bool = False) -> DIContainer:
    """
    創建一個帶有默認生產實現的DI容器。
    如果 use_mocks 為 True，則提供模擬實現。
    """
    container = DIContainer(use_mocks=use_mocks)

    # 總是註冊狀態管理器
    from ..utils.state_manager import StateManager

    container.register_singleton(StateManager)

    if use_mocks:
        logger.info("Using MOCK implementations for DI container")

        # 顯式註冊所有接口的 AsyncMock 實例
        interfaces_to_mock = [
            EventProcessorInterface,
            CandidateSelectorInterface,
            RLIntegrationInterface,
            DecisionExecutorInterface,
            VisualizationCoordinatorInterface,
        ]
        for iface in interfaces_to_mock:
            mock_instance = AsyncMock(spec=iface)

            # 為 mock 添加一個總返回 True 的 health_check
            async def mock_health_check():
                return True

            mock_instance.health_check = mock_health_check

            container.register_instance(iface, mock_instance)

    else:
        logger.info("Using REAL implementations for DI container")
        # 生產模式下的真實實現
        from ..event_processing.processor import EventProcessor
        from ..candidate_selection.selector import CandidateSelector
        from ..decision_execution.rl_integration import RLDecisionEngine
        from ..decision_execution.executor import DecisionExecutor
        from ..visualization_integration.handover_3d_coordinator import (
            Handover3DCoordinator,
        )

        container.register_singleton(EventProcessorInterface, EventProcessor)
        container.register_singleton(CandidateSelectorInterface, CandidateSelector)
        container.register_singleton(RLIntegrationInterface, RLDecisionEngine)
        container.register_singleton(DecisionExecutorInterface, DecisionExecutor)

        # Handover3DCoordinator 需要一個 event_streamer 實例。
        # 在真實應用中，這個實例也應該由容器管理。這裡暫時用一個 Mock。
        container.register_factory(
            VisualizationCoordinatorInterface,
            lambda: Handover3DCoordinator(event_streamer=Mock()),
        )

    logger.info("Default DI container created", use_mocks=use_mocks)
    return container
