"""
AI Decision Orchestrator API Router
===================================

提供基於新一代 AI 決策協調器的 API 端點。
此路由器旨在逐步取代舊的 `ai_decision_router.py`。
"""

import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
import structlog
from unittest.mock import Mock, AsyncMock
import time

from ..services.ai_decision_integration.orchestrator import DecisionOrchestrator
from ..services.ai_decision_integration.config.di_container import (
    DIContainer,
    create_default_container,
)
from ..services.ai_decision_integration.interfaces import (
    EventProcessorInterface,
    CandidateSelectorInterface,
    RLIntegrationInterface,
    DecisionExecutorInterface,
    VisualizationCoordinatorInterface,
)
from ..services.ai_decision_integration.interfaces.event_processor import ProcessedEvent
from ..services.ai_decision_integration.interfaces.candidate_selector import (
    Candidate,
    ScoredCandidate,
)
from ..services.ai_decision_integration.interfaces.decision_engine import Decision
from ..services.ai_decision_integration.interfaces.executor import (
    ExecutionResult,
    ExecutionStatus,
)
from ..services.ai_decision_integration.utils.state_manager import StateManager

# 初始化
router = APIRouter(
    prefix="/api/v2/decision",
    tags=["AI Decision Orchestrator"],
)
logger = structlog.get_logger(__name__)

# --- 依賴注入設置 ---


def get_orchestrator() -> DecisionOrchestrator:
    """
    FastAPI 依賴項，用於創建和獲取 DecisionOrchestrator 實例。

    在整合測試階段，我們使用一個預先配置了模擬組件的容器。
    """
    try:
        # 在真實應用中，容器的生命週期應該由應用程式本身管理 (例如，在啟動時創建)
        # 為了整合測試的簡便性，我們在這裡即時創建它。
        container = create_default_container(use_mocks=True)
        orchestrator = DecisionOrchestrator(container)
        return orchestrator
    except Exception as e:
        logger.error("Failed to create DecisionOrchestrator", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: Could not initialize AI orchestrator: {e}",
        )


# --- API 端點定義 ---


@router.post("/handover", response_model=ExecutionResult)
async def make_handover_decision(
    event_data: Dict[str, Any],
    orchestrator: DecisionOrchestrator = Depends(get_orchestrator),
):
    """
    啟動一個非同步的衛星換手決策流程。

    此端點接收一個 3GPP 事件，並啟動完整的 AI 決策管道，
    包括事件處理、候選星篩選、RL決策、執行和視覺化。

    Args:
        event_data: 包含事件類型和測量數據的字典。
        orchestrator: 由 DI 容器注入的決策協調器實例。

    Returns:
        ExecutionResult: 決策執行的最終結果。
    """
    logger.info("Received handover decision request (V2)", initial_event=event_data)
    try:
        # 非同步執行決策流程
        result = await orchestrator.make_handover_decision(event_data)

        if not result.success:
            # 如果流程本身失敗 (例如，在早期階段)，我們可能需要回傳一個錯誤的 HTTP 狀態
            # 但為了保持與 ExecutionResult 的一致性，我們回傳 200 OK，並在響應體中指明失敗
            logger.warning(
                "Handover decision process resulted in failure",
                decision_id=result.execution_id,
                error=result.error_message,
            )

        return result
    except Exception as e:
        logger.error(
            "Unhandled exception in handover decision endpoint (V2)",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


@router.get("/status")
async def get_orchestrator_status(
    orchestrator: DecisionOrchestrator = Depends(get_orchestrator),
):
    """
    獲取 AI 決策協調器的當前狀態和性能指標。
    """
    return orchestrator.get_service_status()


@router.websocket("/ws/realtime")
async def websocket_realtime_updates(
    websocket: WebSocket, orchestrator: DecisionOrchestrator = Depends(get_orchestrator)
):
    """
    提供一個 WebSocket 端點，用於實時串流決策流程的更新和視覺化事件。
    """
    await websocket.accept()

    # 獲取視覺化協調器的模擬實例
    vis_coordinator_mock = orchestrator.visualization_coordinator

    # 將 WebSocket 連接添加到模擬的協調器中，以便它可以發送消息
    # 這是一個測試技巧；在真實實現中，協調器將會有一個更正式的機制來管理客戶端
    if isinstance(vis_coordinator_mock, AsyncMock):
        # 覆蓋 stream_realtime_updates 的行為，使其將數據發送到此 websocket
        async def send_to_websocket(data: Dict[str, Any]):
            await websocket.send_json(data)

        vis_coordinator_mock.stream_realtime_updates.side_effect = send_to_websocket

    try:
        while True:
            # 保持連接開放以接收來自伺服器的推送
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("Realtime websocket client disconnected")
    except Exception as e:
        logger.error("Error in realtime websocket", error=str(e))
    finally:
        # 清理
        if isinstance(vis_coordinator_mock, AsyncMock):
            vis_coordinator_mock.stream_realtime_updates.side_effect = None
        logger.info("Closed realtime websocket connection")
