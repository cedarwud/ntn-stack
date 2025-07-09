"""
協調器測試
==========

測試 DecisionOrchestrator 的基本功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import time

from ..orchestrator import DecisionOrchestrator
from ..config.di_container import DIContainer
from ..interfaces.event_processor import EventProcessorInterface, ProcessedEvent
from ..interfaces.candidate_selector import (
    CandidateSelectorInterface,
    Candidate,
    ScoredCandidate,
)
from ..interfaces.decision_engine import RLIntegrationInterface, Decision
from ..interfaces.executor import (
    DecisionExecutorInterface,
    ExecutionResult,
    ExecutionStatus,
)
from ..interfaces.visualization_coordinator import VisualizationCoordinatorInterface
from ..utils.state_manager import StateManager


class TestDecisionOrchestrator:
    """測試決策協調器"""

    @pytest.fixture
    def mock_container(self):
        """創建模擬的DI容器"""
        container = DIContainer()

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

        # 模擬執行器
        mock_executor = Mock(spec=DecisionExecutorInterface)
        mock_executor.execute_decision.return_value = ExecutionResult(
            success=True,
            execution_time=25.0,
            performance_metrics={"latency": 20.0, "throughput": 100.0},
            status=ExecutionStatus.SUCCESS,
        )

        # 模擬視覺化協調器
        mock_visualization = AsyncMock(spec=VisualizationCoordinatorInterface)
        mock_visualization.trigger_3d_animation.return_value = "anim_001"

        # 模擬狀態管理器
        mock_state_manager = AsyncMock()
        mock_state_manager.get_satellite_pool.return_value = [
            {"satellite_id": "SAT_001", "status": "active"}
        ]
        mock_state_manager.get_network_conditions.return_value = {
            "latency": 50.0,
            "packet_loss": 0.01,
        }

        # 註冊到容器
        container.register_instance(EventProcessorInterface, mock_event_processor)
        container.register_instance(CandidateSelectorInterface, mock_candidate_selector)
        container.register_instance(RLIntegrationInterface, mock_decision_engine)
        container.register_instance(DecisionExecutorInterface, mock_executor)
        container.register_instance(
            VisualizationCoordinatorInterface, mock_visualization
        )
        container.register_instance(StateManager, mock_state_manager)

        return container

    def test_orchestrator_initialization(self, mock_container):
        """測試協調器初始化"""
        orchestrator = DecisionOrchestrator(mock_container)

        assert orchestrator.event_processor is not None
        assert orchestrator.candidate_selector is not None
        assert orchestrator.decision_engine is not None
        assert orchestrator.executor is not None
        assert orchestrator.visualization_coordinator is not None
        assert orchestrator.state_manager is not None
        assert not orchestrator.is_running
        assert len(orchestrator.active_decisions) == 0

    @pytest.mark.asyncio
    async def test_make_handover_decision_success(self, mock_container):
        """測試成功的換手決策流程"""
        orchestrator = DecisionOrchestrator(mock_container)

        event_data = {
            "event_type": "A4",
            "ue_id": "UE_001",
            "measurement_data": {"rsrp": -80.0},
        }

        result = await orchestrator.make_handover_decision(event_data)

        assert result.success
        assert result.execution_time > 0
        assert "latency" in result.performance_metrics
        assert result.decision is not None
        assert result.decision.selected_satellite == "SAT_001"

    @pytest.mark.asyncio
    async def test_make_handover_decision_with_visualization(self, mock_container):
        """測試帶視覺化的換手決策流程"""
        orchestrator = DecisionOrchestrator(mock_container)

        event_data = {"event_type": "A4", "ue_id": "UE_001"}

        result = await orchestrator.make_handover_decision(event_data)

        # 驗證視覺化調用
        viz_coordinator = mock_container.get(VisualizationCoordinatorInterface)
        assert viz_coordinator.trigger_3d_animation.called
        assert viz_coordinator.stream_realtime_updates.called

        # 驗證結果
        assert result.success
        assert result.decision is not None
        assert result.decision.visualization_data is not None

    def test_get_service_status(self, mock_container):
        """測試服務狀態獲取"""
        orchestrator = DecisionOrchestrator(mock_container)

        status = orchestrator.get_service_status()

        assert "is_running" in status
        assert "active_decisions" in status
        assert "metrics" in status
        assert "components" in status
        assert status["components"]["event_processor"] == "healthy"

    @pytest.mark.asyncio
    async def test_orchestrator_lifecycle(self, mock_container):
        """測試協調器生命週期"""
        orchestrator = DecisionOrchestrator(mock_container)

        # 測試啟動
        await orchestrator.start()
        assert orchestrator.is_running

        # 測試停止
        await orchestrator.stop()
        assert not orchestrator.is_running

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_container):
        """測試錯誤處理"""
        # 讓事件處理器拋出異常
        event_processor = mock_container.get(EventProcessorInterface)
        event_processor.process_event.side_effect = Exception("Test error")

        orchestrator = DecisionOrchestrator(mock_container)

        event_data = {"event_type": "A4"}
        result = await orchestrator.make_handover_decision(event_data)

        assert not result.success
        assert result.error_message is not None
        assert "Pipeline failed at stage: event_processing" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__])
