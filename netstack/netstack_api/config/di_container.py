"""
依賴注入容器
"""
import logging
from dependency_injector import containers, providers
from unittest.mock import AsyncMock

# 導入接口
from netstack_api.services.ai_decision_integration.interfaces.event_processor import EventProcessorInterface
from netstack_api.services.ai_decision_integration.interfaces.candidate_selector import CandidateSelectorInterface
from netstack_api.services.ai_decision_integration.interfaces.decision_engine import RLIntegrationInterface
from netstack_api.services.ai_decision_integration.interfaces.executor import DecisionExecutorInterface
from netstack_api.services.ai_decision_integration.interfaces.visualization_coordinator import VisualizationCoordinatorInterface

# 導入實現
from netstack_api.services.ai_decision_integration.event_processing.processor import EventProcessor
from netstack_api.services.ai_decision_integration.candidate_selection.selector import CandidateSelector
from netstack_api.services.ai_decision_integration.decision_execution.rl_integration import RLDecisionEngine
from netstack_api.services.ai_decision_integration.decision_execution.executor import DecisionExecutor
from netstack_api.services.ai_decision_integration.visualization_integration.handover_3d_coordinator import Handover3DCoordinator
from netstack_api.services.ai_decision_integration.visualization_integration.realtime_event_streamer import RealtimeEventStreamer

# 導入主協調器
from netstack_api.services.ai_decision_integration.orchestrator import DecisionOrchestrator

logger = logging.getLogger(__name__)

class DIContainer(containers.DeclarativeContainer):
    """
    應用程序的依賴注入容器
    """

    config = providers.Configuration()
    use_mocks = config.get("use_mock_implementations", True)

    if use_mocks:
        logger.info("Using MOCK implementations for DI container")
        # 使用異步 Mock 以支援健康檢查
        event_processor = providers.Factory(
            AsyncMock, spec=EventProcessorInterface
        )
        candidate_selector = providers.Factory(
            AsyncMock, spec=CandidateSelectorInterface
        )
        decision_engine = providers.Factory(
            AsyncMock, spec=RLIntegrationInterface
        )
        executor = providers.Factory(
            AsyncMock, spec=DecisionExecutorInterface
        )
        visualization_coordinator = providers.Factory(
            AsyncMock, spec=VisualizationCoordinatorInterface
        )
        event_streamer = providers.Factory(
             AsyncMock, spec=RealtimeEventStreamer
        )

    else:
        logger.info("Using REAL implementations for DI container")
        # 真正實現的註冊
        event_processor = providers.Singleton(EventProcessor)
        candidate_selector = providers.Singleton(CandidateSelector)
        decision_engine = providers.Singleton(RLDecisionEngine)
        executor = providers.Singleton(DecisionExecutor)
        event_streamer = providers.Singleton(RealtimeEventStreamer)
        visualization_coordinator = providers.Singleton(
            Handover3DCoordinator, event_streamer=event_streamer
        )

    # 主協調器
    orchestrator = providers.Factory(
        DecisionOrchestrator,
        event_processor=event_processor,
        candidate_selector=candidate_selector,
        decision_engine=decision_engine,
        executor=executor,
        visualization_coordinator=visualization_coordinator,
    )

def get_orchestrator() -> DecisionOrchestrator:
    """
    獲取 DecisionOrchestrator 的實例
    """
    # 這裡可以添加配置加載邏輯
    # from your_config_module import settings
    # container.config.from_dict(settings)
    
    container = DIContainer()
    # 可以在這裡動態決定是否使用mocks
    # container.config.set("use_mock_implementations", False) 
    
    return container.orchestrator()

# 導出一個方便使用的函數
__all__ = ["get_orchestrator", "DIContainer"]
