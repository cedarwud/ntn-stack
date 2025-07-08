"""
決策協調器
==========

主要的決策流程協調器，負責整合所有組件並管理完整的決策流程。
這個類替代了原來的 ai_decision_engine.py 的主要功能。
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional
import structlog

from .interfaces.event_processor import EventProcessorInterface, ProcessedEvent
from .interfaces.candidate_selector import CandidateSelectorInterface
from .interfaces.decision_engine import RLIntegrationInterface, Decision
from .interfaces.executor import (
    DecisionExecutorInterface,
    ExecutionResult,
    ExecutionContext,
    ExecutionStatus,
)
from .interfaces.visualization_coordinator import (
    VisualizationCoordinatorInterface,
    VisualizationEvent,
    AnimationType,
)
from .utils.state_manager import StateManager
from .utils.pipeline import DecisionPipeline
from .utils.metrics import MetricsCollector
from .config.di_container import DIContainer

logger = structlog.get_logger(__name__)


class DecisionOrchestrator:
    """
    決策協調器主類

    負責協調整個AI決策流程：
    1. 事件處理 -> 2. 候選篩選 -> 3. RL決策 -> 4. 執行 -> 5. 視覺化同步
    """

    def __init__(self, container: DIContainer):
        """
        初始化協調器

        Args:
            container: 依賴注入容器
        """
        # 核心組件注入
        self.event_processor: EventProcessorInterface = container.get(
            EventProcessorInterface
        )
        self.candidate_selector: CandidateSelectorInterface = container.get(
            CandidateSelectorInterface
        )
        self.decision_engine: RLIntegrationInterface = container.get(
            RLIntegrationInterface
        )
        self.executor: DecisionExecutorInterface = container.get(
            DecisionExecutorInterface
        )
        self.visualization_coordinator: VisualizationCoordinatorInterface = (
            container.get(VisualizationCoordinatorInterface)
        )

        # 工具組件
        self.state_manager: StateManager = container.get(StateManager)
        self.pipeline: DecisionPipeline = DecisionPipeline(
            [
                self.event_processor,
                self.candidate_selector,
                self.decision_engine,
                self.executor,
            ]
        )
        self.metrics: MetricsCollector = MetricsCollector()

        # 運行狀態
        self.is_running = False
        self.active_decisions: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "Decision orchestrator initialized", components=len(container.registry)
        )

    async def make_handover_decision(
        self, event_data: Dict[str, Any]
    ) -> ExecutionResult:
        """
        主要的換手決策接口 - 包含完整的決策流程和3D視覺化

        Args:
            event_data: 3GPP事件數據

        Returns:
            ExecutionResult: 執行結果
        """
        decision_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            logger.info(
                "Starting handover decision process",
                decision_id=decision_id,
                event_type=event_data.get("event_type"),
            )

            # 發送換手開始事件到3D前端
            await self._notify_handover_start(event_data, decision_id)

            # 階段1: 事件處理
            processed_event = await self._process_event(event_data)
            await self._update_visualization_stage("event_processed", processed_event)

            # 階段2: 候選篩選
            candidates = await self._select_candidates(processed_event)
            await self._update_visualization_stage("candidates_selected", candidates)

            # 階段3: RL決策
            decision = await self._make_rl_decision(candidates, processed_event)
            await self._trigger_3d_visualization(decision, candidates)

            # 階段4: 執行決策
            execution_context = ExecutionContext(
                execution_id=decision_id, timestamp=time.time(), timeout_seconds=30.0
            )
            result = await self._execute_decision(decision, execution_context)

            # 記錄性能指標
            execution_time = time.time() - start_time
            self.metrics.record_decision_latency(execution_time)
            self.metrics.record_decision_success(result.success)

            # 發送完成事件到前端
            await self._notify_handover_complete(result, decision_id)

            logger.info(
                "Handover decision completed",
                decision_id=decision_id,
                success=result.success,
                execution_time=execution_time,
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.metrics.record_decision_error(str(e))
            await self._notify_handover_error(e, event_data, decision_id)

            logger.error(
                "Handover decision failed",
                decision_id=decision_id,
                error=str(e),
                execution_time=execution_time,
            )

            return self._handle_decision_error(e, event_data, decision_id, start_time)

    async def _process_event(self, event_data: Dict[str, Any]) -> ProcessedEvent:
        """處理3GPP事件"""
        try:
            event_type = event_data.get("event_type", "A4")
            processed_event = self.event_processor.process_event(event_type, event_data)

            logger.debug(
                "Event processed successfully",
                event_type=event_type,
                confidence=processed_event.confidence,
            )

            return processed_event
        except Exception as e:
            logger.error("Event processing failed", error=str(e))
            raise

    async def _select_candidates(self, processed_event: ProcessedEvent):
        """選擇候選衛星"""
        try:
            # 從狀態管理器獲取衛星池
            satellite_pool = await self.state_manager.get_satellite_pool()

            # 篩選候選衛星
            candidates = self.candidate_selector.select_candidates(
                processed_event, satellite_pool
            )

            # 評分候選衛星
            scored_candidates = self.candidate_selector.score_candidates(candidates)

            logger.debug(
                "Candidates selected",
                total_candidates=len(scored_candidates),
                top_score=(
                    max(c.score for c in scored_candidates) if scored_candidates else 0
                ),
            )

            return scored_candidates
        except Exception as e:
            logger.error("Candidate selection failed", error=str(e))
            raise

    async def _make_rl_decision(
        self, candidates, processed_event: ProcessedEvent
    ) -> Decision:
        """使用RL引擎做出決策"""
        try:
            context = {
                "event": processed_event,
                "timestamp": time.time(),
                "network_conditions": await self.state_manager.get_network_conditions(),
            }

            decision = self.decision_engine.make_decision(candidates, context)

            logger.debug(
                "RL decision made",
                selected_satellite=decision.selected_satellite,
                confidence=decision.confidence,
                algorithm=decision.algorithm_used,
            )

            return decision
        except Exception as e:
            logger.error("RL decision failed", error=str(e))
            raise

    async def _execute_decision(
        self, decision: Decision, context: ExecutionContext
    ) -> ExecutionResult:
        """執行決策"""
        try:
            result = self.executor.execute_decision(decision, context)
            result.decision = decision
            result.execution_id = context.execution_id

            # 更新狀態管理器
            await self.state_manager.update_handover_state(decision, result)

            return result
        except Exception as e:
            logger.error("Decision execution failed", error=str(e))
            raise

    async def _trigger_3d_visualization(self, decision: Decision, candidates):
        """觸發3D視覺化更新"""
        try:
            visualization_event = VisualizationEvent(
                event_type=AnimationType.DECISION_MADE,
                timestamp=time.time(),
                satellite_data=decision.visualization_data,
                animation_params={
                    "selected_satellite": decision.selected_satellite,
                    "candidates": [c.candidate.satellite_id for c in candidates],
                    "confidence": decision.confidence,
                },
                duration_ms=decision.visualization_data.get("animation_duration", 5000),
            )

            animation_id = await self.visualization_coordinator.trigger_3d_animation(
                visualization_event
            )

            logger.debug(
                "3D visualization triggered",
                animation_id=animation_id,
                selected_satellite=decision.selected_satellite,
            )

        except Exception as e:
            logger.warning("3D visualization failed", error=str(e))
            # 視覺化失敗不應該影響決策流程

    async def _notify_handover_start(
        self, event_data: Dict[str, Any], decision_id: str
    ):
        """通知換手開始"""
        try:
            await self.visualization_coordinator.stream_realtime_updates(
                {
                    "type": "handover_started",
                    "decision_id": decision_id,
                    "event_data": event_data,
                    "timestamp": time.time(),
                }
            )
        except Exception as e:
            logger.warning("Failed to notify handover start", error=str(e))

    async def _notify_handover_complete(
        self, result: ExecutionResult, decision_id: str
    ):
        """通知換手完成"""
        try:
            await self.visualization_coordinator.stream_realtime_updates(
                {
                    "type": "handover_completed",
                    "decision_id": decision_id,
                    "result": {
                        "success": result.success,
                        "execution_time": result.execution_time,
                        "performance_metrics": result.performance_metrics,
                    },
                    "timestamp": time.time(),
                }
            )
        except Exception as e:
            logger.warning("Failed to notify handover complete", error=str(e))

    async def _notify_handover_error(
        self, error: Exception, event_data: Dict[str, Any], decision_id: str
    ):
        """通知換手錯誤"""
        try:
            await self.visualization_coordinator.stream_realtime_updates(
                {
                    "type": "handover_error",
                    "decision_id": decision_id,
                    "error": str(error),
                    "event_data": event_data,
                    "timestamp": time.time(),
                }
            )
        except Exception as e:
            logger.warning("Failed to notify handover error", error=str(e))

    async def _update_visualization_stage(self, stage: str, data: Any):
        """更新視覺化前端的階段狀態"""
        try:
            await self.visualization_coordinator.stream_realtime_updates(
                {
                    "type": "stage_update",
                    "stage": stage,
                    "data": data,
                    "timestamp": time.time(),
                }
            )
        except Exception as e:
            logger.warning(
                "Failed to update visualization stage", stage=stage, error=str(e)
            )

    def _handle_decision_error(
        self,
        error: Exception,
        event_data: Dict[str, Any],
        decision_id: str,
        start_time: float,
    ) -> ExecutionResult:
        """統一處理決策過程中的錯誤"""
        execution_time = time.time() - start_time
        self.metrics.record_decision_error(
            str(error), event_data.get("event_type", "unknown")
        )

        logger.error(
            "Handover decision failed",
            decision_id=decision_id,
            error=str(error),
            execution_time=execution_time,
            execution_id=decision_id,
        )

        return ExecutionResult(
            success=False,
            status=ExecutionStatus.FAILED,
            error_message=str(error),
            execution_time=execution_time,
            performance_metrics={},
            execution_id=decision_id,
        )

    def get_service_status(self) -> Dict[str, Any]:
        """獲取協調器和其組件的當前狀態"""
        return {
            "is_running": self.is_running,
            "active_decisions": len(self.active_decisions),
            "metrics": self.metrics.get_summary(),
            "components": {
                "event_processor": "healthy",
                "candidate_selector": "healthy",
                "decision_engine": "healthy",
                "executor": "healthy",
                "visualization_coordinator": "healthy",
            },
        }

    async def start(self):
        """啟動協調器，開始監控任務"""
        self.is_running = True
        logger.info("Decision orchestrator started")

    async def stop(self):
        """停止協調器"""
        self.is_running = False
        # 清理活躍決策
        for decision_id in list(self.active_decisions.keys()):
            await self._cleanup_decision(decision_id)
        logger.info("Decision orchestrator stopped")

    async def _cleanup_decision(self, decision_id: str):
        """清理決策狀態"""
        if decision_id in self.active_decisions:
            del self.active_decisions[decision_id]
