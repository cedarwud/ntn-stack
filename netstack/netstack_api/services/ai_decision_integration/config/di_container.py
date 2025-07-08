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

    def __init__(self):
        """初始化容器"""
        self.registry: Dict[Type, Any] = {}
        self.singletons: Dict[Type, Any] = {}
        self.factories: Dict[Type, Callable] = {}
        self.transients: Dict[Type, Callable] = {}

        logger.info("DI container initialized")

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
            self.singletons[interface] = instance
        elif implementation is not None:
            self.registry[interface] = (implementation, "singleton")
        else:
            self.registry[interface] = (interface, "singleton")

        logger.debug(
            "Singleton registered",
            interface=interface.__name__,
            implementation=implementation.__name__ if implementation else "self",
            instance_provided=instance is not None,
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
        self.registry[interface] = (implementation, "transient")

        logger.debug(
            "Transient registered",
            interface=interface.__name__,
            implementation=implementation.__name__,
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
        self.factories[interface] = factory

        logger.debug(
            "Factory registered", interface=interface.__name__, factory=factory.__name__
        )

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
        self.singletons[interface] = instance

        logger.debug(
            "Instance registered",
            interface=interface.__name__,
            instance_type=type(instance).__name__,
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
            # 1. 檢查已創建的單例
            if interface in self.singletons:
                return self.singletons[interface]

            # 2. 檢查工廠函數
            if interface in self.factories:
                return self.factories[interface]()

            # 3. 檢查註冊的服務
            if interface in self.registry:
                implementation, lifecycle = self.registry[interface]
                instance = self._create_instance(implementation)

                if lifecycle == "singleton":
                    self.singletons[interface] = instance

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
        return (
            interface in self.registry
            or interface in self.singletons
            or interface in self.factories
        )

    def clear(self):
        """清空容器"""
        self.registry.clear()
        self.singletons.clear()
        self.factories.clear()
        self.transients.clear()

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
        for interface, instance in self.singletons.items():
            if interface not in services:  # 避免重複
                services[interface.__name__] = (
                    f"{type(instance).__name__} (singleton instance)"
                )

        # 工廠函數
        for interface, factory in self.factories.items():
            services[interface.__name__] = f"{factory.__name__} (factory)"

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
    創建一個預配置的 DI 容器。

    Args:
        use_mocks: 如果為 True，則註冊所有接口的模擬實現，主要用於測試。

    Returns:
        DIContainer: 配置好的容器。
    """
    container = DIContainer()

    if use_mocks:
        # --- 註冊所有接口的模擬實現 ---
        logger.info("Creating DI container with MOCKED implementations")

        # 模擬事件處理器
        mock_event_processor = Mock(spec=EventProcessorInterface)
        mock_event_processor.process_event.return_value = ProcessedEvent(
            event_type="A4",
            event_data={"test": "data"},
            timestamp=time.time(),
            confidence=0.9,
            trigger_conditions={},
            ue_id="UE_001",
            source_cell="CELL_001",
            target_cells=["CELL_002", "CELL_003"],
            measurement_values={"rsrp": -80.0},
        )
        container.register_instance(EventProcessorInterface, mock_event_processor)

        # 模擬候選篩選器
        mock_candidate_selector = Mock(spec=CandidateSelectorInterface)
        test_candidate = Candidate(
            satellite_id="SAT_001",
            elevation=45.0,
            signal_strength=-75.0,
            load_factor=0.5,
            distance=1000.0,
            azimuth=180.0,
            doppler_shift=1000.0,
            position={"x": 0, "y": 0, "z": 1000},
            velocity={"vx": 5, "vy": 0, "vz": 0},
            visibility_time=600.0,
        )
        mock_candidate_selector.select_candidates.return_value = [test_candidate]
        mock_candidate_selector.score_candidates.return_value = [
            ScoredCandidate(
                candidate=test_candidate,
                score=0.85,
                confidence=0.9,
                ranking=1,
                sub_scores={"elevation": 0.8, "signal": 0.9},
                reasoning={"primary": "high_signal_strength"},
            )
        ]
        container.register_instance(CandidateSelectorInterface, mock_candidate_selector)

        # 模擬決策引擎
        mock_decision_engine = Mock(spec=RLIntegrationInterface)
        mock_decision_engine.make_decision.return_value = Decision(
            selected_satellite="SAT_001",
            confidence=0.88,
            reasoning={"algorithm": "DQN", "score": 0.85},
            alternative_options=["SAT_002"],
            execution_plan={"handover_type": "A4"},
            visualization_data={"animation_duration": 3000},
            algorithm_used="DQN",
            decision_time=15.5,
            context={},
            expected_performance={"latency": 20.0},
        )
        container.register_instance(RLIntegrationInterface, mock_decision_engine)

        # 模擬執行器
        mock_executor = Mock(spec=DecisionExecutorInterface)
        mock_executor.execute_decision.return_value = ExecutionResult(
            success=True,
            execution_time=25.0,
            performance_metrics={"latency": 20.0, "throughput": 100.0},
            status=ExecutionStatus.SUCCESS,
        )
        container.register_instance(DecisionExecutorInterface, mock_executor)

        # 模擬視覺化協調器
        mock_visualization = AsyncMock(spec=VisualizationCoordinatorInterface)
        container.register_instance(
            VisualizationCoordinatorInterface, mock_visualization
        )

        # 模擬狀態管理器
        mock_state_manager = AsyncMock(spec=StateManager)
        container.register_instance(StateManager, mock_state_manager)

    else:
        # --- 註冊真實的組件 (待實現) ---
        logger.info("Creating DI container with REAL implementations (placeholders)")
        # container.register_singleton(EventProcessorInterface, ConcreteEventProcessor)
        # container.register_singleton(StateManager, RedisStateManager)
        # ... 其他真實組件
        pass

    logger.info(
        "Default DI container created",
        mock_mode=use_mocks,
        registered_services=len(container.get_registered_services()),
    )
    return container
