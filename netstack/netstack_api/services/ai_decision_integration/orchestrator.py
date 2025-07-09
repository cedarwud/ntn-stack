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


"""
決策協調器主類 - 階段5優化版本

負責協調整個AI決策流程，採用管道模式簡化邏輯：
1. 使用統一的決策管道處理流程
2. 簡化錯誤處理和狀態管理
3. 增強性能監控和指標收集
4. 完整的3D視覺化整合
"""


class DecisionOrchestrator:
    def __init__(self, container: DIContainer):
        """
        初始化協調器 - 簡化版本

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
        self.metrics: MetricsCollector = MetricsCollector()

        # 創建完整的決策管道
        self.pipeline: DecisionPipeline = self._create_decision_pipeline()

        # 運行狀態
        self.is_running = False
        self.active_decisions: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "Decision orchestrator initialized (Stage 5 optimized)",
            components=len(container.registry),
        )

    def _create_decision_pipeline(self) -> DecisionPipeline:
        """創建完整的決策管道"""
        from .utils.pipeline import PipelineStage

        # 定義管道階段
        stages = [
            PipelineStage(
                name="event_processing",
                processor=self._event_processing_stage,
                timeout=10.0,
            ),
            PipelineStage(
                name="candidate_selection",
                processor=self._candidate_selection_stage,
                timeout=15.0,
            ),
            PipelineStage(
                name="rl_decision", processor=self._rl_decision_stage, timeout=20.0
            ),
            PipelineStage(
                name="visualization_trigger",
                processor=self._visualization_trigger_stage,
                timeout=5.0,
            ),
            PipelineStage(
                name="decision_execution",
                processor=self._decision_execution_stage,
                timeout=30.0,
            ),
            PipelineStage(
                name="result_processing",
                processor=self._result_processing_stage,
                timeout=5.0,
            ),
        ]

        # 創建管道
        pipeline = DecisionPipeline([])
        for stage in stages:
            pipeline.add_stage(stage)

        return pipeline

    async def make_handover_decision(
        self, event_data: Dict[str, Any]
    ) -> ExecutionResult:
        """
        主要的換手決策接口 - 簡化版本使用管道模式

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

            # 準備管道上下文
            context = {
                "decision_id": decision_id,
                "start_time": start_time,
                "event_data": event_data,
                "metrics": self.metrics,
                "components": {
                    "event_processor": self.event_processor,
                    "candidate_selector": self.candidate_selector,
                    "decision_engine": self.decision_engine,
                    "executor": self.executor,
                    "visualization_coordinator": self.visualization_coordinator,
                    "state_manager": self.state_manager,
                },
            }

            # 通知換手開始
            await self._notify_handover_start(event_data, decision_id)

            # 使用管道處理完整決策流程
            result = await self.pipeline.process(event_data, context)

            # 記錄性能指標
            execution_time = time.time() - start_time
            self.metrics.record_decision_latency(execution_time)
            self.metrics.record_decision_success(result.success)

            # 通知換手完成
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

    # 管道階段實現
    async def _event_processing_stage(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """事件處理階段"""
        try:
            event_type = data.get("event_type", "A4")
            processed_event = self.event_processor.process_event(event_type, data)

            # 更新上下文
            context["processed_event"] = processed_event

            # 推送階段更新
            await self._update_visualization_stage("event_processed", processed_event)

            logger.debug(
                "Event processing stage completed",
                event_type=event_type,
                confidence=processed_event.confidence,
            )

            return {**data, "processed_event": processed_event}

        except Exception as e:
            logger.error("Event processing stage failed", error=str(e))
            raise

    async def _candidate_selection_stage(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """候選篩選階段"""
        try:
            processed_event = data["processed_event"]

            # 從狀態管理器獲取衛星池
            satellite_pool = await self.state_manager.get_satellite_pool()

            # 篩選候選衛星
            candidates = await self.candidate_selector.select_candidates(
                processed_event, satellite_pool
            )

            # 評分候選衛星
            scored_candidates = await self.candidate_selector.score_candidates(candidates)

            # 更新上下文
            context["scored_candidates"] = scored_candidates

            # 推送階段更新
            await self._update_visualization_stage(
                "candidates_selected", scored_candidates
            )

            logger.debug(
                "Candidate selection stage completed",
                total_candidates=len(scored_candidates),
                top_score=(
                    max(c.score for c in scored_candidates) if scored_candidates else 0
                ),
            )

            return {**data, "scored_candidates": scored_candidates}

        except Exception as e:
            logger.error("Candidate selection stage failed", error=str(e))
            raise

    async def _rl_decision_stage(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """RL決策階段"""
        try:
            processed_event = data["processed_event"]
            scored_candidates = data["scored_candidates"]

            # 準備決策上下文
            decision_context = {
                "event": processed_event,
                "timestamp": time.time(),
                "network_conditions": await self.state_manager.get_network_conditions(),
                "decision_id": context["decision_id"],
            }

            # 使用RL引擎做決策
            decision = self.decision_engine.make_decision(
                scored_candidates, decision_context
            )

            # 更新上下文
            context["decision"] = decision

            # 推送階段更新
            await self._update_visualization_stage("decision_made", decision)

            logger.debug(
                "RL decision stage completed",
                selected_satellite=decision.selected_satellite,
                confidence=decision.confidence,
                algorithm=decision.algorithm_used,
            )

            return {**data, "decision": decision}

        except Exception as e:
            logger.error("RL decision stage failed", error=str(e))
            raise

    async def _visualization_trigger_stage(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """視覺化觸發階段"""
        try:
            decision = data["decision"]
            scored_candidates = data["scored_candidates"]

            # 觸發3D視覺化
            visualization_event = VisualizationEvent(
                event_type=AnimationType.DECISION_MADE,
                timestamp=time.time(),
                satellite_data=decision.visualization_data,
                animation_params={
                    "selected_satellite": decision.selected_satellite,
                    "candidates": [c.candidate.satellite_id for c in scored_candidates],
                    "confidence": decision.confidence,
                    "decision_id": context["decision_id"],
                },
                duration_ms=decision.visualization_data.get("animation_duration", 5000),
            )

            animation_id = await self.visualization_coordinator.trigger_3d_animation(
                visualization_event
            )

            # 更新上下文
            context["animation_id"] = animation_id

            logger.debug(
                "Visualization trigger stage completed",
                animation_id=animation_id,
                selected_satellite=decision.selected_satellite,
            )

            return {**data, "animation_id": animation_id}

        except Exception as e:
            logger.warning("Visualization trigger stage failed", error=str(e))
            # 視覺化失敗不應該影響決策流程
            return data

    async def _decision_execution_stage(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """決策執行階段"""
        try:
            decision = data["decision"]
            decision_id = context["decision_id"]

            # 執行決策
            execution_context = ExecutionContext(
                execution_id=decision_id, timestamp=time.time(), timeout_seconds=30.0
            )

            result = self.executor.execute_decision(decision, execution_context)
            result.decision = decision
            result.execution_id = decision_id

            # 更新狀態管理器
            await self.state_manager.update_handover_state(decision, result)

            # 更新上下文
            context["execution_result"] = result

            logger.debug(
                "Decision execution stage completed",
                success=result.success,
                execution_time=result.execution_time,
            )

            return {**data, "execution_result": result}

        except Exception as e:
            logger.error("Decision execution stage failed", error=str(e))
            raise

    async def _result_processing_stage(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> ExecutionResult:
        """結果處理階段"""
        try:
            execution_result = data["execution_result"]
            decision = data["decision"]

            # 記錄算法特定指標
            if hasattr(decision, "algorithm_used") and decision.algorithm_used:
                self.metrics.record_algorithm_latency(
                    decision.algorithm_used, execution_result.execution_time
                )

            # 觸發執行完成動畫
            if execution_result.success:
                completion_event = VisualizationEvent(
                    event_type=AnimationType.EXECUTION_COMPLETE,
                    timestamp=time.time(),
                    satellite_data={
                        "selected_satellite": decision.selected_satellite,
                        "success": True,
                        "performance_metrics": execution_result.performance_metrics,
                    },
                    animation_params={
                        "success_indicator": True,
                        "cleanup_previous": True,
                        "decision_id": context["decision_id"],
                    },
                    duration_ms=1000,
                )

                await self.visualization_coordinator.trigger_3d_animation(
                    completion_event
                )

            logger.debug(
                "Result processing stage completed",
                success=execution_result.success,
                selected_satellite=decision.selected_satellite,
            )

            return execution_result

        except Exception as e:
            logger.error("Result processing stage failed", error=str(e))
            # 即使結果處理失敗，也要返回執行結果
            return data.get(
                "execution_result",
                ExecutionResult(
                    success=False,
                    status=ExecutionStatus.FAILED,
                    error_message=str(e),
                    execution_time=0.0,
                    performance_metrics={},
                    execution_id=context["decision_id"],
                ),
            )

    # 輔助方法
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
            "status": "healthy" if self.is_running else "stopped",
            "is_running": self.is_running,
            "active_decisions": len(self.active_decisions),
            "metrics": self.metrics.get_summary(),
            "pipeline_stats": self.pipeline.get_pipeline_stats(),
            "components": {
                "event_processor": "healthy",
                "candidate_selector": "healthy",
                "decision_engine": "healthy",
                "executor": "healthy",
                "visualization_coordinator": "healthy",
            },
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取詳細的性能指標"""
        return {
            "orchestrator_metrics": self.metrics.get_summary(),
            "pipeline_metrics": self.pipeline.get_pipeline_stats(),
            "prometheus_metrics": self.metrics.get_prometheus_metrics(),
            "recent_latencies": self.metrics.get_recent_latencies(),
            "active_animations": len(
                self.visualization_coordinator.get_active_animations()
            ),
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 檢查各組件健康狀態
            components_health = {
                "event_processor": await self._check_component_health(
                    self.event_processor
                ),
                "candidate_selector": await self._check_component_health(
                    self.candidate_selector
                ),
                "decision_engine": await self._check_component_health(
                    self.decision_engine
                ),
                "executor": await self._check_component_health(self.executor),
                "visualization_coordinator": await self._check_component_health(
                    self.visualization_coordinator
                ),
            }

            overall_health = all(components_health.values())

            return {
                "overall_health": overall_health,
                "components": components_health,
                "metrics": self.metrics.get_summary(),
                "pipeline_status": self.pipeline.get_pipeline_stats(),
                "uptime": time.time() - self.metrics._start_time,
            }

        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "overall_health": False,
                "error": str(e),
                "timestamp": time.time(),
            }

    async def _check_component_health(self, component: Any) -> bool:
        """檢查組件健康狀態"""
        try:
            if hasattr(component, "health_check"):
                return await component.health_check()
            return True
        except Exception:
            return False

    async def start(self):
        """啟動協調器，開始監控任務"""
        self.is_running = True
        logger.info("Decision orchestrator started (Stage 5 optimized)")

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
