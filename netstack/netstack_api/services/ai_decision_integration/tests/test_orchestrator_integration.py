"""
協調器與管道集成測試
====================

測試 DecisionOrchestrator 與 DecisionPipeline 的集成，
確保完整的決策流程能夠正確、有序地執行。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, call
import time

from ..orchestrator import DecisionOrchestrator
from ..utils.pipeline import DecisionPipeline
from ..config.di_container import DIContainer
from ..interfaces import (
    EventProcessorInterface,
    CandidateSelectorInterface,
    RLIntegrationInterface,
    DecisionExecutorInterface,
    VisualizationCoordinatorInterface,
)
from ..utils.state_manager import StateManager
from ..interfaces.event_processor import ProcessedEvent
from ..interfaces.candidate_selector import Candidate, ScoredCandidate
from ..interfaces.decision_engine import Decision
from ..interfaces.executor import ExecutionResult, ExecutionStatus


@pytest.fixture
def mock_pipeline_components():
    """創建模擬的管道組件"""
    components = {
        "event_processor": AsyncMock(spec=EventProcessorInterface),
        "candidate_selector": AsyncMock(spec=CandidateSelectorInterface),
        "decision_engine": AsyncMock(spec=RLIntegrationInterface),
        "executor": AsyncMock(spec=DecisionExecutorInterface),
        "visualization": AsyncMock(spec=VisualizationCoordinatorInterface),
        "state_manager": AsyncMock(spec=StateManager),
    }

    # 為每個階段設置返回值
    components["state_manager"].get_satellite_pool.return_value = [{"id": "SAT-01"}]
    components["event_processor"].process_event.return_value = ProcessedEvent(
        event_type="A4",
        event_data={},
        timestamp=time.time(),
        confidence=0.9,
        ue_id="UE1",
        trigger_conditions={},
        source_cell="CELL_01",
        target_cells=["CELL_02"],
        measurement_values={},
    )

    test_candidate = Candidate(
        satellite_id="SAT-01",
        elevation=45.0,
        signal_strength=-80,
        load_factor=0.5,
        distance=1200,
        azimuth=180.0,
        doppler_shift=500.0,
        position={"x": 1, "y": 2, "z": 3},
        velocity={"vx": 1, "vy": 2, "vz": 3},
        visibility_time=300.0,
    )

    components["candidate_selector"].select_candidates.return_value = [test_candidate]
    components["candidate_selector"].score_candidates.return_value = [
        ScoredCandidate(
            candidate=test_candidate,
            score=0.9,
            confidence=0.95,
            ranking=1,
            sub_scores={"signal": 0.9, "elevation": 0.9},
            reasoning={"reason": "best_signal"},
        )
    ]
    components["decision_engine"].make_decision.return_value = Decision(
        selected_satellite="SAT-01",
        confidence=0.9,
        reasoning={"alg": "DQN"},
        alternative_options=[],
        execution_plan={},
        visualization_data={"type": "handover"},
        algorithm_used="DQN",
        decision_time=10.0,
        context={},
        expected_performance={"latency": 30},
    )
    components["executor"].execute_decision.return_value = ExecutionResult(
        success=True,
        execution_time=10.0,
        performance_metrics={},
        status=ExecutionStatus.SUCCESS,
    )

    return components


@pytest.fixture
def container(mock_pipeline_components):
    """創建一個 DI 容器並註冊模擬組件"""
    c = DIContainer()
    c.register_instance(
        EventProcessorInterface, mock_pipeline_components["event_processor"]
    )
    c.register_instance(
        CandidateSelectorInterface, mock_pipeline_components["candidate_selector"]
    )
    c.register_instance(
        RLIntegrationInterface, mock_pipeline_components["decision_engine"]
    )
    c.register_instance(DecisionExecutorInterface, mock_pipeline_components["executor"])
    c.register_instance(
        VisualizationCoordinatorInterface, mock_pipeline_components["visualization"]
    )
    c.register_instance(StateManager, mock_pipeline_components["state_manager"])
    return c


@pytest.mark.asyncio
async def test_successful_pipeline_flow(container, mock_pipeline_components):
    """
    測試一個成功的、完整的決策管道流程。
    驗證:
    1. Orchestrator 正確初始化。
    2. 管道中的每個階段都按預期順序被調用。
    3. 最終返回成功的 ExecutionResult。
    4. 視覺化協調器在關鍵點被調用。
    """
    # 1. 初始化
    orchestrator = DecisionOrchestrator(container)
    event_data = {"event_type": "A4", "ue_id": "UE_001"}

    # 2. 執行決策流程
    result = await orchestrator.make_handover_decision(event_data)

    # 3. 驗證結果
    assert result.success
    assert result.decision is not None
    assert result.decision.selected_satellite == "SAT-01"
    assert result.status == ExecutionStatus.SUCCESS

    # 4. 驗證管道階段調用順序
    proc = mock_pipeline_components["event_processor"]
    sel = mock_pipeline_components["candidate_selector"]
    eng = mock_pipeline_components["decision_engine"]
    exe = mock_pipeline_components["executor"]
    sm = mock_pipeline_components["state_manager"]

    sm.get_network_conditions.assert_awaited_once()
    sm.get_satellite_pool.assert_awaited_once()
    proc.process_event.assert_awaited_once()
    sel.select_candidates.assert_awaited_once()
    sel.score_candidates.assert_awaited_once()
    eng.make_decision.assert_awaited_once()
    exe.execute_decision.assert_awaited_once()

    # 5. 驗證視覺化調用
    viz = mock_pipeline_components["visualization"]

    # 檢查調用次數，start, decision, complete
    assert viz.trigger_3d_animation.call_count >= 1
    assert viz.stream_realtime_updates.call_count >= 1

    # 檢查具體調用
    viz.trigger_3d_animation.assert_awaited()
    viz.stream_realtime_updates.assert_awaited()


@pytest.mark.asyncio
async def test_pipeline_failure_at_selection(container, mock_pipeline_components):
    """
    測試當管道在候選者選擇階段失敗時的行為。
    驗證:
    1. 管道停止執行後續階段。
    2. 返回一個包含錯誤信息的失敗 ExecutionResult。
    3. 觸發了錯誤狀態的視覺化更新。
    """
    # 1. 設置失敗點
    error_message = "Candidate selection failed!"
    mock_pipeline_components["candidate_selector"].select_candidates.side_effect = (
        Exception(error_message)
    )

    # 2. 初始化並執行
    orchestrator = DecisionOrchestrator(container)
    event_data = {"event_type": "A4", "ue_id": "UE_001"}
    result = await orchestrator.make_handover_decision(event_data)

    # 3. 驗證結果
    assert not result.success
    assert result.status == ExecutionStatus.FAILED
    assert error_message in result.error_message
    assert result.decision is None

    # 4. 驗證未被調用的階段
    mock_pipeline_components["decision_engine"].make_decision.assert_not_awaited()
    mock_pipeline_components["executor"].execute_decision.assert_not_awaited()

    # 5. 驗證視覺化錯誤通知
    viz = mock_pipeline_components["visualization"]
    # 檢查 stream_realtime_updates 是否以 'error' 狀態被調用
    error_call_found = False
    for call_args in viz.stream_realtime_updates.await_args_list:
        if call_args[0][0].get("type") == "handover_error":
            error_call_found = True
            assert error_message in call_args[0][0]["data"]["error"]
            break
    assert (
        error_call_found
    ), "An error notification should have been sent via visualization streamer."
